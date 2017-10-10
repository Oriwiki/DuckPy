from NamuMarkParser import NamuMarkParser

input = """
[목차]

== 가나다 ==
마바사

=== 하하하하 ===
자두

== 바바바 ==
멍멍
"""

title = ""
print(NamuMarkParser().parse(input, title))
