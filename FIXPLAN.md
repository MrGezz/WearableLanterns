# Wearable Lanterns Fix Plan

> **Status as of 2026-09-06 - this document now records what was done, not what was
> proposed.** Of the 33 findings: **30 APPLIED**, 1 DEFERRED (#26), 1 REJECTED (#30),
> 1 needed NO ACTION (#33). Where the applied fix differs from the proposal below, the finding's
> Status line says so and `PORT-SSE.md` ("Script fix pass") carries the reasoning.
> Every change is save-safe on an existing character. The seven changed scripts compile
> clean; the working copy is built but **not yet deployed** - `buildcheck.py` reports
> `Wearable Lanterns SE` STALE `+2 ~16 -0`.

## State of the mod in this build

Wearable Lanterns 4.0+ (Chesko) is installed loose under MO2 as "Wearable Lanterns SE"
in the Immersion section, deployed from this working copy. The bundled PapyrusUtil
(JsonUtil/StorageUtil .pex and .psc) was removed intentionally; PapyrusUtil 4.7 is a
separate MO2 mod and is the build requirement. Campfire 1.13.0 SE (this workspace's SSE
port) is the integration target.

The mod is functional but has:

- SkyUI never detected (wrong plugin filename), so MCM profiles never load and three
  legacy config spells are added every session.
- A 5-second OnUpdate loop that runs 12 times/minute for the duration of every lantern-
  lit play session, on a Requiem build where the script engine is already at capacity.
- Disk I/O on every load-game for a PapyrusUtil test that was never gated.
- Several confirmed Papyrus bugs (null crash, no-op MoveTo, property shadowing, counter
  reset, MCM display mismatches).
- Build tooling (Archive.exe, WLBuildRelease.py, manifest) that is LE-era and cannot
  produce a working release.

---

## Summary table

| # | Sev | Kind | File | Summary | Status |
|---|-----|------|------|---------|--------|
| 1 | HIGH | compatibility | `_WL_Compatibility.psc:81` | SkyUI plugin name check uses "SkyUI.esp" -- bIsSKYUILoaded always false | APPLIED |
| 2 | HIGH | compatibility | `_WL_SkyUIConfigPanelScript.psc:426` | SKI_Main form lookup uses "SkyUI.esp" -- rename profile permanently disabled | APPLIED |
| 3 | HIGH | bug | `_WL_Compatibility.psc:18,41` | bIsBUGSLoaded property shadowed by same-named script variable; 101BUGS branch never taken | APPLIED |
| 4 | HIGH | bug | `_WL_LanternOil_v3.psc:694-718` | Null Location crash in SetShouldLightLanternAutomatically | APPLIED |
| 5 | HIGH | bug | `_WL_LanternOil_v3.psc:522,573` | dropped_lantern.MoveTo(dropped_lantern) is a no-op; lantern never repositioned near player | APPLIED |
| 6 | HIGH | script-load | `_WL_LanternOil_v3.psc:326-354` | 5-second RegisterForSingleUpdate loop -- always active while lantern ON | APPLIED (30s + burn accumulator) |
| 7 | HIGH | script-load | `_WL_Compatibility.psc:144-193` | JsonUtil file I/O on every OnPlayerLoadGame -- 17 calls + disk read/write | APPLIED (`bJSONVerified`, not the global) |
| 8 | HIGH | asset | `Archive.exe` | Bundled Archive.exe generates BSA v104 (LE format) | APPLIED (`external/SkyrimSE`) |
| 9 | HIGH | asset | `WLBuildRelease.py` | Build script is Python 2, references deleted SKSE folder | APPLIED (Python 3) |
| 10 | MED | bug | `_WL_LanternOil_v3.psc:757-768,808-818` | UpdateOil/UpdatePollen counter not reset when fuel hits zero; meter events spam every tick | APPLIED (subsumed by #6) |
| 11 | MED | bug | `_WL_NPCLanternActions.psc:54-64` | GetLanternIndex returns implicit 0 (travel lantern) when no lantern equipped | APPLIED |
| 12 | MED | bug | `_WL_SkyUIConfigPanelScript.psc:652` | MCM OnOptionDefault for DropLit passes wrong OID to SetToggleOptionValue | APPLIED |
| 13 | MED | bug | `_WL_SkyUIConfigPanelScript.psc:635` | MCM OnOptionDefault for Position uses == instead of = | APPLIED |
| 14 | MED | bug | `_WL_SkyUIConfigPanelScript.psc:765` | MCM OnOptionDefault for oil meter Y position uses X constant | APPLIED |
| 15 | MED | bug | `_WL_VendorStock.psc:47` | OnInit blocks script queue with Utility.Wait(3.0) | APPLIED (deferred, pattern kept) |
| 16 | MED | bug | `_WL_LanternOil_v3.psc:248-252` | SetLantern spin-wait up to 4 seconds of WaitMenuMode polling | APPLIED |
| 17 | MED | script-load | `_WL_Compatibility.psc:304`, `_WL_LanternOil_v3.psc:161-173` | Dawn/dusk game-time watcher fires unconditionally, never unregistered | APPLIED (gate + re-arm at 5 sites) |
| 18 | MED | script-load | `_WL_LanternOil_v3.psc:619-653` | LanternMutex -- 15 UnequipItem calls on every lantern equip | APPLIED |
| 19 | MED | script-load | `_WL_LanternOil_v3.psc:175-229` | OnObjectEquipped fires for every player equip unconditionally | APPLIED |
| 20 | MED | script-load | `_WL_VendorStock.psc:56-69,111-294` | Vendor restock cycle: up to 168 native calls every 24 game-hours, never stops | APPLIED |
| 21 | MED | save-bloat | `_WL_LanternOil_v3.psc:843-848` | 6 animation event registrations saved when sneak-off enabled; 4 fire during normal play | APPLIED (dynamic registration) |
| 22 | MED | compatibility | `Scripts/*.pex` | CommonMeterInterfaceHandler.pex and Common_SKI_MeterWidget.pex differ between WL and Campfire | APPLIED (Campfire's builds adopted) |
| 23 | MED | compatibility | `Chesko_WearableLantern.esp` | WL overrides TorchEvents IDLE losing Dawnguard's condition set | APPLIED (override dropped, not merged) |
| 24 | MED | asset | `WLArchiveManifest.txt` | Manifest lists four PapyrusUtil-provided scripts that no longer exist | APPLIED |
| 25 | MED | asset | `textures/chesko/_wl_glass*.dds` | Unreferenced NPOT 600x300 textures in manifest | APPLIED (de-listed, art kept) |
| 26 | LOW | script-load | `_WL_NPCMaintenanceScript.psc:32` | Utility.WaitMenuMode(1) in OnEffectFinish | DEFERRED (see below) |
| 27 | LOW | script-load | `_WL_LanternOil_v3.psc:589-597` | RefillTorchbug double GetAt() per inner loop iteration | APPLIED |
| 28 | LOW | script-load | `_WL_LanternOil_v3.psc:934-947` | WLDebug reads _WL_Debug GlobalVariable on every call, 2+ per tick | APPLIED |
| 29 | LOW | compatibility | `Scripts/*.pex` | CommonMeterInterfaceHandler.pex and Common_SKI_MeterWidget.pex have no source | APPLIED (source recovered) |
| 30 | LOW | compatibility | `Chesko_WearableLantern.esp` | WL lanterns carry no Frostfall warmth/coverage keywords | REJECTED (out of scope) |
| 31 | LOW | bug | `_WL_Compatibility.psc:160,167,191` | Frostfall error log prefix in WearableLanterns compatibility check | APPLIED (folded into #7) |
| 32 | LOW | asset | `textures/chesko/_wl_lampgeneric01_backup.dds` | Backup texture in manifest, would ship in release | APPLIED (de-listed, file kept) |
| 33 | LOW | asset | `meshes/chesko/_WL_Lightstone_WIP.nif` | WIP mesh in working copy (not in manifest, no action needed) | NO ACTION |

---

## Detailed findings

### 1. SkyUI plugin name check uses wrong filename (HIGH / compatibility)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_Compatibility.psc` line 81

**What:** `bIsSKYUILoaded = IsPluginLoaded(0x01000814, "SkyUI.esp")` calls
`Game.GetModByName("SkyUI.esp")` which returns 255 (not found). The deployed SkyUI
plugin is `SkyUI_SE.esp` (confirmed at `Project Improvement/SkyUI-Community/data/SkyUI_SE.esp`).

**Why it matters:** `bIsSKYUILoaded` is permanently false. Three consequences:
- Legacy management spells (config, toggle, check-fuel) are added to the player spell
  list every load (lines 277-299).
- `WearableLanterns_LoadProfileOnStartup` mod event is never sent (line 131-133), so
  user MCM settings are never restored from the JSON profile; they reset to defaults on
  every game load.
- The Upgrade_4_0 function (line 136-141) never runs because it requires
  `bIsSKYUILoaded`.

**Fix:** Change line 81 to:
```papyrus
bIsSKYUILoaded = IsPluginLoaded(0x01000814, "SkyUI_SE.esp")
```
If backward compat with the original SkyUI.esp is desired:
```papyrus
bIsSKYUILoaded = IsPluginLoaded(0x01000814, "SkyUI_SE.esp")
if !bIsSKYUILoaded
    bIsSKYUILoaded = IsPluginLoaded(0x01000814, "SkyUI.esp")
endif
```

---

### 2. SKI_Main form lookup uses wrong plugin name (HIGH / compatibility)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_SkyUIConfigPanelScript.psc` line 426

**What:** `Game.GetFormFromFile(0x00000814, "SkyUI.esp")` returns None because the active
plugin is `SkyUI_SE.esp`. The None cast to SKI_Main means `skyui.ReqSWFRelease` returns
0 (Papyrus None-property default). `0 >= 1026` is false, so the rename-profile option is
permanently disabled. SkyUI-Community's `SKI_Main.psc` line 17 confirms
`ReqSWFRelease = 2018`.

**Why it matters:** Profile rename in the MCM Save/Load page is permanently disabled even
though SkyUI-Community fully supports it.

**Fix:** Change line 426 to:
```papyrus
SKI_Main skyui = Game.GetFormFromFile(0x00000814, "SkyUI_SE.esp") as SKI_Main
```

---

### 3. bIsBUGSLoaded property shadowed by script variable (HIGH / bug)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_Compatibility.psc` lines 18 and 41

**What:** Line 18 declares `bool property bIsBUGSLoaded auto hidden` (auto property with
compiler-generated backing store). Line 41 declares a script-level variable
`bool bIsBUGSLoaded`. The local variable shadows the property within the script body.
Assignments at lines 100 and 106 (`bIsBUGSLoaded = true/false`) write the local
variable. External reads via
`(CompatibilityAlias as _WL_Compatibility).bIsBUGSLoaded` in
`_WL_LanternOil_v3.psc:363` access the property backing store, which is never written
and always returns false.

**Why it matters:** The 101BUGS mod (83Willows) is never recognized. `CatchTorchbug`
always takes the default torchbug path and never spawns the firefly variant. The
`FireflyBUG` activator set at line 99 is also unreachable by external callers.

**Fix:** Remove the script-level variable at line 41:
```
Delete line 41: bool bIsBUGSLoaded
```
The auto property at line 18 will then be the sole declaration, and the assignments at
lines 100/106 will write the property's backing store correctly.

Note: the other four booleans at lines 37-40 (`bIsGuardLanternLoaded`,
`bIsKhajiitLanternLoaded`, `bIsCLNLoaded`, `bIsCLNDGLoaded`) are only read within this
script's own body; they have no property counterpart and are not affected.

---

### 4. Null Location crash in SetShouldLightLanternAutomatically (HIGH / bug)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_LanternOil_v3.psc` lines 694-718

**What:** `OnLocationChange` at line 130 passes `akNewLoc` directly to
`SetShouldLightLanternAutomatically(akNewLoc)`. Inside that function, line 700 calls
`akLocation.HasKeyword(LocTypeCastle)` with no None check. `OnLocationChange` fires with
`akNewLoc = None` in unlocated cells. `OnUpdateGameTime` at line 162 passes
`PlayerRef.GetCurrentLocation()` with the same exposure.

**Why it matters:** A None method call terminates the stack frame with a script error.
Automatic lantern mode becomes unreliable in unlocated interiors and exteriors.

**Fix:** Guard only the keyword conditional at line 700. A blanket early return on None
would skip the exterior time-based toggle and the "unlocated interior" path (line 706),
both of which are correct behavior. The correct minimal fix:

Change line 700 from:
```papyrus
if akLocation.HasKeyword(LocTypeCastle) || akLocation.HasKeyword(LocTypeGuild) || 	\
    akLocation.HasKeyword(LocTypeInn) || akLocation.HasKeyword(LocTypeHouse) || 	\
    akLocation.HasKeyword(LocTypePlayerHouse) || akLocation.HasKeyword(LocTypeStore)
```
to:
```papyrus
if akLocation && (akLocation.HasKeyword(LocTypeCastle) || akLocation.HasKeyword(LocTypeGuild) || \
    akLocation.HasKeyword(LocTypeInn) || akLocation.HasKeyword(LocTypeHouse) || 	\
    akLocation.HasKeyword(LocTypePlayerHouse) || akLocation.HasKeyword(LocTypeStore))
```

This way a None location in an interior falls through to the else branch (ToggleLanternOn
at line 706 -- correct for an unlocated dungeon) and the exterior path (lines 709-714) is
completely unaffected.

---

### 5. dropped_lantern.MoveTo(dropped_lantern) is a no-op (HIGH / bug)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_LanternOil_v3.psc` lines 522 and 573

**What:** Both `DropLantern` (line 522) and `DropLitLanternPrompt` (line 573) call
`dropped_lantern.MoveTo(dropped_lantern)` -- moving the object to its own location.
The correct pattern is visible at line 409 in `FindAndDropEmptyBugLantern`:
`myEmptyLantern.MoveTo(PlayerRef, 100.0, 0.0, 50.0)`.

**Why it matters:** The dropped lantern lands wherever PlaceAtMe chose, not at a
deliberate offset in front of the player. On some geometry this puts it inside walls
or under floors. The Havok impulse then fires from an arbitrary position.

**Fix:** Replace both instances:

Line 522:
```papyrus
dropped_lantern.MoveTo(PlayerRef, 100.0, 0.0, 35.0)
```

Line 573:
```papyrus
dropped_lantern.MoveTo(PlayerRef, 100.0, 0.0, 35.0)
```

The offset values (100 forward, 0 lateral, 35 height) match the established pattern at
line 409, adjusted slightly for the lit lantern's visual height.

---

### 6. 5-second OnUpdate loop (HIGH / script-load)

**Status: APPLIED** - 30s + burn accumulator (2026-09-06)

**File:** `Scripts/Source/_WL_LanternOil_v3.psc` lines 326-354

**What:** `ToggleLanternOn()` calls `RegisterForSingleUpdate(5)` unconditionally at
line 354. `OnUpdate` fires every 5 seconds, calls UpdateOil/SetOilLevel or
UpdatePollen/SetPollenLevel, then re-registers at lines 335-340 if the fuel setting is
enabled and the lantern is on. Rate: 12 VM wakeups per minute sustained.

The actual oil reduction in `UpdateOil` (lines 757-767) already gates behind a
`oil_update_counter >= 6` check -- meaning oil only decreases every 6th tick (30 seconds).
The counter exists solely to subdivide the 5-second loop into 30-second oil-burn
intervals.

**Why it matters:** 12 VM wakeups per minute for the entire play session. Each tick also
unconditionally calls WLDebug (reading _WL_Debug GlobalVariable) even in production.

**Fix:** Change the interval from 5 to 30 seconds and remove the counter subdivision.

In `ToggleLanternOn` (line 354), change:
```papyrus
RegisterForSingleUpdate(5)
```
to:
```papyrus
RegisterForSingleUpdate(30)
```

In `OnUpdate` re-registrations (lines 337 and 340), change both:
```papyrus
RegisterForSingleUpdate(5)
```
to:
```papyrus
RegisterForSingleUpdate(30)
```

In `UpdateOil` (lines 757-767), remove the counter and reduce directly:
```papyrus
function UpdateOil()
    if SettingIsEnabled(_WL_SettingOil)
        float oil_level = _WL_OilLevel.GetValue()
        if oil_level >= 0.5
            oil_level -= 0.5
            _WL_OilLevel.SetValue(oil_level)
        endif
        WLDebug(1, "Oil Level: " + oil_level)
        SendEvent_UpdateOilMeter()
    endif
endFunction
```

In `UpdatePollen` (lines 805-820), same pattern:
```papyrus
function UpdatePollen()
    if SettingIsEnabled(_WL_SettingFeeding)
        int pollen_level = _WL_PollenLevel.GetValueInt()
        if pollen_level >= 1
            pollen_level -= 1
            _WL_PollenLevel.SetValueInt(pollen_level)
        endif
        WLDebug(1, "Pollen Level: " + pollen_level)
        SendEvent_UpdatePollenMeter()
    endif
endFunction
```

Remove the script-level variables `oil_update_counter` (line 94) and
`pollen_update_counter` (line 96). These are not properties and are not externally
referenced. Orphan data from existing saves is ignored by the VM on load.

Note: this also eliminates Finding #10 (counter-not-reset bug), because the counter no
longer exists.

---

### 7. JsonUtil file I/O on every OnPlayerLoadGame (HIGH / script-load)

**Status: APPLIED** - `bJSONVerified`, not the global (2026-09-06)

**File:** `Scripts/Source/_WL_Compatibility.psc` lines 144-193

**What:** `CheckJSONReadWrite()` runs on every load game: 17 PapyrusUtil calls including
`JsonUtil.Save` (disk write) and `JsonUtil.Load` (disk read). The purpose is to verify
PapyrusUtil is functional. The error messages at lines 160, 167, and 191 incorrectly
reference "[Frostfall]" and "FrostfallData" (copy-paste from Campfire).

**Why it matters:** Disk I/O blocks the Papyrus thread. With PapyrusUtil 4.7 confirmed
installed and functional, this test runs on every load for the entire campaign.

**Fix:** Gate behind the existing `_WL_Upgraded_4_0` GlobalVariable pattern. After the
check succeeds once, set a version stamp and skip on subsequent loads.

In `CompatibilityCheck()`, change line 68-73 from:
```papyrus
if isSKSELoaded
    bool can_read_write = CheckJSONReadWrite()
    if !can_read_write
        _WL_Error_JSONReadWrite.Show()
    endif
endif
```
to:
```papyrus
if isSKSELoaded && _WL_Upgraded_4_0.GetValueInt() < 3
    bool can_read_write = CheckJSONReadWrite()
    if can_read_write
        _WL_Upgraded_4_0.SetValueInt(3)
    else
        _WL_Error_JSONReadWrite.Show()
    endif
endif
```

The existing `_WL_Upgraded_4_0` check at line 75 uses value 2; using value 3 as the
JSON-verified stamp avoids adding a new GlobalVariable. The Upgrade_4_0 function sets it
to 2 (line 140), so the JSON check runs once after upgrade, then never again.

Also fix the three error strings (Finding #31): lines 160, 167, 191 -- replace
`[Frostfall]` with `[Wearable Lanterns]` and `FrostfallData` with `WearableLanternsData`.

---

### 8. Bundled Archive.exe generates BSA v104 (HIGH / asset)

**Status: APPLIED** - `external/SkyrimSE` (2026-09-06)

**File:** `Archive.exe` in the working copy root

**What:** ProductVersion 2.0.0.0, PDB path contains `TESV` -- Legendary Edition BSA
archiver. Produces BSA format version 104 (0x68). Skyrim SE requires 105 (0x69).

**Why it matters:** If WLBuildRelease.py were repaired and run, it would produce a BSA
that Skyrim SE 1.7.104 rejects. The live MO2 deployment is loose files, so gameplay is
unaffected today.

**Fix:** Replace with the SE Archive.exe from:
`D:\SteamLibrary\steamapps\common\Skyrim Special Edition\Tools\Archive\Archive.exe`
Or switch WLBuildRelease.py to use bsarch/Cathedral Assets Optimizer for v105 BSAs.

---

### 9. WLBuildRelease.py is Python 2 (HIGH / asset)

**Status: APPLIED** - Python 3 (2026-09-06)

**File:** `WLBuildRelease.py`

**What:** Uses `print "..."` (bare print), `raw_input()`, `rv.encode('utf8')` without
parentheses. References `./WearableLanterns/SKSE/Plugins/StorageUtil.dll` which does not
exist (PapyrusUtil 4.7 ships separately). The manifest also lists four PapyrusUtil
scripts that were removed.

**Why it matters:** Cannot execute on the Python 3 toolchain. Even with Python 2 fixes,
it would abort on missing files.

**Fix:**
1. Port to Python 3: `print(...)`, `input()` instead of `raw_input()`.
2. Remove the StorageUtil.dll copy step.
3. Remove or comment the Google Translate/Yandex API calls unless desired.
4. See Finding #24 for the manifest fixes.

---

### 10. UpdateOil/UpdatePollen counter not reset when fuel depleted (MED / bug)

**Status: APPLIED** - subsumed by #6 (2026-09-06)

**File:** `Scripts/Source/_WL_LanternOil_v3.psc` lines 757-768, 808-818

**What:** `oil_update_counter = 0` at line 761 is inside `if oil_level >= 0.5`, which
does not execute when oil is depleted. Once oil hits zero the counter stays at or above 6
and `SendEvent_UpdateOilMeter()` fires every 5 seconds indefinitely. Same for pollen.

**Why it matters:** Persistent high-frequency ModEvent dispatches from depleted lanterns.
On a Requiem build this compounds existing script queue pressure.

**Fix:** Eliminated by Finding #6 (the counter is removed entirely when the loop interval
changes to 30 seconds). If Finding #6 is not applied, the standalone fix is: move
`oil_update_counter = 0` outside the `if oil_level >= 0.5` guard so it resets
unconditionally when the `>= 6` threshold is reached. Same for `pollen_update_counter`.

---

### 11. GetLanternIndex returns implicit 0 when no lantern equipped (MED / bug)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_NPCLanternActions.psc` lines 54-64

**What:** If none of the four InvDisplay forms is equipped, the function has no explicit
return and falls through to Papyrus's implicit `return 0`. Index 0 means travel lantern.

**Why it matters:** NPCs that activate the maintenance effect without an InvDisplay
lantern equipped are incorrectly fitted with a travel lantern.

**Fix:** Add an explicit return at the end of the function and guard callers:
```papyrus
int function GetLanternIndex(Actor akActor)
    if akActor.IsEquipped(_WL_WearableLanternInvDisplay)
        return 0
    elseif akActor.IsEquipped(_WL_WearableTorchbugInvDisplay)
        return 1
    elseif akActor.IsEquipped(_WL_WearableTorchbugInvDisplayRED)
        return 2
    elseif akActor.IsEquipped(_WL_WearablePaperInvDisplay)
        return 3
    endif
    return -1
endFunction
```

In `HandleLanternEquip` (line 27), add after the `GetLanternIndex` call:
```papyrus
int index = GetLanternIndex(akActor)
if index < 0
    return
endif
```

---

### 12. MCM OnOptionDefault DropLit passes wrong OID (MED / bug)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_SkyUIConfigPanelScript.psc` line 652

**What:** `SetToggleOptionValue(General_SettingModeMenu_OID, true)` -- the OID is for the
Mode menu, not the DropLit toggle. The underlying global is set correctly.

**Fix:** Change line 652 to:
```papyrus
SetToggleOptionValue(General_SettingDropLitToggle_OID, true)
```

---

### 13. MCM OnOptionDefault Position uses == instead of = (MED / bug)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_SkyUIConfigPanelScript.psc` line 635

**What:** `PositionIndex == 1` is a comparison whose result is discarded. PositionIndex
is never updated. The MCM label then shows the old position while the global is set to 0.

**Fix:** Change line 635 to:
```papyrus
PositionIndex = 0
```
Value 0 matches the `SetValueInt(0)` call at line 637 (Back is the default).

---

### 14. MCM OnOptionDefault oil meter Y uses X constant (MED / bug)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_SkyUIConfigPanelScript.psc` line 765

**What:** `_WL_SettingMeterOilYPos.SetValue(NORMAL_METER_BOTTOMRIGHT_16_9_X)` sets Y to
1211.0. The correct constant is `NORMAL_METER_BOTTOMRIGHT_16_9_Y` (618.0). The slider and
profile save on the next two lines already use the correct Y constant.

**Fix:** Change line 765 to:
```papyrus
_WL_SettingMeterOilYPos.SetValue(NORMAL_METER_BOTTOMRIGHT_16_9_Y)
```

---

### 15. _WL_VendorStock.OnInit blocks with Utility.Wait(3.0) (MED / bug)

**Status: APPLIED** - deferred, pattern kept (2026-09-06)

**File:** `Scripts/Source/_WL_VendorStock.psc` lines 43-54

**What:** OnInit calls FillAllAliases(), Utility.Wait(3.0), ClearAllAliases(),
RemoveAllModItems(), FillAllAliases(). The 3-second wait is the Hotfix 3.0b pattern
(lines 6-8 comment) -- it lets aliases settle before the clear/remove/fill cycle.

**Why it matters:** 3-second thread block during game initialization on a build with 116
plugins and a stressed script engine.

**Fix:** Do NOT remove the first FillAllAliases -- the Fill/Wait/Clear/Remove/Fill
sequence is a deliberate vendor-inventory-bug-fix from Hotfix 3.0b. The safe change:
replace the blocking `Utility.Wait(3.0)` with a deferred approach. Change OnInit to:
```papyrus
Event OnInit()
    FillAllAliases()
    RegisterForSingleUpdateGameTime(0.01)
endEvent

Event OnUpdateGameTime()
    ClearAllAliases()
    RemoveAllModItems()
    FillAllAliases()
    RegisterForSingleUpdateGameTime(24)
endEvent
```
The 0.01 game-hour delay (~0.6 real seconds at default timescale) gives the engine time
to process alias inventories without blocking the script thread for 3 seconds.

---

### 16. SetLantern spin-wait up to 4 seconds (MED / bug)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_LanternOil_v3.psc` lines 248-252

**What:** Spins on `unequip_lock` with `Utility.WaitMenuMode(0.2)` up to 20 times (4
seconds). The lock is set/cleared in OnObjectUnequipped (lines 235, 241) which should
complete synchronously before SetLantern runs.

**Fix:** Shorten the maximum to 5 iterations (1 second) and add a debug warning if it
triggers:
```papyrus
int i = 5
while unequip_lock == true && i > 0
    Utility.WaitMenuMode(0.2)
    i -= 1
endWhile
if unequip_lock
    WLDebug(2, "SetLantern: unequip_lock still held after timeout")
endif
```

---

### 17. Dawn/dusk game-time watcher fires unconditionally (MED / script-load)

**Status: APPLIED** - gate + re-arm at 5 sites (2026-09-06)

**File:** `Scripts/Source/_WL_Compatibility.psc` line 304,
`Scripts/Source/_WL_LanternOil_v3.psc` lines 161-173

**What:** `RegisterForSingleUpdateGameTime(0.1)` is called on every load. OnUpdateGameTime
calls SetShouldLightLanternAutomatically then re-registers for the next dawn/dusk. This
repeats indefinitely with no unregister path, even when automatic mode is disabled.

**Fix:** In `OnUpdateGameTime`, gate the re-registration:
```papyrus
Event OnUpdateGameTime()
    SetShouldLightLanternAutomatically(PlayerRef.GetCurrentLocation())
    if SettingIsEnabled(_WL_SettingAutomatic)
        float current_hour = GameHour.GetValue()
        if current_hour < 7.0
            RegisterForSingleUpdateGameTime(7.0 - current_hour)
        elseif current_hour >= 7.0 && current_hour < 19.0
            RegisterForSingleUpdateGameTime(19.0 - current_hour)
        elseif current_hour >= 19.0
            RegisterForSingleUpdateGameTime(7.0 + (24.0 - current_hour))
        endif
    endif
endEvent
```

The MCM toggle at `_WL_SkyUIConfigPanelScript.psc` line 1006-1012 sets
`_WL_SettingAutomatic` and calls `ToggleLanternOn()` but does NOT re-arm the game-time
registration. Add after line 1011:
```papyrus
if _WL_SettingAutomatic.GetValueInt() == 2
    LanternQuest.ToggleLanternOn()
    LanternQuest.RegisterForSingleUpdateGameTime(0.1)
endIf
```

The legacy menu at `_WL_LegacyMenu.psc` line 134-136 also needs re-arming. Add after
the mode toggle call in `menu_mode()` -- specifically after the `MenuHandler_MultiSelect2`
call, check:
```papyrus
function menu_mode()
    MenuHandler_MultiSelect2(_WL_legacyconfig_modemanual, _WL_legacyconfig_modeauto, _WL_SettingAutomatic, 1)
    if _WL_SettingAutomatic.GetValueInt() == 2
        LanternQuest.RegisterForSingleUpdateGameTime(0.1)
    endif
endFunction
```

All functions used (`RegisterForSingleUpdateGameTime`, `SettingIsEnabled`, `GetValueInt`)
are vanilla Papyrus or already defined in the script.

---

### 18. LanternMutex -- 15 UnequipItem calls per equip (MED / script-load)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_LanternOil_v3.psc` lines 619-653

**What:** Unconditionally calls `PlayerRef.UnequipItem()` 15 times (one per non-display
lantern form variant) plus up to 5 conditional UnequipItem calls for display lanterns.

**Fix:** Gate each UnequipItem behind an IsEquipped check. `IsEquipped` is cheaper than
`UnequipItem` on a form not in inventory:
```papyrus
function LanternMutex(Form akBaseObject)
    if PlayerRef.IsEquipped(_WL_WearableLanternApparel)
        PlayerRef.UnequipItem(_WL_WearableLanternApparel, false, true)
    endif
    if PlayerRef.IsEquipped(_WL_WearableLanternApparelFront)
        PlayerRef.UnequipItem(_WL_WearableLanternApparelFront, false, true)
    endif
    ; ... repeat for all 15 forms ...
```
In practice the player has at most 1-2 forms equipped, so this reduces from 15+ native
calls to 15 IsEquipped checks + 1-2 UnequipItem calls.

---

### 19. OnObjectEquipped fires for every player equip (MED / script-load)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_LanternOil_v3.psc` lines 175-229

**What:** The handler runs on every player equip (armor, weapons, potions via hotkey).
`IsShield_Safe` does an Armor cast + HasKeyword; `IsLeftHandWeaponOrTorch` checks
Weapon cast, GetEquippedItemType, Light cast, and FormList.HasForm.

**Fix:** Add an early exit when no lantern is equipped (the shield/weapon branch at
line 179 only matters when `iPosition == 2`, i.e., held position, and `current_lantern`
is not LANTERN_NONE):
```papyrus
Event OnObjectEquipped(Form akBaseObject, ObjectReference akReference)
    ; Quick exit: if no lantern and not equipping one, nothing to do
    if current_lantern == LANTERN_NONE && !akBaseObject.HasKeyword(_WL_InventoryLantern)
        return
    endif
    ; ... rest of handler ...
endEvent
```
This skips the shield/weapon checks entirely when no lantern is equipped.

---

### 20. Vendor restock cycle: excessive GetItemCount calls (MED / script-load)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_VendorStock.psc` lines 111-294

**What:** RemoveAllModItems calls GetItemCount before every RemoveItem -- 56 GetItemCount
calls even when items are not present. Each 3-line if-block tests GetItemCount, then
calls RemoveItem with GetItemCount again as the count argument.

**Fix:** Replace each 3-line if/GetItemCount/RemoveItem block with a single RemoveItem
call. RemoveItem on a form not in inventory is a no-op (vanilla ObjectReference.psc,
aiCount defaults to 1). Replace blocks like:
```papyrus
if container.GetItemCount(item) > 0
    container.RemoveItem(item, container.GetItemCount(item))
endif
```
with:
```papyrus
container.RemoveItem(item, 99)
```
This eliminates all 56 GetItemCount calls (both the if-conditions and the RemoveItem
arguments) and reduces RemoveAllModItems from 56-168 native calls to exactly 56
RemoveItem calls. Total per cycle drops from ~140-196 to 84 flat.

No save impact, no gameplay impact, no invented API.

---

### 21. Sneak animation event registrations (MED / save-bloat)

**Status: APPLIED** - dynamic registration (2026-09-06)

**File:** `Scripts/Source/_WL_LanternOil_v3.psc` lines 842-858

**What:** RegisterForSneakEvents registers 6 animation events. The 4 non-sneak events
(tailMTIdle, tailMTLocomotion, tailCombatIdle, tailCombatLocomotion) fire during normal
play and are the mechanism for detecting sneak EXIT (restoring the lantern). Removing them
would break sneak-exit detection.

**Fix:** Dynamic registration: register only the 2 sneak-enter events initially. When
sneak is detected (is_sneaking becomes true, line 137), dynamically register the 4
exit-detection events. When sneak exit is detected (is_sneaking becomes false, line 147),
unregister the 4 exit events.

```papyrus
function RegisterForSneakEvents()
    RegisterForAnimationEvent(PlayerRef, "tailSneakIdle")
    RegisterForAnimationEvent(PlayerRef, "tailSneakLocomotion")
endFunction

function RegisterForSneakExitEvents()
    RegisterForAnimationEvent(PlayerRef, "tailMTIdle")
    RegisterForAnimationEvent(PlayerRef, "tailMTLocomotion")
    RegisterForAnimationEvent(PlayerRef, "tailCombatIdle")
    RegisterForAnimationEvent(PlayerRef, "tailCombatLocomotion")
endFunction

function UnregisterForSneakExitEvents()
    UnregisterForAnimationEvent(PlayerRef, "tailMTIdle")
    UnregisterForAnimationEvent(PlayerRef, "tailMTLocomotion")
    UnregisterForAnimationEvent(PlayerRef, "tailCombatIdle")
    UnregisterForAnimationEvent(PlayerRef, "tailCombatLocomotion")
endFunction
```

In OnAnimationEvent, line 137 (after `is_sneaking = true`):
```papyrus
RegisterForSneakExitEvents()
```

At line 147 (after `is_sneaking = false`):
```papyrus
UnregisterForSneakExitEvents()
```

During normal non-sneaking play only 2 events are registered, and tailSneak* never fires
when the player is not sneaking, so the VM is never woken needlessly.

---

### 22. Base-class .pex mismatch with Campfire (MED / compatibility)

**Status: APPLIED** - Campfire's builds adopted (2026-09-06)

**File:** `Scripts/CommonMeterInterfaceHandler.pex`, `Scripts/Common_SKI_MeterWidget.pex`

**What:** WL and Campfire 1.13.0 ship different versions of these two base-class .pex
files. WL's child classes (_WL_OilMeter, _WL_OilMeterInterfaceHandler etc.) were compiled
against WL's version.

MD5 comparison:
- WL CommonMeterInterfaceHandler.pex: `7acbabd8` (10761 bytes)
- Campfire: `ccb3a71c` (10793 bytes)
- WL Common_SKI_MeterWidget.pex: `c3e107b7` (5581 bytes)
- Campfire: `454af54b` (5578 bytes)

**Fix:** Recompile WL's child-class .psc files (`_WL_OilMeter.psc`,
`_WL_OilMeterInterfaceHandler.psc`, `_WL_PollenMeter.psc`,
`_WL_PollenMeterInterfaceHandler.psc`) against Campfire 1.13.0's current source for
Common_SKI_MeterWidget and CommonMeterInterfaceHandler. Then remove the base-class .pex
files from WL's Scripts/ folder (Campfire ships them). See also Finding #29.

---

### 23. WL overrides TorchEvents IDLE losing Dawnguard conditions (MED / compatibility)

**Status: APPLIED** - override dropped, not merged (2026-09-06)

**File:** `Chesko_WearableLantern.esp` (IDLE Skyrim.esm|0002A9D3 TorchEvents)

**What:** WL replaces the entire CTDA condition set on TorchEvents, discarding
Dawnguard.esm's additions.

**Fix:** Open `Chesko_WearableLantern.esp` in SSEEdit, inspect the TorchEvents IDLE CTDA
block, and merge Dawnguard's condition entries back alongside WL's condition. This is an
ESP edit, not a script change.

---

### 24. Manifest lists removed PapyrusUtil scripts (MED / asset)

**Status: APPLIED** (2026-09-06)

**File:** `WLArchiveManifest.txt`

**What:** Lists `Scripts\JsonUtil.pex`, `Scripts\StorageUtil.pex`,
`Scripts\Source\JsonUtil.psc`, `Scripts\Source\StorageUtil.psc`. All four were
intentionally removed. The manifest is the input to WLBuildRelease.py.

**Fix:** Remove the four lines from WLArchiveManifest.txt. Add a comment at the top
noting PapyrusUtil 4.7 is a runtime dependency.

---

### 25. Unreferenced NPOT textures (MED / asset)

**Status: APPLIED** - de-listed, art kept (2026-09-06)

**File:** `textures/chesko/_wl_glass.dds`, `textures/chesko/_wl_glass_n.dds`

**What:** 600x300 (non-power-of-two), DXT3/ATI2. Not referenced by any NIF or ESP record.
Listed in WLArchiveManifest.txt.

**Fix:** Determine whether these belong to a glass material in a paper lantern NIF. If
yes, add the texture path to the relevant NIF and resize to 512x256 (power-of-two). If
unused, remove from the manifest and delete the files. This is AA's call.

---

### 26. NPC maintenance WaitMenuMode(1) (LOW / script-load)

**Status: DEFERRED** - see below (2026-09-06)

**File:** `Scripts/Source/_WL_NPCMaintenanceScript.psc` line 32

**What:** `ToggleNPCInventoryLantern` does RemoveItem, WaitMenuMode(1), AddItem. The
1-second wait blocks the NPC's script thread on every death or effect expiry.

**Fix:** Remove the `Utility.WaitMenuMode(1)` at line 32. The Remove+Add sequence works
without a wait -- AddItem does not need the item to be absent first, and the
OnContainerChanged event fires on AddItem completion regardless.

---

### 27. RefillTorchbug double GetAt() (LOW / script-load)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_LanternOil_v3.psc` lines 589-597

**What:** The inner loop calls `_WL_PollenFlowers.GetAt(i)` twice per iteration -- once
for GetItemCount (line 590) and once for RemoveItem (line 592).

**Fix:** Cache the result in a local:
```papyrus
while i < list_size && continue
    Form akFlower = _WL_PollenFlowers.GetAt(i)
    int flower_count = PlayerRef.GetItemCount(akFlower)
    if flower_count > 0
        PlayerRef.RemoveItem(akFlower, 1, true)
        pollen_level += 8
        found_flowers = true
        continue = false
    endif
    i += 1
endWhile
```

---

### 28. WLDebug GlobalVariable read per call (LOW / script-load)

**Status: APPLIED** (2026-09-06)

**File:** `Scripts/Source/_WL_LanternOil_v3.psc` lines 934-947

**What:** WLDebug reads `_WL_Debug.GetValueInt()` on every invocation. OnUpdate calls
WLDebug(0, ...) at lines 336/339/342 on every tick -- 2+ GlobalVariable reads per tick
that produce no output in production (_WL_Debug default is 1, severity 0 is suppressed).

**Fix:** Cache `_WL_Debug.GetValueInt()` in a script-level int variable, refreshed in
OnPlayerLoadGame and from the MCM when the debug setting changes. Or: remove the
severity-0 WLDebug calls from OnUpdate entirely (they carry no useful production info).

The duplicate WLDebug in `_WL_LegacyToggleLantern.psc` (lines 44-57) is a separate
maintenance issue -- consolidate into the main script or a shared utility.

---

### 29. Base-class .pex files have no source (LOW / compatibility)

**Status: APPLIED** - source recovered (2026-09-06)

**File:** `Scripts/CommonMeterInterfaceHandler.pex`, `Scripts/Common_SKI_MeterWidget.pex`

**What:** No .psc in Scripts/Source for either. These are Chesko's CheskoPapyrusShared
widget library, compiled against a specific SkyUI version.

**Fix:** Recover source from Chesko's GitHub (CheskoPapyrusShared). If unavailable, use
Champollion to decompile and commit the recovered source. This is prerequisite work for
Finding #22 (recompiling against Campfire 1.13.0's version).

---

### 30. WL lanterns carry no Frostfall warmth/coverage keywords (LOW / compatibility)

**Status: REJECTED** - out of scope (2026-09-06)

**File:** `Chesko_WearableLantern.esp` (ARMO records)

**What:** WL's 6 keywords are all WL-internal. No Frostfall warmth/coverage keywords.
However, Frostfall's `GetGearType` does not recognize armor slot 55 (returning
GEARTYPE_NOTFOUND), and `GetArmorProtectionDataByKeyword` returns GEARTYPE_IGNORE for
unrecognized slots. Even with KID-distributed warmth keywords, the keywords would be
silently ignored.

**Fix:** This is not a simple KID patch. If warmth-from-lantern is desired (a design
decision), it requires either:
(a) modifying Frostfall's `GetGearType` to recognize slot 55 as GEARTYPE_MISC, plus KID
    keywords, or
(b) a script-side approach calling the warmth system API directly when the lantern is lit.

Both are scope changes to the survival system. AA decides whether this is in scope for the
first-party Frostfall support workstream.

---

### 31. Frostfall error log prefix in WearableLanterns (LOW / bug)

**Status: APPLIED** - folded into #7 (2026-09-06)

**File:** `Scripts/Source/_WL_Compatibility.psc` lines 160, 167, 191

**What:** Three `debug.trace` calls say "[Frostfall][ERROR]" and reference
"FrostfallData". The function writes to `../WearableLanternsData/` (line 146).

**Fix:** Replace all three strings. Folded into Finding #7's fix.

---

### 32. Backup texture in manifest (LOW / asset)

**Status: APPLIED** - de-listed, file kept (2026-09-06)

**File:** `textures/chesko/_wl_lampgeneric01_backup.dds`

**What:** 128x128 dev backup of the 1024x1024 diffuse. Listed in WLArchiveManifest.txt.
Would ship in a release.

**Fix:** Remove the entry from WLArchiveManifest.txt. Delete or move the file.

---

### 33. WIP mesh in working copy (LOW / asset)

**Status: NO ACTION** (2026-09-06)

**File:** `meshes/chesko/_WL_Lightstone_WIP.nif`

**What:** BSVersion 100 (SE-format), not in manifest, not referenced by any record.
Dev artifact. Would not be packaged.

**Fix:** No action required for the live build. Consider deleting if the Lightstone
feature remains unimplemented.

---

## Refuted claims

**_WL_NPCMaintenanceScript tracks akCaster rather than akTarget:** The code uses
`akCaster` on line 15, but the MGEF record `_WL_NPCMaintenanceEffect`
(Chesko_WearableLantern.esp 01D9AA) has Delivery=Self and CastingType=Constant Effect.
For a self-targeted constant effect, `akCaster == akTarget`, so the distinction is
irrelevant. Not a bug.

**5 Campfire records overridden by WL:** KYWD CCA002, CCA003 and GLOB CC0E0C, CC0E0D,
CC0E0B are overridden by both Campfire.esm and Chesko_WearableLantern.esp, but all
subrecords are identical. Cosmetic noise in SSEEdit; no functional conflict, no action
needed.

---

## What was applied (2026-09-06)

Passes 1-7 are done; each file compiles with `0 error(s), 0 warning(s)` (the exact
invocation is in `PORT-SSE.md`, "Compiling").

| Pass | File | Findings landed |
|---|---|---|
| 1 | `_WL_Compatibility.psc` | #1, #3, #7 (+#31), #17 (re-arm half) |
| 2 | `_WL_LanternOil_v3.psc` | #4, #5, #6 (+#10), #16, #17 (gate half), #18, #19, #21, #27, #28 |
| 3 | `_WL_SkyUIConfigPanelScript.psc` | #2, #12, #13, #14, #17 (re-arm, two sites) |
| 4 | `_WL_LegacyMenu.psc` | #17 (re-arm half) |
| 5 | `_WL_NPCLanternActions.psc` | #11 |
| 6 | `_WL_VendorStock.psc` | #15, #20 |
| 7 | `_WL_NPCMaintenanceScript.psc` | none - #26 deferred; the file was only recompiled |
| 8 | non-script | #8, #9, #22, #23, #24, #25, #29, #32; #30 rejected, #33 no action |

### Where the applied fix differs from the proposal above

- **#6** the plan removed the tick counter and drained per tick. That silently changes the
  burn rate whenever `ToggleLanternOn` restarts the timer - which it does on equip,
  location change, sneak exit and hotkey - so lit time is banked from
  `Utility.GetCurrentRealTime()` in `oil_burn_carry` / `pollen_burn_carry` and spent in
  35-second units instead, and both toggles settle the accumulator before they touch the
  timer. Net rate is the baseline's.
- **#7** the plan stamped `_WL_Upgraded_4_0` to 3. A private script variable
  `bJSONVerified` is used instead, so the upgrade global keeps exactly one meaning.
- **#17** the plan named three re-arm sites; there are five (`SwitchToProfile` in the MCM
  can turn automatic mode on from a loaded profile, and `RegisterForEventsOnLoad` arms it
  at load only when the mode is already on).
- **#23** the plan proposed merging Dawnguard's CTDA entries into WL's override. The
  override was **dropped** instead: measured from the raw subrecords, Dawnguard's
  `GetIsObjectType(Light) AND IsCarryable` is a strict superset of WL's
  `IsInList(<WL lanterns>) OR GetIsID(Torch01)`, so merging would only re-state what
  Dawnguard already covers. Unverified in play.
- **#25 / #32** the plan offered delete-or-keep. The files were removed from
  `WLArchiveManifest.txt` (so they never ship) and kept in the working copy as source art.

### Still open

- **#26** `Utility.WaitMenuMode(1)` in `_WL_NPCMaintenanceScript.ToggleNPCInventoryLantern`
  is unchanged. The plan asserts `AddItem` needs no wait after `RemoveItem`; that is an
  assertion, not a measurement, and the wait plausibly exists so the engine processes the
  removal before the re-add refreshes the NPC's inventory display. It runs on NPC death or
  effect expiry only - never a hot path - so it was left alone pending evidence.
- **#30** Frostfall warmth on lanterns - rejected as out of scope, see "Decisions for AA".
- **In-game validation of everything in this document.** Nothing here has been run in play.

## Save safety

**Safe on an existing save (no properties added or removed, no state dependencies):**
All script fixes in Passes 1-7 are safe. The counter variables removed in Finding #6
(`oil_update_counter`, `pollen_update_counter`) are script-level variables (not
properties); orphan data from existing saves is ignored by the VM. Unregistered
SingleUpdateGameTime registrations simply stop firing. All GlobalVariable and property
reads/writes use forms already in the save. No new quests, aliases, or magic effects.

**Requires a new game:** None of the fixes require a new game. Finding #11
(GetLanternIndex sentinel) changes NPC behavior going forward but does not corrupt
existing NPC state.

**Confirmed against what was actually written (2026-09-06).** No property was added,
removed or retyped in any of the seven files; no quest, alias, magic effect, keyword or
GlobalVariable was added. Six *script variables* were added - `log_level`, `burn_mark`,
`burn_lantern`, `oil_burn_carry`, `pollen_burn_carry` in `_WL_LanternOil_v3` and
`bJSONVerified` in `_WL_Compatibility` - which default-initialise on load exactly as the
removed counters are discarded. `burn_mark` is re-based in `OnPlayerLoadGame` because
`Utility.GetCurrentRealTime()` restarts with the process, so a mark carried over from a
previous session cannot be mistaken for real burn time.

---

## Decisions for AA

Five of these are now settled; the settled answer is marked **RESOLVED**.

- **RESOLVED - Finding #25 (glass textures):** genuinely unused. All 32 meshes, the
  plugin, every script and every interface file were searched for a `.dds` reference and
  none names them; the paper lanterns have no glass material at all. Removed from
  `WLArchiveManifest.txt`, kept in the working copy as source art. Original question: Are `_wl_glass.dds` and `_wl_glass_n.dds` intended
  for a NIF material that is missing its texture reference, or are they genuinely unused?
  If unused, delete; if wanted, identify the target NIF and resize to power-of-two.

- **RESOLVED - Finding #30 (Frostfall warmth for lanterns):** out of scope for this pass;
  it stays AA's call whether it joins the first-party Frostfall support workstream, and
  nothing was changed. Original question: A lantern is not a garment. Frostfall's
  warmth model measures body coverage from clothing. Distributing warmth keywords via KID
  would be silently ignored because Frostfall's GetGearType does not recognize slot 55.
  If warmth-from-lantern is desired, it is a design change to the survival system, not a
  patch. Does this go into the first-party Frostfall support workstream, or is it out of
  scope?

- **RESOLVED - Finding #22/29 (base-class .pex alignment with Campfire):** neither path.
  Champollion showed the two decompiles differ on one `MeterDebug` severity/string and
  nothing else, so WL's two `.pex` were replaced with Campfire's byte for byte and the two
  `.psc` copied in; no subclass needed recompiling and no mod became a dependency of the
  other. See `PORT-SSE.md`. Original question: The short-term fix is to
  ensure MO2 priority gives WL higher priority than Campfire (so WL's child classes match
  their base classes). The long-term fix (recompile against Campfire's source, then delete
  WL's copies) requires the base-class .psc recovery from Finding #29 first. Which path?

- **RESOLVED - Finding #23 (TorchEvents IDLE):** no merge was needed - the override was
  dropped, because Dawnguard's condition already covers every WL lantern. Original question: The Dawnguard condition merge needs SSEEdit work.
  Confirm whether Dawnguard torch triggers (crossbow oil flask lighting) are gameplay-
  relevant in this build before spending time on the merge.

- **RESOLVED - Finding #6 (loop interval):** 30 seconds, with the drain paid out of a
  banked-time accumulator so the rate survives the timer being restarted. Original question: The plan specifies 30 seconds (matching the existing
  6-tick gate). If a different drain rate is desired, adjust the interval and the per-tick
  decrement accordingly. The net oil-per-minute rate is preserved at 1.0/min by the
  current values.

- **Finding #15 (VendorStock OnInit):** The deferred-init approach uses a 0.01 game-hour
  delay instead of a 3-second real-time wait. Verify that alias inventory injection
  completes within that window in practice.
