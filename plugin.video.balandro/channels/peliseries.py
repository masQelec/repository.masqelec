# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://peliseries.live'

opts_url =  host + '/?v=Opciones'

perpage = 24


def do_downloadpage(url, post=None, headers=None):
    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + '/Peliculas.html?page=1', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + '/Estrenos.html?page=1', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Recientes', action = 'list_all', url = host + '/Seccion.html?ver=UAgregados', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + '/Seccion.html?ver=PelisMasVistos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Marvel', action = 'list_all', url = host + '/Buscar.html?s=Marvel', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'DC', action = 'list_all', url = host + '/Buscar.html?s=DC', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + '/Series.html?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + '/Estrenos.html?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Recientes', action = 'list_all', url = host + '/Seccion.html?ver=UAgregados', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Actualizadas', action = 'list_all', url = host + '/Seccion.html?ver=UActualizados', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Novelas', action = 'list_all', url = host + '/Novelas.html?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Anime', action = 'list_all', url = host + '/Anime.html?page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Más vistas', action = 'list_all', url = host + '/Seccion.html?ver=MasVistos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    opciones = [
        ('Accion', 'Acción'), 
        ('Animacion', 'Animación'), 
        ('Aventura', 'Aventura'),
        ('Belica', 'Belica'),
        ('Ciencia+ficcion', 'Ciencia ficción'),
        ('Comedia', 'Comedia'), 
        ('Crimen', 'Crimen'),
        ('Documental', 'Documental'), 
        ('Drama', 'Drama'),
        ('Familia', 'Familiar'), 
        ('Fantasia', 'Fantasía'),
        ('Guerra', 'Guerra'),
        ('Historia', 'Historia'), 
        ('Kids', 'Infantil'),
        ('Misterio', 'Misterio'),
        ('Musical', 'Musical'),
        ('Reality', 'Reality'),
        ('Romance', 'Romance'),
        ('Suspense', 'Suspense'),
        ('Terror', 'Terror'),
        ('Western', 'Western')
        ]

    if item.search_type == 'movie': 
        opciones.remove(('Kids','Infantil'))
        opciones.remove(('Reality','Reality'))

    elif item.search_type == 'tvshow': 
        opciones.remove(('Suspense','Suspense'))

    for opc, tit in opciones:
        url = host + '/Buscar.html?gen=' + opc

        itemlist.append(item.clone( title = tit, url = url, action = 'list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<div class="list-item(.*?)</a></div>')

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        url = scrapertools.find_single_match(match, ' href="(.*?)"')
        title = scrapertools.find_single_match(match, '<div class="post_title">(.*?)</div>')

        if not url or not title: continue

        tipo = 'tvshow' if '<b>Serie</b>' in match else 'movie'
        if tipo == 'movie':
            if '<b>Anime</b>' in match: tipo = 'tvshow'
            elif '<b>Novela</b>' in match: tipo = 'tvshow'

        sufijo = '' if item.search_type != 'all' else tipo

        url = host + url

        thumb = scrapertools.find_single_match(match, 'img="(.*?)"')

        if '<b>Serie</b>' in match or '<b>Anime</b>' in match or '<b>Novela</b>' in match:
            lngs = scrapertools.find_single_match(match,'<div class="post_info">.*?<br/>.*?<b>(.*?)</b>')
        else:
            lngs = scrapertools.find_single_match(match,'<div class="post_info">.*?<b>(.*?)</b>')

        langs = []
        if 'Esp' in lngs: langs.append('Esp')
        if 'Lat' in lngs: langs.append('Lat')
        if 'Sub' in lngs: langs.append('Vose')
        if 'Ing' in lngs: langs.append('VO')

        year = scrapertools.find_single_match(match,'<div class="post_info">.*?Estreno: (\d{4})-')
        if not year:
            year = '-'

        if tipo == 'tvshow':
            if item.search_type != 'all':
                 if item.search_type == 'movie': continue

            tv_tipo = ''
            if '<b>Serie</b>' in match: tv_tipo = 'Serie'
            elif '<b>Anime</b>' in match: tv_tipo = 'Anime'
            elif '<b>Novela</b>' in match: tv_tipo = 'Novela'

            itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb, tv_tipo = tv_tipo, languages = ', '.join(langs),
                                        fmt_sufijo=sufijo, contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': year} ))

        else:
            if item.search_type != 'all':
                 if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, languages = ', '.join(langs),
                                        fmt_sufijo=sufijo, contentType = 'movie', contentTitle = title, infoLabels = {'year': year} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if not '/Buscar.html' in item.url:
        buscar_next = True
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1, action='list_all', text_color='coral' ))
                buscar_next = False

        if buscar_next:
            if itemlist:
                next_page = scrapertools.find_single_match(data, "<li class='num active'>.*?<li class='num'>.*?<a href='(.*?)'")
                if next_page:
                    if '/Seccion.html' in item.url:
                       next_page = host + '/Seccion.html' + next_page
                    else:
                       next_page = host + next_page

                    itemlist.append(item.clone (url = next_page, page = 0, title = '>> Página siguiente', action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    if not item.tv_tipo:
        return itemlist

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    pid = scrapertools.find_single_match(data, "'pid':(.*?)}")

    if not pid:
        return itemlist

    post = 'pid=%s&tipo=%s&temp=-1&cap=-1' % (str(pid), str(item.tv_tipo))

    data = do_downloadpage(opts_url, post = post)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    temporadas = re.compile("Temporada (.*?)</a>", re.DOTALL).findall(data)

    for tempo in temporadas:
        tempo = tempo.strip()
        title = 'Temporada ' + tempo

        if len(temporadas) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.page = 0
            item.pid = pid
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, pid = pid, contentType = 'season', contentSeason = tempo, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    perpage = 50

    post = 'pid=%s&tipo=Serie&temp=%s&cap=-1' %(str(item.pid), str(item.contentSeason))

    data = do_downloadpage(opts_url, post = post)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = re.compile(' temp">.*?href="(.*?)".*?xhref=".*?cap=(.*?)".*?class="btn btn-large">(.*?)</a>', re.DOTALL).findall(data)

    for url, epis, title in matches[item.page * perpage:]:
        url = host + url

        title = title.strip()
        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + title

        itemlist.append(item.clone( action='findvideos', url = url, title = titulo,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= perpage:
            break

    if len(matches) > ((item.page + 1) * perpage):
        itemlist.append(item.clone( title=">> Página siguiente", action="episodios", page=item.page + 1, text_color='coral' ))

    return itemlist


def puntuar_calidad(txt):
    orden = ['cam', '360p', '480p', 'RHDTV', 'HD', '720p', '1080p']
    txt = txt.replace('HD', '').replace('CAM', '').replace('S', '').strip()
    if txt not in orden: return 0
    else: return orden.index(txt) + 1


def findvideos(item):
    logger.info()
    itemlist = []

    if not item.pid:
        data = do_downloadpage(item.url)

        pid = scrapertools.find_single_match(data, "'pid':(.*?)}")

        if not pid:
            return itemlist

        post = 'pid=%s&tipo=Pelicula&temp=-1&cap=-1' % str(pid)
    else:
        post = 'pid=%s&tipo=Serie&temp=%s&cap=%s' %(str(item.pid), str(item.contentSeason), str(item.contentEpisodeNumber))

    data = do_downloadpage(opts_url, post = post)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, 'onclick="OpenPlayer(.*?)</a></div>')

    ses = 0

    for match in matches:
        ses += 1

        match = match + '</i>'

        code = scrapertools.find_single_match(match, 'code="(.*?)"')
        pid = scrapertools.find_single_match(match, 'pid="(.*?)"')
        lid = scrapertools.find_single_match(match, 'lid="(.*?)"')
        hst = scrapertools.find_single_match(match, 'hst="(.*?)"')
        pos = scrapertools.find_single_match(match, "pos='(.*?)'")

        lang = scrapertools.find_single_match(match, "</i>(.*?)</i>").lower()
        lang = lang.strip()

        if 'latino' in lang:
            lang = 'Lat'
        elif 'castellano' in lang or 'español' in lang:
            lang = 'Esp'
        elif 'subtitulado' in lang or 'sub' in lang:
            lang = 'Vose'
        elif 'ing.' in lang or 'ingles' in lang:
            lang = 'VO'
        else:
            lang = 'Esp'

        qlty =  scrapertools.find_single_match(match, "</i>.*? (.*?)</i>")
        qlty = qlty.strip()

        if 'play_' in match:
            play_down = '(P)'
            url = '%s/?v=Player3&pid=%s&lid=%s&h=%s&pos=%s&u=%s' % (host, pid, lid, hst, pos, code)

            if 'clicknupload' in hst:
                url += '&port=80'
            elif 'myurlshort' in hst:
                url = '%s/?v=Player&pid=%s&lid=%s&h=%s&pos=%s&u=%s' % (host, pid, lid, hst, pos, code)

        elif '_download' in match:
            play_down = '(D)'
            url = 'pid=%s&lid=%s&hst=%s&code=%s' % (pid, lid, hst, code)
        else:
            play_down = '(O)'
            url = '%s/?v=Player&pid=%s&lid=%s&h=%s&pos=%s&u=%s' % (host, pid, lid, hst, pos, code)

        if hst:
            hst = hst.lower()

            if 'hqq.' in hst or 'waaw.' in hst or 'netu.' in hst: continue
            elif 'youtube' in hst: continue

            elif 'openload' in hst: continue
            elif 'powvideo' in hst: continue
            elif 'streamplay' in hst: continue
            elif 'rapidvideo' in hst: continue
            elif 'streamango' in hst: continue
            elif 'verystream' in hst: continue
            elif 'vidtodo' in hst: continue

            elif 'cuevana3' in hst: continue
            elif 'repelis24' in hst: continue
            elif 'flixplayer' in hst: continue
            elif 'vidcloud' in hst: continue
            elif 'mystream' in hst: continue
            elif 'stormo' in hst: continue
            elif 'moovies' in hst: continue
            elif '1fichier' in hst: continue
            elif 'mediafire' in hst: continue
            elif 'pandafiles' in hst: continue
            elif 'myfiles' in hst: continue
            elif 'dropapk' in hst: continue
            elif 'nitroflare' in hst: continue
            elif 'owndrives' in hst: continue
            elif 'primeuploads' in hst: continue

            other = hst
            other = other.replace('www.', '').replace('www', '')
            other = other.replace('.com', '').replace('.net', '').replace('.live', '').replace('api.', '').replace('.io', '').replace('.me', '').replace('.am', '')
            other = other.replace('.co', '').replace('.tv', '').replace('.ru', '').replace('.to', '').replace('.cc', '').replace('.nz', '').replace('.xyz', '')
            other = other.replace('.site', '').replace('.pelisplay', '').replace('.google', '').replace('player.', '').replace('play.', '').replace('.playerd', '')
            other = other.strip()

            other = other.capitalize() + ' ' + play_down

            itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', url = url, other = other,
                                  language = lang, quality = qlty, quality_num = puntuar_calidad(qlty) ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = ''

    if '(P)' in item.other:
        data = do_downloadpage(item.url)
        url = scrapertools.find_single_match(data, "<iframe src='(.*?)'")

        if not url:
            url = scrapertools.find_single_match(data, "<IFRAME SRC='(.*?)'")

        if not url:
            url = scrapertools.find_single_match(data, '<iframe id="myframe" data-src="(.*?)"')

        if not url:
            url = scrapertools.find_single_match(data, "var video_url='(.*?)'")

        if not url:
            url = scrapertools.find_single_match(data, 'sources:.*?"src":.*?"(.*?)"')

    elif '(D)' in item.other:
        down_url =  host + '/?m=Descargas'
        data = do_downloadpage(down_url, post=item.url)

        new_url = scrapertools.find_single_match(data, 'https://peliculasyserieslatino.me(.*?)"')
        if not new_url:
            new_url = scrapertools.find_single_match(data,  host + '(.*?)"')

        if new_url:
            new_url = host + new_url
            new_url = new_url.replace('/peliculasyserieslatino.me/', '/peliseries.live/')

            data = do_downloadpage(new_url)

            if 'Fembed' in item.other:
                new_url = scrapertools.find_single_match(data, "location.href='([^']+)'")
                if new_url:
                    if 'code=' in new_url:
                        id = scrapertools.find_single_match(new_url, 'code=(.*?)&')
                        if id:
                            url = 'https://femax20.com/v/%s' % id
            else:
                url = scrapertools.find_single_match(data, '<div class="cont">.*?href="(.*?)"')

    else:
       url = item.url

    if url:
        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

        url = url.replace('\\/', '/')
        url = url.replace('/peliculasyserieslatino.me/', '/peliseries.live/')

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        if not servidor == 'directo':
            url = servertools.normalize_url(servidor, url)

            itemlist.append(item.clone(server = servidor, url = url))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + '/Buscar.html?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

