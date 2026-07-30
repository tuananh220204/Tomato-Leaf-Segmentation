/* ── CANVAS PARTICLE NETWORK ── */
(function(){
 const c=document.getElementById('bg-canvas');
 if(!c)return;
 const ctx=c.getContext('2d');
 let P=[];
 const N=90,D=130;
 
 function resize(){c.width=innerWidth;c.height=innerHeight}
 function init(){
  P=[];
  for(let i=0;i<N;i++)P.push({
    x:Math.random()*c.width,
    y:Math.random()*c.height,
    vx:(Math.random()-.5)*.35,
    vy:(Math.random()-.5)*.35,
    r:Math.random()*1.8+.4,
    a:Math.random()*.45+.1
  });
 }
 function draw(){
  ctx.clearRect(0,0,c.width,c.height);
  ctx.strokeStyle='rgba(0,232,122,0.018)';
  ctx.lineWidth=.5;
  const s=60;
  for(let x=0;x<c.width+s;x+=s*1.5){
    for(let y=0;y<c.height+s;y+=s){
      const ox=y%2===0?0:s*.75;
      ctx.beginPath();
      for(let k=0;k<6;k++){
        const a=Math.PI/3*k-Math.PI/6;
        k===0?ctx.moveTo(x+ox+s*Math.cos(a)/2,y+s*Math.sin(a)/2)
             :ctx.lineTo(x+ox+s*Math.cos(a)/2,y+s*Math.sin(a)/2);
      }
      ctx.closePath();ctx.stroke();
    }
  }
  for(let i=0;i<P.length;i++){
    for(let j=i+1;j<P.length;j++){
      const dx=P[i].x-P[j].x,dy=P[i].y-P[j].y;
      const dist=Math.sqrt(dx*dx+dy*dy);
      if(dist<D){
        ctx.beginPath();
        ctx.strokeStyle=`rgba(0,232,122,${(1-dist/D)*.14})`;
        ctx.lineWidth=.6;
        ctx.moveTo(P[i].x,P[i].y);
        ctx.lineTo(P[j].x,P[j].y);
        ctx.stroke();
      }
    }
  }
  P.forEach(p=>{
    ctx.beginPath();
    ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
    ctx.fillStyle=`rgba(0,232,122,${p.a})`;
    ctx.fill();
    p.x+=p.vx; p.y+=p.vy;
    if(p.x<0||p.x>c.width) p.vx*=-1;
    if(p.y<0||p.y>c.height) p.vy*=-1;
  });
  requestAnimationFrame(draw);
 }
 addEventListener('resize',()=>{resize();init()});
 resize();init();draw();
})();
 
/* ── VIEW SWITCHING (Hash Routing) ── */
function switchView(name){
 window.location.hash = name;
}
 
function handleHashChange(){
 let hash = window.location.hash.substring(1);
 const validViews = ['analyzer', 'dashboard','about'];
 if (!validViews.includes(hash)) {
  window.location.hash = 'analyzer';
  return;
 }
 
 document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
 document.querySelectorAll('.nav-link').forEach(n=>n.classList.remove('active'));
 
 const viewEl = document.getElementById('view-'+hash);
 const linkEl = document.querySelector('[data-view="'+hash+'"]');
 
 if(viewEl) viewEl.classList.add('active');
 if(linkEl) linkEl.classList.add('active');
 
 if(hash==='dashboard')renderDashboard();
}
 
window.addEventListener('hashchange',handleHashChange);
window.addEventListener('DOMContentLoaded',handleHashChange);
 
/* ── WALLET ── */
const HARDHAT_NETWORK_LABEL='Hardhat Localhost 8545';
const HARDHAT_CHAIN_IDS=new Set(['0x7a69','0x539','31337','1337']);
function shortenAddress(address){
 return address ? `${address.slice(0,6)}...${address.slice(-4)}` : '';
}
function isHardhatChain(chainId){
 return HARDHAT_CHAIN_IDS.has(String(chainId).toLowerCase());
}
function setWalletButtonState({connected=false,account='',chainId='',available=true}={}){
 const btn=document.getElementById('walletBtn');
 const dot=document.getElementById('walletDot');
 const txt=document.getElementById('walletText');
 if(!btn||!dot||!txt)return;
 
 if(!available){
  txt.textContent='Chưa cài MetaMask';
  dot.style.background='var(--orange)';
  btn.style.borderColor='var(--orange)';
  btn.style.color='var(--orange)';
  return;
 }
 
 if(!connected){
  txt.textContent='MetaMask chưa kết nối';
  dot.style.background='var(--cyan)';
  btn.style.borderColor='var(--cyan)';
  btn.style.color='var(--cyan)';
  return;
 }
 
 const chainLabel = chainId && !isHardhatChain(chainId)? 'Sai mạng' : HARDHAT_NETWORK_LABEL;
 txt.textContent = `${chainLabel} · ${shortenAddress(account)}`;
 dot.style.background='var(--primary)';
 btn.style.borderColor='var(--primary)';
 btn.style.color='var(--primary)';
}
async function refreshWalletState(){
 if(typeof window.ethereum === 'undefined'){
  setWalletButtonState({available:false});
  return;
 }
 
 let accounts=[];
 let chainId='';
 try{
  accounts = await window.ethereum.request({method: 'eth_accounts' }) || [];
  chainId = await window.ethereum.request({method: 'eth_chainId' });
 } catch (error) {
  console.warn('Không thể đọc trạng thái ví', error);
 }
 setWalletButtonState({connected:accounts.length>0,account:accounts[0]|| '', chainId});
}
function connectWallet(){
 if(typeof window.ethereum=== 'undefined'){
  setWalletButtonState({available:false});
  alert('MetaMask chưa được cài đặt.');
  return;
 }
 window.ethereum.request({method: 'eth_requestAccounts' })
  .then(refreshWalletState)
  .catch(error => { console.warn(error); refreshWalletState(); });
}
window.addEventListener('DOMContentLoaded', ()=>{
 refreshWalletState();
 if(window.ethereum){
  window.ethereum.on('accountsChanged', refreshWalletState);
  window.ethereum.on('chainChanged', refreshWalletState);
 }
});
 
/* ── UPLOAD ZONE ── */
const uploadZone=document.getElementById('uploadZone');
function handleDragOver(e){e.preventDefault();uploadZone.classList.add('dragover')}
function handleDragLeave(){uploadZone.classList.remove('dragover')}
function handleDrop(e){
 e.preventDefault();
 uploadZone.classList.remove('dragover');
 const f=e.dataTransfer.files[0];
 if(f&&f.type.startsWith('image/'))processFile(f);
}
function handleFileUpload(e){
 const f=e.target.files[0];
 if(f) processFile(f);
}
 
let uploadedSrc='';
function processFile(f){
 const reader=new FileReader();
 reader.onload=e=>{
  uploadedSrc=e.target.result;
  document.getElementById('previewImg').src=uploadedSrc;
  document.getElementById('fileName').textContent=f.name;
  document.getElementById('uploadPlaceholder').style.display='none';
  document.getElementById('uploadPreview').style.display='block';
  uploadZone.style.cursor='default';
 };
 reader.readAsDataURL(f);
}
function removeImage(e){
 e.stopPropagation();
 uploadedSrc='';
 document.getElementById('uploadPlaceholder').style.display='flex';
 document.getElementById('uploadPreview').style.display='none';
 document.getElementById('previewImg').src='';
 document.getElementById('file-input').value='';
 uploadZone.style.cursor='pointer';
}
 
/* ── ANALYSIS & REALTIME MODEL SWITCHING ── */
const STEPS=[
 'Đang khởi tạo các mô hình phân vùng...',
 'Đang tiền xử lý ảnh (512×512)...',
 'Đang chạy U-Net++...',
 'Đang chạy U-Net...',
 'Đang chạy SegNet...',
 'Đang so sánh điểm số mô hình...',
 'Đang chọn kết quả tốt nhất...',
 'Đang hoàn tất kết quả...'
];
 
const MODEL_DATA={
 unetpp: {label:'U-Net++'},
 unet:   {label:'U-Net'},
 segnet: {label:'SegNet'}
};
 
let globalRecordHash = "";
let globalRecordSha256 = "";
let globalRecordTimestamp = "";
let globalBestModelType = "";
let globalBestModelLabel = "";
let globalModelResults = [];
let globalAnalysisResponse = null;
 
// Hàm cập nhật real-time khi người dùng chọn model từ danh sách so sánh hoặc dropdown
function showModelResult(modelType){
 if(!globalModelResults|| !globalModelResults.length)return;
 const result = globalModelResults.find(r => r.model_type === modelType || r.model_name === modelType) || globalModelResults[0];
 if(!result)return;
 
 const mName = result.model_type || result.model_name;
 
 // Cập nhật giá trị đang chọn trên dropdown chính nếu có
 const modelSelectEl = document.getElementById('modelSelect');
 if(modelSelectEl) modelSelectEl.value = mName;
 
 // Cập nhật ảnh hiển thị
 // SỬA Ở ĐÂY: Lấy ảnh gốc trực tiếp từ cục data tổng thay vì trong từng result nhỏ
 if(globalAnalysisResponse && globalAnalysisResponse.image_original_base64) {
  document.getElementById('resultOriginal').src= globalAnalysisResponse.image_original_base64;
 }
 
 const maskImgNodes = document.querySelectorAll('.image-card.mask-card img');
 if(maskImgNodes.length > 0) {
  maskImgNodes[0].src = result.image_mask_base64;
 }
 document.getElementById('resultOverlay').src= result.image_overlay_base64;
 
 // Cập nhật thông số KPIs
 const resPct = Number(result.infection_area_percent|| 0);
 document.getElementById('metricModel').textContent= result.model_label || MODEL_DATA[mName]?.label|| mName;
 document.getElementById('metricIoU').textContent= Number(result.benchmark_iou|| 0).toFixed(4);
 document.getElementById('metricTime').textContent= ((result.inference_time_ms || 0)/ 1000).toFixed(2)+ " s";
 document.getElementById('infectionValue').textContent= resPct + '%';
 document.getElementById('severityTag').textContent= resPct < 0.9 ? 'Khỏe mạnh' : resPct < 5 ? 'Bệnh nhẹ' : resPct < 10 ? 'Bệnh nặng' : 'Bệnh rất nặng';
 
 // Hiệu ứng thanh tiến trình diện tích bệnh
 const bar = document.getElementById('infectionBar');
 if(bar) bar.style.width = resPct + '%';
 
 // Cập nhật biến global để khi lưu DB hay ký Blockchain sẽ ăn theo Model đang chọn này
 globalBestModelType = mName;
 globalBestModelLabel = result.model_label || MODEL_DATA[mName]?.label;
 
 // Highlight dòng đang chọn trong bảng so sánh
 document.querySelectorAll('.model-compare-row').forEach(row => {
  if(row.dataset.modelType === mName) {
    row.classList.add('selected');
  } else {
    row.classList.remove('selected');
  }
 });
}
 
function formatModelRow(result,isBest){
 const badge = isBest ? '<span class="model-compare-badge">TỐT NHẤT</span>' : '<span class="model-compare-badge muted">KHÁC</span>';
 const score = Number(result.benchmark_iou|| 0).toFixed(4);
 const pct = Number(result.infection_area_percent|| 0).toFixed(2);
 const time = `${Number(result.inference_time_ms || 0)} ms`;
 const mType = result.model_type || result.model_name;
 return `
  <div class="model-compare-row ${isBest ? 'best' : ''}" data-model-type="${mType}">
    <div class="model-compare-left">
      <div class="model-compare-rank">${isBest ? '★' : '•'}</div>
      <div>
        <div class="model-compare-name">${result.model_label}</div>
        <div class="model-compare-sub">${mType}</div>
      </div>
      ${badge}
    </div>
    <div class="model-compare-kpis">
      <span class="model-compare-chip">Score ${score}</span>
      <span class="model-compare-chip">Diện tích ${pct}%</span>
      <span class="model-compare-chip">${time}</span>
    </div>
  </div>`;
}
 
function renderModelComparison(modelResults,bestModelType){
 const panel = document.getElementById('modelComparison');
 const body = document.getElementById('modelComparisonBody');
 const bestLabelEl = document.getElementById('modelComparisonBest');
 if(!panel|| !body|| !bestLabelEl|| !Array.isArray(modelResults)|| !modelResults.length){
  if(panel) panel.style.display='none';
  return;
 }
 
 const bestLabel = MODEL_DATA[bestModelType]?.label|| bestModelType;
 const sorted = [...modelResults].sort((a,b) => (b.benchmark_iou || 0)- (a.benchmark_iou || 0));
 bestLabelEl.textContent = bestLabel;
 body.innerHTML = sorted.map(item => formatModelRow(item, (item.model_type || item.model_name) === bestModelType)).join('');
 
 globalModelResults = sorted;
 
 body.querySelectorAll('.model-compare-row').forEach(row => {
  row.addEventListener('click', () => {
    const mt = row.dataset.modelType;
    showModelResult(mt);
  });
 });
 panel.open = false;
 panel.style.display='block';
}
 
async function runAnalysis(){
 const btn = document.getElementById('analyzeBtn');
 const overlay = document.getElementById('loadingOverlay');
 const empty = document.getElementById('emptyState');
 const panel = document.getElementById('resultsPanel');
 const fileInput = document.getElementById('file-input');
 
 if(!fileInput.files[0]) {
  alert("Vui lòng tải lên một ảnh lá cà chua trước khi phân tích!");
  return;
 }
 
 btn.disabled=true;
 empty.style.display='none';
 panel.style.display='none';
 panel.classList.remove('visible');
 overlay.classList.add('show');
 
 let si=0;
 const stepEl=document.getElementById('loadingStep');
 const iv=setInterval(()=>{stepEl.textContent=STEPS[si%STEPS.length];si++},275);
 
 try {
  const file = fileInput.files[0];
  const modelType = document.getElementById('modelSelect').value;
  
  const formData = new FormData();
  formData.append("file", file);
  formData.append("model_type", modelType); // Sửa khớp chuẩn tham số main.py
 
  const rs = await fetch('http://localhost:8000/predict', {
    method: 'POST',
    body: formData
  });
  
  if(!rs.ok)throw new Error(`Máy chủ trả về ${rs.status}`);
  
  const data = await rs.json();
  clearInterval(iv);
  overlay.classList.remove('show');
  btn.disabled=false;
 
  // Gán dữ liệu global phản hồi từ server
  globalAnalysisResponse = data;
  
  // Sửa lỗi ở đây: KHÔNG ĐƯỢC CHÈN THÊM TRƯỜNG "image_original_base64" VÀO model_results
  // Vì nếu chèn thêm, hàm băm sẽ sinh ra chuỗi khác biệt so với Backend, gây lỗi 400
  globalModelResults = (data.model_results || []).map(m => ({
    ...m,
    model_type: m.model_name // Đồng bộ UI mà không phá cấu trúc băm
  }));
 
  const bestModelType = data.best_model || modelType;
 
  panel.style.display='block';
  setTimeout(()=>{
    panel.classList.add('visible');
  },60);
 
  renderModelComparison(globalModelResults, bestModelType);
  showModelResult(bestModelType); // Hiển thị mặc định kết quả model tốt nhất (hoặc model user chọn)
 
  globalRecordSha256 = data.record_sha256 || "";
  globalRecordHash = data.record_keccak || data.record_hash || "";
  globalRecordTimestamp = data.record_timestamp|| "";
 
  const shaEl = document.getElementById('recordSha256');
  const kecEl = document.getElementById('recordKeccak');
  const timeEl = document.getElementById('recordTimestamp');
  if(shaEl)shaEl.textContent = globalRecordSha256 || '—';
  if(kecEl)kecEl.textContent = globalRecordHash || '—';
  if(timeEl)timeEl.textContent = globalRecordTimestamp || '—';
 
  const txReceipt = document.getElementById('txReceipt');
  const miningAnim = document.getElementById('miningAnim');
  const blockchainBtn = document.getElementById('blockchainBtn');
  if(txReceipt)txReceipt.classList.remove('show');
  if(miningAnim)miningAnim.classList.remove('show');
  if(blockchainBtn)blockchainBtn.disabled = false;
 
  // Gửi nguyên vẹn Data chính chủ lấy từ /predict trả về xuống SQLite
  // Tránh việc tự biên dịch lại sẽ lệch mã SHA-256 gây ra HTTP 400
  const logRs = await fetch('http://localhost:8000/verify_record', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: file.name,
      infection_percentage: data.infection_area_percent, 
      record_timestamp: data.record_timestamp,
      record_sha256: data.record_sha256,
      record_keccak: data.record_keccak,
      record_hash: data.record_keccak,
      best_model: data.best_model,
      best_model_label: data.best_model_label,
      selection_basis: data.selection_basis,
      model_results: data.model_results // TRUYỀN NGUYÊN BẢN ARRAY NÀY TỪ BACKEND TRẢ VỀ
    })
  });
 
  if(logRs.ok) {
    console.log("Đã lưu bản ghi kèm Mã Hash xuống CSDL SQLite thành công!");
  } else {
    console.warn("Lưu CSDL thất bại. HTTP Status:", logRs.status);
  }
 
 } catch (error) {
  clearInterval(iv);
  overlay.classList.remove('show');
  btn.disabled = false;
  alert("Lỗi hệ thống: " + error.message);
 }
}
 
// Lắng nghe sự kiện thay đổi trực tiếp từ Dropdown model chính trên giao diện
document.addEventListener('DOMContentLoaded', () => {
 const modelSelect = document.getElementById('modelSelect');
 if(modelSelect) {
  modelSelect.addEventListener('change', (e) => {
    const selectedModel = e.target.value;
    if(globalModelResults && globalModelResults.length > 0) {
      showModelResult(selectedModel);
    }
  });
 }
});
 
/* ── BLOCKCHAIN PEG (REAL WEB3) ── */
async function pegBlockchain(){
 const mining = document.getElementById('miningAnim');
 const receipt = document.getElementById('txReceipt');
 const btn = document.getElementById('blockchainBtn');
 
 if (!globalRecordHash) {
  alert("Vui lòng tải ảnh và thực hiện phân tích dự đoán trước khi đẩy CSDL lên Blockchain!");
  return;
 }
 
 if (typeof CONTRACT_ADDRESS === 'undefined' || !CONTRACT_ADDRESS || CONTRACT_ADDRESS === '0x0000000000000000000000000000000000000000') {
  alert("Hãy deploy SmartFarm.sol trên Hardhat localhost trước rồi cập nhật địa chỉ contract trong contract_abi.js!");
  return;
 }
 
 if (typeof window.ethereum=== 'undefined') {
  alert("Hãy cài đặt ví MetaMask trên trình duyệt của bạn để tương tác với Blockchain!");
  return;
 }
 
 receipt.classList.remove('show');
 mining.classList.add('show');
 btn.disabled = true;
 
 try {
  const provider = new ethers.providers.Web3Provider(window.ethereum);
  await provider.send("eth_requestAccounts", []);
  const signer = provider.getSigner();
  
  const contract = new ethers.Contract(CONTRACT_ADDRESS,CONTRACT_ABI, signer);
  const modelType = globalBestModelType || document.getElementById('modelSelect').value;
 
  const tx = await contract.pegRecord(globalRecordHash,modelType);
  const txReceipt = await tx.wait();
 
  mining.classList.remove('show');
  btn.disabled = false;
 
  const now = new Date();
  const ts = now.toISOString().replace('T',' ').slice(0,19)+ ' UTC';
 
  document.getElementById('txNetwork').textContent= HARDHAT_NETWORK_LABEL;
  document.getElementById('txHash').textContent= txReceipt.transactionHash.slice(0,22)+ '...' + txReceipt.transactionHash.slice(-8);
  document.getElementById('txBlock').textContent= '#' + txReceipt.blockNumber.toLocaleString();
  document.getElementById('txTime').textContent= ts;
  document.getElementById('txContract').textContent= CONTRACT_ADDRESS;
  document.getElementById('txPegHash').textContent= globalRecordHash.length > 34 ? `${globalRecordHash.slice(0,18)}...${globalRecordHash.slice(-8)}` : globalRecordHash;
 
  receipt.classList.add('show');
 
 } catch (error) {
  mining.classList.remove('show');
  btn.disabled = false;
  console.error(error);
  alert("Lỗi Giao Dịch Blockchain: " + (error.message || "Bị từ chối hoặc lỗi mạng"));
 }
}
 
/* ── XÁC MINH TOÀN VẸN (AUDIT) ── */
async function verifyData(){
 const fileNameInput = document.getElementById('verifyFileName');
 const boxSuccess = document.getElementById('verifySuccess');
 const boxError = document.getElementById('verifyError');
 const fileName = fileNameInput.value.trim();
 
 boxSuccess.style.display = 'none';
 boxError.style.display = 'none';
 
 if(!fileName) {
  alert("Vui lòng nhập tên file!");
  return;
 }
 
 if (typeof CONTRACT_ADDRESS === 'undefined' || !CONTRACT_ADDRESS || CONTRACT_ADDRESS === '0x0000000000000000000000000000000000000000') {
  alert("Hãy deploy SmartFarm.sol trước!");
  return;
 }
 
 try {
  const dbRes = await fetch(`http://localhost:8000/record/${fileName}`);
  if (!dbRes.ok)throw new Error("Không tìm thấy file trên server (SQLite)!");
  const dbData = await dbRes.json();
 
  const dbHash = dbData.record_keccak || dbData.record_hash || dbData.record_sha256;
  const hashLabel = dbData.record_keccak ? 'record_keccak' : (dbData.record_hash ? 'record_hash' : 'record_sha256');
 
  if (typeof window.ethereum === 'undefined')throw new Error("Chưa cài MetaMask!");
  const provider = new ethers.providers.Web3Provider(window.ethereum);
  const contract = new ethers.Contract(CONTRACT_ADDRESS,CONTRACT_ABI, provider);
 
  const totalRecordsBN = await contract.getTotalRecords();
  const totalRecords = totalRecordsBN.toNumber();
  let isFoundOnChain = false;
 
  for(let i = 0; i < totalRecords; i++) {
      const chainRecord = await contract.getRecord(i);
      const chainHash = chainRecord[0];
      if(chainHash === dbHash) {
          isFoundOnChain = true;
          break;
      }
  }
 
  if(isFoundOnChain) {
      boxSuccess.textContent = `✅ Khớp ${hashLabel} với on-chain: ${dbHash}`;
      boxSuccess.style.display = 'block';
  } else {
      boxError.textContent = `❌ CẢNH BÁO: Không tìm thấy ${hashLabel} trên Hardhat local.`;
      boxError.style.display = 'block';
  }
 
 } catch (error) {
  console.error(error);
  boxError.textContent = "❌ Lỗi hệ thống: " + error.message;
  boxError.style.display = 'block';
 }
}
 
/* ── MOCK DOWNLOAD ── */
function mockDownload(btn){
 const orig=btn.innerHTML;
 btn.innerHTML='<i class="fa-solid fa-check"></i>&nbsp;Đã tải xuống!';
 btn.style.color='var(--primary)';
 btn.style.borderColor='rgba(0,232,122,.3)';
 setTimeout(()=>{btn.innerHTML=orig;btn.style.color='';btn.style.borderColor=''},2200);
}
 
/* ── DASHBOARD ── */
const HISTORY=[
 {name:'tomato_leaf_001.jpg',model:'unet', pct:8.3, tx:'0x4f7a...b21c',date:'2026-06-10 09:14'},
 {name:'field_sample_22.png',model:'unetpp',pct:31.2,tx:'0x9c2e...ff03',date:'2026-06-10 11:32'},
 {name:'leaf_north_row5.jpg',model:'segnet',pct:5.7, tx:'0xa1d8...0c9e',date:'2026-06-11 08:05'},
];
const TREND=[12.4,18.7,9.2,31.5,22.1,15.8,24.5];
const DAYS=['T2','T3','T4','T5','T6','T7','CN'];
 
function renderDashboard(){
 const cb=document.getElementById('chartBody');
 if(!cb)return;
 cb.innerHTML='';
 const mx=Math.max(...TREND);
 TREND.forEach((v,i)=>{
  const g=document.createElement('div');
  g.className='bar-group';
  const hPct=(v/mx*82);
  g.innerHTML=`
    <div class="bar-val">${v}%</div>
    <div class="bar-fill${v>25?' hi':''}" style="height:${hPct}%;min-height:4px" title="${DAYS[i]}:${v}%"></div>
    <div class="bar-lbl">${DAYS[i]}</div>
  `;
  cb.appendChild(g);
 });
 
 const tbody=document.getElementById('histBody');
 if(!tbody)return;
 tbody.innerHTML='';
 HISTORY.forEach(row=>{
  const ic=row.pct<10?'inf-low':row.pct<25?'inf-mid':'inf-hi';
  const mc={'unet':'tag-unet','segnet':'tag-segnet','unetpp':'tag-unetpp'}[row.model];
  const ml={'unet':'U-Net','segnet':'SegNet','unetpp':'U-Net++'}[row.model];
  const d=document.createElement('div');
  d.className='hist-row';
  d.innerHTML=`
    <div><div class="hist-thumb"><i class="fa-solid fa-seedling"></i></div></div>
    <div style="font-size:12px;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${row.name}</div>
    <div><span class="model-tag ${mc}">${ml}</span></div>
    <div class="inf-pct ${ic}">${row.pct}%</div>
    <div class="tx-cell">${row.tx}</div>
    <div class="date-cell">${row.date}</div>
  `;
  tbody.appendChild(d);
 });
}