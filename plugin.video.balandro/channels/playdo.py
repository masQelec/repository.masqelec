# -*- coding: utf-8 -*-

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, jsontools, tmdb


host = 'https://playdomapp.top/'


useragent = httptools.get_user_agent()


def do_downloadpage(url, post=None, headers=None):
    headers = {"User-Agent": useragent + " pddkit/2023"}

    data = httptools.downloadpage(url, post=post, headers=headers).data

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'api/getNewMedia', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'api/getPopulars/all', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'api/getNewMedia', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Novedades', action = 'list_all', url = host + 'api/getTodaySeries', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'api/getPopulars/all', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    genres = [
       ['28', 'Acción'],
       ['16', 'Animación'],
       ['10752', 'Bélica'],
       ['878', 'Ciencia ficción'],
       ['35', 'Comedia'],
       ['80', 'Crimen'],
       ['99', 'Documental'],
       ['18', 'Drama'],
       ['10751', 'Familia'],
       ['9648', 'Misterio'],
       ['10402', 'Música'],
       ['10749', 'Romance'],
       ['53', 'Suspense'],
       ['27', 'Terror'],
       ['37', 'Western']
       ]

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    for id, title in genres:
        url = host + 'api/getByGenre'

        itemlist.append(item.clone( title = title.capitalize(), action = 'list_all', url = url, genre_id = id, text_color = text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 1

    if item.search_type == 'movie': _type = 'movie'
    elif item.search_type == 'tvshow': _type = 'serie'
    else: _type = 'all'

    if 'api/getNewMedia' in item.url: post = {"page": item.page, "type": _type}
    elif 'api/getPopulars/all' in item.url: post = {"page": item.page, "type": _type}
    elif 'api/getByGenre' in item.url: post = {"page": item.page, "type": _type, "genre_id": item.genre_id}
    elif 'api/getTodaySeries' in item.url: post = {"page": item.page, "type": _type}
    elif 'api/search' in item.url: post = {"page": item.page, "type": _type, "query": item.qry}
    else: return itemlist

    data = do_downloadpage(item.url, post = post)

    jdata = jsontools.load(data)

    if not jdata: return itemlist

    if not jdata.get('status') == "success": return itemlist

    data = jdata['data']

    for elem in data:
        id = elem['id']
        title = elem['name']
        type = elem['type']
        thumb = elem['posterPhoto']
        year = elem['year']

        if not id or not title: continue

        thumb = thumb.replace('http:', 'https:')

        if not year: year = '-'

        tipo = 'movie' if type == 'movie' else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', movie_id=id, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', serie_id=id, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next = True
        if 'api/search' in item.url: 
            if len(itemlist) < 10: next = False

        if next:
            itemlist.append(item.clone( title = 'Siguientes ...', page  = item.page + 1, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    post = {"serie_id": item.serie_id}

    data = do_downloadpage(host + 'api/getSeriesEpisodes', post=post)

    jdata = jsontools.load(data)

    if not jdata: return itemlist

    if not jdata.get('status') == "success": return itemlist

    if not jdata.get('message') == "Success": return itemlist

    data = jdata['seasons']

    for elem in data:
        tempo = elem.get('season')

        tempo = str(tempo)

        title = 'Temporada ' + tempo

        if len(jdata['seasons']) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = tempo, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    post = {"serie_id": item.serie_id}

    data = do_downloadpage(host + 'api/getSeriesEpisodes', post=post)

    jdata = jsontools.load(data)

    if not jdata: return itemlist

    if not jdata.get('status') == "success": return itemlist

    if not jdata.get('message') == "Success": return itemlist

    data = jdata['seasons']

    for elem in data:
        capis = elem.get('episodes')

        for elem1 in capis:
            tempo = elem1['season']

            tempo = str(tempo)

            if not tempo == str(item.contentSeason): continue

            id = elem1['id']
            epis = elem1['number']
            thumb = elem1['image']
            title = elem1['title']

            epis = str(epis)

            titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

            itemlist.append(item.clone( action='findvideos', serie_id = id, links = elem1, title = titulo, thumbnail=thumb,
                                        contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=epis ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not item.movie_id:
        if not item.serie_id: return itemlist

    if item.movie_id: post = {"movie_id": item.movie_id}
    else: post = {"serie_id": item.serie_id}

    ses = 0

    if item.movie_id:
        data = do_downloadpage(host + 'api/getMovieLinks', post=post)

        jdata = jsontools.load(data)

        if not jdata:
            platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Sin Enlaces Disponibles[/B][/COLOR]')
            return

        if not jdata.get('status') == "success":
            platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Sin Enlaces Disponibles[/B][/COLOR]')
            return

        data = jdata['links']

        for elem in data:
            ses += 1

            srv = elem['name']
            srv = srv.lower()

            url = elem['url']
            qlty = elem['quality']
            lang = elem['language']

            if not url: continue

            url = url.replace('\\/', '/')

            if '.rapidvideo.' in url: continue
            elif '/cloudemb.' in url or '.fembed.' in url or '/fembad.' in url or 'vanfem' in url: continue
            elif '/tubesb.' in url or '/sbsonic.' in url or '/sbrapid.' in url or '/lvturbo.' in url or '/sbface.' in url or '/sbbrisk.' in url or '/sblona.' in url: continue
            elif 'powvideo' in url: continue
            elif 'streamplay' in url: continue

            elif '/vidsrc.' in url: continue

            url = url.replace('/.html', '/')

            if '/streamtape.com/' in url:
                if not '/e/' in url:
                    if not '/v/' in url: url = url.replace('/streamtape.com/', '/streamtape.com/v/')
            elif '/filelions.online/' in url:
                if not '/v/' in url and  not '/d/' in url:
                   if not '/f/' in url: url = url.replace('/filelions.online/', '/filelions.online/f/')
            elif '/sltube.org/' in url:
                if not '/e/' in url:
                    if not '/v/' in url: url = url.replace('/sltube.org/', '/sltube.org/v/')

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            lang = lang.replace('ESPSUB', 'Vose').replace('ESP', 'Esp').replace('LAT', 'Lat').replace('ENG', 'Vo').replace('EngSUB', 'Vos').replace('VoSUB', 'Vos')

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)
            elif servidor == 'directo':
               if config.get_setting('developer_mode', default=False): other = url
               else: continue

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = lang, quality = qlty, other = other.capitalize() ))

    # ~ Episodios
    else:
        urls = item.links.get('url')

        for link in urls:
            ses += 1

            srv = scrapertools.find_single_match(str(link), "'name': '(.*?)'")
            srv = srv.lower()

            url = scrapertools.find_single_match(str(link), "'url': '(.*?)'")
            qlty = scrapertools.find_single_match(str(link), "'quality': '(.*?)'")
            lang = scrapertools.find_single_match(str(link), "'language': '(.*?)'")

            if not url: continue

            url = url.replace('\\/', '/')

            if '.rapidvideo.' in url: continue
            elif '/cloudemb.' in url or '.fembed.' in url or '/fembad.' in url or 'vanfem' in url: continue
            elif '/tubesb.' in url or '/sbsonic.' in url or '/sbrapid.' in url or '/lvturbo.' in url or '/sbface.' in url or '/sbbrisk.' in url or '/sblona.' in url: continue
            elif 'powvideo' in url: continue
            elif 'streamplay' in url: continue

            elif '/vidsrc.' in url: continue

            url = url.replace('/.html', '/')

            if '/streamtape.com/' in url:
                if not '/e/' in url:
                    if not '/v/' in url: url = url.replace('/streamtape.com/', '/streamtape.com/v/')
            elif '/filelions.online/' in url:
                if not '/v/' in url and  not '/d/' in url:
                    if not '/f/' in url: url = url.replace('/filelions.online/', '/filelions.online/f/')
            elif '/sltube.org/' in url:
                if not '/e/' in url:
                    if not '/v/' in url: url = url.replace('/sltube.org/', '/sltube.org/v/')

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            lang = lang.replace('ESPSUB', 'Vose').replace('ESP', 'Esp').replace('LAT', 'Lat').replace('ENG', 'Vo').replace('EngSUB', 'Vos').replace('VoSUB', 'Vos')

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)
            elif servidor == 'directo':
                  if config.get_setting('developer_mode', default=False): other = url
                  else: continue

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = lang, quality = qlty, other = other.capitalize() ))
					
    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'api/search' 
        item.qry = texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

