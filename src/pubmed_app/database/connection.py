from pubmed_app.config import settings, logger

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional
from pathlib import Path

class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None
    _pool: Optional[ThreadedConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize_pool(self,minconn: int = 1, maxconn: int = 10) -> None:
        if self._pool is not None:
            logger.warning("Database connection pool is already initialized.")
            return
        
        logger.info(f"Initializing database connection pool: {settings.DB_NAME}@{settings.DB_HOST}:{settings.DB_PORT}")

        try:
            self._pool = ThreadedConnectionPool(
                minconn,
                maxconn,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                cursor_factory=RealDictCursor
            )
            logger.info(f"Database connection pool initialized successfully with {minconn}-{maxconn} connections.")
        except psycopg2.Error as e:
            logger.error(f"Error initializing database connection pool: {e}")
            raise

    def get_connection(self):
        if self._pool is None:
            self.initialize_pool()
        return self._pool.getconn()
    
    def return_connection(self, conn) -> None:
        if self._pool is not None:
            self._pool.putconn(conn)

    def close_all_connections(self) -> None:
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None
            logger.info("All database connections have been closed.")

db_manager = DatabaseManager()

@contextmanager
def get_db_connection():
    conn = db_manager.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        db_manager.return_connection(conn)

@contextmanager
def get_raw_connection(db_name: Optional[str] = None, autocommit: bool = False):
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=db_name if db_name else settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    conn.autocommit = autocommit
    try:
        yield conn
        if not autocommit:
            conn.commit()
    except Exception as e:
        if not autocommit:
            conn.rollback()
        logger.error(f"Raw database operation failed: {e}")
        raise
    finally:
        conn.close()

@contextmanager
def get_dict_cursor():
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur

def execute_query(query: str, params: tuple = ()) -> list[dict]:
    with get_dict_cursor() as cur:
        cur.execute(query, params)
        results = cur.fetchall()
        return results
    
def execute_single_query(query: str, params: tuple = ()) -> dict:
    with get_dict_cursor() as cur:
        cur.execute(query, params)
        result = cur.fetchone()
        return result
    
def execute_write_query(query: str, params: tuple = ()) -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount
        

def create_database_if_not_exists() -> bool:
    logger.info(f"checking if database {settings.DB_NAME} exists.")

    with get_raw_connection(db_name="postgres", autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.DB_NAME,))
            exists = cur.fetchone()
            if not exists:
                logger.info(f"Database {settings.DB_NAME} does not exist. Creating it.")
                cur.execute(f"CREATE DATABASE {settings.DB_NAME}")
                logger.info(f"Database {settings.DB_NAME} created successfully.")
                return True
            else:
                logger.info(f"Database {settings.DB_NAME} already exists.")
                return False
            
def run_schema(schema_path: Optional[str] = None) -> None:
    if schema_path is None:
        schema_path = Path(__file__).parent / "schema.sql"

    logger.info(f"Running database schema from {schema_path}")

    if not Path(schema_path).exists():
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    schema_sql = Path(schema_path).read_text()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
    logger.info("Database schema executed successfully.")

def  get_table_counts() -> dict[str, int]:
    tables = ['articles', 'authors', 'journals', 'mesh_terms', 'article_authors', 'article_mesh_terms']
    counts = {}
    for table in tables:
        try:
            result = execute_single_query(f"SELECT COUNT(*) AS count FROM {table}")
            counts[table] = result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error getting count for table {table}: {e}")
            counts[table] = -1
    return counts

def verify_tables() -> dict[str, bool]:
    excepted = ['articles', 'authors', 'journals', 'mesh_terms', 'article_authors', 'article_mesh_terms']

    with get_raw_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            existing_tables = {row[0] for row in cur.fetchall()}

    return {table: (table in existing_tables) for table in excepted}

def test_connection() -> bool:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                return result is not None
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False