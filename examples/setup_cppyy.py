import cppyy
import os
olddir = os.getcwd()
os.chdir("..")
#cppyy.add_include_path("deps/opendnp3/cpp/lib/include/")
cppyy.load_library("deps/opendnp3/build/cpp/lib/libopendnp3.so")
cppyy.include("AllHeaders.h")
os.chdir(olddir)