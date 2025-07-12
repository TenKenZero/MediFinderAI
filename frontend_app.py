import requests
import json
import uuid
from flask import Flask, render_template_string, request, jsonify

# --- Configuración ---
ADK_API_URL = "http://localhost:8000"
APP_NAME = "MediFinderAgent" # Nombre de la carpeta del agente

# --- Inicialización de la Aplicación Flask ---
app = Flask(__name__)

USER_ID = f"user_{uuid.uuid4().hex[:8]}"
SESSION_ID = f"session_{uuid.uuid4().hex[:8]}"

def create_adk_session():
    """Crea una nueva sesión con el agente en la API del ADK."""
    session_url = f"{ADK_API_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(session_url, headers=headers, data=json.dumps({}))
        if response.status_code == 200 or response.status_code == 409:
            print(f"Sesión {SESSION_ID} lista para el usuario {USER_ID}.")
            return True
        else:
            print(f"Error al crear la sesión: {response.status_code} {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"Error de conexión: No se pudo conectar a la API del ADK en {ADK_API_URL}.")
        print("Asegúrate de que el comando 'adk api_server MediFinder' se está ejecutando.")
        return False

@app.route('/')
def index():
    """Renderiza la página principal del chatbot con un diseño mejorado y selector de rol."""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MediFinder Agent</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-color: #00756a;
                --user-msg-bg: #00756a;
                --bot-msg-bg: #f0f4f8;
                --bg-color: #f8f9fa;
                --text-color: #343a40;
                --tool-bg: #e6f4f1;
                --tool-border: #b2dfdb;
            }
            body { 
                font-family: 'Inter', sans-serif; 
                background-color: var(--bg-color); 
                color: var(--text-color);
                margin: 0; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh;
            }
            #chat-container { 
                width: 95%; 
                max-width: 800px; 
                height: 95vh; 
                background: white; 
                border-radius: 16px; 
                box-shadow: 0 8px 30px rgba(0,0,0,0.12); 
                display: flex; 
                flex-direction: column; 
                overflow: hidden;
            }
            #chat-header {
                background: var(--primary-color);
                color: white;
                padding: 15px 20px;
                font-weight: 600;
                font-size: 1.1em;
                display: flex;
                align-items: center;
            }
            #chat-header svg {
                width: 30px;
                height: 30px;
                margin-right: 12px;
            }
            #chat-box { 
                flex-grow: 1; 
                padding: 20px; 
                overflow-y: auto; 
            }
            .message { 
                display: flex;
                flex-direction: column;
                margin-bottom: 20px; 
                max-width: 80%;
                animation: fadeIn 0.5s ease-in-out;
            }
            .message-content {
                padding: 12px 18px; 
                border-radius: 20px; 
                line-height: 1.6;
                white-space: pre-wrap;
            }
            .user-message { 
                align-self: flex-end; 
                align-items: flex-end;
            }
            .user-message .message-content {
                background-color: var(--user-msg-bg); 
                color: white; 
                border-bottom-right-radius: 5px;
            }
            .bot-message { 
                align-self: flex-start; 
                align-items: flex-start;
            }
            .bot-message .message-content {
                background-color: var(--bot-msg-bg); 
                color: var(--text-color); 
                border-bottom-left-radius: 5px;
            }
            .tool-call { 
                background-color: var(--tool-bg); 
                border: 1px solid var(--tool-border); 
                margin-top: 12px; 
                padding: 12px; 
                border-radius: 12px; 
                font-family: 'SF Mono', 'Courier New', monospace; 
                font-size: 0.8em; 
                white-space: pre-wrap; 
                word-wrap: break-word;
                max-width: 100%;
            }
            .tool-call hr { border: 0; border-top: 1px solid var(--tool-border); margin: 10px 0; }
            #input-area { 
                display: flex; 
                align-items: center;
                padding: 15px;
                border-top: 1px solid #e9ecef;
                gap: 10px;
            }
            #role-selector {
                padding: 12px;
                border: 1px solid #ced4da;
                border-radius: 20px;
                background-color: white;
                font-family: 'Inter', sans-serif;
                font-size: 15px;
                cursor: pointer;
            }
            #user-input { 
                flex-grow: 1; 
                border: 1px solid #ced4da; 
                border-radius: 20px; 
                padding: 12px 18px; 
                font-size: 16px; 
                transition: border-color 0.2s;
            }
            #user-input:focus, #role-selector:focus {
                outline: none;
                border-color: var(--primary-color);
            }
            #send-button { 
                background-color: var(--primary-color); 
                border: none; 
                border-radius: 50%; 
                width: 48px;
                height: 48px;
                cursor: pointer; 
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background-color 0.2s;
                flex-shrink: 0;
            }
            #send-button:hover { background-color: #005a50; }
            #send-button svg { fill: white; width: 24px; height: 24px; }
            .typing-indicator {
                display: none;
                align-items: center;
                padding: 10px 20px;
            }
            .typing-indicator span {
                height: 8px; width: 8px; margin: 0 2px; background-color: #ced4da;
                border-radius: 50%; display: inline-block;
                animation: bounce 1.4s infinite ease-in-out both;
            }
            .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
            .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
            @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        </style>
    </head>
    <body>
        <div id="chat-container">
            <div id="chat-header">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M21.99 4c0-1.1-.89-2-1.99-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18zM17 11h-4v4h-2v-4H7V9h4V5h2v4h4v2z"/></svg>
                <span>Agente MediFinder</span>
            </div>
            <div id="chat-box">
                <div class="message bot-message"><div class="message-content">Hola, soy MediFinder. Selecciona tu rol y hazme una pregunta.</div></div>
            </div>
            <div class="typing-indicator" id="typing-indicator">
                <span></span><span></span><span></span>
            </div>
            <div id="input-area">
                <select id="role-selector">
                    <option value="Publico" selected>Público</option>
                    <option value="Analista">Analista</option>
                </select>
                <input type="text" id="user-input" placeholder="Ej: ¿Dónde encuentro amoxicilina en Tumbes?">
                <button id="send-button" title="Enviar">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </button>
            </div>
        </div>
        <script>
            const sendButton = document.getElementById('send-button');
            const userInput = document.getElementById('user-input');
            const chatBox = document.getElementById('chat-box');
            const typingIndicator = document.getElementById('typing-indicator');
            const roleSelector = document.getElementById('role-selector');

            sendButton.addEventListener('click', sendMessage);
            userInput.addEventListener('keypress', (e) => e.key === 'Enter' && sendMessage());

            function sendMessage() {
                const userText = userInput.value.trim();
                if (userText === '') return;

                const role = roleSelector.value;
                const prefixedMessage = `${role}: ${userText}`;

                // Muestra el mensaje original del usuario en la UI, sin el prefijo.
                appendMessage(userText, 'user');
                userInput.value = '';
                typingIndicator.style.display = 'flex';

                fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    // Envía el mensaje con el prefijo al backend.
                    body: JSON.stringify({ message: prefixedMessage })
                })
                .then(response => response.json())
                .then(data => {
                    typingIndicator.style.display = 'none';
                    appendMessage(data.response, 'bot', data.tool_calls);
                })
                .catch(error => {
                    typingIndicator.style.display = 'none';
                    appendMessage('Lo siento, ocurrió un error al contactar al agente.', 'bot');
                    console.error('Error:', error);
                });
            }

            function appendMessage(text, sender, toolCalls = []) {
                const messageWrapper = document.createElement('div');
                messageWrapper.className = 'message ' + (sender === 'user' ? 'user-message' : 'bot-message');
                
                const messageContent = document.createElement('div');
                messageContent.className = 'message-content';
                messageContent.textContent = text;
                messageWrapper.appendChild(messageContent);

                if (toolCalls.length > 0) {
                    const toolDiv = document.createElement('div');
                    toolDiv.className = 'tool-call';
                    toolDiv.innerHTML = '<strong>Análisis del Agente:</strong><br><br>' + toolCalls.join('<br><hr><br>');
                    messageWrapper.appendChild(toolDiv);
                }
                
                chatBox.appendChild(messageWrapper);
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        </script>
    </body>
    </html>
    """)

@app.route('/chat', methods=['POST'])
def chat():
    """Maneja la lógica de la conversación con la API del ADK."""
    # Recibe el mensaje ya prefijado desde el frontend.
    user_message_with_prefix = request.json['message']
    
    payload = {
        "app_name": APP_NAME,
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "new_message": {
            "role": "user",
            "parts": [{"text": user_message_with_prefix}]
        }
    }
    
    run_url = f"{ADK_API_URL}/run"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(run_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        events = response.json()
        
        final_response = "No he podido procesar tu solicitud. Inténtalo de nuevo."
        tool_calls_info = []

        for event in events:
            content = event.get('content', {})
            parts = content.get('parts', [{}])
            
            if 'functionCall' in parts[0]:
                call = parts[0]['functionCall']
                tool_calls_info.append(f"<b>Paso 1: Decido usar una herramienta</b><br>🤖 Herramienta: <code>{call['name']}</code><br>📋 Argumentos: <code>{json.dumps(call['args'])}</code>")
            
            if 'functionResponse' in parts[0]:
                resp = parts[0]['functionResponse']
                response_data = json.dumps(resp.get('response', {}), ensure_ascii=False)
                if len(response_data) > 350:
                    response_data = response_data[:350] + '...'
                tool_calls_info.append(f"<b>Paso 2: Analizo el resultado de la herramienta</b><br>🔍 Resultado: <code>{response_data}</code>")

            if 'text' in parts[0] and content.get('role') == 'model':
                final_response = parts[0]['text']

        return jsonify({'response': final_response, 'tool_calls': tool_calls_info})

    except requests.exceptions.RequestException as e:
        print(f"Error al llamar a la API del ADK: {e}")
        return jsonify({'response': f"Error al contactar al agente: {e}", 'tool_calls': []}), 500

if __name__ == '__main__':
    if create_adk_session():
        app.run(debug=True, port=5000)
    else:
        print("No se pudo iniciar el servidor del frontend porque la sesión del ADK no pudo ser creada.")
