#!/usr/bin/env python3

import os
import sys
import subprocess
import asyncio
import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import random
from queue import Queue
from threading import Thread

import config
import spotify_parser
import invidious_parser


# The following classes are copied from: https://betterprogramming.pub/how-to-make-parallel-async-http-requests-in-python-d0bd74780b8a
class Worker(Thread):

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print(e)
            finally:
                self.tasks.task_done()


class ThreadPool:
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        self.tasks.join()


def print_error(text):
    print("\033[0;31mERROR: " + text + "\033[1;0m")


def print_success(text):
    print("\033[0;32mSUCCESS: " + text + "\033[1;0m")


__current_invidious_instance = ""
__current_invidious_counter = 0


def __get_invidious_instance(i=3):
    global __current_invidious_instance
    global __current_invidious_counter
    if __current_invidious_counter == 0:
        __current_invidious_counter = 10
        __current_invidious_instance = config.INVIDIOUS_MIRRORS[random.randint(0, len(config.INVIDIOUS_MIRRORS) - 1)]
        try:
            res = requests.get(__current_invidious_instance)
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
    else:
        __current_invidious_counter -= 1
    return __current_invidious_instance


def parse_urls(urls, outputFile, downloadPath):
    pool = ThreadPool(40)
    try:
        con = sqlite3.connect(outputFile)
        con.cursor().execute('''CREATE TABLE IF NOT EXISTS playlists
            (playlist_name TEXT, title TEXT, artists TEXT, url TEXT, url_type TEXT, yt_link TEXT)''')
    except:
        print_error("cannot parse " + outputFile)
        exit()
    results = {}

    arr = []
    for url in urls:
        arr.append([url, downloadPath, outputFile, pool])

    pool.map(__parse_single_url, arr)
    pool.wait_completion()
    con.close()


def __replace_with_invidious(url):
    return __get_invidious_instance() + "/" + url.replace("://", "").split("/")[1]


def __get_url_data(url):
    # check if link is to youtube and replace it with an invidious instance
    if "www.youtube.com" in url or "youtu.be" in url:
        url = __replace_with_invidious(url)

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
            arr = spotify_parser.add_playlist(soup, "Row__Container-sc-brbqzp-0 jKreJT", "EntityRowV2__Link-sc-ayafop-8 cGmPqp", "Type__StyledComponent-sc-1ell6iv-0 Mesto-sc-1e7huob-0 Row__Subtitle-sc-brbqzp-1 eJGiPK gmIWQx")
        elif site_about == "music.song":
            arr = spotify_parser.add_track(soup, url)
        # TODO add artists
        else:
            print_error("cannot parse " + site_name + ": " + site_about.replace("spotify.", ""))
            return None
        return arr
    elif site_name == "Piped":
        return __get_url_data(__replace_with_invidious(url))
    elif site_name == "Invidious":
        # TODO add channels
        if "playlist" in url:
            return invidious_parser.add_playlist(soup, "pure-u-1 pure-u-md-1-4", "channel-profile")
        else:
            return invidious_parser.add_vid(soup, "channel-profile")
    else:
        print_error("cannot parse " + site_name)
        return None


def add_manual_track(db_path, playlist_name, title, artists, url, url_type, yt_link):
    con = sqlite3.connect(db_path)
    db = con.cursor()
    __add_to_db([playlist_name, title, artists, url, url_type, yt_link])
    con.commit()
    con.close()

# TODO add functions: add_url_playlist, search..., copy_to_playlist

def __add_to_db(db_cursor, data):
    db_cursor.execute("INSERT INTO playlists (playlist_name, title, artists, url, url_type, yt_link) VALUES (\'" + "\',\'".join(x.replace("'", "’") for x in data) + "\')")


def __parse_single_url(arr):
    url = arr[0]
    downloadPath = arr[1]
    con = sqlite3.connect(arr[2])
    db = con.cursor()
    pool = arr[3]

    # if url is empty, and downloadPath is given -> download the whole database
    if len(url) == 0:
        data_arr = db.execute("SELECT * FROM playlists").fetchall()
        if downloadPath != "":
            down_arr = []
            for data in data_arr:
                down_arr.append([data[5], data[1], downloadPath + "/" + data[0]])
            pool.map(downloadVideo, down_arr)
    else:
        data_arr = __get_url_data(url)

        if data_arr is not None or len(data_arr) == 0:
            if downloadPath != "":
                down_arr = []
                for data in data_arr:
                    down_arr.append([data[5].replace("'", "’"), data[1].replace("'", "’"), downloadPath + "/" + data[0].replace("'", "’")])
                pool.map(downloadVideo, down_arr)

            fail_counter = 0
            for data in data_arr:
                if len(db.execute("SELECT title FROM playlists WHERE playlist_name='" + data[0].replace("'", "’") + "' AND title='" + data[1].replace("'", "’") + "'").fetchall()) < 1:
                    try:
                        if data[5] == "":
                            data[5] = invidious_parser.search_yt_id(__get_invidious_instance(), data[1].replace("'", "’") + " - " + data[2].replace("'", "’"))
                    except:
                        data[5] = ""
                    try:
                        __add_to_db(db, data)
                    except:
                        fail_counter += 1
                        pass
            con.commit()
            con.close()

            if fail_counter == len(data_arr):
                print_error(f"couldn't save {url}")
            elif fail_counter > 0:
                print_error(f"only saved {len(data_arr) - fail_counter} out of {len(data_arr)}")
            else:
                print_success(f"parsed {url}")

        else:
            print_error(f"couldn't parse {url}")


def downloadVideo(arr):
    youtube_id = arr[0]
    file_name = arr[1]
    file_path = arr[2]

    if (file_path == ""):
        folder = ""
    else:
        try:
            os.mkdir(file_path)
        except:
            pass
        folder = file_path + "/"

    # TODO proxy this
    if not os.path.exists(folder + file_name + ".mp3"):
        subprocess.call("yt-dlp https://www.youtube.com/watch?v=" + youtube_id + " -x --sponsorblock-remove all -o \"" + folder + file_name + ".%(ext)s\" --audio-format mp3", shell=True)


if __name__ == '__main__':
    i = 1
    urls = []
    outputFile = "db.db"
    downloadPath = ""
    while i < len(sys.argv):
        if sys.argv[i] == "-db":
            outputFile = sys.argv[i + 1]
            i += 1
        elif sys.argv[i] == "-d":
            downloadPath = sys.argv[i + 1]
            i += 1
        elif sys.argv[i][0] == "-":
            print_error("'" + sys.argv[i] + "' is not a valid argument")
            exit()
        else:
            urls.append(sys.argv[i])
        i += 1

    parse_urls(urls, outputFile, downloadPath)
