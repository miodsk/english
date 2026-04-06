import type {ErrorDto, TrackerConfig} from '@en/common/tracker'
import {report} from '@/report'

export const reportError = (visitorId: string, config: TrackerConfig) => {
    let url = config.baseUrl + config.error.api
    window.addEventListener('error', (e: ErrorEvent) => {
        const body: ErrorDto = {
            visitorId,
            error: 'js',
            message: e.message,
            stack: e.error?.stack || '',
            url: window.location.href,
        }
        report(url, body)
    })
    window.addEventListener('unhandledrejection', (e: PromiseRejectionEvent) => {
        const isError = e.reason instanceof Error
        const body: ErrorDto = {
            visitorId,
            error: 'promise',
            message: isError ? e.reason.message : JSON.stringify(e.reason),
            stack: isError ? e.reason.stack : 'Promise Rejection',
            url: window.location.href,
        }
        report(url, body)
    })
}