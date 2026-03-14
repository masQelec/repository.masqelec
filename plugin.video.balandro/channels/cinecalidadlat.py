# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.cine-calidad.lat/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action='generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action='generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '<ul class="menu">(.*?)Cerrar</a>')

    matches = re.compile('href="(.*?)">(.*?)</a>').findall(bloque)

    for url, title in matches:
        title = title.strip()

        url = host[:-1] + url

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color = text_color ))

    if itemlist:
        itemlist.append(item.clone( title = 'Western', action = 'list_all', url = host + 'genero/western', text_color = text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<div class="lpmain">(.*?)</div></div></a>')

    for match in matches:
        title = scrapertools.find_single_match(match, '<img alt="(.*?)"')

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        thumb = thumb.replace('&amp;', '&')

        title = title.replace('&#8211;', '').replace('&#8217;', '').replace('&#x27s;', "'s").replace('&#x27;', "'").replace('&#038;', '&').replace('&amp;', '&')

        tipo = 'tvshow' if '/serie/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        url = host[:-1] + url

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': '-'} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title,  infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<span class="page-link current">.*?<a href="(.*?)".*?</span>')

        if next_page:
            if '/pagina/' in next_page:
                next_page = host[:-1] + next_page

                itemlist.append(item.clone( title='Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, 'value="(.*?)"')

    for tempo in matches:
        title = 'Temporada ' + tempo

        if config.get_setting('channels_especiales', default=True):
            if tempo == '0': continue

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

                item.page = 0
                item.contentType = 'season'
                item.contentSeason = tempo
                itemlist = episodios(item)
                return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, url = item.url, page = 0, contentType = 'season', contentSeason = tempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(str(data), '"number":' + str(item.contentSeason) + '.*?"episodes":(.*?)]}')

    matches = scrapertools.find_multiple_matches(str(bloque), '"episode":"(.*?)".*?"slug":"(.*?)"')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('CineCalidadLat', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('CineCalidadLat', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidadLat', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidadLat', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidadLat', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CineCalidadLat', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('CineCalidadLat', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for epis, url in matches[item.page * item.perpage:]:
        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        url = scrapertools.find_single_match(url, "/.*?/(.*?)$")

        url = url.replace('/seasons/', '-temporada-').replace('/episodes/', '-episodio-')

        url = host + 'episodio/' + url

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title = "Siguientes ...", action = "episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    ses = 0

    lngs = scrapertools.find_multiple_matches(str(data), '"player":(.*?)"language":"(.*?)"')

    for lnk, lng in lngs:
        matches = scrapertools.find_multiple_matches(str(lnk), '"result":"(.*?)"')

        for url in matches:
            ses += 1

            if 'latin_spanish' in lng: lang = 'Lat'
            elif 'spanish' in lng: lang = 'Esp'
            elif 'english' in lng: lang = 'Vose'
            else: lang = '?'

            servidor = servertools.get_server_from_url(url)

            if servertools.is_server_available(servidor):
                if not servertools.is_server_enabled(servidor): continue
            else:
                if not config.get_setting('developer_mode', default=False): continue

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)
            elif servidor == 'zures': other = servertools.corregir_zures(url)

            itemlist.append(Item (channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                  language = lang, other = other.capitalize() ))

    # ~ Series
    if not itemlist:
        lngs = scrapertools.find_multiple_matches(str(data), '<div class="pane_descripcion"(.*?)</li></ul>')

        for match in lngs:
            matches = scrapertools.find_multiple_matches(str(match), '<li data-tr="(.*?)".*?<!-- -->(.*?)</span>')

            for url, srv in matches:
                ses += 1

                srv = srv.lower().strip()

                if '>Audio latino<' in match: lang = 'Lat'
                elif '>Audio español<' in match: lang = 'Esp'
                elif '>Audio subtitulado<' in match: lang = 'Vose'
                else: lang = '?'

                servidor = servertools.get_server_from_url(srv)

                if servertools.is_server_available(servidor):
                    if not servertools.is_server_enabled(servidor): continue
                else:
                    if not config.get_setting('developer_mode', default=False): continue

                itemlist.append(Item (channel = item.channel, action = 'play', server = 'directo', title = '', url = url,
                                      language = lang, other = srv.capitalize() ))

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

    if servidor == 'directo':
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

        itemlist.append(item.clone( url=url, server=servidor ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'search?q=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
