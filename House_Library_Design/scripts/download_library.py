from pathlib import Path
import urllib.request,urllib.parse,json,uuid,concurrent.futures,hashlib,time
ROOT=Path(__file__).resolve().parents[1]
HEAD={'User-Agent':'BlenderKit/3.21.2'}
assets=json.loads((ROOT/'data/selected_assets.json').read_text(encoding='utf8'))
scene_uuid=str(uuid.uuid4())
def req(u):return urllib.request.urlopen(urllib.request.Request(u,headers=HEAD),timeout=90)
def one(a):
 assert a['isFree'] and a.get('canDownload',True)
 files=a['files'];f=next((f for f in files if f['fileType']=='resolution_2K'),None) or next(f for f in files if f['fileType']=='blend')
 dest=ROOT/'assets'/(a['role']+'.blend')
 for attempt in range(3):
  try:
   if not dest.exists():
    d=json.load(req(f['downloadUrl']+'?'+urllib.parse.urlencode({'scene_uuid':scene_uuid,'addon_version':'3.21.2'})))
    content=req(d['filePath']).read();dest.write_bytes(content)
   assert dest.stat().st_size>1000
   result={'role':a['role'],'id':a['id'],'asset_base_id':a['assetBaseId'],'name':a['displayName'],'author':a['author'].get('fullName',''),'license':a['license'],'source_url':'https://www.blenderkit.com/asset-gallery-detail/'+a['assetBaseId']+'/','download_endpoint':f['downloadUrl'],'file':str(dest.relative_to(ROOT)).replace(chr(92),'/'),'texture_resolution':f['fileType'],'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'status':'DOWNLOADED'}
   print('DOWNLOADED',a['role'],round(result['bytes']/1048576,2),'MB',flush=True);return result
  except Exception as e:
   if attempt==2:raise
   time.sleep(2)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:manifest=list(ex.map(one,assets))
(ROOT/'data/library_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('LIBRARY_DOWNLOAD_COMPLETE',len(manifest),flush=True)
