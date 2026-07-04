# -*- coding: utf-8 -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True


import re, os, string, time, hashlib

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb

from lib import decrypters


host = 'https://4144-don.mirror.pm/'


# ~ 3/6/26 last domain  'https://dontorrent.review/'

# ~ Web Search
web_search_dontorrent = 'https://dontorrent.review/'


# ~ Alternative Webs Clons
web_clon = False

alt_web_clons = ['https://divxatope.net/',
                 'https://elitedivx.net/',
                 'https://www21.dontorrent.link/',
                 'https://mejortorrent.in/',
                 'https://reinventorrent.org/',
                 'https://todotorrents.org/'] 

# ~ Alternative Webs Findvideos
alt_find_divxatope = 'https://divxatope.net/'
alt_find_elitedivx = 'https://elitedivx.net/'
alt_find_dontorrent21 = 'https://www21.dontorrent.link/'
alt_find_mejortorrentin = 'https://mejortorrent.in/'
alt_find_reinventorrent = 'https://reinventorrent.org/'
alt_find_todotorrents = 'https://todotorrents.org/'


try:
    data_tor_proxy = httptools.downloadpage('https://donproxies.com/').data
except:
    data_tor_proxy = ''
    tor_proxy = ''

if data_tor_proxy:
    tor_proxy = scrapertools.find_single_match(data_tor_proxy, 'Pulse el boton inferior para que se le genere un proxy.*?<a href="(.*?)".*?>Ingresar al Proxy Generado<')
    if tor_proxy:
        if not tor_proxy.endswith('/'): tor_proxy = tor_proxy + '/'

        if not host == tor_proxy: host = tor_proxy


# ~ por si viene de enlaces guardados
ant_hosts =  [
             # ~ 2021
             'https://dontorrents.org/', 'https://dontorrents.net/', 'https://dontorrent.one/',
             'https://dontorrent.app/', 'https://dontorrent.lol/', 'https://dontorrent.nz/',
             'https://dontorrent.rip/', 'https://dontorrent.vip/', 'https://dontorrent.ws/',
             'https://dontorrent.win/', 'https://dontorrent.rs/', 'https://dontorrent.bz/',
             'https://dontorrent.men/', 'https://dontorrent.fit/', 'https://dontorrent.art/',
             'https://dontorrent.fun/', 'https://dontorrent.se/', 'https://dontorrent.pw/',
             # ~ 2022
             'https://dontorrent.li/', 'https://dontorrent.it/', 'https://dontorrent.red/',
             'https://dontorrent.nu/', 'https://dontorrent.si/', 'https://dontorrent.sk/',
             'https://dontorrent.eu/', 'https://dontorrent.top/', 'https://dontorrent.pm/',
             'https://dontorrent.re/', 'https://dontorrent.wf/', 'https://dontorrent.run/',
             'https://dontorrent.cat/', 'https://dontorrent.pl/', 'https://dontorrent.tel/',
             'https://dontorrent.nl/', 'https://dontorrent.cx/', 'https://dontorrent.bet/',
             'https://dontorrent.cab/', 'https://dontorrent.wtf/', 'https://dontorrent.fi/',
             'https://dontorrent.ink/', 'https://dontorrent.kim/', 'https://dontorrent.tw/',
             'https://dontorrent.yt/', 'https://dontorrent.vg/', 'https://dontorrent.ch/',
             'https://dontorrent.vet/', 'https://dontorrent.dog/', 'https://dontorrent.dev/',
             'https://dontorrent.bid/', 'https://dontorrent.pet/', 'https://dontorrent.soy/',
             'https://dontorrent.moe/', 'https://dontorrent.pub/', 'https://dontorrent.tf/',
             'https://dontorrent.vin/', 'https://dontorrent.ist/', 'https://dontorrent.uno/',
             'https://dontorrent.fans/', 'https://dontorrent.ltd/', 'https://dontorrent.me/',
             'https://dontorrent.gs/', 'https://dontorrent.gy/', 'https://dontorrent.click/',
             'https://dontorrent.fail/', 'https://dontorrent.futbol/', 'https://dontorrent.mba/',
             # ~ 2023
             'https://dontorrent.army/', 'https://dontorrent.blue/', 'https://dontorrent.beer/',
             'https://dontorrent.surf/', 'https://dontorrent.how/', 'https://dontorrent.casa/',
             'https://dontorrent.chat/', 'https://dontorrent.plus/', 'https://dontorrent.ninja/',
             'https://dontorrent.love/', 'https://dontorrent.cloud/', 'https://dontorrent.africa/',
             'https://dontorrent.pictures/', 'https://dontorrent.ms/', 'https://dontorrent.care/',
             'https://dontorrent.cash/', 'https://dontorrent.observer/', 'https://dontorrent.company/',
             'https://dontorrent.discount/', 'https://dontorrent.dad/', 'https://dontorrent.zip/',
             'https://dontorrent.mov/', 'https://dontorrent.day/', 'https://dontorrent.boo/',
             'https://dontorrent.foo/', 'https://dontorrent.hair/', 'https://dontorrent.rsvp/',
             'https://dontorrent.quest/', 'https://dontorrent.nexus/', 'https://dontorrent.bond/',
             'https://dontorrent.tokyo/', 'https://dontorrent.boston/', 'https://dontorrent.rodeo/',
             'https://dontorrent.durban/', 'https://dontorrent.party/', 'https://dontorrent.joburg/',
             'https://dontorrent.wales/', 'https://dontorrent.nagoya/', 'https://dontorrent.contact/',
             # ~ 2024
             'https://dontorrent.cymru/', 'https://dontorrent.capetown/', 'https://dontorrent.yokohama/',
             'https://dontorrent.makeup/', 'https://dontorrent.band/', 'https://dontorrent.center/',
             'https://dontorrent.cooking/', 'https://dontorrent.cyou/', 'https://dontorrent.agency/',
             'https://dontorrent.skin/', 'https://dontorrent.directory/', 'https://dontorrent.boutique/',
             'https://dontorrent.miami/', 'https://dontorrent.business/', 'https://dontorrent.clothing/',
             'https://dontorrent.icu/', 'https://dontorrent.fyi/', 'https://dontorrent.sbs/',
             'https://dontorrent.cc/', 'https://dontorrent.esq/', 'https://dontorrent.city/',
             'https://dontorrent.cologne/', 'https://dontorrent.dance/', 'https://dontorrent.cricket/',
             'https://dontorrent.earth/', 'https://dontorrent.date/', 'https://dontorrent.email/',
             'https://dontorrent.education/', 'https://dontorrent.exposed/', 'https://dontorrent.faith/',
             'https://dontorrent.gratis/', 'https://dontorrent.equipment/', 'https://dontorrent.fashion/',
             'https://dontorrent.gallery/', 'https://dontorrent.yoga/', 'https://dontorrent.foundation/',
             # ~ 2025
             'https://dontorrent.co/', 'https://dontorrent.auction/', 'https://dontorrent.football/',
             'https://dontorrent.wiki/', 'https://dontorrent.games/', 'https://dontorrent.tube/',
             'https://dontorrent.trade/', 'https://dontorrent.webcam/', 'https://dontorrent.schule/',
             'https://dontorrent.stream/', 'https://dontorrent.website/', 'https://dontorrent.group/',
             'https://dontorrent.download/', 'https://dontorrent.gift/', 'https://dontorrent.report/',
             'https://dontorrent.homes/', 'https://dontorrent.haus/', 'https://dontorrent.news/',
             'https://dontorrent.institute/', 'https://dontorrent.jetzt/', 'https://dontorrent.loan/',
             'https://dontorrent.graphics/', 'https://dontorrent.international/', 'https://dontorrent.irish/',
             'https://dontorrent.lighting/', 'https://dontorrent.istanbul/', 'https://dontorrent.onl/',
             'https://dontorrent.kids/', 'https://dontorrent.kiwi/', 'https://dontorrent.live/',
             'https://dontorrent.phd/', 'https://dontorrent.gripe/', 'https://dontorrent.sarl/',
             'https://dontorrent.club/',
             # ~ 2026
             'https://dontorrent.prof/', 'https://dontorrent.info/', 'https://dontorrent.promo/',
             'https://dontorrent.photos/', 'https://dontorrent.cfd/', 'https://dontorrent.pink/',
             'https://dontorrent.reisen/', 'https://dontorrent.racing/', 'https://dontorrent.rocks/',
             'https://dontorrent.science/', 'https://dontorrent.support/']


domain = config.get_setting('dominio', 'dontorrents', default='')

if domain:
    if domain == host: config.set_setting('dominio', '', 'dontorrents')
    elif domain in str(ant_hosts): config.set_setting('dominio', '', 'dontorrents')
    else: host = domain


def item_configurar_proxies(item):
    color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

    color_avis = config.get_setting('notification_avis_color', default='yellow')
    color_exec = config.get_setting('notification_exec_color', default='cyan')

    context = []

    tit = '[COLOR %s]Información proxies[/COLOR]' % color_avis
    context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

    if config.get_setting('channel_dontorrents_proxies', default=''):
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
    global web_clon

    # ~ por si viene de enlaces guardados
    for ant in ant_hosts:
        url = url.replace(ant, host)

    hay_proxies = False
    if config.get_setting('channel_dontorrents_proxies', default=''): hay_proxies = True

    if not url.startswith(host):
        data = httptools.downloadpage(url, post=post, headers=headers).data
    else:
        if hay_proxies:
            data = httptools.downloadpage_proxy('dontorrents', url, post=post, headers=headers).data
        else:
            data = httptools.downloadpage(url, post=post, headers=headers).data

    if not '/buscar/' in url:
        if '<title>Just a moment...</title>' in data:
            platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]CloudFlare[COLOR orangered] Protection[/B][/COLOR]')
            return ''

        elif 'Asegurándonos de que no eres un robot' in data:
            for alt_web_clon in alt_web_clons:
                if hay_proxies:
                    data = httptools.downloadpage_proxy('dontorrents', alt_web_clon).data
                else:
                    data = httptools.downloadpage(alt_web_clon).data

                if 'Asegurándonos de que no eres un robot' in data:
                     platformtools.dialog_notification(config.__addon_name, '[COLOR red][B]Boot[COLOR orangered] Protection [COLOR plum]Robots[/B][/COLOR]')
                     continue

                if tor_proxy:
                    if config.get_setting('developer_team'):
                        if not web_clon:
                            platformtools.dialog_notification(config.__addon_name + ' [COLOR palegreen][B]Acceso con el Clon[/COLOR][/B]', '[B][COLOR cyan]' + alt_web_clon + '[/COLOR][/B]')

                    web_clon = True

                    url = url.replace(tor_proxy, alt_web_clon)

                    if not alt_web_clon in url: url = url.replace(web_search_dontorrent, alt_web_clon)

                    data = alt_do_downloadpage(url, post=None, headers=None)
                    break
                else:
                    platformtools.dialog_ok(config.__addon_name + ' - Dontorrents', '[COLOR red][B]Boot[/COLOR][COLOR orangered] Protection [/COLOR][COLOR plum]Robots[/B][/COLOR]', '[B][COLOR cyan]Acceda con su Canal Clon[/COLOR][/B]', '[B][COLOR yellow]' + alt_web_clon + '[/COLOR][/B]')
                    return ''

    return data


def alt_do_downloadpage(url, post=None, headers=None):
    if alt_find_divxatope in url:
        hay_proxies = False
        if config.get_setting('channel_divxatope_proxies', default=''): hay_proxies = True

        if not url.startswith(alt_find_divxatope):
            data = httptools.downloadpage(url, post=post, headers=headers).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('divxatope', url, post=post, headers=headers).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers).data

    elif alt_find_elitedivx in url:
        hay_proxies = False
        if config.get_setting('channel_elitedivx_proxies', default=''): hay_proxies = True

        if not url.startswith(alt_find_elitedivx):
            data = httptools.downloadpage(url, post=post, headers=headers).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('elitedivx', url, post=post, headers=headers).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers).data

    elif alt_find_dontorrent21 in url:
        hay_proxies = False
        if config.get_setting('channel_dontorrent21_proxies', default=''): hay_proxies = True

        if not url.startswith(alt_find_divxatope):
            data = httptools.downloadpage(url, post=post, headers=headers).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('dontorrent21', url, post=post, headers=headers).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers).data

    elif alt_find_mejortorrentin in url:
        hay_proxies = False
        if config.get_setting('channel_mejortorrenin_proxies', default=''): hay_proxies = True

        if not url.startswith(alt_find_mejortorrentin):
            data = httptools.downloadpage(url, post=post, headers=headers).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('mejortorrentin', url, post=post, headers=headers).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers).data

    elif alt_find_reinventorrent in url:
        hay_proxies = False
        if config.get_setting('channel_reinventorrent_proxies', default=''): hay_proxies = True

        if not url.startswith(alt_find_reinventorrent):
            data = httptools.downloadpage(url, post=post, headers=headers).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('reinventorrent', url, post=post, headers=headers).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers).data

    else:
        hay_proxies = False
        if config.get_setting('channel_todotorrents_proxies', default=''): hay_proxies = True

        if not url.startswith(alt_find_todotorrents):
            data = httptools.downloadpage(url, post=post, headers=headers).data
        else:
            if hay_proxies:
                data = httptools.downloadpage_proxy('todotorrents', url, post=post, headers=headers).data
            else:
                data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def acciones(item):
    logger.info()
    itemlist = []

    domain_memo = config.get_setting('dominio', 'dontorrents', default='')

    if domain_memo: url = domain_memo
    else: url = host

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title='[COLOR moccasin][B]Últimos Cambios de Dominios[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(item.clone( channel='helper', action='show_help_domains', title='[B]Información Dominios[/B]', thumbnail=config.get_thumb('help'), text_color='green' ))

    itemlist.append(item.clone( channel='domains', action='test_domain_dontorrents', title='Test Web del canal [COLOR yellow][B] ' + url + '[/B][/COLOR]',
                                from_channel='dontorrents', folder=False, text_color='chartreuse' ))

    itemlist.append(item.clone( channel='domains', action='operative_domains_dontorrents', title='Comprobar [B]Dominio Operativo Vigente' + '[COLOR dodgerblue] t.me/s/DonTorrent[/B][/COLOR]',
                          desde_el_canal = True, thumbnail=config.get_thumb('dontorrents'), text_color='mediumaquamarine' ))

    itemlist.append(item.clone( channel='domains', action='last_domain_dontorrents', title='[B]Comprobar último dominio vigente[/B]',
                          desde_el_canal = True, host_canal = url, thumbnail=config.get_thumb('dontorrents'), text_color='chocolate' ))

    if domain_memo: title = '[B]Modificar/Eliminar el dominio memorizado[/B]'
    else: title = '[B]Informar Nuevo Dominio manualmente[/B]'

    itemlist.append(item.clone( channel='domains', action='manto_domain_dontorrents', title=title, desde_el_canal = True, folder=False, text_color='darkorange' ))

    itemlist.append(item_configurar_proxies(item))

    itemlist.append(item.clone( channel='helper', action='show_help_prales', title='[B]Cuales son sus Clones[/B]', thumbnail=config.get_thumb('dontorrents'), text_color='turquoise' ))

    itemlist.append(item.clone( channel='actions', action='show_old_domains', title='[COLOR coral][B]Historial Dominios[/B][/COLOR]', channel_id = 'dontorrents', thumbnail=config.get_thumb('dontorrents') ))

    platformtools.itemlist_refresh()

    return itemlist


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))
    itemlist.append(item.clone( title = 'Documentales', action = 'mainlist_documentary', text_color='cyan' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/page/1', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Lo último', action = 'list_last', url = host + 'ultimos', search_type = 'movie', text_color='cyan' ))

    itemlist.append(item.clone( title = 'En 4K', action = 'list_all', url = host + 'peliculas/4K/page/1', search_type = 'movie', text_color='moccasin' ))

    itemlist.append(item.clone( title = 'En HD', action = 'list_all', url = host + 'peliculas/hd/page/1', text_color='tan' ))

    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades',  search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie', tipo = 'genero' ))

    itemlist.append(item.clone( title = 'Por año', action = 'call_post', url = host + 'peliculas/buscar', search_type = 'movie', tipo = 'anyo' ))

    itemlist.append(item.clone( title = 'Por letra (A - Z)', action = 'alfabetico', url = host + 'peliculas/buscar', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/page/1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Lo último', action = 'list_last', url = host + 'ultimos', search_type = 'tvshow', text_color='cyan' ))

    itemlist.append(item.clone( title = 'En 4K', action = 'list_all', url = host + 'series/4K/page/1', search_type = 'tvshow', text_color='moccasin' ))

    itemlist.append(item.clone( title = 'En HD', action = 'list_all', url = host + 'series/hd/page/1', search_type = 'tvshow', text_color='tan' ))

    return itemlist


def mainlist_documentary(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='acciones', title= '[B]Acciones[/B] [COLOR plum](si no hay resultados)[/COLOR]', text_color='goldenrod' ))

    itemlist.append(item.clone( title = 'Buscar documental ...', action = 'search', search_type = 'documentary', text_color='cyan' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'documentales/page/1', search_type = 'documentary'))

    itemlist.append(item.clone( title = 'Lo último', action = 'list_last', url = host + 'ultimos', search_type = 'documentary', text_color='cyan' ))

    return itemlist


def calidades(item):
    logger.info()
    itemlist = []

    # ~ Alternative Webs Clons  No existen las opciones

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, 'id="calidadx"(.*?)</select>')

    matches = scrapertools.find_multiple_matches(bloque, '<option>(.*?)</option>')

    for qlty in matches:
        url = host + 'peliculas/buscar'

        itemlist.append(item.clone( title = qlty, url = url, qlty = qlty, tipo = 'qltys', action = 'call_post', text_color='moccasin' ))

    return sorted(itemlist, key=lambda x: x.title)


def generos(item):
    logger.info()
    itemlist = []

    genres = ['Acción',
       'Animación',
       'Aventuras',
       'Bélica',
       'Biográfica',
       'Ciencia Ficción',
       'Cine Negro',
       'Comedia',
       'Crimen',
       'Documental',
       'Drama',
       'Fantasía',
       'Musical',
       'Romántica',
       'Suspense',
       'Terror',
       'Western'
       ]

    for genre in genres:
        url = host + 'peliculas/buscar'

        itemlist.append(item.clone( action = "call_post", title = genre, url = url, tipo='genero', genre=genre, text_color = 'deepskyblue' ))

    return itemlist


def alfabetico(item):
    logger.info()
    itemlist = []

    if item.search_type == 'movie': text_color = 'deepskyblue'
    elif item.search_type == 'tvshow': text_color = 'hotpink'
    else: text_color = 'cyan'

    for letra in string.ascii_uppercase:
        itemlist.append(item.clone(action="call_post", title=letra, letra=letra, tipo='letra', text_color = text_color ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if item.search_type == "movie":
        matches = re.compile(r'<a href="([^"]+)">\s*<img.*?src="([^"]+)').findall(data)

        for url, thumb in matches:
            title = os.path.basename(os.path.normpath(url)).replace("-", " ")

            titulo = title

            if "4K" in titulo: titulo = titulo.split("4K")[0]
            if "ESP" in title: titulo = titulo.split("ESP")[0]
            if "(" in titulo: titulo = titulo.split("(")[0]

            if '/?url=' in thumb: thumb = scrapertools.find_single_match(thumb, '/?url=(.*?)$')
            else:
                thumb if "http" in thumb else "https:" + thumb

            itemlist.append(item.clone( action='findvideos', url=host[:-1] + url, title=title, thumbnail=thumb,
                                        contentType='movie', contentTitle=titulo, infoLabels={'year': "-"} ))

    elif item.search_type== 'tvshow':
        matches = re.compile(r"<a href='([^']+)'>([^<]+)").findall(data)

        if matches:
            for url, title in matches:
                SerieName = corregir_SerieName(title)

                if SerieName:
                    title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

                    itemlist.append(item.clone( action='episodios', url=host[:-1] + url, title=title,
                                                contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': "-"} ))

        else:
            matches = re.compile(r'<a href="([^"]+)">\s*<img.*?src="([^"]+)').findall(data)

            for url, thumb in matches:
                title = os.path.basename(os.path.normpath(url)).replace("-", " ")

                SerieName = corregir_SerieName(title)

                if '/?url=' in thumb: thumb = scrapertools.find_single_match(thumb, '/?url=(.*?)$')

                if SerieName:
                    title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

                    itemlist.append(item.clone( action='episodios', url=host[:-1] + url, title=title, thumbnail=thumb,				
					                            contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': "-"} ))

    else:
        matches = re.compile(r"<a href='([^']+)'>([^<]+)").findall(data)

        if matches:
            for url, title in matches:
                if "(" in title: titulo = title.split("(")[0]
                else: titulo = title

                titulo = titulo.strip()

                itemlist.append(item.clone( action = 'findvideos', url = host[:-1] + url, title = title,
                                            contentType = 'movie', contentTitle = titulo, contentExtra = 'documentary', infoLabels={'year': "-"} ))

        else:
            matches = re.compile(r'<a href="([^"]+)">\s*<img.*?src="([^"]+)').findall(data)

            for url, thumb in matches:
                title = os.path.basename(os.path.normpath(url)).replace("-", " ")

                if "(" in title: titulo = title.split("(")[0]
                else: titulo = title

                titulo = titulo.strip()

                if '/?url=' in thumb: thumb = scrapertools.find_single_match(thumb, '/?url=(.*?)$')

                itemlist.append(item.clone( action = 'findvideos', url = host[:-1] + url, title = title, thumbnail=thumb,
                                            contentType = 'movie', contentTitle = titulo, contentExtra = 'documentary', infoLabels={'year': "-"} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<a class="page-link" href="([^"]+)">Siguiente')
        if not next_page: next_page = scrapertools.find_single_match(data, '<a class="page-link".*?<li class="page-item">.*?href="([^"]+)".*?<i class="fas fa-chevron-right">')

        if next_page:
            next_page = host[:-1] + next_page

            itemlist.append(item.clone( title='Siguientes ...', url=next_page, action='list_all', text_color='coral' ))

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    if not data: return itemlist

    if item.search_type == "movie": search_type = "PELÍCULAS"
    elif item.search_type == "tvshow": search_type = "SERIES"
    elif item.search_type == "documentary": search_type = "DOCUMENTALES"

    try:
        match = re.compile("""(?s)<div class="h5 text-dark">%s:<\/div>(.*?)<br><br>""" % (search_type)).findall(data)[0]
    except:
        try:
            match = re.compile("""(?s)<div class="h5 text-dark">%s:<\/div>(.*?)<br></div>""" % (search_type)).findall(data)[0]
        except:
            match = ''

    matches = re.compile(r"""<span class="text-muted">\d+-\d+-\d+<\/span> <a href='([^']+)' class="text-primary">([^<]+)""").findall(match)

    if not matches:
        if item.search_type == "movie": search_type = "PELICULAS"
        elif item.search_type == "tvshow": search_type = "SERIES"
        elif item.search_type == "documentary": search_type = "DOCUMENTALES"

        if not '<div class="h5 text-dark">' in data:
            data = data.replace("<div class='h5 text-dark'>", '<div class="h5 text-dark">')
            data = data.replace("<span class='text-muted'>", '<span class="text-muted">')
            data = data.replace("class='text-primary'>", 'class="text-primary">')

        try:
            bloque = re.compile('<div class="h5 text-dark">%s:<\/div>(.*?)<br><br>' % (search_type)).findall(data)[0]
            matches = re.compile('<span class="text-muted">.*?' + "<a href='(.*?)'.*?" + 'class="text-primary">(.*?)</a>').findall(bloque)
        except: return itemlist

    for url, title in matches:
        title = title.replace('&#039;', "'")

        if item.search_type== 'movie':
            if "(" in title: titulo = title.split("(")[0]
            elif "[" in title: titulo = title.split("[")[0]
            else: titulo = title

            itemlist.append(item.clone( action='findvideos', url=host + url, title=title, contentType=item.search_type, contentTitle=titulo, infoLabels={'year': "-"} ))
        else:
            SerieName = corregir_SerieName(title)

            title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

            itemlist.append(item.clone( action='episodios', url=host + url, title=title, contentType=item.search_type, contentSerieName=SerieName, infoLabels={'year': "-"} ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def call_post(item):
    logger.info()

    if not item.page: item.page = 1

    if item.tipo == 'anyo':
        val = platformtools.dialog_numeric(0, "Indicar el año a buscar", default="")
        if not val: return

        item.post = "campo=%s&valor=%s&valor2=&valor3=&valor4=&pagina=%s" % ('anyo', val, str(item.page))

        item.contentType = item.search_type

    elif item.tipo == 'genero':
        item.post = "campo=%s&valor=&valor2=%s&valor3=&valor4=&pagina=%s" % ('genero', item.genre, str(item.page))

        item.contentType = item.search_type

    elif item.tipo == 'qltys':
        item.post = "campo=%s&valor=&valor2=&valor3=&valor5=%s&pagina=%s" % ('tiporip', item.qlty, str(item.page))

        item.contentType = item.search_type

    elif item.tipo == 'letra':
        if item.search_type == 'movie':
            item.post = "campo=%s&valor=&valor2=&valor3=%s&valor4=&pagina=%s" % ('letra', item.letra, str(item.page))

            item.contentType = item.search_type

        else:
            if item.search_type == "tvshow": tipo = "series"
            else: tipo = "documentales"
            item.url = host + "%s/letra-%s" %(tipo, item.letra.lower())
            return list_all(item)
 
    return list_post(item)


def list_post(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url, post=item.post)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    patron = '''<a class="position-relative" href="([^"]+)" data-toggle="popover" '''
    patron += '''data-content="<div><p class='lead text-dark mb-0'>([^<]+)'''
    patron += '''<\/p><hr class='my-2'><p>([^<]+).*?src='([^']+)'''

    matches = re.compile(patron).findall(data)

    for url, title, info, thumb in matches:
        titulo = title
        if "[4K]" in title: titulo = title.split("[4K]")[0]
        elif "(" in title: titulo = title.split("(")[0]

        itemlist.append(item.clone( action='findvideos', url=host[:-1] + url, title=title, thumbnail=thumb if "http" in thumb else "https:" + thumb,
                                            contentType=item.contentType, contentTitle=titulo, infoLabels={'year': "-", 'plot': info} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if item.post:
            next_page = scrapertools.find_single_match(item.post, '(.*?)pagina=')

            if next_page:
                item.page = item.page + 1
                exist_page = scrapertools.find_single_match(data, "<option value='" + str(item.page) + "'")

                if exist_page:
                     post = next_page + 'pagina=' + str(item.page)

                     itemlist.append(item.clone( title='Siguientes ...', url=item.url, action='list_post', post=post, text_color='coral' ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    patron = """<td style='vertical-align: middle;'>([^<]+)<\/td>\s*<td>"""
    patron += """<a class="text-white bg-primary rounded-pill d-block shadow-sm text-decoration-none my-1 py-1" """
    patron += """style="font-size: 18px; font-weight: 500;" href='([^']+)'"""

    i = 0

    matches = re.compile(patron).findall(data)

    if not matches:
        matches = scrapertools.find_multiple_matches(data, "<tr>.*?<td style='vertical-align.*?>(.*?)</td>.*?" + 'data-content-id="(.*?)".*?</tr>')

        # ~ Alternative Webs Clons
        if not matches:
            matches = scrapertools.find_multiple_matches(data, "<td style='vertical-align.*?>(.*?)</td>.*?<a.*?href='(.*?)'.*?download>Descargar</a>.*?</tr>")

    for title, id in matches:
        s_e = scrapertools.get_season_and_episode(title)

        try:
           season = int(s_e.split("x")[0])
           episode = s_e.split("x")[1]
        except:
           i += 1
           season = 0
           episode = i

        titulo = str(season) + 'x' + str(episode) + ' ' + item.contentSerieName

        itemlist.append(item.clone( action='findvideos', url = item.url, id = id, title = titulo,
                                    language = 'Esp', contentSeason = season, contentType = 'episode', contentEpisodeNumber = episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def nonce_gen(_challenge, difficulty=3):
    nonce = 0

    target = '0' * difficulty

    while True:
          text = _challenge + str(nonce)
          hash_hex = hashlib.sha256(text.encode()).hexdigest()

          if hash_hex.startswith(target): return nonce 

          nonce += 1

          if nonce % 1000 == 0: time.sleep(0.1)


def findvideos(item):
    logger.info()
    itemlist = []

    url = ''

    _tabla = '"peliculas\"'

    if item.contentType == "episode": _tabla = '"series\"'
    else:
        if item.contentType == 'documentary' or item.contentExtra == 'documentary': _tabla = _tabla = '"documentales\"'

    if not item.id:
        data = do_downloadpage(item.url)

        _id = scrapertools.find_single_match(data, 'data-content-id="(.*?)"')
    else:
        _id = item.id

    # ~ Alternative Webs Clons
    if url.startswith("//"): url = "https:" + url

    if _id:
        headers = {'Referer': item.url, 'Content-Type': 'application/json'}

        post1 = '{\"action\": \"generate\", \"content_id\": %s, \"tabla\": %s}' % (_id, _tabla)

        api = host + 'api_validate_pow.php/'

        data1 = do_downloadpage(api, post = post1, headers = headers)

        _challenge = scrapertools.find_single_match(str(data1), '"challenge":.*?"(.*?)"')

        if _challenge:
            _nonce = nonce_gen(_challenge)

            post2 = '{\"action\": \"validate\", \"challenge\": "%s", \"nonce\": "%s", \"unescape\": "False"}' % (_challenge, _nonce)

            data2 = do_downloadpage(api, post = post2, headers = headers)

            url = ''

            if '"success"' in str(data2):
                url = scrapertools.find_single_match(str(data2), '"download_url":.*?"(.*?)"')

                url = url.replace('\\/', '/')

        # ~ Orden Alternative Webs Findvideos
        if not host in alt_web_clons:
            if not url:
                item.url = item.url.replace(host, alt_find_mejortorrentin)

                url = alternative_find(item, 'MejorTorrentIn')

            if not url:
                item.url = item.url.replace(host, alt_find_dontorrent21)

                url = alternative_find(item, 'DonTorrent21')

            if not url:
                item.url = item.url.replace(host, alt_find_reinventorrent)

                url = alternative_find(item, 'ReinvenTorrent')

            if not url:
                item.url = item.url.replace(host, alt_find_todotorrents)

                url = alternative_find(item, 'TodoTorrents')

            if not url:
                item.url = item.url.replace(host, alt_find_elitedivx)

                url = alternative_find(item, 'EliteDivx')

            if not url:
                item.url = item.url.replace(host, alt_find_divxatope)

                url = alternative_find(item, 'DivxATope')

    # ~ Alternative Webs Clons
    if not url:
        if item.contentType == "episode":
            url = item.url
            qlty = ''

        elif not item.contentType == "tvshow":
            data = do_downloadpage(item.url)

            qlty = scrapertools.find_single_match(data, '<b class="bold">Formato:</b>(.*?)</p>').strip()

            patron = '<div class="text-center">.*?'
            patron += "href='([^']+)'.*?download>Descargar</a>"
            url = scrapertools.find_single_match(data, patron)

            if not url:
                if item.contentType == 'documentary' or item.contentExtra == 'documentary':
                    patron = '<b class="bold">Formato:</b>.*?'
                    patron += "href='([^']+)'.*?download>Descargar</a>"

                    url = scrapertools.find_single_match(data, patron)

            if url:
                url = url if url.startswith("http") else "https:" + url
        else:
            url = item.url
            qlty = ''

        if url:
            if not url == 'https:':
               lang = 'Esp'

               servidor = 'torrent'
               other = ''

               if url.endswith(".torrent"): pass
               elif url.startswith('magnet:'): other = 'magnet'
               else:
                  servidor = 'directo'
                  if '/ttlinks.live/' in url: other = 'ttlinks'

               itemlist.append(Item( channel = item.channel, action = 'play', title = '', language = lang, quality = qlty, url = url, server = servidor, other = other))

    if not url:
        platformtools.dialog_ok(config.__addon_name + ' - DonTorrents', '[COLOR red][B]No se pudo obtener los enlaces.[/B][/COLOR]', '[COLOR cyan][B]Intentélo desde cualquiera de sus Clones.[/B][/COLOR]', 'Vea cuales son sus Clones en [B][COLOR turquoise]Acciones[/COLOR] [COLOR plum](si no hay resultados)[/B][/COLOR]')
        return

    if not 'http' in url: url = 'https:' + url

    itemlist.append(Item( channel = item.channel, action = 'play', title = '', language = 'Esp', url = url, server = 'torrent'))

    return itemlist


def alternative_find(item, canal):
    logger.info()

    url = ''

    if item.contentType == "episode":
        data = alt_do_downloadpage(item.url)

        url = scrapertools.find_single_match(data, "<td style='vertical-align.*?'>" + str(item.contentSeason) + 'x' + str(item.contentEpisodeNumber) + "</td>.*?href='(.*?)'.*?>Descargar<")

        if url:
            url = url if url.startswith("http") else "https:" + url

    elif not item.contentType == "tvshow":
        data = alt_do_downloadpage(item.url)

        patron = '<div class="text-center">.*?'
        patron += "href='([^']+)'.*?download>Descargar</a>"

        url = scrapertools.find_single_match(data, patron)

        if not url:
            if item.contentType == 'documentary' or item.contentExtra == 'documentary':
                patron = '<b class="bold">Formato:</b>.*?'
                patron += "href='([^']+)'.*?download>Descargar</a>"

                url = scrapertools.find_single_match(data, patron)

        if url:
            url = url if url.startswith("http") else "https:" + url

    if url:
        if config.get_setting('channels_re_charges', default=True):
            platformtools.dialog_notification('DonTorrents - [COLOR palegreen]Acceso alternativo[/COLOR]', '[COLOR cyan][B]' + canal + '[/B][/COLOR]')

    return url


def play(item):
    logger.info()
    itemlist = []

    if item.url.endswith('.torrent'):
        if config.get_setting('proxies', item.channel, default=''):
            if PY3:
                from core import requeststools
                data = requeststools.read(item.url, 'dontorrents')
            else:
                data = do_downloadpage(item.url)

            if data:
                if '<h1>Not Found</h1>' in str(data) or '<!DOCTYPE html>' in str(data) or '<!DOCTYPE>' in str(data):
                    return 'Archivo [COLOR red]Inexistente[/COLOR]'

                file_local = os.path.join(config.get_data_path(), "temp.torrent")
                with open(file_local, 'wb') as f: f.write(data); f.close()

                itemlist.append(item.clone( url = file_local, server = 'torrent' ))
        else:
            itemlist.append(item.clone( url = item.url, server = 'torrent' ))

        return itemlist

    if 'magnet' in item.url:
        itemlist.append(item.clone( url = item.url, server = 'torrent' ))
        return itemlist

    host_torrent = alt_find_divxatope[:-1]
    url_base64 = decrypters.decode_url_base64(item.url, host_torrent)

    if not url_base64:
        host_torrent = alt_find_dontorrent21[:-1]
        url_base64 = decrypters.decode_url_base64(item.url, host_torrent)

    if not url_base64:
        host_torrent = alt_find_[mejortorrentin:-1]
        url_base64 = decrypters.decode_url_base64(item.url, host_torrent)

    if url_base64.startswith('magnet:'):
        itemlist.append(item.clone( url = url_base64, server = 'torrent' ))

    elif url_base64.endswith(".torrent"):
        if config.get_setting('proxies', item.channel, default=''):
            if PY3:
                from core import requeststools
                data = requeststools.read(url_base64, 'divxatope')
            else:
                data = do_downloadpage(url_base64)

            if data:
                if '<h1>Not Found</h1>' in str(data) or '<!DOCTYPE html>' in str(data) or '<!DOCTYPE>' in str(data):
                    return 'Archivo [COLOR red]Inexistente[/COLOR]'

                file_local = os.path.join(config.get_data_path(), "temp.torrent")
                with open(file_local, 'wb') as f: f.write(data); f.close()

                itemlist.append(item.clone( url = file_local, server = 'torrent' ))
        else:
            itemlist.append(item.clone( url = url_base64, server = 'torrent' ))

    return itemlist


def list_search(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 1

    # ~ Alternative Webs Clons
    if web_clon:
        headers = {'Referer': host}

        data = do_downloadpage(item.url, headers=headers)

        bloque = data
    else:
        headers = {'Referer': web_search_dontorrent}

        post = {'valor': item.tex, 'Buscar': 'Buscar', 'p': str(item.page)}

        data = do_downloadpage(item.url, post = post, headers = headers)

        new_web_search_dontorrent = scrapertools.find_single_match(data, '<meta property="og:url" content="(.*?)"')

        if new_web_search_dontorrent:
            if not new_web_search_dontorrent == web_search_dontorrent:
                headers = {'Referer': new_web_search_dontorrent}

                post = {'valor': item.tex, 'Buscar': 'Buscar', 'p': str(item.page)}

                data = do_downloadpage(new_web_search_dontorrent, post = post, headers = headers)

        bloque = scrapertools.find_single_match(data, '>Resultados<(.*?)</nav>')

    patron = "<a href='(.*?)'.*?"
    patron += 'class="text-decoration-none">(.*?)</a>'

    matches = re.compile(patron).findall(bloque)

    for url, title in matches:
        title = title.replace('<span class="text-secondary">', '').replace('<span class="text-secondary" >', '').replace('</span>', '').strip()

        if not url or not title: continue

        if "/pelicula/" in url: contentType = "movie"
        elif "/documental/" in url: contentType = "documentary"
        else: contentType = "tvshow"

        if item.search_type not in ['all', contentType]: continue

        sufijo = ''

        if item.search_type == 'all': 
            sufijo = contentType
            if sufijo == "documentary": sufijo = '[COLOR cyan]Documental[/COLOR]'

        if contentType == 'tvshow' or item.search_type == 'all':
            if not item.search_type == 'all':
                if item.search_type == "movie": continue

            SerieName = corregir_SerieName(title)

            title = title.replace('Temporada', '[COLOR tan]Temp.[/COLOR]').replace('temporada', '[COLOR tan]Temp.[/COLOR]')

            itemlist.append(item.clone( action='episodios', url=host[:-1] + url, title=title, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = SerieName, infoLabels={'year': "-"} ))

        if contentType == 'movie' or contentType == "documentary" or item.search_type == 'all':
            if not item.search_type == 'all':
                if item.search_type == "tvshow": continue

            if contentType == 'documentary':
                itemlist.append(item.clone( action = 'findvideos', url = host[:-1] + url, title = title, fmt_sufijo=sufijo,
                                            contentType = 'movie', contentTitle = title, contentExtra = 'documentary', infoLabels={'year': "-"} ))
            else:
                if "[" in title: titulo = title.split("[")[0]
                elif "(" in title: titulo = title.split("(")[0]
                else: titulo = title

                itemlist.append(item.clone( action='findvideos', url=host[:-1] + url, title=title, fmt_sufijo=sufijo,
                                            contentType='movie', contentTitle=titulo, infoLabels={'year': "-"} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<nav class="page-navigator"' in data:
             if 'onclick="buscarPagina' in data:
                 itemlist.append(item.clone( title='Siguientes ...', url = item.url, page = item.page + 1, action='list_search', text_color='coral' ))

    return itemlist


def corregir_SerieName(SerieName):
    logger.info()

    if "[" in SerieName: SerieName = SerieName.split("[")[0]
    elif "720p" in SerieName: SerieName = SerieName.split("720p")[0]

    if '1ª' in SerieName: SerieName = SerieName.split("1ª")[0]
    if '2ª' in SerieName: SerieName = SerieName.split("2ª")[0]
    if '3ª' in SerieName: SerieName = SerieName.split("3ª")[0]
    if '4ª' in SerieName: SerieName = SerieName.split("4ª")[0]
    if '5ª' in SerieName: SerieName = SerieName.split("5ª")[0]
    if '6ª' in SerieName: SerieName = SerieName.split("6ª")[0]
    if '7ª' in SerieName: SerieName = SerieName.split("7ª")[0]
    if '8ª' in SerieName: SerieName = SerieName.split("8ª")[0]
    if '9ª' in SerieName: SerieName = SerieName.split("9ª")[0]

    if "1 Temporada" in SerieName: SerieName = SerieName.split("1 Temporada")[0]
    elif "2 Temporada" in SerieName: SerieName = SerieName.split("2 Temporada")[0]
    elif "3 Temporada" in SerieName: SerieName = SerieName.split("3 Temporada")[0]
    elif "4 Temporada" in SerieName: SerieName = SerieName.split("4 Temporada")[0]
    elif "5 Temporada" in SerieName: SerieName = SerieName.split("5 Temporada")[0]
    elif "6 Temporada" in SerieName: SerieName = SerieName.split("6 Temporada")[0]
    elif "7 Temporada" in SerieName: SerieName = SerieName.split("6 Temporada")[0]
    elif "8 Temporada" in SerieName: SerieName = SerieName.split("8 Temporada")[0]
    elif "9 Temporada" in SerieName: SerieName = SerieName.split("9 Temporada")[0]
    elif " Temporada" in SerieName: SerieName = SerieName.split(" Temporada")[0]
    elif " - " in SerieName: SerieName = SerieName.split(" - ")[0]

    SerieName = SerieName.strip()

    return SerieName


def _news(item):
    logger.info()

    item.url = host + 'ultimos'
    item.search_type = 'movie'

    return list_last(item)


def search(item, texto):
    logger.info()
    try:
       item.url = web_search_dontorrent + 'buscar/'
       item.tex = texto
       return list_search(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []
