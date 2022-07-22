#!/usr/bin/env python3

import requests
import json
# import sponsorblock as sb # sponsorblock.py

# editable variables
ytInstance = "https://y.com.sb"
ytFrontend = "Invidious"

search = input("What do you want to search for? ")

vidId = ""
outFile = ""
if ytFrontend.lower() == "piped":
    # https://piped-docs.kavin.rocks/docks/api-documentation
    req = requests.get(ytInstance + "/suggestions", params={"query": search})
    # FIXME does only return names of videos
elif ytFrontend.lower() == "invidious":
    # https://docs.invidious.io/api
    req = requests.get(ytInstance + "/api/v1/search", params={
        "q": search,
        "duration": "short",
        "type": "video"})
    vids = json.loads(req.text)
    vidId = vids[0]['videoId']
    print(vidId)
    # FIXME
    outFile = requests.post(ytInstance + "/download", data={
                            "id": vids[0]['videoId'],
                            "title": search,
                            "download_widget": {
                                "itag": 140,
                                "ext": "mp4"
                                }
                            })
    print(outFile)
output2 = open(search + ".mp3", 'wb')
output2.write(outFile.text)
output2.close()

# FIXME implement sponsorblcok
# https://sponsorblockpy.readthedocs.io/en/latest
# toSkip = sb.Client().get_skip_segments("https://youtube.com/watch?v=" + vidId)
