"""YAML ローダーとレイアウト計算のテスト。"""

from pathlib import Path

from process_to_pptx.yaml_loader import (
    ProcessNode,
    load_process_yaml,
    compute_layout,
    find_isolated_flow_nodes,
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


def test_find_isolated_flow_nodes_none(tmp_path: Path) -> None:
    """接続されたフローの場合は孤立ノードなし。"""
    p = tmp_path / "process.yaml"
    p.write_text(SAMPLE_YAML, encoding="utf-8")
    _, nodes = load_process_yaml(p)
    assert find_isolated_flow_nodes(nodes) == []


def test_find_isolated_flow_nodes_isolated(tmp_path: Path) -> None:
    """task/gateway で入出次数が 0 のノードは孤立として検出される（DoD: 人のタスクの接続）。"""
    yaml_text = """
actors: [A]
nodes:
  - id: 1
    type: task
    actor: 0
    label: つながっている
    next: [2]
  - id: 2
    type: task
    actor: 0
    label: 終端
    next: []
  - id: 3
    type: task
    actor: 0
    label: 孤立タスク
    next: []
"""
    p = tmp_path / "p.yaml"
    p.write_text(yaml_text.strip(), encoding="utf-8")
    _, nodes = load_process_yaml(p)
    isolated = find_isolated_flow_nodes(nodes)
    assert isolated == [3]


def test_find_isolated_flow_nodes_start_end_ignored(tmp_path: Path) -> None:
    """start/end はフローノード対象外なので孤立リストに含めない。"""
    yaml_text = """
actors: [A]
nodes:
  - id: 1
    type: start
    actor: 0
    label: 開始
    next: []
  - id: 2
    type: end
    actor: 0
    label: 終了
    next: []
"""
    p = tmp_path / "p.yaml"
    p.write_text(yaml_text.strip(), encoding="utf-8")
    _, nodes = load_process_yaml(p)
    isolated = find_isolated_flow_nodes(nodes)
    assert isolated == []


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


def test_load_next_with_labels(tmp_path: Path) -> None:
    """next を [{ id, label }, ...] 形式で読み込むと next_ids と next_labels が設定される。"""
    yaml_text = """
actors: [A]
nodes:
  - id: 1
    type: gateway
    actor: 0
    label: 分岐?
    next:
      - id: 2
        label: "Yes"
      - id: 3
        label: "No"
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
    gw = nodes[0]
    assert gw.next_ids == [2, 3]
    assert gw.next_labels == {2: "Yes", 3: "No"}
    # 従来のスカラー形式もそのまま
    assert nodes[1].next_ids == []
    assert nodes[1].next_labels == {}


def test_compute_layout_edge_labels(tmp_path: Path) -> None:
    """分岐の next_labels から layout.edge_labels が埋まる。"""
    yaml_text = """
actors: [A]
nodes:
  - id: 1
    type: gateway
    actor: 0
    label: "?"
    next: [{ id: 2, label: "Yes" }, { id: 3, label: "No" }]
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
    actors, nodes = load_process_yaml(p)
    layout = compute_layout(actors, nodes)
    assert layout.edge_labels.get((1, 2)) == "Yes"
    assert layout.edge_labels.get((1, 3)) == "No"


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


def test_load_accepts_artifact_type(tmp_path: Path) -> None:
    """type: artifact（成果物）を読み込める。"""
    yaml_text = """
actors: [A]
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
    next: []
"""
    p = tmp_path / "p.yaml"
    p.write_text(yaml_text.strip(), encoding="utf-8")
    _, nodes = load_process_yaml(p)
    assert nodes[1].type == "artifact"
    assert nodes[1].label == "見積書"


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


def test_loop_start_at_column_zero_and_edge_present(tmp_path: Path) -> None:
    """ループ: next で開始ノードを参照した場合、開始は常に列0に配置され、ループ矢印用のエッジが含まれる。"""
    yaml_with_loop = """
actors:
  - A
  - B
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
    next: [0]
"""
    p = tmp_path / "process.yaml"
    p.write_text(yaml_with_loop.strip(), encoding="utf-8")
    actors, nodes = load_process_yaml(p)
    layout = compute_layout(actors, nodes)
    start_node = next(n for n in nodes if n.type == "start" and n.id == 0)
    assert start_node.column == 0, "開始ノードはループ時も列0に配置される"
    assert (2, 0) in layout.edges, "タスク2→開始のループ用エッジが含まれる"


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
