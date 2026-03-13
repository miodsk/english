import { Module } from '@nestjs/common';
import { AuthService } from './auth.service';
import { SharedModule } from '@lib/shared/shared.module';

@Module({
  imports: [SharedModule],
  providers: [AuthService],
  exports: [AuthService],
})
export class AuthModule {
}
