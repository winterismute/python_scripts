# Download the API courses list from https://incubator.duolingo.com/api/1/courses/list
# use results with graphviz: dot -Tpng -O duo.dot

import json

fp = open("duo_courses.txt")
c = json.load(fp)
fp.close()

print()

phases = {1:"red", 2:"orange", 3:"green"}
map = {1:{},2:{},3:{}}

for (p, f, t) in [(a["phase"],a["from_language_id"],a["learning_language_id"]) for a in c["directions"]]:
  if f in map[p].keys():
    map[p][f].append(t)
  else:
    map[p][f] = [t]

print("digraph G {")
print("  rankdir=LR;")
print("  overlap=false;")

for p in [1,2,3]:
  print()
  print("  edge [color={}]".format(phases[p]))
  for k in map[p].keys():
    print("  \"{}\" -> {{".format(c["languages"][k]["name"]), end="")
    for l in map[p][k]:
      print("\"{}\" ".format(c["languages"][l]["name"]), end="")
    print("}; ")
print("}")