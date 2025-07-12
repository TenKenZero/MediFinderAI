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
        "5.  **El mensaje del usuario podría empezar por el nombre de su rol 'Publico: ' o 'Analista: '. Simplemente ignora esta parte y responde a la consulta del usuario.\n"
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
