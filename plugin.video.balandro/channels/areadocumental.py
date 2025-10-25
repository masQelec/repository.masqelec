# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] < 3:
    import urlparse

    PY3 = False
else:
    import urllib.parse as urlparse

    PY3 = True


from platformcode import config, logger, platformtools
from core.item import Item
from core import filetools, httptools, scrapertools, tmdb


host = 'https://www.area-documental.com/'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar documental ...', action = 'search', search_type = 'documentary', text_color='cyan' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'resultados-reciente.php' ))

    itemlist.append(item.clone( title = 'Más valorados', action = 'list_all', url = host + 'resultados.php' ))
    itemlist.append(item.clone( title = 'Más vistos', action = 'list_all', url = host +'resultados-visto.php' ))

    itemlist.append(item.clone( title = 'En [COLOR moccasin][B]3D[/B][/COLOR]', action = 'list_all', url = host + '3D.php' ))

    itemlist.append(item.clone( title = 'Series', action = 'list_all', url = host + 'series.php', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias' ))

    itemlist.append(item.clone( title = 'Por fecha', action = 'list_all', url = host + 'resultados-anio.php' ))
    itemlist.append(item.clone( title = 'Por alfabético', action = 'list_all', url = host +'resultados-titulo.php' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host).data

    block = scrapertools.find_single_match(data, '<ul class="nav navbar-nav">(.*?)</nav>')

    matches = scrapertools.find_multiple_matches(block, '<a href="(.*?)" class="dropdown-toggle" data-toggle="dropdown">(.*?)<b')

    for url, title in matches:
        title = title.strip()

        if title == 'Navegación': continue

        url = url.replace('>Indice</a></li>', '').replace('>TODO</a></li>', '').strip()

        patron = 'data-toggle="dropdown">%s.*?<b(.*?)</ul>' % title

        bloque = scrapertools.find_single_match(data, patron)

        subcats = scrapertools.find_multiple_matches(bloque, '<li><a href=".*?>(.*?)</a>')

        url =  host[:-1] + url

        itemlist.append(item.clone( action='subcategorias', title = title, url = url, subcats = subcats, plot=', '.join(subcats), text_color='cyan' ))

    return sorted(itemlist,key=lambda x: x.title)


def subcategorias(item):
    logger.info()
    itemlist = []

    if item.subcats:
        titulo = item.title.replace('[COLOR cyan]','').replace('[/COLOR]','').strip()

        url = host + 'categoria/' + titulo + '/'

        itemlist.append(item.clone( action='list_all', title=titulo, url = url, text_color='cyan' ))

    for subcat in item.subcats:
        if subcat == 'TODO': continue

        url = host + 'resultados.php?genero=&buscar=' + subcat.replace(' ', '+')

        itemlist.append(item.clone( action = 'list_all', title = subcat, url = url, text_color='dodgerblue' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<a class="hvr-shutter-out-horizontal" href="([^"]+)"><img (?:data-|)src="([^"]+)" alt="([^"]+)"'
    patron += '.*?&nbsp;&nbsp;&nbsp;(\d+| ).*?<div class="comments-space">(.*?)</div>'

    matches = scrapertools.find_multiple_matches(data, patron)

    for url, thumb, title, year, plot in matches:
        thumb = host + thumb
        plot = scrapertools.htmlclean(plot).strip()

        if not year: year = '-'

        if 'player.php' not in url:
            titulo = '%s [COLOR gray](%s)[/COLOR]' % (title, year)

            itemlist.append(item.clone( action='list_all', url = url, title = titulo, thumbnail=thumb, infoLabels={"year": year, "plot": plot} ))
        else:
            itemlist.append(item.clone( action='findvideos', url= host + url, title = title, thumbnail = thumb,
                                        infoLabels={"year": year, "plot": plot}, contentType='movie', contentTitle=title, contentExtra='documentary' ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
         next_page = scrapertools.find_single_match(data, '<li><a class="last">.*?<a href="([^"]+)')

         if next_page:
             next_page = next_page.replace('&amp;', '&')

             if '?page=' in next_page or '/pagina/' in next_page:
                 itemlist.append(item.clone( title='Siguientes ...', action='list_all', url = next_page, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    subs = scrapertools.find_multiple_matches(data, 'file: "(/webvtt[^"]+)".*?label: "([^"]+)"')

    bloque = scrapertools.find_single_match(data, 'title.*?track')

    matches = scrapertools.find_multiple_matches(bloque, 'file:\s*"([^"]+).*?label:\s*"([^"]+)"')

    i = 0

    for _url, qlty in matches:
        i += 1

        url = httptools.get_url_headers(urlparse.urljoin(host, _url))

        for _url_sub, lng in subs:
            url_sub = urlparse.urljoin(host, urlparse.quote(_url_sub))

            if lng == 'Español': lng = 'Vose'
            elif lng == 'Inglés': lng = 'Vos'
            else: lng = 'Sub ' + lng

            itemlist.append(Item( channel = item.channel, action = 'play', server='directo', title = '', url=url,
                                  ref=item.url, language=lng, quality=qlty, subtitle=url_sub ))

    if not itemlist:
        if not i == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info() 
    itemlist = []

    extension = item.url.rsplit("|", 1)[0][-4:]

    itemlist.append(['%s %s' % (extension, item.calidad), item.url, 0, item.subtitle])

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'resultados.php?genero=&buscar=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
