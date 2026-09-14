"""Compatibility bridge: the Facebook runner belongs to DownloadImgFacebook.

AskCpl imports this bridge only to expose optional controls; implementation and
launchers live beside the addon in FacebookMediaHelper.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_RUNNER_PATH = Path(__file__).resolve().parent.parent / "DownloadImgFacebook" / "FacebookMediaHelper" / "background_runner.py"
_SPEC = spec_from_file_location("fb_addon_background_runner", _RUNNER_PATH)
if not _SPEC or not _SPEC.loader:
    raise ImportError(f"Facebook addon runner not found: {_RUNNER_PATH}")
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

default_config = _MODULE.default_config
load_config = _MODULE.load_config
save_config = _MODULE.save_config
start = _MODULE.start
stop = _MODULE.stop
status = _MODULE.status
set_logon_task = _MODULE.set_logon_task
task_exists = _MODULE.task_exists
