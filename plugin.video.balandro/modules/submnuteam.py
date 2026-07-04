# -*- coding: utf-8 -*-

import os, sys, xbmc, xbmcgui, xbmcaddon

from platformcode import logger, config, platformtools, updater
from core import jsontools, filetools, scrapertools

from core.item import Item

from modules import filters


PY3 = False
if config.get_setting('PY3', default=''): PY3 = True

if PY3:
    import xbmcvfs
    translatePath = xbmcvfs.translatePath
else:
    import xbmc
    translatePath = xbmc.translatePath


ant_repos = ['4.0.0', '3.0.0', '2.0.0', '1.0.5', '1.0.3'] 


color_list_prefe = config.get_setting('channels_list_prefe_color', default='gold')
color_list_proxies = config.get_setting('channels_list_proxies_color', default='red')
color_list_inactive = config.get_setting('channels_list_inactive_color', default='gray')

color_alert = config.get_setting('notification_alert_color', default='red')
color_infor = config.get_setting('notification_infor_color', default='pink')
color_adver = config.get_setting('notification_adver_color', default='violet')
color_avis = config.get_setting('notification_avis_color', default='yellow')
color_exec = config.get_setting('notification_exec_color', default='cyan')


search_no_accesibles = config.get_setting('search_no_accesibles', default=False)


_foro = "[COLOR plum][B][I] www.mimediacenter.info/foro/ [/I][/B][/COLOR]"
_telegram = "[COLOR lightblue][B][I] t.me/balandro_asesor [/I][/B][/COLOR]"

_scripts = "[COLOR mediumaquamarine][B][I] https://repobal.github.io/base/scripts/ [/I][/B][/COLOR]"

_team = "[COLOR hotpink][B][I] t.me/balandro_team [/I][/B][/COLOR]"

tests_all_webs = []
tests_all_srvs = []

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

    if con_problemas:
        hay_problemas = str(con_problemas).replace('[B][COLOR moccasin]', 'CHANNEL').replace('[COLOR lime]', '/CHANNEL')
        channels_con_problemas = scrapertools.find_multiple_matches(hay_problemas, "CHANNEL(.*?)/CHANNEL")


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

tit = '[COLOR darkorange]Información Dominios[/COLOR]'
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

tit = '[COLOR %s][B]Cookies Actuales[/B][/COLOR]' % color_infor
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_cook'})

tit = '[COLOR %s][B]Eliminar Cookies[/B][/COLOR]' % color_infor
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_cookies'})

tit = '[COLOR %s]Sus Advanced Settings[/COLOR]' % color_adver
context_config.append({'title': tit, 'channel': 'helper', 'action': 'show_advs'})

tit = '[COLOR fuchsia][B]Eliminar Advanced Settings[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_advs'})

tit = '[COLOR mediumaquamarine][B]Restablecer Parámetros Internos[/B][/COLOR]'
context_config.append({'title': tit, 'channel': 'actions', 'action': 'manto_params'})

context_proxy_channels = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_proxy_channels.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR mediumaquamarine][B]Últimos Cambios Dominios[/B][/COLOR]'
context_proxy_channels.append({'title': tit, 'channel': 'actions', 'action': 'show_latest_domains'})

tit = '[COLOR darkcyan][B]Preferencias Proxies[/B][/COLOR]'
context_proxy_channels.append({'title': tit, 'channel': 'helper', 'action': 'show_prx_parameters'})

tit = '[COLOR powderblue][B]Global Configurar Proxies[/B][/COLOR]'
context_proxy_channels.append({'title': tit, 'channel': 'proxysearch', 'action': 'proxysearch_all'})

if config.get_setting('proxysearch_excludes', default=''):
    tit = '[COLOR %s]Anular canales excluidos de Proxies[/COLOR]' % color_adver
    context_proxy_channels.append({'title': tit, 'channel': 'proxysearch', 'action': 'channels_proxysearch_del'})

tit = '[COLOR %s]Información Proxies[/COLOR]' % color_avis
context_proxy_channels.append({'title': tit, 'channel': 'helper', 'action': 'show_help_proxies'})

tit = '[COLOR %s][B]Quitar los Proxies Actuales[/B][/COLOR]' % color_list_proxies
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

tit = '[COLOR %s][B]Quitar los Proxies Actuales[/B][/COLOR]' % color_list_proxies
context_usual.append({'title': tit, 'channel': 'actions', 'action': 'manto_proxies'})

tit = '[COLOR %s]Ajustes categorías Canales, Dominios y Proxies[/COLOR]' % color_exec
context_usual.append({'title': tit, 'channel': 'actions', 'action': 'open_settings'})

context_ayuda = []

tit = '[COLOR tan][B]Preferencias Menús[/B][/COLOR]'
context_ayuda.append({'title': tit, 'channel': 'helper', 'action': 'show_menu_parameters'})

tit = '[COLOR darkorange]Información Dominios[/COLOR]'
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
    context_ayuda.append({'title': tit, 'channel': 'actions', 'action': 'resumen_fix'})

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


def submnu_team(item):
    logger.info()
    itemlist = []

    avisar = False

    if not config.get_setting('developer_team'): avisar = True

    if not avisar:
        titulo = '[B]DESARROLLO:[/B]'
    else:
        titulo = '[B]FALSO DESARROLLO:[/B]'

    itemlist.append(item.clone( action='', title=titulo, thumbnail=config.get_thumb('team'), text_color='darkorange' ))

    itemlist.append(item.clone( action='submnu_team_info', title='[COLOR green][B]Información[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    if not config.get_setting('mnu_simple', default=False): tit_mnu = '[B][I]Menú Desarrollo:[/I][/B]'
    else: tit_mnu = '[B][I]Menú Desarrollo Simplificado:[/I][/B]'

    itemlist.append(item.clone( action='', title=tit_mnu, context=context_desarrollo, text_color='darkorange' ))

    itemlist.append(item.clone( channel='helper', action='submnu_clean', title= ' - [B]Limpiezas[/B]', text_color='olive', thumbnail=config.get_thumb('quote') ))

    itemlist.append(item.clone( action='submnu_center', title=' - [B]Media Center[/B]', context=context_config, thumbnail=config.get_thumb('mediacenter'), text_color='pink' ))

    itemlist.append(item.clone( action='submnu_addons', title=' - [B]Add-Ons[/B]', thumbnail=config.get_thumb('kodiaddons'), text_color='yellowgreen' ))

    itemlist.append(item.clone( action='submnu_sistema', title=' - [B]Sistema[/B]', context=context_ayuda, thumbnail=config.get_thumb('computer'), text_color='violet' ))

    presentar = False

    if os.path.exists(os.path.join(config.get_data_path(), 'servers_todo.log')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'qualities_todo.log')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'proxies.log')): presentar = True

    if presentar:
        itemlist.append(item.clone( action='submnu_logs', title=' - [B]Logs[/B]', thumbnail=config.get_thumb('tools'), text_color='limegreen' ))

    presentar = False

    if os.path.exists(os.path.join(config.get_data_path(), 'info_channels.csv')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'temp.torrent')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'm3u8hls.m3u8')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'blenditall.m3u8')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'test_logs')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'temp_updates.zip')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'tempfile_mkdtemp')): presentar = True

    if presentar:
        itemlist.append(item.clone( action='submnu_temporales', title=' - [B]Temporales[/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

    presentar = False

    if config.get_setting('developer_team'): presentar = True

    if presentar:
        itemlist.append(item.clone( action='submnu_gestionar', title=' - [B]Gestionar[/B]', thumbnail=config.get_thumb('tools'), text_color='teal' ))

    if not config.get_setting('mnu_simple', default=False):
        itemlist.append(item.clone( action='submnu_proxies', title=' - [B]Tests Proxies[/B]', context=context_proxy_channels, thumbnail=config.get_thumb('flame'), text_color='red' ))

    itemlist.append(item.clone( action='submnu_canales', title=' - [B]Tests Canales[/B]', context=context_usual, thumbnail=config.get_thumb('stack'), text_color='gold' ))
    itemlist.append(item.clone( action='submnu_servidores', title=' - [B]Tests Servidores[/B]', thumbnail=config.get_thumb('bolt'), text_color='fuchsia' ))

    itemlist.append(item.clone( action='submnu_developers', title=' - [B]Developers[/B]', context=context_desarrollo, thumbnail=config.get_thumb('team'), text_color='firebrick' ))

    try: last_ver = updater.check_addon_version()
    except: last_ver = None

    if last_ver is None: last_ver = '[B][I][COLOR gray](fixes off)[/COLOR][/I][/B]'
    elif not last_ver:
          tex_dev = ''

          if config.get_setting('developer_mode', default=False):
              tex_dev = '[COLOR darkorange][B]Desarrollo[/B][/COLOR]'
              if not config.get_setting('developer_team'): tex_dev = '[COLOR darkorange][B]Falso Desarrollo[/B][/COLOR]'

          last_ver = '[B][I][COLOR %s](desfasada)[/COLOR][/I][/B]' % color_adver
          last_ver = last_ver + '  '  + tex_dev
    else: last_ver = ''

    title = '[COLOR chocolate][B]Ajustes [COLOR powderblue]Preferencias[/B][/COLOR] (%s)  %s' % (config.get_addon_version().replace('.fix', '-Fix'), last_ver)

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title=title, context=context_config, thumbnail=config.get_thumb('settings'), text_color='chocolate' ))

    return itemlist


def submnu_team_info(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR green][B]INFORMACIÓN[/COLOR] [COLOR darkorange]DESARROLLO:[/COLOR][/B]' ))

    itemlist.append(item.clone( channel='helper', action='show_msgfixed', title= '[COLOR chartreuse][B]Mensajes Fijados[/B][/COLOR] Telegram Balandro Asesor', thumbnail=config.get_thumb('telegram') ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title='[COLOR aqua][B]Últimos Cambios Dominios[/B][/COLOR]' ))

    itemlist.append(item.clone( action='', title='[COLOR gold][I][B]CANALES:[/B][/I][/COLOR]', thumbnail=config.get_thumb('stack') ))

    if txt_status:
        if con_incidencias:
            itemlist.append(item.clone( action='resumen_incidencias', title=' - [COLOR tan][B] Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

        if no_accesibles:
            itemlist.append(item.clone( action='resumen_no_accesibles', title=' - [COLOR indianred][B] No Accesibles[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

        if con_problemas:
            itemlist.append(item.clone( action='resumen_con_problemas', title=' - [COLOR tomato][B] Con Problemas[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='helper', action='channels_with_crypto', title= ' - [COLOR darksalmon][B] Descifrar Enlaces[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    if config.get_setting('memorize_channels_proxies', default=True):
        itemlist.append(item.clone( channel='helper',  action='channels_with_proxies_memorized', title= ' - [COLOR red][B] Con Proxies[/B][/COLOR]', new_proxies=True, memo_proxies=True, test_proxies=True, thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='test_one_channel', title= ' - [COLOR springgreen][B] Temporalmente Inactivos[/B][/COLOR]', temp_no_active = True, thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='resumen_canales', title=' - [COLOR gold][B] Resúmenes y Distribución[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='', title='[COLOR fuchsia][I][B]SERVIDORES:[/B][/I][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( action='resumen_servidores', title=' - [COLOR fuchsia][B]Resúmenes y Distribución[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    if txt_status:
        if srv_pending:
            itemlist.append(item.clone( action='resumen_pending', title='[COLOR tan][B] - Con Incidencias[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        itemlist.append(item.clone( action='show_help_alternativas', title=' - Qué servidores tienen [COLOR yellow][B]Vías Alternativas[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))
        itemlist.append(item.clone( action='show_help_adicionales', title=' - Servidores [COLOR goldenrod][B]Vías Adicionales[/B][/COLOR] a través de [COLOR yellowgreen][B]ResolveUrl[/B][/COLOR]', thumbnail=config.get_thumb('resolveurl') ))

    return itemlist


def submnu_center(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]MEDIA CENTER:[/B]', thumbnail=config.get_thumb('mediacenter'), text_color='pink' ))

    if not item.helper:
        itemlist.append(item.clone( action='submnu_center_info', title='[COLOR green][B]Información[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='', title='[B][I]TESTS:[/I][/B]', text_color='pink' ))

    itemlist.append(item.clone( channel='helper', action='show_plataforma', title=' - [COLOR gold][B]Plataforma[/B][/COLOR]', thumbnail=config.get_thumb('mediacenter') ))

    itemlist.append(item.clone( channel='actions', action = 'test_internet', title= '- Comprobar [COLOR goldenrod][B]Internet[/B][/COLOR]', thumbnail=config.get_thumb('crossroads') ))

    path = translatePath(os.path.join('special://home/', ''))

    crashes = filetools.listdir(path)

    hay_crashes = False

    for file in crashes:
        if file.endswith('.dmp') == True or file.endswith('.txt') == True: hay_crashes = True

    if hay_crashes:
        itemlist.append(item.clone( action='', title='[B][I]CRASHES:[/I][/B]', text_color='pink' ))

        itemlist.append(item.clone( channel='helper', action='show_crashes', title=' - Ver', thumbnail=config.get_thumb('computer'), text_color='yellow' ))

        itemlist.append(item.clone( channel='actions', action='manto_crashes', title=' - Eliminar', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    path = translatePath(os.path.join('special://home/userdata', ''))

    file_advs = 'advancedsettings.xml'
    file = path + file_advs
    existe = filetools.exists(file)

    if existe:
        itemlist.append(item.clone( action='', title='[B][I]ADVANCED SETTINGS:[/I][/B]', text_color='pink' ))

        itemlist.append(item.clone( channel='helper', action='show_advs', title=' - Ver', thumbnail=config.get_thumb('computer'), text_color='yellow' ))

        itemlist.append(item.clone( channel='actions', action='manto_advs', title=' - Eliminar [B][COLOR violet](Si ejecuta es Recomendable Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

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

    if existe:
        itemlist.append(item.clone( action='', title='[B][I]FAVOURITES SETTINGS:[/I][/B]', text_color='pink' ))

        itemlist.append(item.clone( channel='helper', action='show_favs', title=' - Ver', thumbnail=config.get_thumb('computer'), text_color='yellow' ))
        itemlist.append(item.clone( channel='actions', action='manto_favs', title=' - Eliminar', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    file_pcfs = 'playercorefactory.xml'
    file = path + file_pcfs
    existe = filetools.exists(file)

    if existe:
        itemlist.append(item.clone( action='', title='[B][I]PLAYERCOREFACTORY SETTINGS:[/I][/B]', text_color='pink' ))

        itemlist.append(item.clone( channel='helper', action='show_pcfs', title=' - Ver', thumbnail=config.get_thumb('computer'), text_color='yellow' ))

        itemlist.append(item.clone( channel='actions', action='manto_pcfs', title=' - Eliminar [B][COLOR violet](Si ejecuta es Recomendable Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    presentar = False

    path_cache = translatePath(os.path.join('special://temp/archive_cache', ''))
    existe_cache = filetools.exists(path_cache)

    caches = []
    if existe_cache: caches = os.listdir(path_cache)

    if caches: presentar = True

    if presentar:
        itemlist.append(item.clone( action='', title='[B][I]ARCHIVOS CACHÉ:[/I][/B]', text_color='pink' ))

        itemlist.append(item.clone( action='show_addons', title=' - Ver', addons = caches, tipo = 'Caché', thumbnail=config.get_thumb('computer'), text_color='yellow' ))

        itemlist.append(item.clone( channel='actions', action='manto_caches', title=' - Eliminar [B][COLOR cyan](Si ejecuta es Obligatorio Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    path_thumbs = translatePath(os.path.join('special://home/userdata/Thumbnails', ''))
    existe_thumbs = filetools.exists(path_thumbs)

    if existe_thumbs:
        itemlist.append(item.clone( action='', title='[B][I]ARCHIVOS THUMBNAILS:[/I][/B]', text_color='pink' ))

        itemlist.append(item.clone( channel='actions', action='manto_thumbs', title=' - Eliminar [B][COLOR cyan](Si ejecuta es Obligatorio Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    if item.helper: platformtools.itemlist_refresh()

    if not itemlist:
        if item.helper:
            platformtools.dialog_notification(config.__addon_name + ' [COLOR olive][B]Media Center[/B][/COLOR]', '[B][COLOR cyan]Nada que Limpiar[/B][/COLOR]')
            return

    return itemlist


def submnu_center_info(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR green][B]INFORMACIÓN[/COLOR] [COLOR pink]MEDIA CENTER:[/COLOR][/B]' ))

    itemlist.append(item.clone( action='', title='[B][I]LOG BALANDRO:[/I][/B]', thumbnail=config.get_thumb('computer'), text_color='pink' ))

    itemlist.append(item.clone( action='balandro_log', title=' - Ver Log ejecución Balandro', thumbnail=config.get_thumb('computer'), text_color='coral' ))

    itemlist.append(item.clone( action='', title='[B][I]LOG GENERAL:[/I][/B]', thumbnail=config.get_thumb('computer'), text_color='pink' ))

    itemlist.append(item.clone( channel='helper', action='show_log', title=' - Ver Log', thumbnail=config.get_thumb('computer'), text_color='yellow' ))
    itemlist.append(item.clone( channel='helper', action='copy_log', title=' - Obtener una Copia', thumbnail=config.get_thumb('folder'), text_color='yellowgreen' ))

    return itemlist


def submnu_addons(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]ADD-ONS:[/B]', thumbnail=config.get_thumb('tools'), text_color='yellowgreen' ))

    if not item.helper:
        itemlist.append(item.clone( action='submnu_addons_info', title='[COLOR green][B]Información[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

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
        if packages:
            itemlist.append(item.clone( action='', title='[B][I]ARCHIVOS PACKAGES:[/I][/B]', thumbnail=config.get_thumb('kodiaddons'), text_color='yellowgreen' ))

            itemlist.append(item.clone( action='show_addons', title=' - Ver', addons = packages, tipo = 'Packages', thumbnail=config.get_thumb('computer'), text_color='yellow' ))

            itemlist.append(item.clone( channel='actions', action='manto_addons_packages', title=' - Eliminar [B][COLOR violet](Si ejecuta es Recomendable Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

        if temps:
            itemlist.append(item.clone( action='', title='[B][I]ARCHIVOS TEMP:[/I][/B]', thumbnail=config.get_thumb('kodiaddons'), text_color='yellowgreen' ))

            itemlist.append(item.clone( action='show_addons', title=' - Ver', addons = temps, tipo = 'Temp', thumbnail=config.get_thumb('computer'), text_color='yellow' ))

            itemlist.append(item.clone( channel='actions', action='manto_addons_temp', title=' - Eliminar [B][COLOR violet](Si ejecuta es Recomendable Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    if item.helper: platformtools.itemlist_refresh()

    if not presentar:
        if item.helper:
            platformtools.dialog_notification(config.__addon_name + ' [COLOR olive][B]Add-Ons[/B][/COLOR]', '[B][COLOR cyan]Nada que Limpiar[/B][/COLOR]')
            return

    return itemlist


def submnu_addons_info(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR yellowgreen][B]INFORMACIÓN ADD-ONS:[/COLOR][/B]' ))

    itemlist.append(item.clone( channel='helper', action='show_help_vias', title= 'Vía alternativa [COLOR goldenrod][B]Elementum[/B][/COLOR]', only_elementum=True, thumbnail=config.get_thumb('elementum') ))

    itemlist.append(item.clone( channel='helper', action='show_help_vias', title= 'Vía alternativa [COLOR goldenrod][B]ResolveUrl[/B][/COLOR]', only_resolve=True, thumbnail=config.get_thumb('resolveurl') ))

    itemlist.append(item.clone( channel='helper', action='show_help_vias', title= 'Vía alternativa [COLOR goldenrod][B]YouTube[/B][/COLOR]', only_youtube=True, thumbnail=config.get_thumb('youtube') ))

    itemlist.append(item.clone( channel='helper', action='show_help_torrents', title= '¿ Dónde obtener los Add-Ons para [COLOR gold][B]Clientes/Motores[/B][/COLOR] torrents ?', thumbnail=config.get_thumb('tools') ))

    itemlist.append(item.clone( channel='helper', action='show_clients_torrent', title= 'Clientes/Motores externos torrent [COLOR gold][B]Soportados[/B][/COLOR]', thumbnail=config.get_thumb('cloud') ))

    itemlist.append(item.clone( action='', title='[COLOR yellowgreen][B][I]ADD-ONS y VIAS ALTERNATIVAS:[/B][/I][/COLOR] (Gestión desde Balandro)', thumbnail=config.get_thumb('kodiaddons') ))

    if config.get_setting('mnu_torrents', default=True):
        cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

        if cliente_torrent == 'Seleccionar' or cliente_torrent == 'Ninguno': tex_tor = cliente_torrent
        else:
           tex_tor = cliente_torrent
           cliente_torrent = 'plugin.video.' + cliente_torrent.lower()

           if xbmc.getCondVisibility('System.HasAddon("%s")' % cliente_torrent):
               try:
                   cod_version = xbmcaddon.Addon(cliente_torrent).getAddonInfo("version").strip()
                   tex_tor += '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
               except:
                   tex_tor += '  [COLOR gray]Desactivado[/COLOR]'

           else: tex_tor += '  [COLOR red]No instalado[/COLOR]'

        itemlist.append(item.clone( action = '', title= ' - Cliente/Motor Torrent asignado ' + '[COLOR fuchsia][B] ' + tex_tor + '[/B][/COLOR]', thumbnail=config.get_thumb('torrents') ))

        if xbmc.getCondVisibility('System.HasAddon("script.elementum.burst")'):
            try:
                cod_version = xbmcaddon.Addon("script.elementum.burst").getAddonInfo("version").strip()
                tex_bur = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
            except:
                tex_bur = '  [COLOR gray]Desactivado[/COLOR]'
        else: tex_bur = '  [COLOR red]No instalado[/COLOR]'

        itemlist.append(item.clone( action = '', title= ' - [COLOR fuchsia][B]Elementum Burst[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_bur + '[/B][/COLOR]', thumbnail=config.get_thumb('elementum') ))

    if xbmc.getCondVisibility('System.HasAddon("inputstream.adaptive")'):
        try:
            cod_version = xbmcaddon.Addon("inputstream.adaptive").getAddonInfo("version").strip()
            tex_ia = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_ia = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_ia = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action = '', title= ' - [COLOR fuchsia][B]InputStream Adaptive[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_ia + '[/B][/COLOR]', thumbnail=config.get_thumb('Inputstreamadaptive') ))

    if xbmc.getCondVisibility('System.HasAddon("inputstream.ffmpegdirect")'):
        try:
            cod_version = xbmcaddon.Addon("inputstream.ffmpegdirect").getAddonInfo("version").strip()
            tex_ia = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_ia = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_ia = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action = '', title= ' - [COLOR fuchsia][B]InputStream Ffmpegdirect[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_ia + '[/B][/COLOR]', thumbnail=config.get_thumb('Inputstreamadaptive') ))

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
        try:
            cod_version = xbmcaddon.Addon("plugin.video.youtube").getAddonInfo("version").strip()
            tex_yt = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_yt = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_yt = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action = '', title= ' - [COLOR fuchsia][B]Youtube[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_yt + '[/B][/COLOR]', thumbnail=config.get_thumb('youtube') ))

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        try:
            cod_version = xbmcaddon.Addon("script.module.resolveurl").getAddonInfo("version").strip()
            tex_mr = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_mr = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_mr = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action = '', title= ' - [COLOR fuchsia][B]ResolveUrl[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_mr + '[/B][/COLOR]', thumbnail=config.get_thumb('resolveurl') ))

    itemlist.append(item.clone( action='', title='[COLOR yellowgreen][B][I]REPOSITORIOS:[/B][/I][/COLOR] (Gestión desde Balandro)', thumbnail=config.get_thumb('kodiaddons') ))

    hay_repo = False
    if xbmc.getCondVisibility('System.HasAddon("%s")' % 'repository.balandro'): hay_repo = True

    if hay_repo:
        try:
            repo_version = xbmcaddon.Addon('repository.balandro').getAddonInfo("version").strip()

            tex_repo = 'Repositorio Balandro  ' + repo_version
            if repo_version in ant_repos: tex_repo = '[COLOR red]Desfasado  ' + repo_version + '[/COLOR]'
        except:
            tex_repo = 'Repositorio Balandro  [COLOR gray]Desactivado[/COLOR]'
    else:
        tex_repo = 'Repositorio Balandro  [COLOR red]No Instalado[/COLOR]'

    itemlist.append(item.clone( action='', title=' - [COLOR cyan][B]' + tex_repo + '[/B][/COLOR]', thumbnail=config.get_thumb('repo') ))

    if xbmc.getCondVisibility('System.HasAddon("repository.resolveurl")'):
        try:
            cod_version = xbmcaddon.Addon("repository.resolveurl").getAddonInfo("version").strip()
            tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_rp = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

    itemlist.append(item.clone( action = '', title= ' - [COLOR gold][B]Repository ResolveUrl[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + '[/B][/COLOR]', thumbnail=config.get_thumb('resolveurlrepo') ))

    if config.get_setting('mnu_torrents', default=True):
        if not PY3:
            if xbmc.getCondVisibility('System.HasAddon("repository.elementum")'):
                try:
                    cod_version = xbmcaddon.Addon("repository.elementum").getAddonInfo("version").strip()
                    tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
                except:
                    tex_rp = '  [COLOR gray]Desactivado[/COLOR]'
            else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

            itemlist.append(item.clone( action = '', title= ' - [COLOR gold][B]Repository Elementum[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + '  (hasta K18.x)[/B][/COLOR]', thumbnail=config.get_thumb('elementumrepo') ))

        if xbmc.getCondVisibility('System.HasAddon("repository.elementumorg")'):
            try:
                cod_version = xbmcaddon.Addon("repository.elementumorg").getAddonInfo("version").strip()
                tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
            except:
                tex_rp = '  [COLOR gray]Desactivado[/COLOR]'
        else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

        itemlist.append(item.clone( action = '', title= ' - [COLOR gold][B]Repository ElementumOrg[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + '[/B][/COLOR]', thumbnail=config.get_thumb('elementumrepo') ))

    if not item._help:
        itemlist.append(item.clone( action='submnu_all_addons', title='[COLOR limegreen][B][I]ADD-ONS INSTALADOS[/I][/B][/COLOR]', thumbnail=config.get_thumb('kodiaddons') ))

        itemlist.append(item.clone( action='submnu_resto_addons', title='[COLOR yellowgreen][B][I]ADD-ONS INSTALADOS CON DATOS[/I][/B][/COLOR]', thumbnail=config.get_thumb('kodiaddons') ))

        itemlist.append(item.clone( action='addons_especiales', title='[COLOR palegreen][B][I]ADD-ONS ESPECIALES COMUNES[/I][/B][/COLOR]', thumbnail=config.get_thumb('kodiaddons') ))

    return itemlist


def submnu_all_addons(item):
    logger.info()
    itemlist = []

    item.all_addons = True

    submnu_resto_addons(item)


def submnu_resto_addons(item):
    logger.info()
    itemlist = []

    if item.all_addons:
        path = translatePath(os.path.join('special://home/addons/', ''))
    else:
        path = translatePath(os.path.join('special://home/userdata/addon_data', ''))

    addons = filetools.listdir(path)

    txt = ''

    for addon in addons:
        if item.all_addons:
           if addon == 'packages': continue
           elif addon == 'temp': continue

        cod_version = ''

        if xbmc.getCondVisibility('System.HasAddon("%s")' % addon):
            try:
                cod_version = xbmcaddon.Addon("%s" % addon).getAddonInfo("version")
                cod_version = cod_version.strip()
            except:
                cod_version = '  [COLOR gray]Desactivado[/COLOR]'
        else:
            cod_version = ' [COLOR red]No instalado[/COLOR]'

        addon = addon.replace('plugin', '[COLOR yellow]plugin[/COLOR]')
        addon = addon.replace('repository', '[COLOR cyan]repository[/COLOR]')
        addon = addon.replace('script', '[COLOR orange]script[/COLOR]')
        addon = addon.replace('skin', '[COLOR aquamarine]skin[/COLOR]')
        addon = addon.replace('service', '[COLOR violet]service[/COLOR]')

        addon = addon.replace('requests', '[COLOR palegreen]requests[/COLOR]')
        addon = addon.replace('js2py', '[COLOR orangered]js2py[/COLOR]')

        addon = addon.replace('resource', '[COLOR tomato]resource[/COLOR]')

        addon = addon.replace('github', '[COLOR yellowgreen]github[/COLOR]')

        addon = addon.replace('inputstream', '[COLOR fuchsia]inputstream[/COLOR]')

        addon = addon.replace('resolveurl', '[COLOR fuchsia]resolveurl[/COLOR]')

        addon = addon.replace('elementumorg', '[COLOR fuchsia]elementumorg[/COLOR]')
        addon = addon.replace('elementum', '[COLOR fuchsia]elementum[/COLOR]')

        addon = addon.replace('youtube', '[COLOR fuchsia]youtube[/COLOR]')

        addon = addon.replace('balandro', '[COLOR yellow]balandro[/COLOR]')

        addon = addon + '  [COLOR gold][B]' + cod_version + '[/B][/COLOR]'

        if item.all_addons: txt += '  ' + str(addon) + '[CR]'
        else: txt += '  ' + str(addon) + '[CR][CR]'

    if item.all_addons: tex_cab = 'Add-Ons Instalados'
    else: tex_cab = 'Add-Ons Instalados con Datos'

    platformtools.dialog_textviewer(tex_cab, txt)


def addons_especiales(item):
    logger.info()
    itemlist = []

    txt = 'Si necesitase Instalar alguno de ellos, los localizará en Nuestra Fuente:[CR]'

    txt += _scripts + '[CR]'

    txt += '[CR][COLOR yellow][B]Vienen Integrados en Kodi:[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("script.module.js2py")'):
        try:
            cod_version = xbmcaddon.Addon("script.module.js2py").getAddonInfo("version").strip()
            tex_js2 = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_js2 = '  [COLOR gray]Desactivado[/COLOR]'

    else: tex_js2 = '  [COLOR red]No integrado[/COLOR]'

    txt += ' - [COLOR orangered]script.module.js2py[/COLOR][B]' + tex_js2 + '[/B][CR]'

    if xbmc.getCondVisibility('System.HasAddon("script.module.requests")'):
        try:
            cod_version = xbmcaddon.Addon("script.module.requests").getAddonInfo("version").strip()
            tex_req = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_req = '  [COLOR gray]Desactivado[/COLOR]'

    else: tex_req = '  [COLOR red]No integrado[/COLOR]'

    txt += ' - [COLOR palegreen]script.module.requests[/COLOR][B]' + tex_req + '[/B][CR]'

    txt += '[CR][COLOR yellow][B]Idiomas Opcionales para Kodi:[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("resource.language.es_es")'):
        try:
            cod_version = xbmcaddon.Addon("resource.language.es_es").getAddonInfo("version").strip()
            tex_lng = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_lng = '  [COLOR gray]Desactivado[/COLOR]'

    else: tex_lng = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR tomato]resource.language.es_es[/COLOR][B]' + tex_lng + '[/B][CR]'

    txt += '[CR][COLOR yellow][B]Skins Opcionales para Kodi:[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("skin.confluence")'):
        try:
            cod_version = xbmcaddon.Addon("skin.confluence").getAddonInfo("version").strip()
            tex_skc = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_skc = '  [COLOR gray]Desactivado[/COLOR]'

    else: tex_skc = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR aquamarine]skin.confluence[/COLOR] [B]' + tex_skc + '[/B][CR]'

    platformtools.dialog_textviewer('Add-Ons Especiales Comunes', txt)


def submnu_sistema(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]SISTEMA:[/B]', text_color='violet' ))

    if not item.helper:
        itemlist.append(item.clone( action='submnu_sistema_info', title='[COLOR green][B]Información[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='', title='[B][I]TESTS:[/I][/B]', text_color='violet' ))

    itemlist.append(item.clone( channel='helper', action = 'show_plataforma', title=' - [COLOR gold][B]Plataforma[/B][/COLOR]', thumbnail=config.get_thumb('mediacenter') ))

    itemlist.append(item.clone( channel='actions', action = 'test_internet', title= '- Comprobar [COLOR goldenrod][B]Internet[/B][/COLOR]', thumbnail=config.get_thumb('crossroads') ))

    itemlist.append(item.clone( channel='helper', action = 'show_test', title= ' - Test [COLOR yellow][B]Status[/B][/COLOR] del sistema', thumbnail=config.get_thumb('addon') ))

    path = os.path.join(config.get_data_path(), 'Lista-proxies.txt')

    existe = filetools.exists(path)

    if existe:
        itemlist.append(item.clone( action='', title='[B][I]LISTA-PROXIES.TXT:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='helper', action='show_yourlist', title=' - Ver', thumbnail=config.get_thumb('computer'), text_color='yellow' ))

        itemlist.append(item.clone( channel='actions', action='manto_yourlist', title= " - Eliminar", thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    path = os.path.join(config.get_data_path(), 'cookies.dat')

    existe = filetools.exists(path)

    if existe:
        itemlist.append(item.clone( action='', title='[B][I]COOKIES:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_cookies', title= " - Eliminar", thumbnail=config.get_thumb('computer'), text_color='red' ))

    path = os.path.join(config.get_data_path(), 'cache')

    existe = filetools.exists(path)

    if existe:
        itemlist.append(item.clone( action='', title='[B][I]CARPETA CACHÉ:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_folder_cache', title= " - Eliminar", thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    if not item.helper:
        path = filetools.join(config.get_data_path(), 'tracking_dbs')

        existe = filetools.exists(path)

        if existe:
            itemlist.append(item.clone( action='', title='[B][I]CONTENIDO PREFERIDOS:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

            itemlist.append(item.clone( channel='actions', action='manto_tracking_dbs', title= " - Eliminar", thumbnail=config.get_thumb('keyboard'), text_color='red' ))

        downloadpath = config.get_setting('downloadpath', default='')

        if downloadpath: path = downloadpath
        else: path = filetools.join(config.get_data_path(), 'downloads')

        existe = filetools.exists(path)

        if existe:
            itemlist.append(item.clone( action='', title='[B][I]CONTENIDO DESCARGAS:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

            itemlist.append(item.clone( channel='actions', action='manto_folder_downloads', title= " - Eliminar", thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    path = filetools.join(config.get_data_path(), 'tmdb.sqlite-journal')

    existe = filetools.exists(path)

    if existe:
        itemlist.append(item.clone( action='', title='[B][I]TMDB SQLITE JOURNAL:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_tmdb_sqlite', title= " - Eliminar", journal = 'journal', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    path = filetools.join(config.get_data_path(), 'tmdb.sqlite')

    existe = filetools.exists(path)

    if existe:
        itemlist.append(item.clone( action='', title='[B][I]TMDB SQLITE:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_tmdb_sqlite', title= " - Eliminar", thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    if not item.helper:
        path = config.get_data_path()

        existe = filetools.exists(path)

        if existe:
            itemlist.append(item.clone( action='', title='[B][I]AJUSTES PREFERENCIAS:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

            itemlist.append(item.clone( channel='actions', action='manto_folder_addon', title= " - Eliminar", thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    if item.helper: platformtools.itemlist_refresh()

    if not itemlist:
        if item.helper:
            platformtools.dialog_notification(config.__addon_name + ' [COLOR olive][B]Sistema[/B][/COLOR]', '[B][COLOR cyan]Nada que Limpiar[/B][/COLOR]')
            return

    return itemlist


def submnu_sistema_info(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR green][B]INFORMACIÓN[/COLOR] [COLOR violet]SISTEMA:[/COLOR][/B]' ))

    itemlist.append(item.clone( action='show_sistema', title= 'Información [COLOR teal][B]Ajustes del Sistema[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title='[COLOR aqua][B]Últimos Cambios Dominios[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='helper', action='show_version', title= '[COLOR lime][B]Versión[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    txt_python = '  %s.%s.%s[CR][CR]' % (str(sys.version_info[0]), str(sys.version_info[1]), str(sys.version_info[2]))
    itemlist.append(item.clone( action='', title='[COLOR green][B]Versión Python[/COLOR][COLOR violet]' + txt_python + '[/COLOR][/B]', thumbnail=config.get_thumb('python') ))

    path = os.path.join(config.get_runtime_path(), 'last_fix.json')

    existe = filetools.exists(path)

    if existe:
        itemlist.append(item.clone( action='', title='[B][I]FIXES:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        if config.get_setting('addon_update_atstart', default=True):
            itemlist.append(item.clone( action='', title= '- Comprobar Fixes al [COLOR goldenrod][B]Iniciar[/B][/COLOR] su Media Center [COLOR yellow][B]Activado[/B][/COLOR]', thumbnail=config.get_thumb('settings') ))
        else:
            itemlist.append(item.clone( action='', title= '- Comprobar Fixes al [COLOR goldenrod][B]Iniciar[/B][/COLOR] su Media Center [COLOR red][B]Des-Activado[/B][/COLOR]', thumbnail=config.get_thumb('settings') ))


        itemlist.append(item.clone( channel='helper', action='show_last_fix', title= ' - [COLOR green][B]Información[/B][/COLOR] Fix instalado', thumbnail=config.get_thumb('news') ))

        itemlist.append(item.clone( channel='actions',  action='resumen_fix', title= ' - [COLOR darkcyan][B]Resumen[/B][/COLOR] Fix Instalado', thumbnail=config.get_thumb('news') ))

        itemlist.append(item.clone( channel='actions', action='manto_last_fix', title= ' - [COLOR red][B]Eliminar[/B][/COLOR] fichero control Fix', thumbnail=config.get_thumb('keyboard') ))

    itemlist.append(item.clone( channel='helper',  action='show_sets', title= 'Visualizar sus [COLOR chocolate][B]Ajustes[/B][/COLOR] Personalizados', thumbnail=config.get_thumb('folder') ))

    return itemlist


def submnu_logs(item):
    logger.info()
    itemlist = []

    presentar = False

    if os.path.exists(os.path.join(config.get_data_path(), 'servers_todo.log')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'qualities_todo.log')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'proxies.log')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'canales.log')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'servidores.log')): presentar = True

    if presentar:
        itemlist.append(item.clone( action='', title='[B]LOGS:[/B]', thumbnail=config.get_thumb('tools'), text_color='limegreen' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'servers_todo.log')):
            itemlist.append(item.clone( action='', title='[B][I]SERVIDORES:[/I][/B]', text_color='limegreen' ))

            itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - Ver', todo = 'servers_todo.log', thumbnail=config.get_thumb('bolt'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'qualities_todo.log')):
            itemlist.append(item.clone( action='', title='[B][I]CALIDADES:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='limegreen' ))

            itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - Ver', todo = 'qualities_todo.log', thumbnail=config.get_thumb('computer'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'proxies.log')):
            itemlist.append(item.clone( action='', title='[B][I]PROXIES:[/I][/B]', thumbnail=config.get_thumb('flame'), text_color='limegreen' ))

            itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - Ver', todo = 'proxies.log', thumbnail=config.get_thumb('computer'), text_color='yellow' ))

        if config.get_setting('developer_team'):
            if os.path.exists(os.path.join(config.get_data_path(), 'canales.log')) or os.path.exists(os.path.join(config.get_data_path(), 'servidores.log')):
                itemlist.append(item.clone( action='', title='[B][I]INSATISFACTORIOS:[/I][/B]', text_color='limegreen' ))

                if os.path.exists(os.path.join(config.get_data_path(), 'canales.log')):
                    itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - Ver canales', todo = 'canales.log', thumbnail=config.get_thumb('stack'), text_color='gold' ))

                if os.path.exists(os.path.join(config.get_data_path(), 'servidores.log')):
                    itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - Ver servidores', todo = 'servidores.log', thumbnail=config.get_thumb('bolt'), text_color='fuchsia' ))

        itemlist.append(item.clone( channel='actions', action='manto_temporales', title='Eliminar Todos los LOGS', _logs = True, thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    if item.helper: platformtools.itemlist_refresh()

    if not itemlist:
        if item.helper:
            platformtools.dialog_notification(config.__addon_name + ' [COLOR olive][B]Logs[/B][/COLOR]', '[B][COLOR cyan]Nada que Limpiar[/B][/COLOR]')
            return

    return itemlist


def submnu_temporales(item):
    logger.info()
    itemlist = []

    presentar = False

    if os.path.exists(os.path.join(config.get_data_path(), 'info_channels.csv')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'temp.torrent')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'm3u8hls.m3u8')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'blenditall.m3u8')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'test_logs')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'temp_updates.zip')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'tempfile_mkdtemp')): presentar = True

    if presentar:
        itemlist.append(item.clone( action='', title='[B]TEMPORALES:[/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'info_channels.csv')):
            itemlist.append(item.clone( action='', title='[B][I]INFO CHANNELS:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay Info channels', thumbnail=config.get_thumb('dev'), text_color='goldenrod' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'temp.torrent')):
            itemlist.append(item.clone( action='', title='[B][I]TORRENT:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay Torrent', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'm3u8hls.m3u8')):
            itemlist.append(item.clone( action='', title='[B][I]M3U8HLS:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay M3u8hls', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'blenditall.m3u8')):
            itemlist.append(item.clone( action='', title='[B][I]BLENDITALL:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay M3u8', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'test_logs')):
            itemlist.append(item.clone( action='', title='[B][I]TEST LOGS:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay Test logs', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'temp_updates.zip')):
            itemlist.append(item.clone( action='', title='[B][I]UPDATES:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay Updates', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'tempfile_mkdtemp')):
            itemlist.append(item.clone( action='', title='[B][I]MKDTEMP:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay Mkdtemp', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        itemlist.append(item.clone( channel='actions', action='manto_temporales', title='Eliminar', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    if item.helper: platformtools.itemlist_refresh()

    if not itemlist:
        if item.helper:
            platformtools.dialog_notification(config.__addon_name + ' [COLOR olive][B]Temporales[/B][/COLOR]', '[B][COLOR cyan]Nada que Limpiar[/B][/COLOR]')
            return

    return itemlist


def submnu_gestionar(item):
    logger.info()
    itemlist = []

    presentar = False

    if config.get_setting('developer_team'): presentar = True

    if presentar:
        itemlist.append(item.clone( action='', title='[B]GESTIONAR:[/B]', thumbnail=config.get_thumb('tools'), text_color='teal' ))

        if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developergenres.py')):
            itemlist.append(item.clone( channel='developergenres', action='mainlist', title=' - [COLOR thistle][B]Géneros[/B][/COLOR]', thumbnail=config.get_thumb('genres') ))

        tests = False
        if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')): tests = True
        elif os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')):  tests = True

        if tests:
            itemlist.append(item.clone( action='', title='[B][I]TESTS CANALES Y SERVIDORES:[/I][/B]', thumbnail=config.get_thumb('support'), text_color='teal' ))

            if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')):
                itemlist.append(item.clone( channel='developertest', action='mainlist', title=' - [COLOR gold][B]Canales y Servidores[/B][/COLOR]', thumbnail=config.get_thumb('tools') ))

            if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')):
                if os.path.exists(os.path.join(config.get_data_path(), 'developer.sqlite')):
                    itemlist.append(item.clone( channel='developertools', action='mainlist', title=' - Generación [COLOR darkgoldenrod][B]Queries[/B][/COLOR]', thumbnail=config.get_thumb('tools') ))

        checks = False
        if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developerthumbs.py')): checks = True
        elif os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developerwebs.py')): checks = True

        if checks:
            itemlist.append(item.clone( action='', title='[B][I]CHECKS CANALES:[/I][/B]', thumbnail=config.get_thumb('stack'), text_color='teal' ))

            if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developerthumbs.py')):
                itemlist.append(item.clone( channel='developerthumbs', action='mainlist', title=' - [COLOR palegreen][B]Thumbs[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

            if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developerwebs.py')):
                itemlist.append(item.clone( channel='developerwebs', action='mainlist', title=' - Generación [COLOR cyan][B]Webs/Hosts[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

        itemlist.append(item.clone( action='', title='[B][I]WEBS/HOSTS:[/I][/B]', text_color='teal' ))

        itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - [COLOR yellow]Ver dominios[/COLOR]', todo = 'webs.log', thumbnail=config.get_thumb('computer') ))

        itemlist.append(item.clone( action='', title='[B][I]INSATISFACTORIOS:[/I][/B]', text_color='teal' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'canales.log')):
            itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - [COLOR gold]Ver canales[/COLOR]', todo = 'canales.log', thumbnail=config.get_thumb('stack') ))

        if os.path.exists(os.path.join(config.get_data_path(), 'servidores.log')):
            itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - [COLOR fuchsia]Ver servidores[/COLOR]', todo = 'servidores.log', thumbnail=config.get_thumb('bolt') ))

        if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developerrelease.py')):
            itemlist.append(item.clone( action='', title='[B][I]VERSIÓN:[/I][/B]', thumbnail=config.get_thumb('addon'), text_color='teal' ))

            itemlist.append(item.clone( channel='developerrelease', action='mainlist', title=' - Generación [COLOR yellow][B]Release[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    return itemlist


def submnu_proxies(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]TESTS PROXIES:[/B]', text_color='red' ))

    itemlist.append(item.clone( action='submnu_proxies_info', title='[COLOR green][B]Información[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='', title='[B][I]TESTS PROVIDERS:[/I][/B]', text_color='red' ))

    itemlist.append(item.clone( action='test_providers', title= ' - [COLOR yellowgreen][B]Tests[/B][/COLOR] Proveedores', thumbnail=config.get_thumb('flame') ))

    itemlist.append(item.clone( action='test_tplus', title= ' - Asignar proveedor [COLOR goldenrod][B]TPlus[/B][/COLOR]', thumbnail=config.get_thumb('settings') ))

    itemlist.append(item.clone( action='', title='[B][I]OPCIONES:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='red' ))

    itemlist.append(item.clone( channel='helper', action='channels_with_proxies', title= ' - Qué canales pueden usar Proxies', new_proxies=True, test_proxies=True, thumbnail=config.get_thumb('stack') ))

    if config.get_setting('memorize_channels_proxies', default=True):
        itemlist.append(item.clone( channel='helper', action='channels_with_proxies_memorized', title= ' - Qué [COLOR red]canales[/COLOR] tiene con proxies [COLOR red][B]Memorizados[/B][/COLOR]', new_proxies=True, memo_proxies=True, test_proxies=True, thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='actions', action = 'manto_proxies', title= ' - Quitar los proxies en los canales [COLOR red][B](que los tengan Memorizados)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard') ))

    itemlist.append(item.clone( channel='actions', action = 'global_proxies', title = ' - Configurar proxies a usar [COLOR plum][B](en los canales que los necesiten)[/B][/COLOR]', thumbnail=config.get_thumb('settings') ))

    presentar = False

    path = os.path.join(config.get_data_path(), 'Lista-proxies.txt')

    existe = filetools.exists(path)

    if existe: presentar = True

    if presentar:
        itemlist.append(item.clone( action='', title='[B][I]LISTA-PROXIES.TXT:[/I][/B]', thumbnail=config.get_thumb('tools'), text_color='red' ))

        itemlist.append(item.clone( channel='helper', action='show_help_yourlist', title= ' - [COLOR goldenrod][B]Gestión[/B][/COLOR] Fichero Personalizado', thumbnail=config.get_thumb('pencil') ))

        itemlist.append(item.clone( channel='helper', action='show_yourlist', title= ' - [COLOR green][B]Contenido[/B][/COLOR] de su Fichero [COLOR gold][B]Personalizado[/B][/COLOR] de proxies', thumbnail=config.get_thumb('news') ))

        itemlist.append(item.clone( channel='actions', action='manto_yourlist', title= ' - [COLOR red][B]Eliminar[/B][/COLOR] su Fichero [COLOR yellow][B]Personalizado[/B][/COLOR]', thumbnail=config.get_thumb('keyboard') ))

    return itemlist


def submnu_proxies_info(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR green][B]INFORMACIÓN[/COLOR] [COLOR red]TEST PROXIES:[/COLOR][/B]' ))

    itemlist.append(item.clone( channel='helper', action='show_help_proxies', title= 'Uso de [COLOR red]Proxies[/COLOR]' ))
    itemlist.append(item.clone( channel='helper', action='show_help_providers', title= '[COLOR magenta]Proveedores[/COLOR] de proxies' ))

    if config.get_setting('proxies_extended', default=False):
        itemlist.append(item.clone( channel='helper', action='show_help_providers2', title= 'Lista [COLOR aqua][B]Ampliada[/B][/COLOR] de Proveedores de proxies' ))

    if config.get_setting('proxies_vias', default=False): 
        itemlist.append(item.clone( channel='helper', action='proxies_show_vias', title= 'Lista [COLOR aquamarine][B]Vías Alternativas[/B][/COLOR] de Proveedores de proxies' ))

    return itemlist


def submnu_canales(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]TESTS CANALES:[/B]', text_color='gold' ))

    itemlist.append(item.clone( action='submnu_canales_info', title='[COLOR green][B]Información[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title= '[COLOR cyan][B]Últimos Cambios Dominios[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='resumen_canales', title='[COLOR gold]Resúmenes y Distribución[/COLOR]' ))

    if txt_status:
        if con_incidencias:
            itemlist.append(item.clone( action='resumen_incidencias', title= 'Canales[COLOR tan][B] Con Incidencias[/B][/COLOR]' ))

        if no_accesibles:
            itemlist.append(item.clone( action='resumen_no_accesibles', title= 'Canales[COLOR indianred][B] No Accesibles[/B][/COLOR]' ))

        if con_problemas:
            itemlist.append(item.clone( action='resumen_con_problemas', title='Canales [COLOR tomato][B]Con Problemas[/B][/COLOR]' ))

    itemlist.append(item.clone( action='', title='[B][I]TEST TODOS:[/I][/B]', text_color='gold' ))

    itemlist.append(item.clone( action='test_all_webs', title=' - Posibles [B][COLOR gold]Insatisfactorios[/B][/COLOR]', unsatisfactory = True ))

    itemlist.append(item.clone( action='test_all_webs', title=' - Excepto los Canales que sean [COLOR turquoise][B]Clones[/B][/COLOR]', extra='no_clones', unsatisfactory = True ))

    itemlist.append(item.clone( action='test_all_webs', title=' - Canales [COLOR darkcyan][B]Activos[/B][/COLOR]' ))

    itemlist.append(item.clone( action='', title='[B][I]TEST SELECTIVOS:[/I][/B]', text_color='gold' ))

    itemlist.append(item.clone( action='test_all_webs', title=' - Solo los Canales [COLOR aquamarine][B]Sugeridos[/B][/COLOR]', extra='sugeridos', thumbnail=config.get_thumb('suggested'), unsatisfactory = True ))

    itemlist.append(item.clone( action='test_all_webs', title=' - Solo los Canales que sean [COLOR paleturquoise][B]Principales[/B][/COLOR] con [COLOR turquoise][B]Clones[/B][/COLOR]', extra='clons', unsatisfactory = True  ))

    itemlist.append(item.clone( action='test_all_webs', title=' - Solo los Canales que sean [COLOR turquoise][B]Clones[/B][/COLOR]', extra='clones', unsatisfactory = True  ))

    itemlist.append(item.clone( action='test_alfabetico', title=' - Desde un Canal [COLOR powderblue][B]Letra Inicial[/B][/COLOR]', unsatisfactory = True ))

    itemlist.append(item.clone( action='test_one_channel', title=' - Un Canal Concreto' ))

    itemlist.append(item.clone( action='test_one_channel', title= ' - Canales Temporalmente [COLOR springgreen][B]Inactivos[/B][/COLOR]', temp_no_active = True ))

    return itemlist


def submnu_canales_info(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR green][B]INFORMACIÓN[/COLOR] [COLOR gold]CANALES:[/COLOR][/B]' ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list', title= ' - [COLOR gold][B]Todos[/B][/COLOR] los Canales', tipo = 'all' ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list', title= ' - Qué canales están [COLOR gold][B]Disponibles[/B][/COLOR] (Activos)' ))
    itemlist.append(item.clone( channel='helper', action='show_channels_list', title= ' - Qué canales están [COLOR aquamarine][B]Sugeridos[/B][/COLOR]', suggesteds = True, thumbnail=config.get_thumb('suggested') ))

    itemlist.append(item.clone( channel='helper', action='channels_prefered', title= ' - Qué canales tiene marcados como [COLOR gold][B]Preferidos[/B][/COLOR]' ))
    itemlist.append(item.clone( channel='helper', action='channels_no_actives', title= '    - Qué canales tiene marcados como [COLOR gray][B]Desactivados[/B][/COLOR]' ))

    itemlist.append(item.clone( channel='helper', action='channels_with_notice', title= ' - Qué canales tienen [COLOR green][B]Aviso[/COLOR][COLOR red] CloudFlare [COLOR orangered]Protection[/B][/COLOR]' ))

    itemlist.append(item.clone( channel='helper', action='channels_with_proxies', title= '    - Qué canales pueden necesitar [COLOR red][B]Proxies[/B][/COLOR]', new_proxies=True ))

    if config.get_setting('memorize_channels_proxies', default=True):
        itemlist.append(item.clone( channel='helper', action='channels_with_proxies_memorized', title= ' - Qué [COLOR red]canales[/COLOR] tiene con proxies [COLOR red][B]Memorizados[/B][/COLOR]', new_proxies=True, memo_proxies=True, test_proxies=True, thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list', title= '    - Qué canales están [COLOR plum][B]Inestables[/B][/COLOR]', no_stable = True ))
    itemlist.append(item.clone( channel='helper', action='show_channels_list', title= '    - Qué canales son [COLOR darkgoldenrod][B]Problemátios[/B][/COLOR] (Predominan Sin enlaces Disponibles/Válidos/Soportados)', problematics = True ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list', title= '    - Qué canales son [COLOR aquamarine][B]Principales[/COLOR] con [COLOR turquoise]Clones[/B][/COLOR] Asociados', clons = True ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list', title= '    - Qué canales son [COLOR turquoise][B]Clones[/B][/COLOR] (Clon del Canal Principal)', clones = True ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list_temporaries', title= '    - Qué canales están [COLOR cyan][B]Temporalmente[/B][/COLOR] inactivos' ))
    itemlist.append(item.clone( channel='helper', action='show_channels_list', title= '    - Qué canales son [COLOR grey][B]Privados[/B][/COLOR]', tipo = 'all', privates = True ))

    if not PY3:
        itemlist.append(item.clone( channel='helper', action='show_channels_list', title= '    - Qué canales son [COLOR violet][B]Incompatibiles[/B][/COLOR] con su Media Center', mismatched = True ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list_inactives', title= '    - Qué canales están [COLOR coral][B]Inactivos[/B][/COLOR]' ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list_closed', title= '    - Qué canales están [COLOR darkgoldenrod][B]Cerrados[/B][/COLOR]' ))
    itemlist.append(item.clone( channel='helper', action='show_channels_list_voided', title= '    - Qué canales están [COLOR darkgoldenrod][B]Anulados[/B][/COLOR]' ))

    return itemlist


def submnu_servidores(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]TESTS SERVIDORES:[/B]', text_color='fuchsia' ))

    itemlist.append(item.clone( action='submnu_servidores_info', title='[COLOR green][B]Información[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title= '[COLOR cyan][B]Últimos Cambios Dominios[/B][/COLOR]', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='resumen_servidores', title='[COLOR fuchsia]Resúmenes y Distribución[/COLOR]' ))

    if txt_status:
        if srv_pending:
            itemlist.append(item.clone( action='resumen_pending', title=' - [COLOR tan][B]Con Incidencias[/B][/COLOR]' ))

    itemlist.append(item.clone( action='', title='[B][I]TEST TODOS:[/I][/B]', text_color='fuchsia' ))

    itemlist.append(item.clone( action='test_all_srvs', title=' - Posibles [COLOR fuchsia][B]Insatisfactorios[/B][/COLOR]', unsatisfactory = True ))

    itemlist.append(item.clone( action='test_all_srvs', title=' - Servidores [COLOR darkcyan][B]Activos[/B][/COLOR]' ))

    itemlist.append(item.clone( action='', title='[B][I]TEST SELECTIVOS:[/I][/B]', text_color='fuchsia' ))

    itemlist.append(item.clone( action='test_alfabetico', title=' - Desde un Servidor [COLOR powderblue][B]Letra Inicial[/B][/COLOR]', unsatisfactory = True ))

    itemlist.append(item.clone( action='test_one_server', title=' - Un Servidor Concreto' ))

    return itemlist


def submnu_servidores_info(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[COLOR green][B]INFORMACIÓN[/COLOR] [COLOR fuchsia]SERVIDORES:[/COLOR][/B]' ))

    itemlist.append(item.clone( channel='helper', action='show_servers_list', title= ' - [COLOR darkorange][B]Todos[/B][/COLOR] los Servidores', tipo = 'all', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( channel='helper', action='show_servers_list', title= ' - Qué servidores están [COLOR darkorange][B]Disponibles[/B][/COLOR] (Activos)', tipo = 'activos', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( channel='helper', action='show_servers_list_out_service', title= '    - Qué servidores están [COLOR goldenrod][B]Sin Servicio[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( channel='helper', action='show_servers_list_inactives', title= '    - Qué servidores están [COLOR coral][B]Inactivos[/B][/COLOR]', thumbnail=config.get_thumb('bolt') ))

    itemlist.append(item.clone( channel='helper', action='show_channels_list', title= '    - Qué [COLOR gold][B]Canales[/COLOR] tienen [COLOR orchid][B]Solo un servidor[/B][/COLOR]', onlyone = True, thumbnail=config.get_thumb('stack') ))

    return itemlist


def submnu_developers(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]DEVELOPERS:[/B]', text_color='firebrick' ))

    itemlist.append(item.clone( channel='helper', action='show_help_notice', title='[COLOR aqua][B]Comunicado[/B][/COLOR] Oficial de Balandro', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( channel='helper', action='show_dev_notes', title='[COLOR gold][B]Notas[/B][/COLOR] para Developers (desarrolladores)', thumbnail=config.get_thumb('news') ))

    itemlist.append(item.clone( action='copy_dev', title= 'Obtener Copia del Fihero de [COLOR gold][B]Notas[/B][/COLOR] para Desarrolladores', thumbnail=config.get_thumb('folder'), text_color='yellowgreen' ))

    itemlist.append(item.clone( action='', title='[COLOR firebrick][B][I]FUENTES:[/I][/B][/COLOR]', folder=False ))

    itemlist.append(item.clone( action='', title=' - Fuentes [COLOR darkorange][B]https://github.com/repobal[/B][/COLOR]', thumbnail=config.get_thumb('addon'), folder=False ))

    if config.get_setting('developer_team'):
        itemlist.append(item.clone( action='', title='[COLOR firebrick][B][I]GESTIONAR:[/I][/B][/COLOR]', folder=False ))

        itemlist.append(item.clone( action='submnu_gestionar', title= 'Gestiones Varias del Add-On', thumbnail=config.get_thumb('computer'), text_color='palegreen' ))

    itemlist.append(item.clone( action='', title='[COLOR firebrick][B][I]Developers Telegram:[/I][/B][/COLOR]', folder=False ))

    itemlist.append(item.clone( action='', title=' - Team ' + _team + ' Equipo de Desarrollo', folder=False, thumbnail=config.get_thumb('telegram') ))

    itemlist.append(item.clone( action='', title='[COLOR firebrick][B][I]INCORPORACIONES:[/B][/I][/COLOR]', folder=False ))

    itemlist.append(item.clone( action='', title=' - [COLOR yellow][B][I]Solicitudes solo con Enlace de Invitación[/I][/B][/COLOR]', folder=False, thumbnail=config.get_thumb('pencil') ))

    itemlist.append(item.clone( action='', title=' - Foro ' + _foro, thumbnail=config.get_thumb('foro'), folder=False ))
    itemlist.append(item.clone( action='', title=' - Telegram ' + _telegram, thumbnail=config.get_thumb('telegram'), folder=False ))

    return itemlist


def copy_dev(item):
    logger.info()

    file = os.path.join(config.get_runtime_path(), 'dev-notes.txt')

    existe = filetools.exists(file)

    if existe == False:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No se localiza el fichero dev-notes.txt[/COLOR][/B]' % color_alert)
        return

    destino_path = xbmcgui.Dialog().browseSingle(3, 'Seleccionar carpeta dónde copiar', 'files', '', False, False, '')
    if not destino_path: return

    origen = os.path.join(file)
    destino = filetools.join(destino_path, 'dev-notes.txt')

    if not filetools.copy(origen, destino, silent=False):
        platformtools.dialog_ok(config.__addon_name, 'Error, no se ha podido copiar el fichero dev-notes.txt!', origen, destino)
        return

    platformtools.dialog_notification('Fichero copiado', 'dev-notes.txt')


def test_providers(item):
    logger.info()

    proxies_actuales = config.get_setting('proxies', 'test_providers', default='').strip()

    config.set_setting('channel_test_providers_dominio', '')
    config.set_setting('proxies', '', 'test_providers')

    default_provider = 'proxyscrape.com'
    all_providers = 'All-providers'
    private_list = 'Lista-proxies.txt'

    proxies_extended = config.get_setting('proxies_extended', default=False)
    proxies_list = config.get_setting('proxies_list', default=False)

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

    if proxies_extended:
        opciones_provider.append('z-coderduck')
        opciones_provider.append('z-echolink')
        opciones_provider.append('z-free-proxy-list.anon')
        opciones_provider.append('z-free-proxy-list.com')
        opciones_provider.append('z-free-proxy-list.uk')
        opciones_provider.append('z-github')
        opciones_provider.append('z-hidemium')
        opciones_provider.append('z-opsxcq')
        opciones_provider.append('z-proxy-daily')
        opciones_provider.append('z-proxy-list.org')
        opciones_provider.append('z-proxyhub')
        opciones_provider.append('z-proxyranker')
        opciones_provider.append('z-socks')
        opciones_provider.append('z-squidproxyserver')
        opciones_provider.append('z-xroxy')

    if not proxies_list: opciones_provider.remove(private_list)

    preselect = 0
    opciones_provider = sorted(opciones_provider, key=lambda x: x)
    ret = platformtools.dialog_select('Proveedores de proxies', opciones_provider, preselect=preselect)
    if ret == -1: return

    provider = opciones_provider[ret]

    domain = 'https://'

    domain = platformtools.dialog_input(default=domain, heading='Indicar Dominio a Testear  -->  [COLOR %s]https://??????[/COLOR]' % color_avis)

    if domain is None: domain = ''
    elif domain == 'https://': domain = ''

    if domain:
       if domain.startswith('//'): domain = 'https:' + domain
       elif not domain.startswith('https://'): domain = 'https:' + domain
    else: domain = 'https://www.youtube.com/'

    from core import proxytools

    procesar = False
    if provider == all_providers: procesar = True

    proxies = proxytools._buscar_proxies('test_providers', domain, provider, procesar)

    proxies_encontrados = config.get_setting('proxies', 'test_providers', default='').strip()

    config.set_setting('proxies', '', 'test_providers')

    if proxies:
        if proxies_encontrados: return
        else:
           platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Sin Proxies localizados[/COLOR][/B]' % color_exec)
           return

    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B] Test_Providers[/B][/COLOR]', '[COLOR yellowgreen][B]¿ Desea efectuar el Test del Resultado ?[/B][/COLOR]'):
        from modules import tester

        config.set_setting('channel_test_providers_dominio', domain)

        try: tester.test_channel('test_providers')
        except: platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] Test_Providers[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Test Ignorado[/B][/COLOR]' % color_alert)

    else: platformtools.dialog_notification(config.__addon_name + ' ' + provider, '[B][COLOR %s]Comprobar Proveedor[/COLOR][/B]' % color_alert)

    config.set_setting('dominio', '', 'test_providers')
    config.set_setting('proxies', '', 'test_providers')


def test_tplus(item):
    logger.info()

    tplus_actual = config.get_setting('proxies_tplus', default='32')

    if config.get_setting('proxies_tplus_proces'): tplus_actual = config.get_setting('proxies_tplus_proces', default='32')

    opciones_tplus = [
            'Openproxy http',
            'Openproxy socks4',
            'Openproxy socks5',
            'Vpnoverview',
            'Fyvri all',
            'Fyvri http',
            'Fyvri https',
            'Fyvri socks4',
            'Fyvri socks5',
            'Netzwelt',
            'Proxy-list.download http',
            'Proxy-list.download https',
            'Proxy-list.download socks4',
            'Proxy-list.download socks5',
            'Freeproxy',
            'Freeproxy anonymity',
            'Hidemyna',
            'Proxylistplus',
            'Niek',
            'TheSpeedX',
            'Proxyscan http',
            'Proxyscan all',
            'Proxyscan socks4',
            'Proxyscan socks5',
            'Openproxylist http',
            'Openproxylist socks4',
            'Openproxylist socks5',
            'Proxy-list.download v1 socks4',
            'Proxy-list.download v1 socks5',
            'Monosans',
            'Jetkai',
            'Sunny9577',
            'Proxy4parsing',
            'Hendrikbgr',
            'Rdavydov http',
            'Aslisk',
            'Rdavydov socks4',
            'Hookzof',
            'ManuGMG',
            'Rdavydov socks5',
            'Lamt3012',
            'Proxifly http',
            'Proxifly https',
            'Proxifly socks4',
            'Proxifly socks5',
            'ErcinDedeoglu http',
            'ErcinDedeoglu https',
            'ErcinDedeoglu socks4',
            'ErcinDedeoglu socks5',
            'Proxycompass',
            'Proxybros',
            'Proxyscrape all',
            'Proxyscrape anonymous',
            'Proxyscrape elite',
            'Proxyscrape transparent',
            'Proxyscrape https',
            'Markavale',
            'MuRongPIG',
            'Vakhov http',
            'Vakhov https',
            'Vakhov socks4',
            'Vakhov socks5',
            'Hidemium'
            ]

    preselect = tplus_actual

    opciones_tplus = sorted(opciones_tplus, key=lambda x: x)

    ret = platformtools.dialog_select('[COLOR cyan][B]Proveedores Proxies Tplus[/B][/COLOR]', opciones_tplus, preselect=preselect)
    if ret == -1: return -1

    if opciones_tplus[ret] == 'Openproxy http': proxies_tplus = '0'
    elif opciones_tplus[ret] == 'Openproxy socks4': proxies_tplus = '1'
    elif opciones_tplus[ret] == 'Openproxy socks5': proxies_tplus = '2'
    elif opciones_tplus[ret] == 'Vpnoverview': proxies_tplus = '3'
    elif opciones_tplus[ret] == 'Fyvri all': proxies_tplus = '4'
    elif opciones_tplus[ret] == 'Fyvri http': proxies_tplus = '5'
    elif opciones_tplus[ret] == 'Fyvri https': proxies_tplus = '6'
    elif opciones_tplus[ret] == 'Fyvri socks4': proxies_tplus = '7'
    elif opciones_tplus[ret] == 'Fyvri socks5': proxies_tplus = '56'
    elif opciones_tplus[ret] == 'Netzwelt': proxies_tplus = '8'
    elif opciones_tplus[ret] == 'Proxy-list.download http': proxies_tplus = '9'
    elif opciones_tplus[ret] == 'Proxy-list.download https': proxies_tplus = '10'
    elif opciones_tplus[ret] == 'Proxy-list.download socks4': proxies_tplus = '11'
    elif opciones_tplus[ret] == 'Proxy-list.download socks5': proxies_tplus = '12'
    elif opciones_tplus[ret] == 'Freeproxy': proxies_tplus = '13'
    elif opciones_tplus[ret] == 'Freeproxy anonymity': proxies_tplus = '14'
    elif opciones_tplus[ret] == 'Hidemyna': proxies_tplus = '15'
    elif opciones_tplus[ret] == 'Proxylistplus': proxies_tplus = '16'
    elif opciones_tplus[ret] == 'Niek': proxies_tplus = '17'
    elif opciones_tplus[ret] == 'TheSpeedX': proxies_tplus = '18'
    elif opciones_tplus[ret] == 'Proxyscan http': proxies_tplus = '19'
    elif opciones_tplus[ret] == 'Proxyscan all': proxies_tplus = '20'
    elif opciones_tplus[ret] == 'Openproxylist http': proxies_tplus = '21'
    elif opciones_tplus[ret] == 'Openproxylist socks4': proxies_tplus = '22'
    elif opciones_tplus[ret] == 'Openproxylist socks5': proxies_tplus = '23'
    elif opciones_tplus[ret] == 'Proxy-list.download v1 socks4': proxies_tplus = '24'
    elif opciones_tplus[ret] == 'Proxy-list.download v1 socks5': proxies_tplus = '25'
    elif opciones_tplus[ret] == 'Monosans': proxies_tplus = '26'
    elif opciones_tplus[ret] == 'Jetkai': proxies_tplus = '27'
    elif opciones_tplus[ret] == 'Sunny9577': proxies_tplus = '28'
    elif opciones_tplus[ret] == 'Proxy4parsing': proxies_tplus = '29'
    elif opciones_tplus[ret] == 'Hendrikbgr': proxies_tplus = '30'
    elif opciones_tplus[ret] == 'Rdavydov http': proxies_tplus = '31'
    elif opciones_tplus[ret] == 'Aslisk': proxies_tplus = '32'
    elif opciones_tplus[ret] == 'Rdavydov socks4': proxies_tplus = '33'
    elif opciones_tplus[ret] == 'Hookzof': proxies_tplus = '34'
    elif opciones_tplus[ret] == 'ManuGMG': proxies_tplus = '35'
    elif opciones_tplus[ret] == 'Rdavydov socks5': proxies_tplus = '36'
    elif opciones_tplus[ret] == 'Lamt3012': proxies_tplus = '37'
    elif opciones_tplus[ret] == 'Proxifly http': proxies_tplus = '38'
    elif opciones_tplus[ret] == 'Proxifly https': proxies_tplus = '45'
    elif opciones_tplus[ret] == 'Proxifly socks4': proxies_tplus = '39'
    elif opciones_tplus[ret] == 'Proxifly socks5': proxies_tplus = '40'
    elif opciones_tplus[ret] == 'ErcinDedeoglu http': proxies_tplus = '41'
    elif opciones_tplus[ret] == 'ErcinDedeoglu https': proxies_tplus = '42'
    elif opciones_tplus[ret] == 'ErcinDedeoglu socks4': proxies_tplus = '43'
    elif opciones_tplus[ret] == 'ErcinDedeoglu socks5': proxies_tplus = '44'
    elif opciones_tplus[ret] == 'Proxycompass': proxies_tplus = '46'
    elif opciones_tplus[ret] == 'Proxybros': proxies_tplus = '47'
    elif opciones_tplus[ret] == 'Proxyscrape all': proxies_tplus = '48'
    elif opciones_tplus[ret] == 'Proxyscrape anonymous': proxies_tplus = '49'
    elif opciones_tplus[ret] == 'Proxyscrape elite': proxies_tplus = '50'
    elif opciones_tplus[ret] == 'Proxyscrape transparent': proxies_tplus = '51'
    elif opciones_tplus[ret] == 'Proxyscrape https': proxies_tplus = '52'
    elif opciones_tplus[ret] == 'Markavale': proxies_tplus = '53'
    elif opciones_tplus[ret] == 'Proxyscan socks4': proxies_tplus = '54'
    elif opciones_tplus[ret] == 'Proxyscan socks5': proxies_tplus = '55'
    elif opciones_tplus[ret] == 'MuRongPIG': proxies_tplus = '57'
    elif opciones_tplus[ret] == 'Vakhov http': proxies_tplus = '58'
    elif opciones_tplus[ret] == 'Vakhov https': proxies_tplus = '59'
    elif opciones_tplus[ret] == 'Vakhov socks4': proxies_tplus = '60'
    elif opciones_tplus[ret] == 'Vakhov socks': proxies_tplus = '61'
    elif opciones_tplus[ret] == 'Hidemium': proxies_tplus = '62'

    else: proxies_tplus = '32'

    config.set_setting('proxies_tplus', proxies_tplus)
    config.set_setting('proxies_tplus_proces', '')

    return proxies_tplus


def test_alfabetico(item):
    logger.info()
    itemlist = []

    if 'Canal' in item.title:
        text_color = 'gold'
        accion = 'test_all_webs'
    else:
        text_color = 'fuchsia'
        accion = 'test_all_srvs'

    for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        itemlist.append(item.clone( title = letra, action = accion, letra = letra.lower(), text_color = text_color  ))

    return itemlist


def test_all_webs(item):
    logger.info()

    config.set_setting('developer_test_channels', '')

    config.set_setting('user_test_channel', '')

    if not item.letra:
        if item.extra == 'sugeridos': text = '¿ Iniciar Test Web Solo de los Canales [B][COLOR aquamarine]Sugeridos[/B][/COLOR] ?'
        elif item.extra == 'clones': text = '¿ Iniciar Test Web Solo de los Canales que sean [B][COLOR turquoise]Clones[/B][/COLOR] ?'
        elif item.extra == 'no_clones': text = '¿ Iniciar Test Web de los Canales Excepto los que sean [B][COLOR turquoise]Clones[/B][/COLOR] ?'
        elif item.extra == 'clons': text = '¿ Iniciar Test Web Solo de los Canales que sean [B][COLOR paleturquoise]Principales[/B][/COLOR] con Clones ?'
        elif item.unsatisfactory: text = '¿ Iniciar Test Web de los Posibles Canales [B][COLOR gold]Insatisfactorios[/B][/COLOR] ?'
        else: text = '¿ Iniciar Test Web de [B][COLOR gold]TODOS[/B][/COLOR] los Canales ?'

        if not platformtools.dialog_yesno(config.__addon_name + ' - Canales', text): return

    if item.unsatisfactory: config.set_setting('developer_test_channels', 'unsatisfactory')

    from core import channeltools

    from modules import tester

    filtros = {}

    channels_list_status = config.get_setting('channels_list_status', default=0)
    if channels_list_status > 0:
        filtros['status'] = 0 if channels_list_status == 1 else 1

    ch_list = channeltools.get_channels_list(filtros=filtros)

    i = 0

    for ch in ch_list:
        if item.extra == 'sugeridos':
            if not 'suggested' in ch['clusters']: continue
        elif item.extra == 'clones':
            if not 'clone' in ch['clusters']: continue
        elif item.extra == 'no_clones':
            if 'clone' in ch['clusters']: continue
        elif item.extra == 'clons':
            if not 'clons' in ch['clusters']: continue

        if config.get_setting('mnu_simple', default=False):
            if 'enlaces torrent exclusivamente' in ch['notes']: continue
            elif 'exclusivamente al dorama' in ch['notes']: continue
            elif 'exclusivamente al anime' in ch['notes']: continue
            elif '+18' in ch['notes']: continue
        else:
            if not config.get_setting('mnu_torrents', default=False) or config.get_setting('search_no_exclusively_torrents', default=False):
                if 'enlaces torrent exclusivamente' in ch['notes']: continue

            if not config.get_setting('mnu_doramas', default=True):
                if 'exclusivamente al dorama' in ch['notes']: continue

            if not config.get_setting('mnu_animes', default=True):
                if 'exclusivamente al anime' in ch['notes']: continue

            if not config.get_setting('mnu_adultos', default=True):
                if '+18' in ch['notes']: continue

        i += 1

        try:
            if item.letra:
                el_canal = ch['id']

                if el_canal[0] < item.letra:
                    i -= 1
                    continue

            txt = tester.test_channel(ch['name'])
        except:
            if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[B][COLOR red]Error en la comprobación.[/B][/COLOR]', '[COLOR yellowgreen][B]¿ Desea comprobar el Canal de nuevo ?[/B][/COLOR]'):
                try: txt = tester.test_channel(ch['name'])
                except:
                     platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] ' + ch['name'] + '[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Canal Ignorado[/B][/COLOR]' % color_alert)
                     tests_all_webs.append(ch['name'] + '  Error Comprobacion Canal')
                     continue
            else:
                tests_all_webs.append(ch['name'] + '  Error Canal Ignorado')
                continue

        rememorize = False

        if not txt: continue

        if 'code: [COLOR springgreen][B]200' in str(txt):
            if 'invalid:' in str(txt):
                platformtools.dialog_textviewer(ch['name'], txt)

                if ' con proxies ' in str(txt):
                    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]¿ Desea Iniciar una nueva Búsqueda de Proxies en el Canal ?[/B][/COLOR]'):
                        _proxies(item, ch['id'])

                        try: txt = tester.test_channel(ch['name'])
                        except:
                             platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] ' + ch['name'] + '[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Canal Ignorado[/B][/COLOR]' % color_alert)
                             tests_all_webs.append(ch['name'] + '  Error Comprobacion con Proxies')
                             continue

                        if not 'code: [COLOR springgreen][B]200' in str(txt):
                            if ' con proxies ' in str(txt):
                                platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado Buscando Nuevos Proxies.[/B][/COLOR]')
                                tests_all_webs.append(ch['name'] + '  Sin Nuevos Proxies')
                                continue
                        else:
                            rememorize = True

                elif 'Sin proxies' in str(txt):
                    if 'CloudFlare Human Verify' in txt:
                        tests_all_webs.append(ch['name'] + '  CloudFlare Human Verify')
                        continue

                    elif '[CR]robot: [COLOR indianred][B]CloudFlare[/B][/COLOR]' in txt:
                        tests_all_webs.append(ch['name'] + '  Robot Protection')
                        continue

                    elif '[B]Host error NO responde[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Sin Respuesta del Host')
                        continue

                    elif '[B]No se puede acceder a este sitio web.[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  No se Puede acceder al sitio Web')
                        continue

                    elif '[B]La Cuenta está Suspendida.[/B]' in txt or '[B]Suspendida[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Cuenta Suspendida')
                        continue

                    elif '[B]Dominio Expirado[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Dominio Expirado')
                        continue

                    elif '[B]Copyright infringement[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Copyright infringement')
                        continue

                    elif 'sucess: [COLOR red][B]False[/B]' in txt or '[CR]length: 0[CR]' in txt:
                        tests_all_webs.append(ch['name'] + '  Acceso Sin datos')
                        continue

                    elif '[I]El test del Canal NO ha resultado Satisfactorio.[/I]' in txt:
                        tests_all_webs.append(ch['name'] + '  Resultado Insatisfactorio')
                        continue

                    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR chartreuse][B]Quizás necesite Proxies.[/B][/COLOR] ¿ Desea Iniciar la Búsqueda de Proxies en el Canal ?'):
                        _proxies(item, ch['id'])

                        try: txt = tester.test_channel(ch['name'])
                        except:
                             platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] ' + ch['name'] + '[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Canal Ignorado[/B][/COLOR]' % color_alert)
                             tests_all_webs.append(ch['name'] + '  Error Comprobacion Quizas Necesite Proxies')
                             continue

                        if not 'code: [COLOR springgreen][B]200' in str(txt):
                            if 'Sin proxies' in str(txt):
                                platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado Buscando Nuevos Proxies.[/B][/COLOR]')
                                tests_all_webs.append(ch['name'] + '  Sin Nuevos Proxies')
                                continue
                        else:
                            rememorize = True

                if 'invalid:' in str(txt):
                    if not 'Suspendida' in str(txt):
                        if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '¿ Desea comprobar el Canal de nuevo, [COLOR red][B]por Acceso sin Host Válido en los datos. [/B][/COLOR]?'):

                            try: txt = tester.test_channel(ch['name'])
                            except:
                                 platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] ' + ch['name'] + '[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Canal Ignorado[/B][/COLOR]' % color_alert)
                                 tests_all_webs.append(ch['name'] + '  Error Comprobacion Acceso Sin Host Valido')
                                 continue

                            if 'code: [COLOR springgreen][B]200' in str(txt):
                                if 'invalid:' in str(txt):
                                    platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado el Acceso sin Host Válido en los datos.[/B][/COLOR]')
                                    tests_all_webs.append(ch['name'] + '  Acceso Sin Host Valido')
                                    continue

            elif 'Falso Positivo.' in str(txt):
                platformtools.dialog_textviewer(ch['name'], txt)

                if ' con proxies ' in str(txt):
                    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]¿ Desea Iniciar una nueva Búsqueda de Proxies en el Canal ?[/B][/COLOR]'):
                        _proxies(item, ch['id'])

                        try: txt = tester.test_channel(ch['name'])
                        except:
                              platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] ' + ch['name'] + '[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Canal Ignorado[/B][/COLOR]' % color_alert)
                              tests_all_webs.append(ch['name'] + '  Error Comprobacion Nueva Busqueda de Proxies')
                              continue

                        if not 'code: [COLOR springgreen][B]200' in str(txt):
                            if ' con proxies ' in str(txt):
                                platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado Buscando Nuevos Proxies.[/B][/COLOR]')
                                tests_all_webs.append(ch['name'] + '  Sin Solucion Buscando Nuevos Proxies')
                                continue
                        else:
                            rememorize = True

                elif 'Sin proxies' in str(txt):
                    if 'CloudFlare Human Verify' in txt:
                        tests_all_webs.append(ch['name'] + '  CloudFlare Human Verify')
                        continue

                    elif '[CR]robot: [COLOR indianred][B]CloudFlare[/B][/COLOR]' in txt:
                        tests_all_webs.append(ch['name'] + '  Robot Protection')
                        continue

                    elif '[B]Host error NO responde[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Sin Respuesta del Host')
                        continue

                    elif '[B]No se puede acceder a este sitio web.[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  No se Puede acceder al sitio Web')
                        continue

                    elif '[B]La Cuenta está Suspendida.[/B]' in txt or '[B]Suspendida[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Cuenta Suspendida')
                        continue

                    elif '[B]Dominio Expirado[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Dominio Expirado')
                        continue

                    elif '[B]Copyright infringement[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Copyright infringement')
                        continue

                    elif 'sucess: [COLOR red][B]False[/B]' in txt or '[CR]length: 0[CR]' in txt:
                        tests_all_webs.append(ch['name'] + '  Acceso Sin datos')
                        continue

                    elif '[I]El test del Canal NO ha resultado Satisfactorio.[/I]' in txt:
                        tests_all_webs.append(ch['name'] + '  Resultado Insatisfactorio')
                        continue

                    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR chartreuse][B]Quizás necesite Proxies.[/B][/COLOR] ¿ Desea Iniciar la Búsqueda de Proxies en el Canal ?'):
                        _proxies(item, ch['id'])

                        try: txt = tester.test_channel(ch['name'])
                        except:
                             platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] ' + ch['name'] + '[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Canal Ignorado[/B][/COLOR]' % color_alert)
                             tests_all_webs.append(ch['name'] + '  Error Comprobacion Quizas Necesite Nuevos Proxies')
                             continue

                        if not 'code: [COLOR springgreen][B]200' in str(txt):
                            if 'Sin proxies' in str(txt):
                                platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado Buscando Nuevos Proxies.[/B][/COLOR]')
                                tests_all_webs.append(ch['name'] + '  Sin Solucion Buscando Nuevos Proxies')
                                continue
                        else:
                            rememorize = True

                else:
                    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '¿ Desea comprobar el Canal de nuevo, [COLOR red][B]por Falso Positivo. [/B][/COLOR]?'):

                        try: txt = tester.test_channel(ch['name'])
                        except:
                             platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] ' + ch['name'] + '[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Canal Ignorado[/B][/COLOR]' % color_alert)
                             tests_all_webs.append(ch['name'] + '  Error Comprobacion Falso Positivo')
                             continue

                        if 'code: [COLOR springgreen][B]200' in str(txt):
                            if 'Falso Positivo.' in str(txt):
                                platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado el Falso Positivo.[/B][/COLOR]')
                                tests_all_webs.append(ch['name'] + '  Sin Solucion Falso Positivo')
                                continue

            if txt_status:
                if con_incidencias:
                    host_incid = ch['name']

                    if host_incid in str(con_incidencias):
                        incidencia = ''

                        incids = scrapertools.find_multiple_matches(str(con_incidencias), '[COLOR moccasin](.*?)[/B][/COLOR]')

                        for incid in incids:
                            if not ' ' + host_incid + ' ' in str(incid): continue

                            incidencia = incid
                            break

                        if incidencia:
                            tests_all_webs.append(ch['name'] + '  Con Incidencia')
                            continue

                if no_accesibles:
                    host_incid = ch['name']

                    if host_incid in str(no_accesibles):
                        incidencia = ''

                        incids = scrapertools.find_multiple_matches(str(no_accesibles), '[COLOR moccasin](.*?)[/B][/COLOR]')

                        for incid in incids:
                            if not ' ' + host_incid + ' ' in str(incid): continue

                            incidencia = incid
                            break

                        if incidencia:
                            tests_all_webs.append(ch['name'] + '  No Accesible')
                            continue

            if ' al parecer No se necesitan' in str(txt):
                if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]¿ Desea Quitar los Proxies del Canal ?[/B][/COLOR], porqué parece que NO se necesitan.'):
                    _quitar_proxies(item, ch['id'])

                    try: txt = tester.test_channel(ch['name'])
                    except:
                         platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] ' + ch['name'] + '[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Canal Ignorado[/B][/COLOR]' % color_alert)
                         tests_all_webs.append(ch['name'] + '  Error Comprobacion Quitar Proxies')
                         continue

                    proxies = config.get_setting('proxies', ch['id'], default='').strip()

                    if not proxies:
                        if config.get_setting('memorize_channels_proxies', default=True):
                            channels_proxies_memorized = config.get_setting('channels_proxies_memorized', default='')

                            el_memorizado = "'" + ch['id'] + "'"

                            if el_memorizado in str(channels_proxies_memorized):
                                channels_proxies_memorized = str(channels_proxies_memorized).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                                config.set_setting('channels_proxies_memorized', channels_proxies_memorized)

        else:

            if 'CloudFlare Human Verify' in txt:
                tests_all_webs.append(ch['name'] + '  CloudFlare Human Verify')
                continue

            elif '[CR]robot: [COLOR indianred][B]CloudFlare[/B][/COLOR]' in txt:
                tests_all_webs.append(ch['name'] + '  Robot Protection')
                continue

            elif '[B]Host error NO responde[/B]' in txt:
                tests_all_webs.append(ch['name'] + '  Sin Respuesta del Host')
                continue

            elif '[B]No se puede acceder a este sitio web.[/B]' in txt:
                tests_all_webs.append(ch['name'] + '  No se Puede acceder al sitio Web')
                continue

            elif '[B]La Cuenta está Suspendida.[/B]' in txt or '[B]Suspendida[/B]' in txt:
                tests_all_webs.append(ch['name'] + '  Cuenta Suspendida')
                continue

            elif '[B]Dominio Expirado[/B]' in txt:
                tests_all_webs.append(ch['name'] + '  Dominio Expirado')
                continue

            elif '[B]Copyright infringement[/B]' in txt:
                tests_all_webs.append(ch['name'] + '  Copyright infringement')
                continue

            elif 'code: [COLOR orangered][B]301' in txt or 'code: [COLOR orangered][B]308' in txt:
                tests_all_webs.append(ch['name'] + '  Nuevo Dominio Temporal')
                continue

            elif 'code: [COLOR orangered][B]302' in txt or 'code: [COLOR orangered][B]307' in txt:
                tests_all_webs.append(ch['name'] + '  Nuevo Dominio Permanente')
                continue

            elif 'Podría estar Correcto' in txt:
                tests_all_webs.append(ch['name'] + '  Podria Estar Correcto')
                continue

            elif '[B]Unknow[/B]' in txt:
                tests_all_webs.append(ch['name'] + '  Error Desconocido Comprobar')
                continue

            elif 'sucess: [COLOR red][B]False[/B]' in txt or '[CR]length: 0[CR]' in txt:
                tests_all_webs.append(ch['name'] + '  Acceso Sin datos')
                continue

            elif '[I]El test del Canal NO ha resultado Satisfactorio.[/I]' in txt:
                tests_all_webs.append(ch['name'] + '  Resultado Insatisfactorio')
                continue

            if txt_status:
                if con_incidencias:
                    host_incid = ch['name']

                    if host_incid in str(con_incidencias):
                        incidencia = ''

                        incids = scrapertools.find_multiple_matches(str(con_incidencias), '[COLOR moccasin](.*?)[/B][/COLOR]')

                        for incid in incids:
                            if not ' ' + host_incid + ' ' in str(incid): continue

                            incidencia = incid
                            break

                        if incidencia:
                            tests_all_webs.append(ch['name'] + '  Con Incidencia')
                            continue

                if no_accesibles:
                    host_incid = ch['name']

                    if host_incid in str(no_accesibles):
                        incidencia = ''

                        incids = scrapertools.find_multiple_matches(str(no_accesibles), '[COLOR moccasin](.*?)[/B][/COLOR]')

                        for incid in incids:
                             if not ' ' + host_incid + ' ' in str(incid): continue

                             incidencia = incid
                             break

                        if incidencia:
                            tests_all_webs.append(ch['name'] + '  No Accesible')
                            continue

                if con_problemas:
                    host_incid = ch['name']

                    if host_incid in str(con_problemas):
                        incidencia = ''

                        incids = scrapertools.find_multiple_matches(str(con_problemas), '[COLOR moccasin](.*?)[/B][/COLOR]')

                        for incid in incids:
                             if not ' ' + host_incid + ' ' in str(incid): continue

                             incidencia = incid
                             break

                        if incidencia:
                            tests_all_webs.append(ch['name'] + '  Con Problema')
                            continue

            if 'nuevo:' in txt:
                tests_all_webs.append(ch['name'] + '  Nuevo Dominio Verificar')
            else:
                if ' con proxies ' in str(txt):
                    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]¿ Desea Iniciar una nueva Búsqueda de Proxies en el Canal ?[/B][/COLOR]'):
                        _proxies(item, ch['id'])

                        try: txt = tester.test_channel(ch['name'])
                        except:
                             platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] ' + ch['name'] + '[/COLOR][/B]', '[B][COLOR  %s]Error comprobación, Canal Ignorado[/B][/COLOR]' % color_alert)
                             tests_all_webs.append(ch['name'] + '  Error Comprobacion Iniciar Nueva Busqueda de Proxies')
                             continue

                        if not 'code: [COLOR springgreen][B]200' in str(txt):
                            if ' con proxies ' in str(txt):
                                platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha  solucionado Buscando Nuevos Proxies.[/B][/COLOR]')
                                tests_all_webs.append(ch['name'] + '  Sin Solucion Buscando Nuevos Proxies')
                                continue
                        else:
                            rememorize = True

                elif 'Sin proxies' in str(txt):
                    if 'CloudFlare Human Verify' in txt:
                        tests_all_webs.append(ch['name'] + '  CloudFlare Human Verify')
                        continue

                    elif '[CR]robot: [COLOR indianred][B]CloudFlare[/B][/COLOR]' in txt:
                        tests_all_webs.append(ch['name'] + '  Robot Protection')
                        continue

                    elif '[B]Host error NO responde[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Sin Respuesta del Host')
                        continue

                    elif '[B]No se puede acceder a este sitio web.[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  No se Puede acceder al sitio Web')
                        continue

                    elif '[B]La Cuenta está Suspendida.[/B]' in txt or '[B]Suspendida[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Cuenta Suspendida')
                        continue

                    elif '[B]Dominio Expirado[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Dominio Expirado')
                        continue

                    elif '[B]Copyright infringement[/B]' in txt:
                        tests_all_webs.append(ch['name'] + '  Copyright infringement')
                        continue

                    elif 'sucess: [COLOR red][B]False[/B]' in txt or '[CR]length: 0[CR]' in txt:
                        tests_all_webs.append(ch['name'] + '  Acceso Sin datos')
                        continue

                    elif '[I]El test del Canal NO ha resultado Satisfactorio.[/I]' in txt:
                        tests_all_webs.append(ch['name'] + '  Resultado Insatisfactorio')
                        continue

                    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR chartreuse][B]Quizás necesite Proxies.[/B][/COLOR] ¿ Desea Iniciar la Búsqueda de Proxies en el Canal ?'):
                        _proxies(item, ch['id'])

                        try: txt = tester.test_channel(ch['name'])
                        except:
                             platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B] ' + ch['name'] + '[/COLOR][/B]', '[B][COLOR %s]Error comprobación, Canal Ignorado[/B][/COLOR]' % color_alert)
                             tests_all_webs.append(ch['name'] + '  Error Comprobacion Quizas Necesite Proxies')
                             continue

                        if not 'code: [COLOR springgreen][B]200' in str(txt):
                            if 'Sin proxies' in str(txt):
                                platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado Buscando Nuevos Proxies.[/B][/COLOR]')
                                tests_all_webs.append(ch['name'] + '  Sin Solucion Buscando Nuevos Proxies')
                                continue
                        else:
                            rememorize = True

                else:
                    tests_all_webs.append(ch['name'] + '  Verificar Canal')

        if rememorize:
            proxies = config.get_setting('proxies', ch['id'], default='').strip()

            if proxies:
                if config.get_setting('memorize_channels_proxies', default=True):
                    channels_proxies_memorized = config.get_setting('channels_proxies_memorized', default='')

                    el_memorizado = "'" + ch['id'] + "'"

                    if not el_memorizado in str(channels_proxies_memorized):
                        channels_proxies_memorized = channels_proxies_memorized + ', ' + el_memorizado
                        config.set_setting('channels_proxies_memorized', channels_proxies_memorized)

    if i == 0:
        platformtools.dialog_ok(config.__addon_name, 'Sin Canales Testeados')
    else:
        if not tests_all_webs:
            platformtools.dialog_ok(config.__addon_name, 'Canales Testeados ' + str(i))
        else:
            conflictos = len(tests_all_webs)

            if config.get_setting('developer_team'):
                canales_log = os.path.join(config.get_data_path(), 'canales.log')

                txt_log = ''

                for conflict in tests_all_webs:
                    txt_log += conflict + os.linesep

                with open(canales_log, 'wb') as f: f.write(txt_log if not PY3 else txt_log.encode('utf-8')); f.close()

            if platformtools.dialog_yesno(config.__addon_name + ' Tests Canales', '[B][COLOR gold]Canales Testeados ' + str(i) + '[/B][/COLOR]', '[B][COLOR red]Con Conflictos ' + str(conflictos) + '[/B][/COLOR]', '[COLOR yellow][B]¿ Desea Ver los conflictos ?[/B][/COLOR]'):
                txt_conflict = ''

                for conflict in tests_all_webs:
                    txt_conflict += conflict + '[CR]'

                platformtools.dialog_textviewer('Canales con Conflictos', txt_conflict)

    config.set_setting('developer_test_channels', '')

    config.set_setting('user_test_channel', '')


def test_one_channel(item):
    logger.info()

    config.set_setting('developer_test_channels', '')

    config.set_setting('user_test_channel', '')

    try:
        filters.show_channels_list(item)
    except:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR red]Error comprobación, Reintentelo de Nuevo[/B][/COLOR]')


def _proxies(item, channel):
    item.from_channel = channel

    from modules import submnuctext
    submnuctext._proxies(item)
    return True


def _quitar_proxies(item, channel):
    item.from_channel = channel

    config.set_setting('proxies', '', item.from_channel)


def test_all_srvs(item):
    logger.info()

    config.set_setting('developer_test_servers', '')

    if not item.letra:
        if item.unsatisfactory: text = '¿ Iniciar Test Web de los Posibles Servidores [B][COLOR fuchsia]Insatisfactorios[/B][/COLOR] ?'
        else: text = '¿ Iniciar Test Web de [B][COLOR fuchsia]TODOS[/B][/COLOR] los Servidores ?'

        if not platformtools.dialog_yesno(config.__addon_name + ' - Servidores', text): return

    if item.unsatisfactory: config.set_setting('developer_test_servers', 'unsatisfactory')


    from modules import tester

    path = os.path.join(config.get_runtime_path(), 'servers')

    servidores = os.listdir(path)
    servidores = sorted(servidores)

    i = 0

    for server in servidores:
        if not server.endswith('.json'): continue

        path_server = os.path.join(config.get_runtime_path(), 'servers', server)

        if not os.path.isfile(path_server): continue

        data = filetools.read(path_server)
        dict_server = jsontools.load(data)

        if dict_server['active'] == False: continue

        try:
           notes = dict_server['notes']
        except: 
           notes = ''

        if "out of service" in notes.lower():
            if item.unsatisfactory: continue

        el_servidor = dict_server['name']
        el_servidor = el_servidor.lower()

        if el_servidor == 'various' or el_servidor == 'waaw' or el_servidor == 'zures':
            if item.unsatisfactory: continue

        i += 1

        txt = ''

        try:
            if item.letra:
                el_servidor = dict_server['name']
                el_servidor = el_servidor.lower()

                if el_servidor[0] < item.letra:
                    i -= 1
                    continue

            txt = tester.test_server(dict_server['name'])
        except:
            if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + dict_server['name'] + '[/B][/COLOR]', '[B][COLOR red]Error en la comprobación.[/B][/COLOR]', '[COLOR yellowgreen][B]¿ Desea comprobar el Servidor de nuevo ?[/B][/COLOR]'):
                try: txt = tester.test_server(dict_server['name'])
                except:
                     platformtools.dialog_notification(config.__addon_name + ' [COLOR yellow][B]' + dict_server['name'] + '[/B][/COLOR]', '[B][COLOR %s]Error comprobación, Servidor ignorado[/B][/COLOR]' % color_alert)
                     tests_all_srvs.append(dict_server['name'] + '  Error Comprobacion Servidor')
                     continue
            else:
                tests_all_srvs.append(dict_server['name'] + '  Error Servidor Ignorado')
                continue

        if txt_status:
            if srv_pending:
                srv_incid = dict_server['name']

                if srv_incid in str(srv_pending):
                    incidencia = ''

                    incids = scrapertools.find_multiple_matches(str(srv_pending), '[COLOR orchid](.*?)[/B][/COLOR]')

                    for incid in incids:
                         if not ' ' + srv_incid + ' ' in str(incid): continue

                         incidencia = incid
                         break

                    if incidencia:
                        tests_all_srvs.append(dict_server['name'] + '  Con Incidencia')
                        continue

        if not txt: continue

        if not 'code: [COLOR springgreen][B]200' in str(txt):
            if '[B]Copyright infringement[/B]' in txt:
                tests_all_srvs.append(dict_server['name'] + '  Copyright infringement')
                continue

            elif 'nuevo:' in txt:
                tests_all_srvs.append(dict_server['name'] + '  Nuevo Dominio Verificar')
                continue

            elif '[B]Cloudflare[/B][/COLOR][COLOR red][B] Protection[/B]' in txt:
                tests_all_srvs.append(dict_server['name'] + '  CloudFlare Protection')
                continue

            elif '[B]Host error NO responde[/B]' in txt:
                tests_all_srvs.append(dict_server['name'] + '  Sin Respuesta del Host')
                continue

            elif '[B]No se puede acceder a este sitio web.[/B]' in txt:
                tests_all_srvs.append(dict_server['name'] + '  No se Puede acceder al sitio Web')
                continue

            elif '[B]Dominio Expirado[/B]' in txt:
                tests_all_srvs.append(dict_server['name'] + '  Dominio Expirado')
                continue

            elif 'code: [COLOR orangered][B]301' in txt or 'code: [COLOR orangered][B]308' in txt:
                tests_all_srvs.append(dict_server['name'] + '  Nuevo Dominio Temporal')
                continue

            elif 'Podría estar Correcto' in txt:
                tests_all_srvs.append(dict_server['name'] + '  Podria Estar Correcto')
                continue

            elif 'code: [COLOR orangered][B]302' in txt or 'code: [COLOR orangered][B]307' in txt:
                tests_all_srvs.append(dict_server['name'] + '  Nuevo Dominio Permanente')
                continue

            elif '[B]Unknow[/B]' in txt:
                tests_all_srvs.append(dict_server['name'] + '  Error Desconocido Comprobar')
                continue

            elif 'sucess: [COLOR red][B]False[/B]' in txt or '[CR]length: 0[CR]' in txt:
                tests_all_srvs.append(dict_server['name'] + '  Acceso Sin datos')
                continue

            elif '[I]El test del Servidor NO ha resultado Satisfactorio.[/I]' in txt:
                tests_all_srvs.append(dict_server['name'] + '  Resultado Insatisfactorio')
                continue

            tests_all_srvs.append(dict_server['name'] + '  Error Servidor')

    if i == 0:
        platformtools.dialog_ok(config.__addon_name, 'Sin Servidores Testeados')
    else:
        if not tests_all_srvs:
            platformtools.dialog_ok(config.__addon_name, 'Servidores Testeados ' + str(i))
        else:
            conflictos = len(tests_all_srvs)

            if config.get_setting('developer_team'):
                servidores_log = os.path.join(config.get_data_path(), 'servidores.log')

                txt_log = ''

                for conflict in tests_all_srvs:
                    txt_log += conflict + os.linesep

                with open(servidores_log, 'wb') as f: f.write(txt_log if not PY3 else txt_log.encode('utf-8')); f.close()

            if platformtools.dialog_yesno(config.__addon_name + ' Tests Servidores', '[B][COLOR gold]Servidores Testeados ' + str(i) + '[/B][/COLOR]', '[B][COLOR red]Con Conflictos ' + str(conflictos) + '[/B][/COLOR]', '[COLOR yellow][B]¿ Desea Ver los conflictos ?[/B][/COLOR]'):
                txt_conflict = ''

                for conflict in tests_all_srvs:
                    txt_conflict += conflict + '[CR]'

                platformtools.dialog_textviewer('Servidores con Conflictos', txt_conflict)

    config.set_setting('developer_test_servers', '')


def test_one_server(item):
    logger.info()

    config.set_setting('developer_test_servers', '')

    if not item.tipo: item.tipo = 'activos'

    try:
        filters.show_servers_list(item)
    except:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR red]Error comprobación, Reintentelo de Nuevo[/B][/COLOR]')


def show_addons(item):
    logger.info()

    txt = '[COLOR gold][B]' + item.tipo + ':[/B][/COLOR][CR]'

    for addons in item.addons:
        addons = addons.replace('plugin', '[COLOR yellow]plugin[/COLOR]')
        addons = addons.replace('repository', '[COLOR cyan]repository[/COLOR]')
        addons = addons.replace('script', '[COLOR orange]script[/COLOR]')
        addons = addons.replace('skin', '[COLOR aquamarine]skin[/COLOR]')
        addons = addons.replace('service', '[COLOR violet]service[/COLOR]')
        addons = addons.replace('resource', '[COLOR tomato]resource[/COLOR]')

        addons = addons.replace('inputstream', '[COLOR fuchsia]inputstream[/COLOR]')
        addons = addons.replace('resolveurl', '[COLOR fuchsia]resolveurl[/COLOR]')
        addons = addons.replace('elementum', '[COLOR fuchsia]elementum[/COLOR]')
        addons = addons.replace('youtube', '[COLOR fuchsia]youtube[/COLOR]')

        addons = addons.replace('balandro', '[COLOR yellow]balandro[/COLOR]')

        txt += '  ' + str(addons) + '[CR][CR]'

    titulo = 'Información Add-ons '
    if item.tipo == 'Caché': titulo = 'Información Archivos '

    platformtools.dialog_textviewer(titulo + item.tipo , txt)


def show_help_addons(item):
    logger.info()

    txt = ''

    cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

    if cliente_torrent == 'Seleccionar' or cliente_torrent == 'Ninguno': tex_tor = cliente_torrent
    else:
       tex_tor = cliente_torrent
       cliente_torrent = 'plugin.video.' + cliente_torrent.lower()

       if xbmc.getCondVisibility('System.HasAddon("%s")' % cliente_torrent):
           try:
               cod_version = xbmcaddon.Addon(cliente_torrent).getAddonInfo("version").strip()
               tex_tor += '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
           except:
               tex_tor += '  [COLOR gray]Desactivado[/COLOR]'

       else: tex_tor += '  [COLOR red]No instalado[/COLOR]'

    txt += ' - Cliente/Motor Torrent ' + '[COLOR fuchsia][B] ' + tex_tor + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("script.elementum.burst")'):
        try:
            cod_version = xbmcaddon.Addon("script.elementum.burst").getAddonInfo("version").strip()
            tex_bur = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_bur = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_bur = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]Elementum Burst[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_bur + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("inputstream.adaptive")'):
        try:
            cod_version = xbmcaddon.Addon("inputstream.adaptive").getAddonInfo("version").strip()
            tex_ia = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_ia = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_ia = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]InputStream Adaptive[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_ia + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("inputstream.ffmpegdirect")'):
        try:
            cod_version = xbmcaddon.Addon("inputstream.ffmpegdirect").getAddonInfo("version").strip()
            tex_ia = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_ia = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_ia = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]InputStream Ffmpegdirect[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_ia + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
        try:
            cod_version = xbmcaddon.Addon("plugin.video.youtube").getAddonInfo("version").strip()
            tex_yt = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_yt = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_yt = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]Youtube[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_yt + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        try:
            cod_version = xbmcaddon.Addon("script.module.resolveurl").getAddonInfo("version").strip()
            tex_mr = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_mr = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_mr = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]ResolveUrl[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_mr + '[/B][/COLOR][CR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("repository.resolveurl")'):
        try:
            cod_version = xbmcaddon.Addon("repository.resolveurl").getAddonInfo("version").strip()
            tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_rp = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR cyan][B]Repository ResolveUrl[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + '[/B][/COLOR][CR]'

    if not PY3:
        if xbmc.getCondVisibility('System.HasAddon("repository.elementum")'):
            try:
                cod_version = xbmcaddon.Addon("repository.elementum").getAddonInfo("version").strip()
                tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
            except:
                tex_rp = '  [COLOR gray]Desactivado[/COLOR]'
        else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

        txt += ' - [COLOR cyan][B]Repository Elementum[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + ' (hasta K18.x)[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("repository.elementumorg")'):
        try:
            cod_version = xbmcaddon.Addon("repository.elementumorg").getAddonInfo("version").strip()
            tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_yt = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR cyan][B]Repository ElementumOrg[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + '[/B][/COLOR][CR]'

    platformtools.dialog_textviewer('Información Add-Ons Externos', txt)


def show_help_torrents(item):
    logger.info()

    txt = ''

    cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

    if cliente_torrent == 'Seleccionar' or cliente_torrent == 'Ninguno': tex_tor = cliente_torrent
    else:
       tex_tor = cliente_torrent
       cliente_torrent = 'plugin.video.' + cliente_torrent.lower()

       if xbmc.getCondVisibility('System.HasAddon("%s")' % cliente_torrent):
           try:
               cod_version = xbmcaddon.Addon(cliente_torrent).getAddonInfo("version").strip()
               tex_tor += '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
           except:
               tex_tor += '  [COLOR gray]Desactivado[/COLOR]'

       else: tex_tor += '  [COLOR red]No instalado[/COLOR]'

    txt += ' - Cliente/Motor Torrent ' + '[COLOR fuchsia][B] ' + tex_tor + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("script.elementum.burst")'):
        try:
            cod_version = xbmcaddon.Addon("script.elementum.burst").getAddonInfo("version").strip()
            tex_bur = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_bur = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_bur = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]Elementum Burst[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_bur + '[/B][/COLOR][CR]'

    if not PY3:
        if xbmc.getCondVisibility('System.HasAddon("repository.elementum")'):
            try:
                cod_version = xbmcaddon.Addon("repository.elementum").getAddonInfo("version").strip()
                tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
            except:
                tex_rp = '  [COLOR gray]Desactivado[/COLOR]'
        else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

        txt += ' - [COLOR gold][B]Repository Elementum[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + ' (hasta K18.x)[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("repository.elementumorg")'):
        try:
            cod_version = xbmcaddon.Addon("repository.elementumorg").getAddonInfo("version").strip()
            tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_yt = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR gold][B]Repository ElementumOrg[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + '[/B][/COLOR][CR]'

    platformtools.dialog_textviewer('Información Add-Ons y Repositorios Torrents', txt)


def show_help_players(item):
    logger.info()

    txt = ''

    if config.get_setting('mnu_torrents', default=True):
        cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

        if cliente_torrent == 'Seleccionar' or cliente_torrent == 'Ninguno': tex_tor = cliente_torrent
        else:
           tex_tor = cliente_torrent
           cliente_torrent = 'plugin.video.' + cliente_torrent.lower()

           if xbmc.getCondVisibility('System.HasAddon("%s")' % cliente_torrent):
               try:
                   cod_version = xbmcaddon.Addon(cliente_torrent).getAddonInfo("version").strip()
                   tex_tor += '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
               except:
                   tex_tor += '  [COLOR gray]Desactivado[/COLOR]'

           else: tex_tor += '  [COLOR red]No instalado[/COLOR]'

        txt += ' - Cliente/Motor Torrent asignado ' + '[COLOR fuchsia][B] ' + tex_tor + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("inputstream.adaptive")'):
        try:
            cod_version = xbmcaddon.Addon("inputstream.adaptive").getAddonInfo("version").strip()
            tex_ia = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_ia = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_ia = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]InputStream Adaptive[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_ia + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("inputstream.ffmpegdirect")'):
        try:
            cod_version = xbmcaddon.Addon("inputstream.ffmpegdirect").getAddonInfo("version").strip()
            tex_ia = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_ia = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_ia = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]InputStream Ffmpegdirect[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_ia + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
        try:
            cod_version = xbmcaddon.Addon("plugin.video.youtube").getAddonInfo("version").strip()
            tex_yt = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_yt = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_yt = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]Youtube[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_yt + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        try:
            cod_version = xbmcaddon.Addon("script.module.resolveurl").getAddonInfo("version").strip()
            tex_mr = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_mr = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_mr = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR fuchsia][B]ResolveUrl[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_mr + '[/B][/COLOR][CR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("repository.resolveurl")'):
        try:
            cod_version = xbmcaddon.Addon("repository.resolveurl").getAddonInfo("version").strip()
            tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
        except:
            tex_rp = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

    txt += ' - [COLOR cyan][B]Repository ResolveUrl[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + '[/B][/COLOR][CR]'

    if config.get_setting('mnu_torrents', default=True):
        if not PY3:
            if xbmc.getCondVisibility('System.HasAddon("repository.elementum")'):
                try:
                    cod_version = xbmcaddon.Addon("repository.elementum").getAddonInfo("version").strip()
                    tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
                except:
                    tex_rp = '  [COLOR gray]Desactivado[/COLOR]'
            else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

            txt += ' - [COLOR cyan][B]Repository Elementum[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + '[/B][/COLOR][CR]'

        if xbmc.getCondVisibility('System.HasAddon("repository.elementumorg")'):
            try:
                cod_version = xbmcaddon.Addon("repository.elementumorg").getAddonInfo("version").strip()
                tex_rp = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
            except:
                tex_rp = '  [COLOR gray]Desactivado[/COLOR]'
        else: tex_rp = '  [COLOR red]No instalado[/COLOR]'

        txt += ' - [COLOR cyan][B]Repository Elementum[/B][/COLOR]' + '[COLOR yellowgreen][B] ' + tex_rp + '[/B][/COLOR][CR]'

    platformtools.dialog_textviewer('Información Add-Ons Players y Repositorios Externos', txt)


def show_sistema(item):
    logger.info()

    txt = '[COLOR goldenrod][B]PREFERENCIAS SISTEMA:[/B][/COLOR][CR]'

    txt += ' - Comprobar existencia Balandro Repo: '

    if config.get_setting('check_repo', default=True): txt += '[COLOR yellow][B] Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR yellowgreen][B] Des-Activado[/B][/COLOR][CR]'

    txt += ' - Comprobar Fixes al Iniciar su Media Center: '

    if config.get_setting('addon_update_atstart', default=True): txt += '[COLOR yellow][B]Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR red][B]Des-Activado[/B][/COLOR][CR]'

    txt += ' - Eliminar su fichero de Cookies al Iniciar su Media Center: '

    if config.get_setting('erase_cookies', default=False): txt += '[COLOR yellow][B] Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR yellowgreen][B] Des-Activado[/B][/COLOR][CR]'

    txt += ' - Obtener y Usar la versión más Reciente/Estable de Chrome/Chromium: '

    if config.get_setting('ver_stable_chrome', default=True): txt += '[COLOR yellow][B] Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR yellowgreen][B] Des-Activado[/B][/COLOR][CR]'

    if config.get_setting('chrome_last_version', default=''): txt += '[CR][COLOR yellow][B] - Versión Chrome/Chromium: [/COLOR][COLOR cyan]' + config.get_setting('chrome_last_version') + ' [/B][/COLOR][CR]'

    txt += '[CR] - Confirmar con el Botón pulsar [COLOR palevioletred][B][OK][/B][/COLOR] en ciertas Notificaciones: '

    if config.get_setting('notification_d_ok', default=False): txt += '[COLOR yellow][B] Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR yellowgreen][B] Des-Activado[/B][/COLOR][CR]'

    txt += ' - Emitir un [COLOR paleturquoise][B]Sonido[/B][/COLOR] al mostrar Avisos/Notificaciones: '

    if config.get_setting('notification_beep', default=False): txt += '[COLOR yellow][B] Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR yellowgreen][B] Des-Activado[/B][/COLOR][CR]'

    txt += '[CR][COLOR goldenrod][B]TIEMPOS DE ESPERA:[/B][/COLOR][CR]'

    if config.get_setting('httptools_timeout', default='15'): txt += ' - [COLOR red][B]Time Out   [/B][/COLOR](tiempo máximo Accesos a [COLOR gold][B]Canales[/B][/COLOR], por defecto 15): [COLOR cyan][B]' + str(config.get_setting('httptools_timeout')) + ' [/B][/COLOR][CR]'

    if config.get_setting('search_timeout', default='3'): txt += ' - [COLOR red][B]Time Out   [/B][/COLOR](tiempo máximo Accesos [COLOR yellow][B]Buscar[/B][/COLOR], por defecto 5): [COLOR cyan][B]' + str(config.get_setting('search_timeout')) + ' [/B][/COLOR][CR]'

    if config.get_setting('channels_repeat', default='30'): txt += ' - [COLOR red][B]Time Out   [/B][/COLOR](tiempo máximo al [COLOR darkcyan][B]Reintentar[/B][/COLOR] acceder a ciertos Canales, por defecto 30): [COLOR cyan][B]' + str(config.get_setting('channels_repeat')) + ' [/B][/COLOR][CR]'

    if config.get_setting('servers_waiting', default='6'): txt += ' - [COLOR red][B]Time Wait[/B][/COLOR] (retardo máximo en el acceso a ciertos [COLOR fuchsia][B]Servidores[/B][/COLOR], por defecto 6): [COLOR cyan][B]' + str(config.get_setting('servers_waiting')) + ' [/B][/COLOR][CR]'

    txt += '[CR][COLOR goldenrod][B]PREFERENCIAS NOTIFICACIONES CANALES:[/B][/COLOR][CR]'

    txt += ' - Notificar los Re-Intentos de acceso en los Canales: '

    if config.get_setting('channels_re_charges', default=True): txt += '[COLOR yellow][B] Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR yellowgreen][B] Des-Activado[/B][/COLOR][CR]'

    txt += ' - Presentar Sin Notificar Todas las Películas en las Listas Especiales: '

    if config.get_setting('channels_charges_movies', default=True): txt += '[COLOR yellow][B] Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR yellowgreen][B] Des-Activado[/B][/COLOR][CR]'

    txt += ' - Notificar cuando No existan Temporadas ó tan solo haya Una: '

    if config.get_setting('channels_seasons', default=True): txt += '[COLOR yellow][B] Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR yellowgreen][B] Des-Activado[/B][/COLOR][CR]'

    txt += ' - Presentar Sin Notificar Todos los Episodios en cada Temporada: '

    if config.get_setting('channels_charges', default=True): txt += '[COLOR yellow][B] Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR yellowgreen][B] Des-Activado[/B][/COLOR][CR]'

    txt += ' - No Presentar la Temporada 0 (Especiales): '

    if config.get_setting('channels_especiales', default=True): txt += '[COLOR yellow][B] Activado[/B][/COLOR][CR]'
    else: txt += '[COLOR yellowgreen][B] Des-Activado[/B][/COLOR][CR]'

    txt += '[CR][COLOR goldenrod][B]DEPURACIÓN:[/B][/COLOR][CR]'

    loglevel = config.get_setting('debug', 0)
    if loglevel == 0: tex_niv = 'Solo Errores'
    elif loglevel == 1: tex_niv = 'Errores e Información'
    else: tex_niv = 'Máxima Información'

    txt += '[COLOR yellow][B] - Nivel de información del fichero [COLOR aqua][B]LOG[/B][/COLOR] (por defecto Error): [COLOR cyan][B]' + tex_niv + ' [/B][/COLOR][CR]'

    txt += '[CR][COLOR goldenrod][B]DESARROLLO:[/B][/COLOR][CR]'

    avisar = False

    if not config.get_setting('developer_team'): avisar = True

    if config.get_setting('developer_mode', default=False):
        if not avisar:
            txt += '- [COLOR crimson][B]Opción Desarrollo:[/B][/COLOR]  [COLOR yellow][B]Opción Habilitada[/B][/COLOR]'
        else:
            txt += '- [COLOR crimson][B]Falso Desarrollo:[/B][/COLOR]  [COLOR yellow][B]Opción Habilitada[/B][/COLOR]'

    platformtools.dialog_textviewer('Información Ajustes del Sistema', txt)


def balandro_log(item):
    logger.info()

    txt_errors = ''
    errors = False
    hay_errors = False

    loglevel = config.get_setting('debug', 0)
    if not loglevel >= 2:
        if not platformtools.dialog_yesno(config.__addon_name, 'El nivel actual de información del fichero LOG de su Media Center NO esta Ajustado al máximo. ¿ Desea no obstante visualizarlo ?'): 
            return

    if platformtools.dialog_yesno(config.__addon_name, '[COLOR cyan][B]¿ Desea localizar los [COLOR red]Errores[COLOR cyan] de ejecución ?[/B][/COLOR]'): 
        errors = True

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
        platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]Media Center NO Oficial[/B][/COLOR]', '[COLOR red][B]No se ha localizado su fichero Log[/B][/COLOR]', '[COLOR yellowgreen][B]Localize su fichero Log, mediante un navegador de archivos en su Media Center.[/B][/COLOR]')
        return

    size = filetools.getsize(file)
    if size > 999999: platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Cargando fichero log[/COLOR][/B]' % color_infor)

    txt = ''

    try:
        for line in open(os.path.join(path, file_log), encoding="utf8").readlines():
            if errors:
                if '[Balandro] Traceback' in line: hay_errors = True

                if hay_errors:
                    if line.startswith(' '): txt_errors += '[B][COLOR yellow]' + line.strip() + '[/COLOR][/B][CR]'
                    else:
                       if not 'Balandro' in line: continue
                       txt_errors += '[B][COLOR cyan]' + line + '[/COLOR][/B][CR]'
            else:
                if 'Balandro' in line: txt += line
    except:
        for line in open(os.path.join(path, file_log)).readlines():
            if errors:
                if '[Balandro] Traceback' in line: hay_errors = True

                if hay_errors:
                    if line.startswith(' '): txt_errors += '[B][COLOR yellow]' + line.strip() + '[/COLOR][/B][CR]'
                    else:
                       if not 'Balandro' in line: continue
                       txt_errors += '[B][COLOR cyan]' + line + '[/COLOR][/B][CR]'
            else:
                if 'Balandro' in line: txt += line

    if errors:
       if not txt_errors:
           platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Fichero Log Sin Errores[/COLOR][/B]' % color_exec)
           return

       txt = txt_errors

    if txt: platformtools.dialog_textviewer('Fichero LOG (ejecución Balandro) de su Media Center', txt)


def resumen_canales(item):
    logger.info()

    from core import channeltools

    total = 0

    inactives = 0
    cerrados = 0
    anulados = 0
    temporarys = 0
    mismatcheds = 0
    inestables = 0
    problematics = 0
    clons = 0
    clones = 0
    notices = 0
    cryptos = 0
    proxies = 0
    registers = 0
    dominios = 0
    currents = 0
    streaminytorrent = 0
    onlyones = 0
    nosearchables = 0
    status_access = 0
    status_problems = 0
    con_proxies = 0

    bus_pelisyoseries = 0
    bus_pelis = 0
    bus_series = 0
    bus_documentaryes = 0
    bus_documentales = 0
    bus_infantiles = 0
    bus_kids = 0
    bus_torrents = 0
    bus_doramas = 0
    bus_animes = 0
    bus_trailers = 0

    disponibles = 0
    suggesteds = 0
    peliculas = 0
    series = 0
    pelisyseries = 0
    generos = 40
    documentarys = 0
    infantiles = 0
    tales = 0
    bibles = 0
    torrents = 0
    doramas = 0
    animes = 0
    adults = 0
    trailers = 0
    privates = 0
    others = 0
    no_actives = 0

    temas_adults = 0

    filtros = {'active': False}
    ch_list = channeltools.get_channels_list(filtros=filtros)

    for ch in ch_list:
        total += 1

        if ch['active'] == False:
            if not 'temporary' in ch['clusters']:
                inactives += 1

                if 'Web CERRADA' in ch['notes']: cerrados += 1
                elif 'Web ANULADA' in ch['notes']: anulados += 1
                elif 'Canal Privado' in ch['notes']: privates += 1

                else: others += 1

            else:
                inactives += 1

                temporarys += 1

                if 'privates' in ch['clusters']:
                    el_canal = ch['id']
                    if os.path.exists(os.path.join(config.get_runtime_path(), 'channels', el_canal + '.py')): privates += 1

    filtros = {}
    ch_list = channeltools.get_channels_list(filtros=filtros)

    if ch_list:
        txt_ch = ''

        for ch in ch_list:
            if not ch['status'] == -1: continue
            no_actives += 1

    filtros = {'active': True}
    ch_list = channeltools.get_channels_list(filtros=filtros)

    for ch in ch_list:
        total += 1
        disponibles += 1

        if 'mismatched' in ch['clusters']: mismatcheds += 1
        if 'inestable' in ch['clusters']: inestables += 1
        if 'problematic' in ch['clusters']: problematics += 1
        if 'clons' in ch['clusters']: clons += 1
        if 'clone' in ch['clusters']: clones += 1
        if 'notice' in ch['clusters']: notices += 1
        if 'crypto' in ch['clusters']: cryptos += 1
        if 'proxies' in ch['notes'].lower(): proxies += 1
        if 'register' in ch['clusters']: registers += 1
        if 'dominios' in ch['notes'].lower(): dominios += 1
        if 'current' in ch['clusters']: currents += 1
        if 'Canal con enlaces Streaming y Torrent' in ch['notes']: streaminytorrent +=1
        if 'onlyone' in ch['clusters']: onlyones += 1
        if 'suggested' in ch['clusters']: suggesteds += 1

        if ch['searchable'] == False: nosearchables += 1

        tipos = ch['search_types']

        tipos_torrent = ch['categories']

        if 'exclusivamente a los tráilers' in ch['notes']:
            trailers += 1
            bus_trailers += 1
        else:
            if '+18' in ch['notes']: pass
            elif 'exclusivamente al dorama' in ch['notes']: pass
            elif 'exclusivamente al anime' in ch['notes']: pass
            else:
                if 'movie' in tipos:
                    peliculas += 1

                    if ch['searchable']:
                        bus_pelis += 1

                        if not search_no_accesibles:
                            if no_accesibles:
                                if ch['name'] in str(no_accesibles): bus_pelis -= 1
                            if con_problemas:
                                if ch['name'] in str(con_problemas): bus_pelis -= 1

                if 'tvshow' in tipos:
                    if not 'mangas' in ch['notes'].lower():
                        series += 1

                        if ch['searchable']:
                            bus_series += 1

                            if not search_no_accesibles:
                                if no_accesibles:
                                    if ch['name'] in str(no_accesibles): bus_series -= 1
                                if con_problemas:
                                    if ch['name'] in str(con_problemas): bus_series -= 1

            if 'movie' in tipos:
                if 'tvshow' in tipos:
                    if not 'documentary' in tipos:
                        pelisyseries += 1

            if 'movie' in tipos:
                if ch['searchable']:
                    bus_pelisyoseries += 1

                    if not search_no_accesibles:
                        if no_accesibles:
                            if ch['name'] in str(no_accesibles): bus_pelisyoseries -= 1
                        if con_problemas:
                            if ch['name'] in str(con_problemas): bus_pelisyoseries -= 1

            elif 'tvshow' in tipos:
                if ch['searchable']:
                    bus_pelisyoseries += 1

                    if not search_no_accesibles:
                        if no_accesibles:
                            if ch['name'] in str(no_accesibles): bus_pelisyoseries -= 1
                        if con_problemas:
                            if ch['name'] in str(con_problemas): bus_pelisyoseries -= 1

        if 'documentary' in tipos:
            documentarys += 1

            if ch['searchable']:
                bus_documentaryes += 1

                if not search_no_accesibles:
                    if no_accesibles:
                        if ch['name'] in str(no_accesibles): bus_documentaryes -= 1
                    if con_problemas:
                        if ch['name'] in str(con_problemas): bus_documentaryes -= 1

        else:
           if 'docs' in ch['clusters']:
               if ch['searchable']:
                   bus_documentales += 1 

                   if not search_no_accesibles:
                       if no_accesibles:
                           if ch['name'] in str(no_accesibles): bus_documentales -= 1
                       if con_problemas:
                           if ch['name'] in str(con_problemas): bus_documentales -= 1

        if 'infantil' in ch['clusters']:
             infantiles += 1

             if ch['searchable']:
                 bus_infantiles += 1

                 if not search_no_accesibles:
                     if no_accesibles:
                         if ch['name'] in str(no_accesibles): bus_infantiles -= 1
                     if con_problemas:
                         if ch['name'] in str(con_problemas): bus_infantiles -= 1

        else:
            if 'kids' in ch['clusters']:
                if ch['searchable']:
                    bus_kids += 1

                    if not search_no_accesibles:
                        if no_accesibles:
                            if ch['name'] in str(no_accesibles): bus_kids -= 1
                        if con_problemas:
                            if ch['name'] in str(con_problemas): bus_kids -= 1

        if 'tales' in ch['clusters']: tales += 1

        if 'bibles' in ch['clusters']: bibles += 1

        if 'torrent' in tipos_torrent:
            if not 'Streaming y Torrent' in ch['notes']: torrents += 1

            if ch['searchable']: 
                bus_torrents += 1

                if not search_no_accesibles:
                    if no_accesibles:
                        if ch['name'] in str(no_accesibles): bus_torrents -= 1
                    if con_problemas:
                        if ch['name'] in str(con_problemas): bus_torrents -= 1

        else:
           if 'torrents' in ch['clusters']:
               if ch['searchable']:
                   bus_torrents += 1

                   if not search_no_accesibles:
                       if no_accesibles:
                           if ch['name'] in str(no_accesibles): bus_torrents -= 1
                       if con_problemas:
                           if ch['name'] in str(con_problemas): bus_torrents -= 1

        if 'exclusivamente al dorama' in ch['notes']:
            doramas += 1

            bus_doramas += 1

            if not search_no_accesibles:
                if no_accesibles:
                    if ch['name'] in str(no_accesibles): bus_doramas -= 1
                if con_problemas:
                    if ch['name'] in str(con_problemas): bus_doramas -= 1

        else:
            if 'dorama' in ch['clusters']:
                if 'Animes, Ovas, Doramas y Mangas' in ch['notes']: doramas += 1

                if ch['searchable']:
                    bus_doramas += 1

                    if not search_no_accesibles:
                        if no_accesibles:
                            if ch['name'] in str(no_accesibles): bus_doramas -= 1
                        if con_problemas:
                            if ch['name'] in str(con_problemas): bus_doramas -= 1

        if 'exclusivamente al anime' in ch['notes']:
            animes += 1

            bus_animes += 1

            if not search_no_accesibles:
                if no_accesibles:
                    if ch['name'] in str(no_accesibles): bus_animes -= 1
                if con_problemas:
                    if ch['name'] in str(con_problemas): bus_animes -= 1

        else:
            if 'anime' in ch['clusters']:
                if 'Animes, Ovas, Doramas y Mangas' in ch['notes']: animes += 1

                if ch['searchable']:
                    bus_animes += 1

                    if not search_no_accesibles:
                        if no_accesibles:
                            if ch['name'] in str(no_accesibles): bus_animes -= 1
                        if con_problemas:
                            if ch['name'] in str(con_problemas): bus_animes -= 1

        if config.get_setting('mnu_adultos', default=True):
            if '+18' in ch['notes']: adults += 1

        if 'adults' in ch['clusters']:
            if not config.get_setting('descartar_xxx', default=False): temas_adults += 1

        if 'privates' in ch['clusters']:
            el_canal = ch['id']
            if os.path.exists(os.path.join(config.get_runtime_path(), 'channels', el_canal + '.py')): privates += 1

    txt = '[COLOR yellow][B]RESUMEN SITUACIÓN CANALES:[/B][/COLOR][CR]'

    txt += '  ' + str(total) + ' [COLOR darkorange][B]CANALES[/B][/COLOR][CR]'

    activos = (total - inactives)

    txt += '           ' + str(activos) + ' [COLOR cyan][B]Activos[/B][/COLOR][CR]'

    if not inactives == 0:
        txt += '             ' + str(inactives) + ' [COLOR palevioletred][B]Inactivos[/B][/COLOR][CR]'

        if not cerrados == 0: txt += '                   [COLOR darkred][B]Cerrados[/B][/COLOR] ' + str(cerrados) + '[CR]'
        if not anulados == 0: txt += '                   [COLOR darkviolet][B]Anulados[/B][/COLOR] ' + str(anulados) + '[CR]'

        if not others == 0: txt += '                   [COLOR palegoldenrod][B]Otros[/B][/COLOR] ' + str(others) + '[CR]'
        if not temporarys == 0: txt += '                   [COLOR mediumaquamarine][B]Temporalmente[/B][/COLOR] ' + str(temporarys) + '[CR]'

        if not privates == 0: txt += '                   [COLOR grey][B]Privados[/B][/COLOR] ' + str(privates) + '[CR]'

    txt += '[CR]  ' + str(activos) + ' [COLOR cyan][B]CANALES ACTIVOS DISTRIBUCIÓN:[/B][/COLOR][CR]'

    if not PY3:
        if not mismatcheds == 0: txt +=  '          [COLOR violet][B]Con Posible Incompatibilidad[/B][/COLOR] ' + str(mismatcheds) + '[CR]'

    if not inestables == 0: txt += '          [COLOR plum][B]Inestables[/B][/COLOR] ' + str(inestables) + '[CR]'

    if not problematics == 0: txt += '          [COLOR darkgoldenrod][B]Problemáticos[/B][/COLOR] ' + str(problematics) + '[CR]'

    if not clons == 0:txt += '          [COLOR aquamarine][B]Principales con Clones[/B][/COLOR] ' + str(clons) + '[CR]' 

    if not clones == 0: txt += '          [COLOR turquoise][B]Que son Clones de un Canal Principal[/B][/COLOR] ' + str(clones) + '[CR]'

    if not notices == 0: txt += '          [COLOR olivedrab][B]Con Control CloudFlare Protection[/B][/COLOR] ' + str(notices) + '[CR]'

    if not cryptos == 0: txt += '          [COLOR darksalmon][B]Que Requieren Descifrar Enlaces[/B][/COLOR] ' + str(cryptos) + '[CR]' 

    if not proxies == 0: txt += '          [COLOR red][B]Que Pueden Usar Proxies[/B][/COLOR] ' + str(proxies) + '[CR]'

    if not registers == 0: txt += '          [COLOR teal][B]Que Requieren Cuenta[/B][/COLOR] ' + str(registers) + '[CR]'

    if not dominios == 0: txt += '          [COLOR green][B]Con Varios Dominios[/B][/COLOR] ' + str(dominios) + '[CR]'

    if not currents == 0: txt += '          [COLOR goldenrod][B]Con Gestión Dominio Vigente[/B][/COLOR] ' + str(currents) + '[CR]'

    if not streaminytorrent == 0: txt += '          [COLOR magenta][B]Con enlaces Streaming y Torrent[/B][/COLOR] ' + str(streaminytorrent) +'[CR]'

    if not onlyones == 0: txt += '          [COLOR fuchsia][B]Con un Único Servidor[/B][/COLOR] ' + str(onlyones) + '[CR]'

    if not nosearchables == 0: txt += '          [COLOR aquamarine][B]Que No Intervienen en Búsquedas[/B][/COLOR] ' + str(nosearchables) + '[CR]'

    con_tipologia = (mismatcheds + inestables + problematics + clons + clones + notices + cryptos + proxies + registers + dominios + currents + streaminytorrent + onlyones + nosearchables)

    sin_tipologia = (activos - con_tipologia)
    sin_tipologia = (sin_tipologia * (- 1))
 
    txt += '          [COLOR palegreen][B]Sin Tipología Especial[/B][/COLOR] ' + str(sin_tipologia) + '[CR]'

    if txt_status:
        if no_accesibles:
            matches = no_accesibles.count('[COLOR lime]')

            if matches:
                status_access = matches

        if con_problemas:
            matches = con_problemas.count('[COLOR lime]')

            if matches:
                status_problems = matches

    txt += '[CR]  ' + str(disponibles) + ' [COLOR gold][B]CANALES ACTIVOS DISPONIBLES:[/B][/COLOR][CR]'

    if not status_access == 0: txt += '          [COLOR indianred][B]No Accesibles[/COLOR] '  + str(status_access) + '[/B][CR]'
    if not status_problems == 0: txt += '          [COLOR tomato][B]Con Problemas[/COLOR] '  + str(status_problems) + '[/B][CR]'

    if not (status_access + status_problems) == 0:
        accesibles = (disponibles - status_access - status_problems)

        txt += '         ' + ' [COLOR powderblue][B]Accesibles[/COLOR] ' + str(accesibles) + '[/B][CR]'

    if txt_status:
        if con_incidencias:
            matches = con_incidencias.count('[COLOR lime]')

            if matches:
                status_incid = matches

                txt += '          [COLOR tan][B]Con Incidencias[/COLOR] ' + str(status_incid) + '[/B][CR]'

    if not no_actives == 0: txt += '          [COLOR gray][B]Desactivados[/COLOR] ' + str(no_actives) + '[/B][CR]'

    filtros = {}

    ch_list = channeltools.get_channels_list(filtros=filtros)

    if ch_list:
        for ch in ch_list:
            cfg_proxies_channel = 'channel_' + ch['id'] + '_proxies'

            if not config.get_setting(cfg_proxies_channel, default=''): continue

            con_proxies += 1

        if con_proxies > 0: txt += '          [COLOR red][B]Con Proxies Informados[/COLOR] ' +  str(con_proxies) + '[/B][CR]'

    txt += '[CR][COLOR dodgerblue][B]CANALES DISPONIBLES DISTRIBUCIÓN:[/B][/COLOR]'

    if config.get_setting('mnu_sugeridos', default=True): txt += '[CR]    ' + str(suggesteds) + ' [COLOR moccasin][B]Sugeridos[/B][/COLOR][CR]'

    if config.get_setting('mnu_simple', default=False):
        canales = (disponibles - no_actives)
        txt += '[CR]  ' + str(canales) + ' [COLOR aqua][B]Canales[/B][/COLOR][CR]'

    else:
        if config.get_setting('mnu_pelis', default=True):txt += '[CR]  ' + str(peliculas) + ' [COLOR deepskyblue][B]Películas[/B][/COLOR][CR]' 

        if config.get_setting('mnu_series', default=True): txt += '    ' + str(series) + ' [COLOR hotpink][B]Series[/B][/COLOR][CR]'

        if config.get_setting('channels_link_pyse', default=False): txt += '    ' + str(pelisyseries) + ' [COLOR teal][B]Películas y Series[/B][/COLOR][CR]'

        if config.get_setting('mnu_generos', default=True): txt += '[CR]    ' + str(generos) + '  [COLOR thistle][B]Géneros[/B][/COLOR][CR]'

        if config.get_setting('mnu_documentales', default=True): txt += '    ' + str(documentarys) + '  [COLOR cyan][B]Documentales[/B][/COLOR][CR]'

        if config.get_setting('mnu_infantiles', default=True):
            if not infantiles == 0: txt += '      ' + str(infantiles) + '  [COLOR lightyellow][B]Infantiles[/B][/COLOR][CR]'

        if config.get_setting('mnu_novelas', default=True): txt += '      ' + str(tales) + '  [COLOR limegreen][B]Novelas[/B][/COLOR][CR]'

        if not bibles == 0: txt += '      ' + str(bibles) + '  [COLOR tan][B]Bíblicos[/B][/COLOR][CR]'

        if config.get_setting('mnu_torrents', default=True): txt += '    ' + str(torrents) + ' [COLOR blue][B]Torrents[/B][/COLOR][CR]'

        if config.get_setting('mnu_doramas', default=True): txt += '    ' + str(doramas) + '  [COLOR firebrick][B]Doramas[/B][/COLOR][CR]'

        if config.get_setting('mnu_animes', default=True):
            if not config.get_setting('descartar_anime', default=False): txt += '    ' + str(animes) + '  [COLOR springgreen][B]Animes[/B][/COLOR][CR]'

        if not trailers == 0: txt += '      ' + str(trailers) + '  [COLOR darkgoldenrod][B]Traílers[/B][/COLOR][CR]'

        if config.get_setting('mnu_adultos', default=True):
            if not adults == 0: txt += '    ' + str(adults) + '  [COLOR orange][B]Adultos[/B][/COLOR][CR]'

    txt += '[CR][COLOR powderblue][B]BÚSQUEDAS POR TÍTULO EN CANALES DISPONIBLES:[/B][/COLOR][CR]'

    txt += '  ' + str(bus_pelisyoseries) + ' [COLOR yellow][B]Películas y/ó Series[/B][/COLOR][CR]'

    bus_tematica_documentales = bus_documentales + bus_documentaryes
    txt += '          [COLOR darkcyan][B]Con Temática Documental[/B][/COLOR] ' + str(bus_tematica_documentales) + '[CR]'

    bus_tematica_infantil = bus_kids + bus_infantiles
    txt += '          [COLOR lightyellow][B]Con Temática Infantil[/B][/COLOR] ' + str(bus_tematica_infantil) + '[CR]'

    if not bus_torrents == 0: txt += '          [COLOR blue][B]Con Contenido Torrent[/B][/COLOR] ' + str(bus_torrents) + '[CR]'

    bus_tematica_doramas = bus_doramas + doramas
    if not bus_tematica_doramas == 0: txt += '          [COLOR firebrick][B]Con Temática Dorama[/B][/COLOR] ' + str(bus_tematica_doramas) +'[CR]'

    bus_tematica_animes = bus_animes + animes
    if not bus_tematica_animes == 0:
        if not config.get_setting('descartar_anime', default=True): txt += '          [COLOR springgreen][B]Con Temática Anime[/B][/COLOR] ' + str(bus_tematica_animes) + '[CR]'

    if not temas_adults == 0: txt += '          [COLOR orange][B]Con Temática Adultos[/B][/COLOR] ' + str(temas_adults) + '[CR]'

    if config.get_setting('mnu_pelis', default=True): txt += '[CR]    ' + str(bus_pelis) + ' [COLOR deepskyblue][B]Películas[/B][/COLOR][CR]'

    if config.get_setting('mnu_series', default=True): txt += '    ' + str(bus_series) + ' [COLOR hotpink][B]Series[/B][/COLOR][CR]'

    if config.get_setting('mnu_documentales', default=True): txt += '[CR]    ' + str(bus_tematica_documentales) + ' [COLOR cyan][B]Documentales[/B][/COLOR][CR]'

    if config.get_setting('mnu_torrents', default=True): txt += '    ' + str(torrents) + ' [COLOR blue][B]Torrents[/B][/COLOR][CR]'

    if config.get_setting('mnu_doramas', default=True):
        if not bus_tematica_doramas == 0: txt += '    ' + str(bus_tematica_doramas) + ' [COLOR firebrick][B]Doramas[/B][/COLOR][CR]'

    if config.get_setting('mnu_animes', default=True):
        if not config.get_setting('descartar_anime', default=True):
            if not bus_tematica_animes == 0: txt += '    ' + str(bus_tematica_animes) + ' [COLOR springgreen][B]Animes[/COLOR][/B][CR]'

    if not bus_trailers == 0:
        if config.get_setting('search_extra_trailers', default=False): txt += '      ' + str(bus_trailers) + ' [COLOR darkgoldenrod][B]Traílers[/B][/COLOR]'

    platformtools.dialog_textviewer('Resúmenes de Canales y su Distribución (según sus Ajustes)', txt)


def resumen_incidencias(item):
    logger.info()

    txt = ''

    if txt_status:
        if con_incidencias:
            matches = scrapertools.find_multiple_matches(con_incidencias, "[B](.*?)[/B]")

            for match in matches:
               match = match.strip()

               if '[COLOR moccasin]' in match: txt += '[B' + match + '/I][/B][/COLOR][CR]'

    if not txt:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No Hay Incidencias[/COLOR][/B]' % color_exec)
        return

    platformtools.dialog_textviewer('Canales Con Incidencias', txt)


def resumen_no_accesibles(item):
    logger.info()

    txt = ''

    if txt_status:
        if no_accesibles:
            matches = scrapertools.find_multiple_matches(no_accesibles, "[B](.*?)[/B]")

            for match in matches:
                match = match.strip()

                if '[COLOR moccasin]' in match: txt += '[B' + match + '/I][/B][/COLOR][CR]'

    if not txt:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No Hay No Accesibles[/COLOR][/B]' % color_exec)
        return

    platformtools.dialog_textviewer('Canales No Accesibles', txt)


def resumen_con_problemas(item):
    logger.info()

    txt = ''

    if txt_status:
        if con_problemas:
            matches = scrapertools.find_multiple_matches(con_problemas, "[B](.*?)[/B]")

            for match in matches:
                match = match.strip()

                if '[COLOR moccasin]' in match: txt += '[B' + match + '/I][/B][/COLOR][CR]'

    if not txt:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No Hay Con Problemas[/COLOR][/B]' % color_exec)
        return

    platformtools.dialog_textviewer('Canales Con Problemas', txt)


def resumen_servidores(item):
    logger.info()

    total = 0
    inactives = 0
    notsuported = 0
    outservice = 0
    alternatives = 0

    aditionals = 0
    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
         aditionals = 102  # ~ 44 Various  y  58 Zures

    pending = 0

    path = os.path.join(config.get_runtime_path(), 'servers')

    servidores = os.listdir(path)

    for server in servidores:
        if not server.endswith('.json'): continue

        path_server = os.path.join(config.get_runtime_path(), 'servers', server)

        if not os.path.isfile(path_server): continue

        data = filetools.read(path_server)
        dict_server = jsontools.load(data)

        total += 1

        if dict_server['active'] == False: inactives += 1

        try:
           notes = dict_server['notes']
        except: 
           notes = ''

        if "requiere" in notes.lower(): notsuported += 1
        elif "out of service" in notes.lower(): outservice += 1

        if not dict_server['name'] in ['Various', 'Youtube', 'Zures']:
            if "alternative" in notes.lower(): alternatives += 1

    txt = '[COLOR yellow][B]RESUMEN SITUACIÓN SERVIDORES:[/B][/COLOR][CR]'

    txt += '  ' + str(total) + ' [COLOR darkorange][B]SERVIDORES[/B][/COLOR][CR]'

    inactivos = (inactives + notsuported + outservice)

    disponibles = (total - inactivos)

    txt += '          ' + str(disponibles) + ' [COLOR cyan][B]Activos[/B][/COLOR][CR]'

    if not inactivos == 0:
        txt += '          ' + str(inactivos) + ' [COLOR palevioletred][B]Inactivos[/B][/COLOR][CR]'

        txt += '                [COLOR darkviolet][B]Desactivados[/B][/COLOR] ' + str(inactives) + '[CR]'
        txt += '                [COLOR darkred][B]Sin Soporte[/B][/COLOR] ' + str(notsuported) + '[CR]'

        if outservice > 0: txt += '                [COLOR red][B]Sin Servicio[/B][/COLOR] ' + str(outservice) + '[CR]'

    txt += '[CR]    ' + str(disponibles) + ' [COLOR cyan][B]SERVIDORES ACTIVOS[/B][/COLOR][CR]'

    presentar = False

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'): presentar = True
    elif xbmc.getCondVisibility('System.HasAddon("inputstream.adaptive")'): presentar = True
    elif xbmc.getCondVisibility('System.HasAddon("inputstream.ffmpegdirect")'): presentar = True
    elif xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'): presentar = True
    else:
       cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

       if not cliente_torrent == 'Ninguno':  presentar = True

    if presentar:
        txt += '[COLOR yellow][B][CR]SERVIDORES OTRAS VÍAS:[/B][/COLOR]'

        if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
            try:
                cod_version = xbmcaddon.Addon("script.module.resolveurl").getAddonInfo("version").strip()
                tex_mr = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'
            except:
                tex_mr = '  [COLOR gray]Desactivado[/COLOR]'

            txt += '[CR]  [COLOR goldenrod][B]Resolveurl:[/B][/COLOR][CR]'

            txt += '      Versión' + tex_mr + '[CR]'

            txt += '          ' + str(alternatives) + '  [COLOR green][B]Vías alternativas[/B][/COLOR][CR]'
            txt += '        ' + str(aditionals) + '  [COLOR powderblue][B]Vías Adicionales[/B][/COLOR][CR]'

        cliente_torrent = config.get_setting('cliente_torrent', default='Seleccionar')

        if cliente_torrent == 'Seleccionar' or cliente_torrent == 'Ninguno': tex_tor = cliente_torrent
        else:
           tex_tor = cliente_torrent
           cliente_torrent = 'plugin.video.' + cliente_torrent.lower()

           if xbmc.getCondVisibility('System.HasAddon("%s")' % cliente_torrent):
               try:
                   cod_version = xbmcaddon.Addon(cliente_torrent).getAddonInfo("version").strip()
                   tex_tor += '  [COLOR goldenrod]' + cod_version + '[/COLOR]'

                   aditionals += 1
               except:
                   tex_tor += '  [COLOR gray]Desactivado[/COLOR]'

           else: tex_tor += '  [COLOR red]No instalado[/COLOR]'

        if not cliente_torrent == 'Ninguno':
            txt += '[CR]  [COLOR goldenrod][B]Torrents:[/B][/COLOR][CR]'

            txt += '       1' + '   [COLOR fuchsia][B]' + tex_tor + '[/B][/COLOR][CR]'

        tex_ia = ''

        if xbmc.getCondVisibility('System.HasAddon("inputstream.adaptive")'):
            try:
                cod_version = xbmcaddon.Addon("inputstream.adaptive").getAddonInfo("version").strip()
                tex_ia = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'

                aditionals += 1
            except:
                tex_ia = '  [COLOR gray]Desactivado[/COLOR]'
        else: tex_ia = '  [COLOR red]No instalado[/COLOR]'

        tex_ia = '       1' + '   [COLOR orchid][B]InputStream Adaptive[/B][/COLOR] ' + tex_ia + '[CR]'

        tex_if = ''

        if xbmc.getCondVisibility('System.HasAddon("inputstream.ffmpegdirect")'):
            try:
                cod_version = xbmcaddon.Addon("inputstream.ffmpegdirect").getAddonInfo("version").strip()
                tex_if = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'

                aditionals += 1
            except:
                tex_if = '  [COLOR gray]Desactivado[/COLOR]'
        else: tex_if = '  [COLOR red]No instalado[/COLOR]'

        tex_if = '       1' + '   [COLOR orchid][B]InputStream Ffmpegdirect[/B][/COLOR] ' + tex_if + '[CR]'

        if tex_ia or tex_if:
            txt += '[CR]  [COLOR goldenrod][B]InputStream:[/B][/COLOR][CR]'

            if tex_ia: txt += tex_ia
            if tex_if: txt += tex_if

        if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
            try:
                cod_version = xbmcaddon.Addon("plugin.video.youtube").getAddonInfo("version").strip()
                tex_yt = '  [COLOR goldenrod]' + cod_version + '[/COLOR]'

                aditionals += 1
            except:
                tex_yt = '  [COLOR gray]Desactivado[/COLOR]'
        else: tex_yt = '  [COLOR red]No instalado[/COLOR]'

        txt += '[CR]  [COLOR goldenrod][B]Youtube:[/B][/COLOR][CR]'

        txt += '       1' + '   [COLOR palegoldenrod][B]Vía alternativa[/B][/COLOR]' + tex_yt + '[CR]'

    otrasvias = (aditionals + alternatives)
    txt += '[CR]  ' + str(otrasvias) + ' [COLOR cyan][B]OTRAS VIAS[/B][/COLOR][CR]'

    accesibles = (disponibles + aditionals + alternatives)

    txt += '[CR][COLOR cyan][B]SERVIDORES DISPONIBLES:[/B][/COLOR][CR]'

    txt += '  ' + str(accesibles) + '  [COLOR gold][B]Disponibles[/B][/COLOR][CR]'

    txt += '           [COLOR cyan][B]Activos[/B][/COLOR] ' + str(disponibles) + '[CR]'

    txt += '           [COLOR cyan][B]Otras Vías[/B][/COLOR] ' + str(otrasvias) + '[CR]'

    txt += '[CR][COLOR dodgerblue][B]SERVIDORES ACCESIBLES:[/B][/COLOR][CR]'

    txt += '  ' + str(accesibles) + '  [COLOR powderblue][B]Accesibles[/B][/COLOR][CR]'

    if txt_status:
        if srv_pending:
            matches = srv_pending.count('[COLOR orchid]')

            if matches:
                status = matches

                txt += '           [COLOR tan][B]Con Incidencias[/COLOR] ' + str(status) + '[/B][CR]'

    servers_discarded = config.get_setting('servers_discarded', default='')

    if servers_discarded:
        txt += '[CR][COLOR cyan][B]Descartados:[/B][/COLOR][CR]'
        txt += '   ' + str(servers_discarded)

    platformtools.dialog_textviewer('Resúmenes Servidores y su Distribución  (según sus Ajustes)', txt)


def resumen_pending(item):
    logger.info()

    txt = ''

    if txt_status:
        if srv_pending:
            matches = scrapertools.find_multiple_matches(srv_pending, "[B](.*?)[/B]")

            for match in matches:
                match = match.strip()

                if '[COLOR orchid]' in match: txt += '[B' + match + '/I][/B][/COLOR][CR]'

    if not txt:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No Hay Incidencias[/COLOR][/B]' % color_exec)
        return

    platformtools.dialog_textviewer('Servidores con Incidencias', txt)


def show_help_alternativas(item):
    logger.info()

    txt = ''

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        try:
            cod_version = xbmcaddon.Addon("script.module.resolveurl").getAddonInfo("version").strip()
            tex_mr = '  ' + cod_version
        except:
            tex_mr = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_mr = '[COLOR red][B]No instalado[/B][/COLOR]'

    txt += '[CR][COLOR fuchsia][B]ResolveUrl Script[/B]:[/COLOR]  %s' % tex_mr

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        txt += '[CR][CR] - Qué servidores tienen [COLOR goldenrod][B]Vías Alternativas[/B][/COLOR] a través de [COLOR fuchsia][B]ResolveUrl[/B][/COLOR]:[CR]'

        path = os.path.join(config.get_runtime_path(), 'servers')

        servidores = os.listdir(path)
        servidores = sorted(servidores)

        for server in servidores:
            if not server.endswith('.json'): continue

            path_server = os.path.join(config.get_runtime_path(), 'servers', server)

            if not os.path.isfile(path_server): continue

            data = filetools.read(path_server)
            dict_server = jsontools.load(data)

            if dict_server['active'] == False: continue

            try:
               notes = dict_server['notes']
            except: 
               notes = ''

            if not "alternative" in notes.lower(): continue

            server_name = dict_server['name']

            if server_name == 'Youtube': continue

            txt += '   [COLOR gold][B]' + server_name + '[/B][/COLOR][CR]'

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
        try:
            cod_version = xbmcaddon.Addon("plugin.video.youtube").getAddonInfo("version").strip()
            tex_yt = '  ' + cod_version
        except:
            tex_yt = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_yt = '  [COLOR red]No instalado[/COLOR]'

    txt += '[CR][COLOR fuchsia][B]Youtube Plugin[/B]:[/COLOR]  %s' % tex_yt

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.youtube")'):
        txt += '[CR][CR] - Qué servidor tiene [COLOR goldenrod][B]Vía Alternativa[/B][/COLOR] a través de [COLOR fuchsia][B]YouTube[/B][/COLOR]:[CR]'

        txt += '    [COLOR gold][B]Youtube[/B][/COLOR]'

    platformtools.dialog_textviewer('Servidores Vías Alternativas', txt)


def show_help_adicionales(item):
    logger.info()

    txt = ''

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        try:
            cod_version = xbmcaddon.Addon("script.module.resolveurl").getAddonInfo("version").strip()
            tex_mr = '  ' + cod_version
        except:
            tex_mr = '  [COLOR gray]Desactivado[/COLOR]'
    else: tex_mr = '[COLOR red][B]No instalado[/B][/COLOR]'

    txt += '[CR][COLOR fuchsia][B]ResolveUrl Script[/B]:[/COLOR]  %s' % tex_mr

    if xbmc.getCondVisibility('System.HasAddon("script.module.resolveurl")'):
        txt += '[CR][CR] - Servidores [COLOR goldenrod][B]Vías Adicionales[/B][/COLOR] a través de [COLOR yellowgreen][B]Various[/COLOR][/B] [COLOR fuchsia][B]ResolveUrl[/B][/COLOR]:[CR]'

        path = translatePath(os.path.join(config.get_runtime_path(), 'servers/'))

        file_various = 'various.json'
        path_server = path + file_various

        existe = filetools.exists(path_server)

        if existe:
            data = filetools.read(path_server)
            dict_server = jsontools.load(data)

            if dict_server['active'] == True:
                try:
                   notes = dict_server['notes']
                except: 
                   notes = ''

                notes = notes.replace('Alternative vía: Script.Module.ResolveUrl (', '').replace(')', '').strip()

                notes += ','

                servers_names = scrapertools.find_multiple_matches(notes, '(.*?),')

                for server_name in servers_names:
                    server_name = server_name.strip()

                    txt += '   [COLOR gold][B]' + server_name + '[/B][/COLOR][CR]'

        txt += '[CR] - Servidores [COLOR goldenrod][B]Vías Adicionales[/B][/COLOR] a través de [COLOR yellowgreen][B]Zures[/COLOR][/B] [COLOR fuchsia][B]ResolveUrl[/B][/COLOR]:[CR]'

        file_zures = 'zures.json'
        path_server = path + file_zures

        existe = filetools.exists(path_server)

        if existe:
            data = filetools.read(path_server)
            dict_server = jsontools.load(data)

            if dict_server['active'] == True:
                try:
                   notes = dict_server['notes']
                except: 
                   notes = ''

                notes = notes.replace('Alternative vía: Script.Module.ResolveUrl (', '').replace(')', '').strip()

                notes += ','

                servers_names = scrapertools.find_multiple_matches(notes, '(.*?),')

                for server_name in servers_names:
                    server_name = server_name.strip()

                    txt += '   [COLOR gold][B]' + server_name + '[/B][/COLOR][CR]'

    platformtools.dialog_textviewer('Servidores Vías Adicionales', txt)
