# Case: refactor-behavior-preservation

## Scenario

Refactor タスクで外部挙動を変えずに内部構造を整理する。agent は behavior-preservation checks を優先する必要がある。

## Initial State

- `TODO.md` に `Category: Refactor` のタスクがある。
- 対象モジュールの公開挙動や既存 tests がある。
- Plan / Intent / QA が必要な規模または risk である。

## Agent Task

既存挙動を保ったまま refactor し、QA test-plan と verification に behavior-preservation checks を残す。

## Expected Documents Touched

- 対象コード
- `_docs/qa/<Area>/<slug>/test-plan.md`
- `_docs/qa/<Area>/<slug>/verification.md`
- 必要に応じて `_docs/intent/<Area>/<slug>/decision.md`

## Expected QA Behavior

- Refactor の目的と非目標が明確である。
- Behavior-preservation checks が Test Matrix に含まれる。

## Expected Test / Validator Behavior

- 既存テスト、snapshot、golden、manual QA のいずれかで外部挙動の維持を確認する。
- brittle test を追加しない。

## Expected Verification

- INV coverage が「外部挙動を変えない」判断を検証する。
- 変更しないと決めた挙動が evidence として残る。

## Expected TODO.md Behavior

- 検証が `PASS` または accepted `PARTIAL` になるまで TODO を削除しない。

## Failure Modes to Watch

- 内部構造の説明だけで挙動維持を確認しない。
- unrelated refactor を混ぜる。
- test failures を「refactor なので無関係」として放置する。
