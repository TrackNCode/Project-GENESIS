import requests, json, sys
url = 'http://127.0.0.1:8000/knowledge/ingest'
payload = [{
    "id": "test1",
    "text": "sample",
    "metadata": {"title": "T", "abstract": "A"}
}]
try:
    r = requests.post(url, json=payload, timeout=10)
    print('status', r.status_code)
    print('response', r.text)
except Exception as e:
    print('error', e)
    sys.exit(1)
