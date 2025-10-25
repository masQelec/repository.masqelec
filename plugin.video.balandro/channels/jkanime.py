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


host = 'https://jkanime.net/'


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_jkanime_proxies', default=''):
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
    hay_proxies = False
    if config.get_setting('channel_jkanime_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('jkanime', url, post=post, headers=headers, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if not data:
            if not '/buscar/' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('JKAnime', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('jkanime', url, post=post, headers=headers, timeout=timeout).data
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
                        data = httptools.downloadpage_proxy('jkanime', url, post=post, headers=headers, timeout=timeout).data
                    else:
                        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
            except:
                pass

    if '<title>Just a moment...</title>' in data:
        if not '/buscar/' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='jkanime', folder=False, text_color='chartreuse' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_jkanime', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('jkanime') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_animes(item)


def mainlist_animes(item):
    logger.info()
    itemlist = []

    if config.get_setting('descartar_anime', default=False): return

    if not config.get_setting('ses_pin'):
        if config.get_setting('animes_password'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'all', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_dir', url = host + 'directorio/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host, search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Últimos animes', action = 'list_last', url = host, search_type = 'tvshow', text_color = 'moccasin' ))

    itemlist.append(item.clone( title = 'Más populares', action = 'list_dir', url = host + 'directorio?filtro=popularidad', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'top', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'En emisión', action = 'list_dir', url = host + 'directorio?estado=emision', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Finalizados', action = 'list_dir', url = host + 'directorio?estado=finalizados', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Ovas', action = 'list_dir', url = host + 'directorio?tipo=ovas', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Onas', action = 'list_dir', url = host + 'directorio?tipo=onas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Donghuas', action = 'list_dir', url = host + 'directorio?categoria=donghua', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'list_dir', url = host + 'directorio?tipo=peliculas', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'directorio')

    bloque = scrapertools.find_single_match(data, '>Genero<(.*?)</select>')

    matches = re.compile("<option value='(.*?)'.*? >(.*?)</option>").findall(bloque)

    for val, title in matches:
        url = host + 'directorio?genero=' + val

        itemlist.append(item.clone( action = "list_dir", title = title, url = url, text_color='springgreen' ))

    return sorted(itemlist, key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1979, -1):
        url = host + 'directorio?fecha=' + str(x)

        itemlist.append(item.clone( title = str(x), url = url, action = 'list_dir', text_color='springgreen' ))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    for letra in 'abcdefghijklmnopqrstuvwxyz':
        itemlist.append(item.clone ( title = letra.upper(), url = host + 'directorio?letra=' + letra, action = 'list_dir', text_color='springgreen' ))

    return itemlist


def list_dir(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile('{"id":(.*?)short_title"').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, '"slug":"(.*?)"')

        title = scrapertools.find_single_match(match, '"title":"(.*?)"')

        if not url or not title: continue

        url = host + url

        title = title.replace('&quot;', '').replace('&amp;', '').replace('&#039;s', "'s").replace('&#039;', "'").strip()

        thumb = scrapertools.find_single_match(match, '"image":"(.*?)"')

        thumb = thumb.replace('\\/', '/')

        year = scrapertools.find_single_match(title, '(\d{4})')
        if year: title = title.replace('(' + year + ')', '')
        else: year = '-'

        tipo = 'tvshow' if '"TV"' in match or '"OVA"' in match or '"ONA"' in match or '"Serie"' in match else 'movie'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            season = 1

            if 'Season' in title:
                if '2nd' in title: season = 2
                elif '3rd' in title: season = 3
                elif '4th' in title: season = 4
                elif '5th' in title: season = 5
                elif '6th' in title: season = 6
                elif '7th' in title: season = 7
                elif '8th' in title: season = 8
                elif '9th' in title: season = 9
                else:
                   season = scrapertools.find_single_match(title, 'Season(.*?)Capítulo').strip()
                   if not season : season = scrapertools.find_single_match(title, 'Season(.*?)$').strip()

                   if not season: season = 1

            SerieName = corregir_SerieName(title)

            title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=SerieName, contentSeason = season, infoLabels={'year': year} ))

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            url = url + 'pelicula/'

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<li class="page-item active".*?href="(.*?)".*?"')

        if next_page:
            next_page = next_page.replace('&amp;', '&')

            itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_dir', text_color = 'coral' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if '/buscar/' in item.url:
        matches = re.compile('<div class="anime__item">(.*?)</div></div>').findall(data)
    else:
        matches = re.compile('<div data-rank="(.*?)</i').findall(data)

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h5>.*?">(.*?)</a>')
        if not title: title = scrapertools.find_single_match(match, 'alt="(.*?)"')

        if not url or not title: continue

        title = title.replace('&quot;', '').replace('&amp;', '').replace('&#039;s', "'s").replace('&#039;', "'").strip()

        thumb = scrapertools.find_single_match(match, 'data-setbg"(.*?)"')

        year = scrapertools.find_single_match(title, '(\d{4})')
        if year: title = title.replace('(' + year + ')', '')
        else: year = '-'

        tipo = 'movie' if 'Pelicula' in match else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            season = 1

            if 'Season' in title:
                if '2nd' in title: season = 2
                elif '3rd' in title: season = 3
                elif '4th' in title: season = 4
                elif '5th' in title: season = 5
                elif '6th' in title: season = 6
                elif '7th' in title: season = 7
                elif '8th' in title: season = 8
                elif '9th' in title: season = 9
                else:
                   season = scrapertools.find_single_match(title, 'Season(.*?)Capítulo').strip()
                   if not season : season = scrapertools.find_single_match(title, 'Season(.*?)$').strip()

                   if not season: season = 1

            SerieName = corregir_SerieName(title)

            title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=SerieName, contentSeason = season, infoLabels={'year': year} ))

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            url = url + 'pelicula/'

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<a class="text nav-next".*?href="(.*?)".*?">Resultados')

        if next_page:
            itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>Animes recientes<(.*?)</div></div></div>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?<img src="(.*?)".*?alt="(.*?)"')

    for url, thumb, title in matches:
        title = title.replace('&quot;', '').replace('&amp;', '').replace('&#039;s', "'s").replace('&#039;', "'").strip()

        year = scrapertools.find_single_match(title, '(\d{4})')
        if year: title = title.replace('(' + year + ')', '')
        else: year = '-'

        season = 1

        if 'Season' in title:
            if '2nd' in title: season = 2
            elif '3rd' in title: season = 3
            elif '4th' in title: season = 4
            elif '5th' in title: season = 5
            elif '6th' in title: season = 6
            elif '7th' in title: season = 7
            elif '8th' in title: season = 8
            elif '9th' in title: season = 9
            else:
               season = scrapertools.find_single_match(title, 'Season(.*?)Capítulo').strip()
               if not season : season = scrapertools.find_single_match(title, 'Season(.*?)$').strip()

               if not season: season = 1

        SerieName = corregir_SerieName(title)

        title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb,
                                    contentType='tvshow', contentSerieName=SerieName, contentSeason = season, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, 'id="animes"(.*?)id="donghuas"')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?<div class="d-thumb">.*?src="(.*?)".*?alt="(.*?)".*?<span class="badge badge-primary">Ep (.*?)</span>')

    for url, thumb, title, epis in matches:
        if not epis: epis = 1

        title = title.replace('&quot;', '').replace('&amp;', '').replace('&#039;s', "'s").replace('&#039;', "'").strip()

        season = 1

        if 'Season' in title:
            if '2nd' in title: season = 2
            elif '3rd' in title: season = 3
            elif '4th' in title: season = 4
            elif '5th' in title: season = 5
            elif '6th' in title: season = 6
            elif '7th' in title: season = 7
            elif '8th' in title: season = 8
            elif '9th' in title: season = 9
            else:
               season = scrapertools.find_single_match(title, 'Season(.*?)-').strip()
               if not season : season = scrapertools.find_single_match(title, 'Season(.*?)$').strip()

               if not season: season = 1

        SerieName = title

        SerieName = SerieName.strip()

        title = 'Cap. ' + epis + ' ' + title

        title = title.replace('Cap. ', '[COLOR goldenrod]Epis. [/COLOR]')

        title = title.replace('Season', '[COLOR tan]Temp.[/COLOR]').replace('season', '[COLOR tan]Temp.[/COLOR]')

        itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail=thumb,
                                    contentSerieName=SerieName, contentType='episode', contentSeason = season, contentEpisodeNumber=epis ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 1
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    if '>Por estrenar<' in data:
        platformtools.dialog_notification(config.__addon_name, '[COLOR cyan][B]Por Estrenar[/B][/COLOR]')
        return

    _token = scrapertools.find_single_match(data, '<meta name="csrf-token" content="(.*?)"')

    if not _token: return itemlist

    id_serie = scrapertools.find_single_match(data, '/ajax/episodes/(\d+)/')

    if not id_serie:
        title = scrapertools.find_single_match(data, '<h3>(.*?)</h3>')
        itemlist.append(item.clone( action='findvideos', title = title, url = item.url ))
        return itemlist

    pag_nro = 1

    i = 0

    headers = {"Referer": item.url}

    post = {'_token': _token}

    url = host + 'ajax/episodes/%s/%s/' % (id_serie, pag_nro)

    data1 = do_downloadpage(url, post=post, headers=headers)

    total = scrapertools.find_single_match(data1, '"total":(.*?)}')

    if not total: return itemlist

    matches = scrapertools.find_multiple_matches(data1, '"number":(\d+),"title"\:"([^"]+)"')

    for nro, title in matches:
        i += 1

        title = title.strip()

        if item.contentSerieName:
            titulo = str(item.contentSeason) + 'x' + str(nro) + ' ' + title.replace(' - ' + str(nro), '').strip()
            season = item.contentSeason
        else:
            titulo = item.title
            season = 1

        titulo = titulo.replace('Season', '[COLOR tan]Temp.[/COLOR]')

        url = item.url + '/' + nro

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = nro ))

    if not str(i) == str(total):
       if config.get_setting('channels_charges', default=True):
           platformtools.dialog_notification('JkAnime', '[COLOR cyan]Cargando ' + str(total) + ' episodios[/COLOR]')

       bucle_pags = True

       while bucle_pags:
           pag_nro += 1

           url = host + 'ajax/episodes/%s/%s/' % (id_serie, pag_nro)

           data1 = do_downloadpage(url, post=post, headers=headers)

           matches = scrapertools.find_multiple_matches(data1, '"number":(\d+),"title"\:"([^"]+)"')

           for nro, title in matches:
               i += 1

               title = title.strip()

               if item.contentSerieName:
                   titulo = str(item.contentSeason) + 'x' + str(nro) + ' ' + title.replace(' - ' + str(nro), '').strip()
                   season = item.contentSeason
               else:
                   titulo = item.title
                   season = 1

               titulo = titulo.replace('Season', '[COLOR tan]Temp.[/COLOR]')

               url = item.url + '/' + nro

               itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                           contentType = 'episode', contentSeason = season, contentEpisodeNumber = nro ))

           if not str(i) == str(total): continue

           bucle_pags = False

    tmdb.set_infoLabels(itemlist)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if not config.get_setting('ses_pin'):
        if config.get_setting('animes_password'):
            if config.get_setting('adults_password'):
                from modules import actions
                if actions.adults_password(item) == False: return

        config.set_setting('ses_pin', True)

    data = do_downloadpage(item.url)

    data = data.replace('src=https', 'src="https').replace('/ width="', '/" width="')

    # ~ Servers
    v_servers = scrapertools.find_single_match(data, 'var servers =(.*?);')

    if v_servers:
        matches = re.compile('"remote":"(.*?)".*?"server":"(.*?)"', re.DOTALL).findall(str(v_servers))

        for remote, srv in matches:
            srv = srv.lower()

            url = 'https://jkanime.net/c1.php?u=' + remote + '&s=' + srv

            itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', url = url,
                                  language = 'Vose', other = srv.capitalize() ))

    # ~ Iframe
    matches = re.compile('video\[\d+\] = \'<iframe.*?src="(.*?)".*?</iframe>', re.DOTALL).findall(data)

    ses = 0

    for url in matches:
        if url == "/','src=": continue

        ses += 1

        if 'jkanime.net/um2.php' in url: url = url.replace('jkanime.net/um2.php', 'jkanime.net/um.php')
        elif '/um2.php' in url: url = url.replace('/um2.php', '/um.php')

        other = ''

        if "/um.php" in url: other = 'um'
        elif "/um2.php" in url: other = 'um2'
        elif "/umv.php" in url: other = 'umv'

        elif "/jk.php" in url: other = 'jk'
        elif '/jksw.php' in url: other =  'jksw'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servidor == 'directo':
           if url.startswith("/jkfembed?u="): continue

           elif url.startswith("/jkokru.php?u="):
               url = url.replace('/jkokru.php?u=', 'https://ok.ru/videoembed/')
               servidor = 'okru'
           elif url.startswith("/jkvmixdrop?u="):
               url = url.replace('/?u=', 'https://mixdrop.co/e/')
               servidor = 'mixdrop'
           else:
               if not url.startswith(host): url = host[:-1] + url

               if "okru" in url: servidor = 'okru'
               if "mixdrop" in url: servidor = 'mixdrop'

        if servidor == 'various': other = servertools.corregir_other(url)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, language = 'Vose', other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url_play = item.url

    if "/um.php" in item.url or "/um2.php" in item.url or "/umv.php" in item.url:
        item.url = item.url.replace('/um2.php', '/um.php').replace('/umv.php', '/um.php')

        headers = {"Referer": item.url}
        data = do_downloadpage(item.url, headers = headers)

        url_play = scrapertools.find_single_match(data, "swarmId: \'([^\']+)\'")

    elif "/jk.php" in item.url or "/jksw.php" in item.url:
        item.url = item.url.replace('/jksw.php', '/jk.php')

        data = do_downloadpage(item.url)

        url_play = scrapertools.find_single_match(data, '<source src="(.*?)"')
        if not url_play: url_play = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')
        if not url_play: url_play = scrapertools.find_single_match(data, "video: {.*?url:.*?'(.*?)'")

        if host in url_play:
            if not url_play.startswith(host):
                url = httptools.downloadpage(url_play, follow_redirects=False, only_headers=True).headers.get("location", "")
            else:
                if config.get_setting('channel_jkanime_proxies', default=''):
                    url = httptools.downloadpage_proxy('jkanime', url_play, follow_redirects=False, only_headers=True).headers.get("location", "")
                else:
                    url = httptools.downloadpage(url_play, follow_redirects=False, only_headers=True).headers.get("location", "")

            url_play = url

    elif "/c1.php?u=" in item.url:
        item.url = item.url.replace(host, host + 'jkplayer/').replace('c1.php?', 'c1?')

        data = do_downloadpage(item.url)

        url_play = scrapertools.find_single_match(data, '<source src="(.*?)"')
        if not url_play: url_play = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')
        if not url_play: url_play = scrapertools.find_single_match(data, "video: {.*?url:.*?'(.*?)'")

        if host in url_play:
            if not url_play.startswith(host):
                url = httptools.downloadpage(url_play, follow_redirects=False, only_headers=True).headers.get("location", "")
            else:
                if config.get_setting('channel_jkanime_proxies', default=''):
                    url = httptools.downloadpage_proxy('jkanime', url_play, follow_redirects=False, only_headers=True).headers.get("location", "")
                else:
                    url = httptools.downloadpage(url_play, follow_redirects=False, only_headers=True).headers.get("location", "")

            url_play = url

    elif "okru" in item.url or "mixdrop" in item.url:
        data = do_downloadpage(item.url)

        url_play = scrapertools.find_single_match(data, '<iframe.*?src="([^"]+)"')

    if url_play:
        if not item.other:
            if not config.get_setting('developer_mode', default=False): return itemlist

        if '.playmudos.' in url_play: return itemlist
        elif '/content-na.drive.' in url_play: return itemlist

        elif '/jkplayer/um?' in url_play or '/jkplayer/umv?' in url_play:
            return '[COLOR red]CloudFlare Protection[/COLOR]'

        if not url_play.startswith("http"): url_play = "https:" + url_play

        url_play = url_play.replace("\\/", "/")

        servidor = servertools.get_server_from_url(url_play)
        servidor = servertools.corregir_servidor(servidor)

        url_play = servertools.normalize_url(servidor, url_play)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url_play).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        itemlist.append(item.clone(url = url_play, server = servidor))

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if 'OVA' in SerieName: SerieName = SerieName.split("OVA")[0]

    if 'Specials' in SerieName: SerieName = SerieName.split("Specials")[0]
    elif 'Special' in SerieName: SerieName = SerieName.split("Special")[0]
    elif 'Especiales' in SerieName: SerieName = SerieName.split("Epeciales")[0]
    elif 'Especial' in SerieName: SerieName = SerieName.split("Epecial")[0]

    if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
    if 'season' in SerieName: SerieName = SerieName.split("season")[0]

    if 'Movie' in SerieName: SerieName = SerieName.split("Movie")[0]

    if '(TV)' in SerieName: SerieName = SerieName.split("(TV)")[0]

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
        item.url = host + 'buscar/' + texto.replace(" ", "_")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

