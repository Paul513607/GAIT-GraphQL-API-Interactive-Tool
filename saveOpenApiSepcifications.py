import requests

response = requests.get("http://127.0.0.1:8000/openapi.json")
with open("apiSpecifications.json", "w", encoding="utf-8") as file:
    file.write(response.text)