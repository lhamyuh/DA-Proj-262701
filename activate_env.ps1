# activate_env.ps1 — 每次开新终端先执行一次
# 用途：设置 GDAL / PROJ 数据路径（消除 gdalvrt.xsd 警告），并打印关键库版本。
# 用法：在项目根目录执行  .\activate_env.ps1
# 说明：不改动 conda 环境本身，只影响当前 PowerShell 会话。

$EnvRoot = "D:\miniconda3\envs\ev311"

if (-not (Test-Path "$EnvRoot\python.exe")) {
    Write-Host "[FAIL] 未找到环境：$EnvRoot" -ForegroundColor Red
    return
}

$env:PATH = "$EnvRoot;$EnvRoot\Library\mingw-w64\bin;$EnvRoot\Library\usr\bin;$EnvRoot\Library\bin;$EnvRoot\Scripts;$env:PATH"

# 关键：Intel MKL 的线程层在本机会硬崩溃（0xC06D007F），必须设为 SEQUENTIAL。
# 症状：np.corrcoef / np.dot / matplotlib 绘图 / 部分 pandas 分组调用时进程直接消失，无 traceback。
$env:MKL_THREADING_LAYER = "SEQUENTIAL"
$env:KMP_DUPLICATE_LIB_OK = "TRUE"

$gdal = "$EnvRoot\Library\share\gdal"
$proj = "$EnvRoot\Library\share\proj"
if (Test-Path $gdal) { $env:GDAL_DATA = $gdal } else { Write-Host "[warn] 未找到 $gdal" -ForegroundColor Yellow }
if (Test-Path $proj) { $env:PROJ_LIB = $proj } else { Write-Host "[warn] 未找到 $proj" -ForegroundColor Yellow }

Write-Host "GDAL_DATA = $env:GDAL_DATA"
Write-Host "PROJ_LIB  = $env:PROJ_LIB"

# 版本自检：任一导入失败会直接暴露出来
& "$EnvRoot\python.exe" -c "import sys,geopandas,rasterio,rasterstats,pandas,numpy,pyarrow;print('env ok | python',sys.version.split()[0],'| gpd',geopandas.__version__,'| rasterio',rasterio.__version__,'| rasterstats',rasterstats.__version__,'| pandas',pandas.__version__,'| numpy',numpy.__version__)"
