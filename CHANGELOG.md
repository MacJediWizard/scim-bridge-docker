# Changelog

All notable changes to this project will be documented in this file.

---

## [v0.1.0] - 2025-04-27
### Added
- Initial project structure
- FastAPI SCIM server
- Mailcow mailbox creation integration
- Dockerfile for containerization
- Docker Compose configuration
- `.env.example` environment template
- Healthcheck endpoint

---

## [v0.1.1] - 2025-04-28
### Added
- Added full Portainer deployment instructions (`PORTAINER.md`)
- Added manual environment variable setup notes
- Improved documentation for Docker stack usage
- Updated health check endpoint to `/healthz`

---

## [v0.1.2] - 2025-04-28
### Added
- Added curl installation to Dockerfile for health check functionality
- Updated Dockerfile to install necessary dependencies
- Updated health check in container to ensure service is running correctly

---

## [v0.1.3] - 2025-04-28
### Updated
- Mailcow API integration to correctly create mailboxes
- SCIM User creation endpoint to handle mailbox creation with proper parameters
- User creation logic to match Mailcow API’s expected fields

---

## [v0.1.4] - 2025-04-28
### Added
- SCIM ServiceProviderConfig endpoint to provide integration metadata
- SCIM Groups endpoint for group creation (mock success response)

---

## [v0.1.5] - 2025-04-28
### Added
- SCIM GET `/Users` and `/Users/{id}` endpoints for full sync support
- SCIM GET `/Groups` endpoint returning an empty list for group sync

---

## [v0.1.6] - 2025-04-28
### Changed
- **SCIM POST /Users** now returns a full SCIM User resource (`id`, `userName`, `name`, `emails`, `externalId`) with HTTP 201 Created
- **SCIM POST /Groups** now returns a full SCIM Group resource (`id`, `displayName`, `members`) with HTTP 201 Created
- Provided valid `id` fields in create responses to eliminate 422 errors during Authentik sync

---

## [v0.1.7] - 2025-04-28
### Changed
- Re-added **GET /ServiceProviderConfig** so Authentik SCIM sync no longer 404s
- Implemented **PUT /Users/{id}** to support Authentik full-sync updates
- Implemented **PUT /Groups/{id}** and **PATCH /Groups/{id}** to support group updates and avoid 405/404 during sync
- Split request vs. response SCIM models so creation endpoints accept minimal payloads and return full SCIM resources

---

## [v0.1.8] - 2025-04-28
### Changed
- Split SCIMUser/SCIMGroup into Create vs Resource models
- `POST /Users` and `PUT /Users/{id}` now accept minimal payloads
- No-op `PUT`/`PATCH` on Groups to satisfy Authentik sync

---

## [v0.1.9] - 2025-04-28
### Changed
- Ensured mailbox provisioning on **PUT /Users/{id}** by calling Mailcow API
- Added error handling for Mailcow API failures during full-sync updates

---

## [v0.1.10] - 2025-04-28
### Changed
- POST & PUT /Users now accept minimal payloads and provision mailboxes
- Errors from Mailcow surfaced as HTTP 400

---

## [v0.1.11] - 2025-04-28
### Added
- `set_mailcow_custom_attr` helper for updating custom mailbox attributes
- Wired **PUT /Groups/{id}** and **PATCH /Groups/{id}** to call Mailcow’s `/edit/mailbox/custom-attribute` endpoint during group sync  