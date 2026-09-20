# Auditoria completa da pipeline de dados e da aplicação Streamlit

Data da auditoria: 20/09/2026

## Resumo executivo

A camada processada preserva exatamente 17.575 `CD_BAIRRO` únicos e todas as tabelas fato têm a cardinalidade estrutural esperada, sem chaves órfãs. As diferenças entre `populacao_total`, demografia e cor/raça já existem nos XLSX do IBGE e não foram criadas por joins da aplicação. Em especial, Gericinó/Rio de Janeiro já chega da fonte com 23.130 pessoas em `v0001`, 2.571 em `V01006` e 2.570 na soma das cinco categorias de cor/raça.

Há, entretanto, falhas comprovadas no código: (1) qualquer texto não numérico, inclusive `x`, era convertido em ausente e depois em zero; (2) o filtro de bairro usava `NM_BAIRRO`, podendo selecionar bairros homônimos em vários municípios; (3) o KPI populacional escolhia `race_age` para um filtro somente de idade ou somente de raça, em vez de `demo_age` e `race_population`; (4) uma combinação simultânea de sexo, idade e raça era apresentada embora nenhuma fato possua as três dimensões; (5) merges não declaravam cardinalidade com `validate=`; (6) a aplicação reconstruía todas as fatos a partir dos XLSX em memória, ignorando a camada processada; e (7) “População total” podia ser interpretada como total do Brasil, embora o universo seja apenas o recorte de bairros disponível.

Os totais do recorte são:

| Medida | Total |
|---|---:|
| População básica (`v0001`) | 83.649.397 |
| População demográfica (`V01006`) | 83.478.900 |
| Soma das 11 faixas de idade | 83.446.278 |
| Soma das 22 células idade × sexo | 83.303.083 |
| Soma das 5 categorias de cor/raça | 83.382.880 |
| Soma das 10 células cor/raça × sexo | 83.294.153 |
| Soma das 20 células cor/raça × idade | 83.099.024 |

Nenhum desses valores representa a população total brasileira. São totais do recorte dos 17.575 códigos de bairro contidos nos arquivos fornecidos.

## Fontes e método

Foram inspecionados integralmente `app.py`, todos os módulos de `src/`, os testes, os três XLSX originais, o dicionário do IBGE e os 12 CSVs processados. As validações foram recalculadas diretamente dos CSVs e rastreadas aos XLSX. A nota metodológica oficial do IBGE confirma que `x` indica omissão por sigilo em agregados por setores; zero e omissão não são equivalentes.

## Problemas confirmados

### Conversão silenciosa de ausente/suprimido em zero

`src/data_cleaning.py` chamava `to_numeric(...).fillna(0)` em toda coluna `V...` e `AREA_KM2`. `src/modeling.py` repetia `pd.to_numeric(..., errors="coerce").fillna(0).astype("int32")`. Qualquer `x`, vazio, `None`, texto inválido ou `NaN` tornava-se zero e ficava indistinguível de um zero real.

Impacto observado nos arquivos atuais: os três XLSX têm zero ocorrências literais de `x`. Cor/raça e demografia também não têm células nulas. Logo, os totais atualmente publicados não foram reduzidos por `x` nesses três arquivos. A falha é real e crítica para reprocessamentos, arquivos por setor ou futuras versões, mas não explica as diferenças numéricas atuais.

### Seleção errada da tabela fato no KPI populacional

Em `summary_kpis`:

- filtro somente de idade usava `race_age`, não `demo_age`;
- filtro somente de cor/raça usava `race_age`, não `race_population`;
- sexo + idade + raça caía em `race_age`, que não possui sexo e ignora essa dimensão;
- filtros são aplicados somente quando a coluna existe, portanto combinações incompatíveis podem ser silenciosamente ignoradas em KPIs secundários.

Isso produz números diferentes da fato mais direta e, na combinação de três dimensões, um número sem o cruzamento solicitado.

### Filtro territorial por nome

O seletor e `filter_frame` usam `NM_MUN` e `NM_BAIRRO`. Nomes não são chaves. Ao escolher um nome de bairro repetido sem restringir adequadamente o município, todos os homônimos entram no cálculo. O filtro deve transmitir `CD_MUN` e `CD_BAIRRO`, mantendo o nome apenas no rótulo.

### Universo geográfico mal rotulado

O card “População total” soma `bairro.csv`. O resultado, 83.649.397, cobre somente os bairros presentes na estrutura fornecida e não o Brasil inteiro. O número é correto para esse recorte, mas o rótulo é ambíguo e metodologicamente incorreto se interpretado como total nacional.

### Uso desnecessário dos XLSX na aplicação

Apesar da existência dos CSVs processados, `load_project()` lê os três XLSX e refaz limpeza/modelagem a cada invalidação de cache. A memória profunda aproximada dos CSVs lidos sem otimização é 531 MB (6 + 55 + 116 + 22 + 47 + 95 + 22 + 120 + 47 MB). O cache evita repetições dentro do processo, mas não corrige o pico inicial. Carregamento seletivo das fatos processadas e Parquet reduziriam tempo e memória.

### Merge sem contrato explícito

Os merges atuais não são muitos-para-muitos, mas não usam `validate=`. Em `build_model`, cor/raça e demografia (um registro por código após limpeza) recebem a dimensão básica por merge muitos-para-um. Os merges de indicadores já agregados são um-para-um. Sem validação, uma regressão na unicidade pode gerar multiplicação silenciosa.

## Problemas prováveis ou limitações metodológicas

- Somas de decomposições são menores que seus totais de referência. Como os XLSX de bairro não contêm `x`, isso não é perda introduzida pelo ETL. É necessário tratar cada variável conforme seu universo publicado e não forçar igualdade.
- A média simples dos IDRs dos bairros não é um “IDR do recorte” e dá o mesmo peso a bairros de tamanhos muito diferentes. Ela pode ser exibida, mas deve ser rotulada “média não ponderada do IDR dos bairros”.
- Proporções calculadas apenas sobre categorias publicadas podem excluir células não divulgadas. O denominador precisa ser descrito como soma das células disponíveis da mesma fato.
- `safe_divide` devolve zero para denominador zero. Em indicadores estatísticos, “não calculável” é mais fiel que 0% quando o universo é vazio ou integralmente ausente.

## Falsos problemas identificados

- Nomes curtos, numéricos ou alfanuméricos não são motivo para exclusão. Todos os 17.575 códigos são preservados.
- As diferenças entre tabelas não decorrem de merge cartesiano na versão analisada.
- Gericinó não foi alterado pelo ETL: a discrepância existe na fonte.
- A redução de 17.576 para 17.575 não descartou duas linhas idênticas: agregou duas linhas diferentes que compartilham o mesmo código.

## Tratamento dos valores `x`

Contagem literal nos XLSX fornecidos:

| Arquivo | Ocorrências de `x` |
|---|---:|
| básico | 0 |
| cor/raça | 0 |
| demografia | 0 |

O código anterior não preservava essa distinção. A regra correta é: zero numérico permanece zero; `x` torna-se valor ausente com marca de supressão; vazio/`None` permanece ausente; agregações usam somente valores publicados e retornam ausente quando nenhuma célula do grupo está disponível. Não se estima valor suprimido.

## Auditoria dos nomes de bairros

Classificação diagnóstica, sem exclusões:

| Classe | Quantidade |
|---|---:|
| NORMAL | 16.970 |
| CURTO (até 4 caracteres, após priorizar numéricos) | 286 |
| ALFANUMÉRICO | 257 |
| NUMÉRICO | 61 |
| REPETITIVO | 1 |

Não há `CD_BAIRRO` nulo, `NM_BAIRRO` nulo, chave duplicada na camada final, chave associada a mais de um nome na camada final ou chave associada a mais de um município na camada final. A classificação é exclusivamente diagnóstica.

## Auditoria do `CD_BAIRRO` duplicado

O código duplicado nos três XLSX é `3205200069`, Vila Velha/ES. Os registros não são idênticos:

| Origem | Nome | Distrito | Área km² | População básica/demográfica |
|---|---|---|---:|---:|
| linha 1 | São Toquarto | Argolas (`320520010`) | 0,1973446 | 1.632 |
| linha 2 | São Torquato | São Torquato (`320520025`) | 0,3543462 | 2.444 |

Em cor/raça e demografia, todas as medidas relevantes também diferem. Somar contagens é necessário para não perder população: o total consolidado é 4.076. Contudo, o algoritmo anterior também somava medidas não aditivas: `v0005` virava 5,4 e `v0006` virava 0,0253. Isso é incorreto. Área e contagens são aditivas; médias e percentuais devem ser recalculados ou ponderados; atributos territoriais conflitantes devem ser registrados, não silenciosamente escolhidos. O nome “São Toquarto” parece erro de origem, mas não foi usado como justificativa para exclusão ou alteração de dado oficial.

## Auditoria de cardinalidade e merges

| Tabela | Linhas por `CD_BAIRRO` | Linhas | Chaves órfãs |
|---|---:|---:|---:|
| bairro | 1 | 17.575 | — |
| demo_age | 11 | 193.325 | 0 |
| demo_age_sex | 22 | 386.650 | 0 |
| race_population | 5 | 87.875 | 0 |
| race_sex | 10 | 175.750 | 0 |
| race_age | 20 | 351.500 | 0 |
| responsible_race | 5 | 87.875 | 0 |
| responsible_race_age | 25 | 439.375 | 0 |
| responsible_race_sex | 10 | 175.750 | 0 |

Contratos esperados:

- fonte temática → dimensão territorial: muitos-para-um na modelagem longa ou um-para-um antes do `melt`;
- dimensão → fato: um-para-muitos;
- indicadores previamente agregados por código: um-para-um;
- geometria BA → indicador de bairro: um-para-um, condicionada à unicidade da malha;
- merge direto entre duas fatos por `CD_BAIRRO`: proibido sem agregação prévia, pois seria muitos-para-muitos.

## Auditoria de filtros

Os filtros são aplicados independentemente a todas as tabelas e ignorados quando a coluna não existe. Isso é aceitável somente se a interface declarar a incompatibilidade. A combinação UF/município/bairro deve usar códigos. Filtros de sexo, idade e raça devem escolher uma fato que contenha exatamente as dimensões solicitadas. Não existe fato com sexo × idade × raça, então essa combinação não pode produzir um KPI conjunto.

Uma soma após filtro não excedeu a soma anterior nos dados não negativos inspecionados. O risco principal é semântico (filtro ignorado), não aritmético.

## Auditoria dos KPIs, gráficos e tabelas

| Elemento | Fonte | Agregação/universo | Diagnóstico |
|---|---|---|---|
| População coberta | `bairro.populacao_total` ou fato compatível | soma | rótulo ambíguo; seleção de fato errada em alguns filtros |
| Municípios/bairros | `bairro` | `nunique` de código | correto no recorte filtrado |
| IDR médio | `race_population` | Simpson normalizado por bairro, média simples | cálculo interno coerente; rótulo deve declarar média não ponderada |
| Representatividade feminina | `responsible_race_sex` | mulheres / responsáveis publicados | correto no universo dessa fato; pode ser distorcido por filtros incompatíveis |
| Jovens/idosos | `demo_age` | faixa / soma das faixas publicadas | coerente, mas denominador não é `v0001` |
| Distribuição racial | `race_population` | soma por raça | coerente; total 83.382.880, não população básica |
| Pirâmide etária | `demo_age_sex` | soma por sexo/faixa | coerente com a fato; `fillna(0)` do gráfico deve ser evitado para supressão total |
| Municípios/Bairros | indicadores agregados e merges | merges por código | sem M:N, mas faltava `validate=` |
| Responsáveis | fatos `responsible_*` | soma/percentual | universo é pessoa responsável, não população geral |
| Mapa | dimensão + indicadores | merge por `CD_BAIRRO` | apenas Bahia possui geometria; validar unicidade da malha |
| Exportação | modelo filtrado | mesmas regras do app | herda problemas de filtro/KPI |

## Comparação de totais

### População básica × demográfica

- diferença líquida: 170.497 pessoas;
- bairros afetados: 1.510;
- maior diferença: Gericinó/Rio de Janeiro, 20.559;
- em Gericinó: `v0001=23.130`, `V01006=2.571`, idade=2.571 e idade×sexo=2.571.

### Cor/raça × população básica

- diferença líquida: -266.517;
- bairros afetados: 13.000;
- maior diferença absoluta: Gericinó, 20.560;
- percentis da diferença absoluta: P50=2, P90=17, P95=32, P99=153,78.

Maiores diferenças por UF: Rio de Janeiro (-47.925), São Paulo (-41.258), Pernambuco (-22.677), Santa Catarina (-22.272) e Rio Grande do Sul (-17.086). Maiores por município: Rio de Janeiro (-32.736), Recife (-8.132), Boa Vista (-7.586), Salvador (-7.353) e Itaitinga (-6.926).

### Outras decomposições

| Comparação | Diferença líquida | Bairros afetados | Maior diferença | P50 | P90 | P95 | P99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| idade × demografia | -32.622 | 4.973 | 286 | 0 | 6 | 10 | 21 |
| idade×sexo × demografia | -175.817 | 9.689 | 1.601 | 2 | 26 | 41 | 96 |
| raça × básica | -266.517 | 13.000 | 20.560 | 2 | 17 | 32 | 153,78 |
| raça×sexo × básica | -355.244 | 14.721 | 20.560 | 4 | 31 | 57 | 190,52 |
| raça×idade × básica | -550.373 | 16.416 | 20.568 | 9 | 57 | 102 | 306 |

Essas diferenças são monotonicamente maiores nas decomposições mais detalhadas, padrão compatível com limitações de divulgação/sigilo, mas os arquivos de bairro entregues já contêm zeros, não `x`. Não é possível reclassificar retroativamente quais zeros seriam suprimidos sem uma fonte que preserve essa marca. Portanto, zeros existentes não serão alterados nem estimados.

## Caso Gericinó

O rastreamento confirma:

- XLSX básico: 23.130 pessoas, 1.128 domicílios totais e 877 domicílios particulares ocupados;
- XLSX demografia: 2.571 moradores, 1.266 homens e 1.305 mulheres; as 11 faixas somam 2.571;
- XLSX cor/raça: 754 brancas, 510 pretas, 0 amarelas, 1.300 pardas e 6 indígenas, soma 2.570.

A presença de população em domicílios coletivos é uma explicação plausível para a grande diferença entre total básico e variáveis de pessoas/domicílios, especialmente pela natureza territorial de Gericinó, mas isso é inferência contextual; a documentação local não rotula `V01006` com uma exclusão explícita. O fato comprovado é que a discrepância está na publicação fonte, não no ETL. A dashboard deve manter universos separados.

## Impacto e prioridade

| Problema | Impacto | Prioridade |
|---|---|---|
| `x`/ausente convertido em 0 | quebra integridade estatística e mascara sigilo | crítica |
| fato errada nos filtros | KPI populacional incorreto | crítica |
| combinação sexo×idade×raça sem fato | filtro ignorado silenciosamente | crítica |
| bairro filtrado por nome | mistura bairros homônimos | alta |
| rótulo de população nacional/total | interpretação errada do universo | alta |
| soma de média/percentual na duplicata | dois atributos incorretos em um bairro | média |
| merges sem `validate=` | risco de regressão e dupla contagem | média |
| reconstrução em XLSX | pico de memória e lentidão | média |

## Correções realizadas

O relatório foi criado antes das mudanças de código, conforme solicitado. Depois do diagnóstico, foram aplicadas somente as correções comprovadas:

- `x`, vazio e nulo deixam de receber `fillna(0)`; contagens usam `Int32` anulável nas fatos e agregações preservam ausência quando todo o grupo é desconhecido;
- a duplicata `3205200069` passa a somar contagens e área mesmo quando valores coincidem, enquanto `v0005` e `v0006` são ponderados por `v0007`; no registro consolidado, `v0005` passou do valor incorreto 5,4 para 2,716866 e `v0006` de 0,0253 para 0,012625;
- a dimensão `bairro` ganhou `status_nome`, estritamente diagnóstico, sem remoção de registros;
- todos os merges da modelagem, indicadores e mapa agora declaram `validate="one_to_one"` onde aplicável;
- filtros de UF, município e bairro usam `CD_UF`, `CD_MUN` e `CD_BAIRRO`; o rótulo mantém nome e código para desambiguação;
- `CD_UF`/`NM_UF` foram propagados às fatos, evitando que um filtro somente de UF fosse ignorado;
- o filtro etário foi alinhado à granularidade comum publicada (`30 a 59`), agregando `30 a 39` e `40 a 59` na fato demográfica;
- o KPI usa `demo_age` para idade, `race_population` para raça, `demo_age_sex` para sexo×idade, `race_sex` para sexo×raça e `race_age` para idade×raça;
- sexo×idade×raça retorna indisponível e mostra aviso, pois nenhuma tabela fornecida contém esse cruzamento;
- o card foi renomeado para “População coberta pelos bairros da base”;
- o ETL gera Parquet Zstandard e o Streamlit prefere a camada processada, mantendo CSV como fallback. Os nove Parquets ocupam 10,83 MB contra 166,60 MB dos 12 CSVs; o modelo carregado e otimizado ocupa aproximadamente 54,22 MB em memória, contra cerca de 531 MB na leitura ingênua dos CSVs;
- foram adicionados testes de chave, 17.575 bairros, cardinalidade das fatos, chaves órfãs, supressão, consolidação da duplicata, filtros combinados, mapeamento etário e monotonicidade de soma.

Após a regeneração, os totais populacionais permaneceram inalterados. Isso confirma que as divergências publicadas não foram “corrigidas” artificialmente. A suíte final tem 9 testes aprovados e o carregamento real da aplicação a partir dos Parquets foi validado.

## Correções recomendadas

- preservar `x` e ausências como valores nulos distintos de zero, com indicador de supressão quando presente;
- usar inteiros anuláveis (`Int32`) nas fatos;
- escolher a fato pela combinação exata de dimensões e bloquear combinações inexistentes;
- usar códigos nos filtros territoriais e incluir UF;
- explicitar “população coberta pelos bairros da base”;
- adicionar `validate=` em todo merge;
- ponderar `v0005`/`v0006` na consolidação da chave duplicada, sem somar taxas;
- carregar fatos processadas seletivamente; avaliar Parquet quando `pyarrow` estiver disponível;
- manter fatos separadas e nunca uni-las diretamente em uma tabela gigante;
- ampliar testes para integridade, filtros combinados, supressão e conservação de totais.

## Referências oficiais

- IBGE, Censo Demográfico 2022, Agregados por Setores Censitários: https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html
- IBGE, Nota metodológica n. 06, tratamento de sigilo e marca `x`: https://biblioteca.ibge.gov.br/visualizacao/livros/liv102136.pdf
