# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.pelisplus24.xyz/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/fecha-de-lanzamiento/' in url:
        raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    return data


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'ver-pelicula-online/' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'peliculas-online/estrenos/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>GÉNEROS<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)">(.*?)</a>')

    for url, tit in matches:
        itemlist.append(item.clone( title = tit, url = url, action = 'list_all' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1938, -1):
        itemlist.append(item.clone( title = str(x), url = host + 'fecha-de-lanzamiento/' + str(x) + '/', action = 'list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h1>(.*?)<h2>')

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for article in matches:
        url = scrapertools.find_single_match(article, '<a href="(.*?)"')
        title = scrapertools.find_single_match(article, '<div class="title">.*?<h4>(.*?)</h4>').strip()

        if not url or not title: continue

        title = re.sub(r" \(.*?\)| \| .*", "", title)

        thumb = scrapertools.find_single_match(article, '<img src="(.*?)")')

        year = scrapertools.find_single_match(article, '</h3>.*?<span>(.*?)</span>')
        if year:
            title = title.replace('(' + year + ')', '').strip()
        else:
            year = '-'

        plot = scrapertools.htmlclean(scrapertools.find_single_match(article, '<div class="texto">(.*?)</div>'))

        langs = []
        if '/es.png' in article: langs.append('Esp')
        if '/mx.png' in article: langs.append('Lat')
        if '/en.png' in article: langs.append('Lat')
        if '/jp.png' in article: langs.append('Vose')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, languages=', '.join(langs),
                                    contentType = 'movie', contentTitle = title, infoLabels = {'year': year, 'plot': plot} ))


    tmdb.set_infoLabels(itemlist)

    if '<div class="pagination">' in data:
        patron = '<div class="pagination">.*?<span class="current">.*?'
        patron += "<a href='(.*?)'"

        next_page = scrapertools.find_single_match(data, patron)
        if next_page:
           itemlist.append(item.clone (url = next_page, page=0, title = '>> Página siguiente', action = 'list_all', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'mx': 'Lat', 'es': 'Esp', 'en': 'Vose', 'jp': 'Vose'}

    data = do_downloadpage(item.url)

    # embeds
    matches = scrapertools.find_multiple_matches(data, "<li id='player-option-(.*?)</li>")

    for match in matches:
        servidor = scrapertools.find_single_match(match, "<span class='title'>(.*?)</span>")

        if not servidor: continue

        if 'Trailer' in servidor: continue

        elif 'hqq' in servidor or 'waaw' in servidor or 'netu' in servidor: continue
        elif 'openload' in servidor: continue
        elif 'powvideo' in servidor: continue
        elif 'streamplay' in servidor: continue
        elif 'rapidvideo' in servidor: continue
        elif 'streamango' in servidor: continue
        elif 'verystream' in servidor: continue
        elif 'vidtodo' in servidor: continue

        lang = scrapertools.find_single_match(match, " src='.*?/flags/(.*?).png'")

        dpost = scrapertools.find_single_match(match, " data-post='(.*?)'")
        dnume = scrapertools.find_single_match(match, " data-nume='(.*?)'")

        if not dpost or not dnume: continue

        itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', dpost = dpost, dnume = dnume, other = servidor,
                              language = IDIOMAS.get(lang, lang) ))

    # enlaces
    matches = scrapertools.find_multiple_matches(data, "<tr id='link-'(.*?)</tr>")

    for match in matches:
        url = scrapertools.find_single_match(match, "<a href='(.*?)'")

        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url: continue
        elif 'openload' in url: continue
        elif 'powvideo' in url: continue
        elif 'streamplay' in url: continue
        elif 'rapidvideo' in url: continue
        elif 'streamango' in url: continue
        elif 'verystream' in url: continue
        elif 'vidtodo' in url: continue

        elif 'ul.to' in url: continue
        elif 'katfile.com' in url: continue
        elif 'rapidgator.net' in url: continue

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if url:
            qlty = scrapertools.find_single_match(match, "<strong class='quality'>(.*?)</strong>")

            lang = scrapertools.find_single_match(match, " src='.*?/flags/(.*?).png'")

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = IDIOMAS.get(lang, lang), quality = qlty ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if not url:
        post = {'action': 'doo_player_ajax', 'post': item.dpost, 'nume': item.dnume, 'type': 'movie'}
        headers = {"Referer": item.url}

        data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = post, headers = headers)

        url = scrapertools.find_single_match(data, "src='(.*?)'")

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        itemlist.append(item.clone( url = url, server = servidor ))

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
