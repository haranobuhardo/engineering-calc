// This tells SvelteKit to prerender all pages into static HTML at build time.
// Since all calculators are pure client-side logic (no server data needed),
// prerendering makes them available offline via the service worker cache.
export const prerender = true;
