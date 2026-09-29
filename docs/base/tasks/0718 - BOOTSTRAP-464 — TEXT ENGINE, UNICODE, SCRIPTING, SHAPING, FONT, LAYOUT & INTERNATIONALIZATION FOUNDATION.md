# BOOTSTRAP-464 — TEXT ENGINE, UNICODE, SCRIPTING, SHAPING, FONT, LAYOUT & INTERNATIONALIZATION FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

464 định nghĩa text foundation cho Axiom, phục vụ trực tiếp cho **452 GUI, 460 Graphics, 462 Media, 463 Image**, đồng thời giữ đúng nguyên tắc: **UTF-8 là representation mặc định nhưng UTF-8 byte không phải là Unicode character**.

Kiến trúc:

```text
Axiom Core
    ↓
UTF-8
    ↓
Unicode
    ├── Scalar Value
    ├── Code Point
    ├── Grapheme Cluster
    ├── Normalization
    ├── Segmentation
    ├── Bidi
    ├── Script
    └── Properties
          ↓
       TEXT ENGINE
          ├── Font
          ├── Glyph
          ├── Shaping
          ├── Layout
          ├── Line Breaking
          ├── Measurement
          └── Rasterization
                ↓
             460 Graphics / 463 Image
```

---

## 464.1 — Text representation

Axiom giữ ba tầng chính:

```text
String
    = UTF-8 owned text

StringView
    = UTF-8 borrowed view

ByteString / ByteView
    = arbitrary bytes
```

Không được coi arbitrary bytes là text.

---

## 464.2 — UTF-8 invariant

`String` luôn chứa UTF-8 hợp lệ.

Byte sequence không hợp lệ không thể trở thành `String` thông qua safe API.

---

## 464.3 — Unicode scalar value

Text engine phân biệt:

```text
UTF-8 byte
Unicode code point
Unicode scalar value
grapheme cluster
glyph
```

---

## 464.4 — Code point

Code point là giá trị Unicode `U+0000..U+10FFFF`.

---

## 464.5 — Scalar value

Scalar value loại bỏ surrogate code points.

---

## 464.6 — UTF-8 decoding

Decoder phải reject:

```text
overlong encoding
invalid continuation
surrogate encoding
out-of-range code point
truncated sequence
```

---

## 464.7 — Lossy decoding

API riêng:

```text
decode_utf8_lossy(...)
```

không được nhầm với strict decoding.

---

## 464.8 — Character terminology

Axiom không dùng từ "character" trong low-level APIs nếu có thể gây mơ hồ.

API nên dùng:

```text
byte
code_point
scalar
grapheme
glyph
```

---

## 464.9 — Grapheme cluster

Một grapheme cluster có thể chứa nhiều Unicode scalar values.

Ví dụ một ký tự người dùng nhìn thấy có thể gồm:

```text
base + combining marks
```

---

## 464.10 — User-perceived character

API text-editing nên thao tác theo grapheme cluster thay vì byte.

---

## 464.11 — Grapheme iterator

```text
text.graphemes()
```

trả các cluster boundaries.

---

## 464.12 — Code-point iterator

```text
text.codepoints()
```

---

## 464.13 — Byte iterator

```text
text.bytes()
```

---

## 464.14 — Complexity

UTF-8 indexing theo byte có thể O(1).

Index theo grapheme không được hứa O(1) trừ khi có index/cache.

---

## 464.15 — Text index

Text engine có thể dùng:

```text
ByteOffset
ScalarOffset
GraphemeOffset
```

nhưng không được tráo đổi.

---

## 464.16 — Range

Range phải ghi rõ đơn vị:

```text
ByteRange
ScalarRange
GraphemeRange
```

---

## 464.17 — Unicode properties

Unicode database cung cấp:

```text
GeneralCategory
Script
ScriptExtensions
CombiningClass
EastAsianWidth
LineBreakClass
BidiClass
```

---

## 464.18 — Unicode version

Text engine phải ghi Unicode version.

---

## 464.19 — Unicode database determinism

Build phải cố định Unicode database version nếu cần reproducibility.

---

## 464.20 — Normalization

Hỗ trợ:

```text
NFC
NFD
NFKC
NFKD
```

---

## 464.21 — Normalization không mặc định

Axiom không tự normalize mọi `String`.

---

## 464.22 — Identifier normalization

Compiler identifier comparison theo policy đã định nghĩa ở 429; text runtime không được tự áp dụng compiler identifier rules.

---

## 464.23 — Case conversion

Hỗ trợ Unicode-aware:

```text
lowercase
uppercase
case folding
```

---

## 464.24 — Case folding

Case folding phục vụ comparison/search, không phải presentation.

---

## 464.25 — Locale-independent case

Có API Unicode-default không phụ thuộc locale.

---

## 464.26 — Locale-sensitive case

Các trường hợp đặc biệt có locale-aware API.

---

## 464.27 — Unicode segmentation

Hỗ trợ:

```text
grapheme segmentation
word segmentation
sentence segmentation
line segmentation
```

---

## 464.28 — Word boundaries

Word boundary không được định nghĩa đơn giản bằng whitespace.

---

## 464.29 — Sentence boundaries

Sentence segmentation sử dụng Unicode rules và có thể có language-specific extensions.

---

## 464.30 — Line breaking

Line breaking phải tách khỏi word segmentation.

---

# 464.31 — Bidirectional text

Hỗ trợ Unicode Bidirectional Algorithm.

---

## 464.32 — Bidi paragraph

Text layout xác định paragraph direction:

```text
LTR
RTL
Auto
```

---

## 464.33 — Bidi isolation

Inline embedded direction phải được xử lý theo Unicode bidi rules.

---

## 464.34 — Mixed-direction text

Ví dụ:

```text
English + Arabic + numbers
```

phải layout đúng mà không yêu cầu caller tự đảo chuỗi.

---

## 464.35 — Logical order

String luôn lưu logical order.

---

## 464.36 — Visual order

Visual ordering chỉ tồn tại ở layout/render stage.

---

## 464.37 — Cursor movement

Cursor movement phải dựa trên grapheme/bidi layout, không đơn giản tăng byte offset.

---

## 464.38 — Selection

Selection có thể biểu diễn theo logical text range và layout geometry.

---

## 464.39 — Hit testing

Text layout hỗ trợ:

```text
x,y → text position
```

---

## 464.40 — Caret geometry

Có thể trả:

```text
caret rectangle
leading/trailing edge
bidi direction
```

---

# 464.41 — Script detection

Text engine xác định script runs:

```text
Latin
Cyrillic
Greek
Arabic
Hebrew
Devanagari
Han
Hangul
Thai
...
```

---

## 464.42 — Script extensions

Một scalar có thể thuộc nhiều script contexts.

---

## 464.43 — Language metadata

Text run có thể mang language tag.

---

## 464.44 — Language ≠ script

Ví dụ cùng một script có thể được dùng bởi nhiều ngôn ngữ.

---

## 464.45 — Font selection

Font selection sử dụng:

```text
language
script
style
weight
stretch
coverage
fallback
```

---

## 464.46 — Font family

Font family là logical family, không nhất thiết là một file duy nhất.

---

## 464.47 — Font fallback

Nếu font chính thiếu glyph, engine tìm fallback.

---

## 464.48 — Fallback chain

Fallback chain phải deterministic khi cùng configuration.

---

## 464.49 — Missing glyph

Missing glyph không được làm crash renderer.

Có thể render replacement glyph.

---

## 464.50 — Font resource

```text
FontFace
FontFamily
FontInstance
```

là các abstraction khác nhau.

---

# 464.51 — Font loading

Font có thể đến từ:

```text
file
memory
embedded resource
system font provider
network/application provider
```

Network loading không thuộc text core.

---

## 464.52 — Font ownership

Font resource tuân thủ 423.

---

## 464.53 — Font cache

Font face/instance có thể được cache.

---

## 464.54 — Font cache key

Bao gồm:

```text
font identity
variation
size
render mode
```

---

## 464.55 — Font format

Engine có thể hỗ trợ OpenType/TrueType thông qua provider.

---

## 464.56 — Font parser security

Font files là untrusted input.

---

## 464.57 — Font parser limits

Phải có giới hạn:

```text
tables
glyph count
variation axes
memory
recursion
```

---

## 464.58 — Font sandbox

Font parsing/rendering từ nguồn không tin cậy có thể isolation.

---

## 464.59 — Font licensing

License metadata không thuộc compiler semantics.

---

## 464.60 — Font embedding

Application có thể embed font resources.

---

# 464.61 — Glyph

Glyph là graphical representation được font cung cấp.

Glyph không đồng nhất với Unicode scalar.

---

## 464.62 — Glyph ID

Font-local glyph ID.

---

## 464.63 — Glyph advance

Glyph có advance width/height.

---

## 464.64 — Glyph offsets

Shaping có thể tạo offset riêng cho từng glyph.

---

## 464.65 — Glyph cluster mapping

Mỗi glyph output có thể map về source text range.

---

## 464.66 — Ligature

Một glyph có thể đại diện cho nhiều scalar.

---

## 464.67 — Combining marks

Multiple glyphs có thể overlap/attach.

---

## 464.68 — Zero-advance glyph

Một số glyph có advance bằng zero.

---

## 464.69 — Vertical metrics

Font có vertical metrics riêng.

---

## 464.70 — Baseline

Layout phải xác định baseline.

---

# 464.71 — Text shaping

Shaping chuyển:

```text
Unicode text
 ↓
script/language runs
 ↓
font
 ↓
OpenType shaping
 ↓
glyph sequence
```

---

## 464.72 — Shaping output

```text
ShapedRun {
    glyphs[]
    positions[]
    clusters[]
}
```

---

## 464.73 — Shaping context

Shaping có thể phụ thuộc vào glyph/text lân cận.

---

## 464.74 — OpenType features

Có thể chỉ định:

```text
liga
kern
calt
locl
frac
tnum
...
```

---

## 464.75 — Feature control

Application có thể bật/tắt feature.

---

## 464.76 — Kerning

Kerning là shaping/layout behavior, không phải đơn giản cộng hai glyph widths.

---

## 464.77 — Script-specific shaping

Các script như Arabic/Indic yêu cầu shaping rules phức tạp.

---

## 464.78 — Vietnamese

Vietnamese text phải xử lý combining marks đúng.

Không được giả định mỗi ký tự hiển thị = một glyph.

---

## 464.79 — Emoji

Emoji sequences có thể chứa nhiều scalar.

---

## 464.80 — Emoji ZWJ

Zero Width Joiner sequences được xử lý như text sequences, không phải từng glyph độc lập.

---

# 464.81 — Variation selectors

Variation selectors phải được giữ trong shaping pipeline.

---

## 464.82 — Regional indicators

Flag emoji sequences cần Unicode-aware segmentation/shaping.

---

## 464.83 — Skin-tone modifiers

Modifier sequences được xử lý theo Unicode rules.

---

## 464.84 — Font color glyphs

Font có thể cung cấp color glyphs.

---

## 464.85 — Color glyph rendering

Renderer phải hỗ trợ hoặc fallback phù hợp.

---

## 464.86 — Font variations

OpenType variable fonts:

```text
weight
width
slant
custom axes
```

---

## 464.87 — Variation instance

`FontInstance` chứa axis values.

---

## 464.88 — Optical size

Nếu font hỗ trợ, optical size là một variation axis.

---

## 464.89 — Font size

Font size không nhất thiết bằng pixel height.

---

## 464.90 — Device scale

Layout units và physical pixels phải được phân biệt.

---

# 464.91 — Text layout

Layout input:

```text
Text
Font
Style
Width
Direction
Language
Features
```

---

## 464.92 — Layout output

```text
TextLayout {
    lines[]
    runs[]
    glyphs[]
    bounds
}
```

---

## 464.93 — Paragraph

Paragraph là đơn vị layout tự nhiên.

---

## 464.94 — Line

Line có:

```text
start
end
baseline
ascent
descent
leading
width
```

---

## 464.95 — Inline runs

Một paragraph có nhiều font/style/script runs.

---

## 464.96 — Line breaking

Line breaker phải xét Unicode line-break rules.

---

## 464.97 — Hyphenation

Hyphenation là language-specific optional subsystem.

---

## 464.98 — Justification

Text layout có thể hỗ trợ:

```text
left
right
center
justify
```

---

## 464.99 — Letter spacing

Explicit layout property.

---

## 464.100 — Word spacing

Explicit layout property.

---

# 464.101 — Text measurement

API:

```text
measure(text, style)
```

trả logical metrics.

---

## 464.102 — Bounding box

Phân biệt:

```text
advance bounds
ink bounds
line bounds
```

---

## 464.103 — Baseline metrics

Expose:

```text
ascent
descent
line_gap
```

---

## 464.104 — Font metrics

Font metrics không được suy ra đơn giản từ glyph bitmap.

---

## 464.105 — Text wrapping

Wrapping là layout operation.

---

## 464.106 — Ellipsis

Ellipsis là policy:

```text
clip
ellipsis
fade
```

---

## 464.107 — Truncation

Truncation phải giữ text semantics riêng với rendered representation.

---

## 464.108 — Selection geometry

Layout cung cấp rectangles/ranges cho selection.

---

## 464.109 — Hit testing

Hit test có thể trả:

```text
TextPosition
Affinity
```

---

## 464.110 — Caret affinity

Quan trọng với bidi và line boundaries.

---

# 464.111 — Text rendering

Rendering pipeline:

```text
Text
 ↓
Unicode segmentation
 ↓
Bidi
 ↓
Font selection
 ↓
Shaping
 ↓
Layout
 ↓
Glyph rasterization
 ↓
460 Graphics / 463 Image
```

---

## 464.112 — Glyph rasterization

Có thể tạo:

```text
bitmap
alpha mask
grayscale mask
SDF
MSDF
GPU glyph resource
```

---

## 464.113 — Antialiasing

Các mode:

```text
None
Grayscale
Subpixel
```

Subpixel rendering là platform-dependent.

---

## 464.114 — Hinting

Font hinting có thể bật/tắt.

---

## 464.115 — Rasterization determinism

Font rasterization có thể device-dependent.

---

## 464.116 — Vector glyph

Glyph outlines có thể giữ vector representation.

---

## 464.117 — GPU glyph rendering

GPU có thể render glyph paths hoặc sample glyph atlas.

---

## 464.118 — Glyph atlas

Atlas caching là optimization.

---

## 464.119 — Atlas invalidation

Thay đổi font/size/render mode/device phải invalidate entry thích hợp.

---

## 464.120 — Atlas ownership

Atlas resource ownership explicit.

---

# 464.121 — Text on GPU

Text engine có thể output:

```text
GpuGlyphRun
```

để 460 render.

---

## 464.122 — CPU fallback

CPU rasterizer luôn là fallback architecture.

---

## 464.123 — SDF

Signed Distance Field là optional representation.

---

## 464.124 — MSDF

Multi-channel SDF là optional advanced technique.

---

## 464.125 — Large text

Large glyphs có thể chuyển sang vector/path rendering thay vì atlas.

---

# 464.126 — Internationalization

I18N modules:

```text
locale
number formatting
date/time formatting
plural rules
collation
message formatting
```

---

## 464.127 — Locale

Locale gồm language/region/script/extensions.

---

## 464.128 — BCP-style language tags

Language tags được lưu canonicalized theo tiêu chuẩn phù hợp.

---

## 464.129 — Locale ≠ language

Locale có thể ảnh hưởng formatting nhưng không thay đổi language semantics.

---

## 464.130 — Number formatting

Locale-aware:

```text
decimal separator
group separator
digits
sign
currency
```

---

## 464.131 — Parsing

Formatting và parsing là hai chiều riêng.

---

## 464.132 — Currency

Currency formatting không nên dùng floating-point binary trực tiếp cho accounting.

---

## 464.133 — Decimal

Có thể dùng decimal types từ 458/library.

---

## 464.134 — Date formatting

Uses time/date subsystem from 441.

---

## 464.135 — Calendar

Gregorian và additional calendars là library features.

---

## 464.136 — Plural rules

Plural selection phải dựa trên locale rules.

---

## 464.137 — Message formatting

Structured message formatting thay vì string concatenation.

---

## 464.138 — Translation catalogs

Catalog API:

```text
message_id
locale
translated_message
```

---

## 464.139 — Fallback locale

Explicit fallback chain.

---

## 464.140 — Missing translation

Policy có thể:

```text
fallback
message_id
error
```

---

# 464.141 — Collation

Unicode string ordering không đồng nghĩa byte ordering.

---

## 464.142 — Binary comparison

Nếu muốn byte ordering, dùng byte/string binary comparison explicit.

---

## 464.143 — Unicode collation

Locale-aware collation là separate API.

---

## 464.144 — Search

Case/diacritic-insensitive search phải explicit.

---

## 464.145 — Normalized search

Search pipeline có thể:

```text
normalize
case-fold
segment
compare
```

---

# 464.146 — Text editing buffer

Editor-oriented buffer:

```text
TextBuffer
```

có thể sử dụng piece table/rope/gap buffer.

---

## 464.147 — TextBuffer ≠ String

`String` tối ưu ownership/contiguous representation.

`TextBuffer` tối ưu editing.

---

## 464.148 — Rope

Rope là library implementation option.

---

## 464.149 — Piece table

Editor có thể dùng piece table.

---

## 464.150 — Stable positions

Text editor cần position tracking qua edits.

---

## 464.151 — Position invalidation

Raw offsets có thể trở nên invalid sau mutation.

---

## 464.152 — Anchors

Optional stable text anchors.

---

## 464.153 — Undo/redo

Undo system nằm ở editor library, không phải core text semantics.

---

## 464.154 — Clipboard

Clipboard thuộc GUI/platform layer 452.

---

## 464.155 — IME

Input Method Editor thuộc platform/text-input layer.

---

# 464.156 — Font discovery

System font discovery là platform service.

---

## 464.157 — Font matching

Matching algorithm phải deterministic given same font database/configuration.

---

## 464.158 — Font database

Font DB có thể index:

```text family
style
weight
stretch
coverage
language
```

---

## 464.159 — Font fallback cache

Fallback result có thể cache.

---

## 464.160 — Font invalidation

Installing/removing fonts invalidates affected cache entries.

---

# 464.161 — Security

Text security includes:

```text invalid UTF-8
bidi spoofing
confusables
oversized text
font attacks
pathological shaping
resource exhaustion
```

---

## 464.162 — Confusables

Unicode confusable detection là security utility, không tự động block text.

---

## 464.163 — Bidi warnings

Tools có thể cảnh báo suspicious bidi controls.

---

## 464.164 — Invisible characters

Tools có thể hiển thị/inspect invisible Unicode characters.

---

## 464.165 — Normalization security

Security-sensitive identifiers có thể yêu cầu normalization/canonical comparison theo explicit policy.

---

## 464.166 — Homoglyphs

Engine không được tự coi các visually similar characters là cùng character.

---

## 464.167 — Resource limits

Text operations có thể nhận:

```text max_bytes
max_graphemes
max_runs
max_glyphs
max_layout_width
```

---

## 464.168 — Shaping denial-of-service

Complex shaping operations phải có resource budget.

---

## 464.169 — Font memory limits

Font provider phải hỗ trợ memory/resource budgets.

---

## 464.170 — Untrusted documents

Text document parser không được có quyền filesystem/network mặc định.

---

# 464.171 — Performance

Hot paths:

```text UTF-8 decode
segmentation
shaping
layout
glyph cache
rasterization
```

---

## 464.172 — SIMD

UTF-8 validation/search có thể vectorize bằng 458.

---

## 464.173 — Parallel layout

Independent paragraphs có thể layout song song.

---

## 464.174 — Parallel rasterization

Independent glyphs có thể rasterize song song.

---

## 464.175 — Cache

Cache:

```text Unicode properties
font faces
font instances
shaping
glyphs
layouts
```

---

## 464.176 — Cache key

Cache key phải bao gồm mọi semantic input ảnh hưởng kết quả.

---

## 464.177 — No hidden global mutable state

Text engine không phụ thuộc implicit global font/layout state.

---

## 464.178 — Thread safety

Read-only font resources có thể `Share` nếu implementation cho phép.

---

## 464.179 — Mutable caches

Caches dùng synchronization từ 424.

---

## 464.180 — Allocation

Hot text paths có thể sử dụng caller-provided arenas/buffers.

---

# 464.181 — AI metadata

446 phải expose:

```text source text range
grapheme boundaries
script runs
bidi runs
font selection
fallback reason
shaping features
glyph mapping
line breaks
layout bounds
```

---

## 464.182 — Explain font fallback

AI/tooling có thể trả lời:

```text
font X thiếu glyph
→ fallback font Y
```

---

## 464.183 — Explain shaping

Có thể inspect:

```text source range
glyph IDs
OpenType features
positions
```

---

## 464.184 — Explain layout

Có thể inspect lý do line break.

---

## 464.185 — Explain Unicode

Tooling có thể hiển thị:

```text byte
code point
scalar
grapheme
script
category
```

---

## 464.186 — Editor integration

LSP/IDE có thể dùng cùng semantic/text services.

---

## 464.187 — Source mapping

Text positions trong diagnostics phải giữ distinction giữa byte offsets và user-visible columns.

---

## 464.188 — Column semantics

Compiler diagnostic column phải có defined encoding unit.

---

## 464.189 — Unicode diagnostics

Compiler có thể hiển thị source snippets chính xác dù source chứa Unicode.

---

## 464.190 — AI-safe text query

AI tooling có thể query text spans mà không cần load toàn bộ file.

---

# 464.191 — Testing

Test:

```text UTF-8
normalization
grapheme
word boundary
sentence boundary
bidi
script
font fallback
shaping
ligature
kerning
emoji
line breaking
layout
hit testing
rasterization
I18N
collation
```

---

## 464.192 — Unicode conformance

Unicode conformance tests phải được versioned theo Unicode version.

---

## 464.193 — Bidi conformance

Use official-style bidi test vectors.

---

## 464.194 — Grapheme tests

Include combining marks/emoji/ZWJ sequences.

---

## 464.195 — Vietnamese tests

Phải có test cho:

```text
Vietnamese precomposed
Vietnamese combining sequences
mixed Vietnamese + English
```

---

## 464.196 — RTL tests

Arabic/Hebrew + Latin + numbers.

---

## 464.197 — CJK tests

Chinese/Japanese/Korean font fallback and line breaking.

---

## 464.198 — Emoji tests

Variation selectors, modifiers, ZWJ sequences.

---

## 464.199 — Font tests

Different font metrics/features/variable axes.

---

## 464.200 — Layout golden tests

Text layout outputs có thể được snapshot.

---

# 464.201 — Rendering tests

Glyph rasterization có:

```text exact tests
tolerance tests
platform-specific tests
```

---

## 464.202 — Platform rendering

Platform-specific rasterization differences phải được đánh dấu thay vì coi mọi pixel mismatch là compiler failure.

---

## 464.203 — Fuzzing

Fuzz:

```text UTF-8
Unicode segmentation
font parser
shaper
layout
text formatter
```

---

## 464.204 — Malformed font fuzzing

Bắt buộc đối với bundled font parser.

---

## 464.205 — Large text tests

Test resource exhaustion với text cực lớn.

---

## 464.206 — Performance benchmarks

Measure:

```text MB/s UTF-8
graphemes/s
glyphs/s
shaping latency
layout throughput
rasterization throughput
font-load latency
cache hit rate
```

---

## 464.207 — Benchmark isolation

Shaping benchmark không được trộn với disk/network latency.

---

## 464.208 — Memory benchmark

Track allocations/peak memory/font cache size.

---

## 464.209 — GPU benchmark

Track glyph upload/render/atlas behavior.

---

## 464.210 — No aggregate score

Không có "text engine score" tổng hợp.

---

# 464.211 — Implementation order

### Phase 1

```text
UTF-8
Unicode scalar
code point
grapheme
Unicode properties
```

### Phase 2

```text
normalization
segmentation
bidi
script
language tags
```

### Phase 3

```text
Font
FontFace
FontInstance
FontDatabase
fallback
```

### Phase 4

```text
Shaping
GlyphRun
OpenType features
kerning
ligatures
```

### Phase 5

```text
TextLayout
line breaking
measurement
hit testing
selection
```

### Phase 6

```text
Glyph rasterization
glyph atlas
GPU text
SDF/MSDF
```

### Phase 7

```text
locale
number/date formatting
plural
message formatting
collation
```

### Phase 8

```text
editor TextBuffer
advanced font
advanced internationalization
accessibility integration
```

---

# 464.212 — Compiler interaction

Compiler chỉ cần:

```text
UTF-8 source
Unicode identifiers
source positions
diagnostics
formatter
LSP
```

Không đưa font/shaping/layout vào compiler core.

---

# 464.213 — String semantics

Compiler/runtime `String` tiếp tục chỉ bảo đảm:

```text
valid UTF-8
ownership
length
capacity
```

Text engine mới hiểu:

```text grapheme
script
bidi
glyph
font
layout
```

---

# 464.214 — GUI integration

452 sử dụng 464 cho:

```text buttons
menus
text fields
labels
accessibility text
IME
cursor
selection
```

---

# 464.215 — Graphics integration

460 nhận:

```text glyph paths
glyph masks
GPU glyph resources
text geometry
```

---

# 464.216 — Image integration

463 có thể nhận glyph raster/mask để compositing.

---

# 464.217 — Media integration

462 subtitle renderer dùng 464 để:

```text shaping
bidi
font
layout
rasterization
```

---

# 464.218 — No GUI dependency

Text engine có thể chạy headless.

---

# 464.219 — No GPU dependency

Text engine có CPU raster fallback.

---

# 464.220 — No font system dependency

Embedded font provider có thể được dùng trong freestanding/WASM environment.

---

# 464.221 — Hard invariants

1. UTF-8 is the default Axiom text representation.
2. Arbitrary bytes are not text.
3. Invalid UTF-8 cannot enter safe `String`.
4. Byte, code point, scalar, grapheme and glyph are distinct.
5. UTF-8 indexing is distinct from grapheme indexing.
6. Text ranges specify their coordinate unit.
7. Unicode version is explicit.
8. Unicode properties are versioned.
9. Normalization is explicit.
10. NFC/NFD/NFKC/NFKD remain distinct.
11. Text is not automatically normalized.
12. Case conversion is distinct from case folding.
13. Locale-independent and locale-sensitive operations are distinct.
14. Grapheme segmentation follows Unicode rules.
15. Word segmentation is not whitespace splitting.
16. Sentence segmentation is separate.
17. Line breaking is separate.
18. Logical text order is preserved.
19. Visual bidi order is layout-level.
20. Mixed LTR/RTL text is supported.
21. Cursor movement is grapheme/layout-aware.
22. Script detection is separate from language detection.
23. A scalar can participate in multiple script contexts.
24. Font selection considers script/language/style/coverage.
25. Font fallback is explicit and inspectable.
26. Missing glyphs do not crash rendering.
27. Font face and font instance are distinct.
28. Font size is distinct from pixel dimensions.
29. Glyph is distinct from Unicode character.
30. One glyph may represent multiple source scalars.
31. Multiple glyphs may represent one grapheme.
32. Ligatures are supported.
33. Combining marks are supported.
34. Emoji sequences are supported.
35. ZWJ sequences are supported.
36. Variation selectors are preserved.
37. Variable fonts are supported.
38. OpenType shaping is a distinct stage.
39. Shaping output preserves source cluster mapping.
40. Kerning is shaping/layout data.
41. Script-specific shaping is supported.
42. Vietnamese combining sequences are supported.
43. Text layout supports multiple runs.
44. Paragraph and line are distinct concepts.
45. Baseline metrics are explicit.
46. Advance and ink bounds are distinct.
47. Line breaking is Unicode-aware.
48. Hyphenation is optional/language-specific.
49. Justification is layout policy.
50. Hit testing is supported.
51. Caret affinity is represented.
52. Selection geometry is available.
53. CPU text rasterization exists as fallback architecture.
54. GPU text rendering is optional.
55. Glyph atlases are optimization, not semantics.
56. Atlas cache invalidation is deterministic.
57. SDF/MSDF are optional.
58. Color glyphs are supported where provider permits.
59. Rasterization can be device-dependent.
60. Device-dependent output is identifiable.
61. Locale is distinct from language.
62. Locale-aware number formatting is supported.
63. Date/time formatting integrates with 441.
64. Decimal formatting can integrate with 458.
65. Plural rules are locale-aware.
66. Message formatting is structured.
67. Translation catalogs are explicit.
68. Collation is distinct from byte ordering.
69. Case-insensitive search is explicit.
70. Confusable detection does not redefine character identity.
71. Bidi security diagnostics are available.
72. Invisible Unicode inspection is available.
73. Font files are untrusted input.
74. Font parsing has resource limits.
75. Shaping has resource limits.
76. Text processing supports cancellation where needed.
77. Text processing follows 423 ownership.
78. Text caches follow 424 synchronization.
79. Text engine does not require GC.
80. Text engine does not require a borrow checker.
81. Text engine does not require GUI.
82. Text engine does not require GPU.
83. Text engine can operate headlessly.
84. UTF-8 operations can exploit SIMD.
85. Independent paragraphs/runs can execute in parallel.
86. Deterministic mode defines relevant ordering.
87. Cache keys include semantic inputs.
88. TextBuffer is distinct from String.
89. Editor undo/redo is not core text semantics.
90. IME is platform integration.
91. Clipboard is GUI/platform integration.
92. Text diagnostics distinguish byte and user-visible positions.
93. AI can query Unicode structure.
94. AI can query font fallback reasons.
95. AI can query shaping results.
96. AI can query layout decisions.
97. AI can query glyph provenance.
98. Text metadata integrates with 446.
99. Text rendering integrates with 460.
100. Text rasterization integrates with 463.
101. Subtitle rendering integrates with 462.
102. GUI text integrates with 452.
103. Text source storage remains UTF-8.
104. External encodings must be explicitly decoded.
105. No hidden encoding conversion.
106. No hidden font loading from network.
107. No hidden background threads.
108. No mandatory text runtime.
109. Unused font/shaping subsystems are not linked.
110. Unused GUI/GPU infrastructure is not linked.
111. External font providers remain optional.
112. External shaping engines remain optional FFI/providers.
113. Axiom can implement its text layer natively.
114. No LLVM/GCC/Clang dependency is introduced.
115. Text processing can be allocation-conscious.
116. Large text can be streamed where applicable.
117. Text resources can be memory-budgeted.
118. Unicode conformance tests are versioned.
119. Font/shaper fuzzing is mandatory for bundled parsers.
120. No universal text-quality score exists.
121. Text semantics remain independent of rendering.
122. Rendering remains independent of any particular GPU API.
123. Font selection remains independent of GUI widgets.
124. Internationalization remains independent of compiler semantics.
125. **Axiom text foundation must correctly represent, shape, lay out and render modern multilingual Unicode text—from UTF-8 bytes through grapheme clusters and complex scripts to GPU/CPU glyph rendering—without conflating text semantics with presentation or forcing GUI/font/GPU infrastructure into unrelated applications.**

**BOOTSTRAP-464 hoàn tất.**

---

# BOOTSTRAP-465 — INPUT SYSTEM, KEYBOARD, MOUSE, TOUCH, PEN, GAMEPAD, IME & UNIFIED EVENT MODEL

Task kế tiếp:

```text
OS / Window
     ↓
Platform Input
     ↓
INPUT CORE
 ├── Event
 ├── Keyboard
 ├── Mouse
 ├── Touch
 ├── Pen
 ├── Gamepad
 ├── IME
 ├── Text Input
 ├── Gestures
 ├── Focus
 ├── Capture
 ├── Device
 └── Input Mapping
     ↓
GUI 452 / Games / Editor / Media
```

465 sẽ phải giải quyết đặc biệt:

- physical key vs logical key;
- Unicode text input vs keyboard shortcuts;
- IME composition;
- Vietnamese/Chinese/Japanese input;
- mouse/touch/pen unified pointer model;
- pressure/tilt/rotation của stylus;
- multi-touch;
- pointer capture;
- focus;
- keyboard repeat;
- gamepad;
- hotkey;
- event ordering;
- timestamp;
- device identity;
- raw input;
- OS-specific input;
- accessibility input;
- event queue/backpressure;
- thread affinity;
- deterministic input recording/replay;
- input-to-GUI routing;
- input-to-game routing;
- AI-readable event diagnostics.

Đặc biệt, 465 sẽ khóa một nguyên tắc quan trọng:

```text
Physical Keyboard
      ≠
Logical Key
      ≠
Text Input
      ≠
IME Composition
      ≠
Shortcut Command
```

Điều này sẽ giúp Axiom GUI/editor/game/media applications không mắc lỗi phổ biến kiểu **dùng keycode để xử lý text**, đồng thời hỗ trợ trực tiếp Unicode/IME của 464.