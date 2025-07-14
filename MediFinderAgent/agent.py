from google.adk.agents import Agent
from dotenv import load_dotenv

from .tools import query_tools
from .tools import analytics_tools

# Importar Prompts desde el archivo de prompts
from .tools.prompts import (
    PUBLIC_AGENT_DESC, PUBLIC_AGENT_INST,
    ANALYTICS_AGENT_DESC, ANALYTICS_AGENT_INST,
    ROOT_AGENT_DESC, ROOT_AGENT_INST
)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# -- Modelo a usar --
MODEL = "gemini-2.0-flash"

# --- Definición del Agente Público (Para Usuarios Finales) ---

PublicAgent = Agent(
    name="MediFinderPublicAgent",
    model=MODEL,
    description=PUBLIC_AGENT_DESC,
    instruction=PUBLIC_AGENT_INST,
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
    description=ANALYTICS_AGENT_DESC,
    instruction=ANALYTICS_AGENT_INST,
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
    description=ROOT_AGENT_DESC,
    instruction=ROOT_AGENT_INST,
    sub_agents=[
        PublicAgent,
        AnalyticsAgent
    ]
)