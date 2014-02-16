from pysmium.lib.db import get_db

class Account(object):
    def __init__(self, account_id, nickname, api_verified, character_id,
                 character_name, corporation_id, corporation_name, alliance_id,
                 alliance_name, is_moderator, reputation):
        self.account_id = account_id
        self.nickname = nickname
        self.api_verified = api_verified
        self.character_id = character_id
        self.character_name = character_name
        self.corporation_id = corporation_id
        self.corporation_name = corporation_name
        self.alliance_id = alliance_id
        self.alliance_name = alliance_name
        self.is_moderator = is_moderator
        self.reputation = reputation

    @staticmethod
    def get(account_id):
        db = get_db()
        db.execute('SELECT accountid, nickname, apiverified, characterid, '
                   'charactername, corporationid, corporationname, allianceid, '
                   'alliancename, ismoderator, reputation '
                   'FROM osmium.accounts WHERE accountid = %s',
                   (account_id, ))
        return Account(*db.fetchone())
