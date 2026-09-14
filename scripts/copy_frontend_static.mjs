import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const src = join(root, 'frontend', 'dist')
const dest = join(root, 'backend', 'static')

if (!existsSync(join(src, 'index.html'))) {
  console.error('frontend/dist/index.html не найден. Сначала npm run build в frontend.')
  process.exit(1)
}

rmSync(dest, { recursive: true, force: true })
mkdirSync(dest, { recursive: true })
cpSync(src, dest, { recursive: true })
console.log(`Copied ${src} -> ${dest}`)
