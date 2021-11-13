# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://entrepeliculasyseries.io/'

perpage = 21


def do_downloadpage(url, raise_weberror=True):
    # ~ por si viene de enlaces guardados
    url = url.replace('/entrepeliculasyseries.com/', '/entrepeliculasyseries.io/')

    if '/peliculas-del' in url:
        raise_weberror = False

    data = httptools.downloadpage(url, raise_weberror=raise_weberror).data

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

    itemlist.append(item.clone( title = 'Netflix', action = 'list_all', url = host + 'peliculas-de-netflix/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimas recientes', action = 'list_all', url = host + 'series-recientes/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por productora', action = 'categorias', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    matches = scrapertools.find_multiple_matches(data, 'menu-item"><a href="([^"]+)">(.*?)</a>')

    for url, title in matches:
        if item.search_type == 'movie':
           if '/series-' in url: continue
        else:
           if '/peliculas-' in url: continue
           elif '/documentales' in url: continue

        itemlist.append(item.clone( action = 'list_all', title = title, url = url ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 2008, -1):
        url = host + 'peliculas-del-' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    productoras = [
        ('amazon-prime-video', 'Amazon Prime Video'),
        ('dc-comic', 'Dc Comic'),
        ('disney', 'Disney +'),
        ('hbo', 'HBO'),
        ('hulu', 'Hulu'),
        ('marvel', 'Marvel'),
        ('netflix', 'Netflix')
        ]

    for opc, tit in productoras:
        url = host + 'series-de-' + opc + '/'

        itemlist.append(item.clone( title = tit, action = 'list_all', url = url ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<figcaption(.*?)</figcaption')

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        title = scrapertools.find_single_match(match, '<h3>(.*?)</h3>').strip()
        if not title:
            title = scrapertools.find_single_match(match, '<h2>(.*?)</h2>').strip()

        thumb = scrapertools.find_single_match(match, 'src="([^"]+)"')

        url = scrapertools.find_single_match(match, 'href="([^"]+)"')
        if url == '#':
            url =  scrapertools.find_single_match(match, '<div class="title">.*?href="([^"]+)"')

        if not title or not url: continue

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if '/pelicula/' in url:
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': '-'} ))

        if '/serie/' in url:
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action ='temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        buscar_next = True
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1, action='list_all', text_color='coral' ))
                buscar_next = False

        if buscar_next:
            if "<span aria-current='page' class='current'>" in data:
                if '>Ultima »</a>' in data:
                    next_page_link = scrapertools.find_single_match(data, "<span aria-current='page' class='current'>.*?href=(.*?)>")

                    if next_page_link != '':
                        next_page_link =  next_page_link.replace('"', '')
                        itemlist.append(item.clone( title = '>> Página siguiente', action = 'list_all', url = next_page_link, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<option value="(.*?)"')

    for nro_season in matches:
        title = 'Temporada ' + nro_season

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = nro_season
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, contentType = 'season', contentSeason = nro_season, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return sorted(itemlist, key=lambda it: it.contentSeason)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    perpage = 50

    data = do_downloadpage(item.url)

    season = scrapertools.find_single_match(data, '<ul id="season-' + str(item.contentSeason) + '"(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(season, '<a href="(.*?)"')

    for url in matches[item.page * perpage:]:
        title = item.contentSerieName.replace('&#038;', '&')
        nro_epi = scrapertools.find_single_match(url, '-capitulo-(.*?)/')

        titulo = str(item.contentSeason) + 'x' + nro_epi + ' ' + title

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = nro_epi ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > ((item.page + 1) * perpage):
        itemlist.append(item.clone( title=">> Página siguiente", action="episodios", page=item.page + 1, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    options = scrapertools.find_multiple_matches(data, '<h3 class="select-idioma">(.*?)<div class="')

    ses = 0

    for option in options:
        ses += 1

        language = scrapertools.find_single_match(option, '</span>(.*?)<i').strip()

        if language == 'Subtitulado': language = 'Vose'
        elif language == 'Latino': language = 'Lat'
        elif language == 'Castellano': language = 'Esp'

        links = scrapertools.find_multiple_matches(option, '<li class="option".*?data-link="(.*?)".*?</span>(.*?)</li>')

        for url, servidor in links:
            servidor = servertools.corregir_servidor(servidor)

            if servidor:
               itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = language ))

    # Descargas
    if '>Enlaces de descarga<' in data:
        patron = '<tr><td>(.*?)</td><td>(.*?)</td><td><span>(.*?)</span>.*?href="(.*?)"'

        descargas = scrapertools.find_multiple_matches(data, patron)

        for servidor, language, qlty, url in descargas:
            ses += 1

            language = language.strip()

            if language == 'Subtitulado': language = 'Vose'
            elif language == 'Latino': language = 'Lat'
            elif language == 'Castellano': language = 'Esp'

            qlty = qlty.replace(' - ', ' ').strip()

            servidor = servertools.corregir_servidor(servidor)

            if servidor:
                if servidor == '1fitchier': continue

                if servidor:
                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = language,
                                          quality = qlty, other = 'D' ))

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

    if item.other == 'D':
       if '/go.php?' in url:
           data = do_downloadpage(url)
           url = scrapertools.find_single_match(data, '<a id="DownloadScript" href="([^"]+)"')

           if '//cuon.io/' in url or '/uii.io/' in url: return itemlist

           if url:
               servidor = servertools.get_server_from_url(url)
               servidor = servertools.corregir_servidor(servidor)

    elif url.startswith(host):
       if '/ir.php?' in url:
           data = do_downloadpage(url)

           url = scrapertools.find_single_match(data, 'window.location="([^"]+)"')

           if url:
               servidor = servertools.get_server_from_url(url)
               servidor = servertools.corregir_servidor(servidor)

       elif '/player.php?' in url:
           url = url.replace('.html', '')

           data = do_downloadpage(url)

           vid = scrapertools.find_single_match(data, 'name="h" value="(.*?)"')

           if vid:
               post = {'h': vid}
               ref = url.replace('.html', '')
               headers = {'Referer': ref}

               url = httptools.downloadpage(host + 'r.php', post = post, headers= headers, follow_redirects=False).headers.get('location', '')

               if url:
                   servidor = servertools.get_server_from_url(url)
                   servidor = servertools.corregir_servidor(servidor)

    if url:
        if not url.startswith('http'): url = 'https:' + url

        itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<div class="TPost C">(.*?)</li')

    for match in matches:
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')
        title = title.replace('ver ', '').replace('Online', '').strip()
        if not title:
            title = scrapertools.find_single_match(match, '<h2 class="Title">(.*?)</h2>')

        thumb = scrapertools.find_single_match(match, 'src="([^"]+)"')

        url = scrapertools.find_single_match(match, 'href="([^"]+)"')

        if not title or not url: continue

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if '/pelicula/' in url:
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': '-'} ))

        if '/serie/' in url:
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action ='temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

