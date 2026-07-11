---
title: User-local installation decision
status: active
draft_status: n/a
created_at: 2026-07-11
updated_at: 2026-07-11
references:
  - "_docs/plan/Core/user-local-install/plan.md"
  - "_docs/qa/Core/user-local-install/test-plan.md"
related_issues: []
related_prs: []
---

# User-local installation decision

## Context

既存serviceはcheckoutの絶対pathと`PYTHONPATH=src`をunitへ埋め込むため、checkoutの移動・削除で停止する。
第三者が検証済みtagから導入し、その後repositoryをruntimeとして保守し続けなくても動く再現可能な経路が必要である。
一方、PyGObjectとPlayerctl typelibはArch系OS packageとして提供され、Python packageへbinary vendorしない境界がある。

## Decision

- runtimeは`~/.local/share/mpris-discord-presence/venv`の専用venvへ導入する。
- venvはOS packageのPyGObject / Playerctlを参照するため`--system-site-packages`付きで作成する。
- installerは現在のcheckoutからwheelをbuildし、staging venvへinstallしてからruntime pathへ反映する。
- service unitは専用venv内の`mpris-discord-presence` entry pointを実行し、checkoutと`PYTHONPATH`を参照しない。
- configは`$XDG_CONFIG_HOME/mpris-discord-presence/config.toml`に置き、既存値を上書きしない。
- support対象はArch Linux / EndeavourOSと公式Discord clientに限定する。

## Alternatives

- `pip install --user`: user siteの他packageと依存関係が混在し、実行先の固定が弱いため不採用。
- checkout常駐: 最小だがcheckoutの状態がruntimeへ直結し、再現可能な導入物として扱いにくいため置換する。
- fully isolated venv: PyGObject / PlayerctlのOS packageを参照できずbinary vendor境界と両立しないため不採用。
- AUR / distribution package: 再現性は高いが、今回のsource repositoryからの最小導入経路を越えるため対象外。

## Rationale

専用venvはPython packageの配置とsystemdの実行先を一意にでき、user siteを汚染しない。
`--system-site-packages`は隔離を弱めるが、OS管理のGI bindingsを再build / vendorせず利用するために必要である。
staging後の切替により、buildまたはinstall失敗が既存serviceを直ちに破損する可能性を抑える。

## Consequences / Impact

- installerはbuild frontend、venv、pip、user-local pathの管理を担う。
- installed packageの更新には検証済みtagをcheckoutしてinstallerを再実行する。
- OS側Python ABIまたはGI package更新後はvenv再作成が必要になる場合がある。
- 他distributionやsandboxed / unofficial Discord clientの動作は保証しない。
- checkout方式からの移行時にunit内容が変わるためrollback手順を保持する。

## Quality Implications

- 導入成功後のunitにcheckout pathまたは`PYTHONPATH`が残ってはならない。
- configやApplication IDをinstallerの更新処理で破壊してはならない。
- stagingが失敗した場合に既存の動作可能なunitを置換してはならない。
- support対象外を一般的なLinux対応として表示してはならない。

## Intent-derived Invariants

- INV-001: installed serviceは専用venvのentry pointとuser configだけをruntime入力とし、source checkoutを参照しない。
- INV-002: 既存configはinstall / updateで上書きされず、初回生成時だけmode `0600`で作成される。
- INV-003: package buildまたはstaging installが失敗した場合、既存service unitとenvironmentは変更されない。
- INV-004: 専用venvは`--system-site-packages`を使用し、PyGObject / Playerctlをrepoまたはwheelへvendorしない。
- INV-005: 公開手順はArch Linux / EndeavourOSと公式Discord clientだけをsupport対象として明記する。

## Enforced in (optional)

- INV-001: `scripts/install-user-service.sh`、`packaging/systemd/mpris-discord-presence.service.in`
- INV-002: `scripts/install-user-service.sh` integration tests
- INV-003: `scripts/install-user-service.sh` integration tests
- INV-004: venv creation integration test、package contents review
- INV-005: `README.md`、`QUICKSTART.md`

## Rollback / Follow-ups

移行前unitとenvironmentをbackupし、新unitで起動できない場合に復元できる手順をguideへ記載する。
PyPI、AUR、他distribution supportは今回の完了条件に含めず、必要になった時点で別のintentとして判断する。
