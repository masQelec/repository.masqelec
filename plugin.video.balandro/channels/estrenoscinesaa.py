# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://www.estrenoscinesaa.com/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_estrenoscinesaa_proxies', default=''):
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


def do_downloadpage(url):
    hay_proxies = False
    if config.get_setting('channel_estrenoscinesaa_proxies', default=''): hay_proxies = True

    if not url.startswith(host):
        data = httptools.downloadpage(url).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('estrenoscinesaa', url).data
        else:
            data = httptools.downloadpage(url).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='estrenoscinesaa', folder=False, text_color='chartreuse' ))

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

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'movies/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'DC Comics', action = 'list_all', url = host + 'genre/d-c/', search_type = 'movie', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'Netflix', action = 'list_all', url = host + 'genre/netflix/', search_type = 'movie', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'Marvel', action = 'list_all', url = host + 'genre/marvel/', search_type = 'movie', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'Star wars', action = 'list_all', url = host + 'genre/starwars/', search_type = 'movie', text_color='moccasin' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'tvshows/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por plataforma', action = 'plataformas', search_type = 'tvshow', text_color='moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '<ul class="genres(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)">(.*?)</a>')

    for url, title in matches:
        title = title.replace('&amp;', '&')

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = text_color ))

    return itemlist


def plataformas(item):
    logger.info()
    itemlist = []

    productoras = [
        ('amazon', 'Amazon'),
        ('apple-tv', 'Apple TV'),
        ('cbs-all-access', 'Cbs'),
        ('dc-universe', 'DC Universe'),
        ('disney', 'Disney+'),
        ('epix', 'Epix'),
        ('fox', 'FOX'),
        ('hbo', 'HBO'),
        ('hbo-max', 'HBO Max'),
        ('hulu', 'Hulu'),
        ('mgm', 'Mgm+'),
        ('netflix', 'Netflix'),
        ('showtime', 'Showtime')
        ]

    for opc, tit in productoras:
        url = host + 'network/' + opc + '/'

        itemlist.append(item.clone( title = tit, action = 'list_all', url = url, text_color = 'moccasin' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    hasta_data = '<div class="pagination">' if '<div class="pagination">' in data else '<nav class="genres">'

    bloque = scrapertools.find_single_match(data, '<h2>Añadido recientemente(.*?)' + hasta_data)
    if not bloque: bloque = scrapertools.find_single_match(data, '<h2>Añadido recientemente(.*?)$')

    matches = scrapertools.find_multiple_matches(bloque, '<article id="post-(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="([^"]+)')
        title = scrapertools.find_single_match(match, ' alt="([^"]+)').strip()

        if not url or not title: continue

        title = title.replace('&#8211;', '').replace('&#8217;', '').replace('&#038;', '&')

        thumb = scrapertools.find_single_match(match, ' src="([^"]+)')

        year = scrapertools.find_single_match(match, '<span>(\d{4})</span>')
        if not year: year = '-'

        plot = scrapertools.htmlclean(scrapertools.find_single_match(match, '<div class="texto">(.*?)</div>'))

        tipo = 'tvshow' if '/tvshows/' in url else 'movie'

        if tipo == 'movie':
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, 
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year, 'plot': plot} ))

        if tipo == 'tvshow':
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<span class="current".*?' + "<a href='(.*?)'")

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone (url = next_page, title = 'Siguientes ...', action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    temporadas = re.compile("<span class='title'>Temporada(.*?)<i>", re.DOTALL).findall(data)

    for tempo in temporadas:
        tempo = tempo.strip()

        title = 'Temporada ' + tempo

        if len(temporadas) == 1:
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

    bloque = scrapertools.find_single_match(data, "<span class='se-t.*?'>" + str(item.contentSeason) + '</span>(.*?)</ul>')

    patron = "<li class='mark-.*?<img src='(.*?)'.*?<div class='numerando'>(.*?)</div>.*?href='(.*?)'.*?>(.*?)</a>"

    matches = re.compile(patron, re.DOTALL).findall(bloque)

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
                platformtools.dialog_notification('EstrenosCinesaA', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('EstrenosCinesaA', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EstrenosCinesaA', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EstrenosCinesaA', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EstrenosCinesaA', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EstrenosCinesaA', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('EstrenosCinesaA', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for thumb, temp_epis, url, title in matches:
        epis = scrapertools.find_single_match(temp_epis, '-(.*?)$').strip()

        if not epis: epis = 1

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

    data = do_downloadpage(item.url)

    ses = 0

    matches = scrapertools.find_multiple_matches(data, "(?i)<div class='pframe'><iframe.*?src=(?:'|\")([^'\"]+)")

    for url in matches:
        ses += 1

        if 'youtube.com' in url: continue

        elif '/mirrorace.' in url: continue

        elif '.fivemanage.' in url: continue

        servidor = servertools.get_server_from_url(url)

        if servidor:
            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                  language = 'Esp', other = other ))

    # Descarga
    bloque = scrapertools.find_single_match(data, "<div id='download'(.*?)</table></div></div></div>")

    matches = scrapertools.find_multiple_matches(bloque, "<tr id='link-[^']+'>(.*?)</tr>")

    for enlace in matches:
        ses += 1

        url = scrapertools.find_single_match(enlace, " href='([^']+)")

        servidor = scrapertools.find_single_match(enlace, "domain=(?:www.|dl.|)([^'.]+)")

        if 'up-4ever' in servidor: continue
        elif 'mirrorace' in servidor: continue
        elif '1fichier' in servidor: continue

        other = ''
        age = ''

        if servidor == 'qiwi': other = 'Qiwi'
        elif servidor == 'drop':
              other = 'Drop'
              age = 'Captcha'

        servidor = servertools.corregir_servidor(servidor)

        if not url or not servidor: continue

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                              language = 'Esp', quality = 'HD' , other = 'd' + ' ' + other, age = age ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if host in item.url:
        data = do_downloadpage(item.url)

        url = scrapertools.find_single_match(data, '<a id="link".*?href="([^"]+)')
        if not url:
            data = str(data).replace('=\\', '=').replace('\\"', '/"')

            url = scrapertools.find_single_match(data, '<IFRAME SRC="(.*?)"')
            if not url: url = scrapertools.find_single_match(data, '<iframe src="(.*?)"')

        if url:
            servidor = servertools.get_server_from_url(url)

            if servidor == 'directo':
                new_server = servertools.corregir_other(url).lower()
                if new_server.startswith("http"):
                    if not config.get_setting('developer_mode', default=False): return itemlist
                servidor = new_server

            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

    else:
        servidor = servertools.get_server_from_url(item.url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(item.url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        if servidor:
            if 'streamsb' in item.url or 'playersb' in item.url:
                return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

            elif 'openload' in item.url or 'streamango' in item.url or 'vidlox' in item.url or 'jetload' in item.url or 'verystream' in item.url or 'streamcherry' in item.url or 'gounlimited' in item.url or 'streamix' in item.url or 'viewsb' in item.url or 'flix555' in item.url or '.stormo.' in item.url or '.spruto.' in item.url or '/biter.' in item.url or '/streamin.' in item.url or '/filebebo.' in item.url or '/streamcloud.' in item.url or '/videofiles.' in item.url or '/kingvid.' in item.url or '/allvid.' in item.url or '/goo.' in item.url:
                 return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

            elif '/powv1deo.' in item.url or '/powvibeo.' in item.url or '/pouvideo.' in item.url or '/povw1deo.' in item.url or '/powvldeo.' in item.url or '/pomvideo.' in item.url or '/streamp1ay.' in item.url or '/slreamplay.' in item.url or '/stemplay.' in item.url or '/steamplay.' in item.url:
                 return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

            elif '.rapidvideo.' in item.url or '.filefactory.' in item.url or '.owndrives.' in item.url or '/rapidcloud.' in item.url or '/ul.' in item.url or '/fileflares.' in item.url or '/rockfile.' in item.url or '/estream.' in item.url or '/uploadrocket.' in item.url or '/uploading.' in item.url or '/ddownload.' in item.url or '/uploadz.' in item.url or '/fikper.' in item.url or '/www.datafile.' in item.url or '/filerice.' in item.url or '/thevideo.' in item.url:
                return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

            elif '.fembed.' in item.url:
                return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

            elif 'jetload.' in item.url:
                return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

            elif '.up-4ever'in item.url:
                return 'Servidor [COLOR red]No Soportado[/COLOR]'

            if '.fivemanage.' in item.url:
                if item.url.startswith("//"): item.url = 'https:' + item.url
                servidor = 'directo'

            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, item.url)

    if url:
        if '.fivemanage.' in url: url = ''

    if url:
        itemlist.append(item.clone( url = url, server = servidor ))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<article>(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="([^"]+)')
        title = scrapertools.find_single_match(match, ' alt="([^"]+)').strip()

        if not url or not title: continue

        title = title.replace('&#8211;', '').replace('&#8217;', '').replace('&#038;', '&')

        thumb = scrapertools.find_single_match(match, ' src="([^"]+)')

        year = scrapertools.find_single_match(match, '<span class="year">(\d{4})</span>')
        if not year: year = '-'

        plot = scrapertools.htmlclean(scrapertools.find_single_match(match, '<div class="contenido"><p>(.*?)<p></div>'))

        tipo = 'tvshow' if '/tvshows/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, fmt_sufijo = sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year, 'plot': plot} ))

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo = sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<span class="current".*?' + "<a href='(.*?)'")

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone (url = next_page, title = 'Siguientes ...', action = 'list_search', text_color='coral' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

