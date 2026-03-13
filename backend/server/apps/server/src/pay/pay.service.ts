import { Injectable } from '@nestjs/common';
import type { CreatePayDto } from '@en/common/pay/index';
import * as nanoid from 'nanoid';
import type { User, TokenPayload } from '@en/common/user/index';
import { PayService as SharedPayService } from '@lib/shared';
import { PrismaService } from '@lib/shared';
import { TradeStatus } from '@lib/shared/generated/prisma/enums';
import dayjs from 'dayjs';
import { ConfigService } from '@nestjs/config';
import { ResponseService } from '@lib/shared';
import { SocketGateway } from '../socket/socket.gateway';
import type { Request } from 'express';
interface AlipayNotifyBody {
  out_trade_no: string;
  trade_no: string;
  gmt_payment: string;
  body: string;
  subject: string;
  // 如果有其他字段，继续添加
}
@Injectable()
export class PayService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly sharedPayService: SharedPayService,
    private readonly configService: ConfigService,
    private readonly response: ResponseService,
    private readonly socketGateway: SocketGateway,
  ) {}
  private createTradeNo() {
    const prefix = 'LBM';
    return `${prefix}-${nanoid.nanoid(10)}`;
  }
  async create(
    createPayDto: CreatePayDto,
    user: Pick<User, 'name' | 'email'> & { userId: User['id'] },
  ) {
    const courseRecord = await this.prisma.courseRecord.findFirst({
      where: {
        userId: user.userId,
        courseId: createPayDto.courseId,
      },
    });
    if (courseRecord) {
      return this.response.error('课程已购买');
    }
    const res = await this.prisma.$transaction(async (tx) => {
      const outTradeNo = this.createTradeNo();
      const dateTime = dayjs().add(1, 'minute');
      await tx.paymentRecord.create({
        data: {
          userId: user.userId,
          outTradeNo,
          amount: createPayDto.total_amount,
          subject: createPayDto.subject,
          body: createPayDto.body,
        },
      });
      const payUrl = this.sharedPayService
        .getAlipaySdk()
        .pageExecute('alipay.trade.page.pay', 'GET', {
          bizContent: {
            out_trade_no: outTradeNo,
            total_amount: createPayDto.total_amount,
            subject: createPayDto.subject,
            body: `${JSON.stringify({
              courseId: createPayDto.courseId,
              userId: user.userId,
            })}`,
            product_code: 'FAST_INSTANT_TRADE_PAY',
            time_express: dateTime.format('YYYY-MM-DD HH:mm:ss'),
          },
          notify_url: `${this.configService.get<string>('ALIPAY_NOTIFY_URL')!}/api/v1/pay/notify`,
        });
      return {
        payUrl,
        timeExpire: dateTime.toDate().getTime(),
      };
    });
    return this.response.success(res);
  }
  async notify(req: Request) {
    const body = req.body as AlipayNotifyBody;
    const res = await this.prisma.$transaction(async (tx) => {
      const paymentRecord = await tx.paymentRecord.update({
        where: {
          outTradeNo: body.out_trade_no,
        },
        data: {
          tradeNo: body.trade_no,
          tradeStatus: TradeStatus.TRADE_SUCCESS,
          sendPayTime: dayjs(body.gmt_payment).toDate(),
        },
      });
      const { userId, courseId } = JSON.parse(body.body) as {
        userId: string;
        courseId: string;
      };
      await tx.courseRecord.create({
        data: {
          userId,
          courseId,
          isPurchased: true,
          paymentRecordId: paymentRecord.id,
        },
      });
      this.socketGateway.emitPaymentSuccess(userId);
    });
    return true;
  }
}
