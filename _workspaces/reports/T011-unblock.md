## Tóm tắt
Lỗi sai lệch offset lexer trong 14 test của `tests/lex` được báo cáo trong T011 không phải do code của lexer bị lỗi. Nguyên nhân là các file `.tokens` mẫu (golden tests) trước đây được tạo ra trên môi trường Windows với line ending CRLF, nhưng thuộc tính `.gitattributes` quy định chúng phải là LF (`eol=lf`). Khi QA chạy test trên môi trường chuẩn (có line ending LF), các byte offset bị lệch đi 1 byte cho mỗi dòng. Vì `tests/lex` nằm ngoài phạm vi path cho phép của T011, agent trước không thể chạy `--bless` để sửa.
Giải pháp là chạy `python tools/axtest.py --bless lex` với các file đã được normalize sang LF để cập nhật đúng offset.

## Files changed
- tests/lex/L01_range.tokens
- tests/lex/L02_tuple_index.tokens
- tests/lex/L03_float.tokens
- tests/lex/L04_shl.tokens
- tests/lex/L05_generics.tokens
- tests/lex/L06_char_range.tokens
- tests/lex/L07_label.tokens
- tests/lex/L08_byte_literal.tokens
- tests/lex/L09_newlines.tokens
- tests/lex/L10_attr.tokens
- tests/lex/L11_comments.tokens
- tests/lex/L12_string.tokens
- tests/lex/L13_underscore.tokens
- tests/lex/L14_self.tokens
