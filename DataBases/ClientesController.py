import sqlite3
import hashlib
import uuid
import os
from typing import Union, Optional, Dict, List

# === CONFIGURACIÓN DE LA BASE DE DATOS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "MezonPeruano.db")

# === INICIALIZACIÓN DE LA BASE DE DATOS ===
def init_db():
    """Inicializa la base de datos y crea las tablas si no existen"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tabla de clientes
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
    
    # Crear tabla de menú (mantenida por compatibilidad)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicializar la base de datos al importar el módulo
init_db()

# === FUNCIÓN PARA HASHEAR LA CÉDULA ===
def hash_cedula(cedula: str, salt: str = None):
    if not salt:
        salt = uuid.uuid4().hex
    hash_obj = hashlib.sha256((cedula + salt).encode("utf-8"))
    return hash_obj.hexdigest(), salt

# === FUNCIÓN PARA AGREGAR CLIENTES ===
def agregar_cliente(nombre: str, numero: str, direccion: str, cedula: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar si ya existe un cliente con ese número
        cursor.execute("SELECT id FROM clientes WHERE numero = ?", (numero,))
        existente = cursor.fetchone()
        if existente:
            print("⚠️ Ya existe un cliente con ese número.")
            return False

        cedula_hash, salt = hash_cedula(cedula)
        
        # Insertar nuevo cliente (el id se autoincrementa)
        cursor.execute('''
            INSERT INTO clientes (nombre, numero, direccion, cedula_hash, salt)
            VALUES (?, ?, ?, ?, ?)
        ''', (nombre, numero, direccion, cedula_hash, salt))
        
        conn.commit()
        print(f"✅ Cliente '{nombre}' agregado correctamente.")
        return True
        
    except sqlite3.IntegrityError:
        print("⚠️ Ya existe un cliente con ese número.")
        return False
    finally:
        conn.close()

# === FUNCIÓN PARA INICIAR SESIÓN ===
def iniciar_sesion(numero: str, cedula: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, numero, direccion, cedula_hash, salt 
        FROM clientes WHERE numero = ?
    ''', (numero,))
    
    resultado = cursor.fetchone()
    conn.close()
    
    if not resultado:
        print("❌ Número no encontrado.")
        return False

    # Reconstruir el diccionario del cliente
    cliente = {
        "id": resultado[0],
        "nombre": resultado[1],
        "numero": resultado[2],
        "direccion": resultado[3],
        "cedula_hash": resultado[4],
        "salt": resultado[5]
    }
    
    cedula_hash_verif = hashlib.sha256((cedula + cliente["salt"]).encode("utf-8")).hexdigest()
    if cedula_hash_verif == cliente["cedula_hash"]:
        print(f"✅ Inicio de sesión exitoso. Bienvenido, {cliente['nombre']}.")
        return cliente  # ← Cambiado para retornar el objeto cliente completo
    else:
        print("❌ Cédula incorrecta.")
        return False

# === FUNCIÓN PARA LISTAR TODOS LOS CLIENTES ===
def listar_clientes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, numero, direccion FROM clientes ORDER BY id
    ''')
    
    resultados = cursor.fetchall()
    conn.close()
    
    if not resultados:
        print("📭 No hay clientes registrados.")
        return []

    # Convertir a lista de diccionarios para mantener compatibilidad
    clientes = []
    for resultado in resultados:
        cliente = {
            "id": resultado[0],
            "nombre": resultado[1],
            "numero": resultado[2],
            "direccion": resultado[3]
        }
        clientes.append(cliente)

    print("\n📋 Lista de clientes:")
    for c in clientes:
        print(f" - ID: {c['id']} | Nombre: {c['nombre']} | Número: {c['numero']} | Dirección: {c['direccion']}")
    print()
    return clientes

# === FUNCIÓN PARA BUSCAR UN CLIENTE POR NÚMERO ===
def buscar_cliente(numero: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, numero, direccion, cedula_hash, salt 
        FROM clientes WHERE numero = ?
    ''', (numero,))
    
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        cliente = {
            "id": resultado[0],
            "nombre": resultado[1],
            "numero": resultado[2],
            "direccion": resultado[3],
            "cedula_hash": resultado[4],
            "salt": resultado[5]
        }
        print(f"🔎 Cliente encontrado: {cliente['nombre']} - Dirección: {cliente['direccion']}")
        return cliente
    else:
        print("❌ Cliente no encontrado.")
        return None

# === FUNCIÓN PARA ELIMINAR UN CLIENTE ===
def eliminar_cliente(numero: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM clientes WHERE numero = ?", (numero,))
    eliminado = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cliente = None
    
    # Buscar por ID (si es numérico)
    if isinstance(identificador, int):
        cursor.execute('''
            SELECT id, nombre, numero, direccion, cedula_hash, salt 
            FROM clientes WHERE id = ?
        ''', (identificador,))
        resultado = cursor.fetchone()
        if resultado:
            cliente = {
                "id": resultado[0],
                "nombre": resultado[1],
                "numero": resultado[2],
                "direccion": resultado[3],
                "cedula_hash": resultado[4],
                "salt": resultado[5]
            }
    else:
        # Buscar por cédula (recalculando el hash con cada salt guardado)
        cursor.execute('''
            SELECT id, nombre, numero, direccion, cedula_hash, salt 
            FROM clientes
        ''')
        resultados = cursor.fetchall()
        
        for resultado in resultados:
            c = {
                "id": resultado[0],
                "nombre": resultado[1],
                "numero": resultado[2],
                "direccion": resultado[3],
                "cedula_hash": resultado[4],
                "salt": resultado[5]
            }
            cedula_hash_verif = hashlib.sha256((cedula_verificacion + c["salt"]).encode("utf-8")).hexdigest()
            if cedula_hash_verif == c["cedula_hash"]:
                cliente = c
                break

    if not cliente:
        print("❌ Cliente no encontrado.")
        conn.close()
        return False

    # Verificar que la cédula ingresada corresponda
    cedula_hash_verif = hashlib.sha256((cedula_verificacion + cliente["salt"]).encode("utf-8")).hexdigest()
    if cedula_hash_verif != cliente["cedula_hash"]:
        print("❌ La cédula no coincide. No se puede actualizar.")
        conn.close()
        return False

    # Actualizar datos válidos
    actualizacion = {}
    campos_validos = []
    valores = []
    
    for campo in ["nombre", "numero", "direccion"]:
        if campo in nuevos_datos:
            actualizacion[campo] = nuevos_datos[campo]
            campos_validos.append(f"{campo} = ?")
            valores.append(nuevos_datos[campo])

    if not actualizacion:
        print("⚠️ No se proporcionaron campos válidos para actualizar.")
        conn.close()
        return False

    # Agregar el ID al final de los valores para la cláusula WHERE
    valores.append(cliente["id"])
    
    # Construir y ejecutar la consulta UPDATE
    query = f"UPDATE clientes SET {', '.join(campos_validos)} WHERE id = ?"
    cursor.execute(query, valores)
    conn.commit()
    conn.close()
    
    print(f"✅ Cliente '{cliente['nombre']}' actualizado correctamente.")
    return True

# === FUNCIÓN PARA ACTUALIZAR NOMBRE ===
def actualizar_nombre_cliente(numero: str, nuevo_nombre: str, cedula_verificacion: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, nombre, cedula_hash, salt FROM clientes WHERE numero = ?
        ''', (numero,))
        
        resultado = cursor.fetchone()
        if not resultado:
            print("❌ Cliente no encontrado.")
            conn.close()
            return False
        
        cliente = {
            "id": resultado[0],
            "nombre": resultado[1],
            "cedula_hash": resultado[2],
            "salt": resultado[3]
        }
        
        # Verificar cédula
        cedula_hash_verif = hashlib.sha256((cedula_verificacion + cliente["salt"]).encode("utf-8")).hexdigest()
        if cedula_hash_verif != cliente["cedula_hash"]:
            print("❌ La cédula no coincide. No se puede actualizar.")
            conn.close()
            return False
        
        # Actualizar nombre
        cursor.execute("UPDATE clientes SET nombre = ? WHERE id = ?", 
                      (nuevo_nombre, cliente["id"]))
        conn.commit()
        conn.close()
        
        print(f"✅ Nombre actualizado correctamente: {cliente['nombre']} -> {nuevo_nombre}")
        return True
        
    except Exception as e:
        print(f"🔴 Error en actualizar_nombre_cliente: {e}")
        if 'conn' in locals():
            conn.close()
        return False

# === FUNCIÓN PARA ACTUALIZAR DIRECCIÓN ===
def actualizar_direccion_cliente(numero: str, nueva_direccion: str, cedula_verificacion: str):
    """
    Actualiza solo la dirección de un cliente
    """
    print(f"{numero},{nueva_direccion},{cedula_verificacion}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, cedula_hash, salt FROM clientes WHERE numero = ?
    ''', (numero,))
    
    resultado = cursor.fetchone()
    if not resultado:
        print("❌ Cliente no encontrado.")
        conn.close()
        return False
    
    cliente = {
        "id": resultado[0],
        "nombre": resultado[1],
        "cedula_hash": resultado[2],
        "salt": resultado[3]
    }
    
    # Verificar cédula
    cedula_hash_verif = hashlib.sha256((cedula_verificacion + cliente["salt"]).encode("utf-8")).hexdigest()
    if cedula_hash_verif != cliente["cedula_hash"]:
        print("❌ La cédula no coincide. No se puede actualizar.")
        conn.close()
        return False
    
    # Actualizar dirección
    cursor.execute("UPDATE clientes SET direccion = ? WHERE id = ?", 
                  (nueva_direccion, cliente["id"]))
    conn.commit()
    conn.close()
    
    print(f"✅ Dirección actualizada correctamente para {cliente['nombre']}")
    return True

# === FUNCIÓN PARA ACTUALIZAR CÉDULA ===
def actualizar_cedula_cliente(numero: str, nueva_cedula: str, cedula_actual: str):
    """
    Actualiza la cédula de un cliente
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, nombre, cedula_hash, salt FROM clientes WHERE numero = ?
    ''', (numero,))
    
    resultado = cursor.fetchone()
    if not resultado:
        print("❌ Cliente no encontrado.")
        conn.close()
        return False
    
    cliente = {
        "id": resultado[0],
        "nombre": resultado[1],
        "cedula_hash": resultado[2],
        "salt": resultado[3]
    }
    
    # Verificar cédula actual
    cedula_hash_verif = hashlib.sha256((cedula_actual + cliente["salt"]).encode("utf-8")).hexdigest()
    if cedula_hash_verif != cliente["cedula_hash"]:
        print("❌ La cédula actual no coincide. No se puede actualizar.")
        conn.close()
        return False
    
    # Generar nuevo hash para la nueva cédula
    nuevo_cedula_hash, nuevo_salt = hash_cedula(nueva_cedula)
    
    # Actualizar cédula y salt
    cursor.execute('''
        UPDATE clientes SET cedula_hash = ?, salt = ? WHERE id = ?
    ''', (nuevo_cedula_hash, nuevo_salt, cliente["id"]))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Cédula actualizada correctamente para {cliente['nombre']}")
    return True

# === FUNCIÓN PARA OBTENER CÉDULA ACTUAL (para verificación) ===
def verificar_cedula_cliente(numero: str, cedula_ingresada: str):
    """
    Verifica si la cédula ingresada coincide con la almacenada
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT cedula_hash, salt FROM clientes WHERE numero = ?
    ''', (numero,))
    
    resultado = cursor.fetchone()
    conn.close()
    
    if not resultado:
        return False
    
    cedula_hash_almacenado = resultado[0]
    salt = resultado[1]
    
    cedula_hash_verif = hashlib.sha256((cedula_ingresada + salt).encode("utf-8")).hexdigest()
    return cedula_hash_verif == cedula_hash_almacenado

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