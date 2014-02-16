from collections import defaultdict, OrderedDict
import dogma

import pysmium.lib.dogma_attrs as dogma_attrs
from pysmium.lib.db import get_db
from pysmium.lib.dogma_attrs import Att, get_attr

# The loadout can be viewed by everyone.
VIEW_EVERYONE = 0

# The loadout can be viewed by everyone, provided they have the
# password. This mode implies VISIBILITY_PRIVATE.*/
VIEW_PASSWORD_PROTECTED = 1

# The loadout can only be viewed by characters in the same alliance
# than the author.
VIEW_ALLIANCE_ONLY = 2

# The loadout can only be viewed by characters in the same
# corporation than the author.
VIEW_CORPORATION_ONLY = 3

# The loadout can only be viewed by its author.
VIEW_OWNER_ONLY = 4

# The loadout can only be viewed by contacts with good standing with the
# author.
VIEW_GOOD_STANDING = 5

# The loadout can only be viewed by contacts with excellent standing with the
# author.
VIEW_EXCELLENT_STANDING = 6


# The loadout can only be edited by its author.
EDIT_OWNER_ONLY = 0

# The loadout can only be edited by its author and people in the
# same corporation with the "Fitting Manager" role (or directors).
EDIT_OWNER_AND_FITTING_MANAGER_ONLY = 1

# The loadout can be edited by its author and anyone in the same
# corporation.
EDIT_CORPORATION_ONLY = 2

# The loadout can be edited by its author and everyone in the same
# alliance.
EDIT_ALLIANCE_ONLY = 3



# The loadout can be indexed by the Osmium search engine and other
# search engines, and will appear on search results when appropriate
# (conforming with the view permission).
VISIBILITY_PUBLIC = 0

# The loadout can never appear on any search results and will never
# be indexed. It is still accessible to anyone (conforming with the
# view permission) provided they
# have manually been given the URI.
VISIBILITY_PRIVATE = 1



# Offline module. (Such modules do not use CPU/Power.)
STATE_OFFLINE = 0

# Online module.
STATE_ONLINE = 1

# Active module (assumes online).
STATE_ACTIVE = 2

# Overloaded module (assumes active).
STATE_OVERLOADED = 3

# Each value is (title, sprite position, stateful, attributename)
slottypes = {
    'high':      ('High slots', (0, 15, 64, 64), True, 'hiSlots'),
    'medium':    ('Medium slots', (1, 15, 64, 64), True, 'medSlots'),
    'low':       ('Low slots', (2, 15, 64, 64), True, 'lowSlots'),
    'rig':       ('Rig slots', (3, 15, 64, 64), False, 'upgradeSlotsLeft'),
    'subsystem': ('Subsystems', (4, 15, 64, 64), False, 'maxSubSystems'),
}

# Each value is (pretty name, sprite position, clf name)
state_names = {
    STATE_OFFLINE: ('Offline', [ 2, 58, 16, 16 ], 'offline'),
    STATE_ONLINE: ('Online', [ 2, 59, 16, 16 ], 'online'),
    STATE_ACTIVE: ('Active', [ 3, 58, 16, 16 ], 'active'),
    STATE_OVERLOADED: ('Overloaded', [ 0, 29, 32, 32 ], 'overloaded'),
}

dogma_states = {
    None:             dogma.State.UNPLUGGED,
    STATE_OFFLINE:    dogma.State.OFFLINE,
    STATE_ONLINE:     dogma.State.ONLINE,
    STATE_ACTIVE:     dogma.State.ACTIVE,
    STATE_OVERLOADED: dogma.State.OVERLOADED,
}

class Fit(object):
    def __init__(self,
                 ship_typeid=None,
                 presets=None,
                 active_preset_id=None,
                 active_charge_preset_id=None,
                 drone_presets=None,
                 active_drone_preset_id=None,
                 fleet=None,
                 remote=None,
                 skillset=None,
                 damageprofile=None,
                 metadata=None):
        self.dogma_context = dogma.Context()
        self.ship = None
        if ship_typeid is not None:
            self.set_ship(ship_typeid)

        # XXX default preset id things?
        self.presets = presets or {}
        self.active_preset_id = active_preset_id
        self.active_charge_preset_id = active_charge_preset_id
        self.drone_presets = drone_presets or {}
        self.active_drone_preset_id = active_drone_preset_id

        self.set_fleet(fleet or [])
        self.set_remote(remote or [])
        self.set_skillset(skillset or {
            'name': 'All V',
            'default': 5,
            'override': {}
        })
        if damageprofile:
            self.damageprofile = damageprofile
        else:
            self.set_damage_profile('Uniform', .25, .25, .25, .25)
        self.metadata = metadata or {
            'name': 'Unnamed loadout',
            'description': '',
            'tags': [],
            'evebuildnumber': 0, # XXX
            'view_permission': VIEW_EVERYONE,
            'edit_permission': EDIT_OWNER_ONLY,
            'visibility': VISIBILITY_PUBLIC,
        }

    @property
    def modules(self):
        return self.presets[self.active_preset_id].modules

    ########################################
    # Fit modification methods

    def set_ship(self, ship_typeid):
        assert ship_typeid != None
        db = get_db()
        db.execute('SELECT invships.typename FROM osmium.invships '
                   'JOIN eve.invtypes ON invtypes.typeid = invships.typeid '
                   'WHERE invships.typeid = %s',
                   (ship_typeid, ))
        if not db.rowcount:
            return False
        (typename, ) = db.fetchone()
        self.ship = {
            'typeid': ship_typeid,
            'typename': typename,
        }
        self.dogma_context.set_ship(ship_typeid)
        return True

    def set_damage_profile(self, name, em, expl, kin, therm):
        assert name
        assert em >= 0 and expl >= 0 and kin >= 0 and therm >= 0
        tot = float(em + expl + kin + therm)
        assert tot > 0
        self.damageprofile = {
            'name': name,
            'damages': {
                'em': em/tot,
                'explosive': expl/tot,
                'kinetic': kin/tot,
                'thermal': therm/tot,
            },
        }

    def set_fleet(self, fleet):
        self.fleet = fleet

    def set_remote(self, remote):
        self.remote = remote

    def set_skillset(self, skillset):
        self.skillset = skillset

    def add_module(self, index, typeid, state=None):
        type = dogma_attrs.get_slottype(typeid)
        preset = self.presets[self.active_preset_id]
        if index in preset.modules[type]:
            self.remove_module(index, preset.modules[type][index]['typeid'])
        (is_activable, _) = dogma_attrs.get_states(typeid)
        if state is None:
            state = STATE_ACTIVE if is_activable and slottypes[type][2] else STATE_ONLINE
        dogma_index = self.dogma_context.add_module(typeid, state=state)
        preset.modules[type][index] = {
            'typeid': typeid,
            'typename': dogma_attrs.get_typename(typeid),
            'state': state,
            'dogma_index': dogma_index,
        }

    def remove_module(self, index, typeid):
        type = dogma_attrs.get_slottype(typeid)
        preset = self.presets[self.active_preset_id]

        # remove charge in current preset
        charge_preset = preset.charge_presets[self.active_charge_preset_id]
        if (type in charge_preset['charges'] and
                index in charge_preset['charges'][type]):
            self.remove_charge(type, index)

        # remove charge in all presets
        for charge_preset in preset.charge_presets:
            if (type in charge_preset['charges'] and
                    index in charge_preset['charges'][type]):
                del charge_preset['charges'][type][index]

        self.dogma_context.remove_module(preset.modules[type][index]['dogma_index'])
        del preset.modules[type][index]

    def add_charge(self, type, index, typeid):
        preset = self.presets[self.active_preset_id]
        assert index in preset.modules[type]
        
        charge_preset = preset.charge_presets[self.active_charge_preset_id]
        if (type in charge_preset.charges and
                index in charge_preset.charges[type]):
            self.remove_charge(type, index)

        charge_preset.charges[type][index] = {
            'typeid': typeid,
            'typename': dogma_attrs.get_typename(typeid),
        }
        self.dogma_context.add_charge(preset.modules[type][index]['dogma_index'],
                                      typeid)

    def remove_charge(self, type, inde):
        return NotImplemented

    def add_implant(self, typeid):
        return NotImplemented

    def remove_implant(self, typeid):
        return NotImplemented

    def add_drone(self, typeid, inbay=1, inspace=0):
        preset = self.drone_presets[self.active_drone_preset_id]
        
        if typeid not in preset.drones:
            preset.drones[typeid] = {
                'typeid': typeid,
                'typename': dogma_attrs.get_typename(typeid),
                'volume': dogma_attrs.get_volume(typeid),
                'quantityinbay': 0,
                'quantityinspace': 0,
            }

        preset.drones[typeid]['quantityinbay'] += inbay
        preset.drones[typeid]['quantityinspace'] += inspace
        self.dogma_context.add_drone(typeid, inspace)

    def remove_drone(self, typeid, where, quantity=1):
        return NotImplemented

    def use_preset(self, preset_id, create_default_charge_preset=False):
        assert preset_id in self.presets

        if self.active_preset_id:
            if preset_id == self.active_preset_id:
                return

            active_preset = self.presets[self.active_preset_id]
            for slottype, modules in active_preset.modules.items():
                for idx, module in modules.items():
                    dogma_index = module['dogma_index']
                    if 'target' in module:
                        self.dogma_context.clear_target(
                            dogma.Location(
                                dogma.LocationType.MODULE,
                                dogma.LocationUnion(module_index=dogma_index)
                        ))
                    self.dogma_context.remove_module(dogma_index)

            for typeid, implant in active_preset.implants.items():
                self.dogma_context.remove_implant(implant['dogma_index'])

        self.active_charge_preset_id = None

        self.active_preset_id = preset_id
        active_preset = self.presets[preset_id]
        if len(active_preset.charge_presets) == 0 and create_default_charge_preset:
            active_preset.charge_presets[0] = ChargePreset(
                0, 'Default charge preset', '')
            self.active_charge_preset_id = 0

        for slottype, modules in active_preset.modules.items():
            for idx, module in modules.items():
                dogma_index = self.dogma_context.add_module(
                        module['typeid'], dogma_states[module['state']])
                module['dogma_index'] = dogma_index
                if 'target' in module:
                    self.dogma_context.target(
                        dogma.Location(
                            dogma.LocationType.MODULE,
                            dogma.LocationUnion(module_index=dogma_index)
                        ),
                        self.get_remote(module['target']).dogma_context
                    )
                    self.dogma_context.remove_module(dogma_index)

        for typeid, implant in active_preset.implants.items():
            implant['dogma_index'] = self.dogma_context.add_implant(typeid)

    def use_charge_preset(self, charge_preset_id):
        active_preset = self.presets[self.active_preset_id]
        assert charge_preset_id in active_preset.charge_presets

        if self.active_charge_preset_id:
            active_charge_preset = active_preset[self.active_charge_preset_id]
            for slottype, charges in active_charge_preset.charges.items():
                for typeid, change in charges.items():
                    dogma_index = active_preset.modules[slottype][index]['dogma_index']
                    self.dogma_context.remove_charge(dogma_index)

        self.active_charge_preset_id = charge_preset_id
        active_charge_preset = active_preset.charge_presets[charge_preset_id]

        for slottype, charges in active_charge_preset.charges.items():
            for typeid, change in charges.items():
                dogma_index = active_preset.modules[slottype][index]['dogma_index']
                self.dogma_context.add_charge(dogma_index, typeid)

    def use_drone_preset(self, drone_preset_id):
        assert drone_preset_id in self.drone_presets

        if self.active_drone_preset_id:
            active_drone_preset = self.drone_presets[self.active_drone_preset_id]
            for typeid in active_drone_preset.keys():
                self.dogma_context.remove_drone(typeid)

        self.active_drone_preset_id = drone_preset_id
        active_drone_preset = self.drone_presets[self.active_drone_preset_id]

        for typeid, drone in active_drone_preset.drones.items():
            if drone['quantityinspace']:
                self.dogma_context.add_drone(typeid, drone['quantityinspace'])

    ########################################
    # misc

    def get_remote(self, key):
        if key == 'local':
            return self
        return self.remotes[key]

    def to_dict(self):
        return {
            'ship': self.ship,
            'presets': dict((k, p.to_dict()) for k, p in self.presets.items()),
            'dronepresets': dict((k, p.to_dict()) for k, p in self.drone_presets.items()),
            'fleet': self.fleet,
            'remote': self.remote,
            'skillset': self.skillset,
            'damageprofile': self.damageprofile,
            'metadata': self.metadata
        }

    def get_module_attribute(self, slottype, index, attr):
        pass

    def get_ship_attribute(self, attr):
        def sum_attribute(slottype, attr):
            return sum(self.get_module_attribute(slottype, index, attr)
                       for index in self.modules.get(slottype, {})) 

        if attr in ('upgradeLoad', Att.UpgradeLoad):
            return sum_attribute('rig', 'upgradeCost')
        if attr in ('hiSlots', 'medSlots', 'lowSlots',
                    Att.HiSlots, Att.MedSlots, Att.LowSlots):
            return (self.dogma_context.get_ship_attribute(get_attr(attr)) +
                    sum_attribute('subsystem', attr[:-1]+'Modifier'))
        if attr in ('turretSlots', 'launcherSlots'):
            if not self.ship:
                return 0
            return (dogma.type_base_attribute(self.ship['typeid'],
                                              get_attr(attr+'Left')) +
                    sum_attribute('subsystem', attr[:-5]+'HardPointModifier'))
        if attr in ('turretSlotsLeft', 'launcherSlotsLeft',
                    Att.TurretSlotsLeft, Att.LauncherSlotsLeft):
            return (self.dogma_context.get_ship_attribute(get_attr(attr)) +
                    sum_attribute('subsystem', attr[:-9]+'HardPointModifier'))
        return self.dogma_context.get_ship_attribute(get_attr(attr))


    ########################################
    # Computed attributes

    def get_cap_stability(self, reload=True):
        caps_by_context = self.dogma_context.get_capacitor_all(reload)
        return caps_by_context[self.dogma_context]

    def get_all_capacitors(self, reload=True):
        caps_by_context = self.dogma_context.get_capacitor_all(reload)
        remotes = {'local': self}.update(self.remotes)
        keys_by_context = dict((fit.dogma_context, key) for key, fit in remotes)
        return dict((keys_by_context[ctx], cap) for ctx, cap in caps_by_context)

    ########################################
    # Construction from database

    @staticmethod
    def get_bare_fit(fitting_hash):
        """Loads a fit (no metadata) from a fitting hash."""
        db = get_db()
        db.execute('SELECT name, description, evebuildnumber, hullid, '
                   '       creationdate, damageprofileid '
                   'FROM osmium.fittings '
                   'WHERE fittinghash = %s',
                   (fitting_hash, ))
        if not db.rowcount:
            return None
        (name, description, eve_build_number, hull_id, creation_date,
         damage_profile_id) = db.fetchone()

        fit = Fit(ship_typeid=hull_id)

        fit.metadata = {
            'hash': fitting_hash,
            'name': name,
            'description': description,
            'evebuildnumber': eve_build_number,
            'creation_date': creation_date,
        }

        db.execute(
            'SELECT tagname FROM osmium.fittingtags WHERE fittinghash = %s',
            (fitting_hash, ))
        fit.metadata['tags'] = [row[0] for row in db.fetchall()]

        if damage_profile_id:
            db.execute(
                'SELECT name, electromagnetic, explosive, kinetic, thermal '
                'FROM osmium.damageprofiles '
                'WHERE damageprofileid = %s',
                (damage_profile_id, ))
            if not db.rowcount:
                return None
            fit.set_damage_profile(*db.fetchone())


        db.execute('SELECT presetid, name, description '
                   'FROM osmium.fittingpresets '
                   'WHERE fittinghash = %s '
                   'ORDER BY presetid ASC',
                   (fitting_hash,))

        for (preset_id, name, description) in db.fetchall():
            preset = Preset(preset_id, name, description)
            fit.presets[preset_id] = preset
            fit.use_preset(preset_id)

            db.execute('SELECT index, typeid, state '
                       'FROM osmium.fittingmodules '
                       'WHERE fittinghash = %s AND presetid = %s '
                       'ORDER BY index ASC', (fitting_hash, preset_id))
            for (index, type, state) in db.fetchall():
                fit.add_module(index, type, state)

            db.execute('SELECT chargepresetid, name, description '
                       'FROM osmium.fittingchargepresets '
                       'WHERE fittinghash = %s AND presetid = %s '
                       'ORDER BY chargepresetid ASC',
                       (fitting_hash, preset_id))
            for (charge_preset_id, name, description) in db.fetchall():
                charge_preset = ChargePreset(charge_preset_id, name,
                                             description)
                preset.charge_presets[charge_preset_id] = charge_preset
                fit.use_charge_preset(charge_preset_id)

                db.execute('SELECT slottype, index, typeid '
                           'FROM osmium.fittingcharges '
                           'WHERE fittinghash = %s AND presetid = %s AND '
                           '      chargepresetid = %s '
                           'ORDER BY slottype ASC, index ASC',
                           (fitting_hash, preset_id, charge_preset_id))
                for (slottype, index, typeid) in db.fetchall():
                    fit.add_charge(slottype, index, typeid)

            db.execute('SELECT typeid '
                       'FROM osmium.fittingimplants '
                       'WHERE fittinghash = %s AND presetid = %s',
                       (fitting_hash, preset_id))
            for (implant, ) in db.fetchall():
                fit.add_implant(implant)


        db.execute('SELECT dronepresetid, name, description '
                   'FROM osmium.fittingdronepresets '
                   'WHERE fittinghash = %s '
                   'ORDER BY dronepresetid ASC',
                   (fitting_hash, ))
        for preset_id, name, description in db.fetchall():
            preset = DronePreset(preset_id, name, description)
            fit.drone_presets[preset_id] = preset
            fit.use_drone_preset(preset_id)

            db.execute('SELECT typeid, quantityinbay, quantityinspace '
                       'FROM osmium.fittingdrones '
                       'WHERE fittinghash = %s AND dronepresetid = %s',
                       (fitting_hash, preset_id))
            for typeid, inbay, inspace in db.fetchall():
                fit.add_drone(typeid, inbay, inspace)

        # TODO: fleet, remote, targets

        return fit

    @staticmethod
    def get_fit(loadout_id, revision=None):
        """Loads a loadout (with metadata) by loadout ID."""
        db = get_db()

        # TODO caching

        latest_revision = False
        if revision is None:
            db.execute('SELECT latestrevision '
                       'FROM osmium.loadoutslatestrevision '
                       'WHERE loadoutid = %s', (loadout_id, ))
            if not db.rowcount:
                return None
            (revision, ) = db.fetchone()
            latest_revision = True

        # TODO caching

        db.execute('SELECT accountid, viewpermission, editpermission, '
                   'visibility, passwordhash, privatetoken '
                   'FROM osmium.loadouts WHERE loadoutid = %s',
                   (loadout_id, ))
        if not db.rowcount:
            return None
        (account_id, view_permission, edit_permission,
         visibility, password_hash, private_token) = db.fetchone()

        db.execute('SELECT loadouthistory.fittinghash '
                   'FROM osmium.loadouthistory '
                   'WHERE loadoutid = %s AND revision = %s',
                   (loadout_id, revision))
        if not db.rowcount:
            return None
        (hash, ) = db.fetchone()

        fit = Fit.get_bare_fit(hash)
        fit.metadata.update({
            'loadoutid': loadout_id,
            'private_token': private_token,
            'viewpermission': view_permission,
            'editpermission': edit_permission,
            'visibility': visibility,
            'password': password_hash,
            'revision': revision,
            'accountid': account_id,
        })
        return fit

class Preset(object):
    def __init__(self, id, name=None, description=None):
        self.id = id
        self.name = name
        self.description = description
        self.modules = defaultdict(dict)
        self.charge_presets = {}
        self.implants = {}

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'modules': self.modules,
            'chargepresets': dict((id, cp.to_dict()) for id, cp in
                                  self.charge_presets.items()),
            'implants': self.implants, # XXX
        }

class ChargePreset(object):
    def __init__(self, id, name=None, description=None):
        self.id = id
        self.name = name
        self.description = description
        self.charges = defaultdict(dict)

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'charges': self.charges,
        }

class DronePreset(object):
    def __init__(self, id, name=None, description=None):
        self.id = id
        self.name = name
        self.description = description
        self.drones = {}

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'drones': self.drones,
        }
