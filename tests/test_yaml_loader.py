"""YAML ローダーとレイアウト計算のテスト。"""

from pathlib import Path

from process_to_pptx.yaml_loader import (
    ProcessNode,
    load_process_yaml,
    compute_layout,
    SLIDE_MARGIN_MIN_EMU,
)


SAMPLE_YAML = """
actors:
  - お客様
  - IT営業
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
    next: [3]
  - id: 3
    type: task
    actor: 1
    label: 契約手続き
    next: []
"""


def test_load_process_yaml(tmp_path: Path) -> None:
    p = tmp_path / "process.yaml"
    p.write_text(SAMPLE_YAML, encoding="utf-8")
    actors, nodes = load_process_yaml(p)
    assert actors == ["お客様", "IT営業"]
    assert len(nodes) == 3
    assert nodes[0].id == 1
    assert nodes[0].type == "task"
    assert nodes[0].actor_index == 0
    assert nodes[0].label == "要件検討"
    assert nodes[0].next_ids == [2]
    assert nodes[1].type == "gateway"
    assert nodes[2].actor_index == 1


def test_load_gateway_type(tmp_path: Path) -> None:
    """gateway で gateway_type: exclusive / parallel を読み込める。"""
    yaml_text = """
actors: [A]
nodes:
  - id: 1
    type: gateway
    actor: 0
    label: 分岐
    gateway_type: parallel
    next: [2, 3]
  - id: 2
    type: task
    actor: 0
    label: T2
    next: []
  - id: 3
    type: task
    actor: 0
    label: T3
    next: []
"""
    p = tmp_path / "p.yaml"
    p.write_text(yaml_text.strip(), encoding="utf-8")
    _, nodes = load_process_yaml(p)
    assert nodes[0].type == "gateway"
    assert nodes[0].gateway_type == "parallel"
    # 省略時は exclusive
    yaml2 = yaml_text.replace("gateway_type: parallel", "")
    p.write_text(yaml2.strip(), encoding="utf-8")
    _, nodes2 = load_process_yaml(p)
    assert nodes2[0].gateway_type == "exclusive"


def test_load_accepts_start_end_types(tmp_path: Path) -> None:
    """type: start / type: end を読み込める。"""
    yaml_text = """
actors: [X]
nodes:
  - id: 0
    type: start
    actor: 0
    label: 開始
    next: [1]
  - id: 1
    type: task
    actor: 0
    label: 作業
    next: [2]
  - id: 2
    type: end
    actor: 0
    label: 終了
    next: []
"""
    p = tmp_path / "p.yaml"
    p.write_text(yaml_text.strip(), encoding="utf-8")
    actors, nodes = load_process_yaml(p)
    assert len(nodes) == 3
    assert nodes[0].type == "start"
    assert nodes[1].type == "task"
    assert nodes[2].type == "end"


def test_compute_layout(tmp_path: Path) -> None:
    p = tmp_path / "process.yaml"
    p.write_text(SAMPLE_YAML, encoding="utf-8")
    actors, nodes = load_process_yaml(p)
    layout = compute_layout(actors, nodes)
    assert layout.num_slides >= 1
    assert len(layout.node_positions) == 3
    assert len(layout.edges) == 2
    for nid, (left, top, w, h) in layout.node_positions.items():
        assert w == layout.task_side
        assert h == layout.task_side


def test_slide_margin_10pt(tmp_path: Path) -> None:
    """スライド左右に 10pt 以上余白がとられる（DoD）。"""
    p = tmp_path / "process.yaml"
    p.write_text(SAMPLE_YAML, encoding="utf-8")
    actors, nodes = load_process_yaml(p)
    layout = compute_layout(actors, nodes)
    assert layout.left_margin >= SLIDE_MARGIN_MIN_EMU
    assert layout.right_margin >= SLIDE_MARGIN_MIN_EMU
    for nid, (left, top, w, h) in layout.node_positions.items():
        assert left >= layout.left_margin
        assert left + w <= layout.slide_width - layout.right_margin


def test_actor_count_scaling() -> None:
    """アクター数が少ないときはレーン・タスクが大きく、多いときは小さくなる。"""
    two_actors = ["A", "B"]
    seven_actors = ["A", "B", "C", "D", "E", "F", "G"]
    nodes_2 = [
        ProcessNode(id=1, type="task", actor_index=0, label="T1", next_ids=[2]),
        ProcessNode(id=2, type="task", actor_index=1, label="T2", next_ids=[]),
    ]
    nodes_7 = [
        ProcessNode(id=i, type="task", actor_index=(i - 1) % 7, label=f"T{i}", next_ids=[i + 1] if i < 7 else [])
        for i in range(1, 8)
    ]
    layout_few = compute_layout(two_actors, nodes_2)
    layout_many = compute_layout(seven_actors, nodes_7)
    assert layout_few.lane_height > layout_many.lane_height
    assert layout_few.task_side > layout_many.task_side


def test_layout_fits_in_slide(tmp_path: Path) -> None:
    """生成レイアウトの図がスライドの描画領域からはみ出さない。"""
    p = tmp_path / "process.yaml"
    p.write_text(SAMPLE_YAML, encoding="utf-8")
    actors, nodes = load_process_yaml(p)
    layout = compute_layout(actors, nodes)
    # 縦: 描画領域下端
    content_bottom = layout.content_top_offset + len(actors) * layout.lane_height
    assert content_bottom <= layout.slide_height, "レーンがスライド下端からはみ出す"
    # 各ノードがスライド内
    for nid, (left, top, w, h) in layout.node_positions.items():
        assert left >= 0 and top >= 0, f"ノード {nid} が左上にはみ出す"
        assert left + w <= layout.slide_width, f"ノード {nid} が右にはみ出す"
        assert top + h <= layout.slide_height, f"ノード {nid} が下にはみ出す"
