# Case: experimental-baseline

## Scenario

実験的な合成処理には固定のblend weightがあり、比較用baselineとして採用された経緯がIntentに残っている。agentは値を「仕様」とみなし、同値テストで固定しようとしている。

## Agent Task

baselineの再現性と、将来の改善余地を同時に保つ記録・テスト方針を選ぶ。

## Expected Decision / Invariant Behavior

- `DEC-001` は値を採用した比較条件と判断時点の根拠を記録する。
- `Revisit when` は新しい評価結果や品質基準を明示する。
- `Change freedom` は、比較結果と更新根拠を残す限りweight変更を許容する。
- 現在のweightそのものを恒久的な `INV-*` にしない。

## Expected Test / Review Behavior

- Testは出力範囲、決定性、比較手順など、baselineとして必要な性質を検証する。
- exact weight testが必要なら、再現対象となるversioned fixtureへ限定する。
- 改善案はIntentを破るのではなく、`Revisit when` に基づいてdecisionを更新できる。

## Failure Modes to Watch

- 実験値を製品の永久仕様へ変換する。
- 「変更可能」を理由に、比較可能性や更新根拠を残さない。
