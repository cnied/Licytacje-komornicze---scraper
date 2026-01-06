import os
import psycopg2
from dotenv import load_dotenv
from psycopg2 import OperationalError, Error

load_dotenv(".env")

DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_HOST = os.getenv("DB_HOST", "LicytacjeKomornicze")
DB_PORT = int(os.getenv("DB_PORT", 5432))

def db_login():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        return conn, None
    except OperationalError as e:
        print("Error while connecting to PostgreSQL:", e)
        return None, e
    except Error as e:
        print("Other error:", e)
        return None, e

if __name__ == "__main__":
    db_login()
