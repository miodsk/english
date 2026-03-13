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
import { CourseService } from './course.service';
import type { Request } from 'express';
@Controller('course')
export class CourseController {
  constructor(private readonly courseService: CourseService) {}

  @Get('list')
  findAll() {
    return this.courseService.findAll();
  }
  @Get('my')
  findMy(@Req() req: Request) {
    return this.courseService.findMy(req.user.userId);
  }
}
