from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'scripts/update_revision14_viewer.py').read_text(encoding='utf8').replace('revision14','revision15').replace('REVISION14','REVISION15').replace('LIBRARY 14.0 Oak pivot shelf door and rounded white corner shelves','LIBRARY 15.0 Concealed hood with storage')
s='\n'.join(line for line in s.splitlines() if not line.startswith('motion=') and not line.startswith(' for role,names_in_role') and not line.startswith("  if n.get('name') in names_in_role"))+'\n'
(R/'scripts/update_revision15_viewer.py').write_text(s,encoding='utf8')
