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

def filter_languages(data, languages, source, dest, phases):

    include_sources = [l for l in source if l[0] != '~']
    exclude_sources = [l[1:] for l in source if l[0] == '~']

    include_destinations = [l for l in dest if l[0] != '~']
    exclude_destinations = [l[1:] for l in dest if l[0] == '~']

    course_data = filter(lambda cd: cd.phase in phases and
                             ((len(include_sources) == 0 or languages[cd.source].upper() in include_sources) and
                              (languages[cd.source].upper() not in exclude_sources)) and
                             ((len(include_destinations) == 0 or languages[cd.dest].upper() in include_destinations) and
                              (languages[cd.dest].upper() not in exclude_destinations)),
                             data)
    return course_data

def parse_json(course_data, languages, colours):

    courses = {}
    for course in sorted(course_data):
        if course.phase not in courses:
            courses[course.phase] = {}
        if course.source not in courses[course.phase]:
            courses[course.phase][course.source] = []
        courses[course.phase][course.source].append(course.dest)

    print('digraph G {')
    print('  rankdir=LR;')
    print('  overlap=false;')

    for (phase,sources) in courses.items():
        print('\n  edge [color={}]'.format(colours[phase]))

        for (source, dests) in sorted(sources.items()):
            print('  "{}" -> {{ '.format(languages[source]), end='')

            for dest in sorted(dests):
                print('"{}" '.format(languages[dest]), end='')

            print('};')
    print('}')

def get_arguments():
    import argparse
    parser = argparse.ArgumentParser(description='Process Duolingo course data into a dot file for graphviz')
    parser.add_argument('filename', nargs='?', help='Name of the file with the Duolingo course data. Requests current data from the Duolino API if ommitted')
    parser.add_argument('-s','--source_language', nargs='*', default='', type=str, help='Filter to only show courses from the SOURCE_LANGUAGE. Prefix with a "~" to exclude the language instead')
    parser.add_argument('-d','--dest_language', nargs='*', default='', type=str, help='Filter to only show courses to the DEST_LANGUAGE. Prefix with a "~" to exclude the language instead')
    parser.add_argument('-p','--phase', nargs='*', type=int, default=[1,2,3], choices=[1,2,3], help='Only show courses in the selected phase(s)')
    parser.add_argument('--download', default='', action='store_const', const='Y', help='Download and display the API data for easy output to a file')
    parser.add_argument('-c','--colours', nargs=3, type=str, default=['red','yellow','green'], help='Choose alternate colours for phase 1, 2 and 3')
    return parser.parse_args()

def main():
    args = get_arguments()

    data = None
    if args.download == 'Y':
        print(download_api_data().text)
        return

    if not args.filename:
      #grab the latest course data from the API
      data = get_api_data()
    else:
      data = get_file_data(args.filename)

    if args.download == 'Y':
      print(data.text)

    else:
        languages = {code:details['name'] for (code,details) in data['languages'].items()}

        from collections import namedtuple
        Language = namedtuple('Language', ['phase', 'source', 'dest'])

        course_data = [Language(direction['phase'],direction['from_language_id'],direction['learning_language_id'])
                            for direction in data['directions']]
        course_data = filter_languages(course_data,
                            languages,
                            list(map(str.upper, args.source_language)),
                            list(map(str.upper, args.dest_language)),
                            args.phase)

        colours = {phase:colour for (phase, colour) in zip([1,2,3], args.colours)}

        parse_json(course_data, languages, colours)

if __name__ == '__main__':
    main()
