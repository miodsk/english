import {
  IsString,
  IsInt,
  Min,
  IsBoolean,
  IsNotEmpty,
  IsOptional,
} from 'class-validator';
import { Transform, Type } from 'class-transformer';
// 导入你的通用接口，起个别名防止重名冲突
import { type WordQuery as IWordQuery } from '@en/common/word';

export class WordQueryDto implements IWordQuery {
  @IsNotEmpty({ message: '页码不能为空' })
  @Type(() => Number) // 强制转为数字
  @IsInt()
  @Min(1)
  page: number;

  @IsNotEmpty({ message: '每页数量不能为空' })
  @Type(() => Number) // 强制转为数字
  @IsInt()
  @Min(1)
  pageSize: number;

  @IsOptional()
  @IsString()
  word?: string;

  /**
   * 标签字段：
   * 接口定义的是 boolean，但 URL 传过来的是字符串 "true"
   * 使用 @Transform 进行统一处理
   */
  @IsOptional()
  @IsBoolean()
  @Transform(({ value }) => value === 'true' || value === true)
  gk?: boolean;

  @IsOptional()
  @IsBoolean()
  @Transform(({ value }) => value === 'true' || value === true)
  zk?: boolean;

  @IsOptional()
  @IsBoolean()
  @Transform(({ value }) => value === 'true' || value === true)
  gre?: boolean;

  @IsOptional()
  @IsBoolean()
  @Transform(({ value }) => value === 'true' || value === true)
  toefl?: boolean;

  @IsOptional()
  @IsBoolean()
  @Transform(({ value }) => value === 'true' || value === true)
  ielts?: boolean;

  @IsOptional()
  @IsBoolean()
  @Transform(({ value }) => value === 'true' || value === true)
  cet6?: boolean;

  @IsOptional()
  @IsBoolean()
  @Transform(({ value }) => value === 'true' || value === true)
  cet4?: boolean;

  @IsOptional()
  @IsBoolean()
  @Transform(({ value }) => value === 'true' || value === true)
  ky?: boolean;
}
