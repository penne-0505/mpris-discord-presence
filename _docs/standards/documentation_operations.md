# ドキュメント運用標準

## 目的

- `_docs/` 配下のドキュメント種別ごとの役割と運用境界を明確化する。
- intent を恒久的な設計判断ログとして扱い、QA / test plan / verification へ接続する。
- 昇格・更新・廃止・archive フローを標準化し、全メンバーと coding agent が同じ基準で扱えるようにする。
- Front-matter と Markdown テンプレートを連携させ、ドキュメント品質と可観測性を高める。

## 適用範囲

- 対象: `_docs/draft/`, `_docs/survey/`, `_docs/plan/`, `_docs/intent/`, `_docs/qa/`, `_docs/guide/`, `_docs/reference/`, `_docs/archives/`。
- 適用範囲: ドキュメント作成・更新・保守・QA 証跡・自動化。
- 非対象: アプリケーションコードや API の実装規約。ただし、QA test-plan は実行可能なテストの配置方針を参照してよい。

## ディレクトリの役割

| パス | 目的 | 主な利用者 | 備考 |
| --- | --- | --- | --- |
| `_docs/draft/<Area>/<slug>/notes.md` | アイデア、検討メモ、仮説、代替案等の一時保管 | 設計者・実装者・調査担当 | `updated_at` 基準で stale 管理。決定事項はここに残さない。 |
| `_docs/survey/<Area>/<slug>/survey.md` | 調査・検証レポート | 調査担当・意思決定者 | plan / intent から根拠として参照。 |
| `_docs/plan/<Area>/<slug>/plan.md` | 合意済み仕様・実施計画の単一参照点 | 施策オーナー・実装担当 | `Size >= M` の TODO で必須。QA Plan を含める。 |
| `_docs/intent/<Area>/<slug>/decision.md` | 設計判断・意思決定ログ | 設計判断を参照する開発者 | 恒久記録。archive しない。 |
| `_docs/qa/<Area>/<slug>/test-plan.md` | intent / plan / TODO から導いた QA 計画 | 実装者・レビュアー・QA 担当 | `Size >= M` または `Risk >= Medium` で必須。archive しない。 |
| `_docs/qa/<Area>/<slug>/verification.md` | 実装後の検証証跡 | 実装者・レビュアー・運用担当 | 実行コマンド、手動 QA、残リスク、verdict を残す。archive しない。 |
| `_docs/guide/<Area>/<slug>/usage.md` | 実装済み機能の運用ガイド | 全メンバー | plan / intent / verification の結果を反映。 |
| `_docs/reference/<Area>/<slug>/reference.md` | 実装済み機能の詳細リファレンス | 実装者・保守担当 | API / データ / 挙動保証の詳細を記述。 |
| `_docs/archives/{draft,plan,survey}/<Area>/<slug>/...` | intent 作成済み一時ドキュメントの保管庫 | 後から経緯を参照する開発者 | archive 対象は draft / plan / survey のみ。 |

`<Area>` は `TODO.md` の `Area` と一致させる。`<slug>` は機能・変更単位の kebab-case 名にする。

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

references は root-relative canonical path を推奨する。

```yaml
references:
  - "_docs/intent/Core/feature-x/decision.md"
  - "_docs/plan/Core/feature-x/plan.md"
  - "_docs/qa/Core/feature-x/test-plan.md"
```

## ライフサイクルと昇格ルール

1. **標準フロー**: `draft/survey → plan → intent → qa/test-plan → implementation → qa/verification → guide/reference`
   - 大規模な変更 (`Size >= M`) や、設計判断が必要な機能追加に適用。
   - Plan は QA Plan を含め、QA test-plan は acceptance criteria と、存在する場合の intent-derived invariant を Test Matrix へ変換する。変更が影響する DEC は review scope として扱う。
   - `draft` / `survey` / `plan` は、対応する `intent` が存在し、archive checklist を満たす場合のみ archives へ移送できる。

2. **Risk-based QA flow**:
   - `Risk >= Medium` では Intent と QA test-plan を必須とする。
   - `Risk High / Critical` では、完了前に verification を必須とし、rollback / recovery / security / data safety を確認する。
   - Bug 修正では regression test または no-test rationale を残す。
   - Refactor では behavior-preservation checks を残す。
   - Agent workflow / validator / CI / Skill / documentation rule の変更では agent misbehavior checks を残す。

3. **軽量フロー (Fast Track)**: `TODO定義(Steps) → 実装 → 必要なら intent/guide/reference`
   - `Size XS/S` かつ `Risk Low` の小規模修正に適用。
   - TODO 上でタスク定義、Acceptance Criteria、Steps が明確である場合、Plan / Intent / QA を `None` にできる。
   - ただし、将来の作業者が未実装と誤認しそうな非対応・制限・省略は intentional omission risk として扱い、TODO Description / PR / commit、または必要に応じて Plan Non-Goals / Intent の DEC（Why / Why not）に理由を残す。
   - ただし、Bug / Refactor などで再発防止や挙動維持の根拠が必要な場合は、PR / commit / verification に残す。

4. **QA documents のライフサイクル**
   - `qa/test-plan.md` は intent・plan・TODO から導いた QA 計画であり、原則として archive しない。
   - `qa/verification.md` は実装後の検証証跡であり、原則として archive しない。
   - feature や判断が obsolete になった場合は、`status: obsolete` または `status: superseded` にする。
   - QA docs はテストコードの置き場ではない。実行可能なテストはコードベース側の標準的な場所に置く。

## 一時ドキュメントのアーカイブルール

- `draft`、`plan`、`survey` は「開発過程専用の一時ドキュメント」であり、対応する `intent` を作成していない状態でのアーカイブを禁止する。
- `intent` は恒久的な設計判断ログであり、archive 対象にしない。
- QA docs は persistent quality records であり、archive 対象にしない。
- archive 対象は `draft` / `plan` / `survey` のみとする。
- `_docs/archives/intent`、`_docs/archives/qa`、`_docs/archives/guide`、`_docs/archives/reference` は作らない。
- 一時ドキュメントの移行フロー:
  1. 一時ドキュメントを `intent` テンプレートへ再構成する。
  2. `intent` を `_docs/intent/<Area>/<slug>/decision.md` に作成し、一時ドキュメントと相互参照する。
  3. アーカイブ移送時は、元ディレクトリから原本を取り除き、`_docs/archives/{draft,plan,survey}/<Area>/<slug>/...` へ同じ front-matter を保持したまま移す。
- 違反例:
  - 対応する `intent` を作成しないまま `_docs/archives/` へ移動する。
  - `intent` または `_docs/qa/**` を `_docs/archives/` へ移動する。
  - アーカイブ後も元ディレクトリに原本を残す。

## 破壊的操作と archive 移送

- `rm` / `git rm` による恒久削除は禁止する。不要に見えるファイルでも、削除はユーザーに提案して実行を待つ。
- archive checklist を満たす一時ドキュメントの移送に限り、`mv` / `git mv` を許可する。
- archive 移送は削除ではなく、履歴保持のための移動として扱う。
- archive 実行前に、対応する `intent` が存在し、対象一時ドキュメントへの参照または相互リンクがあることを確認する。
- 「テンプレート repo 自身の meta-work に対する例外」は persistent records 分類上の整理にとどまり、本節の原則を上書きしない。

## テンプレート repo 自身の meta-work に対する例外

本 repo は docs-driven development のテンプレートとして配布される。テンプレート利用者は新規プロジェクトとしてこの repo を起点に作業するため、**テンプレート repo 自身の改善作業 (meta-work) に伴って生成された intent / plan / qa docs** を配布物に混入させない運用を許容する。

- 対象: テンプレート repo そのものを磨くための作業として作成された intent / plan / qa。たとえば validator 自体の挙動を決める decision、テンプレートの workflow を整える plan、テンプレ運用上の自己検証 verification など。Area 名としては `Template` や同等のメタ作業領域が該当する。
- 分類上の扱い: 上記対象は persistent records の射程外とする。決定事項が `_docs/standards/` または `_docs/standards/templates/` へ吸収された後は、ライフサイクル上「保持義務のあるドキュメント」とは見なさない。
- 操作の権限: 本例外は分類の整理であり、「破壊的操作と archive 移送」の原則を上書きしない。実ファイルに対する操作は同節の通常ルールに従う。
- 適用しない範囲: 利用者プロジェクトとして clone した後の通常運用には適用しない。利用者側 intent / qa は引き続き persistent records として扱い、`status: superseded` / `status: obsolete` で処理する。

この例外を設ける理由は二つある。第一に、配布物に meta-work 履歴が混入すると、新規利用者が「テンプレートの一部の規約・例」と誤読しやすい。実例として、過去に coding agent が `_docs/intent/Template/...` を active guidance / 参照例として扱った事象がある。第二に、「持続的記録として残す」原則は **テンプレートを適用したプロジェクト** を想定して書かれており、テンプレート自身の meta-work には射程が及ばない。テンプレ repo に対しては git 履歴がその役割を担う。

## Root Markdown と一回限り prompt

- root 直下の Markdown は、coding agent に active project guidance として読まれる前提で管理する。
- 一回限りの implementation prompt は root に残さない。
- 履歴として残す場合は `_evals/prompts/` 等の明確に非運用の場所へ移し、ファイル先頭に historical / non-operational warning を付ける。
- 現在の作業指示は `AGENTS.md`、`TODO.md`、`_docs/documentation_guide.md`、`_docs/standards/`、関連 Skills を参照する。

## TODO.md 完了処理

- 完了タスクは `TODO.md` から削除する。
- 完了履歴は PR、commit、CHANGELOG、intent、guide、reference、QA verification に残す。
- `TODO.md` に Done / Archived セクションを作らない。
- follow-up が必要な場合は、新しい ID を採番して Backlog に追加する。
- `Size >= M` または `Risk >= Medium` のタスクは、完了前に `verification.md` を作成または更新する。
- verification verdict が `FAIL` / `BLOCKED` の場合は完了扱いにしない。
- verdict が `PARTIAL` の場合は、残リスクと follow-up TODO が明記され、受け入れ可能な場合のみ限定的に完了扱いにできる。

## アーカイブ実行チェックリスト

1. 対応する `_docs/intent/<Area>/<slug>/decision.md` が作成済みであることを確認する。
2. アーカイブ対象ドキュメントと `intent` が `references` または本文リンクで関連付けられていることを確認する。
3. アーカイブ対象が `draft` / `plan` / `survey` のいずれかであることを確認する。
4. アーカイブ対象ドキュメントの front-matter を保持したまま `_docs/archives/{draft,plan,survey}/<Area>/<slug>/...` へ移す。
5. 移行元ディレクトリのクリーンアップを差分で確認し、同じ一時ドキュメントが live path に残っていないことを確認する。
6. アーカイブ対象と関連する `intent` を `references` フィールドに追記し、相互リンクを更新する。
7. 必要に応じて `CHANGELOG.md` や関連 Issue へ作業ログを残す。

## Front-matter Schema

`_docs/standards/` 配下を除く運用対象ドキュメントは、以下の共通 front-matter を持つ。

| フィールド | 説明 |
| --- | --- |
| `title` | 文書タイトル |
| `status` | `proposed` \| `active` \| `superseded` \| `obsolete` |
| `draft_status` | `idea` \| `exploring` \| `paused` \| `n/a` |
| `created_at` | `YYYY-MM-DD` |
| `updated_at` | `YYYY-MM-DD` |
| `references` | 関連リンク配列。root-relative canonical path を推奨。 |
| `related_issues` | 関連 Issue の番号配列。ない場合は `[]`。 |
| `related_prs` | 関連 PR の番号配列。ない場合は `[]`。 |

`_docs/qa/**/*.md` は、共通 front-matter に加えて以下を必須とする。

| フィールド | 説明 |
| --- | --- |
| `qa_status` | `planned` \| `in-progress` \| `verified` \| `partial` \| `failed` \| `blocked` |
| `risk` | `Low` \| `Medium` \| `High` \| `Critical` |

新しい why-first schema を使う文書は、次の marker を持つ。marker のない既存文書は legacy schema として
引き続き受理し、一斉移行を要求しない。既存文書のリンク・typo・metadata 修正だけなら marker は不要だが、
decision の意味または QA 契約を追加・変更する場合は対応する schema v2 へ移行する。

| 対象 | フィールド | 値 |
| --- | --- | --- |
| `_docs/intent/**/*.md` | `intent_schema` | `2` |
| `_docs/qa/**/*.md` | `qa_schema` | `2` |

draft の stale 管理向け任意フィールド:

- `stale_exempt_until: YYYY-MM-DD`
- `stale_exempt_reason: <string>`
- `stale_extensions: <number>`

## ドキュメント構造とテンプレート

作成用の雛形は `_docs/standards/templates/` にある。該当する種別をコピーし、`created_at` / `updated_at` / `status` / `draft_status` / `qa_status` / `risk` などを実情に合わせて更新する。

### Plan ドキュメントの構造例

```markdown
## Overview
概要を記述。

## Scope
- 実装する機能範囲
- 変更の影響範囲

## Non-Goals
- 今回のスコープに含まれないもの

## Requirements
- **Functional**: 機能要件
- **Non-Functional**: 非機能要件

## Tasks
- 実装タスク一覧

## QA Plan
- Risk level
- QA document
- Test strategy
- Acceptance criteria と、存在する場合の intent-derived invariant の確認手段
- 影響する `DEC-xxx` の review 方針

## Deployment / Rollout
- デプロイ手順、ロールバック方針
```

### QA Test Plan の構造例

```markdown
## Source of Intent
## Quality Goal
## Acceptance Criteria
## Decision Review Scope
## Intent-derived Invariants
## Risk Assessment
## Test Strategy
## Test Matrix
## Manual QA Checklist
## Regression Checklist
## Out of Scope
## Open Questions
```

### QA Verification の構造例

```markdown
## Summary
## Verification Verdict
## Commands Run
## Automated Test Results
## Manual QA Results
## Acceptance Criteria Coverage
## Decision Conformance
## Invariant Coverage
## Deferred / Not Covered
## Residual Risks
## Follow-up TODOs
```

## Template revision provenance

この template を適用した project が後続 release を継続的に取り込めるよう、upstream template の provenance を `docs-template.lock.json` に記録する。雛形は root の `docs-template.lock.example.json` とする。

```json
{
  "schema": 1,
  "source": "https://github.com/penne-0505/docs_driven_dev_template.git",
  "revision": {
    "tag": "v1.0.0",
    "commit": "<tagが解決するfull 40-character commit SHA>"
  }
}
```

- **更新単位**: upstream が推奨する immutable release tag を使う。branch 名や moving tip を lock に記録しない。
- **実体の固定**: tag 名だけでなく、その tag が解決する full commit SHA を記録する。後から同名 tag の解決先が変わった場合は migration を停止する。
- **初回導入**: tagged release から開始した project は、雛形を `docs-template.lock.json` へコピーし、採用 tag の full SHA を記録する。lock は project の tracked file とする。
- **通常更新**: lock の revision を `B`、次の推奨 tag を `U` とし、`docs-template-migration` skill で project customization を含む three-way migration を行う。`U` の配布ファイルを reconciliation し、compatibility checks が成功した後に、lock を最後の migration write として `U` へ進める。closure verification では更新後の tag と full SHA を確認する。
- **schema 状態との分離**: lock は統合済み upstream revision だけを示す。strict schema migration の完了・延期・残リスクは QA verification に記録し、lock schema へ混在させない。
- **pre-v1.0.0 bootstrap**: tag、lock、local migration skill がない既存 project は、repository history、導入記録、upstream と一致する blob から最後に採用した commit `B` を復元する。project 固有ルールを安全境界とし、対象 `U` の skill を外部入力としてレビューしてから書き込みを行う。`v1.0.0` を中継せず、`v1.0.0` 以降の任意の推奨 tag へ直接移行できる。`B` が一意に特定できない場合は owner 判断を推測せず停止する。compatibility migration の PASS 後に初回 lock を `U` で作成する。
- **template release 側**: release tag を作成する commit では、`docs-template.lock.example.json` の `revision.tag` をその tag 名へ更新しておく。commit SHA は tag 作成後に解決するため、雛形では placeholder のままとする。

`DD_SCOPE_BASE` は導入先 repository 内の validator 対象を決める project-local git ref であり、upstream template の採用 revision を示す値ではない。両者を兼用しない。

## 段階的導入スコープ (Incremental Adoption)

既存プロジェクトへ後付け導入する際、テンプレート規約に従っていない既存 docs が一斉に検証対象となり CI が埋まるのを避けるため、docs validator は「導入以降に追加された docs」だけを判定対象に絞る opt-in スコープ機構を持つ。本節を段階的導入スコープの正典とする。

- **既定は全走査**: 環境変数が未設定なら、各 validator は従来通り全 docs を走査する。テンプレート自身の CI はこの既定で dogfooding を続ける。
- **`DD_SCOPE_BASE`**: 導入時点の git ref（commit / tag）を設定すると、`git diff --name-only --diff-filter=A <ref>...HEAD` で得た「追加されたファイル」のみを判定対象にする。既存ファイルは判定しない。一度導入後に既存ファイルを編集しても、既定ではスコープに入らない（追加のみ）。
- **`DD_SCOPE_DIFF_FILTER`**: `DD_SCOPE_BASE` 使用時の git `--diff-filter` を上書きする。既定は `A`。既存 docs を編集した時点で管理対象にしたい導入先では `ACMR` を設定する。
- **`DD_SCOPE_PATHS`**: 改行 / コロン区切りの明示パスリスト。CI で対象集合を自前計算する場合やテスト向け。優先順位は `DD_SCOPE_PATHS > DD_SCOPE_BASE > 未設定`。
- **対象 validator**: `validate-frontmatter` / `validate-doc-links` / `validate-intent` / `validate-qa` がスコープを共有する。母集合決定は `scripts/scope.mjs` に集約されている。
- **`TODO.md` は常時検証**: `validate-todo.mjs` はスコープの影響を受けない。運用台帳は導入時点から管理対象とする。
- **横断チェックの扱い**: リンク / references の整合チェックは判定の起点ファイルだけをスコープで絞り、参照先の存在確認はファイルシステム全体に対して行う。新規 doc から既存 doc へのリンクは壊れない。
- **必要権限**: スコープ対応 validator の実行には `--allow-env` を、`DD_SCOPE_BASE`（git）使用時は加えて `--allow-run=git` を付与する。権限が無い場合は安全側（全走査）へフォールバックする。
- **CI 設定**: `DD_SCOPE_BASE` を使う場合、baseline commit を参照できるよう `actions/checkout` で `fetch-depth: 0` を設定する。

導入先での有効化例:

```yaml
env:
  DD_SCOPE_BASE: <導入時点の commit SHA または tag>
  # Optional: include edited / copied / modified / renamed docs as managed.
  # DD_SCOPE_DIFF_FILTER: ACMR
```

問題が出た場合は環境変数を外すだけで全走査の従来挙動へ復帰できる（コード変更不要）。

## コンプライアンス

- ドキュメントに秘密情報・個人情報を含めない。環境値は `.env.example` を参照する。
- CI ログ出力にはマスク設定を適用し、機密情報が残らないようにする。
- 公開資料として扱える品質を前提に、OSS 化を想定した文言に統一する。
- intent と QA docs を archive しない。
- Deno validator (`validate-frontmatter`, `validate-todo`, `validate-doc-links`, `validate-intent`, `validate-qa`, `test-validators`) をローカルと CI で実行する。
