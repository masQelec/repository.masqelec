import requests
import json
import base64
import sys

data = json.loads(open(sys.argv[1], 'rb').read())

if 'status' in data:
    data = json.loads(open(sys.argv[1], 'rb').read())
    body = base64.b64decode(data['data'])
    status = data['status']
    headers = data['headers']
else:
    print('Request: {}'.format(data['url']))
    resp = requests.request(data['method'], data['url'], data=base64.b64decode(data['data']), headers=data['headers'])
    body = resp.content
    status = resp.status_code
    headers = resp.headers

with open('body.txt', 'wb') as f:
    f.write(body)

print(status)
print(headers)
print(body.decode("utf-8", errors="replace"))