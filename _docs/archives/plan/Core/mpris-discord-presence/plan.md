---
title: MPRIS Discord Rich Presence MVP implementation plan
status: archived
draft_status: n/a
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/archives/survey/Core/mpris-discord-presence/survey.md"
  - "_docs/intent/Core/mpris-discord-presence/decision.md"
  - "_docs/qa/Core/mpris-discord-presence/test-plan.md"
related_issues: []
related_prs: []
---

# MPRIS Discord Rich Presence MVP implementation plan

## Overview

Linux session D-Bus上の全MPRIS playerを監視し、直近の`Playing`遷移をactive playerとして
1件選ぶ。そのtrackをDiscord desktopの`Listening` / `Watching` Rich Presenceへ送り、
privacy control、source/Discord churn recovery、systemd user serviceを含むdaily-use MVPにする。

## Scope

- Playerctl GIによるMPRIS player appearance/vanish/status/metadata/seek監視。
- Pure domain snapshotとdeterministic active-player arbiter。
- 最新`Playing`優先、active終了時fallback、候補なし時grace後clear。
- Discord local IPC v1 handshake/frame/SET_ACTIVITY/clear/reconnect。
- title、artist、album、position/duration、remote artwork、track URL mapping。
- 既定share-all、player glob denylist、activity type/priority override。
- TOML config、CLI doctor/run、systemd user service installer、logs。
- Unit/integration/live QA、README、Quickstart、guide、reference。

## Non-Goals

- Discord user token/self-bot、bot account、channel message投稿。
- 複数trackを一つのPresenceに同時表示またはrotationすること。
- audio capture、window title scraping、browser extension、content fingerprinting。
- Apple Music/YouTube catalog APIでmetadataを補完すること。
- local `file://` artworkをpublic serverへuploadすること。
- daemonがmedia playerやDiscordを起動・停止すること。
- Discord Social SDK binary/headerをrepoへvendorすること。

## Requirements

- **Functional**:
  - newly Playing playerがactiveになり、複数Playing時は最新transitionを優先する。
  - activeがpause/stop/vanishすると他Playingへfallbackし、なければ1.5秒後にclearする。
  - startup時の複数Playingはconfigured priority、次にstable player nameで決める。
  - metadata changeはactive identityを不必要に切り替えずPresenceを更新する。
  - Discord unavailable時はlatest desired Activityを保持し、bounded reconnect後にreplayする。
  - graceful shutdownとsharing disabledはDiscord Activityをclearする。
  - denied playerはcandidateにもActivityにもならない。
- **Non-Functional**:
  - secret/user tokenを扱わず、Application IDだけを設定する。
  - player names/track metadataはlocal processingに限定し、Discord表示以外へ送らない。
  - updateはcoalesceし、positionの毎秒送信を避けtimestampsでclient projectionさせる。
  - domain logicとI/O adapterを分離し、live servicesなしでunit testできる。
  - source/Discord failureはdaemon crashやstale Activity放置にしない。

## Tasks

1. Python package、config schema、CLI skeletonを作る。
2. Track/player snapshotとactive arbiterを実装する。
3. Activity mapperとmedia type/artwork/link fallbackを実装する。
4. Discord IPC framing、socket discovery、handshake、clear、reconnect/replayを実装する。
5. Playerctl GI source adapterとGLib lifecycleを実装する。
6. service/doctor/install helper、README/Quickstart/guide/referenceを整える。
7. AC/INV対応test、static checks、live QA、verificationを実行する。

## QA Plan

- QA document: `_docs/qa/Core/mpris-discord-presence/test-plan.md`
- Risk level: High
- Test strategy:
  - Unit: config、arbiter、mapping、framing、retry/coalescing。
  - Integration: fake Playerctl eventsとfake Unix Discord socket。
  - E2E: local Vivaldi/Waydroid MPRISとDiscord desktop。
  - Manual QA: profile表示、pause grace、denylist、service stop clear、Discord restart。
  - Validator / static check: unittest、compile、shell syntax、systemd verify、docs validators。
  - Security/privacy review: no user token、share-all disclosure、denylist、no SDK vendor。

## Deployment / Rollout

- repo-local runとfake integrationを先に通す。
- Application IDを設定してforeground live probeを行う。
- userがprofile表示を確認した後だけsystemd user serviceをinstall/enableする。
- rollbackはservice disable/stopでActivityをclearし、repo-local daemonを停止する。
- unauthenticated IPCが現行clientで成立しない場合は成功扱いにせず、Social SDK adapterを
  follow-up taskへ分離する。
