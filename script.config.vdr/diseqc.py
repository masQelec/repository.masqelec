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

import os
import sys
import math
import xbmc
import json
import urllib
import urllib2
import xbmcgui
import xbmcaddon
import xbmcplugin

import httplib
import rotor_calc

XBMC_USER_HOME = os.environ.get('XBMC_USER_HOME', '/storage/.kodi')

__author__ = 'LuFi'
__scriptid__ = 'script.config.vdr'
__vdrscriptid__ = 'service.multimedia.vdr-addon'
__addon__ = xbmcaddon.Addon(id=__scriptid__)
__cwd__ = __addon__.getAddonInfo('path')
__usrcfg__ = '%s/userdata/addon_data/%s/latest.cfg' % (XBMC_USER_HOME, __scriptid__)

try:
    __vrdaddon__ = xbmcaddon.Addon(id=__vdrscriptid__)
except Exception, e:
    xbmc.executebuiltin('Notification(VDR Configuration, VDR Plugin not found, 5000, "")')
    quit()
    
gWinMain = None

def _(code):
    if isinstance(code, int):
        return __addon__.getLocalizedString(code)
    else:
        return code
        
class cWinDiSEqC(xbmcgui.WindowXMLDialog):
    
    lDicLnb = {
        "state":"0",
        "sat":'none',
        "LnbFrequLo":"0",
        "LnbFrequHi":"0",
        "LnbSLOF":"0",
        "dual":"0",
        "pol":"0",
        "type":"none",
        "port1":"",
        "port1_version":"",
        "port2":"",
        "port2_version":"",        
        "tone_on":"",
        "tone_off":"",
        "wait":"",
        "repeat":"",
        "position":"",
        "commands":{},
        "adapter":""
    }
    
    lDicDiSEqC = {
        "modes":{
            "Tune-22k":{
                "name":32070, "ports":2,
                "order":0, "info":32117,
                "mode":"1"
            },
            "Toneburst":{
                "name":32071, "ports":2,
                "order":1, "info":32118,
                "mode":"2"                
            },
            "DiSEqC-1.0":{
                "name":32072, "ports":4,
                "order":2, "info":32119,
                "mode":"3"                
            },
            "DiSEqC-1.1":{
                "name":32073, "ports":16,
                "order":3, "info":32120, 
                "mode":"4"               
            },
            "DiSEqC-1.2":{
                "name":32074, "ports":16,
                "order":4, "info":32121,
                "mode":"5"                
            },
            "User-defined":{
                "name":32075, "ports":64,
                "order":5, "info":32122,
                "mode":"6"                
            },
            "Disabled":{
                "name":32076, "ports":0,
                "order":6, "info":32147,
                "mode":"0"                
            },
        },
        "lnbtype":{
            "5150":{
                "name":32100,
                "LnbFrequLo":"0",
                "LnbFrequHi":"5150",
                "LnbSLOF":"11700",
                "dual":"0",                  
            },
            "5750":{
                "name":32101,
                "LnbFrequLo":"0",
                "LnbFrequHi":"5750",
                "LnbSLOF":"11700",
                "dual":"0",                  
            },            
            "9750":{
                "name":32102,
                "LnbFrequLo":"0",
                "LnbFrequHi":"9750",
                "LnbSLOF":"11700",
                "dual":"0",                  
            },   
            "10600":{
                "name":32103,
                "LnbFrequLo":"0",
                "LnbFrequHi":"10600",
                "LnbSLOF":"11700",
                "dual":"0",                  
            },
            "10750":{
                "name":32104,
                "LnbFrequLo":"0",
                "LnbFrequHi":"10750",
                "LnbSLOF":"11700",
                "dual":"0",                  
            },            
            "11250":{
                "name":32105,
                "LnbFrequLo":"0",
                "LnbFrequHi":"11250",
                "LnbSLOF":"11700",
                "dual":"0",                  
            }, 
            "11300":{
                "name":32106,
                "LnbFrequLo":"0",
                "LnbFrequHi":"11300",
                "LnbSLOF":"11700",
                "dual":"0",                  
            },
            "9750/10600":{
                "name":32107,
                "LnbFrequLo":"9750",
                "LnbFrequHi":"10600",
                "LnbSLOF":"11700",
                "dual":"1",
            },            
            "9750/10750":{
                "name":32108,
                "LnbFrequLo":"9750",
                "LnbFrequHi":"10750",
                "LnbSLOF":"11700",
                "dual":"1",                
            },
            "custom":{
                "name":32109,
                "LnbFrequLo":"9750",
                "LnbFrequHi":"10750",
                "LnbSLOF":"11700",
                "dual":"1",                
            },            
            "none":{
                "name":32127
            }            
        }       
    }
    
    lIntSelectedLnb = 0
    lIntSelectedConfig = 0    
    lIntMenuDepth = 0
    lStrDiSEqCMode = None
    lDicDiSEqCLNBs = {}
    lDicSatellites = {'none':{'name':_(32127),'index':0}}
    
    def __init__(self, *args, **kwargs):
        xbmc.executebuiltin('dialog.close(10140)')
        self.lStrDiSEqCMode = self.lDicDiSEqC['modes']['Disabled']
        self.fncLoadSatelites()
        
    def onInit(self):
        self.fncLoadConfig()
        self.setFocusId(1050)
        self.getControl(1050).setLabel(_(self.lStrDiSEqCMode['name']))
                
    def onAction(self, lIntActionId):
        lIntFocusId = self.getFocusId()            
        if lIntFocusId != 1000:
            if lIntActionId in (9,10,216,247,257,275,61467,92,61448):
                self.visible = False
                self.close()    
        else:
            self.setFocusId(1000)
            if lIntActionId in (9,10,216,247,257,275,61467,92,61448):
                if self.lIntMenuDepth == 0:
                    self.visible = False
                    self.close()
                else:
                    self.fncBuildLnbList()     
                    
    def onClick(self, controlID):
        if controlID == 1000:
            lObjItm = self.getControl(1000).getSelectedItem()
            getattr(self, lObjItm.getProperty('action'))(lObjItm) 
            
        if controlID == 1001:
            if self.lIntMenuDepth > 0:
                self.fncBuildLnbList()
            else:
                self.fncSaveConfig()
                self.visible = False
                self.close()                
        if controlID == 1020:
            self.visible = False
            self.close()
        if controlID == 1050:
            self.fncSetDiSEqCVersion()
        
        self.onFocus(0)
        
    def onUnload(self):
        pass

    def onFocus(self, controlID):
        if self.lIntMenuDepth > 0:
            self.getControl(1020).setVisible(False)
            self.getControl(1050).setEnabled(False)
            self.getControl(1001).setLabel(_(32136))
        else:
            self.getControl(1020).setVisible(True)
            self.getControl(1050).setEnabled(True)
            self.getControl(1001).setLabel(_(32135))
            
        self.setProperty("infotext", "")
        if controlID == 1000:
            lStrTextId = self.getControl(1000).getSelectedItem().getProperty('infotext')
            if not lStrTextId == "":
                self.setProperty("infotext", _(int(lStrTextId)))
        if controlID == 1050:
            self.setProperty("infotext", _(self.lStrDiSEqCMode['info']))        

    def fncGetKey(self, key):
        try:
            return int(key)
        except ValueError:
            return key
        
    def fncSaveConfig(self):
        lStrWriteMode = "\n"
        if not os.path.exists(os.path.dirname(__usrcfg__)):
            os.makedirs(os.path.dirname(__usrcfg__))
        if os.path.exists(__usrcfg__):
            os.rename(__usrcfg__, __usrcfg__.replace('.cfg', '.bck'))
        lObjFile = open(__usrcfg__, 'w')
        for lStrMode in self.lDicDiSEqC['modes']:
            if self.lDicDiSEqC['modes'][lStrMode]['mode'] == self.lStrDiSEqCMode['mode']:
                lStrWriteMode = "%s%s" % (lStrMode, lStrWriteMode)
                break
        lObjFile.write(lStrWriteMode)
        lObjFile.write(json.dumps(self.lDicDiSEqCLNBs))
        lObjFile.close()   
        xbmc.log(repr(self.lStrDiSEqCMode))
        if self.lStrDiSEqCMode['mode'] == '0':
            self.fncSetDiSEqCConfig(False)
        else:
            self.fncSetDiSEqCConfig(True)
        self.fncWriteDiseqcConf()
        
    def fncLoadConfig(self):
        if os.path.exists(__usrcfg__):
            with open(__usrcfg__) as lStrFile:
                lStrMode = lStrFile.readline().strip()
                self.lDicDiSEqCLNBs = json.loads(lStrFile.readline().strip()) 
                self.fncSetDiSEqCVersion(lStrMode)
            lStrFile.close()
            
    def fncSetDiSEqCConfig(self, lBolState):
        lArrLines = []
        lStrFile = '%s/userdata/addon_data/%s/config/setup.conf' % (XBMC_USER_HOME, __vdrscriptid__)
        if os.path.exists(lStrFile):
            with open(lStrFile, "r") as lObjFile:
                for lStrLine in lObjFile:
                    if "diseqc" in lStrLine.lower():
                        if lBolState == True:
                            lStrLine = "DiSEqC = 1\n"
                        else:
                            lStrLine = "DiSEqC = 0\n"
                    lArrLines.append(lStrLine)
            lObjFile.close()
            os.rename(lStrFile, lStrFile.replace('.conf', '.bck'))            
            lObjFile = open(lStrFile, 'w')
            for lStrLine in lArrLines:
                lObjFile.write("%s" % lStrLine)
            lObjFile.close() 
          
    def fncWriteDiseqcConf(self):
        lStrConf = ""
        lIntEntry = 0
        for lStrLnb in sorted(self.lDicDiSEqCLNBs, key=self.fncGetKey):
            lStrLine = ""
            lDicLnb = self.lDicDiSEqCLNBs[lStrLnb]
            if not lDicLnb['adapter'] == '':
                lStrLine += "%s:\n" % lDicLnb['adapter']
            if lDicLnb['state'] != "0":
                lArrPol = ['V', 'H'] if lDicLnb['pol'] == '0' else ['L', 'R'] 
                if lDicLnb['type'] != 'none' and lDicLnb['type'] != 'custom':
                    lDicLnb['LnbFrequLo'] = self.lDicDiSEqC['lnbtype'][lDicLnb['type']]['LnbFrequLo']  
                    lDicLnb['LnbFrequHi'] = self.lDicDiSEqC['lnbtype'][lDicLnb['type']]['LnbFrequHi'] 
                    lDicLnb['LnbSLOF'] = self.lDicDiSEqC['lnbtype'][lDicLnb['type']]['LnbSLOF'] 
                    lDicLnb['dual'] = self.lDicDiSEqC['lnbtype'][lDicLnb['type']]['dual']                    
                
                if self.lStrDiSEqCMode['mode'] == "1":
                    lStrTsh = lDicLnb['LnbSLOF'] if lIntEntry == 0 else "99999"
                    lStrTone = "t" if lIntEntry == 0 else "T"
                    lStrLine += "%s %s %s %s t v W50 %s\n" % (lDicLnb['sat'], lStrTsh, lArrPol[0], lDicLnb['LnbFrequHi'], lStrTone)
                    lStrLine += "%s %s %s %s t V W50 %s\n" % (lDicLnb['sat'], lStrTsh, lArrPol[1], lDicLnb['LnbFrequHi'], lStrTone)          

                elif self.lStrDiSEqCMode['mode'] == "2":
                    lStrPort = "A" if lIntEntry == 0 else "B"
                    lStrLine += "%s 99999 %s %s t v W50 %s\n" % (lDicLnb['sat'], lArrPol[0], lDicLnb['LnbFrequHi'], lStrPort)
                    lStrLine += "%s 99999 %s %s t V W50 %s\n" % (lDicLnb['sat'], lArrPol[1], lDicLnb['LnbFrequHi'], lStrPort) 
                    
                elif self.lStrDiSEqCMode['mode'] == "3":
                    lArrDual = ['W50 t', 'W50 T'] if lDicLnb['dual'] == "1" else ['','']
                    if lDicLnb['dual'] == "1":
                        lStrLine += "%s %s %s %s t v W50 [E0 00 00] W50 [E0 00 03] W150 [E0 10 38 F%X] %s\n" % (lDicLnb['sat'], lDicLnb['LnbSLOF'], lArrPol[0], lDicLnb['LnbFrequLo'], (0 + ((lIntEntry) * 4)), lArrDual[0])
                        lStrLine += "%s %s %s %s t V W50 [E0 00 00] W50 [E0 00 03] W150 [E0 10 38 F%X] %s\n" % (lDicLnb['sat'], lDicLnb['LnbSLOF'], lArrPol[1], lDicLnb['LnbFrequLo'], (2 + ((lIntEntry) * 4)), lArrDual[0])   
                    lStrLine += "%s 99999 %s %s t v W50 [E0 00 00] W50 [E0 00 03] W150 [E0 10 38 F%X] %s\n" % (lDicLnb['sat'], lArrPol[0], lDicLnb['LnbFrequHi'], (1 + ((lIntEntry) * 4)), lArrDual[1])
                    lStrLine += "%s 99999 %s %s t V W50 [E0 00 00] W50 [E0 00 03] W150 [E0 10 38 F%X] %s\n" % (lDicLnb['sat'], lArrPol[1], lDicLnb['LnbFrequHi'], (3 + ((lIntEntry) * 4)), lArrDual[1]) 
                    
                elif self.lStrDiSEqCMode['mode'] == "4":
                    lArrDual = ['W50 t', 'W50 T'] if lDicLnb['dual'] == "1" else ['','']
                    if lDicLnb['dual'] == "1":
                        lStrLine += "%s %s %s %s t v W50 [E0 00 00] W50 [E0 00 03] W150 [E0 10 39 F%X] %s\n" % (lDicLnb['sat'], lDicLnb['LnbSLOF'], lArrPol[0], lDicLnb['LnbFrequLo'], lIntEntry, lArrDual[0])
                        lStrLine += "%s %s %s %s t V W50 [E0 00 00] W50 [E0 00 03] W150 [E0 10 39 F%X] %s\n" % (lDicLnb['sat'], lDicLnb['LnbSLOF'], lArrPol[1], lDicLnb['LnbFrequLo'], lIntEntry, lArrDual[0]) 
                    lStrLine += "%s 99999 %s %s t v W50 [E0 00 00] W50 [E0 00 03] W150 [E0 10 39 F%X] %s\n" % (lDicLnb['sat'], lArrPol[0], lDicLnb['LnbFrequHi'], lIntEntry, lArrDual[1])
                    lStrLine += "%s 99999 %s %s t V W50 [E0 00 00] W50 [E0 00 03] W150 [E0 10 39 F%X] %s\n" % (lDicLnb['sat'], lArrPol[1], lDicLnb['LnbFrequHi'], lIntEntry, lArrDual[1]) 
                    
                elif self.lStrDiSEqCMode['mode'] == "5":
                    lArrDual = ['W50 t', 'W50 T'] if lDicLnb['dual'] == "1" else ['','']
                    if lDicLnb['dual'] == "1":
                        lStrLine += "%s %s %s %s t v W50 [E0 31 60] W150 [E0 31 6B %02X] %s\n" % (lDicLnb['sat'], lDicLnb['LnbSLOF'], lArrPol[0], lDicLnb['LnbFrequLo'], int(lDicLnb['position']), lArrDual[0])
                        lStrLine += "%s %s %s %s t V W50 [E0 31 60] W150 [E0 31 6B %02X] %s\n" % (lDicLnb['sat'], lDicLnb['LnbSLOF'], lArrPol[1], lDicLnb['LnbFrequLo'], int(lDicLnb['position']), lArrDual[0]) 
                    lStrLine += "%s 99999 %s %s t v W50 [E0 31 60] W150 [E0 31 6B %02X] %s\n" % (lDicLnb['sat'], lArrPol[0], lDicLnb['LnbFrequHi'], int(lDicLnb['position']), lArrDual[1])
                    lStrLine += "%s 99999 %s %s t V W50 [E0 31 60] W150 [E0 31 6B %02X] %s\n" % (lDicLnb['sat'], lArrPol[1], lDicLnb['LnbFrequHi'], int(lDicLnb['position']), lArrDual[1])
                    
                elif self.lStrDiSEqCMode['mode'] == "6":
                    lArrDual = ['W50 t', 'W50 T'] if lDicLnb['dual'] == "1" else ['','']
                    lStrCmd = ""
                    for lStrCommand in sorted(lDicLnb['commands'], key=self.fncGetKey):
                        lStrCmd = "%s %s" % (lStrCmd, lDicLnb['commands'][lStrCommand]['cmd'])
                    if lDicLnb['dual'] == "1":
                        lStrLine += "%s %s %s %s t v W50 %s %s\n" % (lDicLnb['sat'], lDicLnb['LnbSLOF'], lArrPol[0], lDicLnb['LnbFrequLo'], lStrCmd, lArrDual[0])
                        lStrLine += "%s %s %s %s t V W50 %s %s\n" % (lDicLnb['sat'], lDicLnb['LnbSLOF'], lArrPol[1], lDicLnb['LnbFrequLo'], lStrCmd, lArrDual[0]) 
                    lStrLine += "%s 99999 %s %s t v W50 %s %s\n" % (lDicLnb['sat'], lArrPol[0], lDicLnb['LnbFrequHi'], lStrCmd, lArrDual[1])
                    lStrLine += "%s 99999 %s %s t V W50 %s %s\n" % (lDicLnb['sat'], lArrPol[1], lDicLnb['LnbFrequHi'], lStrCmd, lArrDual[1])
                    
                elif self.lStrDiSEqCMode['mode'] == "0":
                    lStrLine = ""

                lStrConf += lStrLine

            lIntEntry+=1
                      
        lStrFile = '%s/userdata/addon_data/%s/config/diseqc.conf' % (XBMC_USER_HOME, __vdrscriptid__)
        if os.path.exists(lStrFile):
            os.rename(lStrFile, lStrFile.replace('.cfg', '.bck'))          
        lObjFile = open(lStrFile, 'w') 
        lObjFile.write(lStrConf)
        lObjFile.close() 
        
    def fncGetLnbState(self, lIntState):
        lStrReturn = ""
        if int(lIntState) > 0:
            lStrReturn = _(32082)
        else:
            lStrReturn = _(32081)
        return lStrReturn
        
    def fncLoadSatelites(self):

        with open('%s/config/sources.conf' % __vrdaddon__.getAddonInfo('path')) as lStrFile:
            lIntSplitPos = 0
            lStrShort = ""
            lStrLong = ""
            lIntSatCount = 1
            for lStrLine in lStrFile:
                lStrLine = lStrLine.strip()
                if not lStrLine.startswith('#') and not lStrLine == "":
                    lIntSplitPos = lStrLine.find(" ")
                    lStrShort = lStrLine[:lIntSplitPos].strip()
                    lStrLong = lStrLine[lIntSplitPos:].strip()
                    if len(lStrShort) >= 2 and len(lStrLong)>= 2:
                        self.lDicSatellites[lStrShort] = {'name':lStrLong,'index':lIntSatCount}
                        lIntSatCount = lIntSatCount + 1
        
    def fncAddListItem(self, lStrLabel, lStrEntry, lStrValue, lStrAction, lStrTyp, lStrInfoText="", lDicProperties={}):
        lLstItem = xbmcgui.ListItem(label=lStrLabel)
        lLstItem.setProperty("config", lStrEntry)        
        lLstItem.setProperty("value", lStrValue)
        lLstItem.setProperty("action", lStrAction)
        lLstItem.setProperty("typ", lStrTyp)
        lLstItem.setProperty("infotext", lStrInfoText)
        if len(lDicProperties) > 0:
            for lStrProperty in lDicProperties:
                lLstItem.setProperty(lStrProperty, lDicProperties[lStrProperty])
        self.getControl(1000).addItem(lLstItem) 
        return lLstItem
        
    def fncSetDiSEqCVersion(self, lStrMode=""):
        if lStrMode == "":
            lArrValues = []        
            lArrModes = []
            for lStrMode in sorted(self.lDicDiSEqC['modes'], key=lambda x: self.lDicDiSEqC['modes'][x]['order']): #self.lDicDiSEqC['modes']:
                lArrValues.append(lStrMode)
                lArrModes.append(_(self.lDicDiSEqC['modes'][lStrMode]['name']))
            lObjSelectDialog = xbmcgui.Dialog()
            lIntResult = lObjSelectDialog.select(_(32115), lArrModes)
            if lIntResult >= 0:
                self.lStrDiSEqCMode = self.lDicDiSEqC['modes'][lArrValues[lIntResult]]
                self.lDicDiSEqCLNBs = {'%d' % key: self.lDicLnb.copy() for 
                    (key) in range(1, self.lStrDiSEqCMode['ports']+1)}
        else: 
            if lStrMode in self.lDicDiSEqC['modes']:
                self.lStrDiSEqCMode = self.lDicDiSEqC['modes'][lStrMode]
        self.fncBuildLnbList()
        self.getControl(1050).setLabel(_(self.lStrDiSEqCMode['name']))
        self.setFocusId(1050)            

    def fncBuildLnbList(self):
        self.lIntMenuDepth = 0
        self.getControl(1000).reset()
        for lIntLnb in sorted(self.lDicDiSEqCLNBs, key=self.fncGetKey): #self.lDicDiSEqCLNBs:
            lDicExtraProperties = {}
            if self.lDicDiSEqCLNBs[lIntLnb]['state'] != "0":
                if self.lDicDiSEqCLNBs[lIntLnb]['type'] != 'none':
                    if self.lDicDiSEqCLNBs[lIntLnb]['type'] == 'custom':
                        lDicExtraProperties = {
                            "LnbFrequLo": self.lDicDiSEqCLNBs[lIntLnb]['LnbFrequLo'],
                            "LnbFrequHi": self.lDicDiSEqCLNBs[lIntLnb]['LnbFrequHi'],
                            "LnbSLOF": self.lDicDiSEqCLNBs[lIntLnb]['LnbSLOF'],
                            "LnbPolar": self.lDicDiSEqCLNBs[lIntLnb]['pol'], 
                            "sat": self.lDicDiSEqCLNBs[lIntLnb]['sat'],
                            "state":"1",
                        }
                    else:
                        lDicExtraProperties = {
                            "LnbFrequLo": self.lDicDiSEqC['lnbtype'][self.lDicDiSEqCLNBs[lIntLnb]['type']]['LnbFrequLo'],
                            "LnbFrequHi": self.lDicDiSEqC['lnbtype'][self.lDicDiSEqCLNBs[lIntLnb]['type']]['LnbFrequHi'],
                            "LnbSLOF": self.lDicDiSEqC['lnbtype'][self.lDicDiSEqCLNBs[lIntLnb]['type']]['LnbSLOF'],
                            "LnbPolar": str(self.lDicDiSEqCLNBs[lIntLnb]['pol']), 
                            "sat": self.lDicDiSEqCLNBs[lIntLnb]['sat'],
                            "state":"1",
                        }                
            lIntEntryName = 32080
            self.getControl(1111).setLabel(_(32156))
            if self.lStrDiSEqCMode['mode'] == '5':
                lIntEntryName = 32155
                self.getControl(1111).setLabel(_(32157))
            if self.lStrDiSEqCMode['mode'] == '6':    
                lIntEntryName = 32161
                self.getControl(1111).setLabel(_(32160))
            lObjListItem = self.fncAddListItem("%s#%s" % (_(lIntEntryName), lIntLnb), lIntLnb, 
                self.fncGetLnbState(self.lDicDiSEqCLNBs[lIntLnb]['state']), "fncLnbConfigMenu", "lnb", "", lDicExtraProperties)

        self.setFocusId(1000)
        self.getControl(1000).selectItem(self.lIntSelectedLnb)
        self.lIntSelectedLnb = -1
        
    def fncLnbConfigMenu(self, lObjItem):
        lStrConfig = lObjItem.getProperty('config')
        lStrValue = lObjItem.getProperty('value')
        lStrTyp = lObjItem.getProperty('typ')
        self.getControl(1111).setLabel(_(32158))
        if self.lIntSelectedLnb == -1:
            self.lIntSelectedLnb = self.getControl(1000).getSelectedPosition()         
        self.lIntMenuDepth = 1   
        self.getControl(1000).reset()    
        self.fncAddListItem(_(32303), lStrConfig, 
            self.lDicDiSEqCLNBs[lStrConfig]['adapter'], "fncAssignAdapter", "list", "32304")        
        self.fncAddListItem(_(32123), lStrConfig, 
            self.lDicSatellites[self.lDicDiSEqCLNBs[lStrConfig]['sat']]['name'], "fncLnbSetSat", "list", "32128")
        self.fncAddListItem(_(32124), lStrConfig, 
            _(self.lDicDiSEqC['lnbtype'][self.lDicDiSEqCLNBs[lStrConfig]['type']]['name']), "fncLnbSetLo", "list", "32129")
        if self.lStrDiSEqCMode['mode'] == '5': 
            self.fncAddListItem(_(32159), lStrConfig, 
                self.lDicDiSEqCLNBs[lStrConfig]['position'], "fncLnbSetPos", "list", "32129")
        if self.lStrDiSEqCMode['mode'] == '6':    
            for lStrCommand in sorted(self.lDicDiSEqCLNBs[lStrConfig]['commands']):
                self.fncAddListItem(_(self.lDicDiSEqCLNBs[lStrConfig]['commands'][lStrCommand]['name']), lStrConfig, 
                    _(self.lDicDiSEqC['modes'][self.lDicDiSEqCLNBs[lStrConfig]['commands'][lStrCommand]['mode']]['name']) \
                    + ' -> ' + self.lDicDiSEqCLNBs[lStrConfig]['commands'][lStrCommand]['value'], "fncAddCommand", "list", "", 
                    {'idx':str(lStrCommand)})
            self.fncAddListItem(_(32152), lStrConfig, "", "fncAddCommand", "list", "32143")              
        else:
            pass
        if self.lDicDiSEqCLNBs[lStrConfig]['sat'] == 'none' or \
            self.lDicDiSEqCLNBs[lStrConfig]['type'] == 'none':
            self.lDicDiSEqCLNBs[lStrConfig]['state'] = "0"
        else:
            self.lDicDiSEqCLNBs[lStrConfig]['state'] = "1"
        self.getControl(1000).selectItem(self.lIntSelectedConfig)
        self.lIntSelectedConfig = -1
        
    def fncAssignAdapter(self, lObjItem):
        lStrConfig = lObjItem.getProperty('config')
        lStrValue = lObjItem.getProperty('value')
        lStrTyp = lObjItem.getProperty('typ')
        if self.lIntSelectedConfig == -1:
            self.lIntSelectedConfig = self.getControl(1000).getSelectedPosition()      
        lObjDialog = xbmcDialog = xbmcgui.Dialog()
        lStrReturn = lObjDialog.input(_(32303), '')
        self.lDicDiSEqCLNBs[lStrConfig]['adapter'] = lStrReturn
        self.fncLnbConfigMenu(lObjItem)
      
    def fncLnbSetSat(self, lObjItem):
        lStrConfig = lObjItem.getProperty('config')
        lStrValue = lObjItem.getProperty('value')
        lStrTyp = lObjItem.getProperty('typ')
        if self.lIntSelectedConfig == -1:
            self.lIntSelectedConfig = self.getControl(1000).getSelectedPosition()         
        self.lIntMenuDepth = 1
        lArrKey = []        
        lArrSat = []
        for lStrSat in sorted(self.lDicSatellites, key=lambda x: self.lDicSatellites[x]['index']):
            lArrKey.append(lStrSat)        
            lArrSat.append("%s - %s" % (lStrSat, self.lDicSatellites[lStrSat]['name']))
        lObjSelectDialog = xbmcgui.Dialog()
        lIntResult = lObjSelectDialog.select(_(32031), lArrSat)    
        if lIntResult >= 0:
            self.lDicDiSEqCLNBs[lStrConfig]['dual'] = "0"
            self.lDicDiSEqCLNBs[lStrConfig]['sat'] = lArrKey[lIntResult]
        self.fncLnbConfigMenu(lObjItem)

    def fncLnbSetLo(self, lObjItem):
        lStrConfig = lObjItem.getProperty('config')
        lStrValue = lObjItem.getProperty('value')
        lStrTyp = lObjItem.getProperty('typ')
        if self.lIntSelectedConfig == -1:
            self.lIntSelectedConfig = self.getControl(1000).getSelectedPosition()                
        lArrKey = []        
        lArrType = []
        lArrKey.append('none')
        lArrType.append(_(32127))
        lArrKey.append('custom')
        lArrType.append(_(32109))          
        for lStrType in self.lDicDiSEqC['lnbtype']:
            if lStrType != 'none' and lStrType != 'custom':
                lArrKey.append(lStrType)
                lArrType.append("%s (%s)" % (_(self.lDicDiSEqC['lnbtype'][lStrType]['name']), _(32112)))
        for lStrType in self.lDicDiSEqC['lnbtype']:
            if lStrType != 'none' and lStrType != 'custom':
                lArrKey.append(lStrType)
                lArrType.append("%s (%s)" % (_(self.lDicDiSEqC['lnbtype'][lStrType]['name']), _(32113)))     
        lObjSelectDialog = xbmcgui.Dialog()
        lIntResult = lObjSelectDialog.select(_(32031), lArrType)
        if lIntResult == 0:
            self.lDicDiSEqCLNBs[lStrConfig]['type'] = lArrKey[lIntResult]       
            self.lDicDiSEqCLNBs[lStrConfig]['pol'] = "0"
        if lIntResult == 1:
            lObjDialog = xbmcDialog = xbmcgui.Dialog()
            self.lDicDiSEqCLNBs[lStrConfig]['type'] = lArrKey[lIntResult]
            lIntReturn = lObjDialog.numeric(0, _(32130), str(self.lDicDiSEqCLNBs[lStrConfig]['LnbFrequLo']))
            if lIntReturn:
                if lIntReturn > 0:
                    self.lDicDiSEqCLNBs[lStrConfig]['dual'] = "1"
                self.lDicDiSEqCLNBs[lStrConfig]['LnbFrequLo'] = str(lIntReturn)
            lIntReturn = lObjDialog.numeric(0, _(32131), str(self.lDicDiSEqCLNBs[lStrConfig]['LnbFrequHi']))
            if lIntReturn:
                self.lDicDiSEqCLNBs[lStrConfig]['LnbFrequHi'] = str(lIntReturn)
            lIntReturn = lObjDialog.numeric(0, _(32132), str(self.lDicDiSEqCLNBs[lStrConfig]['LnbSLOF']))
            if lIntReturn:
                self.lDicDiSEqCLNBs[lStrConfig]['LnbSLOF'] = str(lIntReturn)
            lIntReturn = lObjDialog.select(_(32133), [_(32112),_(32113)])
            if lIntReturn >=0:
               self.lDicDiSEqCLNBs[lStrConfig]['pol'] = str(lIntReturn)                
        if lIntResult >= 2:
            self.lDicDiSEqCLNBs[lStrConfig]['type'] = lArrKey[lIntResult]
            self.lDicDiSEqCLNBs[lStrConfig]['pol'] = "0"
            if lIntResult >= len(self.lDicDiSEqC['lnbtype']):
                self.lDicDiSEqCLNBs[lStrConfig]['pol'] = "1"
        self.fncLnbConfigMenu(lObjItem)  
    
    def fncSelectCustomPortVersion(self, lArrNotUsable = []):
        lArrValues = []        
        lArrModes = []
        for lStrMode in sorted(self.lDicDiSEqC['modes'], key=lambda x: self.lDicDiSEqC['modes'][x]['order']): 
            if not lStrMode in lArrNotUsable: #lStrMode != "User-defined" and lStrMode != "Tune-22k" and lStrMode != "Disabled" :
                lArrValues.append(lStrMode)
                lArrModes.append(_(self.lDicDiSEqC['modes'][lStrMode]['name']))
        lObjSelectDialog = xbmcgui.Dialog()
        lIntResult = lObjSelectDialog.select(_(32115), lArrModes)
        if lIntResult >= 0:
            return lArrValues[lIntResult]
        else:
            return None
            
    def fncSelectCustomPortNumber(self, lStrVersion):
        lArrValues = []        
        lArrModes = []
        lIntRange = int(self.lDicDiSEqC['modes'][lStrVersion]['ports'])
        for lStrMode in range(1, lIntRange+1):
            lArrValues.append(str(lStrMode))
            lArrModes.append("%s #%d" % (_(32142), lStrMode))
        lObjSelectDialog = xbmcgui.Dialog()
        lIntResult = lObjSelectDialog.select(_(32115), lArrModes)
        if lIntResult >= 0:
            return lArrValues[lIntResult]
        else: 
            return None  
        
    def fncLnbSetPos(self, lObjItem):
        lStrConfig = lObjItem.getProperty('config')
        lStrValue = lObjItem.getProperty('value')
        lStrTyp = lObjItem.getProperty('typ')
        lStrIndex = lObjItem.getProperty('idx')
        if self.lIntSelectedConfig == -1:
            self.lIntSelectedConfig = self.getControl(1000).getSelectedPosition()      
        lObjDialog = xbmcDialog = xbmcgui.Dialog()
        lIntReturn = lObjDialog.numeric(0, _(32153), '')
        if lIntReturn >= 0:
            self.lDicDiSEqCLNBs[lStrConfig]['position'] = str(lIntReturn)
        self.fncLnbConfigMenu(lObjItem)
        
    def fncAddCommand(self, lObjItem):
        lStrConfig = lObjItem.getProperty('config')
        lStrValue = lObjItem.getProperty('value')
        lStrTyp = lObjItem.getProperty('typ')
        lStrIndex = lObjItem.getProperty('idx')
        if self.lIntSelectedConfig == -1:
            self.lIntSelectedConfig = self.getControl(1000).getSelectedPosition()      
        lArrValue = [_(32148), _(32149), _(32305), _(32151)]
        #lArrValue = [_(32148), _(32149), _(32151)]
        lObjSelectDialog = xbmcgui.Dialog()
        lIntResult = lObjSelectDialog.select(_(32150), lArrValue)
        if lIntResult == 0: #Set Switch
            lArrNotUsable = ["User-defined", "Tune-22k", "Disabled"]
            for lStrVersion in self.lDicDiSEqC['modes']:
                lBolExist = False
                for lStrCommand in self.lDicDiSEqCLNBs[lStrConfig]['commands']:
                    if lStrVersion == self.lDicDiSEqCLNBs[lStrConfig]['commands'][lStrCommand]['mode']:
                        lBolExist = True
                if lBolExist == True:
                    lArrNotUsable.append(lStrVersion)
            lStrSwitchVersion = self.fncSelectCustomPortVersion(lArrNotUsable)
            if lStrSwitchVersion == "Disabled":
                return 0               
            if not lStrSwitchVersion is None: 
                lStrSwitchPort = int(self.fncSelectCustomPortNumber(lStrSwitchVersion))             
                if not lStrSwitchPort is None: 
                    if lStrSwitchVersion == "Tune-22k":
                        if lStrSwitchPort == 1:
                            lStrCommand = "t"
                            lStrSwitchPort = "t"
                        elif lStrSwitchPort == 2:
                            lStrCommand = "T"
                            lStrSwitchPort = "T"
                    elif lStrSwitchVersion == "Toneburst":
                        if lStrSwitchPort == 1:
                            lStrCommand = "A"
                            lStrSwitchPort = "A"
                        elif lStrSwitchPort == 2:
                            lStrCommand = "B"
                            lStrSwitchPort = "B"
                    elif lStrSwitchVersion == "DiSEqC-1.0":
                        lStrCommand = "W50 [E0 00 00] W50 [E0 00 03] W150 [E0 10 38 F%X]" % (2 + ((lStrSwitchPort-1) * 4))
                    else:
                        lStrCommand = "W50 [E0 00 00] W50 [E0 00 03] W150 [E0 10 39 F%X]" % ((lStrSwitchPort-1))
                    
                    if str(lStrIndex) != '':
                        lIntCmdEntry = lStrIndex
                    else:
                        if len(self.lDicDiSEqCLNBs[lStrConfig]['commands']) == 0:
                            lIntCmdEntry = 1
                        else:                   
                            lIntCmdEntry = max(int(x) for x in self.lDicDiSEqCLNBs[lStrConfig]['commands'].keys()) + 1
                        
                    self.lDicDiSEqCLNBs[lStrConfig]['commands'][str(lIntCmdEntry)] = {'name':32148, 'value':str(lStrSwitchPort), 
                        'mode':lStrSwitchVersion, 'cmd':lStrCommand}
            
        elif lIntResult == 1: #Set Position
            lObjDialog = xbmcDialog = xbmcgui.Dialog()
            lIntReturn = lObjDialog.numeric(0, _(32153), '')
            if lIntReturn >= 0:
                if str(lStrIndex) != '':
                    lIntCmdEntry = int(lStrIndex)
                else:
                    if len(self.lDicDiSEqCLNBs[lStrConfig]['commands']) == 0:
                        lIntCmdEntry = 1
                    else:                   
                        lIntCmdEntry = max(int(x) for x in self.lDicDiSEqCLNBs[lStrConfig]['commands'].keys()) + 1

                lStrCommand = "W50 [E0 31 60] W150 [E0 31 6B %02X]" % int(lIntReturn)  
                self.lDicDiSEqCLNBs[lStrConfig]['commands'][str(lIntCmdEntry)] = {'name':32149, 'value':str(lIntReturn), 
                    'mode':"DiSEqC-1.2", 'cmd':lStrCommand}            
                
        elif lIntResult == 2: #Set Position (USALS)
            lObjDialog = xbmcDialog = xbmcgui.Dialog()
            lDblLong = float(lObjDialog.input(_(32306), ''))
            if lDblLong >= 0:
                lDblLat = float(lObjDialog.input(_(32307), ''))
                if lDblLat >= 0:                
                    lDblSat = float(lObjDialog.input(_(32308), ''))
                    if lDblSat >= 0:
                        lDblHA = rotor_calc.calcSatHourangle(lDblSat, lDblLat, lDblLong)
                        if lDblLat >= 0:
                            rotorCmd = rotor_calc.azimuth2Rotorcode(180 - lDblHA)
                            if lDblHA <= 180:
                                rotorCmd |= 0xE000
                            else:
                                rotorCmd |= 0xD000
                        else: 
                            if lDblHA <= 180:
                                rotorCmd = rotor_calc.azimuth2Rotorcode(lDblHA) | 0xD000
                            else:
                                rotorCmd = rotor_calc.azimuth2Rotorcode(360 - lDblHA) | 0xE000                       
                        lStrCommand = "W50 [E0 31 60] W150 [E010%X]" % rotorCmd  
                        
                        if str(lStrIndex) != '':
                            lIntCmdEntry = lStrIndex
                        else:
                            if len(self.lDicDiSEqCLNBs[lStrConfig]['commands']) == 0:
                                lIntCmdEntry = 1
                            else:                   
                                lIntCmdEntry = max(int(x) for x in self.lDicDiSEqCLNBs[lStrConfig]['commands'].keys()) + 1
                            
                        self.lDicDiSEqCLNBs[lStrConfig]['commands'][str(lIntCmdEntry)] = {'name':32149, 'value':'USALS', 
                            'mode':"DiSEqC-1.2", 'cmd':lStrCommand}  
                    
        elif lIntResult == 3: #Delete
            del self.lDicDiSEqCLNBs[lStrConfig]['commands'][lStrIndex]

        self.fncLnbConfigMenu(lObjItem)
    
gWinDiSEqC = cWinDiSEqC('WinDiSEqC_window.xml', __cwd__, 'Default')
gWinDiSEqC.doModal()
