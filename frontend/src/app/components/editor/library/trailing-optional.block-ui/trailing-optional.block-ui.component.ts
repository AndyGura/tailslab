import { ChangeDetectionStrategy, Component, forwardRef } from '@angular/core';
import { SubscribableGuiComponent } from '../../gui.component';
import { BlockData } from '../../types';
import { MatCheckbox } from '@angular/material/checkbox';
import { MatTooltip } from '@angular/material/tooltip';
import { EditorComponent } from '../../editor.component';

// A TrailingOptionalBlock's data is the child's own value when present, or `null` when absent -
// there is no wrapper object to look inside, unlike e.g. DelegateBlock.
// forwardRef: EditorComponent imports this component back
@Component({
  selector: 'app-trailing-optional-block-ui',
  templateUrl: './trailing-optional.block-ui.component.html',
  styleUrls: ['./trailing-optional.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatCheckbox, MatTooltip, forwardRef(() => EditorComponent)],
})
export class TrailingOptionalBlockUiComponent extends SubscribableGuiComponent<BlockData | null> {
  get isPresent(): boolean {
    return this.resourceData !== null && this.resourceData !== undefined;
  }

  async setPresent(present: boolean): Promise<void> {
    if (!this.resourceId || present === this.isPresent) return;
    const oldValue = this.resourceData ?? null;
    const newValue = present ? await this.mainService.getTrailingOptionalFieldData(this.resourceId) : null;
    this.emitNewChange({ op: 'set', oldValue, newValue });
  }
}
