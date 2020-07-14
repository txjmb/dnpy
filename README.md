# dnpy
A Python wrapper around the excellent [opendnp3](https://github.com/dnp3/opendnp3) project using [Cppyy](https://cppyy.readthedocs.io/en/latest/index.html).

The opendnp library includes wrappers for Java and .NET Framework (not .NET Core/Standard yet) within the repo.  Several years ago, Chargepoint developed a wrapper for Python as a separate project called [pydnp3](https://github.com/ChargePoint/pydnp3).

Pydnp3 uses pybind11 to wrap the c++ classes.  Unfortunately, pydnp3 has gone very stale and is limited by the capabilities of pybind11, that have caused some unfortunate lack of functionality.

[dnpy](https://github.com/txjmb/dnpy) seeks to wrap the opendnp3 library using a different approach, namely the wonderful [Cppyy](https://cppyy.readthedocs.io/en/latest/index.html) project.  Cppyy offers a number of advantages over pybind11.  It is actively developed by members of the CERN team (Wim Lavrijsen primary developer) for high energy physics projects, and dynamically generates wrappers by inspecting header files, rather than custom coding of wrapper classes.  It can handle modern c++ language and compiler features and has a number of performance enhancements that make it superior to pybind11 in many ways.  It is also compatible with PyPy

When a new version of opendnp3 comes out, such as the much-improved 3.x versions, it is a simple matter to update any project to use the new c++ code, without any code required (although some pythonizations may be desired).

Currently, this project has not been set up to install the cppyy wrapper as a package.  This will be abstracted out into a separate project called cppyy-opendnp3 soon.  In the meantime, this project does runtime generation of the wrapper, so there is a minor startup speed cost.

# Dependencies
## opendnp3
opendnp3 is included in the repo as a submodule
### update it:

```
git submodule update --recursive --remote
```

### build it:
```
cd deps/opendnp3
mkdir build
cd build
cmake ..
make -j
```

## Latest **cppyy** (1.8 as of last writing)
You can [install](https://cppyy.readthedocs.io/en/latest/installation.html) cppyy in a number of ways, including through conda forge.  You can also [build from source](https://cppyy.readthedocs.io/en/latest/repositories.html).  It's probably not a bad idea to build from source at least once to become familiar with the way cppyy works and its dependencies.

Briefly, here's how you build from source (although you should always reference cppyy docs).

### cling (from cppyy-backend repo)
```
git clone https://bitbucket.org/wlav/cppyy-backend.git
cd cppyy-backend/cling
python setup.py egg_info
python create_src_directory.py
python -m pip install . --upgrade # this takes a while
cd ../..
```

### cppyy-backend
```
cd cppyy-backend/clingwrapper
python -m pip install . --upgrade
cd ../..
```

### CPyCppyy (if using CPython, not needed for PyPy)
```
git clone https://bitbucket.org/wlav/CPyCppyy.git
cd CPyCppyy
python -m pip install . --upgrade
cd ../..
```

### cppyy
```
git clone https://bitbucket.org/wlav/cppyy.git
cd cppyy
python -m pip install . --upgrade
```

# Testing/running
setup_cppy.py loads the Allheaders.h file into cppyy and points cppyy to the built opendnp3 library.

The examples can be run from the examples directory.  There is a master and an outstation example, with each having a \_cmd.py wrapper for interactive testing.  These were adapted from the pydnp3 library.  

They are not 100% functional as of yet, although most of the basic functions have been tested.  Callbacks with templated functions are the main challenge right now.  Users are welcome to document issues here in this repo.  If the issue appears to be one with cppyy, the developer there is very responsive and helpful:  [cppyy issues](https://bitbucket.org/wlav/cppyy/issues?status=new&status=open).  Assistance in getting the packaging process for the generated bindings to work so that a new wrapper repo can be created and published to PyPi would be very appreciated.  Info on packaging using CMake is available [here](https://cppyy.readthedocs.io/en/latest/cmake_interface.html).  Example repos and articles:

* https://github.com/camillescott/cookiecutter-cppyy-cmake
* https://www.camillescott.org/2019/04/11/cmake-cppyy/
* https://gitlab.com/coopr/coek/tree/cppyy
* https://github.com/camillescott/cppyy-bbhash
* https://bitbucket.org/wlav/cppyy/issues/76/binding-generation-issue-on-ubuntu1604
