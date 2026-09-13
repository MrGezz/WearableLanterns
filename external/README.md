# External build dependencies

Wearable Lanterns needs one thing that is not part of the mod: the Creation Kit's BSA
packer. It is built separately for each Skyrim runtime and the two are **not**
interchangeable, so a copy of each lives here and `WLBuildRelease.py` picks the matching
one.

    external/Skyrim/Archive.exe      Skyrim Legendary Edition  - writes BSA version 104
    external/SkyrimSE/Archive.exe    Skyrim Special Edition    - writes BSA version 105

This mirrors `Campfire/external/`, which is the house pattern for the survival mods; see
that directory's README.

## Which is which

Both executables report the same version resource (ProductVersion 2.0.0.0,
FileVersion 1.0.0.1, "Archive creation tool."), so the only reliable way to tell them
apart is the archive they produce. Measured 2026-09-06 by packing the same two staged
files with each:

| File | Size | BSA version written |
| --- | --- | --- |
| `external/Skyrim/Archive.exe` | 428,032 | 104 |
| `external/SkyrimSE/Archive.exe` | 273,920 | 105 |

`external/Skyrim/Archive.exe` is the copy that used to sit in the project root and is
byte-identical to `Campfire/external/Skyrim/Archive.exe` (MD5 `76d4d947...`). It was the
one the old build script ran, which is why a "Special Edition" release built from this
checkout would have shipped a Legendary Edition BSA that Skyrim SE rejects.

`external/SkyrimSE/Archive.exe` is byte-identical to `Campfire/external/SkyrimSE/Archive.exe`
(MD5 `712f917e...`), the Special Edition Creation Kit's packer.

`WLBuildRelease.py` does not take Archive.exe's word for it: after the archiver runs it
reads the BSA header back and aborts unless the version and the file count are what the
target runtime and the manifest say they should be. The Creation Kit packer has been seen
in this workspace to skip files and still report success - see
`RequiemLotDPatch/tools/bsapack.py`, which was written after Archive.exe silently dropped
201 voice files from Inconsequential NPCs. Wearable Lanterns ships no voice assets, but
the check costs nothing.

## What is not here

PapyrusUtil. Wearable Lanterns used to ship `SKSE/Plugins/StorageUtil.dll` and the
`JsonUtil` / `StorageUtil` scripts; all of it was removed during the SSE port (see
`../PORT-SSE.md`). PapyrusUtil 4.7 is a separate MO2 mod and a runtime dependency of the
build, not something a Wearable Lanterns release installs.

`nifopt.exe`. Campfire keeps `meshes/` in Legendary Edition format and converts the staged
copies during the build; this checkout's 32 meshes are already Special Edition format
(NIF user version 2 = 100), so there is nothing to convert. `WLBuildRelease.py` verifies
that the staged meshes match the runtime being built for and stops if they do not.
