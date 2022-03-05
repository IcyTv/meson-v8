project('v8', 'cpp', version: '9.9.115.7')

gclient = find_program('gclient')
gn = find_program('gn')
python = find_program('python3')
ninja = find_program('ninja')
sccache = find_program('sccache', required: false)

is_clang = meson.get_compiler('cpp').get_id() == 'clang'

cc_wrapper = ''
if sccache.found()
	cc_wrapper = sccache.full_path()
else
	
	ccache = find_program('ccache', required: false)
	if ccache.found()
		cc_wrapper = ccache.full_path()
	endif
endif

buildtype = 'release'
if get_option('debug')
	buildtype = 'debug'
endif

command = [
	python, join_paths(meson.current_source_dir(), 'build.py'),
	'--build-dir', meson.current_build_dir(), 
	'--header-out', meson.current_source_dir(),
	'--target', buildtype,
]
if is_clang
	command += ['--clang']
endif
command += [
	'--cc-wrapper', cc_wrapper,
	'--revision', meson.project_version(),
	gn.full_path(),
	gclient.full_path(),
	ninja.full_path(),
]

run_command(command + ['--gen-headers'], check: true)
# message(command.stdout())


outputs = [
	'v8_monolith.lib'
]

# TODO https://mesonbuild.com/Reference-manual_functions.html#custom_target
v8_build = custom_target('v8_build',
	output: outputs,
	input: [
		'build.py'
	],
	console: true,
	command: command + ['--build'],
)

inc = include_directories('include')

# TODO allow shared
libv8 = static_library('libv8',
	[v8_build],
	include_directories: inc,
)

v8_dep = declare_dependency(
	include_directories: inc,
	link_with: [libv8],
	version: meson.project_version(),
)