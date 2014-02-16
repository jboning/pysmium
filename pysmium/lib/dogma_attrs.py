import dogma

from pysmium.lib.db import get_db

class Category(object):
    Skill = 16

class Effect(object):
    ArmorRepair = 27
    EMPWave = 38
    EnergyDestabilizationNew = 2303
    EnergyTransfer = 31
    FighterMissile = 4729
    FueledArmorRepair = 5275
    FueledShieldBoosting = 4936
    HiPower = 12
    Leech = 3250
    LoPower = 11
    MedPower = 13
    MiningLaser = 67
    ProjectileFired = 34
    RemoteHullRepair = 3041
    RigSlot = 2663
    ShieldBoosting = 4
    ShieldTransfer = 18
    StructureRepair = 26
    SubSystem = 3772
    TargetArmorRepair = 592
    TargetAttack = 10
    UseMissiles = 101

class Att(object):
    Boosterness = 1087
    HiSlots = 14
    Implantness = 331
    LauncherSlotsLeft = 101
    LowSlots = 12
    MedSlots = 13
    ReloadTime = 1795
    ScanResolution = 564
    SignatureRadius = 552
    SkillTimeConstant = 275
    TurretSlotsLeft = 102
    UpgradeLoad = 1152

class Type(object):
    _1MNMicrowarpdriveII = 440
    _10MNMicrowarpdriveII = 12076
    _100MNMicrowarpdriveII = 12084

class Group(object):
    Booster = 303
    FighterBomber = 1023
    FighterDrone = 549


def get_generic(table, field, wherename, whereval):
    # XXX TODO caching
    db = get_db()
    db.execute('SELECT %s FROM %s WHERE %s = %%s'
               % (field, table, wherename),
               (whereval, ))
    return db.fetchone()[0]

def get_attributedisplayname(attrid):
    # XXX complicatied
    #return get_thing_generic('eve.dgmattribs', 'eve.invtypes', 'typeid'
    #db = get_db()
    #db.execute('SELECT typename FROM eve.invtypes WHERE typeid = %s',
    #           (typeid, ))
    #return db.fetchone()[0]
    pass

def get_attributename(id):
    return get_generic('eve.dgmattribs', 'attributename', 'attributeid', id)

def get_attributeid(name):
    return get_generic('eve.dgmattribs', 'attributeid', 'attributename', name)

def get_unitid(id):
    return get_generic('eve.dgmattribs', 'unitid', 'attributeid', id)

def get_unitdisplayname(id):
    return get_generic('eve.dgmunits', 'displayname', 'unitid', id)

def get_typename(id):
    return get_generic('eve.invtypes', 'typename', 'typeid', id)

def get_typeid(name):
    return get_generic('eve.invtypes', 'typeid', 'typename', name)

def get_groupid(id):
    return get_generic('eve.invtypes', 'groupid', 'typeid', id)

def get_volume(id):
    return get_generic('eve.invtypes', 'volume', 'typeid', id)

def get_average_market_price(id):
    return get_generic('eve.averagemarketprices', 'averageprice', 'typeid', id)

def get_parent_typeid(id):
    try:
        return get_generic('eve.metatypes', 'parenttypeid', 'typeid', id)
    except dogma.DogmaException:
        return None

def get_categoryid(id):
    return get_generic(
        'eve.invtypes JOIN eve.invgroups ON invgroups.groupid = invtypes.groupid',
        'categoryid',
        'typeid',
        id
    )

def get_groupname(id):
    return get_generic('eve.invgroups', 'groupname', 'groupid', id)

def get_required_skills(id):
    return NotImplemented

def get_slottype(typeid):
    if dogma.type_has_effect(typeid, dogma.State.OFFLINE, Effect.LoPower):
        return 'low'
    if dogma.type_has_effect(typeid, dogma.State.OFFLINE, Effect.MedPower):
        return 'medium'
    if dogma.type_has_effect(typeid, dogma.State.OFFLINE, Effect.HiPower):
        return 'high'
    if dogma.type_has_effect(typeid, dogma.State.OFFLINE, Effect.RigSlot):
        return 'rig'
    if dogma.type_has_effect(typeid, dogma.State.OFFLINE, Effect.SubSystem):
        return 'subsystem'
    raise Exception("module slot found for %r", typeid)

def get_states(typeid):
    if dogma.type_has_overload_effects(typeid):
        return (True, True)
    return (dogma.type_has_active_effects(typeid), False)

def get_attr(attr):
    if isinstance(attr, int):
        return attr
    return get_attributeid(attr)
