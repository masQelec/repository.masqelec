# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://retroflix.org/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    if not data:
        if not '/?s=' in url:
            if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('RetroFlix', '[COLOR cyan]Re-Intentando acceso[/COLOR]')

            timeout = config.get_setting('channels_repeat', default=30)

            data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    if config.get_setting('mnu_documentales', default=True):
        itemlist.append(item.clone( title='Documentales', action = 'mainlist_documentales', text_color='cyan' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title='Animes', action = 'mainlist_animes', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Listas', action = 'mainlist_listas', text_color = 'moccasin' ))

    return itemlist


def mainlist_listas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Charles chaplin', action = 'list_all', url = 'https://retroflix.org/cast/charles-chaplin/', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Historia cinema', action = 'list_all', url = 'https://retroflix.org/browse/cinema-history/', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'John wayne', action = 'list_all', url = 'https://retroflix.org/cast/john-wayne/', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Looney tunes', action = 'list_all', url = 'https://retroflix.org/cartoon-series/looney-tunes/', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Popeye', action = 'list_all', url = 'https://retroflix.org/cartoon-character/popeye-the-sailor/', text_color = 'moccasin' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'browse/movies/?sort=newest', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'browse/movies/?sort=popular', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más antiguas', action = 'list_all', url = host + 'browse/movies/?sort=oldest', search_type = 'movie' ))

    itemlist.append(item.clone( action='', title = '[B]Listas:[/B]', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = ' - Charles chaplin', action = 'list_all', url = 'https://retroflix.org/cast/charles-chaplin/' ))

    itemlist.append(item.clone( title = ' - Historia cinema', action = 'list_all', url = 'https://retroflix.org/browse/cinema-history/' ))

    itemlist.append(item.clone( title = ' - John wayne', action = 'list_all', url = 'https://retroflix.org/cast/john-wayne/' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( action='', title = '[B]Episodios Cartoons:[/B]', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host + 'browse/cartoons/?sort=newest', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = ' - Más populares', action = 'list_all', url = host + 'browse/cartoons/?sort=popular', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = ' - Más antiguos', action = 'list_all', url = host + 'browse/cartoons/?sort=oldest', search_type = 'tvshow' ))

    itemlist.append(item.clone( action='', title = '[B]Listas:[/B]', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = ' - Looney tunes', action = 'list_all', url = 'https://retroflix.org/cartoon-series/looney-tunes/' ))

    itemlist.append(item.clone( title = ' - Popeye', action = 'list_all', url = 'https://retroflix.org/cartoon-character/popeye-the-sailor/' ))

    return itemlist


def mainlist_documentales(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar documental ...', action = 'search', tipo = 'Animes', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'genre/documentary/?sort=newest', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'genre/documentary/?sort=popular', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más antiguos', action = 'list_all', url = host + 'genre/documentary/?sort=oldest', search_type = 'movie' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', tipo = 'Animes', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( action='', title = '[B]Episodios Animes:[/B]', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = ' - Catálogo', action = 'list_all', url = host + 'browse/anime/?sort=newest', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = ' - Más populares', action = 'list_all', url = host + 'browse/anime/?sort=popular', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = ' - Más antiguos', action = 'list_all', url = host + 'browse/anime/?sort=oldest', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    opciones = [
       ('action', 'Acción'),
       ('animation', 'Animación'),
       ('aventure', 'Aventura'),
       ('comedy', 'Comedia'),
       ('crime', 'Crimen'),
       ('drama', 'Drama'),
       ('family', 'Familia'),
       ('fantasy', 'Fantasía'),
       ('war', 'Guerra'),
       ('history', 'Historia'),
       ('mistery', 'Misterio'),
       ('music', 'Música'),
       ('romance', 'Romance'),
       ('horror', 'Terror'),
       ('thriller', 'Thriller'),
       ('western', 'Western')
    ]

    for opc, tit in opciones:
        itemlist.append(item.clone( title=tit, url= host + 'genre/' + opc + '/', action = 'list_all', text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<a href=".*?">(.*?)</a>')

        if not url or not title: continue

        title = title.replace('&#8217;s', "'s").replace('n&#8217;', "'n").replace('&#8211;', '').replace('&#8230;', '').replace('&#8216;', '').replace('&#8217;', '').replace('&#8212;', '').strip()

        thumb = scrapertools.find_single_match(match, 'background-url:url(.*?)"')

        thumb = thumb.replace('(', '').replace(')', '').strip()

        tipo = 'movie' if item.search_type == 'movie' else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie' or item.search_type == "all":
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': '-'} ))

        if tipo == 'tvshow' or item.search_type == "all":
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<a class="next page-numbers".*?href="(.*?)".*?</nav>')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    match = scrapertools.find_single_match(data, '<video controls=".*?src="(.*?)"')

    ses = 0

    if match:
        url = match

        url = url.replace('%20', ' ').replace('%28', '(').replace('%29', ')')

        servidor = servertools.get_server_from_url(url)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): url = ''
        else:
            if not config.get_setting('developer_mode', default=False): url = ''

        if url:
            ses += 1

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = 'Vo' ))

    if not itemlist:
        if not ses == 0:
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

