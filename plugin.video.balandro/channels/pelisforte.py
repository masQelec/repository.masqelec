# -*- coding: utf-8 -*-

import re, codecs

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, servertools


host = 'https://www2.pelisforte.se/'


# ~ por si viene de enlaces guardados
ant_hosts = ['https://pelisforte.co/', 'https://pelisforte.nu/','https://www1.pelisforte.se/' ]

domain = config.get_setting('dominio', 'pelisforte', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'pelisforte')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'pelisforte')
    else: host = domain


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_pelisforte_proxies', default=''):
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
    if config.get_setting('channel_pelisforte_proxies', default=''): hay_proxies = True

    if '/release/' in url: raise_weberror = False

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('pelisforte', url, post=post, headers=headers, raise_weberror=raise_weberror).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

        if not data:
            if not '?s=' in url:
                if config.get_setting('channels_re_charges', default=True): platformtools.dialog_notification('PelisForte', '[COLOR cyan]Re-Intentanto acceso[/COLOR]')

                timeout = config.get_setting('channels_repeat', default=30)

                if hay_proxies:
                    data = httptools.downloadpage_proxy('pelisforte', url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
                else:
                    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    if '<title>You are being redirected...</title>' in data or '<title>Just a moment...</title>' in data:
        if not url.startswith(host):
            data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('pelisforte', url, post=post, headers=headers, raise_weberror=raise_weberror).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    if '<title>Just a moment...</title>' in data:
        if not '?s=' in url:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
        return ''

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'pelisforte', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(Item( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(Item( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_pelisforte', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='pelisforte', folder=False, text_color='chartreuse' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_pelisforte', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(Item( channel='helper', action='show_help_pelisforte', title='[COLOR aquamarine][B]Aviso[/COLOR] [COLOR green]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('pelisforte') ))

    itemlist.append(Item( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'pelisforte', thumbnail=config.get_thumb('pelisforte') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'todas-las-peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Marvel', action = 'list_all', url = host + 'sg/marvel-mcu/', search_type = 'movie', text_color='moccasin' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', search_type = 'movie' ))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Castellano', action = 'list_all', url = host + 'pelis/idiomas/castellano/', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'Latino', action = 'list_all', url = host + 'pelis/idiomas/espanol-latino/', text_color='moccasin' ))
    itemlist.append(item.clone( title = 'Subtitulado', action = 'list_all', url = host + 'pelis/idiomas/subtituladas/', text_color='moccasin' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host + 'portal003/')

    bloque = scrapertools.find_single_match(data, '>Géneros<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="(.*?)">(.*?)</a>')
    if not matches: matches = scrapertools.find_multiple_matches(bloque, '<a href=(.*?)>(.*?)</a>')

    for url, title in matches:
        itemlist.append(item.clone( action='list_all', title=title, url=url, text_color = 'deepskyblue' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    url = host + 'release/'

    for x in range(current_year, 1939, -1):
         itemlist.append(item.clone( title=str(x), url = url + str(x), action='list_all', text_color = 'deepskyblue' ))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    url_letra = host + 'letter/'

    for letra in '#ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if letra == '#': url = url_letra + '0-9/'
        else: url = url_letra + letra + '/'

        itemlist.append(item.clone( title = letra, action = 'list_all', url = url, text_color = 'deepskyblue' ))

    return itemlist


def list_all(item): 
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h1(.*?)<p class="copy">© PelisForte')

    matches = scrapertools.find_multiple_matches(bloque, '<article(.*?)</article>')

    for match in matches:
        url = scrapertools.find_single_match(match, '<a href="(.*?)"')
        if not url: url = scrapertools.find_single_match(match, 'href=(.*?) ').strip()

        title = scrapertools.find_single_match(match, 'class="entry-title">(.*?)</')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        year = scrapertools.find_single_match(match, '<span class="Year">(.*?)</span>')
        if not year:
            if '/release/' in item.url: year = scrapertools.find_single_match(item.url, "/release/(.*?)$")
            else: year ='-'

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '>SIGUIENTE' in data:
            next_page = scrapertools.find_single_match(data, 'class="page-link current".*?class="page-link".*?</a>.*?' + "href='(.*?)'.*?</section>")
            if not next_page: next_page = scrapertools.find_single_match(data, 'class="page-link current".*?class="page-link".*?</a>.*?href="(.*?)".*?</section>')

            if not next_page: next_page = scrapertools.find_single_match(data, 'class="page-link current".*?</a>.*?class=page-link.*?href=(.*?)>.*?</section>')

            if next_page:
                next_page = next_page.replace('&#038;', '&')

                if '/page/' in next_page:
                    itemlist.append(item.clone (url = next_page, title = 'Siguientes ...', action = 'list_all', text_color='coral'))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>OPCIONES<(.*?)</section>')

    matches = scrapertools.find_multiple_matches(bloque, 'href="#options-(.*?)">.*?<span class="server">(.*?)-(.*?)</span>')
    if not matches: matches = scrapertools.find_multiple_matches(bloque, 'href=#options-(.*?)>.*?<spanclass=server>(.*?)-(.*?)</span>')

    ses = 0

    for opt, srv, idioma in matches:
        ses += 1

        srv = srv.lower().strip()

        if not srv: continue
        elif srv == 'trailer': continue

        if '+ veloz' in srv: continue
        elif 'sdav' in srv: continue
        elif 'guayhd' in srv: continue

        idioma = idioma.strip()

        if 'Latino' in idioma: lang = 'Lat'
        elif 'Castellano' in idioma: lang = 'Esp'
        elif 'Subtitulado' in idioma: lang = 'Vose'
        else: lang = idioma

        url = scrapertools.find_single_match(data, '<div id="options-' + opt + '".*?src="([^"]+)"')
        if not url: url = scrapertools.find_single_match(data, '<divid=options-' + opt + '.*?data-src="(.*?)"')

        if url:
            servidor = servertools.corregir_servidor(srv)

            ref = ''
            other = ''

            if srv == 'pf': continue
            elif srv == 'w1tv': continue

            elif srv == 'ok':
                servidor = 'directo'
                srv = 'ok'
            elif srv == 'okhd':
                servidor = 'directo'
                srv = 'tiwi'
                ref = item.url

            elif srv == 'playpf': servidor = 'directo'
            elif srv == 'ds': servidor = 'directo'

            if servidor == 'directo': other = srv

            elif servidor == 'various': other = servertools.corregir_other(srv)

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, ref = ref,
                            language = lang, other = other.capitalize()))

    # ~ descargas recaptcha

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'pelisforte', default='')

    if domain_memo: host_player = domain_memo
    else: host_player = host

    item.url = item.url.replace('&amp;#038;', '&').replace('&#038;', '&').replace('&amp;', '&')

    url = item.url

    if item.other:
        if '/mp4.nu/' in url:
            new_url = url.replace('/mp4.nu//?h=', '/mp4.nu/r.php?h=').replace('/mp4.nu/', '/mp4.nu/r.php')

            if not new_url.startswith(host_player):
                resp = httptools.downloadpage(new_url, headers={'Referer': host_player}, follow_redirects=False, only_headers=True)
            else:
                if config.get_setting('channel_pelisforte_proxies', default=''):
                    resp = httptools.downloadpage_proxy('pelisforte', new_url, headers={'Referer': host_player}, follow_redirects=False, only_headers=True)
                else:
                    resp = httptools.downloadpage(new_url, headers={'Referer': host_player}, follow_redirects=False, only_headers=True)

            if 'location' in resp.headers: url = resp.headers['location']
            else: url = ''

            if url:
                if '/rehd.net/' in url:
                    data = do_downloadpage(url)
                    url = scrapertools.find_single_match(data, '"url": "(.*?)"')

                if 'gounlimited' in url:
                    return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'
                elif '/guayhd.me/' in url:
                    return 'Servidor [COLOR plum]No Soportado[/COLOR]'
                elif '/playpf.link/' in url:
                    return 'Servidor [COLOR plum]No Soportado[/COLOR]'

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                if item.ref:
                    if not "vgfplay" in url and not "listeamed":
                        if not '/ok.ru/' in url: url += "|Referer=" + url
                    else:
                        url += "|Referer=https://mp4.nu/"
                else:
                    if 'streamwish' in url or 'strwish' in url or 'embedwish' in url or 'wishembed' in url or 'awish' in url or 'dwish' in url or 'mwish' in url or 'wishfast' in url or 'sfastwish' in url or 'doodporn' in url or 'flaswish' in url or 'obeywish' in url or 'cdnwish' in url or 'asnwish' in url or 'flastwish' in url or 'jodwish' in url or 'swhoi' in url or 'fsdcmo' in url or 'swdyu' in url or 'wishonly' in url or 'playerwish' in url or 'hlswish' in url or 'wish' in url or 'iplayerhls' in url or 'hlsflast' in url or 'ghbrisk' in url:
                        url += "|Referer=https://mp4.nu/"

                    else:
                       if not "vgfplay" in url and not "listeamed" in url:
                           if not '/ok.ru/' in url: url += "|Referer=" + url
                       else:
                           url += "|Referer=https://mp4.nu/"

                itemlist.append(item.clone(server = servidor, url = url))
                return itemlist

        headers = {'Referer': host_player}
        data = do_downloadpage(url, headers = headers)

        url = scrapertools.find_single_match(data, '<div class="Video">.*?src="(.*?)"')
        if not url: url = scrapertools.find_single_match(data, '<IFRAME SRC="(.*?)"')
        if not url: url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')
        if not url: url = scrapertools.find_single_match(data, 'src=(.*?) ').strip()

        if 'trhide' in url:
            try:
               new_url = scrapertools.find_single_match(url, 'tid=([A-z0-9]+)')[::-1]
               new_url = codecs.decode(new_url, 'hex')

               headers = {'Referer': item.url}
               data = do_downloadpage(new_url, headers = headers)

               if 'grecaptcha.execute' in data:
                   return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

               url = new_url
            except:
               pass

        elif url.startswith(host_player):
            if url.endswith('&'):
                url = url + '='
                url = url.replace('&=', '')

            headers = {'Referer': item.url}
            data = do_downloadpage(url, headers = headers)

            url = scrapertools.find_single_match(data, '<div class="Video">.*?src="(.*?)"')
            if not url: url = scrapertools.find_single_match(data, '<IFRAME SRC="(.*?)"')

    if url:
        if 'gounlimited' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        if item.ref:
            if not "vgfplay" in url and not "listeamed" in url:
                if not '/ok.ru/' in url: url += "|Referer=" + url
            else:
                url += "|Referer=https://mp4.nu/"
        else:
            if 'streamwish' in url or 'strwish' in url or 'embedwish' in url or 'wishembed' in url or 'awish' in url or 'dwish' in url or 'mwish' in url or 'wishfast' in url or 'sfastwish' in url or 'doodporn' in url or 'flaswish' in url or 'obeywish' in url or 'cdnwish' in url or 'asnwish' in url or 'flastwish' in url or 'jodwish' in url or 'swhoi' in url or 'fsdcmo' in url or 'swdyu' in url or 'wishonly' in url or 'playerwish' in url or 'hlswish' in url or 'wish' in url or 'iplayerhls' in url or 'hlsflast' in url or 'ghbrisk' in url:
                url += "|Referer=https://mp4.nu/"

            else:
              if not "vgfplay" in url and not "listeamed" in url:
                  if not '/ok.ru/' in url: url += "|Referer=" + url
              else:
                  url += "|Referer=https://mp4.nu/"

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
