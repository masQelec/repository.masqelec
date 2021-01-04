import threading
import os
import shutil
import re
import uuid
import time
import base64
import json

from io import BytesIO, SEEK_END
from xml.dom.minidom import parseString
from collections import defaultdict, OrderedDict

from six.moves.BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from six.moves.socketserver import ThreadingMixIn
from six.moves.urllib.parse import urlparse, urljoin, unquote, parse_qsl, quote_plus
from kodi_six import xbmc, xbmcvfs
from requests import Session

from slyguy.log import log
from slyguy.constants import ADDON_DEV, ADDON_PROFILE
from slyguy.util import hash_6
from slyguy import settings

from .constants import PROXY_CACHE, PROXY_CACHE_AHEAD, PROXY_CACHE_BEHIND

sessions = OrderedDict()

REMOVE_OUT_HEADERS = ['connection', 'transfer-encoding', 'content-encoding', 'date', 'server', 'content-length', 'set-cookie']

HOST = settings.get('proxy_host')
PORT = settings.getInt('proxy_port')
PROXY_PATH = 'http://{}:{}/'.format(HOST, PORT)

def devlog(msg):
    if ADDON_DEV:
        log.debug(msg)

class ResponseStream(object):
    def __init__(self, response=None, chunk_size=None):
        self._bytes = BytesIO()
        self._response = response
        self._iterator = response.iter_content(chunk_size) if response else []
        self._chunk_size = chunk_size

    def _load_until(self, goal_position=None):
        current_position = self._bytes.seek(0, SEEK_END)

        while goal_position is None or current_position < goal_position:
            try:
                current_position = self._bytes.write(next(self._iterator))
            except StopIteration:
                break

    @property
    def size(self):
        return self._size

    def tell(self):
        return self._bytes.tell()

    def read(self, size=None, start_from=None):
        if size is None:
            left_off_at = start_from or 0
            goal_position = None
        else:
            left_off_at = start_from or self._bytes.tell()
            goal_position = left_off_at + size

        self._load_until(goal_position)
        self._bytes.seek(left_off_at)

        return self._bytes.read(size)

    def set(self, _bytes):
        self._bytes = BytesIO(_bytes)

    def iter_content(self):
        self._bytes.seek(0)

        while True:
            chunk = self._bytes.read(self._chunk_size)
            if not chunk:
                break

            yield chunk

        for chunk in self._iterator:
            yield chunk

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self._chunk_size = 4096
        self._override_headers = {}
        try:
            BaseHTTPRequestHandler.__init__(self, request, client_address, server)
        except (IOError, OSError) as e:
            pass

    def log_message(self, format, *args):
        return

    def setup(self):
        BaseHTTPRequestHandler.setup(self)
        self.request.settimeout(5)

    def _plugin_request(self, url):
        if '$POST' in url or '%24POST' in url:
            path = ''
            length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(length) if length else None
            if post_data:
                path = xbmc.translatePath('special://temp/{}'.format(hash_6(url)))
                with open(path, 'wb') as f:
                    f.write(post_data)

            param = quote_plus(path)
            url = url.replace('$POST', param).replace('%24POST', param)

        if '$HEADERS' in url or '%24HEADERS' in url:
            headers = {}
            for header in self.headers:
                key = header.lower()
                if not key.startswith('_proxy'):
                    headers[key] = self.headers[header]
            headers.pop('host', None)

            param = quote_plus(json.dumps(headers))
            url = url.replace('$HEADERS', param).replace('%24HEADERS', param)

        devlog('PLUGIN REQUEST: {}'.format(url))
        dirs, files = xbmcvfs.listdir(url)

        path = unquote(files[0])
        split = path.split('|')
        url = split[0]

        if len(split) > 1:
            self._override_headers = dict(parse_qsl(u'{}'.format(split[1]), keep_blank_values=True))

        return url

    def _get_url(self):
        url = self.path.lstrip('/').strip('\\')

        if url.lower().startswith('plugin'):
            url = self._plugin_request(url)

        return url

    def do_GET(self):
        url = self._get_url()
        devlog('GET IN: {}'.format(url))

        response = self._proxy_request('GET', url)
        if not response.ok:
            self._output_response(response)
            return

        first_chunk = response.stream.read(self._chunk_size, start_from=0)

        if b'urn:mpeg:dash:schema' in first_chunk.lower():
            self._parse_dash(response)

        elif b'#extm3u' in first_chunk.lower():
            self._parse_m3u8(response)

        self._output_response(response)

    def _parse_dash(self, response):
        data = response.stream.read().decode('utf8')

        data = data.replace('_xmlns:cenc', 'xmlns:cenc')
        data = data.replace('_:default_KID', 'cenc:default_KID')
        data = data.replace('<pssh', '<cenc:pssh')
        data = data.replace('</pssh>', '</cenc:pssh>')

        try:
            root = parseString(data.encode('utf8'))
        except Exception as e:
            log.debug("Proxy: Failed to parse MPD")
            log.exception(e)
            return self._output_response(response)

        mpd = root.getElementsByTagName("MPD")[0]

        ## Set publishtime to utctime
        utc_time = mpd.getElementsByTagName("UTCTiming")
        if utc_time:
            value = utc_time[0].getAttribute('value')
            mpd.setAttribute('publishTime', value)
            log.debug('publishTime updated to UTCTiming ({})'.format(value))

        for elem in mpd.getElementsByTagName("SupplementalProperty"):
            if elem.getAttribute('schemeIdUri') == 'urn:scte:dash:utc-time':
                value = elem.getAttribute('value')
                mpd.setAttribute('publishTime', value)
                log.debug('publishTime updated to urn:scte:dash:utc-time ({})'.format(value))
                break

        ## FIXED in IA 2.4.6
        ## Commit: https://github.com/peak3d/inputstream.adaptive/commit/dc7b42783d18c65ebcf205a4979a1c9ea6b825e7
        if self.headers.get('_proxy_addon_id') in ('plugin.video.skygo.nz', 'plugin.video.optus.sport') and 'availabilityStartTime' in mpd.attributes.keys():
            mpd.removeAttribute('availabilityStartTime')
            log.debug('Removed availabilityStartTime')

        base_url_nodes = []
        for node in mpd.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if node.localName == 'BaseURL':
                    url = node.firstChild.nodeValue

                    if not url.startswith('http'):
                        url = urljoin(response.url, url)

                    node.firstChild.nodeValue = PROXY_PATH + url
                    base_url_nodes.append(node)

        # Keep first base_url node
        if base_url_nodes:
            base_url_nodes.pop(0)
            for e in base_url_nodes:
                e.parentNode.removeChild(e)
        ####################

        ## Live mpd needs non-last periods removed
        ## https://github.com/peak3d/inputstream.adaptive/issues/574
        if 'type' in mpd.attributes.keys() and mpd.getAttribute('type').lower() == 'dynamic':
            periods = [elem for elem in root.getElementsByTagName('Period')]

            # Keep last period
            if len(periods) > 1:
                periods.pop()
                for e in periods:
                    e.parentNode.removeChild(e)
        #################################################

        ## SUPPORT NEW DOLBY FORMAT
        ## PR to fix in IA: https://github.com/peak3d/inputstream.adaptive/pull/466
        for elem in root.getElementsByTagName('AudioChannelConfiguration'):
            if elem.getAttribute('schemeIdUri') == 'tag:dolby.com,2014:dash:audio_channel_configuration:2011':
                elem.setAttribute('schemeIdUri', 'urn:dolby:dash:audio_channel_configuration:2011')
        ###########################

        ## Make sure Representation are last in adaptionset
        for elem in root.getElementsByTagName('Representation'):
            parent = elem.parentNode
            parent.removeChild(elem)
            parent.appendChild(elem)

        ## SORT ADAPTION SETS BY BITRATE ##
        video_sets = []
        audio_sets = []
        trick_sets = []
        lang_adap_sets = []

        default_language = self.headers.get('_proxy_default_language', '')

        for adap_set in root.getElementsByTagName('AdaptationSet'):
            highest_bandwidth = 0
            is_video = False
            is_trick = False

            adapt_frame_rate = adap_set.getAttribute('frameRate')
            if adapt_frame_rate and '/' not in adapt_frame_rate:
                adapt_frame_rate = None

            if adapt_frame_rate:
                adap_set.removeAttribute('frameRate')
                log.debug('fpsScale MPD fix')

            for stream in adap_set.getElementsByTagName("Representation"):
                attrib = {}

                for key in adap_set.attributes.keys():
                    attrib[key] = adap_set.getAttribute(key)

                for key in stream.attributes.keys():
                    attrib[key] = stream.getAttribute(key)

                if adapt_frame_rate and not stream.getAttribute('frameRate'):
                    stream.setAttribute('frameRate', adapt_frame_rate)

                if default_language and 'audio' in attrib.get('mimeType', '') and attrib.get('lang') == default_language and adap_set not in lang_adap_sets:
                    lang_adap_sets.append(adap_set)

                if 'bandwidth' in attrib:
                    bandwidth = int(attrib['bandwidth'])
                    if bandwidth > highest_bandwidth:
                        highest_bandwidth = bandwidth

                if 'video' in attrib.get('mimeType', ''):
                    is_video = True

                if 'maxPlayoutRate' in attrib:
                    is_trick = True

            parent = adap_set.parentNode
            parent.removeChild(adap_set)

            if is_trick:
                trick_sets.append([highest_bandwidth, adap_set, parent])
            elif is_video:
                video_sets.append([highest_bandwidth, adap_set, parent])
            else:
                audio_sets.append([highest_bandwidth, adap_set, parent])

        video_sets.sort(key=lambda  x: x[0], reverse=True)
        audio_sets.sort(key=lambda  x: x[0], reverse=True)
        trick_sets.sort(key=lambda  x: x[0], reverse=True)

        select_set = int(self.headers.get('_proxy_adaption_set', 0))
        if select_set > 0 and len(video_sets) > select_set:
            video_sets.insert(0, video_sets.pop(select_set))
            log.debug('Proxy: AdaptationSet #{} moved to top'.format(select_set))

        for elem in video_sets:
            elem[2].appendChild(elem[1])

        for elem in audio_sets:
            elem[2].appendChild(elem[1])

        for elem in trick_sets:
            elem[2].appendChild(elem[1])
        ##################

        ## Set default languae
        if lang_adap_sets:
            for elem in root.getElementsByTagName('Role'):
                if elem.getAttribute('schemeIdUri') == 'urn:mpeg:dash:role:2011':
                    elem.parentNode.removeChild(elem)

            for adap_set in lang_adap_sets:
                elem = root.createElement('Role')
                elem.setAttribute('schemeIdUri', 'urn:mpeg:dash:role:2011')
                elem.setAttribute('value', 'main')
                adap_set.appendChild(elem)
                log.debug('default language set to: {}'.format(default_language))
        ####

        elems = root.getElementsByTagName('SegmentTemplate')
        elems.extend(root.getElementsByTagName('SegmentURL'))

        for e in elems:
            def process_attrib(attrib):
                if attrib not in e.attributes.keys():
                    return

                url = e.getAttribute(attrib)

                if url.startswith('http'):
                    e.setAttribute(attrib, PROXY_PATH + url)

            process_attrib('initialization')
            process_attrib('media')

            ## FIX FOR BEIN MENA TO GET CORRECT SEGMENT
            ## PR TO FIX: https://github.com/peak3d/inputstream.adaptive/pull/564
            if 'presentationTimeOffset' in e.attributes.keys():
                e.removeAttribute('presentationTimeOffset')
            ###################

        if ADDON_DEV:
            text = root.toprettyxml(encoding='utf-8')
            text = b"\n".join([ll.rstrip() for ll in text.splitlines() if ll.strip()])
            with open(xbmc.translatePath('special://temp/proxy.mpd'), 'wb') as f:
                f.write(text)

        response.stream.set(root.toxml(encoding='utf-8'))

    def _parse_m3u8(self, response):
        m3u8 = response.stream.read().decode('utf8')

        ## FIX AES-128 streams with KEYFORMAT
        ## Fixed with this PR: https://github.com/peak3d/inputstream.adaptive/pull/461
        m3u8 = m3u8.replace('KEYFORMAT="identity"', 'KEYFORMAT=""')

        if '#EXT-X-STREAM-INF' in m3u8:
            file_name = 'proxy-master.m3u8'
            try:
                m3u8 = self._parse_m3u8_master(m3u8)
            except Exception as e:
                log.exception(e)
                log.debug('failed to parse m3u8 master')
        else:
            file_name = 'proxy-sub.m3u8'

        m3u8 = re.sub(r'^/', r'{}'.format(urljoin(response.url, '/')), m3u8, flags=re.I|re.M)
        m3u8 = re.sub(r'(https?)://', r'{}\1://'.format(PROXY_PATH), m3u8, flags=re.I)

        if ADDON_DEV:
            with open(xbmc.translatePath('special://temp/'+file_name), 'wb') as f:
                f.write(m3u8.encode('utf8'))

        response.stream.set(m3u8.encode('utf8'))

    def _parse_m3u8_master(self, m3u8):
        def _process_media(line):
            attribs = {}

            for key, value in re.findall('([\w-]+)="?([^",]*)[",$]?', line):
                attribs[key.upper()] = value.strip()

            return attribs

        audio_whitelist   = [x.strip().lower() for x in self.headers.get('_proxy_audio_whitelist', '').split(',') if x]
        subs_whitelist    = [x.strip().lower() for x in self.headers.get('_proxy_subs_whitelist', '').split(',') if x]
        subs_forced       = int(self.headers.get('_proxy_subs_forced', 1))
        subs_non_forced   = int(self.headers.get('_proxy_subs_non_forced', 1))
        audio_description = int(self.headers.get('_proxy_audio_description', 1))
        original_language = self.headers.get('_proxy_original_language', '').lower().strip()
        default_language  = self.headers.get('_proxy_default_language', '').lower().strip()

        if original_language and not default_language:
            default_language = original_language

        if audio_whitelist:
            audio_whitelist.append(original_language)
            audio_whitelist.append(default_language)

        def _lang_allowed(lang, lang_list):
            for _lang in lang_list:
                if not _lang:
                    continue

                if lang.startswith(_lang):
                    return True

            return False

        default_groups = []
        groups = defaultdict(list)
        for line in m3u8.splitlines():
            if not line.startswith('#EXT-X-MEDIA'):
                continue

            attribs = _process_media(line)
            if not attribs:
                continue

            if audio_whitelist and attribs.get('TYPE') == 'AUDIO' and 'LANGUAGE' in attribs and not _lang_allowed(attribs['LANGUAGE'].lower().strip(), audio_whitelist):
                m3u8 = m3u8.replace(line, '')
                continue

            if subs_whitelist and attribs.get('TYPE') == 'SUBTITLES' and 'LANGUAGE' in attribs and not _lang_allowed(attribs['LANGUAGE'].lower().strip(), subs_whitelist):
                m3u8 = m3u8.replace(line, '')
                continue

            if not subs_forced and attribs.get('TYPE') == 'SUBTITLES' and attribs.get('FORCED','').upper() == 'YES':
                m3u8 = m3u8.replace(line, '')
                continue

            if not subs_non_forced and attribs.get('TYPE') == 'SUBTITLES' and attribs.get('FORCED','').upper() != 'YES':
                m3u8 = m3u8.replace(line, '')
                continue

            if not audio_description and attribs.get('TYPE') == 'AUDIO' and attribs.get('CHARACTERISTICS','').lower() == 'public.accessibility.describes-video':
                m3u8 = m3u8.replace(line, '')
                continue

            groups[attribs['GROUP-ID']].append([attribs, line])
            if attribs.get('DEFAULT') == 'YES' and attribs['GROUP-ID'] not in default_groups:
                default_groups.append(attribs['GROUP-ID'])

        if default_language:
            for group_id in groups:
                if group_id in default_groups:
                    continue

                languages = []
                for group in groups[group_id]:
                    attribs, line = group

                    attribs['AUTOSELECT'] = 'NO'
                    attribs['DEFAULT']    = 'NO'

                    if attribs['LANGUAGE'] not in languages or attribs.get('TYPE') == 'SUBTITLES':
                        attribs['AUTOSELECT'] = 'YES'

                        if attribs['LANGUAGE'].lower().strip().startswith(default_language):
                            attribs['DEFAULT'] = 'YES'

                        languages.append(attribs['LANGUAGE'])

        for group_id in groups:
            for group in groups[group_id]:
                attribs, line = group

                # FIX es-ES > es fr-FR > fr languages #
                if 'LANGUAGE' in attribs:
                    split = attribs['LANGUAGE'].split('-')
                    if len(split) > 1 and split[1].lower() == split[0].lower():
                        attribs['LANGUAGE'] = split[0]
                #############################

                new_line = '#EXT-X-MEDIA:' if attribs else ''
                for key in attribs:
                    new_line += u'{}="{}",'.format(key, attribs[key])

                m3u8 = m3u8.replace(line, new_line.rstrip(','))

        return m3u8

    def _proxy_request(self, method, url):
        if not url.startswith('http'):
            class Response(object):
                pass

            response = Response()
            response.status_code = 200
            response.headers = {}
            response.stream = ResponseStream()

            with open(url, 'rb') as f:
                response.stream.set(f.read())

            os.remove(url)
            return response

        parsed = urlparse(url)

        headers = {}
        for header in self.headers:
            key = header.lower()
            if not key.startswith('_proxy'):
                headers[key] = self.headers[header]

        headers['host'] = parsed.hostname
        headers.update(self._override_headers)

        length    = int(headers.get('content-length', 0))
        post_data = self.rfile.read(length) if length else None

        debug = self.headers.get('_proxy_debug_all') or self.headers.get('_proxy_debug_{}'.format(method.lower()))
        _time  = int(time.time())
        if post_data and debug:
            with open(os.path.join(ADDON_PROFILE, '{}-{}-request.txt'.format(method.lower(), _time)), 'wb') as f:
                f.write(post_data)

        session = sessions.get(headers['host'], Session())
        sessions[headers['host']] = session

        if len(sessions) > 5:
            sessions.popitem(last=False)

        # session.cookies.clear()
        session.headers.clear()

        response = session.request(method=method, url=url, headers=headers, data=post_data, allow_redirects=False, stream=True)
        response.stream = ResponseStream(response, self._chunk_size)

        devlog('{} OUT: {} ({})'.format(method.upper(), url, response.status_code))

        headers = {}
        for header in response.headers:
            headers[header.lower()] = response.headers[header]

        if debug:
            with open(os.path.join(ADDON_PROFILE, '{}-{}-response.txt'.format(method.lower(), _time)), 'wb') as f:
                f.write(response.stream.read())

        if 'location' in headers:
            if not headers['location'].lower().startswith('http'):
                headers['location'] = urljoin(url, headers['location'])

            headers['location']  = PROXY_PATH + headers['location']

        ## IA COOKIES ARE BROKEN - SO USE OWN SESSION FOR COOKIES
        ## FIX SET-COOKIE ##
        # if 'set-cookie' in headers:
        #     headers['set-cookie'] = headers['set-cookie'].split(';')[0]

        response.headers = headers

        return response

    def _output_headers(self, response):
        self.send_response(response.status_code)

        for header in REMOVE_OUT_HEADERS:
            response.headers.pop(header, None)

        for d in list(response.headers.items()):
            self.send_header(d[0], d[1])

        self.end_headers()

    def _output_response(self, response):
        self._output_headers(response)

        for chunk in response.stream.iter_content():
            try:
                self.wfile.write(chunk)
            except Exception as e:
                break

    def do_HEAD(self):
        url = self._get_url()
        devlog('HEAD IN: {}'.format(url))
        response = self._proxy_request('HEAD', url)
        self._output_response(response)

    def do_POST(self):
        url = self._get_url()
        devlog('POST IN: {}'.format(url))
        response = self._proxy_request('POST', url)
        self._output_response(response)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class Proxy(object):
    def start(self):
        self._server = ThreadedHTTPServer((HOST, PORT), RequestHandler)
        self._httpd_thread = threading.Thread(target=self._server.serve_forever)
        self._httpd_thread.start()
        log.info("Proxy bound to {}:{}".format(HOST, PORT))

    def stop(self):
        self._server.shutdown()
        self._server.server_close()
        self._server.socket.close()
        self._httpd_thread.join()
        log.debug("Proxy Server: Stopped")