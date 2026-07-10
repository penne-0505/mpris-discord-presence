# Quickstart

この手順は、まずforegroundで表示とclearを確認し、その後にsystemd user serviceへ移す順序です。

## 1. Runtimeを用意する

EndeavourOS / Arch Linux:

```bash
sudo pacman -S playerctl python-gobject
python -c "import gi; gi.require_version('Playerctl', '2.0'); from gi.repository import Playerctl"
```

別distributionでは、PythonのPyGObjectとPlayerctl 2.0 typelibをOS packageから導入してください。venvを使う場合はsystem site packagesが見える構成が必要です。

## 2. Discord Applicationを作る

[Discord Developer Portal](https://discord.com/developers/applications)でApplicationを作り、General Informationに表示されるApplication IDを控えます。

このツールに必要なのはApplication IDだけです。bot、OAuth redirect、user token、client secretは設定しません。任意でRich Presence Assetsへfallback iconを登録すると、MPRIS artworkがlocalまたは欠落しているtrackにも固定画像を表示できます。

## 3. Configを作る

repo-localで試す場合:

```bash
cp config.example.toml config.toml
```

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

## 4. 診断とforeground確認

Discord desktopと確認したいmedia playerを起動して実行します。

```bash
PYTHONPATH=src python -m mpris_discord_presence --config config.toml doctor
PYTHONPATH=src python -m mpris_discord_presence --config config.toml run
```

次を確認します。

1. 再生開始後、Discord profileへ1件だけ表示される。
2. 別playerで再生を開始すると、そのplayerへ切り替わる。
3. activeをpauseすると、別のPlayingへ戻るか、候補がなければ約1.5秒で消える。
4. `Ctrl-C`後にPresenceが消える。

表示されない場合は、Discord側でactivity共有が許可されているか、Application ID、IPC socket、MPRIS playerを`doctor`出力で確認します。

## 5. 検証コマンド

実装・設定変更後のlocal checks:

```bash
PYTHONPATH=src python -m unittest -v
python -m compileall -q src tests
bash -n scripts/install-user-service.sh
./scripts/check-docs.sh
```

## 6. user serviceへ移す

installerはcheckoutの絶対pathを埋め込んだunitを生成します。事前確認:

```bash
./scripts/install-user-service.sh --dry-run
```

install後、生成されたconfigへApplication IDとprivacy設定を反映します。

```bash
./scripts/install-user-service.sh
${EDITOR:-nano} ~/.config/mpris-discord-presence/config.toml
systemctl --user enable --now mpris-discord-presence.service
systemctl --user status mpris-discord-presence.service
```

ログ:

```bash
journalctl --user -u mpris-discord-presence.service -f
```

ログはplayer instanceと接続状態だけを扱い、track titleなどを意図的に出しません。

## 7. 停止・rollback

```bash
./scripts/install-user-service.sh --disable-now
```

または:

```bash
systemctl --user disable --now mpris-discord-presence.service
```

接続中のDiscord Activityをclearしてからdaemonが終了します。unitとconfigは再開・調査用に保持されます。共有だけを止めてserviceを残す場合は`sharing_enabled = false`へ変更してserviceをrestartします。

## 次に読む文書

- [運用ガイド](_docs/guide/Core/mpris-discord-presence/usage.md)
- [設定・挙動リファレンス](_docs/reference/Core/mpris-discord-presence/reference.md)
- [architecture decision](_docs/intent/Core/mpris-discord-presence/decision.md)
