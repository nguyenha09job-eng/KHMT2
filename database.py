import mysql.connector
from mysql.connector import Error


class DatabaseConnection:
    def __init__(self):
        self.config = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "123456",
            "database": "PetHotel",
        }

    def connect(self):
        try:
            conn = mysql.connector.connect(**self.config)
            if conn.is_connected():
                return conn
        except Error as e:
            raise Exception(f"Không thể kết nối MySQL: {e}")

    def fetch_all(self, query, params=None):
        conn = self.connect()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            raise Exception(f"Lỗi truy vấn: {e}")
        finally:
            cursor.close()
            conn.close()

    def fetch_one(self, query, params=None):
        conn = self.connect()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            raise Exception(f"Lỗi truy vấn: {e}")
        finally:
            cursor.close()
            conn.close()

    def execute(self, query, params=None):
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            conn.rollback()
            raise Exception(f"Lỗi thực thi: {e}")
        finally:
            cursor.close()
            conn.close()

    def schema_info(self):
        """Trả về toàn bộ cấu trúc database: bảng, cột, khóa, quan hệ."""
        tables = self.fetch_all("""
            SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, EXTRA
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME, ORDINAL_POSITION
        """, (self.config["database"],))

        foreign_keys = self.fetch_all("""
            SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME,
                   REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY TABLE_NAME
        """, (self.config["database"],))

        return {"columns": tables, "foreign_keys": foreign_keys}


if __name__ == "__main__":
    db = DatabaseConnection()

    print("=" * 70)
    print(" KẾT NỐI DATABASE PetHotel THÀNH CÔNG")
    print("=" * 70)

    schema = db.schema_info()

    # Nhóm cột theo bảng
    tables = {}
    for col in schema["columns"]:
        t = col["TABLE_NAME"]
        if t not in tables:
            tables[t] = []
        tables[t].append(col)

    for table_name, cols in tables.items():
        print(f"\n--- {table_name} ---")
        for c in cols:
            pk_fk = ""
            if c["COLUMN_KEY"] == "PRI":
                pk_fk = " [PK]"
            for fk in schema["foreign_keys"]:
                if fk["TABLE_NAME"] == table_name and fk["COLUMN_NAME"] == c["COLUMN_NAME"]:
                    pk_fk = f" [FK -> {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}]"
            print(f"  {c['COLUMN_NAME']:<25s} {c['COLUMN_TYPE']:<20s} {c['IS_NULLABLE']:<5s}{pk_fk}")

    print("\n" + "=" * 70)
    print(f" Tổng: {len(tables)} bảng, {len(schema['columns'])} cột, {len(schema['foreign_keys'])} khóa ngoại")
    print("=" * 70)
