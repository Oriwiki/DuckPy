from pyparsing import QuotedString, LineStart, restOfLine, LineEnd
from urllib.parse   import quote
import re
import time
from datetime import datetime
from collections import OrderedDict
from mywiki.models import Page, Revision
from django.core.exceptions import ObjectDoesNotExist

class NamuMarkParser:
    def __init__(self, input, title, category=True):
        self.nowiki = []
        self.footnote = OrderedDict()
        self.footnote_i = 0
        self.toc = []
        self.toc_before = ""
        self.input = input.replace('\r', '')
        self.title = title
        if category == True:
            self.category = []
        else:
            self.category = False

    def parse(self):
        start_time = time.time()
        text = ""
        input = self.input
        
        self.__text_paragraph(input)

        if len(self.toc) > 0:
            if self.toc_before != "":
                text += '<p>'
                text += self.__parse_defs_multiline(self.toc_before)
                text += '</p>'
            for idx, each_toc in enumerate(self.toc):
                text += '<h' + str(each_toc[2]) + ' class="wiki-heading"><a id="s-' + each_toc[0] + '" href="#toc">' + each_toc[0] + '.</a>' + each_toc[1] + '<span class="wiki-edit-section"><a href="/edit/' + quote(self.title) + '?section=' + str(idx + 1) + '" rel="nofollow">[편집]</a></span></h' + str(each_toc[2]) + '>'
                text += '<p>'
                try:
                    text += self.__parse_defs_multiline(each_toc[3])
                except IndexError:
                    pass
                text += '</p>'
        else:
            text += '<p>'
            text += self.__parse_defs_multiline(input)
            text += '</p>'
        text += self.__text_footnote()
        text += self.__text_category()
        
        end_time = time.time()
        print('parse 처리 시간: ', end_time - start_time)
        
        return text
        
    def get_category(self):
        if not '[[분류:' in self.input:
            return []
            
        text = ""
        for line in self.input.splitlines(True):
            text += self.__text_curly_bracket(line)
            
        category = []
        
        greet = QuotedString('[[분류:',  endQuoteChar="]]")
        for i in greet.searchString(text):
            for n in i:
                category.append('분류:' + n)
                
        return category
        
    def get_toc(self):
        self.__text_paragraph(self.input)
        return self.toc
        
    def get_link(self):
        if not '[[' in self.input:
            return []
            
        text = ""
        for line in self.input.splitlines(True):
            text += self.__text_curly_bracket(line)
            
        link = []
        
        greet = QuotedString('[[',  endQuoteChar="]]")
        for i in greet.searchString(text):
            for n in i:
            
                n_split = n.split("|", 1)
                
                if n.startswith("http://"):
                    continue
                elif n.startswith("#"):
                    continue
                elif n.startswith('분류:'):
                    continue
                elif n.startswith(':분류:'):
                    continue
                    
                link.append(n_split[0])
                    
        return link
        
    def __parse_defs_multiline(self, input):
        text = ""
        # singleline
        lines = input.splitlines(True)
        for key, line in enumerate(lines):
            line = self.__parse_defs_singleline(line)
            text += line
                
        # muliline
        text = self.__text_blockquote(text)
        text = self.__text_folding(text)
        text = self.__text_div(text)
        text = self.__text_syntax(text)
        text = self.__text_unorderd_list(text)
        text = self.__text_orderd_list(text)
        text = self.__text_table(text)
        text = self.__text_indent(text)
        
        
        text_lines = text.splitlines(True)
        text = ''
        for each_line in text_lines:
            if each_line == '<br />':
                continue
            text += each_line + '<br />'
            
        return text
        
    def __parse_defs_singleline(self, text):
        line = text
    
        line = self.__text_curly_bracket(line)
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
        
        return line
        
    def __text_curly_bracket(self, text):
        if not '{{{' in text:
            return text
        
        open_bracket = 0
        close_bracket = 0
        open = 0
        open_list = []
        content_list = []
        for char in list(text):
            if char == "{":
                open_bracket += 1
                
                if open > 0:
                    for i in range(0, open):
                        open_list[i] += char
                
                if open_bracket == 3:
                    open += 1
                    open_bracket = 0
                    open_list.append('{{{')
                    
            elif char == "}":
                close_bracket += 1
                
                if close_bracket == 3:
                    if open > 0:
                        for i in range(0, open):
                            open_list[i] += '}}}'
                    if open == 1:
                        for i in range(0, len(open_list)):
                            content_list.append(open_list[i - 1])
                        open_list = []
                    
                        
                    open -= 1
                    close_bracket = 0
                                    
            else:
                if open > 0:
                    if open > len(open_list):
                        open_list.append(char)
                    elif open == len(open_list):
                        for i in range(0, open):
                            open_list[i] += char
                    elif open < len(open_list):
                        for i in range(0, open):
                            open_list[i] += char
                        
        for each_content in sorted(content_list, key=len, reverse=True):
            for i in QuotedString("{{{", endQuoteChar="}}}", escQuote='}}}').searchString(each_content):
                for n in i:
                    if n.startswith('#'):
                        n = n[1:]
                        n_split = n.split(" ", 1)
                        # hex 코드 구별
                        if re.search(r'^(?:[0-9a-fA-F]{3}){1,2}$', n_split[0]):
                            text = text.replace("{{{#" + n + "}}}", '<span class="wiki-color" style="color: #' + n_split[0] + '">' + n_split[1] + '</span>')
                        elif n_split[0].startswith("!") == False:
                            text = text.replace("{{{#" + n + "}}}", '<span class="wiki-color" style="color: ' + n_split[0] + '">' + n_split[1] + '</span>')
                    elif n.startswith('+'):
                        n = n[1:]
                        n_split = n.split(" ", 1)
                        if 1 <= int(n_split[0]) <= 5:
                            text = text.replace("{{{+" + n + "}}}", '<span class="wiki-size size-' + n_split[0] + '">' + n_split[1] + '</span>')
                    else:
                        text = text.replace("{{{" + n + "}}}", "<nowiki" + str(len(self.nowiki)) + " />", 1)
                        self.nowiki.append(n)
        
            
        return text


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
                    if self.category != False:
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
                        try:
                            Page.objects.get(title=n[1:], is_created=True, is_deleted=False)
                        except ObjectDoesNotExist:
                            text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal not-exist" href="' + quote(n[1:]) + '" title="' + n[1:] + '">' + n[1:] + '</a>')
                        else:
                            text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal" href="' + quote(n[1:]) + '" title="' + n[1:] + '">' + n[1:] + '</a>')
                    else:
                        try:
                            Page.objects.get(title=n, is_created=True, is_deleted=False)
                        except ObjectDoesNotExist:
                            text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal not-exist" href="/w/' + quote(n, '#') + '" title="' + n + '">' + n + '</a>')
                        else:
                            text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal" href="/w/' + quote(n, '#') + '" title="' + n + '">' + n + '</a>')
                elif len(n_split) == 2:
                    if ex_link == True:
                        text = text.replace("[[" + n + "]]", '<a class="wiki-link-external" href="' + n_split[0] + '" target="_blank" rel="noopener" title="' + n_split[0] + '">' + n_split[1] + '</a>')
                    elif self_link == True:
                        text = text.replace("[[" + n + "]]", '<a class="wiki-self-link" href="' + quote(n_split[0], '#') + '" title="' + n_split[0] + '">' + n_split[1] + '</a>')
                    elif category_link == True:
                        try:
                            Page.objects.get(title=n_split[0][1:], is_created=True, is_deleted=False)
                        except ObjectDoesNotExist:
                            text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal not-exist" href="' + quote(n_split[0][1:]) + '" title="' + n_split[0][1:] + '">' + n_split[1] + '</a>')
                        else:
                            text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal" href="' + quote(n_split[0][1:]) + '" title="' + n_split[0][1:] + '">' + n_split[1] + '</a>')
                    else:
                        try:
                            Page.objects.get(title=n_split[0], is_created=True, is_deleted=False)
                        except ObjectDoesNotExist:
                            text = text.replace("[[" + n + "]]", '<a class="wiki-link-internal not-exist" href="/w/' + quote(n_split[0], '#') + '" title="' + n_split[0] + '">' + n_split[1] + '</a>')
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
        if not "[" in text and not "[age(" in text and not "[dday(" in text and not "[pagecount" in text and not "[include(" in text:
            return text
            
    
        now = time.localtime()
        s = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        text = self.ireplace('[date]', s, text)
        
        text = self.ireplace('[datetime]', s, text)
        
        text = self.ireplace('[br]', '<br />', text)
        
        if "[각주]" in text:
            text = text.replace('[각주]', self.__text_footnote())
        if "[footnote]" in text.lower():
            text = self.ireplace('[footnote]', self.__text_footnote(), text)
            
        if "[목차]" in text:
            text = text.replace('[목차]', self.__text_toc())
        if "[tableofcontents]" in text.lower():
            text = self.ireplace('[tableofcontents]', self.__text_toc(), text)
            
        if "[pagecount]" in text:
            text = self.ireplace('[pagecount]', str(self.__text_pagecount()), text)
        elif "[pagecount(" in text.lower():
            greet  = QuotedString("[pagecount(", endQuoteChar=")]")
            for i in greet.searchString(text):
                for n in i:
                    text = text.replace("[pagecount(" + n + ")]", str(self.__text_pagecount(namespace=n)))
            
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
                
        greet = QuotedString("[include(", endQuoteChar=")]")
        for i in greet.searchString(text):
            for n in i:
                n_split = n.split(',')
                try:
                    included_page_jd = Page.objects.get(title=n_split[0]).id
                except ObjectDoesNotExist:
                    text = text.replace("[include(" + n + ")]", "")
                    continue
                    
                included_text = Revision.objects.filter(page=included_page_jd).order_by('-id').first().text
                included_text = NamuMarkParser(included_text, n_split[0], category=False).parse().replace("\n", "")
                
                if len(n_split) > 1:
                    for each_n_split in n_split[1:]:
                        each_n_split_split = each_n_split.strip().split('=')
                        var = each_n_split_split[0]
                        val = each_n_split_split[1]
                        included_text = included_text.replace(var, val)
                        
                    
                text = text.replace("[include(" + n + ")]", included_text)
                
                
        return text
        
    def __text_folding(self, text):
        if not "{{{#!folding " in text:
            return text
    
        greet = QuotedString("{{{#!folding ", endQuoteChar="}}}", multiline=True)
        for i in greet.searchString(text):
            for n in i:
                n_split = n.splitlines(True)
                is_first = True
                s = '<dl class="wiki-folding">'
                for a in n_split:
                    if is_first == True:
                        s += '<dt>' + a + '</dt>' + "<dd>"
                        is_first = False
                    elif a == "":
                        continue
                    else:
                        s += a
                s += '</dd></dl>'
                
                text = text.replace("{{{#!folding" + n + "}}}", s)
        return text
        
    def __text_html(self, text):
        if not "{{{#!html" in text:
            return text
    
        greet = QuotedString("{{{#!html", endQuoteChar="}}}")
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
                n_split = n.splitlines(True)
                is_first = True
                for a in n_split:
                    if is_first == True:
                        s = '<div' + a.replace("\n", "") + '>'
                        is_first = False
                    else:
                        s += a
                s += '</div>'
                
                text = text.replace("{{{#!wiki" + n + "}}}", s)
                
        return text

    def __text_syntax(self, text):
        if not "{{{#!syntax " in text:
            return text
    
        greet = QuotedString("{{{#!syntax ", endQuoteChar="}}}", escQuote="}}}", multiline=True)
        for i in greet.searchString(text):
            for n in i:
                n_split = n.splitlines(True)
                is_first = True
                s = "<pre>"
                for a in n_split:
                    if is_first == True:
                        s += '<code class="syntax" data-language="' + a.strip() + '">'
                        is_first = False
                    elif a == "":
                        continue
                    else:
                        s += a
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
    
        line = text.splitlines(True)
        is_start = False
        new_line = ""
        for key, each_line in enumerate(line):
            if each_line.startswith('>'):
                each_line = self.__text_blockquote(each_line[1:].lstrip())
                if is_start == False:
                    new_line += '<blockquote class="wiki-quote"><p>'+ each_line
                    is_start = True
                else:
                    new_line += each_line
            else:
                if is_start == True:
                    new_line += '</p></blockquote>' + each_line
                    is_start = False
                else:
                    new_line += each_line
                     
        if len(line) == 1:
            if is_start == True:
                new_line += '</p></blockquote>'
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
        line = text.splitlines(True)
        is_start = False
        new_line = ""
        for key, each_line in enumerate(line):
            if each_line.startswith(' '):
                each_line = self.__text_indent(each_line[1:])
                if is_start == False:
                    new_line += '<div class="wiki-indent"><p>'+ each_line
                    is_start = True
                else:
                    new_line += each_line
            else:
                if is_start == True:
                    new_line += '</p></div>' + each_line
                    is_start = False
                else:
                    new_line += each_line
        if len(line) == 1:
            if is_start == True:
                new_line += '</p></div>'
                is_start = False
        return new_line
        
    def __text_footnote(self):
        if len(self.footnote) == 0:
            return ""

        s = '<div class="wiki-macro-footnote">'
        
        i = 0
        d_footnote = []
        for key, value in self.footnote.items():
            i += 1
            if value != "":
                s += '<span class="footnote-list"><span id="fn-' + str(key) + '" class="target"></span><a href="#rfn-' + str(i) + '">[' + str(key) + ']</a>' + value + '</span>'
            d_footnote.append(key)
        
        for key in d_footnote:
            del(self.footnote[key])
        return s + "</div>"

    def __text_unorderd_list(self, text):
        if not '*' in text:
            return text
    
        line = text.splitlines(True)
        is_start = False
        new_line = ""
        list_n = 0
        for key, each_line in enumerate(line):
            if each_line.lstrip().startswith('*'):
                now_len = len(each_line) - len(each_line.lstrip())
                if is_start == False:
                    new_line += '<ul class="wiki-list"><li>' + each_line.lstrip()[1:]
                    is_start = True
                elif now_len > pro_len:
                    new_line += '<ul class="wiki-list"><li>' + each_line.lstrip()[1:]
                    list_n += 1
                elif now_len < pro_len:
                    for r in range(0, list_n):
                        new_line += "</li></ul>"
                        
                    new_line += "<li>" + each_line.lstrip()[1:]
                    list_n -= 1
                else:
                    new_line += "</li><li>" + each_line.lstrip()[1:]
                    
                pro_len = now_len
            else:
                if is_start == True:
                    if list_n == 0:
                        new_line += "</li></ul>"
                    else:
                        for r in range(0, list_n):
                            new_line += "</li></ul>"
                            
                    new_line += each_line
                    
                    is_start = False
                else:
                    new_line += each_line
        
        
        return new_line
        
    def __text_orderd_list(self, text):
        if not '1.' in text and not 'A.' in text and not 'a.' in text and not 'I.' in text and not 'i.' in text:
            return text
    
        line = text.splitlines(True)
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
                    new_line += ol_start + "<li>" + each_line 
                    is_start = True
                elif now_len > pro_len:
                    new_line += ol_start + "<li>" + each_line
                    list_n += 1
                elif now_len < pro_len:
                    for r in range(0, list_n):
                        new_line += "</li></ol>"
                        
                    new_line += "<li>" + each_line
                    list_n -= 1
                else:
                    new_line += "</li><li>" + each_line
                    
                pro_len = now_len
            else:
                if is_start == True:
                    if list_n == 0:
                        new_line += "</li></ol>"
                    else:
                        for r in range(0, list_n):
                            new_line += "</li></ol>"
                    new_line += each_line
                    is_start = False
                else:
                    new_line += each_line
        
        return new_line
        
    def __text_table(self, text):
        if not '||' in text:
            return text
    
        line = OrderedDict()
        for idx, val in enumerate(text.splitlines(True)):
            line[idx] = val
        if line[len(line) - 1] != "":
            line[len(line)] = ""
            
        
        new_line = ""
        is_start = False
        isnt_end = False
        

        line_i = 0
        table = []
        table_line_n = []
        tr_list = []
        caption = []
        each_caption = ""
        for each_line in line.values():
            each_line = each_line.replace('\n', '')
            if each_line.startswith('||'):
                if each_line.endswith('||'):
                    if is_start == False:
                        table_line_n.append([])
                    is_start = True
                    td_list = each_line.split('||')
                    del(td_list[0], td_list[len(td_list) - 1])
                    tr_list.append(td_list)
                    table_line_n[len(table_line_n) - 1].append(line_i)
                else:
                    if is_start == False:
                        table_line_n.append([])
                    isnt_end = True
                    td_list = each_line.split('||')
                    del(td_list[0])
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
            elif each_line.endswith('||'):
                table_line_n[len(table_line_n) - 1].append(line_i)
                tr_list[len(tr_list) - 1][len(tr_list[len(tr_list) - 1]) - 1] += '<br />' + each_line[:-2]
                table.append(tr_list)
                caption.append(each_caption)
                each_caption = ""
                tr_list = []
                isnt_end = False
            else:
                if is_start == True:
                    table.append(tr_list)
                    caption.append(each_caption)
                    each_caption = ""
                    tr_list = []
                    is_start = False
                elif isnt_end == True:
                    table_line_n[len(table_line_n) - 1].append(line_i)
                    
                    tr_list[len(tr_list) - 1][len(tr_list[len(tr_list) - 1]) - 1] += '<br />' + each_line
            line_i += 1
        
        
                
        for table_i in range(0, len(table)):
            for i in table_line_n[table_i][1:]:
                del(line[i])
                
            tr = ""
            table_opt = {}
            for each_tr in table[table_i]:
                tr_style = {}
                td = ""
                td_opt = {}
                td_opt['colspan'] = 0
                for each_td in each_tr:
                    td_style = {}
                    
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
                        
                        td += '><p>' + each_td.strip() + '</p></td>'
                        
                        td_opt = {}
                        td_opt['colspan'] = 0

                        
    
                tr += '<tr'
                if len(tr_style) > 0:
                    tr += ' style="'
                    for key, value in tr_style.items():
                        tr += key + ': ' + value + ';'
                    tr += '"'
                
                tr += '>' + td + '</tr>'
            
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
            
            
            line[table_line_n[table_i][0]] = '<div class="' + div_class + '" style="' + div_style +'">' + '<table class="wiki-table" style="' + table_style + '">'
            
            if caption[table_i] != "":
                line[table_line_n[table_i][0]] += '<caption>' + caption[table_i] + '</caption>'
            
            line[table_line_n[table_i][0]] += '<tbody>' + tr + "</tbody></table></div>"
            
        for key, each_line in line.items():
            new_line += each_line
            
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
            if line.startswith('======') and line.replace('\n', '').endswith('======'):
                line = line.replace('\n', '')
                content = self.__parse_defs_singleline(line[6:][:-6])
                if len(self.toc) == 0:
                    self.toc.append(['1', content, 6])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] < 6:
                        self.toc.append([lastest[0] + '.1', content, 6])
                    elif lastest[2] > 6:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx in range(0, len(lastest_split)):
                            if each_n_idx == len(lastest_split) - 2:
                                toc_str += str(int(lastest_split[each_n_idx]) + 1) + '.'
                            else:
                                toc_str += lastest_split[each_n_idx] + '.'
                        self.toc.append([toc_str[:-1], content, 6])
                    elif lastest[2] == 6:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, content, 6])
            elif line.startswith('=====') and line.replace('\n', '').endswith('====='):
                line = line.replace('\n', '')
                content = self.__parse_defs_singleline(line[5:][:-5])
                if len(self.toc) == 0:
                    self.toc.append(['1', content, 5])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] < 5:
                        self.toc.append([lastest[0] + '.1', content, 5])
                    elif lastest[2] > 5:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx in range(0, len(lastest_split)):
                            if each_n_idx == len(lastest_split) - 2:
                                toc_str += str(int(lastest_split[each_n_idx]) + 1) + '.'
                            else:
                                toc_str += lastest_split[each_n_idx] + '.'
                        self.toc.append([toc_str[:-1], content, 5])
                    elif lastest[2] == 5:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, content, 5])
            elif line.startswith('====') and line.replace('\n', '').endswith('===='):
                line = line.replace('\n', '')
                content = self.__parse_defs_singleline(line[4:][:-4])
                if len(self.toc) == 0:
                    self.toc.append(['1', content, 4])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] < 4:
                        self.toc.append([lastest[0] + '.1', content, 4])
                    elif lastest[2] > 4:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx in range(0, len(lastest_split)):
                            if each_n_idx == len(lastest_split) - 2:
                                toc_str += str(int(lastest_split[each_n_idx]) + 1) + '.'
                            else:
                                toc_str += lastest_split[each_n_idx] + '.'
                        self.toc.append([toc_str[:-1], content, 4])
                    elif lastest[2] == 4:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, lcontent, 4])
            elif line.startswith('===') and line.replace('\n', '').endswith('==='):
                line = line.replace('\n', '')
                content = self.__parse_defs_singleline(line[3:][:-3])
                if len(self.toc) == 0:
                    self.toc.append(['1', content, 3])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] < 3:
                        self.toc.append([lastest[0] + '.1', content, 3])
                    elif lastest[2] > 3:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx in range(0, len(lastest_split)):
                            if each_n_idx == len(lastest_split) - 2:
                                toc_str += str(int(lastest_split[each_n_idx]) + 1) + '.'
                            else:
                                toc_str += lastest_split[each_n_idx] + '.'
                        self.toc.append([toc_str[:-1], content, 3])
                    elif lastest[2] == 3:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, content, 3])
            elif line.startswith('==') and line.replace('\n', '').endswith('=='):
                line = line.replace('\n', '')
                content = self.__parse_defs_singleline(line[2:][:-2])
                if len(self.toc) == 0:
                    self.toc.append(['1', content, 2])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] < 2:
                        self.toc.append([lastest[0] + '.1', content, 2])
                    elif lastest[2] > 2:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        
                        for each_n_idx in range(0, len(lastest_split)):
                            if each_n_idx == len(lastest_split) - 2:
                                toc_str += str(int(lastest_split[each_n_idx]) + 1) + '.'
                            else:
                                toc_str += lastest_split[each_n_idx] + '.'
                        
                        self.toc.append([toc_str[:-1], content, 2])
                    elif lastest[2] == 2:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, content, 2])
            elif line.startswith('=') and line.replace('\n', '').endswith('='):
                line = line.replace('\n', '')
                content = self.__parse_defs_singleline(line[1:][:-1])
                if len(self.toc) == 0:
                    self.toc.append(['1', content, 1])
                else:
                    lastest = self.toc[len(self.toc) - 1]
                    if lastest[2] > 1:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        toc_str += str(int(lastest_split[0]) + 1) + '.'
                                
                        self.toc.append([toc_str[:-1], content, 1])
                    elif lastest[2] == 1:
                        lastest_split = lastest[0].split('.')
                        toc_str = ""
                        for each_n_idx, each_n in enumerate(lastest_split):
                            if each_n_idx == len(lastest_split) - 1:
                                toc_str += str(int(each_n) + 1)
                            else:
                                toc_str += each_n + '.'
                        self.toc.append([toc_str, content, 1])
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
    
        text = '<div id="toc" class="wiki-macro-toc"><div class="toc-indent">'
        last_count = 0
        div_count = 0
        for idx, each in enumerate(self.toc):
            each[1] = self.__parse_defs_singleline(each[1])
            if idx == 0:
                text += '<span class="toc-item"><a href="#s-' + each[0] + '">' + each[0] + '</a>. ' + each[1] + '</span>'
            else:
                now_count = each[0].count('.')
                if last_count == now_count:
                    text += '<span class="toc-item"><a href="#s-' + each[0] + '">' + each[0] + '</a>. ' + each[1] + '</span>'
                elif last_count < now_count:
                    text += '<div class="toc-indent"><span class="toc-item"><a href="#s-' + each[0] + '">' + each[0] + '</a>. ' + each[1] + '</span>'
                    div_count += 1
                    last_count = now_count
                elif last_count > now_count:
                    for j in range(0, last_count - now_count):
                        text += '</div>'
                    div_count -= last_count - now_count
                    text += '<span class="toc-item"><a href="#s-' + each[0] + '">' + each[0] + '</a>. ' + each[1] + '</span>'
                    last_count = now_count
                
        
        for j in range(0, div_count):
            text += '</div>'
        text += '</div></div>'
        return text
        
    def __text_category(self):
        if self.category == False or len(self.category) == 0:
            return ""
            
        text = '<div class="wiki-category"><h2>분류</h2><ul>'
        for each_category in self.category:
            text += '<li><a href="/w/' + quote('분류:' + each_category) + '">' + each_category + '</a></li>'
        text += '</ul></div>'
        
        return text
        
    def __text_pagecount(self, namespace=None):
        if namespace == None:
            return Page.objects.filter(is_created=True).count()
        else:
            if namespace == "문서":
                return Page.objects.filter(is_created=True, namespace=0).count()
            elif namespace == "파일":
                return Page.objects.filter(is_created=True, namespace=3).count()
            elif namespace == "사용자":
                return Page.objects.filter(is_created=True, namespace=2).count()
            elif namespace == LocalSettings.project_name:
                return Page.objects.filter(is_created=True, namespace=5).count()
        
        
    def __cleanhtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

    def ireplace(self, old, new, text):
        idx = 0
        while idx < len(text):
            index_l = text.lower().find(old.lower(), idx)
            if index_l == -1:
                return text
            text = text[:index_l] + new + text[index_l + len(old):]
            idx = index_l + len(new) 
        return text





