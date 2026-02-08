"""yaml2pptx のテスト。"""

from pathlib import Path

from process_to_pptx import yaml2pptx


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
