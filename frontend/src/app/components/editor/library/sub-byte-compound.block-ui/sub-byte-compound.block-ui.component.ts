import { ChangeDetectionStrategy, Component } from '@angular/core';
import { SubscribableGuiComponent } from '../../gui.component';
import { MatLabel, MatFormField, MatSelect, MatOption } from '@angular/material/select';
import { MatTooltip } from '@angular/material/tooltip';
import { MatCheckbox } from '@angular/material/checkbox';
import { MatInput } from '@angular/material/input';

@Component({
  selector: 'app-sub-byte-compound-block-ui',
  templateUrl: './sub-byte-compound.block-ui.component.html',
  styleUrls: [],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatLabel, MatTooltip, MatCheckbox, MatFormField, MatInput, MatSelect, MatOption],
})
export class SubByteCompoundBlockUiComponent extends SubscribableGuiComponent<{
  [key: string]: number | string | boolean;
}> {}
