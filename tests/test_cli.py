"""CLI のテスト。"""

import subprocess
import sys
from pathlib import Path


SAMPLE_XML = """<mxGraphModel><root>
  <mxCell id="0"/>
  <mxCell id="1" parent="0"/>
  <mxCell id="2" parent="0" value="CLI Test" vertex="1"><mxGeometry x="50" y="50" width="100" height="30" as="geometry"/></mxCell>
</root></mxGraphModel>"""


def _run(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "process_to_pptx"] + list(args)
    return subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )


def test_cli_to_drawio(tmp_path: Path) -> None:
    inp = tmp_path / "in.xml"
    inp.write_text(SAMPLE_XML, encoding="utf-8")
    out = tmp_path / "out.drawio"
    r = _run("to-drawio", str(inp), "-o", str(out))
    assert r.returncode == 0
    assert out.exists()
    assert out.read_text().strip().startswith("<mxfile")


def test_cli_to_pptx(tmp_path: Path) -> None:
    inp = tmp_path / "in.drawio"
    inp.write_text(
        """<mxfile host="drawio"><diagram><mxGraphModel><root>
  <mxCell id="0"/>
  <mxCell id="1" parent="0"/>
  <mxCell id="2" parent="0" value="X" vertex="1"><mxGeometry x="0" y="0" width="80" height="30" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>""",
        encoding="utf-8",
    )
    out = tmp_path / "out.pptx"
    r = _run("to-pptx", str(inp), "-o", str(out))
    assert r.returncode == 0
    assert out.exists()
    assert out.stat().st_size > 0


def test_cli_pipeline(tmp_path: Path) -> None:
    inp = tmp_path / "in.xml"
    inp.write_text(SAMPLE_XML, encoding="utf-8")
    out = tmp_path / "out.pptx"
    r = _run("pipeline", str(inp), "-o", str(out))
    assert r.returncode == 0
    assert out.exists()
    assert out.stat().st_size > 0


SAMPLE_YAML = """
actors:
  - A
  - B
nodes:
  - id: 1
    type: task
    actor: 0
    label: T1
    next: [2]
  - id: 2
    type: task
    actor: 1
    label: T2
    next: []
"""


def test_cli_from_yaml(tmp_path: Path) -> None:
    inp = tmp_path / "in.yaml"
    inp.write_text(SAMPLE_YAML, encoding="utf-8")
    out = tmp_path / "out.pptx"
    r = _run("from-yaml", str(inp), "-o", str(out))
    assert r.returncode == 0
    assert out.exists()
    assert out.stat().st_size > 0
    assert "Shapes:" in r.stderr
