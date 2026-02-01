<script lang="ts">
	import '../app.css';
	import 'carbon-components-svelte/css/g10.css';
	import 'katex/dist/katex.min.css';
	import {
		Header,
		HeaderUtilities,
		HeaderGlobalAction,
		SideNav,
		SideNavItems,
		SideNavLink,
		Content,
		SkipToContent
	} from 'carbon-components-svelte';
	import { calcLinks } from '$lib/nav';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { pwaInfo } from 'virtual:pwa-info';

	let isSideNavOpen = $state(false);
	let { children } = $props();

	onMount(async () => {
		if (pwaInfo) {
			const { registerSW } = await import('virtual:pwa-register');
			registerSW({
				immediate: true,
				onRegistered(r) {
					console.log('SW Registered: ' + r);
				},
				onRegisterError(error) {
					console.log('SW registration error', error);
				}
			});
		}
	});
</script>

<svelte:head>
	{@html pwaInfo?.webManifest.linkTag}
</svelte:head>

<Header companyName="Hardo's" platformName="Calc" bind:isSideNavOpen>
	<svelte:fragment slot="skipToContent">
		<SkipToContent />
	</svelte:fragment>
</Header>

<SideNav bind:isOpen={isSideNavOpen}>
	<SideNavItems>
		<SideNavLink href="/" text="Home" isSelected={$page.url.pathname === '/'} />
		{#each calcLinks as calcLink (calcLink.id)}
			<SideNavLink
				href={calcLink.href}
				text={calcLink.label}
				isSelected={$page.url.pathname === calcLink.href}
			/>
		{/each}
	</SideNavItems>
</SideNav>

<Content>
	{@render children()}
</Content>
