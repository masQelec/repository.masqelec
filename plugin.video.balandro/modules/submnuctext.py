# -*- coding: utf-8 -*-

import os

from platformcode import logger, config, platformtools
from core import filetools, scrapertools

from core.item import Item


fanart = os.path.join(config.get_runtime_path(), 'fanart.jpg')


color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')

color_alert = config.get_setting('notification_alert_color', default='red')
color_infor = config.get_setting('notification_infor_color', default='pink')
color_adver = config.get_setting('notification_adver_color', default='violet')
color_avis = config.get_setting('notification_avis_color', default='yellow')
color_exec = config.get_setting('notification_exec_color', default='cyan')


con_incidencias = ''
no_accesibles = ''
con_problemas = ''

try:
    with open(os.path.join(config.get_runtime_path(), 'dominios.txt'), 'r') as f: txt_status=f.read(); f.close()
except:
    try: txt_status = open(os.path.join(config.get_runtime_path(), 'dominios.txt'), encoding="utf8").read()
    except: txt_status = ''

if txt_status:
    # ~ Incidencias
    bloque = scrapertools.find_single_match(txt_status, 'SITUACION CANALES(.*?)CANALES TEMPORALMENTE DES-ACTIVADOS')

    matches = scrapertools.find_multiple_matches(bloque, "[B](.*?)[/B]")

    for match in matches:
        match = match.strip()

        if '[COLOR moccasin]' in match: con_incidencias += '[B' + match + '/I][/B][/COLOR][CR]'

    # ~ No Accesibles
    bloque = scrapertools.find_single_match(txt_status, 'CANALES PROBABLEMENTE NO ACCESIBLES(.*?)ULTIMOS CAMBIOS DE DOMINIOS')

    matches = scrapertools.find_multiple_matches(bloque, "[B](.*?)[/B]")

    for match in matches:
        match = match.strip()

        if '[COLOR moccasin]' in match: no_accesibles += '[B' + match + '/I][/B][/COLOR][CR]'

    # ~ Con Problemas
    bloque = scrapertools.find_single_match(txt_status, 'CANALES CON PROBLEMAS(.*?)$')

    matches = scrapertools.find_multiple_matches(bloque, "[B](.*?)[/B]")

    for match in matches:
        match = match.strip()

        if '[COLOR moccasin]' in match: con_problemas += '[B' + match + '/I][/B][/COLOR][CR]'


cfg_search_excluded_movies = 'search_excludes_movies'
cfg_search_excluded_tvshows = 'search_excludes_tvshows'
cfg_search_excluded_documentaries = 'search_excludes_documentaries'
cfg_search_excluded_torrents = 'search_excludes_torrents'
cfg_search_excluded_mixed = 'search_excludes_mixed'
cfg_search_excluded_all = 'search_excludes_all'

channels_search_excluded_movies = config.get_setting(cfg_search_excluded_movies, default='')
channels_search_excluded_tvshows = config.get_setting(cfg_search_excluded_tvshows, default='')
channels_search_excluded_documentaries = config.get_setting(cfg_search_excluded_documentaries, default='')
channels_search_excluded_torrents = config.get_setting(cfg_search_excluded_torrents, default='')
channels_search_excluded_mixed = config.get_setting(cfg_search_excluded_mixed, default='')
channels_search_excluded_all = config.get_setting(cfg_search_excluded_all, default='')


cfg_search_included = 'search_included_all'

channels_search_included = config.get_setting(cfg_search_included, default='')


host_filmaffinity = 'https://www.filmaffinity.com/es/'

thumb_filmaffinity = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'filmaffinity.jpg')
thumb_tmdb = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'tmdb.jpg')


context_buscar = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR fuchsia][B]Preferencias Play[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'helper', 'action': 'show_play_parameters'})

tit = '[COLOR powderblue][B]Preferencias Buscar[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'helper', 'action': 'show_help_parameters_search'})

tit = '[COLOR darkcyan][B]Preferencias Proxies[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'helper', 'action': 'show_prx_parameters'})

tit = '[COLOR bisque]Gestión Dominios[/COLOR]'
context_buscar.append({'title': tit, 'channel': 'helper', 'action': 'show_help_domains'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR darkorange][B]Quitar Dominios Memorizados[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'actions', 'action': 'manto_domains'})

tit = '[COLOR gold][B]Qué Canales No Intervienen[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'helper', 'action': 'channels_no_searchables'})

tit = '[COLOR gray][B]Qué Canales están Desactivados[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'filters', 'action': 'no_actives'})

tit = '[COLOR yellow][B]Búsquedas Solo en ...[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_included'})

if config.get_setting('search_included_all', default=''):
    tit = '[COLOR indianred][B]Quitar Búsquedas Solo en ...[/B][/COLOR]'
    context_buscar.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_included_del'})

tit = '[COLOR greenyellow][B]Excluir Canales[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded'})

if config.get_setting('search_excludes_all', default=''):
    tit = '[COLOR violet][B]Quitar Canales Excluidos[/B][/COLOR]'
    context_buscar.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del'})

if config.get_setting('search_excludes_movies', default=''):
    tit = '[B][COLOR deepskyblue]Películas [COLOR violet]Quitar Canales Excluidos [/B][/COLOR]'
    context_buscar.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del_movies'})

if config.get_setting('search_excludes_tvshows', default=''):
    tit = '[B][COLOR hotpink]Series [COLOR violet]Quitar Canales Excluidos [/B][/COLOR]'
    context_buscar.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del_tvshows'})

if config.get_setting('search_excludes_documentaries', default=''):
    tit = '[B][COLOR cyan]Documentales [COLOR violet]Quitar Canales Excluidos [/B][/COLOR]'
    context_buscar.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del_documentaries'})

if config.get_setting('search_excludes_torrents', default=''):
    tit = '[B][COLOR blue]Torrents [COLOR violet]Quitar Canales Excluidos [/B][/COLOR]'
    context_buscar.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del_torrents'})

if config.get_setting('search_excludes_mixed', default=''):
    tit = '[B][COLOR teal]Películas y/ó Series [COLOR violet]Quitar Canales Excluidos [/B][/COLOR]'
    context_buscar.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del_mixed'})

tit = '[COLOR powderblue][B]Global Configurar Proxies[/B][/COLOR]'
context_buscar.append({'title': tit, 'channel': 'proxysearch', 'action': 'proxysearch_all'})

if config.get_setting('proxysearch_excludes', default=''):
    tit = '[COLOR %s]Anular canales excluidos de Proxies[/COLOR]' % color_adver
    context_buscar.append({'title': tit, 'channel': 'proxysearch', 'action': 'channels_proxysearch_del'})

tit = '[COLOR %s]Información Proxies[/COLOR]' % color_infor
context_buscar.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

tit = '[COLOR %s][B]Quitar Todos los Proxies[/B][/COLOR]' % color_list_proxies
context_buscar.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s][B]Información Búsquedas[/B][/COLOR]' % color_infor
context_buscar.append({'title': tit, 'channel': 'helper', 'action': 'show_help_search'})

tit = '[COLOR %s]Ajustes categorías Canales, Dominios, Play, Proxies y Buscar[/COLOR]' % color_exec
context_buscar.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_search = []

tit = '[COLOR yellow][B]Preferencias Buscar[/B][/COLOR]'
context_search.append({'title': tit, 'channel': 'helper', 'action': 'show_help_parameters_search'})

tit = '[COLOR powderblue][B]Global Configurar Proxies[/B][/COLOR]'
context_search.append({'title': tit, 'channel': 'proxysearch', 'action': 'proxysearch_all'})

if config.get_setting('proxysearch_excludes', default=''):
    tit = '[COLOR %s]Anular canales excluidos en Proxies[/COLOR]' % color_list_proxies
    context_search.append({'title': tit, 'channel': 'proxysearch', 'action': 'channels_proxysearch_del'})

tit = '[COLOR %s]Información Proxies[/COLOR]' % color_avis
context_search.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

tit = '[COLOR %s][B]Información Búsquedas[/B][/COLOR]' % color_infor
context_search.append({'title': tit, 'channel': 'helper', 'action': 'show_help_search'})

tit = '[COLOR %s]Ajustes categoría Buscar[/COLOR]' % color_exec
context_search.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_cfg_search = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_cfg_search.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR %s]Ajustes categoría Menú[/COLOR]' % color_exec
context_cfg_search.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_generos = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_generos.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_generos.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR powderblue][B]Global Configurar Proxies[/B][/COLOR]'
context_generos.append({'title': tit, 'channel': 'proxysearch', 'action': 'proxysearch_all'})

if config.get_setting('proxysearch_excludes', default=''):
    tit = '[COLOR %s]Anular canales excluidos de Proxies[/COLOR]' % color_adver
    context_generos.append({'title': tit, 'channel': 'proxysearch', 'action': 'channels_proxysearch_del'})

tit = '[COLOR %s]Información Proxies[/COLOR]' % color_infor
context_generos.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

tit = '[COLOR %s][B]Quitar Proxies Actuales[/B][/COLOR]' % color_list_proxies
context_generos.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s]Ajustes categorías Menú, Canales, Dominios y Proxies[/COLOR]' % color_exec
context_generos.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

context_proxy_channels = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_proxy_channels.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_proxy_channels.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR powderblue][B]Global Configurar Proxies[/B][/COLOR]'
context_proxy_channels.append({'title': tit, 'channel': 'proxysearch', 'action': 'proxysearch_all'})

if config.get_setting('proxysearch_excludes', default=''):
    tit = '[COLOR %s]Anular canales excluidos de Proxies[/COLOR]' % color_adver
    context_proxy_channels.append({'title': tit, 'channel': 'proxysearch', 'action': 'channels_proxysearch_del'})

tit = '[COLOR %s]Información Proxies[/COLOR]' % color_avis
context_proxy_channels.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

tit = '[COLOR %s][B]Quitar Proxies Actuales[/B][/COLOR]' % color_list_proxies
context_proxy_channels.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s]Ajustes categorías Menú, Canales, Dominios y Proxies[/COLOR]' % color_exec
context_proxy_channels.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

context_usual = []

tit = '[COLOR tan][B]Preferencias Canales[/B][/COLOR]'
context_usual.append({'title': tit, 'channel': 'helper', 'action': 'show_channels_parameters'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_usual.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR powderblue][B]Global Configurar Proxies[/B][/COLOR]'
context_usual.append({'title': tit, 'channel': 'proxysearch', 'action': 'proxysearch_all'})

if config.get_setting('proxysearch_excludes', default=''):
    tit = '[COLOR %s]Anular canales excluidos de Proxies[/COLOR]' % color_adver
    context_usual.append({'title': tit, 'channel': 'proxysearch', 'action': 'channels_proxysearch_del'})

tit = '[COLOR %s]Información Proxies[/COLOR]' % color_avis
context_usual.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

tit = '[COLOR %s][B]Quitar Proxies Actuales[/B][/COLOR]' % color_list_proxies
context_usual.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s]Ajustes categorías Canales, Dominios y Proxies[/COLOR]' % color_exec
context_usual.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


def submnu_news(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]NOVEDADES:[/B]', thumbnail=config.get_thumb('novedades'), text_color='darksalmon' ))

    itemlist.append(item.clone( channel='helper', action='show_help_audios', title= '[COLOR green][B]Información[/B][/COLOR] [COLOR cyan][B]Idiomas[/B][/COLOR] en los Audios de los Vídeos', thumbnail=config.get_thumb('news'), fanart=fanart ))

    if config.get_setting('sub_mnu_favoritos', default=False):
        if  item.mnupral == 'main':
             itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), fanart=fanart, text_color='plum' ))

    itemlist.append(item.clone( action='submnu_channels', title='[COLOR yellow][B]Buscar[/B][/COLOR]', context=context_buscar, extra = item.extra, thumbnail=config.get_thumb('search'), fanart=fanart ))

    presentar = False
    if config.get_setting('mnu_pelis', default=True) or config.get_setting('mnu_series', default=True): presentar = True

    if presentar:
        itemlist.append(item.clone( title = '[B]Canales:[/B]', action = '', context=context_usual, thumbnail=config.get_thumb('stack'), text_color='gold' ))

        if config.get_setting('mnu_pelis', default=True):
            if item.extra == 'all' or item.extra == 'mixed' or item.extra == 'movies' or item.extra == 'groups':
                itemlist.append(item.clone( channel='groups', action = 'ch_groups', title = ' - De [COLOR deepskyblue][B]Películas[/B][/COLOR] con Estrenos y/ó Novedades', thumbnail=config.get_thumb('movie'), group = 'news', extra = 'movies', ))

        if config.get_setting('mnu_series', default=True):
            if item.extra == 'all' or item.extra == 'mixed' or item.extra == 'tvshows' or item.extra == 'groups':
               itemlist.append(item.clone( channel='groups', action = 'ch_groups', title = ' - De [COLOR hotpink][B]Series[/B][/COLOR] con Nuevos Episodios y/ó Últimos', thumbnail=config.get_thumb('tvshow'), group = 'lasts', extra = 'tvshows' ))

    itemlist.append(item.clone( action='', title= '[B]Cartelera:[/B]', folder=False, text_color='yellowgreen' ))

    itemlist.append(item.clone( channel='tmdblists', action='listado', title= ' - [COLOR deepskyblue][B]Películas[/B][/COLOR] en cartelera [COLOR violet][B]TMDB[/B][/COLOR]', thumbnail=thumb_tmdb, search_type='movie', extra = 'now_playing' ))

    itemlist.append(item.clone( channel='filmaffinitylists', action='list_all', url = host_filmaffinity + 'cat_new_th_es.html', title= ' - [COLOR deepskyblue][B]Películas[/B][/COLOR] en cartelera [COLOR violet][B]Filmaffinity[/B][/COLOR]', thumbnail=thumb_filmaffinity, search_type='movie' ))

    itemlist.append(item.clone( title = '[B]Filmaffinity:[/B]', action = '', thumbnail=config.get_thumb('novedades'), text_color='violet' ))

    itemlist.append(item.clone( title = ' - [B][COLOR teal]Películas y Series[/COLOR][/B] Novedades a la venta', channel='filmaffinitylists', action = 'list_all', url = host_filmaffinity + 'cat_new_sa_es.html', search_type = 'all', thumbnail=thumb_filmaffinity ))

    itemlist.append(item.clone( title = ' - [B][COLOR teal]Películas y Series[/COLOR][/B] Novedades en alquiler', channel='filmaffinitylists', action = 'list_all', url = host_filmaffinity + 'cat_new_re_es.html', search_type = 'all', thumbnail=thumb_filmaffinity ))

    return itemlist


def submnu_genres(item):
    logger.info()
    itemlist = []

    if config.get_setting('mnu_search_proxy_channels', default=False):
        itemlist.append(item.clone( action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), fanart=fanart, text_color='red' ))

    if config.get_setting('sub_mnu_favoritos', default=False):
        if  item.mnupral == 'main':
             itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), fanart=fanart, text_color='plum' ))

    itemlist.append(item.clone( action='submnu_news', title='[B]Novedades[/B]', extra = 'all', thumbnail=config.get_thumb('novedades'), text_color='darksalmon' ))

    itemlist.append(item.clone( action='submnu_special', title='[B]Especiales[/B]', context=context_cfg_search, extra='all', thumbnail=config.get_thumb('heart'), text_color='pink' ))

    itemlist.append(item.clone( channel='generos', action='mainlist', title='[B]Géneros[/B]', context=context_generos, thumbnail=config.get_thumb('genres'), text_color='thistle' ))

    itemlist.append(item.clone( action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'all', thumbnail=config.get_thumb('search'), text_color='yellow' ))

    itemlist.append(item.clone( title = '[B]Canales:[/B]', action = '', context=context_usual, thumbnail=config.get_thumb('stack'), text_color='gold' ))

    itemlist.append(item.clone( channel='groups', action='ch_generos', title=' - Canales de [COLOR deepskyblue][B]Películas[/B][/COLOR] con géneros', context=context_usual, group = 'generos', extra = 'movies', thumbnail = config.get_thumb('movie') ))

    itemlist.append(item.clone( channel='groups', action='ch_generos', title=' - Canales de [COLOR hotpink][B]Series[/B][/COLOR] con géneros', context=context_usual, group = 'generos', extra = 'tvshows', thumbnail = config.get_thumb('tvshow') ))

    itemlist.append(item.clone( title = '[B]Proxies:[/B]', action = '', context=context_usual, thumbnail=config.get_thumb('flame'), text_color='red' ))

    itemlist.append(item.clone(  channel='filters', action='with_proxies', title= '- [B]Canales que podrían necesitar Nuevamente [COLOR red]Proxies[/COLOR][/B]', thumbnail=config.get_thumb('stack'), fanart=fanart, text_color='coral' ))

    if config.get_setting('memorize_channels_proxies', default=True):
        itemlist.append(item.clone( channel='helper', action='channels_with_proxies_memorized', title= ' - Qué [COLOR red][B]Canales[/B][/COLOR] tiene con proxies Memorizados', new_proxies=True, memo_proxies=True, test_proxies=True, thumbnail=config.get_thumb('stack'), fanart=fanart ))

    return itemlist


def submnu_special(item):
    logger.info()
    itemlist = []

    bus_docs = False
    filmaffinity = False

    itemlist.append(item.clone( action='', title='[B]ESPECIALES:[/B]', folder=False, text_color='pink' ))

    if config.get_setting('sub_mnu_favoritos', default=False):
        if  item.mnupral == 'main':
             itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), fanart=fanart, text_color='plum' ))

    itemlist.append(item.clone( action='submnu_channels', title='[COLOR yellow][B]Buscar[/B][/COLOR]', context=context_buscar, extra = item.extra, thumbnail=config.get_thumb('search') ))

    if item.extra == 'all' or item.extra == 'mixed' or item.extra == 'movies':
        itemlist.append(item.clone( action='', title = '[COLOR deepskyblue][B]Películas Recomendadas:[/B][/COLOR]', thumbnail=config.get_thumb('movie'), folder=False ))

        thumb_cinedeantes = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'cinedeantes.jpg')
        itemlist.append(item.clone( channel='cinedeantes', action='list_all', title='[COLOR dodgerblue] - Joyas del cine clásico[/COLOR]', url = 'https://cinedeantes2.weebly.com/joyas-del-cine.html', thumbnail=thumb_cinedeantes, search_type = 'movie' ))

        thumb_zoowomaniacos = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'zoowomaniacos.jpg')
        itemlist.append(item.clone( channel='zoowomaniacos', action='_las1001', title='[COLOR cyan] - Las 1001 que hay que ver[/COLOR]', thumbnail=thumb_zoowomaniacos, search_type = 'movie' ))

        itemlist.append(item.clone( channel='zoowomaniacos', action='_culto', title='[COLOR moccasin] - Cine de culto[/COLOR]', thumbnail=thumb_zoowomaniacos, search_type = 'movie' ))

        itemlist.append(item.clone( channel='zoowomaniacos', action='generos', title='[COLOR thistle] - Géneros[/COLOR]', thumbnail=thumb_zoowomaniacos, search_type = 'movie' ))

        thumb_sigloxx = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'sigloxx.jpg')
        itemlist.append(item.clone( channel='sigloxx', action='youtubes', title='[COLOR olivedrab] - Seleccion YouTube[/COLOR]', thumbnail=thumb_sigloxx, search_type = 'movie' ))

        presentar = False
        if config.get_setting('mnu_simple', default=False): presentar = True
        elif config.get_setting('mnu_pelis', default=True): presentar = True
        elif config.get_setting('mnu_series', default=True): presentar = True
        elif config.get_setting('channels_link_pyse', default=False): presentar = True
        elif config.get_setting('search_extra_main', default=False): presentar = True

        if presentar:
            itemlist.append(item.clone( action='', title= '[B]Listas de Películas:[/B]', folder=False, text_color='yellowgreen' ))

            itemlist.append(item.clone( channel='filmaffinitylists', title = ' - Sagas y colecciones', action = 'sagas', url = host_filmaffinity + 'movie-groups-all.php', page = 1, thumbnail=config.get_thumb('bestsagas'), search_type = 'movie', text_color='aqua' ))

            itemlist.append(item.clone( channel='filmaffinitylists', action='oscars', title=' - Premios Oscar', url = host_filmaffinity + 'oscar_data.php', text_color='deepskyblue', thumbnail=config.get_thumb('oscars'), plot = 'Las películas nominadas/galardonadas en los premios Oscars' ))

            itemlist.append(item.clone( channel='tmdblists', action='descubre', title=' - Halloween', text_color='aquamarine', extra = 27, search_type = 'movie', thumbnail=config.get_thumb('halloween'), plot = 'Películas del género Terror' ))

            itemlist.append(item.clone( channel='filmaffinitylists', action='_navidad', title=' - Navidad', thumbnail=config.get_thumb('navidad'), plot = 'Películas y Series del tema Navidad', text_color = 'dodgerblue' ))

            itemlist.append(item.clone( channel='filmaffinitylists', title = ' - Festivales', action = 'festivales', url = host_filmaffinity + 'all_awards.php', search_type = 'movie', text_color = 'powderblue' ))

            itemlist.append(item.clone( channel='filmaffinitylists', title = ' - Otros Premios', action = 'festivales', url = host_filmaffinity + 'all_awards.php', group = 'awards', search_type = 'movie', text_color = 'slateblue' ))

            itemlist.append(item.clone( channel='filmaffinitylists', title = ' - Por tema', action = 'temas', url = host_filmaffinity + 'topics.php', thumbnail=config.get_thumb('listthemes'), search_type = 'movie', text_color='moccasin' ))

    if item.extra == 'all' or item.extra == 'mixed' or item.extra == 'tvshows' or item.extra == 'infantil':
        itemlist.append(item.clone( action='', title = '[COLOR hotpink][B]Series Recomendadas:[/B][/COLOR]', thumbnail=config.get_thumb('tvshow'), folder=False ))

        thumb_tvseries = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'tvseries.jpg')
        itemlist.append(item.clone(  channel='tvseries', title = '[COLOR olivedrab] - Seleccion YouTube [/COLOR][COLOR hotpink]Animación[/COLOR]', action = 'youtubes', thumbnail=thumb_tvseries ))

        if not item.extra == 'infantil':
            itemlist.append(item.clone(  channel='tvseries', title = '[COLOR olivedrab] - Seleccion YouTube [/COLOR][COLOR hotpink]Humor[/COLOR]', action = 'youtubes2', thumbnail=thumb_tvseries ))

            presentar = False
            if config.get_setting('mnu_simple', default=False): presentar = True
            elif config.get_setting('mnu_series', default=True): presentar = True
            elif config.get_setting('channels_link_pyse', default=False): presentar = True
            elif config.get_setting('search_extra_main', default=False): presentar = True

            if presentar:
                itemlist.append(item.clone( action='', title= '[B]Listas de Series:[/B]', folder=False, text_color='yellowgreen' ))

                itemlist.append(item.clone( channel='filmaffinitylists', action='emmy_ediciones', title=' - Premios Emmy', url = host_filmaffinity +'award_data.php?award_id=emmy&year=', text_color='hotpink', thumbnail=config.get_thumb('emmys'), plot = 'Las Series nominadas/galardonadas en los premios Emmy' ))

                itemlist.append(item.clone( channel='filmaffinitylists', title = ' - Por tema', action = 'temas', url = host_filmaffinity + 'topics.php', thumbnail=config.get_thumb('listthemes'), search_type = 'tvshow', text_color='moccasin' ))

    if item.extra == 'all' or item.extra == 'mixed' or item.extra == 'documentaries':
        itemlist.append(item.clone( action='', title = '[COLOR cyan][B]Documentales Recomendados:[/B][/COLOR]', thumbnail=config.get_thumb('documentary'), folder=False ))

        itemlist.append(item.clone( channel='filmaffinitylists', title = ' - Los mejores', action = 'list_sel', url = host_filmaffinity +  'topgen.php?country=%s&genre%s5s&fromyear=%s&toyear=%s&notvse=1', cod_genre = 'DO', thumbnail=config.get_thumb('bestdocumentaries'), search_type = 'all', text_color='moccasin' ))

        thumb_youtubedocs = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'youtubedocs.jpg')
        itemlist.append(item.clone(  channel='youtubedocs', title = '[COLOR olivedrab] - Seleccion YouTube[/COLOR]', action = 'mainlist', thumbnail=thumb_youtubedocs ))

    return itemlist


def submnu_channels(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]Buscar:[/B]', folder=False, text_color='yellow' ))

    if item.extra == 'movies':
        if config.get_setting('sub_mnu_cfg_search', default=True):
            itemlist.append(item.clone( action='submnu_search', title=' - [B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'movies', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

        itemlist.append(Item( channel='search', action='search', search_type='movie', title=' - [B]Buscar Película[/B] ...', context=context_search, extra = 'movies', thumbnail=config.get_thumb('movie'), fanart=fanart, text_color='deepskyblue' ))

        if config.get_setting('search_extra_trailers', default=False):
            itemlist.append(item.clone( channel='trailers', action='search', title=' - [B]Buscar Tráiler[/B] ...', thumbnail=config.get_thumb('trailers'), fanart=fanart, text_color='darkgoldenrod' ))

        if config.get_setting('search_extra_main', default=False) or config.get_setting('channels_link_pyse', default=False):
            itemlist.append(item.clone( channel='tmdblists', action='mainlist', search_type='movie', title=' - [B]Búsquedas y listas en TMDB[/B]', thumbnail=thumb_tmdb, text_color=color_adver ))

            itemlist.append(item.clone( channel='filmaffinitylists', action='mainlist', search_type='movie', title=' - [B]Búsquedas y listas en Filmaffinity[/B]', thumbnail=thumb_filmaffinity, text_color=color_adver ))

    elif item.extra == 'tvshows':
        if config.get_setting('sub_mnu_cfg_search', default=True):
            itemlist.append(item.clone( action='submnu_search', title=' - [B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'tvshows', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

        itemlist.append(Item( channel='search', action='search', search_type='tvshow', title=' - [B]Buscar Serie[/B] ...', context=context_search, extra = 'tvshows', thumbnail=config.get_thumb('tvshow'), fanart=fanart, text_color='hotpink' ))

        if config.get_setting('search_extra_main', default=False) or config.get_setting('channels_link_pyse', default=False):
            itemlist.append(item.clone( channel='tmdblists', action='mainlist', search_type='tvshow', title=' - [B]Búsquedas y listas en TMDB[/B]', thumbnail=thumb_tmdb, text_color=color_adver ))

            itemlist.append(item.clone( channel='filmaffinitylists', action='mainlist', search_type='tvshow', title=' - [B]Búsquedas y listas en Filmaffinity[/B]', thumbnail=thumb_filmaffinity, text_color=color_adver ))

    elif item.extra == 'documentaries':
        if config.get_setting('sub_mnu_cfg_search', default=True):
            itemlist.append(item.clone( action='submnu_search', title=' - [B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'documentaries', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

        itemlist.append(Item( channel='search', action='search', search_type='documentary', title=' - [B]Buscar Documental[/B] ...', context=context_search, extra = 'documentaries', thumbnail=config.get_thumb('documentary'), fanart=fanart, text_color='cyan' ))

        if config.get_setting('search_extra_main', default=False) or config.get_setting('channels_link_pyse', default=False):
            itemlist.append(item.clone( channel='filmaffinitylists', action='mainlist', search_type='documentary', title=' - [B]Búsquedas y listas en Filmaffinity[/B]', thumbnail=thumb_filmaffinity, text_color=color_adver ))

    elif item.extra == 'mixed':
        if config.get_setting('sub_mnu_cfg_search', default=True):
            itemlist.append(item.clone( action='submnu_search', title=' - [B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'mixed', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

        itemlist.append(Item( channel='search', action='search', search_type='all', title=' - [B]Buscar Película y/ó Serie[/B] ...', context=context_search, extra = 'mixed', thumbnail=config.get_thumb('search'), fanart=fanart, text_color='yellow' ))

        if config.get_setting('mnu_documentales', default=True):
            itemlist.append(Item( channel='search', action='search', search_type='documentary', title=' - [B]Buscar documental[/B] ...', context=context_search, extra = 'documentaries', thumbnail=config.get_thumb('documentary'), fanart=fanart, text_color='cyan' ))

        if config.get_setting('search_extra_trailers', default=False):
             itemlist.append(item.clone( channel='trailers', action='search', title=' - [B]Buscar Tráiler[/B] ...', thumbnail=config.get_thumb('trailers'), fanart=fanart, text_color='darkgoldenrod' ))

        if config.get_setting('search_extra_main', default=False) or config.get_setting('channels_link_pyse', default=False):
            itemlist.append(item.clone( channel='tmdblists', action='mainlist', search_type='all', title=' - [B]Búsquedas y listas en TMDB[/B]', thumbnail=thumb_tmdb, text_color=color_adver ))

            itemlist.append(item.clone( channel='filmaffinitylists', action='mainlist', search_type='all', title=' - [B]Búsquedas y listas en Filmaffinity[/B]', thumbnail=thumb_filmaffinity, text_color=color_adver ))

    elif item.extra == 'torrents':
        if config.get_setting('sub_mnu_cfg_search', default=True):
            itemlist.append(item.clone( action='submnu_search', title=' - [B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'torrents', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

        if not config.get_setting('search_no_exclusively_torrents', default=False):
            itemlist.append(Item( channel='search', action='search', search_type='all', title=' - [B][COLOR blue]Buscar Torrent[/COLOR] película y/ó Serie [/B] ...', context=context_search, extra = 'only_torrents', search_special = 'torrent', thumbnail=config.get_thumb('search'), fanart=fanart, text_color='yellow' ))

        if config.get_setting('mnu_documentales', default=True):
            itemlist.append(Item( channel='search', action='search', search_type='documentary', title=' - [B]Buscar documental[/B] ...', context=context_search, extra = 'documentaries', thumbnail=config.get_thumb('documentary'), fanart=fanart, text_color='cyan' ))

        if config.get_setting('search_extra_trailers', default=False):
            itemlist.append(item.clone( channel='trailers', action='search', title=' - [B]Buscar Tráiler[/B] ...', thumbnail=config.get_thumb('trailers'), fanart=fanart, text_color='darkgoldenrod' ))

    elif item.extra == 'infantil':
        if config.get_setting('sub_mnu_cfg_search', default=True):
            itemlist.append(item.clone( action='submnu_search', title=' - [B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'mixed', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

        itemlist.append(Item( channel='search', action='search', search_type='all', title=' - [B]Buscar Película y/ó Serie[/B] ...', context=context_search, extra = 'mixed', thumbnail=config.get_thumb('search'), fanart=fanart, text_color='yellow' ))

        if config.get_setting('search_extra_trailers', default=False):
            itemlist.append(item.clone( channel='trailers', action='search', title=' - [B]Buscar Tráiler[/B] ...', thumbnail=config.get_thumb('trailers'), fanart=fanart, text_color='darkgoldenrod' ))

        if config.get_setting('search_extra_main', default=False) or config.get_setting('channels_link_pyse', default=False):
            itemlist.append(item.clone( channel='tmdblists', action='mainlist', search_type='all', title=' - [B]Búsquedas y listas en TMDB[/B]', thumbnail=thumb_tmdb, text_color=color_adver ))

            itemlist.append(item.clone( channel='filmaffinitylists', action='mainlist', search_type='all', title=' - [B]Búsquedas y listas en Filmaffinity[/B]', thumbnail=thumb_filmaffinity, text_color=color_adver ))

    elif item.extra == 'tales':
        if config.get_setting('sub_mnu_cfg_search', default=True):
            itemlist.append(item.clone( action='submnu_search', title=' - [B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'tvshows', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

        itemlist.append(Item( channel='search', action='search', search_type='tvshow', title=' - [B]Buscar Serie[/B] ...', context=context_search, extra = 'tvshows', thumbnail=config.get_thumb('tvshow'), fanart=fanart, text_color='hotpink' ))

        if config.get_setting('search_extra_main', default=False) or config.get_setting('channels_link_pyse', default=False):
            itemlist.append(item.clone( channel='tmdblists', action='mainlist', search_type='tvshow', title=' - [B]Búsquedas y listas en TMDB[/B]', thumbnail=thumb_tmdb, text_color=color_adver ))

            itemlist.append(item.clone( channel='filmaffinitylists', action='mainlist', search_type='tvshow', title=' - [B]Búsquedas y listas en Filmaffinity[/B]', thumbnail=thumb_filmaffinity, text_color=color_adver ))

    elif item.extra == 'dorama':
        if config.get_setting('sub_mnu_cfg_search', default=True):
            itemlist.append(item.clone( action='submnu_search', title=' - [B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'mixed', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

        itemlist.append(Item( channel='search', action='search', search_type='all', title=' - [B]Buscar Dorama[/B] ...', thumbnail=config.get_thumb('computer'), search_special = 'dorama', fanart=fanart, text_color='firebrick' ))

    elif item.extra == 'anime':
        if config.get_setting('sub_mnu_cfg_search', default=True):
            itemlist.append(item.clone( action='submnu_search', title=' - [B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'mixed', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

        itemlist.append(Item( channel='search', action='search', search_type='all', title=' - [B]Buscar Anime[/B] ...', thumbnail=config.get_thumb('anime'), search_special = 'anime', fanart=fanart, text_color='springgreen' ))

    else:
        if config.get_setting('sub_mnu_cfg_search', default=True):
            itemlist.append(item.clone( action='submnu_search', title=' - [B]Personalizar búsquedas[/B]', context=context_cfg_search, extra = 'all', thumbnail=config.get_thumb('help'), text_color='moccasin' ))

        itemlist.append(Item( channel='search', action='search', search_type='all', title=' - [B]Buscar Película y/ó Serie[/B] ...', context=context_search, thumbnail=config.get_thumb('search'), fanart=fanart, text_color='yellow' ))

        if not config.get_setting('mnu_simple', default=False):
            if config.get_setting('mnu_documentales', default=True):
                itemlist.append(Item( channel='search', action='search', search_type='documentary', title=' - [B]Buscar Documental[/B] ...', context=context_search, thumbnail=config.get_thumb('documentary'), fanart=fanart, text_color='cyan' ))

        if config.get_setting('search_extra_trailers', default=False):
            itemlist.append(item.clone( channel='trailers', action='search', title=' - [B]Buscar Tráiler[/B] ...', thumbnail=config.get_thumb('trailers'), fanart=fanart, text_color='darkgoldenrod' ))

        if config.get_setting('search_extra_main', default=False) or config.get_setting('channels_link_pyse', default=False):
            itemlist.append(item.clone( channel='tmdblists', action='mainlist', search_type='all', title=' - [B]Búsquedas y listas en TMDB[/B]', thumbnail=thumb_tmdb, text_color=color_adver ))

            itemlist.append(item.clone( channel='filmaffinitylists', action='mainlist', search_type='all', title=' - [B]Búsquedas y listas en Filmaffinity[/B]', thumbnail=thumb_filmaffinity, text_color=color_adver ))

    return itemlist


def submnu_search(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]PERSONALIZAR BÚSQUEDAS:[/B]', folder=False, text_color='moccasin' ))

    itemlist.append(item.clone( action='show_infos', title='[COLOR fuchsia][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    if config.get_setting('search_extra_proxies', default=True):
        itemlist.append(item.clone( action='', title='[B]Búsquedas en canales con Proxies:[/B]', folder=False, thumbnail=config.get_thumb('stack'), fanart=fanart, text_color='red' ))

        itemlist.append(item.clone( action='show_infos_proxies', title=' - [COLOR salmon][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

        itemlist.append(item.clone( channel='filters', action='with_proxies', title=' - Qué canales pueden usar [COLOR red][B]Proxies[/B][/COLOR]', thumbnail=config.get_thumb('stack'), fanart=fanart, new_proxies=True ))

        if config.get_setting('memorize_channels_proxies', default=True):
            itemlist.append(item.clone( channel='filters', action='with_proxies', title=  ' - Qué [COLOR red][B]Canales[/B][/COLOR] tiene con proxies Memorizados', thumbnail=config.get_thumb('stack'), fanart=fanart, new_proxies=True, memo_proxies=True, test_proxies=True ))

        itemlist.append(item.clone( channel='actions', action = 'manto_proxies', title= ' - Quitar los proxies en los canales [COLOR red][B](que los Tengan)[/B][/COLOR]', thumbnail=config.get_thumb('flame'), fanart=fanart ))

        itemlist.append(item.clone( channel='proxysearch', action='proxysearch_all', title=' - Configurar proxies a usar [COLOR plum][B](en los canales que los Necesiten)[/B][/COLOR]', thumbnail=config.get_thumb('flame'), fanart=fanart ))

        if config.get_setting('proxysearch_excludes', default=''):
            itemlist.append(item.clone( channel='proxysearch', action='channels_proxysearch_del', title=' - Anular los canales excluidos de Configurar proxies a usar', thumbnail=config.get_thumb('flame'), fanart=fanart, text_color='coral' ))

    if item.only_options_proxies:
        itemlist.append(item.clone( action='', title= '[B]Preferencias:[/B]', folder=False, text_color='goldenrod' ))

        itemlist.append(item.clone( channel='actions', title=' - [COLOR chocolate]Ajustes[/COLOR] categorías ([COLOR tan][B]Menú[/B][/COLOR], [COLOR red][B]Proxies[/B][/COLOR] y [COLOR yellow][B]Buscar[/B][/COLOR])', action = 'open_settings', thumbnail=config.get_thumb('settings'), fanart=fanart ))

        return itemlist

    if config.get_setting('sub_mnu_cfg_search', default=True):
        itemlist.append(item.clone( action='', title= '[B]Personalización búsquedas:[/B]', folder=False, text_color='moccasin' ))

        itemlist.append(item.clone( channel='helper', action='show_help_parameters_search', title=' - Qué [COLOR chocolate][B]Ajustes[/B][/COLOR] tiene en preferencias para las búsquedas', thumbnail=config.get_thumb('news'), fanart=fanart ))

        itemlist.append(item.clone( channel='filters', action='no_actives', title=' - Qué canales no intervienen en las búsquedas están [COLOR grey][B]están Desactivados[/B][/COLOR]', thumbnail=config.get_thumb('stack'), fanart=fanart ))

        itemlist.append(item.clone( channel='filters', action='channels_status', title=' - Personalizar [COLOR gold]Canales[/COLOR] (Desactivar ó Re-activar)', des_rea=True, thumbnail=config.get_thumb('stack'), fanart=fanart ))

        itemlist.append(item.clone( channel='filters', action='only_prefered', title=' - Qué canales tiene marcados como [COLOR gold]Preferidos[/COLOR]', thumbnail=config.get_thumb('stack'), fanart=fanart ))

        itemlist.append(item.clone( channel='filters', action='channels_status', title=' - Personalizar canales [COLOR gold]Preferidos[/COLOR] (Marcar ó Des-marcar)', des_rea=False, thumbnail=config.get_thumb('stack'), fanart=fanart ))

    itemlist.append(item.clone( action='', title= '[B]Personalizaciones especiales:[/B]', folder=False, text_color='yellow' ))

    if config.get_setting('search_show_last', default=True):
        itemlist.append(item.clone( channel='actions', action = 'manto_textos', title= ' - Quitar los [COLOR coral][B]Textos[/B][/COLOR] Memorizados de las búsquedas', thumbnail=config.get_thumb('pencil'), fanart=fanart ))

    itemlist.append(item.clone( channel='filters', action = 'mainlist2', title = ' - Efectuar búsquedas [COLOR gold][B](solo en determinados canales)[/B][/COLOR]', thumbnail=config.get_thumb('stack'), fanart=fanart ))

    itemlist.append(item.clone( action='', title= '[COLOR cyan][B]Excluir canales de las búsquedas:[/B][/COLOR]', folder=False, thumbnail=config.get_thumb('stack'), fanart=fanart ))

    itemlist.append(item.clone( channel='filters', action = 'mainlist', title = ' - [COLOR cyan]Excluir[/COLOR] canales de las búsquedas', thumbnail=config.get_thumb('stack'), fanart=fanart ))

    if item.extra == 'movies':
        itemlist.append(item.clone( channel='filters', action='channels_excluded', title=' - [COLOR tomato]Excluir[/COLOR] canales de [COLOR deepskyblue][B]Películas[/B][/COLOR]', extra='movies', thumbnail=config.get_thumb('movie'), fanart=fanart ))

        if channels_search_excluded_movies:
            itemlist.append(item.clone( channel='filters', action='channels_excluded_del', title=' - [COLOR coral][B]Anular los canales excluidos de [COLOR deepskyblue]Películas[/B][/COLOR]', extra='movies', thumbnail=config.get_thumb('movie'), fanart=fanart ))

    elif item.extra == 'tvshows':
        itemlist.append(item.clone( channel='filters', action='channels_excluded', title=' - [COLOR tomato]Excluir[/COLOR] canales de [COLOR hotpink][B]Series[/B][/COLOR]', extra='tvshows', thumbnail=config.get_thumb('tvshow'), fanart=fanart ))

        if channels_search_excluded_tvshows:
            itemlist.append(item.clone( channel='filters', action='channels_excluded_del', title=' - [COLOR coral][B]Anular los canales excluidos de [COLOR hotpink]Series[/B][/COLOR]', extra='tvshows', thumbnail=config.get_thumb('tvshow'), fanart=fanart ))

    elif item.extra == 'documentaries':
        itemlist.append(item.clone( channel='filters', action='channels_excluded', title=' - [COLOR tomato]Excluir[/COLOR] canales de [COLOR cyan][B]Documentales[/B][/COLOR]', extra='documentaries', thumbnail=config.get_thumb('documentary'), fanart=fanart ))

        if channels_search_excluded_documentaries:
            itemlist.append(item.clone( channel='filters', action = 'channels_excluded_del', title=' - [COLOR coral][B]Anular los canales excluidos de [COLOR cyan]Documentales[/B][/COLOR]', extra='documentaries', thumbnail=config.get_thumb('documentary'),fanart=fanart  ))

    elif item.extra == 'torrents':
        itemlist.append(item.clone( channel='filters', action='channels_excluded', title=' - [COLOR tomato]Excluir[/COLOR] canales [COLOR blue][B]Torrent[/COLOR][COLOR tomato] de [COLOR yellow]Películas y/ó Series[/B][/COLOR]', extra='torrents', thumbnail=config.get_thumb('torrents'), fanart=fanart ))

        if channels_search_excluded_mixed:
            itemlist.append(item.clone( channel='filters', action='channels_excluded_del', title=' - [COLOR coral][B]Anular los canales [COLOR blue]Torrent[/COLOR][COLOR coral]excluidos de Películas y/ó Series[/B][/COLOR]', extra='torrents', thumbnail=config.get_thumb('torrents'), fanart=fanart ))

    else:
        itemlist.append(item.clone( channel='filters', action='channels_excluded', title=' - [COLOR tomato]Excluir[/COLOR] canales de [COLOR green][B]Todos[/B][/COLOR]', extra='all', thumbnail=config.get_thumb('stack'), fanart=fanart ))

        if channels_search_excluded_all:
            itemlist.append(item.clone( channel='filters', action='channels_excluded_del', title=' - [COLOR coral][B]Anular los canales excluidos de [COLOR green]Todos[/B][/COLOR]', extra='all', thumbnail=config.get_thumb('stack'), fanart=fanart ))

    itemlist.append(item.clone( action='', title= '[B]Preferencias:[/B]', folder=False, text_color='goldenrod' ))

    itemlist.append(item.clone( channel='actions', title=' - [COLOR chocolate]Ajustes[/COLOR] categorías ([COLOR tan][B]Menú[/B][/COLOR], [COLOR gold][B]Canales[/B][/COLOR], [COLOR red][B]Proxies[/B][/COLOR] y [COLOR yellow][B]Buscar[/B][/COLOR])', action = 'open_settings', thumbnail=config.get_thumb('settings'), fanart=fanart ))

    return itemlist


def show_infos(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][B]PERSONALIZAR Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_search', title=' - [COLOR green][B]Información [COLOR yellow]Búsquedas[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_audios', title= ' - [COLOR green][B]Información[/B][/COLOR] [COLOR cyan][B]Idiomas[/B][/COLOR] en los Audios de los Vídeos', thumbnail=config.get_thumb('news') ))

    if config.get_setting('mnu_torrents', default=True):
        itemlist.append(item.clone( channel='helper', action='show_help_semillas', title= ' - [COLOR green][B]Información[/B][/COLOR] archivos Torrent [COLOR gold][B]Semillas[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_canales', title= ' - [COLOR green][B]Información[/B][/COLOR] Resumen y Distribución Canales', thumbnail=config.get_thumb('stack') ))

    if con_incidencias:
        itemlist.append(item.clone( channel='submnuteam', action='resumen_incidencias', title=' - [COLOR green][B]Información[/B][/COLOR] Canales[COLOR tan][B] Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    if no_accesibles:
        itemlist.append(item.clone( channel='submnuteam', action='resumen_no_accesibles', title= ' - [COLOR green][B]Información[/B][/COLOR] Canales[COLOR indianred][B] No Accesibles[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    if con_problemas:
        itemlist.append(item.clone( channel='submnuteam', action='resumen_con_problemas', title=' - [COLOR green][B]Información[/B][/COLOR] Canales[COLOR tomato][B] Con Problemas[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list_temporaries', title= ' - Qué canales están [COLOR darkcyan][B]Temporalmente[/B][/COLOR] inactivos', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='filters', action='no_actives', title= ' - Qué canales [COLOR goldenrod][B]Nunca[/B][/COLOR] intervendrán en las búsquedas', no_searchables = True, thumbnail=config.get_thumb('stack'), fanart=fanart ))

    return itemlist


def show_infos_proxies(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR salmon][B]PROXIES Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_proxies', title= ' - [COLOR green][B]Información[/B][/COLOR] Uso de [COLOR red][B]Proxies[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_providers', title= ' - [COLOR green][B]Información[/B][/COLOR] [COLOR magenta][B]Proveedores[/B][/COLOR] de Proxies', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_providers2', title= ' - [COLOR green][B]Información[/B][/COLOR] Lista [COLOR aqua][B]Ampliada[/B][/COLOR] Proveedores de proxies', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_recommended', title= ' - Qué [COLOR magenta][B]Proveedores[/B][/COLOR] de proxies están [COLOR lime][B]Recomendados[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    return itemlist


def _refresh_menu(item):
    platformtools.dialog_notification(config.__addon_name, 'Refrescando [B][COLOR %s]caché Menú[/COLOR][/B]' % color_exec)
    platformtools.itemlist_refresh()


def _marcar_canal(item):
    config.set_setting('status', item.estado, item.from_channel)

    if not item.module_search: _refresh_menu(item)


def _poner_no_searchable(item):
    platformtools.dialog_notification(config.__addon_name + '[B][COLOR yellow] ' + item.from_channel.capitalize() + '[/COLOR][/B]', '[B][COLOR violet]Excluyendo de búsquedas[/COLOR][/B]')

    config.set_setting('no_searchable', True, item.from_channel)

    if not item.module_search: _refresh_menu(item)

def _quitar_no_searchable(item):
    platformtools.dialog_notification(config.__addon_name + '[B][COLOR yellow] ' + item.from_channel.capitalize() + '[/COLOR][/B]', '[B][COLOR violet]Incluyendo en búsquedas[/COLOR][/B]')

    config.set_setting('no_searchable', False, item.from_channel)

    if not item.module_search: _refresh_menu(item)


def _channels_included(item):
    logger.info()

    from modules import filters

    item.extra = 'included'
    item.settings = True

    incluidos = filters.channels_excluded(item)

    if incluidos:
        import time
        time.sleep(5)

        platformtools.itemlist_refresh()

        if str(incluidos) == '[]': incluidos = ''

        config.set_setting(cfg_search_included, incluidos)

def _channels_included_del(item):
    logger.info()

    from modules import filters

    item.extra = 'included'
    item.only_one = False

    filters.channels_excluded_del(item)

def _channels_included_del_one(item):
    logger.info()

    from modules import filters

    item.extra = 'included'
    item.only_one = True
	
    filters.channels_excluded_del(item)


def _channels_excluded(item):
    logger.info()

    from modules import filters

    item.extra = 'excludded'

    item.settings = True

    excluidos = filters.channels_excluded(item)

    if excluidos:
        import time
        time.sleep(5)

        platformtools.itemlist_refresh()

        if str(excluidos) == '[]': excluidos = ''

        config.set_setting(cfg_search_excluded_all, excluidos)

def _channels_excluded_del(item):
    logger.info()

    from modules import filters

    item.extra = 'all'
    item.only_one = False

    filters.channels_excluded_del(item)

def _channels_excluded_del_movies(item):
    logger.info()

    from modules import filters

    item.extra = 'movies'
    item.only_one = False

    filters.channels_excluded_del(item)

def _channels_excluded_del_tvshows(item):
    logger.info()

    from modules import filters

    item.extra = 'tvshows'
    item.only_one = False

    filters.channels_excluded_del(item)

def _channels_excluded_del_documentaries(item):
    logger.info()

    from modules import filters

    item.extra = 'documentaries'
    item.only_one = False

    filters.channels_excluded_del(item)

def _channels_excluded_del_torrents(item):
    logger.info()

    from modules import filters

    item.extra = 'torrents'
    item.only_one = False

    filters.channels_excluded_del(item)

def _channels_excluded_del_mixed(item):
    logger.info()

    from modules import filters

    item.extra = 'mixed'
    item.only_one = False

    filters.channels_excluded_del(item)


def _dominios(item):
    logger.info()

    from modules import domains

    if item.from_channel == 'hdfull':
        from channels import hdfull

        item.channel = 'hdfull'
        hdfull.configurar_dominio(item)

    else:
        _dominio_memorizado(item)


def _dominio_vigente(item):
    from modules import domains

    item.desde_el_canal = True

    if item.from_channel == 'dontorrents': domains.last_domain_dontorrents(item)

    elif item.from_channel == 'hdfull': domains.last_domain_hdfull(item)

    else:
        domains.manto_domain_common(item, item.from_channel, item.from_channel.capitalize())


def _dominio_memorizado(item):
    from modules import domains

    if item.from_channel == 'animeflv': domains.manto_domain_animeflv(item)

    elif item.from_channel == 'animeonline': domains.manto_domain_animeonline(item)

    elif item.from_channel == 'animeyt': domains.manto_domain_animeyt(item)

    elif item.from_channel == 'cinecalidad': domains.manto_domain_cinecalidad(item)

    elif item.from_channel == 'cinecalidadla': domains.manto_domain_cinecalidadla(item)

    elif item.from_channel == 'cinecalidadlol': domains.manto_domain_cinecalidadlol(item)

    elif item.from_channel == 'cuevana2': domains.manto_domain_cuevana2(item)

    elif item.from_channel == 'cuevana2esp': domains.manto_domain_cuevana2esp(item)

    elif item.from_channel == 'cuevana3pro': domains.manto_domain_cuevana3pro(item)

    elif item.from_channel == 'divxtotal': domains.manto_domain_divxtotal(item)

    elif item.from_channel == 'dontorrents': domains.manto_domain_dontorrents(item)

    elif item.from_channel == 'dontorrentsin': domains.manto_domain_dontorrentsin(item)

    elif item.from_channel == 'elifilms': domains.manto_domain_elifilms(item)

    elif item.from_channel == 'elitetorrent': domains.manto_domain_elitetorrent(item)

    elif item.from_channel == 'elitetorrentnz': domains.manto_domain_elitetorrentnz(item)

    elif item.from_channel == 'ennovelastv': domains.manto_domain_ennovelastv(item)

    elif item.from_channel == 'entrepeliculasyseries': domains.manto_domain_entrepeliculasyseries(item)

    elif item.from_channel == 'gnula': domains.manto_domain_gnula(item)

    elif item.from_channel == 'gnula24': domains.manto_domain_gnula24(item)

    elif item.from_channel == 'gnula24h': domains.manto_domain_gnula24h(item)

    elif item.from_channel == 'grantorrent': domains.manto_domain_grantorrent(item)

    elif item.from_channel == 'hdfull': domains.manto_domain_hdfull(item)

    elif item.from_channel == 'henaojara': domains.manto_domain_henaojara(item)

    elif item.from_channel == 'homecine': domains.manto_domain_homecine(item)

    elif item.from_channel == 'mejortorrentapp': domains.manto_domain_mejortorrentapp(item)

    elif item.from_channel == 'mejortorrentnz': domains.manto_domain_mejortorrentnz(item)

    elif item.from_channel == 'mitorrent': domains.manto_domain_mitorrent(item)

    elif item.from_channel == 'peliculaspro': domains.manto_domain_peliculaspro(item)

    elif item.from_channel == 'pelisforte': domains.manto_domain_pelisforte(item)

    elif item.from_channel == 'pelismart': domains.manto_domain_pelismart(item)

    elif item.from_channel == 'pelispanda': domains.manto_domain_pelispanda(item)

    elif item.from_channel == 'pelispediaws': domains.manto_domain_pelispediaws(item)

    elif item.from_channel == 'pelisplushd': domains.manto_domain_pelisplushd(item)

    elif item.from_channel == 'pelisplushdlat': domains.manto_domain_pelisplushdlat(item)

    elif item.from_channel == 'pelisplushdnz': domains.manto_domain_pelisplushdnz(item)

    elif item.from_channel == 'pgratishd': domains.manto_domain_pgratishd(item)

    elif item.from_channel == 'poseidonhd2': domains.manto_domain_poseidonhd2(item)

    elif item.from_channel == 'series24': domains.manto_domain_series24(item)

    elif item.from_channel == 'serieskao': domains.manto_domain_serieskao(item)

    elif item.from_channel == 'seriespapayato': domains.manto_domain_seriespapayato(item)

    elif item.from_channel == 'seriesplus': domains.manto_domain_seriesplus(item)

    elif item.from_channel == 'srnovelas': domains.manto_domain_srnovelas(item)

    elif item.from_channel == 'subtorrents': domains.manto_domain_subtorrents(item)

    elif item.from_channel == 'todotorrents': domains.manto_domain_todotorrents(item)

    elif item.from_channel == 'vernovelas': domains.manto_domain_vernovelas(item)

    elif item.from_channel == 'veronline': domains.manto_domain_veronline(item)

    else:
        platformtools.dialog_notification(config.__addon_name + '[B][COLOR yellow] ' + item.from_channel.capitalize() + '[/COLOR][/B]', '[B][COLOR %s]Ajuste No Permitido[/B][/COLOR]' % color_alert)


def _credenciales(item):
    if item.from_channel == 'hdfull':
        cfg_user_channel = 'channel_hdfull_hdfull_username'
        cfg_pass_channel = 'channel_hdfull_hdfull_password'

        if not config.get_setting(cfg_user_channel, default='') or not config.get_setting(cfg_pass_channel, default=''):
            platformtools.dialog_notification(config.__addon_name + '[B][COLOR yellow] ' + item.from_channel.capitalize() + '[/COLOR][/B]', '[B][COLOR   %s]HdFull Faltan credenciales[/B][/COLOR]' % color_alert)
            return

        _credenciales_hdfull(item)

    else:
        platformtools.dialog_notification(config.__addon_name + '[B][COLOR yellow] ' + item.from_channel.capitalize() + '[/COLOR][/B]', '[B][COLOR %s]Falta _Credenciales[/B][/COLOR]' % color_alert)


def _credenciales_hdfull(item):
    logger.info()

    cfg_user_channel = 'channel_hdfull_hdfull_username'
    cfg_pass_channel = 'channel_hdfull_hdfull_password'

    if not config.get_setting(cfg_user_channel, default='') or not config.get_setting(cfg_pass_channel, default=''):
        platformtools.dialog_notification(config.__addon_name + '[B][COLOR yellow] ' + item.from_channel.capitalize() + '[/COLOR][/B]', '[B][COLOR   %s]HdFull Faltan credenciales[/B][/COLOR]' % color_alert)
        return

    from core import jsontools

    channel_json = 'hdfull.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name + ' - HdFull', el_canal + '[/COLOR][/B]')
       return

    name = params['name']

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] ' + name) % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    from channels import hdfull

    item.channel = 'hdfull'

    if not config.get_setting('hdfull_login', 'hdfull', default=False): hdfull.logout(item)

    result = hdfull.login('')

    if result: platformtools.dialog_notification(config.__addon_name + ' - HdFull', '[COLOR %s][B]Login Correcto [/COLOR][/B]' % color_avis)
    else: platformtools.dialog_notification(config.__addon_name + ' - HdFull', '[COLOR %s][B]Login Incorrecto [/COLOR][/B]' % color_alert)

    if item.from_channel: _refresh_menu(item)


def _proxies(item):
    logger.info()

    refrescar = True

    if item.from_channel == 'allpeliculasse':
        from channels import allpeliculasse
        item.channel = 'allpeliculasse'
        allpeliculasse.configurar_proxies(item)

        if config.get_setting('channel_allpeliculasse_proxies') is None: refrescar = False

    elif item.from_channel == 'animejl':
        from channels import animejl
        item.channel = 'animejl'
        animejl.configurar_proxies(item)

        if config.get_setting('channel_animejl_proxies') is None: refrescar = False

    elif item.from_channel == 'animeonline':
        from channels import animeonline
        item.channel = 'animeonline'
        animeonline.configurar_proxies(item)

        if config.get_setting('channel_animeonline_proxies') is None: refrescar = False

    elif item.from_channel == 'cine24h':
        from channels import cine24h
        item.channel = 'cine24h'
        cine24h.configurar_proxies(item)

        if config.get_setting('channel_cine24h_proxies') is None: refrescar = False

    elif item.from_channel == 'cinecalidad':
        from channels import cinecalidad
        item.channel = 'cinecalidad'
        cinecalidad.configurar_proxies(item)

        if config.get_setting('channel_cinecalidad_proxies') is None: refrescar = False

    elif item.from_channel == 'cinecalidadla':
        from channels import cinecalidadla
        item.channel = 'cinecalidadla'
        cinecalidadla.configurar_proxies(item)

        if config.get_setting('channel_cinecalidadla_proxies') is None: refrescar = False

    elif item.from_channel == 'cinecalidadlol':
        from channels import cinecalidadlol
        item.channel = 'cinecalidadlol'
        cinecalidadlol.configurar_proxies(item)

        if config.get_setting('channel_cinecalidadlol_proxies') is None: refrescar = False

    elif item.from_channel == 'cinehdplus':
        from channels import cinehdplus
        item.channel = 'cinehdplus'
        cinehdplus.configurar_proxies(item)

        if config.get_setting('channel__cinehdplusproxies') is None: refrescar = False

    elif item.from_channel == 'cinemitas':
        from channels import cinemitas
        item.channel = 'cinemitas'
        cinemitas.configurar_proxies(item)

        if config.get_setting('channel_cinemitas_proxies') is None: refrescar = False

    elif item.from_channel == 'cineplay':
        from channels import cineplay
        item.channel = 'cineplay'
        cineplay.configurar_proxies(item)

        if config.get_setting('channel_cineplay_proxies') is None: refrescar = False

    elif item.from_channel == 'cuevana2':
        from channels import cuevana2
        item.channel = 'cuevana2'
        cuevana2.configurar_proxies(item)

        if config.get_setting('channel_cuevana2_proxies') is None: refrescar = False

    elif item.from_channel == 'cuevana2esp':
        from channels import cuevana2esp
        item.channel = 'cuevana2esp'
        cuevana2esp.configurar_proxies(item)

        if config.get_setting('channel_cuevana2esp_proxies') is None: refrescar = False

    elif item.from_channel == 'cuevana3pro':
        from channels import cuevana3pro
        item.channel = 'cuevana3pro'
        cuevana3pro.configurar_proxies(item)

        if config.get_setting('channel_cuevana3pro_proxies') is None: refrescar = False

    elif item.from_channel == 'cuevana3run':
        from channels import cuevana3run
        item.channel = 'cuevana3pro'
        cuevana3run.configurar_proxies(item)

        if config.get_setting('channel_cuevana3run_proxies') is None: refrescar = False

    elif item.from_channel == 'detodo':
        from channels import detodo
        item.channel = 'detodo'
        detodo.configurar_proxies(item)

        if config.get_setting('channel_detodo_proxies') is None: refrescar = False

    elif item.from_channel == 'divxatope':
        from channels import divxatope
        item.channel = 'divxatope'
        divxatope.configurar_proxies(item)

        if config.get_setting('channel_divxatope_proxies') is None: refrescar = False

    elif item.from_channel == 'divxtotal':
        from channels import divxtotal
        item.channel = 'divxtotal'
        divxtotal.configurar_proxies(item)

        if config.get_setting('channel_divxtotal_proxies') is None: refrescar = False

    elif item.from_channel == 'dontorrents':
        from channels import dontorrents
        item.channel = 'dontorrents'
        dontorrents.configurar_proxies(item)

        if config.get_setting('channel_dontorrents_proxies') is None: refrescar = False

    elif item.from_channel == 'dontorrentsin':
        from channels import dontorrentsin
        item.channel = 'dontorrentsin'
        dontorrentsin.configurar_proxies(item)

        if config.get_setting('channel_dontorrentsin_proxies') is None: refrescar = False

    elif item.from_channel == 'doramasyt':
        from channels import doramasyt
        item.channel = 'doramasyt'
        doramasyt.configurar_proxies(item)

        if config.get_setting('channel_doramasyt_proxies') is None: refrescar = False

    elif item.from_channel == 'dpeliculas':
        from channels import dpeliculas
        item.channel = 'dpeliculas'
        dpeliculas.configurar_proxies(item)

        if config.get_setting('channel_dpeliculas_proxies') is None: refrescar = False

    elif item.from_channel == 'elifilms':
        from channels import elifilms
        item.channel = 'elifilms'
        elifilms.configurar_proxies(item)

        if config.get_setting('channel_elifilms_proxies') is None: refrescar = False

    elif item.from_channel == 'elitedivx':
        from channels import elitedivx
        item.channel = 'elitedivx'
        elitedivx.configurar_proxies(item)

        if config.get_setting('channel_elitedivx_proxies') is None: refrescar = False

    elif item.from_channel == 'entrepeliculasyseries':
        from channels import entrepeliculasyseries
        item.channel = 'entrepeliculasyseries'
        entrepeliculasyseries.configurar_proxies(item)

        if config.get_setting('channel_entrepeliculasyseries_proxies') is None: refrescar = False

    elif item.from_channel == 'estrenoscinesaa':
        from channels import estrenoscinesaa
        item.channel = 'estrenoscinesaa'
        estrenoscinesaa.configurar_proxies(item)

        if config.get_setting('channel_estrenoscinesaa_proxies') is None: refrescar = False

    elif item.from_channel == 'eztv':
        from channels import eztv
        item.channel = 'eztv'
        eztv.configurar_proxies(item)

        if config.get_setting('channel_eztv_proxies') is None: refrescar = False

    elif item.from_channel == 'filmoves':
        from channels import filmoves
        item.channel = 'filmoves'
        filmoves.configurar_proxies(item)

        if config.get_setting('channel_filmoves_proxies') is None: refrescar = False

    elif item.from_channel == 'flixcorn':
        from channels import flixcorn
        item.channel = 'flixcorn'
        flixcorn.configurar_proxies(item)

        if config.get_setting('channel_flixcorn_proxies') is None: refrescar = False

    elif item.from_channel == 'gnula':
        from channels import gnula
        item.channel = 'gnula'
        gnula.configurar_proxies(item)

        if config.get_setting('channel_gnula_proxies') is None: refrescar = False

    elif item.from_channel == 'gnula24':
        from channels import gnula24
        item.channel = 'gnula24'
        gnula24.configurar_proxies(item)

        if config.get_setting('channel_gnula24_proxies') is None: refrescar = False

    elif item.from_channel == 'gnula24h':
        from channels import gnula24h
        item.channel = 'gnula24h'
        gnula24h.configurar_proxies(item)

        if config.get_setting('channel_gnula24h_proxies') is None: refrescar = False

    elif item.from_channel == 'gnulacenter':
        from channels import gnulacenter
        item.channel = 'gnulacenter'
        gnulacenter.configurar_proxies(item)

        if config.get_setting('channel_gnulacenter_proxies') is None: refrescar = False

    elif item.from_channel == 'grantorrent':
        from channels import grantorrent
        item.channel = 'grantorrent'
        grantorrent.configurar_proxies(item)

        if config.get_setting('channel_grantorrent_proxies') is None: refrescar = False

    elif item.from_channel == 'hdcinema':
        from channels import hdcinema
        item.channel = 'hdcinema'
        hdcinema.configurar_proxies(item)

        if config.get_setting('channel_hdcinema_proxies') is None: refrescar = False

    elif item.from_channel == 'hdfull':
        from channels import hdfull
        item.channel = 'hdfull'
        hdfull.configurar_proxies(item)

        if config.get_setting('channel_hdfull_proxies') is None: refrescar = False

    elif item.from_channel == 'henaojara':
        from channels import henaojara
        item.channel = 'henaojara'
        henaojara.configurar_proxies(item)

        if config.get_setting('channel_henaojara_proxies') is None: refrescar = False

    elif item.from_channel == 'homecine':
        from channels import homecine
        item.channel = 'homecine'
        homecine.configurar_proxies(item)

        if config.get_setting('channel_homecine_proxies') is None: refrescar = False

    elif item.from_channel == 'jkanime':
        from channels import jkanime
        item.channel = 'jkanime'
        jkanime.configurar_proxies(item)

        if config.get_setting('channel_jkanime_proxies') is None: refrescar = False

    elif item.from_channel == 'joinclub':
        from channels import joinclub
        item.channel = 'joinclub'
        joinclub.configurar_proxies(item)

        if config.get_setting('channel_joinclub_proxies') is None: refrescar = False

    elif item.from_channel == 'latanime':
        from channels import latanime
        item.channel = 'latanime'
        latanime.configurar_proxies(item)

        if config.get_setting('channel_latanime_proxies') is None: refrescar = False

    elif item.from_channel == 'lilatorrent':
        from channels import lilatorrent
        item.channel = 'lilatorrent'
        lilatorrent.configurar_proxies(item)

        if config.get_setting('channel_lilatorrent_proxies') is None: refrescar = False

    elif item.from_channel == 'megaserie':
        from channels import megaserie
        item.channel = 'megaserie'
        megaserie.configurar_proxies(item)

        if config.get_setting('channel_megaserie_proxies') is None: refrescar = False

    elif item.from_channel == 'mejortorrentapp':
        from channels import mejortorrentapp
        item.channel = 'mejortorrentapp'
        mejortorrentapp.configurar_proxies(item)

        if config.get_setting('channel_mejortorrentapp_proxies') is None: refrescar = False

    elif item.from_channel == 'mejortorrentnz':
        from channels import mejortorrentnz
        item.channel = 'mejortorrentnz'
        mejortorrentnz.configurar_proxies(item)

        if config.get_setting('channel_mejortorrentnz_proxies') is None: refrescar = False

    elif item.from_channel == 'moviesdvdr':
        from channels import moviesdvdr
        item.channel = 'moviesdvdr'
        moviesdvdr.configurar_proxies(item)

        if config.get_setting('channel_moviesdvdr_proxies') is None: refrescar = False

    elif item.from_channel == 'mundodonghua':
        from channels import mundodonghua
        item.channel = 'mundodonghua'
        mundodonghua.configurar_proxies(item)

        if config.get_setting('channel_mundodonghua_proxies') is None: refrescar = False

    elif item.from_channel == 'mundodonghuaxyz':
        from channels import mundodonghuaxyz
        item.channel = 'mundodonghuaxyz'
        mundodonghuaxyz.configurar_proxies(item)

        if config.get_setting('channel_mundodonghuaxyz_proxies') is None: refrescar = False

    elif item.from_channel == 'naranjatorrent':
        from channels import naranjatorrent
        item.channel = 'naranjatorrent'
        naranjatorrent.configurar_proxies(item)

        if config.get_setting('channel_naranjatorrent_proxies') is None: refrescar = False

    elif item.from_channel == 'onlinetv':
        from channels import onlinetv
        item.channel = 'onlinetv'
        onlinetv.configurar_proxies(item)

        if config.get_setting('channel__onlinetv_proxies') is None: refrescar = False

    elif item.from_channel == 'papayaseries':
        from channels import papayaseries
        item.channel = 'papayaseries'
        papayaseries.configurar_proxies(item)

        if config.get_setting('channel_papayaseries_proxies') is None: refrescar = False

    elif item.from_channel == 'pasateatorrent':
        from channels import pasateatorrent
        item.channel = 'pasateatorrent'
        pasateatorrent.configurar_proxies(item)

        if config.get_setting('channel_pasateatorrent_proxies') is None: refrescar = False

    elif item.from_channel == 'pediatorrent':
        from channels import pediatorrent
        item.channel = 'pediatorrent'
        pediatorrent.configurar_proxies(item)

        if config.get_setting('channel_pediatorrent_proxies') is None: refrescar = False

    elif item.from_channel == 'peliculaspro':
        from channels import peliculaspro
        item.channel = 'peliculaspro'
        peliculaspro.configurar_proxies(item)

        if config.get_setting('channel_peliculaspro_proxies') is None: refrescar = False

    elif item.from_channel == 'pelisforte':
        from channels import pelisforte
        item.channel = 'pelisforte'
        pelisforte.configurar_proxies(item)

        if config.get_setting('channel_pelisforte_proxies') is None: refrescar = False

    elif item.from_channel == 'pelisgratishd':
        from channels import pelisgratishd
        item.channel = 'pelisgratishd'
        pelisgratishd.configurar_proxies(item)

        if config.get_setting('channel_pelisgratishd_proxies') is None: refrescar = False

    elif item.from_channel == 'pelispanda':
        from channels import pelispanda
        item.channel = 'pelispanda'
        pelispanda.configurar_proxies(item)

        if config.get_setting('channel_pelispanda_proxies') is None: refrescar = False

    elif item.from_channel == 'pelispediais':
        from channels import pelispediais
        item.channel = 'pelispediais'
        pelispediais.configurar_proxies(item)

        if config.get_setting('channel_pelispediais_proxies') is None: refrescar = False

    elif item.from_channel == 'pelisplushd':
        from channels import pelisplushd
        item.channel = 'pelisplushd'
        pelisplushd.configurar_proxies(item)

        if config.get_setting('channel_pelisplushd_proxies') is None: refrescar = False

    elif item.from_channel == 'pelisplushdlat':
        from channels import pelisplushdlat
        item.channel = 'pelisplushdlat'
        pelisplushdlat.configurar_proxies(item)

        if config.get_setting('channel_pelisplushdlat_proxies') is None: refrescar = False

    elif item.from_channel == 'pelisplushdnz':
        from channels import pelisplushdnz
        item.channel = 'pelisplushdnz'
        pelisplushdnz.configurar_proxies(item)

        if config.get_setting('channel_pelisplushdnz_proxies') is None: refrescar = False

    elif item.from_channel == 'pelisyseries':
        from channels import pelisyseries
        item.channel = 'pelisyseries'
        pelisyseries.configurar_proxies(item)

        if config.get_setting('channel_pelisyseries_proxies') is None: refrescar = False

    elif item.from_channel == 'pgratishd':
        from channels import pgratishd
        item.channel = 'pgratishd'
        pgratishd.configurar_proxies(item)

        if config.get_setting('channel_pgratishd_proxies') is None: refrescar = False

    elif item.from_channel == 'plushd':
        from channels import plushd
        item.channel = 'plushd'
        plushd.configurar_proxies(item)

        if config.get_setting('channel_plushd_proxies') is None: refrescar = False

    elif item.from_channel == 'ppeliculas':
        from channels import ppeliculas
        item.channel = 'ppeliculas'
        ppeliculas.configurar_proxies(item)

        if config.get_setting('channel_ppeliculas_proxies') is None: refrescar = False

    elif item.from_channel == 'rarbg':
        from channels import rarbg
        item.channel = 'rarbg'
        rarbg.configurar_proxies(item)

        if config.get_setting('channel_rarbg_proxies') is None: refrescar = False

    elif item.from_channel == 'reinventorrent':
        from channels import reinventorrent
        item.channel = 'reinventorrent'
        reinventorrent.configurar_proxies(item)

        if config.get_setting('channel_reinventorrent_proxies') is None: refrescar = False

    elif item.from_channel == 'repelishd':
        from channels import repelishd
        item.channel = 'repelishd'
        repelishd.configurar_proxies(item)

        if config.get_setting('channel_repelishd_proxies') is None: refrescar = False

    elif item.from_channel == 'rojotorrent':
        from channels import rojotorrent
        item.channel = 'rojotorrent'
        rojotorrent.configurar_proxies(item)

        if config.get_setting('channel_rojotorrent_proxies') is None: refrescar = False

    elif item.from_channel == 'series24':
        from channels import series24
        item.channel = 'series24'
        series24.configurar_proxies(item)

        if config.get_setting('channel_series24_proxies') is None: refrescar = False

    elif item.from_channel == 'seriesonline':
        from channels import seriesonline
        item.channel = 'seriesonline'
        seriesonline.configurar_proxies(item)

        if config.get_setting('channel_seriesonline_proxies') is None: refrescar = False

    elif item.from_channel == 'seriespapayato':
        from channels import seriespapayato
        item.channel = 'seriespapayato'
        seriespapayato.configurar_proxies(item)

        if config.get_setting('channel_seriespapayato_proxies') is None: refrescar = False

    elif item.from_channel == 'seriesplus':
        from channels import seriesplus
        item.channel = 'seriesplus'
        seriesplus.configurar_proxies(item)

        if config.get_setting('channel_seriesplus_proxies') is None: refrescar = False

    elif item.from_channel == 'seriesretro':
        from channels import seriesretro
        item.channel = 'seriesretro'
        seriesretro.configurar_proxies(item)

        if config.get_setting('channel_seriesretro_proxies') is None: refrescar = False

    elif item.from_channel == 'sololatino':
        from channels import sololatino
        item.channel = 'sololatino'
        sololatino.configurar_proxies(item)

        if config.get_setting('channel_sololatino_proxies') is None: refrescar = False

    elif item.from_channel == 'srnovelas':
        from channels import srnovelas
        item.channel = 'srnovelas'
        srnovelas.configurar_proxies(item)

        if config.get_setting('channel_srnovelas_proxies') is None: refrescar = False

    elif item.from_channel == 'star':
        from channels import star
        item.channel = 'star'
        star.configurar_proxies(item)

        if config.get_setting('channel_star_proxies') is None: refrescar = False

    elif item.from_channel == 'subtorrents':
        from channels import subtorrents
        item.channel = 'subtorrents'
        subtorrents.configurar_proxies(item)

        if config.get_setting('channel_subtorrents_proxies') is None: refrescar = False

    elif item.from_channel == 'tiodonghua':
        from channels import tiodonghua
        item.channel = 'tiodonghua'
        tiodonghua.configurar_proxies(item)

        if config.get_setting('channel_tiodonghua_proxies') is None: refrescar = False

    elif item.from_channel == 'todotorrents':
        from channels import todotorrents
        item.channel = 'todotorrents'
        todotorrents.configurar_proxies(item)

        if config.get_setting('channel_todotorrents_proxies') is None: refrescar = False

    elif item.from_channel == 'tomadivx':
        from channels import tomadivx
        item.channel = 'tomadivx'
        tomadivx.configurar_proxies(item)

        if config.get_setting('channel_tomadivx_proxies') is None: refrescar = False

    elif item.from_channel == 'tubepelis':
        from channels import tubepelis
        item.channel = 'tubepelis'
        tubepelis.configurar_proxies(item)

        if config.get_setting('channel_tubepelis_proxies') is None: refrescar = False

    elif item.from_channel == 'ultrapelis':
        from channels import ultrapelis
        item.channel = 'ultrapelis'
        ultrapelis.configurar_proxies(item)

        if config.get_setting('channel_ultrapelis_proxies') is None: refrescar = False

    elif item.from_channel == 'verdetorrent':
        from channels import verdetorrent
        item.channel = 'verdetorrent'
        verdetorrent.configurar_proxies(item)

        if config.get_setting('channel_verdetorrent_proxies') is None: refrescar = False

    elif item.from_channel == 'verflix':
        from channels import verflix
        item.channel = 'verflix'
        verflix.configurar_proxies(item)

        if config.get_setting('channel_verflix_proxies') is None: refrescar = False

    elif item.from_channel == 'veronline':
        from channels import veronline
        item.channel = 'veronline'
        veronline.configurar_proxies(item)

        if config.get_setting('channel_veronline_proxies') is None: refrescar = False

    elif item.from_channel == 'verseries':
        from channels import verseries
        item.channel = 'verseries'
        verseries.configurar_proxies(item)

        if config.get_setting('channel_verseries_proxies') is None: refrescar = False

    elif item.from_channel == 'zonaleros':
        from channels import zonaleros
        item.channel = 'zonaleros'
        zonaleros.configurar_proxies(item)

        if config.get_setting('channel_zonaleros_proxies') is None: refrescar = False

    else:
        if item.channels_new_proxies:
            platformtools.dialog_notification(config.__addon_name + '[B][COLOR yellow] ' + item.from_channel.capitalize() + '[/COLOR][/B]', '[B][COLOR %s]Falta _Proxies[/B][/COLOR]' % color_alert)

            refrescar = False

    channels_unsatisfactory = config.get_setting('developer_test_channels', default='')
    if channels_unsatisfactory == 'unsatisfactory': refrescar = False

    if item.module_search: refrescar = False

    if refrescar: _refresh_menu(item)


def _search_new_proxies(item):
    if item.channels_new_proxies:
        if platformtools.dialog_yesno(config.__addon_name, '[COLOR yellow][B]Solo se tendrán en cuenta para las próximas búsquedas[/B][/COLOR]','[COLOR red][B]¿ Desea efectuar una nueva búsqueda de proxies en Todos esos canales ?[/B][/COLOR]'):
            for channel in item.channels_new_proxies:
                item.from_channel = channel
                item.module_search = True
                _proxies(item)


def _quitar_proxies(item):
    platformtools.dialog_notification(config.__addon_name + '[B][COLOR yellow] ' + item.from_channel.capitalize() + '[/COLOR][/B]', '[B][COLOR red]Quitando los proxies[/COLOR][/B]')

    config.set_setting('proxies', '', item.from_channel)

    if config.get_setting('memorize_channels_proxies', default=True):
        channels_proxies_memorized = config.get_setting('channels_proxies_memorized', default='')

        el_memorizado = "'" + item.from_channel.lower() + "'"

        if el_memorizado in str(channels_proxies_memorized):
            if (', ' + el_memorizado) in str(channels_proxies_memorized): channels_proxies_memorized = channels_proxies_memorized.replace(', ' + el_memorizado, '').strip()
            else: channels_proxies_memorized = channels_proxies_memorized.replace(el_memorizado, '').strip()

            config.set_setting('channels_proxies_memorized', channels_proxies_memorized)

    _refresh_menu(item)


def _test_webs(item):
    platformtools.dialog_notification(config.__addon_name + '[B][COLOR yellow] ' + item.from_channel.capitalize() + '[/COLOR][/B]', '[B][COLOR violet]Test web canal[/COLOR][/B]')

    config.set_setting('developer_test_channels', '')
    config.set_setting('developer_test_servers', '')

    config.set_setting('user_test_channel', '')

    from modules import tester

    try:
        tester.test_channel(item.from_channel)
    except:
        platformtools.dialog_notification(config.__addon_name + '[B][COLOR yellow] ' + item.from_channel.capitalize() + '[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Reintentelo de Nuevo[/B][/COLOR]' % color_alert)
