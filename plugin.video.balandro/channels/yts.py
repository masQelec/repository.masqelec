# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://yts.bz/'


url_browser = host + "browse-movies"


def do_downloadpage(url, post=None):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://en.yts-official.mx/', 'https://wwv.yts-official.mx/', 'https://yts.lt/']

    for ant in ant_hosts:
        url = url.replace(ant, host)

    data = httptools.downloadpage(url, post=post).data

    if '<title>Just a moment...</title>' in data:
        if not '/all/all/0/latest/0/all' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = url_browser, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Actualizadas', action = 'list_all', url = url_browser + '/0/all/all/0/featured/0/all', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = url_browser + '/0/all/all/0/likes/0/all', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = url_browser + '/0/all/all/0/rating/0/all', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'En [COLOR moccasin]4K[/COLOR]', action = 'list_all', url = url_browser + '/0/2160p/all/0/latest/0/all', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def calidades(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(url_browser)

    bloque = scrapertools.find_single_match(data,'<select name="quality">(.*?)</select>')

    matches = scrapertools.find_multiple_matches(bloque,'<option value="(.*?)">(.*?)</option>')

    for qlty, tit in matches:
        if tit == 'All': continue

        url = url_browser + '/0/' + qlty + '/all/0/latest/0/all'

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = 'moccasin' ))

    return sorted(itemlist, key=lambda it: it.title)


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(url_browser)

    bloque = scrapertools.find_single_match(data,'<select name="genre">(.*?)</select>')

    matches = scrapertools.find_multiple_matches(bloque,'<option value="(.*?)">(.*?)</option>')

    for genre, tit in matches:
        if tit == 'All': continue

        url = url_browser + '/0/all/' + genre + '/0/latest/0/all'

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = 'deepskyblue' ))

    return sorted(itemlist, key=lambda it: it.title)


def anios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(url_browser)

    bloque = scrapertools.find_single_match(data,'<select name="year">(.*?)</select>')

    matches = scrapertools.find_multiple_matches(bloque,'<option value="(.*?)"')

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
            if '?page=' in next_page or '&page=' in next_page:
                next_page = host[:-1] + next_page

                itemlist.append(item.clone( title='Siguientes ...', action='list_all', url=next_page, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<div class="modal-torrent">(.*?)</a></div>', re.DOTALL).findall(data)

    ses = 0

    for match in matches:
        links = scrapertools.find_multiple_matches(match,'href="(.*?)"')

        for link in links:
            ses += 1

            url = link

            url = url.replace('&amp;', '&').strip()

            if url:
                qlty = scrapertools.find_single_match(match, 'id="modal-quality-(.*?)"')

                lang = 'Vo'

                if item.lang: lang = item.lang

                peso = scrapertools.find_single_match(match, '<p>Tamaño del archivo</p>.*?<p class="quality-size">(.*?)</p>')

                quality_num = puntuar_calidad(qlty)

                age = ''
                if 'magnet:' in url: age ='Magnet'

                if url.startswith("/"): url = host[:-1] + url

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
