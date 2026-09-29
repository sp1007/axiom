Tiếp tục chuỗi thiết kế Axiom. Task kế tiếp là **BOOTSTRAP-677**, mở rộng Axiom từ tầng chính quyền/xã hội sang tầng văn hóa, nghệ thuật, truyền thông, tri thức công cộng và di sản — đồng thời giữ ranh giới rõ với AI foundation, knowledge graph, pháp luật, kinh tế và chính quyền.

:::writing{variant="document" id="58241" title="BOOTSTRAP-677 — Native AI Civilization-Scale Culture, Arts, Media, Information, Public Knowledge, Heritage, Creative Industries & Collective Cultural Memory Runtime 5.0"}

# BOOTSTRAP-677
## Native AI Civilization-Scale Culture, Arts, Media, Information, Public Knowledge, Heritage, Creative Industries & Collective Cultural Memory Runtime 5.0

**Status:** Architecture Specification  
**Layer:** Civilization Runtime / Culture & Information Systems  
**Version:** 5.0  
**Depends on:** BOOTSTRAP-603, 617, 625, 639, 640, 645, 649, 650, 651, 658, 667, 668, 670, 671, 672, 673, 675, 676

---

# 1. Mục tiêu

BOOTSTRAP-677 định nghĩa runtime native của Axiom cho toàn bộ hệ thống:

- văn hóa;
- nghệ thuật;
- tác phẩm sáng tạo;
- truyền thông;
- xuất bản;
- báo chí;
- thông tin công cộng;
- thư viện;
- lưu trữ;
- bảo tàng;
- di sản vật thể;
- di sản phi vật thể;
- lịch sử truyền miệng;
- bảo tồn văn hóa;
- số hóa;
- phục chế;
- bản quyền và quyền sử dụng ở mức operational metadata;
- phân phối nội dung;
- provenance;
- fact-checking;
- correction/retraction;
- nội dung tổng hợp bằng AI;
- ngành công nghiệp sáng tạo;
- ký ức văn hóa tập thể;
- dịch thuật/localization;
- phụ đề/lồng tiếng;
- hệ thống discovery/search media;
- mô phỏng hệ sinh thái văn hóa và truyền thông.

Mục tiêu không phải tạo một "ứng dụng mạng xã hội" hay "CMS".

Mục tiêu là cung cấp **native substrate** để Axiom có thể xây dựng:

```text
Library
Archive
Museum
Publishing Platform
Newsroom
Digital Newspaper
Streaming Platform
Podcast Platform
Video Platform
Music Platform
Art Platform
Game Platform
Cultural Heritage System
Digital Humanities Platform
Public Knowledge Portal
Creative Studio
Media Production Pipeline
AI Media Platform
Cultural Simulation
```

mà không cần một runtime văn hóa riêng bên ngoài ngôn ngữ.

---

# 2. Nguyên tắc kiến trúc

## 2.1 Culture không phải Social Intelligence

BOOTSTRAP-658 xử lý:

```text
social perception
social interaction
social reasoning
social relationship
social behavior
```

BOOTSTRAP-677 xử lý:

```text
cultural artifact
media
publication
heritage
creative production
information dissemination
collective cultural memory
```

---

# 3. Ranh giới với các bootstrap khác

| Bootstrap | Trách nhiệm |
|---|---|
| 617 | Unicode, text, font, typography |
| 645 | semantic knowledge / knowledge graph |
| 649 | multimodal representation / generative media |
| 650 | AI memory |
| 651 | personalization / recommendation |
| 658 | social intelligence |
| 661 | value / goal / motivation |
| 667 | organizations / institutions |
| 670 | population / society |
| 671 | economy / payment / finance |
| 672 | scientific knowledge production |
| 673 | education |
| 675 | legal semantics / rights / law |
| 676 | government / public administration |
| **677** | **culture / media / information / heritage / creative systems** |

677 **không sở hữu**:

- compiler media codec;
- Unicode primitive;
- neural foundation model;
- legal definition của copyright;
- payment ledger;
- generic knowledge graph;
- recommendation mathematics;
- government authority.

Nó sử dụng các layer đó.

---

# 4. Core abstraction

Mọi hệ thống văn hóa được quy về:

```text
Creator
    ↓
CreativeWork
    ↓
MediaAsset
    ↓
Publication
    ↓
Distribution
    ↓
Audience
    ↓
CulturalMemory
```

với provenance:

```text
Source
  ↓
Claim
  ↓
Evidence
  ↓
Work
  ↓
Transformation
  ↓
Publication
  ↓
Distribution
```

và preservation:

```text
Artifact
  ↓
Capture
  ↓
Digitization
  ↓
Catalog
  ↓
Preservation
  ↓
Archive
  ↓
Access
```

---

# 5. Fundamental type model

## 5.1 Culture

```axiom
struct Culture {
    id: CultureId
    name: String
    description: String?
    language_set: Set<LanguageId>
    region_set: Set<RegionId>
    period: TimeRange?
}
```

## 5.2 CulturalSystem

```axiom
struct CulturalSystem {
    id: CulturalSystemId
    cultures: Set<CultureId>
    practices: Set<CulturalPracticeId>
    artifacts: Set<CulturalArtifactId>
    traditions: Set<TraditionId>
}
```

---

# 6. Cultural groups

```axiom
struct CulturalGroup {
    id: CulturalGroupId
    name: String
    description: String?
    culture_refs: Set<CultureId>
}
```

Axiom không tự suy luận:

```text
cultural group = race
cultural group = nationality
cultural group = religion
```

Các khái niệm này phải được mô hình hóa riêng khi cần.

---

# 7. Cultural practice

```axiom
struct CulturalPractice {
    id: CulturalPracticeId
    name: String
    description: String?
    participants: Set<CulturalGroupId>
    region: RegionId?
    period: TimeRange?
}
```

---

# 8. Tradition

```axiom
struct Tradition {
    id: TraditionId
    name: String
    origins: Set<SourceRef>
    practices: Set<CulturalPracticeId>
    versions: Set<TraditionVersionId>
}
```

Một tradition có thể thay đổi theo thời gian.

Không được coi:

```text
current_version == original_version
```

một cách mặc định.

---

# 9. Cultural artifact

```axiom
struct CulturalArtifact {
    id: ArtifactId
    type: ArtifactType
    title: String?
    creator: CreatorRef?
    creation_time: TimePoint?
    location: Location?
    provenance: ProvenanceId?
    media: MediaAssetRef?
}
```

---

# 10. Artwork

```axiom
struct Artwork {
    id: ArtworkId
    work: CreativeWorkId
    medium: ArtMedium
    creator_set: Set<CreatorId>
    edition: EditionId?
}
```

---

# 11. CreativeWork

Đây là abstraction trung tâm của creative layer.

```axiom
struct CreativeWork {
    id: WorkId
    title: String
    creators: Set<CreatorId>
    contributors: Set<ContributorId>
    genre: Set<GenreId>
    language: LanguageId?
    created_at: TimePoint?
    versions: Set<WorkVersionId>
    rights: RightsRef?
}
```

Một work có thể có nhiều:

```text
version
edition
translation
adaptation
remix
restoration
cut
release
localization
```

---

# 12. MediaAsset

```axiom
struct MediaAsset {
    id: MediaAssetId
    media_type: MediaType
    storage: ResourceRef
    codec: CodecId?
    duration: Duration?
    dimensions: Dimensions?
    checksum: Hash
    provenance: ProvenanceId
}
```

MediaAsset chỉ đại diện cho dữ liệu media.

Nó không tự mang nghĩa:

```text
journalism
fiction
truth
copyright
cultural importance
```

Các semantics nằm ở layer metadata.

---

# 13. Media types

Native enum:

```axiom
enum MediaType {
    Text
    Image
    Audio
    Video
    Animation
    Interactive
    Game
    Dataset
    3D
    Mixed
}
```

---

# 14. Publication

```axiom
struct Publication {
    id: PublicationId
    work: CreativeWorkId
    publisher: OrganizationRef?
    edition: EditionId?
    publication_time: TimePoint
    distribution: DistributionPlanId?
}
```

---

# 15. Article

```axiom
struct Article {
    id: ArticleId
    publication: PublicationId?
    title: String
    author_set: Set<CreatorId>
    body: Document
    claims: Set<ClaimId>
    sources: Set<SourceId>
    status: ArticleStatus
}
```

---

# 16. Book

```axiom
struct Book {
    id: BookId
    work: CreativeWorkId
    edition: EditionId
    isbn: String?
    chapters: List<ChapterId>
}
```

---

# 17. Journal / periodical

```axiom
struct Journal {
    id: JournalId
    title: String
    publisher: OrganizationRef
    issues: List<IssueId>
}
```

---

# 18. Broadcast

```axiom
struct Broadcast {
    id: BroadcastId
    program: CreativeWorkId
    channel: DistributionChannelId
    schedule: BroadcastSchedule
}
```

---

# 19. Podcast

```axiom
struct Podcast {
    id: PodcastId
    series: CreativeWorkId
    episodes: List<PodcastEpisodeId>
}
```

---

# 20. Performance

```axiom
struct Performance {
    id: PerformanceId
    work: CreativeWorkId
    performers: Set<CreatorId>
    venue: VenueId?
    time: TimeRange
}
```

---

# 21. Exhibition

```axiom
struct Exhibition {
    id: ExhibitionId
    title: String
    works: Set<CreativeWorkId>
    venue: VenueId
    curator_set: Set<CreatorId>
    period: TimeRange
}
```

---

# 22. Creator model

```axiom
struct Creator {
    id: CreatorId
    name: String
    roles: Set<CreatorRole>
}
```

Roles:

```axiom
enum CreatorRole {
    Author
    Artist
    Composer
    Director
    Writer
    Journalist
    Photographer
    Filmmaker
    Performer
    Musician
    Designer
    Animator
    GameDeveloper
    Translator
    Curator
    Researcher
    Editor
    Producer
    Other
}
```

Một creator có thể có nhiều role.

---

# 23. Contributor

```axiom
struct Contributor {
    id: ContributorId
    creator: CreatorId
    contribution: ContributionType
}
```

Không được coi:

```text
creator == sole_owner
```

Rights ownership thuộc layer rights/legal.

---

# 24. Publisher

```axiom
struct Publisher {
    id: PublisherId
    organization: OrganizationRef
    catalogs: Set<CatalogId>
}
```

---

# 25. Information model

Axiom phải phân biệt **content** và **epistemic status**.

```axiom
enum InformationClass {
    FactualClaim
    Report
    Analysis
    Opinion
    Commentary
    Fiction
    Satire
    Advertisement
    UserGenerated
    ArchivalRecord
    Testimony
    Synthetic
    Educational
    Promotional
    Other
}
```

Đây là classification metadata.

Không được coi classification là một chứng minh về độ đúng.

---

# 26. Claim

```axiom
struct Claim {
    id: ClaimId
    subject: EntityRef
    predicate: PredicateId
    object: EntityRef
    context: ClaimContext?
    information_class: InformationClass
    status: ClaimStatus
}
```

---

# 27. ClaimStatus

```axiom
enum ClaimStatus {
    Supported
    Contradicted
    Disputed
    Unverified
    Withdrawn
    Historical
    ContextDependent
}
```

Không tồn tại primitive:

```axiom
Claim.is_absolute_truth()
```

Axiom chỉ lưu:

```text
claim
evidence
source
verification result
method
time
verifier
confidence
```

---

# 28. Source

```axiom
struct Source {
    id: SourceId
    type: SourceType
    locator: SourceLocator?
    publisher: OrganizationRef?
    author: CreatorRef?
    published_at: TimePoint?
    captured_at: TimePoint?
}
```

---

# 29. Evidence

```axiom
struct Evidence {
    id: EvidenceId
    source: SourceId
    supports: Set<ClaimId>
    contradicts: Set<ClaimId>
    excerpt: ContentRef?
    provenance: ProvenanceId
}
```

---

# 30. Citation

```axiom
struct Citation {
    source: SourceId
    target: ClaimId | DocumentRef
    locator: SourceLocator?
    context: String?
}
```

Citation là dữ liệu có cấu trúc, không chỉ là chuỗi URL.

---

# 31. Fact-check

```axiom
struct FactCheck {
    id: FactCheckId
    claim: ClaimId
    evidence: Set<EvidenceId>
    methodology: MethodologyRef
    result: FactCheckResult
    verifier: OrganizationRef | CreatorRef
    performed_at: TimePoint
}
```

```axiom
enum FactCheckResult {
    Supported
    PartiallySupported
    Contradicted
    Inconclusive
    ContextRequired
}
```

Fact-check engine không phải "truth oracle".

---

# 32. Editorial workflow

```text
Pitch
 ↓
Assignment
 ↓
Reporting
 ↓
SourceCollection
 ↓
Draft
 ↓
FactCheck
 ↓
EditorialReview
 ↓
Approval
 ↓
Publish
 ↓
Distribution
 ↓
Correction / Update / Retraction
 ↓
Archive
```

---

# 33. EditorialAssignment

```axiom
struct EditorialAssignment {
    id: AssignmentId
    topic: String
    reporter: CreatorId
    editor: CreatorId?
    deadline: TimePoint?
    source_requirements: Set<SourceRequirement>
}
```

---

# 34. EditorialReview

```axiom
struct EditorialReview {
    id: ReviewId
    article: ArticleId
    reviewer: CreatorId
    findings: List<ReviewFinding>
    decision: EditorialDecision
}
```

---

# 35. Correction

```axiom
struct Correction {
    id: CorrectionId
    publication: PublicationId
    target_version: WorkVersionId
    corrected_version: WorkVersionId
    reason: String
    published_at: TimePoint
}
```

Không overwrite lịch sử.

---

# 36. Retraction

```axiom
struct Retraction {
    id: RetractionId
    publication: PublicationId
    target: WorkVersionId
    reason: String
    authority: CreatorRef | OrganizationRef
    time: TimePoint
}
```

Retraction không xóa bản archive.

---

# 37. Provenance

Provenance là một thành phần bắt buộc đối với media quan trọng.

```axiom
struct Provenance {
    id: ProvenanceId
    origin: ProvenanceNode
    transformations: List<TransformationStep>
    current: ProvenanceNode
    integrity: IntegrityProof?
}
```

---

# 38. TransformationStep

```axiom
struct TransformationStep {
    operation: TransformationType
    actor: ActorRef
    input: ContentRef
    output: ContentRef
    timestamp: TimePoint
    tool: ToolRef?
}
```

Ví dụ:

```text
camera
→ raw
→ denoise
→ color grade
→ upscale
→ subtitle
→ dub
→ encode
→ publish
```

có thể được biểu diễn đầy đủ.

---

# 39. AI-generated content

Axiom phải có first-class metadata cho nội dung AI.

```axiom
struct SyntheticMedia {
    asset: MediaAssetId
    generated: Bool
    assisted: Bool
    model: ModelRef?
    model_version: String?
    generation_time: TimePoint?
    transformation_chain: List<TransformationStep>
    disclosure: SyntheticDisclosure
}
```

---

# 40. SyntheticDisclosure

```axiom
enum SyntheticDisclosure {
    None
    AIAssisted
    AIGenerated
    AITransformed
    Unknown
}
```

`Unknown` không có nghĩa là "human-created".

---

# 41. AI media provenance

Nếu pipeline hỗ trợ:

```text
prompt
model
model version
seed
input assets
reference assets
tool
operator
timestamp
output hash
```

thì runtime có thể lưu:

```axiom
struct GenerationRecord {
    model: ModelRef
    version: String
    inputs: List<ContentRef>
    parameters: Map<String, Value>
    operator: ActorRef?
    timestamp: TimePoint
    output: ContentRef
}
```

---

# 42. Không có primitive impersonation abuse

Core không cung cấp abstraction kiểu:

```text
ForgePersonIdentity()
FakeStatementAsPerson()
UndisclosedImpersonation()
```

Synthetic media phải giữ provenance và disclosure metadata khi pipeline có khả năng xác định nguồn gốc.

---

# 43. Rights metadata

677 quản lý operational content-right metadata.

```axiom
struct ContentRights {
    work: CreativeWorkId
    holder: RightsHolderRef
    rights: Set<UsageRight>
    territories: Set<RegionId>
    valid_from: TimePoint?
    valid_until: TimePoint?
    license: LicenseId?
}
```

Legal semantics vẫn thuộc BOOTSTRAP-675.

---

# 44. License

```axiom
struct ContentLicense {
    id: LicenseId
    rights: Set<UsageRight>
    restrictions: Set<UsageRestriction>
    attribution_required: Bool
    derivative_allowed: Bool
    commercial_allowed: Bool
    expires_at: TimePoint?
}
```

677 không tự định nghĩa luật copyright.

---

# 45. Attribution

```axiom
struct Attribution {
    work: CreativeWorkId
    creator: CreatorId
    role: CreatorRole
    ordering: Int?
}
```

---

# 46. Distribution

```axiom
struct DistributionPlan {
    id: DistributionPlanId
    channels: Set<DistributionChannelId>
    territories: Set<RegionId>
    schedule: DistributionSchedule?
}
```

---

# 47. DistributionChannel

```axiom
struct DistributionChannel {
    id: DistributionChannelId
    type: DistributionChannelType
    endpoint: Endpoint?
}
```

Types:

```text
Print
Broadcast
Streaming
Web
Mobile
Cinema
Podcast
Library
Archive
Museum
Physical
Interactive
Game
Other
```

---

# 48. Audience

```axiom
struct Audience {
    id: AudienceId
    constraints: AudienceConstraintSet
}
```

Audience model không đồng nghĩa với political preference.

---

# 49. Discovery

677 cung cấp substrate cho:

```text
search
catalog
browse
filter
faceted discovery
semantic discovery
similarity
related works
collection navigation
```

Recommendation cá nhân hóa vẫn thuộc BOOTSTRAP-651.

---

# 50. ContentIndex

```axiom
struct ContentIndex {
    id: IndexId
    sources: Set<ContentSource>
    fields: Set<IndexField>
    version: IndexVersion
}
```

Có thể xây:

```text
full-text index
metadata index
semantic index
multimodal index
temporal index
provenance index
citation index
heritage index
```

---

# 51. Search

Native operation:

```axiom
search(
    index,
    query,
    filter?,
    sort?,
    limit?
) -> SearchResult
```

Search result phải có provenance:

```axiom
struct SearchResult {
    item: ContentRef
    score: Float?
    matched_fields: Set<String>
    explanation: SearchExplanation?
}
```

---

# 52. Recommendation boundary

677 có thể cung cấp:

```text
candidate generation
content similarity
catalog relationships
contextual discovery
```

nhưng:

```text
user preference learning
personal ranking
adaptive recommendation
```

thuộc BOOTSTRAP-651.

---

# 53. Cultural artifact preservation

```axiom
struct PreservationPlan {
    id: PreservationPlanId
    artifact: ArtifactId
    target_formats: Set<FormatId>
    replication_policy: ReplicationPolicy
    integrity_policy: IntegrityPolicy
}
```

---

# 54. Archive

```axiom
struct Archive {
    id: ArchiveId
    institution: OrganizationRef?
    collections: Set<CollectionId>
    preservation_policy: PreservationPolicy
}
```

---

# 55. ArchiveRecord

```axiom
struct ArchiveRecord {
    id: ArchiveRecordId
    artifact: ArtifactId
    acquisition: AcquisitionRecord
    provenance: ProvenanceId
    preservation: PreservationPlanId?
    access_policy: AccessPolicy
}
```

---

# 56. Library

```axiom
struct Library {
    id: LibraryId
    catalog: CatalogId
    collections: Set<CollectionId>
}
```

---

# 57. Catalog

```axiom
struct Catalog {
    id: CatalogId
    records: Set<CatalogRecordId>
}
```

CatalogRecord hỗ trợ:

```text
creator
title
subject
language
date
edition
identifier
location
rights
provenance
related works
```

---

# 58. Museum

```axiom
struct Museum {
    id: MuseumId
    collections: Set<CollectionId>
    exhibitions: Set<ExhibitionId>
}
```

---

# 59. Heritage

```axiom
struct Heritage {
    id: HeritageId
    type: HeritageType
    name: String
    provenance: ProvenanceId?
}
```

```axiom
enum HeritageType {
    Tangible
    Intangible
    NaturalCultural
    Documentary
    Digital
    Mixed
}
```

---

# 60. HeritageSite

```axiom
struct HeritageSite {
    id: HeritageSiteId
    location: Location
    heritage: HeritageId
    preservation_state: PreservationState
}
```

---

# 61. HeritageObject

```axiom
struct HeritageObject {
    id: HeritageObjectId
    heritage: HeritageId
    physical_state: PhysicalState?
    digital_representation: MediaAssetId?
}
```

---

# 62. Intangible heritage

```axiom
struct IntangibleHeritage {
    id: IntangibleHeritageId
    practice: CulturalPracticeId
    transmission_methods: Set<TransmissionMethod>
    community_refs: Set<CulturalGroupId>
}
```

---

# 63. Oral history

```axiom
struct OralHistory {
    id: OralHistoryId
    speaker: CreatorRef?
    interviewer: CreatorRef?
    recording: MediaAssetId
    transcript: Document?
    provenance: ProvenanceId
    consent: ConsentRef?
}
```

Oral history phải phân biệt:

```text
testimony
memory
historical claim
verified historical fact
```

---

# 64. Digitization

```axiom
struct DigitizationJob {
    id: DigitizationJobId
    source_artifact: ArtifactId
    output_asset: MediaAssetId?
    capture_method: CaptureMethod
    operator: ActorRef
    timestamp: TimePoint
}
```

---

# 65. Restoration

```axiom
struct RestorationJob {
    id: RestorationJobId
    source: MediaAssetId | ArtifactId
    target: MediaAssetId
    operations: List<RestorationOperation>
    operator: ActorRef
}
```

Restoration không được ghi đè source.

---

# 66. Translation

```axiom
struct Translation {
    source: ContentRef
    target: ContentRef
    source_language: LanguageId
    target_language: LanguageId
    translator: CreatorRef?
    machine_assisted: Bool
}
```

---

# 67. Localization

Localization bao gồm:

```text
language
date
number
currency
cultural references
UI
imagery
audio
subtitles
legal notices
```

Nhưng không được mặc định thay đổi meaning của original work.

---

# 68. Subtitle

```axiom
struct SubtitleTrack {
    language: LanguageId
    segments: List<SubtitleSegment>
}
```

```axiom
struct SubtitleSegment {
    start: Duration
    end: Duration
    text: String
}
```

---

# 69. Dubbing

```axiom
struct DubTrack {
    source: MediaAssetId
    language: LanguageId
    voice_source: VoiceRef?
    script: Document
    media: MediaAssetId
}
```

---

# 70. Creative project

```axiom
struct CreativeProject {
    id: CreativeProjectId
    title: String
    works: Set<CreativeWorkId>
    assets: Set<MediaAssetId>
    contributors: Set<ContributorId>
    stages: List<ProductionStage>
}
```

---

# 71. Production pipeline

```text
Concept
 ↓
PreProduction
 ↓
Production
 ↓
Capture
 ↓
Editing
 ↓
Review
 ↓
PostProduction
 ↓
Mastering
 ↓
Localization
 ↓
Publishing
 ↓
Distribution
 ↓
Archive
```

---

# 72. Cultural event

```axiom
struct CulturalEvent {
    id: CulturalEventId
    name: String
    type: CulturalEventType
    venue: VenueId?
    works: Set<CreativeWorkId>
    time: TimeRange
}
```

---

# 73. Festival

```axiom
struct Festival {
    id: FestivalId
    name: String
    events: Set<CulturalEventId>
    editions: List<FestivalEditionId>
}
```

---

# 74. Collective cultural memory

Đây là một abstraction quan trọng.

```axiom
struct CulturalMemory {
    id: CulturalMemoryId
    subject: EntityRef
    records: Set<MemoryRecordId>
    sources: Set<SourceId>
    temporal_scope: TimeRange?
}
```

Memory record:

```axiom
struct MemoryRecord {
    id: MemoryRecordId
    content: ContentRef
    source: SourceId?
    testimony: Bool
    provenance: ProvenanceId?
    status: MemoryStatus
}
```

---

# 75. MemoryStatus

```axiom
enum MemoryStatus {
    Testimonial
    Archival
    Documented
    Oral
    Contested
    Interpretive
    Unverified
}
```

Axiom không được tự biến:

```text
collective memory
```

thành:

```text
objective historical truth
```

---

# 76. Cultural versioning

Culture không phải immutable database.

Mọi artifact quan trọng có thể có:

```text
origin
version
edition
interpretation
adaptation
restoration
translation
reinterpretation
```

Runtime phải bảo tồn lineage.

---

# 77. Cultural graph

677 cung cấp graph layer chuyên biệt:

```text
Creator
  ↓ creates
Work
  ↓ published_as
Publication
  ↓ distributed_by
Channel
  ↓ consumed_by
Audience

Artifact
  ↓ preserved_by
Institution

Tradition
  ↓ practiced_by
CulturalGroup

Claim
  ↓ supported_by
Evidence
  ↓ derived_from
Source
```

Semantic ontology nâng cao vẫn thuộc 645.

---

# 78. Information integrity

Runtime phải hỗ trợ:

```text
source provenance
claim provenance
citation
version history
correction
retraction
authorship
publication time
modification history
AI-generation disclosure
content hash
```

Không có primitive:

```text
make_content_true()
```

---

# 79. Content moderation

677 chỉ cung cấp infrastructure:

```axiom
struct ModerationDecision {
    content: ContentRef
    policy: PolicyRef
    classifier: ModelRef?
    result: ModerationResult
    confidence: Float?
    reviewer: ActorRef?
    appeal: AppealRef?
}
```

Policy semantics đến từ:

```text
639
675
application policy
institution policy
```

---

# 80. ModerationResult

```axiom
enum ModerationResult {
    Allow
    Restrict
    Label
    AgeGate
    Review
    Remove
    Restore
    Unknown
}
```

Không được hard-code một bộ giá trị văn hóa phổ quát.

---

# 81. Moderation appeal

```axiom
struct ModerationAppeal {
    decision: ModerationDecisionId
    appellant: ActorRef
    reason: String
    submitted_at: TimePoint
    resolution: AppealResolution?
}
```

---

# 82. Public information

Public information có thể có:

```text
official
journalistic
academic
archival
community
user-generated
synthetic
commercial
```

Source type phải được lưu riêng.

Không được mặc định:

```text
official == true
```

hoặc:

```text
popular == true
```

---

# 83. Information provenance chain

Ví dụ:

```text
RAW_SOURCE
   ↓
TRANSCRIPTION
   ↓
TRANSLATION
   ↓
EDIT
   ↓
FACT_CHECK
   ↓
ARTICLE
   ↓
SYNDICATION
   ↓
VIDEO
   ↓
SOCIAL_CLIP
```

Runtime phải truy ngược được chain.

---

# 84. Content identity

Mỗi content object có:

```text
stable identity
version identity
content hash
semantic metadata
provenance
rights
creation time
modification time
```

Do đó:

```text
same work
!= same binary
```

---

# 85. Immutable history

Correction/update/retraction phải tạo version mới.

Không:

```axiom
database.overwrite(old_article)
```

nếu artifact đó đã được public hoặc archived.

---

# 86. Archive immutability

Archive record có thể:

```text
append
annotate
link
supersede
restrict
```

nhưng không được silently destroy provenance.

---

# 87. Creative industry boundary

677 mô hình:

```text
studio
production
catalog
creator
work
distribution
license
rights
```

Nhưng:

```text
payment
invoice
royalty settlement
tax
market transaction
```

được chuyển sang BOOTSTRAP-671.

---

# 88. Rights/economy bridge

Ví dụ:

```axiom
royalty_report = culture.calculate_usage(
    work,
    distribution_period
)

economy.settle(
    royalty_report
)
```

677 không trở thành financial ledger.

---

# 89. Cultural institution bridge

677 sử dụng BOOTSTRAP-667:

```text
Museum
Library
Archive
Publisher
Studio
Newsroom
Festival
CulturalCenter
```

là các tổ chức.

677 cung cấp semantics domain.

---

# 90. Government bridge

677 có thể cung cấp:

```text
public archive
public media
heritage registry
cultural program
public information
```

nhưng quyền hành chính thuộc 676.

---

# 91. Legal bridge

677 có:

```text
rights metadata
license metadata
consent metadata
usage constraints
```

675 quyết định semantics pháp lý.

---

# 92. Knowledge bridge

677 tạo:

```text
source
claim
citation
publication
artifact
cultural entity
```

645 có thể xây:

```text
knowledge graph
semantic graph
entity resolution
reasoning
```

từ dữ liệu đó.

---

# 93. AI foundation bridge

649 cung cấp:

```text
image generation
audio generation
video generation
multimodal embedding
speech synthesis
vision
```

677 cung cấp:

```text
creative context
provenance
work identity
publication
rights
cultural metadata
```

---

# 94. AI memory bridge

650 lưu:

```text
creator memory
editorial context
project history
cultural references
```

677 giữ:

```text
persistent cultural artifacts
```

Hai khái niệm không được trộn.

---

# 95. Cultural simulation

677 hỗ trợ simulation:

```text
cultural diffusion
media diffusion
language interaction
creative ecosystem
audience behavior
heritage preservation
information propagation
collective memory evolution
```

Simulation phải tách khỏi live state.

---

# 96. Simulation object

```axiom
struct CulturalSimulation {
    id: SimulationId
    world_model: WorldModelRef
    cultural_state: CulturalState
    media_state: MediaState
    population_model: PopulationModelRef?
    parameters: Map<String, Value>
}
```

---

# 97. Simulation operations

```text
create
initialize
step
run
pause
checkpoint
restore
branch
compare
export
```

Không được ghi simulation trực tiếp vào production cultural state.

---

# 98. Cultural metrics

Có thể đo:

```text
work_count
publication_count
archive_coverage
language_coverage
translation_coverage
heritage_preservation_rate
media_reach
source_diversity
citation_density
correction_rate
content_provenance_coverage
creator_concentration
catalog_completeness
```

Không nên có primitive:

```text
culture_quality_score
culture_superiority_score
human_cultural_value_score
```

vì đây là những đánh giá normative không thuộc substrate.

---

# 99. Cultural diversity

Runtime có thể thống kê:

```text
language diversity
creator diversity
genre diversity
source diversity
regional coverage
historical coverage
```

nhưng không được tự suy ra:

```text
culture A > culture B
```

---

# 100. Recommendation safety boundary

677 không có API:

```text
persuade_user_to_believe(...)
```

hoặc:

```text
target_political_preference(...)
```

Core discovery chỉ nhận:

```text
query
context
content
explicit user preference
policy
```

và trả về candidate/ranking metadata.

---

# 101. Content classification

```axiom
struct ContentLabel {
    label: LabelType
    source: LabelSource
    confidence: Float?
    timestamp: TimePoint
}
```

Label source:

```text
Author
Publisher
AutomatedModel
Reviewer
Archive
Institution
Community
Unknown
```

---

# 102. Search ranking transparency

Search engine nên hỗ trợ:

```axiom
struct SearchExplanation {
    matched_terms: Set<String>
    semantic_matches: Set<EntityRef>
    filters: Set<Filter>
    ranking_features: Set<RankingFeature>
}
```

Không bắt buộc expose proprietary implementation details, nhưng runtime phải có audit hooks.

---

# 103. Media collections

```axiom
struct Collection {
    id: CollectionId
    title: String
    items: Set<ContentRef>
    curator: ActorRef?
    description: String?
}
```

Collection có thể là:

```text
library collection
museum collection
playlist
archive collection
research corpus
creative reference board
```

---

# 104. Corpus

```axiom
struct CulturalCorpus {
    id: CorpusId
    items: Set<ContentRef>
    selection_policy: SelectionPolicy
    provenance: ProvenanceId
}
```

Dùng cho:

```text
AI training
digital humanities
historical research
linguistic research
cultural analytics
```

với data-governance từ 640.

---

# 105. AI training data bridge

677 có thể mô tả:

```text
dataset membership
creator attribution
license
provenance
consent
source
transformation
```

Nhưng training execution thuộc 643.

---

# 106. Translation memory

```axiom
struct TranslationMemory {
    source_language: LanguageId
    target_language: LanguageId
    segments: Set<TranslationMemoryEntry>
}
```

---

# 107. Localization memory

```axiom
struct LocalizationMemory {
    source_locale: LocaleId
    target_locale: LocaleId
    mappings: Map<String, LocalizedValue>
}
```

---

# 108. Media pipeline

Native pipeline:

```text
Import
 → Decode
 → Transform
 → Analyze
 → Edit
 → Compose
 → Encode
 → Validate
 → Publish
 → Distribute
 → Archive
```

Pipeline có thể chạy:

```text
CPU
GPU
NPU
distributed workers
```

thông qua các runtime thấp hơn.

---

# 109. Zero-copy media

Media pipeline phải hỗ trợ:

```text
memory mapping
buffer sharing
GPU buffer
DMA-compatible buffer
streaming
chunked processing
```

để tránh:

```text
decode → copy → transform → copy → encode
```

không cần thiết.

---

# 110. Streaming

Native APIs:

```axiom
MediaReader
MediaWriter
MediaDecoder
MediaEncoder
MediaTransformer
MediaMuxer
MediaDemuxer
```

phải hỗ trợ streaming.

Không bắt buộc load toàn bộ file vào RAM.

---

# 111. Large archive

Archive có thể chứa:

```text
TB
PB
EB
```

thông qua:

```text
chunking
content addressing
deduplication
compression
tiered storage
remote storage
cold storage
```

Các primitive storage thấp hơn lấy từ 611/613.

---

# 112. Content-addressed identity

Media artifact có thể có:

```axiom
ContentId = Hash(content)
```

cho immutable binary.

Nhưng semantic work identity:

```axiom
WorkId
```

được tách riêng.

---

# 113. Work vs Asset

Ví dụ:

```text
Movie
 ├── WorkId
 ├── MasterAsset
 ├── 4KAsset
 ├── 1080pAsset
 ├── Trailer
 ├── SubtitleVI
 ├── SubtitleEN
 ├── DubVI
 └── DubJP
```

Tất cả có thể thuộc một `CreativeWork`.

---

# 114. Version graph

Không chỉ linear version:

```text
v1
 ├── v2
 │    └── v3
 └── restored-v1
      └── remaster
```

Runtime phải hỗ trợ DAG lineage.

---

# 115. Cultural preservation integrity

Mỗi preservation operation nên lưu:

```text
source hash
output hash
operator
tool
tool version
parameters
timestamp
```

---

# 116. Metadata schema

Metadata phải hỗ trợ:

```text
strongly typed core fields
extension fields
namespaces
versioning
schema migration
unknown-field preservation
```

Không ép mọi nền văn hóa vào một schema quá hẹp.

---

# 117. Extensibility

Culture domain phải hỗ trợ custom:

```axiom
extension CulturalMetadata {
    field local_identifier: String
    field community_definition: String
}
```

Community-specific metadata không được coi là invalid chỉ vì không nằm trong global schema.

---

# 118. Cultural ontology boundary

677 không ép một ontology duy nhất.

Cho phép:

```text
institution ontology
community ontology
academic ontology
archive ontology
publisher ontology
application ontology
```

cùng tồn tại.

---

# 119. Conflict handling

Nếu hai nguồn định nghĩa khác nhau:

```text
Source A → Tradition X
Source B → Tradition Y
```

runtime lưu cả hai provenance.

Không tự overwrite.

---

# 120. Interpretation

```axiom
struct Interpretation {
    work: CreativeWorkId
    interpreter: ActorRef
    statement: Document
    sources: Set<SourceId>
    created_at: TimePoint
}
```

Interpretation không được lưu như objective source fact.

---

# 121. Cultural annotation

```axiom
struct CulturalAnnotation {
    target: ContentRef
    annotator: ActorRef
    concept: CulturalConceptRef
    confidence: Float?
    source: SourceId?
}
```

---

# 122. Archive access

Access policy:

```text
Open
Restricted
Embargoed
Private
InstitutionOnly
ResearchOnly
ConsentRequired
Unavailable
```

Legal enforcement vẫn phụ thuộc 675/603.

---

# 123. Consent

Đối với nội dung có người tham gia:

```axiom
struct CulturalConsent {
    subject: ActorRef
    purpose: ConsentPurpose
    scope: ConsentScope
    granted_at: TimePoint
    expires_at: TimePoint?
    revoked_at: TimePoint?
}
```

Consent semantics phải tích hợp 640 và 675.

---

# 124. Personal data boundary

677 không biến cultural archive thành hệ thống unrestricted PII.

Sensitive personal data phải đi qua:

```text
640 Data Governance
603 Security
675 Legal
```

---

# 125. Provenance verification

Native operation:

```axiom
verify_provenance(asset)
    -> ProvenanceVerification
```

Kết quả:

```text
Verified
PartiallyVerified
BrokenChain
Unknown
Invalid
```

---

# 126. Content authenticity

Authenticity phải phân biệt:

```text
binary integrity
source authenticity
creator attribution
publication authenticity
historical authenticity
```

Không gộp thành một boolean:

```text
is_authentic
```

---

# 127. Editorial audit

Newsroom có thể query:

```text
who created this?
who edited it?
which sources were used?
which claims were checked?
which model assisted?
when was it changed?
what was corrected?
why was it retracted?
```

---

# 128. Media audit

Tương tự:

```text
original asset
transformations
AI operations
human edits
encoding
publication
distribution
```

---

# 129. AI-assisted editorial workflow

```text
SourceCollection
 ↓
AIExtraction
 ↓
HumanReview
 ↓
ClaimGeneration
 ↓
EvidenceLinking
 ↓
FactCheck
 ↓
HumanEditorialDecision
 ↓
Publish
```

AI output không tự trở thành editorial decision.

---

# 130. AI-assisted creative workflow

```text
Concept
 ↓
Generation
 ↓
Selection
 ↓
HumanEdit
 ↓
Transformation
 ↓
Review
 ↓
Publish
```

---

# 131. AI model attribution

Nếu model đóng góp đáng kể:

```axiom
struct AIAssistance {
    model: ModelRef
    version: String
    operation: AIOperation
    contribution: ContributionLevel
}
```

---

# 132. ContributionLevel

```axiom
Minor
Assisted
Substantial
Primary
Unknown
```

Không tự biến contribution thành legal authorship.

---

# 133. Cultural memory preservation

Memory system phải hỗ trợ:

```text
source
speaker
date
place
recording
transcript
translation
context
later interpretation
contradiction
correction
```

---

# 134. Temporal cultural model

Cultural state:

```text
Culture(t0)
Culture(t1)
Culture(t2)
...
```

phải giữ historical lineage.

Không được collapse tất cả vào current state.

---

# 135. Cultural diffusion

Simulation primitives:

```axiom
diffuse(
    artifact,
    population,
    channel,
    parameters
)
```

có thể mô phỏng:

```text
language spread
music spread
fashion spread
media spread
memes
traditions
creative styles
```

---

# 136. Media diffusion

```axiom
struct MediaDiffusionEvent {
    content: ContentRef
    source: ActorRef
    destination: AudienceRef
    channel: DistributionChannelId
    time: TimePoint
}
```

---

# 137. Collective memory evolution

Simulation có thể mô hình:

```text
creation
remembering
forgetting
reinterpretation
archiving
rediscovery
contestation
```

nhưng simulation không tự sửa historical archive.

---

# 138. Cultural ecosystem

```axiom
struct CulturalEcosystem {
    creators: Set<CreatorId>
    institutions: Set<OrganizationRef>
    works: Set<CreativeWorkId>
    channels: Set<DistributionChannelId>
    audiences: Set<AudienceId>
}
```

---

# 139. Ecosystem metrics

Có thể tính:

```text
creator_count
institution_count
work_count
distribution_reach
language_coverage
archive_coverage
production_rate
publication_rate
```

Các metrics chỉ mang tính descriptive.

---

# 140. Creative production scheduling

677 có thể tạo:

```axiom
ProductionPlan
ProductionStage
AssetDependency
Deadline
Milestone
ReviewGate
ReleaseGate
```

Scheduling engine nâng cao có thể sử dụng BOOTSTRAP-652/629.

---

# 141. Cultural workflow state machine

Mỗi workflow phải có:

```text
state
transition
actor
timestamp
reason
provenance
```

Không có hidden transition.

---

# 142. Event sourcing

Các domain quan trọng có thể lưu:

```text
WorkCreated
AssetImported
SourceAdded
ClaimCreated
EvidenceLinked
ArticleDrafted
ArticleReviewed
ArticlePublished
ArticleCorrected
ArticleRetracted
AssetTransformed
LicenseGranted
DistributionStarted
ArchiveCreated
```

---

# 143. Deterministic replay

Workflow phải hỗ trợ:

```axiom
replay(workflow_id)
```

để tái dựng:

```text
state
decision path
provenance
versions
```

---

# 144. Audit invariants

Không được có:

```text
publication without author/creator metadata
correction without target version
retraction without target
transformation without provenance
archive replacement without lineage
AI-generated media without generation metadata when declared
```

---

# 145. Native commands

CLI namespace:

```text
axiom culture
axiom culture list
axiom culture inspect
axiom culture status
```

---

# 146. Art commands

```text
axiom art list
axiom art inspect
axiom art create
axiom art version
axiom art archive
```

---

# 147. Media commands

```text
axiom media import
axiom media inspect
axiom media transform
axiom media encode
axiom media decode
axiom media compose
axiom media publish
axiom media archive
```

---

# 148. Publication commands

```text
axiom publication create
axiom publication inspect
axiom publication publish
axiom publication correct
axiom publication retract
axiom publication archive
```

---

# 149. Journalism commands

```text
axiom editorial pitch
axiom editorial assign
axiom editorial draft
axiom editorial review
axiom editorial factcheck
axiom editorial publish
axiom editorial correct
axiom editorial retract
```

---

# 150. Provenance commands

```text
axiom provenance inspect
axiom provenance verify
axiom provenance trace
axiom provenance export
```

---

# 151. Rights commands

```text
axiom rights inspect
axiom rights license
axiom rights grant
axiom rights revoke
axiom rights attribute
```

---

# 152. Archive commands

```text
axiom archive create
axiom archive add
axiom archive inspect
axiom archive preserve
axiom archive digitize
axiom archive restore
axiom archive verify
```

---

# 153. Heritage commands

```text
axiom heritage list
axiom heritage inspect
axiom heritage register
axiom heritage preserve
axiom heritage digitize
axiom heritage restore
```

---

# 154. Library commands

```text
axiom library catalog
axiom library search
axiom library add
axiom library checkout
axiom library preserve
```

---

# 155. Translation commands

```text
axiom translate
axiom localize
axiom subtitle
axiom dub
```

---

# 156. Discovery commands

```text
axiom media index
axiom media search
axiom media related
axiom media discover
```

---

# 157. Cultural simulation commands

```text
axiom culture-sim create
axiom culture-sim initialize
axiom culture-sim step
axiom culture-sim run
axiom culture-sim checkpoint
axiom culture-sim restore
axiom culture-sim branch
axiom culture-sim compare
```

---

# 158. Native IR operations

Compiler/runtime IR cần các operation:

```text
CultureCreate
CultureLink
CulturalGroupCreate
PracticeCreate
TraditionCreate

ArtifactCreate
ArtworkCreate
CreativeWorkCreate
WorkVersionCreate

MediaImport
MediaTransform
MediaAnalyze
MediaEncode
MediaDecode

PublicationCreate
ArticleCreate
BookCreate
JournalCreate
BroadcastCreate
PodcastCreate

SourceCreate
ClaimCreate
EvidenceCreate
EvidenceLink
CitationCreate
FactCheckCreate

EditorialAssign
DraftCreate
EditorialReview
Publish
Correct
Retract

ProvenanceAttach
ProvenanceVerify
SyntheticMediaMark

RightsCreate
LicenseGrant
LicenseRevoke
AttributionCreate

DistributionCreate
ChannelCreate

CollectionCreate
CatalogCreate
ArchiveCreate
ArchiveRecordCreate

DigitizationCreate
DigitizationRun
PreservationCreate
RestorationCreate

HeritageCreate
HeritageSiteCreate
HeritageObjectCreate
OralHistoryCreate

TranslationCreate
LocalizationCreate
SubtitleCreate
DubCreate

CreativeProjectCreate
ProductionPlanCreate
ExhibitionCreate
FestivalCreate
CulturalEventCreate

ContentIndexBuild
ContentSearch
ContentDiscover

ModerationEvaluate
ContentLabelCreate
ModerationAppeal

CulturalMemoryCreate
MemoryRecordCreate

CultureSimulationCreate
CultureSimulationStep
CultureSimulationRun
CultureSimulationCheckpoint
CultureSimulationRestore
```

---

# 159. Runtime profiles

```text
AXCULTURE_NONE
AXCULTURE_CORE
AXCULTURE_ART
AXCULTURE_CREATIVE
AXCULTURE_MEDIA
AXCULTURE_JOURNALISM
AXCULTURE_PUBLICATION
AXCULTURE_AUDIO
AXCULTURE_VIDEO
AXCULTURE_IMAGE
AXCULTURE_INTERACTIVE
AXCULTURE_PUBLISHING
AXCULTURE_DISTRIBUTION
AXCULTURE_PROVENANCE
AXCULTURE_INFORMATION
AXCULTURE_FACTCHECK
AXCULTURE_ARCHIVE
AXCULTURE_LIBRARY
AXCULTURE_MUSEUM
AXCULTURE_HERITAGE
AXCULTURE_DIGITIZATION
AXCULTURE_PRESERVATION
AXCULTURE_TRANSLATION
AXCULTURE_LOCALIZATION
AXCULTURE_AI_MEDIA
AXCULTURE_CREATIVE_INDUSTRY
AXCULTURE_RIGHTS
AXCULTURE_DISCOVERY
AXCULTURE_RECOMMENDATION
AXCULTURE_CULTURAL_MEMORY
AXCULTURE_SIMULATION
AXCULTURE_DISTRIBUTED
AXCULTURE_GPU
AXCULTURE_WASM
AXCULTURE_MOBILE
AXCULTURE_GLOBAL
AXCULTURE_FULL
```

---

# 160. Annotations

Native annotations:

```text
@culture
@cultural_system
@cultural_group
@cultural_practice
@tradition
@artifact
@artwork
@creative_work
@media
@media_asset
@publication
@article
@book
@journal
@broadcast
@podcast
@video
@audio
@image
@performance
@exhibition
@museum
@archive
@library
@heritage
@heritage_site
@heritage_object
@intangible_heritage
@oral_history
@creator
@author
@publisher
@editor
@journalist
@curator
@source
@claim
@evidence
@citation
@fact_check
@correction
@retraction
@content_provenance
@content_rights
@license
@distribution
@editorial_workflow
@moderation
@content_label
@cultural_memory
@preservation
@digitization
@restoration
@translation
@localization
@subtitling
@dubbing
@creative_project
@festival
@cultural_event
@creative_industry
@media_simulation
@cultural_simulation
@synthetic_media
@ai_media
```

---

# 161. File extensions

Native domain extensions:

```text
.axculture
.axart
.axwork
.axmedia
.axpublication
.axarticle
.axbook
.axjournal
.axbroadcast
.axpodcast
.axvideo
.axaudio
.aximage
.axperformance
.axexhibition
.axmuseum
.axarchive
.axlibrary
.axheritage
.axartifact
.axoralhistory
.axclaim
.axevidence
.axfactcheck
.axprovenance
.axrights
.axlicense
.axeditorial
.axmoderation
.axpreservation
.axculturemodel
.axculturesim
.axcreativeproject
```

Các extension này là semantic/document formats; binary storage vẫn có thể sử dụng generic Axiom container.

---

# 162. Security

Culture/media runtime phải tích hợp:

```text
603 Security
604 IPC
609 Network
610 Crypto
611 Storage
613 Package
640 Data Governance
675 Legal
```

Đặc biệt:

```text
content signing
provenance signing
archive integrity
access control
license enforcement
creator account security
```

---

# 163. Distributed operation

Media platform quy mô lớn phải hỗ trợ:

```text
distributed ingest
distributed transcoding
distributed indexing
distributed archive
distributed search
content replication
edge distribution
cache
event propagation
```

Không được yêu cầu toàn bộ media đi qua một process.

---

# 164. GPU operation

Các workload:

```text
image processing
video processing
audio processing
embedding
OCR
speech recognition
speech synthesis
vision
generative media
```

có thể sử dụng GPU/NPU thông qua 614/615/616/643/649.

677 chỉ orchestration semantics.

---

# 165. WASM

WASM profile hỗ trợ:

```text
content parsing
metadata extraction
search
catalog
document rendering
lightweight media manipulation
interactive cultural experiences
```

Native codec/GPU features có thể bị giới hạn theo host.

---

# 166. Mobile

Mobile profile hỗ trợ:

```text
camera
microphone
media playback
offline archive
content creation
publishing
translation
museum guide
heritage guide
```

với quyền OS từ 603/614.

---

# 167. Offline-first archive

Cultural archive phải hỗ trợ:

```text
offline ingest
local catalog
incremental sync
content-addressed replication
conflict resolution
event replay
```

---

# 168. Conflict resolution

Metadata có thể dùng:

```text
version merge
field-level merge
CRDT
manual review
provenance-preserving merge
```

Không merge binary media một cách mù quáng.

---

# 169. Schema evolution

Mỗi cultural record phải có:

```text
schema_version
migration_path
unknown_field_preservation
```

Archive cũ phải đọc được khi schema mới xuất hiện.

---

# 170. Performance requirements

Mục tiêu:

```text
zero-copy media path where possible
streaming-first
lazy metadata loading
incremental indexing
parallel transcoding
GPU acceleration
content-addressed deduplication
memory bounded processing
```

Một video 8K không được buộc runtime load toàn bộ vào RAM.

---

# 171. Determinism

Metadata operations phải deterministic.

Generative operations phải lưu:

```text
model
version
seed
parameters
inputs
environment
```

nếu cần reproducibility.

---

# 172. Failure recovery

Pipeline phải hỗ trợ checkpoint:

```text
ingest checkpoint
transcode checkpoint
index checkpoint
archive checkpoint
digitization checkpoint
simulation checkpoint
```

Crash không làm mất provenance.

---

# 173. Testing target

BOOTSTRAP-677 yêu cầu tối thiểu:

```text
>= 5,600 automated tests
>= 450 invariants
```

bao gồm:

```text
unit
integration
property
fuzz
serialization
provenance
workflow
security
concurrency
performance
distributed
media pipeline
archive integrity
schema migration
AI provenance
simulation
WASM
mobile
```

---

# 174. Critical invariants

## INV-001

Một published work phải có immutable identity.

## INV-002

Một version mới không được silently overwrite version cũ.

## INV-003

Correction phải trỏ đến version cụ thể.

## INV-004

Retraction phải giữ archival lineage.

## INV-005

Transformation phải có provenance.

## INV-006

AI-generated content không được tự nhận là human-created.

## INV-007

Synthetic metadata phải có source/model information khi available.

## INV-008

Fact-check không phải universal truth oracle.

## INV-009

Claim phải có context.

## INV-010

Source và claim là hai object khác nhau.

## INV-011

Evidence không đồng nghĩa truth.

## INV-012

Opinion không được tự chuyển thành fact.

## INV-013

Fiction không được tự chuyển thành historical record.

## INV-014

Archive không được mất provenance khi update.

## INV-015

Restoration phải giữ source lineage.

## INV-016

Translation phải giữ source reference.

## INV-017

Localization phải giữ source work identity.

## INV-018

License không tự tạo legal authority.

## INV-019

Rights metadata không thay thế BOOTSTRAP-675.

## INV-020

Payment không thuộc cultural ledger.

## INV-021

Recommendation không được giả lập thành truth ranking.

## INV-022

Search result phải truy nguyên được nguồn dữ liệu.

## INV-023

Cultural classification không được mặc định là normative superiority.

## INV-024

Historical memory và objective fact phải có metadata khác nhau.

## INV-025

Simulation không được mutate live cultural state.

## INV-026

Archive retrieval phải giữ integrity verification.

## INV-027

Media pipeline không được yêu cầu full-buffer nếu streaming path khả dụng.

## INV-028

Content identity và binary asset identity phải tách biệt.

## INV-029

Creator attribution không tự quyết định legal ownership.

## INV-030

Institution metadata không tự quyết định truthfulness.

## INV-031

Public popularity không được coi là evidence.

## INV-032

Automated classifier output phải giữ model/version metadata.

## INV-033

Moderation decision phải giữ policy reference.

## INV-034

Moderation decision phải hỗ trợ audit.

## INV-035

Appeal không được xóa decision history.

## INV-036

Cultural data phải tuân theo data-governance boundary.

## INV-037

Personal data không được tự động trở thành public archive.

## INV-038

Community-specific metadata không được bị coi là invalid chỉ vì không nằm trong global ontology.

## INV-039

Conflicting cultural interpretations phải có thể coexist.

## INV-040

Provenance chain phải có thể verify.

---

# 175. Acceptance criteria

BOOTSTRAP-677 chỉ được xem là hoàn thành khi Axiom có thể:

1. tạo và quản lý cultural entities;
2. tạo artwork;
3. tạo creative work;
4. quản lý work versions;
5. import media;
6. transform media;
7. stream media;
8. publish content;
9. distribute content;
10. lưu provenance;
11. trace provenance;
12. tạo source;
13. tạo claim;
14. link evidence;
15. tạo citation;
16. chạy fact-check workflow;
17. correction;
18. retraction;
19. archive;
20. preserve;
21. digitize;
22. restore;
23. catalog library;
24. quản lý museum collections;
25. quản lý heritage;
26. lưu oral history;
27. translation;
28. localization;
29. subtitle;
30. dubbing;
31. quản lý creative project;
32. editorial workflow;
33. synthetic-media disclosure;
34. rights metadata;
35. license metadata;
36. content indexing;
37. search;
38. discovery;
39. moderation;
40. appeal;
41. cultural memory;
42. cultural simulation;
43. distributed processing;
44. GPU acceleration;
45. WASM profile;
46. mobile profile;
47. deterministic replay;
48. archive integrity verification;
49. schema migration;
50. AI provenance.

---

# 176. Final architectural contract

BOOTSTRAP-677 biến Axiom thành một nền tảng native có thể mô hình hóa và thực thi:

```text
culture
art
creative work
media
journalism
publishing
public information
libraries
archives
museums
heritage
oral history
preservation
digitization
restoration
translation
localization
creative industries
content provenance
fact-check workflows
AI-generated media
content discovery
collective cultural memory
cultural simulation
```

nhưng **không** được tự động:

```text
declare absolute truth
define cultural superiority
rewrite history silently
erase provenance
assign ownership without legal basis
replace legal semantics
replace human editorial judgment
hide AI-generated origin
manipulate political preference
treat popularity as truth
turn simulation into reality
```

Kiến trúc đúng của Axiom là:

```text
                    ┌──────────────────────┐
                    │   CULTURAL SYSTEM    │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
       CREATION             MEDIA              HERITAGE
          │                    │                    │
          ↓                    ↓                    ↓
       WORK                PUBLICATION          ARCHIVE
          │                    │                    │
          └──────────────┬─────┴──────────────┬─────┘
                         ↓                    ↓
                    PROVENANCE             RIGHTS
                         │                    │
                         ↓                    ↓
                      TRUST              LEGAL 675
                         │
                         ↓
                 PUBLIC KNOWLEDGE
                         │
             ┌───────────┼───────────┐
             ↓           ↓           ↓
          SEARCH      DISCOVERY   MEMORY
             │           │           │
             └───────────┼───────────┘
                         ↓
                    CULTURAL AI
                         │
                         ↓
                    SIMULATION
```

**BOOTSTRAP-677 hoàn tất về mặt kiến trúc.**

Điểm quan trọng nhất của layer này là Axiom không chỉ biết "file media là gì", mà biết **một tác phẩm sinh ra từ đâu, ai tạo, đã biến đổi như thế nào, được xuất bản ở đâu, được kiểm chứng bằng nguồn nào, được bảo tồn ra sao và lịch sử của nó có thể được tái dựng như thế nào**.

Đây là nền tảng cần thiết nếu Axiom hướng tới một hệ điều hành/runtime native cho cả con người lẫn AI ở quy mô civilization.

:::

**Task kế tiếp: BOOTSTRAP-678 — Native AI Civilization-Scale Religion, Philosophy, Belief, Worldview, Meaning & Spiritual/Cultural Interpretation Runtime 5.0.** Chuỗi sẽ tiếp tục tự động sang task này.