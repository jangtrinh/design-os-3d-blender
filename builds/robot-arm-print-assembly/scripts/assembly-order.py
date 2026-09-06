"""Installation presentation from source membership; unknown retention stays unresolved."""
def classify(o):
 n=o['source_object'].removeprefix('A2-').removesuffix('-task')
 k=o.get('part_type');parent=o.get('source_parent','')
 if any(s in n for s in ['electronics','service-connector','TTL-RS485','shoulder-diamond']):return 'finish',0 if 'shell' in n else 1 if 'controller' in n or 'connector' in n else 2
 if n.startswith(('table-','base-matte','yaw-')):
  if n.startswith('table-'):return 'base',0
  if n=='base-matte-cover':return 'base',1
  if n=='yaw-servo' or (n.startswith('yaw-output') and 'case-frame' in parent):return 'base',2
  if 'pedestal' in n:return 'base',3 if k=='print' else 4
  if 'bearing' in n:return 'base',5
  if 'turntable' in n or 'output' in n:return 'base',6
  if 'horn-bolt' in n:return 'base',7
  return 'base',8
 for group,fork in [('shoulder','lower'),('elbow','upper')]:
  if n.startswith((group+'-',fork+'-')):
   if 'cradle-floor' in n:return group,0
   if 'motor-mount' in n:return group,1
   if 'mount-foot-nut' in n:return group,2
   if 'servo' in n or o.get('part_type')=='actuator-visual':return group,3
   if 'case-mount' in n or 'mount-foot-' in n:return group,4
   if 'drive-flange' in n or 'U-body' in n:return group,7
   if 'cassette-nut' in n:return group,8
   if 'bearing-carrier' in n:return group,5 if '--1' in n else 9
   if '61806' in n:return group,6 if '--1' in n else 10
   if 'carrier-foot' in n or 'flange-' in n or 'output-bolt' in n:return group,11
   if 'flush-bearing' in n:return group,12
   if 'bearing-cap-' in n:return group,13
   return group,14
 if n.startswith(('wrist-','roll-','tool-dock','tool-lock','tool-dowel')):
  if 'pitch-cassette' in n:return 'wrist',0
  if 'cage-nut' in n:return 'wrist',1
  if n=='wrist-servo':return 'wrist',2
  if 'case-retainer' in n:return 'wrist',3
  if 'cage-' in n:return 'wrist',4
  if 'wrist-output' in n or 'extension-hub' in n:return 'wrist',5
  if 'cheek' in n:return 'wrist',6
  if 'pivot' in n or 'cross-bridge' in n:return 'wrist',7
  if 'cradle' in n:return 'wrist',8
  if 'roll-servo' in n or 'roll-output' in n:return 'wrist',9
  if 'tool-dock' in n:return 'wrist',10
  if 'tool-lock' in n or 'dowel' in n:return 'wrist',11
  if 'roll-dock' in n:return 'wrist',12
  if 'vented-cover' in n:return 'wrist',13
  return 'wrist',14
 if n.startswith(('hand-','gripper-','fixed-','moving-','tool-retention')):
  if n=='gripper-tool-plate':return 'hand',0
  if 'servo-cradle' in n:return 'hand',1
  if 'nut' in n:return 'hand',2
  if n=='gripper-servo' or 'gripper-output' in n:return 'hand',3
  if 'case-retainer' in n:return 'hand',4
  if 'case-clamp' in n or 'adapter-bolt' in n:return 'hand',5
  if n in ['fixed-jaw','moving-jaw']:return 'hand',6
  if 'jaw-bolt' in n:return 'hand',7
  if 'TPU-pad' in n:return 'hand',8
  return 'hand',9
 raise ValueError('Unclassified component '+n)
