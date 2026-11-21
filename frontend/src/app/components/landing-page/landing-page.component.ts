import { Component, ChangeDetectionStrategy } from '@angular/core';
import { ApiDelegateService } from '../../services/api/api-delegate.service';

import { MatDialog } from '@angular/material/dialog';
import { NewFileDialogComponent } from '../new-file.dialog/new-file.dialog.component';

@Component({
  selector: 'app-landing-page',
  templateUrl: './landing-page.component.html',
  styleUrls: ['./landing-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.Eager,
  standalone: false,
})
export class LandingPageComponent {
  constructor(
    public readonly api: ApiDelegateService,
    private readonly dialog: MatDialog,
  ) {}

  async openFile() {
    const fileNames = await this.api.openFileDialog();
    if (fileNames.length > 0) {
      await this.api.openFile(fileNames[0], true);
    }
  }

  async createNewFile() {
    await NewFileDialogComponent.createNewFile(this.dialog, this.api);
  }

  async openRecentFile(path: string) {
    await this.api.openFile(path, true);
  }

  async openRecentFileLocation(path: string) {
    await this.api.openFileWithSystemApp(path.substring(0, Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'))));
  }

  getFileName(path: string): string {
    if (!path) return '';
    const lastSlash = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
    if (lastSlash === -1) return path;
    return path.substring(lastSlash + 1);
  }
}
