from tinydb import TinyDB, Query
import hashlib, uuid, os

# === CONFIGURACIÓN DE LA BASE DE DATOS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "clientes.json")  # misma base usada por clientes
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
        "categoria": categoria
    })

    print(f"✅ Producto '{nombre}' agregado correctamente.")
    return True


# === FUNCIÓN PARA LISTAR PRODUCTOS ===
def listar_productos():
    """
    Muestra todos los productos registrados en el menú.
    """
    productos = productos_table.all()
    if not productos:
        print("📭 No hay productos registrados.")
        return []

    print("\n📋 MENÚ DEL RESTAURANTE:")
    for p in productos:
        print(f" - {p['nombre']} | ${p['precio']} | {p['categoria']}")
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
        {"nombre": "Ceviche Peruano", "descripcion": "Pescado fresco marinado en limón, con cebolla y cilantro.", "precio": 25000, "categoria": "Entrada"},
        {"nombre": "Lomo Saltado", "descripcion": "Carne salteada con cebolla, tomate y papas fritas.", "precio": 32000, "categoria": "Plato Fuerte"},
        {"nombre": "Ají de Gallina", "descripcion": "Pechuga de pollo desmenuzada en salsa de ají amarillo y leche.", "precio": 28000, "categoria": "Plato Fuerte"},
        {"nombre": "Papa a la Huancaína", "descripcion": "Papas con salsa cremosa de ají amarillo, queso y leche.", "precio": 18000, "categoria": "Entrada"},
        {"nombre": "Tallarines Verdes", "descripcion": "Pasta en salsa de albahaca y queso fresco.", "precio": 27000, "categoria": "Plato Fuerte"},
        {"nombre": "Arroz Chaufa", "descripcion": "Arroz frito peruano con pollo, cebolla y huevo.", "precio": 29000, "categoria": "Plato Fuerte"},
        {"nombre": "Chicha Morada", "descripcion": "Bebida tradicional de maíz morado con frutas y canela.", "precio": 8000, "categoria": "Bebida"},
        {"nombre": "Suspiro Limeño", "descripcion": "Postre dulce de manjar blanco con merengue.", "precio": 12000, "categoria": "Postre"},
        {"nombre": "Inca Kola", "descripcion": "Refresco peruano sabor vainilla.", "precio": 6000, "categoria": "Bebida"},
        {"nombre": "Causa Limeña", "descripcion": "Puré de papa amarilla relleno con pollo y palta.", "precio": 20000, "categoria": "Entrada"}
    ]

    for p in menu_inicial:
        agregar_producto(p["nombre"], p["descripcion"], p["precio"], p["categoria"])

    print("✅ Menú inicial cargado correctamente.")


# === PRUEBA DEL MÓDULO ===
if __name__ == "__main__":
    print("=== PRUEBA DE MENÚ ===")
    cargar_menu_inicial()
    listar_productos()
    buscar_producto("Lomo Saltado")
