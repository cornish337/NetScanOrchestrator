<script lang="ts">
  import { onMount } from 'svelte';
  import { getCoverage, getChunks, killChunk, splitChunk, requeueChunk, updateSettings } from '$lib/api';
  import { events } from '$lib/stores/events';

  let coverage: any = { total: 0, completed: 0, failed: 0, pending: 0, killed: 0 };
  let chunks: any[] = [];
  let statusFilter = '';
  let maxWorkers = 4;
  let parts = 2;
  let loading = false;
  let perHostWorkers = 8;
  let scanType = 'sT'; // sS if container has NET_RAW
  let ports = 'top-1000';
  let extraArgs = '';
  let error = '';

  async function refresh() {
    loading = true;
    try {
      coverage = await getCoverage();
      const res = await getChunks(statusFilter || undefined, 100, 0);
      chunks = res.items;
    } catch (e: any) {
      error = e?.message || 'Failed to fetch';
    } finally {
      loading = false;
    }
  }

  function handleEvent(e: any) {
    if (!e) return;
    const type = e.type;
    if (['chunk_started','chunk_progress','chunk_completed','chunk_killed','chunk_created','chunk_split','chunk_requeued','settings_updated'].includes(type)) {
      refresh();
    }
  }

  const unsub = events.subscribe(handleEvent);

  async function setWorkers() {
    try { await updateSettings({ max_workers: maxWorkers }); } finally {}
  }

  async function applyScanSettings() {
    await updateSettings({
      max_workers: maxWorkers,
      per_host_workers: perHostWorkers,
      scan_type: scanType,
      ports,
      extra_args: extraArgs
    });
  }

  async function doKill(id: string) { await killChunk(id); }
  async function doSplit(id: string) { await splitChunk(id, parts); }
  async function doRequeue(id: string) { await requeueChunk(id); }

  onMount(() => { refresh(); return () => unsub(); });
</script>

<section class="space-y-3">
  <h2 class="text-base font-semibold">Dashboard</h2>
  {#if error}<div class="text-red-600">{error}</div>{/if}
  <div class="flex flex-wrap gap-3 text-sm">
    <div class="px-3 py-2 bg-gray-100 rounded">Total: {coverage.total}</div>
    <div class="px-3 py-2 bg-green-100 rounded">Completed: {coverage.completed}</div>
    <div class="px-3 py-2 bg-red-100 rounded">Failed: {coverage.failed}</div>
    <div class="px-3 py-2 bg-yellow-100 rounded">Pending: {coverage.pending}</div>
    <div class="px-3 py-2 bg-orange-100 rounded">Killed: {coverage.killed}</div>
  </div>
  <div class="flex flex-wrap items-end gap-3">
    <label class="text-sm">Filter status
      <select class="ml-2 border rounded p-1" bind:value={statusFilter} on:change={refresh}>
        <option value=''>all</option>
        <option value='queued'>queued</option>
        <option value='running'>running</option>
        <option value='completed'>completed</option>
        <option value='failed'>failed</option>
        <option value='killed-slow'>killed-slow</option>
      </select>
    </label>
    <label class="text-sm">Max workers
      <input class="ml-2 border rounded p-1 w-20" type="number" min="1" bind:value={maxWorkers} />
      <button class="ml-2 px-3 py-1 border rounded bg-blue-600 text-white" on:click={setWorkers}>Apply</button>
    </label>
    <label class="text-sm">Split parts
      <input class="ml-2 border rounded p-1 w-20" type="number" min="2" bind:value={parts} />
    </label>
    <button class="px-3 py-1 border rounded" on:click={refresh} disabled={loading}>{loading ? 'Refreshing...' : 'Refresh'}</button>
  </div>
  <div class="flex flex-wrap items-end gap-3">
    <!-- existing controls -->
    <label class="text-sm">Per-host workers
      <input class="ml-2 border rounded p-1 w-20" type="number" min="1" bind:value={perHostWorkers} />
    </label>
    <label class="text-sm">Scan type
      <select class="ml-2 border rounded p-1" bind:value={scanType}>
        <option value="sT">-sT (TCP Connect)</option>
        <option value="sS">-sS (SYN, needs NET_RAW)</option>
      </select>
    </label>
    <label class="text-sm">Ports
      <input class="ml-2 border rounded p-1 w-48" placeholder="top-1000 or 1-1024,3389" bind:value={ports} />
    </label>
    <label class="text-sm">Extra args
      <input class="ml-2 border rounded p-1 w-64" placeholder="--min-rate 1000" bind:value={extraArgs} />
    </label>
    <button class="px-3 py-1 border rounded bg-indigo-600 text-white" on:click={applyScanSettings}>Apply scan settings</button>
  </div>
</section>

<section class="mt-4">
  <h2 class="text-base font-semibold mb-2">Chunks</h2>
  <div class="overflow-auto border rounded">
    <table class="min-w-full text-sm">
      <thead class="bg-gray-50">
        <tr>
          <th class="text-left p-2">Id</th>
          <th class="text-left p-2">Status</th>
          <th class="text-left p-2">Progress</th>
          <th class="text-left p-2">Elapsed(s)</th>
          <th class="text-left p-2">Actions</th>
        </tr>
      </thead>
      <tbody>
        {#each chunks as c}
          <tr class="border-t">
            <td class="p-2 max-w-[28rem] truncate">{c.id}</td>
            <td class="p-2">{c.status}</td>
            <td class="p-2">{c.progress_completed}/{c.progress_total}</td>
            <td class="p-2">
              {#if c.started_at}
                {Math.floor(((c.completed_at || Date.now()/1000) - c.started_at))}
              {:else}0{/if}
            </td>
            <td class="p-2 space-x-2">
              {#if c.status === 'running' || c.status === 'queued'}
                <button class="px-2 py-1 border rounded bg-red-600 text-white" on:click={() => doKill(c.id)}>Kill</button>
                <button class="px-2 py-1 border rounded bg-amber-600 text-white" on:click={() => doSplit(c.id)}>Split</button>
              {/if}
              {#if c.status !== 'running'}
                <button class="px-2 py-1 border rounded bg-gray-200" on:click={() => doRequeue(c.id)}>Requeue</button>
              {/if}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</section>
