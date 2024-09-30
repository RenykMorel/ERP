from flask import Flask, render_template, jsonify, request, render_template_string
import requests
import json
import logging
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración básica de logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AsistenteVirtual:
    def __init__(self, api_key, app, activo=True):
        self.api_key = api_key
        self.app = app
        self.activo = activo
        self.context = "Eres un asistente virtual para CalculAI. Debes responder preguntas basándote en la información proporcionada en el contexto y la pregunta del usuario."

    def responder(self, pregunta):
        if not self.activo:
            return "El asistente no está activo. Por favor, contacte al equipo de CalculAI para su activación."

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        data = {
            "model": "claude-2.1",
            "messages": [
                {"role": "user", "content": f"{self.context}\n\nPregunta del usuario: {pregunta}"}
            ],
            "max_tokens": 300
        }

        try:
            logger.debug(f"Enviando solicitud a la API de Claude. API Key: {self.api_key[:5]}...")
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Respuesta recibida de la API de Claude")
            return response.json()["content"][0]["text"]
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP al obtener respuesta de Claude: {str(e)}")
            logger.error(f"Respuesta de error: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al obtener respuesta de Claude: {str(e)}")
            raise

def create_app():
    app = Flask(__name__)
    
    # Obtener la API key desde las variables de entorno
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    if not CLAUDE_API_KEY:
        raise ValueError("La API key de Claude no está configurada en el archivo .env")
    
    ASISTENTE_ACTIVO = True
    
    asistente = AsistenteVirtual(CLAUDE_API_KEY, app, activo=ASISTENTE_ACTIVO)

    @app.route('/api/asistente', methods=['POST'])
    def consultar_asistente():
        logger.debug("Solicitud al asistente recibida.")
        
        pregunta = request.json.get('pregunta', '').strip()
        logger.debug(f"Pregunta recibida: {pregunta}")
        if not pregunta:
            return jsonify({"respuesta": "Por favor, proporciona una pregunta."}), 400
        
        try:
            respuesta = asistente.responder(pregunta)
            logger.info(f"Respuesta del asistente obtenida. Longitud: {len(respuesta)}")
            return jsonify({"respuesta": respuesta})
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP al consultar el asistente: {str(e)}")
            return jsonify({"respuesta": "Error al comunicarse con el asistente. Por favor, inténtalo de nuevo más tarde."}), 500
        except Exception as e:
            logger.error(f"Error inesperado al consultar el asistente: {str(e)}")
            return jsonify({"respuesta": "Ha ocurrido un error inesperado. Por favor, inténtalo de nuevo más tarde."}), 500

    @app.route('/')
    def index():
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Prueba Asistente CalculAI</title>
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        </head>
        <body>
            <h1>Prueba del Asistente CalculAI</h1>
            <input type="text" id="pregunta" placeholder="Escribe tu pregunta aquí">
            <button onclick="consultarAsistente()">Enviar</button>
            <div id="respuesta"></div>

            <script>
            function consultarAsistente() {
                var pregunta = $('#pregunta').val();
                $.ajax({
                    url: '/api/asistente',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({pregunta: pregunta}),
                    success: function(response) {
                        $('#respuesta').text(response.respuesta);
                    },
                    error: function(error) {
                        console.error('Error:', error);
                        $('#respuesta').text('Error al consultar al asistente');
                    }
                });
            }
            </script>
        </body>
        </html>
        """)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)