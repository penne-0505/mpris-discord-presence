# Quality Assurance Standard

## 目的

このテンプレートにおける QA は、単に「テストを増やすこと」ではない。以下を確認する活動として扱う。

- 実装が intent に記録された設計判断を裏切っていないか。
- Plan で約束した実装方針を満たしているか。
- Acceptance Criteria が自動テスト・手動 QA・validator・review のいずれかで確認されているか。
- 未確認リスクが明示されているか。

QA 文書は実装の後始末ではなく、設計判断を検証可能な条件へ変換するための作業台である。

## 基本原則

- QA は実装後ではなく、実装前または実装中に設計する。
- `Size >= M` のタスクでは QA test-plan を必須とする。
- `Risk >= Medium` のタスクでは QA test-plan を必須とする。
- `Risk High / Critical` のタスクでは rollback / recovery / data safety の確認項目を必須とする。
- Bug 修正では、原則として regression test または no-test rationale を残す。
- Refactor では、behavior-preservation checks を明記する。
- Agent workflow / validator / CI / Skill / documentation rule の変更では、agent misbehavior risk を確認する。
- テストは実装詳細ではなく、acceptance criteria と、該当する場合だけ intent-derived invariant に紐づける。
- intent の第一目的は、将来の変更者が設計判断の `Why` と `Why not` を再構成できることである。
- QA 文書はテストそのものではない。実行可能なテストが書ける場合は、必ずコードベース側の適切な場所に置く。

## Risk 分類

| Risk | 定義 |
| --- | --- |
| Low | 局所的で、失敗しても影響が小さい変更。`Size XS/S` の軽微な Doc や Chore など。 |
| Medium | 機能挙動、ワークフロー、validator、ドキュメント規約、agent skill に影響する変更。`Size M` 以上は原則 Medium 以上。 |
| High | 互換性、データ損失、認証、権限、セキュリティ、課金、外部 API、CI/CD、migration に関わる変更。 |
| Critical | 本番障害、secret 漏洩、重大なデータ破壊、ユーザー影響の大きい破壊的変更につながり得る変更。 |

Risk は「作業量」ではなく、失敗時の影響と検証難度で判断する。

## QA 必須条件

| 条件 | 必須文書・確認 |
| --- | --- |
| `Size >= M` | Plan, Intent, QA test-plan が必須。 |
| `Risk >= Medium` | Intent, QA test-plan が必須。 |
| `Risk High / Critical` | Intent, QA test-plan, verification が必須。rollback / recovery / security / data safety の観点を明記する。 |
| `Category Bug` | regression test または no-test rationale が必須。 |
| `Category Refactor` | behavior-preservation checks が必須。 |
| Agent workflow / docs workflow / validator / CI / Skill 変更 | agent misbehavior checks が必須。 |

`Size XS/S` かつ `Risk Low` のタスクでは、Plan / Intent / QA / Verification は `None` にできる。ただし、Bug や Refactor など再発防止や挙動維持の説明が必要な場合は、軽量な根拠を TODO / PR / verification に残す。将来の作業者が未実装と誤認しそうな非対応・制限・省略がある場合も intentional omission risk として扱い、軽量な理由または Intent を残す。

## intent decision record

intent は「現在の実装を変えるな」と命令する台帳ではない。将来の変更者が、なぜその実装・省略・境界を
選んだのかを理解し、同じ意図を満たす別実装へ安全に変更できるようにする decision record である。

新規 intent は `intent_schema: 2` を使い、`DEC-001` 形式の安定 ID を持つ decision entry を作る。
各 decision entry は、最低限次の情報を持つ。

- **What**: 採用した判断。現在値の羅列ではなく、選択した意味や方針を書く。
- **Why**: 解決したい問題、守りたい性質、避けたい失敗との因果を書く。必須。
- **Change freedom**: `Why` を保つ限り変更できる実装方式・値・構造を明示する。必須。
- **Why not**: 一見妥当に見える不採用案と、その案では目的を満たせない理由。非自明な案がある場合に書く。
- **Revisit when**: 判断を再検討できる証拠・環境変化・条件。必要な場合に書く。

`What` や exact 値を言い換えただけの `Why` は不十分である。たとえば「timeout を 3000ms に保つ。
選定値だから」ではなく、「遅い応答を待ちつつ、UI が無反応に見える時間を制限するため」と、値を選んだ
目的へ遡る。値そのものが契約でなければ、再計測に基づく調整を `Change freedom` で許容する。

schema 指定のない既存 intent は legacy document として引き続き受理する。新規作成または意図を再構成する
文書から schema v2 を使い、既存文書を一斉移行のためだけに書き換えない。リンクや typo の修正だけなら
legacy のままでよいが、decision の意味を追加・変更する編集では schema v2 へ移行する。

## intent-derived invariant (optional)

intent-derived invariant は、active な decision の下で、実装方式が変わっても破ってはいけない結果だけを
表す。すべての decision から INV を作る必要はなく、INV が 0 件でも正常である。

例:

```text
Decision:
  DEC-001: intent と QA は履歴として live path に保持する。
  Why: archive すると coding agent が active decision と quality evidence を発見できない。
  Change freedom: draft / plan / survey の保管方式は変更できる。

Invariant:
  INV-001 (from DEC-001): `_docs/intent/**` と `_docs/qa/**` を archives へ移動しない。
```

INV へ昇格する前に確認する。

1. 現在のタスク完了後に破られても、active decision の下でなお誤りである。
2. 契約上固定する理由のない exact 値、比較 variant、実験の統制条件、migration 中だけの保全条件ではない。
3. 別実装でも守るべき結果として書ける。
4. 親となる `DEC-xxx` の `Why` から因果的に導ける。

一つでも満たさなければ INV にせず、Plan / Acceptance Criteria / survey / reference / decision の
`Change freedom` へ置く。INV を作った場合だけ、自動テスト・validator・手動 QA・diff review のいずれかへ
Test Matrix で割り当てる。

## intent ↔ code traceability

自己説明的なコードには限度がある。とくに why not（なぜその実装をしなかったか）はコードに不在として現れ、テストや git blame では拾いにくい。コードを読んでいる作業者や agent が、意図的な省略・非自明な実装の形を「未実装」「不要」と誤認して設計判断を壊すのを防ぐため、コードから intent へ到達する手がかりを残す。本節を intent と code の traceability に関する正典とする。

### いつ参照を残すか（ターゲット型）

- 全コード・全コメントへの一律義務化はしない。Fast Track の軽量さを壊さないため、対象を絞る。
- 残す対象は、設計判断を体現していて、素朴な読み手が誤って「直す」「消す」をしうる非自明な箇所に限る。例: 意図的な省略、互換性のために残した形、「冗長に見えるが必要」な処理、性能や順序のための非直感的な実装。

### テストとコメントの線引き

- 壊れたら落ちる形でテスト化できる acceptance criterion または任意の invariant は、AC / INV 名をテストへ割り当てる（`test-maintenance` 参照）。
- テスト化しにくい why not・意図的省略・構造的選択は、`DEC-xxx` を参照するコードコメントに残す。
- 同一条件をテストとコメントで二重義務化しない。
- exact 値を固定するテストは、その値自体が契約である理由を decision が説明している場合だけ作る。

### 参照書式

アンカーは理由へ辿る `DEC-xxx` を基本とし、厳格な invariant を体現する場合だけ `INV-xxx` を使う。
intent slug を併記し、生 doc パスだけの参照は正典にしない。

grep 可能な接頭辞を用いる。

```text
// intent: DEC-003 (<Area>/<slug>) — この実装・省略が必要な理由
// intent why-not: DEC-002 (<Area>/<slug>) — 一見妥当な別案を採らない理由
// intent-invariant: INV-002 (<Area>/<slug>) — active decision 下で破れない結果
```

ダッシュ以降は decision の `What` や値を繰り返さず、因果を一行で要約する。`preserve 210svh` のように
変更禁止だけを記すコメントは不十分である。コメントだけで説明し切れない場合も、`DEC-xxx` から完全な
`Why`、`Why not`、`Change freedom` へ到達できるようにする。

### 強制レベル

- コード参照の有無は validator で error として機械強制しない。「参照が要るほど非自明か」は機械判定できず、強制すればノイズと形骸化を生む。
- 遵守は skill（`implementation-prep` / `test-maintenance` / `post-implementation`）と review で担保する。
- 参照先 DEC / INV / intent slug の実在確認（リンク切れ検出）は、validator で任意に補える。これは参照の有無ではなく、参照先の存在のみを対象にする。

### intent 側の書き方

- Decision は安定した `DEC-xxx` ID を持ち、`Why` と `Change freedom` を必須にする。
- `Why not` は実際に検討した非自明な代替案がある場合だけ書き、架空の選択肢を水増ししない。
- Intent-derived Invariants は任意で、親 `DEC-xxx` を明示する。
- 任意で、DEC / INV がどこで体現・enforce されているかを示す back-reference を intent に残してよい。

## test matrix

test matrix は最低限、以下の列を持つ。

| ID | Source | Requirement / Optional Invariant | Test Type | Command / File | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | ... | unit | ... | ... | planned |
| INV-001 | DEC-001 | ... | validator | ... | ... | planned |

Test Matrix には少なくとも一つの AC を含める。INV 行は、対応 intent に INV が存在する場合だけ必要である。
DEC 自体を機械テストの対象にせず、変更が影響する DEC は verification の Decision Conformance で、
`Why` と `Change freedom` に沿っているかを review する。

`Status` は以下のいずれかにする。

- `planned`
- `covered`
- `verified`
- `deferred`
- `not-applicable`

`deferred` には理由が必要である。理由のない deferred は、検証漏れとして review で扱う。

## verification verdict

`verification.md` の最終判定は以下のいずれかにする。

| Verdict | 意味 |
| --- | --- |
| `PASS` | AC と該当する INV が確認され、影響した DEC が理由に沿って review され、完了扱いにできる。 |
| `PARTIAL` | 一部未確認だが、残リスクと follow-up TODO が明示され、限定的に完了扱いにできる。 |
| `FAIL` | 必須条件を満たしていない。完了不可。 |
| `BLOCKED` | 外部要因や未解決 blocker により検証不能。完了不可。 |

`PARTIAL` / `FAIL` / `BLOCKED` では、残リスクと次アクションを必須にする。

`verification.md` の front-matter `qa_status` は、本文 `Verification Verdict` の `Verdict` と一致しなければならない。

| Verdict | qa_status |
| --- | --- |
| `PASS` | `verified` |
| `PARTIAL` | `partial` |
| `FAIL` | `failed` |
| `BLOCKED` | `blocked` |

## QA documents

QA 文書は以下の canonical path に置く。

```text
_docs/qa/<Area>/<slug>/test-plan.md
_docs/qa/<Area>/<slug>/verification.md
```

- `test-plan.md` は intent・plan・TODO から導いた QA 計画である。
- `verification.md` は実装後の検証証跡であり、実行コマンド、手動 QA、未確認リスク、最終判定を残す。
- QA docs は persistent quality records であり、archive しない。
- feature や判断が obsolete になった場合は、`status: obsolete` または `status: superseded` にする。
- references は root-relative canonical path を推奨する。

## Root-level prompts

- Root-level Markdown files are treated as active project guidance.
- One-off implementation prompts must not be left at repository root.
- If retained, move them under `_evals/prompts/` or another clearly historical location and mark them as non-operational.
