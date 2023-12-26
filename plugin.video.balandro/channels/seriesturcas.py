# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://seriesturcas.one/'


perpage = 30


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'category/peliculas-turcas/', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_list', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos capítulos', action = 'list_all', url = host + 'category/capitulos-completos/', group = 'capis', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Novedades', action = 'list_all', url = host + 'category/news/', group = 'capis', text_color = 'moccasin', search_type = 'tvshow' ))

    return itemlist


def list_list(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(host + 'seriesturcastv-4/')

    bloque = scrapertools.find_single_match(data, ">Categories<(.*?)</div>	</aside>")

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?"category-text">(.*?)</span>')

    num_matches = len(matches)

    for url, title in matches[item.page * perpage:]:
        title = title.capitalize()

        if title == 'Capitulos completos': continue

        itemlist.append(item.clone( action = 'temporadas', title = title, url = url, text_color = 'hotpink',
                                    contentType = 'tvshow', contentSerieName = title, infoLabels={'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='Siguientes ...', page=item.page + 1, action='list_list', text_color='coral' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        if 'En Vivo' in title or 'en Vivo' in title or 'en vivo' in title: continue

        thumb = scrapertools.find_single_match(match, 'data-img="(.*?)"')
        if not thumb:
            thumb = scrapertools.find_single_match(match, '<div class="posterThumb">.*?url(.*?)"')
            thumb = thumb.replace('(', '').replace(');', '').strip()

        title = title.replace('&#8211;', "").replace('&#8220;', "").replace('&#8221;', "").strip()

        title = title.replace('Telenovelas Gratis', '').replace('Telenovelas  Gratis', '').replace('Telenovelas', '').replace('Gratis', '').replace('Ver ', '').strip()
        title = title.replace('Pelicula Completa Online', '').replace('Pelicula Completa online', '').replace('Completa online', '').strip()

        if 'Capitulos Completos Online' in title: title = scrapertools.find_single_match(title, '(.*?)Capitulos Completos Online').strip()
        if 'Completos Online' in title: title = scrapertools.find_single_match(title, '(.*?)Completos Online').strip()
        if 'Completo' in title: title = scrapertools.find_single_match(title, '(.*?)Completo').strip()
        if 'Online' in title: title = scrapertools.find_single_match(title, '(.*?)Online').strip()
        if 'Capitulos' in title: title = scrapertools.find_single_match(title, '(.*?)Capitulos').strip()
        if 'HD' in title: title = scrapertools.find_single_match(title, '(.*?)HD').strip()

        title = title.replace(' ❤️', '').replace(' ✔️', '').strip()

        SerieName = title

        if "(SUBTITULO ESPAÑOL)" in SerieName: SerieName = SerieName.split("(SUBTITULO ESPAÑOL)")[0]
        elif "(SUBTITULADO ESPAÑOL)" in SerieName: SerieName = SerieName.split("(SUBTITULADO ESPAÑOL)")[0]

        elif "En Español" in SerieName: SerieName = SerieName.split("En Español")[0]
        elif "en Español" in SerieName: SerieName = SerieName.split("en Español")[0]
        elif "(En Espanol)" in SerieName: SerieName = SerieName.split("(En Espanol)")[0]
        elif "[Español Subtitulado]" in SerieName: SerieName = SerieName.split("[Español Subtitulado]")[0]
        elif "[SUB Espanol]" in SerieName: SerieName = SerieName.split("[SUB Espanol]")[0]
        elif "(English Subtitles)" in SerieName: SerieName = SerieName.split("(English Subtitles)")[0]
        elif "English Subtitles" in SerieName: SerieName = SerieName.split("English Subtitles")[0]

        SerieName = SerieName.strip()

        if "Temporada" in SerieName: SerieName = SerieName.split("Temporada")[0]

        if "Capitulos" in SerieName: SerieName = SerieName.split("Capitulos")[0]
        elif "Capítulos" in SerieName: SerieName = SerieName.split("Capítulos")[0]
        elif "Episodes" in SerieName: SerieName = SerieName.split("Episodes")[0]

        if "Capitulo" in SerieName: SerieName = SerieName.split("Capitulo")[0]
        elif "Capítulo" in SerieName: SerieName = SerieName.split("Capítulo")[0]
        elif "Episode" in SerieName: SerieName = SerieName.split("Episode")[0]

        if "Doblada" in SerieName: SerieName = SerieName.split("Doblada")[0]
        elif "Pelicula" in SerieName: SerieName = SerieName.split("Pelicula")[0]

        if " –" in SerieName: SerieName = scrapertools.find_single_match(SerieName, '(.*?) –').strip()

        if " |" in SerieName: SerieName = SerieName.replace(' |', '').strip()

        SerieName = SerieName.strip()

        tipo = 'tvshow' if '/category/' in item.url else 'movie'

        if item.search_type == 'tvshow':
            if '?s=' in item.url: tipo = 'tvshow'
        elif item.search_type == 'movie':
            if '?s=' in item.url: tipo = 'movie'
        else:
            if '?s=' in item.url:
                if '>Películas Turcas<' in match: tipo = 'movie'
                elif '>Capitulos Completos<' in match: tipo = 'tvshow'

        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

                if '?s=' in item.url: 
                    if '>Capitulos Completos<' in match: continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = SerieName, infoLabels={'year': '-'} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

                if '?s=' in item.url: 
                    if '>Películas Turcas<' in match: continue

            lang = ''
            if 'subtitulado' in title.lower() or 'subtitulo' in title.lower(): lang = 'Vose'

            if '?s=' in item.url or item.group == 'capis':
                if item.group == 'capis':
                    if not '-capitulo-' in url: continue

                cap = False

                if 'Capitulos' in title or 'Capítulos' in title or 'Episodes' in title: pass

                elif 'Capitulo' in title or 'Capítulo' in title or 'Episode' in title: cap = True

                if 'EN VIVO' in title: title = title.replace('EN VIVO', '').strip()

                if cap:
                    season = scrapertools.find_single_match(title, 'Temporada(.*?)Capítulo').strip()
                    if not season: season = scrapertools.find_single_match(title, 'Temporada(.*?)Capitulo').strip()
                    if not season: season = 1

                    epis = scrapertools.find_single_match(match, '<span>Cap.*?<span>(.*?)</span>')
                    if not epis: epis = 1

                    title = title.replace('Capitulo', '[COLOR goldenrod]Capitulo[/COLOR]').replace('Capítulo', '[COLOR goldenrod]Capítulo[/COLOR]').replace('Episode', '[COLOR goldenrod]Episode[/COLOR]')

                    itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, lang = lang, fmt_sufijo=sufijo, infoLabels={'year': '-'},
                                                contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis ))
                    continue

                else:
                    title = title.replace('Temporada', '[COLOR tan]Temporada[/COLOR]')

                    itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, lang = lang, fmt_sufijo=sufijo,
                                                contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '?s=' in item.url: next_page = scrapertools.find_single_match(data, '<nav id="vce-pagination" class="vce-load-more">.*?a href="(.*?)"')
        else:
            next_page = scrapertools.find_single_match(data, "<div class='pagination'>.*?<span class='current'>.*?a href='(.*?)'")
            if not next_page: next_page = scrapertools.find_single_match(data, '<nav id="vce-pagination" class="vce-load-more">.*?a href="(.*?)"')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Temporadas y episodios<(.*?)</div></div></div>')

    if bloque:
        block = scrapertools.find_single_match(data, '<ul class="eplist">(.*?)</ul>')

        epis = re.compile('<a class="epNum"(.*?)</a>', re.DOTALL).findall(block)

        if epis:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '[COLOR tan]Sin temporadas[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = 1
            itemlist = episodios(item)

    else:
        if config.get_setting('channels_seasons', default=True):
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '[COLOR tan]Sin temporadas[/COLOR]')

        item.page = 0
        item.contentType = 'season'
        item.contentSeason = 1
        itemlist = episodios(item)

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    block = scrapertools.find_single_match(data, '<ul class="eplist">(.*?)</ul>')

    matches = re.compile('<a class="epNum"(.*?)</a>', re.DOTALL).findall(block)

    if not matches: matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(data)

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
                platformtools.dialog_notification('SeriesTurcas', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:

            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SeriesTurcas', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SeriesTurcas', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SeriesTurcas', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SeriesTurcas', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('SeriesTurcas', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')
        title = scrapertools.find_single_match(match, 'title="(.*?)"').strip()

        if not url or not title: continue

        title = title.replace('&#8211;', "").strip()

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        epis = scrapertools.find_single_match(match, 'title=".*?Capitulo (.*?)"').strip()

        if '–' in epis: epis = scrapertools.find_single_match(epis, '(.*?)–').strip()

        if 'Completo' in epis: epis = epis.replace('Completo', '').strip()
        if 'Online' in epis: epis = epis.replace('Online', '').strip()

        if num_matches < 100:
            if len(epis) == 1: epis = '0' + epis
        else:
            if len(epis) == 1: epis = '00' + epis
            elif len(epis) == 2: epis = '0' + epis

        if not epis: epis = '01'

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail=thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if num_matches > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return sorted(itemlist, key = lambda it: it.title)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if item.lang == 'Vose': lang = 'Vose'
    else: lang = 'Lat'

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<iframe.*?src="(.*?)"')

    ses = 0

    for url in matches:
        ses += 1

        if url.startswith('//'): url = 'https:' + url

        if url.startswith('http://vidmoly'): url = url.replace('http://vidmoly', 'https://vidmoly').replace('/w/', '/embed-')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)

        if not servidor == 'directo':
            itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = lang, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

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

