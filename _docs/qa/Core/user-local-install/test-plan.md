---
title: "QA Test Plan: User-local installation"
status: active
draft_status: n/a
qa_status: in-progress
risk: High
created_at: 2026-07-11
updated_at: 2026-07-11
references:
  - "_docs/intent/Core/user-local-install/decision.md"
  - "_docs/plan/Core/user-local-install/plan.md"
related_issues: []
related_prs: []
---

# QA Test Plan: `User-local installation`

## Source of Intent

- TODO: `Core-Enhance-11`
- Plan: `_docs/plan/Core/user-local-install/plan.md`
- Intent: `_docs/intent/Core/user-local-install/decision.md`

## Quality Goal

fresh checkoutからuser-local runtimeを再現でき、導入後はcheckoutに依存せず、更新失敗や再導入で既存設定・serviceを破壊しない。

## Acceptance Criteria

- AC-001: installerが`--system-site-packages`付き専用venvへpackageを導入し、serviceがそのCLIを実行する。
- AC-002: installed runtimeがcheckout pathと`PYTHONPATH`を参照しない。
- AC-003: 既存configを保持し、install失敗時に既存unit / environmentを置換しない。
- AC-004: 利用者文書がsupport境界とfresh cloneからupdate / rollbackまでを説明する。
- AC-005: 一時HOMEのautomated integration testsが主要install invariantsを検証する。

## Intent-derived Invariants

- INV-001: installed serviceは専用venvのentry pointとuser configだけをruntime入力とし、source checkoutを参照しない。
- INV-002: 既存configはinstall / updateで上書きされず、初回生成時だけmode `0600`で作成される。
- INV-003: package buildまたはstaging installが失敗した場合、既存service unitとenvironmentは変更されない。
- INV-004: 専用venvは`--system-site-packages`を使用し、PyGObject / Playerctlをrepoまたはwheelへvendorしない。
- INV-005: 公開手順はArch Linux / EndeavourOSと公式Discord clientだけをsupport対象として明記する。

## Risk Assessment

- Risk level: High
- Risk rationale: 既存systemd user serviceの実行pathを変更するmigrationであり、失敗すると自動起動不能になる。
- Regression risk: 既存config、environment、stop時clear、CLI argumentが新unitで失われる可能性がある。
- Data safety risk: config上のApplication IDとprivacy設定を上書きする可能性がある。
- Security / privacy risk: config permission低下、意図しないmetadata共有、任意checkout pathの実行が残る可能性がある。
- UX risk: Arch以外や非公式Discord clientでもsupportされると誤解される可能性がある。
- Agent misbehavior risk: CI変更時にlive desktopを要求したり、doctorの期待failureをCI failureと誤認する可能性がある。

## Test Strategy

- Unit: Python domain / CLI testsを維持する。
- Integration: temporary HOME / XDG_CONFIG_HOME / XDG_DATA_HOMEとfake systemctlでinstallerを実行する。
- E2E: built wheelをstaging venvへinstallし、installed CLI `--help`を実行する。
- Manual QA: generated paths、unit、config permission、dry-run、document手順を確認する。
- Validator / static check: `bash -n`、compile、docs check、build、`git diff --check`。
- Diff review: secret混入、checkout path、package data、rollback説明を確認する。

## Test Matrix

| ID | Source | Requirement / Invariant | Test Type | Command / File | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | 専用venvへinstallしserviceがinstalled CLIを使う | integration | installer test | venv creation flagとExecStartを確認 | verified |
| AC-002 | TODO | runtimeがcheckout非依存 | integration / diff | installer test、generated unit | repo pathとPYTHONPATHがunitに存在しない | verified |
| AC-003 | TODO | config保持とfailure-safe切替 | integration | installer test | sentinel config / unitが保持される | verified |
| AC-004 | TODO | support / install / update / rollback手順 | docs review | README、Quickstart、guide | 一続きの手順と境界が存在する | verified |
| AC-005 | TODO | install invariantsをCIで検証 | CI / integration | `.github/workflows/tests.yml` | fresh runnerでtestsが実行される | verified |
| INV-001 | intent | installed serviceはcheckoutを参照しない | integration | installer test | dedicated venv CLIだけを参照 | verified |
| INV-002 | intent | configを上書きしない | integration | installer test | contentとmodeを確認 | verified |
| INV-003 | intent | staging failureでunitを変更しない | integration | installer failure test | preexisting sentinelを確認 | verified |
| INV-004 | intent | system-site-packages、no vendor | integration / package review | installer test、wheel listing | flagあり、GI binaryなし | verified |
| INV-005 | intent | support境界を限定する | docs review | README、Quickstart | Arch系＋公式clientの明記 | verified |

## Manual QA Checklist

- [x] `--dry-run`がuser-local runtime / config / unit pathを表示し、filesystemを変更しない。
- [x] 初回installでconfigがmode `0600`で作られる。
- [x] 既存configを再installしても内容が変わらない。
- [x] generated unitがcheckout pathと`PYTHONPATH`を含まない。
- [x] installed CLIの`--help`がcheckout外から成功する。

## Regression Checklist

- [x] 既存69 Python testsがPASSする。
- [x] systemd sandboxとshutdown clear pathがunitに保持される。
- [x] `--disable-now`がinstalled packageを削除せずserviceだけをdisableする。
- [x] docs validatorsとCI workflow定義のlocal equivalentがPASSする。

## High-risk Checklist

- [x] Rollback / recovery pathが文書化されている。
- [x] 既存configのdata safetyが確認されている。
- [x] Security / privacyとしてconfig permissionと共有境界が確認されている。
- [x] build / install / doctor failure時の挙動が理解されている。

## Out of Scope

- live Discord / MPRIS interactionの再検証。
- Arch Linux / EndeavourOS以外、非公式またはsandboxed Discord client。
- PyPI / AUR release automation。

## Open Questions

- None
