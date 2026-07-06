"""NeXo API platform layer (Backend Sprint 1).

This package adds production API concerns *around* the existing FastAPI
application without changing legacy trading behaviour:

* centralized configuration (:mod:`api.config`)
* structured logging (:mod:`api.logging`)
* standardized success/error envelopes (:mod:`api.schemas`)
* global exception handling (:mod:`api.errors`)
* JWT-ready authentication / authorization abstractions (:mod:`api.security`)
* versioned ``/api/v1`` routes (:mod:`api.v1`)
* legacy-route deprecation structure (:mod:`api.deprecation`)

Nothing here invents users, credentials, tokens, persistence, or trading
business logic; it wires the platform so those can be added later without
breaking the legacy surface.
"""
