import httpx
import traceback

url = "https://www.milanuncios.com/casas-en-murcia/?demanda=s&vendedor=part"

def fetch():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as c:
            r = c.get(url, headers=headers)
            print("Status:", r.status_code)
            print("Final URL:", r.url)
            print("Headers:\n", r.headers)
            print("Body snippet:\n", r.text[:800])
    except Exception as e:
        print("EXCEPTION:")
        traceback.print_exc()

if __name__ == '__main__':
    fetch()
