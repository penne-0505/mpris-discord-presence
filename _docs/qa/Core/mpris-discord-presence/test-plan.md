---
title: "QA Test Plan: MPRIS Discord Rich Presence MVP"
status: active
draft_status: n/a
qa_status: in-progress
risk: High
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/archives/survey/Core/mpris-discord-presence/survey.md"
  - "_docs/intent/Core/mpris-discord-presence/decision.md"
  - "_docs/archives/plan/Core/mpris-discord-presence/plan.md"
  - "_docs/archives/plan/Core/compact-status-artist/plan.md"
related_issues: []
related_prs: []
---

# QA Test Plan: `MPRIS Discord Rich Presence MVP`

## Source of Intent

- TODO: `Core-Feat-9`, `Core-Enhance-10`
- Plan: `_docs/archives/plan/Core/mpris-discord-presence/plan.md`
- Enhancement Plan: `_docs/archives/plan/Core/compact-status-artist/plan.md`
- Intent: `_docs/intent/Core/mpris-discord-presence/decision.md`
- Survey: `_docs/archives/survey/Core/mpris-discord-presence/survey.md`

## Quality Goal

active media 1件を予測可能かつprivacy-controlledにDiscordへ共有し、MPRIS/Discordのchurnで
別track・denied metadata・stale presenceを残さない。live外部依存と自動検証範囲を分離する。

## Acceptance Criteria

- AC-001: 全MPRIS playerを監視し、Playing transition/fallback/grace/clear規則でactive 1件を選ぶ。
- AC-002: metadata/timestamps/artwork/link/typeを有効なDiscord Activityへ写像する。
- AC-003: share-all default、denylist、disable、shutdown clearが機能する。
- AC-004: Discord IPC disconnect/restartをbounded retryし、latest desired Activityをreplayする。
- AC-005: Application ID以外のcredentialとSocial SDK vendorを必要としない。
- AC-006: CLI diagnostics、config、systemd service、運用docsが提供される。
- AC-007: core behaviorを自動テストし、live Discord/MPRIS evidenceをverificationへ残す。
- AC-008: compact statusはApplication名ではなく`{artist} を再生中`というstateを表示元にする。

## Intent-derived Invariants

- INV-001: 最新Playing transitionとfallback ruleを守る。
- INV-002: startup selectionはdiscovery order非依存である。
- INV-003: denied/disabled metadataをDiscordへ送らない。
- INV-004: public Application ID以外のDiscord credentialを扱わない。
- INV-005: disconnect後にstale Activityを残さない。
- INV-006: positionの毎秒Activity updateを行わない。
- INV-007: media typeはexplicit ruleだけで決める。
- INV-008: compact statusは`State`を明示し、`{label} を再生中`書式でstateを空にしない。

## Risk Assessment

- Risk level: High
- Risk rationale: public profileへの自動metadata公開、external Discord IPC、systemd常駐を扱う。
- Regression risk: source選択誤り、stale Activity、Discord reconnect failure。
- Data safety risk: Low。永続dataはlocal configとservice unitのみ。
- Security / privacy risk: High。browser media titleを既定で公開し得る。user token/secretは禁止。
- UX risk: High。誤player、誤type、pause後残留、update spamが共有体験を損なう。
- Agent misbehavior risk: Medium。live Discord未確認をunit結果から成功扱いする可能性がある。

## Test Strategy

- Unit: domain snapshots、arbiter、config、mapper、framing、retry/coalescing。
- Integration: fake Playerctl event source、fake Unix socket Discord server。
- E2E: local Vivaldi/Waydroid MPRIS、Discord desktop/profile。
- Manual QA: denylist、pause grace、fallback、shutdown clear、Discord restart。
- Validator / static check: unittest、compile、shell syntax、systemd verify、docs checks、diff check。
- Diff review: no user token/secret、no Social SDK artifact、no content heuristic、no channel bot。

## Test Matrix

| ID | Source | Requirement / Invariant | Test Type | Command / File | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | appearance/status/vanishからactive 1件を選ぶ。 | unit + integration | `tests/test_arbiter.py`; source adapter tests | transition、fallback、grace、clearがdeterministic。 | verified |
| AC-002 | TODO | metadataをListening/Watching Activityへ写像する。 | unit + live | `tests/test_activity.py`; Discord profile | fields、timestamps、fallback、typeが一致。 | verified |
| AC-003 | TODO | share-all、denylist、disable、clear。 | unit + manual | config/arbiter/daemon tests | denied metadata absent、stop時clear。 | verified |
| AC-004 | TODO | IPC churnからreconnect/replayする。 | integration + live | `tests/test_discord_ipc.py`; Discord restart | bounded retry、latest-only replay、no crash。 | verified |
| AC-005 | TODO | Application ID以外を扱わない。 | static + config | diff、`config.example.toml`、reference | token/secret/SDK artifactなし。 | verified |
| AC-006 | TODO | daily-use entrypointsがある。 | static + manual | CLI/service/README/guide | diagnose、install、rollback手順が動く。 | verified |
| AC-007 | TODO | testとverificationがclosureする。 | test + validator | full checks、verification | AC/INV coverageと残gapが正確。 | verified |
| AC-008 | TODO | compact statusにartist stateを使う。 | unit + live | `tests/test_activity.py`; Discord member list | `status_display_type = 1`、stateが`{artist} を再生中`、clientが受理。 | verified |
| INV-001 | intent | latest Playing/fallback。 | unit | `tests/test_arbiter.py` | event orderごとのselected player一致。 | verified |
| INV-002 | intent | startup order非依存。 | property/table test | `tests/test_arbiter.py` | input permutationで同じ選択。 | verified |
| INV-003 | intent | denied/disabled metadata非送信。 | unit + integration | config/daemon tests | payload captureにmetadataなし。 | verified |
| INV-004 | intent | credential boundary。 | config + diff | config parser、repo scan | Application IDだけ。 | verified |
| INV-005 | intent | stale Activityなし。 | integration + live | fake socket/source churn | clear/replay transition一致。 | verified |
| INV-006 | intent | update coalescing。 | fake-clock unit | daemon/publisher tests | tickごとのsendなし、semantic changeのみ。 | verified |
| INV-007 | intent | explicit media type rule。 | unit | mapper/config tests | title/URL内容でtypeが変わらない。 | verified |
| INV-008 | intent | explicit State selectionと表示書式。 | unit + live | mapper payload test; Discord desktop | field省略なし、接尾辞、artist欠落fallback、publish成功。 | verified |

## Manual QA Checklist

- [x] Application IDを設定し、Discord desktopでListening Activityを確認する。
- [x] Vivaldi overrideでWatching Activityを確認する。
- [x] Waydroid Apple MusicとVivaldiのPlaying切替がactive selectionへ反映される。
- [x] active pause時のfallback/grace clearを確認する。
- [x] denylist playerのmetadataがprofileへ出ない。
- [x] Discord restart後にlatest Activityが復帰する。
- [x] service stop後にActivityがclearされる。
- [x] friend/member listのcompact statusに`{artist} を再生中`が表示される。

## Regression Checklist

- [x] sourceなし、metadata欠落、artworkなしでもdaemonが継続する。
- [x] multiple Playing startup orderで選択が揺れない。
- [x] malformed/partial Discord frameでunbounded allocationやcrashが起きない。
- [x] repeated identical stateがDiscord update spamにならない。
- [x] docs validatorsとservice static checksが通る。

## High-risk Checklist

- [x] Rollback/recovery pathがguideとverificationにある。
- [x] Data safety: config/service以外の永続dataを作らないことを確認する。
- [x] Security / privacy: share-all disclosureとdenylist/clearがlive確認される。
- [x] Discord unavailable/auth failureを成功扱いしない。

## Out of Scope

- Discord channel posting、複数同時表示、catalog enrichment、local artwork hosting。
- daemonによるplayer/Discord起動、user token/self-bot、Social SDK vendor。

## Open Questions

- None。
