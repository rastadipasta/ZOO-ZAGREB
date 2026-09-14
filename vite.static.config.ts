import react from '@vitejs/plugin-react';
import {defineConfig} from 'vite';
import {sites} from './build/sites-vite-plugin';
export default defineConfig({plugins:[react(),sites()],build:{outDir:'dist/client',emptyOutDir:true},server:{port:5173,strictPort:true}});
