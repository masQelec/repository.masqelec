# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


# ~ 18/4/25  Las Pelis NO se tratan porque hay pocas y SIN enlaces


host = 'https://ts.ennovelas.net/'


perpage = 25


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://ennovelas.net/', 'https://ennovelas.app/']

    for ant in ant_hosts:
        url = url.replace(ant, host)

    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'all-series.php', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host + 'episodes.php', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + 'newvideos.php', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'topvideos.php', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por país', action='paises', search_type = 'tvshow' ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    text_color = 'hotpink'

    itemlist.append(item.clone( title = 'América', action = 'list_all', url = host + 'category.php?cat=Novelas-Americanas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Argentina', action = 'list_all', url = host + 'category.php?cat=Novelas-Argentinas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Brasil', action = 'list_all', url = host + 'category.php?cat=Novelas-brasilenas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Colombia', action = 'list_all', url = host + 'category.php?cat=Novelas-Colombianas', text_color=text_color ))
    itemlist.append(item.clone( title = 'España', action = 'list_all', url = host + 'category.php?cat=Novelas-Espanolas', lang = 'Esp', text_color=text_color ))
    itemlist.append(item.clone( title = 'Francia', action = 'list_all', url = host + 'category.php?cat=novelas-francesiano', text_color=text_color ))
    itemlist.append(item.clone( title = 'México', action = 'list_all', url = host + 'category.php?cat=Novelas-Mexicanas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Perú', action = 'list_all', url = host + 'category.php?cat=Novelas-Peruanas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Polonia', action = 'list_all', url = host + 'category.php?cat=novelas-polacas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Suecia', action = 'list_all', url = host + 'category.php?cat=Novelas-suecas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Tuquía', action = 'list_all', url = host + 'category.php?cat=series-turcas', text_color=text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<div class="thumbnail">(.*?)</li>')

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        if '/search.php?keywords=' in item.url:
            if 'Capitulo' in title: pass
            elif 'Capítulo' in title: pass
            elif 'capitulo' in title: pass
            elif 'capítulo' in title: pass
            else: continue

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        title = title.replace('&#8211;', '').replace('&#8220;', '').replace('&#8221;', '').strip()
        title = title.replace('&#8216;', '').replace('&#8217;', '').replace('&#8230;', '').strip()
        title = title.replace('&#038;', '&').replace('&amp;', '&')

        SerieName = title

        if " (" in SerieName: SerieName = SerieName.split(" (")[0]
        elif "(En Espanol)" in SerieName: SerieName = SerieName.split("(En Espanol)")[0]
        elif "En Espanol" in SerieName: SerieName = SerieName.split("En Espanol")[0]
        elif "En Español" in SerieName: SerieName = SerieName.split("En Español")[0]
        elif "[Español Subtitulado]" in SerieName: SerieName = SerieName.split("[Español Subtitulado]")[0]
        elif "[SUB Espanol]" in SerieName: SerieName = SerieName.split("[SUB Espanol]")[0]

        SerieName = SerieName.strip()

        if "Temporada" in SerieName: SerieName = SerieName.split("Temporada")[0]

        if "Capitulos" in SerieName: SerieName = SerieName.split("Capitulos")[0]
        elif "Capítulos" in SerieName: SerieName = SerieName.split("Capítulos")[0]

        if "Capitulo" in SerieName: SerieName = SerieName.split("Capitulo")[0]
        elif "Capítulo" in SerieName: SerieName = SerieName.split("Capítulo")[0]

        SerieName = SerieName.strip()

        if '/search.php?keywords=' in item.url:
            cap = False
            if 'Capitulos' in title or 'Capítulos' in title: pass
            elif 'Capitulo' in title or 'Capítulo' in title: cap = True

            if cap:
                season = scrapertools.find_single_match(title, 'Temporada(.*?)Capítulo').strip()
                if not season: season = scrapertools.find_single_match(title, 'Temporada(.*?)Capitulo').strip()
                if not season: season = 1

                epis = scrapertools.find_single_match(match, '<span>Cap.*?<span>(.*?)</span>')
                if not epis: epis = 1

                title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

                title = title.replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]')

                itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                            contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis, infoLabels={'year': '-'} ))

                if len(itemlist) >= perpage: break

                continue

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

        title = title.replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]')

        itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                    contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        buscar_next = True
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='Siguientes ...', page=item.page + 1, pagina = item.pagina, action='list_all', text_color='coral' ))
                buscar_next = False

        if buscar_next:
            if '<ul class="pagination' in data:
                next_page = scrapertools.find_single_match(data, '<ul class="pagination.*?<li class="active">.*?</a>.*?href="(.*?)"')

                if next_page:
                    if '&page=' in next_page:
                        next_page = host + next_page

                        itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, page = 0, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<button class="tablinks.*?' + "'Season(.*?)'" + '.*?">Temporada(.*?)</button>', re.DOTALL).findall(data)


    for id_season, numtempo in matches:
        numtempo = numtempo.strip()

        title = 'Temporada ' + numtempo

        if len(matches) == 1:
            if not numtempo:
                itemlist.append(item.clone( action = 'findvideos', url = item.url, title = item.title,
                                            contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = item.contentEpisodeNumber ))

                return itemlist

            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.id_season = id_season
            item.contentType = 'season'
            item.contentSeason = numtempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title=title, id_season=id_season, page=0, contentType='season', contentSeason=numtempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div id="Season' + item.id_season + '".*?class="tabcontent"(.*?)</div>')

    matches = re.compile('<a href="(.*?)".*?title="(.*?)"', re.DOTALL).findall(bloque)

    num_matches = len(matches)

    if item.page == 0 and item.perpage == 50:
        sum_parts = num_matches

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('NetNovelas', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('NetNovelas', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('NetNovelas', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('NetNovelas', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('NetNovelas', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('NetNovelas', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('NetNovelas', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, title in matches[item.page * item.perpage:]:
        title = title.replace('&#8211;', '').strip()

        epis = scrapertools.find_single_match(title, 'Capitulo(.*?)$').strip()
        if not epis: epis = 1

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

        title = title.replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]')

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo,
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

    if item.lang == 'Esp': lang = 'Esp'
    else: lang = 'Lat'

    data = do_downloadpage(item.url)

    ses = 0

    matches = scrapertools.find_multiple_matches(data, '<a class="xtgo" href="(.*?)"')

    for url in matches:
        ses += 1

        data = do_downloadpage(url)

        links = scrapertools.find_multiple_matches(data, 'id="server_.*?' + "iframe src='(.*?)'.*?</iframe>")

        for link in links:
            url = link

            if '/esprinahy.' in url: continue
            elif '/nuuuppp.' in url: continue
            elif '/younetu.' in url: continue

            if 'api.mycdn.moe/uqlink.php?id=' in url: url = url.replace('api.mycdn.moe/uqlink.php?id=', 'uqload.com/embed-')

            elif 'api.mycdn.moe/dourl.php?id=' in url: url = url.replace('api.mycdn.moe/dourl.php?id=', 'dood.to/e/')

            elif 'api.mycdn.moe/dl/?uptobox=' in url: url = url.replace('api.mycdn.moe/dl/?uptobox=', 'uptobox.com/')

            elif url.startswith('http://vidmoly/'): url = url.replace('http://vidmoly/w/', 'https://vidmoly/embed-').replace('http://vidmoly/', 'https://vidmoly/')

            elif url.startswith('https://sr.ennovelas.net/'): url = url.replace('/sr.ennovelas.net/', '/waaw.to/')
            elif url.startswith('https://sr.ennovelas.watch/'): url = url.replace('/sr.ennovelas.watch/', '/waaw.to/')
            elif url.startswith('https://w.ennovelas.net/'): url = url.replace('/w.ennovelas.net/', '/waaw.to/')
            elif url.startswith('https://w.ennovelas.watch/'): url = url.replace('/w.ennovelas.watch/', '/waaw.to/')
            elif url.startswith('https://video.ennovelas.net/'): url = url.replace('/video.ennovelas.net/', '/waaw.to/')
            elif url.startswith('https://reproductor.telenovelas-turcas.com.es/'): url = url.replace('/reproductor.telenovelas-turcas.com.es/', '/waaw.to/')
            elif url.startswith('https://novelas360.cyou/player/'): url = url.replace('/novelas360.cyou/player/', '/waaw.to/')
            elif url.startswith('https://novelas360.cyou/'): url = url.replace('/novelas360.cyou/', '/waaw.to/')

            elif url.startswith('https://vidspeeds.com:2096/'): url = url.replace('/vidspeeds.com:2096/', '/vidspeeds.com/')

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            other = ''

            if servidor == 'various': other = servertools.corregir_other(link)

            itemlist.append(Item( channel=item.channel, action = 'play', server = servidor, url = url, language = lang, other = other.capitalize() ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
       item.url = host + 'search.php?keywords=' + texto.replace(" ", "+")
       return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

