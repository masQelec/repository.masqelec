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
import xbmc
import json
import urllib
import urllib2
import xbmcgui
import xbmcaddon
import xbmcplugin
import subprocess
import httplib

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
        
class cWinMain(xbmcgui.WindowXMLDialog):

    lIntMenuDepth = 0
    lStrDiSEqCMode = "Disabled"
    lDicDiSEqCLNBs = {}
    lStrParentMenuEntry = None
    
    lBolClearScan = "0"
    lObjState = None
    lDicConfig = None
    lDicCountries = None
    lDicSatellites = None
    lStrWirbelscanHost = __addon__.getSetting('HOST')
    lStrWirbelscanPort = __addon__.getSetting('PORT')
    lIntInProgress = 0   
    lIntSelectedItem = 0
    
    lDicSetup = {
        "loglevel":{
            "name":32024,
            "entry":"verbosity",
            "values":{"0":32001, "1":32002, "2":32003, "3":32004, "4":32005, "5":32006},
            "order":1,
            "visible":0
        },
        "logtype":{
            "name":32032,
            "entry":"logFile",
            "values":{"0":32033, "1":32034, "2":32035},
            "order":2,
            "visible":0
        },    
        "type":{
            "name":32025,
            "entry":"DVB_Type",
            "values":{"0":32007, "1":32008, "2":32009, "3":32010, "4":32011, "5":32012, "999":32013},
            "order":3,
            "visible":1
        },
        "t_inversion":{
            "name":32026,
            "entry":"DVBT_Inversion",
            "values":{"0":32014, "1":32015},
            "type":[0],
            "order":4,
            "visible":1
        },  
        "c_inversion":{
            "name":32054,
            "entry":"DVBC_Inversion",
            "values":{"0":32014, "1":32015},
            "type":[1],
            "order":5,
            "visible":1
        },          
        "c_rate":{
            "name":32027,
            "entry":"DVBC_Symbolrate",
            "values":{"0":32016, "1":"69000", "2":"68750", "3":"61110", "4":"62500", 
                      "5":"67900", "6":"68110", "7":"59000", "8":"50000", "9":"34500", 
                      "10":"40000", "11":"69500", "12":"70000", "13":"69520", "14":"51560", 
                      "15":"54830"},
            "type":[1],
            "order":6,
            "visible":1
        }, 
        "c_quam":{
            "name":32028,
            "entry":"DVBC_QAM",
            "values":{"0":32016, "1":32018, "2":32019, "3":32020, "4":32017},
            "type":[1],
            "order":7,
            "visible":1
        },  
        "a_type":{
            "name":32029,
            "entry":"ATSC_type",
            "values":{"0":32021, "1":32022, "2":32023},
            "type":[5],
            "order":8,
            "visible":1
        },          
    }
    
    def __init__(self, *args, **kwargs):
        xbmc.executebuiltin('dialog.close(10140)')
        pass
        
    def onInit(self):
        try:
            self.lObjState = self.fncGetStatus()
        except Exception, e:
            xbmc.executebuiltin('Notification(VDR Configuration, Unable to connect to VDR restfull API, 5000, "")')
            self.close()
            quit()        
        self.fncLoadDefaults()
        self.fncConfigRootMenu()   
        self.setFocusId(1000)
        if 'status' in self.lObjState:
            if self.lObjState['status'] == 1:
                self.getControl(1001).setLabel(_(32045))
                self.getControl(1010).setVisible(True)
                self.lIntInProgress = 1
                self.fncStartScan()
            else:
                self.getControl(1001).setLabel(_(32044))
                self.getControl(1010).setVisible(False)
                self.lIntInProgress = 0
                
    def onAction(self, lIntActionId):
        lIntFocusId = self.getFocusId()
        if lIntFocusId != 1000:
            if lIntActionId in (9,10,216,247,257,275,61467,92,61448):
                self.lIntInProgress = 0
                self.visible = False
                self.close()    
        else:
            self.setFocusId(1000)
            if lIntActionId in (9,10,216,247,257,275,61467,92,61448):
                if self.lIntMenuDepth == 0:
                    self.lIntInProgress = 0
                    self.visible = False
                    self.close()
                elif self.lIntMenuDepth == 1:
                    self.fncLoadConfig()
                    self.fncConfigRootMenu()   
                    self.getControl(1000).selectItem(self.lIntSelectedItem)            
                else:
                    eval(self.lStrParentMenuEntry)
                    self.getControl(1000).selectItem(self.lIntSelectedItem)     
                        
    def onClick(self, controlID):
        if controlID == 1000:
            lObjItm = self.getControl(1000).getSelectedItem()
            getattr(self, lObjItm.getProperty('action'))(
                lObjItm.getProperty('config'), 
                lObjItm.getProperty('value'),
                lObjItm.getProperty('typ')
            )
        if controlID == 1001:
            if self.lIntInProgress != 1:
                self.fncStartScan()
            else:
                self.fncStopScan()
        if controlID == 1020:
            self.lIntInProgress = 0
            self.visible = False
            self.close()            

    def onUnload(self):
        pass

    def onFocus(self, controlID):
        pass

    def fncGetUrl(self, lStrUrl):
        lObjRequest = urllib2.Request(lStrUrl)
        lObjResponse = urllib2.urlopen(lObjRequest) 
        return lObjResponse.read()

    def fncPostUrl(self, lStrUrl, lDicData):
        lStrData = urllib.urlencode(lDicData)
        lObjRequest = urllib2.Request(lStrUrl, lStrData)
        lObjResponse = urllib2.urlopen(lObjRequest) 
        return lObjResponse.read()

    def fncPutUrl(self, lStrUrl, lStrData):
        lObjOpener = urllib2.build_opener(urllib2.HTTPHandler)
        lObjRequest = urllib2.Request(lStrUrl, lStrData)
        lObjRequest.get_method = lambda: 'PUT'
        lStrResult = lObjOpener.open(lObjRequest)
        return lStrResult.read()
        
    def fncParameterToDictionarry(self, lStrParameters):
        lObjDictionary = {}
        if lStrParameters:
            lArrKeyValues = lStrParameters[1:].split("&")
            for lItmKeyValue in lArrKeyValues:
                lArrKeyValue = lItmKeyValue.split('=')
                if (len(lArrKeyValue)) == 2:
                    lObjDictionary[lArrKeyValue[0]] = lArrKeyValue[1]
        return lObjDictionary

    def fncGetStatus(self):
        lStrJson = self.fncGetUrl("http://%s:%s/wirbelscan/getStatus.json" % 
            (self.lStrWirbelscanHost, self.lStrWirbelscanPort))
        return json.loads(lStrJson)
        
    def fncLoadConfig(self):
        lStrJson = self.fncGetUrl("http://%s:%s/wirbelscan/getSetup.json" % 
            (self.lStrWirbelscanHost, self.lStrWirbelscanPort))
        self.lDicConfig = json.loads(lStrJson)
        
    def fncLoadDefaults(self):
        lStrJson = self.fncGetUrl("http://%s:%s/wirbelscan/countries.json" % 
            (self.lStrWirbelscanHost, self.lStrWirbelscanPort))
        self.lDicCountries = json.loads(lStrJson)
        lStrJson = self.fncGetUrl("http://%s:%s/wirbelscan/satellites.json" % 
            (self.lStrWirbelscanHost, self.lStrWirbelscanPort))
        self.lDicSatellites = json.loads(lStrJson)
        self.fncLoadConfig()

    def fncAddListItem(self, lStrLabel, lStrEntry, lStrValue, lStrAction, lStrTyp):
        lLstItem = xbmcgui.ListItem(label=lStrLabel)
        lLstItem.setProperty("config", lStrEntry)        
        lLstItem.setProperty("value", lStrValue)
        lLstItem.setProperty("action", lStrAction)
        lLstItem.setProperty("typ", lStrTyp)
        self.getControl(1000).addItem(lLstItem)  
    
    def fncAddSeparator(self, lStrLabel):
        lLstItem = xbmcgui.ListItem(label=lStrLabel)
        lLstItem.setProperty("typ", "separator")        
        self.getControl(1000).addItem(lLstItem)  
        
    def fncConfigRootMenu(self):
        self.lIntMenuDepth = 0
        self.getControl(1000).reset()
        for lItmKey in sorted(self.lDicSetup, key=lambda x: self.lDicSetup[x]['order']):
            lStrEntry = self.lDicSetup[lItmKey]
            lStrOption = str(self.lDicConfig[lStrEntry['entry']])
            if (not 'type' in lStrEntry or self.lDicConfig['DVB_Type'] in lStrEntry['type']) \
                and lStrEntry['visible'] == 1:
                self.fncAddListItem(_(lStrEntry['name']), lItmKey, 
                    _(lStrEntry['values'][lStrOption]), "fncConfigSubMenu", "list")
        if self.lDicConfig['DVB_Type'] != 2:
            for lObjCountry in self.lDicCountries["countries"]:
                if lObjCountry['id'] == self.lDicConfig['CountryId']:
                    self.fncAddListItem(_(32030), "CountryId", 
                        lObjCountry['fullName'], "fncCountrySubMenu", "list")
                    break
        if self.lDicConfig['DVB_Type'] == 2:
            for lObjSattelite in self.lDicSatellites["satellites"]:
                if lObjSattelite['id'] == self.lDicConfig['SatId']:
                    self.fncAddListItem(_(32031), "SatId", 
                        lObjSattelite['fullName'], "fncSatSubMenu", "list")
                    break

        self.fncAddListItem(_(32146), "clear", self.lBolClearScan, "fncSetClearScan", "bool")
        if self.lDicConfig['scanflags'] & 1 == 1: 
            lStrFlagState = _(32042)
            lIntFlagState = "1"
        else:
            lStrFlagState = _(32043)
            lIntFlagState = "0"
        self.fncAddListItem(_(32037), "0", lIntFlagState, "fncSetConfig", "bool")
        if self.lDicConfig['scanflags'] & 2 == 2: 
            lStrFlagState = _(32042)
            lIntFlagState = "1"
        else:
            lStrFlagState = _(32043)  
            lIntFlagState = "0"
        self.fncAddListItem(_(32038), "1", lIntFlagState, "fncSetConfig", "bool")
        if self.lDicConfig['scanflags'] & 4 == 4: 
            lStrFlagState = _(32042)
            lIntFlagState = "1"
        else:
            lStrFlagState = _(32043)
            lIntFlagState = "0"
        self.fncAddListItem(_(32039), "2", lIntFlagState, "fncSetConfig", "bool")
        if self.lDicConfig['scanflags'] & 8 == 8: 
            lStrFlagState = _(32042)
            lIntFlagState = "1"
        else:
            lStrFlagState = _(32043)
            lIntFlagState = "0"
        self.fncAddListItem(_(32040), "3", lIntFlagState, "fncSetConfig", "bool")
        
    def fncConfigSubMenu(self, lStrConfig, lStrValue, lStrTyp):
        self.lIntSelectedItem = self.getControl(1000).getSelectedPosition()
        lArrValues = []
        lArrOptions = []
        for lStrOption in sorted(self.lDicSetup[lStrConfig]['values'], 
            key=lambda x: self.lDicSetup[lStrConfig]['values'][x]):
            lArrValues.append(lStrOption)
            lArrOptions.append(_(self.lDicSetup[lStrConfig]['values'][lStrOption]))
        lObjSelectDialog = xbmcgui.Dialog()
        lIntResult = lObjSelectDialog.select("", lArrOptions)    
        if lIntResult >= 0:
            self.fncSetConfig(self.lDicSetup[lStrConfig]['entry'], str(lArrValues[lIntResult]), "")
            
    def fncCountrySubMenu(self, lStrConfig, lStrValue, lStrTyp):
        self.lIntSelectedItem = self.getControl(1000).getSelectedPosition()        
        lArrValues = []
        lArrCountrys = []
        for lObjCountry in self.lDicCountries["countries"]:
            lArrValues.append(lObjCountry['id'])
            lArrCountrys.append(lObjCountry['fullName'])
        lObjSelectDialog = xbmcgui.Dialog()
        lIntResult = lObjSelectDialog.select(_(32031), lArrCountrys)    
        if lIntResult >= 0:
            self.fncSetConfig("CountryId", str(lArrValues[lIntResult]), "")
        
    def fncSatSubMenu(self, lStrConfig, lStrValue, lStrTyp):
        self.lIntSelectedItem = self.getControl(1000).getSelectedPosition()    
        lArrValues = []        
        lArrSattelites = []
        for lObjSat in self.lDicSatellites["satellites"]:
            lArrValues.append(lObjSat['id'])        
            lArrSattelites.append(lObjSat['fullName'])
        lObjSelectDialog = xbmcgui.Dialog()
        lIntResult = lObjSelectDialog.select(_(32031), lArrSattelites)    
        if lIntResult >= 0:
            self.fncSetConfig("SatId", str(lArrValues[lIntResult]), "")
            
    def fncDiSEqCSubMenu(self, lStrConfig, lStrValue, lStrTyp):
        gWinDiSEqC = cWinDiSEqC('WinDiSEqC_window.xml', __cwd__, 'Default')
        gWinDiSEqC.doModal()
            
    def fncSetConfig(self, lStrEntry, lStrValue, lStrTyp):       
        if lStrTyp == "bool" and lStrValue == "0":
            self.lIntSelectedItem = self.getControl(1000).getSelectedPosition()
            lStrValue = self.lDicConfig['scanflags'] | (1<<int(lStrEntry))
            lStrEntry = "scanflags"
        if lStrTyp == "bool" and lStrValue == "1":
            self.lIntSelectedItem = self.getControl(1000).getSelectedPosition()
            lStrValue = self.lDicConfig['scanflags'] & ~(1<<int(lStrEntry))
            lStrEntry = "scanflags"
        lStrSendData = "{\"%s\":%s}" % (lStrEntry, lStrValue)
        lStrResult = self.fncPutUrl("http://%s:%s/wirbelscan/setSetup.json" % 
            (self.lStrWirbelscanHost, self.lStrWirbelscanPort), lStrSendData)
        self.fncPostUrl("http://%s:%s/wirbelscan/doCommand.json" % 
            (self.lStrWirbelscanHost, self.lStrWirbelscanPort), {"command":2})
        self.fncLoadConfig()
        self.fncConfigRootMenu()   
        self.setFocusId(1000)
        self.getControl(1000).selectItem(self.lIntSelectedItem)
    
    def fncSetClearScan(self, lStrEntry, lStrValue, lStrTyp):      
        self.lIntSelectedItem = self.getControl(1000).getSelectedPosition()
        if lStrValue == "0":
            self.lBolClearScan = "1"
        else:
            self.lBolClearScan = "0" 
        self.fncConfigRootMenu()   
        self.setFocusId(1000)
        self.getControl(1000).selectItem(self.lIntSelectedItem)
        
    def fncStartScan(self):
        lIntRetry = 0
        lIntPercent = 0
        self.lIntInProgress = 1
        self.getControl(1001).setLabel(_(32045))
        self.getControl(1010).setVisible(True)  

        if self.lBolClearScan == "1":
            xbmc.executebuiltin('ActivateWindow(busydialog)')
            lStrFile = '%s/userdata/addon_data/%s/config/channels.conf' % (XBMC_USER_HOME, __vdrscriptid__)
            if os.path.exists(lStrFile):
                os.rename(lStrFile, lStrFile.replace('.conf', '.bck'))                      
            lObjProcess = subprocess.Popen("systemctl restart service.multimedia.vdr-addon", shell=True)
            lObjProcess.wait()
            xbmc.executebuiltin('Notification(VDR Configuration, Unable to connect to VDR restfull API, 5000, "")')
            xbmc.sleep(5000)
            xbmc.executebuiltin('Dialog.Close(busydialog)')
            self.fncPostUrl("http://%s:%s/wirbelscan/doCommand.json" % 
                (self.lStrWirbelscanHost, self.lStrWirbelscanPort), {"command":0})                
            
        self.fncPostUrl("http://%s:%s/wirbelscan/doCommand.json" % 
            (self.lStrWirbelscanHost, self.lStrWirbelscanPort), {"command":0})
        while self.lIntInProgress == 1 and lIntRetry < 5:
            lObjState = self.fncGetStatus()
            if 'status' in lObjState:
                self.lIntInProgress = lObjState['status']
                if self.lIntInProgress == 1:
                    try:
                        lIntPercent = lObjState['progress']
                        lStrFrequency = lObjState['transponder'].split(' ')
                        if len(lStrFrequency) > 0:
                            self.getControl(1003).setLabel(lStrFrequency[1])
                        self.getControl(1002).setLabel(lObjState['currentDevice'])
                        self.getControl(1004).setLabel(str(lObjState['numChannels']))
                        self.getControl(1005).setLabel(str(lObjState['newChannels']))
                    except Exception, e:
                        pass
                elif self.lIntInProgress == 0 or self.lIntInProgress == 3:
                    self.lIntInProgress = 1
                    lIntRetry+=1
                    self.fncPostUrl("http://%s:%s/wirbelscan/doCommand.json" % 
                        (self.lStrWirbelscanHost, self.lStrWirbelscanPort), {"command":0})
                    xbmc.sleep(1000)
                    
                else:
                    self.lIntInProgress = 0
                    lIntPercent = 100

            self.getControl(1006).setPercent(lIntPercent)                
            xbmc.sleep(1000)

        self.getControl(1006).setPercent(100)
        self.getControl(1001).setLabel(_(32044))
        
    def fncStopScan(self):
        self.fncPostUrl("http://%s:%s/wirbelscan/doCommand.json" % 
            (self.lStrWirbelscanHost, self.lStrWirbelscanPort), {"command":1})
        
gWinMain = cWinMain('window.xml', __cwd__, 'Default')
gWinMain.doModal()
