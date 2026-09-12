# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True

import os, re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb


host = 'https://www.vivatorrents.org/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    if not data:
        if not '/buscar' in url:
            if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('VivaTorrents', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

        timeout = config.get_setting('channels_repeat', default=30)

        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"').strip()
        if not title: title = scrapertools.find_single_match(match, '<h2 class="Title"(.*?)</h2>').strip()

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        if thumb.startswith("//"): thumb = 'https' + thumb

        year = scrapertools.find_single_match(match, '<i>(.*?)</i>')
        if not year: year = '-'

        qlty = ''
        if '(720p)' in title:
            qlty = '720p'
            title = title.replace('(720p)', '').strip()
        elif '(1080p)' in title:
            qlty = '1080p'
            title = title.replace('(1080p)', '').strip()
        elif '(DVDrip)' in title:
            qlty = 'DVDrip'
            title = title.replace('(DVDrip)', '').strip()
        elif '(BRS)' in title:
            qlty = 'BRS'
            title = title.replace('(BRS)', '').strip()
        elif '(HDRip)' in title:
            qlty = 'HDRip'
            title = title.replace('(HDRip)', '').strip()
        elif '(HDR)' in title:
            qlty = 'HDR'
            title = title.replace('(HDR)', '').strip()
        elif '(TS)' in title:
            qlty = 'TS'
            title = title.replace('(TS)', '').strip()
        elif '3D' in title:
            qlty = '3D'
            title = title.replace('3D', '').strip()

        title = title.replace('Español Torrent', '').strip()

        url = host[:-1] + url

        tipo = 'movie' if '/movie/' in url  or '/online/' in url else 'tvshow'

        if tipo == 'tvshow':
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

        if tipo == 'movie':
            title = title.replace('&#039;s', "'s")

            titulo = title

            if "(" in titulo: titulo = titulo.split("(")[0]
            elif "[" in titulo: titulo = titulo.split("[")[0]

            if "Torrent" in titulo: titulo = titulo.split("Torrent")[0]

            titulo = titulo.strip()

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, qualities=qlty,
                                        contentType='movie', contentTitle=titulo, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?<span class="page-numbers current".*?.*?href="(.*?)".*?</a></div></div>')

        if next_page:
            if '/pg/' in next_page:
                next_page = host[:-1] + next_page

                itemlist.append(item.clone( title='Siguientes ...', action='list_all', url=next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    temporadas = re.compile('<span>Temporada(.*?)</span>', re.DOTALL).findall(data)

    for tempo in temporadas:
        season = tempo.strip()

        title = 'Temporada ' + season

        if len(temporadas) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

                item.page = 0
                item.url = item.url
                item.contentType = 'season'
                item.contentSeason = season
                itemlist = episodios(item)
                return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, url = item.url,
                                    page = 0, contentType = 'season', contentSeason = season, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, "<span>Temporada.*?" + str(item.contentSeason) + '.*?</summary>(.*?)</ul>')

    matches = re.compile('<li>(.*?)</li>', re.DOTALL).findall(bloque)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('VivaTorrents', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('VivaTorrents', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VivaTorrents', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VivaTorrents', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VivaTorrents', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VivaTorrents', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('VivaTorrents', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        url = host[:-1] + url

        title = scrapertools.find_single_match(match, '<span>(.*?)</span>').strip()

        epis = scrapertools.find_single_match(match, 'Ep.(.*?)</span>').strip()

        if not epis: epis = 1

        titulo = str(item.contentSeason) + 'x' + str(epis)+ ' ' + item.contentSerieName

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

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

    data = do_downloadpage(item.url)

    ses = 0

    if 'data-url' in data or 'data-lmt' in data:
        links = scrapertools.find_multiple_matches(data, '<span class="Num">(.*?)</span>.*?".*?data-url="(.*?)".*?data-lmt="(.*?)"')

        if not links: links = scrapertools.find_multiple_matches(data, '<span class=Num>(.*?)</span>.*?".*?data-url="(.*?)".*?data-lmt="(.*?)"')

        for num, data_url, data_lmt in links:
            ses += 1

            url = base64.b64decode(data_url).decode("utf-8")

            itemlist.append(Item( channel = item.channel, action='play', title='', url=url, server='torrent', language='Esp', quality='HD' ))

    # ~ Descargar
    downs = scrapertools.find_multiple_matches(data, '<a class="btn btn-primary".*?href="(.*?)".*?>Descargar torrent<')

    for down in downs:
        ses += 1

        itemlist.append(Item( channel = item.channel, action='play', title='', url=down, server='torrent', language='Esp', quality='HD' ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if '/?trdownload=' in url:
        if PY3:
            from core import requeststools
            data = requeststools.read(url, 'vivatorrents')
        else:
             data = do_downloadpage(url, raise_weberror=False)

        if data:
            if 'Página no encontrada' in str(data) or 'no encontrada</title>' in str(data) or '<h1>403 Forbidden</h1>' in str(data):
                 return 'Archivo [COLOR red]No encontrado[/COLOR]'

            file_local = os.path.join(config.get_data_path(), "temp.torrent")
            with open(file_local, 'wb') as f: f.write(data); f.close()

            itemlist.append(item.clone( url = file_local, server = 'torrent' ))

            return itemlist

        else: url = ''

    if url:
        if url.startswith('magnet:'):
            itemlist.append(item.clone( url = url, server = 'torrent' ))

        elif url.endswith(".torrent"):
            itemlist.append(item.clone( url = url, server = 'torrent' ))

        elif '.torrent' in url:
            itemlist.append(item.clone( url = url, server = 'torrent' ))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    _token = scrapertools.find_single_match(data, '<input type="hidden" name="token" value="(.*?)"')

    if not _token: return itemlist

    post = {'Content-Disposition': 'form-data', 'token': _token, 'q': item.tex, 'pg': '1'}

    data = do_downloadpage(host + 'mvc/controllers/data.find.php', post = post, headers = {'Referer': item.url})

    matches = re.compile('{"guid":(.*?)}', re.DOTALL).findall(str(data))

    for match in matches:
        url = scrapertools.find_single_match(match, '"(.*?)"')

        title = scrapertools.find_single_match(match, '"torrentName":"(.*?)"')

        if not url or not title: continue

        url = url.replace('\\/', '/')

        url = host + url

        title = title.replace('&#8211;', '').replace('&#8230;', '').strip()

        thumb = scrapertools.find_single_match(match, '"image":"(.*?)"')

        if thumb.startswith("//"): thumb = 'https' + thumb

        tipo = 'movie' if '/movie/' in url or '/online/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if not item.search_type == 'all':
                if item.search_type == 'movie': continue

            if ' Temporada ' in title:
                itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                            contentType='episode', contentTitle=title, infoLabels={'year': '-'} ))
            else:
                itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                            contentType = 'tvshow', contentSerieName = title, infoLabels={'year': '-'} ))

        if tipo == 'movie':
            if not item.search_type == 'all':
                if item.search_type == 'tvshow': continue

            title = title.replace('&#039;s', "'s")

            titulo = title

            if "(" in titulo: titulo = titulo.split("(")[0]
            elif "[" in titulo: titulo = titulo.split("[")[0]

            if "Torrent" in titulo: titulo = titulo.split("Torrent")[0]

            titulo = titulo.strip()

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=titulo, infoLabels={'year': '-'} ))


    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<a class="page-numbers"' in data:
            next_page = scrapertools.find_single_match(data, '<a class="page-numbers".*?class="page-numbers current">.*?href="(.*?)"')

            if not next_page: next_page = scrapertools.find_single_match(data, '<a class="page-numbers".*?href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title='Siguientes ...', url = next_page, action='list_search', text_color='coral' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
       item.url = host + 'buscar'
       item.tex = texto.replace(" ", "+")
       return list_search(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []
