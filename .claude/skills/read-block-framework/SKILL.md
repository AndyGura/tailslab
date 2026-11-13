---
name: read-block-framework
description: Use when extending the core parsing framework itself — adding a new generic DataBlock subclass to library/read_blocks, a new generic Angular *.block-ui component, or new cross-cutting serializer behavior in serializers/base.py. NOT for defining a new game file format or adding fields to an existing one — use nfs-resource-formats for that (it composes this framework's existing blocks instead of extending it).
---

# Read-block framework development

> Keep this file in sync with the codebase: if something here is wrong, stale, or missing, fix it
> as part of your change. Describe only the current state, dry and reference-like — never
> change-log prose ("used to be X", "was migrated", "no longer exists"). If something's gone,
> remove its mention instead of noting its removal.

This project's whole parsing/serialization/GUI/docs pipeline is driven by one class hierarchy:
`DataBlock` (`library/read_blocks/basic.py`). This skill covers changing that hierarchy or its
generic Angular counterparts. If you just want to describe a new file format using blocks that
already exist, use skill `nfs-resource-formats` instead — read its cheat-sheet first, since the
block you need very likely already exists.

## The `DataBlock` contract

Required (abstract):
- `read(self, ctx: ReadContext, name='', read_bytes_amount=None) -> value` — parse from `ctx.buffer`.
- `write(self, data, ctx: WriteContext=None, name='') -> bytes` — serialize back.

Never override `unpack()`/`pack()` — they're final wrappers: `unpack` calls `read` then
`validate_after_read` (which checks `value_validator` if set); `pack` substitutes
`programmatic_value(ctx)` for `data` when that kwarg was given, then calls `write`.

Commonly overridden:
- `estimate_packed_size(data, ctx) -> int` — byte length `write(data)` would produce, without
  actually writing. Needed by containers to compute offsets/lengths ahead of time.
- `new_data(patch=None)` — default/empty value used by the GUI "create new item" flow and by
  container blocks building placeholder children. Fall back to `value_validator.new_data()` when
  a validator is set (see existing blocks for the pattern).
- `schema` (property) — `{**super().schema, 'block_description': ..., ...}`. Feeds both docs and
  GUI. `DataBlock.schema` already includes `block_class_mro` (the `__`-joined class name chain,
  most specific first — see "GUI dispatch" below), `value_validator`, `is_programmatic`, and
  `serialization` (from `serializer_class()`).
- `size_doc_str` (property) — a short string used only for documentation (`"4"`, `"0..4"`,
  `"width*height"`, `"?"` if unknowable). Must tolerate being evaluated with a
  `DocumentationContext` (see below) — arithmetic/comparison ops only, no branching on real values.
- `serializer_class()` — return a `ResourceSerializer` subclass to make this block convertible from
  the GUI/CLI; return `None` (default) if it isn't independently convertible.
- For container blocks, subclass `DataBlockWithChildren` too and implement
  `get_child_block(name)`, `get_child_block_with_data(unpacked_data, name)`, and
  `offset_to_child_when_packed(data, child_name, ctx)` — these back the GUI's per-field navigation
  and the "jump to byte offset" feature.

## Context objects (`library/context.py`)

- `ReadContext` wraps the buffer and builds a tree of children mirroring the block tree as you
  read, so a lambda deep in one field can read siblings/ancestors: `ctx.data('other_field')`,
  `ctx.data('../parent_field')`, `ctx.relative_block('other_field')`. Also
  `ctx.local_buffer_pos`, `ctx.read_bytes_remaining`.
- `WriteContext` mirrors the same API against the data being written.
- `DocumentationContext` is a **fake** context fed to length/condition lambdas at doc-generation
  time, so e.g. `lambda ctx: ctx.data('width') * ctx.data('height')` degrades to the *string*
  `"width*height"` (via `DocumentationCtxData`, which overloads arithmetic/comparison operators)
  instead of crashing. **Implication:** keep length/condition/choice-index lambdas pure arithmetic
  or comparisons on `ctx.data(...)` — no `if`/branching logic that assumes a real number, no
  Python built-ins that don't work on `DocumentationCtxData`. If a lambda can't be made doc-safe,
  it's fine — `size_doc_str` swallows exceptions and shows `'?'`/`'custom_func'`.

## Lazy parts (`library/lazy.py`)

`require_file(path, lazy=None)` reads lazily by default (`lazy_loading` setting in the General config
section, env `NFS_RESOURCES_CONVERTER_GENERAL_LAZY_LOADING`); `ReadContext.lazy` carries the flag down
the context tree (`unpack_from_bytes` and bare `ReadContext`s are eager).
- Lazy parts are archive entries (`ArchiveBlock.read_entry`) and `DelegateBlock` data with
  `part_length` (NFSU bundle chunks). Each is an unloaded `LazyDict` (a real `dict`) with a `Slot`
  (source, absolute offset, length, parse function, parent context) and seeded values (alias, chunk
  id). First access to another key parses the part with
  `slot.parent_ctx.detached(buffer)` — same name, data, parent chain and offsets as the eager read,
  over a reopened buffer — and fills the same object. Whole-dict readers (iteration, `items()`,
  `dict()`, `json.dumps`, `==`, `copy`, `pickle`) load first; `deepcopy` of an unloaded part is an
  unloaded twin, equal to the original without parsing; `clear()` marks it loaded without parsing.
- Writing: a block holding a lazy part writes `slot.raw()` while it is unloaded (`unloaded_slot(data)`),
  so untouched parts round-trip byte for byte. Validation of a part runs when it loads.
- Sources: `FileSource` per file (`open_file_source` in `require_file`, `close_file_source` in
  `clear_file_cache` and before saving over a file; a changed or closed file raises
  `FileChangedError`/`SourceClosedError`; `release_file_source` when the file cache evicts a file: trees
  still holding the source keep reading, its handle closes with the last of them), `MemorySource` for a
  `BytesIO` buffer (decompressed data). `source_for_buffer` maps a context buffer to its source; a part
  over any other buffer is read eagerly.
- File cache (`library/loader.py`): `files_cache` keeps at most `file_cache_size` (General settings,
  default 16) least recently required files; `pin_file` / `unpin_file` exempt a file (the GUI pins the
  open file, `FileAPI.open_file` drops the previous one). `clear_file_cache` forgets a file and closes
  its source.
- GUI: `convert_bytes` (`serializers/misc/json_utils.py`) renders an unloaded part as its seeded values
  plus `"__lazy__": true` (`LAZY_MARKER`, `unloaded_items`), so `open_file` sends no parsed entries or
  chunks. The frontend (`utils/lazy.ts`, `MainService.ensureLoaded`) calls `load_lazy_part(id)`
  (`ResourceAPI`) when a stub is about to be shown (`EditorComponent`, archive list selection / edit /
  remove) and fills the stub object in place; `retrieve_value` returns a whole value with every part
  loaded.
- Helpers: `is_loaded`, `load_all(tree)`, `transient(node)` (parse, use, drop again), `lazy_unpack`
  (generic deferred `block.unpack`), `stats['parses']` (counter used by tests).
- Parse of a part may depend only on its own bytes, fixed file offsets and header values, never on
  where a previous part's parse stopped. `test/library/test_lazy.py` checks lazy vs eager reads of
  every archive/bundle/compressed sample.
- `EacCompressedBlock` data is `CompressedData` (dict remembering the compressed bytes and a digest of
  the uncompressed ones): written back as the original compressed bytes while the inner bytes are
  unchanged; `estimate_packed_size` is the compressed size.

## Adding a new generic block class

1. Add it to the right file under `library/read_blocks/` (new file if it's a new concern), and
   export it from `library/read_blocks/__init__.py`.
2. Implement `read`/`write`/`estimate_packed_size` and a `schema` override.
3. Add unit tests in `test/library/read_blocks/test_<name>.py`, following the existing pattern:
   `ReadContext(BytesIO(...))` → `block.unpack(ctx)`, assert the value, then assert
   `block.pack(value)` round-trips, plus a `size_doc_str` assertion.
4. Decide whether it needs new GUI support (next section) — most concrete blocks don't.

## GUI dispatch and adding a generic `*.block-ui` component

`frontend/src/app/components/editor/editor.component.ts` keeps two maps keyed by Python class name:
`DATA_BLOCK_COMPONENTS_MAP` (the generic `library/` components and the angle field, imported statically,
rendered synchronously) and `LAZY_DATA_BLOCK_COMPONENTS_MAP` (every bespoke editor as
`() => import('...').then((m) => m.X)`: its own chunk, loaded on first use with a spinner, which keeps
three.js and the chart editors out of the initial bundle and under the `initial` budget of `angular.json`).
To render a field `EditorComponent.findComponent` walks `schema.block_class_mro.split('__')`
(most-specific class first) and uses the **first** name found in either map. All editor components are
standalone (their own `imports`); `EditorModule` only exports `EditorComponent`, `SidenavResListComponent`
and `BlockActionsComponent` to the app. Consequences:

- A brand-new *concrete* block class (e.g. a new format-specific `CompoundBlock` subclass) needs
  **no** new UI as long as some ancestor (`CompoundBlock`, `ArrayBlock`, `IntegerBlock`, ...) is
  already mapped — which is true for anything built from `library/read_blocks` primitives. It just
  renders generically, driven by `schema`.
- Add a new generic component only when a whole *category* of blocks needs different generic
  interaction (not a one-off custom viewer — that belongs to `nfs-resource-formats` instead, under
  `editor/eac/` or `editor/common/`).
- To add one: create
  `frontend/src/app/components/editor/library/<name>.block-ui/{<name>.block-ui.component.ts,.html,.scss}`,
  implementing the `GuiComponent` inputs (copy `number.block-ui` or `string.block-ui` as the
  simplest templates; `compound.block-ui`/`array.block-ui`/`delegate.block-ui` show the
  container/recursive pattern), standalone with its own `imports`. Register it in `editor.component.ts`'s
  `DATA_BLOCK_COMPONENTS_MAP` keyed by the **Python class name** (a bespoke editor goes into
  `LAZY_DATA_BLOCK_COMPONENTS_MAP` as a dynamic import instead, never imported statically by eager code, or it
  lands back in the initial bundle). A component of the eager map that renders `<app-editor>` imports it as
  `forwardRef(() => EditorComponent)`: `editor.component.ts` imports it back, and without the `forwardRef` its
  compiled `dependencies` capture `EditorComponent` before the class exists (the map is built on first use for
  the same reason).

## Adding cross-cutting serializer behavior

`serializers/base.py` defines the serializer contract:
- `ResourceSerializer` (ABC): `serialize(data, path, id=None, block=None, **kwargs) -> List[str]`,
  optional `deserialize(...)`, `ui_serialization()`, `patch_settings(dict)`.
- `BaseFileSerializer`: adds `is_dir` (file vs directory output).
- `DelegateBlockSerializer`: dispatches to the serializer of whichever block a `DelegateBlock`
  actually resolved to at read time — the pattern to follow if you add another
  dispatch/composition-style block.

Only extend these classes here for behavior that should apply across many resource kinds.
Format-specific serializers (PNG export, OBJ export, WAV export, ...) belong in
`nfs-resource-formats`. `ui_serialization()`'s return shape drives the GUI "convert" panel:
`{file_type, is_directory, output_file_name_suffix, reversible, reversible_settings_patch}`
(`None` hides the block from the convert UI). The only wiring point back into the system is a
`DataBlock` subclass's own `serializer_class()` returning your class directly — `get_serializer()`
in `serializers/__init__.py` just calls that — so a new serializer module needs an import added to
`serializers/__init__.py` for its class(es) to be importable/discoverable, but no separate registry.

## Spatial edits and partial chunk export (3D track viewer)

- `library/spatial_edit.py`: a block whose positions the GUI shows in 3D declares kinds in its schema
  (`spatial_edit`: `kind`, `title`, `description`, `translate_axes` / `rotate_axes` like `'xyz'` / `'z'` / `''`,
  optional `deforms_mesh`, `pick_entities`) and mixes in `SpatialEditable`: `spatial_handles(data, kind, chunks)`,
  `spatial_handle(data, kind, id)`, `spatial_move(data, kind, id, position, rotation)` returning
  `{relative data path: new value}` without changing the data. Everything is in the serializer's export space (the
  axes / units of the files the viewer loads). `stored_value(block, value)` = the value as the file holds it (write +
  read back): use it so the handle read back after the move is what the file will contain.
  `ResourceAPI.spatial_move` takes the moves of all selected handles and applies them as one undoable bundle
  (`apply_spatial_moves`: each move on the data the earlier ones left, a value changed twice is one change) and returns
  the handles read back; the GUI snaps to them and shows the difference. A block implements single moves only.
  Example: `TriMap` (props, terrain vertices, road points).
- `serializers/common/chunk_export.py`: a track serializer may add `serialize_chunks(data, path, id, block, chunks)`
  (via `export_chunks`: per-chunk fingerprints of the data a chunk's files are made of, `chunks_state.json` in the
  output folder). The track viewer then asks for the chunks it loads only and, after any change, reloads the loaded
  chunks whose fingerprint changed; changed chunks not loaded get their files deleted. The adapter opts in with
  `chunkExport` (`track-map-adapters.ts`). Example: `TriMapSerializer`.
- GUI: `frontend/.../editor/common/spatial-edit/` (`SpatialEditController`: markers, picking, multi-selection,
  `TransformControls` gizmo with the declared axes at the selection's centre, preview / commit through a
  `SpatialEditHost`; `SelectionOrbit`: the camera turning around the selection; `app-spatial-edit-panel`: the
  viewport's edit panel). The track viewer is the host; another 3D viewer can host it the same way.

## Testing & verification

- Backend: `./.venv/bin/python -m unittest` (whole suite) or target a module, e.g.
  `./.venv/bin/python -m unittest test.library.read_blocks.test_array`.
- Frontend: `cd frontend && npm run test -- --watch=false --no-progress --browsers=ChromeHeadless`.
- CI (`.github/workflows/pull_request_build.yml`) runs exactly those two — keep both green.
- For UI changes, `python run.py --dev` + Angular dev server (see root `CLAUDE.md`/`README.md`)
  is the fastest way to eyeball a new/changed component against a real file.
