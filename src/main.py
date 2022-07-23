#!/usr/bin/env python3

import music_parser

url = ["https://open.spotify.com/playlist/1SHOvAkw16hJlydMcFmrc1",
       "https://piped.kavin.rocks/watch?v=0b7poHSUvUo"]
# music_parser.parse_urls(url, "json", "out.json")
music_parser.parse_urls(url, "sqlite", "db/db.db")
# music_parser.parse_urls(url)
