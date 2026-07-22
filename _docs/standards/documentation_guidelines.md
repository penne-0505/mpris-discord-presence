# ドキュメント整備指針

**ドキュメンテーションでわからないことがあれば、まずこのファイルを確認してください。**

**アーカイブ運用フローは `_docs/standards/documentation_operations.md` に定義されたルールに必ず従ってください。**

## 概要

本指針は、このプロジェクトにおけるドキュメント作成・管理・メンテナンスの統一的な方針を定めるものです。運用プロセスや自動化の詳細は `_docs/standards/documentation_operations.md`、QA の判断基準は `_docs/standards/quality_assurance.md` を参照し、本書では日々の執筆・更新の実務指針にフォーカスします。

## 関連ドキュメント

- `_docs/standards/documentation_operations.md`: draft / plan / survey / intent / QA / archive を中心とした運用ルール。
- `_docs/standards/quality_assurance.md`: intent-derived invariant、risk 分類、QA test-plan、verification verdict の標準。
- `_docs/standards/security_for_agents.md`: LLM / coding agent の安全な操作標準。
- `_docs/documentation_guide.md`: ドキュメント執筆者向けのクイックガイド。

## ドキュメントの目的

1. **新メンバー・対象領域外の人が仕様・用法を理解するため**（主目的）
2. **実装上の意図を明確にするため**
3. **設計判断が守られているかを検証するため**
4. **汎用的な参考資料として**

## ディレクトリ構造と役割

```text
_docs/
├── guide/<Area>/<slug>/usage.md          # 使用方法・運用指針・ベストプラクティス・トラブルシューティング
├── reference/<Area>/<slug>/reference.md  # API仕様・詳細リファレンス・簡易的内部実装説明
├── plan/<Area>/<slug>/plan.md            # 実装計画・仕様書（intentに昇華する原典）
├── intent/<Area>/<slug>/decision.md      # 実装意図・背景・判断理由（ADR的な用途）
├── qa/<Area>/<slug>/test-plan.md         # intent / plan / TODO から導いたQA計画
├── qa/<Area>/<slug>/verification.md      # 実装後の検証証跡
├── survey/<Area>/<slug>/survey.md        # 機能調査・技術比較・検証レポート
├── draft/<Area>/<slug>/notes.md          # メモ・草案置き場（正式化前の作業用）
├── standards/                            # 開発ガイドライン・プロジェクト標準
├── archives/                             # draft / plan / survey の保管庫
```

実ファイルは以下の canonical path に従う。

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

`<Area>` は `TODO.md` の `Area` と一致させる。`<slug>` は機能・変更単位の kebab-case 名にする。references は root-relative canonical path を推奨する。

## ドキュメント種別

### `_docs/plan/<Area>/<slug>/plan.md`

- **目的**: 実装計画・技術仕様の単一参照点。
- **読者**: 実装背景を理解したい開発者・新メンバー。
- **内容**: Scope / Non-Goals / Requirements / Tasks / QA Plan / Deployment。
- **QA**: `Size >= M` では `_docs/qa/<Area>/<slug>/test-plan.md` を作成し、Plan から参照する。
- **ライフサイクル**: intent に昇華する原典として扱い、archive checklist を満たす場合のみ archives へ移送できる。

### `_docs/intent/<Area>/<slug>/decision.md`

- **目的**: 将来の変更者が実装上の意図、判断理由、変更可能範囲を再構成するための記録。
- **読者**: 設計判断の背景を理解したい開発者。
- **内容**: Context / DEC-ID 付き Decisions（What / Why / Change freedom、必要な Why not / Revisit when）/ Consequences / Quality Implications / 任意の Intent-derived Invariants。
- **QA**: intent は QA の一次資料であり、変更が影響する DEC を review する。実装方式を越えて守る結果がある場合だけ invariant を抽出する。
- **ライフサイクル**: 恒久的な設計判断ログとして保持し、archives へ移送しない。テンプレート repo 自身の meta-work に対する例外は `_docs/standards/documentation_operations.md` を参照する。

### `_docs/qa/<Area>/<slug>/test-plan.md`

- **目的**: intent / plan / TODO から、品質上守るべき条件と確認手段を設計する。
- **読者**: 実装者、レビュアー、QA 担当、coding agent。
- **内容**: Source of Intent / Quality Goal / Acceptance Criteria / Decision Review Scope / 任意の Intent-derived Invariants / Risk Assessment / Test Matrix。
- **作成条件**: `Size >= M` または `Risk >= Medium` で必須。
- **ライフサイクル**: QA docs は persistent quality records であり、archives へ移送しない。obsolete な場合は `status: obsolete` または `status: superseded` にする。テンプレート repo 自身の meta-work に対する例外は `_docs/standards/documentation_operations.md` を参照する。

### `_docs/qa/<Area>/<slug>/verification.md`

- **目的**: 実装後の検証証跡を残す。
- **読者**: レビュアー、運用担当、将来の保守者。
- **内容**: 実行コマンド、手動 QA、AC coverage、Decision Conformance、該当する INV coverage、Deferred、Residual Risks、Follow-up TODOs、Verification Verdict。
- **完了条件**: `Size >= M` または `Risk >= Medium` の TODO を完了する前に作成する。`Risk High / Critical` では特に必須。
- **ライフサイクル**: archive しない。古くなった場合は status を更新し、後継 verification を references で示す。

### `_docs/guide/<Area>/<slug>/usage.md`

- **目的**: 実際の開発・運用シナリオでの使い方を学ぶ。
- **読者**: 新メンバー・対象領域外の人。
- **内容**: 基本的な使用方法、手順、ベストプラクティス、トラブルシューティング。
- **QA**: ユーザー向け挙動や保証範囲が変わる場合は verification を参照する。

### `_docs/reference/<Area>/<slug>/reference.md`

- **目的**: API / 仕様を確認する辞書的用途。
- **読者**: 実装時に詳細仕様を調べたい開発者。
- **内容**: クラス・メソッド・データモデル・エラー仕様・例。
- **QA**: 保証範囲や既知の残リスクがある場合は verification を参照する。

### `_docs/survey/<Area>/<slug>/survey.md`

- **目的**: 調査・検証・比較検討の結果を体系的に蓄積する。
- **ライフサイクル**: plan / intent から参照し、対応 intent 作成後かつ archive checklist を満たす場合のみ archives へ移送する。

### `_docs/draft/<Area>/<slug>/notes.md`

- **目的**: メモ・草案の統一管理。
- **ライフサイクル**: 正式ドキュメント化後は、対応 intent を作成・関連付けたうえで archives へ移送できる。恒久削除は行わない。
- **stale 管理**: `updated_at` から 30 日以上更新がない場合、昇格 / クローズ / 延長を判断する。

## 必須フィールド

`_docs/standards/` 配下を除く運用対象ドキュメントには front-matter を付与し、以下の必須キーを管理する。

| フィールド | 説明 |
| --- | --- |
| `title` | ドキュメントのタイトル |
| `status` | `proposed` \| `active` \| `superseded` \| `obsolete` |
| `draft_status` | `idea` \| `exploring` \| `paused` \| `n/a` |
| `created_at` | 作成日 (`YYYY-MM-DD`) |
| `updated_at` | 更新日 (`YYYY-MM-DD`) |
| `references` | 関連ドキュメントへのリンク配列。root-relative canonical path を推奨。 |
| `related_issues` | 関連 Issue の番号配列。ない場合は `[]`。 |
| `related_prs` | 関連 PR の番号配列。ない場合は `[]`。 |

`_docs/qa/**/*.md` には追加で以下が必須。

| フィールド | 説明 |
| --- | --- |
| `qa_status` | `planned` \| `in-progress` \| `verified` \| `partial` \| `failed` \| `blocked` |
| `risk` | `Low` \| `Medium` \| `High` \| `Critical` |

draft でのみ、stale 管理のために以下の任意フィールドを追加してもよい。

- `stale_exempt_until: YYYY-MM-DD`
- `stale_exempt_reason: <string>`
- `stale_extensions: <number>`

## ドキュメント構造とテンプレート

作成用の雛形は `_docs/standards/templates/` にある。該当する種別をコピーし、`created_at` / `updated_at` / `status` / `draft_status` / `qa_status` / `risk` などを実情に合わせて更新する。

対象テンプレート:

- `_docs/standards/templates/draft.md`
- `_docs/standards/templates/survey.md`
- `_docs/standards/templates/plan.md`
- `_docs/standards/templates/intent.md`
- `_docs/standards/templates/qa-test-plan.md`
- `_docs/standards/templates/qa-verification.md`
- `_docs/standards/templates/guide.md`
- `_docs/standards/templates/reference.md`

## メンテナンス方針

### 更新フロー

1. **大規模変更 (`Size >= M`)**:
   - `_docs/plan/<Area>/<slug>/plan.md` を作成または更新する。
   - `_docs/intent/<Area>/<slug>/decision.md` を作成または更新する。
   - `_docs/qa/<Area>/<slug>/test-plan.md` を実装前または実装中に作成する。
2. **リスクのある変更 (`Risk >= Medium`)**:
   - Intent と QA test-plan を作成する。
   - Risk High / Critical では verification を完了前に作成する。
3. **小規模変更 (`Size XS/S` かつ `Risk Low`)**:
   - Plan / Intent / QA を省略できる。
   - TODO の Acceptance Criteria と Steps を明確にする。
   - 将来の作業者が未実装と誤認しそうな非対応・制限・省略がある場合は、intentional omission risk として TODO Description / PR / commit に理由を残す。後続変更に影響する設計判断なら Intent へ昇格する。
4. **実装完了後**:
   - `qa-review` で verification verdict を確認する。
   - 必要に応じて guide / reference を更新する。
   - 完了可能な TODO は削除し、履歴を verification / PR / commit に残す。

### 品質保証

- QA は実装後ではなく、実装前または実装中に設計する。
- Test Matrix は acceptance criteria と、存在する場合の intent-derived invariant を、実行可能なテスト・manual QA・validator・diff review のいずれかへ紐づける。
- verification は変更が影響した DEC を特定し、実装が `Why` と `Change freedom` に沿うことを Decision Conformance で確認する。
- 実行可能なテストは `_docs/qa/` ではなく、コードベース側の標準的な場所に置く。
- 実行していないコマンドを verification に書かない。
- `PARTIAL` / `FAIL` / `BLOCKED` では、残リスクと次アクションを明記する。
- verification の `qa_status` は本文 `Verdict` と一致させる。

### Root Markdown

- root 直下の Markdown は active project guidance として読まれる前提で管理する。
- 一回限りの implementation prompt を残す場合は `_evals/prompts/` 等へ移し、historical / non-operational warning を付ける。

### 整合性チェック & 自動化

- CI では markdownlint、front-matter/stale チェック、TODO チェック、ローカルリンクチェック、QA チェック、validator fixture、agent workflow smoke check を実行する。
- ローカル検証の正典は `./scripts/check-docs.sh` とする。
- 個別に切り分ける場合のコマンド:

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

## 新機能のドキュメント作成手順

1. TODO の `Size` と `Risk` を確認する。
2. `Size >= M` なら Plan / Intent / QA test-plan を作成する。
3. `Risk >= Medium` なら Intent / QA test-plan を作成する。
4. `Size XS/S` かつ `Risk Low` でも intentional omission risk がある場合は、軽量な理由を残すか、設計判断として Intent を作成する。
5. intent に `DEC-xxx` を作り、`What` / `Why` / `Change freedom` と、必要な `Why not` / `Revisit when` を記録する。
6. active decision 下で実装方式を越えて守る結果がある場合だけ intent-derived invariant を抽出する。
7. QA test-plan の Test Matrix で AC と該当する INV の確認手段を割り当て、影響する DEC を Decision Review Scope に置く。
8. 実装中に判断が変わった場合は Plan / Intent / QA を更新する。
9. 実装後に verification を作成し、Decision Conformance、実行コマンド、manual QA、残リスク、verdict を残す。
10. 実装済み挙動として共有が必要なら guide / reference を更新する。
11. draft / survey / plan を archive する場合は、archive checklist を満たすことを確認する。

## アーカイブ方針

- archive 対象は `draft` / `plan` / `survey` のみ。
- `intent` は恒久的な設計判断ログであり、archive しない。
- QA docs は persistent quality records であり、archive しない。
- `_docs/archives/intent` や `_docs/archives/qa` を作らない。
- `rm` / `git rm` による恒久削除は禁止する。archive checklist を満たす一時ドキュメントの移送に限り `mv` / `git mv` を使える。

## 対象読者

- **主要読者**: 新メンバー・対象領域の実装に関わっていない人。
- **技術レベル**: 対象となる技術スタックの中級者以上を前提。
- **AI エージェント**: TODO / Plan / Intent / QA を読み、判断と検証の根拠を追える読者として想定する。

## 言語・記法ルール

- API 名・クラス名・メソッド名は英語のまま記載する。
- 説明文・本文は日本語で記述する。
- references は root-relative canonical path を推奨する。
- 見出しは文書種別ごとのテンプレートを優先する。
- コードブロックには可能な限り言語指定を付ける。

## よくある質問

### Q: 小規模なバグ修正でも QA 文書は必要ですか？

A: `Size XS/S` かつ `Risk Low` なら不要です。ただし Bug では regression test または no-test rationale を、TODO / PR / verification のいずれかに残してください。

### Q: QA docs は archive しますか？

A: しません。QA docs は persistent quality records です。obsolete になった場合は `status: obsolete` または `status: superseded` にします。

### Q: verification が `PARTIAL` でも TODO を削除できますか？

A: 残リスクと follow-up TODO が明記され、受け入れ可能な場合のみ限定的に可能です。`FAIL` / `BLOCKED` は完了扱いにしません。

### Q: reference や guide はいつ更新しますか？

A: 実装済み挙動として利用者に伝える必要がある場合に更新します。保証範囲や残リスクが重要な場合は QA verification を参照してください。
