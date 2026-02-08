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


@dataclass
class ProcessNode:
    """1 ノード（タスク・分岐・スタート・終了）。"""

    id: str | int
    type: str  # "task" | "gateway" | "start" | "end"
    actor_index: int
    label: str
    next_ids: list[str | int]
    # 分岐矢印のラベル: to_id -> 表示テキスト（next が { id, label } 形式のとき）
    next_labels: dict[str | int, str] = field(default_factory=dict)
    # gateway のときのみ: "exclusive"（条件分岐・菱形に✕）| "parallel"（並行・菱形に＋）
    gateway_type: str = "exclusive"
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

    actors: list[str] = field(default_factory=list)
    nodes: list[ProcessNode] = field(default_factory=list)
    # ノード id → 配置 (x, y) 中心または左上（図形用）
    node_positions: dict[str | int, tuple[int, int, int, int]] = field(
        default_factory=dict
    )  # id -> (left_emu, top_emu, width_emu, height_emu)
    edges: list[tuple[str | int, str | int]] = field(default_factory=list)  # (from_id, to_id)
    # 分岐矢印のラベル: (from_id, to_id) -> 表示テキスト
    edge_labels: dict[tuple[str | int, str | int], str] = field(default_factory=dict)
    num_slides: int = 1

    def __post_init__(self) -> None:
        if self.gap == 0:
            self.gap = self.task_side

    @property
    def content_width(self) -> int:
        return self.slide_width - self.left_margin - self.left_label_width - self.right_margin

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


def load_process_yaml(path: str | Path) -> tuple[list[str], list[ProcessNode]]:
    """
    YAML ファイルを読み、actors とノードリストを返す。
    ノードの actor はインデックスに正規化し、next は ID のリストに正規化する。
    """
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not data or not isinstance(data, dict):
        return [], []

    raw_actors = data.get("actors") or []
    actors = [str(a) for a in raw_actors] if isinstance(raw_actors, list) else []

    raw_nodes = data.get("nodes") or []
    if not isinstance(raw_nodes, list):
        return actors, []

    nodes: list[ProcessNode] = []
    for item in raw_nodes:
        if not isinstance(item, dict):
            continue
        nid = item.get("id")
        if nid is None:
            continue
        nid = _normalize_id(nid)
        typ = (item.get("type") or "task").lower()
        if typ not in ("task", "gateway", "start", "end"):
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

        nodes.append(
            ProcessNode(
                id=nid,
                type=typ,
                actor_index=actor_index,
                label=label,
                next_ids=next_ids,
                next_labels=next_labels,
                gateway_type=gateway_type,
            )
        )

    return actors, nodes


def validate_no_isolated_human_tasks(
    actors: list[str], nodes: list[ProcessNode]
) -> list[str]:
    """
    人に属するタスクに孤立がないか検証する（DoD: 人のタスクの接続）。
    孤立 = タスクなのに next が空（かつ type が end でない）、または
    誰からも next で参照されていない（かつ type が start でない）。
    戻り値: 検出した問題のメッセージリスト（0件ならOK）。
    """
    id_to_node = {n.id: n for n in nodes}
    in_degree: dict[str | int, int] = {n.id: 0 for n in nodes}
    for node in nodes:
        for to_id in node.next_ids:
            if to_id in id_to_node:
                in_degree[to_id] = in_degree.get(to_id, 0) + 1

    issues: list[str] = []
    for node in nodes:
        if node.type != "task":
            continue
        actor_name = actors[node.actor_index] if node.actor_index < len(actors) else str(node.actor_index)
        # タスクで next が空なら「行き先のない孤立」
        if not node.next_ids:
            issues.append(
                f"孤立したタスク: id={node.id} (actor={actor_name}) に接続先(next)がありません。"
            )
        # 誰からも参照されていないタスクは「入り口のない孤立」（start は type が start なので対象外）
        if in_degree.get(node.id, 0) == 0:
            issues.append(
                f"孤立したタスク: id={node.id} (actor={actor_name}) へ接続する矢印がありません。"
            )
    return issues


def _assign_columns(nodes: list[ProcessNode], id_to_node: dict) -> None:
    """
    フロー順で列番号を付与。分岐発生時は「分岐前の列＋分岐先用の1列」とし、
    分岐先のノードは同一列に配置し得るようにする（横に間延びしない）。
    入次数0から BFS で列を伝播し、複数 predecessor の場合は最大列+1 を採用。
    """
    # 入次数を計算（next の逆方向）
    in_degree: dict[str | int, int] = {n.id: 0 for n in nodes}
    for node in nodes:
        for to_id in node.next_ids:
            if to_id in id_to_node:
                in_degree[to_id] = in_degree.get(to_id, 0) + 1

    # 列は未割り当てを -1 で表す
    for node in nodes:
        node.column = -1

    # 入次数0のノードを列0にし、BFS のキューに入れる。ループ時は type=start をシードにする
    queue: deque[ProcessNode] = deque()
    for node in nodes:
        if in_degree[node.id] == 0:
            node.column = 0
            queue.append(node)
    if not queue:
        # 閉路のみのグラフ（ループ）: スタートノードを列0でシード
        for node in nodes:
            if node.type == "start":
                node.column = 0
                in_degree[node.id] = 0
                queue.append(node)
                break

    while queue:
        n = queue.popleft()
        c = n.column
        for to_id in n.next_ids:
            next_node = id_to_node.get(to_id)
            if not next_node:
                continue
            # ループでスタートに戻る場合はスタートの列0を維持（DoD: ループ）
            if next_node.type == "start" and next_node.column == 0:
                in_degree[next_node.id] -= 1
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


def compute_layout(
    actors: list[str],
    nodes: list[ProcessNode],
    max_cols_per_slide: int | None = None,
) -> ProcessLayout:
    """
    アクター名・ノードリストからレイアウトを計算する。
    アクター数に応じてレーン高さ・タスクサイズを調整し、
    図がスライドの描画領域からはみ出さないようスケールする。
    ノードは列に割り当て、max_cols を超えたら次スライド。
    """
    layout = ProcessLayout(actors=actors, nodes=nodes)
    layout.content_top_offset = int(layout.slide_height * 0.25)

    # アクター数に応じたベースサイズ（少ない＝大きく、多い＝小さく）
    num_actors = len(actors) or 1
    layout.lane_height, layout.task_side = _base_sizes_for_actors(num_actors)
    layout.gap = layout.task_side

    id_to_node = {n.id: n for n in nodes}
    _assign_columns(nodes, id_to_node)

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
    bottom_margin = int(0.05 * layout.slide_height)
    available_height = layout.slide_height - layout.content_top_offset - bottom_margin
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

    # 各ノードの (left, top, width, height) を EMU で計算（スライド内の座標）
    for node in nodes:
        lane = node.actor_index
        col = node.col_in_slide

        left = layout.left_margin + layout.left_label_width + col * (layout.task_side + layout.gap)
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
        left = layout.left_margin + layout.left_label_width + col * (layout.task_side + layout.gap)
        # 列幅は1タスク時と同じ（task_side）。高さのみ分割。
        width = layout.task_side
        offset = 0
        for i, node in enumerate(group):
            h = row_height + (1 if i < remainder else 0)
            top = zone_top + offset
            offset += h
            layout.node_positions[node.id] = (left, top, width, h)

    return layout
