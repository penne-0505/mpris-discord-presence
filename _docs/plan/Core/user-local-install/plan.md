---
title: User-local installation plan
status: active
draft_status: n/a
created_at: 2026-07-11
updated_at: 2026-07-11
references:
  - "_docs/intent/Core/user-local-install/decision.md"
  - "_docs/qa/Core/user-local-install/test-plan.md"
related_issues: []
related_prs: []
---

# User-local installation plan

## Overview

checkoutの`src`を直接実行するserviceから、user-localな専用venvへpackageを導入して実行する方式へ移行する。
fresh cloneから再現でき、導入後はcheckoutを移動または削除してもruntimeが成立する状態を作る。

## Scope

- `~/.local/share/mpris-discord-presence/venv`に`--system-site-packages`付きvenvを作成する。
- installerが現在のcheckoutからwheelを構築し、専用venvへ導入する。
- systemd user unitは専用venv内のCLIとuser configだけを参照する。
- install、update、dry-run、disable、rollbackに必要な利用者向け手順を整備する。
- 一時HOME / XDG pathでinstallerのfilesystem挙動を自動検証する。
- CIでpackage build、isolated install、installer testsを実行する。

## Non-Goals

- PyPIへの公開とPyPIからのinstall。
- Arch package、AUR package、他distribution向けpackage。
- Arch Linux / EndeavourOS以外のruntime support。
- Flatpak / Snap / Vesktopなど公式Linux Discord client以外のsupport。
- live Discord / MPRIS desktop sessionをGitHub Actionsで再現すること。
- installerによる設定値やsecretの自動投入。

## Requirements

- **Functional**: installerは専用venvを作成または更新し、package、config、environment、systemd user unitをuser-local pathへ配置する。
- **Functional**: configが存在する場合は保持し、初回だけmode `0600`で作成する。
- **Functional**: `--enable-now`は新runtimeのdoctor成功後にserviceをenable / startする。
- **Functional**: update失敗時は既存unitとenvironmentを保持する。
- **Non-Functional**: installed runtimeはcheckout path、`PYTHONPATH`、repo内のPython interpreterへ依存しない。
- **Non-Functional**: OS package由来のPyGObject / Playerctlを参照するため、venvは`--system-site-packages`を使用する。
- **Non-Functional**: installer testは実HOMEや実systemd stateを変更しない。

## Tasks

1. installerのpath、staging、install/update、failure behaviorを実装する。
2. service templateをinstalled CLI実行へ変更する。
3. package buildと一時HOME integration testを追加する。
4. CIへbuild / installer smokeを追加する。
5. README、Quickstart、guide、referenceをuser-local方式へ更新する。
6. automated checksと影響確認済みmanual QAをverificationへ記録する。

## QA Plan

- QA document: `_docs/qa/Core/user-local-install/test-plan.md`
- Risk level: High
- Test strategy:
  - Unit: 既存Python testsでruntime behaviorを維持する。
  - Integration: 一時HOMEとfake systemctl / Python wrapperを用いてinstallerを実行する。
  - E2E: built wheelを専用venv相当へinstallし、CLI entry pointを確認する。
  - Manual QA: dry-run出力、generated unit、既存config保持を確認する。
  - Validator / static check: shell syntax、compile、docs validator、diff checkを実行する。
- AC / INVの対応はQA test-planのTest Matrixを正典とする。
- rollback、既存config、既存service保護をHigh-risk項目として確認する。

## Deployment / Rollout

既存checkout方式の利用者は同じinstallerを再実行してuser-local runtimeへ移行する。初回の新方式install前に既存unitは保持し、
package導入とdoctorが成功した後で新unitへ切り替える。rollbackは直前に保持したunit / environmentを復元して
`systemctl --user daemon-reload`とrestartを行う手順を文書化する。
