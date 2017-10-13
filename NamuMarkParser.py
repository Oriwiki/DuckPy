from pyparsing import QuotedString, LineStart, restOfLine, LineEnd
from urllib.parse   import quote
import re
import time
from datetime import datetime
from collections import OrderedDict

class NamuMarkParser:
    def __init__(self, input, title):
        self.nowiki = []
        self.footnote = OrderedDict()
        self.footnote_i = 0
        self.toc = []
        self.toc_before = ""
        self.input = input
        self.title = title
        self.category = []

    def parse(self):
        start_time = time.time()
        text = ""
        input = self.input
        self.__text_paragraph(input)

        if len(self.toc) > 0:
            if self.toc_before != "":
                text += '<p>\n'
                text += self.__parse_defs_multiline(self.toc_before)
                text += '\n</p>\n'
            for idx, each_toc in enumerate(self.toc):
                text += '<h' + str(each_toc[2]) + ' class="wiki-heading"><a id="s-' + each_toc[0] + '" href="#toc">' + each_toc[0] + '.</a>' + each_toc[1] + '<span class="wiki-edit-section"><a href="/edit/' + quote(self.title) + '?section=' + str(idx + 1) + '" rel="nofollow">[편집]</a></span></h' + str(each_toc[2]) + '>\n'
                text += '<p>\n'
                text += self.__parse_defs_multiline(each_toc[3])
                text += '\n</p>\n'
        else:
            text += '<p>\n'
            text += self.__parse_defs_multiline(input)
            text += '\n</p>\n'
        text += self.__text_footnote()
        text += self.__text_category()
        
        end_time = time.time()
        print('parse 처리 시간: ', end_time - start_time)
        
        return text
        
    def __parse_defs_multiline(self, input):
        text = ""
    
        # muliline
        input = self.__text_blockquote(input)
        input = self.__text_folding(input)
        input = self.__text_div(input)
        input = self.__text_syntax(input)
        input = self.__text_unorderd_list(input)
        input = self.__text_orderd_list(input)
        input = self.__text_table(input)
        input = self.__text_indent(input)


        # singleline
        lines = input.split("\n")
        for key, line in enumerate(lines):
            line = self.__parse_defs_singleline(line)
            text += line
            if key == 0 and line == "":
                pass
            elif key < len(lines) - 1:
                text += "<br />\n"
                
        return text
        
    def __parse_defs_singleline(self, text):
        line = text
    
        line = self.__text_nowiki(line)
        line = self.__text_sizing(line)
        line = self.__text_coloring(line)
        line = self.__text_link(line)
        line = self.__text_foramting(line)
        line = self.__text_anchor(line)
        line = self.__text_youtube(line)
        line = self.__text_reference(line)

        line = self.__text_macro(line)
        line = self.__text_html(line)
        
        line = self.__text_closure(line)
        
        line = self.__text_comment(line)
        line = self.__text_hr(line)
        line = self.__text_math(line)

        line = self.__text_nowiki_print(line)
        
        #후처리
        line = re.sub(r'{{{(.*)(</.*>)}}}', r"<code>\1</code>\2", line)
        
        return line


    def __text_foramting(self, text):
        if not "''" in text and not "~~" in text and not "--" in text and not "__" in text and not "^^" in text and not ",," in text:
            return text
    
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
                    
    def __text_sizing(self, text):
        if not "{{{+" in text:
            return text
    
        greet = QuotedString("{{{+", endQuoteChar="}}}")
        
        for i in greet.searchString(text):
            for n in i:
                n_split = n.split(" ", 1)
                if 1 <= int(n_split[0]) <= 5:
                    text = text.replace("{{{+" + n + "}}}", '<span class="wiki-size size-' + n_split[0] + '">' + n_split[1] + '</span>')
        return text

    def __text_coloring(self, text):
        if not "{{{#" in text:
            return text
    
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
        
    def __text_nowiki(self, text):
        if not "{{{" in text:
            return text
    
        greet = QuotedString("{{{", endQuoteChar="}}}", escQuote="}}}")
        for i in greet.searchString(text):
            for n in i:
                if n.startswith(('#', '+')):
                    return text
                text = text.replace("{{{" + n + "}}}", "<nowiki" + str(len(self.nowiki)) + " />")
                self.nowiki.append(n)
        return text

    def __text_nowiki_print(self, text):
        if len(self.nowiki) == 0:
            return text
    
        i = 0
        while i <= len(self.nowiki) - 1:
            text = text.replace("<nowiki" + str(i) + " />", "<code>" + self.nowiki[i] + "</code>")
            i += 1
        return text
        
    def __text_link(self, text):
        if not "[[" in text:
            return text
    
        greet = QuotedString("[[", endQuoteChar="]]")
        for i in greet.searchString(text):
            for n in i:
                n_split = n.split("|", 1)
                ex_link = False
                self_link = False
                category_link = False
                
                if n.startswith("http://"):
                    ex_link = True
                elif n.startswith("#"):
                    self_link = True
                elif n.startswith('분류:'):
                    text = text.replace("[[" + n + "]]", '')
                    self.category.append(n[3:])
                    continue
                elif n.startswith(':분류:'):
                    category_link = True
                
                if len(n_split) == 1:
                    if ex_link == True:
                        text = text.replace("[[" + n + "]]", '<a class="wiki-link-external" href="' + n + '" target="_blank" rel="noopener" title="' + n + '">' + n + '</a>')
                    elif self_link == True:
                        text = text.replace("[[" + n + "]]", '<a class="wiki-self-link" href="' + quote(n, '#') + '" title="' + n + '">' + n + '</a>')
                    elif category_link == True:
                        text = text.replace("[[" + n + "]]", '<a class="wiki-self-internal" href="' + quote(n[1:]) + '" title="' + n[1:] + '">' + n[1:] + '</a>')
                    else:
                        text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal" href="/w/' + quote(n, '#') + '" title="' + n + '">' + n + '</a>')
                elif len(n_split) == 2:
                    if ex_link == True:
                        text = text.replace("[[" + n + "]]", '<a class="wiki-link-external" href="' + n_split[0] + '" target="_blank" rel="noopener" title="' + n_split[0] + '">' + n_split[1] + '</a>')
                    elif self_link == True:
                        text = text.replace("[[" + n + "]]", '<a class="wiki-self-link" href="' + quote(n_split[0], '#') + '" title="' + n_split[0] + '">' + n_split[1] + '</a>')
                    elif category_link == True:
                        text = text.replace("[[" + n + "]]", '<a class="wiki-self-internal" href="' + quote(n_split[0][1:]) + '" title="' + n_split[0][1:] + '">' + n_split[1] + '</a>')
                    else:
                        text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal" href="/w/' + quote(n_split[0], '#') + '" title="' + n_split[0] + '">' + n_split[1] + '</a>')
        return text
        
    def __text_anchor(self, text):
        if not "[anchor(" in text:
            return text
    
        greet = QuotedString("[anchor(", endQuoteChar=")]")
        for i in greet.searchString(text):
            for n in i:
                text = text.replace("[anchor(" + n + ")]", '<a id="' + n + '"></a>')
        return text
        
    def __text_youtube(self, text):
        if not "[youtube(" in text:
            return text
            
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
        
    def __text_macro(self, text):
        if not "[" in text and not "[age(" in text and not "[dday(" in text:
            return text
            
    
        now = time.localtime()
        s = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        text = text.replace('[date]', s)
        text = text.replace('[datetime]', s)
        
        text = text.replace('[br]', '<br />')
        
        if "[각주]" in text:
            text = text.replace('[각주]', self.__text_footnote())
        if "[footnote]" in text:
            text = text.replace('[footnote]', self.__text_footnote())
            
        if "[목차]" in text:
            text = text.replace('[목차]', self.__text_toc())
        if "[tableofcontents]" in text:
            text = text.replace('[tableofcontents]', self.__text_toc())
            
        
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
        
    def __text_folding(self, text):
        if not "{{{#!folding " in text:
            return text
    
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
        
    def __text_html(self, text):
        if not "{{{#!html " in text:
            return text
    
        greet = QuotedString("{{{#!html ", endQuoteChar="}}}")
        for i in greet.searchString(text):
            for n in i:
                text = text.replace('{{{#!html' + n + "}}}", n)
        return text
        
    def __text_div(self, text):
        if not "{{{#!wiki " in text:
            return text
    
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

    def __text_syntax(self, text):
        if not "{{{#!syntax " in text:
            return text
    
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
        
    def __text_closure(self, text):
        if not "{{|" in text:
            return text
    
        greet = QuotedString("{{|", endQuoteChar="|}}")
        for i in greet.searchString(text):
            for n in i:
                text = text.replace('{{|' + n + '|}}', '<table class="wiki-closure"><tbody><tr><td><p>' + n + '</p></td></tr></tbody></table>')
        return text
        
    def __text_reference(self, text):
        if not '[*' in text:
            return text
        
        sliced_text = list(text)
        open = 0
        content = []
        text = ""
        
        for idx, each_char in enumerate(sliced_text):
            if each_char == '[' and sliced_text[idx + 1] == '*':
                content.append('')
                open += 1
            elif each_char == ']':
                    
                for each_content in content:
                    self.footnote_i += 1
                    each_content_split = each_content.split(" ", 1)
                    if each_content_split[0] == "":
                        self.footnote[self.footnote_i] = each_content_split[1]
                        text += '<a class="wiki-fn-content" title="' + self.__cleanhtml(each_content_split[1]) + '" href="#fn-' + str(self.footnote_i) + '"><span id="rfn-' + str(self.footnote_i) + '" class="target"></span>[' + str(self.footnote_i) + ']</a>'
                        
                        
                    elif len(each_content_split) == 1:
                        self.footnote[self.footnote_i] = ""
                        text += '<a class="wiki-fn-content" title="' + self.__cleanhtml(self.footnote[each_content_split[0]]) + '" href="#fn-' + each_content_split[0] + '"><span id="rfn-' + str(self.footnote_i) + '" class="target"></span>[' + each_content_split[0] + ']</a>'
                        
                    else:
                        self.footnote[each_content_split[0]] = each_content_split[1]
                        text += '<a class="wiki-fn-content" title="' + self.__cleanhtml(each_content_split[1]) + '" href="#fn-' + each_content_split[0] + '"><span id="rfn-' + str(self.footnote_i) + '" class="target"></span>[' + each_content_split[0] + ']</a>'
                        
                content = []
                    
                open -= 1
            elif open > 0 and each_char == '*':
                pass
            elif open > 0 and each_char != '*':
                if len(content) < open:
                    content.append(each_char)
                elif len(content) == open:
                    for i in range(0, len(content)):
                        content[i] += each_char
                elif len(content) > open:
                    content[len(content) - 1] += each_char
            else:
                text += each_char
                
        return text
    
    def __text_blockquote(self, text):
        if not '>' in text:
            return text
    
        line = text.split("\n")
        is_start = False
        new_line = ""
        for key, each_line in enumerate(line):
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
                    new_line += each_line
                    if key < len(line) - 1:
                        new_line += "\n"
                     
        if len(line) == 1:
            if is_start == True:
                new_line += '</p></blockquote>' + "\n"
                is_start = False
        return new_line
        
    def __text_comment(self, text):
        if not '##' in text:
            return text
    
        for t in (LineStart() + '##' + restOfLine).searchString(text):
            for n in t:
                text = text.replace('##' + n, '')
           
        return text

    def __text_hr(self, text):
        if '----' in text:
            text = re.sub(r'^\-{4,9}$', '<hr>', text, 0, re.M)
        return text
        
    def __text_indent(self, text):
        line = text.split("\n")
        is_start = False
        new_line = ""
        for key, each_line in enumerate(line):
            if each_line.startswith(' '):
                each_line = self.__text_indent(each_line[1:])
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
                    new_line += each_line
                    if key < len(line) - 1:
                        new_line += "\n"
        if len(line) == 1:
            if is_start == True:
                new_line += '</p></div>' + "\n"
                is_start = False
        return new_line
        
    def __text_footnote(self):
        if len(self.footnote) == 0:
            return ""

        s = '<div class="wiki-macro-footnote">' + "\n"
        
        i = 0
        d_footnote = []
        for key, value in self.footnote.items():
            i += 1
            if value != "":
                s += '<span class="footnote-list"><span id="fn-' + str(key) + '" class="target"></span><a href="#rfn-' + str(i) + '">[' + str(key) + ']</a>' + value + '</span>' + "\n"
            d_footnote.append(key)
        
        for key in d_footnote:
            del(self.footnote[key])
        return s + "</div>"

    def __text_unorderd_list(self, text):
        if not '*' in text:
            return text
    
        line = text.split("\n")
        is_start = False
        new_line = ""
        list_n = 0
        for key, each_line in enumerate(line):
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
                            
                    new_line += each_line
                    if key < len(line) - 1:
                        new_line += "\n"
                    
                    is_start = False
                else:
                    new_line += each_line
                    if key < len(line) - 1:
                        new_line += "\n"
        
        
        return new_line
        
    def __text_orderd_list(self, text):
        if not '1.' in text and not 'A.' in text and not 'a.' in text and not 'I.' in text and not 'i.' in text:
            return text
    
        line = text.split("\n")
        is_start = False    
        new_line = ""
        list_n = 0
        for key, each_line in enumerate(line):
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
                    new_line += each_line
                    if key < len(line) - 1:
                        new_line += "\n"
                    is_start = False
                else:
                    new_line += each_line
                    if key < len(line) - 1:
                        new_line += "\n"
        
        
        return new_line
        
    def __text_table(self, text):
        if not '||' in text:
            return text
    
        line = OrderedDict()
        for idx, val in enumerate(text.split("\n")):
            line[idx] = val
            
        
        new_line = ""
        is_start = False
        

        line_i = 0
        table = []
        table_line_n = []
        tr_list = []
        caption = []
        each_caption = ""
        for each_line in line.values():
            if each_line.startswith('||'):
                if is_start == False:
                    table_line_n.append([])
                is_start = True
                td_list = each_line.split('||')
                del(td_list[0], td_list[len(td_list) - 1])
                tr_list.append(td_list)
                table_line_n[len(table_line_n) - 1].append(line_i)
            elif each_line.startswith('|'):
                each_caption = each_line.split('|')[1]
                each_line = each_line.replace('|' + each_caption + '|', '||')
                
                if is_start == False:
                    table_line_n.append([])
                is_start = True
                td_list = each_line.split('||')
                del(td_list[0], td_list[len(td_list) - 1])
                tr_list.append(td_list)
                table_line_n[len(table_line_n) - 1].append(line_i)
            else:
                if is_start == True:
                    table.append(tr_list)
                    caption.append(each_caption)
                    each_caption = ""
                    tr_list = []
                    is_start = False
            line_i += 1
        
        
                
        for table_i in range(0, len(table)):
            for i in table_line_n[table_i][1:]:
                del(line[i])
                
            tr = ""
            table_opt = {}
            for each_tr in table[table_i]:
                tr_style = {}
                td = ""
                for each_td in each_tr:
                    td_opt = {}
                    td_style = {}
                    td_opt['colspan'] = 0
                    
                    colspan = re.search(r"<-(\d+)>", each_td)
                    if colspan:
                        td_opt['colspan'] += int(colspan.group(1))
                        each_td = each_td.replace(colspan.group(0), '', 1)
                        
                    rowspan = re.search(r"<([v^]?)\|(\d+)>", each_td)
                    if rowspan:
                        td_opt['rowspan'] = rowspan.group(2)
                        if rowspan.group(1) == "v":
                            td_style['vertical-align'] = 'bottom'
                        elif rowspan.group(1) == "^":
                            td_style['vertical-align'] = 'top'
                        each_td = each_td.replace(rowspan.group(0), '', 1)
                        
                    bgcolor = re.search(r"<(#(?:[0-9a-fA-F]{3}){1,2})>", each_td)
                    if bgcolor:
                        td_style['background-color'] = bgcolor.group(1)
                        each_td = each_td.replace(bgcolor.group(0), '', 1)
                    
                    for align_re in re.finditer(r"<(\W)>", each_td):
                        if align_re.group(1) == ':':
                            td_style['text-align'] = 'center'
                        elif align_re.group(1) == ')':
                            td_style['text-align'] = 'right'
                        each_td = each_td.replace(align_re.group(0), '', 1)
                        
                    for tdtr_style_re in re.finditer(r"<([a-zA-Z]+)=([a-zA-Z#\d%]+)>", each_td):
                        if tdtr_style_re.group(1) == 'rowbgcolor':
                            tr_style['background-color'] = tdtr_style_re.group(2)
                        elif tdtr_style_re.group(1) == 'bgcolor':
                            td_style['background-color'] = tdtr_style_re.group(2)
                        else:
                            td_style[tdtr_style_re.group(1)] = tdtr_style_re.group(2)
                            
                        each_td = each_td.replace(tdtr_style_re.group(0), '', 1)
                        
                    
                    for table_opt_re in re.finditer(r"<table ([a-zA-Z]+)=([a-zA-Z#\d%]+)>", each_td):
                        table_opt[table_opt_re.group(1)] = table_opt_re.group(2)
                        each_td = each_td.replace(table_opt_re.group(0), '', 1)
                        
                    if len(each_td) > len(each_td.lstrip()) and len(each_td) > len(each_td.rstrip()):
                        td_style['text-align'] = 'center'
                    elif len(each_td) > len(each_td.lstrip()) and len(each_td) == len(each_td.rstrip()):
                        td_style['text-align'] = 'right'
                        
                    if each_td == "":
                        if td_opt['colspan'] == 0:
                            td_opt['colspan'] += 2
                        else:
                            td_opt['colspan'] += 1
                    else:
                        
                        td += '<td'
                        for key, value in td_opt.items():
                            if key == 'colspan' and value == 0:
                                continue
                            td += ' ' + key + '=' + '"' + str(value) + '"'
                        if len(td_style) > 0:
                            td += ' style="'
                            for key, value in td_style.items():
                                td += key + ': ' + value + ';'
                            td += '"'
                        
                        td += '><p>' + each_td.strip() + '</p></td>'  + "\n"
                        
                tr += '<tr'
                if len(tr_style) > 0:
                    tr += ' style="'
                    for key, value in tr_style.items():
                        tr += key + ': ' + value + ';'
                    tr += '"'
                
                tr += '>\n' + td + '</tr>' + "\n"
            
            div_class = 'wiki-table-wrap'
            div_style = ''
            table_style = ''
            for key, value in table_opt.items():
                if key == 'align':
                    div_class += ' table-' + value
                elif key == 'bgcolor':
                    table_style += 'background-color: ' + value + ';'
                elif key == 'bordercolor':
                    table_style += 'border: 2px solid ' + value + ';'
                elif key == 'width':
                    div_style += 'width: ' + value + ';'
                    table_style += 'width: 100%;'
            
            
            line[table_line_n[table_i][0]] = '<div class="' + div_class + '" style="' + div_style +'">' + "\n" + '<table class="wiki-table" style="' + table_style + '">' + "\n"
            
            if caption[table_i] != "":
                line[table_line_n[table_i][0]] += '<caption>' + caption[table_i] + '</caption>\n'
            
            line[table_line_n[table_i][0]] += '<tbody>' + "\n" + tr + "</tbody>\n</table>\n</div>"
            
        for key, each_line in line.items():
            new_line += each_line
            if key < len(line) - 1:
                new_line += "\n"
            
            
        return new_line
        
    def __text_math(self, text):
        if not '<math>' in text:
            return text
    
        greet = QuotedString("<math>", endQuoteChar="</math>")
        for i in greet.searchString(text):
            for n in i:
                text = text.replace('<math>' + n + '</math>', '[math]' + n + '[/math]')
        return text
        
    def __text_paragraph(self, text):
        if not '=' in text:
            return False
    
        lines = text.splitlines(True)
        new_line = ""
        
        for key, line in enumerate(lines):
            if line.startswith('======') and line.endswith('======\n'):
                line = line.replace('\n', '')
                if len(self.toc) == 0:
                    self.toc.append(['1', line[6:][:-6], 6])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] < 6:
                        self.toc.append([lastest[0] + '.1', line[6:][:-6], 6])
                    elif lastest[2] > 6:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx in range(0, 6):
                            if each_n_idx == 5:
                                toc_str += str(int(lastest_split[each_n_idx]) + 1) + '.'
                            else:
                                toc_str += lastest_split[each_n_idx] + '.'
                        self.toc.append([toc_str[:-1], line[6:][:-6], 6])
                    elif lastest[2] == 6:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, line[6:][:-6], 6])
            elif line.startswith('=====') and line.endswith('=====\n'):
                line = line.replace('\n', '')
                if len(self.toc) == 0:
                    self.toc.append(['1', line[5:][:-5], 5])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] < 5:
                        self.toc.append([lastest[0] + '.1', line[5:][:-5], 5])
                    elif lastest[2] > 5:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx in range(0, 5):
                            if each_n_idx == 4:
                                toc_str += str(int(lastest_split[each_n_idx]) + 1) + '.'
                            else:
                                toc_str += lastest_split[each_n_idx] + '.'
                        self.toc.append([toc_str[:-1], line[5:][:-5], 5])
                    elif lastest[2] == 5:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, line[5:][:-5], 5])
            elif line.startswith('====') and line.endswith('====\n'):
                line = line.replace('\n', '')
                if len(self.toc) == 0:
                    self.toc.append(['1', line[4:][:-4], 4])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] < 4:
                        self.toc.append([lastest[0] + '.1', line[4:][:-4], 4])
                    elif lastest[2] > 4:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx in range(0, 4):
                            if each_n_idx == 3:
                                toc_str += str(int(lastest_split[each_n_idx]) + 1) + '.'
                            else:
                                toc_str += lastest_split[each_n_idx] + '.'
                        self.toc.append([toc_str[:-1], line[4:][:-4], 4])
                    elif lastest[2] == 4:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, line[4:][:-4], 4])
            elif line.startswith('===') and line.endswith('===\n'):
                line = line.replace('\n', '')
                if len(self.toc) == 0:
                    self.toc.append(['1', line[3:][:-3], 3])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] < 3:
                        self.toc.append([lastest[0] + '.1', line[3:][:-3], 3])
                    elif lastest[2] > 3:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx in range(0, 3):
                            if each_n_idx == 2:
                                toc_str += str(int(lastest_split[each_n_idx]) + 1) + '.'
                            else:
                                toc_str += lastest_split[each_n_idx] + '.'
                        self.toc.append([toc_str[:-1], line[3:][:-3], 3])
                    elif lastest[2] == 3:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, line[3:][:-3], 3])
            elif line.startswith('==') and line.endswith('==\n'):
                line = line.replace('\n', '')
                if len(self.toc) == 0:
                    self.toc.append(['1', line[2:][:-2], 2])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] < 2:
                        self.toc.append([lastest[0] + '.1', line[2:][:-2], 2])
                    elif lastest[2] > 2:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        
                        for each_n_idx in range(0, 2):
                            if each_n_idx == 1:
                                toc_str += str(int(lastest_split[each_n_idx]) + 1) + '.'
                            else:
                                toc_str += lastest_split[each_n_idx] + '.'
                        
                        self.toc.append([toc_str[:-1], line[2:][:-2], 2])
                    elif lastest[2] == 2:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, line[2:][:-2], 2])
            elif line.startswith('=') and line.endswith('=\n'):
                line = line.replace('\n', '')
                if len(self.toc) == 0:
                    self.toc.append(['1', line[1:][:-1], 1])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] > 1:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        toc_str += str(int(lastest_split[0]) + 1) + '.'
                                
                        self.toc.append([toc_str[:-1], line[1:][:-1], 1])
                    elif lastest[2] == 1:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, line[1:][:-1], 1])
            else:
                if len(self.toc) > 0:
                    if len(self.toc[len(self.toc) - 1]) == 4:
                        self.toc[len(self.toc) - 1][3] += line
                    else:
                        self.toc[len(self.toc) - 1].append(line)
                else:
                    self.toc_before += line
                    
        return True
        
    def __text_toc(self):
        if len(self.toc) == 0:
            return ""
    
        text = '<div id="toc" class="wiki-macro-toc">\n<div class="toc-indent">\n'
        last_count = 0
        div_count = 0
        for idx, each in enumerate(self.toc):
            each[1] = self.__parse_defs_singleline(each[1])
            if idx == 0:
                text += '<span class="toc-item">\n<a href="#s-' + each[0] + '">' + each[0] + '</a>\n. ' + each[1] + '\n</span>\n'
            else:
                now_count = each[0].count('.')
                if last_count == now_count:
                    text += '<span class="toc-item">\n<a href="#s-' + each[0] + '">' + each[0] + '</a>\n. ' + each[1] + '\n</span>\n'
                elif last_count < now_count:
                    text += '<div class="toc-indent">\n<span class="toc-item">\n<a href="#s-' + each[0] + '">' + each[0] + '</a>\n. ' + each[1] + '\n</span>\n'
                    div_count += 1
                    last_count = now_count
                elif last_count > now_count:
                    for j in range(0, last_count - now_count):
                        text += '</div>\n'
                    div_count -= last_count - now_count
                    text += '<span class="toc-item">\n<a href="#s-' + each[0] + '">' + each[0] + '</a>\n. ' + each[1] + '\n</span>\n'
                    last_count = now_count
                
        
        for j in range(0, div_count):
            text += '</div>\n'
        text += '</div>\n</div>'
        return text
        
    def __text_category(self):
        if len(self.category) == 0:
            return ""
            
        text = '<div class="wiki-category"><h2>분류</h2><ul>'
        for each_category in self.category:
            text += '<li><a href="/w/' + quote('분류:' + each_category) + '">' + each_category + '</a></li>'
        text += '</ul></div>'
        
        return text
        
    def __cleanhtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

            






