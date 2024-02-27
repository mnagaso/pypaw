# Installing python dependencies

Pypaw has dependancies on the following packages:

1. [obspy](https://github.com/obspy/obspy)
2. [pytomo3d](https://github.com/wjlei1990/pytomo3d)
3. [hdf5-libray compiled with parallel support](https://www.hdfgroup.org/HDF5/)
4. [h5py](http://www.h5py.org/)
5. [mpi4py](https://mpi4py.scipy.org/docs/usrman/index.html)
6. [pyasdf](https://github.com/SeismicData/pyasdf)


## Manual installation

#### 1. load your compiler modules.
  You can choose any version you like(intel, gnu or pgi). But we are using GNU compiler on RHEA at ORNL.

  ```
  module load gcc/4.8.2
  module load openmpi/1.8.4
  ```

#### 2. downwnload Anaconda for Python 2.7 and 64 bit Linux and install it (http://continuum.io/downloads)(**optional**)

  Tips: If you are new to python, [anaconda](https://www.continuum.io/downloads) is recommmended. Please download the newest version( >= Anaconda2 - 2.5.0) since it already contains a lot of useful python packages, like pip, numpy and scipy.  Older versions is not recommended since it usually has compliers inside, like gfortran and gcc. It is always better to use comiplers coming from your system rather than the very old ones embeded in anaconda. If you are expert in python, please choose the way you like.

#### 3. uninstall all HDF5 and MPI related things.
  Those need to be recompiled to enable parallel I/O and use the MPI implementation of the current machine
  ```
  conda uninstall hdf5 h5py openmpi mpi4py
  ```

#### 4. load(or install) hdf5-parallel

  For large computing clusters, hdf5-parallel is usually pre-installed(or work as a module). So first you want to check if this library is pre-installed on your machine. If so, load the module and go to the next step. If not, you need to install hdf5-parallel yourself.  
  For some cases, even the hdf5-parallel is pre-installed on your machine, it might not work since it is not compiled with correct flags(shared library or so). If the system library doesn't work, install it yourself. For example, there is a module one tiger called `hdf5/intel-13.0/openmpi-1.8.8`. However, I could not use that since h5py fails on it. So I download hdf5 and compiled it myself.

  If you decided to install the library yourself, get it from this link: [https://www.hdfgroup.org/HDF5/release/obtainsrc.html](https://www.hdfgroup.org/HDF5/release/obtainsrc.html) or use command line:
  ```
  wget http://www.hdfgroup.org/ftp/HDF5/current/src/hdf5-1.8.16.tar
  tar -xvf hdf5-1.8.16.tar 
  ```

  Here is the instruction on how to build it up with parallel support: [https://www.hdfgroup.org/ftp/HDF5/current/src/unpacked/release_docs/INSTALL_parallel](https://www.hdfgroup.org/ftp/HDF5/current/src/unpacked/release_docs/INSTALL_parallel). Before installation, type in `which mpicc` to check your mpicc compiler

  A simple configure and compiled instruction:
  ```
  cd hdf5-1.8.16
  CC=mpicc ./configure --enable-fortran --enable-parallel --prefix=/path/to/hdf5/install/dir --enable-shared --enable-static
  make
  make install
  ```
  I found a very useful link to talk about how to install hdf5-parallel and h5py. It is here:
  ```
  http://alexis.praga.free.fr/computing/2014/04/02/rant-h5py.html
  ```


#### 5. prepare conda environment

Modify the line below in the `install_script.sh` to the path of your hdf5-parallel library
```
export HDF5_DIR=/path/to/hdf5/install/dir
```

then run the following command:

```
source ./install_script.sh
```

#### 6. then your conda environment should be ready to use as pypaw
