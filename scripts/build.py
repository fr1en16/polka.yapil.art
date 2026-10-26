# -*- coding: utf-8 -*-
"""Build the Apollinaria portfolio using content from posmm and the ksu template."""
import html
import json
import re
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'source-content'
DATA = json.loads((SOURCE / 'content.json').read_text())
TEMPLATE = (ROOT / 'ksu/index.html').read_text()
OPTIMIZATION_FILE = SOURCE / 'image-optimization.json'
OPTIMIZED_IMAGES = {
    item['output']: item['sha256'][:12]
    for item in json.loads(OPTIMIZATION_FILE.read_text())['images']
} if OPTIMIZATION_FILE.exists() else {}
VIDEO_FILE = SOURCE / 'video-optimization.json'
VIDEO_MANIFEST = json.loads(VIDEO_FILE.read_text()) if VIDEO_FILE.exists() else {'videos': []}
VIDEO_OPTIMIZATIONS = {item['name']: item for item in VIDEO_MANIFEST['videos']}
ASSET_VERSIONS = dict(OPTIMIZED_IMAGES)
for item in VIDEO_MANIFEST['videos']:
    ASSET_VERSIONS[item['output']] = item['sha256'][:12]
    ASSET_VERSIONS[item['poster']] = item['poster_sha256'][:12]
SOCIAL_IMAGE = ROOT / 'assets/social/brand-content.png'
if SOCIAL_IMAGE.is_file():
    ASSET_VERSIONS['assets/social/brand-content.png'] = hashlib.sha256(SOCIAL_IMAGE.read_bytes()).hexdigest()[:12]
SITE_URL = 'https://polka.yapil.art'
SITE_NAME = 'Аполлинария Пилипюк — BRAND CONTENT'
FIRST_PUBLISHED = '2026-10-27T00:25:42+05:00'
UPDATED = datetime.now(ZoneInfo('Asia/Qostanay')).isoformat(timespec='seconds')
SEO_PAGES = []

def asset_url(path, absolute=False):
    path = '/' + path.lstrip('/')
    version = ASSET_VERSIONS.get(path.lstrip('/'))
    url = path + ('?v=' + version if version else '')
    return (SITE_URL if absolute else '') + url

def esc(value):
    return html.escape(str(value), quote=True)

def copy_media(path, name):
    if name in VIDEO_OPTIMIZATIONS:
        target = ROOT / VIDEO_OPTIMIZATIONS[name]['output']
        if not target.is_file():
            raise FileNotFoundError('Missing optimized video: ' + str(target))
        return '/' + VIDEO_OPTIMIZATIONS[name]['output']
    source = SOURCE / path
    # Some original .webm assets actually contain MP4; use the correct extension.
    extension = '.mp4' if source.read_bytes()[4:8] == b'ftyp' else source.suffix
    target = ROOT / 'assets/media' / (name + extension)
    if target.relative_to(ROOT).as_posix() in OPTIMIZED_IMAGES:
        if not target.is_file():
            raise FileNotFoundError('Missing Tinify image: ' + str(target))
        return '/assets/media/' + target.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return '/assets/media/' + target.name

portrait = copy_media(DATA['portrait'], 'apollinaria-pilipyuk')
slugs = ['lukoil', 'puma', 'diskokras', 'nscom', 'sankari-motors', 'klimakin-motoschool', 'alexandr-kuguyenko']
SEO_DESCRIPTIONS = {
    'lukoil': 'SMM и контент для LUKOIL: фирменные масла, новинки, акции и открытие пунктов замены масел. Проект в портфолио Аполлинарии Пилипюк, примеры видео.',
    'puma': 'SMM и контент для PUMA в Казахстане: спортивная экипировка, локальные кампании и коллаборации. Фото и видео в портфолио Аполлинарии Пилипюк.',
    'diskokras': 'Контент для DISKOKRAS: ремонт и покраска дисков, реставрация, примеры до и после и советы по уходу. SMM-проект Аполлинарии Пилипюк.',
    'nscom': 'SMM для NSCom: IT-инфраструктура, дата-центр, кибербезопасность и облачные решения. Контент для бизнеса в портфолио Аполлинарии Пилипюк.',
    'sankari-motors': 'Контент для Sankari Motors: японская спецтехника и погрузчики в Казахстане, надёжность и выгода для бизнеса. SMM-проект Аполлинарии Пилипюк.',
    'klimakin-motoschool': 'SMM-проект Klimakin Motoschool: обучение вождению мотоциклов, безопасность, инструкторы и сообщество байкеров. Портфолио Аполлинарии Пилипюк.',
    'alexandr-kuguyenko': 'Продвижение личного бренда Alexandr Kuguyenko в логистике: экспертный имидж, деловой контент и клиентские кейсы. Проект Аполлинарии Пилипюк.',
}
categories = ['Масла и смазочные материалы', 'Спорт и lifestyle', 'Автосервис и детейлинг', 'IT и инфраструктура', 'Спецтехника', 'Образование и мотоспорт', 'Личный бренд и логистика']
colors = ['#ce0e2d', '#e7f254', '#242424', '#e4b808', '#f1d937', '#bf1518', '#1553bf']
for index, project in enumerate(DATA['projects']):
    slug = slugs[index]
    project.update(slug=slug, category=categories[index], color=colors[index], light=index in [1, 3, 4])
    project['cover'] = copy_media(project['screenshot'], slug + '-profile')
    project['logo_file'] = copy_media(project['logo'], slug + '-logo') if project['logo'] else None
    project['image_files'] = [copy_media(path, slug + '-post-' + str(i + 1)) for i, path in enumerate(project['images'])]
    project['video_files'] = [copy_media(path, slug + '-video-' + str(i + 1)) for i, path in enumerate(project['videos'])]

# Retain the local fonts and decorative shapes from the supplied ksu export.
font_rules = []
for rule in re.findall(r'@font-face\s*\{[^}]+\}', TEMPLATE):
    if 'Placeholder' in rule or not any('"' + family + '"' in rule for family in ['Archivo', 'Inter']):
        continue
    if 'font-style: italic' in rule or 'font-style:italic' in rule:
        continue
    if not any('font-weight: ' + weight in rule for weight in ['400', '500', '600', '700', '800']):
        continue
    for filename in re.findall(r'assets/fonts/([^"\)]+)', rule):
        shutil.copyfile(ROOT / 'ksu/assets/fonts' / filename, ROOT / 'assets/fonts' / filename)
    font_rules.append(rule.replace('assets/fonts/', './fonts/'))
(ROOT / 'assets/fonts.css').write_text('\n'.join(font_rules) + '\n')

for target_name in ['star.webp', 'lightning.webp']:
    target_path = ROOT / 'assets/images' / target_name
    # WebP conversion is performed by Tinify; do not rename an original PNG.
    if not target_path.is_file():
        raise FileNotFoundError('Missing Tinify WebP: ' + str(target_path))

ARROW = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 19 19 5M5 5h14v14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
WHATSAPP = DATA['contacts']['whatsapp']
TELEGRAM = DATA['contacts']['telegram']

def external(url, label, cls=''):
    return f'<a class="{cls}" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{label}{ARROW}</a>'

def header():
    return '''<a class="skip-link" href="#main">К содержимому</a>
<header class="site-header"><nav class="floating-nav" aria-label="Основная навигация">
<div class="nav-top"><a class="brand" href="/index.html#hero-section">Аполлинария</a>
<button class="menu-toggle" aria-label="Открыть меню" aria-expanded="false" aria-controls="nav-menu"><span></span><span></span><span></span></button></div>
<div class="nav-menu" id="nav-menu" hidden><a href="/index.html#bio-section">Обо мне</a><a href="/index.html#values">Подход</a><a href="/work.html">Проекты</a><a href="/index.html#contact">Контакты</a></div>
</nav></header>'''

def contact():
    return f'''<section class="contact section" id="contact"><div class="container contact-layout">
<h2>Давайте<br>поговорим.</h2><div class="contact-copy"><p>Обсудим ваш проект?</p><p class="muted">Напишите мне в удобном мессенджере.</p><div class="contact-links">{external(WHATSAPP, 'WhatsApp', 'button')}{external(TELEGRAM, 'Telegram', 'button')}</div></div>
</div></section>'''

def footer():
    return f'''<footer class="footer"><div class="container"><div class="footer-top"><h2>Контент,<br>который работает<br>на результат.</h2><div class="footer-links"><span class="eyebrow">/Навигация</span><a href="/index.html#hero-section">Главная</a><a href="/index.html#bio-section">Обо мне</a><a href="/work.html">Проекты</a><a href="/index.html#contact">Контакты</a></div><div class="footer-links"><span class="eyebrow">/Связаться</span>{external(WHATSAPP, 'WhatsApp')}{external(TELEGRAM, 'Telegram')}</div></div><a class="footer-wordmark" href="/index.html#hero-section" aria-label="Аполлинария — на главную">АПОЛЛИНАРИЯ</a><div class="footer-bottom"><span>Аполлинария Пилипюк</span><span>©2026 · SMM-портфолио</span></div></div></footer>'''

def card(project, index):
    name = esc(project['name'])
    tone = ' light' if project['light'] else ''
    return f'''<a class="project-card reveal" href="/work/{project['slug']}.html" aria-label="{name} — смотреть проект">
<div class="project-visual{tone}" style="--project-color:{project['color']}"><div class="project-brand">{name}</div><span class="project-number">/{index + 1:02d}</span><img class="project-phone" src="{project['cover']}" alt="Instagram-профиль {name}" loading="lazy" width="1260" height="2800"><span class="project-open">{ARROW}</span></div>
<div class="project-caption"><div><h3>{name}</h3><p>{esc(project['category'])}</p></div><span class="caption-arrow">{ARROW}</span></div></a>'''

def projects_section(all_work=False):
    cards = ''.join(card(project, index) for index, project in enumerate(DATA['projects']))
    title = 'Все проекты.' if all_work else 'Мои<br>проекты.'
    tag = 'h1' if all_work else 'h2'
    return f'''<section class="projects section" id="projects"><div class="container"><div class="section-heading"><{tag} class="section-title">{title}</{tag}><span class="eyebrow">/07 проектов</span></div><div class="projects-grid">{cards}</div></div></section>'''

def document(title, description, body, path, project=None):
    canonical = SITE_URL + ('/' if path == 'index.html' else '/' + path)
    person_id = SITE_URL + '/#apollinaria'
    website_id = SITE_URL + '/#website'
    page_id = canonical + '#webpage'
    person = {'@type': 'Person', '@id': person_id, 'name': DATA['name'],
              'jobTitle': DATA['role'], 'url': SITE_URL + '/',
              'image': asset_url(portrait, True), 'telephone': '+77478831903',
              'sameAs': [TELEGRAM], 'knowsAbout': ['SMM', 'Контент для брендов', 'Социальные сети']}
    website = {'@type': 'WebSite', '@id': website_id, 'url': SITE_URL + '/',
               'name': SITE_NAME, 'inLanguage': 'ru', 'publisher': {'@id': person_id}}
    webpage = {'@type': 'ProfilePage' if path == 'index.html' else 'CollectionPage' if not project else 'WebPage',
               '@id': page_id, 'url': canonical, 'name': title, 'description': description,
               'inLanguage': 'ru', 'isPartOf': {'@id': website_id},
               'dateModified': UPDATED, 'author': {'@id': person_id}}
    graph = [person, website, webpage]
    breadcrumbs = [{'@type': 'ListItem', 'position': 1, 'name': 'Главная', 'item': SITE_URL + '/'}]
    videos = []
    if path == 'index.html':
        webpage['mainEntity'] = {'@id': person_id}
    else:
        breadcrumbs.append({'@type': 'ListItem', 'position': 2, 'name': 'Проекты', 'item': SITE_URL + '/work.html'})
    if project:
        work_id = canonical + '#project'
        work = {'@type': 'CreativeWork', '@id': work_id, 'name': project['name'] + ' — SMM и контент',
                'url': canonical, 'description': description, 'genre': project['category'],
                'creator': {'@id': person_id}, 'image': asset_url(project['cover'], True),
                'mainEntityOfPage': {'@id': page_id}}
        webpage['mainEntity'] = {'@id': work_id}
        graph.append(work)
        breadcrumbs.append({'@type': 'ListItem', 'position': 3, 'name': project['name'], 'item': canonical})
        for index, video_path in enumerate(project['video_files']):
            key = Path(video_path).stem
            metadata = VIDEO_OPTIMIZATIONS.get(key)
            if not metadata:
                continue
            name = project['name'] + ' — видеоконтент ' + str(index + 1)
            video = {'@type': 'VideoObject', '@id': canonical + '#video-' + str(index + 1),
                     'name': name,
                     'description': 'Ролик №' + str(index + 1) + ' для ' + project['name'] + ' в портфолио Аполлинарии Пилипюк. ' + project['focus'],
                     'thumbnailUrl': [asset_url(metadata['poster'], True)],
                     'uploadDate': FIRST_PUBLISHED, 'duration': 'PT' + str(metadata['duration']) + 'S',
                     'contentUrl': asset_url(metadata['output'], True),
                     'isPartOf': {'@id': work_id}, 'creator': {'@id': person_id}}
            videos.append(video)
            graph.append(video)
        if videos:
            work['hasPart'] = [{'@id': video['@id']} for video in videos]
    else:
        item_list = {'@type': 'ItemList', '@id': canonical + '#projects', 'name': 'Проекты Аполлинарии Пилипюк',
                     'numberOfItems': len(DATA['projects']), 'itemListElement': [
                         {'@type': 'ListItem', 'position': index + 1, 'name': item['name'],
                          'url': SITE_URL + '/work/' + item['slug'] + '.html'}
                         for index, item in enumerate(DATA['projects'])]}
        graph.append(item_list)
        if path != 'index.html':
            webpage['mainEntity'] = {'@id': item_list['@id']}
    if len(breadcrumbs) > 1:
        graph.append({'@type': 'BreadcrumbList', '@id': canonical + '#breadcrumbs', 'itemListElement': breadcrumbs})
        webpage['breadcrumb'] = {'@id': canonical + '#breadcrumbs'}
    structured = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False).replace('<', '\\u003c')
    font = 'font-be1d4c1a.woff2' if path == 'index.html' else 'font-34c75c25.woff2'
    social_image = asset_url('/assets/social/brand-content.png', True)
    output = f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#f8f7f3"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="author" content="Аполлинария Пилипюк"><meta name="robots" content="index,follow,max-image-preview:large,max-video-preview:-1"><link rel="canonical" href="{canonical}"><meta property="og:type" content="website"><meta property="og:locale" content="ru_RU"><meta property="og:site_name" content="{SITE_NAME}"><meta property="og:url" content="{canonical}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:image" content="{social_image}"><meta property="og:image:secure_url" content="{social_image}"><meta property="og:image:type" content="image/png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Аполлинария Пилипюк — BRAND CONTENT, SMM и контент для брендов"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{social_image}"><meta name="twitter:image:alt" content="Аполлинария Пилипюк — BRAND CONTENT"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="preload" href="/assets/fonts/{font}" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="/assets/fonts.css"><link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/motion.css"><script type="application/ld+json">{structured}</script><script src="/assets/site.js" defer></script></head><body>{header()}<main id="main">{body}</main>{footer()}</body></html>'''
    # The custom domain uses Cloudflare caching. Version image URLs by content so
    # a published optimization also reaches returning visitors immediately.
    output = output.replace('/index.html#', '/#').replace('href="/index.html"', 'href="/"')
    for image_path, version in ASSET_VERSIONS.items():
        output = output.replace('="/' + image_path + '"', '="/' + image_path + '?v=' + version + '"')
    (ROOT / path).write_text(output + '\n')
    image_paths = ([project['cover'], *project['image_files']] if project else [portrait, *[item['cover'] for item in DATA['projects']]])
    SEO_PAGES.append({'url': canonical, 'path': path, 'videos': videos,
                      'images': list(dict.fromkeys(asset_url(image, True) for image in image_paths))})

hero = '''<section class="hero" id="hero-section" aria-labelledby="hero-title"><div class="container hero-inner"><img class="hero-shape star" src="/assets/images/star.webp" alt="" width="160" height="160" draggable="false"><img class="hero-shape lightning" src="/assets/images/lightning.webp" alt="" width="140" height="140" draggable="false"><h1 id="hero-title"><span>BRAND</span> <span>CONTENT</span></h1><div class="hero-bottom"><span class="hero-year">©2026</span><span class="hero-name">/АПОЛЛИНАРИЯ ПИЛИПЮК</span></div></div></section>'''
about = f'''<section class="about section" id="bio-section"><div class="container about-layout"><div class="about-intro"><h2>Обо мне.</h2><p class="intro-name">Аполлинария<br>Пилипюк</p><span class="eyebrow">/SMM-специалист</span></div><div class="about-copy"><p class="lead">{esc(DATA['about'][0])}</p><a class="text-link" href="#projects">Смотреть проекты<span class="arrow-box">{ARROW}</span></a></div></div></section>'''
portrait_scene = f'''<div class="portrait-track"><div class="portrait-sticky"><div class="portrait-enter"><div class="portrait-card"><div class="portrait-face portrait-front"><img src="{portrait}" alt="Аполлинария Пилипюк" width="1396" height="1980" fetchpriority="high"></div><div class="portrait-face portrait-back" aria-hidden="true"><img src="{portrait}" alt="" width="1396" height="1980"></div></div></div></div></div>'''
intro_scene = '<div class="intro-scene">' + portrait_scene + hero + about + '</div>'
statement = f'''<section class="statement"><div class="container"><p class="scroll-statement">{esc(DATA['about'][1])}</p></div></section>'''
values = f'''<section class="values section" id="values"><div class="container"><div class="values-heading"><span class="eyebrow">/Итоги и ценность моей работы</span><h2>Контент с фокусом<br>на результат.</h2></div><div class="values-grid">{''.join(f'<article class="value"><span class="value-index">/0{i + 1}</span><p>{esc(value)}</p></article>' for i, value in enumerate(DATA['values']))}</div></div></section>'''
document('Аполлинария Пилипюк — SMM и контент для брендов', 'Портфолио Аполлинарии Пилипюк: SMM и контент для LUKOIL, PUMA, DISKOKRAS, NSCom, Sankari Motors и других брендов. Проекты, фото и видео, контакты.', intro_scene + statement + values + projects_section() + contact(), 'index.html')
work_intro = '<div class="container work-intro"><a class="back-link" href="/index.html">← На главную</a><p class="lead">От нефтегазовой отрасли и IT до моды, спорта и образования.</p></div>'
document('Проекты — Аполлинария Пилипюк', 'Семь проектов Аполлинарии Пилипюк: описания брендов, направления контента, фотографии и видео.', work_intro + projects_section(True) + contact(), 'work.html')

for index, project in enumerate(DATA['projects']):
    next_project = DATA['projects'][(index + 1) % len(DATA['projects'])]
    name = esc(project['name'])
    logo = f'<img class="detail-logo" src="{project["logo_file"]}" alt="Логотип {name}">' if project['logo_file'] else ''
    tone = ' light' if project['light'] else ''
    images = ''.join(f'<figure class="gallery-image"><a href="{path}" target="_blank" rel="noopener" aria-label="Открыть изображение PUMA {i + 1} в полном размере"><img src="{path}" alt="PUMA — пример публикации {i + 1}" loading="lazy" width="900" height="1600"></a></figure>' for i, path in enumerate(project['image_files']))
    video_cards = []
    for i, video_path in enumerate(project['video_files']):
        metadata = VIDEO_OPTIMIZATIONS.get(Path(video_path).stem, {})
        poster = ' poster="/' + metadata['poster'] + '"' if metadata.get('poster') else ''
        width, height = metadata.get('width', 1080), metadata.get('height', 1920)
        seconds = round(metadata.get('duration', 0))
        length = f'{seconds // 60}:{seconds % 60:02d}' if seconds else ''
        video_cards.append(f'<figure class="gallery-video" id="video-{i + 1}"><video controls playsinline preload="none" loading="lazy"{poster} width="{width}" height="{height}" aria-label="{name} — видео {i + 1}"><source src="{video_path}" type="video/{"mp4" if video_path.endswith("mp4") else "webm"}"></video><figcaption><span>/{i + 1:02d} · {name}</span><span>{length}</span></figcaption></figure>')
    videos = ''.join(video_cards)
    gallery = (f'<section class="section gallery container"><div class="section-heading"><h2>Примеры<br>контента.</h2><span class="eyebrow">/{name}</span></div>' + (f'<div class="image-gallery">{images}</div>' if images else '') + (f'<div class="video-gallery">{videos}</div>' if videos else '') + '</section>') if images or videos else ''
    detail = f'''<section class="detail-intro container"><a class="back-link" href="/work.html">← Все проекты</a><div class="detail-heading"><span class="eyebrow">/{index + 1:02d} · {esc(project['category'])}</span><h1>{name}</h1></div><div class="detail-layout"><div class="detail-copy">{logo}<p class="lead">{esc(project['description'])}</p><p>{esc(project['focus'])}</p>{external(project['url'], '@' + esc(project['handle']), 'text-link')}<span class="eyebrow detail-role">/SMM · Контент</span></div><div class="detail-cover{tone}" style="--project-color:{project['color']}"><img src="{project['cover']}" alt="Instagram-профиль {name}" width="1260" height="2800"></div></div></section>{gallery}<section class="next-project container"><span class="eyebrow">/Следующий проект</span><a href="/work/{next_project['slug']}.html">{esc(next_project['name'])}{ARROW}</a></section>'''
    document(project['name'] + ' — SMM-проект | Аполлинария Пилипюк', SEO_DESCRIPTIONS[project['slug']], detail + contact(), 'work/' + project['slug'] + '.html', project=project)

# Public discovery files use the same canonical host and asset URLs as the pages.
SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
IMAGE_NS = 'http://www.google.com/schemas/sitemap-image/1.1'
VIDEO_NS = 'http://www.google.com/schemas/sitemap-video/1.1'
ET.register_namespace('', SITEMAP_NS)
ET.register_namespace('image', IMAGE_NS)
ET.register_namespace('video', VIDEO_NS)
sitemap = ET.Element('{' + SITEMAP_NS + '}urlset')
video_sitemap = ET.Element('{' + SITEMAP_NS + '}urlset')
for page in SEO_PAGES:
    item = ET.SubElement(sitemap, '{' + SITEMAP_NS + '}url')
    ET.SubElement(item, '{' + SITEMAP_NS + '}loc').text = page['url']
    ET.SubElement(item, '{' + SITEMAP_NS + '}lastmod').text = UPDATED
    for image in page['images']:
        image_item = ET.SubElement(item, '{' + IMAGE_NS + '}image')
        ET.SubElement(image_item, '{' + IMAGE_NS + '}loc').text = image
    if page['videos']:
        watch_page = ET.SubElement(video_sitemap, '{' + SITEMAP_NS + '}url')
        ET.SubElement(watch_page, '{' + SITEMAP_NS + '}loc').text = page['url']
        for video in page['videos']:
            video_item = ET.SubElement(watch_page, '{' + VIDEO_NS + '}video')
            fields = {'thumbnail_loc': video['thumbnailUrl'][0], 'title': video['name'],
                      'description': video['description'], 'content_loc': video['contentUrl'],
                      'duration': str(max(1, round(float(video['duration'][2:-1])))),
                      'publication_date': video['uploadDate']}
            for key, value in fields.items():
                ET.SubElement(video_item, '{' + VIDEO_NS + '}' + key).text = value
ET.ElementTree(sitemap).write(ROOT / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
ET.ElementTree(video_sitemap).write(ROOT / 'video-sitemap.xml', encoding='utf-8', xml_declaration=True)
(ROOT / 'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: ' + SITE_URL + '/sitemap.xml\nSitemap: ' + SITE_URL + '/video-sitemap.xml\n')

# Publish only the completed portfolio, keeping both source sites out of the build.
dist = ROOT / 'dist'
dist.mkdir(exist_ok=True)
for filename in ['index.html', 'work.html', 'robots.txt', 'sitemap.xml', 'video-sitemap.xml']:
    shutil.copyfile(ROOT / filename, dist / filename)
for directory in ['assets', 'work']:
    shutil.copytree(ROOT / directory, dist / directory, dirs_exist_ok=True)
print('Built dist/: home, project index, 7 project pages and all source media.')
