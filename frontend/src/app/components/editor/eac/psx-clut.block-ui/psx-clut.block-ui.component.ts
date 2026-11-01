import { ChangeDetectionStrategy, Component, ElementRef, ViewChild } from '@angular/core';
import { SubscribableGuiComponent } from '../../gui.component';
import { hexToPsxColor, psxColorToHex, PSX_STP_BIT } from '../../../../utils/psx-color';

// The CLUT of a PSX image (`PsxClut`): its PSX 16-bit colors as swatches, a click changes one
@Component({
  selector: 'app-psx-clut-block-ui',
  templateUrl: './psx-clut.block-ui.component.html',
  styleUrls: ['./psx-clut.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class PsxClutBlockUiComponent extends SubscribableGuiComponent {
  @ViewChild('colorInput') colorInput!: ElementRef<HTMLInputElement>;

  readonly fieldBlacklist = ['colors'];
  private selectedIndex: number | null = null;

  get colors(): number[] {
    return this.resourceData?.colors || [];
  }

  swatch(color: number): string | null {
    return color === 0 ? null : psxColorToHex(color);
  }

  tooltip(index: number, color: number): string {
    const raw = '0x' + color.toString(16).padStart(4, '0');
    if (color === 0) return `${index}: ${raw}, transparent`;
    return `${index}: ${raw}, ${psxColorToHex(color)}${color & PSX_STP_BIT ? ', STP bit set' : ''}`;
  }

  onColorClicked(element: HTMLElement, index: number) {
    if (this.disabled) return;
    this.selectedIndex = index;
    const input = this.colorInput.nativeElement;
    input.value = psxColorToHex(this.colors[index]);
    const rect = element.getBoundingClientRect();
    input.style.left = `${rect.left}px`;
    input.style.top = `${rect.top}px`;
    input.click();
  }

  onColorChange(hex: string) {
    const index = this.selectedIndex;
    if (index === null) return;
    const value = hexToPsxColor(hex, this.colors[index]);
    if (value !== null && value !== this.colors[index]) {
      this.onValueSet(value, 'colors', index);
    }
  }
}
