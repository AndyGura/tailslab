import { NgModule } from '@angular/core';
import { EditorComponent } from './editor.component';
import { SidenavResListComponent } from './common/sidenav-res-list/sidenav-res-list.component';
import { BlockActionsComponent } from './common/block-actions/block-actions.component';

// The block editors are standalone: EditorComponent creates them by block class, the bespoke ones loaded on first use
@NgModule({
  imports: [EditorComponent, SidenavResListComponent, BlockActionsComponent],
  exports: [EditorComponent, SidenavResListComponent, BlockActionsComponent],
})
export class EditorModule {}
