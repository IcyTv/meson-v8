#!/usr/bin/env python3
# Simple wrapper for building v8.

import os
import sys
import subprocess
import shutil
import argparse
import pathlib
import time
import glob


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
parser.add_argument('--header-out', default=os.getcwd(), type=pathlib.Path)
parser.add_argument('--target', default='debug')
parser.add_argument('--is-clang', action='store_true')
parser.add_argument('--cc-wrapper', default='')
parser.add_argument('gn', action='store', type=pathlib.Path)
parser.add_argument('gclient', action='store', type=pathlib.Path)
parser.add_argument('ninja', action='store', type=pathlib.Path)
parser.add_argument('--revision', action='store', type=str)
parser.add_argument('--shared', action='store_false')
parser.add_argument('--gen-headers', action='store_true')
parser.add_argument('--build', action='store_true')

args = parser.parse_args()

start = time.time()
build_dir = args.build_dir
if str(build_dir).endswith('.py'):
    build_dir = build_dir.parent

os.chdir(build_dir)

my_env = os.environ.copy()
my_env['DEPOT_TOOLS_WIN_TOOLCHAIN'] = '0'

outname = 'out/x64.custom-%s' % args.target

if args.gen_headers:
    args_file_found = False

    gn_args = [
        'is_component_build=false',
        'v8_monolithic=true',
        'v8_static_library=true',
        'v8_use_external_startup_data=false',
        'enable_iterator_debugging=true',
        'is_clang=%s' % ('true' if args.is_clang else 'false'),
        'cc_wrapper="%s"' % args.cc_wrapper,
        'is_debug=%s' % ('true' if args.target == 'debug' else 'false'),
        ]

    if args.shared:
        gn_args.append('v8_expose_symbols=true')

    if args.target == 'debug':
        gn_args.append('symbol_level=2')
        gn_args.append('v8_symbol_level=2')
        # gn_args.append('strip_absolute_paths_from_debug_symbols=true')

    if os.path.exists(os.path.join('v8', outname, 'args.gn')) and not args.build and os.path.exists(os.path.join(args.header_out, 'include')):
        args_file_found = True
        # print("Reusing existing installation")
        with open(os.path.join('v8', outname, 'args.gn'), 'r') as f:
            read = f.read()
            found = False
            for arg in gn_args:
                if not arg in read:
                    found = True
            if not found:
                sys.exit(0)


    if not args_file_found:
        print(bcolors.OKBLUE + "Setting up build directory %s %s..." %
              (args.build_dir, args.target) + bcolors.ENDC)

        subprocess.run(
            [args.gclient, 'config', '--name', 'v8', '--unmanaged',
             'https://chromium.googlesource.com/v8/v8.git'], shell=True, check=True,
            env=my_env
        )

        print(bcolors.OKGREEN + "Syncing..." + bcolors.ENDC)

        subprocess.run(
            [args.gclient, 'sync', '--revision', args.revision, '--shallow', '--no-history', '-A'], shell=True, check=True,
            env=my_env
        )

    print(bcolors.OKGREEN + "Configuring with gn..." + bcolors.ENDC)

    os.chdir('v8')

    subprocess.run(
        [args.gn, 'gen', outname, '--args=%s' % " ".join(gn_args)], shell=True, check=True,
        env=my_env
    )

    args.header_out.mkdir(parents=True, exist_ok=True)

    def keep(filename):
        # TODO figure out a better way to do this
        return filename.endswith('.h') or filename == 'libplatform' or filename == 'cppgc'

    def ignore_non_headers(d, files):
        return [f for f in files if not keep(f)]

    # TODO - Do we want to symlink?
    shutil.copytree(
        os.path.join(args.build_dir, 'v8', 'include'),
        os.path.join(args.header_out, 'include'),
        dirs_exist_ok=True,
        ignore=ignore_non_headers
    )

if args.build:
    # print(bcolors.OKGREEN + "Building v8 Monolith..." + bcolors.ENDC)

    out = subprocess.run(
        [args.ninja, '-C', os.path.join('v8', outname), 'v8_monolith'], check=True,
        env=my_env,
        shell=True
        # capture_output=True
    )

    # out = out.stdout.decode('utf-8')
    # if "no work to do." in out:
    #     sys.exit(0)
    # else:
    #     print(out)

    delta = time.time() - start

    print(bcolors.OKGREEN + "Done. Took %.02fs" % delta + bcolors.ENDC)

    # TODO - Add cross platform support. Currently only supports Windows.
    os.chdir('..')

    files = [
		'v8_monolith.lib',
    ]

    for i in files:
        shutil.copy(
            os.path.join(args.build_dir, 'v8', outname, 'obj', i),
            os.path.join(args.build_dir, os.path.basename(i))
        )

