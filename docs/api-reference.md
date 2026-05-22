# Flasharr API Reference

Complete reference for Flasharr's REST API, integration APIs (Newznab/SABnzbd), and WebSocket protocol.

## Base URL

```
http://<host>:8484/api
```

## Authentication

Flasharr uses a single API key for securing external integrations and protected endpoints.

- **Header**: `X-Api-Key: your-api-key`
- **Query Parameter**: `?apikey=your-api-key` (Used primarily for Indexer/SABnzbd compatibility)

*Note: The API key is configured in Settings and stored in the database.*

---

## Downloads API (`/api/downloads`)

Manage download tasks, batches, and queue priority.

### List Downloads

**GET** `/api/downloads`

Get all download tasks with pagination, sorting, and filtering.

**Query Parameters:**

- `status` (optional): Filter by `QUEUED`, `DOWNLOADING`, `PAUSED`, `COMPLETED`, `FAILED`.
- `page` (optional): Page number (1-indexed, default: 1).
- `limit` (optional): Items per page (default: 20, max: 100).
- `sort_by` (optional): Sort field (`added`, `status`, `filename`, `size`, `progress`).
- `sort_dir` (optional): Sort direction (`asc`, `desc`).

**Response:**

```json
{
  "downloads": [
    {
      "id": "uuid",
      "filename": "Breaking.Bad.S01E01.mkv",
      "state": "DOWNLOADING",
      "progress": 45.5,
      "speed": 5242880,
      "eta": 120,
      "size": 1152921504,
      "downloaded": 524288000,
      "category": "tv",
      "batch_id": "uuid",
      "batch_name": "Breaking Bad S01",
      "tmdb_title": "Breaking Bad",
      "tmdb_season": 1,
      "tmdb_episode": 1
    }
  ],
  "stats": { /* engine stats */ },
  "status_counts": { "QUEUED": 5, "DOWNLOADING": 1, ... },
  "total": 100,
  "page": 1,
  "total_pages": 5
}
```

### Add Download

**POST** `/api/downloads`

Add a new download task.

**Request Body:**

```json
{
  "url": "https://fshare.vn/file/...",
  "filename": "string (optional)",
  "category": "string (optional)",
  "batch_id": "uuid (optional)",
  "batch_name": "string (optional)",
  "tmdb": {
    "tmdb_id": 1396,
    "media_type": "tv",
    "title": "Breaking Bad",
    "season": 1,
    "episode": 1
  }
}
```

### Task Operations

- **GET** `/api/downloads/:id`: Get single task details.
- **POST** `/api/downloads/:id/pause`: Pause task.
- **POST** `/api/downloads/:id/resume`: Resume task.
- **POST** `/api/downloads/:id/retry`: Retry failed task.
- **POST** `/api/downloads/:id/redownload`: Re-download (delete local and restart).
- **DELETE** `/api/downloads/:id`: Delete task (and optionally files).

### Batch Operations

- **GET** `/api/downloads/batches`: List batch summaries with pagination.
- **GET** `/api/downloads/batch/:id/progress`: Get aggregated batch progress.
- **POST** `/api/downloads/batch/:id/pause`: Pause all tasks in batch.
- **POST** `/api/downloads/batch/:id/resume`: Resume all tasks in batch.
- **POST** `/api/downloads/batch/:id/redownload`: Re-download entire batch.
- **DELETE** `/api/downloads/batch/:id`: Delete entire batch.

---

## Indexer API (`/api/indexer`)

Flasharr acts as a **Newznab/Torznab** indexer for Sonarr/Radarr.

### Integration Details

- **URL**: `http://<host>:8484/api/indexer`
- **API Key**: Required via `apikey` parameter.
- **Supported Modes**: `caps`, `search`, `tvsearch`, `movie`.

### NZB Download Route

**GET** `/api/indexer/download`

Generates a "fake NZB" that encapsulates the Fshare URL and TMDB metadata for processing by the SABnzbd shim.

---

## SABnzbd API (`/sabnzbd/api`)

Flasharr acts as a **SABnzbd-compatible** download client.

### Integration Details

- **URL**: `http://<host>:8484/sabnzbd` (or `/sabnzbd/api`)
- **API Key**: Required via `apikey` parameter.
- **Flow**: Receives fake NZBs from the Indexer, extracts Fshare URLs, and starts real downloads.

### Supported Modes

- `addurl`: Add download via URL.
- `addfile`: Add download via NZB upload (multipart).
- `queue`: Get current queue status.
- `history`: Get completed/failed items (with path mapping for host-side access).
- `fullstatus`: Detailed engine status.

---

## Search & Discovery API

### Smart Search

- **POST** `/api/smart-search/movie`: Movie search with TMDB enrichment and scoring.
- **POST** `/api/smart-search/tv`: TV search (supports season/episode grouping).
- **POST** `/api/smart-search/multi`: Cross-media search.

### Discovery

- **GET** `/api/discovery/trending`: Trending movies/shows.
- **GET** `/api/discovery/popular`: Popular content.
- **GET** `/api/tmdb/movie/:id`: Get movie metadata.
- **GET** `/api/tmdb/tv/:id`: Get TV show metadata.

---

## System & Infrastructure API

- **GET** `/health`: Basic health check (`{"status":"ok"}`).
- **GET** `/api/stats`: Engine and system statistics (CPU, memory, active tasks).
- **GET** `/api/system/config`: Current application configuration.
- **GET** `/api/accounts`: Manage Fshare accounts and session status.
- **GET** `/api/folder-source`: Manage timFshare folder sources.

---

## WebSocket Protocol (`/api/ws`)

Flasharr uses WebSockets for real-time updates. See the dedicated [WebSocket Protocol](file:///Users/blavkbeav/Documents/Workspace/media-set/flasharr/docs/websocket-protocol.md) documentation for full details on message types and implementation.

**Endpoint:** `ws://<host>:8484/api/ws`

### Summary of Messages
- `SYNC_ALL`: Initial sync of active tasks (`DOWNLOADING`/`STARTING`).
- `TASK_BATCH_UPDATE`: High-frequency progress/state updates (500ms intervals).
- `ENGINE_STATS`: Global speed and status counts.
- `TASK_ADDED` / `TASK_REMOVED`: Membership changes.

---

## Error Codes

Errors are returned as JSON: `{"error": "message"}`.

- `401 Unauthorized`: Missing or invalid API key.
- `404 Not Found`: Task or resource missing.
- `409 Conflict`: Download URL already exists in queue.
- `500 Internal Server Error`: Backend exception or database failure.
