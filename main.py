print("Ahoj, Python funguje!")
import requests

url = "https://api.electree.cz/859182400102993847/prices"

response = requests.get(url)

data = response.json()

for hour in data:
    print(hour)
    import requests

url = "https://api.electree.cz/859182400102993847/prices"

response = requests.get(url)
data = response.json()

print("Hodinové spotové ceny:")

for item in data:
    time = item["timeLocalStart"][11:16]   # vytáhne jen HH:MM
    price_mwh = item["priceCZK"]
    price_kwh = price_mwh / 1000

    print(f"{time}  {price_kwh:.2f} Kč/kWh")