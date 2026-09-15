# Wearable Lanterns - SSE port notes (2026-09-05)

Working copy for the D:/Mosais build. The root `IcZ Skyrim/WearableLanterns` clone stays
as the untouched reference; this clone carries the changes.

## What changed

- `meshes/chesko/_wl_paperlanterngo.nif` converted BS 83 -> 100 with `nifopt`. The other
  31 meshes were already SSE.
- `SKSE/Plugins/StorageUtil.dll` removed. It was a 32-bit (machine 014C) 2016 build of
  PapyrusUtil's StorageUtil for Legendary Edition; it cannot load in a 64-bit process. The
  build ships PapyrusUtil 4.7 for 1.7.104, which provides StorageUtil.
- `.gitattributes` added.

## Verified

- `assetaudit.py`: 0 LE-format assets.
- Records: 375 total, 6 overrides (KYWD 2, GLOB 2, MISC 1, IDLE 1), all against vanilla;
  0 records shared with anything in the current load order.
- Scripts: 25 distinct attached, 24 resolve. The one that does not is
  `_Camp_TinderTypeScript` - a Campfire hook. It is inert until the Campfire port lands and
  must NOT be stripped; it resolves then.

## Deployed

`D:/Mosais/mods/Wearable Lanterns SE/` (staged with meta.ini; enable in the MO2 UI).
`SEQ/Chesko_WearableLantern.seq` ships - start-enabled quests with dialogue need it.

## Scripts (checked 2026-09-05, later)

- Removed `Scripts/Source/JsonUtil.psc`, `Scripts/JsonUtil.pex`, `Scripts/Source/StorageUtil.psc`,
  `Scripts/StorageUtil.pex` from both the working copy and the staged mod. These were an older
  PapyrusUtil's headers bundled inside the repo; shipped, they would shadow PapyrusUtil 4.7's
  copies at runtime (the build's are byte-identical to the 4.7 repo's, in `Data/Scripts`).
- The remaining 26 `.psc` compile against the 1.7.104 headers: **26 succeeded, 0 failed**,
  with imports `<src>; Campfire/Scripts/Source; PapyrusUtil/Scripts/Source;
  SkyUI-Community/source/scripts; Data/Scripts/Source (SKSE); Data/Source/Scripts`.
  Campfire's tree supplies `Common_SKI_MeterWidget` / `CommonMeterInterfaceHandler`
  (Chesko's shared meter code, also in `CheskoPapyrusShared`) and `_Camp_TinderTypeScript`.
- 28 shipped `.pex` = 26 built + the two shared meter scripts, whose source lives in
  Campfire, not here. Shipped `.pex` are kept as-is; the compile is validation.

## Archive manifest (checked 2026-09-06)

`WLArchiveManifest.txt` 107 -> 100 entries. Removed seven lines; no other line changed.

- `Scripts/JsonUtil.pex`, `Scripts/StorageUtil.pex`, `Scripts/Source/JsonUtil.psc`,
  `Scripts/Source/StorageUtil.psc` - the four files deleted above were still listed, so
  `WLBuildRelease.py` (which copies every manifest line) could not build a release.
  **PapyrusUtil 4.7 is a runtime dependency, shipped as its own MO2 mod; WL must not
  bundle JsonUtil/StorageUtil.**
- `textures/chesko/_wl_glass.dds`, `_wl_glass_n.dds` - 600x300 (non-power-of-two),
  DXT3/ATI2. Referenced by no NIF (all 32 meshes scanned for `.dds` strings), no ESP
  record (the plugin contains zero `.dds` strings), no script and no interface file. The
  paper lanterns - the only plausible glass consumer - use `DLC2DarkElfFurniture01` +
  `GradHotCoals` + `RiftenRope01` and have no glass material at all.
- `textures/chesko/_wl_lampgeneric01_backup.dds` - 128x128 DXT3 dev backup, unreferenced.
  Not a mip of the live 1024x1024 DXT5 `_wl_lampgeneric01.dds` (different compression
  format), so it is not regenerable from what ships.

The three textures stay in the working copy as source art; being out of the manifest they
are simply not packaged. `meshes/chesko/_WL_Lightstone_WIP.nif` (an unreferenced dev
artifact for an unimplemented "Lightstone" feature) was **deleted 2026-09-15** - FIXPLAN
#33; it remains in git history. `manifestcheck.py` passes: all 100 manifest entries
present, no orphan `.pex`/`.psc`.

Note: `manifestcheck.py` derives the mesh/texture folders from its project-name argument
(`WearableLanterns`), but WL stores those under `chesko`, so its reverse check skips
`meshes/` and `textures/` entirely. Run it a second time with `chesko` as the argument to
exercise them.


## Shared meter base classes (2026-09-06, FIXPLAN #22 / #29)

`CommonMeterInterfaceHandler` and `Common_SKI_MeterWidget` are Chesko's shared meter
library (`CheskoPapyrusShared`, MIT, (c) 2016 Chesko). Ten subclasses across four mods
extend them: WL (2), Frostfall (4), Last Seed (3), plus Campfire's own tree.

Measured: WL shipped Chesko's 2017-01-08 builds; Campfire 1.13.0 SE ships 2026-08-22
builds from the current `CheskoPapyrusShared` source. Champollion decompile of both
pairs: `Common_SKI_MeterWidget` identical; `CommonMeterInterfaceHandler` differed on
exactly one line - `MeterDebug(0, "... This is bad.")` vs
`MeterDebug(3, "... This is bad and you should let the author know.")`. Property set,
variables, states and function signatures are identical, so no subclass needed
recompiling (Papyrus resolves inherited members by name; the child `.pex` reference the
parent only by its name string).

Fix: WL's two `.pex` replaced with Campfire's byte-for-byte, and the two `.psc` copied in
from `Campfire/Scripts/Source` (byte-identical to `CheskoPapyrusShared`). WL and Campfire
now ship identical files, so mod priority no longer decides which build the meters get.
`WLArchiveManifest.txt` 100 -> 102 entries (the two new `.psc`).

Not deleted: WL's `Chesko_WearableLantern.esp` masters only Skyrim.esm + Update.esm, so
WL is standalone upstream - dropping the base classes would make Campfire a hard runtime
dependency of WL's oil/pollen meters. Campfire ships its copies inside `Campfire.bsa`
while WL ships loose, and loose files win over archived ones, so deleting WL's was the
only way Campfire's copy could ever load - a new dependency bought for no behaviour gain.

## Release tooling (2026-09-06, FIXPLAN #8 / #9)

The release path could not produce a loadable Special Edition release. Both halves are
fixed and the mod's deployment is untouched: `Wearable Lanterns SE` still installs loose
under MO2, so nothing the running build uses changed.

**#8 - BSA format.** `Archive.exe` in the project root was the Legendary Edition Creation
Kit's packer (MD5 `76d4d947...`, byte-identical to `Campfire/external/Skyrim/Archive.exe`).
Measured 2026-09-06 by packing the same two staged files with each candidate: it writes
BSA version **104**, which Skyrim SE will not load; `Campfire/external/SkyrimSE/Archive.exe`
(MD5 `712f917e...`) writes **105**. Both now sit in `external/`, keyed by runtime the way
Campfire does it:

    external/Skyrim/Archive.exe      LE, v104   (the copy moved out of the project root)
    external/SkyrimSE/Archive.exe    SE, v105   (copied from Campfire/external/SkyrimSE)

**#9 - build script.** `WLBuildRelease.py` rewritten for Python 3, shaped like
`Campfire/Frostfall_BuildRelease.py` but self-contained because this is its own repository:

- `print`/`raw_input` ported; the `requests` + `googleapiclient` machine-translation step
  removed. It called Yandex's v1.5 translate API (retired) with an API key from
  `yandex_api_secret.txt`, which is not in the checkout. Translation files listed in
  `WLArchiveManifest.txt` are packed like any other asset; only English is committed.
- The `SKSE/Plugins/StorageUtil.dll` copy removed - that directory is gone (see above).
- Paths resolve from `__file__`, not from `os.chdir("..")` plus a hardcoded
  `./WearableLanterns/` prefix, so the checkout can be named anything.
- A missing manifest entry now names every missing file at once instead of raising
  `IOError` on the first.
- `python WLBuildRelease.py [version] [LE|SE]` also takes both answers as arguments.

**Not shipped broken.** Two checks stand between the archiver and a release:

- the finished BSA's header is read back and the build aborts unless the version matches
  the runtime (104 LE / 105 SE) and the file count matches the manifest. Archive.exe has
  been seen in this workspace to skip files and still exit 0 - that is why
  `RequiemLotDPatch/tools/bsapack.py` exists.
- staged meshes are checked against the runtime's NIF format (user version 2 = 83 LE /
  100 SE). This checkout's 32 meshes are already SE, so an LE build here would otherwise
  have shipped SE meshes silently. Campfire keeps `meshes/` in LE format and converts the
  staged copies with `nifopt`; this checkout does not, so there is no conversion step.

**Verified 2026-09-06.** `python WLBuildRelease.py 4.0.6-test SE` produced
`Chesko_WearableLantern.bsa` at **BSA version 105, 9 folders, 102 files** = the manifest
exactly (31 meshes, 28 `.pex`, 28 `.psc`, 8 textures, 3 readmes, 1 `.seq`, 1 `.swf`,
1 translation, 1 `_wl_title.dds`), read back with `bsapack.read_archive`. Release layout:
plugin + BSA + `readmes/` + the zip. Failure paths exercised: a v104 archive offered to an
SE build, a v105 archive to an LE build, a short file count, and an LE build of this
SE-format checkout - each aborts with a message naming the fix. The test release directory
was deleted afterwards; no release is committed.

Still Python 2 and not in the fix plan: `manifestcheck.py` (`ManifestCheck.bat`). It is a
separate audit tool, not on the release path - the builder's own manifest check covers
"listed but missing", not "present but unlisted".

## Script fix pass (2026-09-06, FIXPLAN #1-#31)

An audit of the mod produced 38 findings; 33 survived adversarial verification and became
`FIXPLAN.md`. This pass applied the script and plugin half of that plan. **Deployment is
unchanged**: `Wearable Lanterns SE` still installs loose under MO2, nothing was enabled or
reordered, and the mod list is AA's.

### Save safety

**Every change in this pass is safe on an existing character. No new game is needed.**
No property was added, removed or retyped; no quest, alias, magic effect, keyword or
GlobalVariable was added; every form read or written already exists in the save. The
plan's own analysis says the same and it was preserved deliberately.

Three things are worth stating explicitly, because they are the only places where the
save's script data changes shape at all - and all three are cases the Papyrus VM already
handles:

- `oil_update_counter` / `pollen_update_counter` were deleted from `_WL_LanternOil_v3`.
  They are script variables, not properties. Orphan variable data in an existing save is
  discarded by the VM on load.
- Six script variables were added (`_WL_LanternOil_v3`: `log_level`, `burn_mark`,
  `burn_lantern`, `oil_burn_carry`, `pollen_burn_carry`; `_WL_Compatibility`:
  `bJSONVerified`). Added script variables default-initialise on load. `burn_mark` is
  re-based in `OnPlayerLoadGame` because `Utility.GetCurrentRealTime()` restarts with the
  process, so a mark saved in a previous session is meaningless.
- Registrations only. `RegisterForSingleUpdate(5)` becomes `(30)`, the dawn/dusk
  `RegisterForSingleUpdateGameTime` is now conditional, and four animation-event
  registrations became dynamic. A registration that is no longer renewed simply stops
  firing; none of them is a persistent form.

### Applied - scripts (7 files, all compile clean)

| # | File | Change |
|---|------|--------|
| 1 | `_WL_Compatibility` | `IsPluginLoaded(0x01000814, "SkyUI_SE.esp")`, falling back to `SkyUI.esp`. `bIsSKYUILoaded` was permanently false, so MCM profiles never loaded and three legacy spells were re-added every session. |
| 2 | `_WL_SkyUIConfigPanelScript` | `Game.GetFormFromFile(0x00000814, "SkyUI_SE.esp")`. `skyui.ReqSWFRelease` read 0 off a None cast, so profile rename was permanently disabled. |
| 3 | `_WL_Compatibility` | Deleted the script-level `bool bIsBUGSLoaded` (line 41) that shadowed the auto property. External reads always saw false, so 101BUGS was never recognised. |
| 4 | `_WL_LanternOil_v3` | `if akLocation && (...HasKeyword...)` - guards **only** the keyword conditional. See "Rejected" below for why an early return is wrong. |
| 5 | `_WL_LanternOil_v3` | `dropped_lantern.MoveTo(PlayerRef, 100.0, 0.0, 35.0)` in both `DropLantern` and `DropLitLanternPrompt`; it was `MoveTo(dropped_lantern)`, a no-op. Offsets follow `FindAndDropEmptyBugLantern`. |
| 6, 10 | `_WL_LanternOil_v3` | Update interval 5s -> 30s (12 VM wakeups/minute -> 2). The 6-tick counters are gone; lit time is banked in `oil_burn_carry` / `pollen_burn_carry` from `Utility.GetCurrentRealTime()` and spent in 35-second units, which is the baseline rate. Banking is needed because `ToggleLanternOn` restarts the timer from many events (equip, location change, sneak exit, hotkey) and would otherwise starve the loop; both toggles settle the accumulator first, so an interruption cannot discard or duplicate fuel progress. An empty lantern clears its carry - that is #10, whose counter was never reset at zero and spammed meter events forever. |
| 7, 31 | `_WL_Compatibility` | `CheckJSONReadWrite()` (17 PapyrusUtil calls, one disk write and one disk read) now runs once and sets `bJSONVerified`, instead of on every load game. The plan proposed stamping `_WL_Upgraded_4_0` to 3; a private script variable was used instead so the upgrade global keeps one meaning. The three `debug.trace` strings that said `[Frostfall]` / `FrostfallData` now say `[Wearable Lanterns]` / `WearableLanternsData` (#31). |
| 11 | `_WL_NPCLanternActions` | `GetLanternIndex` returns `-1` instead of falling through to Papyrus's implicit `return 0`, which means "travel lantern"; `HandleLanternEquip` returns on `-1`. NPCs with no InvDisplay lantern equipped were being fitted with one. |
| 12 | `_WL_SkyUIConfigPanelScript` | `SetToggleOptionValue(General_SettingDropLitToggle_OID, true)` - it passed the Mode menu's OID. |
| 13 | `_WL_SkyUIConfigPanelScript` | `PositionIndex = 0` - it was `PositionIndex == 1`, a discarded comparison, so the label disagreed with the global. |
| 14 | `_WL_SkyUIConfigPanelScript` | Oil-meter Y reset uses `NORMAL_METER_BOTTOMRIGHT_16_9_Y` (618.0); it used the X constant (1211.0). |
| 15 | `_WL_VendorStock` | `OnInit` no longer blocks on `Utility.Wait(3.0)`: `FillAllAliases()` then `RegisterForSingleUpdateGameTime(0.01)`, and `OnUpdateGameTime` does Clear / Remove / Fill and re-arms at 24. Chesko's Hotfix 3.0b sequence is intact - see "Rejected". |
| 16 | `_WL_LanternOil_v3` | `SetLantern` spin-wait 20 -> 5 iterations (4s -> 1s) with a `WLDebug(2, ...)` if the lock is still held. |
| 17 | four files | The dawn/dusk watcher re-registers **only while automatic mode is on**, and every site that turns automatic mode on re-arms it with `RegisterForSingleUpdateGameTime(0.1)`: `_WL_LanternOil_v3.OnUpdateGameTime` (the gate), `_WL_Compatibility.RegisterForEventsOnLoad`, `_WL_LegacyMenu.menu_mode`, `_WL_SkyUIConfigPanelScript.OnOptionMenuAccept` and `_WL_SkyUIConfigPanelScript.SwitchToProfile` (a loaded profile can turn automatic mode on too). |
| 18 | `_WL_LanternOil_v3` | Each of the 15 unconditional `UnequipItem` calls in `LanternMutex` is behind an `IsEquipped` check, as are the five display-lantern calls. In practice 1-2 unequips instead of 15-20 native calls per equip. |
| 19 | `_WL_LanternOil_v3` | `OnObjectEquipped` returns immediately when no lantern is carried and the equipped form has no `_WL_InventoryLantern` keyword, skipping the Armor/Weapon/Light casts on every armour, weapon and hotkeyed potion. |
| 20 | `_WL_VendorStock` | `RemoveAllModItems` drops 56 `GetItemCount` guards and 56 `GetItemCount` count arguments for a flat `RemoveItem(item, 99)`; `RemoveItem` on an absent form is a no-op. ~140-196 native calls per 24-hour cycle -> 56. |
| 21 | `_WL_LanternOil_v3` | The four non-sneak animation events are registered on sneak entry and unregistered on sneak exit (`RegisterForSneakExitEvents` / `UnregisterForSneakExitEvents`); only the two `tailSneak*` events are held during normal play. `RegisterForSneakEvents` also arms the exit events when it is called while the player is already sneaking, so re-enabling the setting mid-sneak cannot strand the lantern. |
| 27 | `_WL_LanternOil_v3` | `RefillTorchbug` caches `_WL_PollenFlowers.GetAt(i)` in a local instead of calling it twice per iteration. |
| 28 | `_WL_LanternOil_v3` | `WLDebug` reads a cached `log_level` instead of `_WL_Debug.GetValueInt()` on every call; refreshed in `OnPlayerLoadGame`, lazily initialised when `< 0`. No script writes `_WL_Debug`, so a console `set _WL_Debug to ...` mid-session now needs a reload to take effect - the only behaviour this trades away. |

### Applied - plugin

- **#23** `Chesko_WearableLantern.esp` no longer overrides `IDLE Skyrim.esm|0002A9D3
  TorchEvents`. Measured from the raw CTDA subrecords: vanilla is `GetIsID(Torch01)`;
  Dawnguard replaces it with `GetIsObjectType(Light) AND IsCarryable`; WL replaced *that*
  with `IsInList(<WL lantern list>) OR GetIsID(Torch01)`, discarding Dawnguard's pair.
  Dawnguard's condition is a strict superset of WL's - every WL held lantern is a
  carryable LIGH - so the override was dropped rather than merged
  (`RequiemLotDPatch/tools/droprecords.py`; backup `Chesko_WearableLantern.esp.bak-droprecords`).
  HEDR 406 -> 405 records, 122,697 -> 122,483 bytes; nothing else in the plugin changed.
  Unverified in play - check in-game that torch-swap idles still fire on a lit WL lantern.

### Rejected - four fixes that were tried and thrown out

Each of these is the obvious fix and each is wrong. Do not re-apply them.

1. **#4, an early `return` on a None `akLocation`.** `SetShouldLightLanternAutomatically`
   only dereferences `akLocation` inside the interior branch. Returning early would also
   skip the exterior time-of-day toggle and the unlocated-interior path (`ToggleLanternOn`),
   both of which are correct behaviour and both of which run with no location. Only the
   keyword conditional is guarded, so a None location in an interior falls to the else
   branch - correct for an unlocated dungeon.
2. **#17, gating the watcher without re-arming it.** Stopping `OnUpdateGameTime` from
   re-registering while automatic mode is off is half a fix: nothing then re-registers
   when the player turns automatic mode back on, so the watcher stays dead until the next
   save reload. The gate ships only together with the `RegisterForSingleUpdateGameTime(0.1)`
   re-arm at all five sites listed above.
3. **#21, deleting the four non-sneak animation events.** `tailMTIdle`,
   `tailMTLocomotion`, `tailCombatIdle` and `tailCombatLocomotion` are the *only*
   mechanism that detects the player leaving sneak and restores the lantern. Removing them
   removes sneak-exit detection. They are registered dynamically instead.
4. **#15, removing the first `FillAllAliases()`.** The Fill / Wait / Clear / Remove / Fill
   sequence is Chesko's Hotfix 3.0b working around an engine alias-inventory bug, not
   redundant work. Only the blocking `Utility.Wait(3.0)` was replaced, with a 0.01
   game-hour deferral; the sequence itself is unchanged.

Also refuted during the audit and deliberately **not** changed: `_WL_NPCMaintenanceScript`
passing `akCaster` rather than `akTarget`. `_WL_NPCMaintenanceEffect`
(`Chesko_WearableLantern.esp` 01D9AA) is Delivery=Self, CastingType=Constant Effect, so
`akCaster == akTarget`. Not a bug.

### Not applied

- **#26** `_WL_NPCMaintenanceScript.psc:32` still calls `Utility.WaitMenuMode(1)` between
  the `RemoveItem` and the `AddItem` in `ToggleNPCInventoryLantern`; the fix phase left it
  and the file's only change this pass is a recompile. Inference, not measurement: the
  wait is there so the engine processes the removal before the re-add refreshes the NPC's
  inventory display, and this runs only on NPC death or effect expiry, never on a hot
  path - so "port, don't reinvent" argues for leaving it until someone can show the re-add
  is safe without it. **Open.**
- **#30** Frostfall warmth on WL lanterns - **implemented 2026-09-15** as first-party
  carried-light heat (see "Frostfall carried-light warmth" below). The keyword route stays
  rejected (slot 55 is invisible to `GetGearType`); instead a lit lantern nudges Exposure
  via the documented `FrostUtil.ModPlayerExposure`, gated on lit state and Requiem-balanced.
- **#25 / #32** were resolved as manifest work (see "Archive manifest" above), not by
  deleting art: the two NPOT glass textures and the 128x128 backup diffuse stay in the
  working copy as source and are simply not packaged. **#33** - the `_WL_Lightstone_WIP.nif`
  dev artifact - was deleted 2026-09-15 (unreferenced; still in git history).

### Compiling

`BuildSingle.bat` is Legendary Edition era: it points at `..\PapyrusCommon` and
`..\CheskoPapyrusShared`, neither of which exists beside this checkout. This is the
invocation that works, run from the checkout root. **The SKSE headers must precede the
vanilla tree** or every script fails, and they now live in the MO2 mod, because the game's
own `Data\Scripts\Source` was emptied on 2026-09-05:

**2026-09-15 - use the Campfire compile environment.** `_WL_LanternOil_v3.psc` now calls
`FrostUtil.ModPlayerExposure` (Frostfall carried-light warmth, #30). Referencing `FrostUtil`
pulls in the whole FrostfallAPI type graph, which needs Campfire's full compile environment,
so the recipe below mirrors `Campfire/pscompile.py`'s `import_dirs()`. It is a superset that
builds every WL script (all 26 clean), including the seven from 2026-09-06.

```bat
set GAME=D:\SteamLibrary\steamapps\common\Skyrim Special Edition
set WS=C:\Users\IceCreamAssasin\Claude\Projects\IcZ Skyrim
set WL=%WS%\Project Improvement\WearableLanterns
set CAMP=%WS%\Project Improvement\Campfire
set IMPORTS=%CAMP%\external\SkyrimSE\Scripts\Source;%CAMP%\Scripts\Source;%CAMP%\external\headers;%WL%\Scripts\Source;%WS%\Project Improvement\PapyrusExtenderSSE\Papyrus\Source\scripts;%WS%\Lilac\Scripts\Source;%CAMP%\.papyrus\skse64;%WS%\Project Improvement\SkyUI-Community\source\scripts;%GAME%\Data\Source\Scripts

REM run from a directory with no stray .psc (e.g. a scratch dir), not from Scripts\Source
"%GAME%\Papyrus Compiler\PapyrusCompiler.exe" "<ScriptName>.psc" ^
    -f="%GAME%\Data\Source\Scripts\TESV_Papyrus_Flags.flg" ^
    -i="%IMPORTS%" -o="%WL%\Scripts"
```

Why each dir (first match wins):
- `%CAMP%\external\SkyrimSE\Scripts\Source` - PapyrusUtil SE (`StorageUtil`).
- `%CAMP%\Scripts\Source` - `FrostUtil`, `FrostfallAPI`, the `_Frost_*` / `_Camp_*` graph,
  and `CommonArrayHelper` (which defines `LinkedArrayAddArmor`, used by
  `_Frost_LegacyArmorDatastore`).
- `%CAMP%\external\headers` - compile-only Devious Devices / Equipping Overhaul stubs
  (`_Camp_TentSystem` casts to `ddUnequipMCMScript` / `ddUnequipHandlerScript`).
- `%WL%\Scripts\Source` - the `_WL_*` sources.
- Papyrus Extender, Lilac, `%CAMP%\.papyrus\skse64` (merged SKSE64 headers - run
  `pscompile.py` once to build it), SkyUI-Community SDK, vanilla.

**CheskoPapyrusShared is deliberately excluded.** Both it and Campfire ship
`CommonArrayHelper.psc`, but only Campfire's copy defines `LinkedArrayAddArmor`; put
CheskoPapyrusShared first and the FrostfallAPI graph fails to compile
(`LinkedArrayAddArmor is not a function`). The meter base classes WL needs
(`Common_SKI_MeterWidget`, `CommonMeterInterfaceHandler`) are in Campfire's tree too, so
CheskoPapyrusShared is not needed at all.

The simpler pre-Frostfall chain (PapyrusUtil SE -> this checkout -> CheskoPapyrusShared ->
SkyUI SDK -> SKSE -> vanilla) still builds the six scripts that never touch `FrostUtil`, but
`_WL_LanternOil_v3` must use the Campfire environment above.

**Verified 2026-09-06 08:15-08:16.** Seven scripts, seven `.pex` written,
`0 error(s), 0 warning(s)` each:

    _WL_Compatibility.pex            12,660   08:15:58
    _WL_LanternOil_v3.pex            36,808   08:16:00
    _WL_LegacyMenu.pex                7,834   08:16:00
    _WL_NPCLanternActions.pex         5,891   08:16:01
    _WL_NPCMaintenanceScript.pex      1,386   08:16:02
    _WL_SkyUIConfigPanelScript.pex   67,153   08:16:04
    _WL_VendorStock.pex               6,005   08:16:05

## Frostfall carried-light warmth (2026-09-15, FIXPLAN #30 / #26 / #33)

The three items the 2026-09-06 pass left open were closed. Wearable Lanterns and Frostfall
are meant to be used together, so a lit lantern now takes the edge off the cold.

**#30 - carried-light warmth (`_WL_LanternOil_v3.psc`).** While a lantern is lit AND
Frostfall is installed, the lantern's existing 30s update loop calls the documented public
API `FrostUtil.ModPlayerExposure(-WARMTH_STEP, WARMTH_FLOOR)` in cold areas
(`FrostUtil.GetCurrentTemperature() < 10`). The negative amount warms; the `WARMTH_FLOOR`
limit stops the reduction at the Comfortable/Cold boundary, so the lantern *slows* the cold
but never makes the player warm.

- **Why not keywords (the original #30 route):** a lantern is not a garment, and Frostfall's
  `GetGearType` returns GEARTYPE_NOTFOUND for armour slot 55, so KID warmth keywords would be
  silently ignored - and a garment warmth value could not be gated on the lit state anyway.
- **Why not the heat-source system:** the smallest heat level is `1 -> -40` to the exposure
  target (a worn lantern would beat mild cold outright - a Requiem regression), and
  `FindClosestReferenceOfAnyTypeInListFromRef` only finds *placed* world refs, not an
  equipped left-hand `Light`, so it would not fire for the worn case at all.
- **Balance:** the nudge is a fixed 8 per 30s while the cold's own attractor scales with
  temperature (`TEMP_MOD = -5.1*temp + 102`, `_Frost_ExposureSystem.psc`), so it dominates in
  mild cold and is progressively overpowered in a blizzard. Knobs are script constants:
  `WARMTH_STEP` 8.0, `WARMTH_FLOOR` 40.0 (raise toward 50 harsher / 30 cozier), `WARMTH_INTERVAL`
  30.0. Final tuning is an in-game pass.
- **Plumbing:** `FrostfallActive()` caches a one-time `FrostUtil.GetAPI()` probe (re-probed
  each load in `OnPlayerLoadGame`). `OnUpdate` keeps the loop alive while lit+Frostfall even
  when the fuel mechanic is off; `AccrueBurnTime` was gated on the fuel setting so the
  now-sustained loop cannot bank oil/pollen burn time that the disabled mechanic never spends
  (which would otherwise burst-drain when re-enabled).
- **Save-safe / no-op:** only plain script variables were added (`frostfall_installed`,
  `WARMTH_STEP/FLOOR/INTERVAL`); no Frostfall record, form or property is touched. When
  `Frostfall.esp` is absent, `FrostUtil.GetAPI()` returns None and nothing is applied.
  `FrostUtil.pex` ships in Campfire, so the call resolves whenever Frostfall is present
  (Frostfall.esp masters Campfire.esm).

**#26 (`_WL_NPCMaintenanceScript.psc`).** The blocking `Utility.WaitMenuMode(1)` between
`RemoveItem` and `AddItem` was removed - the calls are sequential synchronous natives, and
an NPC has no inventory menu for `WaitMenuMode` to service.

**#33.** `meshes/chesko/_WL_Lightstone_WIP.nif` deleted (unreferenced dev artifact).

Adversarially reviewed 2026-09-15 (opus-4-6): API existence, `ModPlayerExposure` semantics,
save-safety, no script-load regression, Requiem balance, and the compile all confirmed.
`_WL_LanternOil_v3.pex` links `GetAPI` / `GetCurrentTemperature` / `ModPlayerExposure`.

### Deployment state

**Deployed and byte-current (2026-09-15).** The 2026-09-06 pass was deployed earlier; the
2026-09-15 pass was landed with `deploy.py --apply --only "Wearable Lanterns SE"` (MO2
closed), syncing its four files and one removal:

- update: `Scripts\_WL_LanternOil_v3.pex`, `Scripts\_WL_NPCMaintenanceScript.pex`,
  `Scripts\Source\_WL_LanternOil_v3.psc`, `Scripts\Source\_WL_NPCMaintenanceScript.psc`
- remove: `meshes\chesko\_WL_Lightstone_WIP.nif`

`buildcheck.py` then reports `Wearable Lanterns SE (tree) CURRENT, 106 files`, tracked and
byte-checked against this workspace. (That buildcheck run exits 1 only because of unrelated
UNTRACKED Interesting NPCs / 3DNPC folders AA added after 2026-09-13, which still need
`mod-sources.json` entries - not a Wearable Lanterns issue.)

In-game validation of the Frostfall warmth feel (and tuning of the `WARMTH_*` constants)
is the one remaining step.
