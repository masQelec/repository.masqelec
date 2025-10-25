# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


from lib.pyberishaes import GibberishAES
from lib import decrypters


host = 'https://verpelishd.me/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://www.pelisgratishd.life/', 'https://www.pelisgratishd.xyz/', 'https://ver.pelisgratishd.life/',
             'https://app.pelisgratishd.life/', 'https://neo.pelisgratishd.life/', 'https://ver.cuevanahd.lat/',
             'https://verpelishd.net/', 'https://www.verpelishd.net/']

domain = config.get_setting('dominio', 'pgratishd', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'pgratishd')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'pgratishd')
    else: host = domain


perpage = 35


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_pgratishd_proxies', default=''):
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

    if '/year/' in url: raise_weberror = False

    hay_proxies = False
    if config.get_setting('channel_pgratishd_proxies', default=''): hay_proxies = True

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('pgratishd', url, post=post, headers=headers, raise_weberror=raise_weberror).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

        if not data:
            if not '/search/' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('PGratisHd', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('pgratishd', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    if '<title>Just a moment...</title>' in data:
        if not '/search/' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'pgratishd', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_pgratishd', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='pgratishd', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_pgratishd', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_pgratishd', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('pgratishd') ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'pgratishd', thumbnail=config.get_thumb('pgratishd') ))

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'category/peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'category/series/', search_type = 'tvshow' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title = 'Animes', action = 'mainlist_animes', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Bíblicas', action = 'list_all', url = host + 'category/series-biblicas/', search_type = 'tvshow', text_color = 'moccasin' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'category/anime/', search_type = 'all' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    opciones = {
        'accion': 'Acción',
        'animacion': 'Animación',
        'aventura': 'Aventura',
        'ciencia-ficcion': 'Ciencia ficción',
        'comedia': 'Comedia',
        'crimen': 'Crimen',
        'documental': 'Documental',
        'drama': 'Drama',
        'familia': 'Familia',
        'fantasia': 'Fantasía',
        'historia': 'Historia',
        'misterio': 'Misterio',
        'musica': 'Música',
        'pelicula-de-tv': 'Película Tv',
        'romance': 'Romance',
        'suspense': 'Suspense',
        'terror': 'Terror',
        'war': 'War',
        'western': 'Western'
        }

    for opc in opciones:
        url = host + 'genres/' + opc + '/'

        itemlist.append(item.clone( title = opciones[opc], url = url, action ='list_all', text_color = text_color ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1989, -1):
        url = host + 'year/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color='deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        title = scrapertools.find_single_match(match, 'alt="(.*?)"').strip()

        url = scrapertools.find_single_match(match, '<a href="([^"]+)"')

        if not title or not url: continue

        if not 'http' in url: continue

        thumb = scrapertools.find_single_match(match, 'data-src="([^"]+)"')

        year = scrapertools.find_single_match(match, '<div class="list-year">(.*?)</div>')

        if '/year/' in item.url:
            year = scrapertools.find_single_match(item.url, "/year/(.*?)/")

        if not year: year = '-'

        title = title.replace('&#8211;', '').replace('&#039;', "'").replace('&#8230;', ' &').replace('&amp;', '&').replace('&#8217;s', "'").strip()
        title = title.replace('PelisplusHD', '').replace('Pelisplus', '').replace('Cuevana', '').replace(' Online', '').strip()

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

            itemlist.append(item.clone( action ='temporadas', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if 'aria-label="pagination">' in data:
            next_page = scrapertools.find_single_match(data, 'aria-label="pagination">.*?class="page-numbers current">.*?href="(.*?)"')

            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '>Lista de temporadas<(.*?)</div>')

    matches = scrapertools.find_multiple_matches(bloque, 'data-season="(.*?)"')

    if not matches:
        if '>Lista de episodios<' in data:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan] Una Temporada[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = 1
            itemlist = episodios(item)

        return itemlist

    for nro_season in matches:
        title = 'Temporada ' + nro_season

        if len(matches) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = nro_season
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = nro_season, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    d_id = scrapertools.find_single_match(data, 'data-tmdb-id="(.*?)"')

    d_nonce = scrapertools.find_single_match(data, 'data-nonce="(.*?)"')

    if not d_id or not d_nonce: return itemlist

    headers = {'Referer': item.url}

    data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = {'action': 'corvus_get_episodes', 'post_id': d_id, 'nonce': d_nonce, 'season': item.contentSeason}, headers = headers )

    matches = scrapertools.find_multiple_matches(str(data), '"permalink":"(.*?)".*?"name":"(.*?)".*?"episode_number":(.*?),')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('PGratisHd', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('PGratisHd', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PGratisHd', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PGratisHd', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PGratisHd', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PGratisHd', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('PGratisHd', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, title, epis in matches[item.page * item.perpage:]:
        if not url: continue

        if not epis: epis = 1

        title = clean_title(title)

        if not title: title = item.contentSerieName

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        if 'episodie' in titulo.lower() or 'episodio' in titulo.lower() or 'capítulo' in titulo.lower() or 'capitulo' in titulo.lower():
            titulo = titulo + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        titulo = titulo.replace('Episode', '[COLOR goldenrod]Epis.[/COLOR]').replace('episode', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')
        titulo = titulo.replace('Capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capítulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')

        url = url.replace('\\/', '/')

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

    d_id = scrapertools.find_single_match(data, 'data-id="(.*?)"')

    if not d_id:
        d_id = scrapertools.find_single_match(data, 'data-tmdb-id="(.*?)"')

    d_nonce = scrapertools.find_single_match(data, 'data-nonce="(.*?)"')

    if not d_id or not d_nonce: return itemlist

    headers = {'Referer': item.url}

    data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = {'action': 'corvus_get_servers', 'post_id': d_id, 'nonce': d_nonce}, headers = headers )

    new_url = scrapertools.find_single_match(data, '"url":"(.*?)"')

    if not new_url: return itemlist

    if not 'http' in new_url: return itemlist

    new_url = new_url.replace('\\/', '/')

    data = do_downloadpage(new_url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    ses = 0

    if '/streamsito.' in new_url: ses += 1 

    if '//plustream.' in new_url or '.playflv.' in new_url:
        ses += 1

        datae = data

        dataLink = scrapertools.find_single_match(datae, 'const dataLink =(.*?);')
        if not dataLink: dataLink = scrapertools.find_single_match(datae, 'dataLink(.*?);')

        e_bytes = scrapertools.find_single_match(datae, "const bytes =.*?'(.*?)'")
        if not e_bytes: e_bytes = scrapertools.find_single_match(datae, "encrypted,.*?'(.*?)'")
        if not e_bytes: e_bytes = scrapertools.find_single_match(datae, "const safeServer =.*?'(.*?)'")

        e_links = dataLink.replace(']},', '"type":"file"').replace(']}]', '"type":"file"')

        age = ''
        if not dataLink or not e_bytes or '\\u003c' in e_bytes: age = 'crypto'

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
                elif 'embedsito' in srv: continue
                elif 'disable2' in srv: continue
                elif 'disable' in srv: continue
                elif 'xupalace' in srv: continue
                elif 'uploadfox' in srv: continue
                elif 'streamsito' in srv: continue

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

    # ~ Otros
    options = scrapertools.find_multiple_matches(data, '<li onclick="go_to_playerVast(.*?)</li>')

    for option in options:
        ses += 1

        if 'data-lang="2"' in option: lang = 'Vose'
        elif 'data-lang="0"' in option: lang = 'Lat'
        elif 'data-lang="1"' in option: lang = 'Esp'
        else: lang = '?'

        url = scrapertools.find_single_match(str(option), "'(.*?)'")

        if '/embedsito.' in url:
           data1 = do_downloadpage(url)
           data1 = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

           url = scrapertools.find_single_match(data1, '<a href="(.*?)"')

        if not url: continue
        elif url == '#': continue

        elif 'fembed' in url: continue
        elif 'streamsb' in url: continue
        elif 'playersb' in url: continue
        elif 'sbembed' in url: continue

        elif 'player-cdn' in url: continue
        elif 'streamsito' in url: continue

        elif '/1fichier.' in url: continue
        elif '/short.' in url: continue
        elif '/disable2.' in url: continue
        elif '/disable.' in url: continue
        elif '/embedsito.' in url: continue
        elif '/xupalace.' in url: continue

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servertools.is_server_available(servidor):
            if not servertools.is_server_enabled(servidor): continue
        else:
            if not config.get_setting('developer_mode', default=False): continue

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)

        if servidor == 'directo':
            if not config.get_setting('developer_mode', default=False): continue
            else:
                other = url.split("/")[2]
                other = other.replace('https:', '').strip()

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = lang, other = other ))

    # ~ Downloads error link

    if not itemlist:
        matches = scrapertools.find_multiple_matches(data, '<iframe src="(.*?)"')
        if not matches: matches = scrapertools.find_multiple_matches(data, '<IFRAME SRC="(.*?)"')

        for url in matches:
            if '/1fichier.' in url: continue
            elif '/short.' in url: continue
            elif '/disable2.' in url: continue
            elif '/disable.' in url: continue
            elif '/embedsito.' in url: continue
            elif '/xupalace.' in url: continue
            elif 'streamsito' in url: continue

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

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = '?', other = other ))

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
    try:
        item.url = host + 'search/' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

