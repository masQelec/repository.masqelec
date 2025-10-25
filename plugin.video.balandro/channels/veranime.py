# -*- coding: utf-8 -*-

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://ver-anime.com/'


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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'directorio', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host, group = 'last', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Últimos animes', action = 'list_all', url = host, group = 'news', search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'directorio?status=Finalizado&order=recent', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Sin censura', action = 'list_all', url = host + 'directorio?type[]=Sin+Censura&status=&order=recent', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Cortos', action = 'list_all', url = host + 'directorio?type[]=Corto&status=&order=recent', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Especiales', action = 'list_all', url = host + 'directorio?type[]=Especial&status=&order=recent', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Donghuas', action = 'list_all', url = host + 'directorio?type[]=Donghua&status=&order=recent', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Ovas', action = 'list_all', url = host + 'directorio?type[]=Ova&status=&order=recent', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Onas', action = 'list_all', url = host + 'directorio?type[]=Ona&status=&order=recent', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'directorio?type[]=Pelicula&status=&order=recent', search_type = 'movie', text_color = 'deepskyblue' ))


    itemlist.append(item.clone( title = 'Por género', action = 'generos',  search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    url_genre = host + 'directorio?genero[]='

    data = httptools.downloadpage(url_genre).data

    bloque = scrapertools.find_single_match(data, '>Genero<(.*?)</select>')

    matches = scrapertools.find_multiple_matches(bloque, '<option value="(.*?)".*?>(.*?)</option>')

    for genre, title in matches:
        title = title.replace('&aacute;', 'a').replace('&eacute;', 'e').replace('&iacute;', 'í').replace('&oacute;', 'ó').replace('&uacute;', 'u')

        title = title.strip()

        url = url_genre + genre + '&status=&sort=recent'

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='springgreen' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime

    url_anios = host + 'directorio?anio='

    current_year = int(datetime.today().year)

    for x in range(current_year, 1989, -1):
        url = url_anios + str(x) + '&status=&sort=recent'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color='springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    if item.group == 'last': bloque = scrapertools.find_single_match(data, '>Últimos Episodios<(.*?)>Últimas Peliculas<')
    elif item.group == 'news': bloque = scrapertools.find_single_match(data, '>Últimos Animes<(.*?)</section>')
    else: bloque = data

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, '<h3 class="title">(.*?)</h3>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        title = title.replace('&amp;', '').replace('#039;s', "'s").replace('#039;', '').replace('&quot;', '').strip()

        SerieName = corregir_SerieName(title)

        tipo = 'movie' if '-movie-' in url or '>Pelicula<' in match else 'tvshow'
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

        if item.group == 'last':
            if ':' in SerieName: SerieName = title.split(":")[0]

            epis = 1

            if '- Episodio' in title:
                epis = scrapertools.find_single_match(title, '- Episodio(.*?)$').strip()
                title = title.split("- Episodio")[0]
                title = title.strip()

                SerieName = corregir_SerieName(title)

            titulo = '[COLOR goldenrod]Epis. [/COLOR]' +str(epis) + ' ' + title

            titulo = titulo.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

            itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, infoLabels={'year': '-'},
                                        contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis))
        else:
            if tipo == 'tvshow':
                if item.search_type != 'all':
                    if item.search_type == 'movie': continue

                title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

                itemlist.append(item.clone( action = 'episodios', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                             contentType = 'tvshow', contentSerieName = SerieName, contentSeason = season, infoLabels={'year': '-'} ))

            if tipo == 'movie':
                if item.search_type != 'all':
                    if item.search_type == 'tvshow': continue

                itemlist.append(item.clone( action = 'episodios', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                            contentType = 'movie', contentTitle = SerieName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if item.group == 'last': return itemlist

    if itemlist:
        if '<ul class="pagination">' in data:
            next_page = scrapertools.find_single_match(data,'<li class="page-item active".*?</span>.*?<li class="page-item">.*?href="(.*?)".*?</a>')

            if next_page:
                next_page = next_page.replace('&amp;','&')

                itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = httptools.downloadpage(item.url).data

    bloque = scrapertools.find_single_match(data, ">Listado de episodios<(.*?)</section>")

    episodes = scrapertools.find_multiple_matches(bloque, '</div>.*?href="(.*?)".*?title="(.*?)".*?<img src="(.*?)"')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(episodes)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('VerAnime', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('VerAnime', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VerAnime', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VerAnime', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VerAnime', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('VerAnime', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('VerAnime', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, title, thumb in episodes[item.page * item.perpage:]:
        epi = scrapertools.find_single_match(title, "Episodio(.*?)$").strip()

        if not epi: epi = 1

        if item.contentSerieName:
            titulo = str(item.contentSeason) + 'x' + str(epi) + ' ' + item.contentSerieName
            season = item.contentSeason
        else:
            titulo = item.title
            season = 1

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = epi ))

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

    if not 'var videos =' in data: return itemlist

    videos = eval(scrapertools.find_single_match(data, "var videos = (\[.*?);"))

    ses = 0

    for datos in videos:
        ses += 1

        servidor = datos[0]
        servidor = servidor.lower()

        url = datos[1].replace("\\/", "/")

        if servidor == 'streamium': continue
        elif servidor == 'amus': continue
        elif servidor == 'mepu': continue
        elif servidor == 'streamsb': continue

        if servidor == 'umi':
            url = url.replace("gocdn.html#", "gocdn.php?v=")

            data = httptools.downloadpage(url).data
            url = scrapertools.find_single_match(data, '"file":"(.*?)"')
            url = url.replace("\\/", "/")

        if url:
            if not 'http' in url: url = 'https:' + url

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            link_other = ''

            if config.get_setting('developer_mode', default=False):
                try:
                   link_other = url.split('//')[1]
                   link_other = link_other.split('/')[0]
                except:
                   link_other = url
            else: link_other = url

            link_other = link_other.replace('www.', '').replace('.com', '').replace('.net', '').replace('.org', '').replace('.top', '')
            link_other = link_other.replace('.co', '').replace('.cc', '').replace('.sh', '').replace('.to', '').replace('.tv', '').replace('.ru', '').replace('.io', '')
            link_other = link_other.replace('.eu', '').replace('.ws', '').replace('.sx', '').replace('.nz', '')

            if '/s1.' in url: servidor = ''

            if servidor == 'directo': other = link_other
            else: link_other = ''

            if servidor == 'various': link_other = servertools.corregir_other(url)

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = 'Vose', other = link_other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if not item.server:
        data = httptools.downloadpage(item.url).data

        new_url = scrapertools.find_single_match(data, "window.location.href.*?'(.*?)'")

        if new_url == 'https://goodstream.one/video/embed/': url = ''
        else:
           servidor = servertools.get_server_from_url(new_url)
           servidor = servertools.corregir_servidor(servidor)

           url = new_url

    if url:
        if 'streamium' in url: url = ''
        elif 'amus' in url: url = ''
        elif 'mepu' in url: url = ''
        elif 'streamsb' in url: url = ''
        elif 'umi' in url: url = ''

    if url:
        url = servertools.normalize_url(servidor, url)

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

    if ' Especiales' in SerieName: SerieName = SerieName.split(" Especiales")[0]
    elif ' Especial' in SerieName: SerieName = SerieName.split(" Especial")[0]
    elif ' Specials' in SerieName: SerieName = SerieName.split(" Specials")[0]
    elif ' Special' in SerieName: SerieName = SerieName.split(" Special")[0]

    if 'Movie' in SerieName: SerieName = SerieName.split("Movie")[0]

    if '(TV)' in SerieName: SerieName = SerieName.split(" (TV)")[0]

    if ' Latino' in SerieName: SerieName = SerieName.split(" Latino")[0]
    if ' Japonés' in SerieName: SerieName = SerieName.split(" Japonés")[0]

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
        item.url =  host + "directorio?q=" + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
