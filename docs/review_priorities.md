# Follow-up Recommendations

The following items are prioritized suggestions based on the latest review. They outline work that should be considered, but no code has been changed yet.

1. **Sanitize uploaded filenames.** Ensure user-provided filenames are normalized (e.g., `Path(name).name`) before writing them to the uploads directory to avoid directory traversal and accidental overwrites.
2. **Validate compression request paths.** Confirm that filenames used for compression resolve inside the uploads directory so crafted `..` segments cannot touch arbitrary files on disk.
3. **Handle ffprobe failures gracefully.** Wrap ffprobe execution with error handling that logs context, enforces timeouts, and cleans up partially written uploads if probing fails.
4. **Align history download naming.** Update the history fallback logic to recognize task-suffixed output files so users can download completed artifacts from their job history.
5. **Limit queue polling overhead.** Reduce repeated `AsyncResult` lookups during queue status checks to avoid excessive broker round-trips under heavy load.
6. **Prevent duplicate scheduler startups.** Ensure the cleanup scheduler is initialized exactly once during application startup to avoid running multiple background jobs simultaneously.
7. **Warm system capability caches.** Await the capability probe during startup so later requests can reuse the cached value without redundant probes.
8. **Consolidate exception types.** Introduce a purpose-built exception for ffprobe failures so API and worker code can differentiate probe issues from other runtime errors.
9. **Document cleanup behavior.** Clarify in developer docs how temporary uploads are pruned and what operators should expect from the scheduled cleanup task.
10. **Add automated tests.** Cover filename validation and ffprobe failure handling with unit tests to prevent regressions once the changes above are implemented.
11. **Avoid blocking Celery calls on the event loop.** `_get_hw_info_cached()` and `_get_hw_info_fresh()` call `AsyncResult.get()` directly inside FastAPI handlers, which blocks the asyncio loop until the worker responds. Offload these calls to a thread executor or refactor the worker API to return results via Redis.
12. **Run ffprobe outside the main event loop.** The `/api/upload` handler invokes `_ffprobe()` synchronously, so a slow or hung process stalls every concurrent request. Use `asyncio.to_thread()` or similar to move the subprocess call off the loop in addition to adding timeouts.
13. **Strengthen startup codec sync.** `_sync_codec_settings_from_tests()` polls hardware info by repeatedly calling the blocking `_get_hw_info_fresh()`, which can monopolize the event loop during startup. Fetch hardware info in a background thread or precompute it before scheduling the async task.
14. **Add Redis failure handling for queue publications.** `_publish()` in the worker assumes Redis is reachable; connection drops raise and abort the entire task. Wrap publishes in try/except and degrade gracefully so encoding can finish even if progress updates fail.
15. **Validate numeric inputs.** Enforce lower bounds for `target_size_mb`, `audio_bitrate_kbps`, and retention hours at the API layer to catch negative values early instead of relying on downstream logic.
16. **Harden download fallbacks.** When `/api/jobs/{task_id}/download` rebuilds filenames, it should verify that any reconstructed path resides beneath `/app/outputs` to avoid accidentally serving files outside the intended directory if metadata is tampered with.
17. **Paginate history responses.** `history_manager.get_history()` returns the entire list and the API layers expose it directly; for long-running instances this can grow large and slow down dashboard loads. Add pagination and bounds to keep responses lightweight.
18. **Normalize logging volume.** The SSE stream logs each Redis message and heartbeat at info level, which can flood logs under load. Downgrade repetitive logs or guard them behind a debug flag to improve signal-to-noise.
19. **Surface cleanup errors.** The cleanup scheduler currently swallows `os.remove` failures. Capture and log exceptions (with the offending path) so operators can detect permission issues or stubborn files.
20. **Document GPU environment requirements.** Codify the NVIDIA/Intel environment expectations (e.g., required containers vars) in operator docs so deployments reproduce the worker assumptions without trial and error.
