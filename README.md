# drawio-to-pptx

AI が出力した Drawio 形式の XML を .drawio に変換し、編集可能な PPTX を生成するパイプライン。

## 要件

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)（推奨）

## セットアップ

```bash
uv sync
```

## 使い方

### 一連フロー（XML → .drawio → PPTX）

```bash
uv run drawio-to-pptx pipeline input.xml -o output.pptx
# 中間 .drawio も保存する場合
uv run drawio-to-pptx pipeline input.xml -o output.pptx --drawio diagram.drawio
```

### XML を .drawio に変換

```bash
uv run drawio-to-pptx to-drawio input.xml -o diagram.drawio
# 標準入力から
cat input.xml | uv run drawio-to-pptx to-drawio - -o diagram.drawio
```

### .drawio / XML から PPTX を生成

```bash
uv run drawio-to-pptx to-pptx diagram.drawio -o slides.pptx
```

## 出力の確認

- **図形数の表示**: `pipeline` および `to-pptx` 実行時、標準エラー出力に `Shapes: N` が表示されます。図形が 1 つも描画されなかった場合は `Warning: no shapes were added to the slide. Check input XML.` と表示されます。
- **見た目のプレビュー**: 生成した PPTX は PowerPoint、Keynote、LibreOffice Impress などで開き、スライド上の図形の配置・テキストを確認してください。

## 入力 XML について

- Drawio の **mxGraphModel** に準拠した XML を想定しています。
- `<mxGraphModel>...</mxGraphModel>` 全体、または `<root>` 内の mxCell 断片を入力できます。
- 1 ページ・基本的な図形（四角、楕円など）とテキストを優先しています。
