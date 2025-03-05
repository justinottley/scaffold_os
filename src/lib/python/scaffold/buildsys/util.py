#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

def import_module(module_ns):

    top_module = __import__(module_ns)
    for entry in module_ns.split('.')[1:]:
        top_module = getattr(top_module, entry)

    return top_module


def get_required_thirdparty_info(thirdparty_value):

    result = []

    thirdparty_entries = thirdparty_value.split()
    for thirdparty_entry in thirdparty_entries:
        thirdparty_entry = thirdparty_entry.strip()
        entry_parts = thirdparty_entry.split('-')
        result.append(entry_parts)

    return result


def get_required_thirdparty_version(thirdparty_value, project_name):

    thirdparty_entries = thirdparty_value.split()
    for thirdparty_entry in thirdparty_entries:
        thirdparty_entry = thirdparty_entry.strip()
        entry_parts = thirdparty_entry.split('-')
        if entry_parts[0] == project_name:
            return entry_parts[1]