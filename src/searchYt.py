#!/usr/bin/env python3

import requests
import json


def get_youtube_id(search, invInstance):
    req = requests.get(invInstance + "/api/v1/search", params={
        "q": search,
        "duration": "short",
        "type": "video"})
    vids = json.loads(req.text)
    vidId = vids[0]['videoId']
    return vidId


def download_id(id, file, invInstance):  # FIXME
    outFile = requests.post(invInstance + "/download", data={
                            "id": id,
                            "title": file,
                            "download_widget": {
                                "itag": 140,
                                "ext": "mp4"
                                }
                            })
    print(outFile)

    output2 = open(file, 'wb')
    output2.write(outFile.text)
    output2.close()
