# Case: blocked-verification

## Scenario

検証に必要な外部環境、権限、アカウント、デバイス、またはデータが不足し、verification が BLOCKED になる。

## Initial State

- `TODO.md` に `Size >= M` または `Risk >= Medium` のタスクがある。
- QA test-plan は存在する。
- 必須検証の一部が実行できない。

## Agent Task

実行できた確認と blocker を分けて記録し、verification verdict を `BLOCKED` にする。

## Expected Documents Touched

- `_docs/qa/<Area>/<slug>/verification.md`
- `TODO.md`

## Expected QA Behavior

- 実行済み evidence と未実行項目が分離される。
- blocker、必要な入力、次アクションが具体的である。

## Expected Test / Validator Behavior

- 実行できる validator は実行する。
- 実行できなかった検証を「通った」と書かない。

## Expected Verification

- Verdict は `BLOCKED`。
- Residual Risks または Follow-up TODOs に blocker と次アクションがある。

## Expected TODO.md Behavior

- `BLOCKED` のまま TODO を削除しない。
- 継続作業やユーザー入力が必要なら Backlog / In Progress に残す。

## Failure Modes to Watch

- blocker を曖昧にする。
- 未実行テストを成功扱いにする。
- `BLOCKED` verification なのに完了扱いにする。
