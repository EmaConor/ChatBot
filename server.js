const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// Configuración de la base de datos
const DB_PATH = path.join(__dirname, 'DataBases', 'MezonPeruano.db');

function connectDB() {
  return new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
      console.error('❌ Error conectando a la base de datos:', err.message);
      return null;
    } else {
      console.log('✅ Conectado a la base de datos SQLite.');
      return true;
    }
  });
}

// Verificar conexión al iniciar
console.log('🔍 Intentando conectar a la base de datos...');
const dbCheck = connectDB();
if (!dbCheck) {
  console.log('❌ No se pudo conectar a la base de datos. Verifica la ruta:', DB_PATH);
} else {
  console.log('✅ Conexión a BD verificada al inicio');
}

// Ruta principal
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Ruta de salud
app.get('/api/health', (req, res) => {
  const db = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
      res.json({ 
        status: 'error', 
        message: 'Error conectando a BD: ' + err.message,
        dbPath: DB_PATH
      });
    } else {
      db.get('SELECT 1 as test', (err, row) => {
        db.close();
        if (err) {
          res.json({ status: 'error', message: 'Error en consulta: ' + err.message });
        } else {
          res.json({ 
            status: 'ok', 
            message: 'Servidor y BD funcionando correctamente',
            dbPath: DB_PATH
          });
        }
      });
    }
  });
});

// API Routes
app.get('/api/dashboard/stats', (req, res) => {
  const db = new sqlite3.Database(DB_PATH);
  
  const queries = [
    'SELECT SUM(precio_total) as total FROM facturas',
    'SELECT COUNT(*) as total FROM facturas', 
    'SELECT COUNT(*) as total FROM clientes',
    "SELECT COUNT(*) as total FROM facturas WHERE DATE(fecha) = DATE('now')",
    'SELECT COUNT(*) as total FROM productos WHERE disponible = 1'
  ];

  Promise.all(queries.map(query => 
    new Promise((resolve) => {
      db.get(query, (err, row) => {
        resolve(row?.total || 0);
      });
    })
  )).then(([totalVentas, totalPedidos, totalClientes, pedidosHoy, productosActivos]) => {
    db.close();
    res.json({ totalVentas, totalPedidos, totalClientes, pedidosHoy, productosActivos });
  }).catch(err => {
    db.close();
    console.error('Error en stats:', err);
    res.json({ totalVentas: 0, totalPedidos: 0, totalClientes: 0, pedidosHoy: 0, productosActivos: 0 });
  });
});

app.get('/api/dashboard/estados-pedidos', (req, res) => {
  const db = new sqlite3.Database(DB_PATH);

  db.all('SELECT estado, COUNT(*) as cantidad FROM facturas GROUP BY estado', (err, rows) => {
    db.close();
    if (err) {
      console.error('Error en estados:', err);
      res.json({});
    } else {
      const estados = {};
      if (rows) {
        rows.forEach(row => {
          estados[row.estado] = row.cantidad;
        });
      }
      res.json(estados);
    }
  });
});

app.get('/api/dashboard/productos-mas-vendidos', (req, res) => {
  const db = new sqlite3.Database(DB_PATH);

  db.all(`
    SELECT p.nombre, p.categoria, SUM(ip.cantidad) as total_vendido
    FROM items_pedido ip
    JOIN productos p ON ip.producto_id = p.id
    GROUP BY p.id, p.nombre, p.categoria
    ORDER BY total_vendido DESC
    LIMIT 5
  `, (err, rows) => {
    db.close();
    if (err) {
      console.error('Error en productos:', err);
      res.json([]);
    } else {
      res.json(rows || []);
    }
  });
});

app.get('/api/dashboard/ventas-recientes', (req, res) => {
  const db = new sqlite3.Database(DB_PATH);

  db.all(`
    SELECT f.id, f.precio_total, f.descripcion, f.cedula_cliente, f.fecha, f.estado, 
           c.nombre as nombre_cliente
    FROM facturas f
    LEFT JOIN clientes c ON f.cedula_cliente = c.cedula_hash
    ORDER BY f.fecha DESC
    LIMIT 6
  `, async (err, facturas) => {
    if (err) {
      console.error('Error en ventas recientes:', err);
      res.json([]);
      db.close();
      return;
    }

    // Cargar items para cada factura
    const ventasConItems = await Promise.all(
      (facturas || []).map(factura => 
        new Promise((resolve) => {
          const dbItems = new sqlite3.Database(DB_PATH);
          dbItems.all(`
            SELECT 
              ip.id,
              ip.producto_id,
              ip.cantidad,
              ip.precio_unitario,
              ip.notas,
              p.nombre as producto_nombre,
              p.descripcion as producto_descripcion
            FROM items_pedido ip
            JOIN productos p ON ip.producto_id = p.id
            WHERE ip.factura_id = ?
          `, [factura.id], (err, items) => {
            dbItems.close();
            resolve({ 
              ...factura, 
              items: items || [] 
            });
          });
        })
      )
    );

    db.close();
    res.json(ventasConItems);
  });
});

// Obtener pedidos CON SUS ITEMS
app.get('/api/pedidos', (req, res) => {
  const db = new sqlite3.Database(DB_PATH);
  const { estado } = req.query;

  let query = `
    SELECT f.id, f.precio_total, f.descripcion, f.cedula_cliente, f.fecha, f.estado, 
           c.nombre as nombre_cliente, c.direccion, c.numero
    FROM facturas f
    LEFT JOIN clientes c ON f.cedula_cliente = c.cedula_hash
  `;

  const params = [];
  if (estado && estado !== 'Todos') {
    query += ' WHERE f.estado = ?';
    params.push(estado);
  }

  query += ' ORDER BY f.fecha DESC';

  db.all(query, params, async (err, facturas) => {
    if (err) {
      console.error('Error en pedidos:', err);
      res.json([]);
      db.close();
      return;
    }

    // Cargar items para cada pedido
    const pedidosConItems = await Promise.all(
      (facturas || []).map(factura => 
        new Promise((resolve) => {
          const dbItems = new sqlite3.Database(DB_PATH);
          dbItems.all(`
            SELECT 
              ip.id,
              ip.producto_id,
              ip.cantidad,
              ip.precio_unitario,
              ip.notas,
              p.nombre as producto_nombre,
              p.descripcion as producto_descripcion
            FROM items_pedido ip
            JOIN productos p ON ip.producto_id = p.id
            WHERE ip.factura_id = ?
          `, [factura.id], (err, items) => {
            dbItems.close();
            resolve({ 
              ...factura, 
              items: items || [] 
            });
          });
        })
      )
    );

    db.close();
    res.json(pedidosConItems);
  });
});

// Ruta específica para obtener items de un pedido (por si acaso)
app.get('/api/pedidos/:id/items', (req, res) => {
  const { id } = req.params;
  const db = new sqlite3.Database(DB_PATH);

  db.all(`
    SELECT 
      ip.id,
      ip.producto_id,
      ip.cantidad,
      ip.precio_unitario,
      ip.notas,
      p.nombre as producto_nombre,
      p.descripcion as producto_descripcion
    FROM items_pedido ip
    JOIN productos p ON ip.producto_id = p.id
    WHERE ip.factura_id = ?
  `, [id], (err, items) => {
    db.close();
    if (err) {
      console.error('Error obteniendo items:', err);
      res.json([]);
    } else {
      res.json(items || []);
    }
  });
});

// Manejo de errores 404
app.use((req, res) => {
  res.status(404).json({ error: 'Ruta no encontrada: ' + req.url });
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor corriendo en http://localhost:${PORT}`);
  console.log(`📊 Dashboard disponible en http://localhost:${PORT}`);
  console.log(`🔍 Para verificar: http://localhost:${PORT}/api/health`);
  console.log(`📁 Ruta de BD: ${DB_PATH}`);
  console.log(`✅ Los pedidos ahora incluyen items desde items_pedido`);
});