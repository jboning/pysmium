from flask import g, render_template, request
from jinja2 import Markup

from pysmium import app, config, path_root
from pysmium.constants import CSS_STATICVER, STATICVER

@app.before_request
def chrome_init():
    g.js_urls = []
    g.js_snippets = []
    g.js_data = {}
    pass


def sprite(alt, x, y, grid_w, grid_h=None, w=None, h=None):
    if grid_h is None:
        grid_h = grid_w
    if w is None:
        w = grid_w
    if h is None:
        h = w

    posx = x * w
    posy = y * h
    imgw = 1024 * w / grid_w
    imgh = 1024 * h / grid_h

    return render('sprite.html',
                  w=w, h=h,
                  imgw=imgw, imgh=imgh,
                  posx=posx, posy=posy,
                  alt=alt)


def static_url(static_file):
    return "/static/%s?ver=%d" % (static_file, STATICVER)

def css_url(css_file):
    return "/static/%s?ver=%d" % (css_file, CSS_STATICVER)

def js_url(js_file):
    return "/static/%s?ver=%d" % (js_file, JS_STATICVER)


def include_js_url(url):
    g.js_urls.append(url)

def include_js_snippet(file):
    g.js_snippets.append(file)

def add_js_data(key, val):
    g.js_data[key] = val

def snippets_url():
    if not g.js_snippets:
        return None
    g.js_snippets.sort()
    combined_name = '|'.join(g.js_snippets)

    # TODO: skip this if destination exists already

    js_snippet_data = ""
    for name in g.js_snippets:
        with open('%s/snippets/%s.js' % (path_root, name)) as f:
            js_snippet_data += f.read()
    
    with open('%s/static/cache/%s.js' % (path_root, combined_name), 'w') as f:
        f.write(js_snippet_data)

    # TODO: minify

    return '/static/cache/%s.js' % combined_name

def js_data():
    build = "<div id='osmium-data' "
    for k, v in g.js_data.items():
        build += "data-%s='%s'" % (k, v)
    build += "></div>"
    return build

def header(title='', index=True, extra_head_tags=''):
    # TODO: use index

    osmium_name = config.get('branding', 'name')
    if title:
        title = title + " / " + osmium_name
    else:
        title = osmium_name + " / " + config.get('branding', 'description')

    g.xhtml = "application/xhtml+xml" in request.headers.get('Accept', "")

    # TODO notifications

    themes = {'Dark': 'dark.css', 'Light': 'light.css'}
    theme = request.cookies.get('t')
    if theme not in themes:
        theme = 'Dark'
    theme_url = css_url(themes[theme])

    favicon = config.get('branding', 'favicon')
    if not favicon.startswith('//'):
        favicon = static_url(favicon)

    # TODO logged in?

    include_js_snippet('persistent_theme')
    include_js_snippet('notifications')
    include_js_snippet('feedback')

    
    parts = request.path[1:].split('/')
    if len(parts) <= 1:
        add_js_data('relative', '.')
    else:
        add_js_data('relative', '/'.join(['..'] * len(parts)))

    return render('header.html',
                  osmium=osmium_name,
                  index=index,
                  title=title,
                  theme_url=theme_url,
                  favicon_url=favicon,
                  is_current=is_current,
                  extra_head_tags=extra_head_tags,
                 )

def is_current(path):
    return path == request.path

def footer():
    return render('footer.html',
                  osmium_version=9999, # XXX
                  js_urls=g.js_urls,
                  js_snippets_url=snippets_url(),
                  js_data=js_data(),
                 )

def render(template, **kwargs):
    rendered = render_template(template,
                               static_url=static_url,
                               sprite=sprite,
                               **kwargs
                              )
    #return Markup(rendered)
    import logging
    print type(rendered)
    #print Markup(rendered)
    return Markup(rendered)
