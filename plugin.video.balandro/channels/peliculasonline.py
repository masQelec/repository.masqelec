# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://pelisonline.ws/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'pelis/', acces = 'post', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>Generos<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)".*?title="(.*?)"')

    for url, title in matches:
        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = 'deepskyblue' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie':
        text_color = 'deepskyblue'
        limit_year = 1939
        url_any = host + 'peliculas-'
    else:
        text_color = 'hotpink'
        limit_year = 1959
        url_any = host + 'series-'

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, limit_year, -1):
        itemlist.append(item.clone( title = str(x), url = url_any + str(x) + '/', action = 'list_all', text_color=text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if item.acces == 'post':
        if not item.page: item.page = 1

        post = {'action': 'action_load_pagination_home', 'number': '25', 'paged': item.page, 'postype': item.search_type}

        pelis = host + 'pelis/wp-admin/admin-ajax.php'

        data = do_downloadpage(pelis, post = post, headers = {'Referer': item.url})
    else:
        data = do_downloadpage(item.url)

    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')
    if not matches: matches = scrapertools.find_multiple_matches(data, '<li class="movie-item"(.*?)</li>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h2 class="entry-title">(.*?)</h2>')
        if not title: title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        year = scrapertools.find_single_match(match, '<div class="gr-quality">(.*?)</div>')

        if year: title = title.replace('(' + year + ')', '').strip()
        else: year = '-'

        tipo = 'tvshow' if '/serie/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if item.acces == 'post':
            itemlist.append(item.clone( title = 'Siguientes ...', url = item.url, acces = item.acces, page = item.page + 1,
                            action = 'list_all', text_color='coral' ))
        else:
            if '<div id="pagination">' in data:
                next_page = scrapertools.find_single_match(data, '<div id="pagination">.*?<li class="active">.*?<a href="(.*?)".*?</li>')

                if next_page:
                    if '?page=' in next_page:
                        itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<div class="item-season">.*?Temporada (.*?)</div>', re.DOTALL).findall(data)

    for tempo in matches:
        tempo = tempo.strip()

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
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="item-season">.*?Temporada ' + str(item.contentSeason) + '(.*?)</div></div>')

    matches = re.compile('<a href="(.*?)".*?</i>(.*?)</a>', re.DOTALL).findall(bloque)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('PeliculasOnline', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('PeliculasOnline', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PeliculasOnline', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PeliculasOnline', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PeliculasOnline', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PeliculasOnline', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('PeliculasOnline', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, epis in matches[item.page * item.perpage:]:
        epis = epis.replace('capitulo', '').strip()
        if not epis: epis = 1

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=epis ))

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

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<li data-playerid="(.*?)"')

    if not matches:
        bloque = scrapertools.find_single_match(data, 'var video =(.*?)</script>')

        matches = scrapertools.find_multiple_matches(str(bloque), 'src="(.*?)"')

    ses = 0

    for url in matches:
        ses += 1

        if '=LAT' in url: lang = 'Lat'
        elif '=CAS' in url: lang = 'Esp'
        elif '=SUB' in url: lang = 'Vose'
        else: lang = '?'

        if lang == '?':
            if '(Castellano)' in data: lang = 'Esp'
            elif '(Latino)' in data: lang = 'Lat'
            elif '(Substitulado)' in data: lang = 'Vose'

        if '/ul.' in url: continue
        elif '/1fichier.' in url: continue
        elif '/rapidgator' in url: continue
        elif '/katfile' in url: continue
        elif '/nitro' in url: continue
        elif '/filecrypt.' in url: continue
        elif '/multiup.' in url: continue
        elif '/filemirage.' in url: continue
        elif '/powvideo.' in url: continue

        elif '/viewsb.' in url: continue

        elif '.fembed.' in url: continue
        elif '/fembed.' in url: continue

        elif '/feurl.' in url: continue

        if '/player.cuevana.ac/' in url:
            url = url.replace('/player.cuevana.ac/', '/waaw.to/')

            if '#idioma' in url: url = url.split("#idioma")[0]
            elif '#lang=' in url: url = url.split("#lang=")[0]

        elif '/player.cuevana3.one/' in url:
            url = url.replace('/player.cuevana3.one/', '/waaw.to/')

            if '#idioma' in url: url = url.split("#idioma")[0]
            elif '#lang=' in url: url = url.split("#lang=")[0]

        servidor = servertools.get_server_from_url(url)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        if servidor == 'directo':
            if '/play/' in url:
                data1 = do_downloadpage(url)

                links1 = scrapertools.find_multiple_matches(str(data1), '<li onclick="go_to_player' + ".*?'(.*?)'")
                links2 = scrapertools.find_multiple_matches(str(data1), '<a href="(.*?)"')

                links = links1 + links2

                for url in links:
                    if '/ul.' in url: continue
                    elif '/1fichier.' in url: continue
                    elif '/rapidgator' in url: continue
                    elif '/katfile' in url: continue
                    elif '/nitro' in url: continue
                    elif '/filecrypt.' in url: continue

                    elif '/multiup.' in url: continue
                    elif '/filemirage.' in url: continue
                    elif '/powvideo.' in url: continue

                    elif '/viewsb.' in url: continue

                    elif '.fembed.' in url: continue
                    elif '/fembed.' in url: continue

                    elif '/feurl.' in url: continue

                    if '/player.cuevana.ac/' in url:
                        url = url.replace('/player.cuevana.ac/', '/waaw.to/')

                        if '#idioma' in url: url = url.split("#idioma")[0]
                        elif '#lang=' in url: url = url.split("#lang=")[0]

                    elif '/player.cuevana3.one/' in url:
                        url = url.replace('/player.cuevana3.one/', '/waaw.to/')

                        if '#idioma' in url: url = url.split("#idioma")[0]
                        elif '#lang=' in url: url = url.split("#lang=")[0]

                    servidor = servertools.get_server_from_url(url)

                    if servertools.is_server_available(servidor):
                        if not servertools.is_server_enabled(servidor): continue
                    else:
                        if not config.get_setting('developer_mode', default=False): continue

                    other = ''
                    if servidor == 'various': other = servertools.corregir_other(url)
                    elif servidor == 'zures': other = servertools.corregir_zures(url)

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = lang, other = other ))

                continue

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)
        elif servidor == 'zures': other = servertools.corregir_zures(url)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = lang, other = other ))

    # ~ Series
    if not itemlist:
        bloque = scrapertools.find_single_match(str(data), 'var video =(.*?)</script>')

        matches = scrapertools.find_multiple_matches(str(bloque), '>video.*?<iframe.*?src="(.*?)"')

        for url in matches:
            ses += 1

            if '/ul.' in url: continue
            elif '/1fichier.' in url: continue
            elif '/rapidgator' in url: continue
            elif '/katfile' in url: continue
            elif '/nitro' in url: continue
            elif '/filecrypt.' in url: continue
            elif '/multiup.' in url: continue
            elif '/filemirage.' in url: continue
            elif '/powvideo.' in url: continue

            elif '/viewsb.' in url: continue

            elif '.fembed.' in url: continue
            elif '/fembed.' in url: continue

            elif '/feurl.' in url: continue

            servidor = servertools.get_server_from_url(url)

            if servertools.is_server_available(servidor):
                if not servertools.is_server_enabled(servidor): continue
            else:
                if not config.get_setting('developer_mode', default=False): continue

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)
            elif servidor == 'zures': other = servertools.corregir_zures(url)

            if '(Castellano)' in data: lang = 'Esp'
            elif '(Latino)' in data: lang = 'Lat'
            elif '(Substitulado)' in data: lang = 'Vose'
            else: lang = '?'

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = lang, other = other ))

    # ~ Downloads  No se tratan

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
        new_server = servertools.corregir_other(url).lower()
        if new_server.startswith("http"):
            if not config.get_setting('developer_mode', default=False): return itemlist
        servidor = new_server

    if '.fembed.' in url or '/feurl.' in url:
        return 'Servidor [COLOR red]Fuera de Servicio[/COLOR]'

    url = servertools.normalize_url(servidor, url)

    itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def search(item, texto):
    logger.info()
    try:
       if item.search_type == 'movie': url_search = host + 'pelis/?s='
       elif item.search_type == 'tvshow': url_search = host + 'series/?s='
       else: url_search = host + '?s='

       item.url = url_search + texto.replace(" ", "+")
       return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

