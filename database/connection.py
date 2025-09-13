"""
Advanced PostgreSQL Connection Management for Resume Customizer
High-performance connection pooling, retry logic, and concurrent access support
"""

import os
import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator
from urllib.parse import quote_plus
import threading

from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, OperationalError
from sqlalchemy.pool import QueuePool
import psycopg2
from psycopg2 import OperationalError as PsycopgOperationalError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """
    High-performance database connection manager with advanced features:
    - Connection pooling for concurrent access
    - Automatic retry logic
    - Health monitoring
    - Performance optimization
    - Thread-safe operations
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global connection manager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
            
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._connection_string: Optional[str] = None
        self._is_connected = False
        self._retry_count = 0
        self._max_retries = 3
        self._connection_stats = {
            'total_connections': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'active_connections': 0,
            'pool_size': 0,
            'overflow_connections': 0
        }
        self.initialized = True
    
    def initialize(self, database_url: Optional[str] = None, **kwargs) -> bool:
        """
        Initialize database connection with advanced configuration
        
        Args:
            database_url: PostgreSQL connection string
            **kwargs: Additional engine configuration options
            
        Returns:
            bool: True if initialization successful
        """
        try:
            if not database_url:
                database_url = self._build_connection_string()
            
            self._connection_string = database_url
            
            # Advanced engine configuration for high performance
            engine_config = {
                'echo': False,  # Set to True for SQL debugging
                'poolclass': QueuePool,
                'pool_size': 20,  # Base pool size for concurrent connections
                'max_overflow': 30,  # Additional connections when needed
                'pool_timeout': 30,  # Timeout for getting connection from pool
                'pool_recycle': 3600,  # Recycle connections every hour
                'pool_pre_ping': True,  # Verify connections before use
                'pool_reset_on_return': 'commit',  # Clean state on return
                'connect_args': {
                    'connect_timeout': 10,
                    'application_name': 'ResumeCustomizer',
                    'sslmode': 'require',  # Required for Replit/Neon databases
                    'options': '-c statement_timeout=60000'  # 60 second query timeout
                },
                **kwargs
            }
            
            # Create engine with optimizations
            self.engine = create_engine(database_url, **engine_config)
            
            # Configure session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=True,
                bind=self.engine,
                expire_on_commit=False  # Keep objects accessible after commit
            )
            
            # Add event listeners for monitoring
            self._setup_event_listeners()
            
            # Test connection
            if self._test_connection():
                self._is_connected = True
                logger.info("✅ Database connection initialized successfully")
                return True
            else:
                logger.error("❌ Failed to establish database connection")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string from environment variables"""
        # First, check for DATABASE_URL (preferred for Replit and cloud deployments)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            logger.info("🔗 Using DATABASE_URL for database connection")
            # Extract host info for logging
            try:
                from urllib.parse import urlparse
                parsed = urlparse(database_url)
                logger.info(f"📡 Connecting to database: {parsed.hostname}:{parsed.port or 5432}/{parsed.path[1:] if parsed.path else 'unknown'}")
            except:
                logger.info("📡 Using DATABASE_URL (connection details parsed)")
            return database_url
        
        # Fallback to individual environment variables
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'resume_customizer'),
            'username': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        
        # URL encode password to handle special characters
        password = quote_plus(db_config['password'])
        
        connection_string = (
            f"postgresql://{db_config['username']}:{password}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        logger.info(f"📡 Connecting to database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        return connection_string
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring and optimization"""
        
        @event.listens_for(self.engine, 'connect')
        def on_connect(dbapi_connection, connection_record):
            """Configure connection on creation"""
            self._connection_stats['total_connections'] += 1
            
            # Only set session-level optimizations that work with managed databases
            with dbapi_connection.cursor() as cursor:
                try:
                    # Set only parameters that are typically allowed in managed databases
                    cursor.execute("SET application_name TO 'ResumeCustomizer'")
                    cursor.execute("SET timezone TO 'UTC'")
                    # Skip WAL and checkpoint settings as they require server restart
                except Exception as e:
                    # Ignore connection setup errors for managed databases
                    logger.debug(f"Connection setup warning: {e}")
                
        @event.listens_for(self.engine, 'checkout')
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Track active connections"""
            self._connection_stats['active_connections'] += 1
            
        @event.listens_for(self.engine, 'checkin')
        def on_checkin(dbapi_connection, connection_record):
            """Track connection returns"""
            self._connection_stats['active_connections'] -= 1
            
        @event.listens_for(self.engine, 'invalidate')
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Handle connection invalidation"""
            logger.warning(f"⚠️ Connection invalidated: {exception}")
            
    def _test_connection(self) -> bool:
        """Test database connectivity with retry logic"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1")).fetchone()
                    if result and result[0] == 1:
                        self._connection_stats['successful_connections'] += 1
                        return True
            except Exception as e:
                self._connection_stats['failed_connections'] += 1
                logger.warning(f"⚠️ Connection test failed (attempt {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return False
    
    @contextmanager
    def get_session(self, auto_commit: bool = True) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic error handling
        
        Args:
            auto_commit: Whether to auto-commit on success
            
        Yields:
            Session: SQLAlchemy session object
        """
        if not self._is_connected:
            raise ConnectionError("Database not initialized. Call initialize() first.")
        
        session = self.SessionLocal()
        try:
            yield session
            if auto_commit:
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Database session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_with_retry(self, operation, max_retries: int = 3, *args, **kwargs):
        """
        Execute database operation with automatic retry on failure
        
        Args:
            operation: Function to execute
            max_retries: Maximum number of retry attempts
            *args, **kwargs: Arguments for the operation
            
        Returns:
            Result of the operation
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except (OperationalError, DisconnectionError, PsycopgOperationalError) as e:
                last_exception = e
                logger.warning(f"⚠️ Operation failed (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) + (attempt * 0.1)
                    time.sleep(wait_time)
                    
                    # Try to reconnect if connection is lost
                    if not self._test_connection():
                        logger.info("🔄 Attempting to reconnect to database...")
                        self.reconnect()
            except Exception as e:
                logger.error(f"❌ Non-recoverable error: {e}")
                raise
                
        # If all retries failed
        raise last_exception or Exception("All retry attempts failed")
    
    def reconnect(self) -> bool:
        """Reconnect to database after connection loss"""
        try:
            if self.engine:
                self.engine.dispose()
            return self.initialize(self._connection_string)
        except Exception as e:
            logger.error(f"❌ Reconnection failed: {e}")
            return False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics"""
        if self.engine and hasattr(self.engine.pool, 'size'):
            self._connection_stats.update({
                'pool_size': self.engine.pool.size(),
                'checked_in': self.engine.pool.checkedin(),
                'overflow': self.engine.pool.overflow(),
                'checked_out': self.engine.pool.checkedout()
            })
        
        return self._connection_stats.copy()
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        health_status = {
            'connected': False,
            'response_time_ms': None,
            'pool_status': {},
            'errors': []
        }
        
        try:
            start_time = time.time()
            
            with self.get_session() as session:
                # Test basic query
                session.execute(text("SELECT 1"))
                
                # Test table access
                session.execute(text("SELECT COUNT(*) FROM requirements LIMIT 1"))
                
            end_time = time.time()
            
            health_status.update({
                'connected': True,
                'response_time_ms': round((end_time - start_time) * 1000, 2),
                'pool_status': self.get_connection_stats()
            })
            
        except Exception as e:
            health_status['errors'].append(str(e))
            logger.error(f"❌ Health check failed: {e}")
        
        return health_status
    
    def optimize_database(self):
        """Run database optimization commands"""
        optimization_queries = [
            "ANALYZE;",  # Update table statistics
            "VACUUM (ANALYZE);",  # Cleanup and analyze
            "REINDEX DATABASE resume_customizer;",  # Rebuild indexes
        ]
        
        try:
            with self.get_session() as session:
                for query in optimization_queries:
                    logger.info(f"🔧 Running optimization: {query}")
                    session.execute(text(query))
                    session.commit()
            logger.info("✅ Database optimization completed")
        except Exception as e:
            logger.error(f"❌ Database optimization failed: {e}")
    
    def close(self):
        """Close all database connections"""
        try:
            if self.engine:
                self.engine.dispose()
                self._is_connected = False
                logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing database connections: {e}")

# Global connection manager instance
db_manager = DatabaseConnectionManager()

# Convenience functions for external use
def get_db_session():
    """Get database session context manager"""
    return db_manager.get_session()

def initialize_database(database_url: Optional[str] = None, **kwargs) -> bool:
    """Initialize database connection"""
    return db_manager.initialize(database_url, **kwargs)

def get_database_stats() -> Dict[str, Any]:
    """Get database connection statistics"""
    return db_manager.get_connection_stats()

def database_health_check() -> Dict[str, Any]:
    """Perform database health check"""
    return db_manager.health_check()


