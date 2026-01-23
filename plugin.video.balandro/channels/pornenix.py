# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://pornenix.com/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('adults_password'):
            from modules import actions
            if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    itemlist.append(item.clone( title = 'Buscar vídeo ...', action = 'search', search_type = 'movie', search_video = 'adult', text_color = 'orange' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + "videos/" ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + "most-viewed/" ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + "top-rated/" ))

    itemlist.append(item.clone( title = 'Más candentes', action = 'list_all', url = host + "most-discussed/" ))

    itemlist.append(item.clone( title = 'Long play', action = 'list_all', url = host + "longest/" ))

    itemlist.append(item.clone( title = 'Por canal', action = 'canales', url = host + 'tags/' ))
    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = host + 'channels/' ))
    itemlist.append(item.clone( title = 'Por estrella', action = 'pornstars', url = host + 'models/' ))

    return itemlist


def canales(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'id="Pornenix-tags">(.*?)</section>')

    matches = re.compile('<a href="(.*?)".*?<span class="regular__link-label">(.*?)</span>').findall(bloque)

    for url, title in matches:
        title = title.capitalize()

        itemlist.append(item.clone( action = 'list_all', url = url, title = title, text_color = 'violet' ))

    return sorted(itemlist, key=lambda x: x.title)


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Categories </h1>(.*?)<div class="wrapper">')

    matches = re.compile('href="(.*?)".*?src="(.*?)".*?alt="(.*?)"').findall(bloque)

    for url, thumb, title in matches:
        itemlist.append(item.clone( action = 'list_all', url = url, title = title, thumbnail = thumb, text_color = 'moccasin' ))

    return sorted(itemlist, key=lambda x: x.title)


def pornstars(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<!-- alphabet :: column :: end -->(.*?)</section>')

    patron = '<a href="(.*?)".*?title="(.*?)".*?<img src="(.*?)"'

    matches = re.compile(patron).findall(bloque)

    for url, title, thumb in matches:
        itemlist.append(item.clone( action = 'list_all', url = url, title = title, thumbnail = thumb, text_color='orange' ))

    if itemlist:
        next_url = scrapertools.find_single_match(data, '<ul class="pagination-list">.*?<li class="pagination-list__li is-active">.*?href="([^"]+)')

        if next_url:
            ant_page = item.url
            if '/page' in ant_page:
                ant_page = ant_page.split("/page")[0]
                ant_page = ant_page + '/'

            next_url = ant_page + next_url

            itemlist.append(item.clone( action = 'pornstars', title = 'Siguientes ...', url = next_url, text_color = 'coral' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    patron = '<div class="item col">.*?<a href="(.*?)".*?title="(.*?)".*?<span class="item__stat -duration">.*?<span class="item__stat-label">(.*?)</span>.*?<img src="(.*?)"'

    matches = re.compile(patron).findall(data)

    for url, title, duration, thumb, in matches:
        title = title.replace('&quot;', '').replace('&#039;', "'").strip()

        titulo = "[COLOR tan]%s[/COLOR] %s" % (duration, title)

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if itemlist:
        next_url = scrapertools.find_single_match(data, '<ul class="pagination-list">.*?<li class="pagination-list__li is-active">.*?href="([^"]+)')

        if next_url:
            ant_page = item.url
            if '/page' in ant_page:
                ant_page = ant_page.split("/page")[0]
                ant_page = ant_page + '/'

            next_url = ant_page + next_url

            itemlist.append(item.clone( action = 'list_all', title = 'Siguientes ...', url = next_url, text_color = 'coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('adults_password'):
            from modules import actions
            if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<video id="thisPlayer">(.*?)</video>')
    if not bloque: bloque = scrapertools.find_single_match(data, '<div class="media col -video">(.*?)</div>')

    matches = re.compile('<source.*?src="(.*?)"').findall(bloque)
    if not matches: matches = re.compile('<iframe.*?src="(.*?)"').findall(bloque)

    for url in matches:
        if url:
            if url.endswith('.mp4'): vid = url
            else:
               datap = do_downloadpage(url)

               vid = scrapertools.find_single_match(datap, "'src', '(.*?)'")

            if vid:
                itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', url = vid, language = 'Vo' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url =  host + 'search/' + (texto.replace(" ", "+")) + '/'
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
