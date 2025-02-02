import { Injectable } from '@angular/core';
import { Apollo, gql } from 'apollo-angular';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class GraphQlService {
  constructor(private apollo: Apollo) {}

  executeQuery(
    endpoint: string,
    query: string,
    variables?: any
  ): Observable<any> {
    return this.apollo.watchQuery({
      query: gql(query),
      variables: variables,
      context: {
        uri: endpoint,
      },
    }).valueChanges;
  }
}
