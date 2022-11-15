# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://espapelis.pro/'


perpage = 20


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/fecha/' in url: raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    patron = '<li id="menu-item-\d+" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-\d+"><a href="([^"]+)">([^<]+)'
    matches = re.compile(patron).findall(data)

    for url, title in matches:
        itemlist.append(item.clone( title = title.capitalize(), action = 'list_cat', url = url ))

    if itemlist:
        opciones = {
            'accion': 'Acción',
            'action': 'Action',
            'animacion': 'Animación',
            'animation': 'Animation',
            'adventure': 'Adventure',
            'belica': 'Bélica',
            'ciencia-ficcion': 'Ciencia ficción',
            'comedy': 'Comedy',
            'crime': 'Crime',
            'documental': 'Documental',
            'documentary': 'Documentary',
            'familia': 'Familia',
            'family': 'Family',
            'fantasia': 'Fantasía',
            'fantasy': 'Fantasy',
            'historia': 'Historia',
            'history': 'History',
            'horror': 'Horror',
            'misterio': 'Misterio',
            'mystery': 'Mystery',
            'music': 'Music',
            'musica': 'Música',
            'romance': 'Romance',
            'science-fiction': 'Science Fiction',
            'suspense': 'Suspense',
            'thriller': 'Thriller',
            'war': 'War',
            'western': 'Western'
            }

        for opc in sorted(opciones):
            itemlist.append(item.clone( title = opciones[opc], url = host + 'category/' + opc + '/', action ='list_cat' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1919, -1):
        url = host + 'peliculas/fecha/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action='list_cat' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    if item.post:
        data = do_downloadpage(item.url, item.post)
    else:
        data = do_downloadpage(item.url)

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(data)

    num_matches = len(matches)

    for article in matches[item.page * perpage:]:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')

        title = scrapertools.find_single_match(article, '<div class="entry-title">(.*?)</div>')
        if not title: title = scrapertools.find_single_match(article, '<h2 class="entry-title">(.*?)</h2>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, infoLabels = {'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        buscar_next = True
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title = 'Siguientes ...', page = item.page + 1, action='list_all', text_color='coral' ))
                buscar_next = False

        if buscar_next:
            url = host + 'wp-admin/admin-ajax.php'

            if not item.next_page:
                if not '"load-more-ajax"' in data:
                   return itemlist

                item.next_page = 1

            item.next_page = item.next_page + 1

            post = {'action': 'action_load_pagination_home', 'number': 20, 'paged': item.next_page, 'postype': 'movie'}

            itemlist.append(item.clone( title = 'Siguientes ...', url = url, post = post, action = 'list_all',
                                        page = 0, next = item.next_page, text_color='coral' ))

    return itemlist


def list_cat(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(data)

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')

        title = scrapertools.find_single_match(article, '<div class="entry-title">(.*?)</div>')
        if not title: title = scrapertools.find_single_match(article, '<h2 class="entry-title">(.*?)</h2>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if "<div class='wp-pagenavi'" in data:
            next_page = scrapertools.find_single_match(data, "class='current'>" + '.*?href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_cat',  next = next_page, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist=[]

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<li data-playerid="(.*?)".*?/flags/(.*?).png.*?<span style.*?>(.*?)</span>')

    ses = 0

    for url, lang, qlty in matches:
        ses += 1

        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url: continue

        elif '/gounlimited.' in url: continue
        elif '/jetload.' in url: continue
        elif '/vidcloud.' in url: continue
        elif '.mystream.' in url: continue

        elif '/links.cuevana.ac' in url: continue
        elif '/player.cuevana3.one' in url: continue

        if lang == 'es': lang = 'Esp'
        elif lang == 'la': lang = 'Lat'
        elif lang == 'mx': lang = 'Lat'
        else: lang = 'Vose'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        itemlist.append(Item(channel = item.channel, action = 'play', title = '', server = servidor, url = url, language = lang, quality = qlty ))

    # Descargas No se tratan por Warez Locker Site

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
