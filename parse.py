from pyparsing import Word, srange, alphas, QuotedString
from urllib.parse   import quote
import re

string = alphas + srange(r"[\0xac00-\0xd7a3]") + " "
nowiki = []

def text_foramting(text):
    bold = QuotedString("'''")
    italic = QuotedString("''")
    strike1 = QuotedString("~~")
    strike2 = QuotedString("--")
    under = QuotedString("__")
    super = QuotedString("^^")
    sub = QuotedString(",,")

    for i in bold.searchString(text):
        for n in i:
            text = text.replace("'''" + n + "'''", "<strong>" + n + "</strong>")

    for i in italic.searchString(text):
        for n in i:
            text = text.replace("''" + n + "''", "<em>" + n + "</em>")
           
    for i in strike1.searchString(text):
        for n in i:
            text = text.replace("~~" + n + "~~", "<del>" + n + "</del>")
            
    for i in strike2.searchString(text):
        for n in i:
            text = text.replace("--" + n + "--", "<del>" + n + "</del>")       

    for i in under.searchString(text):
        for n in i:
            text = text.replace("__" + n + "__", "<u>" + n + "</u>")       
            
    for i in super.searchString(text):
        for n in i:
            text = text.replace("^^" + n + "^^", "<sup>" + n + "</sup>")       
            
    for i in sub.searchString(text):
        for n in i:
            text = text.replace(",," + n + ",,", "<sub>" + n + "</sub>")
    
    return text
                
def text_sizing(text):
    greet = QuotedString("{{{+", endQuoteChar="}}}")
    
    for i in greet.searchString(text):
        for n in i:
            n_split = n.split(" ", 1)
            if 1 <= int(n_split[0]) <= 5:
                text = text.replace("{{{+" + n + "}}}", '<span class="wiki-size size-' + n_split[0] + '">' + n_split[1] + '</span>')
    return text

def text_coloring(text):
    greet = QuotedString("{{{#", endQuoteChar="}}}")
    for i in greet.searchString(text):
        for n in i:
            n_split = n.split(" ", 1)
            # hex 코드 구별
            if re.search(r'^(?:[0-9a-fA-F]{3}){1,2}$', n_split[0]):
                text = text.replace("{{{#" + n + "}}}", '<span class="wiki-color" style="color: #' + n_split[0] + '">' + n_split[1] + '</span>')
            else:
                text = text.replace("{{{#" + n + "}}}", '<span class="wiki-color" style="color: ' + n_split[0] + '">' + n_split[1] + '</span>')
    return text

def text_nowiki(text):
    greet = QuotedString("{{{", endQuoteChar="}}}")
    for i in greet.searchString(text):
        for n in i:
            if n.startswith(('#', '+')):
                return text
            text = text.replace("{{{" + n + "}}}", "<nowiki" + str(len(nowiki)) + " />")
            nowiki.append(n)
    return text

def text_nowiki_print(text):
    i = 0
    while i <= len(nowiki) - 1:
        text = text.replace("<nowiki" + str(i) + " />", "<code>" + nowiki[i] + "</code>")
        i += 1
    return text
    
def text_inlink(text):
    greet = QuotedString("[[", endQuoteChar="]]")
    for i in greet.searchString(text):
        for n in i:
            n_split = n.split("|", 1)
            if len(n_split) == 1:
                text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal" href="/w/' + quote(n) + '" title="' + n + '">' + n + '</a>')
            elif len(n_split) == 2:
                text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal" href="/w/' + quote(n_split[0]) + '" title="' + n_split[0] + '">' + n_split[1] + '</a>')
    return text
    
    
text = "{{{''거짓말!!'' }}} 하지만 [[사실|거짓말]][[쟁이!]]"
text = text_nowiki(text)         
text = text_foramting(text)
text = text_sizing(text)
text = text_coloring(text)
text = text_inlink(text)

text = text_nowiki_print(text)
print(text)
