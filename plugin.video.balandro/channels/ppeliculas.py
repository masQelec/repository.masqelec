# -*- coding: utf-8 -*-

from platformcode import logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

host = 'https://www.pepeliculas.org/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'pelicula/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'genre/estreno/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Destacadas', action = 'list_all', url = host + 'pelicula/', group = 'destacadas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_top', url = host, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_episodes', url = host + 'episodios/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Destacadas', action = 'list_all', url = host + 'series/', group = 'destacadas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_top', url = host, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    opciones = [
       ('accion', 'Acción'),
       ('action-adventure', 'Action & Adventure'),
       ('animacion', 'Animación'),
       ('aventura', 'Aventura'),
       ('ciencia-ficcion', 'Ciencia ficción'),
       ('comedia', 'Comedia'),
       ('comedy', 'Comedy'),
       ('crimen', 'Crimen'),
       ('documental', 'Documental'),
       ('drama', 'Drama'),
       ('familia', 'Familia'),
       ('fantasia', 'Fantasía'),
       ('guerra', 'Guerra'),
       ('historia', 'Historia'),
       ('history', 'History'),
       ('misterio', 'Misterio'),
       ('mystery', 'Mystery'),
       ('musica', 'Música'),
       ('romance', 'Romance'),
       ('sci-fi-fantasy', 'Sci-Fi & Fantasy'),
       ('suspense', 'Suspense'),
       ('terror', 'Terror'),
       ('thriller', 'Thriller'),
       ('war', 'War'),
       ('western', 'Western')
    ]

    for opc, tit in opciones:
        itemlist.append(item.clone( title=tit, url= host + 'genre/' + opc + '/', action = 'list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if item.group == 'destacadas':
        blk = 'destacadas</h2(.*?)recientemente</h2'
    else:
        blk = 'recientemente</h2(.*?)</a></div></div>'

    bloque = scrapertools.find_single_match(data, blk)

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        qlty = scrapertools.find_single_match(match, '<span class="quality">(.*?)</span>')

        year = scrapertools.find_single_match(match, '</h3>.*?<span>(.*?)</span>')
        if year:
            if not len(year) == 4:
                try:
                   year = year.split(',')[1]
                   year = year.strip()
                except:
                   year = ''

        if not year: year = '-'

        if '/pelicula/' in url:
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, qualities=qlty,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if not item.group == 'destacadas':
        next_page = scrapertools.find_single_match(data, "<div class='resppages'>" + '.*?</a><a href="(.*?)".*?><span')
        if not next_page:
            next_page = scrapertools.find_single_match(data, "<div class='resppages'>" + '<a href="(.*?)".*?><span')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone(title = '>> Página siguiente', url = next_page, action = 'list_all', text_color = 'coral'))

    return itemlist


def list_top(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if item.search_type == 'movie':
        blk = '<h3>TOP Movies(.*?)<h3>TOP Series'
    else:
        blk = '<h3>TOP Series(.*?)</div></div></div>'

    bloque = scrapertools.find_single_match(data, blk)

    matches = scrapertools.find_multiple_matches(bloque, "<div class='top-imdb-item'(.*?)<div class='puesto'>")

    for match in matches:
        url = scrapertools.find_single_match(match, "<a href='(.*?)'")

        title = scrapertools.find_single_match(match, "alt='(.*?)'")

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, "src='(.*?)'")

        if '/pelicula/' in url:
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def last_episodes(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, 'recientemente</h2(.*?)</a></div></div>')
    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        season, episode = scrapertools.find_single_match(match, '</h3> <span>T(.*?)E(.*?)/')

        season = season.strip()
        episode = episode.strip()

        title = title.replace('Online', '').replace('Sub Español', 'Vose').strip()

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, contentSerieName=title,
                                   contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, "<div class='resppages'>" + '.*?</a><a href="(.*?)".*?><span')
    if not next_page:
        next_page = scrapertools.find_single_match(data, "<div class='resppages'>" + '<a href="(.*?)".*?><span')

    if next_page:
        if '/page/' in next_page:
            itemlist.append(item.clone(title = '>> Página siguiente', url = next_page, action = 'last_episodes', text_color = 'coral'))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, "<span class='se-t.*?'>(.*?)</span>")

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


def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    perpage = 50

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, "<span class='se-t.*?'>" + str(item.contentSeason) + "</span>(.*?)</div></li></ul></div></div>")

    patron = "<li class='mark-(.*?)'>.*?<img src='(.*?)'.*?<a href='(.*?)'>(.*?)</a>"

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for episode, thumb, url, title in matches[item.page * perpage:]:
        titulo = str(item.contentSeason) + 'x' + str(episode) + ' ' + title

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail=thumb,
                                    contentType = 'episode', contentEpisodeNumber = episode ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > ((item.page + 1) * perpage):
        itemlist.append(item.clone( title = ">> Página siguiente", action = "episodios", page = item.page + 1, text_color= 'coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    patron = "<li id='player-option-.*?"
    patron += "data-type='(.*?)'.*?data-post='(.*?)'.*?data-nume='(.*?)'.*?<span class='title'>(.*?)</span><span class='server'>(.*?)</span>"

    matches = scrapertools.find_multiple_matches(data, patron)

    for _type, _post, _nume, qlty_lang, _server in matches:
        url = host + 'wp-json/dooplayer/v2/%s/%s/%s'  %  (_post, _type, _nume)

        if 'Latino' in qlty_lang:
            qlty = qlty_lang.replace('Latino', '').strip()
            lang = 'Lat'
        elif 'Castellano' in qlty_lang or 'Español' in qlty_lang:
            qlty = qlty_lang.replace('Castellano', '').strip()
            lang = 'Esp'
        elif 'Subtitulado' in qlty_lang or 'VOSE' in qlty_lang:
            qlty = qlty_lang.replace('Subtitulado', '').strip()
            lang = 'Vose'
        else:
            qlty = qlty_lang
            lang = '?'

        other = _server.lower()
        other = other.replace('.com', '').replace('.co', '').replace('.cc', '').replace('.ru', '').replace('.tv', '').replace('my.', '')
        other = other.replace('v2.', '').replace('.veoh', '').replace('.sh', '').replace('.site', '').strip()

        if 'youtube' in other: continue
        elif 'waaw' in other: continue
        elif 'hqq' in other: continue
        elif 'netu' in other: continue
        elif 'openload' in other: continue
        elif 'powvideo' in other: continue
        elif 'streamplay' in other: continue
        elif 'rapidvideo' in other: continue
        elif 'streamango' in other: continue
        elif 'verystream' in other: continue
        elif 'vidtodo' in other: continue

        if other == qlty:
            qlty = ''

        itemlist.append(Item( channel = item.channel, action = 'play', title = '', server = 'directo', url = url, other = other,
                              language = lang, quality = qlty ))

    # ~ Ver en linea
    if 'Ver en línea' in data: 
        patron = "<tr id='link-.*?<img src=.*?"
        patron += "domain=(.*?)'>.*?<a href='(.*?)'.*?target='_blank'>(.*?)</a>.*?<strong class='quality'>(.*?)</strong>.*?</td><td>(.*?)</td>"

        matches = scrapertools.find_multiple_matches(data, patron)

        for domain, url, tipo, qlty, lang in matches:
            if not tipo == 'Ver en línea': continue

            servidor = domain.replace('.com', '').replace('.co', '').replace('.cc', '')

            if lang == 'Latino':
                lang = 'Lat'
            elif lang == 'Castellano' or lang == 'Español':
                lang = 'Esp'
            elif lang == 'Subtitulado' or lang == 'VOSE':
                lang = 'Vose'
            else:
                lang = '?'

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', server = servidor, url = url, other = 'v', language = lang, quality = qlty ))

    # ~ Descargas
    if 'Descarga' in data:
        patron = "<tr id='link-.*?<img src=.*?"
        patron += "domain=(.*?)'>.*?<a href='(.*?)'.*?target='_blank'>(.*?)</a>.*?<strong class='quality'>(.*?)</strong>.*?</td><td>(.*?)</td>"

        matches = scrapertools.find_multiple_matches(data, patron)

        for domain, url, tipo, qlty, lang in matches:
            if not tipo == 'Descarga': continue

            servidor = domain.replace('.com', '').replace('.co', '').replace('.cc', '')

            if lang == 'Latino':
                lang = 'Lat'
            elif lang == 'Castellano' or lang == 'Español':
                lang = 'Esp'
            elif lang == 'Subtitulado' or lang == 'VOSE':
                lang = 'Vose'
            else:
                lang = '?'

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', server = servidor, url = url, other = 'd', language = lang, quality = qlty ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.other == 'v' or item.other == 'd':
        resp = httptools.downloadpage(item.url, follow_redirects=False)
        if 'location' in resp.headers:
            url = resp.headers['location']

    else:
        data = do_downloadpage(item.url)

        url = scrapertools.find_single_match(data, '"embed_url":"(.*?)"')

        url = url.replace('\\/', '/')

        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

        if url.startswith('//'): url = 'https:' + url

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)
        itemlist.append(item.clone( url=url, server=servidor))


    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<article>(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')

        title = scrapertools.find_single_match(match, ' alt="(.*?)"')

        if not url or not title: continue

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        year = scrapertools.find_single_match(match, '<span class="year">(.*?)</span>')
        if not year:
            year = '-'

        plot = scrapertools.htmlclean(scrapertools.find_single_match(match, '<p>(.*?)</p>'))

        if '/pelicula/' in url:
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))
        else:
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year, 'plot': plot} ))

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
