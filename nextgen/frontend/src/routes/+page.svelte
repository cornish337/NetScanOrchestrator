<script lang="ts">
  import { onMount } from 'svelte';
  import { getCoverage, getChunks, killChunk, splitChunk, requeueChunk, updateSettings, importTargets, exportResults } from '$lib/api';
  import { events } from '$lib/stores/events';

  let coverage: any = { total: 0, completed: 0, failed: 0, pending: 0, killed: 0 };
  let chunks: any[] = [];
  let statusFilter = '';
  let maxWorkers = 4;
  let parts = 2;
  let loading = false;
  let exportLoading = false;
  let perHostWorkers = 8;
  let scanType = 'sT'; // sS if container has NET_RAW
  let ports = 'top-1000';
  let extraArgs = '';
  let error = '';

  // For new scan
  let targetsFile: FileList | null = null;
  let targetsText = '';
  let importError = '';
  let importLoading = false;

  async function handleExport() {
    exportLoading = true;
    try {
      await exportResults('json');
    } catch (e: any) {
      error = e.message || 'Failed to export results';
    } finally {
      exportLoading = false;
    }
  }

  async function handleImport() {
    importError = '';
    importLoading = true;
    let fileToUpload: File;

    if (targetsFile && targetsFile.length > 0) {
      fileToUpload = targetsFile[0];
    } else if (targetsText.trim()) {
      fileToUpload = new File([targetsText.trim()], "targets.txt", { type: "text/plain" });
    } else {
      importError = 'Please provide a file or paste targets.';
      importLoading = false;
      return;
    }

    try {
      await importTargets(fileToUpload);
      targetsFile = null;
      targetsText = '';
      // A refresh will be triggered by the chunk_created event via websocket
    } catch (e: any) {
      importError = e?.message || 'Failed to import targets';
    } finally {
      importLoading = false;
    }
  }

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
    <button class="px-3 py-1 border rounded bg-purple-600 text-white" on:click={handleExport} disabled={exportLoading}>
      {exportLoading ? 'Exporting...' : 'Download Report (JSON)'}
    </button>
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

<section class="mt-4 space-y-3 p-4 border rounded bg-gray-50">
  <h2 class="text-base font-semibold">Start New Scan</h2>
  {#if importError}<div class="text-red-600">{importError}</div>{/if}
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div>
      <label for="targets-file" class="block text-sm font-medium text-gray-700">Upload Targets File</label>
      <input id="targets-file" type="file" class="mt-1 block w-full text-sm" bind:files={targetsFile} accept=".txt,text/plain">
    </div>
    <div>
      <label for="targets-text" class="block text-sm font-medium text-gray-700">Or Paste Targets</label>
      <textarea id="targets-text" class="mt-1 block w-full border rounded-md p-2 h-24" placeholder="8.8.8.8&#10;scanme.nmap.org" bind:value={targetsText}></textarea>
    </div>
  </div>
  <div class="flex justify-end">
    <button class="px-4 py-2 border rounded bg-green-600 text-white" on:click={handleImport} disabled={importLoading}>
      {importLoading ? 'Importing...' : 'Import Targets & Start Scan'}
    </button>
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
          <tr class="border-t hover:bg-gray-50">
            <td class="p-2 max-w-[28rem] truncate">
              <a href="/chunk/{c.id}" class="text-blue-600 hover:underline" title="View chunk details">
                {c.id}
              </a>
            </td>
            <td class="p-2">{c.status}</td>
            <td class="p-2">{c.progress_completed}/{c.progress_total}</td>
            <td class="p-2">
              {#if c.started_at}
                {Math.floor(((c.completed_at || Date.now()/1000) - c.started_at))}
              {:else}0{/if}
            </td>
            <td class="p-2 space-x-2">
              {#if c.status === 'running' || c.status === 'queued'}
                <button class="px-2 py-1 border rounded bg-red-600 text-white" on:click|stopPropagation={() => doKill(c.id)}>Kill</button>
                <button class="px-2 py-1 border rounded bg-amber-600 text-white" on:click|stopPropagation={() => doSplit(c.id)}>Split</button>
              {/if}
              {#if c.status !== 'running'}
                <button class="px-2 py-1 border rounded bg-gray-200" on:click|stopPropagation={() => doRequeue(c.id)}>Requeue</button>
              {/if}
               <a href="/chunk/{c.id}" class="px-2 py-1 border rounded bg-gray-200" title="View Details">Details</a>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</section>
