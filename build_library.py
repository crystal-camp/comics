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
        canvas = Image.new('RGB', (W, H), (5, 12, 10))

        # On donne d'abord la même hauteur maximale aux deux images.
        # Elles sont ensuite collées l'une à l'autre avec seulement `gap`
        # pixels entre elles, puis le duo entier est centré dans le canvas.
        ratios = [im.width / max(1, im.height) for im in imgs]
        widths = [r * H for r in ratios]
        total_w = sum(widths) + gap

        # Si un format très large dépasse le canvas, on réduit les deux
        # images ensemble afin de préserver leurs proportions.
        scale = min(1.0, W / total_w)
        target_h = max(1, round(H * scale))
        target_widths = [max(1, round(r * target_h)) for r in ratios]
        total_w = sum(target_widths) + gap

        x = (W - total_w) // 2
        for im, target_w in zip(imgs, target_widths):
            fitted = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            y = (H - target_h) // 2
            canvas.paste(fitted, (x, y))
            x += target_w + gap

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


def is_generated_or_auxiliary_image(name):
    stem = Path(name).stem.lower()
    # Fichiers créés par le site ou généralement utilisés comme visuels annexes.
    return (
        stem.startswith('discord-preview')
        or stem.startswith('social-preview')
        or stem.startswith('og-preview')
        or stem.startswith('share-preview')
        or stem.startswith('thumbnail')
        or stem.startswith('thumb-')
    )

def is_numbered_page(name):
    stem = Path(name).stem.lower().strip()
    # Formats acceptés : 1, 01, 001, page1, page-01, page_001, p01, p-01...
    return bool(re.fullmatch(r'(?:page|p)?[-_ ]?\d+', stem))

def main():
    COMICS.mkdir(exist_ok=True);site=load_json(ROOT/'site.config.json',{});items=[]
    for folder in sorted([p for p in COMICS.iterdir() if p.is_dir()],key=lambda p:natural_key(p.name)):
        meta=load_json(folder/'comic.json',{})
        images=sorted([
            p.name for p in folder.iterdir()
            if p.is_file()
            and p.suffix.lower() in IMG_EXT
            and not is_generated_or_auxiliary_image(p.name)
        ], key=natural_key)
        if not images: continue

        cover=meta.get('cover')
        if cover not in images:
            candidates=[n for n in images if Path(n).stem.lower() in {'cover','couverture','front','00','000'}]
            cover=candidates[0] if candidates else images[0]

        back=meta.get('backCover')
        excluded={cover,back}

        # Si "pages" est renseigné dans comic.json, cette liste est la vérité absolue.
        explicit_pages=meta.get('pages')
        if isinstance(explicit_pages,list) and explicit_pages:
            pages=[n for n in explicit_pages if isinstance(n,str) and n in images and n not in excluded]
        else:
            remaining=[n for n in images if n not in excluded]
            numbered=[n for n in remaining if is_numbered_page(n)]
            # Convention normale du projet : pages numérotées.
            # Fallback pour ne pas casser un ancien comic aux noms libres :
            # si aucune page n'est numérotée, on conserve les images restantes.
            pages=numbered if numbered else remaining
        theme=meta.get('theme','lake')
        if theme not in {'lake','forest','night','paper','blood'}: theme='lake'
        item={'slug':folder.name,'title':meta.get('title') or pretty_slug(folder.name),'subtitle':meta.get('subtitle','Une histoire de Crystal Lake'),'description':meta.get('description') or site.get('defaultDescription','Une histoire de Crystal Lake.'),'date':meta.get('date',''),'category':meta.get('category','stories'),'characters':meta.get('characters',[]),'tags':meta.get('tags',[]),'cover':cover,'backCover':back if back in images else None,'pages':pages,'pageCount':len(pages)+1+(1 if back in images else 0),'accent':meta.get('accent','#b8493f'),'theme':theme}
        items.append(item);make_share_page(item,site)
    payload={'site':site,'comics':sorted(items,key=lambda x:x.get('date',''),reverse=True)}
    (ROOT/'library.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'OK: {len(items)} comic(s) -> library.json')
if __name__=='__main__':main()
