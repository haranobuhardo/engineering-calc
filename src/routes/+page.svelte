<script>
	import { calcLinks, siteConfig } from '$lib/nav';
	import { Grid, Row, Column, ClickableTile } from 'carbon-components-svelte';
</script>

<svelte:head>
	<title>{siteConfig.title}</title>
	<meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<Grid>
	<Row>
		<Column>
			<h1 class="landing-page__heading">Welcome to Hardo's Engineering Calculator Collection</h1>
			<p class="landing-page__subheading mb-8">Select a calculator to get started:</p>
		</Column>
	</Row>
	<Row>
		{#each calcLinks as calcLink (calcLink.id)}
			<Column sm={4} md={4} lg={4} class="mb-4">
				<ClickableTile href={calcLink.href}>
					{calcLink.label}
				</ClickableTile>
			</Column>
		{/each}
	</Row>
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
	:global(.mb-8) {
		margin-bottom: 2rem;
	}
</style>
