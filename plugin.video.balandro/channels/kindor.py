# -*- coding: utf-8 -*-

import re, base64

from platformcode import logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, jsontools, tmdb


host = 'https://kindor.io/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'peliculas/estrenos/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Novedades', action = 'list_all', url = host, search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más destacadas', action = 'list_all', url = host + 'destacadas/', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más recomendadas', action = 'list_all', url = host + 'recomendadas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Novedades', action = 'list_all', url = host, search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más destacadas', action = 'list_all', url = host + 'destacadas/', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más recomendadas', action = 'list_all', url = host + 'recomendadas/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'peliculas/')

    bloque = scrapertools.find_single_match(data, '>Géneros<(.*?)</ul>')

    patron = '<a href="(.*?)">(.*?)</a>'
    matches = re.compile(patron).findall(bloque)

    for url, title in matches:
        itemlist.append(item.clone( title = title.capitalize(), action = 'list_all', url = url ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h1(.*?)</section>')

    patron = '<div class="pogd">.*?href="(.*?)".*?data-src="(.*?)".*?<h3 class="pogd_tit"><a.*?>(.*?)</a>'
    matches = scrapertools.find_multiple_matches(bloque, patron)

    for url, thumb, title in matches:
        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if thumb.startswith('//'):
            thumb = 'https:' + thumb

        if '/serie/' in url:
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': '-'} ))

        else:
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_url = scrapertools.find_single_match(bloque, '<div class="pazza">.*?<a class="ffas">.*?<a href="(.*?)"')
        if next_url:
            itemlist.append(item.clone( title = '>> Página siguiente', url = next_url, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    fom, hash = scrapertools.find_single_match(data, "fom:(.*?),hash:'([^']+)'")

    json_data = jsontools.load(fom)

    i = 0

    for elem in json_data:
        i +=1
        if i > 1:
            break

    if i == 1:
        data_epi = json_data[elem]

        platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]Temporada' + str(i) + '[/COLOR]')
        item.data_epi = data_epi
        item.hash = hash
        item.page = 0
        item.contentType = 'season'
        item.contentSeason = i
        itemlist = episodios(item)
        return itemlist


    for elem in json_data:
        data_epi = json_data[elem]

        season = str(elem)
        if len(str(season)) == 1:
            season = '0' + season 

        titulo = 'Temporada ' + season

        itemlist.append(item.clone( action = 'episodios', title = titulo, data_epi = data_epi, hash = hash,
                                    contentType = 'season', contentSeason = season, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return sorted(itemlist, key=lambda x: x.title)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    perpage = 50

    matches = item.data_epi

    matches = matches.items()

    num_matches = len(matches)

    if num_matches > 100: 
        platformtools.dialog_notification('Kindor', '[COLOR blue]Cargando episodios[/COLOR]')

    season = str(item.contentSeason)

    for episode, info in matches[item.page * perpage:]:
        if season.startswith('0'):
            season = season.replace('0', '')

        ord_epis = str(episode)

        if len(str(ord_epis)) == 1:
            ord_epis = '0000' + ord_epis
        elif len(str(ord_epis)) == 2:
            ord_epis = '000' + ord_epis
        elif len(str(ord_epis)) == 3:
            ord_epis = '00' + ord_epis
        else:
            ord_epis = '0' + ord_epis

        titulo = '%sx%s - %s' % (season, episode, info["name"])

        json_data = info["all"]

        itemlist.append(item.clone( action='findvideos', url = item.url, title = titulo, json_data = json_data, hash = item.hash, orden = ord_epis,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = episode ))

        if len(itemlist) >= perpage:
            break

    if num_matches > ((item.page + 1) * perpage):
        itemlist.append(item.clone( title=">> Página siguiente", action="episodios", data_epi = item.data_epi, hash = item.hash, orden = '10000',
                                    page=item.page + 1, text_color='coral' ))

    itemlist = sorted(itemlist, key=lambda i: i.orden)


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'0': 'Lat', '1': 'Esp', '2': 'Vose'}

    if item.json_data:
        json_data = item.json_data
        hash = item.hash
    else:
        data = do_downloadpage(item.url)

        json_data = jsontools.load(scrapertools.find_single_match(data, "fom:(\{.*?})"))
        hash = scrapertools.find_single_match(data, "hash:'([^']+)'")

    for lang in json_data:
        url = "%s?h=%s" % (base64.b64decode(json_data[lang]), hash)

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, title = '', language = IDIOMAS.get(lang, lang) ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'buscar/' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

