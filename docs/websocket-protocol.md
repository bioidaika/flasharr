# WebSocket Protocol

## Overview

Flasharr uses WebSocket for real-time updates between the backend and frontend. This ensures that download progress, state changes, and batch updates are reflected immediately in the UI without requiring manual refresh.

## Connection

- **Endpoint**: `ws://<host>:8484/api/ws` (or `wss://` for HTTPS)
- **Auto-reconnect**: Enabled with exponential backoff ($5000ms \times 1.5^n$)
- **Max reconnect attempts**: 10

## Message Types

### SYNC_ALL

Initial synchronization of active tasks.

**Direction**: Backend → Frontend  
**Frequency**: On initial connection  
**Note**: Only sends tasks in `DOWNLOADING` or `STARTING` states. Completed/Failed history must be loaded via REST API.

```json
{
  "type": "SYNC_ALL",
  "tasks": [
    /* array of active DownloadTask */
  ]
}
```

### TASK_ADDED

New download task created.

**Direction**: Backend → Frontend  
**Frequency**: Immediate

```json
{
  "type": "TASK_ADDED",
  "task": {
    /* DownloadTask object */
  }
}
```

### TASK_UPDATED

Download task state or progress changed (individual update).

**Direction**: Backend → Frontend  
**Frequency**: Immediate (used for specific state transitions)

```json
{
  "type": "TASK_UPDATED",
  "task": {
    /* Full DownloadTask object */
  }
}
```

### TASK_BATCH_UPDATE

Batch of task updates (primary update mechanism).

**Direction**: Backend → Frontend  
**Frequency**: Every 500ms (when active tasks exist)

```json
{
  "type": "TASK_BATCH_UPDATE",
  "tasks": [
    /* array of DownloadTask objects */
  ]
}
```

### TASK_REMOVED

Download task deleted.

**Direction**: Backend → Frontend  
**Frequency**: Immediate

```json
{
  "type": "TASK_REMOVED",
  "task_id": "uuid-string"
}
```

### ENGINE_STATS

Engine statistics and status counts.

**Direction**: Backend → Frontend  
**Frequency**: Every 2 seconds (only if values have changed)

```json
{
  "type": "ENGINE_STATS",
  "stats": {
    "active_downloads": 3,
    "queued": 5,
    "completed": 10,
    "failed": 1,
    "paused": 2,
    "cancelled": 0,
    "total_speed": 5242880,
    "db_counts": {
      "all": 100,
      "downloading": 3,
      "queued": 5,
      "paused": 2,
      "completed": 85,
      "failed": 5,
      "cancelled": 0
    }
  }
}
```

## Frontend Implementation

The frontend uses a WebSocket client (`websocket.ts`) that:

1. Automatically connects on page load (using `window.location.host`)
2. Registers message handlers in the `DownloadStore`
3. Updates Svelte runes (`$state`) in real-time
4. Handles reconnection with exponential backoff

### Batch Updates

When tasks are updated in the batch interval:

- Frontend updates individual items in the `downloads` Map
- If the task belongs to a batch, it patches the `batchItems` cache
- It recalculates live batch metrics (total speed, combined progress) immediately in the UI

## Performance Optimizations

1. **Batched Updates**: Progress and state updates are collected and sent every 500ms to reduce UI re-renders and network overhead.
2. **Task Filtering**: Only tasks that have actually changed since the last tick are included in the batch update.
3. **Lazy Stats**: Engine statistics are only broadcast if the values have actually changed.
4. **Selective Refetch**: Full server refetches (e.g. for batch summaries) are only triggered for terminal state changes (`COMPLETED`, `FAILED`).

## Troubleshooting

### Connection Issues

- Check backend is running on port 8484
- Verify WebSocket endpoint is accessible (check for `Upgrade: websocket` headers)
- Check browser console for `[WS]` logs (enabled by default)

### Missing Updates

- Verify WebSocket connection status in the UI indicator
- Check if the task is in an "Active" state (only active tasks are synced on connect)
- For historical tasks, ensure you are not filtered to "Active" only in the UI
