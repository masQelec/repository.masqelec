# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://pepecine.co/'


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    timeout = 50

    if not headers: headers = {'Referer': host}

    if '/fecha/' in url: raise_weberror = False
    elif '/category/' in url: raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data

    if '<title>You are being redirected...</title>' in data:
        try:
            from lib import balandroresolver
            ck_name, ck_value = balandroresolver.get_sucuri_cookie(data)
            if ck_name and ck_value:
                httptools.save_cookie(ck_name, ck_value, host.replace('https://', '')[:-1])
                data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror, timeout=timeout).data
        except:
            pass

    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all', text_color = 'yellow' ))

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis', text_color = 'deepskyblue' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series', text_color = 'hotpink' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'peliculas/', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más destacadas', action = 'list_all', url = host, group = 'masd', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'series/', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    patron = '<li id="menu-item-\d+" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-\d+"><a href="([^"]+)">([^<]+)'
    matches = re.compile(patron).findall(data)

    for url, title in matches:
        itemlist.append(item.clone( title = title.capitalize(), action = 'list_all', url = url ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1978, -1):
        url = host + 'peliculas/fecha/' + str(x) + '/'

        itemlist.append(item.clone( title = str(x), url = url, action='list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if item.post:
        data = do_downloadpage(item.url, item.post)
    else:
        data = do_downloadpage(item.url)

    if not item.group:
        bloque = data
    else:
        bloque = scrapertools.find_single_match(data, '<div class="grid popular">(.*?)</section>')

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(bloque)

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')

        title = scrapertools.find_single_match(article, '<div class="entry-title">(.*?)</div>')
        if not title: title = scrapertools.find_single_match(article, '<h2 class="entry-title">(.*?)</h2>')

        if not url or not title: continue

        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')

        tipo = 'movie' if '/pelicula/' in url else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if item.search_type != 'all':
                if item.search_type == 'tvshow': continue

            itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb, fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels = {'year': '-'} ))

        if tipo == 'tvshow':
            if item.search_type != 'all':
                if item.search_type == 'movie': continue

            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, fmt_sufijo=sufijo,
                                        contentType = 'tvshow', contentSerieName = title, infoLabels={'year': '-'} ))

    tmdb.set_infoLabels(itemlist)

    if item.group: return itemlist

    if itemlist:
        url = host + 'wp-admin/admin-ajax.php'

        if not item.next_page:
            if not '"load-more-ajax"' in data: return itemlist
            item.next_page = 1

        item.next_page = item.next_page + 1

        _types = 'all'
        if item.search_type == 'movie': _types = 'movie'
        elif item.search_type == 'tvshow': _types = 'serie'

        post = {'action': 'action_sorting_post', 'page': item.next_page, 'types': _types}

        itemlist.append(item.clone( title = 'Siguientes ...', url = url, post = post, action = 'list_all', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    temporadas = re.compile('data-temporada="(.*?)"', re.DOTALL).findall(data)

    for tempo in temporadas:
        title = 'Temporada ' + tempo

        if len(temporadas) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.contentType = 'season'
            item.contentSeason = tempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, contentType = 'season', contentSeason = tempo ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    serie_id = scrapertools.find_single_match(data, 'data-id="(.*?)"')

    if not serie_id: return itemlist

    post = {'action': 'action_change_episode', 'season': str(item.contentSeason), 'serie_id': serie_id}

    headers = {'Referer': item.url}

    data = do_downloadpage(host + 'wp-admin/admin-ajax.php', post = post, headers = headers)

    matches = scrapertools.find_multiple_matches(data, ' src="(.*?)".*?<div class="num">(.*?)</div>.*?<h2 class="entry-title">(.*?)</h2>.*?<a href="(.*?)"')

    if item.page == 0:
        sum_parts = len(matches)
        if sum_parts > 250:
            if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos?'):
                platformtools.dialog_notification('PepeCineCo', '[COLOR cyan]Cargando elementos[/COLOR]')
                item.perpage = 250

    for thumb, s_e, title, url in matches[item.page * item.perpage:]:
        if not thumb.startswith('http'): thumb = 'https:' + thumb

        episode = scrapertools.find_single_match(s_e, ".*?- E(.*?)$")

        itemlist.append(item.clone( action='findvideos', url = url, title = title, thumbnail=thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber=episode ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist=[]

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '<li data-playerid="(.*?)".*?/flags/(.*?).png.*?<span style.*?>(.*?)</span>')

    ses = 0

    for url, lang, qlty in matches:
        ses += 1

        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url: continue
        elif '/gounlimited.' in url: continue
        elif '/jetload.' in url: continue
        elif '/vidcloud.' in url: continue
        elif '.mystream.' in url: continue

        if lang == 'es': lang = 'Esp'
        elif lang == 'la': lang = 'Lat'
        elif lang == 'mx': lang = 'Lat'
        else: lang = 'Vose'

        if '//mega.' in url:
            servidor = 'mega'
            if '/embed#!#!' in url: url = url.replace('/embed#!#!', '/embed#!')
        else:
            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        other = ''
        if '//pelistop' in url:
            if '&server=apialfa' in url: other = 'Apialfa'
            else: other = 'Pelistop'
        elif '//api.cuevana3' in url: other = 'Apicuevana3'

        itemlist.append(Item(channel = item.channel, action = 'play', title = '', server = servidor, url = url,
                        language = lang, quality = qlty, other = other ))

    # Descargas
    matches = scrapertools.find_multiple_matches(data, '<span class="num">#.*?</span>(.*?)</td><td>(.*?)</td><td><span>(.*?)</span>.*?href="(.*?)"')

    for srv, lang, qlty, url in matches:
        ses += 1

        srv = srv.replace('.net', '').replace('.com', '').replace('.nz', '').replace('.to', '').replace('.co', '').strip().lower()

        if srv == 'turbobit': continue
        elif srv == '1fichier': continue

        if lang == 'Castellano': lang = 'Esp'
        elif lang == 'Latino': lang = 'Lat'
        elif lang == 'Subtitulado': lang = 'Vose'

        if srv == 'bittorrent': servidor = 'torrent'
        elif srv == 'mega':
              servidor = 'mega'

              if 'url=' in url: url = scrapertools.find_single_match(url, 'url=(.*?)$')
              if not '/embed' in url: url = url.replace('https://mega.nz/', 'https://mega.nz/embed')
        else:
           servidor = servertools.get_server_from_url(url)
           servidor = servertools.corregir_servidor(servidor)

           url = servertools.normalize_url(servidor, url)

        other = 'D'
        if not srv == servidor: other = srv + ' d'

        itemlist.append(Item(channel = item.channel, action = 'play', title = '', server = servidor, url = url,
                        language = lang, quality = qlty, other = other ))

    itemlist = servertools.get_servers_itemlist(itemlist)

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def resuelve_dame_toma(dame_url):
    data = do_downloadpage(dame_url)

    url = scrapertools.find_single_match(data, 'file:\s*"([^"]+)')
    if not url:
        checkUrl = dame_url.replace('embed.html#', 'details.php?v=')
        data = do_downloadpage(checkUrl, headers={'Referer': dame_url})
        url = scrapertools.find_single_match(data, '"file":\s*"([^"]+)').replace('\\/', '/')

    return url


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if 'D' in item.other or ' d' in item.other:
        if not '//streamsb.net/' in item.url:
            if '/?url=magnet:' in url: url = scrapertools.find_single_match(url, '/?url=(.*?)$')
            else:
               if '?url=' in item.url:
                   new_url = scrapertools.find_single_match(item.url, 'url=(.*?)$')

                   if '.tomatomatela.' in new_url:
                      url_post = scrapertools.find_single_match(new_url, 'h=(.*?)$')

                      if url_post:
                          resp = httptools.downloadpage('https://apialfa.tomatomatela.com/ir/rd.php', post={'url': url_post}, follow_redirects=False, only_headers=True)

                          url = resp.headers['location']

                          servidor = servertools.get_server_from_url(url)
                          servidor = servertools.corregir_servidor(servidor)

                          if not servidor == 'directo':
                              itemlist.append(item.clone( url = url, server = servidor ))
                          else:
                              url = resuelve_dame_toma(url)
                              itemlist.append(item.clone( url = url, server = 'directo' ))

                          return itemlist

               else:
                   data = do_downloadpage(item.url)

                   url = scrapertools.find_single_match(data, 'url="(.*?)"')

                   if not url:
                       new_url = scrapertools.find_single_match(data, 'href="(.*?)"')
                       if new_url:
                           if '/short/' in new_url:
                               data = do_downloadpage(new_url)
                               url = scrapertools.find_single_match(data, 'url=(.*?)"')

        if url:
            if '/%23!' in url: url = url.replace('/%23!%23!', '/#!').replace('/%23!', '/#!')

            if '//pelistop.co/' in url:
                url = url.replace('//pelistop.co/', '//streamsb.net/')

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                itemlist.append(item.clone( url = url, server = servidor ))
                return itemlist

    elif item.server == 'directo':
        if item.other == 'Apicuevana3':
            data = do_downloadpage(item.url)

            new_url = scrapertools.find_single_match(item.url, '(.*?)h=')
            new_url = new_url.replace('?', '').strip()

            url_post = scrapertools.find_single_match(data, 'onclick="location.href=' + "'.*?h=(.*?)'")

            if url_post:
                data = do_downloadpage(new_url + 'api.php', post={'h': url_post})

                url = scrapertools.find_single_match(data, '"url":"(.*?)"')
                url = url.replace('\\/', '/')

                servidor = servertools.get_server_from_url(url)
                servidor = servertools.corregir_servidor(servidor)

                itemlist.append(item.clone( url = url, server = servidor ))
                return itemlist

        elif '/api/' in item.url:
           data = do_downloadpage(item.url)

           new_url = scrapertools.find_single_match(data, '<iframe.*?src="(.*?)"')

           if item.other == 'Apialfa':
               if new_url:
                   if '.tomatomatela.' in new_url:
                      data = do_downloadpage(new_url)

                      url_post = scrapertools.find_single_match(data, '<input type="hidden" id="url" name="url" value="(.*?)"')

                      if url_post:
                          data = do_downloadpage('https://apialfa.tomatomatela.com/ir/rd.php', post={'url': url_post})

                          new_url_post = scrapertools.find_single_match(data, '<input type="hidden" id="url" name="url" value="(.*?)"')
                          if new_url_post:
                              resp = httptools.downloadpage('https://apialfa.tomatomatela.com/ir/redirect_ddh.php', post={'url': new_url_post}, follow_redirects=False, only_headers=True)

                              url = resp.headers['location']
                              url = resuelve_dame_toma(url)

                              itemlist.append(item.clone( url = url, server = item.server ))
                              return itemlist

                   elif '/tomatomatela.' in new_url:
                      url = resuelve_dame_toma(new_url)

                      itemlist.append(item.clone( url = url, server = item.server ))
                      return itemlist

           url = scrapertools.find_single_match(data, '>Ver ahora<.*?src="(.*?)"')

           if url:
               if '//pelistop.co/' in url:
                   url = url.replace('//pelistop.co/', '//streamsb.net/')

                   servidor = servertools.get_server_from_url(url)
                   servidor = servertools.corregir_servidor(servidor)

                   itemlist.append(item.clone( url = url, server = servidor ))
                   return itemlist

    if url:
        if url.startswith('magnet:'):
           itemlist.append(item.clone( url = url, server = 'torrent' ))

        elif url.endswith(".torrent"):
           itemlist.append(item.clone( url = url, server = 'torrent' ))

        elif url.startswith('https://adfly.mobi/'):
            return itemlist

        else:
           itemlist.append(item.clone( url = url, server = item.server ))

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
