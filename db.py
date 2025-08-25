import psycopg2
from psycopg2 import sql
from db_config import DATABASE_CONFIG
import logging

def get_connection():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        return conn
    except psycopg2.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def create_db():
    conn = get_connection()
    if conn is None:
        logging.error("Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id BIGINT PRIMARY KEY,
            expiration_date TIMESTAMP NOT NULL
        )
        ''')
        conn.commit()
        logging.info("Database tables created successfully")
    except psycopg2.Error as e:
        logging.error(f"Error creating tables: {e}")
    finally:
        cursor.close()
        conn.close()

def add_subscription(user_id, expiration_date):
    conn = get_connection()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO subscriptions (user_id, expiration_date) 
        VALUES (%s, %s)
        ON CONFLICT (user_id) 
        DO UPDATE SET expiration_date = EXCLUDED.expiration_date
        ''', (user_id, expiration_date))
        conn.commit()
    except psycopg2.Error as e:
        logging.error(f"Error adding subscription: {e}")
    finally:
        cursor.close()
        conn.close()

def get_subscription_status(user_id):
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT expiration_date FROM subscriptions WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        if result:
            expiration_date = result[0]
            # Handle timezone-aware datetime
            if hasattr(expiration_date, 'replace') and expiration_date.tzinfo is not None:
                expiration_date = expiration_date.replace(tzinfo=None)
            return expiration_date
        return None
    except psycopg2.Error as e:
        logging.error(f"Error getting subscription status: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def database_exists():
    """Check if the database exists"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False

def create_database():
    """Create the database if it doesn't exist"""
    db_config = DATABASE_CONFIG.copy()
    db_name = db_config.pop('database')
    
    try:
        # Connect to PostgreSQL server (not specific database)
        db_config['database'] = 'postgres'
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if cursor.fetchone():
            print(f"База данных '{db_name}' уже существует!")
            return True
        
        # Create database
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        print(f"База данных '{db_name}' успешно создана!")
        return True
        
    except psycopg2.Error as e:
        logging.error(f"Ошибка при создании базы данных: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def check_tables_exist():
    """Check if tables exist in the database"""
    conn = get_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'subscriptions'
        )
        """)
        return cursor.fetchone()[0]
    except psycopg2.Error as e:
        logging.error(f"Ошибка при проверке таблиц: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_all_subscriptions():
    """Get all active subscriptions"""
    conn = get_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, expiration_date FROM subscriptions')
        results = cursor.fetchall()
        return results
    except psycopg2.Error as e:
        logging.error(f"Error getting all subscriptions: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def remove_expired_subscription(user_id):
    """Remove expired subscription"""
    conn = get_connection()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM subscriptions WHERE user_id = %s', (user_id,))
        conn.commit()
        logging.info(f"Removed expired subscription for user {user_id}")
    except psycopg2.Error as e:
        logging.error(f"Error removing expired subscription: {e}")
    finally:
        cursor.close()
        conn.close()
