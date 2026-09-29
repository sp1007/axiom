# BOOTSTRAP-457 — TEXT, UNICODE, INTERNATIONALIZATION, LOCALIZATION, COLLATION & HUMAN-LANGUAGE FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của 457 là biến text thành một phần nền tảng được thiết kế đúng ngay từ đầu, nhưng **không đưa toàn bộ Unicode/i18n database vào language core**.

Nguyên tắc trung tâm:

```text id="1y2h4m"
Raw Bytes
    ↓
UTF-8 Code Units
    ↓
Unicode Scalar Values
    ↓
Grapheme Clusters
    ↓
Words / Lines / Sentences
    ↓
Locale-aware Text
```

Axiom tuyệt đối không đồng nhất các tầng này.

---

## 457.1 — Text model

Axiom phân biệt:

```text
Bytes
Utf8Bytes
char
StringSlice
String
Grapheme
TextSegment
```

---

## 457.2 — UTF-8 default

`String` mặc định chứa UTF-8 hợp lệ.

---

## 457.3 — UTF-8 invariant

Một giá trị `String` hợp lệ không được chứa malformed UTF-8.

---

## 457.4 — Raw bytes

Binary data dùng `[]u8` hoặc equivalent byte container, không dùng `String`.

---

## 457.5 — String ownership

`String` là owning UTF-8 sequence.

---

## 457.6 — StringSlice

`StringSlice`/string view là non-owning UTF-8 view.

Conceptual representation:

```text
{ ptr, byte_len }
```

---

## 457.7 — Slice lifetime

String view phải obey ownership/lifetime model 423.

Compiler phải ngăn safe code tạo view tới object đã hết lifetime khi dependency có thể được chứng minh local.

---

## 457.8 — No hidden allocation

String slicing/view không được tự động allocate.

---

## 457.9 — String concatenation

Concatenation có thể allocate khi cần capacity.

---

## 457.10 — String builder

Large concatenation nên dùng builder/buffer API.

---

# 457.11 — `char`

`char` đại diện một **Unicode scalar value**, không phải byte và không nhất thiết là một grapheme.

---

## 457.12 — Scalar range

`char` không chứa surrogate code points.

---

## 457.13 — UTF-8 encoding

`char` có thể encode thành 1–4 UTF-8 bytes.

---

## 457.14 — UTF-8 decoding

Malformed byte sequence trả `Result`, không panic trong checked API.

---

## 457.15 — Lossy decoding

Có thể có explicit lossy decoder thay thế malformed sequence bằng replacement character.

---

## 457.16 — Strict decoding

Strict decoder phải reject malformed UTF-8.

---

## 457.17 — BOM

UTF-8 BOM không bắt buộc.

Source compiler có thể accept BOM ở đầu file nhưng không đưa BOM vào semantic source content.

---

## 457.18 — Unicode identifiers

Axiom source hỗ trợ Unicode identifiers theo 429.

---

## 457.19 — Identifier normalization

Compiler dùng canonical normalization policy để tránh hai identifier visually equivalent nhưng semantic khác nhau ngoài ý muốn.

---

## 457.20 — Identifier confusables

Tooling có thể cảnh báo Unicode confusables.

Không biến warning thành semantic language rule trừ security profile.

---

# 457.21 — Byte indexing

String byte indexing không được giả vờ là character indexing.

---

## 457.22 — Character indexing

Nếu API hỗ trợ scalar indexing:

```text
s.char_at(i)
```

thì index là scalar-value index, không phải byte offset.

---

## 457.23 — Grapheme indexing

Grapheme indexing là separate API.

---

## 457.24 — Complexity disclosure

API documentation phải thể hiện indexing có thể O(n).

---

## 457.25 — Byte offset

Low-level APIs có thể truy cập theo byte offset sau UTF-8 boundary validation.

---

## 457.26 — Boundary validation

UTF-8 slicing phải đảm bảo boundary nằm tại code-point boundary.

---

## 457.27 — Invalid boundary

Invalid UTF-8 boundary trả error hoặc yêu cầu explicit unsafe API.

---

## 457.28 — Unsafe byte mutation

Raw mutation có thể phá UTF-8 invariant và phải nằm trong unsafe/validated construction boundary.

---

## 457.29 — Safe mutation

Safe String APIs duy trì UTF-8 validity.

---

## 457.30 — Capacity

Owning strings có `length` và `capacity` semantics tương tự dynamic vector.

---

# 457.31 — Grapheme clusters

Grapheme cluster đại diện đơn vị gần với "ký tự mà người dùng nhìn thấy".

---

## 457.32 — Grapheme != char

Một grapheme có thể chứa nhiều Unicode scalar values.

---

## 457.33 — Grapheme iterator

Unicode text library cung cấp grapheme iterator.

---

## 457.34 — Extended grapheme clusters

Implementation nên theo Unicode grapheme segmentation specification tương ứng với Unicode version được package sử dụng.

---

## 457.35 — Unicode version

Unicode data version phải được expose trong library metadata.

---

## 457.36 — Versioned Unicode behavior

Behavior phụ thuộc Unicode database phải versionable.

---

## 457.37 — Core independence

Compiler core không cần embed toàn bộ Unicode property database.

---

## 457.38 — Unicode data package

Unicode tables thuộc standard-library data package.

---

## 457.39 — Minimal compiler Unicode

Compiler chỉ embed dữ liệu cần thiết cho:

```text
identifier validation
lexical classification
normalization policy
```

---

## 457.40 — Runtime data pruning

Application không dùng advanced Unicode processing không được kéo toàn bộ Unicode database vào binary.

---

# 457.41 — Unicode normalization

Axiom hỗ trợ:

```text
NFC
NFD
NFKC
NFKD
```

thông qua Unicode library.

---

## 457.42 — No implicit normalization

String operations không tự động normalize toàn bộ text.

---

## 457.43 — Why no implicit normalization

Normalization có thể:

- tốn CPU;
- thay đổi representation;
- ảnh hưởng equality;
- ảnh hưởng security semantics.

Vì vậy phải explicit.

---

## 457.44 — Normalized string

Có thể có semantic wrapper:

```text
NormalizedString<NFC>
```

---

## 457.45 — Normalization validation

API có thể kiểm tra text đã ở normalization form nào.

---

## 457.46 — Normalization caching

Library có thể cache normalization state khi hữu ích.

---

## 457.47 — Security normalization

Security-sensitive identifiers phải chọn normalization policy explicit.

---

## 457.48 — Compatibility normalization

NFKC/NFKD không được dùng tự động cho mọi user-visible text.

---

## 457.49 — Canonical equivalence

Unicode-equivalent strings không mặc định có cùng byte representation.

---

## 457.50 — Equality modes

Axiom distinguish:

```text
byte_equal
scalar_equal
normalized_equal
locale_equal
```

---

# 457.51 — Case mapping

Library hỗ trợ Unicode case conversion.

---

## 457.52 — ASCII case

ASCII-only case conversion có fast path.

---

## 457.53 — Unicode case

Unicode case conversion dùng Unicode data.

---

## 457.54 — Locale-independent case

Default Unicode case mapping phải phân biệt với locale-specific mapping.

---

## 457.55 — Locale-sensitive case

Locale-specific case mapping explicit.

---

## 457.56 — Case folding

Case folding là separate operation phục vụ matching/search.

---

## 457.57 — Case-insensitive equality

Không được implement đơn giản bằng ASCII lowercase đối với Unicode text.

---

## 457.58 — Case expansion

Một scalar có thể map thành nhiều scalars.

API không được assume length-preserving.

---

## 457.59 — Case conversion allocation

Case conversion có thể allocate.

---

## 457.60 — In-place conversion

In-place conversion chỉ được cung cấp khi implementation có thể preserve correctness.

---

# 457.61 — Unicode properties

Library có API query properties như:

```text
is_letter
is_digit
is_whitespace
is_mark
is_number
is_punctuation
is_symbol
```

---

## 457.62 — Script

Có thể query script property.

---

## 457.63 — Block

Có thể query Unicode block.

---

## 457.64 — General category

Có thể query Unicode General_Category.

---

## 457.65 — Combining mark

Combining marks được xử lý như scalar values nhưng không tự coi là independent user-visible characters.

---

## 457.66 — Bidirectional text

Unicode Bidirectional Algorithm thuộc text library.

---

## 457.67 — Bidi control

Security tooling có thể detect suspicious bidi controls.

---

## 457.68 — Bidi rendering

Compiler không chịu trách nhiệm rendering bidi text.

---

## 457.69 — Script detection

Script detection là informational, không phải language identification proof.

---

## 457.70 — Unicode security profiles

Security-sensitive applications có thể enable Unicode restriction/confusable checks.

---

# 457.71 — Word segmentation

Word segmentation là separate operation.

---

## 457.72 — Sentence segmentation

Sentence segmentation là separate operation.

---

## 457.73 — Line breaking

Line-breaking algorithm thuộc text layout library.

---

## 457.74 — Word != whitespace split

Không coi `split(" ")` là Unicode word segmentation chuẩn.

---

## 457.75 — Locale-specific segmentation

Một số ngôn ngữ cần locale-aware segmentation.

---

## 457.76 — Dictionary segmentation

Dictionary-based segmentation là optional high-level package.

---

## 457.77 — Search normalization

Search APIs có thể combine normalization + case folding + locale policy.

---

## 457.78 — Search semantics

Search phải công khai semantic mode thay vì hidden normalization.

---

## 457.79 — Regex

Regex engine là library/ecosystem, không thuộc compiler core.

---

## 457.80 — Unicode regex

Regex implementation có thể support Unicode categories/graphemes.

---

# 457.81 — Collation

String byte order không phải human-language alphabetical order.

---

## 457.82 — Binary comparison

`byte_compare(a,b)` là deterministic machine ordering.

---

## 457.83 — Unicode code-point ordering

Scalar-value ordering là separate operation.

---

## 457.84 — Locale collation

Locale-aware collation là library operation.

---

## 457.85 — Collator

Conceptual:

```text
Collator(locale, options)
```

---

## 457.86 — Sort keys

Collator có thể generate reusable sort keys.

---

## 457.87 — Collation version

Collation behavior phải gắn với Unicode/locale data version.

---

## 457.88 — Stable sorting

Application cần reproducibility phải pin locale/collation version.

---

## 457.89 — Database integration

Database 455 không được assume String byte ordering tương đương locale collation.

---

## 457.90 — SQL collation

SQL/database layer phải define collation explicitly.

---

# 457.91 — Locale

Locale không chỉ là language code.

Conceptual:

```text
Locale {
    language
    script
    region
    extensions
}
```

---

## 457.92 — BCP-style language tags

Language identifiers nên support standardized language-tag representation.

---

## 457.93 — Locale negotiation

Network/UI applications có thể negotiate locale.

---

## 457.94 — Locale fallback

Fallback chain phải deterministic.

---

## 457.95 — Default locale

Application environment có thể cung cấp default locale nhưng library behavior phải expose source.

---

## 457.96 — Locale independence

Core numeric/string operations không phụ thuộc process-global locale.

---

## 457.97 — No hidden global locale mutation

Một thread không được âm thầm thay đổi formatting behavior của toàn process.

---

## 457.98 — Locale object

Locale nên là explicit value/object được truyền vào formatting/collation APIs.

---

## 457.99 — Locale data

Locale database là optional data package.

---

## 457.100 — Minimal locale builds

Embedded applications có thể chỉ bundle một subset locale.

---

# 457.101 — Number formatting

Formatting hỗ trợ:

```text
decimal
percent
currency
scientific
compact
```

khi locale package được dùng.

---

## 457.102 — Parsing

Parsing phải distinguish:

```text
machine_parse
locale_parse
```

---

## 457.103 — Machine number syntax

Machine parsing phải deterministic và locale-independent.

---

## 457.104 — Human number syntax

Human-facing parsing có thể locale-aware.

---

## 457.105 — Currency

Currency formatting không imply currency conversion.

---

## 457.106 — Currency conversion

FX rates là external data/service, không thuộc i18n core.

---

## 457.107 — Decimal formatting

Floating-point formatting phải có deterministic machine mode.

---

## 457.108 — Rounding

Rounding mode phải explicit khi financial correctness quan trọng.

---

## 457.109 — Monetary values

Financial libraries nên có decimal/fixed-point types thay vì dùng binary floating point blindly.

---

## 457.110 — Digit shaping

Locale-aware number rendering có thể support localized digits.

---

# 457.111 — Date/time localization

Date/time localization integrates 441 time primitives.

---

## 457.112 — Instant vs calendar

`Instant` không phải localized calendar date.

---

## 457.113 — Calendar

Calendar abstraction:

```text
Gregorian
other calendar systems
```

được library cung cấp.

---

## 457.114 — Time zone

Time zone database thuộc platform/data library.

---

## 457.115 — UTC

UTC remains machine-stable reference.

---

## 457.116 — Local time

Local time requires explicit time zone.

---

## 457.117 — DST

Daylight-saving transitions phải được xử lý bởi timezone database.

---

## 457.118 — Ambiguous local time

Repeated local times phải có explicit disambiguation policy.

---

## 457.119 — Invalid local time

Skipped local times phải trả explicit conversion error/policy result.

---

## 457.120 — Time-zone database version

Reproducible applications nên pin timezone database version.

---

# 457.121 — Pluralization

Localization library hỗ trợ plural categories.

---

## 457.122 — Plural rules

Không được giả định mọi ngôn ngữ chỉ có:

```text
one
other
```

---

## 457.123 — Message formatting

Message formatting phải support locale-aware plural/select rules.

---

## 457.124 — Gender/select

Message system có thể hỗ trợ grammatical selection.

---

## 457.125 — Message catalogs

Translation resources nằm ngoài compiler core.

---

## 457.126 — Resource IDs

Application có thể reference messages bằng stable IDs.

---

## 457.127 — Missing translation

Fallback policy phải explicit.

---

## 457.128 — Translation fallback

Typical chain:

```text
language-region
→ language
→ default locale
→ source language
```

nhưng application có thể cấu hình khác.

---

## 457.129 — Formatting safety

Localized messages phải phân biệt text data và executable formatting directives.

---

## 457.130 — Injection

Translation content không được trở thành code.

---

# 457.131 — Text encoding conversion

Axiom library hỗ trợ conversion giữa:

```text
UTF-8
UTF-16
UTF-32
```

---

## 457.132 — Native OS strings

Platform APIs có thể yêu cầu UTF-16, UTF-8 hoặc native representation.

---

## 457.133 — Conversion boundary

FFI/platform layer chịu trách nhiệm encoding conversion.

---

## 457.134 — Windows

Windows APIs có thể dùng UTF-16 interfaces.

---

## 457.135 — Unix

Unix APIs thường dùng byte sequences interpreted according to platform conventions; Axiom API phải không giả định mọi filesystem byte sequence là valid UTF-8.

---

## 457.136 — Path vs String

`Path` không phải synonym của `String`.

---

## 457.137 — Invalid filesystem names

OS có thể chứa path/name bytes không valid UTF-8.

Axiom phải có raw/native path representation.

---

## 457.138 — Lossless path handling

Path API phải cho phép round-trip native names mà không làm mất dữ liệu.

---

## 457.139 — Display conversion

Display-oriented conversion có thể dùng replacement semantics nhưng phải explicit.

---

## 457.140 — Security-sensitive path

Security code nên dùng native/path-safe APIs thay vì convert tùy tiện qua display strings.

---

# 457.141 — Terminal text

Terminal API phân biệt:

```text
raw bytes
UTF-8 text
control sequences
```

---

## 457.142 — ANSI/terminal control

Escape/control sequences không phải text semantics.

---

## 457.143 — Terminal width

Byte length, scalar count và display width là ba giá trị khác nhau.

---

## 457.144 — Display width

Text library có thể cung cấp Unicode display-width operation.

---

## 457.145 — Zero-width characters

Display-width calculation phải xử lý combining/zero-width characters.

---

## 457.146 — East Asian width

Terminal/UI layout có thể dùng Unicode East_Asian_Width properties.

---

## 457.147 — Emoji

Emoji sequence handling thuộc grapheme/rendering layer.

---

## 457.148 — Emoji != char

Một emoji hiển thị có thể gồm nhiều scalar values.

---

## 457.149 — Rendering

Actual glyph rendering thuộc GUI/font/text-rendering stack.

---

## 457.150 — Font shaping

OpenType shaping, HarfBuzz-like functionality và glyph rasterization thuộc rendering ecosystem.

---

# 457.151 — Text formatting language

Axiom standard formatting API:

```text
format(...)
print(...)
write(...)
```

có thể compile format strings when statically known.

---

## 457.152 — Compile-time format validation

Static format strings nên được kiểm tra tại compile time.

---

## 457.153 — Dynamic format strings

Dynamic format strings dùng runtime parser khi explicitly requested.

---

## 457.154 — Type-aware formatting

Formatter dispatch thông qua traits/interfaces.

---

## 457.155 — Debug formatting

Debug representation và user-facing display representation là separate concepts.

---

## 457.156 — Secret formatting

Sensitive types từ 456 không được tự động format raw secret values.

---

## 457.157 — Localization formatting

Localized formatting nhận explicit Locale.

---

## 457.158 — Allocation-free formatting

Formatter có thể write trực tiếp vào buffer/writer.

---

## 457.159 — Streaming formatting

Large output không cần tạo intermediate String.

---

## 457.160 — Compile-time literals

String literals được compiler validate UTF-8.

---

# 457.161 — Raw strings

Raw string literals hỗ trợ text không cần escape thông thường.

---

## 457.162 — Multiline strings

Multiline string syntax phải deterministic.

---

## 457.163 — Byte literals

`b"..."` là bytes, không phải String.

---

## 457.164 — Character literals

Character literal biểu diễn Unicode scalar.

---

## 457.165 — Escape validation

Invalid Unicode escape phải compile error.

---

## 457.166 — Unicode escapes

Support scalar escapes independent of UTF-8 encoding.

---

## 457.167 — Newline normalization

Source lexer có thể normalize supported line-ending forms internally nhưng source mapping phải giữ original positions đủ cho diagnostics.

---

## 457.168 — Text file reading

Text file APIs phải specify decoding.

---

## 457.169 — Default file text

UTF-8 is default Axiom text encoding.

---

## 457.170 — Explicit legacy encoding

Legacy encodings phải explicit codec.

---

# 457.171 — Text streams

Text stream abstraction wraps byte stream + decoder/encoder.

---

## 457.172 — Incremental decoding

Streaming decoder phải preserve incomplete multi-byte sequence between reads.

---

## 457.173 — Decode errors

Decoder có policy:

```text
strict
replace
ignore
```

và policy phải explicit.

---

## 457.174 — Encoder errors

Unicode scalar → target encoding failure trả typed error khi representation không thể encode.

---

## 457.175 — Buffer boundaries

UTF-8 sequence có thể bị chia giữa network/file chunks; decoder phải xử lý đúng.

---

## 457.176 — Network integration

HTTP/network layer 454 không được assume mỗi packet/read tương ứng một Unicode character.

---

## 457.177 — Protocol text

Protocol-specific encoding is defined by protocol, not automatically UTF-8.

---

## 457.178 — HTTP headers

HTTP APIs phải obey protocol-defined header encoding constraints.

---

## 457.179 — JSON

JSON text APIs dùng UTF-8 internally nhưng phải handle escaped Unicode correctly.

---

## 457.180 — Serialization

Serialization layer 454/455 phải distinguish textual encoding from binary representation.

---

# 457.181 — Text security

Unicode text có thể tạo security ambiguities.

---

## 457.182 — Confusable detection

Security package có thể detect visually confusable identifiers.

---

## 457.183 — Invisible characters

Tooling có thể flag suspicious invisible/control characters.

---

## 457.184 — Bidi controls

Source tooling có thể flag suspicious bidi controls.

---

## 457.185 — Identifier restrictions

Security-sensitive codebases có thể enforce restricted identifier scripts.

---

## 457.186 — Mixed scripts

Mixed-script identifiers có thể produce diagnostics.

---

## 457.187 — Homograph attacks

Language/tooling không thể ngăn mọi visual homograph attack, nhưng có thể cung cấp diagnostics.

---

## 457.188 — Display vs identity

Program identity must never depend solely on rendered appearance.

---

## 457.189 — Canonical identifiers

Symbol identity uses compiler canonical identifier representation.

---

## 457.190 — Source hashing

Source/content hashing uses canonical bytes/content policy defined by compiler/build system, not visual rendering.

---

# 457.191 — Performance model

UTF-8 storage is compact for ASCII and common text but variable-width.

---

## 457.192 — ASCII fast path

String algorithms nên có ASCII fast paths khi có thể.

---

## 457.193 — SIMD text

Compiler/backend 438 có thể optimize ASCII/UTF-8 scanning bằng SIMD.

---

## 457.194 — Vectorized validation

UTF-8 validation có thể có vectorized implementation.

---

## 457.195 — Zero-copy parsing

UTF-8 views có thể parse without allocation.

---

## 457.196 — Rope

Rope/piece-table structures thuộc library, dành cho editors/large text.

---

## 457.197 — Small String Optimization

`String` có thể dùng SSO nếu ABI/layout được specify và optimization có lợi.

---

## 457.198 — SSO is implementation detail

Language semantics không phụ thuộc SSO.

---

## 457.199 — String capacity

Capacity semantics phải deterministic enough for API contracts nhưng exact allocation strategy có thể implementation-specific.

---

## 457.200 — String performance metadata

AI/compiler metadata có thể expose allocation behavior của text operations.

---

# 457.201 — Compiler source text

Compiler source is UTF-8 by default.

---

## 457.202 — Lexer and Unicode

Lexer must distinguish Unicode identifier characters from arbitrary Unicode text.

---

## 457.203 — Token spans

Source span indexing can use byte offsets for efficient compiler implementation.

---

## 457.204 — User-facing columns

Diagnostics should expose human-oriented line/column information in addition to byte offsets.

---

## 457.205 — Column semantics

Tooling phải specify whether column means byte, Unicode scalar, or grapheme index.

Default human-facing column nên là Unicode scalar position hoặc editor-compatible UTF-16 position where protocol requires.

---

## 457.206 — LSP interoperability

LSP adapter có thể convert Axiom byte/scalar positions sang UTF-16 positions required by protocol.

---

## 457.207 — Stable source identity

FileId/content hash remains byte/content based, consistent with 446.

---

## 457.208 — Formatter

Formatter phải preserve Unicode scalar content và only alter syntactic whitespace according to formatting rules.

---

## 457.209 — Documentation

Documentation generator phải preserve UTF-8.

---

## 457.210 — AI metadata

AI semantic metadata stores identifiers and documentation as UTF-8.

---

# 457.211 — Text traits

Core/standard traits can include:

```text
Text
Encode
Decode
Display
Debug
CharSequence
GraphemeSequence
```

---

## 457.212 — Iterator integration

Text iterators integrate with standard Iterator trait.

---

## 457.213 — Scalar iterator

`String.chars()` yields Unicode scalar values.

---

## 457.214 — Byte iterator

`String.bytes()` yields UTF-8 bytes.

---

## 457.215 — Grapheme iterator

`String.graphemes()` yields grapheme views/segments.

---

## 457.216 — Words iterator

Optional Unicode-aware words iterator.

---

## 457.217 — Lines iterator

Lines are logical text segments and need not correspond to OS newline bytes.

---

## 457.218 — Newline modes

Library can recognize:

```text
LF
CRLF
CR
```

where appropriate.

---

## 457.219 — Line ending preservation

Editor/text transformation APIs can preserve original line ending mode.

---

## 457.220 — Text normalization pipeline

Applications can explicitly construct:

```text
decode
→ normalize
→ casefold
→ segment
→ compare
```

rather than relying on hidden transformations.

---

# 457.221 — Internationalization architecture

Recommended modules:

```text id="f0y2ce"
text-core
text-utf8
text-unicode
text-normalize
text-segment
text-collate
text-locale
text-format
text-message
text-encoding
text-display
text-security
```

---

## 457.222 — Data packages

Unicode/CLDR-like datasets should be separable from algorithms.

---

## 457.223 — Data versioning

Data packages have explicit version identifiers.

---

## 457.224 — Minimal data

Application may bundle only required locales/scripts.

---

## 457.225 — Lazy data

Large Unicode datasets may be memory-mapped or lazily loaded where appropriate.

---

## 457.226 — Deterministic builds

Pinned Unicode/locale data ensures reproducible behavior.

---

## 457.227 — OS-provided data

Platform APIs may provide locale/timezone data.

---

## 457.228 — OS-data variation

Applications requiring reproducibility should not silently depend on mutable OS locale databases.

---

## 457.229 — Data provenance

Build metadata records Unicode/locale/timezone dataset versions when relevant.

---

## 457.230 — AI inspection

AI tooling can query:

```text
Unicode version
locale data version
timezone database version
collation version
```

---

# 457.231 — Text and memory ownership

All text containers follow 423.

---

## 457.232 — Borrowed views

Views are non-owning and do not retain source object.

---

## 457.233 — Mutation invalidation

Mutating an owning String may invalidate existing views.

Safe API must prevent or clearly constrain such mutation.

---

## 457.234 — Unsafe views

Unsafe raw views may bypass invalidation guarantees.

---

## 457.235 — Thread safety

Immutable string values may be `Send`/`Share` when their representation permits.

---

## 457.236 — Mutable string

Concurrent mutable access requires synchronization under 424.

---

## 457.237 — Interning

String interning is optional library optimization.

---

## 457.238 — Global intern pool

No mandatory global intern pool.

---

## 457.239 — Arena strings

Parser/compiler can use arena allocation for temporary text.

---

## 457.240 — Lifetime

Arena string views become invalid when arena is destroyed; ownership analysis must model the dependency.

---

# 457.241 — FFI

C interop uses explicit:

```text
CString
CStr
```

or equivalent.

---

## 457.242 — NUL termination

Axiom `String` does not guarantee NUL termination.

---

## 457.243 — CString invariant

`CString` guarantees required terminator and forbids embedded NUL if API contract requires it.

---

## 457.244 — Conversion

`String → CString` validates NUL constraints and may allocate.

---

## 457.245 — Borrowed C strings

Borrowed C string wrappers obey foreign lifetime contract.

---

## 457.246 — UTF-16 FFI

Windows/other APIs can use explicit UTF-16 string types.

---

## 457.247 — Native string ABI

No universal native-string ABI is assumed.

---

## 457.248 — FFI encoding

Every foreign text API must specify encoding.

---

## 457.249 — FFI invalid encoding

Invalid foreign bytes cannot silently become valid Axiom String without explicit lossy conversion.

---

## 457.250 — FFI ownership

Foreign string allocation/deallocation follows 451 ownership annotations.

---

# 457.251 — Serialization

Text serialization distinguishes:

```text
String
Utf8Bytes
EncodedText
```

---

## 457.252 — UTF-8 wire format

Protocols that require UTF-8 can directly serialize String bytes.

---

## 457.253 — UTF-16 wire format

UTF-16 protocols require explicit encoder.

---

## 457.254 — Normalization on wire

No implicit normalization unless protocol specification requires it.

---

## 457.255 — Canonical serialization

Protocol-defined canonicalization must happen in protocol package.

---

## 457.256 — Text hashes

Hashing text must specify whether hash input is:

```text
raw UTF-8 bytes
normalized UTF-8
encoded representation
```

---

## 457.257 — Cryptographic signatures

Signature protocols must define canonical text representation before signing.

---

## 457.258 — No visual signing

Rendered appearance is never a canonical cryptographic representation.

---

## 457.259 — Unicode security and crypto

Normalization/confusable processing is protocol-specific, not automatically inserted into 456.

---

## 457.260 — Deterministic text serialization

Machine protocols should use deterministic encoding independent of user locale.

---

# 457.261 — Testing

Unicode test suite must include:

```text
ASCII
multibyte UTF-8
combining marks
emoji sequences
RTL
mixed scripts
invalid UTF-8
normalization
case mapping
graphemes
word segmentation
collation
locale formatting
encoding conversion
```

---

## 457.262 — Unicode conformance

Where an algorithm claims Unicode conformance, tests reference a specific Unicode version.

---

## 457.263 — Differential testing

Unicode algorithms can compare against independent implementations.

---

## 457.264 — Fuzzing

UTF-8 decoders and Unicode parsers must be fuzzed.

---

## 457.265 — Invalid sequences

Fuzzing must include malformed overlong sequences, surrogate encodings, truncated sequences and out-of-range scalars.

---

## 457.266 — Security tests

Test suite must cover bidi/confusable/invisible-character handling where security tooling is enabled.

---

## 457.267 — Locale tests

Locale formatting tests pin locale data version.

---

## 457.268 — Timezone tests

Timezone tests pin timezone database version.

---

## 457.269 — Reproducibility

Same pinned Unicode/locale data must produce deterministic machine-format results.

---

## 457.270 — Performance tests

Benchmark:

```text
UTF-8 validation
ASCII scan
Unicode iteration
grapheme segmentation
normalization
case mapping
collation
formatting
encoding conversion
```

---

# 457.271 — AI-facing text metadata

Compiler/standard library metadata can expose:

```text
encoding
normalization
locale dependency
allocation
complexity
Unicode version
```

---

## 457.272 — AI misuse diagnostics

AI tooling should be able to detect patterns such as:

```text
byte index used as char index
ASCII lowercase used for Unicode matching
locale-sensitive operation without locale
String passed to C API requiring NUL
```

---

## 457.273 — Semantic query

AI can query:

```text
is this string valid UTF-8?
what encoding does this API expect?
does this operation allocate?
is comparison locale-aware?
```

---

## 457.274 — Documentation metadata

Public text APIs expose machine-readable encoding and allocation contracts.

---

## 457.275 — Source diagnostics

Unicode-related compiler diagnostics use stable `E457xxx` identifiers.

---

# 457.276 — Core language boundary

Language core owns only the minimum required semantics:

```text
UTF-8 source
Unicode identifiers
char = Unicode scalar value
String = valid UTF-8 text
```

---

## 457.277 — Standard library boundary

Standard library owns:

```text
Unicode properties
normalization
segmentation
case mapping
collation
formatting
encoding
locale
```

---

## 457.278 — Platform boundary

Platform layer owns:

```text
native keyboard/input
font APIs
timezone providers
OS locale
clipboard
IME
```

---

## 457.279 — GUI boundary

GUI/text-rendering layer owns:

```text
glyph shaping
font fallback
cursor movement
text selection
line layout
bidi rendering
IME composition
```

---

## 457.280 — No Unicode monolith

Axiom must not turn Unicode into a giant mandatory runtime component.

---

# 457.281 — Hard invariants

1. Axiom source is UTF-8 by default.
2. `String` contains valid UTF-8.
3. Raw bytes are not Strings.
4. `char` means Unicode scalar value.
5. `char` is not a byte.
6. `char` is not a grapheme.
7. Grapheme clusters are separate.
8. String byte indexing must not masquerade as character indexing.
9. UTF-8 boundaries must be validated in safe slicing.
10. Invalid UTF-8 must not silently enter safe `String`.
11. Strict decoding must reject malformed UTF-8.
12. Lossy decoding must be explicit.
13. String views obey ownership/lifetime semantics.
14. String views do not implicitly allocate.
15. String mutation must respect view invalidation.
16. No mandatory garbage collector is introduced for text.
17. Unicode normalization is explicit.
18. String equality does not implicitly normalize.
19. NFC/NFD/NFKC/NFKD are distinct operations.
20. Unicode version is identifiable.
21. Advanced Unicode tables are not mandatory compiler/runtime components.
22. Unicode properties are library functionality.
23. Grapheme segmentation is library functionality.
24. Word segmentation is library functionality.
25. Sentence segmentation is library functionality.
26. Line breaking is library functionality.
27. Bidi processing is not compiler rendering.
28. Case conversion is not ASCII-only by default for Unicode APIs.
29. Case folding is distinct from case conversion.
30. Locale-sensitive case mapping is explicit.
31. Collation is distinct from byte comparison.
32. Locale is an explicit semantic object.
33. Process-global hidden locale mutation is forbidden.
34. Locale data is versionable.
35. Reproducible builds can pin locale data.
36. Number formatting must distinguish machine and human parsing.
37. Currency formatting is not currency conversion.
38. Financial decimal semantics must not depend on binary floating point accidentally.
39. Date/time localization is separate from `Instant`.
40. Local time requires timezone semantics.
41. Ambiguous/skipped local times require explicit handling.
42. Pluralization is locale-aware.
43. Translation resources are external data, not compiler syntax.
44. Translation text cannot become executable code.
45. Text stream decoding handles UTF-8 sequences split across buffers.
46. Network reads are not Unicode character boundaries.
47. Protocol encoding is protocol-defined.
48. `Path` is not necessarily `String`.
49. Filesystem names may contain non-UTF-8 native data.
50. Lossless native-path handling is required.
51. `CString` is distinct from `String`.
52. `String` does not guarantee NUL termination.
53. C-string conversion is explicit.
54. Foreign text encoding must be declared.
55. Invalid foreign encoding cannot silently become valid String.
56. Text serialization must specify encoding.
57. Cryptographic text signing requires canonical representation defined by protocol.
58. Visual appearance is never cryptographic identity.
59. ASCII fast paths are permitted.
60. SIMD UTF-8 processing is permitted.
61. String SSO is an implementation optimization, not semantic requirement.
62. Allocation behavior should be queryable.
63. String interning is optional.
64. Unicode data can be selectively bundled.
65. Unicode data can be memory-mapped/lazy-loaded where useful.
66. Unicode data provenance is recorded when relevant.
67. Unicode security diagnostics may detect confusables.
68. Suspicious bidi controls may be diagnosed.
69. Mixed-script identifiers may be diagnosed.
70. Visual homographs cannot be completely solved by the compiler.
71. Identifier semantic identity is based on canonical compiler representation, not rendered appearance.
72. LSP position conversion must account for UTF-16 protocol semantics.
73. Compiler source spans may use byte offsets internally.
74. Human-facing diagnostics must expose meaningful character positions.
75. Unicode decoders must be fuzz-tested.
76. Unicode conformance tests must pin Unicode version.
77. Locale tests must pin locale data.
78. Timezone tests must pin timezone database.
79. Text operations must integrate with ownership model 423.
80. Text operations must integrate with `Send`/`Share` model 424.
81. Text APIs must use Result for invalid decoding/encoding where appropriate.
82. Text APIs must not panic on ordinary malformed external input.
83. Text APIs must expose complexity/allocation behavior where meaningful.
84. AI tooling must be able to inspect encoding semantics.
85. AI tooling must be able to inspect allocation and locale dependencies.
86. AI diagnostics should identify common byte/character/string misuse.
87. UTF-8 is default, but protocol-specific encodings remain explicit.
88. GUI rendering is separate from text storage.
89. Font shaping is separate from Unicode storage.
90. IME is platform/UI functionality.
91. Unicode support must not force a giant runtime.
92. Core remains small while standard library can provide complete Unicode functionality.
93. Text security checks are advisory unless explicitly enforced by a security profile.
94. No implicit locale-dependent machine behavior.
95. No hidden normalization.
96. No hidden encoding conversion.
97. No hidden allocation merely because text is being viewed.
98. No hidden Unicode database dependency for applications that do not use advanced text functionality.
99. Axiom must support efficient Unicode text while preserving native byte-level performance.
100. **Axiom's fundamental text model must remain: bytes are bytes, UTF-8 is encoded text, `char` is a scalar value, graphemes are user-perceived clusters, and locale-aware human language is a higher semantic layer.**

**BOOTSTRAP-457 hoàn tất.**

---

# BOOTSTRAP-458 — NUMERIC COMPUTING, SIMD, VECTOR/MATRIX, FLOATING-POINT, DECIMAL & HIGH-PERFORMANCE MATH

Task này sẽ khóa nền tảng numeric của Axiom để sau đó có thể xây:

```text
CPU numeric
SIMD
linear algebra
signal processing
image processing
scientific computing
tensor/ML
GPU
```

mà **không biến compiler core thành một framework AI/ML**.

Kiến trúc dự kiến:

```text
Axiom primitive types
        ↓
Scalar arithmetic
        ↓
SIMD / Vector
        ↓
Matrix / Linear Algebra
        ↓
Math / Numeric libraries
        ↓
Tensor / ML
        ↓
GPU compute
```

Trọng tâm của 458 sẽ là **vector types, SIMD ABI, floating-point semantics, fast-math, NaN/Inf, FMA, transcendental math, integer overflow, fixed-point/decimal, complex numbers, matrix layout, alignment, vectorization và khả năng đạt hiệu năng C/C++ mà không buộc programmer phải viết intrinsic cho mọi thứ.**