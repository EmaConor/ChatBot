from tinydb import TinyDB, Query
import hashlib, uuid, os

# === CONFIGURACIÓN DE LA BASE DE DATOS ===
# El archivo se crea automáticamente en la misma carpeta del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "clientes.json")

db = TinyDB(DB_PATH)
clientes_table = db.table("clientes")
menu_table = db.table("menu")


# === FUNCIÓN PARA HASHEAR LA CÉDULA ===
def hash_cedula(cedula: str, salt: str = None):
    """
    Crea un hash SHA256 de la cédula con un salt único.
    Devuelve (hash, salt)
    """
    if not salt:
        salt = uuid.uuid4().hex
    hash_obj = hashlib.sha256((cedula + salt).encode("utf-8"))
    return hash_obj.hexdigest(), salt


# === FUNCIÓN PARA AGREGAR CLIENTES ===
def agregar_cliente(nombre: str, numero: str, direccion: str, cedula: str):
    """
    Agrega un nuevo cliente si el número no existe.
    Guarda la cédula de forma segura (hash + salt).
    """
    Cliente = Query()
    existente = clientes_table.get(Cliente.numero == numero)
    if existente:
        print("⚠️ Ya existe un cliente con ese número.")
        return False

    cedula_hash, salt = hash_cedula(cedula)
    nuevo_id = len(clientes_table) + 1

    clientes_table.insert({
        "id": nuevo_id,
        "nombre": nombre,
        "numero": numero,
        "direccion": direccion,
        "cedula_hash": cedula_hash,
        "salt": salt
    })

    print(f"✅ Cliente '{nombre}' agregado correctamente.")
    return True


# === FUNCIÓN PARA INICIAR SESIÓN ===
def iniciar_sesion(numero: str, cedula: str):
    """
    Verifica si el número y la cédula coinciden con los datos almacenados (hash + salt).
    """
    Cliente = Query()
    cliente = clientes_table.get(Cliente.numero == numero)

    if not cliente:
        print("❌ Número no encontrado.")
        return False

    # Verificar el hash con el salt guardado
    cedula_hash_verif = hashlib.sha256((cedula + cliente["salt"]).encode("utf-8")).hexdigest()
    if cedula_hash_verif == cliente["cedula_hash"]:
        print(f"✅ Inicio de sesión exitoso. Bienvenido, {cliente['nombre']}.")
        return True
    else:
        print("❌ Cédula incorrecta.")
        return False


# === FUNCIÓN PARA LISTAR TODOS LOS CLIENTES ===
def listar_clientes():
    """
    Devuelve y muestra todos los clientes almacenados.
    """
    clientes = clientes_table.all()
    if not clientes:
        print("📭 No hay clientes registrados.")
        return []

    print("\n📋 Lista de clientes:")
    for c in clientes:
        print(f" - ID: {c['id']} | Nombre: {c['nombre']} | Número: {c['numero']} | Dirección: {c['direccion']}")
    print()
    return clientes


# === FUNCIÓN PARA BUSCAR UN CLIENTE POR NÚMERO ===
def buscar_cliente(numero: str):
    """
    Busca un cliente por su número de celular.
    """
    Cliente = Query()
    cliente = clientes_table.get(Cliente.numero == numero)
    if cliente:
        print(f"🔎 Cliente encontrado: {cliente['nombre']} - Dirección: {cliente['direccion']}")
        return cliente
    else:
        print("❌ Cliente no encontrado.")
        return None


# === FUNCIÓN PARA ELIMINAR UN CLIENTE ===
def eliminar_cliente(numero: str):
    """
    Elimina un cliente de la base de datos por su número.
    """
    Cliente = Query()
    eliminado = clientes_table.remove(Cliente.numero == numero)
    if eliminado:
        print(f"🗑️ Cliente con número {numero} eliminado correctamente.")
        return True
    else:
        print("❌ No se encontró ningún cliente con ese número.")
        return False


# === PRUEBA DEL MÓDULO ===
if __name__ == "__main__":
    print("=== PRUEBA DE FUNCIONALIDAD ===")

    # Agregar clientes
    agregar_cliente("Yoan Valdes", "3001234567", "Calle Nueva #8-10", "123456789")
    agregar_cliente("Laura Gómez", "3009876543", "Carrera 5 #9-20", "987654321")

    # Listar
    listar_clientes()

    # Buscar
    buscar_cliente("3009876543")

    # Iniciar sesión correcta
    iniciar_sesion("3009876543", "987654321")

    # Iniciar sesión incorrecta
    iniciar_sesion("3009876543", "000000000")

    # Eliminar
    #eliminar_cliente("3009876543")

    # Listar después de eliminar
    listar_clientes()
