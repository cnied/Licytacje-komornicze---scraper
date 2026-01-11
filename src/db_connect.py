import os
import psycopg2
from dotenv import load_dotenv
from psycopg2 import OperationalError, Error
from .logger import setup_logger


logger = setup_logger("DB_CONNECT")

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
        logger.info("Successfully connected to PostgreSQL")
        return conn, None
    except OperationalError as e:
        logger.error("Error while connecting to PostgreSQL: %s", e)
        return None, e
    except Error as e:
        logger.error("Other error: %s", e)
        return None, e

if __name__ == "__main__":
    db_login()
