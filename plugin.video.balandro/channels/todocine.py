# -*- coding: utf-8 -*-

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

from lib import jsunpack


host = 'https://yaske.ru/'


api = host + 'api/v1/channel/'


perpage = 25


def do_downloadpage(url, post=None, headers=None):
    if not headers: headers = {'Referer': host}

    data = httptools.downloadpage(url, post=post, headers=headers).data

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

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all',
                                url = api + '2?returnContentOnly=true&restriction=&order=popularity:desc&perPage=50&query=&page=1', search_type = 'movie' ))

    itemlist.append(item.clone( title='[COLOR cyan]Estrenos[/COLOR]', action='list_all',
                                url = api + '31?returnContentOnly=true&restriction=&order=popularity:desc&perPage=50&query=&page=1', search_type = 'movie' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow', text_color = 'hotpink' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all',
                                url = api + '3?returnContentOnly=true&restriction=&order=popularity:desc&perPage=50&query=&page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title='[COLOR cyan]Estrenos[/COLOR]', action='list_all',
                                url = api + '30?0returnContentOnly=true&restriction=&order=popularity:desc&perPage=50&query=&page=1', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Animación', action = 'list_all',
                                url = api + '117?0returnContentOnly=true&restriction=&order=popularity:desc&perPage=50&query=&page=1', search_type = 'tvshow' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 1

    data = do_downloadpage(item.url)

    data = data.replace('}}]}}', '}},')

    matches = scrapertools.find_multiple_matches(str(data), '{"id":(.*?)}},')

    num_matches = len(matches)

    for match in matches[item.page * perpage:]:
        _id = scrapertools.find_single_match(match, '(.*?),')

        title =  scrapertools.find_single_match(match, '"name":"(.*?)"')

        if title.startswith('Estrenos') or title.startswith('estreno'):
            title =  scrapertools.find_single_match(match, '"data":.*?"name":"(.*?)"')

        if not title or not _id: continue

        title = clean_title(title)

        thumb = scrapertools.find_single_match(match, '"poster":"(.*?)"')

        thumb = thumb.replace('\\/', '/')

        year = scrapertools.find_single_match(match, '"release_date":"(.*?)-')
        if not year: year = '-'

        langs = []
        if '"language":"es"' in match: langs.append('Esp')
        if '"language":"la"' in match: langs.append('Lat')
        if '"language":"en_ES"' in match: langs.append('Vose')
        if '"language":"sub-es"' in match: langs.append('Vose')

        plot = scrapertools.find_single_match(match, '"description":"(.*?)"')

        tipo = 'movie' if '"is_series":false' in match else 'tvshow'
        sufijo = '' if item.search_type != 'all' else tipo

        if tipo == 'movie':
            if not item.search_type == "all":
                if item.search_type == "tvshow": continue

            url = scrapertools.find_single_match(match, '"primary_video":{"id":(.*?),')

            if not url: url = _id

            url = host + 'api/v1/watch/' + url

            itemlist.append(item.clone( action = 'findvideos', url=url, title=title, thumbnail=thumb, languages=', '.join(langs), fmt_sufijo=sufijo,
                                        contentType = 'movie', contentTitle = title, infoLabels={'year': year, 'plot': plot} ))

        if tipo == 'tvshow':
            if not item.search_type == "all":
                if item.search_type == "movie": continue

            url = _id

            url = host + 'api/v1/titles/' + url + '?loader=titlePage'

            itemlist.append(item.clone( action='temporadas', url=url, id=_id, title=title, thumbnail=thumb, languages=', '.join(langs), fmt_sufijo=sufijo,
                                        contentType='tvshow', contentSerieName=title, infoLabels={'year': year, 'plot': plot} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        buscar_next = True
        if num_matches > perpage:
            hasta = (item.page * perpage) + perpage
            if hasta < num_matches:
                itemlist.append(item.clone( title='Siguientes ...', page=item.page + 1, action='list_all', text_color='coral' ))
                buscar_next = False

        if buscar_next:
            next_page = scrapertools.find_single_match(str(data), '"next_page":(.*?),')

            if next_page:
                actu_page = scrapertools.find_single_match(item.url, '(.*?)&page=')

                if actu_page:
                    next_page = actu_page + '&page=' + next_page

                    itemlist.append(item.clone( title = 'Siguientes ...', action='list_all', url = next_page, page = 0, text_color='coral' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    match = scrapertools.find_single_match(str(data), '"total":(.*?)},')

    tempo = 1

    total = int(match)

    while tempo <= total:
        season = tempo

        if int(season) < 10: season = '0%s' % season

        title = 'Temporada ' + str(season)

        url = host + 'api/v1/titles/' + item.id + '/seasons/' + str(season) + '?loader=seasonPage'

        if total == 1:
            if config.get_setting('channels_seasons', default=True):
                platformtools.dialog_notification(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), 'solo [COLOR tan]' + title + '[/COLOR]')

            item.page = 0
            item.contentType = 'season'
            item.contentSeason = tempo
            item.url = url
            itemlist = episodios(item)
            return itemlist

        tempo +=1

        itemlist.append(item.clone( action = 'episodios', url = url, title = title, page = 0,
                                    contentType = 'season', contentSeason = season, text_color = 'tan' ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = do_downloadpage(item.url)

    matches = scrapertools.find_multiple_matches(str(data), '"poster":"(.*?)".*?"episode_number":(.*?),.*?"primary_video":.*?"id":(.*?),')

    if item.page == 0 and item.perpage == 50:
        sum_parts = len(matches)

        try:
            tvdb_id = scrapertools.find_single_match(str(item), "'tvdb_id': '(.*?)'")
            if not tvdb_id: tvdb_id = scrapertools.find_single_match(str(item), "'tmdb_id': '(.*?)'")
        except: tvdb_id = ''

        if config.get_setting('channels_charges', default=True):
            item.perpage = sum_parts
            if sum_parts >= 100:
                platformtools.dialog_notification('TodoCine', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
        elif tvdb_id:
            if sum_parts > 50:
                platformtools.dialog_notification('TodoCine', '[COLOR cyan]Cargando Todos los elementos[/COLOR]')
                item.perpage = sum_parts
        else:
            item.perpage = sum_parts

            if sum_parts >= 1000:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]500[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('TodoCine', '[COLOR cyan]Cargando 500 elementos[/COLOR]')
                    item.perpage = 500

            elif sum_parts >= 500:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('TodoCine', '[COLOR cyan]Cargando 250 elementos[/COLOR]')
                    item.perpage = 250

            elif sum_parts >= 250:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]125[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('TodoCine', '[COLOR cyan]Cargando 125 elementos[/COLOR]')
                    item.perpage = 125

            elif sum_parts >= 125:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]75[/B][/COLOR] elementos ?'):
                    platformtools.dialog_notification('TodoCine', '[COLOR cyan]Cargando 75 elementos[/COLOR]')
                    item.perpage = 75

            elif sum_parts > 50:
                if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos [COLOR cyan][B]Todos[/B][/COLOR] de una sola vez ?'):
                    platformtools.dialog_notification('TodoCine', '[COLOR cyan]Cargando ' + str(sum_parts) + ' elementos[/COLOR]')
                    item.perpage = sum_parts
                else: item.perpage = 50

    for thumb, epis, id in matches[item.page * item.perpage:]:
        if int(epis) < 10: epis = '0%s' % epis

        titulo = str(item.contentSeason) + 'x' + str(epis) + ' ' + item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'")

        thumb = thumb.replace('\\/', '/')

        url = host + 'api/v1/watch/' + id

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb,
                                    contentType = 'episode', contentSeason = item.contentSeason, contentEpisodeNumber = epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title = "Siguientes ...", action = "episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {"es": "Esp", "la": "Lat", "en_ES": "Vose", "sub-es": "Vose"}

    QLTYS = {
    "69efbcea-12fa-4de8-bd19-02fa4f3278e0": "HD-1080p",
    "0cff0831-29ef-402d-8261-2c9f1880d807": "HD-720p",
    "d9297a62-c289-4780-8c00-dab7d3249839": "HD-TS",
    "5f744bff-7374-40c2-8f22-bb493823d3b9": "CAM",
    "042a13b8-ea18-4e56-9d4e-aec2684746ec": "SD"
    }

    data = do_downloadpage(item.url)

    options = scrapertools.find_multiple_matches(str(data), '"src":"(.*?)".*?"quality":"(.*?)".*?"language":"(.*?)".*?"domain":"(.*?)"')

    ses = 0

    for src, qlty, lang, domain in options:
        ses += 1

        src = src.replace('\\/', '/')

        if not src: continue

        if 'katfile' in domain: continue
        elif 'nitroflare' in domain: continue
        elif 'rapidgator' in domain: continue
        elif '1fichier' in domain: continue
        elif 'localhost' in domain: continue

        elif 'powvideo' in domain: continue
        elif 'streamplay' in domain: continue

        other = domain.replace('www.', '').replace('.com', '').replace('.net', '').replace('.me', '').replace('.sx', '').replace('.to', '').replace('.name', '').replace('.site', '').replace('.space', '').replace('.io', '').replace('.st', '').lower().strip()

        url = host[:-1] + src

        servidor = ''
        if not '.' in other:
            servidor = other

            if servidor == 'smoothpre':
                other = servidor
                servidor = servidor = servertools.corregir_servidor(other)
            else:
                other = ''

        itemlist.append(Item(channel = item.channel, action = 'play', server=servidor, title = '', url=url,
                             language=IDIOMAS.get(lang, lang), quality=QLTYS.get(qlty, qlty), other=other.capitalize() ))

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    video = get_video_url(item.url)

    if video:
        servidor = servertools.corregir_other(video)
        servidor = servertools.corregir_servidor(servidor)

        url = servertools.normalize_url(servidor, video)

        if servidor == 'directo':
            new_server = servertools.corregir_other(url).lower()
            if new_server.startswith("http"):
                if not config.get_setting('developer_mode', default=False): return itemlist
            servidor = new_server

        url = url + '|Referer=' + host

        itemlist.append(item.clone(url = url, server = servidor))

    return itemlist


def get_video_url(url):
    video = ''

    headers = {'Referer': url.replace('/link/', '/watch/')}

    data = do_downloadpage(url, headers=headers)

    logger.info("check-01-todo: %s" % data)

    try:
        # ~ eval(function(p,a,c,k,e,d){ ... }
        packed = scrapertools.find_single_match(data, "<script>(.*?)\s</script>")

        logger.info("check-02-todo: %s" % packed)

        unpacked = jsunpack.unpack(packed)
    except:
        unpacked = ''

    logger.info("check-03-todo: %s" % unpacked)

    if unpacked:
        video = scrapertools.find_single_match(unpacked, 'link:"(.*?)"')

        return video

    # ~ FORZADO PARA FILEMOON
    _packed = """eval(function(p,a,c,k,e,d){while(c--)if(k[c])p=p.replace(new RegExp('\\b'+c.toString(a)+'\\b','g'),k[c]);return p}('m g=u("1e");g.aq({ap:[{ao:"2d://an.am.al.ak.aj/ai/ah/ag/af/ae.ad?t=ac&s=4m&e=ab&f=4n&aa=23&a9=a8&a7=a6&p="}],a5:"2d://a4.a3/18.a2",21:"27%",20:"27%",a1:"a0",9z:\'9y\',9x:"9w",9v:"9u",q:[],"9t":{9s:"%9r 4e%1b%9q%9p%9o%9n.5a%9m%9l%9k.59%22 4d%1b%34%22 9j%1b%34%22 9i%1b%34%22 4c%1b%9h%22 21%1b%9g%22 20%1b%9f%22 9e%5b%9d%9c%5b",9b:"2d://2x.5a/d/18/9a.59",99:[]},"98":{"97":"96","95":"94","93":1d},\'92\':{"90":"8z"},8y:{2u:"/8x/26/58-57.26?v=3.0.6",2i:"58-57"},8w:"8v",8u:"2d://2x.4l",8t:{},8s:1d,8r:[0.25,0.50,0.75,1,1.25,1.5,2]});m 31,33,8q;m 8p=0,8o=0;m g=u("1e");m 56=0,8n=0,8m=0,1p=0;m 2s=\'18\';$.8l({8k:{\'8j-8i\':\'4b-8h\'}});g.l(\'3j\',9(x){8(5>0&&x.1f>=5&&33!=1){33=1;$(\'11.8g\').8f(\'8e\')}8(x.1f>=1p+5||x.1f<1p){1p=x.1f;2o.8d(\'18\',2q.8c(1p),{8b:60*60*24})}});g.l(\'1k\',9(x){56=x.1f});g.l(\'1u\',9(x){32(x);$(\'.7-1a-46\').2r()});g.l(\'8a\',9(){$(\'11.54\').89();2o.2r(\'18\')});$(4r).l(\'z\',9(19){w 1n=19.88-$(\'#1e\').55().4g;w 1m=19.87-$(\'#1e\').55().2t;32(1n,1m)});9 32(1n,1m){$(\'11.54\').3k();8(31)1r;31=1;w 29=0;8(2y.86===1d){29=1}w 15="2c";8(/85|52/i.k(h.j)){15=/84|83|82/i.k(h.j)?"53/81":"53/52"}r 8(/51/i.k(h.j)){15="2c/51"}r 8(/4z/i.k(h.j)){15="2c/4z"}r 8(/80|7z 7y 7x/i.k(h.j)){15="2c/7w"}r 8(/4y/i.k(h.j)){15="4x/4y"}r 8(/4w/i.k(h.j)){15="4x/4w"}r 8(/7v|7u|7t|7s/i.k(h.j)){15="7r"}w 12="7q";8(/4v/i.k(h.j)){12="4v"}r 8(/30/i.k(h.j)&&!/2z|4s/i.k(h.j)){12="30"}r 8(/4u/i.k(h.j)&&!/30/i.k(h.j)){12="4u"}r 8(/4t/i.k(h.j)){12="4t"}r 8(/2z/i.k(h.j)){12="2z"}r 8(/4s/i.k(h.j)){12="7p"}r 8(/7o|7n/i.k(h.j)){12="7m 7l"}8(h.7k){12+=" (7j)"}w 4k=2y.7i;w 4j=2y.7h;w 2w="";w 2v="";7g{w 2b=4r.7f(\'2b\');w 1o=2b.4q(\'4p\')||2b.4q(\'7e-4p\');8(1o){w 2a=1o.7d(\'7c\');8(2a){2w=1o.4o(2a.7b)||"";2v=1o.4o(2a.7a)||""}}}79(e){}w 2u=\'/78?b=77&2s=18&76=4n-91-74-4m-73&72=1&71=&70=2x.4l&6z=0&29=\'+29+\'&1n=\'+1n+\'&1m=\'+1m+\'&6y=\'+28(15)+\'&6x=\'+28(12)+\'&6w=\'+4k+\'&6v=\'+4j+\'&6u=\'+28(2w)+\'&6t=\'+28(2v);$.3p(2u,9(4i){$(\'#6s\').6r(4i)});$(\'.7-c-6q-6p:6o("6n")\').z(9(e){4h();u().6m(0);u().6l(1d)});9 4h(){m $1z=$("<11 />").26({1f:"6k",21:"27%",20:"27%",4g:0,2t:0,4f:6j,6i:"6h(10%, 10%, 10%, 0.4)","2m-6g":"6f"});$("<6e />").26({21:"60%",20:"60%",4f:6d,"6c-2t":"6b"}).6a({\'4e\':\'/?b=69&2s=18\',\'4d\':\'0\',\'4c\':\'4b\'}).4a($1z);$1z.z(9(){$(68).2r();u().1u()});$1z.4a($(\'#1e\'))}u().1k(0)}9 47(2p){m 48=2q.49(2p/60);m 1l=2q.49(2p%60);8(1l<10){1l="0"+1l}1r 48+":"+1l}9 3o(a){a=47(a);$(\'#1e\').3i(`<11 1y="7-1a-46"><11 1y="7-1a-2m">67 66 ${a}</11><1x 1y="7-1a-14">65</1x><1x 1y="7-1a-3n">64</1x></11>`)}9 63(){m q=g.2f(45);44.43(q);8(q.1i>1){37(i=0;i<q.1i;i++){8(q[i].2i==45){44.43(\'!!=\'+i);g.35(i)}}}}g.l(\'62\',9(){u().2k(\'<1j 42="41://40.3z.3y/3x/1j" 3w:3v="3u" 3t=" 0 0 1 1" 3s="1.1"/>\',"61 10 3r",9(){u().1k(u().3q()+10)},"1t");$("11[14=1t]").3m().3l(\'.7-y-2n\');u().2k(\'<1j 42="41://40.3z.3y/3x/1j" 3w:3v="3u" 3t=" 0 0 1 1" 3s="1.1"/>\',"5z 10 3r",9(){m 1w=u().3q()-10;8(1w<0)1w=0;u().1k(1w)},"1s");m 1v=2o.3p(\'18\');8(1v!==5y){3o(1v);$(\'1h\').l(\'z\',\'.7-1a-14\',9(){g.1u();3a(9(){g.1k(1v)},5x)});$(\'1h\').l(\'z\',\'.7-1a-3n\',9(){u().1u()})}$("11[14=1s]").3m().3l(\'.7-y-2n\');$("11.7-y-2n").3k();$(\'.7-5w-3j\').3i($(\'.7-2m-5v\'));$(\'1h\').l(\'z\',\'.7-3h-y-3g .7-y[14="1t"]\',9(){$(\'.7-2j .7-y[14="1t"]\').3f(\'z\')});$(\'1h\').l(\'z\',\'.7-3h-y-3g .7-y[14="1s"]\',9(){$(\'.7-2j .7-y[14="1s"]\').3f(\'z\')})});9 2l(){}g.l(\'5u\',9(){2l()});g.l(\'5t\',9(){2l()});g.l("n",9(19){m q=g.2f();8(q.1i<2)1r;$(\'.7-c-5s-5r\').5q(9(){$(\'#7-c-o-n\').1q(\'7-c-o-1g\');$(\'.7-o-n\').17(\'13-16\',\'1c\')});g.2k("/5p/5o.1j","3c 3b",9(e){$(\'.7-3e\').5n(\'7-c-3d\');8($(\'.7-3e\').5m(\'7-c-3d\')){$(\'.7-c-n\').17(\'13-16\',\'1d\');$(\'.7-c-o-n \').17(\'13-16\',\'1d\');$(\'.7-c-o-n \').5l(\'7-c-o-1g\')}r{$(\'.7-c-n\').17(\'13-16\',\'1c\');$(\'.7-c-o-n \').17(\'13-16\',\'1c\');$(\'.7-c-o-n \').1q(\'7-c-o-1g\')}$(\'.7-2j .7-y:5k([13-5j="3c 3b"])\').l(\'z\',9(){$(\'.7-c-n\').17(\'13-16\',\'1c\');$(\'.7-c-o-n \').17(\'13-16\',\'1c\');$(\'.7-c-o-n \').1q(\'7-c-o-1g\')})},"5i");g.l("5h",9(19){2h.5g(\'2g\',19.q[19.5f].2i)});8(2h.39(\'2g\')){3a("38(2h.39(\'2g\'));",5e)}});m 2e;9 38(36){m q=g.2f();8(q.1i>1){37(i=0;i<q.1i;i++){8(q[i].5d==36){8(i==2e){1r}2e=i;g.35(i)}}}}$(\'1h\').l(\'z\',\'.7-y-c\',9(){$(\'.7-c-o-n \').1q(\'7-c-o-1g\');$(\'.7-14-5c.7-c-n\').17(\'13-16\',\'1c\')});',36,387,'|||||||jw|if|function|||settings||||videop|navigator||userAgent|test|on|var|audioTracks|submenu||tracks|else|||jwplayer||let||icon|click||div|browserName|aria|button|deviceType|expanded|attr|askmwd74zutw|event|resume|3D|false|true|vplayer|position|active|body|length|svg|seek|remainingSeconds|cy|cx|gl|lastt|removeClass|return|ff00|ff11|play|savedTime|tt|span|class|dd|height|width|||||css|100|encodeURIComponent|adb|debugInfo|canvas|Desktop|https|current_audio|getAudioTracks|default_audio|localStorage|name|controlbar|addButton|callMeMaybe|text|rewind|ls|seconds|Math|remove|file_code|top|url|gpuRenderer|gpuVendor|filemoon|window|Edge|Chrome|vvplay|doPlay|vvad|220|setCurrentAudioTrack|audio_iso|for|audio_set|getItem|setTimeout|Track|Audio|open|controls|trigger|container|display|append|time|hide|insertAfter|detach|reset|addResume|get|getPosition|sec|version|viewBox|preserve|space|xml|2000|org|w3|www|http|xmlns|log|console|track_name|box|formatTime|minutes|floor|appendTo|no|scrolling|frameborder|src|zIndex|left|showCCform|data|windowHeight|windowWidth|sx|1744001403|36021501|getParameter|webgl|getContext|document|OPR|Firefox|Safari|Brave|PlayStation|Console|Xbox|Linux||Windows|Android|Mobile|video_ad|offset|prevt|theme|jw8|mp4|to|3E|color|language|300|currentTrack|setItem|audioTrackChanged|dualSound|label|not|addClass|hasClass|toggleClass|dualy|images|mousedown|buttons|topbar|playAttemptFailed|beforePlay|countdown|slider|1500|null|Rewind||Forward|ready|set_audio_track|No|Yes|at|Resume|this|upload_srt|prop|50px|margin|1000001|iframe|center|align|rgba|background|1000000|absolute|pause|setCurrentCaptions|Upload|contains|item|content|html|fviews|gpur|gpuv|wh|ww|browser|device|vb|referer|prem|embed|142775dd56cd0b72141ec8fb0e5fa920|126||hash|view|dl|catch|UNMASKED_RENDERER_WEBGL|UNMASKED_VENDOR_WEBGL|WEBGL_debug_renderer_info|getExtension|experimental|createElement|try|innerHeight|innerWidth|Selenium|webdriver|Explorer|Internet|Trident|MSIE|Opera|Unknown|TV|NetCast|Web0S|Tizen|SmartTV|MacOS|X|OS|Mac|Macintosh|iOS|iPod|iPad|iPhone|Mobi|ZorDon|pageY|pageX|show|complete|ttl|round|set|slow|fadeIn|video_ad_fadein|cache|Cache|Content|headers|ajaxSetup|v2done|tott|vastdone2|vastdone1|vvbefore|playbackRates|playbackRateControls|cast|aboutlink|FileMoon|abouttext|assets|skin|1080p|3967||qualityLabels|preloadAds|insecure|vpaidmode|vast|client|advertising|sites|Longlegs1080|link|2Fiframe|3C|allowfullscreen|22360|22640|22no|marginheight|marginwidth|2FLonglegs1080|2Faskmwd74zutw|2Fe|2Ffilemoon|2F|3A|22https|3Ciframe|code|sharing|start|startparam|none|fullscreenOrientationLock|metadata|preload|uniform|stretching|jpg|me|videothumbs|image|5500|sp|35699|asn|srv|10800|Yder1y7TzoREibOSVcaosn2BI4A4jwm1WqAfo7dnVOE|m3u8|master|x1koqyijqbwa_x|07204|01|hls2|com|cdn255|waw05|rcr82|be7713|file|sources|setup'.split('|')))"""

    _unpacked = jsunpack.unpack(_packed)

    logger.info("check-04-todo: %s" % _unpacked)

    video = scrapertools.find_single_match(_unpacked, 'link:"(.*?)"')

    return video


def clean_title(title):
    logger.info()

    title = title.replace('\\u00e1', 'a').replace('\\u00c1', 'a').replace('\\u00e9', 'e').replace('\\u00ed', 'i').replace('\\u00f3', 'o').replace('\\u00fa', 'u')
    title = title.replace('\\u00f1', 'ñ').replace('\\u00bf', '¿').replace('\\u00a1', '¡').replace('\\u00ba', 'º')
    title = title.replace('\\u00eda', 'a').replace('\\u00f3n', 'o').replace('\\u00fal', 'u').replace('\\u00e0', 'a')

    title = title.replace('\\u2019', "'")

    title = title.replace('\\u00c0', "A").replace('\\u00c9', "E").replace('\\u010c0', "C")

    return title


def search(item, texto):
    logger.info()
    try:
       item.url = host + 'api/v1/search/' + texto.replace(" ", "+") + '?loader=searchPage'
       return list_all(item)
    except:
       import sys
       for line in sys.exc_info():
           logger.error("%s" % line)
       return []

