"""Write guard shared by the one-time pipeline scripts.

The scripts in this directory regenerate files that were later refined by hand.
Running one by accident would overwrite the real deliverables in source/, sprites/
and analysis/. Importing `guarded_open` as `open` makes any write into those
directories fail with a clear message unless CATERKILLER_PIPELINE_OVERWRITE=1 is set.
Writes anywhere else (for example build/) pass through unchanged.
"""

import builtins
import os

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
CATERKILLER_DIR = os.path.normpath(os.path.join(PIPELINE_DIR, '..'))
REPO_DIR = os.path.normpath(os.path.join(CATERKILLER_DIR, '..', '..'))
OUTPUT_DIR = os.path.join(REPO_DIR, 'build', 'caterkiller', 'pipeline')
PROTECTED = [os.path.join(CATERKILLER_DIR, d) for d in ('source', 'sprites', 'analysis', 'original')]
OVERRIDE_VAR = 'CATERKILLER_PIPELINE_OVERWRITE'


def output_path(*parts):
    """Path under build/caterkiller/pipeline/, creating the directory."""
    path = os.path.join(OUTPUT_DIR, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def guarded_open(file, mode='r', *args, **kwargs):
    if any(c in mode for c in 'wa+x') and os.environ.get(OVERRIDE_VAR) != '1':
        # realpath so a symlink into a protected directory is caught too
        target = os.path.realpath(os.fspath(file))
        for root in PROTECTED:
            root = os.path.realpath(root)
            if target == root or target.startswith(root + os.sep):
                raise SystemExit(
                    f"refusing to overwrite {os.path.relpath(target, REPO_DIR)}: it is a hand-refined "
                    f"deliverable. Write under build/ instead, or set {OVERRIDE_VAR}=1 to force.")
    # Default text files to UTF-8 unless the caller gave an encoding (keyword, or
    # positionally as open()'s fourth argument after buffering).
    if 'b' not in mode and 'encoding' not in kwargs and len(args) < 2:
        kwargs['encoding'] = 'utf-8'
    return builtins.open(file, mode, *args, **kwargs)
