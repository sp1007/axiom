Tiếp tục với **BOOTSTRAP-672**. Task này hoàn thiện lớp **science/research/knowledge/innovation** ở quy mô văn minh, nhưng giữ ranh giới rõ với knowledge graph 645, simulation 648, AI reasoning 653/655 và kinh tế 671.

:::writing{variant="document" id="74126" title="BOOTSTRAP-672 — Native AI Civilization-Scale Science, Research, Knowledge Production, Technology Development, Innovation, Discovery & Scientific Simulation Runtime 5.0"}
# BOOTSTRAP-672
## Native AI Civilization-Scale Science, Research, Knowledge Production, Technology Development, Innovation, Discovery & Scientific Simulation Runtime 5.0

**Status:** ARCHITECTURE COMPLETE  
**Layer:** Civilization-Scale Science, Research & Innovation  
**Task ID:** BOOTSTRAP-672  
**Depends on:** BOOTSTRAP-603 … BOOTSTRAP-671  
**Target:** ≥ 4,200 tests, ≥ 340 invariants  
**Execution:** local / distributed / GPU / cluster / edge / WASM / deterministic simulation  
**Default:** optional, capability-gated, provenance-gated, safety-gated, privacy-gated  
**Zero-cost requirement:** no runtime overhead when unused

---

# 1. Purpose

BOOTSTRAP-672 defines the native scientific and technological substrate of Axiom.

It provides primitives for:

- scientific knowledge;
- research projects;
- hypotheses;
- experiments;
- observations;
- measurements;
- instruments;
- datasets;
- samples;
- protocols;
- methodologies;
- laboratory workflows;
- simulations;
- mathematical models;
- scientific models;
- theories;
- evidence;
- uncertainty;
- reproducibility;
- peer review;
- research provenance;
- citations;
- publications;
- research organizations;
- researchers;
- collaboration;
- discoveries;
- inventions;
- technology development;
- technology readiness;
- innovation;
- technology diffusion;
- scientific forecasting;
- computational experiments;
- digital laboratories;
- scientific digital twins;
- automated experimentation;
- AI-assisted research.

The system must support both:

1. **real scientific workflows**, and
2. **pure computational/synthetic scientific worlds**.

---

# 2. Architectural Position

```text
645  Knowledge Graph / Semantic Knowledge
648  Simulation / Synthetic Environment
652  Optimization / Search
653  Causal / Probabilistic Reasoning
655  World Model
656  Embodied Intelligence
661  Objectives
663  Evaluation
664  Safety
665  Human Oversight
667  Organizations
668  Inter-Organization Coordination
669  Civilization Infrastructure
670  Human Systems
671  Economy
        ↓
672  Science / Research / Innovation
```

672 becomes the primary layer for **producing and validating new knowledge**, rather than merely storing existing knowledge.

---

# 3. Critical Separation

## 3.1 645 — Knowledge

645 represents:

```text
entities
relationships
concepts
ontology
semantic graphs
knowledge retrieval
```

672 represents:

```text
how knowledge is generated
how evidence is collected
how hypotheses are tested
how models are validated
how discoveries are established
```

---

## 3.2 648 — Simulation

648 provides generic simulation infrastructure.

672 provides:

```text
scientific models
experimental designs
scientific datasets
laboratory workflows
scientific validation
```

A scientific simulation ultimately executes through 648.

---

## 3.3 653 — Causal Reasoning

653 provides:

```text
causal inference
probability
Bayesian reasoning
uncertainty
```

672 uses these capabilities for scientific research.

---

## 3.4 655 — World Model

655 represents a model of an environment.

672 generates and validates scientific models of that environment.

---

## 3.5 671 — Economy

671 models:

```text
economic activity
markets
production
finance
trade
investment
```

672 models:

```text
scientific discovery
technology development
research productivity
innovation
technology diffusion
```

The two layers can interact but neither subsumes the other.

---

# 4. Non-Goals

672 does not define:

- what scientific conclusions society must accept;
- political control of science;
- mandatory research priorities;
- ownership policy;
- patent law;
- intellectual-property law;
- funding policy;
- ideological definitions of valid knowledge.

Such rules are external policy inputs.

---

# 5. Core Scientific Principle

Axiom must distinguish:

```text
Observation
Measurement
Evidence
Hypothesis
Model
Prediction
Experiment
Result
Interpretation
Conclusion
Theory
```

These are not interchangeable.

---

# 6. Scientific Entity Model

Core entities:

```text
ScienceDomain
ResearchField
ResearchProject
ResearchProgram
Researcher
ResearchTeam
Institution
Laboratory
Hypothesis
Question
Experiment
Study
Protocol
Method
Measurement
Observation
Dataset
Sample
Specimen
Instrument
Model
Simulation
Prediction
Result
Evidence
Conclusion
Theory
Discovery
Invention
Technology
Innovation
Publication
Citation
Review
Replication
Reproduction
Benchmark
```

---

# 7. Science Domain

```axiom
struct ScienceDomain {
    id: ScienceDomainId
    name: String
    parent: ScienceDomainId?
    ontology: OntologyRef?
}
```

Supports arbitrary domains:

```text
physics
chemistry
biology
medicine
astronomy
geology
climate
computer_science
mathematics
engineering
social_science
economics
materials
neuroscience
robotics
```

No fixed taxonomy is mandatory.

---

# 8. Research Field

```axiom
struct ResearchField {
    id: ResearchFieldId
    domain: ScienceDomainId
    concepts: []ConceptRef
}
```

Research fields may form a directed graph rather than a strict tree.

---

# 9. Research Project

```axiom
struct ResearchProject {
    id: ResearchProjectId
    title: String
    domain: ResearchFieldId
    researchers: []ResearcherRef
    hypotheses: []HypothesisRef
    experiments: []ExperimentRef
    datasets: []DatasetRef
    status: ResearchStatus
}
```

Lifecycle:

```text
IDEA
↓
QUESTION
↓
DESIGN
↓
PRE_REGISTRATION
↓
EXECUTION
↓
ANALYSIS
↓
REVIEW
↓
PUBLICATION
↓
REPLICATION
↓
ARCHIVE
```

---

# 10. Research Question

```axiom
struct ResearchQuestion {
    id: QuestionId
    statement: ScientificExpression
    domain: ResearchFieldId
    assumptions: []Assumption
}
```

Questions are explicit objects so AI agents can reason over research programs.

---

# 11. Hypothesis

```axiom
struct Hypothesis {
    id: HypothesisId
    statement: ScientificExpression
    predictions: []Prediction
    assumptions: []Assumption
    status: HypothesisStatus
}
```

Status:

```text
PROPOSED
REGISTERED
TESTING
SUPPORTED
REFUTED
INCONCLUSIVE
SUPERSEDED
ARCHIVED
```

"Supported" does not mean "proven universally."

---

# 12. Scientific Claim

```axiom
struct ScientificClaim {
    id: ClaimId
    statement: ScientificExpression
    evidence: []EvidenceRef
    confidence: Confidence?
    provenance: Provenance
}
```

Claims must retain their evidence chain.

---

# 13. Evidence

```axiom
struct Evidence {
    id: EvidenceId
    source: EvidenceSource
    observations: []ObservationRef
    measurements: []MeasurementRef
    provenance: Provenance
    uncertainty: UncertaintyModel
}
```

Evidence may be:

```text
experimental
observational
computational
mathematical
simulation
historical
synthetic
derived
```

---

# 14. Observation

```axiom
struct Observation {
    id: ObservationId
    subject: EntityRef
    variable: VariableId
    value: Value
    timestamp: Instant
    provenance: Provenance
}
```

Observation represents recorded information.

It does not automatically imply causation.

---

# 15. Measurement

```axiom
struct Measurement {
    id: MeasurementId
    variable: VariableId
    value: Quantity
    instrument: InstrumentRef?
    uncertainty: UncertaintyModel
    timestamp: Instant
}
```

Measurements must preserve units.

---

# 16. Measurement Uncertainty

```axiom
struct UncertaintyModel {
    type: UncertaintyType
    parameters: []Parameter
    confidence_level: Decimal?
}
```

Types:

```text
interval
standard_error
variance
distribution
confidence_interval
credible_interval
measurement_error
systematic_error
custom
```

---

# 17. Unit Safety

Scientific quantities must use compile-time dimensions whenever possible.

Example:

```axiom
distance: 10 m
time: 2 s

velocity = distance / time
```

produces:

```text
5 m/s
```

Invalid:

```axiom
distance + time
```

must fail type checking.

---

# 18. Constants

```axiom
const speed_of_light: 299792458 m/s
```

Scientific constants should support:

```text
symbol
value
unit
uncertainty
source
version
```

---

# 19. Experimental Design

```axiom
struct ExperimentDesign {
    id: ExperimentDesignId
    variables: []Variable
    controls: []ControlVariable
    treatments: []Treatment
    repetitions: UInt64
    randomization: RandomizationPolicy?
    stopping_rule: StoppingRule?
}
```

---

# 20. Experiment

```axiom
struct Experiment {
    id: ExperimentId
    design: ExperimentDesignRef
    protocol: ProtocolRef
    samples: []SampleRef
    instruments: []InstrumentRef
    observations: []ObservationRef
    status: ExperimentStatus
}
```

Lifecycle:

```text
DESIGNED
↓
REGISTERED
↓
READY
↓
RUNNING
↓
COMPLETED
↓
ANALYZING
↓
ARCHIVED
```

---

# 21. Protocol

```axiom
struct ScientificProtocol {
    id: ProtocolId
    version: Version
    steps: []ProtocolStep
    inputs: []ResourceRequirement
    outputs: []OutputSpecification
    safety: SafetySpecification
}
```

Protocols must be versioned.

---

# 22. Protocol Step

```axiom
struct ProtocolStep {
    id: StepId
    action: ScientificAction
    inputs: []Value
    expected_outputs: []ValueSpecification
    constraints: []Constraint
}
```

---

# 23. Laboratory

```axiom
struct Laboratory {
    id: LaboratoryId
    facilities: []FacilityRef
    instruments: []InstrumentRef
    protocols: []ProtocolRef
    capabilities: CapabilitySet
}
```

A laboratory is a computational abstraction.

It may map to:

- physical laboratory;
- virtual laboratory;
- simulation environment;
- robotic laboratory.

---

# 24. Instrument

```axiom
struct ScientificInstrument {
    id: InstrumentId
    type: InstrumentType
    calibration: CalibrationState
    capabilities: []MeasurementCapability
    uncertainty_model: UncertaintyModel
}
```

Examples:

```text
sensor
camera
microscope
spectrometer
sequencer
telescope
accelerator
robotic_arm
weather_station
simulation_sensor
```

---

# 25. Calibration

```axiom
struct Calibration {
    instrument: InstrumentId
    reference: ReferenceStandard
    coefficients: []CalibrationParameter
    timestamp: Instant
    validity: TimeWindow
}
```

Measurements may reference the calibration state active at acquisition time.

---

# 26. Sample

```axiom
struct Sample {
    id: SampleId
    source: SampleSource
    composition: []Property
    lineage: []SampleEvent
    custody: []CustodyEvent
}
```

Sample lineage must remain traceable.

---

# 27. Dataset

```axiom
struct ScientificDataset {
    id: DatasetId
    schema: SchemaRef
    observations: []ObservationRef
    provenance: ProvenanceGraph
    quality: DatasetQuality
    license: DataLicense?
}
```

---

# 28. Dataset Provenance

Every derived dataset should be able to answer:

```text
Where did this data come from?
What transformations occurred?
Which code produced it?
Which model version was used?
Which source datasets were involved?
```

Represent:

```axiom
struct DataDerivation {
    inputs: []DatasetRef
    operation: OperationRef
    code_hash: Hash
    parameters: []Parameter
    output: DatasetRef
}
```

---

# 29. Scientific Data Lineage

The lineage graph must support:

```text
source
→ acquisition
→ cleaning
→ transformation
→ aggregation
→ analysis
→ visualization
→ publication
```

No step may silently disappear.

---

# 30. Scientific Model

```axiom
struct ScientificModel {
    id: ModelId
    domain: ResearchFieldId
    variables: []Variable
    parameters: []Parameter
    equations: []ScientificExpression
    assumptions: []Assumption
    outputs: []Variable
}
```

Models may be:

```text
analytical
numerical
statistical
mechanistic
empirical
agent_based
differential_equation
discrete_event
machine_learning
hybrid
```

---

# 31. Model Assumptions

```axiom
struct ScientificAssumption {
    id: AssumptionId
    statement: ScientificExpression
    scope: ModelScope
    provenance: Provenance
}
```

Assumptions must be queryable.

---

# 32. Mathematical Expression

672 extends the compiler's expression system with scientific metadata:

```text
variable
constant
function
equation
inequality
integral
derivative
summation
matrix
tensor
probability_distribution
differential_equation
constraint
```

---

# 33. Scientific Computation

Required primitives:

```text
vector
matrix
tensor
sparse_matrix
complex
interval
rational
high_precision
automatic_differentiation
symbolic_expression
```

These reuse lower-level numeric primitives where possible.

---

# 34. Numerical Solver

```axiom
trait ScientificSolver {
    solve(problem: ScientificProblem) -> ScientificResult
}
```

Solver families:

```text
linear
nonlinear
ODE
PDE
optimization
eigenvalue
root_finding
MonteCarlo
MCMC
sampling
constraint
symbolic
```

---

# 35. Simulation Integration

672 does not duplicate 648.

```axiom
ScientificSimulation
    -> SimulationEngine
        -> 648
```

672 defines:

- scientific model;
- variables;
- equations;
- parameters;
- experiment;
- measurements;
- validation.

648 executes the generic simulation mechanics.

---

# 36. Simulation Experiment

```axiom
struct SimulationExperiment {
    id: SimulationExperimentId
    model: ScientificModelRef
    parameters: []ParameterValue
    initial_state: State
    duration: Duration
    solver: SolverConfig
    outputs: []VariableId
}
```

---

# 37. Prediction

```axiom
struct ScientificPrediction {
    model: ModelRef
    input_state: State
    predicted_output: Value
    uncertainty: UncertaintyModel
}
```

Predictions must reference the model version.

---

# 38. Model Validation

```axiom
struct ModelValidation {
    model: ModelId
    dataset: DatasetId
    metrics: []ValidationMetric
    residuals: []Residual
    status: ValidationStatus
}
```

Statuses:

```text
PASS
FAIL
PARTIAL
INCONCLUSIVE
NOT_APPLICABLE
```

---

# 39. Reproducibility

A research result must be reproducible where technically possible.

Reproducibility bundle:

```text
source_code
compiler_version
dependency_manifest
model_version
dataset_version
parameters
random_seed
hardware_profile
execution_mode
environment_hash
result_hash
```

---

# 40. Reproduction vs Replication

Axiom distinguishes:

```text
reproduction
replication
validation
extension
```

### Reproduction

Same data/code/method where applicable.

### Replication

Independent execution intended to test whether a result recurs.

### Validation

Testing model/results against evidence.

### Extension

Testing a broader or modified hypothesis.

---

# 41. Scientific Benchmark

```axiom
struct ScientificBenchmark {
    id: BenchmarkId
    task: ScientificTask
    dataset: DatasetRef
    metrics: []Metric
    protocol: ProtocolRef
}
```

Benchmark results must preserve:

```text
model
version
hardware
dataset
configuration
random_seed
```

---

# 42. Scientific Evaluation

672 integrates with 663.

```axiom
ScientificEvaluation
    -> 663 Evaluation
```

Evaluation may include:

```text
accuracy
precision
recall
error
uncertainty
reproducibility
robustness
generalization
calibration
computational_cost
```

No single metric is universally sufficient.

---

# 43. Peer Review

```axiom
struct ScientificReview {
    id: ReviewId
    artifact: ScientificArtifactRef
    reviewer: ReviewerRef
    criteria: []ReviewCriterion
    findings: []ReviewFinding
    status: ReviewStatus
}
```

Review states:

```text
REQUESTED
IN_PROGRESS
SUBMITTED
REVISED
RESOLVED
ARCHIVED
```

The runtime records reviews; it does not determine scientific truth solely from review status.

---

# 44. Publication

```axiom
struct ScientificPublication {
    id: PublicationId
    title: String
    authors: []ResearcherRef
    artifacts: []ScientificArtifactRef
    datasets: []DatasetRef
    methods: []ProtocolRef
    citations: []CitationRef
}
```

---

# 45. Citation

```axiom
struct ScientificCitation {
    source: ScientificArtifactRef
    target: ScientificArtifactRef
    context: CitationContext
}
```

Citation graph may be consumed by 645.

---

# 46. Researcher

```axiom
struct Researcher {
    id: ResearcherId
    identity: IdentityRef
    affiliations: []OrganizationRef
    fields: []ResearchFieldId
    credentials: []CredentialRef
}
```

Credentials are separate from scientific claims.

---

# 47. Research Team

```axiom
struct ResearchTeam {
    id: ResearchTeamId
    members: []ResearcherRef
    projects: []ResearchProjectRef
}
```

Organization semantics remain in 667.

---

# 48. Research Collaboration

```axiom
struct ResearchCollaboration {
    participants: []OrganizationRef
    projects: []ResearchProjectRef
    agreements: []AgreementRef
    shared_resources: []ResourceRef
}
```

Cross-organization agreements integrate with 668.

---

# 49. Research Resource

Resources may include:

```text
compute
laboratory_time
instrument_time
samples
datasets
funding
storage
energy
researcher_time
```

Physical resource accounting is provided by 669/671.

---

# 50. Research Funding

672 represents funding as an input.

```axiom
struct ResearchFunding {
    source: ParticipantRef
    recipient: ResearchProjectRef
    amount: Money
    constraints: []FundingConstraint
}
```

Actual monetary accounting is performed by 671.

---

# 51. Research Portfolio

```axiom
struct ResearchPortfolio {
    projects: []ResearchProjectRef
    resources: []ResourceAllocation
    objectives: []ObjectiveRef
}
```

Optimization belongs to 652.

---

# 52. Research Planning

A research planner can optimize:

```text
experiment selection
instrument scheduling
compute allocation
sample usage
research timeline
resource utilization
```

But objectives must be explicitly supplied.

---

# 53. Active Learning / Experiment Selection

```axiom
struct ExperimentSelectionPolicy {
    candidate_experiments: []ExperimentRef
    objective: ObjectiveRef
    uncertainty_model: UncertaintyModel
}
```

Possible strategies:

```text
information_gain
uncertainty_reduction
cost_sensitive
Bayesian_optimization
active_learning
random
custom
```

---

# 54. Automated Science

Axiom may support:

```text
hypothesis generation
experiment design
robotic execution
measurement
analysis
model update
new hypothesis generation
```

Pipeline:

```text
QUESTION
↓
HYPOTHESIS
↓
DESIGN
↓
EXPERIMENT
↓
OBSERVATION
↓
ANALYSIS
↓
MODEL
↓
VALIDATION
↓
REPLICATION
↓
KNOWLEDGE UPDATE
```

---

# 55. AI Scientist Boundary

An AI agent may propose:

- hypotheses;
- experiments;
- models;
- explanations;
- research plans.

It does not automatically establish scientific truth.

Scientific claims retain:

```text
evidence
uncertainty
provenance
validation
review
```

---

# 56. Discovery

```axiom
struct ScientificDiscovery {
    id: DiscoveryId
    claim: ScientificClaimRef
    evidence: []EvidenceRef
    discovery_method: DiscoveryMethod
    confidence: Confidence?
}
```

A discovery is an explicit record of a claimed new finding.

---

# 57. Invention

```axiom
struct Invention {
    id: InventionId
    principle: []ScientificClaimRef
    implementation: []TechnologyComponent
    provenance: Provenance
}
```

Invention is distinct from discovery.

---

# 58. Technology

```axiom
struct Technology {
    id: TechnologyId
    capabilities: []Capability
    components: []TechnologyComponent
    maturity: TechnologyMaturity
}
```

---

# 59. Technology Readiness

Generic maturity levels may be represented without enforcing a specific external standard:

```text
concept
prototype
validated
demonstrated
pilot
production_ready
deployed
obsolete
```

Custom maturity systems are supported.

---

# 60. Innovation

```axiom
struct Innovation {
    id: InnovationId
    invention: InventionRef?
    technology: TechnologyRef
    adoption_state: AdoptionState
    diffusion_model: DiffusionModel?
}
```

Innovation describes implementation/adoption of new technology or methods.

---

# 61. Technology Diffusion

672 may model:

```text
adoption_rate
adoption_curve
network_effect
cost_reduction
learning_curve
availability
compatibility
infrastructure_dependency
```

Actual economic consequences belong to 671.

Human/social adoption dynamics may integrate with 670.

---

# 62. Research-to-Economy Bridge

```text
ScientificDiscovery
        ↓
Invention
        ↓
Technology
        ↓
ProductionCapability
        ↓
EconomicActivity
```

672 owns the first three.

669 owns physical capability.

671 owns economic production/market activity.

No layer silently crosses the boundary.

---

# 63. Knowledge Update

Research results can publish updates to 645.

```axiom
KnowledgeUpdate {
    claims
    evidence
    provenance
    confidence
    source_artifacts
}
```

645 stores/queries the resulting knowledge graph.

672 owns the generation process.

---

# 64. Scientific Versioning

Every scientific artifact must support:

```text
artifact_id
version
parent_version
created_at
creator
code_hash
data_hash
model_hash
provenance_hash
```

---

# 65. Branching Research

Research may branch:

```text
baseline
├── hypothesis_A
│   ├── experiment_A1
│   └── experiment_A2
└── hypothesis_B
    ├── experiment_B1
    └── experiment_B2
```

Branches are first-class objects.

---

# 66. Research Checkpoint

```axiom
struct ResearchCheckpoint {
    project: ResearchProjectId
    state_hash: Hash
    datasets: []DatasetRef
    model_versions: []ModelVersion
    timestamp: Instant
}
```

Used for long-running automated research.

---

# 67. Scientific Workflow Engine

Required operations:

```text
project.create
question.create
hypothesis.create
experiment.design
experiment.register
experiment.run
measurement.acquire
dataset.create
dataset.transform
model.create
model.fit
model.validate
simulation.run
prediction.generate
analysis.run
review.request
review.submit
publication.create
replication.create
discovery.register
invention.register
technology.create
innovation.register
```

---

# 68. Scientific IR

Required IR operations:

```text
ScienceDomainCreate
ResearchFieldCreate
ResearchProjectCreate
ResearchQuestionCreate
HypothesisCreate
ClaimCreate

ProtocolDefine
ExperimentDesign
ExperimentRegister
ExperimentRun
ExperimentComplete

InstrumentRegister
CalibrationCreate
MeasurementAcquire
ObservationRecord

SampleCreate
SampleTransform
SampleTransfer

DatasetCreate
DatasetTransform
DatasetMerge
DatasetSplit
DatasetVersion

ScientificModelCreate
ScientificModelFit
ScientificModelValidate

ScientificSimulationCreate
ScientificSimulationRun
ScientificPredictionGenerate

BenchmarkCreate
BenchmarkRun
ScientificEvaluate

ReviewRequest
ReviewSubmit

PublicationCreate
CitationCreate

ReplicationCreate
ReplicationRun

DiscoveryRegister
InventionRegister
TechnologyCreate
InnovationCreate
TechnologyDiffuse

ResearchCheckpoint
ResearchRestore
ResearchBranch

ScientificKnowledgeUpdate
ScientificProvenanceAudit
```

---

# 69. Scientific Metadata

Recommended annotations:

```text
@science
@research
@research_field
@research_project
@question
@hypothesis
@claim
@evidence
@experiment
@study
@protocol
@method
@measurement
@observation
@instrument
@calibration
@sample
@dataset
@dataset_derivation
@scientific_model
@scientific_simulation
@prediction
@validation
@benchmark
@review
@publication
@citation
@replication
@discovery
@invention
@technology
@innovation
@research_program
@research_team
@research_resource
@research_funding
@research_portfolio
@scientific_forecast
@scientific_uncertainty
```

---

# 70. Scientific File Formats

Logical extensions:

```text
.axscience
.axresearch
.axproject
.axhypothesis
.axexperiment
.axprotocol
.axmeasurement
.axobservation
.axsample
.axdataset
.axscientificmodel
.axscisim
.axprediction
.axvalidation
.axbenchmark
.axreview
.axpublication
.axcitation
.axreplication
.axdiscovery
.axinvention
.axtechnology
.axinnovation
.axresearchprogram
.axscientificforecast
```

Physical storage uses Axiom's common serialization and content-addressed storage layers.

---

# 71. Scientific Reproducibility Package

CLI:

```text
axiom science package create
axiom science package verify
axiom science package reproduce
axiom science package compare
```

A package contains:

```text
source
data manifest
model
parameters
environment
compiler
seed
protocol
results
provenance
```

---

# 72. Scientific CLI

```text
axiom science list
axiom science domains
axiom science fields
```

Research:

```text
axiom research list
axiom research create
axiom research inspect
axiom research status
```

Hypotheses:

```text
axiom hypothesis list
axiom hypothesis create
axiom hypothesis test
axiom hypothesis inspect
```

Experiments:

```text
axiom experiment list
axiom experiment design
axiom experiment register
axiom experiment run
axiom experiment inspect
```

Data:

```text
axiom science dataset list
axiom science dataset create
axiom science dataset inspect
axiom science dataset lineage
axiom science dataset validate
```

Models:

```text
axiom science model list
axiom science model create
axiom science model fit
axiom science model validate
```

Simulation:

```text
axiom science simulation create
axiom science simulation run
axiom science simulation checkpoint
axiom science simulation restore
```

Validation:

```text
axiom science validate
axiom science benchmark
axiom science reproduce
axiom science replicate
```

Publication:

```text
axiom science publication create
axiom science publication inspect
axiom science citation graph
```

Innovation:

```text
axiom discovery list
axiom discovery register

axiom invention list
axiom invention register

axiom technology list
axiom technology create

axiom innovation list
axiom innovation create
```

Audit:

```text
axiom science provenance
axiom science audit
```

---

# 73. Profiles

```text
AXSCI_NONE
AXSCI_CORE
AXSCI_RESEARCH
AXSCI_HYPOTHESIS
AXSCI_EXPERIMENT
AXSCI_PROTOCOL
AXSCI_MEASUREMENT
AXSCI_INSTRUMENT
AXSCI_SAMPLE
AXSCI_DATASET
AXSCI_PROVENANCE
AXSCI_MODEL
AXSCI_NUMERICAL
AXSCI_SYMBOLIC
AXSCI_SIMULATION
AXSCI_VALIDATION
AXSCI_BENCHMARK
AXSCI_REPRODUCIBILITY
AXSCI_REPLICATION
AXSCI_REVIEW
AXSCI_PUBLICATION
AXSCI_DISCOVERY
AXSCI_INVENTION
AXSCI_TECHNOLOGY
AXSCI_INNOVATION
AXSCI_AUTOMATED_RESEARCH
AXSCI_AI_SCIENTIST
AXSCI_DISTRIBUTED
AXSCI_GPU
AXSCI_CLUSTER
AXSCI_WASM
AXSCI_EDGE
AXSCI_GLOBAL
AXSCI_FULL
```

---

# 74. GPU Acceleration

Scientific workloads should map naturally to Axiom GPU primitives.

Targets:

```text
matrix computation
tensor computation
PDE
ODE ensembles
Monte Carlo
MCMC
optimization
simulation
image analysis
signal processing
molecular simulation
particle simulation
neural models
large-scale parameter sweeps
```

CPU and GPU implementations must preserve semantic equivalence within declared numerical tolerances.

---

# 75. Numerical Reproducibility

Axiom must expose explicit numerical modes:

```text
fast
deterministic
reproducible
high_precision
interval
```

Floating-point nondeterminism must not be hidden.

---

# 76. Scientific Safety

Scientific execution integrates with 664.

Operations may be classified:

```text
SAFE
CONTROLLED
RESTRICTED
HIGH_RISK
PROHIBITED
```

The exact classification is provided by the safety policy.

672 provides the execution boundary, not the normative policy.

---

# 77. Physical Laboratory Boundary

For connected laboratory equipment:

```text
ScientificModel
    ↓
ExperimentPlan
    ↓
SafetyCheck
    ↓
CapabilityCheck
    ↓
HumanApproval?
    ↓
InstrumentCommand
```

The final hardware action must never occur merely because an AI generated a valid-looking protocol.

---

# 78. Autonomous Experimentation

Autonomous laboratory execution requires:

```text
research capability
instrument capability
resource capability
safety capability
authorization
optional human approval
audit
```

Every physical action must be traceable.

---

# 79. Research Privacy

Potentially sensitive data includes:

```text
human subject data
genomic data
medical measurements
private research
industrial research
proprietary datasets
unpublished results
```

672 integrates with 640.

Access must be capability and policy controlled.

---

# 80. Intellectual Property Boundary

672 may represent:

```text
patent
license
ownership
inventor
assignee
publication_date
priority
```

only as data structures.

Legal interpretation belongs to external policy/legal systems.

---

# 81. Research Ethics Boundary

Ethical approval is represented as metadata:

```axiom
struct ResearchApproval {
    authority: AuthorityRef
    protocol: ProtocolRef
    scope: Scope
    status: ApprovalStatus
}
```

672 does not create universal ethical rules.

---

# 82. Scientific Causality Boundary

Correlation:

```text
A correlates_with B
```

must not compile as:

```text
A causes B
```

Causal claims require explicit causal evidence/model metadata.

---

# 83. Scientific Confidence

Confidence must be represented with provenance.

```axiom
struct Confidence {
    value: Decimal
    method: ConfidenceMethod
    source: Provenance
}
```

The runtime must not convert confidence into certainty.

---

# 84. Uncertainty Propagation

When:

```text
z = f(x, y)
```

and `x`, `y` have uncertainty, the derived result should preserve propagated uncertainty where supported.

Methods:

```text
analytic
MonteCarlo
interval
linearized
automatic
custom
```

---

# 85. Scientific Data Quality

```axiom
struct DatasetQuality {
    completeness: Decimal?
    consistency: Decimal?
    accuracy: Decimal?
    timeliness: Decimal?
    provenance_coverage: Decimal?
}
```

These are metrics, not claims of absolute truth.

---

# 86. Missing Data

Missing values must remain distinguishable from:

```text
zero
false
unknown
not_applicable
below_detection
not_measured
redacted
```

This is a compiler/runtime semantic requirement.

---

# 87. Scientific Null Model

Scientific data types must support explicit null semantics.

Example:

```text
Missing
Unknown
NotMeasured
NotApplicable
Suppressed
```

must not collapse into ordinary zero/default values.

---

# 88. Research Event Log

Research events include:

```text
QuestionCreated
HypothesisRegistered
ProtocolVersioned
ExperimentStarted
MeasurementRecorded
DatasetCreated
DatasetTransformed
ModelFitted
ModelValidated
PredictionGenerated
ExperimentCompleted
ReviewRequested
ReviewSubmitted
PublicationReleased
ReplicationStarted
DiscoveryRegistered
InventionRegistered
TechnologyCreated
InnovationRegistered
```

---

# 89. Provenance Graph

Every scientific artifact may reference:

```text
creator
instrument
dataset
code
compiler
model
parameter
protocol
environment
execution
review
publication
```

The provenance graph must be queryable by 645.

---

# 90. Scientific Search

672 may expose structured search:

```text
axiom science search hypothesis ...
axiom science search dataset ...
axiom science search model ...
axiom science search experiment ...
axiom science search evidence ...
```

Search implementation may use 641.

---

# 91. Research Knowledge Graph

The graph may connect:

```text
Researcher
→ Project
→ Question
→ Hypothesis
→ Experiment
→ Dataset
→ Model
→ Result
→ Publication
→ Discovery
→ Technology
```

This becomes an important machine-readable research graph.

---

# 92. AI Research Context

AI agents can request a context package:

```text
ResearchContext {
    question
    relevant_knowledge
    prior_experiments
    datasets
    models
    unresolved_questions
    constraints
    safety
}
```

The context should be assembled through 645/641 rather than duplicated in 672.

---

# 93. Research Memory

Long-lived research memory includes:

```text
successful experiments
failed experiments
negative results
superseded hypotheses
parameter ranges
known limitations
replication status
```

Negative results must remain representable.

---

# 94. Failure Knowledge

A research system must preserve:

```text
failed experiment
failed model
invalid hypothesis
non-reproducible result
instrument failure
dataset corruption
```

Failure is data.

It must not be automatically deleted from the research graph.

---

# 95. Experiment Cost Model

Experiments may declare:

```text
time
compute
energy
material
instrument_usage
researcher_time
money
risk
```

Economic costs integrate with 671.

Physical resources integrate with 669.

Optimization integrates with 652.

---

# 96. Research Scheduling

A scheduler may optimize:

```text
instrument utilization
experiment ordering
sample availability
compute availability
research deadlines
```

Subject to:

```text
resource constraints
protocol constraints
safety constraints
human approval
```

---

# 97. Technology Dependency Graph

```axiom
struct TechnologyDependencyGraph {
    nodes: []TechnologyRef
    edges: []TechnologyDependency
}
```

Can represent:

```text
semiconductor
→ processor
→ computer
→ AI accelerator
→ scientific computing
```

and arbitrary dependency networks.

---

# 98. Technology Maturity Simulation

Technology development can be simulated:

```text
research
→ prototype
→ validation
→ pilot
→ deployment
```

Each transition may require explicit criteria.

---

# 99. Innovation Diffusion

Diffusion models may integrate:

```text
671 economic cost
670 human adoption
669 infrastructure
668 institutional agreements
```

The diffusion engine itself remains neutral.

---

# 100. Scientific Optimization

Possible objectives:

```text
maximize_information_gain
minimize_experiment_cost
minimize_uncertainty
maximize_reproducibility
maximize_coverage
minimize_compute
maximize_throughput
```

These are supplied objectives.

There is no universal default.

---

# 101. Scientific Digital Twin

A scientific digital twin may combine:

```text
real-world observations
physical model
simulation
state estimation
forecast
control interface
```

Pipeline:

```text
REAL WORLD
↓
SENSOR
↓
OBSERVATION
↓
STATE ESTIMATION
↓
SCIENTIFIC MODEL
↓
SIMULATION
↓
PREDICTION
↓
COMPARISON
↓
MODEL UPDATE
```

---

# 102. Digital Twin Boundary

A digital twin prediction must never automatically modify the physical system.

Physical control requires:

```text
capability
authorization
safety
optional human approval
```

---

# 103. Scientific Federated Research

Research institutions can share:

```text
datasets
models
experiments
protocols
compute
instrument access
results
```

through 668 federation primitives.

Data-sharing policy comes from 640/668.

---

# 104. Distributed Research

Large projects may distribute:

```text
dataset
simulation
Monte Carlo
parameter sweeps
experiments
model training
validation
```

Across:

```text
desktop
server
cluster
cloud adapter
edge
GPU
WASM
```

---

# 105. Checkpointing

Long scientific workloads must support:

```text
checkpoint
restore
branch
resume
partial recovery
incremental checkpoint
```

A failed 72-hour simulation must not require restarting from zero when a valid checkpoint exists.

---

# 106. Scientific Artifact Hashing

Artifacts should support content-addressed identity:

```text
dataset_hash
model_hash
experiment_hash
protocol_hash
result_hash
environment_hash
```

This integrates with 613.

---

# 107. Scientific Package Distribution

Research packages may contain:

```text
model
data_manifest
protocol
code
results
visualizations
metadata
provenance
```

Packages can be distributed through the package infrastructure of 625.

---

# 108. Compiler Integration

The compiler should recognize scientific declarations without introducing a separate language.

Example:

```axiom
science model projectile {
    variable velocity: m/s
    variable position: m

    equation:
        position' = velocity
}
```

The syntax is syntactic sugar over ordinary Axiom types, functions and metadata.

---

# 109. Scientific Genericity

Scientific objects should remain ordinary Axiom values.

For example:

```axiom
struct Measurement {
    value: Quantity
    uncertainty: Uncertainty
}
```

can be used in ordinary functions.

No special VM is required.

---

# 110. Zero-Cost Principle

If a program does not use:

```text
@science
@research
@experiment
@dataset
@scientific_model
```

then 672 must contribute no runtime code.

Metadata may be eliminated after compilation when not required.

---

# 111. Performance Architecture

Hot scientific paths must support:

```text
SIMD
vectorization
GPU
multithreading
distributed execution
memory mapping
streaming
chunked datasets
columnar layouts
sparse layouts
zero-copy buffers
```

---

# 112. Memory Architecture

Large datasets should support:

```text
memory mapped
streaming
chunked
compressed
columnar
sparse
distributed
out-of-core
```

The runtime must not assume all scientific data fits in RAM.

---

# 113. Dataset Execution

Data pipelines should support:

```text
lazy
eager
streaming
batch
incremental
distributed
```

without changing scientific semantics.

---

# 114. Scientific Query Engine

Research data can be queried through 641/642.

672 supplies domain metadata.

Example conceptual query:

```text
find experiments
where field == "materials"
and temperature > 1000 K
and reproducibility == true
```

---

# 115. Scientific Safety and Human Control

For physical experiments:

```text
AI proposal
    ↓
protocol validation
    ↓
resource validation
    ↓
safety validation
    ↓
authorization
    ↓
human approval if required
    ↓
execution
```

No automatic bypass.

---

# 116. Responsibility Map

| Capability | Owner |
|---|---|
| capability/security | 603 |
| cryptography | 610 |
| distributed data | 628 |
| observability | 633 |
| data governance/privacy | 640 |
| search/indexing | 641 |
| analytics | 642 |
| simulation infrastructure | 648 |
| optimization | 652 |
| causal/probabilistic reasoning | 653 |
| world model | 655 |
| embodied execution | 656 |
| objectives | 661 |
| evaluation/validation | 663 |
| safety | 664 |
| human oversight | 665 |
| organizations | 667 |
| federation/collaboration | 668 |
| physical infrastructure/resources | 669 |
| human researchers/labor | 670 |
| economic resources/funding | 671 |
| **science/research/innovation** | **672** |

---

# 117. Hard Separation Rules

672 MUST NOT:

```text
declare a hypothesis universally true merely because it is stored
convert correlation into causation
convert simulation into observation
convert forecast into fact
delete negative results automatically
hide provenance
silently change experimental data
grant itself laboratory authority
bypass safety controls
bypass human approval
change economic policy
change political policy
assign human value
claim legal ownership automatically
```

---

# 118. Core Invariants

Minimum target: **≥340 invariants**.

Mandatory invariant families include:

### Scientific identity

```text
artifact identity remains stable across versions
version ancestry is valid
```

### Provenance

```text
derived data references its source
model results reference model version
measurement references acquisition context
```

### Units

```text
incompatible dimensions cannot combine
```

### Uncertainty

```text
derived uncertainty cannot silently disappear
```

### Experiments

```text
registered experiment cannot silently mutate its protocol version
```

### Data

```text
raw data remains distinguishable from derived data
```

### Models

```text
model parameters remain versioned
```

### Simulation

```text
simulation state remains distinct from observed state
```

### Reproducibility

```text
reproducibility package contains required execution metadata
```

### Causality

```text
correlation != causation
```

### Hypotheses

```text
unsupported != refuted
```

### Review

```text
peer review status != truth status
```

### Discovery

```text
discovery record != universal proof
```

### AI execution

```text
AI proposal != physical execution
```

---

# 119. Test Plan

Minimum:

```text
≥ 4,200 tests
≥ 340 invariants
```

Required suites:

```text
scientific type system
unit system
dimension analysis
uncertainty propagation
dataset
dataset lineage
sample lineage
instrument
calibration
measurement
observation
protocol
experiment
hypothesis
claim
evidence
model
solver
simulation
prediction
validation
benchmark
reproduction
replication
review
publication
citation
discovery
invention
technology
innovation
research scheduling
research optimization
AI research
automated experimentation
digital twin
GPU
distributed execution
determinism
checkpoint
recovery
privacy
capability
safety
human approval
WASM
serialization
fuzzing
property testing
performance
```

---

# 120. Property-Based Testing

Required properties:

```text
unit-safe expressions never produce dimensionally invalid results
dataset derivation preserves lineage
measurement preserves uncertainty
model output references model version
simulation checkpoint restores equivalent state
deterministic runs reproduce identical outputs
negative results remain queryable
hypothesis status transitions remain valid
protocol version cannot mutate historical experiment
scientific artifacts remain content-addressable
AI-generated proposal cannot directly execute restricted hardware
real observations cannot be overwritten by simulations
```

---

# 121. Failure Recovery

Research execution must tolerate:

```text
instrument failure
network failure
GPU failure
node failure
dataset corruption
simulation interruption
worker failure
partial experiment
checkpoint corruption
external repository failure
```

Recovery states:

```text
UNKNOWN
PENDING
PARTIAL
COMPLETED
FAILED
ABORTED
RECOVERABLE
INVALIDATED
```

---

# 122. Scientific Audit

Audit records:

```text
artifact
actor
capability
timestamp
input hashes
output hashes
model version
dataset version
protocol version
compiler version
environment
approval
```

This allows a research result to be reconstructed.

---

# 123. AI Research Loop

Axiom supports:

```text
ResearchAgent
    ↓
ResearchContext
    ↓
Question
    ↓
Hypothesis
    ↓
ExperimentDesign
    ↓
SafetyCheck
    ↓
Execution
    ↓
Observation
    ↓
Analysis
    ↓
ModelUpdate
    ↓
Validation
    ↓
Replication
    ↓
KnowledgeUpdate
```

The loop may be autonomous in simulation.

Physical execution remains capability/safety/human-control gated.

---

# 124. Research Agent Memory

An AI research agent should retain:

```text
what was attempted
why it was attempted
what happened
what failed
what assumptions were used
which datasets were used
which models were invalidated
which questions remain open
```

This integrates with 650.

---

# 125. Scientific Planning

Research planning can use:

```text
645 knowledge
648 simulation
652 optimization
653 uncertainty
655 world model
669 resources
670 researchers
671 funding
672 scientific workflow
```

This produces a complete cross-layer research planning stack.

---

# 126. Scientific Civilization Graph

At civilization scale:

```text
Researcher
   ↓
Research Team
   ↓
Research Institution
   ↓
Research Program
   ↓
Scientific Field
   ↓
Knowledge
   ↓
Discovery
   ↓
Technology
   ↓
Infrastructure
   ↓
Economy
   ↓
Human Society
```

No single layer owns the entire chain.

---

# 127. Final Contract

BOOTSTRAP-672 gives Axiom a native substrate for:

```text
scientific research
hypotheses
experiments
measurements
observations
datasets
scientific models
simulation
prediction
uncertainty
validation
reproducibility
replication
peer review
publication
knowledge production
discovery
invention
technology development
innovation
technology diffusion
automated research
AI-assisted science
scientific digital twins
```

The final semantic boundary is:

> **672 can represent, execute, validate, reproduce and simulate scientific research and technology-development workflows, but it cannot manufacture scientific truth merely by declaration, replace evidence with model output, bypass safety or human control, or decide what humanity should research.**

**BOOTSTRAP-672 — ARCHITECTURE COMPLETE.**

---

# 128. Next Architecture Task

The next logical layer is:

## BOOTSTRAP-673
### Native AI Civilization-Scale Education, Learning, Knowledge Transfer, Skill Development, Training, Assessment & Human-AI Learning Runtime 5.0

This will connect:

```text
670 Human / Education / Skills
672 Science / Knowledge Production
645 Knowledge Graph
650 AI Memory
651 Personalization
652 Optimization
653 Reasoning
655 World Model
659 Emotion / Affective Computing
660 Metacognition
661 Goals / Motivation
```

while keeping **education/learning** distinct from the underlying scientific knowledge-production system of 672.
:::

**BOOTSTRAP-672 đã hoàn tất.** Chuỗi tiếp theo là **BOOTSTRAP-673 — Education, Learning, Knowledge Transfer, Skill Development, Training, Assessment & Human-AI Learning Runtime 5.0**.