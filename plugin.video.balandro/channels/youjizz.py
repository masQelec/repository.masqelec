# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools


host = 'https://www.youjizz.com/'


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

    itemlist.append(item.clone( title = 'Últimos', action = 'list_all', url = host + 'newest-clips/1.html', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Tendencias', action = 'list_all', url = host + 'trending/1.html' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'most-popular/1.html' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'top-rated/1.html' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>', '', data)

    bloque = scrapertools.find_single_match(data, '<ul class="footer-menu-links">(.*?)</ul>')

    matches = re.compile('<a href="(.*?)".*?>(.*?)</a>', re.DOTALL).findall(bloque)

    for url, title in matches:
        url = host[:-1] + url

        title = title.capitalize()

        itemlist.append(item.clone (action='list_all', title=title, url=url, text_color='moccasin' ))

    return sorted(itemlist, key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>', '', data)

    matches = re.compile('<div class="video-thumb".*?href="(.*?)".*?data-original="(.*?)".*?class="">(.*?)</a>.*?<span class="time">.*?</i>(.*?)</span>', re.DOTALL).findall(data)

    for url, thumb, title, duration, in matches:
        url = host[:-1] + url

        thumb = 'https:' + thumb

        duration = duration.replace('&nbsp;', '').strip()
		
        title = "[COLOR tan]%s[/COLOR] %s" % (duration, title)

        itemlist.append(item.clone (action='findvideos', title=title, url=url, thumbnail=thumb, contentType = 'movie', contentTitle = title, contentExtra='adults') )

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<a class="pagination-next".*?href="(.*?)"')

        if next_page:
            next_page = host[:-1] + next_page

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

    bloque = scrapertools.find_single_match(str(data), 'var dataEncodings =(.*?)var encodings =')

    matches = scrapertools.find_multiple_matches(bloque, '"quality":.*?"(.*?)".*?"filename":.*?"(.*?)"')

    for qlty, url in matches:
        url = url.replace('\\/', '/')

        url = 'https:' + url

        sort = 'B'
        if qlty == 'Auto': sort = 'A'

        itemlist.append(Item( channel = item.channel, action='play', title='', url=url,
                              server='directo', quality = qlty, language = 'Vo', sort = sort) )

    return sorted(itemlist, key=lambda it: it.sort)


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url =  host + 'search/recent_' + texto.replace(" ", "+") + '-1.html'
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
