<script>
  import {calcLinks, siteConfig} from '$lib/nav';
</script>

<svelte:head>
  <title>{siteConfig.title}</title>
  <meta name={siteConfig.description} content={siteConfig.description} />
</svelte:head>

<div id="calc" class='flex flex-col justify-center items-center space-y-4 my-4 w-full'>
  <div class='flex flex-col justify-center items-center space-y-2 w-1/2'>
    <article class='prose text-center mb-4'>Welcome to <h1>Hardo's Engineering Calculator Collection</h1></article>
    {#each calcLinks as calcLink (calcLink.id)}
      <a href={calcLink.href} class="btn">{calcLink.label}</a>
    {/each}
  </div>
</div>