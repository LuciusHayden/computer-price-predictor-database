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
import re
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

def scrape_laptops(url):
    html = session.get(url).text
    soup = bs(html, 'html.parser')
    laptops =  soup.find_all('a', {'class' :'image-link'})
    next_page = soup.find('a', {'class' : 'sku-list-page-next'})
    spans = soup.find_all('span', {'class' : "sr-only"})
    err_num = 0
    success_num = 0

    for span in spans:
        if "Page 1. Selected." in span.text:
            selected_page = span.text
            print(selected_page)

    link = next_page['href']
   
    print(f'https://bestbuy.com{link}')
    for _laptop in laptops:
        try:
            print(f"{err_num} failures")
            print(f"{success_num} successes")
            siteHtml = session.get(f"https://bestbuy.com{_laptop['href']}").text
            soup_ = bs(siteHtml, 'html.parser')
            details = soup_.find_all('script', {'type' : 'application/json'})
            data = json.loads(details[2].text)
        
            price = json.loads(details[4].text)['app']['data']['customerPrice']
            
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

            laptop = Laptop(company, cpu, inches, screen_resolution, ram, storage, storage_type, graphics, operating_system, weight)   

            data = (company, laptop.cpu, extract_number(laptop.inches),
                        format_resolution(screen_resolution), int(extract_number(laptop.ram)), storage, storage_type,
                        graphics, operating_system, float(extract_number(laptop.weight)), price)

            conn = mysql.connector.connect(
                host="localhost",      
                user="root",          
                database="computer_database",
                password=os.getenv("DB_PASSWORD")
            )

            cursor = conn.cursor()

            try:
                query = "INSERT INTO laptops (company, cpu, inches, screen_resolution, ram, storage, storage_type, graphics, operating_system, weight, price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query, data)
                success_num +=1

            except mysql.connector.Error as err:
                err_num +=1
                # print(f"Error: {err}")
                # print("\n")

            conn.commit()
            os.system('clear')
        

        except Exception as e:
            # print(e)
            # print("failed to scrape laptop")
            # print("\n")
            err_num +=1

    try:
        print(f'https://bestbuy.com{link}')
        scrape_laptops(f"https://www.bestbuy.com{link}")
    except Exception as e:
        print(" \n No next page")

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

session = requests.Session()
url = "https://www.bestbuy.com/site/all-laptops/pc-laptops/pcmcat247400050000.c?id=pcmcat247400050000"
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}) 

load_dotenv()

if (os.path.exists('model.joblib')):
    model = joblib.load('model.joblib')
else:
    model = create_model()
  
scrape_laptops(url)