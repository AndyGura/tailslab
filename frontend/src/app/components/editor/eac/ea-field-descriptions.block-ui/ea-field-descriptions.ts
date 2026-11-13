// Decoding, flattening and checking of EA's field description files (`.DES`, EaFieldDescriptions): the TypeScript
// counterpart of `des_fields`, `des_value` and `des_check` in resources/eac/field_descriptions.py

export const DES_NAME_LENGTH = 80;

// bytes as the GUI receives them: `{$bytes: number[]}` (BytesBlock), or a plain array
export type DesBytes = { $bytes: number[] } | number[] | Uint8Array;

export type DesShape = { dimensions: number; size_1: number; size_2: number };

export type DesRecord = {
  type: string;
  name: string;
  data_size: number;
  extra?: { choice_index?: number; data?: DesBody | DesShape | DesBytes | null } | null;
};

export type DesBody = { data: DesBytes; records: DesRecord[] };

// a leaf of the TailsLab block of the described data (`block_layout`)
export type DatLeaf = {
  path: string;
  offset: number;
  size: number;
  kind: string;
  element_kind?: string;
  element_size?: number;
  description?: string;
};

export type DesValue = number | number[] | null;

export type DesRow = {
  // unique: the record indices down the chains
  key: string;
  // key of the chain holding it, '' at the top
  parentKey: string;
  depth: number;
  // path of the record in the resource data, e.g. ['records', 3, 'extra', 'data', 'records', 1]
  recordPath: (string | number)[];
  // chain names and the name, `/` separated
  path: string;
  type: string;
  name: string;
  // in the described data
  offset: number;
  size: number;
  isChain: boolean;
  // a chain whose body is kept as raw bytes (nested too deep)
  rawChain: boolean;
  shape: [number, number, number] | null;
  value: DesValue;
  raw: number[];
  // leaves of the TailsLab block overlapping the field
  leaves: DatLeaf[];
  problems: string[];
};

export function desBytes(value: DesBytes | null | undefined): number[] {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (value instanceof Uint8Array) return Array.from(value);
  return Array.isArray(value.$bytes) ? value.$bytes : [];
}

const int32 = (b: number[], i: number) => b[i] | (b[i + 1] << 8) | (b[i + 2] << 16) | (b[i + 3] << 24) | 0;

// value of a field as its `.DES` type reads it (`des_value`): Fixed = 16.16, Integer = int32, Array = int32 elements,
// Char / CArray = bytes (one byte as a number), anything else (Import) = the raw bytes
export function desValue(type: string, raw: number[]): DesValue {
  if (type === 'Fixed' && raw.length === 4) return int32(raw, 0) / 0x10000;
  if (type === 'Integer' && raw.length === 4) return int32(raw, 0);
  if (type === 'Array' && raw.length % 4 === 0) {
    const res: number[] = [];
    for (let i = 0; i < raw.length; i += 4) res.push(int32(raw, i));
    return res;
  }
  if (type === 'Char' || type === 'CArray') return raw.length !== 1 ? raw : raw[0];
  return raw;
}

function isBody(v: any): v is DesBody {
  return !!v && typeof v === 'object' && Array.isArray(v.records);
}

function isShape(v: any): v is DesShape {
  return !!v && typeof v === 'object' && 'size_2' in v;
}

// the fields of a body, chains flattened into their children (`des_fields`), in data order: a chain's offset is its
// own place in the data, its records' offsets follow from there
export function desRows(
  body: DesBody,
  offset: number = 0,
  path: string = '',
  depth: number = 0,
  recordPath: (string | number)[] = [],
  parentKey: string = '',
): DesRow[] {
  const res: DesRow[] = [];
  const data = desBytes(body.data);
  let pos = 0;
  (body.records || []).forEach((record, i) => {
    const name = record.name ?? '';
    const full = path ? `${path}/${name}` : name;
    const size = record.data_size || 0;
    const extra = record.extra?.data;
    const key = parentKey ? `${parentKey}.${i}` : `${i}`;
    const ownPath = [...recordPath, 'records', i];
    const raw = data.slice(pos, pos + size);
    const row: DesRow = {
      key,
      parentKey,
      depth,
      recordPath: ownPath,
      path: full,
      type: record.type,
      name,
      offset: offset + pos,
      size,
      isChain: record.type === 'Chain',
      rawChain: false,
      shape: null,
      value: null,
      raw,
      leaves: [],
      problems: [],
    };
    res.push(row);
    if (record.type === 'Chain' && isBody(extra)) {
      res.push(...desRows(extra, offset + pos, full, depth + 1, [...ownPath, 'extra', 'data'], key));
    } else {
      if (record.type === 'Chain') row.rawChain = true;
      if (isShape(extra)) row.shape = [extra.dimensions, extra.size_1, extra.size_2];
      row.value = desValue(record.type, raw);
    }
    pos += size;
  });
  return res;
}

// does a `.DES` type fit a leaf of the TailsLab block (`_des_type_fits`)
export function desTypeFits(type: string, leaf: DatLeaf, size: number): boolean {
  const kind = leaf.element_kind ?? leaf.kind;
  const elementSize = leaf.element_size ?? leaf.size;
  switch (type) {
    case 'Fixed':
      return kind === 'fixed' && elementSize === 4;
    case 'Integer':
      return kind === 'int' && elementSize === 4;
    case 'Char':
      return elementSize === 1 && size === 1;
    case 'Array':
      return elementSize === 4 && (kind === 'fixed' || kind === 'int');
    case 'CArray':
      return elementSize === 1;
    default:
      return true;
  }
}

const hex = (v: number) => '0x' + v.toString(16);

// the leaves a field overlaps and the problems of the field against them (`des_check`): a field that is not one leaf,
// inside one leaf, or exactly a run of leaves, or whose type does not fit them. Chains are not checked
export function checkDesRow(row: Pick<DesRow, 'path' | 'type' | 'offset' | 'size'>, layout: DatLeaf[]) {
  const start = row.offset;
  const end = row.offset + row.size;
  const leaves = layout.filter(x => x.offset < end && start < x.offset + x.size);
  const problems: string[] = [];
  if (row.type === 'Chain') return { leaves, problems };
  if (!leaves.length) {
    problems.push(`${row.path}: no field at ${hex(start)}`);
    return { leaves, problems };
  }
  const first = leaves[0];
  const last = leaves[leaves.length - 1];
  const inside = leaves.length === 1 && first.offset <= start && end <= first.offset + first.size;
  const tiles = first.offset === start && last.offset + last.size === end;
  if (!inside && !tiles) {
    problems.push(`${row.path}: ${hex(start)}..${hex(end)} cuts ${leaves.map(x => x.path).join(', ')}`);
    return { leaves, problems };
  }
  for (const leaf of leaves) {
    const part = Math.min(end, leaf.offset + leaf.size) - Math.max(start, leaf.offset);
    if (!desTypeFits(row.type, leaf, leaves.length > 1 ? part : row.size)) {
      problems.push(`${row.path}: ${row.type} does not fit ${leaf.path} (${leaf.kind})`);
    }
  }
  return { leaves, problems };
}

// rows with their leaves and problems
export function checkDesRows(rows: DesRow[], layout: DatLeaf[] | null | undefined): DesRow[] {
  for (const row of rows) {
    const { leaves, problems } = checkDesRow(row, layout || []);
    row.leaves = leaves;
    row.problems = layout?.length ? problems : [];
  }
  return rows;
}

// every problem of a body against the layout, as `des_check` lists them
export function desCheck(body: DesBody, layout: DatLeaf[]): string[] {
  return checkDesRows(desRows(body), layout).flatMap(r => r.problems);
}

// ---------- display ----------

const PREVIEW_ELEMENTS = 4;

const fmtNumber = (v: number) =>
  Number.isInteger(v) ? '' + v : v.toLocaleString('en-US', { maximumFractionDigits: 6, useGrouping: false });

const printable = (bytes: number[]) => {
  // text up to the trailing zeros
  let end = bytes.length;
  while (end > 0 && bytes[end - 1] === 0) end--;
  return end > 0 && bytes.slice(0, end).every(b => b >= 0x20 && b < 0x7f);
};

const chars = (bytes: number[]) => {
  let end = bytes.length;
  while (end > 0 && bytes[end - 1] === 0) end--;
  return String.fromCharCode(...bytes.slice(0, end));
};

// short text of a value for the table and the full one for its tooltip
export function desValueText(row: DesRow): { text: string; title: string } {
  if (row.isChain) {
    return row.rawChain
      ? { text: `${row.size} bytes, body not parsed`, title: '' }
      : { text: `group of ${row.size} bytes`, title: '' };
  }
  const v = row.value;
  const t = row.type;
  if ((t === 'Fixed' || t === 'Integer') && typeof v === 'number') {
    return { text: fmtNumber(v), title: t === 'Fixed' ? `16.16: ${hex(Math.round(v * 0x10000) >>> 0)}` : '' };
  }
  if (t === 'Char' || t === 'CArray') {
    if (typeof v === 'number') {
      const c = v >= 0x20 && v < 0x7f ? ` '${String.fromCharCode(v)}'` : '';
      return { text: `${v}${c}`, title: '' };
    }
    const bytes = Array.isArray(v) ? v : [];
    if (printable(bytes)) return { text: `"${chars(bytes)}"`, title: bytes.join(', ') };
    const shown = bytes.slice(0, PREVIEW_ELEMENTS * 2).join(', ');
    return { text: `[${shown}${bytes.length > PREVIEW_ELEMENTS * 2 ? ', …' : ''}]`, title: bytes.join(', ') };
  }
  if (t === 'Array' && Array.isArray(v) && row.size % 4 === 0) {
    const shown = v.slice(0, PREVIEW_ELEMENTS).map(fmtNumber).join(', ');
    const fixed = row.leaves.length > 0 && row.leaves.every(l => (l.element_kind ?? l.kind) === 'fixed');
    let title = v.join(', ');
    if (fixed) title += '\nas 16.16: ' + v.map(x => fmtNumber(x / 0x10000)).join(', ');
    return { text: `[${shown}${v.length > PREVIEW_ELEMENTS ? `, … ${v.length}` : ''}]`, title };
  }
  return { text: `${row.raw.length} bytes`, title: row.raw.map(b => b.toString(16).padStart(2, '0')).join(' ') };
}

// rows matching a text (name, path, type, TailsLab field), with the chains holding them
export function filterDesRows(rows: DesRow[], text: string, problemsOnly: boolean = false): DesRow[] {
  const q = text.trim().toLowerCase();
  if (!q && !problemsOnly) return rows;
  const keep = new Set<string>();
  const byKey = new Map(rows.map(r => [r.key, r]));
  for (const r of rows) {
    const hay = [r.path, r.type, ...r.leaves.map(l => l.path)].join('\n').toLowerCase();
    if ((!q || hay.includes(q)) && (!problemsOnly || r.problems.length)) {
      let k: string = r.key;
      while (k && !keep.has(k)) {
        keep.add(k);
        k = byKey.get(k)?.parentKey ?? '';
      }
    }
  }
  return rows.filter(r => keep.has(r.key));
}

// a name the file can hold: up to 80 Latin-1 characters, no zero
export function desNameProblem(name: string): string | null {
  if (name.length > DES_NAME_LENGTH) return `At most ${DES_NAME_LENGTH} characters`;
  for (const c of name) {
    const code = c.charCodeAt(0);
    if (code === 0) return 'No zero character';
    if (code > 0xff) return `"${c}" is not a Latin-1 character`;
  }
  return null;
}
