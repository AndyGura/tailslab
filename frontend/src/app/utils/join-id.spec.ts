import { idToPath, isFileId, joinId, lastIdPart, pathToId, splitId, splitLastIdPart } from './join-id';

describe('join-id', () => {
  it('maps resource ids and paths like the backend', () => {
    expect(idToPath('C---DRIVE/Games/my_%5Fdir/nfs5.car__cars/3')).toBe('C:/Games/my__dir/nfs5.car');
    expect(pathToId('C:\\Games\\my__dir\\nfs5.prt')).toBe('C---DRIVE/Games/my_%5Fdir/nfs5.prt');
  });

  it('splits an id at its last separator', () => {
    expect(splitId('/g/TR1.FSH')).toEqual(['/g/TR1.FSH', '']);
    expect(splitId('/g/TR1.FSH__children/3/item/data')).toEqual(['/g/TR1.FSH', 'children/3/item/data']);
    expect(isFileId('/g/TR1.FSH')).toBeTrue();
    expect(isFileId('/g/TR1.FSH__children')).toBeFalse();
  });

  it('keeps a file name ending in an underscore', () => {
    const itemId = joinId(pathToId('/g/TRACK_'), 'children', 0);
    expect(itemId).toBe('/g/TRACK___children/0');
    expect(splitId(itemId)).toEqual(['/g/TRACK_', 'children/0']);
    expect(idToPath(itemId)).toBe('/g/TRACK_');
    expect(lastIdPart('/g/TRACK___children')).toBe('children');
    expect(splitLastIdPart('/g/TRACK___children')).toEqual(['/g/TRACK_', 'children']);
  });

  it('splits off the last key', () => {
    expect(splitLastIdPart('/g/F__children/3/item')).toEqual(['/g/F__children/3', 'item']);
    expect(splitLastIdPart('/g/F__children')).toEqual(['/g/F', 'children']);
    expect(splitLastIdPart('/g/F')).toEqual(['/g', 'F']);
    expect(lastIdPart('/g/F__children/3/item/')).toBe('item');
    expect(lastIdPart('/g/F__')).toBe('F');
  });
});
