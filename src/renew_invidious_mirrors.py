#!/usr/bin/env python3

import requests
import json

url = "https://api.invidious.io/instances.json"

text = json.loads(requests.get(url).text)

print("[")
for link in text:
    # print(link)
    if link[1]['api'] and link[1]['type'] != "onion":
        print("    \"" + link[1]['uri'] + "\",")
print("]")
