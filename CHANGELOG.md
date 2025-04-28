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
- **SCIM POST /Users** now returns a full SCIM User resource including `id`, `userName`, `name`, `emails`, and `externalId`.
- **SCIM POST /Users** returns HTTP 201 Created per SCIM specification.
- **SCIM POST /Groups** now returns a full SCIM Group resource including `id`, `displayName`, and `members`.
- **SCIM POST /Groups** returns HTTP 201 Created.
- Eliminated 422 errors during Authentik sync by providing valid `id` fields in create responses.

---