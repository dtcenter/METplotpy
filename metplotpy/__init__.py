from distutils.util import convert_path

main_ns = {}
version_path = convert_path('docs/version')
with open(version_path) as version_file:
    exec(version_file.read(), main_ns)
__version__ = main_ns['__version__']