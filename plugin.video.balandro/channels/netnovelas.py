# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


# ~ 17/9/25  Las Pelis NO se tratan NO hay


host = 'https://telennovelas.com/'


def do_downloadpage(url, post=None, headers=None):
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://ennovelas.app/', 'https://ts.ennovelas.net/', 'https://ennovelas.net/',
                'https://enpantallas.one/']

    for ant in ant_hosts:
        url = url.replace(ant, host)

    data = httptools.downloadpage(url, post=post, headers=headers).data

    if not data:
        if not '/?q=' in url:
            if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('NetNovelas', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

            timeout = config.get_setting('channels_repeat', default=30)

            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    if '<title>Just a moment...</title>' in data:
        if not '/?q=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'videos/allseries', page = 1, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host + 'videos/allepisodes', page = 1, search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Por país', action='paises', page = 1, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', page = 1, search_type = 'tvshow' ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    text_color = 'hotpink'

    itemlist.append(item.clone( title = 'América', action = 'list_all', url = host + 'videos/categories/Novelas-Americanas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Australia', action = 'list_all', url = host + 'videos/categories/novelas-australianas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Argentina', action = 'list_all', url = host + 'videos/categories/Novelas-Argentinas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Brasil', action = 'list_all', url = host + 'videos/categories/Novelas-brasilenas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Canada', action = 'list_all', url = host + 'videos/categories/Novelas-Canadienses', text_color=text_color ))
    itemlist.append(item.clone( title = 'Chile', action = 'list_all', url = host + 'videos/categories/Novelas-Chileanas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Colombia', action = 'list_all', url = host + 'videos/categories/Novelas-Colombianas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Corea', action = 'list_all', url = host + 'videos/categories/Novelas-Coreanas', text_color=text_color ))
    itemlist.append(item.clone( title = 'España', action = 'list_all', url = host + 'videos/categories/Novelas-Espanolas', lang = 'Esp', text_color=text_color ))
    itemlist.append(item.clone( title = 'Finlandia', action = 'list_all', url = host + 'videos/categories/Novelas-Finlandesas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Francia', action = 'list_all', url = host + 'videos/categories/novelas-francesiano', text_color=text_color ))
    itemlist.append(item.clone( title = 'Holanda', action = 'list_all', url = host + 'videos/categories/Novelas-Holandes', text_color=text_color ))
    itemlist.append(item.clone( title = 'India', action = 'list_all', url = host + 'videos/categories/Novelas-Indias', text_color=text_color ))
    itemlist.append(item.clone( title = 'Italia', action = 'list_all', url = host + 'videos/categories/Novelas-Italianas', text_color=text_color ))
    itemlist.append(item.clone( title = 'México', action = 'list_all', url = host + 'videos/categories/Novelas-Mexicanas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Noruega', action = 'list_all', url = host + 'videos/categories/Novela-Noruegos', text_color=text_color ))
    itemlist.append(item.clone( title = 'Perú', action = 'list_all', url = host + 'videos/categories/Novelas-Peruanas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Polonia', action = 'list_all', url = host + 'videos/categories/novelas-polacas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Portugal', action = 'list_all', url = host + 'videos/categories/Novelas-portuguesas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Reino Unido', action = 'list_all', url = host + 'videos/categories/Novelas-del-Reino-Unido', text_color=text_color ))
    itemlist.append(item.clone( title = 'Sudafrica', action = 'list_all', url = host + 'videos/categories/Novelas-de-Sudafrica', text_color=text_color ))
    itemlist.append(item.clone( title = 'Suecia', action = 'list_all', url = host + 'videos/categories/Novelas-suecas', text_color=text_color ))

    itemlist.append(item.clone( title = 'Tuquía', action = 'list_all', url = host + 'videos/categories/Series-y-Novelas-Turcas', text_color=text_color ))
    itemlist.append(item.clone( title = 'Tuquía (Vose)', action = 'list_all', url = host + 'videos/categories/Series-Turcas-en-Espanol-Subtitulado', text_color=text_color ))
    itemlist.append(item.clone( title = 'Tuquía (Esp)', action = 'list_all', url = host + 'videos/categories/Series-Turcas-en-Espanol-Audio', text_color=text_color ))

    itemlist.append(item.clone( title = 'Venezuela', action = 'list_all', url = host + 'videos/categories/novelas-venezolanas', text_color=text_color ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1979, -1):
        url = host + 'videos/years/' + str(x)

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color='hotpink' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    data = data.replace('=\\', '=').replace('\\"', '"')

    bloque = scrapertools.find_single_match(data, '>Browse(.*?)</body>')

    matches = scrapertools.find_multiple_matches(str(bloque), '"video"(.*?),null,')

    for match in matches:
        match = match.replace('\\/', '/')

        url = scrapertools.find_single_match(match, '"videoSlug":"(.*?)"')

        title = scrapertools.find_single_match(match, '"videoTitle":"(.*?)"')

        if not url or not title: continue

        if '/?q=' in item.url:
            if 'Capitulo' in title: pass
            elif 'Capítulo' in title: pass
            elif 'capitulo' in title: pass
            elif 'capítulo' in title: pass
            else: continue

        thumb = scrapertools.find_single_match(match, '"ytThumb":"(.*?)"')

        thumb = host + 'videoimage/' + thumb

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

        if '/?q=' in item.url:
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

                continue

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

        title = title.replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]')

        url = host + 'videos/' + url

        itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb,
                                    contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if item.page:
            if '?page=' in item.url: item.url = item.url.split("?page=")[0]

            item.page = item.page + 1

            next_page = item.url + '?page=' + str(item.page)

            itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, page = item.page, action = 'list_all', text_color = 'coral' ))

        else:
            next_page = scrapertools.find_single_match(data, '</div><a class="rounded-md px-3 py-1 hover:bg-muted/80 bg-muted" aria-disabled="false".*?href="(.*?)"')

            if next_page:
                next_page = next_page.replace('&amp;', '&').strip()

                if '&page=' in next_page:
                    next_page = host[:-1] + next_page

                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    data = data.replace('=\\', '=').replace('\\"', '"')

    bloque = scrapertools.find_single_match(data, '>Seasons and Episodes<(.*?)</div></div></div></div>')

    bloque = bloque.replace('<!-- -->', '"').replace('</span></button>', '"')

    matches = re.compile('>Season "(.*?)</span>', re.DOTALL).findall(bloque)

    for numtempo in matches:
         numtempo = numtempo.strip()

         title = 'Temporada ' + numtempo

         if len(matches) == 1:
             if not numtempo:
                 itemlist.append(item.clone( action = 'findvideos', url = item.url, title = item.title,
                                             contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = item.contentEpisodeNumber ))

                 return itemlist

             if config.get_setting('channels_seasons', default=True):
                 platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title +  '[/COLOR]')

             item.page = 0
             item.contentType = 'season'
             item.contentSeason = numtempo
             item.only_one_season = True
             itemlist = episodios(item)
             return itemlist

         itemlist.append(item.clone( action = 'episodios', title=title, page=0,
                                     contentType='season', contentSeason=numtempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    data = data.replace('=\\', '=').replace('\\"', '"')

    data = data.replace('<!-- -->', '"').replace('</span></button>', '"')

    if item.only_one_season:
       bloque = scrapertools.find_single_match(str(data), '>Season "' + str(item.contentSeason) + '(.*?)</section>')
    else:
       bloque = scrapertools.find_single_match(str(data), '(.*?)</body>')

    matches = re.compile('<a aria-label="(.*?)".*?href="(.*?)"', re.DOTALL).findall(str(bloque))

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

    for title, url in matches[item.page * item.perpage:]:
        if '/years' in url: continue
        elif '/categories/' in url: continue
        elif '/aboutus' in url: continue
        elif 'Breadcrumb' in url: continue

        if not item.only_one_season:
            if not str(item.contentSeason) == '1':
                if not url.endswith('-1'): continue
            else:
                if url.endswith('-1'): continue

        url = host[:-1] + url

        epis = scrapertools.find_single_match(title, 'Episode(.*?)$').strip()
        if not epis: epis = 1

        if ' Capítulo' in title: title = title.split(" Capítulo")[0]
        elif ' capítulo' in title: title = title.split(" capítulo")[0]
        elif ' Capitulo' in title: title = title.split(" Capitulo")[0]
        elif ' capitulo' in title: title = title.split(" capitulo")[0]

        title = title.replace(item.contentSerieName, '').strip()

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title.replace(' - ', ' ').strip()

        if ' Capítulo' in titulo: titulo = titulo.split(" Capítulo")[0]
        elif ' capítulo' in titulo: titulo = titulo.split(" capítulo")[0]
        elif ' Capitulo' in titulo: titulo = titulo.split(" Capitulo")[0]
        elif ' capitulo' in titulo: titulo = titulo.split(" capitulo")[0]

        titulo = titulo.replace('Temporada', '[COLOR tan]Temp.[/COLOR]')

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

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

    data = data.replace('\\/', '/')

    data = data.replace('=\\', '=').replace('\\"', '/"')

    data = data.replace('\\r', '"').replace('\\n', ' "')

    data = data.replace('\\"', '" ')

    data = data.replace('/"', '"')

    ses = 0

    bloque = scrapertools.find_single_match(data, '"watchServers"(.*?)"downloadServers"')

    matches = scrapertools.find_multiple_matches(bloque, '"(.*?)"')

    for url in matches:
        if not url: continue

        ses += 1

        if '/fembuki.' in url: continue
        elif '/nuuuppp.' in url: continue
        elif '/younetu.' in url: continue

        elif '/argtesa.' in url: continue
        elif '/esprinahy.' in url: continue

        elif '.p2pstream.' in url: continue
        elif '/cuevana.' in url: continue

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

        url = url.replace('\\u0026', '&')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)
        elif servidor == 'zures': other = servertools.corregir_zures(url)

        itemlist.append(Item( channel=item.channel, action = 'play', server = servidor, url = url, language = lang, other = other.capitalize() ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    servidor = item.server

    if url.startswith("https://sb"):
        return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

    elif '/argtesa.' in url or '/esprinahy.' in url:
         return 'Servidor [COLOR tan]No soportado[/COLOR]'

    elif '.p2pstream.' in url: url = ''
    elif '/cuevana.' in url: url = ''

    if '/player.php?h=' in url:
        data = do_downloadpage(url)

        url = scrapertools.find_single_match(data, "var url = '(.*?)'")

        if url:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

    if url:
        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def search(item, texto):
    logger.info()
    try:
       item.url = host + '?q=' + texto.replace(" ", "+")
       return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

