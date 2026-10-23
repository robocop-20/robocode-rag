import urllib.request
import json

def test_query():
    payload = {"query": "Where is the PID calculation?", "top_k": 3}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/query',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            res = json.loads(body)
            print("Status: 200 OK")
            print(f"Query: {res['query']}")
            print(f"Citations count: {len(res['citations'])}")
            print(f"Latency: {res['latency_ms']} ms")
            print("\nFirst citation:")
            print(f"File: {res['citations'][0]['file_path']}:{res['citations'][0]['start_line']}-{res['citations'][0]['end_line']}")
    except Exception as e:
        print('Error:', e)

if __name__ == "__main__":
    test_query()
