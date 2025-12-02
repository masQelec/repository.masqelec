# -*- coding: utf-8 -*-

import re, base64

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.cinemundo.com.ar/'


perpage = 20


def do_downloadpage(url, post=None, headers=None):
    if not headers: headers = {'Referer': host}

    data = httptools.downloadpage(url, post=post, headers=headers).data

    return data


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie', text_color = 'deepskyblue' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'list_page.php', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Más valoradas', action = 'list_list', url = host + 'ranking_page.php', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'movie' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    cats = {
        'Adolescencia',
        'Amor',
        'Clasico',
        'Comedia',
        'Cortometraje',
        'Culto',
        'Documental',
        'Derechos Humanos',
        'Hechos Reales',
        'LGTB',
        'Sexualidad',
        'Suspenso',
        'Tercera Edad',
        'Terror',
        'Thriller',
        'Violencia de Género'
        }

    for cat in cats:
        categ = base64.b64encode(cat.encode('utf8')).decode('utf8')

        if cat == 'Violencia de Género': categ = 'VmlvbGVuY2lhIGRlIEfpbmVybw=='

        url = "{}find_page.php?str={}".format(host, categ)

        itemlist.append(item.clone( title = cat, url = url, action = 'list_all', text_color = 'deepskyblue' ))

    return sorted(itemlist, key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    data = do_downloadpage(host)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '>BUSQUEDA POR A(.*?)</div>')

    matches = scrapertools.find_multiple_matches(bloque, '<span class="text-gray-3500 font-size-16">(.*?)</span>')

    for match in matches:
        if match == str(current_year): continue

        anyo = base64.b64encode(match.encode('utf8')).decode('utf8')

        url = "{}find_page.php?str={}".format(host, anyo)

        itemlist.append(item.clone( title = match, url = url, action = 'list_all', year = match, text_color='deepskyblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    if 'ENCONTRAMOS' in data:
        bloque = scrapertools.find_single_match(data, 'ENCONTRAMOS(.*?)</main>')

        matches = scrapertools.find_multiple_matches(bloque, '<div class="product(.*?)style="width: 98%;">')

    elif 'LISTADO COMPLETO' in data:
        bloque = scrapertools.find_single_match(data, 'LISTADO COMPLETO(.*?)</main>')

        matches = scrapertools.find_multiple_matches(bloque, '<div class="col-md-4 col-xl-3 my-auto"(.*?)</div></div></div></div></div>')

    else:
        bloque = scrapertools.find_single_match(data, '</section>(.*?)</main>')

        matches = scrapertools.find_multiple_matches(bloque, '<div class="col-md(.*?)</div></div></div></div></div>')

    for match in matches:
        if 'ENCONTRAMOS' in data:
            url = scrapertools.find_single_match(match, 'id="hijo">.*?<a href="(.*?)"')
        else:
            url = scrapertools.find_single_match(match, '<a href="(.*?)"')

        title = scrapertools.find_single_match(match, 'alt="(.*?)"').strip()

        if not url or not title: continue

        if 'RECOMENDADAS' in title: continue

        thumb = scrapertools.find_single_match(match, 'src="(.*?)"')

        if thumb: thumb = host[:-1] + thumb

        if '.arimages/' in thumb: thumb.replace('.arimages/', '.ar/images/')

        url = host + url

        year = '-'

        if item.year: year = year

        if not year == '-':
          year = scrapertools.find_single_match(title, ' (\d{4})')

          if year:
              title = title.replace('(%s)' % year, '').strip()

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                    contentType = 'movie', contentTitle = title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if '<ul class="pagination">' in data:
             next_page = scrapertools.find_single_match(data, '<ul class="pagination">.*?<li class="page-item d-none d-md-block active">.*?</a>.*?href="(.*?)"')

             if next_page:
                 if '?pagina=' in next_page or '&pagina=' in next_page:
                     if not '?pagina=' in item.url and not '&pagina=' in item.url:
                         if '?str=' in item.url: item.url = item.url.split("?str=")[0]
                         next_url = item.url + next_page
                     else:
                         if "?pagina=" in item.url: ant_url = item.url.split("?pagina=")[0]
                         else: ant_url = item.url.split("&pagina=")[0]

                         ant_pag = scrapertools.find_single_match(item.url, 'pagina=(.*?)$')

                         next_page = int(ant_pag)
                         next_page = next_page + 1

                         if '?pagina=' in item.url:
                             next_url = ant_url + '?pagina=' + str(next_page)
                         else:
                             next_url = ant_url + '&pagina=' + str(next_page)

                     itemlist.append(item.clone( title = 'Siguientes ...', url = next_url, action = 'list_all', text_color='coral' ))

    return itemlist


def list_list(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<table>(.*?)</section>')

    matches = scrapertools.find_multiple_matches(bloque, "<a href='(.*?)'>(.*?)</a>")

    num_matches = len(matches)

    for url, title in matches[item.page * perpage:]:
        if 'RECOMENDADAS' in title: continue

        MovieName = title

        if ' (' in MovieName: MovieName = MovieName.split(" (")[0]

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title,
                                    contentType = 'movie', contentTitle = MovieName, infoLabels={'year': '-'} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='Siguientes ...', page=item.page + 1, action='list_list', text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<div class="col-lg">(.*?)</div>')

    matches = scrapertools.find_multiple_matches(bloque, '<iframe.*?src="(.*?)".*?</iframe>')

    ses = 0

    for match in matches:
        if not match: continue

        ses += 1

        lang = '?'

        url = match

        servidor = servertools.get_server_from_url(url)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, url)

        itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, url = url, language = lang ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
       texto = base64.b64encode(str(texto).encode('utf8')).decode('utf8')
       item.url = "{}find_page.php?str={}".format(host, texto)
       return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

