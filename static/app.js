const btn=document.getElementById('go'), statusBox=document.getElementById('status'), results=document.getElementById('results');
btn.addEventListener('click', async()=>{
 const url=document.getElementById('url').value.trim();
 if(!url){statusBox.textContent='Pega primero el enlace de un video.';return}
 btn.disabled=true;statusBox.textContent='Descargando y analizando el video. Puede tardar varios minutos…';results.innerHTML='';
 try{
  const res=await fetch('/api/clip',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,clips:Number(document.getElementById('count').value)})});
  const data=await res.json();if(!res.ok)throw new Error(data.detail||'Ocurrió un error.');
  statusBox.textContent='¡Tus clips están listos!';
  data.clips.forEach((c,i)=>{const el=document.createElement('article');el.className='clip';const info=document.createElement('div');const h=document.createElement('h3');h.textContent=(i+1)+'. '+c.title;const p=document.createElement('p');p.textContent=c.reason+' · Puntuación '+c.score+'/100';info.append(h,p);const a=document.createElement('a');a.href=c.url;a.textContent='Descargar';a.download='';el.append(info,a);results.append(el)});
 }catch(e){statusBox.textContent=e.message}finally{btn.disabled=false}
});
