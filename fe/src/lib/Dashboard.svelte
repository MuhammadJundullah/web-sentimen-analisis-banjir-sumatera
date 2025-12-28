<script lang="ts">
  import { onMount } from 'svelte';
  import { analysisHistory } from '../stores/analysisStore';
  import { apiClient, type FetchStatusResponse } from '../services/api';
  import AnalysisResult from './AnalysisResult.svelte';

  let tweetText = '';
  let apiUrl = '';
  let isLoading = false;
  let error = '';
  let uploadFile: File | null = null;
  let uploadMessage = '';
  let uploadError = '';
  let isUploading = false;
  let uploadSummary: { label: string; value: number }[] = [];
  let categorySummary: { label: string; value: number }[] = [];
  let fetchStatus: FetchStatusResponse | null = null;
  let fetchMessage = '';
  let fetchError = '';
  let isFetching = false;
  let tokenInput = '';
  let tokenMessage = '';
  let tokenError = '';
  let isSettingToken = false;

  async function handleAnalysis() {
    if (!tweetText.trim()) {
      error = 'Mohon masukkan teks tweet';
      return;
    }

    if (!apiUrl.trim()) {
      error = 'Mohon masukkan URL API Backend';
      return;
    }

    isLoading = true;
    error = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      const result = await apiClient.predict(tweetText);
      analysisHistory.addAnalysis(result);
      tweetText = '';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Terjadi kesalahan saat analisis';
    } finally {
      isLoading = false;
    }
  }

  async function handleUpload() {
    if (!apiUrl.trim()) {
      uploadError = 'Mohon masukkan URL API Backend';
      return;
    }

    if (!uploadFile) {
      uploadError = 'Mohon pilih file CSV';
      return;
    }

    isUploading = true;
    uploadError = '';
    uploadMessage = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      const result = await apiClient.uploadCsv(uploadFile);
      uploadMessage = `Analisis selesai: ${result.total} data diproses.`;
      uploadSummary = Object.entries(result.sentiment_percentages).map(([label, value]) => ({ label, value }));
      categorySummary = Object.entries(result.category_percentages).map(([label, value]) => ({ label, value }));
      uploadFile = null;
    } catch (err) {
      uploadError = err instanceof Error ? err.message : 'Gagal upload CSV';
    } finally {
      isUploading = false;
    }
  }

  async function handleFetchNow() {
    if (!apiUrl.trim()) {
      fetchError = 'Mohon masukkan URL API Backend';
      return;
    }

    isFetching = true;
    fetchError = '';
    fetchMessage = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      const result = await apiClient.fetchTweets();
      fetchMessage = `Fetch selesai: ${result.inserted}/${result.total} data tersimpan.`;
      fetchStatus = await apiClient.fetchStatus();
    } catch (err) {
      fetchError = err instanceof Error ? err.message : 'Gagal fetch tweet';
    } finally {
      isFetching = false;
    }
  }

  async function handleSetToken() {
    if (!apiUrl.trim()) {
      tokenError = 'Mohon masukkan URL API Backend';
      return;
    }

    if (!tokenInput.trim()) {
      tokenError = 'Mohon masukkan Bearer Token';
      return;
    }

    isSettingToken = true;
    tokenError = '';
    tokenMessage = '';

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      await apiClient.setToken(tokenInput.trim());
      tokenMessage = 'Token berhasil diperbarui.';
      tokenInput = '';
    } catch (err) {
      tokenError = err instanceof Error ? err.message : 'Gagal memperbarui token';
    } finally {
      isSettingToken = false;
    }
  }

  async function loadFetchStatus() {
    if (!apiUrl.trim()) {
      return;
    }

    try {
      apiClient.setBaseUrl(apiUrl.trim());
      fetchStatus = await apiClient.fetchStatus();
    } catch (err) {
      fetchError = err instanceof Error ? err.message : 'Gagal mengambil status fetch';
    }
  }

  function clearHistory() {
    analysisHistory.clearHistory();
  }

  function handleFileChange(event: Event) {
    const target = event.target as HTMLInputElement;
    uploadFile = target.files && target.files.length > 0 ? target.files[0] : null;
  }

  function formatStatusTime(value: string | null): string {
    if (!value) {
      return '-';
    }
    return new Date(value).toLocaleString('id-ID');
  }

  onMount(() => {
    loadFetchStatus();
    const interval = setInterval(loadFetchStatus, 30000);
    return () => clearInterval(interval);
  });
</script>

<div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 py-8 px-4">
  <div class="max-w-6xl mx-auto">
    <header class="text-center mb-8">
      <h1 class="text-4xl md:text-5xl font-bold text-gray-800 mb-3">
        Dashboard Monitoring Bencana
      </h1>
      <p class="text-gray-600 text-lg">
        Analisis sentimen dan kategori dari tweet terkait bencana
      </p>
    </header>

    <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8 mb-8 border border-gray-100">
      <div class="mb-6">
        <label for="apiUrl" class="block text-sm font-semibold text-gray-700 mb-2">
          URL API Backend
        </label>
        <input
          id="apiUrl"
          type="text"
          bind:value={apiUrl}
          placeholder="https://huggingface.co/spaces/username/projectname"
          class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
        />
      </div>

      <div class="mb-6">
        <label for="tweetInput" class="block text-sm font-semibold text-gray-700 mb-2">
          Masukkan Teks Tweet
        </label>
        <textarea
          id="tweetInput"
          bind:value={tweetText}
          placeholder="Contoh: Bantuan makanan belum sampai di posko pengungsian desa A."
          rows="5"
          class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all resize-none"
        />
      </div>

      {#if error}
        <div class="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
          <p class="font-medium">{error}</p>
        </div>
      {/if}

      <button
        on:click={handleAnalysis}
        disabled={isLoading}
        class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] disabled:transform-none disabled:cursor-not-allowed shadow-lg"
      >
        {#if isLoading}
          <span class="inline-flex items-center gap-2">
            <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Menganalisis...
          </span>
        {:else}
          Analisis Tweet
        {/if}
      </button>
    </div>

    <div class="grid gap-6 md:grid-cols-2 mb-8">
      <div class="bg-white rounded-2xl shadow-md p-6 border border-gray-100">
        <h3 class="text-xl font-bold text-gray-800 mb-4">Upload Data CSV</h3>
        <input
          type="file"
          accept=".csv"
          on:change={handleFileChange}
          class="w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />

        {#if uploadError}
          <div class="mt-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
            <p class="font-medium">{uploadError}</p>
          </div>
        {/if}

        {#if uploadMessage}
          <div class="mt-4 p-3 bg-green-50 border-l-4 border-green-500 text-green-700 rounded">
            <p class="font-medium">{uploadMessage}</p>
          </div>
        {/if}

        {#if uploadSummary.length > 0}
          <div class="mt-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">Distribusi Sentimen</h4>
            <div class="space-y-2 text-sm text-gray-600">
              {#each uploadSummary as item}
                <div class="flex justify-between">
                  <span>{item.label}</span>
                  <span class="font-semibold">{item.value.toFixed(1)}%</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        {#if categorySummary.length > 0}
          <div class="mt-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">Distribusi Kategori</h4>
            <div class="space-y-2 text-sm text-gray-600 max-h-48 overflow-y-auto pr-2">
              {#each categorySummary as item}
                <div class="flex justify-between">
                  <span>{item.label}</span>
                  <span class="font-semibold">{item.value.toFixed(1)}%</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <button
          on:click={handleUpload}
          disabled={isUploading}
          class="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 disabled:cursor-not-allowed"
        >
          {#if isUploading}
            Mengunggah...
          {:else}
            Upload CSV
          {/if}
        </button>
      </div>

      <div class="bg-white rounded-2xl shadow-md p-6 border border-gray-100">
        <h3 class="text-xl font-bold text-gray-800 mb-2">Fetch Tweet Periodik</h3>
        <p class="text-sm text-gray-600 mb-4">
          Sistem mengambil data setiap 2 jam (atau sesuai konfigurasi backend).
        </p>

        <div class="space-y-2 text-sm text-gray-700">
          <div class="flex justify-between">
            <span>Terakhir Fetch</span>
            <span class="font-semibold">{formatStatusTime(fetchStatus?.last_run ?? null)}</span>
          </div>
          <div class="flex justify-between">
            <span>Jumlah Data</span>
            <span class="font-semibold">{fetchStatus?.last_count ?? 0}</span>
          </div>
          <div class="flex justify-between">
            <span>Tersimpan</span>
            <span class="font-semibold">{fetchStatus?.last_inserted ?? 0}</span>
          </div>
        </div>

        {#if fetchStatus?.last_error}
          <div class="mt-4 p-3 bg-amber-50 border-l-4 border-amber-500 text-amber-700 rounded">
            <p class="font-medium">{fetchStatus.last_error}</p>
          </div>
        {/if}

        {#if fetchError}
          <div class="mt-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
            <p class="font-medium">{fetchError}</p>
          </div>
        {/if}

        {#if fetchMessage}
          <div class="mt-4 p-3 bg-green-50 border-l-4 border-green-500 text-green-700 rounded">
            <p class="font-medium">{fetchMessage}</p>
          </div>
        {/if}

        <button
          on:click={handleFetchNow}
          disabled={isFetching}
          class="mt-4 w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 disabled:cursor-not-allowed"
        >
          {#if isFetching}
            Mengambil...
          {:else}
            Fetch Sekarang
          {/if}
        </button>

        <div class="mt-6 border-t border-gray-200 pt-4">
          <h4 class="text-sm font-semibold text-gray-700 mb-2">Update Bearer Token</h4>
          <input
            type="password"
            bind:value={tokenInput}
            placeholder="Masukkan Twitter Bearer Token"
            class="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-sm"
          />

          {#if tokenError}
            <div class="mt-3 p-2 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
              <p class="font-medium text-sm">{tokenError}</p>
            </div>
          {/if}

          {#if tokenMessage}
            <div class="mt-3 p-2 bg-green-50 border-l-4 border-green-500 text-green-700 rounded">
              <p class="font-medium text-sm">{tokenMessage}</p>
            </div>
          {/if}

          <button
            on:click={handleSetToken}
            disabled={isSettingToken}
            class="mt-3 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2.5 px-4 rounded-lg transition-all duration-200 disabled:cursor-not-allowed text-sm"
          >
            {#if isSettingToken}
              Menyimpan...
            {:else}
              Simpan Token
            {/if}
          </button>
        </div>
      </div>
    </div>

    {#if $analysisHistory.length > 0}
      <div class="mb-6 flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-800">
          Riwayat Analisis ({$analysisHistory.length})
        </h2>
        <button
          on:click={clearHistory}
          class="px-4 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors font-medium"
        >
          Hapus Riwayat
        </button>
      </div>

      <div class="grid gap-6 md:grid-cols-2">
        {#each $analysisHistory as analysis (analysis.id)}
          <AnalysisResult {analysis} />
        {/each}
      </div>
    {:else}
      <div class="text-center py-12 bg-white rounded-2xl shadow-md border border-gray-100">
        <svg class="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-gray-500 text-lg">Belum ada analisis. Mulai dengan memasukkan teks tweet di atas.</p>
      </div>
    {/if}
  </div>
</div>
