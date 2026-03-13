<template>
  <div class="wave-wrapper">
    <svg viewBox="0 0 1440 1080" preserveAspectRatio="none">
      <path ref="wavePath" fill="#42b883" d="M0,1080 L1440,1080 L1440,1080 L0,1080 Z" />
    </svg>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import gsap from 'gsap'

const wavePath = ref(null)

// 路径数据（关键：点的数量保持一致）
const paths = {
  bottom: 'M0,1080 L1440,1080 L1440,1080 L0,1080 Z',
  wave: 'M0,1080 C360,800 1080,800 1440,1080 L1440,0 L0,0 Z',
  full: 'M0,1080 L1440,1080 L1440,0 L0,0 Z',
  top: 'M0,0 L1440,0 L1440,0 L0,0 Z',
}

// 动画：升起并盖住屏幕
const animateIn = () => {
  const tl = gsap.timeline()
  return tl
    .to(wavePath.value, {
      duration: 0.5,
      attr: { d: paths.wave },
      ease: 'power2.in',
    })
    .to(wavePath.value, {
      duration: 0.4,
      attr: { d: paths.full },
      ease: 'power2.out',
    })
}

// 动画：向顶部退场
const animateOut = () => {
  return gsap.to(wavePath.value, {
    duration: 0.8,
    attr: { d: paths.top },
    ease: 'power4.inOut',
  })
}

// 暴露方法给外部
defineExpose({ animateIn, animateOut })
</script>

<style scoped>
.wave-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  pointer-events: none; /* 初始状态不阻挡点击 */
}
svg {
  width: 100%;
  height: 100%;
}
</style>
