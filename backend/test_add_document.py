import requests
import os
import base64

# Hardcode the JWT token for testing
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ2MDEwMjkwLCJpYXQiOjE3NDYwMDY2OTAsImp0aSI6ImEzYmE5MDQzMTE3MTQ4YzVhYzNlY2JjZThiYjY3NDJlIiwidXNlcl9pZCI6NX0.5uX58dOHjKfSxqdH3ZKjpHXlcVOpbTIvgz0mrSLQx8A"

# Specify the filename in the current directory
filename = "sampleunsecuredpdf.pdf"  # Replace with your file name

# Ensure the file exists in the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, filename)
if not os.path.exists(file_path):
    print(f"Error: File '{filename}' not found in {current_dir}")
    exit(1)

# API endpoint - Update this to the correct endpoint for file upload
url = "http://localhost:8000/documents/add/"  

# Headers with Authorization
headers = {
    "Authorization": f"Bearer {token}",
}

files = {
    'file': open(file_path, 'rb')
}

data = {
    'name': 'Sample PDF Document',
    'chat_id': 3
}

try:
    # Make the POST request with multipart form data
    response = requests.post(url, headers=headers, files=files, data=data)
    response.raise_for_status()  # Raise an error for bad status codes

    # Print the response
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
    print(f"Response: {response.text}")
except requests.exceptions.RequestException as err:
    print(f"Error occurred: {err}")