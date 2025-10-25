# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


from lib.pyberishaes import GibberishAES
from lib import decrypters


host = 'https://entrepeliculasyseries.nz/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://entrepeliculasyseries.com/', 'https://entrepeliculasyseries.io/', 'https://entrepeliculasyseries.nu/']


domain = config.get_setting('dominio', 'entrepeliculasyseries', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'entrepeliculasyseries')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'entrepeliculasyseries')
    else: host = domain


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_entrepeliculasyseries_proxies', default=''):
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
    if config.get_setting('channel_entrepeliculasyseries_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('entrepeliculasyseries', url, post=post, headers=headers, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if not data:
            if not 'search?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('EntrePeliculasySeries', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('entrepeliculasyseries', url, post=post, headers=headers, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    if '<title>You are being redirected...</title>' in data or '<title>Just a moment...</title>' in data:
        if not url.startswith(host):
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('entrepeliculasyseries', url, post=post, headers=headers, timeout=timeout).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    if '<title>Just a moment...</title>' in data:
        if not 'search?s=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'entrepeliculasyseries', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_entrepeliculasyseries', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='entrepeliculasyseries', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_entrepeliculasyseries', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(item.clone( channel='helper', action='show_help_prales', title='[B]Cuales son sus Clones[/B]', text_color='turquoise' ))

    itemlist.append(Item( channel='helper', action='show_help_entrepeliculasyseries', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('entrepeliculasyseries') ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'entrepeliculasyseries', thumbnail=config.get_thumb('entrepeliculasyseries') ))

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

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'peliculas/populares/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'series/populares/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'animes/', group = 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_all', url = host + 'animes/populares/', group = 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', group = 'animes', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       text_color = 'hotpink'
       if item.group == 'animes': text_color = 'springgreen'

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>Géneros<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)">(.*?)</a>')

    for url, title in matches:
        if not config.get_setting('mnu_doramas', default=False):
            if title == 'Dorama': continue

        title = title.replace('&amp;', '&')

        url = host[:-1] + url

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')
        if not title: title = scrapertools.find_single_match(match, '<h2 class="title">(.*?)</h2>').strip()

        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        if not title or not url: continue

        thumb = scrapertools.find_single_match(match, 'src="([^"]+)"')

        year = scrapertools.find_single_match(match, '<span class="inf">(.*?)</span>').strip()

        if year: title = title.replace('(' + year + ')', '').strip()
        else:
            year = scrapertools.find_single_match(title, '(\d{4})')
            if year: title = title.replace('(' + year + ')', '').strip()

        if not year: year = '-'

        c_year = scrapertools.find_single_match(title, '(\d{4})')
        if not c_year: c_year = scrapertools.find_single_match(title, '(d{4})')

        if c_year:
            title = title.replace('(' + c_year + ')', '').strip()
            title = title.replace(' ' + c_year + ' ', '').strip()

        if '/release/' in item.url: year = scrapertools.find_single_match(item.url, "/release/(.*?)/")

        title = title.replace('&#39;s', "'s").replace('&#039;s', "'s").replace('&#8211;', '').replace('&#039;', "'").replace('&#8230;', ' &').replace('&amp;', '&').replace('&#8217;s', "'").strip()

        if url.startswith("/"): url = host[:-1] + url

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == 'all':
               if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))

        if tipo == 'tvshow':
            if not item.search_type == 'all':
                if item.search_type == 'movie': continue

            if item.group == 'animes':
                if not '/anime/' in url: continue

            itemlist.append(item.clone( action ='temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<nav class="nav-links">' in data:
            next_page = scrapertools.find_single_match(data, '<nav class="nav-links">.*?class="page-numbers current">.*?href="(.*?)"')

            if '?page=' in next_page:
                ant_page = item.url

                if '?page=' in ant_page: ant_page = ant_page.split("?page=")[0]

                if next_page.startswith("?"): next_page = ant_page + next_page

                itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, 'id="season-tab-(.*?)".*?Temporada(.*?)</button>')

    for id_season, nro_season in matches:
        nro_season = nro_season.strip()

        title = 'Temporada ' + nro_season

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.id_season = id_season
            item.contentSeason = nro_season
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, id_season = id_season,
                                    contentType = 'season', contentSeason = nro_season, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return sorted(itemlist, key=lambda it: it.contentSeason)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    season = scrapertools.find_single_match(data, 'id="season-' + item.id_season + '"(.*?)</div></div>')

    matches = scrapertools.find_multiple_matches(season, '<div class="episode-card">(.*?)</a>')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('EntrePeliculasySeries', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('EntrePeliculasySeries', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EntrePeliculasySeries', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EntrePeliculasySeries', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EntrePeliculasySeries', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('EntrePeliculasySeries', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('EntrePeliculasySeries', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for match in matches[item.page * item.perpage:]:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        if url.startswith("/"): url = host[:-1] + url

        title = item.contentSerieName.replace('&#038;', '&')

        epis = scrapertools.find_single_match(match, '<div>(.*?)</div>')

        epis = epis.replace('Episodio', '').replace('episodio', '').strip()

        if not epis: epis = 1

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        if 'Epis.' in titulo: titulo = titulo + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

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
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    embeds = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)".*?</iframe>')

    if not 'http' in embeds: embeds = ''

    if not embeds: embeds = scrapertools.find_single_match(data, 'data-src="(.*?)"')

    if not embeds: return itemlist

    embeds = embeds.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

    data = do_downloadpage(embeds)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    ses = 0

    if '/waaw.' in embeds:
        ses += 1

        lang = '?'

        url = embeds

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = lang, other = other ))

    elif '//embed69.' in embeds:
        ses += 1

        datae = data

        dataLink = scrapertools.find_single_match(datae, 'const dataLink =(.*?);')
        if not dataLink: dataLink = dataLink = scrapertools.find_single_match(datae, 'let dataLink =(.*?);')
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

                if '.eyJs' in link: age = ''

                itemlist.append(Item( channel = item.channel, action = 'play', server=servidor, title = '', crypto=link, bytes=e_bytes, age=age,
                                      language=lang, other=other ))

            continue

    # ~ Otros
    matches = scrapertools.find_multiple_matches(data, 'onclick="go_to_player.*?' + "'(.*?)'")
    if not matches: matches = scrapertools.find_multiple_matches(data, 'onclick="go_to_player.*?' + "'(.*?)'")

    langs = []
    if 'data-lang="1"' in data: langs.append('Esp')
    if 'data-lang="0"' in data: langs.append('Lat')
    if 'data-lang="2"' in data: langs = langs.append('Vose')

    if ',' in str(langs): lang = ",".join(langs)
    else: lang = str(langs).replace('[', '').replace("'", '').replace(']', '').strip()

    if not langs: lang = '?'

    for url in matches:
        ses += 1

        if not url: continue
        elif url == '#': continue

        elif '/1fichier.' in url: continue
        elif '/short.' in url: continue
        elif '/plustream.' in url: continue
        elif '/player-cdn.' in url: continue

        elif 'embedsito' in url: continue
        elif 'disable2' in url: continue
        elif 'disable' in url: continue
        elif 'xupalace' in url: continue
        elif 'uploadfox' in url: continue

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)

        if servidor == 'directo':
            if config.get_setting('developer_mode', default=False):
                other = url.split("/")[2]
                other = other.replace('https:', '').strip()

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = lang, other = other ))

    # ~ iframes data-src
    matches = scrapertools.find_multiple_matches(data, '<iframe.*?data-src="(.*?)"')

    for match in matches:
        lang = '?'

        if '/xupalace.' in match:
            ses += 1

            if 'php?id=' in match:
                datax = do_downloadpage(match)

                url = scrapertools.find_single_match(datax, '<iframe src="(.*?)"')

                if url:
                    servidor = servertools.get_server_from_url(url)
                    servidor = servertools.corregir_servidor(servidor)

                    if servertools.is_server_available(servidor):
                        if not servertools.is_server_enabled(servidor): continue
                    else:
                        if not config.get_setting('developer_mode', default=False): continue

                    url = servertools.normalize_url(servidor, url)

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url=url, language=lang ))

                continue

            elif '/video/' in match:
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

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url=url, language=lang, other=other ))

                continue

            else: continue

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

        url = ''

        if not bytes:
            url = scrapertools.find_single_match(item.crypto, '\.(eyJs.*?)\.')
            url += '='
            url = base64.b64decode(url).decode()
            url = scrapertools.find_single_match(url, '"link":"(.*?)"')

        if not url:
            try:
                url = GibberishAES.dec(GibberishAES(), string = crypto, pass_ = bytes)
            except:
                url = ''

            if not url:
                url = decrypters.decode_decipher(crypto, bytes)

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
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'search?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

