import { Component, ChangeDetectionStrategy, Inject } from '@angular/core';
import {
  MAT_DIALOG_DATA,
  MatDialogRef,
  MatDialogTitle,
  MatDialogContent,
  MatDialogActions,
} from '@angular/material/dialog';
import { BlockSchema } from '../../types';
import { fileFormatIcon } from '../../../../utils/file-format-icon';
import { CdkScrollable } from '@angular/cdk/scrolling';
import { MatSelectionList, MatListOption, MatListItemIcon, MatListItemTitle } from '@angular/material/list';
import { MatIcon } from '@angular/material/icon';
import { MatButton } from '@angular/material/button';

@Component({
  selector: 'app-archive-delegate-item-type.dialog',
  templateUrl: './archive-delegate-item-type.dialog.component.html',
  styleUrls: ['./archive-delegate-item-type.dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatDialogTitle,
    CdkScrollable,
    MatDialogContent,
    MatSelectionList,
    MatListOption,
    MatIcon,
    MatListItemIcon,
    MatListItemTitle,
    MatDialogActions,
    MatButton,
  ],
})
export class ArchiveDelegateItemTypeDialogComponent {
  public selectedIndex = 0;

  constructor(
    public dialogRef: MatDialogRef<ArchiveDelegateItemTypeDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { schemas: BlockSchema[] },
  ) {}

  onCancel(): void {
    this.dialogRef.close();
  }

  onSelect(): void {
    this.dialogRef.close(this.selectedIndex);
  }

  fileFormatIcon = fileFormatIcon;

  getSchemaName(schema: BlockSchema): string {
    return schema.block_class_mro.split('__')[0];
  }
}
