from typing import Optional
import datetime
import decimal
import enum

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Boolean, DateTime, Double, Enum, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP


class Tradestatus(str, enum.Enum):
    NOT_PAY = 'NOT_PAY'
    WAIT_BUYER_PAY = 'WAIT_BUYER_PAY'
    TRADE_CLOSED = 'TRADE_CLOSED'
    TRADE_SUCCESS = 'TRADE_SUCCESS'
    TRADE_FINISHED = 'TRADE_FINISHED'


class Course(SQLModel, table=True):
    __tablename__ = 'Course'

    id: str = Field(sa_column=Column(Text, primary_key=True))
    name: str = Field(sa_column=Column(Text, nullable=False))
    value: str = Field(sa_column=Column(Text, nullable=False))
    teacher: str = Field(sa_column=Column(Text, nullable=False))
    url: str = Field(sa_column=Column(Text, nullable=False))
    price: decimal.Decimal = Field(sa_column=Column(Numeric(65, 30), nullable=False))
    createdAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP')))
    updatedAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(Text))

    CourseRecord: list['CourseRecord'] = Relationship(back_populates='Course_')


class User(SQLModel, table=True):
    __tablename__ = 'User'

    id: str = Field(sa_column=Column(Text, primary_key=True))
    name: str = Field(sa_column=Column(Text, nullable=False))
    phone: str = Field(sa_column=Column(Text, nullable=False, unique=True))
    password: str = Field(sa_column=Column(Text, nullable=False))
    wordNumber: int = Field(sa_column=Column(Integer, nullable=False, server_default=text('0')))
    dayNumber: int = Field(sa_column=Column(Integer, nullable=False, server_default=text('0')))
    createdAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP')))
    updatedAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False))
    isTimingTask: bool = Field(sa_column=Column(Boolean, nullable=False, server_default=text('false')))
    timingTaskTime: str = Field(sa_column=Column(Text, nullable=False, server_default=text("'00:00:00'::text")))
    email: Optional[str] = Field(default=None, sa_column=Column(Text, unique=True))
    address: Optional[str] = Field(default=None, sa_column=Column(Text))
    avatar: Optional[str] = Field(default=None, sa_column=Column(Text))
    lastLoginAt: Optional[datetime.datetime] = Field(default=None, sa_column=Column(TIMESTAMP(precision=3)))
    bio: Optional[str] = Field(default=None, sa_column=Column(Text))

    PaymentRecord: list['PaymentRecord'] = Relationship(back_populates='User_')
    WordBookRecord: list['WordBookRecord'] = Relationship(back_populates='User_')
    CourseRecord: list['CourseRecord'] = Relationship(back_populates='User_')


class WordBook(SQLModel, table=True):
    __tablename__ = 'WordBook'

    id: str = Field(sa_column=Column(Text, primary_key=True))
    word: str = Field(sa_column=Column(Text, nullable=False))
    createdAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP')))
    updatedAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False))
    phonetic: Optional[str] = Field(default=None, sa_column=Column(Text))
    definition: Optional[str] = Field(default=None, sa_column=Column(Text))
    translation: Optional[str] = Field(default=None, sa_column=Column(Text))
    pos: Optional[str] = Field(default=None, sa_column=Column(Text))
    collins: Optional[str] = Field(default=None, sa_column=Column(Text))
    oxford: Optional[str] = Field(default=None, sa_column=Column(Text))
    tag: Optional[str] = Field(default=None, sa_column=Column(Text))
    bnc: Optional[str] = Field(default=None, sa_column=Column(Text))
    frq: Optional[str] = Field(default=None, sa_column=Column(Text))
    exchange: Optional[str] = Field(default=None, sa_column=Column(Text))
    gk: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    zk: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    gre: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    toefl: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    ielts: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    cet6: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    cet4: Optional[bool] = Field(default=None, sa_column=Column(Boolean))
    ky: Optional[bool] = Field(default=None, sa_column=Column(Boolean))

    WordBookRecord: list['WordBookRecord'] = Relationship(back_populates='WordBook_')


class PrismaMigrations(SQLModel, table=True):
    __tablename__ = '_prisma_migrations'

    id: str = Field(sa_column=Column(String(36), primary_key=True))
    checksum: str = Field(sa_column=Column(String(64), nullable=False))
    migration_name: str = Field(sa_column=Column(String(255), nullable=False))
    started_at: datetime.datetime = Field(sa_column=Column(DateTime(True), nullable=False, server_default=text('now()')))
    applied_steps_count: int = Field(sa_column=Column(Integer, nullable=False, server_default=text('0')))
    finished_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column(DateTime(True)))
    logs: Optional[str] = Field(default=None, sa_column=Column(Text))
    rolled_back_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column(DateTime(True)))


class PaymentRecord(SQLModel, table=True):
    __tablename__ = 'PaymentRecord'

    id: str = Field(sa_column=Column(Text, primary_key=True))
    userId: str = Field(sa_column=Column(Text, ForeignKey('User.id'), nullable=False))
    outTradeNo: str = Field(sa_column=Column(Text, nullable=False, unique=True))
    amount: decimal.Decimal = Field(sa_column=Column(Numeric(65, 30), nullable=False))
    subject: str = Field(sa_column=Column(Text, nullable=False))
    body: str = Field(sa_column=Column(Text, nullable=False))
    tradeStatus: Tradestatus = Field(
        sa_column=Column(
            Enum(Tradestatus, values_callable=lambda cls: [member.value for member in cls], name='TradeStatus'),
            nullable=False,
            server_default=text('\'NOT_PAY\'::"TradeStatus"')
        )
    )
    createdAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP')))
    updatedAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False))
    tradeNo: Optional[str] = Field(default=None, sa_column=Column(Text))
    sendPayTime: Optional[datetime.datetime] = Field(default=None, sa_column=Column(TIMESTAMP(precision=3)))

    User_: 'User' = Relationship(back_populates='PaymentRecord')
    CourseRecord: list['CourseRecord'] = Relationship(back_populates='PaymentRecord_')


class WordBookRecord(SQLModel, table=True):
    __tablename__ = 'WordBookRecord'

    id: str = Field(sa_column=Column(Text, primary_key=True))
    wordId: str = Field(sa_column=Column(Text, ForeignKey('WordBook.id'), nullable=False))
    userId: str = Field(sa_column=Column(Text, ForeignKey('User.id'), nullable=False))
    easinessFactor: float = Field(sa_column=Column(Double(53), nullable=False, server_default=text('2.5')))
    interval: int = Field(sa_column=Column(Integer, nullable=False, server_default=text('0')))
    reps: int = Field(sa_column=Column(Integer, nullable=False, server_default=text('0')))
    nextReviewAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP')))
    isMaster: bool = Field(sa_column=Column(Boolean, nullable=False, server_default=text('false')))
    wrongCount: int = Field(sa_column=Column(Integer, nullable=False, server_default=text('0')))
    createdAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP')))
    updatedAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False))

    User_: 'User' = Relationship(back_populates='WordBookRecord')
    WordBook_: 'WordBook' = Relationship(back_populates='WordBookRecord')
    ReviewLog: list['ReviewLog'] = Relationship(back_populates='WordBookRecord_')


class CourseRecord(SQLModel, table=True):
    __tablename__ = 'CourseRecord'

    id: str = Field(sa_column=Column(Text, primary_key=True))
    userId: str = Field(sa_column=Column(Text, ForeignKey('User.id'), nullable=False))
    courseId: str = Field(sa_column=Column(Text, ForeignKey('Course.id'), nullable=False))
    isPurchased: bool = Field(sa_column=Column(Boolean, nullable=False, server_default=text('false')))
    createdAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP')))
    updatedAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False))
    paymentRecordId: Optional[str] = Field(default=None, sa_column=Column(Text, ForeignKey('PaymentRecord.id')))

    Course_: 'Course' = Relationship(back_populates='CourseRecord')
    PaymentRecord_: Optional['PaymentRecord'] = Relationship(back_populates='CourseRecord')
    User_: 'User' = Relationship(back_populates='CourseRecord')


class ReviewLog(SQLModel, table=True):
    __tablename__ = 'ReviewLog'

    id: str = Field(sa_column=Column(Text, primary_key=True))
    recordId: str = Field(sa_column=Column(Text, ForeignKey('WordBookRecord.id'), nullable=False))
    rating: int = Field(sa_column=Column(Integer, nullable=False))
    responseTime: int = Field(sa_column=Column(Integer, nullable=False))
    createdAt: datetime.datetime = Field(sa_column=Column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP')))

    WordBookRecord_: 'WordBookRecord' = Relationship(back_populates='ReviewLog')
