# 作業記録: 業務プロセス図 → PPTX

- 計画: [plan.md](./plan.md)
- 開始: 2025-02-07

## DR 決定

| ID | 決定 |
|----|------|
| DR-001 | Python + uv |
| DR-002 | python-pptx で図形生成 |
| DR-003 | ベストエフォート（スキーマ検証なし） |

## Phase 1 実装

- XML → .drawio: `xml2drawio.xml_to_drawio` / `save_drawio`
- XML → PPTX: `xml2pptx.xml_to_pptx` / `xml_file_to_pptx`
- CLI: `process-to-pptx to-drawio | to-pptx | pipeline`
- Phase 1 完了: 全 DoD 達成

## 検証・プレビュー DoD 対応（plan 追記分）

- **検証**: `process_to_pptx` が図形数を返すように変更。CLI の `to-pptx` / `pipeline` で図形数を stderr に表示し、0 件のときは警告を表示。
- **プレビュー**: README に「出力の確認」を追加（図形数表示・0件警告の説明、および PowerPoint 等で開いてプレビューする手順）。
- Phase 2 完了: ruff check / pytest 通過、コミット作成。
- Phase 3: セルフレビュー（軽微: .gitignore 追加で __pycache__ 除外）。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。

## YAML 駆動 DoD 対応（plan-execute SKIP 続行）

- **YAML スキーマ**: [docs/yaml-schema.md](../../yaml-schema.md) で形式を定義・ドキュメント化。サンプルは [docs/examples/process.yaml](../../examples/process.yaml)。
- **YAML → PPTX**: `yaml2pptx.yaml_to_pptx()` で YAML から編集可能な PPTX を生成。
- **レイアウト**: アクター名は左、レーン間はグレー点線、タスクは正方形・余白ゼロ・最小 10pt、矢印間隔＝正方形一辺、改ページ時も同じ構造。
- **矢印**: タスク同士は `begin_connect` / `end_connect` で接続子として描画。
- **CLI/API**: `process-to-pptx from-yaml <input.yaml> -o <out.pptx>` で実行可能。
- **検証**: 図形数を返却し、CLI で stderr に `Shapes: N`、0 件時は警告表示。
- **プレビュー**: README に YAML の説明と出力確認手順を追記。
- **名前の整理**: パッケージ名を `process_to_pptx`、CLI を `process-to-pptx` に変更。XML 経路は mxGraph 表記に統一。
- 品質ゲート: .llm/configs/quality-gate.toml 未設定のためスキップ。手動で `uv run ruff check .` / `uv run pytest` を実行し、全通過。

## Docker Compose DoD（plan-execute 2025-02-08）

- **Docker Compose**: 指定の **src** に変換前（YAML 等）を置き、`docker compose run convert` で変換し、変換後（PPTX 等）が **gen** に出力される構成を追加。
  - `Dockerfile`: Python 3.12 + uv、`scripts/docker-entrypoint.sh` で src 内の .yaml/.yml を gen に .pptx 出力。
  - `docker-compose.yml`: サービス名 `convert`、ボリューム `./src:/src`, `./gen:/gen`。
  - `src/`, `gen/` を .gitkeep で作成。README に Docker の使い方を追記。
- Phase 1 完了: 全 DoD 達成（Docker Compose 含む）。
- Phase 2 完了: 品質ゲートは llm/codex 未使用のためスキップ。ruff / pytest 手動実行で通過。コミット作成済み。
- Phase 3 完了: Codex 未使用のためセルフレビューのみ。修正不要と判断。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。
