from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import google.generativeai as genai
import os

app = Flask(__name__)

# Configurar Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Configurar Twilio (opcional, solo si quieres enviar mensajes activos)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')

# Diccionario para guardar historial de conversaciones
conversaciones = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    # Obtener el mensaje entrante
    mensaje_entrante = request.values.get('Body', '').strip()
    numero_remitente = request.values.get('From', '')
    
    # Crear respuesta
    resp = MessagingResponse()
    
    # Verificar si el mensaje empieza con !bot
    if mensaje_entrante.startswith('!bot'):
        # Extraer la pregunta (quitar el !bot)
        pregunta = mensaje_entrante[4:].strip()
        
        if not pregunta:
            resp.message("@bot Por favor, escribe algo después de !bot. Ejemplo: !bot ¿Qué es Python?")
            return str(resp)
        
        try:
            # Obtener o crear historial de conversación
            if numero_remitente not in conversaciones:
                conversaciones[numero_remitente] = model.start_chat(history=[])
            
            chat = conversaciones[numero_remitente]
            
            # Enviar pregunta a Gemini
            respuesta_gemini = chat.send_message(pregunta)
            
            # Formatear respuesta con @bot al inicio
            mensaje_respuesta = f"@bot {respuesta_gemini.text}"
            
            # Limitar la longitud del mensaje (WhatsApp tiene límite de 1600 caracteres)
            if len(mensaje_respuesta) > 1500:
                mensaje_respuesta = mensaje_respuesta[:1500] + "...\n\n(Respuesta cortada por longitud)"
            
            resp.message(mensaje_respuesta)
            
        except Exception as e:
            resp.message(f"@bot ❌ Error: {str(e)}")
    
    return str(resp)

@app.route('/health', methods=['GET'])
def health():
    return "Bot funcionando correctamente ✅", 200

@app.route('/', methods=['GET'])
def home():
    return """
    <h1>WhatsApp Gemini Bot</h1>
    <p>El bot está activo y esperando mensajes.</p>
    <p>Usa: <code>!bot tu pregunta aquí</code></p>
    """, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
