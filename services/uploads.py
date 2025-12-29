import requests
from config import FREEIMAGE_API_KEY

def subir_foto_nube(archivo):
    url = "https://freeimage.host/api/1/upload"
    payload = {"key": FREEIMAGE_API_KEY, "action": "upload", "format": "json"}
    archivo.seek(0)
    files = {"source": archivo.read()}

    response = requests.post(url, data=payload, files=files)
    if response.status_code == 200:
        return response.json()['image']['url']
    return None
