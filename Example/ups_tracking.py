import requests

inquiry_number = "YOUR_inquiryNumber_PARAMETER"
url = "https://wwwcie.ups.com/api/track/v1/details/" + inquiry_number

query = {
  "locale": "en_US",
  "returnSignature": "false",
  "returnMilestones": "false",
  "returnPOD": "false"
}

headers = {
  "transId": "string",
  "transactionSrc": "testing",
  "Authorization": "Bearer <YOUR_TOKEN_HERE>"
}

response = requests.get(url, headers=headers, params=query)

data = response.json()
print(data)