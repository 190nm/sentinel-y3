from distutils.core import setup, Extension
setup(name="Y3gk", version="1.0", ext_modules=[Extension("Y3gk", ["Y3gk.c", "libgk.c"])])
