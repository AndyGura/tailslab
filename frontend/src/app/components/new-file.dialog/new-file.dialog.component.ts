import { Component, ChangeDetectionStrategy, ChangeDetectorRef, OnInit } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { firstValueFrom } from 'rxjs';
import { fileFormatIcon } from '../../utils/file-format-icon';
import { ApiDelegateService } from '../../services/api/api-delegate.service';
import { BaseApiDelegateService } from '../../services/api/base-api-delegate';
import { NewFileFormat, NewFileFormats } from '../../services/api/api-types';

type FormatSection = { kind: string; formats: NewFileFormat[] };

@Component({
  selector: 'app-new-file.dialog',
  templateUrl: './new-file.dialog.component.html',
  styleUrls: ['./new-file.dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class NewFileDialogComponent implements OnInit {
  public games: NewFileFormats['games'] = [];
  public counts: Record<string, number> = {};
  public gameId: string | null = null;
  public search = '';
  // the formats of the picked game, or the search results across all games, by kind
  public sections: FormatSection[] = [];
  public selectedId: string | null = null;
  private kinds: string[] = [];
  private formats: NewFileFormat[] = [];

  // picks a format, then where to save the new file, and opens it
  static async createNewFile(dialog: MatDialog, api: BaseApiDelegateService) {
    const dialogRef = dialog.open(NewFileDialogComponent, { width: '900px', maxWidth: '95vw' });
    const format: NewFileFormat | undefined = await firstValueFrom(dialogRef.afterClosed());
    if (format) {
      const path = await api.saveFileDialog(format.file_name);
      if (path) {
        await api.createNewFile(path, format.id);
      }
    }
  }

  constructor(
    public dialogRef: MatDialogRef<NewFileDialogComponent>,
    private readonly api: ApiDelegateService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  async ngOnInit() {
    const [res, config] = await Promise.all([this.api.newFileFormats(), this.api.getGeneralConfig()]);
    this.games = res.games;
    this.kinds = res.kinds;
    this.formats = res.formats;
    this.counts = {};
    for (const format of this.formats) {
      for (const game of format.games) this.counts[game] = (this.counts[game] || 0) + 1;
    }
    const lastGame = this.games.find(g => g.id === config.new_file_game);
    this.gameId = (lastGame || this.games[0])?.id ?? null;
    this.update();
  }

  get searching(): boolean {
    return !!this.search.trim();
  }

  get gameName(): string {
    return this.games.find(g => g.id === this.gameId)?.name ?? '';
  }

  get selected(): NewFileFormat | null {
    return this.formats.find(f => f.id === this.selectedId) ?? null;
  }

  pickGame(gameId: string) {
    this.search = '';
    if (gameId !== this.gameId) {
      this.gameId = gameId;
      this.api.patchGeneralConfig({ new_file_game: gameId }).then();
    }
    // the game's first format, not one of another game scrolled out of view
    this.selectedId = null;
    this.update();
  }

  setSearch(text: string) {
    this.search = text;
    this.update();
  }

  // the games of a format of several games
  gameNames(format: NewFileFormat): string {
    return this.games
      .filter(g => format.games.includes(g.id))
      .map(g => g.name)
      .join(', ');
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onCreate(): void {
    if (this.selected) this.dialogRef.close(this.selected);
  }

  private update() {
    const words = this.search
      .trim()
      .toLowerCase()
      .split(/\s+/)
      .filter(w => !!w);
    const shown = words.length
      ? this.formats.filter(f => {
          const text = [f.label, f.file_name, f.description, this.gameNames(f)].join(' ').toLowerCase();
          return words.every(w => text.includes(w));
        })
      : this.formats.filter(f => !!this.gameId && f.games.includes(this.gameId));
    this.sections = this.kinds
      .map(kind => ({ kind, formats: shown.filter(f => f.kind === kind) }))
      .filter(s => s.formats.length > 0);
    const listed = this.sections.flatMap(s => s.formats);
    if (!listed.some(f => f.id === this.selectedId)) {
      this.selectedId = listed.length ? listed[0].id : null;
    }
    this.cdr.markForCheck();
  }

  fileFormatIcon = fileFormatIcon;
}
