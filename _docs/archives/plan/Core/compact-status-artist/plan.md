---
title: Discord compact status artist display plan
status: archived
draft_status: n/a
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/intent/Core/mpris-discord-presence/decision.md"
  - "_docs/qa/Core/mpris-discord-presence/test-plan.md"
  - "_docs/reference/Core/mpris-discord-presence/reference.md"
related_issues: []
related_prs: []
---

# Discord compact status artist display plan

## Overview

Discord Rich Presenceのexpanded cardを維持したまま、friend/member listのcompact statusに
Application名ではなく`{artist} を再生中`というstateを表示する。

## Scope

- Activity payloadへDiscord公式の`status_display_type = State`を追加する。
- `state = {artist} を再生中`とmetadata欠落fallbackをcompact statusに使う。
- payload mapping、fallback、実Discord client受理を検証する。
- README、guide、reference、Intent、QA、verificationを同期する。

## Non-Goals

- expanded card上部のApplication名を変更すること。
- Spotifyまたは他Applicationの名称、ID、logo、brandを使用すること。
- compact statusへ曲名を出すこと、または表示fieldを設定可能にすること。
- artist / albumを外部catalogから補完すること。

## Requirements

- `status_display_type`はDiscord Activity Status Display Typeの`State` (`1`)である。
- artistがある場合、`state`は`{artist} を再生中`とする。
- artist欠落時はalbum、次にplayer nameへfallbackし、同じ`{label} を再生中`書式で空fieldを送らない。
- `details`、timestamps、assets、URLs、Activity typeの既存mappingを変えない。
- expanded cardの2行目も同じ`state`を使うため、同じ接尾辞が表示される。
- 日本語接尾辞はpayload textであり、Discord client localeによる翻訳対象にしない。
- local IPC rejectionまたは表示不一致を自動testだけから成功扱いしない。

## Tasks

1. TODO、Intent、QA test-planへAC / INVと検証方法を追加する。
2. Activity model、mapper、AC / INV対応unit testを更新する。
3. full checks、package build、実Discord publishを実行する。
4. 利用者目視をverificationへ反映し、qa-review後にTODOを完了する。

## QA Plan

- QA document: `_docs/qa/Core/mpris-discord-presence/test-plan.md`
- Risk level: High
- Unit: payloadの`status_display_type`、artist state書式、album/player fallback。
- Regression: expanded card用field、全既存domain/source/IPC test、package build。
- Live: Discord desktopへのpublish ACKとfriend/member listの利用者目視。
- Static: compile、docs validators、Markdown lint、diff check。

## Deployment / Rollout

- repo sourceを参照するsystemd user serviceをrestartし、最新payloadをpublishする。
- client rejection時はservice logsとforeground debugのgeneric ACKだけを確認し、metadataをlogへ出さない。
- rollbackは`status_display_type`指定を外した既存revisionへ戻してserviceをrestartする。
- user token、secret、別Application IDは導入しない。
