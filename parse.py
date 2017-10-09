from pyparsing import Word, srange, alphas, QuotedString, LineStart, restOfLine
from urllib.parse   import quote
import re
import time
from datetime import datetime
import collections


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
    n_split = text[1:].split(" ", 1)
    if 1 <= int(n_split[0]) <= 5:
        return '<span class="wiki-size size-' + n_split[0] + '">' + n_split[1] + '</span>'
    
    return text

def text_coloring(text):
    n_split = text[1:].split(" ", 1)
    if re.search(r'^(?:[0-9a-fA-F]{3}){1,2}$', n_split[0]):
        return '<span class="wiki-color" style="color: #' + n_split[0] + '">' + n_split[1] + '</span>'
    elif n_split[0].startswith("!") == False:
        return '<span class="wiki-color" style="color: ' + n_split[0] + '">' + n_split[1] + '</span>'

def text_nowiki(text):
    greet = QuotedString("{{{", endQuoteChar="}}}", escQuote="}}}")
    for i in greet.searchString(text):
        for n in i:
            if len(nowiki) > 0 and n == nowiki[len(nowiki) - 1]:
                return text
            if n.startswith(('#', '+')) == False:
                text = text.replace("{{{" + n + "}}}", "<nowiki" + str(len(nowiki)) + " />")
                nowiki.append(n)
            old_n = n
            n = text_nowiki(n)
            n_split = n.split(" ", 1)
            # 텍스트 색상, 크기
            if n.startswith('#'):
                text = text.replace("{{{" + old_n + "}}}", text_coloring(n))
            elif n.startswith('+'):
                text = text.replace("{{{" + old_n + "}}}", text_sizing(n))
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
    
    if "[각주]" in text:
        text = text.replace('[각주]', text_footnote())
    if "[footnote]" in text:
        text = text.replace('[footnote]', text_footnote())
    
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
    
def text_reference(text):
    greet = QuotedString("[*", endQuoteChar="]", escQuote="]")
    for i in greet.searchString(text):
        if len(i) == 0:
            return False
        for n in i:
            global footnote_i
            old_n = n
            n = text_reference(n)
            footnote_i += 1

            n_split = n.split(" ", 1)
            if n_split[0] == "":
                footnote[footnote_i] = n_split[1]
                text = text.replace('[*' + old_n + ']', '<a class="wiki-fn-content" title="' + n_split[1] + '" href="#fn-' + str(footnote_i) + '"><span id="rfn-' + str(footnote_i) + '" class="target"></span>[' + str(footnote_i) + ']</a>')
            elif len(n_split) == 1:
                footnote[footnote_i] = ""
                
                text = text.replace('[*' + old_n + ']', '<a class="wiki-fn-content" title="' + footnote[n_split[0]] + '" href="#fn-' + n_split[0] + '"><span id="rfn-' + str(footnote_i) + '" class="target"></span>[' + n_split[0] + ']</a>')
            else:
                footnote[n_split[0]] = n_split[1]
                
                text = text.replace('[*' + old_n + ']', '<a class="wiki-fn-content" title="' + n_split[1] + '" href="#fn-' + n_split[0] + '"><span id="rfn-' + str(footnote_i) + '" class="target"></span>[' + n_split[0] + ']</a>')
    
    return text
    
def text_blockquote(text):
    line = text.split("\n")
    is_start = False
    new_line = ""
    for each_line in line:
        if each_line.startswith('>'):
            each_line = text_blockquote(each_line[1:].lstrip())
            if is_start == False:
                new_line += '<blockquote class="wiki-quote"><p>'+ "\n" + each_line + "\n"
                is_start = True
            else:
                new_line += each_line + "\n"
        else:
            if is_start == True:
                new_line += '</p></blockquote>' + "\n" + each_line + "\n"
                is_start = False
            else:
                new_line += each_line + "\n"
    if len(line) == 1:
        if is_start == True:
            new_line += '</p></blockquote>' + "\n"
            is_start = False
    return new_line
    
def text_comment(text):
    for t in (LineStart() + '##' + restOfLine).searchString(text):
        for n in t:
            text = text.replace('##' + n, '')
       
    return text

def text_hr(text):
    text = re.sub(r'^\-{4,9}$', '<hr>', text, 0, re.M)
    return text
    
def text_indent(text):
    line = text.split("\n")
    is_start = False
    new_line = ""
    for each_line in line:
        if each_line.startswith(' '):
            each_line = text_indent(each_line[1:])
            if is_start == False:
                new_line += '<div class="wiki-indent"><p>'+ "\n" + each_line + "\n"
                is_start = True
            else:
                new_line += each_line + "\n"
        else:
            if is_start == True:
                new_line += '</p></div>' + "\n" + each_line + "\n"
                is_start = False
            else:
                new_line += each_line + "\n"
    if len(line) == 1:
        if is_start == True:
            new_line += '</p></div>' + "\n"
            is_start = False
    return new_line
    
def text_footnote():
    if len(footnote) == 0:
        return ""

    s = '<div class="wiki-macro-footnote">' + "\n"
    
    i = 0
    d_footnote = []
    for key, value in footnote.items():
        i += 1
        if value != "":
            s += '<span class="footnote-list"><span id="fn-' + str(key) + '" class="target"></span><a href="#rfn-' + str(i) + '">[' + str(key) + ']</a>' + value + '</span>' + "\n"
        d_footnote.append(key)
    
    for key in d_footnote:
        del(footnote[key])
    return s + "</div>"

def text_unorderd_list(text):
    line = text.split("\n")
    is_start = False
    new_line = ""
    list_n = 0
    for each_line in line:
        if each_line.lstrip().startswith('*'):
            now_len = len(each_line) - len(each_line.lstrip())
            if is_start == False:
                new_line += '<ul class="wiki-list">\n<li>' + each_line.lstrip()[1:] + "\n"
                is_start = True
            elif now_len > pro_len:
                new_line += '<ul class="wiki-list">\n<li>' + each_line.lstrip()[1:] + "\n"
                list_n += 1
            elif now_len < pro_len:
                for r in range(0, list_n):
                    new_line += "</li></ul>"
                    
                new_line += "<li>" + each_line.lstrip()[1:] + "\n"
                list_n -= 1
            else:
                new_line += "</li>\n<li>" + each_line.lstrip()[1:] + "\n"
                
            pro_len = now_len
        else:
            
            if is_start == True:
                if list_n == 0:
                    new_line += "</li></ul>\n"
                else:
                    for r in range(0, list_n):
                        new_line += "</li></ul>\n"
                new_line += each_line + "\n"
                is_start = False
            else:
                new_line += each_line + "\n"
    
    
    return new_line
    
def text_orderd_list(text):
    line = text.split("\n")
    is_start = False    
    new_line = ""
    list_n = 0
    for each_line in line:
        if each_line.lstrip().startswith(('1.', 'A.', 'a.', 'I.', 'i.')):
            now_len = len(each_line) - len(each_line.lstrip())

            each_line = each_line.lstrip()
        
            if each_line.startswith('1.'):
                ol_start = '<ol class="wiki-list wiki-list-decimal" '
            elif each_line.startswith('A.'):
                ol_start = '<ol class="wiki-list wiki-list-upper-alpha" '
            elif each_line.startswith('a.'):
                ol_start = '<ol class="wiki-list wiki-list-alpha" '
            elif each_line.startswith('I.'):
                ol_start = '<ol class="wiki-list wiki-list-upper-roman" '
            elif each_line.startswith('I.'):
                ol_start = '<ol class="wiki-list wiki-list-roman" '
                
            each_line = each_line[2:]
            
            start_n = re.findall(r"^#(\d+)", each_line)
            if(len(start_n)) > 0:
                ol_start += 'start="' + start_n[0] + '">'
                each_line = re.sub(r"^#(\d+)", '', each_line)
            else:
                ol_start += 'start="1">'
                
            if is_start == False:
                new_line += ol_start + "\n<li>" + each_line + "\n"
                is_start = True
            elif now_len > pro_len:
                new_line += ol_start + "\n<li>" + each_line + "\n"
                list_n += 1
            elif now_len < pro_len:
                for r in range(0, list_n):
                    new_line += "</li></ol>"
                    
                new_line += "<li>" + each_line + "\n"
                list_n -= 1
            else:
                new_line += "</li>\n<li>" + each_line + "\n"
                
            pro_len = now_len
        else:
            if is_start == True:
                if list_n == 0:
                    new_line += "</li></ol>\n"
                else:
                    for r in range(0, list_n):
                        new_line += "</li></ol>\n"
                new_line += each_line + "\n"
                is_start = False
            else:
                new_line += each_line + "\n"
    
    
    return new_line
    

input = """ 
 1. 리스트1
  1. 리스트 2
  1. 리스트 3
   1. 리스트 4
 1. 리스트 5 
 
 a.#20 리스트 7
 a. 리스트 8
"""
text = ""
nowiki = []
footnote = collections.OrderedDict()
footnote_i = 0

# muliline
input = text_blockquote(input)
input = text_folding(input)
input = text_div(input)
input = text_syntax(input)
input = text_unorderd_list(input)
input = text_orderd_list(input)
input = text_indent(input)

# singleline
for line in input.split("\n"):
    line = text_nowiki(line)
    line = text_link(line)
    line = text_foramting(line)
    line = text_anchor(line)
    line = text_youtube(line)
    line = text_reference(line)
    line = text_macro(line)
    line = text_html(line)
    
    line = text_closure(line)
    
    line = text_comment(line)
    line = text_hr(line)

    line = text_nowiki_print(line)
    text += line + "\n"

text += text_footnote()
print(text)