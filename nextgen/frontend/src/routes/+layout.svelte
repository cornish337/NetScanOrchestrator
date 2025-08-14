<script lang="ts">
  import '$/app.css';
  import { events } from '$lib/stores/events';
  let lastEvent: any = null;
  const unsub = events.subscribe((e) => { if (e) lastEvent = e; });
  $: eventType = lastEvent?.type;
</script>

<div class="min-h-screen flex flex-col">
  <header class="p-3 border-b flex items-center justify-between bg-gray-50">
    <h1 class="text-lg font-semibold">Nmap Parallel Scanner</h1>
    <small class="text-gray-600">{eventType ? `Last event: ${eventType}` : 'Connecting...'}</small>
  </header>
  <main class="flex-1 p-4">
    <slot />
  </main>
</div>
