# 作業記録: Drawio XML → PPTX

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
- Drawio/XML → PPTX: `drawio2pptx.drawio_to_pptx` / `drawio_file_to_pptx`
- CLI: `drawio-to-pptx to-drawio | to-pptx | pipeline`
- Phase 1 完了: 全 DoD 達成

## 検証・プレビュー DoD 対応（plan 追記分）

- **検証**: `drawio_to_pptx` が図形数を返すように変更。CLI の `to-pptx` / `pipeline` で図形数を stderr に表示し、0 件のときは警告を表示。
- **プレビュー**: README に「出力の確認」を追加（図形数表示・0件警告の説明、および PowerPoint 等で開いてプレビューする手順）。
- Phase 2 完了: ruff check / pytest 通過、コミット作成。
- Phase 3: セルフレビュー（軽微: .gitignore 追加で __pycache__ 除外）。
- Phase 4: リモート未設定のため PR は未作成。main にコミット済み。
