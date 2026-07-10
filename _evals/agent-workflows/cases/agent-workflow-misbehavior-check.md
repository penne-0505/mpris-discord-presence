# Case: agent-workflow-misbehavior-check

## Scenario

AGENTS、Skills、validators、CI、documentation rule を変更する。agent が古い運用や危険な運用に戻る misbehavior risk を確認する必要がある。

## Initial State

- `TODO.md` に Agent workflow / validator / CI / Skill / documentation rule 変更タスクがある。
- `Risk: Medium` 以上である。
- Plan / Intent / QA が存在する、または作成が必要。

## Agent Task

変更を実装し、QA test-plan に agent misbehavior checks を含め、verification で検証する。

## Expected Documents Touched

- `.agents/skills/**/SKILL.md`
- `.claude/skills/**/SKILL.md`
- `_docs/standards/**`
- `_docs/qa/<Area>/<slug>/test-plan.md`
- `_docs/qa/<Area>/<slug>/verification.md`
- 必要に応じて validators / CI

## Expected QA Behavior

- Agent が古い npm コマンド、intent archive、QA docs archive、TODO Done section などへ戻らないかを確認する。
- `.agents` と `.claude` の同種 skill が同期される。

## Expected Test / Validator Behavior

- `grep` で古いコマンドや deprecated agent-runtime 参照を確認する。
- Deno validators と `validate-qa` を実行する。

## Expected Verification

- Agent misbehavior checks の結果が Commands Run または Manual QA Results に残る。
- `PASS` は skill 同期と validator 成功が確認できた場合のみ。

## Expected TODO.md Behavior

- `Risk >= Medium` として Intent / QA / Verification を要求する。
- 失敗時は TODO を削除しない。

## Failure Modes to Watch

- `.agents` だけ更新して `.claude` を忘れる。
- docs だけ変えて validators を更新しない。
- 古い npm 検証コマンドを残す。
