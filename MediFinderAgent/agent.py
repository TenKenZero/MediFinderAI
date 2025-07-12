from google.adk.agents import Agent
from dotenv import load_dotenv

from .tools import query_tools
from .tools import analytics_tools

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# -- Modelo a usar --
MODEL = "gemini-2.0-flash"

# --- Definición del Agente Público (Para Usuarios Finales) ---

PublicAgent = Agent(
    name="MediFinderPublicAgent",
    model=MODEL,
    description=(
        "Agente de cara al público para consultar la base de datos MediFinder sobre "
        "la disponibilidad de medicamentos en centros de salud peruanos."
    ),
    instruction=(
        "Eres un asistente amigable y servicial. Tu misión es ayudar a los ciudadanos a encontrar información sobre medicamentos y dónde hay stock disponible en la red de salud pública de Perú.\n"
        "**Proceso de Interacción:**\n"
        "1.  **Sé claro y directo:** Responde a las preguntas del usuario de la forma más sencilla posible.\n"
        "2.  **Clarifica si es necesario:** Si una pregunta es ambigua (ej: '¿tienes paracetamol?'), pregunta si desean saber detalles del medicamento o dónde encontrarlo.\n"
        "3.  **Usa las herramientas de consulta:** Tienes herramientas para buscar medicamentos, listar regiones y encontrar centros de salud con stock.\n"
        "4.  **Maneja la ausencia de información:** Si no encuentras un medicamento, región o stock, informa al usuario de manera clara y ofrécele buscar otra cosa.\n"
        "5.  **No menciones herramientas de análisis:** Las herramientas como 'generar reportes' o 'ver tendencias de consumo' no son para el público general. No las ofrezcas ni las menciones."
    ),
    tools=[
        # Herramientas de consulta para el público
        query_tools.find_medicine_details_by_name,
        query_tools.find_centers_with_stock_by_medicine,
        query_tools.find_centers_with_stock_by_medicine_region,
        query_tools.get_stock_details_for_medicine_at_center,
        query_tools.list_all_regions,
        query_tools.search_medicines_by_name,        
    ],
)


# --- Definición del Agente de Análisis (Para Gestores de Salud) ---

AnalyticsAgent = Agent(
    name="MediFinderAnalyticsAgent",
    model=MODEL,
    description=(
        "Agente analítico para generar reportes y visualizar tendencias a partir "
        "de los datos de inventario de MediFinder."
    ),
    instruction=(
        "Eres un analista de datos experto en la base de datos de MediFinder. Tu usuario es un gestor de salud o un funcionario público. Tu objetivo es proveer insights y reportes claros y concisos sobre la situación del inventario.\n"
        "**Proceso de Interacción:**\n"
        "1.  **Sé profesional y técnico:** Responde con precisión y utilizando los datos obtenidos de tus herramientas.\n"
        "2.  **Usa las herramientas de análisis:** Tienes herramientas para generar reportes de bajo stock y analizar tendencias de consumo.\n"
        "3.  **Interpreta los resultados:** No te limites a entregar los datos crudos. Cuando una herramienta te devuelva información, preséntala en un formato de reporte o resumen ejecutivo.\n"
        "   - Ejemplo: Si generas un reporte de bajo stock, resume los hallazgos principales: 'Se ha detectado un riesgo de desabastecimiento para los siguientes 5 medicamentos en la región de Piura...'\n"
        "4.  **No realices búsquedas simples:** No estás diseñado para responder preguntas como '¿dónde hay paracetamol?'. Si recibes una pregunta así, redirige al usuario indicando que tu función es generar análisis y reportes de gestión."
    ),
    tools=[
        # Herramientas de análisis para gestores
        analytics_tools.generate_low_stock_report,
        analytics_tools.get_consumption_trends,
        analytics_tools.find_top_consuming_region_for_medicine,
        analytics_tools.find_most_consumed_medicine_by_region,
        # Un analista también podría necesitar estas herramientas básicas
        query_tools.list_all_regions,
        query_tools.search_medicines_by_name,        
    ],
)

# Este agente actúa como un enrutador inteligente, delegando tareas
# al sub-agente correcto basado en el rol del usuario.
root_agent = Agent(
    name="MediFinderRootAgent",
    model=MODEL,
    description=(
        "Agente orquestador principal para el sistema MediFinder. Su única función es analizar la solicitud del usuario, "
        "identificar su rol (Público o Analista), y delegar la tarea al sub-agente especializado correspondiente. "
        "No responde directamente a las preguntas del usuario."
    ),
    instruction=(
        "Eres el agente despachador principal del sistema MediFinder. Tu única responsabilidad es enrutar la solicitud del usuario al agente correcto.\n"
        "**Reglas de Enrutamiento:**\n"
        "1.  **Analiza el prefijo del mensaje:** El mensaje del usuario vendrá con un prefijo que indica su rol.\n"
        "2.  **Si el mensaje empieza con 'Publico:':** Delega la tarea completa al sub-agente `PublicAgent`. No intentes responder tú mismo.\n"
        "3.  **Si el mensaje empieza con 'Analista:':** Delega la tarea completa al sub-agente `AnalyticsAgent`. No intentes responder tú mismo.\n"
        "4.  **Si el mensaje NO tiene prefijo:** Asume que es un usuario público y delega la tarea al sub-agente `PublicAgent` por defecto.\n"
        "**IMPORTANTE:** Tu única acción es delegar. No proceses el contenido de la pregunta. Simplemente pásala al especialista adecuado."
    ),
    sub_agents=[
        PublicAgent,
        AnalyticsAgent
    ]
)