#!/usr/bin/env python3

import argparse
import subprocess
import os
import sys


# Function to check if the binary exists
def binary_exists(path):
    return os.path.exists(path) or subprocess.call(['which', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

# Attempt to automatically set the path based on the operating system
# If this doesn't work, modify the variables for your OS to the correct location.
if os.name == "posix":
    # Further check for macOS specifically
    if 'darwin' in sys.platform:
        print("Operating System: macOS")
        PATH_TO_OPENSCAD = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'
    else:  # Assume Linux if not macOS
        print("Operating System: Linux")
        PATH_TO_OPENSCAD = '/usr/bin/openscad'
        
        if binary_exists(PATH_TO_OPENSCAD):
            print(f"Binary found at {PATH_TO_OPENSCAD}")
        else:
            print(f"Binary not found at {PATH_TO_OPENSCAD}")

        POSSIBLE_PATH_LOCATIONS_FOR_OPENSCAD_NIGHTLY = [
            '/snap/bin/openscad-nightly', #Path when installed using the snap tooling
            '/usr/bin/openscad-nightly' #Path when installed using apt (also used in dockerfile)
        ]

        PATH_TO_OPENSCAD_NIGHTLY = ''
        for LOCATION in POSSIBLE_PATH_LOCATIONS_FOR_OPENSCAD_NIGHTLY:
            if binary_exists(LOCATION):
                print(f"Nightly binary found at {LOCATION}")
                PATH_TO_OPENSCAD_NIGHTLY = LOCATION

        if PATH_TO_OPENSCAD_NIGHTLY == '':
            print('Nightly binary not installed')

elif os.name == "nt":  # Windows
    print("Operating System: Windows")
    PATH_TO_OPENSCAD = r'C:\Program Files\OpenSCAD\openscad.exe'
    
    if binary_exists(PATH_TO_OPENSCAD):
        print(f"Binary found at {PATH_TO_OPENSCAD}")
    else:
        print(f"Binary not found at {PATH_TO_OPENSCAD}")

else:
    print("Unsupported OS")
    exit(1)


# For actual dimensions, please see profiles.scad.
class BuildSizeConfig:
    NANO = 'nano'
    MINI = 'mini'
    MICRO = 'micro'
    CUSTOM = 'custom'


FILE_DIR = os.path.dirname(os.path.abspath(__file__))

RACK_BUILD_DIR = os.path.join(FILE_DIR, 'rack/print')
BUILD_PARENT_DIR = os.path.join(FILE_DIR, 'stl')
RACK_MOUNT_DIR = os.path.join(FILE_DIR, 'rack-mount')
RACK_BUILD_TARGET_SUB_DIR = 'rack'

ASSEMBLY_GIF_DIR = os.path.join(FILE_DIR, 'rack/assembly')
ASSEMBLY_GIF_BUILD_DIR = os.path.join(FILE_DIR, 'assembly-guide/gifs')
ASSEMBLY_GIF_TEMP_DIR = os.path.join(ASSEMBLY_GIF_BUILD_DIR, 'tmp')
BUILD_GIF_FROM_PNG_SCRIPT = os.path.join(FILE_DIR, 'misc/animate.sh')

ASSEMBLY_STEPS = [
    ('slideHexNutsIntoYBar.scad', 24),
    ('addMagnetsToMagnetModules.scad', 16),
    ('addMagnetsToSideWall.scad', 16),
    ('attachXBarWithYBar.scad', 16),
    ('screwXBarAndYBar.scad', 16),
    ('attachSideConnectorModulesToYBars.scad', 16),
    ('connectXYTrayWithMainRails.scad', 24),
    ('insertDowelsIntoSideWall.scad', 16),
    ('propUpBottomXYTraywithSideWalls.scad', 16),
    ('slideHexNutsIntoYBarXYPlate.scad', 16),
    ('attachXYTrays.scad', 24),
    ('slideHexNutToFeet.scad', 16),
    ('insertFeet.scad', 16),
    ('screwFeet.scad', 16),
    ('attachXYPlates.scad', 16)
]

MOUNT_ANIMATIONS = [
    ('enclosed-box', 32),
    ('tray', 32),
    ('patch-panel', 32),
    ('angle-bracket', 32)
]

def main():
    if not assertOpenscadExists():
        print(
            "Could not find OpenSCAD binary. Please make sure it's configured in rbuild.py. Currently only Darwin and Linux have been tested to work.")

    parser = argparse.ArgumentParser(
        prog='rbuild',
        description='CLI-based helper utility to build project items. '
                    'This includes both the rack and also rack-mount items'
    )

    parser.add_argument(
        '-b',
        nargs='?',
        const='all',
        help='Build command. Optionally pass in a specific part name to only build that item. '
             'Defaults to building everything'
    )

    parser.add_argument(
        '-c',
        default=BuildSizeConfig.MICRO,
        choices=[BuildSizeConfig.NANO, BuildSizeConfig.MINI, BuildSizeConfig.MICRO, BuildSizeConfig.CUSTOM],
        help='Build size config profile. This will determine the size of the rack you wish to generate. '
             'For actual dimensions, please see profiles.scad.'
    )

    parser.add_argument(
        '-t',
        default="",
        help='Target directory to build STLs in (is under the /stl directory). Default target directory is based on '
             'the config.'
    )

    parser.add_argument(
        '-dz',
        default=0,
        help='Override number of rail screws (ie override rail height). Defaults to profile settings.'
    )

    parser.add_argument(
        '--nightly',
        action='store_true',
        help='Use openscad-nightly command. Should result in much faster build times.'
    )

    parser.add_argument(
        '--build_gifs',
        action='store_true',
        help='Generate the GIFS for the assembly guide, as well as various rack-mount systems.'
    )

    args = parser.parse_args()
    run_build(args)


def run_build(args):
    build_var = args.b
    config_var = args.c
    target_var = args.t
    dz = args.dz
    nightly = args.nightly
    build_gifs = args.build_gifs

    if (build_var is not None) == (build_gifs is True):
        print("Please either provide the build (-b) variable, or the build-gifs option (--build-gifs)")
        return

    if build_gifs:
        build_assembly_gifs(config_var, dz, nightly)
        build_rack_mount_gifs(config_var, nightly)
        return

    if target_var != "":
        final_target_directory_name = target_var
    else:
        final_target_directory_name = config_var

    rackBuildDirFull = os.path.join(BUILD_PARENT_DIR, final_target_directory_name, RACK_BUILD_TARGET_SUB_DIR)

    if not os.path.exists(rackBuildDirFull):
        os.makedirs(rackBuildDirFull)

    if build_var == 'all':
        for dir_file in os.listdir(RACK_BUILD_DIR):
            build_single(RACK_BUILD_DIR, rackBuildDirFull, dir_file, config_var, dz, nightly)

        return

    filename_rack = find_rack(build_var)

    if not (filename_rack):
        print('File:', build_var, 'not found!')
        return

    if filename_rack:
        build_single(RACK_BUILD_DIR, rackBuildDirFull, filename_rack, config_var, dz, nightly)

def build_single(build_dir, target_dir, filename, config, dz, nightly):
    print('Building:', filename, 'from', build_dir, 'to', target_dir)
    openscad_args = construct_openscad_args(build_dir, target_dir, filename, config, dz)
    run_openscad(openscad_args, nightly)


def build_assembly_gifs(config, dz, nightly):
    print('Building assembly-gifs. Source Dir:', ASSEMBLY_GIF_DIR, '| Target:', ASSEMBLY_GIF_BUILD_DIR)

    if not os.path.exists(ASSEMBLY_GIF_TEMP_DIR):
        os.makedirs(ASSEMBLY_GIF_TEMP_DIR)

    for (fileName, numSteps) in ASSEMBLY_STEPS:
        print('Building GIF for', fileName)
        openscad_args = construct_openscad_animation_args(
            ASSEMBLY_GIF_DIR, ASSEMBLY_GIF_TEMP_DIR, fileName, config, dz, numSteps
        )
        run_openscad(openscad_args, nightly)
        build_gif_from_png(fileName, ASSEMBLY_GIF_TEMP_DIR, ASSEMBLY_GIF_BUILD_DIR)

def build_rack_mount_gifs(config, nightly):
    print('Building GIFs for rack-mounts systems')

    for (system, numSteps) in MOUNT_ANIMATIONS:
        print('Building GIF for', system)
        system_dir = os.path.join(RACK_MOUNT_DIR, system)
        temp_dir = os.path.join(system_dir, 'tmp')

        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        openscad_args = construct_openscad_animation_args(system_dir, temp_dir, 'animate.scad', config, 10, numSteps)
        run_openscad(openscad_args, nightly)
        build_gif_from_png('animate', temp_dir, system_dir)

def build_gif_from_png(fileName, source, target):

    if not os.path.exists(target):
        os.makedirs(target)

    try:
        subprocess.run(["bash", BUILD_GIF_FROM_PNG_SCRIPT, fileName, source, target],
                       check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error calling shell script: {e}")


def construct_openscad_args(build_dir, target_dir, filename, config, dz, format='.stl'):
    print(build_dir, target_dir, filename)
    source = os.path.join(build_dir, filename)
    target = os.path.join(target_dir, os.path.splitext(filename)[0] + format)

    openscad_args = ['--export-format', 'binstl']
    openscad_args += ['-D', 'profileName=\"' + config + '\"']

    if dz != 0:
        openscad_args += ['-D', 'numRailScrews=' + dz]

    # added this here because for some reason the current nightly build won't listen to the $fn definition in
    # helper/common.scad
    openscad_args += ['-D', '$fn=64']
    openscad_args += ['-o', target, source]

    return openscad_args


def construct_openscad_animation_args(build_dir, target_dir, filename, config, dz, steps):
    source = os.path.join(build_dir, filename)
    target = os.path.join(target_dir, os.path.splitext(filename)[0] + '.png')

    openscad_args = []
    openscad_args += ['--colorscheme', 'Tomorrow Night']
    openscad_args += ['--render']
    openscad_args += ['--imgsize', '1920,1080']
    openscad_args += ['--projection', 'o']
    openscad_args += ['--animate', str(steps)]
    openscad_args += ['-o', target, source]

    return openscad_args


def find_rack(filename):
    return find_scad_file(RACK_BUILD_DIR, filename)


def find_scad_file(directory, filename):
    for dir_file in os.listdir(directory):
        dir_file_normalized = dir_file.lower()
        filename_normalized = filename.lower()

        if dir_file_normalized.endswith("_p.scad"):
            dir_file_normalized = dir_file_normalized[:-7]

        if filename_normalized.endswith("_p.scad"):
            filename_normalized = filename_normalized[:-7]

        if dir_file_normalized == filename_normalized \
                or os.path.splitext(dir_file_normalized)[0] == filename_normalized:
            return dir_file
    return None


def run_openscad(options, nightly):
    if nightly:
        command = [PATH_TO_OPENSCAD_NIGHTLY, '--enable', 'fast-csg', '--enable', 'manifold']
    else:
        command = [PATH_TO_OPENSCAD]

    command += options
    try:
        subprocess.check_output(command, universal_newlines=True, stderr=subprocess.DEVNULL)

    except FileNotFoundError:
        print('OpenSCAD command not found! '
              'Please make sure that you have the OpenSCAD binary configured in rbuild.py.'
              '(Currently needs Linux/Mac for this)')


def assertOpenscadExists():
    return os.path.exists(PATH_TO_OPENSCAD)


if __name__ == '__main__':
    main()
