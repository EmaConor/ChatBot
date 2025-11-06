# ChatBot con registro e inicio de sesión en WhatsApp
from flask import Flask, jsonify, request
import DataBases.DataBaseController as DB
import requests
import re

app = Flask(__name__)

# === CONFIGURACIÓN ===
TOKEN = "EAApdsnrt0rUBP6SK65wClfiC0sc567779pr5mZBLuy7zFQHd2vqmyLXVtp9PqhLLj8Iq0399bV2mMZArS9KKZCjZCNsECtOiqILIEpo9qGKhgr3tP4P2rmSMFH2T4jc6l1ZALNiAkPzsq3uDd9sjJhxhGtfC0ksuBH7Y2hA5GrMjZBRoZCC5PQM33oor3sXZBycwiAalnKU7QjAH7dRKF5cfjEYmc2kOOnqfikYOrxYsZB44jotxBkgLTq3jkStcbkf5zbR1ExZAXyopAEast2UMZC0"
PHONE_NUMBER_ID = "863285753529334"

# === BASE DE DATOS TEMPORAL DE USUARIOS ===
USUARIOS = {}  # {telefono: {"etapa": "pidiendo_nombre", "nombre": "", "direccion": "", "cedula": ""}}
LOGIN_ATTEMPTS = {}  # {telefono: intentos}

# === FUNCIÓN DE REGISTRO ===
def agregar_cliente(nombre, tel, direccion, cedula):
    try:
        DB.agregar_cliente(nombre, tel, direccion, cedula)
        print(f"🟢 Cliente registrado:\nNombre: {nombre}\nTeléfono: {tel}\nDirección: {direccion}\nCédula: {cedula}")
        return True
    except Exception as e:
        print(f"🔴 Error al registrar cliente: {e}")
        return False

# === FUNCIÓN DE INICIO DE SESIÓN MEJORADA ===
def iniciar_sesion(tel, cedula):
    try:
        cliente = DB.iniciar_sesion(tel, cedula)
        if cliente:
            print(f"🟢 Inicio de sesión exitoso para: {tel}")
            return True, "¡Inicio de sesión exitoso! 🎉"
        else:
            print(f"🔴 Fallo en inicio de sesión para: {tel}")
            return False, "❌ Credenciales incorrectas. Verifica tu número y cédula."
    except Exception as e:
        print(f"🔴 Error en inicio de sesión: {e}")
        return False, "❌ Error del sistema. Intenta más tarde."

# === VALIDACIÓN DE CÉDULA ===
def validar_cedula(cedula):
    # Validación básica - puedes ajustar según tu país
    if not cedula.isdigit():
        return False
    if len(cedula) < 6 or len(cedula) > 12:
        return False
    return True

# === ENVIAR MENSAJE DE TEXTO ===
def enviar_mensaje(numero, texto):
    try:
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "text",
            "text": {"body": texto}
        }
        response = requests.post(url, headers=headers, json=data)
        print(f"→ Enviado a {numero}: {texto}")
        return response.status_code == 200
    except Exception as e:
        print(f"🔴 Error enviando mensaje: {e}")
        return False

# === ENVIAR MENÚ PRINCIPAL ===
def enviar_menu(numero):
    try:
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": "👋 Bienvenido"},
                "body": {"text": "Por favor selecciona una opción del menú:"},
                "footer": {"text": "ChatBot - Sistema de Autenticación"},
                "action": {
                    "button": "Ver opciones",
                    "sections": [
                        {
                            "title": "Menú principal",
                            "rows": [
                                {"id": "1", "title": "🔐 Iniciar sesión", "description": "Accede a tu cuenta existente"},
                                {"id": "2", "title": "📝 Registrarse", "description": "Crea una nueva cuenta"},
                                {"id": "3", "title": "🍽️ Ver menú", "description": "Consulta nuestros productos"},
                                {"id": "4", "title": "ℹ️ Información", "description": "Conoce más sobre nosotros"}
                            ]
                        }
                    ]
                }
            }
        }
        response = requests.post(url, headers=headers, json=data)
        print(f"→ Menú enviado a {numero}")
        return response.status_code == 200
    except Exception as e:
        print(f"🔴 Error enviando menú: {e}")
        return False

# === ENVIAR MENSAJE DE BIENVENIDA AL LOGUEARSE ===
def enviar_bienvenida_logueado(numero, nombre_usuario=None):
    mensaje = "🎉 *¡Bienvenido de nuevo!*\n\n"
    if nombre_usuario:
        mensaje += f"👋 Hola *{nombre_usuario}*\n\n"
    
    mensaje += "✅ *Sesión iniciada correctamente*\n\n"
    mensaje += "Ahora puedes:\n"
    mensaje += "• 📋 Ver tu perfil\n"
    mensaje += "• 🍽️ Hacer pedidos\n"
    mensaje += "• 📊 Ver historial\n"
    mensaje += "• ⚙️ Configurar preferencias\n\n"
    mensaje += "Escribe *menu* en cualquier momento para ver las opciones."
    
    enviar_mensaje(numero, mensaje)

# === WEBHOOK PRINCIPAL ===
@app.route("/webhook/", methods=["POST", "GET"])
def webhook_whatsapp():
    if request.method == "GET":
        if request.args.get('hub.verify_token') == "HolaNovato":
            return request.args.get('hub.challenge')
        return "Token inválido"

    data = request.get_json()

    # Extraer datos del mensaje
    try:
        telefono = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
        mensaje = ""
        tipo = data['entry'][0]['changes'][0]['value']['messages'][0]['type']
        
        if tipo == "text":
            mensaje = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'].strip().lower()
        elif tipo == "interactive":
            mensaje = data['entry'][0]['changes'][0]['value']['messages'][0]['interactive']['list_reply']['id']
    except KeyError:
        return jsonify({"status": "no message"}), 200

    print(f"📱 Mensaje de {telefono}: {mensaje}")

    # === MANEJO DE INICIO DE SESIÓN ===
    if telefono in USUARIOS and USUARIOS[telefono]["etapa"] == "iniciando_sesion":
        cedula = mensaje
        
        # Validar cédula
        if not validar_cedula(cedula):
            enviar_mensaje(telefono, "❌ Formato de cédula inválido. Por favor ingresa solo números.")
            return jsonify({"status": "invalid cedula"}), 200
        
        # Intentar inicio de sesión
        success, mensaje_respuesta = iniciar_sesion(telefono, cedula)
        
        if success:
            enviar_bienvenida_logueado(telefono)
            # Limpiar estado
            del USUARIOS[telefono]
            if telefono in LOGIN_ATTEMPTS:
                del LOGIN_ATTEMPTS[telefono]
        else:
            # Contar intentos fallidos
            if telefono not in LOGIN_ATTEMPTS:
                LOGIN_ATTEMPTS[telefono] = 0
            LOGIN_ATTEMPTS[telefono] += 1
            
            if LOGIN_ATTEMPTS[telefono] >= 3:
                enviar_mensaje(telefono, "🔒 Demasiados intentos fallidos. Por seguridad, el inicio de sesión ha sido bloqueado temporalmente.")
                del USUARIOS[telefono]
                del LOGIN_ATTEMPTS[telefono]
                enviar_menu(telefono)
            else:
                enviar_mensaje(telefono, f"{mensaje_respuesta}\n\nIntento {LOGIN_ATTEMPTS[telefono]}/3\n\nPor favor ingresa tu cédula nuevamente:")
        
        return jsonify({"status": "login processed"}), 200

    # === ETAPAS DEL REGISTRO ===
    if telefono in USUARIOS and USUARIOS[telefono]["etapa"] in ["pidiendo_nombre", "pidiendo_direccion", "pidiendo_cedula"]:
        etapa = USUARIOS[telefono]["etapa"]

        if etapa == "pidiendo_nombre":
            if len(mensaje) < 2:
                enviar_mensaje(telefono, "❌ El nombre debe tener al menos 2 caracteres. Por favor ingresa tu nombre completo:")
                return jsonify({"status": "invalid name"}), 200
            
            USUARIOS[telefono]["nombre"] = mensaje.title()
            USUARIOS[telefono]["etapa"] = "pidiendo_direccion"
            enviar_mensaje(telefono, "📍 Ingresa tu dirección completa:")
            return jsonify({"status": "ask direccion"}), 200

        elif etapa == "pidiendo_direccion":
            if len(mensaje) < 5:
                enviar_mensaje(telefono, "❌ La dirección parece muy corta. Por favor ingresa una dirección válida:")
                return jsonify({"status": "invalid address"}), 200
            
            USUARIOS[telefono]["direccion"] = mensaje
            USUARIOS[telefono]["etapa"] = "pidiendo_cedula"
            enviar_mensaje(telefono, "🆔 Ingresa tu número de cédula (solo números):")
            return jsonify({"status": "ask cedula"}), 200

        elif etapa == "pidiendo_cedula":
            if not validar_cedula(mensaje):
                enviar_mensaje(telefono, "❌ Cédula inválida. Por favor ingresa solo números (6-12 dígitos):")
                return jsonify({"status": "invalid cedula"}), 200
            
            USUARIOS[telefono]["cedula"] = mensaje
            nombre = USUARIOS[telefono]["nombre"]
            direccion = USUARIOS[telefono]["direccion"]
            cedula = USUARIOS[telefono]["cedula"]
            tel = telefono
            
            if agregar_cliente(nombre, tel, direccion, cedula):
                mensaje_exito = f"""✅ *¡Registro completado!*

📋 Nombre: {nombre}
📞 Teléfono: {tel}
🏠 Dirección: {direccion}
🆔 Cédula: {cedula}

¡Bienvenido a nuestro sistema! 🎉"""
                enviar_mensaje(telefono, mensaje_exito)
            else:
                enviar_mensaje(telefono, "❌ Error al completar el registro. Por favor intenta nuevamente.")
            
            del USUARIOS[telefono]
            return jsonify({"status": "registro completo"}), 200

    # === MENSAJE DE BIENVENIDA ===
    if mensaje in ["hola", "hi", "hello", "menú", "menu", "opciones"]:
        enviar_menu(telefono)
        return jsonify({"status": "menu"}), 200

    # === OPCIONES DEL MENÚ ===
    if mensaje == "1":  # Iniciar sesión
        enviar_mensaje(telefono, "🔐 *Inicio de Sesión*\n\nPor favor ingresa tu *número de cédula* para continuar:")
        USUARIOS[telefono] = {"etapa": "iniciando_sesion"}
        return jsonify({"status": "login started"}), 200

    elif mensaje == "2":  # Registrarse
        enviar_mensaje(telefono, "📝 *Registro de Nuevo Usuario*\n\nPor favor escribe tu *nombre completo*:")
        USUARIOS[telefono] = {"etapa": "pidiendo_nombre"}
        return jsonify({"status": "registro inicio"}), 200

    elif mensaje == "3":  # Ver menú
        enviar_mensaje(telefono, "🍽️ *Nuestro Menú*\n\n🔸 Pizza Margarita - $12\n🔸 Pizza Pepperoni - $14\n🔸 Lasagna - $10\n🔸 Ensalada César - $8\n\nPróximamente podrás hacer pedidos directamente.")
        return jsonify({"status": "ver menu"}), 200

    elif mensaje == "4":  # Información
        enviar_mensaje(telefono, "ℹ️ *Información*\n\nSomos un restaurante familiar con más de 10 años de experiencia. Usa este chatbot para registrarte, iniciar sesión y pronto hacer pedidos.\n\n📍 Dirección: Calle Principal #123\n📞 Teléfono: +1-234-567-8900\n🕒 Horario: 9AM - 10PM")
        return jsonify({"status": "info"}), 200

    # === FALLBACK ===
    enviar_mensaje(telefono, "🤖 No entendí tu mensaje. Escribe *hola* o *menu* para ver las opciones disponibles.")
    return jsonify({"status": "fallback"}), 200

# === INICIAR FLASK ===
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)