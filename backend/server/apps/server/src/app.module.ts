import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { UserModule } from './user/user.module';
import { SharedModule } from '@lib/shared';
import { WordBookModule } from './word-book/word-book.module';
import { AuthModule } from './auth/auth.module';
import { AuthGuard } from '@lib/shared/auth/auth.guard';
import { CourseModule } from './course/course.module';
import { PayModule } from './pay/pay.module';
import { SocketModule } from './socket/socket.module';
import { LearnModule } from './learn/learn.module';
import { DigestService } from './digest/digest.service';
import { DigestModule } from './digest/digest.module';

@Module({
  imports: [
    UserModule,
    SharedModule,
    WordBookModule,
    AuthModule,
    CourseModule,
    PayModule,
    SocketModule,
    LearnModule,
    DigestModule,
  ],
  controllers: [AppController],
  providers: [
    AppService,
    {
      provide: 'APP_GUARD',
      useClass: AuthGuard,
    },
  ],
})
export class AppModule {}
