# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://www.superporn.com/es/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host ))

    itemlist.append(item.clone( title = 'Por canal', action = 'categorias', url = host + 'series/' ))
    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = host + 'categorias/', group = 'cats' ))
    itemlist.append(item.clone( title = 'Por estrella', action = 'categorias', url = host + 'pornostars/', group = 'stars' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    if item.group == 'cats': text_color = 'moccasin'
    elif item.group == 'stars': text_color = 'orange'
    else: text_color = 'violet'

    if item.group == 'cats':
        matches = re.compile('<div class="thumb-video thumb-categories(.*?)</div>', re.DOTALL).findall(data)
    elif item.group == 'stars':
        bloque = scrapertools.find_single_match(data, '<ul class="celebrities__list">(.*?)</ul>')
        matches = re.compile('<li class="celebrities__celebrity">(.*?)</li>', re.DOTALL).findall(bloque)
    else:
        bloque = scrapertools.find_single_match(data, '<div class="listado-videos listado-series"(.*?)<span class="clear">')
        matches = re.compile('<div class="thumb-serie(.*?)</div>', re.DOTALL).findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        url = host[:-1] + url

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        if not item.group == 'stars': thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        title = title.replace('&#039;', "'")

        itemlist.append(item.clone (action='list_all', title=title, url=url, thumbnail=thumb, text_color=text_color ))

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<li class="pagination_item".*?href="(.*?)"')

        if next_page:
            if not host in next_page: next_page = host[:-1] + next_page

            itemlist.append(item.clone (action='categorias', title='Siguientes ...', url=next_page, text_color = 'coral') )

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    matches = re.compile('<div class="thumb-video  ">(.*?)</span>            </a>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        title = title.replace('&#039;', "'")

        time = scrapertools.find_single_match(match, '<span class="duracion">(.*?)</span>').strip()

        titulo = "[COLOR tan]%s[/COLOR] %s" % (time, title)

        itemlist.append(item.clone (action='findvideos', title=titulo, url=url, thumbnail=thumb, contentType = 'movie', contentTitle = title, contentExtra='adults') )

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<li class="pagination_item".*?href="(.*?)"')

        if next_page:
            if not host in next_page: next_page = host[:-1] + next_page

            itemlist.append(item.clone (action='list_all', title='Siguientes ...', url=next_page, text_color = 'coral') )

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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    matches = scrapertools.find_multiple_matches(data, '<source src="(.*?)"')

    for url in matches:
        itemlist.append(Item( channel = item.channel, action='play', title='', url=url, server='directo', language = 'Vo') )

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url =  host + 'buscar?q=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
