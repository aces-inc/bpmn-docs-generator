# 作業記録: process-to-pptx 未完了 DoD の整理と実装

## 前提

- 計画書: [plan.md](./plan.md)
- 品質ゲート: ユーザー指示により SKIP

## Phase 1: 実装

### 開始

- 2025-02-11: plan-execute 開始。Goal/DoD に従い Phase 0（リファクタ）→ Phase 1（未完了 DoD）の順で実施。

### DR 方針

- **DR-001（リファクタ範囲）**: yaml2pptx.py を主対象とし、yaml_loader は未使用があれば削除。xml2pptx は既存パイプラインのため触れない。
- **DR-002（システム接続が input にない場合）**: 実装後に process.yaml にシステム接続のサンプルを 1 件追記して検証に使う。

### Phase 0 完了

- yaml2pptx / yaml_loader を確認。未使用の関数・変数はなし（find_isolated_flow_nodes は CLI で使用）。リファクタ範囲は最小限で維持。
- `docker compose build` → `docker compose run convert` および `uv run process-to-pptx from-yaml input/process.yaml -o output/process.pptx` で変換可能な状態を維持。

### Phase 1 実装完了

- **分岐矢印のラベル**: process.yaml の id:12 を `next: [{ id: 13, label: "No" }, { id: 14, label: "Yes" }]` に変更。layout.edge_labels と既存描画で矢印近くに表示。既存テスト `test_branch_arrow_labels_drawn` が通過。
- **矢印の接続点**: _connection_site_from / _connection_site_to を DoD どおりに修正（前から: 同レーン左・上レーン上・下レーン下、次へ: 同レーンまたは下は右・上は上）。通常矢印を headEnd（終点側）に変更。
- **システム接続**: yaml_loader に type: service、request_to、response_from を追加。ProcessLayout.system_edges、_assign_columns の extra_edges 対応。yaml2pptx でサービスを FLOWCHART_MAGNETIC_DISK、システム接続を点線（人側○・サービス側矢印、request/response）で描画。process.yaml に sf-svc と id:17 の request_to を追加。
- **検証**: uv run pytest 33 件すべて通過。uv run process-to-pptx from-yaml input/process.yaml -o output/process.pptx で Shapes: 132 で保存成功。
- **ドキュメント**: docs/yaml-schema.md に service / request_to / response_from とシステム接続の説明を追記。

### Phase 1 完了

- 全 DoD 項目を実装済み。品質ゲートは SKIP のため Phase 2 は省略し、実装コミット後に Phase 3（レビュー）・Phase 4（PR）へ進む。

---

（以下、実施ごとに追記）
