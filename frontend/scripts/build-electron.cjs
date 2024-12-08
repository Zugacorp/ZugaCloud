const { build } = require('esbuild');
const path = require('path');

build({
  entryPoints: [path.join(__dirname, '../electron/src/main.cjs')],
  bundle: true,
  platform: 'node',
  target: 'node14',
  outfile: path.join(__dirname, '../electron/dist/main.cjs'),
  external: ['electron']
}).catch(() => process.exit(1)); 