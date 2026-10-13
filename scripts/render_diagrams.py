"""Render every model/*.dbml file as a Mermaid ER diagram in model/<name>.md.

The DBML files are the source of truth. Generating the Mermaid version from
them keeps the diagrams that GitHub renders in sync with the model, instead
of maintaining two drawings by hand.

Usage:
    python scripts/render_diagrams.py
"""

import re
from pathlib import Path

from pydbml import PyDBML

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "model"

TITLES = {
    "normalized": "Modelo normalizado",
    "dimensional": "Modelo dimensional (star schema)",
}


def mermaid_type(dbml_type: str) -> str:
    # Mermaid attribute types cannot contain spaces or commas: decimal(10, 2) -> decimal
    return re.sub(r"\(.*\)", "", str(dbml_type)).strip()


def primary_key(table) -> set[str]:
    single = {c.name for c in table.columns if c.pk}
    composite = {c.name for i in table.indexes if i.pk for c in i.subjects}
    return single | composite


def render(dbml_path: Path) -> str:
    model = PyDBML(dbml_path.read_text(encoding="utf-8"))

    foreign_keys = {table.name: set() for table in model.tables}
    for ref in model.refs:
        foreign_keys[ref.table1.name].update(c.name for c in ref.col1)

    lines = ["erDiagram"]
    for table in model.tables:
        pk = primary_key(table)
        lines.append(f"    {table.name} {{")
        for column in table.columns:
            keys = []
            if column.name in pk:
                keys.append("PK")
            if column.name in foreign_keys[table.name]:
                keys.append("FK")
            if column.unique and column.name not in pk:
                keys.append("UK")
            lines.append(f"        {mermaid_type(column.type)} {column.name} {', '.join(keys)}".rstrip())
        lines.append("    }")

    for ref in model.refs:
        # ">" in DBML: table1 (many) points to table2 (one).
        many, one = ref.table1, ref.table2
        fk = ref.col1[0]
        optional = not (fk.not_null or fk.name in primary_key(many))
        left = "|o" if optional else "||"
        lines.append(f'    {one.name} {left}--o{{ {many.name} : "{fk.name}"')

    title = TITLES.get(dbml_path.stem, dbml_path.stem)
    out = [
        f"# {title}",
        "",
        f"Gerado por `scripts/render_diagrams.py` a partir de [{dbml_path.name}]({dbml_path.name}). "
        "Não edite à mão: altere o `.dbml` e rode o script de novo.",
        "",
        "Legenda: `PK` chave primária, `FK` chave estrangeira, `UK` valor único. "
        "`||--o{` = um para zero ou muitos; `|o--o{` = a chave estrangeira pode ser nula.",
        "",
        "```mermaid",
        *lines,
        "```",
        "",
        "## Tabelas",
        "",
        "| tabela | descrição |",
        "|---|---|",
    ]
    for table in model.tables:
        note = table.note.text.replace("\n", " ") if table.note and table.note.text else ""
        out.append(f"| `{table.name}` | {note} |")
    out.append("")
    return "\n".join(out)


def main() -> None:
    for dbml_path in sorted(MODEL_DIR.glob("*.dbml")):
        target = dbml_path.with_suffix(".md")
        target.write_text(render(dbml_path), encoding="utf-8")
        print(f"Wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
