# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True


import os, re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www2.pelisyseries.net/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_pelisyseries_proxies', default=''):
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


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/lanzamiento/' in url: raise_weberror = False

    hay_proxies = False
    if config.get_setting('channel_pelisyseries_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if config.get_setting('channel_pelisyseries_proxies', default=''): timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('pelisyseries', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

        if not data:
            if not '?s=' in url:
                platformtools.dialog_notification('PelisySeries', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')
                data = httptools.downloadpage_proxy('pelisyseries', url, post=post, headers=header, sraise_weberror=raise_weberror, timeout=timeout).data

    if '<title>You are being redirected...</title>' in data or '<title>Just a moment...</title>' in data:
        if not url.startswith(host):
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('pelisyseries', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    if '<title>Just a moment...</title>' in data:
        if not '?s=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='pelisyseries', folder=False, text_color='chartreuse' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_pelisyseries', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('pelisyseries') ))

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

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'tendencias/?get=movies', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'ratings/?get=movies', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'tendencias/?get=tv', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'ratings/?get=tv', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por plataforma', action = 'plataformas', search_type = 'tvshow', text_color='moccasin' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Castellano', action = 'list_all', url = host + 'tag/castellano/', text_color='deepskyblue' ))
    itemlist.append(item.clone( title = 'Latino', action = 'list_all', url = host + 'tag/latino/', text_color='deepskyblue' ))
    itemlist.append(item.clone( title = 'Subtitulado', action = 'list_all', url = host + 'tag/vose/', text_color='deepskyblue' ))

    return itemlist


def plataformas(item):
    logger.info()
    itemlist = []

    text_color = 'hotpink'

    itemlist.append(item.clone( title = 'Amazon prime vídeo', action = 'list_all', url = host + 'network/amazon/', text_color = text_color ))
    itemlist.append(item.clone( title = 'Antena 3', action = 'list_all', url = host + 'network/antena-3/', text_color = text_color))
    itemlist.append(item.clone( title = 'Channel 4', action = 'list_all', url = host + 'network/channel-4/', text_color = text_color ))
    itemlist.append(item.clone( title = 'Disney+', action = 'list_all', url = host + 'network/amazon/', text_color = text_color ))
    itemlist.append(item.clone( title = 'Hbo Max', action = 'list_all', url = host + 'network/hbo/', text_color = text_color ))
    itemlist.append(item.clone( title = 'Netflix', action = 'list_all', url = host + 'network/netflix/', text_color = text_color ))
    itemlist.append(item.clone( title = 'Telecinco', action = 'list_all', url = host + 'network/telecinco/', text_color = text_color ))
    itemlist.append(item.clone( title = 'Telefe', action = 'list_all', url = host + 'network/telefe/', text_color = text_color ))

    return itemlist


def calidades(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'por Calidad<(.*?)por País<')

    patron = 'href="(.*?)">(.*?)</a>'

    matches = re.compile(patron).findall(bloque)

    for url, title in matches:
        itemlist.append(item.clone( title = title.capitalize(), action = 'list_all', url = url, text_color = 'deepskyblue' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'por Género<(.*?)por Calidad<')

    patron = 'href="(.*?)">(.*?)</a>'

    matches = re.compile(patron).findall(bloque)

    for url, title in matches:
        if config.get_setting('descartar_xxx', default=False):
            if title == 'Eróticas': continue

        itemlist.append(item.clone( title = title.capitalize(), action = 'list_all', url = url, text_color = text_color ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'por País<(.*?)por Año<')

    patron = 'href="(.*?)">(.*?)</a>'

    matches = re.compile(patron).findall(bloque)

    for url, title in matches:
        itemlist.append(item.clone( title = title.capitalize(), action = 'list_all', url = url, text_color = 'deepskyblue' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1927, -1):
        itemlist.append(item.clone( title = str(x), url = host + 'lanzamiento/' + str(x) + '/', action = 'list_all', text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if '>Añadido recientemente<' in data: bloque = scrapertools.find_single_match(data, '>Añadido recientemente<(.*?)>Año de lanzamiento<')
    elif '<h1>' in data: bloque = scrapertools.find_single_match(data, '</h1>(.*?)>Año de lanzamiento<')
    elif '<h2>' in data: bloque = scrapertools.find_single_match(data, '</h2>(.*?)>Año de lanzamiento<')
    else: bloque = data

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        title = title.replace('&#038;', '&').replace('&#8217;s', "'s").replace('&#8211;', '').replace('&#8217;', '')

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        year = scrapertools.find_single_match(match, '</h3>.*?<span>.*?,(.*?)</span>').strip()
        if not year: year = scrapertools.find_single_match(match, '</h3><span>(.*?)</span>')

        if not year: year = '-'
        else: title = title.replace('(' + year + ')', '').strip()

        qlty = scrapertools.find_single_match(match, '<span class="quality">(.*?)</span>')

        if '/peliculas/' in url:
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, qualities=qlty, contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        else:
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_url = scrapertools.find_single_match(data, '<span class="current">' + ".*?<a href='(.*?)'")

        if next_url:
            itemlist.append(item.clone( title = 'Siguientes ...', url = next_url, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    temporadas = re.compile("<span class='se-t.*?'>(.*?)</span>", re.DOTALL).findall(data)

    for tempo in temporadas:
        title = 'Temporada ' + tempo

        if len(temporadas) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, contentType = 'season', contentSeason = tempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if '/seasons/' in item.url: bloque = data
    else: bloque = scrapertools.find_single_match(data, "<span class='se-t.*?'>" + str(item.contentSeason) + "</span>(.*?)</div></div>")

    patron = "<li class='mark-.*?src='(.*?)'.*?<div class='numerando'>(.*?)</div>.*?<a href='(.*?)'>(.*?)</a>"

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
                platformtools.dialog_notification('Cuevana3Pro', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('Cuevana3Pro', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PelisySeries', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PelisySeries', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]100[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PelisySeries', '[COLOR cyan]Cargando 100 elementos[/COLOR]')
                    item.perpage = 100

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana3Pro', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('PelisySeries', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts

    for thumb, s_e, url, title in matches[item.page * item.perpage:]:
        episode = scrapertools.find_single_match(s_e, ".*? - (.*?)$")

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

        titulo = str(item.contentSeason) + 'x' + str(episode) + ' ' + title

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        if 'Epis.' in titulo: titulo = titulo + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = episode ))

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
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    ses = 0

    # Descargas
    matches = scrapertools.find_multiple_matches(data, "<tr id='link-(.*?)</tr>")

    for match in matches:
        ses += 1

        srv = scrapertools.find_single_match(match, ".*?domain=(.*?)'")

        srv = normalize_server(srv)

        if not srv: continue

        servidor = srv

        size = ''

        if servidor == 'waaw' or servidor == 'hqq' or servidor == 'netu': servidor = 'waaw'

        elif servidor == 'ok': servidor = 'okru'
        elif servidor == 'dood': servidor = 'doodstream'
        elif servidor == 'uptostream': servidor = 'uptobox'
        elif servidor == 'archive': servidor = 'archiveorg'
        elif servidor == 'zto': servidor = 'zembed'
        elif servidor == 'player.vimeo': servidor = 'vimeo'

        elif servidor == 'utorrent':
            servidor = 'torrent'
            size = scrapertools.find_single_match(match, "</strong>.*?</td><td>.*?</td><td>(.*?)</td>")

        qlty = scrapertools.find_single_match(match, "<strong class='quality'>(.*?)</strong>")

        if qlty == 'Subtitulos': continue

        lang = scrapertools.find_single_match(match, "</strong>.*?</td><td>(.*?)</td>")

        if 'Latino' in lang: lang = 'Lat'
        elif 'Castellano' in lang or 'Español' in lang: lang = 'Esp'
        elif 'Subtitulado' in lang or 'VOSE' in lang: lang = 'Vose'
        else: lang = '?'

        url = scrapertools.find_single_match(match, "<a href='(.*?)'")

        age = ''
        if servidor == 'torrent': age = 'Magnet'

        quality_num = puntuar_calidad(qlty)

        itemlist.append(Item( channel = item.channel, action = 'play', url = url, server = servidor, title = '',
                              language = lang, quality = qlty, quality_num = quality_num, other = size, age = age ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def normalize_server(server):
    server = server.lower()

    server = server.replace('.com', '').replace('.co', '').replace('.cc', '').replace('.ru', '').replace('.tv', '').replace('.to', '').replace('.me', '').replace('.nz', '').replace('.vg', '').replace('.io', '').replace('.eu', '').replace('.ac', '')

    server = server.replace('.org', '').replace('.net', '').replace('.club', '').replace('.site', '').replace('.watch', '').replace('.life', '').replace('.biz', '').replace('.fun', '').replace('.xyz', '').replace('.host', '').strip()

    if 'pelisyseries' in server: server = ''

    elif 'hydrax' in server: server = ''
    elif 'videohost' in server: server = ''
    elif 'vidto-do' in server: server = ''
    elif 'videomega' in server: server = ''
    elif 'gdriveplayer' in server: server = ''
    elif 'dfiles' in server: server = ''
    elif 'embed.mystream' in server: server = ''
    elif 'storage.googleapis' in server: server = ''
    elif 'goo.gl' in server: server = ''
    elif 'jwplayerembed' in server: server = ''
    elif 'vev.io' in server: server = ''
    elif 'pelispng.online' in server: server = ''
    elif 'verlapeliculaonline28.blogspot' in server: server = ''
    elif 'steamplay' in server or 'streamp1ay' in server: server = ''
    elif 'powvideo' in server or 'powvldeo' in server or 'powv1deo' in server: server = ''
    elif 'uploaded' in server: server = ''
    elif 'vev' in server: server = ''

    elif 'upstream' in server:
           if '.' in server:
               server = scrapertools.find_single_match(server, "s.*?.(.*?)$")
               server = server.replace('.', '').replace('0', '').replace('1', '').replace('2', '').replace('3', '').replace('4', '').replace('5', '').replace('6', '').replace('7', '').replace('8', '').replace('9', '').strip()

    elif 'viduplayer' in server: server = ''
    elif server == 'ul': server = ''

    if server:
        if servertools.is_server_available(server):
            if not servertools.is_server_enabled(server): server = ''
        else:
           if not config.get_setting('developer_mode', default=False):
               if server == 'desconocido': server = ''

    return server


def puntuar_calidad(txt):
    orden = ['SD 240p', 'SD 360p', 'SD 480p', 'HD 720p', 'DVD Rip', 'BD Rip', 'HD 1080p', 'HDTV', 'HD Rip', 'MicroHD 1080p', 'BDremux 1080p', 'BluRay 720p', 'BluRay 1080p', 'FullBluray 1080p', '4K 2160p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.dpost:
        post = {'action': 'doo_player_ajax', 'post': item.dpost, 'nume': item.dnume, 'type': 'movie'}

        data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = post)

        url = scrapertools.find_single_match(data, "src='(.*?)'")
        if not url: url = scrapertools.find_single_match(data, 'src=.*?"(.*?)"')
        if not url: url = scrapertools.find_single_match(data, '"embed_url":"(.*?)"')

        url = url.replace('\\/', '/')

        if '/?source=' in url: url = scrapertools.find_single_match(data, '/?source=(.*?)"')

        if '/www.tokyvideo.com/' in url:
            data = do_downloadpage(url)

            url = scrapertools.find_single_match(data, '<source src="(.*?)"')

            if url:
                itemlist.append(item.clone(server = 'directo', url = url))

                return itemlist

    elif item.server:
        data = do_downloadpage(url)

        url = scrapertools.find_single_match(data, '<a id="link".*?href="(.*?)"')

        url = url.replace('&#038;', '&').replace('&amp;', '&')

        if item.server == 'upstream':
            if 'dl?op=download_orig' in url:
                return 'Upstream download [COLOR tan]No soportado[/COLOR]'

    if url:
        if url.endswith('.torrent'):
            if PY3:
                if config.get_setting('channel_pelisyseries_proxies', default=''):
                    from core import requeststools
                    data = requeststools.read(url, 'pelisyseries')
                else:
                    data = do_downloadpage(url)
            else:
                data = do_downloadpage(url)

            if data:
                if '<h1>Not Found</h1>' in str(data) or '<!DOCTYPE html>' in str(data) or '<!DOCTYPE>' in str(data):
                    return 'Archivo [COLOR red]Inexistente[/COLOR]'

                file_local = os.path.join(config.get_data_path(), "temp.torrent")
                with open(file_local, 'wb') as f: f.write(data); f.close()

                itemlist.append(item.clone( url = file_local, server = 'torrent' ))

            return itemlist

        if 'archive.org' in url: url = url.replace('https%3A%2F%2Farchive.org%2Fdownload%2F', 'https://archive.org/download/').replace('%2F', '/')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h1(.*?)>Año de lanzamiento<')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')

        title = scrapertools.find_single_match(match, ' alt="(.*?)"')

        if not url or not title: continue

        title = title.replace('&#038;', '&').replace('&#8217;s', "'s").replace('&#8211;', '').replace('&#8217;', '')

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        year = scrapertools.find_single_match(match, '<span class="year">(.*?)</span>')
        if not year: year = '-'
        else: title = title.replace('(' + year + ')', '').strip()

        langs = []
        lngs = scrapertools.find_multiple_matches(match, '.*?/flags/(.*?).png')

        if 'es' in lngs: langs.append('Esp')
        if 'mx' in lngs: langs.append('Lat')
        if 'en' in lngs: langs.append('Vose')

        plot = scrapertools.htmlclean(scrapertools.find_single_match(match, '<p>(.*?)</p>'))

        tipo = 'movie' if '/peliculas/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, languages=', '.join(langs), fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

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

