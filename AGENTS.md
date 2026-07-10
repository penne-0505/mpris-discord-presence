## 原則

- 日本語で会話する。
- 日付確認には`date`コマンドを使用する。
- tool や shell command を優先して使用する。
- **徹底的に現状実装・ドキュメントを参照、分析してから実装を行う。**
- **`git rm`や`rm`などの恒久削除は禁止**（ユーザーに提案し、実行は待つ）。ただし、archive checklist を満たす一時ドキュメントの移送に限り `mv` / `git mv` は許可。
- [documentation guidelines](_docs/standards/documentation_guidelines.md) と [documentation operations](_docs/standards/documentation_operations.md) を遵守して、積極的にドキュメントを更新する。skillsを積極活用してドキュメント更新と実装準備を行う。
- 久しぶりの再開、handoff 探索、現状把握、docs が形だけになっていないかの確認では `docs-inventory` skill を使う。
- Size >= M または Risk >= Medium のタスクでは、実装前に QA test-plan を作成し、実装後に verification を残す。
- QA / テスト方針は [quality assurance standard](_docs/standards/quality_assurance.md) に従う。
- 設計判断を体現した非自明なコード（とくに why not・意図的な省略）には、`// intent: INV-00X (<Area>/<slug>) — ...` で intent への参照を残す。全コード義務ではなくターゲット型。詳細は [quality assurance standard](_docs/standards/quality_assurance.md) の intent ↔ code traceability に従う。
- 完了前には `qa-review` skill を使い、verification verdict を確認する。
- 安全性・権限・secret・外部入力の扱いは [security for agents](_docs/standards/security_for_agents.md) に従う。
- root 直下の Markdown は active project guidance として扱われる。一回限りの実装プロンプトを残す場合は `_evals/prompts/` 等へ移し、非運用の履歴資料として明記する。
