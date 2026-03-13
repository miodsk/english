import { Controller, Get } from '@nestjs/common';
import { AppService } from './app.service';
import { PrismaService } from '@lib/shared';
import { ResponseService } from '@lib/shared/response/response.service';
import { AuthGuard } from '@lib/shared/auth/auth.guard';

@Controller()
export class AppController {
  constructor(
    private readonly appService: AppService,
    private readonly prismaService: PrismaService,
    private readonly responseService: ResponseService,
  ) {
  }

  @Get()
  getAllUser() {
    return this.appService.getHello();
  }
}
