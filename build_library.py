#!/usr/bin/env python3
from __future__ import annotations
import json, html, re
from pathlib import Path
from urllib.parse import quote
from PIL import Image, ImageOps

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


def make_discord_preview(item):
    """Crée une image 1200x630 réunissant couverture + première page."""
    folder = COMICS / item['slug']
    out = folder / 'discord-preview.jpg'

    names = [item.get('cover')]
    if item.get('pages'):
        names.append(item['pages'][0])
    else:
        names.append(item.get('cover'))

    try:
        imgs = []
        for name in names:
            if not name:
                raise ValueError("Image manquante")
            with Image.open(folder / name) as im:
                imgs.append(ImageOps.exif_transpose(im).convert('RGB'))

        # Format volontairement plus étroit : les deux pages 2:3 remplissent
        # presque toute l'image, avec seulement une petite séparation centrale.
        W, H = 900, 630
        gap = 6
        panel_w = (W - gap) // 2
        canvas = Image.new('RGB', (W, H), (5, 12, 10))

        for i, im in enumerate(imgs):
            # "contain" : aucune partie du comic n'est coupée.
            fitted = ImageOps.contain(im, (panel_w, H), Image.Resampling.LANCZOS)
            x0 = i * (panel_w + gap)
            x = x0 + (panel_w - fitted.width) // 2
            y = (H - fitted.height) // 2
            canvas.paste(fitted, (x, y))

        canvas.save(out, 'JPEG', quality=94, subsampling=0, optimize=True)
        return out.name
    except Exception as e:
        print(f'WARN preview {item["slug"]}: {e}')
        return None

def make_share_page(item,site):
    slug=item['slug']; folder=COMICS/slug
    site_url=(site.get('siteUrl') or 'https://crystal-camp.github.io/comics').rstrip('/')
    canonical=f'{site_url}/comics/{quote(slug)}/'
    preview_name=make_discord_preview(item)
    image_name=preview_name or item["cover"]
    image=f'{site_url}/comics/{quote(slug)}/{quote(image_name)}'
    reader=f'{site_url}/reader.html?comic={quote(slug)}'
    page=f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(item['title'])} — {esc(site.get('siteName','Crystal Lake Comics'))}</title>
<meta name="description" content="{esc(item['description'])}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{esc(site.get('siteName','Crystal Lake Comics'))}">
<meta property="og:title" content="{esc(item['title'])}">
<meta property="og:description" content="{esc(item['description'])}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(image)}">
<meta property="og:image:secure_url" content="{esc(image)}">
<meta property="og:image:width" content="900">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(item['title'])}">
<meta name="twitter:description" content="{esc(item['description'])}">
<meta name="twitter:image" content="{esc(image)}">
<script>location.replace({json.dumps(reader)});</script>
</head>
<body><p><a href="{esc(reader)}">Ouvrir {esc(item['title'])}</a></p></body>
</html>'''
    (folder/'index.html').write_text(page,encoding='utf-8')

def main():
    COMICS.mkdir(exist_ok=True);site=load_json(ROOT/'site.config.json',{});items=[]
    for folder in sorted([p for p in COMICS.iterdir() if p.is_dir()],key=lambda p:natural_key(p.name)):
        meta=load_json(folder/'comic.json',{})
        images=sorted([p.name for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXT and p.name != 'discord-preview.jpg'],key=natural_key)
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
