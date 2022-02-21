# Meson v8

A very basic (and hacky) wrapper for the [v8](https://chromium.googlesource.com/v8/v8) engine for use with [meson](https://mesonbuild.com/).

To use it, just add the v8.wrap file to your project and add

```meson
v8 = dependency('v8')
```

Currently it only supports static monolithic builds.
