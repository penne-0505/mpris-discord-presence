# Documentation Driven Development Template

> This README is available in English and Japanese. English speakers, please scroll down.

## 概要

このリポジトリは私が常用しているドキュメント駆動開発 *(Documentation Driven Development)* のテンプレートです。

開発サイクルはドキュメントと [TODO.md](TODO.md) によって構成されています。

このテンプレートは `intent` を品質保証の一次資料として扱います。中規模以上、またはリスクのある変更では `_docs/qa/` に QA test-plan と verification を残し、テストを intent-derived invariant と acceptance criteria に紐づけます。`_docs/qa/` はテストコードの置き場ではなく、計画・対応表・検証証跡の置き場です。

人がサイクルを回すことも出来ますが、基本的には**Claude Codeなどのコーディングエージェント**が、この規則に従って自律的な開発を行うために設計されました。

**詳細については [ガイドライン](_docs/documentation_guide.md) を参照してください。**

初めて使う場合は、まず [Quickstart](QUICKSTART.md) を読んでください。

## 使用方法

1. このリポジトリをフォークまたはクローンします。
2. プロジェクトに合わせてドキュメントと設定ファイルを編集します。
3. 開発を開始します。

配布用 ZIP を作る場合は、`.git` / `.jj` などの VCS メタデータを含めないために、GitHub 標準アーカイブまたは `scripts/create-template-archive.sh` を使用してください。

ローカルでドキュメント検証をまとめて実行する場合は、`scripts/check-docs.sh` を使います。

既存プロジェクトへ後付け導入する場合は、`DD_SCOPE_BASE` に導入時点の commit を設定して、既定では「導入以降に追加した docs だけ」を検証対象に絞れます。編集した既存 docs も対象にしたい場合は `DD_SCOPE_DIFF_FILTER=ACMR` を使います。設定方法は [Quickstart](QUICKSTART.md) と [documentation_operations.md](_docs/standards/documentation_operations.md) を参照してください。

Codex / Claude Code 向けの lifecycle hook を同梱しています。hook は docs や TODO を自動更新せず、SessionStart で workflow context を再注入し、Stop で検証・整理・archive 境界の見落としを促し、PreToolUse で代表的な恒久削除や sensitive file 操作を止めるための guardrail です。利用時は各 agent の `/hooks` で内容を確認して信頼してください。

久しぶりの再開や handoff 探索では、`docs-inventory` skill が TODO、intent、QA、guide、reference、一時 docs の棚卸しを行います。これは read-only の診断であり、整理や archive 実行は `docs-cleanup` の役割です。

root 直下の Markdown は agent 向けの active guidance として扱われます。一回限りの実装プロンプトを履歴として残す場合は `_evals/prompts/` などへ移し、非運用文書であることを明記してください。

### カスタマイズ

使用に当たっては、以下のファイルをプロジェクトに合わせてカスタマイズしてください。

#### AGENTS.md

プロジェクト固有の実行コマンド、安全基準、hook / skill の利用方針に合わせて確認・編集してください。

#### README.md

このREADME自体も、プロジェクトに合わせて編集してください。

#### LICENSE.txt

[LICENSE](LICENSE.txt)についても、特に著作者の表示を編集してください。

## ライセンス

このリポジトリは [MITライセンス](LICENSE.txt) の下でライセンスされています。

---

## Summary

This repository is a template for Documentation Driven Development that I commonly use.

The development cycle is structured around documentation and [TODO.md](TODO.md).

This template treats `intent` documents as primary QA inputs. Medium-sized or risky changes keep a QA test plan and verification record under `_docs/qa/`, and tests should map back to intent-derived invariants and acceptance criteria. `_docs/qa/` is for plans, traceability, and evidence; test code belongs in the codebase's normal test locations.

While humans can run the cycle, it is primarily designed **for coding agents like Claude Code** to autonomously develop according to these rules.

**For more details, please refer to the [Guidelines](_docs/documentation_guide.md).**

If this is your first time using the template, start with the [Quickstart](QUICKSTART.md).

## Usage

1. Fork or clone this repository.
2. Edit the documentation and configuration files to suit your project.
3. Start development.

When creating a distribution ZIP, use GitHub's standard archive or `scripts/create-template-archive.sh` so VCS metadata such as `.git` / `.jj` is not included.

Use `scripts/check-docs.sh` to run the local documentation validators together.

When adopting this template in an existing project, set `DD_SCOPE_BASE` to the adoption commit. By default, only docs added after adoption are validated. Set `DD_SCOPE_DIFF_FILTER=ACMR` if edited existing docs should also become managed. See the [Quickstart](QUICKSTART.md) and [documentation_operations.md](_docs/standards/documentation_operations.md) for setup.

Lifecycle hooks for Codex and Claude Code are included. They do not update docs or TODOs automatically; they reinject workflow context on SessionStart, nudge missed verification / cleanup / archive-boundary work on Stop, and block representative permanent-deletion or sensitive-file operations on PreToolUse. Review and trust them through each agent's `/hooks` UI before use.

For project resumes or handoff discovery, the `docs-inventory` skill audits TODO, intent, QA, guide, reference, and temporary docs. It is a read-only diagnosis; cleanup and archive execution belong to `docs-cleanup`.

Root-level Markdown is treated as active guidance for agents. If you keep a one-off implementation prompt for history, move it under `_evals/prompts/` or another historical location and mark it as non-operational.

### Customization

When using this template, please customize the following files to fit your project.

#### AGENTS.md

Review and edit this file to match project-specific commands, safety rules, and hook / skill usage expectations.

#### README.md

Feel free to edit this README itself to suit your project.

#### LICENSE.txt

Please edit the [LICENSE](LICENSE.txt) file, particularly the author attribution.

## License
This repository is licensed under the [MIT License](LICENSE.txt).
