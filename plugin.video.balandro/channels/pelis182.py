# -*- coding: utf-8 -*-

import re

from platformcode import logger
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


# ~ Las series no se tratan pq solo hay 17

host = 'https://www.pelis182.com/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>Menu<(.*?)</form>')

    matches = re.compile('<a href="(.*?)">(.*?)</a>').findall(bloque)

    for url, title in matches:
        if title == 'Series': continue

        itemlist.append(item.clone( title = title.capitalize(), action = 'list_all', url = url, text_color = 'deepskyblue' ))

    return sorted(itemlist,key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="([^"]+)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        if '-temporada-' in url: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        year = scrapertools.find_single_match(title, '(\d{4})')
        if not year: year = '-'
        else: title = title.replace('(' + year + ')', '').strip()

        itemlist.append(item.clone( action = 'findvideos', url=url, title=title, thumbnail=thumb, languages='Lat',
                                    contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
         if '<nav class="navigation pagination"' in data:
             next_page = scrapertools.find_single_match(str(data), '<nav class="navigation pagination".*?class="page-numbers current">.*?href="(.*?)".*?</nav>')

             if next_page:
                 if '/page/' in next_page:
                     itemlist.append(item.clone( title = 'Siguientes ...', action='list_all', url = next_page, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<iframe.*?src="(.*?)".*?</iframe>')

    for url in matches:
        itemlist.append(Item(channel = item.channel, action = 'play', server='', title = '', url=url,
                             language=item.languages, quality=item.qualities, other='M3u8'))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    new_url = get_video_url(url)

    if new_url:
        if new_url == 'error': return '[COLOR red]Archivo Inexistente ó eliminado[/COLOR]'

        itemlist = new_url

    return itemlist


def get_video_url(url):
    logger.info("(url='%s')" % url)
    video_urls = []

    resp = httptools.downloadpage(url, headers = {'Referer': host})

    data = resp.data

    if not resp.sucess: return "error"

    if "NOT FOUND!" in data: return "error" 

    try:
        headers = '|Referer=https://lauchacohete.top/'

        video = scrapertools.find_single_match(data, 'sources:\s+\[\{"file":"([^"]+)')

        if video.endswith(".m3u8"):
            subtitle = scrapertools.find_single_match(data, 'tracks:\s+\[\{"file":"([^"]+)')

            video += headers

            if subtitle.endswith(".srt"):
                subtitle += headers

                video_urls.append(['m3u8', video, 0, subtitle])
            else:
                video_urls.append(['m3u8', video])
    except:
        logger.error("Pelis182 get_video_url")

    return video_urls


def search(item, texto):
    logger.info()
    try:
       item.url = host + '?s=' + texto.replace(" ", "+")
       return list_all(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []

