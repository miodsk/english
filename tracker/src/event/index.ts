import type {EventDto, TrackerConfig} from '@en/common/tracker'
import {report} from '@/report'

export const reportEvent = (visitorId: string, config: TrackerConfig) => {
    const ButtonName = 'BUTTON'
    const SubmitName = 'SUBMIT'
    const SpanName = 'SPAN'
    let url = config.baseUrl + config.event.api
    document.addEventListener('click', (e: MouseEvent) => {
        const target = e.target as HTMLElement
        const sendEvent = () => {
            const react = target.getBoundingClientRect()
            const body: EventDto = {
                visitorId,
                event: e.type,
                payload: {
                    x: react.left.toFixed(2) || '0',
                    y: react.top.toFixed(2) || '0',
                    width: react.width.toFixed(2) || '0',
                    height: react.height.toFixed(2) || '0',
                    text: target.textContent
                },
                url: window.location.href
            }
            report(url, body)
        }
        if (target.nodeName === ButtonName) {
            sendEvent()
        } else if (target.nodeName === SpanName && target.parentElement?.nodeName === ButtonName) {
            sendEvent()
        }
    })
}