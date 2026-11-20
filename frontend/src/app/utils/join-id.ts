// A resource id is the id of a file (`pathToId` of its path: `__` escaped as `_%5F`, `:` as `---DRIVE`), and for a
// resource in the file `__` and its path in the file's data (`children/3/item/data`). That path never contains `__` and
// never starts with `_`, so the last `__` of an id separates the two, also after a file name ending in `_`
// (`TRACK___children/0` = `children/0` of `TRACK_`). Same rules as library/utils/id.py
export const ID_SEPARATOR = '__';

// [file id, path in the file's data] of a resource id, the path '' for the id of a file
export const splitId = (id: string): [string, string] => {
  const i = id.lastIndexOf(ID_SEPARATOR);
  return i < 0 ? [id, ''] : [id.substring(0, i), id.substring(i + ID_SEPARATOR.length)];
};

// whether a resource id is the id of a file (the file's data), not of a resource in it
export const isFileId = (id: string) => !id.includes(ID_SEPARATOR);

// the path of the file holding a resource
export const idToPath = (id: string) =>
  splitId(id)[0]
    .replace(/_%5F/g, ID_SEPARATOR)
    .replace(/---DRIVE/g, ':');

// the id of the file at a path
export const pathToId = (path: string) => path.replace(/\\/g, '/').replace(/:/g, '---DRIVE').replace(/__/g, '_%5F');

export const joinId = (a: string, ...b: (string | number)[]) => a + (isFileId(a) ? ID_SEPARATOR : '/') + b.join('/');

export const idSuffix = (baseId: string, id: string) => {
  if (baseId === id) {
    return '';
  }
  let next = id.substring(baseId.length);
  if (next.startsWith('/')) {
    return next.substring(1);
  } else if (next.startsWith(ID_SEPARATOR)) {
    return next.substring(ID_SEPARATOR.length);
  } else {
    throw new Error('Cannot extract valid suffix from id "' + id + '" in "' + baseId + '"');
  }
};

// the last key of a resource id's path (the file name for the id of a file)
export const lastIdPart = (id: string) => {
  const [fileId, path] = splitId(id);
  const parts = (path || fileId).split('/').filter(part => part !== '');
  return parts[parts.length - 1];
};

// [parent id, last key] of a resource id; [directory, file name] for the id of a file
export const splitLastIdPart = (id: string): [string, string] => {
  const [fileId, path] = splitId(id);
  const source = path || id;
  const i = source.lastIndexOf('/');
  const parent = i < 0 ? '' : source.substring(0, i);
  const key = source.substring(i + 1);
  if (!path) {
    return [parent, key];
  }
  return [parent ? joinId(fileId, parent) : fileId, key];
};
