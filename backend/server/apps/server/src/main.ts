import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { VersioningType } from '@nestjs/common';
import { ValidationPipe } from '@nestjs/common';
import { HttpFilter } from '@lib/shared/httpfilter/httpfilter.filter';
import { StructuredOutPutInterceptor } from '@lib/shared/structured-out-put/structured-out-put.interceptor';
import { AuthGuard } from '@lib/shared/auth/auth.guard';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.useGlobalFilters(new HttpFilter());
  app.useGlobalInterceptors(new StructuredOutPutInterceptor());
  app.setGlobalPrefix('api');
  app.enableVersioning({ type: VersioningType.URI, defaultVersion: '1' });
  app.useGlobalPipes(
    new ValidationPipe({
      transform: true,

      transformOptions: {
        enableImplicitConversion: true,
      },

      whitelist: true,

      stopAtFirstError: true,
    }),
  );
  await app.listen(process.env.PORT ?? 3000);
}

bootstrap();
