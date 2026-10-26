import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input } from '@angular/core';
import { MainService } from '../../../../services/main.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { CustomAction, Resource } from '../../types';
import { lastIdPart } from '../../../../utils/join-id';
import { CustomActionService } from '../../../../services/custom-action.service';
import { MatDialog } from '@angular/material/dialog';
import { firstValueFrom } from 'rxjs';
import {
  IMPORT_GUIDE_CONFIG_KEYS,
  ImportGuide,
  ImportGuideDialogComponent,
  ImportGuideDialogData,
  ImportGuideDialogResult,
} from '../import-guide.dialog/import-guide.dialog.component';

@Component({
  selector: 'app-block-actions',
  templateUrl: './block-actions.component.html',
  styleUrls: ['./block-actions.component.scss'],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class BlockActionsComponent {
  @Input()
  public resource: Resource | null = null;

  @Input()
  public hideCustomActions = false;

  @Input()
  public customActionsBlacklist: string[] = [];

  @Input()
  public size: 'default' | 'small' = 'default';

  public isSerializing = false;
  public isDeserializing = false;
  public isCustomActionRunning = false;

  get customActions(): CustomAction[] {
    return (this.resource?.schema?.custom_actions || []).filter(
      (action: CustomAction) => !this.customActionsBlacklist.includes(action.method),
    );
  }

  constructor(
    readonly mainService: MainService,
    readonly cdr: ChangeDetectorRef,
    private readonly customActionService: CustomActionService,
    private readonly snackBar: MatSnackBar,
    private readonly dialog: MatDialog,
  ) {}

  async serialize() {
    if (!this.resource) {
      return;
    }
    let resId = this.resource.id;
    let nameHint = lastIdPart(resId);
    // filter out delegate block internals
    while (nameHint == 'data') {
      resId = resId.substring(0, resId.length - nameHint.length);
      nameHint = lastIdPart(resId);
    }
    if (this.resource.schema.serialization.is_directory) {
      nameHint += '/';
    } else {
      nameHint += this.resource.schema.serialization.output_file_name_suffix || '';
    }
    let path = await this.mainService.api.saveFileDialog(nameHint);
    if (!path) {
      return;
    }
    this.isSerializing = true;
    this.cdr.markForCheck();
    try {
      const files = await this.mainService.api.serializeResource(
        this.resource.id,
        path,
        this.resource.schema.serialization.reversible_settings_patch,
      );
      if (files && files.length > 0) {
        const commonPathPart = files.reduce((commonBeginning, currentString) => {
          let j = 0;
          while (j < commonBeginning.length && j < currentString.length && commonBeginning[j] === currentString[j]) {
            j++;
          }
          return commonBeginning.substring(0, j);
        });
        const lastSlashIndex = commonPathPart.lastIndexOf('/');
        const commonFolder = lastSlashIndex !== -1 ? commonPathPart.substring(0, lastSlashIndex) : commonPathPart;
        const snackBarRef = this.snackBar.open('Files exported', 'Open location', { duration: 10000 });
        snackBarRef.onAction().subscribe(() => {
          this.mainService.api.openFileWithSystemApp(commonFolder);
        });
      }
    } finally {
      this.isSerializing = false;
      this.cdr.markForCheck();
    }
  }

  async deserialize() {
    if (!this.resource) {
      return;
    }
    const guide: ImportGuide | undefined = this.resource.schema?.serialization?.import_guide;
    if (guide && !(await this.confirmImportGuide(guide))) {
      return;
    }
    const isDirectory = !!this.resource.schema?.serialization?.is_directory;
    let paths: string[] | null = null;
    if (isDirectory) {
      const path = await this.mainService.api.selectDirectoryDialog();
      if (path) {
        paths = [path];
      }
    } else {
      paths = await this.mainService.api.openFileDialog(true);
    }
    if (!paths || paths.length === 0) {
      return;
    }
    this.isDeserializing = true;
    this.cdr.markForCheck();
    try {
      const report = await this.mainService.deserializeResource(this.resource.id, paths);
      if (report) {
        this.snackBar.open(`Imported: ${report}`, 'OK', { duration: 8000 });
      }
    } finally {
      this.isDeserializing = false;
      this.cdr.markForCheck();
    }
  }

  /** Shows the import guide unless the user turned it off; false when they cancel the import */
  private async confirmImportGuide(guide: ImportGuide): Promise<boolean> {
    const configKey = IMPORT_GUIDE_CONFIG_KEYS[guide];
    const config = await this.mainService.api.getGeneralConfig();
    if (config[configKey] === false) {
      return true;
    }
    const result = await firstValueFrom(
      this.dialog
        .open<ImportGuideDialogComponent, ImportGuideDialogData, ImportGuideDialogResult>(ImportGuideDialogComponent, {
          data: { guide },
        })
        .afterClosed(),
    );
    if (result?.dontShowAgain) {
      await this.mainService.api.patchGeneralConfig({ [configKey]: false });
    }
    return !!result?.proceed;
  }

  async runCustomAction(action: CustomAction) {
    if (!this.resource) {
      return;
    }
    this.isCustomActionRunning = true;
    this.cdr.markForCheck();
    try {
      await this.customActionService.runCustomAction(this.resource.id, action);
    } finally {
      this.isCustomActionRunning = false;
      this.cdr.markForCheck();
    }
  }
}
