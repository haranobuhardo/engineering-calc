import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit(),
		SvelteKitPWA({
			registerType: 'autoUpdate',
			includeAssets: ['favicon.svg'],
			manifest: {
				name: 'Engineering Calculator',
				short_name: 'EngCalc',
				description: 'Engineering calculations on the go',
				theme_color: '#ffffff',
				icons: [
					{
						src: 'pwa-icon.svg',
						sizes: 'any',
						type: 'image/svg+xml'
					}
				]
			},
			workbox: {
				// Cache all prerendered pages and static assets
				globPatterns: ['**/*.{js,css,html,svg,png,ico,woff,woff2}'],
				// Handle navigation requests offline
				navigateFallback: '/',
			}
		})
	]
});
