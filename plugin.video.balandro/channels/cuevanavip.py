# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://vip.cuevana3.one/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_cuevanavip_proxies', default=''):
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
    if config.get_setting('channel_cuevanavip_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('cuevanavip', url, post=post, headers=headers, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if not data:
            if not '/?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('CuevanaVip', '[COLOR cyan]Re-Intentando acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('cuevanavip', url, post=post, headers=headers, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='cuevanavip', folder=False, text_color='chartreuse' ))

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '<ul class="sub-menu">(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)">(.*?)</a>')

    for url, title in matches:
        if not '/category/' in url: continue

        title = title.replace('Series de ', '').replace('&#038;', '&').replace('&amp;', '&').strip()

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = 'deepskyblue' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1939, -1):
        url = host + 'release/' + str(x)

        itemlist.append(item.clone( title=str(x), url=url, action='list_all', text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '</h1>(.*?)>Filtrar por idioma<')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        title =  scrapertools.find_single_match(match, '<h2 class="entry-title">(.*?)</h2>').strip()

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if not title or not url: continue

        langs = []
        if '/idioma-espanol-espana.png' in match.lower(): langs.append('Esp')
        if '/idioma-espanol-latino.png' in match.lower(): langs.append('Lat')
        if '/idioma-subtitulado.png' in match.lower(): langs.append('Vose')

        thumb = scrapertools.find_single_match(match, 'data-lazy-src="(.*?)"')

        title = title.replace('&#8217;s', "'s").replace('&#039;', "'").replace('&#038;', '&').replace('&amp;', '&').strip()

        year = scrapertools.find_single_match(match, '<span class="year">(.*?)</span>')
        if not year: year = '-'

        tipo = 'movie' if '/movie/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, languages=', '.join(langs), fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, languages=', '.join(langs), fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<div class="nav-links">.*?<a class="page-link current".*?<a class="page-link".*?href="(.*?)".*?</main>')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', action='list_all', url = next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, 'data-season="(.*?)"')

    for season in matches:
        season = season.strip()

        title = 'Temporada ' + season

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

                item.page = 0
                item.contentType = 'season'
                item.contentSeason = season
                itemlist = episodios(item)
                return itemlist


        itemlist.append(item.clone( action = 'episodios', title = title, page = 0,
                                    contentType = 'season', contentSeason = season, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    d_post = scrapertools.find_single_match(data, 'data-post="(.*?)"')

    if not d_post: return itemlist

    post = {'action': 'action_select_season', 'season': str(item.contentSeason), 'post': d_post}

    data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = post)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('CuevanaVip', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('CuevanaVip', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CuevanaVip', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CuevanaVip', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CuevanaVip', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('CuevanaVip', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('CuevanaVip', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if not url: continue

        title = scrapertools.find_single_match(match, '<h2 class="entry-title">.*?">(.*?)</h2>')

        epis = scrapertools.find_single_match(match, '<span class="num-epi">.*?x(.*?)</span>')

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb,
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

    data = data.replace('<iframe data-src="&lt;iframe src=&quot;', '<iframe data-src="').replace('&quot; ', '"')
 
    opts1 = scrapertools.find_multiple_matches(data, '<iframe src="(.*?)"')
    opts2 = scrapertools.find_multiple_matches(data, '<iframe data-src="(.*?)"')

    options = opts1 + opts2

    ses = 0

    for url in options:
        ses += 1

        if '/links.' in url:
            data1 = do_downloadpage(url)

            links1 = scrapertools.find_multiple_matches(str(data1), '<li onclick="go_to_player' + ".*?'(.*?)'")
            links2 = scrapertools.find_multiple_matches(str(data1), '<a href="(.*?)"')

            links = links1 + links2

            for _url in links:
                if '/ul.' in _url: continue
                elif '/1fichier.' in _url: continue
                elif '/rapidgator' in _url: continue
                elif '/katfile' in _url: continue
                elif '/nitro' in _url: continue
                elif '/filecrypt.' in _url: continue
                elif '/filepv.' in _url: continue
                elif '/ddownload.' in _url: continue

                elif '/multiup.' in _url: continue
                elif '/filemirage.' in _url: continue

                elif '/powvideo.' in _url: continue
                elif '/streamplay.' in _url: continue

                elif '/viewsb.' in _url: continue
                elif '/www.fembed.' in _url: continue
                elif '/fembed.' in _url: continue

                lang = '?'
                if '#idioma=lat' in _url: lang = 'Lat'
                elif '#lang=lat' in _url: lang = 'Lat'
                elif '#idioma=LAT' in _url: lang = 'Lat'
                elif '#lang=LAT' in _url: lang = 'Lat'

                elif '#idioma=cas' in _url: lang = 'Esp'
                elif '#lang=cas' in _url: lang = 'Esp'
                elif '#idioma=ESP' in _url: lang = 'Esp'
                elif '#lang=ESP' in _url: lang = 'Esp'

                elif '#idioma=vos' in _url: lang = 'Vose'
                elif '#lang=vos' in _url: lang = 'Vose'
                elif '#idioma=VOS' in _url: lang = 'Vose'
                elif '#lang=VOS' in _url: lang = 'Vose'

                elif '#idioma=sub' in _url: lang = 'Vose'
                elif '#lang=sub' in _url: lang = 'Vose'
                elif '#idioma=SUB' in _url: lang = 'Vose'
                elif '#lang=SUB' in _url: lang = 'Vose'

                if lang == '?':
                    lng = scrapertools.find_single_match(str(data1), "'" + _url + "'" + '.*?<p>(.*?)</p>')
                    if 'Latino' in lng: lang = 'Lat'
                    elif 'Castellano' in lng: lang = 'Esp'
                    elif 'Subtitulado' in lng: lang = 'Vose'

                if lang == '?':
                    if item.languages == 'Lat': lang = 'Lat'
                    elif item.languages == 'Esp': lang = 'Esp'
                    elif item.languages == 'Vose': lang = 'Vose'

                if '#idioma' in _url: _url = _url.split("#idioma")[0]
                elif '#lang=' in _url: _url = _url.split("#lang=")[0]

                if '/waaw.in/' in _url: _url = _url.replace('/waaw.in/', '/waaw.to/')

                elif '/player.cuevana.ac/' in _url: _url = _url.replace('/player.cuevana.ac/', '/waaw.to/')
                elif '/player.cuevana3.ac/' in _url: _url = _url.replace('/player.cuevana.ac/', '/waaw.to/')
                elif '/player.cuevana.one/' in _url: _url = _url.replace('/player.cuevana3.one/', '/waaw.to/')
                elif '/player.cuevana3.one/' in _url: _url = _url.replace('/player.cuevana3.one/', '/waaw.to/')

                servidor = servertools.get_server_from_url(_url)

                if servertools.is_server_available(servidor):
                    if not servertools.is_server_enabled(servidor): continue
                else:
                    if not config.get_setting('developer_mode', default=False): continue

                other = ''
                if servidor == 'various': other = servertools.corregir_other(_url)
                elif servidor == 'zures': other = servertools.corregir_zures(_url)

                if servidor == 'directo':
                    if '/vidnest.' in _url:
                        servidor = 'Zures'
                        other = 'Vidnest'

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = _url,
                                      language = lang, other = other ))

            continue

        if '/ul.' in url: continue
        elif '/1fichier.' in url: continue
        elif '/rapidgator' in url: continue
        elif '/katfile' in url: continue
        elif '/nitro' in url: continue
        elif '/filecrypt.' in url: continue
        elif '/filepv.' in url: continue
        elif '/ddownload.' in url: continue

        elif '/multiup.' in url: continue
        elif '/filemirage.' in url: continue

        elif '/powvideo.' in url: continue
        elif '/streamplay.' in url: continue

        elif '/viewsb.' in url: continue
        elif '/www.fembed.' in url: continue
        elif '/fembed.' in url: continue

        lang = '?'
        if '#idioma=lat' in url: lang = 'Lat'
        elif '#lang=lat' in url: lang = 'Lat'
        elif '#idioma=LAT' in url: lang = 'Lat'
        elif '#lang=LAT' in url: lang = 'Lat'

        elif '#idioma=cas' in url: lang = 'Esp'
        elif '#lang=cas' in url: lang = 'Esp'
        elif '#idioma=ESP' in url: lang = 'Esp'
        elif '#lang=ESP' in url: lang = 'Esp'

        elif '#idioma=vos' in url: lang = 'Vose'
        elif '#lang=vos' in url: lang = 'Vose'
        elif '#idioma=VOS' in url: lang = 'Vose'
        elif '#lang=VOS' in url: lang = 'Vose'

        elif '#idioma=sub' in url: lang = 'Vose'
        elif '#lang=sub' in url: lang = 'Vose'
        elif '#idioma=SUB' in url: lang = 'Vose'
        elif '#lang=SUB' in url: lang = 'Vose'

        if lang == '?':
            lng = scrapertools.find_single_match(str(data), "'" + url + "'" + '.*?<p>(.*?)</p>')
            if 'Latino' in lng: lang = 'Lat'
            elif 'Castellano' in lng: lang = 'Esp'
            elif 'Subtitulado' in lng: lang = 'Vose'

        if lang == '?':
            if item.languages == 'Lat': lang = 'Lat'
            elif item.languages == 'Esp': lang = 'Esp'
            elif item.languages == 'Vose': lang = 'Vose'

        if '#idioma' in url: url = url.split("#idioma")[0]
        elif '#lang=' in url: url = url.split("#lang=")[0]

        if '/waaw.in/' in url: url = url.replace('/waaw.in/', '/waaw.to/')

        elif '/player.cuevana.ac/' in url: url = url.replace('/player.cuevana.ac/', '/waaw.to/')
        elif '/player.cuevana3.ac/' in url: url = url.replace('/player.cuevana.ac/', '/waaw.to/')
        elif '/player.cuevana.one/' in url: url = url.replace('/player.cuevana3.one/', '/waaw.to/')
        elif '/player.cuevana3.one/' in url: url = url.replace('/player.cuevana3.one/', '/waaw.to/')

        servidor = servertools.get_server_from_url(url)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)
        elif servidor == 'zures': other = servertools.corregir_zures(url)

        if servidor == 'directo':
            if '/vidnest.' in url:
                servidor = 'Zures'
                other = 'Vidnest'

        itemlist.append(Item(channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                             language = lang, other=other ))

    # ~ Downloads No se tratan

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    item.url = item.url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

    url_play = item.url

    data = do_downloadpage(item.url)

    new_url = scrapertools.find_single_match(data, '<div class="Video">.*?src="(.*?)"')

    if new_url:
        new_url = new_url.replace('/player.cuevana.ac/', '/waaw.to/').replace('/player.cuevana3.one/', '/waaw.to/')

        url_play = new_url

    if url_play:
        servidor = servertools.get_server_from_url(url_play)

        url_play = servertools.normalize_url(servidor, url_play)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url_play).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url_play, server = servidor))

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
