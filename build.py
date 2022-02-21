#!/usr/bin/env python3
# Simple wrapper for building v8.

import os
import sys
import subprocess
import shutil
import argparse
import pathlib
import time


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


if sys.platform != 'win32':
    sys.exit('This script is for Windows only.')

parser = argparse.ArgumentParser(description='Build v8.')

parser.add_argument('--build-dir', default=os.getcwd(), type=pathlib.Path)
parser.add_argument('--target', default='debug')
parser.add_argument('--is-clang', action='store_true')
parser.add_argument('--cc-wrapper', default='')
parser.add_argument('gn', action='store', type=pathlib.Path)
parser.add_argument('gclient', action='store', type=pathlib.Path)
parser.add_argument('ninja', action='store', type=pathlib.Path)
parser.add_argument('--revision', action='store', type=str)
parser.add_argument('--shared', action='store_false')

args = parser.parse_args()

start = time.time()
print(bcolors.OKBLUE + "Setting up build directory %s..." %
      args.build_dir + bcolors.ENDC)

build_dir = args.build_dir
if str(build_dir).endswith('.py'):
	build_dir = build_dir.parent

os.chdir(build_dir)

my_env = os.environ.copy()
my_env['DEPOT_TOOLS_WIN_TOOLCHAIN'] = '0'

subprocess.run(
    [args.gclient, 'config', '--name', 'v8', '--unmanaged',
        'https://chromium.googlesource.com/v8/v8.git'], shell=True, check=True,
    env=my_env
)

print(bcolors.OKGREEN + "Syncing..." + bcolors.ENDC)

subprocess.run(
    [args.gclient, 'sync', '--revision', args.revision, '--shallow', '--no-history'], shell=True, check=True,
    env=my_env
)

print(bcolors.OKGREEN + "Configuring with gn..." + bcolors.ENDC)

os.chdir('v8')

outname = 'out/x64.custom-%s' % args.target

gn_args = [
    'is_component_build=false',
    'v8_monolithic=true',
    'v8_static_library=%s' % ('true' if args.shared else 'false'),
    'v8_use_external_startup_data=false',
    'is_clang=%s' % ('true' if args.is_clang else 'false'),
    'cc_wrapper="%s"' % args.cc_wrapper,
]

subprocess.run(
    [args.gn, 'gen', outname, '--args=%s' % " ".join(gn_args)], shell=True, check=True,
    env=my_env
)

print(bcolors.OKGREEN + "Building v8 Monolith..." + bcolors.ENDC)

subprocess.run(
    [args.ninja, '-C', outname, 'v8_monolith'], shell=True, check=True,
    env=my_env
)

delta = time.time() - start

print(bcolors.OKGREEN + "Done. Took %.02f" % delta + bcolors.ENDC)

# TODO - Add cross platform support. Currently only supports Windows.
os.chdir('..')

shutil.copy(
    os.path.join('v8', outname, 'obj/v8_monolith.lib'),
    'v8_monolith.lib'
)

shutil.copy(
    os.path.join('v8', outname, 'obj/v8_libplatform.lib'),
    'v8_libplatform.lib'
)

shutil.copy(
    os.path.join('v8', outname, 'obj/v8_libbase.lib'),
    'v8_libbase.lib'
)
