"""xml2drawio のテスト。"""

from pathlib import Path

from drawio_to_pptx import xml2drawio


def test_mxgraph_model_wrapped_to_mxfile() -> None:
    xml = """<mxGraphModel dx="100" dy="100"><root>
  <mxCell id="0"/>
  <mxCell id="1" parent="0"/>
  <mxCell id="2" parent="0" value="Hello" vertex="1"><mxGeometry x="10" y="20" width="80" height="30" as="geometry"/></mxCell>
</root></mxGraphModel>"""
    out = xml2drawio.xml_to_drawio(xml)
    assert out.strip().startswith("<mxfile")
    assert "<mxGraphModel" in out
    assert "<root>" in out
    assert "Hello" in out
    assert "id=\"2\"" in out


def test_fragment_with_root_wrapped() -> None:
    xml = """<root>
  <mxCell id="0"/>
  <mxCell id="1" parent="0" value="Box" vertex="1"><mxGeometry x="0" y="0" width="100" height="40" as="geometry"/></mxCell>
</root>"""
    out = xml2drawio.xml_to_drawio(xml)
    assert out.strip().startswith("<mxfile")
    assert "Box" in out


def test_save_drawio(tmp_path: Path) -> None:
    xml = """<mxGraphModel><root><mxCell id="0"/></root></mxGraphModel>"""
    p = tmp_path / "out.drawio"
    xml2drawio.save_drawio(xml, str(p))
    assert p.read_text().strip().startswith("<mxfile")
