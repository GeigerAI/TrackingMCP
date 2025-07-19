import requests

url = "https://apis-sandbox.fedex.com/track/v1/trackingnumbers"

payload = input # 'input' refers to JSON Payload
headers = {
    'Content-Type': "application/json",
    'X-locale': "en_US",
    'Authorization': "Bearer "
    }

response = requests.post(url, data=payload, headers=headers)

print(response.text)