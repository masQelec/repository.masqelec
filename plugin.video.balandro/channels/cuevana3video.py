# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] < 3:
    import urlparse
    PY3 = False
else:
    import urllib.parse as urlparse
    PY3 = True

import re, time

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


LINUX = False
BR = False
BR2 = False

if PY3:
    try:
       import xbmc
       if xbmc.getCondVisibility("system.platform.Linux.RaspberryPi") or xbmc.getCondVisibility("System.Platform.Linux"): LINUX = True
    except: pass

try:
   if LINUX:
       try:
          from lib import balandroresolver2 as balandroresolver
          BR2 = True
       except: pass
   else:
       if PY3:
           from lib import balandroresolver
           BR = true
       else:
          try:
             from lib import balandroresolver2 as balandroresolver
             BR2 = True
          except: pass
except:
   try:
      from lib import balandroresolver2 as balandroresolver
      BR2 = True
   except: pass


host = 'https://cuevana3.ch'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://www1.cuevana3.video', 'https://www2.cuevana3.video', 'https://cuevana3.so',
             'https://www1.cuevana3.so', 'https://www2.cuevana3.so', 'https://cuevana3.cx',
             'https://www1.cuevana3.cx', 'https://www2.cuevana3.cx', 'https://cuevana3.pe',
             'https://www1.cuevana3.pe', 'https://www2.cuevana3.pe', 'https://cuevana3.vc',
             'https://www1.cuevana3.vc', 'https://cuevana3.fm', 'https://www1.cuevana3.fm',
             'https://www1.cuevana3.ch', 'https://www2.cuevana3.ch', 'https://www3.cuevana3.ch',
             'https://www4.cuevana3.ch', 'https://www5.cuevana3.ch', 'https://www6.cuevana3.ch',
             'https://www7.cuevana3.ch', 'https://www8.cuevana3.ch', 'https://www9.cuevana3.ch',
             'https://www10.cuevana3.ch', 'https://www11.cuevana3.ch', 'https://www12.cuevana3.ch',
             'https://ww1.cuevana3.ch', 'https://ww2.cuevana3.ch', 'https://ww3.cuevana3.ch']


domain = config.get_setting('dominio', 'cuevana3video', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'cuevana3video')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'cuevana3video')
    else: host = domain


perpage = 22


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_cuevana3video_proxies', default=''):
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
    if config.get_setting('channel_cuevana3video_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('cuevana3video', url, post=post, headers=headers, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if not data:
            if not '/search.html?keyword=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('Cuevana3Video', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('cuevana3video', url, post=post, headers=headers, timeout=timeout).data
                else:
                   data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    if '<title>You are being redirected...</title>' in data or '<title>Just a moment...</title>' in data:
        if BR or BR2:
            try:
                ck_name, ck_value = balandroresolver.get_sucuri_cookie(data)
                if ck_name and ck_value:
                    httptools.save_cookie(ck_name, ck_value, host.replace('https://', '')[:-1])

                if not url.startswith(host):
                    data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
                else:
                    if hay_proxies:
                        data = httptools.downloadpage_proxy('cuevana3video', url, post=post, headers=headers, timeout=timeout).data
                    else:
                        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
            except:
                pass

    if '<title>Just a moment...</title>' in data:
        if not '/search.html?keyword=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'cuevana3video', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_cuevana3video', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='cuevana3video', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_cuevana3video', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_cuevana3video', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('cuevana3video') ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'cuevana3video', thumbnail=config.get_thumb('cuevana3video') ))

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + '/peliculas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + '/estrenos', search_type = 'movie', text_color='cyan' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + '/peliculas-mas-vistas/mes', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catalogo', action = 'list_all', url = host + '/serie', filtro = 'tabserie-1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host + '/serie', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + '/serie', filtro = 'tabserie-4', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data,'href="#">Géneros</a>(.*?)<li id="menu-item-1954"')
    matches = scrapertools.find_multiple_matches(bloque,'<a href=".*?">.*?</a>')

    for match in matches:
        url = scrapertools.find_single_match(match,'<a href="(.*?)">')
        title = scrapertools.find_single_match(match,'>(.*?)</a>')

        itemlist.append(item.clone( title = title, url = host + url, action = 'list_all', search_type = item.search_type, text_color = 'deepskyblue' ))

    return sorted(itemlist, key=lambda it: it.title)


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    if item.filtro:
        if item.pageser:
            url = host + '/serie?action=cuevana_ajax_pagination&page=' + str(item.pageser)
            data = do_downloadpage(url, headers={'Referer': url})
        else:
            data = do_downloadpage(item.url)

        data = scrapertools.find_single_match(data, '<div\s*id="%s"(.*?)</nav>\s*</div>' % item.filtro)
    else:
        data = do_downloadpage(item.url)

    matches = re.compile('<div class="TPost C(.*?)</li>', re.DOTALL).findall(data)

    num_matches = len(matches)

    for article in matches[item.page * perpage:]:
        url = scrapertools.find_single_match(article, '\s*href=(?:"|)([^ >"]+)')
        if '/pagina-ejemplo' in url: continue

        title = scrapertools.find_single_match(article, '<h2 class="Title">([^<]+)</h2>').strip()

        if not url or not title: continue

        title = title.replace('&#039;s', "'s").strip()

        thumb = scrapertools.find_single_match(article, 'data-src="([^ >]+)"')
        if not thumb: thumb = scrapertools.find_single_match(article, ' src=(?:"|)([^ >"]+)')

        thumb = host + url

        qlty = scrapertools.find_single_match(article, '<span\s*class=(?:"|)Qlty(?:"|)>([^<]+)</span>')
        plot = scrapertools.find_single_match(article, '<p>(.*?)</p>')

        url = host + url

        tipo = 'tvshow' if '/serie/' in url else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, qualities=qlty, fmt_sufijo=sufijo, 
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-', 'plot': plot} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo, 
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': '-', 'plot': plot} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        buscar_next = True
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title = 'Siguientes ...', page = item.page + 1, action = 'list_all', text_color='coral' ))
                buscar_next = False

        if buscar_next:
            if item.filtro:
                pagina = 2 if not item.pageser else item.pageser + 1
                itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', pageser = pagina, text_color='coral' ))
            else:
               if '<nav class="navigation pagination">' in data:
                   bloque_next = scrapertools.find_single_match(data, '<nav class="navigation pagination">(.*?)</nav>')
                   next_page = scrapertools.find_single_match(bloque_next, "class='page-link current'>.*?</a><a href='(.*?)'")

                   if next_page:
                       if not '?page=' in item.url:
                           next_page = item.url + next_page
                       else:
                           ant_url = scrapertools.find_single_match(item.url, "(.*?)page=")
                           ant_url = ant_url.replace('?', '')
                           next_page = ant_url + next_page

                       itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, page = 0, action = 'list_all', text_color='coral' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, 'Ultimos Episodios(.*?)</ul>')

    patron  = '(?is)<a href="([^"]+).*?src="([^"]+).*?"Title">([^<]+).*?<p>([^<]+)'

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for url, thumb, title, date in matches:
        if not url or not title: continue

        season, episode = scrapertools.get_season_and_episode(title).split("x")

        contentSerieName = scrapertools.find_single_match(title, '(.*?) \d')

        title = title.replace('&#039;s', "'s").strip()

        url = host + url

        thumb = 'https://' + thumb

        titulo = str(season) + 'x' + str(episode) + ' ' + title.replace(str(season) + 'x' + str(episode), '') + ' (%s)' % date

        itemlist.append(item.clone( action='findvideos', title = titulo, thumbnail=thumb, url = url,
                                    contentType = 'episode', contentSerieName=contentSerieName, contentSeason = season, contentEpisodeNumber = episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = re.compile('<option value=".*?>Temporada(.*?)</option>', re.DOTALL).findall(data)

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

        itemlist.append(item.clone( action='episodios', title=title, page = 0, contentType='season', contentSeason=tempo, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist=[]

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    if item.contentSeason:
        data = scrapertools.find_single_match(data, '<ul id="season-' + str(item.contentSeason) + '(.*?)</ul>')

    matches = re.compile('<a href="(.*?)">(.*?)</li>', re.DOTALL).findall(data)

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('Cuevana3Video', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('Cuevana3Video', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana3Video', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana3Video', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana3Video', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('Cuevana3Video', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('Cuevana3Video', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, datos in matches[item.page * item.perpage:]:
        try:
            season, epis = scrapertools.find_single_match(url, '-(\d+)x(\d+)$')
        except:
            season = scrapertools.find_single_match(url, '-(\d+)x')
            epis = scrapertools.find_single_match(url, '-.*?x(\d+)$')

        if item.contentSeason:
           if not str(item.contentSeason) == str(season): continue

        title = scrapertools.find_single_match(datos, '<h2[^>]*>(.*?)</h2>')

        thumb = scrapertools.find_single_match(datos, 'data-src=([^ >]+)"')
        if thumb.startswith('//'): thumb = 'https:' + thumb

        url = host + url

        titulo = str(season) + 'x' + str(epis) + ' ' + title.replace(str(season) + 'x' + str(epis), '').strip()

        itemlist.append(item.clone( action='findvideos', title = titulo, thumbnail=thumb, url = url,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > (item.page + 1) * item.perpage:
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def puntuar_calidad(txt):
    orden = ['Cam', 'WEB-S', 'DVD-S', 'TS-HQ', 'DVD', 'DvdRip', 'HD', 'FullHD1080p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'Latino': 'Lat', 'Castellano': 'Esp', 'Subtitulado': 'Vose'}

    data = do_downloadpage(item.url)

    matches = re.compile('<ul class="anime_muti_link server-item-(.*?)</ul>', re.DOTALL).findall(data)

    ses = 0

    hay_pelisplay = False

    for option in matches:
        ses += 1

        links = scrapertools.find_multiple_matches(option, '<li data-(.*?)</li>')

        for link in links:
            url = scrapertools.find_single_match(link, 'video="(.*?)"')
            lang = scrapertools.find_single_match(link,'<span class="cdtr">.*?<span>.*?-(.*?)-.*?</span>').strip()

            qlty = scrapertools.find_single_match(link,'<span class="cdtr">.*?<span>.*?-.*?-(.*?)</span>').strip()
            quality_num = puntuar_calidad(qlty)
            if quality_num == 0: qlty = ''

            if url.startswith('//'): url = 'https:' + url

            if url:
                if 'pelisplay' in url:
                    data2 = do_downloadpage(url)

                    links2 = scrapertools.find_multiple_matches(data2, '<li class="linkserver".*?data-status="1".*?data-video="(.*?)"')

                    if links2:
                        hay_pelisplay = True

                        for link2 in links2:
                            servidor = servertools.get_server_from_url(link2)
                            servidor = servertools.corregir_servidor(servidor)

                            url = servertools.normalize_url(servidor, link2)

                            if '/clonamesta' in url: continue

                            link_other = ''

                            if servidor == 'directo' or servidor == 'various':
                                link_other = normalize_other(url)
                                if link_other == '': continue

                            if not config.get_setting('developer_mode', default=False):
                                if link_other == 'hydrax': continue

                            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, referer = item.url,
                                                  language = IDIOMAS.get(lang, lang), quality = qlty, quality_num = quality_num, other = link_other ))

                            continue

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                if '/clonamesta' in url: continue

                link_other = ''

                if servidor == 'directo' or servidor == 'various':
                    link_other = normalize_other(url)
                    if link_other == '': continue

                if not config.get_setting('developer_mode', default=False):
                    if link_other == 'hydrax': continue

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, referer = item.url,
                                      language = IDIOMAS.get(lang, lang), quality = qlty, quality_num = quality_num, other = link_other ))

    if '<li class="downloadopt">' in data:
        url = scrapertools.find_single_match(data, '<li class="downloadopt">.*?<a href="(.*?)"')
        if url:
            ses += 1

            if url.startswith('//'): url = 'https:' + url

            if 'pelisplay' in url:
                if hay_pelisplay: url = ''
                else:
                   new_url = url.replace('/download', '/play')

                   data2 = do_downloadpage(new_url)

                   links2 = scrapertools.find_multiple_matches(data2, '<li class="linkserver".*?data-status="1".*?data-video="(.*?)"')

                   if links2:
                       for link2 in links2:
                           servidor = servertools.get_server_from_url(link2)
                           servidor = servertools.corregir_servidor(servidor)

                           url = servertools.normalize_url(servidor, link2)

                           if '/clonamesta' in url: continue

                           link_other = ''

                           if servidor == 'directo' or servidor == 'various': link_other = normalize_other(url)

                           if not config.get_setting('developer_mode', default=False):
                               if link_other == 'hydrax': continue

                           itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, referer = item.url, quality = 'HD', other = link_other ))

                           continue

        if url:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            link_other = ''

            if servidor == 'directo' or servidor == 'various': link_other = normalize_other(url)

            if not config.get_setting('developer_mode', default=False):
                if link_other == 'hydrax': link_other = ''

            if link_other:
                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, referer = item.url, quality = 'HD', other = link_other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def normalize_other(url):
    # hydrax no es pot resoldre

    link_other = ''
    url = url.lower()

    if 'pelisplus' in url: link_other = 'plus'
    elif 'peliscloud' in url: link_other = 'cloud'
    elif 'pelisplay' in url: link_other = 'play'
    elif 'damedamehoy' in url: link_other = 'dame'
    elif 'apialfa' in url: link_other = 'apialfa'
    elif 'tomatomatela' in url: link_other = 'dame'
    elif 'hydrax' in url: link_other = 'hydrax'
    elif 'streamwish' in url: link_other = 'Streamwish'
    elif 'filemoon' in url: link_other = 'Filemoon'
    elif 'filelions' in url: link_other = 'Filelions'
    elif 'vidhide' in url: link_other = 'Vidhidepro'
    elif 'goodstream' in url: link_other = 'Goodstream'

    elif 'plustream' in url: link_other = ''

    else:
       if config.get_setting('developer_mode', default=False):
           try:
              link_other = url.split('//')[1]
              link_other = link_other.split('/')[0]
              link_other.lower()
           except:
              link_other = url

    return link_other


def resuelve_dame_toma(dame_url):
    data = do_downloadpage(dame_url)

    url = scrapertools.find_single_match(data, 'file:\s*"([^"]+)')
    if not url:
        checkUrl = dame_url.replace('embed.html#', 'details.php?v=')
        data = do_downloadpage(checkUrl, headers={'Referer': dame_url})
        url = scrapertools.find_single_match(data, '"file":\s*"([^"]+)').replace('\\/', '/')

    return url


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    servidor = item.server

    if servidor and servidor != 'directo':
        itemlist.append(item.clone(server = servidor, url = url))
        return itemlist

    if item.other == 'hydrax':
        v = scrapertools.find_single_match(url, 'v=(\w+)')
        post = 'slug=%s&dataType=mp4' % v
        data = do_downloadpage("https://ping.iamcdn.net/", post = post)
        data = do_downloadpage('https://geoip.redirect-ads.com/?v=%s' % v, headers={'Referer' : url})

        return itemlist

    elif item.other == 'plus':
        data = do_downloadpage(item.url)

        if item.url.startswith('https://pelisplus.icu/play'):
            url = scrapertools.find_single_match(data, "sources:.*?'(.*?)'")
            if url:
                itemlist.append(item.clone(url=url, server='directo'))
                return itemlist

        elif item.url.startswith('https://pelisplus.icu/download'):
            matches = scrapertools.find_multiple_matches(data, '<div class="dowload".*?href="(.*?)"')

            for url in matches:
                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                if servidor and servidor != 'directo':
                    itemlist.append(item.clone(url=url, server=servidor))
                    return itemlist

        matches = scrapertools.find_multiple_matches(data, 'data-video="(.*?)"')

        for url in matches:
            if '//damedamehoy.' in url or '//tomatomatela.' in url :
                url = resuelve_dame_toma(url)

                if url:
                    itemlist.append(item.clone(url=url, server='directo'))
                    return itemlist

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            if servidor and servidor != 'directo':
                itemlist.append(item.clone(url=url, server=servidor))
                return itemlist

        return itemlist

    elif item.other == 'cloud':
        dominio = urlparse.urlparse(url)[1]
        id = scrapertools.find_single_match(url, 'id=(\w+)')
        tiempo = int(time.time())
        url = 'https://' + dominio + '/playlist/' + id + '/%s.m3u8' % tiempo
        data = do_downloadpage(url)

        url = scrapertools.find_single_match(data, '/hls/\w+/\w+') + '?v=%s' % tiempo
        url = "https://" + dominio + url

        servidor = 'directo'
        if '/hls/' in url: servidor = 'm3u8hls'

        itemlist.append(item.clone(url=url, server=servidor))
        return itemlist

    elif item.other == 'dame':
        url = resuelve_dame_toma(item.url)

        if url:
            itemlist.append(item.clone(url=url, server='directo'))
            return itemlist

    elif item.other == 'apialfa':
        fid = scrapertools.find_single_match(item.url, "h=([^&]+)")

        if fid:
            if '/sc/' in item.url:
                post = {'h': fid}

                vid = item.url.replace('https://apialfa.tomatomatela.club/sc/index.php', 'https://apialfa.tomatomatela.club/sc/r.php')

                data = do_downloadpage(vid, post=post)

                url = scrapertools.find_single_match(data, '<meta name="og:url" content="(.*?)"')

                if url:
                    servidor = servertools.get_server_from_url(url)
                    servidor = servertools.corregir_servidor(servidor)

                    url = servertools.normalize_url(servidor, url)

                    itemlist.append(item.clone(url=url, server=servidor))

                return itemlist

            vid = item.url.replace('https://apialfa.tomatomatela.club/ir/player.php', 'https://apialfa.tomatomatela.club/ir/rd.php')

            post = {'url': fid}

            try:
                if not vid.startswith(host):
                    new_url = httptools.downloadpage(vid, post=post, follow_redirects=False).headers['location']
                else:
                    if config.get_setting('channel_cuevana3video_proxies', default=''):
                        new_url = httptools.downloadpage_proxy('cuevana3video', vid, post=post, follow_redirects=False).headers['location']
                    else:
                        new_url = httptools.downloadpage(vid, post=post, follow_redirects=False).headers['location']
            except:
                new_url = ''

            if new_url:
                if new_url.startswith('//'): new_url = 'https:' + new_url

                data = do_downloadpage(new_url)
                vid = scrapertools.find_single_match(data, 'value="(.*?)"')

                if vid:
                    try:
                        if not vid.startswith(host):
                            new_url = httptools.downloadpage(vid, post=post, follow_redirects=False).headers['location']
                        else:
                            if config.get_setting('channel_cuevana3video_proxies', default=''):
                                new_url = httptools.downloadpage_proxy('cuevana3video', vid, post=post, follow_redirects=False).headers['location']
                            else:
                                new_url = httptools.downloadpage(vid, post=post, follow_redirects=False).headers['location']
                    except:
                        new_url = ''

                if new_url:
                    servidor = servertools.get_server_from_url(new_url)
                    servidor = servertools.corregir_servidor(servidor)

                    if servidor and servidor != 'directo':
                        url = servertools.normalize_url(servidor, new_url)

                        itemlist.append(item.clone(url=url, server=servidor))

                    return itemlist

            else:
                vid = 'https://apialfa.tomatomatela.club/ir/redirect_ddh.php'
                try:
                    if not vid.startswith(host):
                        url = httptools.downloadpage(vid, post=post, follow_redirects=False).headers['location']
                    else:
                        if config.get_setting('channel_cuevana3video_proxies', default=''):
                            url = httptools.downloadpage_proxy('cuevana3video', vid, post=post, follow_redirects=False).headers['location']
                        else:
                            url = httptools.downloadpage(vid, post=post, follow_redirects=False).headers['location']
                except:
                    url = ''

                if url:
                    if '//damedamehoy.' in url or '//tomatomatela.' in url :
                        url = resuelve_dame_toma(url)

                        if url: itemlist.append(item.clone(url=url, server='directo'))
                        return itemlist

                    servidor = servertools.get_server_from_url(url)
                    servidor = servertools.corregir_servidor(servidor)

                    url = servertools.normalize_url(servidor, url)

                    itemlist.append(item.clone(url=url, server=servidor))
                    return itemlist

    elif item.other == 'play':
        if '/pelisplay.infoplay':
            return 'Servidor [COLOR goldenrod]No Soportado[/COLOR]'

        elif '/pelisplay.ccplay?' in item.url:
            if not item.url.startswith(host):
                resp = httptools.downloadpage(item.url)
            else:
                if config.get_setting('channel_cuevana3video_proxies', default=''):
                    resp = httptools.downloadpage_proxy('cuevana3video', item.url)
                else:
                    resp = httptools.downloadpage(item.url)

            if not resp.data: return itemlist
        else:
            data = do_downloadpage(item.url)

        matches = scrapertools.find_multiple_matches(data, 'data-video="(.*?)"')

        if not matches:
            url = scrapertools.find_single_match(data, "sources.*?'(.*?)'")

            if url:
                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                itemlist.append(item.clone(url=url, server=servidor))
                return itemlist

        for url in matches:
            if '//damedamehoy.' in url or '//tomatomatela.' in url:
                url = resuelve_dame_toma(url)

            if url:
                itemlist.append(item.clone(url = url, server = 'directo'))
                return itemlist

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            if servidor and servidor != 'directo':
                itemlist.append(item.clone(url = url, server = servidor))
                return itemlist

    if url:
        if '/clonamesta' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"): servidor = new_server

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '/search.html?keyword=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
