# Modelagem de dados da Olist

[English](README.md) | **Português**

Peguei o dataset público de e-commerce da Olist e fiz a modelagem de ponta a ponta: de nove arquivos CSV brutos até um star schema testado, que responde perguntas de negócio com poucas linhas de SQL. O foco é o raciocínio por trás de cada decisão de modelagem, registrado junto com as alternativas que descartei.

## O problema

Dados brutos de um sistema de pedidos parecem fáceis de consultar, mas estão cheios de armadilhas. Aqui, o `customer_id` muda a cada pedido, então contá-lo esconde quem comprou de novo; uma avaliação pode cobrir vários pedidos; um CEP tem várias coordenadas, algumas fora do Brasil; e juntar pagamentos com itens multiplica os valores sem avisar. Consultados direto, os dados dão números errados sem nenhuma mensagem de erro.

## Dados

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), licença CC BY-NC-SA 4.0: cerca de 99 mil pedidos feitos entre 2016 e 2018. Os arquivos não ficam no repositório; o `scripts/download_data.py` baixa. Categorias, cidades e status ficam em português, como vieram.

## Como foi construído

```
data/raw/*.csv ──► staging (stg_*) ──► intermediate (int_*) ──► marts (dim_*, fct_*)
                   tipos e nomes       passos reaproveitados    o que as pessoas consultam
```

As transformações rodam no [dbt](https://www.getdbt.com/), sobre um arquivo local do [DuckDB](https://duckdb.org/), que lê os CSVs direto. O staging só converte tipos e renomeia; junções e agregações acontecem depois, para que qualquer número possa ser rastreado até uma linha da origem. Cada etapa foi desenhada em [docs/](docs/) antes de ser construída.

## O modelo

Desenhei duas vezes. O [modelo normalizado](model/normalized.md) mostra como os dados de origem se relacionam, em terceira forma normal. O [star schema](model/dimensional.md) reorganiza tudo para análise, com quatro fatos em grãos diferentes, para nada ser contado duas vezes:

| Fato | Uma linha é |
|---|---|
| `fct_order_items` | uma unidade de produto vendida |
| `fct_orders` | um pedido, com uma data para cada etapa (accumulating snapshot) |
| `fct_payments` | um pagamento |
| `fct_reviews` | uma avaliação ligada a um pedido |

Eles compartilham cinco dimensões: data, cliente, local de entrega, produto e vendedor.

## Principais decisões

As 35 estão em [docs/decisions.md](docs/decisions.md). As que mais pesaram:

- **O cliente é o `customer_unique_id`.** São 96.096 pessoas por trás de 99.441 `customer_id`; o endereço fica no pedido, porque 250 clientes compraram com mais de um CEP.
- **Os totais são somados por pedido antes de juntar**, e testes de reconciliação provam que os marts mantêm cada linha e cada real da origem.
- **"Entregue" é ter data de entrega**, e não o status: 8 pedidos estão `delivered` sem ela.
- **Uma correção que fiz no caminho:** primeiro supus que a mediana por CEP ignoraria os pontos fora do Brasil. Ao construir o modelo, 8 prefixos continuavam fora do país, então esses pontos agora saem antes da mediana.

## O que os dados mostram

De [docs/results.md](docs/results.md), gerado pelo `scripts/export_results.py`; nenhum número aqui foi digitado à mão.

- **Atraso derruba a nota:** pedidos entregues no prazo têm nota média 4,29; com 8 a 14 dias de atraso, 1,67, e 80% das avaliações com 1 ou 2 estrelas.
- **O prazo depende da região:** a mediana é de 7,2 dias em São Paulo e 25,9 no Amazonas.
- **Clientes raramente voltam:** 97% compraram uma vez só.
- **O cartão de crédito domina:** 74% dos pagamentos, com 3,5 parcelas em média.

## O que ficou de fora

O projeto cobre modelagem e transformação. Ingestão a partir de sistemas de origem, carga incremental, agendamento com um orquestrador e um data warehouse na nuvem são o próximo passo, que pretendo construir sobre este modelo num projeto separado. As categorias não foram traduzidas para o inglês, de propósito.

## Como reproduzir

Requer Python 3.12. Na raiz do repositório:

```bash
python -m venv .venv && source .venv/Scripts/activate   # no Linux/macOS: .venv/bin/activate
pip install -r requirements.txt
python scripts/download_data.py
cd dbt && dbt deps && dbt build && cd ..
python scripts/validate_marts.py && python scripts/export_results.py
```

O `dbt build` cria 19 modelos e roda 117 testes (com um alerta esperado: pontos de geolocalização fora do Brasil). Os relatórios ficam em `docs/validation.md` e `docs/results.md`.
