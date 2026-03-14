# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://vip.ikucomics.net/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_ikucomics_proxies', default=''):
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


def do_downloadpage(url, post=None, headers=None):
    hay_proxies = False
    if config.get_setting('channel_ikucomics_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('ikucomics', url, post=post, headers=headers, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if not data:
            if not '/?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('IkuComics', '[COLOR cyan]Re-Intentando acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('ikucomics', url, post=post, headers=headers, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='ikucomics', folder=False, text_color='chartreuse' ))

    itemlist.append(item_configurar_proxies(item))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host, search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'peliculas/', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '<aside class="widget-area">(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)">(.*?)</a>')

    for url, title in matches:
        title = title.replace('&amp;', '&').strip()

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = 'springgreen' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Últimas Episodios<(.*?)>Últimas Series<')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h3 class="Title">(.*?)</h3>')

        if not url or not title: continue

        season = scrapertools.find_single_match(match, '<span class="ClB">(.*?)x')
        if not season: season = 1

        epis = scrapertools.find_single_match(match, '<span class="ClB">.*?x(.*?)</span>').strip()
        if not epis: epis = 1

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]')

        titulo = '[COLOR goldenrod]Epis. [/COLOR]' + str(season) + 'x' + str(epis) + ' ' + title.replace('Capítulo ' + str(epis), '').replace('Capitulo ' + str(epis), '').strip()

        if url:
            itemlist.append(item.clone( action='findvideos', url = url, title = titulo, thumbnail=thumb,
                                        contentSerieName = title, contentType = 'episode',
                                        contentSeason = season, contentEpisodeNumber=epis, infoLabels={'year':'-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '</h1>(.*?)</section>')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        title =  scrapertools.find_single_match(match, '<h3 class="Title">(.*?)</h3>').strip()

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if not title or not url: continue

        thumb = scrapertools.find_single_match(match, 'data-src="(.*?)"')

        title = title.replace('&#8217;s', "'s").replace('&#039;', "'").replace('&#038;', '&').replace('&amp;', '&').replace('&#8211;', '').strip()

        year = scrapertools.find_single_match(match, '<span class="Year">(.*?)</span>')
        if not year: year = '-'

        tipo = 'movie' if '/movies/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<div class="wp-pagenavi">.*?<a class="next page-numbers".*?href="(.*?)".*?</main>')

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', action='list_all', url = next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, 'data-tab="(.*?)"')

    for season in matches:
        season = season.strip()

        title = 'Temporada ' + season

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

                item.page = 0
                item.contentType = 'season'
                item.contentSeason = season
                itemlist = episodios(item)
                return itemlist


        itemlist.append(item.clone( action = 'episodios', title = title, page = 0,
                                    contentType = 'season', contentSeason = season, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'data-tab="' + str(item.contentSeason) + '"(.*?)</table>')

    bloque = bloque.replace('src=&quot;', 'src="').replace('&quot;', '"')

    matches = scrapertools.find_multiple_matches(bloque, '<tr>(.*?)</tr>')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('IkuComics', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('IkuComics', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('IkuComics', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('IkuComics', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('IkuComics', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('IkuComics', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('IkuComics', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        title = scrapertools.find_single_match(match, '<td class="MvTbTtl">.*?">(.*?)</a>')

        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if not url or not title: continue

        epis = scrapertools.find_single_match(match, '<td><span class="Num">(.*?)</span>')

        title = title.replace('Episodio ', '[COLOR goldenrod]Epis. [/COLOR]').replace('episodio ','[COLOR goldenrod]Epis. [/COLOR]')

        if 'Epis. ' in title: title = title + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
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

    IDIOMAS = {'Castellano': 'Esp', 'Latino': 'Lat', 'Subtitulado': 'Vose', 'Sub Latino': 'Vose'}

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="TPlayer">(.*?)</span>')

    bloque = bloque.replace('src=&quot;', 'src="').replace('&quot;', '"').replace('&lt;/iframe&gt;', '</iframe>')

    options = scrapertools.find_multiple_matches(str(bloque), 'id="Opt(.*?)</iframe>')

    ses = 0

    for opt in options:
        ses += 1

        num_opt = scrapertools.find_single_match(opt, '(.*?)"')

        lang = scrapertools.find_single_match(data, 'data-tplayernv="Opt' + num_opt + '".*?</span><span>(.*?)</span>')

        lang = scrapertools.find_single_match(lang, '(.*?)-').strip()

        url = scrapertools.find_single_match(opt, 'src="(.*?)"')
        if 'about:blank' in url: url = scrapertools.find_single_match(opt, 'data-lazy-src="(.*?)"')

        if url:
            srv = scrapertools.find_single_match(data, 'data-tplayernv="Opt' + num_opt + '".*?<span>(.*?)</span>').lower().strip()

            if srv == 'viewsb': continue

            elif srv == 'ok': srv = 'okru'
            elif srv == 'dood': srv = 'doodstream'

            if srv == 'links':
                url = url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

                data1 = do_downloadpage(url)

                new_url = scrapertools.find_single_match(data1, '<div class="Video">.*?src="(.*?)"')

                if not new_url: continue

                data1 = do_downloadpage(new_url)

                links1 = scrapertools.find_multiple_matches(str(data1), '<li onclick="go_to_player' + ".*?'(.*?)'")
                links2 = scrapertools.find_multiple_matches(str(data1), '<a href="(.*?)"')

                links = links1 + links2

                for url in links:
                    if '/ul.' in url: continue
                    elif '/1fichier.' in url: continue
                    elif '/rapidgator' in url: continue
                    elif '/katfile' in url: continue
                    elif '/nitro' in url: continue
                    elif '/filecrypt.' in url: continue
                    elif '/filepv.' in url: continue

                    elif '/multiup.' in url: continue
                    elif '/filemirage.' in url: continue
                    elif '/powvideo.' in url: continue

                    elif '/viewsb.' in url: continue
                    elif '/www.fembed.' in url: continue
                    elif '/fembed.' in url: continue

                    elif 'lvturbo' in url: continue
                    elif 'vanfem' in url: continue
                    elif 'fembed' in url: continue
                    elif 'fcom' in url: continue

                    lang = '?'
                    if '#idioma=lat' in url: lang = 'Lat'
                    elif '#lang=lat' in url: lang = 'Lat'

                    elif '#idioma=cas' in url: lang = 'Esp'
                    elif '#lang=cas' in url: lang = 'Esp'

                    elif '#idioma=vos' in url: lang = 'Vose'
                    elif '#lang=vos' in url: lang = 'Vose'

                    if '#idioma' in url: url = url.split("#idioma")[0]
                    elif '#lang=' in url: url = url.split("#lang=")[0]

                    if '/player.cuevana.ac/' in url: url = url.replace('/player.cuevana.ac/', '/waaw.to/')
                    elif '/player.cuevana.one/' in url: url = url.replace('/player.cuevana3.one/', '/waaw.to/')

                    servidor = servertools.get_server_from_url(url)

                    if servertools.is_server_available(servidor):
                        if not servertools.is_server_enabled(servidor): continue
                    else:
                        if not config.get_setting('developer_mode', default=False): continue

                    url = servertools.normalize_url(servidor, url)

                    other = ''
                    if servidor == 'various': other = servertools.corregir_other(url)
                    elif servidor == 'zures': other = servertools.corregir_zures(url)

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url,
                                          language = lang, other = other ))

                continue

            other = ''
            if srv == 'various': other = servertools.corregir_other(srv)
            elif srv == 'zures': other = servertools.corregir_zures(srv)

            elif srv == 'player':
                srv = ''
                other = 'Player'

            itemlist.append(Item(channel = item.channel, action = 'play', server=srv, title = '', url=url,
                                 language=IDIOMAS.get(lang,lang), other=other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    item.url = item.url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

    url_play = item.url

    data = do_downloadpage(item.url)

    new_url = scrapertools.find_single_match(data, '<div class="Video">.*?src="(.*?)"')

    if new_url:
        new_url = new_url.replace('/player.cuevana.ac/', '/waaw.to/').replace('/player.cuevana3.one/', '/waaw.to/')

        url_play = new_url

    if url_play:
        servidor = servertools.get_server_from_url(url_play)

        url_play = servertools.normalize_url(servidor, url_play)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url_play).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url_play, server = servidor))

    return itemlist


def _epis(item):
    logger.info()

    item.url = host
    item.search_type = 'tvshow'

    return last_epis(item)


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
