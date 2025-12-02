# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://flizzmovies.org/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Castellano', action = 'list_all', url = host + 'audio/castellano', text_color='deepskyblue' ))
    itemlist.append(item.clone( title = 'Latino', action = 'list_all', url = host + 'audio/audio_latino', text_color='deepskyblue' ))
    itemlist.append(item.clone( title = 'Subtitulado', action = 'list_all', url = host + 'audio/subtitulada', text_color='deepskyblue' ))

    return itemlist


def calidades(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'HD', action = 'list_all', url = host + 'calidad/HD', text_color='deepskyblue' ))
    itemlist.append(item.clone( title = 'HDs', action = 'list_all', url = host + 'calidad/HDs', text_color='deepskyblue' ))
    itemlist.append(item.clone( title = 'SD', action = 'list_all', url = host + 'calidad/SD', text_color='deepskyblue' ))
    itemlist.append(item.clone( title = 'CAM', action = 'list_all', url = host + 'calidad/CAM', text_color='deepskyblue' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>Géneros(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)".*?<div>(.*?)<span>')

    for url, tit in matches:
        tit = tit.strip()

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = 'deepskyblue' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>Años(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)".*?<div>(.*?)<span>')

    for url, tit in matches:
        tit = tit.strip()

        if tit > str(current_year): continue

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color='deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<h5>(.*?)>Siguenos<')

    matches = scrapertools.find_multiple_matches(bloque, '<li class="item">(.*?)</a></li>')

    for match in matches:
        title = scrapertools.find_single_match(match, '<div class="card_title">.*?<p>(.*?)</p>').strip()

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if not title or not url: continue

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        year = scrapertools.find_single_match(match, '<div class="card_info">(.*?)|').strip()
        if not year: year = '-'

        itemlist.append(item.clone( action = 'findvideos', url=url, title=title, thumbnail=thumb,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?class="link current">.*?href="(.*?)".*?>Siguenos<')

            if next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', action='list_all', url = next_page, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    ses = 0

    # ~ Castellano
    if '>Audio Castellano<' in data or '>Castellano<':
        bloque = scrapertools.find_single_match(data, '>Audio Castellano<(.*?)</div></div>')
        if not bloque: bloque = scrapertools.find_single_match(data, '>Castellano<(.*?)</div></div>')

        links = scrapertools.find_multiple_matches(bloque, 'data-id="(.*?)".*?<span class="servNa">(.*?)</span>.*?data-num="(.*?)"')

        for _id, srv, _num in links:
            if not _id or not srv or not _num: continue

            ses += 1

            if srv == 'abyss': continue
            elif srv == 'krakenfiles': continue
            elif srv == 'rpmvid': continue

            url = item.url + '?id=' + _id + '&num=' + _num

            other = srv.capitalize()

            itemlist.append(Item(channel = item.channel, action = 'play', server = 'directo', title = '', url = url,
                                 language = 'Esp', other = other ))

    # ~ Latino
    if '>Audio Latino<' in data or '>Latino<' in data:
        bloque = scrapertools.find_single_match(data, '>Audio Latino<(.*?)</div></div>')
        if not bloque: bloque = scrapertools.find_single_match(data, '>Latino<(.*?)</div></div>')

        links = scrapertools.find_multiple_matches(bloque, 'data-id="(.*?)".*?<span class="servNa">(.*?)</span>.*?data-num="(.*?)"')

        for _id, srv, _num in links:
            if not _id or not srv or not _num: continue

            ses += 1

            if srv == 'abyss': continue
            elif srv == 'krakenfiles': continue
            elif srv == 'rpmvid': continue

            url = item.url + '?id=' + _id + '&num=' + _num

            other = srv.capitalize()

            itemlist.append(Item(channel = item.channel, action = 'play', server = 'directo', title = '', url = url,
                                 language = 'Lat', other = other ))

    # ~ Subtitulado
    if '>Subtitulada<' in data or '>Audio Subtitulada<' in data:
        bloque = scrapertools.find_single_match(data, '>Subtitulada<(.*?)</div></div>')
        if not bloque: bloque = scrapertools.find_single_match(data, '>Audio Subtitulada<(.*?)</div></div>')

        links = scrapertools.find_multiple_matches(bloque, 'data-id="(.*?)".*?<span class="servNa">(.*?)</span>.*?data-num="(.*?)"')

        for _id, srv, _num in links:
            if not _id or not srv or not _num: continue

            ses += 1

            if srv == 'abyss': continue
            elif srv == 'krakenfiles': continue
            elif srv == 'rpmvid': continue

            url = item.url + '?id=' + _id + '&num=' + _num

            other = srv.capitalize()

            itemlist.append(Item(channel = item.channel, action = 'play', server = 'directo', title = '', url = url,
                                 language = 'Vose', other = other ))

    # ~ Enlaces y Descargar no se tratan

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

    vid_url = re.search(r'\?id\=(\d+)\&num\=(\d+)', url)

    if vid_url:
        item.url = item.url.replace(vid_url.group(0), '')

        _id = vid_url.group(1)

        _num = vid_url.group(2)

        data = do_downloadpage(url, post = {'idF': _id, 'ajax': _num})

        vid = scrapertools.find_single_match(data, '"link":"(.*?)"')

        if vid:
            vid = vid.replace('\\/', '/')

            url = vid

            if '.esplay.' in url: url = ''

            if url:
                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

    if url:
        if item.other.startswith("Sb"):
            return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

        elif 'streamsb' in url or 'playersb' in url:
            return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

        elif 'sbplay' in url or 'sbplay1' in url or 'sbplay2' in url or 'pelistop' in url or 'sbfast' in url or 'sbfull' in url or 'ssbstream' in url or 'sbthe' in url or 'sbspeed' in url or 'cloudemb' in url or 'tubesb' in url or 'embedsb' in url or 'playersb' in url or 'sbcloud1' in url or 'watchsb' in url or 'viewsb' in url or 'watchmo' in url or 'streamsss' in url or 'sblanh' in url or 'sbanh' in url or 'sblongvu' in url or 'sbchill' in url or 'sbrity' in url or 'sbhight' in url or 'sbbrisk' in url or 'sbface' in url or 'view345' in url or 'sbone' in url or 'sbasian' in url or 'streaamss' in url or 'lvturbo' in url or 'sbnet'in url or 'sbani' in url or 'sbrapid' in url or 'cinestart' in url or 'vidmoviesb' in url or 'sbsonic' in url or 'sblona' in url or 'likessb' in url:
            return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

        elif 'openload' in url or 'streamango' in url or 'vidlox' in url or 'jetload' in url or 'verystream' in url or 'streamcherry' in url or 'gounlimited' in url or 'streamix' in url or 'viewsb' in url or 'flix555' in url or '.stormo.' in url or '.spruto.' in url or '/biter.' in url or '/streamin.' in url or '/filebebo.' in url or '/streamcloud.' in url or '/videofiles.' in url or '/kingvid.' in url or '/allvid.' in url or '/goo.' in url:
            return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

        elif 'uptobox' in url:
            return 'Servidor [COLOR goldenrod]Fuera de Servicio[/COLOR]'

        elif '.fembed.' in url:
            return 'Servidor [COLOR goldenrod]Fuera de Servicio[/COLOR]'

        elif '/powv1deo.' in url or '/powvibeo.' in url or '/pouvideo.' in url or '/povw1deo.' in url or '/powvldeo.' in url or '/pomvideo.' in url or '/streamp1ay.' in url or '/slreamplay.' in url or '/stemplay.' in url or '/steamplay.' in url:
            return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

        elif '.rapidvideo.' in url or '.filefactory.' in url or '.owndrives.' in url or '/rapidcloud.' in url or '/ul.' in url or '/fileflares.' in url or '/rockfile.' in url or '/estream.' in url or '/uploadrocket.' in url or '/uploading.' in url or '/ddownload.' in url or '/uploadz.' in url or '/fikper.' in url or '/www.datafile.' in url or '/filerice.' in url or '/thevideo.' in url:
            return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        if url.startswith(host): return itemlist

        itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url, post = item.post)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<li class="item">(.*?)</a></li>')

    for match in matches:
        title = scrapertools.find_single_match(match, '<div class="card_title">.*?<p>(.*?)<small>').strip()

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if not title or not url: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        year = scrapertools.find_single_match(match, '<div class="card_info">(.*?)|').strip()
        if not year: year = '-'

        itemlist.append(item.clone( action = 'findvideos', url=url, title=title, thumbnail=thumb,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
       item.post = {'s': texto.replace(" ", "+")}
       item.url = host
       return list_search(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []

