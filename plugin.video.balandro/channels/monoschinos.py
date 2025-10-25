# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://wwv.monoschinos2.net/'


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://monoschinos2.net/']

    for ant in ant_hosts:
        url = url.replace(ant, host)

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

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'animes?estado=en-emision', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'animes?estado=finalizado' , search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Especiales', action = 'list_all', url = host + 'animes?tipo=especial' , search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Cortos', action = 'list_all', url = host + 'animes?tipo=corto' , search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Donghuas', action = 'list_all', url = host + 'animes?tipo=donghua' , search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Onas', action = 'list_all', url = host + 'animes?tipo=ona' , search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Ovas', action = 'list_all', url = host + 'animes?tipo=ova' , search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'animes?tipo=pelicula', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'tvshow' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'En castellano', action = 'list_all', url = host + 'animes?genero=castellano', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'En latino', action = 'list_all', url = host + 'animes?genero=latino', text_color='moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    url_genre = host + 'animes'

    data = do_downloadpage(url_genre)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Género:(.*?)</div>')

    matches = re.compile('data-value="(.*?)".*?>(.*?)</li>').findall(bloque)

    for gen, title in matches:
        title = title.strip()

        if title == 'Genero': continue
        elif title == 'Castellano': continue
        elif title == 'Latino': continue

        url = host + 'animes?genero=' + gen

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='springgreen' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1964, -1):
        url = host + 'animes?anio=' + str(x)

        itemlist.append(item.clone( title = str(x), url = url, action='list_all', text_color='springgreen' ))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    for letra in '#ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if letra == '#':
            url = host + 'animes?letra=0-9'
        else:
            url = host + 'animes?letra=' + letra.lower()

        itemlist.append(item.clone( title = letra, action = 'list_all', url = url, text_color='springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('ficha_efecto">(.*?)</li>').findall(data)

    for match in matches:
        title = scrapertools.find_single_match(match, 'title="(.*?)"')
        if not title: title = scrapertools.find_single_match(match, '<h.*?>(.*?)</h')

        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        if not url or not title: continue

        url = url.replace('./', host)

        title = title.replace('Ver Anime', '').replace('Online Gratis', '').strip()

        title = title.replace('&quot;', '').replace('&amp;', '').replace('&#039;', "'")

        title = title.replace('Japonés', '[COLOR yellowgreen]Japonés[/COLOR]')

        SerieName = corregir_SerieName(title)

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')
        if not thumb: thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        tipo = 'movie' if '-movie-' in url or '>Pelicula<' in match else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            season = scrapertools.find_single_match(url, '-season-(.*?)$')

            if not season:
                season = 1

                if '-2nd-' in url: season = 2
                elif '-3rd-' in url: season = 3
                elif '-4th-' in url: season = 4
                elif '-5th-' in url: season = 5
                elif '-6th-' in url: season = 6
                elif '-7th-' in url: season = 7
                elif '-8th-' in url: season = 8
                elif '-9th*' in url: season = 9

            title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName=SerieName, contentSeason=season, infoLabels={'year': '-'} ))

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = SerieName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<a class="page-item active.*?</a>.*?href="(.*?)".*?</li>')

        if next_page:
            next_page = next_page.replace('&amp;', '&')

            if '?pag=' in next_page or '&pag=' in next_page:
                next_page = next_page.replace('./', host)

                itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>últimos capítulos<(.*?)>Series recientes<')

    matches = re.compile('<article>(.*?)</article>', re.DOTALL).findall(bloque)

    for match in matches:
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')
        if not title: title = scrapertools.find_single_match(match, 'title="(.*?)"')

        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        epis = scrapertools.find_single_match(match, '<span class="episode px-3 py-1 rounded-3">(.*?)</span>')
        if not epis: epis = scrapertools.find_single_match(url, '-episodio-(.*?)$')

        if not epis: epis = 1

        title = title.replace('&quot;', '').replace('&amp;', '').replace('&#039;', "'")

        SerieName = corregir_SerieName(title) 

        titulo = '[COLOR goldenrod]Epis. [/COLOR]' + str(epis) + ' ' + title.replace('capítulo ' + str(epis), '').replace('capitulo ' + str(epis), '').strip()

        titulo = titulo.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        titulo = titulo.replace('Japonés', '[COLOR yellowgreen]Japonés[/COLOR]')

        season = scrapertools.find_single_match(url, '-season-(.*?)$')

        if not season:
            season = 1

            if '-2nd-' in url: season = 2
            elif '-3rd-' in url: season = 3
            elif '-4th-' in url: season = 4
            elif '-5th-' in url: season = 5
            elif '-6th-' in url: season = 6
            elif '-7th-' in url: season = 7
            elif '-8th-' in url: season = 8
            elif '-9th*' in url: season = 9

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail=thumb,
                                    contentSerieName = SerieName, contentType = 'episode', contentSeason=season, contentEpisodeNumber=epis ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Series recientes<(.*?)</section>')

    matches = re.compile('<article>(.*?)</article>', re.DOTALL).findall(bloque)

    for match in matches:
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')
        if not title: title = scrapertools.find_single_match(match, 'title="(.*?)"')

        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        if not url or not title: continue

        url = url.replace('./', host)

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        title = title.replace('&quot;', '').replace('&amp;', '').replace('&#039;', "'")

        title = title.replace('Japonés', '[COLOR yellowgreen]Japonés[/COLOR]')

        year = scrapertools.find_single_match(title, '(\d{4})')
        if year: title = title.replace('(' + year + ')', '')
        else: year = '-'

        SerieName = corregir_SerieName(title) 

        season = scrapertools.find_single_match(url, '-season-(.*?)$')

        if not season:
            season = 1

            if '-2nd-' in url: season = 2
            elif '-3rd-' in url: season = 3
            elif '-4th-' in url: season = 4
            elif '-5th-' in url: season = 5
            elif '-6th-' in url: season = 6
            elif '-7th-' in url: season = 7
            elif '-8th-' in url: season = 8
            elif '-9th*' in url: season = 9

        title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb,
                                    contentType='tvshow', contentSerieName=SerieName, contentSeason=season, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    if not item.data_i:
        data = do_downloadpage(item.url)

        data_i = scrapertools.find_single_match(data, 'data-i="(.*?)"')
        data_u = scrapertools.find_single_match(data, 'data-u="(.*?)"')
    else:
        data_i = item.data_i
        data_u = item.data_u

    if not data_i or not data_u: return itemlist

    if not item.tot_epis: tot_epis = scrapertools.find_single_match(data, 'data-e="(.*?)"')
    else: tot_epis = item.tot_epis

    if not item._pag: _pag = 1
    else: _pag = item._pag

    headers = {'Referer': item.url, 'X-Requested-With': 'XMLHttpRequest'}

    post = {'acc': 'episodes', 'i': data_i, 'u': data_u, 'p': _pag}

    data = do_downloadpage(host + 'ajax_pagination', post = post, headers = headers )

    matches = re.compile('<article>(.*?)</article>', re.DOTALL).findall(str(data))

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('MonosChinos', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('MonosChinos', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MonosChinos', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MonosChinos', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MonosChinos', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MonosChinos', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('MonosChinos', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        epis = scrapertools.find_single_match(match, 'alt=".*?episodio(.*?)"').strip()
        if not epis: epis = 1

        title = 'Capítulo ' + str(epis)

        if item.contentSerieName: titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName
        else: titulo = item.title

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason=item.contentSeason, contentEpisodeNumber=epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(itemlist) >= 50:
            try:
               tot_epis = int(tot_epis)
            except:
               tot_epis = 50

            if tot_epis > 50:
                if len(itemlist) >= 50:					
                    _pag += 1

                    itemlist.append(item.clone( title="Siguientes ...", action="episodios", data_i = data_i, data_u = data_u,
                                                tot_epis = tot_epis, _pag = _pag,
                                                page = 0, perpage = 50, text_color='coral' ))

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
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    lng = 'Vo'

    if 'castellano' in item.url: lng = 'Esp'
    elif 'latino' in item.url: lng = 'Lat'

    matches = re.compile('target="_blank" href="(.*?)"', re.DOTALL).findall(data)

    ses = 0

    for url in matches:
        if not url: continue

        ses += 1

        if '/rpmplayer.' in url: continue

        servidor = servertools.get_server_from_url(url)

        servidor = servertools.corregir_servidor(servidor)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)
        elif servidor == 'zures': other = servertools.corregir_zures(url)

        itemlist.append(Item( channel = item.channel, action = 'play', url = url, server = servidor, title = '', language = lng, other = other ))

    # ~ Encrypt
    encrypt = scrapertools.find_single_match(data, 'data-encrypt="(.*?)"')

    if encrypt:
        headers = {'Referer': item.url, 'X-Requested-With': 'XMLHttpRequest'}

        post = {'acc': 'opt', 'i': encrypt}

        data = do_downloadpage(host + 'ajax_pagination', post = post, headers = headers )

        matches = re.compile('data-player="(.*?)"', re.DOTALL).findall(data)

        for url in matches:
            ses += 1

            if not url: continue

            url = base64.b64decode(url).decode("utf-8")

            if '/rpmplayer.' in url: continue

            servidor = servertools.get_server_from_url(url)

            servidor = servertools.corregir_servidor(servidor)

            if servertools.is_server_available(servidor):
                if not servertools.is_server_enabled(servidor): continue
            else:
                if not config.get_setting('developer_mode', default=False): continue

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)
            elif servidor == 'zures': other = servertools.corregir_zures(url)

            itemlist.append(Item( channel = item.channel, action = 'play', url = url, server = servidor, title = '', language = lng, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if 'OVA' in SerieName: SerieName = SerieName.split("OVA")[0]
    if 'Doblaje' in SerieName: SerieName = SerieName.split("Doblaje")[0]
    if 'La película' in SerieName: SerieName = SerieName.split("La película")[0]

    if ' Parte ' in SerieName: SerieName = SerieName.split(" Parte ")[0]
    if ' Part ' in SerieName: SerieName = SerieName.split(" Part ")[0]

    if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
    if 'season' in SerieName: SerieName = SerieName.split("season")[0]

    if ' Temporada' in SerieName: SerieName = SerieName.split(" Temporada")[0]

    if 'Capítulo' in SerieName: SerieName = SerieName.split("Capítulo")[0]
    if 'Capitulo' in SerieName: SerieName = SerieName.split("Capitulo")[0]
    if 'capítulo' in SerieName: SerieName = SerieName.split("capítulo")[0]
    if 'capitulo' in SerieName: SerieName = SerieName.split("capitulo")[0]

    if 'Castellano' in SerieName: SerieName = SerieName.split("Castellano")[0]
    if 'Latino' in SerieName: SerieName = SerieName.split("Latino")[0]
    if 'Japonés' in SerieName: SerieName = SerieName.split("Japonés")[0]

    if ' S1 ' in SerieName: SerieName = SerieName.split(" S1 ")[0]
    elif ' S2 ' in SerieName: SerieName = SerieName.split(" S2 ")[0]
    elif ' S3 ' in SerieName: SerieName = SerieName.split(" S3 ")[0]
    elif ' S4 ' in SerieName: SerieName = SerieName.split(" S4 ")[0]
    elif ' S5 ' in SerieName: SerieName = SerieName.split(" S5 ")[0]
    elif ' S6 ' in SerieName: SerieName = SerieName.split(" S6 ")[0]
    elif ' S7 ' in SerieName: SerieName = SerieName.split(" S7 ")[0]
    elif ' S8 ' in SerieName: SerieName = SerieName.split(" S8 ")[0]
    elif ' S9 ' in SerieName: SerieName = SerieName.split(" S9 ")[0]

    if ' T1 ' in SerieName: SerieName = SerieName.split(" T1 ")[0]
    elif ' T2 ' in SerieName: SerieName = SerieName.split(" T2 ")[0]
    elif ' T3 ' in SerieName: SerieName = SerieName.split(" T3 ")[0]
    elif ' T4 ' in SerieName: SerieName = SerieName.split(" T4 ")[0]
    elif ' T5 ' in SerieName: SerieName = SerieName.split(" T5 ")[0]
    elif ' T6 ' in SerieName: SerieName = SerieName.split(" T6 ")[0]
    elif ' T7 ' in SerieName: SerieName = SerieName.split(" T7 ")[0]
    elif ' T8 ' in SerieName: SerieName = SerieName.split(" T8 ")[0]
    elif ' T9 ' in SerieName: SerieName = SerieName.split(" T9 ")[0]

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
        item.url = host + 'animes?buscar=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

