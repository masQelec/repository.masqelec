# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, jsontools, tmdb


host = 'https://doramaswow.com/'


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar dorama ...', action = 'search', search_type = 'all', text_color = 'firebrick' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'explore?format=movie', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más recientes', action = 'list_all', url = host + 'explore?format=movie&direction=asc&type=movie&sortBy=release_date', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'explore?format=movied&irection=asc&type=movie&sortBy=mosts_week', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'explore?format=drama', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Catálogo variedades', action = 'list_all', url = host + 'explore?format=variety', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos capítulos', action = 'last_episodes', url = host + 'latest-episodes', search_type = 'tvshow', text_color='olive' ))

    itemlist.append(item.clone( title = 'Más recientes', action = 'list_all', url = host + 'explore?format=drama&direction=asc&type=movie&sortBy=release_date', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'explore?format=drama&direction=asc&type=movie&sortBy=mosts_week', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    genres = [
       ['accion', 'Acción'],
       ['amistad', 'Amistad'],
       ['animales', 'Animales'],
       ['artes-marciales', 'Artes Marciales'],
       ['aventura', 'Aventura'],
       ['belico', 'Bélico'],
       ['bruja', 'Bruja'],
       ['cirugia-plastica', 'Cirugía Plástica'],
       ['cliente', 'Cliente'],
       ['cocina', 'Cocina'],
       ['codicia', 'Codicia'],
       ['colegial', 'Colegial'],
       ['comedia', 'Comedia'],
       ['comida', 'Comida'],
       ['cortometraje', 'Cortometraje'],
       ['crimen', 'Crimen'],
       ['deportes', 'Deportes'],
       ['derecho', 'Derecho'],
       ['detective', 'Detective'],
       ['documental', 'Documental'],
       ['drama', 'Drama'],
       ['entretenimiento', 'Entretenimiento'],
       ['escolar', 'Escolar'],
       ['escuela', 'Escuela'],
       ['familiar', 'Familiar'],
       ['fantasia', 'Fantasía'],
       ['ficcion', 'Ficción'],
       ['guerra', 'Guerra'],
       ['heredero', 'Heredero'],
       ['historico', 'Histórico'],
       ['horror', 'Horror'],
       ['intriga', 'Intriga'],
       ['investigacion', 'Investigación'],
       ['juvenil', 'Juvenil'],
       ['juventud', 'Juventud'],
       ['k-pop', 'K Pop'],
       ['kshow', 'K Show'],
       ['legal', 'Legal'],
       ['ley', 'Ley'],
       ['love-hate-relationship', 'Love Hate Relationship'],
       ['maduro', 'Maduro'],
       ['medico', 'Médico'],
       ['melodrama', 'Melodrama'],
       ['militar', 'Militar'],
       ['misterio', 'Misterio'],
       ['mitologia', 'Mitología'],
       ['musica', 'Música'],
       ['musical', 'Musical'],
       ['narrativo', 'Narrativo'],
       ['negocios', 'Negocios'],
       ['obsesion', 'Obsesión'],
       ['pareja-casada', 'Pareja Casada'],
       ['policial', 'Policial'],
       ['politica', 'Política'],
       ['programa-de-variedades', 'Programa de Variedades'],
       ['psicologico', 'Psicológico'],
       ['relacion-abusiva', 'Relación Abusiva'],
       ['romance', 'Romance'],
       ['sitcom', 'Sitcom'],
       ['sobrenatural', 'Sobrenatural'],
       ['suspenso', 'Suspenso'],
       ['terror', 'Terror'],
       ['thriller', 'Thriller'],
       ['tragedia', 'Tragédia'],
       ['vampiro', 'Vampiro'],
       ['venganza', 'Venganza'],
       ['vida', 'Vida'],
       ['webdrama', 'Webdrama'],
       ['wuxia', 'Wuxia'],
       ['zombis', 'Zombis']
       ]

    if item.search_type == 'movie': url_gen = host + 'explore?format=movie&genre='
    else: url_gen = host + 'explore?format=drama&genre='

    for genero in genres:
        url = url_gen + genero[0] + '&direction=asc&type=movie'

        itemlist.append(item.clone( title = genero[1], action = 'list_all', url = url, text_color = text_color ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    from datetime import datetime
    current_year = int(datetime.today().year)

    if item.search_type == 'movie': url_any = host + 'explore?format=movie&year=='
    else: url_any = host + 'explore?format=drama&year='

    for x in range(current_year, 1939, -1):
        url = url_any + str(x) + '&max_year=' + str(x) + '&year=' + str(x) + '&direction=asc&type=movie'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color = text_color ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    web_paises = [
       ['china', 'China'],
       ['south-korea', 'Corea del sur'],
       ['japan', 'Japon'],
       ['taiwan', 'Taiwan'],
       ['thailand', 'Tailandia']
       ]

    if item.search_type == 'movie': url_pais = host + 'explore?format=movie&country='
    else: url_pais = host + 'explore?format=drama&country='

    for x in web_paises:
        url = url_pais + x[0] + '&direction=asc&type=movie'

        itemlist.append(item.clone( title = x[1], url=url, action='list_all', text_color = text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 1

    data = do_downloadpage(item.url + '&page=' + str(item.page))

    matches = re.compile('<a class="MuiButtonBase-root MuiCardActionArea-root css-(.*?)<div class="MuiPaper-root').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, '<div class="MuiTypography-root MuiTypography-body1 MuiTypography-noWrap css-1fzjeoh">(.*?)</div>').strip()

        if not url or not title: continue

        url = host[:-1] + url

        thumb = scrapertools.find_single_match(match, 'srcSet=".*?url=(.*?) ')
        thumb = thumb.replace('&amp;', '&')

        thumb = host[:-1] + thumb

        year = scrapertools.find_single_match(match, '><p class="MuiTypography-root MuiTypography-body2 css-nivh08">(.*?)</p>')
        if not year: year = '-'

        title = title.replace('(Movie)', '').replace('Movie', '').strip()

        title = title.replace('&#x27;s', 's')

        if item.search_type == 'movie':
            if '/drama/' in url: continue
            elif '/variety/' in url: continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if item.search_type == 'tvshow':
            if '/movie/' in url: continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, contentType = 'tvshow', contentSerieName = title, infoLabels={'year':year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        itemlist.append(item.clone( title = 'Siguientes ...', url = item.url, page = item.page + 1, action = 'list_all', text_color = 'coral' ))

    return itemlist


def last_episodes(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)

    patron = '<div class="col-12 sm:col-6 md:col-4 lg:col-4 xl:col-3 mb-3">.*?href="(.*?)".*?src="(.*?)".*?<div class="list-item-title">(.*?)</div>.*?<div class="list-item-subtitle">(.*?)</div>'

    matches = scrapertools.find_multiple_matches(data, patron)

    for url, thumb, title, episode in matches:
        if not url or not title: continue

        title = title.strip()
        episode = episode.strip()

        season = 1
        epis = scrapertools.find_single_match(episode, 'Capítulo(.*?)$').strip()
        if not epis: continue

        thumb = thumb.replace('50x60@', '350x500@')

        titulo = str(season) + 'x' + epis + ' ' + title

        itemlist.append(item.clone( action='findvideos', title = titulo, thumbnail = thumb, url = url,
                                    contentType = 'episode', contentSerieName = title, contentSeason = season, contentEpisodeNumber = epis ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_url = scrapertools.find_single_match(data, '<nav>.*?<a href="(.*?)"')

        if next_url:
            itemlist.append(item.clone( title="Siguientes ...", action="last_episodes", url = next_url, page = 0, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    title = 'Sin temporadas'

    platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '[COLOR tan]' + title + '[/COLOR]')
    item.page = 0
    item.contentType = 'season'
    item.contentSeason = 1
    itemlist = episodios(item)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    patron = '<div data-number=".*?href="(.*?)".*?src="(.*?)".*?<span itemprop="episodeNumber">(.*?)</span>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('DoramasJc', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasJc', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasJc', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasJc', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('DoramasJc', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('DoramasJc', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, thumb, epis, in matches[item.page * item.perpage:]:
        title = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName

        itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail=thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page= item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'LAT': 'Lat', 'VOSE': 'Vose', 'VO': 'VO'}

    data = do_downloadpage(item.url)

    links = jsontools.load(scrapertools.find_single_match(data, 'var links =([^;]+)'))

    ses = 0

    try:
        for link in links['online']:
            ses += 1

            url = link['link'].replace("/link/", "/redirect/")

            if url:
                if link['subtitle']['value'] == 'es': lang = 'Vose'
                else: lang = 'VO'

                try:
                    qlty = link['quality']['text']
                except:
                    qlty = ''

                servidor = link['server']['name'].lower()

                if 'hqq' in servidor or 'waaw' in servidor or 'netu' in servidor: continue
                elif servidor == 'veo': servidor = 'voe'

                servidor = servertools.corregir_servidor(servidor)

                itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', other = servidor, title = '', url = url,language = lang, quality = qlty ))
    except:
        return itemlist

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.url.startswith(host):
       url = httptools.downloadpage(item.url, follow_redirects=False).headers.get('location', '')

       if url:
           if '/hqq.' in url or '/waaw.' in url or '/netu.' in url or '/gounlimited.' in url:
               return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

           if url.startswith('https://odysee.com'):
               data = do_downloadpage(url)

               url = scrapertools.find_single_match(data, '"contentUrl": "(.*?)"')

               if url:
                   itemlist.append(item.clone(server = item.server, url = url))

               return itemlist

           servidor = servertools.get_server_from_url(url)
           servidor = servertools.corregir_servidor(servidor)

           url = servertools.normalize_url(servidor, url)

           itemlist.append(item.clone(server = servidor, url = url))
    else:
        itemlist.append(item.clone(server = item.server, url = item.url))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<a class="MuiButtonBase-root MuiCardActionArea-root css-(.*?)<div class="MuiPaper-root').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, '<div class="MuiTypography-root MuiTypography-body1 MuiTypography-noWrap css-1fzjeoh">(.*?)</div>').strip()

        if not url or not title: continue

        url = host[:-1] + url

        thumb = scrapertools.find_single_match(match, 'srcSet=".*?url=(.*?) ')
        thumb = thumb.replace('&amp;', '&')

        thumb = host[:-1] + thumb

        year = scrapertools.find_single_match(match, '><p class="MuiTypography-root MuiTypography-body2 css-nivh08">(.*?)</p>')
        if not year: year = '-'

        title = title.replace('(Movie)', '').replace('Movie', '').strip()

        title = title.replace('&#x27;s', 's')

        tipo = 'movie' if '/movie/' in url else 'tvshow'

        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))
        if tipo == 'tvshow':
            if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'search?q=' + texto.replace(" ", "+")
        item.text = texto.replace(" ", "+")
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
