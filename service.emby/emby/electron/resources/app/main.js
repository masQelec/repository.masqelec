(function () {

    const path = require('path');

    var electron = require('electron');
    const { app, Menu, Tray, BrowserWindow } = require('electron');

    if (app.makeSingleInstance(function () { })) {
        app.quit();
    }

    var tray;

    if (app.dock) {

        app.dock.setIcon(path.join(__dirname, 'icon.png'));

        app.dock.hide();
    }

    function browseLibrary() {
        launchServerUrl('index.html');
    }

    function openServerDashboard() {
        launchServerUrl('index.html#!/dashboard.html');
    }

    var commandLineArguments = process.argv.slice(1);
    var appMode = commandLineArguments[0];
    var displayLanguage = commandLineArguments[2] || 'en-us';

    function getBaseServerUrl() {

        var baseServerUrl = commandLineArguments[1] || 'http://localhost:8096';

        return baseServerUrl;
    }

    function restartServer() {

        sendPostToServer('/system/restart').catch(function () {

            alert('Unable to restart server');
        });
    }

    function exit() {

        sendPostToServer('/system/shutdown');
    }

    function quitApp() {
        app.quit();
    }

    function isMacOS() {
        if (app.dock) {
            return true;
        }
        return false;
    }

    function sendPostToServer(url) {

        return new Promise(function (resolve, reject) {

            var http = require('http');

            var baseUrl = getBaseServerUrl();
            var parts = baseUrl.split(':');

            baseUrl = baseUrl.substring(0, baseUrl.lastIndexOf(':'));
            baseUrl = baseUrl.substring(baseUrl.indexOf('://') + 3);

            // An object of options to indicate where to post to
            var post_options = {
                host: baseUrl,
                port: parseInt(parts[parts.length - 1]),
                path: url,
                method: 'POST'
            };

            // Set up the request
            var post_req = http.request(post_options, resolve);

            post_req.on('error', reject);

            // post the data
            //post_req.write(post_data);
            post_req.end();
        });
    }

    function openCommunity() {
        launchUrl('https://emby.media/community');
    }

    function showEmbyPremiereInfo() {
        launchServerUrl('index.html#!/supporterkey.html');
    }

    function launchServerUrl(url) {

        url = getBaseServerUrl() + '/web/' + url;

        launchUrl(url);
    }

    function launchUrl(url) {
        const opn = require('opn');
        opn(url);
    }

    function processRequest(request, body) {

        var url = require('url');
        var url_parts = url.parse(request.url, true);
        var action = url_parts.pathname.substring(1).toLowerCase();

        switch (action) {

            case 'exit':
                setTimeout(quitApp, 300);
                return Promise.resolve('{}');
            default:
                return Promise.resolve('{}');
        }
    }

    function processNodeRequest(req, res) {

        var body = [];

        req.on('data', function (chunk) {
            body.push(chunk);
        }).on('end', function () {

            body = Buffer.concat(body).toString();
            // at this point, `body` has the entire request body stored in it as a string

            processRequest(req, body).then((json) => {
                if (json != null) {
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(json);
                } else {
                    res.writeHead(500);
                    res.end();
                }
            }).catch(() => {
                res.writeHead(500);
                res.end();
            });
        });
    }

    function createHttpServer(protocol, mainWindow) {

        var http = require('http');

        http.createServer(processNodeRequest).listen(8024, '127.0.0.1');
    }

    function showSplash() {

        var splashUrl = 'file://' + path.join(__dirname, 'splash.html');

        var windowOptions = {

            frame: false,
            resizable: false,
            title: 'Emby',
            width: 480,
            height: 270,
            //alwaysOnTop: true,

            //show: false,
            backgroundColor: '#141414',
            center: true,
            show: false,
            minimizable: true,
            maximizable: false,
            closable: false,
            fullscreenable: false,
            skipTaskbar: false,

            webPreferences: {
                webSecurity: false,
                webgl: false,
                nodeIntegration: false,
                plugins: false,
                webaudio: false,
                java: false,
                allowDisplayingInsecureContent: true,
                allowRunningInsecureContent: true,
                experimentalFeatures: false,
                backgroundThrottling: false
            },

            icon: path.join(__dirname, 'icon.ico')
        };

        // Create the browser window.
        var splashWindow = new BrowserWindow(windowOptions);

        // and load the index.html of the app.
        splashWindow.loadURL(splashUrl);

        splashWindow.show();
    }

    function createTray() {

        // Use different icon for mac os
        var trayIconPath = isMacOS() ? path.join(__dirname, 'icon_mac.png') : path.join(__dirname, 'icon32.png');

        tray = new Tray(trayIconPath)

        const contextMenu = Menu.buildFromTemplate([
            { label: getString('LabelBrowseLibrary'), click: browseLibrary },
            { label: getString('LabelConfigureServer'), click: openServerDashboard },
            { label: 'Emby Premiere', click: showEmbyPremiereInfo },
            { type: 'separator' },
            { label: getString('LabelRestartServer'), click: restartServer },
            { type: 'separator' },
            { label: getString('LabelVisitCommunity'), click: openCommunity },
            { label: getString('LabelExit'), click: exit }
        ]);

        if (!isMacOS()) {
            tray.setTitle(getString('EmbyServer'));
        }

        tray.setToolTip(getString('EmbyServer'));
        tray.setContextMenu(contextMenu);

        tray.on('double-click', browseLibrary);

        //if (tray.displayBalloon) {
        //    tray.displayBalloon({
        //        title: 'Emby',
        //        content: getString('WelcomeToEmbyServer'),
        //        icon: path.join(__dirname, 'icon.png')
        //    });
        //}
    }

    var strings = {};
    function getString(key) {
        return strings[key] || key;
    }

    function loadStringsLanguage(lang) {

        return new Promise(function (resolve, reject) {

            // normalize casing
            lang = lang.split('-');
            if (lang.length == 2) {
                lang = lang[0].toLowerCase() + '-' + lang[1].toUpperCase();
            } else {
                lang = lang[0].toLowerCase();
            }

            var url = path.join(__dirname, 'strings');
            url = path.join(url, lang) + '.json';

            var response = require('fs').readFileSync(url);
            strings = JSON.parse(response);
            resolve();
        });
    }

    function loadStrings() {

        return loadStringsLanguage(displayLanguage).catch(function (e) {
            return loadStringsLanguage('en-US');
        });
    }

    app.on('ready', function () {

        loadStrings().then(function () {
            if (appMode == 'tray') {
                createTray();

                createHttpServer();
            } else if (appMode == 'splash') {
                showSplash();
            }
        });
    });

    function alert(text) {
        electron.dialog.showMessageBox(null, {
            message: text.toString(),
            buttons: ['ok']
        });
    }


})();
