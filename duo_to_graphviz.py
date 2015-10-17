#!/usr/bin/python3

# Either download the API courses list from https://incubator.duolingo.com/api/1/courses/list
# and run the script with the file as the first argument
# or run it with no arguments and it will try to download the course data automatically

# If you are going to try out the filtering options, then go easy on Duo's API.
# Download the data and then use it locally
# ./duo_to_graphviz.py --download > list
# ./duo_to_graphviz.py list <options>

# for more options run: ./duo_to_graphviz.py -h

# use results with graphviz: ./duo_to_graphviz.py | circo -Tpng -o courses.png


def download_api_data():
    import requests
    return requests.get('https://incubator.duolingo.com/api/1/courses/list')

def get_api_data():
    fp = download_api_data()
    return fp.json()

def get_file_data(f):
    import json
    with open(f) as fp:
      data = json.load(fp)
    return data

def parse_json(data,source,dest,phases):
    colours = {1:'red', 2:'yellow', 3:'green'}

    course_data = filter(lambda cd: cd[0] in phases and
                                    (data['languages'][cd[1]]['name'].upper() == source or not source) and
                                    (data['languages'][cd[2]]['name'].upper() == dest or not dest),
                                    [(a['phase'],a['from_language_id'],a['learning_language_id']) for a in data['directions']])

    courses = {}
    for (phase, from_lang, to_lang) in sorted(course_data):
        if phase not in courses.keys():
            courses[phase] = {}
        if from_lang not in courses[phase].keys():
            courses[phase][from_lang] = []
        courses[phase][from_lang].append(to_lang)

    print('digraph G {')
    print('  rankdir=LR;')
    print('  overlap=false;')

    for phase in courses.keys():
        print('\n  edge [color={}]'.format(colours[phase]))

        for from_lang in sorted(courses[phase]):
            print('  "{}" -> {{ '.format(data['languages'][from_lang]['name']), end='')
            for to_lang in sorted(courses[phase][from_lang]):
                print('"{}" '.format(data['languages'][to_lang]['name']), end='')

            print('};')
    print('}')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Process Duolingo course data into a dot file for graphviz')
    parser.add_argument('filename', nargs='?', help='Name of the file with the Duolingo course data. Requests current data from the Duolino API if ommitted')
    parser.add_argument('-s','--source_language', default='', help='Filter to only show courses from the SOURCE_LANGUAGE')
    parser.add_argument('-d','--dest_language', default='', help='Filter to only show courses to the DEST_LANGUAGE')
    parser.add_argument('-p','--phase', nargs='*', type=int, default=[1,2,3], choices=[1,2,3], help='Only show courses in the selected phase(s)')
    parser.add_argument('--download', default='', action='store_const', const='Y', help='Download and display the API data for easy output to a file')
    args = parser.parse_args()

    if args.download == 'Y':
      print(download_api_data().text)
    elif args.filename:
        #try to open the file specified on the command line
        parse_json(get_file_data(args.filename),args.source_language.upper(),args.dest_language.upper(),args.phase)
    else:
        #grab the latest course data from the API
        parse_json(get_api_data(),args.source_language,args.dest_language,args.phase)
