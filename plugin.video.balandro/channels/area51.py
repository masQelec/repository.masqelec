# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://area51.porn/'


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

    itemlist.append(item.clone( title = 'Buscar vídeo ...', action = 'search', search_type = 'movie', text_color = 'orange' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'videos/' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'most-popular/' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'top-rated/' ))

    itemlist.append(item.clone( title = 'Long Play', action = 'list_all', url = host + 'search/?sort_by=duration&from_videos=1' ))

    itemlist.append(item.clone( title = 'Por canal', action = 'canales', url = host + 'channels/' ))
    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = host + 'category/' ))
    itemlist.append(item.clone( title = 'Por estrella', action = 'pornstars', url = host + 'models/' ))

    return itemlist


def canales(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    matches = re.compile('<a class="item_cat".*?href="(.*?)".*?title="(.*?)".*?src="(.*?)"').findall(data)

    for url, title, thumb in matches:
        title = title.capitalize()

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, thumbnail = thumb, text_color = 'violet' ))

    if itemlist:
        next_url = scrapertools.find_single_match(data, '<li class="page-current">.*?<a href="(.*?)"')

        if next_url:
            itemlist.append(item.clone( title = 'Siguientes ...', action = 'canales', url = next_url if next_url.startswith('http') else host[:-1] + next_url,
                                        text_color = 'coral' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    matches = re.compile('<a class="item_cat".*?href="(.*?)".*?title="(.*?)".*?src="(.*?)"').findall(data)

    for url, title, thumb in matches:
        title = title.capitalize()

        itemlist.append(item.clone (action='list_all', title = title, url = url, thumbnail = thumb, text_color = 'moccasin' ))

    return sorted(itemlist,key=lambda x: x.title)


def pornstars(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    bloque = scrapertools.find_single_match(data, '<div class="list-videos">(.*?)</div></div></div>')

    matches = re.compile('href="(.*?)".*?title="(.*?)".*?src="(.*?)"').findall(bloque)

    for url, title, thumb in matches:
        title = title.capitalize()
        itemlist.append(item.clone( action = 'list_all', title = title, url = url, thumbnail = thumb, text_color='orange' ))

    if itemlist:
        next_url = scrapertools.find_single_match(data, '<li class="page-current">.*?<a href="(.*?)"')

        if next_url:
            itemlist.append(item.clone( title = 'Siguientes ...', action = 'pornstars', url = next_url if next_url.startswith('http') else host[:-1] + next_url,
                                        text_color = 'coral' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    bloque = scrapertools.find_single_match(data, '<div class="list-videos">(.*?)<footer>')

    matches = re.compile('<div class="item.*?<a href="(.*?)".*?title="(.*?)".*?src="(.*?)".*?<span class="is-hd">(.*?)</span>').findall(bloque)

    for url, title, thumb, time in matches:
        if '</i>' in time: time = scrapertools.find_single_match(time, '</i>(.*?)$')

        titulo = "[COLOR tan]%s[/COLOR] %s" % (time, title)

        itemlist.append(item.clone (action='findvideos', title=titulo, url=url, thumbnail=thumb, contentType = 'movie', contentTitle = title, contentExtra='adults') )

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<li class="page-current">.*?<li class="page">.*?data-parameters=".*?">(.*?)</a>')

        if next_page:
            if 'search/?sort_by=duration' in item.url: next_page = host + 'search/?sort_by=duration&from_videos=1' + next_page + '/'
            elif 'search/' in item.url: next_page = host + 'search/' + item.tex + next_page + '/'
            elif 'most-popular/' in item.url: next_page = host + 'most-popular/' + next_page + '/'
            elif 'top-rated/' in item.url: next_page = host + 'top-rated/' + next_page + '/'
            elif 'channels/' in item.url: next_page = host + 'channels/' + next_page + '/'
            elif 'categories/' in item.url: next_page = host + 'categories/' + next_page + '/'
            elif 'models/' in item.url: next_page = host + 'models/' + next_page + '/'
            else: next_page = host + 'videos/' + next_page + '/'

            itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

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

    vid_id = scrapertools.find_single_match(data, "videoId: '(.*?)'")

    if not vid_id: return itemlist

    url = item.url + '/?video_id=' + vid_id

    data = do_downloadpage(url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    vid_url = scrapertools.find_single_match(data, "video_url: '(.*?)'")

    if not vid_url: return itemlist

    url = vid_url

    servidor = servertools.get_server_from_url(url)
    servidor = servertools.corregir_servidor(servidor)

    url = servertools.normalize_url(servidor, url)

    itemlist.append(Item( channel = item.channel, action='play', title='', url=url, server = servidor, language = 'Vo') )

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.tex = texto.replace(" ", "+") + '/'
        item.url = host + 'search/' + item.tex
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


