// NFS5 car database (FEData/Data/nfs5.car, Nfs5Cars): what the front end computes from a car record (Porsche.exe)

export const NFS5_FIRST_VALUE_YEAR = 1948;
export const NFS5_LAST_VALUE_YEAR = 2000;

export const NFS5_CAR_KINDS = ['Car', 'Traffic', 'Cop'];
export const NFS5_CLASSES: { [id: number]: string } = {
  501: 'Class 3',
  502: 'Class 2',
  503: 'Class 1',
  504: 'Race class',
};
export const NFS5_ERAS: { [id: number]: string } = { 521: 'Classic era', 522: 'Golden era', 523: 'Modern era' };
export const NFS5_AVAILABILITY = [
  'Normal',
  'Not in the dealer list outside Evolution and network games',
  'Never sold new in Evolution, never used (bonus car)',
  'Never in the dealer or used lists (factory driver car)',
];
export const NFS5_RATINGS = ['Acceleration', 'Top speed', 'Braking', 'Handling', 'Overall'];

export type Nfs5Car = { [field: string]: any };

// the dealer price in a year (0x4ee220): after the first year trunc(price x value_by_year[year - first year]) / 100
// (an integer division). The table is by absolute year, so after the first year this reads another year's value
export function nfs5DealerPrice(car: Nfs5Car, year: number): number {
  const price = car['price'] || 0;
  const first = car['first_year'] || 0;
  if (!(first < year)) return price;
  const v = (car['value_by_year'] || [])[year - first] ?? 0;
  return Math.trunc(Math.trunc(price * v) / 100);
}

// the base of the current value in a year (0x4f8e50): trunc(price x value_by_year[year - 1948] x 0.01), before the
// mileage, wear, wins and parts terms
export function nfs5CarValue(car: Nfs5Car, year: number): number {
  const v = (car['value_by_year'] || [])[year - NFS5_FIRST_VALUE_YEAR] ?? 0;
  return Math.trunc((car['price'] || 0) * v * 0.01);
}

export function nfs5CarYears(car: Nfs5Car): string {
  const first = car['first_year'] || 0;
  const last = car['last_year'] || 0;
  return last && last !== first ? `${first}–${last}` : `${first}`;
}
