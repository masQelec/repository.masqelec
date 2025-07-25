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


host = 'https://srnovelas.com/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://www.srnovelas.cc/', 'https://meganovelas.online/', 'https://srnovelas.org/']

domain = config.get_setting('dominio', 'srnovelas', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'srnovelas')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'srnovelas')
    else: host = domain


perpage = 20


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_srnovelas_proxies', default=''):
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

    if not headers: headers = {'Referer': host}

    hay_proxies = False
    if config.get_setting('channel_srnovelas_proxies', default=''): hay_proxies = True

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('srnovelas', url, post=post, headers=headers).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers).data

        if not data:
            if not '?s=' in url:
                if not '/temp/ajax/iframe.php?id=' in url:
                    if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('SrNovelas', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                    timeout = config.get_setting('channels_repeat', default=30)

                    if hay_proxies:
                        data = httptools.downloadpage_proxy('srnovelas', url, post=post, headers=headers, timeout=timeout).data
                    else:
                        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    if '<title>You are being redirected...</title>' in data or '<title>Just a moment...</title>' in data:
        if BR or BR2:
            try:
                ck_name, ck_value = balandroresolver.get_sucuri_cookie(data)
                if ck_name and ck_value:
                    httptools.save_cookie(ck_name, ck_value, host.replace('https://', '')[:-1])

                if not url.startswith(host):
                    data = httptools.downloadpage(url, post=post, headers=headers).data
                else:
                    if hay_proxies:
                        data = httptools.downloadpage_proxy('srnovelas', url, post=post, headers=headers).data
                    else:
                        data = httptools.downloadpage(url, post=post, headers=headers).data
            except:
                pass

    if '<title>Just a moment...</title>' in data:
        if not '?s=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'srnovelas', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_srnovelas', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='srnovelas', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_srnovelas', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_srnovelas', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('srnovelas') ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'srnovelas', thumbnail=config.get_thumb('srnovelas') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'novelas-completas/', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_epis', url = host, search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'Por país', action = 'paises', search_type = 'tvshow' ))

    return itemlist


def paises(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'América', action = 'list_all', url = host + 'novelas-americanas/', text_color='hotpink' ))
    itemlist.append(item.clone( title = 'Brasil', action = 'list_all', url = host + 'novelas-brasilenas/', text_color='hotpink' ))
    itemlist.append(item.clone( title = 'Chile', action = 'list_all', url = host + 'novelas-chilenas/', text_color='hotpink' ))
    itemlist.append(item.clone( title = 'Colombia', action = 'list_all', url = host + 'novelas-colombianas/', text_color='hotpink' ))
    itemlist.append(item.clone( title = 'México', action = 'list_all', url = host + 'novelas-mexicanas/', text_color='hotpink' ))
    itemlist.append(item.clone( title = 'Turquía', action = 'list_all', url = host + 'novelas-turcas/', text_color='hotpink' ))

    return itemlist


def last_epis(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    matches = scrapertools.find_multiple_matches(data, '<div class="grid-item item-(.*?)/div></a></div>')

    for match in matches:
        url = scrapertools.find_single_match(match, 'href="(.*?)"')

        title = scrapertools.find_single_match(match, '<h2>(.*?)</h2>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        SerieName = scrapertools.find_single_match(match, 'alt="(.*?)"')
        if not SerieName:
            SerieName = scrapertools.find_single_match(match, '<h2>(.*?)Capitulo')
            SerieName = SerieName.replace('Final', '').strip()

        season = 1

        epis = scrapertools.find_single_match(match, '<h2>.*?Capitulo(.*?)</h2>')
        epis = epis.replace('Final', '').strip()

        if not epis: epis = 1

        titulo = str(season) + 'x' + str(epis) + ' ' + SerieName

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, infoLabels={'year': '-'},
                                    contentSerieName = SerieName, contentType = 'episode', contentSeason = season, contentEpisodeNumber = epis ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_url = scrapertools.find_single_match(data, 'class="page-numbers current">.*?href="(.*?)"')

        if next_url:
            if '/page/' in next_url:
                itemlist.append(item.clone( title = 'Siguientes ...', url = next_url, action = 'last_epis', text_color = 'coral' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)

    if '>Novelas Completas Gratis<' in data: bloque = scrapertools.find_single_match(data, '>Novelas Completas Gratis<(.*?)</main>')
    else: bloque = scrapertools.find_single_match(data, '<h1>(.*?)$')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, ' title="(.*?)"')
        if not title: title = scrapertools.find_single_match(match, ' alt="(.*?)"')

        if not url or not title: continue

        title = title.replace('&#8211;', "").replace('&#8220;', "").replace('&#8221;', "").strip()
        title = title.replace('&#8216;', "").replace('&#8217;', "").strip()
        title = title.replace('&amp;', '&')

        if title.startswith("Serie "): title = title.replace('Serie ', '').strip()

        year = '-'

        try:
           name = title.split(" (")[0]
           year = title.split(" (")[1]
           if ')' in year: year = year.split(")")[0]
           elif '-' in year: year = year.split("-")[0]

           if year: title = name
        except:
            name = title

        SerieName = name

        if 'Temporada' in SerieName: SerieName = SerieName.split("Temporada")[0]
        elif 'temporada' in SerieName: SerieName = SerieName.split("temporada")[0]

        SerieName = SerieName.strip()

        if 'Capitulos' in SerieName: SerieName = SerieName.split("Capitulos")[0]
        elif 'capitulos' in SerieName: SerieName = SerieName.split("capitulos")[0]

        SerieName = SerieName.strip()

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        title = title.capitalize()

        title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

        itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb,
                                    contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': year} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage

            if hasta < num_matches:
                itemlist.append(item.clone( title='Siguientes ...', page = item.page + 1, action='list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    seasons = scrapertools.find_multiple_matches(data, '<span class="su-spoiler-icon">.*?Temporada(.*?)</div>')

    if not seasons:
        if config.get_setting('channels_seasons', default=True):
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'sin [COLOR tan]Temporadas[/COLOR]')

        item.page = 0
        item.contentType = 'season'
        item.contentSeason = 1
        itemlist = episodios(item)
        return itemlist

    for title in seasons:
        tempo = title.strip()

        title = 'Temporada ' + title.strip()

        if len(seasons) == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, page = 0, contentType = 'season', contentSeason = tempo, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    if '<span class="su-spoiler-icon">' in data:
        bloque = scrapertools.find_single_match(data, '<span class="su-spoiler-icon">.*?Temporada ' + str(item.contentSeason) + '(.*?)</div></div>')
        if not bloque: bloque = scrapertools.find_single_match(data, '<ul class="su-posts su-posts-list-loop(.*?)</ul>')
    else:
        bloque = scrapertools.find_single_match(data, '<ul class="su-posts su-posts-list-loop(.*?)</ul>')

    episodes = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?>(.*?)</a>')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(episodes)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('SrNovelas', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('SrNovelas', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:

            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SrNovelas', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SrNovelas', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SrNovelas', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('SrNovelas', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('SrNovelas', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, title, in episodes[item.page * item.perpage:]:
        epis = scrapertools.find_single_match(title, '.*?Capitulo (.*?) ').strip()
        if not epis: epis = scrapertools.find_single_match(title, '.*?Capitulo (.*?)$').strip()

        epis = epis.replace('|', '').strip()

        if not epis: epis = '1'

        titulo = str(item.contentSeason) + 'x' + epis + ' ' + item.contentSerieName

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(episodes) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title = "Siguientes ...", action = "episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    if item.lang == 'Esp': lang = 'Esp'
    elif item.lang == 'Vose': lang = 'Vose'
    else: lang = 'Lat'

    data = do_downloadpage(item.url)

    ses = 0

    # ~ embeds
    matches = scrapertools.find_multiple_matches(data, 'data-title="Opción.*?data-src="(.*?)"')
    if not matches: matches = scrapertools.find_multiple_matches(data, '<iframe.*?data-src="(.*?)"')

    if not matches: matches = scrapertools.find_multiple_matches(data, 'data-title="Opción.*?src="(.*?)"')
    if not matches: matches = scrapertools.find_multiple_matches(data, '<iframe.*?src="(.*?)"')

    for url in matches:
        ses += 1

        url = url.strip()

        if '/likessb.' in url: continue

        if url.startswith('//'): url = 'https:' + url

        if 'api.mycdn.moe/uqlink.php?id=' in url: url = url.replace('api.mycdn.moe/uqlink.php?id=', 'uqload.com/embed-')

        elif 'api.mycdn.moe/dourl.php?id=' in url: url = url.replace('api.mycdn.moe/dourl.php?id=', 'dood.to/e/')

        elif 'api.mycdn.moe/dl/?uptobox=' in url: url = url.replace('api.mycdn.moe/dl/?uptobox=', 'uptobox.com/')

        elif url.startswith('http://vidmoly/'): url = url.replace('http://vidmoly/w/', 'https://vidmoly/embed-').replace('http://vidmoly/', 'https://vidmoly/')

        elif url.startswith('https://sr.ennovelas.net/'): url = url.replace('/sr.ennovelas.net/', '/waaw.to/')
        elif url.startswith('https://sr.ennovelas.watch/'): url = url.replace('/sr.ennovelas.watch/', '/waaw.to/')
        elif url.startswith('https://video.ennovelas.net/'): url = url.replace('/video.ennovelas.net/', '/waaw.to/')
        elif url.startswith('https://reproductor.telenovelas-turcas.com.es/'): url = url.replace('/reproductor.telenovelas-turcas.com.es/', '/waaw.to/')
        elif url.startswith('https://novelas360.cyou/player/'): url = url.replace('/novelas360.cyou/player/', '/waaw.to/')
        elif url.startswith('https://novelas360.cyou/'): url = url.replace('/novelas360.cyou/', '/waaw.to/')

        url = url.replace('&amp;', '&')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        other = ''

        if servidor == 'various': other = servertools.corregir_other(url)

        itemlist.append(Item( channel=item.channel, action = 'play', server = servidor, url = url, language = lang, other = other.capitalize() ))

    # ~ links

    data = do_downloadpage(item.url + '?do=watch')
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    values = scrapertools.find_multiple_matches(data, '<form method="post".*?action="(.*?)".*?<input type="hidden".*?name="(.*?)".*?value="(.*?)"')

    for link, type, value in values:
        ses += 1

        if not link: continue

        if type == 'watch': post = {'watch': str(value)}
        else: post = {'download': str(value)}

        data1 = do_downloadpage(link, post = post, headers = {'Referer': item.url} )

        matches = scrapertools.find_multiple_matches(data1, "<iframe.*?src='(.*?)'")
        if not matches: matches = scrapertools.find_multiple_matches(data1, '<iframe.*?src="(.*?)"')

        if not matches: matches = scrapertools.find_multiple_matches(data1, "<IFRAME.*?SRC='(.*?)'")
        if not matches: matches = scrapertools.find_multiple_matches(data1, '<IFRAME.*?SRC="(.*?)"')

        if not matches: matches = scrapertools.find_multiple_matches(data1, '<td>Server.*?href="(.*?)"')

        for url in matches:
            if '/wp-admin/' in url: continue

            if url.startswith('//'): url = 'https:' + url

            if 'api.mycdn.moe/uqlink.php?id=' in url: url = url.replace('api.mycdn.moe/uqlink.php?id=', 'uqload.com/embed-')

            elif 'api.mycdn.moe/dourl.php?id=' in url: url = url.replace('api.mycdn.moe/dourl.php?id=', 'dood.to/e/')

            elif 'api.mycdn.moe/dl/?uptobox=' in url: url = url.replace('api.mycdn.moe/dl/?uptobox=', 'uptobox.com/')

            elif url.startswith('http://vidmoly/'): url = url.replace('http://vidmoly/w/', 'https://vidmoly/embed-').replace('http://vidmoly/', 'https://vidmoly/')

            elif url.startswith('https://sr.ennovelas.net/'): url = url.replace('/sr.ennovelas.net/', '/waaw.to/')
            elif url.startswith('https://sr.ennovelas.watch/'): url = url.replace('/sr.ennovelas.watch/', '/waaw.to/')
            elif url.startswith('https://video.ennovelas.net/'): url = url.replace('/video.ennovelas.net/', '/waaw.to/')
            elif url.startswith('https://reproductor.telenovelas-turcas.com.es/'): url = url.replace('/reproductor.telenovelas-turcas.com.es/', '/waaw.to/')
            elif url.startswith('https://novelas360.cyou/player/'): url = url.replace('/novelas360.cyou/player/', '/waaw.to/')
            elif url.startswith('https://novelas360.cyou/'): url = url.replace('/novelas360.cyou/', '/waaw.to/')

            url = url.replace('&amp;', '&')

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            other = ''
            if servidor == 'various': other = servertools.corregir_other(url)

            if type == 'download':
                if other: other = other + ' D'
                else: other = 'D'

            itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = lang, other = other ))

    t_link = scrapertools.find_single_match(data, 'var vo_theme_dir = "(.*?)"')
    id_link = scrapertools.find_single_match(data, 'vo_postID = "(.*?)"')

    if t_link and id_link:
        i = 0

        while i <= 5:
           data2 = do_downloadpage(t_link + '/temp/ajax/iframe.php?id=' + id_link + '&video=' + str(i), headers = {'Referer': item.url, 'x-requested-with': 'XMLHttpRequest'} )

           data2 = data2.strip()

           if not data2: break

           ses += 1

           u_link = scrapertools.find_single_match(data2, '<iframe.*?src="(.*?)"')
           if not u_link: u_link = scrapertools.find_single_match(data2, '<IFRAME.*?SRC="(.*?)"')

           if u_link.startswith('//'): u_link = 'https:' + u_link

           if '/wp-admin/' in u_link: u_link = ''

           if u_link:
               if u_link.startswith('https://sr.ennovelas.net/'): u_link = u_link.replace('/sr.ennovelas.net/', '/waaw.to/')
               elif u_link.startswith('https://sr.ennovelas.watch/'): u_link = u_link.replace('/sr.ennovelas.watch/', '/waaw.to/')
               elif u_link.startswith('https://video.ennovelas.net/'): u_link = u_link.replace('/video.ennovelas.net/', '/waaw.to/')
               elif u_link.startswith('https://reproductor.telenovelas-turcas.com.es/'): u_link = u_link.replace('/reproductor.telenovelas-turcas.com.es/', '/waaw.to/')
               elif u_link.startswith('https://novelas360.cyou/player/'): u_link = u_link.replace('/novelas360.cyou/player/', '/waaw.to/')
               elif u_link.startswith('https://novelas360.cyou/'): u_link = u_link.replace('/novelas360.cyou/', '/waaw.to/')

               elif u_link.startswith('https://vk.com/'): u_link = u_link.replace('&amp;', '&')

               u_link = u_link.replace('&amp;', '&')

               servidor = servertools.get_server_from_url(u_link)
               servidor = servertools.corregir_servidor(servidor)

               u_link = servertools.normalize_url(servidor, u_link)

               other = ''
               if servidor == 'various': other = servertools.corregir_other(u_link)

               itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = u_link, server = servidor, language = lang, other = other ))

           i += 1

    # ~ Downloads
    data = do_downloadpage(item.url + '?do=downloads', headers = {'Referer': item.url, 'x-requested-with': 'XMLHttpRequest'})

    matches = scrapertools.find_multiple_matches(data, '<td>Server.*?href="(.*?)"')

    for url in matches:
        ses += 1

        if '/wp-admin/' in url: continue

        if url.startswith('//'): url = 'https:' + url

        if url.startswith('https://sr.ennovelas.net/'): url = url.replace('/sr.ennovelas.net/', '/waaw.to/')
        elif url.startswith('https://sr.ennovelas.watch/'): url = url.replace('/sr.ennovelas.watch/', '/waaw.to/')
        elif url.startswith('https://video.ennovelas.net/'): url = url.replace('/video.ennovelas.net/', '/waaw.to/')
        elif url.startswith('https://reproductor.telenovelas-turcas.com.es/'): url = url.replace('/reproductor.telenovelas-turcas.com.es/', '/waaw.to/')
        elif url.startswith('https://novelas360.cyou/player/'): url = url.replace('/novelas360.cyou/player/', '/waaw.to/')
        elif url.startswith('https://novelas360.cyou/'): url = url.replace('/novelas360.cyou/', '/waaw.to/')

        url = url.replace('&amp;', '&')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        other = ''
        if servidor == 'various': other = servertools.corregir_other(url)

        if other: other = other + ' d'
        else: other = 'd'


        itemlist.append(Item( channel = item.channel, action = 'play', title = '', url = url, server = servidor, language = lang, other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if url:
        url = url.replace('/Smoothpre.', '/smoothpre.')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        url = servertools.normalize_url(servidor, url)

        if 'filelions' in url or 'azipcdn' in url or 'alions' in url or 'dlions' in url or 'mlions' in url or 'fviplions' in url or 'javlion' in url or 'fdewsdc' in url or 'peytonepre' in url or 'ryderjet' in url:
            url += "|Referer=" + host

        elif 'vidhide' in url or 'stblion' in url or 'dhtpre' in url or 'dramacool' in url:
            url += "|Referer=" + host

        itemlist.append(item.clone( url=url, server=servidor ))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, '<article(.*?)</article>')

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="(.*?)"')

        title = scrapertools.find_single_match(article, ' title="(.*?)"')
        if not title: title = scrapertools.find_single_match(article, '<p class="entry-title">(.*?)</p>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(article, ' src="(.*?)"')

        name = scrapertools.find_single_match(article, ' alt="(.*?)"')

        SerieName = name

        if 'capitulos' in name: SerieName = name.split("capitulos")[0]
        if 'temporada' in name: SerieName = name.split("temporada")[0]

        SerieName = SerieName.strip()

        title = title.capitalize()

        if '-capitulo-' in url:
            epis = scrapertools.find_single_match(url, '-capitulo-(.*?)$')

            epis = epis.replace('/', '')

            if not epis: epis = 1

            title = title.replace('Capitulo', '[COLOR goldenrod]Epis.[/COLOR]').replace('capitulo', '[COLOR goldenrod]Epis.[/COLOR]')
            title = title.replace('Episodio', '[COLOR goldenrod]Epis.[/COLOR]').replace('episodio', '[COLOR goldenrod]Epis.[/COLOR]')

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, infoLabels={'year': '-'},
                                        contentSerieName = SerieName, contentType = 'episode', contentSeason = 1, contentEpisodeNumber = epis ))

        else:
            itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb, infoLabels={'year': '-'}, 
                                        contentSerieName = SerieName, contentType = 'tvshow' ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, 'class="page-numbers current".*?href="(.*?)"')

        if next_page:
            if '?s=' in next_page:
                itemlist.append(item.clone( title = "Siguientes ...", action = "list_search", url = next_page, text_color='coral' ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
       item.url = host + '?s=' + texto.replace(" ", "+")
       return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


