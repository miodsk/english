import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
  InternalServerErrorException,
} from '@nestjs/common';
import { type Response, type Request } from 'express';

interface NestErrorResponse {
  message: string | string[];
  error: string;
  statusCode: number;
}

@Catch()
export class HttpFilter implements ExceptionFilter {
  catch(exception: any, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    let status = 500;
    let message: string | string[] = 'Internal server error';

    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const res = exception.getResponse();
      message =
        typeof res === 'object' && res !== null
          ? (res as NestErrorResponse).message
          : exception.message;
    } else if (exception.code === 'ECONNRESET' || exception.code === 'ETIMEDOUT') {
      status = 503;
      message = 'Service unavailable - connection error';
      console.error('Connection error:', {
        code: exception.code,
        message: exception.message,
        stack: exception.stack,
      });
    } else {
      console.error('Unhandled exception:', exception);
    }

    return response.status(status).json({
      timestamp: new Date().toISOString(),
      data: null,
      path: request.url,
      message: message,
      code: status,
      success: false,
    });
  }
}