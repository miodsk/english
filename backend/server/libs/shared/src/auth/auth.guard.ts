import { CanActivate, ExecutionContext, Injectable } from '@nestjs/common';
import { Observable } from 'rxjs';
import { Reflector } from '@nestjs/core';
import { JwtService } from '@nestjs/jwt';
import type { RefreshTokenPayload } from '@en/common/user';
import { Request } from 'express';
import { UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class AuthGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {
  }

  canActivate(
    context: ExecutionContext,
  ): boolean | Promise<boolean> | Observable<boolean> {
    const request: Request = context.switchToHttp().getRequest();
    const isPublic = this.reflector.getAllAndOverride<boolean>('public', [
      context.getClass(),
      context.getHandler(),
    ]);
    if (isPublic) {
      return true;
    }
    const headers = request.headers;
    if (!headers.authorization) {
      throw new UnauthorizedException('扣1送地狱火');
    }
    const token = headers.authorization.split(' ')[1];
    try {
      const decoded = this.jwtService.verify<RefreshTokenPayload>(token, {
        secret: this.configService.get<string>('JWT_SECRET_KEY'),
      });
      if (decoded.tokenType !== 'access') {
        throw new UnauthorizedException('token已过期');
      }
      request.user = decoded;
      return true;
    } catch (e) {
      throw new UnauthorizedException('token已过期');
    }
  }
}
