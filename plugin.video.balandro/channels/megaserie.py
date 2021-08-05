# -*- coding: utf-8 -*-

import re

from platformcode import logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://megaxserie.me/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/release/' in url:
        raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone ( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone ( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone ( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone ( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone ( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone ( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone ( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone ( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone ( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone ( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone ( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    opciones = [
        ('accion', 'Acción'), 
        ('action-adventure', 'Action & Adventure'),
        ('animacion', 'Animación'), 
        ('aventura', 'Aventura'),
        ('belica', 'Belica'),
        ('ciencia-ficcion', 'Ciencia ficción'),
        ('comedia', 'Comedia'), 
        ('crimen', 'Crimen'),
        ('documental', 'Documental'), 
        ('drama', 'Drama'),
        ('familia', 'Familiar'), 
        ('fantasia', 'Fantasía'),
        ('historia', 'Historia'), 
        ('kids', 'Infantil'),
        ('misterio', 'Misterio'),
        ('musica', 'Música'),
        ('pelicula-de-tv' ,'Película de TV'),
        ('reality', 'Reality'),
        ('romance', 'Romance'),
        ('sci-fi-fantasy' ,'Sci-Fi & Fantasy'),
        ('suspense', 'Suspense'),
        ('terror', 'Terror'),
        ('western', 'Western')
        ]

    if item.search_type == 'movie': 
        opciones.remove(('action-adventure','Action & Adventure'))
        opciones.remove(('kids','Infantil'))
        opciones.remove(('reality','Reality'))
        opciones.remove(('sci-fi-fantasy','Sci-Fi & Fantasy'))

    elif item.search_type == 'tvshow': 
        opciones.remove(('suspense','Suspense'))

    for opc, tit in opciones:
        url = host + opc
        if item.search_type == 'movie': 
            url += '/?type=movies'
        else:
            url += '/?type=series'

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    if item.search_type == 'movie': 
        top_year = 1955
    else:
        top_year = 1998

    for x in range(current_year, top_year, -1):
        itemlist.append(item.clone( title = str(x), url = host + 'release/' + str(x) + '/', action = 'list_all' ))

    return itemlist


def list_all(item): 
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque =  scrapertools.find_single_match(data, '</h1>(.*?)>Por Año<')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        title = scrapertools.find_single_match(article, '<h2 class="entry-title">(.*?)</h2>')
        if not url or not title: continue

        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        if thumb.startswith('//'): thumb = 'https:' + thumb

        year = scrapertools.find_single_match(article, '<span class="year">(\d+)</span>')
        if not year: year = '-'

        qlty = scrapertools.find_single_match(article, '<span class="Qlty">([^<]+)</span>')

        langs = []
        if '/Spain.png' in article: langs.append('Esp')
        if '/Mexico.png' in article: langs.append('Lat')
        if '/United-States-Minor-Outlying.png' in article: langs.append('Vose')

        tipo = 'tvshow' if '/series/' in url else 'movie'
        if item.search_type not in ['all', tipo]: continue

        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, qualities=qlty, languages=', '.join(langs), fmt_sufijo=sufijo, 
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '>SIGUIENTE<' in data:
            next_page = scrapertools.find_single_match(data, '<a class="page-link current".*?</a>.*?href="([^"]+)')
            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone (url = next_page, title = '>> Página siguiente', action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('data-season="(.*?)"', re.DOTALL).findall(data)

    for numtempo in matches:
        title = 'Temporada ' + numtempo

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = numtempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, contentType = 'season', contentSeason = numtempo, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    perpage = 50

    data = do_downloadpage(item.url)

    postid = scrapertools.find_single_match(data, 'data-post="(.*?)"')
    if not postid:
        postid = scrapertools.find_single_match(data, 'postid-(.*?) ')

    post = {'action': 'action_select_season', 'season': str(item.contentSeason), 'post': postid}
    headers = {'Referer': item.url}

    data = do_downloadpage(host + 'wp-admin/admin-ajax.php',  post = post, headers = headers)

    patron = '<span class="num-epi">(.*?)</span>.*?<h2 class="entry-title">(.*?)</h2>.*?<a href="(.*?)"'

    matches = scrapertools.find_multiple_matches(data, patron)

    for episode, title, url in matches[item.page * perpage:]:
        epis = scrapertools.find_single_match(episode, '.*?x(.*?)$')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, contentType = 'episode', contentEpisodeNumber = epis ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > (item.page + 1) * perpage:
        itemlist.append(item.clone( title = ">> Página siguiente", action = "episodios", page = item.page + 1, text_color= 'coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'Castellano': 'Esp', 'Latino': 'Lat', 'Subtitulado': 'Vose'}

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, 'href="#(.*?)">.*?<span class="server">(.*?)-(.*?)</span>')

    for opt, servidor, lang in matches:
        servidor = servidor.lower().strip()

        if servidor == 'ok': servidor = 'okru'

        lang = lang.strip()

        url = scrapertools.find_single_match(data, '<div id="' + str(opt) + '".*?<iframe.*?src="(.*?)"')

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = IDIOMAS.get(lang, lang) ))

    # Descargas con recaptcha

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    item.url = item.url.replace('&#038;', '&')

    data = do_downloadpage(item.url)
    url = scrapertools.find_single_match(data, '<iframe.*? src="([^"]+)')

    if url:
        if url.startswith('//'): url = 'https:' + url
        url = url.replace('https://uptostream/', 'https://uptostream.com/')

        servidor = servertools.get_server_from_url(url)
        if servidor and servidor != 'directo':
            url = servertools.normalize_url(servidor, url)
            itemlist.append(item.clone( url=url, server=servidor ))

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
