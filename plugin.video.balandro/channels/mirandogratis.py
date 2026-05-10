# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://mirandogratis.com/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>PELICULAS POR GENERO<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)">(.*?)</a>')

    for url, title in matches:
        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = 'deepskyblue' ))

    if itemlist:
        itemlist.append(item.clone( action = 'list_all', title = 'Erótico', url = host + 'erotico', text_color = 'deepskyblue' ))

    return sorted(itemlist, key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        title = title.replace('&#8217;s', "'s").replace('&#038;', '&').replace('&#8211;', '').replace('&#8230;', '')

        title = title.replace('ver pelicula', '').replace(' online', '').strip()

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="mt-pagnav">' in data:
            next_page = scrapertools.find_single_match(data, "class='page-numbers current'>.*?href='(.*?)'.*?</a>")

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, 'id="op(.*?)</div>')

    ses = 0

    for match in matches:
        urls = scrapertools.find_multiple_matches(match, '<iframe.*?src="(.*?)"')

        if urls:
            for url in urls:
                ses += 1

                servidor = servertools.get_server_from_url(url)

                other = ''
                if servidor == 'various': other = servertools.corregir_other(url)
                elif servidor == 'zures': other = servertools.corregir_zures(url)

                if '<strong>Audio</strong>: Español Latino' in data: lang = 'Lat'
                elif '<strong>Audio</strong>: Castellano' in data: lang = 'Esp'
                elif '<strong>Audio</strong>: Subtitulado' in data: lang = 'Vose'
                else: lang = '?'

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = lang, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    servidor = item.server

    if servidor == 'directo':
        new_server = servertools.corregir_other(url).lower()
        if new_server.startswith("http"):
            if not config.get_setting('developer_mode', default=False): return itemlist
        servidor = new_server

    url = servertools.normalize_url(servidor, url)

    itemlist.append(item.clone(server = servidor, url = url))

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

