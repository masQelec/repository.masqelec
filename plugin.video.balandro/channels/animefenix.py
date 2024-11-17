# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True

import re

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


host = 'https://www3.animefenix.tv/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://www.animefenix.com/', 'https://animefenix.tv/', 'https://www.animefenix.tv/']


domain = config.get_setting('dominio', 'animefenix', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'animefenix')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'animefenix')
    else: host = domain


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_animefenix_proxies', default=''):
        tit = '[COLOR %s][B]Quitar los proxies del canal[/B][/COLOR]' % color_list_proxies
        context.append({'title': tit, 'channel': item.channel, 'action': 'quitar_proxies'})

    tit = '[COLOR %s]Ajustes categoría proxies[/COLOR]' % color_exec
    context.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio ' + host + ' necesitarás un proxy.'
    return item.clone( title = '[B]Configurar proxies a usar[/B] ...', action = 'configurar_proxies', folder=False, context=context, plot=plot, text_color='red' )

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
    if config.get_setting('channel_animefenix_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('animefenix', url, post=post, headers=headers, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if not data:
            if not 'animes?q=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('AnimeFenix', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('animefenix', url, post=post, headers=headers, timeout=timeout).data
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
                        data = httptools.downloadpage_proxy('animefenix', url, post=post, headers=headers, timeout=timeout).data
                    else:
                        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
            except:
                pass

    if '<title>Just a moment...</title>' in data:
        if not 'animes?q=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'animefenix', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_animefenix', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='animefenix', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_animefenix', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_animefenix', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('animefenix') ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'animefenix', thumbnail=config.get_thumb('animefenix') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_animes(item)


def mainlist_animes(item):
    logger.info()
    itemlist = []

    if config.get_setting('descartar_anime', default=False): return

    if config.get_setting('adults_password'):
        from modules import actions
        if actions.adults_password(item) == False: return

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'all', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'animes?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host, search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Últimos animes', action = 'list_last', url = host, search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'animes?estado[]=1?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'animes?estado[]=2?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Donghuas', action = 'list_all', url = host + 'animes?type[]=donghua&order=defaultpage=1',  search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Especiales', action = 'list_all', url = host + 'animes?type[]=special&order=default?page=1',  search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Ovas', action = 'list_all', url = host + 'animes?type[]=ova&order=default?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'animes?type[]=movie&order=defaultpage=1', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    url_cat = host + 'animes'

    data = do_downloadpage(url_cat)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    data = scrapertools.find_single_match(data, r'<select name="[^"]+" id="order_select"(.*?)<\/select>')

    matches = re.compile(r'<option value="([^"]+)"\s*>([^<]+)').findall(data)

    for categoria, title in matches:
        url = "%s?order=%s&page=1" % (url_cat, categoria)

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='moccasin' ))

    return sorted(itemlist,key=lambda x: x.title)


def generos(item):
    logger.info()
    itemlist = []

    url_genre = host + 'animes'

    data = do_downloadpage(url_genre)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)


    bloque = scrapertools.find_single_match(data, '<select name="genero(.*?)</select>')

    matches = re.compile('<option value="([^"]+)"\s*>([^<]+)</option>').findall(bloque)

    for genre_id, title in matches:
        if title == "Ángeles": title = 'Angeles'

        url = "%s?genero[]=%s&order=default&page=1" % (url_genre, genre_id)

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='springgreen' ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    url_anio = host + 'animes'

    data = do_downloadpage(url_anio)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<select name="year(.*?)</select>')

    matches = re.compile('<option value="([^"]+)"\s*>([^<]+)</option>').findall(bloque)

    for anio, title in matches:
        url = "%s?year[]=%s&order=default&page=1" % (url_anio, anio)

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('<article(.*?)</article>').findall(data)
    if not matches: matches = re.compile('<div class="group(.*?)</a>').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'title="(.*?)"')
        if not title: title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, '<img src="(.*?)"')

        year = scrapertools.find_single_match(match, '<span class="bg-primary text-white text-xs px-2 py-1 rounded">(.*?)</span>')
        if not year: year = '-'

        title = title.replace('&quot;', '').replace('&amp;', '').strip()

        SerieName = corregir_SerieName(title)

        tipo = 'movie' if '>Película<' in match else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, fmt_sufijo = sufijo, 
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': year} ))

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, fmt_sufijo = sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '"Pagination"' in data:
            next_page = scrapertools.find_single_match(data, '"Pagination".*?text-white">.*?<a href="(.*?)".*?</nav>')

            if next_page:
                if 'page=' in next_page:
                    next_page = item.url.split("?")[0] + next_page

                    itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Series Recientes<(.*?)>Comentarios<')

    matches = scrapertools.find_multiple_matches(bloque, '<div class="group.*?<img src="(.*?)".*?alt="(.*?)".*?<a href="(.*?)"')

    for thumb, title, url in matches:
        title = title.replace('&quot;', '').replace('&amp;', '').strip()

        SerieName = corregir_SerieName(title)

        title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb,
                                    contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Episodios recientes<(.*?)>Series Recientes<')

    matches = re.compile('<div class="group.*?<img src="(.*?)".*?alt="(.*?)".*?<p class="text-xs text-gray-400">(.*?)</p>.*?<a href="(.*?)"', re.DOTALL).findall(bloque)

    for thumb, title, episode, url in matches:
        title = title.replace('&quot;', '').replace('&amp;', '').strip()

        SerieName = corregir_SerieName(title)

        try:
            epis = scrapertools.find_single_match(episode, "Episodio.*?(\d+)")
            if not epis: epis = scrapertools.find_single_match(episode, "Ep..*?(\d+)")
        except:
            epis = 1

        SerieName = SerieName.replace(str(epis), '').strip()

        title = episode + ' ' + title.replace(str(epis), '').strip()

        title = title.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('Ep.', '[COLOR goldenrod]Epis.[/COLOR]')

        title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        if url:
            itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail=thumb, infoLabels={'year': '-'},
                                        contentSerieName = SerieName, contentType = 'episode', contentSeason = 1, contentEpisodeNumber=epis))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    hay_proximo = False
    if '>Próximo episodio' in data: hay_proximo = True

    matches = re.compile('<li class="hover.*?<a href="(.*?)".*?<span class="font-semibold">(.*?)</span>', re.DOTALL).findall(data)

    if not matches:
        if '>Próximamente<' in data:
             platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#039;', "'").replace('&#8217;', "'"), '[COLOR cyan]Proximamente[/COLOR]')
             return

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('AnimeFenix', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('AnimeFenix', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeFenix', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeFenix', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeFenix', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('AnimeFenix', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('AnimeFenix', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, title in matches[item.page * item.perpage:]:
        title = title.strip()

        try:
            epis = scrapertools.find_single_match(title, "Episodio.*?(\d+)")
        except:
            epis = 1

        if item.contentSerieName: titulo = '1x' + str(epis) + ' ' + title.replace('Episodio ' + str(epis), '').strip() + ' ' + item.contentSerieName
        else: titulo = item.title

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, contentType = 'episode', contentSeason = 1, contentEpisodeNumber=epis ))

        if len(itemlist) >= item.perpage:
            if hay_proximo:
                next_cap = scrapertools.find_single_match(data, '>Próximo episodio.*?</span>(.*?)</li>').strip()

                if next_cap:
                    next_cap = 'Próx. Epis.: ' + next_cap
                    itemlist.append(item.clone( action='', title = next_cap, thumbnail = item.thumbnail, text_color='cyan' ))
            break

    tmdb.set_infoLabels(itemlist)

    if not itemlist:
        if hay_proximo:
            next_cap = scrapertools.find_single_match(data, '>Próximo episodio.*?</span>(.*?)</li>').strip()

            if next_cap:
                platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Proximamente[/B][/COLOR]')

                next_cap = 'Próx. Epis.: ' + next_cap
                itemlist.append(item.clone( action='', title = next_cap, thumbnail = item.thumbnail, text_color='cyan', infoLabels={'year': ''} ))

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    srvs = scrapertools.find_multiple_matches(data, '<a href="#vid(.*?)".*?">(.*?)</a>')

    matches = re.compile("tabsArray\['\d+'\] = " + '.*?"(.*?)"', re.DOTALL).findall(data)

    ses = 0

    for url in matches:
        ses += 1

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        serv = ''

        for vid, srv in srvs:
            if not vid == str(ses): continue

            serv = srv.lower().strip()
            break

        if serv == 'fireload': continue

        elif serv == 'gamo': servidor = 'gamovideo'
        elif serv == 'ru': servidor = 'okru'
        elif serv == 'burst': servidor = 'burstcloud'
        elif serv == 'yourupload': servidor = 'yourupload'
        elif serv == 'mp4upload': servidor = 'mp4upload'
        elif serv == 'sendvid': servidor = 'sendvid'
        elif serv == 'm': servidor = 'mega'

        if serv == 'stream2':
            servidor = 'various'
            serv = 'Streamwish'
        elif serv == 'lion':
            servidor = 'various'
            serv = 'Filelions'
        elif serv == 'tera':
            servidor = 'various'
            serv = 'Terabox'
        elif serv == 'dea':
            servidor = 'zures'
            serv = 'Videa'
        elif serv == 'hide':
            servidor = 'various'
            serv = 'Vidhide'

        if serv == servidor: serv = ''
        elif serv == 'gamo': serv = ''
        elif serv == 'ru': serv = ''
        elif serv == 'burst': serv = ''
        elif serv == 'm': serv = ''

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language ='Vose', other = serv ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.url.startswith('//'): item.url = 'https:' + item.url

    item.url = item.url.replace('&amp;', '&')

    servidor = item.server

    url = item.url

    if '/stream/amz.php' in url:
        if not url.startswith("http"): url = host + url[1:]

        data = do_downloadpage(url)

        url = scrapertools.find_single_match(data, '"file":"([^"]+)"')

    elif '/redirect.php?' in url:
        data = do_downloadpage(url)

        url = scrapertools.find_single_match(data, 'playerContainer.*?src="([^"]+)"')

        if '/stream/amz.php' in url:
            if not url.startswith("http"): url = host + url[1:]

            data = do_downloadpage(url)

            url = scrapertools.find_single_match(data, '"file":"([^"]+)"')

        elif '.fireload.' in url: url = scrapertools.find_single_match(url, 'v=(.*?)$')

    if url:
        if not url.startswith("http"): url = "https:" + url

        url = url.replace('&amp;', '&').replace("\\/", "/")

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if not new_server.startswith("http"): servidor = new_server

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if 'Peliculas' in SerieName: SerieName = SerieName.split("Peliculas")[0]
    if 'Latino' in SerieName: SerieName = SerieName.split("Latino")[0]
    if 'Movie' in SerieName: SerieName = SerieName.split("Movie")[0]

    if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
    if 'season' in SerieName: SerieName = SerieName.split("season")[0]

    if ': ' in SerieName: SerieName = SerieName.split(": ")[0]

    if ' Picture ' in SerieName: SerieName = SerieName.split(" Picture ")[0]

    if ' Specials' in SerieName: SerieName = SerieName.split(" Specials")[0]
    if ' Especiales' in SerieName: SerieName = SerieName.split(" Especiales")[0]
    if ' Drama' in SerieName: SerieName = SerieName.split(" Drama")[0]
    if ' OVA' in SerieName: SerieName = SerieName.split(" OVA")[0]

    if '2nd' in SerieName: SerieName = SerieName.split("2nd")[0]
    if '3rd' in SerieName: SerieName = SerieName.split("3rd")[0]
    if '4th' in SerieName: SerieName = SerieName.split("4th")[0]
    if '5th' in SerieName: SerieName = SerieName.split("5th")[0]
    if '6th' in SerieName: SerieName = SerieName.split("6th")[0]
    if '7th' in SerieName: SerieName = SerieName.split("7th")[0]
    if '8th' in SerieName: SerieName = SerieName.split("8th")[0]
    if '9th' in SerieName: SerieName = SerieName.split("9th")[0]

    SerieName = SerieName.strip()

    return SerieName


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'animes?q=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

