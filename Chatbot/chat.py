# ChatBot con menús interactivos (select box) en WhatsApp
from flask import Flask, jsonify, request, redirect

import sys
import os

# Obtener la ruta absoluta al directorio raíz 
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Agregar al path de Python
sys.path.append(ROOT_PATH)

import DataBases.ClientesController as BDC
import DataBases.productsController as DBP
import DataBases.PedidosController as DBPedidos
import requests
import re
import html
import time
from datetime import datetime, time as dt_time
import pytz

app = Flask(__name__)

# === CONFIGURACIÓN ===
TOKEN = "EAApdsnrt0rUBP1G1qAOB5hmKasvEKf024GEe919CEIsv4CHB8J5ZBrQpDvFtEomG4WsuwrUlxUp6cvcKvZB3C0pvRIiUKrIXleVZAWou9514E1H8v03ZB0JN7FESrzF6ZCl3T6j6ZA6gh7HF0bdq9aYZBWpzZCwIZAsc4yCiaV2pLKCDtpQkeM7oI3GhZBNCIibNPoulL8SyZC3Fxi8Fa4um2jZCGNrYstecXpFC92MkTciZBcV7gbAZDZD"
PHONE_NUMBER_ID = "863285753529334"

# === BASE DE DATOS TEMPORAL ===
USUARIOS = {}
LOGIN_ATTEMPTS = {}
SESIONES_ACTIVAS = {}
CARRITOS = {}  # {telefono: [{"producto_id": id, "nombre": nombre, "precio": precio, "cantidad": cantidad}]}
NOTAS_PRODUCTOS = {}  # {telefono: {producto_id: nota}}

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
                    <li>🛒 Sistema de carrito de compras</li>
                    <li>📦 Gestión de pedidos integrada</li>
                    <li>📝 Notas por producto</li>
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
            "login_attempts_tracking": len(LOGIN_ATTEMPTS),
            "active_carts": len(CARRITOS)
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
HORARIO_CIERRE = dt_time(23, 0)    # 9:00 PM
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

# === FUNCIONES PARA EL CARRITO ===
def agregar_al_carrito(telefono, producto_id, cantidad=1):
    """Agrega un producto al carrito del usuario"""
    try:
        producto = DBP.buscar_producto_por_id(producto_id)
        if not producto:
            return False, "❌ Producto no encontrado"
        
        if telefono not in CARRITOS:
            CARRITOS[telefono] = []
        
        # Verificar si el producto ya está en el carrito
        for item in CARRITOS[telefono]:
            if item["producto_id"] == producto_id:
                item["cantidad"] += cantidad
                return True, f"✅ Cantidad actualizada: {producto['nombre']} x{item['cantidad']}"
        
        # Agregar nuevo producto al carrito
        CARRITOS[telefono].append({
            "producto_id": producto_id,
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "cantidad": cantidad
        })
        
        return True, f"✅ {producto['nombre']} agregado al carrito"
        
    except Exception as e:
        print(f"🔴 Error agregando al carrito: {e}")
        return False, "❌ Error al agregar al carrito"

def obtener_carrito(telefono):
    """Obtiene el carrito del usuario"""
    return CARRITOS.get(telefono, [])

def calcular_total_carrito(telefono):
    """Calcula el total del carrito"""
    carrito = obtener_carrito(telefono)
    total = 0
    for item in carrito:
        total += item["precio"] * item["cantidad"]
    return total

def eliminar_del_carrito(telefono, producto_id):
    """Elimina un producto del carrito"""
    if telefono in CARRITOS:
        CARRITOS[telefono] = [item for item in CARRITOS[telefono] if item["producto_id"] != producto_id]
        return True
    return False

def actualizar_cantidad_carrito(telefono, producto_id, nueva_cantidad):
    """Actualiza la cantidad de un producto en el carrito"""
    if telefono in CARRITOS:
        for item in CARRITOS[telefono]:
            if item["producto_id"] == producto_id:
                if nueva_cantidad <= 0:
                    eliminar_del_carrito(telefono, producto_id)
                    return True, "Producto eliminado del carrito"
                else:
                    item["cantidad"] = nueva_cantidad
                    return True, f"✅ Cantidad actualizada a {nueva_cantidad}"
    return False, "Producto no encontrado en el carrito"

def vaciar_carrito(telefono):
    """Vacía todo el carrito"""
    if telefono in CARRITOS:
        CARRITOS[telefono] = []
        return True
    return False

def obtener_nota_producto(telefono, producto_id):
    """Obtiene la nota de un producto"""
    if telefono in NOTAS_PRODUCTOS and producto_id in NOTAS_PRODUCTOS[telefono]:
        return NOTAS_PRODUCTOS[telefono][producto_id]
    return ""

def guardar_nota_producto(telefono, producto_id, nota):
    """Guarda la nota de un producto"""
    if telefono not in NOTAS_PRODUCTOS:
        NOTAS_PRODUCTOS[telefono] = {}
    NOTAS_PRODUCTOS[telefono][producto_id] = nota

# === FUNCIONES PARA MENÚS INTERACTIVOS ===
def validar_titulo_seccion(titulo):
    """Valida y ajusta el título de sección al límite de WhatsApp"""
    if len(titulo) > 24:
        # Acortar el título manteniendo la esencia
        if "Categorías" in titulo:
            return "📂 Categorías"
        elif "Opciones" in titulo:
            return "📋 Opciones"
        elif "Servicios" in titulo:
            return "🍽️ Servicios"
        elif "Mi Cuenta" in titulo:
            return "👤 Mi Cuenta"
        elif "Navegación" in titulo:
            return "🔙 Navegación"
        elif "Información" in titulo:
            return "📝 Información"
        elif "Actualizar" in titulo:
            return "✏️ Actualizar"
        elif "Productos" in titulo:
            return "🍽️ Productos"
        else:
            return titulo[:21] + "..."
    return titulo

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
        # Validar y ajustar títulos de secciones
        for seccion in secciones:
            if 'title' in seccion:
                seccion['title'] = validar_titulo_seccion(seccion['title'])
        
        # Verificar que no excedamos el límite de 10 filas en total
        total_rows = 0
        for seccion in secciones:
            total_rows += len(seccion.get('rows', []))
        
        if total_rows > 10:
            print(f"⚠️ Advertencia: Demasiadas filas ({total_rows}), limitando a 10")
            # Limitar a 10 filas máximo
            secciones_limited = []
            rows_count = 0
            for seccion in secciones:
                if rows_count >= 10:
                    break
                limited_rows = []
                for row in seccion.get('rows', []):
                    if rows_count < 10:
                        limited_rows.append(row)
                        rows_count += 1
                    else:
                        break
                if limited_rows:
                    secciones_limited.append({
                        'title': seccion['title'],
                        'rows': limited_rows
                    })
            secciones = secciones_limited
        
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
    
    carrito = obtener_carrito(numero)
    items_carrito = len(carrito) if carrito else 0
    
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
                },
                {
                    "id": "ver_carrito",
                    "title": f"🛒 Carrito ({items_carrito})",
                    "description": f"Ver tus productos ({items_carrito} items)"
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
    carrito = obtener_carrito(numero)
    items_carrito = len(carrito) if carrito else 0
    
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
                },
                {
                    "id": "ver_carrito",
                    "title": f"🛒 Carrito ({items_carrito})",
                    "description": f"Ver tus productos ({items_carrito} items)"
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
            "title": "✏️ Actualizar Datos",
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

def enviar_menu_carrito(numero):
    """Envía el menú del carrito con opciones"""
    carrito = obtener_carrito(numero)
    total = calcular_total_carrito(numero)
    
    if not carrito:
        mensaje = "🛒 *Tu Carrito está vacío*\n\nNo hay productos en tu carrito."
        enviar_mensaje(numero, mensaje)
        time.sleep(1)
        enviar_menu_categorias(numero)
        return False
    
    # Construir resumen del carrito
    resumen = "🛒 *Tu Carrito de Compras*\n\n"
    for i, item in enumerate(carrito, 1):
        subtotal = item["precio"] * item["cantidad"]
        nota = obtener_nota_producto(numero, item["producto_id"])
        resumen += f"{i}. {item['nombre']}\n"
        resumen += f"   Cantidad: {item['cantidad']} x ${item['precio']:,} = ${subtotal:,}\n"
        if nota:
            resumen += f"   📝 Nota: {nota}\n"
        resumen += "\n"
    
    resumen += f"💰 *Total: ${total:,}*"
    
    # Enviar resumen primero
    enviar_mensaje(numero, resumen)
    time.sleep(1)
    
    # Menú de opciones del carrito
    secciones = [
        {
            "title": "🛒 Opciones Carrito",
            "rows": [
                {
                    "id": "confirmar_pedido",
                    "title": "✅ Confirmar Pedido",
                    "description": "Finalizar y enviar tu pedido"
                },
                {
                    "id": "agregar_producto",
                    "title": "➕ Agregar Producto",
                    "description": "Seguir agregando productos"
                },
                {
                    "id": "editar_carrito",
                    "title": "✏️ Editar Carrito",
                    "description": "Modificar cantidades o eliminar"
                }
            ]
        },
        {
            "title": "📝 Información",
            "rows": [
                {
                    "id": "agregar_notas",
                    "title": "📄 Agregar Notas",
                    "description": "Añadir notas a los productos"
                },
                {
                    "id": "volver_menu_principal",
                    "title": "🔙 Menú Principal",
                    "description": "Volver al menú principal"
                }
            ]
        }
    ]
    
    return enviar_menu_interactivo(
        numero,
        "🛒 Gestionar Carrito",
        "Selecciona una opción para gestionar tu carrito:",
        secciones
    )

def enviar_menu_edicion_carrito(numero):
    """Envía menú para editar productos del carrito"""
    carrito = obtener_carrito(numero)
    
    if not carrito:
        enviar_mensaje(numero, "❌ Tu carrito está vacío")
        enviar_menu_carrito(numero)
        return False
    
    # Si hay muchos productos, dividir en múltiples menús
    if len(carrito) > 4:
        enviar_mensaje(numero, f"📦 Tienes {len(carrito)} productos en tu carrito.")
        enviar_mensaje(numero, "Para editar productos individuales, por favor elimina algunos primero o confirma tu pedido actual.")
        time.sleep(1)
        enviar_menu_carrito(numero)
        return False
    
    secciones = []
    
    # Sección para cada producto en el carrito (máximo 4 productos)
    for i, item in enumerate(carrito[:4], 1):
        nota_actual = obtener_nota_producto(numero, item['producto_id'])
        tiene_nota = "📝" if nota_actual else ""
        
        secciones.append({
            "title": f"📦 {item['nombre'][:20]}...",
            "rows": [
                {
                    "id": f"editar_cantidad_{item['producto_id']}",
                    "title": f"✏️ Cantidad ({item['cantidad']})",
                    "description": f"Cambiar cantidad"
                },
                {
                    "id": f"agregar_nota_{item['producto_id']}",
                    "title": f"📝 Agregar Nota {tiene_nota}",
                    "description": f"Añadir nota especial"
                },
                {
                    "id": f"eliminar_producto_{item['producto_id']}",
                    "title": "🗑️ Eliminar",
                    "description": f"Quitar del carrito"
                }
            ]
        })
    
    # Sección de navegación
    secciones.append({
        "title": "🔙 Navegación",
        "rows": [
            {
                "id": "volver_carrito",
                "title": "Volver al Carrito",
                "description": "Regresar al menú del carrito"
            }
        ]
    })
    
    return enviar_menu_interactivo(
        numero,
        "✏️ Editar Carrito",
        "Selecciona qué producto deseas modificar:",
        secciones
    )

def enviar_menu_agregar_nota(numero, producto_id):
    """Envía menú para agregar nota a un producto específico"""
    try:
        producto = DBP.buscar_producto_por_id(producto_id)
        if not producto:
            enviar_mensaje(numero, "❌ Producto no encontrado.")
            return False
        
        nota_actual = obtener_nota_producto(numero, producto_id)
        
        secciones = [
            {
                "title": f"📝 {producto['nombre'][:20]}",
                "rows": [
                    {
                        "id": f"escribir_nota_{producto_id}",
                        "title": "✏️ Escribir Nota",
                        "description": "Escribir una nota personalizada"
                    }
                ]
            }
        ]
        
        if nota_actual:
            secciones[0]["rows"].append({
                "id": f"ver_nota_{producto_id}",
                "title": "👀 Ver Nota Actual",
                "description": "Ver la nota que tienes guardada"
            })
            secciones[0]["rows"].append({
                "id": f"eliminar_nota_{producto_id}",
                "title": "🗑️ Eliminar Nota",
                "description": "Quitar la nota actual"
            })
        
        secciones.append({
            "title": "🔙 Navegación",
            "rows": [
                {
                    "id": "volver_edicion_carrito",
                    "title": "Volver a Edición",
                    "description": "Regresar al menú de edición"
                }
            ]
        })
        
        mensaje_cuerpo = f"📝 *Agregar nota para {producto['nombre']}*"
        if nota_actual:
            mensaje_cuerpo += f"\n\nNota actual: \"{nota_actual}\""
        
        return enviar_menu_interactivo(
            numero,
            "📝 Gestionar Nota",
            mensaje_cuerpo,
            secciones
        )
        
    except Exception as e:
        print(f"🔴 Error mostrando menú de notas: {e}")
        enviar_mensaje(numero, "❌ Error al cargar opciones de nota.")
        return False

def enviar_menu_categorias(numero):
    """Envía un menú con categorías"""
    try:
        productos = DBP.listar_productos()
        categorias_set = set()
        
        for producto in productos:
            if producto.get("Disponible", 1) == 1:
                categorias_set.add(producto.get("categoria", "Otros"))
        
        categorias = list(categorias_set)
        
        if not categorias:
            enviar_mensaje(numero, "📭 No hay categorías disponibles.")
            return False
        
        secciones = []
        rows_categorias = []
        
        for categoria in categorias[:10]:
            productos_cat = DBP.obtener_productos_por_categoria(categoria)
            count = len(productos_cat)
            
            rows_categorias.append({
                "id": f"categoria_{categoria}",
                "title": f"📂 {categoria}",
                "description": f"{count} producto{'s' if count != 1 else ''}"
            })
        
        secciones.append({
            "title": "📂 Categorías",
            "rows": rows_categorias
        })
        
        # Opciones de navegación
        secciones.append({
            "title": "🔙 Navegación",
            "rows": [
                {
                    "id": "volver_menu_principal",
                    "title": "🏠 Menú Principal",
                    "description": "Volver al menú principal"
                },
                {
                    "id": "ver_carrito",
                    "title": "🛒 Ver Carrito",
                    "description": "Ver productos en tu carrito"
                }
            ]
        })
        
        return enviar_menu_interactivo(
            numero,
            "🍽️ Ver Menú",
            "📋 *Selecciona una categoría para ver sus productos:*",
            secciones
        )
        
    except Exception as e:
        print(f"🔴 Error mostrando categorías: {e}")
        enviar_mensaje(numero, "❌ Error al cargar categorías.")
        return False

def enviar_productos_categoria(numero, categoria):
    """Envía un menú con los productos de una categoría específica"""
    try:
        productos = DBP.obtener_productos_por_categoria(categoria)
        
        if not productos:
            enviar_mensaje(numero, f"📭 No hay productos disponibles en '{categoria}'.")
            time.sleep(1)
            enviar_menu_categorias(numero)
            return False
        
        secciones = []
        rows_productos = []
        
        for producto in productos[:10]:
            precio_formateado = f"${producto.get('precio', 0):,}"
            nombre = producto.get("nombre", "Producto")
            if len(nombre) > 20:
                nombre = nombre[:20] + "..."
            
            rows_productos.append({
                "id": f"producto_{producto.get('id', '')}",
                "title": nombre,
                "description": precio_formateado
            })
        
        # Acortar el título de la categoría si es necesario
        titulo_categoria = f"🍽️ {categoria}"
        if len(titulo_categoria) > 24:
            titulo_categoria = f"🍽️ {categoria[:18]}..."
        
        secciones.append({
            "title": titulo_categoria,
            "rows": rows_productos
        })
        
        # Opciones de navegación
        secciones.append({
            "title": "🔙 Navegación",
            "rows": [
                {
                    "id": "volver_categorias",
                    "title": "📂 Volver a Categorías",
                    "description": "Ver todas las categorías"
                },
                {
                    "id": "volver_menu_principal",
                    "title": "🏠 Menú Principal",
                    "description": "Volver al menú principal"
                },
                {
                    "id": "ver_carrito",
                    "title": "🛒 Ver Carrito",
                    "description": "Ver productos en tu carrito"
                }
            ]
        })
        
        return enviar_menu_interactivo(
            numero,
            "🍽️ Seleccionar",
            f"📋 *Productos de {categoria}*\n\nSelecciona un producto para agregarlo al carrito:",
            secciones
        )
        
    except Exception as e:
        print(f"🔴 Error mostrando productos de {categoria}: {e}")
        enviar_mensaje(numero, f"❌ Error al cargar productos de {categoria}.")
        return False

def enviar_menu_pdf(numero):
    """Envía el menú en formato PDF al usuario"""
    try:
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
            
            time.sleep(1)
            mensaje_adicional = """📋 *¿Necesitas ayuda para elegir?*

Explora nuestras categorías en el menú interactivo."""
            enviar_mensaje(numero, mensaje_adicional)
            
            return True
        else:
            print(f"🔴 Error enviando PDF: {response.status_code} - {response.text}")
            enviar_mensaje(numero, "❌ No pude cargar el menú PDF. Te muestro nuestras categorías:")
            
    except Exception as e:
        print(f"🔴 Error enviando PDF del menú: {e}")
        enviar_mensaje(numero, "❌ Error al cargar el menú PDF. Te muestro nuestras categorías:")

def guardar_pedido_en_bd(telefono, descripcion_general=""):
    """Guarda el pedido en la base de datos"""
    try:
        if telefono not in SESIONES_ACTIVAS:
            return False, "❌ Debes iniciar sesión para guardar el pedido"
        
        carrito = obtener_carrito(telefono)
        if not carrito:
            return False, "❌ El carrito está vacío"
        
        # Preparar productos para la base de datos
        productos_pedido = []
        for item in carrito:
            nota = obtener_nota_producto(telefono, item["producto_id"])
            productos_pedido.append({
                'producto_id': item['producto_id'],
                'cantidad': item['cantidad'],
                'notas': nota
            })
        
        # Crear pedido en la base de datos usando el teléfono
        pedido_id = DBPedidos.crear_pedido_por_telefono(
            telefono=telefono,
            productos=productos_pedido,
            descripcion=descripcion_general
        )
        
        if pedido_id:
            # Limpiar carrito y notas después de guardar
            vaciar_carrito(telefono)
            if telefono in NOTAS_PRODUCTOS:
                del NOTAS_PRODUCTOS[telefono]
            
            return True, f"✅ *Pedido #{pedido_id} guardado correctamente*"
        else:
            return False, "❌ Error al guardar el pedido en el sistema"
            
    except Exception as e:
        print(f"🔴 Error guardando pedido: {e}")
        return False, "❌ Error al procesar el pedido"

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
        
        # === PRIMERO: Manejo de etapas activas ===
        if telefono in USUARIOS:
            etapa = USUARIOS[telefono].get("etapa")
            print(f"🔍 Usuario {telefono} en etapa: {etapa}")
            
            # === PROCESO DE ACTUALIZACIÓN DE DATOS ===
            if etapa == "actualizando_nombre":
                if len(mensaje) < 2:
                    enviar_mensaje(telefono, "❌ El nombre debe tener al menos 2 caracteres.\n\nIngresa un nombre válido:")
                    return jsonify({"status": "invalid name"}), 200
    
                try:
                    cedula_actual = SESIONES_ACTIVAS[telefono].get("cedula")
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
                if len(mensaje) < 5:
                    enviar_mensaje(telefono, "❌ La dirección debe tener al menos 5 caracteres.\n\nIngresa una dirección válida:")
                    return jsonify({"status": "invalid address"}), 200
    
                try:
                    cedula_actual = SESIONES_ACTIVAS[telefono].get("cedula")
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
                if not validar_cedula(mensaje):
                    enviar_mensaje(telefono, "❌ Cédula inválida. Debe tener entre 6 y 10 dígitos.\n\nIngresa tu cédula actual:")
                    return jsonify({"status": "invalid cedula"}), 200
    
                try:
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
                if not validar_cedula(mensaje):
                    enviar_mensaje(telefono, "❌ Cédula inválida. Debe tener entre 6 y 10 dígitos.\n\nIngresa una cédula válida:")
                    return jsonify({"status": "invalid cedula"}), 200
    
                try:
                    cedula_actual = SESIONES_ACTIVAS[telefono].get("cedula")
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
                if len(mensaje) < 2:
                    enviar_mensaje(telefono, "❌ El nombre debe tener al menos 2 caracteres.\n\nIngresa tu nombre completo:")
                    return jsonify({"status": "invalid name"}), 200
                
                USUARIOS[telefono]["nombre"] = mensaje.title()
                USUARIOS[telefono]["etapa"] = "pidiendo_direccion"
                enviar_mensaje(telefono, "📍 Perfecto! Ahora ingresa tu *dirección completa*:")
                return jsonify({"status": "ask direccion"}), 200

            elif etapa == "pidiendo_direccion":
                if len(mensaje) < 5:
                    enviar_mensaje(telefono, "❌ La dirección debe tener al menos 5 caracteres.\n\nIngresa una dirección válida:")
                    return jsonify({"status": "invalid address"}), 200
                
                USUARIOS[telefono]["direccion"] = mensaje
                USUARIOS[telefono]["etapa"] = "pidiendo_cedula"
                enviar_mensaje(telefono, "🆔 Excelente! Por último, ingresa tu *número de cédula* (6-10 dígitos):")
                return jsonify({"status": "ask cedula"}), 200

            elif etapa == "pidiendo_cedula":
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

            # === PROCESO DE EDICIÓN DE CARRITO ===
            elif etapa == "editando_cantidad":
                try:
                    nueva_cantidad = int(mensaje)
                    producto_id = USUARIOS[telefono]["producto_id"]
                    success, mensaje_respuesta = actualizar_cantidad_carrito(telefono, producto_id, nueva_cantidad)
                    enviar_mensaje(telefono, mensaje_respuesta)
                    del USUARIOS[telefono]
                    time.sleep(1)
                    enviar_menu_carrito(telefono)
                except ValueError:
                    enviar_mensaje(telefono, "❌ Por favor ingresa un número válido para la cantidad:")
                return jsonify({"status": "cantidad actualizada"}), 200

            # === PROCESO DE AGREGAR NOTA ===
            elif etapa == "agregando_nota":
                producto_id = USUARIOS[telefono]["producto_id"]
                guardar_nota_producto(telefono, producto_id, mensaje)
                enviar_mensaje(telefono, f"✅ *Nota guardada correctamente*\n\nTu nota ha sido guardada para este producto.")
                del USUARIOS[telefono]
                time.sleep(1)
                enviar_menu_edicion_carrito(telefono)
                return jsonify({"status": "nota guardada"}), 200

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
                enviar_menu_actualizacion(telefono)
                return jsonify({"status": "menu actualizacion"}), 200
            
            elif mensaje == "actualizar_nombre":
                enviar_mensaje(telefono, "✏️ *Actualizar Nombre*\n\nIngresa tu nuevo nombre completo:")
                USUARIOS[telefono] = {"etapa": "actualizando_nombre"}
                return jsonify({"status": "actualizando nombre"}), 200
            
            elif mensaje == "actualizar_direccion":
                enviar_mensaje(telefono, "✏️ *Actualizar Dirección*\n\nIngresa tu nueva dirección completa:")
                USUARIOS[telefono] = {"etapa": "actualizando_direccion"}
                return jsonify({"status": "actualizando direccion"}), 200
            
            elif mensaje == "actualizar_cedula":
                enviar_mensaje(telefono, "🔐 *Verificación de Seguridad*\n\nPor tu seguridad, primero debes confirmar tu cédula actual.\n\nIngresa tu cédula actual (6-10 dígitos):")
                USUARIOS[telefono] = {"etapa": "verificando_cedula_actual"}
                return jsonify({"status": "verificando cedula"}), 200
            
            elif mensaje == "cancelar_actualizacion":
                nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                enviar_mensaje(telefono, "❌ Actualización cancelada.")
                enviar_menu_logueado(telefono, nombre)
                return jsonify({"status": "actualizacion cancelada"}), 200

        # === MANEJO DE CATEGORÍAS Y PRODUCTOS ===
        if mensaje.startswith("categoria_"):
            categoria = mensaje.replace("categoria_", "")
            print(f"📂 Categoría seleccionada: {categoria}")
            enviar_productos_categoria(telefono, categoria)
            return jsonify({"status": "categoria seleccionada"}), 200

        elif mensaje.startswith("producto_"):
            producto_id = int(mensaje.replace("producto_", ""))
            print(f"🍽️ Producto seleccionado: {producto_id}")
            # Agregar directamente al carrito
            success, mensaje_respuesta = agregar_al_carrito(telefono, producto_id)
            enviar_mensaje(telefono, mensaje_respuesta)
            time.sleep(1)
            enviar_menu_principal(telefono)
            return jsonify({"status": "producto agregado"}), 200

        # === OPCIONES PRINCIPALES ===
        elif mensaje == "iniciar_sesion":
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
            time.sleep(1)
            enviar_menu_categorias(telefono)
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

        # === OPCIONES DEL CARRITO ===
        elif mensaje == "ver_carrito":
            enviar_menu_carrito(telefono)
            return jsonify({"status": "ver carrito"}), 200

        elif mensaje == "agregar_producto":
            enviar_menu_categorias(telefono)
            return jsonify({"status": "agregar producto"}), 200

        elif mensaje == "editar_carrito":
            enviar_menu_edicion_carrito(telefono)
            return jsonify({"status": "editar carrito"}), 200

        elif mensaje == "volver_carrito":
            enviar_menu_carrito(telefono)
            return jsonify({"status": "volver carrito"}), 200

        elif mensaje == "volver_categorias":
            enviar_menu_categorias(telefono)
            return jsonify({"status": "volver categorias"}), 200

        elif mensaje == "volver_menu_principal":
            enviar_menu_principal(telefono)
            return jsonify({"status": "volver menu principal"}), 200

        elif mensaje == "volver_menu":
            enviar_menu_principal(telefono)
            return jsonify({"status": "volver menu"}), 200

        elif mensaje == "volver_edicion_carrito":
            enviar_menu_edicion_carrito(telefono)
            return jsonify({"status": "volver edicion carrito"}), 200

        # Manejar edición de cantidades
        elif mensaje.startswith("editar_cantidad_"):
            producto_id = int(mensaje.replace("editar_cantidad_", ""))
            USUARIOS[telefono] = {
                "etapa": "editando_cantidad",
                "producto_id": producto_id
            }
            enviar_mensaje(telefono, "✏️ Ingresa la nueva cantidad para este producto:")
            return jsonify({"status": "editando cantidad"}), 200

        # Manejar notas de productos
        elif mensaje.startswith("agregar_nota_"):
            producto_id = int(mensaje.replace("agregar_nota_", ""))
            enviar_menu_agregar_nota(telefono, producto_id)
            return jsonify({"status": "menu agregar nota"}), 200

        elif mensaje.startswith("escribir_nota_"):
            producto_id = int(mensaje.replace("escribir_nota_", ""))
            USUARIOS[telefono] = {
                "etapa": "agregando_nota",
                "producto_id": producto_id
            }
            enviar_mensaje(telefono, "📝 *Escribe la nota para este producto:*\n\n(Puedes escribir cualquier instrucción especial)")
            return jsonify({"status": "escribiendo nota"}), 200

        elif mensaje.startswith("ver_nota_"):
            producto_id = int(mensaje.replace("ver_nota_", ""))
            nota = obtener_nota_producto(telefono, producto_id)
            producto = DBP.buscar_producto_por_id(producto_id)
            if producto and nota:
                enviar_mensaje(telefono, f"📝 *Nota para {producto['nombre']}:*\n\n\"{nota}\"")
            else:
                enviar_mensaje(telefono, "ℹ️ No hay nota guardada para este producto.")
            time.sleep(1)
            enviar_menu_agregar_nota(telefono, producto_id)
            return jsonify({"status": "ver nota"}), 200

        elif mensaje.startswith("eliminar_nota_"):
            producto_id = int(mensaje.replace("eliminar_nota_", ""))
            if telefono in NOTAS_PRODUCTOS and producto_id in NOTAS_PRODUCTOS[telefono]:
                del NOTAS_PRODUCTOS[telefono][producto_id]
                enviar_mensaje(telefono, "✅ Nota eliminada correctamente.")
            else:
                enviar_mensaje(telefono, "ℹ️ No había nota para eliminar.")
            time.sleep(1)
            enviar_menu_agregar_nota(telefono, producto_id)
            return jsonify({"status": "eliminar nota"}), 200

        elif mensaje.startswith("eliminar_producto_"):
            producto_id = int(mensaje.replace("eliminar_producto_", ""))
            eliminar_del_carrito(telefono, producto_id)
            # También eliminar la nota si existe
            if telefono in NOTAS_PRODUCTOS and producto_id in NOTAS_PRODUCTOS[telefono]:
                del NOTAS_PRODUCTOS[telefono][producto_id]
            enviar_mensaje(telefono, "✅ Producto eliminado del carrito")
            time.sleep(1)
            enviar_menu_carrito(telefono)
            return jsonify({"status": "producto eliminado"}), 200

        elif mensaje == "agregar_notas":
            enviar_mensaje(telefono, "📝 *Agregar Notas a Productos*\n\nPara agregar notas a productos específicos, ve a 'Editar Carrito' y selecciona 'Agregar Nota' en cada producto.")
            time.sleep(1)
            enviar_menu_carrito(telefono)
            return jsonify({"status": "info notas"}), 200

        elif mensaje == "confirmar_pedido":
            if telefono not in SESIONES_ACTIVAS:
                enviar_mensaje(telefono, "❌ Debes iniciar sesión para confirmar el pedido")
                enviar_menu_principal(telefono)
                return jsonify({"status": "login requerido"}), 200
            
            carrito = obtener_carrito(telefono)
            
            if not carrito:
                enviar_mensaje(telefono, "❌ Tu carrito está vacío")
                enviar_menu_carrito(telefono)
                return jsonify({"status": "carrito vacio"}), 200
            
            total = calcular_total_carrito(telefono)
            notas_pedido = NOTAS_PRODUCTOS.get(telefono, {}).copy()

            # Guardar pedido en la base de datos
            success, mensaje_respuesta = guardar_pedido_en_bd(telefono)
            enviar_mensaje(telefono, mensaje_respuesta)
            
            if success:
                # Mostrar resumen del pedido guardado
                mensaje_confirmacion = f"""✅ *Pedido Confirmado* 🎉

🛒 *Resumen de tu pedido:*
"""
                for item in carrito:
                    subtotal = item["precio"] * item["cantidad"]
                    nota = notas_pedido.get(item["producto_id"], "")
                    mensaje_confirmacion += f"• {item['nombre']} x{item['cantidad']} = ${subtotal:,}"
                    if nota:
                        mensaje_confirmacion += f" (Nota: {nota})"
                    mensaje_confirmacion += "\n"
                
                mensaje_confirmacion += f"\n💰 *Total: ${total:,}*"
                mensaje_confirmacion += "\n\n📞 Nos contactaremos contigo pronto para coordinar la entrega."
                
                enviar_mensaje(telefono, mensaje_confirmacion)
            
            time.sleep(2)
            enviar_menu_principal(telefono)
            
            return jsonify({"status": "pedido confirmado"}), 200

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
            
            if telefono in SESIONES_ACTIVAS:
                nombre = SESIONES_ACTIVAS[telefono].get("nombre")
                enviar_menu_logueado(telefono, nombre)
            
            return jsonify({"status": "informacion mostrada"}), 200

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
    print("🛒 Sistema de carrito de compras activado")
    print("📂 Navegación por categorías implementada")
    print("📝 Sistema de notas por producto activado")
    print("💾 Guardado en base de datos implementado")
    print("⚠️  Límites implementados: máximo 10 filas por menú")
    app.run(debug=True, host="0.0.0.0", port=5000)