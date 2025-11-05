"""
clientes_db.py

Módulo para gestionar clientes con TinyDB.
Cambios principales:
- El login se realiza con (numero, cedula).
- La cédula se almacena hasheada (cedula_hash) junto con un salt único por usuario.
- Las funciones que devuelven clientes devuelven una copia "sanitizada" (sin cedula_hash ni salt).
Funciones públicas:
- init_db(path)
- register_client(nombre, numero, direccion, cedula, id_cliente=None)
- get_client_by_numero(numero)  # devuelve cliente sin campos sensibles
- get_client_raw_by_numero(numero)  # devuelve cliente con todos los campos (solo si lo necesitas)
- authenticate_by_cedula(numero, cedula) -> devuelve cliente (sanitizado) si ok, else None
- update_direccion(numero, nueva_direccion)
- update_nombre(numero, nuevo_nombre)
- update_numero(numero_actual, nuevo_numero)
- update_cedula(numero, nueva_cedula)
- delete_cliente(numero)
- list_clients()  # lista sanitizada
- next_id()
"""

from tinydb import TinyDB, Query
from tinydb.operations import set as tiny_set
import hashlib
import os
from typing import Optional, Dict, Any, List
import copy

# Estado interno del módulo
_db: Optional[TinyDB] = None
_table_name = "clientes"


# ---------- Inicialización ----------
def init_db(filename: str = "clientes.json"):
    """
    Inicializa la base de datos TinyDB en la misma carpeta donde está este archivo.
    """
    global _db
    if _db is None:
        # Carpeta actual del archivo clientes_db.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, filename)
        _db = TinyDB(db_path, indent=4)
    return _db


# ---------- Hash de cédula ----------
def _generate_salt() -> str:
    return os.urandom(16).hex()


def _hash_cedula(cedula: str, salt: str) -> str:
    """
    Hash con SHA-256 de (salt + cedula).
    """
    return hashlib.sha256((salt + str(cedula)).encode('utf-8')).hexdigest()


# ---------- Helpers ----------
def _table():
    if _db is None:
        raise RuntimeError("Base de datos no inicializada. Llama a init_db(path) primero.")
    return _db.table(_table_name)


def _sanitize_cliente(cliente: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve una copia del cliente sin campos sensibles (cedula_hash, salt).
    """
    cliente_copy = copy.deepcopy(cliente)
    cliente_copy.pop('cedula_hash', None)
    cliente_copy.pop('salt', None)
    return cliente_copy


def next_id() -> int:
    """
    Devuelve un id único incremental para clientes (1,2,3,...).
    """
    tbl = _table()
    all_clients = tbl.all()
    if not all_clients:
        return 1
    max_id = 0
    for c in all_clients:
        try:
            cid = int(c.get('id', 0))
            if cid > max_id:
                max_id = cid
        except (ValueError, TypeError):
            continue
    return max_id + 1


# ---------- CRUD y Autenticación (con cédula hasheada) ----------
def register_client(nombre: str, numero: str, direccion: str, cedula: str, id_cliente: Optional[int] = None) -> bool:
    """
    Registra un cliente. Si id_cliente es None, se genera automáticamente.
    La cédula se guarda hasheada (cedula_hash) y se guarda el salt.
    Devuelve True si se insertó, False si ya existe (por numero o id).
    """
    tbl = _table()
    Cliente = Query()
    numero = str(numero)

    # Revisar existencia por número o id
    if id_cliente is not None:
        if tbl.search(Cliente.id == id_cliente):
            return False

    if tbl.search(Cliente.numero == numero):
        return False

    if id_cliente is None:
        id_cliente = next_id()

    salt = _generate_salt()
    cedula_hash = _hash_cedula(cedula, salt)

    tbl.insert({
        'id': id_cliente,
        'nombre': nombre,
        'numero': numero,
        'direccion': direccion,
        'cedula_hash': cedula_hash,
        'salt': salt
    })
    return True


def get_client_raw_by_numero(numero: str) -> Optional[Dict[str, Any]]:
    """
    Devuelve el documento tal cual (incluye cedula_hash y salt).
    Úsalo solo internamente o si necesitas los campos sensibles.
    """
    tbl = _table()
    Cliente = Query()
    numero = str(numero)
    res = tbl.search(Cliente.numero == numero)
    return res[0] if res else None


def get_client_by_numero(numero: str) -> Optional[Dict[str, Any]]:
    """
    Devuelve el cliente pero SIN cedula_hash ni salt.
    """
    raw = get_client_raw_by_numero(numero)
    return _sanitize_cliente(raw) if raw else None


def authenticate_by_cedula(numero: str, cedula: str) -> Optional[Dict[str, Any]]:
    """
    Verifica que el numero exista y que la cédula ingresada coincida con el hash guardado.
    Si es correcto, devuelve el cliente sanitizado; si no, devuelve None.
    """
    cliente = get_client_raw_by_numero(numero)
    if not cliente:
        return None
    salt = cliente.get('salt')
    stored_hash = cliente.get('cedula_hash')
    if not salt or not stored_hash:
        return None
    if _hash_cedula(cedula, salt) == stored_hash:
        return _sanitize_cliente(cliente)
    return None


def update_direccion(numero: str, nueva_direccion: str) -> bool:
    tbl = _table()
    Cliente = Query()
    numero = str(numero)
    if tbl.search(Cliente.numero == numero):
        tbl.update(tiny_set('direccion', nueva_direccion), Cliente.numero == numero)
        return True
    return False


def update_nombre(numero: str, nuevo_nombre: str) -> bool:
    tbl = _table()
    Cliente = Query()
    numero = str(numero)
    if tbl.search(Cliente.numero == numero):
        tbl.update(tiny_set('nombre', nuevo_nombre), Cliente.numero == numero)
        return True
    return False


def update_numero(numero_actual: str, nuevo_numero: str) -> bool:
    """
    Cambia el número del cliente. Verifica que nuevo_numero no exista ya.
    """
    tbl = _table()
    Cliente = Query()
    numero_actual = str(numero_actual)
    nuevo_numero = str(nuevo_numero)

    if tbl.search(Cliente.numero == nuevo_numero):
        # nuevo número ya está en uso
        return False

    if tbl.search(Cliente.numero == numero_actual):
        tbl.update(tiny_set('numero', nuevo_numero), Cliente.numero == numero_actual)
        return True
    return False


def update_cedula(numero: str, nueva_cedula: str) -> bool:
    """
    Actualiza la cédula (genera nuevo salt y nuevo hash).
    """
    tbl = _table()
    Cliente = Query()
    numero = str(numero)
    if tbl.search(Cliente.numero == numero):
        salt = _generate_salt()
        cedula_hash = _hash_cedula(nueva_cedula, salt)
        tbl.update({'salt': salt, 'cedula_hash': cedula_hash}, Cliente.numero == numero)
        return True
    return False


def delete_cliente(numero: str) -> bool:
    tbl = _table()
    Cliente = Query()
    numero = str(numero)
    if tbl.search(Cliente.numero == numero):
        tbl.remove(Cliente.numero == numero)
        return True
    return False


def list_clients() -> List[Dict[str, Any]]:
    """
    Lista todos los clientes en forma sanitizada.
    """
    tbl = _table()
    return [_sanitize_cliente(c) for c in tbl.all()]


# ---------- Demo pequeño (opcional) ----------
if __name__ == "__main__":
    init_db("clientes_demo.json")

    print("Generando demo (cédula hasheada)...")
    register_client("Yoan Valdés", "3001234567", "Calle 10 #5-22", "1234567890")
    register_client("Laura Pérez", "3109876543", "Carrera 7 #20-14", "1087654321")

    print("Todos (sanitizados):", list_clients())
    print("Buscar por número:", get_client_by_numero("3001234567"))

    print("Autenticar correcto (3001234567, 1234567890):", authenticate_by_cedula("3001234567", "1234567890") is not None)
    print("Autenticar incorrecto (3001234567, 0000):", authenticate_by_cedula("3001234567", "0000") is None)

    update_direccion("3001234567", "Calle Nueva #8-10")
    update_cedula("3001234567", "9999999999")
    print("Después de cambios (nota: cédula actualizada):", get_client_by_numero("3001234567"))

    delete_cliente("3109876543")
    print("Final:", list_clients())
