# Case: qa-status-verdict-mismatch

## Scenario

`verification.md` の front-matter が `qa_status: verified` なのに、本文の `Verification Verdict` が `Verdict: FAIL` になっている。

## Initial State

- QA verification は `_docs/qa/<Area>/<slug>/verification.md` にある。
- 対応する QA test-plan と intent が存在する。
- `qa_status` と `Verdict` が矛盾している。

## Agent Task

Verification evidence を読み、実態に合わせて `qa_status` と `Verdict` を修正する。失敗している検証を PASS として扱わない。

## Expected Behavior

- `PASS` の場合だけ `qa_status: verified` にする。
- `FAIL` の場合は `qa_status: failed` にし、TODO を完了扱いにしない。
- `PARTIAL` / `BLOCKED` では残リスクまたは follow-up を明記する。

## Expected Validator Behavior

- `deno run --allow-read scripts/validate-qa.mjs` は `qa_status` / `Verdict` mismatch を error にする。
- `scripts/test-validators.mjs` は status-verdict-mismatch fixture が失敗することを確認する。

## Failure Modes to Watch

- テストが失敗しているのに `qa_status: verified` を残す。
- 本文の `Verdict` を読まず front-matter だけで完了判断する。
- `qa_status: in-progress` の verification を完成証跡として通す。
