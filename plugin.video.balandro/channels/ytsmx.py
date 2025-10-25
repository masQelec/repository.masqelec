# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://yts.mx/'


url_browser = host + "browse-movies"


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://en.yts-official.mx/']

    for ant in ant_hosts:
        url = url.replace(ant, host)

    headers = {'Referer': host}

    data = httptools.downloadpage(url, post=post, headers=headers).data

    if not data:
        if not '/all/all/0/latest/0/all' in url:
            if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('YtsMx', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

            timeout = config.get_setting('channels_repeat', default=30)

            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = url_browser, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Tendencias', action = 'list_all', url = host + 'trending-movies', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = url_browser + '/0/all/all/0/featured/0/all', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = url_browser + '/0/all/all/0/rating/0/all', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'En [COLOR moccasin]4K[/COLOR]', action = 'list_all', url = url_browser + '/0/2160p/all/0/latest/0/all', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por idioma', action= 'idiomas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'movie' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'En castellano', action = 'list_all', url = url_browser + '/0/all/all/0/latest/0/es', lang='Esp', search_type = 'movie', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'En inglés', action = 'list_all', url = url_browser + '/0/all/all/0/latest/0/en', lang='Ing', search_type = 'movie', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'Subtituladas', action = 'list_all', url = url_browser + '/0/all/all/0/latest/0/foreign', lang='Vos', search_type = 'movie', text_color='moccasin' ))

    return itemlist


def calidades(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(url_browser)

    bloque = scrapertools.find_single_match(data,'<select name="quality">(.*?)</select>')

    matches = scrapertools.find_multiple_matches(bloque, '<option value="(.*?)">(.*?)</option>')

    for qlty, tit in matches:
        if tit == 'All': continue

        url = url_browser + '/0/' + qlty + '/all/0/latest/0/all'

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = 'moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(url_browser)

    bloque = scrapertools.find_single_match(data,'<select name="genre">(.*?)</select>')

    matches = scrapertools.find_multiple_matches(bloque, '<option value="(.*?)">(.*?)</option>')

    for genre, tit in matches:
        if tit == 'Todos': continue

        url = url_browser + '/0/all/' + genre + '/0/latest/0/all'

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = 'deepskyblue' ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'languages')

    bloque = scrapertools.find_single_match(data, '<select name="language">(.*?)</select>')

    matches = re.compile('<option value="(.*?)">(.*?)</option>', re.DOTALL).findall(bloque)

    for value, title in matches:
        if 'all"' in value: continue

        if title == 'Extranjero': continue

        title = title.capitalize()

        url = url_browser + '/0/all/all/0/latest/0/' + value

        itemlist.append(item.clone( title = title, url = url, action = 'list_all', value = value, text_color='deepskyblue' ))

    return sorted(itemlist, key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(url_browser)

    bloque = scrapertools.find_single_match(data,'<select name="year">(.*?)</select>')

    matches = scrapertools.find_multiple_matches(bloque, '<option value="(.*?)"')

    for anyo in matches:
        if anyo == '0': continue

        url = url_browser + '/0/all/all/0/latest/' + anyo + '/all'

        itemlist.append(item.clone( title = anyo, url = url, action = 'list_all', text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    data = data.replace('</div></div> </div>', '</div></div></div>')

    matches = re.compile('<div class="browse-movie-wrap col-xs-10 col-sm-4 col-md-5 col-lg-4">(.*?)</div></div></div>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'class="browse-movie-title">(.*?)</a>')

        if not url or not title: continue

        if '</span>' in title: 
            title = scrapertools.find_single_match(title, '</span>(.*?)$').strip()

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        year = scrapertools.find_single_match(match, '<div class="browse-movie-year">(.*?)$')
        if not year: tear = '-'

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, 'class="current">.*?href="(.*?)"')

        if next_page:
            if '?page=' in next_page:
                next_page = host[:-1] + next_page

                itemlist.append(item.clone( title='Siguientes ...', action='list_all', url=next_page, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<div class="modal-torrent">(.*?)</span></a>', re.DOTALL).findall(data)

    lang = 'Vo'

    if 'SPANISH' in data: lang = 'Esp'
    elif 'CATALAN' in data: lang = 'Cat'
    else:
        if item.lang: lang = item.lang

    ses = 0

    for match in matches:
        ses += 1

        links = scrapertools.find_multiple_matches(match, 'href="(.*?)"')

        for url in links:
            url = url.replace('&amp;', '&').strip()

            if url:
                if url.startswith("/"): url = host[:-1] + url

                qlty = scrapertools.find_single_match(match, 'id="modal-quality-.*?<span>(.*?)</span>')

                peso = scrapertools.find_single_match(match, '<p>File size</p>.*?<p class="quality-size">(.*?)</p>')

                age = ''

                if 'magnet:?' in url: age = 'Magnet'

                quality_num = puntuar_calidad(qlty)

                itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = 'torrent',
                                      language = lang, quality = qlty, quality_num = quality_num, other = peso, age = age ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def puntuar_calidad(txt):
    orden = ['480p', '720p', '1080p', 'x.265', '3d', '3D', '2160p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1


def search(item, texto):
    logger.info()
    try:
        item.url = url_browser + '/' + texto.replace(" ", "+") + '/all/all/0/latest/0/all'
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
