"""YAML 業務プロセス定義の読み込みとレイアウト計算。"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# 1 inch = 914400 EMU（python-pptx の標準）
EMU_PER_INCH = 914400
# 1 pt = 1/72 inch
EMU_PER_PT = EMU_PER_INCH // 72

# 最小フォント 10pt を維持するための最小タスク一辺（約 0.25 inch）
MIN_TASK_SIDE_EMU = int(0.25 * EMU_PER_INCH)
# スライド左右余白の最小（DoD: 10pt 以上）
SLIDE_MARGIN_MIN_EMU = 10 * EMU_PER_PT
# アクター枠の右端と最初のタスク列の間の余白（DoD: 10pt）
TASK_AREA_LEFT_GAP_EMU = 10 * EMU_PER_PT


@dataclass
class ProcessNode:
    """1 ノード（タスク・分岐・スタート・終了・成果物・サービス）。"""

    id: str | int
    type: str  # "task" | "gateway" | "start" | "end" | "artifact" | "service"
    actor_index: int
    label: str
    next_ids: list[str | int]
    # 分岐矢印のラベル: to_id -> 表示テキスト（next が { id, label } 形式のとき）
    next_labels: dict[str | int, str] = field(default_factory=dict)
    # gateway のときのみ: "exclusive"（条件分岐・菱形に✕）| "parallel"（並行・菱形に＋）
    gateway_type: str = "exclusive"
    # システム接続: 人タスクからサービスへのリクエスト先ノード ID のリスト
    request_to: list[str | int] = field(default_factory=list)
    # システム接続: 人タスクがレスポンスを受け取るサービスノード ID のリスト
    response_from: list[str | int] = field(default_factory=list)
    # レイアウト後に設定
    column: int = 0
    slide_index: int = 0
    col_in_slide: int = 0


@dataclass
class ProcessLayout:
    """レイアウト定数と計算結果。"""

    # 定数（EMU）
    slide_width: int = 10 * EMU_PER_INCH
    slide_height: int = int(7.5 * EMU_PER_INCH)
    # スライド左右 10pt 以上余白（DoD）
    left_margin: int = SLIDE_MARGIN_MIN_EMU
    right_margin: int = max(int(0.5 * EMU_PER_INCH), SLIDE_MARGIN_MIN_EMU)
    # 左余白を抑え、アクター名とタスク領域が一体になる幅（DoD: 左端開始位置）
    left_label_width: int = int(1.2 * EMU_PER_INCH)
    lane_height: int = int(1.2 * EMU_PER_INCH)
    task_side: int = int(0.4 * EMU_PER_INCH)
    gap: int = 0  # task_side で後から設定
    # 図の描画開始位置（スライド上端から約25%下がった位置、タイトル・キーメッセージ用領域確保）
    content_top_offset: int = 0  # compute_layout で設定
    # 図の下端からスライド下縁までの余白（compute_layout で使用）
    bottom_margin: int = 0  # compute_layout で設定

    actors: list[str] = field(default_factory=list)
    nodes: list[ProcessNode] = field(default_factory=list)
    # ノード id → 配置 (x, y) 中心または左上（図形用）
    node_positions: dict[str | int, tuple[int, int, int, int]] = field(
        default_factory=dict
    )  # id -> (left_emu, top_emu, width_emu, height_emu)
    edges: list[tuple[str | int, str | int]] = field(default_factory=list)  # (from_id, to_id)
    # 分岐矢印のラベル: (from_id, to_id) -> 表示テキスト
    edge_labels: dict[tuple[str | int, str | int], str] = field(default_factory=dict)
    # システム接続: (from_id, to_id, "request"|"response")。request=人→サービス、response=サービス→人
    system_edges: list[tuple[str | int, str | int, str]] = field(default_factory=list)
    num_slides: int = 1

    def __post_init__(self) -> None:
        if self.gap == 0:
            self.gap = self.task_side

    @property
    def content_width(self) -> int:
        # アクター枠とタスク領域の間の 10pt 余白を含める
        return self.slide_width - self.left_margin - self.left_label_width - TASK_AREA_LEFT_GAP_EMU - self.right_margin

    @property
    def max_cols_per_slide(self) -> int:
        """1 スライドに並べられる最大タスク列数。"""
        unit = self.task_side + self.gap
        return max(1, self.content_width // unit)


# タスク正方形の一辺はスイムレーン高さの約60%（DoD）
TASK_SIDE_RATIO = 0.6


def _base_sizes_for_actors(num_actors: int) -> tuple[int, int]:
    """
    アクター数に応じたレーン高さ（EMU）を返す。タスク一辺はレーン高さの約60%。
    少ないときは大きく、多いときは小さくする。最小フォント 10pt 維持のため下限あり。
    """
    if num_actors <= 2:
        lane_height = int(1.8 * EMU_PER_INCH)
    elif num_actors <= 4:
        lane_height = int(1.4 * EMU_PER_INCH)
    elif num_actors <= 6:
        lane_height = int(1.2 * EMU_PER_INCH)
    else:
        lane_height = int(1.0 * EMU_PER_INCH)
    task_side = max(int(lane_height * TASK_SIDE_RATIO), MIN_TASK_SIDE_EMU)
    return lane_height, task_side


def _resolve_actor_index(actor: Any, actors: list[str]) -> int:
    """actor（名前またはインデックス）を 0 始まりのインデックスに。"""
    if isinstance(actor, int):
        if 0 <= actor < len(actors):
            return actor
        return 0
    if isinstance(actor, str):
        try:
            return actors.index(actor)
        except ValueError:
            pass
    return 0


def _normalize_id(raw: Any) -> str | int:
    """YAML の id をそのまま返す（キーとして一貫して使う）。"""
    if isinstance(raw, (str, int)):
        return raw
    if isinstance(raw, float) and raw == int(raw):
        return int(raw)
    return str(raw)


def load_process_yaml(path: str | Path) -> tuple[list[str], list[ProcessNode], dict[str, Any]]:
    """
    YAML ファイルを読み、actors とノードリストと layout 設定を返す。
    ノードの actor はインデックスに正規化し、next は ID のリストに正規化する。
    戻り値: (actors, nodes, layout_config)。layout_config はルートの "layout" の値（なければ {}）。
    """
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not data or not isinstance(data, dict):
        return [], [], {}

    layout_config = data.get("layout") if isinstance(data.get("layout"), dict) else {}

    raw_actors = data.get("actors") or []
    actors = [str(a) for a in raw_actors] if isinstance(raw_actors, list) else []

    raw_nodes = data.get("nodes") or []
    if not isinstance(raw_nodes, list):
        return actors, [], layout_config

    nodes: list[ProcessNode] = []
    for item in raw_nodes:
        if not isinstance(item, dict):
            continue
        nid = item.get("id")
        if nid is None:
            continue
        nid = _normalize_id(nid)
        typ = (item.get("type") or "task").lower()
        if typ not in ("task", "gateway", "start", "end", "artifact", "service"):
            typ = "task"
        actor = item.get("actor", 0)
        actor_index = _resolve_actor_index(actor, actors)
        label = str(item.get("label") or "")
        next_raw = item.get("next")
        next_ids: list[str | int] = []
        next_labels: dict[str | int, str] = {}
        if isinstance(next_raw, list):
            for x in next_raw:
                if isinstance(x, dict):
                    to_id_raw = x.get("id")
                    if to_id_raw is not None:
                        to_id = _normalize_id(to_id_raw)
                        next_ids.append(to_id)
                        lb = x.get("label")
                        if lb is not None and str(lb).strip():
                            next_labels[to_id] = str(lb).strip()
                else:
                    next_ids.append(_normalize_id(x))
        elif next_raw is not None:
            next_ids = [_normalize_id(next_raw)]

        gateway_type = "exclusive"
        if typ == "gateway":
            gt = (item.get("gateway_type") or "exclusive").lower()
            gateway_type = "parallel" if gt == "parallel" else "exclusive"

        request_to: list[str | int] = []
        for rid in item.get("request_to") or []:
            request_to.append(_normalize_id(rid))
        response_from: list[str | int] = []
        for rid in item.get("response_from") or []:
            response_from.append(_normalize_id(rid))

        nodes.append(
            ProcessNode(
                id=nid,
                type=typ,
                actor_index=actor_index,
                label=label,
                next_ids=next_ids,
                next_labels=next_labels,
                gateway_type=gateway_type,
                request_to=request_to,
                response_from=response_from,
            )
        )

    return actors, nodes, layout_config


def find_isolated_flow_nodes(nodes: list[ProcessNode]) -> list[str | int]:
    """
    人に属するフローノード（task / gateway）のうち、
    入次数・出次数がともに 0 の孤立ノードの ID を返す。
    DoD: 人のタスクの接続（孤立した人のタスクが存在しないことの確認用）。
    """
    if not nodes:
        return []
    id_to_node = {n.id: n for n in nodes}
    in_degree: dict[str | int, int] = {n.id: 0 for n in nodes}
    for n in nodes:
        for to_id in n.next_ids:
            if to_id in id_to_node:
                in_degree[to_id] = in_degree.get(to_id, 0) + 1
    isolated: list[str | int] = []
    for n in nodes:
        if n.type not in ("task", "gateway", "artifact"):
            continue
        out_degree = sum(1 for to_id in n.next_ids if to_id in id_to_node)
        if in_degree[n.id] == 0 and out_degree == 0:
            isolated.append(n.id)
    return isolated


def _assign_columns(
    nodes: list[ProcessNode],
    id_to_node: dict,
    extra_edges: list[tuple[str | int, str | int]] | None = None,
) -> None:
    """
    フロー順で列番号を付与。分岐発生時は「分岐前の列＋分岐先用の1列」とし、
    分岐先のノードは同一列に配置し得るようにする（横に間延びしない）。
    入次数0から BFS で列を伝播し、複数 predecessor の場合は最大列+1 を採用。
    extra_edges はシステム接続など next 以外の辺（列計算用）。
    """
    # 入次数を計算（next の逆方向 + extra_edges）
    in_degree: dict[str | int, int] = {n.id: 0 for n in nodes}
    for node in nodes:
        for to_id in node.next_ids:
            if to_id in id_to_node:
                in_degree[to_id] = in_degree.get(to_id, 0) + 1
    for from_id, to_id in extra_edges or []:
        if to_id in id_to_node:
            in_degree[to_id] = in_degree.get(to_id, 0) + 1

    # 列は未割り当てを -1 で表す
    for node in nodes:
        node.column = -1

    # 入次数0のノードを列0にし、BFS のキューに入れる
    queue: deque[ProcessNode] = deque()
    for node in nodes:
        if in_degree[node.id] == 0:
            node.column = 0
            queue.append(node)

    # extra_edges の from -> to も列伝播に使う（to の列 = from + 1）
    out_extra: dict[str | int, list[str | int]] = defaultdict(list)
    for from_id, to_id in extra_edges or []:
        out_extra[from_id].append(to_id)

    while queue:
        n = queue.popleft()
        c = n.column
        for to_id in n.next_ids:
            next_node = id_to_node.get(to_id)
            if not next_node:
                continue
            # 分岐先も単一 next も同じ: 次の列は c+1。合流点は複数回更新で max になる
            next_node.column = max(next_node.column, c + 1)
            in_degree[next_node.id] -= 1
            if in_degree[next_node.id] == 0:
                queue.append(next_node)
        for to_id in out_extra.get(n.id, []):
            next_node = id_to_node.get(to_id)
            if not next_node:
                continue
            next_node.column = max(next_node.column, c + 1)
            in_degree[next_node.id] -= 1
            if in_degree[next_node.id] == 0:
                queue.append(next_node)

    # 未到達ノード（閉路や孤立）は既存の最大列の続きで割り当て
    max_col = max((n.column for n in nodes if n.column >= 0), default=-1)
    for node in nodes:
        if node.column < 0:
            max_col += 1
            node.column = max_col

    # ループ対応: スタートノードは常に列0に配置し、戻り矢印が左向きに描画されるようにする
    for node in nodes:
        if node.type == "start":
            node.column = 0


def _parse_margins_emu(margins: dict[str, Any] | None) -> dict[str, int]:
    """
    YAML の layout.margins（pt 指定）を EMU に変換する。
    未指定のキーは変更しない（compute_layout の既定値を使用）。
    left_pt / right_pt は最小 SLIDE_MARGIN_MIN_EMU（10pt）を維持。
    戻り値: left_margin, right_margin, content_top_offset, bottom_margin の EMU。
    """
    if not margins or not isinstance(margins, dict):
        return {}
    out: dict[str, int] = {}
    if "left_pt" in margins and margins["left_pt"] is not None:
        pt = int(margins["left_pt"])
        out["left_margin"] = max(pt * EMU_PER_PT, SLIDE_MARGIN_MIN_EMU)
    if "right_pt" in margins and margins["right_pt"] is not None:
        pt = int(margins["right_pt"])
        out["right_margin"] = max(pt * EMU_PER_PT, SLIDE_MARGIN_MIN_EMU)
    if "top_pt" in margins and margins["top_pt"] is not None:
        out["content_top_offset"] = max(0, int(margins["top_pt"]) * EMU_PER_PT)
    if "bottom_pt" in margins and margins["bottom_pt"] is not None:
        out["bottom_margin"] = max(0, int(margins["bottom_pt"]) * EMU_PER_PT)
    return out


def compute_layout(
    actors: list[str],
    nodes: list[ProcessNode],
    max_cols_per_slide: int | None = None,
    margins: dict[str, Any] | None = None,
) -> ProcessLayout:
    """
    アクター名・ノードリストからレイアウトを計算する。
    アクター数に応じてレーン高さ・タスクサイズを調整し、
    図がスライドの描画領域からはみ出さないようスケールする。
    ノードは列に割り当て、max_cols を超えたら次スライド。
    margins: YAML の layout.margins（left_pt, right_pt, top_pt, bottom_pt 等）。未指定時は現行どおり。
    """
    layout = ProcessLayout(actors=actors, nodes=nodes)
    layout.content_top_offset = int(layout.slide_height * 0.25)
    layout.bottom_margin = int(0.05 * layout.slide_height)

    # YAML の layout.margins で上書き
    margins_emu = _parse_margins_emu(margins)
    if "left_margin" in margins_emu:
        layout.left_margin = margins_emu["left_margin"]
    if "right_margin" in margins_emu:
        layout.right_margin = margins_emu["right_margin"]
    if "content_top_offset" in margins_emu:
        layout.content_top_offset = margins_emu["content_top_offset"]
    if "bottom_margin" in margins_emu:
        layout.bottom_margin = margins_emu["bottom_margin"]

    # アクター数に応じたベースサイズ（少ない＝大きく、多い＝小さく）
    num_actors = len(actors) or 1
    layout.lane_height, layout.task_side = _base_sizes_for_actors(num_actors)
    layout.gap = layout.task_side

    id_to_node = {n.id: n for n in nodes}
    # システム接続を列計算に含める（サービスノードに列を付与）
    extra_edges: list[tuple[str | int, str | int]] = []
    for n in nodes:
        for to_id in n.request_to:
            if to_id in id_to_node:
                extra_edges.append((n.id, to_id))
        for from_id in n.response_from:
            if from_id in id_to_node:
                extra_edges.append((from_id, n.id))
    _assign_columns(nodes, id_to_node, extra_edges)

    # 仮の max_cols_per_slide でスライド・列を割り当て
    unit = layout.task_side + layout.gap
    if max_cols_per_slide is not None:
        tentative_max_cols = max(1, max_cols_per_slide)
    else:
        tentative_max_cols = max(1, layout.content_width // unit)
    for node in nodes:
        node.slide_index = node.column // tentative_max_cols
        node.col_in_slide = node.column % tentative_max_cols

    # スライドに必ず収まるようスケールを算出
    required_height = num_actors * layout.lane_height
    available_height = layout.slide_height - layout.content_top_offset - layout.bottom_margin
    required_width_per_slide = tentative_max_cols * unit
    available_width = layout.content_width

    scale_h = available_height / required_height if required_height else 1.0
    scale_w = available_width / required_width_per_slide if required_width_per_slide else 1.0
    scale = min(scale_h, scale_w, 1.0)

    # 最小フォント 10pt 維持のため task_side の下限を守る
    if layout.task_side * scale < MIN_TASK_SIDE_EMU:
        scale = MIN_TASK_SIDE_EMU / layout.task_side

    layout.lane_height = int(layout.lane_height * scale)
    # タスク正方形の一辺はレーン高さの約60%（DoD）
    layout.task_side = max(int(layout.lane_height * TASK_SIDE_RATIO), MIN_TASK_SIDE_EMU)
    layout.gap = layout.task_side

    # スケール後の列幅で最大列数を再計算し、スライド・列を再割り当て
    unit = layout.task_side + layout.gap
    final_max_cols = max(1, layout.content_width // unit)
    for node in nodes:
        node.slide_index = node.column // final_max_cols
        node.col_in_slide = node.column % final_max_cols

    layout.num_slides = max((n.slide_index for n in nodes), default=0) + 1

    # エッジ収集（next から）と分岐矢印ラベル
    for node in nodes:
        for to_id in node.next_ids:
            if to_id in id_to_node:
                layout.edges.append((node.id, to_id))
                lbl = node.next_labels.get(to_id)
                if lbl:
                    layout.edge_labels[(node.id, to_id)] = lbl
    # システム接続エッジ（request / response）
    for n in nodes:
        for to_id in n.request_to:
            if to_id in id_to_node:
                layout.system_edges.append((n.id, to_id, "request"))
        for from_id in n.response_from:
            if from_id in id_to_node:
                layout.system_edges.append((from_id, n.id, "response"))

    # 各ノードの (left, top, width, height) を EMU で計算（スライド内の座標）
    # アクター枠と最初のタスクの間に 10pt 余白（DoD）
    for node in nodes:
        lane = node.actor_index
        col = node.col_in_slide

        left = layout.left_margin + layout.left_label_width + TASK_AREA_LEFT_GAP_EMU + col * (layout.task_side + layout.gap)
        top = layout.content_top_offset + lane * layout.lane_height + (
            layout.lane_height - layout.task_side
        ) // 2
        layout.node_positions[node.id] = (
            left,
            top,
            layout.task_side,
            layout.task_side,
        )

    # 同一アクター・同一列に複数ノードがある場合、レーン高さの90%を縦分割して配置（DoD）
    key_to_nodes: dict[tuple[int, int, int], list[ProcessNode]] = defaultdict(list)
    for node in nodes:
        key_to_nodes[(node.slide_index, node.actor_index, node.col_in_slide)].append(node)

    for key, group in key_to_nodes.items():
        if len(group) <= 1:
            continue
        _slide_idx, lane, col = key
        lane_top = layout.content_top_offset + lane * layout.lane_height
        zone_height = int(layout.lane_height * 0.9)
        zone_top = lane_top + (layout.lane_height - zone_height) // 2
        n = len(group)
        row_height = zone_height // n
        remainder = zone_height % n
        left = layout.left_margin + layout.left_label_width + TASK_AREA_LEFT_GAP_EMU + col * (layout.task_side + layout.gap)
        # 列幅は1タスク時と同じ（task_side）。高さのみ分割。
        width = layout.task_side
        offset = 0
        for i, node in enumerate(group):
            h = row_height + (1 if i < remainder else 0)
            top = zone_top + offset
            offset += h
            layout.node_positions[node.id] = (left, top, width, h)

    return layout
