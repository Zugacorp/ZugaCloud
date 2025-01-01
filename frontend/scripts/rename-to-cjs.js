import { rename } from 'fs/promises'
import { join } from 'path'
import { fileURLToPath } from 'url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

async function renameFiles() {
  const electronDir = join(__dirname, '..', 'dist-electron')
  
  try {
    await rename(join(electronDir, 'main.js'), join(electronDir, 'main.cjs'))
    await rename(join(electronDir, 'preload.js'), join(electronDir, 'preload.cjs'))
    console.log('Successfully renamed files to .cjs')
  } catch (error) {
    console.error('Error renaming files:', error)
    process.exit(1)
  }
}

renameFiles() 