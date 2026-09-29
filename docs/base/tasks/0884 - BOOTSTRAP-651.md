Tiếp tục với **BOOTSTRAP-651 — Native AI Personalization, User/Agent Profiles, Preference Learning, Recommendation, Ranking, Adaptive Behavior & Online Learning Runtime 5.0**.

:::writing{variant="document" id="58321" title="BOOTSTRAP-651 — Native AI Personalization, User/Agent Profiles, Preference Learning, Recommendation, Ranking, Adaptive Behavior & Online Learning Runtime 5.0"}
# BOOTSTRAP-651
## Native AI Personalization, User/Agent Profiles, Preference Learning, Recommendation, Ranking, Adaptive Behavior & Online Learning Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native AI Personalization & Adaptive Decision Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-650

---

# 1. Mục tiêu

BOOTSTRAP-651 bổ sung native runtime cho các hệ thống cần thích nghi với:

- user;
- agent;
- tenant;
- device;
- environment;
- session;
- context;
- historical behavior;
- explicit preferences;
- implicit preferences;
- recommendations;
- ranking;
- adaptive policies;
- online learning;
- personalization.

Mục tiêu không phải xây một "recommendation engine" cố định.

651 cung cấp primitive để Axiom xây:

```text
Personal Assistant
Recommendation System
Search Personalization
Content Ranking
Adaptive UI
Adaptive Agent
E-commerce Recommendation
Media Recommendation
Learning Systems
Personalized Retrieval
Adaptive Control
```

---

# 2. Boundary

```text
628 Distributed Data
641 Search / Retrieval
642 Analytics
643 ML / Tensor
644 Agent
645 Knowledge
646 Evaluation
647 Model Lifecycle
648 Simulation
649 Multimodal
650 Memory
651 Personalization
```

Phân biệt:

```text
650 = memory
651 = preference/adaptation/decision
641 = retrieval
642 = analytics
643 = model execution
637 = runtime configuration
639 = policy
640 = governance
```

651 **không được trở thành security policy engine**.

---

# 3. Nguyên tắc

1. Personalization là explicit runtime state.
2. Profile không phải identity.
3. Preference không phải fact.
4. Prediction không phải fact.
5. Recommendation không phải authorization.
6. Ranking không phải security policy.
7. User identity thuộc 627.
8. Capability thuộc 603.
9. Authorization thuộc 603/639.
10. Governance thuộc 640.
11. Memory thuộc 650.
12. Model execution thuộc 643.
13. Evaluation thuộc 646.
14. Model lifecycle thuộc 647.
15. Analytics thuộc 642.
16. Search thuộc 641.
17. Recommendation inputs phải provenance-aware.
18. Learned state phải versioned.
19. Online updates phải bounded.
20. Training data lineage phải preserved.
21. Personalization phải tenant-isolated.
22. Cross-user data sharing bị deny mặc định.
23. Sensitive attributes không được suy diễn để mở quyền.
24. Model output không được thay đổi security policy.
25. Ranking phải deterministic khi policy yêu cầu.
26. Exploration phải explicit.
27. Feedback phải distinguish positive/negative/neutral/unknown.
28. Feedback không đồng nghĩa preference.
29. Cold-start phải được hỗ trợ.
30. Model drift phải detect được.
31. Online learning phải rollback được.
32. Không bắt buộc external recommendation system.
33. Không bắt buộc online ML.
34. Không bắt buộc embedding.
35. Struct-only API.

---

# 4. Core concepts

```text
Profile
ProfileId
ProfileRevision

Preference
PreferenceId
PreferenceRevision

Feature
FeatureValue
FeatureVector

BehaviorEvent
Feedback
FeedbackType

RecommendationRequest
RecommendationCandidate
RecommendationResult

Ranker
RankingModel
RankingFeature
RankingScore

PersonalizationContext
PersonalizationPolicy

AdaptationRule
AdaptationState

OnlineModel
OnlineUpdate
UpdateBatch

ExperimentAssignment
Cohort
Segment

ColdStartPolicy
ExplorationPolicy

RecommendationSession
RecommendationSnapshot

PersonalizationModel
PersonalizationModelVersion
```

---

# 5. Profile

Profile là tập metadata phục vụ personalization.

```text
Profile {
    profile_id
    subject_id
    namespace
    revision
    attributes
    preferences
    features
    provenance
}
```

---

# 6. Profile không phải identity

Identity:

```text
627
```

Profile:

```text
651
```

Một identity có thể có nhiều profile theo:

- application;
- tenant;
- device;
- context.

---

# 7. Profile scope

```text
Global
Tenant
Application
Device
Agent
Session
Context
```

---

# 8. Profile inheritance

Profile có thể kế thừa metadata từ scope cha.

Precedence phải deterministic.

---

# 9. Profile revision

Mọi mutation tạo revision mới.

---

# 10. Preference

Preference mô tả xu hướng lựa chọn.

Ví dụ:

```text
language = vi
content_type = science_fiction
notification_frequency = low
```

---

# 11. Explicit preference

Nguồn:

```text
User
Administrator
Application
Agent
Imported
```

---

# 12. Implicit preference

Derived từ:

- interaction;
- selection;
- dwell time;
- skip;
- purchase;
- search;
- feedback.

---

# 13. Explicit vs inferred

Phải lưu riêng:

```text
Declared
Inferred
Observed
Imported
```

---

# 14. Preference confidence

Confidence là metadata.

Không biến inference thành explicit user statement.

---

# 15. Preference decay

Preference có thể có thời hạn/decay.

---

# 16. Preference history

Historical preferences không bị overwrite.

---

# 17. Preference conflict

Ví dụ:

```text
Declared: language = Vietnamese
Observed: English content frequently selected
```

Hai signals có thể cùng tồn tại.

---

# 18. Conflict policy

```text
ExplicitWins
RecentWins
ContextWins
KeepBoth
RequireResolution
```

Application chọn.

---

# 19. Preference context

Preference có thể chỉ đúng trong:

```text
Home
Work
Mobile
Desktop
Weekend
Session
Application
```

---

# 20. Contextual preference

```text
Preference {
    key
    value
    scope
    context
    source
    confidence
}
```

---

# 21. BehaviorEvent

```text
BehaviorEvent {
    event_id
    subject_id
    event_type
    item_id
    context
    timestamp
    provenance
}
```

---

# 22. Behavior types

```text
View
Click
Open
Skip
Like
Dislike
Save
Share
Purchase
Search
Query
Play
Pause
Complete
Abandon
ExplicitFeedback
```

---

# 23. Behavior semantics

Behavior không tự động được coi là preference.

---

# 24. Feedback

```text
Positive
Negative
Neutral
Correction
Unknown
```

---

# 25. Feedback strength

Feedback có thể có explicit strength.

---

# 26. Feedback provenance

Mỗi feedback ghi:

```text
source
method
timestamp
context
```

---

# 27. RecommendationCandidate

```text
RecommendationCandidate {
    item_id
    source
    features
    eligibility
    provenance
}
```

---

# 28. Eligibility

Eligibility chỉ mô tả candidate có thể được xem xét.

Authorization vẫn thuộc 603/639.

---

# 29. RecommendationRequest

```text
RecommendationRequest {
    subject
    context
    candidates
    objective
    constraints
    limit
}
```

---

# 30. Recommendation objective

Ví dụ:

```text
Relevance
Diversity
Freshness
Completion
Similarity
Exploration
```

Không có objective mặc định universal.

---

# 31. Candidate generation

Các nguồn:

```text
Search
History
Graph
Rules
Collaborative
ContentBased
Embedding
ExternalProvider
```

---

# 32. Candidate retrieval

641.

---

# 33. Semantic candidate retrieval

643 + 641.

---

# 34. Knowledge candidate retrieval

645.

---

# 35. Memory candidate retrieval

650.

---

# 36. Collaborative candidate generation

Có thể sử dụng interaction patterns.

---

# 37. Content-based recommendation

So sánh item features với preference/profile.

---

# 38. Rule-based recommendation

651 hỗ trợ deterministic rules.

---

# 39. Rule engine boundary

639 remains authority for policy.

651 rules chỉ dùng recommendation/adaptation.

---

# 40. Ranking

Ranking nhận candidate set và tạo ordered result.

---

# 41. Ranker

```text
Ranker {
    score(candidate, context)
}
```

---

# 42. Ranking score

Score là numeric signal, không phải truth.

---

# 43. Ranking model

Có thể là:

```text
Linear
Tree
Neural
Embedding
Pairwise
Listwise
RuleBased
External
```

---

# 44. Ranking model version

Mandatory.

---

# 45. Ranking features

```text
user_feature
item_feature
context_feature
interaction_feature
temporal_feature
semantic_feature
```

---

# 46. Feature

Feature có:

```text
name
type
value
timestamp
source
version
```

---

# 47. Feature freshness

Feature có thể yêu cầu freshness bound.

---

# 48. Feature store integration

643 feature store.

---

# 49. Offline features

642.

---

# 50. Online features

628/643.

---

# 51. Point-in-time correctness

Training feature retrieval phải tránh future information leakage.

---

# 52. Feature lineage

640.

---

# 53. Feature schema

612.

---

# 54. Feature version

Explicit.

---

# 55. Feature transformation

Transformation identity/version required.

---

# 56. Feature cache

Can be cached with revision/freshness.

---

# 57. Candidate filtering

Filters may use:

- availability;
- category;
- time;
- geography;
- language;
- profile context.

Security filters remain 603/639.

---

# 58. Policy filtering

Authorization must occur independently of ranking.

---

# 59. Security ordering

Conceptually:

```text
Candidate
→ Security/Policy Eligibility
→ Governance
→ Personalization
→ Ranking
```

---

# 60. No ranking bypass

A high-ranked item cannot bypass access policy.

---

# 61. Governance filtering

640 can exclude data according to classification/residency/retention.

---

# 62. Diversity

Ranking can include diversity constraints.

---

# 63. Diversity strategies

```text
Category
Creator
Topic
Modality
Language
Source
```

---

# 64. Freshness

Ranking can incorporate freshness.

---

# 65. Saturation

Repeated exposure can reduce ranking score.

---

# 66. Exposure tracking

```text
ExposureEvent
```

---

# 67. Recommendation feedback loop

```text
Recommendation
→ Exposure
→ Interaction
→ Feedback
→ Feature Update
→ Model Update
```

---

# 68. Feedback delay

Feedback may arrive asynchronously.

---

# 69. Delayed reward

Supported through event/time association.

---

# 70. Attribution window

```text
AttributionWindow {
    start
    end
}
```

---

# 71. Attribution ambiguity

A result may have multiple possible causes.

System must preserve attribution uncertainty.

---

# 72. Recommendation session

```text
RecommendationSession {
    session_id
    subject
    context
    request_revision
}
```

---

# 73. Session state

650 can store relevant interaction memory.

---

# 74. PersonalizationContext

```text
PersonalizationContext {
    profile
    preferences
    recent_behavior
    features
    session
    environment
}
```

---

# 75. Context budget

Limits:

```text
max_features
max_history
max_candidates
max_compute
max_latency
```

---

# 76. PersonalizationPolicy

```text
PersonalizationPolicy {
    allowed_sources
    allowed_features
    retention
    exploration
    diversity
}
```

---

# 77. Privacy

Personalization must minimize data use.

---

# 78. Data minimization

Only features required for selected model/policy should be loaded.

---

# 79. Sensitive attributes

Sensitive data cannot automatically be used for ranking.

---

# 80. Protected-feature policy

Applications may explicitly prohibit features.

---

# 81. Inference restriction

A model must not silently create a sensitive attribute solely to bypass a policy restriction.

---

# 82. Profile export

Requires capability + policy.

---

# 83. Profile deletion

Governed through 640.

---

# 84. Profile retention

Explicit.

---

# 85. Profile residency

Explicit.

---

# 86. Tenant isolation

Profile data cannot cross tenants.

---

# 87. User isolation

User-specific preference data cannot become another user's profile by default.

---

# 88. Aggregated statistics

Cross-user aggregates may be permitted if policy allows.

---

# 89. Aggregation privacy

Optional privacy-preserving aggregation boundary.

---

# 90. Differential privacy

Provider boundary; not mandatory.

---

# 91. Recommendation explanation

System can return:

```text
features_used
candidate_source
ranker_version
ranking_signals
policy_filters
```

---

# 92. Explanation is not chain-of-thought

Only structured decision metadata.

---

# 93. Ranking explain

```text
RankExplanation {
    candidate
    score_components
    model_version
    policy_revision
}
```

---

# 94. Score components

Example:

```text
relevance
freshness
diversity
preference_match
exploration
```

---

# 95. No hidden score modification

Production ranking configuration must be inspectable.

---

# 96. Deterministic ranking

Tie-breaking uses stable candidate ID.

---

# 97. Stable ordering

Same inputs/model/config can reproduce ordering when ranker is deterministic.

---

# 98. Exploration

Optional exploration intentionally introduces alternatives.

---

# 99. Exploration strategies

```text
EpsilonGreedy
UCB
ThompsonSampling
Random
ContextualBandit
```

Provider/runtime boundary.

---

# 100. Exploration flag

Must be explicit.

---

# 101. Exploration budget

Bounded percentage/number of candidates.

---

# 102. Safety filter

Exploration cannot bypass security/governance.

---

# 103. Cold start

New user/item/model must have fallback.

---

# 104. New user

Possible sources:

```text
ExplicitPreferences
Context
GenericRanking
ContentBased
LocalHistory
```

---

# 105. New item

Possible sources:

```text
Metadata
ContentEmbedding
Category
Creator
Text/Image/Audio features
```

---

# 106. New model

Must undergo 646 evaluation before production promotion where policy requires.

---

# 107. ColdStartPolicy

```text
ColdStartPolicy {
    user_strategy
    item_strategy
    model_strategy
}
```

---

# 108. Online learning

651 supports incremental model updates.

---

# 109. OnlineModel

```text
OnlineModel {
    model_id
    version
    state_revision
    update_policy
}
```

---

# 110. OnlineUpdate

```text
OnlineUpdate {
    update_id
    examples
    gradient_or_delta
    source_revision
}
```

---

# 111. Update batch

Updates should be batched when possible.

---

# 112. Update frequency

Policy-defined.

---

# 113. Online learning safety

No unbounded per-event model mutation.

---

# 114. Update budget

```text
max_updates
max_compute
max_memory
max_model_delta
```

---

# 115. Model delta

Can be validated before activation.

---

# 116. Shadow update

New model state can learn without serving traffic.

---

# 117. Canary model

647/636 can deploy a new model version to a subset.

---

# 118. Rollback

Previous model state remains available according to lifecycle policy.

---

# 119. Checkpoint

Online model state checkpoint via 600/611/628.

---

# 120. Model version

Every promoted state has immutable version identity.

---

# 121. Update lineage

640 records:

```text
dataset
events
features
model
update
```

---

# 122. Training leakage

Online learner must not consume future labels.

---

# 123. Time boundary

Training examples have event time and availability time.

---

# 124. Point-in-time training

Features must correspond to information available at event time.

---

# 125. Delayed labels

Supported.

---

# 126. Label correction

Creates new training revision.

---

# 127. Feedback correction

Historical feedback is not silently rewritten.

---

# 128. Negative feedback

Can be explicit or inferred.

---

# 129. Unknown feedback

Absence of interaction is not automatically negative.

---

# 130. Exposure bias

System can record exposure to distinguish:

```text
not shown
shown but ignored
shown and skipped
```

---

# 131. Selection bias

Evaluation should account for candidate-generation effects.

---

# 132. Offline evaluation

646.

---

# 133. Online evaluation

646 + 633 telemetry.

---

# 134. Metrics

Possible:

```text
CTR
CompletionRate
ConversionRate
Retention
Diversity
Coverage
Freshness
Recall
Precision
NDCG
MRR
Calibration
Latency
```

These are metrics, not a universal score.

---

# 135. Metric segmentation

Metrics can be segmented by:

- model;
- cohort;
- device;
- context;
- time;
- modality.

---

# 136. Cohort

```text
Cohort {
    cohort_id
    membership_rule
}
```

---

# 137. Cohort rule

Declarative and bounded.

---

# 138. Cohort assignment

Deterministic when possible.

---

# 139. Experiment assignment

637.

---

# 140. Experiment identity

```text
ExperimentId
VariantId
AssignmentRevision
```

---

# 141. Personalization experiment

Can compare configurations without assuming which is better.

---

# 142. Assignment stickiness

Stable hash:

```text
hash(experiment_id, subject_id, salt)
```

---

# 143. No hidden assignment

Assignment metadata is inspectable.

---

# 144. Online learning + experiment

Can be separated:

```text
Experiment
ModelUpdate
```

---

# 145. Model update gate

646 can require evaluation.

---

# 146. Promotion

647 manages model lifecycle.

---

# 147. Adaptive behavior

651 can adapt parameters:

```text
UI
Ranking
Recommendation
Agent style
Content selection
Model routing
```

---

# 148. Adaptive UI

619/620 consumes personalization state.

---

# 149. Adaptive agent

644 consumes preferences.

---

# 150. Agent behavior policy

651 can provide preferences but 639 controls authority.

---

# 151. Language preference

Example:

```text
language = vi
```

---

# 152. Modality preference

Example:

```text
preferred_output = audio
```

---

# 153. Model preference

User may prefer low-latency vs high-quality model.

---

# 154. Resource preference

Application can select:

```text
low_memory
low_latency
high_quality
```

---

# 155. Personalization cannot violate resource policy

606 remains authoritative.

---

# 156. Personalization cannot override security

603/639.

---

# 157. Personalization cannot override governance

640.

---

# 158. Recommendation service

631 can expose:

```text
recommend()
rank()
profile()
feedback()
```

---

# 159. Gateway

632 controls external API access.

---

# 160. Distributed recommendation

630/635 distribute candidate generation/ranking.

---

# 161. Locality

Recommendations can be region/device aware where policy permits.

---

# 162. Cache

Recommendation cache key includes:

```text
profile_revision
model_revision
candidate_revision
policy_revision
context_revision
```

---

# 163. Cache invalidation

Profile change invalidates affected cache entries.

---

# 164. Candidate cache

Separate from result cache.

---

# 165. Feature cache

643.

---

# 166. Model cache

647.

---

# 167. Distributed cache

628.

---

# 168. Approximate ranking

Can use approximate nearest neighbor via 641.

---

# 169. Exact ranking

Final top-K ranking can be exact after candidate retrieval.

---

# 170. Two-stage recommendation

```text
Candidate Generation
→ Filtering
→ Ranking
```

---

# 171. Multi-stage ranking

```text
Retrieval
→ Lightweight Ranker
→ Expensive Ranker
→ Diversity
→ Final
```

---

# 172. Stage budget

Each stage has resource limits.

---

# 173. Early exit

Optional if enough candidates satisfy policy.

---

# 174. Parallel ranking

Candidate subsets can rank concurrently.

---

# 175. GPU ranking

643.

---

# 176. Batch inference

643 dynamic batching.

---

# 177. Streaming recommendation

Candidate results can stream incrementally.

---

# 178. Streaming ordering

Final ordering may change until completion.

If provisional results are returned, they must be marked provisional.

---

# 179. RecommendationSnapshot

```text
RecommendationSnapshot {
    request_revision
    candidate_revision
    profile_revision
    model_revision
    result
}
```

---

# 180. Reproducibility

Snapshot captures relevant versions.

---

# 181. Recommendation audit

Can reproduce why candidate was returned.

---

# 182. Item metadata

641/642.

---

# 183. Item embeddings

641/643.

---

# 184. Item graph relations

645.

---

# 185. Item media

649.

---

# 186. Item memory

650.

---

# 187. Unified personalization

```text
650 Memory
      +
641 Retrieval
      +
645 Knowledge
      +
643 Model
      ↓
651 Personalization
```

---

# 188. User representation

Can be:

```text
profile features
preference vector
embedding
history
graph relations
```

---

# 189. User embedding

Optional.

---

# 190. Embedding privacy

User embeddings are derived data governed by 640.

---

# 191. Embedding version

Required.

---

# 192. Preference vector

May contain weighted dimensions.

---

# 193. Preference vector semantics

Application-defined.

---

# 194. No universal preference ontology

651 provides typed storage, not one global user model.

---

# 195. Profile schema

Applications define schema through 612.

---

# 196. Schema validation

Compile/runtime validation.

---

# 197. Schema migration

Explicit.

---

# 198. Profile inheritance

Can be recomputed after parent revision.

---

# 199. Derived profile

Must identify source revisions.

---

# 200. Profile provenance

Every inferred attribute references evidence.

---

# 201. Attribute lifecycle

```text
Candidate
Active
Superseded
Expired
Deleted
```

---

# 202. Attribute correction

Creates revision.

---

# 203. Profile merge

Explicit merge operation.

---

# 204. Profile split

For migrated identities or namespaces.

---

# 205. Identity changes

627 handles identity lifecycle.

651 must not infer identity equivalence.

---

# 206. Account linking

Requires identity provider/policy.

---

# 207. Device profile

Can personalize device behavior.

---

# 208. Environment profile

Simulation 648 can provide context features.

---

# 209. Context profile

Current environment/session can override defaults.

---

# 210. Preference precedence

```text
Explicit Context
→ Explicit User
→ Application
→ Inferred
→ Default
```

This is a configurable default, not a universal truth rule.

---

# 211. Preference source policy

Application may choose a different precedence.

---

# 212. Default

Safe neutral defaults.

---

# 213. Personalization opt-out

A subject can disable personalization where application supports it.

---

# 214. Opt-out state

Explicit profile setting.

---

# 215. Opt-out propagation

Recommendation service must honor current revision.

---

# 216. Data deletion

Opt-out/deletion can trigger derived data deletion according to governance.

---

# 217. Consent boundary

Consent/legal semantics belong to application/policy/governance providers.

651 records status but does not claim legal compliance.

---

# 218. Audit

Sensitive profile access auditable.

---

# 219. Logging

No raw sensitive profile data in default logs.

---

# 220. Metrics privacy

Metrics should aggregate/minimize subject-level data.

---

# 221. Differential privacy provider

Optional.

---

# 222. Federated learning boundary

651 defines adaptation metadata but federated learning can be provided by a specialized provider.

---

# 223. Federated update

```text
local model delta
→ secure aggregation provider
→ global model
```

---

# 224. No raw user data requirement

Federated provider may support learning without central raw examples.

---

# 225. Secure aggregation

Crypto/provider boundary 610.

---

# 226. Client learning

Local device can adapt model state.

---

# 227. Model personalization layers

Possible:

```text
Base Model
+
Adapter
+
User State
```

---

# 228. Adapter

643/647 model artifact.

---

# 229. Adapter version

Immutable.

---

# 230. Adapter lifecycle

647.

---

# 231. Personal adapter

Subject-scoped model delta.

---

# 232. Resource limit

Personal adapters have storage/compute budgets.

---

# 233. Adapter isolation

One user's adapter cannot be loaded for another without explicit authorization.

---

# 234. Online adapter update

Requires validation and rollback.

---

# 235. Shadow personalization

Test adapted model without changing production behavior.

---

# 236. Safe promotion

646 + 647.

---

# 237. Model drift

Monitor metric distributions.

---

# 238. Preference drift

Monitor preference distribution changes.

---

# 239. Data drift

642.

---

# 240. Concept drift

643/646.

---

# 241. Drift response

Possible:

```text
Observe
Alert
Retrain
Rollback
Freeze
```

---

# 242. No automatic unsafe remediation

Policy decides allowed response.

---

# 243. Online update freeze

Emergency freeze prevents further updates.

---

# 244. Rollback state

Previous known-good model version.

---

# 245. Checkpoint chain

```text
ModelVersion N
→ Update N+1
→ Update N+2
```

---

# 246. Update provenance

Each update references source data/events.

---

# 247. Update reproducibility

Seed/config/provider captured.

---

# 248. Training data lineage

640.

---

# 249. Feature lineage

640.

---

# 250. Model lineage

647.

---

# 251. Evaluation lineage

646.

---

# 252. Recommendation lineage

651 records:

```text
candidate source
features
model
policy
context
```

---

# 253. Recommendation explanation

Available without exposing hidden model reasoning.

---

# 254. Structured reason codes

```text
PreferenceMatch
SemanticMatch
Freshness
Diversity
Exploration
ContextMatch
```

---

# 255. Reason code provenance

Each code points to explicit signal.

---

# 256. Recommendation uncertainty

Optional.

---

# 257. Calibration

Models can provide calibrated probability where validated.

---

# 258. Probability semantics

Must identify target/event.

---

# 259. No generic confidence

Avoid ambiguous "confidence score".

---

# 260. Ranking score semantics

Model-defined.

---

# 261. Candidate diversity

Diversity algorithm explicit.

---

# 262. Exposure frequency

Can be bounded.

---

# 263. Frequency cap

```text
max_exposures
window
```

---

# 264. Repetition penalty

Explicit ranking feature.

---

# 265. User fatigue

Represented as behavior/context signal, not a mental-state claim.

---

# 266. Session exploration

Can vary candidates within bounded policy.

---

# 267. Personalization cache

Subject-scoped.

---

# 268. Cache poisoning protection

Cache values bound to model/profile revision.

---

# 269. Feature poisoning

Training/online updates can validate source provenance.

---

# 270. Malicious feedback

646/639 can test or restrict.

---

# 271. Feedback rate limiting

606/639.

---

# 272. Update abuse

Online learning endpoints require authentication/capability.

---

# 273. Recommendation abuse

Gateway 632 rate limits.

---

# 274. Model extraction

External recommendation APIs can limit detailed score exposure.

---

# 275. Score privacy

Applications can choose whether score components are exposed.

---

# 276. Profile privacy

Profile fields need access controls.

---

# 277. Subject export

Structured export through 612.

---

# 278. Subject deletion

Governance-controlled deletion.

---

# 279. Derived deletion

Embeddings/features/adapters can be deleted according to dependency policy.

---

# 280. Historical audit

Audit records may have separate retention requirements.

---

# 281. Audit vs profile

Deleting profile data does not necessarily delete legally/operationally required audit metadata.

---

# 282. Recommendation storage

Results may be ephemeral or persistent.

---

# 283. Recommendation history

Can be stored as episodic memory in 650.

---

# 284. Exposure history

650/628.

---

# 285. Event integration

634 publishes:

```text
ProfileChanged
PreferenceChanged
RecommendationGenerated
RecommendationShown
FeedbackReceived
ModelUpdated
ExperimentAssigned
```

---

# 286. Workflow

629 can orchestrate:

```text
collect
→ train
→ evaluate
→ promote
```

---

# 287. Compute

630 runs distributed training/ranking.

---

# 288. Cluster

635 places workloads.

---

# 289. Deployment

636 deploys ranker/model.

---

# 290. Configuration

637 tunes non-security parameters.

---

# 291. Policy

639 governs operational constraints.

---

# 292. Governance

640 controls data lifecycle.

---

# 293. Credentials

638 controls external providers.

---

# 294. Crypto

610 protects transport/data.

---

# 295. Security

603 controls access.

---

# 296. Storage

611/612.

---

# 297. Distributed state

628.

---

# 298. Search

641.

---

# 299. Analytics

642.

---

# 300. Tensor/ML

643.

---

# 301. Agent

644.

---

# 302. Knowledge

645.

---

# 303. Evaluation

646.

---

# 304. Model lifecycle

647.

---

# 305. Simulation

648.

---

# 306. Multimodal

649.

---

# 307. Compiler annotations

```text
@personalization
@profile
@preference
@behavior
@feedback
@candidate
@recommend
@rank
@ranker
@feature
@cohort
@segment
@experiment
@exploration
@cold_start
@online_model
@online_update
@adaptation
@personal_adapter
@exposure
@attribution
@diversity
@freshness
@frequency_cap
```

---

# 308. Generated metadata

```text
.axprofile
.axpreference
.axbehavior
.axfeedback
.axrecommend
.axrank
.axfeaturemap
.axcohort
.axsegment
.axadapt
.axonline
.axpersonalmodel
```

---

# 309. CLI

```text
axiom profile inspect
axiom profile history
axiom profile preferences
axiom profile export
axiom profile delete

axiom recommend
axiom recommend explain
axiom recommend trace
axiom recommend candidates

axiom rank inspect
axiom rank explain
axiom rank benchmark

axiom feature inspect
axiom feature lineage

axiom online status
axiom online updates
axiom online checkpoint
axiom online rollback
axiom online freeze

axiom experiment assignment
axiom cohort inspect
```

---

# 310. Errors

```text
ProfileNotFound
ProfileRevisionConflict
PreferenceConflict
PreferenceExpired
FeatureUnavailable
FeatureStale
FeatureSchemaMismatch
CandidateUnavailable
RecommendationTimeout
RecommendationBudgetExceeded
RankingModelUnavailable
RankingModelMismatch
PolicyDenied
GovernanceViolation
ProfileAccessDenied
TenantIsolationViolation
ExplorationDisabled
OnlineUpdateRejected
OnlineUpdateConflict
OnlineUpdateBudgetExceeded
ModelDriftDetected
FeatureDriftDetected
ColdStartUnavailable
ExperimentAssignmentConflict
PersonalAdapterUnavailable
PersonalAdapterMismatch
```

---

# 311. Provider architecture

```text
NativePersonalizationProvider
NativeRankerProvider
NativeOnlineLearningProvider
FeatureStoreProvider
RecommendationProvider
ExternalRecommendationProvider
FederatedLearningProvider
TestPersonalizationProvider
```

---

# 312. External systems

Có thể adapter:

- recommendation engines;
- vector databases;
- feature stores;
- ML serving systems;
- federated learning providers.

Không bắt buộc.

---

# 313. Struct-only API

Ví dụ:

```text
ranker := Ranker.open(model)

result := ranker.rank(
    candidates,
    context
)
```

---

# 314. Recommendation example

```text
result := recommender.recommend(
    RecommendationRequest {
        subject: user,
        context: context,
        limit: 20
    }
)
```

---

# 315. Feedback example

```text
recommender.feedback(
    Feedback {
        subject: user,
        item: item,
        kind: Positive,
        source: Explicit
    }
)
```

---

# 316. Preference example

```text
profile.preferences.set(
    Preference {
        key: "language",
        value: "vi",
        source: User
    }
)
```

---

# 317. Online update example

```text
online.update(
    UpdateBatch {
        examples,
        expected_revision
    }
)
```

---

# 318. Safety

Online learning must not:

- execute arbitrary code;
- modify capabilities;
- modify security policy;
- modify governance policy.

---

# 319. Model update safety

Only validated model state may become active.

---

# 320. Rollback safety

Rollback cannot restore revoked credentials or permissions.

---

# 321. Personalization + agent

Agent can receive:

```text
preferred_language
preferred_response_format
interaction_history
task_preferences
```

---

# 322. Agent authority separation

These preferences do not grant authority.

---

# 323. Adaptive response

Agent may adapt presentation according to preference.

---

# 324. Tool routing

Personalization can suggest a tool but 639/603 decide whether it may be used.

---

# 325. Model routing

Personalization may choose a model candidate based on declared preferences/resources.

---

# 326. Security routing

Security constraints are applied afterward/independently.

---

# 327. Personalization + multimodal

649 can expose preferences such as:

```text
preferred_modality
preferred_language
preferred_media_format
```

---

# 328. Personalization + memory

650 stores long-term preference observations.

---

# 329. Personalization + knowledge

645 provides entity/category semantics.

---

# 330. Personalization + search

641 retrieves personalized candidates.

---

# 331. Personalization + analytics

642 computes aggregate behavior statistics.

---

# 332. Personalization + evaluation

646 evaluates recommendation models.

---

# 333. Personalization + simulation

648 can generate synthetic users/scenarios.

---

# 334. Synthetic personalization

Simulation may generate:

```text
synthetic_profile
synthetic_behavior
synthetic_feedback
```

These must be marked synthetic.

---

# 335. Synthetic ≠ real user

Synthetic observations cannot silently enter production user profiles.

---

# 336. Offline training

Synthetic and real datasets remain distinguishable.

---

# 337. Benchmark

646 can benchmark ranking using fixed datasets.

---

# 338. Reproducibility

Record:

```text
profile_revision
candidate_revision
feature_revision
model_revision
policy_revision
dataset_revision
seed
```

---

# 339. Deterministic mode

For tests:

```text
fixed candidate order
fixed seed
fixed feature snapshot
fixed model
```

---

# 340. Random exploration

Seeded when reproducibility is required.

---

# 341. Distributed determinism

Stable partitioning + stable aggregation order where supported.

---

# 342. Floating-point

Exact bit-level reproducibility depends on provider/device.

---

# 343. Acceptance criteria target

**≥600 acceptance criteria** covering:

- profiles;
- namespaces;
- identity separation;
- preferences;
- preference inference;
- behavioral events;
- feedback;
- candidates;
- candidate generation;
- retrieval;
- ranking;
- features;
- feature freshness;
- point-in-time correctness;
- recommendation;
- diversity;
- freshness;
- frequency caps;
- exploration;
- cold start;
- personalization context;
- privacy;
- profile deletion;
- governance;
- security;
- online learning;
- model updates;
- rollback;
- shadow models;
- adapters;
- federated learning boundary;
- experiments;
- cohorts;
- attribution;
- analytics;
- evaluation;
- simulation;
- multimodal personalization;
- agent personalization;
- model routing;
- distributed execution;
- caching;
- consistency;
- observability;
- reproducibility;
- fault injection;
- fuzzing;
- performance;
- scalability.

---

# 344. Core invariants

1. Profile is not identity.
2. Preference is not fact.
3. Prediction is not fact.
4. Ranking is not authorization.
5. Recommendation cannot grant capability.
6. Profile revision is monotonic.
7. Preference history is preserved where configured.
8. Explicit and inferred preferences remain distinguishable.
9. Behavior does not automatically imply preference.
10. Feedback source is explicit.
11. Unknown feedback is not negative feedback.
12. Candidate provenance is preserved.
13. Ranking model version is explicit.
14. Feature version is explicit.
15. Feature freshness is explicit.
16. Training features respect event-time availability.
17. Future information cannot silently leak into training.
18. Security filtering precedes recommendation exposure.
19. Governance filtering remains authoritative.
20. Cross-tenant profile access is denied by default.
21. Cross-user data sharing is explicit.
22. Sensitive attributes are not automatically usable for ranking.
23. Inferred sensitive attributes cannot bypass policy.
24. Exploration is explicit.
25. Exploration cannot bypass policy.
26. Exploration is bounded.
27. Cold-start behavior is explicit.
28. Online updates are bounded.
29. Online updates are versioned.
30. Online updates are reversible.
31. Model state is checkpointable.
32. Model promotion is lifecycle-controlled.
33. Model evaluation is versioned.
34. Model lineage is preserved.
35. Recommendation explanation does not expose hidden reasoning.
36. Ranking score is not universal truth.
37. Score semantics are model-specific.
38. Attribution uncertainty can be represented.
39. Exposure is distinct from interaction.
40. No interaction is not automatically negative.
41. Cache keys include relevant revisions.
42. Profile changes invalidate affected caches.
43. Model changes invalidate incompatible caches.
44. Feature changes invalidate affected model state where required.
45. Personal adapters are isolated.
46. Personal adapters cannot grant authority.
47. Memory is distinct from personalization.
48. Search is distinct from recommendation.
49. Analytics is distinct from online learning.
50. Simulation data is marked synthetic.
51. Synthetic behavior cannot silently become real behavior.
52. Online learning cannot execute arbitrary code.
53. Online learning cannot alter security policy.
54. Online learning cannot alter governance policy.
55. Model output cannot mint capabilities.
56. External providers cannot expand authority.
57. Distributed updates do not assume exactly-once.
58. Idempotency keys can prevent duplicate updates.
59. Deleted profile data cannot be resurrected by stale replicas.
60. Derived embeddings follow governance deletion rules.
61. User opt-out is versioned.
62. Opt-out propagation is observable.
63. Personalization is bounded by resource policy.
64. Recommendation latency has explicit budget.
65. Candidate generation has explicit budget.
66. Ranking has explicit budget.
67. Context has explicit budget.
68. Multimodal inputs have explicit budget.
69. No mandatory external recommender.
70. No mandatory online learning.
71. No mandatory embedding.
72. No mandatory LLM.
73. No mandatory GC.
74. No raw pointer public API.
75. Struct-only public API.
76. Provider capabilities are explicit.
77. Provider versions are explicit.
78. Recommendation snapshots are reproducible where supported.
79. Experiment assignment is deterministic when configured.
80. Cohort rules are bounded.
81. Policy revisions are recorded.
82. Governance revisions are recorded.
83. Security decisions remain outside personalization.
84. Audit data is separated from profile data.
85. Sensitive payloads are not emitted to default logs.
86. Recommendation results can be traced to candidate sources.
87. Model routing decisions can be explained structurally.
88. Personalization cannot silently change application semantics.
89. Adaptive behavior is explicitly configured.
90. Rollback restores model state, not authority.
91. Profile restoration validates current policy.
92. Historical data retains provenance.
93. Feature transformations retain lineage.
94. Ranking changes are versioned.
95. Online model updates have stable identities.
96. Experiment variants have stable identities.
97. Recommendation results can be marked provisional.
98. Partial results are explicit.
99. Stale results are explicit.
100. Personalization is an adaptation mechanism, not a security mechanism.

---

# 345. Profiles

```text
AXPERSONAL_NONE

AXPERSONAL_CORE
AXPERSONAL_PROFILE
AXPERSONAL_PREFERENCE
AXPERSONAL_BEHAVIOR
AXPERSONAL_FEEDBACK

AXPERSONAL_FEATURE
AXPERSONAL_RETRIEVAL
AXPERSONAL_RANK
AXPERSONAL_RECOMMEND

AXPERSONAL_DIVERSITY
AXPERSONAL_EXPLORATION
AXPERSONAL_COLDSTART

AXPERSONAL_EXPERIMENT
AXPERSONAL_COHORT
AXPERSONAL_ADAPTIVE

AXPERSONAL_ONLINE
AXPERSONAL_FEDERATED
AXPERSONAL_AGENT
AXPERSONAL_MULTIMODAL

AXPERSONAL_DISTRIBUTED
AXPERSONAL_FULL
```

---

# 346. Minimal profile

```text
AXPERSONAL_CORE
```

bao gồm:

```text
Profile
Preference
BehaviorEvent
Feedback
PersonalizationContext
```

---

# 347. Recommendation profile

```text
AXPERSONAL_PROFILE
+
AXPERSONAL_RETRIEVAL
+
AXPERSONAL_RANK
+
AXPERSONAL_RECOMMEND
```

---

# 348. Adaptive AI profile

```text
AXPERSONAL_RECOMMEND
+
AXPERSONAL_AGENT
+
AXPERSONAL_ONLINE
```

---

# 349. Full profile

```text
AXPERSONAL_FULL
```

bao gồm distributed personalization, online adaptation, multimodal features, experimentation và federated provider boundary.

---

# 350. Final architecture

```text
                    AXIOM PERSONALIZATION

                           ┌───────────┐
                           │    User   │
                           │  Agent    │
                           │  Context  │
                           └─────┬─────┘
                                 │
                                 ▼
                     ┌─────────────────────┐
                     │        651          │
                     │ Personalization     │
                     └──────────┬──────────┘
                                │
          ┌─────────────────────┼──────────────────────┐
          ▼                     ▼                      ▼
      ┌────────┐          ┌────────────┐         ┌──────────┐
      │ Profile│          │ Preferences│         │ Behavior │
      └────┬───┘          └──────┬─────┘         └────┬─────┘
           │                     │                    │
           └─────────────────────┼────────────────────┘
                                 ▼
                       ┌──────────────────┐
                       │ Feature / Context│
                       └────────┬─────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                   641         645         650
                Retrieval   Knowledge    Memory
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                       Candidate Generation
                                │
                                ▼
                         Policy/Governance
                                │
                                ▼
                            Ranking
                                │
                     ┌──────────┴──────────┐
                     ▼                     ▼
               Recommendation         Adaptive Agent
                     │                     │
                     └──────────┬──────────┘
                                ▼
                             Feedback
                                │
                                ▼
                          Online Learning
                                │
                                ▼
                           646 / 647
                         Eval / Lifecycle
```

---

# 351. End-to-end adaptive loop

```text
User / Environment
        ↓
Observation
        ↓
650 Memory
        ↓
651 Profile + Preference
        ↓
641 / 645 Retrieval
        ↓
Candidate Generation
        ↓
Policy / Governance
        ↓
651 Ranking
        ↓
Recommendation / Agent Action
        ↓
Exposure
        ↓
Feedback
        ↓
Feature Update
        ↓
Optional Online Learning
        ↓
646 Evaluation
        ↓
647 Model Lifecycle
        ↓
New Model
```

---

# 352. Kết quả

BOOTSTRAP-651 hoàn thiện lớp **adaptive intelligence** của Axiom.

Axiom hiện có chuỗi:

```text
Experience
   ↓
650 Memory
   ↓
651 Personalization
   ↓
Recommendation / Ranking
   ↓
Agent / Application Behavior
   ↓
Feedback
   ↓
Online Learning
```

Điểm quan trọng nhất là Axiom **không trộn personalization với security, memory, identity hoặc policy**:

```text
627 Identity
603 Security
639 Policy
640 Governance
650 Memory
651 Personalization
643 ML
646 Evaluation
647 Model Lifecycle
```

Điều này cho phép xây hệ thống AI thích nghi lâu dài nhưng vẫn giữ được khả năng kiểm soát, audit, rollback và reproducibility.

---

# 353. Trạng thái

**BOOTSTRAP-651 — COMPLETE**

### Task kế tiếp

**BOOTSTRAP-652 — Native AI Planning, Decision Optimization, Constraint Solving, Search-Based Reasoning, Scheduling Intelligence & Decision Runtime 5.0**
:::