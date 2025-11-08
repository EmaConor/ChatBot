from tinydb import TinyDB, Query
import hashlib, uuid, os

# === CONFIGURACIÓN DE LA BASE DE DATOS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "clientes.json")

db = TinyDB(DB_PATH)
clientes_table = db.table("clientes")
menu_table = db.table("menu")


# === FUNCIÓN PARA HASHEAR LA CÉDULA ===
def hash_cedula(cedula: str, salt: str = None):
    if not salt:
        salt = uuid.uuid4().hex
    hash_obj = hashlib.sha256((cedula + salt).encode("utf-8"))
    return hash_obj.hexdigest(), salt


# === FUNCIÓN PARA AGREGAR CLIENTES ===
def agregar_cliente(nombre: str, numero: str, direccion: str, cedula: str):
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
    Cliente = Query()
    cliente = clientes_table.get(Cliente.numero == numero)

    if not cliente:
        print("❌ Número no encontrado.")
        return False

    cedula_hash_verif = hashlib.sha256((cedula + cliente["salt"]).encode("utf-8")).hexdigest()
    if cedula_hash_verif == cliente["cedula_hash"]:
        print(f"✅ Inicio de sesión exitoso. Bienvenido, {cliente['nombre']}.")
        return cliente  # ← Cambiado para retornar el objeto cliente completo
    else:
        print("❌ Cédula incorrecta.")
        return False


# === FUNCIÓN PARA LISTAR TODOS LOS CLIENTES ===
def listar_clientes():
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
    Cliente = Query()
    eliminado = clientes_table.remove(Cliente.numero == numero)
    if eliminado:
        print(f"🗑️ Cliente con número {numero} eliminado correctamente.")
        return True
    else:
        print("❌ No se encontró ningún cliente con ese número.")
        return False


# === FUNCIÓN PARA ACTUALIZAR CLIENTE POR ID O CÉDULA ===
def actualizar_cliente(identificador, cedula_verificacion, nuevos_datos: dict):
    """
    Actualiza la información de un cliente buscándolo por ID o verificando su cédula.
    nuevos_datos puede contener: {"nombre": "...", "numero": "...", "direccion": "..."}
    """
    Cliente = Query()
    cliente = None

    # Buscar por ID (si es numérico)
    if isinstance(identificador, int):
        cliente = clientes_table.get(Cliente.id == identificador)
    else:
        # Buscar por cédula (recalculando el hash con cada salt guardado)
        for c in clientes_table.all():
            cedula_hash_verif = hashlib.sha256((cedula_verificacion + c["salt"]).encode("utf-8")).hexdigest()
            if cedula_hash_verif == c["cedula_hash"]:
                cliente = c
                break

    if not cliente:
        print("❌ Cliente no encontrado.")
        return False

    # Verificar que la cédula ingresada corresponda
    cedula_hash_verif = hashlib.sha256((cedula_verificacion + cliente["salt"]).encode("utf-8")).hexdigest()
    if cedula_hash_verif != cliente["cedula_hash"]:
        print("❌ La cédula no coincide. No se puede actualizar.")
        return False

    # Actualizar datos válidos
    actualizacion = {}
    for campo in ["nombre", "numero", "direccion"]:
        if campo in nuevos_datos:
            actualizacion[campo] = nuevos_datos[campo]

    if not actualizacion:
        print("⚠️ No se proporcionaron campos válidos para actualizar.")
        return False

    clientes_table.update(actualizacion, Cliente.id == cliente["id"])
    print(f"✅ Cliente '{cliente['nombre']}' actualizado correctamente.")
    return True

#=== FUNCIÓN PARA ACTUALIZAR NOMBRE ===
def actualizar_nombre_cliente(numero: str, nuevo_nombre: str, cedula_verificacion: str):
    try:
        Cliente = Query()
        cliente = clientes_table.get(Cliente.numero == numero)
        
        if not cliente:
            print("❌ Cliente no encontrado.")
            return False
        
        # Verificar cédula
        cedula_hash_verif = hashlib.sha256((cedula_verificacion + cliente["salt"]).encode("utf-8")).hexdigest()
        if cedula_hash_verif != cliente["cedula_hash"]:
            print("❌ La cédula no coincide. No se puede actualizar.")
            return False
        
        # Actualizar nombre
        clientes_table.update({"nombre": nuevo_nombre}, Cliente.id == cliente["id"])
        print(f"✅ Nombre actualizado correctamente: {cliente['nombre']} -> {nuevo_nombre}")
        return True
        
    except Exception as e:
        print(f"🔴 Error en actualizar_nombre_cliente: {e}")
        return False

# === FUNCIÓN PARA ACTUALIZAR DIRECCIÓN ===
def actualizar_direccion_cliente(numero: str, nueva_direccion: str, cedula_verificacion: str):
    """
    Actualiza solo la dirección de un cliente
    """
    print(f"{numero},{nueva_direccion},{cedula_verificacion}")
    Cliente = Query()
    cliente = clientes_table.get(Cliente.numero == numero)
    
    if not cliente:
        print("❌ Cliente no encontrado.")
        return False
    
    # Verificar cédula
    cedula_hash_verif = hashlib.sha256((cedula_verificacion + cliente["salt"]).encode("utf-8")).hexdigest()
    if cedula_hash_verif != cliente["cedula_hash"]:
        print("❌ La cédula no coincide. No se puede actualizar.")
        return False
    
    # Actualizar dirección
    clientes_table.update({"direccion": nueva_direccion}, Cliente.id == cliente["id"])
    print(f"✅ Dirección actualizada correctamente para {cliente['nombre']}")
    return True

# === FUNCIÓN PARA ACTUALIZAR CÉDULA ===
def actualizar_cedula_cliente(numero: str, nueva_cedula: str, cedula_actual: str):
    """
    Actualiza la cédula de un cliente
    """
    Cliente = Query()
    cliente = clientes_table.get(Cliente.numero == numero)
    
    if not cliente:
        print("❌ Cliente no encontrado.")
        return False
    
    # Verificar cédula actual
    cedula_hash_verif = hashlib.sha256((cedula_actual + cliente["salt"]).encode("utf-8")).hexdigest()
    if cedula_hash_verif != cliente["cedula_hash"]:
        print("❌ La cédula actual no coincide. No se puede actualizar.")
        return False
    
    # Generar nuevo hash para la nueva cédula
    nuevo_cedula_hash, nuevo_salt = hash_cedula(nueva_cedula)
    
    # Actualizar cédula y salt
    clientes_table.update({
        "cedula_hash": nuevo_cedula_hash,
        "salt": nuevo_salt
    }, Cliente.id == cliente["id"])
    
    print(f"✅ Cédula actualizada correctamente para {cliente['nombre']}")
    return True

# === FUNCIÓN PARA OBTENER CÉDULA ACTUAL (para verificación) ===
def verificar_cedula_cliente(numero: str, cedula_ingresada: str):
    """
    Verifica si la cédula ingresada coincide con la almacenada
    """
    Cliente = Query()
    cliente = clientes_table.get(Cliente.numero == numero)
    
    if not cliente:
        return False
    
    cedula_hash_verif = hashlib.sha256((cedula_ingresada + cliente["salt"]).encode("utf-8")).hexdigest()
    return cedula_hash_verif == cliente["cedula_hash"]

# === PRUEBA DEL MÓDULO ===
if __name__ == "__main__":

    
    #print("=== PRUEBA DE FUNCIONALIDAD ===")

    # Agregar clientes
    #agregar_cliente("Yoan Valdes", "573001234567", "Calle Nueva #8-10", "123456789")
    #agregar_cliente("Laura Gómez", "573009876543", "Carrera 5 #9-20", "987654321")

    # Listar
    #listar_clientes()

    # Buscar
    
    #buscar_cliente("573009876543")

    # Iniciar sesión correcta
    #iniciar_sesion("573009876543", "987654321")

    # Iniciar sesión incorrecta
    #iniciar_sesion("573009876543", "000000000")

    # Eliminar
    #eliminar_cliente("3009876543")

    # Listar después de eliminar
    #actualizar_direccion_cliente("573012331635", "calle 45 bcspn", "1033179153")
    listar_clientes()