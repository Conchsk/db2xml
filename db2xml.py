# -*- coding: UTF-8 -*-
import csv
import re
import os
from xml.dom import minidom

stack = []


def get_metadata(cur_node):
    for node in cur_node.childNodes:
        if node.nodeName == 'metadata':
            return node
    return None


def query_slaves(metadata):
    csvfile = metadata.childNodes[0].childNodes[0].data
    id = int(metadata.childNodes[1].childNodes[0].data) - 1
    ref_csvfile = metadata.childNodes[2].childNodes[0].data
    ref_id = int(metadata.childNodes[3].childNodes[0].data) - 1

    for ref in stack:
        if ref['csvfile'] == ref_csvfile:
            ref_value = ref['data'][ref_id]
            break

    result = []
    title_line = True
    for line in csv.reader(open(csvfile, 'r')):
        if title_line:
            title_line = False
        else:
            if line[id] == ref_value:
                result.append({'csvfile': csvfile, 'data': line})

    return result


def process_node(cur_node, out):
    if cur_node.nodeType == cur_node.TEXT_NODE:
        return

    out.write(f'<{cur_node.nodeName}>')
    if len(cur_node.childNodes) == 1 and cur_node.childNodes[0].nodeType == cur_node.TEXT_NODE:
        if cur_node.childNodes[0].data.isdigit():
            out.write(
                f'{stack[-1]["data"][int(cur_node.childNodes[0].data) - 1]}')
        else:
            out.write(cur_node.childNodes[0].data)
    else:
        metadata = get_metadata(cur_node)
        if metadata is None:
            for child in cur_node.childNodes:
                process_node(child, out)
        else:
            for data in query_slaves(metadata):
                stack.append(data)
                for child in cur_node.childNodes:
                    if child.nodeName != 'metadata':
                        process_node(child, out)
                stack.pop()
    out.write(f'</{cur_node.nodeName}>')


def predeal(origin_xml):
    with open(origin_xml, 'r') as fp:
        origin_text = fp.read()
    with open('temp_collapse.xml', 'w+') as fp:
        collapse_text = re.sub(re.compile(r'(\r|\n|\t|[ ]{2})'), '', origin_text)
        fp.write(collapse_text)
    DOM = minidom.parse('temp_collapse.xml')
    os.remove('temp_collapse.xml')
    return DOM


def postdeal(collapse_xml):
    with open('temp_pretty.xml', 'w+') as fp:
        fp.write(minidom.parse(collapse_xml).toprettyxml(
            encoding='utf-8').decode('utf-8'))
    os.remove(collapse_xml)
    os.rename('temp_pretty.xml', collapse_xml)


if __name__ == '__main__':
    DOM = predeal('test.xml')
    root = DOM.documentElement

    root_data = get_metadata(root)
    csv_file = root_data.childNodes[0].childNodes[0].data

    title_line = True
    for line in csv.reader(open(csv_file, 'r')):
        if title_line:
            title_line = False
        else:
            while len(stack) != 0:
                stack.pop()
            stack.append({
                'csvfile': csv_file,
                'data': line
            })
            with open(f'{line[0]}_out.xml', 'w') as fp:
                process_node(root.childNodes[1], fp)
            postdeal(f'{line[0]}_out.xml')
