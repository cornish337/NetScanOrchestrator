<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { getChunkDetails, getResult } from '$lib/api';
  import { goto } from '$app/navigation';

  let chunkId: string;
  let chunkDetails: any = null;
  let selectedHost: any = null;
  let selectedResult: any = null;
  let loading = true;
  let error = '';

  onMount(async () => {
    chunkId = $page.params.id;
    if (!chunkId) {
      error = 'No chunk ID provided.';
      loading = false;
      return;
    }
    try {
      chunkDetails = await getChunkDetails(chunkId);
    } catch (e: any) {
      error = e.message || 'Failed to load chunk details.';
    } finally {
      loading = false;
    }
  });

  async function viewHost(host: any) {
    if (!host.has_result) {
      selectedHost = host;
      selectedResult = { status: { state: 'down' } }; // Or some other indicator
      return;
    }
    try {
      selectedHost = host;
      selectedResult = await getResult(chunkId, host.ip);
    } catch (e: any) {
      error = e.message || `Failed to load result for ${host.ip}`;
      selectedResult = null;
    }
  }
</script>

<svelte:head>
  <title>Chunk Details - {chunkId}</title>
</svelte:head>

<section class="p-4 md:p-6 space-y-4">
  <div class="flex items-center gap-4">
    <button on:click={() => goto('/')} class="px-3 py-1 border rounded hover:bg-gray-100">&larr; Back</button>
    <h1 class="text-xl font-semibold">Chunk Details</h1>
  </div>

  {#if loading}
    <p>Loading chunk details...</p>
  {:else if error}
    <div class="text-red-600 bg-red-100 p-3 rounded">{error}</div>
  {:else if chunkDetails}
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Host List -->
      <div class="md:col-span-1 border rounded-lg overflow-hidden bg-white">
        <h2 class="text-lg font-medium p-3 bg-gray-50 border-b">Hosts in Chunk <span class="font-mono text-sm bg-gray-200 px-1 rounded">{chunkId}</span></h2>
        <ul class="divide-y max-h-[70vh] overflow-y-auto">
          {#each chunkDetails.targets as host (host.ip)}
            <li>
              <button on:click={() => viewHost(host)} class="w-full text-left p-3 hover:bg-blue-50 focus:outline-none focus:bg-blue-100" class:bg-blue-100={selectedHost?.ip === host.ip}>
                <div class="flex justify-between items-center">
                  <span class="font-mono">{host.ip}</span>
                  {#if host.has_result}
                    <span class="text-xs px-2 py-1 rounded-full bg-green-200 text-green-800">scanned</span>
                  {:else}
                     <span class="text-xs px-2 py-1 rounded-full bg-gray-200 text-gray-600">no data</span>
                  {/if}
                </div>
              </button>
            </li>
          {/each}
        </ul>
      </div>

      <!-- Result Details -->
      <div class="md:col-span-2">
        {#if selectedHost}
          <div class="border rounded-lg bg-white p-4">
             <h2 class="text-lg font-medium mb-3">Scan Result for <span class="font-mono text-indigo-600">{selectedHost.ip}</span></h2>
             {#if selectedResult}
                {#if selectedResult.error}
                    <div class="text-red-500">Error: {selectedResult.error} {selectedResult.details || ''}</div>
                {:else}
                    <div class="space-y-4">
                        <div>
                            <h3 class="font-semibold">Status</h3>
                            <p class="text-sm">State: <span class="font-medium">{selectedResult.status?.state || 'N/A'}</span></p>
                            <p class="text-sm">Reason: <span class="font-medium">{selectedResult.status?.reason || 'N/A'}</span></p>
                        </div>
                        {#if selectedResult.hostnames && selectedResult.hostnames.length > 0}
                        <div>
                            <h3 class="font-semibold">Hostnames</h3>
                            <ul class="list-disc list-inside text-sm">
                                {#each selectedResult.hostnames as hn}
                                    <li>{hn.name} ({hn.type})</li>
                                {/each}
                            </ul>
                        </div>
                        {/if}
                        {#if selectedResult.ports && selectedResult.ports.length > 0}
                        <div>
                            <h3 class="font-semibold">Open Ports</h3>
                            <div class="overflow-x-auto">
                                <table class="min-w-full text-sm mt-2 border">
                                    <thead class="bg-gray-100">
                                        <tr>
                                            <th class="text-left p-2">Port</th>
                                            <th class="text-left p-2">State</th>
                                            <th class="text-left p-2">Service</th>
                                            <th class="text-left p-2">Product/Version</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                    {#each selectedResult.ports as port}
                                        <tr class="border-t">
                                            <td class="p-2">{port.portid}/{port.protocol}</td>
                                            <td class="p-2">{port.state}</td>
                                            <td class="p-2">{port.service || ''}</td>
                                            <td class="p-2">{port.product || ''} {port.version || ''}</td>
                                        </tr>
                                    {/each}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        {/if}
                    </div>
                {/if}
             {:else if !selectedHost.has_result}
                <p class="text-gray-600">Host was not responsive or no scan data was returned.</p>
             {:else}
                <p class="text-gray-600">Loading result...</p>
             {/if}
          </div>
        {:else}
          <div class="flex items-center justify-center h-full border-2 border-dashed rounded-lg text-gray-500">
            <p>Select a host from the list to view its scan details.</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</section>
