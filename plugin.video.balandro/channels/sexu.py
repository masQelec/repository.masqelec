# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools


host = 'https://sexu.com/'


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

    itemlist.append(item.clone( title = 'Buscar vídeo ...', action = 'search', search_type = 'movie', search_video = 'adult', text_color='orange' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host  + 'all' ))

    itemlist.append(item.clone( title = 'Últimos', action = 'list_all', url = host + 'new', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'trending' ))
    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host + 'engaging' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = host + 'categories?sort=name' ))

    itemlist.append(item.clone( title = 'Por estrella', action = 'categorias', url = host + 'pornstars', group = 'stars' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    text_color = 'moccasin'
    if item.group == 'stars': text_color = 'orange'

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<a class="item" href="([^"]+)" title="([^"]+)".*?'
    patron += '(?:data-src|src)="([^"]+)"'

    matches = re.compile(patron,re.DOTALL).findall(data)

    for url, title, thumb in matches:
        if not thumb.startswith("https"): thumb = "http:%s" % thumb

        url = host[:-1] + url + '?st=upload'

        itemlist.append(item.clone( action = 'list_all', url = url, title = title, thumbnail = thumb, text_color=text_color ))


    if itemlist:
        next_page = scrapertools.find_single_match(data, '<a class="pagination__arrow pagination__arrow--next" href="([^"]+)">')

        if next_page:
            next_page =  host[:-1] + next_page

            itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'categorias', text_color = 'coral' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    patron = '<a class="item__main" href="/([^"]+)/" title="([^"]+)".*?'
    patron += '(?:data-src|src)="([^"]+)".*?'
    patron += '<div class="item__counter">([^<]+)<'

    matches = re.compile(patron,re.DOTALL).findall(data)

    for url, title, thumb, time in matches:
        title = title.replace('&#039;s', "'s").strip()

        titulo = "[COLOR tan]%s[/COLOR] %s" % (time, title)

        if not thumb.startswith("https"): thumb = "http:%s" % thumb

        url = 'videoId=' + url

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<a class="pagination__arrow pagination__arrow--next" href="([^"]+)">')

        if next_page:
            next_page =  host[:-1] + next_page

            itemlist.append(item.clone( title = 'Siguientes ...', url= next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('adults_password'):
            from modules import actions
            if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    url = host + 'api/video-info'

    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

    data = do_downloadpage(url, post=item.url, headers=headers)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    jdata = jsontools.load(data)

    for Video in jdata['sources']:
        url = Video["src"]
        qlty = Video["quality"]
        if not url.startswith("http"): url = 'https:' + url 
 
        itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', url = url, quality = qlty, language = 'VO' ))

    return itemlist


def _lasts(item):
    logger.info()

    item.url = host + "new"

    return list_all(item)


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url = "%ssearch?q=%s&st=upload" % (host, texto.replace(" ", "+"))
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
