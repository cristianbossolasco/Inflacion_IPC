REGIONES_INDEC = [
    "Nacional",
    "GBA",
    "Pampeana",
    "Noreste",
    "Noroeste",
    "Cuyo",
    "Patagonia",
]

PROVINCIA_A_REGION = {
    "Ciudad Autonoma de Buenos Aires": "GBA",
    "Buenos Aires": "GBA",
    "Catamarca": "Noroeste",
    "Chaco": "Noreste",
    "Chubut": "Patagonia",
    "Cordoba": "Pampeana",
    "Corrientes": "Noreste",
    "Entre Rios": "Pampeana",
    "Formosa": "Noreste",
    "Jujuy": "Noroeste",
    "La Pampa": "Pampeana",
    "La Rioja": "Noroeste",
    "Mendoza": "Cuyo",
    "Misiones": "Noreste",
    "Neuquen": "Patagonia",
    "Rio Negro": "Patagonia",
    "Salta": "Noroeste",
    "San Juan": "Cuyo",
    "San Luis": "Cuyo",
    "Santa Cruz": "Patagonia",
    "Santa Fe": "Pampeana",
    "Santiago del Estero": "Noroeste",
    "Tierra del Fuego": "Patagonia",
    "Tucuman": "Noroeste",
}


def region_para_provincia(provincia: str) -> str:
    return PROVINCIA_A_REGION[provincia]

