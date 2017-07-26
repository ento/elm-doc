from collections import ChainMap
import imp
from distutils.sysconfig import get_python_lib


def elm_package_overlayer_env(
        use_elm_package_path,
        instead_of_elm_package_path,
        base_environ):
    overlayer_path = _elm_package_overlayer_path()
    # todo: make overlayer support windows if we want to (can we?)
    return dict(ChainMap(
            {
                'USE_ELM_PACKAGE': use_elm_package_path,
                'INSTEAD_OF_ELM_PACKAGE': instead_of_elm_package_path,
                'DYLD_INSERT_LIBRARIES': _prepend_overlayer(
                    base_environ, 'DYLD_INSERT_LIBRARIES', overlayer_path),
                'LD_PRELOAD': _prepend_overlayer(base_environ, 'LD_PRELOAD', overlayer_path),
            },
            base_environ,
        ))


def _elm_package_overlayer_path():
    search_paths = __path__ + [get_python_lib()]
    (_file, overlayer_path, _desc) = imp.find_module(
        "overlay_elm_package", search_paths)
    return overlayer_path


def _prepend_overlayer(base_environ, key, overlayer_path):
    if key in base_environ:
        return '{}:{}'.format(overlayer_path, base_environ[key])
    else:
        return overlayer_path
