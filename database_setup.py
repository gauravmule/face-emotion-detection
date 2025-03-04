import os
import psycopg2
from psycopg2.extras import DictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_config = {
    "dbname": os.getenv('DB_NAME', 'emotion_db'),
    "user": os.getenv('DB_USER', 'root'),
    "password": os.getenv('DB_PASSWORD', 'admin@123'),
    "host": os.getenv('DB_HOST', 'localhost'),
    "port": os.getenv('DB_PORT', '5432'),
    "cursor_factory": DictCursor
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**db_config)
        logger.info("Database connection successful!")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Connection failed: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to initialize database: No connection")
        return
    try:
        with conn.cursor() as cursor:
            tables = [
                '''CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(128) NOT NULL
                )''',
                '''CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    total_faces INT DEFAULT 0,
                    most_common_emotion VARCHAR(50),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )''',
                '''CREATE TABLE IF NOT EXISTS emotion_logs (
                    id SERIAL PRIMARY KEY,
                    session_id INT,
                    emotion VARCHAR(50),
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )''',
                '''CREATE TABLE IF NOT EXISTS dashboard_stats (
                    id INT PRIMARY KEY DEFAULT 1,
                    total_sessions INT DEFAULT 0,
                    total_faces_detected INT DEFAULT 0,
                    most_common_emotion VARCHAR(50),
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )'''
            ]
            for table in tables:
                cursor.execute(table)
            cursor.execute('INSERT INTO dashboard_stats (id) VALUES (1) ON CONFLICT (id) DO NOTHING')
            conn.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Init error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()