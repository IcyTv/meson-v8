project('v8', 'cpp', version: '9.9.115.7')

gclient = find_program('gclient')
gn = find_program('gn')
python = find_program('python3')
ninja = find_program('ninja')
sccache = find_program('sccache', required: false)

# v8_src = custom_target('v8_src',
# 	output: 'v8',
# 	console: true,
# 	command: [fetch, '--no-history', 'v8'],
# 	install: true,
# 	install_dir: 'v8',
# )

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

command = [
	python, '@INPUT@', 
	'--build-dir', meson.current_build_dir(), 
	'--target', get_option('buildtype'),
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

v8_build = custom_target('v8_build',
	output: [
		'v8_monolith.lib',
	],
	input: [
		'build.py'
	],
	console: true,
	command: command,
)

# TODO allow shared
v8 = static_library('v8', [v8_build])

inc_path = join_paths(meson.current_build_dir(), 'v8', 'include')
inc = include_directories(inc_path)

v8_dep = declare_dependency(
	include_directories: inc,
	link_with: v8,
)