"""
clientes_db.py

Módulo para gestionar clientes con TinyDB.
Funciones públicas:
- init_db(path)
- register_client(nombre, numero, direccion, contrasena, id_cliente=None)
- get_client_by_id(id_cliente)
- get_client_by_numero(numero)
- authenticate_cliente(numero, contrasena) -> devuelve cliente si ok, else None
- update_direccion(numero, nueva_direccion)
- update_nombre(numero, nuevo_nombre)
- update_numero(numero_actual, nuevo_numero)
- delete_cliente(numero)
- list_clients()
- next_id()  # útil si quieres generar id externo sin pasar id_cliente al registrar
"""

from tinydb import TinyDB, Query
from tinydb.operations import set as tiny_set
import hashlib
import os
from typing import Optional, Dict, Any, List

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


# ---------- Hash de contraseñas ----------
def _generate_salt() -> str:
    return os.urandom(16).hex()


def _hash_password(password: str, salt: str) -> str:
    """
    Hash simple con SHA-256 de (salt + password).
    """
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()


# ---------- Helpers ----------
def _table():
    if _db is None:
        raise RuntimeError("Base de datos no inicializada. Llama a init_db(path) primero.")
    return _db.table(_table_name)


def next_id() -> int:
    """
    Devuelve un id único incremental para clientes (1,2,3,...).
    """
    tbl = _table()
    all_clients = tbl.all()
    if not all_clients:
        return 1
    # Buscar máximo id presente (si hay clientes con 'id' guardado)
    max_id = 0
    for c in all_clients:
        try:
            cid = int(c.get('id', 0))
            if cid > max_id:
                max_id = cid
        except (ValueError, TypeError):
            continue
    return max_id + 1


# ---------- CRUD y Autenticación ----------
def register_client(nombre: str, numero: str, direccion: str, contrasena: str, id_cliente: Optional[int] = None) -> bool:
    """
    Registra un cliente. Si id_cliente es None, se genera automáticamente.
    Devuelve True si se insertó, False si ya existe (por numero o id).
    """
    tbl = _table()
    Cliente = Query()

    # Normalizar número como string
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
    pwd_hash = _hash_password(contrasena, salt)

    tbl.insert({
        'id': id_cliente,
        'nombre': nombre,
        'numero': numero,
        'direccion': direccion,
        'password_hash': pwd_hash,
        'salt': salt
    })
    return True


def get_client_by_numero(numero: str) -> Optional[Dict[str, Any]]:
    tbl = _table()
    Cliente = Query()
    numero = str(numero)
    res = tbl.search(Cliente.numero == numero)
    return res[0] if res else None


def get_client_by_id(id_cliente: int) -> Optional[Dict[str, Any]]:
    tbl = _table()
    Cliente = Query()
    res = tbl.search(Cliente.id == id_cliente)
    return res[0] if res else None


def authenticate_cliente(numero: str, contrasena: str) -> Optional[Dict[str, Any]]:
    """
    Verifica que el numero y la contraseña coincidan.
    Devuelve el cliente (sin remover salt/hash) si es correcto, o None.
    """
    cliente = get_client_by_numero(numero)
    if not cliente:
        return None
    salt = cliente.get('salt')
    stored_hash = cliente.get('password_hash')
    if not salt or not stored_hash:
        return None
    if _hash_password(contrasena, salt) == stored_hash:
        return cliente
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


def update_password(numero: str, nueva_contrasena: str) -> bool:
    """
    Actualiza la contraseña: genera nuevo salt y hash.
    """
    tbl = _table()
    Cliente = Query()
    numero = str(numero)
    if tbl.search(Cliente.numero == numero):
        salt = _generate_salt()
        pwd_hash = _hash_password(nueva_contrasena, salt)
        tbl.update({'salt': salt, 'password_hash': pwd_hash}, Cliente.numero == numero)
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
    Lista todos los clientes.
    """
    tbl = _table()
    return tbl.all()


# ---------- Demo pequeño (opcional) ----------
if __name__ == "__main__":
    # Demo de uso rápido
    init_db("clientes_demo.json")

    print("Generando demo...")
    register_client("Yoan Valdés", "3001234567", "Calle 10 #5-22", "mi_pass_segura")
    register_client("Laura Pérez", "3109876543", "Carrera 7 #20-14", "otra_pass")

    print("Todos:", list_clients())
    print("Buscar por número:", get_client_by_numero("3001234567"))
    print("Autenticar correcto:", authenticate_cliente("3001234567", "mi_pass_segura") is not None)
    print("Autenticar incorrecto:", authenticate_cliente("3001234567", "mal") is None)

    update_direccion("3001234567", "Calle Nueva #8-10")
    update_password("3001234567", "nueva_pass")
    print("Después de cambios:", get_client_by_numero("3001234567"))

    delete_cliente("3109876543")
    print("Final:", list_clients())
