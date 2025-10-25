# -*- coding: utf-8 -*-

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

from lib import jsunpack


host = 'https://osjonosu.es/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/lanzamiento/' in url: raise_weberror = False

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Tendencias', action = 'list_all', url = host + 'tendencias/?get=movies', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Infantil', action = 'list_all', url = host + 'genero/infantiles/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Sagas', action = 'sagas', url = host, search_type = 'movie', text_color='moccasin' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Tendencias', action = 'list_all', url = host + 'tendencias/?get=tv', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def sagas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, 'SAGAS<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<li id="menu-item-(.*?)</li>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="([^"]+)"')

        title = scrapertools.find_single_match(match, '<a href=".*?">(.*?)</a>')

        if not url or not title: continue

        title = title.replace('&#8217;', "'").replace('&#038;', '&')

        itemlist.append(item.clone( action = 'list_all', url=url, title=title ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    opciones = {
        'accion': 'Acción',
        'animacion': 'Animación',
        'aventura': 'Aventura',
        'biografia': 'Biografía',
        'ciencia-ficcion': 'Ciencia ficción',
        'comedia': 'Comedia',
        'crimen': 'Crimen',
        'documental': 'Documental',
        'drama': 'Drama',
        'familia': 'Familia',
        'fantasia': 'Fantasía',
        'guerra': 'Guerra',
        'historia': 'Historia',
        'misterio': 'Misterio',
        'musica': 'Música',
        'romance': 'Romance',
        'suspense': 'Suspense',
        'terror': 'Terror',
        'western': 'Western'
        }

    for opc in opciones:
        itemlist.append(item.clone( title = opciones[opc], url = host + 'genero/' + opc + '/', action ='list_all', text_color = text_color ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1959, -1):
        url = host + 'lanzamiento/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color='deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if '>Añadido recientemente<' in data:
        bloque = scrapertools.find_single_match(data, '>Añadido recientemente<(.*?)>RELACIONADOS<')
    elif '<h1' in data:
        bloque = scrapertools.find_single_match(data, '<h1(.*?)>RELACIONADOS<')
    else:
        bloque = data

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="([^"]+)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        title = title.replace('&#8217;', "'").replace('&#038;', '&').replace('&#8211;', '-')

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        tipo = 'movie' if '/peliculas/' in match else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action = 'findvideos', url=url, title=title, thumbnail=thumb, languages='Esp', qualities='1080p', fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': '-'} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, languages='Esp', qualities='720p', fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
         next_page = scrapertools.find_single_match(str(data), '<div class="pagination">.*?<span class="current">.*?' + "<a href='(.*?)'")

         if next_page:
             if '/page/' in next_page:
                 itemlist.append(item.clone( title = 'Siguientes ...', action='list_all', url = next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, "<span class='title'>(.*?)<i>")

    for tempo in matches:
        tempo = tempo.replace('Temporada', '').replace('TEMPORADA', '').strip()

        nro_tempo = tempo

        title = 'Temporada ' + nro_tempo

        if len(matches) == 1:
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

    bloque = scrapertools.find_single_match(data, "<span class='se-t.*?'>" + str(item.contentSeason) + "</span>(.*?)</ul>")

    matches = scrapertools.find_multiple_matches(bloque, "<li class='mark-(.*?)</li>")

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('OsjoNosu', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('OsjoNosu', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('OsjoNosu', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('OsjoNosu', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('OsjoNosu', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('OsjoNosu', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('OsjoNosu', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        temp = scrapertools.find_single_match(match, "<div class='numerando'>(.*?)-").strip()

        if not temp == str(item.contentSeason): continue

        epis = scrapertools.find_single_match(match, "<div class='numerando'>.*?-(.*?)</div>").strip()
        if not epis: epis = 1

        title = scrapertools.find_single_match(match, "<div class='episodiotitle'>.*?'>(.*?)</a>")

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]')

        if 'Epis.' in titulo:
            titulo = titulo + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        thumb = scrapertools.find_single_match(match, "<img src='(.*?)'")

        url = scrapertools.find_single_match(match, "<a href='(.*?)'")

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

    data = do_downloadpage(item.url)

    options = scrapertools.find_multiple_matches(data, "<li id='player-option-(.*?)</i>")

    ses = 0

    for opt in options:
        if 'trailer' in opt: continue

        dpost = scrapertools.find_single_match(opt, "data-post='(.*?)'")
        dtype = scrapertools.find_single_match(opt, "data-type='(.*?)'")
        dnume = scrapertools.find_single_match(opt, "data-nume='(.*?)'")

        if not dpost or not dtype or not dnume: return

        ses += 1

        headers = {'Referer': item.url}

        post = {'action': 'doo_player_ajax', 'post': dpost, 'nume': dnume, 'type': dtype}

        data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = post, headers = headers)

        url = scrapertools.find_single_match(str(data), '"embed_url":"(.*?)"')

        url = url.replace('\\/', '/')

        if '/vmi597113.' in url: continue

        elif 'osjonosu.osjonosu.' in url: continue

        if not host in url:
            if not '/player.osjonosu.' in url: url = ''

        if url:
            itemlist.append(Item(channel = item.channel, action = 'play', server='', title = '', url=url,
                                 language=item.languages, quality=item.qualities, other='M3u8'))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    new_url = get_video_url(url)

    if new_url:
        if new_url == 'error': return '[COLOR red]Archivo Inexistente ó eliminado[/COLOR]'

        itemlist = new_url

    return itemlist


def get_video_url(url):
    logger.info("(url='%s')" % url)
    video_urls = []

    resp = httptools.downloadpage(url)

    data = resp.data

    if not resp.sucess: return "error"

    if "Video not found" in data or "Not Found" in data or "File was deleted" in data or "is no longer available" in data: return "error" 

    try:
        url = scrapertools.find_single_match(data, "\{\s*file:\s*'([^']+)'")

        if not url:
            pack = scrapertools.find_single_match(data, 'p,a,c,k,e,d.*?</script>')
            unpacked = jsunpack.unpack(pack)
            unpacked = unpacked.replace("\\'", "'")

            url = scrapertools.find_single_match(unpacked, "sources\:\s*\[\{'(?:file|src)':'([^']+)'")

            if url: url = host + url

        if url:
            video_urls.append(['m3u8', url])
    except:
        url = scrapertools.find_single_match(data, '"file":"(.*?)"')

        url = url.replace('\\/', '/')

        if '.mp4' in url: logger.error("Osjonosu Mp4")
        else: logger.error("Osjonosu get_video_url")

    return video_urls


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

