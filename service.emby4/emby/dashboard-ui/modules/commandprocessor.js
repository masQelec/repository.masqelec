define(["connectionManager"],function(connectionManager){"use strict";function downloadFiles(urls){return require(["multi-download"]).then(function(responses){(0,responses[0])(urls)})}return{executeCommand:function(command,item,options){return"download"===command?function(item,options){var apiClient=connectionManager.getApiClient(item);if("Log"===item.Type)return downloadFiles([apiClient.getLogDownloadUrl(item)]);var mediaSourceId=options?options.mediaSourceId:null;return downloadFiles([apiClient.getItemDownloadUrl(item.Id,mediaSourceId)])}(item,options):"delete"===command?function(item){return require(["deleteHelper"]).then(function(responses){return responses[0].deleteItem({item:item,navigate:!1})})}(item):"identify"===command?function(item){return require(["itemIdentifier"]).then(function(responses){return responses[0].show(item)})}(item):Promise.reject()}}});