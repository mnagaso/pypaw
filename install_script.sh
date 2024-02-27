# pre-requisites:
# 1. Anaconda
# 2. git
# 3. mpi
# 4. HDF5 (parallel) installed
# (please check the INSTALL.md for more details)

export HDF5_DIR="/usr/lib/x86_64-linux-gnu/hdf5/openmpi/"

conda env create -f environment.yml
conda activate pypaw

CC=mpicc pip install --no-binary=mpi4py mpi4py #==3.1.2
#CC=mpicc HDF5_MPI=ON HDF5_DIR="$TACC_HDF5_DIR" pip install --no-binary=h5py h5py==3.5.0
#CC=mpicc HDF5_MPI=ON HDF5_DIR="$HDF5_DIR" pip install --no-binary=h5py h5py==3.5.0

## or from source
rm -rf ./h5py && git clone https://github.com/h5py/h5py.git && cd h5py && HDF5_MPI=ON CC=mpicc pip install . && cd .. && rm -rf h5py

pip install -e .