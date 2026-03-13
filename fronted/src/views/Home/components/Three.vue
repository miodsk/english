<script setup lang="ts">
import * as THREE from 'three'
import { onMounted, useTemplateRef } from 'vue'
import { GLTFLoader, type GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const threeContainer = useTemplateRef('threeContainer')

// 1. 动画相关的全局变量
let mixer: THREE.AnimationMixer | null = null
const clock = new THREE.Clock()

const loader = new GLTFLoader()

function initThree() {
  // --- 场景与相机 ---
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(75, 500 / 250, 0.1, 4000)
  // 使用你提供的坐标
  camera.position.set(1144.29, 608.59, 2205.28)

  // --- 灯光 ---
  const ambientLight = new THREE.AmbientLight(0xffffff, 1)
  scene.add(ambientLight)
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(10, 20, 10)
  scene.add(directionalLight)

  // --- 渲染器 ---
  const renderer = new THREE.WebGLRenderer({
    canvas: threeContainer.value as HTMLCanvasElement,
    antialias: true,
    alpha: true,
    precision: 'highp',
    powerPreference: 'high-performance',
  })
  renderer.setSize(500, 250)
  renderer.setPixelRatio(window.devicePixelRatio)

  // --- 控制器 ---
  const controls = new OrbitControls(camera, renderer.domElement)

  // --- 加载模型与动画 ---
  loader.load('/models/steve.glb', (gltf: GLTF) => {
    const model = gltf.scene
    model.scale.set(2, 2, 2)
    scene.add(model)

    // 2. 初始化动画混合器
    if (gltf.animations && gltf.animations.length > 0) {
      mixer = new THREE.AnimationMixer(model)

      // 默认播放第一个动画 (Walk)
      const action = mixer.clipAction(gltf.animations[0])
      action.play()
    }
  })

  // --- 动画循环 ---
  const animate = () => {
    requestAnimationFrame(animate)

    if (mixer) {
      const delta = clock.getDelta()
      mixer.update(delta)
    }

    controls.update()
    renderer.render(scene, camera)
  }

  animate()
}

onMounted(() => {
  if (threeContainer.value) {
    initThree()
  }
})
</script>

<template>
  <div class="canvas-wrapper">
    <canvas ref="threeContainer"></canvas>
  </div>
</template>

<style scoped></style>
