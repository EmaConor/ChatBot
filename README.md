# 🤖 ChatBot — Mezon Peruano

Sistema web para la gestión de pedidos y consulta de información de un restaurante, desarrollado como una aplicación full-stack con integración de chatbot, dashboard administrativo y base de datos SQLite.

El proyecto permite gestionar y consultar información relacionada con **clientes, productos, pedidos, facturas y ventas**, además de proporcionar un dashboard para visualizar información relevante del negocio.

---

## 📌 Descripción

**ChatBot — Mezon Peruano** es una aplicación orientada a facilitar la interacción con la información de un restaurante y apoyar la gestión de sus pedidos.

El sistema está compuesto por diferentes módulos:

* 🤖 **Chatbot:** módulo destinado a la interacción conversacional.
* 📊 **Dashboard:** panel administrativo para consultar estadísticas y pedidos.
* 🗄️ **Base de datos:** almacenamiento de clientes, productos, facturas e información de pedidos.
* 🔌 **API REST:** comunicación entre el dashboard y la base de datos.

El dashboard permite visualizar información como ventas totales, cantidad de pedidos, clientes registrados, productos activos, estados de los pedidos, productos más vendidos y ventas recientes.

---

## ✨ Características

### 📊 Dashboard

El sistema proporciona un panel administrativo con información resumida del negocio:

* Ventas totales.
* Número total de pedidos.
* Clientes registrados.
* Productos activos.
* Cantidad de pedidos realizados durante el día.
* Estado de los pedidos.
* Productos más vendidos.
* Ventas recientes.

Los datos se obtienen dinámicamente desde la API y la base de datos SQLite.

### 📦 Gestión de pedidos

Permite consultar los pedidos registrados y filtrarlos según su estado:

* `Todos`
* `Pedido`
* `Pagado`
* `En envio`
* `Enviado`

También se muestra información asociada a cada pedido, incluyendo cliente, productos, cantidades, precio y fecha.

### 🗄️ Base de datos

El proyecto utiliza **SQLite** para almacenar la información del sistema.

La base de datos se encuentra en:

```text
DataBases/MezonPeruano.db
```

Entre las entidades utilizadas se encuentran:

* `clientes`
* `productos`
* `facturas`
* `items_pedido`

Las relaciones entre estas tablas permiten obtener información detallada de los pedidos y sus productos.

### 🔌 API

El backend proporciona diferentes endpoints para consultar la información almacenada en SQLite.

Algunos endpoints disponibles son:

```text
GET /api/health
GET /api/dashboard/stats
GET /api/dashboard/estados-pedidos
GET /api/dashboard/productos-mas-vendidos
GET /api/dashboard/ventas-recientes
GET /api/pedidos
GET /api/pedidos/:id/items
```

---

## 🛠️ Tecnologías utilizadas

### Backend

* **Node.js**
* **Express.js**
* **SQLite3**
* **CORS**

El servidor está configurado para ejecutarse en el puerto:

```text
3001
```

El backend también sirve la aplicación del dashboard y proporciona los endpoints REST para consultar los datos.

### Frontend

El dashboard está construido utilizando:

* HTML5
* JavaScript
* Tailwind CSS
* Font Awesome

La interfaz utiliza Tailwind CSS para los estilos y componentes visuales, mientras que JavaScript se encarga de consumir la API y actualizar dinámicamente la información mostrada.

### Base de datos

```text
SQLite
```

La conexión se realiza mediante el paquete `sqlite3`.

---

## 📁 Estructura del proyecto

```text
ChatBot/
│
├── Chatbot/
│   └── # Módulo del chatbot
│
├── Dashboard/
│   ├── index.html
│   ├── server.js
│   └── package.json
│
├── DataBases/
│   └── MezonPeruano.db
│
├── .vscode/
│
└── .gitattributes
```

> La estructura puede variar según las modificaciones realizadas al proyecto.

---

## ⚙️ Requisitos

Antes de ejecutar el proyecto es necesario tener instalado:

* [Node.js](https://nodejs.org/)
* npm
* Git

Puedes comprobar las instalaciones con:

```bash
node --version
npm --version
git --version
```

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/EmaConor/ChatBot.git
```

Entrar al proyecto:

```bash
cd ChatBot
```

### 2. Entrar al Dashboard

```bash
cd Dashboard
```

### 3. Instalar las dependencias

```bash
npm install
```

El proyecto utiliza, entre otras dependencias:

```json
{
  "express": "^4.18.2",
  "sqlite3": "^5.1.6",
  "cors": "^2.8.5"
}
```

### 4. Ejecutar el servidor

```bash
npm start
```

El servidor estará disponible en:

```text
http://localhost:3001
```

También puedes comprobar el estado del servidor y de la base de datos mediante:

```text
http://localhost:3001/api/health
```

---

## 📊 Dashboard

Una vez iniciado el servidor, accede desde el navegador a:

```text
http://localhost:3001/dashboard
```

La aplicación proporciona dos vistas principales:

### Dashboard

Muestra:

* Ventas totales.
* Pedidos.
* Clientes.
* Productos activos.
* Estados de pedidos.
* Productos más vendidos.
* Ventas recientes.

### Pedidos

Permite:

* Consultar pedidos.
* Buscar pedidos.
* Filtrar por estado.
* Consultar información del cliente.
* Consultar productos asociados a cada pedido.

---

## 🔗 API

### Verificar estado del sistema

```http
GET /api/health
```

Comprueba que el servidor pueda conectarse correctamente a SQLite.

### Obtener estadísticas

```http
GET /api/dashboard/stats
```

Devuelve información como:

```json
{
  "totalVentas": 0,
  "totalPedidos": 0,
  "totalClientes": 0,
  "pedidosHoy": 0,
  "productosActivos": 0
}
```

### Estados de pedidos

```http
GET /api/dashboard/estados-pedidos
```

Devuelve la cantidad de pedidos agrupados por estado.

### Productos más vendidos

```http
GET /api/dashboard/productos-mas-vendidos
```

Obtiene los productos con mayor cantidad de unidades vendidas.

### Ventas recientes

```http
GET /api/dashboard/ventas-recientes
```

Obtiene las ventas más recientes junto con la información de los productos asociados.

### Pedidos

```http
GET /api/pedidos
```

También permite filtrar por estado:

```http
GET /api/pedidos?estado=Pagado
```

### Productos de un pedido

```http
GET /api/pedidos/:id/items
```

Ejemplo:

```http
GET /api/pedidos/15/items
```

---

## 🏗️ Arquitectura

El proyecto sigue una arquitectura sencilla basada en tres elementos principales:

```text
┌─────────────────────┐
│      Frontend       │
│  Dashboard / Chat   │
└──────────┬──────────┘
           │
           │ HTTP / REST
           ▼
┌─────────────────────┐
│       Backend       │
│ Node.js + Express   │
└──────────┬──────────┘
           │
           │ SQL
           ▼
┌─────────────────────┐
│      SQLite         │
│  MezonPeruano.db    │
└─────────────────────┘
```

El servidor Express funciona como intermediario entre la interfaz web y la base de datos SQLite.

---

## 🔄 Flujo de información

El funcionamiento básico del sistema es:

```text
Usuario
   │
   ▼
Dashboard
   │
   ▼
API REST
   │
   ▼
Express / Node.js
   │
   ▼
SQLite
   │
   ▼
Datos de clientes,
productos y pedidos
```

Por ejemplo, cuando el dashboard solicita las estadísticas:

```text
Dashboard
    ↓
GET /api/dashboard/stats
    ↓
Express
    ↓
Consultas SQL
    ↓
SQLite
    ↓
JSON
    ↓
Dashboard
```

---

## 🎨 Interfaz

La interfaz utiliza un diseño orientado a la administración de un restaurante, con una combinación de tarjetas, indicadores, filtros y listados.

El dashboard presenta información de manera visual para facilitar la consulta de:

* Indicadores generales.
* Pedidos.
* Productos.
* Ventas.
* Estados de pedidos.

La interfaz está implementada con HTML y JavaScript y utiliza Tailwind CSS y Font Awesome para los elementos visuales.

---

## 🔐 Consideraciones de seguridad

Para futuras versiones se recomienda incorporar:

* Autenticación de usuarios.
* Autorización por roles.
* Variables de entorno para configuraciones sensibles.
* Validación de datos recibidos por la API.
* Manejo centralizado de errores.
* Protección adicional de los endpoints.
* No almacenar información sensible directamente en el repositorio.

---

## 🚧 Mejoras futuras

Algunas funcionalidades que pueden incorporarse al proyecto:

* [ ] Sistema de autenticación.
* [ ] Gestión CRUD de productos.
* [ ] Gestión CRUD de clientes.
* [ ] Creación y actualización de pedidos desde el dashboard.
* [ ] Actualización automática de estadísticas.
* [ ] Gráficos interactivos de ventas.
* [ ] Exportación de reportes.
* [ ] Sistema de roles y permisos.
* [ ] Mejoras en el módulo de chatbot.
* [ ] Despliegue en un servidor.
* [ ] Pruebas automatizadas.
* [ ] Documentación completa de la API.

---

## 👨‍💻 Desarrollo

El proyecto se encuentra en desarrollo y puede ser extendido para incorporar nuevas funcionalidades relacionadas con la gestión del restaurante y la interacción mediante chatbot.

Repositorio:

[EmaConor/ChatBot](https://github.com/EmaConor/ChatBot?utm_source=chatgpt.com)

---

## 📄 Licencia

Actualmente el repositorio no muestra una licencia definida en su información pública.

Si se desea distribuir o reutilizar el proyecto, se recomienda definir una licencia explícita.

