import { Controller, Get, Post, Body, Req } from '@nestjs/common';
import { Public } from '@lib/shared/public/public.decorator';
import { All } from '@nestjs/common';
import { PayService } from './pay.service';
import type { Request } from 'express';
import type { CreatePayDto } from '@en/common/pay/index';

@Controller('pay')
export class PayController {
  constructor(private readonly payService: PayService) {}

  @Post('create')
  create(@Body() createPayDto: CreatePayDto, @Req() req: Request) {
    const user = req.user;
    return this.payService.create(createPayDto, user);
  }
  @All('notify')
  @Public()
  notify(@Req() req: Request) {
    console.log(req.body);
    return this.payService.notify(req);
  }
}
