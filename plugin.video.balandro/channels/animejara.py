# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://animejara.com/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'catalogo', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host + 'inicio', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Últimos animes', action = 'list_last', url = host + 'inicio', search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'catalogo?paged=1&tipo=serie&estado=Emision', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'catalogo?paged=1&tipo=serie&estado=Finalizado', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'catalogo?paged=1&tipo=pelicula', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'En castellano', action = 'list_all', url = host + 'catalogo?idioma=castellano', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'En japonés', action = 'list_all', url = host + 'catalogo?idioma=japones', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'En latino', action = 'list_all', url = host + 'catalogo?idioma=latino', text_color = 'moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    url_gen = host + 'catalogo'

    data = do_downloadpage(url_gen)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    bloque = scrapertools.find_single_match(data, 'Género<(.*?)</select>')

    matches = scrapertools.find_multiple_matches(bloque, '<option value="(.*?)".*?>(.*?)</option>')

    for gen, title in matches:
        if title == 'Todos': continue

        title = title.replace('&amp;', '&')

        url = url_gen + '?tag=' + gen

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='springgreen' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    url_anio = url = host + 'catalogo'

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1984, -1):
        url = url_anio + '?anio=' + str(x)

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color='springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    bloque = scrapertools.find_single_match(data, 'id="anime-results">(.*?)</main>')

    matches = scrapertools.find_multiple_matches(bloque, '<div class="anime-card-wrapper">(.*?)</h3></a></div>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, '<h3 class="card-title">(.*?)$')

        if not title: title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        title = title.replace('#8217;', "'").replace('#8211;', '')

        nro_season = ''
        if 'Temporada' in title:
            nro_season = scrapertools.find_single_match(title, 'Temporada (.*?) ').strip()
            if nro_season: nro_season = ' T' + nro_season

        title = title.replace('#8217;', "'").replace('#8211;', '')

        year = scrapertools.find_single_match(match, '<span class="card-year">(.*?)</span>')

        if not year: year = '-'

        _year = scrapertools.find_single_match(title, '(\d{4})')
        if _year: title = title.replace('(' + _year + ')', '').strip()

        SerieName = corregir_SerieName(title)

        thumb = scrapertools.find_single_match(match, '<div class="card-poster-wrapper">.*?<img src="(.*?)"')

        tipo = 'movie' if '/movie/' in url else 'tvshow'
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

            PeliName = title.strip()

            if 'Movie' in PeliName: PeliName = PeliName.split("Movie")[0]

            PeliName = PeliName.replace('Peliculas', '').replace('Pelicula', '').strip()

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=PeliName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data,'<ul class="paginacion">.*?class="current">.*?data-page="(.*?)"')

        ##########temlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'catalogo?paged=1&tipo=pelicula'
        ####https://animejara.com/catalogo?paged=2

        if next_page:
            _url = item.url

            _urlt = scrapertools.find_single_match(item.url, '&tipo=(.*?)$')

            if '?paged=': _url = _url.split("?paged=")[0]
            elif '&paged=': _url = _url.split("&paged=")[0]

            if _urlt: _url = host + 'catalogo?' + _urlt

            if not '?' in _url:
                url = _url + '?paged=' + next_page
            else:
                url = _url + '&paged=' + next_page

            itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = url, text_color = 'coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Últimos Episodios<(.*?)</section>')

    patron = '<a href="(.*?)".*?<span class="ep-tag">(.*?)</span>.*?<img data-src="(.*?)".*?alt="(.*?)"'

    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for url, temp_epis, thumb, title in matches:
        title = title.replace('#8217;', "'").replace('#8211;', '')

        SerieName = title

        if 'Temporada' in title: SerieName = title.split("Temporada")[0]

        SerieName = SerieName.strip()

        temp = scrapertools.find_single_match(temp_epis, '(.*?)x')
        if not temp: temp = 1

        epis = scrapertools.find_single_match(temp_epis, 'x(.*?)$')
        if not epis: epis = 1

        titulo = '[COLOR tan]Temp. [/COLOR]%s [COLOR goldenrod]Epis. [/COLOR]%s %s' % (str(temp), str(epis), title)

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail=thumb, infoLabels={'year': '-'},
                                    contentSerieName = SerieName, contentType = 'episode', contentSeason=temp, contentEpisodeNumber=epis))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Últimas Temporadas<(.*?)</section>')

    matches = re.compile('<a href="(.*?)".*?<img data-src="(.*?)".*?alt="(.*?)"', re.DOTALL).findall(bloque)

    for url, thumb, title in matches:
        title = title.replace('#8217;', "'").replace('#8211;', '')

        _year = scrapertools.find_single_match(title, '(\d{4})')
        if _year: title = title.replace('(' + _year + ')', '').strip()

        SerieName = corregir_SerieName(title)

        PeliName = SerieName

        tipo = 'movie' if '/movie/' in url else 'tvshow'

        if tipo == 'tvshow':
            titulo = title

            if '#season-' in url:
                nro_season = scrapertools.find_single_match(url, '#season-(.*?)$').strip()

                url = url.split("#season-")[0]

                if not nro_season == '1':
                    titulo = title + ' Season ' + nro_season

                    titulo = titulo.replace(' Season ', '[COLOR tan] Temp. [/COLOR]')

            itemlist.append(item.clone( action='temporadas', url=url, title=titulo, thumbnail=thumb,
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': '-'} ))

        if tipo == 'movie':
            PeliName = title.strip()

            if 'Movie' in PeliName: PeliName = PeliName.split("Movie")[0]

            title = '[COLOR deepskyblue]Film [/COLOR]' + title

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                        contentType='movie', contentTitle=PeliName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    matches = re.compile('data-season="(.*?)"', re.DOTALL).findall(data)


    for season in matches:
        title = 'Temporada ' + season

        if len(matches) == 1:
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

    nexts_caps = ''
    if '>PRÓXIMO EPISODIO:' in data:
        nexts_caps = scrapertools.find_single_match(data, '<div class="fechas-lista">(.*?)</div></div>')

    bloque = scrapertools.find_single_match(str(data), '"numero_temporada":' + str(item.contentSeason) + ',(.*?)}]}')

    matches = re.compile('"numero_episodio":"(.*?)".*?"poster_episodio":"(.*?)"', re.DOTALL).findall(bloque)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('AnimeJara', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('AnimeJara', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeJara', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeJara', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeJara', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeJara', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('AnimeJara', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    if nexts_caps:
        sigtes_caps = scrapertools.find_multiple_matches(nexts_caps, '<div class="proximo-item">.*?<strong>(.*?)</strong>(.*?)</span>')

        for lang_cap, fec_cap in sigtes_caps:
            fec_cap = fec_cap.strip()

            lang_cap = lang_cap.replace('JAPONÉS', 'Japonés').replace('LATINO', 'Latino').replace('CASTELLANO', 'Castellano')

            lang_cap = '[COLOR moccasin]' + lang_cap + '[/COLOR]'

            next_cap = 'Próx. Epis. ' + lang_cap + ' ' + fec_cap

            itemlist.append(item.clone( action='', title = next_cap, thumbnail = item.thumbnail, text_color='cyan'))

    for epis, thumb in matches[item.page * item.perpage:]:
        titulo = '%sx%s %s' % (str(item.contentSeason), str(epis), str(item.contentSerieName))

        thumb = thumb.replace('\/', '/')

        _serie = scrapertools.find_single_match(item.url, '/anime/(.*?)$')
        _serie = _serie.replace('/', '')

        url = host + 'episode/' + _serie + '-' + str(item.contentSeason) + 'x' + str(epis) + '/'

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page=item.page + 1, perpage = item.perpage, text_color='coral' ))

    tmdb.set_infoLabels(itemlist)

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

    lang = scrapertools.find_single_match(data, '<h1 class="Title">(.*?)<span>')
 
    if 'castellano' in lang.lower(): lang = 'Esp'
    elif 'latino' in lang.lower(): lang = 'Lat'
    elif 'subtitulado' in lang.lower(): lang = 'Vose'
    elif 'sub español' in lang.lower(): lang = 'Vose'
    else: lang = 'VO'

    matches = re.compile('<iframe id="iframe-video" src="(.*?)"', re.DOTALL).findall(data)

    if not matches: matches = re.compile('<iframe id="iframe-video-movie" src="(.*?)"', re.DOTALL).findall(data)

    ses = 0

    for url in matches:
        ses += 1

        if '/multiplayer.' in url:
            url2 = url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

            data2 = do_downloadpage(url2)

            data2 = data2.replace('&quot;', '"')

            if ' Castellano -' in data2: lang = 'Esp'
            elif ' Latino -' in data2: lang = 'Lat'
            elif ' Subtitulado -' in data2: lang = 'Vose'
            elif ' Sub -' in data2: lang = 'Vose'
            else: lang = 'VO'

            matches2 = scrapertools.find_multiple_matches(data2, 'playVideo.*?"(.*?)".*?alt="(.*?)"')

            for player, srv in matches2:
                srv = srv.strip().lower()

                servidor = srv

                other = ''

                if srv == 'fembed': continue
                elif srv == 'streamsb': continue
                elif srv == 'nyuu': continue
                elif srv == '4sync': continue
                elif srv == 'upnshare': continue

                if srv == 'netuplayer' or srv == 'netu' or srv == 'hqq': servidor = 'waaw'

                elif srv == 'streamwish': servidor = 'various'
                elif srv == 'streamhg': servidor = 'various'
                elif srv == 'filelions': servidor = 'various'
                elif srv == 'filemoon': servidor = 'various'
                elif srv == 'streamvid': servidor = 'various'
                elif srv == 'vidhide': servidor = 'various'
                elif srv == 'lulustream': servidor = 'various'
                elif srv == 'krakenfiles': servidor = 'various'

                elif srv == 'savefiles':
                      servidor = 'zures'
                      other = srv

                elif srv == 'ok': servidor = 'okru'

                elif srv == 'okru':
                      servidor = 'okru'
                      if 'my.mail.ru' in player: servidor = 'mailru'

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
    elif 'TV' in SerieName: SerieName = SerieName.split("TV")[0]

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

    item.url = host + 'inicio'
    item.search_type = 'tvshow'

    return last_epis(item)


def _news(item):
    logger.info()

    item.url = host + 'inicio'
    item.search_type = 'tvshow'

    return list_last(item)


def search(item, texto):
    logger.info()
    try:
        item.url =  host + 'catalogo/?q=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
