"""
Interfaz de chat para el Asesor Tecnico Pfannenberg.
Estilo visual alineado a la identidad de pfannenberg.com (azul marino + azul
de marca + acento dorado + fondo blanco).

Uso:
    streamlit run streamlit_app.py
"""

import uuid
import streamlit as st

from main import preguntar

# --- Paleta de marca (extraida de pfannenberg.com) --------------------------
NAVY = "#173A5E"
BRAND_BLUE = "#2E86C1"
LIGHT_BLUE_BG = "#EAF2F8"
ACCENT_GOLD = "#E8A33D"
GRAY_TEXT = "#555555"

st.set_page_config(
    page_title="Asesor Técnico Pfannenberg",
    page_icon="🌡️",
    layout="centered",
)

# --- Estado de sesión -------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role": "user"|"assistant", "content": str}]

# --- Estilos globales (botones, franja superior) ----------------------------
st.markdown(
    f"""
    <style>
    .stButton > button {{
        background-color: white;
        color: {BRAND_BLUE};
        border: 2px solid {BRAND_BLUE};
        border-radius: 2px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        font-size: 0.8rem;
    }}
    .stButton > button:hover {{
        background-color: {BRAND_BLUE};
        color: white;
        border: 2px solid {BRAND_BLUE};
    }}
    div.block-container {{
        padding-top: 1rem;
    }}
    </style>
    <div style="background:{NAVY}; margin: -1rem -1rem 1rem -1rem; padding: 6px 1rem;
                text-align:right; font-size:0.7rem; color:white; letter-spacing:0.5px;">
        DATOS VERIFICADOS · CATÁLOGO REAL PFANNENBERG
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Encabezado tipo marca ---------------------------------------------------
st.markdown(
    f"""
    <div style="display:flex; align-items:baseline; gap:0.5rem;">
        <span style="font-size:2.1rem; font-weight:800; color:{BRAND_BLUE};
                     letter-spacing:-1px;">Pfannenberg</span>
        <span style="font-size:1.3rem;">🌡️</span>
    </div>
    <div style="font-size:0.72rem; letter-spacing:2px; color:#777;
                text-transform:uppercase; margin-bottom:1.1rem;">
        Asesor Técnico IA — Gestión Térmica y Señalización
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Hero / intro -------------------------------------------------------------
st.markdown(
    f"""
    <div style="background:{LIGHT_BLUE_BG}; border-left:4px solid {ACCENT_GOLD};
                padding:1.1rem 1.4rem; border-radius:4px; margin-bottom:1.1rem;">
        <div style="color:{BRAND_BLUE}; font-size:1.35rem; font-weight:800;
                    line-height:1.25; margin-bottom:0.4rem;">
            RECOMENDACIONES TÉCNICAS<br>VERIFICADAS AL INSTANTE
        </div>
        <div style="color:{GRAY_TEXT}; font-size:0.92rem;">
            Describe tu gabinete o necesidad y el asesor recomienda productos
            reales del catálogo — nunca inventa un modelo que no exista.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Franja de categorías (como el pie del hero real de Pfannenberg) -------
st.markdown(
    f"""
    <div style="display:flex; background:linear-gradient(90deg, {BRAND_BLUE}, #5DADE2);
                border-radius:4px; overflow:hidden; margin-bottom:1.3rem;">
        <div style="flex:1; padding:0.7rem 0.5rem; color:white; font-weight:700;
                    text-align:center; font-size:0.85rem;
                    border-right:1px solid rgba(255,255,255,0.35);">
            🌀 Gestión Térmica
        </div>
        <div style="flex:1; padding:0.7rem 0.5rem; color:white; font-weight:700;
                    text-align:center; font-size:0.85rem;">
            🔔 Técnica de Señales
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Nueva conversación", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

# --- Ejemplos rápidos (útil para la demo en vivo) ---------------------------
if not st.session_state.messages:
    st.markdown(f"<div style='color:{GRAY_TEXT}; font-size:0.85rem; margin-bottom:0.4rem;'>Prueba con:</div>", unsafe_allow_html=True)
    ejemplos = [
        "Necesito ventilar un gabinete con IP54 y al menos 100 m³/h de caudal",
        "¿Qué unidad de enfriamiento me recomiendas para 800W de carga térmica?",
        "Necesito una alarma sonora de al menos 100 dB para alerta de incendio",
    ]
    cols = st.columns(len(ejemplos))
    for col, ejemplo in zip(cols, ejemplos):
        if col.button(ejemplo, use_container_width=True):
            st.session_state.pending_input = ejemplo

# --- Historial de chat --------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Input del usuario ---------------------------------------------------
entrada = st.chat_input("Describe tu gabinete o necesidad técnica...")
if "pending_input" in st.session_state:
    entrada = st.session_state.pop("pending_input")

if entrada:
    st.session_state.messages.append({"role": "user", "content": entrada})
    with st.chat_message("user"):
        st.markdown(entrada)

    with st.chat_message("assistant"):
        with st.spinner("Consultando catálogo..."):
            try:
                respuesta = preguntar(entrada, thread_id=st.session_state.thread_id)
            except Exception as e:
                respuesta = f"⚠️ Error al consultar el agente: {e}"
        st.markdown(respuesta)

    st.session_state.messages.append({"role": "assistant", "content": respuesta})