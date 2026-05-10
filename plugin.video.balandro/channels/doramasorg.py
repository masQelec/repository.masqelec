# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.doramas.org/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    if not data:
        if not '/ajax/search.php' in url:
            if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('DoramasOrg', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

            timeout = config.get_setting('channels_repeat', default=30)

            httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Doramas', action = 'mainlist_series', text_color = 'firebrick' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'movies/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar dorama ...', action = 'search', search_type = 'tvshow', text_color = 'firebrick' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'catalogo/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host + 'nuevos/', search_type = 'tvshow', text_color='cyan' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'catalogo?status=1', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'catalogo?status=2', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie':
        text_color = 'deepskyblue'
        url_gen = host + 'movies/'
    else:
        text_color = 'firebrick'
        url_gen = host + 'catalogo/'

    data = do_downloadpage(url_gen)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    bloque = scrapertools.find_single_match(data, 'los generos(.*?)los paises')

    matches = re.compile('id="(.*?)".*?<label class="custom-control-label".*?">(.*?)</label>').findall(bloque)
    if not matches: matches = re.compile('id="(.*?)".*?<label class="form-check-label".*?">(.*?)</label>').findall(bloque)

    for id, title in matches:
        title = title.strip()

        url = url_gen[:-1] + '?genre[]=' + id

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color=text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    matches = re.compile('<li class="col-6 col-sm-6 col-md-4 col-lg-3 col-xl-2 col-xxl-2">(.*?)</div></div></div></div>').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, '<div class="content_title fs-15 pr-3 truncate">(.*?)</div>')
        if not title: title = scrapertools.find_single_match(match, '<div class="content_title fs-15 pe-3 truncate">(.*?)</div>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        year = scrapertools.find_single_match(match, '<div class="status">(.*?)</div>').strip()
        if not year: year = '-'
        else: title = title.replace('(' + year + ')', '').strip()

        if '/movie/' in url:
            if item.search_type == 'tvshow': continue

            contentTitle = title

            contentTitle = contentTitle.strip()

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                        contentType='movie', contentTitle=contentTitle, infoLabels={'year': year} ))
        else:
            if item.search_type == 'movie': continue

            SerieName = title

            SerieName = SerieName.strip()

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if '/nuevos/' in item.url: return itemlist

    if itemlist:
        if 'aria-label="Page navigation">' in data:
            next_page = scrapertools.find_single_match(data, 'aria-label="Page navigation">.*?<li class="page-item active">.*?href="(.*?)"')

            if next_page:
                next_page = next_page.replace('&amp;', '&')

                if '?pagina=' in next_page or '&pagina=' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    if config.get_setting('channels_charges', default=True):
        platformtools.dialog_notification('DoramasOrg', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<li class="col-6 col-sm-6 col-md-4 col-lg-4 col-xl-3 col-xxl-3">(.*?)</li>').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, '<div class="content_subtitle truncate">(.*?)</div>')

        if not url or not title: continue

        year = scrapertools.find_single_match(match, '<div class="status">(.*?)</div>')
        if not year: year = '-'
        else: title = title.replace('(' + year + ')', '').strip()

        epis = scrapertools.find_single_match(match, '<div class="content_title truncate">(.*?)<').strip()

        epis = epis.replace('Capitulo', '').replace('Capítulo', '').strip()
        if not epis: epis = 1

        if ' - Temporada' in epis:
            season = scrapertools.find_single_match(epis, ' - Temporada(.*?)$').strip()
            epis = scrapertools.find_single_match(epis, '(.*?) - Temporada')
        else: season = 1

        if not season: season = 1

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

        titulo = str(season) + 'x' + str(epis) + ' ' + title

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo,
                                    contentType='episode', contentSerieName=title, contentSeason=season, contentEpisodeNumber=epis,
                                    infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    if not '<a class="number__season' in data:
        if config.get_setting('channels_seasons', default=True):
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'sin [COLOR tan]Temporadas[/COLOR]')

        item.page = 0
        item.contentType = 'season'
        item.contentSeason = 1

        itemlist = episodios(item)

        return itemlist

    temporadas = re.compile('<a class="number__season.*?href="(.*?)".*?<h6 class="card-title">(.*?)</h6>').findall(data)

    for url, tempo in temporadas:
        tempo = tempo.replace('Temporada', '').strip()

        title = 'Temporada ' + tempo

        season = int(tempo)

        if len(temporadas) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

                item.url = url
                item.page = 0
                item.contentType = 'season'
                item.contentSeason = season
                itemlist = episodios(item)
                return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, url = url,
                                    contentType = 'season', contentSeason = season, page = 0, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    bloque = scrapertools.find_single_match(data, '<div class="chapters__list(.*?)</article>')

    patron = '<a class="media".*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?<h6 class="body-title truncate">(.*?)</h6>'

    matches = re.compile(patron, re.DOTALL).findall(bloque)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('DoramasOrg', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('DoramasOrg', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasOrg', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasOrg', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasOrg', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasOrg', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('DoramasOrg', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, thumb, title, numer in matches[item.page * item.perpage:]:
        title = title.replace('Imagen de', '').strip()

        episode = numer.replace('Capítulo', '').strip()
        if not episode: episode = 1

        title = str(item.contentSeason) + 'x' + str(episode) + ' ' + title

        title = title.replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]')

        itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail=thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=episode ))

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
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    bloque = scrapertools.find_single_match(data, '<ul class="dropdown-menu server(.*?)</ul>')

    matches = re.compile('<li data-lang="(.*?)".*?data-langname="(.*?)".*?<a class="check">(.*?)</a>', re.DOTALL).findall(bloque)

    ses = 0

    for _post, _lang, srv in matches:
        if not _post: continue

        ses += 1

        post = {'id': _post}

        headers = {'Referer': item.url, 'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive'}

        datap = do_downloadpage(host + 'ajax/play.php', post = post, headers = headers)

        url = scrapertools.find_single_match(datap, '<iframe.*?src="(.*?)"')

        if url:
            servidor = servertools.get_server_from_url(url)

            url = servertools.normalize_url(servidor, url)

            if not servidor == 'directo':
                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = 'Vose' ))

    # ~ 23/12/25  es por las Peliculas
    if not itemlist:
        url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')

        if url:
            ses += 1

            servidor = servertools.get_server_from_url(url)

            url = servertools.normalize_url(servidor, url)

            if not servidor == 'directo':
                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = 'Vose' ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def sub_search(item):
    logger.info()
    itemlist = []

    post = {'title': item.post}

    headers = {'Referer': item.ref, 'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive'}

    data = do_downloadpage(host + 'ajax/search.php', post = post, headers = headers)

    matches = re.compile('"slug":"(.*?)".*?"titulo":"(.*?)".*?"img":"(.*?)"', re.DOTALL).findall(str(data))

    for url, title, thumb in matches:
        thumb = thumb.replace('\\/', '/')

        tipo = 'movie' if '/movies/' in item.url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            url = host + 'movies/' + url + '/'

            contentTitle = title

            contentTitle = contentTitle.strip()

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo, 
                                        contentType='movie', contentTitle=contentTitle, infoLabels={'year': '-'} ))

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            url = host + url + '/'

            SerieName = title

            SerieName = SerieName.strip()

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=SerieName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def _epis(item):
    logger.info()

    item.url = host + 'nuevos/'
    item.search_type = 'tvshow'

    return last_epis(item)


def search(item, texto):
    logger.info()
    try:
        if item.search_type == 'movie': item.ref = host + 'movies/'
        elif item.search_type == 'tvshow':  item.ref = host + 'catalogo/'
        else: item.ref = host

        item.post = texto.replace(" ", "+")
        return sub_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
