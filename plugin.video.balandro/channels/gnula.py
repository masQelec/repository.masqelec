# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://ww3.gnulahd.nu/'


# ~ por si viene de enlaces guardados
ant_hosts = ['http://gnula.nu/', 'https://gnula.nu/', 'https://gnulahd.nu/']

domain = config.get_setting('dominio', 'gnula', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'gnula')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'gnula')
    else: host = domain


_player = '.gnulahd.'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_gnula_proxies', default=''):
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


def do_downloadpage(url, post=None):
    # ~ por si viene de enlaces guardados
    for ant in ant_hosts:
        url = url.replace(ant, host)

    url = url.replace('http://', 'https://')

    hay_proxies = False
    if config.get_setting('channel_gnula_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url or _player in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host) and not _player in url:
        data = httptools.downloadpage(url, post=post, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('gnula', url, post=post, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, timeout=timeout).data

        if data:
            if not host in data and not _player in data:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('Gnula', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('gnula', url, post=post, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, timeout=timeout).data

            if not host in data and not _player in data: data = ''

    if '<title>You are being redirected...</title>' in data or '<title>Just a moment...</title>' in data or '<title>Just a moment please...</title>' in data:
        if not url.startswith(host) and not _player in url:
            data = httptools.downloadpage(url, post=post, timeout=timeout).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('gnula', url, post=post, timeout=timeout).data
            else:
                data = httptools.downloadpage(url, post=post, timeout=timeout).data

    if '<title>Just a moment...</title>' in data or '<title>Just a moment please...</title>' in data:
        platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Gnula [COLOR red]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'gnula', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_gnula', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='gnula', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_gnula', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_gnula', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('gnula') ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'gnula', thumbnail=config.get_thumb('gnula') ))

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'ver/?status=&type=Pelicula', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Últimas', action = 'list_all', url = host + 'ver/?status=&type=Pelicula&order=latest', search_type = 'movie', text_color='cyan' ))

    itemlist.append(item.clone( title = 'Actualizadas', action = 'list_all', url = host + 'ver/?type=Pelicula&order=update', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'ver/?status=&type=Pelicula&order=popular', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'ver/?type=Pelicula&order=rating', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por tema', action = 'temas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por estudio', action = 'estudios', search_type = 'movie', text_color='moccasin' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'ver/?status=&type=Serie', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimas', action = 'list_all', url = host + '/ver/?status=&type=Serie&order=latest', search_type = 'tvshow', text_color='cyan' ))

    itemlist.append(item.clone( title = 'Actualizadas', action = 'list_all', url = host + 'ver/?type=Serie&order=update', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'ver/?status=Ongoing&type=Serie', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Finalizadas', action = 'list_all', url = host + 'ver/?status=Completed&type=Serie&order=', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'ver/?status=&type=Serie&order=popular', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_all', url = host + 'ver/?type=Serie&order=rating', search_type = 'tvshow' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'ver/?status=&type=Anime', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos', action = 'list_all', url = host + '/ver/?status=&type=Anime&order=latest', search_type = 'tvshow', text_color='cyan' ))

    itemlist.append(item.clone( title = 'Actualizados', action = 'list_all', url = host + 'ver/?type=Anime&order=update', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'ver/?status=Ongoing&type=Anime', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'ver/?status=Completed&type=Anime&order=', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'ver/?status=&type=Anime&order=popular', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'ver/?type=Anime&order=rating', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'generos/')

    bloque = scrapertools.find_single_match(data, '<h1><span>Generos<(.*?)</ul>')

    matches = re.compile('<a href="(.*?)".*?<span class="name">(.*?)</span>', re.DOTALL).findall(bloque)

    for url, title in matches:
        itemlist.append(item.clone( title=title, url=url, action='list_all', text_color = 'deepskyblue' ))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    for letra in '#0ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if letra == '#': letter = '.'
        elif letra == '0': letter = '0-9'
        else: letter = letra.upper()

        url = host + 'az-lists/?show=' + letter

        itemlist.append(item.clone ( title = letra, url = url, action = 'list_all', text_color = 'deepskyblue' ))

    return itemlist


def temas(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    data = do_downloadpage(host + 'generos/')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Etiquetas<(.*?)</div></div>')

    matches = re.compile('<a href="(.*?)".*?aria-label=".*?">(.*?)</a>', re.DOTALL).findall(bloque)

    for url, title in matches:
        title = title.capitalize()

        title = title.replace('relationship', '').strip()

        itemlist.append(item.clone( title=title, url=url, action='list_all', text_color = text_color ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'ver/')

    bloque = scrapertools.find_single_match(data, '> Pais <(.*?)</ul>')

    matches = re.compile('value="(.*?)".*?">(.*?)</label>', re.DOTALL).findall(bloque)

    for value, title in matches:
        url = host + 'ver/?country[]=' + value

        itemlist.append(item.clone( title=title, url=url, action='list_all', text_color = 'deepskyblue' ))

    return itemlist


def estudios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'ver/')

    bloque = scrapertools.find_single_match(data, '> Network <(.*?)</ul>')

    matches = re.compile('value="(.*?)".*?">(.*?)</label>', re.DOTALL).findall(bloque)

    for value, title in matches:
        url = host + 'ver/?studio[]=' + value

        itemlist.append(item.clone( title=title, url=url, action='list_all', text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    patron  = '<article class="bs".*?<a href="(.*?)".*?title="(.*?)".*?<div class="typez(.*?)</div>.*?src="(.*?)".*?</article>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title, type, thumb in matches:
        title = title.replace('&#8217;', "'").replace('&#038;', "&").replace('&#8230;', '')

        tipo = 'movie' if '>Pelicula' in type else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo = sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            itemlist.append(item.clone( action = 'temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo = sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '>Siguiente' in data:
            if '<div class="hpage">' in data:
                blk_next = scrapertools.find_single_match(data, '<div class="hpage">(.*?)</div>')

                if 'Atras<' in blk_next:
                    next_page = scrapertools.find_single_match(blk_next, 'Atras<.*?href="(.*?)"')
                else:
                    next_page = scrapertools.find_single_match(blk_next, 'href="(.*?)"')

                if next_page:
                    if '?page=' in next_page:
                        next_page = host + 'ver/' + next_page

                        itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

            elif '<div class="pagination">' in data:
                next_page = scrapertools.find_single_match(data, '<div class="pagination">.*?class="page-numbers current">.*?href="(.*?)"')

                if next_page:
                    if '/page/' in next_page:
                        itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))


    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    if config.get_setting('channels_seasons', default=True):
        platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '[COLOR tan]sin Temporadas[/COLOR]')

    item.page = 0
    item.contentType = 'season'
    item.contentSeason = 0
    itemlist = episodios(item)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<li data-index=".*?<a href="(.*?)".*?<div class="epl-num">(.*?)</div>.*?<div class="epl-title">(.*?)</div>', re.DOTALL).findall(data)

    num_matches = len(matches)

    if item.page == 0 and item.perpage == 50:
        sum_parts = num_matches

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('Gnula', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('Gnula', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Gnula', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Gnula', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Gnula', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Gnula', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('Gnula', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, temp_epis, title in matches:
        temp = scrapertools.find_single_match(temp_epis, "(.*?)x")
        if not temp: temp = 1

        epis = scrapertools.find_single_match(temp_epis, "x(.*?)$")
        if not epis: epis = 1

        titulo = str(temp) + 'x' + str(epis) + ' ' + title.replace(temp_epis, '').strip()

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason=temp, contentEpisodeNumber=epis ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'VC': 'Esp', 'VL': 'Lat', 'VS': 'Vose', 'castellano': 'Esp', 'latino': 'Lat', 'vose': 'Vose'}

    lang = '?'

    data = do_downloadpage(item.url)

    ses = 0

    if item.contentSeason:
        url = scrapertools.find_single_match(data, '<div class="player-embed".*?<iframe.*?src="(.*?)".*?</iframe>')

        if not '/embed.php?id=' in url: return itemlist

        ses += 1

        data2 = do_downloadpage(url)

        bloque2 = scrapertools.find_single_match(data2, '<script>.*?var videos.*?=(.*?)</script>')

        matches2 = re.compile('", "(.*?)"', re.DOTALL).findall(str(bloque2))

        for match2 in matches2:
            data3 = do_downloadpage(match2)

            link = scrapertools.find_single_match(data3, "var url = '(.*?)'")

            if link:
                servidor = servertools.get_server_from_url(link)
                servidor = servertools.corregir_servidor(servidor)

                if servertools.is_server_available(servidor):
                    if not servertools.is_server_enabled(servidor): continue
                else:
                    if not config.get_setting('developer_mode', default=False): continue

                other = servidor

                if servidor == 'various': other = servertools.corregir_other(link)

                if servidor == other: other = ''

                itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = link, server = servidor, language = lang, other = other ))


        bloque3 = scrapertools.find_single_match(data2, '<tbody>(.*?)</tbody>')

        matches3 = re.compile('<tr>(.*?)</tr>', re.DOTALL).findall(bloque3)

        for match3 in matches3:
             url = scrapertools.find_single_match(match3, 'href="(.*?)"')

             if url:
                 if '/powvideo.' in url: continue
                 elif '/streamplay' in url: continue
                 elif '/streamango.' in url: continue
                 elif '/streamcloud.' in url: continue
                 elif '/openload.'in url: continue
                 elif '/rapidvideo.' in url: continue
                 elif '/jetload.' in url: continue
                 elif '/uploaded' in url: continue
                 elif '/byter' in url: continue
                 elif '/uploadmp4' in url: continue
                 elif '/xdrive' in url: continue

                 elif '/1fichier.' in url: continue
                 elif '/ul.' in url: continue
                 elif '/multiup.' in url: continue
                 elif '/filemirage.' in url: continue
                 elif '/filepv.' in url: continue
                 elif '.rapidvideo.' in url: continue

                 servidor = servertools.get_server_from_url(url)
                 servidor = servertools.corregir_servidor(servidor)

                 if servertools.is_server_available(servidor):
                     if not servertools.is_server_enabled(servidor): continue
                 else:
                    if not config.get_setting('developer_mode', default=False): continue

                 other = servidor

                 if servidor == 'various': other = servertools.corregir_other(url)

                 if servidor == other: other = ''

                 if 'latino' in match3: lng = 'Lat'
                 elif 'castellano' in match3: lng = 'Esp'
                 elif 'subtitulado' in match3: lng = 'Vose'
                 else: lng = '?'

                 itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor,
                                       language = lng, other = other ))

    else:

        matches = re.compile('<li data-index="(.*?)".*?<a href="(.*?)"', re.DOTALL).findall(data)

        for opcion, url in matches:
            ses += 1

            data1 = do_downloadpage(url)

            url = scrapertools.find_single_match(data1, '<div class="player-embed".*?<iframe.*?src="(.*?)".*?</iframe>')

            if url:
                if '/powvideo.' in url: continue
                elif '/streamplay' in url: continue
                elif '/streamango.' in url: continue
                elif '/streamcloud.' in url: continue
                elif '/openload.'in url: continue
                elif '/rapidvideo.' in url: continue
                elif '/jetload.' in url: continue
                elif '/uploaded' in url: continue
                elif '/byter' in url: continue
                elif '/uploadmp4' in url: continue
                elif '/xdrive' in url: continue

                elif '/1fichier.' in url: continue
                elif '/ul.' in url: continue
                elif '/multiup.' in url: continue
                elif '/filemirage.' in url: continue
                elif '/filepv.' in url: continue
                elif '.rapidvideo.' in url: continue

                if not '/embed.php?id=' in url:
                    servidor = servertools.get_server_from_url(url)
                    servidor = servertools.corregir_servidor(servidor)

                    if servertools.is_server_available(servidor):
                        if not servertools.is_server_enabled(servidor): continue
                    else:
                        if not config.get_setting('developer_mode', default=False): continue

                    itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = lang))

                    continue


                data2 = do_downloadpage(url)

                bloque2 = scrapertools.find_single_match(data2, '<script>.*?var videos =(.*?)</script>')

                matches2 = re.compile('", "(.*?)"', re.DOTALL).findall(str(bloque2))

                for match2 in matches2:
                    data3 = do_downloadpage(match2)

                    link = scrapertools.find_single_match(data3, "var url = '(.*?)'")

                    if link:
                       servidor = servertools.get_server_from_url(link)
                       servidor = servertools.corregir_servidor(servidor)

                       if servertools.is_server_available(servidor):
                           if not servertools.is_server_enabled(servidor): continue
                       else:
                           if not config.get_setting('developer_mode', default=False): continue

                       other = servidor

                       if servidor == 'various': other = servertools.corregir_other(link)

                       if servidor == other: other = ''

                       itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = link, server = servidor,
                                             language = lang, other = other ))


                bloque3 = scrapertools.find_single_match(data2, '<tbody>(.*?)</tbody>')

                matches3 = re.compile('<tr>(.*?)</tr>', re.DOTALL).findall(bloque3)

                for match3 in matches3:
                    url = scrapertools.find_single_match(match3, 'href="(.*?)"')

                    if url:
                        if '/powvideo.' in url: continue
                        elif '/streamplay' in url: continue
                        elif '/streamango.' in url: continue
                        elif '/streamcloud.' in url: continue
                        elif '/openload.'in url: continue
                        elif '/rapidvideo.' in url: continue
                        elif '/jetload.' in url: continue
                        elif '/uploaded' in url: continue
                        elif '/byter' in url: continue
                        elif '/uploadmp4' in url: continue
                        elif '/xdrive' in url: continue

                        elif '/1fichier.' in url: continue
                        elif '/ul.' in url: continue
                        elif '/multiup.' in url: continue
                        elif '/filemirage.' in url: continue
                        elif '/filepv.' in url: continue
                        elif '.rapidvideo.' in url: continue

                        servidor = servertools.get_server_from_url(url)
                        servidor = servertools.corregir_servidor(servidor)

                        if servertools.is_server_available(servidor):
                            if not servertools.is_server_enabled(servidor): continue
                        else:
                            if not config.get_setting('developer_mode', default=False): continue

                        other = servidor

                        if servidor == 'various': other = servertools.corregir_other(url)

                        if servidor == other: other = ''

                        if 'latino' in match3: lng = 'Lat'
                        elif 'castellano' in match3: lng = 'Esp'
                        elif 'subtitulado' in match3: lng = 'Vose'
                        else: lng = '?'

                        itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor,
                                              language = lng, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if '/powvideo' in url or '/streamplay' in url:
        return 'Servidor [COLOR goldenrod]No Admitido[/COLOR]'

    elif '/1fichier' in url or '/ul' in url or '/multiup' in url or '/filemirage' in url or '/filepv' in url:
        return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

    elif '/uptobox' in url:
         return 'Servidor [COLOR goldenrod]Fuera de Servicio[/COLOR]'

    elif '/jetload' in url or '/streamango' in url or '/streamcloud' in url or '/openload' in url or '/rapidvideo' in url or '/byter' in url or '/uploaded' in url or '/uploadmp4' in url or '/xdrive' in url:
        return 'Servidor [COLOR goldenrod]Obsoleto[/COLOR]'

    url = url.replace('http://', 'https://')

    if '/soon' in url: url = ''
    elif '/bembed.' in url: url = ''

    if url:
        servidor = item.server

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(server = servidor, url = url))

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
