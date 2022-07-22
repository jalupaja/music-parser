#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup

def add_playlist(text, vidDiv, vidLink):
    playlistName = text.find("div", "pure-u-2-3").find("h3").decode_contents()
    tracks = text.findAll("div", vidDiv)

    ret = []

    for track in tracks:
        title = track.find("p", "").decode_contents()
        artist = track.find("p", "channel-name").decode_contents()
        url = track.find("div", "icon-buttons").find("a")['href'].replace("https://www.youtube.com/watch?v=", "").split("&", 1)[0]
        ret.append([playlistName, title, artist, url, "yt", url])

    return ret


def add_vid(text, vidLink):
    title_h1 = text.find("h1")
    title = title_h1.decode_contents().split("\n", 2)[1].strip()
    url = title_h1.find("a")['href'].replace("/watch?v=", "").split("&", 1)[0]
    artists = text.find("div", vidLink).find("span").decode_contents().split("<", 1)[0].strip()
    print(artists)
    return [["", title, artists, url, "yt", url]]
