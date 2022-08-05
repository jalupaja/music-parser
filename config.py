#!/usr/bin/env python3

# https://api.invidious.io/

INVIDIOUS_MIRRORS = [
    "https://vid.puffyan.us",
    "https://inv.riverside.rocks",
    "https://invidious.osi.kr",
    "https://y.com.sb",
    "https://yt.artemislena.eu",
    "https://invidious.flokinet.to",
    "https://invidious.sethforprivacy.com",
    "https://invidious.tiekoetter.com",
    "https://inv.bp.projectsegfau.lt",
    "https://invidious.projectsegfau.lt",
    "https://inv.vern.cc",
    "https://invidious.nerdvpn.de",
    "https://invidious.slipfox.xyz",
    "https://youtube.076.ne.jp",
    "https://invidious.esmailelbob.xyz",
    "https://invidious.weblibre.org",
    "https://invidious.namazso.eu",
]

# CONSTANTS

## Spotify
spotify_track_div = "Row__Container-sc-brbqzp-0 jKreJT"
spotify_track_link = "EntityRowV2__Link-sc-ayafop-8 cGmPqp"
spotify_artists_span = "Type__StyledComponent-sc-1ell6iv-0 Mesto-sc-1e7huob-0 Row__Subtitle-sc-brbqzp-1 eJGiPK gmIWQx"

## Invidious
invidious_vid_div = "pure-u-1 pure-u-md-1-4"
invidious_vid_link = "channel-profile"
invidious_vid_date_div = "pure-u-1 pure-u-lg-3-5"
invidious_playlist_div = "pure-u-2-3"

## set the variable below to a file containing http procies in order to use them to download content
## There is a problem that if the proxy doesn't work, the error will only be shown in the console.
proxy_file = ""
