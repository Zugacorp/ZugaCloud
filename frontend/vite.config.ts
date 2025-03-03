import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { loadEnv } from 'vite';

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  // Load env file based on `mode` in the current directory.
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [
      react()
    ],
    
    base: './',
    
    // Development server config
    server: {
      port: 5001,
      strictPort: true,
      host: true,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },
    
    // Build config
    build: {
      outDir: 'dist',
      emptyOutDir: true,
      sourcemap: true,
      // Electron build settings
      target: 'chrome108',
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom'],
            'aws-vendor': ['@aws-sdk/client-s3', '@aws-sdk/client-cognito-identity'],
          }
        }
      },
      // Optimize dependencies
      commonjsOptions: {
        include: [/node_modules/],
        extensions: ['.js', '.cjs']
      }
    },
    
    // Path resolution
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    
    // Optimization settings
    optimizeDeps: {
      include: [
        'react', 
        'react-dom', 
        '@aws-sdk/client-s3',
        'amazon-cognito-identity-js'
      ],
      exclude: ['electron']
    },
    
    // Define global variables
    define: {
      global: 'globalThis',
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    },
    
    // Preview settings
    preview: {
      port: 5001,
      strictPort: true,
      host: true,
    }
  }
});

