# ChatBot inteligente con WhatsApp en Python
from flask import Flask, jsonify, request
import requests  # para enviar mensajes a la API de WhatsApp

app = Flask(__name__)

# Token y número de teléfono (ajusta con los tuyos)
TOKEN = "EAApdsnrt0rUBP1ZArDPgSKn8WWAZApJviUtBnBJwjJIceBaTBHkm5NZAkUI1Nf5ZALj9ZCGwAC97QVgOjNuQ1qVtkZBj2CxZBtsDvSn03D77cQZBwmtC8GZADVOYLNNayhjSzk2HhkyzdhSa5HilNyCPzcXmUPgdryuQFQNhE8udRatoCIc84geHPDylvqdPG2iZAF5sWjdOBbeFORzypBRByrNz2iCw1Rclxm4Qb0XjVpu00LVXNkNLZB0WiHuZCZAzrfnJ8TimAcsoJRF0J8nmvQ6FVBAZDZD"
PHONE_NUMBER_ID = "863285753529334"

# CUANDO RECIBAMOS LAS PETICIONES EN ESTA RUTA
@app.route("/webhook/", methods=["POST", "GET"])
def webhook_whatsapp():
    # SI HAY DATOS RECIBIDOS VIA GET (para verificación inicial)
    if request.method == "GET":
        if request.args.get('hub.verify_token') == "HolaNovato":
            return request.args.get('hub.challenge')
        else:
            return "Error de autentificación."

    # SI RECIBIMOS UN MENSAJE
    data = request.get_json()
    try:
        mensaje = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'].lower()
        telefonoCliente = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
    except KeyError:
        return jsonify({"status": "no message"}), 200

    # Guardamos el mensaje recibido en un archivo de texto
    with open("texto.txt", "w") as f:
        f.write(mensaje)

    # Si el mensaje contiene "hola", respondemos con "hola"
    if "hola" in mensaje:
        enviar_mensaje(telefonoCliente, "Hola 👋")

    return jsonify({"status": "success"}), 200


# Función para enviar mensajes a WhatsApp
def enviar_mensaje(numero, texto):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, headers=headers, json=data)


# INICIAMOS FLASK
if __name__ == "__main__":
    app.run(debug=True, port=5000)