# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = "https://seriespepito.co/"


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if not headers: headers = {'Referer': host}

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    return data


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Atualizadas', action = 'list_all', url = host + 'category/actualizadas/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'HBO', action = 'list_all', url = host, group = 'HBO',search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Netflix', action = 'list_all', url = host, group = 'Netflix',search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist=[]

    generos = [
       'accion',
       'action-adventure',
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
       'terror',
       'western'
       ]

    for genero in generos:
        url = host + 'category/' + genero + '/'

        itemlist.append(item.clone( action = 'list_all', title = genero.capitalize(), url = url ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if not item.group:
        bloque = scrapertools.find_single_match(data, '<h1(.*?)</section>')
    else:
        bloque = scrapertools.find_single_match(data, '<h2 class="Title">Series de ' + item.group + '(.*?)</section>')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h3 class="Title">(.*?)</h3>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, '<img data-src="(.*?)"')
        if thumb.startswith('/'): thumb = 'https:' + thumb

        year = scrapertools.find_single_match(match, '<span class="TpTv BgA Yr">(.*?)</span>')
        if not year: year = '-'

        plot = scrapertools.find_single_match(match, '<div class="Description"><p>(.*?)</p>')

        itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb, 
                                    contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year, 'plot': plot } ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if not item.group:
            if ' class="page-numbers current">' in data:
                next_page = scrapertools.find_single_match(data, ' class="page-numbers current">.*?href="(.*?)"')
                if next_page:
                    if '/page/' in next_page:
                        itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    seasons = scrapertools.find_multiple_matches(data, 'data-tab="(.*?)"')

    for tempo in seasons:
        title = 'Temporada ' + tempo

        if len(seasons) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, contentType = 'season', contentSeason = tempo ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, 'data-tab="' + str(item.contentSeason) + "(.*?)</table>")

    if '&lt;img data-src=' in bloque:
        bloque = bloque.replace('&lt;img data-src=', '<img data-src="').replace('&quot;', '"')

    patron = '<td><span class="Num">(.*?)</span>.*?<a href="(.*?)".*?<img data-src="(.*?)".*?<td class="MvTbTtl">.*?>(.*?)</a>'

    episodes = scrapertools.find_multiple_matches(bloque, patron)

    if item.page == 0:
        sum_parts = len(episodes)
        if sum_parts > 250:
            if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos?'):
                platformtools.dialog_notification('SeriesPepito', '[COLOR cyan]Cargando elementos[/COLOR]')
                item.perpage = 250

    for epis, url, thumb, title, in episodes[item.page * item.perpage:]:
        if thumb.startswith('/'): thumb = 'https:' + thumb

        titulo = str(item.contentSeason) + 'x' + epis + ' ' + title

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

    IDIOMAS = {'Latino': 'Lat', 'Espanol': 'Esp', 'Subtitulado': 'Vose'}

    data = do_downloadpage(item.url)

    if 'src=&quot;' in data:
        data = data.replace('src=&quot;', 'src="').replace('&quot;', '"')

    matches = scrapertools.find_multiple_matches(data, 'id="Opt.*?src="(.*?)"')

    if len(matches) > 5:
         platformtools.dialog_notification('SeriesPepito', '[COLOR cyan]Comprobando vídeos[/COLOR] ' + str(len(matches)))

    ses = 0

    for link in matches:
        ses += 1

        link = link.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')
        link = link.replace('amp;#038;', '&').replace('#038;', '&').replace('amp;', '&')

        data2 = do_downloadpage(link)

        new_url = scrapertools.find_single_match(data2, '<iframe.*?src="(.*?)"')

        if not new_url: continue

        data3 = do_downloadpage(new_url)

        if data3 == 'File was deleted': continue

        matches2 = scrapertools.find_multiple_matches(data3, 'onclick="go_to_player(.*?)</li>')

        for match in matches2:
            url = scrapertools.find_single_match(match, "'(.*?)'")

            srv = scrapertools.find_single_match(match, "<span>(.*?)</span>")

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            if url:
                lang = scrapertools.find_single_match(match, "<p>(.*?)-.*?</p>").strip()

                if not servidor == 'directo': srv = ''

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url,
                                      language = IDIOMAS.get(lang, lang), other = srv.capitalize() ))

    # ~ Download no se tratan

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.other:
        data = do_downloadpage(url)

        if 'name="h"' in data:
            hash = scrapertools.find_single_match(data, 'name="h".*?value="(.*?)"')

            if hash:
                post = {'h': hash}

                url = httptools.downloadpage('https://pelispluss.net/sc/r.php', post = post, follow_redirects=False).headers.get('location', '')

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        itemlist.append(item.clone( url = url, server = servidor ))

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

