import sqlite3
from datetime import datetime, timedelta
from sqlite3 import Connection

DATABASE_NAME = "amazon_scraper.db"


def create_connection() -> Connection:
    """
    Create a connection to the database.

    Returns:
        Connection: The sqlite3 Connection object.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    return conn


def create_tables(conn: Connection):
    """
    Create the necessary tables for the application.

    Args:
        conn (Connection): The sqlite3 Connection object.
    """
    cursor = conn.cursor()

    # Drop the old table if it exists
    cursor.execute("DROP TABLE IF EXISTS search_history;")

    # Create the new table with the updated schema
    cursor.execute("""
    CREATE TABLE search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        Query TEXT NOT NULL,
        Time DATETIME,
        Item_name TEXT,
        Amazon_US REAL,
        Amazon_UK REAL,
        Amazon_DE REAL,
        Amazon_CA REAL
    )
    """)

    conn.commit()


def save_search_history(conn: Connection, user_id: int, query: str):
    """
    Save the search history to the database.

    Args:
        conn (Connection): The sqlite3 Connection object.
        user_id (int): The user ID.
        query (str): The search query string.
    """
    cursor = conn.cursor()

    time = datetime.now().replace(microsecond=0)

    cursor.execute("INSERT INTO search_history (user_id, query, Time) VALUES (?, ?, ?)", (user_id, query, time))
    conn.commit()
    return cursor.lastrowid


def save_price_comparison(conn: Connection, item_title, prices_tuple: tuple, user_id):
    """
    Save the price comparison results to the database.

    Args:
        conn (Connection): The sqlite3 Connection object.
        item_title (str): The item title.
        prices_tuple (tuple): Tuple containing the prices from different Amazon domains.
        user_id (int): The user ID.
    """
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE search_history
    SET Item_name = ?, Amazon_US = ?, Amazon_UK = ?, Amazon_DE = ?, Amazon_CA = ?
    WHERE id = (SELECT MAX(id) FROM search_history WHERE user_id = ?)
    """, (item_title, *prices_tuple, user_id))
    conn.commit()


def get_searches_count_last_24_hours(conn, user_id=1):
    """
    Get the number of searches made by a user in the last 24 hours.

    Args:
        conn (Connection): The sqlite3 Connection object.
        user_id (int): The user ID.

    Returns:
        int: The count of searches made by the user in the last 24 hours.
    """
    curr_time = datetime.now()
    past_24_hours = curr_time - timedelta(hours=24)

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM search_history
        WHERE search_history.user_id = ? AND Time >= ?;
        """, (user_id, past_24_hours,)
    )
    count = cursor.fetchone()[0]
    return count


def get_user_search_history(conn: Connection, user_id: int):
    """
    Retrieve the search history of a user.

    Args:
        conn (Connection): The sqlite3 Connection object.
        user_id (int): The user ID.

    Returns:
        list[dict]: A list of dictionaries containing the search history of the user.
    """
    cursor = conn.cursor()
    cursor.execute("""
    SELECT *
    FROM search_history
    WHERE user_id = ?
    ORDER BY Time DESC
    """, (user_id,))

    search_history = cursor.fetchall()
    # Get column names from the cursor description
    column_names = [desc[0] for desc in cursor.description]
    # Convert search_history into a list of dictionaries
    search_history = [dict(zip(column_names, record)) for record in search_history]

    return search_history


if __name__ == "__main__":
    conn = create_connection()
    create_tables(conn)
