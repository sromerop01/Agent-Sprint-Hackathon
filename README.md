# Agent-Sprint-Hackathon

Asesor técnico de Pfannenberg basado en un agente LLM (LangChain). Recomienda productos reales de gestión térmica (Filterfans, Cooling Units, Heaters) y señalización (alarmas sonoras, luces de alerta) según las condiciones del gabinete industrial que describa el usuario — siempre contra un catálogo verificado, sin inventar productos ni specs.

## Cómo funciona

```text
main.py ──► get_model() [groq | google] ──► create_agent(model, tools, system_prompt)
              │                                    │
              │                          ReflectionMiddleware
              │                    (marca IDs de producto no verificados)
              │
tools_pfannenberg.py ──► buscar_producto_pfannenberg ──► pfannenberg_products.json
```

- **`tools_pfannenberg.py`** — tool de LangChain que filtra el dataset local por categoría, subcategoría, IP rating, airflow, capacidad de enfriamiento, potencia y nivel sonoro. Reemplaza la API pública que Pfannenberg no ofrece.
- **`pfannenberg_products.json`** — catálogo curado a mano con productos reales (specs, IP rating, caso de uso, link a ficha técnica), sacado de products.pfannenberg.com.
- **`main.py`** — arma el agente con `create_agent`, mantiene memoria conversacional por `thread_id` (checkpointer en memoria) y valida tras cada respuesta que los IDs de producto mencionados existan de verdad en el catálogo.
- **`streamlit_app.py`** — interfaz de chat con el branding de Pfannenberg sobre `main.preguntar()`.
- **`test_setup.py`** — smoke test para correr antes de usar el agente: valida dependencias, proveedor/API key configurados y que el dataset y la tool carguen bien.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# completa la API key del proveedor que vayas a usar (GOOGLE_API_KEY o GROQ_API_KEY)
# y configura LLM_PROVIDER=google|groq
```

Verifica que todo esté listo:

```bash
python test_setup.py
```

## Uso

**Chat en terminal:**

```bash
python main.py
```

**Interfaz web (Streamlit):**

```bash
streamlit run streamlit_app.py
```

**Programático:**

```python
from main import preguntar
print(preguntar("necesito un filterfan con IP54 y al menos 100 m3/h", thread_id="sesion-1"))
```

## Configuración (`.env`)

| Variable | Descripción |
| --- | --- |
| `LLM_PROVIDER` | `google` o `groq` — qué proveedor de LLM usar |
| `GOOGLE_API_KEY` / `GROQ_API_KEY` | API key del proveedor elegido |
| `LLM_MODEL` | Modelo a usar (debe existir para el proveedor elegido) |
| `LLM_TEMPERATURE` | Temperatura del modelo |
