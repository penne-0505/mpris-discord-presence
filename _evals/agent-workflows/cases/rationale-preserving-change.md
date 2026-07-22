# Case: rationale-preserving-change

## Scenario

スクロール区間を確保するため、現在の実装はコンテナ高に `210svh` を使っている。agent は `200vh` の方が単純だとして置換しようとしているが、Intent はモバイルブラウザのUI変動後も操作区間を確保することを理由としている。

## Agent Task

現在値を絶対視せず、`DEC-*` の理由と変更自由度に照らして置換の妥当性を判断する。

## Expected Decision / Invariant Behavior

- `DEC-001` の `Why` は「UI変動後も必要な操作区間を確保する」という結果を示す。
- `Change freedom` は、計測ベースのレイアウトや別のviewport unitを許容できる。
- `210svh` という値自体を `INV-*` にしない。

## Expected Test / Review Behavior

- Testは複数のviewport条件で操作区間が成立するかを確認する。
- `210svh` という文字列の存在だけをassertしない。
- 置換案が同じ結果を満たす証拠を示せなければ、変更を見送る。

## Failure Modes to Watch

- Intentを「210svhを変えるな」という命令として読む。
- 単純化だけを理由に、記録された目的を検証せず値を置換する。
