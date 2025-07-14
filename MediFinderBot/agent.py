from .tools.prompts import AGENT_DESCRIPTION, AGENT_INSTRUCTION
from google.adk.agents import Agent
from dotenv import load_dotenv

from .tools import query_tools

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# -- Modelo a usar --
MODEL = "gemini-2.0-flash"

# --- Definición del Agente Público (Para Usuarios Finales) ---
root_agent = Agent(
    name="MediFinderPublicAgent",
    model=MODEL,
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTION,
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
