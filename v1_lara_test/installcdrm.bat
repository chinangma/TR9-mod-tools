

for %%I in (%3) do set ORIGINAL_SIZE=%%~zI
@echo %ORIGINAL_SIZE% 

for /f "tokens=2,3 delims=x_. " %%I in ("%3") do set "SectionNum=%%I"
@echo %SectionNum%

copy %3  tempfile.tmp
cdrm.exe tempfile.tmp
tr9tigetadd.exe %1 %2  %SectionNum%  "tempfile.tmp=%ORIGINAL_SIZE%" "%4"