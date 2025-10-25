# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://doramasmp4.org.mx/'


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://doramasmp4.se/', 'https://doramasmp4.dev/']

    for ant in ant_hosts:
        url = url.replace(ant, host)

    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar dorama ...', action = 'search', search_type = 'tvshow', text_color = 'firebrick' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host, group = 'last', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    genres = [
       ['action-adventure', 'Acción y Aventura'],
       ['animation', 'Animación'],
       ['comedy', 'Comedia'],
       ['crime', 'Crimen'],
       ['drama', 'Drama'],
       ['family', 'Familiar'],
       ['mystery', 'Misterio'],
       ['reality', 'Reality'],
       ['sci-fi-fantasy', 'Sci-fi Fantasy']
       ]

    url_gen = host + '/category/'

    for genero in genres:
        url = url_gen + genero[0] + '/'

        itemlist.append(item.clone( title = genero[1], action = 'list_all', url = url, text_color = 'firebrick' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    bloque = data

    if item.group == 'last': bloque = scrapertools.find_single_match(data, '>Episodes<(.*?)</section>')

    matches = re.compile('<article(.*?)</article>').findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<div class="Title">(.*?)</div>')
        if not title: title = scrapertools.find_single_match(match, 'data-subtitle="(.*?)"')

        if not url or not title: continue

        title = title.replace('&#8217;', "'").replace('&#8220;', '').replace('&#8221;', '').replace('&#8211;', '').strip()

        SerieName = title

        if 'Capitulo' in SerieName: SerieName = SerieName.split("Capitulo")[0]
        if 'Capítulo' in SerieName: SerieName = SerieName.split("Capítulo")[0]
        if 'capitulo' in SerieName: SerieName = SerieName.split("capitulo")[0]
        if 'capítulo' in SerieName: SerieName = SerieName.split("capítulo")[0]

        if 'Temporada' in SerieName: SerieName = SerieName.split("Temporada")[0]
        if 'temporada' in SerieName: SerieName = SerieName.split("temporada")[0]
        if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
        if 'season' in SerieName: SerieName = SerieName.split("season")[0]

        SerieName = SerieName.strip()

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')
        if not thumb: thumb = scrapertools.find_single_match(match, 'data-lazy-src="(.*?)"')

        titulo = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        titulo = titulo.replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')

        if item.group == 'last':
            season = 1

            if '-temporada-' in url:
                season = scrapertools.find_single_match(url, '-temporada-(.*?)/')
                if not season: season = 1

            epis = scrapertools.find_single_match(url, '-capitulo-(.*?)/')
            if not epis: epis = scrapertools.find_single_match(url, '-capitulo-(.*?)-')

            if not epis: epis = 1

            if '>Upcoming<' in match:
                titulo = '[COLOR cyan][B]Proximamente[/B][/COLOR]' + ' ' + titulo

            itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, contentType = 'episode', contentSerieName = SerieName,
                                        contentSeason = season, contentEpisodeNumber=epis, infoLabels={'year': '-'} ))
        else:
            itemlist.append(item.clone( action='temporadas', url=url, title=titulo, thumbnail=thumb, contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if item.group == 'last': return itemlist

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<link rel="next".*?href="(.*?)"')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if not '<li data-index="' in data:
        if '>Upcoming<' in data or '>Ongoing<' in data:
            platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Proximamente[/B][/COLOR]')
            return

    if config.get_setting('channels_seasons', default=True):
        title = 'Sin temporadas'

        platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '[COLOR tan]' + title + '[/COLOR]')

    item.contentType = 'season'

    season = 1

    if '-temporada-' in item.url:
        season = scrapertools.find_single_match(item.url, '-temporada-(.*?)/')

        if not season: season = 1
    elif '-season-' in item.url:
        season = scrapertools.find_single_match(item.url, '-season-(.*?)/')

        if not season: season = 1

    item.contentSeason = season

    item.ref = item.url

    name_ser = item.contentSerieName.lower()
    name_ser = name_ser.replace(' ', '-').replace("'", '').replace(".", '').replace(",", '')

    item.url = host + 'season/' + name_ser + '-' + str(season) + '/'

    itemlist = episodios(item)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    headers = {'Referer': item.ref}

    data = do_downloadpage(item.url, headers = headers)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    bloque = scrapertools.find_single_match(data, '<tbody>(.*?)</tbody>')

    patron = '<span class="Num">(.*?)</span>.*?href="(.*?)".*?src="(.*?)".*?<td class="MvTbTtl">.*?">(.*?)</a>'

    matches = re.compile(patron, re.DOTALL).findall(bloque)

    if not matches:
        season = item.contentSeason
        if '-temporada-' in item.url: season = scrapertools.find_single_match(item.url, '-temporada-(.*?)/')

        epis = scrapertools.find_single_match(item.url, '-capitulo-(.*?)/')
        if not epis: epis = scrapertools.find_single_match(item.url, '-capitulo-(.*?)-')

        if not epis: epis = 1

        itemlist.append(item.clone( action='findvideos', url=item.url, title=item.title, contentType = 'episode', contentSeason = season, contentEpisodeNumber=epis ))

        return itemlist

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('DoramasMp4Dev', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('DoramasMp4Dev', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasMp4Dev', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasMp4Dev', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts > 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos?'):
                    platformtools.dialog_notification('DoramasMp4Dev', '[COLOR cyan]Cargando elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasMp4Dev', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('DoramasMp4Dev', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for epis, url, thumb, title, in matches[item.page * item.perpage:]:
        epis = epis.replace('Cap ', '').strip()

        orden = epis

        if len(orden) == 1: orden = '0' + orden

        titulo = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        titulo = titulo.replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + titulo

        if 'Sub Espanol' in title or 'sub espanol' in title:
            titulo = titulo.replace('Sub Espanol', '').replace('sub espanol', '').strip()

            titulo = titulo + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb, orden = orden,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page= item.page + 1, perpage = item.perpage, text_color='coral', orden = '10000' ))

    return sorted(itemlist, key=lambda i: i.orden)


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)

    ses = 0

    matches = scrapertools.find_multiple_matches(data, '<div id="VideoOption.*?<iframe src="(.*?)".*?</iframe>')

    for url in matches:
        if not url: continue

        ses += 1

        if url.startswith("//"): url = 'https:' + url

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = 'Vose', other = other ))

    if not itemlist:
        if '>Upcoming<' in data or '>Ongoing<' in data:
            platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Proximamente[/B][/COLOR]')
            return

        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    item.url = item.url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')
    item.url = item.url.replace('amp;#038;', '&').replace('#038;', '&').replace('amp;', '&')

    url = item.url

    if item.server == 'directo':
        if '/fkplayer.xyz' in url:
            return 'Servidor [COLOR plum]NO Soportado[/COLOR]'

        elif '.mundodrama.' in url or '/?trembed=' in url:
            data = do_downloadpage(url)

            url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')
            if not url: url = scrapertools.find_single_match(data, '<IFRAME.*?SRC="(.*?)"')

            if '/fkplayer.xyz' in url:
                return 'Servidor [COLOR plum]NO Soportado[/COLOR]'

        else: url = ''

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '?s=' + texto.replace(" ", "+")
        item.text = texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
