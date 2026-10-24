PE32+ and ELF linkers and startup stubs. Layer: above obj (depends on objmodel, kernel, diag; never on MIR/HIR).

Symbol resolution (ADR-0035 section 2): a relocation whose target symbol is defined in the same object
(SectionNumber > 0) is bound by that symbol's table index, whatever its name or storage class; only
`IMAGE_SYM_CLASS_EXTERNAL` definitions enter the global name table (a second EXTERNAL definition is
`AX_LINK_DUPLICATE_SYMBOL`); STATIC symbols (`.Lstr.<f>.<k>`, `.Lpanic.<n>`) never do; an undefined
EXTERNAL reference resolves by name. The Axiom port (`compiler/link`) behaves identically.
