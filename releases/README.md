# Release manifests

Each `vX.Y.Z.manifest` is a complete list of files installed below `/opt/xmr`
for that release. Every non-comment line contains a one-character change marker,
one space, and a repository-relative path.

- `*` means the file changed in that release.
- `.` means the file was unchanged in that release.

Both kinds of entries are installed. The marker is informational.
