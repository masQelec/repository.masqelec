# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://ww3.monoschinos3.com/'



def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_animes(item)


def mainlist_animes(item):
    logger.info()
    itemlist = []

    if config.get_setting('descartar_anime', default=False): return

    if not config.get_setting('ses_pin'):
        if config.get_setting('animes_password'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'all', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host, search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Últimos animes', action = 'list_last', url = host, search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'animes?estado[]=1?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'animes?estado[]=2?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Cortos', action = 'list_all', url = host + 'animes?tipo[]=5&estado[]=2',  search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Especiales', action = 'list_all', url = host + 'animes?tipo[]=4&estado[]=2',  search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Donghuas', action = 'list_all', url = host + 'animes?tipo[]=9&estado[]=2',  search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Ovas', action = 'list_all', url = host + 'animes?tipo[]=2&estado[]=2', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Onas', action = 'list_all', url = host + 'animes?tipo[]=6&estado[]=2', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'TV series', action = 'list_all', url = host + 'animes?tipo[]=1&estado[]=2', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'animes?tipo[]=3&estado[]=2', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'En castellano', action = 'list_all', url = host + 'animes?genre[]=42', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'En latino', action = 'list_all', url = host + 'animes?q=latino', text_color='moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    url_genre = host + 'animes'

    data = do_downloadpage(url_genre)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="dropdown-menu2"(.*?)</div></div>')

    matches = re.compile('id="(.*?)".*?">(.*?)</label>').findall(bloque)

    for genre_id, title in matches:
        if title == 'Latino': continue
        elif title == 'Castellano': continue

        title = title.capitalize()

        url = host + 'animes?genre[]=' + genre_id

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='springgreen' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1989, -1):
        url = host + 'animes?year[]=' + str(x)

        itemlist.append(item.clone( title = str(x), url = url, action='list_all', text_color='springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<li(.*?)</li>').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')
        if not title: title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        year = scrapertools.find_single_match(match, '<span class="bg-primary text-white text-xs px-2 py-1 rounded">(.*?)</span>')
        if not year: year = '-'

        title = title.replace('&quot;', '').replace('&amp;', '').strip()

        SerieName = corregir_SerieName(title)

        tipo = 'movie' if '>Pelicula' in match else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')
            title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

            season = scrapertools.find_single_match(url, '-temporada-(.*?)$')

            if not season: season = scrapertools.find_single_match(match, 'alt=".*?Temporada(.*?)"').strip()

            if not season: season = 1

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, fmt_sufijo = sufijo, 
                                        contentType = 'tvshow', contentSerieName = SerieName, contentSeason = season, infoLabels={'year': year} ))

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, fmt_sufijo = sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<li class="page-item active"' in data:
            next_page = scrapertools.find_single_match(data, '<li class="page-item active".*?href="(.*?)".*?</span>')

            if next_page:
                if 'page=' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Últimos capítulos(.*?)>Series recientes')

    matches = re.compile('<article>(.*?)</article>', re.DOTALL).findall(bloque)

    for match in matches:
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        if not url or not title: continue

        title = title.replace('&quot;', '').replace('&amp;', '').strip()

        SerieName = corregir_SerieName(title)

        season = scrapertools.find_single_match(url, '-temporada-(.*?)/')
        if not season: season = scrapertools.find_single_match(url, '-temporada-(.*?)$')

        if not season: season = scrapertools.find_single_match(match, 'alt=".*?Temporada(.*?)"').strip()

        if not season: season = 1

        epis = scrapertools.find_single_match(url, '/episodio-(.*?)$')

        if not epis: epis = scrapertools.find_single_match(match, '<span class="episode px-3 py-1 rounded-3">(.*?)</span>')

        if not epis: epis = 1

        SerieName = SerieName.replace(str(epis), '').strip()

        title = str(season) + 'x' + str(epis) + ' ' + title

        title = title.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('Ep.', '[COLOR goldenrod]Epis.[/COLOR]')

        title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')
        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        thumb = host[:-1] + thumb

        itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail=thumb, infoLabels={'year': '-'},
                                    contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber=epis))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Series recientes(.*?)</section>')

    matches = scrapertools.find_multiple_matches(bloque, '<article>(.*?)</article>')

    for match in matches:
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        if not url or not title: continue

        title = title.replace('&quot;', '').replace('&amp;', '').strip()

        SerieName = corregir_SerieName(title)

        title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')
        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        thumb = host[:-1] + thumb

        season = scrapertools.find_single_match(url, '-temporada-(.*?)$')

        if not season: season = scrapertools.find_single_match(match, 'alt=".*?Temporada(.*?)"').strip()

        if not season: season = 1

        itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb,
                                    contentType = 'tvshow', contentSerieName = SerieName, contentSeason = season, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    hay_proximo = False
    if '>Próximo episodio' in data: hay_proximo = True

    matches = re.compile('<article>(.*?)</article>', re.DOTALL).findall(data)

    if not matches:
        if '>Próximamente<' in data:
             platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#039;', "'").replace('&#8217;', "'"), '[COLOR cyan]Proximamente[/COLOR]')
             return

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('VillaAnimex', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('VillaAnimex', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VillaAnimex', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VillaAnimex', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VillaAnimex', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VillaAnimex', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('VillaAnimex', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        epis = scrapertools.find_single_match(match, '<h2 class="fs-5 mt-2 mb-1 text-light text-truncate d-flex gap-1">.*?Capitulo(.*?)<').strip()
        if not epis: epis = 1

        title = 'Capítulo ' + str(epis)

        if item.contentSerieName: titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName
        else: titulo = item.title

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo,
                                    contentType = 'episode', contentSeason=item.contentSeason, contentEpisodeNumber=epis ))

        if len(itemlist) >= item.perpage:
            if hay_proximo:
                next_cap = scrapertools.find_single_match(data, '>Próximo episodio.*?</span>(.*?)</li>').strip()

                if next_cap:
                    next_cap = 'Próx. Epis.: ' + next_cap
                    itemlist.append(item.clone( action='', title = next_cap, thumbnail = item.thumbnail, text_color='cyan' ))
            break

    tmdb.set_infoLabels(itemlist)

    if not itemlist:
        if hay_proximo:
            next_cap = scrapertools.find_single_match(data, '>Próximo episodio.*?</span>(.*?)</li>').strip()

            if next_cap:
                platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Proximamente[/B][/COLOR]')

                next_cap = 'Próx. Epis.: ' + next_cap
                itemlist.append(item.clone( action='', title = next_cap, thumbnail = item.thumbnail, text_color='cyan', infoLabels={'year': ''} ))

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('animes_password'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    data = do_downloadpage(item.url)

    matches = re.compile('data-video="(.*?)"', re.DOTALL).findall(data)

    ses = 0

    for url in matches:
        if not url: continue

        ses += 1

        url = base64.b64decode(url).decode("utf-8")

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)
        elif servidor == 'zures': other = servertools.corregir_zures(url)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language ='Vose', other = other ))

    # ~ Descargas NO funcionan

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if 'Peliculas' in SerieName: SerieName = SerieName.split("Peliculas")[0]
    if 'Movie' in SerieName: SerieName = SerieName.split("Movie")[0]

    if 'Latino' in SerieName: SerieName = SerieName.split("Latino")[0]
    if 'Castellano' in SerieName: SerieName = SerieName.split("Castellano")[0]

    if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
    if 'season' in SerieName: SerieName = SerieName.split("season")[0]

    if ' Parte ' in SerieName: SerieName = SerieName.split(" Parte ")[0]
    if ' Part ' in SerieName: SerieName = SerieName.split(" Part ")[0]

    if ': ' in SerieName: SerieName = SerieName.split(": ")[0]

    if ' Picture ' in SerieName: SerieName = SerieName.split(" Picture ")[0]

    if ' Temporada ' in SerieName: SerieName = SerieName.split(" Temporada ")[0]

    if ' Specials' in SerieName: SerieName = SerieName.split(" Specials")[0]
    if ' Especiales' in SerieName: SerieName = SerieName.split(" Especiales")[0]
    if ' Drama' in SerieName: SerieName = SerieName.split(" Drama")[0]
    if ' OVA' in SerieName: SerieName = SerieName.split(" OVA")[0]

    if '2nd' in SerieName: SerieName = SerieName.split("2nd")[0]
    if '3rd' in SerieName: SerieName = SerieName.split("3rd")[0]
    if '4th' in SerieName: SerieName = SerieName.split("4th")[0]
    if '5th' in SerieName: SerieName = SerieName.split("5th")[0]
    if '6th' in SerieName: SerieName = SerieName.split("6th")[0]
    if '7th' in SerieName: SerieName = SerieName.split("7th")[0]
    if '8th' in SerieName: SerieName = SerieName.split("8th")[0]
    if '9th' in SerieName: SerieName = SerieName.split("9th")[0]

    SerieName = SerieName.strip()

    return SerieName


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'animes?q=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

