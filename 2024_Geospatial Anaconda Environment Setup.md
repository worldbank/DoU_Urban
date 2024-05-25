his is a short walkthrough on setting up a *generic* geospatial analysis Anaconda environment on your  machine.

This also installs the Jupyter Notebook software commonly used for Python (and other) development tasks.

Please let Marziya Farooq (mfarooq1@worldbank.org) know if any changes are required!

-----------------------------------

1. Install Anaconda
2. Open Anaconda Powershell

3. Run the following commands *in this order*

conda create --name geoenv python=3.11.8
conda activate geoenv

conda install -n base conda-libmamba-solver

conda install vs2015_runtime=14 --solver=libmamba

conda install -c conda-forge geopandas rasterio geojson pycrs regex numpy --solver=libmamba

conda install dask

pip install xarray-spatial

pip install GOSTRocks

pip install rioxarray openpyxl

pip install pytest-warnings
