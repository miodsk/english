import { Injectable } from '@nestjs/common';
import { PrismaService } from '@lib/shared/prisma/prisma.service';
import { ResponseService } from '@lib/shared/response/response.service';
@Injectable()
export class LearnService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly response: ResponseService,
  ) {}
  async saveWordMaster(wordIds: string[], userId: string) {
    const wordBookRecords = wordIds.map((wordId) => {
      return {
        wordId,
        userId,
        isMaster: true,
      };
    });
    await this.prisma.wordBookRecord.createMany({
      data: wordBookRecords,
    });
    await this.prisma.user.update({
      where: {
        id: userId,
      },
      data: {
        wordNumber: {
          increment: wordIds.length,
        },
      },
    });
    return this.response.success(wordBookRecords);
  }
  async getWordList(id: string, userId: string) {
    const courseRecord = await this.prisma.courseRecord.findFirst({
      where: {
        userId,
        courseId: id,
        isPurchased: true,
      },
      include: {
        course: true,
      },
    });
    if (!courseRecord) {
      return this.response.error('课程未购买');
    }
    const courseType = courseRecord.course.value;
    const res = await this.prisma.wordBook.findMany({
      where: {
        [courseType]: true,
        wordBookRecords: {
          none: {
            userId,
          },
        },
      },
      skip: 0,
      take: 10,
      orderBy: {
        frq: 'desc',
      },
    });
    return this.response.success(res);
  }
}
