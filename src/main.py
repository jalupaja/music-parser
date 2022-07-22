#!/usr/bin/env python3

import music_parser
import sqlite3

url = "https://open.spotify.com/playlist/1SHOvAkw16hJlydMcFmrc1"
music_parser.parse_urls(url, "json", "out.json")
# music_parser.parse_url(url, "sqlite", "db/db.db")
