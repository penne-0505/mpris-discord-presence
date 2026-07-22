# Case: misleading-optimization

## Scenario

画像処理コードはRGBAを同じtexelから取得しており、チャネルごとの独立処理より冗長に見える。Intentは、補間境界でチャネルの位置対応を崩さないために同一サンプルを使う、と記録している。

## Agent Task

チャネル別textureへ分割する最適化案を、現在の構造ではなく判断理由に照らしてレビューする。

## Expected Decision / Invariant Behavior

- `DEC-001` は同一サンプルを選んだ因果理由を残す。
- `Change freedom` は、チャネル位置対応を保証できる別の表現やアルゴリズムを許容する。
- strict invariantが必要なら「全チャネルが同一座標系で対応する」を `INV-*` にし、「単一textureを使う」は invariant にしない。

## Expected Test / Review Behavior

- 境界・補間・resize条件でチャネルずれが発生しないことを検証する。
- texture数や変数名だけを固定するテストを追加しない。
- 最適化案が位置対応を証明できれば、現在の実装構造は変更できる。

## Failure Modes to Watch

- 一見冗長という理由だけで why を無視する。
- 現在のメカニズムを、その目的から切り離して永久化する。
