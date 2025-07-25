# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


from lib.pyberishaes import GibberishAES
from lib import decrypters


host = 'https://pelisplushd.bz/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://pelisplushd.cx/', 'https://ww3.pelisplushd.nz/', 'https://pelisplushd.top/',
             'https://pelisplushd.rip/', 'https://pelisplushd.run/', 'https://pelisplushd.nz/']


domain = config.get_setting('dominio', 'pelisplushdnz', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'pelisplushdnz')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'pelisplushdnz')
    else: host = domain



def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_pelisplushdnz_proxies', default=''):
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
    if config.get_setting('channel_animefenix_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if '/year/' in url: raise_weberror = False

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('pelisplushdnz', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

        if not data:
            if not 'search?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('PelisPlusHdNz', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('pelisplushdnz', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'pelisplushdnz', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_pelisplushdnz', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='pelisplushdnz', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_pelisplushdnz', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'pelisplushdnz', thumbnail=config.get_thumb('pelisplushdnz') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    if config.get_setting('mnu_doramas', default=False):
        itemlist.append(item.clone( title = 'Doramas', action = 'mainlist_series', text_color = 'firebrick' ))

    if not config.get_setting('descartar_anime', default=False):
       itemlist.append(item.clone( title = 'Animes', action = 'mainlist_animes', text_color = 'springgreen' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas?page=1', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series?page=1', search_type = 'tvshow' ))

    if config.get_setting('mnu_doramas', default=False):
        itemlist.append(item.clone( title = 'Doramas', action = 'list_all', url = host + 'generos/dorama/series?page=1', search_type = 'tvshow', text_color = 'firebrick' ))

    if not config.get_setting('descartar_anime', default=False):
        itemlist.append(item.clone( title = 'Animes', action = 'mainlist_animes', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def mainlist_animes(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color = 'springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'animes?page=1', search_type = 'tvshow' ))

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

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Generos(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, 'href="(.*?)">(.*?)</a>')

    for url, tit in matches:
        if item.group == 'animes':
           if tit == 'Documental': continue
           elif tit == 'Historia': continue

        if item.search_type == 'tvshow':
	        if 'Televisión' in tit: continue

        if config.get_setting('descartar_anime', default=False):
            if title == 'Anime': continue

        url = host[:-1] + url + '?page='

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all', text_color = text_color ))

    return sorted(itemlist, key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    else:
       if item.group == 'animes': text_color = 'springgreen'
       else: text_color = 'hotpink'

    from datetime import datetime
    current_year = int(datetime.today().year)

    if item.search_type == 'movie': limit = 1930
    else:
       if item.group == 'animes': limit = 1989
       else: limit = 1959

    for x in range(current_year, limit, -1):
        url = host + 'year/' + str(x) + '?page=1'

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_all', text_color = text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<div class="Posters">(.*?)<div class="copyright">')

    matches = scrapertools.find_multiple_matches(bloque, '<a(.*?)</a>')

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')
        title = scrapertools.find_single_match(match, '<p>(.*?)</p>')

        if not url or not title: continue

        title =  re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', title)

        if url.startswith('/'): url = host[:-1] + url

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        year = '-'

        if ' (' in title:
            year = title.split(' (')[1]
            year = year.replace(')', '').strip()
        elif ' [' in title:
            year = title.split(' [')[1]
            year = year.replace(']', '').strip()

        if not year == '-':
            if ' (' in title: title = title.replace(' (' + year + ')', '').strip()
            elif ' [' in title: title = title.replace(' [' + year + ']', '').strip()

        if '/year/' in item.url:
            year = scrapertools.find_single_match(item.url, "/year/(.*?)$")
            if year: year = scrapertools.find_single_match(year, "(.*?)page=")

            year = year.replace('?', '')

        if not year: year = '-'

        title = title.replace("&#039;", "'")

        if '/pelicula/' in url:
            if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))
        else:
            if item.search_type == 'movie': continue

            if item.group == 'animes':
                if not '/anime/' in url: continue

            itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<ul class="pagination' in data:
            next_page = scrapertools.find_single_match(data, '<ul class="pagination.*?<li class="page-item active".*?</span>.*?href="(.*?)"')

            if next_page:
                if 'page=' in next_page:
                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    temporadas = re.compile('data-toggle="tab">(.*?)</a>', re.DOTALL).findall(data)

    hay_season0 = False

    tot_tempo = len(temporadas)

    for tempo in temporadas:
        tempo = tempo.replace('Temporada', '').replace('TEMPORADA', '').strip()

        if tempo == '0': hay_season0 = True

        nro_tempo = tempo
        if tot_tempo >= 10:
            if int(tempo) < 10: nro_tempo = '0' + tempo

        title = 'Temporada ' + nro_tempo

        if len(temporadas) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.pills = ''
            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        pills = tempo
        if hay_season0: pills = int(tempo) + 1

        itemlist.append(item.clone( action = 'episodios', title = title, pills = pills, page = 0,
                                   contentType = 'season', contentSeason = tempo, text_color='tan' ))

    tmdb.set_infoLabels(itemlist)

    return sorted(itemlist, key=lambda it: it.title)


def episodios(item):
    logger.info()
    itemlist = []

    tab_epis = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'data-toggle="tab">Temporada.*?' + str(item.contentSeason) + '(.*?)<div class="clear"></div>')
    if not bloque: bloque = scrapertools.find_single_match(data, 'data-toggle="tab">TEMPORADA.*?' + str(item.contentSeason) + '(.*?)<div class="clear"></div>')

    if bloque:
        bloque = scrapertools.find_single_match(bloque, 'id="pills-vertical-' + str(item.pills) + '(.*?)</div>')

        if not bloque: bloque = scrapertools.find_single_match(bloque, 'id="pills-vertical-' + str(item.contentSeason) + '(.*?)</div>')

    matches = re.compile('<a href="(.*?)".*?">(.*?):(.*?)</a>', re.DOTALL).findall(bloque)

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
                platformtools.dialog_notification('PelisPlusHdNz', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('PelisPlusHdNz', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PelisPlusHdNz', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PelisPlusHdNz', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PelisPlusHdNz', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('PelisPlusHdNz', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('PelisPlusHdNz', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, temp_epis, title in matches:
        if not title: continue

        if url.startswith('/'): url = host[:-1] + url

        episode = scrapertools.find_single_match(temp_epis, ".*?-(.*?)$").strip()

        episode = episode.replace('E', '').strip()

        ord_epis = str(episode)

        if len(str(ord_epis)) == 1: ord_epis = '0000' + ord_epis
        elif len(str(ord_epis)) == 2: ord_epis = '000' + ord_epis
        elif len(str(ord_epis)) == 3: ord_epis = '00' + ord_epis
        else:
            if num_matches > 50: ord_epis = '0' + ord_epis

        titulo = str(item.contentSeason) + 'x' + str(episode) + ' ' + title

        if num_matches > 50:
            tab_epis.append([ord_epis, url, titulo, episode])
        else:
            itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                        contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=episode, orden = ord_epis ))

    if num_matches > 50:
        tab_epis = sorted(tab_epis, key=lambda x: x[0])

        for orden, url, tit, epi in tab_epis[item.page * item.perpage:]:
            itemlist.append(item.clone( action = 'findvideos', url = url, title = tit,
                                        orden = orden, contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epi ))

            if len(itemlist) >= item.perpage:
                break

        tmdb.set_infoLabels(itemlist)

        if itemlist:
            if num_matches > ((item.page + 1) * item.perpage):
                itemlist.append(item.clone( title = "Siguientes ...", action = "episodios", data_epi = item.data_epi, orden = '10000',
                                            page = item.page + 1, perpage = item.perpage, text_color = 'coral' ))

        return itemlist

    else:
        tmdb.set_infoLabels(itemlist)

        return sorted(itemlist, key=lambda i: i.orden)


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'0': 'Lat', '1': 'Esp', '2': 'Vose'}

    lang = 'Lat'

    data = do_downloadpage(item.url)

    ses = 0

    matches = scrapertools.find_multiple_matches(data, '<a href="#option(.*?)">(.*?)</a>')

    for opt, srv in matches:
        if not srv: continue

        ses += 1

        url = scrapertools.find_single_match(str(data), 'var video =.*?video.*?' + opt + "].*?'(.*?)'")

        if not url: continue

        srv = srv.lower()

        if srv == 'embed69':
            ses += 1

            datae = do_downloadpage(url)

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
                    elif 'download' in srv: continue

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

        elif srv == 'moe':
            data2 = do_downloadpage(url)

            matches2 = scrapertools.find_multiple_matches(data2, '<li onclick="' + "go_to_player.*?'(.*?)'.*?" + 'data-lang="(.*?)".*?<span>(.*?)</span>')

            for link, lng, srv2 in matches2:
                srv2 = srv2.lower()

                if srv2 == '1fichier': continue
                elif srv2 == 'embedsito': continue
                elif srv2 == 'mirror': continue
                elif srv2 == 'hydrax': continue
	
                elif 'xupalace' in link: continue
                elif 'uploadfox' in link: continue
                elif 'plustream' in link: continue
                elif 'embed69' in link: continue

                if not link: continue

                try:
                    link = base64.b64decode(link).decode("utf-8")
                except:
                    pass

                if '/?uptobox=' in link:
                    link = scrapertools.find_single_match(link, '/?uptobox=(.*?)$')
                    link = 'https://uptobox.com/' + link

                servidor = servertools.get_server_from_url(link)

                if lng == '1': lang = 'Esp'
                elif lng == '2': lang = 'Vose'

                other = ''

                if srv2 == 'plusvip':
                    vid_url = link

                    url_pattern = '(?:[\w\d]+://)?[\d\w]+\.[\d\w]+/moe\?data=(.+)$'
                    src_pattern = "this\[_0x5507eb\(0x1bd\)\]='(.+?)'"

                    data3 = do_downloadpage(vid_url)

                    url = scrapertools.find_single_match(vid_url, url_pattern)
                    src = scrapertools.find_single_match(data3, src_pattern)

                    src_url = "https://plusvip.net{}".format(src)

                    url = do_downloadpage(src_url, post={'link': url}, headers = {'Referer': vid_url})

                    url = scrapertools.find_single_match(url, '"link":"(.*?)"')

                    if not url: continue

                    link = url.replace('\\/', '/')

                    servidor = 'directo'
                    other = 'plusvip'

                if 'plustream' in link: continue

                if servidor == 'various': other = servertools.corregir_other(link)

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = link,
                                      language = IDIOMAS.get(lang, lang), other = other.capitalize() ))

        else:
            lang = '?'

            if '/xupalace.' in url:
                ses += 1

                if 'php?id=' in url:
                    datax = do_downloadpage(url)

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

                elif '/video/' in url:
                    datax = do_downloadpage(url)

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

        if '/xupalace.' in url:
            lang = '?'

            ses += 1

            if 'php?id=' in url:
                datax = do_downloadpage(url)

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

            elif '/video/' in url:
                datax = do_downloadpage(url)

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

        if url:
            if 'api.mycdn.moe/uqlink.php?id=' in url: url = url.replace('api.mycdn.moe/uqlink.php?id=', 'uqload.com/embed-')

            elif 'api.mycdn.moe/dourl.php?id=' in url: url = url.replace('api.mycdn.moe/dourl.php?id=', 'dood.to/e/')

            elif 'api.mycdn.moe/dl/?uptobox=' in url: url = url.replace('api.mycdn.moe/dl/?uptobox=', 'uptobox.com/')

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            link_other = ''

            if servidor == 'directo':
                link_other = scrapertools.find_single_match(data, '<a href="#option' + opt + '">(.*?)</a>')

            link_other = link_other.lower().strip()

            if link_other == '1fichier': continue

            elif 'embedsito' in link_other: continue
            elif 'player-cdn' in link_other: continue
            elif '1fichier' in link_other: continue
            elif 'hydrax' in link_other: continue
            elif 'xupalace' in link_other: continue
            elif 'uploadfox' in link_other: continue

            elif 'plustream' in link_other: continue
            elif 'embed69' in link_other: continue

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url,
	                              language = IDIOMAS.get(lang, lang), other = link_other.capitalize() ))

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
            url = decrypters.decode_decipher(crypto, bytes)

        if not url:
            if crypto.startswith("http"):
                url = crypto.replace('\\/', '/')

            if not url:
                return '[COLOR cyan]No se pudo [COLOR goldenrod]Descifrar[/COLOR]'

        elif not url.startswith("http"):
            return '[COLOR cyan]No se pudo [COLOR goldenrod]Descifrar[/COLOR]'

    if url:
        if '/streamsito.com/uqlink.php?id=' in url: url = url.replace('/streamsito.com/uqlink.php?id=', '/uqload.com/embed-')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if '/plustream.' in url or '/xupalace.' in url:
            return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

        if servidor == 'zplayer': url = url + '|Referer=' + host

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone( url = url, server = servidor ))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<div class="Posters">(.*?)<div class="copyright">')

    matches = scrapertools.find_multiple_matches(bloque, '<a(.*?)</a>')

    for match in matches:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')
        title = scrapertools.find_single_match(match, '<p>(.*?)</p>')

        if not url or not title: continue

        title =  re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', title)

        if url.startswith('/'): url = host[:-1] + url

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        year = '-'

        if ' (' in title:
            year = title.split(' (')[1]
            year = year.replace(')', '').strip()
        elif ' [' in title:
            year = title.split(' [')[1]
            year = year.replace(']', '').strip()

        if not year == '-':
            if ' (' in title: title = title.replace(' (' + year + ')', '').strip()
            elif ' [' in title: title = title.replace(' [' + year + ']', '').strip()

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo, contentType='movie', contentTitle=title, infoLabels={'year': year} ))

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo, contentType = 'tvshow', contentSerieName = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<ul class="pagination' in data:
            next_page = scrapertools.find_single_match(data, '<ul class="pagination.*?<li class="page-item active".*?<a class="page-link" href="(.*?)"')

            if next_page:
                if 'page=' in next_page:
                    next_page = next_page.replace('&amp;', '&')

                    next_page = host[:-1] + '/' + next_page

                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_search', text_color='coral' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
       item.url = host + 'search?s=' + texto.replace(" ", "+") + '&page=1'
       return list_search(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []
