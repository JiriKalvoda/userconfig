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
parser.add_argument('--output', default=None)
args = parser.parse_args()



if args.output is None:
    output = tempfile.mkdtemp()
    print(directory)
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

m = email.parser.BytesParser(policy=email.policy.default).parse(f)


def modify_html(html_str):
    parser = AdvancedHTMLParser.AdvancedHTMLParser()
    parser.parseStr(html_str)
    def go(nd):
        if isinstance(nd, AdvancedHTMLParser.Tags.AdvancedTag):
            if nd.tagName == 'img':
                src = nd.getAttribute('src')
                print(src)
                if src.startswith('cid:'):
                    src = src[4:]
                nd.setAttribute('src', src)
            if not nd.isSelfClosing:
                for x in nd.childBlocks:
                    go(x)
    for nd in parser.getRootNodes():
        go(nd)

    return parser.getHTML()



def go(x, id, directory):
    filename = x.get_filename()
    if filename is None:
        filename = f"[{x.get_content_type().replace('/','-')}]"
    # TODO kolize
    dirfile = directory+"/"+filename

    print(filename, x.get_content_type(), type(x), x.is_attachment())
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
            with open(page_dir+"/index.html", "w") as f:
                f.write(modify_html(x.get_payload(decode=True)))
        else:
            if x.get_filename():
                os.symlink("../"+dirfile, page_dir+filename)

go(m, 0, "")

body = m.get_body()
print(body.get_content_type())




