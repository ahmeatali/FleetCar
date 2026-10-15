# Production deployment — 15 October 2026

Status: deployed to https://fleetrent.com.tr through the existing DigitalOcean Chrome web console.

- Server: 188.166.68.240, existing `/opt/fleetcar` installation.
- Release: `20261015T084458Z`.
- Archive SHA-256: `df3df83903b1fb5dc695c6743709b1c3b3600c5953379b4145eb78d2ffafda80`.
- Recovery files on the server: `/opt/fleetcar-backups/20261015T084458Z` (private; database, original code, frontend assets/source, uploads and configuration).
- Live release manifest: `/opt/fleetcar/release-manifest.json`.

The release includes the current working tree, including uncommitted feature and refactoring files. No GitHub push was performed. Future deployment must use the reviewed release source; the historical `update.sh` pulls `main` and is not a reliable reproduction of this release.

## Checks completed

- 85 backend tests and 27 frontend tests; lint, format and production build passed locally.
- Migration rehearsed against a separate SQLite copy on the production host; all 47 model tables/columns and SQLite integrity/foreign keys checked.
- New backend booted as `www-data` on an isolated localhost port; 124 API paths registered. Unauthenticated API and private upload access denied.
- Production code and all 144 manifest files verified by SHA-256; live HTML and initial JavaScript/CSS assets matched the built release.
- Live HTTPS requests and Chrome supplier/service login screens passed without JavaScript or HTTP 5xx errors. Authentication inside existing accounts was not tested because credentials were not supplied.
- Backend and Nginx active; staging server stopped. Existing core table counts and uploaded file contents preserved. No local database, test fixture, secret environment file or sample data was deployed.

ReportLab 4.5.1 installed; existing DejaVu Unicode font verified. HTTPS upload session cookies configured with `FLEETCAR_COOKIE_SECURE=true`. Existing `/uploads/` backend proxy retained; Nginx request limit increased from 10M to 16M for signed PDF uploads.

The first cutover rolled back automatically when copied source ownership prevented the service user from importing it. File ownership was corrected, then the deployment and all checks succeeded. Existing production records were preserved; no production data cleanup was performed in this deployment.

Existing sessions may require users to log in again. Arvento and other external providers still require their real provider configuration; deployment does not activate unconfigured integrations.

No SSH access key was added. The proposed temporary key step was rejected by automatic approval review, and the archive was transferred over the already authorized web console instead.
