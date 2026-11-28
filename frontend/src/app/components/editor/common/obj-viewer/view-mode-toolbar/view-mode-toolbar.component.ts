import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy } from '@angular/core';
import { ViewMode, ViewModeController } from './view-mode.controller';

// Icon (assets/editor/icons/shading_<icon>.svg) and title of each view mode
const VIEW_MODE_BUTTONS: { [mode in ViewMode]: { icon: string; title: string } } = {
  material: { icon: 'rendered', title: 'Shading: material' },
  wireframe: { icon: 'wire', title: 'Shading: wireframe' },
  unlit: { icon: 'solid', title: 'Shading: unlit' },
  edges: { icon: 'edges', title: 'Shading: edges' },
  vertex_colors: { icon: 'vertex_colors', title: 'Shading: vertex colours (grey: meshes without them)' },
};

@Component({
  selector: 'app-view-mode-toolbar',
  templateUrl: './view-mode-toolbar.component.html',
  styleUrls: ['./view-mode-toolbar.component.scss'],
  changeDetection: ChangeDetectionStrategy.Eager,
})
export class ViewModeToolbarComponent {
  @Input() viewModeController?: ViewModeController;
  @Input() currentViewMode: ViewMode = 'material';
  @Output() viewModeChanged = new EventEmitter<ViewMode>();

  readonly buttons = VIEW_MODE_BUTTONS;

  setViewMode(mode: ViewMode): void {
    this.viewModeChanged.emit(mode);
  }

  frameAll(): void {
    this.viewModeController?.frameAll();
  }
}
