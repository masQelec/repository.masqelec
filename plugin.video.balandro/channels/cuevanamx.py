# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.cuevana-3.mx'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    if not data:
        if not '/search?q=' in url:
            if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('CuevanaMx', '[COLOR cyan]Re-Intentando acceso[/COLOR]')

            timeout = config.get_setting('channels_repeat', default=30)

            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title='Animes', action = 'mainlist_animes', text_color='springgreen' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + '/peliculas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + '/peliculas/estrenos', search_type = 'movie', text_color='cyan' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + '/peliculas/tendencias/semana', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catalogo', action = 'list_all', url = host + '/series', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host + '/episodios', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + '/series/tendencias/semana', search_type = 'tvshow' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catalogo', action = 'list_all', url = host + '/animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + '/animes/tendencias/semana', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    logger.info()
    itemlist = []

    data = do_downloadpage(host + '/peliculas')

    bloque = scrapertools.find_single_match(data,'>Generos<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque,'<a href="(.*?)">(.*?)</a>')

    for url, tit in matches:
        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color='deepskyblue' ))

    if itemlist:
        itemlist.append(item.clone( title = 'Western', url = host + '/genero/western', action = 'list_all', text_color='deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<div class="TPost C(.*?)</li>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<div class="Title">(.*?)</div>').strip()

        if not url or not title: continue

        title = title.replace('&#039;s', "'s").replace('&#x27;s', "'s").replace('&#x27;', "'").strip()

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"').replace('&amp;', '&').strip()

        thumb = host + thumb

        year = scrapertools.find_single_match(match, '<span class="Year">(.*?)</span>')
        if not year: year = '-'

        tipo = 'tvshow' if '/serie/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<nav class="navigation pagination">' in data:
            bloque_next = scrapertools.find_single_match(data, '<nav class="navigation pagination">(.*?)</nav>')

            next_page = scrapertools.find_single_match(bloque_next, '<span class="page-link current">.*?href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h2 class="Title">(.*?)</h2>').strip()

        if not url or not title: continue

        title = title.replace('&#039;s', "'s").replace('&#x27;s', "'s").replace('&#x27;', "'").strip()

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"').replace('&amp;', '&').strip()

        thumb = host + thumb

        season = scrapertools.find_single_match(url, '/temporada/(.*?)/episodio/')
        if not season: season = 1

        episode = scrapertools.find_single_match(url, '/episodio/(.*?)$')
        if not episode: episode = 1

        contentSerieName = scrapertools.find_single_match(title, '(.*?) \d')

        thumb = 'https://' + thumb

        titulo = str(season) + 'x' + str(episode) + ' ' + title.replace(str(season) + 'x' + str(episode), '')

        itemlist.append(item.clone( action='findvideos', title = titulo, thumbnail=thumb, url = url,
                                    contentType = 'episode', contentSerieName=contentSerieName, contentSeason = season, contentEpisodeNumber = episode ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<nav class="navigation pagination">' in data:
            bloque_next = scrapertools.find_single_match(data, '<nav class="navigation pagination">(.*?)</nav>')

            next_page = scrapertools.find_single_match(bloque_next, '<span class="page-link current">.*?href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'last_epis', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<option value="(.*?)"', re.DOTALL).findall(data)

    for tempo in matches:
        tempo = tempo.strip()

        if tempo == '0':
            if config.get_setting('channels_especiales', default=True): continue

        title = 'Temporada ' + tempo

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action='episodios', title=title, page = 0, contentType='season', contentSeason=tempo, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist=[]

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    data = data.replace('{"number"', '<INICIO>').replace('}]},', '}</FINAL>')

    bloque = scrapertools.find_single_match(str(data), '<INICIO>:' + str(item.contentSeason) + '(.*?)</FINAL>')

    matches = re.compile('(.*?)}}', re.DOTALL).findall(bloque)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('CuevanaMx', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('CuevanaMx', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CuevanaMx', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CuevanaMx', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CuevanaMx', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CuevanaMx', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('CuevanaMx', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        title = scrapertools.find_single_match(str(match), '"title":"(.*?)"')

        url = scrapertools.find_single_match(str(match), '"slug":"(.*?)"')

        if not title or not url: continue

        epis = scrapertools.find_single_match(str(match), '"number":(.*?),')
        if not epis: epis = 1

        thumb = scrapertools.find_single_match(str(match), '"image":"(.*?)"')

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title.replace(str(item.contentSeason) + 'x' + str(epis), '').strip()

        url = host + '/' + url

        url = url.replace('/series/', '/serie/').replace('/seasons/', '/temporada/').replace('/episodes/', '/episodio/')

        itemlist.append(item.clone( action='findvideos', title = titulo, thumbnail=thumb, url = url,
                                    contentType = 'episode', contentSeason = item.season, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > (item.page + 1) * item.perpage:
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'Latino': 'Lat', 'Castellano': 'Esp', 'Subtitulado': 'Vose'}

    data = do_downloadpage(item.url)

    matches = re.compile('<div class="_1R6bW_0">(.*?)</path>', re.DOTALL).findall(data)

    ses = 0

    for option in matches:
        ses += 1

        links = re.compile('<li class="clili(.*?)</li>', re.DOTALL).findall(option)

        for link in links:
            srv = scrapertools.find_single_match(link, '>. <!-- -->(.*?)<!-- -->').lower()

            if srv == 'ul': continue
            elif srv == '1fichier': continue
            elif srv == 'rapidgator': continue
            elif srv == 'katfile': continue
            elif srv == 'nitro': continue
            elif srv == 'filecrypt': continue
            elif srv == 'filepv': continue
            elif srv == 'ddownload': continue

            elif srv == 'netu' or srv == 'hqq': srv = 'waaw'
            elif srv == 'voesx': srv = 'voe'

            if servertools.is_server_available(srv):
                if not servertools.is_server_enabled(srv): continue
            else:
                if not config.get_setting('developer_mode', default=False): continue

            url = scrapertools.find_single_match(link, 'data-tr="(.*?)"')

            if 'Español Latino' in option: lng = 'Lat'
            elif 'Español' in option: lng = 'Esp'
            elif 'Subtitulado' in option: lng = 'Vose'
            else: lng = '?'

            other = ''
            if srv == 'streamwish':
                other = srv
                srv = 'various'
            elif srv == 'filemoon':
                other = srv
                srv = 'various'
            elif srv == 'vidhide':
                other = srv
                srv = 'various'

            itemlist.append(Item( channel = item.channel, action = 'play', server = srv, title = '', url = url,
                                  language = IDIOMAS.get(lng, lng), other = other.capitalize() )) 

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    servidor = item.server

    data = do_downloadpage(item.url)

    new_url = scrapertools.find_single_match(data, "var url = '(.*?)'")

    if new_url: url = new_url

    if url:
        servidor = servertools.get_server_from_url(url)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def _news(item):
    logger.info()

    item.url = host + '/peliculas/estrenos'
    item.search_type = 'movie'

    return list_all(item)


def _epis(item):
    logger.info()

    item.url = host + '/episodios'
    item.search_type = 'tvshow'

    return last_epis(item)


def search(item, texto):
    logger.info()
    try:
        item.url = host + '/search?q=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
