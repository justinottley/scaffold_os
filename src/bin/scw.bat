@REM vc wrapper script for Windows
@echo off

IF "%1"=="--help" (
    __SCAFFOLD_PYTHON_BIN_SUBST__ __SCAFFOLD_INST_SUBST__\__SCAFFOLD_INST_VERSION__\bin\sc.py %*
) ELSE IF "%1"=="init" (
    @rem set "PYTHONPATH=__SCAFFOLD_PYTHONPATH_SUBST__;%PYTHONPATH%"
    @rem set "PATH=__SCAFFOLD_INST_SUBST__\__SCAFFOLD_INST_VERSION__\bin;%PATH%"
    for /f "usebackq tokens=*" %%a in (`__SCAFFOLD_PYTHON_BIN_SUBST__ __SCAFFOLD_INST_SUBST__\__SCAFFOLD_INST_VERSION__\bin\sc.py %*`) do %%a
) ELSE (
    __SCAFFOLD_PYTHON_BIN_SUBST__ __SCAFFOLD_INST_SUBST__\__SCAFFOLD_INST_VERSION__\bin\sc.py %*
)
