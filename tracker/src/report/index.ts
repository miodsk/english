export const report = (url, body) => {
    const blob = new Blob([JSON.stringify(body)], {type: 'application/json'})
    navigator.sendBeacon(url, blob)

}
export const reportFetch = async (url: string, body: any) => {
    const res = await fetch(url, {
        method: "POST",
        keepalive: true,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    })
    return res.json()
}