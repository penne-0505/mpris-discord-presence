---
title: Documentation Guide
status: active
draft_status: n/a
created_at: 2025-12-07
updated_at: 2026-06-15
references:
  - "_docs/standards/documentation_guidelines.md"
  - "_docs/standards/documentation_operations.md"
  - "_docs/standards/quality_assurance.md"
  - "_docs/standards/security_for_agents.md"
related_issues: []
related_prs: []
---

# Documentation Guide

**必読:** ドキュメントのアーカイブ運用フローに関する最新ルールは、常に `_docs/standards/documentation_operations.md` を参照して遵守してください。QA / テスト設計の詳細は `_docs/standards/quality_assurance.md` を参照してください。

## このガイドの位置づけ

- このプロジェクトでドキュメントを作成・更新する際の要点をまとめたクイックリファレンスです。
- 詳細な執筆手順は `_docs/standards/documentation_guidelines.md`、運用プロセスは `_docs/standards/documentation_operations.md`、QA の判断基準は `_docs/standards/quality_assurance.md` を確認してください。
- coding agent は `TODO.md`、Plan、Intent、QA test-plan、Verification をつなぎ、変更が decision の Why / Why not / Change freedom に沿っているかを検証します。

## 参照すべき中核ドキュメント

1. **`_docs/standards/documentation_operations.md`**
   - draft / plan / survey から intent への移行、archive 手順、TODO 完了処理、front-matter schema を規定しています。
2. **`_docs/standards/documentation_guidelines.md`**
   - ドキュメント体系、各ディレクトリの役割、テンプレート、更新フローをまとめています。
3. **`_docs/standards/quality_assurance.md`**
   - why-first の decision record、任意の intent-derived invariant、Risk 分類、QA test-plan、verification verdict を定義しています。
4. **`_docs/standards/security_for_agents.md`**
   - secret、外部入力、外部 skill / script、破壊的操作の扱いを定義しています。
5. **テンプレート集 (`_docs/standards/templates/`)**
   - draft / survey / plan / intent / QA / guide / reference の雛形を配置しています。

## Canonical Paths

```text
_docs/draft/<Area>/<slug>/notes.md
_docs/survey/<Area>/<slug>/survey.md
_docs/plan/<Area>/<slug>/plan.md
_docs/intent/<Area>/<slug>/decision.md
_docs/qa/<Area>/<slug>/test-plan.md
_docs/qa/<Area>/<slug>/verification.md
_docs/guide/<Area>/<slug>/usage.md
_docs/reference/<Area>/<slug>/reference.md
_docs/archives/{draft,plan,survey}/<Area>/<slug>/...
```

`<Area>` は `TODO.md` の `Area` と一致させ、`<slug>` は機能・変更単位の kebab-case 名にします。references は root-relative canonical path を推奨します。

```yaml
references:
  - "_docs/intent/Core/feature-x/decision.md"
  - "_docs/plan/Core/feature-x/plan.md"
  - "_docs/qa/Core/feature-x/test-plan.md"
```

## QA Documents

- `test-plan.md` は intent / plan / TODO から作ります。
- `verification.md` は実装後の検証証跡です。
- QA docs は archive しません。
- `_docs/qa/` はテストコードの置き場ではなく、計画・対応表・検証証跡の置き場です。
- 実行可能なテストは、コードベース側の標準的なテストディレクトリに置きます。
- `verification.md` の `qa_status` は本文の `Verdict` と一致させます。

## intent ↔ code traceability

- 設計判断を体現した非自明なコード（とくに why not・意図的な省略）には、intent への参照コメントを残します。全コード義務ではなくターゲット型です。
- 理由へ辿る基本アンカーは `DEC-xxx` です: `// intent: DEC-003 (Workflow/<slug>) — <理由>`。
- strict invariant を体現する場合だけ `// intent-invariant: INV-003 ...` を使います。
- テストで落とせる acceptance criterion または任意の invariant はテスト（AC / INV 名）へ、テスト化しにくい why not は DEC を参照するコメントへ置きます。二重には書きません。
- コメントは decision の What や exact 値を繰り返さず、因果を一行で要約します。
- 参照の有無は validator で強制しません。skill と review で担保します。
- 正典は `_docs/standards/quality_assurance.md` の intent ↔ code traceability です。

## Front-matter クイックリファレンス

全ての運用対象ドキュメントで以下の8項目が必須です。

| フィールド | 説明 |
| --- | --- |
| `title` | ドキュメントのタイトル |
| `status` | `proposed` \| `active` \| `superseded` \| `obsolete` |
| `draft_status` | `idea` \| `exploring` \| `paused` \| `n/a` |
| `created_at` | 作成日 (`YYYY-MM-DD`) |
| `updated_at` | 更新日 (`YYYY-MM-DD`) |
| `references` | 関連ドキュメントへのリンク配列 |
| `related_issues` | 関連 Issue の番号配列。ない場合は `[]`。 |
| `related_prs` | 関連 PR の番号配列。ない場合は `[]`。 |

`_docs/qa/**/*.md` では追加で以下が必須です。

| フィールド | 説明 |
| --- | --- |
| `qa_status` | `planned` \| `in-progress` \| `verified` \| `partial` \| `failed` \| `blocked` |
| `risk` | `Low` \| `Medium` \| `High` \| `Critical` |

新規の why-first 文書では、intent に `intent_schema: 2`、QA に `qa_schema: 2` を追加します。
marker のない既存文書は legacy schema として受理されます。リンク・typo・metadata の修正だけなら
legacy のままでよく、decision の意味または QA 契約を変更する編集から schema v2 へ移行します。

## よくある更新パターン

### 0. 小規模な修正 (`Size XS/S` かつ `Risk Low`)

- Plan / Intent / QA は `None` にできます。
- `TODO.md` の Acceptance Criteria と Steps に従って直接作業します。
- Bug の場合は regression test または no-test rationale を残します。
- 将来の作業者が未実装と誤認しそうな非対応・制限・省略がある場合は、TODO Description / PR / commit に理由を残し、後続変更に影響するなら Intent に昇格します。

### 1. `Size >= M` の変更

- `_docs/plan/<Area>/<slug>/plan.md` を作成します。
- `_docs/intent/<Area>/<slug>/decision.md` を作成します。
- `_docs/qa/<Area>/<slug>/test-plan.md` を実装前または実装中に作成します。
- TODO の `Plan`, `Intent`, `QA` を root-relative canonical path で更新します。

### 2. `Risk >= Medium` の変更

- Intent と QA test-plan が必須です。
- Risk High / Critical では完了前に verification が必須です。
- rollback / recovery / security / data safety の観点を QA に含めます。

### 3. 実装後の verification

```yaml
title: "QA Verification: Feature X"
status: active
draft_status: n/a
qa_status: verified
risk: Medium
created_at: 2026-05-25
updated_at: 2026-05-25
references:
  - "_docs/intent/Core/feature-x/decision.md"
  - "_docs/plan/Core/feature-x/plan.md"
  - "_docs/qa/Core/feature-x/test-plan.md"
related_issues: []
related_prs: []
```

schema v2 の verification には、実行したコマンド、手動 QA、Acceptance Criteria Coverage、影響した DEC の Decision Conformance、該当する場合の Invariant Coverage、Deferred / Not Covered、Residual Risks、Follow-up TODOs、Verification Verdict を残します。

Verdict と `qa_status` は次の対応にします。

| Verdict | qa_status |
| --- | --- |
| `PASS` | `verified` |
| `PARTIAL` | `partial` |
| `FAIL` | `failed` |
| `BLOCKED` | `blocked` |

### 4. plan / draft / survey の archive

- archive 対象は `draft` / `plan` / `survey` のみです。
- 対応 intent が存在し、archive checklist を満たす場合だけ移送できます。
- `intent` と QA docs は archive しません。

### 5. Template release の継続更新

- `docs-template.lock.json` は、最後に統合した upstream release tag と full SHA を記録します。
- moving branch tip ではなく推奨 tag を `U` とし、`docs-template-migration` skill で `B` / `U` / project snapshot を比較します。
- `U` の reconciliation と compatibility checks 後に lock を最後の migration write として更新し、closure verification で確認します。strict schema migration の延期状態は verification に残します。
- pre-`v1.0.0` project は導入元 commit を一度だけ復元し、`v1.0.0` 以降の推奨 tag へ直接移行できます。
- `DD_SCOPE_BASE` は導入先の validator scope であり、template provenance lock の代替にはなりません。

## 検証コマンド

```bash
deno fmt --check scripts/*.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-frontmatter.mjs
deno run --allow-read scripts/validate-todo.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-doc-links.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-intent.mjs
deno run --allow-read --allow-env --allow-run=git scripts/validate-qa.mjs
deno run --allow-read --allow-write --allow-env --allow-run scripts/test-validators.mjs
deno run --allow-read --allow-run=git scripts/test-agent-workflow-hook.mjs
deno run --allow-read scripts/test-agent-workflow-smoke.mjs
```

`--allow-env` / `--allow-run=git` は段階的導入スコープ（`DD_SCOPE_BASE`）向けの権限です。既存プロジェクトへ後付け導入し「導入以降に追加した docs だけ」を検証したい場合は、`_docs/standards/documentation_operations.md` の段階的導入スコープを参照してください。まとめて実行する場合:

```bash
./scripts/check-docs.sh
```

手元で Node.js / npx が使える場合は、markdownlint も実行できます。

```bash
npx markdownlint-cli2 "_docs/**/*.md" "_evals/**/*.md" "README.md" "AGENTS.md" "TODO.md" "QUICKSTART.md" "!_docs/archives/**/*" "!_docs/standards/templates/**/*" --config .markdownlint.jsonc
```

## トラブルシューティング

| 状況 | 対応 |
| --- | --- |
| Plan が必要か分からない | `Size >= M` なら必須。`Size XS/S` かつ `Risk Low` なら省略可。 |
| QA test-plan が必要か分からない | `Size >= M` または `Risk >= Medium` なら必須。 |
| verification verdict が `FAIL` | TODO を削除せず、修正または follow-up TODO を追加する。 |
| verification verdict が `BLOCKED` | blocker と次アクションを記録し、完了扱いにしない。 |
| QA docs を archive したい | archive しない。obsolete / superseded にする。 |
| `references` の相対パスに迷う | root-relative canonical path を使う。 |
