import { Injectable } from '@nestjs/common';
import { PrismaService } from 'libs/shared/src/prisma/prisma.service';
import { ResponseService } from 'libs/shared/src/response/response.service';
import type {
  UvDto,
  PerformanceDto,
  PvDto,
  EventDto,
  ErrorDto,
  UpdateUvDto,
} from '@en/common/tracker';
@Injectable()
export class TrackerService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly response: ResponseService,
  ) {}
  async uv(body: UvDto) {
    const visitor = await this.prisma.visitor.upsert({
      where: { anonymousId: body.anonymousId },
      create: {
        anonymousId: body.anonymousId,
        userId: body.userId,
        browser: body.browser,
        os: body.os,
        device: body.device,
      },
      update: {
        userId: body.userId,
        browser: body.browser,
        os: body.os,
        device: body.device,
      },
      select: {
        id: true,
      },
    });
    return this.response.success(visitor.id);
  }
  async updateUv(body: UpdateUvDto) {
    await this.prisma.visitor.update({
      where: { id: body.visitorId },
      data: {
        userId: body.userId,
      },
    });
    return this.response.success(true);
  }
  async performance(body: PerformanceDto) {
    await this.prisma.performanceEntry.create({
      data: {
        visitorId: body.visitorId,
        fp: body.fp,
        fcp: body.fcp,
        lcp: body.lcp,
        cls: body.cls,
        inp: body.inp,
      },
    });
    return this.response.success(true);
  }
  async pv(body: PvDto) {
    await this.prisma.pageView.create({
      data: {
        visitorId: body.visitorId,
        url: body.url,
        referrer: body.referrer,
        path: body.path,
      },
    });
    return this.response.success(true);
  }
  async event(body: EventDto) {
    await this.prisma.trackEvent.create({
      data: {
        visitorId: body.visitorId,
        event: body.event,
        payload: body.payload,
        url: body.url,
      },
    });
    return this.response.success(true);
  }
  async error(body: ErrorDto) {
    await this.prisma.errorEntry.create({
      data: {
        visitorId: body.visitorId,
        error: body.error,
        message: body.message,
        stack: body.stack,
        url: body.url,
      },
    });
    return this.response.success(true);
  }
}
