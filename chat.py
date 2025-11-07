# ChatBot con registro e inicio de sesión en WhatsApp
from flask import Flask, jsonify, request
import DataBases.DataBaseController as DB
import requests
import re

app = Flask(__name__)

# === CONFIGURACIÓN ===
TOKEN = "EAApdsnrt0rUBP45WWo8wwVZCIaPcM3iN4M3tuiprRtPgANA7fWm4uZCb909t8MCFh3kbo4Y16fSZBWeZC0dClw3enMUc8nAXUBBBwJrZCeNTlmWJaobHDwINQhACfmQGYCC63dpW5ylSkAEwdKOEFTxAKIXwSUMEQYZBxMhVroF45r54NUbLYWuLnT0Fdx1a5qFaEHr30l9ff87ddxvZCLj9u4eYbOWUnYw9OA1EijGySIorPa0ge35P4kOgBVNKdH3T6vRv2wxODcbx5qbK3eauAZDZD"
PHONE_NUMBER_ID = "863285753529334"

# === BASE DE DATOS TEMPORAL DE USUARIOS ===
USUARIOS = {}  # {telefono: {"etapa": "pidiendo_nombre", "nombre": "", "direccion": "", "cedula": ""}}
LOGIN_ATTEMPTS = {}  # {telefono: intentos}
SESIONES_ACTIVAS = {}  # {telefono: {"id_usuario": id, "cedula": cedula, "nombre": nombre}}

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
            # Obtener información completa del cliente
            cliente_completo = DB.buscar_cliente(tel)
            if cliente_completo:
                print(f"🟢 Inicio de sesión exitoso para: {tel}")
                return True, "¡Inicio de sesión exitoso! 🎉", cliente_completo
            else:
                return False, "❌ Error al obtener información del usuario.", None
        else:
            print(f"🔴 Fallo en inicio de sesión para: {tel}")
            return False, "❌ Credenciales incorrectas. Verifica tu número y cédula.", None
    except Exception as e:
        print(f"🔴 Error en inicio de sesión: {e}")
        return False, "❌ Error del sistema. Intenta más tarde.", None

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

# === ENVIAR MENÚ DE USUARIO LOGUEADO ===
def enviar_menu_logueado(numero, nombre_usuario=None):
    try:
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
        
        saludo = f"👋 Hola {nombre_usuario}" if nombre_usuario else "👋 Hola"
        
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": "🎉 ¡Sesión Activa!"},
                "body": {"text": f"{saludo}\n\nSelecciona una opción:"},
                "footer": {"text": "Sesión iniciada - ChatBot"},
                "action": {
                    "button": "Opciones",
                    "sections": [
                        {
                            "title": "Menú de Usuario",
                            "rows": [
                                {"id": "cerrar_sesion", "title": "🚪 Cerrar sesión", "description": "Salir de tu cuenta"},
                                {"id": "actualizar_datos", "title": "✏️ Actualizar datos", "description": "Modificar tu información"},
                                {"id": "menu_principal", "title": "🏠 Menú principal", "description": "Volver al menú inicial"},
                                {"id": "informacion", "title": "ℹ️ Mi información", "description": "Ver tus datos personales"}
                            ]
                        }
                    ]
                }
            }
        }
        response = requests.post(url, headers=headers, json=data)
        print(f"→ Menú logueado enviado a {numero}")
        return response.status_code == 200
    except Exception as e:
        print(f"🔴 Error enviando menú logueado: {e}")
        return False

# === ENVIAR MENSAJE DE BIENVENIDA AL LOGUEARSE ===
def enviar_bienvenida_logueado(numero, nombre_usuario=None):
    mensaje = "🎉 *¡Bienvenido de nuevo!*\n\n"
    if nombre_usuario:
        mensaje += f"👋 Hola *{nombre_usuario}*\n\n"
    
    mensaje += "✅ *Sesión iniciada correctamente*\n\n"
    mensaje += "Ahora puedes acceder a funciones exclusivas:\n"
    mensaje += "• 📋 Ver y actualizar tu perfil\n"
    mensaje += "• 🍽️ Hacer pedidos (próximamente)\n"
    mensaje += "• 📊 Ver historial (próximamente)\n"
    mensaje += "• ⚙️ Gestionar tu cuenta\n\n"
    mensaje += "Usa el menú interactivo para navegar."
    
    enviar_mensaje(numero, mensaje)
    # Enviar menú de usuario logueado después del mensaje de bienvenida
    enviar_menu_logueado(numero, nombre_usuario)

# === ACTUALIZAR DATOS DEL USUARIO ===
def actualizar_datos_usuario(telefono, nuevos_datos):
    try:
        if telefono not in SESIONES_ACTIVAS:
            return False, "❌ No hay sesión activa."
        
        sesion = SESIONES_ACTIVAS[telefono]
        id_usuario = sesion["id_usuario"]
        cedula = sesion["cedula"]
        
        # Actualizar en la base de datos
        success = DB.actualizar_cliente(id_usuario, cedula, nuevos_datos)
        
        if success:
            # Actualizar sesión local si el nombre fue modificado
            if "nombre" in nuevos_datos:
                SESIONES_ACTIVAS[telefono]["nombre"] = nuevos_datos["nombre"]
            return True, "✅ Datos actualizados correctamente."
        else:
            return False, "❌ Error al actualizar los datos."
            
    except Exception as e:
        print(f"🔴 Error actualizando datos: {e}")
        return False, "❌ Error del sistema al actualizar."

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

    # === MANEJO DE USUARIOS LOGUEADOS ===
    if telefono in SESIONES_ACTIVAS:
        if mensaje in ["cerrar_sesion", "5"]:
            nombre_usuario = SESIONES_ACTIVAS[telefono]["nombre"]
            del SESIONES_ACTIVAS[telefono]
            enviar_mensaje(telefono, f"👋 *Hasta pronto, {nombre_usuario}!*\n\nTu sesión ha sido cerrada correctamente.")
            enviar_menu(telefono)
            return jsonify({"status": "sesion cerrada"}), 200

        elif mensaje in ["actualizar_datos", "6"]:
            enviar_mensaje(telefono, "✏️ *Actualizar Datos*\n\nPor favor ingresa los nuevos datos en el formato:\n\n*Nombre:Nuevo nombre\nDirección:Nueva dirección*\n\nEjemplo:\nNombre:Juan Pérez\nDirección:Calle 123 #45-67")
            USUARIOS[telefono] = {"etapa": "actualizando_datos"}
            return jsonify({"status": "actualizando datos"}), 200

        elif mensaje in ["menu_principal", "7"]:
            enviar_menu(telefono)
            return jsonify({"status": "menu principal"}), 200

        elif mensaje in ["informacion", "8"]:
            sesion = SESIONES_ACTIVAS[telefono]
            info_msg = f"📋 *Tu Información*\n\n"
            info_msg += f"👤 *Nombre:* {sesion['nombre']}\n"
            info_msg += f"📞 *Teléfono:* {telefono}\n"
            info_msg += f"🆔 *ID de usuario:* {sesion['id_usuario']}\n"
            info_msg += f"📝 *Cédula:* {sesion['cedula']}\n\n"
            info_msg += "Para actualizar tus datos, selecciona 'Actualizar datos' en el menú."
            enviar_mensaje(telefono, info_msg)
            return jsonify({"status": "informacion mostrada"}), 200

        else:
            # Si el usuario está logueado pero envía otro mensaje, mostrar menú logueado
            enviar_menu_logueado(telefono, SESIONES_ACTIVAS[telefono]["nombre"])
            return jsonify({"status": "menu logueado"}), 200

    # === MANEJO DE ACTUALIZACIÓN DE DATOS ===
    if telefono in USUARIOS and USUARIOS[telefono]["etapa"] == "actualizando_datos":
        # Procesar actualización de datos
        lineas = mensaje.split('\n')
        nuevos_datos = {}
        
        for linea in lineas:
            if ':' in linea:
                clave, valor = linea.split(':', 1)
                clave = clave.strip().lower()
                valor = valor.strip()
                
                if clave == "nombre" and len(valor) >= 2:
                    nuevos_datos["nombre"] = valor.title()
                elif clave == "dirección" or clave == "direccion":
                    if len(valor) >= 5:
                        nuevos_datos["direccion"] = valor
                    else:
                        enviar_mensaje(telefono, "❌ La dirección debe tener al menos 5 caracteres.")
                        return jsonify({"status": "direccion invalida"}), 200
        
        if nuevos_datos:
            success, mensaje_respuesta = actualizar_datos_usuario(telefono, nuevos_datos)
            enviar_mensaje(telefono, mensaje_respuesta)
            
            if success:
                # Actualizar el nombre en la sesión si fue modificado
                if "nombre" in nuevos_datos:
                    SESIONES_ACTIVAS[telefono]["nombre"] = nuevos_datos["nombre"]
        else:
            enviar_mensaje(telefono, "❌ No se proporcionaron datos válidos para actualizar.")
        
        del USUARIOS[telefono]
        enviar_menu_logueado(telefono, SESIONES_ACTIVAS[telefono]["nombre"])
        return jsonify({"status": "actualizacion procesada"}), 200

    # === MANEJO DE INICIO DE SESIÓN ===
    if telefono in USUARIOS and USUARIOS[telefono]["etapa"] == "iniciando_sesion":
        cedula = mensaje
        
        # Validar cédula
        if not validar_cedula(cedula):
            enviar_mensaje(telefono, "❌ Formato de cédula inválido. Por favor ingresa solo números.")
            return jsonify({"status": "invalid cedula"}), 200
        
        # Intentar inicio de sesión
        success, mensaje_respuesta, cliente = iniciar_sesion(telefono, cedula)
        
        if success and cliente:
            # Guardar sesión activa con ID y cédula
            SESIONES_ACTIVAS[telefono] = {
                "id_usuario": cliente["id"],
                "cedula": cedula,
                "nombre": cliente["nombre"]
            }
            enviar_bienvenida_logueado(telefono, cliente["nombre"])
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