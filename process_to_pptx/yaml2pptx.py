"""YAML 業務プロセス定義から編集可能な PPTX を生成する。"""

from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_CONNECTOR_TYPE, MSO_SHAPE
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.oxml import parse_xml

from .yaml_loader import (
    ProcessLayout,
    load_process_yaml,
    compute_layout,
)


def _add_arrow_to_connector(connector) -> None:
    """コネクタの終端（接続先側）に矢印を付ける。OOXML では tailEnd が線の終点（end）、headEnd が始点。"""
    line_elem = connector.line._get_or_add_ln()
    line_elem.append(
        parse_xml(
            '<a:tailEnd xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" type="triangle" w="med" len="med"/>'
        )
    )


def _draw_actor_labels(slide, layout: ProcessLayout) -> None:
    """スライド左側にアクター名を描画。描画開始は content_top_offset から。"""
    for i, name in enumerate(layout.actors):
        top = layout.content_top_offset + i * layout.lane_height + (
            layout.lane_height - layout.task_side
        ) // 2
        # テキストボックス: 左端に配置、幅は left_label_width より少し小さく
        w = layout.left_label_width - Emu(36000)  # 約 1mm マージン
        left = Emu(18000)
        tb = slide.shapes.add_textbox(left, Emu(top), w, Emu(layout.task_side))
        tf = tb.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = name
        p.font.size = Pt(10)
        p.font.bold = True


def _draw_lane_separators(slide, layout: ProcessLayout) -> None:
    """レーン間をグレーの点線で区切る。点線はレーンの左端（アクター名がある左端）まで届く（DoD）。"""
    gray = RGBColor(0x80, 0x80, 0x80)
    x1 = 0  # レーン左端まで届かせる
    x2 = int(layout.slide_width - layout.right_margin)
    for i in range(1, len(layout.actors)):
        y = layout.content_top_offset + i * layout.lane_height
        line = slide.shapes.add_connector(
            MSO_CONNECTOR_TYPE.STRAIGHT, x1, y, x2, y
        )
        line.line.color.rgb = gray
        line.line.width = Pt(0.5)
        # 点線: dashType を設定（a:prstDash）
        ln = line.line._get_or_add_ln()
        dash = parse_xml(
            '<a:prstDash xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" val="dot"/>'
        )
        ln.append(dash)


# 四角形の接続点: 0=上, 1=左, 2=下, 3=右（各辺の中央＝上下中央）
CONNECTION_SITE_RIGHT = 3
CONNECTION_SITE_LEFT = 1


def _draw_node_shape(slide, node, left: int, top: int, width: int, height: int):
    """タスクまたは分岐の図形を 1 つ描画。タスクは正方形の四角、分岐はひし形。"""
    if node.type == "gateway":
        shape_type = MSO_SHAPE.DIAMOND
    else:
        shape_type = MSO_SHAPE.ROUNDED_RECTANGLE
    shape = slide.shapes.add_shape(
        shape_type,
        Emu(left),
        Emu(top),
        Emu(width),
        Emu(height),
    )
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = False  # 明示的改行がない限り1行で表示
    tf.margin_left = 0
    tf.margin_top = 0
    tf.margin_right = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = node.label
    p.font.size = Pt(10)
    p.font.bold = False
    p.font.color.rgb = RGBColor(0, 0, 0)  # 黒文字（DoD: タスク文字の配置）
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0xE8, 0xE8, 0xE8)
    shape.line.color.rgb = RGBColor(0x37, 0x37, 0x37)
    # タスクの四角には影を付けない（DoD）
    shape.shadow.inherit = False
    return shape


def yaml_to_pptx(
    yaml_path: str | Path,
    output_path: str | Path,
) -> int:
    """
    YAML ファイルを読み、PPTX レイアウト仕様に従って編集可能な PPTX を生成する。
    戻り値はスライドに追加した図形の総数（タスク・分岐・矢印・レーン線・ラベル含む）。
    """
    actors, nodes = load_process_yaml(yaml_path)
    if not actors or not nodes:
        prs = Presentation()
        prs.slide_width = Emu(9144000)
        prs.slide_height = Emu(6858000)
        blank = prs.slide_layouts[6]
        prs.slides.add_slide(blank)
        prs.save(str(output_path))
        return 0

    layout = compute_layout(actors, nodes)
    prs = Presentation()
    prs.slide_width = Emu(layout.slide_width)
    prs.slide_height = Emu(layout.slide_height)
    blank = prs.slide_layouts[6]

    total_shapes = 0

    for slide_idx in range(layout.num_slides):
        slide = prs.slides.add_slide(blank)
        shape_by_id = {}

        # アクター名（左）
        _draw_actor_labels(slide, layout)
        total_shapes += len(layout.actors)

        # レーン区切り（グレー点線）
        _draw_lane_separators(slide, layout)
        total_shapes += max(0, len(layout.actors) - 1)

        # このスライドに属するノード
        for node in layout.nodes:
            if node.slide_index != slide_idx:
                continue
            pos = layout.node_positions.get(node.id)
            if not pos:
                continue
            left, top, w, h = pos
            shp = _draw_node_shape(slide, node, left, top, w, h)
            shape_by_id[node.id] = shp
            total_shapes += 1

        # このスライド内のエッジのみ矢印で接続（両端が同じスライド）
        for from_id, to_id in layout.edges:
            from_node = next((n for n in layout.nodes if n.id == from_id), None)
            to_node = next((n for n in layout.nodes if n.id == to_id), None)
            if not from_node or not to_node:
                continue
            if from_node.slide_index != slide_idx or to_node.slide_index != slide_idx:
                continue
            from_shp = shape_by_id.get(from_id)
            to_shp = shape_by_id.get(to_id)
            if not from_shp or not to_shp:
                continue
            # 同一レーン内は直線、異なるレーン間は折れ曲がり（直角コネクタ）
            same_lane = from_node.actor_index == to_node.actor_index
            connector_type = (
                MSO_CONNECTOR_TYPE.STRAIGHT
                if same_lane
                else MSO_CONNECTOR_TYPE.ELBOW
            )
            conn = slide.shapes.add_connector(
                connector_type, 0, 0, 0, 0
            )
            # 接続点: タスクの上下中央（右辺中央→左辺中央）
            conn.begin_connect(from_shp, CONNECTION_SITE_RIGHT)
            conn.end_connect(to_shp, CONNECTION_SITE_LEFT)
            conn.line.fill.solid()
            conn.line.fill.fore_color.rgb = RGBColor(0x37, 0x37, 0x37)
            conn.line.width = Pt(1)
            _add_arrow_to_connector(conn)
            total_shapes += 1

    prs.save(str(output_path))
    return total_shapes
