---
Created: 2025-02-11
Owner: x4066x
Status: draft
---

# 実装計画: process-to-pptx 未完了 DoD の整理と実装

## Goal

`docs/plans/20250207-process-to-pptx/plan.md` で未完了の 3 項目（分岐矢印のラベル・システム接続・矢印の接続点）について、**まずリファクタリングを行い**、そのうえで仕様どおり動作するようにする。あわせて入力例は **input/** の YAML に合わせ、**docs/yaml-schema.md** を現状に合わせて更新する。完了後、問題なければ **process-yaml スキル** と **yaml-schema.md** の更新を実施する。

## Background / Motivation

- 3 つの未完了 DoD には**一部すでに実装が入っているが、正常に動いていない**状態のコードが残っている可能性がある。
- 未使用の関数・変数を残したまま機能追加すると複雑化するため、**リファクタリングを最初に行い**、使っていない関数や変数を除くなど最低限の整理をしてから本実装に進む。
- 入力例は **input/**（`process.yaml`, `bank-sales.yaml`, `it-sales.yaml`）を基準とし、スキーマ・スキルもこれに合わせて更新する。

## Constraints

- **既存の YAML スキーマ・PPTX レイアウト仕様**（`docs/plans/20250207-process-to-pptx/plan.md` の Constraints）は維持する。新規のレイアウト仕様は追加しない。
- **入力例**: 挙動確認・スキーマ・スキルの記述は **input/** の YAML（`process.yaml`, `bank-sales.yaml`, `it-sales.yaml`）を例とする。
- **検証方法**: README に従い、`docker compose build` ののち `docker compose run convert` で変換し、出力 PPTX で確認する。
- 使用言語・ランタイムは既存どおり（Python + uv）。既存パイプライン（XML → .drawio / PPTX）の名前整理済み部分には触れない。

## Definition of Done

**Phase 0: リファクタリング（最初に実施）**

- [x] YAML→PPTX まわりのコード（`process_to_pptx/yaml2pptx.py` 等）を対象に、未使用の関数・変数を特定し削除している。（確認の結果、未使用なしのため整理のみ）
- [x] 上記の最低限の整理後も、`docker compose build` → `docker compose run convert` で input の YAML が PPTX に変換できる状態を維持している。

**Phase 1: 未完了 DoD の実装**

- [x] **分岐矢印のラベル**: YAML で `next: [{ id: 先のID, label: "表示テキスト" }, ...]` と指定した分岐矢印に、PPTX 上で説明テキスト（Yes/No 等）が**矢印の近くに表示されている**。ラベル指定があるのに表示されない場合は不備とする。
- [x] **システム接続**: システム側に磁気ディスク図形でデータ方向を表示。人→システムは点線・人側○・サービス側矢印下向き、レスポンスは下→上点線。システムレーン内はサービス 1 つに複数タスクから点線。列ずれ時は elbow（L 字）点線で描画されている。
- [x] **矢印の接続点**: 矢印がタスクの辺に応じて正しく結合されている（前タスクから: 同レーンは左、上レーンは上、下レーンは下。次タスクへ: 同レーンまたは下は右、上は上）。矢印・アクター・レーン線に影が付いていない。

**検証**

- [x] 上記はいずれも **input/** の YAML を入力に、`docker compose build` → `docker compose run convert` で生成した PPTX を開き、目視または既存テストで確認できる。

**ドキュメント・スキル**

- [x] **docs/yaml-schema.md** を、input の YAML で実際に使われている形式（分岐ラベル・成果物・ループ・システム接続など）に合わせて更新している。
- [x] 問題なければ **.cursor/skills/process-yaml/SKILL.md** を更新する旨を本プランに記載済みである（実施は完了確認後）。→ 本実装完了確認後、スキル側に `type: service`・`request_to`・`response_from` の記述を追加する。

## Assumptions

- リファクタリングは「未使用の削除・最低限の整理」に留め、既存の振る舞いが変わるような大きな構造変更は行わない。
- input の YAML にシステム接続や分岐ラベルが含まれていれば、それを正しく描画できることが目標である。含まれていない場合は、スキーマ・スキル上は「書ける形式」としてドキュメント化する。
- Docker Compose の利用方法は README の記述どおりとする（`docker compose build` → `docker compose run convert`）。

## Decision Required

| ID | 内容 | 選択肢 | Priority |
|----|------|--------|----------|
| DR-001 | リファクタリングの範囲 | yaml2pptx.py のみ / yaml_loader・xml2pptx も含める | P1 |
| DR-002 | システム接続が input の YAML にない場合 | サンプルを input に 1 件追加する / 既存 process.yaml 等に追記する / スキーマのみ記載し実データは後回し | P1 |

## References

- 親プラン: `docs/plans/20250207-process-to-pptx/plan.md`
- 入力例: `input/process.yaml`, `input/bank-sales.yaml`, `input/it-sales.yaml`
- スキーマ: `docs/yaml-schema.md`
- スキル: `.cursor/skills/process-yaml/SKILL.md`
- 検証手順: README「Docker Compose（YAML ビルド）」— `docker compose build` → `docker compose run convert`
