import { Injectable } from '@nestjs/common';

@Injectable()
export class ResponseService {
  success(data: any, message: string = 'Success', code: number = 200) {
    return {
      code,
      message,
      data: data as unknown,
    };
  }
  error(message: string = 'Error', data: any = null, code: number = 500) {
    return {
      code,
      message,
      data: data as unknown,
    };
  }
}
