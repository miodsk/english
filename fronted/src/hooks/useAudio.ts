export interface Options {
  rate?: number
  pitch?: number
  volume?: number
  lang?: string
}
let instance: SpeechSynthesisUtterance | null = null
const getInstance = () => {
  if (!instance) {
    instance = new SpeechSynthesisUtterance()
  }
  return instance
}
export const useAudio = (options: Options) => {
  const pronounce = getInstance()
  const { rate = 0.8, pitch = 1, volume = 1, lang = 'en-US' } = options
  pronounce.rate = rate
  pronounce.pitch = pitch
  pronounce.volume = volume
  pronounce.lang = lang

  const playAudio = (word: string) => {
    console.log('Playing audio for:', word)
    pronounce.text = word
    pronounce.lang = 'en-US'
    window.speechSynthesis.speak(pronounce)
  }
  return {
    playAudio,
  }
}
