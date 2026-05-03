<script lang="ts">
	import { calcGroups, calcLinks, siteConfig } from '$lib/nav';
	import { Grid, Row, Column, ClickableTile, Search } from 'carbon-components-svelte';

	let searchTerm = $state('');

	let searchResults = $derived.by(() => {
		if (!searchTerm.trim()) return null;
		const term = searchTerm.toLowerCase().trim();
		return calcLinks.filter((calc) => {
			const labelMatch = calc.label.toLowerCase().includes(term);
			const groupMatch = calcGroups.some((g) =>
				g.items.some((item) => item.id === calc.id) && g.label.toLowerCase().includes(term)
			);
			return labelMatch || groupMatch;
		});
	});
</script>

<svelte:head>
	<title>{siteConfig.title}</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Welcome to Hardo's Engineering Calculator Collection</h1>
			<p class="landing-page__subheading mb-4">Select a calculator to get started:</p>
		</Column>
	</Row>

	<!-- Search -->
	<Row class="mb-8">
		<Column sm={4} md={8} lg={8}>
			<Search
				bind:value={searchTerm}
				placeholder="Search calculators..."
				size="lg"
				labelText="Search"
			/>
		</Column>
	</Row>

	<!-- Search results (flat) -->
	{#if searchResults !== null}
		{#if searchResults.length > 0}
			<Row>
				{#each searchResults as calc (calc.id)}
					<Column sm={4} md={4} lg={4} class="mb-4">
						<ClickableTile href={calc.href}>
							{calc.label}
						</ClickableTile>
					</Column>
				{/each}
			</Row>
		{:else}
			<Row>
				<Column>
					<p class="no-results">No calculators found for "{searchTerm}"</p>
				</Column>
			</Row>
		{/if}

	<!-- Grouped layout (default) -->
	{:else}
		{#each calcGroups as group (group.id)}
			<Row class="mb-2">
				<Column>
					<h2 class="category-heading">{group.label}</h2>
				</Column>
			</Row>
			<Row class="mb-8">
				{#each group.items as calc (calc.id)}
					<Column sm={4} md={4} lg={4} class="mb-4">
						<ClickableTile href={calc.href}>
							{calc.label}
						</ClickableTile>
					</Column>
				{/each}
			</Row>
		{/each}
	{/if}
</Grid>

<style>
	:global(.landing-page__heading) {
		font-size: 2rem;
		font-weight: 400;
		margin-bottom: 1rem;
		margin-top: 2rem;
	}
	:global(.landing-page__subheading) {
		font-size: 1rem;
		font-weight: 300;
	}
	:global(.mb-4) {
		margin-bottom: 1rem;
	}
	:global(.mb-8) {
		margin-bottom: 2rem;
	}
	.category-heading {
		font-size: 1.25rem;
		font-weight: 500;
		color: #525252;
		margin-bottom: 0.5rem;
	}
	.no-results {
		font-size: 0.95rem;
		color: #525252;
		padding: 1rem 0;
	}
</style>
