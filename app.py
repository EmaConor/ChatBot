# ChatBot inteligente con WhatsApp en Python
from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# === CONFIGURACIÓN ===
TOKEN = "EAApdsnrt0rUBP4hDyvp5KJEUQWIP7Xh8ZCwpQ1r72wPyPoCQtA93a8XKYZBa5h7kFa64cUUqtzZCdH7oAoHqpCJXPxMjEfCSjjcKPfmQZAosX3Yr4DNQTjIKs7OsZAWq6ovwBaTjkVT37QdEVcQQMkfiKKpNcJIYzQZCoZAcoFMhF0NB4uR3TIdBy6qOouZB4ID0rYsvGOadXTjIVqG1ok7Pf8cew0IhzvzPHDuc4Or6ecEkRGYkZBWzSFDKtjCroSRGcgoXi8ZBk06BEONCa0qt2ilwZDZD"
PHONE_NUMBER_ID = "863285753529334"

# === CARRITO EN MEMORIA ===
# Estructura: {numero_whatsapp: {'stage': 'menu', 'cart': [{id, name, qty, price, notes}], 'temp': {...}}}
CARTS = {}

# === FUNCIONES AUXILIARES ===
def fetch_menu():
    return [
        {'id': 1, 'name': 'Hamburguesa', 'price': 15000, 'description': 'Jugosa carne con queso y papas.'},
        {'id': 2, 'name': 'Perro caliente', 'price': 12000, 'description': 'Con salsa especial y tocineta.'},
        {'id': 3, 'name': 'Pizza personal', 'price': 18000, 'description': 'De pepperoni o hawaiana.'}
    ]

def format_menu():
    items = fetch_menu()
    lines = []
    for it in items:
        lines.append(f"{it['id']}. {it['name']} - ${it['price']:.0f}\n   {it['description']}")
    return "\n\n".join(lines)

# Simulación de base de datos (puedes reemplazar por tu lógica)
def get_or_create_customer(whatsapp_number, name): return 1
def create_order(customer_id, total, notes=None): return 101
def add_order_item(order_id, menu_id, quantity, price): pass
def notify_staff(msg): print("Notificación staff:", msg)

# === WEBHOOK ===
@app.route("/webhook/", methods=["POST", "GET"])
def webhook_whatsapp():
    # Verificación inicial (GET)
    if request.method == "GET":
        if request.args.get('hub.verify_token') == "HolaNovato":
            return request.args.get('hub.challenge')
        else:
            return "Error de autentificación."

    # Recepción de mensajes (POST)
    data = request.get_json()
    try:
        mensaje = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'].strip()
        telefonoCliente = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
    except KeyError:
        return jsonify({"status": "no message"}), 200

    text = mensaje.lower()
    user = CARTS.get(telefonoCliente, {'stage': 'start', 'cart': []})

    # === MENÚ INICIAL ===
    if text in ['menu', '1', 'ver menu', 'ver menú'] or user['stage'] == 'start':
        user['stage'] = 'browsing'
        CARTS[telefonoCliente] = user

        # --- Mensaje de texto del menú ---
        reply = (
        "📋 Aquí tienes nuestro *menú completo* 👇Descubre todos los platos y bebidas que tenemos para ti.¡Seguro encontrarás tu favorito! 😋\n\n"
        + format_menu()
        + "\n\n👉 Usa: *Agregar <id> <cantidad>*\nEjemplo: Agregar 2 1"
    )

        enviar_mensaje(telefonoCliente, reply)

    # --- Enviar el PDF después del mensaje ---
        PDF_URL = "https://github.com/EmaConor/ChatBot/blob/main/Resources/CARTA%20MEZON%20PERUANO%202025.pdf" 
        NOMBRE_ARCHIVO = "menu.pdf"
        enviar_pdf(telefonoCliente, PDF_URL, NOMBRE_ARCHIVO)
        return jsonify({"status": "menu"}), 200

    # === AGREGAR ITEM ===
    if text.startswith('agregar') or text.startswith('add'):
        parts = mensaje.split()
        try:
            idx = int(parts[1])
            qty = int(parts[2]) if len(parts) > 2 else 1
        except Exception:
            enviar_mensaje(telefonoCliente, "❌ Usa: *Agregar <id> <cantidad>*.\nEjemplo: Agregar 2 1")
            return jsonify({"status": "bad format"}), 200

        menu = [m for m in fetch_menu() if m['id'] == idx]
        if not menu:
            enviar_mensaje(telefonoCliente, "🚫 Ese ID no está disponible.")
            return jsonify({"status": "not found"}), 200

        m = menu[0]
        user['cart'].append({'id': m['id'], 'name': m['name'], 'qty': qty, 'price': float(m['price'])})
        CARTS[telefonoCliente] = user
        enviar_mensaje(telefonoCliente, f"✅ *Agregado:* {m['name']} x{qty}.\nEscribe *Carrito* para ver tus productos.")
        return jsonify({"status": "added"}), 200

    # === VER CARRITO ===
    if text in ['carrito', 'cart', 'ver carrito']:
        if not user.get('cart'):
            enviar_mensaje(telefonoCliente, "🛒 Tu carrito está vacío.\nEscribe *menu* para ver productos.")
            return jsonify({"status": "empty cart"}), 200
        lines = []
        total = 0
        for i, it in enumerate(user['cart'], 1):
            subtotal = it['qty'] * it['price']
            total += subtotal
            lines.append(f"{i}. {it['name']} x{it['qty']} - ${subtotal:.0f}")
        lines.append(f"\n💰 *Total:* ${total:.0f}\n\nEscribe *Confirmar* para finalizar o *Eliminar <n°>* para quitar un ítem.")
        enviar_mensaje(telefonoCliente, "\n".join(lines))
        return jsonify({"status": "cart shown"}), 200

    # === ELIMINAR ITEM ===
    if text.startswith('eliminar') or text.startswith('remove'):
        parts = mensaje.split()
        try:
            pos = int(parts[1]) - 1
            item = user['cart'].pop(pos)
            CARTS[telefonoCliente] = user
            enviar_mensaje(telefonoCliente, f"🗑️ Se eliminó {item['name']}.")
        except Exception:
            enviar_mensaje(telefonoCliente, "Usa: *Eliminar <número>*.\nEjemplo: Eliminar 1")
        return jsonify({"status": "removed"}), 200

    # === CONFIRMAR PEDIDO ===
    if text in ['confirmar', 'checkout']:
        if not user.get('cart'):
            enviar_mensaje(telefonoCliente, "Tu carrito está vacío. Escribe *menu* para comenzar.")
            return jsonify({"status": "no cart"}), 200
        user['stage'] = 'asking_name'
        CARTS[telefonoCliente] = user
        enviar_mensaje(telefonoCliente, "📝 ¿Cuál es tu nombre completo?")
        return jsonify({"status": "ask name"}), 200

    # === PEDIR NOMBRE Y DIRECCIÓN ===
    if user.get('stage') == 'asking_name':
        user['temp'] = {'name': mensaje}
        user['stage'] = 'asking_address'
        CARTS[telefonoCliente] = user
        enviar_mensaje(telefonoCliente, "📍 Gracias. Dime la dirección de envío (o escribe *Retirar* si recogerás en tienda).")
        return jsonify({"status": "ask address"}), 200

    if user.get('stage') == 'asking_address':
        user['temp']['address'] = mensaje
        cid = get_or_create_customer(whatsapp_number=telefonoCliente, name=user['temp'].get('name'))
        total = sum(it['qty'] * it['price'] for it in user['cart'])
        oid = create_order(customer_id=cid, total=total)
        for it in user['cart']:
            add_order_item(order_id=oid, menu_id=it['id'], quantity=it['qty'], price=it['price'])
        CARTS.pop(telefonoCliente, None)
        msg = f"✅ *Pedido recibido*\n🧾 Orden #{oid}\n💰 Total: ${total:.0f}\n📦 Dirección: {mensaje}\n\nGracias por tu pedido 🎉"
        enviar_mensaje(telefonoCliente, msg)
        notify_staff(f"🧾 Nuevo pedido #{oid}\nCliente: {user['temp']['name']}\nTotal: ${total:.0f}\nDirección: {mensaje}")
        return jsonify({"status": "order complete"}), 200

    # === FALLBACK ===
    enviar_mensaje(telefonoCliente, "🤖 No entendí. Escribe *menu* para ver productos o *carrito* para revisar tu pedido.")
    return jsonify({"status": "fallback"}), 200


# === FUNCIÓN PARA ENVIAR MENSAJES A WHATSAPP ===
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
    print(f"→ Enviado a {numero}: {texto}")
    print("Status:", response.status_code, response.text)
# === FUNCIÓN PARA ENVIAR PDF A WHATSAPP ===
def enviar_pdf(numero, pdf_url, nombre_archivo):
    #"""Envía un archivo PDF por WhatsApp."""
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
            "link": pdf_url,
            "filename": nombre_archivo
        }
    }
    requests.post(url, headers=headers, json=data)

# === INICIAR FLASK ===
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
