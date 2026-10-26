import { of } from 'rxjs';
import { BlockActionsComponent } from './block-actions.component';
import { Resource } from '../../types';

describe('BlockActionsComponent import guide', () => {
  function setUp(showGuide: boolean, dialogResult: any, importGuide: string | null = 'orip_obj') {
    const api = {
      getGeneralConfig: jasmine.createSpy('getGeneralConfig').and.resolveTo({ show_orip_import_guide: showGuide }),
      patchGeneralConfig: jasmine.createSpy('patchGeneralConfig').and.resolveTo({}),
      selectDirectoryDialog: jasmine.createSpy('selectDirectoryDialog').and.resolveTo('/models/orip0'),
    };
    const mainService = { api, deserializeResource: jasmine.createSpy('deserializeResource').and.resolveTo(null) };
    const dialog = { open: jasmine.createSpy('open').and.returnValue({ afterClosed: () => of(dialogResult) }) };
    const component = new BlockActionsComponent(
      mainService as any,
      { markForCheck: () => {} } as any,
      {} as any,
      { open: () => {} } as any,
      dialog as any,
    );
    component.resource = {
      id: 'car.CFM__children/0/item/data',
      schema: {
        block_class_mro: 'OripGeometry',
        serialization: { is_directory: true, reversible: true, import_guide: importGuide },
      },
    } as unknown as Resource;
    return { component, api, mainService, dialog };
  }

  it('shows the guide, then imports the picked folder', async () => {
    const { component, api, mainService, dialog } = setUp(true, { proceed: true, dontShowAgain: false });
    await component.deserialize();
    expect(dialog.open).toHaveBeenCalled();
    expect(api.patchGeneralConfig).not.toHaveBeenCalled();
    expect(mainService.deserializeResource).toHaveBeenCalledWith('car.CFM__children/0/item/data', ['/models/orip0']);
  });

  it('stops the import when the guide is cancelled', async () => {
    const { component, api, mainService } = setUp(true, { proceed: false, dontShowAgain: false });
    await component.deserialize();
    expect(api.selectDirectoryDialog).not.toHaveBeenCalled();
    expect(mainService.deserializeResource).not.toHaveBeenCalled();
  });

  it('turns the guide off with "Don\'t show this again"', async () => {
    const { component, api } = setUp(true, { proceed: true, dontShowAgain: true });
    await component.deserialize();
    expect(api.patchGeneralConfig).toHaveBeenCalledWith({ show_orip_import_guide: false });
    expect(api.selectDirectoryDialog).toHaveBeenCalled();
  });

  it('skips the guide once it is turned off, and for imports without one', async () => {
    for (const [showGuide, importGuide] of [
      [false, 'orip_obj'],
      [true, null],
    ] as [boolean, string | null][]) {
      const { component, api, dialog } = setUp(showGuide, undefined, importGuide);
      await component.deserialize();
      expect(dialog.open).not.toHaveBeenCalled();
      expect(api.selectDirectoryDialog).toHaveBeenCalled();
    }
  });
});
