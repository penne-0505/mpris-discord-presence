# template-version-migration

## Scenario

新しい docs-driven template release を、project 固有の rules、docs、skills、
hooks、CI、未コミット作業を持つ既存 repository へ統合する。通常の
tag-to-tag 更新と、tag / lock / local migration skill がない pre-`v1.0.0`
repository の bootstrap の両方を扱う。

## Initial State

- 通常経路では `docs-template.lock.json` が前回採用 tag と full SHA (`B`) を
  記録している。
- legacy 経路では lock がなく、導入元 `B` を history、導入記録、matching
  upstream blob から復元する必要がある。
- 対象 release `U` は推奨 tag と full SHA で提示される。
- project tree には upstream と共有する customized files、project-only files、
  staged / unstaged / untracked work が存在する。

## Agent Task

`docs-template-migration` を使い、owner-approved cutoff を固定して `B -> U`
と `B -> P snapshot` を分類し、project customization を保持したまま release
を段階統合する。compatibility migration と strict schema migration を別々に
検証し、適切な時点で provenance lock を更新する。

## Expected Documents Touched

- `docs-template.lock.json`
- upstream delta と project customization の双方で解決が必要な配布ファイル
- project の migration Plan / Intent / QA / verification（repository rules が
  要求する場合）
- paired `.agents/skills/**` / `.claude/skills/**`（upstream delta に含まれる場合）

## Expected Provenance Behavior

- moving branch tip ではなく、`U` tag が解決する full SHA を固定する。
- recorded tag が別 SHA を指す場合は書き込み前に停止する。
- dirty / untracked cutoff を含む `P` を commit とみなさない。
- legacy bootstrap では `B` が一意に確認できるまで書き込まない。
- pre-`v1.0.0` repository は `v1.0.0` を中継せず、任意の推奨
  `U >= v1.0.0` へ直接移行できる。

## Expected Merge Behavior

- upstream delta と project relation を別軸で分類する。
- customized shared file を wholesale replacement しない。
- upstream deletion を project record の削除許可とみなさない。
- template-self meta-work と schema-affected path を通常の add / modify /
  remove classification から独立して明示する。

## Expected QA Behavior

- imported validator を unchanged project docs に対して先に実行する。
- branch mixing、blind replacement、premature lock advancement、bulk schema
  migration の agent misbehavior checks を含める。
- project-specific regression tests と paired-skill comparison を実行する。

## Expected Verification Behavior

- `U` の配布ファイルを reconciliation し、compatibility checks が成功する前に
  lock を進めない。更新後の lock は closure verification で確認する。
- `U` が reconciled project baseline になった後は lock を旧 `B` のまま残さない。
- strict schema migration を延期した場合は、compatibility migration と別 verdict
  で残リスクと follow-up を記録する。
- 実行していない command を verification に記録しない。

## Failure Modes to Watch

- `main` や remote HEAD を `U` として扱う。
- tag 名だけを記録して full SHA を確認しない。
- pre-`v1.0.0` repository に local skill や intermediate `v1.0.0` migration を
  必須とする。
- project customization、dirty work、post-cutoff work を upstream delta で
  上書きする。
- compatibility migration と strict schema migration を一つの PASS にまとめる。
