// 用户核心接口
export interface User {
    id: string;
    name: string;
    email?: string | null;      // Prisma 中的 String?
    phone: string;
    bio?: string | null;
    isTimingTask: boolean;
    timingTaskTime: string;
    address?: string | null;
    password: string;        // 提示：前端 Store 通常不建议存储密码
    avatar?: string | null;
    wordNumber: number;         // 单词数量
    dayNumber: number;          // 打卡天数
    createdAt: Date | string;   // 建议兼容 Date 对象或 ISO 字符串
    updatedAt: Date | string;
    lastLoginAt?: Date | string | null;

    // 关联记录（如果需要连表查询的数据）
    wordBookRecords?: WordBookRecord[];
    paymentRecords?: PaymentRecord[];
    courseRecords?: CourseRecord[];
}

// 关联模型的占位接口（根据你的需求补充具体字段）
export interface WordBookRecord {
    id: string;
    userId: string;
    // ... 其他字段
}

export interface PaymentRecord {
    id: string;
    amount: number;
    // ... 其他字段
}

export interface CourseRecord {
    id: string;
    courseName: string;
    // ... 其他字段
}

export type Token = {
    accessToken: string;
    refreshToken: string;
}

export type UserLogin = Pick<User, 'phone' | 'password'>
export type UserRegister = Pick<User, 'phone' | 'password' | 'name' | 'email'>
export type UserUpdate = Partial<Pick<User, 'name' | 'email' | 'bio' | 'isTimingTask' | 'timingTaskTime' | 'address' | 'avatar'>>
export type ResultUser = Omit<User, 'password'>

export type AvatarResult = {
    previewUrl: string;
    databaseUrl: string;
}
export type WebResultUser = ResultUser & {
    token: Token
}
export type TokenPayload = Pick<User, 'name' | 'email'> & {
    userId: User['id'];
}
export type RefreshTokenPayload = TokenPayload & {
    tokenType: 'access' | 'refresh';
}
export type UserInfo = Omit<User, 'password'>