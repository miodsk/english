<script setup lang="ts">
import { ref, onMounted, onUnmounted, inject } from 'vue'
import { LOGIN_MODE } from './types.ts'

const mode = inject(LOGIN_MODE, ref<'login' | 'register'>('login'))

const canvasRef = ref<HTMLCanvasElement | null>(null)
const score = ref(0)
const gameOver = ref(false)
const gameStarted = ref(false)
const highScore = ref(parseInt(localStorage.getItem('snakeHighScore') || '0'))

// 游戏配置
const gridSize = 20
const canvasSize = 400
let ctx: CanvasRenderingContext2D | null = null
let gameLoop: number | null = null

// 蛇和食物
let snake: { x: number; y: number }[] = []
let food = { x: 0, y: 0 }
let direction = { x: 1, y: 0 }
let nextDirection = { x: 1, y: 0 }

// 初始化游戏
const initGame = () => {
  snake = [
    { x: 10, y: 10 },
    { x: 9, y: 10 },
    { x: 8, y: 10 }
  ]
  direction = { x: 1, y: 0 }
  nextDirection = { x: 1, y: 0 }
  score.value = 0
  gameOver.value = false
  generateFood()
}

// 生成食物
const generateFood = () => {
  do {
    food = {
      x: Math.floor(Math.random() * (canvasSize / gridSize)),
      y: Math.floor(Math.random() * (canvasSize / gridSize))
    }
  } while (snake.some(segment => segment.x === food.x && segment.y === food.y))
}

// 绘制游戏
const draw = () => {
  if (!ctx) return

  // 清空画布
  ctx.fillStyle = '#1a1a2e'
  ctx.fillRect(0, 0, canvasSize, canvasSize)

  // 绘制网格
  ctx.strokeStyle = '#16213e'
  ctx.lineWidth = 0.5
  for (let i = 0; i <= canvasSize; i += gridSize) {
    ctx.beginPath()
    ctx.moveTo(i, 0)
    ctx.lineTo(i, canvasSize)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(0, i)
    ctx.lineTo(canvasSize, i)
    ctx.stroke()
  }

  // 绘制蛇
  snake.forEach((segment, index) => {
    const isHead = index === 0
    ctx!.fillStyle = isHead ? '#00ff88' : '#00cc6a'
    ctx!.fillRect(
      segment.x * gridSize + 1,
      segment.y * gridSize + 1,
      gridSize - 2,
      gridSize - 2
    )
    
    // 绘制蛇头眼睛
    if (isHead) {
      ctx!.fillStyle = '#fff'
      const eyeSize = 3
      const eyeOffset = 5
      ctx!.beginPath()
      ctx!.arc(
        segment.x * gridSize + eyeOffset,
        segment.y * gridSize + eyeOffset,
        eyeSize,
        0,
        Math.PI * 2
      )
      ctx!.fill()
      ctx!.beginPath()
      ctx!.arc(
        segment.x * gridSize + gridSize - eyeOffset,
        segment.y * gridSize + eyeOffset,
        eyeSize,
        0,
        Math.PI * 2
      )
      ctx!.fill()
    }
  })

  // 绘制食物
  ctx.fillStyle = '#ff6b6b'
  ctx.beginPath()
  ctx.arc(
    food.x * gridSize + gridSize / 2,
    food.y * gridSize + gridSize / 2,
    gridSize / 2 - 2,
    0,
    Math.PI * 2
  )
  ctx.fill()
  
  // 食物高光
  ctx.fillStyle = '#ff8787'
  ctx.beginPath()
  ctx.arc(
    food.x * gridSize + gridSize / 2 - 3,
    food.y * gridSize + gridSize / 2 - 3,
    3,
    0,
    Math.PI * 2
  )
  ctx.fill()
}

// 游戏更新
const update = () => {
  if (snake.length === 0) return
  
  direction = { ...nextDirection }
  
  const head = {
    x: snake[0]!.x + direction.x,
    y: snake[0]!.y + direction.y
  }

  // 检查撞墙
  if (
    head.x < 0 ||
    head.x >= canvasSize / gridSize ||
    head.y < 0 ||
    head.y >= canvasSize / gridSize
  ) {
    endGame()
    return
  }

  // 检查撞自己
  if (snake.some(segment => segment.x === head.x && segment.y === head.y)) {
    endGame()
    return
  }

  snake.unshift(head)

  // 检查吃到食物
  if (head.x === food.x && head.y === food.y) {
    score.value += 10
    if (score.value > highScore.value) {
      highScore.value = score.value
      localStorage.setItem('snakeHighScore', highScore.value.toString())
    }
    generateFood()
  } else {
    snake.pop()
  }
}

// 游戏循环
const gameStep = () => {
  update()
  draw()
}

// 开始游戏
const startGame = () => {
  if (gameLoop) {
    clearInterval(gameLoop)
  }
  initGame()
  gameStarted.value = true
  gameLoop = window.setInterval(gameStep, 150)
}

// 结束游戏
const endGame = () => {
  gameOver.value = true
  if (gameLoop) {
    clearInterval(gameLoop)
    gameLoop = null
  }
}

// 键盘控制
const handleKeydown = (e: KeyboardEvent) => {
  if (!gameStarted.value) return
  
  const key = e.key.toLowerCase()
  
  if ((key === 'arrowup' || key === 'w') && direction.y !== 1) {
    nextDirection = { x: 0, y: -1 }
  } else if ((key === 'arrowdown' || key === 's') && direction.y !== -1) {
    nextDirection = { x: 0, y: 1 }
  } else if ((key === 'arrowleft' || key === 'a') && direction.x !== 1) {
    nextDirection = { x: -1, y: 0 }
  } else if ((key === 'arrowright' || key === 'd') && direction.x !== -1) {
    nextDirection = { x: 1, y: 0 }
  }
}

onMounted(() => {
  if (canvasRef.value) {
    ctx = canvasRef.value.getContext('2d')
    draw()
  }
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (gameLoop) {
    clearInterval(gameLoop)
  }
})
</script>

<template>
  <div class="snake-game">
    <!-- 切换按钮 -->
    <div class="mode-switch">
      <button
        class="switch-btn"
        :class="{ active: mode === 'login' }"
        @click="mode = 'login'"
      >
        登录
      </button>
      <button
        class="switch-btn"
        :class="{ active: mode === 'register' }"
        @click="mode = 'register'"
      >
        注册
      </button>
    </div>
    
    <div class="game-header">
      <div class="score-board">
        <div class="score-item">
          <span class="label">分数</span>
          <span class="value">{{ score }}</span>
        </div>
        <div class="score-item">
          <span class="label">最高分</span>
          <span class="value">{{ highScore }}</span>
        </div>
      </div>
    </div>
    
    <div class="game-container">
      <canvas
        ref="canvasRef"
        :width="canvasSize"
        :height="canvasSize"
        class="game-canvas"
      ></canvas>
      
      <div v-if="!gameStarted" class="game-overlay">
        <div class="overlay-content">
          <h2>🐍 贪吃蛇</h2>
          <p>使用方向键或 WASD 控制蛇的移动</p>
          <button class="start-btn" @click="startGame">开始游戏</button>
        </div>
      </div>
      
      <div v-if="gameOver" class="game-overlay">
        <div class="overlay-content">
          <h2>游戏结束!</h2>
          <p>得分: {{ score }}</p>
          <p v-if="score >= highScore && score > 0" class="new-record">🎉 新纪录!</p>
          <button class="start-btn" @click="startGame">重新开始</button>
        </div>
      </div>
    </div>
    
    <div class="game-controls">
      <p>控制: ↑ ↓ ← → 或 W A S D</p>
    </div>
  </div>
</template>

<style scoped>
.snake-game {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.mode-switch {
  display: flex;
  gap: 8px;
  background: rgba(0, 0, 0, 0.3);
  padding: 4px;
  border-radius: 30px;
}

.switch-btn {
  padding: 8px 24px;
  font-size: 14px;
  font-weight: 500;
  color: #888;
  background: transparent;
  border: none;
  border-radius: 26px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.switch-btn.active {
  color: #1a1a2e;
  background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
  box-shadow: 0 2px 10px rgba(0, 255, 136, 0.3);
}

.switch-btn:hover:not(.active) {
  color: #00ff88;
}

.game-header {
  width: 100%;
}

.score-board {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.score-item .label {
  font-size: 14px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.score-item .value {
  font-size: 28px;
  font-weight: bold;
  color: #00ff88;
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
}

.game-container {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
}

.game-canvas {
  display: block;
  border-radius: 8px;
}

.game-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.overlay-content {
  text-align: center;
  color: #fff;
}

.overlay-content h2 {
  font-size: 32px;
  margin-bottom: 16px;
  color: #00ff88;
  text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
}

.overlay-content p {
  font-size: 16px;
  color: #aaa;
  margin-bottom: 8px;
}

.new-record {
  color: #ffd700 !important;
  font-weight: bold;
  animation: pulse 0.5s ease-in-out infinite alternate;
}

@keyframes pulse {
  from { transform: scale(1); }
  to { transform: scale(1.1); }
}

.start-btn {
  margin-top: 20px;
  padding: 12px 32px;
  font-size: 18px;
  font-weight: bold;
  color: #1a1a2e;
  background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
  border: none;
  border-radius: 30px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 255, 136, 0.4);
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 255, 136, 0.6);
}

.start-btn:active {
  transform: translateY(0);
}

.game-controls {
  color: #666;
  font-size: 14px;
}
</style>
