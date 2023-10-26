

rem patch000.tiger is in the parent directory of this bat file 

rem covert dds to pcd9

for %%I in (*.dds) do dds2pcd9.exe "%%I"

rem install all pcd9 and mesh files

for %%I in  (*.pcd9 *.mesh) do call installcdrm.bat . cine_v1_lara.drm "%%I" ../patch.000.tiger
pause