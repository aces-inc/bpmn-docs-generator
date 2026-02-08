"""YAML 業務プロセス定義の読み込みとレイアウト計算。"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# 1 inch = 914400 EMU（python-pptx の標準）
EMU_PER_INCH = 914400


@dataclass
class ProcessNode:
    """1 ノード（タスクまたは分岐）。"""

    id: str | int
    type: str  # "task" | "gateway"
    actor_index: int
    label: str
    next_ids: list[str | int]
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
    left_label_width: int = int(2.0 * EMU_PER_INCH)
    right_margin: int = int(0.5 * EMU_PER_INCH)
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
    num_slides: int = 1

    def __post_init__(self) -> None:
        if self.gap == 0:
            self.gap = self.task_side

    @property
    def content_width(self) -> int:
        return self.slide_width - self.left_label_width - self.right_margin

    @property
    def max_cols_per_slide(self) -> int:
        """1 スライドに並べられる最大タスク列数。"""
        unit = self.task_side + self.gap
        return max(1, self.content_width // unit)


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
        if typ not in ("task", "gateway"):
            typ = "task"
        actor = item.get("actor", 0)
        actor_index = _resolve_actor_index(actor, actors)
        label = str(item.get("label") or "")
        next_raw = item.get("next")
        if isinstance(next_raw, list):
            next_ids = [_normalize_id(x) for x in next_raw]
        elif next_raw is not None:
            next_ids = [_normalize_id(next_raw)]
        else:
            next_ids = []

        nodes.append(
            ProcessNode(
                id=nid,
                type=typ,
                actor_index=actor_index,
                label=label,
                next_ids=next_ids,
            )
        )

    return actors, nodes


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

    # 入次数0のノードを列0にし、BFS のキューに入れる
    queue: deque[ProcessNode] = deque()
    for node in nodes:
        if in_degree[node.id] == 0:
            node.column = 0
            queue.append(node)

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
    ノードは YAML の並び順で列に割り当て、max_cols を超えたら次スライド。
    """
    layout = ProcessLayout(actors=actors, nodes=nodes)
    layout.content_top_offset = int(layout.slide_height * 0.25)
    if max_cols_per_slide is None:
        max_cols_per_slide = layout.max_cols_per_slide

    id_to_node = {n.id: n for n in nodes}
    _assign_columns(nodes, id_to_node)

    for node in nodes:
        node.slide_index = node.column // max_cols_per_slide
        node.col_in_slide = node.column % max_cols_per_slide

    layout.num_slides = max((n.slide_index for n in nodes), default=0) + 1

    # エッジ収集（next から）
    for node in nodes:
        for to_id in node.next_ids:
            if to_id in id_to_node:
                layout.edges.append((node.id, to_id))

    # 各ノードの (left, top, width, height) を EMU で計算（スライド内の座標）
    for node in nodes:
        lane = node.actor_index
        col = node.col_in_slide

        left = layout.left_label_width + col * (layout.task_side + layout.gap)
        top = layout.content_top_offset + lane * layout.lane_height + (
            layout.lane_height - layout.task_side
        ) // 2
        layout.node_positions[node.id] = (
            left,
            top,
            layout.task_side,
            layout.task_side,
        )

    return layout
