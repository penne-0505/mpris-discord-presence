---
title: "QA Verification: User-local installation"
status: active
draft_status: n/a
qa_status: verified
risk: High
created_at: 2026-07-11
updated_at: 2026-07-11
references:
  - "_docs/intent/Core/user-local-install/decision.md"
  - "_docs/plan/Core/user-local-install/plan.md"
  - "_docs/qa/Core/user-local-install/test-plan.md"
related_issues: []
related_prs: []
---

# QA Verification: `User-local installation`

## Summary

専用user-local venv、versioned runtime切替、checkout非依存unit、config保持、staging失敗時のfailure safety、
直前runtimeと移行前unitへのrollbackを実装した。temporary HOME / XDG pathsとfake systemctlでintegration testを行い、
既存runtime、package build、documentation checksを確認した。

## Verification Verdict

Verdict: PASS

## Commands Run

| Command / Test | Result | Notes |
| --- | --- | --- |
| `bash -n scripts/install-user-service.sh scripts/test-install-user-service.sh` | PASS | installer / integration test syntax。 |
| `./scripts/test-install-user-service.sh` | PASS | temporary HOMEでinstall、migration rollback、update、failure safety、runtime rollbackを確認。 |
| `PYTHONPATH=src python -m unittest -v` | PASS | 69 tests。 |
| `python -m compileall -q src tests` | PASS | Python modulesをcompile。 |
| `python -m build --outdir /tmp/mpris-discord-presence-user-local-build` | PASS | sdist / wheelをisolated build。 |
| wheel content listing | PASS | application Python packageとmetadata / licenseのみ。GI binaryなし。 |
| `./scripts/check-docs.sh` | PASS | TODO、frontmatter、links、QA、fixtures。 |
| `npx --yes markdownlint-cli2 ...` | PASS | 49 active Markdown files、0 errors。 |
| `git diff --check` | PASS | whitespace errorなし。 |
| `systemd-analyze verify <generated-unit>` | PASS with environment warning | unit固有errorなし。隔離したunit search pathのため`sysinit.target`不在warning。 |
| isolated `--dry-run` | PASS | pathsを表示し、temporary rootを変更しない。 |
| `shellcheck` | NOT RUN | localにshellcheckがない。bash syntaxとintegration testで代替。 |

## Automated Test Results

- User-local installer integration: PASS
- Existing Python unit tests: PASS (69 tests)
- Distribution build: PASS
- Documentation validators / lint: PASS

## Manual QA Results

- generated unitは専用venvのentry pointを参照し、checkout pathと`PYTHONPATH`を含まない。
- configは初回mode `0600`、再install後もsentinel contentを保持した。
- staging failure後にactive runtime symlinkとunitが同一であることを確認した。
- migration前unit / environmentと直前versioned runtimeの双方へrollbackできた。
- live user serviceとDiscord / MPRIS sessionは、runtime機能を変更していないため実行対象外とした。

## Acceptance Criteria Coverage

- AC-001: PASS — system-site-packages venvとinstalled CLIをintegration testで確認。
- AC-002: PASS — generated unitにcheckout path / `PYTHONPATH`がない。
- AC-003: PASS — config保持、staging failure、migration rollbackをsentinelで確認。
- AC-004: PASS — README / Quickstart / guide / referenceをinstall / update / rollbackとsupport境界へ同期。
- AC-005: PASS — installer integrationを追加し、GitHub Actions test workflowへ組み込んだ。

## Invariant Coverage

- INV-001: PASS — serviceは専用venv entry pointとuser config / environmentだけを参照。
- INV-002: PASS — initial mode `0600`とreinstall content preservationを確認。
- INV-003: PASS — failing Python wrapperでstaging failure後のruntime / unit保持を確認。
- INV-004: PASS — `pyvenv.cfg`とwheel listingでsystem-site-packages / no GI vendorを確認。
- INV-005: PASS — 公開文書がArch Linux / EndeavourOS＋公式Discord clientへ限定。

## Deferred / Not Covered

- GitHub-hosted Actions自体はpush前のため未実行。workflowと同じlocal commandsはPASS。
- live Discord / MPRIS behaviorはinstall境界変更のOut of Scopeであり、既存69 testsによるbehavior preservationを確認した。

## Residual Risks

None

## Follow-up TODOs

None
