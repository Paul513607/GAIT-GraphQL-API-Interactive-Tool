import { CdkTextareaAutosize } from '@angular/cdk/text-field';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
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
import { MatAutocompleteSelectedEvent } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
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
  skipWhile,
  Subject,
  switchMap,
  take,
  takeUntil,
  tap,
  throwError,
} from 'rxjs';
import { IApiModel } from '../../lib/model/i-api-model';
import { GraphQlService } from '../../lib/service/graph-ql.service';
import { QueryManagerService } from '../../lib/service/query-manager.service';

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
    MatChipsModule,
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
  selectedApi!: string;
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
  private words$: Subject<string> = new Subject<string>();
  suggestions$: Observable<string[]> = this.words$.pipe(
    switchMap((word) =>
      this.service.getEntities(this.selectedApi).pipe(
        map((entities) =>
          entities.map((entity) => this.getLastWordFromURL(entity.uri))
        ),
        switchMap((entities) =>
          entities
            .map((word) => this.capitalize(word))
            .includes(this.capitalize(word))
            ? this.service.getFields(this.capitalize(word))
            : of([])
        ),
        skipWhile((suggestions) => suggestions.length == 0)
      )
    ),
    map((fields) => fields.map((field) => this.getLastWordFromURL(field)))
  );

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

  onInputChange(event: Event) {
    const input = (event.target as HTMLTextAreaElement)?.value;

    if (!!input) {
      const words = input.trim().split(/\s+/);
      this.words$.next(words[words.length - 1]);
    }
  }

  suggestionSelected(event: MatAutocompleteSelectedEvent) {
    this.naturalLanguageQuery += ' ' + event.option.value;
  }

  addSuggestion(suggestion: string) {
    this.naturalLanguageQuery += ' ' + suggestion;
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
        catchError((err) => of(JSON.stringify({ error: err }, null, 2)))
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

  private getLastWordFromURL(url: string) {
    const urlObj = new URL(url);
    const pathSegments = urlObj.pathname
      .split('/')
      .filter((segment) => segment !== '');
    return pathSegments[pathSegments.length - 1];
  }

  private capitalize(value: string): string {
    if (!value) return value;
    return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
  }
}
