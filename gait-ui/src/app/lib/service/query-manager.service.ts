import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { IGenerateQueryResponse } from '../model/i-generate-query-response';
import { IApiModel } from '../model/i-api-model';
import { IEntity } from '../model/i-entity';

@Injectable({
  providedIn: 'root',
})
export class QueryManagerService {
  private apiUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  generateGraphqlQuery(
    apiUrl: string,
    model: string,
    userInput: string
  ): Observable<IGenerateQueryResponse> {
    const body = {
      api_url: apiUrl,
      model: model,
      user_input: userInput,
    };
    const headers = new HttpHeaders().set('Content-Type', 'application/json');

    return this.http.post<IGenerateQueryResponse>(
      `${this.apiUrl}/generate_query`,
      body,
      {
        headers,
      }
    );
  }

  getApis(): Observable<IApiModel[]> {
    return this.http.get<IApiModel[]>(`${this.apiUrl}/apis`);
  }

  getEntities(apiUrl: string): Observable<IEntity[]> {
    let params = new HttpParams().set('api_url', apiUrl);
    return this.http.get<IEntity[]>(`${this.apiUrl}/entities`, {
      params: params,
    });
  }

  getFields(entity: string): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/entities/${entity}`);
  }
}
