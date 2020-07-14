# dnpy
A Python wrapper around the excellent [opendnp3](https://github.com/dnp3/opendnp3) project using [Cppyy].

The opendnpy library includes wrappers for Java and .NET Framework (not .NET Core/Standard yet).  Chargepoint subsequently developed a wrapper for Python as a separate project called pydnp3 https://github.com/ChargePoint/pydnp3.

This project uses pybind11 to wrap the c++ classes.  Unfortunately, this project has gone very stale and is limited by the capabilities of pybind11, that have caused some unfortunate lack of functionality.

This project, dnpy seeks to wrap the opendnp3 library using a different approach, namely the wonderful cppyy project.  cppyy offers a number of advantages over pybind11.  It is actively developed and dynamically generates wrappers by inspecting header files.  It can handle modern c++ compiler features and has a number of performance enhancements.

When a new version of opendnp3 comes out, such as the 3.x versions, it is a simple matter to update any project to use the new c++ code, without any code required (although some pythonizations may be desired).

Currently, this project has not been set up to install the cppyy wrapper as a package.  This will be abstracted out into a separate project called cppyy-opendnp3 soon.

#Dependencies
Latest cppyy (1.8 as of last writing)
You can [install](https://cppyy.readthedocs.io/en/latest/installation.html) cppyy in a number of ways, including through conda forge.  You can also [build from source](https://cppyy.readthedocs.io/en/latest/repositories.html)
