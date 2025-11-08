from tinydb import TinyDB, Query
import os

# === CONFIGURACIÓN DE LA BASE DE DATOS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "Productos.json")  # misma base usada por clientes
db = TinyDB(DB_PATH)

productos_table = db.table("productos")


# === FUNCIÓN PARA AGREGAR PRODUCTOS ===
def agregar_producto(nombre: str, descripcion: str, precio: int, categoria: str):
    """
    Agrega un producto nuevo al menú si no existe otro con el mismo nombre.
    """
    Producto = Query()
    existente = productos_table.get(Producto.nombre == nombre)
    if existente:
        print(f"⚠️ Ya existe el producto '{nombre}'.")
        return False

    nuevo_id = len(productos_table) + 1
    productos_table.insert({
        "id": nuevo_id,
        "nombre": nombre,
        "descripcion": descripcion,
        "precio": precio,
        "categoria": categoria,
        "Disponible": 1
    })

    print(f"✅ Producto '{nombre}' agregado correctamente.")
    return True


# === FUNCIÓN PARA LISTAR PRODUCTOS ===
def listar_productos():
    """
    Muestra todos los productos registrados en el menú, indicando su disponibilidad (1 = disponible, 0 = no disponible).
    """
    productos = productos_table.all()
    if not productos:
        print("📭 No hay productos registrados.")
        return []

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
    Producto = Query()
    producto = productos_table.get(Producto.nombre == nombre)
    if producto:
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
    Producto = Query()
    producto = productos_table.get(Producto.id == producto_id)
    if producto:
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
    Producto = Query()
    eliminado = productos_table.remove(Producto.nombre == nombre)
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
    if len(productos_table) > 0:
        print("ℹ️ El menú ya está cargado.")
        return

    menu_inicial = [
        {"nombre": "Ceviche Peruano", "descripcion": "Pescado fresco marinado en limón, con cebolla y cilantro.", "precio": 25000, "categoria": "Entrada", "Disponible":1},
        {"nombre": "Lomo Saltado", "descripcion": "Carne salteada con cebolla, tomate y papas fritas.", "precio": 32000, "categoria": "Plato Fuerte", "Disponible":1},
        {"nombre": "Ají de Gallina", "descripcion": "Pechuga de pollo desmenuzada en salsa de ají amarillo y leche.", "precio": 28000, "categoria": "Plato Fuerte", "Disponible":1},
        {"nombre": "Papa a la Huancaína", "descripcion": "Papas con salsa cremosa de ají amarillo, queso y leche.", "precio": 18000, "categoria": "Entrada", "Disponible":1},
        {"nombre": "Tallarines Verdes", "descripcion": "Pasta en salsa de albahaca y queso fresco.", "precio": 27000, "categoria": "Plato Fuerte", "Disponible":1},
        {"nombre": "Arroz Chaufa", "descripcion": "Arroz frito peruano con pollo, cebolla y huevo.", "precio": 29000, "categoria": "Plato Fuerte", "Disponible":1},
        {"nombre": "Chicha Morada", "descripcion": "Bebida tradicional de maíz morado con frutas y canela.", "precio": 8000, "categoria": "Bebida", "Disponible":1},
        {"nombre": "Suspiro Limeño", "descripcion": "Postre dulce de manjar blanco con merengue.", "precio": 12000, "categoria": "Postre", "Disponible":1},
        {"nombre": "Inca Kola", "descripcion": "Refresco peruano sabor vainilla.", "precio": 6000, "categoria": "Bebida", "Disponible":1},
        {"nombre": "Causa Limeña", "descripcion": "Puré de papa amarilla relleno con pollo y palta.", "precio": 20000, "categoria": "Entrada", "Disponible":1}
    ]

    for p in menu_inicial:
        agregar_producto(p["nombre"], p["descripcion"], p["precio"], p["categoria"])

    print("✅ Menú inicial cargado correctamente.")


# === FUNCIÓN PARA OBTENER PRODUCTOS POR CATEGORÍA ===
def obtener_por_categoria(categoria: str):
    """
    Obtiene todos los productos de una categoría específica.
    """
    Producto = Query()
    productos = productos_table.search(Producto.categoria == categoria)
    return productos
# === FUNCIÓN PARA OBTENER PRODUCTOS POR DISPONIBLES ===
def obtener_disponible():
    """
    Obtiene todos los productos que hayan disponibles.
    """
    Producto = Query()
    productos = productos_table.search(Producto.Disponible == 1)
    for p in productos:
        print(f" - {p['nombre']} | ${p['precio']} | {p['categoria']}")
    return productos
# === FUNCION PARA CAMBIAR DISPONIBILIDAD DE PRODUCTOS ===
def cambiar_disponibilidad(producto_id: int = None, nombre: str = None, disponible: int = 1):
    """
    Cambia la disponibilidad de un producto (1 = disponible, 0 = no disponible)
    Se puede buscar por 'producto_id' o por 'nombre'.
    """
    Producto = Query()

    if producto_id is not None:
        producto = productos_table.get(Producto.id == producto_id)
    elif nombre is not None:
        producto = productos_table.get(Producto.nombre == nombre)
    else:
        print("⚠️ Debes indicar el 'producto_id' o el 'nombre' del producto.")
        return False

    if not producto:
        print("❌ Producto no encontrado.")
        return False

    productos_table.update({"Disponible": disponible}, Producto.id == producto["id"])
    estado = "🟢 Disponible" if disponible == 1 else "🔴 No disponible"
    print(f"✅ El producto '{producto['nombre']}' ahora está {estado}.")
    return True

# === PRUEBA DEL MÓDULO ===
if __name__ == "__main__":
    #print("=== PRUEBA DE MENÚ ===")
    #cargar_menu_inicial()
    #listar_productos()
    #buscar_producto("Lomo Saltado")
    #cambiar_disponibilidad(None,"Ceviche Peruano",0)
    listar_productos()
    obtener_disponible()