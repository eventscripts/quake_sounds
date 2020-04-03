# Hunter's Quake Sounds Addon
#  
# Install instructions:
#       1. Install Mattie's EventScripts 2.0 plugin:
#           http://mattie.info/cs/
#
#       2. Copy and upload this script to:
#           <gamedir>/addons/eventscripts/quake_sounds/
#
#       3. Add the following line somewhere in autoexec.cfg:
#           es_load quake_sounds
#
################################################################################
#import EventScripts
import es
#import Libraries
import gamethread
import keyvalues
import langlib
import playerlib
import settinglib
import usermsg
import time
#import Psyco Compiler
import psyco
psyco.full()

# Addon Information
info = es.AddonInfo()
info.name = "Quake Sounds"
info.version = "4.0.6"
info.author = "Hunter"
info.url = "http://addons.eventscripts.com/addons/user/289"
info.description = "This scriptaddon adds Quake sounds to your server"
info.basename = "quake_sounds"

hunter_quake_sounds_ver     = info.version
hunter_quake_sounds_text    = 'Hunters '+info.name+', www.sourceplugins.de, '+info.version+', ES 2.0.0.247+ (Python Version)'

# Server Variables
quake_sounds_savetime       = es.ServerVar('quake_sounds_savetime', '30', 'How much days should inactive users be stored, before their settings get deleted? ( default = 30 )')
quake_sounds_default        = es.ServerVar('quake_sounds_default', 'standard', 'Which quake sounds should be the default setting? ( standard, ...)')
quake_sounds_round_reset    = es.ServerVar('quake_sounds_round_reset', '0', 'Should the player kills be resetted after every round? ( 1=yes 0=no )')
quake_sounds_round_announce = es.ServerVar('quake_sounds_round_announce', '1', 'Should the quake menu command be announced every round_start? ( 1=yes 0=no )')
quake_sounds_soundload      = es.ServerVar('quake_sounds_soundload', '1', 'Should the sounds be downloaded with EventScripts?')
quake_sounds_multikill_time = es.ServerVar('quake_sounds_multikill_time', '1.5', 'The time between kills that counts up the multikill count? ( >0 )')

# Global Variables
quake_sounds_language       = langlib.Strings(es.getAddonPath('quake_sounds')+'/language.ini')
quake_sounds_kills          = 0
quake_sounds_players        = {}

# KeyValues Object
quake_sounds_kv             = keyvalues.KeyValues(name='quake_sounds')

# Settinglib Object
quake_sounds_setting        = settinglib.create('quakesounds', 'Quake Sounds Style', 'list')

# Module Object
quake_sounds_module         = __import__('quake_sounds.quake_sounds')

def load():
    public = es.ServerVar('hu_qs', info.version, info.name)
    public.makepublic()
    
    quake_sounds_players = {}
    for userid in es.getUseridList():
        quake_sounds_players[userid] = {'kills':0,'multikills':0,'headshot':False,'headshots':0}

    quake_sounds_setting.clearoption()

    quake_sounds_kv.load(es.getAddonPath('quake_sounds')+'/quake_sounds.txt')
    for keyname in quake_sounds_kv['styles']:
        quake_sounds_setting.addoption(str(keyname), str(quake_sounds_kv['styles'][str(keyname)]))

    quake_sounds_setting.addoption('off', 'Off')
    quake_sounds_setting.setdefault(str(quake_sounds_default))
    quake_sounds_setting.addsound('ui/buttonclick.wav')

    es.regsaycmd('!quake', 'quake_sounds/saycmd', 'Quake Sounds Style')
    es.addons.registerForEvent(quake_sounds_module, 'player_changename', _check_event)
    es.addons.registerForEvent(quake_sounds_module, 'player_info', _check_event)
    es.addons.registerForEvent(quake_sounds_module, 'player_say', _check_event)
    es.addons.registerForEvent(quake_sounds_module, 'round_freeze_end', _check_event)
    es.addons.registerForEvent(quake_sounds_module, 'round_end', _check_event)
    es.addons.registerForEvent(quake_sounds_module, 'bomb_planted', _check_event)
    es.addons.registerForEvent(quake_sounds_module, 'bomb_defused', _check_event)
    es.log(hunter_quake_sounds_text)
    es.msg('#multi', '#green[QuakeSounds] #defaultLoaded')
    
def unload():
    es.unregsaycmd('!quake')
    es.addons.unregisterForEvent(quake_sounds_module, 'player_changename')
    es.addons.unregisterForEvent(quake_sounds_module, 'player_info')
    es.addons.unregisterForEvent(quake_sounds_module, 'player_say')
    es.addons.unregisterForEvent(quake_sounds_module, 'round_freeze_end')
    es.addons.unregisterForEvent(quake_sounds_module, 'round_end')
    es.addons.unregisterForEvent(quake_sounds_module, 'bomb_planted')
    es.addons.unregisterForEvent(quake_sounds_module, 'bomb_defused')
    es.msg('#multi', '#green[QuakeSounds] #defaultUnloaded')
    
def es_map_start(event_var):
    quake_sounds_setting.clear(int(quake_sounds_savetime)*86400)
    quake_sounds_players = {}
    for userid in es.getUseridList():
        quake_sounds_players[userid] = {'kills':0,'multikills':0,'headshot':False,'headshots':0}
    if int(quake_sounds_soundload):
        for keyname in quake_sounds_kv:
            if (str(keyname) != 'styles') and ('sound' in quake_sounds_kv[str(keyname)]):
                for soundname in quake_sounds_kv[str(keyname)]['sound']:
                    es.stringtable('downloadables', 'sound/'+str(quake_sounds_kv[str(keyname)]['sound'][str(soundname)]))
    _check_event(event_var)

def es_client_command(event_var):
    if (str(event_var['command']) == '!hunter_quake_sounds_ver') or (str(event_var['command']) == '!hunter_all_ver'):
        es.cexec(int(event_var['userid']), 'echo '+hunter_quake_sounds_text)
    _check_event(event_var)

def player_activate(event_var):
    quake_sounds_setting.updateTime(int(event_var['userid']))
    quake_sounds_players[int(event_var['userid'])] = {'kills':0,'multikills':0,'headshot':False,'headshots':0}
    gamethread.delayed(30, es.cexec, (int(event_var['userid']), 'echo '+hunter_quake_sounds_text))
    gamethread.delayed(15, es.tell, (int(event_var['userid']), '#multi', '#green[QuakeSounds] #defaultSay \'!quake\' for settings menu'))
    _check_event(event_var)

def player_disconnect(event_var):
    quake_sounds_setting.updateTime(int(event_var['userid']))
    if int(event_var['userid']) in quake_sounds_players:
        del quake_sounds_players[int(event_var['userid'])]
        
def player_team(event_var):
    quake_sounds_players[int(event_var['userid'])] = {'kills':0,'multikills':0,'headshot':False,'headshots':0}
    _check_event(event_var)

def player_spawn(event_var):
    userid = int(event_var['userid'])
    if int(quake_sounds_round_reset) or not userid in quake_sounds_players:
        quake_sounds_players[userid] = {'kills':0,'multikills':0,'headshot':False,'headshots':0}
    else:
        quake_sounds_players[userid]['multikills'] = 0
        quake_sounds_players[userid]['headshot'] = False
        quake_sounds_players[userid]['headshots'] = 0
    _check_event(event_var)

def round_start(event_var):
    global quake_sounds_kills
    quake_sounds_kills = 0
    if int(quake_sounds_round_reset):
        for userid in es.getUseridList():
            quake_sounds_players[userid] = {'kills':0,'multikills':0,'headshot':False,'headshots':0}
    else:
        for userid in es.getUseridList():
            if userid in quake_sounds_players:
                quake_sounds_players[userid]['multikills'] = 0
                quake_sounds_players[userid]['headshot'] = False
                quake_sounds_players[userid]['headshots'] = 0
            else:
                quake_sounds_players[userid] = {'kills':0,'multikills':0,'headshot':False,'headshots':0}
    if int(quake_sounds_round_announce):
        gamethread.delayed(10, round_announce)
    _check_event(event_var)

def round_announce():
    usermsg.hudhint(playerlib.getUseridList('#human'), 'Say !quake for Quake Styles')

def player_death(event_var):
    global quake_sounds_kills
    userid = int(event_var['userid'])
    attackerid = int(event_var['attacker'])
    if userid > 0:
        headshot = quake_sounds_players[userid]['headshot']
        try:
            if int(event_var['headshot']):
                headshot = True
        except:
            pass
        quake_sounds_players[userid] = {'kills':0,'multikills':0,'headshot':False,'headshots':0}
        if (attackerid > 0) and (userid != attackerid):
            userteam = int(event_var['es_userteam'])
            attackerteam = int(event_var['es_attackerteam'])
            weapon = str(event_var['weapon'])
            quake_sounds_kills = quake_sounds_kills + 1
            quake_sounds_players[attackerid]['kills'] = int(quake_sounds_players[attackerid]['kills']) + 1
            if userteam != attackerteam:
                temporary = {'prio':-1,'keyname':''}
                keyname = 'kill_'+str(quake_sounds_kills)
                if keyname in quake_sounds_kv:
                    if quake_sounds_kv[keyname]['prio'] > temporary['prio']:
                        temporary['prio'] = quake_sounds_kv[keyname]['prio']
                        temporary['keyname'] = keyname
                keyname = 'playerkills_'+str(quake_sounds_players[attackerid]['kills'])
                if keyname in quake_sounds_kv:
                    if quake_sounds_kv[keyname]['prio'] > temporary['prio']:
                        temporary['prio'] = quake_sounds_kv[keyname]['prio']
                        temporary['keyname'] = keyname
                if int(quake_sounds_players[attackerid]['multikills']) > 0:
                    keyname = 'multikills_'+str(quake_sounds_players[attackerid]['multikills'])
                    if keyname in quake_sounds_kv:
                        if quake_sounds_kv[keyname]['prio'] > temporary['prio']:
                            temporary['prio'] = quake_sounds_kv[keyname]['prio']
                            temporary['keyname'] = keyname
                if headshot:
                    quake_sounds_players[attackerid]['headshots'] = int(quake_sounds_players[attackerid]['headshots']) + 1
                    keyname = 'headshots_'+str(quake_sounds_players[attackerid]['headshots'])
                    if keyname in quake_sounds_kv:
                        if quake_sounds_kv[keyname]['prio'] > temporary['prio']:
                            temporary['prio'] = quake_sounds_kv[keyname]['prio']
                            temporary['keyname'] = keyname
                    else:
                        if 'special_headshot' in quake_sounds_kv:
                            if quake_sounds_kv['special_headshot']['prio'] > temporary['prio']:
                                temporary['prio'] = quake_sounds_kv['special_headshot']['prio']
                                temporary['keyname'] = 'special_headshot'
                keyname = 'weapon_'+str(weapon)
                if keyname in quake_sounds_kv:
                    if quake_sounds_kv[keyname]['prio'] > temporary['prio']:
                        temporary['prio'] = quake_sounds_kv[keyname]['prio']
                        temporary['keyname'] = keyname
                _play_quakesound(temporary['keyname'], userid, attackerid)
            else:
                _play_quakesound('special_teamkill', userid, attackerid)
            quake_sounds_players[attackerid]['multikills'] = int(quake_sounds_players[attackerid]['multikills']) + 1
            gamethread.delayed(int(quake_sounds_multikill_time), _check_multikill, (attackerid, quake_sounds_players[attackerid]['multikills']))
        else:
            _play_quakesound('special_selfkill', userid, attackerid)
    _check_event(event_var)
            

def player_hurt(event_var):
    userid = int(event_var['userid'])
    attackerid = int(event_var['attacker'])
    try:
        if (userid > 0) and (attackerid > 0):
            if int(event_var['es_userteam']) != int(event_var['es_attackerteam']):
                if (int(event_var['hitgroup']) == 1) and (int(event_var['health']) == 0):
                    quake_sounds_players[userid]['headshot'] = True
    except:
        pass
    _check_event(event_var)

def saycmd():
    quake_sounds_setting.send(int(es.getcmduserid()))
    
def _check_event(event_var):
    if event_var['userid']:
        userid = int(event_var['userid'])
    else:
        userid = 0
    if event_var['attacker']:
        attackerid = int(event_var['attacker'])
    else:
        attackerid = 0
    _play_quakesound('event_'+str(event_var['es_event']), userid, attackerid)

def _check_multikill(userid, kills):
    if quake_sounds_players[userid]['multikills'] == kills:
        quake_sounds_players[userid]['multikills'] = 0

def _play_quakesound(soundname, userid, attackerid):
    if soundname in quake_sounds_kv:
        if 'mode' in quake_sounds_kv[soundname]:
            mode = int(quake_sounds_kv[soundname]['mode'])
        else:
            mode = '1'
        if 'visual_mode' in quake_sounds_kv[soundname]:
            visual_mode = int(quake_sounds_kv[soundname]['visual_mode'])
        else:
            visual_mode = '1'
        if mode == 0:
            useridlist_sound = []
        elif mode == 1:
            useridlist_sound = playerlib.getUseridList('#human')
        elif mode == 2:
            useridlist_sound = [userid, attackerid]
        elif mode == 3:
            useridlist_sound = [attackerid]
        elif mode == 4:
            useridlist_sound = [userid]
        else:
            useridlist_sound = playerlib.getUseridList('#human')
        if visual_mode == 0:
            useridlist_text = []
        elif visual_mode == 1:
            useridlist_text = playerlib.getUseridList('#human')
        elif visual_mode == 2:
            useridlist_text = [userid, attackerid]
        elif visual_mode == 3:
            useridlist_text = [attackerid]
        elif visual_mode == 4:
            useridlist_text = [userid]
        else:
            useridlist_text = playerlib.getUseridList('#human')
        if (userid > 0) and (attackerid > 0):
            langdata = {"username":es.getplayername(userid), "attackername":es.getplayername(attackerid)}
        elif userid > 0:
            langdata = {"username":es.getplayername(userid)}
        elif attackerid > 0:
            langdata = {"attackername":es.getplayername(attackerid)}
        else:
            langdata = {}
        for userid in useridlist_sound:
            if not es.isbot(userid):
                soundfile = None
                style = str(quake_sounds_setting.get(userid))
                if style != 'off':
                    if style in quake_sounds_kv[soundname]['sound']:
                        soundfile = str(quake_sounds_kv[soundname]['sound'][style])
                    elif 'standard' in quake_sounds_kv[soundname]['sound']:
                        soundfile = str(quake_sounds_kv[soundname]['sound']['standard'])
                    if soundfile:
                        es.playsound(userid, soundfile, 1.0)
        for userid in useridlist_text:
            if not es.isbot(userid):
                style = str(quake_sounds_setting.get(userid))
                if style != 'off':
                    player = playerlib.getPlayer(userid)
                    soundtext = quake_sounds_language(soundname, langdata, player.get("lang"))
                    usermsg.centermsg(userid, str(soundtext))
