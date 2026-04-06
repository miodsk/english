import {defineConfig} from 'vite';
import {fileURLToPath, URL} from 'url';
import {Config} from '@en/config/index'
import dts from 'vite-plugin-dts'

export default defineConfig({
    plugins: [
        dts({
            outDir: 'dist',
            entryRoot: '.'
        })
    ],
    build: {
        minify: true,
        outDir: 'dist',
        emptyOutDir: true,
        sourcemap: false,
        lib: {
            entry: 'index.ts',
            name: 'tracker',
            fileName: 'tracker',
            formats: ['es', 'cjs', 'umd', 'iife']
        },
    },
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    server: {
        port: Config.ports.web,
        proxy: {
            '/api/v1': {
                target: `http://localhost:${Config.ports.server}`,
                changeOrigin: true,
            },

        },
    },
})