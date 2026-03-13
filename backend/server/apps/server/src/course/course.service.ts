import { Injectable } from '@nestjs/common';
import { PrismaService, ResponseService } from '@lib/shared';
import { CourseList } from '@en/common/course/index';
import { TradeStatus } from '@lib/shared/generated/prisma/enums';
@Injectable()
export class CourseService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly response: ResponseService,
  ) {}
  async findAll() {
    const courses = await this.prisma.course.findMany();
    const list: { price: string }[] = courses.map((course) => {
      return {
        ...course,
        price: Number(course.price).toFixed(2),
      };
    });

    return this.response.success(list);
  }
  async findMy(userId: string) {
    const courses = await this.prisma.courseRecord.findMany({
      where: {
        userId,
        paymentRecord: {
          tradeStatus: TradeStatus.TRADE_SUCCESS,
        },
      },
      include: {
        course: true,
      },
    });
    const list = courses.map((course) => {
      return {
        ...course.course,
        price: Number(course.course.price).toFixed(2),
      };
    });
    return this.response.success(list);
  }
}
