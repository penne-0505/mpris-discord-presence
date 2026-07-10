---
title: MPRIS Discord Rich Presence architecture decision
status: active
draft_status: n/a
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/archives/survey/Core/mpris-discord-presence/survey.md"
  - "_docs/archives/plan/Core/mpris-discord-presence/plan.md"
  - "_docs/archives/plan/Core/compact-status-artist/plan.md"
  - "_docs/qa/Core/mpris-discord-presence/test-plan.md"
related_issues: []
related_prs: []
---

# MPRIS Discord Rich Presence architecture decision

## Context

共有対象はApple Musicだけではなく、browser動画やnative playerを含む全MPRIS sourceである。
Discordには同時に1件だけ表示し、直近に再生を開始したmediaをSpotifyに近いprofile Activityとして
見せたい。MPRISにはglobal active player概念がなく、Discord IPCとsource lifecycleも独立して揺れる。

既定share-allは利用者の意図だが、browserのprivate media titleを公開し得る。外部SDKのvendor、
Discord user credential、暗黙のcontent inferenceも避ける必要がある。

## Decision

- source boundaryはMPRIS session busとし、Playerctl GI adapterで全playerを監視する。
- playerごとのstateをpure snapshotへ変換し、I/Oから独立したarbiterでactive 1件を選ぶ。
- activeは実際のnon-Playing→Playing transitionのmonotonic sequenceで決める。
- active終了時は他Playingへ即fallbackし、候補なしは1.5秒grace後にclearする。
- startup履歴がない複数Playingはconfigured priority、次にstable player nameで決める。
- Discord transportはlocal IPC v1を直接実装し、Social SDKをMVP dependencyにしない。
- Activity typeは既定Listening、player glob overrideでWatching等を指定する。content heuristicは使わない。
- compact statusはDiscordの`status_display_type = State`を明示し、`{artist} を再生中`という
  日本語固定の`state`を表示元にする。
- 全playerを既定共有し、denylistとservice stop/disableによるclearを必須にする。
- public HTTPS artwork/linkだけをDiscordへ渡し、local file artworkはstatic app assetへfallbackする。
- Discord切断中はlatest desired stateだけを保持し、bounded reconnect後にreplayする。

## Alternatives

- **Apple Music専用consumer**: Waydroid bridgeには合うがbrowser/native player共有という目的を失う。
- **playerctldをactive sourceにする**: most-recent selectionは近いがsynthetic player追加、startup tie-break、
  denylist、media typeを本project側で一貫して検証しにくい。
- **playerctl subprocess follow**: lifecycleと複数player stateをstructured eventとして扱いにくい。
- **Discord Social SDK**: supported APIだがLinux Experimental、C++/shared library、public repoへの
  vendor/CI制約がMVP規模に見合わない。direct IPCがliveで不成立の場合のみ再評価する。
- **window/audio detection**: MPRISのprivacy/metadata境界を越え、誤検出とplatform依存が増える。
- **content-based Listening/Watching inference**: URL欠落とbrowser用途混在により誤分類する。
- **Application名またはSpotify偽装**: 再生内容をmember listから判別できず、他Applicationの名称・brandを
  借りる方法は誤認を生む。Discord公式のstatus display selectionで必要な表示だけを選ぶ。
- **titleをcompact statusへ表示**: 曲名よりartist名を優先する利用者要件と異なる。expanded cardの
  `details`にはtitleを維持する。

## Rationale

MPRISとDiscordをadapterで分離すれば、Waydroid bridgeを含む任意のplayerを同じdomain ruleで扱え、
arbiterとprivacy policyをlive desktopなしで検証できる。direct IPCは必要機能が小さい本projectで
dependency/distribution boundaryを最小化する。explicit configurationはheuristicより予測可能である。

## Consequences / Impact

- Python runtime、PyGObject、Playerctl typelib、Discord desktop、Application IDが必要になる。
- Application ID取得前にdomain/IPC testはできるが、actual profile表示は検証できない。
- browserを既定共有するため、denylistを設定しない利用者はmedia titleを公開する。
- local artworkをtrack-specificに表示できない場合があり、static fallbackを使う。
- Discord IPC protocol/client behaviorの変化はadapter更新で吸収する。
- compact statusとexpanded cardの2行目は同じ`state`を共有するため、どちらにも「を再生中」が付く。

## Quality Implications

- active selectionはevent orderとstartup orderを混同してはならない。
- denied/disabled source metadataはDiscord payloadに入ってはならない。
- source vanish、Discord disconnect、shutdownでstale presenceを放置してはならない。
- partial reads、unexpected opcode、socket churnでdaemon全体をcrashさせてはならない。
- live Discord未検証をunit PASSから推測して完了扱いしてはならない。
- compact statusの表示fieldをApplication既定値へ暗黙依存させてはならない。

## Intent-derived Invariants

- INV-001: active playerは最新のPlaying transitionで選び、候補消失時は残るPlayingへfallbackしなければならない。
- INV-002: startupの複数Playing選択はdiscovery orderに依存せず、設定priorityとstable nameでdeterministicでなければならない。
- INV-003: denied playerまたはsharing disabled時のmetadataはDiscord Activity payloadへ到達してはならない。
- INV-004: Discordへ送るcredentialはpublic Application IDだけで、user token/secret/SDK vendorを要求してはならない。
- INV-005: Discord/source disconnect後はbounded recoveryし、desired stateをreplayするかActivityをclearし、staleな別trackを残してはならない。
- INV-006: Activity updateはtrack/status/selection変化にcoalesceし、position表示のため毎秒Discordへ送信してはならない。
- INV-007: media typeは既定Listeningとexplicit player ruleだけで決め、private content inspection heuristicを追加してはならない。
- INV-008: compact statusは`State`を明示的に選び、artistがあれば`{artist} を再生中`というstateを使わなければならない。artist欠落時も同じ書式でstateを空にしてはならない。

## Enforced in (optional)

- INV-001〜002: arbiter unit tests。
- INV-003: config/selection/mapper tests。
- INV-004: config schema、diff review、security checks。
- INV-005〜006: fake IPC integrationとlifecycle tests。
- INV-007: classification testsとconfig reference。
- INV-008: Activity mapperのpayload testsと実Discord client publish。

## Rollback / Follow-ups

- service stop/disableとforeground daemon終了でActivityをclearする。
- direct IPCが現行Discord clientで不成立ならverificationをPASSにせず、Social SDK adapterを別TODOで評価する。
- catalog enrichment、local artwork hosting、automatic content classificationはMVP後の独立判断とする。
