import sqlite3
import os

# === CONFIGURACIÓN DE LA BASE DE DATOS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "MezonPeruano.db")  # misma base de datos que clientes

# === INICIALIZACIÓN DE LA BASE DE DATOS ===
def init_db():
    """Inicializa la base de datos y crea la tabla de productos si no existe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tabla de productos
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
    
    conn.commit()
    conn.close()

# Inicializar la base de datos al importar el módulo
init_db()

# === FUNCIÓN PARA AGREGAR PRODUCTOS ===
def agregar_producto(nombre: str, descripcion: str, precio: int, categoria: str):
    """
    Agrega un producto nuevo al menú si no existe otro con el mismo nombre.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar si ya existe un producto con ese nombre
        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (nombre,))
        existente = cursor.fetchone()
        if existente:
            print(f"⚠️ Ya existe el producto '{nombre}'.")
            return False

        # Insertar nuevo producto (el id se autoincrementa)
        cursor.execute('''
            INSERT INTO productos (nombre, descripcion, precio, categoria, disponible)
            VALUES (?, ?, ?, ?, ?)
        ''', (nombre, descripcion, precio, categoria, 1))
        
        conn.commit()
        print(f"✅ Producto '{nombre}' agregado correctamente.")
        return True
        
    except sqlite3.IntegrityError:
        print(f"⚠️ Ya existe el producto '{nombre}'.")
        return False
    finally:
        conn.close()

# === FUNCIÓN PARA LISTAR PRODUCTOS ===
def listar_productos():
    """
    Muestra todos los productos registrados en el menú, indicando su disponibilidad (1 = disponible, 0 = no disponible).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, descripcion, precio, categoria, disponible 
        FROM productos ORDER BY id
    ''')
    
    resultados = cursor.fetchall()
    conn.close()
    
    if not resultados:
        print("📭 No hay productos registrados.")
        return []

    # Convertir a lista de diccionarios para mantener compatibilidad
    productos = []
    for resultado in resultados:
        producto = {
            "id": resultado[0],
            "nombre": resultado[1],
            "descripcion": resultado[2],
            "precio": resultado[3],
            "categoria": resultado[4],
            "Disponible": resultado[5]
        }
        productos.append(producto)

    print(f"\n📋 MENÚ DEL RESTAURANTE ({len(productos)} productos):")
    for p in productos:
        disponible = p.get("Disponible", 0)
        estado = "🟢 Disponible (1)" if disponible == 1 else "🔴 No disponible (0)"
        print(f" - {p['nombre']} | ${p['precio']} | {p['categoria']} | {estado}")
    print()
    return productos

# === FUNCIÓN PARA BUSCAR UN PRODUCTO POR NOMBRE ===
def buscar_producto(nombre: str):
    """
    Busca un producto por su nombre.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, descripcion, precio, categoria, disponible 
        FROM productos WHERE nombre = ?
    ''', (nombre,))
    
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        producto = {
            "id": resultado[0],
            "nombre": resultado[1],
            "descripcion": resultado[2],
            "precio": resultado[3],
            "categoria": resultado[4],
            "Disponible": resultado[5]
        }
        print(f"🔎 Producto encontrado: {producto['nombre']} - ${producto['precio']} ({producto['categoria']})")
        return producto
    else:
        print("❌ Producto no encontrado.")
        return None

# === FUNCIÓN PARA BUSCAR UN PRODUCTO POR ID ===
def buscar_producto_por_id(producto_id: int):
    """
    Busca un producto por su ID.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, descripcion, precio, categoria, disponible 
        FROM productos WHERE id = ?
    ''', (producto_id,))
    
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        producto = {
            "id": resultado[0],
            "nombre": resultado[1],
            "descripcion": resultado[2],
            "precio": resultado[3],
            "categoria": resultado[4],
            "Disponible": resultado[5]
        }
        print(f"🔎 Producto encontrado: {producto['nombre']} - ${producto['precio']}")
        return producto
    else:
        print("❌ Producto no encontrado.")
        return None

# === FUNCIÓN PARA ELIMINAR UN PRODUCTO ===
def eliminar_producto(nombre: str):
    """
    Elimina un producto del menú por su nombre.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM productos WHERE nombre = ?", (nombre,))
    eliminado = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    if eliminado:
        print(f"🗑️ Producto '{nombre}' eliminado correctamente.")
        return True
    else:
        print("❌ No se encontró ningún producto con ese nombre.")
        return False

# === CARGAR MENÚ INICIAL ===
def cargar_menu_inicial():
    """
    Carga los productos del menú si la base está vacía.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM productos")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count > 0:
        print("ℹ️ El menú ya está cargado.")
        return

    menu_inicial = [
        {"nombre": "Ceviche Peruano", "descripcion": "Pescado fresco marinado en limón, con cebolla y cilantro.", "precio": 25000, "categoria": "Entrada", "Disponible": 1},
        {"nombre": "Lomo Saltado", "descripcion": "Carne salteada con cebolla, tomate y papas fritas.", "precio": 32000, "categoria": "Plato Fuerte", "Disponible": 1},
        {"nombre": "Ají de Gallina", "descripcion": "Pechuga de pollo desmenuzada en salsa de ají amarillo y leche.", "precio": 28000, "categoria": "Plato Fuerte", "Disponible": 1},
        {"nombre": "Papa a la Huancaína", "descripcion": "Papas con salsa cremosa de ají amarillo, queso y leche.", "precio": 18000, "categoria": "Entrada", "Disponible": 1},
        {"nombre": "Tallarines Verdes", "descripcion": "Pasta en salsa de albahaca y queso fresco.", "precio": 27000, "categoria": "Plato Fuerte", "Disponible": 1},
        {"nombre": "Arroz Chaufa", "descripcion": "Arroz frito peruano con pollo, cebolla y huevo.", "precio": 29000, "categoria": "Plato Fuerte", "Disponible": 1},
        {"nombre": "Chicha Morada", "descripcion": "Bebida tradicional de maíz morado con frutas y canela.", "precio": 8000, "categoria": "Bebida", "Disponible": 1},
        {"nombre": "Suspiro Limeño", "descripcion": "Postre dulce de manjar blanco con merengue.", "precio": 12000, "categoria": "Postre", "Disponible": 1},
        {"nombre": "Inca Kola", "descripcion": "Refresco peruano sabor vainilla.", "precio": 6000, "categoria": "Bebida", "Disponible": 1},
        {"nombre": "Causa Limeña", "descripcion": "Puré de papa amarilla relleno con pollo y palta.", "precio": 20000, "categoria": "Entrada", "Disponible": 1}
    ]

    for p in menu_inicial:
        agregar_producto(p["nombre"], p["descripcion"], p["precio"], p["categoria"])

    print("✅ Menú inicial cargado correctamente.")

# === FUNCIÓN PARA OBTENER PRODUCTOS POR CATEGORÍA ===
def obtener_productos_por_categoria(categoria: str):
    """
    Obtiene todos los productos de una categoría específica.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, descripcion, precio, categoria, disponible 
        FROM productos WHERE categoria = ? AND disponible = 1
    ''', (categoria,))
    
    resultados = cursor.fetchall()
    conn.close()
    
    # Convertir a lista de diccionarios para mantener compatibilidad
    productos = []
    for resultado in resultados:
        producto = {
            "id": resultado[0],
            "nombre": resultado[1],
            "descripcion": resultado[2],
            "precio": resultado[3],
            "categoria": resultado[4],
            "Disponible": resultado[5]
        }
        productos.append(producto)
    
    print(f"📂 Productos encontrados en categoría '{categoria}': {len(productos)}")
    return productos

# === FUNCIÓN PARA OBTENER PRODUCTOS DISPONIBLES ===
def obtener_disponible():
    """
    Obtiene todos los productos que hayan disponibles.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, descripcion, precio, categoria, disponible 
        FROM productos WHERE disponible = 1
    ''')
    
    resultados = cursor.fetchall()
    conn.close()
    
    # Convertir a lista de diccionarios para mantener compatibilidad
    productos = []
    for resultado in resultados:
        producto = {
            "id": resultado[0],
            "nombre": resultado[1],
            "descripcion": resultado[2],
            "precio": resultado[3],
            "categoria": resultado[4],
            "Disponible": resultado[5]
        }
        productos.append(producto)
    
    for p in productos:
        print(f" - {p['nombre']} | ${p['precio']} | {p['categoria']}")
    
    return productos

# === FUNCION PARA CAMBIAR DISPONIBILIDAD DE PRODUCTOS ===
def cambiar_disponibilidad(producto_id: int = None, nombre: str = None, disponible: int = 1):
    """
    Cambia la disponibilidad de un producto (1 = disponible, 0 = no disponible)
    Se puede buscar por 'producto_id' o por 'nombre'.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    producto = None
    
    if producto_id is not None:
        cursor.execute('''
            SELECT id, nombre, disponible FROM productos WHERE id = ?
        ''', (producto_id,))
        resultado = cursor.fetchone()
        if resultado:
            producto = {
                "id": resultado[0],
                "nombre": resultado[1],
                "Disponible": resultado[2]
            }
    elif nombre is not None:
        cursor.execute('''
            SELECT id, nombre, disponible FROM productos WHERE nombre = ?
        ''', (nombre,))
        resultado = cursor.fetchone()
        if resultado:
            producto = {
                "id": resultado[0],
                "nombre": resultado[1],
                "Disponible": resultado[2]
            }
    else:
        print("⚠️ Debes indicar el 'producto_id' o el 'nombre' del producto.")
        conn.close()
        return False

    if not producto:
        print("❌ Producto no encontrado.")
        conn.close()
        return False

    # Actualizar disponibilidad
    cursor.execute("UPDATE productos SET disponible = ? WHERE id = ?", 
                  (disponible, producto["id"]))
    conn.commit()
    conn.close()
    
    estado = "🟢 Disponible" if disponible == 1 else "🔴 No disponible"
    print(f"✅ El producto '{producto['nombre']}' ahora está {estado}.")
    return True

# === PRUEBA DEL MÓDULO ===
if __name__ == "__main__":
    #print("=== PRUEBA DE MENÚ ===")
    cargar_menu_inicial()
    listar_productos()
    buscar_producto("Lomo Saltado")
    cambiar_disponibilidad(None,"Ceviche Peruano",0)
    listar_productos()
    obtener_disponible()