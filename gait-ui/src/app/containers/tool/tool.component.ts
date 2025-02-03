import { CdkTextareaAutosize } from '@angular/cdk/text-field';
import { CommonModule } from '@angular/common';
import {
  afterNextRender,
  Component,
  computed,
  inject,
  Injector,
  signal,
  Signal,
  ViewChild,
  WritableSignal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { CodemirrorModule } from '@ctrl/ngx-codemirror';
import {
  catchError,
  finalize,
  map,
  Observable,
  of,
  Subject,
  switchMap,
  take,
  takeUntil,
  tap,
} from 'rxjs';
import { GraphQlService } from '../../lib/service/graph-ql.service';
import { QueryManagerService } from '../../lib/service/query-manager.service';
import { IApiModel } from '../../lib/model/i-api-model';

@Component({
  selector: 'app-tool',
  imports: [
    CommonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    CodemirrorModule,
    FormsModule,
  ],
  templateUrl: './tool.component.html',
  styleUrl: './tool.component.scss',
})
export class ToolComponent {
  title: string = 'GraphQL API Interactive Tool';
  private injector = inject(Injector);
  private service = inject(QueryManagerService);
  private gqlService = inject(GraphQlService);
  editorOptions = {
    mode: 'javascript',
    theme: 'nord',
    lineNumbers: true,
    matchBrackets: true,
    autoCloseBrackets: true,
    autocorrect: true,
  };
  queryEditorOptions = {
    ...this.editorOptions,
  };
  resultEditorOptions = {
    ...this.editorOptions,
    readOnly: true,
  };
  private destroy$: Subject<void> = new Subject();
  models: string[] = ['OpenAi', 'Custom'];
  selectedModel = this.models[0];
  apis$: Observable<IApiModel[]> = this.service.getApis();
  selectedApi?: string;
  @ViewChild('autosize') autosize!: CdkTextareaAutosize;
  input$: Subject<string> = new Subject<string>();
  buildingQuery: WritableSignal<boolean> = signal(false);
  queryStream$: Observable<string> = this.input$.pipe(
    tap(() => this.buildingQuery.set(true)),
    switchMap((value) => this.fetchGraphQlQuery(value))
  );
  result$: Subject<void> = new Subject();
  resultStream$: Observable<string> = this.result$.pipe(
    tap(() => this.fetchingResult.set(true)),
    switchMap(() => this.fetchData())
  );
  fetchingResult: WritableSignal<boolean> = signal(false);
  naturalLanguageQuery: string | undefined;
  queryModel: WritableSignal<string> = signal('');
  sendQueryEnabled: Signal<boolean> = computed(() => !!this.queryModel());

  ngOnInit() {
    this.apis$.pipe(takeUntil(this.destroy$)).subscribe({
      next: (values) => {
        this.selectedApi = values[0].url;
      },
    });
  }

  ngOnDestroy() {
    this.destroy$.next();
  }

  private fetchGraphQlQuery(value: string): Observable<string> {
    return this.service
      .generateGraphqlQuery(this.selectedApi!, this.selectedModel, value)
      .pipe(
        map((response) => response.query ?? response.message),
        tap((value) => this.queryModel.set(value)),
        finalize(() => this.buildingQuery.set(false))
      );
  }

  generateQuery() {
    if (this.naturalLanguageQuery) {
      this.input$.next(this.naturalLanguageQuery.trim());
    }
  }

  sendQuery() {
    this.result$.next();
  }

  fetchData() {
    return this.gqlService
      .executeQuery(this.selectedApi!, this.queryModel())
      .pipe(
        map((response) => JSON.stringify(response.data, null, 2)),
        finalize(() => {
          this.fetchingResult.set(false);
        }),
        take(1),
        catchError((err) => of(err))
      );
  }

  triggerResize() {
    afterNextRender(
      () => {
        this.autosize.resizeToFitContent(true);
      },
      {
        injector: this.injector,
      }
    );
  }
}
