import rasterio, numpy as np
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
URL='/vsicurl/https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dtm_16bit_cog.tif'
ENV=dict(GDAL_HTTP_UNSAFESSL='YES', GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_HTTP_MULTIRANGE='YES', GDAL_HTTP_MERGE_CONSECUTIVE_RANGES='YES', VSI_CACHE='TRUE')
def read(e0,n0,e1,n1,res):
    """read area [e0,e1]x[n0,n1] at pixel size res (m) -> array north-up"""
    with rasterio.Env(**ENV):
        with rasterio.open(URL) as d:
            w=from_bounds(e0,n0,e1,n1,d.transform)
            ow=int(round((e1-e0)/res)); oh=int(round((n1-n0)/res))
            a=d.read(1,window=w,out_shape=(oh,ow),resampling=Resampling.average if res>1 else Resampling.bilinear,masked=True)
            return a

from scipy.ndimage import uniform_filter, map_coordinates
def fine_grid(Ec,Nc,half=750,step=7.5,m=8):
    e0,e1,n0,n1=Ec-half-m,Ec+half+m,Nc-half-m,Nc+half+m
    a=read(e0,n0,e1,n1,1)
    nod=np.ma.getmaskarray(a); arr=a.astype(np.float64).filled(np.nan)
    # fill nodata with nearest-ish via local mean
    if nod.any():
        from scipy.ndimage import distance_transform_edt
        idx=distance_transform_edt(nod,return_distances=False,return_indices=True)
        arr=arr[tuple(idx)]
    sm=uniform_filter(arr,size=8,mode='nearest')
    n=int(round(2*half/step))+1
    xs=np.arange(n)*step-half  # east offsets
    zs=np.arange(n)*step-half  # z: south positive; row 0 = north (z=-half)
    # pixel coords: col = (Ec+x - e0) - 0.5 ; row = (n1 - (Nc - z)) - 0.5
    X,Z=np.meshgrid(xs,zs)
    cols=(Ec+X-e0)-0.5; rows=(n1-(Nc-Z))-0.5
    g=map_coordinates(sm,[rows,cols],order=1,mode='nearest')
    return g.astype(np.float32), float(nod.mean())
def coarse_grid(Ec,Nc,half=6000,step=60):
    n=int(round(2*half/step))+1
    a=read(Ec-half-step/2,Nc-half-step/2,Ec+half+step/2,Nc+half+step/2,step)
    nod=np.ma.getmaskarray(a); arr=a.filled(0).astype(np.float32)
    return arr, float(nod.mean())
