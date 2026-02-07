import pandas as pd
from sqlalchemy import create_engine
from prophet import Prophet
import datetime

# --- CONFIGURACIÓN ---
db_connection_str = 'postgresql://postgres:Nacho6150&@localhost:5432/Libreria_DB'
db_connection = create_engine(db_connection_str)

print("🔌 Conectando a la base de datos...")

# --- PASO 1: EXTRAER DATOS ---

query = """
SELECT 
    fecha as ds, 
    book_id,
    SUM(cantidad_vendida) as y
FROM ventas
GROUP BY fecha, book_id
ORDER BY book_id, fecha;
"""
df_historico = pd.read_sql(query, db_connection)

# --- AGREGA ESTA LÍNEA AQUÍ ---
df_historico['ds'] = pd.to_datetime(df_historico['ds'])

print(f"✅ Datos históricos cargados: {len(df_historico)} registros.")

# --- PASO 2 Y 3: BUCLE DE PREDICCIÓN POR LIBRO ---
# Prophet trabaja con un libro a la vez. Haremos un bucle.

lista_predicciones = []
ids_libros = df_historico['book_id'].unique()

print(f"🔮 Iniciando predicción para {len(ids_libros)} libros (Best Sellers)...")

for b_id in ids_libros:
    # 1. Filtrar datos de este libro
    df_libro = df_historico[df_historico['book_id'] == b_id].copy()
    
    # Si tenemos muy pocos datos, saltamos (se necesitan al menos 2 semanas para que Prophet funcione bien)
    if len(df_libro) < 7:
        continue

    # 2. Entrenar el modelo
    # 'yearly_seasonality=False' porque solo tenemos un año simulado
    # 'weekly_seasonality=True' es vital para detectar picos de fin de semana
    m = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)
    m.fit(df_libro)

    # 3. Predecir futuro (próximos 7 días)
    future = m.make_future_dataframe(periods=7)
    forecast = m.predict(future)

    # 4. Quedarnos solo con los días futuros
    # forecast contiene historia + futuro. Filtramos los últimos 7 días.
    last_date = df_libro['ds'].max()
    forecast_future = forecast[forecast['ds'] > last_date][['ds', 'yhat']]
    
    # Añadir el ID del libro para saber de quién es la predicción
    forecast_future['book_id'] = b_id
    
    # Evitar predicciones negativas 
    forecast_future['yhat'] = forecast_future['yhat'].apply(lambda x: max(x, 0))
    
    lista_predicciones.append(forecast_future)

# Unir todas las predicciones en un solo DataFrame
df_final = pd.concat(lista_predicciones)
df_final.rename(columns={'ds': 'fecha_prediccion', 'yhat': 'venta_estimada'}, inplace=True)

# --- PASO 4: LÓGICA DE INVENTARIO (ROI) ---
# Aquí calculamos cuánto stock DEBERÍAMOS tener
LEAD_TIME_DIAS = 2      # El proveedor tarda 2 días en traer libros
STOCK_SEGURIDAD = 5     # Queremos tener siempre 5 por si acaso

# El "Punto de Reorden" es la demanda que esperamos durante el tiempo de espera + seguridad
df_final['punto_reorden'] = (df_final['venta_estimada'] * LEAD_TIME_DIAS) + STOCK_SEGURIDAD
df_final['punto_reorden'] = df_final['punto_reorden'].round(0).astype(int)

# --- PASO 5: CARGAR RESULTADOS A SQL ---
print("💾 Guardando predicciones en PostgreSQL...")

# Para poder reemplazar datos
df_final.to_sql('predicciones_futuras', db_connection, if_exists='replace', index=False)

print("🚀 ¡Proceso terminado! Tabla 'predicciones_futuras' creada exitosamente.")