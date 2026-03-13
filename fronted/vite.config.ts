import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import { Config } from '@en/config/index'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    tailwindcss(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  server: {
    port: Config.ports.web,
    proxy: {
      '/api/v1': {
        target: `http://localhost:${Config.ports.server}`,
        changeOrigin: true,
      },
      '/api/ai': {
        target: `http://127.0.0.1:${Config.ports.ai}`,
        changeOrigin: true,
        ws: true,
        rewrite(path) {
          return path.replace(/^\/api\/ai/, '/ai')
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
