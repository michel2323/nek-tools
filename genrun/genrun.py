#!/home/maxhutch/anaconda3/bin/python
##!/usr/bin/env python3

from sys import argv
from os import system
from os import path
import shutil
import argparse
import json
from mesh import Mesh

''' Loading stuff '''
parser = argparse.ArgumentParser(description="Generate NEK inputs")
parser.add_argument('name', help="Name to assign to generated system")
parser.add_argument('-d', '--dict', dest='config', help="Dictionary of parametesr (JSON)")
parser.add_argument('-u', '--usr', dest='usr', help="*.usr file to use for build")
parser.add_argument('-n', '--nproc', dest='np', type=int, default=-1, help="Number of processes to target")
parser.add_argument('-l', '--legacy', dest='legacy', default=False, action="store_true", help="Legacy Nek5000 support (instead of NekBox)")
parser.add_argument('--map', dest='map', default=False, action="store_true", help="Make a map file.  genmap if legacy, internal otherwise.")
parser.add_argument('--makenek', dest='makenek', default="makenek", help="Path to makenek")
parser.add_argument('--clean', dest='clean', default=False, action="store_true", help="Clean before making")
parser.add_argument('--tdir', dest='tdir', default='.',  help="Directory to build in")
parser.add_argument('--no-make', dest='make', default=True, action="store_false", help="Don't run makenek")
parser.add_argument('--override', dest='override', type=json.loads, default={}, help="JSON overrides")

args = parser.parse_args()
mypath = (path.realpath(__file__))[:-9]

with open(path.join(mypath, "default.json"), "r") as f:
  default_config = json.load(f)

loaded_config = {}
if args.config != None:
  with open(args.config, 'r') as f:
    loaded_config = json.load(f)

config = dict(list(default_config.items()) + list(loaded_config.items()) + list(args.override.items()))

from os.path import exists
from os import makedirs
if not exists(args.tdir):
    makedirs(args.tdir)

with open("{:s}/{:s}.json".format(args.tdir, args.name), "w") as f:
  json.dump(config, f, indent=2)

''' Computing stuff '''

# loads the configuration into current variable scope
locals().update(config)

dealiasing_order = order * 3 / 2

# Manipulate the configuration here
elements_total = shape_mesh[0] * shape_mesh[1] * shape_mesh[2]

if args.np > 0: 
  procs = args.np

if left_bound == 'P':
  left_boundv = 'P'

if right_bound == 'P':
  right_boundv = 'P'

if front_bound == 'P':
  front_boundv = 'P'

if back_bound == 'P':
  back_boundv = 'P'

if top_bound == 'P':
  top_boundv = 'P'

if bottom_bound == 'P':
  bottom_boundv = 'P'

if args.legacy:
    if left_boundv == 'T':
        left_boundv = 't'
    if right_boundv == 'T':
        right_boundv = 't'
    if front_boundv == 'T':
        front_boundv = 't'
    if back_boundv == 'T':
        back_boundv = 't'
    if top_boundv == 'T':
        top_boundv = 't'
    if bottom_boundv == 'T':
        bottom_boundv = 't'

# genbox and genmap
msh = Mesh(root_mesh, extent_mesh, shape_mesh, [left_bound, front_bound, right_bound, back_bound, top_bound, bottom_bound])
if args.map:
  msh.generate_elements()

#mesh_data = msh.get_mesh_data()
#msh.generate_faces()
#fluid_boundaries = msh.get_fluid_boundaries()
#thermal_boundaries = fluid_boundaries.replace('SYM', 'I  ').replace('W  ', 'I  ')

if args.map:
  msh.set_map(procs)
  map_data = msh.get_map()
else:
  if left_bound == 'P':
    map0 = shape_mesh[0]
  else:
    map0 = -shape_mesh[0]
  if front_bound == 'P':
    map1 = shape_mesh[1]
  else:
    map1 = -shape_mesh[1]
  if top_bound == 'P':
    map2 = shape_mesh[2]
  else:
    map2 = -shape_mesh[2]

  map_data = "{:d} 0 {:d} {:d} {:d} 0 0\n".format(
              elements_total, 
              map0,
              map1,
              map2)

# writes the current variable scope to the configuration
config = locals()

''' Writing stuff '''

with open(path.join(mypath, "template.SIZE"), "r") as f:
  size_template = f.read()
size = size_template.format(**config)
with open("{:s}/SIZE".format(args.tdir), "w") as f:
  f.write(size)

with open(path.join(mypath, "template.size_mod"), "r") as f:
  size_template = f.read()
size = size_template.format(**config)
with open("{:s}/size_mod.F90".format(args.tdir), "w") as f:
  f.write(size)
import os
print("In {:s}\n".format(os.getcwd()))
print("Wrote size_mod.F90 to {:s}/size_mod.F90\n".format(args.tdir))

with open(path.join(mypath, "template.rea"), "r") as f:
  rea_template = f.read()
rea = rea_template.format(**config)
with open("{:s}/{:s}.rea".format(args.tdir, args.name), "w") as f:
  f.write(rea)

with open(path.join(mypath, "template.box"), "r") as f:
  box_template = f.read()
box = box_template.format(**config)
with open("{:s}/{:s}.box".format(args.tdir, args.name), "w") as f:
  f.write(box)

with open("{:s}/{:s}.map".format(args.tdir, args.name), "w") as f:
  f.write(map_data) 

if args.usr != None:
  with open(args.usr, "r") as f:
    usr_template = f.read()
  usr = usr_template.format(**config)
  with open("{:s}/{:s}.usr".format(args.tdir, args.name), "w") as f:
    f.write(usr)

if args.legacy:
  from os import chdir
  chdir(args.tdir)
  shutil.copy("./{:s}.rea".format(args.name), "./tmp.rea".format(args.name))
  system("echo './{:s}.box' | genbox".format(args.name))
  shutil.copy("./box.rea", "./{:s}.rea".format(args.name))
  #shutil.copy("box.re2", args.name+".re2")
  if not args.map:
    with open(".tmp", "w") as f:
      f.write("{:s}\n0.05\n".format(args.name))
    system("genmap < .tmp")
  #chdir('..')

from subprocess import call
from os.path import dirname
#from os import chdir
#chdir(args.tdir)
if args.clean:
  cmd = [args.makenek, "clean" , dirname(args.makenek)]
  call(cmd)
if args.make:
  cmd = [args.makenek, args.name, dirname(args.makenek)]
  if args.tdir == '.':
    call(cmd)
  else:
    call(cmd, cwd=args.tdir)

