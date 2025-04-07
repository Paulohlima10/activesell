import sqlite3

class SQLiteSchemaExplorer:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)

    def get_all_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in cursor.fetchall()]

    def get_table_info(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        return cursor.fetchall()

    def filter_tables(self, keywords):
        tables = self.get_all_tables()
        matched_tables = []

        for table in tables:
            columns = self.get_table_info(table)
            column_names = [col[1].lower() for col in columns]

            if any(kw in table.lower() for kw in keywords) or \
               any(kw in col for kw in keywords for col in column_names):
                matched_tables.append(table)

        return matched_tables
