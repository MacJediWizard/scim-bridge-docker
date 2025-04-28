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
- SCIM POST /Users now returns a full SCIM User resource with HTTP 201
- SCIM POST /Groups now returns a full SCIM Group resource with HTTP 201

---

## [v0.1.7] - 2025-04-28
### Changed
- Added SCIM PUT /Users/{id} to support Authentik full-sync updates
- Added SCIM PUT /Groups/{id} and PATCH /Groups/{id} to support group updates

---

## [v0.1.8] - 2025-04-28
### Changed
- Split SCIMUser/SCIMGroup into Create vs Resource models
- POST /Users and PUT /Users/{id} now accept minimal payloads

---

## [v0.1.9] - 2025-04-28
### Changed
- Ensured mailbox provisioning on PUT /Users/{id}
- Added error handling for Mailcow API failures

---

## [v0.1.10] - 2025-04-28
### Changed
- POST & PUT /Users accept minimal payloads and provision mailboxes
- Surfaced Mailcow errors as HTTP 400

---

## [v0.1.11] - 2025-04-28
### Changed
- Improved Mailcow custom-attribute handling

---

## [v0.1.12] - 2025-04-28
### Changed
- Automatically set `groups` custom-attribute on mailboxes for SCIM group ops
- Consolidated Mailcow custom-attribute update logic

---

## [v0.1.13] - 2025-04-28
### Changed
- Mailbox provisioning uses `emails[0].value` instead of `userName`
- Supports userName without email format

---

## [v0.1.14] - 2025-04-28
### Changed
- Improved SCIM PATCH /Groups to handle Authentik PatchOp requests correctly
- Fixed Mailcow custom-attribute request format
- Full group updates now correctly update mailbox "groups" custom attribute
- Resolved 422 errors during Authentik SCIM group sync

---

## [v0.1.15] - 2025-04-28
### Added
- Implemented GET /Groups/{id} endpoint to return minimal group data.
- Fixed PATCH /Groups/{id} parsing to read PatchOp "members" operation correctly.

### Fixed
- Resolved 405 Method Not Allowed error during Authentik SCIM group sync.
- Resolved 422 Unprocessable Entity error during Authentik SCIM group sync.

---