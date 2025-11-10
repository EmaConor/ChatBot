# datosEjemplo.py
import sqlite3
import os
import hashlib
import uuid
from typing import List, Dict
from datetime import datetime, timedelta

# === CONFIGURACIÓN DE LA BASE DE DATOS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "MezonPeruano.db")

# === DATOS DE EJEMPLO ===

# Clientes de ejemplo
CLIENTES_EJEMPLO = [
    {"nombre": "Juan Pérez", "numero": "573001234567", "direccion": "Calle 123 #45-67", "cedula": "1001234567"},
    {"nombre": "María García", "numero": "573002345678", "direccion": "Avenida Principal #78-90", "cedula": "1002345678"},
    {"nombre": "Carlos López", "numero": "573003456789", "direccion": "Carrera 56 #12-34", "cedula": "1003456789"},
    {"nombre": "Ana Martínez", "numero": "573004567890", "direccion": "Diagonal 78 #56-12", "cedula": "1004567890"},
    {"nombre": "Pedro Rodríguez", "numero": "573005678901", "direccion": "Transversal 34 #67-89", "cedula": "1005678901"},
    {"nombre": "Laura González", "numero": "573006789012", "direccion": "Calle 90 #23-45", "cedula": "1006789012"},
    {"nombre": "Diego Hernández", "numero": "573007890123", "direccion": "Avenida Central #11-22", "cedula": "1007890123"},
    {"nombre": "Sofia Díaz", "numero": "573008901234", "direccion": "Carrera 33 #44-55", "cedula": "1008901234"},
    {"nombre": "Miguel Torres", "numero": "573009012345", "direccion": "Calle 66 #77-88", "cedula": "1009012345"},
    {"nombre": "Elena Ramírez", "numero": "573010123456", "direccion": "Avenida Norte #99-00", "cedula": "1010123456"}
]

# Productos de ejemplo (adicionales a los que ya tienes)
PRODUCTOS_EJEMPLO = [
    {"nombre": "Anticuchos", "descripcion": "Brochetas de corazón de res marinadas", "precio": 18000, "categoria": "Entrada"},
    {"nombre": "Rocoto Relleno", "descripcion": "Rocoto relleno de carne y queso", "precio": 22000, "categoria": "Plato Fuerte"},
    {"nombre": "Pisco Sour", "descripcion": "Coctel tradicional peruano", "precio": 15000, "categoria": "Bebida"},
    {"nombre": "Arroz con Mariscos", "descripcion": "Arroz con mix de mariscos frescos", "precio": 35000, "categoria": "Plato Fuerte"},
    {"nombre": "Picarones", "descripcion": "Rosquillas de camote con miel de chancaca", "precio": 12000, "categoria": "Postre"}
]

# Menú de ejemplo (para la tabla menu)
MENU_EJEMPLO = [
    {"nombre": "Menú Ejecutivo", "precio": 25000},
    {"nombre": "Menú Vegetariano", "precio": 22000},
    {"nombre": "Menú Infantil", "precio": 18000},
    {"nombre": "Menú Especial", "precio": 35000},
    {"nombre": "Menú Degustación", "precio": 45000}
]

# Estados posibles para los pedidos
ESTADOS_PEDIDO = ['Pedido', 'Pagado', 'En envio', 'Enviado']

# === FUNCIÓN PARA HASHEAR LA CÉDULA ===
def hash_cedula(cedula: str, salt: str = None):
    if not salt:
        salt = uuid.uuid4().hex
    hash_obj = hashlib.sha256((cedula + salt).encode("utf-8"))
    return hash_obj.hexdigest(), salt

# === FUNCIÓN PARA INSERTAR CLIENTES DE EJEMPLO ===
def insertar_clientes_ejemplo():
    """Inserta clientes de ejemplo en la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    clientes_insertados = 0
    
    for cliente in CLIENTES_EJEMPLO:
        try:
            # Verificar si ya existe un cliente con ese número
            cursor.execute("SELECT id FROM clientes WHERE numero = ?", (cliente["numero"],))
            if cursor.fetchone():
                continue
            
            cedula_hash, salt = hash_cedula(cliente["cedula"])
            
            cursor.execute('''
                INSERT INTO clientes (nombre, numero, direccion, cedula_hash, salt)
                VALUES (?, ?, ?, ?, ?)
            ''', (cliente["nombre"], cliente["numero"], cliente["direccion"], cedula_hash, salt))
            
            clientes_insertados += 1
            
        except sqlite3.IntegrityError:
            continue
    
    conn.commit()
    conn.close()
    
    print(f"✅ {clientes_insertados} clientes de ejemplo insertados correctamente.")
    return clientes_insertados

# === FUNCIÓN PARA INSERTAR PRODUCTOS DE EJEMPLO ===
def insertar_productos_ejemplo():
    """Inserta productos de ejemplo en la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    productos_insertados = 0
    
    for producto in PRODUCTOS_EJEMPLO:
        try:
            # Verificar si ya existe un producto con ese nombre
            cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto["nombre"],))
            if cursor.fetchone():
                continue
            
            cursor.execute('''
                INSERT INTO productos (nombre, descripcion, precio, categoria, disponible)
                VALUES (?, ?, ?, ?, 1)
            ''', (producto["nombre"], producto["descripcion"], producto["precio"], producto["categoria"]))
            
            productos_insertados += 1
            
        except sqlite3.IntegrityError:
            continue
    
    conn.commit()
    conn.close()
    
    print(f"✅ {productos_insertados} productos de ejemplo insertados correctamente.")
    return productos_insertados

# === FUNCIÓN PARA INSERTAR MENÚ DE EJEMPLO ===
def insertar_menu_ejemplo():
    """Inserta menús de ejemplo en la tabla menu"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    menus_insertados = 0
    
    for menu in MENU_EJEMPLO:
        try:
            # Verificar si ya existe un menú con ese nombre
            cursor.execute("SELECT id FROM menu WHERE nombre = ?", (menu["nombre"],))
            if cursor.fetchone():
                continue
            
            cursor.execute('''
                INSERT INTO menu (nombre, precio)
                VALUES (?, ?)
            ''', (menu["nombre"], menu["precio"]))
            
            menus_insertados += 1
            
        except sqlite3.IntegrityError:
            continue
    
    conn.commit()
    conn.close()
    
    print(f"✅ {menus_insertados} menús de ejemplo insertados correctamente.")
    return menus_insertados

# === FUNCIÓN PARA INSERTAR FACTURAS Y ITEMS DE EJEMPLO ===
def insertar_pedidos_completos_ejemplo():
    """Inserta pedidos completos de ejemplo (facturas + items_pedido)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    facturas_insertadas = 0
    items_insertados = 0
    
    try:
        # Obtener todos los clientes disponibles
        cursor.execute("SELECT cedula_hash FROM clientes")
        clientes_db = cursor.fetchall()
        
        if not clientes_db:
            print("❌ No hay clientes en la base de datos para crear pedidos.")
            return {"facturas": 0, "items": 0}
        
        # Obtener todos los productos disponibles
        cursor.execute("SELECT id, precio FROM productos WHERE disponible = 1")
        productos_db = cursor.fetchall()
        
        if not productos_db:
            print("❌ No hay productos disponibles en la base de datos.")
            return {"facturas": 0, "items": 0}
        
        # Crear 8 pedidos de ejemplo con diferentes estados y fechas
        for i in range(8):
            # Seleccionar un cliente aleatorio
            cliente_cedula = clientes_db[i % len(clientes_db)][0]
            
            # Crear descripción y estado
            descripciones = [
                "Pedido para llevar",
                "Almuerzo familiar",
                "Cena ejecutiva", 
                "Pedido a domicilio",
                "Celebración especial",
                "Reunión de amigos",
                "Pedido rápido",
                "Cena romántica"
            ]
            
            estado = ESTADOS_PEDIDO[i % len(ESTADOS_PEDIDO)]
            descripcion = descripciones[i % len(descripciones)]
            
            # Crear fecha con variación (algunos pedidos más recientes, otros más antiguos)
            fecha_base = datetime.now() - timedelta(days=(7 - i))
            fecha_str = fecha_base.strftime("%Y-%m-%d %H:%M:%S")
            
            # Seleccionar 2-4 productos aleatorios para este pedido
            num_productos = (i % 3) + 2  # Entre 2 y 4 productos
            productos_pedido = []
            precio_total = 0
            
            for j in range(num_productos):
                producto_idx = (i + j) % len(productos_db)
                producto_id, precio_unitario = productos_db[producto_idx]
                cantidad = (j % 2) + 1  # 1 o 2 unidades
                subtotal = precio_unitario * cantidad
                precio_total += subtotal
                
                notas_posibles = ["", "Sin picante", "Poco sal", "Bien cocido", "Para llevar"]
                notas = notas_posibles[j % len(notas_posibles)]
                
                productos_pedido.append({
                    'producto_id': producto_id,
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'notas': notas,
                    'subtotal': subtotal
                })
            
            # Insertar la factura con fecha personalizada
            cursor.execute('''
                INSERT INTO facturas (precio_total, descripcion, cedula_cliente, estado, fecha)
                VALUES (?, ?, ?, ?, ?)
            ''', (precio_total, descripcion, cliente_cedula, estado, fecha_str))
            
            factura_id = cursor.lastrowid
            facturas_insertadas += 1
            
            # Insertar los items del pedido
            for item in productos_pedido:
                cursor.execute('''
                    INSERT INTO items_pedido (factura_id, producto_id, cantidad, precio_unitario, notas)
                    VALUES (?, ?, ?, ?, ?)
                ''', (factura_id, item['producto_id'], item['cantidad'], item['precio_unitario'], item['notas']))
                
                items_insertados += 1
        
        conn.commit()
        print(f"✅ {facturas_insertadas} facturas y {items_insertados} items de pedido insertados correctamente.")
        
        return {
            "facturas": facturas_insertadas,
            "items": items_insertados
        }
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error al insertar pedidos completos: {e}")
        return {"facturas": 0, "items": 0}
    finally:
        conn.close()

# === FUNCIÓN PARA CARGAR TODOS LOS DATOS DE EJEMPLO ===
def cargar_datos_ejemplo():
    """Carga todos los datos de ejemplo en la base de datos"""
    print("🔄 Cargando datos de ejemplo...")
    
    total_clientes = insertar_clientes_ejemplo()
    total_productos = insertar_productos_ejemplo()
    total_menus = insertar_menu_ejemplo()
    pedidos_result = insertar_pedidos_completos_ejemplo()
    
    print(f"\n📊 RESUMEN DE DATOS CARGADOS:")
    print(f"   👥 Clientes: {total_clientes}")
    print(f"   🍽️  Productos: {total_productos}")
    print(f"   📋 Menús: {total_menus}")
    print(f"   📦 Facturas: {pedidos_result['facturas']}")
    print(f"   🛒 Items de pedido: {pedidos_result['items']}")
    print(f"   💾 Total registros: {total_clientes + total_productos + total_menus + pedidos_result['facturas'] + pedidos_result['items']}")
    
    return {
        "clientes": total_clientes,
        "productos": total_productos,
        "menus": total_menus,
        "facturas": pedidos_result['facturas'],
        "items_pedido": pedidos_result['items']
    }

# === FUNCIÓN PARA ELIMINAR DATOS DE EJEMPLO ===
def eliminar_datos_ejemplo():
    """Elimina todos los datos de ejemplo de la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Contadores para el resumen
    clientes_eliminados = 0
    productos_eliminados = 0
    menus_eliminados = 0
    facturas_eliminadas = 0
    items_eliminados = 0
    
    try:
        # Eliminar items_pedido de ejemplo (primero para evitar problemas de FK)
        cursor.execute('''
            DELETE FROM items_pedido 
            WHERE factura_id IN (
                SELECT f.id FROM facturas f 
                WHERE f.descripcion IN (
                    'Pedido para llevar', 'Almuerzo familiar', 'Cena ejecutiva', 
                    'Pedido a domicilio', 'Celebración especial', 'Reunión de amigos',
                    'Pedido rápido', 'Cena romántica'
                )
            )
        ''')
        items_eliminados = cursor.rowcount
        
        # Eliminar facturas de ejemplo
        cursor.execute('''
            DELETE FROM facturas 
            WHERE descripcion IN (
                'Pedido para llevar', 'Almuerzo familiar', 'Cena ejecutiva', 
                'Pedido a domicilio', 'Celebración especial', 'Reunión de amigos',
                'Pedido rápido', 'Cena romántica'
            )
        ''')
        facturas_eliminadas = cursor.rowcount
        
        # Eliminar productos de ejemplo
        for producto in PRODUCTOS_EJEMPLO:
            cursor.execute("DELETE FROM productos WHERE nombre = ?", (producto["nombre"],))
            if cursor.rowcount > 0:
                productos_eliminados += 1
        
        # Eliminar menús de ejemplo
        for menu in MENU_EJEMPLO:
            cursor.execute("DELETE FROM menu WHERE nombre = ?", (menu["nombre"],))
            if cursor.rowcount > 0:
                menus_eliminados += 1
        
        # Eliminar clientes de ejemplo
        for cliente in CLIENTES_EJEMPLO:
            cursor.execute("DELETE FROM clientes WHERE numero = ?", (cliente["numero"],))
            if cursor.rowcount > 0:
                clientes_eliminados += 1
        
        conn.commit()
        
        print(f"🗑️  DATOS DE EJEMPLO ELIMINADOS:")
        print(f"   👥 Clientes eliminados: {clientes_eliminados}")
        print(f"   🍽️  Productos eliminados: {productos_eliminados}")
        print(f"   📋 Menús eliminados: {menus_eliminados}")
        print(f"   📦 Facturas eliminadas: {facturas_eliminadas}")
        print(f"   🛒 Items eliminados: {items_eliminados}")
        print(f"   💾 Total: {clientes_eliminados + productos_eliminados + menus_eliminados + facturas_eliminadas + items_eliminados} registros")
        
        return {
            "clientes": clientes_eliminados,
            "productos": productos_eliminados,
            "menus": menus_eliminados,
            "facturas": facturas_eliminadas,
            "items_pedido": items_eliminados
        }
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error al eliminar datos de ejemplo: {e}")
        return None
    finally:
        conn.close()

# === FUNCIÓN PARA VER ESTADO ACTUAL ===
def ver_estado_actual():
    """Muestra el estado actual de la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Contar registros en cada tabla
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM productos")
        total_productos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM menu")
        total_menus = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM facturas")
        total_facturas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM items_pedido")
        total_items = cursor.fetchone()[0]
        
        # Obtener algunos datos adicionales para mostrar
        cursor.execute("SELECT estado, COUNT(*) FROM facturas GROUP BY estado")
        estados_pedidos = cursor.fetchall()
        
        cursor.execute("SELECT categoria, COUNT(*) FROM productos GROUP BY categoria")
        categorias_productos = cursor.fetchall()
        
        print(f"\n📊 ESTADO ACTUAL DE LA BASE DE DATOS:")
        print(f"   👥 Clientes registrados: {total_clientes}")
        print(f"   🍽️  Productos en menú: {total_productos}")
        print(f"   📋 Menús especiales: {total_menus}")
        print(f"   📦 Facturas/pedidos: {total_facturas}")
        print(f"   🛒 Items en pedidos: {total_items}")
        print(f"   💾 Total registros: {total_clientes + total_productos + total_menus + total_facturas + total_items}")
        
        if estados_pedidos:
            print(f"\n📈 ESTADOS DE PEDIDOS:")
            for estado, count in estados_pedidos:
                print(f"   - {estado}: {count}")
        
        if categorias_productos:
            print(f"\n🏷️  CATEGORÍAS DE PRODUCTOS:")
            for categoria, count in categorias_productos:
                print(f"   - {categoria}: {count}")
                
    except Exception as e:
        print(f"❌ Error al obtener estado actual: {e}")
    finally:
        conn.close()

# === FUNCIÓN PARA REINICIAR BASE DE DATOS COMPLETAMENTE ===
def reiniciar_base_datos():
    """Elimina y recrea todas las tablas (ADVERTENCIA: Esto borra TODOS los datos)"""
    confirmacion = input("⚠️  ¿Estás seguro? Esto borrará TODOS los datos (s/N): ")
    if confirmacion.lower() != 's':
        print("❌ Operación cancelada.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Eliminar todas las tablas
        cursor.execute("DROP TABLE IF EXISTS items_pedido")
        cursor.execute("DROP TABLE IF EXISTS facturas")
        cursor.execute("DROP TABLE IF EXISTS productos")
        cursor.execute("DROP TABLE IF EXISTS clientes")
        cursor.execute("DROP TABLE IF EXISTS menu")
        
        # Recrear las tablas (usando las definiciones originales)
        
        # Tabla de clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                numero TEXT UNIQUE NOT NULL,
                direccion TEXT NOT NULL,
                cedula_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
        ''')
        
        # Tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                descripcion TEXT NOT NULL,
                precio INTEGER NOT NULL,
                categoria TEXT NOT NULL,
                disponible INTEGER DEFAULT 1
            )
        ''')
        
        # Tabla de facturas (pedidos)
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
        
        # Tabla de items del pedido
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
        
        # Tabla de menú (mantenida por compatibilidad)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL
            )
        ''')
        
        conn.commit()
        print("✅ Base de datos reiniciada completamente.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error al reiniciar base de datos: {e}")
    finally:
        conn.close()

# === FUNCIÓN PARA VER DETALLES DE PEDIDOS DE EJEMPLO ===
def ver_pedidos_ejemplo():
    """Muestra los pedidos de ejemplo existentes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT f.id, f.precio_total, f.descripcion, f.estado, f.fecha, c.nombre
            FROM facturas f
            JOIN clientes c ON f.cedula_cliente = c.cedula_hash
            WHERE f.descripcion IN (
                'Pedido para llevar', 'Almuerzo familiar', 'Cena ejecutiva', 
                'Pedido a domicilio', 'Celebración especial', 'Reunión de amigos',
                'Pedido rápido', 'Cena romántica'
            )
            ORDER BY f.fecha DESC
        ''')
        
        pedidos = cursor.fetchall()
        
        if pedidos:
            print(f"\n📦 PEDIDOS DE EJEMPLO ENCONTRADOS ({len(pedidos)}):")
            for pedido in pedidos:
                print(f"   - Pedido #{pedido[0]}: {pedido[2]} | ${pedido[1]:,} | {pedido[3]} | {pedido[4]} | Cliente: {pedido[5]}")
        else:
            print("📭 No se encontraron pedidos de ejemplo.")
            
    except Exception as e:
        print(f"❌ Error al obtener pedidos de ejemplo: {e}")
    finally:
        conn.close()

# === MENÚ PRINCIPAL ===
if __name__ == "__main__":
    print("=" * 50)
    print("      GESTOR DE DATOS DE EJEMPLO")
    print("         RESTAURANTE MEZÓN PERUANO")
    print("=" * 50)
    
    while True:
        print("\n📋 OPCIONES DISPONIBLES:")
        print("1. Cargar datos de ejemplo")
        print("2. Eliminar datos de ejemplo")
        print("3. Ver estado actual")
        print("4. Ver pedidos de ejemplo")
        print("5. Reiniciar base de datos completa (¡CUIDADO!)")
        print("6. Salir")
        
        opcion = input("\nSelecciona una opción (1-6): ").strip()
        
        if opcion == "1":
            cargar_datos_ejemplo()
        elif opcion == "2":
            eliminar_datos_ejemplo()
        elif opcion == "3":
            ver_estado_actual()
        elif opcion == "4":
            ver_pedidos_ejemplo()
        elif opcion == "5":
            reiniciar_base_datos()
        elif opcion == "6":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción no válida. Por favor, selecciona 1-6.")