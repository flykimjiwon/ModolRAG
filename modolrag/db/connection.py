"""PostgreSQL connection pool management with asyncpg."""

import asyncpg
from pathlib import Path

_pool: asyncpg.Pool | None = None

SCHEMA_SQL = Path(__file__).parent / "schema.sql"


async def get_pool(dsn: str | None = None) -> asyncpg.Pool:
    """Get or create the connection pool.
    
    Args:
        dsn: PostgreSQL connection string. If None, uses POSTGRES_URI from settings.
        
    Returns:
        asyncpg.Pool: Connection pool instance.
    """
    global _pool
    if _pool is None:
        if dsn is None:
            from modolrag.config import get_settings
            dsn = get_settings().POSTGRES_URI
        
        # Initialize connection with pgvector support
        async def init_connection(conn):
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            # Register halfvec type codec for pgvector
            await conn.set_type_codec(
                'halfvec',
                encoder=lambda v: v,
                decoder=lambda v: v,
                schema='public',
                format='text'
            )
        
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=2,
            max_size=10,
            init=init_connection
        )
    return _pool


async def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def init_schema(dsn: str | None = None):
    """Initialize database schema from schema.sql.
    
    Creates all tables, indexes, and extensions defined in schema.sql.
    Safe to call multiple times (uses IF NOT EXISTS).
    
    Args:
        dsn: PostgreSQL connection string. If None, uses POSTGRES_URI from settings.
    """
    pool = await get_pool(dsn)
    schema_sql = SCHEMA_SQL.read_text()
    async with pool.acquire() as conn:
        await conn.execute(schema_sql)


async def execute(query: str, *args):
    """Execute a query without returning results.
    
    Args:
        query: SQL query string.
        *args: Query parameters.
        
    Returns:
        Query result (usually a status string).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def fetch(query: str, *args):
    """Fetch multiple rows.
    
    Args:
        query: SQL query string.
        *args: Query parameters.
        
    Returns:
        List of asyncpg.Record objects.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(query: str, *args):
    """Fetch a single row.
    
    Args:
        query: SQL query string.
        *args: Query parameters.
        
    Returns:
        asyncpg.Record or None if no rows found.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetchval(query: str, *args):
    """Fetch a single value.
    
    Args:
        query: SQL query string.
        *args: Query parameters.
        
    Returns:
        Single value or None if no rows found.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)
