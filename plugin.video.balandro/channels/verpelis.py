# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://verpelis.gratis/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/anos/' in url: raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catalogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    data = do_downloadpage(host + 'peliculas/')

    bloque = scrapertools.find_single_match(data, '>Géneros<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?>(.*?)</a>')

    for url, tit in matches:
        tit = tit.replace('&amp;', '&')

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = text_color ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1959, -1):
        itemlist.append(item.clone( title = str(x), url = host + 'anos/' + str(x) + '/', action = 'list_all', text_color='deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Añadido recientemente<(.*?)>Géneros<')
    if not bloque: bloque = scrapertools.find_single_match(data, '</h1>(.*?)>Géneros<')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, '<a href="(.*?)"')

        title = scrapertools.find_single_match(article, 'alt="(.*?)"').strip()

        if not url or not title: continue

        title = title.replace('&#039;s', "'s").replace('&#038;', '').replace('&#8211;', '').replace('&#8217;', "'").replace('&amp;', '&').strip()

        thumb = scrapertools.find_single_match(article, '<img src="(.*?)"')

        c_year = scrapertools.find_single_match(title, '(\d{4})')
        if c_year: title = title.replace('(' + c_year + ')', '').strip()

        year = scrapertools.find_single_match(article, '</h3><span>(.*?)</span>')
        if not year: year = '-'

        tipo = 'tvshow' if '/series/' in url else 'movie'

        if tipo == 'movie':
            if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<span class="current">' in data:
            next_page = scrapertools.find_single_match(data, '<span class="current">.*?' + "<a href='(.*?)'.*?</a>")

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile("<span class='se-t.*?'>(.*?)</span>", re.DOTALL).findall(data)

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

    bloque = scrapertools.find_single_match(data, "<span class='se-t.*?'>" + str(item.contentSeason) + "</span>(.*?)</ul>")

    matches = re.compile("<li class='mark-.*?<img src='(.*?)'.*?</div><div class='numerando'>(.*?)</div>.*?<a href='(.*?)'>(.*?)</a>", re.DOTALL).findall(bloque)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('VerPelis', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('VerPelis', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VerPelis', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VerPelis', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VerPelis', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VerPelis', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('VerPelis', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for thumb, season_epis, url, title in matches[item.page * item.perpage:]:
        season = scrapertools.find_single_match(season_epis, '(.*?)-').strip()
        epis = scrapertools.find_single_match(season_epis, '-(.*?)$').strip()

        titulo = str(season) + 'x' + str(epis) + ' ' + title.strip()

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        if 'Epis.' in titulo: titulo = titulo + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        itemlist.append(item.clone( action='findvideos', title = titulo, thumbnail=thumb, url = url,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis ))

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

    IDIOMAS = {'Latino': 'Lat', 'LAT': 'Lat', 'LA': 'Lat', 'Castellano': 'Esp', 'Español': 'Esp', 'ESP': 'Esp', 'ES': 'Esp', 'Subtitulado': 'Vose', 'SUB': 'Vose'}

    data = do_downloadpage(item.url)

    ses = 0

    matches = re.compile("<li id='player-option-(.*?)</li>", re.DOTALL).findall(data)

    for option in matches:
        ses += 1

        dpost = scrapertools.find_single_match(option, " data-post='(.*?)'")
        dtype = scrapertools.find_single_match(option, " data-type='(.*?)'")
        dnume = scrapertools.find_single_match(option, " data-nume='(.*?)'")

        if not dpost or not dtype or not dnume: continue

        if dnume == 'trailer': continue

        post = {'action': 'doo_player_ajax', 'post': dpost, 'nume': dnume, 'type': dtype}

        data1 = do_downloadpage(host + 'wp-json/dooplayer/v2/', post=post, headers= {'Referer': item.url} )

        embed = scrapertools.find_single_match(data1, '"embed_url":"(.*?)"')

        if not embed: continue

        embed = embed.replace('\\/', '/')

        datae = do_downloadpage(embed)

        bloque = scrapertools.find_single_match(datae, '<div class="SelectLangDisp">(.*?)<div class="FirstLoad"')

        lang = scrapertools.find_single_match(bloque,'/lang/(.*?).png')

        links = scrapertools.find_multiple_matches(bloque, '<li onclick="(.*?)</p>')

        for url in links:
            ses += 1

            if url:
                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                link_other = ''

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                      language = IDIOMAS.get(lang, lang), other = link_other ))

    # ~ Downloads
    matches = re.compile("<tr id='link-(.*?)</tr>", re.DOTALL).findall(data)

    for match in matches:
        ses += 1

        link = scrapertools.find_single_match(match, "<a href='(.*?)'")

        if not link: continue

        lng = '?'

        if 'Latino' in match: lng = 'Lat'
        elif 'Castellano' in match: lng = 'Esp'
        elif 'Español' in match: lng = 'Esp'
        elif 'Subtitulado' in match: lng = 'Vose'

        datad = do_downloadpage(link)

        url = scrapertools.find_single_match(datad, '<a id="link".*?href="(.*?)".*?</a>')

        if url:
            if '/1fichier.' in url: continue
            elif '.fireload.' in url: continue
            elif '/ranoz.' in url: continue

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            other = ''

            if servidor == 'various': other = servertools.corregir_other(url)
            elif servidor == 'zures': other = servertools.corregir_zures(url)

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url,
                                  language = lng, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

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


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '</h1>(.*?)</div></div></div>')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"').strip()

        if not url or not title: continue

        title = title.replace('&#039;s', "'s").replace('&#038;', '').replace('&#8211;', '').replace('&#8217;', "'").replace('&amp;', '&').strip()

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        c_year = scrapertools.find_single_match(title, '(\d{4})')
        if c_year: title = title.replace('(' + c_year + ')', '').strip()

        year = scrapertools.find_single_match(match, '<span class="year">(.*?)</span>')
        if not year: year = '-'

        tipo = 'tvshow' if '>TV<' in match else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

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
