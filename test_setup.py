"""
Corre esto ANTES de construir main.py, para confirmar que el entorno
esta listo: dependencias instaladas, API key funcionando, y los
archivos del proyecto (dataset + tool) presentes y cargables.

Uso: python test_setup.py
"""

import os
import sys
from pathlib import Path

# Cada proveedor soportado: que variable de entorno trae la key, que paquete
# pip lo provee, y como se instancia el chat model.
PROVEEDORES = {
    "google": {
        "env_key": "GOOGLE_API_KEY",
        "paquete": "langchain_google_genai",
        "pip_nombre": "langchain-google-genai",
    },
    "groq": {
        "env_key": "GROQ_API_KEY",
        "paquete": "langchain_groq",
        "pip_nombre": "langchain-groq",
    },
}


def check(nombre, condicion, detalle=""):
    estado = "OK" if condicion else "FALLA"
    print(f"[{estado}] {nombre}" + (f" — {detalle}" if detalle and not condicion else ""))
    return condicion


def _crear_chat(proveedor, model, api_key, temperature):
    if proveedor == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=temperature)
    if proveedor == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, api_key=api_key, temperature=temperature)
    raise ValueError(f"Proveedor desconocido: {proveedor}")


def main():
    todo_ok = True

    from dotenv import load_dotenv
    load_dotenv()

    # 1. Que proveedor toca usar (LLM_PROVIDER en .env)
    proveedor = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if proveedor not in PROVEEDORES:
        check(
            "LLM_PROVIDER configurado",
            False,
            f"pon LLM_PROVIDER=google|groq en .env (valor actual: '{proveedor or 'vacio'}')",
        )
        print("\nNo puedo seguir sin saber que proveedor usar. Configura LLM_PROVIDER en .env.")
        sys.exit(1)
    check("LLM_PROVIDER configurado", True, proveedor)
    info = PROVEEDORES[proveedor]

    # 2. Dependencias del proveedor elegido
    try:
        import langchain_core  # noqa: F401
        __import__(info["paquete"])
        todo_ok &= check(f"Dependencias instaladas (langchain-core, {info['pip_nombre']}, python-dotenv)", True)
    except ImportError as e:
        todo_ok &= check("Dependencias instaladas", False, f"falta instalar: {e.name}. Corre: pip install -r requirements.txt")
        print("\nNo puedo seguir verificando sin las dependencias. Instálalas y vuelve a correr este script.")
        sys.exit(1)

    # 3. .env presente y con la API key del proveedor elegido
    api_key = os.getenv(info["env_key"])
    todo_ok &= check(
        f".env cargado con {info['env_key']}",
        bool(api_key) and "tu_api_key" not in api_key,
        f"revisa que copiaste .env.example a .env y pusiste tu key real en {info['env_key']}"
    )

    # 4. La API key funciona de verdad (llamada real, mínima)
    model = os.getenv("LLM_MODEL", "")
    temperature = float(os.getenv("LLM_TEMPERATURE") or 0)
    if api_key and "tu_api_key" not in api_key and model:
        try:
            chat = _crear_chat(proveedor, model, api_key, temperature)
            respuesta = chat.invoke("Responde solo con la palabra: ok")
            todo_ok &= check(f"Llamada real a {proveedor} ({model}) funciona", "ok" in str(respuesta.content).lower())
        except Exception as e:
            todo_ok &= check(f"Llamada real a {proveedor} ({model}) funciona", False, str(e))
    else:
        check(f"Llamada real a {proveedor} funciona", False, "sin API key válida o sin LLM_MODEL, no se puede probar")
        todo_ok = False

    # 5. Dataset de productos presente y cargable
    try:
        import json
        data_path = Path(__file__).parent / "pfannenberg_products.json"
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        n_productos = len(data.get("productos", []))
        todo_ok &= check(f"pfannenberg_products.json cargado ({n_productos} productos)", n_productos > 0)
    except Exception as e:
        todo_ok &= check("pfannenberg_products.json cargado", False, str(e))

    # 6. Tool cargable y funcional
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from tools_pfannenberg import buscar_producto_pfannenberg
        resultado = buscar_producto_pfannenberg.invoke({"subcategoria": "Filterfan"})
        todo_ok &= check("tools_pfannenberg.py cargado y funcional", "PF" in resultado)
    except Exception as e:
        todo_ok &= check("tools_pfannenberg.py cargado y funcional", False, str(e))

    print()
    if todo_ok:
        print("Todo listo. Puedes seguir con main.py.")
    else:
        print("Hay pendientes arriba (FALLA) — resuélvelos antes de seguir.")

    sys.exit(0 if todo_ok else 1)


if __name__ == "__main__":
    main()
