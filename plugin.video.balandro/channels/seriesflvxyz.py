# -*- coding: utf-8 -*-

import sys

PY3 = sys.version_info[0] >= 3

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, servertools, tmdb


host = 'https://seriesflv.xyz/'

url_ajax = host + 'wp-admin/admin-ajax.php'

IDIOMAS = {'Español': 'Esp', 'es': 'Esp', 'Latino': 'Lat', 'mx': 'Lat', 'Subtitulado': 'Vose', 'Ingles': 'VO', 'en': 'VO', 'Japones': 'VO', 'jp': 'VO'}


def do_downloadpage(url, post=None, headers=None, raise_weberror=True):
    if 'ano/' in url:
        raise_weberror = False

    data = httptools.downloadpage(url, post=post, headers=headers, raise_weberror=raise_weberror).data

    return data


def mainlist(item):
    return mainlist_series(item)


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url= host + 'online-series-completas/' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'last_episodes', url = host + 'ver/' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios' ))
    itemlist.append(item.clone( title = 'Por plataforma', action = 'plataformas' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action='search', search_type='tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(host)

    bloque = scrapertools.find_single_match(data, '>Generos<(.*?)</ul>')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)">(.*?)</a>')

    for url, tit in matches:
        itemlist.append(item.clone( title = tit, url = url, action = 'list_all' ))

    return itemlist


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1979, -1):
        itemlist.append(item.clone( title = str(x), url = host + 'ano/' + str(x) + '/', action = 'list_all' ))

    return itemlist


def plataformas(item):
    logger.info()
    itemlist = []

    productoras = [
        ['abc', 'ABC'],
        ['adult-swim', 'Adult Swim'],
        ['amazon', 'Amazon'],
        ['amc', 'AMC'],
        ['apple-tv', 'Apple TV+'],
        ['bbc-one', 'BBC One'],
        ['bbc-two', 'BBC Two'],
        ['bs11', 'BS11'],
        ['cbc', 'CBC'],
        ['cbs', 'CBS'],
        ['comedy-central', 'Comedy Central'],
        ['disney', 'Disney+'],
        ['disney-xd', 'Disney XD'],
        ['espn', 'ESPN'],
        ['fox', 'FOX'],
        ['fx', 'FX'],
        ['hbc', 'HBC'],
        ['hbo', 'HBO'],
        ['hbo-espana', 'HBO España'],
        ['hbo-max', 'HBO Max'],
        ['hulu', 'Hulu'],
        ['kbs-kyoto', 'KBS Kyoto'],
        ['mbs', 'MBS'],
        ['nbc', 'NBC'],
        ['netflix', 'Netflix'],
        ['nickelodeon', 'Nickelodeon'],
        ['paramount', 'Paramount+'],
        ['showtime', 'Showtime'],
        ['sky-atlantic', 'Sky Atlantic'],
        ['stan', 'Stan'],
        ['starz', 'Starz'],
        ['syfy', 'Syfy'],
        ['tbs', 'TBS'],
        ['telemundo', 'Telemundo'],
        ['the-cw', 'The CW'],
        ['tnt', 'TNT'],
        ['tokyo-mx', 'Tokyo MX'],
        ['tv-tokyo', 'TV Tokyo'],
        ['usa-network', 'USA Network'],
        ['youtube-premium', 'YouTube Premium'],
        ['zdf', 'ZDF']
        ]

    url = host + 'network/'

    for x in productoras:
        itemlist.append(item.clone( title = x[1], url = url + str(x[0]) + '/', action = 'list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h1>(.*?)>Series Mas Vistas<')

    matches = scrapertools.find_multiple_matches(bloque, '<article (.*?)</article>')

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)')
        title = scrapertools.find_single_match(article, ' alt="([^"]+)').strip()
        if not url or not title: continue

        year = scrapertools.find_single_match(title, '\((\d{4})\)')
        if year:
            title = re.sub('\(\d{4}\)$', '', title).strip()
        else:
            year = '-'

        thumb = scrapertools.find_single_match(article, ' src="([^"]+)')

        itemlist.append(item.clone( action = 'temporadas', url = url, title = title, thumbnail = thumb, 
                                    contentType = 'tvshow', contentSerieName = title, infoLabels = {'year': year} ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, '<div class="pagination".*?<span class="current".*?href="([^"]+)"')
    if next_page:
       if '/page/' in next_page:
           itemlist.append(item.clone (url = next_page, page = 0, title = '>> Página siguiente', action = 'list_all', text_color='coral' ))

    return itemlist


def last_episodes(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    bloque = scrapertools.find_single_match(data, '<h1>(.*?)>Series Mas Vistas<')

    matches = scrapertools.find_multiple_matches(bloque, '<article (.*?)</article>')

    for article in matches:
        url = scrapertools.find_single_match(article, ' href="(.*?)"')
        title = scrapertools.find_single_match(article, '<span class="c">(.*?)</span>').strip()

        season, episode = scrapertools.find_single_match(article, '<span class="b">(.*?)x(.*?)</span>')
        season = season.strip()
        episode = episode.strip()

        if not title or not url or not season or not episode: continue

        thumb = scrapertools.find_single_match(article, ' src="(.*?)"')

        titulo = '%sx%s %s' % (season, episode, title)

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail = thumb,
                                    contentType='episode', contentSerieName=title, contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, '<div class="pagination".*?<span class="current".*?href="([^"]+)"')
    if next_page:
       if '/page/' in next_page:
           itemlist.append(item.clone (url = next_page, page = 0, title = '>> Página siguiente', action = 'last_episodes', text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    headers = {'Referer': host}
    data = do_downloadpage(item.url, headers = headers)

    script = scrapertools.find_single_match(data, '<script type="text/javascript" src="data:text/javascript;base64,([^"]+)"')
    script_dec = base64.b64decode(script) if not PY3 and not isinstance(base64.b64decode(script), bytes) else base64.b64decode(script).decode('utf-8')

    d = re.search('jQuery\.post\("([^"]+)",({[^}+]+})', script_dec).group(2)
    post = re.sub('([A-Z|a-z]+):', lambda x: '"%s":' % (x.group(1)), re.sub('id:(id)', '"id":%s' %(re.findall("var id=(\d+)", script_dec)[0]), d))

    if not post: return

    post_id = scrapertools.find_single_match(post, '"id":(.*?)}')

    headers = {'Referer': item.url}
    post = {'action': 'seasons', 'id': post_id}

    data = do_downloadpage(url_ajax, post = post, headers = headers)

    matches = scrapertools.find_multiple_matches(data, "<span class='title'>Temporada(.*?)<i>")

    for numtempo in matches:
        numtempo = numtempo.strip()
        title = 'Temporada ' + numtempo

        if len(matches) == 1:
            platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&'), 'solo [COLOR tan]' + title + '[/COLOR]')
            item.page = 0
            item.id = post_id
            item.contentType = 'season'
            item.contentSeason = numtempo
            itemlist = episodios(item)
            return itemlist

        itemlist.append(item.clone( action = 'episodios', title = title, id = post_id, contentType = 'season', contentSeason = numtempo, page = 0 ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    perpage = 50

    headers = {'Referer': item.url}
    post = {'action': 'seasons', 'id': item.id}

    data = do_downloadpage(url_ajax, post = post, headers = headers)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, "<span class='title'>Temporada " + str(item.contentSeason) + "(.*?)</div></div>")

    matches = scrapertools.find_multiple_matches(bloque, "div class='imagen'(.*?)</li>")

    for match in matches[item.page * perpage:]:
        id = scrapertools.find_single_match(match, "data-id='(.*?)'")

        url = scrapertools.find_single_match(match, "<a href='(.*?)'")
        title = scrapertools.find_single_match(match, "<div class='episodiotitle'>.*?>(.*?)</a>").strip()

        thumb = scrapertools.find_single_match(match, "src='(.*?)'")

        langs = scrapertools.find_multiple_matches(match, '<img title="(.*?)"')

        lngs = []
        for lang in langs:
            lngs.append(IDIOMAS.get(lang, lang))

        temp, epis = scrapertools.find_single_match(match, "div class='numerando'>(.*?)-(.*?)</div>")
        temp = temp.strip()
        epis = epis.strip()

        titulo = temp + 'x' + epis + ' ' + title

        itemlist.append(item.clone( action = 'findvideos', url = url, title = titulo, id = id, thumbnail = thumb, languages = ', '.join(lngs),
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= perpage:
            break

    if len(matches) > (item.page + 1) * perpage:
        itemlist.append(item.clone( title=">> Página siguiente", action="episodios", page=item.page + 1, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(data, "<tr id='link-'(.*?)</tr>")

    ses = 0

    for match in matches:
        ses += 1

        url = scrapertools.find_single_match(match, "<a href='(.*?)'")

        if url:
            if 'hqq' in url or 'waaw' in url or 'netu' in url: continue
            elif 'openload' in url: continue
            elif 'powvideo' in url: continue
            elif 'streamplay' in url: continue
            elif 'streamcloud' in url: continue
            elif 'vidtodo' in url: continue
            elif 'vidia' in url: continue

            elif url.endswith("/lmesl.html"): continue

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            if servidor == 'directo':
                if '/ul.to/' in url: continue
                elif '/rapidgator.net/' in url: continue
                elif '/katfile.com/' in url: continue

            lng = scrapertools.find_single_match(match, "<img style.*?src='.*?/flags/(.*?).png")
            qlty = scrapertools.find_single_match(match, "<strong class='quality'>(.*?)</strong>")

            itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url, quality = qlty,
                                 language = IDIOMAS.get(lng, lng) ))

    # embeds
    matches = scrapertools.find_multiple_matches(data, "<li id='player-option-(.*?)</li>")

    for match in matches:
        ses += 1

        d_post = scrapertools.find_single_match(match, "data-post='(.*?)'")
        d_nume = scrapertools.find_single_match(match, "data-nume='(.*?)'")

        if not d_post or not d_nume: continue

        other =  scrapertools.find_single_match(match, "<span class='title'>(.*?)</span>")

        if 'hqq' in other or 'waaw' in other or 'netu' in other: continue
        elif 'openload' in other: continue
        elif 'powvideo' in other: continue
        elif 'streamplay' in other: continue
        elif 'streamcloud' in url: continue
        elif 'vidtodo' in other: continue
        elif 'vidia' in other: continue

        other = other.replace('www.', '').replace('.com', '').replace('.net', '').replace('.org', '').replace('.co', '').replace('.cc', '')
        other = other.replace('.to', '').replace('.tv', '').replace('.ru', '').replace('.io', '').replace('.eu', '').replace('.ws', '')
        other = other.replace('.', '')

        lng = scrapertools.find_single_match(match, "<img src='.*?/flags/(.*?).png")

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = item.url, dpost = d_post, dnume = d_nume,
                             language = IDIOMAS.get(lng, lng), other = other ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    url = item.url

    if item.other:
        headers = {'Referer': item.url}
        post = {'action': 'doo_player_ajax', 'post': item.dpost, 'nume': item.dnume, 'type': 'tv'}

        data = do_downloadpage(url_ajax, post = post, headers = headers)

        vid = scrapertools.find_single_match(data, "<iframe.*?src='(.*?)'")

        if vid:
            url = vid

    if url:
        if '/hqq.' in url or '/waaw.' in url or '/netu.' in url:
            return 'Requiere verificación [COLOR red]reCAPTCHA[/COLOR]'

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

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
