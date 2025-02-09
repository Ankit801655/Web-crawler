import psycopg2

class DBHandler:
    def __init__(self, db_config):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS product_urls (
            id SERIAL PRIMARY KEY,
            domain TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL
        );
        """
        self.cursor.execute(query)
        self.conn.commit()

    def save_product_urls(self, urls):
        query = "INSERT INTO product_urls (domain, url) VALUES %s ON CONFLICT (url) DO NOTHING;"
        psycopg2.extras.execute_values(self.cursor, query, urls)
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()
