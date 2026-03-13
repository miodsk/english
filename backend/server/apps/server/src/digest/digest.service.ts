import { Injectable, OnModuleInit } from '@nestjs/common';
import { EmailService } from '@lib/shared/email/email.service';
import { PrismaService } from '@lib/shared/prisma/prisma.service';
import { ResponseService } from '@lib/shared/response/response.service';
import { Queue } from 'bullmq';
import { InjectQueue } from '@nestjs/bullmq';
import { digestQueueName } from './queue';
import dayjs from 'dayjs';
@Injectable()
export class DigestService implements OnModuleInit {
  constructor(
    private readonly email: EmailService,
    private readonly prisma: PrismaService,
    private readonly response: ResponseService,
    @InjectQueue(digestQueueName.name) private readonly digestQueue: Queue,
  ) {}
  async onModuleInit() {
    const jobId = 'every-day-digest-job';
    const existing = await this.digestQueue.getJob(jobId);
    if (!existing) {
      await this.digestQueue.add(
        digestQueueName.task.everyDayDigest,
        {},
        {
          jobId,
          repeat: {
            pattern: '0 0 * * *',
            tz: 'Asia/Shanghai',
          },
        },
      );
    }
  }
  async handleEmailDigest() {
    const userIds = await this.prisma.user.findMany({
      where: {
        isTimingTask: true,
        timingTaskTime: { not: '' },
        email: { not: null },
        wordBookRecords: {
          some: {
            createdAt: {
              gte: dayjs().startOf('day').toDate(),
              lte: dayjs().add(1, 'day').startOf('day').toDate(),
            },
          },
        },
      },
      select: {
        id: true,
        email: true,
        timingTaskTime: true,
        wordBookRecords: {
          where: {
            createdAt: {
              gte: dayjs().startOf('day').toDate(),
              lte: dayjs().add(1, 'day').startOf('day').toDate(),
            },
          },
        },
      },
    });
    console.log('用户列表', userIds);
    for (const user of userIds) {
      const [hour, minute, second] = user.timingTaskTime.split(':').map(Number);
      const targetTime = dayjs().hour(hour).minute(minute).second(second);
      let delay = targetTime.diff(dayjs());
      if (delay < 0) {
        delay = 0;
      }
      await this.digestQueue.add(
        digestQueueName.task.emailDigest,
        {
          userId: user.id,
          email: user.email,
          wordCount: user.wordBookRecords.length,
        },
        {
          delay,
        },
      );
    }
  }
}
