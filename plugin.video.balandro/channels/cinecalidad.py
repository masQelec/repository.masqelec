# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] < 3:
    import urlparse
else:
    import urllib.parse as urlparse

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.cine-calidad.com/'


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    url = url.replace('https://www.cinecalidad.eu/', host)
    url = url.replace('https://www.cinecalidad.im/', host)
    url = url.replace('https://www.cinecalidad.is/', host)
    url = url.replace('https://www.cinecalidad.li/', host)

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

    itemlist.append(item.clone( title = 'En castellano:', folder=False, text_color='plum' ))
    itemlist.append(item.clone( title = ' Catálogo', action = 'list_all', url = host + 'espana/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'En latino:', folder=False, text_color='plum' ))
    itemlist.append(item.clone( title = ' Catálogo', action = 'list_all', url = host, search_type = 'movie' ))
    itemlist.append(item.clone( title = ' Destacadas', action = 'destacadas', url = host, search_type = 'movie' ))
    itemlist.append(item.clone( title = ' En 4K', action = 'list_all', url = host + '4k/', search_type = 'movie' ))

    itemlist.append(item.clone( title = ' Por género', action='generos' ))
    itemlist.append(item.clone( title = ' Por año', action='anios' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    opciones = [
        ('accion','Acción'),
        ('animacion','Animación'),
        ('aventura','Aventura'),
        ('biografia','Biografía'),
        ('ciencia-ficcion','Ciencia ficción'),
        ('comedia','Comedia'),
        ('crimen','Crimen'),
        ('documental','Documental'),
        ('drama','Drama'),
        ('fantasia','Fantasía'),
        ('guerra','Guerra'),
        ('historia','Historia'),
        ('infantil','Infantil'),
        ('misterio','Misterio'),
        ('musica','Música'),
        ('romance','Romance'),
        ('suspenso','Suspenso'),
        ('terror','Terror'),
        ('thriller','Thriller'),
        ('western','Western')
    ]

    for opc, tit in opciones:
        itemlist.append(item.clone( title = tit, url = host + opc + '/', action = 'list_all', search_type = 'movie' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    item.url = host + 'peliculas-por-ano/'

    data = do_downloadpage(item.url)

    matches = re.compile('<a href=([^>]+)>([^<]+)</a><br', re.DOTALL).findall(data)

    for url, title in matches:
        url = urlparse.urljoin(item.url, url)

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, search_type = 'movie' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<div class="home_post_content">(.*?)</div></div>')

    for match in matches:
        title = scrapertools.find_single_match(match, 'class="in_title">(.*?)</div>')
        plot = scrapertools.find_single_match(match, '<p><p>(.*?)</p>')
        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        url = scrapertools.find_single_match(match, ' extract="<a href=.*?' + "'(.*?)'")
        url = url.replace('\\/', '/')

        if not url or not title: continue

        m = re.match(r"^(.*?)\((\d+)\)$", title)
        if m:
            title = m.group(1).strip()
            year = m.group(2)
        else:
            year = '-'

        tipo = 'tvshow' if '/series/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if item.search_type == 'movie':
            if '/series/' in url: continue
            elif '/episodios/' in url: continue
        elif item.search_type == 'tvshow':
            if not '/series/' in url:
               if not '/episodios/' in url: continue
        else:
            if '/episodios/' in url: sufijo = ''

        if tipo == 'movie':
            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year, 'plot': plot} ))

        if tipo == 'tvshow':
            itemlist.append(item.clone( action='temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title,  infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<a class="nextpostslink".*?href="(.*?)"')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url = next_page_link, action = 'list_all', text_color='coral' ))

    return itemlist


def destacadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Destacadas<(.*?)>Herramientas<')

    matches = scrapertools.find_multiple_matches(bloque, 'div class="upw-image">(.*?)</div></li>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'title="(.*?)"')
        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        m = re.match(r"^(.*?)\((\d+)\)$", title)
        if m:
            title = m.group(1).strip()
            year = m.group(2)
        else:
            year = '-'

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, 'name="tab-effect-.*?<span>(.*?)</span>')

    for tempo in matches:
        season = tempo.replace('Temporada', '').strip()

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + tempo + '[/COLOR]')
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = season
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = tempo, url = item.url, contentType = 'season', contentSeason = season, page = 0 ))

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

    bloque = scrapertools.find_single_match(data, 'id="tab-item-' + str(item.contentSeason) + '(.*?)</div>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?class="btn btn btn-primary btn-block">(.*?)</a>')

    for url, title in matches[item.page * perpage:]:
        epis = scrapertools.find_single_match(title, '.*?&#215;(.*?)$').strip()

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > ((item.page + 1) * perpage):
        itemlist.append(item.clone( title = ">> Página siguiente", action = "episodios", page = item.page + 1, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'latino': 'Lat', 'castellano': 'Esp', 'subtitulado': 'Vose'}

    lang = 'Lat'

    if '/espana/' in item.url: lang = 'Esp'

    data = do_downloadpage(item.url)

    data = data.replace("'", '"')

    dec_value = scrapertools.find_single_match(data, 'String\.fromCharCode\(parseInt\(str\[i\]\)-(\d+)\)')

    if 'class="pane_title">VER ONLINE' in data:
        matches = re.compile('(?:onclick="Abrir.*?"|class="link(?: onlinelink)?").*?data(?:-url)?="([^"]+)".*?<li>([^<]+)</li>', re.DOTALL).findall(data)

        for video, servidor in matches:
            servidor = servidor.lower()

            if servidor == "trailer": continue
            elif servidor == 'veri': continue
            elif servidor == 'netu': continue
            elif servidor == 'gounlimited': continue
            elif servidor == 'jetload': continue
            elif servidor == '1fichier': continue
            elif servidor == 'turbobit': continue

            video = dec(video, dec_value)

            if servidor == 'mega':
               if video.startswith('#'):
                   video = 'https://mega.nz/' + video

            servidor = servertools.get_server_from_url(video)
            url = servertools.normalize_url(servidor, video)

            if '/netu.' in url or '/hqq.' in url or '/waaw.' in url: continue

            itemlist.append(Item(channel = item.channel, action = 'play', server = servidor, title = '', url = url, quality = '1080p', language = lang ))

    if '<div class="pane_title">DESCARGAR' in data:
         bloque = scrapertools.find_single_match(data, '<div class="pane_title">DESCARGAR(.*?)<div id="player"')
         matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?<li>(.*?)</li>')

         for url, servidor in matches:
             servidor = servidor.lower()

             if servidor == "subtítulos" or servidor == 'subtitulos': continue
             elif servidor == 'vei': continue
             elif servidor == 'netu': continue
             elif servidor == 'gounlimited': continue
             elif servidor == 'jetload': continue
             elif servidor == '1fichier': continue
             elif servidor == 'turbobit': continue

             qlty = '1080'
             if "4k" in servidor: qlty = '4K'

             if servidor == 'torrent 4k': servidor = 'torrent'
             elif servidor == 'bittorrent': servidor = 'torrent'

             if servidor == 'mega':
                 if url.startswith('#'):
                     url = 'https://mega.nz/' + url

             itemlist.append(Item(channel = item.channel, action = 'play', server = servidor, title = '', url = url, quality = qlty, language = lang ))


    if not itemlist:
        url = scrapertools.find_single_match(data, '<div class="tab-content">.*?src="(.*?)"')
        data = do_downloadpage(url)

        patron = '<li onclick="go_to.*?'
        patron += "'(.*?)'.*?<span>(.*?)</span>.*?<p>(.*?)-"

        matches = scrapertools.find_multiple_matches(data, patron)

        for url, servidor, lang in matches:
            servidor = servidor.lower()

            if servidor == 'netu': continue
            elif servidor == 'veri': continue
            elif servidor == 'gounlimited': continue
            elif servidor == 'jetload': continue
            elif servidor == '1fichier': continue
            elif servidor == 'turbobit': continue
            elif servidor == 'embed': continue

            if '/netu.' in url or '/hqq.' in url or '/waaw.' in url: continue

            lang = lang.lower().strip()
            lang = IDIOMAS[lang]

            servidor = servertools.get_server_from_url(url)
            url = servertools.normalize_url(servidor, url)

            itemlist.append(Item(channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = lang ))

    return itemlist


def dec(item, dec_value):
    link = []

    val = item.split(' ')
    link = list(map(int, val))

    for i in range(len(link)):
        link[i] = link[i] - int(dec_value)
        real = ''.join(map(chr, link))

    return (real)


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    url = url.replace('&amp;', '&')

    if '/protect/v.php' in url or '/protect/v2.php' in url:
        enc_url = scrapertools.find_single_match(url, "i=([^&]+)")
        url = base64.b64decode(enc_url).decode("utf-8")

        if not 'magnet' in url:
            url = url.replace('/file/', '/embed#!')

    if url:
        if url.endswith('.torrent'):
            if config.get_setting('proxies', item.channel, default=''):
                import os

                data = do_downloadpage(url)
                file_local = os.path.join(config.get_data_path(), "temp.torrent")
                with open(file_local, 'wb') as f: f.write(data); f.close()

                itemlist.append(item.clone( url = file_local, server = 'torrent' ))
            else:
                itemlist.append(item.clone( url = url, server = 'torrent' ))

            return itemlist

        if item.server == 'directo':
            if not url.startswith('http'):
                return itemlist

        itemlist.append(item.clone(url = url))

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
