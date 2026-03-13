import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Query,
  Param,
  Delete,
} from '@nestjs/common';
import { WordBookService } from './word-book.service';
import { WordQueryDto } from './dto/searchWord.dto';
import { type Request } from 'express';
@Controller('word-book')
export class WordBookController {
  constructor(private readonly wordBookService: WordBookService) {}

  @Get()
  findAll(@Query() query: WordQueryDto) {
    console.log(query);
    return this.wordBookService.findAll(query);
  }
}
