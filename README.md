# 📦 Optimización de Inventario & Forecasting

![Status](https://img.shields.io/badge/Status-Completed-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![SQL](https://img.shields.io/badge/PostgreSQL-15-336791)
![PowerBI](https://img.shields.io/badge/PowerBI-Desktop-F2C811)

> **Business Intelligence & Data Science Project** > Un sistema integral para la optimización de stock, detección de ventas perdidas y predicción de demanda futura utilizando Python, SQL y Power BI.

## 🎯 El Problema de Negocio

Mi madre siempre se está quejando de que algunos hay ciertos momentos en los que varios clientes piden el mismo libro, y en ese momento no lo disponen en el almacén. ¿Cómo poder anticipar esos momentos para poderte llevar esas ventas extra? La respuesta está en los datos. Este proyecto fue diseñado originalmente para modernizar la gestión de la librería de mi madre, que sufría el clásico dilema de: "¿Qué pido hoy para no quedarme corto ni pasarme?".

¿Por qué Datos Sintéticos? Principalmente, porque mi madre no se fía mucho de mi asi que tuve que entregarle una herramienta probada, no un experimento. Dado que los datos históricos reales estaban fragmentados o en papel, y para no hacerle perder dinero en caso de equivocarme, decidí crear una simulación completa del negocio.

Utilizando Python (Faker y Numpy), recreé un año completo de ventas e inventario, introduciendo intencionalmente patrones complejos y "trampas" (como stockouts) para asegurarme de que mi algoritmo de predicción fuera capaz de detectarlos y resolverlos. Este proyecto es la prueba de concepto "Punto de Reorden! lista para ser conectada a su sistema real.

## 📊 Vista Previa del Dashboard

![Dashboard Preview](https://github.com/Nachoide100/Optimizacion-libreria/blob/904805b273c25c92e1c5afbe7cdcd4840cf4c7b7/visualizations/informe.png)




---

## 🛠️ Arquitectura Técnica

El proyecto sigue un flujo de datos ETL + ML moderno:

1.  **Generación de Datos (Python):** Simulación de transacciones realistas.
2.  **Almacenamiento (PostgreSQL):** Modelado de datos en esquema de estrella.
3.  **Procesamiento (SQL):** Cálculo de KPIs históricos y limpieza.
4.  **Machine Learning (Python):** Forecasting de demanda futura.
5.  **Visualización (Power BI):** Dashboard interactivo para toma de decisiones.

---

## 🚀 Características Clave del Proyecto

### 1. Ingeniería de Datos Sintéticos (Python & Faker)
Ante la falta de datos sensibles reales, desarrollé un script en Python (`generador_datos.py`) que simula un entorno de retail complejo:
* **Librerías utilizadas:** `Pandas`, `Numpy`, `Faker`.
* **Lógica de Negocio:** Implementación de estacionalidad (picos en fines de semana), distribución de Pareto (Principios 80/20 en ventas) y simulación intencional de fallos de stock.

### 2. Modelado y Gestión de Base de Datos (PostgreSQL)
Diseño de un Data Warehouse local con **PostgreSQL**:
* Creación de tablas relacionales (`libros`, `ventas`, `inventario`).
* Ingesta de datos masiva desde CSV.
* Integridad referencial mediante Foreign Keys.

### 3. Análisis Avanzado con SQL (Vistas Materializadas)
La lógica pesada de negocio se centralizó en la base de datos para optimizar el rendimiento de Power BI.
* **Creación de `vw_analisis_stock`:** Una vista maestra que cruza inventario y ventas.
* **Detección de "Venta Perdida":** Uso de `CASE WHEN` y `COALESCE` para estimar cuánto dinero se perdió los días que el stock fue 0.

```sql
CREATE OR REPLACE VIEW vw_analisis_stock AS
SELECT 
    -- 1. Dimensiones (Contexto)
    i.fecha,
    l.titulo,
    l.categoria,
    l.tipo_abc,
    l.precio,
    l.costo,
    
    -- 2. Métricas de Inventario Real
    i.stock_al_cierre,
    
    -- 3. Métricas de Venta Real (Manejo de Nulos)
    -- Usamos COALESCE para que si no hay venta, ponga un 0 en vez de NULL
    COALESCE(v.cantidad_vendida, 0) AS unidades_vendidas,
    COALESCE(v.cantidad_vendida * l.precio, 0) AS ingreso_real,
    
    -- 4. Detección de Problemas (Lógica de Negocio)
    -- Si el stock es 0, marcamos el día como 'Stockout' (1 = Sí, 0 = No)
    CASE 
        WHEN i.stock_al_cierre = 0 THEN 1 
        ELSE 0 
    END AS es_stockout,
    
    -- 5. Cálculo de venta perdida
    -- Si hubo stockout, asumimos que podríamos haber vendido la demanda promedio del libro
    CASE 
        WHEN i.stock_al_cierre = 0 THEN (l.demanda_promedio * l.precio)
        ELSE 0 
    END AS venta_perdida_estimada

FROM inventario i
-- Unimos con Libros para saber el precio y categoría
JOIN libros l ON i.book_id = l.book_id
-- Unimos con Ventas usando LEFT JOIN (queremos el día del inventario aunque no haya ventas)
LEFT JOIN ventas v ON i.fecha = v.fecha AND i.book_id = v.book_id;
```

### 4. Forecasting y Machine Learning (Holt-Winters)
Este script en Python automatiza el ciclo de predicción conectándose a PostgreSQL para extraer el histórico de ventas. Utiliza la librería Prophet para generar un modelo de Machine Learning individual por cada libro, prediciendo la demanda para los próximos 7 días y detectando patrones semanales..
* **Cálculo del ROP (Reorder Point):**
    > `Punto de Reorden = (Demanda Diaria Predicha * Lead Time) + Stock de Seguridad`


### 5. Dashboard Operativo (Power BI)
Un cuadro de mando diseñado para la acción inmediata, no solo para la observación.
* **KPIs de Impacto:** Cálculo de dinero perdido y alertas de disponibilidad.
* **Semáforo de Inventario (DAX):** Lógica condicional que compara `Stock Actual` vs `Target IA` para marcar en ROJO los pedidos urgentes.
* **Visualización Híbrida:** Gráfico de líneas continuo que une Datos Históricos (SQL) + Predicción (Python) con opción de filtrado según el título del libro.

![informe_libro](https://github.com/Nachoide100/Optimizacion-libreria/blob/904805b273c25c92e1c5afbe7cdcd4840cf4c7b7/visualizations/libreo.png)

Si queréis acceder al informe dinámico -> [Informe](https://drive.google.com/file/d/1JGaj8_F-tG617mo-sAqFJZM1khyx2OBg/view?usp=drive_link)
---


## 📈 Impacto Potencial (Simulado)

* **Reducción del 15%** en ventas perdidas mediante alertas tempranas de stock.
* **Optimización del flujo de caja** al reducir la compra de libros de categoría C (baja rotación).
* **Automatización total** del cálculo de necesidades de compra, ahorrando horas de análisis manual.

---

## 👤 Autor

**José Ignacio Rubio**

*Data Scientist / Data Analyst* [![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/jos%C3%A9-ignacio-rubio-194471308/) 
[![Portfolio](https://img.shields.io/badge/Portfolio-Web-orange)](https://github.com/Nachoide100/Nachoide100.git)
