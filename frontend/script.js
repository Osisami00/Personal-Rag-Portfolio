
async function ingest(){
  const f=document.getElementById('cv').files[0];
  const repo=document.getElementById('repo').value;

  const fd=new FormData();
  fd.append('cv',f);
  fd.append('repo_link',repo);

  await fetch('http://localhost:8000/ingest',{method:'POST',body:fd});
  alert('Knowledge ingested');
}

async function ask(){
  const q=document.getElementById('q').value;
  const res=await fetch('http://localhost:8000/ask',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({question:q})
  });
  const data=await res.json();
  document.getElementById('chat').innerHTML+=`<p>${data.answer}</p>`;
}
