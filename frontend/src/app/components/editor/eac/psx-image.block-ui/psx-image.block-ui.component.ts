import { ChangeDetectionStrategy, Component } from '@angular/core';
import { SubscribableGuiComponent } from '../../gui.component';

const PSX_VRAM_ROTATED = 0x4000;
const PSX_VRAM_COORDINATE_MASK = 0x3fff;

// A PSX image of an SHPP archive (`PsxImage`): the image as the game shows it, its color model and CLUT
@Component({
  selector: 'app-psx-image-block-ui',
  templateUrl: './psx-image.block-ui.component.html',
  styleUrls: ['./psx-image.block-ui.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false,
})
export class PsxImageBlockUiComponent extends SubscribableGuiComponent {
  // the color model decides the pixel layout: shown, not edited (no conversion between the models)
  readonly fieldBlacklist = ['resource_id'];

  get stats(): { label: string; value: string }[] {
    const data = this.resourceData;
    if (!data) return [];
    const rotated = !!(data.vram_x & PSX_VRAM_ROTATED);
    const colors = data.clut?.colors?.length;
    return [
      { label: 'Color model', value: data.resource_id },
      {
        label: 'Palette (CLUT)',
        value: colors ? `${colors} colors` : data.resource_id === '16Bit PSX' ? 'none, direct colors' : 'missing',
      },
      { label: 'Stored', value: rotated ? `rotated, ${data.width}x${data.height}` : 'as shown' },
      { label: 'VRAM', value: `${data.vram_x & PSX_VRAM_COORDINATE_MASK}, ${data.vram_y & PSX_VRAM_COORDINATE_MASK}` },
    ];
  }
}
