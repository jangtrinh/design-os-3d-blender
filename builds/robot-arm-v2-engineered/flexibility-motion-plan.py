"""Large, continuous joint sweeps with deliberate endpoint holds; degrees."""
import math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# Source timing is compressed from60 to40seconds while retaining all endpoint holds.
anchors=[(1,[0,0,0,0,0,-16]),(24,[0,0,0,0,0,-16]),
 (96,[0,90,0,0,0,-16]),(112,[0,90,0,0,0,-16]),
 (256,[0,-100,0,0,0,-16]),(272,[0,-100,0,0,0,-16]),
 (344,[0,0,0,0,0,-16]),(360,[0,0,0,0,0,-16]),
 (432,[0,0,-130,0,0,-16]),(448,[0,0,-130,0,0,-16]),
 (552,[0,0,85,0,0,-16]),(568,[0,0,85,0,0,-16]),
 (624,[0,35,0,0,0,-16]),(696,[180,35,0,0,0,-16]),
 (708,[180,35,0,0,0,-16]),(840,[-180,35,0,0,0,-16]),
 (852,[-180,35,0,0,0,-16]),(924,[0,35,0,0,0,-16]),
 (984,[0,35,0,0,180,-16]),(996,[0,35,0,0,180,-16]),
 (1116,[0,35,0,0,-180,-16]),(1128,[0,35,0,0,-180,-16]),
 (1188,[0,35,0,0,0,-16]),(1248,[0,35,0,30,0,-16]),
 (1260,[0,35,0,30,0,-16]),(1332,[0,35,0,-15,0,-16]),
 (1344,[0,35,0,-15,0,-16]),(1392,[0,0,0,0,0,12]),
 (1404,[0,0,0,0,0,12]),(1440,[0,0,0,0,0,-16])]
anchors=[(max(1,round(f*2/3)),p) for f,p in anchors]
frames=[];segment=0
for frame in range(1,961):
    while segment+1<len(anchors)-1 and frame>anchors[segment+1][0]:segment+=1
    a,p=anchors[segment];b,q=anchors[segment+1]
    u=max(0,min(1,(frame-a)/(b-a)));u=u*u*(3-2*u)
    frames.append({'frame':frame,'degrees':[x+(y-x)*u for x,y in zip(p,q)]})
chapters=[(1,'01 / DUOI THANG LEN'),(17,'02 / VUON NGANG'),(76,'03 / VONG QUA DINH - RA SAU'),
 (183,'04 / GAP KHUYU HAI PHIA'),(380,'05 / XOAY DE +/-180'),
 (617,'06 / XOAY CO TAY +/-180'),(794,'07 / GAP CO TAY + DONG NGAM')]
result={'fps':24,'frame_count':960,'duration_seconds':40,'anchors':anchors,'chapters':chapters,'frames':frames,
 'scope':'Geometric CAD travel demonstration. These are selected screened ranges, not vendor mechanical stops or load-rated limits. Base/wrist turn once and unwind; cable routing unmodeled.'}
(ROOT/'reports/flexibility-motion-plan.json').write_text(json.dumps(result,indent=2))
print('AGENT_OK motion plan',len(frames))
