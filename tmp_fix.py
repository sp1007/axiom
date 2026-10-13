import sys

content = open("bootstrap/axiom0/src/syntax/parse.c", "r", encoding="utf-8").read()

content = content.replace("self: &Self", "self: view Self")
content = content.replace("self: &mut Self", "self: mut_view Self")
content = content.replace("state: &mut H", "state: mut_view H")
content = content.replace("Ordering::Equal", "Ordering.Equal")
content = content.replace("&other", "other") # Wait, actually we can just pass views by doing `other` or something if it expects a view?

# Let's just fix the python script to generate correct Axiom syntax!
