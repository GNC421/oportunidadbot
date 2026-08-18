import sys
import json

sys.path.append('.')

from app.sources.milanuncios_source import MilanunciosSource


def main():
    url = "https://www.milanuncios.com/casas-en-murcia/?demanda=s&vendedor=part"
    src = MilanunciosSource(url=url)
    items = src.parse_items(limit=5)
    if not items:
        print("No items parsed")
        return
    out = [item.to_dict() for item in items]
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
