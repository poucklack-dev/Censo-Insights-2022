from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


DISPLAY_NAMES: dict[str, str] = {
    "CD_REGIAO": "Código da Região",
    "NM_REGIAO": "Região",
    "CD_UF": "Código da UF",
    "NM_UF": "Estado",
    "CD_MUN": "Código do Município",
    "NM_MUN": "Município",
    "Municipio": "Município",
    "CD_DIST": "Código do Distrito",
    "NM_DIST": "Distrito",
    "CD_SUBDIST": "Código do Subdistrito",
    "NM_SUBDIST": "Subdistrito",
    "CD_BAIRRO": "Código do Bairro",
    "NM_BAIRRO": "Bairro",
    "CD_RGINT": "Código da Região Geográfica Intermediária",
    "NM_RGINT": "Região Geográfica Intermediária",
    "CD_RGI": "Código da Região Geográfica Imediata",
    "NM_RGI": "Região Geográfica Imediata",
    "CD_CONCURB": "Código da Concentração Urbana",
    "NM_CONCURB": "Concentração Urbana",
    "AREA_KM2": "Área (km²)",
    "Populacao": "População",
    "Populacao total": "População Analisada",
    "Municipios": "Municípios",
    "Bairros": "Bairros",
    "IDR medio": "Índice de Diversidade Racial Médio",
    "populacao_total": "População Residente",
    "pop_demografia_total": "População na Base Demográfica",
    "pop_masculina": "População Masculina",
    "pop_feminina": "População Feminina",
    "valor": "População",
    "IDR": "Índice de Diversidade Racial (IDR)",
    "categorias": "Grupos Raciais Observados",
    "Posicao": "Posição",
    "Percentual": "Participação na População (%)",
    "Representatividade feminina": "Responsáveis do Sexo Feminino (%)",
    "Jovens": "População Jovem (%)",
    "Idosos": "População Idosa (%)",
    "Total": "Total de Pessoas",
    "Quantidade": "Quantidade de Pessoas",
    "Total_Responsaveis": "Total de Responsáveis",
    "Jovens_Pardos": "Jovens Pardos",
    "Cor_Raca": "Cor ou Raça",
    "Faixa_Etaria": "Faixa Etária",
    "Faixa_Etaria_Original": "Faixa Etária Detalhada",
    "Sexo": "Sexo",
    "Grupo racial predominante": "Grupo Racial Predominante",
    "Ponto_Medio_Estimado": "Ponto Médio Estimado da Idade",
    "Eh_Jovem": "Pessoa Jovem",
    "Eh_Idoso": "Pessoa Idosa",
    "Eh_40_Mais": "40 Anos ou Mais",
    "domicilios_total": "Domicílios",
    "domicilios_ocupados": "Domicílios Ocupados",
    "media_moradores_dpo": "Média de Moradores por Domicílio Ocupado",
    "pct_dpo_imputados": "Domicílios Ocupados com Valor Imputado (%)",
    "Domicilios": "Domicílios",
    "Domicilios_Ocupados": "Domicílios Ocupados",
    "Media_Moradores": "Média de Moradores por Domicílio Ocupado",
    "DPO_Imputados": "Domicílios Ocupados com Valor Imputado (%)",
    "Densidade": "Densidade Demográfica (hab./km²)",
    "tabela": "Tabela",
    "registros": "Registros",
    "colunas": "Colunas",
    "duplicados_linha": "Linhas Duplicadas",
    "duplicados_cd_bairro": "Códigos de Bairro Duplicados",
    "acao": "Tratamento",
    "quantidade": "Quantidade",
    "motivo": "Motivo",
    "validacao": "Validação",
    "registros_afetados": "Registros Afetados",
    "maior_diferenca": "Maior Diferença",
    "status": "Situação",
    "tema": "Tema",
    "variavel": "Variável",
    "descricao": "Descrição",
    "aba": "Planilha de Origem",
    "sigla": "Sigla",
    "tipo": "Tipo",
    "variavel_norm": "Código Normalizado da Variável",
}


METRIC_HELP: dict[str, dict[str, str]] = {
    "IDR": {
        "name": "Índice de Diversidade Racial (IDR)",
        "description": (
            "Mede a diversidade da composição racial pelo índice de Simpson normalizado. "
            "O cálculo usa (1 − soma das proporções ao quadrado) dividido por "
            "(1 − 1/k), em que k é o número de grupos raciais com população positiva. "
            "O resultado varia de 0 a 1; valores maiores indicam maior diversidade entre "
            "os grupos observados."
        ),
    },
    "IDR_MEDIO": {
        "name": "IDR Médio dos Bairros",
        "description": (
            "Média simples do Índice de Diversidade Racial dos bairros no recorte atual. "
            "Cada bairro tem o mesmo peso, independentemente de sua população."
        ),
    },
    "REPRESENTATIVIDADE_FEMININA": {
        "name": "Responsáveis do Sexo Feminino",
        "description": (
            "Percentual de responsáveis por domicílios identificados como do sexo feminino "
            "entre os responsáveis com informação disponível no recorte atual."
        ),
    },
    "JOVENS": {
        "name": "População Jovem",
        "description": "Percentual da população com idade entre 0 e 14 anos no recorte atual.",
    },
    "IDOSOS": {
        "name": "População Idosa",
        "description": "Percentual da população com 60 anos ou mais no recorte atual.",
    },
}


def get_display_name(column: str) -> str:
    """Return the user-facing name while preserving unknown source columns."""
    return DISPLAY_NAMES.get(column, column.replace("_", " ").strip().title())


def get_metric_help(metric: str) -> str | None:
    item = METRIC_HELP.get(metric)
    return item["description"] if item else None


def presentation_frame(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    hidden: Iterable[str] = (),
) -> pd.DataFrame:
    """Create a display-only copy with friendly headers and optional column selection."""
    selected = list(columns) if columns is not None else list(df.columns)
    hidden_set = set(hidden)
    selected = [column for column in selected if column in df.columns and column not in hidden_set]
    return df.loc[:, selected].copy().rename(columns=get_display_name)
