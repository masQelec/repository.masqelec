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
from collections import defaultdict
from functools import cmp_to_key

from six.moves.BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from six.moves.socketserver import ThreadingMixIn
from six.moves.urllib.parse import urlparse, urljoin, unquote, parse_qsl, quote_plus
from kodi_six import xbmc, xbmcvfs
import requests

from slyguy.log import log
from slyguy.constants import *
from slyguy.util import check_port, remove_file, get_kodi_string, set_kodi_string, cenc_version1to0
from slyguy.exceptions import Exit
from slyguy import settings, gui
from slyguy.language import _

from .constants import PROXY_CACHE, PROXY_CACHE_AHEAD, PROXY_CACHE_BEHIND

HOP_BY_HOP = ['connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade', 'x-uidh', 'host']
REMOVE_OUT_HEADERS = ['content-encoding', 'date', 'server', 'content-length']
REMOVE_OUT_HEADERS.extend(HOP_BY_HOP)

HOST = settings.get('proxy_host')
PORT = settings.getInt('proxy_port')

if not check_port(PORT):
    PORT = check_port(default=PORT)
    settings.setInt('proxy_port', PORT)

PROXY_PATH = 'http://{}:{}/'.format(HOST, PORT)

#ADDON_DEV = True
def devlog(msg):
    if ADDON_DEV:
        log.debug(msg)

class ResponseStream(object):
    def __init__(self, response=None, chunk_size=None):
        self._bytes = BytesIO()
        self._response = response
        self._iterator = response.iter_content(chunk_size) if response != None else iter([])
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

CODECS = {
    'avc': 'H.264',
    'hvc': 'H.265',
    'hev': 'H.265',
    'mp4v': 'MPEG-4',
    'mp4s': 'MPEG-4',
    'dvh': 'H.265 DV',
}

CODEC_RANKING = ['MPEG-4', 'H.264', 'H.265', 'H.265 DV']

PROXY_GLOBAL = {
    'last_quality': QUALITY_BEST,
    'session': {},
}

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
        data_path = None
        if '$POST' in url or '%24POST' in url:
            path = ''
            length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(length) if length else None
            if post_data:
                data_path = xbmc.translatePath('special://temp/proxy.post')
                with open(data_path, 'wb') as f:
                    f.write(post_data)

            param = quote_plus(data_path)
            url = url.replace('$POST', param).replace('%24POST', param)

        if '$HEADERS' in url or '%24HEADERS' in url:
            headers = {}
            for header in self.headers:
                headers[header.lower()] = self.headers[header]
            headers.pop('host', None)

            param = quote_plus(json.dumps(headers))
            url = url.replace('$HEADERS', param).replace('%24HEADERS', param)

        devlog('PLUGIN REQUEST: {}'.format(url))
        dirs, files = xbmcvfs.listdir(url)

        path = unquote(files[0])
        split = path.split('|')
        url = split[0]

        if data_path and os.path.realpath(path) != os.path.realpath(data_path):
            remove_file(data_path)

        if len(split) > 1:
            self._override_headers = dict(parse_qsl(u'{}'.format(split[1]), keep_blank_values=True))

        return url

    def _get_url(self):
        url = self.path.lstrip('/').strip('\\')

        session_id = self.headers.get('x-uidh', None)
        if session_id:
            self._session = PROXY_GLOBAL['session']

            if self._session.get('session_id') != session_id:
                PROXY_GLOBAL['session'] = self._session = {}

            try:
                proxy_data = json.loads(get_kodi_string('_slyguy_quality'))
                if proxy_data.get('session_id') == session_id:
                    self._session.update(proxy_data)
                    set_kodi_string('_slyguy_quality', '')
            except:
                pass
        else:
            self._session = {}

        if url.lower().startswith('plugin'):
            try:
                url = self._plugin_request(url)
            except Exception as e:
                log.debug('Plugin requsted failed')
                log.exception(e)

        return url

    def do_GET(self):
        url = self._get_url()
        devlog('GET IN: {}'.format(url))

        response = self._proxy_request('GET', url)
        if not self._session:
            self._output_response(response)
            return

        first_chunk = response.stream.read(self._chunk_size, start_from=0)

        if b'urn:mpeg:dash:schema' in first_chunk.lower():
            self._parse_dash(response)

        elif b'#extm3u' in first_chunk.lower():
            self._parse_m3u8(response)

        # elif not self._session.get('redirecting', False) and self._session.get('quality', None) is not None and self._session.get('selected_quality', None) is None:
        #     gui.error(_(_.QUALITY_PARSE_ERROR, error=_(_.QUALITY_HTTP_ERROR, code=response.status_code)))

        self._output_response(response)

    def _quality_select(self, qualities):
        def codec_rank(_codecs):
            highest = -1

            for codec in _codecs:
                for key in CODECS:
                    if codec.lower().startswith(key.lower()) and CODECS[key] in CODEC_RANKING:
                        rank = CODEC_RANKING.index(CODECS[key])
                        if not highest or rank > highest:
                            highest = rank

            return highest

        def compare(a, b):
            if a['resolution'] and b['resolution']:
                if int(a['resolution'].split('x')[0]) > int(b['resolution'].split('x')[0]):
                    return 1
                elif int(a['resolution'].split('x')[0]) < int(b['resolution'].split('x')[0]):
                    return -1

            # Same resolution - compare codecs
            a_rank = codec_rank(a['codecs'])
            b_rank = codec_rank(b['codecs'])

            if a_rank > b_rank:
                return 1
            elif a_rank < b_rank:
                return -1

            # Same codec rank - compare bandwidth
            if a['bandwidth'] and b['bandwidth']:
                if a['bandwidth'] > b['bandwidth']:
                    return 1
                elif a['bandwidth'] < b['bandwidth']:
                    return -1

            # Same bandwidth - they are equal (could compare framerate)
            return 0

        def _stream_label(stream):
            try: fps = _(_.QUALITY_FPS, fps=float(stream['frame_rate']))
            except: fps = ''

            codec_string = ''
            for codec in stream['codecs']:
                for key in CODECS:
                    if codec.lower().startswith(key.lower()):
                        codec_string += ' ' + CODECS[key]

            return _(_.QUALITY_BITRATE, bandwidth=int((stream['bandwidth']/10000.0))/100.00, resolution=stream['resolution'], fps=fps, codecs=codec_string.strip()).replace('  ', ' ')

        if self._session.get('selected_quality') is not None:
            if self._session['selected_quality'] in (QUALITY_DISABLED, QUALITY_SKIP):
                return None
            else:
                return qualities[self._session['selected_quality']]

        quality_compare = cmp_to_key(compare)

        quality = int(self._session.get('quality', QUALITY_DISABLED))
        streams = sorted(qualities, key=quality_compare, reverse=True)

        if not streams:
            quality = QUALITY_DISABLED
        elif len(streams) < 2:
            quality = QUALITY_BEST

        if quality == QUALITY_ASK:
            options = []
            options.append([QUALITY_BEST, _.QUALITY_BEST])

            for x in streams:
                options.append([x, _stream_label(x)])

            options.append([QUALITY_LOWEST, _.QUALITY_LOWEST])
            options.append([QUALITY_SKIP, _.QUALITY_SKIP])

            values = [x[0] for x in options]
            labels = [x[1] for x in options]

            default = -1
            if PROXY_GLOBAL['last_quality'] in values:
                default = values.index(PROXY_GLOBAL['last_quality'])
            else:
                options = [streams[-1]]
                for stream in streams:
                    if PROXY_GLOBAL['last_quality'] >= stream['bandwidth']:
                        options.append(stream)

                default = values.index(sorted(options, key=quality_compare, reverse=True)[0])

            index = gui.select(_.PLAYBACK_QUALITY, labels, preselect=default, autoclose=5000)
            if index < 0:
                raise Exit('Cancelled quality select')

            quality = values[index]
            if index != default:
                PROXY_GLOBAL['last_quality'] = quality['bandwidth'] if quality in qualities else quality

        if quality in (QUALITY_DISABLED, QUALITY_SKIP):
            quality = quality
        elif quality == QUALITY_BEST:
            quality = streams[0]
        elif quality == QUALITY_LOWEST:
            quality = streams[-1]
        elif quality not in streams:
            options = [streams[-1]]
            for stream in streams:
                if quality >= stream['bandwidth']:
                    options.append(stream)
            quality = sorted(options, key=quality_compare, reverse=True)[0]

        if quality in qualities:
            self._session['selected_quality'] = qualities.index(quality)
            return qualities[self._session['selected_quality']]
        else:
            self._session['selected_quality'] = quality
            return None

    def _parse_dash(self, response):
        if ADDON_DEV:
            root = parseString(response.stream.read())
            mpd = root.toprettyxml(encoding='utf-8')
            mpd = b"\n".join([ll.rstrip() for ll in mpd.splitlines() if ll.strip()])
            with open(xbmc.translatePath('special://temp/in.mpd'), 'wb') as f:
                f.write(mpd)

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
        if 'availabilityStartTime' in mpd.attributes.keys() and self._session.get('remove_availability_startTime'):
            mpd.removeAttribute('availabilityStartTime')
            log.debug('Removed availabilityStartTime')

        base_url_parents = []
        for elem in root.getElementsByTagName('BaseURL'):
            url = elem.firstChild.nodeValue

            ## Only keep the first baseurl for each parent
            if elem.parentNode in base_url_parents:
                log.debug('Non-1st BaseURL removed: {}'.format(url))
                elem.parentNode.removeChild(elem)
                continue

            if not url.startswith('http'):
                url = urljoin(response.url, url)

            elem.firstChild.nodeValue = PROXY_PATH + url
            base_url_parents.append(elem.parentNode)

        ## Live mpd needs non-last periods removed
        ## https://github.com/peak3d/inputstream.adaptive/issues/574
        if 'type' in mpd.attributes.keys() and mpd.getAttribute('type').lower() == 'dynamic':
            periods = [elem for elem in root.getElementsByTagName('Period')]

            # Keep last period
            if len(periods) > 1:
                periods.pop()
                for elem in periods:
                    elem.parentNode.removeChild(elem)
        #################################################

        ## SUPPORT NEW DOLBY FORMAT
        ## PR to fix in IA: https://github.com/peak3d/inputstream.adaptive/pull/466
        for elem in root.getElementsByTagName('AudioChannelConfiguration'):
            if elem.getAttribute('schemeIdUri') == 'tag:dolby.com,2014:dash:audio_channel_configuration:2011':
                elem.setAttribute('schemeIdUri', 'urn:dolby:dash:audio_channel_configuration:2011')
        ###########################

        # for elem in root.getElementsByTagName('ContentProtection'):
        #     if elem.getAttribute('schemeIdUri') not in ('urn:uuid:EDEF8BA9-79D6-4ACE-A3C8-27DCD51D21ED', 'urn:mpeg:dash:mp4protection:2011'):
        #         elem.parentNode.removeChild(elem)

        # for elem in root.getElementsByTagName('cenc:pssh'):
        #     old = elem.firstChild.nodeValue
        #     new = cenc_version1to0(old)
        #     if old != new:
        #         log.debug('cenc coverted from 1 to 0')
        #         elem.firstChild.nodeValue = new

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
        streams, all_streams, ids = [], [], []

        def get_base_url(node):
            if not node.parentNode:
                return None

            siblings = node.parentNode.getElementsByTagName('BaseURL')
            if siblings:
                return siblings[0]
            else:
                return get_base_url(node.parentNode)

        default_language = self._session.get('default_language', '')
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

                    ## will be fixed with https://github.com/xbmc/inputstream.adaptive/pull/602
                    if key == 'lang' and not (len(attrib[key]) == 2 or len(attrib[key]) == 3 or len(attrib[key]) > 3 and attrib[key][2] == '-'):
                        adap_set.setAttribute('lang', u'en-{}'.format(attrib[key]))

                for key in stream.attributes.keys():
                    attrib[key] = stream.getAttribute(key)

                if adapt_frame_rate and not stream.getAttribute('frameRate'):
                    stream.setAttribute('frameRate', adapt_frame_rate)

                if default_language and 'audio' in attrib.get('mimeType', '') and attrib.get('lang').lower() == default_language.lower() and adap_set not in lang_adap_sets:
                    lang_adap_sets.append(adap_set)

                bandwidth = 0
                if 'bandwidth' in attrib:
                    bandwidth = int(attrib['bandwidth'])
                    if bandwidth > highest_bandwidth:
                        highest_bandwidth = bandwidth

                if 'maxPlayoutRate' in attrib:
                    is_trick = True

                if 'video' in attrib.get('mimeType', ''):
                    is_video = True

                    if not is_trick:
                        resolution = ''
                        if 'width' in attrib and 'height' in attrib:
                            resolution = '{}x{}'.format(attrib['width'], attrib['height'])

                        frame_rate = ''
                        if 'frameRate'in attrib:
                            frame_rate = attrib['frameRate']
                            try:
                                if '/' in str(frame_rate):
                                    split = frame_rate.split('/')
                                    frame_rate = float(split[0]) / float(split[1])
                            except:
                                frame_rate = ''

                        codecs = [x for x in attrib.get('codecs', '').split(',') if x]
                        stream  = {'bandwidth': bandwidth, 'resolution': resolution, 'frame_rate': frame_rate, 'codecs': codecs, 'id': attrib['id'], 'elem': stream}
                        all_streams.append(stream)

                        if stream['id'] not in ids:
                            streams.append(stream)
                            ids.append(stream['id'])

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

        for elem in video_sets:
            elem[2].appendChild(elem[1])

        for elem in audio_sets:
            elem[2].appendChild(elem[1])

        # for elem in trick_sets:
        #     elem[2].appendChild(elem[1])
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
                else:
                    base_url = get_base_url(e)
                    if base_url and not base_url.firstChild.nodeValue.endswith('/'):
                        base_url.firstChild.nodeValue = base_url.firstChild.nodeValue + '/'

            process_attrib('initialization')
            process_attrib('media')

            ## FIX FOR BEIN MENA TO GET CORRECT SEGMENT
            ## PR TO FIX: https://github.com/peak3d/inputstream.adaptive/pull/564
            if 'presentationTimeOffset' in e.attributes.keys():
                e.removeAttribute('presentationTimeOffset')
            ###################

        selected = self._quality_select(streams)
        if selected:
            for stream in all_streams:
                if stream['id'] != selected['id']:
                    stream['elem'].parentNode.removeChild(stream['elem'])

        for adap_set in root.getElementsByTagName('AdaptationSet'):
            if not adap_set.getElementsByTagName('Representation'):
                adap_set.parentNode.removeChild(adap_set)

        mpd = root.toprettyxml(encoding='utf-8')
        mpd = b"\n".join([ll.rstrip() for ll in mpd.splitlines() if ll.strip()])

        if ADDON_DEV:
            with open(xbmc.translatePath('special://temp/out.mpd'), 'wb') as f:
                f.write(mpd)

        response.stream.set(mpd)

    def _parse_m3u8(self, response):
        m3u8 = response.stream.read().decode('utf8')

        is_master = False
        if '#EXT-X-STREAM-INF' in m3u8:
            is_master = True
            file_name = 'master'
        else:
            file_name = 'sub'

        if ADDON_DEV:
            _m3u8 = m3u8.encode('utf8')
            _m3u8 = b"\n".join([ll.rstrip() for ll in _m3u8.splitlines() if ll.strip()])
            with open(xbmc.translatePath('special://temp/'+file_name+'-in.m3u8'), 'wb') as f:
                f.write(_m3u8)

        if is_master:
            try:
                m3u8 = self._parse_m3u8_master(m3u8)
            except Exit:
                raise
            except Exception as e:
                log.exception(e)
                log.debug('failed to parse m3u8 master')

        base_url = urljoin(response.url, '/')

        ## FIX AES-128 streams with KEYFORMAT
        ## Fixed with this PR: https://github.com/peak3d/inputstream.adaptive/pull/461
        m3u8 = m3u8.replace('KEYFORMAT="identity"', 'KEYFORMAT=""')

        # URI="/.." fix (https://github.com/peak3d/inputstream.adaptive/issues/591)
        m3u8 = re.sub(r'URI="/', r'URI="{}'.format(base_url), m3u8, flags=re.I|re.M)

        ## Convert to proxy paths
        m3u8 = re.sub(r'^/', r'{}'.format(base_url), m3u8, flags=re.I|re.M)
        m3u8 = re.sub(r'(https?)://', r'{}\1://'.format(PROXY_PATH), m3u8, flags=re.I)

        m3u8 = m3u8.encode('utf8')
        m3u8 = b"\n".join([ll.rstrip() for ll in m3u8.splitlines() if ll.strip()])

        if ADDON_DEV:
            with open(xbmc.translatePath('special://temp/'+file_name+'-out.m3u8'), 'wb') as f:
                f.write(m3u8)

        response.stream.set(m3u8)

    def _parse_m3u8_master(self, m3u8):
        def _process_media(line):
            attribs = {}

            for key, value in re.findall('([\w-]+)="?([^",]*)[",$]?', line):
                attribs[key.upper()] = value.strip()

            return attribs

        audio_whitelist   = [x.strip().lower() for x in self._session.get('audio_whitelist', '').split(',') if x]
        subs_whitelist    = [x.strip().lower() for x in self._session.get('subs_whitelist', '').split(',') if x]
        subs_forced       = int(self._session.get('subs_forced', 1))
        subs_non_forced   = int(self._session.get('subs_non_forced', 1))
        audio_description = int(self._session.get('audio_description', 1))
        original_language = self._session.get('original_language', '').lower().strip()
        default_language  = self._session.get('default_language', '').lower().strip()

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

        lines = list(m3u8.splitlines())
        line1 = None
        streams, all_streams, urls = [], [], []
        for index, line in enumerate(lines):
            if not line.strip():
                continue

            if line.startswith('#EXT-X-STREAM-INF'):
                line1 = index
            elif line1 and not line.startswith('#'):
                attribs = _process_media(lines[line1])

                codecs     = [x for x in attribs.get('CODECS', '').split(',') if x]
                bandwidth  = int(attribs.get('BANDWIDTH') or 0)
                resolution = attribs.get('RESOLUTION', '')
                frame_rate = attribs.get('FRAME_RATE', '')

                url = line
                if '://' in url:
                    url = '/'+'/'.join(url.lower().split('://')[1].split('/')[1:])

                stream = {'bandwidth': int(bandwidth), 'resolution': resolution, 'frame_rate': frame_rate, 'codecs': codecs, 'url': url, 'lines': [line1, index]}
                all_streams.append(stream)

                if stream['url'] not in urls:
                    streams.append(stream)
                    urls.append(stream['url'])

                line1 = None

        selected = self._quality_select(streams)
        if selected:
            adjust = 0
            for stream in all_streams:
                if stream['url'] != selected['url']:
                    for index in stream['lines']:
                        lines.pop(index-adjust)
                        adjust += 1

        return '\n'.join(lines)

    def _proxy_request(self, method, url):
        self._session['redirecting'] = False

        if not url.startswith('http'):
            class Response(object):
                pass

            response = Response()
            response.status_code = 200
            response.headers = {}
            response.stream = ResponseStream()

            with open(url, 'rb') as f:
                response.stream.set(f.read())

            remove_file(url)
            return response

        parsed = urlparse(url)

        headers = {}
        for header in self.headers:
            if header.lower() not in HOP_BY_HOP:
                headers[header.lower()] = self.headers[header]

        headers.update(self._override_headers)

        length    = int(headers.get('content-length', 0))
        post_data = self.rfile.read(length) if length else None

        debug = self._session.get('debug_all') or self._session.get('debug_{}'.format(method.lower()))
        if post_data and debug:
            with open(xbmc.translatePath('special://temp/{}-request.txt').format(method.lower()), 'wb') as f:
                f.write(post_data)

        if not self._session.get('session'):
            self._session['session'] = requests.Session()
        else:
            self._session['session'].headers.clear()
        #    self._session['session'].cookies.clear()

        retries = 3
        # some reason we get connection errors every so often when using a session. something to do with the socket
        for i in range(retries):
            try:
                response = self._session['session'].request(method=method, url=url, headers=headers, data=post_data, allow_redirects=False, stream=True)
            except requests.ConnectionError as e:
                if 'Connection aborted' not in str(e) or i == retries-1:
                    log.exception(e)
                    raise
            except Exception as e:
                log.exception(e)
                raise
            else:
                break

        response.stream = ResponseStream(response, self._chunk_size)

        devlog('{} OUT: {} ({})'.format(method.upper(), url, response.status_code))

        headers = {}
        for header in response.headers:
            headers[header.lower()] = response.headers[header]

        if debug:
            with open(xbmc.translatePath('special://temp/{}-response.txt').format(method.lower()), 'wb') as f:
                f.write(response.stream.read())

        if 'location' in headers:
            self._session['redirecting'] = True
            if not headers['location'].lower().startswith('http'):
                headers['location'] = urljoin(url, headers['location'])

            headers['location'] = PROXY_PATH + headers['location']

        ## IA COOKIES ARE BROKEN - SO USE OWN SESSION FOR COOKIES
        ## FIX SET-COOKIE ##
        # if 'set-cookie' in headers:
        #     headers['set-cookie'] = headers['set-cookie'].split(';')[0]
        headers.pop('set-cookie', None)
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
        log.debug("Starting Proxy {}:{}".format(HOST, PORT))
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