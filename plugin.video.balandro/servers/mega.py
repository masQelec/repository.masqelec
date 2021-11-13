# -*- coding: utf-8 -*-

from platformcode import config, logger, platformtools
from core import scrapertools
from lib.megaserver import Client


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)

    video_urls = []

    page_url = page_url.replace('/embed#!', '/embed#')
    page_url = page_url.replace('/embed/', '/embed#')
    page_url = page_url.replace('/file/', '/embed#')
    page_url = page_url.replace('/embed#', '/#!')

    try:
       c = Client(url=page_url, is_playing_fnc=platformtools.is_playing)
       files = c.get_files()
    except:
       color_exec = config.get_setting('notification_exec_color', default='cyan')
       el_srv = ('Sin respuesta en [B][COLOR %s]') % color_exec
       el_srv += ('Mega[/B][/COLOR]')
       platformtools.dialog_notification(config.__addon_name, el_srv, time=3000)
       return video_urls

    # Esta función no va
    if len(files) > 5:
        media_url = c.get_play_list()
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [mega]", media_url])
    else:
        for f in files:
            media_url = f["url"]
            video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [mega]", media_url])

    if len(video_urls) == 1:
        if '.zip ' in str(video_urls):
            return "El archivo está en formato comprimido"

    return video_urls