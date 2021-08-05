# -*- coding: utf-8 -*-

import codecs

from platformcode import logger
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://pelisforte.co/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '&years[]' in url:
        raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    return data


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Últimas', action = 'list_all', url = host, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Marvel', action = 'list_all', url = host + 'sg/marvel-mcu/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone ( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>Géneros<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)">(.*?)</a>')

    for url, title in matches:
        itemlist.append(item.clone( action='list_all', title=title, url=url ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Castellano', action = 'list_all', url = host + 'pelis/idiomas/castellano/' ))
    itemlist.append(item.clone( title = 'Latino', action = 'list_all', url = host + 'pelis/idiomas/espanol-latino/' ))
    itemlist.append(item.clone( title = 'Subtitulado', action = 'list_all', url = host + 'pelis/idiomas/subtituladas/' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1977, -1):
        url = '%s?s=trfilter&trfilter=1&years[]=%s,' % (host, str(x))

        itemlist.append(item.clone( title=str(x), url = url, action='list_all' ))

    return itemlist


def list_all(item): 
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, '<h3 class="Title">(.*?)</h3>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')
        plot = scrapertools.find_single_match(match, '<div class="Description"><p>(.*?)</p>')

        year = scrapertools.find_single_match(match, '<span class="Year">(.*?)</span>')
        if not year:
            year ='-'

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    if '<a class="next page-numbers"' in data:
        if '>Siguiente' in data:
            next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="(.*?)"')
            if next_page:
                next_page = next_page.replace('&#038;', '&')
                itemlist.append(item.clone (url = next_page, title = '>> Página siguiente', action = 'list_all', text_color='coral'))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<ul id="fenifdev-lang-ul">(.*?)<div>Trailer</div>')

    matches = scrapertools.find_multiple_matches(bloque, '.*?<div>(.*?)<span class="quality">(.*?)</span>')

    for idioma, qlty in matches:
        if 'Latino' in idioma: lang = 'Lat'
        elif 'Castellano' in idioma: lang = 'Esp'
        elif 'Subtitulado' in idioma: lang = 'Vose'
        else:
           lang = idioma

        blok_lang = scrapertools.find_single_match(bloque, '<div>' + idioma + '.*?<i class="fa fa-chevron-down">(.*?)/img/')

        options = scrapertools.find_multiple_matches(blok_lang, 'data-tplayernv="(.*?)"')

        blok_opts = scrapertools.find_single_match(data, '<div class="TPlayer">(.*?)<span class="')
        blok_opts = blok_opts.replace('&quot;', '"')

        for opt in options:
            srv = scrapertools.find_single_match(blok_lang, 'data-tplayernv="' + opt + '".*?<img src=".*?/>(.*?)</li>')
            srv = scrapertools.find_single_match(srv, '.*?-(.*?)-').strip()

            if not srv: continue

            servidor = 'directo'
            other = srv

            url = scrapertools.find_single_match(blok_opts, 'id="' + opt + '".*?src="([^"]+)"')

            if url:
                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, other = other,
                                      language = lang, quality = qlty ))

    # ~ descargas requieren recaptcha
    # ~ links = scrapertools.find_multiple_matches(data, '<td><span class="Num">(.*?)</tr>')

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    item.url = item.url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

    url = item.url

    if item.other:
        data = do_downloadpage(item.url)

        url = scrapertools.find_single_match(data, '<div class="Video">.*?src="(.*?)"')
        if not url: url = scrapertools.find_single_match(data, '<IFRAME SRC="(.*?)"')

        if not url:
            url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')

        if 'trhide' in url:
            try:
               new_url = scrapertools.find_single_match(url, 'tid=([A-z0-9]+)')[::-1]
               new_url = codecs.decode(new_url, 'hex')

               headers = {'Referer': item.url}
               data = do_downloadpage(new_url, headers = headers)

               if 'grecaptcha.execute' in data:
                   return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

               url = new_url
            except:
               pass

        elif url.startswith(host):
            if url.endswith('&'):
                url = url + '='
                url = url.replace('&=', '')

            headers = {'Referer': item.url}
            data = do_downloadpage(url, headers = headers)

            url = scrapertools.find_single_match(data, '<div class="Video">.*?src="(.*?)"')
            if not url: url = scrapertools.find_single_match(data, '<IFRAME SRC="(.*?)"')

    if url:
        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url or 'gounlimited' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def search(item, texto):
    logger.info("texto: %s" % texto)
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
