# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, jsontools, scrapertools, servertools, tmdb


host = 'https://allcalidad.re/'


api = host + 'api/rest/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://elifilms.net/', 'https://elifilms.org/', 'https://allcalidad.si/',
             'https://allcalidad.ms/']


domain = config.get_setting('dominio', 'elifilms', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'elifilms')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'elifilms')
    else: host = domain


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_elifilms_proxies', default=''):
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
    # ~ por si viene de enlaces guardados
    for ant in ant_hosts:
        url = url.replace(ant, host)

    hay_proxies = False
    if config.get_setting('channel_elifilms_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    raise_weberror = False if 'tax=years&term=' in url else True

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('elifilms', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

        if not data:
            if not '?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('EliFilms', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('elifilms', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'elifilms', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_elifilms', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='elifilms', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_elifilms', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'elifilms', thumbnail=config.get_thumb('elifilms') ))

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = api + 'listing?page=1&post_type=movies&posts_per_page=25', _next = '&post_type=movies&posts_per_page=25', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = api + 'tops?range=month&limit=25&post_type=movies', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = api + 'listing?page=1&post_type=tvshows&posts_per_page=25', _next = '&post_type=tvshows&posts_per_page=25', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = api + 'tops?range=month&limit=25&post_type=tvshows', search_type = 'tvshow' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title = 'Animes', action = 'mainlist_animes', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', group = 'animes', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = api + 'listing?page=1&post_type=animes&posts_per_page=25', _next = '&post_type=animes&posts_per_page=25', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = api + 'tops?range=month&limit=25&post_type=animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', group = 'animes', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', group = 'animes', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       if item.group == 'animes': text_color = 'springgreen'
       else: text_color = 'hotpink'

    genres = [
       'accion',
       'action-adventure',
       'animacion',
       'aventura',
       'belica',
       'ciencia-ficcion',
       'comedia',
       'crimen',
       'documental',
       'drama',
       'familia',
       'fantasia',
       'guerra',
       'kids',
       'romance',
       'misterio',
       'musica',
       'pelicula-de-tv',
       'reality',
       'romance',
       'sci-fi-fantasy',
       'suspense',
       'terror',
       'war-politics',
       'western'
       ]

    for genre in genres:
        if item.search_type == 'movie': _next = '&post_type=movies&posts_per_page=25'
        else:
           if item.group == 'animes':  _next = '&post_type=animes&posts_per_page=25'
           else: _next = '&post_type=tvshows&posts_per_page=25'

        url = api + 'listing?tax=genres&term=' + genre + '&page=1' + _next

        title = genre.replace('-', ' ').capitalize()

        itemlist.append(item.clone( title=title, url=url, _next=_next, action='list_all', text_color = text_color ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       if item.group == 'animes': text_color = 'springgreen'
       else: text_color = 'hotpink'

    from datetime import datetime
    current_year = int(datetime.today().year)

    if item.search_type == 'movie': limit = 1939
    else:
       if item.group == 'animes': limit = 1989
       else: limit = 1959

    for x in range(current_year, limit, -1):
        if item.search_type == 'movie': _next = '&post_type=movies&posts_per_page=25'
        else:
           if item.group == 'animes':  _next = '&post_type=animes&posts_per_page=25'
           else: _next = '&post_type=tvshows&posts_per_page=25'

        url = api + 'listing?tax=years&term=' + str(x) + '&page=1' + _next
		
        itemlist.append(item.clone( title=str(x), url=url, _next=_next, action='list_all', text_color = text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    try:
       jdata = jsontools.load(data)

       _jdata = jdata['data']

       if not item._next: _p_jdata = _jdata
       else: _p_jdata = _jdata['posts']
    except:
        return itemlist

    for match in _p_jdata:
        id = scrapertools.find_single_match(str(match), "'_id':(.*?),").strip()
        title = scrapertools.find_single_match(str(match), "'title':.*?'(.*?)'")

        if not id or not title: continue

        thumb = scrapertools.find_single_match(str(match), "'poster':.*?'(.*?)'")

        thumb = host[:-1] + thumb

        year = scrapertools.find_single_match(title, '(\d{4})')

        if not year: year = '-'
        else: title = title.replace('(' + year + ')', '').strip()
 
        title = title.replace('&#8211;', '').replace('&#8217;', '').replace('#038;', '').replace('&amp;', '&')

        tipo = 'movie' if "'movies'" in str(match) else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            url = api + 'player?post_id=' + id + '&_any=1'

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            if item.group == 'animes':
                if not "'animes'" in str(match): continue

            itemlist.append(item.clone( action='temporadas', id=id, title=title, thumbnail=thumb, fmt_sufijo=sufijo, 
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if not item._next: return itemlist

    if itemlist:
        pag_jdata = _jdata['pagination']

        next_page = scrapertools.find_single_match(str(pag_jdata), "'next_page_url':.*?'(.*?)'")

        if next_page:
            if 'page=' in next_page:
                next_page = next_page + item._next

                itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(api + 'episodes?post_id=' + item.id)

    ant_tempo = ''

    temporadas = scrapertools.find_multiple_matches(str(data), '"season_number":.*?(.*?),')

    for tempo in temporadas:
        season = tempo.strip()

        title = 'Temporada ' + season

        if not ant_tempo:
            ant_tempo = season
        else:
           if season == ant_tempo: continue
           ant_tempo = season

        if len(temporadas) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = int(season)
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = int(season), text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(api + 'episodes?post_id=' + item.id)

    try:
        jdata = jsontools.load(data)
        _jdata = jdata['data']

        _jdata = str(_jdata).replace('},', '-Fin').replace('}]', '-Fin').replace('[{', '').replace('{', '').replace('}', '')
    except:
        return itemlist

    matches = scrapertools.find_multiple_matches(str(_jdata), '(.*?)-Fin')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('EliFilms', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('EliFilms', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EliFilms', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EliFilms', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EliFilms', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EliFilms', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('EliFilms', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        id = scrapertools.find_single_match(str(match), "'_id':(.*?),").strip()
        title = scrapertools.find_single_match(str(match), "'title':.*?'(.*?)'")

        if not id or not title: continue

        season = scrapertools.find_single_match(str(match), "'season_number':(.*?),").strip()

        epis = scrapertools.find_single_match(str(match), "'episode_number':(.*?)$").strip()

        if not season == str(item.contentSeason): continue

        thumb = scrapertools.find_single_match(str(match), "'still_path':.*?'(.*?)'")

        thumb = host[:-1] + thumb.replace('\\/', '/')

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

        titulo = "%sx%s %s" % (str(season), str(epis), title)

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        url = api + 'player?post_id=' + id + '&_any=1'

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber=epis ))

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

    lang = 'Lat'

    ses = 0

    # ~ Embeds
    bloque = scrapertools.find_single_match(data, '"embeds"(.*?)"downloads"')

    matches = scrapertools.find_multiple_matches(bloque, '"url":.*?"(.*?)"')

    for link in matches:
        ses += 1

        other = ''

        link = link.replace('\\/', '/')

        if 'sbcom' in link: continue
        elif 'lvturbo' in link: continue
        elif 'vanfem' in link: continue
        elif 'fembed' in link: continue
        elif 'fcom' in link: continue

        servidor = servertools.get_server_from_url(link)
        servidor = servertools.corregir_servidor(servidor)

        if '/vimeos.' in link:
            servidor = 'zures'
            other = 'Vimeos'

        if servidor == 'various': other = servertools.corregir_other(link)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = link, language = lang, other = other ))

    # ~ Descargas
    bloque = scrapertools.find_single_match(data, '"downloads"(.*?)$')

    matches = scrapertools.find_multiple_matches(bloque, '"url":.*?"(.*?)"')

    for link in matches:
        ses += 1

        other = ''

        link = link.replace('\\/', '/')

        if '1fichier' in link: continue
        elif 'fireload' in link: continue

        elif 'sbcom' in link: continue
        elif 'lvturbo' in link: continue
        elif 'vanfem' in link: continue
        elif 'fembed' in link: continue
        elif 'fcom' in link: continue

        elif '/vimeos.' in link: continue

        servidor = servertools.get_server_from_url(link)
        servidor = servertools.corregir_servidor(servidor)

        if '/vimeos.' in link:
            servidor = 'zures'
            other = 'Vimeos'

        if servidor == 'various': other = servertools.corregir_other(link)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = link, language = lang, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    servidor = item.server

    url = item.url

    if 'jodwish' in url or 'swhoi' in url or 'swdyu' in url or 'strwish' in url or 'playerwish' in url or 'streamwish' in url or 'wish' in url:
        url = url + '|Referer=' + url

    itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        if item.search_type == 'all':
            item.url = api + 'search?post_type=movies,tvshows,animes&query=' + texto.replace(" ", "+") + '&posts_per_page=25'
            item._next = '&post_type=movies,tvshows,animes&posts_per_page=25'
        else:
            if item.search_type == 'movie':
                item.url = api + 'search?post_type=movies&query=' + texto.replace(" ", "+") + '&posts_per_page=25'
                item._next = '&post_type=movies&posts_per_page=25'
            else:
                if item.group == 'animes':
                    item.url = api + 'search?post_type=animes&query=' + texto.replace(" ", "+") + '&posts_per_page=25'
                    item._next = '&post_type=animes&posts_per_page=25'
                else:
                    item.url = api + 'search?post_type=tvshows&query=' + texto.replace(" ", "+") + '&posts_per_page=25'
                    item._next = '&post_type=tvshows&posts_per_page=25'

        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

