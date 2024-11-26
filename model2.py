import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host="localhost",      
    user="root",          
    password=os.getenv("DB_PASSWORD"),
    database="computer_database"
)
cursor = conn.cursor()

query = "SELECT * FROM laptops"
data = pd.read_sql(query, con=conn)

data.drop('id', axis=1, inplace=True)

print(data.head())