"""
Database module for storing and managing AI-generated project ideas.
Uses SQLite3 for data persistence with optimized connection handling.
"""

import sqlite3
import json
from contextlib import contextmanager
from typing import List, Dict, Optional
import threading
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ideas.db")
_connection_lock = threading.Lock()


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures proper connection handling and cleanup.
    
    Yields:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    """Initialize the database with required tables and indexes."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                inspiration_link TEXT,
                requirements TEXT NOT NULL,
                functionalities TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                implemented BOOLEAN DEFAULT 0,
                implemented_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_implemented ON ideas(implemented)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON ideas(created_at DESC)
        """)
        
        print(f"✅ Database initialized at {DB_PATH}")


def save_ideas(ideas: List[Dict]) -> List[int]:
    """
    Save ideas to the database using efficient batch insert.
    
    Args:
        ideas: List of idea dictionaries
    
    Returns:
        List of inserted idea IDs
    """
    if not ideas:
        return []
    
    inserted_ids = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(id) FROM ideas")
        max_id_before = cursor.fetchone()[0]
        start_id = (max_id_before or 0) + 1
        
        data = [
            (
                idea.get('title', 'Untitled'),
                idea.get('description', 'No description'),
                idea.get('inspiration_link', ''),
                json.dumps(idea.get('requirements', [])),
                json.dumps(idea.get('functionalities', []))
            )
            for idea in ideas
        ]
        
        cursor.executemany("""
            INSERT INTO ideas (title, description, inspiration_link, requirements, functionalities)
            VALUES (?, ?, ?, ?, ?)
        """, data)
        
        inserted_ids = list(range(start_id, start_id + len(ideas)))
    
    return inserted_ids


def _row_to_dict(row: sqlite3.Row) -> Dict:
    """Convert database row to dictionary efficiently."""
    return {
        'id': row['id'],
        'title': row['title'],
        'description': row['description'],
        'inspiration_link': row['inspiration_link'],
        'requirements': json.loads(row['requirements']),
        'functionalities': json.loads(row['functionalities']),
        'created_at': row['created_at'],
        'implemented': bool(row['implemented']),
        'implemented_at': row['implemented_at']
    }


def get_all_ideas(limit: Optional[int] = None, implemented_only: bool = False) -> List[Dict]:
    """
    Get all ideas from the database with optimized query.
    
    Args:
        limit: Maximum number of ideas to return
        implemented_only: If True, only return implemented ideas
    
    Returns:
        List of idea dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM ideas"
        params: List = []
        
        if implemented_only:
            query += " WHERE implemented = 1"
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        return [_row_to_dict(row) for row in cursor.fetchall()]


def get_idea_by_id(idea_id: int) -> Optional[Dict]:
    """
    Get a specific idea by ID.
    
    Args:
        idea_id: The ID of the idea
    
    Returns:
        Idea dictionary or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None


def mark_idea_implemented(idea_id: int) -> bool:
    """
    Mark an idea as implemented in a single query.
    
    Args:
        idea_id: The ID of the idea to mark
    
    Returns:
        True if successful, False if idea not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ideas 
            SET implemented = 1, implemented_at = CURRENT_TIMESTAMP
            WHERE id = ? AND implemented = 0
        """, (idea_id,))
        return cursor.rowcount > 0


def mark_idea_unimplemented(idea_id: int) -> bool:
    """
    Mark an idea as not implemented.
    
    Args:
        idea_id: The ID of the idea to unmark
    
    Returns:
        True if successful, False if idea not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ideas 
            SET implemented = 0, implemented_at = NULL
            WHERE id = ? AND implemented = 1
        """, (idea_id,))
        return cursor.rowcount > 0


def delete_idea(idea_id: int) -> bool:
    """
    Delete an idea from the database.
    
    Args:
        idea_id: The ID of the idea to delete
    
    Returns:
        True if successful, False if idea not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
        return cursor.rowcount > 0


def get_idea_count() -> Dict[str, int]:
    """
    Get statistics about ideas in the database using a single query.
    
    Returns:
        Dictionary with total, implemented, and unimplemented counts
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN implemented = 1 THEN 1 ELSE 0 END) as implemented
            FROM ideas
        """)
        row = cursor.fetchone()
        total = row['total']
        implemented = row['implemented'] or 0
        
        return {
            'total': total,
            'implemented': implemented,
            'unimplemented': total - implemented
        }
