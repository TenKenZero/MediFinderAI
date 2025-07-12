# Agente Inteligente MediFinder con Google ADK

![Licencia MIT](https://img.shields.io/badge/License-MIT-green.svg)

**MediFinder** es un sistema de agente inteligente construido con el **Google Agent Development Kit (ADK)**. Su objetivo es democratizar el acceso a la información sobre la disponibilidad de medicamentos en la red de salud pública de Perú, utilizando datos del Ministerio de Salud.

Este proyecto fue desarrollado como caso de estudio para la ponencia **"Desarrollo de Agentes RAG con Google Agent SDK: Implementación del proyecto Medifinder"** en el evento **Google I/O Extended - GDG Piura 2025**.

---

### Demo del Prototipo

Así luce la interfaz de usuario del prototipo, donde un usuario puede interactuar con el agente, seleccionando un rol (Público o Analista) para realizar consultas específicas. La interfaz también muestra el "razonamiento" del agente al visualizar las herramientas que utiliza.

![Interfaz de Usuario de MediFinder](https://i.imgur.com/xLg6nZc.png)

---

## 🚀 Propósito del Proyecto

En muchos sistemas de salud, existe una asimetría de información que dificulta a los ciudadanos saber dónde encontrar los medicamentos que necesitan. MediFinder aborda este problema proporcionando una interfaz conversacional que permite a dos tipos de usuarios obtener información valiosa en tiempo real:

1.  **Público General:** Pueden realizar consultas como "¿Dónde encuentro Amoxicilina en Tumbes?" para localizar rápidamente los centros de salud con stock disponible.
2.  **Gestores de Salud (Analistas):** Pueden realizar consultas analíticas para la toma de decisiones, como "¿Cuál es la medicina más consumida en Piura?" o "Genérame un reporte de bajo stock para Lima".

---

## 🛠️ Pila Tecnológica

* **Framework de Agente:** Google Agent Development Kit (ADK) para Python
* **Modelo de Lenguaje (LLM):** Google Gemini 1.5 Flash
* **Backend y Herramientas:** Python 3
* **Base de Datos:** PostgreSQL
* **Servidor de API (ADK):** Uvicorn/FastAPI (gestionado por `adk api_server`)
* **Frontend (Prototipo):** Flask, HTML, CSS, JavaScript

---

## 🏛️ Arquitectura Evolutiva

El proyecto está estructurado para demostrar la evolución de un simple bot a un sistema multi-agente complejo.

### Fase 1: `agent - Bot.py` (Agente RAG Simple)

* **Patrón:** Retrieval-Augmented Generation (RAG).
* **Descripción:** Un único agente que responde a las preguntas del usuario consultando un conjunto de herramientas conectadas a la base de datos.

### Fase 2: `agent.py` (Sistema Multi-Agente con Despachador)

* **Patrón:** Coordinador/Despachador.
* **Descripción:** Un `root_agent` (agente raíz) basado en LLM actúa como un despachador inteligente. Analiza la solicitud del usuario y, basándose en un prefijo (`Publico:` o `Analista:`), delega la tarea al sub-agente especialista adecuado (`PublicAgent` o `AnalyticsAgent`).

### Fase 3: `agent - Watcher.py` (Flujo de Trabajo Proactivo - Experimental)

* **Patrón:** Orquestación Jerárquica y Secuencial.
* **Descripción:** Un `MasterOrchestratorAgent` (cuya lógica está en Python, no en un LLM) ejecuta un flujo de trabajo complejo:
    1.  Obtiene una lista de todas las regiones.
    2.  Inicia un bucle para iterar sobre cada región.
    3.  Dentro del bucle, llama a sub-agentes para analizar cada región, generar reportes y decidir si se debe notificar a un analista.

---

## ⚙️ Configuración y Ejecución

Sigue estos pasos para ejecutar el proyecto en tu entorno local.

### Prerrequisitos

* Python 3.8+
* PostgreSQL instalado y corriendo.
* Una base de datos creada (puedes usar el script `database-creation-sql.sql`).

### Pasos de Instalación

1.  **Clona el repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/MediFinder.git](https://github.com/tu-usuario/MediFinder.git)
    cd MediFinder
    ```

2.  **Crea y activa un entorno virtual:**
    ```bash
    python -m venv venv
    # En Windows
    .\venv\Scripts\activate
    # En macOS/Linux
    source venv/bin/activate
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura las variables de entorno:**
    * Crea un archivo `.env` en el directorio raíz del proyecto.
    * Añade las credenciales de tu base de datos:
        ```env
        DB_HOST=localhost
        DB_PORT=5432
        DB_NAME=medifinder
        DB_USER=tu_usuario_postgres
        DB_PASS=tu_contraseña_postgres
        ```

### Ejecución

Para correr la aplicación, necesitas dos terminales.

1.  **Terminal 1: Inicia el Servidor de la API del Agente**
    * *Nota para Windows:* Puede que necesites ejecutar esta terminal como **Administrador** para evitar errores de permisos (`WinError 1314`).
    * Asegúrate de estar en el directorio raíz del proyecto (`GADK` o similar).
    ```bash
    # Este comando sirve el agente raíz definido en MediFinder/agent.py
    adk api_server MediFinder
    ```
    Deberías ver un mensaje indicando que el servidor Uvicorn está corriendo en `http://localhost:8000`.

2.  **Terminal 2: Inicia el Frontend con Flask**
    ```bash
    # Desde el directorio raíz del proyecto
    python frontend_app.py
    ```
    Deberías ver un mensaje indicando que el servidor de Flask está corriendo en `http://localhost:5000`.

3.  **Abre tu navegador:**
    * Ve a `http://127.0.0.1:5000` para interactuar con la aplicación.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

## 👨‍💻 Autor

* **Lenin Carrasco** - [leningeniero@gmail.com](mailto:leningeniero@gmail.com)