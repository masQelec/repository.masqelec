# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


from lib.pyberishaes import GibberishAES
from lib import decrypters


host = 'https://megadede.mobi/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='MegaDedeOficial', folder=False, text_color='chartreuse' ))

    itemlist.append(item.clone( channel='helper', action='show_help_prales', title='[B]Cual es su canal Principal[/B]', pral = True, text_color='turquoise' ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title = 'Animes', action = 'mainlist_animes', text_color = 'springgreen' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'peliculas/populares/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'series/populares/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'animes/', group = 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'animes/populares/', group = 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', group = 'animes', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       text_color = 'hotpink'
       if item.group == 'animes': text_color = 'springgreen'

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>Géneros<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)">(.*?)</a>')

    for url, title in matches:
        if not config.get_setting('mnu_doramas', default=False):
            if title == 'Dorama': continue

        title = title.replace('&amp;', '&')

        url = host[:-1] + url

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = text_color ))

    if itemlist:
        itemlist.append(item.clone( action = 'list_all', title = 'Animación', url = host + 'generos/animacion', text_color = text_color ))
        itemlist.append(item.clone( action = 'list_all', title = 'Bélica', url = host + 'generos/belica', text_color = text_color ))
        itemlist.append(item.clone( action = 'list_all', title = 'Crimen', url = host + 'generos/crimen', text_color = text_color ))
        itemlist.append(item.clone( action = 'list_all', title = 'Documental', url = host + 'generos/documental', text_color = text_color ))
        itemlist.append(item.clone( action = 'list_all', title = 'Familia', url = host + 'generos/familia', text_color = text_color ))
        itemlist.append(item.clone( action = 'list_all', title = 'Guerra', url = host + 'generos/guerra', text_color = text_color ))
        itemlist.append(item.clone( action = 'list_all', title = 'Historia', url = host + 'generos/historia', text_color = text_color ))
        itemlist.append(item.clone( action = 'list_all', title = 'Misterio', url = host + 'generos/misterio', text_color = text_color ))
        itemlist.append(item.clone( action = 'list_all', title = 'Suspense', url = host + 'generos/suspense', text_color = text_color ))
        itemlist.append(item.clone( action = 'list_all', title = 'Western', url = host + 'generos/western', text_color = text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')
        if not title: title = scrapertools.find_single_match(match, '<h2 class="title">(.*?)</h2>').strip()

        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        if not title or not url: continue

        thumb = scrapertools.find_single_match(match, 'src="([^"]+)"')

        year = scrapertools.find_single_match(match, '<span class="inf">(.*?)</span>').strip()

        if year: title = title.replace('(' + year + ')', '').strip()
        else:
            year = scrapertools.find_single_match(title, '(\d{4})')
            if year: title = title.replace('(' + year + ')', '').strip()

        if not year: year = '-'

        c_year = scrapertools.find_single_match(title, '(\d{4})')
        if not c_year: c_year = scrapertools.find_single_match(title, '(d{4})')

        if c_year:
            title = title.replace('(' + c_year + ')', '').strip()
            title = title.replace(' ' + c_year + ' ', '').strip()

        if '/release/' in item.url: year = scrapertools.find_single_match(item.url, "/release/(.*?)/")

        title = title.replace('Ver ', '').replace('online en HD', '').replace('- Película completa', '').replace('- Serie completa', '').replace('- Anime completa', '').strip()

        title = title.replace('&#39;s', "'s").replace('&#039;s', "'s").replace('&#8211;', '').replace('&#039;', "'").replace('&#8230;', ' &').replace('&amp;', '&').replace('&#8217;s', "'").strip()

        if url.startswith("/"): url = host[:-1] + url

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == 'all':
               if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == 'all':
                if item.search_type == 'movie': continue

            if item.group == 'animes':
                if not '/anime/' in url: continue

            itemlist.append(item.clone( action ='temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            bloque = scrapertools.find_single_match(data, '<div class="pagination(.*?)</section>')

            next_page = scrapertools.find_single_match(bloque, '</span>.*?href="(.*?)"')

            if '?page=' in next_page or '&page=' in next_page:
                ant_page = item.url

                num_page = scrapertools.find_single_match(item.url, 'page=.*?page=(.*?)$')

                if num_page:
                    try:
                       num_page = int(num_page) + 1

                       new_page = '?page=' + str(num_page)

                       item.url = item.url.split("?page=")[0]

                       next_page = item.url + new_page
                    except:
                       pass

                else:
                    if '?page=' in ant_page: ant_page = ant_page.split("?page=")[0]
                    elif '&page=' in ant_page: ant_page = ant_page.split("&page=")[0]

                    if next_page.startswith("?"): next_page = ant_page + next_page
                    elif next_page.startswith("&"): next_page = ant_page + next_page

                    elif next_page.startswith("/"): next_page = host[:-1] + next_page

                itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Episodios<(.*?)</div>')

    matches = scrapertools.find_multiple_matches(bloque, 'data-season="(.*?)".*?Temp(.*?)</button>')

    tot_tempo = len(matches)

    if not matches:
        id_season = scrapertools.find_single_match(data, 'data-season="(.*?)"')

        if id_season:
             nro_season = id_season

             if config.get_setting('channels_seasons', default=True):
                 platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]Una temporada[/COLOR]')

                 item.page = 0
                 item.contentType = 'season'
                 item.id_season = id_season
                 item.contentSeason = nro_season
                 itemlist = episodios(item)
                 return itemlist

             itemlist.append(item.clone( action = 'episodios', title = title, page = 0, id_season = id_season,
                                         contentType = 'season', contentSeason = nro_season, text_color='tan' ))

             tmdb.set_infoLabels(itemlist)
             return itemlist

    for id_season, nro_season in matches:
        nro_season = nro_season.strip()

        if tot_tempo > 9:
            if len(nro_season) == 1: nro_season = '0' + nro_season

        title = 'Temporada ' + nro_season

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

                item.page = 0
                item.contentType = 'season'
                item.id_season = id_season
                item.contentSeason = nro_season
                itemlist = episodios(item)
                return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, id_season = id_season,
                                    contentType = 'season', contentSeason = nro_season, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return sorted(itemlist, key=lambda x: x.title)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    season = scrapertools.find_single_match(data, '<div class="season-container".*?data-season="' + item.id_season + '"(.*?)</div></div>')

    matches = scrapertools.find_multiple_matches(season, '<a(.*?)</a>')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('MegaDedeOficial', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('MegaDedeOficial', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MegaDedeOficial', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MegaDedeOficial', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MegaDedeOficial', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MegaDedeOficial', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('MegaDedeOficial', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        if url.startswith("/"): url = host[:-1] + url

        title = item.contentSerieName.replace('&#038;', '&')

        epis = scrapertools.find_single_match(match, '<div class="fz5 fw6 mab0">(.*?)</div>')

        epis = epis.replace('Ep', '').replace('ep', '').strip()

        if not epis: epis = 1

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    embeds = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)".*?</iframe>')

    if not embeds: embeds = scrapertools.find_single_match(data, 'data-src="(.*?)"')

    if not embeds: return itemlist

    if embeds.startswith('//'): embeds = 'https:' + embeds
    elif embeds.startswith("/"): embeds = host[:-1] + embeds

    if not 'http' in embeds: return itemlist

    embeds = embeds.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

    data = do_downloadpage(embeds)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    ses = 0

    if '/waaw.' in embeds:
        ses += 1

        lang = '?'

        url = embeds

        servidor = servertools.get_server_from_url(url)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = lang ))

    elif '/embed69.' in embeds or '/vidurl/' in embeds:
        ses += 1

        datae = data

        dataLink = scrapertools.find_single_match(datae, 'const dataLink =(.*?);')
        if not dataLink: dataLink = dataLink = scrapertools.find_single_match(datae, 'let dataLink =(.*?);')
        if not dataLink: dataLink = scrapertools.find_single_match(datae, 'dataLink(.*?);')

        e_bytes = scrapertools.find_single_match(datae, "const bytes =.*?'(.*?)'")
        if not e_bytes: e_bytes = scrapertools.find_single_match(datae, "const safeServer =.*?'(.*?)'")

        e_links = dataLink.replace(']},', '"type":"file"').replace(']}]', '"type":"file"')

        age = ''
        if not dataLink or not e_bytes: age = 'crypto'

        langs = scrapertools.find_multiple_matches(str(e_links), '"video_language":(.*?)"type":"file"')

        for lang in langs:
            ses += 1

            lang = lang + '"type":"video"'

            links = scrapertools.find_multiple_matches(str(lang), '"servername":"(.*?)","link":"(.*?)".*?"type":"video"')

            if 'SUB' in lang: lang = 'Vose'
            elif 'LAT' in lang: lang = 'Lat'
            elif 'ESP' in lang: lang = 'Esp'
            else: lang = '?'

            for srv, link in links:
                ses += 1

                srv = srv.lower().strip()

                if not srv: continue
                elif host in link: continue

                elif '1fichier.' in srv: continue
                elif 'plustream' in srv: continue
                elif 'embedsito' in srv: continue
                elif 'disable2' in srv: continue
                elif 'disable' in srv: continue
                elif 'xupalace' in srv: continue
                elif 'uploadfox' in srv: continue

                elif srv == 'download': continue
                elif srv == 'up2box': continue

                servidor = servertools.corregir_servidor(srv)

                if servertools.is_server_available(servidor):
                    if not servertools.is_server_enabled(servidor): continue
                else:
                    if not config.get_setting('developer_mode', default=False): continue

                other = ''
                cpow = ''

                if servidor == 'various': other = servertools.corregir_other(srv)

                if '.eyJs' in link: age = ''

                elif 'POW_CHALLENGE' in data:
                   cpow = scrapertools.find_single_match(data, "POW_CHALLENGE\s*=\s*'([^']+)';" +
                                                               "\s*\w*\s*POW_DIFFICULTY\s*=\s*(\d+);" +
                                                               "\s*\w*\s*POW_SALT\s*=\s*'([^']+)';")
                   if cpow: age = ''

                itemlist.append(Item( channel = item.channel, action = 'play', server=servidor, title = '',
                                      crypto=link, bytes=e_bytes, age=age, cpow=cpow, language=lang, other=other ))

            continue

    # ~ Otros
    matches = scrapertools.find_multiple_matches(data, 'onclick="go_to_player.*?' + "'(.*?)'")
    if not matches: matches = scrapertools.find_multiple_matches(data, 'onclick="go_to_player.*?' + "'(.*?)'")

    langs = []
    if 'data-lang="1"' in data: langs.append('Esp')
    if 'data-lang="0"' in data: langs.append('Lat')
    if 'data-lang="2"' in data: langs = langs.append('Vose')

    if ',' in str(langs): lang = ",".join(langs)
    else: lang = str(langs).replace('[', '').replace("'", '').replace(']', '').strip()

    if not langs: lang = '?'

    for url in matches:
        ses += 1

        if not url: continue
        elif url == '#': continue

        elif '/1fichier.' in url: continue
        elif '/short.' in url: continue
        elif '/plustream.' in url: continue
        elif '/player-cdn.' in url: continue

        elif 'embedsito' in url: continue
        elif 'disable2' in url: continue
        elif 'disable' in url: continue
        elif 'xupalace' in url: continue
        elif 'uploadfox' in url: continue

        servidor = servertools.get_server_from_url(url)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)

        if servidor == 'directo':
            if config.get_setting('developer_mode', default=False):
                other = url.split("/")[2]
                other = other.replace('https:', '').strip()

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = lang, other = other ))

    # ~ iframes data-src
    matches = scrapertools.find_multiple_matches(data, '<iframe.*?data-src="(.*?)"')

    for match in matches:
        lang = '?'

        if '/xupalace.' in match:
            ses += 1

            if 'php?id=' in match:
                datax = do_downloadpage(match)

                url = scrapertools.find_single_match(datax, '<iframe src="(.*?)"')

                if url:
                    servidor = servertools.get_server_from_url(url)

                    if servertools.is_server_available(servidor):
                        if not servertools.is_server_enabled(servidor): continue
                    else:
                        if not config.get_setting('developer_mode', default=False): continue

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url=url, language=lang ))

                continue

            elif '/video/' in match:
                datax = do_downloadpage(match)

                matchesx = scrapertools.find_multiple_matches(datax, "go_to_playerVast.*?'(.*?)'(.*?)</span>")

                for matchx, restox in matchesx:
                    if '/embedsito.' in matchx: continue
                    elif '/player-cdn.' in matchx: continue
                    elif '/1fichier.' in matchx: continue
                    elif '/hydrax.' in matchx: continue
                    elif '/xupalace.' in matchx: continue
                    elif '/uploadfox.' in matchx: continue

                    if 'data-lang="0"' in restox: lang = 'Lat'
                    elif 'data-lang="1"' in restox: lang = 'Esp'
                    elif 'data-lang="2"' in restox: lang = 'Vose'
                    elif 'data-lang="3"' in restox: lang = 'Jap'
                    else: lang = '?'

                    servidor = servertools.get_server_from_url(matchx)

                    if servertools.is_server_available(servidor):
                        if not servertools.is_server_enabled(servidor): continue
                    else:
                        if not config.get_setting('developer_mode', default=False): continue

                    other = ''
                    if servidor == 'various': other = servertools.corregir_other(matchx)

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = matchx,
                                          language=lang, other=other ))

                continue

            else: continue

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.crypto:
        crypto = str(item.crypto)
        bytes = str(item.bytes)

        url = ''

        if not bytes:
            if '.eyJs' in item.crypto:
                url = scrapertools.find_single_match(item.crypto, '\.(eyJs.*?)\.')
                url += '='

                try:
                    url = base64.b64decode(url).decode()
                    url = scrapertools.find_single_match(url, '"link":"(.*?)"')
                except:
                    url = ''

            elif item.cpow:
                res_pow = {"challenge": item.cpow[0], "difficulty": int(item.cpow[1]), "salt": item.cpow[2]}

                resolve_pow = decrypters.decode_pow(res_pow)
                aes_clave = resolve_pow.get("aes_key", "")

                if aes_clave:
                    url = decrypters.decode_decipher(crypto, aes_clave)

        if not url:
            if bytes:
                try:
                   url = GibberishAES.dec(GibberishAES(), string = crypto, pass_ = bytes)
                except:
                    url = ''

            if not url:
                if bytes:
                    url = decrypters.decode_decipher(crypto, bytes)

            if not url:
                if crypto.startswith("http"):
                    url = crypto.replace('\\/', '/')

                if not url:
                    return '[COLOR cyan]No se pudo [COLOR goldenrod]Descifrar[/COLOR]'

            elif not url.startswith("http"):
                return '[COLOR cyan]No se pudo [COLOR goldenrod]Descifrar[/COLOR]'

    if url:
        if '/hydrax.' in url or '/xupalace.' in url or '/uploadfox.' in url or '/embed69.' in url or '/pelisplay.' in url:
            return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

        servidor = servertools.get_server_from_url(url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        url = servertools.normalize_url(servidor, url)

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'search?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

