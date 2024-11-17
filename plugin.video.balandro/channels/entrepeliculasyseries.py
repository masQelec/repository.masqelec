# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

try:
    from Cryptodome.Cipher import AES
    from lib import jscrypto
except:
    pass


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

    raise_weberror = True
    if '/release/' in url: raise_weberror = False

    hay_proxies = False
    if config.get_setting('channel_entrepeliculasyseries_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('entrepeliculasyseries', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

        if not data:
            if not '?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('EntrePeliculasySeries', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('entrepeliculasyseries', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    if '<title>You are being redirected...</title>' in data or '<title>Just a moment...</title>' in data:
        if not url.startswith(host):
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('entrepeliculasyseries', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    if '<title>Just a moment...</title>' in data:
        if not '?s=' in url:
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

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'movies/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Doramas', action = 'list_all', url = host + 'genero/dorama/', search_type = 'tvshow', text_color = 'firebrick' ))

    itemlist.append(item.clone( title = 'Animes', action = 'list_all', url = host + 'genero/animacion/', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else: text_color = 'hotpink'

    data = do_downloadpage(host)

    matches = scrapertools.find_multiple_matches(data, '<li class="cat-item cat-.*?<a href="([^"]+)">(.*?)</a>')

    for url, title in matches:
        if item.search_type == 'movie':
           if '/series-' in url: continue
        else:
           if '/peliculas-' in url: continue
           elif '/documentales' in url: continue

           if title == 'Series Documentales': title = 'Documentales'

        if config.get_setting('descartar_anime', default=False):
            if title == 'Anime': continue

        if not config.get_setting('mnu_doramas', default=False):
            if title == 'Dorama': continue

        title = title.replace('&amp;', '&')

        itemlist.append(item.clone( action = 'list_all', title = title, url = url, text_color = text_color ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1928, -1):
        url = host + 'release/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color = 'deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for match in matches:
        title = scrapertools.find_single_match(match, 'alt="(.*?)"')
        if not title: title = scrapertools.find_single_match(match, '<h2>(.*?)</h2>').strip()

        url = scrapertools.find_single_match(match, 'href="([^"]+)"')

        if not title or not url: continue

        thumb = scrapertools.find_single_match(match, 'src="([^"]+)"')

        year = scrapertools.find_single_match(match, '<span class="inf">(.*?)</span>').strip()
        if year: title = title.replace('(' + year + ')', '').strip()
        else:
            year = scrapertools.find_single_match(title, '(\d{4})')
            if year: title = title.replace('(' + year + ')', '').strip()

        if not year: year = '-'

        if '/release/' in item.url: year = scrapertools.find_single_match(item.url, "/release/(.*?)/")

        title = title.replace('&#8211;', '').replace('&#039;', "'").replace('&#8230;', ' &').replace('&amp;', '&').replace('&#8217;s', "'").strip()

        tipo = 'movie' if '/movies/' in url else 'tvshow'
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
        if '<span aria-current="page" class="page-numbers current">' in data:
            next_page = scrapertools.find_single_match(data, '<span aria-current="page" class="page-numbers current">.*?href="(.*?)"')

            if '/page/' in next_page:
                itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '>Temporada <span>(.*?)</span>')

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

    return sorted(itemlist, key=lambda it: it.contentSeason)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    season = scrapertools.find_single_match(data, 'data-season>.*?>Temporada <span>' + str(item.contentSeason) + '</span>(.*?)</aside>')

    matches = scrapertools.find_multiple_matches(season, '<a href="(.*?)".*?<span>(.*?)</span>')

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

    for url, epis in matches[item.page * item.perpage:]:
        title = item.contentSerieName.replace('&#038;', '&')

        nro_epi = scrapertools.find_single_match(epis, 'Ep.(.*?)$').strip()

        titulo = str(item.contentSeason) + 'x' + nro_epi + ' ' + title

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = nro_epi ))

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

    vids = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')

    if not vids: return itemlist

    vids = vids.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

    data = do_downloadpage(vids)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    embeds = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')

    if not embeds: return itemlist

    ses = 0

    data = do_downloadpage(embeds)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if '//embed69.' in embeds:
        ses += 1

        datae = data

        e_links = scrapertools.find_single_match(datae, 'const dataLink =(.*?);')
        e_bytes = scrapertools.find_single_match(datae, "const bytes =.*?'(.*?)'")

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

                itemlist.append(Item( channel = item.channel, action = 'play', server=servidor, title = '', crypto=link, bytes=e_bytes,
                                      language=lang, other=other ))

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

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url=url, language=lang, other=other ))

                continue

            elif '/video/' in match:
                datax = do_downloadpage(match)

                matchesx = scrapertools.find_multiple_matches(datax, "go_to_playerVast.*?'(.*?)'")

                for matchx in matchesx:
                    if '/embedsito.' in matchx: continue
                    elif '/player-cdn.' in matchx: continue
                    elif '/1fichier.' in matchx: continue
                    elif '/hydrax.' in matchx: continue
                    elif '/xupalace.' in matchx: continue
                    elif '/uploadfox.' in matchx: continue

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
        logger.info("check-1-crypto: %s" % item.crypto)
        logger.info("check-2-crypto: %s" % item.bytes)
        try:
            ###############url =  AES.decrypt(item.crypto, item.bytes)
            url = AES.new(item.crypto, AES.MODE_SIV==10)
            logger.info("check-3-crypto: %s" % url)

            url = jscrypto.new(item.crypto, 2, IV=item.bytes)
            logger.info("check-4-crypto: %s" % url)
        except:
            return '[COLOR cyan]No se pudo [COLOR red]Desencriptar[/COLOR]'

    if url:
        if '/xupalace.' in url or '/uploadfox.' in url:
            return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if not new_server.startswith("http"): servidor = new_server

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

