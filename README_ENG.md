# MediFinder Intelligent Agent with Google ADK

![MIT License](https://img.shields.io/badge/License-MIT-green.svg)

**MediFinder** is an intelligent agent system built with the **Google Agent Development Kit (ADK)**. Its goal is to democratize access to information about the availability of medicines in Peru's public health network, using data from the Ministry of Health.

This project was developed as a case study for the talk **"Developing RAG Agents with the Google Agent SDK: Implementing the Medifinder project"** at the **Google I/O Extended - GDG Piura 2025** event.

---

### Prototype Demo

This is the prototype's user interface, where a user can interact with the agent by selecting a role (Public or Analyst) to make specific queries. The interface also shows the agent's "reasoning" by visualizing the tools it uses.

![MediFinder User Interface](https://i.imgur.com/xLg6nZc.png)

---

## 🚀 Project Purpose

In many healthcare systems, an information asymmetry exists that makes it difficult for citizens to know where to find the medicines they need. MediFinder addresses this problem by providing a conversational interface that allows two types of users to obtain valuable real-time information:

1.  **General Public:** They can make queries like "Where can I find Amoxicillin in Tumbes?" to quickly locate health centers with available stock.
2.  **Health Managers (Analysts):** They can perform analytical queries for decision-making, such as "What is the most consumed medicine in Piura?" or "Generate a low-stock report for Lima."

---

## 🛠️ Tech Stack

* **Agent Framework:** Google Agent Development Kit (ADK) for Python
* **Language Model (LLM):** Google Gemini 1.5 Flash
* **Backend and Tools:** Python 3
* **Database:** PostgreSQL
* **API Server (ADK):** Uvicorn/FastAPI (managed by `adk api_server`)
* **Frontend (Prototype):** Flask, HTML, CSS, JavaScript

---

## 🏛️ Evolutionary Architecture

The project is structured to demonstrate the evolution from a simple bot to a complex multi-agent system.

### Phase 1: `agent - Bot.py` (Simple RAG Agent)

* **Pattern:** Retrieval-Augmented Generation (RAG).
* **Description:** A single agent that answers user questions by querying a set of tools connected to the database.

### Phase 2: `agent.py` (Multi-Agent System with Dispatcher)

* **Pattern:** Coordinator/Dispatcher.
* **Description:** An LLM-based `root_agent` acts as an intelligent dispatcher. It analyzes the user's request and, based on a prefix (`Publico:` or `Analista:`), delegates the task to the appropriate specialized sub-agent (`PublicAgent` or `AnalyticsAgent`).

### Phase 3: `agent - Watcher.py` (Proactive Workflow - Experimental)

* **Pattern:** Hierarchical and Sequential Orchestration.
* **Description:** A `MasterOrchestratorAgent` (whose logic is in Python, not an LLM) executes a complex workflow:
    1.  Gets a list of all regions.
    2.  Starts a loop to iterate over each region.
    3.  Inside the loop, it calls sub-agents to analyze each region, generate reports, and decide whether an analyst should be notified.

---

## ⚙️ Setup and Execution

Follow these steps to run the project in your local environment.

### Prerequisites

* Python 3.8+
* PostgreSQL installed and running.
* A database created (you can use the `database-creation-sql.sql` script).

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/MediFinder.git](https://github.com/your-username/MediFinder.git)
    cd MediFinder
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    * Create a `.env` file in the project's root directory.
    * Add your database credentials:
        ```env
        DB_HOST=localhost
        DB_PORT=5432
        DB_NAME=medifinder
        DB_USER=your_postgres_user
        DB_PASS=your_postgres_password
        ```

### Running the Application

To run the application, you need two terminals.

1.  **Terminal 1: Start the Agent API Server**
    * *Note for Windows:* You may need to run this terminal as **Administrator** to avoid permission errors (`WinError 1314`).
    * Make sure you are in the project's root directory (`GADK` or similar).
    ```bash
    # This command serves the root agent defined in MediFinder/agent.py
    adk api_server MediFinder
    ```
    You should see a message indicating the Uvicorn server is running on `http://localhost:8000`.

2.  **Terminal 2: Start the Flask Frontend**
    ```bash
    # From the project's root directory
    python frontend_app.py
    ```
    You should see a message indicating the Flask server is running on `http://localhost:5000`.

3.  **Open your browser:**
    * Go to `http://127.0.0.1:5000` to interact with the application.

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

## 👨‍💻 Author

* **Lenin Carrasco** - [leningeniero@gmail.com](mailto:leningeniero@gmail.com)