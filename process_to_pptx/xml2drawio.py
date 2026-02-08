"""mxGraph 互換 XML を .drawio ファイル形式に変換する。"""


def _ensure_mxfile_wrapper(xml_content: str) -> str:
    """入力が mxGraphModel または root 断片の場合、mxfile/diagram でラップする。"""
    xml_content = xml_content.strip()
    if xml_content.startswith("<mxfile"):
        return xml_content
    if xml_content.startswith("<mxGraphModel"):
        return f'<mxfile host="drawio"><diagram id="page1"><mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0"><root>{_extract_root_content(xml_content)}</root></mxGraphModel></diagram></mxfile>'
    # 断片（root のみ or mxCell の並び）を想定
    if "<root>" in xml_content and "</root>" in xml_content:
        inner = _extract_between(xml_content, "<root>", "</root>")
    else:
        inner = xml_content
    return f'<mxfile host="drawio"><diagram id="page1"><mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0"><root>{inner}</root></mxGraphModel></diagram></mxfile>'


def _extract_root_content(mx_graph_model_xml: str) -> str:
    """<mxGraphModel>...</mxGraphModel> 内の <root>...</root> の中身を返す。"""
    if "<root>" in mx_graph_model_xml and "</root>" in mx_graph_model_xml:
        return _extract_between(mx_graph_model_xml, "<root>", "</root>")
    return ""


def _extract_between(s: str, start: str, end: str) -> str:
    """start の直後から end の直前までを返す。"""
    i = s.find(start)
    if i == -1:
        return ""
    i += len(start)
    j = s.find(end, i)
    if j == -1:
        return s[i:]
    return s[i:j]


def xml_to_drawio(xml_content: str) -> str:
    """
    mxGraph 互換 XML を、.drawio として保存・開ける形式に変換する。
    入力は mxGraphModel 全体、または <root> 内の mxCell 断片を想定。
    """
    return _ensure_mxfile_wrapper(xml_content)


def save_drawio(xml_content: str, path: str) -> None:
    """xml_content を .drawio 形式に変換して path に保存する。"""
    drawio_xml = xml_to_drawio(xml_content)
    with open(path, "w", encoding="utf-8") as f:
        f.write(drawio_xml)
