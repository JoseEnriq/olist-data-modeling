# Modelos

| Arquivo | O que é |
|---|---|
| [normalized.dbml](normalized.dbml) | Modelo normalizado (3FN), fonte da verdade |
| [dimensional.dbml](dimensional.dbml) | Star schema, fonte da verdade |
| [normalized.md](normalized.md) | Diagrama do modelo normalizado, gerado a partir do `.dbml` |
| [dimensional.md](dimensional.md) | Diagrama do star schema, gerado a partir do `.dbml` |

As justificativas de cada tabela e relacionamento estão em [docs/decisions.md](../docs/decisions.md).

## Por que DBML e Mermaid

Os modelos são escritos como texto (DBML), e não desenhados à mão, para ficarem versionados no Git: uma mudança no modelo aparece no Pull Request como qualquer mudança de código. Os diagramas em Mermaid são gerados a partir do DBML por `scripts/render_diagrams.py`, então nunca ficam diferentes do modelo. O GitHub desenha o Mermaid direto na página.

Para atualizar os diagramas depois de mudar um `.dbml`:

```bash
python scripts/render_diagrams.py
```

## Ver e exportar no dbdiagram.io

O Mermaid organiza as tabelas sozinho. Para um diagrama com o layout escolhido à mão (fatos no centro, dimensões em volta):

1. Abra https://dbdiagram.io/d e cole o conteúdo de um `.dbml` no editor da esquerda.
2. Arraste as tabelas para organizar o desenho.
3. Exporte em *Export → PNG* (ou PDF).
