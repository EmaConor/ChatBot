# ChatBot con menús interactivos (select box) en WhatsApp
from flask import Flask, jsonify, request, redirect
import DataBases.ClientesController as BDC
import DataBases.productsController as DBP
import requests
import re
import html
import time
from datetime import datetime, time as dt_time
import pytz

app = Flask(__name__)

# === CONFIGURACIÓN ===
TOKEN = "EAApdsnrt0rUBP4eO8SdYVeiZB2QrJLDuxdwSA0IZBJECWTaZCN3ClZAbWd6LBWr1Hzgd5A4QZBX2k19w1CucuL8Gz5afchNyrpLIfFS7NUEmxgBttEXWQqW6QSmlYHEJA4GFbZBBot5b04GWZCkpcgcN4s59Pa5AeDlbzs5ZBpFE1JopuqwCD91ameSKOMUUVovjd3wAJ5ZCruhrZBNfSuZC75MR7BgQKASsCwL8U6usJA3ZCVEboSfYnVFgxEk9ytRpwBc4m3kovvrE4oQJSZCOvc1ei"
PHONE_NUMBER_ID = "863285753529334"

# === BASE DE DATOS TEMPORAL ===
USUARIOS = {}
LOGIN_ATTEMPTS = {}
SESIONES_ACTIVAS = {}

# === RUTAS BÁSICAS ===
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 ChatBot WhatsApp Interactivo - Mezón Peruano</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #25D366; }
            .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .feature { background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 ChatBot WhatsApp Interactivo - Mezón Peruano</h1>
            
            <div class="status">
                <strong>✅ Servidor funcionando con menús interactivos</strong>
                <p>Hora del servidor: """ + time.strftime("%Y-%m-%d %H:%M:%S") + """</p>
            </div>
            
            <div class="feature">
                <h3>✨ Características Interactivas:</h3>
                <ul>
                    <li>📋 Menús con botones de selección (Select Box)</li>
                    <li>🎯 Navegación intuitiva con listas interactivas</li>
                    <li>🔐 Registro e inicio de sesión interactivo</li>
                    <li>⚙️ Gestión de sesiones con menús dinámicos</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/status')
def status():
    return jsonify({
        "status": "active",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "interactive_menus": "enabled",
        "statistics": {
            "users_in_registration": len(USUARIOS),
            "active_sessions": len(SESIONES_ACTIVAS),
            "login_attempts_tracking": len(LOGIN_ATTEMPTS)
        }
    })

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "whatsapp-interactive-chatbot"})

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/webhook')
def webhook_redirect():
    return redirect('/webhook/', code=301)

# === CONFIGURACIÓN DE HORARIO ===
HORARIO_APERTURA = dt_time(11, 0)   # 11:00 AM
HORARIO_CIERRE = dt_time(21, 0)    # 9:00 PM
ZONA_HORARIA = pytz.timezone('America/Bogota')

def esta_en_horario_servicio():
    """Verifica si el chatbot está en horario de servicio"""
    ahora = datetime.now(ZONA_HORARIA)
    hora_actual = ahora.time()
    return HORARIO_APERTURA <= hora_actual <= HORARIO_CIERRE

def enviar_mensaje_fuera_horario(numero):
    """Envía mensaje cuando está fuera del horario de atención"""
    mensaje = """🚫 *Fuera del Horario de Atención*

🕒 *Horario de Atención:*
📅 Lunes a Domingo
⏰ 11:00 AM - 9:00 PM

Actualmente no estamos en horario de servicio. 
Nuestro equipo te atenderá tan pronto como volvamos.

¡Gracias por tu comprensión! 🙏"""
    return enviar_mensaje(numero, mensaje)

# === FUNCIONES DE VALIDACIÓN ===
def sanitizar_texto(texto):
    texto = html.escape(texto)
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)
    return texto[:100]

def validar_cedula(cedula):
    if not cedula.isdigit():
        return False
    if 6 <= len(cedula) <= 10:
        return True
    return False

def limpiar_estado_usuario(telefono):
    if telefono in USUARIOS:
        del USUARIOS[telefono]
    if telefono in LOGIN_ATTEMPTS:
        del LOGIN_ATTEMPTS[telefono]

def usuario_ya_registrado(telefono):
    try:
        cliente = BDC.buscar_cliente(telefono)
        return cliente is not None
    except Exception as e:
        print(f"🔴 Error verificando usuario: {e}")
        return False

def agregar_cliente(nombre, tel, direccion, cedula):
    try:
        if usuario_ya_registrado(tel):
            return False, 'El usuario ya está registrado'
        BDC.agregar_cliente(nombre, tel, direccion, cedula)
        print(f"🟢 Cliente registrado: {nombre} - {tel}")
        return True, 'Registro exitoso'
    except Exception as e:
        print(f"🔴 Error al registrar cliente: {e}")
        return False, f'Error al registrar: {str(e)}'

def iniciar_sesion(tel, cedula):
    try:
        cliente = BDC.iniciar_sesion(tel, cedula)
        if cliente:
            cliente_completo = BDC.buscar_cliente(tel)
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

# === FUNCIONES PARA MENÚS INTERACTIVOS ===
def enviar_mensaje(numero, texto):
    """Envía mensaje de texto simple"""
    try:
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
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            print(f"→ Mensaje enviado a {numero}")
            return True
        else:
            print(f"🔴 Error API WhatsApp: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"🔴 Error enviando mensaje: {e}")
        return False

def enviar_menu_interactivo(numero, titulo_boton, texto_cuerpo, secciones):
    """Envía un menú interactivo con lista de opciones"""
    try:
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": "🇵🇪 Mezón Peruano"
                },
                "body": {
                    "text": texto_cuerpo
                },
                "footer": {
                    "text": "Selecciona una opción del menú"
                },
                "action": {
                    "button": titulo_boton,
                    "sections": secciones
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"→ Menú interactivo enviado a {numero}")
            return True
        else:
            print(f"🔴 Error enviando menú: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"🔴 Error en enviar_menu_interactivo: {e}")
        return False

def enviar_menu_principal(numero):
    """Menú principal con opciones de login, registro, menú e información"""
    if numero in SESIONES_ACTIVAS:
        nombre = SESIONES_ACTIVAS[numero].get("nombre")
        enviar_menu_logueado(numero, nombre)
        return True
    
    secciones = [
        {
            "title": "🔐 Acceso",
            "rows": [
                {
                    "id": "iniciar_sesion",
                    "title": "Iniciar Sesión",
                    "description": "Accede con tu cuenta"
                },
                {
                    "id": "registrarse",
                    "title": "Registrarse",
                    "description": "Crea una nueva cuenta"
                }
            ]
        },
        {
            "title": "📱 Servicios",
            "rows": [
                {
                    "id": "ver_menu",
                    "title": "Ver Menú",
                    "description": "Consulta nuestros productos"
                },
                {
                    "id": "informacion",
                    "title": "Información",
                    "description": "Sobre nosotros"
                }
            ]
        }
    ]
    
    return enviar_menu_interactivo(
        numero,
        "📋 Ver Opciones",
        "👋 ¡Bienvenid@ a Mezón Peruano!\n\nSelecciona una opción para continuar:",
        secciones
    )

def enviar_menu_logueado(numero, nombre_usuario=None):
    """Menú para usuarios con sesión activa"""
    saludo = f"👋 Hola {nombre_usuario}" if nombre_usuario else "👋 Hola"
    
    secciones = [
        {
            "title": "🍽️ Servicios",
            "rows": [
                {
                    "id": "ver_menu",
                    "title": "Ver Menú",
                    "description": "Consulta nuestros productos"
                },
                {
                    "id": "informacion",
                    "title": "Información",
                    "description": "Sobre nosotros"
                }
            ]
        },
        {
            "title": "👤 Mi Cuenta",
            "rows": [
                {
                    "id": "mi_informacion",
                    "title": "Mi Información",
                    "description": "Ver mis datos personales"
                },
                {
                    "id": "actualizar_datos",
                    "title": "Actualizar Datos",
                    "description": "Modificar mi información"
                },
                {
                    "id": "cerrar_sesion",
                    "title": "Cerrar Sesión",
                    "description": "Salir de mi cuenta"
                }
            ]
        }
    ]
    
    return enviar_menu_interactivo(
        numero,
        "⚙️ Opciones",
        f"{saludo} - *Sesión Activa* 🎉\n\n¿Qué deseas hacer?",
        secciones
    )

def enviar_menu_actualizacion(numero):
    """Menú para seleccionar qué dato actualizar"""
    secciones = [
        {
            "title": "¿Qué deseas actualizar?",
            "rows": [
                {
                    "id": "actualizar_nombre",
                    "title": "Actualizar Nombre",
                    "description": "Cambiar tu nombre completo"
                },
                {
                    "id": "actualizar_direccion",
                    "title": "Actualizar Dirección",
                    "description": "Cambiar tu dirección"
                },
                {
                    "id": "actualizar_cedula",
                    "title": "Actualizar Cédula",
                    "description": "Cambiar tu número de cédula"
                }
            ]
        },
        {
            "title": "🔙 Navegación",
            "rows": [
                {
                    "id": "cancelar_actualizacion",
                    "title": "Cancelar",
                    "description": "Volver al menú anterior"
                }
            ]
        }
    ]
    
    return enviar_menu_interactivo(
        numero,
        "✏️ Seleccionar Campo",
        "📝 *Actualizar Datos Personales*\n\nSelecciona el campo que deseas modificar:",
        secciones
    )

def enviar_menu_productos(numero):
    """Menú de productos disponibles desde la base de datos"""
    try:
        productos = DBP.listar_productos()
        
        if not productos:
            enviar_mensaje(numero, "📭 No hay productos disponibles en este momento.")
            enviar_menu_principal(numero)
            return False
        
        categorias = {}
        for producto in productos:
            if producto.get("Disponible", 1) == 1:
                categoria = producto.get("categoria", "Otros")
                if categoria not in categorias:
                    categorias[categoria] = []
                
                descripcion = f"${producto.get('precio', 0):,}"
                if len(descripcion) > 70:
                    descripcion = descripcion[:67] + "..."
                
                categorias[categoria].append({
                    "id": f"producto_{producto.get('id', '')}",
                    "title": producto.get("nombre", "Producto"),
                    "description": descripcion
                })
        
        secciones = []
        
        for categoria, productos_cat in categorias.items():
            if productos_cat:
                secciones.append({
                    "title": f"🍽️ {categoria}",
                    "rows": productos_cat
                })
        
        secciones.append({
            "title": "🔙 Navegación",
            "rows": [
                {
                    "id": "volver_menu",
                    "title": "Volver al Menú",
                    "description": "Regresar al menú principal"
                }
            ]
        })
        
        return enviar_menu_interactivo(
            numero,
            "🍽️ Ver Productos",
            "📋 *Menú Disponible - Mezón Peruano* 🇵🇪\n\nSelecciona un producto para más información:",
            secciones
        )
        
    except Exception as e:
        print(f"🔴 Error obteniendo productos: {e}")
        enviar_mensaje(numero, "❌ Error al cargar el menú. Intenta más tarde.")
        enviar_menu_principal(numero)
        return False

def enviar_menu_pdf(numero):
    """Envía el menú en formato PDF al usuario"""
    try:
        # URL del PDF del menú (debes reemplazar esto con tu URL real)
        url_pdf = "https://menu.emaconor.site/menu.pdf"
        
        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "document",
            "document": {
                "link": url_pdf,
                "caption": "🍽️ *Menú Mezón Peruano* 🇵🇪\n\nNuestra carta completa con todos los platos y precios.",
                "filename": "menu-mezon-peruano.pdf"
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"→ PDF del menú enviado a {numero}")
            
            # Mensaje adicional después del PDF
            time.sleep(1)
            mensaje_adicional = """📋 *¿Necesitas ayuda para elegir?*

Conoce más detalles sobre algún plato o explora nuestras categorías en el menú interactivo.
Selecciona una opción a continuación:"""
            enviar_mensaje(numero, mensaje_adicional)
            
            return True
        else:
            print(f"🔴 Error enviando PDF: {response.status_code} - {response.text}")
            # Fallback: enviar menú interactivo si el PDF falla
            enviar_mensaje(numero, "❌ No pude cargar el menú PDF. Te muestro nuestras opciones:")
            
    except Exception as e:
        print(f"🔴 Error enviando PDF del menú: {e}")
        # Fallback a menú interactivo
        enviar_mensaje(numero, "❌ Error al cargar el menú PDF. Te muestro nuestras opciones:")

def enviar_detalle_producto(numero, producto_id):
    """Envía los detalles de un producto específico"""
    try:
        if producto_id.startswith("producto_"):
            id_num = producto_id.replace("producto_", "")
            try:
                id_num = int(id_num)
            except ValueError:
                enviar_mensaje(numero, "❌ Producto no encontrado.")
                enviar_menu_productos(numero)
                return
        
        producto = DBP.buscar_producto_por_id(id_num)
        
        if not producto:
            enviar_mensaje(numero, "❌ Producto no encontrado.")
            enviar_menu_productos(numero)
            return
        
        mensaje = f"🍽️ *{producto.get('nombre', 'Producto')}*\n\n"
        mensaje += f"📝 *Descripción:* {producto.get('descripcion', 'Sin descripción')}\n"
        mensaje += f"💰 *Precio:* ${producto.get('precio', 0):,}\n"
        mensaje += f"📂 *Categoría:* {producto.get('categoria', 'General')}\n"
        
        disponibilidad = producto.get("Disponible", 1)
        if disponibilidad == 1:
            mensaje += "✅ *Disponible*\n\n"
        else:
            mensaje += "❌ *No disponible*\n\n"
        
        mensaje += "¡Próximamente podrás hacer pedidos! 🚀"
        
        enviar_mensaje(numero, mensaje)
        
        time.sleep(1)
        enviar_menu_productos(numero)
        
    except Exception as e:
        print(f"🔴 Error mostrando detalle producto: {e}")
        enviar_mensaje(numero, "❌ Error al cargar información del producto.")
        enviar_menu_productos(numero)

# === WEBHOOK PRINCIPAL ===
@app.route("/webhook/", methods=["POST", "GET"])
def webhook_whatsapp():
    if request.method == "GET":
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        print(f"🔍 Verificación webhook - Token recibido: {verify_token}")
        
        if verify_token == "HolaNovato":
            print("✅ Token de verificación correcto")
            return challenge
        else:
            print(f"❌ Token incorrecto. Esperado: 'HolaNovato', Recibido: '{verify_token}'")
            return "Token inválido", 403

    try:
        data = request.get_json()
        try:
            telefono = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
            mensaje = ""
            tipo = data['entry'][0]['changes'][0]['value']['messages'][0]['type']
            
            if tipo == "text":
                mensaje = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'].strip().lower()
                mensaje = sanitizar_texto(mensaje)
            elif tipo == "interactive":
                mensaje = data['entry'][0]['changes'][0]['value']['messages'][0]['interactive']['list_reply']['id']
                print(f"🎯 Opción interactiva seleccionada: {mensaje}")
                
        except KeyError:
            return jsonify({"status": "no message"}), 200

        print(f"📱 Mensaje de {telefono}: {mensaje}")

        # === VERIFICACIÓN DE HORARIO DE ATENCIÓN ===
        if not esta_en_horario_servicio():
            print("⏰ Mensaje recibido fuera del horario de atención")
            enviar_mensaje_fuera_horario(telefono)
            return jsonify({"status": "fuera de horario"}), 200
        
        # === PRIMERO: Manejo de etapas activas (actualización, registro, login) ===
        if telefono in USUARIOS:
            etapa = USUARIOS[telefono].get("etapa")
            print(f"🔍 Usuario {telefono} en etapa: {etapa}")
            
            # === PROCESO DE ACTUALIZACIÓN DE DATOS ===
            if etapa == "actualizando_nombre":
                print("🔧 Procesando actualización de nombre...")
                if len(mensaje) < 2:
                    enviar_mensaje(telefono, "❌ El nombre debe tener al menos 2 caracteres.\n\nIngresa un nombre válido:")
                    return jsonify({"status": "invalid name"}), 200
    
                try:
                    # Obtener cédula del usuario para verificación
                    cedula_actual = SESIONES_ACTIVAS[telefono].get("cedula")
                    print(f"🔑 Verificando con cédula: {cedula_actual}")
        
                    # Actualizar en base de datos
                    print(f"🔄 Actualizando nombre a: {mensaje.title()}")
                    success = BDC.actualizar_nombre_cliente(str(telefono), mensaje.title(), str(cedula_actual))
        
                    if success:
                        SESIONES_ACTIVAS[telefono]["nombre"] = mensaje.title()
                        enviar_mensaje(telefono, f"✅ *Nombre actualizado correctamente*\n\nNuevo nombre: {mensaje.title()}")
                        del USUARIOS[telefono]
                        enviar_menu_logueado(telefono, mensaje.title())
                    else:
                        enviar_mensaje(telefono, "❌ Error al actualizar. Verifica tus datos.")
                        del USUARIOS[telefono]
                        nombre_anterior = SESIONES_ACTIVAS[telefono].get("nombre")
                        enviar_menu_logueado(telefono, nombre_anterior)
            
                except Exception as e:
                    print(f"🔴 Error actualizando nombre: {e}")
                    enviar_mensaje(telefono, "❌ Error al actualizar. Intenta nuevamente.")
                    del USUARIOS[telefono]
                
                return jsonify({"status": "nombre actualizado"}), 200
            
            elif etapa == "actualizando_direccion":
                print("🔧 Procesando actualización de dirección...")
                if len(mensaje) < 5:
                    enviar_mensaje(telefono, "❌ La dirección debe tener al menos 5 caracteres.\n\nIngresa una dirección válida:")
                    return jsonify({"status": "invalid address"}), 200
    
                try:
                    # Obtener cédula del usuario para verificación
                    cedula_actual = SESIONES_ACTIVAS[telefono].get("cedula")
                    print(f"🔑 Verificando con cédula: {cedula_actual}")
        
                    # Actualizar en base de datos
                    print(f"🔄 Actualizando dirección a: {mensaje}")
                    success = BDC.actualizar_direccion_cliente(telefono, mensaje, cedula_actual)
        
                    if success:
                        enviar_mensaje(telefono, f"✅ *Dirección actualizada correctamente*\n\nNueva dirección: {mensaje}")
                        del USUARIOS[telefono]
                        nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                        enviar_menu_logueado(telefono, nombre)
                    else:
                        enviar_mensaje(telefono, "❌ Error al actualizar. Verifica tus datos.")
                        del USUARIOS[telefono]
                        nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                        enviar_menu_logueado(telefono, nombre)
            
                except Exception as e:
                    print(f"🔴 Error actualizando dirección: {e}")
                    enviar_mensaje(telefono, "❌ Error al actualizar. Intenta nuevamente.")
                    del USUARIOS[telefono]
    
                return jsonify({"status": "direccion actualizada"}), 200
            
            elif etapa == "verificando_cedula_actual":
                print("🔧 Procesando verificación de cédula actual...")
                if not validar_cedula(mensaje):
                    enviar_mensaje(telefono, "❌ Cédula inválida. Debe tener entre 6 y 10 dígitos.\n\nIngresa tu cédula actual:")
                    return jsonify({"status": "invalid cedula"}), 200
    
                # Verificar que la cédula ingresada coincida con la almacenada
                try:
                    print(f"🔑 Verificando cédula: {mensaje}")
                    cedula_coincide = BDC.verificar_cedula_cliente(telefono, mensaje)
        
                    if cedula_coincide:
                        enviar_mensaje(telefono, "✅ *Verificación exitosa*\n\nAhora ingresa tu nueva cédula (6-10 dígitos):")
                        USUARIOS[telefono] = {"etapa": "actualizando_cedula"}
                    else:
                        enviar_mensaje(telefono, "❌ *Cédula incorrecta*\n\nLa cédula ingresada no coincide con tu cédula registrada.\n\nActualización cancelada por seguridad.")
                        del USUARIOS[telefono]
                        nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                        enviar_menu_logueado(telefono, nombre)
        
                except Exception as e:
                    print(f"🔴 Error verificando cédula: {e}")
                    enviar_mensaje(telefono, "❌ Error en verificación. Intenta más tarde.")
                    del USUARIOS[telefono]
    
                return jsonify({"status": "cedula verificada"}), 200
            
            elif etapa == "actualizando_cedula":
                print("🔧 Procesando actualización de cédula...")
                if not validar_cedula(mensaje):
                    enviar_mensaje(telefono, "❌ Cédula inválida. Debe tener entre 6 y 10 dígitos.\n\nIngresa una cédula válida:")
                    return jsonify({"status": "invalid cedula"}), 200
    
                try:
                    # Obtener cédula actual del usuario para verificación
                    cedula_actual = SESIONES_ACTIVAS[telefono].get("cedula")
                    print(f"🔑 Verificando con cédula actual: {cedula_actual}")
        
                    # Actualizar en base de datos
                    print(f"🔄 Actualizando cédula a: {mensaje}")
                    success = BDC.actualizar_cedula_cliente(str(telefono), mensaje, str(cedula_actual))
        
                    if success:
                        SESIONES_ACTIVAS[telefono]["cedula"] = mensaje
                        enviar_mensaje(telefono, f"✅ *Cédula actualizada correctamente*\n\nTu información ha sido actualizada de forma segura.")
                        del USUARIOS[telefono]
                        nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                        enviar_menu_logueado(telefono, nombre)
                    else:
                        enviar_mensaje(telefono, "❌ Error al actualizar. Verifica tus datos.")
                        del USUARIOS[telefono]
                        nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                        enviar_menu_logueado(telefono, nombre)
            
                except Exception as e:
                    print(f"🔴 Error actualizando cédula: {e}")
                    enviar_mensaje(telefono, "❌ Error al actualizar. Intenta nuevamente.")
                    del USUARIOS[telefono]
    
                return jsonify({"status": "cedula actualizada"}), 200
            
            # === PROCESO DE INICIO DE SESIÓN ===
            elif etapa == "iniciando_sesion":
                print("🔧 Procesando inicio de sesión...")
                if not validar_cedula(mensaje):
                    enviar_mensaje(telefono, "❌ Cédula inválida. Debe tener entre 6 y 10 dígitos.\n\nPor favor, ingresa tu cédula nuevamente:")
                    return jsonify({"status": "invalid cedula"}), 200
                
                success, mensaje_respuesta, cliente = iniciar_sesion(telefono, mensaje)
                
                if success and cliente:
                    SESIONES_ACTIVAS[telefono] = {
                        "id_usuario": cliente["id"],
                        "cedula": mensaje,
                        "nombre": cliente["nombre"]
                    }
                    enviar_mensaje(telefono, f"🎉 *¡Bienvenido de nuevo, {cliente['nombre']}!*\n\n✅ Sesión iniciada correctamente.")
                    enviar_menu_logueado(telefono, cliente["nombre"])
                    limpiar_estado_usuario(telefono)
                else:
                    if telefono not in LOGIN_ATTEMPTS:
                        LOGIN_ATTEMPTS[telefono] = 0
                    LOGIN_ATTEMPTS[telefono] += 1
                    
                    if LOGIN_ATTEMPTS[telefono] >= 3:
                        enviar_mensaje(telefono, "🔒 Demasiados intentos fallidos. Intenta más tarde.")
                        limpiar_estado_usuario(telefono)
                        enviar_menu_principal(telefono)
                    else:
                        enviar_mensaje(telefono, f"{mensaje_respuesta}\n\nIntento {LOGIN_ATTEMPTS[telefono]}/3\n\nIngresa tu cédula:")
                
                return jsonify({"status": "login processed"}), 200

            # === PROCESO DE REGISTRO ===
            elif etapa == "pidiendo_nombre":
                print("🔧 Procesando registro - nombre...")
                if len(mensaje) < 2:
                    enviar_mensaje(telefono, "❌ El nombre debe tener al menos 2 caracteres.\n\nIngresa tu nombre completo:")
                    return jsonify({"status": "invalid name"}), 200
                
                USUARIOS[telefono]["nombre"] = mensaje.title()
                USUARIOS[telefono]["etapa"] = "pidiendo_direccion"
                enviar_mensaje(telefono, "📍 Perfecto! Ahora ingresa tu *dirección completa*:")
                return jsonify({"status": "ask direccion"}), 200

            elif etapa == "pidiendo_direccion":
                print("🔧 Procesando registro - dirección...")
                if len(mensaje) < 5:
                    enviar_mensaje(telefono, "❌ La dirección debe tener al menos 5 caracteres.\n\nIngresa una dirección válida:")
                    return jsonify({"status": "invalid address"}), 200
                
                USUARIOS[telefono]["direccion"] = mensaje
                USUARIOS[telefono]["etapa"] = "pidiendo_cedula"
                enviar_mensaje(telefono, "🆔 Excelente! Por último, ingresa tu *número de cédula* (6-10 dígitos):")
                return jsonify({"status": "ask cedula"}), 200

            elif etapa == "pidiendo_cedula":
                print("🔧 Procesando registro - cédula...")
                if not validar_cedula(mensaje):
                    enviar_mensaje(telefono, "❌ Cédula inválida. Debe tener entre 6 y 10 dígitos.\n\nIngresa tu cédula:")
                    return jsonify({"status": "invalid cedula"}), 200
                
                nombre = USUARIOS[telefono]["nombre"]
                direccion = USUARIOS[telefono]["direccion"]
                cedula = mensaje
                
                success, mensaje_respuesta = agregar_cliente(nombre, telefono, direccion, cedula)
                
                if success:
                    mensaje_exito = f"""✅ *¡Registro completado exitosamente!*

📋 *Tus datos registrados:*
👤 Nombre: {nombre}
📞 Teléfono: {telefono}
🏠 Dirección: {direccion}
🆔 Cédula: {cedula}

                    ¡Bienvenido a Mezón Peruano! 🇵🇪"""
                    enviar_mensaje(telefono, mensaje_exito)
                    del USUARIOS[telefono]
                    enviar_menu_principal(telefono)
                else:
                    if "ya está registrado" in mensaje_respuesta:
                        enviar_mensaje(telefono, f"❌ *Usuario ya registrado*\n\nEl número {telefono} ya tiene una cuenta.\n\nPor favor selecciona 'Iniciar Sesión' desde el menú.")
                        del USUARIOS[telefono]
                        enviar_menu_principal(telefono)
                    else:
                        enviar_mensaje(telefono, f"❌ {mensaje_respuesta}")
                        del USUARIOS[telefono]
                
                return jsonify({"status": "registro completo"}), 200

        # === SEGUNDO: Manejo de usuarios logueados ===
        if telefono in SESIONES_ACTIVAS:
            print(f"🔐 Usuario {telefono} tiene sesión activa")
            
            if mensaje == "cerrar_sesion":
                nombre_usuario = SESIONES_ACTIVAS[telefono].get("nombre", "Usuario")
                del SESIONES_ACTIVAS[telefono]
                enviar_mensaje(telefono, f"👋 *Hasta pronto, {nombre_usuario}!*\n\nTu sesión ha sido cerrada correctamente.")
                enviar_menu_principal(telefono)
                return jsonify({"status": "sesion cerrada"}), 200

            elif mensaje == "actualizar_datos":
                print("🔄 Usuario seleccionó actualizar datos")
                enviar_menu_actualizacion(telefono)
                return jsonify({"status": "menu actualizacion"}), 200
            
            # LAS OPCIONES DE ACTUALIZACIÓN ESPECÍFICAS DEBEN ESTAR AQUÍ
            elif mensaje == "actualizar_nombre":
                print("📝 Iniciando actualización de nombre")
                enviar_mensaje(telefono, "✏️ *Actualizar Nombre*\n\nIngresa tu nuevo nombre completo:")
                USUARIOS[telefono] = {"etapa": "actualizando_nombre"}  # ✅ AHORA SÍ SE GUARDA
                print(f"✅ Usuario {telefono} en etapa: actualizando_nombre")
                return jsonify({"status": "actualizando nombre"}), 200
            
            elif mensaje == "actualizar_direccion":
                print("📝 Iniciando actualización de dirección")
                enviar_mensaje(telefono, "✏️ *Actualizar Dirección*\n\nIngresa tu nueva dirección completa:")
                USUARIOS[telefono] = {"etapa": "actualizando_direccion"}
                print(f"✅ Usuario {telefono} en etapa: actualizando_direccion")
                return jsonify({"status": "actualizando direccion"}), 200
            
            elif mensaje == "actualizar_cedula":
                print("📝 Iniciando actualización de cédula")
                enviar_mensaje(telefono, "🔐 *Verificación de Seguridad*\n\nPor tu seguridad, primero debes confirmar tu cédula actual.\n\nIngresa tu cédula actual (6-10 dígitos):")
                USUARIOS[telefono] = {"etapa": "verificando_cedula_actual"}
                print(f"✅ Usuario {telefono} en etapa: verificando_cedula_actual")
                return jsonify({"status": "verificando cedula"}), 200
            
            elif mensaje == "cancelar_actualizacion":
                nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                enviar_mensaje(telefono, "❌ Actualización cancelada.")
                enviar_menu_logueado(telefono, nombre)
                return jsonify({"status": "actualizacion cancelada"}), 200

            elif mensaje == "menu_principal":
                enviar_menu_principal(telefono)
                return jsonify({"status": "menu principal"}), 200
            
            elif mensaje == "ver_menu":
                enviar_menu_pdf(telefono)
                enviar_menu_productos(telefono)
                return jsonify({"status": "ver menu"}), 200
            
            elif mensaje == "informacion":
                info_texto = """ℹ️ *Información - Mezón Peruano* 🇵🇪

🍽️ Auténtico sabor peruano en cada plato

📍 *Dirección:* Casa Terrarosa - Zipaquirá, Cundinamarca
📞 *Teléfono:* +1-234-567-8900
🕒 *Horario:* 11:00 AM - 9:00 PM
📅 *Abierto:* Lunes a Domingo

        ¡Te esperamos! 🎉"""

                enviar_mensaje(telefono, info_texto)
                nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                enviar_menu_logueado(telefono, nombre)
                return jsonify({"status": "info"}), 200

            elif mensaje == "mi_informacion":
                try:
                    cliente = BDC.buscar_cliente(telefono)
                    if cliente:
                        info_msg = f"📋 *Tu Información Completa*\n\n"
                        info_msg += f"👤 *Nombre:* {cliente.get('nombre', 'No disponible')}\n"
                        info_msg += f"📞 *Teléfono:* {telefono}\n"
                        info_msg += f"🏠 *Dirección:* {cliente.get('direccion', 'No disponible')}\n"
                        enviar_mensaje(telefono, info_msg)
                    else:
                        enviar_mensaje(telefono, "❌ No se pudo obtener tu información.")
                except Exception as e:
                    print(f"🔴 Error obteniendo información: {e}")
                    enviar_mensaje(telefono, "❌ Error al consultar información.")
                
                sesion = SESIONES_ACTIVAS[telefono]
                enviar_menu_logueado(telefono, sesion.get('nombre'))
                return jsonify({"status": "informacion mostrada"}), 200

            else:
                # Si el usuario está logueado pero envía otro mensaje, mostrar menú logueado
                nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                enviar_menu_logueado(telefono, nombre)
                return jsonify({"status": "menu logueado"}), 200

        # === OPCIONES DEL MENÚ INTERACTIVO (cuando NO está en proceso) ===
        if mensaje == "iniciar_sesion":
            enviar_mensaje(telefono, "🔐 *Inicio de Sesión*\n\nPor favor, ingresa tu *número de cédula* (6-10 dígitos):")
            USUARIOS[telefono] = {"etapa": "iniciando_sesion"}
            return jsonify({"status": "login started"}), 200

        elif mensaje == "registrarse":
            if usuario_ya_registrado(telefono):
                enviar_mensaje(telefono, f"❌ *Ya estás registrado*\n\nEl número {telefono} ya tiene una cuenta.\n\nPor favor selecciona 'Iniciar Sesión' desde el menú.")
                enviar_menu_principal(telefono)
            else:
                enviar_mensaje(telefono, "📝 *Registro de Nuevo Usuario*\n\nComencemos con tu registro. Por favor ingresa tu *nombre completo*:")
                USUARIOS[telefono] = {"etapa": "pidiendo_nombre"}
            return jsonify({"status": "registro inicio"}), 200

        elif mensaje == "ver_menu":
            enviar_menu_pdf(telefono)
            enviar_menu_productos(telefono)
            return jsonify({"status": "ver menu"}), 200

        elif mensaje == "informacion":
            info_texto = """ℹ️ *Información - Mezón Peruano* 🇵🇪

🍽️ Auténtico sabor peruano en cada plato

📍 *Dirección:* Casa Terrarosa - Zipaquirá, Cundinamarca
📞 *Teléfono:* +1-234-567-8900
🕒 *Horario:* 11:00 AM - 9:00 PM
📅 *Abierto:* Lunes a Domingo

                ¡Te esperamos! 🎉"""
            enviar_mensaje(telefono, info_texto)
            enviar_menu_principal(telefono)
            return jsonify({"status": "info"}), 200

        # === OPCIONES DE PRODUCTOS ===
        elif mensaje.startswith("producto_"):
            enviar_detalle_producto(telefono, mensaje)
            return jsonify({"status": "detalle producto"}), 200
        
        elif mensaje == "volver_menu":
            if telefono in SESIONES_ACTIVAS:
                nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                enviar_menu_logueado(telefono, nombre)
            else:
                enviar_menu_principal(telefono)
            return jsonify({"status": "volver menu"}), 200

        # === MENSAJE DE BIENVENIDA ===
        if mensaje in ["hola", "hi", "hello", "menú", "menu", "opciones", "inicio"]:
            enviar_menu_principal(telefono)
            return jsonify({"status": "menu principal"}), 200

        # === FALLBACK ===
        enviar_menu_principal(telefono)
        return jsonify({"status": "fallback"}), 200

    except Exception as e:
        print(f"🔴 Error general en webhook: {e}")
        import traceback
        traceback.print_exc()
        try:
            enviar_mensaje(telefono, "❌ Ocurrió un error. Por favor intenta nuevamente escribiendo *hola*.")
        except:
            pass
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Iniciando servidor Flask con menús interactivos...")
    print("📍 Webhook: /webhook/")
    print("✨ Menús interactivos habilitados (Select Box)")
    app.run(debug=True, host="0.0.0.0", port=5000)