<script lang="ts">
	import '../app.css';

	let { children } = $props();
</script>

<div class="navbar bg-base-100 shadow-sm">
  <div class="flex-1">
    <a class="btn btn-ghost text-xl" href="/">Hardo's Calc</a>
  </div>
  <div class="flex-none">
    <ul class="menu menu-horizontal px-1">
      <li><a href='/'>About Me</a></li>
      <li>
        <details>
          <summary>Calcs</summary>
          <ul class="bg-base-100 rounded-t-none p-2">
            <li><a href='/'>Lag Time</a></li>
            <li><a href='/'>Pressure Drop</a></li>
          </ul>
        </details>
      </li>
    </ul>
  </div>
</div>

{@render children()}
