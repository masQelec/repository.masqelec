# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://estrenosanime.net/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'ultimo-actualizado', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', group = 'lasts', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Últimos animes', action = 'list_all', url = host + 'ultimo-anime', search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'estado/En+Emision', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'estado/Completado', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'popular', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Especiales', action = 'list_all', url = host + 'tipo/Especial', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'TV series', action = 'list_all', url = host + 'tipo/TV+Series', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Onas', action = 'list_all', url = host + 'tipo/ONA', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Ovas', action = 'list_all', url = host + 'tipo/OVA', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'tipo/Pelicula', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos',  search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'tvshow' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host + 'ultimo-episodios', group = 'lasts', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos en latino', action = 'list_all', url = host + 'ultimo-latino', group = 'lasts', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos subtitulados', action = 'list_all', url = host + 'ultimo-subtitulado', group = 'lasts', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host + 'home').data

    bloque = scrapertools.find_single_match(data, '>Genero<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?title="(.*?)"')

    for genre, title in matches:
        title = title.strip()

        url = host[:-1] + genre

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='springgreen' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime

    url_anios = host + 'years/'

    current_year = int(datetime.today().year)

    for x in range(current_year, 1979, -1):
        url = url_anios + str(x)

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color='springgreen' ))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    for letra in 'abcdefghijklmnopqrstuvwxyz':
        letra = letra.upper()

        itemlist.append(item.clone ( title = letra, url = host + 'az-list/' + letra, action = 'list_all', group = 'alfa', text_color='springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<div class="tick ltr">(.*?)<div class="clearfix"></div>')

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')

        if not url or not title: continue

        url = host[:-1] + url

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        title = title.replace('&amp;', '').replace('&#039;s', "'s").replace('&#39;', "'").replace('#039;', '').replace('&quot;', '').strip()

        SerieName = corregir_SerieName(title)

        tipo = 'movie' if '-movie' in url or '>Pelicula<' in match else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        season = 1

        if 'Season' in title:
            if '2nd' in title: season = 2
            elif '3rd' in title: season = 3
            elif '4th' in title: season = 4
            elif '5th' in title: season = 5
            elif '6th' in title: season = 6
            elif '7th' in title: season = 7
            elif '8th' in title: season = 8
            elif '9th' in title: season = 9

            elif '2Nd' in title: season = 2
            elif '3Rd' in title: season = 3
            elif '4Th' in title: season = 4
            elif '5Th' in title: season = 5
            elif '6Th' in title: season = 6
            elif '7Th' in title: season = 7
            elif '8Th' in title: season = 8
            elif '9Th' in title: season = 9

            else:
               season = scrapertools.find_single_match(title, 'Season(.*?)Capítulo').strip()
               if not season : season = scrapertools.find_single_match(title, 'Season(.*?)$').strip()

               if not season: season = 1
        else:
            if ' S2' in title: season = 2
            elif ' S3' in title: season = 3
            elif ' S4' in title: season = 4
            elif ' S5' in title: season = 5
            elif ' S6' in title: season = 6
            elif ' S7' in title: season = 7
            elif ' S8' in title: season = 8
            elif ' S9' in title: season = 9
            else:
               season = scrapertools.find_single_match(url, '-temporada-(.*?)-Capítulo').strip()
               if not season : season = scrapertools.find_single_match(url, '-temporada-(.*?)-').strip()

               if not season: season = 1

        action = 'episodios'

        if item.group == 'lasts': action = 'findvideos'


        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]').replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

            if item.group == 'lasts':
               epis = scrapertools.find_single_match(match, '<div class="tick-item tick-eps amp-algn">(.*?)</div>').strip()

               if epis:
                   epis = epis.replace('EP', '[COLOR goldenrod]Epis.[/COLOR]')
                   title = epis + ' ' + title

            itemlist.append(item.clone( action = action, url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = SerieName, contentSeason = season, infoLabels={'year': '-'} ))

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            if '-temporada-' in url: continue

            title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]').replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

            itemlist.append(item.clone( action = action, url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = SerieName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '"Page navigation">' in data:
            bloque = scrapertools.find_single_match(data,'"Page navigation">(.*?)</nav>')

            next_page = scrapertools.find_single_match(bloque, '<li class="page-item active">.*?</a>.*?</li>.*?href="(.*?)".*?</ul>')

            if next_page:
                if '?page=' in item.url: item.url = item.url.split("?page=")[0]
                elif '&page=' in item.url: item.url = item.url.split("&page=")[0]

                if '?page=' in next_page or '&page=' in next_page:
                    if '?page=' in next_page:
                        next_page = next_page.split("?page=")[1]
                        next_page = '?page=' + next_page
                    elif '&page=' in next_page:
                        next_page = next_page.split("&page=")[1]
                        next_page = '&page=' + next_page

                    if item.group == 'alfa': next_page = host + 'az-list/' + next_page

                    else: next_page = item.url + next_page

                    itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = httptools.downloadpage(item.url).data

    da_id = scrapertools.find_single_match(data, 'data-anime-id="(.*?)"')

    if not da_id: return itemlist

    item.url = item.url.replace('/anime/', '/ver/') + '/episodio-1'

    headers = {'Referer': item.url, 'X-Requested-With': 'XMLHttpRequest'}

    data = httptools.downloadpage(host + 'ajax/v2/episode/list/' + da_id + '?order=asc', headers = headers).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    data = data.replace('\\/', '/')

    data = data.replace('=\\', '=').replace('\\"', '"')

    episodes = scrapertools.find_multiple_matches(data, 'data-number="(.*?)".*?href="(.*?)"')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(episodes)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('EstrenosAnime', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('EstrenosAnime', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EstrenosAnime', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EstrenosAnime', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EstrenosAnime', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EstrenosAnime', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('EstrenosAnime', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for epis, url in episodes[item.page * item.perpage:]:
        if not epis: epis = 1

        if item.contentSerieName:
            titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName
            season = item.contentSeason
        else:
            if not item.contentSeason: season = 1
            else: season = item.contentSeason

            titulo = str(season) + 'x' + str(epis) + ' ' + item.title

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        url = host[:-1] + url

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    if itemlist:
        if len(episodes) > ((item.page + 1) * item.perpage):
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

    data = httptools.downloadpage(item.url).data

    depi_id = scrapertools.find_single_match(data, 'data-episode-id="(.*?)"')

    if not depi_id: return itemlist

    headers = {'Referer': item.url, 'X-Requested-With': 'XMLHttpRequest' }

    data = httptools.downloadpage(host + 'ajax/v2/episode/servers?episodeId=' + depi_id, headers = headers).data

    data = data.replace('\\/', '/')

    data = data.replace('=\\', '=').replace('\\"', '"')

    d_id = scrapertools.find_single_match(data, 'data-id="(.*?)"')

    if not d_id: return itemlist

    data = httptools.downloadpage(host + 'ajax/v2/episode/sources?id=' + d_id, headers = headers).data

    new_url = scrapertools.find_single_match(data, '"link":.*?"(.*?)"')

    if not new_url: return itemlist

    data = httptools.downloadpage(new_url).data

    videos = scrapertools.find_multiple_matches(data, '<li onclick="go_to_player.*?' + "'(.*?)'.*?<span>(.*?)</span>.*?<p>(.*?)</p>.*?</li>")

    ses = 0

    for url, srv, datos in videos:
        ses += 1

        if url:
            if 'krakenfiles.' in srv: continue

            servidor = servertools.get_server_from_url(srv)
            servidor = servertools.corregir_servidor(servidor)

            link_other = srv


            link_other = link_other.replace('www.', '').replace('.com', '').replace('.net', '').replace('.org', '').replace('.top', '')
            link_other = link_other.replace('.co', '').replace('.cc', '').replace('.sh', '').replace('.to', '').replace('.tv', '').replace('.ru', '').replace('.io', '')
            link_other = link_other.replace('.eu', '').replace('.ws', '').replace('.sx', '').replace('.nz', '').replace('.io', '').replace('.pro', '')

            if servidor == 'directo': other = link_other
            else: link_other = ''

            if servidor == 'various': link_other = servertools.corregir_other(srv)
            elif servidor == 'zures': link_other = servertools.corregir_zures(srv)

            lang = 'Vose'
            if 'Español Latino' in datos: lang = 'Lat'

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = lang, other = link_other.capitalize() ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    servidor = item.server

    url = item.url

    if url:
        data = httptools.downloadpage('https://multiserver.icu/embed/api/decrypt-stream', post = {'encrypted': url}).data

        new_url = scrapertools.find_single_match(data, '"url":.*?"(.*?)"')

        if new_url:
            url = new_url

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

    if url:
        if url.startswith("https://sb"):
            return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
    if 'season' in SerieName: SerieName = SerieName.split("season")[0]

    if 'Temporada' in SerieName: SerieName = SerieName.split("Temporada")[0]
    if 'temporada' in SerieName: SerieName = SerieName.split("temporada")[0]

    if ' Especiales' in SerieName: SerieName = SerieName.split(" Especiales")[0]
    elif ' Especial' in SerieName: SerieName = SerieName.split(" Especial")[0]
    elif ' Specials' in SerieName: SerieName = SerieName.split(" Specials")[0]
    elif ' Special' in SerieName: SerieName = SerieName.split(" Special")[0]

    if 'Movie' in SerieName: SerieName = SerieName.split("Movie")[0]

    if '(TV)' in SerieName: SerieName = SerieName.split(" (TV)")[0]

    if '(Latino)' in SerieName: SerieName = SerieName.split("(Latino)")[0]
    if ' Latino' in SerieName: SerieName = SerieName.split(" Latino")[0]

    if ' Japonés' in SerieName: SerieName = SerieName.split(" Japonés")[0]

    if ':' in SerieName: SerieName = SerieName.split(": ")[0]

    if ' S1' in SerieName: SerieName = SerieName.split(" S1")[0]
    elif ' S2' in SerieName: SerieName = SerieName.split(" S2")[0]
    elif ' S3' in SerieName: SerieName = SerieName.split(" S3")[0]
    elif ' S4' in SerieName: SerieName = SerieName.split(" S4")[0]
    elif ' S5' in SerieName: SerieName = SerieName.split(" S5")[0]
    elif ' S6' in SerieName: SerieName = SerieName.split(" S6")[0]
    elif ' S7' in SerieName: SerieName = SerieName.split(" S7")[0]
    elif ' S8' in SerieName: SerieName = SerieName.split(" S8")[0]
    elif ' S9' in SerieName: SerieName = SerieName.split(" S9")[0]

    if ' T1' in SerieName: SerieName = SerieName.split(" T1")[0]
    elif ' T2' in SerieName: SerieName = SerieName.split(" T2")[0]
    elif ' T3' in SerieName: SerieName = SerieName.split(" T3")[0]
    elif ' T4' in SerieName: SerieName = SerieName.split(" T4")[0]
    elif ' T5' in SerieName: SerieName = SerieName.split(" T5")[0]
    elif ' T6' in SerieName: SerieName = SerieName.split(" T6")[0]
    elif ' T7' in SerieName: SerieName = SerieName.split(" T7")[0]
    elif ' T8' in SerieName: SerieName = SerieName.split(" T8")[0]
    elif ' T9' in SerieName: SerieName = SerieName.split(" T9")[0]

    if '2nd' in SerieName: SerieName = SerieName.split("2nd")[0]
    elif '3rd' in SerieName: SerieName = SerieName.split("3rd")[0]
    elif '4th' in SerieName: SerieName = SerieName.split("4th")[0]
    elif '5th' in SerieName: SerieName = SerieName.split("5th")[0]
    elif '6th' in SerieName: SerieName = SerieName.split("6th")[0]
    elif '7th' in SerieName: SerieName = SerieName.split("7th")[0]
    elif '8th' in SerieName: SerieName = SerieName.split("8th")[0]
    elif '9th' in SerieName: SerieName = SerieName.split("9th")[0]

    if '2Nd' in SerieName: SerieName = SerieName.split("2Nd")[0]
    elif '3Rd' in SerieName: SerieName = SerieName.split("3Rd")[0]
    elif '4Th' in SerieName: SerieName = SerieName.split("4Th")[0]
    elif '5Th' in SerieName: SerieName = SerieName.split("5Th")[0]
    elif '6Th' in SerieName: SerieName = SerieName.split("6Th")[0]
    elif '7Th' in SerieName: SerieName = SerieName.split("7Th")[0]
    elif '8Th' in SerieName: SerieName = SerieName.split("8Th")[0]
    elif '9Th' in SerieName: SerieName = SerieName.split("9Th")[0]

    SerieName = SerieName.strip()

    return SerieName


def search(item, texto):
    logger.info()
    try:
        item.url =  host + "search?keyword=" + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
