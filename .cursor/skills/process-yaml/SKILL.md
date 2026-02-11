---
name: process-yaml
description: Write or edit YAML for the process-to-pptx pipeline that defines BPMN-style business process diagrams with swimlanes. Use when creating or editing process YAML, when the user asks for business process, swimlane, BPMN, or YAML that converts to PPTX.
---

# 業務プロセス図 YAML の書き方

このプロジェクトの `from-yaml` で使う YAML は、**BPMN 風の業務プロセス（スイムレーン・タスク・分岐・フロー）** を定義する。人が編集しやすく、PPTX に変換すると編集可能な図形になる。

## 入出力の場所

- **入力 YAML**: 作成・編集した YAML は **`input/`** フォルダに置く。
- **出力 PPTX**: 変換後の PPTX は **`output/`** フォルダに出力する（`-o` で指定）。Docker 利用時も `input/` に YAML を置けば `output/` に PPTX が生成される。

---

## ルート構造

```yaml
actors:
  - アクター名1
  - アクター名2
nodes:
  - id: 1
    type: task
    actor: 0
    label: 表示テキスト
    next: [2]
```

- **actors**: スイムレーン名のリスト。**上から下**の順でレーンが並ぶ（PPTX では名前は左に表示）。
- **nodes**: ノードのリスト。`id` で一意、`next` で接続先を参照。**列（左→右の位置）は `next` のつながりから自動計算**される（YAML の並び順は列の順にはならない）。

---

## ノードのキー

| キー | 必須 | 説明 |
|------|------|------|
| `id` | ✅ | 一意識別子。数値または文字列。`next` から参照される。 |
| `type` | ✅ | `task`（タスク＝四角）、`gateway`（分岐＝ひし形）、`start`（開始＝正円）、`end`（終了＝正円）、`artifact`（成果物＝フローチャートのデータ図形）、`service`（システム接続用＝磁気ディスク図形） |
| `gateway_type` | - | `gateway` のときのみ。`exclusive`（条件分岐・菱形に **✕**）または `parallel`（並行・菱形に **＋**）。省略時は `exclusive`。 |
| `actor` | ✅ | 属するスイムレーン。`0` 始まりのインデックスか、`actors` の名前（文字列） |
| `label` | ✅ | 図形に表示するテキスト（分岐は PPTX 上では ✕/＋ のみ表示） |
| `next` | ✅ | 接続先の ID のリスト。例: `[2]` または `[3, 4]`。空なら `[]`。**矢印ラベル**: 分岐先ごとにラベル（Yes/No 等）を付けたい場合は `[{ id: 2, label: "Yes" }, { id: 3, label: "No" }]` のようにオブジェクトのリストで書く。`id` は必須、`label` は省略可。**ループ**: 開始ノードの ID を指定すると、そのタスクから開始へ戻る矢印が PPTX に描画される（開始は常に左端に配置）。 |
| `request_to` | - | システム接続。このタスクからリクエストを送るサービスノードの ID のリスト。人タスク→サービスが点線（人側○・サービス側矢印）で描画される。 |
| `response_from` | - | システム接続。このタスクがレスポンスを受け取るサービスノードの ID のリスト。サービス→人タスクが下→上の点線で描画される。 |

---

## レイアウトの考え方（PPTX での動き）

- **左 = アクター名**  
  各レーンの左にアクター名が表示され、その右からタスク領域が始まる。アクター名は**角のある長方形（角丸ではない）**内に表示され、**塗りつぶしなし・枠線黒・フォント黒・影なし**。**スイムレーンの高さの縦方向中央**に配置される。アクター枠の右端と最初のタスク列の間に**10pt の余白**があり、枠とタスクは引っ付かない。

- **左→右 = 時間の流れ（列）**  
  **列は `next` のつながりで決まる**。入次数 0 のノードが列 0、その `next` が列 1、さらにその先が列 2 …。分岐（`gateway`）の複数 `next` は**同じ列**にまとめて配置され、横に間延びしない。

- **同一アクターに複数分岐先がある場合**  
  同じレーン・同じ列に複数タスクがあると、そのレーンの高さの 90% を**縦に分割**して並ぶ。横幅は 1 タスク時と同じ。分岐で「Yes/No」など同じレーンに複数置く場合に便利。

- **ノードの形**  
  タスクはレーン高さの約 60% の正方形（同一列に複数ある場合は縦長の矩形）。**開始・終了**（`type: start` / `end`）は**正円**で描画される。分岐（`gateway`）はひし形で、条件分岐は **✕**、並行は **＋** が中に表示される。**成果物**（`type: artifact`）はフローチャートのデータ図形、**サービス**（`type: service`）は磁気ディスク図形で描画され、`label` に名前を書く。レーン間はグレーの点線で区切り、点線はレーン左端まで届く。

- **スライド余白**  
  スイムレーン全体はスライドの左端・右端からそれぞれ 10pt 以上離して配置される。

- **矢印**  
  タスク同士は矢印（コネクタ）で接続。同一レーン内は直線、異なるレーン間は折れ曲がり矢印。**接続点**は自動: **基本は左から入り、右から出る**（送る側は右辺中央から出し、受け側は左辺中央で受ける）。**同列**（同じ列に複数ノードがある場合）のときだけ上下に伸ばし、上レーンへは上辺・下レーンへは下辺で出入りする。矢印・アクター・レーン線など**すべての要素に影は付かない**。分岐で `next: [{ id, label: "Yes" }, ...]` と書いたラベルは矢印の近くに表示される。

- **スライドに収まる**  
  アクター数・列数に応じてレーン高さとタスクサイズが自動調整され、はみ出しは改ページで次のスライドに続く。

---

## 良い書き方のコツ

1. **タスク名は短く**  
   図形内に文字が収まり、折り返しなし・最小 10pt で表示される。長いラベルは省略するか、2〜3 語にまとめる。

2. **`next` でフローを一意に**  
   列は `next` のつながりから決まる。どこからどこへ流れるかを `next` で明確に書く。未定義 ID は無視されるので、参照先の `id` は typo しない。

3. **分岐は `gateway` + 複数 `next`**  
   `type: gateway` で `next: [3, 4]` のように複数先を書く。条件分岐（Yes/No など）は省略で菱形に ✕、並行（AND 分岐）は `gateway_type: parallel` で菱形に ＋。3 と 4 が同じアクターなら、PPTX では同じ列に縦並びで表示される。**矢印にラベル**（Yes/No、承認/差し戻しなど）を付けたい場合は `next: [{ id: 3, label: "Yes" }, { id: 4, label: "No" }]` と書く。PPTX では各矢印の近くにそのテキストが表示される。

4. **開始・終了は `start` / `end`**  
   フローの開始ノードは `type: start`、終了ノードは `type: end` にすると、PPTX 上で正円で描画される。

5. **成果物は `artifact`**  
   作成・保存する成果物（見積書、契約書など）は `type: artifact` にし、`label` に成果物名を書く。PPTX ではフローチャートのデータ図形で描画される。

6. **ループは `next` で開始 ID を指定**  
   どこかで「開始に戻る」フローにしたいときは、そのタスクの `next` に開始ノードの `id` を入れる。例: 開始が `id: 0` なら `next: [0]`。PPTX では開始が常に左端に置かれ、戻り矢印が描画される。

7. **システム接続は `service` + `request_to` / `response_from`**  
   システムレーンに `type: service` のノードを 1 つ置き、`label` にサービス名（例: Salesforce）を書く。人タスクからリクエストを送る場合はそのタスクに `request_to: [サービスID]` を指定すると、点線（人側○・サービス側矢印）で描画される。レスポンスを受け取るタスクには `response_from: [サービスID]` を指定すると、サービスからそのタスクへ下→上の点線が描かれる。列がずれる場合は L 字点線になる。

8. **YAML の並びは「読みやすさ」で**  
   列の順は自動計算のため、YAML 上はブロックごとにまとめたりコメントで区切ったりしてよい（例: `# ----- 商談・見積 -----`）。

9. **アクター数**  
   多いとレーンとタスクは小さくなる。必要なら 4〜6 レーン程度に抑えると 1 枚に収まりやすい。

10. **スキーマ検証はなし**  
   ベストエフォートで変換する。`actor` や `next` の typo は無視される可能性があるので、変換後に PPTX で確認する。

---

## 最小例（開始・終了付き）

開始と終了を正円で描く場合は `type: start` / `type: end` を使う。

```yaml
actors:
  - 担当者
nodes:
  - id: 1
    type: start
    actor: 0
    label: 開始
    next: [2]
  - id: 2
    type: task
    actor: 0
    label: 作業
    next: [3]
  - id: 3
    type: end
    actor: 0
    label: 終了
    next: []
```

タスクだけの最小例（従来どおり）:

```yaml
actors:
  - 担当者
nodes:
  - id: 1
    type: task
    actor: 0
    label: 作業
    next: [2]
  - id: 2
    type: task
    actor: 0
    label: 確認
    next: []
```

---

## 分岐付き例

```yaml
actors:
  - お客様
  - 営業
nodes:
  - id: 1
    type: task
    actor: 0
    label: 要件検討
    next: [2]
  - id: 2
    type: gateway
    actor: 0
    label: 成約?
    gateway_type: exclusive   # 省略可。条件分岐＝菱形に ✕
    next: [3, 4]
  - id: 3
    type: task
    actor: 1
    label: 契約手続き
    next: [5]
  - id: 4
    type: task
    actor: 0
    label: 見送り
    next: []
  - id: 5
    type: task
    actor: 1
    label: キックオフ
    next: []
```

**矢印にラベルを付ける場合**（Yes/No 等を矢印の横に表示したい場合）は、分岐ノードの `next` をオブジェクトのリストにし、各要素に `id` と `label` を書く。

```yaml
  - id: 2
    type: gateway
    actor: 0
    label: 成約?
    gateway_type: exclusive
    next:
      - { id: 3, label: "Yes" }
      - { id: 4, label: "No" }
```

---

## 同一アクターに複数分岐先（縦並びになる例）

分岐先の 3 と 4 がどちらも `actor: 1` なので、PPTX では**同じ列に縦に 2 つ**並ぶ。

```yaml
actors:
  - 依頼者
  - 担当者
nodes:
  - id: 1
    type: task
    actor: 0
    label: 依頼
    next: [2]
  - id: 2
    type: gateway
    actor: 0
    label: 種別?
    next: [3, 4]
  - id: 3
    type: task
    actor: 1
    label: A対応
    next: [5]
  - id: 4
    type: task
    actor: 1
    label: B対応
    next: [5]
  - id: 5
    type: task
    actor: 1
    label: 完了報告
    next: []
```

---

## ループの例（開始に戻る）

タスクの `next` に開始ノードの ID を書くと、そのタスクから開始へ戻る矢印が PPTX に描かれる。開始ノードは常に左端（列 0）に配置される。

```yaml
actors:
  - 担当者
nodes:
  - id: 0
    type: start
    actor: 0
    label: 開始
    next: [1]
  - id: 1
    type: task
    actor: 0
    label: 作業1
    next: [2]
  - id: 2
    type: task
    actor: 0
    label: 作業2
    next: [0]   # 開始(0)に戻る → ループ矢印が描画される
```

---

## 成果物の例

作成・保存する成果物は `type: artifact` にし、`label` に成果物名を書く。PPTX ではフローチャートのデータ図形で描画される。

```yaml
actors:
  - 担当者
nodes:
  - id: 1
    type: task
    actor: 0
    label: 作成
    next: [2]
  - id: 2
    type: artifact
    actor: 0
    label: 見積書
    next: [3]
  - id: 3
    type: task
    actor: 0
    label: 確認
    next: []
```

---

## システム接続の例

人タスクからシステム（サービス）へリクエストを送り、レスポンスを受け取る流れを表す。システムレーンに `type: service` のノードを 1 つ置き、人タスクに `request_to` / `response_from` でサービス ID を指定する。

```yaml
actors:
  - 営業
  - Salesforce
nodes:
  - id: 17
    type: task
    actor: 0
    label: 受注登録依頼
    next: [18]
    request_to: [sf-svc]
  - id: 18
    type: task
    actor: 1
    label: 受注登録
    next: [19]
  - id: sf-svc
    type: service
    actor: 1
    label: Salesforce
  - id: 19
    type: task
    actor: 0
    label: 確認
    next: []
```

- `request_to: [sf-svc]` → 人タスクからサービスへ点線（人側○・サービス側矢印）。
- レスポンスを表す場合は、レスポンスを受け取る人タスクに `response_from: [sf-svc]` を追加すると、サービスからそのタスクへ下→上の点線が描かれる。

---

## 変換コマンド

```bash
uv run process-to-pptx from-yaml input/process.yaml -o output/process.pptx
```

Docker の場合: `input/` に YAML を置き、`docker compose run convert` で変換すると `output/` に PPTX が出力される。

---

## 参照

- 詳細スキーマ: `docs/yaml-schema.md`
- サンプル: `input/process.yaml`（コメントでブロック分けした実例）
