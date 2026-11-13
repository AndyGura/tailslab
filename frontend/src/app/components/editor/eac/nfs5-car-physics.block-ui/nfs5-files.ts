// The NFS5 car data files reference each other: the car database (FEData/Data/nfs5.car) names each car's .sim
// (GameData/Simulation/CarData) and .ais (GameData/Simulation/AICarData) and lists nfs5.prt part ids. The editors read
// the files next to the opened one through the backend (find_files: case-insensitive, `..` allowed; retrieve_value)

// the file path of a resource id (library/loader.py id_to_path)
export function resourcePath(id: string): string {
  return id
    .split('__')[0]
    .replace(/_%5F/g, '__')
    .replace(/---DRIVE/g, ':');
}

// the resource id of a file path (library/loader.py path_to_name)
export function pathToResourceId(path: string): string {
  return path.replace(/\\/g, '/').replace(/:/g, '---DRIVE').replace(/__/g, '_%5F');
}

export function dirOf(path: string): string {
  const p = path.replace(/\\/g, '/');
  const i = p.lastIndexOf('/');
  return i < 0 ? '' : p.substring(0, i);
}

export function fileNameOf(path: string): string {
  const p = path.replace(/\\/g, '/');
  return p.substring(p.lastIndexOf('/') + 1);
}

// where the files lie relative to FEData/Data (the folder of nfs5.car / nfs5.prt / nfs5.fac)
export const NFS5_FEDATA_TO_SIM = '../../GameData/Simulation/CarData';
export const NFS5_FEDATA_TO_AIS = '../../GameData/Simulation/AICarData';
export const NFS5_SIM_TO_FEDATA = '../../../FEData/Data';

export type Nfs5FileApi = {
  findFiles(patterns: string[]): Promise<string[]>;
  retrieveValue<T = any>(id: string): Promise<T>;
};

// the first file found for the patterns (relative to `dir`), or null
export async function findNfs5File(api: Nfs5FileApi, dir: string, patterns: string[]): Promise<string | null> {
  try {
    const found = await api.findFiles(patterns.map(p => (dir ? dir + '/' : '') + p));
    return found.length ? found[0] : null;
  } catch (err) {
    console.warn('Could not look up', patterns, err);
    return null;
  }
}

// a file's parsed data, or null
export async function loadNfs5File<T = any>(api: Nfs5FileApi, path: string): Promise<T | null> {
  try {
    return await api.retrieveValue<T>(pathToResourceId(path));
  } catch (err) {
    console.warn('Could not read', path, err);
    return null;
  }
}

// the record to show first when an NFS5 editor opens another file at one of its records (a link); read once
export const nfs5PendingSelection: { carId?: number; partId?: number } = {};

export function takePendingSelection(key: 'carId' | 'partId'): number | undefined {
  const v = nfs5PendingSelection[key];
  delete nfs5PendingSelection[key];
  return v;
}

export type Nfs5PartInfo = { id: number; index: number; label: string; type: number; family: string; part: any };
export type Nfs5CarInfo = { id: number; index: number; name: string; kind: number };

// the parts of nfs5.prt next to `dir` by id, or null
export async function loadNfs5Parts(
  api: Nfs5FileApi,
  dir: string,
): Promise<{ path: string; byId: Map<number, Nfs5PartInfo> } | null> {
  const path = await findNfs5File(api, dir, ['nfs5.prt']);
  if (!path) return null;
  const data = await loadNfs5File<any>(api, path);
  if (!data?.['parts']) return null;
  const byId = new Map<number, Nfs5PartInfo>();
  (data['parts'] as any[]).forEach((p, index) => {
    if (!byId.has(p['id'])) {
      byId.set(p['id'], { id: p['id'], index, label: nfs5PartName(p), type: p['type'], family: p['family'], part: p });
    }
  });
  return { path, byId };
}

// the cars of nfs5.car next to `dir` by id, or null
export async function loadNfs5Cars(
  api: Nfs5FileApi,
  dir: string,
): Promise<{ path: string; byId: Map<number, Nfs5CarInfo> } | null> {
  const path = await findNfs5File(api, dir, ['nfs5.car']);
  if (!path) return null;
  const data = await loadNfs5File<any>(api, path);
  if (!data?.['cars']) return null;
  const byId = new Map<number, Nfs5CarInfo>();
  (data['cars'] as any[]).forEach((c, index) => {
    if (!byId.has(c['id'])) byId.set(c['id'], { id: c['id'], index, name: c['display_name'], kind: c['kind'] });
  });
  return { path, byId };
}

const PART_TYPE_NAMES: { [t: number]: string } = {
  1: 'Engine',
  2: 'Brakes',
  3: 'Gearbox',
  4: 'Springs',
  5: 'Shocks',
  6: 'Aero',
  7: 'Body panel',
  8: 'Sway bars',
  9: 'Tyres',
  10: 'Body',
};

// a part as the editors list it: "<family> <name>" (the menus show the FEStrings name, not in the file)
export function nfs5PartName(p: any): string {
  const name = p['name'] || PART_TYPE_NAMES[p['type']] || `type ${p['type']}`;
  return `${p['family'] ? p['family'] + ' ' : ''}${name}`;
}

// 0xAARRGGBB <-> CSS
export function argbToCss(v: number): string {
  return '#' + ((v >>> 0) & 0xffffff).toString(16).padStart(6, '0');
}

export function cssToArgb(css: string, old: number): number {
  const rgb = parseInt(css.replace('#', ''), 16) & 0xffffff;
  return ((((old >>> 24) & 0xff) << 24) | rgb) >>> 0;
}
