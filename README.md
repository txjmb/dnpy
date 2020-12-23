# dnpy
A Python wrapper around the excellent [opendnp3](https://github.com/dnp3/opendnp3) project using [Cppyy](https://cppyy.readthedocs.io/en/latest/index.html).

The opendnp library includes wrappers for Java and .NET Framework (not .NET Core/Standard yet) within the repo.  Several years ago, Chargepoint developed a wrapper for Python as a separate project called [pydnp3](https://github.com/ChargePoint/pydnp3).

Pydnp3 uses pybind11 to wrap the c++ classes.  Unfortunately, pydnp3 has gone very stale and is limited by the capabilities of pybind11, that have caused some unfortunate lack of functionality.

[dnpy](https://github.com/txjmb/dnpy) seeks to wrap the opendnp3 library using a different approach, namely the wonderful [Cppyy](https://cppyy.readthedocs.io/en/latest/index.html) project.  Cppyy offers a number of advantages over pybind11 although it is not a good fit for every wrapper project.  It is actively developed by members of the CERN team (Wim Lavrijsen primary developer) for high energy physics projects, and dynamically generates wrappers by inspecting header files, rather than custom coding of wrapper classes.  It can handle modern c++ language and compiler features and has a number of performance enhancements over other approaches.  There is a memory cost to the cppyy approach.  One can expect around a ~100MB memory overhead.  If that's a problem for a particular project, another approach may work better.  There are a lot of perhaps unexpected benefits to using cppyy that should be considered.  It would be a good idea to read [philosophy](https://cppyy.readthedocs.io/en/latest/philosophy.html) behind cppyy to understand all of the pros and cons.

There is a memory cost to the cppyy approach.  One can expect around a ~100MB overhead.  If that's a problem for a particular project, another approach may work better.  There are a lot of perhaps unexpected benefits to using cppyy that should be considered.  It would be a good idea to read [philosophy](https://cppyy.readthedocs.io/en/latest/philosophy.html) behind cppyy to understand all of the pros and cons.

Of course, one of the main advantages is that no binding coding is required when a new version of opendnp3 comes out with api changes, such as the recent much-improved 3.x versions of opendnp3.  It is a simple matter to update any project to use new c++ code. Since the bindings automatically generate based on the C++ API, Python code using those bindings still may need to change to reflect API changes, and some pythonizations may be desired.

The project has not been uploaded to PiPy yet, although it does build into a distributable package, so that will happen soon once additional testing has been done.  Users who want to assist in testing are welcome!

# Dependencies
## opendnp3
opendnp3 is included in the repo as a submodule
### update it:

```
git submodule update --recursive --remote
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

### build and install dnpy and opendnp3 package
```
mkdir build
cd build
cmake ..
make -j
make install
cd ..
pip install build/dist/dnpy-0.2-py3-none-linux_x86_64.whl
```

# Testing/running

The examples can be run from the examples directory.  There is a master and an outstation example, with each having a \_cmd.py wrapper for interactive testing.  These were adapted from the pydnp3 library.  

They are not 100% functional as of yet, although most of the basic functions have been tested.  Callbacks with templated functions are the main challenge right now.  Users are welcome to document issues here in this repo.  If the issue appears to be one with cppyy, the developer there is very responsive and helpful:  [cppyy issues](https://bitbucket.org/wlav/cppyy/issues?status=new&status=open).  Assistance in getting the packaging process for the generated bindings to work so that a new wrapper repo can be created and published to PyPi would be very appreciated.  Info on packaging using CMake is available [here](https://cppyy.readthedocs.io/en/latest/cmake_interface.html).  Example repos and articles related to packaging using CMake for those who want to try to figure this out:

* https://github.com/camillescott/cookiecutter-cppyy-cmake
* https://www.camillescott.org/2019/04/11/cmake-cppyy/
* https://gitlab.com/coopr/coek/tree/cppyy
* https://github.com/camillescott/cppyy-bbhash
* https://bitbucket.org/wlav/cppyy/issues/76/binding-generation-issue-on-ubuntu1604
* https://github.com/camillescott/cppyy-knn

[![Build Status](https://travis-ci.org/txjmb/cppyy_opendnp3.svg?branch=master)](https://travis-ci.org/txjmb/cppyy_opendnp3)

This project is set of Python bindings for opendnp3 using
[cppyy](https://bitbucket.org/wlav/cppyy/src/master/). The project template comes from [camillescott's cookiecutter recipe](https://github.com/camillescott/cookiecutter-cppyy-cmake), in which the CMake sources are based on the bundled cppyy CMake modules, with a number of improvements and changes:

- `genreflex` and a selection XML are use instead of a direct `rootcling` invocation. This makes
    name selection much easier.
- Python package files are generated using template files. This allows them to be customized for the
    particular library being wrapped.
- The python package is more complete: it includes a MANIFEST, LICENSE, and README; it properly
    recognizes submodules; it includes a tests submodule for bindings tests; it directly copies a
    python module file and directory structure for its pure python code.
- The cppyy initializor routine has basic support for packaging cppyy pythonizors. These are stored
    in the pythonizors/ submodule, in files of the form `pythonize_*.py`. The pythonizor routines
    themselves should be named `pythonize_<NAMESPACE>_*.py`, where `<NAMESPACE>` refers to the
    namespace the pythonizor will be added to in the `cppyy.py.add_pythonization` call. These will
    be automatically found and added by the initializor.

## Repo Structure

- `CMakeLists.txt`: The CMake file for bindings generation.
- `selection.xml`:  The genreflex selection file.
- `interface.hh`:   The interface header used by genreflex. Should include the headers and template
    declarations desired in the bindings.
- `cmake/`: CMake files for the build. Should not need to be modified.
- `pkg_templates/`: Templates for the generated python package. Users can modify the templates to
    their liking; they will be configured and copied into the build and package directory.
- `py/`: Python package structure that will be copied into the generated package. Add any pure
    python code you'd like include in your bindings package here.
- `py/initializor.py`: The cppyy bindings initializor that will be copied in the package. Do not
    delete!
