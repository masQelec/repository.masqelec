# -*- coding: utf-8 -*-

import os, xbmc

from platformcode import config, logger, platformtools
from core import httptools, scrapertools, filetools, jsontools

from core.item import Item

from modules import tester


color_alert = config.get_setting('notification_alert_color', default='red')
color_infor = config.get_setting('notification_infor_color', default='pink')
color_adver = config.get_setting('notification_adver_color', default='violet')
color_avis = config.get_setting('notification_avis_color', default='yellow')
color_exec = config.get_setting('notification_exec_color', default='cyan')


def manto_domain_animeflv(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando AnimeFlv[/B][/COLOR]' % color_exec)

    channel_json = 'animeflv.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] AnimeFlv') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_animeflv(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('AnimeFlv')


def manto_domain_cinecalidad(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando CineCalidad[/B][/COLOR]' % color_exec)

    channel_json = 'cinecalidad.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] CineCalidad') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_cinecalidad(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('CineCalidad')


def manto_domain_cinecalidadla(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando CineCalidadLa[/B][/COLOR]' % color_exec)

    channel_json = 'cinecalidadla.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] CineCalidadLa') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_cinecalidadla(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('CineCalidadLa')


def manto_domain_cinecalidadlol(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando CineCalidadLol[/B][/COLOR]' % color_exec)

    channel_json = 'cinecalidadlol.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] CineCalidadLol') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_cinecalidadlol(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('CineCalidadLol')


def manto_domain_cinetux(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando CineTux[/B][/COLOR]' % color_exec)

    channel_json = 'cinetux.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] CineTux') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_cinetux(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('CineTux')


def manto_domain_cuevana3(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando Cuevana3[/B][/COLOR]' % color_exec)

    channel_json = 'cuevana3.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] Cuevana3') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_cuevana3(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('Cuevana3')


def manto_domain_cuevana3video(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando Cuevana3Video[/B][/COLOR]' % color_exec)

    channel_json = 'cuevana3video.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] Cuevana3Video') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_cuevana3video(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('Cuevana3Video')


def manto_domain_divxtotal(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando DivxTotal[/B][/COLOR]' % color_exec)

    channel_json = 'divxtotal.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] DivxTotal') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_divxtotal(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('DivxTotal')


def last_domain_dontorrents(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando dominio[/B][/COLOR]' % color_exec)

    channel_json = 'dontorrents.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] DonTorrents') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    last_domain = ''

    try:
       data = httptools.downloadpage('https://t.me/s/DonTorrent').data

       dominios = scrapertools.find_multiple_matches(data, '>Dominio Oficial.*?<a href="(.*?)"')

       if dominios:
           for dominio in dominios:
               last_domain = dominio
    except:
       pass

    if not last_domain:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No se pudo comprobar[/B][/COLOR]' % color_alert)

        xbmc.sleep(1000)
        platformtools.dialog_ok(config.__addon_name + ' - DonTorrents', '[COLOR yellow]Para conocer el último dominio vigente deberá acceder a través de un navegador web a:', '[COLOR cyan][B]https://t.me/s/DonTorrent[/B][/COLOR]')
        return

    domain = config.get_setting('dominio', 'dontorrents', default='')

    if domain == last_domain:
        platformtools.dialog_ok(config.__addon_name + ' - DonTorrents', '[COLOR yellow]El último dominio vigente es correcto.', '[COLOR cyan][B]' + last_domain + '[/B][/COLOR]')
        return

    nom_dom = domain
    txt_dom = 'Último Dominio memorizado incorrecto.'
    if not domain:
        nom_dom = 'Sin información'
        txt_dom = 'Aún No hay ningún Dominio memorizado.'

    if platformtools.dialog_yesno(config.__addon_name + ' - DonTorrents', '¿ [COLOR red] ' + txt_dom + ' [/COLOR] Desea cambiarlo  ?','Memorizado:  [COLOR yellow][B]' + nom_dom + '[/B][/COLOR]', 'Vigente:           [COLOR cyan][B]' + last_domain + '[/B][/COLOR]'): 
        config.set_setting('dominio', last_domain, 'dontorrents')

        if not item.desde_el_canal:
            if not item.from_action == 'mainlist':
                platformtools.dialog_ok(config.__addon_name + ' - DonTorrents', '[COLOR yellow]Dominio memorizado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar la configuración/ajustes de Balandro a través de su correspondiente botón --> OK[/B][/COLOR]')


def manto_domain_dontorrents(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando DonTorrents[/B][/COLOR]' % color_exec)

    channel_json = 'dontorrents.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] DonTorrents') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    domain = config.get_setting('dominio', 'dontorrents', default='')

    if not domain: domain = 'https://dontorrent.'

    new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio DonTorrents  -->  [COLOR %s]https://dontorrent.???/[/COLOR]' % color_avis)

    if new_domain is None: return
    elif new_domain == 'https://dontorrent.': return

    if not new_domain:
        if domain:
            if platformtools.dialog_yesno(config.__addon_name + ' - DonTorrents', '¿ [COLOR red] Confirma eliminar el dominio Memorizado ?[/COLOR]', '[COLOR cyan][B] ' + domain + ' [/B][/COLOR]'): 
                config.set_setting('dominio', new_domain, 'dontorrents')

                if item.desde_el_canal:
                    platformtools.dialog_ok(config.__addon_name + ' - DonTorrents', '[COLOR yellow]Dominio eliminado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar el Canal e Ingresar de nuevo en él.[/B][/COLOR]')
                else:
                    if not item.from_action == 'mainlist':
                        platformtools.dialog_ok(config.__addon_name + ' - DonTorrents', '[COLOR yellow]Dominio eliminado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar la configuración/ajustes de Balandro a través de su correspondiente botón --> OK[/B][/COLOR]')
        return

    if new_domain:
        if not new_domain.startswith('https://'): new_domain = 'https://' + new_domain
        if not new_domain.endswith('/'): new_domain = new_domain + '/'

        if platformtools.dialog_yesno(config.__addon_name + ' - DonTorrents', '¿ [COLOR yellow] Confirma el dominio informado ?[/COLOR]', '[COLOR cyan][B] ' + new_domain + ' [/B][/COLOR]'): 
            config.set_setting('dominio', new_domain, 'dontorrents')

            if item.desde_el_canal:
                platformtools.dialog_ok(config.__addon_name + ' - DonTorrents', '[COLOR yellow]Dominio memorizado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar el Canal e Ingresar de nuevo en él.[/B][/COLOR]')
            else:
                if not item.from_action == 'mainlist':
                    platformtools.dialog_ok(config.__addon_name + ' - DonTorrents', '[COLOR yellow]Dominio memorizado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar la configuración/ajustes de Balandro a través de su correspondiente botón --> OK[/B][/COLOR]')

    return


def test_domain_dontorrents(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('DonTorrents')


def manto_domain_elifilms(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando EliFilms[/B][/COLOR]' % color_exec)

    channel_json = 'elifilms.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] EliFilms') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_elifilms(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('EliFilms')


def manto_domain_elitetorrent(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando EliteTorrent[/B][/COLOR]' % color_exec)

    channel_json = 'elitetorrent.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] EliteTorrent') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_elitetorrent(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('EliteTorrent')


def manto_domain_entrepeliculasyseries(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando EntrePeliculasySeries[/B][/COLOR]' % color_exec)

    channel_json = 'entrepeliculasyseries.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] EntrePeliculasySeries') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_entrepeliculasyseries(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('EntrePeliculasySeries')


def manto_domain_grantorrent(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando GranTorrent[/B][/COLOR]' % color_exec)

    channel_json = 'grantorrent.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] GranTorrent') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_grantorrent(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('GranTorrent')


def manto_domain_grantorrents(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando GranTorrents[/B][/COLOR]' % color_exec)

    channel_json = 'grantorrents.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] GranTorrents') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_grantorrents(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('GranTorrents')


def latest_domains_hdfull(item):
    logger.info()

    # ~ web para conocer el ultimo dominio vigente en actions
    # ~ web  'https://dominioshdfull.com/'

    last_domain = ''

    try:
       host_domain = 'https://dominioshdfull.com/'

       data = httptools.downloadpage(host_domain).data

       latest_domain = scrapertools.find_single_match(data, 'onclick="location.href.*?' + "'(.*?)'")

       if latest_domain:
           latest_domain = latest_domain.replace('login', '')
           if not latest_domain.endswith('/'): latest_domain = latest_domain + '/'
    except:
       latest_domain = ''

    if latest_domain: last_domain = latest_domain

    if not last_domain:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No se pudo comprobar[/B][/COLOR]' % color_alert)

        xbmc.sleep(1000)
        platformtools.dialog_ok(config.__addon_name + ' - HdFull', '[COLOR yellow]Para conocer el último dominio vigente deberá acceder a través de un navegador web a:', '[COLOR cyan][B]https://twitter.com/hdfulloficial[/B][/COLOR]')
        return

    platformtools.dialog_ok(config.__addon_name + ' - HdFull', '[COLOR yellow]El último dominio es ', '[COLOR cyan][B]' + last_domain + '[/B][/COLOR]')


def last_domain_hdfull(item):
    logger.info()

    domain = config.get_setting('dominio', 'hdfull', default='')

    if domain:
        if domain == 'https://new.hdfull.one/':
            platformtools.dialog_notification(config.__addon_name, '[B]HdFull [COLOR %s]Dominio especial correcto[/B][/COLOR]' % color_infor)
            return

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando dominio[/B][/COLOR]' % color_exec)

    channel_json = 'hdfull.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] HdFull') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return


    # ~ webs para comprobar dominio vigente en actions pero pueden requerir proxies
    # ~ webs  1)-'https://dominioshdfull.com/'  2)-'https://hdfull.vip/'  3)-'https://new.hdfull.one/'


    last_domain = ''

    if domain:
        try:
           host_domain = 'https://dominioshdfull.com/'

           data = httptools.downloadpage(host_domain).data

           latest_domain = scrapertools.find_single_match(data, 'onclick="location.href.*?' + "'(.*?)'")

           if latest_domain:
               latest_domain = latest_domain.replace('login', '')
               if not latest_domain.endswith('/'): latest_domain = latest_domain + '/'
        except:
           latest_domain = ''

        if latest_domain:
            if latest_domain == domain: last_domain = latest_domain


    if not last_domain:
        try:
           host_domain = 'https://dominioshdfull.com/'

           data = httptools.downloadpage(host_domain).data

           last_domain = scrapertools.find_single_match(data, 'onclick="location.href.*?' + "'(.*?)'")

           if last_domain:
               last_domain = last_domain.replace('login', '')
               if not last_domain.endswith('/'): last_domain = last_domain + '/'
        except:
           last_domain = ''


    if not last_domain:
        try:
           host_domain = 'https://hdfull.vip/'

           try:
              last_domain = httptools.downloadpage(host_domain, follow_redirects=False).headers.get('location', '')
           except:
              last_domain = ''

           if not last_domain:
               if config.get_setting('channel_hdfull_proxies', default=''):
                   try:
                      last_domain = httptools.downloadpage_proxy('hdfull', host_domain, follow_redirects=False).headers.get('location', '')
                   except:
                      last_domain = ''

           if last_domain:
               last_domain = last_domain.replace('login', '')
               if not last_domain.endswith('/'): last_domain = last_domain + '/'
        except:
           last_domain = ''


    if not last_domain:
        try:
           host_domain = 'https://new.hdfull.one/login'

           if item.desde_el_canal:
               if item.dominios_ret: host_domain = item.dominios_ret + 'login'

           data = httptools.downloadpage(host_domain).data

           last_domain = scrapertools.find_single_match(data, 'location.replace.*?"(.*?)"')
           if not last_domain: last_domain = scrapertools.find_single_match(data, '<link rel="canonical".*?href="(.*?)"')

           if not last_domain:
               if config.get_setting('channel_hdfull_proxies', default=''):
                   data = httptools.downloadpage_proxy('hdfull', host_domain).data
                   last_domain = scrapertools.find_single_match(data, 'location.replace.*?"(.*?)"')
                   if not last_domain: last_domain = scrapertools.find_single_match(data, '<link rel="canonical".*?href="(.*?)"')

           if last_domain:
               last_domain = last_domain.replace('login', '')
               if not last_domain.endswith('/'): last_domain = last_domain + '/'
        except:
           last_domain = ''


    if not last_domain:
        platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]No se pudo comprobar[/B][/COLOR]' % color_alert)

        xbmc.sleep(1000)
        platformtools.dialog_ok(config.__addon_name + ' - HdFull', '[COLOR yellow]Para conocer el último dominio vigente deberá acceder a través de un navegador web a:', '[COLOR cyan][B]https://twitter.com/hdfulloficial[/B][/COLOR]')
        return

    if domain == last_domain:
        platformtools.dialog_ok(config.__addon_name + ' - HdFull', '[COLOR yellow]El último dominio vigente es correcto.', '[COLOR cyan][B]' + last_domain + '[/B][/COLOR]')
        return

    nom_dom = domain
    txt_dom = 'Último Dominio memorizado incorrecto.'
    if not domain:
        nom_dom = 'Sin información'
        txt_dom = 'Aún No hay ningún Dominio memorizado.'

    if platformtools.dialog_yesno(config.__addon_name + ' - HdFull', '¿ [COLOR red] ' + txt_dom + ' [/COLOR] Desea cambiarlo  ?','Memorizado:  [COLOR yellow][B]' + nom_dom + '[/B][/COLOR]', 'Vigente:           [COLOR cyan][B]' + last_domain + '[/B][/COLOR]'): 
        config.set_setting('dominio', last_domain, 'hdfull')

        if not item.desde_el_canal:
            if not item.from_action == 'mainlist':
                platformtools.dialog_ok(config.__addon_name + ' - HdFull', '[COLOR yellow]Último dominio vigente memorizado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar la configuración/ajustes de Balandro a través de su correspondiente botón --> OK[/B][/COLOR]')


def del_datos_hdfull(item):
    logger.info()

    username = config.get_setting('hdfull_username', 'hdfull', default='')
    password = config.get_setting('hdfull_password', 'hdfull', default='')

    if not username or not password:
        return

    if platformtools.dialog_yesno(config.__addon_name, '[COLOR red]¿ Confirma eliminar sus credenciales de HdFull ?[/COLOR]'):
        config.set_setting('channel_hdfull_hdfull_login', False)
        config.set_setting('channel_hdfull_hdfull_password', '')
        config.set_setting('channel_hdfull_hdfull_username', '')


def manto_domain_hdfull(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando HdFull[/B][/COLOR]' % color_exec)

    channel_json = 'hdfull.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] HdFull') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    domain = config.get_setting('dominio', 'hdfull', default='')

    if not domain: domain = 'https://hdfull.'

    new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio HdFull  -->  [COLOR %s]https://hdfull.???/[/COLOR]' % color_avis)

    if new_domain is None: return
    elif new_domain == 'https://hdfull.': return

    if not new_domain:
        if domain:
            if platformtools.dialog_yesno(config.__addon_name + ' - HdFull', '¿ [COLOR red] Confirma eliminar el dominio Memorizado ?[/COLOR]', '[COLOR cyan][B] ' + domain + ' [/B][/COLOR]'): 
                config.set_setting('dominio', new_domain, 'hdfull')

                if item.desde_el_canal:
                    platformtools.dialog_ok(config.__addon_name + ' - HdFull', '[COLOR yellow]Dominio eliminado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar el Canal e Ingresar de nuevo en él.[/B][/COLOR]')
                else:
                    if not item.from_action == 'mainlist':
                        platformtools.dialog_ok(config.__addon_name + ' - HdFull', '[COLOR yellow]Dominio eliminado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar la configuración/ajustes de Balandro a través de su correspondiente botón --> OK[/B][/COLOR]')
        return

    if new_domain:
        if not new_domain.startswith('https://'): new_domain = 'https://' + new_domain
        if not new_domain.endswith('/'): new_domain = new_domain + '/'

        if platformtools.dialog_yesno(config.__addon_name + ' - HdFull', '¿ [COLOR yellow] Confirma el dominio informado ?[/COLOR]', '[COLOR cyan][B] ' + new_domain + ' [/B][/COLOR]'): 
            config.set_setting('dominio', new_domain, 'hdfull')

            if item.desde_el_canal:
                platformtools.dialog_ok(config.__addon_name + ' - HdFull', '[COLOR yellow]Dominio memorizado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar el Canal e Ingresar de nuevo en él.[/B][/COLOR]')
            else:
                if not item.from_action == 'mainlist':
                    platformtools.dialog_ok(config.__addon_name + ' - HdFull', '[COLOR yellow]Dominio memorizado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar la configuración/ajustes de Balandro a través de su correspondiente botón --> OK[/B][/COLOR]')

    return


def test_domain_hdfull(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('HdFull')


def manto_domain_hdfullse(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando HdFullSe[/B][/COLOR]' % color_exec)

    channel_json = 'hdfullse.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] HdFullSe') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_hdfullse(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('HdFullSe')


def manto_domain_kindor(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando Kindor[/B][/COLOR]' % color_exec)

    channel_json = 'kindor.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] Kindor') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_kindor(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('Kindor')


def manto_domain_pelis28(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando Pelis28[/B][/COLOR]' % color_exec)

    channel_json = 'pelis28.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] Pelis28') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_pelis28(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('Pelis28')


def manto_domain_pelisflix(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando PelisFlix[/B][/COLOR]' % color_exec)

    channel_json = 'pelisflix.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] PelisFlix') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_pelisflix(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('PelisFlix')


def manto_domain_pelisplus(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando PelisPlus[/B][/COLOR]' % color_exec)

    channel_json = 'pelisplus.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] PelisPlus') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_pelisplus(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('PelisPlus')


def manto_domain_pelisplushd(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando PelisPlusHd[/B][/COLOR]' % color_exec)

    channel_json = 'pelisplushd.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] PelisPlusHd') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_pelisplushd(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('PelisPlusHd')


def manto_domain_pelisplushdlat(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando PelisPlusHdLat[/B][/COLOR]' % color_exec)

    channel_json = 'pelisplushdlat.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] PelisPlusHdLat') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_pelisplushdlat(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('PelisPlusHdLat')


def del_datos_playdede(item):
    logger.info()

    username = config.get_setting('playdede_username', 'playdede', default='')
    password = config.get_setting('playdede_password', 'playdede', default='')

    if not username or not password:
        return

    if platformtools.dialog_yesno(config.__addon_name, '[COLOR red]¿ Confirma eliminar sus credenciales de PlayDede ?[/COLOR]'):
        config.set_setting('channel_playdede_playdede_login', False)
        config.set_setting('channel_playdede_playdede_password', '')
        config.set_setting('channel_playdede_playdede_username', '')


def manto_domain_playdede(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando Playdede[/B][/COLOR]' % color_exec)

    channel_json = 'playdede.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] Playdede') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_playdede(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('PlayDede')


def manto_domain_repelis24(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando RePelis24[/B][/COLOR]' % color_exec)

    channel_json = 'repelis24.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] RePelis24') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_repelis24(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('RePelis24')


def manto_domain_repelishd(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando RepPlisHd[/B][/COLOR]' % color_exec)

    channel_json = 'repelishd.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] RePelisHd') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_repelishd(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('RePelisHd')


def manto_domain_series24(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando Series24[/B][/COLOR]' % color_exec)

    channel_json = 'series24.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] Series24') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_series24(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('Series24')


def manto_domain_subtorrents(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando SubTorrents[/B][/COLOR]' % color_exec)

    channel_json = 'subtorrents.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] SubTorrents') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_subtorrents(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('SubTorrents')


def manto_domain_torrentdivx(item):
    logger.info()

    platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Comprobando TorrentDivx[/B][/COLOR]' % color_exec)

    channel_json = 'torrentdivx.json'
    filename_json = os.path.join(config.get_runtime_path(), 'channels', channel_json)

    data = filetools.read(filename_json)
    params = jsontools.load(data)

    try:
       data = filetools.read(filename_json)
       params = jsontools.load(data)
    except:
       el_canal = ('Falta [B][COLOR %s]' + channel_json) % color_alert
       platformtools.dialog_notification(config.__addon_name, el_canal + '[/COLOR][/B]')
       return

    if params['active'] == False:
        el_canal = ('[B][COLOR %s] TorrentDivx') % color_avis
        platformtools.dialog_notification(config.__addon_name, el_canal + '[COLOR %s] inactivo [/COLOR][/B]' % color_alert)
        return

    id = params['id']
    name = params['name']

    manto_domain_common(item, id, name)


def test_domain_torrentdivx(item):
    logger.info()

    config.set_setting('developer_test_channels', '')
    tester.test_channel('TorrentDivx')


def manto_domain_common(item, id, name):
    logger.info()

    domain = config.get_setting('dominio', id, default='')

    if id == 'animeflv':
        if not domain: domain = 'https://animeflv.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio AnimeFlv  -->  [COLOR %s]https://animeflv.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://animeflv.': return

    elif id == 'cinecalidad':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio CineCalidad  -->  [COLOR %s]https://??.cinecalidad.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    elif id == 'cinecalidadla':
        if not domain: domain = 'https://cinecalidad.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio CineCalidadLa  -->  [COLOR %s]https://cinecalidad.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://cinecalidad.': return

    elif id == 'cinecalidadlol':
        if not domain: domain = 'https://cinecalidad.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio CineCalidadLol  -->  [COLOR %s]https://cinecalidad.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://cinecalidad.': return

    elif id == 'cinetux':
        if not domain: domain = 'https://cinetux.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio CineTux  -->  [COLOR %s]https://cinetux..??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://cinetux.': return

    elif id == 'cuevana3':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio Cuevana3  -->  [COLOR %s]https://??.cuevana3.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    elif id == 'cuevana3video':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio Cuevana3Video  -->  [COLOR %s]https://???.cuevana3.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    elif id == 'divxtotal':
        if not domain: domain = 'https://www.divxtotal.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio DivxTotal  -->  [COLOR %s]https://www.divxtotal.???/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://www.divxtotal.': return

    elif id == 'elifilms':
        if not domain: domain = 'https://allcalidad.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio EliFilms  -->  [COLOR %s]https://allcalidad..??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://allcalidad.': return

    elif id == 'elitetorrent':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio EliteTorrent  -->  [COLOR %s]https://??.elitetorrent.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    elif id == 'entrepeliculasyseries':
        if not domain: domain = 'https://entrepeliculasyseries.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio EntrePeliculasySeries  -->  [COLOR %s]https://entrepeliculasyseries.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://entrepeliculasyseries.': return

    elif id == 'grantorrent':
        if not domain: domain = 'https://grantorrent.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio GranTorrent  -->  [COLOR %s]https://grantorrent.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://grantorrent.': return

    elif id == 'grantorrents':
        if not domain: domain = 'https://grantorrent.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio GranTorrents  -->  [COLOR %s]https://grantorrent.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://grantorrent.': return

    elif id == 'hdfullse':
        if not domain: domain = 'https://hdfull.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio HdFullSe  -->  [COLOR %s]https://hdfull.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://hdfull.': return

    elif id == 'kindor':
        if not domain: domain = 'https://kindor.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio Kindor  -->  [COLOR %s]https://kindor.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://kindor.': return

    elif id == 'pelis28':
        if not domain: domain = 'https://pelis28.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio Pelis28  -->  [COLOR %s]https://pelis28..??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://pelis28.': return

    elif id == 'pelisflix':
        if not domain: domain = 'https://pelisflix.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio PelisFlix  -->  [COLOR %s]https://pelisflix.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://pelisflix.': return

    elif id == 'pelisplus':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio PelisPlus  -->  [COLOR %s]https://???.pelisplus.???/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    elif id == 'pelisplushd':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio PelisPlusHd  -->  [COLOR %s]https://???.pelisplus.???/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    elif id == 'pelisplushdlat':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio PelisPlusHdLat  -->  [COLOR %s]https://???.pelisplus.???/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    elif id == 'playdede':
        if not domain: domain = 'https://playdede.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio Playdede  -->  [COLOR %s]https://playdede.???/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://playdede.': return

    elif id == 'repelis24':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio RePelis24  -->  [COLOR %s]https://??.repelis24.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    elif id == 'repelishd':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio RePelisHd  -->  [COLOR %s]https://??.repelishd.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    elif id == 'series24':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio Series24  -->  [COLOR %s]https://??.series24.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    elif id == 'subtorrents':
        if not domain: domain = 'https://www.subtorrents.'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio SubTorrents  -->  [COLOR %s]https://www.subtorrents.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://www.subtorrents.': return

    elif id == 'torrentdivx':
        if not domain: domain = 'https://'

        new_domain = platformtools.dialog_input(default=domain, heading='Indicar dominio TorrentDivx  -->  [COLOR %s]https://??.ditorrent.??/[/COLOR]' % color_avis)

        if new_domain is None: return
        elif new_domain == 'https://': return

    else:
        return

    if not new_domain:
        if domain:
            if platformtools.dialog_yesno(config.__addon_name + ' - ' + name, '¿ [COLOR red] Confirma eliminar el dominio Memorizado ?[/COLOR]', '[COLOR cyan][B] ' + domain + ' [/B][/COLOR]'): 
                config.set_setting('dominio', new_domain, id)

                if item.desde_el_canal:
                    platformtools.dialog_ok(config.__addon_name + ' - ' + name, '[COLOR yellow]Dominio eliminado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar el Canal e Ingresar de nuevo en él.[/B][/COLOR]')
                else:
                    if not item.from_action == 'mainlist':
                        platformtools.dialog_ok(config.__addon_name + ' - ' + name, '[COLOR yellow]Dominio memorizado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar la configuración/ajustes de Balandro a través de su correspondiente botón --> OK[/B][/COLOR]')
        return

    if new_domain:
        new_domain = new_domain.lower()

        mistake = False

        if ':' not in new_domain: mistake = True
        elif '//' not in new_domain: mistake = True
        elif '.' not in new_domain: mistake = True

        if mistake:
            platformtools.dialog_notification(config.__addon_name, '[B][COLOR %s]Dominio incorrecto[/B][/COLOR]' % color_adver)
            return

        if new_domain.startswith('http:'): new_domain = new_domain.replace('http:', 'https:')
        elif new_domain.startswith('//'): new_domain = 'https:' + new_domain

        if not new_domain.startswith('https://'): new_domain = 'https://' + new_domain
        if not new_domain.endswith('/'): new_domain = new_domain + '/'

        if platformtools.dialog_yesno(config.__addon_name + ' - ' + name, '¿ [COLOR yellow] Confirma el dominio informado ?[/COLOR]', '[COLOR cyan][B] ' + new_domain + ' [/B][/COLOR]'): 
            config.set_setting('dominio', new_domain, id)

            if item.desde_el_canal:
                platformtools.dialog_ok(config.__addon_name + ' - ' + name, '[COLOR yellow]Dominio memorizado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar el Canal e Ingresar de nuevo en él.[/B][/COLOR]')
            else:
                if not item.from_action == 'mainlist':
                    platformtools.dialog_ok(config.__addon_name + ' - ' + name, '[COLOR yellow]Dominio memorizado, pero aún NO guardado.[/COLOR]', '[COLOR cyan][B]Recuerde, que para que el cambio surta efecto deberá abandonar la configuración/ajustes de Balandro a través de su correspondiente botón --> OK[/B][/COLOR]')

    return
