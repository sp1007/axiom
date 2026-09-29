# BOOTSTRAP-783 — AXDOC

**Native Axiom Documentation, Language Reference, API Documentation, Specification Extraction, Source/ABI/IR Documentation, Cross-Linking, Generated Documentation, AI-Readable Semantic Index & Documentation Build Runtime 5.0**

**Namespace:** `AXDOC`  
**Status:** **FROZEN — Target 5.0**  
**ABI:** `AXDOC_ABI_1`

---

# 1. Mục tiêu

`AXDOC` là hệ thống documentation native của Axiom.

Nó không chỉ sinh HTML từ comment mà xây dựng một **semantic documentation system** lấy thông tin từ:

```text
Axiom source
      │
      ├── declarations
      ├── types
      ├── traits
      ├── functions
      ├── modules
      ├── attributes
      ├── ABI metadata
      ├── compiler semantic model
      ├── test metadata
      └── specification metadata
              │
              ▼
            AXDOC
              │
      ┌───────┼────────┬──────────┐
      ▼       ▼        ▼          ▼
   Human    IDE       AI        Tooling
   docs    symbols   semantic   search
```

Mục tiêu là một định nghĩa/API chỉ cần khai báo một lần nhưng có thể cung cấp:

```text
source documentation
API reference
language reference
ABI documentation
example
cross-reference
test links
AI metadata
search index
```

---

# 2. Triết lý thiết kế

## 2.1 Documentation là semantic artifact

Documentation không được coi chỉ là text.

```text
symbol
+
signature
+
type
+
effects
+
ownership
+
ABI
+
examples
+
tests
+
references
```

tạo thành một documentation node.

---

## 2.2 Source là nguồn sự thật cho API

AXDOC không cho phép documentation nói một signature không tồn tại.

Ví dụ source:

```text
fn parse_i32(input: Str) -> Result<i32, ParseError>
```

AXDOC phải biết chính xác:

```text
parse_i32(Str) -> Result<i32, ParseError>
```

Nếu comment nói:

```text
parse_i32(Bytes)
```

AXDOC phải phát hiện inconsistency.

---

## 2.3 Documentation không thay đổi semantics

AXDOC không được:

- thay đổi AST
- thay đổi type checking
- thay đổi ABI
- tạo runtime behavior
- inject code vào executable

---

# 3. Boundary

## AXDOC sở hữu

```text
documentation syntax
documentation AST
semantic documentation model
API extraction
language reference model
cross references
examples
generated documentation
documentation index
search
AI metadata
documentation validation
documentation builds
```

## AXDOC không sở hữu

```text
AXCOMPILER → compiler semantics
AXSTANDARD → API implementation
AXTEST → testing
AXBUILD → project build graph
AXPACKAGE → package distribution
AXIDE → editor/IDE UI
AXABI → ABI rules
```

---

# 4. Documentation Sources

AXDOC nhận dữ liệu từ:

```text
1. source declarations
2. documentation comments
3. attributes
4. compiler semantic metadata
5. specification files
6. test metadata
7. ABI metadata
8. generated metadata
9. external reference documents
```

Pipeline:

```text
Source
  ↓
AXCOMPILER
  ↓
Semantic Model
  ↓
AXDOC Extractor
  ↓
Doc IR
  ↓
Doc Graph
  ↓
Renderer / Indexer / AI
```

---

# 5. Documentation Comment

Axiom có documentation comment:

```text
/// Adds two integers.
///
/// Returns the mathematical sum of `a` and `b`.
fn add(a: i32, b: i32) -> i32
```

AXDOC đọc comment nhưng compiler vẫn có thể bỏ qua phần prose.

---

# 6. Documentation Block

Cho documentation dài:

```text
/**
# Overview

Long-form documentation.

## Example

...
*/
```

Hỗ trợ:

```text
paragraph
heading
list
table
code
quote
note
warning
example
math
link
reference
```

---

# 7. Structured Documentation

Có thể dùng annotations:

```text
@doc {
    summary = "Parse a signed 32-bit integer."
    errors = [InvalidInput, Overflow]
    allocation = none
    blocking = false
}
```

Structured metadata có priority cao hơn prose khi kiểm tra máy.

---

# 8. Canonical Documentation Model

```text
DocNode {
    id
    kind
    symbol
    module
    title
    summary
    body
    signature
    attributes
    parameters[]
    returns
    errors[]
    effects
    examples[]
    references[]
    tests[]
    source_location
    abi
    metadata
}
```

---

# 9. Documentation Kinds

```text
MODULE
PACKAGE
TYPE
STRUCT
ENUM
UNION
TRAIT
FUNCTION
METHOD
CONSTANT
VARIABLE
MACRO
ATTRIBUTE
ERROR
FIELD
VARIANT
OPERATOR
PROTOCOL
ABI
TARGET
FEATURE
CONCEPT
GUIDE
TUTORIAL
REFERENCE
EXAMPLE
```

---

# 10. Documentation Identity

Mỗi documentation node có ID ổn định:

```text
doc://ax.standard.string/String
doc://ax.standard.string/String.push
doc://ax.standard.result/Result
```

Không dùng source line làm identity.

Source location chỉ là metadata.

---

# 11. Symbol Identity

AXDOC sử dụng compiler symbol identity:

```text
SymbolId
```

kết hợp:

```text
package
module
namespace
name
generic signature
declaration kind
```

Điều này tránh collision giữa:

```text
foo()
```

ở nhiều module.

---

# 12. Overload

Nếu Axiom hỗ trợ overload:

```text
foo(i32)
foo(f64)
foo(Str)
```

mỗi declaration là một DocNode riêng.

Reference:

```text
foo(i32)
```

phải resolve đúng overload.

---

# 13. Generic Documentation

Ví dụ:

```text
fn max<T: Ordered>(a: T, b: T) -> T
```

AXDOC hiển thị:

```text
max<T: Ordered>(a: T, b: T) -> T
```

và phải lưu:

```text
generic parameters
constraints
associated types
where clauses
```

---

# 14. Trait Documentation

```text
trait Ordered<T> {
    fn compare(self, other: T) -> Ordering
}
```

AXDOC tạo:

```text
Trait
 ├── associated types
 ├── required methods
 ├── provided methods
 ├── implementations
 └── implementors
```

---

# 15. Struct Documentation

```text
struct User {
    id: u64
    name: String
}
```

Documentation:

```text
User
 ├── id: u64
 └── name: String
```

Có thể ghi:

```text
/// Stable identity of the user.
id: u64
```

---

# 16. Enum Documentation

```text
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

AXDOC tạo cross-reference tới:

```text
Result
Ok
Err
T
E
```

---

# 17. Module Documentation

Module có:

```text
module ax.standard.string
```

với:

```text
overview
public API
submodules
examples
dependencies
```

Private symbols mặc định không xuất hiện public docs.

---

# 18. Visibility

AXDOC tôn trọng:

```text
public
internal
private
package
protected
```

Profile:

```text
PUBLIC
PACKAGE
INTERNAL
FULL
```

`PUBLIC` là mặc định khi sinh thư viện phân phối.

---

# 19. Documentation Visibility

Một symbol có thể:

```text
visible in source
visible in package docs
visible in internal docs
hidden from docs
```

Không được nhầm:

```text
documentation visibility
```

với:

```text
language visibility
```

---

# 20. API Extraction

AXDOC phải tự động extract:

```text
public types
public functions
public constants
public traits
public errors
public attributes
```

Không yêu cầu developer copy signature vào documentation.

---

# 21. Signature Canonicalization

AXDOC dùng compiler formatter để canonicalize:

```text
generic order
spacing
type names
attributes
receiver
return type
```

Không tự xây một parser type riêng nếu compiler semantic information đã có.

---

# 22. Documentation Validation

AXDOC kiểm tra:

```text
missing parameter docs
invalid reference
invalid code example
wrong type
wrong return documentation
unknown error
obsolete symbol
duplicate anchor
broken link
invalid syntax
```

Mức:

```text
ERROR
WARNING
INFO
```

---

# 23. Parameter Documentation

Ví dụ:

```text
/// Parses `input`.
///
/// # Parameters
/// - `input`: UTF-8 text to parse.
/// - `base`: Numeric base.
///
/// # Returns
/// Parsed integer.
fn parse(input: Str, base: u32) -> Result<i32, ParseError>
```

AXDOC đối chiếu:

```text
input ✓
base ✓
missing parameter? ✗
```

---

# 24. Return Documentation

Nếu function có result:

```text
# Returns
```

AXDOC có thể validate rằng type thực tế khớp semantic model.

Không yêu cầu mọi function phải có prose return documentation.

---

# 25. Error Documentation

Nếu:

```text
Result<T, ParseError>
```

AXDOC có thể resolve:

```text
ParseError
```

và liệt kê:

```text
invalid input
overflow
encoding
```

nếu error type có metadata.

---

# 26. Effect Documentation

AXDOC có thể lấy từ compiler metadata:

```text
allocates
blocks
io
unsafe
panic
async
```

Ví dụ:

```text
Effects:
    allocation: none
    blocking: false
    unsafe: false
    panic: false
```

Không được suy đoán effects từ prose.

---

# 27. Ownership Documentation

AXDOC có thể biểu diễn:

```text
borrowed
owned
mutable
consumed
returned
```

Ví dụ:

```text
fn find(data: Str, key: Str) -> Option<Str>
```

documentation có thể hiển thị lifetime/ownership semantics nếu compiler cung cấp.

---

# 28. ABI Documentation

AXDOC tích hợp AXABI:

```text
Function
 ↓
native ABI
 ↓
calling convention
 ↓
parameter representation
 ↓
return representation
```

Nhưng chi tiết ABI cấp thấp chỉ hiển thị trong:

```text
ABI
INTERNAL
COMPILER
```

profiles.

---

# 29. C ABI Documentation

`extern "C"` được đánh dấu:

```text
ABI: C
```

và AXDOC hiển thị:

```text
C-compatible
```

nếu compiler xác nhận.

---

# 30. Examples

Example là first-class documentation artifact:

```text
/// # Example
///
/// ```axiom
/// let x = add(2, 3)
/// assert(x == 5)
/// ```
```

Example có metadata:

```text
Example {
    language
    source
    expected
    runnable
    target
}
```

---

# 31. Doctest

AXDOC có thể chuyển example thành AXTEST test:

```text
documentation example
        ↓
AXTEST
        ↓
compile
        ↓
run
        ↓
validate
```

Đây là một integration quan trọng.

---

# 32. Doctest Isolation

Example không được thực thi trong process documentation generator nếu nó có khả năng:

- filesystem destructive
- network
- process spawning
- privileged operation

Doctest chạy theo AXTEST isolation policy.

---

# 33. Example Modes

```text
COMPILE_ONLY
RUN
EXPECTED_OUTPUT
PANIC_EXPECTED
ERROR_EXPECTED
```

---

# 34. Specification Documentation

AXDOC hỗ trợ tài liệu cấp ngôn ngữ:

```text
language reference
semantic specification
ABI reference
runtime reference
standard library reference
platform reference
```

Không giới hạn ở API docs.

---

# 35. Specification Node

```text
SpecNode {
    id
    section
    title
    body
    normative
    references[]
    invariants[]
    tests[]
    implementation[]
}
```

`normative = true` nghĩa nội dung là specification requirement.

---

# 36. Spec ↔ Test Traceability

Ví dụ:

```text
SPEC:
AXMEMORY §4.2 ownership

        ↓

TEST:
MEM-OWN-017

        ↓

IMPLEMENTATION:
compiler/lifetime.ax
```

AXDOC phải hiển thị liên kết.

---

# 37. Spec ↔ Implementation

Một specification section có thể link:

```text
implementation component
source file
symbol
test
invariant
```

Điều này đặc biệt quan trọng với Axiom vì project có số lượng subsystem lớn.

---

# 38. Invariant Documentation

Các invariant như:

```text
TEST-INV-01
```

có thể trở thành first-class nodes.

Ví dụ:

```text
Invariant
 ├── definition
 ├── affected subsystem
 ├── tests
 └── implementation
```

---

# 39. Documentation Graph

AXDOC xây graph:

```text
Module
 │
 ├── Type
 │    ├── Field
 │    └── Method
 │
 ├── Function
 │
 ├── Trait
 │    └── Implementor
 │
 └── Example
```

Cross-system:

```text
API
 ↓
ABI
 ↓
Test
 ↓
Implementation
 ↓
Spec
```

---

# 40. Cross References

Syntax:

```text
[`String`]
[`Result<T,E>`]
[`parse_i32`]
```

AXDOC resolve theo semantic symbol ID.

Broken references là build error trong strict mode.

---

# 41. External Links

External links có:

```text
url
title
source
trust
```

AXDOC không tự xác minh nội dung external website.

---

# 42. Link Stability

Internal links dùng:

```text
stable symbol ID
```

không dùng:

```text
generated HTML filename
```

Renderer quyết định URL cuối cùng.

---

# 43. Search Index

AXDOC tạo:

```text
.axdoc-index
```

Index fields:

```text
symbol
module
title
summary
signature
tags
kind
visibility
target
text
references
```

---

# 44. Search

API:

```text
doc_search(query)
doc_find_symbol(symbol)
doc_find_type(type)
doc_find_module(module)
doc_find_reference(id)
```

Search ranking phải deterministic.

---

# 45. AI Semantic Index

AXDOC tạo một semantic representation tối ưu cho AI:

```text
AIDocNode {
    symbol
    signature
    purpose
    parameters
    returns
    errors
    effects
    ownership
    examples
    related_symbols
    tests
    specification
    implementation
}
```

---

# 46. AI Query

Ví dụ:

```text
doc_ai_lookup("How do I create a UTF-8 string?")
```

có thể trả:

```text
String::from_utf8
String::new
Str
Bytes
```

kèm constraints.

---

# 47. AI Must Not Invent API

AI index chỉ được lấy từ:

```text
compiler semantic model
AXDOC metadata
```

Nếu API không tồn tại:

```text
NOT_FOUND
```

không tự sinh documentation.

---

# 48. AI Context Pack

AXDOC có thể tạo:

```text
DocContextPack
```

cho agent:

```text
symbol
related symbols
signature
constraints
examples
tests
spec
ABI
```

Agent không cần đọc toàn repository.

Đây là một mục tiêu quan trọng của Axiom AI-friendly architecture.

---

# 49. Documentation Metadata

```text
DocMetadata {
    stable_id
    version
    package
    module
    symbol
    visibility
    since
    deprecated
    experimental
    target
    feature
    tags[]
}
```

---

# 50. Versioning

Symbol có:

```text
since
deprecated_since
removed_since
replacement
```

Ví dụ:

```text
@deprecated(
    since = "2.1",
    replacement = "new_api"
)
```

AXDOC hiển thị migration path.

---

# 51. Compatibility

AXDOC có thể lấy AXABI compatibility:

```text
source compatible
ABI compatible
behavior compatible
deprecated
removed
```

Không tự đánh giá compatibility; compiler/ABI metadata cung cấp.

---

# 52. Documentation Diff

AXDOC hỗ trợ:

```text
axtdoc diff old new
```

Phân loại:

```text
ADDED
REMOVED
CHANGED
DEPRECATED
SIGNATURE_CHANGED
ABI_CHANGED
DOCUMENTATION_CHANGED
```

---

# 53. API Diff

Ví dụ:

```text
old:
fn foo(i32) -> i32

new:
fn foo(i64) -> i64
```

AXDOC báo:

```text
SIGNATURE_CHANGED
```

và link tới AXABI/AXTEST compatibility nếu có.

---

# 54. Documentation Build

Pipeline:

```text
AXBUILD
   ↓
AXCOMPILER semantic extraction
   ↓
AXDOC extraction
   ↓
Doc IR
   ↓
validation
   ↓
cross-reference
   ↓
index
   ↓
render
```

---

# 55. Output Formats

Native renderer contract:

```text
HTML
TEXT
MARKDOWN
JSON
BINARY_INDEX
```

PDF/eBook không phải core AXDOC.

Có thể dùng external renderer.

---

# 56. HTML Renderer

HTML output:

```text
index
module
symbol
type
function
trait
example
spec
```

Có search client/index.

Không cần JavaScript framework nặng.

---

# 57. Static Documentation

Mục tiêu:

```text
documentation/
    index.html
    ax.standard/
    ax.runtime/
    ax.compiler/
```

Không cần server.

---

# 58. Offline Documentation

Documentation phải chạy:

```text
offline
```

với tất cả internal references.

Không có CDN dependency mặc định.

---

# 59. Markdown Renderer

Dùng cho:

```text
README
API references
source docs
AI context
repository docs
```

AXDOC Markdown phải canonical.

---

# 60. JSON Documentation

Canonical machine format:

```text
DocBundle {
    schema
    package
    version
    nodes[]
    references[]
    index
    metadata
}
```

---

# 61. Binary Documentation Bundle

`.axdoc`:

```text
header
string table
symbol table
doc nodes
cross-reference table
search index
metadata
checksum
```

Mục tiêu:

- nhanh
- compact
- mmap-friendly
- random access

---

# 62. Zero-Copy Reading

Doc reader có thể:

```text
mmap(.axdoc)
```

và lấy:

```text
DocNode
```

mà không cần deserialize toàn bộ.

---

# 63. Compression

Compression là optional.

Core reader phải hỗ trợ uncompressed canonical representation.

Compressed bundles có:

```text
compression = ...
```

---

# 64. Deterministic Documentation

Cùng source + cùng toolchain:

```text
DocBundle A
DocBundle B
```

phải:

```text
A == B
```

trừ external/non-deterministic metadata được explicit loại bỏ.

---

# 65. Canonicalization

Loại bỏ:

```text
absolute source paths
timestamps
machine IDs
temporary names
random IDs
```

Stable:

```text
symbol IDs
package IDs
signatures
content hashes
```

---

# 66. Source Mapping

DocNode:

```text
SourceLocation {
    file
    line
    column
    byte_offset
}
```

Path có thể canonicalized relative project root.

---

# 67. Documentation Coverage

AXDOC có thể báo:

```text
public API documented
public API undocumented
examples
deprecated APIs
broken references
```

Không biến documentation coverage thành correctness score.

---

# 68. Missing Documentation Policy

Profiles:

```text
PERMISSIVE
WARNING
STRICT
```

Ví dụ:

```text
library release → STRICT
application → WARNING
internal prototype → PERMISSIVE
```

---

# 69. Documentation Lint

Lint:

```text
DOC001 missing summary
DOC002 invalid symbol reference
DOC003 missing parameter
DOC004 stale example
DOC005 deprecated symbol
DOC006 malformed markup
DOC007 duplicate heading
DOC008 broken external link
```

---

# 70. Documentation Examples as Tests

Mỗi runnable example có:

```text
doc_id
test_id
```

Do đó:

```text
documentation change
```

có thể trigger:

```text
AXTEST doctest
```

---

# 71. Documentation Build Cache

Cache key:

```text
source hash
semantic model hash
doc comment hash
compiler fingerprint
AXDOC version
renderer version
```

Thay đổi prose chỉ rebuild affected docs.

---

# 72. Incremental Documentation

Nếu thay đổi:

```text
module A
```

AXDOC chỉ cần rebuild:

```text
A
pages referencing A
search index affected nodes
```

không phải toàn bộ repository.

---

# 73. Package Documentation

AXPACKAGE cung cấp:

```text
package identity
version
dependencies
```

AXDOC tạo:

```text
package docs
```

nhưng không quản lý package installation.

---

# 74. Documentation Dependency

Một package docs có thể reference package khác.

AXDOC resolution:

```text
local package
 ↓
dependency package
 ↓
stable symbol ID
```

Nếu dependency docs unavailable:

```text
external reference placeholder
```

không tự fabricate API.

---

# 75. Private Documentation

Internal build có thể tạo:

```text
FULL
```

bao gồm private implementation.

Public release:

```text
PUBLIC
```

chỉ API contract.

---

# 76. Source Code Links

HTML renderer có thể tạo:

```text
function → source
```

với source mapping.

Không cần expose source nếu package distribution không cho phép.

---

# 77. Security

AXDOC phải coi source/docs là untrusted trong package contexts.

Không thực thi:

```text
embedded scripts
code examples
external commands
```

trong documentation generation mặc định.

---

# 78. Markdown Safety

Renderer phải escape:

```text
HTML
scripts
unsafe URLs
```

nếu output profile yêu cầu safe docs.

---

# 79. Example Execution Security

Doctest:

```text
sandbox
resource limits
network deny
filesystem temporary
```

mặc định.

---

# 80. Documentation Generator Plugin

Renderer interface:

```text
DocRenderer {
    open()
    render_bundle()
    render_node()
    render_index()
    close()
}
```

External renderers có thể dùng interface này.

---

# 81. Theme

Theme không thuộc semantic AXDOC.

```text
AXDOC
 ↓
canonical DocBundle
 ↓
theme/renderer
```

Do đó theme thay đổi không làm thay đổi documentation semantics.

---

# 82. IDE Integration

IDE có thể query:

```text
hover(symbol)
signature(symbol)
documentation(symbol)
definition(symbol)
references(symbol)
examples(symbol)
tests(symbol)
```

AXDOC trở thành backend documentation provider.

---

# 83. Compiler Integration

Compiler cung cấp:

```text
SemanticSnapshot
```

AXDOC consume snapshot thay vì re-parse toàn bộ source nếu có thể.

---

# 84. Semantic Snapshot

```text
SemanticSnapshot {
    compiler_version
    language_version
    package
    modules[]
    symbols[]
    types[]
    traits[]
    implementations[]
    diagnostics[]
}
```

---

# 85. Documentation Extraction API

```text
doc_extract_source()
doc_extract_module()
doc_extract_package()
doc_extract_symbol()

doc_build_model()
doc_validate_model()
doc_resolve_references()
doc_build_index()
doc_build_bundle()
```

---

# 86. Reader API

```text
doc_open()
doc_close()

doc_package()
doc_modules()
doc_find()
doc_lookup_symbol()

doc_node()
doc_signature()
doc_examples()
doc_references()
doc_tests()

doc_search()
doc_related()
```

---

# 87. Builder API

```text
doc_builder_create()
doc_builder_add_source()
doc_builder_add_spec()
doc_builder_add_metadata()

doc_builder_resolve()
doc_builder_validate()

doc_builder_render()
doc_builder_write()
doc_builder_finalize()
```

---

# 88. AI API

```text
doc_ai_lookup()
doc_ai_context()
doc_ai_symbol()
doc_ai_related()
doc_ai_examples()
doc_ai_tests()
doc_ai_spec()
```

Output phải machine-readable.

---

# 89. Documentation ABI

`AXDOC_ABI_1`:

```text
DocNode
DocMetadata
DocReference
DocExample
DocTestLink
DocBundleHeader
DocSearchEntry
```

Tất cả ABI structures:

```text
size
version
flags
reserved
```

ở dạng phù hợp để forward compatibility.

---

# 90. Documentation Schema

```text
AXDOC_SCHEMA_1
```

độc lập với:

```text
AXDOC_ABI_1
```

Schema version dành cho serialized docs.

---

# 91. Error Model

Canonical errors:

```text
DOC_NOT_FOUND
DOC_PARSE_ERROR
DOC_INVALID_REFERENCE
DOC_SYMBOL_NOT_FOUND
DOC_DUPLICATE_ID
DOC_INVALID_SIGNATURE
DOC_EXAMPLE_FAILED
DOC_RENDER_FAILED
DOC_SCHEMA_MISMATCH
DOC_CORRUPT_BUNDLE
DOC_UNSUPPORTED_FORMAT
DOC_PERMISSION_DENIED
DOC_RESOURCE_LIMIT
```

---

# 92. Performance

Mục tiêu:

```text
large codebase
→ incremental extraction
→ parallel processing
→ deterministic merge
```

Không load toàn bộ documentation vào RAM nếu không cần.

---

# 93. Parallel Documentation

Pipeline:

```text
module A ─┐
module B ─┼→ extraction
module C ─┤
module D ─┘
             ↓
       deterministic merge
             ↓
         cross-reference
```

---

# 94. Memory Efficiency

Ưu tiên:

```text
string interning
string tables
symbol IDs
immutable buffers
memory mapping
streaming renderer
```

Không duplicate cùng một documentation string nhiều lần.

---

# 95. Search Performance

Index hỗ trợ:

```text
exact symbol
prefix
module
kind
full text
tags
```

Không bắt buộc search engine bên thứ ba.

---

# 96. Documentation Version Diff

Bundle:

```text
v1.axdoc
v2.axdoc
```

có thể diff semantic:

```text
symbol added
symbol removed
signature changed
trait changed
example changed
doc changed
deprecated
```

---

# 97. Documentation Reproducibility

AXTEST có suite:

```text
build docs twice
compare bundles
```

Expected:

```text
identical canonical bundle
```

---

# 98. Documentation Fuzzing

AXTEST fuzz AXDOC:

```text
malformed doc comments
invalid markup
deep nesting
huge tables
invalid references
corrupt .axdoc
invalid UTF-8
```

AXDOC không được crash.

---

# 99. Documentation Round Trip

Test:

```text
source docs
 ↓
Doc IR
 ↓
serialize
 ↓
read
 ↓
Doc IR
```

Expected:

```text
semantic equivalence
```

---

# 100. Renderer Round Trip

Renderer không được thay đổi semantic content.

```text
Doc IR
 ↓
HTML
```

Parser HTML không phải canonical requirement; canonical source remains Doc IR.

---

# 101. Specification Integrity

AXDOC không được âm thầm sửa normative specification.

Nếu generated docs khác spec:

```text
SPEC-DOC-MISMATCH
```

---

# 102. API/Spec Conflict

Nếu:

```text
spec says:
fn foo(i32)

source:
fn foo(i64)
```

AXDOC phải báo conflict.

Không tự chọn một bên.

---

# 103. API/Test Conflict

Nếu documentation example không compile:

```text
DOC_EXAMPLE_FAILED
```

Nếu API signature thay đổi nhưng example chưa sửa:

```text
test failure
```

---

# 104. Documentation Deprecation

AXDOC hiển thị:

```text
Deprecated since X
Use Y instead
```

Compiler có thể cũng phát warning.

AXDOC không tự tạo compiler warning.

---

# 105. Feature Flags

API có thể thuộc:

```text
feature = "network"
feature = "gpu"
feature = "unsafe"
```

AXDOC hiển thị availability.

---

# 106. Target-Specific API

Ví dụ:

```text
@target("windows")
fn windows_console(...)
```

AXDOC:

```text
Available:
Windows only
```

Không đưa API đó vào cross-target documentation như universal API.

---

# 107. Platform Matrix in Docs

AXDOC có thể sinh:

| API | Windows | Linux | macOS | iOS | Android | WASM |
|---|---|---|---|---|---|---|
| API A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| API B | ✓ | — | — | — | — | — |

Thông tin lấy từ compiler/metadata, không suy đoán.

---

# 108. ABI Matrix

Documentation cấp thấp có thể hiển thị:

```text
x86_64 Windows → AXABI-WIN64
x86_64 Linux   → AXABI-SYSV64
AArch64        → AXABI-A64
WASM32         → AXABI-WASM32
```

---

# 109. AI Context Compression

AXDOC có thể tạo context theo ngân sách:

```text
doc_ai_context(symbol, budget)
```

Ưu tiên:

```text
signature
summary
constraints
effects
examples
related APIs
tests
spec
```

Giúp agent không cần đưa toàn bộ repository vào context.

---

# 110. AI Trust Levels

Mỗi documentation fact có provenance:

```text
COMPILER_DERIVED
SOURCE_DOCUMENTED
SPEC_NORMATIVE
TEST_VERIFIED
USER_AUTHORED
EXTERNAL
```

AI consumer biết nguồn của thông tin.

---

# 111. Provenance

```text
DocProvenance {
    source_kind
    source_id
    source_version
    location
    generated_by
}
```

---

# 112. AI Conflict Resolution

Nếu:

```text
prose says A
compiler says B
```

AXDOC đánh dấu:

```text
DOCUMENTATION_CONFLICT
```

AI metadata ưu tiên structured semantic data nhưng phải giữ conflict information.

---

# 113. Documentation as Build Artifact

AXDOC output:

```text
.axdoc
.axdoc-index
```

có thể được cache và package.

---

# 114. Documentation as Package Artifact

Package:

```text
library.axpkg
```

có thể chứa:

```text
binary
headers/FFI metadata
.axdoc
debug metadata
```

AXPACKAGE quyết định distribution.

AXDOC chỉ tạo documentation artifact.

---

# 115. No Mandatory Runtime

AXDOC không kéo runtime vào application.

```text
application binary
```

không cần:

```text
AXDOC runtime
```

---

# 116. No Third-Party Documentation Dependency

Core AXDOC phải có thể:

```text
parse
extract
index
render
```

không cần external documentation generator.

External tools chỉ là optional adapters.

---

# 117. Test Integration

AXTEST suite tối thiểu:

```text
doc parser
doc extraction
symbol resolution
generic docs
trait docs
cross-reference
doctest
golden docs
AI metadata
bundle serialization
reproducibility
fuzzing
incremental build
API diff
```

---

# 118. AXDOC Invariants

### DOC-INV-01
Every public documented symbol resolves to a valid semantic symbol.

### DOC-INV-02
Documentation cannot alter program semantics.

### DOC-INV-03
Every stable documentation ID is unique within its namespace.

### DOC-INV-04
Symbol references resolve through semantic identity.

### DOC-INV-05
Broken internal references are detectable.

### DOC-INV-06
Documentation signatures are derived from compiler semantics.

### DOC-INV-07
AXDOC does not invent missing APIs.

### DOC-INV-08
Generic constraints in documentation match compiler constraints.

### DOC-INV-09
Documented parameter names must match the declaration when parameter documentation is structured.

### DOC-INV-10
Documented return types cannot contradict the semantic model.

### DOC-INV-11
Documented error types must resolve to valid types.

### DOC-INV-12
Visibility filtering cannot expose symbols outside the selected documentation profile.

### DOC-INV-13
Private symbols are excluded from PUBLIC documentation unless explicitly exported.

### DOC-INV-14
Documentation examples marked runnable are testable by AXTEST.

### DOC-INV-15
A failed required doctest causes documentation validation failure.

### DOC-INV-16
Golden documentation is never silently rewritten.

### DOC-INV-17
Canonical documentation output is deterministic.

### DOC-INV-18
Non-deterministic metadata must be explicitly excluded or normalized.

### DOC-INV-19
Documentation bundles contain schema/version information.

### DOC-INV-20
Corrupt documentation bundles are rejected safely.

### DOC-INV-21
AXDOC readers never execute documentation content by default.

### DOC-INV-22
External links cannot execute local commands.

### DOC-INV-23
Documentation generation does not implicitly access the network.

### DOC-INV-24
Documentation examples execute under declared AXTEST isolation.

### DOC-INV-25
Documentation provenance is preserved for generated semantic facts.

### DOC-INV-26
Normative specification content is distinguishable from explanatory prose.

### DOC-INV-27
Specification/documentation conflicts are detectable.

### DOC-INV-28
API documentation can reference associated tests.

### DOC-INV-29
ABI documentation derives ABI facts from AXABI metadata.

### DOC-INV-30
Target-specific availability is explicitly represented.

### DOC-INV-31
Documentation cache keys include all semantic inputs.

### DOC-INV-32
Semantic changes invalidate affected documentation.

### DOC-INV-33
Unchanged documentation can be reused incrementally.

### DOC-INV-34
Parallel documentation generation produces deterministic output.

### DOC-INV-35
Search index entries resolve to valid documentation nodes.

### DOC-INV-36
AI-readable metadata does not contain fabricated symbols or signatures.

### DOC-INV-37
AI context can expose provenance of semantic facts.

### DOC-INV-38
AXDOC does not become a mandatory runtime dependency.

### DOC-INV-39
AXDOC can be bootstrapped without requiring the final documentation stack.

### DOC-INV-40
AXDOC itself is validated by AXTEST through unit, integration, fuzz, golden, and reproducibility tests.

---

# 119. Implementation Phases

## Phase 1 — Semantic extraction

```text
compiler semantic snapshot
→ DocNode
```

## Phase 2 — Documentation parser

```text
/// comments
→ Doc AST
```

## Phase 3 — Resolver

```text
references
→ SymbolId
```

## Phase 4 — Validation

```text
signature
examples
references
```

## Phase 5 — Bundle

```text
.axdoc
```

## Phase 6 — Renderer

```text
HTML
Markdown
JSON
```

## Phase 7 — Search/AI

```text
index
AI context
```

## Phase 8 — Integration

```text
AXTEST
AXBUILD
AXPACKAGE
IDE
```

---

# 120. Core API

```text
doc_open()
doc_close()

doc_extract_source()
doc_extract_module()
doc_extract_package()
doc_extract_symbol()

doc_builder_create()
doc_builder_destroy()

doc_add_comment()
doc_add_spec()
doc_add_metadata()

doc_resolve_reference()
doc_resolve_all()

doc_validate()
doc_validate_symbol()
doc_validate_examples()

doc_build_index()
doc_search()

doc_build_bundle()
doc_write_bundle()
doc_read_bundle()

doc_render_html()
doc_render_markdown()
doc_render_json()

doc_diff()

doc_ai_lookup()
doc_ai_context()
doc_ai_related()

doc_source_location()
doc_provenance()
```

---

# 121. Definition of Done

`AXDOC 5.0` hoàn thành khi:

### Semantic

- [x] source extraction
- [x] compiler semantic integration
- [x] symbol identity
- [x] type/generic/trait metadata
- [x] visibility
- [x] ABI metadata
- [x] target metadata

### Documentation

- [x] doc comments
- [x] structured docs
- [x] specification docs
- [x] examples
- [x] cross references
- [x] API references
- [x] deprecation
- [x] provenance

### Build

- [x] incremental generation
- [x] deterministic output
- [x] caching
- [x] parallel generation
- [x] canonical `.axdoc`

### Verification

- [x] validation
- [x] doctest
- [x] golden tests
- [x] fuzzing
- [x] reproducibility
- [x] API diff
- [x] AXTEST integration

### AI

- [x] semantic index
- [x] AI context packs
- [x] provenance
- [x] symbol lookup
- [x] test/spec/implementation cross-links
- [x] no fabricated API metadata

### Platform

- [x] offline documentation
- [x] target-aware API
- [x] ABI-aware documentation
- [x] static HTML
- [x] Markdown
- [x] JSON

### ABI

- [x] `AXDOC_ABI_1`
- [x] `AXDOC_SCHEMA_1`
- [x] stable reader/builder contract

**AXDOC 5.0 = FROZEN.**

---

# 122. Kiến trúc sau AXDOC

Axiom lúc này có thêm một semantic information plane:

```text
                         AXDOC
                           │
              ┌────────────┼────────────┐
              │            │            │
             IDE          AI         HUMAN
              │            │            │
              └────────────┼────────────┘
                           │
                      semantic graph
                           │
     ┌─────────────────────┼─────────────────────┐
     │                     │                     │
 AXCOMPILER              AXTEST              AXBUILD
     │                     │                     │
     └─────────────────────┼─────────────────────┘
                           │
                       AXPACKAGE
```

Điểm đáng chú ý là **AXDOC không chỉ là documentation generator**. Nó trở thành lớp semantic index có thể liên kết:

```text
Specification
     ↕
API
     ↕
Source
     ↕
ABI
     ↕
Implementation
     ↕
Test
     ↕
Binary
```

Đây là nền tảng rất hữu ích cho mục tiêu **AI-friendly language/toolchain** của Axiom mà không đưa AI vào compiler core.

---

# 123. Task tiếp theo

## BOOTSTRAP-784 — AXIDE

**Native Axiom Development Environment, Language Server, Semantic Editor Services, Incremental Parsing, Diagnostics, Symbol Navigation, Refactoring, Debug Integration, Build/Test Integration, AI Context Integration & IDE Protocol Runtime 5.0**

Sau `AXDOC`, subsystem tự nhiên tiếp theo là **AXIDE**: sử dụng semantic graph của `AXCOMPILER` + `AXDOC` + `AXTEST` + `AXBUILD` để tạo môi trường phát triển native cho Axiom, thay vì phụ thuộc vào một IDE bên thứ ba.