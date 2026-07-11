---
title: MPRIS Discord Presence operations guide
status: active
draft_status: n/a
created_at: 2026-07-10
updated_at: 2026-07-11
references:
  - "README.md"
  - "QUICKSTART.md"
  - "_docs/reference/Core/mpris-discord-presence/reference.md"
  - "_docs/intent/Core/mpris-discord-presence/decision.md"
  - "_docs/qa/Core/user-local-install/verification.md"
related_issues: []
related_prs: []
---

# MPRIS Discord Presence operations guide

## Daily operation

service状態とprivacy設定は次で確認する。

```bash
systemctl --user status mpris-discord-presence.service
sed -n '1,160p' ~/.config/mpris-discord-presence/config.toml
~/.local/share/mpris-discord-presence/venv/bin/mpris-discord-presence \
  --config ~/.config/mpris-discord-presence/config.toml doctor
```

config変更後はserviceをrestartする。

```bash
systemctl --user restart mpris-discord-presence.service
```

daemonはMPRIS playerやDiscord desktopを起動しない。どちらが後から起動しても、source appearanceまたは
bounded IPC retryによって追従する。

## Active playerの決まり方

daemon起動後は、non-Playingから`Playing`へ最後に遷移したplayerがactiveになる。同じplayerのmetadata更新や
通常のposition進行はactive順を変更しない。

activeがpause、stop、vanishした場合:

1. 他にPlayingがあれば、最後にPlayingへ遷移した候補へ直ちにfallbackする。
2. 候補がなければ現在表示を`clear_grace_seconds`だけ保持する。
3. grace中に再生が戻らなければPresenceをclearする。

起動前から複数playerがPlayingの場合は履歴を復元できないため、`startup_priority`の先頭一致、次にinstance名の
辞書順で決める。

## Privacy control

既定はshare-allである。共有範囲を絞る場合はglobを追加する。

```toml
deny_players = ["playerctld", "vivaldi*", "firefox*"]
```

全共有を止めてPresenceをclearする場合:

```toml
sharing_enabled = false
```

変更後にserviceをrestartする。即時停止なら次を使う。

```bash
systemctl --user stop mpris-discord-presence.service
```

title、artist、album、public HTTPS URL（queryを含む）はDiscord Activity以外へ送らず、通常ログにも記録しない。`doctor`はplayer instance名だけを
表示する。

## Listening / Watching

MPRIS metadataだけではbrowserの音楽と動画を一貫して識別できない。このためcontent titleやURLによる推測は行わず、
player globで明示する。

```toml
default_activity_type = "listening"

[activity_types]
"vivaldi*" = "watching"
"waydroid_mpris" = "listening"
```

Vivaldi全体にruleが適用されるため、同じbrowserで音楽serviceも使う場合はListeningを既定にするか、Vivaldiを
denylistへ入れる。

## Discord上の表示

friend/member listのcompact statusにはApplication名ではなく、`{artist} を再生中`という日本語固定の`state`を
表示する。artistがなければalbum、両方なければplayer nameへfallbackし、同じ`{label} を再生中`書式を使う。
profileを開いたexpanded cardでは、曲名を`details`、同じstateを2行目、再生位置をprogressとして表示する。
albumはartworkが使える場合のhover textにも残る。

expanded card上部の「Application名を再生中」という見出しはDiscordがApplication情報から生成するため、この
設定では変更しない。別Applicationの名称やbrandを偽装せず、compact statusだけをDiscord公式の
`status_display_type = State`で切り替える。

## Troubleshooting

### Discord IPC socketが見つからない

- Discord desktopを同じLinux user/sessionで起動する。
- Flatpak/Snapなどsandbox版はhostからsocketが見えない場合がある。`doctor`で確認する。
- daemonは終了せず、`reconnect_max_seconds`を上限にretryする。

### MPRIS playerが見えない

```bash
playerctl --list-all
busctl --user list | grep org.mpris.MediaPlayer2
```

playerがMPRISを公開しているか、serviceとplayerが同じsession busを使っているかを確認する。

### Presenceが表示されない

- Application IDがdecimal値か確認する。
- Discord側のactivity sharing設定を確認する。
- `journalctl --user -u mpris-discord-presence.service`でIPC rejectionを確認する。
- local artworkが表示されないことは仕様である。必要なら`fallback_art_asset`を設定する。

Discord cardの画像が「？」になる場合は、Developer PortalのGeneral InformationでApplication iconを設定する。
曲ごとのlocal `file://` artworkは使わないため、固定画像を明示したい場合はRich Presence Assetsへ画像を登録し、
そのasset keyを`fallback_art_asset`へ設定する。

### 古い表示が残る

通常のstopではdaemonがclearを送る。強制kill、session crash、Discord IPC failureではclear requestが届かない場合がある。
daemonを再起動すると、最新Activityまたはclearを再送する。

```bash
systemctl --user restart mpris-discord-presence.service
```

## Install boundary

サポート対象はArch Linux / EndeavourOSとDiscord公式Linux clientである。runtimeは
`~/.local/share/mpris-discord-presence/venv`の専用venv、configは
`~/.config/mpris-discord-presence/config.toml`に置く。serviceはcheckoutや`PYTHONPATH`を参照しない。

## Update and rollback

新しい検証済みtagへcheckoutを切り替え、installerを再実行する。package導入が成功するまで現行runtimeとunitは変更されず、
既存configは常に保持される。

```bash
./scripts/install-user-service.sh
systemctl --user restart mpris-discord-presence.service
```

直前の完全なruntimeへ戻す場合は`./scripts/install-user-service.sh --rollback`を使う。停止だけなら
`--disable-now`を使う。installerはconfigを削除または上書きしないため、同じ設定で再開できる。
