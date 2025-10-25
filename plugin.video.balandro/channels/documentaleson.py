# -*- coding: utf-8 -*-

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://documentaleson.com/'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar documental ...', action = 'search', search_type = 'documentary', text_color='cyan' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data

    bloque = scrapertools.find_single_match(data, '<ul class="sub-menu">(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)">(.*?)</a>')

    for url, title in matches:
        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color='cyan' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not title: title = scrapertools.find_single_match(match, 'rel="bookmark">(.*?)</a>')

        url = scrapertools.find_single_match(match, ' href="(.*?)"')

        title = title.replace('&#8211', '')

        thumb = scrapertools.find_single_match(match, ' data-src="(.*?)"')

        plot = scrapertools.find_single_match(match, ' <p>(.*?)</p>')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, infoLabels = {'year': '-', 'plot': plot},
                                    contentType='movie', contentTitle=title, contentExtra='documentary' ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="(.*?)"')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title='Siguientes ...', action='list_all', url = next_page, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    i = 0

    url = scrapertools.find_single_match(data, '<iframe.*?(.*?)data-src="(.*?)"')

    if url:
        i += 1

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor and servidor != 'directo':
            itemlist.append(Item( channel = item.channel, action = 'play', server=servidor, title = '', url = url, language = 'Esp' ))

    if not itemlist:
        if not i == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


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
