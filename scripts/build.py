# -*- coding: utf-8 -*-
"""Build the Apollinaria portfolio using content from posmm and the ksu template."""
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'source-content'
DATA = json.loads((SOURCE / 'content.json').read_text())
TEMPLATE = (ROOT / 'ksu/index.html').read_text()
OPTIMIZATION_FILE = SOURCE / 'image-optimization.json'
OPTIMIZED_IMAGES = {
    item['output']: item['sha256'][:12]
    for item in json.loads(OPTIMIZATION_FILE.read_text())['images']
} if OPTIMIZATION_FILE.exists() else {}

def esc(value):
    return html.escape(str(value), quote=True)

def copy_media(path, name):
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

def document(title, description, body, path):
    output = f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#f8f7f3"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:image" content="{portrait}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/fonts.css"><link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/motion.css"><script src="/assets/site.js" defer></script></head><body>{header()}<main id="main">{body}</main>{footer()}</body></html>'''
    # The custom domain uses Cloudflare caching. Version image URLs by content so
    # a published optimization also reaches returning visitors immediately.
    for image_path, version in OPTIMIZED_IMAGES.items():
        output = output.replace('="/' + image_path + '"', '="/' + image_path + '?v=' + version + '"')
    (ROOT / path).write_text(output + '\n')

hero = '''<section class="hero" id="hero-section" aria-labelledby="hero-title"><div class="container hero-inner"><img class="hero-shape star" src="/assets/images/star.webp" alt="" width="160" height="160" draggable="false"><img class="hero-shape lightning" src="/assets/images/lightning.webp" alt="" width="140" height="140" draggable="false"><h1 id="hero-title"><span>BRAND</span> <span>CONTENT</span></h1><div class="hero-bottom"><span class="hero-year">©2026</span><span class="hero-name">/АПОЛЛИНАРИЯ ПИЛИПЮК</span></div></div></section>'''
about = f'''<section class="about section" id="bio-section"><div class="container about-layout"><div class="about-intro"><h2>Обо мне.</h2><p class="intro-name">Аполлинария<br>Пилипюк</p><span class="eyebrow">/SMM-специалист</span></div><div class="about-copy"><p class="lead">{esc(DATA['about'][0])}</p><a class="text-link" href="#projects">Смотреть проекты<span class="arrow-box">{ARROW}</span></a></div></div></section>'''
portrait_scene = f'''<div class="portrait-track"><div class="portrait-sticky"><div class="portrait-enter"><div class="portrait-card"><div class="portrait-face portrait-front"><img src="{portrait}" alt="Аполлинария Пилипюк" width="1396" height="1980" fetchpriority="high"></div><div class="portrait-face portrait-back" aria-hidden="true"><img src="{portrait}" alt="" width="1396" height="1980"></div></div></div></div></div>'''
intro_scene = '<div class="intro-scene">' + portrait_scene + hero + about + '</div>'
statement = f'''<section class="statement"><div class="container"><p class="scroll-statement">{esc(DATA['about'][1])}</p></div></section>'''
values = f'''<section class="values section" id="values"><div class="container"><div class="values-heading"><span class="eyebrow">/Итоги и ценность моей работы</span><h2>Контент с фокусом<br>на результат.</h2></div><div class="values-grid">{''.join(f'<article class="value"><span class="value-index">/0{i + 1}</span><p>{esc(value)}</p></article>' for i, value in enumerate(DATA['values']))}</div></div></section>'''
document('Аполлинария Пилипюк — SMM-специалист', 'Портфолио Аполлинарии Пилипюк: SMM и контент для LUKOIL, PUMA, DISKOKRAS, NSCom, Sankari Motors и других брендов.', intro_scene + statement + values + projects_section() + contact(), 'index.html')
work_intro = '<div class="container work-intro"><a class="back-link" href="/index.html">← На главную</a><p class="lead">От нефтегазовой отрасли и IT до моды, спорта и образования.</p></div>'
document('Проекты — Аполлинария Пилипюк', 'Семь проектов Аполлинарии Пилипюк: описания брендов, направления контента, фотографии и видео.', work_intro + projects_section(True) + contact(), 'work.html')

for index, project in enumerate(DATA['projects']):
    next_project = DATA['projects'][(index + 1) % len(DATA['projects'])]
    name = esc(project['name'])
    logo = f'<img class="detail-logo" src="{project["logo_file"]}" alt="Логотип {name}">' if project['logo_file'] else ''
    tone = ' light' if project['light'] else ''
    images = ''.join(f'<figure class="gallery-image"><a href="{path}" target="_blank" rel="noopener" aria-label="Открыть изображение PUMA {i + 1} в полном размере"><img src="{path}" alt="PUMA — пример публикации {i + 1}" loading="lazy" width="900" height="1600"></a></figure>' for i, path in enumerate(project['image_files']))
    videos = ''.join(f'<figure class="gallery-video"><video controls playsinline preload="metadata" aria-label="{name} — видео {i + 1}"><source src="{path}" type="video/{"mp4" if path.endswith("mp4") else "webm"}"></video><figcaption>/{i + 1:02d} · {name}</figcaption></figure>' for i, path in enumerate(project['video_files']))
    gallery = (f'<section class="section gallery container"><div class="section-heading"><h2>Примеры<br>контента.</h2><span class="eyebrow">/{name}</span></div>' + (f'<div class="image-gallery">{images}</div>' if images else '') + (f'<div class="video-gallery">{videos}</div>' if videos else '') + '</section>') if images or videos else ''
    detail = f'''<section class="detail-intro container"><a class="back-link" href="/work.html">← Все проекты</a><div class="detail-heading"><span class="eyebrow">/{index + 1:02d} · {esc(project['category'])}</span><h1>{name}</h1></div><div class="detail-layout"><div class="detail-copy">{logo}<p class="lead">{esc(project['description'])}</p><p>{esc(project['focus'])}</p>{external(project['url'], '@' + esc(project['handle']), 'text-link')}<span class="eyebrow detail-role">/SMM · Контент</span></div><div class="detail-cover{tone}" style="--project-color:{project['color']}"><img src="{project['cover']}" alt="Instagram-профиль {name}" width="1260" height="2800"></div></div></section>{gallery}<section class="next-project container"><span class="eyebrow">/Следующий проект</span><a href="/work/{next_project['slug']}.html">{esc(next_project['name'])}{ARROW}</a></section>'''
    document(project['name'] + ' — Аполлинария Пилипюк', project['description'] + ' ' + project['focus'], detail + contact(), 'work/' + project['slug'] + '.html')

# Publish only the completed portfolio, keeping both source sites out of the build.
dist = ROOT / 'dist'
dist.mkdir(exist_ok=True)
for filename in ['index.html', 'work.html']:
    shutil.copyfile(ROOT / filename, dist / filename)
for directory in ['assets', 'work']:
    shutil.copytree(ROOT / directory, dist / directory, dirs_exist_ok=True)
print('Built dist/: home, project index, 7 project pages and all source media.')
