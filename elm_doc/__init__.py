import imp


def elm_package_overlayer_path():
    (_file, overlayer_path, _desc) = imp.find_module("overlay_elm_package", __path__)
    return overlayer_path
