# 作業記録: タスクサイズ・レーン縦伸ばし・列数・フォントのパラメータ化

## 2025-02-18

### plan-execute 開始
- 計画: docs/plans/20250218-task-size-and-columns/plan.md
- 品質ゲート: ユーザー指示により SKIP

## Goal
1. タスクサイズを layout パラメータで指定可能に（未指定時は現状維持）
2. アクターが少ないときは余白内でレーンを縦に広げ、タスクは指定サイズのまま中央配置
3. 1スライドあたりの列数を layout で指定可能に（未指定時は幅から自動計算）
4. スイムレーン区切り線はアクター四角の境界（四角と四角の間）に描画
5. フォントサイズを layout で指定可能に

## Definition of Done
- [x] タスクサイズのパラメータ化（layout.task_size_ratio）
- [x] アクターが少ないときの縦伸ばし（2～4 アクターで描画領域をレーンに割り当て）
- [x] 列数のパラメータ化（layout.max_cols_per_slide）
- [x] スイムレーン区切り線がレーン境界と一致（既存実装で lane_height 境界に描画済み）
- [x] フォントサイズのパラメータ化（layout.task_font_pt / actor_font_pt / label_font_pt）
- [x] docs/yaml-schema.md と SKILL.md に追記

### Phase 1 完了
全 DoD 達成。品質ゲートはユーザー指示により SKIP。

## DR 方針（実装時に採用）
- **DR-001** タスクサイズ: キー `task_size_ratio`。レーン高さに対する比率（0.0～1.0）。未指定時は 0.6（現状維持）。
- **DR-002** 列数: キー `max_cols_per_slide`。既存の compute_layout 引数名に合わせる。
- **DR-003** フォント: 種別ごと `task_font_pt`, `actor_font_pt`, `label_font_pt`。未指定時は 10, 10, 8。
