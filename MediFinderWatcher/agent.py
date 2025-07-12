from typing import AsyncGenerator
from google.adk.agents import Agent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from dotenv import load_dotenv

from .tools import query_tools
from .tools import analytics_tools

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# -- Modelo a usar --
MODEL = "gemini-2.0-flash"

# =================================================================
#  1. AGENTES ESPECIALISTAS (TRABAJADORES)
# =================================================================

# Agente 1: Obtiene la lista de todas las regiones.
RegionFetcherAgent = Agent(
    name="RegionFetcher",
    model=MODEL,
    description="Obtiene una lista de todas las regiones de la base de datos.",
    instruction="Llama a la herramienta 'list_all_regions' para obtener la lista completa de regiones. Guarda el resultado en la clave de estado 'region_list'.",
    tools=[query_tools.list_all_regions],
    output_key="region_list"
)

# Agente 2: Analiza una única región.
RegionAnalyzerAgent = Agent(
    name="RegionAnalyzer",
    model=MODEL,
    description="Para una región dada, encuentra la medicina más consumida y luego genera un reporte de bajo stock para esa medicina.",
    instruction=(
        "Recibirás un nombre de región en la clave de estado 'current_region'.\n"
        "Paso 1: Usa la herramienta 'find_most_consumed_medicine_by_region' con la región actual para encontrar la medicina más consumida. Guarda el nombre de la medicina en la clave de estado 'top_medicine'.\n"
        "Paso 2: Usa la herramienta 'generate_low_stock_report' con la región actual y la medicina de la clave 'top_medicine' para obtener el reporte de stock. Guarda este reporte en la clave 'stock_report'."
    ),
    tools=[
        analytics_tools.find_most_consumed_medicine_by_region,
        analytics_tools.generate_low_stock_report
    ]
)

# Agente 3: Decide si notificar y actúa.
NotificationAgent = Agent(
    name="NotificationAgent",
    model=MODEL,
    description="Analiza un reporte de stock y decide si enviar una notificación por correo.",
    instruction=(
        "Recibirás un reporte de stock en la clave de estado 'stock_report'.\n"
        "Si el reporte contiene datos (es decir, no está vacío y el status es 'success'), entonces hay un problema de stock.\n"
        "En ese caso, llama a la herramienta 'send_notification_email' con los siguientes argumentos:\n"
        "- recipient_email: 'analista.salud@minsa.gob.pe'\n"
        "- subject: 'Alerta de Bajo Stock para [nombre_medicina] en [nombre_region]'\n"
        "- body: Un resumen del reporte de stock que recibiste.\n"
        "Si el reporte no contiene datos (status 'no_issues_found'), no hagas nada."
    ),
    tools=[analytics_tools.send_notification_email]
)

# =================================================================
#  2. AGENTE ORQUESTADOR (EL JEFE DE PROYECTO)
# =================================================================

class MasterOrchestratorAgent(BaseAgent):
    """
    Este agente personalizado no usa un LLM. Su lógica está escrita en Python
    para controlar un flujo de trabajo complejo: obtener una lista, y luego
    iterar sobre ella, llamando a otros agentes para cada ítem.
    """
    name: str = "MasterOrchestrator"
    description: str = "Orquesta el flujo de análisis de stock para todas las regiones."

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        
        yield Event(author=self.name, content_parts=["Iniciando flujo de trabajo de análisis de stock..."])

        # --- PASO 1: Obtener todas las regiones ---
        fetcher = self.find_agent("RegionFetcher")
        async for event in fetcher.run_async(ctx):
            yield event # Pasamos los eventos del sub-agente para ver su progreso

        region_list_result = ctx.session.state.get("region_list", {})
        regions = region_list_result.get("regions", [])

        if not regions:
            yield Event(author=self.name, content_parts=["No se encontraron regiones. Finalizando flujo."])
            return

        yield Event(author=self.name, content_parts=[f"Se encontraron {len(regions)} regiones. Iniciando análisis para cada una..."])

        # --- PASO 2: Iterar sobre cada región y procesarla ---
        for region in regions:
            yield Event(author=self.name, content_parts=[f"--- Procesando Región: {region} ---"])
            
            # Guardamos la región actual en el estado para que los sub-agentes la usen
            ctx.session.state["current_region"] = region

            # a) Analizar la región para encontrar la medicina y su stock
            analyzer = self.find_agent("RegionAnalyzer")
            async for event in analyzer.run_async(ctx):
                yield event

            # b) Decidir si notificar basado en el análisis
            notifier = self.find_agent("NotificationAgent")
            async for event in notifier.run_async(ctx):
                yield event

        yield Event(author=self.name, content_parts=["\nFlujo de trabajo de análisis completado para todas las regiones."])


# =================================================================
#  3. AGENTE RAÍZ (PUNTO DE ENTRADA)
# =================================================================

# Creamos el agente raíz y le asignamos los especialistas como sub-agentes.
# Esto le permite al orquestador encontrarlos y llamarlos por su nombre.
root_agent = MasterOrchestratorAgent(
    sub_agents=[
        RegionFetcherAgent,
        RegionAnalyzerAgent,
        NotificationAgent
    ]
)

# Definimos 'agent' para que 'adk api_server' sepa qué servir.
#agent = root_agent
