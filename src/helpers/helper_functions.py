import sqlite3
import pandas as pd

def display_table(table_name, db_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    
    # Create SQL query to fetch the table
    query = f"SELECT * FROM {table_name}"
    
    # Load data into a pandas DataFrame
    df = pd.read_sql_query(query, conn)
    
    # Close the connection
    conn.close()
    
    # Display the DataFrame
    df
    return df

def get_column_names(db_path, table):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    conn.close()
    return columns


def get_table_list(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return tables