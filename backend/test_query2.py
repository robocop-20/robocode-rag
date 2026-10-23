import urllib.request, json

data = json.dumps({"query": "test", "top_k": 5}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/query', data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        print('Response:', resp.read().decode())
except Exception as e:
    print('Error:', e)
