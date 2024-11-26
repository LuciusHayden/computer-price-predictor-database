from model import create_model
import os
import joblib
from bs4 import BeautifulSoup as bs
import requests
import re
import json
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

if (os.path.exists('model.joblib')):
    model = joblib.load('model.joblib')
else:
    model = create_model()

class Laptop:
    def __init__(self, company, cpu, inches, screen_resolution, ram, storage, storage_type, graphics, operating_system, weight):
        self.company = company
        self.inches = inches
        self.screen_resolution = screen_resolution
        self.cpu = cpu
        self.ram = ram
        self.storage = storage
        self.storage_type = storage_type
        self.graphics = graphics
        self.operating_system = operating_system
        self.weight = weight

def extract_number(text):
    # Find all numeric parts and join them as a single number
    match = re.search(r'\d+(\.\d+)?', text)
    return float(match.group()) if match else None

def format_resolution(resolution_text):
    # Extract width and height using regex
    resolution_match = re.findall(r'\d+', resolution_text)
    if len(resolution_match) >= 2:
        width = resolution_match[0]
        height = resolution_match[1]
        return f"{width}x{height}"
    return None

# simplify operating system
# dataset doesnt contain Windows 11, so use windows 10
def simplify_os(os_name):
    if 'Windows 11 Home in S Mode' in os_name:
        return 'Windows 10 S'
    elif 'Windows 11' in os_name:
        return 'Windows 10'
    return os_name

import re

def simplify_cpu(cpu_name):
    # Handle Intel CPUs
    if "Intel" in cpu_name:
        # Match "Core iX" or "Core Ultra X"
        match = re.search(r"Core\s(?:Ultra\s)?(i[3579])", cpu_name)
        if match:
            core_type = match.group(1)
            return f"Intel Core {core_type}"
        elif "Pentium" in cpu_name:
            return "Intel Pentium"
        elif "Celeron" in cpu_name:
            return "Intel Celeron"
        elif "Atom" in cpu_name:
            return "Intel Atom"
        elif "Xeon" in cpu_name:
            return "Intel Xeon"
    
    # Handle AMD CPUs
    if "AMD" in cpu_name:
        if "Ryzen" in cpu_name:
            match = re.search(r"Ryzen\s(\d)", cpu_name)
            if match:
                ryzen_series = match.group(1)
                return f"AMD Ryzen {ryzen_series}"
        elif "A" in cpu_name:
            match = re.search(r"A(\d+)", cpu_name)
            if match:
                a_series = match.group(1)
                return f"AMD A{a_series}-Series"
        elif "FX" in cpu_name:
            return "AMD FX-Series"
        elif "E-Series" in cpu_name:
            return "AMD E-Series"
    
    # Return original if no match found
    return cpu_name

session = requests.Session()
url = "https://www.bestbuy.com/site/all-laptops/pc-laptops/pcmcat247400050000.c?id=pcmcat247400050000"
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}) 

html = session.get(url).text
soup = bs(html, 'html.parser')

laptops =  soup.find_all('a', {'class' :'image-link'})

for _laptop in laptops:
    siteHtml = session.get(f"https://bestbuy.com{_laptop['href']}").text
    soup_ = bs(siteHtml, 'html.parser')
    details = soup_.find_all('script', {'type' : 'application/json'})
    data = json.loads(details[2].text)
   
    for category in data['specifications']['categories']:
        for spec in category["specifications"]:
        
            spec_name = spec.get("displayName", "N/A")
            spec_value = spec.get("value", "N/A")
            spec_definition = spec.get("definition", "No description")

            match spec_name:
                case "Brand":
                    company = spec_value
                case "Screen Size":
                    inches = spec_value
                case "Screen Resolution":
                    screen_resolution = spec_value
                case "Processor Model":
                    cpu = spec_value
                case "System Memory (RAM)":
                    ram = spec_value
                case "Total Storage Capacity":
                    storage = spec_value
                case "Storage Type":
                    storage_type = spec_value
                case "Graphics":
                    graphics = spec_value
                case "Operating System":
                    operating_system = spec_value
                case "Product Weight":
                    weight = spec_value
                case _:
                    pass
    
    print("\n")

    laptop = Laptop(company, cpu, inches, screen_resolution, ram, storage, storage_type, graphics, operating_system, weight)   


    data = (company, simplify_cpu(laptop.cpu), extract_number(laptop.inches),
             screen_resolution, int(extract_number(laptop.ram)), storage, storage_type,
               graphics, operating_system, float(extract_number(laptop.weight)))

    conn = mysql.connector.connect(
        host="localhost",      
        user="root",          
        database="computer_database",
        # password=os.getenv("DB_PASSWORD")
        password=os.getenv("DB_PASSWORD")
    )

    cursor = conn.cursor()

    try:
        query = "INSERT INTO laptops (company, cpu, inches, screen_resolution, ram, storage, storage_type, graphics, operating_system, weight) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, data)

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    conn.commit()

    data_frame = pd.DataFrame({
        'Company': [laptop.company.strip()],
        'Inches': [extract_number(laptop.inches)],
        'Cpu': [simplify_cpu(laptop.cpu)],
        'Ram': [int(extract_number(laptop.ram))],
        'Gpu': [laptop.graphics], 
        'OpSys': [simplify_os(laptop.operating_system)],
        'Weight': [float(extract_number(laptop.weight))],
        'Resolution': [format_resolution(laptop.screen_resolution)],
        'Memory': [f"{int(extract_number(laptop.storage))}GB {laptop.storage_type}"],
    })

    # print(data_frame)

    y_pred = model.predict(data_frame)
    # print(f"Predicted Price: {y_pred * 1.06} - https://bestbuy.com{_laptop['href']}") # euros to usd


