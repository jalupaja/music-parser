#!/usr/bin/env python3

class song:
    def __init__(self, title, playlist_name="", artists="", genre="", url="", url_type="", yt_link=""):
        self.title = title
        self.playlist_name = playlist_name
        self.artists = artists
        self.genre = genre
        self.url = url
        self.url_type = url_type
        self.yt_link = yt_link

    def from_select(self, data):
        self.playlist_name = data[0]
        self.title = data[1]
        self.artists = data[2]
        self.genre = data[3]
        self.url = data[4]
        self.url_type = data[5]
        self.yt_link = data[6]
        self.year = data[7]
        return self

    def collums(self):
        return "playlist_name, title, artists, genre, url, url_type, yt_link, year"

    def values(self):
        return f"'{self.playlist_name.replace(''', '’')}', '{self.title.replace(''', '’')}', '{self.artists.replace(''', '’')}', '{self.genre.replace(''', '’')}', '{self.url.replace(''', '’')}', '{self.url_type.replace(''', '’')}', '{self.yt_link.replace(''', '’')}', '{self.year.replace(''', '’')}'"


sql_table = "playlist_name TEXT, title TEXT NOT NULL, artists TEXT, genre TEXT, url TEXT, url_type TEXT, yt_link TEXT, year INTEGER"
