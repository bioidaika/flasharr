<script lang="ts">
  import { onMount } from "svelte";
  import { MediaShelf, MediaCard } from "@media-set/core-ui";
  import {
    fetchHistory,
    fetchAllSeries,
    fetchAllMovies,
    getSeriesPoster,
    getMoviePoster,
    type SonarrSeries,
    type RadarrMovie,
  } from "$lib/stores/arr";

  let items = $state<any[]>([]);
  let loading = $state(true);

  onMount(async () => {
    try {
      const [history, series, movies] = await Promise.all([
        fetchHistory(50),
        fetchAllSeries(),
        fetchAllMovies(),
      ]);

      if (!history?.records) {
        loading = false;
        return;
      }

      // Filter for imports
      const imports = history.records.filter(
        (r: any) => r.eventType === "downloadFolderImported",
      );

      const mapped: any[] = [];
      const seenIds = new Set<string>();

      for (const record of imports) {
        let item: any | null = null;

        if (record.seriesId) {
          if (seenIds.has(`tv-${record.seriesId}`)) continue;

          const s = series.find((s: SonarrSeries) => s.id === record.seriesId);
          if (s && s.tmdbId) {
            item = {
              tmdbId: s.tmdbId,
              type: "tv",
              title: s.title,
              poster: getSeriesPoster(s),
              year: s.year,
              status: "available",
            };
            seenIds.add(`tv-${s.id}`);
          }
        } else if (record.movieId) {
          if (seenIds.has(`movie-${record.movieId}`)) continue;

          const m = movies.find((m: RadarrMovie) => m.id === record.movieId);
          if (m && m.tmdbId) {
            item = {
              tmdbId: m.tmdbId,
              type: "movie",
              title: m.title,
              poster: getMoviePoster(m),
              year: m.year,
              status: "available",
            };
            seenIds.add(`movie-${m.id}`);
          }
        }

        if (item) mapped.push(item);
        if (mapped.length >= 12) break;
      }

      items = mapped;
    } catch (e) {
      console.error("Failed to load Just Added:", e);
    } finally {
      loading = false;
    }
  });
</script>

{#if !loading && items.length > 0}
  <MediaShelf
    title="Just Added"
    {items}
    keyExtractor={(item) => String(item.tmdbId)}
  >
    {#snippet card(item, index, isHovered)}
      <MediaCard
        title={item.title}
        imgUrl={item.poster || ''}
        year={item.year?.toString() || ''}
        tag={item.type.toUpperCase()}
        href="/{item.type === 'tv' ? 'tv' : 'movie'}/{item.tmdbId}"
        badgeText={item.status === 'available' ? 'Available' : ''}
        badgeVariant={item.status === 'available' ? 'success' : 'default'}
        {isHovered}
      />
    {/snippet}
  </MediaShelf>
{/if}
