import { Routes } from '@angular/router';
import { ToolComponent } from './containers/tool/tool.component';
import { MainComponent } from './containers/main/main.component';

export const routes: Routes = [
  {
    path: '',
    component: MainComponent,
    children: [
      { path: '', redirectTo: 'main', pathMatch: 'full' },
      {
        path: 'main',
        component: MainComponent,
      },
    ],
  },
  {
    path: 'tool',
    component: ToolComponent,
  },
];
