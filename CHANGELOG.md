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
- Updated health check endpoint to `/healthz`.

---

## Version 0.1.2 - 2025-04-28

### Added

- Added curl installation to Dockerfile for health check functionality.
- Updated Dockerfile to install necessary dependencies.
- Updated health check in container to ensure service is running correctly.