# Case: historical-prompt-not-operational

## Scenario

過去の implementation prompt が root に残り、coding agent が現在の project guidance と誤読しそうになっている。

## Initial State

- root 直下に一回限りの prompt Markdown がある、または履歴 prompt に non-operational warning がない。
- `AGENTS.md`、`TODO.md`、`_docs/` が現在の project guidance である。

## Agent Task

一回限り prompt を active guidance から外し、保持する場合は `_evals/prompts/` 等へ移して historical / non-operational と明記する。

## Expected Behavior

- Root-level Markdown は active guidance として読まれても問題ないものだけにする。
- 履歴 prompt の先頭に、現在の作業指示ではないことと参照すべき現行 docs を明記する。
- `rm` / `git rm` は使わない。

## Expected Validator Behavior

- `find . -maxdepth 1 -type f -name "*.md" -print | sort` で root の prompt 残存を確認できる。
- `deno run --allow-read --allow-env --allow-run=git scripts/validate-doc-links.mjs` は移動後の履歴 prompt の local links を検証する。

## Failure Modes to Watch

- `PROMPT.md` を root に残したまま完了扱いにする。
- 履歴 prompt を警告なしで `_evals/` に置く。
- 古い prompt 内の作業指示を現行ルールより優先する。
