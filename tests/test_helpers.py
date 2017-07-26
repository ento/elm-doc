from elm_doc import elm_package_overlayer_env


def test_ld_preload_is_preserved():
    existing_preload = 'existing.lib'
    base_env = {
        'DYLD_INSERT_LIBRARIES': existing_preload,
        'LD_PRELOAD': existing_preload,
    }

    env = elm_package_overlayer_env('', '', base_env)

    assert existing_preload in env['LD_PRELOAD']
    assert existing_preload in env['DYLD_INSERT_LIBRARIES']


def test_overlayer_environment_is_configured():
    original_elm_package = 'elm-package.json'
    modified_elm_package = 'tmp/elm-package.json'
    env = elm_package_overlayer_env(modified_elm_package, original_elm_package, {})

    assert env['USE_ELM_PACKAGE'] == modified_elm_package
    assert env['INSTEAD_OF_ELM_PACKAGE'] == original_elm_package
    # test for existence but not the actual path because the helper function
    # to get the overlayer path is private. there might be a better way to test this?
    assert len(env['DYLD_INSERT_LIBRARIES']) > 0
    assert len(env['LD_PRELOAD']) > 0
