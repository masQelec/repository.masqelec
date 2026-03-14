# -*- coding: utf-8 -*-

import re, base64 

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://seriesflixhd.info/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://seriesflix.wtf/', 'https://seriesflixhd.one/', 'https://seriesflixhd.fun/',
            'https://seriesflixhd.help/']


domain = config.get_setting('dominio', 'sflix', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'sflix')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'sflix')
    else: host = domain


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    # ~ por si viene de enlaces guardados
    for ant in ant_hosts:
        url = url.replace(ant, host)

    if not headers: headers = {'Referer': host}

    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'sflix', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_sflix', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='sflix', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_sflix', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'sflix', thumbnail=config.get_thumb('sflix') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series-online/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host, search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Dc', action = 'list_all', url = host + 'genero/dc/', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Marvel', action = 'list_all', url = host + 'genero/marvel/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por plataforma', action = 'plataformas', search_type = 'tvshow', text_color='moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>GÉNEROS<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?>(.*?)</a>')

    for url, title in matches:
        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color='hotpink' ))

    return sorted(itemlist, key=lambda it: it.title)


def plataformas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>PRODUCTORAS<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?-title">(.*?)</span>')

    for url, title in matches:
        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color='hotpink' ))

    return sorted(itemlist, key=lambda it: it.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h2 class="Title">(.*?)</h2>')

        if not url or not title: continue

        if ('|') in title:
            title = title.split("|")[0]
            title = title.strip()

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')
        if not 'http' in thumb: thumb = 'https:' + thumb

        year = scrapertools.find_single_match(match, '<span class="Qlty Yr">.*?)</span>')

        if not year: year = '-'

        title = title.replace('&#8230;', '').replace('&#8211;', '').replace('&#038;', '').replace('&#8217;s', "'s").replace('&#8217;', '').replace('&amp;', '&')

        title = title.replace('Poster', '').strip()

        if not host in url: url = host[:-1] + url

        itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                    contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<nav class="wp-pagenavi">' in data:
            next_page = scrapertools.find_single_match(data, '<nav class="wp-pagenavi">.*?<a class="page-numbers current">.*?href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Últimos Episodios<(.*?)</section>')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h2 class="Title".*?">(.*?)</h2>').strip()

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        temp_epis = scrapertools.find_single_match(match, 'data-subtitle="Episodio(.*?)">')

        if not temp_epis: continue

        temp_epis = temp_epis.strip()

        season = scrapertools.find_single_match(temp_epis, '(.*?)x').strip()
        if not season: season = 1

        episode = scrapertools.find_single_match(temp_epis, 'x(.*?)$').strip()
        if not episode: episode = 1

        title = title.replace('&#8230;', '').replace('&#8211;', '').replace('&#038;', '').replace('&#8217;s', "'s").replace('&#8217;', '').replace('&amp;', '&')

        title = title.replace('( ' + str(season) + ' x ' + str(episode) + ' )', '').strip()

        titulo = temp_epis + '  ' + title

        SerieName = title

        if ": " in SerieName: SerieName = SerieName.split(": ")[0]

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb,
                                    contentSerieName=SerieName, contentType='episode', contentSeason=season, contentEpisodeNumber=episode,
                                    infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    seasons = scrapertools.find_multiple_matches(data, '<div class="Title">.*?<a href="(.*?)".*?>Temporada(.*?)</span>')

    for url, tempo in seasons:
        tempo = tempo.replace('<span>', '').strip()

        title = 'Temporada ' + tempo

        if len(seasons) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

                item.page = 0
                item.contentType = 'season'
                item.contentSeason = tempo
                item.url = url
                itemlist = episodios(item)
                return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, url = url, page = 0,
                                    contentType = 'season', contentSeason = tempo, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    bloque = scrapertools.find_single_match(data, "</h1>(.*?)</tbody>")

    episodes = scrapertools.find_multiple_matches(bloque, '<td>(.*?)</td> </tr>')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(episodes)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('SFlix', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('SFlix', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SFlix', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SFlix', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SFlix', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SFlix', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('SFlix', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in episodes[item.page * item.perpage:]:
        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')
        if thumb: thumb = 'https' + thumb

        epis = scrapertools.find_single_match(match, '<span class="Num">(.*?)</span>')

        if not epis: epis = 1

        title = scrapertools.find_single_match(match, '<td class="MvTbTtl">.*?">(.*?)</a>')

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title.replace(' - ' + str(epis), '').strip()

        if 'episodie' in titulo.lower() or 'episodio' in titulo.lower() or 'capítulo' in titulo.lower() or 'capitulo' in titulo.lower():
            titulo = titulo + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(episodes) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title = "Siguientes ...", action = "episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    logger.info()
    itemlist = []

    IDIOMAS = {'LATINO': 'Lat', 'CASTELLANO': 'Esp', 'SUBTITULADO': 'Vose'}

    data = do_downloadpage(item.url)

    # embeds
    matches = scrapertools.find_multiple_matches(data, '<div data-url="(.*?)".*?<span>(.*?)<span>')

    ses = 0

    for d_url, lang in matches:
        if not d_url: continue

        ses += 1

        language = IDIOMAS.get(lang, lang)

        itemlist.append(Item( channel = item.channel, action = 'play', server = '', durl = d_url, language = language ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.durl:
        new_url = base64.b64decode(item.durl).decode("utf-8")

        if new_url:
            data = do_downloadpage(new_url)

            url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')

            if not url: url = new_url
            else: url = url.replace('/tmdbcdn.lat/', '/waaw.to/').replace('/latlat.xyz/', '/waaw.to/')

    if '/nuuuppp.' in url:
        return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

    if url:
        servidor = servertools.get_server_from_url(url)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone( url = url, server = servidor ))

    return itemlist


def _epis(item):
    logger.info()

    item.url = host
    item.search_type = 'tvshow'

    return last_epis(item)


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

