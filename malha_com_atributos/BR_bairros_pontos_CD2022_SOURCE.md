# Pontos representativos dos bairros do Brasil

O arquivo `BR_bairros_pontos_CD2022.csv` foi derivado da malha oficial
`BR_bairros_CD2022.zip`, publicada pelo IBGE:

https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/bairros/shp/BR/BR_bairros_CD2022.zip

Processamento:

1. leitura dos 17.575 polígonos e de `CD_BAIRRO`;
2. reprojeção de SIRGAS 2000 (`EPSG:4674`) para SIRGAS 2000 / Brazil Polyconic (`EPSG:5880`);
3. cálculo de um ponto representativo garantidamente dentro de cada polígono;
4. reprojeção para latitude/longitude (`EPSG:4326`);
5. armazenamento das coordenadas com seis casas decimais.

O CSV não contém as geometrias e tem como finalidade reduzir memória e tráfego
na visualização nacional do Streamlit. `CD_BAIRRO` permanece como chave de junção.
