"""Diagnostics must execute the native XP chain exactly once and preserve it."""
import unittest
import test_native as base
SCRIPT=(base.ROOT/'experience_diagnostics.lua').read_text()
CONTINUOUS=(base.ROOT/'continuous_experience.lua').read_text()
SETUP='''
unpack=table.unpack;math.mod=math.fmod;ATTR_CEXP=15
function IsPlayer(c) return c.player and 1 or 0 end
function GetChaAttr(c,k) return c.xp end
function GetExpState(c) return c.scale end
function GetChaDefaultName(c) return 'test_actor' end
function GetChaTypeID(c) return c.model end
EXP_RAID=14;calls=0
Owner60OriginalGetExp=function(dead,attacker)
 calls=calls+1;attacker.xp=attacker.xp+dead.xp*EXP_RAID*attacker.scale/100
 return 123
end
'''
class XP60Tests(unittest.TestCase):
 runlua=base.NativeLuaTests.runlua
 def test_continuous_native_rewards_keep_x14_and_remove_only_online_penalty(self):
  self.runlua(SETUP+CONTINUOUS+SCRIPT+'''
Owner60OriginalGetExp=function(dead,c)
 calls=calls+1;c.xp=c.xp+dead.xp*EXP_RAID*GetExpState(c)/100;return 123
end
local d={player=false,xp=120,model=85};local c={player=true,xp=10,scale=0}
assert(GetExp_New(d,c)==123 and c.xp==1690 and calls==1 and EXP_RAID==14)
assert(c.scale==0 and string.find(c.notice,'scale=0') and string.find(c.notice,'effective=100'))
c.scale=50;assert(GetExpState(c)==100)
c.scale=100;assert(GetExpState(c)==100)
c.scale=150;assert(GetExpState(c)==150)
assert(GetExpState({player=false,scale=0})==0)
''')
 def test_native_multiplier_and_zero_scale_are_observed_without_changes(self):
  self.runlua(SETUP+SCRIPT+'''
local dead={player=false,xp=120,model=85};local c={player=true,xp=10,scale=100}
assert(GetExp_New(dead,c)==123 and calls==1 and c.xp==1690)
assert(string.find(c.notice,'scale=100') and string.find(c.notice,'after=1690'))
c.scale=0
assert(GetExp_New(dead,c)==123 and calls==2 and c.xp==1690)
assert(string.find(c.notice,'scale=0') and c.scale==0 and EXP_RAID==14)
''')
 def test_diagnostic_failure_does_not_break_native_rewards(self):
  self.runlua(SETUP+SCRIPT+'''
function GetChaDefaultName(c) error('diagnostics unavailable') end
local c={player=true,xp=10,scale=100};local d={player=false,xp=120,model=85}
assert(GetExp_New(d,c)==123 and c.xp==1690 and calls==1)
''')
 def test_native_error_is_not_swallowed_or_retried(self):
  self.runlua(SETUP+SCRIPT+'''
Owner60OriginalGetExp=function() calls=calls+1;error('native failure') end
local c={player=true,xp=10,scale=100};local d={player=false,xp=120,model=85}
assert(not pcall(GetExp_New,d,c) and calls==1 and c.xp==10)
assert(string.find(c.notice,'ok=0'))
''')
