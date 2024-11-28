import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
import os

def create_database():
    load_dotenv()

    conn = None
    cursor = None

    try:
        # Establishing the connection
        conn = mysql.connector.connect(
            host="localhost",      
            user="root",          
            password=os.getenv("DB_PASSWORD")
        )

        # Create a cursor object to interact with the MySQL server
        cursor = conn.cursor()

        # Database name
        database_name = "computer_database"

        # Check if the database exists
        cursor.execute("SHOW DATABASES LIKE %s", (database_name,))
        result = cursor.fetchone()
        if result:
            print(f"Database '{database_name}' already exists.")
        else:
            # SQL query to create a new database
            create_database_query = f"CREATE DATABASE {database_name}"
            cursor.execute(create_database_query)
            print(f"Database '{database_name}' created successfully!")

        # Switch to the newly created (or existing) database
        conn.database = database_name

        # Check if the 'laptops' table exists
        cursor.execute("SHOW TABLES LIKE 'laptops'")
        result = cursor.fetchone()
        if result:
            print("Table 'laptops' already exists.")
        else:
            # SQL query to create the 'laptops' table
            create_table_query = """
            CREATE TABLE laptops (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company VARCHAR(50) NOT NULL,
                cpu VARCHAR(255) NOT NULL,
                inches DECIMAL(3,1),
                screen_resolution VARCHAR(50),
                ram VARCHAR(255),
                storage VARCHAR(50),
                storage_type VARCHAR(50),
                graphics VARCHAR(50),
                operating_system VARCHAR(50),
                weight DECIMAL(5,2),
                price DECIMAL(10,2),
                UNIQUE (company, cpu, ram, storage, graphics, weight, inches, screen_resolution, operating_system, price)
            );
            """
            cursor.execute(create_table_query)
            print("Table 'laptops' created successfully.")

        # Commit the changes
        conn.commit()

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Access denied. Check your username or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"Database '{database_name}' does not exist.")
        else:
            print(err)

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

create_database()