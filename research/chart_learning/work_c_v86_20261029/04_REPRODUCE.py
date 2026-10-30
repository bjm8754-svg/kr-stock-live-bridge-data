#!/usr/bin/env python3
"""Read-only audit of the frozen Work C evidence; never generates new grades.

Usage: python3 04_REPRODUCE.py --root WORKDIR --evidence 03_EVIDENCE.json \
    --frozen 01_INDEPENDENT_FROZEN.md

Extract the original public stage ZIPs separately into WORKDIR/stages/V86_Sxx;
B into WORKDIR/workb/v86_work_b_final_frozen; decrypted A/reference and audit into
WORKDIR/private/V86_SEALED_REFERENCE and WORKDIR/private/V86_PRIVATE_AUDIT.
Keep original B/SEALED/PRIVATE ZIPs in WORKDIR/inputs, public ZIPs in public_inputs.
Decryption is deliberately outside this script. No keys, network, orders, account,
portfolio, fills, profits, or statistical skill certification are created.
Float tolerance reconciles the supplied source representations; it is not a tick rule.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

EXPECTED_B = [
 'cbe95b885aad97c725c89c27afc43a06745d69b21c72cb3c6b84b54df2830aec',
 '15f57b4796068580e03ec3e2c8dc16a5ee7b8b0ab31c6a2e30c580926fc311a2',
 'b5a1132dd33a3f6d65917100a707989dc395990e009a777579d500e42943354c',
 'fc6e687bbeb6ee47767e721f307b538b5f94c71f5a656036be0ae20faddfa719',
 '5abd6838e8dce7ccb1b845099500907935594551fab326159988f79950eca6d2',
 '45ccdec01a7960445352e3ebb92fad40832b5ae7868f75ff3d448fafa4ade2e4',
 '3d20959983175215442d709e24b553f9d3729c424065c0272e9accdf2984c9ca',
]
FROZEN_SHA = '626700d333ceb18d88dc09fa69a8053c5d0287a68f212c75dc253b01a858782b'
# Transcribed from B's immutable plans before computing quote-event results.
CONTRACTS = '''
S00 Q02 100 98.104265 94.786730 105.687204 105.687204,108.530806
S00 Q05 100 95.480226 95.480226 103.389831 103.389831,105.084746
S00 Q07 100 98.562300 95.207668 105.750799 105.750799,109.584665
S01 Q01 108.805031 107.547170 105.031447 113.836478 116.037736,118.867925
S01 Q02 107.582938 105.687204 104.739336 113.744076 113.744076,115.165877
S01 Q04 97.798742 94.025157 88.259958 104.612159 104.612159,106.289308
S01 Q07 103.035144 101.757188 100.319489 109.584665 109.584665,111.821086
S01 Q08 108.154506 106.008584 104.721030 114.592275 114.592275,118.025751
S02 Q02 103.317536 100.947867 99.052133 106.161137 106.161137,108.056872
S02 Q04 85.953878 84.067086 82.809224 90.251572 90.251572,93.710692
S02 Q06 118.046133 115.468114 110.176391 127.544098 127.544098,130.936228
S02 Q08 113.733906 112.875536 108.154506 120.171674 120.171674,123.605150
S02 Q09 91.926803 90.850377 87.405813 97.201292 97.201292,99.677072,102.475780
S02 Q10 83.946488 81.382386 79.487179 90.858417 90.858417,94.871795
S03 Q01 103.459119 103.144654 101.572327 111.949686 111.949686,113.836478,116.037736
S03 Q07 93.769968 92.332268 91.693291 97.763578 97.763578,98.562300
S03 Q09 102.475780 100.430571 97.524220 107.319699 107.319699,110.656620
S03 Q10 84.169454 83.612040 82.051282 90.858417 90.858417,91.638796,94.871795
S04 Q01 110.691824 107.547170 103.773585 116.352201 116.352201,118.238994
S04 Q02 82.559242 81.421801 79.336493 87.393365 87.393365,90.047393
S04 Q05 87.288136 85.028249 84.745763 91.807910 91.807910,92.372881,94.915254
S04 Q07 94.568690 95.047923 92.651757 97.763578 97.763578,98.402556,98.562300
S04 Q08 121.030043 120.171674 118.884120 126.180258 126.180258,127.896996,130.042918
S05 Q01 119.496855 118.867925 111.949686 125.786164 125.786164,128.301887
S05 Q04 102.410901 101.048218 95.073375 112.578616 112.578616
S05 Q10 65.774805 63.433668 60.200669 70.234114 70.234114,73.578595,75.473802
'''

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_json(p):
    return json.loads(p.read_text(encoding='utf-8'))

def rows(p):
    with p.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def require(ok, label):
    if not ok:
        raise ValueError(label)

def close(a, b):
    return abs(float(a) - float(b)) < 1e-7

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--evidence', type=Path, default=Path(__file__).with_name('03_EVIDENCE.json'))
    p.add_argument('--frozen', type=Path, default=Path(__file__).with_name('01_INDEPENDENT_FROZEN.md'))
    args = p.parse_args()
    root = args.root.resolve()
    evidence = read_json(args.evidence)
    require(sha(args.frozen) == FROZEN_SHA, 'independent frozen report changed')
    require(evidence['frozenReportSha256'] == FROZEN_SHA, 'evidence freeze reference differs')
    ea = evidence['inputAndRiskAudit']
    sealed = root / 'private/V86_SEALED_REFERENCE'
    private = root / 'private/V86_PRIVATE_AUDIT'
    bbase = root / 'workb/v86_work_b_final_frozen'
    require(sha(root/'inputs/V86_WorkB_S00_S06_FINAL_FROZEN_20261029.zip') == ea['BZipSha256'], 'B ZIP changed')
    for name, field in [('V86_SEALED_REFERENCE.zip','sealedZipSha256'), ('V86_PRIVATE_AUDIT.zip','privateAuditZipSha256')]:
        require(sha(root/'inputs'/name) == evidence['postUnsealAudit'][field], name+' changed')
    manifests = {}
    for label, directory in [('sealed',sealed), ('audit',private)]:
        m = read_json(directory/'FILE_SHA256.json')
        require(all(sha(directory/f) == v for f,v in m.items()), label+' manifest mismatch')
        manifests[label] = len(m)
    prior = {}
    total_public_files = 0
    for i in range(7):
        stage = f'S{i:02}'
        public = root/'stages'/f'V86_{stage}'
        answer = bbase/'answers'/f'{stage}_answers.json'
        require(sha(answer) == EXPECTED_B[i], stage+' answer changed')
        bd = read_json(answer)
        require(len(bd['cases']) == 10, stage+' B case count')
        sm = ea['stages'][i]
        require(sha(root/'public_inputs'/f'V86_{stage}_INPUT_ONLY.zip') == sm['publicZipSha256'], stage+' public ZIP changed')
        m = read_json(public/'INPUT_MANIFEST.json')
        require(all(sha(public/f) == v for f,v in m.items()), stage+' public manifest mismatch')
        total_public_files += len(m)
        bm = bbase/'stage_records'/stage/('INPUT_MANIFEST.json' if i==0 else f'INPUT_MANIFEST_{stage}.json')
        require(sha(bm) == sha(public/'INPUT_MANIFEST.json'), stage+' B input manifest mismatch')
        for qi in range(1,11):
            q = f'Q{qi:02}'
            data = rows(public/q/'DAILY.csv')
            require(max(int(x['t']) for x in data) == 20*i, stage+q+' cutoff')
            if q in prior:
                require(data[:len(prior[q])] == prior[q], stage+q+' prefix changed')
            prior[q] = data
            allrows = rows(sealed/q/'ALL_NORMALIZED.csv')
            by = {int(x['t']):x for x in allrows}
            for x in data:
                y = by[int(x['t'])]
                for field in ['Open','High','Low','Close','Volume']:
                    require(bool(x[field]) == bool(y.get(field)), stage+q+' missing quote mismatch')
                    if x[field]:
                        require(close(x[field],y[field]), stage+q+' normalized quote mismatch')
            ref = read_json(sealed/q/stage/'PREFIX_REFERENCE_EVIDENCE.json')
            anchors = ref['lastLowPivots']+ref['lastHighPivots']+ref['allPivotsLast130']
            require(all(x['knownT'] <= 20*i and x['sourceT'] <= 20*i for x in anchors), stage+q+' future pivot')
            ar = read_json(sealed/q/stage/'FINAL_AUTHOR_REFERENCE.json')
            er = next(x for x in evidence['comparisons70'] if x['stage']==stage and x['caseId']==q)
            require(er['AFlatFamily'] == ar['curatorPrimaryFlatFamily'], stage+q+' A flat mismatch')
            require(er['AProbeFamily'] == ar['curatorHoldingFamily'], stage+q+' A holding mismatch')
            require(er['ARationale'] == ar['rationale'], stage+q+' A rationale mismatch')
            br = next(x for x in evidence['independentRows'] if x['stage']==stage and x['caseId']==q)
            original = next(x for x in bd['cases'] if x['caseId']==q)
            require(br['flatAction']==original['flat']['action'] and br['probeAction']==original['holding_probe']['action'], stage+q+' B action mismatch')
            require(br['remainingUnits']==original['holding_probe']['remainingUnits'], stage+q+' B quantity mismatch')
            require(er['finalFlatVerdict']==br['flatVerdict'] and er['finalProbeVerdict']==br['probeVerdict'], stage+q+' independent grade overwritten')
            nxt = [x for x in allrows if 20*i<int(x['t'])<=20*i+20]
            if not nxt:
                require(i==6 and er['next20Quotes'] is None, stage+q+' future absence mismatch')
            else:
                actual = {'low':min(float(x['Low']) for x in nxt if x['Low']),
                          'high':max(float(x['High']) for x in nxt if x['High']),
                          'endClose':float(nxt[-1]['Close'])}
                for k,v in actual.items():
                    require(close(v,er['next20Quotes'][k]) and close(v,ar['next20ActualQuotes_AUTHOR_ONLY'][k]), stage+q+' next20 mismatch')
    for r in ea['riskRecalculations']:
        tf = 'WEEKLY' if r['Ibar'].startswith('W') else 'DAILY'
        src = rows(root/'stages'/f"V86_{r['stage']}"/r['caseId']/(tf+'.csv'))
        bar = next(x for x in src if x['barId']==r['Ibar'])
        require(any(bar[k] and close(bar[k],r['I']) for k in ['Open','High','Low','Close']), 'risk boundary mismatch')
        risk = r['q']*(max(r['P']-r['I'],0)+.006*r['P'])
        require(close(risk,r['recomputedRisk']) and risk<=5+1e-8, 'risk equation/budget mismatch')
    recomputed = []
    for line in CONTRACTS.strip().splitlines():
        stage,q,entry,stop,emergency,upper,targets = line.split()
        cut = int(stage[1:])*20
        src = rows(root/'stages'/f'V86_{stage}'/q/'DAILY.csv')
        vals = [float(r[k]) for r in src for k in ['Open','High','Low','Close'] if r[k]]
        def anchor(x):
            v = float(x)
            near = min(vals,key=lambda y:abs(y-v))
            require(abs(near-v)<.00000051, 'transcribed threshold lacks source anchor')
            return near
        entry,stop,emergency,upper = map(anchor,[entry,stop,emergency,upper])
        targets = [anchor(x) for x in targets.split(',')]
        future = [r for r in rows(sealed/q/'ALL_NORMALIZED.csv') if cut<int(r['t'])<=cut+20]
        def first(fn):
            return next((int(r['t']) for r in future if fn(r)),None)
        eps = 1e-8
        limit = first(lambda r:r['Low'] and float(r['Low'])<=entry+eps)
        up = first(lambda r:r['High'] and float(r['High'])>=upper-eps)
        cf = first(lambda r:float(r['Close'])<stop-eps)
        ef = first(lambda r:r['Low'] and float(r['Low'])<=emergency+eps)
        ob = first(lambda r:r['Open'] and float(r['Open'])<=emergency+eps)
        cancels = [x for x in [up,cf,ef] if x is not None]
        if limit is None:
            status = 'NO_LIMIT_ACCESS_IN_NEXT20'
        elif any(x<limit for x in cancels):
            status = 'CANCEL_BEFORE_LATER_LIMIT_ACCESS'
        elif ef==limit and any(int(r['t'])==limit and r['Open'] and emergency<float(r['Open'])<=entry+eps for r in future):
            status = 'OPEN_ACCESS_THEN_INTRADAY_FAILURE_NO_FILL_PROOF'
        elif up==limit or ef==limit:
            status = 'SAME_BAR_ORDERING_OR_EXECUTION_UNRESOLVED'
        else:
            status = 'LIMIT_PRICE_ACCESS_BEFORE_CANCEL_NOT_FILL_PROOF'
        hits = [first(lambda r,p=p:r['High'] and float(r['High'])>=p-eps) for p in targets]
        r = {'stage':stage,'caseId':q,'entryAnchor':entry,'closeFailureAnchor':stop,
             'emergencyAnchor':emergency,'upperCancelAnchor':upper,'firstLimitAccessT':limit,
             'firstUpperCancelT':up,'firstCloseFailureT':cf,'firstEmergencyT':ef,
             'firstOpenAtOrBelowEmergencyT':ob,'targetAnchors':targets,
             'firstTargetQuoteAccessT':hits,'quoteClassification':status,'notActualTrades':True}
        expected = next(x for x in evidence['buyContractQuoteEvents26'] if x['stage']==stage and x['caseId']==q)
        require(r == expected, stage+q+' quote-event record mismatch')
        recomputed.append(r)
    order = collections.Counter(x['quoteClassification'] for x in recomputed)
    outcomes = collections.Counter()
    for r in recomputed:
        if r['quoteClassification'] not in ['LIMIT_PRICE_ACCESS_BEFORE_CANCEL_NOT_FILL_PROOF','OPEN_ACCESS_THEN_INTRADAY_FAILURE_NO_FILL_PROOF']:
            continue
        failures = [x for x in [r['firstCloseFailureT'],r['firstEmergencyT']] if x is not None]
        f = min(failures) if failures else float('inf')
        t = r['firstTargetQuoteAccessT'][0] or float('inf')
        outcomes['target_first' if t<f else 'failure_first' if f<t else 'unresolved'] += 1
    require(dict(outcomes)=={'target_first':7,'failure_first':9}, 'aggregate order mismatch')
    print(json.dumps({'status':'PASS','readOnly':True,'publicManifestItems':total_public_files,
                      'privateManifestItems':manifests,'caseStagePrefixes':70,'next20Windows':60,
                      'riskRecalculations':len(ea['riskRecalculations']),
                      'buyContracts':len(recomputed),'quoteAccessClasses':dict(order),
                      'afterPriorAccessEventOrder':dict(outcomes),
                      'gradingRegenerated':False,'fillsOrReturnsCalculated':False},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
