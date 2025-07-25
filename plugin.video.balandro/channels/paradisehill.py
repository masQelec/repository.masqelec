# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://en.paradisehill.cc/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'all/?sort=created_at' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'popular/?filter=month&sort=by_likes' ))

    itemlist.append(item.clone( title = 'Por canal', action = 'categorias', url = host + 'studios/?sort=by_likes' ))
    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = host + 'categories/?sort=by_likes', group = 'cats' ))
    itemlist.append(item.clone( title = 'Por estrella', action = 'categorias', url = host + 'actors/?sort=by_likes', group = 'stars' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    if item.group == 'cats': text_color = 'moccasin'
    elif item.group == 'stars': text_color = 'orange'
    else: text_color = 'violet'

    matches = re.compile('<div class="item"(.*?)</a></div>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')

        url = host[:-1] + url

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        thumb = host[:-1] + thumb

        title = scrapertools.find_single_match(match, ' alt="(.*?)"')

        title = title.replace('&#039;', "'")

        itemlist.append(item.clone (action='list_all', title=title, url=url, thumbnail=thumb, text_color=text_color ))

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<li class="next"><a href="(.*?)"')

        if next_page:
            next_page = next_page.replace('&amp;', '&')

            if '&page=' in next_page:
                next_page = host[:-1] + next_page

                itemlist.append(item.clone (action='categorias', title='Siguientes ...', url=next_page, text_color = 'coral') )

    if item.group == 'cats':
        return sorted(itemlist,key=lambda x: x.title)

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    matches = re.compile('<div class="item list-film-item"(.*?)</div></div>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        url = host[:-1] + url

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        thumb = host[:-1] + thumb

        title = scrapertools.find_single_match(match, ' alt="(.*?)"')

        title = title.replace('&#039;', "'")

        itemlist.append(item.clone (action='findvideos', title=title, url=url, thumbnail=thumb, contentType = 'movie', contentTitle = title, contentExtra='adults') )

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<li class="next"><a href="(.*?)"')

        if next_page:
            next_page = next_page.replace('&amp;', '&')

            if '&page=' in next_page:
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

    part = 0

    pornstars = scrapertools.find_multiple_matches(data, '"/actor/\d+/">([^<]+)</a>')
    pornstar = ' & '.join(pornstars)
    pornstar = "[COLOR darkorange]%s[/COLOR]" % pornstar

    if len(pornstars) <= 2:
        lista = item.contentTitle.split()
        lista.insert (0, pornstar)
        item.contentTitle = ' '.join(lista)

    matches = scrapertools.find_multiple_matches(data, '{"src":"([^"]+)","type"')

    for url in matches:
        part +=1

        url = url.replace("\\", "")

        age = 'Parte ' + str(part)

        itemlist.append(Item( channel = item.channel, action='play', title='', url=url, server='directo', language = 'Vo', age = age) )

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url =  host + 'search/?pattern=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
