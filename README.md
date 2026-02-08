# process-to-pptx

業務プロセス図を **YAML** または **mxGraph XML** から編集可能な PPTX に変換するパイプライン。XML は .drawio ファイルにも変換できる。

## 要件

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)（推奨）

## Docker Compose（YAML ビルド）

Docker のみで変換する場合は、**input** に YAML を置き、`docker compose run` で変換すると **output** に PPTX が出力されます。

```bash
# 初回のみイメージビルド
docker compose build

# input/ に YAML を置いて実行（例: input/process.yaml → output/process.pptx）
docker compose run convert
```

- **入力**: `input/` フォルダに変換前のファイル（.yaml / .yml）を置く
- **出力**: `output/` フォルダに変換後の .pptx が出力される
- 必要に応じて `docker-compose.yml` にサービスを追加し、並列実行なども可能

## セットアップ

```bash
uv sync
```

## 使い方

### YAML から PPTX（推奨）

業務プロセスを YAML で定義し、そのまま PPTX に変換します。

```bash
uv run process-to-pptx from-yaml docs/examples/process.yaml -o output.pptx
```

YAML のスキーマは [docs/yaml-schema.md](docs/yaml-schema.md) を参照してください。

### 一連フロー（XML → .drawio → PPTX）

```bash
uv run process-to-pptx pipeline input.xml -o output.pptx
# 中間 .drawio も保存する場合
uv run process-to-pptx pipeline input.xml -o output.pptx --drawio diagram.drawio
```

### XML を .drawio に変換

```bash
uv run process-to-pptx to-drawio input.xml -o diagram.drawio
# 標準入力から
cat input.xml | uv run process-to-pptx to-drawio - -o diagram.drawio
```

### .drawio / XML から PPTX を生成

```bash
uv run process-to-pptx to-pptx diagram.drawio -o slides.pptx
```

## 出力の確認

- **図形数の表示**: `from-yaml`・`pipeline`・`to-pptx` 実行時、標準エラー出力に `Shapes: N` が表示されます。図形が 1 つも描画されなかった場合は `Warning: no shapes were added to the slide. Check input.` が表示されます。
- **見た目のプレビュー**: 生成した PPTX は PowerPoint、Keynote、LibreOffice Impress などで開き、スライド上の図形の配置・テキストを確認してください。

## 入力形式

### YAML（業務プロセス図）

- スキーマ: [docs/yaml-schema.md](docs/yaml-schema.md)
- アクター（スイムレーン）・タスク／分岐・接続先を記述し、PPTX のレイアウト（アクター名左、レーン区切り、正方形タスク、矢印接続）で出力します。

### mxGraph XML

- **mxGraphModel** に準拠した XML を想定しています。
- `<mxGraphModel>...</mxGraphModel>` 全体、または `<root>` 内の mxCell 断片を入力できます。
- 1 ページ・基本的な図形（四角、楕円など）とテキストを優先しています。
