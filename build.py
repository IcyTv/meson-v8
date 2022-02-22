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

assert(args.gen_headers or args.build,
       'Must specify either --gen-headers or --build')

start = time.time()
print(bcolors.OKBLUE + "Setting up build directory %s %s..." %
      (args.build_dir, args.target) + bcolors.ENDC)

build_dir = args.build_dir
if str(build_dir).endswith('.py'):
    build_dir = build_dir.parent

os.chdir(build_dir)

my_env = os.environ.copy()
my_env['DEPOT_TOOLS_WIN_TOOLCHAIN'] = '0'

outname = 'out/x64.custom-%s' % args.target

if args.gen_headers:
    if os.path.exists(os.path.join('v8', outname, 'args.gn')) and not args.build and os.path.exists(os.path.join(args.header_out, 'include')):
        print("Reusing existing installation")
        sys.exit(0)

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

    gn_args = [
        'is_component_build=false',
        'v8_monolithic=true',
        'v8_static_library=%s' % ('true' if args.shared else 'false'),
        'v8_use_external_startup_data=false',
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

    subprocess.run(
        [args.gn, 'gen', outname, '--args=%s' % " ".join(gn_args)], shell=True, check=True,
        env=my_env
    )

    args.header_out.mkdir(parents=True, exist_ok=True)

    def keep(filename):
        # TODO figure out a better way to do this
        return filename.endswith('.h') or filename == 'libplatform'

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
    print(bcolors.OKGREEN + "Building v8 Monolith..." + bcolors.ENDC)

    subprocess.run(
        [args.ninja, '-C', os.path.join('v8', outname), 'v8_monolith'], shell=True, check=True,
        env=my_env
    )

    delta = time.time() - start

    print(bcolors.OKGREEN + "Done. Took %.02fs" % delta + bcolors.ENDC)

    # TODO - Add cross platform support. Currently only supports Windows.
    os.chdir('..')

    shutil.copy(
        os.path.join(args.build_dir, 'v8', outname, 'obj/v8_monolith.lib'),
        os.path.join(args.build_dir, 'v8_monolith.lib')
    )

    shutil.copy(
        os.path.join(args.build_dir, 'v8', outname, 'obj/v8_libplatform.lib'),
        os.path.join(args.build_dir, 'v8_libplatform.lib')
    )

    shutil.copy(
        os.path.join(args.build_dir, 'v8', outname, 'obj/v8_libbase.lib'),
        os.path.join(args.build_dir, 'v8_libbase.lib')
    )

    pdbs = [
        'v8_base_without_compiler_0_cc.pdb',
        'v8_cppgc_shared_cc.pdb',
        'v8_initializers_cc.pdb',
        'v8_init_cc.pdb',
        'v8_libbase_cc.pdb',
        'v8_libplatform_cc.pdb',
        'v8_snapshot_cc.pdb',
        'v8_compiler_cc.pdb',
        'v8_bigint_cc.pdb',
        'v8_base_without_compiler_1_cc.pdb',
    ]

    if sys.platform == 'win32':
        for pdb in pdbs:
            path = os.path.join('v8', outname, 'obj', pdb)
            shutil.copy(path, pdb)
