import type {TrackerConfig, UvDto} from '@en/common/tracker'
import FingerprintJS from '@fingerprintjs/fingerprintjs'
import {UAParser} from 'ua-parser-js'
import {reportFetch} from '@/report'

export const getBrowserInfo = () => {
    const ua = new UAParser()
    return {
        browser: ua.getBrowser().name,
        os: ua.getOS().name,
        device: ua.getDevice().type || "desktop "
    }
}
export const getFingerprint = async (config: TrackerConfig) => {
    const browserInfo = getBrowserInfo()
    const fp = await FingerprintJS.load()
    const result = await fp.get()
    const body: UvDto = {
        anonymousId: result.visitorId,
        ...browserInfo
    }
    let url = config.baseUrl + config.uv.api
    const res = await reportFetch(url, body)

    return res.data
}