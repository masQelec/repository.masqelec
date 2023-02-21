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


import os

from platformcode import logger, config, platformtools
from core import filetools
from core.item import Item

from modules import filters


def submnu_team(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]Desarrollo:[/B]', thumbnail=config.get_thumb('team'), text_color='darkorange' ))

    itemlist.append(item.clone( action='submnu_center', title=' - [B]Media Center[/B]', thumbnail=config.get_thumb('computer'), text_color='pink' ))

    itemlist.append(item.clone( action='submnu_addons', title=' - [B]Addons[/B]', thumbnail=config.get_thumb('tools'), text_color='yellowgreen' ))

    itemlist.append(item.clone( action='submnu_sistema', title=' - [B]Sistema[/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

    itemlist.append(item.clone( action='submnu_logs', title=' - [B]Logs[/B]', thumbnail=config.get_thumb('tools'), text_color='limegreen' ))

    itemlist.append(item.clone( action='submnu_temporales', title=' - [B]Temporales[/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

    itemlist.append(item.clone( action='submnu_gestionar', title=' - [B]Gestionar[/B]', thumbnail=config.get_thumb('tools'), text_color='teal' ))

    itemlist.append(item.clone( action='submnu_canales', title=' - [B]Tests Canales[/B]', thumbnail=config.get_thumb('tools'), text_color='gold' ))

    itemlist.append(item.clone( action='submnu_servidores', title=' - [B]Tests Servidores[/B]', thumbnail=config.get_thumb('tools'), text_color='fuchsia' ))

    itemlist.append(item.clone( channel='actions', action = 'open_settings', title='[B]Configuración[/B]', thumbnail=config.get_thumb('settings'), text_color='chocolate' ))

    return itemlist


def submnu_center(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]MEDIA CENTER[/B]', thumbnail=config.get_thumb('computer'), text_color='pink' ))

    itemlist.append(item.clone( channel='helper', action='show_plataforma', title='Información [B]Plataforma[/B]', thumbnail=config.get_thumb('computer'), text_color='green' ))

    itemlist.append(item.clone( action='', title='Archivo Log:', thumbnail=config.get_thumb('computer'), text_color='pink' ))

    itemlist.append(item.clone( channel='helper', action='show_log', title=' - Ver', thumbnail=config.get_thumb('computer'), text_color='yellow' ))
    itemlist.append(item.clone( channel='helper', action='copy_log', title=' - Obtener una Copia', thumbnail=config.get_thumb('folder'), text_color='yellowgreen' ))

    presentar = False

    path_advs = translatePath(os.path.join('special://home/userdata', ''))

    file_advs = 'advancedsettings.xml'

    file = path_advs + file_advs

    existe = filetools.exists(file)

    if existe: presentar = True
    if presentar:
        itemlist.append(item.clone( action='', title='Archivo advancedsettings:', thumbnail=config.get_thumb('computer'), text_color='pink' ))

        itemlist.append(item.clone( channel='helper', action='show_advs', title=' - Ver', thumbnail=config.get_thumb('quote'), text_color='yellow' ))
        itemlist.append(item.clone( channel='actions', action='manto_advs', title=' - Eliminar [B][COLOR violet](Si ejecuta es Recomendable Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('quote'), text_color='red' ))

    path_cache = translatePath(os.path.join('special://temp/archive_cache', ''))
    existe_cache = filetools.exists(path_cache)

    caches = []
    if existe_cache: caches = os.listdir(path_cache)

    if caches: presentar = True
    if presentar:
        itemlist.append(item.clone( action='', title='Archivos en Caché:', thumbnail=config.get_thumb('computer'), text_color='pink' ))

        itemlist.append(item.clone( action='show_addons', title=' - Ver', addons = caches, tipo = 'Caché', thumbnail=config.get_thumb('keyboard'), text_color='yellow' ))

        itemlist.append(item.clone( channel='actions', action='manto_caches', title=' - Eliminar [B][COLOR cyan](Si ejecuta es Obligatorio Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    path_thumbs = translatePath(os.path.join('special://home/userdata/Thumbnails', ''))
    existe_thumbs = filetools.exists(path_thumbs)

    if existe_thumbs:
        itemlist.append(item.clone( action='', title='Archivos en Thumbnails:', thumbnail=config.get_thumb('computer'), text_color='pink' ))

        itemlist.append(item.clone( channel='actions', action='manto_thumbs', title=' - Eliminar [B][COLOR cyan](Si ejecuta es Obligatorio Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    return itemlist


def submnu_addons(item):
    logger.info()
    itemlist = []

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
        itemlist.append(item.clone( action='', title='[B]ADDONS[/B]', thumbnail=config.get_thumb('tools'), text_color='yellowgreen' ))

        if packages:
            itemlist.append(item.clone( action='', title='Archivos en Packages:', thumbnail=config.get_thumb('computer'), text_color='yellowgreen' ))

            itemlist.append(item.clone( action='show_addons', title=' - Ver', addons = packages, tipo = 'Packages', thumbnail=config.get_thumb('keyboard'), text_color='yellow' ))

            itemlist.append(item.clone( channel='actions', action='manto_addons_packages', title=' - Eliminar [B][COLOR violet](Si ejecuta es Recomendable Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

        if temps:
            itemlist.append(item.clone( action='', title='Archivos en Temp:', thumbnail=config.get_thumb('computer'), text_color='yellowgreen' ))

            itemlist.append(item.clone( action='show_addons', title=' - Ver', addons = temps, tipo = 'Temp', thumbnail=config.get_thumb('keyboard'), text_color='yellow' ))

            itemlist.append(item.clone( channel='actions', action='manto_addons_temp', title=' - Eliminar [B][COLOR violet](Si ejecuta es Recomendable Re-iniciar Media Center)[/B][/COLOR]', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    return itemlist


def submnu_sistema(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]SISTEMA[/B]', thumbnail=config.get_thumb('tools'), text_color='violet' ))

    itemlist.append(item.clone( channel='actions', action = 'test_internet', title= 'Comprobar el estado de su [COLOR gold][B]Internet[/B][/COLOR]', thumbnail=config.get_thumb('crossroads') ))
    itemlist.append(item.clone( channel='helper', action='show_test', title= 'Test [COLOR gold][B]Status[/B][/COLOR] del sistema', thumbnail=config.get_thumb('addon') ))

    presentar = False

    path = os.path.join(config.get_runtime_path(), 'last_fix.json')

    existe = filetools.exists(path)
    if existe: presentar = True
    if presentar:
        itemlist.append(item.clone( action='', title='Archivo Fix:', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='helper', action='show_last_fix', title= ' - Información [B]Fix instalado[/B]', thumbnail=config.get_thumb('news'), text_color='green' ))
        itemlist.append(item.clone( channel='actions', action='manto_last_fix', title= " - Eliminar fichero control 'Fix'", thumbnail=config.get_thumb('news'), text_color='red' ))

    presentar = False

    path = os.path.join(config.get_data_path(), 'cookies.dat')

    existe = filetools.exists(path)
    if existe: presentar = True
    if presentar:
        itemlist.append(item.clone( action='', title='Archivo Cookies:', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_cookies', title= " - Eliminar", thumbnail=config.get_thumb('computer'), text_color='red' ))

    presentar = False

    path = os.path.join(config.get_data_path(), 'cache')

    existe = filetools.exists(path)
    if existe: presentar = True
    if presentar:
        itemlist.append(item.clone( action='', title='Carpeta Caché:', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_folder_cache', title= " - Eliminar", thumbnail=config.get_thumb('computer'), text_color='red' ))

    presentar = False

    downloadpath = config.get_setting('downloadpath', default='')

    if downloadpath: path = downloadpath
    else: path = filetools.join(config.get_data_path(), 'downloads')

    existe = filetools.exists(path)
    if existe: presentar = True
    if presentar:
        itemlist.append(item.clone( action='', title='Contenido Descargas:', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_folder_downloads', title= " - Eliminar", thumbnail=config.get_thumb('computer'), text_color='red' ))

    presentar = False

    path = filetools.join(config.get_data_path(), 'tracking_dbs')

    existe = filetools.exists(path)
    if existe: presentar = True
    if presentar:
        itemlist.append(item.clone( action='', title='Contenido Preferidos:', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_tracking_dbs', title= " - Eliminar", thumbnail=config.get_thumb('computer'), text_color='red' ))

    presentar = False

    path = filetools.join(config.get_data_path(), 'tmdb.sqlite-journal')

    existe = filetools.exists(path)
    if existe: presentar = True
    if presentar:
        itemlist.append(item.clone( action='', title='Archivo Tmdb Sqlite Journal:', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_tmdb_sqlite', title= " - Eliminar", journal = 'journal', thumbnail=config.get_thumb('computer'), text_color='red' ))

    presentar = False

    path = filetools.join(config.get_data_path(), 'tmdb.sqlite')

    existe = filetools.exists(path)
    if existe: presentar = True
    if presentar:
        itemlist.append(item.clone( action='', title='Archivo Tmdb Sqlite:', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_tmdb_sqlite', title= " - Eliminar", thumbnail=config.get_thumb('computer'), text_color='red' ))

    presentar = False

    path = config.get_data_path()

    existe = filetools.exists(path)
    if existe: presentar = True
    if presentar:
        itemlist.append(item.clone( action='', title='Ajustes Configuración:', thumbnail=config.get_thumb('tools'), text_color='violet' ))

        itemlist.append(item.clone( channel='actions', action='manto_folder_addon', title= " - Eliminar", thumbnail=config.get_thumb('computer'), text_color='red' ))

    return itemlist


def submnu_logs(item):
    logger.info()
    itemlist = []

    presentar = False

    if os.path.exists(os.path.join(config.get_data_path(), 'servers_todo.log')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'qualities_todo.log')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'proxies.log')): presentar = True

    if presentar:
        itemlist.append(item.clone( action='', title='[B]LOGS[/B]', thumbnail=config.get_thumb('tools'), text_color='limegreen' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'servers_todo.log')):
            itemlist.append(item.clone( action='', title='Log de Servidores:', thumbnail=config.get_thumb('tools'), text_color='limegreen' ))

            itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - Ver', todo = 'servers_todo.log', thumbnail=config.get_thumb('crossroads'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'qualities_todo.log')):
            itemlist.append(item.clone( action='', title='Log de Calidades:', thumbnail=config.get_thumb('tools'), text_color='limegreen' ))

            itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - Ver', todo = 'qualities_todo.log', thumbnail=config.get_thumb('quote', text_color='yellow') ))

        if os.path.exists(os.path.join(config.get_data_path(), 'proxies.log')):
            itemlist.append(item.clone( action='', title='Log de Proxies:', thumbnail=config.get_thumb('tools'), text_color='limegreen' ))

            itemlist.append(item.clone( channel='helper', action='show_todo_log', title=' - Ver', todo = 'proxies.log', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        itemlist.append(item.clone( channel='actions', action='manto_temporales', title='Eliminar', _logs = True, thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    return itemlist


def submnu_temporales(item):
    logger.info()
    itemlist = []

    presentar = False

    if os.path.exists(os.path.join(config.get_data_path(), 'info_channels.csv')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'temp.torrent')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'm3u8hls.m3u8')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'test_logs')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'temp_updates.zip')): presentar = True
    elif os.path.exists(os.path.join(config.get_data_path(), 'tempfile_mkdtemp')): presentar = True

    if presentar:
        itemlist.append(item.clone( action='', title='[B]TEMPORALES[/B]', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'info_channels.csv')):
            itemlist.append(item.clone( action='', title='Ficheros Info Channels:', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay Info channels', thumbnail=config.get_thumb('dev'), text_color='goldenrod' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'temp.torrent')):
            itemlist.append(item.clone( action='', title='Fichero Torrent:', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay Torrent', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'm3u8hls.m3u8')):
            itemlist.append(item.clone( action='', title='Fichero M3u8hls:', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay M3u8hls M3u8', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'test_logs')):
            itemlist.append(item.clone( action='', title='Ficheros Test logs:', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay Test logs', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'temp_updates.zip')):
            itemlist.append(item.clone( action='', title='Fichero Updates Zip:', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay Updates Zip', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        if os.path.exists(os.path.join(config.get_data_path(), 'tempfile_mkdtemp')):
            itemlist.append(item.clone( action='', title='Ficheros Mkdtemp:', thumbnail=config.get_thumb('tools'), text_color='cyan' ))

            itemlist.append(item.clone( action='', title=' - Hay Mkdtemp', thumbnail=config.get_thumb('dev'), text_color='yellow' ))

        itemlist.append(item.clone( channel='actions', action='manto_temporales', title='Eliminar', thumbnail=config.get_thumb('keyboard'), text_color='red' ))

    return itemlist


def submnu_gestionar(item):
    logger.info()
    itemlist = []

    presentar = False

    if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developerdeveloper.py')): presentar = True
    elif os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')): presentar = True
    elif os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')): presentar = True

    if presentar:
        itemlist.append(item.clone( action='', title='[B]GESTIONAR[/B]', thumbnail=config.get_thumb('tools'), text_color='teal' ))

        if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developergenres.py')):
            itemlist.append(item.clone( channel='developergenres', action='mainlist', title=' - Géneros', thumbnail=config.get_thumb('genres') ))

        if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertest.py')):
            itemlist.append(item.clone( channel='developertest', action='mainlist', title=' - Canales y Servidores', thumbnail=config.get_thumb('tools') ))

        if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developertools.py')):
            if os.path.exists(os.path.join(config.get_data_path(), 'developer.sqlite')):
                itemlist.append(item.clone( channel='developertools', action='mainlist', title=' - Queries Canales y Servidores', thumbnail=config.get_thumb('tools') ))

    return itemlist


def submnu_canales(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]TESTS CANALES[/B]', thumbnail=config.get_thumb('tools'), text_color='gold' ))

    itemlist.append(item.clone( channel='actions', action='show_latest_domains', title=' - [COLOR cyan][B]Últimos Cambios dominios[/B][/COLOR]', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='test_all_webs', title=' - Insatisfactorios', thumbnail=config.get_thumb('stack'), unsatisfactory = True ))
    itemlist.append(item.clone( action='test_all_webs', title=' - Todos', thumbnail=config.get_thumb('stack') ))

    itemlist.append(item.clone( action='test_one_channel', title=' - Un canal concreto', thumbnail=config.get_thumb('stack') ))

    return itemlist


def submnu_servidores(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='', title='[B]TESTS SERVIDORES[/B]', thumbnail=config.get_thumb('tools'), text_color='fuchsia' ))
    itemlist.append(item.clone( action='test_all_srvs', title=' - Insatisfactorios', thumbnail=config.get_thumb('flame'), unsatisfactory = True ))
    itemlist.append(item.clone( action='test_all_srvs', title=' - Todos', thumbnail=config.get_thumb('flame') ))

    itemlist.append(item.clone( action='test_one_server', title=' - Un servidor concreto', thumbnail=config.get_thumb('flame') ))

    return itemlist


def test_all_webs(item):
    logger.info()

    config.set_setting('developer_test_channels', '')

    config.set_setting('user_test_channel', '')

    if item.unsatisfactory: text = '¿ Iniciar Test Web de los Posibles Canales Insatisfactorios ?'
    else: text = '¿ Iniciar Test Web de Todos los Canales ?'

    if not platformtools.dialog_yesno(config.__addon_name, text):
        return

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
        i += 1

        try:
            txt = tester.test_channel(ch['name'])
        except:
            if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[B][COLOR red]Error en la comprobación.[/B][/COLOR]', '[COLOR yellowgreen][B]¿ Desea comprobar el Canal de nuevo ?[/B][/COLOR]'):
                txt = tester.test_channel(ch['name'])
            else: continue

        rememorize = False

        if not txt: continue

        if 'code: [COLOR springgreen][B]200' in str(txt):
            if 'Falso Positivo.' in str(txt):
                platformtools.dialog_textviewer(ch['name'], txt)

                if ' con proxies ' in str(txt):
                    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]¿ Desea Iniciar una nueva Búsqueda de Proxies en el Canal ?[/B][/COLOR]'):
                        _proxies(item, ch['id'])
                        txt = tester.test_channel(ch['name'])
	
                        if not 'code: [COLOR springgreen][B]200' in str(txt):
                            if ' con proxies ' in str(txt):
                                platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado Buscando Nuevos Proxies.[/B][/COLOR]')
                        else:
                            rememorize = True

                elif 'Sin proxies' in str(txt):
                    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]Quizás necesite Proxies.[/B][/COLOR] ¿ Desea Iniciar la Búsqueda de Proxies en el Canal ?'):
                        _proxies(item, ch['id'])
                        txt = tester.test_channel(ch['name'])

                        if not 'code: [COLOR springgreen][B]200' in str(txt):
                            if 'Sin proxies' in str(txt):
                                platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado Buscando Nuevos Proxies.[/B][/COLOR]')
                        else:
                            rememorize = True

                if 'Falso Positivo.' in str(txt):
                    if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]¿ Desea comprobar el Canal de nuevo por Falso Positivo ?[/B][/COLOR]'):
                        txt = tester.test_channel(ch['name'])

                        if 'code: [COLOR springgreen][B]200' in str(txt):
                            if 'Falso Positivo.' in str(txt):
                                platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado el Falso Positivo.[/B][/COLOR]')

            if ' al parecer No se necesitan' in str(txt):
                if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]¿ Desea Quitar los Proxies del Canal ?[/B][/COLOR], porqué parece que NO se necesitan.'):
                    _quitar_proxies(item, ch['id'])
                    txt = tester.test_channel(ch['name'])

                    proxies = config.get_setting('proxies', ch['id'], default='').strip()

                    if not proxies:
                        if config.get_setting('memorize_channels_proxies', default=True):
                            el_memorizado = "'" + ch['id'] + "'"

                            if el_memorizado in str(channels_proxies_memorized):
                                channels_proxies_memorized = str(channels_proxies_memorized).replace(el_memorizado + ',', '').replace(el_memorizado, '').strip()
                                config.set_setting('channels_proxies_memorized', channels_proxies_memorized)

        else:
           if 'code: [COLOR [COLOR orangered][B]301' in str(txt) or 'code: [COLOR [COLOR orangered][B]308' in str(txt): continue

           if 'code: [COLOR [COLOR orangered][B]302' in str(txt) or 'code: [COLOR [COLOR orangered][B]307' in str(txt): continue

           if 'Podría estar Correcto' in str(txt): continue

           if ' con proxies ' in str(txt):
               if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]¿ Desea Iniciar una nueva Búsqueda de Proxies en el Canal ?[/B][/COLOR]'):
                   _proxies(item, ch['id'])
                   txt = tester.test_channel(ch['name'])
	
                   if not 'code: [COLOR springgreen][B]200' in str(txt):
                       if ' con proxies ' in str(txt):
                           platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado Buscando Nuevos Proxies.[/B][/COLOR]')
                   else:
                       rememorize = True

           elif 'Sin proxies' in str(txt):
               if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]Quizás necesite Proxies.[/B][/COLOR] ¿ Desea Iniciar la Búsqueda de Proxies en el Canal ?'):
                   _proxies(item, ch['id'])
                   txt = tester.test_channel(ch['name'])

                   if not 'code: [COLOR springgreen][B]200' in str(txt):
                       if 'Sin proxies' in str(txt):
                           platformtools.dialog_ok(config.__addon_name + ' [COLOR yellow][B]' + ch['name'] + '[/B][/COLOR]', '[COLOR red][B]No se ha solucionado Buscando Nuevos Proxies.[/B][/COLOR]')
                   else:
                       rememorize = True

        if rememorize:
            proxies = config.get_setting('proxies', ch['id'], default='').strip()

            if proxies:
                if config.get_setting('memorize_channels_proxies', default=True):
                    channels_proxies_memorized = config.get_setting('channels_proxies_memorized', default='')

                    el_memorizado = "'" + ch['id'] + "'"

                    if not el_memorizado in str(channels_proxies_memorized):
                        channels_proxies_memorized = channels_proxies_memorized + ', ' + el_memorizado
                        config.set_setting('channels_proxies_memorized', channels_proxies_memorized)

    if i > 0: platformtools.dialog_ok(config.__addon_name, 'Canales Testeados ' + str(i))

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

    if item.unsatisfactory: text = '¿ Iniciar Test Web de los Posibles Servidores Insatisfactorios ?'
    else: text = '¿ Iniciar Test Web de Todos los Servidores ?'

    if not platformtools.dialog_yesno(config.__addon_name, text):
        return

    if item.unsatisfactory: config.set_setting('developer_test_servers', 'unsatisfactory')

    from core import jsontools

    from modules import tester

    path = os.path.join(config.get_runtime_path(), 'servers')

    servidores = os.listdir(path)

    i = 0

    for server in servidores:
        if not server.endswith('.json'): continue

        path_server = os.path.join(config.get_runtime_path(), 'servers', server)

        if not os.path.isfile(path_server): continue

        data = filetools.read(path_server)
        dict_server = jsontools.load(data)

        if dict_server['active'] == False: continue

        i += 1

        txt = ''

        try:
            txt = tester.test_server(dict_server['name'])
        except:
            if platformtools.dialog_yesno(config.__addon_name + ' [COLOR yellow][B]' + dict_server['name'] + '[/B][/COLOR]', '[B][COLOR red]Error en la comprobación.[/B][/COLOR]', '[COLOR yellowgreen][B]¿ Desea comprobar el Servidor de nuevo ?[/B][/COLOR]'):
                txt = tester.test_server(dict_server['name'])
            else: continue

        if not txt: continue

    if i > 0: platformtools.dialog_ok(config.__addon_name, 'Servidores Testeados ' + str(i))

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
        txt += '  ' + str(addons) + '[CR][CR]'

    titulo = 'Información Addons '
    if item.tipo == 'Caché': titulo = 'Información Archivos '

    platformtools.dialog_textviewer(titulo + item.tipo , txt)
