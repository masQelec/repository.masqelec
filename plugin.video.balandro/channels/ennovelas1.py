# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://ennovelas1.com/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'movies.php', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'all-series.php', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Nuevos episodios', action = 'last_epis', url = host + 'episodes.php', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Por país', action='paises', search_type = 'tvshow' ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    opciones = [
       ('novelas-americanas', 'América'),
       ('novelas-arabicas', 'Arabia'),
       ('novelas-britanica', 'Britania'),
       ('novelas-chilenas', 'Chile'),
       ('novelas-colombianas', 'Colombia'),
       ('novelas-coreanas', 'Corea'),
       ('novelas-espanolas', 'España'),
       ('novelas-frances', 'Francia'),
       ('novelas-mexicanas', 'México'),
       ('novelas-noruegas', 'Noruega'),
       ('Novelas-de-Reino-Unido', 'Reino Unido'),
       ('novelas-suecas', 'Suecia'),
       ('series-y-novelas-turcas', 'Turquía')
    ]

    for opc, tit in opciones:
        itemlist.append(item.clone( title=tit, url= host + 'category.php?cat=' + opc, action = 'list_all', text_color='moccasin' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<li class="col-xs-6 col-sm-4 col-md-3">(.*?)</div></div></li>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        tipo = 'movie' if 'película' in title or 'película' in title else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        title = title.replace('Ver Online', '').replace('Ver película', '').replace('Ver pelìcula', '').replace('película', '').replace('Ver', '').strip()
        title = title.replace('Online Gratis', '').replace('Online HD Gratis', '').replace('película Completa', '').replace('Completa', '').strip()

        SerieName = title

        if " - " in SerieName: SerieName = SerieName.split(" - ")[0]
        if "(en Español)" in SerieName: SerieName = SerieName.split("(en Español)")[0]
        if "(en Espanol)" in SerieName: SerieName = SerieName.split("(en Espanol)")[0]
        if "en español" in SerieName: SerieName = SerieName.split("en español")[0]

        SerieName = SerieName.strip()

        if "Temporada" in SerieName: SerieName = SerieName.split("Temporada")[0]
        if "Capitulos" in SerieName: SerieName = SerieName.split("Capitulos")[0]

        SerieName = SerieName.strip()

        year = scrapertools.find_single_match(match, '<span class="hot" style="background:#ff0000;">(.*?)</span>')
        if not year: year = '-'

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = SerieName, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            if 'search.php?keywords=' in item.url:
                cap = False
                if 'Capitulos' in title or 'Capítulos' in title: pass
                elif 'Capitulo' in title or 'Capítulo' in title: cap = True

                if cap:
                    season = scrapertools.find_single_match(title, 'Temporada(.*?)*').strip()
                    if not season: season = 1

                    epis = scrapertools.find_single_match(title, '- Capitulo(.*?)$').strip()
                    if not epis: epis = 1

                    title = title.replace('Capitulo', '[COLOR goldenrod]Capitulo[/COLOR]').replace('Capítulo', '[COLOR goldenrod]Capítulo[/COLOR]')

                    itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                                contentSerieName = SerieName, contentType = 'episode',
                                                contentSeason = season, contentEpisodeNumber = epis, infoLabels={'year': year} ))
                    continue

                else:
                    title = title.replace('Temporada', '[COLOR tan]Temporada[/COLOR]')

            lang = ''
            if 'category.php?cat=novelas-espanolas' in item.url: lang = 'Esp'

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, lang=lang, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<ul class="pagination.*?<li class="active">.*?</a>.*?<a href="(.*?)"')

        if next_page:
            if '&page=' in next_page:
                next_page = host + next_page

                itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<li class="col-xs-6 col-sm-4 col-md-3">(.*?)</div></div></li>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        season = 1

        epis = scrapertools.find_single_match(match, '<span class="ep">Ep (.*?)</span>')
        if not epis: epis = 1

        SerieName = title

        if " - " in SerieName: SerieName = SerieName.split(" - ")[0]
        if "(en Español)" in SerieName: SerieName = SerieName.split("(en Español)")[0]
        if "(en Espanol)" in SerieName: SerieName = SerieName.split("(en Espanol)")[0]
        if "en español" in SerieName: SerieName = SerieName.split("en español")[0]

        SerieName = SerieName.strip()

        if "Temporada" in SerieName: SerieName = SerieName.split("Temporada")[0]
        if "Capitulos" in SerieName: SerieName = SerieName.split("Capitulos")[0]
        if "Completo" in SerieName: SerieName = SerieName.split("Completo")[0]

        SerieName = SerieName.strip()

        title = title.replace('Capitulo', '[COLOR goldenrod]Capitulo[/COLOR]').replace('Capítulo', '[COLOR goldenrod]Capítulo[/COLOR]')

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, infoLabels={'year': '-'},
                                    contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<ul class="pagination.*?<li class="active">.*?</a>.*?<a href="(.*?)"')

        if next_page:
            if '&page=' in next_page:
                next_page = host + next_page

                itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'last_epis', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if config.get_setting('channels_seasons', default=True):
        platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '[COLOR tan]Sin temporadas[/COLOR]')

    item.page = 0
    item.contentType = 'season'
    item.contentSeason = 1
    itemlist = episodios(item)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="SeasonsEpisodesMain">(.*?)</div></div></div>')

    matches = re.compile('<a href="(.*?)".*?title="(.*?)".*?>Cap (.*?)</a>', re.DOTALL).findall(bloque)

    num_matches = len(matches)

    if item.page == 0 and item.perpage == 50:
        sum_parts = num_matches

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True): item.perpage = sum_parts
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('EnNovelas', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EnNovelas1', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EnNovelas1', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EnNovelas1', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EnNovelas1', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('EnNovelas1', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, title, epis in matches[item.page * item.perpage:]:
        epis = epis.strip()
        if not epis: epis = 1

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if num_matches > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    lang = 'Lat'

    if 'película en español' in data or 'pelicula en español' in data: lang = 'Esp'
    elif item.lang == 'Esp': lang = 'Esp'

    ses = 0

    # ~ embeds
    matches1 = scrapertools.find_multiple_matches(data, '<iframe.*?src="(.*?)"')
    matches2 = scrapertools.find_multiple_matches(data, '<div class="video-bibplayer-video">.*?href="(.*?)"')

    matches = matches1 + matches2

    for url in matches:
        ses += 1

        itemlist.append(Item( channel=item.channel, action = 'play', server = '', url = url, language = lang ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    data = do_downloadpage(url)

    vid = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')
    if vid:
       if '/uploads/' in vid: vid = scrapertools.find_single_match(data, 'data-embed=".*?3' + "<iframe.*?src='(.*?)'")

    if not vid: vid = scrapertools.find_single_match(data, "<iframe.*?src='(.*?)'")

    if vid:
       if not '/uploads/' in vid: url = vid

    if url:
        if url.startswith('https://sr.ennovelas.net/'): url = url.replace('/sr.ennovelas.net/', '/waaw.to/')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if not new_server.startswith("http"): servidor = new_server

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def search(item, texto):
    logger.info()
    try:
       item.url = host + 'search.php?keywords=' + texto.replace(" ", "+") + '/'
       return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

