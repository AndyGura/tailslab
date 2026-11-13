import { ChangeDetectionStrategy, Component, Inject, inject } from '@angular/core';
import { MainService } from '../../../../services/main.service';
import {
  MAT_DIALOG_DATA,
  MatDialogRef,
  MatDialogTitle,
  MatDialogContent,
  MatDialogActions,
} from '@angular/material/dialog';
import { BlockData, BlockSchema } from '../../types';
import { CdkScrollable } from '@angular/cdk/scrolling';
import { CompoundBlockUiComponent } from '../../library/compound.block-ui/compound.block-ui.component';
import { MatButton } from '@angular/material/button';
import { AsyncPipe } from '@angular/common';

export interface ArchiveItemEditDialogData {
  id: string;
  data: BlockData;
  schema: BlockSchema;
  name: string;
}

@Component({
  selector: 'app-archive-item-edit-dialog',
  templateUrl: './archive-item-edit.dialog.component.html',
  styleUrls: ['./archive-item-edit.dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatDialogTitle,
    CdkScrollable,
    MatDialogContent,
    CompoundBlockUiComponent,
    MatDialogActions,
    MatButton,
    AsyncPipe,
  ],
})
export class ArchiveItemEditDialogComponent {
  readonly mainService = inject(MainService);

  constructor(
    public dialogRef: MatDialogRef<ArchiveItemEditDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ArchiveItemEditDialogData,
  ) {}
}
