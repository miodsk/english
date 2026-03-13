import { Injectable } from '@nestjs/common';
import { PrismaService, ResponseService } from '@lib/shared';
import { WordQueryDto } from './dto/searchWord.dto';
@Injectable()
export class WordBookService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly response: ResponseService,
  ) {}
  async findAll(query: WordQueryDto) {
    const res = await this.prisma.wordBook.findMany({
      where: {
        word: query.word ? { contains: query.word } : undefined,
        gk: query.gk,
        zk: query.zk,
        gre: query.gre,
        toefl: query.toefl,
        ielts: query.ielts,
        cet6: query.cet6,
        cet4: query.cet4,
        ky: query.ky,
      },
      skip: (query.page - 1) * query.pageSize,
      take: query.pageSize,
    });
    const total = await this.prisma.wordBook.count({
      where: {
        word: query.word ? { contains: query.word } : undefined,
        gk: query.gk,
        zk: query.zk,
        gre: query.gre,
        toefl: query.toefl,
        ielts: query.ielts,
        cet6: query.cet6,
        cet4: query.cet4,
        ky: query.ky,
      },
    });
    return this.response.success({
      list: res,
      total,
    });
  }
}
