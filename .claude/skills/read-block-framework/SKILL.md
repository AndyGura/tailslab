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
  `serialization` (from `serializer_class()`). A fixed description is a class attribute
  `block_description = '...'` instead: `DataBlock.__init_subclass__` gives a class defining it a
  `schema` that sets it over the one of the class (or its base classes), as such an override would;
  subclasses inherit it, a subclass's own `schema` override still wins. Framework classes in
  `library/read_blocks` don't define it (their descriptions depend on the instance).
  `CompoundBlock.inline_description` (the constructor argument, or a class attribute of a subclass)
  renders a compound block inline in the docs with that description.
- `size_doc_str` (property) — a short string used only for documentation (`"4"`, `"0..4"`,
  `"width*height"`, `"?"` if unknowable). Must tolerate being evaluated with a
  `DocumentationContext` (see below) — arithmetic/comparison ops only, no branching on real values.
- `serializer` (class attribute) — the name of a `ResourceSerializer` subclass in the `serializers`
  package (`serializer = 'ImageSerializer'`) to make this block convertible from the GUI/CLI; `None`
  (default) if it isn't independently convertible. `DataBlock.serializer_class()` resolves the name
  (`BytesBlock`: `PlainBinarySerializer`, `DelegateBlock`: `DelegateBlockSerializer`); override
  `serializer_class()` only for a serializer that depends on the block's settings.
- `fixed_size` (cached property) — the packed size of every value (what `estimate_packed_size`
  returns for any data), `None` (default) when it depends on the data. `IntegerBlock` / `DecimalBlock`:
  their length; `CompoundBlock`: the sum of its io fields; `ArrayBlock` with a positive int length:
  length × child (0 marks arrays filled by custom code). Compound and array estimates return it
  without walking the data; `ArrayBlock.estimate_packed_size` is `len(data) × child.fixed_size`.
- Struct records — `struct_format` (cached: byte order `'<'` / `'>'` or `''`, and the `struct`
  format characters), `struct_raw` (the value is the unpacked value as it is), `from_struct(values,
  index)` / `to_struct(data, values)`, `struct_record` (the compiled `StructRecord`,
  `library/read_blocks/struct_record.py`). Integer / float leaves, compounds of them (nested ones
  too) and arrays of a positive int length of them have one when no block in them has a value
  validator or programmatic value and the byte orders agree. `CompoundBlock.read` / `write` and the
  items of `ArrayBlock.read` / `write` (`struct.iter_unpack`, one `struct.pack` per item) then go
  through it, without a context per field; on any exception (end of buffer, a value out of range,
  a wrong array length) they fall back to the field by field path, which raises the error with its
  context. Caches are left out of copies (`DataBlock.__getstate__`): `big_endian_copy` changes the
  byte order of a copy.
- Number leaves storing another value as an integer (fixed point, enum, angle, time, bit fields:
  `SubByteCompoundBlock`) override `IntegerBlock.from_raw(raw)` / `to_raw(value)`, never `read` /
  `write`: a leaf class overriding `read` / `write` has no struct format, and neither has a record
  holding it.
- `CompoundBlock.field_by_field_io` — the class's `read` / `write` / `estimate_packed_size` are
  `CompoundBlock`'s; only then do `fixed_size` and `struct_format` come from the fields. A subclass
  whose override changes nothing (`Point3D` without `normalized`) overrides it
  (`ArrayBlock.item_by_item_io` likewise). `CompoundBlock.io_field_blocks` = the `(name, block)` of
  the fields with io usage (`is_io_usage`), computed in `__init__`: use it instead of filtering
  `field_blocks` by `usage`.
- `DeclarativeCompoundBlock.declared_fields()` (classmethod) builds the field list from the `Fields` class (the
  fields of its own body: `CompoundBlockFields.fields`, cached per class); a base class adding fields to every
  subclass overrides it (`ChunkBlock` in `resources/blackbox/chunks.py`: the chunk header).
- `LengthPrefixed` (`library/read_blocks/basic.py`): mixin of a block stored after a length field
  (`LengthPrefixedArrayBlock`, `LengthPrefixedUtf8Block`): reads the field and passes it as `resolved_length`, writes
  `prefix_value(data, packed_size)` before the value.
- `ArrayBlock(child, byte_length=...)` (a block parameter): the items take that many bytes. A child with a
  `fixed_size` is read as a counted array of as many as fit (struct fast path; the rest is left to the next field),
  other children one by one until they took them (`DataIntegrityException` past them); documented by the
  parameter's doc text (size) and, for children with a numeric `size_doc_str`, `<doc> / <item size>` items.
  `stop_before(ctx)` / `stop_after(item)` (functions or `(function, doc)`): items one by one up to
  `ReadContext.read_end`, ended before an item (`ctx.peek(n)`) or after one; the doc text is the length,
  the size is length x item size.
- `REMAINING` (`library/read_blocks/basic.py`): a length parameter taking the bytes the block is read with
  (`read_bytes_amount`, `read_length(param, ctx, read_bytes_amount)`), else `ctx.read_bytes_remaining` of the
  parent: `BytesBlock` (the raw choice of archive items), `UTF8Block`, `ArrayBlock(byte_length=REMAINING)`.
- Block parameters (`library/read_blocks/references.py`): the `length` of `BytesBlock` / `ArrayBlock`
  / `SubByteArrayBlock` / `UTF8Block` and `Padding(to=...)` are a number, a field path (`'num_items'`,
  `'../count'`: `ctx.data` of it, documented as the path), a `lambda ctx: ...`, or one of these with
  its doc text `(param, 'doc')`. A new block taking such a parameter resolves it with
  `param_value(param, ctx)`, documents it with `param_doc(param)` and tells a fixed one with
  `is_static_param(param)`, instead of unwrapping it itself.
- Field references (same module), programmatic values computed from other fields of the compound:
  `CountOf(path)` (`len(ctx.data(path))`), and the `LayoutReference`s `OffsetOf(name)`,
  `SizeOf(*names)`, `OwnSize()`, `ItemOffsetsOf(name)` (an offset table: the offset of each item of an
  array field; `CompoundBlock.write` packs that array item by item, `ArrayBlock.write_items`); `+ n` /
  `- n` adds a constant. `CompoundBlock.write` writes a
  fixed-size field holding a `LayoutReference` as zeros, writes the other fields, then fills it from
  where they were written (`back_patched_fields`, `from_spans`): no `estimate_packed_size` pass, so
  nested size fields cost nothing extra. `ctx.result` holds those zeros until the end of the
  compound's write. Called like any programmatic value (another block's `write` packing the field,
  a class overriding `estimate_packed_size` for `OwnSize` or `offset_to_child_when_packed` for
  `OffsetOf`, a reference to a non-io field), a reference estimates instead.
- For container blocks, subclass `DataBlockWithChildren` too and implement
  `get_child_block(name)`, `get_child_block_with_data(unpacked_data, name)`, and
  `offset_to_child_when_packed(data, child_name, ctx)` — these back the GUI's per-field navigation
  and the "jump to byte offset" feature.

## Context objects (`library/context.py`)

- `ReadContext` wraps the buffer and builds a tree of children mirroring the block tree as you
  read, so a lambda deep in one field can read siblings/ancestors: `ctx.data('other_field')`,
  `ctx.data('../parent_field')`, `ctx.relative_block('other_field')`. Also
  `ctx.local_buffer_pos`, `ctx.read_bytes_remaining` (None when the block was read without an amount: array
  items), `ctx.read_end` (absolute end offset of the closest context read with an amount, else the buffer end)
  and `ctx.peek(n)` (bytes ahead up to `read_end`, position kept).
- `WriteContext` mirrors the same API against the data being written.
- `DocumentationContext` is a **fake** context fed to length/condition lambdas at doc-generation
  time, so e.g. `lambda ctx: ctx.data('width') * ctx.data('height')` degrades to the *string*
  `"width*height"` (via `DocumentationCtxData`, whose arithmetic / bit / comparison operators come from the
  `_DOC_OPERATORS` table: symbol and the characters that put each operand in brackets) instead of crashing. **Implication:** keep length/condition/choice-index lambdas pure arithmetic
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
  optional `deserialize(...)`, `ui` (class attribute, a `UiSerialization`), `patch_settings(dict)`.
- `BaseFileSerializer`: adds `is_dir` (file vs directory output) and `output_path(path, id)` (a file output in a
  folder path named after the resource).
- Shared helpers there: `current_resource(id, block)` (the data an import replaces), `export_child` /
  `write_skipped` / `unique_name` (archive items and `skipped.txt`).
- `DelegateBlockSerializer`: dispatches to the serializer of whichever block a `DelegateBlock`
  actually resolved to at read time — the pattern to follow if you add another
  dispatch/composition-style block.

Only extend these classes here for behavior that should apply across many resource kinds.
Format-specific serializers (PNG export, OBJ export, WAV export, ...) belong in
`nfs-resource-formats`. `ui = UiSerialization(file_type, is_directory, suffix, reversible, settings_patch,
import_guide)` drives the GUI "convert" panel (common ones: `JSON_UI`, `REVERSIBLE_JSON_UI`, `PNG_UI`,
`REVERSIBLE_PNG_UI`, `DIRECTORY_UI`; a variant `dataclasses.replace(Base.ui, ...)`); `ui_serialization()` sends it
as `{file_type, is_directory, output_file_name_suffix, reversible, reversible_settings_patch[, import_guide]}` in
`schema['serialization']` (`ui = None` hides the block from the convert UI). The only wiring point back into the system is a
`DataBlock` subclass's `serializer` attribute naming your class — `get_serializer()` in
`serializers/__init__.py` calls `serializer_class()`, which looks the name up in the `serializers`
package — so a new serializer class needs an import in `serializers/__init__.py`, but no separate
registry.

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
