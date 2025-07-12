import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "medifinder"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "admin"),
}

def get_db_connection():
    """Establece una conexión con la base de datos PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

# --- Herramientas de Análisis (Para el Agente de Gestores) ---

def generate_low_stock_report(region_name: str) -> dict:
    """
    Genera un reporte de medicamentos con bajo stock o desabastecidos para una región específica.
    Bajo stock se define por el indicador 'Substock' o 'Desabastecido'.
    """
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "error_message": "La conexión a la base de datos falló."}

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # 1. Encontrar el region_id
            cur.execute("SELECT region_id FROM regions WHERE name ILIKE %s LIMIT 1;", (f"%{region_name}%",))
            region_result = cur.fetchone()
            if not region_result:
                return {"status": "region_not_found", "error_message": f"Región '{region_name}' no encontrada."}
            region_id = region_result['region_id']

            # 2. Obtener el reporte de los últimos registros de inventario
            query = """
                WITH LatestInventory AS (
                    SELECT
                        i.product_id,
                        i.center_id,
                        i.current_stock,
                        i.status_indicator,
                        ROW_NUMBER() OVER(PARTITION BY i.center_id, i.product_id ORDER BY i.report_date DESC) as rn
                    FROM inventory i
                    JOIN medical_centers mc ON i.center_id = mc.center_id
                    WHERE mc.region_id = %s
                )
                SELECT
                    p.name as medicine_name,
                    mc.name as center_name,
                    li.current_stock,
                    li.status_indicator
                FROM LatestInventory li
                JOIN products p ON li.product_id = p.product_id
                JOIN medical_centers mc ON li.center_id = mc.center_id
                WHERE li.rn = 1 AND li.status_indicator IN ('Substock', 'Desabastecido')
                ORDER BY mc.name, p.name;
            """
            cur.execute(query, (region_id,))
            results = cur.fetchall()

            if results:
                return {"status": "success", "report": [dict(row) for row in results]}
            
            return {"status": "no_issues_found", "message": f"No se encontraron problemas de bajo stock o desabastecimiento en la región '{region_name}'."}

    except psycopg2.Error as e:
        return {"status": "error", "error_message": f"Error de base de datos: {e}"}
    finally:
        if conn: conn.close()


def get_consumption_trends(medicine_name: str, region_name: str) -> dict:
    """
    Analiza las tendencias de consumo de un medicamento específico en una región.
    Devuelve el consumo promedio mensual y datos históricos.
    """
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "error_message": "La conexión a la base de datos falló."}

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # 1. Encontrar product_id y region_id
            cur.execute("SELECT product_id FROM products WHERE name ILIKE %s LIMIT 1;", (f"%{medicine_name}%",))
            product_result = cur.fetchone()
            if not product_result:
                return {"status": "medicine_not_found", "error_message": f"Medicamento '{medicine_name}' no encontrado."}
            product_id = product_result['product_id']

            cur.execute("SELECT region_id FROM regions WHERE name ILIKE %s LIMIT 1;", (f"%{region_name}%",))
            region_result = cur.fetchone()
            if not region_result:
                return {"status": "region_not_found", "error_message": f"Región '{region_name}' no encontrada."}
            region_id = region_result['region_id']

            # 2. Calcular el consumo promedio y obtener datos históricos
            query = """
                SELECT
                    mc.name as center_name,
                    i.report_date,
                    i.avg_monthly_consumption,
                    i.last_month_consumption,
                    i.accumulated_consumption_12m
                FROM inventory i
                JOIN medical_centers mc ON i.center_id = mc.center_id
                WHERE i.product_id = %s AND mc.region_id = %s
                ORDER BY mc.name, i.report_date DESC;
            """
            cur.execute(query, (product_id, region_id))
            results = cur.fetchall()

            if results:
                trends = []
                for row in results:
                    row_dict = dict(row)
                    row_dict['report_date'] = row_dict['report_date'].isoformat()
                    trends.append(row_dict)
                return {"status": "success", "trends": trends}

            return {"status": "no_data_found", "message": f"No se encontraron datos de consumo para '{medicine_name}' en la región '{region_name}'."}

    except psycopg2.Error as e:
        return {"status": "error", "error_message": f"Error de base de datos: {e}"}
    finally:
        if conn: conn.close()

def find_most_consumed_medicine_by_region(region_name: str) -> dict:
    """
    Encuentra el medicamento con el mayor consumo mensual promedio en una región específica.
    """
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "error_message": "La conexión a la base de datos falló."}

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # 1. Encontrar el region_id
            cur.execute("SELECT region_id FROM regions WHERE name ILIKE %s LIMIT 1;", (f"%{region_name}%",))
            region_result = cur.fetchone()
            if not region_result:
                return {"status": "region_not_found", "error_message": f"Región '{region_name}' no encontrada."}
            region_id = region_result['region_id']

            # 2. Encontrar el producto más consumido en esa región
            query = """
                SELECT
                    p.name AS medicine_name,
                    SUM(i.avg_monthly_consumption) AS total_monthly_consumption
                FROM inventory i
                JOIN products p ON i.product_id = p.product_id
                JOIN medical_centers mc ON i.center_id = mc.center_id
                WHERE mc.region_id = %s AND i.avg_monthly_consumption IS NOT NULL
                GROUP BY p.name
                ORDER BY total_monthly_consumption DESC
                LIMIT 1;
            """
            cur.execute(query, (region_id,))
            result = cur.fetchone()

            if result:
                return {"status": "success", "data": dict(result)}
            
            return {"status": "no_data_found", "message": f"No se encontraron datos de consumo para la región '{region_name}'."}

    except psycopg2.Error as e:
        return {"status": "error", "error_message": f"Error de base de datos: {e}"}
    finally:
        if conn: conn.close()


def find_top_consuming_region_for_medicine(medicine_name: str) -> dict:
    """
    Encuentra la región que más ha consumido un medicamento específico, basado en el consumo mensual promedio.
    """
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "error_message": "La conexión a la base de datos falló."}

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # 1. Encontrar el product_id
            cur.execute("SELECT product_id FROM products WHERE name ILIKE %s LIMIT 1;", (f"%{medicine_name}%",))
            product_result = cur.fetchone()
            if not product_result:
                return {"status": "medicine_not_found", "error_message": f"Medicamento '{medicine_name}' no encontrado."}
            product_id = product_result['product_id']

            # 2. Encontrar la región con el mayor consumo de ese producto
            query = """
                SELECT
                    r.name AS region_name,
                    SUM(i.avg_monthly_consumption) AS total_monthly_consumption
                FROM inventory i
                JOIN medical_centers mc ON i.center_id = mc.center_id
                JOIN regions r ON mc.region_id = r.region_id
                WHERE i.product_id = %s AND i.avg_monthly_consumption IS NOT NULL
                GROUP BY r.name
                ORDER BY total_monthly_consumption DESC
                LIMIT 1;
            """
            cur.execute(query, (product_id,))
            result = cur.fetchone()

            if result:
                return {"status": "success", "data": dict(result)}
            
            return {"status": "no_data_found", "message": f"No se encontraron datos de consumo para el medicamento '{medicine_name}'."}

    except psycopg2.Error as e:
        return {"status": "error", "error_message": f"Error de base de datos: {e}"}
    finally:
        if conn: conn.close()

def send_notification_email(recipient_email: str, subject: str, body: str) -> dict:
    """
    Simula el envío de un correo electrónico de notificación a un analista.
    En una aplicación real, esto se integraría con un servicio de correo.
    """
    print("--- SIMULANDO ENVÍO DE CORREO ---")
    print(f"Para: {recipient_email}")
    print(f"Asunto: {subject}")
    print(f"Cuerpo: {body}")
    print("---------------------------------")
    return {"status": "success", "message": "Notificación por correo simulada exitosamente."}
