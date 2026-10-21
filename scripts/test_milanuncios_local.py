import sys
import json

sys.path.append('.')

from app.sources.milanuncios_source import MilanunciosSource


def main():
    path = 'scripts/milanuncios_sample.html'
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    src = MilanunciosSource(url='http://local')
    items = src._extract_items_from_html(html, limit=10)
    if not items:
        print('No items parsed')
        return
    out = [item.to_dict() for item in items]
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
