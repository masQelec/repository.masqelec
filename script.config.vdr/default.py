################################################################################
#      This file is part of OpenELEC - http://www.openelec.tv
#      Copyright (C) 2015 Lutz Fiebach (lufie@openelec.tv)
#
#      *** Big thanks to the Wetek Team (http://www.wetek.com) ***
#      ***             for making this tool possible           ***
#
#  This program is dual-licensed; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with OpenELEC; see the file COPYING.  If not, see
#  <http://www.gnu.org/licenses/>.
#
#  Alternatively, you can license this library under a commercial license,
#  please contact OpenELEC Licensing for more information.
#
#  For more information contact:
#  OpenELEC Licensing  <license@openelec.tv>  http://www.openelec.tv
################################################################################
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcaddon

__author__ = 'LuFi'
__scriptid__ = 'script.config.vdr'
__vdrscriptid__ = 'service.multimedia.vdr-addon'
__addon__ = xbmcaddon.Addon(id=__scriptid__)
__cwd__ = __addon__.getAddonInfo('path')

try:
    __vrdaddon__ = xbmcaddon.Addon(id=__vdrscriptid__)
except Exception, e:
    xbmc.executebuiltin('Notification(VDR Configuration, VDR Plugin not found, 5000, "")')
    quit()

def _(code):
    if isinstance(code, int):
        return __addon__.getLocalizedString(code)
    else:
        return code

if __name__ == '__main__':
    lObjSelectDialog = xbmcgui.Dialog()
    lIntResult = lObjSelectDialog.select(_(32300), [_(32301), _(32302)])    
    if lIntResult == 0:
        import scan
    elif lIntResult == 1:
        import diseqc
    else:
        pass
