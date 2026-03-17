"""Database module for ModolRAG.

Provides asyncpg connection pool management and schema initialization.
"""

from modolrag.db.connection import (
    get_pool,
    close_pool,
    init_schema,
    execute,
    fetch,
    fetchrow,
    fetchval,
)

__all__ = [
    "get_pool",
    "close_pool",
    "init_schema",
    "execute",
    "fetch",
    "fetchrow",
    "fetchval",
]
