import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from '@nestjs/common';
import { type OutPutData } from '@lib/shared/types/outPutData';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { type Response, type Request } from 'express';
@Injectable()
export class StructuredOutPutInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const ctx = context.switchToHttp();
    const request: Request = ctx.getRequest();
    const response: Response = ctx.getResponse();

    return next.handle().pipe(
      map((data: OutPutData) => {
        // Set the HTTP status code on the response
        const statusCode = data.code || 200;
        response.status(statusCode);
        return {
          timestamp: new Date().toISOString(),
          // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
          data: data.data ?? null,
          path: request.url,
          code: statusCode,
          message: data.message || 'success',
          success: true,
        };
      }),
    );
  }
}
