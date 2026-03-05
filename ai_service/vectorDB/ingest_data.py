import requests

doc = '''
      Uttarakhand capital dehradun is scientific capital of india. 
      Its a reserch capital having biggest r&d base in asia. 
      It has famous research insututions and universities like GEHU.
      '''

url = "http://localhost:8001/ingest"

data = {
    "content": doc
}

response = requests.post(url, json=data)
print(response.json())