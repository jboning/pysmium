import json

from flask import make_response, render_template

import pysmium.lib.chrome as chrome
import pysmium.lib.chrome_fit as chrome_fit

from pysmium import app
from pysmium.model.account import Account
from pysmium.model.fit import Fit

@app.route('/loadout/<loadout_id>')
def view_loadout_public(loadout_id):
    fit = Fit.get_fit(loadout_id)
    author = Account.get(fit.metadata['accountid'])

    # TODO: loadout history stuff
    # TODO: viewer permission stuff
    # TODO: url overrides

    tags = ''
    if fit.metadata.get('tags', []):
        tags = ' (%s)' % (', '.join(fit.metadata['tags']))
    title = fit.metadata['name'] + tags
    if fit.metadata.get('ship'):
        title += ' / ' + fit.metadata['ship']['typename']
    # TODO revision override in title

    # TODO canonicaluri

    #capacitors = fit.get_all_capacitors()
    #interesting_attrs = fit.get_interesting_attrs()

    formatted_attributes = chrome_fit.formatted_loadout_attributes(fit)

    loadout_section = chrome.render('loadout_loadout.html',
                                    fit=fit)
    #presets_section = chrome.render('loadout_presets.html', fit=fit)
    #remote_section = chrome.render('loadout_remote.html', fit=fit)
    #comments_section = chrome.render('loadout_comments.html', fit=fit)
    #meta_section = chrome.render('loadout_meta.html', fit=fit)
    #export_section = chrome.render('loadout_export.html', fit=fit)

    page = chrome.header(title=title) # TODO index checking

    page += chrome.render('loadout_view.html',
                          loadoutid=loadout_id,
                          fit=fit,
                          formatted_attributes=formatted_attributes,
                          fitname='TODO',
                         )

    # TODO: cap and ia data
    chrome.include_js_snippet('view_loadout')
    chrome.include_js_snippet('view_loadout-presets')
    chrome.include_js_snippet('new_loadout-ship')
    chrome.include_js_snippet('new_loadout-modules')
    chrome.include_js_snippet('new_loadout-drones')
    chrome.include_js_snippet('new_loadout-implants')
    chrome.include_js_snippet('new_loadout-remote')

    from jinja2 import Markup
    page += Markup('<pre style="overflow: hidden;">%s</pre>' %
                   json.dumps(fit.to_dict(), indent=4))
    page += chrome.footer()
    resp = make_response(page)


    #resp = make_response(chrome.header() + data + chrome.footer())
    resp.headers['Content-Security-Policy'] = (
        "default-src 'none'"
        " ; style-src 'self' https://fonts.googleapis.com http://fonts.googleapis.com https://cdnjs.cloudflare.com http://cdnjs.cloudflare.com 'unsafe-inline'"
        " ; font-src https://themes.googleusercontent.com http://themes.googleusercontent.com"
        " ; img-src 'self' https://image.eveonline.com http://image.eveonline.com"
        " ; script-src 'self' https://cdnjs.cloudflare.com http://cdnjs.cloudflare.com"
        " ; connect-src 'self'"
    )


    return resp
