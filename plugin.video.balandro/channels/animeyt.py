# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://animeyt.moe/'


def mainlist(item):
    return mainlist_animes(item)


def mainlist_animes(item):
    logger.info()
    itemlist = []

    descartar_anime = config.get_setting('descartar_anime', default=False)

    if descartar_anime: return itemlist

    if config.get_setting('adults_password'):
        from modules import actions
        if actions.adults_password(item) == False:
            return itemlist

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Actualizados', action = 'list_all', url = host + 'animes-actualizados', search_type = 'tvshow' ))

    # ~ itemlist.append(item.clone( title = 'Últimos animes', action = 'list_all', url = host + 'animes-nuevos', search_type = 'tvshow' ))

    # ~ itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'animes-en-emision', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host + 'animes-mas-vistos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por categorías', action = 'categorias', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    data = scrapertools.find_single_match(data, '<a>Categorias(.*?)<li class="second_menu_item">')

    matches = re.compile(r'<a href="(.*?)">(.*?)</a>').findall(data)

    for url, title in matches:
        itemlist.append(item.clone( title = title, action = 'list_all', url = url ))

    return sorted(itemlist,key=lambda x: x.title)


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    data = scrapertools.find_single_match(data, '<a>Géneros(.*?)</ul>')

    matches = re.compile('<a href="(.*?)".*?">(.*?)</a>').findall(data)

    for url, title in matches:
        if title == 'MÃºsica': title = 'Música'
        elif title == 'NiÃ±os': title = 'Niños'
        elif title == 'PolicÃ­a': title = 'Policía'
        elif title == 'PsicolÃ³gico': title = 'Psicológico'
        elif title == 'ReencarnaciÃ³n': title = 'Reencarnación'

        itemlist.append(item.clone( title = title, action = 'list_all', url = url ))

    return sorted(itemlist,key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    try:
        data = httptools.downloadpage(item.url).data
        data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)
    except:
        return itemlist

    bloque = scrapertools.find_single_match(data, '<h2.*?</i></a></div>(.*?)</main>')
    if not bloque: bloque = scrapertools.find_single_match(data, '<h2(.*?)</main>')

    patron = '<a href="(.*?)".*?<div class="category.*?">(.*?)</div>.*?<img src="(.*?)".*?<div class="title">(.*?)</div>'

    matches = re.compile(patron).findall(bloque)

    for url, type, thumb, title in matches:
        if not url or not title: continue

        title = title.replace('(Sub EspaÃ±ol)', '(Sub Español)')

        titulo = title.replace('(Pelicula)', '').replace('(Sub Español)', '').replace('(Audio Latino)', '').replace('Audio castellano', '').strip()

        type = type.strip()

        if type:
            if not type == 'Anime':
                if not type == 'Especial':
                    title = '[COLOR tan]' + type + '[/COLOR] ' + title

        if '/pelicula/' in url:
            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                        contentType='movie', contentTitle=titulo, infoLabels={'year': '-'} ))
        else:
            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, 
                                        contentType = 'tvshow', contentSerieName = titulo, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
         if '<div class="pagination' in data:
             next_url = scrapertools.find_single_match(data, '<div class="pagination.*?href="#">.*?href="(.*?)"')

             if next_url:
                 itemlist.append(item.clone( title = 'Siguientes ...', url = next_url, action = 'list_all', text_color = 'coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = httptools.downloadpage(item.url).data

    matches = scrapertools.find_multiple_matches(data, '<div data-episode="(.*?)".*?<a href="(.*?)".*?<div class="episode_number">(.*?)</div>')

    if item.page == 0:
        sum_parts = len(matches)
        if sum_parts > 250:
            if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos?'):
                platformtools.dialog_notification('AnimeYt', '[COLOR cyan]Cargando elementos[/COLOR]')
                item.perpage = 250

    for epis, url, title in matches[item.page * item.perpage:]:
        itemlist.append(item.clone( action='findvideos', url = url, title = title, contentType = 'episode', contentSeason = 1, contentEpisodeNumber=epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    ses = 0

    bloque = scrapertools.find_single_match(data, 'var iframes =(.*?)</script>')

    matches = re.compile(r'.*?"(.*?)"', re.DOTALL).findall(str(bloque))

    for url in matches:
        ses += 1

        url = url.replace('\\/' ,'/')

        if url:
            if url.startswith('//'): url = 'https:' + url

            if '/hqq.' in url or '/waaw.' in url or '/netu.' in url: continue

            elif 'player.animeyt' in url: continue
            elif 'jetload.' in url: continue

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            other = ''
            if servidor == 'directo': other = url

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    servidor = item.server

    url = item.url

    if not servidor == 'directo':
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        itemlist.append(item.clone(url = url, server = servidor))

        return itemlist

    if url:
        if not url.startswith("http"): url = "https:" + url

        url = url.replace('&amp;', '&').replace("\\/", "/")

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        itemlist.append(item.clone(url = url, server = servidor))

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

