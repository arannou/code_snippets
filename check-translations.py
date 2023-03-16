''' Script used to check translations
'''

import json
import glob
import re
from os import sys
from click import prompt, confirm
import inquirer

from check_translations_config import *

nb_errors = int(0)
nb_corrected = int(0)
edit = False


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def find_duplicates():
    '''find duplicates in en_US, for both key and value ie key: value is duplicated at key: value'''
    global nb_errors
    with open(en_file) as f:
        seen = {}
        line_count = 1
        for line in f:
            line_trim = " ".join(line.split())
            if not any(elem in r"\{\}" for elem in line_trim):
                if line_trim in seen.keys():
                    seen[line_trim] += ", " + str(line_count)
                else:
                    seen[line_trim] = str(line_count)
            line_count += 1
        f.close()

    for value, lines in seen.items():
        if any(elem in "," for elem in lines):  # seen at least twice
            nb_errors += 1
            print(bcolors.WARNING + value + bcolors.ENDC +
                  " is duplicated at line(s) " + lines)


def find_duplicates_text():
    global nb_errors
    '''find duplicates in en_US, for only value ie key: value is duplicated at otherKey: value'''
    values = list_indexes().values()

    seen = {}

    for v in values:
        v_no_space = v.replace(" ", "")
        if v_no_space in seen.keys():
            seen[v_no_space] += 1
        else:
            seen[v_no_space] = 0

    for key, count in seen.items():
        if count > 0:
            nb_errors += 1
            print(bcolors.WARNING + key + bcolors.ENDC +
                  " is duplicated %s times " % (count))


def check_existing(raw_text):
    values = list_indexes()

    # trim & lowercase
    trimed = re.sub("\r?\n", "", raw_text)
    trimed = trimed.strip().lower()  # \t and spaces before and after

    if trimed in map(lambda v: v.lower(), values.values()):
        for k, v in values.items():
            if v.lower() == trimed:
                print("'%s' is already translated with key: %s" % (trimed, k))
                if confirm("Do you want to use it?", default=True):
                    return True, k
                break

    return False, None


def addMissingEntry(file, entryPath, entryKey, groupOrKey, entry):
    '''append an entry in a file'''
    success = False
    with open(file, "r+", encoding='utf8') as f_xx:
        data = json.load(f_xx)

        if isinstance(entryPath, str):
            if entryPath[-1] != ".":
                entryPath += "."  # we need the last dot for str formatting
            paths = entryPath[:-1].split(".")  # [:-1] is removing the last dot
        else:
            paths = entryPath.copy()
            entryPath = ".".join(paths) + "."

        # determine where to add entry
        whereToAdd = data
        for path in paths:
            if path not in whereToAdd:
                whereToAdd[path] = {}
            else:
                if isinstance(whereToAdd[path], str):
                    # already exists
                    print("%s: %s already exists with name " % (file, groupOrKey) +
                          bcolors.WARNING + entryPath + entryKey + bcolors.ENDC, flush=True)
            whereToAdd = whereToAdd[path]

        if entryKey in whereToAdd:
            # already exists
            print("%s: %s already exists with name " % (file, groupOrKey) +
                  bcolors.WARNING + entryPath + entryKey + bcolors.ENDC, flush=True)
        else:
            # actually adding the entry
            if groupOrKey == "group":
                whereToAdd[entryKey] = {}
            else:
                if entry is None:
                    entry = prompt("Translation in %s for %s%s" %
                                   (file, entryPath, entryKey))
                whereToAdd[entryKey] = entry
            f_xx.seek(0)  # go back to begin of file
            json.dump(data, f_xx, ensure_ascii=False,
                      indent=2)  # overwrite all
            print("%s: adding %s " % (file, groupOrKey) + bcolors.WARNING +
                  entryPath + entryKey + bcolors.ENDC, flush=True)
            success = True

        f_xx.close()
    return success


def removeUnusedEntry(index):
    '''delete entry in all files'''
    all_files = other_languages.copy()
    all_files.insert(0, en_file)

    for file in all_files:
        with open(file, "r+", encoding='utf8') as f_xx:
            data = json.load(f_xx)
            paths = index.split(".")
            key = paths.pop()
            whatToRemove = data['translation']
            for path in paths:
                whatToRemove = whatToRemove[path]

            del whatToRemove[key]

            f_xx.truncate(0)  # clear file to prevent mess
            f_xx.seek(0)  # go back to begin of file
            json.dump(data, f_xx, ensure_ascii=False,
                      indent=2)  # overwrite all
            print("%s: removing " % (file) + bcolors.WARNING +
                  index + bcolors.ENDC, flush=True)

            f_xx.close()


def verify_pars(reference, copies, path=""):
    '''crawl a dict of translations to verify if each key of reference is in copies'''
    global nb_errors, nb_corrected, edit

    for key, val in reference.items():
        if isinstance(val, str):
            for idx, one_copy in enumerate(copies):
                if not key in one_copy:
                    nb_errors += 1
                    if edit:
                        print("Translate: " + val)
                        success = addMissingEntry(
                            other_languages[idx], path, key, "key", None)
                        if not success:
                            nb_corrected += 1
                    else:
                        print(other_languages[idx] + ": missing translation for key " +
                              bcolors.WARNING + path + key + bcolors.ENDC, flush=True)
        else:
            rebuit_copies = []
            for idx, one_copy in enumerate(copies):
                if not key in one_copy:
                    nb_errors += 1

                    if edit:
                        success = addMissingEntry(
                            other_languages[idx], path, key, "group", None)
                        nb_corrected += 1
                        rebuit_copies.append({})
                    else:
                        print(other_languages[idx] + ": missing group " +
                              bcolors.WARNING + path + key + bcolors.ENDC, flush=True)
                else:
                    rebuit_copies.append(one_copy[key])
            verify_pars(val, rebuit_copies, path+key + ".")


def find_missing():
    '''find missing translations in other languages'''
    with open(en_file) as f_en:
        data_en = json.load(f_en)

        other_files = []
        for file in other_languages:
            with open(file) as f_xx:
                data = json.load(f_xx)
                other_files.append(data)
                f_xx.close()

        f_en.close()
        verify_pars(data_en, other_files)


def list_paths(reference, list, path=""):
    '''crawl a dict of translation to list all path in a json file'''
    for key, val in reference.items():
        if isinstance(val, str):
            list[path + key] = val
        else:
            list_paths(val, list, path+key + ".")


def list_indexes():
    '''build a list of all inputs in reference file'''
    indexes = {}
    with open(en_file) as f_en:
        data_en = json.load(f_en)
        list_paths(data_en['translation'], indexes)
        f_en.close()
    return indexes


def list_paths_groups(reference, list, path=""):
    '''crawl a dict of translation to list all path in a json file'''
    for key, val in reference.items():
        if not isinstance(val, str):
            list[key] = {}
            list_paths_groups(val, list[key], path+key + ".")


def list_indexes_groups():
    '''build a list of group inputs in reference file'''
    indexes = {}
    with open(en_file) as f_en:
        data_en = json.load(f_en)
        list_paths_groups(data_en['translation'], indexes)
        f_en.close()
    return indexes


def list_occurences():
    '''build a list of all translated text in the app'''
    # get all .ts and .html
    tsfiles = []
    for file in glob.glob(all_ts_files, recursive=True):
        tsfiles.append(file)
    htmlfiles = []
    for file in glob.glob(all_html_files, recursive=True):
        htmlfiles.append(file)

    # search for pattern {{'path' | i18next }} or i18next.t('path') or [text]="'path' | i18next"
    occured = set()
    tsMatches = []
    for tsfile in tsfiles:
        textfile = open(tsfile, 'r')
        filetext = textfile.read()
        textfile.close()
        tsMatches = re.findall("i18next\.t\([^\(\)]*\)", filetext)

        for match in tsMatches:
            occured.add(re.sub(" |'|\)|i18next.t\(", "", match))

    htmlMatches = []
    for htmlfile in htmlfiles:
        textfile = open(htmlfile, 'r')
        filetext = textfile.read()
        textfile.close()
        htmlMatches = re.findall("\'[\w|\.]*' ?\| ?i18next", filetext)

        for match in htmlMatches:
            occured.add(re.sub(" |'|\||i18next", "", match))

    return occured


def find_unused():
    '''find translations that are in json files but not used in html or ts'''
    global nb_errors, nb_corrected, unused_exceptions, edit
    json_indexes = list_indexes().keys()
    app_occurences = list_occurences()

    for index in json_indexes:
        if not index in app_occurences and not index in unused_exceptions:
            nb_errors += 1
            if edit:
                removeUnusedEntry(index)
                nb_corrected += 1
            else:
                print(bcolors.WARNING + index + bcolors.ENDC + " is not used")


def find_unfound():
    global nb_errors, nb_corrected, edit
    json_indexes = list_indexes().keys()
    app_occurences = list_occurences()

    for occurence in app_occurences:
        if not occurence in json_indexes:
            nb_errors += 1
            if edit:
                path = ("translation."+occurence).split('.')
                key = path.pop()
                all_files = other_languages.copy()
                all_files.insert(0, en_file)
                for file in all_files:
                    addMissingEntry(file, path, key, "key", None)
                    nb_corrected += 1
            else:
                print(bcolors.WARNING + occurence +
                      bcolors.ENDC + " is not translated")


def showHelp():
    print("\t--help | -h \tDisplays this help")
    print("\t--duplicate \tList all translations that are duplicated in english file. Use --deep for text based search")
    print("\t--missing \tList all translations that are present in english file but not in another")
    print("\t--unused \tList all translations that are present in english file but not in the app")
    print("\t--unfound \tList all translations that are present in the app but not in the english file")
    print("\t--plain \tList all plain texts that are present in the app and not using translation")
    print("\t--edit | -e\tAdd this option to a previous mode to fix translation errors")
    print("\t--sort \t\tRe-order translation files alphabetically. Done in edit mode anyways")


def choose_index(tag_content, htmlfile):
    index_groups = list_indexes_groups()

    print("Choose an index for plain text " + bcolors.OKBLUE +
          tag_content + bcolors.ENDC + " caught in file " + htmlfile)

    chosen_index_str = ""
    dig = True
    while(dig):
        choices = list(index_groups.keys())
        choices.sort()
        if len(choices) == 0:
            choices.insert(0, " + New index: use camelCase text as index")
        choices.insert(0, " + New index")
        questions = [
            inquirer.List('index',
                          message="Where to organize translation > %s" % (
                              chosen_index_str),
                          choices=choices,
                          ),
        ]

        chosen_index = inquirer.prompt(questions).get('index')
        print(chosen_index)
        if chosen_index == " + New index: use camelCase text as index":
            # clear text
            # dots (that are index separators) and new lines
            tag_content = re.sub("\r?\n|\.", "", tag_content)
            tag_content = tag_content.strip()  # \t and spaces before and after

            # camelise
            s = re.sub(r"(_|-)+", " ", tag_content).title().replace(" ", "")
            chosen_index_str += ''.join([s[0].lower(), s[1:]])
            dig = False
        elif chosen_index == " + New index":
            new_index = prompt("Type new index(es) dot separated")
            chosen_index_str += new_index
            dig = False
        else:
            chosen_index_str += chosen_index + '.'
            index_groups = index_groups.get(chosen_index)

    return chosen_index_str


def bind_plain(content, htmlfile, filetext, format, chosen_index, existing_index=False):

    if not existing_index:
        # write english translation file
        path = ("translation."+chosen_index).split('.')
        key = path.pop()
        addMissingEntry(en_file, path, key, "key", content)

    # edit html file
    the_file = open(htmlfile, 'w')

    if format == "betweenTags":
        filetext = re.sub(
            "> ?%s ?<" % (content), ">{{'%s' | i18next }}<" % (chosen_index), filetext)
    elif format == "placeholder":
        filetext = re.sub(
            'placeholder="%s"' % (content), '[placeholder]="\'%s\' | i18next "' % (chosen_index), filetext)

    the_file.write(filetext)
    the_file.close()
    print("%s: replacing '%s' by " % (htmlfile, content) +
          bcolors.WARNING + chosen_index + bcolors.ENDC, flush=True)
    return filetext


def find_plain():
    global nb_errors, nb_corrected, edit

    # get all .html
    htmlfiles = []
    for file in glob.glob(all_html_files, recursive=True):
        if file not in excluded_files:
            htmlfiles.append(file)

    # search for pattern {{'path' | i18next }} or i18next.t('path') or [text]="'path' | i18next"
    occured = list()
    for htmlfile in htmlfiles:
        textfile = open(htmlfile, 'r')
        filetext = textfile.read()
        textfile.close()

        tooltipMatches = re.findall(
            '[^\[] ?ngbTooltip ?[^\]] ?"([^"]*)"', filetext)
        for match in tooltipMatches:
            nb_errors += 1
            occured.append({
                "type": "tooltip",
                "file": htmlfile,
                "text": match
            })

        placeholderMatches = re.findall(
            '[^\[] ?placeholder ?[^\]] ?"([^"]*)"', filetext)
        for match in placeholderMatches:
            nb_errors += 1
            if edit:
                use_existing_index, existing_index = check_existing(
                    match)
                if existing_index is None:
                    chosen_index = choose_index(
                        match, htmlfile)
                else:
                    chosen_index = existing_index

                filetext = bind_plain(match, htmlfile,
                                      filetext, "placeholder", chosen_index, use_existing_index)
                nb_corrected += 1

            occured.append({
                "type": "placeholder",
                "file": htmlfile,
                "text": match
            })

        betweenTagsMatches = re.findall(
            '(?<=<)([^<]*)(?<=>)([\w\s\',\.;?!-]+)<\/([\w-]+)', filetext)
        # match group 0 is between html tags, match group 1 is the closing tag
        for match in betweenTagsMatches:
            tag_name = match[2]
            tag_content = match[1]
            previous_tag = match[0]
            if "sr-only" not in previous_tag and "visually-hidden" not in previous_tag:
                if not tag_name in exclude_tags:
                    no_spaces = re.sub(" |\r?\n|\t", "", tag_content)

                    if (len(no_spaces) > 0 and "i18next" not in no_spaces):
                        nb_errors += 1

                        if edit:
                            use_existing_index, existing_index = check_existing(
                                tag_content)
                            if existing_index is None:
                                chosen_index = choose_index(
                                    tag_content, htmlfile)
                            else:
                                chosen_index = existing_index

                            filetext = bind_plain(tag_content, htmlfile,
                                                  filetext, "betweenTags", chosen_index, use_existing_index)
                            nb_corrected += 1

                        occured.append({
                            "type": "tag <" + bcolors.OKCYAN + tag_name + bcolors.ENDC + "> content",
                            "file": htmlfile,
                            "text": tag_content
                        })

    for o in occured:
        if not edit:
            print(bcolors.WARNING + o["file"] + bcolors.ENDC + " the " + o["type"] +
                  " " + bcolors.OKBLUE + o["text"] + bcolors.ENDC + " is not translated")


def print_report():
    global nb_errors, nb_corrected, edit
    if nb_errors > 0:
        if edit:
            print(bcolors.OKGREEN + "Corrected " +
                  str(nb_corrected) + " on " + str(nb_errors) + " error(s) 💪" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + "Found " + str(nb_errors) +
                  " error(s) 👎" + bcolors.ENDC)
    else:
        print(bcolors.OKGREEN + "No errors found 👍" + bcolors.ENDC)


def sortedDeep(d):
    if isinstance(d, list):
        return sorted(sortedDeep(v) for v in d)
    if isinstance(d, dict):
        return {k: sortedDeep(d[k]) for k in sorted(d)}
    return d


def main():
    global edit
    args = sys.argv
    if '--help' in args or '-h' in args:
        showHelp()
    else:
        if len(args) > 2 and ('--edit' in args or '-e' in args):
            edit = True

        if len(args) == 1 or '--duplicate' in args:
            if '--deep' in args:
                print(bcolors.OKGREEN +
                      "\n#### DUPLICATED ENTRIES (DEEP) ####" + bcolors.ENDC)
                find_duplicates_text()
            else:
                print(bcolors.OKGREEN +
                      "\n#### DUPLICATED ENTRIES ####" + bcolors.ENDC)
                find_duplicates()
        if len(args) == 1 or '--missing' in args:
            print(bcolors.OKGREEN +
                  "\n#### MISSING TRANSLATIONS ####" + bcolors.ENDC)
            find_missing()
        if len(args) == 1 or '--unused' in args:
            print(bcolors.OKGREEN +
                  "\n#### UNUSED ENTRIES ####" + bcolors.ENDC)
            find_unused()  # translation in json files but not in html or ts
        if len(args) == 1 or '--unfound' in args:
            print(bcolors.OKGREEN +
                  "\n#### UNFOUND ENTRIES ####" + bcolors.ENDC)
            find_unfound()  # translation in html or ts files but not in json

        if len(args) == 1 or '--plain' in args:
            print(bcolors.OKGREEN +
                  "\n#### PLAIN TEXT IN PROJECT ####" + bcolors.ENDC)
            find_plain()  # plain text in project not translated

        if '--sort' in args or edit:
            all_files = other_languages.copy()
            all_files.insert(0, en_file)
            for file in all_files:
                with open(file, "r+", encoding='utf8') as f_xx:
                    data = json.load(f_xx)
                    ordered_data = sortedDeep(data)
                    f_xx.truncate(0)
                    f_xx.seek(0)
                    json.dump(ordered_data, f_xx, ensure_ascii=False,
                              indent=2)  # overwrite all
                    print("Sorted file %s" % (file), flush=True)

                    f_xx.close()

        print_report()


main()
if __name__ == "__madin__":
    try:
        main()
    except Exception as e:
        print(e)
        print(" -Interrupted")
        print_report()
        quit()
