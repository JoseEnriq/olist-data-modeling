"""Draw the star schema in model/dimensional.dbml as an SVG (model/dimensional.svg).

Facts go in the middle column and dimensions around them. Each box lists only
the key columns (PK/FK) plus a count of the other columns, so the picture
stays readable; the full column list is in model/dimensional.md.

Usage:
    python scripts/render_star_schema.py
"""

from pathlib import Path
from xml.sax.saxutils import escape

from pydbml import PyDBML

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "model" / "dimensional.dbml"
OUTPUT = ROOT / "model" / "dimensional.svg"

WIDTH = 1000
BOX_WIDTH = 240
HEADER = 34
ROW = 20
PADDING = 12
FACT_GAP = 28

# Column of each table and, for dimensions, the vertical position (top).
COLUMNS = {"left": 40, "center": (WIDTH - BOX_WIDTH) // 2, "right": WIDTH - BOX_WIDTH - 40}
FACTS = ["fct_order_items", "fct_orders", "fct_payments", "fct_reviews"]
DIMENSIONS = {
    "dim_location": ("left", 170),
    "dim_customer": ("left", 440),
    "dim_product": ("right", 60),
    "dim_seller": ("right", 230),
    "dim_date": ("right", 500),
}

COLORS = {
    "fact": "#1d4ed8",
    "dimension": "#0f766e",
    "line": "#94a3b8",
    "text": "#0f172a",
    "muted": "#64748b",
    "background": "#ffffff",
    "box": "#f8fafc",
}
FONT = "font-family='Segoe UI, Helvetica, Arial, sans-serif'"


def key_rows(table, foreign_keys):
    pk = {c.name for c in table.columns if c.pk} | {
        c.name for i in table.indexes if i.pk for c in i.subjects
    }
    rows = []
    for column in table.columns:
        marks = []
        if column.name in pk:
            marks.append("PK")
        if column.name in foreign_keys:
            marks.append("FK")
        if column.unique and column.name not in pk:
            marks.append("UK")
        if marks:
            rows.append((column.name, " ".join(marks)))
    others = len(table.columns) - len(rows)
    return rows, others


def box_height(rows, others):
    return HEADER + ROW * (len(rows) + (1 if others else 0)) + PADDING


def anchors(boxes, pairs):
    # Lines leave each box through the side that faces the other box, so they
    # stay in the gutters between columns and never cross a table. When several
    # lines use the same side, their end points are spread along it.
    by_side = {}
    for fact, dimension in pairs:
        dim_on_right = boxes[dimension][0] > boxes[fact][0]
        fact_side = (fact, "right" if dim_on_right else "left")
        dim_side = (dimension, "left" if dim_on_right else "right")
        by_side.setdefault(fact_side, []).append((fact, dimension))
        by_side.setdefault(dim_side, []).append((fact, dimension))

    points = {}
    for (name, side), links in by_side.items():
        x, y, w, h = boxes[name]
        other = lambda link: link[1] if link[0] == name else link[0]
        links.sort(key=lambda link: boxes[other(link)][1] + boxes[other(link)][3] / 2)
        edge_x = x + w if side == "right" else x
        usable = h - HEADER
        for i, link in enumerate(links):
            points[(name, link)] = (edge_x, y + HEADER + usable * (i + 1) / (len(links) + 1))
    return points


def draw_box(name, box, rows, others, kind):
    x, y, w, h = box
    color = COLORS[kind]
    parts = [
        f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='{COLORS['box']}' "
        f"stroke='{color}' stroke-width='1.5'/>",
        f"<path d='M{x},{y + 8} a8,8 0 0 1 8,-8 h{w - 16} a8,8 0 0 1 8,8 v{HEADER - 8} h-{w} z' "
        f"fill='{color}'/>",
        f"<text x='{x + 12}' y='{y + 22}' {FONT} font-size='14' font-weight='600' "
        f"fill='#ffffff'>{escape(name)}</text>",
    ]
    for i, (column, marks) in enumerate(rows):
        row_y = y + HEADER + ROW * i + 16
        parts.append(
            f"<text x='{x + 12}' y='{row_y}' {FONT} font-size='12' fill='{COLORS['text']}'>"
            f"{escape(column)}</text>"
        )
        parts.append(
            f"<text x='{x + w - 12}' y='{row_y}' {FONT} font-size='10' font-weight='600' "
            f"fill='{color}' text-anchor='end'>{marks}</text>"
        )
    if others:
        row_y = y + HEADER + ROW * len(rows) + 16
        parts.append(
            f"<text x='{x + 12}' y='{row_y}' {FONT} font-size='12' fill='{COLORS['muted']}' "
            f"font-style='italic'>+{others}</text>"
        )
    return parts


def main() -> None:
    model = PyDBML(SOURCE.read_text(encoding="utf-8"))
    tables = {t.name: t for t in model.tables}

    foreign_keys = {name: set() for name in tables}
    pairs = set()
    for ref in model.refs:
        foreign_keys[ref.table1.name].update(c.name for c in ref.col1)
        pairs.add((ref.table1.name, ref.table2.name))

    boxes, contents = {}, {}
    y = 40
    for name in FACTS:
        rows, others = key_rows(tables[name], foreign_keys[name])
        h = box_height(rows, others)
        boxes[name] = (COLUMNS["center"], y, BOX_WIDTH, h)
        contents[name] = (rows, others, "fact")
        y += h + FACT_GAP
    height = y + 12

    for name, (column, top) in DIMENSIONS.items():
        rows, others = key_rows(tables[name], foreign_keys[name])
        boxes[name] = (COLUMNS[column], top, BOX_WIDTH, box_height(rows, others))
        contents[name] = (rows, others, "dimension")

    svg = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{WIDTH}' height='{height}' "
        f"viewBox='0 0 {WIDTH} {height}'>",
        f"<rect width='{WIDTH}' height='{height}' rx='12' fill='{COLORS['background']}'/>",
    ]

    # Lines first, so the boxes are drawn on top of them.
    points = anchors(boxes, pairs)
    for link in sorted(pairs):
        fact, dimension = link
        x1, y1 = points[(fact, link)]
        x2, y2 = points[(dimension, link)]
        svg.append(
            f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
            f"stroke='{COLORS['line']}' stroke-width='1.5'/>"
        )

    for name, box in boxes.items():
        rows, others, kind = contents[name]
        svg += draw_box(name, box, rows, others, kind)

    svg.append("</svg>")
    OUTPUT.write_text("\n".join(svg) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(FACTS)} facts, {len(DIMENSIONS)} dimensions)")


if __name__ == "__main__":
    main()
