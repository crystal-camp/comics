#!/usr/bin/env python3
from __future__ import annotations
import json, html, re
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parent
COMICS=ROOT/'comics'
IMG_EXT={'.jpg','.jpeg','.png','.webp','.gif','.avif','.svg'}

def natural_key(s): return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)',s)]
def load_json(path,fallback=None):
    if not path.exists(): return fallback or {}
    try:return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e: print(f'WARN: {path}: {e}');return fallback or {}
def pretty_slug(slug):return re.sub(r'[-_]+',' ',slug).strip().title()
def esc(v):return html.escape(str(v or ''),quote=True)

def make_share_page(item,site):
    slug=item['slug'];folder=COMICS/slug
    site_url=(site.get('siteUrl') or '').rstrip('/')
    canonical=(f'{site_url}/comics/{quote(slug)}/' if site_url else f'../../reader.html?comic={quote(slug)}')
    image=(f'{site_url}/comics/{quote(slug)}/{quote(item["cover"])}' if site_url else quote(item['cover']))
    reader=(f'{site_url}/reader.html?comic={quote(slug)}' if site_url else f'../../reader.html?comic={quote(slug)}')
    page=f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(item['title'])} — {esc(site.get('siteName','Crystal Lake Comics'))}</title>
<meta name="description" content="{esc(item['description'])}"><meta property="og:type" content="article"><meta property="og:site_name" content="{esc(site.get('siteName','Crystal Lake Comics'))}"><meta property="og:title" content="{esc(item['title'])}"><meta property="og:description" content="{esc(item['description'])}"><meta property="og:image" content="{esc(image)}"><meta property="og:url" content="{esc(canonical)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(item['title'])}"><meta name="twitter:description" content="{esc(item['description'])}"><meta name="twitter:image" content="{esc(image)}"><link rel="canonical" href="{esc(canonical)}">
<script>location.replace({json.dumps(reader)});</script></head><body></body></html>'''
    (folder/'index.html').write_text(page,encoding='utf-8')

def main():
    COMICS.mkdir(exist_ok=True);site=load_json(ROOT/'site.config.json',{});items=[]
    for folder in sorted([p for p in COMICS.iterdir() if p.is_dir()],key=lambda p:natural_key(p.name)):
        meta=load_json(folder/'comic.json',{})
        images=sorted([p.name for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXT],key=natural_key)
        if not images: continue
        cover=meta.get('cover')
        if cover not in images:
            candidates=[n for n in images if Path(n).stem.lower() in {'cover','couverture','front','00','000'}]
            cover=candidates[0] if candidates else images[0]
        back=meta.get('backCover')
        excluded={cover,back}
        pages=[n for n in images if n not in excluded]
        theme=meta.get('theme','lake')
        if theme not in {'lake','forest','night','paper','blood'}: theme='lake'
        item={'slug':folder.name,'title':meta.get('title') or pretty_slug(folder.name),'subtitle':meta.get('subtitle','Une histoire de Crystal Lake'),'description':meta.get('description') or site.get('defaultDescription','Une histoire de Crystal Lake.'),'date':meta.get('date',''),'category':meta.get('category','stories'),'characters':meta.get('characters',[]),'tags':meta.get('tags',[]),'cover':cover,'backCover':back if back in images else None,'pages':pages,'pageCount':len(pages)+1+(1 if back in images else 0),'accent':meta.get('accent','#b8493f'),'theme':theme}
        items.append(item);make_share_page(item,site)
    payload={'site':site,'comics':sorted(items,key=lambda x:x.get('date',''),reverse=True)}
    (ROOT/'library.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'OK: {len(items)} comic(s) -> library.json')
if __name__=='__main__':main()
