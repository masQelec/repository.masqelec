# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www3.homecine.to/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://homecine.tv/', 'https://www3.homecine.tv/', 'https://homecine.cc/']


domain = config.get_setting('dominio', 'homecine', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'homecine')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'homecine')
    else: host = domain


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_homecine_proxies', default=''):
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
    for ant in ant_hosts:
        url = url.replace(ant, host)

    hay_proxies = False
    if config.get_setting('channel_homecine_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('homecine', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

        if not data:
            if not '/?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('HomeCine', '[COLOR cyan]Re-Intentando acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('homecine', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    if '<title>Just a moment...</title>' in data:
        if not '/?s=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'homecine', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(item.clone( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_homecine', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='homecine', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_homecine', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(item.clone( channel='helper', action='show_help_homecine', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal' ))

    itemlist.append(item.clone( channel='helper', action='show_help_prales', title='[B]Cuales son sus Clones[/B]', text_color='turquoise' ))

    itemlist.append(item.clone( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'homecine' ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Búsqueda de personas:', action = '', folder=False, text_color='tan' ))

    itemlist.append(item.clone( title = ' - Buscar intérprete ...', action = 'search', search_type = 'person',
                                plot = 'Indicar el nombre y/ó apellido/s del intérprete.'))
    itemlist.append(item.clone( title = ' - Buscar dirección ...', action = 'search', search_type = 'person',
                                plot = 'Indicars el nombre y/ó apellido/s del director.'))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas-nuevas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Últimas', action = 'last_epis', url = host + 'cartelera', group = 'plast', search_type = 'movie', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host + 'cartelera', group = 'elast', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Últimas', action = 'last_epis', url = host + 'cartelera', group = 'slast', search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '<ul class="sub-menu">(.*?)</ul>')
    if not bloque: bloque = scrapertools.find_single_match(data, "<ul class='sub-menu'>(.*?)</ul>")

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?>(.*?)</a>')

    for url, title in matches:
        title = title.replace('&amp;', '&')

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = text_color ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1939, -1):
        url = host + 'release-year/' + str(x)

        itemlist.append(item.clone( title=str(x), url=url, action='list_all', text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<div data-movie-id="(.*?)</div></div>', re.DOTALL).findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        if thumb.startswith('//'): thumb = 'https:' + thumb
        elif thumb.startswith('/'): thumb = host + thumb

        title = title.replace('&amp;', '&').replace('&#8211;', '').replace('&#8217;', "'")

        year = scrapertools.find_single_match(match, 'rel="tag">(.*?)</a>')
        if not year: year = '-'

        qlty = scrapertools.find_single_match(match, '<div class="jtip-quality">(.*?)</div>')

        tipo = 'tvshow' if '/series/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            sufijo = '' if item.search_type == 'tvshow' else 'tvshow'

            itemlist.append(item.clone( action ='temporadas', url = url, title = title, thumbnail = thumb, qualities=qlty, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': year} ))

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            sufijo = '' if item.search_type == 'movie' else 'movie'

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail=thumb, qualities=qlty, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<div id="pagination".*?' + "<li class='active'>.*?href='(.*?)'")

        if next_page:
            if '/page/' in next_page:
                itemlist.append(item.clone (url = next_page, title = 'Siguientes ...', action = 'list_all', text_color='coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if item.group == 'plast':
        bloque = scrapertools.find_single_match(data, '>Ultimas Películas Agregadas(.*?)>Ultimas Series Agregadas')
    elif item.group == 'slast':
        bloque = scrapertools.find_single_match(data, '>Ultimas Series Agregadas(.*?)>Últimos Episodios Agregados')
    else:
        bloque = scrapertools.find_single_match(data, '>Últimos Episodios Agregados(.*?)$')

    matches = re.compile('<div data-movie-id="(.*?)</div></div>', re.DOTALL).findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="(.*?)"')

        title = scrapertools.find_single_match(article, 'alt="(.*?)"')

        if not title or not url: continue

        thumb = scrapertools.find_single_match(article, 'src="(.*?)"')

        if thumb.startswith('//'): thumb = 'https:' + thumb

        year = scrapertools.find_single_match(article, 'rel="tag">(.*?)</a>')
        if not year: year = '-'

        qlty = scrapertools.find_single_match(article, '<div class="jtip-quality">(.*?)</div>')

        if '-capitulo-' in url:
            season = scrapertools.find_single_match(url, '-temporada-(.*?)-')
            if not season: season = 1

            episode = scrapertools.find_single_match(article, '<span class="mli-eps">Eps<i>(.*?)</i>')
            if not episode: episode = 1

            SerieName = title

            if 'Temporada' in SerieName: SerieName = SerieName.split("Temporada")[0]

            if 'Capítulo' in SerieName: SerieName = SerieName.split("Capítulo")[0]
            if 'Capitulo' in SerieName: SerieName = SerieName.split("Capitulo")[0]

            SerieName = SerieName.strip()

            title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')
            title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

            title = title.replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')
            title = title.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
            title = title.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')

            titulo = '%sx%s %s' % (season, episode, title)

            itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, qualities=qlty,
                                        contentType='episode', contentSerieName=SerieName,
                                        contentSeason=season, contentEpisodeNumber=episode, infoLabels={'year': year} ))

            continue

        tipo = 'tvshow' if '/series/' in url else 'movie'

        if tipo == 'movie':
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail=thumb, qualities=qlty,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))
        if tipo == 'tvshow':
            if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, qualities=qlty,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<strong>Season(.*?)</strong>')

    for tempo in matches:
        tempo = tempo.strip()

        title = 'Temporada ' + tempo

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

                item.page = 0
                item.contentType = 'season'
                item.contentSeason = tempo
                itemlist = episodios(item)
                return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0,
                                    contentType = 'season', contentSeason = tempo, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item): 
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<strong>Season ' + str(item.contentSeason) + '(.*?)</div></div>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?>(.*?)</a>')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('HomeCine', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
            elif tvdb_id:
                if sum_parts > 50:
                    platformtools.dialog_notification('HomeCine', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
            else:
                item.perpage = sum_parts

                if sum_parts >= 1000:
                    if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                        platformtools.dialog_notification('HomeCine', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                        item.perpage = 500

                elif sum_parts >= 500:
                    if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                        platformtools.dialog_notification('HomeCine', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                        item.perpage = 250

                elif sum_parts >= 250:
                    if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                        platformtools.dialog_notification('HomeCine', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                        item.perpage = 125

                elif sum_parts >= 125:
                    if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                        platformtools.dialog_notification('HomeCine', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                        item.perpage = 75

                elif sum_parts > 50:
                    if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                        platformtools.dialog_notification('HomeCine', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                        item.perpage = sum_parts
                    else: item.perpage = 50

    for url, epis in matches[item.page * item.perpage:]:
        epi = scrapertools.find_single_match(epis, 'Episode(.*?)$').strip()
        if not epi: epi = 1

        titulo = str(item.contentSeason) + 'x' + str(epi) + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo,
                                    contentType='episode', ontentSeason=item.contentSeason, contentEpisodeNumber=epi ))

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

    IDIOMAS = {
      'español latino': 'Lat',
      'latino': 'Lat',
      'español castellano': 'Esp',
      'castellano': 'Esp',
      'español': 'Esp',
      'sub latino': 'Vose',
      'sub español': 'Vose',
      'subtitulado': 'Vose',
      'sub': 'Vose',
      'vose': 'Vose',
      'ingles / subtitulado': 'Vose',
      'ingles': 'VO'
      }

    data = do_downloadpage(item.url)

    ses = 0

    options = scrapertools.find_multiple_matches(data, 'href="#tab(.*?)">(.*?)</a>')

    for opt, lng in options:
        ses += 1

        qlty = scrapertools.find_single_match(lng, '(.*?)-').strip()

        lng = scrapertools.find_single_match(lng, '.*?-(.*?)$').lower().strip()

        matches = scrapertools.find_multiple_matches(data, '<iframe src="(.*?)".*?</iframe>')
        if not matches: matches = scrapertools.find_multiple_matches(data, '<IFRAME SRC="(.*?)".*?</IFRAME>')

        for url in matches:
            ses += 1

            lang = lng

            itemlist.append(Item( channel = item.channel, action = 'play', server = 'fastream', title = '', url = url, quality = qlty,
                                  language = IDIOMAS.get(lang, lang) ))

    # ~ Descargas No se tratan

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def _news(item):
    logger.info()

    item.url = host + 'cartelera'
    item.group = 'plast'
    item.search_type = 'movie'

    return last_epis(item)


def _lasts(item):
    logger.info()

    item.url = host + 'cartelera'
    item.group = 'slast'
    item.search_type = 'tvshow'

    return last_epis(item)


def _epis(item):
    logger.info()

    item.url = host + 'cartelera'
    item.group = 'elast'
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

