#!/usr/bin/env python3
"""Hand-built COFF objects for the local-symbol linking test (T147, ADR-0035 section 2).

The bytes are written here from the Microsoft PE/COFF specification (file header, section headers,
relocations, symbol table, string table); neither axiom0 nor the Axiom port produced them.

local_symbols.obj
  .rdata  (24 bytes)   [0] = 3      [8] = 5      [16] = 9
  symbols (index)      0  .Lk   STATIC    .rdata+0      (A)
                       1  fa    EXTERNAL  .text         movzx eax, byte [rip + .Lk#0] ; ret
                       2  .Lk   STATIC    .rdata+8      (B)  -- same NAME as symbol 0
                       3  fb    EXTERNAL  .text         movzx eax, byte [rip + .Lk#2] ; ret
                       4  ext_k EXTERNAL  .rdata+16     (E)
                       5  main  EXTERNAL  .text         exit code = fa() + 4 * fb() + 16 * ext_k
  Every relocation names its target by symbol INDEX; resolving the two `.Lk` references by name
  would give both functions the first symbol's byte. Exit code if every reference resolves to its
  own symbol: 3 + 4 * 5 + 16 * 9 = 167. If fb read A instead: 3 + 4 * 3 + 144 = 159.

dup_ext.obj           defines EXTERNAL `ext_k` again (linking both must fail: duplicate symbol).

Usage: gen_local_symbols_obj.py <out_dir>   (writes both objects)
"""

import os
import struct
import sys

EXPECTED_EXIT_CODE = 167

IMAGE_FILE_MACHINE_AMD64 = 0x8664
IMAGE_SYM_CLASS_EXTERNAL = 2
IMAGE_SYM_CLASS_STATIC = 3
IMAGE_REL_AMD64_REL32 = 4
SCN_CODE_X16_RX = 0x60500020   # CNT_CODE | ALIGN_16BYTES | MEM_EXECUTE | MEM_READ
SCN_DATA_X8_R = 0x40400040     # CNT_INITIALIZED_DATA | ALIGN_8BYTES | MEM_READ


def sym_record(name, value, section, storage_class, sym_type=0):
    raw = name.encode("ascii")
    assert len(raw) <= 8, "long names would need the string table"
    return struct.pack("<8sIhHBB", raw.ljust(8, b"\0"), value, section, sym_type, storage_class, 0)


def section_header(name, size, raw_ptr, reloc_ptr, nrelocs, characteristics):
    return struct.pack("<8sIIIIIIHHI", name.ljust(8, b"\0"), 0, 0, size, raw_ptr, reloc_ptr, 0,
                       nrelocs, 0, characteristics)


def reloc(offset, sym_index):
    return struct.pack("<IIH", offset, sym_index, IMAGE_REL_AMD64_REL32)


def build_coff(sections, symbols):
    """sections: list of (name, data, relocs[(offset, sym_index)], characteristics);
    symbols: list of packed 18-byte records."""
    header_size = 20 + 40 * len(sections)
    off = header_size
    layout = []
    for (_n, data, relocs, _c) in sections:
        raw_ptr = off if data else 0
        off += len(data)
        layout.append(raw_ptr)
    reloc_ptrs = []
    for (_n, _d, relocs, _c) in sections:
        reloc_ptrs.append(off if relocs else 0)
        off += 10 * len(relocs)
    sym_ptr = off
    out = struct.pack("<HHIIIHH", IMAGE_FILE_MACHINE_AMD64, len(sections), 0, sym_ptr, len(symbols), 0, 0)
    for i, (n, data, relocs, c) in enumerate(sections):
        out += section_header(n.encode("ascii"), len(data), layout[i], reloc_ptrs[i], len(relocs), c)
    for (_n, data, _r, _c) in sections:
        out += data
    for (_n, _d, relocs, _c) in sections:
        for (o, idx) in relocs:
            out += reloc(o, idx)
    assert len(out) == sym_ptr
    out += b"".join(symbols)
    out += struct.pack("<I", 4)   # empty string table: just its own size
    return out


def build_local_symbols_obj():
    # .text, 16-byte aligned functions
    fa = bytes([0x0F, 0xB6, 0x05, 0, 0, 0, 0, 0xC3])            # movzx eax, byte [rip+d32] ; ret
    fb = bytes([0x0F, 0xB6, 0x05, 0, 0, 0, 0, 0xC3])
    fa_off, fb_off, main_off = 0, 16, 32
    main = bytes([
        0x53,                                # push rbx
        0x48, 0x83, 0xEC, 0x20,              # sub rsp, 32
        0xE8, 0, 0, 0, 0,                    # call fa            (reloc at +6)
        0x89, 0xC3,                          # mov ebx, eax
        0xE8, 0, 0, 0, 0,                    # call fb            (reloc at +13)
        0xC1, 0xE0, 0x02,                    # shl eax, 2
        0x01, 0xC3,                          # add ebx, eax
        0x0F, 0xB6, 0x05, 0, 0, 0, 0,        # movzx eax, byte [rip+d32] (ext_k, reloc at +25)
        0xC1, 0xE0, 0x04,                    # shl eax, 4
        0x01, 0xD8,                          # add eax, ebx
        0x48, 0x83, 0xC4, 0x20,              # add rsp, 32
        0x5B,                                # pop rbx
        0xC3,                                # ret
    ])
    text = fa.ljust(16, b"\xCC") + fb.ljust(16, b"\xCC") + main
    text_relocs = [
        (fa_off + 3, 0),            # fa  -> symbol 0 (.Lk, .rdata+0)
        (fb_off + 3, 2),            # fb  -> symbol 2 (.Lk, .rdata+8)
        (main_off + 6, 1),          # call fa
        (main_off + 13, 3),         # call fb
        (main_off + 25, 4),         # ext_k
    ]
    rdata = bytearray(24)
    rdata[0] = 3
    rdata[8] = 5
    rdata[16] = 9
    symbols = [
        sym_record(".Lk", 0, 2, IMAGE_SYM_CLASS_STATIC),
        sym_record("fa", fa_off, 1, IMAGE_SYM_CLASS_EXTERNAL, 0x20),
        sym_record(".Lk", 8, 2, IMAGE_SYM_CLASS_STATIC),
        sym_record("fb", fb_off, 1, IMAGE_SYM_CLASS_EXTERNAL, 0x20),
        sym_record("ext_k", 16, 2, IMAGE_SYM_CLASS_EXTERNAL),
        sym_record("main", main_off, 1, IMAGE_SYM_CLASS_EXTERNAL, 0x20),
    ]
    return build_coff([(".text", text, text_relocs, SCN_CODE_X16_RX),
                       (".rdata", bytes(rdata), [], SCN_DATA_X8_R)], symbols)


def build_dup_ext_obj():
    rdata = bytes([7, 0, 0, 0, 0, 0, 0, 0])
    symbols = [sym_record("ext_k", 0, 1, IMAGE_SYM_CLASS_EXTERNAL)]
    return build_coff([(".rdata", rdata, [], SCN_DATA_X8_R)], symbols)


def main():
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    for name, data in (("local_symbols.obj", build_local_symbols_obj()), ("dup_ext.obj", build_dup_ext_obj())):
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(data)


if __name__ == "__main__":
    main()
