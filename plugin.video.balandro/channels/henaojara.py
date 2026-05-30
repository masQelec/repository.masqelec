# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://henaojara.com/'


def do_downloadpage(url, post=None, headers=None):
    if not url: return ''

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'view/category/categorias/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host, search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Últimos animes', action = 'list_last', url = host, search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'view/category/estrenos/?tr_post_type=2', search_type = 'tvshow', text_color = 'greenyellow' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'view/category/emision/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'view/category/pelicula/', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'En castellano', action = 'list_all', url = host + 'view/category/categorias/espanol-castellano/', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'En latino', action = 'list_all', url = host + 'view/category/categorias/latino/', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Subtitulado', action = 'list_all', url = host + 'view/category/categorias/subtitulos/', text_color = 'moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    bloque = scrapertools.find_single_match(data, '<div id="categories-3"(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?>(.*?)</a>')

    for url, title in matches:
        if title == 'EMISION': continue
        elif title == 'ESTRENOS': continue
        elif title == 'PELICULAS': continue

        elif 'ESPAÑOL CASTELLANO' in title: continue
        elif 'ESPAÑOL LATINO' in title: continue
        elif 'ESPAÑOL SUBTITULADO' in title: continue

        title = title.replace('&amp;', '&')

        title = title.lower()
        title = title.capitalize()

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='springgreen' ))

    if not itemlist:
        if '>Crear cuenta<' in data:
            platformtools.dialog_ok(config.__addon_name + ' HenaOjara', '[COLOR cyan][B]Para Acceder a los Contenidos, a partir del [COLOR yellow]1/12/2025[/B][/COLOR]', '[COLOR red][B]La Web Obliga a Registrarse.[/B][/COLOR]')
            return

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')
        title = scrapertools.find_single_match(match, '<h3 class="Title">(.*?)</h3>')

        if not url or not title: continue

        title = title.replace('#8217;', "'").replace('#8211;', '')

        nro_season = ''
        if 'Temporada' in title:
            nro_season = scrapertools.find_single_match(title, 'Temporada (.*?) ').strip()
            if nro_season: nro_season = ' T' + nro_season

        title = title.replace('#8217;', "'").replace('#8211;', '')

        year = scrapertools.find_single_match(title, '(\d{4})')
        if year: title = title.replace('(' + year + ')', '').strip()

        SerieName = corregir_SerieName(title)

        thumb = scrapertools.find_single_match(match, ' src="(.*?)"')

        tipo = 'movie' if '>PELICULA<' in match or '>Pelicula' in match or '-movie-' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            titulo = title + nro_season

            titulo = titulo.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]').replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

            itemlist.append(item.clone( action = 'temporadas', url= url, title=titulo, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': '-'} ))

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            PeliName = re.sub(r"Sub |Español|Latino|Castellano|HD|Temporada \d+|\(\d{4}\)", "", title).strip()

            if 'Movie' in PeliName: PeliName = PeliName.split("Movie")[0]

            PeliName = PeliName.replace('Peliculas', '').replace('Pelicula', '').strip()

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=PeliName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data,'<link rel="next" href="(.*?)"')

        if next_page:
            itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

    if not itemlist:
        if not '/?s=' in item.url:
            if '>Crear cuenta<' in data:
                platformtools.dialog_ok(config.__addon_name + ' HenaOjara', '[COLOR cyan][B]Para Acceder a los Contenidos, a partir del [COLOR yellow]1/12/2025[/B][/COLOR]', '[COLOR red][B]La Web Obliga a Registrarse.[/B][/COLOR]')
                return

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Últimos Animes<(.*?)>Últimos Episodios<')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, '<h3 class="Title">(.*?)</h3>')

        if not url or not title: continue

        title = title.replace('#8217;', "'").replace('#8211;', '')

        year = scrapertools.find_single_match(match, '<span class="Year">.*?-(.*?)</span>').strip()
        if not year: year = scrapertools.find_single_match(title, '(\d{4})')

        if year: title = title.replace('(' + year + ')', '').strip()
        else: year = '-'

        SerieName = corregir_SerieName(title)

        PeliName = SerieName

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        epis = scrapertools.find_single_match(match, '<span class="ClB">(.*?)</span>')

        tipo = 'movie' if epis == '0' else 'tvshow'

        if tipo == 'tvshow':
            temp = scrapertools.find_single_match(url, '/season/.*?hd-(.*?)/')
            if not temp: temp = 1

            title = 'Temporada ' + str(temp) + ' ' + title

            title = title.replace('Temporada', '[COLOR goldenrod]Temp.[/COLOR]')

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': year} ))

        if tipo == 'movie':
            PeliName = re.sub(r"Sub |Español|Latino|Castellano|HD|Temporada \d+|\(\d{4}\)", "", title).strip()

            if 'Movie' in PeliName: PeliName = PeliName.split("Movie")[0]

            PeliName = PeliName.replace('Peliculas', '').replace('Pelicula', '').strip()

            title = '[COLOR deepskyblue]Film [/COLOR]' + title

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                        contentType='movie', contentTitle=PeliName, infoLabels={'year': year} ))

    if not itemlist:
        if '>Crear cuenta<' in data:
            platformtools.dialog_ok(config.__addon_name + ' HenaOjara', '[COLOR cyan][B]Para Acceder a los Contenidos, a partir del [COLOR yellow]1/12/2025[/B][/COLOR]', '[COLOR red][B]La Web Obliga a Registrarse.[/B][/COLOR]')
            return

    tmdb.set_infoLabels(itemlist)

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Últimos Episodios<(.*?)</section>')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, '<h3 class="Title">(.*?)</h3>')

        if not url or not title: continue

        title = title.replace('#8217;', "'").replace('#8211;', '')

        SerieName = title

        if 'Temporada' in title: SerieName = title.split("Temporada")[0]
        if 'Movie' in title: SerieName = title.split("Movie")[0]

        SerieName = re.sub(r"Sub |Español|Latino|Castellano|HD|Temporada \d+|\(\d{4}\)", "", SerieName).strip()
        SerieName = SerieName.replace('Español Latino HD', '').replace('Español Castellano HD', '').replace('Sub Español HD', '').strip()
        SerieName = SerieName.strip()

        temp = scrapertools.find_single_match(match, '<span class="ClB">(.*?)x')
        if not temp: temp = 1

        epis = scrapertools.find_single_match(match, '<span class="ClB">.*?x(.*?)</span>')
        if not epis: epis = 1

        if not str(temp) == '1': title = 'Episodio ' + str(temp) + 'x' + str(epis) + ' ' + title
        else: title = 'Episodio ' + str(epis) + ' ' + title

        title = title.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]')

        if 'Pelicula' in title: title = title.replace('Pelicula', '[COLOR deepskyblue]Pelicula[/COLOR]')

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        thumb = 'https:' + thumb

        year = scrapertools.find_single_match(match, '<span class="Year">.*?,(.*?)</span>').strip()

        if not year: year = '-'

        itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail=thumb, infoLabels={'year': year},
                                    contentSerieName = SerieName, contentType = 'episode', contentSeason=temp, contentEpisodeNumber=epis))

    if not itemlist:
        if '>Crear cuenta<' in data:
            platformtools.dialog_ok(config.__addon_name + ' HenaOjara', '[COLOR cyan][B]Para Acceder a los Contenidos, a partir del [COLOR yellow]1/12/2025[/B][/COLOR]', '[COLOR red][B]La Web Obliga a Registrarse.[/B][/COLOR]')
            return

    tmdb.set_infoLabels(itemlist)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    hay_estreno = False
    if '>ESTRENO:' in data or '>Estreno:' in data: hay_estreno = True

    if hay_estreno:
        fec_estreno = scrapertools.find_single_match(data, '>ESTRENO:(.*?)<').strip()
        if not fec_estreno: fec_estreno = scrapertools.find_single_match(data, '>Estreno:(.*?)<').strip()

        if fec_estreno:
            platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Proximamente[/B][/COLOR]')

            fec_estreno = 'Estreno: ' + fec_estreno
            itemlist.append(item.clone( action='', title = fec_estreno, thumbnail = item.thumbnail, text_color='cyan', infoLabels={'year': ''} ))

            return itemlist

    if '>PELICULA<' in data or '>Pelicula' in data or '-movie-' in item.url:
        peli = scrapertools.find_single_match(data, '<span class="Num">.*?<a href="(.*?)"')

        itemlist.append(item.clone( action='findvideos', url = peli, title = '[COLOR yellow]Servidores[/COLOR] ' + item.title,
                                    thumbnail = item.thumbnail, contentType='movie', contentTitle=item.title, text_color='tan' ))

        return itemlist

    elif '<div class="TPlayer">' in data:
        itemlist.append(item.clone( action='findvideos', url = item.url, title = '[COLOR yellow]Servidores[/COLOR] ' + item.title,
                                    thumbnail = item.thumbnail, contentType='tvshow', contentTitle=item.title, text_color='tan' ))

        return itemlist

    if '<div class="snslst">' in data:
        bloque = scrapertools.find_single_match(data, '<div class="snslst">(.*?)</tbody>')

        matches = re.compile('<a href="(.*?)".*?class="Button STPb.*?>Temporada <span>(.*?)</span>', re.DOTALL).findall(bloque)


        for url, season in matches:
            title = 'Temporada ' + season

            if len(matches) == 1:
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]Una Temporada[/COLOR]')
                item.url = url
                item.page = 0
                item.contentType = 'season'
                item.contentSeason = season
                itemlist = episodios(item)
                return itemlist

            itemlist.append(item.clone( action = 'episodios', title = title, url = url, page = 0, contentType = 'season', contentSeason = season, text_color='tan' ))

    elif 'data-tab="' in data:
        matches = re.compile('data-tab="(.*?)"', re.DOTALL).findall(data)

        for season in matches:
            title = 'Temporada ' + season

            if len(matches) == 1:
                if config.get_setting('channels_seasons', default=True):
                    platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]Una Temporada[/COLOR]')

                    item.page = 0
                    item.contentType = 'season'
                    item.contentSeason = season
                    itemlist = episodios(item)
                    return itemlist

            itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = season, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    hay_estreno = False
    if '>ESTRENO:' in data or '>Estreno:' in data: hay_estreno = True

    if 'data-tab="' in data:
        bloque = scrapertools.find_single_match(data, 'data-tab="' + str(item.contentSeason) + '"(.*?)</table>')
    else:
        bloque = data

    bloque = bloque.replace('&quot;', '"')

    matches = re.compile('<span class="Num">(.*?)</span>.*?><a href="(.*?)".*?src="(.*?)".*?<td class="MvTbTtl">.*?">(.*?)</a>', re.DOTALL).findall(bloque)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('HenaOjara', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('HenaOjara', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('HenaOjara', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('HenaOjara', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('HenaOjara', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('HenaOjara', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('HenaOjara', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for epis, url, thumb, title in matches[item.page * item.perpage:]:
        next_cap = ''
        if '">Proximo Capitulo' in title:
            next_cap = scrapertools.find_single_match(str(title), '.*?">(.*?)</b>')
            title = scrapertools.find_single_match(title, "(.*?)- <b").strip()

        if '</b>' in title: title = scrapertools.find_single_match(title, "</b>(.*?)$").strip()

        if item.contentSerieName: titulo = '%sx%s %s' % (str(item.contentSeason), epis, str(item.contentSerieName))
        else: titulo = item.title

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            if next_cap:
                next_cap = next_cap.replace('Proximo Capitulo', 'Próx. Epis.')
                itemlist.append(item.clone( action='', title = next_cap, thumbnail = item.thumbnail, text_color='cyan'))
            break

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page=item.page + 1, perpage = item.perpage, text_color='coral' ))

    tmdb.set_infoLabels(itemlist)

    if not itemlist:
        if hay_estreno:
            fec_estreno = scrapertools.find_single_match(data, '>ESTRENO:(.*?)<').strip()
            if not fec_estreno: fec_estreno = scrapertools.find_single_match(data, '>Estreno:(.*?)<').strip()

            if fec_estreno:
                platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Proximamente[/B][/COLOR]')

                fec_estreno = 'Estreno: ' + fec_estreno
                itemlist.append(item.clone( action='', title = fec_estreno, thumbnail = item.thumbnail, text_color='cyan', infoLabels={'year': ''} ))

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
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    if not '/episode/' in item.url:
        if '>PELICULA<' in data or '>Pelicula' in data or '-movie-' in item.url:
            peli = scrapertools.find_single_match(data, '<span class="Num">.*?<a href="(.*?)"')

            peli = peli.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

            if not '/disqus.' in peli: data = do_downloadpage(peli)

    lang = scrapertools.find_single_match(data, '<h1 class="Title">(.*?)<span>')

    if 'castellano' in lang.lower(): lang = 'Esp'
    elif 'latino' in lang.lower(): lang = 'Lat'
    elif 'subtitulado' in lang.lower(): lang = 'Vose'
    elif 'sub español' in lang.lower(): lang = 'Vose'
    else: lang = 'VO'

    matches = re.compile('id="Opt(.*?)">(.*?)</div>', re.DOTALL).findall(data)

    ses = 0

    for option, datos in matches:
        ses += 1

        url = scrapertools.find_single_match(datos, 'src="(.*?)"')
        if not url: url = scrapertools.find_single_match(datos, 'src=&quot;(.*?)&quot;')

        if not url: continue

        other = scrapertools.find_single_match(data, 'data-tplayernv="Opt' + str(option) + '"><span>(.*?)</span>')
        other = other.replace('<strong>', '').replace('</strong>', '')

        other = other.strip().lower()

        if other == 'multiplayer':
            url2 = url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

            data2 = do_downloadpage(url2)

            player = scrapertools.find_single_match(data2, '<iframe.*?src="(.*?)"')

            if player:
                player = player.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&').strip()

                headers = {'Referer': host}
                if player: headers = {'Referer': player}

                data3 = do_downloadpage(player, headers=headers)

                servers = scrapertools.find_single_match(data3, '<div id="lista-server">(.*?)Descargar<')

                servers = servers.replace('&quot;', '"')

                matches3 = scrapertools.find_multiple_matches(servers, 'playVideo.*?"(.*?)".*?alt="(.*?)"')

                for player, srv in matches3:
                    srv = srv.strip().lower()

                    servidor = srv

                    other = ''

                    if srv == 'fembed': continue
                    elif srv == 'streamsb': continue
                    elif srv == 'nyuu': continue
                    elif srv == '4sync': continue

                    if srv == 'netuplayer' or srv == 'netu' or srv == 'hqq': servidor = 'waaw'

                    elif srv == 'streamwish': servidor = 'various'
                    elif srv == 'streamhg': servidor = 'various'
                    elif srv == 'filelions': servidor = 'various'
                    elif srv == 'filemoon': servidor = 'various'
                    elif srv == 'streamvid': servidor = 'various'
                    elif srv == 'vidhide': servidor = 'various'
                    elif srv == 'lulustream': servidor = 'various'

                    elif srv == 'savefiles':
                          servidor = 'zures'
                          other = srv

                    elif srv == 'ok': servidor = 'okru'
                    elif srv == 'dood': servidor = 'doodstream'

                    else:
                       if servertools.is_server_available(servidor):
                           if not servertools.is_server_enabled(servidor): continue
                       else:
                           if not config.get_setting('developer_mode', default=False): continue
                           servidor = 'directo'

                    if not servidor == 'zures':
                        if servidor == 'various': other = servertools.corregir_other(srv)
                        elif not servidor == 'directo': other = ''

                    force_input = ''

                    if other == 'Lulustream': force_input = True

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = player,
                                          language = lang, other = other.capitalize(), force_input = force_input ))

        else:
            servidor = other

            if other == 'fembed': continue
            elif other == 'streamsb': continue
            elif other == '4sync': continue

            if other == 'netuplayer' or other == 'netu' or other == 'hqq': servidor = 'waaw'

            elif other == 'streamwish': servidor = 'various'
            elif other == 'filelions': servidor = 'various'
            elif other == 'filemoon': servidor = 'various'
            elif other == 'streamvid': servidor = 'various'
            elif other == 'vidhide': servidor = 'various'
            elif other == 'lulustream': servidor = 'various'

            elif other == 'savefiles':
                  servidor = 'zures'

            elif other == 'ok': servidor = 'okru'
            elif other == 'dood': servidor = 'doodstream'

            else:
               if servertools.is_server_available(servidor):
                   if not servertools.is_server_enabled(servidor): continue
               else:
                   if not config.get_setting('developer_mode', default=False): continue
                   servidor = 'directo'

            if not servidor == 'zures':
                if servidor == 'various': other = servertools.corregir_other(other)
                elif not servidor == 'directo': other = ''

            force_input = ''

            if other == 'Lulustream': force_input = True

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url,
                                  language = lang, other = other.capitalize(), force_input = force_input ))

    # Descargas No se Tratan

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    host_player = host

    item.url = item.url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

    url = item.url.strip()

    if '/?trdownload=' in url:
        try:
           url = httptools.downloadpage(url, follow_redirects=False).headers['location']
        except:
           url = ''

        if url:
           url = url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

           if '/multiplayer/' in url:
               headers = {'Referer': host}

               data = do_downloadpage(url, headers=headers)

               srv = scrapertools.find_single_match(data, "value = '(.*?)'")

               if srv:
                   data = do_downloadpage(url, post={'servidor': srv}, headers=headers)

                   url = scrapertools.find_single_match(data, '<a href="(.*?)"')
               else: url = ''

               if not url:
                   return 'Tiene [COLOR plum]Acortador[/COLOR] del enlace'

    elif '/go.php?v=' in url:
          url = scrapertools.find_single_match(url, 'v=(.*?)$')

    else:
        data = do_downloadpage(url)

        new_url = scrapertools.find_single_match(data, '<div class="Video">.*?src="(.*?)"').strip()

        if new_url:
            if new_url.startswith('//'): new_url = 'https:' + new_url

            url = new_url

            if '/nyuu.' in new_url:
                new_url = new_url.replace('&amp;', '&').strip()

                data = do_downloadpage(new_url)

                url = scrapertools.find_single_match(data, 'url: "(.*?)"')

                url = url.replace('&amp;', '&').strip()

                if url:
                    itemlist.append(item.clone( url=url, server='directo'))
                    return itemlist

            elif '/player/go.php?v=' in new_url:
                new_url = new_url.replace('/player/go.php?v=', '/player/go-player.php?v=')

                data = do_downloadpage(new_url)

                url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')

                if url.startswith('//'): url = 'https:' + url

    if '/streamium.xyz/' in url: url = ''
    elif '/pelispng.' in url: url = ''
    elif '/pelistop.' in url: url = ''
    elif '/descargas/' in url: url = ''

    if url:
        if '.mystream.' in url:
            return 'Servidor [COLOR tan]Cerrado[/COLOR]'
        elif '.fembed.' in url:
            return 'Servidor [COLOR tan]Cerrado[/COLOR]'

        url = url.replace('&amp;', '&').strip()

        if '/player.streamhj.top/' in url: url = url.replace('/player.streamhj.top/', '/netu.to/')
        elif '/netuplayer.top/' in url: url = url.replace('/netuplayer.top/', '/netu.to/')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone( url=url, server=servidor))

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if 'Capítulo' in SerieName: SerieName = SerieName.split("Capítulo")[0]
    if 'Capitulo' in SerieName: SerieName = SerieName.split("Capitulo")[0]

    if 'Movie' in SerieName: SerieName = SerieName.split("Movie")[0]

    if '(Sin Relleno)' in SerieName: SerieName = SerieName.split("(Sin Relleno)")[0]

    if '(TV)' in SerieName: SerieName = SerieName.split("(TV)")[0]

    SerieName = re.sub(r"Sub |Español|Latino|Castellano|HD|Temporada \d+|\(\d{4}\)", "", SerieName).strip()
    SerieName = SerieName.replace('Español Latino HD', '').replace('Español Castellano HD', '').replace('Sub Español HD', '').strip()

    if 'Temporada' in SerieName: SerieName = SerieName.split("Temporada")[0]

    if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
    if 'season' in SerieName: SerieName = SerieName.split("season")[0]

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


def _epis(item):
    logger.info()

    item.url = host
    item.search_type = 'tvshow'

    return last_epis(item)


def _news(item):
    logger.info()

    item.url = host
    item.search_type = 'tvshow'

    return list_last(item)


def search(item, texto):
    logger.info()
    try:
        item.url =  host + '?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
