(() => {
 const button=document.createElement('button');button.id='pantry-toggle';button.className='wide';button.textContent='Відкрити кутову шафу';document.querySelector('#photos-button').before(button);
 let amount=0,busy=false,targets=[];const clamp=x=>Math.max(0,Math.min(1,x));
 function collect(){const found=[];window.VIEWER_TEST.scene.traverse(n=>{if(n.userData.pantry_role==='pivot'){n.userData.pantryClosedPosition||=n.position.clone();n.userData.pantryClosedQuaternion||=n.quaternion.clone();found.push(n);}});if(found.length)targets=found;return targets;}
 function pose(u){const slide=.22*clamp(u/.3),angle=-Math.PI/2*clamp((u-.3)/.7),c=Math.cos(angle),s=Math.sin(angle);
  for(const n of targets){const p=n.userData.pantryClosedPosition,dx=p.x-9.735,dz=p.z+4.56;n.position.set(9.735+c*dx+s*dz,p.y,-4.56-slide-s*dx+c*dz);const q=n.quaternion.clone().setFromAxisAngle(n.position.clone().set(0,1,0),angle);n.quaternion.copy(n.userData.pantryClosedQuaternion).premultiply(q);}
  amount=u;const v=window.VIEWER_TEST;v.renderer.render(v.scene,v.camera);
 }
 function sync(){button.hidden=!document.querySelector('[data-floor="1"]').classList.contains('active');button.textContent=amount>.5?'Закрити кутову шафу':'Відкрити кутову шафу';}
 button.onclick=()=>{if(busy||!window.VIEWER_READY||!collect().length)return;busy=true;button.disabled=true;const from=amount,to=amount>.5?0:1,start=performance.now();function frame(now){const t=clamp((now-start)/1400);pose(from+(to-from)*t);if(t<1)requestAnimationFrame(frame);else{busy=false;button.disabled=false;sync();}}requestAnimationFrame(frame);};
 new MutationObserver(sync).observe(document.querySelector('[data-floor="1"]'),{attributes:true,attributeFilter:['class']});sync();window.CORNER_PANTRY={setOpen(u){if(!busy&&collect().length){pose(clamp(u));sync();}},getState(){return{amount,busy,movingObjects:targets.length};}};
})();
