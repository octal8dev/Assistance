import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'telegram_bot'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
    'port': os.getenv('DB_PORT', '5432')
}
