---
title: MPRIS Discord Presence technical reference
status: active
draft_status: n/a
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/intent/Core/mpris-discord-presence/decision.md"
  - "_docs/qa/Core/mpris-discord-presence/test-plan.md"
  - "_docs/guide/Core/mpris-discord-presence/usage.md"
related_issues: []
related_prs: []
---

# MPRIS Discord Presence technical reference

## Runtime flow

```text
Playerctl GI / session D-Bus
        │ immutable SourceEvent
        ▼
PresenceController ── ActivePlayerArbiter
        │ one Activity or clear
        ▼
ReconnectCoordinator ── DiscordIPCClient ── same-user Discord socket
```

`mpris_source.py`だけがGI objectを所有する。source callbackより先はplain immutable valuesを使う。
`app.py`はsource event、arbiter decision、Activity mappingを結ぶがevent loopを所有しない。CLIがGLib main loopへ
100ms tickを登録し、retry deadlineとpause graceを進める。

## Source events

| Kind | Meaning | Active selection effect |
| --- | --- | --- |
| `appeared` | playerをmanageし初期snapshotを取得 | initial setに収集、runtimeなら通常upsert |
| `playback-status` | Playing / Paused / Stopped変化 | non-Playing→Playingだけが最新sequenceを取得 |
| `metadata` | title等の変更 | activeならActivity更新、active identityは奪わない |
| `seeked` | discontinuous position change | activeならtimestamp更新 |
| `vanished` | owner/player消失 | activeならfallbackまたはgrace |

identityはbase player name、full instance、generationを保持する。vanish後に同名instanceが再出現しても、旧GI callbackは
generationとobject identityで無視する。

## Config reference

既定pathは`$XDG_CONFIG_HOME/mpris-discord-presence/config.toml`、未設定時は
`~/.config/mpris-discord-presence/config.toml`である。`--config`で上書きできる。

| Key | Type | Default | Behavior |
| --- | --- | --- | --- |
| `application_id` | decimal string | none | public Discord Application ID。envでも指定可能 |
| `sharing_enabled` | boolean | `true` | falseならcandidateを使わずclearする |
| `deny_players` | string array | `["playerctld"]` | base nameまたはinstanceにcase-sensitive glob match |
| `startup_priority` | string array | `[]` | startup時だけordered glob priorityとして使用 |
| `default_activity_type` | enum | `listening` | `playing/listening/watching/competing` |
| `activity_types` | TOML table | `{}` | player globからactivity typeへのordered rule |
| `clear_grace_seconds` | number | `1.5` | Playing候補なしからclearまで。0で即時clear |
| `reconnect_initial_seconds` | positive number | `0.5` | Discord IPC retryの初期待機 |
| `reconnect_max_seconds` | positive number | `30.0` | exponential backoff上限 |
| `fallback_art_asset` | string | none | Discord application asset key |

Application IDは環境変数`MPRIS_DISCORD_APPLICATION_ID`でも指定できる。configの非空値を優先する。

## Activity mapping

| MPRIS | Discord Activity |
| --- | --- |
| `xesam:title` | `details` |
| `xesam:artist` | `state` (`{artist} を再生中`) |
| `xesam:album` | artwork hover text、artist欠落時の`state` fallback |
| position + `mpris:length` | start/end timestamps |
| public HTTPS `mpris:artUrl` | `assets.large_image` |
| public HTTPS `xesam:url` | details URL / `Open media` button |
| configured type | Activity `type` |
| formatted `state` | compact status (`status_display_type = State`) |

表示fieldはwhitespaceをnormalizeし、128 Unicode code pointsへ制限する。title/artist欠落時はplayer nameを使う。
localhost、private IP、credential付きURL、HTTP、`file://`はDiscordへ渡さない。

positionは通常進行ごとにpublishしない。Activity送信時のpositionからstart/end timestampを作り、Discord client側の
clock projectionへ任せる。metadata/status/seek/selection変化だけが新しいdesired stateを作り、connected時は
[Discord Activity仕様](https://docs.discord.com/developers/events/gateway-events#activity-object)の
5 updates / 20 seconds制限に対して4秒間隔でlatest stateだけをflushする。clearと再接続後のreplayは残留防止を優先して
即時送信する。同仕様のbutton制限に合わせ、button/details URLは512文字を超える場合に省略する。
`status_display_type`には`State` (`1`)を明示し、member listのcompact statusでApplication名ではなく
`{artist} を再生中`という`state`を選ぶ。artistがない場合はalbum、次にplayer nameへfallbackし、同じ
`{label} を再生中`書式を使う。この日本語文字列はpayloadの一部であり、client localeでは翻訳されない。

## Discord IPC boundary

- Linux Unix socket候補`discord-ipc-0`〜`discord-ipc-9`をruntime dir順に探索する。
- socket path所有UIDと接続後`SO_PEERCRED` UIDの双方をcurrent userと照合する。
- IPC v1 little-endian header、1 MiB frame上限、partial read、PING/PONG/CLOSE/ERRORを扱う。
- handshakeにはApplication ID、`SET_ACTIVITY`にはcurrent process PIDとActivityだけを送る。
- disconnect中はlatest desired stateだけを保持し、0.5秒から30秒までbounded exponential retryする。
- user token、OAuth、client secret、join secret、Social SDK binary/headerはruntime/repo boundaryに含めない。

## Operational files

- example config: `config.example.toml`
- unit template: `packaging/systemd/mpris-discord-presence.service.in`
- installer: `scripts/install-user-service.sh`
- generated config: `~/.config/mpris-discord-presence/config.toml`
- generated unit: `~/.config/systemd/user/mpris-discord-presence.service`

unitはcheckoutの`src`を`PYTHONPATH`へ指定する。checkoutを移動・削除すると起動できないため、移動後はinstallerを
再実行する。

## Known limits

- MPRISを公開しないmediaは検出しない。
- MPRISにはglobal active playerがないため、本project独自のPlaying transition ruleを使う。
- browser metadataだけから音楽/動画を安全に分類できないためplayer単位のtype ruleである。
- local artworkをupload/serveしないためtrack固有画像が表示されない場合がある。
- Discord local IPCはdocumented Social SDKよりcompatibility riskがあり、live client受理をreleaseごとに確認する。
