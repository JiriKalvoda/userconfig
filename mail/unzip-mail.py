#!/usr/bin/env python3
import email
import email.policy
import email.parser
import os, sys
import AdvancedHTMLParser
import html

import tempfile
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('input', default='-')
parser.add_argument('-o', '--output', default=None)
parser.add_argument('-C', '--no-charset-fix', action='store_false', dest='charset_fix')
parser.add_argument('-H', '--input-html', action='store_true')
args = parser.parse_args()


def modify_html(html_str):
    #print(html_str)
    parser = AdvancedHTMLParser.AdvancedHTMLParser()
    parser.parseStr(html_str)
    def go(nd):
        if isinstance(nd, AdvancedHTMLParser.Tags.AdvancedTag):
            for k, v in nd.attributesList:
                if v == 'None':
                    nd.setAttribute(k, v) # HACK for fixing lib
            if args.charset_fix:
                if nd.tagName == 'meta' and nd.hasAttribute('http-equiv') and nd.getAttribute('http-equiv') == "Content-Type":
                    nd.setAttribute('content', 'text/html; charset=utf-8')
            if nd.tagName == 'img':
                src = nd.getAttribute('src')
                #print(src)
                if src.startswith('cid:'):
                    src = src[4:]
                nd.setAttribute('src', src)
            if not nd.isSelfClosing:
                for x in nd.childBlocks:
                    go(x)
            #print(nd.tagName)
            #for x in nd.childBlocks:
                #print("    ", type(x))
                #try:
                    #print("    ", x.tagName)
                    #print("    ", x.attributesList)
                #except AttributeError:
                    #pass
                #print("    ", x)
            #print(nd.innerHTML)
    for nd in parser.getRootNodes():
        go(nd)

    return parser.getHTML()

if args.output is None:
    output = tempfile.mkdtemp()
    print(output)
else:
    output = args.output
    os.mkdir(output)
output+='/'

attachments_dir = output+"/attachments/"
os.mkdir(attachments_dir)

page_dir = output+"/page/"
os.mkdir(page_dir)

if args.input == '-':
    f = sys.stdin.buffer
else:
    f = open(args.input, "br")

if args.input_html:
    with open(page_dir+"/index.html", "w") as of:
        of.write(modify_html(f.read().decode('utf-8')))
    exit(0)



m = email.parser.BytesParser(policy=email.policy.default).parse(f)




page_htmls = []
page_texts = []

def go(x, id, directory):
    filename = x.get_filename()
    if filename is None:
        filename = f"[{x.get_content_type().replace('/','-')}]"
    # TODO kolize
    dirfile = directory+"/"+filename

    #print(filename, x.get_content_type(), type(x), x.is_attachment())
    if x.is_multipart():
        os.mkdir(output+dirfile)
        for id, i in enumerate(x.iter_parts()):
            go(i, id, dirfile)
    else:
        with open(output+dirfile, "wb") as f:
            f.write(x.get_payload(decode=True))
        if x.is_attachment():
            # TODO kolize
            os.symlink("../"+dirfile, attachments_dir+filename)
        else:
            if x.get_content_type() == "text/html":
                page_htmls.append(x)
            if x.get_content_type() == "text/plain":
                page_texts.append(x)
            if x.get_filename():
                os.symlink("../"+dirfile, page_dir+filename)

go(m, 0, "")

main_html = page_htmls[0] if len(page_htmls) else (page_texts[0] if len(page_texts) else None)
if main_html is not None:
    with open(page_dir+"/index.html", "w") as f:
        f.write(modify_html(main_html.get_payload(decode=True).decode('utf-8')))

