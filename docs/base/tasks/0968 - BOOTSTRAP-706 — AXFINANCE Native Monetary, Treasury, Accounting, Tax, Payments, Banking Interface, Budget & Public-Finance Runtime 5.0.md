# BOOTSTRAP-706 — AXFINANCE: Native Monetary, Treasury, Accounting, Tax, Payments, Banking Interface, Budget & Public-Finance Runtime 5.0

**Namespace:** `AXFINANCE`  
**Phase:** Axiom Civilization Runtime / Financial Infrastructure  
**Status:** ARCHITECTURAL BASELINE — FROZEN TARGET  
**Depends on:** `AXLAW`, `AXIDENTITY`, `AXCIVIL`, `AXGOV`, `AXJUSTICE`

---

## 706.0 — Mục tiêu

`AXFINANCE` là runtime native của Axiom cho toàn bộ **financial state, monetary transactions, accounting, taxation, treasury, budgeting và payment infrastructure**.

Core phải hỗ trợ:

```text
Money
Currency
Account
Ledger
Transaction
Payment
Invoice
Receivable
Payable
Tax
Budget
Treasury
Asset
Liability
Equity
Settlement
Clearing
Financial Instrument
Public Finance
```

Kiến trúc phải đủ tổng quát để xây dựng:

```text
commercial finance
banking interfaces
payment systems
accounting systems
tax systems
government treasury
public budgeting
enterprise finance
personal finance
```

nhưng không hard-code một mô hình ngân hàng hoặc hệ thống thuế cụ thể.

---

# 706.1 — Core Principle

Nguyên tắc nền tảng:

> **AXFINANCE records and executes authorized financial state transitions with exact monetary semantics.**

Không được sử dụng floating-point làm authoritative monetary representation.

Không được để:

```text
AI
analytics
UI
external API
```

trực tiếp sửa financial state.

Canonical flow:

```text
Authority
    ↓
Financial Command
    ↓
Validation
    ↓
Authorization
    ↓
Ledger Event
    ↓
Accounting / Financial State
    ↓
Settlement
    ↓
Projection
```

---

# 706.2 — Monetary Model

Money phải là native value type:

```axiom
money {
    amount
    currency
}
```

Trong đó:

```text
amount = exact integer/scaled integer
currency = explicit currency identity
```

Không:

```text
float
double
```

cho authoritative money.

---

# 706.3 — Currency

```axiom
currency {
    currency_id
    code
    numeric_code
    minor_unit
    status
    effective_from
    effective_to
}
```

Phải hỗ trợ:

```text
fiat
commodity-denominated unit
local currency
foreign currency
accounting unit
custom jurisdictional monetary unit
```

---

# 706.4 — Currency Precision

Currency phải định nghĩa:

```text
minor_unit
rounding_rule
cash_rounding_rule
display_precision
```

Ví dụ:

```text
USD → 2
JPY → 0
```

Nhưng runtime không giả định tất cả currency có 2 decimal digits.

---

# 706.5 — Exact Arithmetic

Financial arithmetic phải deterministic:

```text
add
subtract
multiply
divide
allocate
round
convert
```

Mọi operation phải có explicit rounding semantics.

Ví dụ:

```axiom
money * rate
```

không được tự động quyết định rounding nếu context chưa xác định rule.

---

# 706.6 — Rounding

```axiom
round(value, rule)
```

Các rule có thể gồm:

```text
HALF_UP
HALF_DOWN
HALF_EVEN
FLOOR
CEILING
TOWARD_ZERO
AWAY_FROM_ZERO
```

Jurisdiction/accounting policy quyết định rule.

---

# 706.7 — Currency Conversion

FX conversion phải tách:

```text
source_currency
target_currency
rate
rate_source
effective_time
rounding_rule
```

```axiom
fx_quote {
    source
    target
    rate
    source_authority
    effective_at
    expires_at
}
```

---

# 706.8 — No Implicit Currency Conversion

Không cho phép:

```text
USD + EUR
```

hoặc:

```text
USD > EUR
```

nếu không có explicit conversion.

Compiler/runtime phải reject.

---

# 706.9 — Money Identity

Hai money values chỉ có thể cộng/trừ nếu:

```text
currency == currency
```

hoặc đã có explicit conversion.

Đây là **type-level financial invariant**.

---

# 706.10 — Account Model

```axiom
account {
    account_id
    owner
    account_type
    currency
    status
    jurisdiction
    opened_at
    closed_at
}
```

Account không nhất thiết là bank account.

Có thể là:

```text
cash account
bank account
wallet
tax account
budget account
receivable account
payable account
ledger account
escrow account
```

---

# 706.11 — Account Ownership

Account phải phân biệt:

```text
owner
controller
authorized_user
beneficiary
custodian
```

Không:

```text
account_user == owner
```

mặc định.

---

# 706.12 — Account Status

```text
PENDING
ACTIVE
RESTRICTED
FROZEN
SUSPENDED
CLOSED
ARCHIVED
```

State transition phải có authority và audit.

---

# 706.13 — Ledger

Ledger là authoritative accounting structure:

```axiom
ledger {
    ledger_id
    jurisdiction
    accounting_standard
    currency_policy
    accounts
    status
}
```

Ledger không được mutate tùy tiện.

---

# 706.14 — Double-Entry Principle

Accounting ledger phải hỗ trợ native double-entry:

```text
Debit
Credit
```

Một balanced transaction:

```text
Σ Debit = Σ Credit
```

theo từng accounting dimension/currency rule.

---

# 706.15 — Ledger Entry

```axiom
ledger_entry {
    entry_id
    transaction_id
    account
    side
    amount
    currency
    timestamp
    description
    dimensions
}
```

---

# 706.16 — Transaction

```axiom
financial_transaction {
    transaction_id
    type
    initiator
    authority
    entries
    status
    created_at
    effective_at
}
```

Transaction phải atomic ở authoritative ledger boundary.

---

# 706.17 — Balanced Transaction Invariant

Không được commit transaction nếu:

```text
total_debit != total_credit
```

trong cùng accounting context.

Invariant này phải được enforce ở runtime, không chỉ application layer.

---

# 706.18 — Immutable Ledger

Historical ledger entries không được sửa trực tiếp.

Correction:

```text
original transaction
      ↓
reversal
      ↓
corrected transaction
```

hoặc:

```text
adjustment entry
```

theo accounting policy.

---

# 706.19 — No Destructive Accounting Mutation

Không:

```text
UPDATE transaction amount
```

theo nghĩa thay đổi lịch sử.

Phải:

```text
superseding / adjustment event
```

và giữ historical provenance.

---

# 706.20 — Transaction State

```text
CREATED
AUTHORIZED
PENDING
POSTED
SETTLED
FAILED
REVERSED
CANCELLED
```

`POSTED` và `SETTLED` phải được phân biệt.

---

# 706.21 — Settlement

Settlement nghĩa là obligation đã được thực hiện theo settlement mechanism.

Có thể:

```text
posted != settled
```

Ví dụ payment instruction đã posted nhưng clearing chưa hoàn tất.

---

# 706.22 — Payment

```axiom
payment {
    payment_id
    payer
    payee
    amount
    currency
    method
    instruction
    settlement
    status
}
```

Payment là financial operation; settlement là một lifecycle riêng.

---

# 706.23 — Payment Lifecycle

```text
INITIATED
    ↓
AUTHORIZED
    ↓
SUBMITTED
    ↓
PROCESSING
    ↓
CLEARED
    ↓
SETTLED
```

Failure:

```text
REJECTED
FAILED
RETURNED
REVERSED
```

---

# 706.24 — Payment Methods

Core abstraction:

```text
CASH
BANK_TRANSFER
CARD
DIRECT_DEBIT
WALLET
INTERNAL_TRANSFER
CLEARING_SYSTEM
OTHER
```

Danh sách phải extensible.

---

# 706.25 — Payment Rail

Payment rail:

```axiom
payment_rail {
    rail_id
    operator
    currency
    settlement_model
    capabilities
    limits
    jurisdiction
}
```

AXFINANCE không hard-code một payment network.

---

# 706.26 — Banking Interface

Banking integration phải qua adapter:

```text
AXFINANCE
   ↓
Banking Interface
   ↓
External Bank
```

External bank không trở thành authoritative AXFINANCE database.

---

# 706.27 — External Account

```axiom
external_account {
    account_reference
    institution
    owner
    currency
    verification
    status
}
```

Sensitive banking identifiers phải được tokenized/scoped.

---

# 706.28 — Account Verification

Verification:

```text
UNKNOWN
PENDING
VERIFIED
FAILED
REVOKED
```

AI inference không được coi là account verification.

---

# 706.29 — Authorization

Financial command phải có:

```text
actor
capability
purpose
scope
authority
```

Ví dụ:

```text
finance.transfer
finance.post
finance.reverse
finance.refund
finance.tax.assess
finance.budget.allocate
```

---

# 706.30 — No Ambient Financial Authority

Không module nào mặc định có:

```text
money.transfer
ledger.write
tax.assess
budget.modify
account.freeze
```

Capabilities phải explicit.

---

# 706.31 — Multi-Signature

High-value operations có thể yêu cầu:

```text
SINGLE_SIGNATURE
DUAL_CONTROL
MULTI_SIGNATURE
AUTHORITY_SIGNATURE
```

Policy quyết định threshold.

---

# 706.32 — Separation of Duties

Runtime phải hỗ trợ:

```text
initiator
approver
poster
settler
auditor
```

và policy có thể cấm cùng một actor thực hiện nhiều role trong một transaction.

---

# 706.33 — Financial Limits

Capability có thể có:

```text
amount_limit
daily_limit
transaction_limit
currency_scope
account_scope
jurisdiction_scope
time_scope
```

Ví dụ:

```text
transfer ≤ 10,000 USD/day
```

được biểu diễn thành policy, không hard-code.

---

# 706.34 — Escrow

```axiom
escrow {
    escrow_id
    parties
    amount
    currency
    conditions
    release_rules
    authority
    status
}
```

Lifecycle:

```text
CREATED
FUNDED
HELD
RELEASE_ELIGIBLE
RELEASED
REFUNDED
DISPUTED
```

---

# 706.35 — Hold

Financial hold:

```text
hold {
    hold_id
    account
    amount
    authority
    reason
    created_at
    expires_at
    status
}
```

Hold phải được phân biệt với actual debit.

---

# 706.36 — Freeze

Account freeze:

```text
ACTIVE
→ FROZEN
```

không được tự động đồng nghĩa với:

```text
balance = 0
```

Balance vẫn phải được giữ nguyên.

---

# 706.37 — Receivable

```axiom
receivable {
    receivable_id
    debtor
    creditor
    amount
    currency
    due_date
    source
    status
}
```

Status:

```text
OPEN
PARTIALLY_PAID
PAID
OVERDUE
DISPUTED
WRITTEN_OFF
```

---

# 706.38 — Payable

```axiom
payable {
    payable_id
    creditor
    debtor
    amount
    currency
    due_date
    source
    status
}
```

---

# 706.39 — Invoice

```axiom
invoice {
    invoice_id
    issuer
    recipient
    lines
    tax
    total
    currency
    issue_date
    due_date
    status
}
```

Invoice không tự động tạo cash movement.

---

# 706.40 — Invoice Lifecycle

```text
DRAFT
ISSUED
ACCEPTED
PARTIALLY_PAID
PAID
OVERDUE
CANCELLED
CREDITED
```

---

# 706.41 — Tax Model

Tax phải được model thành:

```text
tax_rule
tax_base
tax_rate
tax_period
tax_assessment
tax_liability
tax_payment
```

Không hard-code một loại thuế duy nhất.

---

# 706.42 — Tax Rule

```axiom
tax_rule {
    rule_id
    jurisdiction
    tax_type
    base_definition
    rate
    exemptions
    deductions
    effective_from
    effective_to
}
```

---

# 706.43 — Tax Base

Tax calculation phải phân biệt:

```text
gross_amount
deductible_amount
exempt_amount
taxable_amount
```

Không tính tax trực tiếp từ gross amount trong mọi trường hợp.

---

# 706.44 — Tax Assessment

```axiom
tax_assessment {
    assessment_id
    taxpayer
    tax_type
    period
    taxable_base
    tax_amount
    rule_version
    authority
    status
}
```

---

# 706.45 — Tax Liability

Assessment và liability phải tách:

```text
assessment
    ↓
liability
```

Một assessment có thể tạo obligation nhưng không nhất thiết đã được thanh toán.

---

# 706.46 — Tax Payment

```text
tax_liability
      ↓
payment
      ↓
settlement
      ↓
liability reduction
```

Không update liability bằng direct database mutation.

---

# 706.47 — Tax Refund

Refund là transaction riêng:

```text
REFUND_REQUESTED
    ↓
AUTHORIZED
    ↓
PROCESSED
    ↓
SETTLED
```

Refund phải reference obligation gốc.

---

# 706.48 — Tax Dispute

```axiom
tax_dispute {
    dispute_id
    assessment
    claimant
    grounds
    authority
    status
    outcome
}
```

Original assessment phải được giữ nguyên lịch sử.

---

# 706.49 — Budget Model

Public budget:

```axiom
budget {
    budget_id
    jurisdiction
    fiscal_year
    authority
    revenues
    expenditures
    constraints
    status
}
```

---

# 706.50 — Fiscal Period

```axiom
fiscal_period {
    period_id
    start
    end
    jurisdiction
    calendar_type
}
```

Không giả định fiscal year = calendar year.

---

# 706.51 — Budget Allocation

```axiom
budget_allocation {
    allocation_id
    budget
    agency
    program
    amount
    currency
    authority
    period
    restrictions
}
```

Allocation không phải payment.

---

# 706.52 — Budget Commitment

Lifecycle:

```text
BUDGETED
    ↓
ALLOCATED
    ↓
COMMITTED
    ↓
OBLIGATED
    ↓
SPENT
    ↓
SETTLED
```

Mỗi state mang semantics riêng.

---

# 706.53 — Public Treasury

Treasury phải quản lý:

```text
cash position
government accounts
receipts
disbursements
debt
reserves
budget execution
liquidity
```

---

# 706.54 — Treasury Account

```axiom
treasury_account {
    account_id
    government_entity
    currency
    purpose
    authority
    status
}
```

---

# 706.55 — Public Revenue

Revenue categories:

```text
tax
fee
fine
grant
dividend
resource_revenue
other
```

Danh sách extensible.

---

# 706.56 — Public Expenditure

Expenditure phải reference:

```text
budget
program
agency
appropriation
commitment
payment
```

Không được payment nếu thiếu required authorization.

---

# 706.57 — Appropriation

```axiom
appropriation {
    appropriation_id
    budget
    authority
    purpose
    ceiling
    period
    restrictions
}
```

Invariant:

```text
spending <= authorized appropriation
```

trừ khi explicit overdraft/exception authority tồn tại.

---

# 706.58 — Public Debt

```axiom
debt_instrument {
    debt_id
    issuer
    holder
    principal
    currency
    interest_rule
    maturity
    covenants
    status
}
```

Hỗ trợ:

```text
bond
loan
credit_line
other_debt
```

---

# 706.59 — Interest

Interest calculation phải explicit:

```text
principal
rate
compounding
day_count
period
rounding
```

Không dùng một công thức global.

---

# 706.60 — Financial Instrument

General model:

```axiom
financial_instrument {
    instrument_id
    type
    issuer
    holder
    currency
    terms
    status
}
```

Specialized modules có thể xây:

```text
bond
share
derivative
deposit
loan
```

---

# 706.61 — Asset / Liability Boundary

Accounting phải phân biệt:

```text
asset
liability
equity
income
expense
```

Không dùng một generic balance field thay thế toàn bộ accounting semantics.

---

# 706.62 — Chart of Accounts

```axiom
chart_of_accounts {
    chart_id
    jurisdiction
    standard
    accounts
    version
}
```

Account hierarchy:

```text
Assets
Liabilities
Equity
Revenue
Expenses
```

có thể mở rộng theo accounting standard.

---

# 706.63 — Accounting Dimensions

Ledger entry có thể có dimensions:

```text
cost_center
department
program
project
fund
geography
grant
tax_category
```

Dimensions là metadata, không thay thế account.

---

# 706.64 — Accounting Period Close

```text
OPEN
    ↓
CLOSING
    ↓
CLOSED
    ↓
LOCKED
```

Closed period không được sửa trực tiếp.

Correction phải qua adjustment/reversal.

---

# 706.65 — Financial Statements

Runtime phải hỗ trợ projections:

```text
balance_sheet
income_statement
cash_flow
budget_execution
tax_report
trial_balance
```

Statements là derived views từ ledger.

---

# 706.66 — Statement Integrity

Một statement phải có:

```text
period
ledger
accounting_standard
rule_version
generation_time
```

Có thể regenerate từ source ledger.

---

# 706.67 — Reconciliation

Phải hỗ trợ:

```text
bank_reconciliation
ledger_reconciliation
tax_reconciliation
budget_reconciliation
interagency_reconciliation
```

Conflict không được tự động hidden.

---

# 706.68 — Reconciliation Model

```axiom
reconciliation {
    reconciliation_id
    source_a
    source_b
    period
    differences
    status
    resolver
}
```

Status:

```text
MATCHED
DIFFERENCE
INVESTIGATING
RESOLVED
```

---

# 706.69 — Settlement Network

Settlement có thể sử dụng:

```text
internal ledger
bank rail
clearing house
central settlement system
external financial institution
```

Adapter architecture phải giữ core independent.

---

# 706.70 — Clearing

Clearing và settlement phải tách:

```text
transaction
→ clearing
→ netting
→ settlement
```

Không giả định mọi payment settle instantly.

---

# 706.71 — Netting

```axiom
netting {
    participants
    obligations
    net_positions
    settlement_date
    rules
}
```

Netting engine phải deterministic.

---

# 706.72 — Atomic Financial Operations

Các operations quan trọng:

```text
transfer
post
reverse
settle
refund
allocate
assess_tax
record_payment
```

phải có idempotency.

---

# 706.73 — Idempotency

Command:

```text
command_id
```

là unique trong authority scope.

Nếu command gửi lại:

```text
same command_id
```

system trả lại original outcome thay vì thực hiện lần hai.

---

# 706.74 — Exactly-Once Semantic Effect

Transport có thể là:

```text
at-least-once
```

nhưng financial effect phải có:

```text
exactly-once semantic result
```

---

# 706.75 — Event Ledger

Mọi legally/financially significant transition phải tạo immutable event:

```text
ACCOUNT_CREATED
ACCOUNT_FROZEN
TRANSACTION_AUTHORIZED
TRANSACTION_POSTED
PAYMENT_INITIATED
PAYMENT_SETTLED
PAYMENT_REVERSED
TAX_ASSESSED
TAX_PAID
BUDGET_ALLOCATED
BUDGET_COMMITTED
EXPENDITURE_POSTED
DEBT_ISSUED
DEBT_REPAID
```

---

# 706.76 — Financial Event

```axiom
financial_event {
    event_id
    event_type
    transaction_id
    actor
    authority
    timestamp
    effective_time
    payload_hash
    causal_parent
}
```

---

# 706.77 — Historical Integrity

Không được:

```text
delete_transaction()
```

đối với authoritative history.

Chỉ:

```text
reverse_transaction()
adjust_transaction()
supersede_transaction()
```

---

# 706.78 — Financial Replay

API:

```axiom
replay_account(account_id, timestamp)
replay_ledger(ledger_id, timestamp)
replay_budget(budget_id, timestamp)
replay_taxpayer(subject, timestamp)
```

Phải deterministic.

---

# 706.79 — Simulation

Hỗ trợ:

```axiom
simulate_transfer()
simulate_tax()
simulate_budget()
simulate_cashflow()
simulate_debt()
simulate_fx()
```

Không mutate authoritative state.

---

# 706.80 — Financial Forecasting Boundary

Forecast:

```text
forecast != ledger fact
```

AI/analytics output phải được đánh dấu:

```text
DERIVED
FORECAST
SIMULATION
```

---

# 706.81 — AI Financial Assistance

AI có thể:

```text
document extraction
transaction classification
reconciliation assistance
fraud/anomaly detection
cashflow forecasting
tax form assistance
budget analysis
financial report summarization
```

Nhưng:

```text
AI prediction != financial fact
AI anomaly != fraud finding
AI recommendation != authorization
```

---

# 706.82 — Fraud Boundary

Anomaly engine có thể tạo:

```text
SUSPECTED_ANOMALY
```

Không tự động tạo:

```text
FRAUD_CONFIRMED
```

nếu determination cần human/legal process.

---

# 706.83 — AI Provenance

AI financial output phải lưu:

```text
model_id
model_version
input_references
output
confidence
generated_at
human_review
final_action
```

---

# 706.84 — AI Prompt Injection

Invoices, transaction descriptions, tax documents, emails và external financial records là:

```text
UNTRUSTED_DATA
```

Không được biến nội dung của chúng thành executable financial instructions.

---

# 706.85 — Privacy

Financial data phải được partition:

```text
identity
accounts
transactions
tax
credit
assets
liabilities
public_finance
```

API phải dùng minimum-necessary projection.

---

# 706.86 — Sensitive Financial Identifiers

Bank/account/payment identifiers nên hỗ trợ:

```text
tokenization
hash references
encrypted storage
scoped access
```

Không expose raw identifiers mặc định.

---

# 706.87 — Audit

Auditor phải trả lời:

```text
Who initiated?
Who authorized?
Who posted?
Which account?
Which amount?
Which currency?
Which rule?
Which authority?
Which external rail?
When?
Was AI involved?
What was reversed?
```

---

# 706.88 — Separation of Duties

Core phải hỗ trợ policy:

```text
initiator != approver
approver != auditor
```

nếu jurisdiction/organization yêu cầu.

---

# 706.89 — Multi-Currency Ledger

Một ledger có thể hỗ trợ nhiều currency, nhưng transaction phải giữ:

```text
transaction_currency
account_currency
conversion_rate
conversion_source
conversion_time
```

FX gain/loss phải là explicit accounting result.

---

# 706.90 — Exchange Rate

```axiom
exchange_rate {
    source_currency
    target_currency
    rate
    provider
    timestamp
    validity
}
```

Không dùng một global mutable FX value.

---

# 706.91 — Tax Calendar

Tax system phải hỗ trợ:

```text
filing_period
payment_deadline
assessment_period
fiscal_period
tax_year
```

vì chúng không nhất thiết trùng nhau.

---

# 706.92 — Tax Rule Versioning

Tax calculation phải lưu:

```text
rule_id
rule_version
jurisdiction
effective_from
effective_to
```

Historical tax assessment phải replay được.

---

# 706.93 — Budget Rule Versioning

Budget policy cũng phải versioned:

```text
budget_rule
appropriation_rule
spending_rule
authorization_rule
```

Không dùng current rule để reinterpret historical transactions.

---

# 706.94 — Public Finance Boundary

`AXFINANCE` có thể quản lý:

```text
government treasury
budget
tax
public debt
government accounting
```

Nhưng policy ownership vẫn thuộc:

```text
AXLAW / AXGOV
```

theo authority model.

---

# 706.95 — AXGOV Integration

```text
AXGOV
   ↓
administrative obligation
   ↓
AXFINANCE
   ↓
invoice / fee / budget / payment
```

AXGOV không giữ canonical financial ledger.

---

# 706.96 — AXCIVIL Integration

Civil registry có thể cung cấp:

```text
identity
property ownership
residency
civil status
```

cho AXFINANCE qua scoped projections.

Không copy civil database.

---

# 706.97 — AXIDENTITY Integration

Authentication:

```text
AXIDENTITY
    ↓
financial authorization
```

Identity không đồng nghĩa với ownership/account control.

---

# 706.98 — AXJUSTICE Integration

Court orders có thể tạo:

```text
financial obligation
asset hold
payment order
fine
restitution
```

nhưng authority source phải reference `AXJUSTICE`.

---

# 706.99 — Native Axiom Financial Types

Core language nên cung cấp native types:

```axiom
money
currency
rate
account_id
transaction_id
ledger_id
payment_id
tax_id
budget_id
```

Các type này phải có semantic checking ở compiler.

---

# 706.100 — Financial Type Safety

Compiler phải reject:

```text
money<USD> + money<EUR>
```

nếu không có conversion.

Có thể hỗ trợ:

```axiom
money<USD>
money<VND>
money<JPY>
```

như generic/semantic type specialization.

---

# 706.101 — Units

Ngoài currency, financial runtime phải hỗ trợ units:

```text
percent
basis_point
rate
quantity
share
```

Không dùng raw `float` cho:

```text
tax_rate
interest_rate
ownership_share
```

nếu semantic precision yêu cầu exact representation.

---

# 706.102 — Percentage

```axiom
percentage {
    numerator
    denominator
}
```

hoặc fixed-point representation.

Ví dụ:

```text
5% = 500 basis points
```

phải giữ exact semantics.

---

# 706.103 — Ownership Shares

Ownership share phải hỗ trợ exact fraction:

```axiom
share {
    numerator
    denominator
}
```

Không dùng floating-point để biểu diễn:

```text
1/3 ownership
```

---

# 706.104 — Financial Limits

Amount limits phải exact:

```axiom
limit {
    amount
    currency
    period
    scope
}
```

Không dùng approximate comparison.

---

# 706.105 — Concurrency

Financial transactions phải hỗ trợ optimistic concurrency:

```text
account_version
ledger_version
expected_version
```

Nếu state thay đổi:

```text
CONFLICT
```

không silently overwrite.

---

# 706.106 — Race Protection

Ví dụ:

```text
balance = 100
```

hai concurrent withdrawals:

```text
60
60
```

không được cả hai commit nếu available balance policy không cho phép.

---

# 706.107 — Atomic Balance Transition

Balance projection phải được derivable:

```text
opening_balance
+
credits
-
debits
=
closing_balance
```

Canonical truth vẫn là ledger.

---

# 706.108 — Negative Balance

Negative balance phải là explicit policy:

```text
ALLOW
DENY
LIMITED
AUTHORIZED_OVERDRAFT
```

Không implicit.

---

# 706.109 — Chargeback

Payment systems phải hỗ trợ:

```text
chargeback
return
refund
reversal
adjustment
```

Mỗi operation có semantic khác nhau.

---

# 706.110 — Dispute

```axiom
financial_dispute {
    dispute_id
    transaction
    claimant
    reason
    evidence
    authority
    status
}
```

Lifecycle:

```text
FILED
UNDER_REVIEW
RESOLVED
ESCALATED
CLOSED
```

Original transaction không bị xóa.

---

# 706.111 — Financial Holds

Các hold có thể đến từ:

```text
legal authority
risk policy
settlement requirement
escrow
tax authority
internal control
```

Source phải explicit.

---

# 706.112 — Account Closure

Closure:

```text
REQUESTED
→ REVIEW
→ AUTHORIZED
→ CLOSED
```

Nếu balance != zero, closure policy phải xác định:

```text
transfer
settlement
write-off
refund
```

---

# 706.113 — Dormancy

Account có thể:

```text
ACTIVE
DORMANT
REACTIVATION_PENDING
REACTIVATED
```

Dormancy không tự động đồng nghĩa với closure.

---

# 706.114 — Financial Notifications

```axiom
financial_notification {
    recipient
    transaction
    type
    channel
    timestamp
    delivery_status
}
```

Không để notification system trở thành source of truth.

---

# 706.115 — Receipts

Receipt:

```axiom
receipt {
    receipt_id
    transaction
    issuer
    amount
    currency
    timestamp
    signature
}
```

Receipt là signed projection.

---

# 706.116 — Financial Documents

Documents:

```text
invoice
receipt
statement
tax_form
payment_order
budget_report
financial_statement
```

phải reference authoritative financial records.

---

# 706.117 — Document Hash

Mỗi authoritative generated document phải có:

```text
content_hash
source_version
generation_time
issuer
signature
```

---

# 706.118 — Retention

Financial records phải hỗ trợ:

```text
ACTIVE
CLOSED
ARCHIVED
LEGAL_HOLD
SEALED
DESTROYED
```

Destruction chỉ khi policy cho phép.

---

# 706.119 — Legal Hold

```axiom
financial_legal_hold {
    hold_id
    scope
    authority
    created_at
    release_condition
}
```

Hold phải ngăn destructive operations trong scope.

---

# 706.120 — Distributed Ledger Boundary

AXFINANCE không yêu cầu blockchain.

Core ledger có thể dùng:

```text
append-only database
event store
distributed database
consensus system
```

Blockchain chỉ là một possible external implementation, không phải architectural requirement.

---

# 706.121 — Cryptographic Integrity

Authoritative events có thể sử dụng:

```text
hash chaining
digital signatures
Merkle structures
trusted timestamps
```

để phát hiện tampering.

---

# 706.122 — Audit Proof

Audit subsystem phải có thể tạo:

```text
proof(event)
proof(transaction)
proof(account_state)
proof(statement)
```

để chứng minh state được derived từ authoritative history.

---

# 706.123 — Recovery

Crash recovery phải đảm bảo:

```text
no lost posted transaction
no duplicated settlement
no corrupted balance
no orphaned ledger entry
```

---

# 706.124 — Disaster Recovery

Phải hỗ trợ:

```text
snapshot
incremental log
event replay
cross-region replication
point-in-time recovery
```

---

# 706.125 — Backup Integrity

Backup phải giữ:

```text
ledger
event history
rule versions
schema versions
authorization metadata
```

Nếu thiếu rule version, historical financial state không được coi là fully reproducible.

---

# 706.126 — Formal Invariants

```text
FIN-INV-01  Authoritative money uses exact arithmetic.
FIN-INV-02  Currency mismatch cannot be silently ignored.
FIN-INV-03  Every posted accounting transaction is balanced.
FIN-INV-04  Historical ledger entries are immutable.
FIN-INV-05  Corrections use reversal/adjustment/superseding events.
FIN-INV-06  Financial authority is explicit.
FIN-INV-07  No ambient financial authority exists.
FIN-INV-08  High-impact transactions may require multi-party authorization.
FIN-INV-09  Duplicate commands cannot duplicate financial effects.
FIN-INV-10  Settlement and posting are distinct states.
FIN-INV-11  Tax assessment and tax payment are distinct states.
FIN-INV-12  Budget allocation and payment are distinct states.
FIN-INV-13  AI output is not authoritative financial fact.
FIN-INV-14  AI anomaly detection is not automatically a fraud finding.
FIN-INV-15  Historical financial state is deterministically replayable.
FIN-INV-16  Simulation cannot mutate authoritative state.
FIN-INV-17  Account balance is derived from authoritative ledger.
FIN-INV-18  Closed periods cannot be silently modified.
FIN-INV-19  Legal holds block prohibited destruction.
FIN-INV-20  Financial identifiers are scope-controlled.
FIN-INV-21  Offline operation cannot create unauthorized monetary authority.
FIN-INV-22  FX conversion is explicit and auditable.
FIN-INV-23  Tax calculations retain rule version.
FIN-INV-24  Public spending cannot exceed authorized limits without explicit authority.
FIN-INV-25  Financial state survives AI/service failure without corruption.
```

---

# 706.127 — Canonical Architecture

```text
                         ┌──────────────────┐
                         │      AXLAW       │
                         └────────┬─────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │ Financial Authority    │
                     │ / Policy / Rules       │
                     └───────────┬────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │        AXFINANCE            │
                  │                             │
                  │ Money / Currency            │
                  │ Accounts                    │
                  │ Ledger                      │
                  │ Payments                    │
                  │ Clearing / Settlement       │
                  │ Tax                         │
                  │ Budget                      │
                  │ Treasury                    │
                  │ Accounting                  │
                  │ Debt                        │
                  │ Financial Instruments       │
                  │ Reconciliation               │
                  └──────────────┬──────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
       ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
       │ AXGOV        │  │ AXBANK       │  │ External     │
       │ Public       │  │ Interface    │  │ Rails        │
       │ Finance      │  │              │  │              │
       └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
                       ┌───────────────────┐
                       │ Capability +      │
                       │ Effect Engine     │
                       └─────────┬─────────┘
                                 ▼
                       ┌───────────────────┐
                       │ Financial Command │
                       │ Engine             │
                       └─────────┬─────────┘
                                 ▼
                       ┌───────────────────┐
                       │ Immutable Ledger  │
                       │ + Event Store     │
                       └─────────┬─────────┘
                                 ▼
                       ┌───────────────────┐
                       │ Financial State   │
                       │ Projections       │
                       └───────────────────┘
```

---

# 706.128 — Cross-Axiom Architecture

```text
                    AXLAW
                      │
       ┌──────────────┼───────────────┐
       ▼              ▼               ▼
    AXGOV          AXJUSTICE       AXCIVIL
       │              │               │
       └──────────────┼───────────────┘
                      ▼
                  AXFINANCE
                      │
       ┌──────────────┼───────────────┐
       ▼              ▼               ▼
   AXIDENTITY      AXHEALTH       AXEDUCATION
                      │
                      ▼
                 External Banks
                 Payment Rails
                 Clearing Systems
```

`AXFINANCE` sở hữu **financial state**, nhưng không sở hữu identity, civil, legal hay government workflow state của các domain khác.

---

# 706.129 — Native Axiom API

API tối thiểu:

```axiom
create_currency()
create_account()
open_account()
freeze_account()
close_account()

create_transaction()
authorize_transaction()
post_transaction()
reverse_transaction()

initiate_payment()
authorize_payment()
submit_payment()
settle_payment()
refund_payment()

create_invoice()
record_receivable()
record_payable()

create_tax_rule()
calculate_tax()
assess_tax()
record_tax_payment()
issue_tax_refund()

create_budget()
allocate_budget()
commit_budget()
record_expenditure()

create_treasury_account()
issue_debt()
record_debt_payment()

reconcile_accounts()
reconcile_bank()
generate_statement()

replay_ledger()
replay_account()
simulate_transaction()
simulate_budget()
```

---

# 706.130 — End-to-End Commercial Flow

```text
Customer
   ↓
Invoice
   ↓
Receivable
   ↓
Payment Instruction
   ↓
Authorization
   ↓
Payment Rail
   ↓
Clearing
   ↓
Settlement
   ↓
Ledger Posting
   ↓
Receipt
   ↓
Statement
```

Mỗi bước có state riêng và provenance.

---

# 706.131 — End-to-End Government Flow

```text
AXGOV
   ↓
Administrative Fee / Tax / Obligation
   ↓
AXFINANCE
   ↓
Assessment
   ↓
Liability
   ↓
Payment
   ↓
Settlement
   ↓
Treasury Ledger
   ↓
Budget / Revenue Projection
```

---

# 706.132 — End-to-End Public Expenditure

```text
Budget
   ↓
Appropriation
   ↓
Allocation
   ↓
Commitment
   ↓
Obligation
   ↓
Invoice
   ↓
Payment
   ↓
Settlement
   ↓
Accounting
```

Không được bỏ qua intermediate states nếu chúng có legal/accounting significance.

---

# 706.133 — Compiler Integration

Axiom compiler phải hiểu các semantic types:

```text
money
currency
rate
percentage
share
account
transaction
```

Compiler có thể phát hiện compile-time:

```text
currency mismatch
invalid money arithmetic
invalid capability usage
missing effect
```

---

# 706.134 — Runtime Integration

Runtime enforce:

```text
authorization
limits
ledger balance
double-entry
idempotency
concurrency
audit
signatures
settlement
```

Compiler và runtime cùng tạo defense-in-depth.

---

# 706.135 — Financial DSL Layer

Trên core financial primitives có thể xây DSL:

```axiom
tax
budget
accounting
payment
treasury
```

Nhưng DSL chỉ là higher-level layer.

Core vẫn phải đủ nhỏ để compiler hiểu trực tiếp các invariant quan trọng.

---

# 706.136 — Test Matrix

Phải có:

```text
money_tests
currency_tests
rounding_tests
fx_tests
account_tests
ledger_tests
double_entry_tests
payment_tests
settlement_tests
tax_tests
budget_tests
treasury_tests
debt_tests
reconciliation_tests
authorization_tests
concurrency_tests
replay_tests
simulation_tests
AI_boundary_tests
security_tests
disaster_recovery_tests
```

---

# 706.137 — Property Tests

Các property bắt buộc:

```text
sum(debits) == sum(credits)

replay(ledger) == current_state

reverse(transaction)
    restores accounting effect

duplicate(command)
    does not duplicate effect

currency mismatch
    cannot silently execute

unauthorized transfer
    cannot post

closed_period mutation
    cannot directly modify history

simulation
    does not alter ledger
```

---

# 706.138 — End-to-End Test

Canonical test:

```text
Create Account
      ↓
Issue Invoice
      ↓
Create Receivable
      ↓
Initiate Payment
      ↓
Authorize
      ↓
Clear
      ↓
Settle
      ↓
Post Ledger
      ↓
Generate Receipt
      ↓
Generate Statement
      ↓
Reverse
      ↓
Replay Full History
```

Expected:

```text
replayed_state == authoritative_state
```

---

# 706.139 — Public Finance Test

```text
Create Budget
      ↓
Appropriation
      ↓
Agency Allocation
      ↓
Commitment
      ↓
Obligation
      ↓
Expenditure
      ↓
Payment
      ↓
Settlement
      ↓
Financial Statement
      ↓
Budget Execution Report
      ↓
Replay
```

---

# 706.140 — Completion Criteria

`BOOTSTRAP-706` chỉ hoàn thành khi:

1. Money type frozen.
2. Currency model frozen.
3. Exact arithmetic frozen.
4. FX model frozen.
5. Account model frozen.
6. Ledger model frozen.
7. Double-entry semantics frozen.
8. Transaction model frozen.
9. Payment lifecycle frozen.
10. Clearing/settlement semantics frozen.
11. Tax model frozen.
12. Budget model frozen.
13. Treasury model frozen.
14. Accounting model frozen.
15. Debt model frozen.
16. Financial instrument boundary frozen.
17. Reconciliation model frozen.
18. Authorization model frozen.
19. Multi-signature/separation-of-duties model frozen.
20. AI boundary frozen.
21. Privacy model frozen.
22. Immutable event model frozen.
23. Temporal semantics frozen.
24. Replay semantics frozen.
25. Distributed transaction semantics frozen.
26. Native financial types frozen.
27. Compiler financial type checking frozen.
28. Native Axiom API frozen.
29. Security invariants frozen.
30. Commercial and public-finance end-to-end tests defined.

---

# 706.141 — Definition of Done

```text
BOOTSTRAP-706
STATUS: COMPLETE / FROZEN

AXFINANCE 5.0
    ├── Exact Money
    ├── Currency
    ├── FX
    ├── Accounts
    ├── Double-Entry Ledger
    ├── Transactions
    ├── Payments
    ├── Clearing
    ├── Settlement
    ├── Invoices
    ├── Receivables / Payables
    ├── Tax
    ├── Budget
    ├── Treasury
    ├── Public Finance
    ├── Debt
    ├── Financial Instruments
    ├── Reconciliation
    ├── Multi-Signature Authorization
    ├── Capability Security
    ├── Immutable Audit
    ├── Exact Replay
    ├── Simulation
    ├── Distributed Financial Execution
    ├── Native Financial Types
    ├── Compiler-Level Financial Safety
    └── AI Assistance Boundary
```

**BOOTSTRAP-706 / AXFINANCE hoàn thành architectural baseline.**

### Task kế tiếp

**BOOTSTRAP-707 — AXHEALTH: Native Healthcare, Medical Records, Clinical Workflow, Pharmacy, Laboratory, Public Health & Health-Data Runtime 5.0**