# Case: malformed-todo-heading

## Scenario

`TODO.md` に `### [Feat] Bad task` のような正式形式でない task heading がある。

## Initial State

- Task は `## Backlog`、`## Ready`、または `## In Progress` にある。
- Required fields が一部そろっていても、heading は `### <ID>: [<Category>] <Title>` ではない。

## Agent Task

Validator の失敗を確認し、heading と fields を正式 schema に直す。

## Expected Behavior

- Agent は `Title` field だけで task が valid だと判断しない。
- 正式 heading、`Title` field、`ID` field、`Area` field を同期する。

## Expected Validator Behavior

- `deno run --allow-read scripts/validate-todo.mjs` は malformed heading を error にする。
- `scripts/test-validators.mjs` は malformed-heading fixture が失敗することを確認する。

## Failure Modes to Watch

- `Title` field 起点の parser に戻して heading 不備を見逃す。
- fenced code block 内の heading 例を実 task と誤検出する。
- heading ID と `ID` field の不一致を見逃す。
