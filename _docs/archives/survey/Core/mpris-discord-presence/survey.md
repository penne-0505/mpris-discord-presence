---
title: MPRIS to Discord Rich Presence feasibility survey
status: archived
draft_status: n/a
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/archives/plan/Core/mpris-discord-presence/plan.md"
  - "_docs/intent/Core/mpris-discord-presence/decision.md"
  - "_docs/qa/Core/mpris-discord-presence/test-plan.md"
related_issues: []
related_prs: []
---

# MPRIS to Discord Rich Presence feasibility survey

## Background

Linux desktop上のnative player、browser、Waydroid bridgeはMPRIS playerとして同じ
session D-Busへ現れる。目的はApple Music固有のintegrationではなく、現在activeなmedia
1件をSpotifyに近いDiscord profile Activityとして共有することである。

## Objective

- 複数MPRIS playerをevent-drivenに監視できるsource APIを選ぶ。
- 全player横断のactive selectionをdeterministicかつtestableに定義する。
- Linux Discord desktopへ`Listening` / `Watching` Activityを送るtransportを選ぶ。
- public OSS repo、privacy、SDK distribution、live verificationの制約を把握する。

## Method

2026-07-10に以下を確認した。

- MPRIS 2.2 Player interfaceと`PropertiesChanged`契約。
- playerctl 2.4.1の`Playerctl.PlayerManager` / `Playerctl.Player` GI API。
- Discord RPC IPC v1のhandshake、frame、`SET_ACTIVITY`、activity types。
- Discord Social SDK direct Rich Presence、Linux compatibility、SDK Terms。
- local Discord 1.0.146、`/run/user/1000/discord-ipc-0`、Vivaldiと
  `waydroid_mpris`のMPRIS availability。

Primary references:

- <https://specifications.freedesktop.org/mpris/latest/>
- <https://github.com/altdesktop/playerctl>
- <https://docs.discord.com/developers/topics/rpc>
- <https://docs.discord.com/developers/discord-social-sdk/development-guides/setting-rich-presence>
- <https://docs.discord.com/developers/discord-social-sdk/core-concepts/platform-compatibility>
- <https://support-dev.discord.com/hc/en-us/articles/30225844245271-Discord-Social-SDK-Terms>

## Results

- Python 3.14、PyGObject、Playerctl 2.0 typelib、GLibがlocalに存在する。
- `Playerctl.PlayerManager`はplayer appearance/vanishを管理でき、managed playerは
  playback-status、metadata、seeked signalsを公開する。
- MPRISはplayerごとのstateを定義するが、全player横断のactive playerは定義しない。
- Discord RPC `SET_ACTIVITY`はPlaying、Listening、Watching、Competingを受け、timestampsと
  Activity metadataを送れる。IPC framingはUnix socketとlength-prefixed JSONで実装できる。
- Discord Social SDKはLinuxをExperimentalとして提供するが、C++ libraryとproprietary
  shared libraryを必要とする。SDK Terms上、public repoへのstandalone vendorは避ける。
- Discord docsはRPC一般commandのauthentication requirementと、Social SDK direct Rich
  Presenceのauthentication-free pathを別々に説明している。現行clientでのunauthenticated
  direct IPCはApplication ID取得後にlive verificationが必要である。
- MPRIS metadataはplayerごとに欠落し得る。特にbrowser mediaは`xesam:url`を公開しない場合が
  あり、Listening / Watchingをcontentから常に判定できない。

## Discussion

MVP sourceはPlayerctl GI adapterとし、domain model / arbiterから分離する。CLI subprocess
followやplayerctld依存はappearance/vanish、fake tests、classificationを扱いにくい。

MVP transportは公式仕様のlocal Discord IPCを直接実装する。Social SDKを使わないことで、
SDK binary/headerのvendor、C++ build、public CIの配布条件をcoreから外せる。ただしlive
Discord clientがunauthenticated `SET_ACTIVITY`を拒否する場合は、verificationをFAIL/PARTIALに
してSocial SDK adapterをfollow-upとして再評価する。

media typeは既定`Listening`とし、player bus-name globで`Watching`等へoverrideする。URLや
タイトルからのheuristic分類は誤公開・誤分類を生むためMVPでは行わない。

## Recommended Actions

1. Pure domain model、active arbiter、activity mapperを先に実装しfake testsで固定する。
2. Playerctl GI sourceとDiscord IPC transportをadapterとして分離する。
3. share-all + denylist、service stop時clear、reconnect replayをcore invariantにする。
4. Application ID取得後、Discord desktopでListening/Watching、timestamps、clear、reconnectを
   live検証する。
