import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  Req,
} from '@nestjs/common';
import { LearnService } from './learn.service';
import type { Request } from 'express';

@Controller('learn')
export class LearnController {
  constructor(private readonly learnService: LearnService) {}
  @Post('word/master')
  saveWordMater(
    @Body() { wordIds }: { wordIds: string[] },
    @Req() req: Request,
  ) {
    return this.learnService.saveWordMaster(wordIds, req.user.userId);
  }
  @Get('word/:id')
  getWordList(@Param('id') id: string, @Req() req: Request) {
    return this.learnService.getWordList(id, req.user.userId);
  }
}
