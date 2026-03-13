import { Injectable } from '@nestjs/common';
import * as Minio from 'minio';
import { ConfigService } from '@nestjs/config';
import { OnModuleInit } from '@nestjs/common';

@Injectable()
export class MinioService implements OnModuleInit {
  private readonly minioClient: Minio.Client;

  constructor(private readonly configService: ConfigService) {
    const useSSL = this.configService.get<string>('MINIO_USE_SSL') === 'true';
    this.minioClient = new Minio.Client({
      endPoint: this.configService.get<string>('MINIO_ENDPOINT')!,
      port: Number(this.configService.get<number>('MINIO_PORT')),
      useSSL,
      accessKey: this.configService.get<string>('MINIO_ACCESS_KEY'),
      secretKey: this.configService.get<string>('MINIO_SECRET_KEY'),
    });
  }

  async onModuleInit() {
    try {
      const bucket = this.configService.get<string>('MINIO_BUCKET')!;
      console.log('Checking MinIO connection...');
      const exists = await Promise.race([
        this.minioClient.bucketExists(bucket),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('MinIO connection timeout')), 5000),
        ),
      ]);

      if (!exists) {
        await this.minioClient.makeBucket(bucket);
        await this.minioClient.setBucketPolicy(
          bucket,
          JSON.stringify({
            Version: '2012-10-17',
            Statement: [
              {
                Sid: 'PublicReadObjects',
                Effect: 'Allow',
                Principal: '*',
                Action: ['s3:GetObject'],
                Resource: [`arn:aws:s3:::${bucket}/*`],
              },
            ],
          }),
        );
      }
      console.log('MinIO connected successfully');
    } catch (error) {
      console.error('Failed to connect to MinIO:', error);
      throw error;
    }
  }

  getClient() {
    return this.minioClient;
  }

  getBucket() {
    return this.configService.get<string>('MINIO_BUCKET');
  }
}
