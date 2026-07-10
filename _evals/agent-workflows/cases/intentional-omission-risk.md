# Case: intentional-omission-risk

## Scenario

`Size XS/S` かつ `Risk Low` に見える変更だが、意図的に非対応・制限・省略している挙動がある。将来の作業者が「未実装なので直そう」と誤認する可能性がある。

## Initial State

- `TODO.md` に Fast Track 相当のタスクがある。
- `Plan`, `Intent`, `QA`, `Verification` は `None` にできる規模である。
- ただし、Description や周辺 docs に、意図的な非対応・制限・省略がある。

## Agent Task

Fast Track のまま軽量に進めてよいか、intentional omission risk として設計判断に昇格すべきかを判断する。軽量で足りる場合は TODO Description / PR / commit に理由を残し、後続変更に影響する場合は Intent を作成または更新する。

## Expected Documents Touched

- 軽量記録で足りる場合: `TODO.md` または PR / commit summary。
- 設計判断として残す場合: `_docs/intent/<Area>/<slug>/decision.md`。
- 既存 Plan がある場合: `_docs/plan/<Area>/<slug>/plan.md` の Non-Goals。

## Expected QA Behavior

- `Why not` 専用フィールドは追加しない。
- Validator で semantic な why-not 記述を強制しない。
- Intent に昇格した場合は、intent-derived invariant と QA test-plan を検討する。

## Expected Intent-derived Invariants

- INV-001: Fast Track は小規模変更の軽量性を保つ。
- INV-002: 将来誤修正されやすい intentional omission は理由を追える場所に残す。
- INV-003: 設計判断に昇格した intentional omission は Intent Alternatives / Rationale に記録する。

## Expected TODO.md Behavior

- `Size XS/S` かつ `Risk Low` なら Plan / Intent / QA を常に必須にしない。
- intentional omission risk がある場合は Description に理由を残すか、Intent path を設定する。

## Failure Modes to Watch

- すべての小規模変更に why-not 記録を要求する。
- 意図的な非対応を記録せず、将来の agent が欠落として実装してしまう。
- `scripts/validate-todo.mjs` に semantic な why-not field requirement を追加する。
