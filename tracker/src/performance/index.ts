import type {PerformanceDto, TrackerConfig} from '@en/common/tracker'
import {onINP, onCLS} from 'web-vitals'
import {report} from "@/report"

export const reportPerformance = async (visitorId: string, config: TrackerConfig) => {
    let fp = 0
    let fcp = 0
    let lcp = 0
    let cls = 0
    let inp = 0
    let performanceEntries = performance.getEntriesByType('paint')
    let url = config.baseUrl + config.performance.api
    performanceEntries.forEach((entry) => {
        if (entry.name === 'first-paint') {
            fp = entry.startTime
        } else if (entry.name === 'first-contentful-paint') {
            fcp = entry.startTime
        }
    })
    let lcpPromise = new Promise<{ lcpTime: number, lcpObserver: PerformanceObserver }>(resolve => {
        const lcpObserver = new PerformanceObserver((entryList) => {
            resolve({lcpTime: entryList.getEntries().at(-1).startTime || 0, lcpObserver})
        })
        lcpObserver.observe({type: 'largest-contentful-paint', buffered: true})
    })
    const {lcpTime, lcpObserver} = await lcpPromise
    lcpObserver.disconnect()
    lcp = lcpTime

    onINP((metric) => {
        inp = metric.value
    })
    onCLS(metric => {
        cls = metric.value
    })
    window.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            console.log({
                visitorId,
                fp,
                fcp,
                lcp,
                cls,
                inp
            })
        }
        const body: PerformanceDto = {
            visitorId,
            fp,
            fcp,
            lcp,
            cls,
            inp
        }
        report(url, body)
    }, {once: true})
}