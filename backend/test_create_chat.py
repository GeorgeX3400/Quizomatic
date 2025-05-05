import requests
import os

# Hardcode the JWT token for testing
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ1OTA0NTI1LCJpYXQiOjE3NDU5MDA5MjUsImp0aSI6IjM1ZWM3MDJiNWViYzQyOWNiN2EyMjcyNzQ2ODc0NjJjIiwidXNlcl9pZCI6Nn0.2iV56jleaChRPrmutwLSaCqMWLQu7cRo3n8eLDeBYgI"  # Replace with a valid token

# API endpoint
url = "http://localhost:8000/chats/create/"

# Headers with Authorization
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

body = {
    "name": "New Chat2", # mai schimba numele
}

try:
    # Make the POST request with proper JSON data
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()  # Raise an error for bad status codes

    # Print the response
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
    print(f"Response: {response.text}")
except requests.exceptions.RequestException as err:
    print(f"Error occurred: {err}")