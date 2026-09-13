"""Build a Wearable Lanterns release.

    python WLBuildRelease.py [version] [LE|SE]

Both arguments are prompted for when they are not given. The release is written next to
the checkout, not inside it:

    <parent>/WearableLanterns/WLBuildRelease.py  ->  <parent>/Wearable Lanterns 4.0.6 Release/

Everything that goes into the BSA is listed in WLArchiveManifest.txt, with paths written
Windows-style (``Scripts\\Source\\Foo.psc``) because that is what the Creation Kit's
Archive.exe expects; they are normalised here so the staging half also runs off Windows.
The archiver itself is a Windows executable.

This follows the same shape as Campfire/Frostfall/Last Seed's builders (see
``Campfire/buildcommon.py``), kept self-contained because Wearable Lanterns is its own
repository.

Two things it will not do quietly:

  * ship a Legendary Edition BSA as a Special Edition release. LE Archive.exe writes BSA
    version 104 and SE Archive.exe writes 105; the header is read back and checked.
  * ship an archive that is missing files. Archive.exe has been seen in this workspace to
    skip files and still exit 0, so the file count in the finished BSA is compared against
    the manifest.

Wearable Lanterns no longer ships PapyrusUtil - PapyrusUtil 4.7 is a separate mod and a
runtime dependency - and no longer machine-translates its MCM strings at build time. Any
``interface/translations/chesko_wearablelantern_<language>.txt`` file that is listed in
WLArchiveManifest.txt is packed like every other asset.
"""

import os
import shutil
import struct
import subprocess
import sys

# The directory holding this script, i.e. the project checkout.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Releases are built alongside the checkout, not inside it.
BUILD_ROOT = os.path.dirname(PROJECT_DIR)

MANIFEST = "WLArchiveManifest.txt"
BUILDER = "WLArchiveBuilder.txt"
PLUGIN = "Chesko_WearableLantern.esp"
ARCHIVE = "Chesko_WearableLantern.bsa"
README_FILES = (
    "wearablelanterns_readme.txt",
    "wearablelanterns_changelog.txt",
    "wearablelanterns_license.txt",
)

GAME_NAMES = {"LE": "Skyrim Legendary Edition", "SE": "Skyrim Special Edition"}

# The BSA packer from that runtime's Creation Kit. See external/README.md.
GAME_EXTERNALS = {
    "LE": os.path.join(PROJECT_DIR, "external", "Skyrim"),
    "SE": os.path.join(PROJECT_DIR, "external", "SkyrimSE"),
}

# BSA header version each runtime's archiver writes, and each runtime loads.
BSA_VERSION = {"LE": 104, "SE": 105}

# NIF header "user version 2". Legendary Edition meshes are 83, Special Edition 100.
NIF_USER_VERSION_2 = {"LE": 83, "SE": 100}


def fail(message):
    """Abort the build with a readable message instead of a traceback."""
    sys.stderr.write("\nERROR: " + message + "\n")
    sys.exit(1)


def prompt_version(argv):
    version = argv[0].strip() if argv else input("Enter the release version: ").strip()
    if not version:
        fail("No release version entered.")
    return version


def prompt_game(argv):
    """Which runtime to build for. Returns "LE" or "SE"."""
    answer = argv[1].strip() if len(argv) > 1 else input("(C)lassic Skyrim or Skyrim (SE)? ").strip()
    answer = answer.upper()
    if answer in ("C", "LE", "CLASSIC"):
        answer = "LE"
    if answer not in GAME_EXTERNALS:
        fail("Unknown game type '%s'. Please enter C or SE." % answer)
    print("Generating %s build." % GAME_NAMES[answer])
    return answer


def project_path(*parts):
    return os.path.join(PROJECT_DIR, *parts)


def externals_path(game, *parts):
    return os.path.join(GAME_EXTERNALS[game], *parts)


def require_archiver(game):
    """The archiver for this runtime, or a readable failure."""
    archiver = externals_path(game, "Archive.exe")
    if not os.path.isfile(archiver):
        fail(
            "%s is missing.\n"
            "    It is the %s Creation Kit's BSA packer. See external/README.md."
            % (archiver, GAME_NAMES[game])
        )
    return archiver


def normalize(manifest_line):
    """Turn a Windows-style manifest path into one for the current platform."""
    return manifest_line.strip().replace("\\", os.sep).replace("/", os.sep)


def read_manifest(manifest_file):
    """Read a manifest, skipping blank lines and # comments."""
    if not os.path.isfile(manifest_file):
        fail("Manifest not found: %s" % manifest_file)

    entries = []
    with open(manifest_file) as manifest:
        for line in manifest:
            entry = normalize(line)
            if entry and not entry.startswith("#"):
                entries.append(entry)
    if not entries:
        fail("Manifest is empty: %s" % manifest_file)
    return entries


def copy_file(source, destination):
    """Copy a single file, creating the destination directory as needed."""
    if not os.path.isfile(source):
        fail("Required file is missing: %s" % source)

    destination_dir = os.path.dirname(destination)
    if destination_dir:
        os.makedirs(destination_dir, exist_ok=True)
    shutil.copyfile(source, destination)


def copy_manifest(manifest_file, source_dir, destination_dir):
    """Stage every file the manifest lists.

    Every missing file is reported at once, rather than stopping at the first, so a
    manifest that has drifted from the project directory can be fixed in one pass.
    """
    entries = read_manifest(manifest_file)
    missing = [e for e in entries if not os.path.isfile(os.path.join(source_dir, e))]
    if missing:
        fail(
            "%d file(s) listed in %s are missing from %s:\n    %s"
            % (len(missing), os.path.basename(manifest_file), source_dir, "\n    ".join(missing))
        )

    for entry in entries:
        copy_file(os.path.join(source_dir, entry), os.path.join(destination_dir, entry))
    return entries


def nif_user_version_2(path):
    """The BS header version of a NIF, or None if it cannot be read.

    Header layout for the versions Skyrim uses: a header string terminated by \\n, then
    uint32 version, uint8 endian, uint32 user version, uint32 block count, uint32 BS
    version - the value the NIF Optimizer calls "user version 2".
    """
    with open(path, "rb") as nif:
        head = nif.read(256)
    end_of_string = head.find(b"\n")
    if end_of_string < 0 or len(head) < end_of_string + 18:
        return None
    return struct.unpack_from("<I", head, end_of_string + 1 + 4 + 1 + 4 + 4)[0]


def check_staged_meshes(game, datadir):
    """Stop before packing if the staged meshes are not in this runtime's NIF format.

    Special Edition loads a Legendary Edition mesh and vice versa, badly, without ever
    saying so - a mismatched release fails in game, later, on somebody else's save. This
    checkout's meshes are already Special Edition format; Campfire keeps its own in LE
    format and converts the staged copies with nifopt instead, which is why there is no
    conversion step here (see external/README.md).
    """
    meshes = os.path.join(datadir, "meshes")
    if not os.path.isdir(meshes):
        return

    expected = NIF_USER_VERSION_2[game]
    wrong = []
    for root, _, files in os.walk(meshes):
        for name in files:
            if not name.lower().endswith(".nif"):
                continue
            path = os.path.join(root, name)
            version = nif_user_version_2(path)
            if version != expected:
                wrong.append("%s (user version 2 = %s)" % (os.path.relpath(path, datadir), version))

    if wrong:
        fail(
            "%d staged mesh(es) are not in %s format (expected user version 2 = %d):\n    %s\n"
            "    Convert meshes/ with nifopt (see NifOptCLI/) before building for this runtime."
            % (len(wrong), GAME_NAMES[game], expected, "\n    ".join(wrong))
        )


def run_archiver(game, tempdir):
    """Run the Creation Kit's Archive.exe over the builder script to produce the BSA."""
    archiver = os.path.join(tempdir, "Archive.exe")
    try:
        result = subprocess.call([archiver, "./" + BUILDER], cwd=tempdir)
    except OSError as error:
        fail(
            "Could not run %s: %s\nArchive.exe is a Windows executable; BSA generation "
            "has to run on Windows (or under Wine)." % (archiver, error)
        )

    if result != 0:
        fail(
            "Archive.exe failed with exit code %d.\n"
            "    The staging directory was kept: %s\n"
            "    Its WLArchiveLog.txt says what the archiver was doing." % (result, tempdir)
        )


def read_bsa_header(path):
    """(version, folder count, file count) from a BSA header, or a readable failure."""
    if not os.path.isfile(path):
        fail("Archive.exe reported success but did not write %s." % path)

    with open(path, "rb") as archive:
        head = archive.read(36)
    if len(head) < 36 or head[:4] != b"BSA\x00":
        fail("%s is not a BSA (magic %r)." % (path, head[:4]))

    version, _offset, _flags, folders, files = struct.unpack_from("<IIIII", head, 4)
    return version, folders, files


def verify_archive(game, path, expected_files):
    """Refuse to ship an archive of the wrong format, or one that is missing files.

    The whole point of finding #8: the Legendary Edition archiver writes version 104,
    which Skyrim Special Edition will not load, and nothing in the build said so. The file
    count is checked as well because the Creation Kit packer has been observed in this
    workspace to skip files and still exit 0 (RequiemLotDPatch/tools/bsapack.py).
    """
    version, folders, files = read_bsa_header(path)
    expected_version = BSA_VERSION[game]

    if version != expected_version:
        other = next((g for g, v in BSA_VERSION.items() if v == version), None)
        fail(
            "%s is BSA version %d; %s needs %d.\n"
            "    %s"
            % (
                os.path.basename(path),
                version,
                GAME_NAMES[game],
                expected_version,
                "The archiver in %s is the %s one - see external/README.md."
                % (GAME_EXTERNALS[game], GAME_NAMES[other]) if other else
                "The archiver in %s is not a Skyrim BSA packer." % GAME_EXTERNALS[game],
            )
        )

    if files != expected_files:
        fail(
            "%s holds %d file(s); %s lists %d.\n"
            "    Archive.exe reported success but did not pack everything. The staging\n"
            "    directory and its WLArchiveLog.txt were kept next to the archive."
            % (os.path.basename(path), files, MANIFEST, expected_files)
        )

    print(
        "Verified %s: BSA version %d, %d folders, %d files."
        % (os.path.basename(path), version, folders, files)
    )


def reset_directory(path):
    """Create an empty directory, discarding anything already there."""
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)
    return path


def make_release_zip(dirname, zip_basename):
    """Zip up a finished release directory and drop the archive inside it."""
    staged_zip = shutil.make_archive(os.path.join(BUILD_ROOT, zip_basename), "zip", root_dir=dirname)
    final_zip = os.path.join(dirname, zip_basename + ".zip")
    shutil.move(staged_zip, final_zip)
    print("Created " + final_zip)
    return final_zip


def main(argv):
    print(" ")
    print("=======================================")
    print("|  Wearable Lanterns Release Builder  |")
    print("=======================================")
    print(" ")

    version = prompt_version(argv)
    game = prompt_game(argv)
    archiver = require_archiver(game)

    # Stage the BSA contents.
    print("Creating temp directories...")
    tempdir = reset_directory(os.path.join(BUILD_ROOT, "tmp"))
    datadir = os.path.join(tempdir, "Data")

    print("Copying project files...")
    entries = copy_manifest(project_path(MANIFEST), PROJECT_DIR, datadir)
    check_staged_meshes(game, datadir)

    # Build the release directory.
    dirname = os.path.join(BUILD_ROOT, "Wearable Lanterns " + version + " Release")
    print("Creating build directory...")
    reset_directory(dirname)

    # Generate BSA archive.
    print("Generating BSA archive...")
    copy_file(archiver, os.path.join(tempdir, "Archive.exe"))
    copy_file(project_path(BUILDER), os.path.join(tempdir, BUILDER))
    copy_file(project_path(MANIFEST), os.path.join(tempdir, MANIFEST))

    run_archiver(game, tempdir)
    verify_archive(game, os.path.join(tempdir, ARCHIVE), len(entries))

    # Copy files - Mod
    copy_file(project_path(PLUGIN), os.path.join(dirname, PLUGIN))
    copy_file(os.path.join(tempdir, ARCHIVE), os.path.join(dirname, ARCHIVE))

    for readme in README_FILES:
        copy_file(project_path("readmes", readme), os.path.join(dirname, "readmes", readme))

    # Create release zip
    make_release_zip(dirname, "WearableLanterns_" + version.replace(".", "_") + "_Release")

    # Clean Up
    print("Removing temp files...")
    shutil.rmtree(tempdir)

    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
