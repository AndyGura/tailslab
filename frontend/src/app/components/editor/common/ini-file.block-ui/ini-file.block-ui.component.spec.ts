import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { MainService } from '../../../../services/main.service';
import { ChangesService } from '../../../../services/changes.service';
import { IniFileBlockUiComponent, iniKeyRows, parseIniInput } from './ini-file.block-ui.component';

const float = (unit?: string, def?: number) => ({
  block_class_mro: 'IniFloat___IniValue__DecimalBlock__DataBlock',
  ini_kind: 'float',
  ini_unit: unit,
  ini_default: def,
});
const int = () => ({ block_class_mro: 'IniInt___IniValue__IntegerBlock__DataBlock', ini_kind: 'int' });
const text = () => ({ block_class_mro: 'IniString___IniValue__UTF8Block__DataBlock', ini_kind: 'string' });
const otherKeys = { name: 'other_keys', schema: { block_class_mro: 'ArrayBlock__DataBlock' }, description: '' };

// a small typed INI file schema as resources/eac/ini.py makes it
const schema = () => ({
  block_class_mro: 'Nfs6BoundsIni__IniFile__DeclarativeCompoundBlock__CompoundBlock__DataBlock',
  block_description: 'Test file',
  fields: [
    {
      name: 'basic',
      description: 'Basics',
      schema: {
        block_class_mro: 'Nfs6CarIniBasic__IniSection___IniStructure__CompoundBlock__DataBlock',
        ini_section: 'basic',
        fields: [
          { name: 'Mass', description: 'Car mass', schema: float('kg') },
          { name: 'Damp', description: 'Damping', schema: float(undefined, 1) },
          { name: 'Shape', description: 'Not read by NFSHP2.exe (no such string).', schema: int() },
          {
            name: 'driveWheels',
            description: 'Driven wheels',
            schema: {
              block_class_mro: 'IniArray__ArrayBlock__DataBlock',
              ini_key: 'driveWheels_%d',
              first_index: 0,
              length: 4,
              child_schema: int(),
            },
          },
          otherKeys,
        ],
      },
    },
    {
      name: 'skins',
      description: 'Skins',
      schema: {
        block_class_mro: 'IniSectionGroup___IniStructure__ArrayBlock__DataBlock',
        ini_section_pattern: 'skin\\d+',
        child_schema: {
          block_class_mro: 'IniGroupSection__IniSection__CompoundBlock__DataBlock',
          fields: [
            { name: 'section', description: '', schema: text() },
            { name: 'specular_red', description: 'Red', schema: int() },
            otherKeys,
          ],
        },
      },
    },
    { name: 'other_sections', description: '', schema: { block_class_mro: 'ArrayBlock__DataBlock' } },
    { name: 'source_text', description: '', usage: 'io', schema: { block_class_mro: 'UTF8Block__DataBlock' } },
  ],
});

const data = () => ({
  basic: { Mass: 1439, Damp: null, Shape: 6, driveWheels: [1, 1, null, null], other_keys: [{ key: 'X', value: '1' }] },
  skins: [{ section: 'skin00', specular_red: 10, other_keys: [] }],
  other_sections: [],
});

describe('IniFileBlockUiComponent helpers', () => {
  it('reads the rows of a section schema', () => {
    const rows = iniKeyRows(schema().fields[0].schema as any);
    expect(rows.map(r => r.field)).toEqual(['Mass', 'Damp', 'Shape', 'driveWheels']);
    expect(rows[0]).toEqual(jasmine.objectContaining({ kind: 'float', unit: 'kg', notRead: false, itemKeys: null }));
    expect(rows[1].default).toBe(1);
    expect(rows[2].notRead).toBeTrue();
    expect(rows[3].itemKeys).toEqual(['driveWheels_0', 'driveWheels_1', 'driveWheels_2', 'driveWheels_3']);
    expect(rows[3].kind).toBe('int');
  });

  it('parses inputs as the key values', () => {
    expect(parseIniInput('', 'float')).toBeNull();
    expect(parseIniInput('2.6', 'int')).toBe(3);
    expect(parseIniInput('0.5', 'float')).toBe(0.5);
    expect(parseIniInput('abc', 'float')).toBeUndefined();
    expect(parseIniInput(' x ', 'string')).toBe(' x ');
  });
});

describe('IniFileBlockUiComponent', () => {
  let fixture: ComponentFixture<IniFileBlockUiComponent>;
  let component: IniFileBlockUiComponent;
  let appendChanges: jasmine.Spy;

  beforeEach(async () => {
    appendChanges = jasmine.createSpy('appendChanges').and.returnValue(Promise.resolve());
    await TestBed.configureTestingModule({
      imports: [IniFileBlockUiComponent],
      providers: [
        { provide: MainService, useValue: { focusedResourceId$: new BehaviorSubject(null) } },
        {
          provide: ChangesService,
          useValue: {
            change$: new Subject<string>(),
            appendChanges,
            subscribeComponent: () => {},
            unsubscribeComponent: () => {},
          },
        },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
    fixture = TestBed.createComponent(IniFileBlockUiComponent);
    component = fixture.componentInstance;
    component.resourceId = 'bounds.ini';
    component.resourceSchema = schema();
    component.resourceData = data();
    fixture.detectChanges();
  });

  it('lists sections and groups', () => {
    expect(component.sections.map(s => [s.field, s.group])).toEqual([
      ['basic', false],
      ['skins', true],
    ]);
    expect(component.keysInFile(data().basic)).toBe(5);
    component.showNotRead = false;
    expect(component.visibleRows(component.sections[0], data().basic).map(r => r.field)).not.toContain('Shape');
    component.onlyInFile = true;
    expect(component.visibleRows(component.sections[0], data().basic).map(r => r.field)).toEqual([
      'Mass',
      'driveWheels',
    ]);
  });

  it('sets values, removes keys and adds group sections', () => {
    component.onKeyInput(['basic', 'Mass'], '1500.5', 'float');
    expect(appendChanges.calls.mostRecent().args[0]).toEqual(
      jasmine.objectContaining({ op: 'set', id: 'bounds.ini__basic/Mass', newValue: 1500.5 }),
    );
    component.removeKey(['basic', 'Mass']);
    expect(appendChanges.calls.mostRecent().args[0].newValue).toBeNull();
    component.addGroupItem(component.sections[1]);
    const insert = appendChanges.calls.mostRecent().args[0];
    expect(insert.op).toBe('array_insert');
    expect(insert.id).toBe('bounds.ini__skins');
    expect(insert.value.section).toBe('skin01');
  });

  it('keeps only the whitelisted sections', () => {
    component.sectionWhitelist = ['skins'];
    expect(component.sections.map(s => s.field)).toEqual(['skins']);
  });
});
