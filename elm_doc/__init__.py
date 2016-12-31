import imp
from distutils.sysconfig import get_python_lib


def elm_package_overlayer_path():
    search_paths = __path__ + [get_python_lib()]
    (_file, overlayer_path, _desc) = imp.find_module(
        "overlay_elm_package", search_paths)
    return overlayer_path
