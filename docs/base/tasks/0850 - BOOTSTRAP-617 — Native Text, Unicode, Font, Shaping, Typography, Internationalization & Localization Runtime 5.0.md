Tiếp tục với **BOOTSTRAP-617**, xây nền tảng text/Unicode/typography native để Axiom xử lý tiếng Việt và đa ngôn ngữ đúng ở mức runtime/compiler, đồng thời làm nền cho GUI, document, subtitle và rendering.

:::writing{variant="document" id="58324" title="BOOTSTRAP-617 — Native Text, Unicode, Font, Shaping, Typography, Internationalization & Localization Runtime 5.0"}
# BOOTSTRAP-617 — Native Text, Unicode, Font, Shaping, Typography, Internationalization & Localization Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Native Runtime / Text & Internationalization  
**Depends on:** BOOTSTRAP-600 → 616

---

# 1. Purpose

BOOTSTRAP-617 defines the native text foundation of Axiom:

- Unicode;
- UTF-8;
- Unicode scalar values;
- grapheme clusters;
- normalization;
- case conversion;
- Unicode properties;
- bidirectional text;
- script detection;
- text segmentation;
- locale;
- collation;
- number/date formatting;
- pluralization;
- message localization;
- font discovery;
- font loading;
- font fallback;
- font metrics;
- glyph mapping;
- text shaping;
- OpenType features;
- complex-script layout;
- text measurement;
- line breaking;
- text layout;
- text-to-GPU rendering bridge;
- text rasterization;
- text caching;
- localization resources.

Primary requirement:

> **UTF-8 is the canonical application text representation.**

The runtime must correctly support Vietnamese, English and other Unicode languages without requiring applications to manually manipulate UTF-16 code units or platform-specific encodings.

---

# 2. Design Goals

617 must provide:

1. Correct Unicode semantics.
2. UTF-8-first APIs.
3. Zero unnecessary conversion.
4. Efficient ASCII fast paths.
5. Correct Vietnamese combining marks.
6. Correct emoji handling.
7. Correct complex-script shaping.
8. Bidirectional text.
9. Font fallback.
10. Locale-aware formatting.
11. Deterministic text operations where required.
12. GPU-compatible glyph rendering.
13. No mandatory third-party text framework.
14. Platform font integration through providers.
15. No GC dependency.
16. Bounded allocations.
17. AI-friendly text metadata.
18. Compiler integration.
19. Cross-platform behavior.
20. Explicit distinction between bytes, code points, graphemes and glyphs.

---

# 3. Fundamental Representation

Axiom defines four distinct concepts:

```text
Byte
UnicodeScalar
GraphemeCluster
Glyph
```

They must never be treated as interchangeable.

---

# 4. UTF-8 Canonical Representation

The ordinary Axiom string:

```text
String
```

stores UTF-8.

Example:

```text
let s: String = "Xin chào Việt Nam"
```

---

# 5. UTF-8 Invariant

A valid `String` must contain valid UTF-8.

Invalid UTF-8 is represented separately:

```text
ByteString
```

or:

```text
Utf8Error
```

---

# 6. Raw Bytes

Binary data must use:

```text
Bytes
```

not `String`.

This prevents accidental interpretation of arbitrary binary data as text.

---

# 7. Unicode Scalar

A Unicode scalar represents one Unicode code point excluding surrogate code points.

```text
UnicodeScalar
```

---

# 8. Character Semantics

Axiom does not define:

```text
1 byte = character
```

nor:

```text
1 scalar = visible character
```

because a visible character can consist of multiple scalars.

---

# 9. Grapheme Cluster

The user-visible character unit is:

```text
Grapheme
```

Example:

```text
e + combining acute
```

may form one grapheme cluster.

---

# 10. Vietnamese Requirement

The implementation must correctly handle:

```text
ă
â
ê
ô
ơ
ư
đ
```

and combining tone/diacritic sequences.

It must not assume every Vietnamese character is represented by one Unicode scalar.

---

# 11. String Indexing

Direct integer indexing:

```text
s[i]
```

must not silently mean byte indexing.

Axiom provides explicit APIs:

```text
byte_at()
scalar_at()
grapheme_at()
```

---

# 12. String Slicing

Supported views:

```text
ByteSlice
ScalarSlice
GraphemeSlice
```

with explicit semantics.

---

# 13. String View

```text
StringView
```

is a non-owning UTF-8 view.

It does not own the underlying storage.

---

# 14. String Ownership

```text
String
```

owns its data.

It may use small-string optimization.

---

# 15. Small String Optimization

Short strings may be stored inline.

The exact inline capacity is ABI/platform dependent.

---

# 16. String Immutability

Strings are immutable values by default.

Mutation requires:

```text
StringBuilder
```

or mutable byte/text buffer APIs.

---

# 17. StringBuilder

```text
StringBuilder {
    buffer
    length
    capacity
}
```

provides amortized efficient construction.

---

# 18. Builder Reservation

```text
reserve(bytes)
```

allows predictable allocation.

---

# 19. ASCII Fast Path

Operations should detect ASCII strings and use optimized paths for:

- comparison;
- search;
- copying;
- case conversion;
- hashing;
- validation.

---

# 20. UTF-8 Validation

The runtime provides:

```text
Utf8.validate(bytes)
```

with linear complexity.

---

# 21. Incremental UTF-8 Decoder

Streaming input supports:

```text
Utf8Decoder
```

for arbitrary chunk boundaries.

---

# 22. UTF-8 Error Policy

Explicit policies:

```text
Reject
Replace
PreserveBytes
```

`String` construction defaults to `Reject`.

---

# 23. Unicode Replacement

When requested:

```text
�
```

may replace malformed sequences.

Replacement must be explicit and observable.

---

# 24. Unicode Version

Unicode algorithms are versioned.

Runtime exposes:

```text
Unicode.version()
```

---

# 25. Unicode Database

The runtime may contain a compact generated Unicode property database.

It must not require a huge general-purpose runtime database.

---

# 26. Unicode Properties

Supported property queries include:

```text
GeneralCategory
Script
ScriptExtensions
Block
EastAsianWidth
CombiningClass
BidiClass
LineBreakClass
GraphemeBreakClass
WordBreakClass
SentenceBreakClass
```

---

# 27. Character Classification

APIs:

```text
is_letter()
is_digit()
is_whitespace()
is_mark()
is_punctuation()
is_symbol()
```

must be Unicode-aware.

---

# 28. ASCII vs Unicode Classification

ASCII-specific functions remain available:

```text
ascii_is_digit()
ascii_is_alpha()
```

for high-performance protocol parsing.

---

# 29. Case Mapping

Support:

```text
to_upper()
to_lower()
to_title()
case_fold()
```

using Unicode rules.

---

# 30. Locale Independence

Unicode case folding is distinct from locale-sensitive casing.

Applications must not confuse:

```text
case_fold()
```

with display-oriented localized case conversion.

---

# 31. Locale

```text
Locale
```

contains:

```text
language
script?
region?
calendar?
numbering_system?
```

---

# 32. Locale Identifier

Canonical form:

```text
language[-script][-region]
```

with Unicode BCP-47-compatible tags.

Examples:

```text
vi
vi-VN
en
en-US
zh-Hans
zh-Hant
```

---

# 33. Locale Parsing

```text
Locale.parse("vi-VN")
```

returns a normalized locale.

---

# 34. Locale Matching

Locale negotiation supports:

```text
requested
available
fallback
```

with deterministic selection rules.

---

# 35. Language Tags

Language tags are represented as typed values:

```text
LanguageTag
```

rather than arbitrary strings where practical.

---

# 36. Script

```text
Script
```

identifies writing systems:

```text
Latin
Cyrillic
Greek
Arabic
Han
Hiragana
Katakana
Devanagari
Hangul
...
```

---

# 37. Region

```text
Region
```

represents standardized geographic regions used by locale data.

---

# 38. Text Segmentation

617 provides:

```text
GraphemeIterator
WordIterator
SentenceIterator
LineBreakIterator
```

---

# 39. Grapheme Segmentation

Grapheme segmentation follows the Unicode grapheme boundary algorithm.

---

# 40. Extended Grapheme Clusters

Applications generally use extended grapheme clusters.

---

# 41. Emoji

Emoji sequences may contain:

```text
multiple scalars
variation selectors
zero-width joiners
skin-tone modifiers
regional indicators
```

and must be treated accordingly.

---

# 42. Emoji Width

The runtime must not assume:

```text
one emoji = one column
```

Terminal/display width is context dependent.

---

# 43. Word Segmentation

Unicode word-boundary rules are exposed.

Language-specific tokenizers may exist above the core layer.

---

# 44. Sentence Segmentation

Sentence boundary detection follows Unicode rules with optional locale/provider extensions.

---

# 45. Line Breaking

Line breaking uses Unicode line-break classes.

---

# 46. Hyphenation

Hyphenation is an optional higher-level provider.

The core runtime exposes a boundary for:

```text
Hyphenator
```

rather than embedding dictionaries for every language.

---

# 47. Normalization

Supported forms:

```text
NFC
NFD
NFKC
NFKD
```

---

# 48. Normalization APIs

```text
normalize_nfc()
normalize_nfd()
normalize_nfkc()
normalize_nfkd()
```

---

# 49. Normalization Policy

Axiom does **not** automatically normalize every string.

This avoids:

- unnecessary CPU cost;
- data corruption;
- surprising equality semantics.

---

# 50. Canonical Equality

Applications can explicitly request:

```text
canonical_equal(a, b)
```

---

# 51. Binary String Equality

Ordinary:

```text
a == b
```

means byte-for-byte equality of valid UTF-8.

---

# 52. Unicode-Aware Equality

A separate operation performs normalized/canonical comparison.

---

# 53. Security Normalization

Security-sensitive identifiers may require a stronger normalization and restriction policy.

---

# 54. Identifier Rules

Axiom source identifiers are distinct from ordinary Unicode text.

The compiler defines allowed identifier profiles.

---

# 55. Source Encoding

Axiom source files are:

```text
UTF-8
```

by default.

---

# 56. Source BOM

UTF-8 BOM may be accepted but is not required.

---

# 57. Compiler Unicode Diagnostics

Compiler diagnostics preserve source locations in:

```text
byte offset
line
column
grapheme-aware display column
```

---

# 58. Source Position

The compiler internally stores byte offsets.

This permits efficient source indexing.

---

# 59. User-Facing Column

Diagnostics can additionally report grapheme/display columns.

---

# 60. Text Hashing

String hashing operates on UTF-8 bytes by default.

Unicode-normalized hashing is a separate operation.

---

# 61. Hash Stability

Axiom can define:

```text
StableTextHash
```

for persistent structures and serialized metadata.

---

# 62. Collation

Locale-sensitive sorting uses:

```text
Collator
```

---

# 63. Collation Strength

Supported conceptual levels:

```text
Primary
Secondary
Tertiary
Quaternary
Identical
```

---

# 64. Collation Is Not Equality

Two strings may compare equivalent for sorting while remaining bytewise unequal.

---

# 65. Natural Sort

Natural sorting is a higher-level utility:

```text
file2
file10
```

rather than pure lexicographic ordering.

---

# 66. Number Formatting

```text
NumberFormatter
```

supports locale-sensitive:

```text
decimal
percent
currency
scientific
compact
```

---

# 67. Number Parsing

```text
NumberParser
```

supports locale-aware parsing where explicitly requested.

Protocol parsing should use locale-independent parsers.

---

# 68. Decimal Formatting

Formatting must correctly handle:

```text
group separators
decimal separator
negative signs
currency placement
digits
```

---

# 69. Currency

```text
Currency
```

is represented by a typed ISO-compatible code.

---

# 70. Date/Time Formatting

617 integrates with the Axiom time subsystem.

```text
DateFormatter
TimeFormatter
DateTimeFormatter
```

---

# 71. Calendar

The locale layer can expose:

```text
Gregorian
Buddhist
Japanese
Islamic
Hebrew
...
```

through providers.

The core calendar model remains explicitly typed.

---

# 72. Time Zone

Time-zone data belongs to a dedicated provider/database.

The formatter must not assume system local time is UTC.

---

# 73. Relative Time

Optional formatter:

```text
RelativeTimeFormatter
```

for:

```text
yesterday
today
tomorrow
3 minutes ago
```

---

# 74. Plural Rules

```text
PluralRules
```

supports categories:

```text
zero
one
two
few
many
other
```

---

# 75. Message Formatting

```text
MessageFormatter
```

supports structured arguments.

Example conceptual form:

```text
"{count, plural,
  one {# file}
  other {# files}
}"
```

---

# 76. No String Concatenation for Localization

Localized messages should not rely on manually concatenating translated fragments.

---

# 77. Message IDs

Localization resources use stable IDs:

```text
message.home.title
message.files.count
```

---

# 78. Translation Resource

Axiom resource format:

```text
.axloc
```

---

# 79. AXLOC

AXLOC contains:

```text
locale
resource_version
message_table
plural_rules
format_schema
fallback
```

---

# 80. Localization Lookup

```text
loc.get("message.home.title")
```

---

# 81. Missing Translation

Policies:

```text
Fallback
Placeholder
Error
```

---

# 82. Fallback Chain

Example:

```text
vi-VN
 ↓
vi
 ↓
default
```

---

# 83. Translation Validation

Build tooling detects:

- missing IDs;
- unused IDs;
- malformed placeholders;
- incompatible argument types;
- invalid plural branches.

---

# 84. Typed Messages

Compiler-generated localization bindings may provide:

```text
MessageId<TArgs>
```

so argument mismatches become compile-time errors.

---

# 85. Localization Example

Conceptual Axiom:

```text
let msg = tr.files_count(count)
```

The compiler can validate that `count` is the expected argument type.

---

# 86. Translation Formatting Safety

Localized messages cannot execute arbitrary code.

Formatting expressions are declarative.

---

# 87. Localization Resource Security

AXLOC is treated as data, not executable code.

---

# 88. Font Model

Core types:

```text
Font
FontFace
FontFamily
FontInstance
FontMetrics
Glyph
GlyphRun
```

---

# 89. Font Discovery

```text
FontManager.enumerate()
```

returns available fonts from platform/system/package providers.

---

# 90. Font Source

Fonts can originate from:

```text
System
ApplicationPackage
Memory
File
EmbeddedResource
```

---

# 91. Font Security

Font parsers must be sandbox-safe and bounded.

Malformed font data must not compromise the application.

---

# 92. Supported Font Formats

Compatibility boundary:

```text
TrueType
OpenType
WOFF
WOFF2
```

where providers support them.

---

# 93. Font Provider

```text
FontProvider
```

may be:

```text
Native
Platform
Package
Memory
Test
```

---

# 94. Font Family

A family groups related faces:

```text
Regular
Italic
Bold
Bold Italic
...
```

---

# 95. Font Selection

Selection considers:

```text
family
weight
width
slant
optical size
language/script
```

---

# 96. Variable Fonts

Variable axes may include:

```text
weight
width
slant
optical_size
```

plus custom registered axes.

---

# 97. Font Instance

A variable font instance contains explicit axis values.

---

# 98. Font Fallback

When a font lacks a glyph, the runtime searches fallback fonts.

---

# 99. Fallback Order

Fallback considers:

1. requested font;
2. script-compatible fonts;
3. locale;
4. emoji fonts where appropriate;
5. platform fallback;
6. application fallback.

---

# 100. Mixed Font Runs

A single text paragraph can contain multiple fonts.

---

# 101. Fallback Run

Shaping may produce:

```text
GlyphRun(font=A)
GlyphRun(font=B)
GlyphRun(font=C)
```

for one logical string.

---

# 102. Font Matching

Font matching must not silently substitute an unrelated script font when a compatible fallback exists.

---

# 103. Font Metrics

Metrics include:

```text
ascent
descent
line_gap
cap_height
x_height
underline_position
underline_thickness
```

---

# 104. Glyph Metrics

Each glyph may have:

```text
advance_x
advance_y
offset_x
offset_y
bounds
```

---

# 105. Glyph ID

A glyph ID is font-local.

It must never be treated as a Unicode code point.

---

# 106. Shaping

```text
Shaper
```

converts:

```text
Unicode text
+
font
+
script
+
language
+
features
```

into:

```text
GlyphRun
```

---

# 107. Shaping Input

```text
ShapeRequest {
    text
    font
    direction
    script
    language
    features
}
```

---

# 108. Shaping Output

```text
GlyphRun {
    glyphs[]
    positions[]
    clusters[]
    font
}
```

---

# 109. Cluster Mapping

Every glyph run must preserve mapping between glyphs and source text clusters.

This is essential for:

- cursor movement;
- selection;
- hit testing;
- text editing.

---

# 110. Ligatures

OpenType ligatures may combine multiple characters into one glyph.

---

# 111. Contextual Shaping

Arabic, Indic and other complex scripts require contextual shaping.

The runtime must not implement shaping as simple character-to-glyph lookup.

---

# 112. Vietnamese Shaping

Vietnamese Latin text must correctly preserve:

- base letter;
- diacritics;
- tone marks;
- positioning;
- fallback behavior.

---

# 113. Arabic

Right-to-left shaping and contextual forms must be supported by the shaping engine/provider.

---

# 114. Indic Scripts

Complex Indic shaping requires script-specific OpenType behavior.

---

# 115. Thai

Thai combining marks and positioning must be handled correctly.

---

# 116. Devanagari

Conjuncts and reordering must be handled by the shaping system.

---

# 117. Hangul

Hangul syllable composition and font shaping must be supported.

---

# 118. CJK

CJK font fallback and glyph selection must support locale/script distinctions.

---

# 119. Emoji Shaping

Emoji sequences are shaped as sequences, not independently rendered scalar values.

---

# 120. Variation Selectors

Variation selectors must affect glyph selection.

---

# 121. OpenType Features

Features may include:

```text
liga
clig
kern
calt
frac
subs
sups
smcp
onum
tnum
```

---

# 122. Feature API

```text
TextFeature {
    tag
    value
}
```

---

# 123. Feature Defaults

Font-defined defaults apply unless application explicitly overrides them.

---

# 124. Direction

Text direction:

```text
LTR
RTL
Auto
```

---

# 125. Bidirectional Text

The runtime implements Unicode Bidirectional Algorithm semantics.

---

# 126. Bidi Paragraph

```text
BidiParagraph
```

computes directional runs.

---

# 127. Bidi Run

A paragraph may contain:

```text
LTR
RTL
LTR
RTL
```

runs.

---

# 128. Mixed Vietnamese/English

A Vietnamese sentence containing English tokens must remain correctly ordered and shaped.

Example conceptual input:

```text
"Xin chào, OpenAI!"
```

must not require the application to manually split scripts.

---

# 129. Text Layout

```text
TextLayout
```

takes shaped runs and produces lines.

---

# 130. Layout Inputs

```text
text
font
width
direction
alignment
line_spacing
wrap_mode
```

---

# 131. Layout Outputs

```text
Line
GlyphRun
Bounds
Baseline
ClusterMap
```

---

# 132. Wrapping

Modes:

```text
NoWrap
Character
Word
WordThenCharacter
```

---

# 133. Line Width

Layout must respect shaped glyph advances, not raw character count.

---

# 134. Alignment

```text
Start
Center
End
Justify
```

with direction-aware interpretation.

---

# 135. Vertical Alignment

```text
Top
Center
Bottom
Baseline
```

---

# 136. Justification

Justification may modify:

```text
word spacing
glyph positioning
```

according to script capabilities.

---

# 137. Ellipsis

Supported forms:

```text
End
Middle
Start
```

subject to layout constraints.

---

# 138. Text Measurement

```text
measure(text, constraints)
```

returns:

```text width
height
line_count
baseline
bounds
```

---

# 139. Hit Testing

```text
layout.hit_test(x, y)
```

returns a logical text position.

---

# 140. Cursor Position

Cursor positions operate on grapheme boundaries, not arbitrary UTF-8 byte positions.

---

# 141. Selection

Selection preserves grapheme/cluster semantics.

---

# 142. Caret Movement

Operations:

```text
move_left
move_right
move_word_left
move_word_right
move_line_start
move_line_end
```

must use Unicode segmentation.

---

# 143. Delete

Backspace/delete should remove a logical grapheme cluster rather than an arbitrary byte sequence.

---

# 144. Text Editing Model

A higher-level editor may use:

```text
TextBuffer
TextSelection
TextCursor
EditTransaction
```

---

# 145. Rope Boundary

For very large documents, 617 defines a boundary for:

```text
RopeText
PieceTable
GapBuffer
```

implementations.

The core `String` remains compact.

---

# 146. Large Document Requirement

Large documents must not require copying the entire document for every edit.

---

# 147. Text Rendering

Rendering uses:

```text
GlyphAtlas
GlyphCache
TextRenderer
```

---

# 148. Glyph Atlas

Glyphs may be packed into GPU textures.

---

# 149. Atlas Types

Possible:

```text
Bitmap
Grayscale
LCD
SDF
MSDF
Color
```

---

# 150. Color Glyphs

Support:

```text
COLR
CPAL
CBDT
CBLC
sbix
SVG
```

where backend/provider supports them.

---

# 151. GPU Text Rendering

Preferred path:

```text
Text
 ↓
Shape
 ↓
GlyphRun
 ↓
GlyphAtlas
 ↓
615 GPU Pipeline
 ↓
Screen
```

---

# 152. CPU Text Rendering

A software renderer must remain available for:

- headless;
- testing;
- embedded;
- fallback.

---

# 153. Rasterizer Provider

```text
FontRasterizer
```

can use:

```text
NativeProvider
PlatformProvider
SoftwareProvider
GPUProvider
```

---

# 154. Glyph Cache Key

Cache key includes:

```text
font_id
font_instance
glyph_id
size
render_mode
subpixel_mode
```

---

# 155. Cache Invalidation

Font unloading or provider changes invalidate dependent glyph caches.

---

# 156. DPI

Text layout separates:

```text
logical units
device pixels
```

---

# 157. DPI Scaling

Integration with BOOTSTRAP-615 provides display scale.

---

# 158. Fractional Metrics

Layout should retain subpixel precision internally.

---

# 159. Pixel Snapping

Pixel snapping is an explicit rendering policy.

---

# 160. Hinting

Font hinting is provider/backend controlled.

---

# 161. Subpixel Rendering

Subpixel LCD rendering is optional.

It must not be assumed available on modern displays.

---

# 162. Accessibility

Text objects can expose:

```text
semantic text
language
role
selection
caret
```

to a future accessibility layer.

---

# 163. Copy/Paste

Clipboard text uses UTF-8 internally with platform conversion at the boundary.

---

# 164. Clipboard Formats

Possible formats:

```text
PlainText
RichText
HTML
Image
```

but rich clipboard belongs to a higher layer.

---

# 165. Text-to-Speech Boundary

617 exposes text semantics to a future speech subsystem.

It does not implement TTS itself.

---

# 166. Speech-to-Text Boundary

ASR output can use:

```text
String
WordTimestamp
TextSegment
LanguageTag
```

without coupling the text runtime to a particular ASR engine.

---

# 167. Subtitle Integration

Timed subtitle text can use:

```text
String
LanguageTag
MediaTime
```

from 616.

---

# 168. Search

Unicode-aware search APIs:

```text
find
find_all
contains
replace
```

must have explicit comparison modes.

---

# 169. Search Modes

```text
Binary
CaseInsensitive
Canonical
LocaleAware
```

---

# 170. Regex Boundary

Regular expressions are not part of the Unicode core.

A later regex engine can consume UTF-8 strings and Unicode properties.

---

# 171. Text Tokenization Boundary

NLP tokenization is a higher-level layer.

Unicode word segmentation is provided by 617.

---

# 172. Text Security

Potentially dangerous characters may be detected:

```text
BidiControl
Invisible
Confusable
Deprecated
PrivateUse
```

---

# 173. Confusable Detection

Security tooling may expose Unicode confusable detection.

---

# 174. Bidi Security

Source/UI tooling can identify suspicious bidirectional controls.

---

# 175. Identifier Security

The compiler may restrict mixed-script identifiers or require explicit policy.

---

# 176. Normalization Security

Security-sensitive identifiers should use a documented normalization profile.

---

# 177. Spoof Detection

617 provides detection primitives but does not automatically reject all visually similar text.

---

# 178. Font Security

Fonts are treated as untrusted data.

Font parsing must be bounded and fuzz-tested.

---

# 179. Font Sandboxing

Untrusted application fonts may be parsed in a restricted provider process where required by platform policy.

---

# 180. Resource Limits

Limits include:

```text
max_font_size
max_glyph_count
max_glyph_atlas_size
max_text_layout_size
max_localization_resource_size
```

---

# 181. Text Layout Limits

A layout operation must not allocate unbounded memory from malicious input.

---

# 182. Streaming Text

Large text sources can be processed incrementally.

---

# 183. Text Reader

```text
TextReader
```

decodes UTF-8 incrementally from BOOTSTRAP-611 streams.

---

# 184. Text Writer

```text
TextWriter
```

encodes text to UTF-8.

---

# 185. Line Reader

```text
LineReader
```

supports:

```text
LF
CRLF
CR
```

with explicit normalization policy.

---

# 186. Newline Model

Internal text APIs use:

```text
LF
```

as the canonical logical newline.

---

# 187. Newline Conversion

File/network boundaries can explicitly convert newline style.

---

# 188. BOM Handling

Text readers can detect:

```text
UTF-8 BOM
UTF-16 BOM
UTF-32 BOM
```

at external boundaries.

The canonical runtime representation remains UTF-8.

---

# 189. Legacy Encoding Boundary

Legacy encodings such as:

```text
Windows-1252
Shift-JIS
GB18030
```

are optional provider functionality.

---

# 190. No Implicit Legacy Conversion

Axiom must not silently interpret bytes using a machine-local legacy code page.

---

# 191. Encoding Provider

```text
TextEncodingProvider
```

converts explicit encoding ↔ Unicode.

---

# 192. Locale Data

Locale data can be generated into compact binary tables.

---

# 193. Data Versioning

Unicode and locale database versions are recorded in runtime metadata.

---

# 194. Reproducible Formatting

For reproducible builds/tests, formatting can use a pinned locale-data version.

---

# 195. Platform Locale

Applications may request:

```text
system_default_locale()
```

but deterministic services should explicitly choose a locale.

---

# 196. Environment Independence

Core serialization/configuration must not depend on the host locale.

---

# 197. Serialization

AXBIN strings remain UTF-8.

Locale formatting must not alter serialized numeric representation.

---

# 198. Network Protocols

Protocol parsers should use explicit ASCII/UTF-8 rules rather than system locale.

---

# 199. Compiler Metadata

The compiler can generate:

```text
Unicode property tables
locale tables
message IDs
font metadata
shaping metadata
```

only when referenced.

---

# 200. Dead Stripping

A console application using only UTF-8 strings should not link:

```text
font rasterizer
text shaper
locale database
GPU glyph renderer
```

unless required.

---

# 201. Text ABI

The stable native ABI uses:

```text
UTF-8 pointer + length
```

only at explicit FFI boundaries.

---

# 202. Native FFI

Axiom FFI provides conversion helpers:

```text
String → Utf8Slice
Utf8Slice → String
```

with explicit ownership.

---

# 203. UTF-16 FFI

Platform APIs requiring UTF-16 receive generated temporary/platform buffers.

The conversion remains at the boundary.

---

# 204. Windows Boundary

Windows APIs can use UTF-16 internally through an adapter.

Applications remain UTF-8-first.

---

# 205. Apple Boundary

Apple text APIs use platform-native Unicode representations behind the adapter.

---

# 206. Android Boundary

Android Java/Kotlin APIs use UTF-16 at the boundary where necessary.

---

# 207. WASM Boundary

JavaScript strings are converted at the host boundary.

Repeated conversion should be avoided through cached views/handles.

---

# 208. Terminal Boundary

Terminal APIs use UTF-8 by default.

Terminal width remains separate from string length.

---

# 209. Text Width

A separate:

```text
DisplayWidth
```

API accounts for:

- wide characters;
- combining marks;
- emoji;
- terminal conventions.

---

# 210. Font Fallback Cache

Font fallback decisions can be cached by:

```text
script
language
codepoint range
font stack
```

---

# 211. Shaping Cache

Shaping results may be cached for immutable text/font/feature combinations.

---

# 212. Layout Cache

Layout cache keys include:

```text
text_hash
font
size
features
width
direction
locale
layout_options
```

---

# 213. Cache Safety

Caches are bounded by BOOTSTRAP-606 resource budgets.

---

# 214. Cache Invalidation

Changing:

```text
font
DPI
locale
Unicode version
font provider
```

invalidates affected cache entries.

---

# 215. Text Rendering Across Windows

A single `TextLayout` may be rendered into different surfaces if device-scale assumptions remain compatible.

---

# 216. Multi-Monitor

Rendering uses the target monitor's DPI/color characteristics from 615.

---

# 217. Color Emoji

Color emoji rendering must respect the target surface color space.

---

# 218. HDR Text

Text rendering can operate in HDR surfaces where supported, while preserving intended UI luminance policy.

---

# 219. Accessibility Font Scaling

Higher-level UI may request text scaling independently from window DPI.

---

# 220. Font Size

Font size is represented as a typed unit:

```text
FontSize
```

rather than raw integer pixels.

---

# 221. Typography Units

Support:

```text
Points
Pixels
DeviceIndependentUnits
Em
```

through explicit conversions.

---

# 222. Baseline Grid

Higher-level layout systems may align text to a baseline grid.

617 exposes accurate metrics for that purpose.

---

# 223. Text Decoration

Rendering supports:

```text
Underline
Strike
Overline
```

as layout/render metadata.

---

# 224. Decoration Position

Decoration geometry is derived from font metrics.

---

# 225. Text Transform

Optional layout transforms:

```text
scale
rotate
skew
```

are performed by graphics 615.

---

# 226. Rich Text Boundary

617 provides runs with style attributes:

```text
font
size
weight
color
features
language
```

but does not define a document editor.

---

# 227. Text Span

```text
TextSpan {
    start
    end
    style
}
```

---

# 228. Style Run

Adjacent spans with identical style may be coalesced.

---

# 229. Layout Performance

Large text layout must support incremental reflow.

---

# 230. Incremental Layout

Editing one line should not require relayout of an unrelated entire document where avoidable.

---

# 231. Paragraph Layout

Paragraphs are independent layout units when possible.

---

# 232. Multi-Paragraph Document

A higher-level document engine can compose multiple paragraph layouts.

---

# 233. Text Selection Across Runs

Selection uses logical source ranges, not glyph IDs.

---

# 234. Glyph Cluster Mapping

Clusters map:

```text
source byte range
→ glyph range
```

and support reverse mapping.

---

# 235. Cursor in Ligature

Cursor positions can exist between logical source characters even when the font renders them as one ligature.

---

# 236. Bidi Cursor

Cursor movement respects logical text order while display position follows visual layout.

---

# 237. Copy Selection

Copied text uses original logical Unicode text rather than reconstructed glyphs.

---

# 238. Font License Metadata

Package fonts may contain license metadata.

The package system can expose it for inspection.

---

# 239. Font Embedding

Applications may package licensed fonts explicitly.

The runtime does not assume every system font may be redistributed.

---

# 240. Font Package

AXPK can contain:

```text
font files
font metadata
license metadata
fallback rules
```

---

# 241. Font Trust

Application-bundled fonts can be verified through BOOTSTRAP-613/610 package signatures.

---

# 242. Localization Package

AXPK can contain:

```text
.axloc
```

resources per locale.

---

# 243. Locale Resource Selection

Package selection follows deterministic target locale rules.

---

# 244. Hot Locale Change

Applications may change locale at runtime.

Affected formatters/layouts can be invalidated.

---

# 245. Translation Reload

Development builds may reload localization resources.

Production builds can disable dynamic reload.

---

# 246. Locale Snapshot

Formatting uses an immutable locale snapshot.

Concurrent formatting does not depend on mutable global locale state.

---

# 247. Thread Safety

Unicode tables are immutable.

Font resources use concurrent-safe immutable metadata with explicit mutable caches.

---

# 248. No Global Locale

Axiom must not expose a mutable process-global locale that silently changes behavior across threads.

---

# 249. Per-Operation Locale

Formatting APIs accept an explicit locale or immutable locale context.

---

# 250. Per-Task Locale

Higher-level applications may attach locale context to a task through BOOTSTRAP-607.

---

# 251. Diagnostics

Text diagnostics expose:

```text
unicode_version
locale
font
script
direction
shaping_provider
```

when useful.

---

# 252. No Raw Text in Diagnostics

Large/private text content is not logged automatically.

---

# 253. Privacy

Text may contain sensitive personal information.

Diagnostic systems must therefore use:

```text
length
hash
classification
```

rather than automatically recording content.

---

# 254. Redaction

Applications can mark fields:

```text
@secret
@sensitive
```

and 602 handles redaction.

---

# 255. Localization Diagnostics

Missing translations are diagnostic events, not arbitrary exceptions unless strict mode is enabled.

---

# 256. Translation Testing

Automated validation checks:

- placeholder compatibility;
- plural completeness;
- malformed messages;
- missing translations;
- extra translations.

---

# 257. Pseudolocalization

Development tooling can generate pseudolocalized text to test layout expansion.

---

# 258. RTL Testing

Development tooling can force:

```text
RTL
```

to expose layout assumptions.

---

# 259. Unicode Test Suite

The implementation must test against relevant Unicode conformance data.

---

# 260. Grapheme Tests

Must include:

- combining marks;
- emoji ZWJ;
- regional indicators;
- variation selectors;
- Hangul;
- Indic sequences.

---

# 261. Bidi Tests

Must include mixed:

```text
Latin
Arabic
Hebrew
numbers
punctuation
```

---

# 262. Shaping Tests

Must include:

```text
Vietnamese
Arabic
Devanagari
Thai
Hebrew
Indic scripts
CJK
emoji
```

---

# 263. Font Tests

Must include:

- malformed fonts;
- variable fonts;
- missing glyphs;
- fallback;
- color glyphs;
- large fonts.

---

# 264. Fuzzing

Fuzz targets:

```text
UTF-8 decoder
Unicode normalization
Bidi
line breaker
font parser
OpenType parser
shaper
localization parser
number formatter/parser
```

---

# 265. Resource Fuzzing

Malicious text/font/localization resources must remain bounded.

---

# 266. Performance Benchmarks

Benchmark:

```text
ASCII strings
Vietnamese text
mixed-language text
emoji
CJK
Arabic
large documents
font fallback
shaping
layout
rasterization
```

---

# 267. Performance Target

Common ASCII operations should approach raw byte-processing performance.

Unicode-heavy operations should scale approximately linearly with input size.

---

# 268. Allocation Target

Repeated formatting/shaping/layout should support reusable buffers and caches.

---

# 269. Compiler Fast Path

The compiler may specialize:

```text
ASCII literals
UTF-8 literal validation
string concatenation
string length
```

---

# 270. Compile-Time UTF-8 Validation

String literals are validated at compile time.

---

# 271. Compile-Time String Storage

Immutable literals may be stored directly in read-only binary sections.

---

# 272. Literal Deduplication

Identical string literals may be merged.

---

# 273. UTF-8 Literal Metadata

Compiler metadata can include:

```text
byte_length
scalar_count
grapheme_count
```

when cheaply determinable.

---

# 274. Constant Folding

Pure Unicode operations may be constant-folded.

---

# 275. Compile-Time Localization

Typed localization IDs can be validated during compilation.

---

# 276. Resource Compiler

Axiom tooling includes:

```text
axlocc
```

for AXLOC compilation.

---

# 277. Font Resource Compiler

Optional:

```text
axfontc
```

can inspect/package fonts.

---

# 278. Text Inspection CLI

```text
axiom text inspect file
```

can report:

```text
encoding
Unicode version
scalar count
grapheme count
bidi classes
normalization
```

---

# 279. Font Inspection CLI

```text
axiom font inspect file
```

reports:

```text
families
faces
axes
glyph count
scripts
license metadata
```

---

# 280. Localization CLI

```text
axiom loc validate
axiom loc extract
axiom loc merge
```

---

# 281. AI-Friendly Metadata

The tooling can export deterministic machine-readable descriptions of:

```text
text resources
fonts
locales
message schemas
shaping requirements
```

---

# 282. AI Code Generation

Typed localization schemas can be consumed by AI tooling without parsing arbitrary source code.

---

# 283. Native API Example

```text
let text: String = "Xin chào Việt Nam"

let locale = Locale.parse("vi-VN")

let font = FontManager.find("Noto Sans")

let shaped = Shaper.shape(
    text,
    font,
    locale
)

let layout = TextLayout.build(
    shaped,
    width = 640
)

renderer.draw_text(layout)
```

---

# 284. Struct-Only Design

No class hierarchy is required:

```text
struct TextLayout {
    runs: Array<GlyphRun>
    bounds: Rect
}

fn TextLayout.measure(self) -> Size {
    ...
}
```

---

# 285. Provider Interface

Conceptually:

```text
trait FontProvider {
    fn enumerate(...)
    fn load(...)
}

trait ShaperProvider {
    fn shape(...)
}

trait RasterizerProvider {
    fn rasterize(...)
}
```

---

# 286. Static Dispatch

When provider type is known at compile time, dispatch should be statically optimized.

---

# 287. Dynamic Provider

Runtime-loaded providers use explicit dynamic interfaces.

---

# 288. Cross-Platform Layer

```text
Axiom Text API
       │
       ├── Unicode Core
       ├── Locale Data
       ├── Font Provider
       ├── Shaper Provider
       └── Rasterizer Provider
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
 Windows   Apple    Linux
 Android   WASM     Embedded
```

---

# 289. Relationship With 615

615 provides:

```text
Window
Surface
GPU
Texture
Render Pipeline
```

617 provides:

```text
Glyph
Glyph Atlas
Text Layout
Text Rendering Data
```

The two layers remain independently usable.

---

# 290. Relationship With 616

616 provides:

```text
MediaTime
Subtitle Track
Timed Metadata
```

617 provides:

```text
Text
Language
Font
Layout
```

Together they support subtitle rendering.

---

# 291. Relationship With 612

612 serializes:

```text
String
LanguageTag
Locale metadata
Localization schemas
```

using AXBIN.

---

# 292. Relationship With 613

613 packages:

```text
fonts
translations
text assets
```

and provides content-addressed storage.

---

# 293. Relationship With 611

611 supplies:

```text
TextReader
TextWriter
font files
localization files
```

---

# 294. Relationship With 603

Security capabilities cover:

```text
font loading
external resources
clipboard
system locale data
```

where applicable.

---

# 295. Relationship With 602

Diagnostics track:

```text
font fallback
missing glyph
localization miss
shaping failure
layout overflow
```

without leaking text content.

---

# 296. Relationship With 606

Resource budgets cover:

```text
font cache
glyph atlas
layout cache
locale database
document memory
```

---

# 297. Relationship With 607

Text shaping/layout may execute asynchronously for large documents.

The rendering thread must never block indefinitely on font loading.

---

# 298. Async Font Loading

A font can be:

```text
Requested
Loading
Ready
Failed
```

---

# 299. Rendering Placeholder

If a font is not ready, higher-level UI can choose:

```text
fallback font
placeholder
delay
```

rather than blocking the UI thread.

---

# 300. Font Loading Determinism

Applications requiring deterministic rendering may package exact fonts and disable system fallback.

---

# 301. Reproducible Rendering

A deterministic text-rendering profile specifies:

```text
font package
Unicode version
shaping provider
rasterizer
DPI
locale
```

---

# 302. Cross-Platform Visual Consistency

Exact glyph pixels are not guaranteed across rasterizers.

For pixel-identical output, applications must use a pinned font/rasterizer profile.

---

# 303. Text Snapshot

A layout snapshot can contain:

```text
text hash
font fingerprint
shaping result
layout result
```

without necessarily storing source text.

---

# 304. Cache Fingerprint

Text cache fingerprints include relevant versions to avoid stale rendering.

---

# 305. Memory Model

Text objects follow Axiom ownership rules.

No tracing GC is required.

---

# 306. Reference Model

Large immutable text/font resources may use explicit shared ownership mechanisms.

---

# 307. Mutation

Mutable text buffers have exclusive ownership.

---

# 308. Thread Safety

Immutable strings are safely shareable.

Mutable buffers require exclusive access or synchronization.

---

# 309. No Hidden Copies

Converting:

```text
StringView → String
```

allocates only when ownership is actually required.

---

# 310. UTF-8 FFI Performance

FFI can borrow UTF-8 data directly where the native API supports UTF-8.

---

# 311. Windows UTF-16 Optimization

Windows adapters should reuse conversion buffers where possible rather than allocate for every call.

---

# 312. WASM Optimization

Repeated JS↔Axiom text conversion should use persistent handles or shared linear-memory views where safe.

---

# 313. Embedded Profile

Minimal embedded builds may omit:

```text
locale
font discovery
complex shaping
GPU rasterization
```

while retaining UTF-8 core.

---

# 314. Server Profile

Server builds may omit:

```text
font rasterization
windowing
GPU text
```

while retaining:

```text
Unicode
locale
formatting
normalization
```

---

# 315. GUI Profile

GUI builds enable:

```text
fonts
shaping
layout
glyph rendering
locale
accessibility metadata
```

---

# 316. Document Profile

Document systems enable:

```text
large text buffers
line breaking
layout
font embedding
localization
```

---

# 317. Game Profile

Games may use:

```text
UTF-8
font packages
shaping
glyph atlas
GPU rendering
localization
```

without system font discovery.

---

# 318. AI/ML Profile

AI applications can use:

```text
UTF-8
Unicode normalization
segmentation
language tags
streaming text
```

without linking graphical typography.

---

# 319. TTS/ASR Integration

617 intentionally provides the canonical text representation needed by future:

```text
TTS
ASR
phoneme/token
subtitle
voice
```

systems.

It does not prescribe a phoneme representation.

---

# 320. Multilingual Invariant

An application must be able to process mixed-language UTF-8 text without manually converting:

```text
Vietnamese
English
Chinese
Japanese
Arabic
```

into separate string systems.

---

# 321. Core Invariants

1. Axiom `String` is valid UTF-8.
2. Binary bytes are not strings.
3. Byte, scalar, grapheme and glyph are distinct.
4. String equality is byte equality by default.
5. Unicode normalization is explicit.
6. Locale is explicit/immutable.
7. No mutable global locale.
8. Cursor movement uses logical text boundaries.
9. Glyph IDs are font-local.
10. Glyphs are never treated as Unicode characters.
11. Shaping preserves source cluster mappings.
12. Bidi behavior follows Unicode semantics.
13. Font fallback is explicit and deterministic under a pinned profile.
14. Malformed fonts cannot escape parser boundaries.
15. Large text processing is bounded.
16. UTF-16 is an FFI boundary, not the Axiom canonical model.
17. Localization formatting cannot execute arbitrary code.
18. Raw text is excluded from ordinary diagnostics.
19. Text caches are resource-budgeted.
20. No garbage collector is required.
21. GPU rendering is optional.
22. Server builds can exclude typography rendering.
23. Unicode-heavy operations remain approximately linear.
24. Protocol parsing must not depend on locale.
25. Reproducible rendering requires pinned font/rasterizer/data versions.

---

# 322. Acceptance Criteria

### Unicode

1. UTF-8 validation.
2. Incremental UTF-8 decoding.
3. Unicode scalar iteration.
4. Grapheme iteration.
5. Unicode properties.
6. Unicode normalization.
7. Unicode case mapping.
8. Case folding.
9. Unicode word segmentation.
10. Sentence segmentation.
11. Line breaking.
12. Unicode version reporting.
13. Vietnamese combining marks.
14. Emoji sequences.
15. Variation selectors.
16. ZWJ sequences.
17. CJK.
18. Arabic.
19. Indic.
20. Hangul.

### String

21. UTF-8 String.
22. StringView.
23. ByteSlice.
24. ScalarSlice.
25. GraphemeSlice.
26. StringBuilder.
27. SSO.
28. ASCII fast path.
29. Stable hashing.
30. explicit normalization equality.

### Locale

31. Locale parsing.
32. LanguageTag.
33. Script.
34. Region.
35. Locale negotiation.
36. fallback chain.
37. number formatting.
38. currency formatting.
39. date formatting.
40. time formatting.
41. calendar boundary.
42. relative time.
43. plural rules.
44. collation.
45. no mutable global locale.

### Localization

46. AXLOC.
47. message IDs.
48. typed message arguments.
49. plural messages.
50. missing-translation detection.
51. placeholder validation.
52. fallback.
53. pseudolocalization.
54. runtime locale switching.
55. resource versioning.

### Fonts

56. font discovery.
57. font loading.
58. font family.
59. font face.
60. variable fonts.
61. font axes.
62. font metrics.
63. glyph metrics.
64. font fallback.
65. font packages.
66. font validation.
67. malformed-font fuzzing.
68. color fonts.

### Shaping

69. glyph mapping.
70. glyph clusters.
71. OpenType features.
72. ligatures.
73. kerning.
74. contextual shaping.
75. Vietnamese shaping.
76. Arabic shaping.
77. Indic shaping.
78. Thai shaping.
79. Hebrew.
80. CJK.
81. emoji shaping.
82. RTL.
83. mixed LTR/RTL.
84. cluster-to-source mapping.

### Layout

85. TextLayout.
86. line wrapping.
87. alignment.
88. justification.
89. ellipsis.
90. measurement.
91. hit testing.
92. cursor movement.
93. selection.
94. grapheme-aware deletion.
95. bidi-aware caret.
96. incremental layout.
97. large-document support.

### Rendering

98. glyph atlas.
99. glyph cache.
100. GPU text rendering.
101. CPU fallback.
102. color glyph rendering.
103. DPI scaling.
104. subpixel metrics.
105. hinting boundary.
106. text decorations.
107. multi-monitor DPI.
108. HDR text boundary.

### Security

109. font sandbox boundary.
110. malicious font handling.
111. text resource bounds.
112. localization resource bounds.
113. bidi security detection.
114. confusable detection.
115. sensitive text diagnostics.
116. provider capability enforcement.

### Compiler

117. UTF-8 literal validation.
118. literal deduplication.
119. source byte offsets.
120. grapheme-aware diagnostics.
121. compile-time Unicode operations.
122. localization validation.
123. dead stripping.
124. AI-readable text metadata.

### Integration

125. 611 TextReader/TextWriter.
126. 612 AXBIN strings.
127. 613 font/localization packaging.
128. 615 GPU text bridge.
129. 616 subtitle/media integration.
130. 602 diagnostics.
131. 603 security.
132. 606 resource quotas.
133. 607 async font/layout loading.

### Testing

134. Unicode conformance tests.
135. normalization tests.
136. grapheme tests.
137. bidi tests.
138. shaping tests.
139. font fuzzing.
140. localization fuzzing.
141. layout fuzzing.
142. cache stress tests.
143. large-document tests.
144. cross-platform FFI tests.
145. deterministic rendering tests.

---

# 323. Final Architecture

```text
                         AXIOM APPLICATION
                                │
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
           GUI              DOCUMENT             AI/TEXT
             │                  │                  │
             └──────────────────┼──────────────────┘
                                ▼
                         BOOTSTRAP-617
 ┌─────────────────────────────────────────────────────────┐
 │                                                         │
 │ Unicode Core                                            │
 │ ├─ UTF-8                                                │
 │ ├─ Scalars                                              │
 │ ├─ Graphemes                                            │
 │ ├─ Normalization                                        │
 │ ├─ Properties                                           │
 │ └─ Segmentation                                         │
 │                                                         │
 │ Internationalization                                   │
 │ ├─ Locale                                               │
 │ ├─ Collation                                            │
 │ ├─ Number/Date Formatting                               │
 │ ├─ Plural Rules                                         │
 │ └─ Localization / AXLOC                                │
 │                                                         │
 │ Typography                                              │
 │ ├─ Font                                                 │
 │ ├─ Fallback                                              │
 │ ├─ Shaping                                              │
 │ ├─ Bidi                                                 │
 │ ├─ GlyphRun                                             │
 │ └─ TextLayout                                           │
 │                                                         │
 │ Rendering                                               │
 │ ├─ Glyph Atlas                                          │
 │ ├─ Rasterizer                                           │
 │ ├─ GPU Text                                             │
 │ └─ CPU Fallback                                         │
 │                                                         │
 └──────────────────────┬──────────────────────────────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
      615             616              612/613
    Graphics          Media          Data/Package
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                  Native Platform
```

Cross-cutting:

```text
600 State / Recovery
602 Diagnostics
603 Security
604 IPC
605 Supervision
606 Resource Governor
607 Scheduler / Async
608 Synchronization
609 Networking
610 Cryptography
611 Storage / VFS
612 Serialization
613 Package / CAS
614 Device
615 Graphics
616 Media
```

---

# 324. Architectural Decision

BOOTSTRAP-617 establishes a strict **UTF-8-first, Unicode-correct text architecture**.

The key separation is:

```text
UTF-8 bytes
    ↓
Unicode scalars
    ↓
Grapheme clusters
    ↓
Bidi/script analysis
    ↓
Font selection
    ↓
Shaping
    ↓
Glyph runs
    ↓
Text layout
    ↓
Glyph rendering
    ↓
615 GPU / display
```

This avoids one of the most common architectural mistakes in language/runtime design: treating strings, characters, glyphs and visible characters as the same abstraction.

It also gives Axiom a proper foundation for **Vietnamese + English mixed text**, multilingual GUI, subtitles, documents, AI text processing, TTS/ASR integration and future internationalized applications without making UTF-16 or a particular operating system's text model part of the language itself.

---

# 325. Task Completion

**BOOTSTRAP-617 — COMPLETE**

**Next queued task: BOOTSTRAP-618 — Native Input, Keyboard, Mouse, Touch, Pen, Gamepad, HID, Gesture & Interaction Runtime 5.0**
:::