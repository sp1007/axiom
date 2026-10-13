with open('bootstrap/axiom0/src/syntax/parse.c', 'r', encoding='utf-8') as f:
    text = f.read()

# wait, I can just write a quick C program to printf the exact string my macro generates for Point.
c_prog = '''
#include <stdio.h>
#include <string.h>

int main() {
    char body[2048] = {0};
    const char *struct_name = "Point";
    // x
    char cbuf[128];
    snprintf(cbuf, sizeof(cbuf), "let c = self.%s.cmp(view(other.%s)); match c { Ordering.Equal => {}, _ => return c, }; ", "x", "x");
    strcat(body, cbuf);
    // y
    snprintf(cbuf, sizeof(cbuf), "let c = self.%s.cmp(view(other.%s)); match c { Ordering.Equal => {}, _ => return c, }; ", "y", "y");
    strcat(body, cbuf);
    
    strcat(body, "Ordering.Equal");

    char buf[4096];
    snprintf(buf, sizeof(buf), "impl Ord for %s { fn cmp(self: view<%s>, other: view<%s>) -> Ordering { %s } }", struct_name, struct_name, struct_name, body);

    printf("%s\\n", buf);
    printf("Span 102..106: %.*s\\n", 4, buf + 102);
    return 0;
}
'''
with open('test_macro.c', 'w') as f: f.write(c_prog)
