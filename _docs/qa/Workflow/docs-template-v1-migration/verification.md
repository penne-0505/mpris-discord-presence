---
title: "QA Verification: docs-driven template v1.0.0 migration"
status: active
draft_status: n/a
qa_status: verified
risk: High
qa_schema: 2
created_at: 2026-07-22
updated_at: 2026-07-22
references:
  - "_docs/intent/Workflow/docs-template-v1-migration/decision.md"
  - "_docs/archives/plan/Workflow/docs-template-v1-migration/plan.md"
  - "_docs/qa/Workflow/docs-template-v1-migration/test-plan.md"
related_issues: []
related_prs: []
---

# QA Verification: docs-driven template v1.0.0 migration

## Summary

`B=ebb098e4536d28d834ef8ecbf9686906a5b23d41`、`P=2a2f9ab583b46cb4e1d43ebcbbc33c8d0644ebe1`、`U=v1.0.0 / f71e9ab20466ea2972158334261f5ae2b2265754` のthree-way inventoryに従い、v1.0.0 workflowをisolated worktreeへ統合した。

## Verification Verdict

Verdict: PASS

- Compatibility migration: PASS。legacy Core docsとschema-v2 migration docsが同じvalidator setで受理される。
- Strict schema migration: scope外。既存Core docsはsemantic reviewなしに一括変換せず、legacy-compatible recordとして保持した。

## Commands Run

```bash
./scripts/check-docs.sh
deno run --allow-read --allow-write --allow-env --allow-run scripts/test-validators.mjs
deno run --allow-read --allow-run=git scripts/test-agent-workflow-hook.mjs
deno run --allow-read scripts/test-agent-workflow-smoke.mjs
deno fmt --check scripts/*.mjs
npx --yes markdownlint-cli2 "_docs/**/*.md" "_evals/**/*.md" "README.md" "AGENTS.md" "TODO.md" "QUICKSTART.md" "!_docs/archives/**/*" "!_docs/standards/templates/**/*" --config .markdownlint.jsonc
for d in .agents/skills/*; do n=$(basename "$d"); cmp "$d/SKILL.md" ".claude/skills/$n/SKILL.md"; done
PYTHONPATH=src python -m unittest -v
python -m compileall -q src tests
uv build --out-dir /tmp/docs-template-v1-rollout/dist
./scripts/test-install-user-service.sh
git -C /home/penne/dev/tools/templates/docs_driven_dev_template rev-parse 'v1.0.0^{}'
deno eval 'const x=JSON.parse(await Deno.readTextFile("docs-template.lock.json")); console.log(x.revision.commit)'
git diff --check
git diff --name-only -- src tests scripts/install-user-service.sh scripts/test-install-user-service.sh packaging pyproject.toml config.example.toml .github/workflows/tests.yml
```

Result: all commands passed。upstream template repositoryで解決したtagとlockはいずれも`f71e9ab20466ea2972158334261f5ae2b2265754`だった。Python unit testsは69件PASS。system Pythonに`pip` moduleがなかったため、documented CIのwheel command相当は`uv build`でsdistとwheelを生成して確認した。

## Automated Test Results

| Command / Test | Result | Notes |
| --- | --- | --- |
| docs wrapper、validator fixtures、hooks、smoke | PASS | legacy/v2共存、migration provenance、agent misbehavior checksを確認。 |
| Deno format、markdownlint、paired skill cmp、diff check | PASS | lint 0 issue、paired tree一致。 |
| Python unittest、compileall | PASS | 69 tests、compile errorなし。 |
| `uv build`、installer integration | PASS | sdist/wheel生成、staged install/reinstall/rollback PASS。 |
| runtime/project-only path diff | PASS | source、tests、installer、unit、project CIに内容差分なし。 |

## Manual QA Results

| Checklist Item | Result | Notes |
| --- | --- | --- |
| provenance | PASS | `/home/penne/dev/tools/templates/docs_driven_dev_template`で`git rev-parse 'v1.0.0^{}'`を実行し、lock full SHAとの一致を確認。 |
| customization | PASS | user-local runtime、Arch系＋公式Discord、privacy/security記述を保持。 |
| meta-work exclusion | PASS | upstream `Workflow/lifecycle-self-audit` docsを未導入。 |
| scope isolation | PASS | existing checkout、live service、remoteを操作していない。 |

## Acceptance Criteria Coverage

| ID | Result | Evidence |
| --- | --- | --- |
| AC-001 | PASS | Plan inventory、lock、tag resolution。 |
| AC-002 | PASS | wrapper、fixtures、hooks、paired skill checks。 |
| AC-003 | PASS | path diff 0、project regression tests。 |
| AC-004 | PASS | compatibility PASSとstrict non-goalを別記。 |
| AC-005 | PASS |全closure commands PASS。 |

## Decision Conformance

| ID | Result | Why the implementation remains aligned |
| --- | --- | --- |
| DEC-001 | PASS | B/U/Pと全path resolutionを固定した。 |
| DEC-002 | PASS | 新規recordsだけv2、既存Core docsはlegacyのまま。 |
| DEC-003 | PASS | runtime/project-only blobを変更していない。 |
| DEC-004 | PASS | hook commentsを到達可能なdecisionへ付け替え、unit / smokeで監査境界を確認した。 |

## Invariant Coverage

| ID | Result | Evidence |
| --- | --- | --- |
| INV-001 | PASS | lock tag/full SHAとlocal tag resolution一致。 |
| INV-002 | PASS | scoped `git diff --name-only`出力なし。 |

## Deferred / Not Covered

| ID | Reason | Follow-up |
| --- | --- | --- |
| strict schema migration of legacy Core docs | semantic reviewなしのbulk editを禁止したため | 各decisionを変更する将来taskで必要に応じてv2化する。 |
| live Discord/service QA | runtime behavior変更なし、利用者影響を避けるため | 不要。runtime変更taskで実施する。 |
| frontmatter schema marker warning | v1.0.0 frontmatter validatorはmarkerをunknown field warningとして表示するが、intent/QA validatorsはv2を検証しwrapperはPASSする | upstream compatibility behaviorとして保持する。 |

## Residual Risks

- None

## Follow-up TODOs

- None
