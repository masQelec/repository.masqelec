import urllib.request
import urllib.error
import json
import traceback
import time
from . import utils

# URL de la API de Kodi
KODI_API_URL = "http://127.0.0.1:8080/jsonrpc"

def json_rpc_call(method, params=None, retries=5, timeout=5):
    """Realiza una llamada a la API JSON-RPC de Kodi con lógica de reintento."""
    headers = {'Content-Type': 'application/json'}
    data = {'jsonrpc': '2.0', 'method': method, 'id': 1}
    if params:
        data['params'] = params
    
    data_encoded = json.dumps(data).encode('utf-8')
    
    for i in range(retries):
        try:
            req = urllib.request.Request(KODI_API_URL, data=data_encoded, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            if i < retries - 1:
                utils.write_log(f"Error en la llamada JSON-RPC: {e}. Reintentando en {timeout} segundos...", level="ERROR")
                time.sleep(timeout)
            else:
                utils.write_log(f"Error en la llamada JSON-RPC: {e}", level="ERROR")
                utils.write_log(traceback.format_exc(), level="ERROR")
                return None
        except Exception as e:
            utils.write_log(f"Error inesperado en la llamada JSON-RPC: {e}", level="ERROR")
            utils.write_log(traceback.format_exc(), level="ERROR")
            return None

def notify_kodi(title, message):
    """Envía una notificación a Kodi."""
    params = {
        "title": title,
        "message": message
    }
    json_rpc_call("GUI.ShowNotification", params)

def get_setting(setting_id):
    """Obtiene el valor de una configuración de Kodi."""
    params = {"setting": setting_id}
    response = json_rpc_call("Settings.GetSettingValue", params)
    if response and 'result' in response:
        return response['result']['value']
    return None

def set_setting(setting_id, value):
    """Establece el valor de una configuración de Kodi."""
    params = {"setting": setting_id, "value": value}
    response = json_rpc_call("Settings.SetSettingValue", params)
    return response and 'result' in response and response['result'] == 'OK'
