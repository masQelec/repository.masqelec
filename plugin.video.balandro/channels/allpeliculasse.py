# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True

import re, os

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

from lib import decrypters


host = 'https://allpeliculas.se/'


per_page = '20'

rut_movies = host + 'wp-api/v1/tops?postType=movies&range=day&orderBy=latest&order=desc&postsPerPage=' + per_page + '&page=1'
rut_series = host + 'wp-api/v1/tops?postType=tvshows&range=day&orderBy=latest&order=desc&postsPerPage=' + per_page + '&page=1'
rut_animes = host + 'wp-api/v1/tops?postType=animes&range=day&orderBy=latest&order=desc&postsPerPage=' + per_page + '&page=1'

ten_movies = host + 'wp-api/v1/tops?postType=movies&range=week&orderBy=latest&order=desc&postsPerPage=' + per_page + '&page=1'
ten_series = host + 'wp-api/v1/tops?postType=tvshows&range=week&orderBy=latest&order=desc&postsPerPage=' + per_page + '&page=1'
ten_animes = host + 'wp-api/v1/tops?postType=animes&range=week&orderBy=latest&order=desc&postsPerPage=' + per_page + '&page=1'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_allpeliculasse_proxies', default=''):
        tit = '[COLOR %s][B]Quitar los proxies del canal[/B][/COLOR]' % color_list_proxies
        context.append({'title': tit, 'channel': item.channel, 'action': 'quitar_proxies'})

    tit = '[COLOR %s]Ajustes categoría proxies[/COLOR]' % color_exec
    context.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    return item.clone( title = '[B]Configurar proxies a usar ...[/B]', action = 'configurar_proxies', folder=False, context=context, plot=plot, text_color='red' )

def quitar_proxies(item):
    from modules import submnuctext
    submnuctext._quitar_proxies(item)
    return True

def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)


def do_downloadpage(url, post=None, headers=None):
    hay_proxies = False
    if config.get_setting('channel_allpeliculasse_proxies', default=''): hay_proxies = True

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('allpeliculasse', url, post=post, headers=headers).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers).data

        if not data:
            if not '?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('AllPeliculasSe', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('allpeliculasse', url, post=post, headers=headers, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='allpeliculasse', folder=False, text_color='chartreuse' ))

    itemlist.append(item_configurar_proxies(item))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title='Animes', action = 'mainlist_animes', text_color='springgreen' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = rut_movies, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Tendencias', action = 'list_all', url = ten_movies, search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por plataforma', action = 'productoras', search_type = 'movie', text_color='moccasin' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = rut_series, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Tendencias', action = 'list_all', url = ten_series, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por plataforma', action = 'productoras', search_type = 'tvshow', text_color='moccasin' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', tipo = 'Animes', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = rut_animes, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Tendencias', action = 'list_all', url = ten_animes, tipo = 'Animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', tipo = 'Animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', tipo = 'Animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', tipo = 'Animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por país', action = 'paises', tipo = 'Animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por plataforma', action = 'productoras', tipo = 'Animes', search_type = 'tvshow', text_color='moccasin' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       if item.tipo == 'Animes': text_color = 'springgreen'
       else: text_color = 'hotpink'

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'langs:(.*?)routes:')

    matches = scrapertools.find_multiple_matches(bloque, '"(.*?)":.*?"slug":"(.*?)".*?"tax":"lang"')

    for value, tit in matches:
        if item.search_type == 'movie':
            url = host + 'wp-api/v1/listing/any?filter={"langs":[' + value + ']}&orderBy=latest&order=desc&postType=movies&postsPerPage=' + per_page + '&page=1'
        else:
           if item.tipo == 'Animes':
	            url = host + 'wp-api/v1/listing/any?filter={"langs":[' + value + ']}&orderBy=latest&order=desc&postType=animes&postsPerPage=' + per_page + '&page=1'
           else:
                url = host + 'wp-api/v1/listing/any?filter={"langs":[' + value + ']}&orderBy=latest&order=desc&postType=tvshos&postsPerPage=' + per_page + '&page=1'

        tit = tit.capitalize()

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def calidades(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       if item.tipo == 'Animes': text_color = 'springgreen'
       else: text_color = 'hotpink'

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'qualities:(.*?)countries:')

    matches = scrapertools.find_multiple_matches(bloque, '"(.*?)":.*?"slug":"(.*?)".*?"tax":"quality"')

    for value, tit in matches:
        if item.search_type == 'movie':
            url = host + 'wp-api/v1/listing/any?filter={"qualities":[' + value + ']}&orderBy=latest&order=desc&postType=movies&postsPerPage=' + per_page + '&page=1'
        else:
           if item.tipo == 'Animes':
	            url = host + 'wp-api/v1/listing/any?filter={"qualities":[' + value + ']}&orderBy=latest&order=desc&postType=animes&postsPerPage=' + per_page + '&page=1'
           else:
                url = host + 'wp-api/v1/listing/any?filter={"qualities":[' + value + ']}&orderBy=latest&order=desc&postType=tvshos&postsPerPage=' + per_page + '&page=1'

        tit = tit.capitalize()

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       if item.tipo == 'Animes': text_color = 'springgreen'
       else: text_color = 'hotpink'

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'genres:(.*?)years:')

    matches = scrapertools.find_multiple_matches(bloque, '"(.*?)":.*?"slug":"(.*?)".*?"tax":"genres"')

    for value, tit in matches:
        if item.search_type == 'movie':
            url = host + 'wp-api/v1/listing/any?filter={"genres":[' + value + ']}&orderBy=latest&order=desc&postType=movies&postsPerPage=' + per_page + '&page=1'
        else:
           if item.tipo == 'Animes':
	            url = host + 'wp-api/v1/listing/any?filter={"genres":[' + value + ']}&orderBy=latest&order=desc&postType=animes&postsPerPage=' + per_page + '&page=1'
           else:
                url = host + 'wp-api/v1/listing/any?filter={"genres":[' + value + ']}&orderBy=latest&order=desc&postType=tvshos&postsPerPage=' + per_page + '&page=1'

        tit = tit.capitalize()

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'years:(.*?)qualities:')

    matches = scrapertools.find_multiple_matches(bloque, '"(.*?)":.*?"slug":"(.*?)".*?"tax":"years"')

    for value, anyo in matches:
        if item.search_type == 'movie':
           url = host + 'wp-api/v1/listing/any?filter={"years":[' + value + ']}&orderBy=latest&order=desc&postType=movies&postsPerPage=' + per_page + '&page=1'
        else:
           url = host + 'wp-api/v1/listing/any?filter={"years":[' + value + ']}&orderBy=latest&order=desc&postType=tvshows&postsPerPage=' + per_page + '&page=1'

        itemlist.append(item.clone( title = str(anyo), url = url, action = 'list_all', text_color = text_color))

    return sorted(itemlist, key=lambda x: x.title, reverse=True)


def paises(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       if item.tipo == 'Animes': text_color = 'springgreen'
       else: text_color = 'hotpink'

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'countries:(.*?)providers:')

    matches = scrapertools.find_multiple_matches(bloque, '"(.*?)":.*?"slug":"(.*?)".*?"tax":"country"')

    for value, tit in matches:
        if item.search_type == 'movie':
            url = host + 'wp-api/v1/listing/any?filter={"countries":[' + value + ']}&orderBy=latest&order=desc&postType=movies&postsPerPage=' + per_page + '&page=1'
        else:
           if item.tipo == 'Animes':
	            url = host + 'wp-api/v1/listing/any?filter={"countries":[' + value + ']}&orderBy=latest&order=desc&postType=animes&postsPerPage=' + per_page + '&page=1'
           else:
                url = host + 'wp-api/v1/listing/any?filter={"countries":[' + value + ']}&orderBy=latest&order=desc&postType=tvshos&postsPerPage=' + per_page + '&page=1'

        tit = tit.capitalize()

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def productoras(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       if item.tipo == 'Animes': text_color = 'springgreen'
       else: text_color = 'hotpink'

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'providers:(.*?)langs:')

    matches = scrapertools.find_multiple_matches(bloque, '"(.*?)":.*?"slug":"(.*?)".*?"tax":"providers"')

    for value, tit in matches:
        tit = tit.replace('-', ' ')

        if item.search_type == 'movie':
            url = host + 'wp-api/v1/listing/any?filter={"providers":[' + value + ']}&orderBy=latest&order=desc&postType=movies&postsPerPage=' + per_page + '&page=1'
        else:
           if item.tipo == 'Animes':
	            url = host + 'wp-api/v1/listing/any?filter={"providers":[' + value + ']}&orderBy=latest&order=desc&postType=animes&postsPerPage=' + per_page + '&page=1'
           else:
                url = host + 'wp-api/v1/listing/any?filter={"providers":[' + value + ']}&orderBy=latest&order=desc&postType=tvshos&postsPerPage=' + per_page + '&page=1'

        tit = tit.capitalize()

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    data = data.replace('}}}' ,',{"')

    matches = scrapertools.find_multiple_matches(str(data), '_id":(.*?),{"')

    num_matches = len(matches)

    for match in matches:
        match = match.replace('\\/', '/')

        url = scrapertools.find_single_match(match, '"slug":"(.*?)"')

        title = scrapertools.find_single_match(match, '"title":"(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, '"featured":"(.*?)"')

        year = scrapertools.find_single_match(match, '"release_date":"(.*?)-').strip()
        if not year: year = '-'

        if not year == '-':
            if ' (' in title: title = title.replace(' (' + year + ')', '').strip()
            elif ' [' in title: title = title.replace(' [' + year + ']', '').strip()

        title = clean_title(title)

        title = title.replace('&#8217;', "'").replace('&#038;', '&').replace('&#8211;', '').replace('&#8230;', ' ').strip()

        tipo = 'movie' if '"type":"movies"' in match else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            titulo = title

            if "La Película" in titulo: titulo = titulo.split("La Película")[0]
            if "La película" in title: titulo = titulo.split("La película")[0]

            url = host + 'peliculas/' + url

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, fmt_sufijo = sufijo,
                                        contentType = 'movie', contentTitle = titulo, infoLabels = {'year': year} ))

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            if item.tipo == 'Animes':
                if not '/animes/' in url: continue

                url = host + 'animes/' + url
            else:
                url = host + 'series/' + url

            itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo = sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if str(num_matches) == per_page:
            if '"next_page_url":' in data:
                ant_pag = scrapertools.find_single_match(item.url, '&page=(.*?)$')

                if ant_pag:
                    ant_url = scrapertools.find_single_match(item.url, '(.*?)&page=')

                    next_page = int(ant_pag)
                    next_page = next_page + 1

                    next_url = ant_url + '&page=' + str(next_page)

                    itemlist.append(item.clone( title='Siguientes ...', url=next_url, action='list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    _id = scrapertools.find_single_match(data, '<link rel="canonical".*?href=".*?&p=(.*?)"')

    if not _id: return itemlist

    url = host + 'wp-api/v1/single/episodes/list?_id=' +_id + '&season=1&postsPerPage=' + per_page + '&page=1'

    data = do_downloadpage(url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '"seasons":(.*?)"pagination":')

    seasons = re.compile('"(.*?)"', re.DOTALL).findall(bloque)

    for tempo in seasons:
        title = 'Temporada ' + tempo

        if len(seasons) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = tempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    _id = scrapertools.find_single_match(data, '<link rel="canonical".*?href=".*?&p=(.*?)"')

    if not _id: return itemlist

    url = host + 'wp-api/v1/single/episodes/list?_id=' +_id + '&season=' + str(item.contentSeason) + '&postsPerPage=' + per_page + '&page=1'

    data = do_downloadpage(url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    patron = '"_id":(.*?),.*?"title":"(.*?)",.*?"slug":"(.*?)".*?"still_path":"(.*?)".*?"episode_number":(.*?),'

    matches = re.compile(patron, re.DOTALL).findall(data)

    num_matches = len(matches)

    if item.page == 0 and item.perpage == 50:
        sum_parts = num_matches

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('AllPeliculasSe', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('AllPeliculasSe', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AllPeliculasSe', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AllPeliculasSe', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AllPeliculasSe', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AllPeliculasSe', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('AllPeliculasSe', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for _id, title, slug, thumb, epis in matches:
        epis = epis.replace(']', '').replace('}', '').strip()

        if not epis: epis = 1

        thumb = thumb.replace('\\/', '/')

        thumb = 'https://image.tmdb.org/t/p/w500/' + thumb

        url = host + 'wp-api/v1/player?postId=' + _id + '&demo=0'

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=epis ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    url = item.url

    if not '?postId=' in item.url:
        data = do_downloadpage(item.url)
        data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

        _id = scrapertools.find_single_match(data, '<link rel="canonical".*?href=".*?&p=(.*?)"')

        if not _id: return itemlist

        url = host + 'wp-api/v1/player?postId=' + _id + '&demo=0'

    data = do_downloadpage(url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('"url":"(.*?)".*?"server":"(.*?)".*?"lang":"(.*?)"(.*?)}', re.DOTALL).findall(data)

    ses = 0

    for url, srv, lng, rest in matches:
        ses += 1

        if '/1fichier.' in url: continue
        elif '/turbobit.' in url: continue

        elif '/fembed.' in url: continue

        elif '/cloudemb.' in url or '.fembed.' in url or '/fembad.' in url or 'vanfem' in url: continue
        elif '/tubesb.' in url or '/sbsonic.' in url or '/sbrapid.' in url or '/lvturbo.' in url or '/sbface.' in url or '/sbbrisk.' in url or '/sblona.' in url: continue

        lng = clean_title(lng)

        url = url.replace('\\/', '/')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)
        elif servidor == 'zures': other = servertools.corregir_zures(url)

        if 'Latino' in lng: lang = 'Lat'
        elif 'Castellano' in lng: lang = 'Esp'
        elif 'Subtitulado' in lng: lang = 'Vose'
        elif 'Latino/Inglés' in lng: lang = 'lat'
        elif 'inglés' in lng or 'ingles' in lng: lang = 'Ing'
        else: lang = '?'

        age = ''
        if '/acortalink.' in url:
            servidor = 'directo'

            age = srv.capitalize()

            if not age == 'Torrent':
                _raw = scrapertools.find_single_match(rest, '".*?"url_raw":"(.*?)"')

                if _raw:
                    _raw = _raw.replace('\\/', '/').replace('https://', '')

                    age = _raw

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url,
                              language = lang, other = other.capitalize(), age = age ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.url.endswith('.torrent'):
        if config.get_setting('proxies', item.channel, default=''):
            if PY3:
                from core import requeststools
                data = requeststools.read(item.url, 'allpeliculasse')
            else:
                data = do_downloadpage(item.url)

            if data:
                if '<h1>Not Found</h1>' in str(data) or '<!DOCTYPE html>' in str(data) or '<!DOCTYPE>' in str(data):
                    return 'Archivo [COLOR red]Inexistente[/COLOR]'

                file_local = os.path.join(config.get_data_path(), "temp.torrent")
                with open(file_local, 'wb') as f: f.write(data); f.close()

                itemlist.append(item.clone( url = file_local, server = 'torrent' ))
        else:
            itemlist.append(item.clone( url = item.url, server = 'torrent' ))

    else:
        if 'magnet' in item.other:
            itemlist.append(item.clone( url = item.url, server = 'torrent' ))
            return itemlist

        if item.server == 'directo':
            host_torrent = host[:-1]
            url_base64 = decrypters.decode_url_base64(item.url, host_torrent)

            if url_base64.startswith('magnet:'):
                itemlist.append(item.clone( url = url_base64, server = 'torrent' ))
                return itemlist

            elif url_base64.endswith(".torrent"):
               if config.get_setting('proxies', item.channel, default=''):
                   if PY3:
                       from core import requeststools
                       data = requeststools.read(url_base64, 'allpeliculasse')
                   else:
                       data = do_downloadpage(url_base64)

                   if data:
                       if '<h1>Not Found</h1>' in str(data) or '<!DOCTYPE html>' in str(data) or '<!DOCTYPE>' in str(data):
                           return 'Archivo [COLOR red]Inexistente[/COLOR]'

                       file_local = os.path.join(config.get_data_path(), "temp.torrent")
                       with open(file_local, 'wb') as f: f.write(data); f.close()

                       itemlist.append(item.clone( url = file_local, server = 'torrent' ))
               else:
                   itemlist.append(item.clone( url = url_base64, server = 'torrent' ))

               return itemlist

            else:
               if url_base64:
                   if '/1fichier.' in url_base64:
                       return 'Servidor [COLOR goldenrod]No soportado[/COLOR]'

                   elif '/turbobit.' in url_base64:
                       return 'Servidor [COLOR goldenrod]No soportado[/COLOR]'

                   new_server = servertools.get_server_from_url(url_base64)
                   new_server = servertools.corregir_other(new_server)				   

                   if not new_server == 'directo':
                       url = url_base64
                       item.server = new_server

    if url:
        if url.startswith("https://sb"):
            return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

        elif '/acortalink.' in url:
           return 'Tiene [COLOR plum]Acortador[/COLOR] del enlace'

        if item.server == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url, server = item.server))

    return itemlist


def clean_title(title):
    logger.info()

    title = title.replace('\\u00e1', 'a').replace('\\u00c1', 'a').replace('\\u00e9', 'e').replace('\\u00ed', 'i').replace('\\u00f3', 'o').replace('\\u00fa', 'u')
    title = title.replace('\\u00f1', 'ñ').replace('\\u00bf', '¿').replace('\\u00a1', '¡').replace('\\u00ba', 'º')
    title = title.replace('\\u00eda', 'a').replace('\\u00f3n', 'o').replace('\\u00fal', 'u').replace('\\u00e0', 'a')

    title = title.replace('\\u00da', 'u')

    title = title.replace('\\u2019', "'").replace('\\u00e3o', 'o').replace('\\u010c', 'c').replace('\\u00c9', 'v').replace('\\u00da', 't').replace('\\u0113', 'i').replace('\\u014d', 'v').replace('\\u00d4', '').replace('\\u0130', '').replace('\\u00e8', ' ')

    title = title.replace('\\u2019', "'").replace('\\u2126', 'Ω')

    return title


def search(item, texto):
    logger.info()
    try:
       if item.search_type == 'all':
           item.url = host + 'wp-api/v1/search?filter=[]&q=' + texto.replace(" ", "+") + '&orderBy=latest&order=desc&postType=any&postsPerPage=' + per_page + '&page=1'
       elif item.search_type == 'movie':
           item.url = host + 'wp-api/v1/search?filter=[]&q=' + texto.replace(" ", "+") + '&orderBy=latest&order=desc&postType=movies&postsPerPage=' + per_page + '&page=1'
       else:
          if item.tipo == 'Animes':
               item.url = host + 'wp-api/v1/search?filter=[]&q=' + texto.replace(" ", "+") + '&orderBy=latest&order=desc&postType=animes&postsPerPage=' + per_page + '&page=1'
          else:
               item.url = host + 'wp-api/v1/search?filter=[]&q=' + texto.replace(" ", "+") + '&orderBy=latest&order=desc&postType=tvshows&postsPerPage=' + per_page + '&page=1'

       return list_all(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []
