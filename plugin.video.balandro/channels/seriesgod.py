# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://seriesgod.buzz/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/xfsearch/' in url: raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    return data


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist=[]

    opciones = {
        'accion': 'Acción',
        'animacion': 'Animación',
        'aventura': 'Aventura',
        'biografia': 'Biografía',
        'ciencia-ficcion': 'Ciencia ficción',
        'comedia': 'Comedia',
        'crimen': 'Crimen',
        'documental': 'Documental',
        'drama': 'Drama',
        'familia': 'Familia',
        'fantasia': 'Fantasía',
        'guerra': 'Guerra',
        'historia': 'Historia',
        'misterio': 'Misterio',
        'musica': 'Música',
        'romance': 'Romance',
        'suspense': 'Suspense',
        'terror': 'Terror',
        'western': 'Western'
        }

    for opc in opciones:
        url = host + opc + '/'

        itemlist.append(item.clone( title = opciones[opc], action = 'list_all', url = url, text_color='hotpink' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1989, -1):
        url = host + 'xfsearch/' + str(x)

        itemlist.append(item.clone( title = str(x), url = url, action='list_all', text_color='hotpink' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<h4>(.*?)>Mejores')
    if not bloque: bloque = scrapertools.find_single_match(data, '</header>(.*?)>Mejores')

    matches = scrapertools.find_multiple_matches(bloque, '__item">(.*?)</div></div>')

    for match in matches:
        title =  scrapertools.find_single_match(match, 'title="(.*?)"')
        if not title: title =  scrapertools.find_single_match(match, '<h5>.*?">(.*?)</a>')

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if not title or not url: continue

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')
        thumb = host[:-1] + thumb

        title = title.replace('online gratis', '').replace('&#039;', "'").replace('&amp;', '&').strip()

        year = '-'
        if '/xfsearch/' in item.url:
            year = scrapertools.find_single_match(item.url, "/xfsearch/(.*?)$")
            if year:
               year = year.replace('.html', '')

               if '/page-' in year: year = scrapertools.find_single_match(year, "(.*?)/page-")

        if not year: year = '-'

        url = host[:-1] + url

        itemlist.append(item.clone( action='temporadas', url = url, title = title, thumbnail = thumb,
                                    contentType='tvshow', contentSerieName=title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<div class="navigation">.*?</span>.*?<a href=' + "'(.*?)'.*?</div>")
        if not next_page: next_page = scrapertools.find_single_match(data, '<div class="navigation">.*?</span>.*?<a href="(.*?)".*?</div>')

        if next_page:
            if '/page/' in next_page:
                next_page = host[:-1] + next_page

                itemlist.append(item.clone( title = 'Siguientes ...', action='list_all', url = next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<option value="(.*?)".*?>Temporada(.*?)</option>')

    for url, season in matches:
        season = season.strip()

        title = 'Temporada ' + season

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            url = scrapertools.find_single_match(data, '<link rel="canonical" href="(.*?)"')

            if url:
                if not host in url: url = host[:-1] + url

                item.page = 0
                item.contentType = 'season'
                item.contentSeason = season
                itemlist = episodios(item)

            return itemlist

        if not url:
            url = scrapertools.find_single_match(data, '<link rel="canonical" href="(.*?)"')

        if url:
            if not host in url: url = host[:-1] + url

            itemlist.append(item.clone( action = 'episodios', url = url, title = title, page = 0,
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

    bloque = scrapertools.find_single_match(data, '<li class="active">(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '(.*?)</li>')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('SeriesGod', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('SeriesGod', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SeriesGod', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SeriesGod', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SeriesGod', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SeriesGod', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('SeriesGod', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        title = scrapertools.find_single_match(match, '<span class="epname">(.*?)</span>')

        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        if not url or not title: continue

        epis = scrapertools.find_single_match(match, 'data-episode="(.*?)"')

        title = title.replace('Episodio ', '[COLOR goldenrod]Epis. [/COLOR]').replace('episodio ','[COLOR goldenrod]Epis. [/COLOR]')

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'") + ' ' + title

        url = host[:-1] + url

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

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

    IDIOMAS = {'ESPAÑOL': 'Esp', 'espanola': 'Esp', 'LATINO': 'Lat', 'latino': 'Lat', 'SUBTITULADO': 'Vose', 'SUB': 'Vose', 'subtitle': 'Vose'}

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '"links"(.*?)},')

    options = scrapertools.find_multiple_matches(str(bloque), '"(.*?)":"(.*?)"')

    if not options:
        options = scrapertools.find_multiple_matches(data, '<button class="bstd Button">.*?<span>(.*?)<span>.*?data-url="(.*?)"')

    ses = 0

    for lang, embed in options:
        ses += 1

        if not embed: continue

        if '/goodstream.' in embed:
            if not 'http' in embed: embed = 'https:' + embed
            url = embed
        else:
            url = 'https://goodstream.one/video/embed/' + embed

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)

        itemlist.append(Item(channel = item.channel, action = 'play', server=servidor, title = '', url=url, language=IDIOMAS.get(lang,lang), other=other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    post = {'do': 'search', 'subaction': 'search', 'story': item.tex}

    data = do_downloadpage(item.url, post=post)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<h4>(.*?)>Mejores')

    matches = scrapertools.find_multiple_matches(bloque, '__item">(.*?)</div></div>')

    for match in matches:
        title =  scrapertools.find_single_match(match, 'title="(.*?)"')
        if not title: title =  scrapertools.find_single_match(match, '<h5>.*?">(.*?)</a>')

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if not title or not url: continue

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')
        thumb = host[:-1] + thumb

        title = title.replace('online gratis', '').replace('&#039;', "'").replace('&amp;', '&').strip()

        url = host[:-1] + url

        itemlist.append(item.clone( action='temporadas', url = url, title = title, thumbnail = thumb,
                                    contentType='tvshow', contentSerieName=title,  infoLabels = {'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
       item.url = host
       item.tex = texto.replace(" ", "+")
       return list_search(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []

