import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

# Configure logging to write to a file
handler = RotatingFileHandler('database_operations.log', maxBytes=5*1024*1024, backupCount=3)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[handler])
logger = logging.getLogger(__name__)

# Listen for writes (INSERT, UPDATE, DELETE)
@event.listens_for(Session, 'before_flush')
def log_before_flush(session, flush_context, instances):
    for instance in session.new:
        logger.info(f"New instance added: {instance}")
    for instance in session.dirty:
        logger.info(f"Instance updated: {instance}")
    for instance in session.deleted:
        logger.info(f"Instance deleted: {instance}")

# Listen for SELECT queries (reads)
@event.listens_for(Engine, 'before_cursor_execute')
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    logger.info(f"Executing query: {statement} with parameters {parameters}")

@event.listens_for(Engine, 'after_cursor_execute')
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    logger.info(f"Query executed: {statement}")
