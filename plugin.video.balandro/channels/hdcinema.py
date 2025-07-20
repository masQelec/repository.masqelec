# -*- coding: utf-8 -*-

import re


from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://pelicinehd.com/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if not headers: headers = {'Referer': host}

    if '/release/' in url: raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>GENEROS<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)".*?>(.*?)</a>')

    for url, tit in matches:
        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1929, -1):
        url = host + 'release/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color='deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 1

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h1(.*?)CARTELERA')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        title = scrapertools.find_single_match(match, '<h2 class="entry-title">(.*?)</h2>')

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if not title or not url: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        thumb = 'https:' + thumb

        year = scrapertools.find_single_match(match, '<span class="year">(.*?)</span>')
        if not year: year = '-'

        if '/release/' in item.url: year = scrapertools.find_single_match(item.url, "/release/(.*?)/")

        langs = []
        if 'espana.png' in match: langs.append('Esp')
        if 'MEXICO.png' in match: langs.append('Lat')
        if 'ingles.png' in match: langs.append('Vose')

        title = title.replace('&#038;', '&')
		
        tipo = 'movie' if '/movies/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action = 'findvideos', url=url, title=title, thumbnail=thumb, languages=', '.join(langs), fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, languages=', '.join(langs), fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<a class="page-link current".*?class="extend">.*?<a href="(.*?)".*?</section>')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', action='list_all', url = next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    temporadas = re.compile('data-season="(.*?)"', re.DOTALL).findall(data)

    for tempo in temporadas:
        tempo = tempo.replace('Temporada', '').replace('TEMPORADA', '').strip()

        nro_tempo = tempo

        title = 'Temporada ' + nro_tempo

        if len(temporadas) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = tempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    d_post = scrapertools.find_single_match(data, 'data-post="(.*?)"')

    if not d_post: return itemlist

    post = {'action': 'action_select_season', 'season': str(item.contentSeason), 'post': d_post}

    data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = post)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('HdCinema', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('HdCinema', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('HdCinema', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('HdCinema', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('HdCinema', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('HdCinema', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('HdCinema', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        epis = scrapertools.find_single_match(match, '<span class="num-epi">.*?x(.*?)</span>')

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

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

    IDIOMAS = {'mexico': 'Lat', 'latíno': 'Lat', 'latíno': 'Lat', 'espana': 'Esp', 'castellano': 'Esp', 'ingles': 'Vo', 'subtitulado': 'Vose'}

    data = do_downloadpage(item.url)

    options = scrapertools.find_multiple_matches(data, 'href="#options-(.*?)".*?<span class="server">(.*?)</a>')

    ses = 0

    for opt, srv in options:
        if not srv: continue

        ses += 1

        lng = scrapertools.find_single_match(srv, ".*?-(.*?)</span>").lower().strip()

        srv = scrapertools.find_single_match(srv, "(.*?)-").lower().strip()

        links = scrapertools.find_multiple_matches(data, '<div id="options-' + opt + '".*?<iframe.*?src="(.*?)".*?</iframe>')

        for link in links:
            ses += 1

            url = link.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')
            url = link.replace('amp;#038;', '&').replace('#038;', '&').replace('amp;', '&')

            itemlist.append(Item(channel = item.channel, action = 'play', server=srv, title = '', url=url,
                                 language=IDIOMAS.get(lng, lng) ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    item.url = item.url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')
    item.url = item.url.replace('amp;#038;', '&').replace('#038;', '&').replace('amp;', '&')

    url = item.url

    data = do_downloadpage(url)

    new_url = scrapertools.find_single_match(data, 'src="(.*?)"')
    if not new_url: new_url = scrapertools.find_single_match(data, 'SRC="(.*?)"')

    if new_url:
        if new_url == 'null': return itemlist

        url = new_url

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if 'voe.sx' in url: servidor = 'voe'

        else:
           if 'http' in servidor:
               if 'tubeload' in url or 'mvidoo' in url or 'rutube' in url or 'filemoon' in url or 'moonplayer' in url or 'streamhub' in url or 'uploadever' in url or 'videowood' in url or 'yandex' in url or 'yadi.' in url or 'fastupload' in url or 'dropload' in url or 'streamwish' in url or 'krakenfiles' in url or 'hexupload' in url or 'hexload' in url or 'desiupload' in url or 'filelions' in url or 'youdbox' in url or 'yodbox' in url or 'wish' in url or 'azipcdn' in url or 'awish' in url or 'dwish' in url or 'mwish' in url or 'swish' in url or 'lulustream' in url or 'luluvdo' in url or 'lion' in url or 'alions' in url or 'dlions' in url or 'mlions' in url or 'turboviplay' in url or 'emturbovid' in url or 'tuborstb' in url or 'streamvid' in url or 'upload.do' in url or 'uploaddo' in url or 'file-upload' in url or 'wishfast' in url or 'doodporn' in url or 'vidello' in url or 'vidroba' in url or 'vidspeed' in url or 'sfastwish' in url or 'fviplions' in url or 'moonmov' in url or 'flaswish' in url or 'vkspeed' in url or 'vkspeed7' in url or 'obeywish' in url or 'twitch' in url or 'vidhide' in url or 'hxfile' in url or 'drop' in url or 'embedv' in url or 'vgplayer' in url or 'userload' in url or 'uploadraja' in url or 'cdnwish' in url or 'goodstream' in url or 'asnwish' in url  or 'flastwish' in url or 'jodwish' in url or 'fmoonembed' in url or 'embedmoon' in url or 'moonjscdn' in url or 'rumble' in url or 'bembed' in url or 'javlion' in url or 'streamruby' in url or 'sruby' in url or 'rubystream' in url or 'stmruby' in url or 'rubystm' in url or 'rubyvid' in url or 'swhoi'in url or 'listeamed' in url or 'go-streamer.net' in url or 'fsdcmo' in url or 'fdewsdc' in url or 'peytonepre' in url or 'ryderjet' in url or 'smoothpre' in url or 'movearnpre' in url or 'seraphinap' in url or 'seraphinapl' in url or 'qiwi' in url or 'swdyu' in url or 'streamhihi' in url or 'luluvdoo' in url or 'lulu' in url or 'ponmi' in url or 'wishonly' in url or 'streamsilk' in url or 'playerwish' in url or 'hlswish' in url or 'iplayerhls' in url or 'hlsflast' in url or 'ghbrisk' in url or 'cybervynx' in url or 'streamhg ' in url or 'stbhg' in url or 'dhcplay' in url or 'wish' in url or 'stblion' in url or 'terabox' in url or 'dhtpre' in url or 'dramacool' in url or 'l1afav' in url or 'hlsflex' in url or 'swiftplayers' in url or 'gradehgplus' in url: servidor = 'various'

               elif 'allviid' in url or 'cloudfile' in url or 'cloudmail' in url or 'dailyuploads' in url or 'darkibox' in url or 'dembed' in url or 'downace' in url or 'fastdrive' in url or 'fastplay' in url or 'filegram' in url or 'gostream' in url or 'letsupload' in url or 'liivideo' in url or 'myupload' in url or 'neohd' in url or 'oneupload' in url or 'pandafiles' in url or 'rovideo' in url or 'send' in url or 'streamable' in url or 'streamdav' in url or 'streamgzzz' in url or 'streamoupload' in url or 'turbovid' in url or 'tusfiles' in url or 'uploadba' in url or 'uploadflix' in url or 'uploadhub' in url or 'uploady' in url or 'veev' in url or 'doods' in url or 'veoh' in url or 'vidbob' in url or 'vidlook' in url or 'vidmx' in url or 'vido.' in url or 'vidpro' in url or 'vidstore' in url or 'vipss' in url or 'vkprime' in url or 'worlduploads' in url or 'ztreamhub' in url or 'amdahost' in url or 'updown' in url or 'videa' in url or 'asianplay' in url or 'swiftload' in url or 'udrop' in url or 'vidtube' in url or 'bigwarp' in url or 'bgwp' in url or 'wecima': servidor = 'zures'

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
       item.url = host + '?s=' + texto.replace(" ", "+")
       return list_all(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []

