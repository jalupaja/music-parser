#!/usr/bin/env python3

import requests
import json
import re
import config
import urllib.parse
from ytmusicapi import YTMusic


def __search_yt(ytmusic, search):
    return ytmusic.search(search)


def search_yt_id(ytmusic, search, last=False):
    try:
        vids = __search_yt(ytmusic, search)
        vidId = vids[0]['videoId']
        year = vids[0]['year']
    except:
        try:
            vidId = vids[1]['videoId']
            year = vids[1]['year']
        except:
            try:
                vidId = vids[2]['videoId']
                year = vids[2]['year']
            except IndexError:
                if last:
                    return ""
                else:
                    return search_yt_id(ytmusic, search, True)
    return vidId, year
