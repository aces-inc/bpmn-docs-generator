# 作業記録: 余白コンフィグ化とシステム用スイムレーン・接続ルール

## 2025-02-17

### plan-execute 開始
- 計画: Part 1（余白のコンフィグ化）を先行実装。Part 2 は DR-002/003 未決定のためスコープ外。
- 品質ゲート: ユーザー指示により SKIP。

### Phase 1: 実装
- [x] DoD Part 1-1: 余白をプロセス YAML で指定（layout.margins）
- [x] DoD Part 1-2: 左右・上下が compute_layout と PPTX 描画で一貫して効く
- [x] DoD Part 1-3: test_slide_margin_10pt 相当の検証を維持（test_layout_margins_from_yaml 追加）
- [x] DoD Part 1-4: SKILL.md に余白コンフィグの書き方を追記（「対応予定」注記削除で確定）
- [x] DoD Part 1-5: docs/yaml-schema.md に余白コンフィグを反映

Phase 1 完了: Part 1 全 DoD 達成（Part 2 は DR-002/003 未決定のためスコープ外）

### Phase 2: 品質ゲート
- ユーザー指示により SKIP。全テスト 35 件は手動実行で通過済み。
- 実装コミット: feat: 余白のコンフィグ化（layout.margins）
- feature ブランチ \`feat/margins-config\` を push 済み。main は origin に合わせてリセット済み。

### Phase 3: レビュー
- 品質ゲート SKIP のため Codex レビューは省略。変更内容のセルフ確認で問題なしと判断。

### Phase 4: PR 作成
- ブランチ \`feat/margins-config\` は \`origin/feat/margins-config\` に push 済み。
- PR 作成: ブラウザで https://github.com/aces-inc/bpmn-docs-generator/pull/new/feat/margins-config を開き、タイトル「feat: 余白のコンフィグ化（layout.margins）」で PR を作成してください。

### plan-execute 再開（品質ゲート SKIP）
- Part 1: 全 DoD 達成済み。Part 2: DR-002（P0）未決定のため実装着手不可 → DR 作成して停止。

### plan-execute 再開（Part 2 実装）
- DR-002 決定済み（接頭辞 `[システム]` / 接尾辞 `_`）のため Part 2 実装を実施。
- [x] DoD Part 2-1: 接続ルール（タスク下辺・システム上辺）— yaml2pptx.py で request/response の接続点を変更。
- [x] DoD Part 2-2: システム用レーン指定 — yaml_loader に is_system_lane_actor, _collapse_system_lanes を追加。
- [x] DoD Part 2-3: システム用レーン内にユニークシステム名を配置 — サービスノードの列を unique label 順で割り当て。
- [x] DoD Part 2-4: request_to/response_from 矢印接続 — 既存 system_edges で描画、接続点を DoD に合わせて変更済み。
- [x] DoD Part 2-5: 1レーン集約・レイアウト — テストで検証（test_collapse_system_lanes_in_compute_layout, test_system_lane_actor_detection）。
- [x] DoD Part 2-6: docs/yaml-schema.md と SKILL.md にシステム用レーン・接続ルールを反映。
Phase 1 完了: Part 2 全 DoD 達成。

### Phase 2: 品質ゲート
- .llm/configs/quality-gate.toml 未定義のためスキップ。手動で pytest 37 件通過を確認。
- 実装コミット: feat: システム用スイムレーン・接続ルール（DR-002）

### Phase 3: レビュー
- セルフ確認: 接続ルール・システムレーン集約・ドキュメント整合。修正不要と判断。

### Phase 4: PR 作成
- ブランチ \`feat/margins-config\` を push 後、ブラウザで PR を作成してください。
- 例: https://github.com/aces-inc/bpmn-docs-generator/compare/feat/margins-config
- タイトル例: feat: 余白コンフィグ化・システム用スイムレーン（layout.margins + DR-002）

### plan-execute 再開（Part 3 実装・品質ゲート SKIP）
- Part 1・Part 2 は完了済み。Part 3（システム列の見た目＋矢印ラベル）を実装。
- [x] DoD Part 3-1: システム列に磁気ディスクでシステム名表示 — 既存実装で対応済み（FLOWCHART_MAGNETIC_DISK）。
- [x] DoD Part 3-2: request_to / response_from を \`[{ id, label? }]\` に拡張し、矢印にアクション名ラベルを描画（yaml_loader + yaml2pptx + test 追加）。
- [x] DoD Part 3-3: docs/yaml-schema.md と SKILL.md にラベル付き書き方・書き換え可能である旨を反映。
Phase 1 完了: Part 3 全 DoD 達成。

### Phase 2: 品質ゲート
- ユーザー指示により SKIP。

### Phase 3: レビュー
- 品質ゲート SKIP のため Codex レビューは省略。セルフ確認で問題なし。

### Phase 4: PR 作成
- コミット: feat: システム矢印にアクション名ラベル（request_to/response_from [{ id, label? }]）
- ブランチ \`feat/margins-config\` を push 済み。PR は以下で作成可能:
  - https://github.com/aces-inc/bpmn-docs-generator/compare/feat/margins-config
  - タイトル例: feat: 余白コンフィグ化・システム用スイムレーン・矢印ラベル（Part 1–3）
