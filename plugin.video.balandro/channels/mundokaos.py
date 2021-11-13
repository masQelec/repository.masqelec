# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb
from lib import jsunpack


host = 'https://mundokaos.net/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    headers = {'Referer': host}

    if '/release/' in url:
        raise_weberror = False

    # ~ Pendiente de resolver HTTP Error 403: Forbidden

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

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

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'category/estrenos/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Marvel', action = 'list_all', url = host + 'category/marvel/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'category/series-en-estreno/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Destacadas', action = 'list_all', url = host + 'category/series-destacadas/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Animes', action = 'list_all', url = host + 'category/anime/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>GENEROS<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)">(.*?)</a>')

    for url, title in matches:
        if '/estrenos/' in url: continue

        itemlist.append(item.clone( title = title, url = url, action = 'list_all' ))

    itemlist.append(item.clone( title = 'Western', url = host + 'category/western/', action = 'list_all' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1938, -1):
        itemlist.append(item.clone( title = str(x), url = host + 'release/' + str(x) + '/', action = 'list_all' ))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    for letra in 'abcdefghijklmnopqrstuvwxyz#':
        letter = letra
        if letra == '#': letter = '0-9'

        itemlist.append(item.clone ( title = letra.upper(), url = host + 'letter/' + letter + '/', action = 'list_abc' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    data = scrapertools.find_single_match(str(data), '<h2(.*?)</section>')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        tipo = 'movie' if '/peliculas/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')
        title = scrapertools.find_single_match(match, '<h2 class="Title">(.*?)</h2>')

        year = scrapertools.find_single_match(match, '<span class="Date">(.*?)</span>')
        if not year: year = '-'

        qlty = scrapertools.find_single_match(match, '<span class="Qlty">(.*?)</span>')

        if '/peliculas/' in url:
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, qualities=qlty, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))
        else:
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, '<a class="page-link current".*?</a>.*?href="(.*?)"')

    if next_page:
        if '/page/' in next_page:
            itemlist.append(item.clone(title = '>> Página siguiente', url = next_page, action = 'list_all', text_color = 'coral'))

    return itemlist


def list_abc(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<span class="Num">.*?<a href="(.*?)".*?data-src="(.*?)".*?<strong>(.*?)</strong>.*?</td>.*?</td>.*?<td>(.*?)</td>')

    for url, thumb, title, year in matches:
        if thumb.startswith('//'): thumb = 'https:' + thumb

        if '/peliculas/' in url:
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))
        else:
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, '<a class="page-link current".*?</a>.*?href="(.*?)"')

    if next_page:
        if '/page/' in next_page:
            itemlist.append(item.clone(title = '>> Página siguiente', url = next_page, action = 'list_abc', text_color = 'coral'))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<div class="Title"><a href="(.*?)".*?<span>(.*?)</span>')

    for url, numtempo in matches:
        title = 'Temporada ' + numtempo

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.url = url
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = numtempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, url = url, contentType = 'season', contentSeason = numtempo, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    perpage = 50

    data = do_downloadpage(item.url)

    patron = '<td><span class="Num">(.*?)</span>.*?<a href="(.*?)".*?data-lazy-src="(.*?)".*?<td class="MvTbTtl">.*?">(.*?)</a>'

    matches = scrapertools.find_multiple_matches(data, patron)

    for episode, url, thumb, title in matches[item.page * perpage:]:
        titulo = str(item.contentSeason) + 'x' + str(episode) + ' ' + title

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail=thumb,
                                    contentType = 'episode', contentEpisodeNumber = episode ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > (item.page + 1) * perpage:
        itemlist.append(item.clone( title = ">> Página siguiente", action = "episodios", page = item.page + 1, text_color= 'coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'Castellano': 'Esp', 'Spain': 'Esp', 'Mexico': 'Lat', 'Latino': 'Lat', 'Subtitulado': 'Vose', 'United-States-of-AmericaUSA': 'Vose'}

    if '/episodios/' in item.url:
        _type = '2'
    else:
        _type = '1'

    data = do_downloadpage(item.url)

    patron = 'data-key="(.*?)".*?data-id="(.*?)".*?<p class="AAIco-language">(.*?)</p>.*?<p class="AAIco-dns">(.*?)</p>.*?<p class="AAIco-equalizer">(.*?)</p>'

    matches = scrapertools.find_multiple_matches(data, patron)

    ses = 0

    for _key, _id, lang, srv, qlty in matches:
        ses += 1

        url = host + '?trembed=%s&trid=%s&trtype=%s'  %  (_key, _id, _type)

        idioma = IDIOMAS.get(lang, lang)

        servidor = srv.lower()
        if servidor == 'sbembed2' or servidor == 'sbembed1':
            servidor = 'sbembed'
        elif servidor == 'flixplayer': continue
        elif servidor == 'gounlimited': continue

        other = ''
        if 'vip' in servidor:
            other = servidor
            servidor = 'directo'

        servidor = servertools.corregir_servidor(servidor)

        itemlist.append(Item( channel = item.channel, action = 'play', title = '', server = servidor, url = url, other = other,
                              language = idioma, quality = qlty ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.other:
        data = do_downloadpage(item.url)

        url = scrapertools.find_single_match(data, '<div class="Video">.*?src="(.*?)"')
        if not url: url = scrapertools.find_single_match(data, '<IFRAME SRC="(.*?)"')

        if url:
            data = do_downloadpage(url)
            matches = re.compile("go_to_player\('([^']+)'\)", re.DOTALL).findall(data)
            for url in matches:
                if '/hqq.' in url or '/waaw.' in url or '/netu.' in url or 'gounlimited' in url: continue

                itemlist.append(item.clone( url=url, server='directo'))
                break

        return itemlist

    elif 'mundokaos' in item.url:
        data = do_downloadpage(item.url)

        url = scrapertools.find_single_match(data, '<div class="Video">.*?src="(.*?)"')
        if not url: url = scrapertools.find_single_match(data, '<IFRAME SRC="(.*?)"')

        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url or 'gounlimited' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

        if url:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)
            itemlist.append(item.clone( url=url, server=servidor))

        return itemlist

    else:
        url = item.url

    if 'mega1080p' in url:
        url = do_downloadpage(url)
        pack = scrapertools.find_single_match(url, "p,a,c,k,e,d.*?</script>")
        unpack = jsunpack.unpack(pack).replace("\\", "")
        url = scrapertools.find_single_match(unpack, "'file':'([^']+)'")
        url = url.replace("/master", "/720/720p")
        url = 'https://pro.mega1080p.club/' + url
        url += '|Referer=' + url

        itemlist.append(item.clone( url=url, server='directo'))

        return itemlist

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

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
