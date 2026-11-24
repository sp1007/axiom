/* T459: C side of the Windows x64 floating-point ABI oracle. Calls the Axiom DLL exports with the
   non-volatile registers XMM6..XMM15 holding known 128-bit patterns and checks them afterwards. */
#include <stdio.h>
#include <string.h>
#include <windows.h>

typedef double (*mix_fn)(int, double, unsigned short, float, double);
typedef float (*stack_fn)(float, long long, double, float, float, int, double, float);
typedef double (*cb1_fn)(double);
typedef float (*cbf_fn)(float, float, int, float, float, double);

static int failures = 0;
static unsigned char pat[10][16], after[10][16];

static void clobber_volatile(void) {
    __asm__ volatile("pcmpeqd %%xmm0,%%xmm0\n\tpcmpeqd %%xmm1,%%xmm1\n\tpcmpeqd %%xmm2,%%xmm2\n\t"
                     "pcmpeqd %%xmm3,%%xmm3\n\tpcmpeqd %%xmm4,%%xmm4\n\tpcmpeqd %%xmm5,%%xmm5"
                     ::: "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5");
}

static void fail(const char *what) {
    printf("FAIL %s\n", what);
    failures++;
}

static double cb_mix(int a, double b, unsigned short c, float d, double e) {
    if (a != 3 || b != 1.5 || c != 7 || d != 0.25f || e != 0.5) fail("cb_mix args");
    return a + b + c + d + e;
}

static float cb_f32(float a, float b, int c, float d, float e, double f) {
    if (a != 1.5f || b != 2.5f || c != 9 || d != 3.0f || e != 1.0f || f != 6.25) fail("cb_f32 args");
    return a + b + c + d + e + (float)f;
}

static double cb1(double x) {
    volatile double v = x * 0.5 + 1.0;
    clobber_volatile();
    return v;
}

#define LOAD(n) "movups " #n "*16-96(%%rsi),%%xmm" #n "\n\t"
#define SAVE(n) "movups %%xmm" #n "," #n "*16-96(%%rdi)\n\t"

/* Calls thunk with XMM6..XMM15 = pat and compares the registers with pat after it returns. */
static void with_patterns(void (*thunk)(void), const char *name) {
    void *fn = (void *)thunk;
    void *s = pat, *d = after;
    memset(after, 0, sizeof after);
    __asm__ volatile(
        LOAD(6) LOAD(7) LOAD(8) LOAD(9) LOAD(10) LOAD(11) LOAD(12) LOAD(13) LOAD(14) LOAD(15)
        "movq %%rsp,%%rbx\n\tandq $-16,%%rsp\n\tsubq $64,%%rsp\n\t"
        "call *%%rax\n\tmovq %%rbx,%%rsp\n\t"
        SAVE(6) SAVE(7) SAVE(8) SAVE(9) SAVE(10) SAVE(11) SAVE(12) SAVE(13) SAVE(14) SAVE(15)
        : "+a"(fn), "+S"(s), "+D"(d)
        :: "rbx", "rcx", "rdx", "r8", "r9", "r10", "r11", "memory", "cc", "xmm0", "xmm1", "xmm2", "xmm3",
           "xmm4", "xmm5", "xmm6", "xmm7", "xmm8", "xmm9", "xmm10", "xmm11", "xmm12", "xmm13", "xmm14", "xmm15");
    for (int i = 0; i < 10; i++) {
        if (memcmp(pat[i], after[i], 16) != 0) {
            printf("FAIL %s clobbered xmm%d\n", name, i + 6);
            failures++;
        }
    }
}

static mix_fn ax_mix;
static stack_fn ax_stack;
static double (*ax_call_mix)(mix_fn);
static float (*ax_call_f32)(cbf_fn, float);
static double (*ax_live)(cb1_fn, double);
static double (*ax_pressure)(double, double);
static volatile double rd;
static volatile float rf;

/* A control thunk that does clobber XMM6: proves that the check can fail. */
static void t_clobber(void) { __asm__ volatile("pcmpeqd %%xmm6,%%xmm6" :::); }
static void t_mix(void) { rd = ax_mix(3, 1.5, 7, 0.25f, 0.5); }
static void t_stack(void) { rf = ax_stack(1.5f, -2, 3.25, 4.5f, -5.75f, 6, 7.125, 8.5f); }
static void t_call_mix(void) { rd = ax_call_mix(cb_mix); }
static void t_call_f32(void) { rf = ax_call_f32(cb_f32, 1.5f); }
static void t_live(void) { rd = ax_live(cb1, 2.75); }
static void t_pressure(void) { rd = ax_pressure(3.5, -1.25); }

static void ckd(const char *n, double want) {
    double g = rd;
    if (g != want) { printf("FAIL %s got %a want %a\n", n, g, want); failures++; }
}

static void ckf(const char *n, float want) {
    float g = rf;
    if (g != want) { printf("FAIL %s got %a want %a\n", n, g, want); failures++; }
}

static double c_live(double x) {
    double a = x + 1.0, b = x * 2.0, c = x - 3.0, d = x / 4.0;
    return (a * b - c * d) + (a + b) * (c + d) - ((a - d) * (b - c) + cb1(x)) * ((a + c) - (b * d) + cb1(a));
}

static double c_pressure(double x, double y) {
    return ((x + y) * (x - y) + ((x * y) - (x / y)) * ((x + 1.0) * (y + 2.0) - ((x - 3.0) * (y - 4.0) +
        ((x + 5.0) / (y + 6.0)) * ((x * 7.0) - (y * 8.0) * ((x + 9.0) - (y / 10.0))))));
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    HMODULE h = LoadLibraryA(argv[1]);
    if (!h) { printf("FAIL LoadLibrary\n"); return 1; }
    ax_mix = (mix_fn)(void *)GetProcAddress(h, "ax_mix");
    ax_stack = (stack_fn)(void *)GetProcAddress(h, "ax_stack");
    ax_call_mix = (double (*)(mix_fn))(void *)GetProcAddress(h, "ax_call_mix");
    ax_call_f32 = (float (*)(cbf_fn, float))(void *)GetProcAddress(h, "ax_call_f32");
    ax_live = (double (*)(cb1_fn, double))(void *)GetProcAddress(h, "ax_live");
    ax_pressure = (double (*)(double, double))(void *)GetProcAddress(h, "ax_pressure");
    if (!ax_mix || !ax_stack || !ax_call_mix || !ax_call_f32 || !ax_live || !ax_pressure) {
        printf("FAIL GetProcAddress\n");
        return 1;
    }
    for (int i = 0; i < 10; i++)
        for (int j = 0; j < 16; j++) pat[i][j] = (unsigned char)(17 * i + 31 * j + 5);
    with_patterns(t_clobber, "control");
    if (failures != 1) { printf("FAIL control check did not detect the xmm6 clobber\n"); return 1; }
    printf("CONTROL ok\n");
    failures = 0;
    with_patterns(t_mix, "ax_mix");
    ckd("ax_mix", 3 * 1000.0 + 150.0 + 70.0 + 0.25 + 0.0625);
    with_patterns(t_stack, "ax_stack");
    ckf("ax_stack", 1.5f + -2.0f * 2.0f + 3.25f * 3.0f + 4.5f * 5.0f + -5.75f * 7.0f + 6.0f * 11.0f +
                    7.125f * 13.0f + 8.5f * 17.0f);
    with_patterns(t_call_mix, "ax_call_mix");
    ckd("ax_call_mix", 3 + 1.5 + 7 + 0.25 + 0.5 + 1.0);
    with_patterns(t_call_f32, "ax_call_f32");
    ckf("ax_call_f32", (1.5f + 2.5f + 9 + 3.0f + 1.0f + 6.25f) * 2.0f);
    with_patterns(t_live, "ax_live");
    ckd("ax_live", c_live(2.75));
    with_patterns(t_pressure, "ax_pressure");
    ckd("ax_pressure", c_pressure(3.5, -1.25));
    if (failures) return 1;
    printf("XMM-INTEROP ok\n");
    return 0;
}
