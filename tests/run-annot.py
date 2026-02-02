from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from tempfile import mkdtemp

tmpPath = mkdtemp()
siteId = "PDBE_TEST"

print(tmpPath)
of = "annot-link-4pdr.gz"
inppath = "/home/wbueno/repos/onedep/py-wwpdb_utils_dp/wwpdb/mock-data/MODELS/4pdr.cif"

dp = RcsbDpUtility(tmpPath=tmpPath, siteId=siteId, verbose=True)
dp.pdbe_cluster_queue = "highpri"
dp.imp(inppath)
dp.op("annot-cis-peptide")
dp.expLog("annot-cis-peptide.log")
dp.exp(of)
dp.cleanup()

# ---

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from tempfile import mkdtemp

tmpPath = mkdtemp()
siteId = "PDBE_TEST"

print(tmpPath)
of = "annot-link-4pdr.gz"
cifPath = "4pdr.cif"

dp = RcsbDpUtility(tmpPath=tmpPath, siteId=siteId, verbose=True)
dp.pdbe_cluster_queue = "highpri"
dp.imp(cifPath)
dp.op("check-cif")
dp.exp("check-cif-diags.txt")
dp.expLog("check-cif.log")

