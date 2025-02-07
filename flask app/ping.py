import time
import requests

url = "https://css-sit-in-monitoring-system.onrender.com" 

while True:
    try:
        response = requests.get(url)
        print(f"Ping successful: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    time.sleep(180) 
