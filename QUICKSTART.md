# Quickstart

この手順は、検証済みtagのsourceからuser-local runtimeを構築し、まずforegroundで表示とclearを確認してから
systemd user serviceへ移す順序です。

サポート対象はArch Linux / EndeavourOSと[Discord公式Linux client](https://discord.com/download)です。
他distribution、Flatpak / Snap、Vesktopなどの非公式clientは動作保証の対象外です。

## 1. Runtimeを用意する

EndeavourOS / Arch Linux:

```bash
sudo pacman -S git playerctl python-gobject python-pip
python -c "import gi; gi.require_version('Playerctl', '2.0'); from gi.repository import Playerctl"
```

installerは専用venvを`--system-site-packages`付きで作成し、上記OS packageのGI bindingsを利用します。

## 2. 検証済みsourceを取得する

GitHub Releasesで案内されたtagを指定します。例:

```bash
git clone --branch <release-tag> --depth 1 \
  https://github.com/penne-0505/mpris-discord-presence.git
cd mpris-discord-presence
```

## 3. Discord Applicationを作る

[Discord Developer Portal](https://discord.com/developers/applications)でApplicationを作り、General Informationに表示されるApplication IDを控えます。

このツールに必要なのはApplication IDだけです。bot、OAuth redirect、user token、client secretは設定しません。任意でRich Presence Assetsへfallback iconを登録すると、MPRIS artworkがlocalまたは欠落しているtrackにも固定画像を表示できます。

## 4. User-local runtimeとConfigを作る

導入先は`~/.local/share/mpris-discord-presence/venv`、configは
`~/.config/mpris-discord-presence/config.toml`です。

```bash
./scripts/install-user-service.sh
${EDITOR:-nano} ~/.config/mpris-discord-presence/config.toml
```

installerは現在のsourceからpackageを専用venvへ導入するため、成功後はcheckoutを移動・削除してもruntimeが動作します。
既存configは再installやupdateで上書きしません。

最初に次の項目を確認します。

```toml
application_id = "123456789012345678"
sharing_enabled = true
deny_players = ["playerctld"]
startup_priority = ["waydroid_mpris", "vivaldi*"]
default_activity_type = "listening"

[activity_types]
"waydroid_mpris" = "listening"
"vivaldi*" = "watching"
```

`sharing_enabled = true`は、denylistに一致しないplayerのmetadataをprofileへ公開します。Vivaldi全体を公開したくない場合は`deny_players = ["playerctld", "vivaldi*"]`のように指定します。

## 5. 診断とforeground確認

Discord desktopと確認したいmedia playerを起動して実行します。

```bash
~/.local/share/mpris-discord-presence/venv/bin/mpris-discord-presence \
  --config ~/.config/mpris-discord-presence/config.toml doctor
~/.local/share/mpris-discord-presence/venv/bin/mpris-discord-presence \
  --config ~/.config/mpris-discord-presence/config.toml run
```

次を確認します。

1. 再生開始後、Discord profileへ1件だけ表示される。
2. 別playerで再生を開始すると、そのplayerへ切り替わる。
3. activeをpauseすると、別のPlayingへ戻るか、候補がなければ約1.5秒で消える。
4. `Ctrl-C`後にPresenceが消える。

表示されない場合は、Discord側でactivity共有が許可されているか、Application ID、IPC socket、MPRIS playerを`doctor`出力で確認します。

## 6. 検証コマンド

実装・設定変更後のlocal checks:

```bash
PYTHONPATH=src python -m unittest -v
python -m compileall -q src tests
bash -n scripts/install-user-service.sh
./scripts/test-install-user-service.sh
./scripts/check-docs.sh
```

## 7. user serviceをenableする

事前確認:

```bash
./scripts/install-user-service.sh --dry-run
```

foreground確認後にenableします。configとunitはすでにuser-local pathへ配置されています。

```bash
systemctl --user enable --now mpris-discord-presence.service
systemctl --user status mpris-discord-presence.service
```

ログ:

```bash
journalctl --user -u mpris-discord-presence.service -f
```

ログはplayer instanceと接続状態だけを扱い、track titleなどを意図的に出しません。

## 8. Update

新しい検証済みtagを取得し、そのcheckoutでinstallerを再実行します。既存configは保持され、直前の完全なruntimeが
rollback用に残ります。

```bash
git fetch --tags
git checkout <new-release-tag>
./scripts/install-user-service.sh
~/.local/share/mpris-discord-presence/venv/bin/mpris-discord-presence \
  --config ~/.config/mpris-discord-presence/config.toml doctor
systemctl --user restart mpris-discord-presence.service
```

## 9. 停止・rollback

```bash
./scripts/install-user-service.sh --disable-now
```

または:

```bash
systemctl --user disable --now mpris-discord-presence.service
```

接続中のDiscord Activityをclearしてからdaemonが終了します。unitとconfigは再開・調査用に保持されます。共有だけを止めてserviceを残す場合は`sharing_enabled = false`へ変更してserviceをrestartします。

直前のuser-local runtimeへ戻す場合:

```bash
./scripts/install-user-service.sh --rollback
```

初回のuser-local移行前に既存unitがあった場合は、そのunitも`.previous`として保持され、runtime履歴がない場合の
`--rollback`で復元されます。configはrollbackでも変更しません。

## 次に読む文書

- [運用ガイド](_docs/guide/Core/mpris-discord-presence/usage.md)
- [設定・挙動リファレンス](_docs/reference/Core/mpris-discord-presence/reference.md)
- [architecture decision](_docs/intent/Core/mpris-discord-presence/decision.md)
