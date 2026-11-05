"""Partial export of a chunked track for the GUI's track viewer: only the chunks it shows are written, and only when
the data they are made of changed.

A serializer supporting it implements `serialize_chunks(data, path, id, block, chunks)` with `export_chunks`: it
gives a fingerprint of every chunk (a hash of the data the chunk's files are made of, so an edit changes the
fingerprints of the chunks it shows in only) and a function writing some chunks. `<path>/chunks_state.json` keeps
the fingerprint and the files of every chunk on disk. A requested chunk is written when its fingerprint differs (or a
file is missing); a chunk not requested keeps its files, unless its fingerprint changed: then they are deleted, and it
is written when requested again.
"""

import hashlib
import json
import os
from typing import Any, Callable, Dict, Iterable, List

STATE_FILE_NAME = 'chunks_state.json'


def fingerprint(*parts: Any) -> str:
    """Hash of JSON-able values (dicts in any key order)"""
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=repr).encode()).hexdigest()


def export_chunks(
    path: str,
    fingerprints: List[str],
    requested: Iterable[int],
    write_chunks: Callable[[List[int]], Dict[int, List[str]]],
) -> Dict[int, Dict[str, Any]]:
    """Writes the requested chunks that are out of date. `write_chunks` gets their indices (ascending) and returns the
    files written for each. Returns {index: {'fingerprint', 'files'}} of the requested chunks"""
    state_path = os.path.join(path, STATE_FILE_NAME)
    try:
        with open(state_path) as f:
            state = {int(k): v for k, v in json.load(f).items()}
    except OSError, ValueError:
        state = {}
    requested = sorted({i for i in requested if 0 <= i < len(fingerprints)})
    requested_set = set(requested)
    for i in list(state):
        if i < len(fingerprints) and (state[i]['fingerprint'] == fingerprints[i] or i in requested_set):
            continue
        for file_path in state.pop(i)['files']:
            if os.path.isfile(file_path):
                os.remove(file_path)
    outdated = [
        i
        for i in requested
        if i not in state
        or state[i]['fingerprint'] != fingerprints[i]
        or not all(os.path.isfile(f) for f in state[i]['files'])
    ]
    os.makedirs(path, exist_ok=True)
    if outdated:
        written = write_chunks(outdated)
        for i in outdated:
            files = written.get(i, [])
            # files of the previous version which this one has not (e.g. a chunk without props has no extra JSON)
            for file_path in state.get(i, {}).get('files', []):
                if file_path not in files and os.path.isfile(file_path):
                    os.remove(file_path)
            state[i] = {'fingerprint': fingerprints[i], 'files': files}
    with open(state_path, 'w') as f:
        json.dump({str(k): v for k, v in sorted(state.items())}, f)
    return {i: state[i] for i in requested}
