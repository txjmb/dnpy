import cppyy
import os
olddir = os.getcwd()
os.chdir("..")
cppyy.add_include_path("deps/opendnp3/cpp/libs/include")
cppyy.add_include_path("deps/opendnp3/deps/asio/asio/include")
cppyy.load_library("deps/opendnp3/build/libopenpal.so")
cppyy.load_library("deps/opendnp3/build/libopendnp3.so")
cppyy.load_library("deps/opendnp3/build/libasiopal.so")
cppyy.load_library("deps/opendnp3/build/libasiodnp3.so")

cppyy.include("AllHeaders.h")
os.chdir(olddir)