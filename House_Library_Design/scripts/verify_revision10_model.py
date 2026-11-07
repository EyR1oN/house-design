from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'scripts/verify_revision9.py').read_text(encoding='utf8').replace("Revision8_Backup","Revision9_Backup").replace("'revision':9","'revision':10").replace('revision9_verification','revision10_verification').replace('REVISION9_VERIFIED','REVISION10_VERIFIED')
needle="check('Boiler service rectangle free of cabinets',bo[1][0]-2.60>.5 and bo[0][1]<front and bo[2][0]>1.45)"
s=s.replace(needle,needle+"\ncheck('Boiler side gap >=510mm',front-bo[0][1]>.51,front-bo[0][1])\ncheck('Boiler clear of conservatively modelled entry door sweep',d['Laundry_Gas_Boiler']['bounds'][1][0]-(2.603+.653)>.15)\ncheck('Service sockets beside boiler clear of its pipes',all(bb(bpy.data.objects[id])[0][0]>bo[0][1] for id in ['E1_022_SOCKET','E1_023_SOCKET']))")
exec(compile(s,str(R/'scripts/verify_revision9.py'),'exec'))
