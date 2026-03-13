import { Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { Token, TokenPayload, RefreshTokenPayload } from '@en/common/user';

@Injectable()
export class AuthService {
  constructor(private readonly jwtService: JwtService) {
  }

  generateToken(payload: TokenPayload): Token {
    // 创建两个token
    // refreshToken刷新时间7天，accessToken刷新时间15分钟
    return {
      accessToken: this.jwtService.sign<RefreshTokenPayload>({
        ...payload,
        tokenType: 'access',
      }),
      refreshToken: this.jwtService.sign<RefreshTokenPayload>(
        {
          ...payload,
          tokenType: 'refresh',
        },
        { expiresIn: '7d' },
      ),
    };
  }
}
