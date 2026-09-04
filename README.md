# Dashboard Analytics Censo 2022 (IBGE)

Aplicacao analitica em Python para explorar agregados do Censo 2022 por bairros, com ETL, modelagem, indicadores, rankings, storytelling, mapa quando houver geometria e exportacao de resultados.

## Objetivo

Transformar os arquivos de agregados por bairros em um produto de analytics interativo, preservando os dados brutos e criando uma camada tratada para analise executiva e tecnica.

## Tecnologias

- Python 3.11+
- Pandas e NumPy
- Plotly
- Streamlit
- GeoPandas para leitura da malha geografica
- OpenPyXL para Excel
- ReportLab para PDF
- Pytest para testes automatizados

## Estrutura do projeto

```text
.
|-- app.py
|-- requirements.txt
|-- README.md
|-- agregados_por_setores_censitarios/
|-- malha_com_atributos/
|-- data/
|   `-- processed/
|-- src/
|   |-- config.py
|   |-- data_loader.py
|   |-- data_cleaning.py
|   |-- modeling.py
|   |-- metrics.py
|   |-- filters.py
|   |-- charts.py
|   |-- maps.py
|   |-- exports.py
|   |-- insights.py
|   `-- utils.py
`-- tests/
    `-- test_metrics.py
```

## Instalacao

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

Execucao:

```bash
streamlit run app.py
```

Regenerar a camada tratada:

```bash
python -m src.pipeline
```

## Modelagem

A chave principal e `CD_BAIRRO`. A tabela basica fornece atributos geograficos e medidas gerais, enquanto as tabelas de demografia e cor/raca sao transformadas em fatos longas:

- `bairro`: dimensao analitica de bairro, municipio, UF, area e totais basicos.
- `race_population`: populacao por bairro e cor/raca.
- `race_sex`: populacao por bairro, sexo e cor/raca.
- `race_age`: populacao por bairro, faixa etaria agregada e cor/raca.
- `demo_age`: populacao por bairro e faixa etaria original/agregada.
- `demo_age_sex`: populacao por bairro, sexo e faixa etaria.
- `responsible_race`, `responsible_race_sex`, `responsible_race_age`: fatos de responsaveis pelo domicilio.

As tabelas de cor/raca e demografia sao enriquecidas com os atributos geograficos vindos da tabela basica. A duplicidade encontrada em `CD_BAIRRO` e registrada no log de tratamento; quando as metricas numericas repetidas sao iguais, o registro e preservado apenas uma vez para evitar dupla contagem.

## Indicadores

- Populacao total: soma de `v0001` na dimensao de bairros ou soma da fato compativel com filtros aplicados.
- IDR: indice de Simpson normalizado, `(1 - soma(p_i^2)) / (1 - 1/k)`, em que `p_i` e a proporcao de cada grupo racial e `k` e o numero de categorias observadas. Varia de 0 a 1; quanto maior, mais diversa e a distribuicao.
- Representatividade feminina: mulheres responsaveis pelo domicilio dividido pelo total de responsaveis, multiplicado por 100.
- Proporcao de jovens: populacao de 0 a 14 anos dividida pela populacao total, multiplicada por 100.
- Proporcao de idosos: populacao de 60 anos ou mais dividida pela populacao total, multiplicada por 100.
- Idade media estimada: media ponderada por pontos medios das faixas. Como a base trabalha com classes e nao idades individuais, o indicador e uma estimativa metodologica.

## Tratamento dos dados

O ETL:

- le arquivos a partir de caminhos relativos;
- converte colunas numericas `V...` e `AREA_KM2`;
- padroniza chaves e textos;
- registra duplicidades;
- nao altera os arquivos originais;
- gera validacoes de consistencia entre totais basicos, demograficos e cor/raca.

As validacoes podem apontar diferencas entre tabelas publicadas. Essas diferencas ficam visiveis na pagina "Qualidade dos Dados" e nao sao corrigidas artificialmente.

## Dashboard

Paginas incluidas:

- Visao Geral
- Municipios
- Bairros
- Demografia
- Diversidade Racial
- Responsaveis pelo Domicilio
- Mapa
- Insights e Storytelling
- Qualidade dos Dados
- Exportacao
- Sobre o Projeto

## Insights

Os textos da pagina "Insights e Storytelling" sao gerados dinamicamente a partir dos rankings e indicadores calculados no recorte filtrado. Nao ha frases fixas com nomes ou valores inventados.

## Exportacao

A aplicacao permite baixar:

- dados filtrados em CSV;
- relatorio Excel com abas de resumo, municipios, bairros, raca, sexo, faixa etaria e responsaveis;
- PDF com insights gerados.

## Observacoes

A malha geografica fornecida e da Bahia (`BA_bairros_CD2022`). O mapa utiliza geometria real quando `geopandas` esta instalado e quando o bairro filtrado existe na malha. Nenhuma coordenada e inventada.
