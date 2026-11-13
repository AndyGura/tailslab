import { ChangeDetectionStrategy, Component, EventEmitter, Output } from '@angular/core';
import { PrimitiveGuiComponent } from '../../gui.component';
import { MatFormField, MatLabel, MatSelect, MatOption } from '@angular/material/select';
import { MatTooltip } from '@angular/material/tooltip';
import { MatInput } from '@angular/material/input';

@Component({
  selector: 'app-enum-block-ui',
  templateUrl: './enum.block-ui.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatFormField, MatTooltip, MatLabel, MatSelect, MatOption, MatInput],
})
export class EnumBlockUiComponent extends PrimitiveGuiComponent<string | number> {
  isKnownEnumValue(value: string | number): boolean {
    return !!this.resourceSchema?.enum_names.find(([_, v]: string[]) => v == value);
  }
}
