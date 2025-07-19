import requests

url = "https://wwwcie.ups.com/security/v1/oauth/token"

payload = {
  "grant_type": "authorization_code",
  "code": "string",
  "redirect_uri": "string",
  "code_verifier": "string",
  "client_id": "string"
}

headers = {"Content-Type": "application/x-www-form-urlencoded"}

response = requests.post(url, data=payload, headers=headers, auth=('<username>','<password>'))

data = response.json()
print(data)