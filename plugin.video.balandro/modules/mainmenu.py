# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] >= 3: PY3 = True
else: PY3 = False


import os

from datetime import datetime

from platformcode import config, logger, platformtools, updater

from core.item import Item

from core import channeltools, scrapertools


color_list_prefe = config.get_setting('channels_list_prefe_color', default='gold')
color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')
color_list_inactive = config.get_setting('channels_list_inactive_color', default='gray')

color_alert = config.get_setting('notification_alert_color', default='red')
color_infor = config.get_setting('notification_infor_color', default='pink')
color_adver = config.get_setting('notification_adver_color', default='violet')
color_avis = config.get_setting('notification_avis_color', default='yellow')
color_exec = config.get_setting('notification_exec_color', default='cyan')

current_year = int(datetime.today().year)
current_month = int(datetime.today().month)


config.set_setting('ses_pin', False)


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


context_desarrollo = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_desarrollo.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR goldenrod][B]Miscelánea[/B][/COLOR]'
context_desarrollo.append({'title': tit, 'channel': 'helper', 'action': 'show_help_miscelanea'})

tit = '[COLOR %s]Ajustes categoría Team[/COLOR]' % color_exec
context_desarrollo.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_menu = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_menu.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR fuchsia][B]Preferencias Play[/B][/COLOR]'
context_menu.append({'title': tit, 'channel': 'helper', 'action': 'show_play_parameters'})

tit = '[COLOR powderblue][B]Preferencias Buscar[/B][/COLOR]'
context_menu.append({'title': tit, 'channel': 'helper', 'action': 'show_help_parameters_search'})

tit = '[COLOR %s]Ajustes categorías Menú, Play y Buscar[/COLOR]' % color_exec
context_menu.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


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

tit = '[COLOR %s][B]Quitar Todos los Proxies[/B][/COLOR]' % color_list_proxies
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

tit = '[COLOR %s][B]Quitar Todos los Proxies[/B][/COLOR]' % color_list_proxies
context_proxy_channels.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s]Ajustes categorías Menú, Canales, Dominios y Proxies[/COLOR]' % color_exec
context_proxy_channels.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_cfg_search = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_cfg_search.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR %s]Ajustes categoría Menú[/COLOR]' % color_exec
context_cfg_search.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_torrents = []

tit = '[COLOR tan][B]Preferencias Canales[/B][/COLOR]'
context_torrents.append({'title': tit, 'channel': 'helper', 'action': 'show_channels_parameters'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_torrents.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

if config.get_setting('cliente_torrent') == 'Seleccionar' or config.get_setting('cliente_torrent') == 'Ninguno':
    tit = '[COLOR %s][B]Información Motores Torrent[/B][/COLOR]' % color_infor
    context_torrents.append({'title': tit, 'channel': 'helper', 'action': 'show_help_torrents'})

tit = '[COLOR %s][B]Motores torrents instalados[/B][/COLOR]' % color_avis
context_torrents.append({'title': tit, 'channel': 'helper', 'action': 'show_clients_torrent'})

tit = '[COLOR powderblue][B]Global Configurar Proxies[/B][/COLOR]'
context_torrents.append({'title': tit, 'channel': 'proxysearch', 'action': 'proxysearch_all'})

if config.get_setting('proxysearch_excludes', default=''):
    tit = '[COLOR %s]Anular canales excluidos de Proxies[/COLOR]' % color_adver
    context_torrents.append({'title': tit, 'channel': 'proxysearch', 'action': 'channels_proxysearch_del'})

tit = '[COLOR %s]Información Proxies[/COLOR]' % color_avis
context_torrents.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

tit = '[COLOR %s][B]Quitar Todos los Proxies[/B][/COLOR]' % color_list_proxies
context_torrents.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s]Ajustes categorías Canales, Dominios, Proxies y Torrents[/COLOR]' % color_exec
context_torrents.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_parental = []

tit = '[COLOR tan][B]Preferencias Canales[/B][/COLOR]'
context_parental.append({'title': tit, 'channel': 'helper', 'action': 'show_channels_parameters'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_parental.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

if config.get_setting('adults_password'):
    tit = '[COLOR %s][B]Eliminar Pin Parental[/B][/COLOR]' % color_adver
    context_parental.append({'title': tit, 'channel': 'actions', 'action': 'adults_password_del'})
else:
    tit = '[COLOR %s][B]Información Parental[/B][/COLOR]' % color_infor
    context_parental.append({'title': tit, 'channel': 'helper', 'action': 'show_help_adults'})

    tit = '[COLOR %s][B]Establecer Pin Parental[/B][/COLOR]' % color_avis
    context_parental.append({'title': tit, 'channel': 'actions', 'action': 'adults_password'})

tit = '[COLOR powderblue][B]Global Configurar Proxies[/B][/COLOR]'
context_parental.append({'title': tit, 'channel': 'proxysearch', 'action': 'proxysearch_all'})

if config.get_setting('proxysearch_excludes', default=''):
    tit = '[COLOR %s]Anular canales excluidos de Proxies[/COLOR]' % color_adver
    context_parental.append({'title': tit, 'channel': 'proxysearch', 'action': 'channels_proxysearch_del'})

tit = '[COLOR %s]Información Proxies[/COLOR]' % color_avis
context_parental.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

tit = '[COLOR %s][B]Quitar Todos los Proxies[/B][/COLOR]' % color_list_proxies
context_parental.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s]Ajustes categorías Canales, Parental, Dominios y Proxies[/COLOR]' % color_exec
context_parental.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_desactivados = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_desactivados.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_desactivados.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR %s]Ajustes categorías Menú, Dominios y Canales[/COLOR]' % color_exec
context_desactivados.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_preferidos = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_preferidos.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_preferidos.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR %s][B]Información Preferidos[/B][/COLOR]' % color_infor
context_preferidos.append({'title': tit, 'channel': 'helper', 'action': 'show_help_tracking'})

tit = '[COLOR %s][B]Comprobar Nuevos Episodios[/B][/COLOR]' % color_adver
context_preferidos.append({'title': tit, 'channel': 'actions', 'action': 'comprobar_nuevos_episodios'})

tit = '[COLOR %s][B]Eliminar Todos los Preferidos[/B][/COLOR]' % color_alert
context_preferidos.append({'title': tit, 'channel': 'actions', 'action': 'manto_tracking_dbs'})

tit = '[COLOR %s]Ajustes categorías Menú, Dominios y Preferidos[/COLOR]' % color_exec
context_preferidos.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_descargas = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_descargas.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_descargas.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR %s][B]Información Descargas[/B][/COLOR]' % color_adver
context_descargas.append({'title': tit, 'channel': 'helper', 'action': 'show_help_descargas'})

tit = '[COLOR %s][B]Ubicación Descargas[/B][/COLOR]' % color_infor
context_descargas.append({'title': tit, 'channel': 'downloads', 'action': 'show_folder_downloads'})

tit = '[COLOR %s][B]Eliminar Todas las Descargas[/B][/COLOR]' % color_alert
context_descargas.append({'title': tit, 'channel': 'actions', 'action': 'manto_folder_downloads'})

tit = '[COLOR %s]Ajustes categoría Menú, Dominios y Descargas[/COLOR]' % color_exec
context_descargas.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


context_config = []

tit = '[COLOR tan][B]Preferencias Canales[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_channels_parameters'})

tit = '[COLOR bisque]Gestión Dominios[/COLOR]'
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_help_domains'})

tit = '[COLOR %s][B]Últimos Cambios Dominios[/B][/COLOR]' % color_exec
context_config.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR darkorange][B]Quitar Dominios Memorizados[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_domains'})

tit = '[COLOR green][B]Información Plataforma[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_plataforma'})

tit = '[COLOR %s][B]Quitar Todos los Proxies[/B][/COLOR]' % color_alert
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR olive][B]Limpiezas[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_limpiezas'})

tit = '[COLOR orange][B]Borrar Carpeta Caché[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_folder_cache'})

tit = '[COLOR %s][B]Sus Ajustes Personalizados[/B][/COLOR]' % color_avis
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_sets'})

tit = '[COLOR %s]Cookies Actuales[/COLOR]' % color_infor
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_cook'})

tit = '[COLOR %s][B]Eliminar Cookies[/B][/COLOR]' % color_infor
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_cookies'})

tit = '[COLOR %s]Sus Advanced Settings[/COLOR]' % color_adver
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_advs'})

tit = '[COLOR fuchsia][B]Eliminar Advanced Settings[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_advs'})

tit = '[COLOR mediumaquamarine][B]Restablecer Parámetros Internos[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_params'})


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

tit = '[COLOR %s][B]Quitar Todos los Proxies[/B][/COLOR]' % color_list_proxies
context_usual.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s]Ajustes categorías Canales, Dominios y Proxies[/COLOR]' % color_exec
context_usual.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})


def mainlist(item):
    logger.info()
    itemlist = []

    item.category = config.__addon_name

    if config.get_setting('developer_mode', default=False):
        itemlist.append(item.clone( channel='submnuteam', action='submnu_team', title = '[B]Desarrollo[/B]', context=context_desarrollo, thumbnail=config.get_thumb('team'), text_color='darkorange' ))

    if config.get_setting('mnu_search_proxy_channels', default=False):
        itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

    if config.get_setting('sub_mnu_favoritos', default=False):
        itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

    if current_month == 4:
        presentar = False
        if config.get_setting('mnu_simple', default=False): presentar = True
        elif config.get_setting('mnu_pelis', default=True): presentar = True
        elif config.get_setting('channels_link_pyse', default=False): presentar = True

        if presentar:
            itemlist.append(item.clone( channel='filmaffinitylists', action='_oscars', title='[B]Premios Oscar ' + str(current_year) + '[/B]', text_color='deepskyblue', thumbnail=config.get_thumb('oscars'), plot = 'Las películas nominadas/galardonadas en los premios Oscars' ))

    elif current_month == 10:
        presentar = False
        if config.get_setting('mnu_simple', default=False): presentar = True
        elif config.get_setting('mnu_series', default=True): presentar = True
        elif config.get_setting('channels_link_pyse', default=False): presentar = True

        if presentar:
            itemlist.append(item.clone( channel='filmaffinitylists', action='_emmys', title='[B]Premios Emmy ' + str(current_year) + '[/B]', text_color='hotpink', thumbnail=config.get_thumb('emmys'), plot = 'Las Series nominadas/galardonadas en los premios Emmy' ))

    elif current_month == 11:
        presentar = False
        if config.get_setting('mnu_simple', default=False): presentar = True
        elif config.get_setting('mnu_pelis', default=True): presentar = True
        elif config.get_setting('channels_link_pyse', default=False): presentar = True

        if presentar:
             itemlist.append(item.clone( channel='tmdblists', action='descubre', title='[B]Halloween[/B]', text_color='deepskyblue', extra = 27, search_type = 'movie', thumbnail=config.get_thumb('halloween'), plot = 'Películas del género Terror' ))

    elif current_month == 12:
        presentar = False
        if config.get_setting('mnu_simple', default=False): presentar = True
        elif config.get_setting('mnu_pelis', default=True): presentar = True
        elif config.get_setting('mnu_series', default=True): presentar = True
        elif config.get_setting('channels_link_pyse', default=False): presentar = True

        if presentar:
            itemlist.append(item.clone( channel='filmaffinitylists', action='_navidad', title='[B]Navidad[/B]', text_color='deepskyblue', thumbnail=config.get_thumb('navidad'), plot = 'Películas y Series del tema Navidad' ))

    if config.get_setting('sub_mnu_news', default=True):
        presentar = False
        if config.get_setting('mnu_simple', default=False): presentar = True
        elif config.get_setting('mnu_pelis', default=True): presentar = True
        elif config.get_setting('mnu_series', default=True): presentar = True
        elif config.get_setting('channels_link_pyse', default=False): presentar = True

        if presentar:
            itemlist.append(item.clone( channel='submnuctext', action='submnu_news', title='[B]Novedades[/B]', context=context_cfg_search, thumbnail=config.get_thumb('novedades'), text_color='darksalmon' ))

    if config.get_setting('sub_mnu_special', default=True):
        itemlist.append(item.clone( channel='submnuctext', action='submnu_special', title='[B]Especiales[/B]', context=context_cfg_search, extra='all', thumbnail=config.get_thumb('heart'), text_color='pink' ))

    itemlist.append(Item( channel='search', action='mainlist', title='[B]Buscar[/B]', context=context_buscar, thumbnail=config.get_thumb('search'), text_color='yellow' ))

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_preferidos', default=True):
            if config.get_setting('ord_preferidos', default=False):
                itemlist.append(item.clone( channel='tracking', action='mainlist', title='[B]Preferidos[/B]', context=context_preferidos, thumbnail=config.get_thumb('videolibrary'), text_color='wheat' ))

        if config.get_setting('mnu_desargas', default=True):
            if config.get_setting('ord_descargas', default=False):
                itemlist.append(item.clone( channel='downloads', action='mainlist', title='[B]Descargas[/B]', context=context_descargas, thumbnail=config.get_thumb('downloads'), text_color='seagreen' ))

    mnu_type = '[B][I]Menú:[/I][/B]'
    if config.get_setting('mnu_simple', default=False): mnu_type = '[B][I]Menú Simplificado:[/I][/B]'

    itemlist.append(item.clone( action='', title=mnu_type, context=context_menu, thumbnail=config.get_thumb('addon'), text_color='tan' ))

    if config.get_setting('mnu_sugeridos', default=True):
        itemlist.append(item.clone( action='channels', extra='suggested', title=' - Sugeridos', context=context_usual, thumbnail=config.get_thumb('suggested'), text_color='aquamarine' ))

    if config.get_setting('channels_link_main', default=True):
        itemlist.append(item.clone( action='channels', extra='all', title=' - Canales', context=context_usual, thumbnail=config.get_thumb('stack'), text_color='gold' ))

    if config.get_setting('channels_mnu_preferidos', default=False):
        itemlist.append(item.clone( action='channels', extra='prefereds', title=' - [B]Canales Preferidos[/B]', context=context_usual, thumbnail=config.get_thumb('stack'), text_color='coral' ))

    if config.get_setting('mnu_idiomas', default=True):
        itemlist.append(item.clone( channel='groups', action='mainlist', mnu_lang='idiomas', title=' - Idiomas', context=context_menu, thumbnail=config.get_thumb('idiomas'), text_color='yellowgreen' ))

    if config.get_setting('mnu_grupos', default=True):
        itemlist.append(item.clone( channel='groups', action='mainlist', extra='groups', title=' - Grupos', context=context_cfg_search, thumbnail=config.get_thumb('bookshelf'), text_color='magenta' ))

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_pelis', default=True):
            itemlist.append(item.clone( action='channels', extra='movies', title=' - Películas', context=context_usual, thumbnail=config.get_thumb('movie'), text_color='deepskyblue' ))

        if config.get_setting('mnu_series', default=True):
            itemlist.append(item.clone( action='channels', extra='tvshows', title=' - Series', context=context_usual, thumbnail=config.get_thumb('tvshow'), text_color='hotpink' ))

        if config.get_setting('channels_link_pyse', default=False):
           itemlist.append(item.clone( action='channels', extra='mixed', title=' - [B]Películas y Series[/B]', context=context_usual, no_docs = True, thumbnail=config.get_thumb('booklet'), text_color='teal' ))

        if config.get_setting('mnu_generos', default=True):
            plot = 'Canales con géneros cinematográficos'
            itemlist.append(item.clone( channel='submnuctext', action='submnu_genres', title= ' - Géneros', context=context_generos, plot=plot, thumbnail=config.get_thumb('genres'), text_color='thistle' ))

        if config.get_setting('mnu_documentales', default=True):
            itemlist.append(item.clone( action='channels', extra='documentaries', title=' - Documentales', context=context_usual, thumbnail=config.get_thumb('documentary'), text_color='cyan' ))

        if config.get_setting('mnu_infantiles', default=True):
            itemlist.append(item.clone( action='channels', extra='infantil', title=' - Infantiles', context=context_usual, thumbnail=config.get_thumb('booklet'), text_color='lightyellow' ))

        if config.get_setting('mnu_novelas', default=True):
            itemlist.append(item.clone( action='channels', extra='tales', title=' - Novelas', context=context_usual, thumbnail=config.get_thumb('booklet'), text_color='limegreen' ))

        if config.get_setting('mnu_torrents', default=True):
            itemlist.append(item.clone( action='channels', extra='torrents', title=' - Torrents', context=context_torrents, thumbnail=config.get_thumb('torrents'), text_color='blue' ))

        if config.get_setting('mnu_doramas', default=True):
            itemlist.append(item.clone( action='channels', extra='dorama', title=' - Doramas', context=context_usual, thumbnail=config.get_thumb('computer'), text_color='firebrick' ))

        if config.get_setting('mnu_animes', default=True):
            itemlist.append(item.clone( action='channels', extra='anime', title=' - Animes', context=context_parental, thumbnail=config.get_thumb('anime'), text_color='springgreen' ))

        if config.get_setting('mnu_adultos', default=True):
            itemlist.append(item.clone( action='channels', extra='adults', title=' - [B]Adultos[/B]', context=context_parental, thumbnail=config.get_thumb('adults'), text_color='orange' ))

        if config.get_setting('mnu_proxies', default=False):
            itemlist.append(item.clone( action='channels', extra='proxies', title=' - [B]Proxies[/B]', context=context_proxy_channels, thumbnail=config.get_thumb('stack'), text_color='red' ))

        if config.get_setting('mnu_clones', default=False):
            itemlist.append(item.clone( action='channels', extra='clones', title=' - [B]Clones[/B]', context=context_proxy_channels, thumbnail=config.get_thumb('stack'), text_color='turquoise' ))

        if config.get_setting('mnu_problematicos', default=False):
            itemlist.append(item.clone( action='channels', extra='problematics', title=' - [B]Problemáticos[/B]', context=context_desactivados, thumbnail=config.get_thumb('stack'), text_color='darkgoldenrod' ))

        if config.get_setting('mnu_desactivados', default=False):
            itemlist.append(item.clone( action='channels', extra='disableds', title=' - [B]Desactivados[/B]', context=context_desactivados, thumbnail=config.get_thumb('stack'), text_color='gray' ))

        if config.get_setting('mnu_preferidos', default=True):
            if not config.get_setting('ord_preferidos', default=False):
                itemlist.append(item.clone( channel='tracking', action='mainlist', title='[B]Preferidos[/B]', context=context_preferidos, thumbnail=config.get_thumb('videolibrary'), text_color='wheat' ))

        if config.get_setting('mnu_desargas', default=True):
            if not config.get_setting('ord_descargas', default=False):
                itemlist.append(item.clone( channel='downloads', action='mainlist', title='[B]Descargas[/B]', context=context_descargas, thumbnail=config.get_thumb('downloads'), text_color='seagreen' ))

    try: last_ver = updater.check_addon_version()
    except: last_ver = None

    if last_ver is None: last_ver = '[B][I][COLOR gray](fixes off)[/COLOR][/I][/B]'
    elif not last_ver:
        last_ver = '[B][I][COLOR %s](desfasada)[/COLOR][/I][/B]' % color_adver

        text_dev = ''
        if config.get_setting('developer_mode', default=False): text_dev = ' [COLOR darkorange][B]Desarrollo[/B][/COLOR]'

        if not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developergenres.py')):
            platformtools.dialog_notification(config.__addon_name + text_dev, '[COLOR yellow][B]Versión Desfasada del Add-On[/COLOR][/B]')
    else: last_ver = ''

    context_ayuda = []

    tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
    context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

    tit = '[COLOR bisque]Gestión Dominios[/COLOR]'
    context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'show_help_domains'})

    tit = '[COLOR %s][B]Últimos Cambios Dominios[/B][/COLOR]' % color_exec
    context_ayuda.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

    tit = '[COLOR %s][B]Información Versión[/B][/COLOR]' % color_infor
    context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'show_version'})

    last_fix = config.get_addon_version()

    if not 'desfasada' in last_ver:
        if 'fix' in last_fix:
            tit = '[COLOR %s]Información Fix[/COLOR]' % color_infor
            context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'show_last_fix'})

            tit = '[COLOR darkcyan][B]Resumen Fix[/B][/COLOR]'
            context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'resumen_fix'})

        tit = '[COLOR %s]Comprobar Actualizaciones Fix[/COLOR]' % color_avis
        context_ayuda.append({'title': tit, 'channel': 'actions', 'action': 'check_addon_updates'})

        tit = '[COLOR %s][B]Forzar Actualizaciones Fix[/B][/COLOR]' % color_adver
        context_ayuda.append({'title': tit, 'channel': 'actions', 'action': 'check_addon_updates_force'})

    tit = '[COLOR green][B]Preguntas Frecuentes[/B][/COLOR]'
    context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'show_help_faq'})

    tit = '[COLOR fuchsia][B]Temas No Contemplados[/B][/COLOR]'
    context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'show_not_contemplated'})

    tit = '[COLOR goldenrod][B]Miscelánea[/B][/COLOR]'
    context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'show_help_miscelanea'})

    tit = '[COLOR darkorange][B]Test Internet[/B][/COLOR]'
    context_ayuda.append({'title': tit, 'channel': 'actions', 'action': 'test_internet'})

    tit = '[COLOR %s][B]Test Sistema[/B][/COLOR]' % color_avis
    context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'show_test'})

    tit = '[COLOR olive][B]Limpiezas[/B][/COLOR]'
    context_ayuda.append({'title': tit, 'channel': 'actions', 'action': 'manto_limpiezas'})

    tit = '[COLOR %s][B]Log Media Center[/B][/COLOR]' % color_adver
    context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'show_log'})

    tit = '[COLOR blue][B]Log Balandro Media Center[/B][/COLOR]'
    context_ayuda.append({'title': tit, 'channel': 'submnuteam', 'action': 'balandro_log'})

    tit = '[COLOR %s]Ajustes preferencias[/COLOR]' % color_exec
    context_ayuda.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

    title = '[B]Ayuda[/B] (%s)  %s' % (config.get_addon_version().replace('.fix', '-Fix'), last_ver)

    itemlist.append(item.clone( channel='helper', action='mainlist', title=title, context=context_ayuda, thumbnail=config.get_thumb('help'), text_color='chartreuse' ))

    if not 'desfasada' in last_ver:
        if 'fix' in last_fix:
            tit = '[COLOR %s][B]Eliminar Fichero Control Fix[/B][/COLOR]' % color_alert
            context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_last_fix'})

    itemlist.append(item.clone( channel='actions', action='open_settings', title='[B]Ajustes[/B]', context=context_config, folder=False, thumbnail=config.get_thumb('settings'), text_color='chocolate' ))

    return itemlist


def channels(item):
    logger.info()
    itemlist = []

    thumb_filmaffinity = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'filmaffinity.jpg')
    thumb_tmdb = os.path.join(config.get_runtime_path(), 'resources', 'media', 'channels', 'thumb', 'tmdb.jpg')

    if item.extra == 'movies':
        if config.get_setting('mnu_search_proxy_channels', default=False):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

        if config.get_setting('sub_mnu_favoritos', default=False):
            itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

        if config.get_setting('sub_mnu_news', default=True):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_news', title='[B]Novedades[/B]', thumbnail=config.get_thumb('novedades'), text_color='darksalmon' ))

        if config.get_setting('sub_mnu_special', default=True):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_special', title='[B]Especiales[/B]', context=context_cfg_search, extra='movies', thumbnail=config.get_thumb('heart'), text_color='pink' ))

        itemlist.append(item.clone( channel='submnuctext', action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'movies', thumbnail=config.get_thumb('search'), text_color='yellow' ))

        if config.get_setting('mnu_grupos', default=True):
            itemlist.append(item.clone( channel='groups', action='mainlist', extra='groups', title='[B]Grupos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('bookshelf'), text_color='magenta' ))

        if config.get_setting('mnu_generos', default=True):
           itemlist.append(item.clone( channel='generos', action='mainlist', title= '[B]Géneros[/B]', tip_sel = 'movie', context=context_generos, thumbnail=config.get_thumb('genres'), text_color='thistle' ))

        item.category = 'Canales con Películas'
        itemlist.append(item.clone( action='', title='[B]- [I]Películas:[/I][/B]', context=context_usual, plot=item.category, thumbnail=config.get_thumb('movie'), text_color='tan' ))

        accion = 'mainlist_pelis'
        filtros = {'categories': 'movie'}

    elif item.extra == 'tvshows':
        if config.get_setting('mnu_search_proxy_channels', default=False):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

        if config.get_setting('sub_mnu_favoritos', default=False):
            itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

        if config.get_setting('sub_mnu_news', default=True):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_news', title='[B]Novedades[/B]', thumbnail=config.get_thumb('novedades'), extra = 'tvshows', text_color='darksalmon' ))

        if config.get_setting('sub_mnu_special', default=True):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_special', title='[B]Especiales[/B]', context=context_cfg_search, extra='tvshows', thumbnail=config.get_thumb('heart'), text_color='pink' ))

        itemlist.append(item.clone( channel='submnuctext', action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'tvshows', thumbnail=config.get_thumb('search'), text_color='yellow' ))

        if config.get_setting('mnu_grupos', default=True):
            itemlist.append(item.clone( channel='groups', action='mainlist', extra='groups', title='[B]Grupos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('bookshelf'), text_color='magenta' ))

        if config.get_setting('mnu_generos', default=True):
           itemlist.append(item.clone( channel='generos', action='mainlist', title= '[B]Géneros[/B]', tip_sel = 'tvshow', context=context_generos, thumbnail=config.get_thumb('genres'), text_color='thistle' ))

        item.category = 'Canales con Series'
        itemlist.append(item.clone( action='', title='[B]- [I]Series:[/I][/B]', context=context_usual, plot=item.category, thumbnail=config.get_thumb('tvshow'), text_color='tan' ))

        accion = 'mainlist_series'
        filtros = {'categories': 'tvshow'}

    elif item.extra == 'documentaries':
        if config.get_setting('mnu_search_proxy_channels', default=False):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

        if config.get_setting('sub_mnu_favoritos', default=False):
            itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

        if config.get_setting('sub_mnu_special', default=True):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_special', title='[B]Especiales[/B]', context=context_cfg_search, extra='documentaries', thumbnail=config.get_thumb('heart'), text_color='pink' ))

        itemlist.append(item.clone( channel='submnuctext', action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'documentaries', thumbnail=config.get_thumb('search'), text_color='yellow' ))

        if config.get_setting('mnu_grupos', default=True):
            itemlist.append(item.clone( channel='groups', action='mainlist', extra='groups', title='[B]Grupos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('bookshelf'), text_color='magenta' ))

        if config.get_setting('mnu_generos', default=True):
           itemlist.append(item.clone( channel='generos', action='mainlist', title= '[B]Géneros[/B]', tip_sel = 'movie', context=context_generos, thumbnail=config.get_thumb('genres'), text_color='thistle' ))

        itemlist.append(item.clone( channel='groups', action='ch_groups', title = '[B]Todos los canales con temática Documental[/B]', group = 'docs', text_color='cyan' ))

        item.category = 'Canales con Documentales'
        itemlist.append(item.clone( action='', title='[B]- [I]Documentales:[/I][/B]', context=context_usual, plot=item.category, thumbnail=config.get_thumb('documentary'), text_color='tan' ))

        accion = 'mainlist'
        filtros = {'categories': 'documentary'}

    elif item.extra == 'mixed':
        if config.get_setting('mnu_search_proxy_channels', default=False):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

        if config.get_setting('sub_mnu_favoritos', default=False):
            itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

        if config.get_setting('sub_mnu_news', default=True):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_news', title='[B]Novedades[/B]', thumbnail=config.get_thumb('novedades'), text_color='darksalmon' ))

        if config.get_setting('sub_mnu_special', default=True):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_special', title='[B]Especiales[/B]', context=context_cfg_search, extra='all', no_docs = item.no_docs, thumbnail=config.get_thumb('heart'), text_color='pink' ))

        itemlist.append(item.clone( channel='submnuctext', action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'mixed', thumbnail=config.get_thumb('search'), text_color='yellow' ))

        if config.get_setting('mnu_grupos', default=True):
            itemlist.append(item.clone( channel='groups', action='mainlist', extra='groups', title='[B]Grupos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('bookshelf'), text_color='magenta' ))

        if config.get_setting('mnu_generos', default=True):
           itemlist.append(item.clone( channel='generos', action='mainlist', title= '[B]Géneros[/B]', tip_sel = 'all', context=context_generos, thumbnail=config.get_thumb('genres'), text_color='thistle' ))

        item.category = 'Canales con Películas y Series (ambos contenidos)'
        itemlist.append(item.clone( action='', title='[B]- [I]Películas y Series:[/I][/B]', context=context_usual, plot=item.category, thumbnail=config.get_thumb('booklet'), text_color='tan' ))

        accion = 'mainlist'
        filtros = {}

    elif item.extra == 'torrents':
        cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

        if cliente_torrent == 'Seleccionar' or cliente_torrent == 'Ninguno':
            itemlist.append(item.clone( channel='actions', action='open_settings', title='[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR blue][B]Torrents)[/B][/COLOR]' + ' [COLOR fuchsia][B]Motor:[/B][/COLOR][COLOR goldenrod][B] ' + cliente_torrent.capitalize() + '[/B][/COLOR]', folder=False, thumbnail=config.get_thumb('settings') ))

        if config.get_setting('mnu_search_proxy_channels', default=False):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

        if config.get_setting('sub_mnu_favoritos', default=False):
            itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

        if config.get_setting('sub_mnu_special', default=True):
            itemlist.append(item.clone( channel='submnuctext', action='submnu_special', title='[B]Especiales[/B]', context=context_cfg_search, extra='torrents', thumbnail=config.get_thumb('heart'), text_color='pink' ))

        itemlist.append(item.clone( channel='submnuctext', action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'torrents', thumbnail=config.get_thumb('search'), text_color='yellow' ))

        if config.get_setting('mnu_grupos', default=True):
            itemlist.append(item.clone( channel='groups', action='mainlist', extra='groups', title='[B]Grupos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('bookshelf'), text_color='magenta' ))

        if config.get_setting('mnu_generos', default=True):
           itemlist.append(item.clone( channel='generos', action='mainlist', title= '[B]Géneros[/B]', tip_sel = 'movie', context=context_generos, thumbnail=config.get_thumb('genres'), text_color='thistle' ))

        itemlist.append(item.clone( channel='groups', action='ch_groups', title = '[B]Canales que pueden tener enlaces Torrents[/B]', group = 'torrents', text_color='blue' ))

        item.category = 'Canales con archivos Torrents'
        itemlist.append(item.clone( action='', title='[B]- [I]Torrents:[/I][/B]', context=context_torrents, plot=item.category, thumbnail=config.get_thumb('torrents'), text_color='tan' ))

        accion = 'mainlist'
        filtros = {'categories': 'torrent'}

    else:
        if item.extra == 'adults': pass
        elif item.extra == 'anime': pass
        elif item.extra == 'dorama': pass
        elif item.extra == 'infantil': pass
        elif item.extra == 'tales': pass

        elif not item.extra == 'groups':
            presentar = True

            if config.get_setting('mnu_proxies', default=False):
                if item.extra == 'proxies': presentar = False

            if config.get_setting('mnu_clones', default=False):
                if item.extra == 'clones': presentar = False

            if config.get_setting('mnu_problematicos', default=False):
                if item.extra == 'problematics': presentar = False

            if config.get_setting('mnu_desactivados', default=False):
                if item.extra == 'disableds': presentar = False

            if presentar:
               if config.get_setting('mnu_search_proxy_channels', default=False):
                   itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

               if config.get_setting('sub_mnu_favoritos', default=False):
                   itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

               if config.get_setting('sub_mnu_news', default=True):
                   itemlist.append(item.clone( channel='submnuctext', action='submnu_news', title='[B]Novedades[/B]', thumbnail=config.get_thumb('novedades'), text_color='darksalmon' ))

               if config.get_setting('sub_mnu_special', default=True):
                   itemlist.append(item.clone( channel='submnuctext', action='submnu_special', title='[B]Especiales[/B]', context=context_cfg_search, extra='all', thumbnail=config.get_thumb('heart'), text_color='pink' ))

               itemlist.append(item.clone( channel='submnuctext', action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'all', thumbnail=config.get_thumb('search'), text_color='yellow' ))

               if config.get_setting('mnu_grupos', default=True):
                   itemlist.append(item.clone( channel='groups', action='mainlist', extra='groups', title='[B]Grupos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('bookshelf'), text_color='magenta' ))

               if config.get_setting('mnu_generos', default=True):
                   itemlist.append(item.clone( channel='generos', action='mainlist', title= '[B]Géneros[/B]', tip_sel = 'all', context=context_generos, thumbnail=config.get_thumb('genres'), text_color='thistle' ))

        if item.extra == 'adults': item.category = 'Solo los Canales exclusivos para Adultos'
        elif item.extra == 'anime': item.category = 'Solo los Canales exclusivos de Animes'
        elif item.extra == 'dorama': item.category = 'Solo los Canales exclusivos de Doramas'
        elif item.extra == 'infantil': item.category = 'Solo los Canales exclusivos Infantiles'
        elif item.extra == 'tales': item.category = 'Solo los Canales con temática de Novelas'

        elif item.extra == 'suggested':
           item.category = 'Solo los Canales Sugeridos'
           itemlist.append(item.clone( action='', title='[B]- [I]Sugeridos:[/I][/B]', context=context_usual, plot=item.category, thumbnail=config.get_thumb('suggested'), text_color='tan' ))

        elif item.extra == 'proxies': item.category = 'Solo los Canales con Proxies Memorizados'
        elif item.extra == 'clones': item.category = 'Solo los Canales que sean Clones'

        elif item.extra == 'disableds': item.category = 'Solo los Canales que estén Desactivados'

        elif item.extra == 'problematics': item.category = 'Solo los Canales que sean Problemáticos (Predominan Sin enlaces Disponibles/Válidos/Soportados)'

        elif not item.extra == 'groups':
           if item.extra == 'prefereds':
               item.category = 'Solo los Canales Preferidos'
               itemlist.append(item.clone( action='', title='[B]- [I]Canales Preferidos:[/I][/B]', context=context_usual, plot=item.category, thumbnail=config.get_thumb('stack'), text_color='tan' ))
           else:
               item.category = 'Todos los Canales'
               itemlist.append(item.clone( action='', title='[B]- [I]Canales:[/I][/B]', context=context_usual, plot=item.category, thumbnail=config.get_thumb('stack'), text_color='tan' ))

        else: item.category = 'Canales con Agrupaciones (Novedades, Estrenos, Temáticas, Países, Años, Plataformas, Productoras, Géneros, etc.)'

        if item.extra == 'infantil':
            if config.get_setting('mnu_search_proxy_channels', default=False):
                itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

            if config.get_setting('sub_mnu_favoritos', default=False):
                itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

            if config.get_setting('sub_mnu_special', default=True):
                itemlist.append(item.clone( channel='submnuctext', action='submnu_special', title='[B]Especiales[/B]', context=context_cfg_search, extra='infantil', thumbnail=config.get_thumb('heart'), text_color='pink' ))

            itemlist.append(item.clone( channel='submnuctext', action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'infantil', thumbnail=config.get_thumb('search'), text_color='yellow' ))

            if config.get_setting('mnu_grupos', default=True):
                itemlist.append(item.clone( channel='groups', action='mainlist', extra='groups', title='[B]Grupos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('bookshelf'), text_color='magenta' ))

            if config.get_setting('mnu_generos', default=True):
                itemlist.append(item.clone( channel='generos', action='mainlist', title= '[B]Géneros[/B]', tip_sel = 'all', context=context_generos, thumbnail=config.get_thumb('genres'), text_color='thistle' ))

            itemlist.append(item.clone( channel='groups', action='ch_groups', title = '[B]Todos los canales con contenido Infantil[/B]', group = 'kids', text_color='lightyellow' ))

            itemlist.append(item.clone( action='', title='[B]- [I]Infantiles:[/I][/B]', context=context_usual, plot=item.category, thumbnail=config.get_thumb('booklet'), text_color='tan' ))

        if item.extra == 'tales':
            if config.get_setting('mnu_search_proxy_channels', default=False):
                itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

            if config.get_setting('sub_mnu_favoritos', default=False):
                itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

            if config.get_setting('sub_mnu_special', default=True):
                itemlist.append(item.clone( channel='submnuctext', action='submnu_special', title='[B]Especiales[/B]', context=context_cfg_search, extra='tales', thumbnail=config.get_thumb('heart'), text_color='pink' ))

            itemlist.append(item.clone( channel='submnuctext', action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'tales', thumbnail=config.get_thumb('search'), text_color='yellow' ))

            itemlist.append(item.clone( channel='groups', action='ch_groups', title = '[B]Todos los canales con contenido de Novelas[/B]', group = 'tales', text_color='limegreen' ))

            itemlist.append(item.clone( action='', title='[B]- [I]Novelas:[/I][/B]', context=context_usual, plot=item.category, thumbnail=config.get_thumb('booklet'), text_color='tan' ))

        if item.extra == 'dorama':
            if config.get_setting('mnu_search_proxy_channels', default=False):
                itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

            if config.get_setting('sub_mnu_favoritos', default=False):
                itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

            itemlist.append(item.clone( channel='submnuctext', action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'dorama', thumbnail=config.get_thumb('search'), text_color='yellow' ))

            itemlist.append(item.clone( channel='groups', action='ch_groups', title = '[B]Todos los canales con contenido Dorama[/B]', group = 'dorama', text_color='firebrick' ))

            itemlist.append(item.clone( action='', title='[B]- [I]Doramas:[/I][/B]', context=context_usual, plot=item.category, thumbnail=config.get_thumb('computer'), text_color='tan' ))

        if item.extra == 'adults' or item.extra == 'anime':
            if not config.get_setting('adults_password'):
                itemlist.append(item.clone( channel='helper', action='show_help_adults', title='[COLOR green][B]Información [COLOR goldenrod]Parental[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

                presentar = True

                if item.extra == 'anime':
                    if not config.get_setting('animes_password'): presentar = False

                if presentar:
                    itemlist.append(item.clone( channel='actions', action='adults_password', title= '[COLOR goldenrod][B]Establecer[/B][/COLOR] un PIN Parental', thumbnail=config.get_thumb('pencil') ))
            else:
                presentar = True

                if item.extra == 'anime':
                    if not config.get_setting('animes_password'): presentar = False

                if presentar:
                    itemlist.append(item.clone( channel='helper', action='show_pin_parental', title= '[COLOR springgreen][B]Ver[/B][/COLOR] el PIN Parental', thumbnail=config.get_thumb('pencil') ))

                    itemlist.append(item.clone( channel='actions', action='adults_password_del', title= '[COLOR red][B]Eliminar[/B][/COLOR] PIN parental', erase = True, folder=False, thumbnail=config.get_thumb('pencil') ))

            if item.extra == 'anime':
                if config.get_setting('mnu_search_proxy_channels', default=False):
                    itemlist.append(item.clone( channel='submnuctext', action='submnu_search', title='[B]Buscar Nuevos Proxies[/B]', context=context_proxy_channels, only_options_proxies = True, thumbnail=config.get_thumb('flame'), text_color='red' ))

            if config.get_setting('sub_mnu_favoritos', default=False):
                itemlist.append(item.clone( channel='favoritos', action='mainlist', title='[B]Favoritos[/B]', context=context_cfg_search, thumbnail=config.get_thumb('star'), text_color='plum' ))

            if item.extra == 'adults':
                itemlist.append(Item( channel='search', action='search', title='[B]Buscar [COLOR orange]vídeo[/COLOR][/B] ...', extra = '+18', search_video = 'adult', thumbnail=config.get_thumb('search'), text_color='yellow' ))

                itemlist.append(item.clone( channel='groups', action='ch_groups', title = '[B]Todos los canales que pueden tener vídeos para Adultos[/B]', group = 'adults', text_color='orange' ))

                itemlist.append(item.clone( action='', title='[B]- [I]Adultos:[/I][/B]', context=context_parental, plot=item.category, thumbnail=config.get_thumb('adults'), text_color='tan' ))

            if item.extra == 'anime':
                itemlist.append(item.clone( channel='submnuctext', action='submnu_channels', title='[B]Buscar[/B]', context=context_buscar, extra = 'anime', thumbnail=config.get_thumb('search'), text_color='yellow' ))

                itemlist.append(item.clone( channel='groups', action='ch_groups', title = '[B]Todos los canales con contenido Anime[/B]', group = 'anime', text_color='springgreen' ))

                itemlist.append(item.clone( action='', title='[B]- [I]Animes:[/I][/B]', context=context_parental, plot=item.category, thumbnail=config.get_thumb('anime'), text_color='tan' ))

        if item.extra == 'proxies' or item.extra == 'clones' or item.extra == 'problematics' or item.extra == 'disableds':
            itemlist.append(item.clone( channel='actions', action='open_settings', title='[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR tan][B]Menú)[/B][/COLOR]', context=context_config, folder=False, thumbnail=config.get_thumb('settings') ))

            if item.extra == 'proxies':
                itemlist.append(item.clone( action='', title='[B]- [I]Proxies:[/I][/B]', context=context_proxy_channels, plot=item.category, thumbnail=config.get_thumb('stack'), text_color='tan' ))

            if item.extra == 'clones':
                itemlist.append(item.clone( action='', title='[B]- [I]Clones:[/I][/B]', context=context_proxy_channels, plot=item.category, thumbnail=config.get_thumb('stack'), text_color='turquoise' ))

            if item.extra == 'problematics':
                itemlist.append(item.clone( action='', title='[B]- [I]Problemáticos:[/I][/B]', context=context_desactivados, plot=item.category, thumbnail=config.get_thumb('stack'), text_color='tan' ))

            if item.extra == 'disableds':
                itemlist.append(item.clone( action='', title='[B]- [I]Desactivados:[/I][/B]', context=context_desactivados, plot=item.category, thumbnail=config.get_thumb('stack'), text_color='gray' ))

        accion = 'mainlist'
        filtros = {}

    channels_list_status = config.get_setting('channels_list_status', default=0)
    if channels_list_status > 0:
        filtros['status'] = 0 if channels_list_status == 1 else 1

    ch_list = channeltools.get_channels_list(filtros=filtros)

    i = 0

    for ch in ch_list:
        cfg_proxies_channel = 'channel_' + ch['id'] + '_proxies'

        if not item.extra == 'all':
            if 'dedicada exclusivamente a los tráilers' in ch['notes']: continue

        if item.extra == 'prefereds':
            if not ch['status'] == 1: continue

        if item.extra == 'problematics':
            if not 'problematic' in ch['clusters']: continue
        else:
            if not item.extra == 'all':
                if config.get_setting('mnu_problematicos', default=False):
                    if 'problematic' in ch['clusters']: continue

        if item.extra == 'disableds':
            if not ch['status'] == -1: continue
        else:
            if not item.extra == 'all':
                if config.get_setting('mnu_desactivados', default=False):
                    if ch['status'] == -1: continue

        if item.extra == 'proxies':
            if not 'Puede requerir el uso de proxies' in ch['notes']: continue

            if not config.get_setting(cfg_proxies_channel, default=''): continue

        if item.extra == 'clones':
            if not 'clone' in ch['clusters']: continue

        else:
            if not item.extra == 'all':
                if item.extra == 'proxies': pass
                elif item.extra == 'clones': pass

                elif not item.extra == 'disableds':
                    if config.get_setting('mnu_proxies', default=False):
                        if 'Puede requerir el uso de proxies' in ch['notes']:
                            if config.get_setting(cfg_proxies_channel, default=''): continue

                    if config.get_setting('mnu_clones', default=False):
                        if 'clone' in ch['clusters']: continue

        if item.extra == 'movies':
            if ch['searchable'] == False:
                if 'adults' in ch['clusters']: continue
                elif 'anime' in ch['clusters']:
                   if config.get_setting('mnu_animes', default=True): continue
                elif 'dorama' in ch['clusters']:
                   if config.get_setting('mnu_doramas', default=True): continue
                elif 'infantil' in ch['clusters']:
                   if config.get_setting('mnu_infantiles', default=True): continue
                elif 'tales' in ch['clusters']:
                   if config.get_setting('mnu_novelas', default=True): continue

        elif item.extra == 'tvshows':
            if ch['searchable'] == False:
                if 'adults' in ch['clusters']: continue
                elif 'mangas' in ch['notes'].lower(): continue
                elif 'anime' in ch['clusters']:
                   if config.get_setting('mnu_animes', default=True): continue
                elif 'dorama' in ch['clusters']:
                   if config.get_setting('mnu_doramas', default=True): continue

                elif 'infantil' in ch['clusters']:
                   if not ch['id'] == 'seodiv':
                       if config.get_setting('mnu_infantiles', default=True): continue

                elif 'tales' in ch['clusters']:
                   if config.get_setting('mnu_novelas', default=True): continue

        elif item.extra == 'adults':
            if ch['searchable'] == True: continue
            if not 'adults' in ch['clusters']: continue

        elif item.extra == 'anime':
            if ch['searchable'] == True: continue
            if not 'anime' in ch['clusters']: continue

        elif item.extra == 'mixed':
            tipos = ch['search_types']
            if 'documentary' in tipos: continue

            if not 'movie' in tipos: continue
            if not 'tvshow' in tipos: continue

        elif item.extra == 'torrents':
            if 'Streaming y Torrent' in ch['notes']: continue

            tipos = ch['search_types']
            if 'documentary' in tipos: continue

        elif item.extra == 'suggested':
            if not 'suggested' in ch['clusters']: continue

            if config.get_setting('mnu_simple', default=False):
                if str(ch['search_types']) == "['documentary']": continue

            if not config.get_setting('mnu_documentales', default=True):
                if str(ch['search_types']) == "['documentary']": continue

            if not config.get_setting('mnu_novelas', default=True):
                if 'exclusivamente en novelas' in ch['notes']: continue

        elif item.extra == 'infantil':
            if not 'infantil' in ch['clusters']: continue

        elif item.extra == 'tales':
            if not 'tales' in ch['clusters']: continue

        elif item.extra == 'dorama':
            if ch['searchable'] == True: continue
            elif not 'dorama' in ch['clusters']: continue

        else:
           if config.get_setting('mnu_simple', default=False):
               if ch['searchable'] == False:
                   if 'adults' in ch['clusters']: continue
                   elif 'anime' in ch['clusters']: continue
                   elif 'dorama' in ch['clusters']: continue
                   elif 'infantil' in ch['clusters']: continue
                   elif 'tales' in ch['clusters']: continue
               else:
                   if str(ch['search_types']) == "['documentary']": continue
                   elif 'enlaces torrent exclusivamente' in ch['notes']: continue
                   elif 'dedicada exclusivamente al dorama' in ch['notes']: continue

                   elif not config.get_setting('mnu_documentales', default=True):
                       if str(ch['search_types']) == "['documentary']": continue

                   elif not config.get_setting('mnu_novelas', default=True):
                       if 'exclusivamente en novelas' in ch['notes']: continue

           else:
              if not config.get_setting('mnu_documentales', default=True):
                  if str(ch['search_types']) == "['documentary']": continue

              if not config.get_setting('mnu_infantiles', default=True):
                  if 'infantil' in ch['clusters']: continue

              if not config.get_setting('mnu_novelas', default=True):
                  if 'exclusivamente en novelas' in ch['notes']: continue
                  elif 'tales' in ch['clusters']: continue

              if not config.get_setting('mnu_torrents', default=True):
                  if 'enlaces torrent exclusivamente' in ch['notes']: continue

              if not config.get_setting('mnu_doramas', default=True):
                  if ch['searchable'] == False: continue
                  elif 'dorama' in ch['clusters']: continue

              if not config.get_setting('mnu_animes', default=True):
                  if ch['searchable'] == False: continue
                  elif 'anime' in ch['clusters']: continue

              if not config.get_setting('mnu_adultos', default=True):
                  if ch['searchable'] == False: continue
                  elif 'adults' in ch['clusters']: continue

        context = []

        if 'proxies' in ch['notes'].lower():
            if config.get_setting(cfg_proxies_channel, default=''):
                tit = '[COLOR %s]Quitar Proxies del Canal[/COLOR]' % color_list_proxies
                context.append({'title': tit, 'channel': item.channel, 'action': '_quitar_proxies'})

        if ch['searchable']:
            if not ch['status'] == -1:
                cfg_searchable_channel = 'channel_' + ch['id'] + '_no_searchable'

                if config.get_setting(cfg_searchable_channel, default=False):
                    tit = '[COLOR %s][B]Quitar Excluido Búsquedas[/B][/COLOR]' % color_adver
                    context.append({'title': tit, 'channel': item.channel, 'action': '_quitar_no_searchables'})
                else:
                    if config.get_setting('search_included_all', default=''):
                        search_included_all = config.get_setting('search_included_all')

                        el_memorizado = "'" + ch['id'] + "'"
                        if el_memorizado in str(search_included_all):
                            tit = '[COLOR indianred][B]Quitar Búsquedas Solo en[/B][/COLOR]'
                            context.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_included_del_one'})

                    if config.get_setting('search_excludes_all', default=''):
                        search_excludes_all = config.get_setting('search_excludes_all')

                        el_memorizado = "'" + ch['id'] + "'"
                        if el_memorizado in str(search_excludes_all):
                            tit = '[COLOR indianred][B]Quitar Exclusión Búsquedas[/B][/COLOR]'
                            context.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del'})


                    elif config.get_setting('search_excludes_movies', default=''):
                        search_excludes_movies = config.get_setting('search_excludes_movies')

                        el_memorizado = "'" + ch['id'] + "'"
                        if el_memorizado in str(search_excludes_movies):
                            tit = '[B][COLOR deepskyblue]Películas [COLOR indianred]Quitar Exclusión Búsquedas[/B][/COLOR]'
                            context.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del'})

                    elif config.get_setting('search_excludes_tvshows', default=''):
                        search_excludes_tvshows = config.get_setting('search_excludes_tvshows')

                        el_memorizado = "'" + ch['id'] + "'"
                        if el_memorizado in str(search_excludes_tvshows):
                            tit = '[B][COLOR hotpink]Series [COLOR indianred]Quitar Exclusión Búsquedas[/B][/COLOR]'
                            context.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del'})

                    elif config.get_setting('search_excludes_documentaries', default=''):
                        search_excludes_documentaries = config.get_setting('search_excludes_documentaries')

                        el_memorizado = "'" + ch['id'] + "'"
                        if el_memorizado in str(search_excludes_documentaries):
                            tit = '[B][COLOR cyan]Documentales [COLOR indianred]Quitar Exclusión Búsquedas[/B][/COLOR]'
                            context.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del'})

                    elif config.get_setting('search_excludes_torrents', default=''):
                        search_excludes_torrents = config.get_setting('search_excludes_torrents')

                        el_memorizado = "'" + ch['id'] + "'"
                        if el_memorizado in str(search_excludes_torrents):
                            tit = '[B][COLOR blue]Torrents [COLOR indianred]Quitar Exclusión Búsquedas[/B][/COLOR]'
                            context.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del'})

                    elif config.get_setting('search_excludes_mixed', default=''):
                        search_excludes_mixed = config.get_setting('search_excludes_mixed')

                        el_memorizado = "'" + ch['id'] + "'"
                        if el_memorizado in str(search_excludes_mixed):
                            tit = '[B][COLOR teal]Películas y/ó Series [COLOR indianred]Quitar Exclusión Búsquedas[/B][/COLOR]'
                            context.append({'title': tit, 'channel': 'submnuctext', 'action': '_channels_excluded_del'})

                    else:
                        tit = '[COLOR %s][B]Excluir en Búsquedas[/B][/COLOR]' % color_adver
                        context.append({'title': tit, 'channel': item.channel, 'action': '_poner_no_searchables'})

        if ch['status'] != 1:
            tit = '[COLOR %s][B]Marcar Canal como Preferido[/B][/COLOR]' % color_list_prefe
            context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': 1})

        if ch['status'] != 0:
            if ch['status'] == 1:
                tit = '[COLOR %s][B]Des-Marcar Canal Preferido[/B][/COLOR]' % color_list_prefe
                context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': 0})
            elif ch['status'] == -1:
                tit = '[COLOR %s][B]Des-Marcar Canal Desactivado[/B][/COLOR]' % color_list_inactive
                context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': 0})
            else:
                tit = '[COLOR white][B]Marcar Canal como Activo[/B][/COLOR]'
                context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': 0})

        if ch['status'] != -1:
            tit = '[COLOR %s][B]Marcar Canal como Desactivado[/B][/COLOR]' % color_list_inactive
            context.append({'title': tit, 'channel': item.channel, 'action': '_marcar_canal', 'estado': -1})

        cfg_domains = False

        if 'current' in ch['clusters']:
            cfg_domains = True

            tit = '[COLOR bisque]Gestión Dominios[/COLOR]'
            context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_domains'})

        tit = '[COLOR %s][B]Últimos Cambios Dominios[/B][/COLOR]' % color_exec
        context.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

        if cfg_domains:
            tit = '[COLOR yellowgreen][B]Dominio Vigente[/B][/COLOR]'
            context.append({'title': tit, 'channel': item.channel, 'action': '_dominio_vigente'})

            if 'Dispone de varios posibles dominios' in ch['notes']:
                tit = '[COLOR powderblue][B]Configurar Dominio a usar[/B][/COLOR]'
                context.append({'title': tit, 'channel': item.channel, 'action': '_dominios'})

            tit = '[COLOR orange][B]Modificar Dominio Memorizado[/B][/COLOR]'
            context.append({'title': tit, 'channel': item.channel, 'action': '_dominio_memorizado'})

        if 'register' in ch['clusters']:
            cfg_user_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_username'
            cfg_pass_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_password'

            if not config.get_setting(cfg_user_channel, default='') or not config.get_setting(cfg_pass_channel, default=''):
                tit = '[COLOR green][B]Información Registrarse[/B][/COLOR]'
                context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_register'})

                tit = '[COLOR teal][B]Credenciales Cuenta[/B][/COLOR]'
                context.append({'title': tit, 'channel': item.channel, 'action': '_credenciales'})
            else:
                cfg_login_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_login'

                presentar = True
                if 'dominios' in ch['notes'].lower():
                    cfg_dominio_channel = 'channel_' + ch['id'] + '_dominio'
                    if not config.get_setting(cfg_dominio_channel, default=''): presentar = False

                if presentar:
                    if config.get_setting(cfg_login_channel, default=False):
                        tit = '[COLOR teal][B]Cerrar Sesión[/B][/COLOR]'
                        context.append({'title': tit, 'channel': item.channel, 'action': '_credenciales'})

        if 'proxies' in ch['notes'].lower():
            if not config.get_setting(cfg_proxies_channel, default=''):
                tit = '[COLOR %s][B]Información Proxies[/B][/COLOR]' % color_infor
                context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

            tit = '[COLOR %s][B]Configurar Proxies a usar[/B][/COLOR]' % color_list_proxies
            context.append({'title': tit, 'channel': item.channel, 'action': '_proxies'})

        if 'notice' in ch['clusters']:
            tit = '[COLOR tan][B]Aviso Canal[/B][/COLOR]'
            context.append({'title': tit, 'channel': 'helper', 'action': 'show_help_' + ch['id']})

        if 'register' in ch['clusters']:
            cfg_user_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_username'
            cfg_pass_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_password'
            if config.get_setting(cfg_user_channel, default='') and config.get_setting(cfg_pass_channel, default=''):
               cfg_login_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_login'

               if config.get_setting(cfg_login_channel, default=False):
                   cfg_dominio_channel = 'channel_' + ch['id'] + '_dominio'
                   tit = '[COLOR springgreen][B]Test Login Cuenta[/B][/COLOR]'
                   context.append({'title': tit, 'channel': 'submnuctext', 'action': '_credenciales_' + ch['id']})

        tit = '[COLOR darkorange][B]Test Web Canal[/B][/COLOR]'
        context.append({'title': tit, 'channel': item.channel, 'action': '_tests'})

        if cfg_domains:
            tit = '[COLOR %s]Ajustes categoría Dominios[/COLOR]' % color_exec
            context.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

        color = color_list_prefe if ch['status'] == 1 else 'white' if ch['status'] == 0 else color_list_inactive

        plot = ''
        if item.extra == 'all': plot += '[' + ', '.join([config.get_localized_category(ct) for ct in ch['categories']]) + '][CR]'
        plot += '[' + ', '.join([idioma_canal(lg) for lg in ch['language']]) + ']'
        if ch['notes'] != '': plot += '[CR][CR]' + ch['notes']

        titulo = ch['name']

        if ch['status'] == -1:
            if not item.extra == 'disableds': titulo += '[I][B][COLOR %s] (desactivado)[/COLOR][/I][/B]' % color_list_inactive
            if config.get_setting(cfg_proxies_channel, default=''): titulo += '[I][B][COLOR %s] (proxies)[/COLOR][/I][/B]' % color_list_proxies
        else:
            if ch['status'] == 1:
               if not item.extra == 'prefereds': titulo += '[I][B][COLOR wheat] (preferido)[/COLOR][/I][/B]'
            else:
                if not item.extra == 'suggested':
                    if 'suggested' in ch['clusters']: titulo += '[I][B][COLOR olivedrab] (sugerido)[/COLOR][/I][/B]'

            if config.get_setting(cfg_proxies_channel, default=''):
                if ch['status'] == 1: titulo += '[I][B][COLOR %s] (proxies)[/COLOR][/I][/B]' % color_list_proxies
                else: color = color_list_proxies

        if 'register' in ch['clusters']:
            cfg_user_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_username'
            cfg_pass_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_password'
            if not config.get_setting(cfg_user_channel, default='') or not config.get_setting(cfg_pass_channel, default=''):
               titulo += '[I][B][COLOR teal] (cuenta)[/COLOR][/I][/B]'
            else:
               cfg_login_channel = 'channel_' + ch['id'] + '_' + ch['id'] + '_login'

               if config.get_setting(cfg_login_channel, default=False):
                   presentar = True
                   if 'dominios' in ch['notes'].lower():
                       cfg_dominio_channel = 'channel_' + ch['id'] + '_dominio'
                       if not config.get_setting(cfg_dominio_channel, default=''): presentar = False

                   if presentar: titulo += '[I][B][COLOR teal] (sesion)[/COLOR][/I][/B]'
               else: titulo += '[I][COLOR teal] (login)[/COLOR][/I]'

        if 'current' in ch['clusters']:
            cfg_current_channel = 'channel_' + ch['id'] + '_dominio'

            if config.get_setting(cfg_current_channel, default=False): titulo += '[I][B][COLOR green] (dominio)[/COLOR][/I][/B]'

        if not PY3:
            if 'mismatched' in ch['clusters']: titulo += '[I][B][COLOR coral] (Incompatible)[/COLOR][/I][/B]'

        if 'inestable' in ch['clusters']:
            if config.get_setting('mnu_simple', default=False): continue
            elif config.get_setting('channels_list_no_inestables', default=False): continue

            titulo += '[I][B][COLOR plum] (inestable)[/COLOR][/I][/B]'

        if 'problematic' in ch['clusters']:
            if config.get_setting('mnu_simple', default=False): continue

            if not item.extra == 'all':
                if not item.extra == 'problematics': 
                    if config.get_setting('mnu_problematicos', default=False): continue
                    elif config.get_setting('channels_list_no_problematicos', default=False): continue

            if not item.extra == 'problematics': titulo += '[I][B][COLOR darkgoldenrod] (problemático)[/COLOR][/I][/B]'

        if 'clone' in ch['clusters']:
            if config.get_setting('mnu_simple', default=False): continue

            if not item.extra == 'all':
                if not item.extra == 'clones': 
                    if config.get_setting('mnu_clones', default=False): continue
                    elif config.get_setting('channels_list_no_clones', default=False): continue

            if not item.extra == 'clones': titulo += '[I][B][COLOR turquoise] (clon)[/COLOR][/I][/B]'

        if con_incidencias:
           if ch['name'] in str(con_incidencias): titulo += '[I][B][COLOR tan] (incidencia)[/COLOR][/I][/B]'

        if no_accesibles:
           if ch['name'] in str(no_accesibles): titulo += '[I][B][COLOR indianred] (no accesible)[/COLOR][/I][/B]'

        if con_problemas:
           if ch['name'] in str(con_problemas):
               hay_problemas = str(con_problemas).replace('[B][COLOR moccasin]', 'CHANNEL').replace('[COLOR lime]', '/CHANNEL')
               channels_con_problemas = scrapertools.find_multiple_matches(hay_problemas, "CHANNEL(.*?)/CHANNEL")

               for channel_con_problema in channels_con_problemas:
                    channel_con_problema = channel_con_problema.strip()

                    if not channel_con_problema == ch['name']: continue

                    titulo += '[I][B][COLOR tomato] (con problema)[/COLOR][/I][/B]'
                    break

        if ch['searchable']:
            if not ch['status'] == -1:
                cfg_searchable_channel = 'channel_' + ch['id'] + '_no_searchable'

                if config.get_setting(cfg_searchable_channel, default=False): titulo += '[I][B][COLOR yellowgreen] (no búsquedas)[/COLOR][/I][/B]'

                if config.get_setting('search_included_all', default=''):
                   if ch['id'] in str(config.get_setting('search_included_all')): titulo += '[I][B][COLOR yellowgreen] (solo buscar)[/COLOR][/I][/B]'

        if config.get_setting('mnu_simple', default=False):
            if not config.get_setting('mnu_adultos', default=True):
                if '+18' in ch['notes']: continue

            if 'movie' in ch['categories']:
                if "tvshow" in ch['categories']:
                    titulo += '[B][I][COLOR deepskyblue] películas[/COLOR] [COLOR hotpink]series[/COLOR][/I][/B]'
                    if 'tales' in ch['clusters']: titulo += '[B][I][COLOR limegreen] novelas[/COLOR][/I][/B]'
                else:
                    if '+18' in ch['notes']: titulo += '[B][I][COLOR orange] +18[/COLOR][/I][/B]'
                    else: titulo += '[B][I][COLOR deepskyblue] películas[/COLOR][/I][/B]'
            else:
                if "tvshow" in ch['categories']:
                    titulo += '[B][I][COLOR hotpink] series[/COLOR][/I][/B]'
                    if 'tales' in ch['clusters']: titulo += '[B][I][COLOR limegreen] novelas[/COLOR][/I][/B]'
                elif "documentary" in ch['categories']: titulo += '[B][I][COLOR cyan] documentales[/COLOR][/I][/B]'

        i =+ 1

        itemlist.append(Item( channel=ch['id'], action=accion, title=titulo, context=context, text_color=color, plot=plot, extra=item.extra, thumbnail=ch['thumbnail'], category=ch['name'] ))

    if len(ch_list) == 0 or i == 0:
        if item.extra == 'Proxies' or item.extra == 'disableds':
            itemlist.append(item.clone( channel='actions', action='open_settings', title='[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR tan][B]Menú)[/B][/COLOR]', context=context_config, folder=False, thumbnail=config.get_thumb('settings') ))

        if item.extra == 'proxies':
            itemlist.append(item.clone( channel='filters', action='with_proxies', title='[B]Sin canales con Proxies Memorizados[/B]', text_color=color_list_proxies, thumbnail=config.get_thumb('stack'), folder=False ))
        elif item.extra == 'clones':
            itemlist.append(item.clone( channel='filters', action='show_channels_list', title='[B]Sin canales Problemáticos[/B]', text_color='darkgoldenrod', problematics=True, thumbnail=config.get_thumb('stack'), folder=False ))
        elif item.extra == 'problematics':
            itemlist.append(item.clone( channel='filters', action='show_channels_list', title='[B]Sin canales Problemáticos[/B]', text_color='darkgoldenrod', clones=True, thumbnail=config.get_thumb('stack'), folder=False ))
        elif item.extra == 'disableds':
            itemlist.append(item.clone( channel='filters', action='channels_status', title='[B]Sin canales Desactivados[/B]', text_color=color_list_inactive, des_rea=True, thumbnail=config.get_thumb('stack'), folder=False ))
        else:
            itemlist.append(item.clone( channel='filters', action='channels_status', title='[B]Opción Sin canales[/B]', text_color=color_list_prefe, des_rea=False, thumbnail=config.get_thumb('stack'), folder=False ))

    return itemlist


def idioma_canal(lang):
    idiomas = { 'cast': 'Castellano', 'lat': 'Latino', 'eng': 'Inglés', 'pt': 'Portugués', 'vo': 'VO', 'vose': 'Vose', 'vos': 'Vos', 'cat': 'Català' }
    return idiomas[lang] if lang in idiomas else lang


def _marcar_canal(item):
    from modules import submnuctext
    submnuctext._marcar_canal(item)


def _poner_no_searchables(item):
    from modules import submnuctext
    submnuctext._poner_no_searchable(item)

def _quitar_no_searchables(item):
    from modules import submnuctext
    submnuctext._quitar_no_searchable(item)


def _quitar_proxies(item):
    from modules import submnuctext
    submnuctext._quitar_proxies(item)


def _dominio_vigente(item):
    from modules import submnuctext
    submnuctext._dominio_vigente(item)


def _dominio_memorizado(item):
    from modules import submnuctext
    submnuctext._dominio_memorizado(item)


def _dominios(item):
    from modules import submnuctext
    submnuctext._dominios(item)


def _credenciales(item):
    from modules import submnuctext
    submnuctext._credenciales(item)


def _proxies(item):
    from modules import submnuctext
    submnuctext._proxies(item)


def _tests(item):
    from modules import submnuctext
    submnuctext._test_webs(item)
