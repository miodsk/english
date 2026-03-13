import { Request, Response } from 'express';
import { TokenPayload } from '@en/common/user';

declare module 'express' {
  interface Request {
    user: TokenPayload;
  }
}
