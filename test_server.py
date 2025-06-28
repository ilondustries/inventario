import requests
import sys

def test_server():
    urls = [
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    for url in urls:
        try:
            print(f"Probando {url}...")
            response = requests.get(url, timeout=5)
            print(f"✅ {url} - Status: {response.status_code}")
            print(f"   Contenido: {response.text[:100]}...")
        except requests.exceptions.ConnectionError:
            print(f"❌ {url} - Error de conexión")
        except requests.exceptions.Timeout:
            print(f"⏰ {url} - Timeout")
        except Exception as e:
            print(f"❌ {url} - Error: {e}")
        print()

if __name__ == "__main__":
    test_server() 