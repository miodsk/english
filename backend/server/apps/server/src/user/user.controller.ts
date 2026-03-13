import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  Req,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { UserService } from './user.service';
import type { Request } from 'express';
import type {
  UserLogin,
  UserRegister,
  Token,
  UserUpdate,
} from '@en/common/user';
import { Public } from '@lib/shared/public/public.decorator';
import { FileInterceptor } from '@nestjs/platform-express';

@Controller('user')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Public()
  @Post('login')
  login(@Body() loginUser: UserLogin) {
    return this.userService.login(loginUser);
  }

  @Public()
  @Post('register')
  register(@Body() registerUser: UserRegister) {
    return this.userService.register(registerUser);
  }
  @Post('info')
  info(@Req() req: Request) {
    const userId = req.user.userId;
    return this.userService.info(userId);
  }
  @Public()
  @Post('refreshToken')
  refreshToken(@Body() body: Omit<Token, 'accessToken'>) {
    return this.userService.refreshToken(body.refreshToken);
  }
  @Post('update')
  update(@Body() data: UserUpdate, @Req() req: Request) {
    const userId = req.user.userId;
    return this.userService.update(data, userId);
  }
  @UseInterceptors(FileInterceptor('file'))
  @Post('upload')
  upload(@UploadedFile() file: Express.Multer.File) {
    return this.userService.upload(file);
  }
}
