import os
import psycopg2
from typing import Optional
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

# --- Herramientas de Consulta (Para el Agente Público) ---

def find_medicine_details_by_name(medicine_name: str) -> dict:
    """
    Busca detalles específicos de medicamentos que coincidan con un nombre dado.
    Proporciona detalles como código, descripción, dosis y concentración.
    """
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "error_message": "La conexión a la base de datos falló."}

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            query = sql.SQL("""
                SELECT product_id, code, name, description, dosage_form, strength
                FROM products
                WHERE name ILIKE %s ORDER BY name LIMIT 20;
            """)
            cur.execute(query, (f"%{medicine_name}%",))
            results = cur.fetchall()
            if results:
                return {"status": "success", "medicines": [dict(row) for row in results]}
            return {"status": "not_found", "medicines": []}
    except psycopg2.Error as e:
        return {"status": "error", "error_message": f"Error de base de datos: {e}"}
    finally:
        if conn: conn.close()

def find_centers_with_stock_by_medicine(medicine_name: str) -> dict:
    """
    Encuentra centros médicos en TODAS las regiones que tienen stock (>0) de un medicamento.
    """
    # Esta función es un caso especial de la búsqueda por región, sin filtro de región.
    return find_centers_with_stock_by_medicine_region(medicine_name, region_name=None)

def find_centers_with_stock_by_medicine_region(medicine_name: str, region_name: Optional[str] = None) -> dict:
    """
    Encuentra centros médicos con stock (>0) de un medicamento, opcionalmente filtrando por región.
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

            # 2. Construir la consulta base
            query_sql = """
                SELECT DISTINCT ON (mc.center_id)
                    mc.name AS center_name, mc.address, r.name AS region_name,
                    i.current_stock, i.report_date, i.status_indicator,
                    mc.latitude, mc.longitude
                FROM inventory i
                JOIN medical_centers mc ON i.center_id = mc.center_id
                JOIN regions r ON mc.region_id = r.region_id
                WHERE i.product_id = %s AND i.current_stock > 0
            """
            params = [product_id]

            # 3. Añadir filtro de región si se proporciona
            if region_name:
                cur.execute("SELECT region_id FROM regions WHERE name ILIKE %s LIMIT 1;", (f"%{region_name}%",))
                region_result = cur.fetchone()
                if not region_result:
                    return {"status": "region_not_found", "error_message": f"Región '{region_name}' no encontrada."}
                
                query_sql += " AND mc.region_id = %s"
                params.append(region_result['region_id'])

            query_sql += " ORDER BY mc.center_id, i.report_date DESC;"
            
            cur.execute(query_sql, tuple(params))
            results = cur.fetchall()

            if results:
                centers_found = []
                for row in results:
                    row_dict = dict(row)
                    row_dict['report_date'] = row_dict['report_date'].isoformat() if row_dict.get('report_date') else None
                    centers_found.append(row_dict)
                return {"status": "success", "centers": centers_found}
            
            message = f"No se encontraron centros con stock para '{medicine_name}'."
            if region_name:
                message += f" en la región '{region_name}'."
            return {"status": "no_centers_found", "centers": [], "message": message}

    except psycopg2.Error as e:
        return {"status": "error", "error_message": f"Error de base de datos: {e}"}
    finally:
        if conn: conn.close()

def get_stock_details_for_medicine_at_center(medicine_name: str, center_name: str) -> dict:
    """
    Obtiene los detalles de stock más recientes para un medicamento en un centro médico específico.
    """
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "error_message": "La conexión a la base de datos falló."}

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            query = """
                SELECT
                    p.name as medicine_name, mc.name as center_name,
                    i.current_stock, i.report_date, i.status_indicator, i.avg_monthly_consumption
                FROM inventory i
                JOIN products p ON i.product_id = p.product_id
                JOIN medical_centers mc ON i.center_id = mc.center_id
                WHERE p.name ILIKE %s AND mc.name ILIKE %s
                ORDER BY i.report_date DESC
                LIMIT 1;
            """
            cur.execute(query, (f"%{medicine_name}%", f"%{center_name}%"))
            stock_result = cur.fetchone()

            if stock_result:
                details = dict(stock_result)
                details['report_date'] = details['report_date'].isoformat() if details.get('report_date') else None
                return {"status": "success", "details": details}
            
            return {"status": "stock_not_found", "error_message": f"No se encontró stock para '{medicine_name}' en '{center_name}'."}
    except psycopg2.Error as e:
        return {"status": "error", "error_message": f"Error de base de datos: {e}"}
    finally:
        if conn: conn.close()

def list_all_regions() -> dict:
    """Lista todas las regiones disponibles en la base de datos."""
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "error_message": "La conexión a la base de datos falló."}

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT name FROM regions ORDER BY name;")
            return {"status": "success", "regions": [row['name'] for row in cur.fetchall()]}
    except psycopg2.Error as e:
        return {"status": "error", "error_message": f"Error de base de datos: {e}"}
    finally:
        if conn: conn.close()

def search_medicines_by_name(search_term: str) -> dict:
    """Busca medicamentos disponibles por nombre (limitado a 20 resultados)."""
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "error_message": "La conexión a la base de datos falló."}

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            query = sql.SQL("SELECT name FROM products WHERE name ILIKE %s ORDER BY name LIMIT 20;")
            cur.execute(query, (f"%{search_term}%",))
            results = cur.fetchall()
            if results:
                return {"status": "success", "medicines": [row['name'] for row in results]}
            return {"status": "not_found", "medicines": []}
    except psycopg2.Error as e:
        return {"status": "error", "error_message": f"Error de base de datos: {e}"}
    finally:
        if conn: conn.close()
