import { ChangeDetectionStrategy, Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

/** Guides the GUI shows before an import, by the `import_guide` of a serializer's `ui_serialization()` */
export type ImportGuide = 'orip_obj';

/** General config key that turns each guide off */
export const IMPORT_GUIDE_CONFIG_KEYS: Record<ImportGuide, 'show_orip_import_guide'> = {
  orip_obj: 'show_orip_import_guide',
};

export interface ImportGuideDialogData {
  guide: ImportGuide;
}

export interface ImportGuideDialogResult {
  proceed: boolean;
  dontShowAgain: boolean;
}

@Component({
  selector: 'app-import-guide-dialog',
  templateUrl: './import-guide.dialog.component.html',
  styleUrls: ['./import-guide.dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class ImportGuideDialogComponent {
  dontShowAgain = false;

  constructor(
    public dialogRef: MatDialogRef<ImportGuideDialogComponent, ImportGuideDialogResult>,
    @Inject(MAT_DIALOG_DATA) public data: ImportGuideDialogData,
  ) {}

  close(proceed: boolean) {
    this.dialogRef.close({ proceed, dontShowAgain: this.dontShowAgain });
  }
}
