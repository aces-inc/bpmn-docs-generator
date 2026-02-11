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

- **Docker Compose**: 指定の **input** に変換前（YAML 等）を置き、`docker compose run convert` で変換し、変換後（PPTX 等）が **output** に出力される構成を追加。
  - `Dockerfile`: Python 3.12 + uv、`scripts/docker-entrypoint.sh` で input 内の .yaml/.yml を output に .pptx 出力。
  - `docker-compose.yml`: サービス名 `convert`、ボリューム `./input:/input`, `./output:/output`。
  - `input/`, `output/` を .gitkeep で作成。README に Docker の使い方を追記。
- Phase 1 完了: 全 DoD 達成（Docker Compose 含む）。
- Phase 2 完了: 品質ゲートは llm/codex 未使用のためスキップ。ruff / pytest 手動実行で通過。コミット作成済み。
- Phase 3 完了: Codex 未使用のためセルフレビューのみ。修正不要と判断。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。

## 入出力ディレクトリ名 input/output（plan-execute 2025-02-08）

- **DoD**: 変換前を **input**、変換後を **output** に統一。従来の src/gen を廃止。
  - `docker-compose.yml`: ボリューム `./input:/input`, `./output:/output`、環境変数 `INPUT_DIR`/`OUTPUT_DIR`。
  - `Dockerfile`: `ENV INPUT_DIR=/input OUTPUT_DIR=/output`。
  - `scripts/docker-entrypoint.sh`: `INPUT_DIR`/`OUTPUT_DIR` を参照。
  - `README.md`: 記載を input/output に変更。
  - `input/`, `output/` を .gitkeep で作成。`src/`, `gen/` を削除。
- Phase 1 完了: 全 DoD 達成（入出力ディレクトリ名 input/output 対応済み）。
- Phase 2 完了: 品質ゲート SKIP。ruff / pytest 手動実行で通過。コミット作成済み。
- Phase 3 完了: セルフレビュー。修正不要と判断。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。

## 矢印・タスク表示 DoD 対応（plan-execute 2025-02-08）

- **矢印の形状**: 既存の `_add_arrow_to_connector` で終端に triangle 矢印を付与済み。変更なし。
- **矢印の接続点**: 接続点を定数化（CONNECTION_SITE_RIGHT=3, LEFT=1）。タスクの右辺中央→左辺中央（上下中央）に結合。
- **矢印の種類**: 同一レーン（actor_index 一致）は `MSO_CONNECTOR_TYPE.STRAIGHT`、異なるレーンは `MSO_CONNECTOR_TYPE.ELBOW` で描画。
- **タスク文字の折り返し**: `text_frame.word_wrap = False` を設定。明示的改行以外は 1 行表示。
- **タスク文字色**: `p.font.color.rgb = RGBColor(0x25, 0x25, 0x25)` で視認可能な濃いグレーに設定。
- Phase 1 完了: 全 DoD 達成（矢印・タスク表示 5 項目対応済み）。
- Phase 2 完了: 品質ゲート SKIP（.llm/codex 未使用）。ruff / pytest 手動実行で通過。コミット作成済み。
- Phase 3 完了: セルフレビュー。修正不要と判断。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。

## 描画開始25%・タスク影なし DoD（plan-execute 2025-02-08 品質ゲートSKIP）

- **描画開始位置**: `ProcessLayout.content_top_offset = int(slide_height * 0.25)` を追加。アクター名・レーン区切り・ノード位置の top に適用。図の描画がスライド上端から約25%下がった位置から開始。
- **タスクの影**: `_draw_node_shape` で `shape.shadow.inherit = False` を設定し、タスクの四角に影を付けない。
- **レイアウト / 矢印 / 矢印の形状**: 既存実装で充足のため plan.md の該当 DoD を [x] に更新。
- Phase 1 完了: 全 DoD 達成。
- Phase 2: 品質ゲート SKIP（.llm/codex 未使用）。手動で ruff / pytest 通過。コミット作成済み。
- Phase 3 完了: セルフレビュー。修正不要と判断。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。

## タスク文字の配置 DoD（plan-execute 2025-02-08）

- **タスク文字の配置**: タスクは既に `add_shape()` の `text_frame` で図形内にテキストを配置済み。DoD の「余白なし」「黒文字」を明示的に対応。
  - `text_frame.margin_left/top/right/bottom = 0` で余白なし。
  - `p.font.color.rgb = RGBColor(0, 0, 0)` で黒文字。
  - 折り返しなし・最小 10pt は既存の word_wrap=False, Pt(10) で充足。
- Phase 1 完了: 全 DoD 達成。
- Phase 2 完了: 品質ゲート SKIP（.llm/codex 未使用）。ruff / pytest 手動実行で通過。コミット作成済み。
- Phase 3 完了: セルフレビュー。修正不要と判断。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。

## 入出力の場所（YAML は input に置く）

- 諸事情により、YAML を変更した場合は **input** フォルダに置く運用にした。出力は従来どおり **output** フォルダ。スキル（process-yaml）と plan の説明を input/output に合わせて更新済み。

## 分岐時の列配置 DoD（plan-execute 2025-02-08）

- **分岐時の列配置**: `_assign_columns` を BFS ベースに変更。入次数0から列を伝播し、分岐（gateway）の next はすべて「分岐の列+1」の同一列に割り当て。合流点は複数 predecessor の最大列+1。分岐先を同一列に配置し得るため横に間延びしない。
- Phase 1 完了: 全 DoD 達成（分岐時の列配置対応済み）。
- Phase 2 完了: 品質ゲート SKIP（.llm/codex 未使用）。ruff / pytest 手動実行で通過。コミット作成済み。
- Phase 3 完了: Codex 未使用のためセルフレビューのみ。変更は _assign_columns の BFS 列割り当てのみで、既存テスト全通過。修正不要と判断。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。

## アクター数スケール・スライド収まり DoD（plan-execute 2025-02-08）

- **アクター数に応じたスケール**: `yaml_loader._base_sizes_for_actors(num_actors)` を追加。1–2 アクターはレーン高・タスク大、3–4 は中、5–6 は現行相当、7+ は小さく。最小タスク一辺 MIN_TASK_SIDE_EMU（0.25 inch）で 10pt 維持。`compute_layout` でベースサイズ適用後にスケール算出。
- **スライドに必ず収まる**: 必要高さ＝アクター数×レーン高、必要幅＝列数×(task_side+gap)。利用可能高さ/幅と比較して scale = min(scale_h, scale_w, 1.0) を算出し、lane_height / task_side / gap をスケール。最小 task_side を下回らないよう補正。スケール後に final_max_cols を再計算してスライド・列を再割り当て。
- テスト: `test_actor_count_scaling`（2 アクター vs 7 アクターでレーン・タスクが少ない方が大きい）、`test_layout_fits_in_slide`（図がスライド内に収まる）を追加。
- Phase 1 完了: 全 DoD 達成。
- Phase 2 完了: 品質ゲート SKIP（.llm/codex 未使用）。ruff / pytest 手動実行で通過。コミット作成済み。
- Phase 3 完了: セルフレビュー。修正不要と判断。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。

## タスク60%・左端・点線・同一アクター複数分岐 DoD（plan-execute 2025-02-08）

- **タスク正方形の比率**: `TASK_SIDE_RATIO = 0.6` を導入。`_base_sizes_for_actors` で task_side = lane_height * 0.6、スケール後も `layout.task_side = max(int(layout.lane_height * 0.6), MIN_TASK_SIDE_EMU)` で約60%を維持。
- **左端開始位置**: `ProcessLayout.left_label_width` を 2.0 inch → 1.2 inch に変更。アクター名とタスク領域の左端を近づけ一体感を確保。
- **点線の範囲**: `_draw_lane_separators` の点線の始点を `x1 = layout.left_label_width` から `x1 = 0` に変更。レーンの左端（スライド左端）まで届くように描画。
- **同一アクターへの複数分岐**: `compute_layout` で同一 (slide_index, actor_index, col_in_slide) のノードをグループ化。2件以上のグループはレーン高さの90%を縦に均等分割し、各ノードの top/height を再計算。横幅は task_side のまま。
- Phase 1 完了: 全 DoD 達成（未完了4項目対応済み）。
- Phase 2 完了: 品質ゲート SKIP（.llm/codex 未使用）。ruff / pytest 手動実行で通過。コミット作成済み。
- Phase 3 完了: セルフレビュー。変更は yaml_loader（60%比率・左端幅・同一セル縦分割）と yaml2pptx（点線左端）のみ。既存テスト全通過。修正不要と判断。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。

## スタート・ゴール DoD（plan-execute 2025-02-09、1件ずつ実装）

- **スタート・ゴール**: YAML で `type: start` / `type: end` を指定可能に。開始・終了ノードを PPTX 上で正円（MSO_SHAPE.OVAL、幅＝高さ）で描画。
  - `yaml_loader`: type に "start", "end" を許可。
  - `yaml2pptx`: start/end のとき OVAL を描画し、セル内で幅＝高さにして正円に。
  - `docs/yaml-schema.md`: type に start/end を追記。
  - テスト: `test_load_accepts_start_end_types`, `test_start_end_drawn_as_oval` を追加。
- 品質ゲート: SKIP。ruff / pytest 手動実行で通過。
- 実装・テスト・確認・コミットを 1 件ずつ実施。

## 分岐図形 DoD（plan-execute 2025-02-09、2件目）

- **分岐図形**: 条件分岐は菱形＋✕、並行処理は菱形＋＋で描画。
  - YAML に `gateway_type: exclusive`（省略可）／`parallel` を追加。ProcessNode に gateway_type を追加。
  - yaml2pptx: gateway 描画時にテキストを "✕"（exclusive）または "＋"（parallel）に設定。
  - スキーマ・テスト（test_load_gateway_type, test_gateway_drawn_with_x_or_plus）追加。
- 品質ゲート: SKIP。ruff / pytest 通過。コミット済み。

## スライド左右10pt余白 DoD（plan-execute 2025-02-09、3件目）

- **スライド左右10pt余白**: left_margin / right_margin を 10pt（SLIDE_MARGIN_MIN_EMU）以上に。ノード・アクター名・点線の X を left_margin 分オフセットし、content_width から左余白を減算。
- テスト: test_slide_margin_10pt で余白とノード範囲を検証。
- 品質ゲート: SKIP。ruff / pytest 通過。

## 分岐矢印のラベル DoD（plan-execute 2025-02-09、4件目）

- **分岐矢印のラベル**: 分岐した矢印に説明テキスト（Yes/No 等）を表示可能に。
  - YAML: `next` を `[{ id: 2, label: "Yes" }, { id: 3, label: "No" }]` 形式で指定可能。従来の `[2, 3]` もそのまま利用可能。
  - `yaml_loader`: ProcessNode に `next_labels`、ProcessLayout に `edge_labels` を追加。load 時に dict 要素から id/label を抽出。
  - `yaml2pptx`: 矢印描画後、`edge_labels` にラベルがあれば矢印の中点付近に小さいテキストボックスで表示（フォント 8pt、中央揃え）。
  - スキーマ・テスト: test_load_next_with_labels, test_compute_layout_edge_labels, test_branch_arrow_labels_drawn を追加。docs/yaml-schema.md に next のオブジェクト形式を追記。
- 品質ゲート: SKIP。ruff / pytest 手動実行で通過。
- 実装・テスト・確認・コミットを 1 件ずつ実施。

## ループ DoD（plan-execute 2025-02-09、影響度順 1件目）

- **ループ**: YAML の `next` で開始ノードの ID を参照可能（既存のまま）。レイアウトで開始ノードを常に列0に固定し、タスク→開始の矢印が左向きに描画されるようにした。
  - `yaml_loader._assign_columns`: 列割り当て後に `type == "start"` のノードの column を 0 に強制。
  - エッジは既存の next 収集で (task_id, start_id) が含まれるため、矢印はそのまま描画される。
  - スキーマ: docs/yaml-schema.md にループの説明を追記。
  - テスト: `test_loop_start_at_column_zero_and_edge_present` を追加。
- 品質ゲート: SKIP。ruff / pytest 通過。実装・テスト・確認・コミット済み。

## 人のタスクの接続 DoD（plan-execute 2025-02-11、1件目）

- **人のタスクの接続**: 孤立したフローノード（task/gateway で入次数・出次数がともに 0）を検出し、CLI で警告表示。
  - `yaml_loader.find_isolated_flow_nodes(nodes)` を追加。YAML 検証として利用可能。
  - CLI `from-yaml`: load 後に `find_isolated_flow_nodes` を実行し、孤立 ID があれば stderr に Warning を出力。
  - テスト: `test_find_isolated_flow_nodes_none`, `test_find_isolated_flow_nodes_isolated`, `test_find_isolated_flow_nodes_start_end_ignored` を追加。
- 実装・テスト・確認・コミットを 1 件ずつ実施。
