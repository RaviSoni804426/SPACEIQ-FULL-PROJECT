import urllib.request, json
req = urllib.request.Request(
    'http://localhost:8000/ai/chat',
    data=json.dumps({'message': 'show coworking spaces', 'history': []}).encode(),
    headers={'Content-Type': 'application/json'}
)
try:
    resp = urllib.request.urlopen(req)
    print("OK:", resp.read().decode())
except urllib.error.HTTPError as e:
    print("ERROR:", e.read().decode())
