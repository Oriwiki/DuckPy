from pyparsing import Word, srange, alphas, QuotedString
from urllib.parse   import quote
import re
import time
from datetime import datetime

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
            elif n_split[0].startswith("!") == False:
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
    
def text_link(text):
    greet = QuotedString("[[", endQuoteChar="]]")
    for i in greet.searchString(text):
        for n in i:
            n_split = n.split("|", 1)
            ex_link = False
            self_link = False
            if n.startswith("http://"):
                ex_link = True
            elif n.startswith("#"):
                self_link = True
            
            if len(n_split) == 1:
                if ex_link == True:
                    text = text.replace("[[" + n + "]]", '<a class="wiki-link-external" href="' + n + '" target="_blank" rel="noopener" title="' + n + '">' + n + '</a>')
                elif self_link == True:
                    text = text.replace("[[" + n + "]]", '<a class="wiki-self-link" href="' + quote(n, '#') + '" title="' + n + '">' + n + '</a>')
                else:
                    text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal" href="/w/' + quote(n, '#') + '" title="' + n + '">' + n + '</a>')
            elif len(n_split) == 2:
                if ex_link == True:
                    text = text.replace("[[" + n + "]]", '<a class="wiki-link-external" href="' + n_split[0] + '" target="_blank" rel="noopener" title="' + n_split[0] + '">' + n_split[1] + '</a>')
                elif self_link == True:
                    text = text.replace("[[" + n + "]]", '<a class="wiki-self-link" href="' + quote(n_split[0], '#') + '" title="' + n_split[0] + '">' + n_split[1] + '</a>')
                else:
                    text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal" href="/w/' + quote(n_split[0], '#') + '" title="' + n_split[0] + '">' + n_split[1] + '</a>')
    return text
    
def text_anchor(text):
    greet = QuotedString("[anchor(", endQuoteChar=")]")
    for i in greet.searchString(text):
        for n in i:
            text = text.replace("[anchor(" + n + ")]", '<a id="' + n + '"></a>')
    return text
    
def text_youtube(text):
    greet = QuotedString("[youtube(", endQuoteChar=")]")
    for i in greet.searchString(text):
        for n in i:
            n_split = n.split(",")
            if len(n_split) == 1:
                text = text.replace("[youtube(" + n + ")]", '<iframe class="wiki-youtube" allowfullscreen="" src="//www.youtube.com/embed/' + n + '" width="640" height="360" frameborder="0"></iframe>')
            elif len(n_split) > 1:
                width = "640"
                height = "360"
                for a in n_split:
                    a_split = a.split("=")
                    if a_split[0] == "width":
                        width = a_split[1]
                    elif a_split[0] == "height":
                        height = a_split[1]
                text = text.replace("[youtube(" + n + ")]", '<iframe class="wiki-youtube" allowfullscreen="" src="//www.youtube.com/embed/' + n_split[0] + '" width="' + width + '" height="' + height + '" frameborder="0"></iframe>')
    return text
    
def text_macro(text):
    now = time.localtime()
    s = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    text = text.replace('[date]', s)
    text = text.replace('[datetime]', s)
    
    text = text.replace('[br]', '<br />')
    
    greet  = QuotedString("[age(", endQuoteChar=")]")
    for i in greet.searchString(text):
        for n in i:
            b_date = datetime.strptime(n, '%Y-%m-%d')
            text = text.replace('[age(' + n + ')]', str(int((datetime.today() - b_date).days/365)))
    
    greet = QuotedString("[dday(", endQuoteChar=")]")
    for i in greet.searchString(text):
        for n in i:
            b_date = datetime.strptime(n, '%Y-%m-%d')
            text = text.replace('[dday(' + n + ')]', str(int((datetime.today() - b_date).days)))
            
    return text
    
def text_folding(text):
    greet = QuotedString("{{{#!folding ", endQuoteChar="}}}", multiline=True)
    for i in greet.searchString(text):
        for n in i:
            n_split = n.split("\n")
            is_first = True
            s = '<dl class="wiki-folding">' + "\n"
            for a in n_split:
                if is_first == True:
                    s += '<dt>' + a + '</dt>' + "\n<dd>"
                    is_first = False
                elif a == "":
                    continue
                else:
                    s += a + "\n"
            s += '</dd></dl>'
            
            text = text.replace("{{{#!folding" + n + "}}}", s)
    return text
    
def text_html(text):
    greet = QuotedString("{{{#!html ", endQuoteChar="}}}")
    for i in greet.searchString(text):
        for n in i:
            text = text.replace('{{{#!html' + n + "}}}", n)
    return text
    
def text_div(text):
    greet = QuotedString("{{{#!wiki ", endQuoteChar="}}}", escQuote="}}}", multiline=True)
    for i in greet.searchString(text):
        for n in i:
            #print(n)
            n_split = n.split("\n")
            is_first = True
            for a in n_split:
                if is_first == True:
                    s = '<div' + a + '>' + "\n"
                    is_first = False
                else:
                    s += a + "\n"
            s += '</div>'
            
            text = text.replace("{{{#!wiki" + n + "}}}", s)
            
    return text

def text_syntax(text):
    greet = QuotedString("{{{#!syntax ", endQuoteChar="}}}", escQuote="}}}", multiline=True)
    for i in greet.searchString(text):
        for n in i:
            n_split = n.split("\n")
            is_first = True
            s = "<pre>"
            for a in n_split:
                if is_first == True:
                    s += '<code class="syntax" data-language="' + a.strip() + '">' + "\n"
                    is_first = False
                elif a == "":
                    continue
                else:
                    s += a + "\n"
            s += '</code></pre>'
            
            text = text.replace("{{{#!syntax" + n + "}}}", s)
            
    return text
    
def text_closure(text):
    greet = QuotedString("{{|", endQuoteChar="|}}")
    for i in greet.searchString(text):
        for n in i:
            text = text.replace('{{|' + n + '|}}', '<table class="wiki-closure"><tbody><tr><td><p>' + n + '</p></td></tr></tbody></table>')
    return text
    
text = """
{{|내용|}}
"""
text = text_nowiki(text)
text = text_foramting(text)
text = text_sizing(text)
text = text_coloring(text)
text = text_link(text)
text = text_anchor(text)
text = text_youtube(text)
text = text_macro(text)
text = text_folding(text)
text = text_html(text)
text = text_div(text)
text = text_syntax(text)
text = text_closure(text)

text = text_nowiki_print(text)
print(text)
