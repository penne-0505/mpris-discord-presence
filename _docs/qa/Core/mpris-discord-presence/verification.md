---
title: "QA Verification: MPRIS Discord Rich Presence MVP"
status: active
draft_status: n/a
qa_status: verified
risk: High
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/intent/Core/mpris-discord-presence/decision.md"
  - "_docs/archives/plan/Core/mpris-discord-presence/plan.md"
  - "_docs/archives/plan/Core/compact-status-artist/plan.md"
  - "_docs/qa/Core/mpris-discord-presence/test-plan.md"
related_issues: []
related_prs: []
---

# QA Verification: `MPRIS Discord Rich Presence MVP`

## Summary

MPRIS source、active arbitration、Activity mapping、privacy control、Discord IPC framing/reconnect/rate control、
CLI、systemd user serviceを実装した。自動test、fake Unix socket、実session D-Bus、有効Application IDでの
Discord profile表示、MPRIS player切替、Discord restart replay、service stop clear、packaging、
docs/operations checksを実行した。compact status向け`State`選択と`{artist} を再生中`書式は自動test、
実Discord IPC ACK、friend/member list上の利用者目視で確認した。

## Verification Verdict

Verdict: PASS

## Commands Run

| Command / Test | Result | Notes |
| --- | --- | --- |
| `PYTHONPATH=src python -m unittest -v` | PASS | 69 domain/source/IPC/CLI tests。 |
| `python -m compileall -q src tests` | PASS | 全Python moduleをcompile。 |
| `python -m build --outdir /tmp/mpris-discord-presence-build` | PASS | sdistとwheelをisolated build。初回license classifier failure修正後に再実行。 |
| `bash -n scripts/install-user-service.sh` | PASS | installer syntax。 |
| `./scripts/install-user-service.sh --dry-run` | PASS | current checkoutの生成pathを確認。 |
| isolated `XDG_CONFIG_HOME ... --enable-now` | PASS | Application ID未設定ではdoctorがexit 1し、systemd start前に停止。 |
| rendered unit + `systemd-analyze --user verify` | PASS | placeholder置換後のunitを検証。 |
| `npx --yes markdownlint-cli2 ...` | PASS | cleanup後の45 active Markdown files、0 errors。 |
| `./scripts/check-docs.sh` | PASS | TODO、frontmatter、links、QA、validator/hook fixtures。warningなし。 |
| `git diff --check` | PASS | whitespace errorなし。 |
| `shellcheck scripts/install-user-service.sh` | NOT RUN | localにshellcheckがない。bash syntaxとisolated installer testで代替。 |
| valid-ID foreground daemon | PASS | Listening/Watching publish、pause fallback、resume、SIGINT clear ACK。 |
| Discord desktop stop/start | PASS | disconnect検知、bounded retry、reconnect、latest Apple Music replay。 |
| `./scripts/install-user-service.sh --enable-now` | PASS | user unitをinstall/enable/startし、doctor gateもPASS。 |
| `systemctl --user stop/start mpris-discord-presence.service` | PASS | SIGTERM clear ACK後にenabled/activeへ復帰。 |
| verbose foreground publish with live Discord | PASS | `status_display_type = State`実装後にstate synchronized。serviceをactiveへ復帰。 |

## Automated Test Results

| Area | Result | Evidence |
| --- | --- | --- |
| Active selection / grace / privacy | PASS | permutation、transition、fallback、vanish、deadline、deny/disable tests。 |
| Activity mapping | PASS | type、`{artist} を再生中`、timestamp、position clamp、URL境界、fallback tests。 |
| MPRIS source | PASS | fake Playerctl lifecycle、generation、normalization、metadata-log redaction tests。 |
| Discord IPC | PASS | fake Unix socketでhandshake、PING/PONG、SET/clear、ERROR/CLOSE、UID、frame上限。 |
| Reconnect / coalescing | PASS | bounded backoff、latest replay、4秒flush、immediate clear、shutdown tests。 |
| Config / CLI / operations | PASS | unknown privacy key reject、env ID validation、doctor、SIGTERM clear path、service guard。 |
| Independent review | PASS | 実装reviewとQA/operations reviewの指摘を修正し、最新treeに新規P1/P2なし。 |

## Manual QA Results

| Checklist Item | Result | Notes |
| --- | --- | --- |
| 実session MPRIS discovery | PASS | Vivaldiと`waydroid_mpris`のinitial snapshot、closeを確認。 |
| Discord IPC socket discovery | PASS | `/run/user/1000/discord-ipc-0`、same-user socketを確認。 |
| invalid Application ID rejection | PASS | 実Discord 1.0.146が`Invalid Client ID`を返し、error mappingを確認。 |
| Listening / Watching profile表示 | PASS | 有効IDで両typeをACK。Listening cardは利用者のredacted visual確認あり。 |
| timestamp / artwork / link表示 | PASS | title/state/progressをvisual確認。local artworkのplaceholderはintentどおり。 |
| 実player切替、fallback、grace | PASS | Vivaldi→Apple Music、Apple pause→Vivaldi、Apple resumeを確認。 |
| Waydroid source recovery | PASS | bridge最新processでADB disconnect後4秒で自動接続しPlaying復帰。 |
| denylist / sharing clear | PASS | 全live playerを一時denyし、clear ACK後に設定を復元。 |
| Discord restart replay | PASS | desktop終了でdisconnect、再起動後reconnectとlatest replayを確認。 |
| installed service stop clear | PASS | systemd SIGTERMでclear acknowledged、再start後active。 |
| compact statusのartist表示 | PASS | `{artist} を再生中`を利用者のredacted visualで確認。画像自体はartifactへ保存しない。 |

## Acceptance Criteria Coverage

| ID | Result | Evidence |
| --- | --- | --- |
| AC-001 | PASS | source/arbiter/controller testsと実session initial discovery。 |
| AC-002 | PASS | payload mappingとactual Listening/Watching profile、progressを確認。 |
| AC-003 | PASS | deny/disable、foreground/service clear ACKを自動・liveで確認。 |
| AC-004 | PASS | actual Discord restart後のbounded reconnect/latest replayを確認。 |
| AC-005 | PASS | Application IDのみ。credential field reject、repo scan、SDK artifactなし。 |
| AC-006 | PASS | doctor、config example、unit、installer guard、guide/reference、rollback手順。 |
| AC-007 | PASS | 自動test、実MPRIS/Discord、verification、docs-cleanup evidenceあり。 |
| AC-008 | PASS | explicit State、新書式test、実client ACK、更新後表示の利用者目視。 |

## Invariant Coverage

| ID | Result | Evidence |
| --- | --- | --- |
| INV-001 | PASS | latest Playing、fallback、vanish、grace tests。 |
| INV-002 | PASS | startup permutationとinitial-enumeration vanish race tests。 |
| INV-003 | PASS | denied/disabled runtime non-publication、immediate clear tests。 |
| INV-004 | PASS | ASCII Application ID validation、credential fields reject、no SDK vendor。 |
| INV-005 | PASS | disconnect latest replay/clear、shutdown testsと実client restart。 |
| INV-006 | PASS | duplicate suppression、4秒latest-only flush、clear bypass tests。 |
| INV-007 | PASS | explicit player ruleとcontent-independent type tests。 |
| INV-008 | PASS | explicit State、`{label} を再生中`、album/player fallback testsと実client ACK。 |

## Deferred / Not Covered

None

## Residual Risks

None

## Follow-up TODOs

None
