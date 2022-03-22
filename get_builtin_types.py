import argparse
import subprocess
import re
from collections import defaultdict
from io import StringIO

"""
This script extracts names of built-in types, variables, and functions from the
Swift standard library, and is used to generate the regular expressions used in
the grammar to match these built-in names.
"""


# Ported from https://github.com/textmate/bundle-development.tmbundle/blob/master/Commands/Optimize%20Regex%20Alternations.tmCommand
def optimize_alternations(strs):
  buckets = defaultdict(list)
  optional = False
  for s in sorted(strs):
    if not s:
      optional = True
    else:
      buckets[s[0]].append(s[1:])

  if buckets:
    ptrns = [key + optimize_alternations(value) for key, value in buckets.items()]
    if optional:
      return "(?:" + "|".join(ptrns) + ")?"
    elif len(ptrns) > 1:
      return "(?:" + "|".join(ptrns) + ")"
    else:
      return ptrns[0]

  return ""


def get_builtins(name, contents):
  contents = re.sub(r"^(\s*)(?:@[\w_():'\", ]+\s+)*(class|struct|protocol|extension) ((?:\w+\.)*_\w+).+\{$(.*\n)*?^\1\}$", "\n", contents, flags=re.MULTILINE)
  types = {
    match.group(1)
    for match in re.finditer(r"^(?:@[\w_():'\", ]+\s+)*(?!class var|class func)(?:class|struct|actor|protocol|enum|typealias) ([^_]\w*)\b", contents, flags=re.MULTILINE)
  }
  types.add('UnorderedRange')
  print(f'===== {name} TYPES =====')
  print(optimize_alternations(types))
  print()
  
  nested_types = {
    match.group(1)
    for match in re.finditer(r"^ +(?:@[\w_():'\", ]+ +)*(?!class var|class func)(?:class|struct|actor|protocol|enum|typealias) ([^_]\w*)\b", contents, flags=re.MULTILINE)
  }
  print(f'===== {name} NESTED TYPES =====')
  print(optimize_alternations(nested_types))
  print()
    
  constants = {
    match.group(2)
    for match in re.finditer(r"^(?:@[\w_():'\", ]+ +)*(?:class )?(?:var|let) (`?)([^_]\w*)\1", contents, flags=re.MULTILINE)
  }
  print(f'===== {name} CONSTANTS =====')
  print(optimize_alternations(constants))
  print()
    
  properties = {
    match.group(2)
    for match in re.finditer(r"^ +(?:@[\w_():'\", ]+ +)*(?:class )?(?:var|let|case) (`?)([^_]\w*)\1", contents, flags=re.MULTILINE)
  }
  print(f'===== {name} PROPERTIES/CASES =====')
  print(optimize_alternations(properties))
  print()
    
  funcs = {
    match.group(2)
    for match in re.finditer(r"^(?:@[\w_():'\", ]+ +)*func (`?)((?!_)\w+)\1", contents, flags=re.MULTILINE)
    if "@_silgen_name" not in match.group(0)
  }
  funcs -= {
    "KEY_TYPE_OF_DICTIONARY_VIOLATES_HASHABLE_REQUIREMENTS",
    "ELEMENT_TYPE_OF_SET_VIOLATES_HASHABLE_REQUIREMENTS",
    "unimplemented_utf8_32bit",
  }
  print(f'===== {name} TOP-LEVEL FUNCTIONS =====')
  print(optimize_alternations(funcs))
  print()
    
  member_funcs = {
    match.group(2)
    for match in re.finditer(r"^ +(?:@[\w_():'\", ]+ +)*func (`?)((?!_)\w+)\1", contents, flags=re.MULTILINE)
  }
  print(f'===== {name} MEMBER FUNCTIONS =====')
  print(optimize_alternations(member_funcs))
  print()

def main():
  swift_mod = subprocess.check_output("swift", input=b":type lookup Swift").decode()
  get_builtins("Swift", swift_mod)
  # foundation_mod = subprocess.check_output("swift", input=b"import Foundation\n:type lookup Foundation").decode()
  # get_builtins("Foundation", foundation_mod)

if __name__ == "__main__":
  main()


