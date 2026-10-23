"""Image provenance and legacy anchor sensitivity; never reads market prices/orders."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image

def main():
    ap=argparse.ArgumentParser();ap.add_argument('uploaded_jpeg');ap.add_argument('derived_png');ap.add_argument('--out',required=True);a=ap.parse_args()
    j,p=Path(a.uploaded_jpeg),Path(a.derived_png)
    native=Image.open(j).convert('RGB');derived=Image.open(p).convert('RGB')
    assert native.size==(709,1536) and derived.size==(1418,920)
    transformed=native.resize((1418,3072),Image.Resampling.BICUBIC).crop((0,1080,1418,2000))
    x,y=np.asarray(transformed).astype(int),np.asarray(derived).astype(int);d=np.abs(x-y)
    points={'A':(118.,593.),'B':(280.,568.),'C':(534.,519.)};probe_x,probe_y=1175.,414.
    alternatives=[]
    for first,second in [('A','B'),('A','C'),('B','C')]:
        x1,y1=points[first];x2,y2=points[second];slope=(y2-y1)/(x2-x1);projection=y1+slope*(probe_x-x1)
        alternatives.append({'anchors':[first,second],'screenSlope':slope,'projectedScreenY':projection,'sameProjectionInUploadedJpegY':(projection+1080)/2,'approxLatestPriceSide':'ABOVE_LINE' if probe_y<projection else 'BELOW_LINE','secondAnchorPlus5ScreenYProjectionEffect':5*(probe_x-x1)/(x2-x1)})
    output={'scope':'SOURCE_PIXEL_DIAGNOSTIC_ONLY_NOT_MARKET_OR_TRANSFER_TEST','transformation':{'resize':'BICUBIC2x1418x3072','crop':[0,1080,1418,2000],'screenToUploadedCoordinates':'x_native=x/2;y_native=(y+1080)/2'},'files':[{'filename':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [j,p]],'meanAbsoluteRgbError':float(np.mean(d)),'maxAbsoluteRgbError':int(np.max(d)),'exactMatchingPixelFraction':float(np.mean(np.all(d==0,axis=2))),'differentPixelCount':int(np.sum(np.any(d!=0,axis=2))),'interiorPlotRectangle':[20,90,1300,890],'interiorPlotExactlyEqual':bool(np.array_equal(x[90:890,20:1300],y[90:890,20:1300])),'legacyApproximateBoxCenters':points,'approximateLatestScreenProbe':[probe_x,probe_y],'pointOrigin':'Previously published CHANNEL_ANCHOR_SENSITIVITY_20261021;box centers,not wick/body OHLC;already outcome-exposed','alternatives':alternatives,'newMarketDataFetched':False,'newNativeDetailRecovered':False,'drawingTimeVerified':False,'actualCompletedBarVerified':False,'predictiveValueVerified':False}
    Path(a.out).write_text(json.dumps(output,indent=2)+'\n')

if __name__=='__main__':main()
