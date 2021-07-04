# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www10.animeflv.cc/'

perpage = 30


def mainlist(item):
    return mainlist_anime(item)


def mainlist_anime(item):
    logger.info()
    itemlist = []

    descartar_anime = config.get_setting('descartar_anime', default=False)

    if descartar_anime: return itemlist
    if config.get_setting('adults_password'):
        from modules import actions
        if actions.adults_password(item) == False:
            return itemlist

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'browse', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Novedades', action = 'list_all', url = host, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos',  search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por categorías', action = 'categories', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def categories(item):
    logger.info()
    itemlist = []

    url_cat = url = host + 'browse'

    data = httptools.downloadpage(url_cat).data

    patron = r'<li class="tmp "><a><label class="radio"><input  type="radio" value="(\d+)" name="order" data-text="([^"]+)'
    matches = re.compile(patron).findall(data)

    search_type = item.search_type

    for categorie_id, title in matches:
        url = '%s?order=%s' %(url_cat, categorie_id)
        title = title.strip()

        itemlist.append(item.clone( action = "list_all", url = url, title = title, search_type = search_type))

    return sorted(itemlist, key=lambda x: x.title)


def generos(item):
    logger.info()
    itemlist = []

    url_genre = url = host + 'browse'

    data = httptools.downloadpage(url_genre).data
    patron = r'a><label><input  class="genre-ids" value="([^"]+)".*?type="checkbox">([^<]+)'
    matches = re.compile(patron).findall(data)

    search_type = item.search_type

    for genre_id, title in matches:
        url = '%s?genres=%s' %(url_genre, genre_id)

        itemlist.append(item.clone( action = "list_all", url = url, title = title, search_type = search_type))

    return sorted(itemlist, key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    url_anio = url = host + 'browse'

    tope_year = 1989

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, tope_year, -1):
        itemlist.append(item.clone( title = str(x), url = '%s?year=%s' % (url_anio, str(x)), action = 'list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    data = httptools.downloadpage(item.url).data

    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)
    patron = '<article class="Anime alt[^"]+"><a href="([^"]+)">'
    patron += '<.*?img src="([^"]+)".*?h3 class="Title">([^<]+).*?<span class="Type ([^"]+).*?<p class="des">([^<]+)'

    matches = re.compile(patron).findall(data)
    num_matches = len(matches)

    for url, thumb, title, tipo, info in matches[item.page * perpage:]:
        if not url or not title: continue

        if tipo == "movie":
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))
        else:
            itemlist.append(item.clone( action='episodios', url=url if url.startswith('http') else host[:-1] + url, title=title, thumbnail=thumb, 
                                        contentType = 'tvshow', plot = info, contentSerieName = title, infoLabels={'year':'-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    # Subpaginación interna y/o paginación de la web
    buscar_next = True
    if num_matches > perpage: # subpaginación interna dentro de la página si hay demasiados items
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title = '>> Página siguiente', page = item.page + 1, action = 'list_all', text_color = 'coral' ))
            buscar_next = False

    if buscar_next:
        if itemlist:
            patron = "li\s*class=selected><a href='[^']+.*?<\/li><li.*?<a href='([^']+)"
            next_url = scrapertools.find_single_match(data, patron)
            if next_url:
                itemlist.append(item.clone( title = '>> Página siguiente', url = next_url if url.startswith('http') else item.url + next_url if not '?' in item.url else item.url.split('?')[0] + next_url,
                                            action = 'list_all', page = 0, text_color = 'coral' ))

            
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    perpage = 50

    data = httptools.downloadpage(item.url).data
    # ~ if developer == True: logger.debug(data)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    patron = '<li class="fa-play-circle"><a href="([^"]+)"><.*?this.src=\'([^\']+).*?<p>([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, thumb, title in matches[item.page * perpage:]:

        itemlist.append(item.clone( action='findvideos', url = url if url.startswith('http') else host[:-1] + url, title = title, thumbnail=thumb, contentType = 'episode'))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > ((item.page + 1) * perpage):
        itemlist.append(item.clone( title=">> Página siguiente", action="episodios", page=item.page + 1, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = r'<li role="presentation" data-video="([^"]+)" title="([^"]+)">\s*<a href="[^"]+'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, server in matches:
        if not url: continue
        if not url.startswith('http'):
            url = 'https:' + url
        servidor = servertools.get_server_from_url(url)
        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if "/v/" in item.url:
        data = httptools.downloadpage(item.url).data
        if 'yandex.ru' in data:
            url = item.url.split('/v/')[0]
            item.url = item.url.replace(url, 'https://fembed.com')

    itemlist.append(item.clone(url = item.url.replace("\\/", "/")))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'browse?q=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

