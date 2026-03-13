import { Injectable } from '@nestjs/common';
import { CreateUserDto } from './dto/create-user.dto';
import { UpdateUserDto } from './dto/update-user.dto';
import { PrismaService } from '@lib/shared/prisma/prisma.service';
import { ResponseService } from '@lib/shared/response/response.service';
import { HttpException, HttpStatus } from '@nestjs/common';
import { MinioService } from '@lib/shared/minio/minio.service';
import { AuthService } from '../auth/auth.service';
import type {
  UserLogin,
  UserRegister,
  RefreshTokenPayload,
  UserUpdate,
} from '@en/common/user';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class UserService {
  constructor(
    private readonly prismaService: PrismaService,
    private readonly responseService: ResponseService,
    private readonly authService: AuthService,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
    private readonly minioService: MinioService,
  ) {}

  async login(data: UserLogin) {
    // phone password
    const user = await this.prismaService.user.findUnique({
      where: {
        phone: data.phone,
      },
    });
    if (!user || user.password !== data.password) {
      return this.responseService.error('Invalid phone or password');
    }
    // 更新登录时间
    const updatedUser = await this.prismaService.user.update({
      where: {
        id: user.id,
      },
      data: {
        lastLoginAt: new Date(),
      },
    });
    // 生成token
    const token = this.authService.generateToken({
      userId: user.id,
      name: user.name,
      email: user.email,
    });
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { password, ...userWithoutPassword } = updatedUser;
    return this.responseService.success({ ...userWithoutPassword, token });
  }

  async register(data: UserRegister) {
    //   name phone email password
    const existingPhone = await this.prismaService.user.findUnique({
      where: {
        phone: data.phone,
      },
    });
    if (existingPhone) {
      throw new HttpException(
        'Phone number already registered',
        HttpStatus.BAD_REQUEST,
      );
    }
    if (data.email) {
      const existingEmail = await this.prismaService.user.findUnique({
        where: {
          email: data.email,
        },
      });
      if (existingEmail) {
        throw new HttpException(
          'Email already registered',
          HttpStatus.BAD_REQUEST,
        );
      }
    }
    const user = await this.prismaService.user.create({
      data: {
        name: data.name,
        phone: data.phone,
        email: data.email,
        password: data.password,
        lastLoginAt: new Date(),
      },
    });
    const token = this.authService.generateToken({
      userId: user.id,
      name: user.name,
      email: user.email,
    });
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { password, ...userWithoutPassword } = user;
    return this.responseService.success({ ...userWithoutPassword, token });
  }

  async refreshToken(refreshToken: string) {
    try {
      const decoded = this.jwtService.verify<RefreshTokenPayload>(
        refreshToken,
        {
          secret: this.configService.get<string>('JWT_SECRET_KEY'),
        },
      );
      if (decoded.tokenType !== 'refresh') {
        return this.responseService.error(
          'Invalid token type',
          HttpStatus.UNAUTHORIZED,
        );
      }
      const user = await this.prismaService.user.findUnique({
        where: {
          id: decoded.userId,
        },
      });
      if (!user) {
        return this.responseService.error(
          'User not found',
          HttpStatus.NOT_FOUND,
        );
      }
      const token = this.authService.generateToken({
        userId: decoded.userId,
        name: decoded.name,
        email: decoded.email,
      });
      return this.responseService.success(token);
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (e) {
      return this.responseService.error(
        'Invalid refresh token',
        HttpStatus.UNAUTHORIZED,
      );
    }
  }

  async upload(file: Express.Multer.File) {
    if (!file) {
      return this.responseService.error(
        'File not found',
        HttpStatus.BAD_REQUEST,
      );
    }
    if (file.size > 5 * 1024 * 1024) {
      return this.responseService.error(
        'File too large',
        HttpStatus.BAD_REQUEST,
      );
    }
    const client = this.minioService.getClient();
    const bucket = this.minioService.getBucket()!;
    const fileName = `${Date.now()}-${file.originalname}`;
    await client.putObject(bucket, fileName, file.buffer, file.size, {
      'Content-Type': file.mimetype,
    });
    const isHttps = !!Number(this.configService.get<number>('MINIO_USE_SSL'));
    const baseUrl = isHttps ? 'https' : 'http';
    const port = Number(this.configService.get<number>('MINIO_PORT'));
    const databaseUrl = `/${bucket}/${fileName}`;
    const previewUrl = `${baseUrl}://${this.configService.get<string>('MINIO_ENDPOINT')}:${port}${databaseUrl}`;
    return this.responseService.success({
      previewUrl,
      databaseUrl,
    });
  }
  async update(data: UserUpdate, userId: string) {
    const updateUser = await this.prismaService.user.update({
      where: {
        id: userId,
      },
      data,
    });
    const updatedInfo = {
      name: updateUser.name,
      email: updateUser.email,
      bio: updateUser.bio,
      isTimingTask: updateUser.isTimingTask,
      timingTaskTime: updateUser.timingTaskTime,
      address: updateUser.address,
      avatar: updateUser.avatar,
    };
    return this.responseService.success(updatedInfo);
  }
  async info(userId: string) {
    const user = await this.prismaService.user.findUnique({
      where: {
        id: userId,
      },
    });
    if (!user) {
      return this.responseService.error('User not found', HttpStatus.NOT_FOUND);
    }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { password, ...userInfo } = user;
    return this.responseService.success(userInfo);
  }
}
