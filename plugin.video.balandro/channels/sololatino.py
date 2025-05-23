# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


from lib.pyberishaes import GibberishAES


host = 'https://sololatino.net/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_sololatino_proxies', default=''):
        tit = '[COLOR %s][B]Quitar los proxies del canal[/B][/COLOR]' % color_list_proxies
        context.append({'title': tit, 'channel': item.channel, 'action': 'quitar_proxies'})

    tit = '[COLOR %s]Ajustes categoría proxies[/COLOR]' % color_exec
    context.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    return item.clone( title = '[B]Configurar proxies a usar ...[/B]', action = 'configurar_proxies', folder=False, context=context, plot=plot, text_color='red' )

def quitar_proxies(item):
    from modules import submnuctext
    submnuctext._quitar_proxies(item)
    return True

def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if '/filtro/' in url: raise_weberror = False

    hay_proxies = False
    if config.get_setting('channel_sololatino_proxies', default=''): hay_proxies = True

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('sololatino', url, post=post, headers=headers, raise_weberror=raise_weberror).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

        if not data:
            if not '/?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('sololatino', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='sololatino', folder=False, text_color='chartreuse' ))

    itemlist.append(item_configurar_proxies(item))

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

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'pelicula/estrenos/', search_type = 'movie', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'pelicula/mejor-valoradas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host + 'series/novedades/', group = 'lasts', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'series/mejor-valoradas/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Animación', action = 'list_all', url = host + 'genre_series/toons/', search_type = 'tvshow', text_color = 'greenyellow' ))

    itemlist.append(item.clone( title = 'Por plataforma', action= 'plataformas', search_type='tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'animes/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host + 'animes/novedades/', group = 'animes', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'animes/mejor-valoradas/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', group = 'animes', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', group = 'animes', search_type = 'tvshow' ))

    return itemlist


def plataformas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Amazon', action = 'list_all', url = host + 'network/amazon/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Disney+', action = 'list_all', url = host + 'network/disney/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Hbo', action = 'list_all', url = host + 'network/hbo/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Hbo Max', action = 'list_all', url = host + 'network/hbo-max/', search_type = 'tvshow', text_color = 'moccasin' ))
    itemlist.append(item.clone( title = 'Netflix', action = 'list_all', url = host + 'network/netflix/', search_type = 'tvshow', text_color = 'moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie':
        url_gen = host + 'peliculas/'
        text_color = 'deepskyblue'
    else:
       if item.group == 'animes':
           url_gen = host + 'animes/'
           text_color = 'springgreen'
       else:
           url_gen = host + 'series/'
           text_color = 'hotpink'

    data = do_downloadpage(url_gen)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('data-type="genre" data-value="(.*?)"').findall(data)

    for title in matches:
        if config.get_setting('descartar_anime', default=False):
           if title == 'anime': continue

        if item.search_type == 'movie': url = host + 'pelicula/filtro/?genre=' + title + '&year='
        else:
            if item.group == 'animes': url = host + 'animes/filtro/?genre=' + title + '&year='
            else: url = host + 'series/filtro/?genre=' + title + '&year='

        title = title.replace('-123-123-123-123', '').replace('-123-123', '').strip()

        itemlist.append(item.clone( title = title.capitalize(), action = 'list_all', url = url, text_color = text_color ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie':
        url_gen = host + 'peliculas/'
        text_color = 'deepskyblue'
    else:
       if item.group == 'animes':
           url_gen = host + 'animes/'
           text_color = 'springgreen'
       else:
           url_gen = host + 'series/'
           text_color = 'hotpink'

    if item.search_type == 'movie': tope_year = 1931
    else:
        if item.group == 'animes': tope_year = 1989
        else: tope_year = 1981

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, tope_year, -1):
        if item.search_type == 'movie': url = host + 'pelicula/filtro/?genre=&year=' + str(x) + '/'
        else:
            if item.group == 'animes': url = host + 'animes/filtro/?genre=&year=' + str(x) + '/'
            else: url = host + 'series/filtro/?genre=&year=' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color = text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        title = title.replace('&#8230;', '').replace('&#8211;', '').replace('&#038;', '').replace('&#8217;', "'").strip()

        thumb = scrapertools.find_single_match(match, '<data-srcset="(.*?)"')

        year = scrapertools.find_single_match(match, '<div class="data"><p>(.*?)</p>')
        if not year: year = '-'

        tipo = 'movie' if '/peliculas/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            if not item.group:
                itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                            contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))
            else:
                season = scrapertools.find_single_match(match, '<h3><span>(.*?)-').strip()
                episode = scrapertools.find_single_match(match, '<h3><span>.*?-(.*?)</span>').strip()

                if not season: season = 1
                if not episode: episode = 1

                if ': ' in title: title = title.split(": ")[0]

                title = title.replace('&#215;', ' ').strip()

                titulo = '[COLOR goldenrod]Epis. [/COLOR]' + str(season) + 'x' + str(episode) + ' ' + title

                SerieName = title

                if ': ' in SerieName: SerieName = SerieName.split(": ")[0]

                itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, fmt_sufijo=sufijo,
                                            contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber = episode,
                                            infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if 'Pagina Anterior' in data:
            next_url = scrapertools.find_single_match(data, '<div class="pagMovidy">.*?Pagina Anterior.*?<a href="(.*?)"')
        else:
            next_url = scrapertools.find_single_match(data, '<div class="pagMovidy">.*?<a href="(.*?)"')

        if next_url:
            if '/page/' in next_url:
                itemlist.append(item.clone( title = 'Siguientes ...', url = next_url, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    temporadas = re.compile('class="clickSeason.*?data-season="(.*?)"', re.DOTALL).findall(data)

    for tempo in temporadas:
        title = 'Temporada ' + tempo

        if len(temporadas) == 1:
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

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="se-c".*?data-season="' + str(item.contentSeason) + '"(.*?)</li></ul></div>')
    if not bloque: bloque = scrapertools.find_single_match(data, "<div class='se-c'.*?data-season='" + str(item.contentSeason) + "'(.*?)</li></ul></div>")

    matches = re.compile('<li class="mark-.*?<a href="(.*?)".*?<img src="(.*?)".*?<div class="epst">(.*?)</div>.*?<div class="numerando">(.*?)</div>', re.DOTALL).findall(bloque)
    if not matches: matches = re.compile("<li class='mark-.*?<a href='(.*?)'.*?<img src='(.*?)'.*?<div class='epst'>(.*?)</div>.*?<div class='numerando'>(.*?)</div>", re.DOTALL).findall(bloque)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('SoloLatino', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, thumb, title, ses_epi in matches[item.page * item.perpage:]:
        season = scrapertools.find_single_match(ses_epi, '(.*?)-').strip()
        episode = scrapertools.find_single_match(ses_epi, '.*?-(.*?)$').strip()

        if not season: season = 1
        if not episode: episode = 1

        titulo = str(season) + 'x' + str(episode) + ' ' + title

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail=thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=episode ))

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

    ses = 0

    # ~ P1
    matches = scrapertools.find_multiple_matches(data, 'dooplay_player_response_.*?src="(.*?)"')

    for stream in matches:
        ses += 1

        if not stream: continue

        if not 'http' in stream: continue
        elif stream.endswith('.js'): continue

        data_s = do_downloadpage(stream)


        if '//embed69.' in stream:
            ses += 1

            datae = data_s

            dataLink = scrapertools.find_single_match(datae, 'const dataLink =(.*?);')
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
                elif 'JAP' in lang: lang = 'Jap'
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

                    servidor = servertools.corregir_servidor(srv)

                    if servertools.is_server_available(servidor):
                        if not servertools.is_server_enabled(servidor): continue
                    else:
                        if not config.get_setting('developer_mode', default=False): continue

                    other = ''

                    if servidor == 'various': other = servertools.corregir_other(srv)

                    if servidor == 'directo':
                        if not config.get_setting('developer_mode', default=False): continue
                        else:
                           other = url.split("/")[2]
                           other = other.replace('https:', '').strip()

                    itemlist.append(Item( channel = item.channel, action = 'play', server=servidor, title = '', crypto=link, bytes=e_bytes, age=age,
                                          language=lang, other=other ))

                continue

        if '//xupalace.' in stream:
            ses += 1

            lang = '?'

            if 'php?id=' in stream:
                datax = do_downloadpage(stream)

                url = scrapertools.find_single_match(datax, '<iframe src="(.*?)"')

                if url:
                    servidor = servertools.get_server_from_url(url)
                    servidor = servertools.corregir_servidor(servidor)

                    if servertools.is_server_available(servidor):
                        if not servertools.is_server_enabled(servidor): continue
                    else:
                        if not config.get_setting('developer_mode', default=False): continue

                    url = servertools.normalize_url(servidor, url)

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url=url, language=lang, other=other ))

                continue

            elif '/video/' in stream:
                datax = do_downloadpage(stream)

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
                    servidor = servertools.corregir_servidor(servidor)

                    if servertools.is_server_available(servidor):
                        if not servertools.is_server_enabled(servidor): continue 
                    else:
                        if not config.get_setting('developer_mode', default=False): continue

                    url = servertools.normalize_url(servidor, matchx)

                    other = ''
                    if servidor == 'various': other = servertools.corregir_other(url)

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url=url, language=lang, other=other ))

                continue

        # ~ Otros
        links = scrapertools.find_multiple_matches(data_s, '<li onclick="go_to_playerVast(.*?)>')

        for link in links:
            url = scrapertools.find_single_match(str(link), "'(.*?)'")
            if not url: url = scrapertools.find_single_match(str(link), '"(.*?)"')

            if not url: continue

            if '/plustream.' in url: continue
            elif '/embedsito.' in url: continue
            elif '/xupalace.' in url: continue

            if 'data-lang="0"' in link: lang = 'Lat'
            elif 'data-lang="1"' in link: lang = 'Esp'
            elif 'data-lang="2"' in link: lang = 'Vose'
            elif 'data-lang="3"' in link: lang = 'Jap'
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

            if servidor == 'directo':
                if not config.get_setting('developer_mode', default=False): continue
                other = url.split("/")[2]
                other = other.replace('https:', '').strip()

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = lang, other = other.capitalize() ))

    # ~ P2
    match = scrapertools.find_single_match(data, '"dooplay_player_option ".*?<iframe.*?src="(.*?)".*?</iframe>')

    if match:
        if not '//embed69.' in match:
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
                servidor = servertools.corregir_servidor(servidor)

                if servertools.is_server_available(servidor):
                    if not servertools.is_server_enabled(servidor): continue 
                else:
                    if not config.get_setting('developer_mode', default=False): continue

                url = servertools.normalize_url(servidor, matchx)

                other = ''
                if servidor == 'various': other = servertools.corregir_other(url)

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url=url, language=lang, other=other, age='P2' ))


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

        try:
            url = GibberishAES.dec(GibberishAES(), string = crypto, pass_ = bytes)
        except:
            url = ''

        if not url:
            if crypto.startswith("http"):
                url = crypto.replace('\\/', '/')

            if not url:
                return '[COLOR cyan]No se pudo [COLOR goldenrod]Descifrar[/COLOR]'

        elif not url.startswith("http"):
            return '[COLOR cyan]No se pudo [COLOR goldenrod]Descifrar[/COLOR]'

    if url:
        if '/xupalace.' in url or '/uploadfox.' in url:
            return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"): servidor = new_server

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

