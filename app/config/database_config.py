import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Dict, Any
from datetime import datetime
import json

class DatabaseConfig:
    def __init__(self):
        self.connection_params = {
            "host": "ep-billowing-salad-a8vln0qo-pooler.eastus2.azure.neon.tech",
            "user": "neondb_owner",
            "port": 5432,
            "database": "new_db_telecom",
            "password": "npg_HyTzNd9bop2S",
            "sslmode": "require"
        }

    def get_connection(self):
        """Get database connection with error handling"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except Exception as e:
            print(f"Database connection failed: {e}")
            return None

    def execute_query(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """Execute query safely with parameterized inputs"""
        conn = self.get_connection()
        if not conn:
            return {"error": "Database connection failed"}

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    # Convert datetime objects to strings to make them JSON serializable
                    serializable_result = []
                    for row in result:
                        serializable_row = {}
                        for key, value in dict(row).items():
                            if isinstance(value, datetime):
                                # Ensure datetime objects are converted into strings
                                serializable_row[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                serializable_row[key] = value
                        serializable_result.append(serializable_row)

                    return {"success": True, "data": serializable_result}

                else:
                    conn.commit()
                    return {"success": True, "affected_rows": cursor.rowcount}

        except Exception as e:
            conn.rollback()
            return {"error": str(e)}

        finally:
            conn.close()

    def execute_update(self, query: str, params: tuple) -> bool:
        """
        Executes an INSERT, UPDATE, or DELETE query.

        Args:
            query (str): SQL query with placeholders (%s).
            params (tuple): Parameters for the query.

        Returns:
            bool: True if executed successfully, False otherwise.
        """
        conn = self.get_connection()
        if not conn:
            return {"error": "Database connection failed"}
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"❌ Error executing update: {e}")
            return False
        finally:
            conn.close()

    def to_json(self, data: Dict[str, Any]) -> str:
        """Convert the result to JSON"""
        return json.dumps(data, default=str)  
    

if __name__ == "__main__":
    db = DatabaseConfig()
    query = """
    SELECT i.*, c.first_name, c.last_name, c.email
            FROM invoices i
            JOIN customers c ON i.customer_id = c.customer_id
            WHERE i.customer_id = %s
            ORDER BY i.invoice_date DESC
            LIMIT 5
    """
    params = ("101")
    result = db.execute_query(query, params)

    if "success" in result and result["success"]:
        json_result = db.to_json(result)
        print(json_result)
    else:
        print("Error:", result.get("error"))