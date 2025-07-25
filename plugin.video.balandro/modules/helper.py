# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] >= 3:
    PY3 = True

    import xbmcvfs
    translatePath = xbmcvfs.translatePath
else:
    PY3 = False

    import xbmc
    translatePath = xbmc.translatePath


import os, re, time, xbmcaddon, glob

import xbmc, xbmcgui, platform

from datetime import datetime

from platformcode import config, logger, platformtools, updater
from core.item import Item
from core import channeltools, filetools, servertools, httptools, scrapertools, trackingtools, jsontools

from modules import filters


ADDON_REPO_ADDONS = 'https://repobal.github.io/base/'
ADDON_UPDATES_JSON = 'https://raw.githubusercontent.com/repobal/fix/main/updates.json'


color_list_prefe = config.get_setting('channels_list_prefe_color', default='gold')
color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')
color_list_inactive = config.get_setting('channels_list_inactive_color', default='gray')

color_alert = config.get_setting('notification_alert_color', default='red')
color_infor = config.get_setting('notification_infor_color', default='pink')
color_adver = config.get_setting('notification_adver_color', default='violet')
color_avis = config.get_setting('notification_avis_color', default='yellow')
color_exec = config.get_setting('notification_exec_color', default='cyan')

descartar_xxx = config.get_setting('descartar_xxx', default=False)
descartar_anime = config.get_setting('descartar_anime', default=False)

_foro = "[COLOR plum][B][I] www.mimediacenter.info/foro/ [/I][/B][/COLOR]"
_source = "[COLOR coral][B][I] repobal.github.io/base/ [/I][/B][/COLOR]"
_scripts = "[COLOR mediumaquamarine][B][I] repobal.github.io/base/scripts/ [/I][/B][/COLOR]"
_telegram = "[COLOR lightblue][B][I] t.me/balandro_asesor [/I][/B][/COLOR]"

_team = "[COLOR hotpink][B][I] t.me/Balandro_team [/I][/B][/COLOR]"


search_no_accesibles = config.get_setting('search_no_accesibles', default=False)

no_results_proxies = config.get_setting('search_no_results_proxies', default=True)
no_results = config.get_setting('search_no_results', default=False)


srv_pending = ''
con_incidencias = ''
no_accesibles = ''
con_problemas = ''

try:
    with open(os.path.join(config.get_runtime_path(), 'dominios.txt'), 'r') as f: txt_status=f.read(); f.close()
except:
    try: txt_status = open(os.path.join(config.get_runtime_path(), 'dominios.txt'), encoding="utf8").read()
    except: txt_status = ''

if txt_status:
    # ~ Pending
    bloque = scrapertools.find_single_match(txt_status, 'SITUACION SERVIDORES(.*?)SITUACION CANALES')

    matches = scrapertools.find_multiple_matches(bloque, "[B](.*?)[/B]")

    for match in matches:
        match = match.strip()

        if '[COLOR orchid]' in match: srv_pending += '[B' + match + '/I][/B][/COLOR][CR]'

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


context_temas = []

try: last_ver = updater.check_addon_version()
except: last_ver = None

if last_ver is None: last_ver = '[B][I][COLOR gray](fixes off)[/COLOR][/I][/B]'
elif not last_ver:
      text_dev = ''
      if config.get_setting('developer_mode', default=False): text_dev = '[COLOR darkorange][B]Desarrollo[/B][/COLOR] '
      last_ver = '[B][I][COLOR %s](desfasada)[/COLOR][/I][/B]' % color_adver
      last_ver = last_ver + '  '  + text_dev
else: last_ver = ''

last_fix = config.get_addon_version()

if not 'desfasada' in last_ver:
    if 'fix' in last_fix:
        tit = '[COLOR %s]Información Fix[/COLOR]' % color_infor
        context_temas.append({'title': tit, 'channel': 'helper', 'action': 'show_last_fix'})

        tit = '[COLOR darkcyan][B]Resumen Fix[/B][/COLOR]'
        context_temas.append({'title': tit, 'channel': 'helper', 'action': 'resumen_fix'})

    tit = '[COLOR %s]Comprobar Actualizaciones Fix[/COLOR]' % color_avis
    context_temas.append({'title': tit, 'channel': 'actions', 'action': 'check_addon_updates'})

    tit = '[COLOR %s][B]Forzar Actualizaciones Fix[/B][/COLOR]' % color_adver
    context_temas.append({'title': tit, 'channel': 'actions', 'action': 'check_addon_updates_force'})

tit = '[COLOR red][B]Temas NO Contemplados[/B][/COLOR]'
context_temas.append({'title': tit, 'channel': 'helper', 'action': 'show_not_contemplated'})

tit = '[COLOR yellowgreen][B]Preguntas Frecuentes[/B][/COLOR]'
context_temas.append({'title': tit, 'channel': 'helper', 'action': 'show_help_faq'})

tit = '[COLOR seagreen][B]Trucos y Consejos[/B][/COLOR]'
context_temas.append({'title': tit, 'channel': 'helper', 'action': 'show_help_tips'})

tit = '[COLOR limegreen][B]Ejemplos de Uso[/B][/COLOR]'
context_temas.append({'title': tit, 'channel': 'helper', 'action': 'show_help_use'})

tit = '[COLOR goldenrod][B]Notas sobre Parámetros[/B][/COLOR]'
context_temas.append({'title': tit, 'channel': 'helper', 'action': 'show_help_settings'})

tit = '[COLOR %s]Ajustes preferencias[/COLOR]' % color_exec
context_temas.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

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

tit = '[COLOR red][B]Temas No Contemplados[/B][/COLOR]'
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

context_usual = []

tit = '[COLOR tan][B]Preferencias Canales[/B][/COLOR]'
context_usual.append({'title': tit, 'channel': 'helper', 'action': 'show_channels_parameters'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_usual.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR yellow][B]Preferencias Buscar[/B][/COLOR]'
context_usual.append({'title': tit, 'channel': 'helper', 'action': 'show_help_parameters_search'})

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

tit = '[COLOR %s][B]Quitar Proxies Actuales[/B][/COLOR]' % color_list_proxies
context_parental.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s]Ajustes categorías Canales, Parental, Dominios y Proxies[/COLOR]' % color_exec
context_parental.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

context_desarrollo = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_desarrollo.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR goldenrod][B]Miscelánea[/B][/COLOR]'
context_desarrollo.append({'title': tit, 'channel': 'helper', 'action': 'show_help_miscelanea'})

tit = '[COLOR %s]Ajustes categoría Team[/COLOR]' % color_exec
context_desarrollo.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

context_config = []

tit = '[COLOR tan][B]Preferencias Canales[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_channels_parameters'})

tit = '[COLOR bisque]Gestión Dominios[/COLOR]'
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_help_domains'})

tit = '[COLOR %s][B]Últimos Cambios Dominios[/B][/COLOR]' % color_exec
context_config.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR %s][B]Quitar Dominios Memorizados[/B][/COLOR]' % color_alert
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_domains'})

tit = '[COLOR green][B]Información Plataforma[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_plataforma'})

tit = '[COLOR %s][B]Quitar Proxies Memorizados[/B][/COLOR]' % color_alert
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR olive][B]Limpiezas[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_limpiezas'})

tit = '[COLOR darkorange][B]Borrar Carpeta Caché[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_folder_cache'})

tit = '[COLOR %s][B]Sus Ajustes Personalizados[/B][/COLOR]' % color_avis
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_sets'})

tit = '[COLOR %s][B]Cookies Actuales[/B][/COLOR]' % color_infor
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_cook'})

tit = '[COLOR %s][B]Eliminar Cookies[/B][/COLOR]' % color_alert
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_cookies'})

tit = '[COLOR %s]Sus Advanced Settings[/COLOR]' % color_adver
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_advs'})

tit = '[COLOR %s][B]Eliminar Advanced Settings[/B][/COLOR]' % color_alert
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_advs'})

tit = '[COLOR mediumaquamarine][B]Restablecer Parámetros Internos[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_params'})

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

tit = '[COLOR %s][B]Quitar Proxies Actuales[/B][/COLOR]' % color_list_proxies
context_torrents.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s]Ajustes categorías Canales, Dominios, Proxies y Torrents[/COLOR]' % color_exec
context_torrents.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

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

tit = '[COLOR %s][B]Quitar Dominios Memorizados[/B][/COLOR]' % color_alert
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

tit = '[COLOR %s][B]Quitar Proxies Actuales[/B][/COLOR]' % color_list_proxies
context_buscar.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s][B]Información Búsquedas[/B][/COLOR]' % color_infor
context_buscar.append({'title': tit, 'channel': 'search', 'action': 'show_help'})

tit = '[COLOR %s]Ajustes categorías Canales, Dominios, Play, Proxies y Buscar[/COLOR]' % color_exec
context_buscar.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

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


def mainlist(item):
    logger.info()
    itemlist = []

    title = '[B][I]AYUDA[/I]  [COLOR chartreuse](%s)[/B]  %s' % (config.get_addon_version().replace('.fix', '-Fix'), last_ver)

    itemlist.append(item.clone( action='', title= title, context=context_temas, text_color='lightyellow', folder=False ))

    itemlist.append(item.clone( action='show_infos', title='[COLOR fuchsia][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    if not config.get_setting('mnu_simple', default=False): tit_mnu = '[B][I]Menú Ayuda:[/I][/B]'
    else: tit_mnu = '[B][I]Menú Ayuda Simplificado:[/I][/B]'

    itemlist.append(item.clone( action='', title=tit_mnu, context=context_ayuda, text_color='lightyellow', folder=False ))

    itemlist.append(item.clone( action='submnu_uso', title= ' - [B]Uso[/B]', context=context_temas, text_color='darkorange', thumbnail=config.get_thumb('addon') ))

    itemlist.append(item.clone( action='submnu_info', title= ' - [B]Info[/B]', text_color='turquoise', thumbnail=config.get_thumb('news') ))
    itemlist.append(item.clone( action='submnu_menus', title= ' - [B]Menús[/B]', text_color='tan', thumbnail=config.get_thumb('dev') ))
    itemlist.append(item.clone( action='submnu_canales', title= ' - [B]Canales[/B]', context=context_usual, text_color='gold', thumbnail=config.get_thumb('stack') ))

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_adultos', default=True):
            itemlist.append(item.clone( action='submnu_parental', title= ' - [B]Adultos [COLOR powderblue][I]Parental[/I][/B]', context=context_parental, text_color='orange', thumbnail=config.get_thumb('adults') ))

    itemlist.append(item.clone( action='submnu_domains', title= ' - [B]Dominios[/B]', context=context_usual, text_color='bisque', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='submnu_cuentas', title= ' - [B]Cuentas[/B]', context=context_usual, text_color='goldenrod', thumbnail=config.get_thumb('support') ))

    itemlist.append(item.clone( action='submnu_audios', title=' - [B]Audios [COLOR powderblue][I]Idiomas[/I][/B]', text_color='limegreen', thumbnail=config.get_thumb('idiomas') ))
    itemlist.append(item.clone( action='submnu_play', title=' - [B]Play [COLOR powderblue][I]Servidores[/I][/B]', text_color='fuchsia', thumbnail=config.get_thumb('bolt') ))
    itemlist.append(item.clone( action='submnu_proxies', title= ' - [B]Proxies[/B]', context=context_proxy_channels, text_color='red', thumbnail=config.get_thumb('flame') ))

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_torrents', default=True):
            itemlist.append(item.clone( action='submnu_torrents', title= ' - [B]Torrents[/B]', context=context_torrents, text_color='blue', thumbnail=config.get_thumb('torrents') ))

    itemlist.append(item.clone( action='submnu_buscar', title=' - [B]Buscar[/B]', context=context_buscar, text_color='yellow', thumbnail=config.get_thumb('magnifyingglass') ))

    presentar = True
    if config.get_setting('mnu_simple', default=False): presentar = False
    else:
       if not config.get_setting('mnu_preferidos', default=True): presentar = False

    if presentar:
        itemlist.append(item.clone( action='submnu_preferidos', title=' - [B]Preferidos[/B]', context=context_preferidos, text_color='wheat', thumbnail=config.get_thumb('videolibrary') ))

    presentar = True
    if config.get_setting('mnu_simple', default=False): presentar = False
    else:
       if not config.get_setting('mnu_desargas', default=True): presentar = False

    if presentar:
        itemlist.append(item.clone( action='submnu_descargas', title=' - [B]Descargas[/B]', context=context_descargas, text_color='seagreen', thumbnail=config.get_thumb('download') ))

    itemlist.append(item.clone( action='submnu_actualizar', title=' - [B]Actualizar [COLOR darkcyan][I]Fixes[/I][/B]', context=context_ayuda, text_color='cyan', thumbnail=config.get_thumb('addon') ))
    itemlist.append(item.clone( action='submnu_mediacenter', title= ' - [B]Media Center[/B]', context=context_config, text_color='pink', thumbnail=config.get_thumb('mediacenter') ))
    itemlist.append(item.clone( action='submnu_addons', title= ' - [B]Add-Ons[/B]', text_color='yellowgreen', thumbnail=config.get_thumb('kodiaddons') ))
    itemlist.append(item.clone( action='submnu_sistema', title= ' - [B]Sistema[/B]', context=context_ayuda, text_color='teal', thumbnail=config.get_thumb('computer') ))
    itemlist.append(item.clone( action='submnu_clean', title= ' - [B]Limpiezas[/B]', text_color='olive', thumbnail=config.get_thumb('quote') ))
    itemlist.append(item.clone( action='submnu_version', title=' - [B]Versiones[/B]', text_color='violet', thumbnail=config.get_thumb('addon') ))

    avisar = False

    if not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developergenres.py')): avisar = True
    elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')): avisar = True
    elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')): avisar = True

    if not avisar:
        titulo = ' - [B]Desarrollo [COLOR slateblue][I]Team[/I][/B]'
    else:
        titulo = ' - [B]Falso Desarrollo [COLOR slateblue][I]Team[/I][/B]'

    itemlist.append(item.clone( action='submnu_desarrollo', title=titulo, context=context_desarrollo, text_color='firebrick', thumbnail=config.get_thumb('team') ))

    itemlist.append(item.clone( action='submnu_legalidad', title=' - [B]Legalidad[/B]', text_color='yellowgreen', thumbnail=config.get_thumb('megaphone') ))

    itemlist.append(item.clone( action='submnu_config', title=' - [B]Ajustes [COLOR moccasin][I]Preferencias[/I][/B]', context=context_config, text_color='chocolate', thumbnail=config.get_thumb('settings') ))

    return itemlist


def show_infos(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][B]AYUDA Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='', title= '[B]Fecha [COLOR powderblue][I]' + str(datetime.today()) + '[/I][/B]', text_color='aquamarine' ))

    itemlist.append(item.clone( action='submnu_contacto', title= '[B]Contacto[/B]', text_color='limegreen', thumbnail=config.get_thumb('news') ))
    itemlist.append(item.clone( action='submnu_fuente', title= '[B]Fuentes [COLOR powderblue][I]Add-Ons[/I][/B]', text_color='coral', thumbnail=config.get_thumb('pencil') ))
    itemlist.append(item.clone( action='show_help_miscelanea', title= '[B]Miscelánea[/B]', text_color='goldenrod', thumbnail=config.get_thumb('booklet') ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title='[B]Últimos Cambios Dominios[/B]', text_color='tomato', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='show_help_bloqueos', title='[B]Bloqueos Operadoras[/B]', text_color='yellowgreen', thumbnail=config.get_thumb('roadblock') ))

    itemlist.append(item.clone( action='', title='[COLOR gold][I][B]CANALES:[/B][/I][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_canales', title= ' - Resumen y su Distribución', thumbnail=config.get_thumb('stack') ))

    if txt_status:
        if con_incidencias:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_incidencias', title=' - [COLOR tan][B]Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

        if no_accesibles:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_no_accesibles', title=' - [COLOR indianred][B]No Accesibles[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

        if con_problemas:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_con_problemas', title=' - [COLOR tomato][B]Con Problemas[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][I][B]SERVIDORES:[/B][/I][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_servidores', title= ' - Resumen y su Distribución', thumbnail=config.get_thumb('bolt') ))

    if txt_status:
        if srv_pending:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_pending', title=' - [COLOR tan][B]Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    return itemlist


def submnu_contacto(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]CONTACTO:[/B]', text_color='limegreen', folder=False ))

    itemlist.append(item.clone( action='', title= ' - Foro ' + _foro + ' Instalaciones, Tutoriales, Sugerencias, etc.', thumbnail=config.get_thumb('foro'), folder=False ))

    itemlist.append(item.clone( action='', title= ' - Telegram ' + _telegram + ' Asesoramiento, Dudas, Consultas, etc.', thumbnail=config.get_thumb('telegram'), folder=False ))
    itemlist.append(item.clone( action='', title= '   [COLOR yellow][B]Usuarios Telegram pueden Añadir Miembros[/B][/COLOR]', thumbnail=config.get_thumb('pencil'), folder=False ))

    itemlist.append(item.clone( action='', title= ' - Team ' + _team + ' Equipo de Desarrollo', thumbnail=config.get_thumb('team'), folder=False ))
    itemlist.append(item.clone( action='', title='    [COLOR goldenrod][B]Incorporaciones a Team con Enlace de Invitación[/B][/COLOR]', folder=False, thumbnail=config.get_thumb('pencil') ))

    return itemlist


def submnu_fuente(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]FUENTES:[/B]', text_color='coral', folder=False ))

    itemlist.append(item.clone( action='', title= ' - Fuente ' + _source + ' Repositorio, Add-On, Scripts', thumbnail=config.get_thumb('addon'), folder=False ))

    itemlist.append(item.clone( action='', title= ' - Fuente ' + _scripts, thumbnail=config.get_thumb('addon'), folder=False ))

    if not PY3:
        itemlist.append(item.clone( action='', title= '   - Carpeta [COLOR yellowgreen][B]Kodi18[/COLOR]: [COLOR gold]Otros repositorios y plugins [/COLOR] hasta [COLOR goldenrod] 18.x[/B][/COLOR]', thumbnail=config.get_thumb('addon'), folder=False ))
    else:
        itemlist.append(item.clone( action='', title= '   - Carpeta [COLOR yellowgreen][B]Kodi19[/COLOR]: [COLOR gold]Otros repositorios y plugins [/COLOR] desde [COLOR goldenrod] 19.x[/B][/COLOR]', thumbnail=config.get_thumb('addon'), folder=False ))

    itemlist.append(item.clone( action='', title= '[B][I]PLUGINS y SCRIPTS:[/I][/B]', text_color='tomato', folder=False, thumbnail=config.get_thumb('kodiaddons') ))

    cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

    if cliente_torrent == 'Seleccionar' or cliente_torrent == 'Ninguno': tex_tor = cliente_torrent
    else:
       tex_tor = cliente_torrent
       cliente_torrent = 'plugin.video.' + cliente_torrent.lower()
       if xbmc.getCondVisibility('System.HasAddon("%s")' % cliente_torrent):
           cod_version = xbmcaddon.Addon(cliente_torrent).getAddonInfo("version").strip()
           tex_tor += '  [COLOR goldenrod]' + cod_version + '[/COLOR]'

    itemlist.append(item.clone( action='', title= ' - [COLOR yellow][B]Cliente/Motor Torrent ' + tex_tor + '[/B][/COLOR]', thumbnail=config.get_thumb('elementum'), folder=False ))

    if xbmc.getCondVisibility('System.HasAddon("script.elementum.burst")'):
        cod_version = xbmcaddon.Addon("script.elementum.burst").getAddonInfo("version").strip()
        tex_tor = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
    else: tex_tor = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action='', title= ' - [COLOR yellow][B]Elementum Burst ' + tex_tor + '[/B][/COLOR]', thumbnail=config.get_thumb('elementum'), folder=False ))

    if xbmc.getCondVisibility('System.HasAddon("inputstream.adaptive")'):
        cod_version = xbmcaddon.Addon("inputstream.adaptive").getAddonInfo("version").strip()
        tex_ia = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
    else: tex_ia = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action='', title= ' - [COLOR yellow][B]InputStream Adaptive ' + tex_ia + '[/B][/COLOR]', thumbnail=config.get_thumb('Inputstreamadaptive'), folder=False ))

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
        cod_version = xbmcaddon.Addon("plugin.video.youtube").getAddonInfo("version").strip()
        tex_yt = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
    else: tex_yt = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action='', title= ' - [COLOR yellow][B]plugin.video.youtube ' + tex_yt + '[/B][/COLOR]', thumbnail=config.get_thumb('youtube'), folder=False ))

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        cod_version = xbmcaddon.Addon("script.module.resolveurl").getAddonInfo("version").strip()
        tex_mr = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
    else: tex_mr = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action='', title= ' - [COLOR yellow][B]script.module.resolveurl ' + tex_mr + '[/B][/COLOR]', thumbnail=config.get_thumb('resolveurl'), folder=False ))

    itemlist.append(item.clone( action='', title= '[B][I]REPOSITORIOS:[/I][/B]', text_color='tomato', folder=False, thumbnail=config.get_thumb('kodiaddons') ))

    if config.get_setting('mnu_torrents', default=True):
        if not PY3:
            if xbmc.getCondVisibility('System.HasAddon("repository.elementum")'):
                cod_version = xbmcaddon.Addon("repository.elementum").getAddonInfo("version").strip()
                tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
            else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

            itemlist.append(item.clone( action='', title= ' - [COLOR yellow][B]repository.elementum ' + tex_rp + '[/B][/COLOR] (hasta K18.x)', thumbnail=config.get_thumb('elementum'), folder=False ))

        if xbmc.getCondVisibility('System.HasAddon("repository.elementumorg")'):
            cod_version = xbmcaddon.Addon("repository.elementumorg").getAddonInfo("version").strip()
            tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

        itemlist.append(item.clone( action='', title= ' - [COLOR yellow][B]repository.elementumorg ' + tex_rp + '[/B][/COLOR]', thumbnail=config.get_thumb('elementum'), folder=False ))

    if xbmc.getCondVisibility('System.HasAddon("repository.resolveurl")'):
        cod_version = xbmcaddon.Addon("repository.resolveurl").getAddonInfo("version").strip()
        tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
    else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action='', title= ' - [COLOR yellow][B]repository.resolveurl ' + tex_rp + '[/B][/COLOR]', thumbnail=config.get_thumb('resolveurl'), folder=False ))

    return itemlist


def submnu_uso(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]USO:[/B]', text_color='darkorange', folder=False ))

    itemlist.append(item.clone( action='show_not_contemplated', title= ' - ¿ Qué [COLOR goldenrod][B]NO[/B][/COLOR] está contemplado/garantizado en Balandro ?', thumbnail=config.get_thumb('roadblock') ))
    itemlist.append(item.clone( action='show_help_faq', title= ' - Preguntas Frecuentes', thumbnail=config.get_thumb('news') ))
    itemlist.append(item.clone( action='show_help_tips', title= ' - Trucos y Consejos', thumbnail=config.get_thumb('news') ))
    itemlist.append(item.clone( action='show_help_use', title= ' - Ejemplos de Uso', thumbnail=config.get_thumb('news') ))
    itemlist.append(item.clone( action='show_help_settings', title= ' - Notas sobre algunos Parámetros de los Ajustes', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_bloqueos', title= ' - ¿ Qué hacer si su Operadora [COLOR yellowgreen][B]Bloquea[/B][/COLOR] algún Canal ?', thumbnail=config.get_thumb('roadblock') ))

    itemlist.append(item.clone( action='show_server_report', title= ' - Como [COLOR cyan][B]Reportar[/B][/COLOR] posible Fallo en la Reproducción de Servidores', thumbnail=config.get_thumb('megaphone') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] Preferencias', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_info(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]INFO:[/B]', text_color='turquoise', folder=False ))

    itemlist.append(item.clone( action='show_not_contemplated', title= ' - ¿ Qué [COLOR goldenrod][B]NO[/B][/COLOR] está contemplado/garantizado en Balandro ?', thumbnail=config.get_thumb('roadblock') ))

    itemlist.append(item.clone( action='show_help_bloqueos', title= ' - ¿ Qué hacer si su Operadora [COLOR yellowgreen][B]Bloquea[/B][/COLOR] algún Canal ?', thumbnail=config.get_thumb('roadblock') ))

    itemlist.append(item.clone( action='show_help_proxies', title= ' - [COLOR green][B]Información[/B][/COLOR] Uso de [COLOR red][B]Proxies[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title=' - [COLOR tomato][B]Últimos Cambios Dominios[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='', title='[COLOR gold][I][B]INFO CANALES:[/B][/I][/COLOR]' ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_canales', title= ' - Resúmenes y su Distribución', thumbnail=config.get_thumb('stack') ))

    if txt_status:
        if con_incidencias:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_incidencias', title=' - [COLOR gold][B]Canales [COLOR tan]Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

        if no_accesibles:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_no_accesibles', title=' - [COLOR gold][B]Canales [COLOR indianred]No Accesibles[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

        if con_problemas:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_con_problemas', title=' - [COLOR gold][B]Canales [COLOR tomato]Con Problemas[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][I][B]INFO SERVIDORES:[/B][/I][/COLOR]' ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_servidores', title= ' - Resúmenes y su Distribución', thumbnail=config.get_thumb('bolt') ))

    if txt_status:
        if srv_pending:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_pending', title=' - [COLOR fuchsia][B]Servidores [COLOR tan]Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( action='', title= '[I]INFO IDIOMAS AUDIOS:[/I]', text_color='yellowgreen', folder=False ))

    itemlist.append(item.clone( action='show_help_audios', title= ' - [COLOR green][B]Información[/B][/COLOR] Idiomas' ))

    itemlist.append(item.clone( action='', title= '[I]INFO PREFERENCIAS ACTUALES:[/I]', text_color='turquoise', folder=False ))

    itemlist.append(item.clone( action='show_menu_parameters', title= ' - [COLOR tan][B]Menús[/B][/COLOR]', _mnu = True ))
    itemlist.append(item.clone( action='show_mnu_specials', title= ' - [COLOR plum][B]Sub-Menús[/B][/COLOR]' ))

    itemlist.append(item.clone( action='show_channels_parameters', title= ' - [COLOR gold][B]Canales[/B][/COLOR]', _mnu = True ))

    if not config.get_setting('mnu_simple', default=False):
        itemlist.append(item.clone( action='show_parental_parameters', title= ' - [COLOR orange][B]Parental[/B][/COLOR]' ))

    itemlist.append(item.clone( action='show_play_parameters', title= ' - [COLOR fuchsia][B]Play[/B][/COLOR]' ))
    itemlist.append(item.clone( action='show_prx_parameters', title= ' - [COLOR red][B]Proxies[/B][/COLOR]' ))

    if config.get_setting('mnu_torrents', default=True):
        itemlist.append(item.clone( action='show_menu_parameters', title= ' - [COLOR blue][B]Torrents[/B][/COLOR]', _mnu = True ))

    itemlist.append(item.clone( channel='helper', action='show_help_parameters_search', title= ' - [COLOR yellow][B]Buscar[/B][/COLOR]' ))

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_preferidos', default=True):
            itemlist.append(item.clone( action='show_menu_parameters', title= ' - [COLOR wheat][B]Preferidos[/B][/COLOR]', _mnu = True ))

        if config.get_setting('mnu_desargas', default=True):
            itemlist.append(item.clone( action='show_menu_parameters', title= ' - [COLOR seagreen][B]Descargas[/B][/COLOR]', _mnu = True ))

    itemlist.append(item.clone( channel='submnuteam', action='show_sistema', title= ' - [COLOR teal][B]Sistema[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    if config.get_setting('developer_mode', default=False):
        avisar = False

        if not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developergenres.py')): avisar = True
        elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')): avisar = True
        elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')): avisar = True

        if not avisar:
            titulo = 'Desarrollo'
        else:
            titulo = 'Falso Desarrollo'

        itemlist.append(item.clone( action='', title='- [COLOR darkorange][B]' + titulo + '[/B][/COLOR]', thumbnail=config.get_thumb('team') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR turquoise][B]Info[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_addons(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]ADD-ONS:[/B]', text_color='yellowgreen', folder=False ))

    itemlist.append(item.clone( channel='submnuteam', action='submnu_addons_info', title= ' - [COLOR yellow][B]Add-Ons[/B][/COLOR] (Gestión desde Balandro)', _help = True, thumbnail=config.get_thumb('kodiaddons') ))

    itemlist.append(item.clone( channel='submnuteam', action='submnu_all_addons', title= ' - Add-Ons [COLOR limegreen][B]Instalados[/B][/COLOR]', thumbnail=config.get_thumb('kodiaddons') ))

    itemlist.append(item.clone( channel='submnuteam', action='submnu_resto_addons', title= ' - Add-Ons [COLOR greenyellow][B]Instalados con Datos[/B][/COLOR]', thumbnail=config.get_thumb('kodiaddons') ))

    return itemlist


def submnu_menus(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]MENÚS:[/B]', text_color='tan', folder=False ))

    itemlist.append(item.clone( action='show_menu_parameters', title= ' - [COLOR green][B]Información[/B][/COLOR] sobre sus [COLOR chocolate][B]Preferencias[/B][/COLOR] Actuales', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='', title= '[I]SUB-MENÚS:[/I]', text_color='tan', folder=False ))

    itemlist.append(item.clone( action='show_mnu_specials', title= ' - [COLOR green][B]Información[/B][/COLOR] sobre sus [COLOR chocolate][B]Preferencias[/B][/COLOR] Actuales', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR tan][B]Menú[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_canales(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]CANALES:[/B]', text_color='gold', folder=False ))

    itemlist.append(item.clone( action='show_infos_canales', title=' - [COLOR fuchsia][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    if config.get_setting('developer_mode', default=False):
        itemlist.append(item.clone( action='show_channels_list', title= ' - [COLOR gold][B]Todos[/B][/COLOR] los Canales', tipo = 'all' ))

    itemlist.append(item.clone( action='show_channels_parameters', title=' - Qué [COLOR chocolate][B]Ajustes[/B][/COLOR] tiene en preferencias para Mostrar los Canales', thumbnail=config.get_thumb('news'), _mnu = True ))

    itemlist.append(item.clone( action='show_channels_list', title= ' - Qué canales están [COLOR gold][B]Disponibles[/B][/COLOR] (Activos)' ))
    itemlist.append(item.clone( action='show_channels_list', title= ' - Qué canales están [COLOR aquamarine][B]Sugeridos[/B][/COLOR]', suggesteds = True, thumbnail=config.get_thumb('suggested') ))

    itemlist.append(item.clone( action='', title= '[B][I]CANALES PERSONALIZACIÓN:[/I][/B]', text_color='goldenrod', folder=False ))
    itemlist.append(item.clone( action='channels_prefered', title= '    - Qué canales tiene marcados como [COLOR gold][B]Preferidos[/B][/COLOR]' ))
    itemlist.append(item.clone( action='channels_status', title= '    - Personalizar canales [COLOR gold][B]Preferidos[/B][/COLOR] (Marcar ó Des-marcar)', des_rea = False, _helper = True ))
    itemlist.append(item.clone( action='channels_no_actives', title= '    - Qué canales tiene marcados como [COLOR gray][B]Desactivados[/B][/COLOR]' ))
    itemlist.append(item.clone( action='channels_status', title= '    - Personalizar canales [COLOR gray][B]Desactivados[/B][/COLOR] (Desactivar ó Re-activar)', des_rea = True, _helper = True ))

    itemlist.append(item.clone( action='show_help_domains', title= '[B]CANALES GESTIÓN DOMINIOS[/B]', text_color='goldenrod' ))

    itemlist.append(item.clone( action='show_channels_list', title= '    - Qué canales tienen varios [COLOR gold][B]Dominios[/B][/COLOR]', var_domains = True ))

    itemlist.append(item.clone( action='show_channels_list', title= '    - En qué canales se puede gestionar el [COLOR gold][B]Último Dominio Vigente[/B][/COLOR]', last_domain = True ))

    itemlist.append(item.clone( action='channels_only_last_domain', title= '    - En qué canales tiene informado el [COLOR yellow][B]Último dominio Vigente[/B][/COLOR]' ))

    itemlist.append(item.clone( channel='actions', action='manto_domains', title= '    - Quitar los Dominios en los canales [COLOR darkorange][B](que los Tengan)[/B][/COLOR]' ))

    itemlist.append(item.clone( action='', title= '[B][I]CANALES CUENTAS:[/I][/B]', text_color='goldenrod', folder=False ))
    itemlist.append(item.clone( action='show_help_register', title= '    - [COLOR green][B]Información[/B][/COLOR] webs que requieren [COLOR gold][B]Registrarse[/B][/COLOR] (Cuenta)', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_channels_list', title= '    - Qué canales requieren [COLOR teal][B]Cuenta[/B][/COLOR]', cta_register = True ))

    itemlist.append(item.clone( action='', title= '[B][I]CANALES SITUACIÓN:[/I][/B]', text_color='goldenrod', folder=False ))

    itemlist.append(item.clone( action='channels_with_notice', title= '    - Qué canales tienen [COLOR green][B]Aviso[/COLOR][COLOR red] CloudFlare [COLOR orangered]Protection[/B][/COLOR]' ))

    itemlist.append(item.clone( action='channels_with_proxies', title= '    - Qué canales pueden necesitar [COLOR red][B]Proxies[/B][/COLOR]', new_proxies=True ))
    if config.get_setting('memorize_channels_proxies', default=True):
        itemlist.append(item.clone( action='channels_with_proxies_memorized', title= ' - Qué [COLOR red]canales[/COLOR] tiene con proxies [COLOR red][B]Memorizados[/B][/COLOR]', new_proxies=True, memo_proxies=True, test_proxies=True, thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='channels_with_crypto', title= '    - Qué canales requieren [COLOR darksalmon][B]Descifrar Enlaces[/B][/COLOR]' ))

    itemlist.append(item.clone( action='show_channels_list', title= '    - Qué canales están [COLOR plum][B]Inestables[/B][/COLOR]', no_stable = True ))
    itemlist.append(item.clone( action='show_channels_list', title= '    - Qué canales son [COLOR darkgoldenrod][B]Problemátios[/B][/COLOR] (Predominan Sin enlaces Disponibles/Válidos/Soportados)', problematics = True ))

    itemlist.append(item.clone( action='show_channels_list', title= '    - Qué canales son [COLOR aquamarine][B]Principales[/COLOR] con [COLOR turquoise]Clones[/B][/COLOR] Asociados', clons = True ))

    itemlist.append(item.clone( action='show_channels_list', title= '    - Qué canales son [COLOR turquoise][B]Clones[/B][/COLOR] (Clon del Canal [COLOR violet][B]Principal[/B][/COLOR])', clones = True ))

    itemlist.append(item.clone( action='show_channels_list', title= '    - Qué canales son [COLOR grey][B]Privados[/B][/COLOR]', tipo = 'all', privates = True ))

    if not PY3:
        itemlist.append(item.clone( action='show_channels_list', title= '    - Qué canales son [COLOR violet][B]Incompatibiles[/B][/COLOR] con su Media Center', mismatched = True ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categorías [COLOR gold][B]Canales, Dominios y Cuentas[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def show_infos_canales(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][B]CANALES Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title= ' - [COLOR tomato][B]Últimos Cambios Dominios[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_canales', title= ' - Resumen y Distribución Canales' ))

    if txt_status:
        if con_incidencias:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_incidencias', title= ' - Canales[COLOR tan][B] Con Incidencias[/B][/COLOR]' ))

        if no_accesibles:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_no_accesibles', title= ' - Canales[COLOR indianred][B] No Accesibles[/B][/COLOR]' ))

        if con_problemas:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_con_problemas', title=' - Canales [COLOR tomato][B]Con Problemas[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='show_channels_list_temporaries', title= '    - Qué canales están [COLOR cyan][B]Temporalmente[/B][/COLOR] inactivos' ))

    itemlist.append(item.clone( action='channels_no_searchables', title= ' - Qué canales [COLOR goldenrod][B]Nunca[/B][/COLOR] intervendrán en las búsquedas', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='show_help_tests', title= ' - Métodos para [COLOR chartreuse][B]Efectuar el Test Web[/B][/COLOR] en un canal', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_proxies', title= ' - [COLOR green][B]Información[/B][/COLOR] Uso de [COLOR red][B]Proxies[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='submnu_avisinfo_channels', title= ' - [COLOR aquamarine][B]Avisos[/COLOR] [COLOR green]Información[/B][/COLOR] canales' ))

    itemlist.append(item.clone( action='show_help_bloqueos', title= ' - ¿ Qué hacer si su Operadora [COLOR yellowgreen][B]Bloquea[/B][/COLOR] algún Canal ?', thumbnail=config.get_thumb('roadblock') ))

    itemlist.append(item.clone( action='show_help_resto', title= ' - ¿ Qué significa el Aviso [COLOR red][B]CloudFlare[/COLOR][COLOR orangered] Protection[/B][/COLOR] ?' ))

    itemlist.append(item.clone( action='show_channels_list_inactives', title= '    - Qué canales están [COLOR coral][B]Inactivos[/B][/COLOR]' ))

    itemlist.append(item.clone( action='show_channels_list_closed', title= '    - Qué canales están [COLOR darkgoldenrod][B]Cerrados[/B][/COLOR]' ))
    itemlist.append(item.clone( action='show_channels_list_voided', title= '    - Qué canales están [COLOR darkgoldenrod][B]Anulados[/B][/COLOR]' ))

    return itemlist


def show_help_bloqueos(item):
    logger.info()

    txt = '[B][COLOR cyan]Cuestión Preliminar:[/B][/COLOR][CR]'

    txt += '  Ciertas Operadoras pueden [COLOR yellowgreen][B]Bloquear[/B][/COLOR] el acceso a algún Canal.[CR]'
    txt += '  Incluso una misma Operadora puede [COLOR yellowgreen][B]Bloquear[/B][/COLOR] en una [COLOR violet][B]Zona Geográfica [/B][/COLOR]concreta[CR]'
    txt += '  y por el contrario en [COLOR violet][B]Otras Zonas Geográficas No[/B][/COLOR].[CR][CR]'

    txt += '[COLOR turquoise][B]VPN:[/B][/COLOR][CR]'

    txt += '  [B][COLOR darkcyan]El Uso de una [/COLOR][COLOR yellowgreen]VPN[/COLOR][COLOR darkcyan] jamás se saltará el control del Canal por [/COLOR][COLOR red]CloudFlare[/COLOR][COLOR orangered] Protection[/B][/COLOR][CR][CR]'

    txt += '  [B][COLOR gold]Si puede acceder a través de un Navegador de Internet al Canal[/B][/COLOR][CR]'
    txt += '  y [COLOR plum][B]No obtiene resultados[/B][/COLOR] desde su Media Center[CR][CR]'

    txt += '  1) Si el Canal dispone de la opción [COLOR red][B]Configurar proxies a usar[/B][/COLOR][CR]'
    txt += '   necesitará obligatoriamente también usar [COLOR red][B]Proxies[/B][/COLOR][CR][CR]'

    txt += '  2) En caso contrario [COLOR turquoise][B]Necesitará Instalar en su Equipo una [/B][/COLOR][COLOR yellowgreen][B]VPN[/B][/COLOR][CR]'
    txt += '  para saber donde obtener una [COLOR turquoise][B]VPN[/B][/COLOR] Acceda a la [COLOR chartreuse][B]Ayuda[/B][/COLOR][COLOR fuchsia][B] Cuestiones Preliminares[/B][/COLOR][COLOR goldenrod][B] Miscelánea[/B][/COLOR][CR]'

    txt += '  [CR][B][COLOR darkorange]Atención:[/COLOR][/B][CR]'

    txt += '  Si el acceso al Dominio del Canal, a través de un Navegador de Internet avisase con[CR]'
    txt += '  [COLOR orange][B]Verificando ...[/COLOR] [COLOR orangered]CLOUDFLARE[/B][/COLOR][CR]'
    txt += '  necesitará obligatoriamente usar [COLOR red][B]Proxies[/B][/COLOR] en el canal.[CR][CR]'

    txt += '[B][COLOR yellow]Los Canales Habitualmente NO Requieren[/COLOR] [COLOR red]Proxies[/COLOR][/B].[CR][CR]'

    txt += 'Determinadas webs Cambian de Dominio y es necesario modificarlo para permitir su acceso:[CR]'

    txt += '  [CR]*) A través de un Navegador de Internet, acceda al Dominio, que verá efectuando el[CR]'
    txt += '    [B][COLOR gold]Test Web del Canal[/COLOR][/B][CR]'
    txt += '    observe los datos [B][COLOR yellow]Host/Nuevo[/COLOR][/B] en la información de Test.[CR]'

    txt += '  [CR]*) ó bien si el canal dispone de la opción [COLOR yellowgreen][B]Configurar dominio a usar[/B][/COLOR][CR]'
    txt += '     deberá ir comprobando, cada uno de los Dominios Disponibles,[CR]'
    txt += '     accediendo a través de un Navegador de Internet, hasta dar con uno que sea [B][COLOR cyan]Válido[/B][/COLOR].[CR]'

    txt += '[CR][B][COLOR darkorange]Atención:[/COLOR][/B][CR]'

    txt += '  Si el acceso al Dominio, a través de un Navegador de Internet avisase con[CR]'
    txt += '  [COLOR orange][B]Verificando ...[/COLOR] [COLOR orangered]CLOUDFLARE[/B][/COLOR][CR]'
    txt += '  necesitará obligatoriamente usar [COLOR red][B]Proxies[/B][/COLOR].[CR]'

    txt += '[CR][B]Si el Canal NO dispone de la opción [COLOR goldenrod][B]Acciones[/COLOR] [COLOR plum](si no hay resultados)[/B][/COLOR]:[CR]'
    txt += '  - [B][COLOR cyan]NO puede solucionarlo y deberá comunicarlo en nuestro Telegram[/B][/COLOR].[CR]'

    txt += '[CR][B][COLOR limegreen]Si el resultado del acceso vía Internet fué Satisfactorio para evitar la restricción:[/B][/COLOR][CR]'

    txt += '  - si el Canal dispone de la opción [COLOR yellowgreen][B]Configurar dominio a usar[/B][/COLOR][CR]'
    txt += '    seleccione un Nuevo Dominio en [COLOR yellowgreen][B]Configurar dominio a usar[/B][/COLOR][CR][CR]'

    txt += '  - y/ó si el Canal dispone de la opción [COLOR red][B]Configurar proxies a usar[/B][/COLOR][CR]'
    txt += '    quizás necesitará obligatoriamente también usar [COLOR red][B]Proxies[/B][/COLOR]'

    platformtools.dialog_textviewer('Qué hacer si su Operadora Bloquea algún Canal', txt)


def submnu_avisinfo_channels(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]AVISOS Información Canales:[/B]', text_color='gold', folder=False ))

    datos = channeltools.get_channel_parameters('hdfull')
    if datos['active']:
        itemlist.append(item.clone( action='show_help_hdfull', title= ' - [COLOR aquamarine][B]Aviso[/COLOR] [COLOR green][B]Información[/B][/COLOR] canal [COLOR yellow][B]HdFull[/B][/COLOR]', thumbnail=config.get_thumb('hdfull', 'thumb', 'channels') ))

    datos = channeltools.get_channel_parameters('playdede')
    if datos['active']:
        itemlist.append(item.clone( action='show_help_playdede', title= ' - [COLOR aquamarine][B]Aviso[/COLOR] [COLOR green][B]Información[/B][/COLOR] canal [COLOR yellow][B]PlayDede[/B][/COLOR]', thumbnail=config.get_thumb('playdede', 'thumb', 'channels') ))

    itemlist.append(item.clone( action='show_help_resto', title= ' - Posible [COLOR aquamarine][B]Aviso[/COLOR] [COLOR green][B]Información[/B][/COLOR] en Otros [COLOR gold][B]Canales[/B][/COLOR]' ))

    return itemlist


def submnu_parental(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]ADULTOS PARENTAL:[/B]', text_color='orange', folder=False ))

    itemlist.append(item.clone( action='show_help_adults', title= ' - [COLOR green][B]Información [COLOR goldenrod]Control Parental [COLOR orange](+18)[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_parental_parameters', title= ' - [COLOR green][B]Información[/B][/COLOR] sobre sus [COLOR chocolate][B]Preferencias[/B][/COLOR] Actuales', thumbnail=config.get_thumb('news') ))

    if config.get_setting('adults_password', default=''):
        itemlist.append(item.clone( action='show_pin_parental', title= ' - [COLOR springgreen][B]Ver[/B][/COLOR] el PIN Parental', thumbnail=config.get_thumb('pencil') ))

        itemlist.append(item.clone( channel='actions', action='adults_password_del', title= ' - [COLOR red][B]Eliminar[/B][/COLOR] PIN parental', erase = True, folder=False, thumbnail=config.get_thumb('pencil') ))
    else:
        itemlist.append(item.clone( channel='actions', action='adults_password', title= ' - [COLOR goldenrod][B]Establecer[/B][/COLOR] un PIN Parental', thumbnail=config.get_thumb('pencil') ))

    presentar = True
    if descartar_xxx:
        if descartar_anime: presentar = False

    if presentar:
        if config.get_setting('mnu_animes', default=True):
            itemlist.append(item.clone( action='', title= '[B][I]CANALES CON POSIBLES ANIMES PARA ADULTOS:[/I][/B]', text_color='springgreen', folder=False, thumbnail=config.get_thumb('anime') ))

        itemlist.append(item.clone( action='channels_only_animes', title= '   - Qué canales [COLOR springgreen][B]Pueden[/B][/COLOR] Tener Contenido de Animes', thumbnail=config.get_thumb('anime') ))

        if not descartar_anime:
            itemlist.append(item.clone( action='channels_exclusively_animes', title= '   - Qué canales tienen contenido Exclusivamente de [COLOR springgreen][B]Animes[/B][/COLOR]', thumbnail=config.get_thumb('anime') ))

        if config.get_setting('mnu_adultos', default=True):
            itemlist.append(item.clone( action='', title= '[B][I]CANALES CON VÍDEOS PARA ADULTOS:[/I][/B]', text_color='orange' ))

        itemlist.append(item.clone( action='channels_only_adults', title= '   - Qué canales [COLOR orange][B]Pueden[/B][/COLOR] Tener Contenido Para Adultos' ))

        if not descartar_xxx:
            itemlist.append(item.clone( action='channels_exclusively_adults', title= '   - Qué canales tienen contenido Exclusivamente para [COLOR orange][B]Adultos[/B][/COLOR]' ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR orange][B]Parental[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_domains(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]DOMINIOS:[/B]', text_color='bisque', folder=False ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title= ' - [COLOR cyan][B]Últimos Cambios Dominios[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_domains', title= ' - [COLOR bisque][B]Gestión Dominios[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_channels_list', title= '    - Qué canales tienen varios [COLOR gold][B]Dominios[/B][/COLOR]', var_domains = True, thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='show_channels_list', title= '    - En qué canales se puede gestionar el [COLOR gold][B]Último Dominio Vigente[/B][/COLOR]', last_domain = True, thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='channels_only_last_domain', title= '    - En qué canales tiene informado el [COLOR yellow][B]Último dominio Vigente[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='actions', action='manto_domains', title= '    - Quitar los Dominios en los canales [COLOR darkorange][B](que los Tengan)[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR gold][B]Dominios[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_cuentas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]CUENTAS:[/B]', text_color='goldenrod', folder=False ))

    itemlist.append(item.clone( action='show_help_domains', title= ' - [COLOR bisque][B]Gestión Dominios[/B][/COLOR]', ctas=True, thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_register', title= ' - [COLOR green][B]Información[/B][/COLOR] webs que requieren [COLOR gold][B]Registrarse[/B][/COLOR] (Cuenta)', thumbnail=config.get_thumb('news') ))

    datos = channeltools.get_channel_parameters('hdfull')
    if datos['active']:
        itemlist.append(item.clone( action='', title= '[B][I]Cuenta Canal HdFull:[/I][/B]', text_color='gold', folder=False, thumbnail=config.get_thumb('hdfull', 'thumb', 'channels') ))

        itemlist.append(item.clone( action='show_help_hdfull', title= ' - [COLOR aquamarine][B]Aviso[/COLOR] [COLOR green][B]Información[/B][/COLOR] canal', _mnu = True, thumbnail=config.get_thumb('hdfull', 'thumb', 'channels') ))

        itemlist.append(item.clone( channel='hdfull', action='diagnosis_domain', title= ' - [COLOR darkgoldenrod][B]Diágnosis Acceso al canal[/B][/COLOR]', thumbnail=config.get_thumb('hdfull', 'thumb', 'channels') ))

        itemlist.append(item.clone( channel='domains', action='operative_domains_hdfull', title= ' - [COLOR mediumaquamarine][B]Dominios Operativos Vigentes[/COLOR][COLOR dodgerblue] dominioshdfull.com[/B][/COLOR]', thumbnail=config.get_thumb('hdfull', 'thumb', 'channels') ))

        itemlist.append(item.clone( channel='domains', action='latest_domains_hdfull', title= ' - [COLOR yellowgreen][B]Último Dominio Vigente[/B][/COLOR]', thumbnail=config.get_thumb('hdfull', 'thumb', 'channels') ))

        itemlist.append(item.clone( channel='domains', action='last_domain_hdfull', title= ' - [COLOR goldenrod][B]Asociar[/B][/COLOR] último Dominio Vigente [COLOR dodgerblue][B]dominioshdfull.com[/B][/COLOR]', thumbnail=config.get_thumb('hdfull', 'thumb', 'channels') ))

        cfg_user_channel = 'channel_hdfull_hdfull_username'
        cfg_pass_channel = 'channel_hdfull_hdfull_password'

        if not config.get_setting(cfg_user_channel, default='') or not config.get_setting(cfg_pass_channel, default=''):
            itemlist.append(item.clone( channel='submnuctext', action='_credenciales_hdfull', title= ' - [COLOR yellow][B]Informar[/B][/COLOR] Credenciales cuenta', thumbnail=config.get_thumb('pencil') ))
        else:
            itemlist.append(item.clone( channel='submnuctext', action='_credenciales_hdfull', title= ' - Test [COLOR chartreuse][B]Login[/B][/COLOR] Credenciales', thumbnail=config.get_thumb('hdfull', 'thumb', 'channels') ))

            itemlist.append(item.clone( channel='hdfull', action='show_credenciales', title= ' - [COLOR springgreen][B]Credenciales[/B][/COLOR]', thumbnail=config.get_thumb('hdfull', 'thumb', 'channels') ))
            itemlist.append(item.clone( channel='domains', action='del_datos_hdfull', title= ' - [COLOR red][B]Eliminar[/B][/COLOR] Credenciales', thumbnail=config.get_thumb('hdfull', 'thumb', 'channels') ))

    datos = channeltools.get_channel_parameters('playdede')
    if datos['active']:
        itemlist.append(item.clone( action='', title= '[B][I]Cuenta Canal PlayDede:[/I][/B]', text_color='gold', folder=False, thumbnail=config.get_thumb('playdede', 'thumb', 'channels') ))

        itemlist.append(item.clone( action='show_help_playdede', title= ' - [COLOR aquamarine][B]Aviso[/COLOR] [COLOR green][B]Información[/B][/COLOR] canal', thumbnail=config.get_thumb('playdede', 'thumb', 'channels') ))

        itemlist.append(item.clone( action='show_help_playdede_media_center', title= ' - [COLOR aquamarine][B]Aviso[/COLOR] [COLOR violet][B]Ubicación[/B][/COLOR] Media Center', thumbnail=config.get_thumb('playdede', 'thumb', 'channels') ))

        itemlist.append(item.clone( action='show_help_playdede_bloqueo', title= ' - [COLOR aquamarine][B]Aviso[/COLOR] [COLOR yellowgreen][B]Bloqueo[/B][/COLOR] Operadoras', thumbnail=config.get_thumb('playdede', 'thumb', 'channels') ))

        itemlist.append(item.clone( channel='playdede', action='show_current_domain', title= ' - [COLOR darkgoldenrod][B]Dominio Actual[COLOR dodgerblue] entrarplaydede.com[/B][/COLOR]', thumbnail=config.get_thumb('playdede', 'thumb', 'channels') ))

        itemlist.append(item.clone( channel='domains', action='last_domain_playdede', title= ' - [COLOR goldenrod][B]Asociar[/B][/COLOR] dominio actual [COLOR dodgerblue][B]privacidad.me/@playdede[/B][/COLOR]', thumbnail=config.get_thumb('playdede', 'thumb', 'channels') ))

        cfg_user_channel = 'channel_playdede_playdede_username'
        cfg_pass_channel = 'channel_playdede_playdede_password'

        if not config.get_setting(cfg_user_channel, default='') or not config.get_setting(cfg_pass_channel, default=''):
            itemlist.append(item.clone( channel='submnuctext', action='_credenciales_playdede', title= ' - [COLOR yellow][B]Informar[/B][/COLOR]  Credenciales cuenta', thumbnail=config.get_thumb('pencil') ))
        else:
            itemlist.append(item.clone( channel='submnuctext', action='_credenciales_playdede', title= ' - Test [COLOR chartreuse][B]Login[/B][/COLOR] Credenciales', thumbnail=config.get_thumb('playdede', 'thumb', 'channels') ))

            itemlist.append(item.clone( channel='playdede', action='show_credenciales', title= ' - [COLOR springgreen][B]Credenciales[/B][/COLOR]', thumbnail=config.get_thumb('playdede', 'thumb', 'channels') ))
            itemlist.append(item.clone( channel='domains', action='del_datos_playdede', title= ' - [COLOR red][B]Eliminar[/B][/COLOR] Credenciales', thumbnail=config.get_thumb('playdede', 'thumb', 'channels') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR goldenrod][B]Cuentas[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_audios(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]AUDIOS IDIOMAS:[/B]', folder=False, text_color='limegreen' ))

    itemlist.append(item.clone( action='show_help_audios', title= ' - [COLOR green][B]Información[/B][/COLOR] [COLOR cyan][B]Idiomas[/B][/COLOR] en los Audios de los Vídeos', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_play_parameters', title=' - Qué [COLOR chocolate][B]Ajustes[/B][/COLOR] tiene en preferencias [COLOR fuchsia][B]Play[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR fuchsia][B]Play[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_play(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]PLAY SERVIDORES:[/B]', folder=False, text_color='fuchsia' ))

    itemlist.append(item.clone( action='show_infos_play', title=' - [COLOR salmon][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    if config.get_setting('developer_mode', default=False):
        itemlist.append(item.clone( action='show_servers_list', title= ' - [COLOR darkorange][B]Todos[/B][/COLOR] los Servidores', tipo = 'all', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( action='show_play_parameters', title=' - Qué [COLOR chocolate][B]Ajustes[/B][/COLOR] tiene en preferencias [COLOR fuchsia][B]Play[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    presentar = False

    if config.get_setting('autoplay', default=False) or config.get_setting('autoplay_one_link', default=True): presentar = True

    if presentar:
        itemlist.append(item.clone( action='', title= '[B][I]AUTO PLAY:[/I][/B]', folder=False, text_color='orchid', thumbnail=config.get_thumb('bolt') ))

        if config.get_setting('autoplay', default=False):
            itemlist.append(item.clone( channel='actions', action='quitar_autoplay', title= ' - Quitar [COLOR fuchsia][B]Auto Play[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

        if config.get_setting('autoplay_one_link', default=True):
            itemlist.append(item.clone( channel='actions', action='quitar_autoplay_one_link', title= ' - Quitar [COLOR fuchsia][B]Auto Play[/B][/COLOR] Si solo hay [COLOR gold][B]Un enlace[/B][/COLOR] para reproducir', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_servers_list', title= ' - Qué servidores están [COLOR darkorange][B]Disponibles[/B][/COLOR] (Activos)', tipo = 'activos', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( action='', title= '[B][I]PLAY SERVIDORES VÍAS ALTERNATIVAS:[/I][/B]', folder=False, text_color='orchid', thumbnail=config.get_thumb('kodiaddons') ))

    itemlist.append(item.clone( action='show_infos_alternativas', title=' - [COLOR coral][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    if xbmc.getCondVisibility('System.HasAddon("inputstream.adaptive")'):
        cod_version = xbmcaddon.Addon("inputstream.adaptive").getAddonInfo("version").strip()
        tex_ia = '  ' + cod_version
    else: tex_ia = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action = '', title= ' - [COLOR goldenrod][B]InputStream Adaptive[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_ia + '[/B][/COLOR]', thumbnail=config.get_thumb('Inputstreamadaptive') ))

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        cod_version = xbmcaddon.Addon("script.module.resolveurl").getAddonInfo("version").strip()
        tex_mr = '  ' + cod_version
    else: tex_mr = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action = '', title= ' - [COLOR goldenrod][B]ResolveUrl[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_mr + '[/B][/COLOR]', thumbnail=config.get_thumb('resolveurl') ))

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
        cod_version = xbmcaddon.Addon("plugin.video.youtube").getAddonInfo("version").strip()
        tex_yt = '  ' + cod_version
    else: tex_yt = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action = '', title= ' - [COLOR goldenrod][B]Youtube[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_yt + '[/B][/COLOR]', thumbnail=config.get_thumb('youtube') ))

    itemlist.append(item.clone( action='', title= '[B][I]PLAY SERVIDORES SITUACIÓN:[/I][/B]', folder=False, text_color='orchid' ))

    if txt_status:
        if srv_pending:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_pending', title=' - Servidores [COLOR tan][B]Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( action='show_servers_list_out_service', title= '    - Qué servidores están [COLOR goldenrod][B]Sin Servicio[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))
    itemlist.append(item.clone( action='show_servers_list_inactives', title= '    - Qué servidores están [COLOR coral][B]Inactivos[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( action='', title= '[B][I]PLAY CANALES CON ENLACES CIFRADOS:[/I][/B]', folder=False, text_color='orchid' ))

    itemlist.append(item.clone( action='channels_with_crypto', title= '    - Qué canales requieren [COLOR darksalmon][B]Descifrar Enlaces[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    if config.get_setting('developer_mode', default=False):
        itemlist.append(item.clone( action='', title= '[B][I]PLAY CANALES CON UN ÚNICO SERVIDOR:[/I][/B]', folder=False, text_color='orchid' ))

        itemlist.append(item.clone( action='show_channels_list', title= '    - Qué [COLOR gold][B]Canales[/COLOR] tienen [COLOR orchid]Solo un servidor[/B][/COLOR]', onlyone = True, thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR fuchsia][B]Play[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def show_infos_play(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR salmon][B]PLAY Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_servidores', title= ' - Resumen y Distribución Servidores', thumbnail=config.get_thumb('bolt') ))

    if txt_status:
        if con_incidencias:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_incidencias', title= '    - Canales[COLOR tan][B] Con Incidencias[/B][/COLOR]' ))

        if no_accesibles:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_no_accesibles', title= '    - Canales[COLOR indianred][B] No Accesibles[/B][/COLOR]' ))

        if con_problemas:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_con_problemas', title='    - Canales[COLOR tomato][B] Con Problemas[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='show_server_report', title= ' - Reportar [COLOR gold][B]Reproducción de lista abortada[/B][/COLOR]', thumbnail=config.get_thumb('megaphone') ))

    itemlist.append(item.clone( action='show_not_play', title= ' - ¿ Qué [COLOR goldenrod][B]NO[/B][/COLOR] está contemplado en Balandro ?', thumbnail=config.get_thumb('roadblock') ))

    itemlist.append(item.clone( action='show_help_recaptcha', title= ' - ¿ Qué significa Requiere verificación [COLOR red][B]reCAPTCHA[/B][/COLOR] ?', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_acortador', title= ' - ¿ Qué significa Tiene [COLOR plum][B]Acortador[/B][/COLOR] del enlace ?', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_server_report', title= ' - Como [COLOR deepskyblue][B]Reportar[/B][/COLOR] posible Fallo en la Reproducción de Servidores', thumbnail=config.get_thumb('telegram') ))

    itemlist.append(item.clone( action='submnu_avisinfo_servers', title= '    - [COLOR aquamarine][B]Avisos[/COLOR] [COLOR green]Información[/B][/COLOR] servidores', thumbnail=config.get_thumb('bolt') ))
    itemlist.append(item.clone( action='show_servers_list', title= '    - Qué servidores se detectan pero [COLOR fuchsia][B]No están Soportados[/B][/COLOR]', tipo = 'sinsoporte', thumbnail=config.get_thumb('roadblock') ))
    itemlist.append(item.clone( action='show_help_not_programed', title= '    - ¿ Qué significa [COLOR red][B]Sin enlaces soportados[/B][/COLOR] ?', thumbnail=config.get_thumb('news') ))

    if txt_status:
        if srv_pending:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_pending', title='[COLOR fuchsia][B]Servidores [COLOR tan]Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='- [COLOR violet][B]Filtre[/B][/COLOR] Servidores en [COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR fuchsia][B]Play[/B][/COLOR])', thumbnail=config.get_thumb('bolt') ))

    return itemlist


def show_infos_alternativas(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR coral][B]PLAY SERVIDORES VÍAS ALTERNATIVAS Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_vias', title= ' - ¿ Dónde obtener Add-Ons para Vías Alternativas ?', thumbnail=config.get_thumb('news') ))

    if not xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        itemlist.append(item.clone( action='show_help_vias', title= ' - [COLOR green][B]Información[/B][/COLOR] vía alternativa [COLOR goldenrod][B]ResolveUrl[/B][/COLOR]', only_resolve=True, thumbnail=config.get_thumb('resolveurl') ))

    if not PY3:
        itemlist.append(item.clone( action='show_help_youtube', title= ' - [COLOR red][B]Incompatibilidad[/B][/COLOR] vía alternativa [COLOR goldenrod][B]Youtube[/B][/COLOR]', thumbnail=config.get_thumb('youtube') ))
    else:
        if not xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
            itemlist.append(item.clone( action='show_help_vias', title= ' - [COLOR green][B]Información[/B][/COLOR] vía alternativa [COLOR goldenrod][B]Youtube[/B][/COLOR]', only_youtube=True, thumbnail=config.get_thumb('youtube') ))

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
       itemlist.append(item.clone( action='show_servers_list', title= '    - Qué servidores tienen [COLOR yellow][B]Vías Alternativas[/B][/COLOR]', tipo = 'alternativos', thumbnail=config.get_thumb('bolt') ))

       itemlist.append(item.clone( channel='submnuteam', action='show_help_adicionales', title= '    - Servidores [COLOR goldenrod][B]Vías Adicionales[/B][/COLOR] a través de [COLOR yellowgreen][B]ResolveUrl[/B][/COLOR]', thumbnail=config.get_thumb('resolveurl') ))
    else:
       itemlist.append(item.clone( action='', title= '- [COLOR yellow][B]ResolveUrl[/B][/COLOR] [COLOR red][B]No Instalado[/B][/COLOR]', thumbnail=config.get_thumb('resolveurl') ))

    if not xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
       itemlist.append(item.clone( action='', title= '- [COLOR yellow][B]YouTube[/B][/COLOR] [COLOR red][B]No Instalado[/B][/COLOR]', thumbnail=config.get_thumb('youtube') ))

    return itemlist


def submnu_avisinfo_servers(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]AVISOS Imformación Servidores:[/B]', text_color='gold', folder=False, thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( action='show_help_gamovideo', title= ' - [COLOR green][B]Información[/B][/COLOR] servidor [COLOR darkorange][B]Gamovideo[/B][/COLOR]', thumbnail=config.get_thumb('gamovideo') ))

    itemlist.append(item.clone( action='show_help_mega', title= ' - [COLOR green][B]Información[/B][/COLOR] servidor [COLOR darkorange][B]Mega[/B][/COLOR]', thumbnail=config.get_thumb('mega') ))

    itemlist.append(item.clone( action='show_help_uptobox', title= ' - [COLOR green][B]Información[/B][/COLOR] servidor [COLOR darkorange][B]Uptobox[/B][/COLOR]', thumbnail=config.get_thumb('uptobox') ))

    return itemlist


def submnu_proxies(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]PROXIES:[/B]', folder=False, text_color='red' ))

    itemlist.append(item.clone( action='show_infos_proxies', title=' - [COLOR fuchsia][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_prx_parameters', title= ' - [COLOR green][B]Información[/B][/COLOR] sobre sus [COLOR chocolate][B]Preferencias[/B][/COLOR] Actuales', thumbnail=config.get_thumb('news') ))

    path = os.path.join(config.get_data_path(), 'Lista-proxies.txt')

    existe = filetools.exists(path)

    if existe:
        itemlist.append(item.clone( action='', title= '[B][I]PROXIES FICHERO LISTA-PROXIES.TXT:[/I][/B]', folder=False, text_color='red', thumbnail=config.get_thumb('flame') ))

        itemlist.append(item.clone( action='show_yourlist', title= ' - [COLOR green][B]Información[/B][/COLOR] de su Fichero Personal [COLOR gold][B]Lista-proxies.txt[/B][/COLOR]', thumbnail=config.get_thumb('pencil') ))

        itemlist.append(item.clone( channel='actions', action='manto_yourlist', title= ' - [COLOR red][B]Eliminar[/B][/COLOR] su Fichero [COLOR gold][B]Lista-proxies.txt[/B][/COLOR]', thumbnail=config.get_thumb('settings') ))

    itemlist.append(item.clone( action='', title= '[B][I]PROXIES SITUACIÓN:[/I][/B]', folder=False, text_color='red', thumbnail=config.get_thumb('flame') ))

    itemlist.append(item.clone( action='channels_with_proxies', title= ' - Qué canales pueden usar Proxies', new_proxies=True, test_proxies=True, thumbnail=config.get_thumb('stack') ))
    if config.get_setting('memorize_channels_proxies', default=True):
        itemlist.append(item.clone( action='channels_with_proxies_memorized', title= ' - Qué [COLOR red][B]Canales[/B][/COLOR] tiene con proxies Memorizados', new_proxies=True, memo_proxies=True, test_proxies=True, thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='actions', action = 'manto_proxies', title= ' - Quitar los proxies en los canales [COLOR red][B](que los Tengan)[/B][/COLOR]', thumbnail=config.get_thumb('flame') ))

    itemlist.append(item.clone( channel='actions', action = 'global_proxies', title = ' - Configurar Proxies a usar [COLOR plum][B](en los canales que los Necesiten)[/B][/COLOR]', thumbnail=config.get_thumb('flame') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR red][B]Proxies[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def show_infos_proxies(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][B]PROXIES Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_proxies', title= ' - [COLOR green][B]Información[/B][/COLOR] Uso de [COLOR red][B]Proxies[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_providers', title= ' - [COLOR green][B]Información[/B][/COLOR][COLOR magenta][B] Proveedores[/B][/COLOR] de proxies', thumbnail=config.get_thumb('news') ))

    if config.get_setting('proxies_extended', default=False): 
        itemlist.append(item.clone( action='show_help_providers2', title= ' - [COLOR green][B]Información[/B][/COLOR] Lista [COLOR aqua][B]Ampliada[/B][/COLOR] de [COLOR magenta][B]Proveedores[/B][/COLOR] de proxies', thumbnail=config.get_thumb('news') ))

    if config.get_setting('proxies_vias', default=False): 
        itemlist.append(item.clone( action='proxies_show_vias', title= ' - [COLOR green][B]Información[/B][/COLOR] Lista [COLOR aqua][B]Vías Alternativas[/B][/COLOR] de [COLOR magenta][B]Proveedores[/B][/COLOR] de proxies', thumbnail=config.get_thumb('news') ))

        if config.get_setting('developer_mode', default=False):
            itemlist.append(item.clone( channel='submnuteam', action='test_tplus', title= ' - Asignar proveedor de proxies[COLOR goldenrod][B]TPlus[/B][/COLOR]', thumbnail=config.get_thumb('settings') ))

    itemlist.append(item.clone( action='show_help_recommended', title= ' - Qué [COLOR magenta][B]Proveedores[/B][/COLOR] de proxies están [COLOR lime][B]Recomendados[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_metodos', title= ' - [COLOR green][B]Información[/B][/COLOR] Métodos para [COLOR red][B]Quitar los Proxies[/B][/COLOR] en un canal', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_yourlist', title= ' - [COLOR green][B]Información[/B][/COLOR] [COLOR goldenrod][B]Gestión[/B][/COLOR] Fichero [COLOR gold][B]Lista-proxies.txt[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    return itemlist


def submnu_torrents(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]TORRENTS:[/B]', folder=False, text_color='blue' ))

    itemlist.append(item.clone( action='show_infos_torrents', title=' - [COLOR fuchsia][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_torrents_parameters', title= ' - [COLOR green][B]Información[/B][/COLOR] sobre sus [COLOR chocolate][B]Preferencias[/B][/COLOR] Actuales', thumbnail=config.get_thumb('news') ))

    if config.get_setting('mnu_torrents', default=True):
        cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

        if cliente_torrent == 'Seleccionar' or cliente_torrent == 'Ninguno': tex_tor = cliente_torrent
        else:
          tex_tor = cliente_torrent
          cliente_torrent = 'plugin.video.' + cliente_torrent.lower()
          if xbmc.getCondVisibility('System.HasAddon("%s")' % cliente_torrent):
              cod_version = xbmcaddon.Addon(cliente_torrent).getAddonInfo("version").strip()
              tex_tor += '  [COLOR yellow]' + cod_version + '[/COLOR]'

        itemlist.append(item.clone( action = '', title= '- Cliente/Motor Habitual asignado ' + '[COLOR fuchsia][B] ' + tex_tor + '[/B][/COLOR]', thumbnail=config.get_thumb('torrents') ))

    if config.get_setting('mnu_torrents', default=True):
        itemlist.append(item.clone( action='channels_only_torrents', title= ' - Qué canales pueden contener archivos Torrent', thumbnail=config.get_thumb('stack') ))
        itemlist.append(item.clone( action='channels_exclusively_torrents', title= ' - Qué canales tienen enlaces Torrent [COLOR goldenrod][B]Exclusivamente[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR blue][B]Torrents[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def show_infos_torrents(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][B]TORRENTS Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_torrents', title= ' - ¿ Dónde obtener los Add-Ons para [COLOR gold][B]Clientes/Motores[/B][/COLOR] torrents ?', thumbnail=config.get_thumb('news') ))
    itemlist.append(item.clone( action='show_clients_torrent', title= ' - Clientes/Motores externos torrent [COLOR gold][B]Soportados[/B][/COLOR]', thumbnail=config.get_thumb('cloud') ))

    if config.get_setting('mnu_torrents', default=True):
        if not xbmc.getCondVisibility('System.HasAddon("plugin.video.elementum")'):
            itemlist.append(item.clone( channel='helper', action='show_help_vias', title= ' - [COLOR green][B]Información[/B][/COLOR] Vía alternativa [COLOR goldenrod][B]Elementum[/B][/COLOR]', only_elementum=True, thumbnail=config.get_thumb('elementum') ))
        else:
            itemlist.append(item.clone( action='show_help_elementum', title= ' - [COLOR green][B]Información[/B][/COLOR] Motor Torrent [COLOR goldenrod][B]Elementum[/B][/COLOR]', thumbnail=config.get_thumb('elementum') ))

            itemlist.append(item.clone( action='show_help_semillas', title= ' - [COLOR green][B]Información[/B][/COLOR] archivos Torrent [COLOR gold][B]Semillas[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    return itemlist


def submnu_buscar(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]BUSCAR:[/B]', folder=False, text_color='yellow' ))

    itemlist.append(item.clone( action='show_infos_buscar', title=' - [COLOR fuchsia][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_help_parameters_search', title=' - Qué [COLOR chocolate][B]Ajustes[/B][/COLOR] tiene en preferencias para las Búsquedas', thumbnail=config.get_thumb('news') ))

    if config.get_setting('search_show_last', default=True):
        itemlist.append(item.clone( channel='actions', action = 'manto_textos', title= ' - Quitar los [COLOR coral][B]Textos[/COLOR][/B] Memorizados de las búsquedas', thumbnail=config.get_thumb('pencil') ))

    itemlist.append(item.clone( action='channels_no_actives', title= ' - Qué canales no intervienen en las búsquedas [COLOR gray][B]Desactivados[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='actions', action = 'global_proxies', title = ' - Configurar Proxies a usar [COLOR plum][B](en los canales que los Necesiten)[/B][/COLOR]', thumbnail=config.get_thumb('flame') ))

    itemlist.append(item.clone( channel='filters', action = 'mainlist2', title = ' - [COLOR greenyellow][B]Efectuar búsquedas [COLOR gold](solo en determinados canales)[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    txt_exc = ''

    if config.get_setting('search_excludes_movies', default=''): txt_exc += '[COLOR deepskyblue][B]Películas[/B][/COLOR] '
    if config.get_setting('search_excludes_tvshows', default=''): txt_exc += '[COLOR hotpink][B]Series[/B][/COLOR] '
    if config.get_setting('search_excludes_documentaries', default=''): txt_exc += '[COLOR cyan][B]Documentales[/B][/COLOR] '
    if config.get_setting('search_excludes_torrents', default=''): txt_exc += '[COLOR blue][B]Torrents[/B][/COLOR] '
    if config.get_setting('search_excludes_mixed', default=''): txt_exc += '[COLOR yellow][B]Películas y/ó Series[/B][/COLOR] '
    if config.get_setting('search_excludes_all', default=''): txt_exc += '[COLOR green][B]Todos[/B][/COLOR] '

    if txt_exc:
        txt_exc.strip()
        txt_exc = '[COLOR chocolate][B] hay en [/B][/COLOR]' + txt_exc

    itemlist.append(item.clone( channel='filters', action = 'mainlist', title = ' - [COLOR cyan][B]Excluir canales en las búsquedas[/B][/COLOR]' + txt_exc, thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR yellow][B]Buscar[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def show_infos_buscar(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][B]BUSCAR Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_canales', title= ' - Resumen y Distribución Canales', thumbnail=config.get_thumb('stack') ))

    if txt_status:
        if con_incidencias:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_incidencias', title= '    - Canales[COLOR tan][B] Con Incidencias[/B][/COLOR]' ))

        if no_accesibles:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_no_accesibles', title= '    - Canales[COLOR indianred][B] No Accesibles[/B][/COLOR]' ))

        if con_problemas:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_con_problemas', title='    - Canales[COLOR tomato][B] Con Problemas[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='channels_no_searchables', title= ' - Qué canales [COLOR goldenrod][B]Nunca[/B][/COLOR] intervendrán en las búsquedas', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='show_help_bucle', title = ' - Las Búsquedas hacen [COLOR yellow][B]Bucle [COLOR goldenrod](piden de nuevo el texto a buscar)[/COLOR][/B]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='search', action='show_help', title = ' - [COLOR green][B]Información[/B][/COLOR] sobre Búsquedas', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_help_audios', title= ' - [COLOR green][B]Información[/B][/COLOR] [COLOR cyan][B]Idiomas[/B][/COLOR] en los Audios de los Vídeos', thumbnail=config.get_thumb('news') ))

    if config.get_setting('search_extra_main', default=False):
        itemlist.append(item.clone( channel='tmdblists', action='show_help', title= ' - [COLOR green][B]Información[/B][/COLOR] Búsquedas y Listas en [COLOR violet][B]TMDB[/B][/COLOR]', thumbnail=config.get_thumb('news') ))
        itemlist.append(item.clone( channel='filmaffinitylists', action='show_help', title= ' - [COLOR green][B]Información[/B][/COLOR] Búsquedas y Listas en [COLOR violet][B]Filmaffinity[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    return itemlist


def submnu_preferidos(item):
    logger.info()
    itemlist = []

    path = os.path.join(config.get_data_path(), 'tracking_dbs')

    existe = filetools.exists(path)
    if not existe:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Aún no tiene Preferidos[/COLOR][/B]' % color_exec)

    itemlist.append(item.clone( action='', title='[B]PREFERIDOS:[/B]', folder=False, text_color='wheat' ))

    itemlist.append(item.clone( action='show_infos_preferidos', title=' - [COLOR fuchsia][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_preferidos_parameters', title= ' - [COLOR green][B]Información[/B][/COLOR] sobre sus [COLOR chocolate][B]Preferencias[/B][/COLOR] Actuales', thumbnail=config.get_thumb('news') ))

    if existe:
        itemlist.append(item.clone(channel='tracking', action='doit_tracking_shows', title= ' - [COLOR violet][B]Buscar ahora nuevos episodios[/B][/COLOR]', thumbnail=config.get_thumb('search') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR wheat][B]Preferidos[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def show_infos_preferidos(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][B]PREFERIDOS Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action = 'show_help_tracking', title = ' - [COLOR green][B]Información[/B][/COLOR] ¿ Cómo funciona ?', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action = 'show_help_tracking_update', title = ' - [COLOR green][B]Información[/B][/COLOR] Búsqueda automática de [COLOR cyan][B]Nuevos Episodios[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    if no_accesibles:
        itemlist.append(item.clone( channel='submnuteam', action='resumen_no_accesibles', title= ' - [COLOR green][B]Información[/B][/COLOR] Canales[COLOR indianred][B] No Accesibles[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    if con_problemas:
        itemlist.append(item.clone( channel='submnuteam', action='resumen_con_problemas', title=' - [COLOR green][B]Información[/B][/COLOR] Canales[COLOR tomato][B] Con Problemas[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    return itemlist


def submnu_descargas(item):
    logger.info()
    itemlist = []

    downloadpath = config.get_setting('downloadpath', default='')

    if downloadpath: path = downloadpath
    else: path = filetools.join(config.get_data_path(), 'downloads')

    existe = filetools.exists(path)
    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Aún no tiene Descargas[/COLOR][/B]' % color_exec)

    itemlist.append(item.clone( action='', title='[B]DESCARGAS:[/B]', folder=False, text_color='seagreen' ))

    itemlist.append(item.clone( action='show_infos_descargas', title=' - [COLOR fuchsia][B]Cuestiones Preliminares[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action='show_ubicacion', title= ' - [COLOR green][B]Información[/B][/COLOR] sobre sus [COLOR chocolate][B]Preferencias[/B][/COLOR] Actuales', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR seagreen][B]Descargas[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def show_infos_descargas(item):
    logger.info()
    itemlist = []

    downloadpath = config.get_setting('downloadpath', default='')

    if downloadpath: path = downloadpath
    else: path = filetools.join(config.get_data_path(), 'downloads')

    existe = filetools.exists(path)

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][B]DESCARGAS Cuestiones Preliminares:[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action = 'show_help_descargas', title = ' - [COLOR green][B]Información[/B][/COLOR] ¿ Cómo funcionan ?', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action='show_ubicacion', title= ' - ¿ Donde se ubican las [COLOR seagreen][B]Descargas[/B][/COLOR] ?', thumbnail=config.get_thumb('news') ))

    if existe:
        itemlist.append(item.clone( channel='downloads', action = 'show_folder_downloads', title = ' - [B]Ubicación actual de las[/B] [COLOR seagreen][B]Descargas[/B][/COLOR]', thumbnail=config.get_thumb('downloads') ))

    itemlist.append(item.clone( channel='helper', action = 'show_help_usb', title = ' - ¿ [B]Se puede Descargar directamente en una[/B] [COLOR goldenrod][B]Unidad USB[/B][/COLOR] ?', thumbnail=config.get_thumb('usb') ))

    itemlist.append(item.clone( channel='helper', action='show_not_download', title= ' - ¿ Qué [COLOR goldenrod][B]NO[/B][/COLOR] está contemplado en las [COLOR seagreen][B]Descargas[/B][/COLOR] ?', thumbnail=config.get_thumb('roadblock') ))

    return itemlist


def submnu_config(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]AJUSTES CATEGORÍAS:[/B]', folder=False, text_color='chocolate', thumbnail=config.get_thumb('settings') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Info[/B]', text_color='turquoise', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Menú[/B]', text_color='tan', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Canales[/B]', text_color='gold', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Parental[/B]',  text_color='orange', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Dominios[/B]',  text_color='bisque', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Cuentas[/B]',  text_color='goldenrod', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Play[/B]',  text_color='fuchsia', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Proxies[/B]',  text_color='red', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Torrents[/B]',  text_color='blue', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Buscar[/B]',  text_color='yellow', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Preferidos[/B]',  text_color='wheat', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Descargas[/B]',  text_color='seagreen', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Actualizar[/B]',  text_color='cyan', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Visual[/B]',  text_color='coral', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - TMDB[/B]',  text_color='darkorange', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Sistema[/B]',  text_color='pink', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Ayuda[/B]',  text_color='chartreuse', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Versión[/B]',  text_color='violet', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Contacto[/B]',  text_color='teal', thumbnail=config.get_thumb('settings') ))
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B] - Team[/B]',  text_color='firebrick', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_actualizar(item):
    logger.info()
    itemlist = []

    access_fixes = False
    tex_access_fixes = ''

    avisar = False

    if not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developergenres.py')): avisar = True
    elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')): avisar = True
    elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')): avisar = True

    try:
       data = httptools.downloadpage(ADDON_UPDATES_JSON).data
       if data:
           if '404: Not Found' in data: tex_access_fixes = '[COLOR red][B][I] (No Accesibles)[/I][/B][/COLOR]'
           else: access_fixes = True

           if 'addon_version' not in data or 'fix_version' not in data: access_fixes = None

           if not access_fixes is None:
               try: last_ver = updater.check_addon_version()
               except: last_ver = None

               if not last_ver is None:
                   text_dev = ''
                   if config.get_setting('developer_mode', default=False):
                       if not avisar:
                           text_dev = ' [COLOR darkorange][B]Desarrollo[/B][/COLOR]'
                       else:
                           text_dev = ' [COLOR darkorange][B]Falso Desarrollo[/B][/COLOR]'

                   if not last_ver: tex_access_fixes = text_dev + '[COLOR indianred][B][I] (Versión desfasada, NO recibe Fixes)[/I][/B][/COLOR]'

       else: tex_access_fixes = '[COLOR red][B] No se pudo comprobar[/B][/COLOR]'
    except: tex_access_fixes = '[COLOR red][B] No se pudo comprobar[/B][/COLOR]'

    if not tex_access_fixes:
        tex_access_fixes = '[COLOR goldenrod][B] Accesibles[/B][/COLOR]'
        if access_fixes == None: tex_access_fixes = '[COLOR yellow][B] (Sin actualizaciones Fix pendientes)[/B][/COLOR]'
        elif access_fixes == False: tex_access_fixes = '[I][B][COLOR red]  (No Accesibles)[/COLOR][/B][/I]'
    else:
        if 'No se pudo comprobar' in tex_access_fixes: tex_access_fixes = '[B][I][COLOR gray] (OFF LINE)[/COLOR][/I][/B] ' + tex_access_fixes

    itemlist.append(item.clone( action='', title='[B]ACTUALIZAR FIXES:[/B]' + tex_access_fixes, folder=False, text_color='cyan' ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title= ' - [COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_test', title= ' - Test [COLOR yellow][B]Status[/B][/COLOR] del sistema', thumbnail=config.get_thumb('addon') ))

    if config.get_setting('addon_update_atstart', default=True):
        itemlist.append(item.clone( action='', title= ' - Comprobar Fixes al [COLOR goldenrod][B]Iniciar[/B][/COLOR] su Media Center [COLOR yellow][B]Activado[/B][/COLOR]', thumbnail=config.get_thumb('settings') ))
    else:
        itemlist.append(item.clone( action='', title= ' - Comprobar Fixes al [COLOR goldenrod][B]Iniciar[/B][/COLOR] su Media Center [COLOR red][B]Des-Activado[/B][/COLOR]', thumbnail=config.get_thumb('settings') ))

    itemlist.append(item.clone( action='show_help_fixes', title= ' - ¿ Qué son los [COLOR coral][B]Fix[/B][/COLOR] ?', thumbnail=config.get_thumb('news') ))

    last_fix = config.get_addon_version()

    if 'fix' in last_fix:
        itemlist.append(item.clone( action='show_last_fix', title= ' - [COLOR green][B]Información[/B][/COLOR] último Fix instalado', thumbnail=config.get_thumb('news') ))

        itemlist.append(item.clone( action='resumen_fix', title= ' - [COLOR darkcyan][B]Resumen[/B][/COLOR] Fix Instalado', thumbnail=config.get_thumb('news') ))

        itemlist.append(item.clone( channel='actions', action='manto_last_fix', title= " - [COLOR red][B]Eliminar[/B][/COLOR] fichero control 'Fix'", thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action = 'check_addon_updates', title= ' - [COLOR goldenrod][B]Comprobar[/B][/COLOR] últimas actualizaciones tipo Fix', thumbnail=config.get_thumb('download') ))
    itemlist.append(item.clone( channel='actions', action = 'check_addon_updates_force', title= ' - [COLOR fuchsia][B]Forzar[/B][/COLOR] Todas las actualizaciones tipo Fix', thumbnail=config.get_thumb('download') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR cyan][B]Actualizar[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_mediacenter(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]MEDIA CENTER:[/B]', folder=False, text_color='pink' ))

    itemlist.append(item.clone( action='show_plataforma', title= ' - Información [COLOR yellow][B]Plataforma[/B][/COLOR]', thumbnail=config.get_thumb('news') ))
    itemlist.append(item.clone( action='show_help_centers', title= ' - [COLOR violet][B]¿ Dónde obtener soporte para su Media Center ?[/B][/COLOR]', thumbnail=config.get_thumb('youtube') ))

    if not config.get_setting('developer_mode', default=False):
        loglevel = config.get_setting('debug', 0)

        if loglevel == 0: tex_niv = 'Solo Errores'
        elif loglevel == 1: tex_niv = 'Errores e Información'
        else: tex_niv = 'Máxima Información'

        itemlist.append(item.clone( action='', title= '- Nivel de información del fichero [COLOR aqua][B]LOG[/B][/COLOR]' + ' [COLOR chocolate][B]' + tex_niv + '[/B][/COLOR]', thumbnail=config.get_thumb('computer') ))

    itemlist.append(item.clone( action='show_report', title= ' - [COLOR red][B]Reportar un Problema[/B][/COLOR] en la Ejecución de Balandro', thumbnail=config.get_thumb('telegram') ))

    itemlist.append(item.clone( action='show_log', title= ' - Visualizar el fichero [COLOR cyan][B]LOG[/B][/COLOR] de su Media Center', thumbnail=config.get_thumb('computer') ))
    itemlist.append(item.clone( action='copy_log', title= ' - Obtener una Copia del fichero [COLOR cyan][B]LOG[/B][/COLOR] de su Media Center', thumbnail=config.get_thumb('folder') ))
    itemlist.append(item.clone( channel='submnuteam', action='balandro_log', title= ' - Visualizar el fichero [COLOR cyan][B]LOG[/COLOR] ([COLOR coral]solo ejecución Balandro[/B][/COLOR])', thumbnail=config.get_thumb('computer') ))

    path_advs = translatePath(os.path.join('special://home/userdata', ''))

    file_advs = 'advancedsettings.xml'
    file = path_advs + file_advs
    existe = filetools.exists(file)

    if existe:
       itemlist.append(item.clone( action='show_advs', title= ' - Visualizar fichero [COLOR goldenrod][B]AdvancedSettings[/B][/COLOR] de su Media Center', thumbnail=config.get_thumb('quote') ))
       itemlist.append(item.clone( channel='actions',  action='manto_advs', title= ' - [COLOR red][B]Eliminar[/B][/COLOR] fichero [COLOR goldenrod][B]AdvancedSettings[/B][/COLOR] de su Media Center', thumbnail=config.get_thumb('quote') ))

    path_favs = translatePath(os.path.join('special://home/userdata', ''))

    file_favs = 'favourites.xml'
    file = path_favs + file_favs
    existe = filetools.exists(file)

    if existe:
        txt_favs = ''

        try:
           with open(os.path.join(path, file_favs), 'r') as f: txt_favs=f.read(); f.close()
        except:
           try: txt_favs = open(os.path.join(path, file_favs), encoding="utf8").read()
           except: pass

        bloque = scrapertools.find_single_match(txt_favs, '<favourites>(.*?)</favourites>')

        matches = bloque.count('<favourite')

        if matches == 0: existe = False

    if existe:
        itemlist.append(item.clone( action='show_favs', title= ' - Visualizar fichero [COLOR goldenrod][B]FavouritesSettings[/B][/COLOR] de su Media Center', thumbnail=config.get_thumb('quote') ))

    path_pcfs = translatePath(os.path.join('special://home/userdata', ''))

    file_pcfs = 'playercorefactory.xml'

    file = path_pcfs + file_pcfs

    existe = filetools.exists(file)

    if existe:
        itemlist.append(item.clone( action='show_pcfs', title= ' - Visualizar fichero [COLOR goldenrod][B]PlayerCoreFactorySettings[/B][/COLOR] de su Media Center', thumbnail=config.get_thumb('quote') ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR pink][B]Sistema[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_sistema(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title= '[B]SISTEMA:[/B]', folder=False, text_color='teal' ))

    itemlist.append(item.clone( channel='submnuteam', action='show_sistema', title= ' - [COLOR green][B]Información [COLOR goldenrod][B]Ajustes[/B][/COLOR] del [COLOR teal][B]Sistema[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_test', title= ' - Test [COLOR yellow][B]Status[/B][/COLOR] del sistema', thumbnail=config.get_thumb('addon') ))
    itemlist.append(item.clone( channel='actions', title= ' - Comprobar el estado de su [COLOR gold][B]Internet[/B][/COLOR]', action = 'test_internet', thumbnail=config.get_thumb('crossroads') ))

    if config.get_setting('developer_mode', default=False):
        itemlist.append(item.clone( action='', title= '[B][I]SISTEMA TESTS:[/I][/B]', folder=False, text_color='teal', thumbnail=config.get_thumb('addon') ))

        itemlist.append(item.clone( channel='submnuteam', action='submnu_canales', title= ' - Test [COLOR gold][B]Canales[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))
        itemlist.append(item.clone( channel='submnuteam', action='submnu_servidores', title= ' - Test [COLOR fuchsia][B]Servidores[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))
        itemlist.append(item.clone( channel='submnuteam', action='submnu_proxies', title= ' - Test [COLOR red][B]Proxies[/B][/COLOR]', thumbnail=config.get_thumb('flame') ))

    itemlist.append(item.clone( action='', title= '[B][I]SISTEMA INFORMACIONES:[/I][/B]', folder=False, text_color='teal', thumbnail=config.get_thumb('addon') ))

    path = os.path.join(config.get_data_path(), 'Lista-proxies.txt')

    existe = filetools.exists(path)

    if existe:
        itemlist.append(item.clone( action='show_yourlist', title= ' - [COLOR green][B]Información[/B][/COLOR] de su Fichero Personal [COLOR limegreen][B]Lista-proxies.txt[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_cook', title= ' - Visualizar su fichero de cookies', thumbnail=config.get_thumb('folder') ))
    itemlist.append(item.clone( action='show_sets', title= ' - Visualizar sus [COLOR chocolate][B]Ajustes[/B][/COLOR] Personalizados', thumbnail=config.get_thumb('folder') ))
 
    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR teal][B]Sistema[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_clean(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]LIMPIEZAS:[/B]', folder=False, text_color='olive', thumbnail=config.get_thumb('quote') ))

    itemlist.append(item.clone( action='show_help_clean', title= ' - [COLOR green][B]Información[/B][/COLOR] Limpiezas', thumbnail=config.get_thumb('news'), text_color='olive' ))

    itemlist.append(item.clone( channel='submnuteam', action='submnu_center', title=' - [B]Limpieza [COLOR pink]Media Center[/COLOR][/B]', helper = True, thumbnail=config.get_thumb('mediacenter'), text_color='olive' ))
    itemlist.append(item.clone( channel='submnuteam', action='submnu_addons', title=' - [B]Limpieza [COLOR yellowgreen]Add-Ons[/COLOR][/B]', helper = True, thumbnail=config.get_thumb('kodiaddons'), text_color='olive' ))
    itemlist.append(item.clone( channel='submnuteam', action='submnu_sistema', title=' - [B]Limpieza [COLOR violet]Sistema[/COLOR][/B]', helper = True, thumbnail=config.get_thumb('computer'), text_color='olive' ))
    itemlist.append(item.clone( channel='submnuteam', action='submnu_logs', title=' - [B]Limpieza [COLOR limegreen]Logs[/COLOR][/B]', helper = True, thumbnail=config.get_thumb('tools'), text_color='olive' ))
    itemlist.append(item.clone( channel='submnuteam', action='submnu_temporales', title=' - [B]Limpieza [COLOR powderblue]Temporales[/COLOR][/B]', helper = True, thumbnail=config.get_thumb('tools'), text_color='olive' ))

    itemlist.append(item.clone( channel='actions', action='manto_proxies', title=' - [B]Limpieza [COLOR red]Proxies[/COLOR][/B]', thumbnail=config.get_thumb('flame'), text_color='olive' ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR olive][B]Sistema[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_version(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]VERSIONES:[/B]', folder=False, text_color='violet', thumbnail=config.get_thumb('addon') ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title= ' - [COLOR cyan][B]Últimos Cambios Dominios[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_version', title= ' - [COLOR green][B]Información[/B][/COLOR] Versión', thumbnail=config.get_thumb('news') ))
    itemlist.append(item.clone( action='show_changelog', title= ' - [COLOR goldenrod][B]Historial[/B][/COLOR] de Versiones', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='', title='[B]VERSIÓN RESÚMENES:[/B]', folder=False, text_color='violet', thumbnail=config.get_thumb('addon') ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_canales', title= ' -  Resumen y Distribución [COLOR gold][B]Canales[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    if txt_status:
        if con_incidencias:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_incidencias', title= ' -  Canales[COLOR tan][B] Con Incidencias[/B][/COLOR]' ))

        if no_accesibles:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_no_accesibles', title= ' -  Canales[COLOR indianred][B] No Accesibles[/B][/COLOR]' ))

        if con_problemas:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_con_problemas', title=' -  Canales[COLOR tomato][B] Con Problemas[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='submnuteam', action='resumen_servidores', title= ' -  Resumen y Distribución [COLOR fuchsia][B]Servidores[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    if txt_status:
        if srv_pending:
            itemlist.append(item.clone( channel='submnuteam', action='resumen_pending', title='[COLOR fuchsia][B]Servidores [COLOR tan]Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    return itemlist


def submnu_desarrollo(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]DESARROLLO TEAM:[/B]', folder=False, text_color='firebrick', thumbnail=config.get_thumb('team') ))

    itemlist.append(item.clone( action='show_help_notice', title= '[COLOR aqua][B]Comunicado[/B][/COLOR] Oficial de Balandro', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='', title= '[COLOR firebrick][B][I]DESARROLLO DEVELOPERS:[/I][/B][/COLOR]', folder=False, thumbnail=config.get_thumb('team') ))

    itemlist.append(item.clone( action='show_dev_notes', title= ' - Notas para Developers (desarrolladores)', thumbnail=config.get_thumb('news') ))

    if config.get_setting('developer_mode', default=False):
        avisar = False

        if not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developergenres.py')): avisar = True
        elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')): avisar = True
        elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')): avisar = True

        if not avisar:
            tex_des = 'Desarrollo'
        else:
            tex_des = 'Falso Desarrollo'

        itemlist.append(item.clone( channel='submnuteam', action='submnu_team', title = ' - Acceso a la opción de [COLOR goldenrod][B]' + tex_des + '[/B][/COLOR]', thumbnail=config.get_thumb('team') ))

    itemlist.append(item.clone( action='', title= '[COLOR firebrick][B][I]DESARROLLO FUENTES:[/I][/B][/COLOR]', folder=False, thumbnail=config.get_thumb('team') ))

    itemlist.append(item.clone( action='', title= ' - Fuentes [COLOR darkorange][B]github.com/repobal/[/B][/COLOR]', thumbnail=config.get_thumb('addon'), folder=False ))

    itemlist.append(item.clone( action='', title= '[COLOR firebrick][B][I]DESARROLLO TELEGRAM:[/I][/B][/COLOR]', folder=False, thumbnail=config.get_thumb('team') ))

    itemlist.append(item.clone( action='', title= ' - Team ' + _team + ' Equipo de Desarrollo', folder=False, thumbnail=config.get_thumb('telegram') ))

    itemlist.append(item.clone( action='', title= '[COLOR firebrick][B][I]DESARROLLO INCORPORACIONES:[/I][/B][/COLOR]', folder=False, thumbnail=config.get_thumb('team') ))

    itemlist.append(item.clone( action='', title='[COLOR yellow][B]  Solicitudes solo con Enlace de Invitación[/B][/COLOR]', folder=False, thumbnail=config.get_thumb('pencil') ))

    itemlist.append(item.clone( action='', title= '  Foro ' + _foro, thumbnail=config.get_thumb('foro'), folder=False ))
    itemlist.append(item.clone( action='', title= '  Telegram ' + _telegram, thumbnail=config.get_thumb('telegram'), folder=False ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title= '[COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR pink][B]Team[/B][/COLOR])', thumbnail=config.get_thumb('settings') ))

    return itemlist


def submnu_legalidad(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]LEGALIDAD:[/B]', folder=False, text_color='yellowgreen' ))

    itemlist.append(item.clone( action='show_legalidad', title= ' - Cuestiones Legales', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='show_license', title= ' - Licencia (Gnu Gpl v3)', thumbnail=config.get_thumb('news') ))

    return itemlist


def channels_only_animes(item):
    logger.info()

    filters.only_animes(item)

def channels_exclusively_animes(item):
    logger.info()

    item.exclusively_animes = True

    filters.only_animes(item)

def channels_only_adults(item):
    logger.info()

    filters.only_adults(item)

def channels_exclusively_adults(item):
    logger.info()

    item.exclusively_adults = True

    filters.only_adults(item)

def show_channels_list(item):
    logger.info()

    filters.show_channels_list(item)

def show_channels_list_cca(item):
    logger.info()

    item. cta_register = True

    filters.show_channels_list(item)

def show_channels_list_temporaries(item):
    logger.info()

    item.temp_no_active = True

    filters.show_channels_list(item)

def show_channels_list_inactives(item):
    logger.info()

    item.no_active = True

    filters.show_channels_list(item)

def show_channels_list_closed(item):
    logger.info()

    item.closed = True

    filters.show_channels_list(item)

def show_channels_list_voided(item):
    logger.info()

    item.voided = True

    filters.show_channels_list(item)

def channels_only_last_domain(item):
    logger.info()

    item.last_domain = True
    item.only_last_domain = True

    filters.show_channels_list(item)

def channels_status(item):
    logger.info()

    filters.channels_status(item)

def channels_des_rea(item):
    logger.info()

    item.des_rea = True

    filters.channels_status(item)

def channels_with_proxies(item):
    logger.info()

    filters.with_proxies(item)

def channels_with_proxies_memorized(item):
    logger.info()

    # por si venimos de config
    if config.get_setting('memorize_channels_proxies', default=True):
        item.memo_proxies = True

        filters.with_proxies(item)

def channels_no_actives(item):
    logger.info()

    filters.no_actives(item)

def channels_no_searchables(item):
    logger.info()

    item.no_searchables = True

    filters.no_actives(item)

def channels_prefered(item):
    logger.info()

    filters.only_prefered(item)

def channels_suggesteds(item):
    logger.info()

    item.suggesteds = True

    filters.show_channels_list(item)

def channels_inestables(item):
    logger.info()

    item.no_stable = True

    filters.show_channels_list(item)

def channels_problematicos(item):
    logger.info()

    item.problematics = True

    filters.show_channels_list(item)

def channels_clons(item):
    logger.info()

    item.clons = True

    filters.show_channels_list(item)

def channels_clones(item):
    logger.info()

    item.clones = True

    filters.show_channels_list(item)

def channels_with_notice(item):
    logger.info()

    item.notices = True

    filters.show_channels_list(item)

def channels_with_crypto(item):
    logger.info()

    item.cryptos = True

    filters.show_channels_list(item)

def channels_only_torrents(item):
    logger.info()

    filters.only_torrents(item)

def channels_exclusively_torrents(item):
    logger.info()

    item.exclusively_torrents = True

    filters.only_torrents(item)

def show_clients_torrent(item):
    logger.info()

    if not item.title: item.title = 'soportados'

    filters.show_clients_torrent(item)

def show_servers_list(item):
    logger.info()

    # por si venimos de config
    if not item.tipo: item.tipo = 'activos'

    filters.show_servers_list(item)

def show_servers_list_out_service(item):
    logger.info()

    item.tipo = 'outservice'

    filters.show_servers_list(item)

def show_servers_list_inactives(item):
    logger.info()

    item.tipo = 'inactivos'

    filters.show_servers_list(item)

def show_servers_unsoported(item):
    logger.info()

    item.tipo = 'sinsoporte'

    filters.show_servers_list(item)

def show_help_miscelanea(item):
    logger.info()

    txt = '[COLOR gold][B]KODI MEDIA CENTER:[/B][/COLOR][CR]'
    txt += '  [B][COLOR tan]Kodi Versiones Oficiales Soportadas:[/COLOR][/B][CR]'
    txt += '  [COLOR darkorange][B]22.x Piers,  21.x Omega,  20.x Nexus,  19.x Matrix,  18.x Leia  y  17.x Krypton[/B][/COLOR][CR][CR]'

    txt += '  Kodi [COLOR yellow]Oficial[/COLOR]:  [COLOR plum][B]kodi.tv/download/[/B][/COLOR][CR]'
    txt += '  para obtener la [COLOR yellowgreen]Última versión[/COLOR] de este Media Center[CR][CR]'

    txt += '  Kodi [COLOR yellow]Oficial[/COLOR]:  [COLOR plum][B]mirrors.kodi.tv/releases/[/B][/COLOR][CR]'
    txt += '  para obtener [COLOR yellowgreen]versiones Anteriores[/COLOR] a la última de este Media Center[CR][CR]'

    txt += '  Kodi [COLOR chartreuse]Soporte:  [/COLOR][COLOR lightblue][B]kodi.wiki/view/[/B][/COLOR][CR]'
    txt += '  para [COLOR yellowgreen]Consultas[/COLOR] sobre su Media Center[CR][CR]'

    txt += '[COLOR fuchsia][B]KODI CONSULTAS:[/B][/COLOR][CR]'
    txt += '  [COLOR yellow][B]Mundo Kodi[/B][/COLOR]:  [COLOR plum][B]mundokodi.com[/B][/COLOR][CR]'
    txt += '  para obtener [COLOR yellowgreen]Tutoriales, Instalaciones, Funciones, Add-Ons, Noticias, etc.[/COLOR][CR][CR]'

    txt += '[COLOR limegreen][B]ADD-ONS EXTERNOS CONSULTAS:[/B][/COLOR][CR]'
    txt += '  [COLOR yellow][B]PluginsXbmc[/B][/COLOR]:  [COLOR plum][B]www.pluginsxbmc.com[/B][/COLOR][CR]'
    txt += '  para obtener [COLOR yellowgreen]Tutoriales, Instalaciones, Funciones, Add-Ons, Noticias, etc.[/COLOR][CR][CR]'

    txt += '[COLOR turquoise][B]VPN:[/B][/COLOR][CR]'

    txt += '  [COLOR yellow][B]Warp de CloudFlare[/B][/COLOR]:  [COLOR plum][B]one.one.one.one[/B][/COLOR][CR]'
    txt += '  disponible para [COLOR yellowgreen]Android, Linux, MacOS, Windows[/COLOR][CR][CR]'

    txt += '[COLOR yellow][B]BALANDRO:[/B][/COLOR][CR]'

    txt += '  Fuente [COLOR yellow]Balandro[/COLOR]:  [COLOR plum][B]repobal.github.io/base/[/B][/COLOR][CR]'
    txt += '  para obtener [COLOR yellowgreen]Repositorio, Add-On, Scripts, etc.[/COLOR][CR][CR]'

    txt += '  Foro:  [COLOR coral][B]www.mimediacenter.info/foro/[/B][/COLOR][CR]'
    txt += '  para [COLOR yellowgreen]Instalaciones, Tutoriales, Sugerencias, etc.[/COLOR][CR][CR]'

    txt += '  [COLOR chartreuse]Telegram[/COLOR]:  [COLOR lightblue][B]t.me/balandro_asesor[/B][/COLOR][CR]'
    txt += '  para [COLOR yellowgreen]Asesoramiento, Dudas, Consultas, etc.[/COLOR][CR][CR]'

    txt += '[COLOR chocolate][B]DESARROLLO BALANDRO:[/B][/COLOR][CR]'

    txt += '  [COLOR firebrick]Fuentes Desarrollo[/COLOR] [COLOR yellow]Balandro[/COLOR]:  [COLOR darkorange][B]github.com/repobal/[/B][/COLOR][CR]'
    txt += '  para [COLOR orange]Mantenimiento del Add-On, Scripts, etc.[/COLOR][CR][CR]'

    txt += '  [COLOR chartreuse]Telegram[/COLOR]:  [COLOR lightblue][B]t.me/Balandro_team[/B][/COLOR][CR]'
    txt += '  para unirse al [COLOR yellowgreen]Equipo de desarrollo[/COLOR][CR][CR]'

    txt += '[COLOR blue][B]AGRADECIMIENTOS:[/B][/COLOR][CR]'

    txt += '  Cita destacada a los miembros de Balandro Team[CR]'
    txt += '  Mención especial al grupo de Balandro Checkers[CR][CR]'

    txt += '[COLOR yellowgreen][B]RECONOCIMIENTOS:[/B][/COLOR][CR]'

    txt += '  A los creadores de Elementum,  InputStream adaptive,'
    txt += '  ResolveUrl  y  YouTube Plugin'

    platformtools.dialog_textviewer('Información Miscelánea', txt)


def show_pin_parental(item):
    logger.info()

    if not config.get_setting('adults_password'):
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Aún no tiene Pin parental[/COLOR][/B]' % color_exec)
        return

    if not platformtools.dialog_yesno(config.__addon_name + ' PIN Parental', '[COLOR cyan][B]Si olvidó el Pin Parental, para poder verlo, necesitará un código de autorizacion y deberá solicitarlo en [/B][/COLOR]' + _telegram + ' [COLOR yellow][B]¿ Tiene el Código ?[/B][/COLOR]'): 
        return

    auth_pin = platformtools.dialog_input('', 'Código Autorización Pin')
    if not auth_pin: return

    auth_pin = auth_pin.upper().strip()

    if not auth_pin == 'PINBAL':
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Código Autorización incorrecto[/COLOR][/B]' % color_avis)
        return

    txt = '[COLOR goldenrod][B]PIN:  [COLOR yellow]' + str(config.get_setting('adults_password')) + '[/B][/COLOR]'

    platformtools.dialog_textviewer('Información PIN Parental', txt)


def show_help_bucle(item):
    logger.info()

    txt = '[CR][COLOR gold][B]¿ Porqué la opción [/COLOR][COLOR yellow]Buscar[/COLOR][COLOR gold] entra em modo bucle (vuelve a solicitar el texto a localizar) ?[/B][/COLOR][CR]'
    txt += 'Add-Ons de Programas que pueden afectar al funcionamiento de las búsquedas:[CR]'
    txt += '  [COLOR yellowgreen][B]LimpiarKodi,  LimpiaTuKodi,  EzMaintenace,  Indigo  y  similares[/B][/COLOR].'

    txt += '[CR][CR]Cuando desde estos Add-Ons se ejecuta la función [COLOR gold][B]Limpiar Cache y Rom[/B][/COLOR],'
    txt += ' se elimina la carpeta interna de la caché de su Media Center Kodi [COLOR gold][B].../.kodi/temp/archive_cache/[/B][/COLOR]'
    txt += ' y ello provoca que este no pueda cachear. Al no poder usar esta caché, puede influir en el rendimiento en general de todos los Add-Ons,'
    txt += ' pero donde resulta una molestia dentro de Balandro (y demás Add-Ons) es al buscar, ya que después de hacer una búsqueda y entrar en alguno de los resultados,'
    txt += ' al volver atrás, vuelve a solicitar de nuevo la introducción de texto, cuando debería volver a mostrar la lista de resultados previa.'

    txt += '[CR][CR][COLOR yellow][B]Este problema se resuelve:[/B][/COLOR] Re-iniciando su Media center Kodi, ya que Kodi vuelve a generar la carpeta de caché al iniciarse.'
    txt += ' Cualquier Add-On que en lugar de eliminar el contenido del caché para limpiar, elimine la propia carpeta provocará este mismo efecto.'

    txt += '[CR][CR][COLOR magenta][B]Si el problema aún persistiera, recomendamos [COLOR yellow]Desactivar ó Eliminar[/COLOR][COLOR magenta] esos Add-Ons de [/COLOR][COLOR gold]Limpieza[/B][/COLOR].'

    platformtools.dialog_textviewer('Información Si las Búsquedas hacen Bucle (solicitan de nuevo el texto a localizar)', txt)


def show_help_register(item):
    logger.info()

    txt = '*) Determinadas webs obligan a registrarse para permitir su acceso.'

    txt += '[CR][CR]    Es aconsejable usar [B][COLOR yellow]Cuentas Secundarias[/COLOR][/B] para registrarse,[CR]'
    txt += '    [B][COLOR cyan]Nunca Useis las Vuestras Personales[/B][/COLOR].'

    txt += '[CR][CR]*) Para ello desde otro equipo debeis acceder a la web en cuestión y registraros (darse de alta)'

    txt += '[CR][CR]    [COLOR goldenrod][B]Acceder a:[/B][/COLOR][CR]'

    presentar = True

    if item.desde_el_canal:
        if not item.channel_id == 'hdfull': presentar = False

    if presentar:
        datos = channeltools.get_channel_parameters('hdfull')
        if datos['active']:
            txt += '      [COLOR yellow][B]HdFull  [/COLOR][COLOR cyan]dominioshdfull.com[/B][/COLOR]'

    presentar = True

    if item.desde_el_canal:
        if not item.channel_id == 'playdede': presentar = False

    if presentar:
        datos = channeltools.get_channel_parameters('playdede')
        if datos['active']:
            txt += '[CR]      [COLOR yellow][B]PlayDede  [/COLOR][COLOR cyan]privacidad.me/@playdede[/B][/COLOR][CR]'
            txt += '      [COLOR yellow][B]PlayDede  [/COLOR][COLOR cyan]entrarplaydede.com[/COLOR][/B][CR]'
            txt += '      [COLOR yellow][B]PlayDede  [/COLOR][COLOR gold]X [/COLOR] [COLOR cyan]x.com/playdedesocial[/COLOR][/B]'

    txt += '[CR][CR]*) Los datos de [B][COLOR gold]Usuario y/ó Contraseña[/COLOR][/B] No pueden ser Solo Números..'
    txt += '[CR]     Imprescindible tomar buena Nota de vuestro [B][COLOR gold]Usuario y Contraseña[/COLOR][/B] para la web.'

    txt += '[CR][CR]*) Una vez tengáis vuestros datos, podéis informarlos en los [B][COLOR chocolate]Ajustes[/COLOR] [COLOR yellow](categoría Cuentas)[/COLOR][/B]'
    txt += '[CR]     ó bien se os solicitará al acceder a ese canal determinado.'

    txt += '[CR][CR][COLOR yellowgreen][B]Sesiones:[/B][/COLOR]'

    txt += '[CR]   Mientras mantengáis la [COLOR chartreuse][B]Sesion Abierta[/B][/COLOR] en esa Web,[CR]'
    txt += '   no tendreis que volver a informar vuestras Credenciales.'

    presentar = False

    datos = channeltools.get_channel_parameters('hdfull')
    if datos['active']:
        if config.get_setting('hdfull_login', 'hdfull', default=False): presentar = True

    if not presentar:
        datos = channeltools.get_channel_parameters('playdede')
        if datos['active']:
            if config.get_setting('playdede_login', 'playdede', default=False): presentar = True

    if presentar:
        txt += '[CR][CR]   [B][COLOR goldenrod]Atención[/COLOR][/B]:[CR]'
        txt += '     las [COLOR chartreuse][B]Sesiones Abiertas[/B][/COLOR] en vuestro Media Center [B][COLOR goldenrod]No son In Eternum[/COLOR][/B],[CR]'
        txt += '     por ello es conveniente [COLOR plum][B](si no hay Resultados)[/B][/COLOR],[CR]'
        txt += '     que procedaís a [COLOR chartreuse][B]Cerrar vuestra Sesión[/B][/COLOR] cada cierto tiempo.'

    txt_channel = 'Información dominios que requieren Registrarse'

    if item.desde_el_canal:
        if item.channel_id == 'hdfull': txt_channel = 'Información para Registrarse en HdFull'
        elif item.channel_id == 'playdede': txt_channel = 'Información para Registrarse en PlayDede'

    platformtools.dialog_textviewer(txt_channel, txt)


def show_help_animejl(item):
    item.notice = 'animejl'
    show_help_canales(item)

def show_help_animeonline(item):
    item.notice = 'animeonline'
    show_help_canales(item)

def show_help_cine24h(item):
    item.notice = 'cine24h'
    show_help_canales(item)

def show_help_cinecalidad(item):
    item.notice = 'cinecalidad'
    show_help_canales(item)

def show_help_cinecalidadla(item):
    item.notice = 'cinecalidadla'
    show_help_canales(item)

def show_help_cinecalidadlol(item):
    item.notice = 'cinecalidadlol'
    show_help_canales(item)

def show_help_cinemitas(item):
    item.notice = 'cinemitas'
    show_help_canales(item)

def show_help_cuevana3pro(item):
    item.notice = 'cuevana3pro'
    show_help_canales(item)

def show_help_cuevana3run(item):
    item.notice = 'cuevana3run'
    show_help_canales(item)

def show_help_detodo(item):
    item.notice = 'detodo'
    show_help_canales(item)

def show_help_doramasyt(item):
    item.notice = 'doramasyt'
    show_help_canales(item)

def show_help_dpeliculas(item):
    item.notice = 'dpeliculas'
    show_help_canales(item)

def show_help_entrepeliculasyseries(item):
    item.notice = 'entrepeliculasyseries'
    show_help_canales(item)

def show_help_flixcorn(item):
    item.notice = 'flixcorn'
    show_help_canales(item)

def show_help_gnula(item):
    item.notice = 'gnula'
    show_help_canales(item)

def show_help_gnula24(item):
    item.notice = 'gnula24'
    show_help_canales(item)

def show_help_gnula24h(item):
    item.notice = 'gnula24h'
    show_help_canales(item)

def show_help_hdfull(item):
    item.notice = 'hdfull'
    show_help_canales(item)

def show_help_henaojara(item):
    item.notice = 'henaojara'
    show_help_canales(item)

def show_help_homecine(item):
    item.notice = 'homecine'
    show_help_canales(item)

def show_help_jkanime(item):
    item.notice = 'jkanime'
    show_help_canales(item)

def show_help_latanime(item):
    item.notice = 'latanime'
    show_help_canales(item)

def show_help_masnovelas(item):
    item.notice = 'masnovelas'
    show_help_canales(item)

def show_help_megaserie(item):
    item.notice = 'megaserie'
    show_help_canales(item)

def show_help_mundodonghua(item):
    item.notice = 'mundodonghua'
    show_help_canales(item)

def show_help_papayaseries(item):
    item.notice = 'papayaseries'
    show_help_canales(item)

def show_help_peliculaspro(item):
    item.notice = 'peliculaspro'
    show_help_canales(item)

def show_help_pelisforte(item):
    item.notice = 'pelisforte'
    show_help_canales(item)

def show_help_pelispanda(item):
    item.notice = 'pelispanda'
    show_help_canales(item)

def show_help_pelisxd(item):
    item.notice = 'pelisxd'
    show_help_canales(item)

def show_help_pelisyseries(item):
    item.notice = 'pelisyseries'
    show_help_canales(item)

def show_help_pgratishd(item):
    item.notice = 'pgratishd'
    show_help_canales(item)

def show_help_playdede(item):
    item.notice = 'playdede'
    show_help_canales(item)

def show_help_ppeliculas(item):
    item.notice = 'ppeliculas'
    show_help_canales(item)

def show_help_pplus(item):
    item.notice = 'pplus'
    show_help_canales(item)

def show_help_rarbg(item):
    item.notice = 'rarbg'
    show_help_canales(item)

def show_help_rojotorrent(item):
    item.notice = 'rojotorrent'
    show_help_canales(item)

def show_help_seriespapayato(item):
    item.notice = 'seriespapayato'
    show_help_canales(item)

def show_help_seriesretro(item):
    item.notice = 'seriesretro'
    show_help_canales(item)

def show_help_srnovelas(item):
    item.notice = 'srnovelas'
    show_help_canales(item)

def show_help_subtorrents(item):
    item.notice = 'subtorrents'
    show_help_canales(item)

def show_help_yaskeorg(item):
    item.notice = 'yaskeorg'
    show_help_canales(item)

def show_help_zonaleros(item):
    item.notice = 'zonaleros'
    show_help_canales(item)

def show_help_resto(item):
    item.notice = ''
    show_help_canales(item)


def show_help_canales(item):
    logger.info()

    if item.notice:
        datos = channeltools.get_channel_parameters(item.notice)
        if not datos['active']:
            platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]El canal está Inactivo[/B][/COLOR]' % color_avis)
            return

    txt = '[COLOR turquoise][B]VPN:[/B][/COLOR][CR]'

    txt += '  [B][COLOR darkcyan]El Uso de una [/COLOR][COLOR yellowgreen]VPN[/COLOR][COLOR darkcyan] jamás se saltará el control del Canal por [/COLOR][COLOR red]CloudFlare[/COLOR][COLOR orangered] Protection[/B][/COLOR][CR][CR]'

    txt += '  [B][COLOR gold]Si puede acceder a través de un Navegador de Internet al Canal[/B][/COLOR][CR]'
    txt += '  y [COLOR plum][B]No obtiene resultados[/B][/COLOR] desde su Media Center[CR][CR]'

    txt += '  1) Si el Canal dispone de la opción [COLOR red][B]Configurar proxies a usar[/B][/COLOR][CR]'
    txt += '   necesitará obligatoriamente también usar [COLOR red][B]Proxies[/B][/COLOR][CR][CR]'

    txt += '  2) En caso contrario [COLOR turquoise][B]Necesitará Instalar en su Equipo una [/B][/COLOR][COLOR yellowgreen][B]VPN[/B][/COLOR][CR]'
    txt += '  para saber donde obtener una [COLOR turquoise][B]VPN[/B][/COLOR] Acceda a la [COLOR chartreuse][B]Ayuda[/B][/COLOR][COLOR fuchsia][B] Cuestiones Preliminares[/B][/COLOR][COLOR goldenrod][B] Miscelánea[/B][/COLOR][CR]'

    txt += '  [CR][B][COLOR darkorange]Atención:[/COLOR][/B][CR]'

    txt += '  Si el acceso al Dominio del Canal, a través de un Navegador de Internet avisase con[CR]'
    txt += '  [COLOR orange][B]Verificando ...[/COLOR] [COLOR orangered]CLOUDFLARE[/B][/COLOR][CR]'
    txt += '  necesitará obligatoriamente usar [COLOR red][B]Proxies[/B][/COLOR] en el canal.[CR][CR]'

    if not item.notice:
        txt += '[CR][B][COLOR yellow]Los Canales Habitualmente NO Requieren[/COLOR] [COLOR red]Proxies[/COLOR][/B][CR][CR]'

    if item.notice == 'hdfull' or item.notice == 'playdede':
        txt += '[B][COLOR yellow]Este Canal Habitualmente NO Requiere[/COLOR] [COLOR red]Proxies[/COLOR][CR]'

        if config.get_setting('channel_' + item.notice + '_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        if item.notice == 'playdede':
            txt += '[CR]'
        else:
            if item._mnu:
               txt += '[CR]Dispone de varios Dominios en [B][COLOR yellowgreen]Configurar dominio a usar ...[/B][/COLOR] que son [B][COLOR goldenrod]Clones[/COLOR][/B][CR]'
               txt += ' y [B][COLOR yellow]Puede Asociar Cualquiera de Ellos[/COLOR][/B], [B][COLOR green]Independientemente del que usó para Registrar su Cuenta.[/COLOR][/B][CR][CR]'

    if item.notice: txt += '[B][COLOR cyan]El webmaster de [COLOR yellow]' + item.notice.capitalize() + '[/COLOR] ha activado un nivel más de protección con [COLOR orangered]CloudFlare[/COLOR][/B][CR]'
    else: txt += '[B][COLOR cyan]El webmaster del [COLOR yellow]Canal[/COLOR] ha activado un nivel más de protección con [COLOR orangered]CloudFlare[/COLOR][/B][CR]'

    if item.notice == 'hdfull' or item.notice == 'playdede':
        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

        if item.notice == 'hdfull': txt += '[CR][COLOR yellow]  Para conocer el dominio actual acceder a través de un Navegador de Internet a[/COLOR] [B][COLOR greenyellow]dominioshdfull.com[/COLOR][/B][CR]'

        elif item.notice == 'playdede':
           txt += '[CR][COLOR yellow]  Para conocer el dominio actual acceder a través de un Navegador de Internet a[/COLOR] [B][COLOR goldenrod]privacidad.me/@playdede[/COLOR][/B][CR]'
           txt += '[COLOR yellow]  También puede acceder a su[/COLOR][COLOR gold][B] Telegram[/B] [B][COLOR greenyellow]entrarplaydede,com[/COLOR][/B][CR]'
           txt += '[COLOR yellow]  ó bien acceder a su [/COLOR][COLOR gold][B]X [/COLOR] [B][COLOR greenyellow] x.com/playdedesocial[/COLOR][/B][CR]'

    elif item.notice == 'animeojl':
        if config.get_setting('channel_animejl_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'animeonline':
        if config.get_setting('channel_animeonline_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'cine24h':
        if config.get_setting('channel_cine24h_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'cinecalidad':
        if config.get_setting('channel_cinecalidad_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'cinecalidadla':
        if config.get_setting('channel_cinecalidadla_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'cinecalidadlol':
        if config.get_setting('channel_cinecalidadlol_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'cinemitas':
        if config.get_setting('channel_cinemitas_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'cuevana3pro':
        if config.get_setting('channel_cuevana3pro_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'
        txt += '[COLOR yellow][B][CR]Además efectuan control de acceso que puede [COLOR indianred]Bloquear[/COLOR] la Web incluso con el uso [COLOR red]Proxies[/COLOR].[/COLOR][/B][CR]'

    elif item.notice == 'cuevana3run':
        if config.get_setting('channel_cuevana3run_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'detodo':
        if config.get_setting('channel_detodo_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'doramasyt':
        if config.get_setting('channel_doramasyt_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'dpeliculas':
        if config.get_setting('channel_dpeliculas_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'entrepeliculasyseries':
        if config.get_setting('channel_entrepeliculasyseries_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'flixcorn':
        if config.get_setting('channel_flixcorn_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'gnula':
        if config.get_setting('channel_gnula_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'gnula24':
        if config.get_setting('channel_gnula24_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'gnula24h':
        if config.get_setting('channel_gnula24h_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'henaojara':
        if config.get_setting('channel_henaojara_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'homecine':
        if config.get_setting('channel_homecine_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'jkanime':
        if config.get_setting('channel_jkanime_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'latanime':
        if config.get_setting('channel_latanime_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'masnovelas':
        if config.get_setting('channel_masnovelas_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'megaserie':
        if config.get_setting('channel_megaserie_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'mundodonghua':
        if config.get_setting('channel_mundodonghua_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'peliculaspro':
        if config.get_setting('channel_peliculaspro_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'pelisforte':
        if config.get_setting('channel_pelisforte_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'pelispanda':
        if config.get_setting('channel_pelispanda_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'papayaseries':
        if config.get_setting('channel_papayaseries_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'pelisxd':
        if config.get_setting('channel_pelisxd_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'pelisyseries':
        if config.get_setting('channel_pelisyseries_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'pgratishd':
        if config.get_setting('channel_pgratishd_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'ppeliculas':
        if config.get_setting('channel_ppeliculas_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'pplus':
        if config.get_setting('channel_pplus_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'rojotorrent':
        if config.get_setting('channel_rojotorrent_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'seriespapayato':
        if config.get_setting('channel_seriespapayato_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'seriesretro':
        if config.get_setting('channel_seriesretro_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'srnovelas':
        if config.get_setting('channel_srnovelas_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'subtorrents':
        if config.get_setting('channel_subtorrents_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'yaskeorg':
        if config.get_setting('channel_yaskeorg_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    elif item.notice == 'zonaleros':
        if config.get_setting('channel_zonaleros_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

        txt += '[COLOR greenyellow][B][CR]También ha añadido un control contra robots [COLOR red]reCAPTCHA[/COLOR] oculto.[/COLOR][/B][CR]'

    else:
        if config.get_setting('channel_' + item.notice + '_proxies', default=''):
	        txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

    txt += '[CR][COLOR goldenrod][B]  Desconocemos si será Temporal ó Definitivo.[/B][/COLOR][CR]'

    txt += '[CR][COLOR plum][B]  Ya ocurrió alguna vez en el pasado y al cabo de un cierto tiempo lo retiró.[/B][/COLOR][CR]'

    txt += '[CR][COLOR aquamarine][B]  Por ello, si no os funciona correctamente, pues hay que tener paciencia,'
    txt += '[CR]  e ir probando uno a uno, los [/COLOR][COLOR magenta][B]Proveedores[/B][/COLOR] de proxies[COLOR aquamarine], en [COLOR red][B]Configurar proxies a usar ...[/B][/COLOR][CR]'

    txt += '[CR][COLOR yellowgreen][B]  Ó bien prescindir/desactivar el canal hasta que se estabilize posiblemente en un futuro.[/B][/COLOR]'

    txt += '[CR][CR][COLOR magenta][B]Proveedores Recomendados:[/B][/COLOR][CR]'

    if config.get_setting('proxies_list', default=False):
        txt += '  [COLOR limegreen][B]Lista-proxies.txt[/B][/COLOR][CR]'

    txt += '  [COLOR yellow][B]All-providers[/COLOR][CR]'
    txt += '  [COLOR aquamarine][B]Mertguvencli[/COLOR][CR]'
    txt += '  [COLOR yellow][B]Mmpx12[/COLOR][CR]'
    txt += '  [COLOR yellow][B]Proxyscrape.com[/B][/COLOR][CR]'
    txt += '  [COLOR aquamarine][B]Roosterkid[/COLOR][CR]'
    txt += '  [COLOR aquamarine][B]Shiftytr[/COLOR][CR]'
    txt += '  [COLOR yellow][B]Us-proxy.org[/B][/COLOR][CR]'

    if config.get_setting('proxies_extended', default=False):
        txt += '  [COLOR gold][B]Free-proxy-list.anon[/B][/COLOR] Proveedoores Lista Ampliada[CR]'

    if config.get_setting('proxies_vias', default=False):
        txt += '[COLOR violet][B]  Openproxy,  Github[/B][/COLOR] Proveedores Lista Vias Alternativas'

    platformtools.dialog_textviewer('Información canal ' + item.notice.capitalize(), txt)


def show_help_playdede_media_center(item):
    logger.info()

    txt = '[B][COLOR yellow]Este Canal Habitualmente NO Requiere[/COLOR] [COLOR red]Proxies[/COLOR][/B][CR]'

    if config.get_setting('channel_playdede_proxies', default=''):
	    txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

    txt += '[CR]Si el Canal [COLOR plum][B] NO Obtiene Resultados[/B][/COLOR] y la Ubicación de su Media Center [COLOR violet][B]NO es España[/B][/COLOR]:[CR]'

    txt += '  Necesitará Obligatoriamente [COLOR red][B]Configurar Proxies a usar[/B][/COLOR] en el canal.[CR][CR]'

    txt += '[COLOR darkcyan][B]Aviso del Web Master de este canal [/COLOR][COLOR cyan] (a partir del 31/12/2024)[/COLOR][COLOR darkcyan]:[/B][/COLOR][CR]'

    txt += '  [COLOR gold][B]Debido a la Situación Actual, hemos tenido que tomar Medidas de Seguridad Adicionales.[CR]'

    txt += '  Por esta razón, el Acceso a nuestra Web está Limitado a Países Hispanohablantes.[CR]'

    txt += '  Sugerimos usar una [/COLOR][COLOR yellowgreen]VPN[/COLOR] [COLOR gold]de un País de habla Hispana para acceder a nuestro Contenido.[CR]'

    txt += '  Entendemos que esto pueda causar inconvenientes, pero es necesario[CR]'
    txt += '  si queremos permanecer activos durante más tiempo.[/B][/COLOR][CR][CR]'

    if not config.get_setting('channel_playdede_proxies', default=''):
        txt += '[COLOR turquoise][B]VPN:[/B][/COLOR][CR]'

        txt += '  [B][COLOR darkcyan]El Uso de una [/COLOR][COLOR yellowgreen]VPN[/COLOR][COLOR darkcyan] jamás se saltará el control del Canal por [/COLOR][COLOR red]CloudFlare[/COLOR][COLOR orangered] Protection[/B][/COLOR][CR][CR]'

        txt += '  [B][COLOR yellow]Si puede acceder a través de un Navegador de Internet al Canal[/B][/COLOR][CR]'
        txt += '  y [COLOR plum][B]No obtiene resultados[/B][/COLOR] desde su Media Center[CR][CR]'

        txt += '  [COLOR turquoise][B]Necesitará Instalar en su Equipo una [/B][/COLOR][COLOR yellowgreen][B]VPN[/B][/COLOR][CR]'
        txt += '  para saber donde obtener una [COLOR turquoise][B]VPN[/B][/COLOR] Acceda a la [COLOR chartreuse][B]Ayuda[/B][/COLOR][COLOR fuchsia][B] Cuestiones Preliminares[/B][/COLOR][COLOR goldenrod][B] Miscelánea[/B][/COLOR][CR]'

        txt += '  [CR][B][COLOR darkorange]Atención:[/COLOR][/B][CR]'

        txt += '  Si el acceso al Dominio del Canal, a través de un Navegador de Internet avisase con[CR]'
        txt += '  [COLOR orange][B]Verificando ...[/COLOR] [COLOR orangered]CLOUDFLARE[/B][/COLOR][CR]'
        txt += '  necesitará obligatoriamente usar [COLOR red][B]Proxies[/B][/COLOR] en el canal.[CR][CR]'

    platformtools.dialog_textviewer('Información PlayDede Aviso Ubicación de su Media Center', txt)


def show_help_playdede_bloqueo(item):
    logger.info()

    txt = '[B][COLOR yellow]Este Canal Habitualmente NO Requiere[/COLOR] [COLOR red]Proxies[/COLOR][/B][CR]'

    if config.get_setting('channel_playdede_proxies', default=''):
	    txt += '[CR][B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

    txt += '[CR][COLOR darkcyan][B]Aviso del Web Master de este canal [/COLOR][COLOR cyan] (a partir del 31/1/2025)[/COLOR][COLOR darkcyan]:[/B][/COLOR][CR]'

    txt += '[COLOR gold][B]  Ahora cada vez que suframos un bloqueo,[CR]'
    txt += '  para hacer mas sencillo el proceso,[CR]'
    txt += '  Sólo va a canbiar la parte del link[/B][/COLOR][CR]'

    txt += '[COLOR yellowgreen][B]  www1. [/COLOR][COLOR gold]por[/COLOR][COLOR yellowgreen] www2.[/COLOR][COLOR gold], luego por [/COLOR][COLOR yellowgreen]www3.[/COLOR][COLOR gold] y así sucesivamente.[/COLOR][CR]'

    txt += '[COLOR violet][B]  El resto del link a la web seguirá igual[/B][/COLOR][CR]'

    txt += '[COLOR gold][B]  y solo cambiará el Número despues de[/COLOR][COLOR yellowgreen] www?[/B][/COLOR]'

    txt += '[CR][CR][COLOR cyan][B]Otras Formas de Saltarse el Bloqueo de este canal:[/B][/COLOR][CR]'

    txt += '[COLOR goldenrod][B]  Usando una [/COLOR][COLOR limegreen] VPN [/COLOR][COLOR goldenrod],[CR]'
    txt += '  ó poniendo el Servidor [/COLOR][COLOR limegreen] DNS [/COLOR][COLOR goldenrod] de Google en su dispositivo,[/B][/COLOR][CR]'
    txt += '  Si lo precisa, Busque tutoriales en [COLOR fuchsia][B] YouTube [/COLOR][COLOR goldenrod] para hacerlo.[/B][/COLOR][CR][CR]'

    if not config.get_setting('channel_playdede_proxies', default=''):
        txt += '[COLOR turquoise][B]VPN:[/B][/COLOR][CR]'

        txt += '  [B][COLOR darkcyan]El Uso de una [/COLOR][COLOR yellowgreen]VPN[/COLOR][COLOR darkcyan] jamás se saltará el control del Canal por [/COLOR][COLOR red]CloudFlare[/COLOR][COLOR orangered] Protection[/B][/COLOR][CR][CR]'

        txt += '  [B][COLOR yellow]Si puede acceder a través de un Navegador de Internet al Canal[/B][/COLOR][CR]'
        txt += '  y [COLOR plum][B]No obtiene resultados[/B][/COLOR] desde su Media Center[CR][CR]'

        txt += '  [COLOR turquoise][B]Necesitará Instalar en su Equipo una [/B][/COLOR][COLOR yellowgreen][B]VPN[/B][/COLOR][CR]'
        txt += '  para saber donde obtener una [COLOR turquoise][B]VPN[/B][/COLOR] Acceda a la [COLOR chartreuse][B]Ayuda[/B][/COLOR][COLOR fuchsia][B] Cuestiones Preliminares[/B][/COLOR][COLOR goldenrod][B] Miscelánea[/B][/COLOR][CR]'

        txt += '  [CR][B][COLOR darkorange]Atención:[/COLOR][/B][CR]'

        txt += '  Si el acceso al Dominio del Canal, a través de un Navegador de Internet avisase con[CR]'
        txt += '  [COLOR orange][B]Verificando ...[/COLOR] [COLOR orangered]CLOUDFLARE[/B][/COLOR][CR]'
        txt += '  necesitará obligatoriamente usar [COLOR red][B]Proxies[/B][/COLOR] en el canal.[CR][CR]'

    platformtools.dialog_textviewer('PlayDede Información Bloqueo Operadoras', txt)


def show_help_audios(item):
    logger.info()

    txt = '*) Casi todos los Canales tienen audio en [COLOR cyan][B](Castellano de España)[/B][/COLOR], porque no lo determina el canal habitualmente, sino que lo implementan los [COLOR yellow][B]Uploaders[/B][/COLOR] al subir los vídeos, es en ese punto donde normalmente están los [COLOR gold][B]idiomas que ellos han decidido[/B][/COLOR], y esto NO se conoce con exactitud, hasta el momento de presentar los [COLOR fuchsia][B]Players[/B][/COLOR][CR]'

    txt += '[CR]*) Los Estrenos en [COLOR cyan][B](Castellano de España)[/B][/COLOR] tardan mucho más tiempo en ponerlos los [COLOR yellow][B]Uploaders[/B][/COLOR] en las Webs.'

    txt += '[CR][CR]*) Si necesitase implementar [COLOR lime][B]Subtitulos[/B][/COLOR] en los vìdeos, localize Tutoriales en [COLOR cyan][B]YouTube[/B][/COLOR] al respecto.'

    txt += '[CR][CR]*) Revise sus [COLOR chocolate][B]Ajustes[/B][/COLOR] preferencias (categoría [COLOR fuchsia][B]Play[/B][/COLOR])'

    platformtools.dialog_textviewer('Información Idiomas en los Audios de los Vídeos', txt)


def show_help_gamovideo(item):
    logger.info()

    if not servertools.is_server_available('gamovideo'):
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]El servidor está Inactivo[/B][/COLOR]' % color_avis)
        return

    txt = '*) Consideraciones si [COLOR gold][B]Jamás[/COLOR][/B] reproduce este servidor en ningún Canal.[CR]'

    txt = '*) Si su Media Center opera bajo alguna de las siguientes opciones:[CR]'

    txt += '  - Ejecución de Balandro en [COLOR darkorange][B]Kodi NO oficiales[/B][/COLOR]. (Mods, Forks, Clons,  etc.)[CR]'
    txt += '    ó bajo [COLOR gold]Builds, Wizards ó Widgets[/COLOR] puede fallar la Reproducción de este servidor[CR]'
	
    txt += '[CR]*) Add-Ons de Programas que pueden afectar también al funcionamiento de este Servidor:[CR]'
    txt += '     [COLOR yellowgreen][B]LimpiarKodi,  LimpiaTuKodi,  EzMaintenace,  Indigo  y  similares[/B][/COLOR].[CR]'

    txt += '     Si Alteran el fichero [COLOR gold]AdvancedSettings[/COLOR] con sentencias relativas a la memoria de su Media Center.'

    platformtools.dialog_textviewer('Información servidor Gamovideo', txt)


def show_help_not_programed(item):
    logger.info()

    txt = '*) Balandro NO almacena ningún tipo de contenido.[CR][CR]'

    txt += '*) Son avisos de porqué no se puede reproducir ese enlace en cuestión.[CR]'

    txt += '[CR]*) [COLOR goldenrod][B]Algunos Ejemplos:[/COLOR][/B][CR]'

    txt += '[CR] - Para reproducir ese enlace el servidor exige resolver que no eres un [COLOR red]Boot[/COLOR], para ello'

    txt += '[CR]   presenta un proceso para [COLOR yellow]seleccionar imágenes[/COLOR] (bicicletas, barcos, semáforos, etc.)'

    txt += '[CR][CR] - Son redireccionamientos, que hacen que un Link concreto, efectue accesos a otros enlaces diferentes.'

    txt += '[CR]   Para reproducir ese enlace el servidor exige resolver y esperar Todas esas [COLOR red]Redirecciones[/COLOR], para ello'

    txt += '[CR]   presenta un proceso para [COLOR yellow]seleccionar diferentes Webs[/COLOR] (publicidad, esperas, etc.)'

    txt += '[CR][CR]*) [COLOR yellowgreen][B]Dada su dificultad ese Reproductor No esta programado.[/COLOR][/B]'

    platformtools.dialog_textviewer('Información Sin Enlaces Soportados', txt)


def show_help_mega(item):
    logger.info()

    if not servertools.is_server_available('mega'):
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]El servidor está Inactivo[/B][/COLOR]' % color_avis)
        return

    if not PY3:
        txt = '*) Al ser su Media Center una versión anterior a [COLOR gold][B]19.x[/COLOR][/B] y si opera bajo el sistema operativo [COLOR gold][B]Windows[/COLOR][/B], en determinadas ocasiones, puede fallar la Reproducción.[CR][CR]'

    txt += '*) Para cualquier plataforma de ejecución [COLOR gold][B](Windows, Android, Rasperri, etc.)[/COLOR][/B] deben existir Obligatoriamente los modulos necesarios de [COLOR yellow][B]Cryptografía[/COLOR][/B] ya integrados en su Equipo, si no existieran, puede fallar la Reproducción.'

    platformtools.dialog_textviewer('Información servidor Mega', txt)


def show_help_uptobox(item):
    logger.info()

    if not servertools.is_server_available('uptobox'):
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]El servidor está Inactivo[/B][/COLOR]' % color_avis)
        return

    txt = '*) Determinados servidores obligan a registrarse para permitir su acceso.'

    txt += '[CR][CR] Es importante usar [B][COLOR gold]cuentas secundarias[/COLOR][/B] para registrarse, nunca useis las vuestras personales.'

    txt += '[CR][CR]*) Para ello desde otro equipo debeis acceder a la web en cuestión y registraros (darse de alta)'

    txt += '[CR][CR] Si desconoceis el dominio actual de ese servidor, mediante un Navegador de Internet localizar su [B][COLOR gold]twitter[/COLOR][/B]'

    txt += '[CR][CR] Por ejemplo [B][COLOR gold]Uptobox[/COLOR][/B] twitter oficial'

    txt += '[CR][CR]*) Imprescindible tomar buena nota de vuestro [B][COLOR gold]Usuario y Contraseña[/COLOR][/B] para ese servidor.'

    txt += '[CR][CR]*) Una vez tengáis vuestros datos, se os solicitará al acceder a ese servidor determinado.'

    txt += '[CR][CR]*) Acceder desde otro equipo via Navegador de Internet a [B][COLOR gold]uptobox.com/pin[/COLOR][/B], solo se gestionan las cuentas [B][COLOR yellow]Free[/COLOR][/B]'

    txt += '[CR][CR]*) En el caso de no estar registrados proceder a ello (darse de alta)'

    txt += '[CR][CR] Iniciar la sesión con vuestras credenciales'
    txt += ' e introducir el [B][COLOR gold]PIN[/COLOR][/B] que se os mostró en la ventana al intentar reproducir, para tener vinculada vuestra cuenta.'

    txt += '[CR][CR]*) Mientras mantengáis la [COLOR chartreuse][B]Sesione Abierta[/COLOR][/B] via Navegador de Internet en ese servidor, no tendreis que volver a informar vuestras credenciales.'

    txt += '[CR][CR]*) Hay servidores que limitan el [B][COLOR gold]tiempo máximo de visionado diario[/COLOR][/B] (aprox. 150 minutos).'

    platformtools.dialog_textviewer('Información servidor Uptobox', txt)


def show_help_youtube(item):
    logger.info()

    if not servertools.is_server_available('youtube'):
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]El servidor está Inactivo[/B][/COLOR]' % color_avis)
        return

    if PY3:
        return

    txt = '*) Al ser su Media Center una versión anterior a [COLOR gold][B]19.x[/COLOR][/B][CR][CR]'

    txt += '*) [COLOR yellow][B]No hay solución para este servidor, y tampoco podrá visualizar Traílers[/B][/COLOR]'

    platformtools.dialog_textviewer('Información servidor Youtube', txt)


def show_server_report(item):
    logger.info()

    txt = '*) Algunos Servidores ([B][COLOR cyan]Filelions, Hexupload, Streamwish, Vidhidepro, Vidspeed[/B][/COLOR])[CR]'
    txt += '    En ciertas ocasiones, [B][COLOR yellowgreen]NO Responden correctamente a la Primera Solicitud de Play[/B][/COLOR],[CR]'
    txt += '    [B][COLOR goldenrod]y Hay que Re-Intentarlo de Nuevo[/B][/COLOR], si persistiera el error, deberá Reportarlo.[CR][CR]'

    txt += '*) Estos Reportes debereís informarlos en nuestro [COLOR chartreuse]Grupo de Telegram[/COLOR]' + _telegram

    txt += '[CR][CR]*) [B][COLOR gold]Antes de reportarlo como un posible error, rogamos accedaís a través de un Navegador de Internet, a ese canal en concreto y procedaís a comprobar si esa pelicula/serie/episodio reproduce a través del servidor en cuestión[/COLOR][/B]'

    txt += '[CR][CR]*) [B][COLOR yellow]Si el resultado de esta operativa ha resultado satisfactoria, indicarnos toda esa información para proceder a su verficación/subsanación[/COLOR][/B]'

    txt += '[CR][CR]*) Debeís comprender que este trabajo ha de ser compartido entre vosotros y nosotros, porqué si la carga solo recayera sobre nosotros sería imposible abordarlo por saturación/falta de tiempo'

    txt += '[CR][CR]*) Muchas gracias, por vuestro tiempo y comprensión al respecto'

    platformtools.dialog_textviewer('Como Reportar posible Fallo en la Reproducción de servidores', txt)


def show_help_settings(item):
    logger.info()

    txt = '*) Las opciones para los [COLOR gold]listados de canales[/COLOR] se usan si marcas canales como [COLOR gold][B]Preferidos[/B][/COLOR] ó [COLOR gray][B]Desactivados[/B][/COLOR].'
    txt += ' Esto lo puedes hacer desde el [COLOR yellow][B]Menú Contextual[/B][/COLOR] en los listados de canales.'

    txt += '[CR][CR]*) En [COLOR gold]Búsquedas[/COLOR] el parámetro [COLOR gold][B]Resultados por canal[/B][/COLOR] sirve para limitar el número de coincidencias que se muestran en la pantalla de búsqueda global.'
    txt += ' Es para que no salga un listado demasiado largo ya que algunos canales son más sensibles que otros y pueden devolver bastantes resultados.'
    txt += ' Pero de todas maneras se puede acceder al listado de todos los resultados de cada canal concreto.'
    txt += ' Dispones de más parámetros personalizables en los Ajustes categoría [COLOR yellow][B]Buscar[/B][/COLOR].'

    txt += '[CR][CR]*) En [COLOR gold]Reproducción[/COLOR] se puede activar [COLOR yellow][B]Auto Play[/B][/COLOR] para no tener que seleccionar un servidor para reproducir.'
    txt += ' Si hay algún canal para el que quieras desactivar el autoplay puedes indicarlo en los Ajustes categoría [COLOR fuchsia][B]Play[/B][/COLOR].'

    txt += '[CR][CR]*) En [COLOR gold]Reproducción[/COLOR] los parámetros para ordenar/filtrar los enlaces [COLOR gold][B]por idioma[/B][/COLOR] permiten indicar nuestras preferencias de idiomas.'
    txt += ' Entre Español, Latino y Versión Original elije el orden que prefieres, ó descarta alguno de ellos si no te interesa.'
    txt += ' Todo ello puedes personalizarlo en los Ajustes categoría [COLOR fuchsia][B]Play[/B][/COLOR].'

    txt += '[CR][CR]*) En [COLOR gold]Reproducción[/COLOR] los parámetros para ordenar los enlaces [COLOR gold][B]por calidad[/B][/COLOR] permiten mostrar antes los de más calidad en lugar de mostrarlos según el orden que tienen en la web.'
    txt += ' Algunos canales tienen valores fiables de calidad pero otros no, depende de cada web.'
    txt += ' Todo ello puedes personalizarlo en los Ajustes categoría [COLOR fuchsia][B]Play[/B][/COLOR].'

    txt += '[CR][CR]*) En [COLOR gold]Reproducción[/COLOR] los parámetros para ordenar/filtrar los enlaces [COLOR gold][B]por servidores[/B][/COLOR] permiten hacer algunos ajustes en función de los servidores.'
    txt += ' Si no quieres que te salgan enlaces de ciertos servidores, escríbelos en [COLOR cyan][B]Descartados[/B][/COLOR] (ej: torrent, mega).'
    txt += ' Y si quieres priorizar algunos servidores escríbelos en [COLOR darkorange][B]Preferidos[/B][/COLOR] (ej: torrent, mega), ó al revés en [COLOR gold][B]última opción[/B][/COLOR] (ej: torrent, mega).'
    txt += ' Para modificar estas opciones necesitas saber qué servidores te funcionan mejor y peor, en caso de duda no hace falta que lo modifiques.'
    txt += ' Todo ello puedes personalizarlo en los Ajustes categoría [COLOR fuchsia][B]Play[/B][/COLOR].'

    txt += '[CR][CR]*) Una opción que puede provocar una demora en los tiempos de respuesta es en Ajustes categoría [COLOR gold][B]TMDB[/B][/COLOR] si se activa [COLOR gold][B]buscar información extendida[/B][/COLOR].'
    txt += ' Esto provoca que los listados de películas y series de todos los canales tarden más en mostrarse ya que se hace una segunda llamada a TMDB para intentar recuperar más datos.'

    txt += '[CR][CR]*) En [COLOR gold][B]TMDB[/B][/COLOR] se pueden desactivar las [COLOR gold][B]llamadas a TMDB[/COLOR][/B] en los listados.'
    txt += ' Esto provoca que los listados de películas y series de todos los canales tarden menos en mostrarse pero en la mayoría de casos no tendrán información como la sinopsis y las carátulas serán de baja calidad.'
    txt += ' Puede ser útil desactivarlo temporalmente en casos donde alguna película/serie no se identifica correctamente en TMDB y se quieran ver los datos originales de la web.'

    txt += '[CR][CR]*) Exiten más parámetros en los [COLOR gold]Ajustes[/COLOR] de Balandro, para tener personalizada su ejecución.'
    txt += ' Divididos por categorías [COLOR gold]Menú, Canales, Parental, Dominios, Cuentas, Play, Proxies, Torrents, Buscar, etc.[/COLOR].'

    platformtools.dialog_textviewer('Notas sobre algunos Parámetros de la Ajustes', txt)


def show_help_tips(item):
    logger.info()

    txt = '*) Es importante usar el [B][COLOR yellow]Menú Contextual[/COLOR][/B] para acceder a acciones que se pueden realizar sobre los elementos de los listados.'
    txt += ' Si dispones de un teclado puedes acceder a él pulsando la tecla C, en dispositivos táctiles manteniendo pulsado un elemento, y en mandos de tv-box manteniendo pulsado el botón de selección.'
    txt += ' Si usas un mando de TV es recomendable configurar una de sus teclas con [COLOR gold][B]ContextMenu[/B][/COLOR] (Menú Contextual).'

    txt += '[CR][CR]*) En los listados de los canales puedes usar el [COLOR yellow][B]Menú Contextual[/B][/COLOR] para marcar los canales como [COLOR goldenrod][B]Desactivado/Activo/Preferido[/B][/COLOR].'
    txt += ' De esta manera podrás tener tus [COLOR gold]^Canales Preferidos[/COLOR] al inicio y mover al final los que no te interesen.'
    txt += ' Los canales [COLOR gray][B]Desactivados[/B][/COLOR] son accesibles pero no forman parte de las búsquedas.'

    txt += '[CR][CR]*) Si en algún canal encuentras una película/serie que te interesa pero fallan sus enlaces, accede al [COLOR yellow][B]Menú Contextual[/B][/COLOR] y selecciona'
    txt += ' [COLOR gold]buscar en otros canales[/COLOR] para ver si está disponible en algún otro canal.'

    txt += '[CR][CR]*) Desde cualquier pantalla desplázate hacia el lateral izquierdo para desplegar algunas [COLOR gold]opciones standard de su Media Center[/COLOR].'
    txt += ' Allí tienes siempre un acceso directo a los Ajustes del Add-On y también puedes cambiar el [COLOR yellow][B]Tipo de Vista[/B][/COLOR] que se aplica a los listados.'
    txt += ' Entre Lista, Cartel, Muro de información, Lista amplia, Muro, Fanart, etc. escoge como prefieres ver la información.'

    txt += '[CR][CR]*) Algunos canales de series tienen un listado de [COLOR gold]últimos episodios[/COLOR]. En función de las características de las webs, los enlaces llevan'
    txt += ' a ver el capítulo ó a listar las temporadas de la serie. Cuando es posible, desde el enlace se ve el episodio y desde el [COLOR yellow][B]Menú Contextual[/B][/COLOR]'
    txt += ' se puede acceder a la temporada concreta ó la lista de temporadas.'

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_preferidos', default=True):
            txt += '[CR][CR]*) Para seguir series es recomendable usar la opción [COLOR wheat][B]Preferidos[/B][/COLOR]. Busca la serie que te interese en cualquiera de los canales y desde el [COLOR yellow][B]Menú Contextual[/B][/COLOR] guárdala.'
            txt += ' Luego ves a [COLOR wheat][B]Preferidos[/B][/COLOR] donde podrás gestionar lo necesario para la serie. Además puedes usar [COLOR gold]Buscar en otros canales[/COLOR] y desde el listado de resultados con el'
            txt += ' [COLOR yellow][B]Menú Contextual[/B][/COLOR] también los puedes guardar y se añadirán a los enlaces que ya tenías. De esta manera tendrás alternativas en diferentes enlaces por si algún día falla alguno ó desaparece.'

    platformtools.dialog_textviewer('Trucos y consejos varios', txt)


def show_help_use(item):
    logger.info()

    txt = '[COLOR cyan][B]Modo CASUAL:[/B][/COLOR][CR]'
    txt += 'Accede por ejemplo a Películas ó Series desde el menú principal, entra en alguno de los canales y navega por sus diferentes opciones hasta encontrar una película que te interese.'
    txt += ' Al entrar en la película se mostrará un diálogo con diferentes opciones de vídeos encontrados.'
    txt += ' Prueba con el primero y si el enlace es válido empezará a reproducirse. Sino, prueba con alguno de los otros enlaces disponibles.'
    txt += ' Si ninguno funcionara, desde el enlace de la película accede al [COLOR yellow][B]Menú Contextual[/B][/COLOR] y selecciona [COLOR gold]Buscar en otros canales[/COLOR].'

    txt += '[CR][CR][COLOR cyan][B]Modo DIRECTO:[/B][/COLOR][CR]'
    txt += 'Si quieres ver una película/serie concreta, accede a [COLOR yellow][B]Buscar[/B][/COLOR] desde el menú principal y escribe el título en el buscador.'
    txt += ' Te saldrá una lista con las coincidencias en todos los canales disponibles.'

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_preferidos', default=True):
            txt += '[CR][CR][COLOR cyan][B]Modo PLANIFICADOR (Guardar en Preferidos):[/B][/COLOR][CR]'
            txt += 'Navega por los diferentes canales y ves apuntando las películas/series que te puedan interesar.'
            txt += ' Para ello accede al [COLOR yellow][B]Menú Contextual[/B][/COLOR] desde cualquier Película/Serie/Episodio y selecciona [COLOR gold][B]Guardar en ...[/B][/COLOR].'
            txt += ' Cuando quieras ver una película/serie, accede a [COLOR wheat][B]Preferidos[/B][/COLOR] desde el menú principal donde estará todo lo guardado.'

            txt += '[CR][CR][COLOR cyan][B]Modo COLECCIONISTA (Menú Preferidos):[/B][/COLOR][CR]'
            txt += 'Desde [COLOR wheat][B]Preferidos[/B][/COLOR] accede a [COLOR gold][B]Gestionar listas[/B][/COLOR], donde puedes crear diferentes listas para organizarte las películas y series que te interesen.'
            txt += ' Por ejemplo puedes tener listas para distintos usuarios de Balandro (Padres, Esposa, Hijos, etc.) ó de diferentes temáticas, ó para guardar lo que ya hayas visto, ó para pasar tus recomendaciones a algún amigo, etc.'

        if config.get_setting('mnu_desargas', default=True):
            txt += '[CR][CR][COLOR cyan][B]Modo ASEGURADOR (Descargas):[/B][/COLOR][CR]'
            txt += 'Descarga algunos [COLOR gold]Vídeos[/COLOR] para tener listas para ver sin depender de la saturación de la red/servidores en momentos puntuales.'
            txt += ' Desde cualquier película/episodio, tanto en los [COLOR gold][B]Canales[/B][/COLOR] como en [COLOR wheat][B]Preferidos[/B][/COLOR], accede al [COLOR yellow][B]Menú Contextual[/B][/COLOR] y selecciona [COLOR gold][B]Descargar vídeo[/B][/COLOR].'
            txt += ' Selecciona alguno de los enlaces igual que cuando se quiere reproducir y empezará la descarga.'
            txt += ' Para ver lo descargado, accede a [COLOR seagreen][B]Descargas[/B][/COLOR] desde el menú principal.'

    platformtools.dialog_textviewer('Ejemplos de uso de Balandro', txt)


def show_help_faq(item):
    logger.info()

    txt = '[COLOR gold][B]¿ De dónde viene Balandro ?[/B][/COLOR][CR]'
    txt += 'Balandro es desde el año [COLOR cyan][B]2018[/B][/COLOR] un Add-On derivado de [COLOR gold]Pelisalacarta y Alfa[/COLOR], optimizado a nivel interno de código y a nivel funcional para el usuario.'
    txt += ' Puede ser útil en dispositivos poco potentes como las [COLOR yellow][B]Raspberry Pi[/B][/COLOR] u otros [COLOR yellow][B]TvBox[/B][/COLOR] y para usuarios que no quieran complicaciones.'
    txt += ' Al ser un Add-On de tipo Navegador, tiene el nombre de un velero ya que Balandro era una embarcación ligera y maniobrable, muy apreciada por los piratas.'

    txt += '[CR][CR][COLOR gold][B]¿ Qué características tiene Balandro ?[/B][/COLOR][CR]'
    txt += 'Principalmente permite acceder a los contenidos de webs con vídeos de películas y series para reproducirlos y/ó guardarlos, y'

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_preferidos', default=True):
            txt += ' dispone de unos [COLOR wheat][B]Preferidos[/B][/COLOR] propios donde poder apuntar todas las Películas y Series que interesen al usuario.'
 
    txt += ' Se pueden configurar múltiples opciones, por ejemplo la preferencia de idioma, la reproducción automática, los colores para los listados, los servidores preferidos, excluir canales en las búsquedas, etc.'

    txt += '[CR][CR][COLOR gold][B]¿ Almacena Balandro algún tipo de contenido?[/B][/COLOR][CR]'
    txt += 'NO, este Add-On es tan solo un mero Ejercicio de Aprendizaje del Lenguaje de Programación Python y se distribuye sin Ningún Contenido Multimedia adjunto al mismo.'
    txt += '[COLOR red][B][I] En consecuencia solo Las Webs son plenamente Responsables de los Contenidos que Publiquen [/I][/B][/COLOR].'

    txt += '[CR][CR][COLOR gold][B]¿ Qué particularidades tienen los Canales [/COLOR][COLOR darkgoldenrod]Problemáticos[/COLOR][COLOR gold] ?[/B][/COLOR][CR]'
    txt += 'Son aquellos canales en los que Predominan Referencias/Elementos Sin enlaces Disponibles, enlaces Inválidos y/ó enlaces a servidores No Soportados.'

    txt += '[CR][CR][COLOR gold][B]¿ Cómo funciona el [/COLOR][COLOR fuchsia]Autoplay[/COLOR][COLOR gold] ?[/B][/COLOR][CR]'
    txt += 'Se puede activar la función de reproducción automática desde los Ajustes  (categoría Play).'
    txt += ' Si se activa, al ver una película ó episodio se intenta reproducir el primero de los enlaces que funcione, sin mostrarse el diálogo de selección de servidor.'
    txt += ' Los enlaces se intentan secuencialmente en el mismo orden que se vería en el diálogo, por lo que es importante haber establecido las preferencias de idioma, servidores y calidades.'

    txt += '[CR][CR][COLOR gold][B]¿ En qué orden se muestran los enlaces de servidores ?[/B][/COLOR][CR]'
    txt += 'El orden inicial es por la fecha de los enlaces, para tener al principio los últimos actualizados ya que es más probable que sigan vigentes, aunque en los canales que no lo informan es según el orden que devuelve la web.'
    txt += ' Desde los Ajustes se puede activar el ordenar por calidades, pero su utilidad va a depender de lo que muestre cada canal y la fiabilidad que tenga.'
    txt += ' A partir de aquí, si hay preferencias de servidores en los Ajustes, se cambia el orden para mostrar al principio los servidores preferentes y al final los de última opción.'
    txt += ' Y finalmente se agrupan en función de las preferencias de idiomas del usuario.'

    txt += '[CR][CR][COLOR gold][B]¿ Funcionan los enlaces [/COLOR][COLOR blue]Torrent[/COLOR][COLOR gold] ?[/B][/COLOR][CR]'
    txt += 'El Add-On está preparado para tratarlos usando un Motor/Cliente de torrents externo, tipo [COLOR gold]Elementum, etc.[/COLOR]'
    txt += ' Estos Motores/Clientes externos (Add-Ons) torrents no están incluidos en Balandro y deben Instalarse por separado.'
    txt += ' Además, debe indicarse Obligatoriamente en los Ajustes de Balandro cual va a ser su Motor/Cliente habitual de torrents.'

    txt += '[CR][CR]Si algún otro Add-On tiene activado [COLOR gold]Borrar caché de kodi en el inicio[/COLOR], se elimina una carpeta temporal que [COLOR gold]Elementum[/COLOR] necesita'
    txt += ' [COLOR gold].../.kodi/temp/elementum/[/COLOR], en consecuencia puede fallar la descarga/reproducción del torrent.'
    txt += ' Cuando a [COLOR gold]Elementum[/COLOR] se le pasa un enlace .torrent lo intenta descargar en esa carpeta, pero no podrá hacerlo si esta carpeta se ha eliminado.'
    txt += ' Si esto sucede, en el Log de su Media Center se observa el mensaje [COLOR gold]Error adding torrent: &os.PathError[/COLOR].'
    txt += ' Este error no se produce si el enlace es de tipo [COLOR gold]magnet:?[/COLOR], por lo tanto, pueden haber enlaces que funcionen y otros que No.'

    txt += '[CR][CR][COLOR blue][B]Este problema se resuelve:[/B][/COLOR]'
    txt += '[CR]Si se accede a los Ajustes de [COLOR gold]Elementum[/COLOR] y se guarda nuevamente, se regenera su carpeta de caché y funcionará correctamente la descarga/reproducción del torrent.'
    txt += ' Pero si se mantiene activado el borrado por ejemplo en Indigo, al reiniciar su Media Center Kodi dejará de funcionar de nuevo.'

    txt += '[CR][CR][COLOR gold][B]¿ Porqué la opción [/COLOR][COLOR yellow]Buscar[/COLOR][COLOR gold] entra em modo bucle (vuelve a solicitar el texto a localizar) ?[/B][/COLOR][CR]'
    txt += 'Add-Ons de Programas que pueden afectar al funcionamiento de Balandro:[CR]' 
    txt += '  [COLOR yellowgreen][B]LimpiarKodi,  LimpiaTuKodi,  EzMaintenace,  Indigo  y  similares.[B][/COLOR]'

    txt += '[CR][CR]Cuando desde estos Add-Ons se ejecuta la función [COLOR gold]Limpiar Cache y Rom[/COLOR],'
    txt += ' se elimina la carpeta interna de la caché de su Media Center Kodi [COLOR gold].../.kodi/temp/archive_cache/[/COLOR]'
    txt += ' y ello provoca que este no pueda cachear. Al no poder usar esta caché, puede influir en el rendimiento en general de todos los Add-Ons,'
    txt += ' pero donde resulta una molestia dentro de Balandro (y demás Add-Ons) es al buscar, ya que después de hacer una búsqueda y entrar en alguno de los resultados,'
    txt += ' al volver atrás, vuelve a solicitar de nuevo la introducción de texto, cuando debería volver a mostrar la lista de resultados previa.'

    txt += '[CR][CR][COLOR yellow][B]Este problema se resuelve:[/B][/COLOR]'
    txt += '[CR]Re-iniciando su Media center Kodi, ya que Kodi vuelve a generar la carpeta de caché al iniciarse.'
    txt += ' Cualquier Add-On que en lugar de eliminar el contenido del caché para limpiar, elimine la propia carpeta provocará este mismo efecto.'

    txt += '[CR][CR][COLOR gold][B]¿ Como evitar la Ventana [/COLOR][COLOR chartreuse]Lista de Reproduccion Abortada[/COLOR][COLOR gold] aunque el enlace NO reproduzca ?[/B][/COLOR][CR]'
    txt += 'Es necesario incorporar en su Media Center, las instrucciones que a continuación se detallan en el archivo [COLOR gold]advancedsettings.xml[/COLOR], si no existiera dicho fichero deberá crear uno Nuevo con ese Contenido.'
    txt += ' la ruta donde debe estar ubicado este arhivo es [COLOR gold].../.kodi/userdata/[/COLOR]'

    txt += '[CR][CR][COLOR chartreuse][B]Este problema se resuelve:[/B][/COLOR] Con las siguientes Instrucciones[CR]'

    if PY3: txt += ' - [COLOR darkorange][B]Pueden NO funcionar correctamente en su Media Center[/B][/COLOR][CR]'

    txt += '[CR]<!-- Balandro -->[CR]'
    txt += '[COLOR darkorange][B]<advancedsettings  version="1.0">[/B][/COLOR][CR]'
    txt += '[COLOR darkorange][B]   <playlistretries>-1</playlistretries>[/B][/COLOR][CR]'
    txt += '[COLOR darkorange][B]   <playlisttimeout>-1</playlisttimeout>[/B][/COLOR][CR]'
    txt += '[COLOR darkorange][B]</advancedsettings>[/B][/COLOR]'

    platformtools.dialog_textviewer('Preguntas Frecuentes', txt)


def show_help_notice(item):
    logger.info()

    txt = '[COLOR gold][B]COMUNICADO BALANDRO 9/5/2022 20:00[/B][/COLOR]'

    txt += '[CR][CR][COLOR yellow][B][I]Son ya más de 7 años desde la aparición pública de nuestro Add-On[/COLOR][COLOR cyan] (2018)[/I][/B][/COLOR]'

    txt += '[CR][CR]Desde [COLOR gold]Enero/2021[/COLOR] hemos solicitado incorporaciones al desarrollo del Add-On [COLOR gold](equipo Balandro Team)[/COLOR] por distintas vías, y todos nuestros intentos han sido infructuosos hasta el momento[CR]'

    txt += '[CR][COLOR darkorange]Motivos:[/COLOR][CR]'
    txt += ' - Desconocen la Programación[CR]'
    txt += ' - Desconocen el lenguaje Python[CR]'
    txt += ' - No disponen de Tiempo para ello[CR]'
    txt += ' - No están Interesados[CR]'
    txt += ' - Solo se comprometen a intervenciones Puntuales[CR]'

    txt += '[CR][COLOR darkorange]Situación:[/COLOR][CR]'
    txt += '  [COLOR chartreuse][B]El Add-On se seguirá manteniendo[/B][/COLOR], pero nos va a ser del todo imposible, acomenter el mantenimiento del mismo como ha sido hasta ahora, a no ser que realmente vengan [COLOR gold]Nuevas Incorporaciones a Balandro Team[/COLOR] con un compromiso y complicidad total[CR]'

    txt += '[CR]  El principal miembro de [COLOR gold]Balandro Team[/COLOR] y responsable del mantenimiento, ya ha superado una edad sexagenaria, y se agotó de este cometido[CR]'

    txt += '[CR]  Tan solo vamos a efectuar los [COLOR chartreuse][B]Mínimos cambios en Canales y Servidores[/B][/COLOR], que no sufran una alteración radical de estructura, y no abordaremos [COLOR gold]Jamás[/COLOR], ni [COLOR chartreuse][B]Nuevos Canales/Servidores[/B][/COLOR], ni [COLOR chartreuse][B]Mejoras[/B][/COLOR], reservandonos el derecho incluso de [COLOR chartreuse][B]Desactivar[/B][/COLOR] lo que nos de un quebradero de cabeza[CR]'

    txt += '[CR][COLOR darkorange]Conclusión:[/COLOR][CR]'
    txt += '  Somos conscientes, que con el paso del tiempo, el Add-On sufra una degradación y deje de cumplir vuestras expectativas sobre el, pero también debeís tener presente, que nosotros así mismo tenemos nuestras vidas y existe más vida fuera del Media Center Kodi[CR]'

    txt += '[CR]Saludos, Balandro Team'

    platformtools.dialog_textviewer('Comunicado Oficial de Balandro', txt)


def show_not_contemplated(item):
    logger.info()

    txt ='[COLOR red][B]¿ Qué temas no están Implementados y/ó Garantizados dentro de Balandro ?[/B][/COLOR][CR]'

    txt += '[CR] - [COLOR pink][B]Media Centers[/COLOR] [COLOR yellow][B]No se puede Garantizar resultados satisfactorios:[/B][/COLOR][CR]'
    txt += '    - Si opera con versiones de Media Center [COLOR darkorange][B]Kodi [/COLOR][COLOR yellowgreen]NO Oficiales[/B][/COLOR]. ([COLOR yellow][B]Mods, Forks, Clons,  etc.[/B][/COLOR])[CR]'
    txt += '    - Si usa Versiones anteriores a [COLOR darkorange][B]Kodi 17.x[/B][/COLOR] en su Media Center.[CR]'

    txt += '    - Ejecución en Media Centers que vengan Pre-instalados en su equipo tipos:[CR]'
    txt += '      [COLOR gold][B]KdPlayer, KkPlayer ó similares[/B][/COLOR][CR]'

    txt += '    - Ejecución de Balandro bajo [COLOR goldenrod][B]Builds, Wizards ó Widgets[/B][/COLOR] en su Media Center.[CR]'

    txt += '[CR] - [COLOR limegreen][B]Add-Ons Externos[/COLOR] de [COLOR yellow][B]Programas[/B][/COLOR] que pueden afectar al funcionamiento de Balandro:[CR]'
    txt += '     [COLOR yellowgreen][B]LimpiarKodi,  LimpiaTuKodi,  EzMaintenace,  Indigo  y  similares[/B][/COLOR].[CR]'

    txt += '     Si Alteran el fichero [COLOR gold]AdvancedSettings[/COLOR] con sentencias relativas a la memoria de su Media Center.[CR]'

    txt += '[CR] - [COLOR limegreen][B]Otros Add-Ons Externos[/COLOR] [COLOR yellow][B]No Contemplados:[/B][/COLOR][CR]'
    txt += '    - Motores [COLOR blue][B]Torrent[/B][/COLOR] [COLOR gold][B]Horus / AceStream[/B][/COLOR][CR]'
    txt += '    - Integración con [COLOR gold][B]AddToLib, Trakt.Tv, Simkl, ó similares[/B][/COLOR] seguimiento de Películas y/ó Series[CR]'

    txt += '[CR] - [COLOR pink][B]Sistema[/COLOR] [COLOR yellow][B]Integraciones y Sincronizaciones:[/B][/COLOR][CR]'
    txt += '    - Fichero [COLOR gold]AdvancedSettings[/COLOR] con sentencias relativas a la [COLOR darkcyan]Memoria ó Buffers[/COLOR] de su Media Center.[CR]'
    txt += '    - Integración con la [COLOR goldenrod][B]Videoteca[/B][/COLOR] de su Media Center[CR]'
    txt += '    - Sincronización entre sus Equipos de sus [COLOR chocolate][B]Ajustes[/B][/COLOR] y [COLOR wheat][B]Preferidos[/B][/COLOR][CR]'

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_desargas', default=True):
            txt += '[CR][COLOR seagreen][B] - Descargas:[/B][/COLOR][CR]'
            txt += '   - Descargar [COLOR gold][B]Todos[/B][/COLOR] los Capítulos de una Temporada alunísono[CR]'
            txt += '   - NO se admiten las descargas de ficheros en formatos [COLOR gold][B]m3u8,  mpd,  rtmp,  torrent[/B][/COLOR][CR]'
            txt += '   - NO están permitidas las descargas de ficheros en formato Comprimido [COLOR goldenrod][B]zip,  rar,  etc.[/B][/COLOR][CR]'
            txt += '   - NO se pueden descargar los Vídeos de [COLOR fuchsia][B]YouTube[/B][/COLOR][CR]'

    txt += '[CR] - [COLOR fuchsia][B]Play[/COLOR] [COLOR yellow]Servidores:[/B][/COLOR][CR]'
    txt += '    - Cuentas Premium en el servidor [COLOR darkorange][B]Uptobox[/B][/COLOR][CR]'
    txt += '    - Integración con [COLOR powderblue][B]Cuentas[/B][/COLOR] [COLOR gold][B]Alldebrid, Realdebrid, ó similares[/B][/COLOR][CR]'
    txt += '    - Algunos Servidores que dada su complejidad para efectuar [COLOR orchid][B]Play[/COLOR] [COLOR gold]No están Soportados[/B][/COLOR][CR]'
    txt += '    - [COLOR orchid][B]Play[/COLOR] archivos con [COLOR red]Contraseña[/B][/COLOR][CR]'

    txt += '[CR] - [COLOR gold][B]Canales[/COLOR] [COLOR yellow]Listas y Otros:[/B][/COLOR][CR]'
    txt += '   - Acceder a [COLOR gold][B]Una Página Concreta[/B][/COLOR] en los listados de las opciones de los canales[CR]'
    txt += '   - Incluir el [COLOR goldenrod][B]Rating[/B][/COLOR] en los listados de las opciones de los canales[CR]'
    txt += '   - Gestión Integral del [COLOR teal][B]Menú Usuario[/B][/COLOR] en los Canales que tengan esa Opción'

    platformtools.dialog_textviewer('¿ Qué NO está contemplado/garantizado en Balandro ?', txt)


def show_not_play(item):
    logger.info()

    txt ='[COLOR red][B]¿ Qué temas no están Implementados en Balandro ?[/B][/COLOR][CR]'

    txt += '[CR][COLOR gold][B] - Servidores:[/B][/COLOR][CR]'
    txt += '    - Cuentas Premium en el servidor [COLOR darkorange][B]Uptobox[/B][/COLOR][CR]'
    txt += '    - Integración con [COLOR powderblue][B]Cuentas[/B][/COLOR] [COLOR gold][B]Alldebrid, Realdebrid, ó similares[/B][/COLOR][CR]'
    txt += '    - Algunos Servidores que dada su complejidad para efectuar [COLOR orchid][B]Play[/B][/COLOR] [COLOR gold]No están Soportados[/COLOR]'

    platformtools.dialog_textviewer('¿ Qué NO está contemplado en Balandro ?', txt)


def show_not_download(item):
    logger.info()

    txt ='[COLOR red][B]¿ Qué temas no están Implementados en las Descargas ?[/B][/COLOR][CR][CR]'

    txt += ' - Descargar [COLOR gold]Todos[/COLOR] los Capítulos de una Temporada alunísono[CR]'
    txt += ' - NO se admiten las descargas de ficheros en formatos [COLOR gold]m3u8,  mpd,  rtmp,  torrent[/COLOR][CR]'
    txt += ' - NO están permitidas las descargas de ficheros en formato Comprimido [COLOR gold]zip,  rar,  etc.[/COLOR]'

    platformtools.dialog_textviewer('¿ Qué NO está contemplado en las Descargas ?', txt)


def show_preferidos_parameters(item):
    logger.info()

    txt = '[COLOR goldenrod][B]AJUSTES PREFERIDOS:[/B][/COLOR][CR]'

    txt += ' - [COLOR cyan]Nuevos Episodios: Valores para Ejecutar el Servicio (Intervalo de horas, por defecto 12): [/COLOR][COLOR red][B]' + str(config.get_setting('addon_tracking_interval', default=12)) + '[/B][/COLOR][CR]'

    tracking_order_movies = config.get_setting('tracking_order_movies', default=0)

    if tracking_order_movies == 0: order_movies = 'Actualización'
    elif tracking_order_movies == 1: order_movies = 'Título'
    else: order_movies = 'Fecha de Estreno'

    txt += '[CR] - [COLOR cyan]Ordenar Películas por (por defecto Actualización): [/COLOR][COLOR red][B]' + order_movies + '[/B][/COLOR][CR]'

    txt += ' - [COLOR cyan]Lista de Películas: Cuantas Películas por página (por defecto 10): [/COLOR][COLOR red][B]' + str(config.get_setting('tracking_perpage_movies', default=10)) + '[/B][/COLOR][CR]'

    tracking_order_tvshows = config.get_setting('tracking_order_tvshows', default=0)

    if tracking_order_tvshows == 0: order_tvshows = 'Actualización'
    elif tracking_order_tvshows == 1: order_tvshows = 'Título'
    else: order_tvshows = 'Fecha de Estreno'

    txt += '[CR] - [COLOR cyan]Ordenar Series por (por defecto Actualización): [/COLOR][COLOR red][B]' + order_tvshows + '[/B][/COLOR][CR]'

    txt += ' - [COLOR cyan]Lista de Series: Cuantas Series por página (por defecto 10): [/COLOR][COLOR red][B]' + str(config.get_setting('tracking_perpage_tvshows', default=10)) + '[/B][/COLOR][CR]'

    tracking_order_episodes = config.get_setting('tracking_order_episodes', default=0)

    if tracking_order_episodes == 0: order_episodes = 'Actualización'
    else: order_episodes = 'Fecha de Emisión'

    txt += '[CR] - [COLOR cyan]Ordenar Series por (por defecto Fecha de Emisión): [/COLOR][COLOR red][B]' + order_episodes + '[/B][/COLOR][CR]'

    txt += ' - [COLOR cyan]Lista de Episodios: Cuantos Episodios por página (por defecto Fecha de Emisión): [/COLOR][COLOR red][B]' + str(config.get_setting('tracking_perpage_episodes', default=10)) + '[/B][/COLOR]'

    platformtools.dialog_textviewer('Información Ajustes Preferidos', txt)


def show_help_tracking(item):
    logger.info()

    txt = '[COLOR gold]¿ Cómo se guardan las películas ó series ?[/COLOR][CR]'
    txt += 'Desde cualquiera de los canales donde se listen películas ó series, accede al [COLOR yellow][B]Menú Contextual[/B][/COLOR] y selecciona [COLOR gold]Guardar película/serie[/COLOR].'
    txt += ' En el caso de películas es casi instantáneo, y para series puede demorarse unos segundos si tiene muchas temporadas/episodios.'
    txt += ' Para ver y gestionar todo lo que tengas, accede a [COLOR wheat]Preferidos[/COLOR] desde el menú principal del Add-On.'
    txt += ' También puedes guardar una temporada ó episodios concretos.'

    txt += '[CR][CR][COLOR gold]¿ Qué pasa si una película/serie no está correctamente identificada ?[/COLOR][CR]'
    txt += 'Esto puede suceder cuando la película/serie no está bien escrita en la web de la que procede ó si hay varias películas con el mismo título.'
    txt += ' Si no se detecta te saldrá un diálogo para seleccionar entre varias opciones ó para cambiar el texto de búsqueda.'
    txt += ' Desde las opciones de Ajustes puedes activar que se muestre siempre el diálogo de confirmación, para evitar que se detecte incorrectamente.'

    txt += '[CR][CR][COLOR gold]¿ Y si no se puede identificar la película/serie ?[/COLOR][CR]'
    txt += 'Es necesario poder identificar cualquier película/serie en TMDB, sino no se puede guardar.'
    txt += ' Si no existe en [COLOR gold]themoviedb.org[/COLOR] ó tiene datos incompletos puedes completar allí la información ya que es un proyecto comunitario y agradecerán tu aportación.'

    txt += '[CR][CR][COLOR gold]¿ Se puede guardar la misma película/serie desde canales diferentes ?[/COLOR][CR]'
    txt += 'Sí, al guardar se apuntan en la base de datos interna los datos propios de la película, serie, temporada ó episodio, y también el enlace al canal de donde se ha guardado.'
    txt += ' De esta manera puedes tener diferentes alternativas por si algún canal fallara ó no tuviera enlaces válidos.'
    txt += ' Si tienes enlaces de varios canales, al reproducir podrás escoger en cual intentarlo.'

    txt += '[CR][CR][COLOR gold]¿ Se guardan las marcas de películas/episodios ya vistos ?[/COLOR][CR]'
    txt += 'Sí, su Media Center gestiona automáticamente las marcas de visto/no visto.'
    txt += ' Estas marcas están en la base de datos de su Media Center pero no en las propias de Balandro.'

    txt += '[CR][CR][COLOR gold]¿ Qué pasa si un enlace guardado deja de funcionar ?[/COLOR][CR]'
    txt += 'A veces las webs desaparecen ó cambian de estructura y/ó de enlaces, y eso provoca que en [COLOR wheat]Preferidos[/COLOR] dejen de ser válidos.'
    txt += ' Al acceder a un enlace que da error, se muestra un diálogo para escoger si se quiere [COLOR gold]Buscar en otros canales[/COLOR] ó [COLOR gold]Volver a buscar en el mismo canal[/COLOR].'
    txt += ' Si la web ha dejado de funcionar deberás buscar en otros canales, pero si ha sufrido cambios puedes volver a buscar en ella.'

    txt += '[CR][CR][COLOR gold]¿ Se puede compartir una lista de Preferidos ?[/COLOR][CR]'
    txt += 'De momento puedes hacerlo manualmente. En la carpeta userdata del Add-On, dentro de [COLOR gold]tracking_dbs[/COLOR] están los ficheros [COLOR gold].sqlite[/COLOR] de cada lista que tengas creada.'
    txt += ' Puedes copiar estos ficheros y llevarlos a otros dispositivos.'

    txt += '[CR][CR][COLOR gold]¿ Cómo invertir el orden de los episodios ?[/COLOR][CR]'
    txt += 'Por defecto los episodios dentro de una temporada se muestran en orden ascendente, del primero al último.'
    txt += ' Si prefieres que sea al revés, desde el [COLOR yellow][B]Menú Contextual[/B][/COLOR] de una temporada selecciona [COLOR gold]Invertir el orden de los episodios[/COLOR] y'
    txt += ' tu preferencia quedará guardada para esa temporada.'

    txt += '[CR][CR][COLOR gold]¿ Hay alguna límitación en los episodios a guardar por cada temporada ?[/COLOR][CR]'
    txt += 'Si, no se almacenarán más de [COLOR red]50 episodios por temporada [/COLOR], si fuera necesario, debe gestionar esa serie y/ó temporada'
    txt += ' a través de los [COLOR gold]favoritos/videoteca genérica[/COLOR] de su Media Center.'

    txt += '[CR][CR][COLOR gold]¿ Cómo integrar los Preferidos en la Videoteca de su Media Center? ?[/COLOR][CR]'
    txt += 'Una alternativa es añadir los [COLOR wheat]Preferidos[/COLOR] de Balandro a los [COLOR gold]favoritos/videoteca genérica[/COLOR] de su Media center.'
    txt += ' ó bien, añadir el contenido de [COLOR wheat]Preferidos[/COLOR] de Balandro a la [COLOR gold]Videoteca genérica[/COLOR] de su Media center, con el Add-On externo [COLOR gold]ADD TO LIB[/COLOR]'

    platformtools.dialog_textviewer('Preferidos y su Funcionamiento', txt)


def show_help_tracking_update(item):
    logger.info()

    txt = '[COLOR gold]¿ Qué es el servicio de búsqueda de nuevos episodios ?[/COLOR][CR]'
    txt += 'El servicio es un proceso de Balandro que se ejecuta al iniciarse su Media Center, y se encarga de comprobar cuando hay que buscar actualizaciones.'
    txt += ' En los Ajustes (categoría [COLOR gold]Actualizar[/COLOR]) puedes indicar cada cuanto tiempo deben hacerse las comprobaciones.'
    txt += ' Por defecto es dos veces al día, cada 12 horas, pero puedes cambiarlo.'
    txt += ' Si lo tienes desactivado, puedes ejecutar manualmente la misma búsqueda desde el [COLOR yellow][B]Menú Contextual[/B][/COLOR] de [COLOR gold]Series[/COLOR] dentro de [COLOR wheat]Preferidos[/COLOR].'

    txt += '[CR][CR][COLOR gold]¿ Cómo se activa la búsqueda de nuevos episodios para series ?[/COLOR][CR]'
    txt += 'Desde el listado de series dentro de [COLOR wheat]Preferidos[/COLOR] accede a [COLOR gold]Gestionar serie[/COLOR] desde el [COLOR yellow][B]Menú Contextual[/B][/COLOR].'
    txt += ' Al seleccionar [COLOR gold]Programar búsqueda automática de nuevos episodios[/COLOR] podrás definir el seguimiento que quieres darle a la serie'
    txt += ' e indicar cada cuanto tiempo hay que hacer la comprobación de si hay nuevos episodios.'

    txt += '[CR][CR][COLOR gold]¿ Cómo se combina el servicio con las series ?[/COLOR][CR]'
    txt += 'Cada vez que se ejecuta el servicio (1, 2, 3 ó 4 veces por día) se buscan las series que tienen activada la búsqueda automática.'
    txt += ' Por cada serie según su propia periodicidad se ejecuta ó no la búsqueda.'
    txt += ' Esto permite por ejemplo tener series que sólo requieren una actualización por semana, y otras donde conviene comprobar cada día.'

    txt += '[CR][CR][COLOR gold]¿ Porqué la búsqueda de nuevos episodios está desactivada por defecto ?[/COLOR][CR]'
    txt += 'Es preferible ser prudente con las actualizaciones para no saturar más las webs de donde se obtiene la información.'
    txt += ' Por esta razón al guardar series por defecto no tienen activada la comprobación de nuevos episodios y hay que indicarlo explícitamente si se quiere.'
    txt += ' Si por ejemplo sigues una serie ya terminada seguramente no necesitarás buscar nuevos episodios, en cambio si sigues una serie de un show diario sí te interesará.'

    txt += '[CR][CR][COLOR gold]¿ Dónde se ven los nuevos episodios encontrados ?[/COLOR][CR]'
    txt += 'En [COLOR wheat]Preferidos[/COLOR] estarán dentro de sus series respectivas, pero también se puede ver un listado de los últimos episodios añadidos'
    txt += ' por fecha de emisión ó de actualización en los canales.'

    platformtools.dialog_textviewer('Búsqueda automática de nuevos episodios', txt)


def show_help_descargas(item):
    logger.info()

    txt = '[CR][COLOR cyan][B]Uso[/B][/COLOR] [COLOR seagreen][B]Descargas:[/B][/COLOR][CR][CR]'

    txt += 'Descargar algunas vídeos para verlos sin depender de la saturación de la red/servidores en momentos puntuales.'
    txt += ' Desde cualquier película/episodio, tanto en los [COLOR gold][B]Canales[/B][/COLOR] como en [COLOR wheat][B]Preferidos[/B][/COLOR], accede al [COLOR yellow][B]Menú Contextual[/B][/COLOR] y [COLOR gold]Descargar vídeo[/COLOR].'
    txt += ' Selecciona alguno de los enlaces igual que cuando se quiere reproducir y empezará la descarga.'
    txt += ' Para ver lo descargado, accede a [COLOR seagreen][B]Descargas[/B][/COLOR] desde el menú principal.'

    txt += '[CR][CR][COLOR cyan][B]Restricciones[/B][/COLOR] en las [COLOR seagreen][B]Descargas:[/B][/COLOR][CR][CR]'

    txt += ' - Descargar [COLOR gold]Todos[/COLOR] los Capítulos de una Temporada alunísono[CR]'
    txt += ' - NO se admiten las descargas de ficheros en formatos [COLOR gold]m3u8,  mpd,  rtmp,  torrent[/COLOR][CR]'
    txt += ' - NO están permitidas las descargas de ficheros en formato Comprimido [COLOR gold]zip,  rar,  etc.[/COLOR]'

    platformtools.dialog_textviewer('Descargas y su Funcionamiento', txt)


def show_help_usb(item):
    logger.info()

    txt = '[COLOR cyan][B]SI[/B][/COLOR] se puede descargar directamente a una [COLOR goldenrod][B]Unidad USB[/B][/COLOR][CR]'
    txt += 'Para ello deberá indicarlo en los Ajustes (categoría [COLOR seagreen][B]Descargas[/B][/COLOR]) apartado Ubicación'

    txt += '[CR][CR][B][COLOR chartreuse]Si observase lentitud, parones, ó cualquier otra anomalía durante la [COLOR seagreen][B]Descarga[/B][/COLOR][COLOR chartreuse][B]:[/COLOR][/B][/COLOR][CR]'
    txt += '  Le [COLOR yellow]sugerimos[/COLOR] que efectue la [COLOR seagreen][B]descarga[/B][/COLOR] en la [COLOR gold][B]carpeta por defecto de los Ajustes[B][/COLOR][CR]'
    txt += '  y una vez finalizada, [COLOR cyan][B]Obtenga una Copia[/B][/COLOR] de esa [COLOR seagreen][B]descarga[/B][/COLOR] hacia la [COLOR goldenrod][B]Unidad USB[/B][/COLOR][CR]'
    txt += '  desde la opción del menú [COLOR seagreen][B]Descargas[/B][/COLOR] al seleccionar cualquier fichero existente en [COLOR seagreen][B]Descargas[/B][/COLOR].[CR]'

    txt += '[CR]También puede [COLOR cyan][B]Obtener una Copia[/B][/COLOR] de su [COLOR seagreen][B]descarga[/B][/COLOR] hacia una [COLOR goldenrod][B]Unidad USB[/B][/COLOR][CR]'
    txt += 'seleccionando cualquier fichero existente en sus [COLOR seagreen][B]Descargas[/B][/COLOR].'

    platformtools.dialog_textviewer('¿ Se puede Descargar directamente en una Unidad USB ?', txt)


def show_help_proxies(item):
    logger.info()

    txt = '[COLOR gold][B]¿ Porqué en algunos canales hay una opción para configurar proxies ?[/B][/COLOR][CR]'
    txt += 'Ciertos canales sufren bloqueos por parte de algunos países/operadoras que no permiten acceder a su contenido.'
    txt += ' Mediante el uso de proxies se puede evitar esa restricción.'

    txt += '[CR][CR][COLOR gold][B]¿ En qué canales hay que usar los proxies ?[/B][/COLOR][CR]'
    txt += 'Depende de la conexión de cada usuario (el país desde dónde se conecta, con qué operadora, qué [COLOR limegreen][B]DNS[/COLOR] tiene configurados, si usa ó no [COLOR limegreen][B]VPN[/COLOR], ...).'
    txt += ' Lo más aconsejable es probar primero si funcionan sin necesidad de proxies ya que es lo más cómodo y rápido.'
    txt += ' Aunque un canal tenga la opción de proxies no es obligatorio usarlos, hacerlo solamente si es necesario.'

    txt += '[CR][CR][COLOR gold][B]¿ Se pueden descartar los canales que requieren proxies ?[/B][/COLOR][CR]'
    txt += 'Sí, desde la opción dentro de buscar [COLOR cyan][B]Excluir canales en las búsquedas[/B][/COLOR].'
    txt += 'También, desde el listado de canales de películas y/ó series, en el [COLOR yellow][B]Menú Contextual[/B][/COLOR] se pueden desactivar los canales deseados.'
    txt += ' De esta manera quedarán descartados para las búsquedas globales, se evitarán sus mensajes relacionados con los proxies'
    txt += ' y se acelerará la búsqueda.'

    txt += '[CR][CR][COLOR gold][B]¿ Como obtener los proxies en un canal determinado ó Globalmente ?[/B][/COLOR][CR]'
    txt += 'Para un canal determinado, acceder a el canal, y en [COLOR goldenrod][B]Acciones[/COLOR] [COLOR plum](si no hay resultados)[/B][/COLOR],[CR]' 
    txt += 'ejecutar [COLOR red][B]Configurar proxies a usar ...[/B][/COLOR][CR][CR]'
    txt += 'Para Globalmente, use la opción Configurar Proxies a usar [COLOR plum][B](en los canales que los Necesiten)[/B][/COLOR]'

    txt += '[CR][CR][COLOR gold][B]¿ Cómo se usan los Ajustes de proxies ?[/B][/COLOR][CR]'
    txt += 'Por defecto en los Ajustes de Balandro esta activada la opción [COLOR red][B]Buscar proxies automáticamente[/B][/COLOR] ello efectua un barrido de búsqueda de acuerdo con el proveedor informado.'

    txt += '[CR][CR]En los Ajustes de [COLOR goldenrod][B]Proxies[/B][/COLOR] se pueden personalizar (Dejar de buscar si se hallaron suficientes válidos, Proveedor de proxies habitual, Limitar la cantidad de válidos a memorizar,'
    txt += ' las solicitudes de Anonimidad, País, etc.)'

    txt += '[CR][CR]En el caso de No obtener suficientes proxies, se puede [COLOR goldenrod][B]Aumentar/No Limitar[/B][/COLOR] el número de proxies válidos a buscar en los [COLOR yellow][B]Apartados Proceso/Especiales[/B][/COLOR] de la [COLOR yellow][B]Categoría Proxies[/B][/COLOR] dentro de los [COLOR goldenrod][B]Ajustes[/COLOR] de Balandro'

    txt += '[CR][CR][COLOR gold][B]¿ Cómo funciona el proceso de Búsqueda ?[/B][/COLOR][CR]'
    txt += 'Una vez finalizado el Proceso de Búsqueda se presentará la consola de resultados con varias [COLOR goldenrod][B]Opciones:[/B][/COLOR]'

    txt += '[CR][CR] - La primera opción [COLOR plum][B]Informar proxies manualmente[/B][/COLOR] es para indicar manualmente los proxies a usar.'
    txt += '[CR] - La segunda opción [COLOR yellow][B]Buscar nuevos proxies[/B][/COLOR] es para realizar una búsqueda de proxies para el canal.'
    txt += '[CR] - La tercera opción [COLOR cyan][B]Parámetros búsquedas[/B][/COLOR] sirve para configurar ciertas opciones para la búsqueda de proxies.'

    txt += '[CR][CR] - Las opciones por defecto son suficientes, pero si no se obtubieran resultados, pueden cambiar algúno de los parámetros para el proceso (el proveedor de dónde se obtienen, el tipo de proxy, ...).'

    txt += '[CR][CR] - Por defecto, los tres proxies más rápidos entre los válidos se guardarán en la configuración del canal.'

    txt += '[CR][CR][COLOR gold][B]¿ Qué hacer si no se obtiene proxies con el proveedor seleccionado ?[/B][/COLOR][CR]'

    txt += '[COLOR aquamarine][B]En el caso de No obtener proxies válidos con un proveedor, pues hay que tener paciencia,[CR]'
    txt += 'e ir probando uno a uno, los Proveedores de proxies de la [COLOR yellow][B]Lista de Proveedores[/B][/COLOR][CR]'
    txt += '[COLOR yellowgreen][B],o bien prescindir/desactivar el canal hasta que se estabilize posiblemente en un futuro.[/B][/COLOR]'

    txt += '[CR][CR][COLOR gold][B]¿ Cuales son los proveedores Recomendados ?[/B][/COLOR][CR]'

    txt += '[COLOR chartreuse][B]Mmpx12,  Pproxyscrape.com,  Uus-proxy.org[/COLOR]'
    if config.get_setting('proxies_extended', default=False): txt += '[COLOR chartreuse][B],  Free-proxy-list.anon[/B][/COLOR]'

    txt += '[CR][CR][COLOR gold][B]¿ Como quitar los proxies en un canal determinado ?[/B][/COLOR][CR]'
    txt += 'Pulsación sostenida sobre el texto [COLOR red][B]Configurar proxies a usar ... [/B][/COLOR]dentro del canal y ahí aparecerá un [COLOR yellow][B]Menú Contextual[/B][/COLOR] con esa opción,'
    txt += ' ó bien dentro del proceso de buscar proxies, en la consola de resultados la opción [COLOR red][B]Quitar proxies[/B][/COLOR].'

    txt += '[CR][CR][COLOR gold][B]¿ Se ralentizan los canales si se utilizan proxies ?[/B][/COLOR][CR]'
    txt += 'Sí, acceder a las webs de los canales a través de proxies ralentiza considerablemente lo que tardan en responder.'
    txt += ' Aún así, [COLOR yellowgreen][B]hay proxies más rápidos que otros, ó más estables, ó menos saturados, ó más duraderos, gratuítos ó de pago, etc.[/B][/COLOR]'

    txt += '[CR][CR][COLOR gold][B]¿ Porqué muchos proxies dejan de funcionar ?[/B][/COLOR][CR]'
    txt += 'Los proxies que se pueden encontrar en la búsqueda [COLOR yellowgreen][B]son todos gratuítos pero tienen ciertas limitaciones y no siempre están activos.[/B][/COLOR]'
    txt += ' Para cada canal se guardan los proxies a utilizar, pero es posible que algunos días cuando entres tengas que volver a hacer una búsqueda de proxies porque han dejado de funcionar.'

    platformtools.dialog_textviewer('Uso de Proxies', txt)


def show_help_tests(item):
    logger.info()

    txt = '[COLOR gold][B]Test Web Canal Método 1:[/B][/COLOR][CR]'

    txt += 'En el Listado de Canales, pulsación sostenida sobre el Nombre del canal y ahí [COLOR darkorange][B]Test Web Canal[/B][/COLOR][CR][CR]'

    txt += '[COLOR gold][B]Test Web Canal Método 2:[/B][/COLOR][CR]'

    txt += 'Entrando en el Canal, si el canal dispone de la opción [COLOR goldenrod][B]Acciones (si no hay resultados)[/B][/COLOR], [COLOR chartreuse][B]Test Web del canal[/B][/COLOR][CR]'

    platformtools.dialog_textviewer('Métodos para Efectuar el Test Web de un canal', txt)


def show_help_metodos(item):
    logger.info()

    txt = '[COLOR yellowgreen][B]Solo proceder si el [/COLOR][COLOR darkorange]Test Wed del Canal[/COLOR][COLOR yellowgreen] da el aviso de que en ese canal ya [/COLOR][COLOR darkorange]No se Necesitan[/B][/COLOR][CR][CR]'

    txt += '[COLOR gold][B]Quitar Proxies Canal Método 1:[/B][/COLOR][CR]'

    txt += 'En el Listado de Canales, pulsación sostenida sobre el Nombre del canal y ahí [COLOR red][B]Quitar los proxies[/B][/COLOR][CR][CR]'

    txt += '[COLOR gold][B]Quitar Proxies Canal Método 2:[/B][/COLOR][CR]'

    txt += 'Entrando en el Canal, si el canal dispone de la opción [COLOR goldenrod][B]Acciones (si no hay resultados)[/B][/COLOR], pulsación sostenida sobre [COLOR red][B]Configurar proxies a usar ...[/B][/COLOR] y ahí [COLOR red][B]Quitar los proxies[/B][/COLOR][CR][CR]'

    txt += '[COLOR gold][B]Quitar Proxies Canal Método 3:[/B][/COLOR][CR]'

    txt += 'Dentro de la Consola del Proceso de obtención de proxies, [COLOR cyan][B]CANCELAR[/B][/COLOR], y ahí [COLOR red][B]Quitar los proxies[/B][/COLOR]'

    platformtools.dialog_textviewer('Métodos para Quitar los Proxies de un canal', txt)


def show_channels_parameters(item):
    txt = '[COLOR yellow][B]CANALES:[/B][/COLOR]'

    todos = True

    if config.get_setting('mnu_simple', default=False):
        todos = False

        txt += '[CR] - Opera con el Menú [B][COLOR tan]SIMPLIFICADO[/COLOR][/B][CR]'
        txt += '    - No Se Muestran los canales [B][I][COLOR plum]Inestables[/COLOR][/I][/B][CR]'
        txt += '    - No Se Muestran los canales que sean [B][I][COLOR turquoise]Clones[/COLOR][/I][/B][CR]'
        txt += '    - No Se Muestran los canales [B][I][COLOR darkgoldenrod]Problemáticos[/COLOR][/I][/B][CR]'
    else:
        if config.get_setting('channels_list_no_inestables', default=False): todos = False
        if config.get_setting('channels_list_no_problematicos', default=False): todos = False
        if config.get_setting('channels_list_no_clones', default=False): todos = False

    channels_list_status = config.get_setting('channels_list_status', default=0)

    if channels_list_status == 0: 
       if todos: txt += '[CR] - Se Muestran [B][COLOR goldenrod]TODOS LOS CANALES[/COLOR][/B][CR]'
       else: txt += '[CR] - Se Muestran Solo [B][COLOR goldenrod]DETERMINADOS CANALES[/COLOR][/B][CR]'

    elif channels_list_status == 1: txt += '[CR] - Solo se Muestran los canales [B][COLOR goldenrod]PREFERIDOS Y ACTIVOS[/COLOR][/B][CR]'
    else: txt += '[CR] - Solo se Muestran los canales [B][COLOR goldenrod]PREFERIDOS[/COLOR][/B][CR]'
 
    if config.get_setting('channels_list_order', default=True): txt += '[CR] - Se Presentan los canales [B][COLOR gold]Preferidos[/COLOR][/B] al principio de las Listas[CR]'

    if not config.get_setting('mnu_desactivados', default=False):
        txt += '[CR] - Se Presentan los canales [B][COLOR gray]Desactivados[/COLOR][/B] al final de las Listas[CR]'

    if config.get_setting('channels_list_no_inestables', default=False): txt += '[CR] - No se presentan los canales [COLOR plum][B]Inestables[/B][/COLOR][CR]'

    if config.get_setting('channels_list_no_problematicos', default=False): txt += '[CR] - No se presentan los canales [COLOR darkgoldenrod][B]Problemáticos[/B][/COLOR][CR]'

    if config.get_setting('channels_list_no_clones', default=False): txt += '[CR] - No se presentan los canales que sean [COLOR turquoise][B]Clones[/B][/COLOR][CR]'

    if not config.get_setting('channels_seasons', default=True) or not config.get_setting('channels_charges', default=True):
        txt += '[CR] - [COLOR cyan][B]Temporadas y/ó Epidodios:[/B][/COLOR]'

        if not config.get_setting('channels_seasons', default=True): txt += '[CR]    - Notificar cuando [COLOR tan][B]No existan Temporadas ó tan solo haya Una[/B][/COLOR] ' + '[COLOR yellow][B] Des-Activado[/B][/COLOR]'

        if not config.get_setting('channels_charges', default=True): txt += '[CR]    - Presentar sin Notificar Todos los [COLOR darkcyan][B]Episodios[/B][/COLOR] en cada Temporada ' + '[COLOR yellow][B] Des-Activado[/B][/COLOR]'

        txt += '[CR]'

    txt += '[CR]'

    if not item._mnu:
        txt_disableds = _menu_parameters()

        if txt_disableds:
            txt += '[COLOR yellow][B]MENÚS:[/B][/COLOR][CR]'
            txt += txt_disableds

        txt_specials = _menu_specials()

        if txt_specials:
            txt += '[COLOR yellow][B]OTRAS OPCIONES EN PRINCIPAL, MENÚS Y SUB-MENÚS:[/B][/COLOR][CR]'
            txt += txt_specials

    if descartar_anime or descartar_xxx:
        txt += '[COLOR orange][B]PARENTAL:[/B][/COLOR][CR]'

        if descartar_anime: txt += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción para Descartar los Canales Exclusivos de [B][COLOR springgreen]Animes[/COLOR][/B][CR]'
        if descartar_xxx: txt += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción para Descartar los Canales con Listas/Géneros para [B][COLOR orange]Adultos[/COLOR][/B][CR]'

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_preferidos', default=True):
            txt += '[COLOR wheat][B]PREFERIDOS:[/B][/COLOR][CR]'

            item.category = trackingtools.get_current_dbname()

            db = trackingtools.TrackingData()
            count_movies = db.get_movies_count()
            count_shows = db.get_shows_count()
            count_episodes = db.get_episodes_count()
            db.close()

            if (count_movies + count_shows + count_episodes) == 0: txt += ' - [COLOR goldenrod]Aún no tiene[/COLOR][CR]'
            else: txt += ' - [COLOR plum]Hay preferidos[/COLOR][CR]'

            txt += '[CR]'

        if config.get_setting('mnu_desargas', default=True):
            txt += '[COLOR seagreen][B]DESCARGAS:[/B][/COLOR][CR]'

            download_path = config.get_setting('downloadpath', default='')
            if not download_path: download_path = filetools.join(config.get_data_path(), 'downloads')

            if not filetools.exists(download_path): filetools.mkdir(download_path)

            if download_path.startswith('smb://'):
                fichs = sorted(filetools.listdir(download_path))
                ficheros = [filetools.join(download_path, fit) for fit in fichs if fit.endswith('.json')]
            else:
                path = filetools.join(download_path, '*.json')
                ficheros = glob.glob(path)
                ficheros.sort(key=os.path.getmtime, reverse=False)

            if not ficheros: txt += ' - [COLOR goldenrod]Aún no tiene[/COLOR][CR]'
            else: txt += ' - [COLOR plum]Hay descargas[/COLOR][CR]'

            txt += '[CR]'

    avisar = False

    if not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developergenres.py')): avisar = True
    elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')): avisar = True
    elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')): avisar = True

    if config.get_setting('developer_mode', default=False):
        if not avisar:
            txt += '[COLOR crimson][B]DESARROLLO:[/B][/COLOR]'
        else:
            txt += '[COLOR crimson][B]FALSO DESARROLLO:[/B][/COLOR]'

        txt += '[CR] - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú [B][COLOR darkorange]Desarrollo[/COLOR][/B] en los ajustes categoría [B][COLOR goldenrod]Team[/COLOR][/B]'

    platformtools.dialog_textviewer('Información Parámetros Actuales para Mostrar los Canales en las Listas', txt)


def show_parental_parameters(item):
    if config.get_setting('mnu_simple', default=False):
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]NO disponible en [COLOR yellow]Menú Simplificado[/B][/COLOR]' % color_alert)
        return

    if config.get_setting('adults_password', default=''): txt = '[COLOR yellow][B]Tiene informado un PIN control Parental[/B][/COLOR][CR]'
    else: txt = '[COLOR red][B]NO Tiene informado un PIN control Parental[/B][/COLOR][CR]'

    txt += '[CR][COLOR springgreen][B]ANIMES:[/B][/COLOR][CR]'

    if config.get_setting('adults_password', default=''):
        if config.get_setting('animes_password', default=True): txt += ' - [COLOR cyan][B]Tiene Activado Solicitar PIN Parental[/B][/COLOR] en los Canales exclusivos de [B][COLOR springgreen]Animes[/COLOR][/B][CR]'
        else: txt += ' - [COLOR greenyellow][B]Tiene Desactivado Solicitar PIN Parental[/B][/COLOR] en los Canales exclusivos de [B][COLOR springgreen]Animes[/COLOR][/B][CR]'

    if config.get_setting('mnu_animes', default=True): txt += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR yellow][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR springgreen]Animes[/COLOR][/B][CR]'
    else: txt += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR springgreen]Animes[/COLOR][/B][CR][CR]'

    txt += '[CR][COLOR orange][B]ADULTOS (+18):[/B][/COLOR][CR]'

    if config.get_setting('mnu_adultos', default=True): txt += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR yellow][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR orange]Adultos[/COLOR][/B][CR]'
    else: txt += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR orange]Adultos[/COLOR][/B][CR][CR]'

    if descartar_anime or descartar_xxx:
        txt += '[CR][COLOR goldenrod][B]DESCARTAR:[/B][/COLOR][CR]'

        if descartar_anime: txt += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción para Descartar los Canales Exclusivos de [B][COLOR springgreen]Animes[/COLOR][/B][CR]'
        if descartar_xxx: txt += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción para Descartar los Canales con Listas/Géneros para [B][COLOR orange]Adultos[/COLOR][/B][CR]'

    platformtools.dialog_textviewer('Información Parámetros Actuales para Control Parental', txt)


def show_play_parameters(item):
    txt = '[COLOR yellow][B]PLAY:[/B][/COLOR]'

    txt += '[CR][CR][COLOR orchid][B] - ADD-ONS EXTERNOS y VIAS ALTERNATIVAS:[/B][/COLOR]'

    cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

    if cliente_torrent == 'Seleccionar' or cliente_torrent == 'Ninguno': tex_tor = cliente_torrent
    else:
       tex_tor = cliente_torrent
       cliente_torrent = 'plugin.video.' + cliente_torrent.lower()
       if xbmc.getCondVisibility('System.HasAddon("%s")' % cliente_torrent):
           cod_version = xbmcaddon.Addon(cliente_torrent).getAddonInfo("version").strip()
           tex_tor += '  [COLOR goldenrod]' + cod_version + '[/COLOR]'

    txt += '[CR]    - Cliente/Motor Torrent Habitual asignado ' + '[COLOR orchid][B] ' + tex_tor + '[/B][/COLOR]'

    if xbmc.getCondVisibility('System.HasAddon("inputstream.adaptive")'):
        cod_version = xbmcaddon.Addon("inputstream.adaptive").getAddonInfo("version").strip()
        tex_ia = '  [COLOR goldenrod][B]' + cod_version
    else: tex_ia = '  [COLOR red]No instalado[/COLOR]'

    txt += '[CR]    - [COLOR orchid][B]InputStream Adaptive[/B][/COLOR] ' + tex_ia + '[/B][/COLOR]'

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
        cod_version = xbmcaddon.Addon("plugin.video.youtube").getAddonInfo("version").strip()
        tex_yt = '  [COLOR goldenrod][B]' + cod_version
    else: tex_yt = '  [COLOR red]No instalado[/COLOR]'

    txt += '[CR]    - [COLOR orchid][B]Youtube[/B][/COLOR] ' + tex_yt + '[/B][/COLOR]'

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        cod_version = xbmcaddon.Addon("script.module.resolveurl").getAddonInfo("version").strip()
        tex_mr = '  [COLOR goldenrod][B]' + cod_version
    else: tex_mr = '  [COLOR red]No instalado[/COLOR]'

    txt += '[CR]    - [COLOR orchid][B]ResolveUrl[/B][/COLOR] ' + tex_mr + '[/B][/COLOR]'

    txt += '[CR][CR][COLOR fuchsia][B] - AUTO PLAY:[/B][/COLOR]'

    if config.get_setting('autoplay', default=False):
        txt += '[CR]    - [COLOR yellow][B] Activado[/B][/COLOR]'
        txt += '[CR]    -  Número máximo de enlaces para intentar el auto play (por defecto 10): [COLOR coral][B]' + str(config.get_setting('autoplay_max_links', default=10)) + '[/COLOR][/B]'
    else: txt += '[CR]    - [COLOR yellow][B] Des-Activado[/B][/COLOR]'

    if config.get_setting('autoplay_one_link', default=True): txt += '[CR]    -  Si solo hay [COLOR gold][B]Un enlace[/B][/COLOR] reproducirlo automáticamente[COLOR yellow][B]  Activado[/B][/COLOR]'
    else: txt += '[CR]    -  Si solo hay [COLOR gold][B]Un enlace[/B][/COLOR] reproducirlo automáticamente[COLOR yellow][B]  Des-Activado[/B][/COLOR]'

    if config.get_setting('autoplay_channels_discarded', default=''):
        txt += '[CR]    -  Canales descartados:'
        sin_autoplay = config.get_setting('autoplay_channels_discarded').split(',')

        for no_autoplay in sin_autoplay:
            no_autoplay = no_autoplay.lower().strip()
            txt += '[CR]       [COLOR gray][B] ' + no_autoplay + '[/B][/COLOR]'

    txt += '[CR][CR][COLOR fuchsia][B] - ORDENAR Y/Ó FILTRAR POR IDIOMA:[/B][/COLOR]'

    tex_idio = 'Descartar'
    if config.get_setting('preferencia_idioma_esp') == 1: tex_idio = 'Primero'
    elif config.get_setting('preferencia_idioma_esp') == 2: tex_idio = 'Segundo'
    elif config.get_setting('preferencia_idioma_esp') == 3: tex_idio = 'Tercero'

    txt += '[CR]    -  Idioma [COLOR red][B]Esp[/B][/COLOR] (castellano de España) ' +  '[COLOR yellow][B] ' + tex_idio + '[/B][/COLOR]'

    tex_idio = 'Descartar'
    if config.get_setting('preferencia_idioma_lat') == 1: tex_idio = 'Primero'
    elif config.get_setting('preferencia_idioma_lat') == 2: tex_idio = 'Segundo'
    elif config.get_setting('preferencia_idioma_lat') == 3: tex_idio = 'Tercero'

    txt += '[CR]    -  Idioma [COLOR red][B]Lat[/B][/COLOR] (castellano de América) ' +  '[COLOR yellow][B] ' + tex_idio + '[/B][/COLOR]'

    tex_idio = 'Descartar'
    if config.get_setting('preferencia_idioma_vos') == 1: tex_idio = 'Primero'
    elif config.get_setting('preferencia_idioma_vos') == 2: tex_idio = 'Segundo'
    elif config.get_setting('preferencia_idioma_vos') == 3: tex_idio = 'Tercero'

    txt += '[CR]    -  Idioma [COLOR red][B]Vose, VO[/B][/COLOR] (versión Subtitulada y/ó Original) ' +  '[COLOR yellow][B] ' + tex_idio + '[/B][/COLOR]'

    txt += '[CR][CR][COLOR fuchsia][B] - ORDENAR POR CALIDAD:[/B][/COLOR]'

    tex_qlty = 'Orden de la Web'

    if config.get_setting('servers_sort_quality') == 1: tex_qlty = 'Calidad Descendente'
    elif config.get_setting('servers_sort_quality') == 2: tex_qlty = 'Calidad Ascendente'

    txt += '[CR]    -  En cada idioma ordenar los enlaces según ' +  '[COLOR yellow][B] ' + tex_qlty + '[/B][/COLOR]'

    if config.get_setting('servers_preferred', default='') or config.get_setting('servers_unfavored', default='') or config.get_setting('servers_discarded', default=''):
        txt += '[CR][CR][COLOR fuchsia][B] - FILTRAR SERVIDORES:[/B][/COLOR]'

        if config.get_setting('servers_preferred', default=''):
            txt += '[CR][COLOR yellow]    -  [/COLOR][COLOR darkorange]Servidores Preferidos[/COLOR]:'
            servers = config.get_setting('servers_preferred').split(',')

            for server in servers:
                server = server.lower().strip()
                txt += '[CR]      [COLOR gold] ' + server + '[/COLOR]'

            txt += '[CR]'

        if config.get_setting('servers_unfavored', default=''):
            txt += '[CR][COLOR yellow]    -  [/COLOR][COLOR blue]Servidores como Última opción[/COLOR]:'
            servers = config.get_setting('servers_unfavored').split(',')

            for server in servers:
                server = server.lower().strip()
                txt += '[CR]       [COLOR blue] ' + server + '[/COLOR]'

            txt += '[CR]'

        if config.get_setting('servers_discarded', default=''):
            txt += '[CR][COLOR yellow]    -  [/COLOR][COLOR gray]Servidores Descartados[/COLOR]:'
            servers = config.get_setting('servers_discarded').split(',')

            for server in servers:
                server = server.lower().strip()
                txt += '[CR]       [COLOR gray] ' + server + '[/COLOR]'

            txt += '[CR]'

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
        txt += '[CR][CR][COLOR fuchsia][B] - TRAÍLERS:[/B][/COLOR] a través de [COLOR yellow][B]YouTube[/B][/COLOR]'
    else:
        txt += '[CR][CR][COLOR fuchsia][B] - TRAÍLERS:[/B][/COLOR] [COLOR yellow][B]YouTube[/B][/COLOR] [COLOR red][B]No Instalado[/B][/COLOR]'

    platformtools.dialog_textviewer('Información Parámetros Actuales en Play', txt)


def show_prx_parameters(item):
    default_provider = 'proxyscrape.com'
    all_providers = 'All-providers'
    private_list = 'Lista-proxies.txt'

    opciones_provider = [
            'spys.one',
            'hidemy.name',
            'httptunnel.ge',
            'proxynova.com',
            'free-proxy-list',
            'spys.me',
            default_provider,
            'proxyservers.pro',
            'us-proxy.org',
            'proxy-list.download',
            all_providers,
            'proxysource.org',
            'silverproxy.xyz',
            'dailyproxylists.com',
            'sslproxies.org',
            'clarketm',
            'google-proxy.net',
            'ip-adress.com',
            'proxydb.net',
            'hidester.com',
            'geonode.com',
            'mmpx12',
            'roosterkid',
            'almroot',
            'shiftytr',
            'mertguvencli',
            private_list
            ]

    txt = '[COLOR yellow][B]PROVEEDORES:[/B][/COLOR]'

    provider = config.get_setting('proxies_provider')
    provider = opciones_provider[provider]

    txt += '[CR][COLOR gold] - Proveedor Habitual (por defecto Todos):[/COLOR]' + ' [COLOR cyan][B]' + provider + '[/B][/COLOR][CR]'

    if config.get_setting('proxies_list', default=False):
        path = os.path.join(config.get_data_path(), 'Lista-proxies.txt')

        existe = filetools.exists(path)

        if existe: txt += '[CR][COLOR gold] - [B]Lista-proxies.txt:[COLOR cyan] Personalizada[/B][/COLOR][CR]'

    txt += '[CR][COLOR gold] - Ampliar Lista de Proveedores:[/COLOR]'

    if config.get_setting('proxies_extended', default=False): txt += ' [COLOR cyan][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Solo tener en cuenta al procesar los Proveedores Recomendados:[/COLOR]'

    if config.get_setting('proxies_recommended', default=False): txt += '[COLOR cyan][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Tratar Primero en las búsquedas los Proveedores de la Lista Ampliada:[/COLOR]'

    if config.get_setting('proxies_search_extended', default=False): txt += ' [COLOR cyan][B] Activado[/B][/COLOR][CR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR][CR]'

    if config.get_setting('providers_preferred', default=''):
        txt += '[CR][COLOR gold] - Tratar Solo los Proveedores Preferidos:[/COLOR]'
        providers_preferred = config.get_setting('providers_preferred').split(',')

        for provider_preferred in providers_preferred:
            provider_preferred = provider_preferred.lower().strip()
            txt += '[CR]   [COLOR cyan][B] ' + provider_preferred + '[/B][/COLOR]'

        txt += '[CR]'

    txt += '[CR][COLOR yellow][B]PROCESOS:[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Buscar Automáticamente (solo si Proveedor Habitual Todos/All-Providers):[/COLOR]'

    if config.get_setting('proxies_auto', default=True): txt += '[CR]    - [COLOR cyan][B] Activado[/B][/COLOR][CR]'
    else: txt += '[CR]    - [COLOR cyan][B] Des-Activado[/B][/COLOR][CR]'

    txt += '[CR][COLOR gold] - Límite Máximo Total de proxies para Analizar (por defecto 500):[/COLOR]' + ' [COLOR cyan][B]' + str(config.get_setting('proxies_totales_limit')) + '[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Si se encontraron Suficientes proxies válidos dejar de buscar más:[/COLOR]'

    if config.get_setting('proxies_limit', default=False): txt += ' [COLOR cyan][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Limitar la Cantidad de proxies válidos:[/COLOR]'

    if config.get_setting('proxies_validos', default=True): txt += ' [COLOR cyan][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Cantidad Máxima de proxies válidos (por defecto 5):[/COLOR]' + ' [COLOR cyan][B]' + str(config.get_setting('proxies_memory')) + '[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Al gestionar los proxies Auto-Eliminar los NO válidos:[/COLOR]'

    if config.get_setting('proxies_erase', default=True): txt += ' [COLOR cyan][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Añadir la opción Ayuda (Información uso de proxies):[/COLOR]'

    if config.get_setting('proxies_help', default=True): txt += ' [COLOR cyan][B] Activado[/B][/COLOR][CR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR][CR]'

    txt += '[CR][COLOR yellow][B]PROCESOS VÍAS ALTERNATIVAS:[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Gestionar Vías alternativas si no se obtubieron suficientes proxies a analizar:[/COLOR]'

    if config.get_setting('proxies_vias', default=False): txt += ' [COLOR cyan][B] Activado (por defecto 32)  '  + str(config.get_setting('proxies_tplus')) + '[/B][/COLOR][CR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR][CR]'

    txt += '[CR][COLOR yellow][B]SOLICITUDES:[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Solicitar el tipo de Anonimidad:[/COLOR]'

    if config.get_setting('proxies_tipos', default=False): txt += ' [COLOR cyan][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR]'

    txt += '[CR][COLOR gold] - Solicitar el País:[/COLOR]'

    if config.get_setting('proxies_paises', default=False): txt += ' [COLOR cyan][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR]'

    txt += '[CR][COLOR gold] - No solicitar y forzar el Valor máximo de los proxies a analizar:[/COLOR]'

    if config.get_setting('proxies_maximo', default=True): txt += ' [COLOR cyan][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR cyan][B] Des-Activado[/B][/COLOR]'

    if config.get_setting('proxies_list', default=False): txt += '[CR][COLOR gold] - Habilitar la selección de su Lista Personalizada:[/COLOR]' + ' [COLOR cyan][B] Activado[/B][/COLOR]'

    platformtools.dialog_textviewer('Información Parámetros Actuales en Proxies', txt)


def _menu_parameters():
    txt_disableds = ''

    if not config.get_setting('mnu_sugeridos', default=True):
        txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR aquamarine]Sugeridos[/COLOR][/B][CR][CR]'
    else:
        txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR aquamarine]Sugeridos[/COLOR][/B][CR][CR]'

    if not config.get_setting('channels_link_main', default=True):
        txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR gold]Canales[/COLOR][/B][CR][CR]'
    else:
        txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR gold]Canales[/COLOR][/B][CR][CR]'

    if config.get_setting('channels_mnu_preferidos', default=False):
        txt_disableds += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR gold]Canales Preferidos[/COLOR][/B][CR][CR]'
    else:
        txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR gold]Canales Preferidos[/COLOR][/B][CR][CR]'

    if not config.get_setting('mnu_idiomas', default=True):
        txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada/[B][/COLOR] la opción del Menú principal [B][COLOR limegreen]Idiomas[/COLOR][/B][CR][CR]'
    else:
        if config.get_setting('mnu_problematicos', default=False):
            txt_disableds += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR limegreen]Idiomas[/COLOR][/B][CR]'

            txt_disableds += '   Además NO se mostrarán los canales que sean [COLOR darkgoldenrod]Problemáticos[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR limegreen]Idiomas[/COLOR][/B][CR][CR]'

    if not config.get_setting('mnu_grupos', default=True):
        txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR magenta]Grupos[/COLOR][/B][CR][CR]'
    else:
        if config.get_setting('mnu_problematicos', default=False):
            txt_disableds += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR magenta]Grupos[/COLOR][/B][CR]'

            txt_disableds += '   Además NO se mostrarán los canales que sean [COLOR darkgoldenrod]Problemáticos[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR magenta]Grupos[/COLOR][/B][CR][CR]'

    if config.get_setting('mnu_simple', default=False):
        txt_disableds += ' - [B][COLOR crimson]Menú Simplificado:[/B][/COLOR][CR]'

        txt_disableds += '   - No se presentará [COLOR gold]Jamás[/COLOR] la opción del Menú principal [B][COLOR wheat]Preferidos[/COLOR][/B][CR]'
        txt_disableds += '     Además no se mostrará en los [COLOR yellow][B]Menús Contextuales[/B][/COLOR] la opción [COLOR darkorange][B]Guardar en Preferidos[/B][/COLOR][CR][CR]'

        txt_disableds += '   - No se presentará [COLOR gold]Jamás[/COLOR] la opción del Menú principal [B][COLOR seagreen]Descargas[/COLOR][/B][CR]'
        txt_disableds += '     Además no se mostrará en los [COLOR yellow][B]Menús Contextuales[/B][/COLOR] la opción [COLOR darkorange][B]Descargar Vídeo[/B][/COLOR][CR][CR]'

        txt_disableds += '   - No se presentarán [COLOR gold][B]Nunca[/B][/COLOR] las opciones de:[CR]'
        txt_disableds += '      - [B][COLOR deepskyblue]Películas[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR hotpink]Series[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR teal]Películas y Series[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR thistle]Géneros[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR cyan]Documentales[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR lightyellow]Infantiles[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR limegreen]Novelas[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR blue]Torrents[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR firebrick]Doramas[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR springgreen]Animes[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR orange]Adultos[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR red]Proxies[/COLOR][/B][CR]'
        txt_disableds += '      - [B][COLOR darkgoldenrod]Problemáticos[/B][/COLOR][CR]'
        txt_disableds += '      - [B][COLOR gray]Desactivados[/COLOR][/B][CR][CR]'

    else:

        if not config.get_setting('mnu_pelis', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR deepskyblue]Películas[/COLOR][/B][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR deepskyblue]Películas[/COLOR][/B][CR][CR]'

        if not config.get_setting('mnu_series', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR hotpink]Series[/COLOR][/B][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR hotpink]Series[/COLOR][/B][CR][CR]'

        if config.get_setting('channels_link_pyse', default=False):
            txt_disableds += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR teal]Películas y Series[/COLOR][/B][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR teal]Películas y Series[/COLOR][/B][CR][CR]'

        if not config.get_setting('mnu_generos', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR thistle]Géneros[/COLOR][/B][CR][CR]'
        else:
            if config.get_setting('mnu_problematicos', default=False):
                txt_disableds += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR thistle]Géneros[/COLOR][/B][CR]'

                txt_disableds += '   Además NO se mostrarán los canales que sean [COLOR darkgoldenrod]Problemáticos[/COLOR][CR][CR]'
            else:
                txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR thistle]Géneros[/COLOR][/B][CR][CR]'

        if not config.get_setting('mnu_documentales', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR cyan]Documentales[/COLOR][/B][CR]'

            txt_disableds += '   Además NO se mostrarán en el resto de las opciones del Menú principal los canales que sean [COLOR cyan]Exclusivos de Documentales[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR cyan]Documentales[/COLOR][/B][CR][CR]'

        if not config.get_setting('mnu_infantiles', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR lightyellow]Infantiles[/COLOR][/B][CR]'

            txt_disableds += '   Además NO se mostrarán en el resto de las opciones del Menú principal los canales que sean [COLOR lightyellow]Exclusivos de Infantiles[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está  [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR lightyellow]Infantiles[/COLOR][/B][CR][CR]'

        if not config.get_setting('mnu_novelas', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR limegreen]Novelas[/COLOR][/B][CR]'

            txt_disableds += '   Además NO se mostrarán en el resto de las opciones del Menú principal los canales que sean [COLOR limegreen]Exclusivos de Novelas[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está  [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR limegreen]Novelas[/COLOR][/B][CR][CR]'

        if not config.get_setting('mnu_torrents', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR blue]Torrents[/COLOR][/B][CR]'

            txt_disableds += '   Además NO se mostrarán en el resto de las opciones del Menú principal los canales que sean [COLOR blue]Exclusivos de Torrents[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está  [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR blue]Torrents[/COLOR][/B][CR][CR]'

        if not config.get_setting('mnu_doramas', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR firebrick]Doramas[/COLOR][/B][CR]'

            txt_disableds += '   Además NO se mostrarán en el resto de las opciones del Menú principal los canales que sean [COLOR firebrick]Exclusivos de Doramas[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está  [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR firebrick]Doramas[/COLOR][/B][CR][CR]'

        if not config.get_setting('mnu_animes', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR springgreen]Animes[/COLOR][/B][CR]'

            txt_disableds += '   Además NO se mostrarán en el resto de las opciones del Menú principal los canales que sean [COLOR springgreen]Exclusivos de Animes[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está  [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR springgreen]Animes[/COLOR][/B][CR][CR]'

        if not config.get_setting('mnu_adultos', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR orange]Adultos[/COLOR][/B][CR]'

            txt_disableds += '   Además NO se mostrarán en el resto de las opciones del Menú principal los canales que sean [COLOR orange]Exclusivos para Adultos[/COLOR][CR][CR]'
        else:
             txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR orange]Adultos[/COLOR][/B][CR][CR]'

        if config.get_setting('mnu_proxies', default=False):
            txt_disableds += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR red]Proxies[/COLOR][/B][CR]'

            txt_disableds += '   Siempre se mostrarán en la Opción del Menú principal [COLOR gold][B]Canales[/B][/COLOR][CR]'

            if config.get_setting('mnu_idiomas', default=True): txt_disableds += '   También se mostrarán en la Opción del Menú principal [COLOR limegreen][B]Idiomas[/B][/COLOR][CR]'

            if config.get_setting('mnu_grupos', default=True): txt_disableds += '   También se mostrarán en la Opción del Menú principal [COLOR magenta][B]Grupos[/B][/COLOR][CR]'

            txt_disableds += '   Además NO se mostrarán en el [COLOR gold]Resto de las opciones del Menú principal[/COLOR] los canales con [COLOR red]Proxies[/COLOR] Memorizados[CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR red]Proxies[/COLOR][/B][CR][CR]'

        if config.get_setting('mnu_clones', default=False):
            txt_disableds += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR turquoise]Clones[/COLOR][/B][CR]'

            txt_disableds += '   Siempre se mostrarán en la Opción del Menú principal [COLOR gold][B]Canales[/B][/COLOR][CR]'
            txt_disableds += '   Además NO se mostrarán en el resto de las opciones del Menú principal los canales que sean [COLOR turquoise]Clones[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR turquoise]Clones[/COLOR][/B][CR][CR]'

        if config.get_setting('mnu_problematicos', default=False):
            txt_disableds += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR darkgoldenrod]Problemáticos[/COLOR][/B][CR]'

            txt_disableds += '   Siempre se mostrarán en la Opción del Menú principal [COLOR gold][B]Canales[/B][/COLOR][CR]'
            txt_disableds += '   Además NO se mostrarán en el resto de las opciones del Menú principal los canales que sean [COLOR darkgoldenrod]Problemáticos[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR darkgoldenrod]Problemáticos[/COLOR][/B][CR][CR]'

        if config.get_setting('mnu_desactivados', default=False):
            txt_disableds += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR gray]Desactivados[/COLOR][/B][CR]'

            txt_disableds += '   Siempre se mostrarán en la Opción del Menú principal [COLOR gold][B]Canales[/B][/COLOR][CR]'
            txt_disableds += '   Además NO se mostrarán en el resto de las opciones del Menú principal los canales que esten [COLOR gray]Desactivados[/COLOR][CR][CR]'
        else:
            txt_disableds += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR gray]Desactivados[/COLOR][/B][CR][CR]'

        if not config.get_setting('mnu_preferidos', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR wheat]Preferidos[/COLOR][/B][CR][CR]'

            txt_disableds += '   Además NO se mostrará en los [COLOR yellow][B]Menús Contextuales[/B][/COLOR] la opción [COLOR darkorange][B]Guardar en Preferidos[/B][/COLOR][CR][CR]'

        if not config.get_setting('mnu_desargas', default=True):
            txt_disableds += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR seagreen]Descargas[/COLOR][/B][CR][CR]'

            txt_disableds += '   Además NO se mostrará en los [COLOR yellow][B]Menús Contextuales[/B][/COLOR] la opción [COLOR darkorange][B]Descargar Vídeo[/B][/COLOR][CR][CR]'

    return txt_disableds


def show_mnu_specials(item):
    txt = ''

    txt_specials = _menu_specials()

    if txt_specials:
        txt += '[COLOR yellow][B]OTRAS OPCIONES EN PRINCIPAL, MENÚS Y SUB-MENÚS:[/B][/COLOR][CR]'
        txt += txt_specials

    platformtools.dialog_textviewer('Información Parámetros Actuales para Otras Opciones en Principal, Menús y Sub-Menús', txt)


def _menu_specials():
    txt_specials = ''

    if config.get_setting('mnu_search_proxy_channels', default=False):
        txt_specials += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR red]Buscar Nuevos Proxies[/COLOR][/B][CR][CR]'
    else:
        txt_specials += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR red]Buscar Nuevos Proxies[/COLOR][/B][CR][CR]'

    if config.get_setting('search_extra_proxies', default=True):
        txt_specials += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR red]Búsquedas en Canales con Proxies[/COLOR][/B][CR][CR]'
    else:
        txt_specials += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR red]Búsquedas en Canales con Proxies[/COLOR][/B][CR][CR]'

    if config.get_setting('sub_mnu_favoritos', default=False):
        txt_specials += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR plum]Favoritos[/COLOR][/B][CR][CR]'
    else:
        txt_specials += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR plum]Favoritos[/COLOR][/B][CR][CR]'

    if config.get_setting('search_extra_trailers', default=False):
        txt_specials += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR darkgoldenrod]Tráilers[/COLOR][/B][CR][CR]'
    else:
        txt_specials += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción en los Sub-Menús [B][COLOR darkgoldenrod]Tráilers[/COLOR][/B][CR][CR]'

    if config.get_setting('sub_mnu_news', default=True):
        txt_specials += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR darksalmon]Novedades[/COLOR][/B][CR][CR]'
    else:
        txt_specials += ' - Tiene [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR darksalmon]Novedades[/COLOR][/B][CR][CR]'

    if config.get_setting('search_extra_main', default=False):
        txt_specials += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR violet]Búsquedas Especiales (Listas TMDB, etc.)[/COLOR][/B][CR][CR]'
    else:
        txt_specials += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR violet]Búsquedas Especiales (Listas TMDB, etc.)[/COLOR][/B][CR][CR]'

    if config.get_setting('sub_mnu_special', default=True):
        txt_specials += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR pink]Especiales[/COLOR][/B][CR][CR]'
    else:
        txt_specials += ' - Tiene [COLOR coral][B]Des-habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR pink]Especiales[/COLOR][/B][CR][CR]'

    if config.get_setting('sub_mnu_cfg_search', default=True):
        txt_specials += ' - [COLOR gold]Por Defecto[/COLOR] está [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR moccasin]Personalizar Búsquedas[/COLOR][/B][CR][CR]'
    else:
        txt_specials += ' - Tiene [COLOR coral][B]Des-habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR moccasin]Personalizar Búsquedas[/COLOR][/B][CR][CR]'

    return txt_specials


def show_menu_parameters(item):
    txt = ''

    if config.get_setting('mnu_simple', default=False): txt += 'Opera con el Menú [B][COLOR chocolate]SIMPLIFICADO[/COLOR][/B][CR][CR]'

    txt_disableds = _menu_parameters()

    if txt_disableds:
        txt += 'MENÚS:[CR]'
        txt += txt_disableds

    if not item._mnu:
        txt_specials = _menu_specials()

        if txt_specials:
            txt += 'OTRAS OPCIONES EN PRINCIPAL, MENÚS Y SUB-MENÚS:[CR]'
            txt += txt_specials

    if descartar_anime or descartar_xxx:
        txt += 'PARENTAL:[CR]'

        if descartar_anime: txt += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción para Descartar los Canales Exclusivos de [B][COLOR springgreen]Animes[/COLOR][/B][CR][CR]'
        if descartar_xxx: txt += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción para Descartar los Canales con Listas/Géneros para [B][COLOR orange]Adultos[/COLOR][/B][CR][CR]'

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_preferidos', default=True):
            txt += 'PREFERIDOS:[CR]'

            item.category = trackingtools.get_current_dbname()

            db = trackingtools.TrackingData()
            count_movies = db.get_movies_count()
            count_shows = db.get_shows_count()
            count_episodes = db.get_episodes_count()
            db.close()

            if (count_movies + count_shows + count_episodes) == 0: txt += ' - [COLOR goldenrod][B]Aún no tiene[/B][/COLOR][CR]'
            else: txt += ' - [COLOR plum][B]Hay preferidos[/B][/COLOR][CR]'

            txt += '[CR]'

        if config.get_setting('mnu_desargas', default=True):
            txt += 'DESCARGAS:[CR]'

            download_path = config.get_setting('downloadpath', default='')
            if not download_path: download_path = filetools.join(config.get_data_path(), 'downloads')

            if not filetools.exists(download_path): filetools.mkdir(download_path)

            if download_path.startswith('smb://'):
                fichs = sorted(filetools.listdir(download_path))
                ficheros = [filetools.join(download_path, fit) for fit in fichs if fit.endswith('.json')]
            else:
                path = filetools.join(download_path, '*.json')
                ficheros = glob.glob(path)
                ficheros.sort(key=os.path.getmtime, reverse=False)

            if not ficheros: txt += ' - [COLOR goldenrod][B]Aún no tiene[/B][/COLOR][CR]'
            else: txt += ' - [COLOR plum][B]Hay descargas[/B][/COLOR][CR]'

            txt += '[CR]'

    avisar = False

    if not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developergenres.py')): avisar = True
    elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')): avisar = True
    elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')): avisar = True

    if config.get_setting('developer_mode', default=False):
        if not avisar:
            txt += 'DESARROLLO:[CR]'
        else:
            txt += 'FALSO DESARROLLO:[CR]'

        txt += ' - Tiene [COLOR plum][B]Habilitada[/B][/COLOR] la opción del Menú principal [B][COLOR darkorange]Desarrollo[/COLOR][/B] en los ajustes [B][COLOR goldenrod]Team[/COLOR][/B][CR][CR]'

    platformtools.dialog_textviewer('Información Parámetros Actuales para los Menús', txt)


def show_help_providers(item):
    logger.info()

    txt = '[COLOR aquamarine][B]Podrían tener acceso dinámico a [COLOR wheat]Otros Proveedores[COLOR aquamarine] en funcion del total de proxies obtenidos.[/B][/COLOR][CR]'

    if not item.ampliada:
        providers_preferred = config.get_setting('providers_preferred', default='')
        if providers_preferred:
            txt += '[CR][COLOR wheat][B]Proveedores preferidos:[/B][/COLOR][CR]'
            providers_preferred = config.get_setting('providers_preferred').split(',')

            for provider_preferred in providers_preferred:
                provider_preferred = provider_preferred.lower().strip()
                txt += ' [COLOR violet][B] ' + provider_preferred + '[/B][/COLOR][CR]'

        txt += '[CR][COLOR goldenrod][B]Proveedores habituales:[/B][/COLOR][CR]'

        txt += '  [COLOR yellow]All-providers[/COLOR][CR]'

        if config.get_setting('proxies_list', default=False):
            path = os.path.join(config.get_data_path(), 'Lista-proxies.txt')

            existe = filetools.exists(path)

            if existe: txt += '  [COLOR red][B]Lista-proxies.txt[COLOR lime]  personalizada[/B][/COLOR][CR]'

        txt += '  [COLOR yellow]almroot[/COLOR][CR]'
        txt += '  [COLOR yellow]clarketm[/COLOR][CR]'
        txt += '  [COLOR yellow]dailyproxylists.com[/COLOR][CR]'
        txt += '  [COLOR yellow]free-proxy-list[/COLOR][CR]'
        txt += '  [COLOR yellow]geonode.com[/COLOR][CR]'
        txt += '  [COLOR yellow]google-proxy.net[/COLOR][CR]'
        txt += '  [COLOR yellow]hidemy.name[/COLOR][CR]'
        txt += '  [COLOR yellow]httptunnel.ge[/COLOR][CR]'
        txt += '  [COLOR yellow]hidester.com[/COLOR][CR]'
        txt += '  [COLOR yellow]ip-adress.com[/COLOR][CR]'
        txt += '  [COLOR yellow]mertguvencli[/COLOR][CR]'
        txt += '  [COLOR red][B]mmpx12[COLOR lime]  recomendado[/B][/COLOR][CR]'
        txt += '  [COLOR yellow]proxy-list.download[/COLOR][CR]'
        txt += '  [COLOR yellow]proxydb.net[/COLOR][CR]'
        txt += '  [COLOR yellow]proxynova.com[/COLOR][CR]'
        txt += '  [COLOR red][B]proxyscrape.com[COLOR lime]  recomendado[/B][/COLOR][CR]'
        txt += '  [COLOR yellow]proxyservers.pro[/COLOR][CR]'
        txt += '  [COLOR yellow]proxysource.org[/COLOR][CR]'
        txt += '  [COLOR yellow]roosterkid[/COLOR][CR]'
        txt += '  [COLOR yellow]shiftytr[/COLOR][CR]'
        txt += '  [COLOR yellow]silverproxy.xyz[/COLOR][CR]'
        txt += '  [COLOR yellow]spys.me[/COLOR][CR]'
        txt += '  [COLOR yellow]spys.one[/COLOR][CR]'
        txt += '  [COLOR yellow]sslproxies.org[/COLOR][CR]'
        txt += '  [COLOR red][B]us-proxy.org[COLOR lime]  recomendado[/B][/COLOR][CR]'

    if config.get_setting('proxies_extended', default=False):
        txt += '[CR][COLOR aqua][B]Lista ampliada de proveedores:[/B][/COLOR][CR]'

        txt += '  [COLOR gold]coderduck[/COLOR][CR]'
        txt += '  [COLOR gold]echolink[/COLOR][CR]'
        txt += '  [COLOR red][B]free-proxy-list.anon[COLOR lime]  recomendado[/B][/COLOR][CR]'
        txt += '  [COLOR gold]free-proxy-list.com[/COLOR][CR]'
        txt += '  [COLOR gold]free-proxy-list.uk[/COLOR][CR]'
        txt += '  [COLOR gold]free-proxy-list.uk[/COLOR][CR]'
        txt += '  [COLOR gold]github[/COLOR][CR]'
        txt += '  [COLOR gold]proxy-daily[/COLOR][CR]'
        txt += '  [COLOR gold]proxy-list.org[/COLOR][CR]'
        txt += '  [COLOR gold]proxyhub[/COLOR][CR]'
        txt += '  [COLOR gold]proxyranker[/COLOR][CR]'
        txt += '  [COLOR gold]xroxy[/COLOR][CR]'
        txt += '  [COLOR gold]socks[/COLOR][CR]'
        txt += '  [COLOR gold]squidproxyserver[/COLOR][CR]'

    if item.ampliada:
        if not config.get_setting('proxies_extended', default=False):
            platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Aún No está configurado en Ajustes[/COLOR][/B]' % color_adver)
            return

    platformtools.dialog_textviewer('Proveedores de proxies', txt)


def show_help_recommended(item):
    logger.info()

    txt = '[COLOR goldenrod][B]Proveedores habituales:[/B][/COLOR][CR]'

    txt += '  [COLOR yellow][B]All-providers[/COLOR][CR]'

    if config.get_setting('proxies_list', default=False):
        txt += '  [COLOR cyan][B]Lista-proxies.txt[/B][/COLOR][CR]'

    txt += '  [COLOR yellow][B]Mmpx12[/COLOR][CR]'
    txt += '  [COLOR yellow][B]Proxyscrape.com[/B][/COLOR][CR]'
    txt += '  [COLOR yellow][B]Us-proxy.org[/B][/COLOR][CR]'

    if config.get_setting('proxies_extended', default=False):
        txt += '[CR][COLOR yellowgreen][B]Lista Ampliada de proveedores:[/B][/COLOR][CR]'

        txt += '  [COLOR gold][B]Free-proxy-list.anon[/B][/COLOR][CR]'

    txt += '[CR][COLOR chocolate][B]Atención:[/B][/COLOR]'

    txt += '[CR][COLOR plum][B]  Si un Canal concreto NO obtuviera nigún proxy válido[CR]'
    txt += '  ó los proxies que se obtengan NO funcionan,[CR]'
    txt += '  pues hay que tener MUCHA Paciencia[CR]'
    txt += '  e ir probando uno a uno, los Proveedores de proxies, en[/COLOR][CR]'
    txt += '  [COLOR red]Configurar proxies a usar ...[/B][/COLOR][CR]'

    txt += '[CR][COLOR magenta][B]  Para esta situación recomendamos los proveedores habituales:[/B][/COLOR][CR]'
    txt += '[COLOR aquamarine][B]    Mertguvencli,  Roosterkid,  Shiftytr[/B][/COLOR][CR]'

    if config.get_setting('proxies_vias', default=False):
        txt += '[CR][COLOR dodgerblue][B]  Proveedores recomendados de la Lista Vias Alternativas:[/B][/COLOR][CR]'
        txt += '[COLOR aquamarine][B]    Ercindedeoglu,  Proxyscrape[/B][/COLOR][CR]'

    txt += '[CR][COLOR yellowgreen][B]  Ó bien prescindir/desactivar el canal.[/B][/COLOR]'

    platformtools.dialog_textviewer('Proveedores Recomendados de proxies', txt)

def show_help_providers2(item):
    logger.info()

    item.ampliada = True
    show_help_providers(item)


def show_help_yourlist(item):
    logger.info()

    txt = ' - [COLOR yellow][B]Cuestión Preliminar:[/B][/COLOR][CR]'

    txt += '    [COLOR darkcyan][B]No necesita efectuar ninguna acción especial al respecto,[CR]'
    txt += '    Porque, cada vez que haya una Revisión de esa Lista,[CR]'
    txt += '    ya viene integrada, dentro del correspondiente Fix ó Versión.[/B][/COLOR][CR]'

    txt += '[CR] - [COLOR yellow][B]Acceso al Foro:[/B][/COLOR][CR]'
    txt += '   ' + _foro + '[CR]'

    txt += '    [COLOR lime][B]Se recomienda su gestión, solo para Usuarios Avanzados.[/B][/COLOR][CR]'
    txt += '    En el Foro, podreís compartir vuestras Listas.[CR]'
    txt += '    Las listas deben revisarse y actualizarse con cierta peridiocidad.'

    txt += '[CR][CR] - [COLOR yellow][B]Requisitos:[/B][/COLOR][CR]'

    txt += '    Para gestionar una Lista Personalizada,[CR]'
    txt += '    Opcionalmente necesitará tener un [COLOR goldenrod][B]Programa Descompresor[/B][/COLOR] de archivos instalado en su equipo[CR]'
    txt += '    y así podrá obtener el fichero descomprimido [COLOR gold][B]Lista-proxies.txt[/B][/COLOR][CR][CR]'

    txt += '    [COLOR cyan][B]Si no obtiene el fichero Des-comprimido, durante el [/B][/COLOR][COLOR yellow][B]Procedimiento[/B][/COLOR][COLOR cyan][B], se le solicitará[CR]'
    txt += '    la ubicacion de [/B][/COLOR][COLOR violet][B]Lista-proxies.zip[/B][/COLOR][COLOR cyan][B], para efectuar su Des-compresión[/B][/COLOR][CR][CR]'

    txt += '    en la carpeta por defecto del Add-On [COLOR goldenrod][B].../kodi/userdata/addon_data/plugin.video.balandro/[/B][/COLOR][CR]'

    txt += '    [COLOR yellowgreen][B]opcionalmente puede ubicarlo allí, ó donde desee, mediante un explorador de archivos.[/B][/COLOR]'

    txt += '[CR][CR] - [COLOR yellow][B]Ajustes:[/B][/COLOR][CR]'

    txt += '    Activar su uso en los [COLOR goldenrod][B]Ajustes[/B][/COLOR] de Balandro, Categoría [COLOR red][B]Proxies[/B][/COLOR], Apartado [COLOR chartreuse][B]Lista Personalizada[/B][/COLOR]'

    txt += '[CR][CR] - [COLOR yellow][B]Procedimiento:[/B][/COLOR][CR]'
    txt += '    Descargar desde Adjuntos en el Foro [COLOR violet][B]Lista-proxies.zip[/B][/COLOR] y opcionalmente descomprimirlo donde le interese.[CR]'

    txt += '    Durante el proceso de obtención de Proxies, se solicitará, la ubicación del fichero[CR]'
    txt += '    [COLOR gold][B]Lista-proxies.txt[/B][/COLOR] ó [COLOR violet][B]Lista-proxies.zip[/B][/COLOR]'

    txt += '[CR][CR] - [COLOR yellow][B]Información:[/B][/COLOR][CR]'

    txt += '     Esta lista al parecer tiene mayor estabilidad y una caducidad mas longeva,[CR]'
    txt += '     es cuestión de ir probando, cuando no se obtengan proxies, por el método automático ó habitual.[CR]'

    txt += '[CR]     Si generaís vuestra lista personalizada, seguir la estructura de 1 proxy por línea,[CR]'
    txt += '     Ver la composición en el fichero adjunto, una vez descomprimido.'

    platformtools.dialog_textviewer('Información Gestión fichero Lista-Proxies.txt', txt)


def proxies_show_vias(item):
    logger.info()

    if not config.get_setting('proxies_vias', default=False):
         platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Aún No está configurado en Ajustes[/COLOR][/B]' % color_adver)
         return

    txt = '[COLOR goldenrod][B]Proveedores Vías Alternativas (si no se obtubieron suficientes proxies a analizar):[/B][/COLOR][CR]'

    txt += ' [COLOR cyan][B]    0 [COLOR yellow][B]Openproxy.space http[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B]    1 [COLOR yellow][B]Openproxy.space socks4[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B]    2 [COLOR yellow][B]Openproxy.space socks5[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B]    3 [COLOR yellow][B]Vpnoverview.com[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B]    4 [COLOR yellow][B]Proxydb.net http[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B]    5 [COLOR yellow][B]Proxydb.net https[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B]    6 [COLOR yellow][B]Proxydb.net socks4[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B]    7 [COLOR yellow][B]Proxydb.net socks5[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B]    8 [COLOR yellow][B]Netzwelt.de[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B]    9 [COLOR yellow][B]Proxy-list.download http[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 10 [COLOR yellow][B]Proxy-list.download https[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 11 [COLOR yellow][B]Proxy-list.download socks4[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 12 [COLOR yellow][B]Proxy-list.download socks5[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 13 [COLOR yellow][B]Freeproxy.world[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 14 [COLOR yellow][B]Freeproxy.world anonymity[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 15 [COLOR yellow][B]Hidemyna.me.en[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 16 [COLOR yellow][B]List.proxylistplus.com[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 17 [COLOR yellow][B]Proxyservers.pro[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 18 [COLOR yellow][B]TheSpeedX[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 19 [COLOR yellow][B]Proxyscan.io http[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 20 [COLOR yellow][B]Proxyscan.io all[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 21 [COLOR yellow][B]Openproxylist.xyz http[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 22 [COLOR yellow][B]Openproxylist.xyz socks4[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 23 [COLOR yellow][B]Openproxylist.xyz socks5[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 24 [COLOR yellow][B]Proxy-list.download v1 socks4[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 25 [COLOR yellow][B]Proxy-list.download v1 socks5[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 26 [COLOR yellow][B]Monosans[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 27 [COLOR yellow][B]Jjetkai[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 28 [COLOR yellow][B]Sunny9577[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 29 [COLOR yellow][B]Proxy4parsing[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 30 [COLOR yellow][B]Hendrikbgr[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 31 [COLOR yellow][B]Rdavydov http[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 32 [COLOR yellow][B]Aslisk[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 33 [COLOR yellow][B]Rdavydov socks4[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 34 [COLOR yellow][B]Hhookzof[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 35 [COLOR yellow][B]MmanuGMG[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 36 [COLOR yellow][B]Rdavydov socks5[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 37 [COLOR yellow][B]Lamt3012[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 38 [COLOR yellow][B]Proxyfly http[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 39 [COLOR yellow][B]Proxyfly socks4[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 40 [COLOR yellow][B]Proxyfly socks5[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 41 [COLOR yellow][B]ErcinDedeoglu http[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 42 [COLOR yellow][B]ErcinDedeoglu https[COLOR lime]  recomendado[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 43 [COLOR yellow][B]ErcinDedeoglu socks4[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 44 [COLOR yellow][B]ErcinDedeoglu socks5[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 45 [COLOR yellow][B]Proxifly https[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 46 [COLOR yellow][B]Proxycompass[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 47 [COLOR yellow][B]Proxybros[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 48 [COLOR yellow][B]Proxyscrape all[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 49 [COLOR yellow][B]Proxyscrape anonymous[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 50 [COLOR yellow][B]Proxyscrape elite[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 51 [COLOR yellow][B]Proxyscrape transparent[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 52 [COLOR yellow][B]Proxyscrape https[COLOR lime]  recomendado[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 53 [COLOR yellow][B]Markavale[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 54 [COLOR yellow][B]Proxyscan.io socks4[/B][/COLOR][CR]'
    txt += ' [COLOR cyan][B] 55 [COLOR yellow][B]Proxyscan.io socks5[/B][/COLOR]'

    platformtools.dialog_textviewer('Proveedores Vías Alternativas de proxies', txt)


def show_help_clean(item):
    logger.info()

    txt = '[COLOR moccasin][B]Análisis efectuado de la situación actual de su Instalación y Ejecución.[/B][/COLOR][CR][CR]'

    txt += '[COLOR yellowgreen][B]Para Procesar, dentro del [COLOR goldenrod][B]Add-On[/B][/COLOR], dirijase a [COLOR chartreuse][B]Ayuda[/B][/COLOR] [COLOR olivedrab][B]Limpiezas[/B][/COLOR][CR]'
    txt += '[COLOR cyan][B]Durante el proceso de cada una de las [/COLOR][COLOR yellow]Opciones[/COLOR][COLOR cyan], podrá Confirmar previamente cada [/COLOR][COLOR red]Eliminación[/B][/COLOR]'

    txt += '[CR][CR][COLOR powderblue][B]Media Center:[/B][/COLOR][CR]'

    path = translatePath(os.path.join('special://home/userdata', ''))

    file = 'advancedsettings.xml'
    file = path + file
    existe = filetools.exists(file)
    if existe: txt += 'Fichero [COLOR yellow][B]advancedsettings.xml[/B][/COLOR][CR]'

    file_favs = 'favourites.xml'
    file = path + file_favs
    existe = filetools.exists(file)

    if existe:
        txt_favs = ''

        try:
           with open(os.path.join(path, file_favs), 'r') as f: txt_favs=f.read(); f.close()
        except:
           try: txt_favs = open(os.path.join(path, file_favs), encoding="utf8").read()
           except: pass

        bloque = scrapertools.find_single_match(txt_favs, '<favourites>(.*?)</favourites>')

        matches = bloque.count('<favourite')

        if matches == 0: existe = False

    if existe: txt += 'Fichero [COLOR yellow][B]favourites.xml[/B][/COLOR][CR]'

    file = 'playercorefactory.xml'
    file = path + file
    existe = filetools.exists(file)
    if existe: txt += 'Fichero [COLOR yellow][B]playercorefactory.xml[/B][/COLOR][CR]'

    presentar = False

    path_cache = translatePath(os.path.join('special://temp/archive_cache', ''))
    existe_cache = filetools.exists(path_cache)

    caches = []
    if existe_cache: caches = os.listdir(path_cache)

    if caches: presentar = True

    if presentar: txt += 'Archivos en la [COLOR yellow][B]Caché[/B][/COLOR][CR]'

    path_thumbs = translatePath(os.path.join('special://home/userdata/Thumbnails', ''))
    existe_thumbs = filetools.exists(path_thumbs)

    if existe_thumbs: txt += 'Archivos en [COLOR yellow][B]Thumbnails[/B][/COLOR][CR]'

    presentar = False

    path_packages = translatePath(os.path.join('special://home/addons/packages', ''))
    existe_packages = filetools.exists(path_packages)

    packages = []
    if existe_packages: packages = os.listdir(path_packages)

    path_temp = translatePath(os.path.join('special://home/addons/temp', ''))
    existe_temp = filetools.exists(path_temp)

    temps = []
    if existe_temp: temps = os.listdir(path_temp)

    if packages: presentar = True
    elif temps: presentar = True

    if presentar:
        txt += '[CR][CR][COLOR powderblue][B]Add-Ons:[/B][/COLOR][CR]'

        if packages:  txt += 'Archivos en [COLOR yellow][B]Packages[/B][/COLOR][CR]'

        if temps: txt += 'Archivos en [COLOR yellow][B]Temp[/B][/COLOR][CR]'


    txt += '[CR][CR][COLOR powderblue][B]Sistema:[/B][/COLOR][CR]'

    path = os.path.join(config.get_runtime_path(), 'last_fix.json')
    existe = filetools.exists(path)
    if existe: txt += 'Fichero [COLOR yellow][B]last_fix.json[/B][/COLOR][CR]'

    path = os.path.join(config.get_data_path(), 'Lista-proxies.txt')
    existe = filetools.exists(path)
    if existe: txt += 'Fichero [COLOR yellow][B]Lista-Proxies.txt[/B][/COLOR][CR]'

    path = os.path.join(config.get_data_path(), 'cookies.dat')
    existe = filetools.exists(path)
    if existe: txt += 'Fichero [COLOR yellow][B]cookies.dat[/B][/COLOR][CR]'

    path = os.path.join(config.get_data_path(), 'cache')
    existe = filetools.exists(path)
    if existe: txt += 'Carpeta [COLOR yellow][B]Caché[/B][/COLOR][CR]'

    path = filetools.join(config.get_data_path(), 'tracking_dbs')
    existe = filetools.exists(path)
    if existe: txt += 'Contenido [COLOR wheat][B]Preferidos[/B][/COLOR][CR]'

    downloadpath = config.get_setting('downloadpath', default='')

    if downloadpath: path = downloadpath
    else: path = filetools.join(config.get_data_path(), 'downloads')

    existe = filetools.exists(path)
    if existe: txt += 'Contenido [COLOR seagreen][B]Descargas[/B][/COLOR][CR]'

    path = filetools.join(config.get_data_path(), 'tmdb.sqlite-journal')
    existe = filetools.exists(path)
    if existe: txt += 'Fichero [COLOR yellow][B]tmdb.sqlite-journal[/B][/COLOR][CR]'

    path = filetools.join(config.get_data_path(), 'tmdb.sqlite')
    existe = filetools.exists(path)
    if existe: txt += 'Fichero [COLOR yellow][B]tmdb.sqlite[/B][/COLOR][CR]'

    presentar = False

    if os.path.exists(os.path.join(config.get_data_path(), 'servers_todo.log')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'qualities_todo.log')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'proxies.log')): presentar = True

    if presentar:
        txt += '[CR][CR][COLOR powderblue][B]Logs:[/B][/COLOR][CR]'

        if os.path.exists(os.path.join(config.get_data_path(), 'servers_todo.log')): txt += 'Fichero [COLOR yellow][B]servers_todo.log[/B][/COLOR][CR]'
        if os.path.exists(os.path.join(config.get_data_path(), 'qualities_todo.log')): txt += 'Fichero [COLOR yellow][B]qualities_todo.log[/B][/COLOR][CR]'
        if os.path.exists(os.path.join(config.get_data_path(), 'proxies.log')): txt += 'Fichero [COLOR yellow][B]proxies.log[/B][/COLOR][CR]'

    presentar = False

    if os.path.exists(os.path.join(config.get_data_path(), 'info_channels.csv')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'temp.torrent')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'm3u8hls.m3u8')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'blenditall.m3u8')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'test_logs')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'temp_updates.zip')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'tempfile_mkdtemp')): presentar = True

    if presentar:
        txt += '[CR][CR][COLOR powderblue][B]Temporales:[/B][/COLOR][CR]'

        if os.path.exists(os.path.join(config.get_data_path(), 'info_channels.csv')): txt += 'Fichero [COLOR yellow][B]info_channels.csv[/B][/COLOR][CR]'
        if os.path.exists(os.path.join(config.get_data_path(), 'temp.torrent')): txt += 'Fichero [COLOR yellow][B]temp.torrent[/B][/COLOR][CR]'
        if os.path.exists(os.path.join(config.get_data_path(), 'm3u8hls.m3u8')): txt += 'Fichero [COLOR yellow][B]m3u8hls.m3u8[/B][/COLOR][CR]'
        if os.path.exists(os.path.join(config.get_data_path(), 'blenditall.m3u8')): txt += 'Fichero [COLOR yellow][B]blenditall.m3u8[/B][/COLOR][CR]'
        if os.path.exists(os.path.join(config.get_data_path(), 'test_logs')): txt += 'Fichero [COLOR yellow][B]test_logs[/B][/COLOR][CR]'
        if os.path.exists(os.path.join(config.get_data_path(), 'temp_updates.zip')): txt += 'Archivo [COLOR yellow][B]temp_updates.zip[/B][/COLOR][CR]'
        if os.path.exists(os.path.join(config.get_data_path(), 'tempfile_mkdtemp')): txt += 'Archivo [COLOR yellow][B]tempfile_mkdtemp[/B][/COLOR][CR]'

    txt = txt.replace('[CR][CR][CR]', '[CR][CR]')

    platformtools.dialog_textviewer('Información Limpiezas (Personalizada)', txt)


def show_help_fixes(item):
    logger.info()

    txt = '[CR] Son correcciones del Add-On:[CR]'

    txt += ' - [COLOR yellow]Por bugs (errores)[/COLOR][CR]'

    txt += ' - [COLOR yellow]Por cambios menores (nuevos dominios, estructuras, etc.)[/COLOR][CR]'

    txt += '[CR] Y que no tienen la embergadura suficiente como para confeccionar y publicar una nueva versión.[CR]'

    txt += '[CR][COLOR gold] Los Fixes siempre se actualizan automáticamente al iniciar sesión en su Media Center.[/COLOR]'

    platformtools.dialog_textviewer('Información ¿ Qué son los fixes ?', txt)


def show_help_recaptcha(item):
    logger.info()

    txt = 'Son avisos de porqué no se puede reproducir ese enlace en cuestión.[CR]'

    txt += '[CR] Para reproducir ese enlace el servidor exige resolver que no eres un [COLOR gold]Boot[/COLOR], para ello'

    txt += '[CR] presenta un proceso para [COLOR yellow]seleccionar imágenes[/COLOR] (bicicletas, barcos, semáforos, etc.)'

    txt += '[CR][CR]Dada su dificultad [COLOR gold]NO[/COLOR] está contemplado en el Add-On esta situación.'

    platformtools.dialog_textviewer('Información ¿ Qué significa Requiere verificación [COLOR red]reCAPTCHA[/COLOR] ?', txt)


def show_help_acortador(item):
    logger.info()

    txt = 'Son avisos de porqué no se puede reproducir ese enlace en cuestión.[CR]'

    txt += '[CR] Son redireccionamientos, que hacen que un Link concreto, efectue accesos a otros enlaces diferentes.'

    txt += '[CR] Para reproducir ese enlace el servidor exige resolver y esperar Todas esas [COLOR gold]Redirecciones[/COLOR], para ello'

    txt += '[CR] presenta un proceso para [COLOR yellow]seleccionar diferentes Webs[/COLOR] (publicidad, esperas, etc.)'

    txt += '[CR][CR]Dada su dificultad [COLOR gold]NO[/COLOR] está contemplado en el Add-On esta situación.'

    platformtools.dialog_textviewer('Información ¿ Qué significa Tiene [COLOR plum]Acortador[/COLOR] del enlace ?', txt)


def show_version(item):
    logger.info()

    txt = ''

    try:
       with open(os.path.join(config.get_runtime_path(), 'version.txt'), 'r') as f: txt=f.read(); f.close()
    except:
       try: txt = open(os.path.join(config.get_runtime_path(), 'version.txt'), encoding="utf8").read()
       except: pass

    if txt: platformtools.dialog_textviewer('Información versión', txt)


def show_changelog(item):
    logger.info()

    txt = ''

    try:
       with open(os.path.join(config.get_runtime_path(), 'changelog.txt'), 'r') as f: txt=f.read(); f.close()
    except:
       try: txt = open(os.path.join(config.get_runtime_path(), 'changelog.txt'), encoding="utf8").read()
       except: pass

    if txt: platformtools.dialog_textviewer('Historial de versiones', txt)


def show_dev_notes(item):
    logger.info()

    txt = ''

    try:
       with open(os.path.join(config.get_runtime_path(), 'dev-notes.txt'), 'r') as f: txt=f.read(); f.close()
    except:
       try: txt = open(os.path.join(config.get_runtime_path(), 'dev-notes.txt'), encoding="utf8").read()
       except: pass

    if txt: platformtools.dialog_textviewer('Notas para developers', txt)


def show_todo_log(item):
    logger.info()

    path = os.path.join(config.get_data_path(), item.todo)

    existe = filetools.exists(path)

    if not existe:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Aún No hay el fichero Log[/COLOR][/B]' % color_alert)
        return

    txt = ''

    try:
        with open(path, 'r') as f: txt=f.read(); f.close()
    except:
        try: txt = open(path, encoding="utf8").read()
        except: pass

    if txt:
        platformtools.dialog_textviewer('Fichero Log ' + item.todo, txt)
    else:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Sin Información[/COLOR][/B]' % color_alert)


def show_report(item):
    logger.info()

    loglevel = config.get_setting('debug', 0)
    if not loglevel >= 2:
        config.set_setting('debug', 2)

    platformtools.dialog_ok(config.__addon_name + ' - Reportes', '[COLOR yellow]Por favor, reproduzca el [B]Problema y Regrese[/B] a esta sección.[/COLOR]', 'para obtener [COLOR cyan][B]una Copia del Fichero LOG[/B][/COLOR] de su Media Center y poder [COLOR goldenrod][B]Remitirnoslo[/B][/COLOR] a la mayor brevedad posible.')


def show_log(item):
    logger.info()

    loglevel = config.get_setting('debug', 0)
    if not loglevel >= 2:
        if not platformtools.dialog_yesno(config.__addon_name, 'El nivel actual de información del fichero LOG de su Media Center NO esta Ajustado al máximo. ¿ Desea no obstante visualizarlo ?'): 
            return

    path = translatePath(os.path.join('special://logpath/', ''))

    file_log = 'kodi.log'

    file = path + file_log

    existe = filetools.exists(file)

    if existe == False:
        files = filetools.listdir(path)
        for file_log in files:
            if file_log.endswith('.log') == True or file_log.endswith('.LOG') == True:
                file = path + file_log
                existe = filetools.exists(file)
                break

    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No se localiza su fichero Log[/COLOR][/B]' % color_alert)
        platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]Media Center NO Oficial[/B][/COLOR]', '[COLOR red][B]No se ha localizado su fichero Log[/B][/COLOR]', '[COLOR yellowgreen][B]Localize su fichero Log, mediante un Navegador de Archivos en su Media Center.[/B][/COLOR]')
        return

    size = filetools.getsize(file)
    if size > 999999: platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Cargando fichero log[/COLOR][/B]' % color_infor)

    txt = ''

    try:
        with open(os.path.join(path, file_log), 'r') as f: txt=f.read(); f.close()
    except:
        try: txt = open(os.path.join(path, file_log), encoding="utf8").read()
        except: pass

    if config.get_setting('developer_mode', default=False):
        txt = txt.replace('Balandro.', '[COLOR yellow][B]Balandro[/B][/COLOR].')
        txt = txt.replace('Balandro ', '[COLOR yellow][B]Balandro[/B][/COLOR] ')
        txt = txt.replace('balandro.', '[COLOR yellow][B]Balandro[/B][/COLOR].')
        txt = txt.replace('balandro ', '[COLOR yellow][B]Balandro[/B][/COLOR] ')

    if txt: platformtools.dialog_textviewer('Fichero LOG de su Media Center', txt)


def copy_log(item):
    logger.info()

    loglevel = config.get_setting('debug', 0)
    if not loglevel >= 2:
        if not platformtools.dialog_yesno(config.__addon_name, 'El nivel actual de información del fichero LOG de su Media Center NO está Ajustado al máximo. [B][COLOR %s]¿ Desea no obstante obtener una Copia ?[/B][/COLOR]' % color_infor):
            return

    path = translatePath(os.path.join('special://logpath/', ''))

    file_log = 'kodi.log'

    file = path + file_log

    existe = filetools.exists(file)

    if existe == False:
        files = filetools.listdir(path)
        for file_log in files:
            if file_log.endswith('.log') == True or file_log.endswith('.LOG') == True:
                file = path + file_log
                existe = filetools.exists(file)
                break

    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No se localiza su fichero Log[/COLOR][/B]' % color_alert)
        platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]Media Center NO Oficial[/B][/COLOR]', '[COLOR red][B]No se ha localizado su fichero Log[/B][/COLOR]', '[COLOR yellowgreen][B]Localize su fichero Log, mediante un Navegador de Archivos en su Media Center.[/B][/COLOR]')
        return

    destino_path = xbmcgui.Dialog().browseSingle(3, 'Seleccionar carpeta dónde copiar', 'files', '', False, False, '')
    if not destino_path: return

    origen = os.path.join(path, file_log)
    destino = filetools.join(destino_path, file_log)
    if not filetools.copy(origen, destino, silent=False):
        platformtools.dialog_ok(config.__addon_name, 'Error, no se ha podido copiar el fichero Log!', origen, destino)
        return

    platformtools.dialog_notification('Fichero Log copiado', file_log)

    time.sleep(0.5)

    loglevel = config.get_setting('debug', 0)
    if not loglevel == 0:
        if not platformtools.dialog_yesno(config.__addon_name, 'El Ajuste actual del nivel de información del fichero LOG de su Media Center REDUCE el rendimiento de su equipo. [B][COLOR %s]¿ Desea mantener ese Nivel de información ?[/B][/COLOR]' % color_avis):
            config.set_setting('debug', '0')


def test_log(item):
    logger.info()

    path = translatePath(os.path.join('special://logpath/', ''))

    file_log = 'kodi.log'

    file = path + file_log

    existe = filetools.exists(file)

    if existe == False:
        files = filetools.listdir(path)
        for file_log in files:
            if file_log.endswith('.log') == True or file_log.endswith('.LOG') == True:
                file = path + file_log
                existe = filetools.exists(file)
                break

    if existe: return file_log

    return '[COLOR red][B]Fichero Log NO localizado[/B][/COLOR]'


def show_advs(item):
    logger.info()

    path = translatePath(os.path.join('special://home/userdata', ''))

    file_advs = 'advancedsettings.xml'
    file = path + file_advs
    existe = filetools.exists(file)

    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No hay fichero Advanced Settings[/COLOR][/B]' % color_infor)
        return

    txt = ''

    try:
       with open(os.path.join(path, file_advs), 'r') as f: txt=f.read(); f.close()
    except:
       try: txt = open(os.path.join(path, file_advs), encoding="utf8").read()
       except: pass

    if txt: platformtools.dialog_textviewer('Fichero Advanced Settings de su Media Center', txt)


def show_favs(item):
    logger.info()

    path = translatePath(os.path.join('special://home/userdata', ''))

    file_favs = 'favourites.xml'
    file = path + file_favs
    existe = filetools.exists(file)

    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No hay fichero Favourites Settings[/COLOR][/B]' % color_infor)
        return

    txt = ''

    try:
       with open(os.path.join(path, file_favs), 'r') as f: txt=f.read(); f.close()
    except:
       try: txt = open(os.path.join(path, file_favs), encoding="utf8").read()
       except: pass

    if existe:
        txt_favs = ''

        try:
           with open(os.path.join(path, file_favs), 'r') as f: txt_favs=f.read(); f.close()
        except:
           try: txt_favs = open(os.path.join(path, file_favs), encoding="utf8").read()
           except: pass

        bloque = scrapertools.find_single_match(txt_favs, '<favourites>(.*?)</favourites>')

        matches = bloque.count('<favourite')

        if matches == 0: existe = False

    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Favourites Settings Sin Datos[/COLOR][/B]' % color_exec)
        return

    if txt: platformtools.dialog_textviewer('Fichero Favourites Settings de su Media Center', txt)


def show_pcfs(item):
    logger.info()

    path = translatePath(os.path.join('special://home/userdata', ''))

    file_pcfs = 'playercorefactory.xml'

    file = path + file_pcfs

    existe = filetools.exists(file)

    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No hay fichero PlayerCoreFactory Settings[/COLOR][/B]' % color_infor)
        return

    txt = ''

    try:
       with open(os.path.join(path, file_pcfs), 'r') as f: txt=f.read(); f.close()
    except:
       try: txt = open(os.path.join(path, file_pcfs), encoding="utf8").read()
       except: pass

    if txt: platformtools.dialog_textviewer('Fichero PlayerCoreFactory Settings de su Media Center', txt)


def show_yourlist(item):
    logger.info()

    path = os.path.join(config.get_data_path(), 'Lista-proxies.txt')

    existe = filetools.exists(path)

    if not existe:
        platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B].../addon_data.../plugin.video.balandro[/B][/COLOR]', 'Aún No hay fichero Lista de Proxies', '[B][COLOR %s]Lista-proxies.txt[/COLOR][/B]' % color_alert)
        return

    txt = ''

    try:
        with open(path, 'r') as f: txt=f.read(); f.close()
    except:
        try: txt = open(path, encoding="utf8").read()
        except: pass

    if txt:
        platformtools.dialog_textviewer('Fichero Lista de Proxies', txt)
    else:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Sin Información[/COLOR][/B]' % color_alert)


def show_help_adults(item):
    logger.info()

    txt = ''

    if config.get_setting('adults_password', default=''):
        txt += '[COLOR yellow][B]Tiene informado un PIN control Parental[/B][/COLOR][CR]'
        txt += '[COLOR gold][B]Solo deberá informarlo una ÚNICA vez hasta que Abandone el Menú Principal del Add-On[/B][/COLOR][CR][CR]'

    else: txt += '[COLOR red][B]NO Tiene informado un PIN control Parental[/B][/COLOR][CR][CR]'

    txt += '*) Las webs podrían, en algún caso, publicar Vídeos con contenido [COLOR cyan][B]No Apto[/B][/COLOR] para menores.[CR]'
    txt += '   Balandro cuenta con un apartado en sus Ajustes exclusivo para el [COLOR gold][B]Control Parental[/B][/COLOR].[CR]'
    txt += '   (por defecto este apartado está [COLOR goldenrod][B]Habilitado[/B])[/COLOR][CR]'

    txt += '[CR]*) [COLOR yellowgreen][B]Pero no se puede garantizar con total seguridad,'
    txt += '[CR]    que todo el material de este tipo se filtre correctamente en determinadas ocasiones.[/B][/COLOR][CR]'

    txt += '[CR]*) También puede desactivar esta opción en los Ajustes, [COLOR cyan][B]categorías[/COLOR] [COLOR yellow]Menú y Parental[/B][/COLOR]'

    platformtools.dialog_textviewer('Información Control Parental', txt)


def show_help_domains(item):
    logger.info()

    txt = '[B][COLOR cyan]Cuestión Preliminar:[/B][/COLOR][CR]'

    if item.category:
        if item.category == 'Balandro':
            txt += '  Ciertas Operadoras pueden [COLOR yellowgreen][B]Bloquear[/B][/COLOR] el acceso a un Canal.[CR]'
        else:
            txt += '  Ciertas Operadoras pueden [COLOR yellowgreen][B]Bloquear[/B][/COLOR] el acceso a este Canal.[CR]'
    else:
        txt += '  Ciertas Operadoras pueden [COLOR yellowgreen][B]Bloquear[/B][/COLOR] el acceso a un Canal.[CR]'

    txt += '  Incluso una misma Operadora puede [COLOR yellowgreen][B]Bloquear[/B][/COLOR] en una [COLOR violet][B]Zona Geográfica [/B][/COLOR]concreta[CR]'
    txt += '  y por el contrario en [COLOR violet][B]Otras Zonas Geográficas No[/B][/COLOR].[CR]'

    if item.category:
        if not item.category == 'Balandro':
            txt += '[CR]  [B][COLOR yellow]Este Canal Habitualmente NO Requiere[/COLOR] [COLOR red]Proxies[/COLOR][/B][CR]'

        if item.category == 'DonTorrents':
            if config.get_setting('channel_dontorrents_proxies', default=''):
	            txt += '[CR]  [B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

            txt += '[CR][COLOR chocolate][B]Para conocer el Dominio Vigente:[/COLOR][/B][CR]'
            txt += '  Acceda a través de un Navegador de Internet a [B][COLOR greenyellow]donproxies.com[/B][/COLOR][CR]'
            txt += '  ó bien acceda a su Telegram [B][COLOR greenyellow]t.me/DonTorrent[/COLOR][/B][CR][CR]'

        elif item.category == 'HdFull':
            if config.get_setting('channel_hdfull_proxies', default=''):
	            txt += '[CR]  [B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'
 
            txt += '[CR][COLOR chocolate][B]Para conocer los Dominios Vigentes:[/COLOR][/B][CR]'
            txt += '  Acceda a través de un Navegador de Internet a [B][COLOR greenyellow]dominioshdfull.com[/COLOR][/B]'

            txt += '  [CR][CR]Dispone de varios Dominios en [B][COLOR yellowgreen]Configurar dominio a usar[/B][/COLOR] que son [B][COLOR goldenrod]Clones[/COLOR][/B]:[CR]'
            txt += '   [B][COLOR yellow]Puede Asociar Cualquiera[/COLOR][/B] de ellos,[CR]'
            txt += '   [B][COLOR green]Independientemente del que usó para Registrar su Cuenta.[/COLOR][/B][CR][CR]'

        elif item.category == 'PlayDede':
            if config.get_setting('channel_playdede_proxies', default=''):
	            txt += '[CR]  [B] [COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR]'

            txt += '[CR][COLOR chocolate][B]Para conocer el Dominio Vigente:[/COLOR][/B][CR]'
            txt += '  Acceda a través de un Navegador de Internet a [B][COLOR greenyellow]privacidad.me/@playdede[/COLOR][/B][CR]'
            txt += '  también puede acceder a [B][COLOR greenyellow] entrarplaydede.com[/COLOR][/B][CR]'
            txt += '  ó bien acceda a su X [B][COLOR greenyellow] x.com/playdedesocial[/COLOR][/B][CR][CR]'

        else:
            if config.get_setting('channel_' + item.category.lower() + '_proxies', default=''):
	            txt += '[CR]  [B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR][CR]'
            else:
                txt += '[CR]'

    if not item.category: txt += '[CR]'

    txt += 'Determinadas webs Cambian de Dominio y es necesario modificarlo para permitir su acceso:'

    txt += '[CR][CR]*) Desde otro equipo acceda a la web a través de un Navegador de Internet para ver el Nuevo Dominio.'
    txt += '[CR]    Si desconoce el Dominio actual de la web, mediante un Navegador de Internet deberá localizarlo.'
    txt += '[CR]    Imprescindible en este caso, tomar Nota del [B][COLOR gold]Nuevo Dominio[/COLOR][/B] para el Canal.'

    txt += '[CR][CR]*) También lo puede obtener, efectuando[CR]'

    if not item.ctas:
        txt += '    el [B][COLOR gold]Test Web del Canal[/COLOR][/B][CR]'
        txt += '    ver los datos [B][COLOR yellow]Host/Nuevo[/COLOR][/B] en la información de Test.'
    else:
        txt += '    la [B][COLOR darkgoldenrod]Diágnosis Acceso al Canal[/B][/COLOR] ó [COLOR darkgoldenrod][B]Dominio Actual[/COLOR][/B][CR]'

    if item.category:
        datos = channeltools.get_channel_parameters(item.category.lower())
        if datos['active']:
            if 'current' in datos['clusters']:
                txt += '[CR][CR]*) Además, al efectuar en [COLOR goldenrod][B]Acciones[/COLOR] [COLOR plum](si no hay resultados)[/B][/COLOR][B]:'
                txt += '[CR]    [B][COLOR chocolate]Comprobar último dominio vigente[/COLOR][/B]'
                txt += '[CR]    puede [B][COLOR cyan]Obtener y Asignar Automáticamente[/B][/COLOR] como Propuesta el'
                txt += '[CR]    [B][COLOR yellow]Nuevo Dominio Permanente/Temporal[/COLOR][/B]'
                txt += '[CR]    ó bien Informarlo [B][COLOR gold]Manualmente[/B][/COLOR].'

    if not item.ctas:
        txt += '[CR][CR][B][COLOR darkorange]Atención:[/COLOR][/B][CR]'

        txt += '  Si el acceso al Dominio, a través de un Navegador de Internet avisase con[CR]'
        txt += '  [COLOR orange][B]Verificando ...[/COLOR] [COLOR orangered]CLOUDFLARE[/B][/COLOR][CR]'
        txt += '  necesitará obligatoriamente usar [COLOR red][B]Proxies[/B][/COLOR] en el canal.'

    platformtools.dialog_textviewer('Gestión Dominios ' + item.category, txt)


def show_help_prales(item):
    logger.info()

    txt = ''

    if item.pral:
        txt += '[B][COLOR gold]Canal Principal del Clon [COLOR yellowgreen]' + item.category + '[/COLOR]:[/B][CR]'

        if item.category == 'Cuevana2': txt += '[B][COLOR yellow]Cuevana2Esp[/COLOR][/B]'

        elif item.category == 'DivxATope' or item.category == 'DonTorrentsIn' or item.category == 'EliteDivx' or item.category == 'LilaTorrent' or item.category == 'MejorTorrentApp' or item.category == 'NaranjaTorrent' or item.category == 'ReinvenTorrent' or item.category == 'RojoTorrent' or item.category == 'TomaDivx' or item.category == 'TodoTorrents' or item.category == 'VerdeTorrent': txt += '[B][COLOR yellow]DonTorrents[/COLOR][/B]'

        elif item.category == 'DPeliculas': txt += '[B][COLOR yellow]DeTodo[/COLOR][/B]'

        elif item.category == 'EliteTorrentNz': txt += '[B][COLOR yellow]EliteTorrent[/COLOR][/B]'

        elif item.category == 'Gnula24H' or item.category == 'Series24' or item.category == 'SeriesPlus': txt += '[B][COLOR yellow]Gnula24[/COLOR][/B]'

        elif item.category == 'OnlineTv' or item.category == 'SeriesEs' or item.category == 'SeriesOnline' or item.category == 'Star' or item.category == 'VerFlix': txt += '[B][COLOR yellow]VerOnline[/COLOR][/B]'

        elif item.category == 'PelisPediaIs' or item.category == 'SeriesMetroN': txt += '[B][COLOR yellow]HomeCine[/COLOR][/B]'

        elif item.category == 'TorrenFlix': txt += '[B][COLOR yellow]ZonaPelis[/COLOR][/B]'

        elif item.category == 'VerSeries': txt += '[B][COLOR yellow]JoinClub[/COLOR][/B]'

    else:

        txt += '[B][COLOR gold]Clones del Canal [COLOR yellowgreen]' + item.category + '[/COLOR]:[/B][CR]'

        if item.category == 'Cuevana2Esp':
            datos = channeltools.get_channel_parameters(item.category.lower())
            if datos['active']:
                if config.get_setting('channel_cuevana2_proxies', default=''):
	                txt += '[CR]  [B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR][CR]'

                datos = channeltools.get_channel_parameters('cuevana2')
                if datos['active']: txt += '   [B][COLOR yellow]Cuevana2[/COLOR][/B][CR]'

        elif item.category == 'DonTorrents':
            datos = channeltools.get_channel_parameters(item.category.lower())
            if datos['active']:
                if config.get_setting('channel_dontorrents_proxies', default=''):
	                txt += '[CR]  [B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR][CR]'

                datos = channeltools.get_channel_parameters('divxatope')
                if datos['active']: txt += '   [B][COLOR yellow]DivxATope[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('dontorrentsin')
                if datos['active']: txt += '   [B][COLOR yellow]DonTorrentsIn[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('elitedivx')
                if datos['active']: txt += '   [B][COLOR yellow]EliteDivx[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('lilatorrent')
                if datos['active']: txt += '   [B][COLOR yellow]LilaTorrent[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('mejortorrentapp')
                if datos['active']: txt += '   [B][COLOR yellow]MejorTorrentApp[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('naranjatorrent')
                if datos['active']: txt += '   [B][COLOR yellow]NaranjaTorrent[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('reinventorrent')
                if datos['active']: txt += '   [B][COLOR yellow]ReinvenTorrent[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('rojotorrent')
                if datos['active']: txt += '   [B][COLOR yellow]RojoTorrent[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('tomadivx')
                if datos['active']: txt += '   [B][COLOR yellow]TomaDivx[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('todotorrents')
                if datos['active']: txt += '   [B][COLOR yellow]TodoTorrents[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('verdetorrent')
                if datos['active']: txt += '   [B][COLOR yellow]VerdeTorrent[/COLOR][/B][CR]'

        elif item.category == 'EliteTorrent':
            datos = channeltools.get_channel_parameters(item.category.lower())
            if datos['active']:
                datos = channeltools.get_channel_parameters('elitetorrentnz')
                if datos['active']: txt += '   [B][COLOR yellow]EliteTorrentNz[/COLOR][/B][CR]'

        elif item.category == 'Gnula24':
            datos = channeltools.get_channel_parameters(item.category.lower())
            if datos['active']:
                if config.get_setting('channel_gnula24_proxies', default=''):
	                txt += '[CR]  [B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR][CR]'

                datos = channeltools.get_channel_parameters('gnula24h')
                if datos['active']: txt += '   [B][COLOR yellow]Gnula24H[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('series24')
                if datos['active']: txt += '   [B][COLOR yellow]Series24[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('seriesplus')
                if datos['active']: txt += '   [B][COLOR yellow]SeriesPlus[/COLOR][/B][CR]'

        elif item.category == 'HomeCine':
            datos = channeltools.get_channel_parameters(item.category.lower())
            if datos['active']:
                if config.get_setting('channel_homecine_proxies', default=''):
	                 txt += '[CR]  [B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR][CR]'

                datos = channeltools.get_channel_parameters('pelispediais')
                if datos['active']: txt += '   [B][COLOR yellow]PelisPediaIs[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('seriesmetron')
                if datos['active']: txt += '   [B][COLOR yellow]SeriesMetroN[/COLOR][/B][CR]'

        elif item.category == 'JoinClub':
            datos = channeltools.get_channel_parameters(item.category.lower())
            if datos['active']:
                if config.get_setting('channel_joinclub_proxies', default=''):
	                txt += '[CR]  [B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR][CR]'

                datos = channeltools.get_channel_parameters('verseries')
                if datos['active']: txt += '   [B][COLOR yellow]VerSeries[/COLOR][/B][CR]'

        elif item.category == 'VerOnline':
            datos = channeltools.get_channel_parameters(item.category.lower())
            if datos['active']:
                if config.get_setting('channel_veronline_proxies', default=''):
	                txt += '[CR]  [B][COLOR cyan]Actualmente Tiene[/COLOR] [COLOR red]Proxies Configurados[/COLOR][/B][CR][CR]'

                datos = channeltools.get_channel_parameters('onlinetv')
                if datos['active']: txt += '   [B][COLOR yellow]OnlineTv[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('serieses')
                if datos['active']: txt += '   [B][COLOR yellow]SeriesEs[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('seriesonline')
                if datos['active']: txt += '   [B][COLOR yellow]SeriesOnline[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('star')
                if datos['active']: txt += '   [B][COLOR yellow]Star[/COLOR][/B][CR]'

                datos = channeltools.get_channel_parameters('verflix')
                if datos['active']: txt += '   [B][COLOR yellow]Verflix[/COLOR][/B][CR]'

        elif item.category == 'ZonaPelis':
            datos = channeltools.get_channel_parameters(item.category.lower())
            if datos['active']:
                datos = channeltools.get_channel_parameters('torrenflix')
                if datos['active']: txt += '   [B][COLOR yellow]TorrenFlix[/COLOR][/B][CR]'

    if item.pral:
        if not txt:
           platformtools.dialog_notification(config.__addon_name + ' ' + item.category, '[B][COLOR %s]Sin canal Principal Activo[/B][/COLOR]' % color_adver)
           return

        platformtools.dialog_textviewer(item.category + ' Cual es su Canal Principal', txt)

    else:
        if not txt:
           platformtools.dialog_notification(config.__addon_name + ' ' + item.category, '[B][COLOR %s]Sin Clones Activos[/B][/COLOR]' % color_adver)
           return

        platformtools.dialog_textviewer(item.category + ' Cuales son sus Clones', txt)


def show_help_torrents(item):
    logger.info()

    txt = '*) A través de un [COLOR gold]Navegador de Internet[/COLOR] localize e instale al menos uno de los Add-Ons de la lista que más se adapte a'
    txt += '  sus necesidades y que sea a su vez compatible con su Media Center.'

    txt += '[CR][CR]*) Add-Ons:[CR]'
    txt += '    - [COLOR yellow][B]plugin.video.elementum[/COLOR]  [COLOR limegreen]Recomendado[/B][/COLOR][CR]'
    txt += '    - [COLOR yellow][B]plugin.video.pulsar[/COLOR]   [COLOR red]Obsoleto[/B][/COLOR][CR]'
    txt += '    - [COLOR yellow][B]plugin.video.quasar[/COLOR]  [COLOR red]Obsoleto[/B][/COLOR][CR]'
    txt += '    - [COLOR yellow][B]plugin.video.stream[/COLOR]  [COLOR red]Obsoleto[/B][/COLOR][CR]'
    txt += '    - [COLOR yellow][B]plugin.video.torrenter[/B][/COLOR][CR]'
    txt += '    - [COLOR yellow][B]plugin.video.torrentin[/B][/COLOR][CR]'
    txt += '    - [COLOR yellow][B]plugin.video.torrest[/B][/COLOR][CR]'
    txt += '    - [COLOR yellow][B]plugin.video.xbmctorrent[/COLOR]  [COLOR red]Obsoleto[/B][/COLOR]'

    txt += '[CR][CR]*) Para [COLOR gold][B]Elementum[/B][/COLOR]:[CR]'

    txt += '     Puede acceder a su web oficial en [COLOR chartreuse][B]elementum.surge.sh[/B][/COLOR][CR]'

    txt += '[CR]     Es recomendable instalar el correspondiente [COLOR limegreen][B]Repositorio[/B][/COLOR] para recibir [COLOR yellow][B]Actualizaciones[/B][/COLOR]:[CR]'

    if not PY3:
        txt += '        [COLOR goldenrod][B]repository.elementum[/B][/COLOR]'
    else:
        txt += '        [COLOR goldenrod][B]repository.elementumorg[/B][/COLOR]'

    txt += '[CR][CR]     Puede obtener estos [COLOR limegreen][B]Repositorios[/B][/COLOR] desde [COLOR chartreuse][B]Nuestra Fuente[/B][/COLOR], carpeta [COLOR gold][B]Scripts[/B][/COLOR].[CR]'
    txt += '        Fuente  [COLOR darkorange][B]repobal.github.io/base/[/B][/COLOR][CR]'

    txt += '        Scripts  [COLOR mediumaquamarine][B]repobal.github.io/base/scripts/[/B][/COLOR][CR]'

    if not PY3:
        txt += '[CR]         - [COLOR lightblue][B]Carpeta Kodi18:[/COLOR][COLOR gold] Otros repositorios y plugins [/COLOR][COLOR lightblue] hasta 18.x[/B][/COLOR][CR]'
        txt += '            - [COLOR goldenrod][B] repository.elementum [/B][/COLOR][CR]'
    else:
        txt += '[CR]         - [COLOR lightblue][B]Carpeta Kodi19:[/COLOR][COLOR gold] Otros repositorios y plugins [/COLOR][COLOR lightblue] desde 19.x[/B][/COLOR][CR]'
        txt += '            - [COLOR goldenrod][B] repository.elementumorg [/B][/COLOR][CR]'

    txt += '[CR]*) Para [COLOR gold][B]Otros Motores Torrent[/B][/COLOR], le sugerimos localize tutoriales al respecto en [COLOR cyan][B]YouTube[/B][/COLOR]'

    platformtools.dialog_textviewer('¿ Dónde obtener los Add-Ons para torrents ?', txt)


def show_help_semillas(item):
    logger.info()

    if not xbmc.getCondVisibility('System.HasAddon("plugin.video.elementum")'):
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Aún No Instalado[/COLOR][/B]' % color_alert)
        return

    txt = '*) Los archivos Torrent se proveen de [COLOR gold][B]Semillas[/B][/COLOR] usuarios que están Online con las partes de ese archivo.'

    txt += '[CR]    Los Usuarios que tengan ese archivo [COLOR goldenrod][B]NO[/B][/COLOR] han de ser necesariamente [COLOR goldenrod][B]SOLO[/B][/COLOR] de Balandro.'
    txt += '[CR]    Estas partes residen en los [COLOR goldenrod][B]EQUIPOS[/B][/COLOR] de cada uno de los usuarios que tengan ese archivo Torrent.'

    txt += '[CR][CR]*) Si [COLOR goldenrod][B]TODAS[/B][/COLOR] las partes no están [COLOR goldenrod][B]ONLINE[/B][/COLOR], [COLOR gold][B]Elememtum[/B][/COLOR] cierra por [COLOR red][B]Time Out[/B][/COLOR], para no perder el tiempo.'

    txt += '[CR]    Si ese dato contiene un [COLOR red]Número[B][/B][/COLOR], significará que hay [COLOR gold][B]Más de Una Semilla[/B][/COLOR].'

    txt += '[CR][CR]    Por ejemplo, en la pantalla de seguimiento de [COLOR gold][B]Elememtum[/B][/COLOR], comprobar el dato [COLOR goldenrod][B]S:[/B][/COLOR]'
    txt += '[CR]    si ese dato contiene [COLOR red][B]0[/B][/COLOR], significará que no hay [COLOR gold][B]Semillas[/B][/COLOR].'

    txt += '[CR][CR]    Si [COLOR red][B]NO[/B][/COLOR] apareciera la pantalla de seguimiento de [COLOR gold][B]Elememtum[/B][/COLOR] [COLOR red][B]No hay ningún usuario Online[/B][/COLOR]'

    txt += '[CR][CR]*) Por lo tanto, tocará esperar, a que estén Onlime [COLOR gold][B]Todos los Usuarios[/B][/COLOR] con las partes para efectuar el Play.'

    platformtools.dialog_textviewer('Información archivos Torrent (Semillas)', txt)


def show_torrents_parameters(item):
    if config.get_setting('mnu_simple', default=False):
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]NO disponible en [COLOR yellow]Menú Simplificado[/B][/COLOR]' % color_alert)
        return

    if not config.get_setting('mnu_torrents', default=True):
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Opción Des-Activada en [COLOR tan]Menú[/B][/COLOR]' % color_alert)
        return

    txt = '[COLOR blue][B]ADD-ONS TORRENTS:[/B][/COLOR][CR]'

    cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

    if cliente_torrent == 'Seleccionar' or cliente_torrent == 'Ninguno': tex_tor = cliente_torrent
    else:
       tex_tor = cliente_torrent
       cliente_torrent = 'plugin.video.' + cliente_torrent.lower()
       if xbmc.getCondVisibility('System.HasAddon("%s")' % cliente_torrent):
           cod_version = xbmcaddon.Addon(cliente_torrent).getAddonInfo("version").strip()
           tex_tor += '  [COLOR goldenrod]' + cod_version + '[/COLOR]'

    txt += ' - Cliente/Motor Torrent (por defecto Seleccionar)' + '[COLOR fuchsia][B] ' + tex_tor + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("script.elementum.burst")'):
        cod_version = xbmcaddon.Addon("script.elementum.burst").getAddonInfo("version").strip()
        tex_tor = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
    else: tex_tor = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]Elementum Burst[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_tor + '[/B][/COLOR][CR]'

    if not PY3:
        if xbmc.getCondVisibility('System.HasAddon("repository.elementum")'):
            cod_version = xbmcaddon.Addon("repository.elementum").getAddonInfo("version").strip()
            tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

        txt += ' - [COLOR gold][B]Repository Elementum[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + ' (hasta K18.x)[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("repository.elementumorg")'):
        cod_version = xbmcaddon.Addon("repository.elementumorg").getAddonInfo("version").strip()
        tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
    else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR gold][B]Repository ElementumOrg[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + '[/B][/COLOR][CR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.elementum")'):
        txt += '[COLOR blue][B]VER[/B][/COLOR] Información Archivos Torrent [COLOR goldenrod][B]SEMILLAS[/B][/COLOR] en la Ayuda de [COLOR blue][B]TORRENTS[/B][/COLOR] [COLOR fuchsia][B]Cuestiones Preliminares[/B][/COLOR]'

    platformtools.dialog_textviewer('Información Parámetros Actuales en Torrents', txt)


def show_help_search(item):
    txt = ''

    if not config.get_setting('search_extra_main', default=False):
        txt += '[COLOR gold][B]Por Defecto[/B][/COLOR]:[CR]'
        txt += ' Está [COLOR coral][B]Des-Habilitada[/B][/COLOR] la opción del Menú principal y Sub-Menús [B][COLOR violet]Búsquedas Especiales (Listas TMDB, etc.)[/COLOR][/B][CR][CR]'

        txt += '[CR]'

    txt += 'Las opciones de búsquedas:[CR]'
    txt += '  [COLOR yellow][B]Películas y/ó Series[/B][/COLOR] y [COLOR hotpink][B]Series[/B][/COLOR][CR]'
    txt += '  abarcan también buscar en [COLOR limegreen][B] Novelas[/B][/COLOR] y en [COLOR goldenrod][B]Programas de Televisión[/B][/COLOR].[CR][CR]'

    txt += 'Desde los Ajustes [COLOR yellow][B]categoría Buscar[/B][/COLOR] se puede definir [COLOR chartreuse][B] los Resultados que se Previsualizan para cada canal[/B][/COLOR].'
    txt += ' Si por ejemplo el canal devuelve 15 resultados y se previsualizan 2, entrar en el enlace del [COLOR gold][B]Nombre del canal[/B][/COLOR] de la búsqueda para verlos todos.'

    txt += '[CR][CR]En cada web/canal el [COLOR cyan][B]Tiempo de Respuesta[/B][/COLOR] puede ser elevado y más aún si tiene [COLOR red][B]Proxies Configurados[/B][/COLOR].'

    txt += '[CR][CR]Según cada web/canal su buscador puede permitir diferenciar por [COLOR yellow][B]Películas y/ó Series[/B][/COLOR] ó [COLOR darkcyan][B]No[/B][/COLOR].'

    txt += '[CR][CR][COLOR yellowgreen][B]También es variable la sensibilidad de la búsqueda (si busca sólo en el Título ó también en la Sinopsis, el tratamiento si hay varias palabras, si devuelve muchos ó pocos resultados, etc.)[/B][/COLOR]'

    txt += '[CR][CR]Desde cualquier [COLOR deepskyblue][B]Película[/B][/COLOR] ó [COLOR hotpink][B]Serie[/B][/COLOR], se puede acceder al [COLOR yellow][B]Menú contextual[/B][/COLOR] para buscar esa misma referencia en los demás canales.'

    if config.get_setting('tracking_weberror_dialog', default=True):
        txt += '[CR][CR]Desde cualquier [COLOR deepskyblue][B]Película[/B][/COLOR] ó [COLOR hotpink][B]Serie[/B][/COLOR] guardada en [COLOR tan][B]Preferidos[/B][/COLOR], si al acceder se produce un error en la web, se ofrece un diálogo para volver a buscar esa referencia ([COLOR gold][B]Misma/Parecida/Similar[/B][/COLOR]) en los demás canales ó en el mismo canal (por si los enlaces ya no funcionan).'

    platformtools.dialog_textviewer('Información sobre búsquedas', txt)

    return True


def show_help_parameters_search(item):
    if config.get_setting('mnu_simple', default=False):
        txt = '[CR] - Opera con el Menú [B][COLOR crimson]SIMPLIFICADO[/COLOR][/B][CR]'
        txt += '    - No Se Buscará en los canales [B][I][COLOR plum]Inestables[/COLOR][/I][/B][CR]'
        txt += '    - No Se Buscará en los canales [B][I][COLOR darkgoldenrod]Problemáticos[/COLOR][/I][/B][CR][CR]'

    else: txt = 'Los canales que tenga marcados como [B][COLOR cyan]Desactivados[/COLOR][/B] nunca intervendrán en las búsquedas[CR][CR]'

    txt += ' - [B][COLOR gold]Canales[/COLOR][/B] que Nunca intervienen en las busquedas:'

    if con_incidencias:
        txt += '[CR][COLOR tan][B]    Hay Canales Con Incidencias[/COLOR] [COLOR darkorange]vea Últimos Cambios de Dominios en la Ayuda[/B][/COLOR][CR]'

    if search_no_accesibles:
        if no_accesibles:
            txt += '[CR][COLOR indianred][B]    Hay Canales No Accesibles[/COLOR] [COLOR darkorange]vea Últimos Cambios de Dominios en la Ayuda[/B][/COLOR][CR]'

        if con_problemas:
            txt += '[CR][COLOR tomato][B]    Hay Canales Con Problemas[/COLOR] [COLOR darkorange]vea Últimos Cambios de Dominios en la Ayuda[/B][/COLOR][CR]'

    presentar = False
    if config.get_setting('mnu_pelis', default=True): presentar = True

    if presentar:
        txt += '[CR][COLOR deepskyblue][B]    CineDeAntes,  CineLibreOnline,  CineMatteFlix,  SigloXX, T ráilers[/B][/COLOR] '

    presentar = False
    if config.get_setting('mnu_documentales', default=True): presentar = True

    if presentar:
        txt += '[CR][COLOR darkcyan][B]    DocumentaryHeaven,  TopDocumentaryFilms,  YouTubeDocs[/B][/COLOR]'

    presentar = False
    if config.get_setting('mnu_series', default=True): presentar = True

    if presentar:
        txt += '[CR][COLOR hotpink][B]    SeriesBiblicas,  TvSeries[/B][/COLOR]'

    presentar = False
    if config.get_setting('mnu_torrents', default=True): presentar = True

    if presentar:
        txt += '[CR][COLOR blue][B]    FrozenLayer[/B][/COLOR]'

    if not config.get_setting('mnu_documentales', default=True): txt += '[CR][CR] - Los canales de [B][COLOR cyan]Documentales[/COLOR][/B] jamás intervendrán en las busquedas'

    txt += '[CR][CR] - Qué canales Nunca intervendrán en las busquedas de [COLOR gold][B]Peliculas, Series y/ó Documentales[/B][/COLOR]:'

    if not search_no_accesibles:
        if no_accesibles:
            txt += '[CR]   - Los canales [B][COLOR tan]No Accesibles[/COLOR][/B]'
        if con_problemas:
            txt += '[CR]   - Los canales [B][COLOR tomato]Con Problemas[/COLOR][/B]'

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_doramas', default=True): txt += '[CR]   - Los canales de [B][COLOR firebrick]Doramas[/COLOR][/B]'

        if config.get_setting('mnu_animes', default=True): txt += '[CR]   - Los canales de [B][COLOR springgreen]Animes[/COLOR][/B]'

        if config.get_setting('mnu_adultos', default=True): txt += '[CR]   - Los canales de [B][COLOR orange]Adultos[/COLOR][/B]'

    txt += '[CR][CR] - [COLOR goldenrod][B]Procesos[/COLOR][/B]:'

    txt += '[CR]   - Cuantos Resultados se previsualizarán por canal (por defecto 2): [COLOR coral][B]' + str(config.get_setting('search_limit_by_channel', default=2)) + '[/COLOR][/B]'

    if config.get_setting('search_only_prefered', default=False): txt += '[CR]   - Tiene Activado efectuar búsquedas solo en los canales [B][COLOR gold]Preferidos[/COLOR][/B]'

    if config.get_setting('search_only_suggesteds', default=False): txt += '[CR]   - Tiene Activado efectuar búsquedas solo en los canales [B][COLOR moccasin]Sugeridos[/COLOR][/B]'

    if config.get_setting('search_no_proxies', default=False): txt += '[CR]   - Tiene Activado descartar búsquedas en los canales con [B][COLOR red]Proxies informados[/COLOR][/B]'

    if config.get_setting('search_con_torrents', default=False): txt += '[CR]   - Tiene Activado efectuar las búsquedas solo en los canales que pueden contener archivos [B][COLOR blue]Torrent[/COLOR][/B]'

    if config.get_setting('search_no_torrents', default=False): txt += '[CR]   - Tiene Activado descartar en las búsquedas los canales que pueden contener archivos [B][COLOR blue]Torrent[/COLOR][/B]'

    if config.get_setting('search_no_exclusively_torrents', default=False): txt += '[CR]   - Tiene Activado descartar en las búsquedas los canales con enlaces exclusivamente [B][COLOR blue]Torrent[/COLOR][/B]'

    if config.get_setting('search_no_notices', default=False): txt += '[CR]   - Tiene Activado descartar búsquedas en los canales con [COLOR green][B]Aviso[/COLOR][COLOR red] CloudFlare [COLOR orangered]Protection[/B][/COLOR]'

    if config.get_setting('search_no_cryptos', default=False): txt += '[CR]   - Tiene Activado descartar búsquedas en los canales con [COLOR darksalmon][B]Enlaces Cifrados[/B][/COLOR]'

    if config.get_setting('search_no_inestables', default=False): txt += '[CR]   - Tiene Activado descartar búsquedas en los canales que sean [B][COLOR plum]Inestables[/COLOR][/B]'

    if config.get_setting('search_no_problematicos', default=False): txt += '[CR]   - Tiene Ativado descartar búsquedas en los canales que sean [B][COLOR darkgoldenrod]Problemáticos[/COLOR][/B]'

    if config.get_setting('search_no_clones', default=False): txt += '[CR]   - Tiene Ativado descartar búsquedas en los canales que sean [B][COLOR turquoise]Clones[/COLOR][/B]'

    if no_accesibles:
        if search_no_accesibles:
            txt += '[CR]   - Tiene [B][COLOR yellow]Activado[/COLOR][/B] que los canales [B][COLOR tan]No Accesibles[/COLOR][/B] Intervengan en las Búsquedas'

    txt += '[CR]   - Añadir acceso al detalle de Personalizar Próximas Búsquedas:'

    if config.get_setting('sub_mnu_cfg_prox_search', default=True): txt += ' [COLOR coral][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR coral][B] Des-Activado[/B][/COLOR]'

    txt += '[CR]   - Menú contextual para Buscar Exacto ó Parecido en los resultados de las Búsquedas:'

    if config.get_setting('search_dialog', default=True): txt += ' [COLOR coral][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR coral][B] Des-Activado[/B][/COLOR]'

    txt += '[CR]   - Notificar en qué canales No han funcionado los Proxies:'

    if config.get_setting('search_no_work_proxies', default=False): txt += ' [COLOR coral][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR coral][B] Des-Activado[/B][/COLOR]'

    txt += '[CR]   - Presentar en qué canales deberá configurar Nuevamente Proxies:'

    if no_results_proxies: txt += ' [COLOR coral][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR coral][B] Des-Activado[/B][/COLOR]'

    txt += '[CR]   - Presentar los canales Sin Resultados:'

    if no_results: txt += ' [COLOR coral][B] Activado[/B][/COLOR]'
    else: txt += ' [COLOR coral][B] Des-Activado[/B][/COLOR]'

    if config.get_setting('search_no_channels', default=False): txt += '[CR]    - Tiene Activado notificar en las búsquedas los canales [B][COLOR yellowgreen]Ignorados[/COLOR][/B]'

    if not config.get_setting('search_multithread', default=True): txt += '[CR]    - Tiene Des-Activada la opción [B][COLOR yellowgreen]Multi T hread[/COLOR][/B](ventana acceso Multi Canales) '

    if config.get_setting('search_included_all', default=''):
        incluidos = config.get_setting('search_included_all', default='')
        if incluidos:
            txt += '[CR]   - [COLOR yellow][B]Búsquedas [COLOR greenyellow][B]Solo Determinados canales[/B][/COLOR] incluidos en [B][COLOR green]Todos[/COLOR][/B]:'
            incluidos = scrapertools.find_multiple_matches(incluidos, "'(.*?)'")

            for incluido in incluidos:
                incluido = incluido.capitalize().strip()
                txt += '[CR]     [COLOR violet][B] ' + incluido + '[/B][/COLOR]'

    filtros = {'searchable': True}

    ch_list = channeltools.get_channels_list(filtros=filtros)

    if ch_list:
        txt_ch = ''

        for ch in ch_list:
            if not ch['status'] == -1: continue

            txt_ch += '[CR]   [COLOR gray]%s[/COLOR]' % ch['name']

        if txt_ch: txt += '[CR][CR] - [COLOR gold]Desactivados:[/COLOR]  %s' % str(txt_ch) 

    filtros = {'searchable': True}

    ch_list = channeltools.get_channels_list(filtros=filtros)

    if ch_list:
       txt_ch = ''

       for ch in ch_list:
           cfg_searchable_channel = 'channel_' + ch['id'] + '_no_searchable'

           if not config.get_setting(cfg_searchable_channel, default=False): continue

           txt_ch += '[CR]   [COLOR gold]%s[/COLOR]' % ch['name']

       if txt_ch: txt += '[CR][CR] - [COLOR goldenrod][B]Canales excluidos[B][/COLOR]:  %s' % str(txt_ch)

    if config.get_setting('search_excludes_movies', default=''):
        excluidos = config.get_setting('search_excludes_movies', default='')
        if excluidos:
            txt += '[CR][CR] - [COLOR goldenrod][B]Canales excluidos en las búsquedas de [COLOR deepskyblue]Películas[/COLOR][/B]:'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt += '[CR]   [COLOR gold][B] ' + excluido + '[/B][/COLOR]'

    if config.get_setting('search_excludes_tvshows', default=''):
        excluidos = config.get_setting('search_excludes_tvshows', default='')
        if excluidos:
            txt += '[CR][CR] - [COLOR goldenrod][B]Canales excluidos en las búsquedas de [COLOR hotpink]Series[/COLOR][/B]:'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt += '[CR]   [COLOR gold][B] ' + excluido + '[/B][/COLOR]'

    if config.get_setting('search_excludes_documentaries', default=''):
        excluidos = config.get_setting('search_excludes_documentaries', default='')
        if excluidos:
            txt += '[CR][CR] - [COLOR goldenrod][B]Canales excluidos en las búsquedas de [COLOR cyan]Documentales[/COLOR][/B]:'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt += '[CR]   [COLOR gold][B] ' + excluido + '[/B][/COLOR]'

    if config.get_setting('search_excludes_torrents', default=''):
        excluidos = config.get_setting('search_excludes_torrents', default='')
        if excluidos:
            txt += '[CR][CR] - [COLOR goldenrod][B]Canales excluidos en las búsquedas de [COLOR blue]Torrents[/COLOR][/B]:'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt += '[CR]   [COLOR gold][B] ' + excluido + '[/B][/COLOR]'

    if config.get_setting('search_excludes_mixed', default=''):
        excluidos = config.get_setting('search_excludes_mixed', default='')
        if excluidos:
            txt += '[CR][CR] - [COLOR goldenrod][B]Canales excluidos en las búsquedas de [COLOR yellow]Películas y/ó Series[/COLOR][/B]:'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt += '[CR]   [COLOR gold][B] ' + excluido + '[/B][/COLOR]'

    if config.get_setting('search_excludes_all', default=''):
        excluidos = config.get_setting('search_excludes_all', default='')
        if excluidos:
            txt += '[CR][CR] - [COLOR goldenrod][B]Canales excluidos en las búsquedas de [COLOR green]Todos[/COLOR][/B]:'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt += '[CR]   [COLOR gold][B] ' + excluido + '[/B][/COLOR]'

    if config.get_setting('search_show_last', default=True):
        txt += '[CR][CR] - Textos para búsquedas [B][COLOR goldenrod]Memorizados[/COLOR][/B]:'

        hay_lastest = False

        if config.get_setting('search_last_all', default=''):
            hay_lastest = True

            txt += '[CR]   [COLOR yellow][B]General:[/B][/COLOR]  ' + config.get_setting('search_last_all')

        if config.get_setting('search_last_movie', default=''):
            hay_lastest = True

            txt += '[CR]   [COLOR deepskyblue][B]Películas:[/B][/COLOR]  ' + config.get_setting('search_last_movie')

        if config.get_setting('search_last_tvshow', default=''):
            hay_lastest = True

            txt += '[CR]   [COLOR hotpink][B]Series:[/B][/COLOR]  ' + config.get_setting('search_last_tvshow')

        if config.get_setting('search_last_documentary', default=''):
            hay_lastest = True

            txt += '[CR]   [COLOR cyan][B]Documentales:[/B][/COLOR]  ' + config.get_setting('search_last_documentary')

        if config.get_setting('search_last_torrent', default=''):
            hay_lastest = True

            txt += '[CR]   [COLOR blue][B]Torrent:[/B][/COLOR]  ' + config.get_setting('search_last_torrent')

        if config.get_setting('search_last_dorama', default=''):
            hay_lastest = True

            txt += '[CR]   [COLOR firebrick][B]Dorama:[/B][/COLOR]  ' + config.get_setting('search_last_dorama')

        if config.get_setting('search_last_anime', default=''):
            hay_lastest = True

            txt += '[CR]   [COLOR springgreen][B]Anime:[/B][/COLOR]  ' + config.get_setting('search_last_anime')

        if config.get_setting('search_last_person', default=''):
            hay_lastest = True

            txt += '[CR]   [COLOR plum][B]Personas:[/B][/COLOR]  ' + config.get_setting('search_last_person')

        if config.get_setting('search_last_list', default=''):
            hay_lastest = True

            txt += '[CR]   [COLOR greenyellow][B]Listas:[/B][/COLOR]  ' + config.get_setting('search_last_list')

        if config.get_setting('search_last_video', default=''):
            hay_lastest = True

            txt += '[CR]   [COLOR orange][B]+18 Vídeos:[/B][/COLOR]  ' + config.get_setting('search_last_video')

        if not hay_lastest: txt += '[CR]   [COLOR cyan][B]Sin textos memorizados[/B][/COLOR]'

    platformtools.dialog_textviewer('Información sobre sus parámetros de búsquedas', txt)

    return True


def show_help_centers(item):
    logger.info()

    txt = '[COLOR yellow][B]KODI:[/B][/COLOR][CR]'

    txt += '  *) Localize tutoriales en [COLOR cyan][B]YouTube[/B][/COLOR] ó bien acceda a [COLOR yellow][B]kodi.tv[/B][/COLOR],[CR]'
    txt += '      para obtener Información y Soporte al respecto.[CR][CR]'

    txt += '  *) También puede acceder a la Web [COLOR violet][B]mundokodi.com[/B][/COLOR] para efectuar consultas.[CR]'
    txt += '      para obtener [COLOR goldenrod]Tutoriales, Instalaciones, Funciones, Add-Ons, Noticias, etc.[/COLOR][CR][CR]'

    txt += '[COLOR limegreen][B]ADD-ONS EXTERNOS:[/B][/COLOR][CR]'

    txt += '   Acceda a la Web [COLOR violet][B]www.pluginsxbmc.com[/B][/COLOR][CR]'
    txt += '   para obtener [COLOR goldenrod]Tutoriales, Instalaciones, Funciones, Add-Ons, Noticias, etc.[/COLOR]'

    platformtools.dialog_textviewer('¿ Dónde obtener soporte para su Media Center ?', txt)


def show_help_vias_elementum(item):
    item.only_elementum = True

    show_help_vias(item)

def show_help_vias_resolve(item):
    item.only_resolve = True

    show_help_vias(item)

def show_help_vias_youtube(item):
    item.only_youtube = True

    show_help_vias(item)

def show_help_vias(item):
    logger.info()

    txt = '*) A través de un [COLOR cyan]Navegador de Internet[/COLOR] localize e instale al menos uno de los Add-Ons de la lista que más se adapte a'
    txt += '  sus necesidades y que a su vez sea compatible con su Media Center.'

    presentar_all = True

    if not item.only_elementum: presentar_elementum = False
    else:
       presentar_all = False
       presentar_elementum = True

    if not item.only_resolve: presentar_resolve = False
    else:
       presentar_all = False
       presentar_resolve = True

    if not item.only_youtube: presentar_youtube = False
    else:
       presentar_all = False
       presentar_youtube = True

    if presentar_all or presentar_youtube or presentar_resolve:
        txt += '[CR][CR]*) Add-Ons:[CR]'

    if presentar_all:
        txt += '    - [COLOR yellow][B]inputstream.adaptive[/B][/COLOR][CR]'

    if presentar_all or presentar_youtube:
        txt += '    - [COLOR yellow][B]plugin.video.youtube[/B][/COLOR][CR]'

    if presentar_all or presentar_resolve:
        txt += '    - [COLOR yellow][B]script.module.resolveurl[/B][/COLOR]'

    if presentar_all or presentar_resolve or presentar_elementum:
        txt += '[CR][CR]*) Repositorios:[CR]'

    if presentar_all or presentar_elementum:
        if not PY3:
            txt += '    - [COLOR yellow][B]repository.elementum[/B][/COLOR][CR]'
        else:
            txt += '    - [COLOR yellow][B]repository.elementumorg[/B][/COLOR][CR]'

    if presentar_all or presentar_resolve:
        txt += '    - [COLOR yellow][B]repository.resolveurl[/B][/COLOR][CR]'

    txt += '[CR]*) Algunos puede obtenerlos desde [COLOR chartreuse][B]Nuestra Fuente[/B][/COLOR], carpeta [COLOR gold][B]Scripts[/B][/COLOR].[CR]'
    txt += '    Fuente  [COLOR darkorange][B]repobal.github.io/base/[/B][/COLOR][CR]'

    txt += '    Scripts  [COLOR mediumaquamarine][B]repobal.github.io/base/scripts/[/B][/COLOR][CR]'

    if not PY3:
        txt += '[CR]     - [COLOR lightblue][B]Carpeta Kodi18:[/COLOR][COLOR gold] Otros repositorios y plugins [/COLOR][COLOR lightblue] hasta 18.x[/B][/COLOR][CR]'

        if presentar_all or presentar_youtube:
            txt += '        - [COLOR goldenrod][B] plugin.video.youtube [/B][/COLOR][CR]'

        if presentar_all or presentar_elementum:
            txt += '        - [COLOR goldenrod][B] repository.elementum [/B][/COLOR][CR]'

        if presentar_all or presentar_resolve:
            txt += '        - [COLOR goldenrod][B] repository.resolveurl [/B][/COLOR][CR]'

    else:
        txt += '[CR]     - [COLOR lightblue][B]Carpeta Kodi19:[/COLOR][COLOR gold] Otros repositorios y plugins [/COLOR][COLOR lightblue] desde 19.x[/B][/COLOR][CR]'

        if presentar_all or presentar_youtube:
            txt += '        - [COLOR goldenrod][B] plugin.video.youtube [/B][/COLOR][CR]'

        if presentar_all or presentar_elementum:
            txt += '        - [COLOR goldenrod][B] repository.elementumorg [/B][/COLOR][CR]'

        if presentar_all or presentar_resolve:
            txt += '        - [COLOR goldenrod][B] repository.resolveurl [/B][/COLOR][CR]'

    txt += '[CR]*) Ó bien, le sugerimos localize tutoriales en [COLOR cyan][B]YouTube[/B][/COLOR], para obtener información al respecto.'

    if presentar_all:
        platformtools.dialog_textviewer('¿ Dónde obtener los Add-Ons para Vías Alternativas ?', txt)

    elif presentar_elementum:
        platformtools.dialog_textviewer('¿ Dónde obtener los Add-Ons para Vía Alternativa Elementum ?', txt)

    elif presentar_resolve:
        platformtools.dialog_textviewer('¿ Dónde obtener los Add-Ons para Vía Alternativa ResolveUrl ?', txt)

    else:
        platformtools.dialog_textviewer('¿ Dónde obtener los Add-Ons para Vía Alternativa YouTube ?', txt)


def show_help_elementum(item):
    logger.info()

    if not xbmc.getCondVisibility('System.HasAddon("plugin.video.elementum")'):
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Aún No Instalado[/COLOR][/B]' % color_alert)
        return

    if not PY3:
        return

    txt = '*) Al ser su Media Center una versión posterior a [COLOR gold][B]18.x[/COLOR][/B] y si [COLOR yellow][B]NO[/B][/COLOR] opera bajo el sistema operativo [COLOR gold][B]Windows[/COLOR][/B], en determinadas ocasiones, puede fallar la Reproducción, a través de este Motor Torrent.'

    txt += '[CR][CR]*) Ejemplo: si esta operando bajo [COLOR yellow][B]Android[/B][/COLOR] y su versión de [COLOR gold][B]Kodi[/B][/COLOR] es superior a [COLOR gold][B]18.x[/B][/COLOR][CR]'
    txt += '    Podría necesitar un [COLOR darkorange][B]Media Center Especial Modificado para ello.[/B][/COLOR]'

    txt += '[CR][CR]*) Localize tutoriales en [COLOR cyan][B]YouTube[/B][/COLOR], para obtener información al respecto.'

    platformtools.dialog_textviewer('Información Motor Torrent Elementum', txt)


def show_legalidad(item):
    logger.info()

    txt = '[COLOR yellow]*)[B] Balandro es un Navegador de Páginas Webs [COLOR moccasin][B]y  es Totalmente [I] GRATUITO [/I], si Pagó por este Add-On le [I] ENGAÑARON, [/I][/B][/COLOR]'
    txt += '[COLOR lightblue][B] y tiene como objeto, permitir visualizar Películas, Series, Documentales, etc... [/B][/COLOR]'
    txt += '[COLOR lightblue][B] Todo a través de Internet y directamente desde su Sistema Media Center.[/B][/COLOR]'

    txt += '[CR][CR][COLOR orchid][B] Este Add-On es tan solo un mero Ejercicio de Aprendizaje del Lenguaje de Programación Python y se distribuye sin Ningún Contenido Multimedia adjunto al mismo.[/B][/COLOR]'
    txt += '[COLOR lightgrey][B][I] En consecuencia solo Las Webs son plenamente Responsables de los Contenidos que Publiquen [/I][/B][/COLOR]'

    txt += '[CR][CR][COLOR tan][B] Úselo de acuerdo con su Criterio y bajo su Responsabilidad,[/B][/COLOR]'
    txt += '[COLOR tan][B] sus Creadores quedarán Totalmente Eximidos de toda Repercusión Legal, si se Re-Distribuye solo ó con acceso a Contenidos Protegidos por los Derechos de Autor, sin el Permiso Explícito de estos mismos.[/B][/COLOR]'

    txt += '[CR][CR]*)[COLOR chocolate][B][I] Si este tipo de contenido está Prohibido en su País, solamente Usted será el Responsable de su uso.[/I][/B][/COLOR]'

    txt += '[CR][CR]*)[COLOR mediumaquamarine][B] Este Add-On es un proyecto sin ánimo de Lucro y con Fines Educativos, por lo tanto está Prohibida su Venta en solitario ó como parte de Software Integrado en cualquier dispositivo, es exclusivamente para un uso Docente y Personal.[/B][/COLOR]'

    txt += '[CR][CR]*)[COLOR moccasin][B] Navega con Kodi por Páginas Webs para poder ver sus contenidos de manera fácil.[/B][/COLOR]'
    txt += '[CR]  [COLOR chartreuse][B] Versiones de este Add-On desde el año 2018.[/B][/COLOR]'

    txt += '[CR][CR]*)[COLOR aqua][B] Los Propietarios y Distribuidores de este Add-On no Proveen ni Distribuyen Ningún Contenido Mostrado por el Add-On, ni Tienen Afiliación alguna con los Proveedores/Webs de contenidos.[/B][/COLOR]'

    txt += '[CR][CR]*)[COLOR red][B][I] Queda totalmente Prohibida su Re-Distribución, sin la Autorización Fehaciente de sus Creadores.[/I][/B][/COLOR]'

    platformtools.dialog_textviewer('Cuestiones Legales', txt)


def show_license(item):
    logger.info()

    txt = ''

    try:
       with open(os.path.join(config.get_runtime_path(), 'LICENSE'), 'r') as f: txt=f.read(); f.close()
    except:
       try: txt = open(os.path.join(config.get_runtime_path(), 'LICENSE'), encoding="utf8").read()
       except: pass

    if txt: platformtools.dialog_textviewer('Licencia (Gnu Gpl v3)', txt)


def show_test(item):
    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Cargando Información Sistema[/B][/COLOR]' % color_exec)

    your_ip = ''

    try:
       data = httptools.downloadpage('http://httpbin.org/ip').data
       data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)
       your_ip = scrapertools.find_single_match(str(data), '.*?"origin".*?"(.*?)"')
    except:
       pass

    if not your_ip:
        try: your_ip = httptools.downloadpage('http://ipinfo.io/ip').data
        except: pass

    if not your_ip:
        try: your_ip = httptools.downloadpage('http://www.icanhazip.com/').data
        except: pass

    if not your_ip:
	    platformtools.dialog_ok(config.__addon_name, '[COLOR red][B]Parece que NO hay conexión con internet.[/B][/COLOR]', 'Compruebelo realizando cualquier Búsqueda, desde un Navegador de Internet.')

    hay_repo = False
    if xbmc.getCondVisibility('System.HasAddon("%s")' % 'repository.balandro'): hay_repo = True

    access_repo = False
    tex_access_repo = ''

    if hay_repo:
        try:
           data = httptools.downloadpage(ADDON_REPO_ADDONS).data
           if data:
               if '<h1>404</h1>' in data: tex_access_repo = '[COLOR red][B][I]No Accesible[/I][/B][/COLOR]'
               else: access_repo = True
           else: tex_access_repo = '[COLOR red][B]No se pudo comprobar[/B][/COLOR]'
        except: tex_access_repo = '[COLOR red][B]No se pudo comprobar[/B][/COLOR]'

    ult_ver = ''

    access_last_ver = False

    if hay_repo:
        if access_repo:
            try: ult_ver = updater.check_addon_version()
            except: pass

            if ult_ver: access_last_ver = True

    access_fixes = False
    tex_access_fixes = ''

    if hay_repo:
        if access_repo:
            try:
               data = httptools.downloadpage(ADDON_UPDATES_JSON).data
               if data:
                   if '404: Not Found' in data: tex_access_fixes = '[COLOR red][B][I]No Accesibles[/I][/B][/COLOR]'
                   else: access_fixes = True

                   if 'addon_version' not in data or 'fix_version' not in data: access_fixes = None

                   if not access_fixes is None:
                       try: last_ver = updater.check_addon_version()
                       except: last_ver = None

                       if not last_ver is None:
                           if not last_ver: tex_access_fixes = '[COLOR indianred][B][I]NO recibe Fixes[/I][/B][/COLOR]'

               else: tex_access_fixes = '[COLOR red][B]No se pudo comprobar[/B][/COLOR]'
            except: tex_access_fixes = '[COLOR red][B]No se pudo comprobar[/B][/COLOR]'

    txt = '[CR][COLOR fuchsia]BALANDRO[/COLOR][CR]'

    if not your_ip: your_ip = '[COLOR red][B] Sin Conexión [/B][/COLOR]'

    txt += ' - [COLOR gold]Conexión internet:[/COLOR]  %s [CR][CR]' % your_ip

    tex_repo = ' Instalado'
    if hay_repo == False: tex_repo = '[I][B][COLOR %s] No instalado, No recibirá más versiones [/COLOR][/B][/I]' % color_adver

    txt += ' - [COLOR gold]Repositorio:[/COLOR]  %s [CR][CR]' % tex_repo
    tex_access_repo = ' Accesible'
    if access_repo == False: tex_access_repo = '[COLOR red][B][I] No Accesible [/I][/B][/COLOR]'

    txt += ' - [COLOR gold]Conexión con repositorio:[/COLOR]  %s [CR][CR]' % tex_access_repo

    if access_last_ver: tex_access_last_ver = ' Versión correcta '
    else:
        if not ult_ver:
            if not access_repo: tex_access_last_ver = '[I][B][COLOR %s] No Accesible [/COLOR][/B][/I]' % color_alert
            else: tex_access_last_ver = '[B][COLOR %s] Accesible desde Repositorio [/COLOR][/B]' % color_exec
        else: tex_access_last_ver = '[I][B][COLOR %s] (desfasada)[/COLOR][/B][/I]' % color_alert

    txt += ' - [COLOR gold]Última versión:[/COLOR]  %s [CR][CR]' % tex_access_last_ver

    if config.get_setting('addon_update_atstart', default=True): tex_atstart = '[COLOR yellow][B]Activado[/B][/COLOR]'
    else: tex_atstart = '[COLOR red][B]Des-Activado[/B][/COLOR]'

    txt += ' - [COLOR gold]Comprobar Fixes al Iniciar Media Center:  %s [CR][CR]' % tex_atstart

    if not tex_access_fixes:
        tex_access_fixes = ' [COLOR white]Accesibles[/COLOR]'
        if access_fixes == None: tex_access_fixes = '[COLOR yellow] Sin actualizaciones tipo Fix pendientes [/COLOR]'
        elif access_fixes == False: tex_access_fixes = '[I][B][COLOR red] No Accesibles [/COLOR][/B][/I]'

    txt += ' - [COLOR gold]Fixes sobre la versión:[/COLOR]  %s [CR][CR]' % tex_access_fixes

    avisar = False

    if not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developergenres.py')): avisar = True
    elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')): avisar = True
    elif not os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')): avisar = True

    txt += ' - [COLOR gold]Versión instalada:[/COLOR]  [COLOR yellow][B]%s[/B][/COLOR]' % config.get_addon_version().replace('.fix', '-Fix')
    if not ult_ver:
        if not access_repo: txt += '[B][I][COLOR %s] Sin Acceso al Repositorio[/COLOR][/I][/B]' % color_alert
        else:
           if not '-Fix' in txt:
               txt += '[B][I][COLOR %s] (desfasada)[/COLOR][/I][/B]' % color_adver

               text_dev = ''
               if config.get_setting('developer_mode', default=False):
                   if not avisar:
                       text_dev = ' [COLOR darkorange][B]Desarrollo[/B][/COLOR]'
                   else:
                       text_dev = ' [COLOR darkorange][B]Falso Desarrollo[/B][/COLOR]'

               txt += '  '  + text_dev

           if 'No se pudo comprobar' in tex_access_fixes: txt += '[B][I][COLOR gray] (fixes off)[/COLOR][/I][/B]'
           elif '(fixes off)' in tex_access_fixes: txt += '[B][I][COLOR gray] (fixes off)[/COLOR][/I][/B]'

    txt += '[CR][CR]'

    folder_down = config.get_setting('downloadpath', default='')
    if not folder_down == '':
        txt += ' - [COLOR gold]Carpeta descargas:[/COLOR]  [COLOR moccasin]%s[/COLOR][CR][CR]' % folder_down

    tex_xml = ''

    path = translatePath(os.path.join('special://home/userdata', ''))

    file_xml = 'advancedsettings.xml'
    file = path + file_xml
    existe = filetools.exists(file)

    if existe:
        if tex_xml: tex_xml = tex_xml + '   advancedsettings.xml  [CR]'
        else: tex_xml = '[CR]   ' +  'advancedsettings.xml[CR]'

    file_xml = 'favourites.xml'
    file = path + file_xml
    existe = filetools.exists(file)

    if existe:
        txt_favs = ''

        try:
           with open(os.path.join(path, file_xml), 'r') as f: txt_favs=f.read(); f.close()
        except:
           try: txt_favs = open(os.path.join(path, file_xml), encoding="utf8").read()
           except: pass

        bloque = scrapertools.find_single_match(txt_favs, '<favourites>(.*?)</favourites>')

        matches = bloque.count('<favourite')

        if matches == 0: existe = False

    if existe:
        if tex_xml: tex_xml = tex_xml + '   favourites.xml  [CR]'
        else: tex_xml = '[CR]   ' +  'favourites.xml[CR]'

    file_xml = 'playercorefactory.xml'

    file = path + file_xml

    existe = filetools.exists(file)

    if existe:
        if tex_xml: tex_xml = tex_xml + '   playercorefactory.xml  [CR]'
        else: tex_xml = '[CR]   ' +  'playercorefactory.xml[CR]'


    if tex_xml: txt += ' - [COLOR gold]Settings: [/COLOR]  [COLOR olive]%s[/COLOR][CR]' % tex_xml

    path = os.path.join(config.get_data_path(), 'Lista-proxies.txt')

    existe = filetools.exists(path)
    if existe: txt += ' - [COLOR gold]Personal:[/COLOR]   [COLOR white]Lista-proxies.txt[/COLOR][CR]'

    providers_preferred = config.get_setting('providers_preferred', default='')
    if providers_preferred:
        txt += '[CR] - [COLOR gold]Proveedores preferidos de proxies:[/COLOR][CR]'
        providers_preferred = config.get_setting('providers_preferred').split(',')

        for provider_preferred in providers_preferred:
            provider_preferred = provider_preferred.lower().strip()
            txt += '   [COLOR violet][B] ' + provider_preferred + '[/B][/COLOR][CR]'

        txt += '[CR]'
    else:
        if existe: txt += '[CR]'

    tex_dom = ''

    datos = channeltools.get_channel_parameters('animeflv')
    if datos['active']:
        animeflv_dominio = config.get_setting('channel_animeflv_dominio', default='')
        if animeflv_dominio:
           if tex_dom: tex_dom = tex_dom + '   AnimeFlv: ' + animeflv_dominio + '[CR]'
           else: tex_dom = '[CR]   AnimeFlv: ' + animeflv_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('animeonline')
    if datos['active']:
        animeonline_dominio = config.get_setting('channel_animeonline_dominio', default='')
        if animeonline_dominio:
           if tex_dom: tex_dom = tex_dom + '   AnimeOnline: ' + animeonline_dominio + '[CR]'
           else: tex_dom = '[CR]   AnimeOnline: ' + animeonline_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('animeyt')
    if datos['active']:
        animeyt_dominio = config.get_setting('channel_animeyt_dominio', default='')
        if animeyt_dominio:
           if tex_dom: tex_dom = tex_dom + '   AnimeYt: ' + animeyt_dominio + '[CR]'
           else: tex_dom = '[CR]   AnimeYt: ' + animeyt_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('cinecalidad')
    if datos['active']:
        cinecalidad_dominio = config.get_setting('channel_cinecalidad_dominio', default='')
        if cinecalidad_dominio:
           if tex_dom: tex_dom = tex_dom + '   CineCalidad: ' + cinecalidad_dominio + '[CR]'
           else: tex_dom = '[CR]   CineCalidad: ' + cinecalidad_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('cinecalidadla')
    if datos['active']:
        cinecalidadla_dominio = config.get_setting('channel_cinecalidadla_dominio', default='')
        if cinecalidadla_dominio:
           if tex_dom: tex_dom = tex_dom + '   CineCalidadLa: ' + cinecalidadla_dominio + '[CR]'
           else: tex_dom = '[CR]   CineCalidadLa: ' + cinecalidadla_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('cinecalidadlol')
    if datos['active']:
        cinecalidadlol_dominio = config.get_setting('channel_cinecalidadlol_dominio', default='')
        if cinecalidadlol_dominio:
           if tex_dom: tex_dom = tex_dom + '   CineCalidadLol: ' + cinecalidadlol_dominio + '[CR]'
           else: tex_dom = '[CR]   CineCalidadLol: ' + cinecalidadlol_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('cuevana2')
    if datos['active']:
        cuevana2_dominio = config.get_setting('channel_cuevana2_dominio', default='')
        if cuevana2_dominio:
           if tex_dom: tex_dom = tex_dom + '   Cuevana2: ' + cuevana2_dominio + '[CR]'
           else: tex_dom = '[CR]   Cuevana2: ' + cuevana2_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('cuevana2esp')
    if datos['active']:
        cuevana2esp_dominio = config.get_setting('channel_cuevana2esp_dominio', default='')
        if cuevana2esp_dominio:
           if tex_dom: tex_dom = tex_dom + '   Cuevana2Esp: ' + cuevana2esp_dominio + '[CR]'
           else: tex_dom = '[CR]   Cuevana2Esp: ' + cuevana2esp_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('cuevana3pro')
    if datos['active']:
        cuevana3pro_dominio = config.get_setting('channel_cuevana3pro_dominio', default='')
        if cuevana3pro_dominio:
           if tex_dom: tex_dom = tex_dom + '   Cuevana3Pro: ' + cuevana3pro_dominio + '[CR]'
           else: tex_dom = '[CR]   CuevanaPro: ' + cuevana3pro_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('divxatope')
    if datos['active']:
        divxatope_dominio = config.get_setting('channel_divxatope_dominio', default='')
        if divxatope_dominio:
           if tex_dom: tex_dom = tex_dom + '   DivxATope: ' + divxatope_dominio + '[CR]'
           else: tex_dom = '[CR]   DivxATope: ' + divxatope_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('divxtotal')
    if datos['active']:
        divxtotal_dominio = config.get_setting('channel_divxtotal_dominio', default='')
        if divxtotal_dominio:
           if tex_dom: tex_dom = tex_dom + '   DivxTotal: ' + divxtotal_dominio + '[CR]'
           else: tex_dom = '[CR]   DivxTotal: ' + divxtotal_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('dontorrents')
    if datos['active']:
        dontorrents_dominio = config.get_setting('channel_dontorrents_dominio', default='')
        if dontorrents_dominio:
           if tex_dom: tex_dom = tex_dom + '   DonTorrents: ' + dontorrents_dominio + '[CR]'
           else: tex_dom = '[CR]   DonTorrents: ' + dontorrents_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('dontorrentsin')
    if datos['active']:
        dontorrentsin_dominio = config.get_setting('channel_dontorrentsin_dominio', default='')
        if dontorrentsin_dominio:
           if tex_dom: tex_dom = tex_dom + '   DonTorrentsIn: ' + dontorrentsin_dominio + '[CR]'
           else: tex_dom = '[CR]   DonTorrentsIn: ' + dontorrentsin_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('elifilms')
    if datos['active']:
        elifilms_dominio = config.get_setting('channel_elifilms_dominio', default='')
        if elifilms_dominio:
           if tex_dom: tex_dom = tex_dom + '   EliFilms: ' + elifilms_dominio + '[CR]'
           else: tex_dom = '[CR]   EliFilms: ' + elifilms_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('elitedivx')
    if datos['active']:
        elitedivx_dominio = config.get_setting('channel_elitedivx_dominio', default='')
        if elitedivx_dominio:
           if tex_dom: tex_dom = tex_dom + '   EliteDivx: ' + elitedivx_dominio + '[CR]'
           else: tex_dom = '[CR]   EliteDivx: ' + elitedivx_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('elitetorrent')
    if datos['active']:
        elitetorrent_dominio = config.get_setting('channel_elitetorrent_dominio', default='')
        if elitetorrent_dominio:
           if tex_dom: tex_dom = tex_dom + '   EliteTorrent: ' + elitetorrent_dominio + '[CR]'
           else: tex_dom = '[CR]   EliteTorrent: ' + elitetorrent_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('elitetorrentnz')
    if datos['active']:
        elitetorrentnz_dominio = config.get_setting('channel_elitetorrentnz_dominio', default='')
        if elitetorrentnz_dominio:
           if tex_dom: tex_dom = tex_dom + '   EliteTorrentNz: ' + elitetorrentnz_dominio + '[CR]'
           else: tex_dom = '[CR]   EliteTorrentNz: ' + elitetorrentnz_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('ennovelastv')
    if datos['active']:
        ennovelastv_dominio = config.get_setting('channel_ennovelastv_dominio', default='')
        if ennovelastv_dominio:
           if tex_dom: tex_dom = tex_dom + '   EnNovelasTv: ' + ennovelastv_dominio + '[CR]'
           else: tex_dom = '[CR]   EnNovelasTv: ' + ennovelastv_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('entrepeliculasyseries')
    if datos['active']:
        entrepeliculasyseries_dominio = config.get_setting('channel_entrepeliculasyseries_dominio', default='')
        if entrepeliculasyseries_dominio:
           if tex_dom: tex_dom = tex_dom + '   EntrePeliculasySeries: ' + entrepeliculasyseries_dominio + '[CR]'
           else: tex_dom = '[CR]   EntrePeliculasySeries: ' + entrepeliculasyseries_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('gnula')
    if datos['active']:
        gnula_dominio = config.get_setting('channel_gnula_dominio', default='')
        if gnula_dominio:
           if tex_dom: tex_dom = tex_dom + '   Gnula: ' + gnula_dominio + '[CR]'
           else: tex_dom = '[CR]   Gnula: ' + gnula_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('gnula24')
    if datos['active']:
        gnula24_dominio = config.get_setting('channel_gnula24_dominio', default='')
        if gnula24_dominio:
           if tex_dom: tex_dom = tex_dom + '   Gnula24: ' + gnula24_dominio + '[CR]'
           else: tex_dom = '[CR]   Gnula24: ' + gnula24_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('gnula24h')
    if datos['active']:
        gnula24h_dominio = config.get_setting('channel_gnula24h_dominio', default='')
        if gnula24h_dominio:
           if tex_dom: tex_dom = tex_dom + '   Gnula24H: ' + gnula24h_dominio + '[CR]'
           else: tex_dom = '[CR]   Gnula24H: ' + gnula24h_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('grantorrent')
    if datos['active']:
        grantorrent_dominio = config.get_setting('channel_grantorrent_dominio', default='')
        if grantorrent_dominio:
           if tex_dom: tex_dom = tex_dom + '   GranTorrent: ' + grantorrent_dominio + '[CR]'
           else: tex_dom = '[CR]   GranTorrent: ' + grantorrent_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('hdfull')
    if datos['active']:
        hdfull_dominio = config.get_setting('channel_hdfull_dominio', default='')
        if hdfull_dominio:
           if tex_dom: tex_dom = tex_dom + '   HdFull: ' + hdfull_dominio + '[CR]'
           else: tex_dom = '[CR]   HdFull: ' + hdfull_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('henaojara')
    if datos['active']:
        henaojara_dominio = config.get_setting('channel_henaojara_dominio', default='')
        if henaojara_dominio:
           if tex_dom: tex_dom = tex_dom + '   HenaOjara: ' + henaojara_dominio + '[CR]'
           else: tex_dom = '[CR]   HenaOjara: ' + henaojara_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('homecine')
    if datos['active']:
        homecine_dominio = config.get_setting('channel_homecine_dominio', default='')
        if homecine_dominio:
           if tex_dom: tex_dom = tex_dom + '   HomeCine: ' + homecine_dominio + '[CR]'
           else: tex_dom = '[CR]   HomeCine: ' + homecine_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('mejortorrentapp')
    if datos['active']:
        mejortorrentapp_dominio = config.get_setting('channel_mejortorrentapp_dominio', default='')
        if mejortorrentapp_dominio:
           if tex_dom: tex_dom = tex_dom + '   MejorTorrentApp: ' + mejortorrentapp_dominio + '[CR]'
           else: tex_dom = '[CR]   MejorTorrentApp: ' + mejortorrentapp_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('mejortorrentnz')
    if datos['active']:
        mejortorrentnz_dominio = config.get_setting('channel_mejortorrentnz_dominio', default='')
        if mejortorrentnz_dominio:
           if tex_dom: tex_dom = tex_dom + '   MejorTorrentNz: ' + mejortorrentnz_dominio + '[CR]'
           else: tex_dom = '[CR]   MejorTorrentNz: ' + mejortorrentnz_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('mitorrent')
    if datos['active']:
        mitorrent_dominio = config.get_setting('channel_mitorrent_dominio', default='')
        if mitorrent_dominio:
           if tex_dom: tex_dom = tex_dom + '   MiTorrent: ' + mitorrent_dominio + '[CR]'
           else: tex_dom = '[CR]   MiTorrent: ' + mitorrent_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('peliculaspro')
    if datos['active']:
        peliculaspro_dominio = config.get_setting('channel_peliculaspro_dominio', default='')
        if peliculaspro_dominio:
           if tex_dom: tex_dom = tex_dom + '   PeliculasPro: ' + peliculaspro_dominio + '[CR]'
           else: tex_dom = '[CR]   PeliculasPro: ' + peliculaspro_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('pelisforte')
    if datos['active']:
        pelisforte_dominio = config.get_setting('channel_pelisforte_dominio', default='')
        if pelisforte_dominio:
           if tex_dom: tex_dom = tex_dom + '   PelisForte: ' + pelisforte_dominio + '[CR]'
           else: tex_dom = '[CR]   PelisForte: ' + pelisforte_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('pelismart')
    if datos['active']:
        pelismart_dominio = config.get_setting('channel_pelismart_dominio', default='')
        if pelismart_dominio:
           if tex_dom: tex_dom = tex_dom + '   PelisMart: ' + pelismart_dominio + '[CR]'
           else: tex_dom = '[CR]   PelisMart: ' + pelismart_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('pelispanda')
    if datos['active']:
        pelispanda_dominio = config.get_setting('channel_pelispanda_dominio', default='')
        if pelispanda_dominio:
           if tex_dom: tex_dom = tex_dom + '   PelisPanda: ' + pelispanda_dominio + '[CR]'
           else: tex_dom = '[CR]   PelisPanda: ' + pelispanda_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('pelispediaws')
    if datos['active']:
        pelispediaws_dominio = config.get_setting('channel_pelispediaws_dominio', default='')
        if pelispediaws_dominio:
           if tex_dom: tex_dom = tex_dom + '   PelisPediaWs: ' + pelispediaws_dominio + '[CR]'
           else: tex_dom = '[CR]   PelisPediaWs: ' + pelispediaws_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('pelisplushd')
    if datos['active']:
        pelisplushd_dominio = config.get_setting('channel_pelisplushd_dominio', default='')
        if pelisplushd_dominio:
           if tex_dom: tex_dom = tex_dom + '   PelisPlusHd: ' + pelisplushd_dominio + '[CR]'
           else: tex_dom = '[CR]   PelisPlusHd: ' + pelisplushd_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('pelisplushdlat')
    if datos['active']:
        pelisplushdlat_dominio = config.get_setting('channel_pelisplushdlat_dominio', default='')
        if pelisplushdlat_dominio:
           if tex_dom: tex_dom = tex_dom + '   PelisPlusHdLat: ' + pelisplushdlat_dominio + '[CR]'
           else: tex_dom = '[CR]   PelisPlusHdLat: ' + pelisplushdlat_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('pelisplushdnz')
    if datos['active']:
        pelisplushdnz_dominio = config.get_setting('channel_pelisplushdnz_dominio', default='')
        if pelisplushdnz_dominio:
           if tex_dom: tex_dom = tex_dom + '   PelisPlusHdNz: ' + pelisplushdnz_dominio + '[CR]'
           else: tex_dom = '[CR]   PelisPlusHdNz: ' + pelisplushdnz_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('pgratishd')
    if datos['active']:
        pgratishd_dominio = config.get_setting('channel_pgratishd_dominio', default='')
        if pgratishd_dominio:
           if tex_dom: tex_dom = tex_dom + '   PGratisHd: ' + pgratishd_dominio + '[CR]'
           else: tex_dom = '[CR]   PGratisHd: ' + pgratishd_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('playdede')
    if datos['active']:
        playdede_dominio = config.get_setting('channel_playdede_dominio', default='')
        if playdede_dominio:
           if tex_dom: tex_dom = tex_dom + '   PlayDede: ' + playdede_dominio + '[CR]'
           else: tex_dom = '[CR]   PlayDede: ' + playdede_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('poseidonhd2')
    if datos['active']:
        poseidonhd2_dominio = config.get_setting('channel_poseidonhd2_dominio', default='')
        if poseidonhd2_dominio:
           if tex_dom: tex_dom = tex_dom + '   PoseidonHd2: ' + poseidonhd2_dominio + '[CR]'
           else: tex_dom = '[CR]   PoseidonHd2: ' + poseidonhd2_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('series24')
    if datos['active']:
        series24_dominio = config.get_setting('channel_series24_dominio', default='')
        if series24_dominio:
           if tex_dom: tex_dom = tex_dom + '   Series24: ' + series24_dominio + '[CR]'
           else: tex_dom = '[CR]   Series24: ' + series24_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('serieskao')
    if datos['active']:
        serieskao_dominio = config.get_setting('channel_serieskao_dominio', default='')
        if serieskao_dominio:
           if tex_dom: tex_dom = tex_dom + '   SeriesKao: ' + serieskao_dominio + '[CR]'
           else: tex_dom = '[CR]   SeriesKao: ' + serieskao_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('seriespapayato')
    if datos['active']:
        seriespapayato_dominio = config.get_setting('channel_seriespapayato_dominio', default='')
        if seriespapayato_dominio:
           if tex_dom: tex_dom = tex_dom + '   SeriesPapayaTo: ' + seriespapayato_dominio + '[CR]'
           else: tex_dom = '[CR]   SeriesPapayaTo: ' + seriespapayato_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('seriesplus')
    if datos['active']:
        seriesplus_dominio = config.get_setting('channel_seriesplus_dominio', default='')
        if seriesplus_dominio:
           if tex_dom: tex_dom = tex_dom + '   SeriesPlus: ' + seriesplus_dominio + '[CR]'
           else: tex_dom = '[CR]   SeriesPlus: ' + seriesplus_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('srnovelas')
    if datos['active']:
        srnovelas_dominio = config.get_setting('channel_srnovelas_dominio', default='')
        if srnovelas_dominio:
           if tex_dom: tex_dom = tex_dom + '   SrNovelas: ' + srnovelas_dominio + '[CR]'
           else: tex_dom = '[CR]   SrNovelas: ' + srnovelas_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('subtorrents')
    if datos['active']:
        subtorrents_dominio = config.get_setting('channel_subtorrents_dominio', default='')
        if subtorrents_dominio:
           if tex_dom: tex_dom = tex_dom + '   SubTorrents: ' + subtorrents_dominio + '[CR]'
           else: tex_dom = '[CR]   SubTorrents: ' + subtorrents_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('todotorrents')
    if datos['active']:
        todotorrents_dominio = config.get_setting('channel_todotorrents_dominio', default='')
        if todotorrents_dominio:
           if tex_dom: tex_dom = tex_dom + '   TodoTorrents: ' + todotorrents_dominio + '[CR]'
           else: tex_dom = '[CR]   TodoTorrents: ' + todotorrents_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('vernovelas')
    if datos['active']:
        vernovelas_dominio = config.get_setting('channel_vernovelas_dominio', default='')
        if vernovelas_dominio:
           if tex_dom: tex_dom = tex_dom + '   VerNovelas: ' + vernovelas_dominio + '[CR]'
           else: tex_dom = '[CR]   VerNovelas: ' + vernovelas_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('veronline')
    if datos['active']:
        veronline_dominio = config.get_setting('channel_veronline_dominio', default='')
        if veronline_dominio:
           if tex_dom: tex_dom = tex_dom + '   VerOnline: ' + veronline_dominio + '[CR]'
           else: tex_dom = '[CR]   VerOnline: ' + veronline_dominio + '[CR]'

    datos = channeltools.get_channel_parameters('zonaleros')
    if datos['active']:
        zonaleros_dominio = config.get_setting('channel_zonaleros_dominio', default='')
        if zonaleros_dominio:
           if tex_dom: tex_dom = tex_dom + '   ZonaLeros: ' + zonaleros_dominio + '[CR]'
           else: tex_dom = '[CR]   ZonaLeros: ' + zonaleros_dominio + '[CR]'

    if tex_dom: txt += ' - [COLOR gold]Dominios:[/COLOR]  [COLOR springgreen]%s[/COLOR][CR]' % str(tex_dom)

    filtros = {'clusters': 'register'}

    ch_list = channeltools.get_channels_list(filtros=filtros)

    if ch_list:
        txt_ch = ''

        for ch in ch_list:
            username = config.get_setting(ch['id'] + '_username', ch['id'], default='')

            if not txt_ch: txt_ch = '[CR]'

            if not username: txt_ch  += '   ' + ch['name'] + ' [COLOR green][B]falta registrarse[/B][/COLOR][CR]'
            else: txt_ch  += '   ' + ch['name'] +  '[COLOR green][B] informadas[/B][/COLOR][CR]'

        if not txt_ch: txt_ch = 'No hay canales que requieran registrarse' 

        txt += ' - [COLOR gold]Credenciales:[/COLOR]  %s' % str(txt_ch)
        txt += '[CR]'

    filtros = {}

    ch_list = channeltools.get_channels_list(filtros=filtros)

    if ch_list:
        txt_ch = ''

        for ch in ch_list:
            if not ch['status'] == 1: continue

            txt_ch += ' [COLOR tan]%s[/COLOR][CR]  ' % ch['name']

        if not txt_ch: txt_ch = ' [COLOR white]No hay canales preferidos[/COLOR][CR]' 
        txt += ' - [COLOR gold]Canales Preferidos:[/COLOR][CR]  %s' % str(txt_ch)

        txt += '[CR]'

    filtros = {}

    ch_list = channeltools.get_channels_list(filtros=filtros)

    if ch_list:
        txt_ch = ''

        for ch in ch_list:
            if not ch['status'] == -1: continue

            txt_ch += ' [COLOR gray]%s[/COLOR][CR]  ' % ch['name']

        if not txt_ch: txt_ch = ' [COLOR white]No hay canales desactivados[/COLOR][CR]' 
        txt += ' - [COLOR gold]Desactivados:[/COLOR][CR]  %s' % str(txt_ch)

        txt += '[CR]'

    filtros = {}

    ch_list = channeltools.get_channels_list(filtros=filtros)

    if ch_list:
        txt_ch = ''

        for ch in ch_list:
            cfg_proxies_channel = 'channel_' + ch['id'] + '_proxies'

            if not config.get_setting(cfg_proxies_channel, default=''): continue

            txt_ch += ' [COLOR red]%s[/COLOR][CR]  ' % ch['name']

        if not txt_ch: txt_ch = ' [COLOR white]No hay canales con proxies[/COLOR][CR]' 
        txt += ' - [COLOR gold]Proxies:[/COLOR][CR]  %s' % str(txt_ch)

    if config.get_setting('search_included_all', default=''):
        incluidos = config.get_setting('search_included_all', default='')
        if incluidos:
            txt += '[CR] - [COLOR gold][B]Búsquedas: [COLOR greenyellow][B]Solo Determinados canales[/B][/COLOR] incluidos en [B][COLOR green]Todos[/COLOR][/B]'
            incluidos = scrapertools.find_multiple_matches(incluidos, "'(.*?)'")

            for incluido in incluidos:
                incluido = incluido.capitalize().strip()
                txt += '[CR]  [COLOR violet][B] ' + incluido + '[/B][/COLOR]'

            txt += '[CR]'

    txt_exc = ''

    if config.get_setting('search_excludes_movies', default=''):
        excluidos = config.get_setting('search_excludes_movies', default='')
        if excluidos:
            txt_exc += ' - [COLOR gold]Excluir Buscar:[/COLOR] [COLOR deepskyblue][B]en Películas[/B][/COLOR][CR'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt_exc += '  [COLOR yellow][B] ' + excluido + '[/B][/COLOR][CR]'

    if config.get_setting('search_excludes_tvshows', default=''):
        excluidos = config.get_setting('search_excludes_tvshows', default='')
        if excluidos:
            txt_exc += ' - [COLOR gold]Excluir Buscar:[/COLOR] COLOR hotpink][B] en Series[/B][/COLOR][CR'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt_exc += '  [COLOR yellow][B] ' + excluido + '[/B][/COLOR][CR]'

    if config.get_setting('search_excludes_documentaries', default=''):
        excluidos = config.get_setting('search_excludes_documentaries', default='')
        if excluidos:
            txt_exc += ' - [COLOR gold]Excluir Buscar:[/COLOR] [COLOR cyan][B en Documentales[/B][/COLOR][CR'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt_exc += '  [COLOR yellow][B] ' + excluido + '[/B][/COLOR][CR]'

    if config.get_setting('search_excludes_torrents', default=''):
        excluidos = config.get_setting('search_excludes_torrents', default='')
        if excluidos:
            txt_exc += ' - [COLOR gold]Excluir Buscar:[/COLOR] [COLOR blue][B] en Torrents[/B][/COLOR][CR'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt_exc += '  [COLOR yellow][B] ' + excluido + '[/B][/COLOR][CR]'

    if config.get_setting('search_excludes_mixed', default=''):
        excluidos = config.get_setting('search_excludes_mixed', default='')
        if excluidos:
            txt_exc += ' - [COLOR gold]Excluir Buscar:[/COLOR] [COLOR yellow][B] en Películas y/ó Series[/B][/COLOR][CR'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt_exc += '  [COLOR yellow][B] ' + excluido + '[/B][/COLOR][CR]'

    if config.get_setting('search_excludes_all', default=''):
        excluidos = config.get_setting('search_excludes_all', default='')
        if excluidos:
            txt_exc += ' - [COLOR gold]Excluir Buscar:[/COLOR] [COLOR green][B]en Todos[/B][/COLOR][CR]'
            excluidos = scrapertools.find_multiple_matches(excluidos, "'(.*?)'")

            for excluido in excluidos:
                excluido = excluido.capitalize().strip()
                txt_exc += '  [COLOR yellow][B] ' + excluido + '[/B][/COLOR][CR]'

    if txt_exc: txt += '[CR]' + txt_exc

    filtros = {'searchable': True}

    ch_list = channeltools.get_channels_list(filtros=filtros)

    if ch_list:
       txt_ch = ''

       for ch in ch_list:
           cfg_searchable_channel = 'channel_' + ch['id'] + '_no_searchable'

           if not config.get_setting(cfg_searchable_channel, default=False): continue

           txt_ch += '[CR]   [COLOR violet]%s[/COLOR]' % ch['name']

       if txt_ch: txt += '[CR] - [COLOR gold]Excluidos en Búsquedas:[/COLOR]  %s[CR]' % str(txt_ch)

    if not config.get_setting('mnu_simple', default=False):
        if config.get_setting('mnu_preferidos', default=True):
            txt += '[CR] - [COLOR wheat][B]Preferidos:[/B][/COLOR]'

            item.category = trackingtools.get_current_dbname()

            db = trackingtools.TrackingData()
            count_movies = db.get_movies_count()
            count_shows = db.get_shows_count()
            count_episodes = db.get_episodes_count()
            db.close()

            if (count_movies + count_shows + count_episodes) == 0: txt += '  [COLOR white]Aún no tiene[/COLOR][CR]'
            else: txt += '  [COLOR yellow]Hay preferidos[/COLOR][CR]'

        if config.get_setting('mnu_desargas', default=True):
            txt += '[CR] - [COLOR seagreen][B]Descargas:[/B][/COLOR]'

            download_path = config.get_setting('downloadpath', default='')
            if not download_path: download_path = filetools.join(config.get_data_path(), 'downloads')

            if not filetools.exists(download_path): filetools.mkdir(download_path)

            if download_path.startswith('smb://'):
                fichs = sorted(filetools.listdir(download_path))
                ficheros = [filetools.join(download_path, fit) for fit in fichs if fit.endswith('.json')]
            else:
                path = filetools.join(download_path, '*.json')
                ficheros = glob.glob(path)
                ficheros.sort(key=os.path.getmtime, reverse=False)

            if not ficheros: txt += '  [COLOR white]Aún no tiene[/COLOR][CR]'
            else: txt += '  [COLOR yellow]Hay descargas[CR][/COLOR]'

    if config.get_setting('autoplay_channels_discarded', default=''):
        txt += '[CR] -  [COLOR gold]Auto Play canales descartados:[/COLOR]'
        sin_autoplay = config.get_setting('autoplay_channels_discarded').split(',')

        for no_autoplay in sin_autoplay:
            no_autoplay = no_autoplay.lower().strip()
            txt += '[CR]   [COLOR gray][B] ' + no_autoplay + '[/B][/COLOR]'

        txt += '[CR]'

    if config.get_setting('servers_preferred', default='') or config.get_setting('servers_unfavored', default='') or config.get_setting('servers_discarded', default=''):
        txt += '[CR] -  [COLOR gold]Filtrar Servidores:[/COLOR]'

        if config.get_setting('servers_preferred', default=''):
            txt += '[CR][COLOR yellowgreen]    -  [/COLOR][COLOR darkorange]Servidores Preferidos[/COLOR]:'
            servers = config.get_setting('servers_preferred').split(',')

            for server in servers:
                server = server.lower().strip()
                txt += '[CR]      [COLOR gold] ' + server + '[/COLOR]'

            txt += '[CR]'

        if config.get_setting('servers_unfavored', default=''):
            txt += '[CR][COLOR yellowgreen]    -  [/COLOR][COLOR blue]Servidores como Última opción[/COLOR]:'
            servers = config.get_setting('servers_unfavored').split(',')

            for server in servers:
                server = server.lower().strip()
                txt += '[CR]       [COLOR blue] ' + server + '[/COLOR]'

            txt += '[CR]'

        if config.get_setting('servers_discarded', default=''):
            txt += '[CR][COLOR yellowgreen]    -  [/COLOR][COLOR gray]Servidores Descartados[/COLOR]:'
            servers = config.get_setting('servers_discarded').split(',')

            for server in servers:
                server = server.lower().strip()
                txt += '[CR]       [COLOR gray] ' + server + '[/COLOR]'

            txt += '[CR]'

    if config.get_setting('mnu_torrents', default=True):
        cliente_torrent = config.get_setting('cliente_torrent', default='Ninguno')
        if cliente_torrent == 'Ninguno': tex_tor = '[COLOR moccasin]Ninguno[/COLOR]'
        elif cliente_torrent == 'Seleccionar':  tex_tor = 'Seleccionar'
        else:
          tex_tor = ' ' + cliente_torrent
          cliente_torrent = 'plugin.video.' + cliente_torrent.lower()
          if xbmc.getCondVisibility('System.HasAddon("%s")' % cliente_torrent):
              cod_version = xbmcaddon.Addon(cliente_torrent).getAddonInfo("version").strip()
              tex_tor += '  [COLOR white]' + cod_version + '[/COLOR]'
          else: tex_tor += '  [COLOR red][B]No instalado[/B][/COLOR]'

        txt += '[CR] - [COLOR gold]Cliente/Motor torrent:[/COLOR]  %s' % tex_tor

    if xbmc.getCondVisibility('System.HasAddon("inputstream.adaptive")'):
        cod_version = xbmcaddon.Addon("inputstream.adaptive").getAddonInfo("version").strip()
        tex_ia = '  [COLOR white]' + cod_version + '[/COLOR]'
    else: tex_ia = '  [COLOR red][B]No instalado[/B][/COLOR]'

    txt += '[CR][CR] - [COLOR gold]InputStream Adaptive:[/COLOR]  %s' % tex_ia

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
        cod_version = xbmcaddon.Addon("plugin.video.youtube").getAddonInfo("version").strip()
        tex_yt = '  [COLOR white]' + cod_version + '[/COLOR]'
    else: tex_yt = '  [COLOR red][B]No instalado[/B][/COLOR]'

    txt += '[CR][CR] - [COLOR gold]YouTube Add-on:[/COLOR]  %s' % tex_yt

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        cod_version = xbmcaddon.Addon("script.module.resolveurl").getAddonInfo("version").strip()
        tex_mr = '  [COLOR white]' + cod_version + '[/COLOR]'
    else: tex_mr = '  [COLOR red][B]No instalado[/B][/COLOR]'

    txt += '[CR][CR] - [COLOR gold]ResolveUrl Script:[/COLOR]  %s' % tex_mr

    loglevel = config.get_setting('debug', 0)
    if loglevel == 0: tex_niv = '[COLOR white]Solo Errores[/COLOR]'
    elif loglevel == 1: tex_niv = '[COLOR white]Errores e Información[/COLOR]'
    else: tex_niv = '[COLOR white]Máxima Información[/COLOR]'

    txt += '[CR][CR] - [COLOR gold]Log:[/COLOR]  %s' % tex_niv

    tex_log = test_log(item)

    txt += '  ' + tex_log

    if config.get_setting('channels_proxies_memorized', default=''):
        memorizeds_ini = config.get_setting('channels_proxies_memorized', default='')
        memorizeds_fin = ''

        if memorizeds_ini:
            txt += '[CR][CR] - [COLOR gold]Proxies memorized:[/COLOR]'
            memorizeds = scrapertools.find_multiple_matches(memorizeds_ini, "'(.*?)'")

            for memorized in memorizeds:
                channel_json = memorized + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)
                existe = filetools.exists(filename_json)
                if not existe: continue

                datos = channeltools.get_channel_parameters(memorized)
                if not datos['active']: continue

                el_memorizado = "'" + memorized + "'"

                if not memorizeds_fin: memorizeds_fin = memorizeds_fin + el_memorizado
                else: memorizeds_fin = memorizeds_fin + ', ' + el_memorizado

                memorized = memorized.capitalize().strip()
                txt += '[CR]  [COLOR goldenrod] ' + memorized + '[/COLOR]'

            config.set_setting('channels_proxies_memorized', memorizeds_fin)

    if config.get_setting('proxysearch_excludes', default=''):
        excludes = config.get_setting('proxysearch_excludes', default='')
        if excludes:
            txt += '[CR][CR] - [COLOR gold]Global proxies excluidos:[/COLOR]'
            excludes = scrapertools.find_multiple_matches(excludes, "'(.*?)'")

            for exclude in excludes:
                exclude = exclude.capitalize().strip()
                txt += '[CR]  [COLOR yellow] ' + exclude + '[/COLOR]'

    if config.get_setting('developer_mode', default=False):
        txt += '[CR][CR][COLOR fuchsia]DESARROLLO[/COLOR][CR]'

        if not avisar:
            txt += ' - [COLOR crimson][B]Desarrollo:[/B][/COLOR]  [COLOR white]Opción habilitada[/COLOR]'
        else:
            txt += ' - [COLOR crimson][B]Falso Desarrollo:[/B][/COLOR]  [COLOR white]Opción habilitada[/COLOR]'

    plataforma = get_plataforma('')

    txt += plataforma

    txt_off = ''
    if '(fixes off)' in txt: txt_off = '[B][I][COLOR gray] (fixes off)[/COLOR][/I][/B]'

    txt_ver = config.get_addon_version().replace('.fix', '-Fix')

    text_dev = ''

    if not ult_ver:
        if not access_repo:
            platformtools.dialog_ok(config.__addon_name + ' Test del Sistema', '[COLOR cyan][B]Versión instalada [COLOR red][I]Sin Acceso al Repositorio [/I][/COLOR][COLOR yellow] ' + txt_ver + '[/B][/COLOR]' + txt_off, '[COLOR violet][B]Instale la última Versión del Repositorio [/COLOR][/B]')
        else:
           if not '-Fix' in txt:
               if config.get_setting('developer_mode', default=False):
                   if not avisar:
                       text_dev = ' [COLOR yellow][B]Desarrollo[/B][/COLOR]'
                   else:
                       text_dev = ' [COLOR yellow][B]Falso Desarrollo[/B][/COLOR]'

               if txt_off:
                  platformtools.dialog_ok(config.__addon_name + ' Test del Sistema' + text_dev, '[COLOR cyan][B]Versión instalada desfasada [/COLOR][COLOR yellow] ' + txt_ver + '[/B][/COLOR] [COLOR red][B][I]Sin Acceso a los Fixes[/I][/B]', '[COLOR violet][B]Espere a que el servidor de los Fixes esté de nuevo ON LINE[/COLOR][/B]')
               else:
                  platformtools.dialog_ok(config.__addon_name + ' Test del Sistema' + text_dev, '[COLOR cyan][B]Versión instalada desfasada [/COLOR][COLOR yellow] ' + txt_ver + '[/B][/COLOR]' + txt_off, '[COLOR violet][B]Instale la última Versión disponible del Add-On[/COLOR][/B]')
           else:
              if txt_off:
                  platformtools.dialog_ok(config.__addon_name + ' Test del Sistema' + text_dev, '[COLOR cyan][B]Versión instalada [COLOR red][I]Sin Acceso a los Fixes [/I][/COLOR][COLOR yellow] ' + txt_ver + '[/B][/COLOR]', '[COLOR violet][B]Espere a que el servidor de los Fixes esté de nuevo ON LINE[/COLOR][/B]')
    else:
       if txt_off:
           platformtools.dialog_ok(config.__addon_name + ' Test del Sistema' + text_dev, '[COLOR cyan][B]Versión instalada [COLOR red][I]Sin Acceso a los Fixes [/I][/COLOR][COLOR yellow] ' + txt_ver + '[/B][/COLOR]', '[COLOR violet][B]Espere a que el servidor de los Fixes esté de nuevo ON LINE[/COLOR][/B]')

    platformtools.dialog_textviewer('Test status sistema', txt)


def show_plataforma(item):
    logger.info()

    plataforma = get_plataforma('')

    txt = plataforma

    platformtools.dialog_textviewer('Información sobre su Plataforma', txt)


def get_plataforma(txt):
    logger.info()

    txt += '[CR][CR][COLOR fuchsia]PLATAFORMA[/COLOR][CR]'

    txt += ' - [COLOR yellow][B]Fecha:[/B][/COLOR]  [COLOR aquamarine]' + str(datetime.today()) + '[/COLOR][CR][CR]'

    kver = str(xbmc.getInfoLabel('System.BuildVersion'))

    txt += ' - [COLOR gold]Media center:[/COLOR]  [COLOR coral]%s[/COLOR][CR][CR]' % kver

    if kver.startswith('14.'): ver = '14 - Helix  NO soportado'
    elif kver.startswith('15.'): ver = '15 - Isengard  NO soportado'
    elif kver.startswith('16.'): ver = '16 - Jarvis  NO soportado'
    elif kver.startswith('17.'): ver = '17 - Krypton'
    elif kver.startswith('18.'): ver = '18 - Leia'
    elif kver.startswith('19.'): ver = '19 - Matrix'
    elif kver.startswith('20.'): ver = '20 - Nexus'
    elif kver.startswith('21.'): ver = '21 - Omega'
    elif kver.startswith('22.'): ver = '22 - Piers'

    else: ver = 'Desconocido'

    txt += ' - [COLOR gold][B]Versión:[/B][/COLOR]  [COLOR white]' + ver + '[/COLOR][CR][CR]'

    try:
       if xbmc.getCondVisibility("System.Platform.Android"): plat = 'Android'
       elif xbmc.getCondVisibility("System.Platform.Windows"): plat = 'Windows'
       elif xbmc.getCondVisibility("System.Platform.UWP"): plat = 'Windows'
       elif xbmc.getCondVisibility("System.Platform.Linux"): plat = 'Linux'
       elif xbmc.getCondVisibility("system.platform.Linux.RaspberryPi"): plat = 'Raspberry'
       elif xbmc.getCondVisibility("System.Platform.OSX"): plat = 'Osx'
       elif xbmc.getCondVisibility("System.Platform.IOS"): plat = 'Ios'
       elif xbmc.getCondVisibility("System.Platform.Darwin"): plat = 'Darwin'
       elif xbmc.getCondVisibility("System.Platform.Xbox"): plat = 'Xbox'
       elif xbmc.getCondVisibility("System.Platform.Tvos"): plat = 'Tvos'
       elif xbmc.getCondVisibility("System.Platform.Atv2"): plat = 'Atv2'
       else: plat = 'Desconocida'
    except:
        plat = '?'

    txt += ' - [COLOR gold][B]Plataforma:[/B][/COLOR]  [COLOR white]' + plat + '[/COLOR][CR][CR]'

    txt += ' - [COLOR gold]Release:[/COLOR]  [COLOR white]' + str(platform.release()) + '[/COLOR][CR]'

    txt += ' - [COLOR gold]Procesador:[/COLOR]  [COLOR white]' + str(platform.machine()) + '[/COLOR][CR]'

    txt += ' - [COLOR gold]Language:[/COLOR]  [COLOR white]' + str(xbmc.getInfoLabel('System.Language')) + '[/COLOR][CR]'

    txt += ' - [COLOR gold]Uso CPU:[/COLOR]  [COLOR white]' + str(xbmc.getInfoLabel('System.CpuUsage')) + '[/COLOR][CR]'

    plataforma = platform.uname()

    txt += ' - [COLOR gold]Sistema:[/COLOR][COLOR white]  %s-%s-%s[/COLOR][CR][CR]' % (str(plataforma[0]), str(plataforma[2]), str(plataforma[3]))

    txt += ' - [COLOR gold]Python:[/COLOR][COLOR white]  %s.%s.%s[/COLOR][CR][CR]' % (str(sys.version_info[0]), str(sys.version_info[1]), str(sys.version_info[2]))

    try:
        mem_tot = str(xbmc.getInfoLabel('System.Memory(total)')).replace('MB', ' MB').replace('KB', ' KB')
        txt += ' - [COLOR gold][B]Memoria Total:[/B][/COLOR][COLOR white] ' + mem_tot  + '[/COLOR][CR]'

        mem_free = str(xbmc.getInfoLabel('System.Memory(free)')).replace('MB', ' MB').replace('KB', ' KB')
        txt += ' - [COLOR gold][B]Memoria Libre:[/B][/COLOR][COLOR white] ' + mem_free  + '[/COLOR][CR]'
    except:
        pass
	
    path = translatePath(os.path.join('special://home/userdata', ''))

    file_advs = 'advancedsettings.xml'
    file = path + file_advs
    existe = filetools.exists(file)

    if existe:
        txt += '[CR] - [COLOR yellow][B]Advanced Settings:[/B][/COLOR][COLOR white] SI[/COLOR][CR]'

    file_pcfs = 'playercorefactory.xml'

    file = path + file_pcfs

    existe = filetools.exists(file)

    if existe:
        txt += '[CR] - [COLOR yellow][B]Player Core Factory:[/B][/COLOR][COLOR white] SI[/COLOR][CR]'

    path = translatePath(os.path.join('special://logpath/', ''))

    file_log = 'kodi.log'

    file = path + file_log

    existe = filetools.exists(file)

    if existe == False:
        files = filetools.listdir(path)
        for file_log in files:
            if file_log.endswith('.log') == True or file_log.endswith('.LOG') == True:
                file = path + file_log
                existe = filetools.exists(file)
                break

    if existe:
       size = filetools.getsize(file)

       txt += '[CR] - [COLOR cyan]Fichero Log:[/COLOR][COLOR white] ' + str(size)  + ' Bytes[/COLOR]'

    return txt


def show_last_fix(item):
    logger.info()

    path = os.path.join(config.get_runtime_path(), 'last_fix.json')

    existe = filetools.exists(path)
    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No hay fichero Fix[/COLOR][/B]' % color_infor)
        return

    txt = ''

    try:
       with open(path, 'r') as f: txt=f.read(); f.close()
    except:
        try: txt = open(path, encoding="utf8").read()
        except: pass

    if txt:
        tot_txt = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', txt)

        blk_channels = scrapertools.find_single_match(tot_txt, '"channels":(.*?)]')
        tot_channels = scrapertools.find_multiple_matches(blk_channels, '"(.*?)"')

        blk_core = scrapertools.find_single_match(tot_txt, '"core":(.*?)]')
        tot_core = scrapertools.find_multiple_matches(blk_core, '"(.*?)"')

        blk_lib = scrapertools.find_single_match(tot_txt, '"lib":(.*?)]')
        tot_lib = scrapertools.find_multiple_matches(blk_lib, '"(.*?)"')

        blk_modules = scrapertools.find_single_match(tot_txt, '"modules":(.*?)]')
        tot_modules = scrapertools.find_multiple_matches(blk_modules, '"(.*?)"')

        blk_platformcode = scrapertools.find_single_match(tot_txt, '"platformcode":(.*?)]')
        tot_platformcode = scrapertools.find_multiple_matches(blk_platformcode, '"(.*?)"')

        blk_resources = scrapertools.find_single_match(tot_txt, '"resources":(.*?)]')
        tot_resources = scrapertools.find_multiple_matches(blk_resources, '"(.*?)"')

        blk_root = scrapertools.find_single_match(tot_txt, '"root dir":(.*?)]')
        tot_root = scrapertools.find_multiple_matches(blk_root, '"(.*?)"')

        blk_servers = scrapertools.find_single_match(tot_txt, '"servers":(.*?)]')
        tot_servers = scrapertools.find_multiple_matches(blk_servers, '"(.*?)"')

        txt = txt.replace('{', '').replace('}', '').replace('[', '').replace(']', '').replace(',', '').replace('"', '').replace("'", '').strip()

        txt = txt.replace('addon_version:', '[COLOR cyan][B]Version:[/B][/COLOR]')
        txt = txt.replace('files:', '[COLOR yellowgreen][B]Archivos:[/B][/COLOR]')

        txt = txt.replace('channels:', '[COLOR yellow][B]Canales:[/B][/COLOR]')
        txt = txt.replace('core:', '[COLOR yellow][B]Core:[/B][/COLOR]')
        txt = txt.replace('lib:', '[COLOR yellow][B]Lib:[/B][/COLOR]')
        txt = txt.replace('modules:', '[COLOR yellow][B]Modules:[/B][/COLOR]')
        txt = txt.replace('platformcode:', '[COLOR yellow][B]Platformcode:[/B][/COLOR]')
        txt = txt.replace('resources:', '[COLOR yellow][B]Resources:[/B][/COLOR]')
        txt = txt.replace('root dir:', '[COLOR yellow][B]Root:[/B][/COLOR]')
        txt = txt.replace('servers:', '[COLOR yellow][B]Servidores:[/B][/COLOR]')

        txt = txt.replace('fix_version:', '[COLOR yellowgreen][B]Fichero Fix:[/B][/COLOR][CR]    [COLOR cyan][B]   Numero de Fix: [/B][/COLOR]')
        txt = txt.replace('hash:', '[COLOR slateblue][B]   Control Hash:    [/B][/COLOR]')

        tot_channels = len(tot_channels)
        tot_core = len(tot_core)
        tot_lib = len(tot_lib)
        tot_modules = len(tot_modules)
        tot_platformcode = len(tot_platformcode)
        tot_resources = len(tot_resources)
        tot_root = len(tot_root)
        tot_servers = len(tot_servers)

        tot_files = tot_channels + tot_core + tot_lib + tot_modules + tot_platformcode + tot_resources + tot_root + tot_servers

        txt += '[CR][COLOR yellow][B]       Total Ficheros:  [/B][/COLOR]' + str(tot_files)

        platformtools.dialog_textviewer('Información del último Fix instalado', txt)

def resumen_fix(item):
    logger.info()

    path = os.path.join(config.get_runtime_path(), 'last_fix.json')

    existe = filetools.exists(path)
    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No hay fichero Fix[/COLOR][/B]' % color_infor)
        return

    txt = ''
    res = ''

    try:
       with open(path, 'r') as f: txt=f.read(); f.close()
    except:
        try: txt = open(path, encoding="utf8").read()
        except: pass

    if txt:
        tot_txt = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', txt)

        blk_channels = scrapertools.find_single_match(tot_txt, '"channels":(.*?)]')

        if blk_channels:
            blk_channels = blk_channels.replace('{', '').replace('}', '').replace('[', '').replace(']', '').strip()

            blk_channels = blk_channels + ','

            res_channels = scrapertools.find_multiple_matches(str(blk_channels), '(.*?),')

            res += '[COLOR goldenrod][B]Canales Modificados:[/B][/COLOR][CR]'

            for channel in res_channels:
                channel = channel.replace('"', '')

                txt = ''

                datos = channeltools.get_channel_parameters(channel)

                if not datos['active']:
                    txt = '  [COLOR red][B]Desactivado[/B][/COLOR]'

                    if 'temporary' in datos['clusters']:
                        txt += ' [COLOR yellow][B]Temporalmente[/B][/COLOR]'

                res += '  [COLOR cyan][B]' + datos['name'] + '[/B][/COLOR]' + txt + '[CR]'

            res += '[CR]'

        blk_servers = scrapertools.find_single_match(tot_txt, '"servers":(.*?)]')

        if blk_servers:
            blk_servers = blk_servers.replace('{', '').replace('}', '').replace('[', '').replace(']', '').strip()

            blk_servers = blk_servers + ','

            res_servers = scrapertools.find_multiple_matches(str(blk_servers), '(.*?),')

            res += '[COLOR goldenrod][B]Servidores Modificados:[/B][/COLOR][CR]'

            for server in res_servers:
                server = server.replace('"', '')

                txt = ''

                path_server = os.path.join(config.get_runtime_path(), 'servers', server)

                data = filetools.read(path_server + '.json')
                dict_server = jsontools.load(data)

                if dict_server['active'] == False:
                    txt = '  [COLOR red][B]Desactivado[/B][/COLOR]'

                res += '  [COLOR cyan][B]' + dict_server['name'] + '[/B][/COLOR]' + txt + '[CR]'

        if not blk_channels and not blk_servers:
            platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No hay Resumen del Fix[/COLOR][/B]' % color_infor)
            return

        platformtools.dialog_textviewer('Resumen Fix Instalado', res)


def show_sets(item):
    logger.info()

    file_sets = os.path.join(config.get_data_path(), "settings.xml")

    existe = filetools.exists(file_sets)

    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No existe settings.xml[/COLOR][/B]' % color_alert)
        return

    if platformtools.dialog_yesno(config.__addon_name, '[COLOR cyan][B]¿ Desea Anular las Preferencias Obsoletas en sus Ajustes ?[/B][/COLOR]'):
        channels_proxies_memorized = config.get_setting('channels_proxies_memorized')

        filtros = {'active': False}

        ch_list = channeltools.get_channels_list(filtros=filtros)

        i = 0

        for ch in ch_list:
            if config.get_setting('channel_' + ch['id'] + '_status'):
                i += 1
                config.set_setting('channel_' + ch['id'] + '_status', '')

            if config.get_setting('show_help_' + ch['id']):
                i += 1
                config.set_setting('show_help_' + ch['id'], '')
           
            if 'proxies' in ch['notes'].lower():
                cfg_proxies_channel = 'channel_' + ch['id'] + '_proxies'

                if config.get_setting(cfg_proxies_channel, default=''):
                    i += 1
                    config.set_setting(cfg_proxies_channel, '')
                    config.set_setting('channel_' + ch['id'] + '_proxytools_max', '')
                    config.set_setting('channel_' + ch['id'] + '_proxytools_pais', '')
                    config.set_setting('channel_' + ch['id'] + '_proxytools_provider', '')
                    config.set_setting('channel_' + ch['id'] + '_proxytools_tipo', '')

                if channels_proxies_memorized:
                    el_memorizado = "'" + ch['id'] + "'"

                    if el_memorizado in str(channels_proxies_memorized):
                        i += 1
                        channels_proxies_memorized = str(channels_proxies_memorized).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                        config.set_setting('channels_proxies_memorized', channels_proxies_memorized)

            if config.get_setting('opc_' + ch['id']):
                i += 1
                config.set_setting('opc_' + ch['id'], '')

            if config.get_setting('ac_' + ch['id']):
                i += 1
                config.set_setting('ac_' + ch['id'], '')

            if config.get_setting('last_domain_' + ch['id']):
                i += 1
                config.set_setting('last_domain_' + ch['id'], '')

            if config.get_setting('ch_' + ch['id'] + '_test'):
                i += 1
                config.set_setting('ch_' + ch['id'] + '_test', '')

            if config.get_setting('ch_' + ch['id'] + '_dominio'):
                i += 1
                config.set_setting('ch_' + ch['id'] + '_dominio', '')

            if config.get_setting('operative_domains_' + ch['id']):
                i += 1
                config.set_setting('operative_domains_' + ch['id'], '')

            if config.get_setting('channel_' + ch['id'] + '_no_searchable'):
                i += 1
                config.set_setting('channel_' + ch['id'] + '_no_searchable', '')

        if channels_proxies_memorized:
            memorizeds = scrapertools.find_multiple_matches(channels_proxies_memorized, "'(.*?)'")

            for memorized in memorizeds:
                memorized = memorized.lower().strip()

                channel_json = memorized + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)
                existe = filetools.exists(filename_json)
                if not existe: continue

                datos = channeltools.get_channel_parameters(memorized)
                if datos['active']:
                    if 'proxies' in datos['notes'].lower():
                        cfg_proxies_channel = 'channel_' + memorized + '_proxies'

                        if not config.get_setting(cfg_proxies_channel, default=''):
                            el_memorizado = "'" + memorized + "'"

                            i += 1
                            channels_proxies_memorized = str(channels_proxies_memorized).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                            config.set_setting('channels_proxies_memorized', channels_proxies_memorized)
                    continue

                el_memorizado = "'" + memorized + "'"

                i += 1
                channels_proxies_memorized = str(channels_proxies_memorized).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('channels_proxies_memorized', channels_proxies_memorized)

        if config.get_setting('autoplay_channels_discarded'):
            channels_autoplay = config.get_setting('autoplay_channels_discarded')

            sin_autoplay = config.get_setting('autoplay_channels_discarded').split(',')

            for no_autoplay in sin_autoplay:
                no_autoplay = no_autoplay.lower().strip()

                channel_json = no_autoplay + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)
                existe = filetools.exists(filename_json)
                if not existe: continue

                datos = channeltools.get_channel_parameters(no_autoplay)
                if datos['active']: continue

                i += 1
                channels_autoplay = str(channels_autoplay).replace(no_autoplay + ',', '').replace(no_autoplay, '').strip()
                config.set_setting('autoplay_channels_discarded', channels_autoplay)

        if config.get_setting('search_included_all'):
            channels_included_all = config.get_setting('search_included_all')

            includes = str(channels_included_all).replace('[', '').replace(']', ',')

            includes = scrapertools.find_multiple_matches(includes, "'(.*?)'")

            for include in includes:
                include = include.lower().strip()

                channel_json = include + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)
                existe = filetools.exists(filename_json)
                if not existe: continue

                datos = channeltools.get_channel_parameters(include)
                if datos['active']: continue

                el_memorizado = "'" + include + "'"

                i += 1
                channels_included_all = str(channels_included_all).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('search_included_all', channels_included_all)

        if config.get_setting('search_excludes_all'):
            search_excludes_all = config.get_setting('search_excludes_all')

            excludes = str(search_excludes_all).replace('[', '').replace(']', ',')

            excludes = scrapertools.find_multiple_matches(excludes, "'(.*?)'")

            for exclude in excludes:
                exclude = exclude.lower().strip()

                channel_json = exclude + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)
                existe = filetools.exists(filename_json)
                if not existe: continue

                datos = channeltools.get_channel_parameters(exclude)
                if datos['active']: continue

                el_memorizado = "'" + exclude + "'"

                i += 1
                search_excludes_all = str(search_excludes_all).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('search_excludes_all', search_excludes_all)

        if config.get_setting('search_excludes_movies'):
            search_excludes_movies = config.get_setting('search_excludes_movies')

            excludes = str(search_excludes_movies).replace('[', '').replace(']', ',')

            excludes = scrapertools.find_multiple_matches(excludes, "'(.*?)'")

            for exclude in excludes:
                exclude = exclude.lower().strip()

                channel_json = exclude + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)
                existe = filetools.exists(filename_json)
                if not existe: continue

                datos = channeltools.get_channel_parameters(exclude)
                if datos['active']: continue

                el_memorizado = "'" + exclude + "'"

                i += 1
                search_excludes_movies = str(search_excludes_movies).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('search_excludes_movies', search_excludes_movies)

        if config.get_setting('search_excludes_tvshows'):
            search_excludes_tvshows = config.get_setting('search_excludes_tvshows')

            excludes = str(search_excludes_tvshows).replace('[', '').replace(']', ',')

            excludes = scrapertools.find_multiple_matches(excludes, "'(.*?)'")

            for exclude in excludes:
                exclude = exclude.lower().strip()

                channel_json = exclude + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)
                existe = filetools.exists(filename_json)
                if not existe: continue

                datos = channeltools.get_channel_parameters(exclude)
                if datos['active']: continue

                el_memorizado = "'" + exclude + "'"

                i += 1
                search_excludes_tvshows = str(search_excludes_tvshows).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('search_excludes_tvshows', search_excludes_tvshows)

        if config.get_setting('search_excludes_documentaries'):
            search_excludes_documentaries = config.get_setting('search_excludes_documentaries')

            excludes = str(search_excludes_documentaries).replace('[', '').replace(']', ',')

            excludes = scrapertools.find_multiple_matches(excludes, "'(.*?)'")

            for exclude in excludes:
                exclude = exclude.lower().strip()

                channel_json = exclude + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)
                existe = filetools.exists(filename_json)
                if not existe: continue

                datos = channeltools.get_channel_parameters(exclude)
                if datos['active']: continue

                el_memorizado = "'" + exclude + "'"

                i += 1
                search_excludes_documentaries = str(search_excludes_documentaries).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('search_excludes_documentaries', search_excludes_documentaries)

        if config.get_setting('search_excludes_torrents'):
            search_excludes_torrents = config.get_setting('search_excludes_torrents')

            excludes = str(search_excludes_torrents).replace('[', '').replace(']', ',')

            excludes = scrapertools.find_multiple_matches(excludes, "'(.*?)'")

            for exclude in excludes:
                exclude = exclude.lower().strip()

                channel_json = exclude + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)
                existe = filetools.exists(filename_json)
                if not existe: continue

                datos = channeltools.get_channel_parameters(exclude)
                if datos['active']: continue

                el_memorizado = "'" + exclude + "'"

                i += 1
                search_excludes_torrents = str(search_excludes_torrents).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('search_excludes_torrents', search_excludes_torrents)

        if config.get_setting('search_excludes_mixed'):
            search_excludes_mixed = config.get_setting('search_excludes_mixed')

            excludes = str(search_excludes_mixed).replace('[', '').replace(']', ',')

            excludes = scrapertools.find_multiple_matches(excludes, "'(.*?)'")

            for exclude in excludes:
                exclude = exclude.lower().strip()

                channel_json = exclude + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)
                existe = filetools.exists(filename_json)
                if not existe: continue

                datos = channeltools.get_channel_parameters(exclude)
                if datos['active']: continue

                el_memorizado = "'" + exclude + "'"

                i += 1
                search_excludes_mixed = str(search_excludes_mixed).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('search_excludes_mixed', search_excludes_mixed)

        if config.get_setting('servers_preferred', default=''):
            servers_preferred = config.get_setting('servers_preferred')

            servers = scrapertools.find_multiple_matches(servers, "'(.*?)'")

            for server in servers:
                server_id = server.lower().strip()

                server_json = server_id + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'servers', server_json)

                try:
                    data = filetools.read(filename_json)
                    dict_server = jsontools.load(data)
                except:
                    continue

                if dict_server['active'] == False: continue

                el_memorizado = "'" + server + "'"

                i += 1
                servers_preferred = str(servers_preferred).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('servers_preferred', servers_preferred)

        if config.get_setting('servers_unfavored', default=''):
            servers_unfavored = config.get_setting('servers_unfavored')

            servers = scrapertools.find_multiple_matches(servers, "'(.*?)'")

            for server in servers:
                server_id = server.lower().strip()

                server_json = server_id + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'servers', server_json)

                try:
                    data = filetools.read(filename_json)
                    dict_server = jsontools.load(data)
                except:
                    continue

                if dict_server['active'] == False: continue

                el_memorizado = "'" + server + "'"

                i += 1
                servers_unfavored = str(servers_unfavored).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('servers_unfavored', servers_unfavored)

        if config.get_setting('servers_discarded', default=''):
            servers_discarded = config.get_setting('servers_discarded')

            servers = scrapertools.find_multiple_matches(servers, "'(.*?)'")

            for server in servers:
                server_id = server.lower().strip()

                server_json = server_id + '.json'
                filename_json = os.path.join(config.get_runtime_path(), 'servers', server_json)

                try:
                    data = filetools.read(filename_json)
                    dict_server = jsontools.load(data)
                except:
                    continue

                if dict_server['active'] == False: continue

                el_memorizado = "'" + server + "'"

                i += 1
                servers_discarded = str(servers_discarded).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                config.set_setting('servers_discarded', servers_discarded)

        if i == 0: platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Sin Preferencias Obsoletas[/B][/COLOR]' % color_exec)
        else: platformtools.dialog_ok(config.__addon_name, '[B][COLOR %s]Anuladas las Preferencias Obsoletas en sus Ajustes Personalizados.[/B][/COLOR]' % color_avis)

    txt = ''

    try:
        with open(os.path.join(file_sets), 'r') as f:txt=f.read(); f.close()
    except:
        try: txt = open(os.path.join(file_sets), encoding="utf8").read()
        except: pass

    txt = txt.replace('">true</setting>', '">[COLOR crimson][B]True[/B][/COLOR]</setting>')

    if txt: platformtools.dialog_textviewer('Su fichero de Ajustes personalizados', txt)


def show_cook(item):
    logger.info()

    file_cook = os.path.join(config.get_data_path(), "cookies.dat")

    existe = filetools.exists(file_cook)

    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No existe cookies.dat[/COLOR][/B]' % color_adver)
        return

    txt = ''

    try:
        with open(os.path.join(file_cook), 'r') as f: txt=f.read(); f.close()
    except:
        try: txt = open(os.path.join(file_cook), encoding="utf8").read()
        except: pass

    if txt: platformtools.dialog_textviewer('Su fichero de Cookies', txt)
