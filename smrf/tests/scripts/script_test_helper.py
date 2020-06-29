import os
import shutil
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader


def create_script_spec(script_name):

    # There are 3 places that the scripts can live
    # 1. In the dev environment
    # 2. In the docker image
    # 3. Installed through wheel
    SMRF_SCRIPT_HOME = [
        os.path.abspath(__file__ + '../../../../../') + '/scripts/',
        '/usr/local/bin/'
    ]

    found = False
    for sch in SMRF_SCRIPT_HOME:
        filename = os.path.join(sch, script_name)
        if os.path.exists(filename):
            SMRF_SCRIPT_HOME = filename
            found = True
            break

    # if it wasn't found then it should be installed
    if not found:
        SMRF_SCRIPT_HOME = shutil.which(script_name)

    return spec_from_loader(
        script_name,
        SourceFileLoader(
            script_name,
            SMRF_SCRIPT_HOME
        )
    )


def load_script_as_module(script_name):
    """
    Load given script file in the 'scripts' folder and load it as a module.

    Example:

    .. code-block:: Python

        from .script_test_helper import load_script_as_module

        script = load_script_as_module('script_name')

        script.method_from_script()

    Args:
        script_name: string
            Name of the script

    Returns:
        Script as module
    """
    spec = create_script_spec(script_name)
    script = module_from_spec(spec)
    spec.loader.exec_module(script)

    return script
