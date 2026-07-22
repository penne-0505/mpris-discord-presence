# Case: qa-prep-from-intent

## Scenario

`Size >= M` のタスクで、Plan と Intent は存在するが QA test-plan が未作成。agent は intent の判断と必要な invariant から QA 計画を作る必要がある。

## Initial State

- `TODO.md` に `Size: M` 以上または `Risk: Medium` 以上のタスクがある。
- `Plan` は `_docs/plan/<Area>/<slug>/plan.md` を指す。
- `Intent` は `_docs/intent/<Area>/<slug>/decision.md` を指す。
- `QA` は `None` または未作成 path を指す。

## Agent Task

`qa-prep` を実行し、TODO / Plan / Intent から `_docs/qa/<Area>/<slug>/test-plan.md` を作成する。

## Expected Documents Touched

- `_docs/qa/<Area>/<slug>/test-plan.md`
- `TODO.md`

## Expected QA Behavior

- Quality Goal が intent の判断に紐づいている。
- Decision Review Scope に影響を受ける `DEC-*` が列挙されている。
- Intent-derived Invariants は Intent に `INV-*` がなければ `None` である。
- Risk Assessment が TODO の `Risk` と一致している。

## Expected Test / Validator Behavior

- `validate-qa` が QA front-matter、references、Test Matrix を検証できる。
- `validate-todo` が `QA` path と Area 一致を検証できる。

## Expected Verification

- 実装前なので verification は `None` でよい。
- Deferred がある場合は理由を残す。

## Expected TODO.md Behavior

- `QA` フィールドが `_docs/qa/<Area>/<slug>/test-plan.md` に更新される。
- タスクは完了扱いにしない。

## Failure Modes to Watch

- intent を読まずに一般的なテスト項目だけを書く。
- Test Matrix に AC がない、または Intent に存在しない INV を作る。
- references に root-relative canonical path を使わない。
