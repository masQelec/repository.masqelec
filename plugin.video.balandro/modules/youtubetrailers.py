# -*- coding: utf-8 -*-

import xbmc, re, time

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools


host = 'https://www.youtube.com'


addons = False

if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'): addons = True
elif xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'): addons = True


espera = config.get_setting('servers_waiting', default=6)


def mainlist(item):
    logger.info()
    itemlist = []

    if item.youtube_search:
        url, tit = youtube_search(item.youtube_search)

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
         return '', ''

    ret = platformtools.dialog_select('Tráilers y Vídeos en YouTube', opciones_youtube)

    if ret == -1: return '', ''

    match = elemento_youtube[ret]

    url = match[1]
    tit = match[0]

    return url, tit


def youtube_play(ini_page_url):
    logger.info()

    video_urls = []

    reintentar = False

    if ini_page_url.startswith(host + '/watch?v='):
        ids_ini_page_url = ini_page_url.replace(host + '/watch?v=', '')

        mvideo = re.match(r"^([0-9A-Za-z_-]{11})", ids_ini_page_url)

        if mvideo:
           idvideo = mvideo.group(1)

           new_page_url = 'https://inv.perditum.com/api/v1/videos/%s' % idvideo

           hdata = httptools.downloadpage(new_page_url).data

           if hdata:
               if 'This helps protect our community' in str(hdata):
                   if config.get_setting('developer_mode', default=False):
                       if config.get_setting('developer_team'):
                           platformtools.dialog_notification(config.__addon_name, '[B][COLOR yellow]Perditum Error Acceso[/B][/COLOR]')

                   if addons:
                       from servers import youtube

                       yt_new_url = 'https://www.youtube.com/watch?v=%s' % idvideo

                       yt_video = youtube.get_video_url(yt_new_url)

                       if yt_video:
                           if not 'No se pudo Reproducir el Vídeo' in str(yt_video):
                               yt_player = scrapertools.find_single_match(str(yt_video), "'mp4',.*?'(.*?)'")

                               if yt_player:
                                   video_urls.append(['mp4', yt_player])
                                   return video_urls

                   return video_urls

               elif 'try again later' in str(hdata):
                   if config.get_setting('servers_time', default=True):
                       platformtools.dialog_notification('Cargando [COLOR cyan][B]YouTube[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)

                       time.sleep(int(espera))

                   reintentar = True

                   hdata = httptools.downloadpage(new_page_url).data

               else:
                   if config.get_setting('developer_mode', default=False):
                       if config.get_setting('developer_team'):
                           platformtools.dialog_notification(config.__addon_name, '[B][COLOR yellow]Perditum Error Acceso[/B][/COLOR]')

                   reintentar = True

               hvideo = scrapertools.find_single_match(hdata, '"formatStreams":.*?"url":"(.*?)"')

               if hvideo:
                   video_urls.append(['mp4', hvideo])
                   return video_urls

               if reintentar:
                   if addons:
                       from servers import youtube

                       yt_new_url = 'https://www.youtube.com/watch?v=%s' % idvideo

                       yt_video = youtube.get_video_url(yt_new_url)

                       if yt_video:
                           if not 'No se pudo Reproducir el Vídeo' in str(yt_video):
                               yt_player = scrapertools.find_single_match(str(yt_video), "'mp4',.*?'(.*?)'")

                               if yt_player:
                                   video_urls.append(['mp4', yt_player])
                                   return video_urls

                   if platformtools.dialog_yesno(config.__addon_name , '[B][COLOR yellow]YouTube Saturado.[/B][/COLOR]', '¿ [B][COLOR cyan]Desea Re-Intentar el Acceso[/B][/COLOR] ?'):
                       time.sleep(int(espera))

                       hdata = httptools.downloadpage(new_page_url).data

                       if hdata:
                           if 'This helps protect our community' in str(hdata):
                               if config.get_setting('developer_mode', default=False):
                                   if config.get_setting('developer_team'):
                                       platformtools.dialog_notification(config.__addon_name, '[B][COLOR yellow]Perditum Error Acceso[/B][/COLOR]')

                           elif 'try again later' in str(hdata):
                              if config.get_setting('servers_time', default=True):
                                  platformtools.dialog_notification('Cargando [COLOR cyan][B]YouTube[/B][/COLOR]', 'Espera requerida de %s segundos' % espera)

                                  time.sleep(int(espera))

                                  hdata = httptools.downloadpage(new_page_url).data

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

    titulo = '[COLOR paleturquoise][B]' + item.tit.strip() + '  [COLOR fuchsia][B]YouTube[/B][/COLOR]'

    itemlist.append(Item( channel = 'actions', action = 'player_youtube', server='directo', title=titulo, url=item.url, thumbnail=config.get_thumb('youtube') ))

    return itemlist


def search(item, texto):
    logger.info()

    try:
        config.set_setting('search_last_youtube', texto)

        if texto:
            item.action = 'search'

            item.search_type = 'all'

            item.youtube_search = texto.replace(" ", "+")

            url, tit = youtube_search(item.youtube_search)

            if url:
                video_urls = youtube_play(url)

                if video_urls:
                    item.channel = 'youtubetrailers'

                    item.url = video_urls[0][1]
                    item.tit = tit

                    return findvideos(item)

        return
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
