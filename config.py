#!/usr/bin/env python3

# Setting this to True will
#   - improve privacy due to contacting Invidious instead of YouTube Music
#   - increase the chance of getting bad YouTube link
use_invidious = False

# This is only useful if above is True
fix_yt_title_artist = True


# https://api.invidious.io/
INVIDIOUS_MIRRORS = [
    "https://invidious.fdn.fr",
    "https://vid.puffyan.us",
    "https://invidious.projectsegfau.lt",
    "https://invidious.nerdvpn.de",
    "https://invidious.lunar.icu",
    "https://invidious.io.lol",
    "https://inv.tux.pizza",
    "https://invidious.privacydev.net",
    "https://onion.tube",
    "https://yt.artemislena.eu",
    "https://vid.priv.au",
    "https://inv.zzls.xyz",
    "https://invidious.protokolla.fi",
    "https://yt.oelrichsgarcia.de",
    "https://iv.ggtyler.dev",
    "https://invidious.asir.dev",
    "https://iv.nboeck.de",
    "https://invidious.private.coffee",
    "https://iv.datura.network",
    "https://inv.in.projectsegfau.lt",
    "https://inv.us.projectsegfau.lt",
    "https://anontube.lvkaszus.pl",
    "https://invidious.perennialte.ch",
    "https://invidious.einfachzocken.eu",
    "https://invidious.slipfox.xyz",
    "https://invidious.no-logs.com",
    "https://yt.drgnz.club",
    "https://yt.cdaut.de",
    "https://inv.citw.lgbt",
    "https://iv.melmac.space",
]

# CONSTANTS

threads = 40

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

## yt-dlp options for easy access. The output name and possible proxies are inserted dynamically
yt_dl_options = {
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        },
        {
            "key": "SponsorBlock",
        },
    ],
}
