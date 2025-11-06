# ChatBot inteligente con WhatsApp en Python
from flask import Flask, jsonify, request
import requests  # para enviar mensajes a la API de WhatsApp
import json

app = Flask(__name__)

# Token y número de teléfono (ajusta con los tuyos)
TOKEN = "EAApdsnrt0rUBP4hDyvp5KJEUQWIP7Xh8ZCwpQ1r72wPyPoCQtA93a8XKYZBa5h7kFa64cUUqtzZCdH7oAoHqpCJXPxMjEfCSjjcKPfmQZAosX3Yr4DNQTjIKs7OsZAWq6ovwBaTjkVT37QdEVcQQMkfiKKpNcJIYzQZCoZAcoFMhF0NB4uR3TIdBy6qOouZB4ID0rYsvGOadXTjIVqG1ok7Pf8cew0IhzvzPHDuc4Or6ecEkRGYkZBWzSFDKtjCroSRGcgoXi8ZBk06BEONCa0qt2ilwZDZD"
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
        # Manejar diferentes tipos de mensajes
        if 'messages' in data['entry'][0]['changes'][0]['value']:
            mensaje_data = data['entry'][0]['changes'][0]['value']['messages'][0]
            
            # Si es un mensaje de texto normal
            if 'text' in mensaje_data:
                mensaje = mensaje_data['text']['body'].lower()
                telefonoCliente = mensaje_data['from']
                
                # Guardamos el mensaje recibido en un archivo de texto
                with open("texto.txt", "w") as f:
                    f.write(mensaje)

                # Lógica de respuestas
                if "hola" in mensaje:
                    enviar_menu_principal(telefonoCliente)
                elif "menu" in mensaje or "opciones" in mensaje:
                    enviar_menu_principal(telefonoCliente)
                elif "ayuda" in mensaje:
                    enviar_mensaje(telefonoCliente, "Escribe 'menu' para ver las opciones disponibles 📋")
                else:
                    enviar_menu_principal(telefonoCliente)
            
            # Si es una interacción con un menú
            elif 'interactive' in mensaje_data:
                interactive_data = mensaje_data['interactive']
                telefonoCliente = mensaje_data['from']
                
                if interactive_data['type'] == 'list_reply':
                    # Usuario seleccionó una opción de lista
                    opcion_seleccionada = interactive_data['list_reply']['id']
                    manejar_opcion_menu(telefonoCliente, opcion_seleccionada)
                
                elif interactive_data['type'] == 'button_reply':
                    # Usuario presionó un botón
                    opcion_seleccionada = interactive_data['button_reply']['id']
                    manejar_opcion_menu(telefonoCliente, opcion_seleccionada)
                    
    except KeyError as e:
        print(f"Error procesando mensaje: {e}")
        return jsonify({"status": "no message"}), 200

    return jsonify({"status": "success"}), 200

def enviar_menu_principal(numero):
    """Envía el menú principal con opciones tipo selectbox"""
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "🏪 MI NEGOCIO"
            },
            "body": {
                "text": "¡Hola! 👋 ¿En qué puedo ayudarte? Selecciona una opción:"
            },
            "footer": {
                "text": "Estamos para servirte"
            },
            "action": {
                "button": "Ver Opciones",
                "sections": [
                    {
                        "title": "Servicios Disponibles",
                        "rows": [
                            {
                                "id": "opcion1",
                                "title": "📋 Productos",
                                "description": "Ver nuestro catálogo"
                            },
                            {
                                "id": "opcion2",
                                "title": "💰 Precios",
                                "description": "Consultar precios"
                            },
                            {
                                "id": "opcion3",
                                "title": "🚚 Pedidos",
                                "description": "Realizar un pedido"
                            }
                        ]
                    },
                    {
                        "title": "Información",
                        "rows": [
                            {
                                "id": "opcion4",
                                "title": "🏠 Sucursales",
                                "description": "Ubicaciones y horarios"
                            },
                            {
                                "id": "opcion5",
                                "title": "📞 Contacto",
                                "description": "Hablar con un asesor"
                            },
                            {
                                "id": "opcion6",
                                "title": "ℹ️ Ayuda",
                                "description": "Preguntas frecuentes"
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

def enviar_menu_productos(numero):
    """Envía submenú de productos"""
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "📋 CATÁLOGO"
            },
            "body": {
                "text": "Selecciona una categoría de productos:"
            },
            "action": {
                "button": "Categorías",
                "sections": [
                    {
                        "title": "Nuestros Productos",
                        "rows": [
                            {
                                "id": "categoria1",
                                "title": "🖥️ Electrónicos",
                                "description": "Tecnología y gadgets"
                            },
                            {
                                "id": "categoria2",
                                "title": "👕 Ropa",
                                "description": "Moda y accesorios"
                            },
                            {
                                "id": "categoria3",
                                "title": "🏠 Hogar",
                                "description": "Artículos para el hogar"
                            },
                            {
                                "id": "categoria4",
                                "title": "🔙 Volver",
                                "description": "Menú principal"
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    requests.post(url, headers=headers, json=data)

def enviar_botones_rapidos(numero):
    """Envía botones rápidos para acciones comunes"""
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "¿Qué te gustaría hacer?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "btn_si",
                            "title": "✅ Sí"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "btn_no",
                            "title": "❌ No"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "btn_info",
                            "title": "📋 Más Info"
                        }
                    }
                ]
            }
        }
    }
    
    requests.post(url, headers=headers, json=data)

def manejar_opcion_menu(numero, opcion):
    """Maneja las opciones seleccionadas por el usuario"""
    respuestas = {
        "opcion1": "📦 Tenemos una gran variedad de productos. Déjame mostrarte nuestras categorías...",
        "opcion2": "💰 Todos nuestros precios incluyen IVA. ¿Te interesa algún producto en específico?",
        "opcion3": "🚚 Para realizar pedidos necesitamos: nombre, dirección y producto deseado.",
        "opcion4": "🏠 Contamos con 3 sucursales. Horario: Lunes a Viernes 9am-6pm, Sábados 9am-2pm",
        "opcion5": "📞 Puedes contactarnos al: 555-123-4567 o escribirnos aquí mismo.",
        "opcion6": "ℹ️ Preguntas frecuentes: Envíos 24-48hrs, Garantía 30 días, Pagos: Tarjeta/Efectivo",
        "categoria1": "🖥️ Electrónicos: Laptops, smartphones, tablets, accesorios. Precios desde $500",
        "categoria2": "👕 Ropa: Ropa casual, formal, deportiva. Tallas S-XXL",
        "categoria3": "🏠 Hogar: Muebles, decoración, electrodomésticos. Envío gratis en compras >$1000",
        "categoria4": "🔙 Volviendo al menú principal...",
        "btn_si": "¡Perfecto! ¿En qué más puedo ayudarte?",
        "btn_no": "Entendido, si cambias de idea aquí estaré.",
        "btn_info": "Somos una empresa con 10 años de experiencia. Calidad garantizada ✅"
    }
    
    mensaje_respuesta = respuestas.get(opcion, "Opción no reconocida. Escribe 'menu' para ver las opciones.")
    enviar_mensaje(numero, mensaje_respuesta)
    
    # Si seleccionó productos, enviar submenú
    if opcion == "opcion1":
        enviar_menu_productos(numero)
    # Si volvió del submenú, mostrar menú principal
    elif opcion == "categoria4":
        enviar_menu_principal(numero)
    # Para opciones que requieren más interacción
    elif opcion in ["btn_si", "btn_info"]:
        enviar_botones_rapidos(numero)

# Función para enviar mensajes simples a WhatsApp
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
    response = requests.post(url, headers=headers, json=data)
    print(f"Mensaje enviado: {response.status_code}")

# INICIAMOS FLASK
if __name__ == "__main__":
    app.run(debug=True, port=5000)