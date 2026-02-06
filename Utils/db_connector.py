import mysql.connector
from mysql.connector import Error
import builtins


class DBConnector:
    def __init__(self, host=None, port=None, user=None, password=None, database=None):
        """
        Initialize the database connection using configuration or provided parameters.
        """
        self.host = host or "127.0.0.1"
        self.port = port or "3306"
        self.user = user or "root"
        self.password = password or "22132213"
        self.database = database or "testdb"
        self.connection = None

    def connect(self):
        """Establish the database connection."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            if self.connection.is_connected():
                print(f"✓ Connected to MySQL database: {self.database}")
                return self.connection
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            return None

    def execute_query(self, query):
        """Execute a query and return results."""
        if not self.connection or not self.connection.is_connected():
            self.connect()

        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"❌ Error executing query: {e}")
            return None
        finally:
            cursor.close()

    def close(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✓ MySQL connection closed")
