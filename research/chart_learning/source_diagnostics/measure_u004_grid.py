"""Measure drawn-line geometry in one archived screenshot; never fetch market data.
Requires Pillow/numpy. Input is ORIGINAL 1000061012.jpg; no images are uploaded.
Manual intercept bands target already visually identified guides, so this is not
an independent line-discovery algorithm or a forecast-performance test.
Usage: python measure_u004_grid.py IMAGE --out OUTPUT_JSON
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image

def measure(path):
    raw = path.read_bytes()
    im = np.array(Image.open(path).convert("RGB")).astype(int)
    if im.shape[:2] != (1536, 709):
        raise ValueError("Expected original 709x1536 screenshot; do not reuse bands on a resized crop")
    labels = ["1352000","1309000","1269000","1228000","1188000","1144000","1103000","1060000","1019000"]
    centers = [832,891,950,1008,1066,1124,1182,1240,1298]
    xs = np.arange(70,581)
    runs = []
    for threshold in (100,145,180):
        mask = (im.max(2)<threshold) & ((im.max(2)-im.min(2))<35)
        lines = []
        for label, center in zip(labels,centers):
            best = (-1.0,0.0,0.0)
            for slope in np.arange(.04,.0751,.001):
                for intercept in np.arange(center-7,center+7.1,.5):
                    yy = np.round(intercept+slope*xs).astype(int)
                    score = float(np.mean(np.max(np.stack([mask[yy+k,xs] for k in (-1,0,1)]),axis=0)))
                    if score>best[0]:
                        best = (score,float(slope),float(intercept))
            score,a,b = best
            lines.append(dict(sourceLabel=label,pixelSlopeYPerX=round(a,3),yAtX300=round(b+a*300,2),darkPixelCoverage=round(score,3)))
        gaps = np.diff([x["yAtX300"] for x in lines])
        runs.append(dict(threshold=threshold,lines=lines,adjacentGapsAtX300=[round(float(x),2) for x in gaps],medianGap=round(float(np.median(gaps)),2)))
    return dict(schema="U004_SOURCE_GRID_DIAGNOSTIC_V1",sourceFilename="1000061012.jpg",sha256=hashlib.sha256(raw).hexdigest(),imageSize=[709,1536],coordinates="Original top-left pixels; compare all lines at x=300",method="Manual line bands +/-7px, x=70..580, slopes .040..075 step .001; neutral dark pixels within +/-1px",runs=runs,interpretation="Near-parallel/equal-spacing source geometry only; not a price-formation rule or proof of the author's software",limitations=["Manually constrained bands, not unbiased line detection","Pixel spacing does not certify arithmetic price spacing or linear/log axis","Dotted guides have lower coverage than solid guides; JPEG/labels/candles interfere","No OHLCV, completed-bar times, drawing times, fills, profits or independent cases"])
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("image",type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    args.out.write_text(json.dumps(measure(args.image),indent=2)+"\n")

