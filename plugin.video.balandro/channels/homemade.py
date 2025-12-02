# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools


host = 'https://homemade.xxx/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'latest-updates/' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'most-popular/' ))
    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'top-rated/1/' ))

    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host + 'most-popular/?sort_by=video_viewed_month' ))
    itemlist.append(item.clone( title = 'Long play', action = 'list_all', url = host + 'latest-updates/?sort_by=duration&from=1' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div id="custom_list_videos_common_videos_list"(.*?)</script>')
    if not bloque: bloque = scrapertools.find_single_match(data, 'id="custom_list_videos_videos_list_search_result_items">(.*?)</script>')

    patron = '<div class="item">.*?'
    patron += ' href="(.*?)".*?title="(.*?)".*?data-original="(.*?)".*?'
    patron += '<span class="label">(.*?)</span>.*?'
    patron += '</div></div></a>'

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for url, title, thumb, duration in matches:
        titulo = "[COLOR tan]%s[/COLOR] [COLOR darksalmon]%s[/COLOR] %s" % (duration, '', title)

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if '<title>Search Results' in data: return itemlist

    if itemlist:
        bloque = scrapertools.find_single_match(data, '<div class="pagination"(.*?)</ul>')

        next_page = scrapertools.find_single_match(bloque, '<li class="item-pagin active">.*?href="([^"]+)"')

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

    plot = ''

    bloque = scrapertools.find_single_match(data, '<div class="block-details">(.*?)</form>')

    pornstars = scrapertools.find_multiple_matches(bloque, '/models/[A-z0-9-]+/')

    for x, value in enumerate(pornstars):
        pornstars[x] = host[:-1] + value

        pornstar = ' & '.join(pornstars)

        pornstar = "[COLOR orange]%s[/COLOR]" % pornstar

        if len(pornstars) <= 3:
            lista = item.contentTitle.split()

            if "[COLOR darksalmon]" in item.title: lista.insert (5, pornstar)
            else: lista.insert (3, pornstar)
 
            item.contentTitle = ' '.join(lista)
        else:
            plot = pornstar


    itemlist.append(Item( channel = item.channel, action='play', title='', server = 'ktp', url = item.url, plot = plot, language = 'Vo') )

    return itemlist


def search(item, texto):
    logger.info()
    try:
        config.set_setting('search_last_video', texto)

        item.url = "%ssearch/?q=%s&sort_by=post_date&from=1" % (host, texto.replace(" ", "+"))
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
