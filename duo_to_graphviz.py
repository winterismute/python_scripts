# Download the API courses list from https://incubator.duolingo.com/api/1/courses/list
# use results with graphviz: dot -Tpng -O duo.dot

import json

fp = open("duo_courses.txt")
c = json.load(fp)
fp.close()

phases = {1:"red", 2:"yellow", 3:"green"}
map = {1:{},2:{},3:{}}

for (phase, from_lang, to_lang) in [(a["phase"],a["from_language_id"],a["learning_language_id"]) for a in c["directions"]]:
  if from_lang not in map[phase].keys():
    map[phase][from_lang] = []
  map[phase][from_lang].append(to_lang)

print("digraph G {")
print("  rankdir=LR;")
print("  overlap=false;")

for phase in [1,2,3]:
  print("\n  edge [color={}]".format(phases[phase]))
  for from_lang in sorted(map[phase].keys()):
    print("  \"{}\" -> {{ ".format(c["languages"][from_lang]["name"]), end="")
    for to_lang in sorted(map[phase][from_lang]):
      print("\"{}\" ".format(c["languages"][to_lang]["name"]), end="")
    print("};")
print("}")

