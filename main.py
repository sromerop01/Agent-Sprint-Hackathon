"""
Agente asesor tecnico de Pfannenberg.

Uso interactivo:
    python main.py

Uso programatico:
    from main import preguntar
    print(preguntar("necesito un filterfan con IP54 y al menos 100 m3/h"))
"""

import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent

from tools_pfannenberg import buscar_producto_pfannenberg

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))


def get_model():
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    elif LLM_PROVIDER == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    else:
        raise ValueError(f"LLM_PROVIDER no soportado: {LLM_PROVIDER}")


SYSTEM_PROMPT = (
    "Eres un asesor técnico de Pfannenberg. Ayudas a elegir el producto correcto "
    "de gestión térmica (Filterfans, Cooling Units, Heaters) o señalización "
    "(alarmas sonoras, luces de alerta) según las condiciones del gabinete "
    "industrial o entorno que describe el usuario.\n\n"
    "Reglas:\n"
    "- Responde SOLO con productos que la herramienta buscar_producto_pfannenberg "
    "confirme que existen en el catálogo. Nunca inventes un producto o una spec.\n"
    "- Si faltan datos clave para recomendar bien (tipo de ambiente, grado IP "
    "requerido, espacio disponible, temperatura, potencia necesaria), pregúntalos "
    "antes de llamar a la herramienta.\n"
    "- Si la herramienta no encuentra nada que cumpla los requisitos, dilo "
    "explícitamente en vez de forzar una recomendación.\n"
    "- Sé conciso y técnico, como lo sería un ingeniero de aplicaciones real."
)

model = get_model()
tools = [buscar_producto_pfannenberg]

agent = create_react_agent(
    model=model,
    tools=tools,
    prompt=SYSTEM_PROMPT,
)


def preguntar(mensaje: str) -> str:
    """Envía un mensaje al agente y devuelve la respuesta en texto."""
    result = agent.invoke({"messages": [{"role": "user", "content": mensaje}]})
    return result["messages"][-1].content


def _chat_loop():
    print("Asesor técnico Pfannenberg — escribe 'salir' para terminar\n")
    while True:
        pregunta = input("Tú: ").strip()
        if pregunta.lower() in ("salir", "exit", "quit"):
            break
        if not pregunta:
            continue
        respuesta = preguntar(pregunta)
        print(f"\nAgente: {respuesta}\n")


if __name__ == "__main__":
    _chat_loop()