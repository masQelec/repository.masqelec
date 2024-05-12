# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://tiodonghua.com/'


def do_downloadpage(url, post=None, headers=None):
    if not headers: headers = {'Referer': host}

    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_animes(item)


def mainlist_animes(item):
    logger.info()
    itemlist = []

    if config.get_setting('descartar_anime', default=False): return

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'donghua/', group = 'donghua', search_type = 'tvshow' )) 

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host + 'episodios/', group = 'last_epis', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Animes', action = 'list_all', url = host + 'anime/', group = 'animes', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Donghuas', action = 'list_all', url = host + 'genero/donghua/', search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos',  search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    opciones = [
       ('accion', 'Acción'),
       ('action-adventure', 'Accion y Aventura'),
       ('animacion', 'Animación'),
       ('anime-japones', 'Anime Japonés'),
       ('artes-marciales', 'Artes Marciales'),
       ('aventura', 'Aventura'),
       ('ciencia-ficcion', 'Ciencia Ficción'),
       ('comedia', 'Comedia'),
       ('demonios', 'Demonios'),
       ('drama', 'Drama'),
       ('fantasia', 'Fantasía'),
       ('misterio', 'Misterio'),
       ('musica', 'Música'),
       ('patreon', 'Patreon'),
       ('romance', 'Romance'),
       ('sci-fi-fantasy', 'Sci-Fi & Fantasy'),
       ('terror', 'Terror')
    ]

    for opc, tit in opciones:
        group = ''

        if opc == 'action-adventure': group = 'donghua'
        elif opc == 'animacion': group = 'donghua'
        elif opc == 'comedia': group = 'donghua'
        elif opc == 'drama': group = 'donghua'
        elif opc == 'sci-fi-fantasy': group = 'donghua'

        elif opc == 'anime-japones': group = 'generos'

        itemlist.append(item.clone( title=tit, url = host + 'genero/' + opc + '/', action = 'list_all', group = group, text_color = 'springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if item.group == 'animes':
         bloque = scrapertools.find_single_match(data, '>Nuevos Episodios<(.*?)>Recomendaciones<')
    else:
         bloque = scrapertools.find_single_match(data, '>Añadido recientemente<(.*?)>Lo mas Popular<')

    if not bloque: bloque = data

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        if '>Película<' in match: continue
        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        title = title.replace('&#8211;', '').replace('&#8217;', '').replace('&#8220;', '').replace('&#8221;', '').strip()

        year = scrapertools.find_single_match(match, '</h3><span>(.*?)</span>')
        if not year: year = '-'

        SerieName = title

        if 'Sub Español' in SerieName: SerieName = SerieName.split("Sub Español")[0]
        if 'Traducida al Español' in SerieName: SerieName = SerieName.split("Traducida al Español")[0]
        if 'Legendado Portugués' in SerieName: SerieName = SerieName.split("Legendado Portugués")[0]
        if 'Portugués' in SerieName: SerieName = SerieName.split("Portugués")[0]

        if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
        if 'Movie' in SerieName: SerieName = SerieName.split("Movie")[0]
        if '(TV)' in SerieName: SerieName = SerieName.split("(TV)")[0]

        SerieName = SerieName.strip()

        if '>T2' in match: season = 2
        elif '>T3' in match: season = 3
        elif '>T4' in match: season = 4
        elif '>T5' in match: season = 5
        elif '>T6' in match: season = 5
        else: season = 1

        if item.group == 'last_epis':
            if 'Episodio' in SerieName: SerieName = SerieName.split("Episodio")[0]

            epi = scrapertools.find_single_match(match, '>Episodio(.*?)</a>').strip()

            title = title.replace('Episodio ', '[COLOR goldenrod]Episodio [/COLOR]')

            itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail = thumb,
                                        contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber = epi ))
        else:
            if item.group == 'donghua': url = url.replace('/donghua/', '/anime/anime/')

            elif item.group == 'generos': url = url.replace('/donghua/', '/anime/anime/')

            elif item.group == 'animes':
                epi = scrapertools.find_single_match(match, '<span class="epx">Ep(.*?)</span>').strip()

                if not epi: epi = 1
                season = 1

                itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail = thumb,
                                            contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber = epi ))

                continue

            itemlist.append(item.clone( action = 'episodios', url = url, title = title, thumbnail = thumb, infoLabels={'year': year},
                                        contentSerieName = SerieName, contentType = 'tvshow', contentSeason = season  ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data,'<div class="pagination">.*?<span class="current">.*?ref="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

        elif '<div class="hpage">' in data:
            if 'Previous' in data:
                next_page = scrapertools.find_single_match(data,'<div class="hpage">.*?Previous.*?ref="(.*?)"')
            else:
                next_page = scrapertools.find_single_match(data,'<div class="hpage">.*?ref="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    epis = scrapertools.find_multiple_matches(data, "<li class='mark-.*?data-src='(.*?)'.*?<div class='numerando'>(.*?)</div>.*?<a href='(.*?)'>(.*?)</a>")
    if not epis: epis = scrapertools.find_multiple_matches(data, '<li class="mark-.*?src="(.*?)".*?<div class="numerando">(.*?)</div>.*?<a href="(.*?)">(.*?)</a>')

    if not epis:
        if item.group == 'donghua' or item.group == 'generos':
            bloque = scrapertools.find_single_match(data, '</a></div><div class="inepcx">(.*?)</a></li></ul>')

            if '<div class="eplister">': bloque = scrapertools.find_single_match(bloque, '<div class="eplister">(.*?)$')

            links = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)"')

            for url in links:
                epi = scrapertools.find_single_match(bloque, '<a href="' + url + '".*?<div class="epl-num">(.*?)</div>').strip()

                if not epi: epi = 1
                item.contentSeason = 1

                titulo = '%sx%s - %s' % (str(item.contentSeason), epi, item.contentSerieName)

                itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                            contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epi ))

            return itemlist

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(epis)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True): item.perpage = sum_parts
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('TioDonghua', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('TioDonghua', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('TioDonghua', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('TioDonghua', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('TioDonghua', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('TioDonghua', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for thumb, temp_epi, url, title in epis[item.page * item.perpage:]:
        epi = scrapertools.find_single_match(temp_epi, '.*?-(.*?)$').strip()

        titulo = '%sx%s - %s' % (str(item.contentSeason), epi, title)

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail = thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epi ))

        if len(itemlist) >= item.perpage:
            break

    if itemlist:
        if len(epis) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, "<li id='player-option-(.*?)</span></li>")
    if not matches: matches = scrapertools.find_multiple_matches(data, '<li id="player-option-(.*?)</span></li>')
    ses = 0

    for match in matches:
        ses += 1

        d_type = scrapertools.find_single_match(match, "data-type='(.*?)'")
        if not d_type: d_type = scrapertools.find_single_match(match, 'data-type="(.*?)"')

        d_post = scrapertools.find_single_match(match, "data-post='(.*?)'")
        if not d_post: d_post = scrapertools.find_single_match(match, 'data-post="(.*?)"')

        d_nume = scrapertools.find_single_match(match, "data-nume='(.*?)'")
        if not d_nume: d_nume = scrapertools.find_single_match(match, 'data-nume="(.*?)"')

        if not d_type or not d_post or not d_nume: continue

        post = {'action': 'doo_player_ajax', 'post': d_post, 'nume': d_nume, 'type': d_type}

        data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = post)

        url = scrapertools.find_single_match(data, '"embed_url":.*?"(.*?)"')

        if '<iframe' in url or '<IFRAME' in url:
             data = str(data).replace('=\\', '=').replace('\\"', '/"')

             url = scrapertools.find_single_match(str(data), '<iframe.*?src="(.*?)"')
             if not url: url = scrapertools.find_single_match(str(data), '<IFRAME.*?SRC="(.*?)"')

        url = url.replace('\\/', '/')

        if not url: continue

        if '/terabox.' in url: continue
        elif '/nephobox.' in url: continue
        elif '.modagamers.' in url: continue
        elif 'cuyplay.com' in url: continue
        elif 'digitalxona.com' in url: continue
        elif 'animetemaefiore.club' in url: continue
        elif 'guccihide.com' in url: continue
        elif 'sharezweb.com' in url: continue
        elif 'videopress.com' in url: continue
        elif 'tioplayer.com' in url: continue
        elif 'likessb.com' in url: continue

        if 'http:' in url: url = url.replace('http:', 'https:')

        if not 'https:' in url: url = 'https:' + url

        if 'es.png' in match: lang = 'Esp'
        elif 'mx.png' in match: lang = 'Lat'
        elif 'br.png' in match: lang = 'Pt'
        elif 'en.png' in match: lang = 'Vose'
        else: lang = '?'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        other = servidor

        if servidor == 'various': other = servertools.corregir_other(url)

        if servidor == other: other = ''

        elif not servidor == 'directo':
           if not servidor == 'various': other = ''

        if servidor == 'directo':
            if config.get_setting('developer_mode', default=False):
                other = url.split("/")[2]
                other = other.replace('https:', '').strip()

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = lang, other = other ))

    if '<strong>DL</strong>' in data:
        url = scrapertools.find_single_match(data, '<strong>DL</strong>.*?<a href="(.*?)"')

        if url:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = 'Vose' ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url =  host + "?s=" + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
