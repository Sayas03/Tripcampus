"""Builds the static Trip Campus website from site-data.json.

Pure Python (standard library only), so it runs the same on a laptop and in AWS Lambda.
build(data, out_dir) writes every HTML page plus sitemap.xml, robots.txt and assets/js/config.js.
Images, CSS, fonts and main.js are static files uploaded once (see the site/ folder).
"""
import json, os, re
from html import escape as E
from urllib.parse import quote

_HERE = os.path.dirname(os.path.abspath(__file__))
_CODE = compile(open(os.path.join(_HERE, 'pages_code.py'), encoding='utf-8').read(), 'pages_code.py', 'exec')


def build(data, out_dir, api_url=''):
    os.makedirs(out_dir, exist_ok=True)
    g = {'__name__': 'tc_pages', 'DATA': data, 'OUT': out_dir.rstrip('/'), 'API_URL': api_url,
         'E': E, 'quote': quote, 'json': json, 'os': os, 're': re}
    exec(_CODE, g)
    return {'pages': list(g['pages']), 'warnings': list(g['WARN'])}


if __name__ == '__main__':
    import sys
    src, out = sys.argv[1], sys.argv[2]
    res = build(json.load(open(src, encoding='utf-8')), out, sys.argv[3] if len(sys.argv) > 3 else '')
    print(len(res['pages']), 'pages', res['warnings'])
