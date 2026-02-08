"""YAML ローダーとレイアウト計算のテスト。"""

from pathlib import Path

from process_to_pptx.yaml_loader import load_process_yaml, compute_layout


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
