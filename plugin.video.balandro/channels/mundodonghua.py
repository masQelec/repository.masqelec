# -*- coding: utf-8 -*-

import re, base64

from lib import jsunpack

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.mundodonghua.com/'


perpage = 30


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_mundodonghua_proxies', default=''):
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
    if config.get_setting('channel_mundodonghua_proxies', default=''): hay_proxies = True

    timeout = None
    if host in url:
        if hay_proxies: timeout = config.get_setting('channels_repeat', default=30)

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('mundodonghua', url, post=post, headers=headers, timeout=timeout).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

        if not data:
            if not '/busquedas/' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('MundoDonghua', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('mundodonghua', url, post=post, headers=headers, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, timeout=timeout).data

    if '<title>You are being redirected...</title>' in data or '<title>Just a moment...</title>' in data:
        if not '/busquedas/' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( channel='submnuctext', action='_test_webs', title='Test Web del canal [COLOR yellow][B] ' + host + '[/B][/COLOR]',
                                from_channel='mundodonghua', folder=False, text_color='chartreuse' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_mundodonghua', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('zonaleros') ))

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

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'lista-donghuas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_all', url = host + 'lista-episodios', group = 'last_epis', search_type = 'tvshow', text_color = 'cyan' ))

    itemlist.append(item.clone( title = 'En emision', action = 'list_all', url = host + 'lista-donghuas-emision', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'lista-donghuas-finalizados', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos',  search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'lista-donghuas')
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>', '', data)

    bloque = scrapertools.find_single_match(data, '</i> Generos<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?"><.*?>(.*?)</span>')

    for url, title in matches:
        if not host in url: url = host[:-1] + url

        itemlist.append(item.clone( title = title, action = 'list_all', url = url, text_color='springgreen' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>', '', data)

    bloque = scrapertools.find_single_match(data,'> Lista de(.*?)</center>')
    if not bloque: bloque = scrapertools.find_single_match(data,'> Resultados de la busqueda(.*?)<center>')

    matches = scrapertools.find_multiple_matches(bloque, '<div class="item col-lg-2 col-md-2 col-xs-4">(.*?)</div></div></div>')
    if not matches:  matches = scrapertools.find_multiple_matches(bloque, '<div class="item col-lg-3 col-md-3 col-xs-4">(.*?)</div></a></div>')

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        title = scrapertools.find_single_match(match, '<h5 class="sf fc-dark f-bold fs-14">(.*?)</h5>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        if not host in thumb: thumb = host[:-1] + thumb

        if not host in url: url = host[:-1] + url

        SerieName = corregir_SerieName(title)

        if item.group == 'last_epis':
            epis = scrapertools.find_single_match(match,'Episodio (.*?)$').strip()
            if '</h5>' in epis: epis = scrapertools.find_single_match(epis,'(.*?)</h5>').strip()

            if not epis: epis = 1

            titulo = '[COLOR goldenrod]Epis. [/COLOR]' + str(epis) + ' ' + title.replace('Episodio', '').strip()

            itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, thumbnail = thumb, infoLabels={'year': '-'},
                                        contentSerieName = SerieName, contentType = 'episode', contentSeason = 1, contentEpisodeNumber = epis))

        else:
            if '>Película<' in match or 'Movie' in match:
                PeliName = SerieName
                itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb,
                                            contentType = 'movie', contentTitle = PeliName, infoLabels={'year': '-'} ))
            else:
                itemlist.append(item.clone( action = 'episodios', url = url, title = title, thumbnail = thumb,
                                            contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        buscar_next = True

        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='Siguientes ...', page=item.page + 1, action='list_all', text_color='coral' ))
                buscar_next = False

        if buscar_next:
            next_page = scrapertools.find_single_match(data,'<ul class="pagination">.*?<li class="active">.*?<li>.*?<a href="(.*?)"')

            if next_page:
                if not host in next_page: next_page = host[:-1] + next_page

                itemlist.append(item.clone( title = 'Siguientes ...', action = 'list_all', url = next_page, text_color = 'coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>', '', data)

    bloque = scrapertools.find_single_match(data, '> Lista de Episodios<(.*?)</div></div>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)".*?<img src="(.*?)".*?<blockquote class="message sf fc-dark f-bold fs-16">(.*?)</blockquote>')

    if not matches:
        url = scrapertools.find_single_match(bloque, '<a href="(.*?)"')

        if url:
            if not host in url: url = host[:-1] + url

            itemlist.append(item.clone( action='findvideos', url = url, title = item.title, contentType = 'movie', contentTitle = item.contentSerieName ))

        return itemlist

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('MundoDonghua', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('MundoDonghua', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MundoDonghua', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MundoDonghua', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MundoDonghua', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('MundoDonghua', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('MundoDonghua', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for url, thumb, title in matches[item.page * item.perpage:]:
        if not host in url: url = host[:-1] + url

        if not host in thumb: thumb = host[:-1] + thumb

        title = title.strip()

        epis = scrapertools.find_single_match(title, '.*?-(.*?)$').strip()

        if item.contentSerieName: titulo = '1x' + str(epis) + ' ' + title.replace(' - ' + str(epis), '').strip()
        else: titulo = item.title

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, contentType = 'episode', contentSeason = 1, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    if itemlist:
        if len(epis) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

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

    ses = 0

    matches = scrapertools.find_multiple_matches(data, "(eval.*?)\n")

    if len(matches) > 1:
        for match in matches:
            ses += 1

            ref = ''

            unpack = jsunpack.unpack(match)


            url = scrapertools.find_single_match(unpack, 'file(?:"|):"([^"]+)')

            if not url:
                unpack = unpack.replace('\\/', '/')
                unpack = unpack.replace('=\\', '=').replace('\\"', '/"')
                unpack = unpack.replace('=/', '=').replace('\/"', '"')

                url = scrapertools.find_single_match(unpack, '<iframe src="(.*=)"')

            if not url:
                slug = scrapertools.find_single_match(unpack, '"slug":"(.*?)"')

                if slug:
                    ref = item.url
                    url =  host + 'api_donghua.php?slug=' + slug

            if ' width=' in url: url = scrapertools.find_single_match(url, '(.*?)"')

            if url:
                if not url.startswith('http'): url = 'https:' + url

                if '/api_donghua.php?' in url: continue

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                other = ''
                if servidor == 'various': other = servertools.corregir_other(url)

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, ref = ref, language = 'Vose', other = other ))

    else:
        unpack = jsunpack.unpack(matches[0])

        matches = scrapertools.find_multiple_matches(unpack, '"slug":"([^"]+)')

        if matches:
            for match in matches:
                ses += 1

                url =  host + 'api_donghua.php?slug=' + match

                data1 = do_downloadpage(url, headers={'Referer': item.url})

                try:
                   if data1.get('url', ''): url = 'https://www.dailymotion.com/video/' + base64.b64decode(data1['url']).decode('utf-8')
                   elif data1.get('source', ''): url = data1['source'][0].get('file', '')
                except:
                   url = scrapertools.find_single_match(str(data1), '"url":.*?"(.*?)"')
                   fil = scrapertools.find_single_match(str(data1), '"file":.*?"(.*?)"')

                   if not url and not fil: continue

                   if url:
                       url = base64.b64decode(url).decode('utf-8')
                       url = 'https://www.dailymotion.com/video/' + url
                   else:
                       url = fil

                if url:
                    if not url.startswith('http'): url = 'https:' + url

                    ref = ''
                    if 'api_donghua.php?slug=' in url: ref = item.url

                    servidor = servertools.get_server_from_url(url)
                    servidor = servertools.corregir_servidor(servidor)

                    url = servertools.normalize_url(servidor, url)

                    other = ''
                    if servidor == 'various': other = servertools.corregir_other(url)

                    if '/redirector.php?' in url: servidor = ''

                    itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, ref = ref, language = 'Vose', other = other ))

        else:
            url = scrapertools.find_single_match(unpack, 'file(?:"|):"([^"]+)')
            if not url: url = scrapertools.find_single_match(unpack, '<iframe src="(.*=)"')

            if url:
                if not url.startswith('http'): url = 'https:' + url

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                url = servertools.normalize_url(servidor, url)

                other = ''
                if servidor == 'various': other = servertools.corregir_other(url)

                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = 'Vose', other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.server == 'directo':
        if item.ref: data = do_downloadpage(url, headers={'Referer': item.ref})
        else: data = do_downloadpage(url)

        if not data: return itemlist

        if '404 Not Found' in data: return itemlist

        vid = scrapertools.find_single_match(data, '"url":"(.*?)"')

        if vid:
            try: vid = base64.b64decode(vid).decode('utf-8')
            except: vid = ''

            if vid: url = 'https://www.dailymotion.com/video/' + vid

    if url:
        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        if '/nemonicplayer/' in url: servidor = 'directo'

        if servidor == 'zplayer': url = url + '|' + host

        itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if 'Episodio ' in SerieName: SerieName = SerieName.split("Episodio ")[0]
    if 'Capítulo' in SerieName: SerieName = SerieName.split("Capítulo")[0]
    if 'Capitulo' in SerieName: SerieName = SerieName.split("Capitulo")[0]

    if 'Movie' in SerieName: SerieName = SerieName.split("Movie")[0]

    if 'Season' in SerieName: SerieName = SerieName.split("Season")[0]
    if 'season' in SerieName: SerieName = SerieName.split("season")[0]

    if 'OVA' in SerieName: SerieName = SerieName.split("OVA")[0]

    if ' S1 ' in SerieName: SerieName = SerieName.split(" S1 ")[0]
    elif ' S2 ' in SerieName: SerieName = SerieName.split(" S2 ")[0]
    elif ' S3 ' in SerieName: SerieName = SerieName.split(" S3 ")[0]
    elif ' S4 ' in SerieName: SerieName = SerieName.split(" S4 ")[0]
    elif ' S5 ' in SerieName: SerieName = SerieName.split(" S5 ")[0]
    elif ' S6 ' in SerieName: SerieName = SerieName.split(" S6 ")[0]
    elif ' S7 ' in SerieName: SerieName = SerieName.split(" S7 ")[0]
    elif ' S8 ' in SerieName: SerieName = SerieName.split(" S8 ")[0]
    elif ' S9 ' in SerieName: SerieName = SerieName.split(" S9 ")[0]

    if ' T1 ' in SerieName: SerieName = SerieName.split(" T1 ")[0]
    elif ' T2 ' in SerieName: SerieName = SerieName.split(" T2 ")[0]
    elif ' T3 ' in SerieName: SerieName = SerieName.split(" T3 ")[0]
    elif ' T4 ' in SerieName: SerieName = SerieName.split(" T4 ")[0]
    elif ' T5 ' in SerieName: SerieName = SerieName.split(" T5 ")[0]
    elif ' T6 ' in SerieName: SerieName = SerieName.split(" T6 ")[0]
    elif ' T7 ' in SerieName: SerieName = SerieName.split(" T7 ")[0]
    elif ' T8 ' in SerieName: SerieName = SerieName.split(" T8 ")[0]
    elif ' T9 ' in SerieName: SerieName = SerieName.split(" T9 ")[0]

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
        item.url =  host + "busquedas/" + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
