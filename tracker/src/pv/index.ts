import type {PvDto, TrackerConfig} from '@en/common/tracker'
import {report} from '@/report'

const reportView = (visitorId: string, config: TrackerConfig) => {
    let url = config.baseUrl + config.pv.api
    const isHash = window.location.href.includes('#')
    const body: PvDto = {
        visitorId,
        url: window.location.protocol + '//' + window.location.host,
        referrer: document.referrer,
        path: isHash ? '/' + window.location.hash : window.location.pathname
    }
    report(url, body)

}
export const reportPv = (visitorId: string, config: TrackerConfig) => {
    reportView(visitorId, config)
    window.addEventListener('hashchange', (e: HashChangeEvent) => {
        reportView(visitorId, config)
    })
    window.addEventListener('popstate', (e: PopStateEvent) => {
        reportView(visitorId, config)
    })
    const originalPushState = history.pushState
    history.pushState = function () {
        originalPushState.apply(this, arguments as any)
        reportView(visitorId, config)
    }
    const originalReplaceState = history.replaceState
    history.replaceState = function () {
        originalReplaceState.apply(this, arguments as any)
        reportView(visitorId, config)
    }
}