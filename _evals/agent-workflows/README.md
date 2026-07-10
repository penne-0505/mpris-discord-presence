# Agent Workflow Evals

このディレクトリは、自動テストというより agent 行動の回帰確認用 golden task 集です。Codex、Claude Code、汎用 coding agent に同じケースを渡したとき、`TODO.md` と `_docs/` の運用規約を守れるかを確認します。

各ケースは同じ構造で書かれています。

- scenario
- initial state
- agent task
- expected documents touched
- expected QA behavior
- expected intent-derived invariants
- expected test-plan behavior
- expected verification behavior
- expected TODO.md behavior
- expected test / validator behavior
- failure modes to watch

将来は、ケースごとの期待差分を固定し、promptfoo や独自 runner に接続して自動比較できる形へ拡張できます。現時点では、人間が agent の出力と差分をレビューするための基準として使います。

## Cases

- [small-bug](cases/small-bug.md)
- [medium-feature](cases/medium-feature.md)
- [breaking-change](cases/breaking-change.md)
- [stale-draft-cleanup](cases/stale-draft-cleanup.md)
- [archive-flow](cases/archive-flow.md)
- [qa-prep-from-intent](cases/qa-prep-from-intent.md)
- [intentional-omission-risk](cases/intentional-omission-risk.md)
- [bug-regression-test](cases/bug-regression-test.md)
- [refactor-behavior-preservation](cases/refactor-behavior-preservation.md)
- [high-risk-change-verification](cases/high-risk-change-verification.md)
- [agent-workflow-misbehavior-check](cases/agent-workflow-misbehavior-check.md)
- [blocked-verification](cases/blocked-verification.md)
- [malformed-todo-heading](cases/malformed-todo-heading.md)
- [qa-status-verdict-mismatch](cases/qa-status-verdict-mismatch.md)
- [historical-prompt-not-operational](cases/historical-prompt-not-operational.md)

## Expected Invariants

全ケース共通の不変条件は [expected-invariants.md](expected-invariants.md) を参照してください。
