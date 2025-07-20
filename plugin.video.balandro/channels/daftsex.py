# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] >= 3:
    import urllib.parse as urllib
else:
    import urllib


import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools


host = 'https://daftsex.app/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host  + 'page/1/?filter=latest'))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'page/1/?filter=popular'))
    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host + 'page/1/?filter=most-viewed'))

    itemlist.append(item.clone( title = 'Long play', action = 'list_all', url = host  + 'page/1/?filter=longest' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'list_all', url = host + 'categories/page/1/', group = 'cats' ))

    itemlist.append(item.clone( title = 'Por estrella', action = 'list_all', group = 'stars', url = host + 'pornstars/page/1/' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<article(.*?)</article>').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        title = title.replace('&quot;', '').replace('[', '').replace(']', '').replace('&#8211;', '').replace('&#038;', '').strip()

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')
        if not thumb: thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        time = scrapertools.find_single_match(match, '<span class="duration">.*?</i>(.*?)</span>').strip()

        if time: titulo = "[COLOR tan]%s[/COLOR] %s" % (time, title)
        else: titulo = title

        url = url.replace('/-/', '/video/')

        if item.group:
            if item.group == 'cats': text_color = 'moccasin'
            else: text_color = 'orange'

            itemlist.append(item.clone( action = 'listas', url = url, title = titulo, thumbnail = thumb, text_color=text_color ))
        else:
            itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?<a class="current">.*?<a href="(.*?)".*?</div>')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', url= next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def listas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<article(.*?)</article>').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        title = title.replace('&quot;', '').replace('[', '').replace(']', '').replace('&#8211;', '').replace('&#038;', '').strip()

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')
        if not thumb: thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        time = scrapertools.find_single_match(match, '<span class="duration">.*?</i>(.*?)</span>').strip()

        if time: titulo = "[COLOR tan]%s[/COLOR] %s" % (time, title)
        else: titulo = title

        url = url.replace('/-/', '/video/')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?<a class="current">.*?<a href="(.*?)".*?</div>')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', url= next_page, action = 'listas', text_color = 'coral' ))

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

    matches = re.compile('<iframe src="(.*?)"').findall(data)

    for url in matches:
        url = url.split('php?q=')

        if url:
            url_decode = base64.b64decode(url[-1]).decode("utf8")
            url = urllib.unquote(url_decode)

            url = scrapertools.find_single_match(url, '<(?:iframe|source) src="([^"]+)"')

            if url:
                itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', url = url, language = 'VO' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url =  host + "spage/1/?s=%s" % (texto.replace(" ", "%20"))
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
