import { Controller, Post, Body } from '@nestjs/common';
import { TrackerService } from './tracker.service';
import type {
  UvDto,
  PerformanceDto,
  PvDto,
  EventDto,
  ErrorDto,
  UpdateUvDto,
} from '@en/common/tracker';
import { Public } from '@lib/shared/public/public.decorator';
@Public()
@Controller('tracker')
export class TrackerController {
  constructor(private readonly trackerService: TrackerService) {}
  @Post('uv')
  uv(@Body() body: UvDto) {
    return this.trackerService.uv(body);
  }
  @Post('update-uv')
  updateUv(@Body() body: UpdateUvDto) {
    return this.trackerService.updateUv(body);
  }
  @Post('performance')
  performance(@Body() body: PerformanceDto) {
    return this.trackerService.performance(body);
  }
  @Post('pv')
  pv(@Body() body: PvDto) {
    return this.trackerService.pv(body);
  }
  @Post('event')
  event(@Body() body: EventDto) {
    return this.trackerService.event(body);
  }
  @Post('error')
  async error(@Body() body: ErrorDto) {
    return this.trackerService.error(body);
  }
}
