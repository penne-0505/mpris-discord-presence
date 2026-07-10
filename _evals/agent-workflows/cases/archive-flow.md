# archive-flow

## Scenario

対応 intent が存在する一時ドキュメントを archives に移送する。

## Initial State

- `_docs/intent/<Area>/<slug>/decision.md` が存在する。
- `_docs/draft/<Area>/<slug>/notes.md`、`_docs/plan/<Area>/<slug>/plan.md`、または `_docs/survey/<Area>/<slug>/survey.md` が存在する。
- intent の `references` に live path または archive target を追加できる状態。

## Agent Task

archive checklist を満たすことを確認し、対象一時ドキュメントを `_docs/archives/{draft,plan,survey}/<Area>/<slug>/...` に移送する。

## Expected Documents Touched

- `_docs/intent/<Area>/<slug>/decision.md`
- `_docs/archives/draft/<Area>/<slug>/notes.md`
- `_docs/archives/plan/<Area>/<slug>/plan.md`
- `_docs/archives/survey/<Area>/<slug>/survey.md`

## Expected QA Behavior

- QA docs are not moved to `_docs/archives/`.
- Existing verification records remain linked from live QA paths.

## Expected Intent-derived Invariants

- INV-001: intent documents are permanent and must not be archived.
- INV-002: QA documents are persistent quality records and must not be archived.
- INV-003: archive targets are limited to draft / plan / survey.

## Expected Test-plan Behavior

- No new QA test-plan is required for the archive operation unless the cleanup task is Risk >= Medium.
- If a QA test-plan exists, it keeps root-relative references to the intent and archive-relevant documents.

## Expected Verification Behavior

- Verification records any archive checklist commands or manual checks.
- `FAIL` / `BLOCKED` verification prevents TODO removal.

## Expected TODO.md Behavior

- archive cleanup タスクが完了したら `TODO.md` から削除する。
- 残作業がある場合だけ Backlog に follow-up を追加する。

## Expected Validation Outcome

- `validate-doc-links` が対応 intent の存在を確認する。
- archive 済みの同一 `<Area>/<slug>` について、live path に同じ一時ドキュメントが残っていない。
- `validate-qa` が QA docs を archive 対象として扱わない。

## Failure Modes to Watch

- `rm` / `git rm` を使う。
- intent を archive する。
- live path と archive path に同じ文書を重複させる。
- intent references を更新しない。
