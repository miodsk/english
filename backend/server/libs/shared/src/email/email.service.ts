import { Injectable, OnModuleInit } from '@nestjs/common';
import * as nodemailer from 'nodemailer';
import { ConfigService } from '@nestjs/config';
@Injectable()
export class EmailService implements OnModuleInit {
  private transporter: nodemailer.Transporter;
  constructor(private readonly config: ConfigService) {}
  onModuleInit() {
    this.transporter = nodemailer.createTransport({
      host: this.config.get('EMAIL_HOST'),
      port: this.config.get('EMAIL_PORT'),
      secure: !!Number(this.config.get('EMAIL_USE_SSL')), // true for 465, false for other ports
      auth: {
        user: this.config.get('EMAIL_USER'),
        pass: this.config.get('EMAIL_PASSWORD'),
      },
    });
    // this.sendEmail('1131156534@qq.com', '测试', '测试');
  }
  async sendEmail(to: string, subject: string, text: string) {
    try {
      await this.transporter.sendMail({
        to,
        subject,
        text,
        from: this.config.get('EMAIL_FROM'),
      });
      return true;
    } catch (error) {
      console.log(error);
      return false;
    }
  }
}
