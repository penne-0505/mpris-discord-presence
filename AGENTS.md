## 原則

- 日本語で会話する。
- 日付確認には`date`コマンドを使用する。
- tool や shell command を優先して使用する。
- **徹底的に現状実装・ドキュメントを参照、分析してから実装を行う。**
- **`git rm`や`rm`などの恒久削除は禁止**（ユーザーに提案し、実行は待つ）。ただし、archive checklist を満たす一時ドキュメントの移送に限り `mv` / `git mv` は許可。
- [documentation guidelines](_docs/standards/documentation_guidelines.md) と [documentation operations](_docs/standards/documentation_operations.md) を遵守して、積極的にドキュメントを更新する。skillsを積極活用してドキュメント更新と実装準備を行う。
- 久しぶりの再開、handoff 探索、現状把握、docs が形だけになっていないかの確認では `docs-inventory` skill を使う。
- upstream の docs-driven template を推奨 release tag へ更新する場合は `docs-template-migration` skill を使い、moving branch tip ではなく tag と full SHA を固定し、`docs-template.lock.json` を互換移行の検証後に更新する。
- Size >= M または Risk >= Medium のタスクでは、実装前に QA test-plan を作成し、実装後に verification を残す。
- QA / テスト方針は [quality assurance standard](_docs/standards/quality_assurance.md) に従う。
- 設計判断を体現した非自明なコード（とくに why not・意図的な省略）には、`// intent: DEC-00X (<Area>/<slug>) — <理由>` で decision の Why へ到達できる参照を残す。strict invariant を体現する場合だけ `// intent-invariant: INV-00X ...` を使う。現在値や「変えるな」の言い換えだけをコメントにしない。全コード義務ではなくターゲット型。詳細は [quality assurance standard](_docs/standards/quality_assurance.md) の intent ↔ code traceability に従う。
- 完了前には `qa-review` skill を使い、verification verdict を確認する。
- 安全性・権限・secret・外部入力の扱いは [security for agents](_docs/standards/security_for_agents.md) に従う。
- root 直下の Markdown は active project guidance として扱われる。一回限りの実装プロンプトを残す場合は `_evals/prompts/` 等へ移し、非運用の履歴資料として明記する。

## Project runtime

- 対象環境は Linux desktop session、session D-Bus、MPRIS、Discord desktop である。
- Python package は `src/` layout。PyGObject と Playerctl typelib は OS package を使用し、repo に binary を vendor しない。
- Discord Application ID は public identifier として扱う。user token、OAuth token、client secret、Rich Presence join secret を追加しない。
- MPRIS metadata は private data になり得る。通常ログ、例外ログ、test artifact に title / artist / album / URL を残さない。
- live QA で player や Discord の停止・再起動を行う前に、利用者への影響を確認する。

## Project commands

- Unit tests: `PYTHONPATH=src python -m unittest -v`
- Compile check: `python -m compileall -q src tests`
- Diagnostics: `PYTHONPATH=src python -m mpris_discord_presence --config config.toml doctor`
- Foreground run: `PYTHONPATH=src python -m mpris_discord_presence --config config.toml run`
- Service dry-run: `./scripts/install-user-service.sh --dry-run`
- Service install/start after config: `./scripts/install-user-service.sh --enable-now`
- Docs checks: `./scripts/check-docs.sh`
