# small-bug

## Scenario

`Size < M` の小さなバグ修正。設計判断は自明で、Plan は不要。

## Initial State

- `TODO.md` の Backlog または Ready に `Size: XS` か `Size: S` の Bug タスクがある。
- タスクの `Plan` は `None`。
- `Steps` に対象ファイルと確認手順が直接書かれている。

## Agent Task

タスクの Steps に従ってバグを修正し、必要な最小限の guide / reference 更新だけを行う。

## Expected Documents Touched

- 必須: 対象コードまたは対象ドキュメント
- 任意: `_docs/guide/<Area>/<slug>/usage.md`
- 任意: `_docs/reference/<Area>/<slug>/reference.md`
- 不要: `_docs/plan/<Area>/<slug>/plan.md`

## Expected QA Behavior

- `Risk: Low` なら QA docs は任意。
- Regression risk がある場合は regression test または no-test rationale を残す。

## Expected Intent-derived Invariants

- INV-001: 小規模修正でも既存のユーザー向け挙動を壊さない。

## Expected Test-plan Behavior

- QA test-plan は必須ではない。
- 作成する場合は bug の再発防止条件を AC に紐づける。

## Expected Verification Behavior

- 手動確認または regression test の結果を最終報告に残す。
- QA verification がない場合でも、TODO の AC が満たされた根拠を説明する。

## Expected TODO.md Behavior

- 完了後、対象タスクを `TODO.md` から削除する。
- Done / Archived セクションを作らない。
- 発見した追加作業があれば、新規 ID で Backlog に追加する。

## Expected Validation Outcome

- `validate-todo` が `Plan: None` を許容する。
- `validate-doc-links` が追加・更新リンクの存在を確認できる。
- `validate-qa` は QA docs がない Low risk task をエラーにしない。

## Failure Modes to Watch

- 小規模タスクなのに Area 定義だけのために Plan ディレクトリを作る。
- 完了タスクを Done セクションへ移動する。
- `rm` / `git rm` で不要ファイルを削除する。
