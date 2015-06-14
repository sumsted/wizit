"""Wizit directory tree comparison report

Given a base path and a delta path produce a report that shows new files, removed files and differences in
same files.

Usage: wizit.py [options] {base path} {delta path}

Options:
  -h, --help            show this help message and exit
  -o HTMLPATH, --output=HTMLPATH
                        output html

"""
import optparse
import os
import difflib
import sys


VALID_EXTENSIONS = ['.py', '.html', '.xml', '.java', '.properties']

HTML_PRE = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html>

<head>
    <meta http-equiv="Content-Type"
          content="text/html; charset=ISO-8859-1" />
    <title></title>
    <style type="text/css">
        table.diff {font-family:Courier; border:medium;}
        .diff_header {background-color:#e0e0e0}
        td.diff_header {text-align:right}
        .diff_next {background-color:#c0c0c0}
        .diff_add {background-color:#aaffaa}
        .diff_chg {background-color:#ffff77}
        .diff_sub {background-color:#ffaaaa}
    </style>
</head>

<body>
"""

HTML_POST = """
    <table class="diff" summary="Legends">
        <tr> <th colspan="2"> Legends </th> </tr>
        <tr> <td> <table border="" summary="Colors">
                      <tr><th> Colors </th> </tr>
                      <tr><td class="diff_add">&nbsp;Added&nbsp;</td></tr>
                      <tr><td class="diff_chg">Changed</td> </tr>
                      <tr><td class="diff_sub">Deleted</td> </tr>
                  </table></td>
             <td> <table border="" summary="Links">
                      <tr><th colspan="2"> Links </th> </tr>
                      <tr><td>(f)irst change</td> </tr>
                      <tr><td>(n)ext change</td> </tr>
                      <tr><td>(t)op</td> </tr>
                  </table></td> </tr>
    </table>
</body>

</html>
"""


def get_file_dict(path):
    file_dict = {}
    path_length = len(path)
    for current_path, subdir_list, file_list in os.walk(path):
        for file_name in file_list:
            proper_name, extension = os.path.splitext(file_name)
            if extension in VALID_EXTENSIONS:
                relative_path = current_path[path_length:]
                relative_file = relative_path + '/' + file_name
                file_dict[relative_file] = True
    return file_dict


def find_missing_files(files1, files2):
    for k in files1.iterkeys():
        if k not in files2.keys():
            files1[k] = False


def main(base_path, delta_path, html_path):
    base_dict = get_file_dict(base_path)
    delta_dict = get_file_dict(delta_path)
    find_missing_files(base_dict, delta_dict)
    find_missing_files(delta_dict, base_dict)

    html = ''
    heading = True
    found = False
    for k, v in base_dict.iteritems():
        if not v:
            html += '<p>Files Removed</p><ul>' if heading else ''
            html += '<li>%s</li>' % k
            heading = False
            found = True
    html += '</ul>' if found else ''
    heading = True
    found = False
    for k, v in delta_dict.iteritems():
        if not v:
            html += '<p>Files Added</p>' if heading else ''
            html += '<li>%s</li>' % k
            heading = False
            found = True
    html += '</ul>' if found else ''
    html += '<p>Left: %s</p><p>Right: %s</p>' % (base_path, delta_path)
    for k, v in base_dict.iteritems():
        if v:
            base_full_path = base_path + k
            delta_full_path = delta_path + k
            bf = open(base_full_path, 'r').readlines()
            df = open(delta_full_path, 'r').readlines()
            diff_found = False
            for line in difflib.context_diff(bf, df, k, k):
                diff_found = True
                break
            if diff_found:
                html += difflib.HtmlDiff(wrapcolumn=60).make_table(bf, df, k, k, context=True)
    if html_path != 'sys.stdout':
        open(html_path, 'w').write(HTML_PRE + html + HTML_POST)
    else:
        sys.stdout.write(HTML_PRE + html + HTML_POST)


if __name__ == '__main__':
    option_parser = optparse.OptionParser("usage: %prog [options] {base path} {delta path}")
    option_parser.add_option("-o", "--output", dest="htmlpath", default="sys.stdout", type="string", help="output html")
    (options, args) = option_parser.parse_args()
    if len(args) != 2:
        option_parser.error("incorrect number of arguments, missing base or delta paths")
    main(args[0], args[1], options.htmlpath)
    print('<!-- done -->')
