# pre-requisites:
# 1. Anaconda
# 2. git
# 3. mpi
# 4. HDF5 (parallel) installed
# (please check the INSTALL.md for more details)

# check cpu architecture
arch_type=$(uname -m)

# export for some general installation, but still need to check the path by yourself
#export HDF5_DIR="/usr/lib/${arch_type}-linux-gnu/hdf5/openmpi/"
export HDF5_DIR="/opt/apps/intel19/impi19_0/phdf5/1.10.4/x86_64/"

# modify PATH to prioritize miniconda3 path
CONDA_bin="/home1/09793/mnagaso/miniconda3/bin"
#CONDA_dir = conda info | grep "env location" | cut -d ":" -f 2
export PATH="$CONDA_bin:$PATH"

# make sure that PYTHONPATH is empty (module load command may add some path)
export PYTHONPATH=""

conda env create -f environment.yml
#conda env create -f environment_frontera.yml
conda activate pypaw

CC=mpicc pip install --no-binary=mpi4py mpi4py #==3.1.2
#CC=mpicc HDF5_MPI=ON HDF5_DIR="$TACC_HDF5_DIR" pip install --no-binary=h5py h5py==3.5.0
#CC=mpicc HDF5_MPI=ON HDF5_DIR="$HDF5_DIR" pip install --no-binary=h5py h5py==3.5.0

## or from source
rm -rf ./h5py && git clone https://github.com/h5py/h5py.git && cd h5py && HDF5_MPI=ON CC=mpicc pip install . && cd .. && rm -rf h5py

pip install -e .
