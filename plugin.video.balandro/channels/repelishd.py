# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://repelishd.city/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_repelishd_proxies', default=''):
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
    # ~ por si viene de enlaces guardados
    ant_hosts = ['https://repelishd.cam/']

    for ant in ant_hosts:
        url = url.replace(ant, host)

    if not headers: headers = {'Referer': host}

    if '/xfsearch/year/' in url: raise_weberror = False

    hay_proxies = False
    if config.get_setting('channel_repelishd_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('repelishd', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

        if not data:
            if not '?story=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('RepelisHd', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('repelishd', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='repelishd', folder=False, text_color='chartreuse' ))

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

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'cine/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'tvshow' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie':
        text_color = 'deepskyblue'
        url_idio = host + 'cine/'
    else:
        text_color = 'hotpink'
        url_idio = host + 'series/'

    itemlist.append(item.clone( title = 'Castellano', action = 'list_all', url = url_idio + '?language=castellano', text_color = text_color ))
    itemlist.append(item.clone( title = 'Latino', action = 'list_all', url = url_idio + '?language=latino', text_color = text_color ))
    itemlist.append(item.clone( title = 'Subtitulado', action = 'list_all', url = url_idio + '?language=sub', text_color = text_color ))

    return itemlist


def calidades(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'cine/')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Calidad(.*?)<span>Aplicar')

    matches = scrapertools.find_multiple_matches(bloque, 'value="(.*?)"')

    for value in matches:
        title = value

        url = host + 'pelicula/?quality=' + value

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = 'deepskyblue' ))

    return sorted(itemlist,key=lambda x: x.title)


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'cine/')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Genres(.*?)<span>Aplicar')

    matches = scrapertools.find_multiple_matches(bloque, 'value="(.*?)".*?<label for=".*?">(.*?)</label>')

    for value, title in matches:
        if title == 'Cine/Estrenos': continue
        elif title == 'Series': continue

        title = title.capitalize()

        url = host + 'cine/?genere=' + value

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = 'deepskyblue' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    from datetime import datetime
    current_year = int(datetime.today().year)

    if item.search_type == 'movie': limit = 1929
    else: limit = 1999

    for x in range(current_year, limit, -1):
        url = host + '/xfsearch/year/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color = text_color ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie':
        text_color = 'deepskyblue'
        url_pais = host + 'cine/'
    else:
        text_color = 'hotpink'
        url_pais = host + 'series/'

    data = do_downloadpage(host + 'cine/')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'País(.*?)<span>Aplicar')

    matches = scrapertools.find_multiple_matches(bloque, 'value="(.*?)"')

    for value in matches:
        title = value

        url = url_pais + '?country=' + value

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = text_color ))

    return sorted(itemlist,key=lambda x: x.title)


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'Añadido recientemente<(.*?)>Películas Destacadas<')

    matches = re.compile('<article(.*?)</article>').findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, '<a href="(.*?)"')

        title = scrapertools.find_single_match(article, 'alt="(.*?)"')

        if not url or not title: continue

        title = title.replace("&#8217;", "'").replace("&amp;", '&')

        thumb = scrapertools.find_single_match(article, '<img src="(.*?)"')
        if not 'https' in thumb: thumb = host[:-1] + thumb

        qlty = scrapertools.find_single_match(article, '<span class="quality">(.*?)</span>')

        langs = []
        if '<div class="castellano"' in article: langs.append('Esp')
        if '<div class="latino"' in article: langs.append('Lat')
        if '<div class="subtitulado"' in article: langs.append('Vose')

        year = scrapertools.find_single_match(article, '</h3> <span>(.*?)</span>')
        if not year: year = '-'

        tipo = 'tvshow' if 'style="background-color:' in article or item.search_type == 'tvshow' else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            itemlist.append(item.clone( action ='temporadas', url = url, title = title, thumbnail = thumb, qualities=qlty, languages=', '.join(langs),
                                        fmt_sufijo=sufijo, contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': year} ))

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title = title, thumbnail = thumb, qualities=qlty, languages=', '.join(langs),
                                        fmt_sufijo=sufijo, contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<div class="pagination">' in data:
            next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?</span>.*?<a href="(.*?)"')

            if next_page:
                if '/page/' in next_page:
                    itemlist.append(item.clone( title='Siguientes ...', url = next_page, action='list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if not 'id="season-' in data:
        platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]No es Una Serie[/B][/COLOR]')
        return

    matches = re.compile('id="season-(.*?)"', re.DOTALL).findall(data)

    for season in matches:
        title = 'Temporada ' + season

        url = item.url

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.page = 0
            item.url = url
            item.contentType = 'season'
            item.contentSeason = season
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, url = url, page = 0,
                                    contentType = 'season', contentSeason = season, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    season = item.contentSeason

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'id="season-' + str(season) + '"(.*?)</ul></div>')

    matches = re.compile("<li>(.*?)</li>").findall(bloque)

    if item.page == 0:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('RePelisHd', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('RePelisHd', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('RePelisHd', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('RePelisHd', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]100[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('RePelisHd', '[COLOR cyan]Cargando 100 elementos[/COLOR]')
                    item.perpage = 100

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('RePelisHd', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts

    for datos in matches[item.page * item.perpage:]:
        url = scrapertools.find_single_match(datos, 'data-link="(.*?)"')
        title = scrapertools.find_single_match(datos, 'data-title="(.*?)"')

        if not url or not title: continue

        epis = scrapertools.find_single_match(datos, 'data-num=".*?x(.*?)"')

        titulo = season + 'x' + epis + ' ' + title + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        itemlist.append(item.clone( action = 'findvideos', datos = datos, title = titulo,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > (item.page + 1) * item.perpage:
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'castellano': 'Esp', 'español': 'Esp', 'latino': 'Lat', 'subtitulado': 'Vose', 'sub español': 'Vose'}

    lang = item.languages

    if not lang: lang = '?'

    ses = 0

    if item.datos:
        matches = re.compile('data-link="(.*?)"').findall(item.datos)

        for url in matches:
            ses += 1

            if url.startswith('/player/'): continue

            elif '/verhdlink.' in url: continue

            if not 'http' in url: url = 'https:' + url

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)

            itemlist.append(Item( channel = item.channel, action = 'play', url = url, server = servidor, title = '', language=lang, other=other ))

            continue

        if itemlist: return itemlist

        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
        return

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if 'id="season-' in data:
        platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Es Una Serie[/B][/COLOR]')
        return

    enlace = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')

    if not enlace: return itemlist

    datae = do_downloadpage(enlace)
    datae = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', datae)

    actives = scrapertools.find_multiple_matches(datae, '<ul class="_player-mirrors (.*?)</ul>')

    for active in actives:
        ses += 1

        if 'castellano' in active or 'español' in active: lang = 'Esp'
        elif 'latino' in active: lang = 'Lat'
        elif 'subtitulado' in active: lang = 'Vose'
        else: lang = '?'

        urls = scrapertools.find_multiple_matches(active, 'data-link="(.*?)"')

        for url in urls:
            ses += 1

            if '/verhdlink.' in url: continue

            if not 'http' in url: url = 'https:' + url

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)

            itemlist.append(Item( channel = item.channel, action = 'play', url = url, server = servidor, title = '', language=lang, other=other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
        url = host

        if item.search_type == 'movie': url = host + 'cine/'
        elif item.search_type == 'tvshow': url = host + 'series/'

        item.url = url + '?story=' + texto.replace(" ", "+") + '&do=search&subaction=search'
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
