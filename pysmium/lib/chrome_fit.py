from jinja2 import Markup

from pysmium.lib.chrome import render

def format_used(used, total):
    # TODO
    return "%d / %d" % (used, total)

def formatted_loadout_attributes(fit, cap=None):
    if cap is None:
        cap = fit.get_cap_stability() # TODO reload time options

    return render('attribs.html',
                  eng=formatted_engineering(fit, cap),
                 )

def format_attr_category(id, title, title_data, title_class, contents):
    return render('attrib_category.html',
                  id=id,
                  title=title,
                  titledata=Markup(title_data),
                  titleclass=title_class,
                  contents=contents)

def format_depletion_time(time):
    return 'TODO'

def format_capacitor(cap):
    rate = str(round(cap.delta * 1000, 1)) + ' GJ/s';
    if cap.stable:
        return str(round(100*cap.stable_fraction, 1))+"%", rate
    else:
        return format_duration(cap.depletion_time / 1000.0), rate

def formatted_engineering(fit, cap):
    slots_left = fit.get_ship_attribute('turretSlotsLeft')
    slots_total = fit.get_ship_attribute('turretSlots')
    turrets_formatted = format_used(slots_total - slots_left, slots_total)
    turrets_over = 'overflow' if slots_left < 0 else ''

    slots_left = fit.get_ship_attribute('launcherSlotsLeft')
    slots_total = fit.get_ship_attribute('launcherSlots')
    launchers_formatted = format_used(slots_total - slots_left, slots_total)
    launchers_over = 'overflow' if slots_left < 0 else ''

    captime, capdelta = format_capacitor(cap)

    contents = render('attribs_engineering.html',
                      turrets_formatted=turrets_formatted,
                      turrets_over=turrets_over,
                      launchers_formatted=launchers_formatted,
                      launchers_over=launchers_over,
                      captime=captime,
                      capdelta=capdelta,
                     )

    return format_attr_category(
        'engineering', 'Engineering',
        ("<span title='Capacitor stability percentage / depletion time (estimated)'>"
         + captime + '</span>'),
        'overflow' if turrets_over or launchers_over else '',
        contents
    )
