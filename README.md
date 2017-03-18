# Agora curation module
Reference implementation of an ML-based crowd curation module using Python

# Status
Currently requires a bit more testing code to be written in order to test all
parts of the curation module to ensure they work

# Prerequisites
Make sure you have installed:  
1. sqlite3
2. Python 2.6+
3. numpy
4. scipy
5. scikit-learn
6. PyInstaller

# Building
```
./install.sh
```
You will find the binary `main` in the `dist` folder.
This is the main executable.

# Run tests on curation integration
```
./test.sh
```
