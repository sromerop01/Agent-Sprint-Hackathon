"""
Tool para el agente: busca productos reales de Pfannenberg en el dataset local
(pfannenberg_products.json) según las especificaciones que pida el usuario.

Como Pfannenberg no tiene API pública, esta tool reemplaza esa llamada:
filtra sobre datos reales que curaste a mano desde su catálogo.
"""

import json
from pathlib import Path
from langchain_core.tools import tool

DATA_PATH = Path(__file__).parent / "pfannenberg_products.json"


def _cargar_productos() -> list[dict]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["productos"]


def _ip_cumple(ip_producto: str, ip_min: str) -> bool:
    """Compara ratings IP tipo 'IP54' vs 'IP44'. Devuelve True si el producto
    cumple o supera el mínimo pedido en ambos dígitos (polvo, agua)."""
    try:
        digitos_prod = [int(c) for c in ip_producto.replace("IP", "")[:2]]
        digitos_min = [int(c) for c in ip_min.replace("IP", "")[:2]]
        return digitos_prod[0] >= digitos_min[0] and digitos_prod[1] >= digitos_min[1]
    except (ValueError, IndexError):
        return True  # si no se puede parsear, no descarta el producto


@tool
def buscar_producto_pfannenberg(
    categoria: str = "",
    subcategoria: str = "",
    ip_rating_min: str = "",
    airflow_min_m3h: int = 0,
    capacidad_enfriamiento_min_w: int = 0,
    potencia_min_w: int = 0,
    sonido_min_db: int = 0,
) -> str:
    """Busca productos reales de Pfannenberg que cumplan las especificaciones dadas.

    Args:
        categoria: "Thermal Management" o "Signaling Technology". Vacío = todas.
        subcategoria: ej. "Filterfan", "Cooling Unit", "Heater", "Audible Signaling", "Visual Signaling". Vacío = todas.
        ip_rating_min: rating IP mínimo requerido, ej. "IP54".
        airflow_min_m3h: caudal de aire mínimo en m³/h (aplica a Filterfans).
        capacidad_enfriamiento_min_w: capacidad de enfriamiento mínima en watts (aplica a Cooling Units).
        potencia_min_w: potencia de calefacción mínima en watts (aplica a Heaters).
        sonido_min_db: nivel sonoro mínimo en dB(A) (aplica a alarmas/sounders).

    Devuelve una lista de productos que cumplen los criterios, con sus specs clave.
    Si no hay coincidencias, lo dice explícitamente en vez de inventar un producto.
    """
    productos = _cargar_productos()
    resultados = []

    for p in productos:
        if categoria and p["categoria"].lower() != categoria.lower():
            continue
        if subcategoria and p["subcategoria"].lower() != subcategoria.lower():
            continue
        if ip_rating_min and not _ip_cumple(p.get("ip_rating", ""), ip_rating_min):
            continue
        specs = p.get("specs", {})
        if airflow_min_m3h and (specs.get("airflow_m3h") or 0) < airflow_min_m3h:
            continue
        if capacidad_enfriamiento_min_w and (specs.get("capacidad_enfriamiento_w") or 0) < capacidad_enfriamiento_min_w:
            continue
        if potencia_min_w and (specs.get("potencia_w") or 0) < potencia_min_w:
            continue
        if sonido_min_db and (specs.get("sonido_db") or 0) < sonido_min_db:
            continue
        resultados.append(p)

    if not resultados:
        return (
            "No encontré ningún producto en el catálogo que cumpla exactamente esas "
            "especificaciones. Puedo mostrar la opción más cercana si quieres, pero "
            "no voy a recomendar algo que no esté verificado en el catálogo."
        )

    lineas = []
    for p in resultados:
        specs_txt = ", ".join(f"{k}={v}" for k, v in p.get("specs", {}).items() if v)
        lineas.append(
            f"- {p['nombre']} ({p['subcategoria']}) | ID: {p['id']} | "
            f"IP: {p.get('ip_rating', 'N/D')} | {specs_txt} | "
            f"Uso: {p['caso_de_uso']}"
        )
    return "Productos encontrados:\n" + "\n".join(lineas)
