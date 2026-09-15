scriptname _WL_NPCMaintenanceScript extends ActiveMagicEffect

import debug
Quest property LanternQuest auto
Actor this_actor = None

State BlockEvents
	Event OnEffectStart(Actor akTarget, Actor akCaster)
	EndEvent
	Event OnEffectFinish(Actor akTarget, Actor akCaster)
	EndEvent
EndState

Event OnEffectStart(Actor akTarget, Actor akCaster)
	this_actor = akCaster
	(LanternQuest as _WL_NPCLanternActions).HandleLanternEquip(this_actor)
EndEvent

Event OnEffectFinish(Actor akTarget, Actor akCaster)
	(LanternQuest as _WL_NPCLanternActions).DestroyNonPlayableLanterns(this_actor)
	if this_actor
		Armor this_lantern = (LanternQuest as _WL_NPCLanternActions).GetCurrentInventoryLantern(this_actor)
		ToggleNPCInventoryLantern(this_lantern)
	endif
EndEvent

function ToggleNPCInventoryLantern(Armor akLantern)
	if akLantern
		GoToState("BlockEvents")
		this_actor.RemoveItem(akLantern, 1)
		GoToState("")
		;Finding #26: the blocking Utility.WaitMenuMode(1) was removed. RemoveItem and
		;AddItem are sequential synchronous native calls, so the remove is committed
		;before the re-add without a wait; for an NPC there is no inventory menu for
		;WaitMenuMode to service (it only elapses time while a menu is open), and this
		;runs only on NPC death or effect expiry - never a hot path.
		this_actor.AddItem(akLantern, 1)
	endif
endFunction
