import { PrismaClient } from '../libs/shared/src/generated/prisma/client';
import { PrismaPg } from '@prisma/adapter-pg';
import * as Minio from 'minio';
import fs from 'node:fs';
import 'dotenv/config';
const data = [
  {
    name: '高考单词',
    value: 'gk',
    description: '覆盖高考大纲核心词汇，按考频与题型分类，助力考前冲刺提分。',
    teacher: '浪白马',
    url: '',
    price: 0.01,
  },
  {
    name: '中考单词',
    value: 'zk',
    description: '紧扣中考考纲，初中三年词汇一站式掌握，打好英语基础。',
    teacher: '浪白马',
    url: '',
    price: 0.02,
  },
  {
    name: 'GRE单词',
    value: 'gre',
    description: 'GRE 核心词汇与同反义词拓展，适合留学备考与高阶阅读。',
    teacher: '浪白马',
    url: '',
    price: 0.03,
  },
  {
    name: '托福词汇',
    value: 'toefl',
    description: '托福听说读写高频词 + 学术场景词汇，提升备考效率。',
    teacher: '浪白马',
    url: '',
    price: 0.04,
  },
  {
    name: '雅思词汇',
    value: 'ielts',
    description: '雅思考试常考词汇与同义替换，兼顾移民与留学需求。',
    teacher: '浪白马',
    url: '',
    price: 0.05,
  },
  {
    name: '大学英语六级单词',
    value: 'cet6',
    description: '六级大纲词汇与真题高频词，配合阅读与写作场景记忆。',
    teacher: '浪白马',
    url: '',
    price: 0.06,
  },
  {
    name: '大学英语四级单词',
    value: 'cet4',
    description: '四级核心词汇与考点搭配，适合在校生系统备考。',
    teacher: '浪白马',
    url: '',
    price: 0.07,
  },
  {
    name: '考研单词',
    value: 'ky',
    description: '考研英语一/二通用词汇，结合真题与长难句场景记忆。',
    teacher: '浪白马',
    url: '',
    price: 0.08,
  },
];
const main = async () => {
  const prisma = new PrismaClient({
    adapter: new PrismaPg({
      connectionString: process.env.DATABASE_URL!,
    }),
  });
  await prisma.$connect();
  const minioClient = new Minio.Client({
    endPoint: process.env.MINIO_ENDPOINT!,
    port: parseInt(process.env.MINIO_PORT!),
    useSSL: process.env.MINIO_USE_SSL === 'true',
    accessKey: process.env.MINIO_ACCESS_KEY!,
    secretKey: process.env.MINIO_SECRET_KEY!,
  });
  const bucketName = 'course';
  const exists = await minioClient.bucketExists(bucketName);
  if (!exists) {
    await minioClient.makeBucket(bucketName);
    await minioClient.setBucketPolicy(
      bucketName,
      JSON.stringify({
        Version: '2012-10-17',
        Statement: [
          {
            Sid: 'CourseReadObjects',
            Effect: 'Allow',
            Principal: '*',
            Action: ['s3:GetObject'],
            Resource: [`arn:aws:s3:::${bucketName}/*`],
          },
        ],
      }),
    );
    console.log(`Bucket "${bucketName}" created successfully.`);
  } else {
    console.log(`Bucket "${bucketName}" already exists.`);
  }
  for (const item of data) {
    const file = fs.readFileSync(`./prisma/assets/${item.value}.png`);
    await minioClient.putObject(
      bucketName,
      `${item.value}.png`,
      file,
      file.length,
      {
        'Content-Type': 'image/png',
      },
    );
    await prisma.course.create({
      data: {
        name: item.name,
        value: item.value,
        description: item.description,
        teacher: item.teacher,
        url: `/${bucketName}/${item.value}.png`,
        price: item.price,
      },
    });
  }
  console.log('connected to database');
};
main();
