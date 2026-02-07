"""XML → Drawio → PPTX 一連フローを実行する CLI。"""

import argparse
import sys
from pathlib import Path

from . import __version__
from . import drawio2pptx
from . import xml2drawio


def _report_pptx_shapes(n: int, output_path: str) -> None:
    """PPTX に書き込んだ図形数を表示し、0 件のときは警告する。"""
    if n == 0:
        print("Warning: no shapes were added to the slide. Check input XML.", file=sys.stderr)
    else:
        print(f"Shapes: {n}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Drawio互換XMLを .drawio に変換し、編集可能なPPTXを生成する",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # xml → .drawio
    p_drawio = sub.add_parser("to-drawio", help="XML を .drawio ファイルに変換")
    p_drawio.add_argument("input", help="入力 XML ファイル（または - で標準入力）")
    p_drawio.add_argument("-o", "--output", required=True, help="出力 .drawio ファイル")

    # drawio/xml → pptx
    p_pptx = sub.add_parser("to-pptx", help=".drawio / XML から PPTX を生成")
    p_pptx.add_argument("input", help="入力 .drawio または Drawio XML ファイル")
    p_pptx.add_argument("-o", "--output", required=True, help="出力 .pptx ファイル")

    # 一連フロー: xml → drawio → pptx
    p_pipeline = sub.add_parser(
        "pipeline",
        help="XML → .drawio → PPTX を一括実行（中間 .drawio は任意で保存）",
    )
    p_pipeline.add_argument("input", help="入力 Drawio 互換 XML ファイル")
    p_pipeline.add_argument("-o", "--output", required=True, help="出力 .pptx ファイル")
    p_pipeline.add_argument(
        "--drawio",
        default=None,
        metavar="PATH",
        help="中間 .drawio を保存するパス（省略時は保存しない）",
    )

    args = parser.parse_args()

    if args.command == "to-drawio":
        if args.input == "-":
            xml_content = sys.stdin.read()
        else:
            xml_content = Path(args.input).read_text(encoding="utf-8")
        xml2drawio.save_drawio(xml_content, args.output)
        print(f"Saved: {args.output}")

    elif args.command == "to-pptx":
        path = Path(args.input)
        xml_content = path.read_text(encoding="utf-8")
        n = drawio2pptx.drawio_to_pptx(xml_content, args.output)
        print(f"Saved: {args.output}")
        _report_pptx_shapes(n, args.output)

    elif args.command == "pipeline":
        xml_content = Path(args.input).read_text(encoding="utf-8")
        if args.drawio:
            xml2drawio.save_drawio(xml_content, args.drawio)
            print(f"Saved drawio: {args.drawio}")
        n = drawio2pptx.drawio_to_pptx(xml_content, args.output)
        print(f"Saved pptx: {args.output}")
        _report_pptx_shapes(n, args.output)


if __name__ == "__main__":
    main()
