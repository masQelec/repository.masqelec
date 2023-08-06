# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.cuevana2.icu/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_cuevana2_proxies', default=''):
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


def do_downloadpage(url, post=None, headers=None, follow_redirects=True, only_headers=False, raise_weberror=True):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://ww2.cuevana2.biz/']

    for ant in ant_hosts:
        url = url.replace(ant, host)

    if not url.startswith(host):
        resp = httptools.downloadpage(url, post=post, headers=headers, follow_redirects=follow_redirects, only_headers=only_headers, raise_weberror=raise_weberror)
    else:
        resp = httptools.downloadpage_proxy('cuevana2', url, post=post, headers=headers, follow_redirects=follow_redirects, only_headers=only_headers, raise_weberror=raise_weberror)

    if '<title>You are being redirected...</title>' in resp.data:
        try:
            from lib import balandroresolver
            ck_name, ck_value = balandroresolver.get_sucuri_cookie(resp.data)
            if ck_name and ck_value:
                httptools.save_cookie(ck_name, ck_value, host.replace('https://', '')[:-1])

                if not url.startswith(host):
                    resp = httptools.downloadpage(url, post=post, headers=headers, follow_redirects=follow_redirects, only_headers=only_headers, raise_weberror=raise_weberror)
                else:
                    resp = httptools.downloadpage_proxy('cuevana2', url, post=post, headers=headers, follow_redirects=follow_redirects, only_headers=only_headers, raise_weberror=raise_weberror)
        except:
            pass

    if only_headers: return resp.headers

    return resp.data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='cuevana2', folder=False, text_color='chartreuse' ))

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'peliculas/estrenos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'peliculas/top/day', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'peliculas/top/week', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host + 'episodios', search_type = 'tvshow', text_color = 'olive' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'series/estrenos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'series/top/day', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'series/top/week', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist=[]

    generos = [
       'accion',
       'animacion',
       'aventura',
       'belica',
       'ciencia-ficcion',
       'comedia',
       'crimen',
       'documental',
       'drama',
       'familia',
       'fantasia',
       'historia',
       'misterio',
       'musica',
       'romance',
       'suspenso',
       'terror',
       'western'
       ]

    for genero in generos:
        url = host + 'genero/' + genero

        itemlist.append(item.clone( action = 'list_all', title = genero.capitalize(), url = url, text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = re.compile('publicadas(.*?)Top de la semana').findall(data)
    if not bloque: bloque = re.compile('Últimas(.*?)Top de la semana').findall(data)
    if not bloque: bloque = re.compile('Tendencias(.*?)Top de la semana').findall(data)
    if not bloque: bloque = re.compile('Género(.*?)Top de la semana').findall(data)
    if not bloque: bloque = re.compile('>Resultados de la búsqueda</span>(.*?)Top de la semana').findall(data)

    matches = re.compile('<article(.*?)</article>').findall(str(bloque))

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="(.*?)"')
        title = scrapertools.find_single_match(article, ' alt="(.*?)"').strip()

        if not url or not title: continue

        url = host[:-1] + url

        thumb = scrapertools.find_single_match(article, ' src="(.*?)"')
        thumb = host[:-1] + thumb

        year = scrapertools.find_single_match(article, '<span>(\d{4})</span>')
        if not year: year = '-'

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                                contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if 'current' in 'data':
            next_url = scrapertools.find_single_match(data, '<a class="page-link".*?current.*?href="(.*?)"')
        else:
            next_url = scrapertools.find_single_match(data, '<a class="page-link".*?href="(.*?)"')

        if next_url:
            if '/page/' in next_url:
               next_url = host[:-1] + next_url

               itemlist.append(item.clone( title='Siguientes ...', url=next_url, page=0, action='list_all', text_color='coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = re.compile('Últimos(.*?)Top de la semana').findall(data)

    matches = re.compile('<article(.*?)</article>').findall(str(bloque))

    for match in matches:
        title = scrapertools.find_single_match(match, ' alt="(.*?)"').strip()

        url = scrapertools.find_single_match(match, ' href="([^"]+)"')

        url = host[:-1] + url

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')
        thumb = host[:-1] + thumb

        temp_epis = scrapertools.find_single_match(match, '</h2></a><span>(.*?)</span>')
        temp_epis = temp_epis.replace('<!-- -->', '')

        season = scrapertools.find_single_match(temp_epis, '(.*?)x')
        episode = scrapertools.find_single_match(temp_epis, '.*?x(.*?)$')

        name = title.replace(temp_epis, '').strip() 

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentSerieName=name, contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if 'current' in 'data':
            next_url = scrapertools.find_single_match(data, '<a class="page-link".*?current.*?href="(.*?)"')
        else:
            next_url = scrapertools.find_single_match(data, '<a class="page-link".*?href="(.*?)"')

        if next_url:
            if '/page/' in next_url:
               next_url = host[:-1] + next_url
               itemlist.append(item.clone( title="Siguientes ...", action="last_epis", url = next_url, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    temporadas = re.compile('<option value="(.*?)"', re.DOTALL).findall(data)

    for tempo in temporadas:
        title = 'Temporada ' + tempo

        if len(temporadas) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = tempo, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(str(data), '"post":(.*?)$')

    patron = '"image":"(.*?)".*?"season":"(.*?)".*?"episode":"(.*?)"'

    i = 0

    matches = re.compile(patron, re.DOTALL).findall(str(bloque))

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('Cuevana2', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana2', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana2', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana2', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana2', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('Cuevana2', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for thumb, season, epis, in matches[item.page * item.perpage:]:
        i += 1

        if not season == str(item.contentSeason):
           i = i - 1
           continue

        url = item.url.replace('/serie/', '/episodio/')

        url = url + '-' + season + 'x' + epis

        titulo = season + 'x' + epis + ' ' + item.contentSerieName

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail=thumb, contentType = 'episode', contentSeason = season, contentEpisodeNumber=epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if i > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if not '"players":' in data: return itemlist

    block = scrapertools.find_single_match(data, '"players":(.*?)$')

    ses = 0

    if '"latino":' in str(block):
        bloque = scrapertools.find_single_match(str(block), '"latino":(.*?)]')

        matches = re.compile('"cyberlocker":"(.*?)","result":"(.*?)","quality":"(.*?)"', re.DOTALL).findall(str(bloque))

        for srv, link, qlty in matches:
            ses += 1

            srv = srv.lower().strip()

            if srv == 'hqq' or srv == 'waaw' or srv == 'netu': continue

            itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', url = link, quality = qlty, language = 'Lat', other = srv ))


    if '"spanish":' in str(block):
        bloque = scrapertools.find_single_match(str(block), '"spanish":(.*?)]')

        matches = re.compile('"cyberlocker":"(.*?)","result":"(.*?)","quality":"(.*?)"', re.DOTALL).findall(str(bloque))

        for srv, link, qlty in matches:
            ses += 1

            srv = srv.lower().strip()

            if srv == 'hqq' or srv == 'waaw' or srv == 'netu': continue

            itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', url = link, quality = qlty, language = 'Esp', other = srv ))

    if '"english":' in str(block):
        bloque = scrapertools.find_single_match(str(block), '"english":(.*?)]')

        matches = re.compile('"cyberlocker":"(.*?)","result":"(.*?)","quality":"(.*?)"', re.DOTALL).findall(str(bloque))

        for srv, link, qlty in matches:
            ses += 1

            srv = srv.lower().strip()

            if srv == 'hqq' or srv == 'waaw' or srv == 'netu': continue

            itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', url = link, quality = qlty, language = 'Vose', other = srv ))

    # ~ Descargas
    if '"downloads":' in str(block):
        bloque = scrapertools.find_single_match(str(block), '"downloads":(.*?)]')

        matches = re.compile('"cyberlocker":"(.*?)","result":"(.*?)","quality":"(.*?)","language":"(.*?)"', re.DOTALL).findall(str(bloque))

        for srv, link, qlty, lang in matches:
            ses += 1

            srv = srv.lower().strip()

            if srv == '1fichier': continue

            if lang == 'Latino': lang = 'Lat'
            elif lang == 'Español': lang = 'Esp'
            elif lang == 'Subtitulado': lang = 'Vose'
            else: lang = '?'

            itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', url = link, quality = qlty, language = lang, other = srv + ' D'))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    data = do_downloadpage(item.url)

    new_url = scrapertools.find_single_match(data, "var url = '(.*?)'")
    if not new_url: new_url = scrapertools.find_single_match(data, 'let url = "(.*?)"')

    if new_url: url = new_url

    if '/cinestart.streams3.com/' in url: url = ''
    elif '/player.php?' in url: url = ''

    if url:

        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'zplayer': url = url + '|' + host

        itemlist.append(item.clone( url = url, server = servidor ))

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

