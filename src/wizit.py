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


COMPARABLE_EXTENSIONS = ['.py', '.html', '.xml', '.java', '.properties', '.sql', '.jsf', '.css', '.pks', '.pkb']
EXCLUDE_EXTENSIONS = ['.svn-base', '.class', '.pyc']
EXCLUDE_PATHS = ['/build/', '/dist/']

HTML_HEAD = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html>

<head>
    <meta http-equiv="Content-Type"
          content="text/html; charset=ISO-8859-1" />
    <title></title>
    <style type="text/css">
        table.diff {font-family:Courier; border:medium;width:1300px;font-size:12px;}
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

HTML_FOOT = """
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
            relative_path = current_path[path_length:].replace('\\','/')
            relative_file = relative_path + '/' + file_name
            full_file = current_path.replace('\\','/') + '/' + file_name
            exclude = True if extension.lower() in EXCLUDE_EXTENSIONS else False
            for exclude_path in EXCLUDE_PATHS:
                exclude = True if exclude_path in relative_file else exclude
            comparable = True if extension.lower() in COMPARABLE_EXTENSIONS else False
            line_count = sum(1 for line in open(full_file)) if comparable else 0
            file_dict[relative_file] = {'comparable': comparable,
                                        'exclude': exclude,
                                        'common': True,
                                        'extension': extension.lower(),
                                        'line_count': line_count}
    return file_dict


def find_missing_files(files1, files2):
    count = 0
    content = ''
    for k, v in files1.iteritems():
        if k not in files2.keys():
            files1[k]['common'] = False
            if not files1[k]['exclude']:
                content += '<li>%s</li>'% k
                count += v['line_count']
    return count, content

            
def main(base_path, delta_path, html_path):
    summary = {'added':0, 'removed':0, 'changed':0, 'project':0}

    # retrieve dict of files in path along with attributes
    base_dict = get_file_dict(base_path)
    delta_dict = get_file_dict(delta_path)
    
    # mark files that are not common between the two dicts
    missing_content = '<p>Files Removed</p><ul>'
    summary['removed'],content = find_missing_files(base_dict, delta_dict)
    missing_content = '<p>Files Removed</p><ul>%s</ul>' % content 
    summary['added'],content = find_missing_files(delta_dict, base_dict)
    missing_content += '<p>Files Added</p><ul>%s</ul>' % content 
    
    # count of all edittable lines in delta project
    summary['project'] = sum(v['line_count'] for k,v in delta_dict.iteritems())

    # check for file differences
    diff_content = '<p>Files Changed</p><ul><li>Left: %s</li><li>Right: %s</li></ul>' % (base_path, delta_path)
    for k, v in base_dict.iteritems():
        if v['comparable'] and v['common'] and not v['exclude']:
            base_full_path = base_path + k
            delta_full_path = delta_path + k
            bf = open(base_full_path, 'r').readlines()
            df = open(delta_full_path, 'r').readlines()
            diff_found = False
            mode = 'UNKNOWN'
            for line in difflib.context_diff(bf, df, k, k, n=0):
                diff_found = True
                # determine mode
                if line[:4] == '*** ':
                    mode = 'BASE'
                elif line[:4] == '--- ':
                    mode = 'DELTA'
                # increment changes    
                if mode == 'BASE' and line[:2] == '- ':
                    summary['removed'] += 1
                elif mode == 'DELTA' and line[:2] == '+ ':
                    summary['added'] += 1
                elif mode == 'DELTA' and line[:2] == '! ':
                    summary['changed'] += 1
            # we found a difference so produce a comparison    
            if diff_found:
                diff_content += '<br/>'+difflib.HtmlDiff(wrapcolumn=80).make_table(bf, df, k, k, context=True)

    # build summary content
    summary_html = '<p>Comparing</p><ul><li>Base: %s</li><li>Delta: %s</li></ul>'% (base_path, delta_path)
    summary_html += '<p>File Extensions Compared</p><ul>'
    for v in COMPARABLE_EXTENSIONS:
        summary_html += '<li>%s</li>'% v
    summary_html += '</ul><p>File Extensions Excluded</p><ul>'
    for v in EXCLUDE_EXTENSIONS:
        summary_html += '<li>%s</li>'% v
    summary_html += '</ul><p>Paths Excluded</p><ul>'
    for v in EXCLUDE_PATHS:
        summary_html += '<li>%s</li>'% v
    summary_html += '</ul><p>Line Count</p><ul>'
    for k, v in summary.iteritems():
        summary_html += '<li>%s: %d</li>'% (k,v)
    summary_html += '</ul>'
    
    content = HTML_HEAD + summary_html + missing_content + diff_content + HTML_FOOT
    
    # write html out
    if html_path != 'sys.stdout':
        open(html_path, 'w').write(content)
    else:
        sys.stdout.write(content)


if __name__ == '__main__':
    option_parser = optparse.OptionParser("usage: %prog [options] {base path} {delta path}")
    option_parser.add_option("-o", "--output", dest="htmlpath", default="sys.stdout", type="string", help="output html")
    (options, args) = option_parser.parse_args()
    if len(args) != 2:
        option_parser.error("incorrect number of arguments, missing base or delta paths")
    main(args[0], args[1], options.htmlpath)
    print('<!-- done -->')
