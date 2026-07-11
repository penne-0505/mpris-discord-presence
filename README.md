# mpris-discord-presence

Linux desktopで現在activeなMPRIS player 1件を選び、Discord Rich Presenceとして共有する常駐ツールです。Waydroid上のApple Music、browser動画、native playerを同じMPRIS境界から扱います。

> [!WARNING]
> 既定では、denylistに一致しない全MPRIS playerのtitle・artist・album・public HTTPS URL（queryを含む）をDiscord profileへ公開します。privateなbrowser mediaを再生する環境では、導入前に`deny_players`を設定してください。

## 現在の機能

- 全MPRIS playerの出現、消失、再生状態、metadata、seekを監視
- 最後に`Playing`へ遷移したplayerをactiveとして自動選択
- activeのpause/stop/終了時に、別のPlayingへfallback、または1.5秒後にclear
- Discordの`Listening` / `Watching`をplayer globごとに設定
- title、artist、album、position/duration、public HTTPS artwork/linkを表示
- friend/member listのcompact statusへ`{artist} を再生中`を表示
- Discord未起動・再起動・IPC切断後に再接続し、最新状態だけを再送
- player denylist、共有全停止、終了時clear
- 診断CLIとsystemd user service

本プロジェクトはalphaです。サポート対象はArch Linux / EndeavourOSのdesktop sessionと、Discord公式Linux clientです。
公式clientのlocal IPCを直接使用し、Discord Social SDKやuser tokenは使用しません。他distributionやFlatpak / Snap、
Vesktopなどの非公式clientはサポート対象外です。

## 必要環境

- Arch LinuxまたはEndeavourOSのdesktop sessionとsession D-Bus
- Python 3.11以降
- PyGObjectとPlayerctl 2.0 typelib
- MPRIS対応player
- Discord desktop
- Discord Developer Portalで作成したApplication ID

OS package:

```bash
sudo pacman -S git playerctl python-gobject python-pip
```

## 最短セットアップ

```bash
git clone https://github.com/penne-0505/mpris-discord-presence.git
cd mpris-discord-presence
./scripts/install-user-service.sh
${EDITOR:-nano} ~/.config/mpris-discord-presence/config.toml
~/.local/share/mpris-discord-presence/venv/bin/mpris-discord-presence \
  --config ~/.config/mpris-discord-presence/config.toml doctor
~/.local/share/mpris-discord-presence/venv/bin/mpris-discord-presence \
  --config ~/.config/mpris-discord-presence/config.toml run
```

installerは`--system-site-packages`付き専用venvへpackageを導入します。導入後のruntimeはcheckoutを参照しません。
foregroundで期待どおり表示・clearされることを確認してからserviceをenableします。

```bash
systemctl --user enable --now mpris-discord-presence.service
journalctl --user -u mpris-discord-presence.service -f
```

詳細は[Quickstart](QUICKSTART.md)、設定と挙動は[運用ガイド](_docs/guide/Core/mpris-discord-presence/usage.md)、実装境界は[リファレンス](_docs/reference/Core/mpris-discord-presence/reference.md)を参照してください。

## 開発

```bash
PYTHONPATH=src python -m unittest -v
python -m compileall -q src tests
./scripts/test-install-user-service.sh
./scripts/check-docs.sh
```

設計判断は[_docs/intent/Core/mpris-discord-presence/decision.md](_docs/intent/Core/mpris-discord-presence/decision.md)、検証計画と結果は[_docs/qa/Core/mpris-discord-presence/](_docs/qa/Core/mpris-discord-presence/)にあります。

## Privacy / security boundary

- Discordへ送るのは選択されたtrackの表示用metadataです。
- 通常ログとtest artifactにはtrack metadataを残しません。
- Discord credentialはpublicなApplication IDだけです。
- user token、OAuth token、client secret、join secretを要求・保存しません。
- local `file://` artworkは公開せず、設定したstatic application assetへfallbackします。

## English summary

This Linux daemon selects the most recently activated MPRIS player and publishes one Discord Listening or Watching Rich Presence. It supports privacy deny rules, deterministic fallback, reconnect/replay, and a systemd user service. The configuration comments and CLI output are in English; the detailed project documentation is currently Japanese.

## License

[MIT License](LICENSE.txt)
