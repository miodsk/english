import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';
import { DigestService } from './digest.service';
import { digestQueueName } from './queue';
import { DigestProcessor } from './digest.processor';
@Module({
  imports: [
    BullModule.registerQueue({
      name: digestQueueName.name,
    }),
  ],
  providers: [DigestService, DigestProcessor],
})
export class DigestModule {}
