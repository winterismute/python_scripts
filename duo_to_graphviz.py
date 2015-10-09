#!/usr/bin/python3

# Either download the API courses list from https://incubator.duolingo.com/api/1/courses/list
# and run the script with the file as the first argument
# or run it with no arguments and it will try to download the course data automatically

# use results with graphviz: ./duo_to_graphviz.py | circo -Tpng -o courses.png


def get_api_data():
  import requests
  fp = requests.get('https://incubator.duolingo.com/api/1/courses/list')
  return fp.json()

def get_file_data(f):
  import json
  fp = open(f)
  return json.load(fp)

def parse_json(data):
  phases = {1:"red", 2:"yellow", 3:"green"}
  map = {1:{},2:{},3:{}}

  for (phase, from_lang, to_lang) in [(a["phase"],a["from_language_id"],a["learning_language_id"]) for a in data["directions"]]:
    if from_lang not in map[phase].keys():
      map[phase][from_lang] = []
    map[phase][from_lang].append(to_lang)

  print("digraph G {")
  print("  rankdir=LR;")
  print("  overlap=false;")

  for phase in [1,2,3]:
    print("\n  edge [color={}]".format(phases[phase]))
    for from_lang in sorted(map[phase].keys()):
      print("  \"{}\" -> {{ ".format(data["languages"][from_lang]["name"]), end="")
      for to_lang in sorted(map[phase][from_lang]):
        print("\"{}\" ".format(data["languages"][to_lang]["name"]), end="")
      print("};")
  print("}")

if __name__ == '__main__':
  import sys
  if len(sys.argv) > 1:
    #try to open the file specified on the command line
    parse_json(get_file_data(sys.argv[1]))
  else:
    #grab the latest course data from the API
    parse_json(get_api_data())
