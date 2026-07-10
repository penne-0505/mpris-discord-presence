# breaking-change

## Scenario

既存 API やデータ形式を変更する破壊的変更。migration / rollback / compatibility を明記する必要がある。

## Initial State

- `TODO.md` に `Size: M` 以上の Refactor または Enhance タスクがある。
- `Plan` は `_docs/plan/<Area>/<slug>/plan.md` を指す。
- 既存 guide / reference が影響を受ける。

## Agent Task

Plan に migration、rollback、compatibility を追記し、実装後に intent と reference を更新する。

## Expected Documents Touched

- `_docs/plan/<Area>/<slug>/plan.md`
- `_docs/intent/<Area>/<slug>/decision.md`
- `_docs/qa/<Area>/<slug>/test-plan.md`
- `_docs/qa/<Area>/<slug>/verification.md`
- `_docs/reference/<Area>/<slug>/reference.md`
- 必要に応じて `_docs/guide/<Area>/<slug>/usage.md`

## Expected QA Behavior

- Risk is High unless proven otherwise.
- QA test-plan includes rollback / recovery / data safety / compatibility checks.

## Expected Intent-derived Invariants

- INV-001: migration or compatibility decisions in intent are verified.
- INV-002: reference docs do not describe unsupported legacy behavior as active.

## Expected Test-plan Behavior

- Test Matrix maps AC / INV to automated tests, validators, manual QA, or diff review.
- Deferred compatibility checks include a reason and follow-up.

## Expected Verification Behavior

- Verification is required before completion.
- Verdict is not PASS unless migration, rollback, and compatibility evidence are present.

## Expected TODO.md Behavior

- 完了後、対象タスクを `TODO.md` から削除する。
- 移行後の follow-up があれば別 ID で Backlog に追加する。

## Expected Validation Outcome

- `validate-todo` が Size と Plan 要件を満たす。
- `validate-doc-links` が更新 references のリンク切れを検出しない。
- `validate-qa` が QA front-matter、High-risk Checklist、verification verdict を検証する。

## Failure Modes to Watch

- rollback 方針なしで破壊的変更を進める。
- 互換性リスクを intent に残さない。
- 古い reference を active のまま放置する。
