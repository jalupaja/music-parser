#!/usr/bin/env python3

import sys
import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import random

import config
import spotify_parser
import invidious_parser


def print_error(text):
    print("\033[0;31mERROR: " + text + "\033[1;0m")


def print_success(text):
    print("\033[0;32mSUCCESS: " + text + "\033[1;0m")


def __get_invidious_instance(i=3):
    instance = config.INVIDIOUS_MIRRORS[random.randint(0, len(config.INVIDIOUS_MIRRORS) - 1)]
    try:
        res = requests.get(instance)
    except:
        if i <= 0:
            print_error("Please check your internet connection")
            exit()
        return __get_invidious_instance(i - 1)


    if res.status_code != 200:
        if i <= 0:
            print_error("couldn't connect to an Invidious instance.\nCheck your internet connection or update the config.py file")
            exit()
        return __get_invidious_instance(i - 1)
    return instance


def __setup_output(outputVar, outputFile):
    if outputVar == "sqlite" or outputVar == "sqlite3":
        con = sqlite3.connect(outputFile)
        con.cursor().execute('''CREATE TABLE IF NOT EXISTS playlists
            (playlist_name TEXT, title TEXT, artists TEXT, url TEXT, url_type TEXT, yt_link TEXT)''')
        con.close()
        return __array_to_sqlite
    elif outputVar == "json":
        with open(outputFile, 'w') as file:
            file.write("")
        return __array_to_json
    elif outputVar == "" and outputFile == "":
        return __array_to_output
    elif outputFile == "":
        print_error("Please specify an output file")
    else:
        print_error(outputVar + "is not a supported output type!")


def __array_to_sqlite(outputFile, arr):
    conn = sqlite3.connect(outputFile)
    db = conn.cursor()
    for data in arr:
        db.execute("INSERT OR IGNORE INTO playlists (playlist_name, title, artists, url, url_type, yt_link) VALUES (\'" + "\',\'".join(x.replace("'", "") for x in data) + "\')")
    conn.commit()
    conn.close()


def __array_to_json(outputFile, arr):

    if len(arr) == 0:
        return
    out = []
    tracks = []
    plName = arr[0][0]
    for data in arr:
        if data[0] == plName:
            tracks.append({"title": data[1], "artists": data[2], "url": data[3], "url_type": data[4], "yt_link": data[5]})
        else:
            out.append({"name": plName, "tracks": tracks})
            plName = data[0]
            tracks.clear()
            tracks.append({"title": data[1], "artists": data[2], "url": data[3], "url_type": data[4], "yt_link": data[5]})

    out.append({"name": plName, "tracks": tracks})
    tracks.append({"title": data[1], "artists": data[2], "url": data[3], "url_type": data[4], "yt_link": data[5]})

    with open(outputFile, 'w') as file:
        file.write(json.dumps(out))


def __array_to_output(useless, arr):
    print(arr)  # TODO should be improved


def __replace_with_invidious(url):
    return __get_invidious_instance() + "/" + url.replace("://", "").split("/")[1]


def __parse_single_url(url):
    # check if link is to youtube and replace it with an invidious instance
    if "www.youtube.com" in url or "youtu.be" in url:
        url = __replace_with_invidious(url)

    # parse from local file
    # with open("T/spotify_parser/playlist/movie_playlist.html") as fp:
    # with open("T/spotify_parser/album/album.html") as fp:
    # with open("T/spotify_parser/track/track.html") as fp:
    # with open("T/invidious/playlist.html") as fp:
    #     soup = BeautifulSoup(fp, features="html.parser")
    # url = "album/abc"

    # parse from url
    try:
        req = requests.get(url)
    except:
        return None

    # check if request was succesfull
    if not req.status_code == 200:
        return None

    soup = BeautifulSoup(req.text, "html.parser")

    # create database table if it doesn't exist
    site_name = soup.find("title").decode_contents().rsplit(None, 1)[-1]

    if site_name == "Spotify":
        site_about = soup.find("meta", property="og:type")["content"]
        if site_about == "music.playlist" or site_about == "music.album":
            return spotify_parser.add_playlist(soup, "Row__Container-sc-brbqzp-0 jKreJT", "EntityRowV2__Link-sc-ayafop-8 cGmPqp", "Type__StyledComponent-sc-1ell6iv-0 bhCKIk Mesto-sc-1e7huob-0 Row__Subtitle-sc-brbqzp-1 hTPACX gmIWQx")
        elif site_about == "music.song":
            return spotify_parser.add_track(soup, url)
        else:
            print_error("cannot parse " + site_name + ": " + site_about.replace("spotify.", ""))
            return None
    elif site_name == "Piped":
        return __parse_single_url(__replace_with_invidious(url))
    elif site_name == "Invidious":
        # TODO add channels
        if "playlist" in url:
            return invidious_parser.add_playlist(soup, "pure-u-1 pure-u-md-1-4", "channel-profile")
        else:
            return invidious_parser.add_vid(soup, "channel-profile")
    else:
        print_error("cannot parse " + site_name)
        return None


def parse_urls(url, outputVar="", outputFile=""):

    urls = url

    try:
        output_func = __setup_output(outputVar, outputFile)
    except:
        print_error("cannot access " + outputFile)

    if isinstance(url, str):
        urls = [url]

    data = []

    for uri in urls:
        add = __parse_single_url(uri)
        if add is not None:
            print_success("parsed " + uri)
            data += add
        else:
            print_error("couldn't parse " + uri)

    output_func(outputFile, data)


if __name__ == '__main__':
    i = 1
    urls = []
    outputVar = ""
    outputFile = ""
    while i < len(sys.argv):
        if sys.argv[i] == "-db":
            outputVar = "sqlite"
            outputFile = sys.argv[i + 1]
            i += 1
        elif sys.argv[i] == "-json":
            outputVar = "json"
            outputFile = sys.argv[i + 1]
            i += 1
        elif sys.argv[i][0] == "-":
            print_error("'" + sys.argv[i] + "' is not a valid argument")
            exit()
        else:
            urls.append(sys.argv[i])
        i += 1
    parse_urls(urls, outputVar, outputFile)
