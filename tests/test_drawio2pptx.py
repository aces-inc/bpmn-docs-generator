"""drawio2pptx のテスト。"""

from pathlib import Path

from drawio_to_pptx import drawio2pptx


SAMPLE_XML = """<mxfile host="drawio"><diagram id="page1"><mxGraphModel dx="1422" dy="794" grid="1" gridSize="10"><root>
  <mxCell id="0"/>
  <mxCell id="1" parent="0"/>
  <mxCell id="2" parent="0" value="Box A" vertex="1"><mxGeometry x="100" y="80" width="120" height="40" as="geometry"/></mxCell>
  <mxCell id="3" parent="0" value="Box B" vertex="1"><mxGeometry x="100" y="160" width="120" height="40" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>"""


def test_parse_cells() -> None:
    cells = drawio2pptx.parse_cells(SAMPLE_XML)
    vertex_cells = [c for c in cells if c.vertex and c.geometry]
    assert len(vertex_cells) >= 2
    values = [c.value for c in vertex_cells]
    assert "Box A" in values
    assert "Box B" in values


def test_drawio_to_pptx(tmp_path: Path) -> None:
    out = tmp_path / "out.pptx"
    drawio2pptx.drawio_to_pptx(SAMPLE_XML, str(out))
    assert out.exists()
    assert out.stat().st_size > 0


def test_drawio_file_to_pptx(tmp_path: Path) -> None:
    drawio_path = tmp_path / "in.drawio"
    drawio_path.write_text(SAMPLE_XML, encoding="utf-8")
    out = tmp_path / "out.pptx"
    drawio2pptx.drawio_file_to_pptx(drawio_path, out)
    assert out.exists()
    assert out.stat().st_size > 0
