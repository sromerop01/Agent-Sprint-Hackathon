"""
Agente asesor tecnico de Pfannenberg.

Uso interactivo:
    python main.py

Uso programatico:
    from main import preguntar
    print(preguntar("necesito un filterfan con IP54 y al menos 100 m3/h", thread_id="sesion-1"))
"""

import os
import re
import json
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

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


# ---------------------------------------------------------------------------
# Reflection: despues de cada respuesta final del modelo, verificamos que
# cualquier numero de producto mencionado exista de verdad en el catalogo.
# Si el modelo "alucina" un ID que no esta en el dataset, lo marcamos en vez
# de dejarlo pasar sin chequear.
# ---------------------------------------------------------------------------
def _cargar_ids_validos():
    data_path = Path(__file__).parent / "pfannenberg_products.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {p["id"] for p in data["productos"]}


class ReflectionMiddleware(AgentMiddleware):
    """Valida, tras cada respuesta final, que los IDs de producto mencionados
    existan de verdad en el catalogo. No reemplaza la logica de grounding de
    la tool -- es una segunda capa de verificacion sobre el texto final."""

    def __init__(self):
        self._ids_validos = _cargar_ids_validos()

    def after_model(self, state, runtime):
        messages = state.get("messages", [])
        if not messages:
            return None
        ultimo = messages[-1]
        # Solo revisamos la respuesta final (sin llamadas a herramientas pendientes)
        if not isinstance(ultimo, AIMessage) or getattr(ultimo, "tool_calls", None):
            return None

        contenido = str(ultimo.content)
        ids_mencionados = re.findall(r"\b\d{8,}\b", contenido)
        ids_invalidos = [i for i in ids_mencionados if i not in self._ids_validos]

        if ids_invalidos:
            nuevo_contenido = (
                contenido
                + f"\n\n[Verificacion interna] no pude confirmar el/los ID(s) "
                f"{', '.join(ids_invalidos)} contra el catalogo. Por favor "
                f"verifica en products.pfannenberg.com antes de usar este dato."
            )
            return {"messages": [AIMessage(content=nuevo_contenido, id=ultimo.id)]}

        return None


SYSTEM_PROMPT = (
    "Eres un asesor tecnico de Pfannenberg. Ayudas a elegir el producto correcto "
    "de gestion termica (Filterfans, Cooling Units, Heaters) o senalizacion "
    "(alarmas sonoras, luces de alerta) segun las condiciones del gabinete "
    "industrial o entorno que describe el usuario.\n\n"
    "Reglas:\n"
    "- Responde SOLO con productos que la herramienta buscar_producto_pfannenberg "
    "confirme que existen en el catalogo. Nunca inventes un producto o una spec.\n"
    "- Si faltan datos clave para recomendar bien (tipo de ambiente, grado IP "
    "requerido, espacio disponible, temperatura, potencia necesaria), preguntalos "
    "antes de llamar a la herramienta.\n"
    "- Si la herramienta no encuentra nada que cumpla los requisitos, dilo "
    "explicitamente en vez de forzar una recomendacion.\n"
    "- Recuerda lo que el usuario ya te conto en turnos anteriores de esta "
    "conversacion; no vuelvas a preguntar datos que ya te dio.\n"
    "- Cuando recomiendes un producto especifico, incluye siempre el link de "
    "ficha_tecnica_url que te devuelve la herramienta, para que el usuario "
    "pueda verificarlo.\n"
    "- Se conciso y tecnico, como lo seria un ingeniero de aplicaciones real."
)

model = get_model()
tools = [buscar_producto_pfannenberg]

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    middleware=[ReflectionMiddleware()],
    checkpointer=InMemorySaver(),
)


def preguntar(mensaje: str, thread_id: str = "default") -> str:
    """Envia un mensaje al agente y devuelve la respuesta en texto.

    thread_id identifica la sesion: usa el mismo thread_id entre llamadas
    para que el agente recuerde turnos anteriores (memory).
    """
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [{"role": "user", "content": mensaje}]}, config=config)
    return result["messages"][-1].content


def _chat_loop():
    thread_id = str(uuid.uuid4())
    print("Asesor tecnico Pfannenberg -- escribe 'salir' para terminar\n")
    while True:
        pregunta = input("Tu: ").strip()
        if pregunta.lower() in ("salir", "exit", "quit"):
            break
        if not pregunta:
            continue
        respuesta = preguntar(pregunta, thread_id=thread_id)
        print(f"\nAgente: {respuesta}\n")


if __name__ == "__main__":
    _chat_loop()