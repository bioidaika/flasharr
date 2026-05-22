//! Discovery Service
//!
//! Orchestrates media acquisition: Search -> Decision -> Library -> Download.
//! This service centralizes the "Smart Grab" logic previously split between frontend and backend.

use std::sync::Arc;
use std::collections::HashSet;
use serde_json::{Value, json};
use tracing::{info, warn};
use crate::services::TmdbService;
use crate::downloader::DownloadOrchestrator;
use crate::db::Db;
use crate::utils::smart_tokenizer::smart_parse;
use crate::utils::title_matcher::{get_title_keywords, is_different_franchise_entry, calculate_unified_similarity};

pub struct DiscoveryService {
    db: Arc<Db>,
    orchestrator: Arc<DownloadOrchestrator>,
    tmdb_service: Arc<TmdbService>,
    http_client: Arc<reqwest::Client>,
}

impl DiscoveryService {
    pub fn new(
        db: Arc<Db>,
        orchestrator: Arc<DownloadOrchestrator>,
        tmdb_service: Arc<TmdbService>,
        http_client: Arc<reqwest::Client>,
    ) -> Self {
        Self {
            db,
            orchestrator,
            tmdb_service,
            http_client,
        }
    }

    /// Atomic Smart Grab
    /// 1. Adds series/movie to Sonarr/Radarr (if not already present).
    /// 2. Performs a smart search across indexers.
    /// 3. Selects the best candidate based on quality/score.
    /// 4. Initiates download.
    pub async fn smart_grab(
        &self,
        tmdb_id: i64,
        media_type: &str,
        title: &str,
        year: Option<String>,
    ) -> Result<Value, String> {
        info!("Starting Atomic Smart Grab for {} (TMDB: {})", title, tmdb_id);

        // 1. Ensure in Library (Arr Suite) — best-effort, non-fatal
        let arr_id = if let Some(arr_client) = self.orchestrator.get_arr_client().await {
            let result: anyhow::Result<i32> = if media_type == "tv" {
                arr_client.add_series_by_tmdb(tmdb_id, 1, "").await
            } else {
                arr_client.add_movie_by_tmdb(tmdb_id, 1, "").await
            };
            match result {
                Ok(id) => Some(id),
                Err(e) => {
                    let msg = e.to_string();
                    if msg.contains("exists") || msg.contains("already") {
                        info!("Item already in arr library");
                    } else {
                        warn!("Failed to add item to arr: {}", msg);
                    }
                    None
                }
            }
        } else {
            warn!("Arr client not configured, skipping library add");
            None
        };

        // 2. Perform Smart Search
        let search_results = self.perform_internal_search(title, year, media_type, Some(tmdb_id)).await?;

        if search_results.is_empty() {
            return Err("No results found for smart grab".to_string());
        }

        // 3. Decision Logic (Quick Grab - Highest Score)
        let best_candidate = search_results.first().ok_or("No valid candidates found")?;
        info!("Selected best candidate: {} (Score: {})", best_candidate.original_name, best_candidate.score);

        // 4. Initiate Download via orchestrator
        match self.orchestrator.add_download_with_metadata(
            best_candidate.url.clone(),
            Some(best_candidate.original_name.clone()),
            "fshare".to_string(),
            "media".to_string(),
            None,
            None,
            None,
        ).await {
            Ok(_task) => {
                info!("Smart Grab successful for {}", title);
                Ok(json!({
                    "success": true,
                    "message": format!("Grab queued: {}", best_candidate.original_name),
                    "grabbed": {
                        "name": best_candidate.original_name,
                        "score": best_candidate.score,
                        "size": best_candidate.size,
                    },
                    "arr_id": arr_id
                }))
            }
            Err(e) => Err(format!("Failed to initiate download: {}", e))
        }
    }

    /// Internal helper to perform search logic similar to api/discovery.rs
    async fn perform_internal_search(
        &self,
        title: &str,
        year: Option<String>,
        _media_type: &str,
        tmdb_id: Option<i64>,
    ) -> Result<Vec<InternalSearchResult>, String> {
        let mut queries = vec![title.to_string()];
        
        // Resolve Aliases
        if let Some(tid) = tmdb_id {
            let aliases = self.tmdb_service.get_movie_alternative_titles(tid).await;
            for alias in aliases.iter().take(2) {
                queries.push(alias.title.clone());
            }
        }

        if let Some(ref y) = year {
            let base = queries.clone();
            for q in base {
                queries.push(format!("{} {}", q, y));
            }
        }

        let mut all_results = Vec::new();
        let search_keywords = get_title_keywords(title);

        for query in queries {
            let url = format!(
                "https://timfshare.com/api/v1/string-query-search?query={}",
                urlencoding::encode(&query)
            );
            
            if let Ok(resp) = self.http_client.post(&url).header("Content-Length", "0").send().await {
                if let Ok(data) = resp.json::<Value>().await {
                    if let Some(items) = data["data"].as_array() {
                        for item in items {
                            let name = item["name"].as_str().unwrap_or("").to_string();
                            let url = item["url"].as_str().unwrap_or("").to_string();

                            // Scoring & Filtering
                            let sim_res = calculate_unified_similarity(title, &name, &[]);
                            if !sim_res.is_valid && search_keywords.len() > 1 { continue; }
                            if is_different_franchise_entry(title, &name) { continue; }

                            let parsed = smart_parse(&name);

                            // Score = relevance (title similarity) + quality (source/resolution/HDR/audio/etc.)
                            // similarity acts as a gate (filtered above) and minor tiebreaker;
                            // total_score() from the smart tokenizer dominates ranking so the
                            // best-quality file wins among equally-relevant results.
                            let relevance = (sim_res.score * 50.0) as i32; // 0-50 range
                            let quality = parsed.total_score();             // 10-355 range
                            let score = relevance + quality;

                            all_results.push(InternalSearchResult {
                                original_name: name,
                                url,
                                size: item["size"].as_u64().unwrap_or(0),
                                score,
                            });
                        }
                    }
                }
            }
        }

        all_results.sort_by(|a, b| b.score.cmp(&a.score));
        // Remove duplicates by URL (dedup_by only works on consecutive elements;
        // use a HashSet over the sorted list to correctly remove all URL dupes)
        let mut seen_urls = HashSet::new();
        all_results.retain(|r| seen_urls.insert(r.url.clone()));

        Ok(all_results)
    }
}

#[derive(Debug, Clone)]
struct InternalSearchResult {
    pub original_name: String,
    pub url: String,
    pub size: u64,
    pub score: i32,
}
