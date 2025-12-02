# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools


host = 'https://www.youtube.com'


def mainlist(item):
    logger.info()
    itemlist = []

    if item.youtube_search:
        url = youtube_search(item.youtube_search)

        if url:
            video_urls = youtube_play(url)

            if video_urls: itemlist = video_urls

    return itemlist


def youtube_search(nombre):
    logger.info()

    opciones_youtube = []
    elemento_youtube = []

    i = 0

    titulo = nombre

    titulo = titulo.replace(" ", "+")

    data = httptools.downloadpage( host + '/results?sp=EgIQAQ%253D%253D&q=' + titulo).data

    patron  = 'thumbnails":\[\{"url":"(https://i.ytimg.com/vi[^"]+).*?'
    patron += 'text":"([^"]+).*?'
    patron += 'simpleText":"[^"]+.*?simpleText":"([^"]+).*?'
    patron += 'url":"([^"]+)'

    matches = scrapertools.find_multiple_matches(data, patron)

    for thumb, title, time, url in matches:
        if not '/watch?v=' in url: continue

        if 'visualizaciones' in time: continue

        if not time: continue

        title = title.replace('\\', '').replace('📢', '').replace('😱', '').replace('🔬', '').replace('🔥', '').replace('✨', '').replace('👁', '').replace('🔎', '').replace('🎬', '').replace('✋⛔🙇🏻❤️‍🩹', '')

        title = title.replace('🇰🇷', '').replace('u0026', '').replace('[', '').replace(']', '').replace('¡', '').replace('!', '').replace('#', '').replace('|', '').replace('.mov', '').strip()

        if not title: continue

        if len(title) == 1: continue

        title = title.capitalize()

        i +=1

        url = host + url

        opciones_youtube.append(platformtools.listitem_to_select('[COLOR tan]' + str(time) + '[/COLOR]' + '  [COLOR yellow]' + title + '[/COLOR]', url))

        elemento_youtube.append([title, url])

    if i == 0:
         platformtools.dialog_notification(config.__addon_name, '[B][COLOR red]Sin Tráilers y/ó Vídeos en YouTube[/B][/COLOR]')
         return ''

    ret = platformtools.dialog_select('Tráilers y Vídeos en YouTube', opciones_youtube)

    if ret == -1: return ''

    match = elemento_youtube[ret]

    url = match[1]

    return url


def youtube_play(ini_page_url):
    logger.info()

    video_urls = []

    if ini_page_url.startswith(host + '/watch?v='):
        ini_page_url = ini_page_url.replace(host + '/watch?v=', '')

        mvideo = re.match(r"^([0-9A-Za-z_-]{11})", ini_page_url)

        if mvideo:
           idvideo = mvideo.group(1)

           new_page_url = "https://inv.perditum.com/api/v1/videos/%s" % idvideo

           hdata = httptools.downloadpage(new_page_url).data

           if hdata:
               hvideo = scrapertools.find_single_match(hdata, '"formatStreams":.*?"url":"(.*?)"')

               if hvideo:
                   video_urls.append(['mp4', hvideo])
                   return video_urls

    if not video_urls:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR cyan]No se localizaron Tráilers y/ó Vídeos en YouTube[/B][/COLOR]')

    return video_urls


def findvideos(item):
    logger.info()
    itemlist = []

    itemlist.append(Item( channel = 'actions', action = 'player_youtube', server = 'directo', title = '[COLOR fuchsia][B]Play Youtube[/B][/COLOR]', url = item.url, thumbnail=config.get_thumb('youtube') ))
 
    return itemlist


def search(item, texto):
    logger.info()

    try:
        config.set_setting('search_last_youtube', texto)

        if texto:
            item.action = 'search'

            item.search_type = 'all'

            item.youtube_search = texto.replace(" ", "+")

            url = youtube_search(item.youtube_search)

            if url:
                video_urls = youtube_play(url)

                if video_urls:
                    item.channel = 'youtubetrailers'

                    item.url = video_urls[0][1]

                    return findvideos(item)

        return
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
