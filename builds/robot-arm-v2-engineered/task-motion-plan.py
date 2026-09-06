"""Pick, inspect, transfer and stack: geometric targets derived from the actual hand."""
from pathlib import Path
import math,json
ROOT=Path(__file__).resolve().parent
D=math.pi/180;L1=.111;L2=.137
# Grip the thin edge of a20x28x8mm workpiece at the upper part of the72mm pad.
GRIP=[.01448,.024,.076];SIDE_Y=.047+GRIP[0];SIDE_X=.1585;SIDE_Z=.017
def side_target(a,b,yaw):
    x=L1*math.sin(a*D)+L2*math.sin((a+b)*D)+SIDE_X
    z=.119+L1*math.cos(a*D)+L2*math.cos((a+b)*D)+SIDE_Z
    c=math.cos(yaw*D);s=math.sin(yaw*D)
    return [x*c-SIDE_Y*s,x*s+SIDE_Y*c,z]
def side_ik(point,jaw=-16):
    x,y,z=point;r=math.hypot(x,y);rad=math.sqrt(r*r-SIDE_Y*SIDE_Y)
    yaw=math.atan2(y,x)-math.atan2(SIDE_Y,rad)
    u=rad-SIDE_X;v=z-.119-SIDE_Z
    cosine=(u*u+v*v-L1*L1-L2*L2)/(2*L1*L2)
    assert -1<=cosine<=1,(point,cosine)
    b=math.acos(cosine);a=math.atan2(u,v)-math.atan2(L2*math.sin(b),L1+L2*math.cos(b))
    result=[yaw/D,a/D,b/D,90-(a+b)/D,90,jaw]
    assert -15.01<=result[3]<=30.01,result
    return result
def above(p,h):return [p[0],p[1],p[2]+h]
def lifted(p):
    scale=1-.045/math.hypot(p[0],p[1])
    return [p[0]*scale,p[1]*scale,p[2]+.10]
A=side_target(83,22,-28);B=side_target(83,22,28);C=side_target(83,22,-150)
stack=above(C,.028);closed=.714
home=[0,45,-110,0,90,-16]
anchors=[(0,home),(1.5,side_ik(above(A,.05))),(2.5,side_ik(A)),(3.2,side_ik(A,closed)),
 (4.5,side_ik(lifted(A),closed)),(6,[0,0,0,0,90,closed]),
 (7,[0,0,0,0,-45,closed]),(8,[0,0,0,0,90,closed]),
 (10,[-150,25,25,0,90,closed]),(11.5,side_ik(above(C,.05),closed)),
 (12.5,side_ik(C,closed)),(13,side_ik(C)),(14.5,side_ik(above(C,.07))),
 (17,side_ik(above(B,.05))),(18,side_ik(B)),(18.7,side_ik(B,closed)),
 (20,side_ik(lifted(B),closed)),(22,[-150,10,15,0,90,closed]),
 (24,side_ik(above(stack,.035),closed)),(25,side_ik(stack,closed)),
 (25.7,side_ik(stack)),(27,side_ik(lifted(stack))),(29,home),(30,home)]
anchors=[(max(1,round(t*24)),p) for t,p in anchors]
frames=[];j=0
for f in range(1,721):
    while j+1<len(anchors)-1 and f>anchors[j+1][0]:j+=1
    a,p=anchors[j];b,q=anchors[j+1];u=max(0,min(1,(f-a)/(b-a)));u=u*u*u*(10+u*(-15+6*u))
    frames.append({'frame':f,'degrees':[v+(w-v)*u for v,w in zip(p,q)]})
result={'fps':24,'frame_count':720,'duration_seconds':30,'anchors':anchors,'frames':frames,
 'grip_local':GRIP,'payload_dimensions_m':[.020,.028,.008],'source_a':A,'source_b':B,'destination':C,
 'payload_events':{'blue':{'attach':77,'release':300,'source':A,'target':C},
                   'orange':{'attach':449,'release':600,'source':B,'target':stack}},
 'scope':'Scripted geometric task demonstration; attachment approximates gripping and is not a force/contact simulation. No250g capability claim.'}
(ROOT/'reports/task-motion-plan.json').write_text(json.dumps(result,indent=2))
print('TASK_PLAN',A,B,C,'angles',[(f,[round(v,1) for v in p]) for f,p in anchors])
