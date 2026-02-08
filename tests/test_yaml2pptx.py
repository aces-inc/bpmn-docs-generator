"""yaml2pptx のテスト。"""

from pathlib import Path

from pptx.enum.shapes import MSO_SHAPE
from pptx import Presentation

from process_to_pptx import yaml2pptx
from process_to_pptx.yaml_loader import EMU_PER_PT, load_process_yaml, compute_layout


SAMPLE_YAML = """
actors:
  - A
  - B
nodes:
  - id: 1
    type: task
    actor: 0
    label: Task 1
    next: [2]
  - id: 2
    type: task
    actor: 1
    label: Task 2
    next: []
"""


def test_yaml_to_pptx_creates_file(tmp_path: Path) -> None:
    yaml_path = tmp_path / "in.yaml"
    yaml_path.write_text(SAMPLE_YAML, encoding="utf-8")
    out = tmp_path / "out.pptx"
    n = yaml2pptx.yaml_to_pptx(yaml_path, out)
    assert out.exists()
    assert out.stat().st_size > 0
    assert n > 0


def test_yaml_to_pptx_returns_shape_count(tmp_path: Path) -> None:
    yaml_path = tmp_path / "in.yaml"
    yaml_path.write_text(SAMPLE_YAML, encoding="utf-8")
    out = tmp_path / "out.pptx"
    n = yaml2pptx.yaml_to_pptx(yaml_path, out)
    # アクターラベル2 + レーン線1 + タスク2 + 矢印1 以上
    assert n >= 6


def test_yaml_to_pptx_empty_yaml(tmp_path: Path) -> None:
    yaml_path = tmp_path / "empty.yaml"
    yaml_path.write_text("actors: []\nnodes: []\n", encoding="utf-8")
    out = tmp_path / "out.pptx"
    n = yaml2pptx.yaml_to_pptx(yaml_path, out)
    assert out.exists()
    assert n == 0


SAMPLE_YAML_START_END = """
actors:
  - A
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
"""


def test_start_end_drawn_as_oval(tmp_path: Path) -> None:
    """スタート・終了ノードは PPTX 上で正円（OVAL）として描画される（DoD）。"""
    yaml_path = tmp_path / "in.yaml"
    yaml_path.write_text(SAMPLE_YAML_START_END.strip(), encoding="utf-8")
    out = tmp_path / "out.pptx"
    n = yaml2pptx.yaml_to_pptx(yaml_path, out)
    assert out.exists()
    assert n > 0
    prs = Presentation(str(out))
    assert len(prs.slides) >= 1
    slide = prs.slides[0]
    ovals = []
    for s in slide.shapes:
        try:
            if hasattr(s, "auto_shape_type") and s.auto_shape_type == MSO_SHAPE.OVAL:
                ovals.append(s)
        except (ValueError, AttributeError):
            pass  # コネクタ・テキストボックス等は auto shape ではない
    assert len(ovals) >= 2, "start と end の少なくとも2つが正円（OVAL）で描画されていること"


SAMPLE_YAML_GATEWAY_SYMBOLS = """
actors:
  - A
nodes:
  - id: 1
    type: gateway
    actor: 0
    label: 条件
    gateway_type: exclusive
    next: [2, 3]
  - id: 2
    type: gateway
    actor: 0
    label: 並行
    gateway_type: parallel
    next: [4]
  - id: 3
    type: task
    actor: 0
    label: T3
    next: [4]
  - id: 4
    type: task
    actor: 0
    label: T4
    next: []
"""


def test_gateway_drawn_with_x_or_plus(tmp_path: Path) -> None:
    """条件分岐は菱形に✕、並行分岐は菱形に＋で描画される（DoD）。"""
    yaml_path = tmp_path / "in.yaml"
    yaml_path.write_text(SAMPLE_YAML_GATEWAY_SYMBOLS.strip(), encoding="utf-8")
    out = tmp_path / "out.pptx"
    yaml2pptx.yaml_to_pptx(yaml_path, out)
    prs = Presentation(str(out))
    slide = prs.slides[0]
    diamond_texts = []
    for s in slide.shapes:
        try:
            if hasattr(s, "auto_shape_type") and s.auto_shape_type == MSO_SHAPE.DIAMOND:
                diamond_texts.append(s.text_frame.paragraphs[0].text if s.text_frame.paragraphs else "")
        except (ValueError, AttributeError):
            pass
    assert "✕" in diamond_texts, "条件分岐（exclusive）は菱形に✕"
    assert "＋" in diamond_texts, "並行分岐（parallel）は菱形に＋"


SAMPLE_YAML_BRANCH_LABELS = """
actors:
  - A
nodes:
  - id: 1
    type: gateway
    actor: 0
    label: 成約?
    next:
      - id: 2
        label: "Yes"
      - id: 3
        label: "No"
  - id: 2
    type: task
    actor: 0
    label: 契約
    next: []
  - id: 3
    type: task
    actor: 0
    label: 見送り
    next: []
"""


def test_branch_arrow_labels_drawn(tmp_path: Path) -> None:
    """分岐矢印にラベル（Yes/No 等）が表示される（DoD）。"""
    yaml_path = tmp_path / "in.yaml"
    yaml_path.write_text(SAMPLE_YAML_BRANCH_LABELS.strip(), encoding="utf-8")
    out = tmp_path / "out.pptx"
    n = yaml2pptx.yaml_to_pptx(yaml_path, out)
    assert out.exists()
    assert n > 0
    prs = Presentation(str(out))
    slide = prs.slides[0]
    all_text = " ".join(
        s.text_frame.paragraphs[0].text
        for s in slide.shapes
        if hasattr(s, "text_frame") and s.text_frame.paragraphs
    )
    assert "Yes" in all_text, "分岐矢印ラベル Yes がスライドに含まれる"
    assert "No" in all_text, "分岐矢印ラベル No がスライドに含まれる"


def test_actor_labels_vertically_centered_in_lane(tmp_path: Path) -> None:
    """アクター名がスイムレーンの上下中央に配置されている（DoD: アクター名の位置）。"""
    yaml_path = tmp_path / "in.yaml"
    yaml_path.write_text(SAMPLE_YAML.strip(), encoding="utf-8")
    out = tmp_path / "out.pptx"
    yaml2pptx.yaml_to_pptx(yaml_path, out)
    actors, nodes = load_process_yaml(yaml_path)
    layout = compute_layout(actors, nodes)
    prs = Presentation(str(out))
    slide = prs.slides[0]
    # アクター名のテキストボックスを名前で収集（左側のテキスト＝アクターラベル）
    actor_texts = ["A", "B"]
    for i, name in enumerate(actor_texts):
        lane_center_y = (
            layout.content_top_offset + i * layout.lane_height + layout.lane_height // 2
        )
        found = False
        for s in slide.shapes:
            if not hasattr(s, "text_frame") or not s.text_frame.paragraphs:
                continue
            if s.text_frame.paragraphs[0].text.strip() != name:
                continue
            # このシェイプの縦中央がレーン中央に近いこと（許容 10%）
            shape_center_y = int(s.top) + int(s.height) // 2
            tolerance = layout.lane_height // 5
            assert abs(shape_center_y - lane_center_y) <= tolerance, (
                f"アクター {name} のラベルがレーン上下中央にない: "
                f"shape_center={shape_center_y} lane_center={lane_center_y}"
            )
            found = True
            break
        assert found, f"アクター名 {name} のテキストボックスが見つからない"


def test_actor_labels_in_box_2pt_from_dotted_line(tmp_path: Path) -> None:
    """アクター名が点線から2pt離した長方形内にあり、等間隔（DoD: アクター名の四角）。"""
    yaml_path = tmp_path / "in.yaml"
    yaml_path.write_text(SAMPLE_YAML.strip(), encoding="utf-8")
    out = tmp_path / "out.pptx"
    yaml2pptx.yaml_to_pptx(yaml_path, out)
    actors, nodes = load_process_yaml(yaml_path)
    layout = compute_layout(actors, nodes)
    gap_emu = 2 * EMU_PER_PT  # 2pt
    prs = Presentation(str(out))
    slide = prs.slides[0]
    for i, name in enumerate(["A", "B"]):
        lane_top = layout.content_top_offset + i * layout.lane_height
        expected_top = lane_top + gap_emu
        expected_height = layout.lane_height - 2 * gap_emu
        found = False
        for s in slide.shapes:
            if not hasattr(s, "text_frame") or not s.text_frame.paragraphs:
                continue
            if s.text_frame.paragraphs[0].text.strip() != name:
                continue
            # 四角の上端は点線から 2pt 下
            assert int(s.top) >= expected_top - 5000 and int(s.top) <= expected_top + 5000, (
                f"アクター {name}: ボックス上端が点線+2ptでない (got {s.top})"
            )
            assert int(s.height) >= expected_height - 5000 and int(s.height) <= expected_height + 5000, (
                f"アクター {name}: ボックス高さが lane_height-4pt でない (got {s.height})"
            )
            found = True
            break
        assert found, f"アクター名 {name} のシェイプが見つからない"
