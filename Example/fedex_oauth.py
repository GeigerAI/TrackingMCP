import requests

url = "https://apis-sandbox.fedex.com/oauth/token"

payload = input # 'input' refers to JSON Payload
headers = {
    'Content-Type': "application/x-www-form-urlencoded"
    }

response = requests.post(url, data=payload, headers=headers)

print(response.text)