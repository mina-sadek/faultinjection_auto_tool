import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

# SCOPETYPE = 'OPENADC'
# # PLATFORM = 'CW308_SAM4S'
# PLATFORM = 'CWLITEXMEGA'
# SS_VER = 'SS_VER_2_1'


# %run "/home/tornado/chipwhisperer/jupyter/Setup_Scripts/Setup_Generic.ipynb"
filename = 'setupXMEGA.ipynb'
with open(filename) as ff:
    nb_in = nbformat.read(ff, nbformat.NO_CONVERT)
ep = ExecutePreprocessor(timeout=600, kernel_name='python')
nb_out = ep.preprocess(nb_in)
print(nb_out)



