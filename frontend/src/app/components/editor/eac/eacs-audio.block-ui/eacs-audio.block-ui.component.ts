import { ChangeDetectionStrategy, Component, inject, OnChanges, SimpleChanges } from '@angular/core';
import { GuiComponent } from '../../gui.component';
import { BehaviorSubject } from 'rxjs';
import { MatLabel } from '@angular/material/select';
import { MatTooltip } from '@angular/material/tooltip';
import { MatProgressSpinner } from '@angular/material/progress-spinner';
import { BlockActionsComponent } from '../../common/block-actions/block-actions.component';
import { CompoundBlockUiComponent } from '../../library/compound.block-ui/compound.block-ui.component';
import { AsyncPipe } from '@angular/common';

@Component({
  selector: 'app-eacs-audio-block-ui',
  templateUrl: './eacs-audio.block-ui.component.html',
  styleUrls: ['./eacs-audio.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.Eager,
  imports: [MatLabel, MatTooltip, MatProgressSpinner, BlockActionsComponent, CompoundBlockUiComponent, AsyncPipe],
})
export class EacsAudioBlockUiComponent extends GuiComponent implements OnChanges {
  audioUrl$: BehaviorSubject<string | null> = new BehaviorSubject<string | null>(null);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.hasOwnProperty('resourceId') || changes.hasOwnProperty('resourceData')) {
      this.audioUrl$.next(null);
      if (this.resourceId) {
        this.mainService.api.serializeResource(this.resourceId).then(paths => {
          this.audioUrl$.next(paths.find(x => x.endsWith('.wav')) || null);
        });
      }
    }
  }
}
