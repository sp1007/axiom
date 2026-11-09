# Red-Team Architectural Review: Proposal #10 (`std.web` FastAPI-Grade HTTP(S) Server in `P21`)

**Author**: Red-Team Critic 3 (Web Framework, Type-System Extractors, HTTPS Security & `P21` Architecture)
**Scope**: Adversarial stress-test, handler type-system ergonomics, OpenAPI/422 comptime design, and HTTPS/DoS security guardrails for `std.web`.

---

## Verdict: `ACCEPT WITH MANDATORY SECURITY & TYPE-SYSTEM REFINEMENTS`

Place as **Epic `E21.11` (`std.web`: FastAPI-Grade Web Framework, Typed Extractors, OpenAPI 3.1 & Hardened HTTPS Server)** in **`P21-standard-library-completion`** (assigning the next free `SPEC-NNN` in `P21` — note `SPEC-120`..`SPEC-128` are already assigned to `E21.1`..`E21.9`, so use `SPEC-129` or next free SPEC number!).

---

## Key Traps Caught & Architectural Guardrails

1. **Solving the Handler Signature Trap (Neither Python Runtime RTTI nor Rust/Axum 16-Tuple Trait Hell)**:
   - Reject runtime `inspect.signature()` (violates `SPEC-61 AXS-RFL-002` zero-RTTI-by-default).
   - Reject inscrutable 16-tuple trait errors: provide `Context` Tier-1 handler + arity `0..5` typed extractor adapters validated via **`P14` `comptime` + `type_info<F>()`**, emitting pinpoint diagnostics (`Handler parameter at index <i> of type '<T>' does not implement 'FromRequest'`)!
   - Dependency injection via `FromRequest<S>` (`State<T>`, scoped extractors) — FastAPI `Depends(...)` ergonomics with zero runtime reflection overhead.

2. **Compile-Time Validation (`422`) & Air-Gapped Offline `/docs`**:
   - `@derive(Validate)` + `@validate(min, max, min_len, max_len, email, regex)` (using `std.regex`) returns structured RFC 9457 `422 Unprocessable Content` JSON (`loc`, `msg`, `type`).
   - `OpenApiSpec` extracts OpenAPI 3.1 JSON (`/openapi.json`) at `comptime` from `TypeInfo` + route table.
   - Interactive `/docs` explorer HTML/JS is embedded offline via `@embed_str` (Proposal #4) — **zero external CDN requests** (safe in air-gapped networks, zero `Referer` endpoint leaks), easily disabled (`docs_url = Option.None`) in production.

3. **Zero-Trust HTTPS & DoS Hardening**:
   - Runs natively over hardened `std.net.tls` (TLS 1.3 + ALPN `h2`/`http/1.1` + SNI + atomic live certificate reload without dropping active connections).
   - Slowloris defenses: `header_read_timeout`, `body_read_timeout`, `idle_keepalive_timeout`.
   - OOM DoS defense: `max_body_bytes` checked *before* buffering (`413 Content Too Large`); streaming `Multipart` uploads via bounded 64 KiB chunks.
   - `StaticDir` path-traversal defense: canonical prefix check, rejecting NUL bytes, `\`, `..`, colons / NTFS `::$DATA`, Windows reserved DOS device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1..9`, `LPT1..9`), and symlinks escaping root.
   - CORS rejects `allow_origins = ["*"]` + `allow_credentials = true`.
   - Client socket disconnect immediately cancels the request's `CancellationToken`, dropping in-flight `Future` / `async gen fn` `SseStream` deterministically.

4. **Clean Layering (`E21.4` vs `E21.11` vs `P24`)**:
   - `E21.4` (`T914`) owns wire-level TLS 1.3, HTTP/1.1 + HTTP/2 framing, HTTP client, and binary RPC framing.
   - `E21.11` (`std.web`) layers radix routing, typed extractors, `422` validation, `comptime` OpenAPI 3.1 + `/docs`, middleware, `StaticDir`, `Multipart`, and high-level `SseStream`/`WebSocketUpgrade` on top of `T914`.
   - ORMs, HTML template engines, OAuth2/OIDC providers, and Redis session stores remain strictly in `P24` (deferred).
