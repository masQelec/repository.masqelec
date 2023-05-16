# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True

if PY3:
    import urllib.parse as urlparse
else:
    import urlparse


import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, jsontools


host = 'https://titsbox.com/'


url_api = host + '?ajax=1&type='


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data
    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    descartar_xxx = config.get_setting('descartar_xxx', default=False)

    if descartar_xxx: return itemlist

    if config.get_setting('adults_password'):
        from modules import actions
        if actions.adults_password(item) == False:
            return itemlist

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = url_api + 'most-recent&page=1' ))

    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = url_api + 'long&page=1' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = url_api + 'top-rated&page=1' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = host ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    data = scrapertools.find_single_match(data, '<ul class="sidebar-nav">(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    matches = re.compile('<a class="category-item" href="([^"]+)">([^"]+)</a>', re.DOTALL).findall(data)

    for url, title in matches:
        url = urlparse.urljoin(item.url, url)
        url = url + '?ajax=1&type=most-recent&page=1'

        itemlist.append(item.clone (action='list_all', title=title, url=url, contentType = 'movie', text_color = 'orange' ))

    return sorted(itemlist,key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    jdata = jsontools.load(data)

    for video in jdata["data"]:
        domain = ''

        duration = video["duration"]

        title = video["videoTitle"]

        titulo = "[COLOR tan]%s[/COLOR] %s" % (duration, title)

        src = video["src"]
        thumb = src.get('domain', domain) + src.get('pathMedium', domain)+"1.jpg"

        url = video["urls_CDN"]
        url = url.get('480', domain)

        url = url.replace("/\n/", "/")

        itemlist.append(item.clone (action='findvideos', title=titulo, url=url, thumbnail=thumb, contentType = 'movie', contentTitle = title, contentExtra='adults') )

    if itemlist:
        actual = int(scrapertools.find_single_match(item.url, '&page=([0-9]+)'))

        if jdata["pagesLeft"] - 1 > actual:
            next_page = item.url.replace("&page=" + str(actual), "&page=" + str(actual + 1))

            itemlist.append(item.clone (action='list_all', title='Siguientes ...', url=next_page, text_color = 'coral') )

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    itemlist.append(Item( channel = item.channel, action='play', title='', url=item.url, server = 'directo', language = 'Vo') )

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url =  host + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
