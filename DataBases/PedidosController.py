import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

# === CONFIGURACIÓN DE LA BASE DE DATOS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "MezonPeruano.db")

# === INICIALIZACIÓN DE LA BASE DE DATOS ===
def init_db():
    """Inicializa la base de datos y crea las tablas si no existen"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tabla de facturas (pedidos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            precio_total REAL NOT NULL,
            descripcion TEXT,
            cedula_cliente TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'Pedido',
            FOREIGN KEY (cedula_cliente) REFERENCES clientes(cedula_hash)
        )
    ''')
    
    # Crear tabla de items del pedido (productos en cada factura)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            notas TEXT,
            FOREIGN KEY (factura_id) REFERENCES facturas(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicializar la base de datos al importar el módulo
init_db()

# === FUNCIÓN PARA CREAR UNA FACTURA/PEDIDO ===
def crear_pedido(cedula_cliente: str, productos: List[Dict], descripcion: str = "") -> Optional[int]:
    """
    Crea un nuevo pedido/factura en el sistema.
    
    Args:
        cedula_cliente: Cédula del cliente (sin hashear)
        productos: Lista de diccionarios con {'producto_id': int, 'cantidad': int, 'notas': str}
        descripcion: Descripción general del pedido
    
    Returns:
        ID del pedido creado o None si hay error
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar que el cliente existe (buscando por cédula)
        cursor.execute('''
            SELECT cedula_hash FROM clientes 
            WHERE cedula_hash IN (
                SELECT cedula_hash FROM clientes 
                WHERE cedula_hash = ? OR id IN (
                    SELECT id FROM clientes WHERE cedula_hash = ?
                )
            )
        ''', (cedula_cliente, cedula_cliente))
        
        cliente = cursor.fetchone()
        if not cliente:
            print("❌ Cliente no encontrado.")
            return None
        
        # Calcular precio total y verificar productos
        precio_total = 0
        items_validos = []
        
        for producto in productos:
            cursor.execute('''
                SELECT id, nombre, precio, disponible FROM productos 
                WHERE id = ? AND disponible = 1
            ''', (producto['producto_id'],))
            
            producto_info = cursor.fetchone()
            if not producto_info:
                print(f"❌ Producto ID {producto['producto_id']} no disponible o no encontrado.")
                return None
            
            precio_unitario = producto_info[2]
            cantidad = producto['cantidad']
            precio_total += precio_unitario * cantidad
            
            items_validos.append({
                'producto_id': producto['producto_id'],
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'notas': producto.get('notas', '')
            })
        
        # Insertar la factura
        cursor.execute('''
            INSERT INTO facturas (precio_total, descripcion, cedula_cliente, estado)
            VALUES (?, ?, ?, 'Pedido')
        ''', (precio_total, descripcion, cedula_cliente))
        
        factura_id = cursor.lastrowid
        
        # Insertar los items del pedido
        for item in items_validos:
            cursor.execute('''
                INSERT INTO items_pedido (factura_id, producto_id, cantidad, precio_unitario, notas)
                VALUES (?, ?, ?, ?, ?)
            ''', (factura_id, item['producto_id'], item['cantidad'], item['precio_unitario'], item['notas']))
        
        conn.commit()
        print(f"✅ Pedido #{factura_id} creado correctamente. Total: ${precio_total:,.2f}")
        return factura_id
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error al crear pedido: {e}")
        return None
    finally:
        conn.close()

# === FUNCIÓN PARA OBTENER DETALLES DE UN PEDIDO ===
def obtener_pedido(pedido_id: int) -> Optional[Dict]:
    """
    Obtiene todos los detalles de un pedido específico.
    
    Returns:
        Diccionario con toda la información del pedido
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Obtener información de la factura
        cursor.execute('''
            SELECT f.id, f.precio_total, f.descripcion, f.cedula_cliente, 
                   f.fecha, f.estado, c.nombre as nombre_cliente
            FROM facturas f
            LEFT JOIN clientes c ON f.cedula_cliente = c.cedula_hash
            WHERE f.id = ?
        ''', (pedido_id,))
        
        factura = cursor.fetchone()
        if not factura:
            print("❌ Pedido no encontrado.")
            return None
        
        # Obtener items del pedido
        cursor.execute('''
            SELECT ip.id, ip.producto_id, p.nombre, ip.cantidad, 
                   ip.precio_unitario, ip.notas, (ip.cantidad * ip.precio_unitario) as subtotal
            FROM items_pedido ip
            JOIN productos p ON ip.producto_id = p.id
            WHERE ip.factura_id = ?
        ''', (pedido_id,))
        
        items = cursor.fetchall()
        
        # Construir respuesta
        pedido = {
            'id': factura[0],
            'precio_total': factura[1],
            'descripcion': factura[2],
            'cedula_cliente': factura[3],
            'fecha': factura[4],
            'estado': factura[5],
            'nombre_cliente': factura[6],
            'items': []
        }
        
        for item in items:
            pedido['items'].append({
                'item_id': item[0],
                'producto_id': item[1],
                'producto_nombre': item[2],
                'cantidad': item[3],
                'precio_unitario': item[4],
                'notas': item[5],
                'subtotal': item[6]
            })
        
        return pedido
        
    except Exception as e:
        print(f"❌ Error al obtener pedido: {e}")
        return None
    finally:
        conn.close()

# === FUNCIÓN PARA LISTAR TODOS LOS PEDIDOS ===
def listar_pedidos(estado: str = None) -> List[Dict]:
    """
    Lista todos los pedidos, opcionalmente filtrados por estado.
    
    Args:
        estado: Filtro por estado ('Pedido', 'Pagado', 'En envio', 'Enviado')
    
    Returns:
        Lista de diccionarios con información de pedidos
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if estado:
            cursor.execute('''
                SELECT f.id, f.precio_total, f.descripcion, f.cedula_cliente, 
                       f.fecha, f.estado, c.nombre as nombre_cliente
                FROM facturas f
                LEFT JOIN clientes c ON f.cedula_cliente = c.cedula_hash
                WHERE f.estado = ?
                ORDER BY f.fecha DESC
            ''', (estado,))
        else:
            cursor.execute('''
                SELECT f.id, f.precio_total, f.descripcion, f.cedula_cliente, 
                       f.fecha, f.estado, c.nombre as nombre_cliente
                FROM facturas f
                LEFT JOIN clientes c ON f.cedula_cliente = c.cedula_hash
                ORDER BY f.fecha DESC
            ''')
        
        pedidos = []
        for row in cursor.fetchall():
            pedido = {
                'id': row[0],
                'precio_total': row[1],
                'descripcion': row[2],
                'cedula_cliente': row[3],
                'fecha': row[4],
                'estado': row[5],
                'nombre_cliente': row[6]
            }
            pedidos.append(pedido)
        
        return pedidos
        
    except Exception as e:
        print(f"❌ Error al listar pedidos: {e}")
        return []
    finally:
        conn.close()

# === FUNCIÓN PARA ACTUALIZAR ESTADO DE PEDIDO ===
def actualizar_estado_pedido(pedido_id: int, nuevo_estado: str) -> bool:
    """
    Actualiza el estado de un pedido.
    
    Estados válidos: 'Pedido', 'Pagado', 'En envio', 'Enviado'
    """
    estados_validos = ['Pedido', 'Pagado', 'En envio', 'Enviado']
    
    if nuevo_estado not in estados_validos:
        print(f"❌ Estado inválido. Estados permitidos: {', '.join(estados_validos)}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE facturas SET estado = ? WHERE id = ?
        ''', (nuevo_estado, pedido_id))
        
        if cursor.rowcount == 0:
            print("❌ Pedido no encontrado.")
            return False
        
        conn.commit()
        print(f"✅ Estado del pedido #{pedido_id} actualizado a '{nuevo_estado}'")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error al actualizar estado: {e}")
        return False
    finally:
        conn.close()

# === FUNCIÓN PARA OBTENER PEDIDOS POR CLIENTE ===
def obtener_pedidos_cliente(cedula_cliente: str) -> List[Dict]:
    """
    Obtiene todos los pedidos de un cliente específico.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT f.id, f.precio_total, f.descripcion, f.fecha, f.estado
            FROM facturas f
            WHERE f.cedula_cliente = ?
            ORDER BY f.fecha DESC
        ''', (cedula_cliente,))
        
        pedidos = []
        for row in cursor.fetchall():
            pedido = {
                'id': row[0],
                'precio_total': row[1],
                'descripcion': row[2],
                'fecha': row[3],
                'estado': row[4]
            }
            pedidos.append(pedido)
        
        return pedidos
        
    except Exception as e:
        print(f"❌ Error al obtener pedidos del cliente: {e}")
        return []
    finally:
        conn.close()

# === FUNCIÓN PARA ELIMINAR PEDIDO ===
def eliminar_pedido(pedido_id: int) -> bool:
    """
    Elimina un pedido y todos sus items (usando CASCADE DELETE).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM facturas WHERE id = ?', (pedido_id,))
        
        if cursor.rowcount == 0:
            print("❌ Pedido no encontrado.")
            return False
        
        conn.commit()
        print(f"✅ Pedido #{pedido_id} eliminado correctamente.")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error al eliminar pedido: {e}")
        return False
    finally:
        conn.close()

# === FUNCIÓN PARA IMPRIMIR DETALLES DE PEDIDO ===
def imprimir_pedido(pedido_id: int):
    """
    Imprime en consola los detalles completos de un pedido de forma legible.
    """
    pedido = obtener_pedido(pedido_id)
    if not pedido:
        return
    
    print(f"\n{'='*50}")
    print(f"📋 DETALLES DEL PEDIDO #{pedido['id']}")
    print(f"{'='*50}")
    print(f"👤 Cliente: {pedido.get('nombre_cliente', 'N/A')}")
    print(f"📅 Fecha: {pedido['fecha']}")
    print(f"📊 Estado: {pedido['estado']}")
    print(f"📝 Descripción: {pedido['descripcion'] or 'Ninguna'}")
    print(f"{'-'*50}")
    print("🛒 PRODUCTOS:")
    
    for item in pedido['items']:
        print(f"  • {item['producto_nombre']}")
        print(f"    Cantidad: {item['cantidad']} x ${item['precio_unitario']:,.2f} = ${item['subtotal']:,.2f}")
        if item['notas']:
            print(f"    Notas: {item['notas']}")
        print()
    
    print(f"💰 TOTAL: ${pedido['precio_total']:,.2f}")
    print(f"{'='*50}\n")

# === PRUEBA DEL MÓDULO ===
if __name__ == "__main__":
    # Ejemplos de uso
    print("=== PRUEBA SISTEMA DE PEDIDOS ===")
    
    # Crear un pedido de ejemplo
    productos_ejemplo = [
        {'producto_id': 1, 'cantidad': 2, 'notas': 'Sin cebolla'},
        {'producto_id': 3, 'cantidad': 1, 'notas': ''},
        {'producto_id': 7, 'cantidad': 3, 'notas': 'Sin hielo'}
    ]
    
    # Crear pedido
    pedido_id = crear_pedido(
        cedula_cliente="123456789",  # Cédula del cliente
        productos=productos_ejemplo,
        descripcion="Pedido para llevar"
    )
    
    if pedido_id:
        # Imprimir detalles
        imprimir_pedido(pedido_id)
        
        # Listar todos los pedidos
        print("📦 TODOS LOS PEDIDOS:")
        pedidos = listar_pedidos()
        for pedido in pedidos:
            print(f"  - Pedido #{pedido['id']}: ${pedido['precio_total']:,.2f} - {pedido['estado']}")
        
        # Actualizar estado
        actualizar_estado_pedido(pedido_id, "Pagado")
        
        # Imprimir nuevamente para ver cambios
        imprimir_pedido(pedido_id)