from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_AGG_DIR = ROOT_DIR / "agregados_por_setores_censitarios"
RAW_GEO_DIR = ROOT_DIR / "malha_com_atributos"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

BASIC_FILE = RAW_AGG_DIR / "Agregados_por_bairros_basico_BR.xlsx"
RACE_FILE = RAW_AGG_DIR / "Agregados_por_bairros_cor_ou_raca_BR.xlsx"
DEMOGRAPHY_FILE = RAW_AGG_DIR / "Agregados_por_bairros_demografia_BR.xlsx"
DICTIONARY_FILE = RAW_AGG_DIR / "dicionario_de_dados_agregados_por_setores_censitarios.xlsx"
GEO_FILE = RAW_GEO_DIR / "BA_bairros_CD2022.shp"

KEY_COLUMNS = ["CD_BAIRRO", "NM_BAIRRO"]
GEO_COLUMNS = [
    "CD_BAIRRO",
    "NM_BAIRRO",
    "CD_REGIAO",
    "NM_REGIAO",
    "CD_UF",
    "NM_UF",
    "CD_MUN",
    "NM_MUN",
    "CD_DIST",
    "NM_DIST",
    "CD_SUBDIST",
    "NM_SUBDIST",
    "CD_RGINT",
    "NM_RGINT",
    "CD_RGI",
    "NM_RGI",
    "CD_CONCURB",
    "NM_CONCURB",
    "AREA_KM2",
]

RACE_COLORS = {
    "Branca": "#E8ECEF",
    "Preta": "#3E4C59",
    "Amarela": "#F4C542",
    "Parda": "#B87333",
    "Indigena": "#2E8B57",
}

RACE_TOTAL_COLS = {
    "Branca": "V01317",
    "Preta": "V01318",
    "Amarela": "V01319",
    "Parda": "V01320",
    "Indigena": "V01321",
}

RACE_SEX_COLS = {
    ("Masculino", "Branca"): "V01322",
    ("Masculino", "Preta"): "V01323",
    ("Masculino", "Amarela"): "V01324",
    ("Masculino", "Parda"): "V01325",
    ("Masculino", "Indigena"): "V01326",
    ("Feminino", "Branca"): "V01327",
    ("Feminino", "Preta"): "V01328",
    ("Feminino", "Amarela"): "V01329",
    ("Feminino", "Parda"): "V01330",
    ("Feminino", "Indigena"): "V01331",
}

RESP_RACE_TOTAL_COLS = {
    "Branca": "V01332",
    "Preta": "V01333",
    "Amarela": "V01334",
    "Parda": "V01335",
    "Indigena": "V01336",
}

RESP_RACE_SEX_COLS = {
    ("Branca", "Masculino"): "V01337",
    ("Branca", "Feminino"): "V01338",
    ("Preta", "Masculino"): "V01339",
    ("Preta", "Feminino"): "V01340",
    ("Amarela", "Masculino"): "V01341",
    ("Amarela", "Feminino"): "V01342",
    ("Parda", "Masculino"): "V01343",
    ("Parda", "Feminino"): "V01344",
    ("Indigena", "Masculino"): "V01345",
    ("Indigena", "Feminino"): "V01346",
}

RESP_RACE_AGE_COLS = {
    ("Branca", "12 a 17 anos"): "V01347",
    ("Branca", "18 a 24 anos"): "V01348",
    ("Branca", "25 a 39 anos"): "V01349",
    ("Branca", "40 a 59 anos"): "V01350",
    ("Branca", "60 anos ou mais"): "V01351",
    ("Preta", "12 a 17 anos"): "V01352",
    ("Preta", "18 a 24 anos"): "V01353",
    ("Preta", "25 a 39 anos"): "V01354",
    ("Preta", "40 a 59 anos"): "V01355",
    ("Preta", "60 anos ou mais"): "V01356",
    ("Amarela", "12 a 17 anos"): "V01357",
    ("Amarela", "18 a 24 anos"): "V01358",
    ("Amarela", "25 a 39 anos"): "V01359",
    ("Amarela", "40 a 59 anos"): "V01360",
    ("Amarela", "60 anos ou mais"): "V01361",
    ("Parda", "12 a 17 anos"): "V01362",
    ("Parda", "18 a 24 anos"): "V01363",
    ("Parda", "25 a 39 anos"): "V01364",
    ("Parda", "40 a 59 anos"): "V01365",
    ("Parda", "60 anos ou mais"): "V01366",
    ("Indigena", "12 a 17 anos"): "V01367",
    ("Indigena", "18 a 24 anos"): "V01368",
    ("Indigena", "25 a 39 anos"): "V01369",
    ("Indigena", "40 a 59 anos"): "V01370",
    ("Indigena", "60 anos ou mais"): "V01371",
}

RACE_AGE_COLS = {
    ("0 a 14 anos", "Branca"): "V01372",
    ("0 a 14 anos", "Preta"): "V01373",
    ("0 a 14 anos", "Amarela"): "V01374",
    ("0 a 14 anos", "Parda"): "V01375",
    ("0 a 14 anos", "Indigena"): "V01376",
    ("15 a 29 anos", "Branca"): "V01377",
    ("15 a 29 anos", "Preta"): "V01378",
    ("15 a 29 anos", "Amarela"): "V01379",
    ("15 a 29 anos", "Parda"): "V01380",
    ("15 a 29 anos", "Indigena"): "V01381",
    ("30 a 59 anos", "Branca"): "V01382",
    ("30 a 59 anos", "Preta"): "V01383",
    ("30 a 59 anos", "Amarela"): "V01384",
    ("30 a 59 anos", "Parda"): "V01385",
    ("30 a 59 anos", "Indigena"): "V01386",
    ("60 anos ou mais", "Branca"): "V01387",
    ("60 anos ou mais", "Preta"): "V01388",
    ("60 anos ou mais", "Amarela"): "V01389",
    ("60 anos ou mais", "Parda"): "V01390",
    ("60 anos ou mais", "Indigena"): "V01391",
}

DEMO_SEX_COLS = {"Masculino": "V01007", "Feminino": "V01008"}

DEMO_AGE_SEX_COLS = {
    ("Masculino", "0 a 4 anos"): "V01009",
    ("Masculino", "5 a 9 anos"): "V01010",
    ("Masculino", "10 a 14 anos"): "V01011",
    ("Masculino", "15 a 19 anos"): "V01012",
    ("Masculino", "20 a 24 anos"): "V01013",
    ("Masculino", "25 a 29 anos"): "V01014",
    ("Masculino", "30 a 39 anos"): "V01015",
    ("Masculino", "40 a 49 anos"): "V01016",
    ("Masculino", "50 a 59 anos"): "V01017",
    ("Masculino", "60 a 69 anos"): "V01018",
    ("Masculino", "70 anos ou mais"): "V01019",
    ("Feminino", "0 a 4 anos"): "V01020",
    ("Feminino", "5 a 9 anos"): "V01021",
    ("Feminino", "10 a 14 anos"): "V01022",
    ("Feminino", "15 a 19 anos"): "V01023",
    ("Feminino", "20 a 24 anos"): "V01024",
    ("Feminino", "25 a 29 anos"): "V01025",
    ("Feminino", "30 a 39 anos"): "V01026",
    ("Feminino", "40 a 49 anos"): "V01027",
    ("Feminino", "50 a 59 anos"): "V01028",
    ("Feminino", "60 a 69 anos"): "V01029",
    ("Feminino", "70 anos ou mais"): "V01030",
}

DEMO_AGE_COLS = {
    "0 a 4 anos": "V01031",
    "5 a 9 anos": "V01032",
    "10 a 14 anos": "V01033",
    "15 a 19 anos": "V01034",
    "20 a 24 anos": "V01035",
    "25 a 29 anos": "V01036",
    "30 a 39 anos": "V01037",
    "40 a 49 anos": "V01038",
    "50 a 59 anos": "V01039",
    "60 a 69 anos": "V01040",
    "70 anos ou mais": "V01041",
}

AGE_TO_REQUIRED_GROUP = {
    "0 a 4 anos": "0 a 14 anos",
    "5 a 9 anos": "0 a 14 anos",
    "10 a 14 anos": "0 a 14 anos",
    "15 a 19 anos": "15 a 29 anos",
    "20 a 24 anos": "15 a 29 anos",
    "25 a 29 anos": "15 a 29 anos",
    "30 a 39 anos": "30 a 39 anos",
    "40 a 49 anos": "40 a 59 anos",
    "50 a 59 anos": "40 a 59 anos",
    "60 a 69 anos": "60 anos ou mais",
    "70 anos ou mais": "60 anos ou mais",
}

AGE_MIDPOINT = {
    "0 a 4 anos": 2,
    "5 a 9 anos": 7,
    "10 a 14 anos": 12,
    "15 a 19 anos": 17,
    "20 a 24 anos": 22,
    "25 a 29 anos": 27,
    "30 a 39 anos": 34.5,
    "40 a 49 anos": 44.5,
    "50 a 59 anos": 54.5,
    "60 a 69 anos": 64.5,
    "70 anos ou mais": 75,
    "12 a 17 anos": 14.5,
    "18 a 24 anos": 21,
    "25 a 39 anos": 32,
    "40 a 59 anos": 49.5,
    "60 anos ou mais": 67.5,
}

