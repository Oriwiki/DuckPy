from NamuMarkParser import NamuMarkParser

input = """
[목차]

= 가 =
== 나 ==
=== 다 ===
= 마 =
"""

title = ""
#NamuMarkParser().parse(input, title)
print(NamuMarkParser().parse(input, title))
