#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    Provides: Globals, Settings, sleep, jsonRPC
'''
from __future__ import unicode_literals
from locale import getdefaultlocale
from kodi_six import xbmcaddon, xbmcgui
from kodi_six.utils import py2_decode
from sys import argv
import json
from .singleton import Singleton
from .l10n import *
from .configs import *

try:
    from xbmcvfs import translatePath
except ImportError:
    from xbmc import translatePath

# Usage:
#   gs = Globals()/Settings()
#   v = gs.attribute
#   v = gs.attribute.AttributeMemberFunction()


class Globals(Singleton):
    """ A singleton instance of globals accessible through dot notation """

    _globals = {
        'platform': 0
    }

    OS_WINDOWS = 1
    OS_LINUX = 2
    OS_OSX = 4
    OS_ANDROID = 8
    OS_LE = 16

    is_addon = 'inputstream.adaptive'
    na = 'not available'
    watchlist = 'watchlist'
    library = 'library'
    DBVersion = 1.4
    PayCol = 'FFE95E01'
    PrimeCol = 'FF00A8E0'
    tmdb = 'b34490c056f0dd9e3ec9af2167a731f4'  # b64decode('YjM0NDkwYzA1NmYwZGQ5ZTNlYzlhZjIxNjdhNzMxZjQ=')
    tvdb = '1D62F2F90030C444'  # b64decode('MUQ2MkYyRjkwMDMwQzQ0NA==')
    langID = {'movie': 30165, 'series': 30166, 'season': 30167, 'episode': 30173, 'tvshow': 30166, 'video': 30173, 'event': 30174}
    KodiVersion = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
    dtid_android = 'A43PXU4ZN2AL1'
    dtid_web = 'AOAGZA014O5RE'
    headers_android = {'Accept-Charset': 'utf-8', 'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 11; SHIELD Android TV RQ1A.210105.003)', 'X-Requested-With': 'com.amazon.avod.thirdpartyclient'}

    """ Allow the usage of dot notation for data inside the _globals dictionary, without explicit function call """
    def __getattr__(self, name): return self._globals[name]
    # def __setattr__(self, name, value): self._globals[name] = value
    # def __delattr__(self, name): self._globals.pop(name, None)

    def __init__(self):
        try:
            from urllib.parse import urlparse
        except ImportError:
            from urlparse import urlparse

        # argv[0] can contain the entire path, so we limit ourselves to the base url
        pid = urlparse(argv[0])
        self.pluginid = '{}://{}/'.format(pid.scheme, pid.netloc)
        self.pluginhandle = int(argv[1]) if (1 < len(argv)) and self.pluginid else -1

        self._globals['monitor'] = xbmc.Monitor()
        self._globals['addon'] = xbmcaddon.Addon()
        self._globals['dialog'] = xbmcgui.Dialog()
        # self._globals['dialogprogress'] = xbmcgui.DialogProgress()
        self._globals['hasExtRC'] = xbmc.getCondVisibility('System.HasAddon(script.chromium_remotecontrol)')

        self._globals['DATA_PATH'] = py2_decode(translatePath(self.addon.getAddonInfo('profile')))
        self._globals['CONFIG_PATH'] = OSPJoin(self._globals['DATA_PATH'], 'config')
        self._globals['LOG_PATH'] = OSPJoin(self._globals['DATA_PATH'], 'log')
        self._globals['HOME_PATH'] = py2_decode(translatePath('special://home'))
        self._globals['PLUGIN_PATH'] = py2_decode(self._globals['addon'].getAddonInfo('path'))

        # With main PATHs configured, we initialise the get/write path attributes
        # and generate/retrieve the device ID
        getConfig.configPath = self._globals['CONFIG_PATH']
        writeConfig.configPath = self._globals['CONFIG_PATH']

        if not xbmcvfs.exists(self._globals['LOG_PATH']):
            xbmcvfs.mkdirs(self._globals['LOG_PATH'])

        self._globals['__plugin__'] = self._globals['addon'].getAddonInfo('name')
        self._globals['__authors__'] = self._globals['addon'].getAddonInfo('author')
        self._globals['__credits__'] = ""
        self._globals['__version__'] = self._globals['addon'].getAddonInfo('version')

        # OS Detection
        if xbmc.getCondVisibility('system.platform.windows'):
            self._globals['platform'] |= self.OS_WINDOWS
        if xbmc.getCondVisibility('system.platform.linux'):
            self._globals['platform'] |= self.OS_LINUX
        if xbmc.getCondVisibility('system.platform.osx'):
            self._globals['platform'] |= self.OS_OSX
        if xbmc.getCondVisibility('system.platform.android'):
            self._globals['platform'] |= self.OS_ANDROID
        if (xbmcvfs.exists('/etc/os-release')) and ('libreelec' in xbmcvfs.File('/etc/os-release').read()):
            self._globals['platform'] |= self.OS_LE

        # Save the language code for HTTP requests and set the locale for l10n
        loc = getdefaultlocale()[0]
        userAcceptLanguages = 'en-gb{}, en;q=0.5'
        self._globals['userAcceptLanguages'] = userAcceptLanguages.format('') if not loc else '{}, {}'.format(loc.lower().replace('_', '-'), userAcceptLanguages.format(';q=0.75'))

        self._globals['CONTEXTMENU_MULTIUSER'] = [
            (getString(30130, self._globals['addon']).split('…')[0], 'RunPlugin({}?mode=LogIn)'.format(self.pluginid)),
            (getString(30131, self._globals['addon']).split('…')[0], 'RunPlugin({}?mode=removeUser)'.format(self.pluginid)),
            (getString(30132, self._globals['addon']), 'RunPlugin({}?mode=renameUser)'.format(self.pluginid))
        ]

    def InitialiseProvider(self, mid, burl, atv, pv, did):
        self._globals['MarketID'] = mid
        self._globals['BaseUrl'] = burl
        self._globals['ATVUrl'] = atv
        self._globals['UsePrimeVideo'] = pv
        self._globals['deviceID'] = did
        ds = 0  # int('0' + self._globals['addon'].getSetting('data_source'))

        if ds == 0:
            from .web_api import PrimeVideo
        elif ds == 1:
            from .android_api import PrimeVideo
        elif ds == 2:
            from .atv_api import PrimeVideo
        if 'pv' not in self._globals:
            self._globals['pv'] = PrimeVideo(self, Settings())


class Settings(Singleton):
    """ A singleton instance of various settings that could be needed to reload during runtime """

    def __init__(self):
        self._g = Globals()
        self._gs = self._g.addon.getSetting

    def __getattr__(self, name):
        if name in ['MOVIE_PATH', 'TV_SHOWS_PATH']:
            export = self._g.DATA_PATH
            if self._gs('enablelibraryfolder') == 'true':
                export = py2_decode(translatePath(self._gs('customlibraryfolder')))
            export = OSPJoin(export, 'Movies' if 'MOVIE_PATH' == name else 'TV')
            return export + '\\' if '\\' in export else export + '/'
        elif 'Language' == name:
            # Language settings
            l = jsonRPC('Settings.GetSettingValue', param={'setting': 'locale.audiolanguage'})
            l = xbmc.convertLanguage(l['value'], xbmc.ISO_639_1)
            l = l if l else xbmc.getLanguage(xbmc.ISO_639_1, False)
            return l if l else 'en'
        elif 'playMethod' == name: return int(self._gs('playmethod'))
        elif 'browser' == name: return int(self._gs('browser'))
        elif 'MaxResults' == name: return int(self._gs('items_perpage'))
        elif 'tvdb_art' == name: return self._gs('tvdb_art')
        elif 'tmdb_art' == name: return self._gs('tmdb_art')
        elif 'showfanart' == name: return self._gs('useshowfanart') == 'true'
        elif 'dispShowOnly' == name: return self._gs('disptvshow') == 'true'
        elif 'payCont' == name: return self._gs('paycont') == 'true'
        elif 'verbLog' == name: return self._gs('logging') == 'true'
        elif 'dumpJSON' == name: return self._gs('json_dump') == 'true'
        elif 'dumpJSONCollisions' == name: return self._gs('json_dump_collisions') == 'true'
        elif 'refineJSON' == name: return self._gs('json_dump_raw') == 'false'
        elif 'logHTTP' == name: return self._gs('log_http') == 'true'
        elif 'useIntRC' == name: return self._gs('remotectrl') == 'true'
        elif 'RMC_vol' == name: return self._gs('remote_vol') == 'true'
        elif 'ms_mov' == name: ms_mov = self._gs('mediasource_movie'); return ms_mov if ms_mov else 'Amazon Movies'
        elif 'ms_tv' == name: ms_tv = self._gs('mediasource_tv'); return ms_tv if ms_tv else 'Amazon TV'
        elif 'multiuser' == name: return self._gs('multiuser') == 'true'
        elif 'DefaultFanart' == name: return OSPJoin(self._g.PLUGIN_PATH, 'fanart.png')
        elif 'ThumbIcon' == name: return OSPJoin(self._g.PLUGIN_PATH, 'icon.png')
        elif 'NextIcon' == name: return OSPJoin(self._g.PLUGIN_PATH, 'resources', 'art', 'next.png')
        elif 'HomeIcon' == name: return OSPJoin(self._g.PLUGIN_PATH, 'resources', 'art', 'home.png')
        elif 'PrimeVideoEntitlement' == name: return OSPJoin(self._g.PLUGIN_PATH, 'resources', 'art', 'prime.png')
        elif 'wl_order' == name: return ['DATE_ADDED_DESC', 'TITLE_DESC', 'TITLE_ASC'][int('0' + self._gs('wl_order'))]
        elif 'verifySsl' == name: return self._gs('ssl_verif') == 'false'
        elif 'OfferGroup' == name: return '' if self.payCont else '&OfferGroups=B0043YVHMY'
        elif 'wl_export' == name: return self._gs('wl_export') == 'true'
        elif 'region' == name: return int(self._gs('region'))
        elif 'proxyaddress' == name: return getConfig('proxyaddress')
        elif 'subtitleStretch' == name: return self._gs('sub_stretch') == 'true'
        elif 'subtitleStretchFactor' == name:
            return [24 / 23.976, 23.976 / 24, 25 / 23.976, 23.976 / 25, 25.0 / 24.0, 24.0 / 25.0][int(self._gs('sub_stretch_factor'))]
        elif 'audioDescriptions' == name: return self._gs('audio_description') == 'true'
        elif 'removePosters' == name: return self._gs('pv_episode_thumbnails') == 'true'
        elif 'useEpiThumbs' == name: return self._gs('tld_episode_thumbnails') == 'true'
        elif 'bypassProxy' == name: return self._gs('proxy_mpdalter') == 'false'
        elif 'uhdAndroid' == name: return self._gs('uhd_android') == 'true'
        elif 'skip_scene' == name: return int('0' + self._gs('skip_scene'))
        elif 'pagination' == name: return {
            'all': self._gs('paginate_everything') == 'true',
            'watchlist': self._gs('paginate_watchlist') == 'true',
            'collections': self._gs('paginate_collections') == 'true',
            'search': self._gs('paginate_search') == 'true'
        }
        elif 'catalogCacheExpiry' == name:
            return [3600, 21600, 43200, 86400, 259200, 604800, 1296000, 2592000][int(self._gs('catalog_cache_expiry'))]
        elif 'profiles' == name: return self._gs('profiles') == 'true'
        elif 'show_pass' == name: return self._gs('show_pass') == 'true'
        elif 'data_source' == name: return 0  # int('0' + self._gs('data_source'))
        elif 'uhd' == name: return self._gs('enable_uhd') == 'true'
        elif 'show_recents' == name: return self._gs('show_recents') == 'true'


def jsonRPC(method, props='', param=None):
    """ Wrapper for Kodi's executeJSONRPC API """
    from .logging import Log
    rpc = {'jsonrpc': '2.0',
           'method': method,
           'params': {},
           'id': 1}

    if props:
        rpc['params']['properties'] = props.split(',')
    if param:
        rpc['params'].update(param)
        if 'playerid' in param.keys():
            res_pid = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Player.GetActivePlayers","id": 1}')
            pid = [i['playerid'] for i in json.loads(res_pid)['result'] if i['type'] == 'video']
            pid = pid[0] if pid else 0
            rpc['params']['playerid'] = pid

    res = json.loads(xbmc.executeJSONRPC(json.dumps(rpc)))
    if 'error' in res.keys():
        Log(res['error'])
        return res['error']

    result = res['result']
    return res['result'].get(props, res['result']) if type(result) == dict else result


def sleep(sec):
    from .logging import Log
    if Globals().monitor.waitForAbort(sec):
        import sys
        Log('Abort requested – exiting addon')
        sys.exit()


def key_exists(dictionary, *keys):
    """ Check if a nested list of keys exists """
    _p = dictionary
    for key in keys:
        try:
            _p = _p[key]
        except:
            return False
    return True


def return_item(dictionary, *keys):
    """ Returns an item nested in the dictionary, or the dictionary itself """
    _p = dictionary
    for key in keys:
        try:
            _p = _p[key]
        except:
            return dictionary
    return _p


def return_value(dictionary, *keys):
    """ Returns an value nested in the dictionary, or the dictionary itself """
    _p = dictionary
    for key in keys:
        try:
            _p = _p[key]
        except:
            return _p
    return _p


def findKey(key, obj):
    if key in obj.keys():
        return obj[key]
    for v in obj.values():
        if isinstance(v, dict):
            res = findKey(key, v)
            if res: return res
        elif isinstance(v, list):
            for d in v:
                if isinstance(d, dict):
                    res = findKey(key, d)
                    if res:
                        return res
    return []
