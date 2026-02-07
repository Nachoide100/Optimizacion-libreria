import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

# Configuración inicial
fake = Faker()
Faker.seed(42)
np.random.seed(42)

NUM_LIBROS = 100        
DIAS_HISTORICO = 365    
FECHA_INICIO = datetime(2023, 1, 1)

print("📚 Generando catálogo de libros...")

# --- PASO 1: Generar Dimension de Libros (Metadata) ---
categorias = ['Ficción', 'Ciencia de Datos', 'Negocios', 'Biografía', 'Infantil']
data_libros = []

for i in range(1, NUM_LIBROS + 1):
    categoria = random.choice(categorias)
    
    # Asignar "Velocidad de Venta" (Lógica Pareto 80/20)
    if i <= NUM_LIBROS * 0.2:
        tipo = 'A' # Best Seller
        demanda_base = random.randint(5, 15)
        precio = round(random.uniform(15.0, 25.0), 2)
    elif i <= NUM_LIBROS * 0.8:
        tipo = 'B' # Venta media
        demanda_base = random.randint(1, 4)
        precio = round(random.uniform(10.0, 20.0), 2)
    else:
        tipo = 'C' # "Long tail" o venta casi nula
        demanda_base = random.uniform(0, 0.5) 
        precio = round(random.uniform(5.0, 15.0), 2)

    item = {
        'book_id': i,
        'titulo': fake.catch_phrase().title(), # Genera títulos 
        'categoria': categoria,
        'costo': round(precio * 0.6, 2), 
        'precio': precio,
        'tipo_abc': tipo,
        'demanda_promedio': demanda_base
    }
    data_libros.append(item)

df_libros = pd.DataFrame(data_libros)

# --- PASO 2: Simulación Diaria de Ventas e Inventario ---
print("🔄 Simulando operaciones día a día (esto puede tardar unos segundos)...")

registros_ventas = []
registros_inventario = []

# Inicializar stock para todos los libros
stock_actual = {book['book_id']: random.randint(20, 50) for book in data_libros}

for dia in range(DIAS_HISTORICO):
    fecha_actual = FECHA_INICIO + timedelta(days=dia)
    es_fin_de_semana = fecha_actual.weekday() >= 5
    
    for libro in data_libros:
        b_id = libro['book_id']
        demanda_base = libro['demanda_promedio']
        
        # 1. Calcular Demanda Potencial (Lo que la gente quiere comprar)
        # Factor de estacionalidad: Fines de semana se vende 30% más
        factor_dia = 1.3 if es_fin_de_semana else 1.0
        
        # Ruido aleatorio (Poisson distribution es ideal para ventas)
        demanda_dia = np.random.poisson(demanda_base * factor_dia)
        
        # 2. Verificar Stock disponible (Lo que realmente se puede vender)
        stock_disponible = stock_actual[b_id]
        
        # La venta real es el mínimo entre lo que quieren y lo que tengo
        venta_real = min(demanda_dia, stock_disponible)
        
        # Si hubo demanda pero no stock, es una "Oportunidad Perdida" (Stockout)
        # Nota: En la tabla de ventas solo registramos ventas reales > 0
        if venta_real > 0:
            registros_ventas.append({
                'fecha': fecha_actual,
                'book_id': b_id,
                'cantidad_vendida': venta_real,
                'precio_unitario': libro['precio']
            })
        
        # 3. Actualizar Inventario
        nuevo_stock = stock_disponible - venta_real
        
        # --- Lógica de Reabastecimiento (Reposición) ---
        # Si el stock baja de 5, pedimos más.
        # TRUCO PARA EL PROYECTO: A veces el proveedor "falla" para generar stockouts
        if nuevo_stock < 5:
            # 10% de probabilidad de que el proveedor se retrase 
            if random.random() > 0.10: 
                nuevo_stock += random.randint(20, 50) # Reposición exitosa
            
            
        stock_actual[b_id] = nuevo_stock
        
        # Guardar foto del inventario al final del día
        registros_inventario.append({
            'fecha': fecha_actual,
            'book_id': b_id,
            'stock_al_cierre': nuevo_stock
        })

# --- PASO 3: Exportar a CSV ---
df_ventas = pd.DataFrame(registros_ventas)
df_inventario = pd.DataFrame(registros_inventario)

print(f"✅ Generados {len(df_libros)} libros.")
print(f"✅ Generadas {len(df_ventas)} transacciones de venta.")
print(f"✅ Generados {len(df_inventario)} registros de inventario diario.")

# Guardar archivos
df_libros.to_csv('libros.csv', index=False)
df_ventas.to_csv('ventas.csv', index=False)
df_inventario.to_csv('inventario.csv', index=False)

print("\n📂 Archivos CSV creados con éxito: '1_libros.csv', '2_ventas.csv', '3_inventario.csv'")