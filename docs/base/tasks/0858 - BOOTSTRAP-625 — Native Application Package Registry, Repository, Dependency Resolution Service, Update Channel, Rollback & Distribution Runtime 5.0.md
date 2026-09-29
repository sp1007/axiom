Tiếp tục với **BOOTSTRAP-625** — lần này hoàn thiện tầng phân phối ứng dụng/package ecosystem phía trên 613 và 623/624, nhưng vẫn giữ nguyên nguyên tắc **registry/marketplace là dịch vụ tùy chọn, không phải dependency của Axiom runtime**.

:::writing{variant="document" id="51683" title="BOOTSTRAP-625 — Native Application Package Registry, Repository, Dependency Resolution Service, Update Channel, Rollback & Distribution Runtime 5.0"}
# BOOTSTRAP-625 — Native Application Package Registry, Repository, Dependency Resolution Service, Update Channel, Rollback & Distribution Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Application Distribution / Package Ecosystem  
**Depends on:** BOOTSTRAP-600 → 624

---

# 1. Purpose

BOOTSTRAP-625 defines the optional distribution layer for Axiom applications and packages:

- package repositories;
- registries;
- package discovery;
- dependency resolution;
- package installation;
- package removal;
- package updates;
- update channels;
- staged rollout;
- rollback;
- package pinning;
- publisher identity;
- package trust;
- application bundles;
- application distribution;
- offline installation;
- enterprise/private repositories;
- package mirrors;
- metadata indexes;
- update manifests;
- delta updates;
- cache management;
- distribution diagnostics.

The design must remain independent from any specific marketplace, cloud provider, vendor, or centralized service.

---

# 2. Core Principle

Axiom must support:

```text
No Registry
    ↓
Local packages only

Private Registry
    ↓
Enterprise / studio / organization

Public Registry
    ↓
Community distribution

Multiple Registries
    ↓
Application-specific ecosystem
```

The Axiom runtime must function without any registry connection.

---

# 3. Non-Goals

625 does not define:

- a mandatory public marketplace;
- a mandatory cloud account;
- a mandatory vendor payment system;
- a mandatory centralized identity service;
- advertising;
- application telemetry;
- mandatory online activation;
- mandatory subscription infrastructure.

---

# 4. Layering

```text
613 Package / CAS
        │
        ▼
625 Distribution Layer
        │
 ┌──────┼───────────────┐
 ▼      ▼               ▼
Registry Resolver     Update Manager
 │      │               │
 └──────┼───────────────┘
        ▼
623 Extension / Package
624 Script / Automation
Application
```

---

# 5. Package vs Repository

A **package** is an immutable distributable artifact.

A **repository** is a source from which package metadata and artifacts can be obtained.

They must remain separate concepts.

---

# 6. Registry

A registry provides:

- package metadata;
- versions;
- hashes;
- signatures;
- dependency metadata;
- target information;
- download locations.

---

# 7. Repository

A repository may be:

```text
LocalDirectory
FileArchive
HTTPRepository
PrivateRegistry
PublicRegistry
Mirror
EmbeddedPackageStore
```

---

# 8. Repository Interface

```text
Repository {
    query()
    metadata()
    download()
    verify()
}
```

---

# 9. Offline First

Axiom must support complete offline installation.

---

# 10. Local Package Installation

Example:

```text
axiom package install mytool.axpk
```

No network access is required.

---

# 11. Repository Configuration

Repositories are configured through 601.

---

# 12. Repository Identity

Every configured repository has:

```text
RepositoryId
RepositoryEndpoint
TrustPolicy
PriorityPolicy
```

---

# 13. Repository Priority

Repository priority is used only for deterministic resolution rules.

It must not silently override security policy.

---

# 14. Trust vs Priority

A higher-priority repository cannot override a package that is forbidden by security policy.

---

# 15. Package Identity

Package identity:

```text
PackageId
PublisherId
Version
Target
Architecture
```

---

# 16. Immutable Package Version

A published package version is immutable.

A changed binary requires a new package content hash and normally a new publication revision/version.

---

# 17. Content Hash

Package content is identified through 613 CAS hashing.

---

# 18. Package Coordinate

Canonical coordinate:

```text
publisher/package@version
```

---

# 19. Target Coordinate

A package may provide variants:

```text
windows-x64
linux-x64
linux-arm64
macos-arm64
android-arm64
ios-arm64
wasm32
```

---

# 20. Target Selection

Resolver chooses a compatible target deterministically.

---

# 21. Architecture Selection

Architecture is part of compatibility.

---

# 22. ABI Selection

ABI compatibility is validated through 623 metadata.

---

# 23. Runtime Compatibility

Application runtime requirements must be satisfied before activation.

---

# 24. Package Manifest

Manifest contains:

```text
package_id
publisher
version
targets
dependencies
optional_dependencies
capabilities
entrypoints
resources
extensions
scripts
signatures
```

---

# 25. Package Metadata

Registry metadata may include:

```text
name
description
version
license
publisher
targets
size
hash
dependencies
release_notes
```

---

# 26. Metadata vs Package

Metadata is not trusted executable content.

Executable activation requires package verification.

---

# 27. Package Signature

Packages may contain signatures generated through 610.

---

# 28. Signature Verification

Installation verifies:

```text
package_hash
publisher_signature
publisher_identity
trust_policy
```

---

# 29. Publisher Identity

Publisher IDs are stable cryptographic identities.

---

# 30. Key Rotation

Publisher keys may rotate while preserving publisher identity through an authorized chain.

---

# 31. Revocation

Revoked publisher keys/packages must not activate when policy requires blocking.

---

# 32. Trust Store

Trust roots are managed through 610/603.

---

# 33. Repository Trust

A repository itself may be authenticated independently from package publishers.

---

# 34. Package Trust

Repository trust does not replace package signature verification.

---

# 35. Repository Compromise

If a repository is compromised, signed package verification still protects against unauthorized package replacement.

---

# 36. Metadata Tampering

Metadata is integrity-protected where possible.

---

# 37. Signed Index

Repositories may provide signed index snapshots.

---

# 38. Index Fingerprint

An index snapshot has:

```text
IndexHash
IndexVersion
Timestamp
RepositoryId
```

---

# 39. Deterministic Resolution

Resolution depends only on:

```text
requested packages
repository snapshots
lock file
target
ABI
security policy
```

---

# 40. Dependency Solver

625 provides a deterministic dependency resolver.

---

# 41. Dependency Constraint

Example:

```text
image.codec >= 2.0 < 3.0
```

---

# 42. Exact Dependency

```text
image.codec = 2.4.1
```

---

# 43. Wildcard Dependency

Wildcards may be permitted but are discouraged for reproducible deployments.

---

# 44. Optional Dependency

Optional dependencies do not make the package unsatisfiable when absent.

---

# 45. Feature Dependency

Features may activate dependencies conditionally.

---

# 46. Platform Dependency

A dependency may exist only for specific targets.

---

# 47. Architecture Dependency

Dependency resolution includes architecture.

---

# 48. ABI Dependency

ABI constraints are explicitly checked.

---

# 49. Dependency Conflict

Example:

```text
A → codec 1.x
B → codec 2.x
```

The resolver must determine whether both can coexist.

---

# 50. Side-by-Side Versions

Multiple versions may coexist if 623 isolation rules permit it.

---

# 51. Singleton Conflict

If a dependency requires process-global state, incompatible versions cannot silently coexist.

---

# 52. Dependency Graph

Resolver produces:

```text
ResolvedGraph
```

containing:

- nodes;
- edges;
- selected versions;
- hashes;
- target;
- ABI.

---

# 53. Graph Fingerprint

The resolved graph receives a deterministic fingerprint.

---

# 54. Lock File

Application can persist:

```text
.axlock
```

with:

```text
package_id
version
hash
target
dependencies
repository
```

---

# 55. Lock Reproducibility

A lock file must be sufficient to reproduce the same package graph while referenced artifacts remain available.

---

# 56. Hash Pinning

Production applications may pin package hashes rather than only versions.

---

# 57. Version Pinning

Applications may pin:

```text
exact
major
minor
range
```

---

# 58. Security Policy

Security policy can impose maximum allowed versions, publishers, capabilities and signatures.

---

# 59. Capability Review

Package installation can display requested capabilities before activation.

---

# 60. Capability Difference

Update manager must detect capability expansion.

Example:

```text
old:
filesystem.read

new:
filesystem.read
network.connect
```

This is a security-relevant update.

---

# 61. Capability Approval

Application policy may require explicit approval before activation.

---

# 62. No Silent Privilege Expansion

An update must not silently grant new capabilities merely because the package version changed.

---

# 63. Package Installation State

```text
Available
Downloaded
Verified
Installed
Activated
Disabled
Quarantined
Removed
```

---

# 64. Installation Transaction

Installation uses an atomic transaction:

```text
download
verify
stage
validate
commit
```

---

# 65. Staging Directory

Temporary package files are stored in a secure staging area.

---

# 66. No Execution During Staging

Package binaries are not executed while staging.

---

# 67. Atomic Activation

Activation switches from old package generation to new package generation atomically where the platform allows.

---

# 68. Generation

Installed package generations are tracked.

---

# 69. Previous Generation

Previous generation remains available until rollback retention policy removes it.

---

# 70. Rollback

Rollback selects a previously verified generation.

---

# 71. Rollback Safety

Rollback must not erase user data.

---

# 72. Application State Compatibility

Package rollback may require state migration compatibility.

---

# 73. State Boundary

Application data is not automatically rolled back with package binaries.

---

# 74. Database Migration

Database/schema migrations must declare forward and rollback capabilities explicitly.

---

# 75. No Fake Rollback

If data migration cannot be reversed, package rollback does not pretend to restore old data.

---

# 76. Update Manager

Core object:

```text
UpdateManager
```

provides:

```text
check()
plan()
download()
verify()
stage()
activate()
rollback()
```

---

# 77. Update Plan

An update plan contains:

```text
current_graph
target_graph
added
removed
changed
capability_changes
migration_requirements
```

---

# 78. Dry Run

Updates can be simulated without modifying the installed state.

---

# 79. Update Preview

Preview reports:

- package changes;
- size;
- dependencies;
- capabilities;
- restart requirements;
- migration requirements.

---

# 80. Restart Requirement

Package metadata may declare whether application restart is required.

---

# 81. Hot Update

Packages compatible with 623 may update without full application restart.

---

# 82. Cold Update

Packages that cannot hot-update require restart.

---

# 83. Hot Update Validation

Hot update follows 623 quiescence and reload rules.

---

# 84. Update Failure

Failure leaves the previous active generation intact where possible.

---

# 85. Interrupted Update

An interrupted update must be recoverable from the staged transaction.

---

# 86. Power Loss

After power loss, installation state is reconciled deterministically.

---

# 87. Crash Recovery

600/611 recovery primitives are used.

---

# 88. Update Journal

Installation may maintain:

```text
.axupdate-journal
```

containing transaction state.

---

# 89. Journal Integrity

Journal state is validated before recovery.

---

# 90. Atomic Pointer

Activation can use an atomic generation pointer:

```text
active → generation_17
```

then:

```text
active → generation_18
```

---

# 91. Update Channels

Packages may publish channels:

```text
stable
beta
preview
nightly
internal
```

---

# 92. Channel Semantics

A channel is a publication policy, not a security boundary.

---

# 93. Channel Pinning

Applications can pin a channel.

---

# 94. Channel Migration

Moving channels is an explicit configuration change.

---

# 95. Downgrade

Downgrade is allowed only if package/state compatibility permits it.

---

# 96. Downgrade Policy

Security policy may prohibit downgrade below a minimum secure version.

---

# 97. Minimum Secure Version

Policy may specify:

```text
min_allowed_version
```

---

# 98. Security Update

A security update can be marked:

```text
security_fix = true
```

This is metadata, not an automatic forced-update requirement.

---

# 99. Emergency Block

Security policy can block known-compromised package versions.

---

# 100. Quarantine

Blocked packages enter:

```text
Quarantined
```

and cannot activate.

---

# 101. Package Removal

Removal transaction:

```text
disable
stop
deactivate
remove registrations
remove package
```

---

# 102. Data Preservation

Removal does not delete application data by default.

---

# 103. Purge

Explicit purge may remove package-owned cache/state where policy allows.

---

# 104. Dependency Removal

A package cannot be removed while required by another active package unless the dependent package is also removed/updated.

---

# 105. Orphan Detection

Resolver identifies unused dependencies.

---

# 106. Garbage Collection of Packages

Package reclamation is distinct from language garbage collection.

---

# 107. Package Reclamation

Unused package generations may be deleted when:

- not active;
- not pinned;
- not required;
- outside rollback retention.

---

# 108. CAS Reclamation

613 handles actual CAS object reclamation.

---

# 109. Cache Layers

```text
Repository Cache
Package Cache
CAS
Compiled Artifact Cache
Runtime Resource Cache
```

---

# 110. Cache Integrity

Caches are verified through hashes.

---

# 111. Corrupted Cache

Corrupted entries are discarded and re-fetched when possible.

---

# 112. Offline Cache

Cached packages remain installable offline.

---

# 113. Mirror

Repositories can use mirrors.

---

# 114. Mirror Selection

Selection can consider:

- configured priority;
- availability;
- locality;
- policy.

---

# 115. Mirror Integrity

All downloaded packages remain independently hash/signature verified.

---

# 116. Partial Download

Large packages support resumable download.

---

# 117. Chunk Verification

613 CAS chunk hashes verify downloaded chunks.

---

# 118. Download Limits

606 resource limits apply to:

- bandwidth;
- disk;
- memory;
- concurrent downloads.

---

# 119. Network

609 provides network transport.

---

# 120. TLS

610 provides TLS/trust.

---

# 121. Authentication

Repository authentication may use:

- TLS certificates;
- tokens;
- signed requests;
- enterprise credentials.

Credentials are managed through 601/610.

---

# 122. Credential Isolation

Repository credentials are not exposed to packages.

---

# 123. Anonymous Repository

Repositories may permit anonymous metadata/download access.

---

# 124. Private Repository

Private repositories require explicit credentials.

---

# 125. Enterprise Repository

Enterprise policy may specify:

```text
allowed_repositories
blocked_repositories
required_signers
allowed_publishers
```

---

# 126. Repository Policy

603 controls access to repository endpoints.

---

# 127. Package Download

Download process:

```text
resolve
→ select artifact
→ download
→ hash verify
→ signature verify
```

---

# 128. Artifact Selection

Selection considers:

- target;
- architecture;
- ABI;
- CPU features;
- graphics capabilities where declared.

---

# 129. CPU Features

A package may publish variants:

```text
baseline
avx2
avx512
neon
```

---

# 130. Runtime Selection

CPU capability detection occurs before selecting an optimized variant.

---

# 131. Fallback

Baseline package remains available when optimized variants are unsupported.

---

# 132. GPU Variants

Packages may provide shader/model/resource variants for different GPUs.

---

# 133. Package Resource Variants

613 handles target-specific resource selection.

---

# 134. Localization

Packages can contain `.axloc` resources from 617.

---

# 135. Theme Resources

Packages can contain theme assets.

---

# 136. Media Resources

Packages can contain 616 media assets.

---

# 137. Shader Resources

Packages can contain 615 shader artifacts.

---

# 138. Model Resources

Packages can contain AI model artifacts.

Large objects should use CAS/chunking rather than duplicating data.

---

# 139. Application Bundle

Application distribution may use:

```text
ApplicationBundle
```

containing:

```text
executable
native libraries
packages
resources
manifest
signatures
```

---

# 140. Platform Bundle

625 maps application bundles to platform-specific packaging:

```text
Windows
Linux
macOS
Android
iOS
WASM
```

---

# 141. Platform Installer

Installer format is platform-specific.

625 defines the logical package model rather than replacing OS-native installers.

---

# 142. Portable Application

An application may be distributed as a self-contained directory/bundle.

---

# 143. Single-File Application

Optional packaging can combine:

```text
executable + resources + package store
```

into a single distributable artifact.

---

# 144. Extraction

Single-file packages may extract resources lazily or at installation time.

---

# 145. Memory Mapping

Uncompressed package resources may be memory mapped through 611/613.

---

# 146. Executable Extraction

Executable components should not be executed directly from unverified temporary locations.

---

# 147. Code Signing

Platform-native signing remains separate from Axiom package signatures.

---

# 148. Dual Verification

Distribution may require:

```text
Axiom package signature
+
OS/platform code signature
```

---

# 149. Application Identity

Application package has:

```text
ApplicationId
PublisherId
Version
BuildId
```

---

# 150. Application Update

Application update follows the same staged-generation model.

---

# 151. Self-Update

An application cannot replace its own running executable directly on platforms that prohibit it.

A separate updater process may perform the operation.

---

# 152. Updater

Optional:

```text
UpdateAgent
```

supervised by 605.

---

# 153. Update Agent Security

Updater receives only the capabilities required for installation.

---

# 154. Updater Isolation

Updater should preferably be a separate executable/process.

---

# 155. Update Agent Failure

A failed update agent must not corrupt the current application generation.

---

# 156. Bootstrap

Applications may use a small bootstrap executable:

```text
bootstrap
    ↓
select generation
    ↓
launch application
```

---

# 157. Generation Selection

Bootstrap chooses the latest valid generation according to policy.

---

# 158. Failed Startup

If the new generation repeatedly fails startup, bootstrap can revert to a known-good generation.

---

# 159. Crash Loop

605 can detect repeated application startup failures.

---

# 160. Rollback Threshold

Rollback requires an explicit configured policy.

---

# 161. Startup Health

Application reports readiness to 605.

---

# 162. Failed Update Detection

An update is considered unhealthy if application readiness is not achieved according to configured policy.

---

# 163. Rollback

Rollback switches to the previous verified generation.

---

# 164. Data Compatibility

Rollback does not automatically revert user data.

---

# 165. Migration Strategy

Applications should use forward-compatible storage migrations where possible.

---

# 166. Database Migration Package

Migration metadata may be included in package manifests.

---

# 167. Migration Transaction

Migration runs transactionally where underlying storage supports it.

---

# 168. Migration Backup

Before irreversible migration, application may create a 600/611 checkpoint/backup.

---

# 169. Backup

Backup is separate from package rollback.

---

# 170. Restore

Restore is an explicit data operation.

---

# 171. Delta Update

Packages may publish binary/content deltas.

---

# 172. Delta Safety

Delta application requires exact source hash matching.

---

# 173. Delta Failure

If delta application fails, full package download remains available.

---

# 174. Delta Verification

Final package hash/signature is verified after reconstruction.

---

# 175. Compression

613 provides package compression.

---

# 176. Encryption

Package encryption is optional and policy-dependent.

---

# 177. Secret Packages

Private packages may be encrypted for authorized deployments.

---

# 178. Package License Metadata

Packages may contain license metadata.

625 stores and exposes it but does not define legal licensing rules.

---

# 179. Publisher Metadata

Publisher metadata may contain:

```text
publisher_id
display_name
key_ids
contact
```

---

# 180. Publisher Verification

Human-readable publisher names are not trust identities.

Cryptographic publisher identity is authoritative.

---

# 181. Package Name Collision

Package IDs, not display names, define identity.

---

# 182. Typosquatting Mitigation

Tooling may warn when package IDs are visually similar to known installed packages.

The warning must not override explicit package identity.

---

# 183. Dependency Confusion Protection

Repository policy can restrict which repositories may satisfy specific package namespaces.

---

# 184. Namespace Ownership

Organizations can reserve package namespaces through repository policy.

---

# 185. Repository Scope

Example:

```text
company.*
```

may be resolved only from an enterprise repository.

---

# 186. Source Locking

Lock file can record the repository that supplied each package.

---

# 187. Source Policy

Resolver can require exact repository identity.

---

# 188. Package Transparency

Repositories may expose immutable publication history.

---

# 189. Reproducible Metadata

Index snapshots should have deterministic serialization.

---

# 190. Repository Snapshot

A snapshot contains a deterministic list of package metadata.

---

# 191. Snapshot Pinning

Production builds can pin a repository snapshot hash.

---

# 192. Build Reproducibility

Build systems can use:

```text
source lock
+
package lock
+
repository snapshot
```

to reproduce dependencies.

---

# 193. Dependency Vendoring

Applications may vendor packages locally.

---

# 194. Vendored Packages

Vendored packages are treated like local immutable packages.

---

# 195. No Network Build

A fully vendored application must build without network access.

---

# 196. Build Cache

Compiler artifacts may be cached through 613.

---

# 197. Binary Cache

Trusted precompiled artifacts can be distributed.

---

# 198. Binary Cache Verification

Binary cache artifacts require:

```text
source_hash
compiler_hash
target
ABI
feature_set
```

matching.

---

# 199. Untrusted Binary Cache

Untrusted binary artifacts are rebuilt locally unless explicitly allowed by policy.

---

# 200. Compiler Trust

Package distribution does not replace compiler/toolchain trust.

---

# 201. Toolchain Packages

Compilers, SDKs and tools can themselves be distributed as packages.

---

# 202. Toolchain Isolation

Different Axiom toolchain versions can coexist.

---

# 203. Toolchain Selection

Project manifest chooses its required toolchain.

---

# 204. Compiler Lock

Project may contain:

```text
toolchain_version
toolchain_hash
```

---

# 205. SDK Packages

Platform SDK metadata can be distributed through package infrastructure.

---

# 206. Cross Compilation

Packages may contain target-specific artifacts.

---

# 207. Native SDK Dependency

Core compiler must not require a public package registry to compile basic Axiom code.

---

# 208. Bootstrap Compiler

Axiom bootstrap toolchain must remain independently distributable.

---

# 209. Package Manager

CLI:

```text
axiom package search
axiom package info
axiom package install
axiom package remove
axiom package update
axiom package verify
axiom package list
axiom package graph
axiom package cache
```

---

# 210. Repository Commands

```text
axiom repo add
axiom repo remove
axiom repo list
axiom repo sync
axiom repo verify
```

---

# 211. Update Commands

```text
axiom update check
axiom update plan
axiom update apply
axiom update rollback
```

---

# 212. Offline Commands

```text
axiom package export
axiom package import
axiom repo snapshot
axiom repo restore
```

---

# 213. Package Inspection

Inspection must never execute package code.

---

# 214. Manifest Inspection

Manifest can be parsed without loading binaries.

---

# 215. Binary Inspection

Binary metadata can be inspected without activation.

---

# 216. Capability Inspection

Tools report requested capabilities before installation.

---

# 217. Update Planning

Planning must not modify active package generations.

---

# 218. Download Scheduling

Downloads use 607 and 606.

---

# 219. Concurrent Downloads

Concurrent downloads are bounded by resource policy.

---

# 220. Backpressure

Repository downloads use bounded buffers.

---

# 221. Resume

Interrupted downloads can resume from verified chunks.

---

# 222. HTTP Range

609 may provide HTTP range support.

---

# 223. TLS

Repository traffic uses 610 TLS.

---

# 224. Certificate Policy

Enterprise repositories can use custom trust policies.

---

# 225. Proxy

Repository access can use 609 proxy support.

---

# 226. Authentication Secrets

Credentials use 601/610 secure secret handling.

---

# 227. Logging

602 logs package operations without exposing credentials.

---

# 228. Diagnostics

Package operations include:

```text
repository_id
package_id
version
hash
operation
duration
result
```

---

# 229. Privacy

Package manager must not transmit unrelated application data.

---

# 230. Telemetry

No package-management telemetry is mandatory.

---

# 231. Opt-In Metrics

Applications may enable aggregate package metrics explicitly.

---

# 232. Audit

Enterprise installations can emit signed audit records.

---

# 233. Audit Content

Audit includes:

- package;
- publisher;
- version;
- operation;
- policy result.

Not secrets.

---

# 234. Resource Quotas

Package manager respects:

- disk quota;
- network quota;
- CPU quota;
- memory quota.

---

# 235. Disk Reservation

Installation reserves sufficient storage before activation where possible.

---

# 236. Disk Full

Failed installation preserves the previous active generation.

---

# 237. Read-Only Filesystem

Installation fails without corrupting active state.

---

# 238. Permission Failure

Permission errors are surfaced as structured errors.

---

# 239. Concurrent Installation

Package store uses transactional locking/generation semantics.

---

# 240. Multiple Processes

Concurrent package operations coordinate through 611 synchronization.

---

# 241. Package Store Lock

Package store lock is separate from application runtime locks.

---

# 242. Crash Recovery

Store transaction journal recovers incomplete operations.

---

# 243. CAS Integrity

613 validates CAS objects.

---

# 244. Package Deduplication

Identical package content is stored once.

---

# 245. Hard-Link/Reflink

Platform-specific deduplication may be used where safe.

---

# 246. Copy-on-Write

Updates prefer immutable generation directories.

---

# 247. Atomic Pointer Switching

Activation uses an atomic metadata update.

---

# 248. Package Garbage Collection

Unused package generations are reclaimed only after safety checks.

---

# 249. Retention Policy

Retention may specify:

```text
minimum_generations
minimum_days
pinned_generations
```

---

# 250. Rollback Retention

At least one known-good generation may be retained where storage allows.

---

# 251. Emergency Recovery

Bootstrap can launch a recovery mode without activating optional packages.

---

# 252. Recovery Environment

Recovery mode contains only trusted minimal components.

---

# 253. Safe Mode

Application can disable third-party extensions during startup.

---

# 254. Safe Mode Trigger

Repeated startup failure may trigger safe mode according to 605 policy.

---

# 255. Extension Isolation

625 delegates extension lifecycle to 623.

---

# 256. Script Isolation

625 delegates scripts to 624.

---

# 257. Package Installation

625 installs packages; 623/624 activate their contents.

---

# 258. Package Removal

625 removes artifacts after 623/624 release them.

---

# 259. Update Coordination

Update manager coordinates:

```text
625
 ↓
623
 ↓
624
```

to ensure active resources are quiescent.

---

# 260. Application Update Order

Recommended:

```text
prepare package
verify
quiesce extensions
quiesce scripts
migrate state if required
activate package
restart/reload
restore
```

---

# 261. Failure During Activation

Previous package generation remains authoritative unless activation transaction commits.

---

# 262. Failure During Migration

Migration rollback occurs before package activation commits.

---

# 263. Failure After Commit

Recovery uses the new package generation or explicit rollback policy.

---

# 264. Application Readiness

Application reports readiness after update through 605.

---

# 265. Update Health

Update health may include:

```text
process ready
services ready
documents recoverable
extensions compatible
workspace restorable
```

---

# 266. No Hidden Health Criteria

Applications explicitly define readiness conditions.

---

# 267. Staged Rollout

Repositories may publish rollout metadata.

---

# 268. Rollout Groups

Deployment policy may select:

```text
internal
pilot
general
```

---

# 269. Rollout Selection

Selection is deployment policy, not package identity.

---

# 270. Percentage Rollout

A deployment service may select a subset of installations.

The core package manager does not require telemetry to implement this.

---

# 271. Rollout Pause

Deployment service can stop publishing a rollout.

---

# 272. Package Availability

Unpublished packages remain usable by installations that already possess them unless policy blocks them.

---

# 273. Security Revocation

Security policy can explicitly disable compromised packages.

---

# 274. Emergency Revocation

Revocation metadata may be distributed independently from ordinary package updates.

---

# 275. Offline Revocation

Organizations can distribute revocation lists offline.

---

# 276. Revocation Cache

Revocation data is cached with expiration policy.

---

# 277. Clock Security

Security-sensitive expiration uses trusted time sources where available.

---

# 278. Clock Failure

If secure time cannot be established, policy decides whether to allow installation.

---

# 279. Repository Availability

A temporary repository outage must not invalidate already installed packages.

---

# 280. Existing Package Execution

Installed and verified packages can operate offline.

---

# 281. Online License Checks

Online license enforcement is outside the mandatory package runtime.

---

# 282. Application Licensing

Applications may implement licensing as a 623/624 service.

---

# 283. Payment

Payment systems are completely outside 625.

---

# 284. Marketplace UI

Marketplace UI is an application built on:

```text
619
622
624
625
```

not a runtime primitive.

---

# 285. Search

Repository search returns metadata only.

---

# 286. Ranking

625 does not require ranking algorithms.

Repository services may define their own search semantics.

---

# 287. Recommendations

Package recommendation systems are outside the core package manager.

---

# 288. Reviews

User reviews are outside the package runtime.

---

# 289. Social Metadata

Social metadata is not part of package identity or trust.

---

# 290. Package Documentation

Documentation may be packaged as resources.

---

# 291. Documentation Rendering

624/619 can render package documentation.

---

# 292. API Documentation

623 metadata can be indexed by package repositories.

---

# 293. Example Package

```text
image.editor@4.2.0
```

contains:

```text
bin/windows-x64/editor.dll
bin/linux-x64/editor.so
extensions/image_importer.axext
scripts/tools.axs
resources/
schemas/
manifest
signature
```

---

# 294. Dependency Example

```text
image.editor
 ├── image.codec >= 3 < 4
 ├── text.ui >= 2
 └── color.core = 1.5.2
```

---

# 295. Resolution

Resolver produces:

```text
image.editor 4.2.0
image.codec 3.7.1
text.ui 2.8.0
color.core 1.5.2
```

with hashes and ABI metadata.

---

# 296. Update Example

Current:

```text
image.editor 4.1.0
```

Available:

```text
4.2.0
```

Update plan determines:

```text
changed:
image.editor

unchanged:
image.codec
text.ui
color.core
```

Only affected packages are downloaded.

---

# 297. Delta Example

If 4.2.0 provides a delta:

```text
4.1.0 hash
    ↓
delta
    ↓
4.2.0
    ↓
verify final hash
```

---

# 298. Rollback Example

```text
generation_17
    ↓
update
    ↓
generation_18
    ↓
failure
    ↓
generation_17
```

---

# 299. Package API

```text
struct PackageManager {
    fn search(query: PackageQuery) -> Result<PackageList>
    fn install(request: PackageRequest) -> Result<InstallResult>
    fn remove(id: PackageId) -> Result<void>
    fn update(request: UpdateRequest) -> Result<UpdateResult>
    fn rollback(id: PackageId) -> Result<void>
}
```

---

# 300. Resolver API

```text
struct PackageResolver {
    fn resolve(
        request: DependencyRequest,
        context: ResolveContext
    ) -> Result<ResolvedGraph>
}
```

---

# 301. Repository API

```text
trait PackageRepository {
    fn query(query: PackageQuery) -> Result<PackageMetadata>
    fn get_manifest(id: PackageId, version: Version)
        -> Result<PackageManifest>

    fn download(
        artifact: ArtifactId,
        destination: Path
    ) -> Result<DownloadResult>
}
```

---

# 302. Update API

```text
struct UpdateManager {
    fn check() -> Result<UpdateSet>
    fn plan() -> Result<UpdatePlan>
    fn apply(plan: UpdatePlan) -> Result<UpdateResult>
    fn rollback(package: PackageId) -> Result<void>
}
```

---

# 303. Package Policy

```text
struct PackagePolicy {
    allowed_publishers
    allowed_repositories
    blocked_packages
    minimum_versions
    required_signatures
    allow_unsigned
    allow_downgrade
}
```

---

# 304. Architecture Invariants

1. Registry is optional.
2. Internet is optional.
3. Marketplace is optional.
4. Online account is optional.
5. Package identity is cryptographic/stable.
6. Package versions are immutable.
7. Package hashes are deterministic.
8. Package signatures are independently verified.
9. Repository trust does not replace package trust.
10. Installation never executes package code.
11. Activation is separate from installation.
12. Updates are transactional.
13. Previous generations remain available according to retention policy.
14. Rollback does not silently roll back user data.
15. Dependency resolution is deterministic.
16. Lock files can reproduce dependency graphs.
17. Hash pinning is supported.
18. Repository source can be pinned.
19. Capability expansion is visible.
20. Updates cannot silently elevate privileges.
21. Package removal preserves user data by default.
22. Package reclamation is distinct from language GC.
23. CAS is content-addressed.
24. Corrupted cache entries are discarded.
25. Offline installation is supported.
26. Self-update uses an appropriate updater architecture.
27. Application readiness participates in update health.
28. Crash loops can trigger safe recovery.
29. Package managers cannot bypass 603.
30. Repository credentials remain secret.
31. Package operations use 606 quotas.
32. Downloads use 609.
33. TLS uses 610.
34. Storage uses 611.
35. CAS uses 613.
36. Extensions use 623.
37. Scripts use 624.
38. Application state uses 600.
39. Package metadata is inspectable without execution.
40. Native Axiom applications do not require package infrastructure.

---

# 305. Acceptance Criteria

### Package Identity
1. Package ID.
2. Publisher ID.
3. Version.
4. Target.
5. Architecture.
6. ABI.
7. Hash.
8. Build ID.
9. Manifest.
10. immutable package version.

### Repository
11. Local repository.
12. File repository.
13. HTTP repository.
14. Private repository.
15. Public repository.
16. Mirror.
17. repository identity.
18. repository trust.
19. repository snapshot.
20. index fingerprint.

### Resolution
21. semantic constraints.
22. exact versions.
23. optional dependencies.
24. platform dependencies.
25. ABI constraints.
26. conflict detection.
27. cycle detection.
28. side-by-side versions.
29. deterministic graph.
30. graph fingerprint.

### Security
31. package signature.
32. publisher identity.
33. key rotation.
34. revocation.
35. trust policy.
36. capability inspection.
37. capability expansion detection.
38. repository restrictions.
39. namespace restrictions.
40. dependency-confusion protection.

### Installation
41. staging.
42. verification.
43. atomic commit.
44. generation.
45. interrupted update recovery.
46. power-loss recovery.
47. disk-full handling.
48. offline install.
49. package removal.
50. purge.

### Updates
51. update check.
52. update plan.
53. dry run.
54. channel selection.
55. staged rollout metadata.
56. hot update.
57. cold update.
58. delta update.
59. rollback.
60. downgrade policy.

### Application Distribution
61. application bundle.
62. portable application.
63. single-file package.
64. platform bundle.
65. platform signing boundary.
66. bootstrap.
67. update agent.
68. safe mode.
69. startup health.
70. crash-loop recovery.

### Cache/CAS
71. package cache.
72. CAS integration.
73. chunk verification.
74. resumable download.
75. cache corruption recovery.
76. deduplication.
77. retention policy.
78. stale generation cleanup.
79. binary cache.
80. compiler cache.

### Toolchain
81. toolchain packages.
82. toolchain pinning.
83. SDK packages.
84. offline build.
85. vendored dependencies.
86. compiler artifact verification.
87. cross-compilation packages.
88. target variants.
89. CPU variants.
90. GPU/resource variants.

### Operations
91. package CLI.
92. repository CLI.
93. update CLI.
94. offline export/import.
95. package inspection.
96. capability inspection.
97. dependency graph.
98. update plan.
99. diagnostics.
100. audit.

### Reliability
101. transaction journal.
102. crash recovery.
103. power-loss recovery.
104. rollback.
105. failed migration handling.
106. concurrent operation handling.
107. repository outage handling.
108. cache recovery.
109. corrupted package handling.
110. incomplete download handling.

### Performance
111. lazy metadata.
112. parallel downloads.
113. bounded download memory.
114. chunked transfer.
115. resumable transfer.
116. CAS deduplication.
117. mmap-compatible resources.
118. minimal package manager.
119. dead stripping.
120. no mandatory daemon.

### Integration
121. 600 state.
122. 601 config.
123. 602 diagnostics.
124. 603 security.
125. 604 IPC.
126. 605 supervision.
127. 606 resources.
128. 607 scheduler.
129. 608 synchronization.
130. 609 networking.
131. 610 crypto.
132. 611 storage.
133. 612 serialization.
134. 613 package/CAS.
135. 614 devices.
136. 615 graphics.
137. 616 media.
138. 617 text.
139. 619 GUI.
140. 620 state/commands.
141. 621 documents.
142. 622 workspace.
143. 623 extensions.
144. 624 scripting.

---

# 306. Final Architecture

```text
                         AXIOM DISTRIBUTION
                                │
                         ┌──────┴──────┐
                         ▼             ▼
                    Local Store    Repository
                         │             │
                         └──────┬──────┘
                                ▼
                         Package Resolver
                                │
                         Resolved Graph
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                 Verify       Download    Policy
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                         Staging / CAS
                                │
                         Atomic Commit
                                │
                         Package Generation
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
          Native App        623 Extension      624 Script
              │                 │                  │
              └─────────────────┼──────────────────┘
                                ▼
                         Application Runtime
                                │
                         Health / Readiness
                                │
                         605 Supervision
                                │
                         Rollback if required
```

---

# 307. Distribution Profiles

## Minimal

```text
AXIOM_PACKAGE_NONE
```

No package manager.

---

## Local

```text
AXIOM_PACKAGE_LOCAL
```

Local AXPK installation and CAS.

---

## Developer

```text
AXIOM_PACKAGE_DEV
```

Local repository, dependency resolution, development packages.

---

## Enterprise

```text
AXIOM_PACKAGE_ENTERPRISE
```

Private repositories, publisher policy, signed packages, audit.

---

## Full

```text
AXIOM_PACKAGE_FULL
```

Repository synchronization, update channels, staged updates, rollback and package management.

---

# 308. Important Boundary

625 does **not** become part of the fundamental Axiom execution model.

The following remains valid:

```text
hello.ax
    ↓
axiom compiler
    ↓
native executable
```

with:

```text
no registry
no account
no package daemon
no marketplace
no network
no plugin manager
no scripting engine
```

unless the application explicitly chooses those features.

---

# 309. Result

BOOTSTRAP-625 establishes a complete distribution architecture from:

```text
single local .axpk
```

through:

```text
private enterprise repository
```

to:

```text
large multi-platform package ecosystem
```

while maintaining:

- deterministic dependency resolution;
- cryptographic package identity;
- offline operation;
- atomic updates;
- rollback;
- package generations;
- capability-aware installation;
- reproducible builds;
- CAS deduplication;
- target-specific artifacts;
- extension integration;
- scripting integration;
- application recovery.

The key architectural distinction is:

```text
613 = how packages are represented and stored
623 = how native extensions execute
624 = how dynamic behavior executes
625 = how packages are discovered, resolved, installed and updated
```

---

# 310. Task Completion

**BOOTSTRAP-625 — COMPLETE**

**Next queued task: BOOTSTRAP-626 — Native Application Networking Services, HTTP Client/Server Framework, Web API, RPC, WebSocket, Service Gateway & Distributed Application Runtime 5.0**
:::