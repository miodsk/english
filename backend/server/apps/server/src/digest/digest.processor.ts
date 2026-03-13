import { Processor, WorkerHost, OnWorkerEvent } from '@nestjs/bullmq';
import { Job } from 'bullmq';
import { digestQueueName } from './queue';
import { EmailService } from '@lib/shared/email/email.service';
import { DigestService } from './digest.service';
interface EmailDigestData {
  userId: number;
  email: string;
  wordCount: number;
}
@Processor(digestQueueName.name)
export class DigestProcessor extends WorkerHost {
  constructor(
    private readonly email: EmailService,
    private readonly digest: DigestService,
  ) {
    super();
  }
  async process(job: Job<EmailDigestData>) {
    // do some stuff
    if (job.name === digestQueueName.task.emailDigest) {
      const { userId, email, wordCount } = job.data;
      await this.email.sendEmail(
        email,
        '每日单词日报',
        `您今天掌握了${wordCount}个单词，继续加油哦！`,
      );
      console.log('消费成功', { userId, email, wordCount });
    }
    if (job.name === digestQueueName.task.everyDayDigest) {
      await this.digest.handleEmailDigest();
      console.log('每天的摘要任务');
    }
  }
}
