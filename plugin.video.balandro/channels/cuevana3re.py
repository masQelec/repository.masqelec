# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


# ~ Temporadas, Episodios, Findvideos y Busquedas  con  web_alt

host = 'https://cuevana.re/'


api = host + 'wp-json/wpreact/v1/postsapi?post_type[]='

web_alt = 'https://cine-calidad.mx/wp-json/mycustom/v1/'

_player = host + 'wp-json/wpreact/v1/'


def do_downloadpage(url, post=None, headers=None):
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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = api + 'pelicula&per_page=25&page=1', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = api + 'tvshow&per_page=25&page=1', search_type = 'tvshow' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title = 'Animes', action = 'list_all', url = api + 'anime&per_page=25&page=1', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie':
        url_gen = api + 'pelicula&per_page=25&page=1'
        text_color = 'deepskyblue'
    else:
        url_gen = api + 'tvshow&per_page=25&page=1'
        text_color = 'hotpink'

    opciones = [
       ('accion', 'Acción'),
       ('animacion', 'Animación'),
       ('aventura', 'Aventura'),
       ('ciencia-ficcion', 'Ciencia Ficción'),
       ('comedia', 'Comedia'),
       ('documental', 'Documental'),
       ('drama', 'Drama'),
       ('familia', 'Familia'),
       ('fantasia', 'Fantasía'),
       ('historia', 'Historia'),
       ('misterio', 'Misterio'),
       ('musica', 'Música'),
       ('romance', 'Romance'),
       ('suspense', 'Suspense'),
       ('terror', 'Terror'),
       ('western', 'Wsetern')

    ]

    for opc, tit in opciones:
        url = url_gen + '&category=' + opc
        itemlist.append(item.clone( title=tit, url = url, action = 'list_all', text_color=text_color))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('"title":"(.*?)"}', re.DOTALL).findall(data)

    num_matches = len(matches)

    for match in matches:
        slug = scrapertools.find_single_match(match, '"slug":"(.*?)"')

        title = scrapertools.find_single_match(match, '(.*?)"')

        if not slug or not title: continue

        id_tmdb = scrapertools.find_single_match(match, '"tmdb":"(.*?)"')

        if not id_tmdb: continue

        title = clean_title(title)

        title = title.replace('&amp;', '&')

        thumb = scrapertools.find_single_match(match, '"featured_image":"(.*?)"')
        thumb = thumb.replace('\\/', '/')

        year = scrapertools.find_single_match(match, '"year":"(.*?)"')
        if year:
            title = title.replace('(' + year + ')', '').strip()
        else:
            year = '-'

        tipo = 'movie' if '"type":"pelicula' in match or '"type":"movies' in match else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            if item.search_type == 'tvshows': continue

            url = host + 'pelicula/' + id_tmdb + '/' + slug

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, id_tmdb=id_tmdb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            if item.search_type == 'movies': continue

            url = host + 'serie/' + id_tmdb + '/' + slug

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, id_tmdb=id_tmdb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) == 25:
            tot_pages = scrapertools.find_single_match(data, '"total_pages":(.*?),')

            tot_pages = int(tot_pages)

            act_url = scrapertools.find_single_match(item.url, '(.*?)&page=')

            act_pag = scrapertools.find_single_match(item.url, '&page=(.*?)$')
            if '&category=' in act_pag: act_pag = scrapertools.find_single_match(act_pag, '(.*?)&category=')

            act_gen = scrapertools.find_single_match(item.url, '&category=(.*?)$')

            act_pag = int(act_pag)

            if act_pag <= tot_pages:
                sig_pag = act_pag + 1

                next_page = act_url + '&page=' + str(sig_pag)

                if act_gen: next_page =next_page  + '&category=' + act_gen

                itemlist.append(item.clone( title='Siguientes ...', url=next_page, action='list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    url = web_alt + 'serie/' + item.id_tmdb

    data = do_downloadpage(url)

    temporadas = re.compile('"number":"(.*?)"', re.DOTALL).findall(str(data))

    for tempo in temporadas:
        title = 'Temporada ' + tempo

        if len(temporadas) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.url = url
            item.ref = item.url
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action='episodios', title=title, page=0, url=url, ref=item.url, contentType='season', contentSeason=tempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(str(data), '"number":"' + str(item.contentSeason) + '"(.*?)]}')

    matches = re.compile('"episode_number":"(.*?)".*?"image":"(.*?)"', re.DOTALL).findall(bloque)

    num_matches = len(matches)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('Cuevana3In', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('Cuevana3In', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana3In', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana3In', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana3In', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana3In', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('Cuevana3In', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for epis, thumb in matches[item.page * item.perpage:]:
        title = item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        thumb = thumb.replace('\\/', '/')

        ord_epis = epis

        if num_matches >= 10:
            if len(epis) == 1:
                ord_epis = '0' + epis

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        itemlist.append(item.clone( action='findvideos', title = titulo, thumbnail=thumb, ref = item.ref,
                                    contentType = 'episode', contentSeason=item.contentSeason, contentEpisodeNumber=epis, orden=ord_epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > (item.page + 1) * item.perpage:
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page=item.page + 1, perpage=item.perpage, orden='1000', text_color='coral' ))

    return sorted(itemlist, key = lambda it: it.orden)


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'Latino': 'Lat', 'Español Latino': 'Lat', 'Español': 'Esp', 'Castellano': 'Esp', 'Subtitulado': 'Vose', 'Latinoingles': 'Vose', 'Japonessub': 'Jap'}

    if item.contentType == 'movie':
        headers = {'Referer': host}

        url = web_alt + 'movie/' + item.id_tmdb
    else:
        headers = {'Referer': item.ref + '/temporada/' + str(item.contentSeason) + '/episodio/' + str(item.contentEpisodeNumber)}

        url = _player + 'episode/' + item.id_tmdb + '/' + str(item.contentSeason) + '/' + str(item.contentEpisodeNumber)

    data = do_downloadpage(url, headers=headers)

    ses = 0

    matches = re.compile('"url":"(.*?)".*?"lang":"(.*?)".*?,"quality":"(.*?)"', re.DOTALL).findall(str(data))

    for url, lang, qlty in matches:
        if not url: continue

        ses += 1

        url = url.replace('\\/', '/')

        if '/1fichier.' in url: continue
        elif '/lamovie.' in url: continue
        elif '//cc/' in url: continue

        if 'sbplay' in url or 'sbplay1' in url or 'sbplay2' in url or 'pelistop' in url or 'sbfast' in url or 'sbfull' in url or 'ssbstream' in url or  'sbthe' in url or 'sbspeed' in url or 'cloudemb' in url or 'tubesb' in url or 'embedsb' in url or 'playersb' in url or 'sbcloud1' in url or 'watchsb' in url or 'viewsb' in url or 'watchmo' in url or 'streamsss' in url or 'sblanh' in url or 'sbanh' in url or 'sblongvu' in url or 'sbchill' in url or 'sbrity' in url or 'sbhight' in url or 'sbbrisk' in url or 'sbface' in url or 'view345' in url or 'sbone' in url or 'sbasian' in url or 'streaamss' in url or 'lvturbo' in url or 'sbnet' in url or 'sbani' in url or 'sbrapid' in url or 'cinestart' in url or 'vidmoviesb' in url or 'sbsonic' in url or 'sblona' in url or 'likessb' in url: continue

        elif 'fembed' in url or 'fembed-hd' in url or 'fembeder'in url or 'divload' in url or 'ilovefembed' in url or 'myurlshort' in url or 'jplayer' in url or 'feurl' in url or 'fembedisthebest'in url or 'femax20'in url or 'fcdn' in url or 'fembad' in url or 'pelispng' in url or 'hlshd'in url or  'embedsito' in url or 'mrdhan' in url or 'dutrag' in url or 'fplayer' in url or 'diasfem' in url or 'suzihaza' in url or 'vanfem'in url or  'youtvgratis' in url or 'oceanplay' in url or 'gotovideo.kiev.ua' in url or 'owodeuwu' in url or 'sypl' in url or 'fembed9hd' in url or 'watchse' in url or 'vcdn' in url or 'femoload' in url or 'cubeembed'in url: continue

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        other = ''

        if servidor == 'various':
            other = servertools.corregir_other(url)

        lang = clean_title(lang).capitalize()

        lang = IDIOMAS.get(lang, lang)

        itemlist.append(Item( channel = item.channel, action = 'play', title = '', url=url, server=servidor, quality=qlty, language=lang, other=other )) 

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if '/redirect?' in item.url:
        new_url = scrapertools.find_single_match(item.url, "url=(.*?)$")

        if new_url:
            new_url = base64.b64decode(new_url).decode("utf-8")

            url = new_url

    if '/pelispng.' in url: url = ''

    if url:
        if '/plustream.' in url:
            return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            if 'sbplay' in url or 'sbplay1' in url or 'sbplay2' in url or 'pelistop' in url or 'sbfast' in url or 'sbfull' in url or 'ssbstream' in url or  'sbthe' in url or 'sbspeed' in url or 'cloudemb' in url or 'tubesb' in url or 'embedsb' in url or 'playersb' in url or 'sbcloud1' in url or 'watchsb' in url or 'viewsb' in url or 'watchmo' in url or 'streamsss' in url or 'sblanh' in url or 'sbanh' in url or 'sblongvu' in url or 'sbchill' in url or 'sbrity' in url or 'sbhight' in url or 'sbbrisk' in url or 'sbface' in url or 'view345' in url or 'sbone' in url or 'sbasian' in url or 'streaamss' in url or 'lvturbo' in url or 'sbnet' in url or 'sbani' in url or 'sbrapid' in url or 'cinestart' in url or 'vidmoviesb' in url or 'sbsonic' in url or 'sblona' in url or 'likessb' in url:
                return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

            elif 'fembed' in url or 'fembed-hd' in url or 'fembeder'in url or 'divload' in url or 'ilovefembed' in url or 'myurlshort' in url or 'jplayer' in url or 'feurl' in url or 'fembedisthebest'in url or 'femax20'in url or 'fcdn' in url or 'fembad' in url or 'pelispng' in url or 'hlshd'in url or  'embedsito' in url or 'mrdhan' in url or 'dutrag' in url or 'fplayer' in url or 'diasfem' in url or 'suzihaza' in url or 'vanfem'in url or  'youtvgratis' in url or 'oceanplay' in url or 'gotovideo.kiev.ua' in url or 'owodeuwu' in url or 'sypl' in url or 'fembed9hd' in url or 'watchse' in url or 'vcdn' in url or 'femoload' in url or 'cubeembed'in url:
                return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"): servidor = new_server

        itemlist.append(item.clone( url=url, server=servidor ))

    return itemlist


def clean_title(title):
    logger.info()

    title = title.replace('\\u00e1', 'a').replace('\\u00c1', 'a').replace('\\u00e9', 'e').replace('\\u00ed', 'i').replace('\\u00f3', 'o').replace('\\u00fa', 'u')
    title = title.replace('\\u00f1', 'ñ').replace('\\u00bf', '¿').replace('\\u00a1', '¡').replace('\\u00ba', 'º')
    title = title.replace('\\u00eda', 'a').replace('\\u00f3n', 'o').replace('\\u00fal', 'u').replace('\\u00e0', 'a')

    title = title.replace('\\u00c9', 'E').replace('\\u00da', 'u')

    title = title.replace('\/', '').strip()

    return title


def search(item, texto):
    logger.info()
    itemlist1 = []
    itemlist2 = []

    try:
        item.url = web_alt + 'search/?s=' + texto.replace(" ", "+") + '&page=1'
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

