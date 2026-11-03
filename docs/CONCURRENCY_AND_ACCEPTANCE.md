# Reliability and acceptance criteria

The loop now locks the **entire** read/execute/update/write transaction through a stable
`state.json.lock` file, using POSIX `flock` and refreshing state after lock acquisition.
The state file continues to use atomic replacement. The lock file must not be deleted
while any agent process runs. This supports cooperating processes using a local filesystem
with working POSIX advisory locks, **not** distributed agents/NFS/Windows. Migrate to
database transactions or a distributed coordinator for multi-host operation.

**Quality gating:** a deterministic offline response is a placeholder. Such a cycle can
still have a heuristic score for debugging, but it always has `passed=false`. Passing
the demo execution script does not demonstrate autonomous development or a production
release. Track provider, offline_fallback and passed separately.

The example Python code executor is NOT a hostile-code security sandbox.
Live provider quotas and network connectivity remain unverified.
