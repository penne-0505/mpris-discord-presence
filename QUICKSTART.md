# Quickstart

このテンプレートは、人間と Codex / Claude Code / 汎用 coding agent が `TODO.md` と `_docs/` を読みながら開発を進めるための土台です。最初のセットアップでは、プロジェクト固有情報に置き換えることと、agent が迷わない入口を残すことを優先してください。

## 1. 最初に読むファイル

- [AGENTS.md](AGENTS.md)
- [TODO.md](TODO.md)
- [_docs/documentation_guide.md](_docs/documentation_guide.md)
- [_docs/standards/documentation_guidelines.md](_docs/standards/documentation_guidelines.md)
- [_docs/standards/documentation_operations.md](_docs/standards/documentation_operations.md)
- [_docs/standards/quality_assurance.md](_docs/standards/quality_assurance.md)
- [_docs/standards/security_for_agents.md](_docs/standards/security_for_agents.md)

## 2. 初回セットアップ

1. [README.md](README.md) をプロジェクト名、目的、使用方法に合わせて書き換える。
2. [LICENSE.txt](LICENSE.txt) の著作者表示を確認し、必要に応じて更新する。
3. [AGENTS.md](AGENTS.md) をプロジェクト固有のコマンド、禁止事項、実行環境に合わせて調整する。
4. [TODO.md](TODO.md) の初期タスクを確認し、不要なテンプレート用タスクは完了後に削除する。
5. TODO の `Risk` を確認し、`Size >= M` または `Risk >= Medium` のタスクでは Plan / Intent / QA test-plan を用意する。
6. 実装後、必要な verification を `_docs/qa/<Area>/<slug>/verification.md` に残す。
7. 一回限りの実装プロンプトを root に残さない。残す必要がある場合は `_evals/prompts/` 等に移し、非運用の履歴資料として明記する。

### Agent lifecycle hooks

このテンプレートは Codex / Claude Code 向けの lifecycle hook を同梱しています。

- Codex: [.codex/hooks.json](.codex/hooks.json)
- Claude Code: [.claude/settings.json](.claude/settings.json)
- 共通 script: [scripts/agent-workflow-hook.mjs](scripts/agent-workflow-hook.mjs)

hook は docs を自動更新しません。SessionStart で workflow context を再注入し、Stop で `qa-review` / `docs-cleanup` / `check-docs` の見落としを促し、PreToolUse で `rm` / `git rm` / file deletion / sensitive file 操作を止めます。

初回利用時は各 agent の `/hooks` で内容を確認し、信頼してください。不要な場合は、hook 設定を無効化または削除してから使います。

### Documentation inventory

久しぶりの再開、handoff 探索、または docs が形だけになっていないか確認したい場合は、`docs-inventory` skill を使います。`docs-inventory` は read-only の棚卸しであり、archive や TODO 削除は行いません。整理を実行する場合は、棚卸し結果を確認してから `docs-cleanup` に進みます。

### 既存プロジェクトへ後付け導入する場合

既存 docs を一斉に検証対象にしないため、段階的導入スコープを設定します。

1. 導入時点の commit SHA または tag を baseline として控える。
2. CI の環境変数に `DD_SCOPE_BASE: <baseline commit>` を設定する。これで、導入以降に**追加された** docs だけが検証対象になり、既存 docs には手を入れずに済む。
3. 既存 docs を編集した時点で検証対象にしたい場合だけ、`DD_SCOPE_DIFF_FILTER=ACMR` を追加する。
4. `actions/checkout` で `fetch-depth: 0` を設定し、baseline commit を参照できるようにする。
5. スコープ対応 validator の実行に `--allow-env`（git 使用時はさらに `--allow-run=git`）を付与する。`scripts/check-docs.sh` は設定済み。
6. `TODO.md` は段階導入でも常に全体が検証対象である点に注意する。

詳細は [段階的導入スコープ](_docs/standards/documentation_operations.md) を参照してください。

## 3. Agent に渡す初回プロンプト例

### Codex

```text
AGENTS.md、TODO.md、_docs/documentation_guide.md、_docs/standards/ を読んで、このリポジトリのドキュメント駆動開発ルールを把握してください。まず TODO.md の Backlog を確認し、最初に着手すべき小さなタスクを提案してください。
```

```text
qa-prepを実行して、対象タスクのintent-derived invariantとtest matrixを作成してください。
```

```text
実装後、qa-reviewを実行してverification verdictを出してください。
```

```text
docs-inventoryを実行して、TODO、intent、QA、guide、reference、draft/plan/surveyの棚卸しをしてください。自動整理はせず、次に判断すべき点を1-3件に絞ってください。
```

### Claude Code

```text
Read AGENTS.md, TODO.md, and _docs/documentation_guide.md first. Follow the documentation operations and security standard. Do not delete files with rm or git rm. Start by reviewing the initial TODO items and propose the first safe change.
```

### Generic Agent

```text
Use TODO.md as the task source of truth. For Size >= M or Risk >= Medium tasks, require Plan / Intent / QA test-plan. Keep intent and QA documents permanent, archive only draft/plan/survey after the archive checklist, and remove completed tasks from TODO.md only after verification.
```

## 4. 最初に完了すべき TODO

- `Docs-Chore-1`: [AGENTS.md](AGENTS.md) の確認とプロジェクト固有化
- `Docs-Chore-2`: [README.md](README.md) のプロジェクト固有化
- `Docs-Chore-3`: [LICENSE.txt](LICENSE.txt) の著作者表示確認
- `Workflow-Chore-7`: 既存プロジェクトへ後付け導入する場合のみ、導入スコープ（`DD_SCOPE_BASE`）を設定（新規プロジェクトでは不要）

完了したタスクは [TODO.md](TODO.md) から削除します。Done / Archived セクションは作りません。

## 5. 検証コマンド

```bash
deno fmt --check scripts/*.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-frontmatter.mjs
deno run --allow-read scripts/validate-todo.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-doc-links.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-qa.mjs
deno run --allow-read --allow-write --allow-env --allow-run scripts/test-validators.mjs
deno run --allow-read --allow-run=git scripts/test-agent-workflow-hook.mjs
deno run --allow-read scripts/test-agent-workflow-smoke.mjs
```

`--allow-env` / `--allow-run=git` は段階的導入スコープ（`DD_SCOPE_BASE`）向けの権限です。スコープ未設定なら全走査の従来挙動になります。まとめて実行する場合:

```bash
./scripts/check-docs.sh
```

CI では markdownlint と上記 Deno validator を実行します。手元で Node.js / npx が使える場合は、次の markdownlint も実行できます。

```bash
npx markdownlint-cli2 "_docs/**/*.md" "_evals/**/*.md" "README.md" "AGENTS.md" "TODO.md" "QUICKSTART.md" "!_docs/archives/**/*" "!_docs/standards/templates/**/*" --config .markdownlint.jsonc
```

## 6. 配布用 ZIP

テンプレートを配布する場合は、`.git` や `.jj` などの VCS メタデータを含めないでください。GitHub 標準アーカイブ、または次のコマンドを使います。

```bash
scripts/create-template-archive.sh docs_driven_dev_template.zip
```
