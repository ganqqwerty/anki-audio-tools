var ph=Object.defineProperty;var Ii=G=>{throw TypeError(G)};var _h=(G,V,ne)=>V in G?ph(G,V,{enumerable:!0,configurable:!0,writable:!0,value:ne}):G[V]=ne;var tt=(G,V,ne)=>_h(G,typeof V!="symbol"?V+"":V,ne),Xa=(G,V,ne)=>V.has(G)||Ii("Cannot "+ne);var h=(G,V,ne)=>(Xa(G,V,"read from private field"),ne?ne.call(G):V.get(G)),R=(G,V,ne)=>V.has(G)?Ii("Cannot add the same private member more than once"):V instanceof WeakSet?V.add(G):V.set(G,ne),T=(G,V,ne,kn)=>(Xa(G,V,"write to private field"),kn?kn.call(G,ne):V.set(G,ne),ne),se=(G,V,ne)=>(Xa(G,V,"access private method"),ne);(function(){"use strict";var vi,gi,yi,pn,_n,$t,mn,Jn,zn,Bt,ft,vn,qe,Ya,Qa,Za,$i,Te,ja,Qe,Gt,ge,Ze,Me,Ge,dt,Vt,kt,gn,yn,bn,Je,Tr,re,mh,vh,gh,Ja,Or,Lr,za,bi,Ve,ze,Se,Ht,er,tr,xr,wi;const G=[{activeIcon:"pause",command:"aqe:play",icon:"play",iconOnly:!0,label:"Play",title:"Play or pause current audio"},{activeIcon:"refresh-cw",command:"aqe:analyze",icon:"chart-line",iconOnly:!0,label:"Graph",title:"Analyze and show pitch/intensity graph"},{command:"aqe:show-file",icon:"folder-open",label:"Folder",title:"Show current audio file in folder"},{command:"aqe:trim-left",icon:"scissors",label:"-L",title:"Trim 100 ms from left"},{command:"aqe:trim-right",icon:"scissors",label:"-R",title:"Trim 100 ms from right"},{command:"aqe:remove-pauses",icon:"timer-reset",label:"Shorten Pauses",title:"Speed up long internal pauses"},{command:"aqe:slower",icon:"rewind",label:"Slower",title:"Decrease speed"},{command:"aqe:faster",icon:"fast-forward",label:"Faster",title:"Increase speed"},{command:"aqe:volume-down",icon:"volume-1",iconOnly:!0,label:"Volume -",title:"Decrease volume"},{command:"aqe:volume-up",icon:"volume-2",iconOnly:!0,label:"Volume +",title:"Increase volume"},{command:"aqe:undo",icon:"undo-2",iconOnly:!0,label:"Undo",title:"Restore the previous generated audio reference"},{command:"aqe:redo",icon:"redo-2",iconOnly:!0,label:"Redo",title:"Restore the most recently undone audio reference"},{command:"aqe:settings",icon:"settings",iconOnly:!0,label:"Settings",title:"Open Audio Quick Editor settings"}],V=[{command:"aqe:denoise-standard",icon:"volume-x",label:"Standard",title:"Denoise speech with DeepFilterNet"},{command:"aqe:rnnoise",icon:"waves",label:"RNNoise",title:"Denoise speech with RNNoise"}],ne=new Set(["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:remove-pauses","aqe:denoise-standard","aqe:rnnoise","aqe:volume-down","aqe:volume-up"]),kn={"aqe:play":"play","aqe:analyze":"graph","aqe:show-file":"show-file","aqe:delete-selection":"delete-selection","aqe:trim-left":"trim-left","aqe:trim-right":"trim-right","aqe:remove-pauses":"remove-pauses","aqe:denoise-standard":"denoise-standard","aqe:rnnoise":"rnnoise","aqe:slower":"slower","aqe:faster":"faster","aqe:volume-down":"volume-down","aqe:volume-up":"volume-up","aqe:undo":"undo","aqe:redo":"redo","aqe:settings":"settings"};function Ir(e,t){return`aqe-button-${e}-${kn[t]}`}function eo(e){return e==="aqe:denoise-standard"?"Denoising with Standard...":e==="aqe:rnnoise"?"Denoising with RNNoise...":e==="aqe:delete-selection"?"Deleting region...":"Processing..."}function nt(e){return document.querySelector(`.aqe-controls[data-aqe-field-ord="${e}"]`)}function I(e){return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${e}"]`)}function to(e,t){const n=nt(e);return(n==null?void 0:n.querySelector(`[data-aqe-command="${t}"]`))??null}function no(e){return to(e,"aqe:analyze")}function ro(e){return to(e,"aqe:play")}function ao(e){const t=nt(e);return(t==null?void 0:t.querySelector(".aqe-repeat-button"))??null}function ir(){return Array.from(document.querySelectorAll(".aqe-button"))}function $r(){return Array.from(document.querySelectorAll(".aqe-visualizer"))}const oo=[];let lr=null,ur=null;function Xt(e){globalThis.pycmd!==void 0&&globalThis.pycmd(e)}function Yt(e,t){Xt(`focus:${e}`),Xt(t)}function Bi(e,t){Xt(`focus:${e}`),window.__aqePendingCommandPayload=t,Xt("aqe:command-payload")}function Gi(e){lr=e,Xt("aqe:analyze-field")}function Vi(e){oo.push(e),Xt("aqe:frontend-log")}function Hi(){return oo.shift()??null}function Wi(e){window.__aqePendingPlaybackRequest=e,window.__aqeLastPlaybackRequest=e}function ji(){if(!window.__aqePendingPlaybackRequest)return null;const e=window.__aqePendingPlaybackRequest;return window.__aqePendingPlaybackRequest=null,e}function Ui(){if(!lr)return null;const e=lr;return lr=null,e}function Ki(e){ur=e}function Xi(){if(!ur)return null;const e=ur;return ur=null,e}function Yi(e){window.__aqeLastCursorIntent=e}function Qi(e){return encodeURIComponent(e||"").replaceAll("%2F","/")}function Re(e){return(e==null?void 0:e.querySelector(".aqe-audio-clock"))??null}function Br(e){e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!1,e.__aqeAudioClockLastSeekedMs=0,e.dataset.progressClockMode="stopped"}function An(e){const t=Re(e);if(!(!t||typeof t.pause!="function"))try{t.pause()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function Gr(e){const t=Re(e);if(Br(e),!!t){An(e),t.removeAttribute("src"),t.src="";try{t.load()}catch{e.__aqeAudioClockFallback=!0}}}function Zi(e,t){const n=Re(e);if(Br(e),!n){e.__aqeAudioClockFallback=!0;return}if(An(e),!t){Gr(e);return}n.setAttribute("src",Qi(t));try{n.load()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function Ji(e,t={}){const n=Re(e);!n||n.__aqeClockHandlersInstalled||(n.__aqeClockHandlersInstalled=!0,n.addEventListener("loadedmetadata",()=>{n.getAttribute("src")&&(e.__aqeAudioClockAvailable=!0,e.__aqeAudioClockFallback=!1)}),n.addEventListener("error",()=>{var r;e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,e.dataset.playbackState==="playing"&&e.dataset.progressClockMode==="audio"&&((r=t.onErrorDuringPlayback)==null||r.call(t))}),n.addEventListener("ended",()=>{var r;e.dataset.playbackState==="playing"&&((r=t.onEndedDuringPlayback)==null||r.call(t))}),n.addEventListener("seeked",()=>{e.__aqeAudioClockLastSeekedMs=Math.round((Number(n.currentTime)||0)*1e3)}))}function cr(e){const t=Re(e);return!t||!(e!=null&&e.__aqeAudioClockAvailable)||!t.getAttribute("src")?!1:t.readyState===void 0||t.readyState>=1}function fr(e,t,n){const r=Re(e);if(!r)return!1;const a=Math.max(0,Math.min(Number(t)||0,n||0));try{return r.currentTime=a/1e3,e.__aqeAudioClockLastSeekedMs=Math.round(a),!0}catch{return e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,!1}}var En=(e=>(e.Debug="debug",e.Error="error",e.Info="info",e.Unknown="unknown",e.Warn="warn",e))(En||{});function zi(e){return e==="error"?console.error:console.warn}function el(e){return e==="debug"?En.Debug:e==="warn"?En.Warn:e==="error"?En.Error:En.Info}function Vr(e,t=0){const n=tl(e);return n!==void 0?n:Array.isArray(e)?nl(e,t):e!==null&&typeof e=="object"?rl(e,t):al(e)}function tl(e){if(e===void 0)return"[undefined]";if(e===null)return null;if(typeof e=="boolean"||typeof e=="number"||typeof e=="string")return e}function nl(e,t){return t>=4?"[array]":e.map(n=>Vr(n,t+1))}function rl(e,t){if(t>=4)return"[object]";const n={};for(const[r,a]of Object.entries(e))n[r]=Vr(a,t+1);return n}function al(e){return typeof e=="bigint"?e.toString():typeof e=="symbol"?e.description?`Symbol(${e.description})`:"Symbol()":typeof e=="function"?`[function ${e.name||"anonymous"}]`:"[unserializable]"}function ol(e,t,n){const r={level:el(e),message:t};return n!==void 0&&(r.context=Vr(n)),r}function sl(e,t){function n(r,a,o){const s=zi(r);o===void 0?s(`[${e}] ${a}`):s(`[${e}] ${a}`,o);try{t(ol(r,a,o))}catch{}}return{debug:(r,a)=>n("debug",r,a),error:(r,a)=>n("error",r,a),info:(r,a)=>n("info",r,a),warn:(r,a)=>n("warn",r,a)}}const he=sl("editor",Vi),Pn=[],dr=new Set;let hr=null,pr=null,_r=!1;function il(){Pn.length=0,dr.clear(),hr=null,pr=null,_r=!1}function ll(e,t){for(const n of e){if(!n.sourceFilename)continue;const r=ul(n);if(dr.has(r))continue;const a=I(n.ord);if((a==null?void 0:a.dataset.hasTrack)==="true"&&a.dataset.sourceFilename===n.sourceFilename){dr.add(r);continue}dr.add(r),Pn.push({key:r,ord:n.ord,sourceFilename:n.sourceFilename})}mr(t)}function mr(e){if(!(hr!==null||e.anyBusy()))for(;Pn.length;){const t=Pn.shift();if(!t)return;const n=I(t.ord);if(!n){io(t,e);return}const r=nt(t.ord);if(!r){io(t,e);return}if((r.dataset.aqeSourceFilename||t.sourceFilename)===t.sourceFilename&&!(n.dataset.hasTrack==="true"&&n.dataset.sourceFilename===t.sourceFilename)){hr=t.key,pr=t.ord,e.requestDefaultGraph({ord:t.ord,sourceFilename:t.sourceFilename});return}}}function so(e,t){pr===e&&(hr=null,pr=null,queueMicrotask(()=>mr(t)))}function ul(e){return`${e.ord}\0${e.sourceFilename}`}function io(e,t){Pn.unshift(e),!_r&&(_r=!0,window.setTimeout(()=>{_r=!1,mr(t)},0))}function cl(e,t){return Math.max(t.startMs,Math.min(Number(e)||0,t.endMs))}function fl(e){let t="start";e.playbackState==="playing"&&(t="pause"),e.playbackState==="paused"&&(t=e.resumeRequiresRestart?"start":"resume");let n=e.anchorMs;return t==="start"&&e.region.mode==="selection"&&(n=e.region.startMs),t==="pause"&&(n=lo(e.currentProgressMs,e.cursorMs,n)),t==="resume"&&(n=lo(e.currentProgressMs,e.cursorMs,n),e.region.mode==="selection"&&(n<e.region.startMs||n>e.region.endMs)&&(t="start",n=e.region.startMs)),{action:t,cursorMs:Math.round(n),endMs:Math.round(e.region.endMs),engine:e.engine,loop:e.repeat,ord:e.ord,regionMode:e.region.mode}}function lo(e,t,n){return Number(e||t||n||0)}function dl(e){return{analyzerName:e.analyzerName,durationMs:Number(e.durationMs)||0,pitchMaxHz:e.pitchMaxHz,pitchMinHz:e.pitchMinHz,points:e.points.map(hl),sourceFilename:e.sourceFilename}}function hl(e){const t=typeof e[0]=="number"?e[0]:0,n=typeof e[1]=="number"?e[1]:null,r=typeof e[2]=="number"?e[2]:null,a=typeof e[3]=="boolean"?e[3]:!1;return[t,n,r,a]}function Hr(e){return e==="playing"||e==="paused"||e==="stopped"}const uo=50,pl=4;function co(){return{active:!1,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:null,startMs:null}}function fo(e,t){return Math.max(0,Math.min(Number(e)||0,Math.max(0,Number(t)||0)))}function vr(e,t,n,r=uo){const a=fo(Math.min(e,t),n),o=fo(Math.max(e,t),n);return!n||o-a<r?null:{startMs:Math.round(a),endMs:Math.round(o)}}function _l(e,t){if(!e.active||e.startMs===null||e.endMs===null)return null;const n=vr(e.startMs,e.endMs,t);return n?{...n,mode:"selection"}:null}function ml(e,t){if(!e.draftActive||e.draftStartMs===null||e.draftEndMs===null)return null;const n=vr(e.draftStartMs,e.draftEndMs,t);return n?{...n,mode:"selection"}:null}function vl(e,t,n,r){const a=vr(t,n,r);return a?{...e,active:!0,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:a.endMs,startMs:a.startMs}:yl(e)}function gl(e,t,n,r){const a=vr(t,n,r);return a?{...e,draftActive:!0,draftEndMs:a.endMs,draftStartMs:a.startMs}:ho(e)}function yl(e){return{...ho(e),active:!1,endMs:null,startMs:null}}function ho(e){return{...e,draftActive:!1,draftEndMs:null,draftStartMs:null}}function po(e,t,n,r){return Math.abs(t.clientX-e.clientX)<pl||Math.abs(r-n)<uo}const M={width:620,height:150,left:44,right:10,top:10,bottom:34};function _o(){return M.width-M.left-M.right}function mo(){return M.height-M.top-M.bottom}function _t(e,t){return t?M.left+Math.max(0,Math.min(1,e/t))*_o():M.left}function bl(e,t,n){if(!e||!t||!n||n<=t)return M.height-M.bottom;const r=Math.max(0,Math.min(1,(e-t)/(n-t)));return M.top+(1-r)*mo()}function vo(e,t){return t&&t<2e3?`${Math.round(e)} ms`:`${(e/1e3).toFixed(2)}s`}function wl(e,t){if(!e.length||!t)return"";const n=M.height-M.bottom,r=e[0];if(!r)return"";const a=`M ${_t(r[0],t).toFixed(2)} ${n.toFixed(2)}`,o=e.map(l=>{const c=_t(l[0],t).toFixed(2),f=Math.max(0,Math.min(1,l[2]??0)),u=(n-f*mo()).toFixed(2);return`L ${c} ${u}`}).join(" "),s=e.at(-1)??r,i=`L ${_t(s[0],t).toFixed(2)} ${n.toFixed(2)} Z`;return`${a} ${o} ${i}`}function ql(e,t,n,r){const a=[];let o=[];for(const s of e){const i=s[1];if(!(s[3]===!0&&i!==null&&i!==void 0)){o.length&&a.push(o),o=[];continue}o.push([_t(s[0],t),bl(i,n,r)])}return o.length&&a.push(o),a}function Ml(e,t){const n=e.querySelector(".aqe-pitch");if(n){n.textContent="";for(const r of ql(t.points,t.durationMs,t.pitchMinHz,t.pitchMaxHz)){if(r.length<2)continue;const a=document.createElementNS("http://www.w3.org/2000/svg","path");a.setAttribute("class","aqe-pitch-path"),a.setAttribute("d",r.map((o,s)=>{const i=o[0]??0,l=o[1]??0;return`${s?"L":"M"} ${i.toFixed(2)} ${l.toFixed(2)}`}).join(" ")),n.appendChild(a)}}}function Sl(e,t){const n=e.querySelector(".aqe-labels");if(!n)return;n.textContent="";const r=t.pitchMaxHz||500,a=t.pitchMinHz||75;for(const o of[[r,M.top+10],[a,M.height-M.bottom]]){const s=document.createElementNS("http://www.w3.org/2000/svg","text");s.setAttribute("class","aqe-hz-label"),s.setAttribute("x","2"),s.setAttribute("y",String(o[1])),s.textContent=`${Math.round(o[0])} Hz`,n.appendChild(s)}}function kl(e,t){const n=e.querySelector(".aqe-x-axis");if(!n)return;n.textContent="";const r=[0,t/2,t].filter((a,o,s)=>o===0||a!==s[o-1]);for(const a of r){const o=_t(a,t),s=document.createElementNS("http://www.w3.org/2000/svg","line");s.setAttribute("class","aqe-x-tick"),s.setAttribute("x1",o.toFixed(2)),s.setAttribute("x2",o.toFixed(2)),s.setAttribute("y1",String(M.height-M.bottom)),s.setAttribute("y2",String(M.height-M.bottom+4));const i=document.createElementNS("http://www.w3.org/2000/svg","text");i.setAttribute("class","aqe-x-label"),i.setAttribute("x",o.toFixed(2)),i.setAttribute("y",String(M.height-8)),i.textContent=vo(a,t),n.append(s,i)}}function go(e){const t=e.getBoundingClientRect(),n=Number(t.width)||M.width,r=Number(t.height)||M.height,a=Math.min(n/M.width,r/M.height)||1;return{left:t.left+M.left*a,width:_o()*a}}function Nn(e,t,n){const r=go(t);return Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*n}function Al(e){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="true",e.dataset.hasTrack="false",e.dataset.durationMs="0",e.dataset.sourceFilename="",e.dataset.anchorMs="0",e.dataset.cursorMs="0",e.dataset.progressMs="0",e.dataset.resumeRequiresRestart="false",e.dataset.playbackEngine="",e.dataset.playbackStartMs="0",e.dataset.playbackEndMs="0",e.dataset.playbackRegionMode="full",yo(e)}function El(e,t){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="false",e.dataset.hasTrack="true",e.dataset.durationMs=String(t.durationMs||0),e.dataset.analyzerName=t.analyzerName||"",e.dataset.sourceFilename=t.sourceFilename||"";const n=e.querySelector(".aqe-intensity");n&&n.setAttribute("d",wl(t.points,t.durationMs)),Ml(e,t),Sl(e,t),kl(e,t.durationMs||0)}function Pl(e,t,n="info"){const r=e.querySelector(".aqe-visualizer-status"),a=e.querySelector(".aqe-spinner"),o=n==="processing";e.dataset.graphBusy=o?"true":"false",a&&(a.hidden=!o),r&&(r.textContent=t||"",r.dataset.kind=n||"info")}function Nl(e,t,n){const r=e.querySelector(".aqe-selection"),a=e.querySelector(".aqe-selection-start"),o=e.querySelector(".aqe-selection-end"),s=n??t,i=Number(e.dataset.durationMs||"0");if(!r||!a||!o||!s||!i){r==null||r.setAttribute("width","0"),r==null||r.setAttribute("visibility","hidden"),r==null||r.classList.remove("aqe-selection-draft"),a==null||a.setAttribute("visibility","hidden"),o==null||o.setAttribute("visibility","hidden");return}const l=_t(s.startMs,i),c=_t(s.endMs,i);r.setAttribute("visibility","visible"),r.classList.toggle("aqe-selection-draft",n!==null),r.setAttribute("x",l.toFixed(2)),r.setAttribute("y",String(M.top)),r.setAttribute("width",Math.max(0,c-l).toFixed(2)),r.setAttribute("height",String(M.height-M.top-M.bottom)),a.setAttribute("visibility","visible"),o.setAttribute("visibility","visible");for(const[f,u]of[[a,l],[o,c]])f.setAttribute("x1",u.toFixed(2)),f.setAttribute("x2",u.toFixed(2)),f.setAttribute("y1",String(M.top)),f.setAttribute("y2",String(M.height-M.bottom))}function Fl(e,t,n){const r=_t(t,n),a=e.querySelector(".aqe-cursor");a&&(a.setAttribute("x1",r.toFixed(2)),a.setAttribute("x2",r.toFixed(2)));const o=e.querySelector(".aqe-cursor-label");o&&(o.textContent=vo(t,n))}function yo(e){var t;(t=e.querySelector(".aqe-intensity"))==null||t.setAttribute("d",""),Wr(e,".aqe-pitch"),Wr(e,".aqe-labels"),Wr(e,".aqe-x-axis")}function Cl(e){const t=e.querySelector(".aqe-cursor");t&&(t.setAttribute("x1",String(M.left)),t.setAttribute("x2",String(M.left)));const n=e.querySelector(".aqe-cursor-label");n&&(n.textContent="0 ms")}function Tl(e,t){return{analyzerName:t.analyzerName,durationMs:t.durationMs,ord:e,points:t.points.length,sourceFilename:t.sourceFilename}}function Wr(e,t){const n=e.querySelector(t);n&&(n.textContent="")}function Fn(e){return!e||e.dataset.selectionActive!=="true"?null:_l({active:e.dataset.selectionActive==="true",startMs:Number(e.dataset.selectionStartMs||"0"),endMs:Number(e.dataset.selectionEndMs||"0")},Number(e.dataset.durationMs||"0"))}function jr(e){return!e||e.dataset.selectionDraftActive!=="true"?null:ml({draftActive:e.dataset.selectionDraftActive==="true",draftStartMs:Number(e.dataset.selectionDraftStartMs||"0"),draftEndMs:Number(e.dataset.selectionDraftEndMs||"0")},Number(e.dataset.durationMs||"0"))}function bo(e){const t=Fn(e);return t||{startMs:0,endMs:Number(e.dataset.durationMs||"0")||0,mode:"full"}}function Qt(e,t={}){e.dataset.selectionDraftActive="false",e.dataset.selectionDraftStartMs="",e.dataset.selectionDraftEndMs="",t.redraw!==!1&&gr(e)}function xl(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=gl(co(),t,n,a);return!o.draftActive||o.draftStartMs===null||o.draftEndMs===null?(Qt(e,r),!1):(e.dataset.selectionDraftActive="true",e.dataset.selectionDraftStartMs=String(o.draftStartMs),e.dataset.selectionDraftEndMs=String(o.draftEndMs),r.redraw!==!1&&gr(e),!0)}function Rl(e,t,n={}){const r=jr(e);return r?(Qt(e,{redraw:!1}),Dl(e,r.startMs,r.endMs,t,n)):(Qt(e),!1)}function wo(e,t={}){if(e.dataset.selectionActive="false",e.dataset.selectionStartMs="",e.dataset.selectionEndMs="",Qt(e,{redraw:!1}),gr(e),t.resetPlaybackRegion!==!1){const n=bo(e);e.dataset.playbackStartMs=String(Math.round(n.startMs)),e.dataset.playbackEndMs=String(Math.round(n.endMs)),e.dataset.playbackRegionMode=n.mode}}function Dl(e,t,n,r,a={}){const o=Number(e.dataset.durationMs||"0"),s=vl(co(),t,n,o);return!s.active||s.startMs===null||s.endMs===null?(wo(e),!1):(Qt(e,{redraw:!1}),e.dataset.selectionActive="true",e.dataset.selectionStartMs=String(s.startMs),e.dataset.selectionEndMs=String(s.endMs),e.dataset.playbackStartMs=String(s.startMs),e.dataset.playbackEndMs=String(s.endMs),e.dataset.playbackRegionMode="selection",gr(e),a.updateCursor!==!1&&r.setCursor(e,s.startMs,!1),!0)}function gr(e){const t=jr(e),n=t??Fn(e);Nl(e,n,t)}function Ol(){return document.body.dataset.aqeBusy==="true"}function Ll(e){var t;return((t=nt(e))==null?void 0:t.querySelector(".aqe-delete-region-button"))??null}function qo(e,t){return e.startMs<=0&&e.endMs>=t}function Mo(e,t){return!!e&&e.endMs>e.startMs&&!qo(e,t)}function Cn(e){const t=Number(e.dataset.aqeFieldOrd||"0"),n=Ll(t);if(!n)return;const r=Fn(e),a=Number(e.dataset.durationMs||"0"),o=r!==null,s=Mo(r,a);n.hidden=!o,n.disabled=Ol()||!s,n.dataset.aqeButtonState=s?"default":"unavailable",n.title=s?"Delete selected region":"Cannot delete the whole audio clip",n.setAttribute("aria-disabled",n.disabled?"true":"false")}function Il(){$r().forEach(Cn)}function So(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=Number(e.dataset.durationMs||"0")||0,a=Fn(e);if(!a||!Mo(a,r))return a&&qo(a,r)&&he.warn("region delete rejected whole clip",{ord:n,sourceFilename:e.dataset.sourceFilename||"",selectionStartMs:a.startMs,selectionEndMs:a.endMs,durationMs:r,trigger:t}),null;const o=e.dataset.sourceFilename||"";if(!o)return null;const s=e.dataset.playbackState;return{ord:n,sourceFilename:o,selectionStartMs:Math.round(a.startMs),selectionEndMs:Math.round(a.endMs),cursorMs:Math.round(Number(e.dataset.cursorMs||"0")||0),durationMs:Math.round(r),trigger:t,playbackActive:Hr(s)&&s!=="stopped"}}function $l(e,t,n,r,a){e.preventDefault();const o=a.playbackStateFor(t),s=t.querySelector(".aqe-visualizer-svg"),i=Number(t.dataset.durationMs||"0");if(!s||!i)return;o==="playing"&&a.stopProgressClock(t);const l=f=>{a.setCursor(t,ko(f,s,i,t,a),!1)},c=f=>{window.removeEventListener("pointermove",l),window.removeEventListener("pointerup",c);const u=o==="playing";o==="paused"&&(t.dataset.resumeRequiresRestart="true");const d=ko(f,s,i,t,a),m=u&&a.audioClockReady(t)?"html":"";a.setCursor(t,d,r,{previousPlaybackState:o,restartPlayback:u,engine:m}),a.audioClockReady(t)&&a.seekAudioClock(t,d),u&&m==="html"&&a.startEditorHtmlPlayback(t,a.playbackRequestForStart(t,n,d,"html"))};l(e),window.addEventListener("pointermove",l),window.addEventListener("pointerup",c)}function Bl(e,t,n,r){e.preventDefault();const a=t.querySelector(".aqe-visualizer-svg"),o=Number(t.dataset.durationMs||"0");if(!a||!o)return;const s=r.playbackStateFor(t),i=r.currentProgressMs(t)??Number(t.dataset.cursorMs||"0"),l={clientX:e.clientX},c=Nn(e,a,o);let f=!1,u=A=>{},d=A=>{},m=()=>{},p=A=>{};const w=()=>{window.removeEventListener("pointermove",u),window.removeEventListener("pointerup",d),window.removeEventListener("pointercancel",m),window.removeEventListener("keydown",p),window.removeEventListener("blur",m),a.removeEventListener("lostpointercapture",m)},_=()=>{f||s!=="playing"||(f=!0,r.stopProgressClock(t,{clearEngine:!1}),r.setCursor(t,i,!1,{updateAnchor:!1}))},v=()=>{s==="playing"&&f&&r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,i,"html"))};u=A=>{const b=Nn(A,a,o);if(po(l,A,c,b)){r.clearSelectionDraft(t);return}_(),r.setSelectionDraft(t,c,b)},d=A=>{w();const b=Nn(A,a,o);if(po(l,A,c,b)){r.clearSelection(t),v();return}_(),r.draftSelectionForVisualizer(t)||r.setSelectionDraft(t,c,b,{redraw:!1});const E=r.commitSelectionDraft(t);if(s==="paused"&&(t.dataset.resumeRequiresRestart="true"),E&&s==="playing"){const F=r.selectionForVisualizer(t);r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,(F==null?void 0:F.startMs)??c,"html"))}},m=()=>{w(),r.clearSelectionDraft(t),v()},p=A=>{A.key==="Escape"&&m()},window.addEventListener("pointermove",u),window.addEventListener("pointerup",d),window.addEventListener("pointercancel",m),window.addEventListener("keydown",p),window.addEventListener("blur",m),a.addEventListener("lostpointercapture",m)}function Gl(e,t,n){const r=n.visualizerForOrd(t);if(r){if(e.shiftKey){Bl(e,r,t,n);return}$l(e,r,t,!0,n)}}function ko(e,t,n,r,a){const o=Nn(e,t,n),s=a.selectionForVisualizer(r);return s&&r.dataset.repeatEnabled==="true"?cl(o,s):o}function At(e){e.__aqePlaybackTimer&&(window.cancelAnimationFrame(e.__aqePlaybackTimer),e.__aqePlaybackTimer=null)}function Ao(e){const t=Number(e.dataset.durationMs||"0"),n=performance.now()-Number(e.dataset.playStartedAt||"0");return Math.min(t,Number(e.dataset.playStartMs||"0")+n)}function Eo(e){const t=Re(e);if(!t)return null;const n=Number(e.dataset.durationMs||"0");return Math.min(n,(Number(t.currentTime)||0)*1e3)}function Po(e){return e.dataset.progressClockMode==="audio"?Eo(e):e.dataset.progressClockMode==="manual"?Ao(e):Number(e.dataset.progressMs||e.dataset.cursorMs||"0")}function Ur(e,t,n,r={}){return t<Ul(e,n)?!1:n.repeatEnabledFor(e)?(Kl(e,n,r),!0):(Vl(e,n),!0)}function Vl(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=t.effectivePlaybackRegion(e),a=e.dataset.playbackRegionMode==="selection"?r.startMs:Number(e.dataset.anchorMs||"0");Xr(e,t),t.setCursor(e,a,!1,{updateAnchor:!1}),cr(e)&&fr(e,a,Number(e.dataset.durationMs||"0")),t.clearStatus(n),window.__aqeActiveField=n,t.focusAndSendCommand(n,"aqe:play-ended")}function Kr(e,t){const n=()=>{if(e.dataset.playbackState!=="playing")return;const r=Eo(e);if(r===null){rt(e,Number(e.dataset.cursorMs||"0"),t);return}t.setCursor(e,r,!1,{updateAnchor:!1}),!Ur(e,r,t)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(n))};e.__aqePlaybackTimer=window.requestAnimationFrame(n)}function rt(e,t,n){if(At(e),An(e),!Number(e.dataset.durationMs||"0"))return;const a=No(e,t);e.__aqeAudioClockFallback=!0,e.dataset.playbackState="playing",e.dataset.progressClockMode="manual",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),Yr(e,a,n),n.setPlaybackButtonLabel(e,"Pause");const o=()=>{if(e.dataset.playbackState!=="playing")return;const s=Ao(e);n.setCursor(e,s,!1,{updateAnchor:!1}),!Ur(e,s,n)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(o))};e.__aqePlaybackTimer=window.requestAnimationFrame(o)}function Hl(e,t,n,r={}){var i;const a=Re(e);if(!a||!fr(e,t,Number(e.dataset.durationMs||"0"))||typeof a.play!="function"){if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}rt(e,t,n);return}e.dataset.progressClockMode="audio",e.__aqeAudioClockFallback=!1;const o=()=>{var l;if(r.manualFallback===!1){(l=r.onAudioPlayFailed)==null||l.call(r);return}rt(e,t,n)},s=()=>{var l;e.dataset.playbackState==="playing"&&(At(e),e.dataset.progressClockMode="audio",he.info("html audio playback started",{ord:e.dataset.aqeFieldOrd}),Kr(e,n),(l=r.onAudioStarted)==null||l.call(r))};Promise.resolve(a.play()).then(s).catch(()=>{e.dataset.playbackState==="playing"&&(he.warn("html audio play rejected; using manual clock",{ord:e.dataset.aqeFieldOrd}),o())})}function Wl(e,t,n,r={}){var i;const a=r.engine||e.dataset.playbackEngine||"";if(Xr(e,n,{clearEngine:!1}),n.stopOtherPlayback(e),!Number(e.dataset.durationMs||"0"))return;const s=No(e,t);if(e.dataset.playbackEngine=a,e.dataset.playbackState="playing",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(s),Yr(e,s,n),n.setCursor(e,s,!1,{updateAnchor:!1}),n.setPlaybackButtonLabel(e,"Pause"),he.info("playback clock selected",{engine:a||"auto",startMs:s}),a==="native"){rt(e,s,n);return}if(cr(e)){Hl(e,s,n,r);return}if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}rt(e,s,n)}function jl(e,t){const n=Po(e);n!==null&&t.setCursor(e,n,!1,{updateAnchor:!1}),At(e),An(e),e.dataset.playbackState="paused",e.dataset.progressClockMode="stopped",t.setPlaybackButtonLabel(e,"Play")}function Xr(e,t,n={}){At(e),An(e),e.dataset.playbackState="stopped",e.dataset.progressClockMode="stopped",e.dataset.resumeRequiresRestart="false",n.clearEngine!==!1&&(e.dataset.playbackEngine=""),n.clearAudio&&Gr(e),t.setPlaybackButtonLabel(e,"Play")}function Yr(e,t,n,r=n.effectivePlaybackRegion(e)){e.dataset.playbackStartMs=String(Math.round(t)),e.dataset.playbackEndMs=String(Math.round(r.endMs)),e.dataset.playbackRegionMode=r.mode}function Ul(e,t){const n=t.effectivePlaybackRegion(e),r=Number(e.dataset.playbackEndMs||"0")||n.endMs;return Math.max(n.startMs,Math.min(r,Number(e.dataset.durationMs||"0")||0))}function Kl(e,t,n={}){const r=t.effectivePlaybackRegion(e),a=r.startMs;if(Yr(e,a,t,r),e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),t.setCursor(e,a,!1,{updateAnchor:!1}),e.dataset.progressClockMode!=="audio"||!cr(e)){rt(e,a,t);return}if(!fr(e,a,Number(e.dataset.durationMs||"0"))){rt(e,a,t);return}if(!n.forceAudioPlay){At(e),Kr(e,t);return}const o=Re(e);!o||typeof o.play!="function"||(At(e),Promise.resolve(o.play()).then(()=>{e.dataset.playbackState==="playing"&&Kr(e,t)}).catch(()=>{e.dataset.playbackState==="playing"&&rt(e,a,t)}))}function No(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function Fo(){return document.body.dataset.aqeBusy==="true"}function Co(){var e;return((e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.repeatPlaybackByDefault)===!0}function Xl(e){for(const t of $r())t!==e&&zt(t)!=="stopped"&&mt(t)}function Yl(){for(const e of $r())zt(e)!=="stopped"&&mt(e)}function Zt(e,t,n="",r=""){document.body.dataset.aqeBusy=t?"true":"false",document.querySelectorAll(".aqe-controls").forEach(s=>{s.dataset.busy=t?"true":"false"}),ir().forEach(s=>{s.disabled=!!t}),Il(),t||queueMicrotask(()=>mr(ra()));const a=nt(e),o=a==null?void 0:a.querySelector(".aqe-status");o&&(o.textContent=n||"",o.dataset.kind=t?"processing":"info",o.title=r||"")}function To(e,t="info"){const n=Number(window.__aqeActiveField??0),r=nt(n),a=r==null?void 0:r.querySelector(".aqe-status");a&&(a.textContent=e||"",a.dataset.kind=t||"info")}function Ql(e){const t=nt(e),n=t==null?void 0:t.querySelector(".aqe-status");n&&(n.textContent="",n.dataset.kind="info",n.title="")}function Jt(e,t,n){var o;const r=t==="aqe:play"?ro(e):t==="aqe:analyze"?no(e):((o=nt(e))==null?void 0:o.querySelector(`[data-aqe-command="${t}"]`))??null;if(!r)return;const a=r.querySelector(".aqe-button-label");a?a.textContent=n:r.textContent=n,t==="aqe:play"&&(r.dataset.aqeButtonState=n==="Pause"?"pause":"play"),t==="aqe:analyze"&&(r.dataset.aqeButtonState=n==="Redraw"?"redraw":"graph")}function Qr(e,t,n,r){if(!Fo()){if(typeof t.focus=="function"&&t.focus(),window.__aqeActiveField=n,he.info("command dispatched",{command:e,ord:n}),e==="aqe:analyze"){Oo(n,!0);return}if(!(e==="aqe:play"&&gu(n))){if(ne.has(e)&&(Yl(),Zt(n,!0,eo(e))),r){Bi(n,r);return}Yt(n,e)}}}function Zl(e){Br(e)}function Jl(e){At(e)}function zl(e){Gr(e)}function eu(e,t){Zi(e,t)}function tu(e){Ji(e,{onErrorDuringPlayback(){he.warn("audio clock failed during playback",{ord:e.dataset.aqeFieldOrd}),vu(e,Number(e.dataset.cursorMs||"0"))},onEndedDuringPlayback(){mu(e,Number(e.dataset.durationMs||"0"),{forceAudioPlay:!0})}})}function Zr(e){return cr(e)}function nu(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function xo(e){return Fn(e)}function Ro(e){return jr(e)}function Jr(e){return bo(e)}function zr(e,t){e.dataset.repeatEnabled=t?"true":"false";const n=Number(e.dataset.aqeFieldOrd||"0"),r=ao(n);r&&(r.ariaPressed=t?"true":"false",r.dataset.aqeButtonState=t?"active":"default")}function ru(e,t){const n=I(e);return n?(zr(n,t),!0):!1}function au(e,t={}){Qt(e,t)}function ou(e,t,n,r={}){return xl(e,t,n,r)}function su(e,t={}){const n=Rl(e,uu(),t);return Cn(e),n}function Tn(e,t={}){wo(e,t),Cn(e)}function iu(e){e.dataset.playbackStartMs="0",e.dataset.playbackEndMs=String(Number(e.dataset.durationMs||"0")||0),e.dataset.playbackRegionMode="full",zr(e,Co()),Tn(e,{resetPlaybackRegion:!1})}function lu(){return{audioClockReady:Zr,clearSelection:Tn,clearSelectionDraft:au,commitSelectionDraft:su,currentProgressMs:Bo,draftSelectionForVisualizer:Ro,playbackRequestForStart:cu,playbackStateFor:zt,seekAudioClock:Do,selectionForVisualizer:xo,setCursor:Et,setSelectionDraft:ou,startEditorHtmlPlayback:Wo,stopProgressClock:mt,visualizerForOrd:I}}function uu(){return{setCursor:Et}}function ea(e){return e.dataset.repeatEnabled==="true"}function xn(){return{clearStatus:Ql,effectivePlaybackRegion:Jr,focusAndSendCommand:Yt,playbackEngineFor:Rn,repeatEnabledFor:ea,setCursor:Et,setPlaybackButtonLabel:_u,stopOtherPlayback:Xl}}function cu(e,t,n,r=Rn(e)){const a=Jr(e);return{ord:t,action:"start",cursorMs:Math.round(nu(e,n)),endMs:Math.round(a.endMs),engine:r,loop:ea(e),regionMode:a.mode}}function Do(e,t){return fr(e,t,Number(e.dataset.durationMs||"0"))}function Et(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Math.max(0,Math.min(Number(t)||0,a||0));if(e.dataset.cursorMs=String(Math.round(o)),e.dataset.progressMs=String(Math.round(o)),r.updateAnchor!==!1&&(e.dataset.anchorMs=String(Math.round(o))),Fl(e,o,a),n){window.__aqeActiveField=Number(e.dataset.aqeFieldOrd||"0");const s={cursorMs:Math.round(o),previousPlaybackState:r.previousPlaybackState||zt(e),restartPlayback:!!r.restartPlayback};r.engine&&(s.engine=r.engine),Yi(s),he.info("cursor committed",s),Yt(window.__aqeActiveField,"aqe:set-cursor")}}function fu(e,t){var n;(n=I(t))==null||n.focus(),Gl(e,t,lu())}function Oo(e,t){Io(e)&&(window.__aqeActiveField=e,he.info("graph requested",{notifyPython:t,ord:e}),Zt(e,!0,"Analyzing...",""),Yt(e,"aqe:analyze"))}function Lo(e){Io(e.ord)&&(he.info("default graph requested",e),Zt(e.ord,!0,"Analyzing...",""),Gi(e))}function Io(e){const t=I(e);return t?(mt(t,{clearAudio:!0}),Al(t),Tn(t),Et(t,0,!1),Jt(e,"aqe:analyze","Redraw"),na(e,"Analyzing...","processing"),!0):!1}function du(e){return window.__aqePendingGraphRedrawField=e,ta()}function ta(){const e=window.__aqePendingGraphRedrawField;if(typeof e!="number")return!1;const t=I(e);return t?(t.dataset.graphBusy==="true"||t.dataset.hasTrack==="true"||Oo(e,!0),!0):!1}function na(e,t,n="info"){const r=I(e);r&&Pl(r,t,n)}function hu(e,t,n){const r=I(e);if(!r||!t)return;const a=dl(t);El(r,a),r.dataset.anchorMs=String(n||0),window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null),Tn(r),r.dataset.playbackStartMs="0",r.dataset.playbackEndMs=String(a.durationMs||0),r.dataset.playbackRegionMode="full",eu(r,a.sourceFilename||""),Jt(e,"aqe:analyze","Redraw"),Et(r,n||0,!1),Zr(r)&&Do(r,n||0),na(e,a.analyzerName||"","info"),Zt(e,!1,"",""),so(e,ra()),he.info("graph rendered",Tl(e,a))}function pu(e,t,n="info"){n!=="processing"&&window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null);const r=I(e);r&&(r.hidden=!1,r.dataset.graphActive="true",n==="processing"&&(r.dataset.hasTrack="false"),Jt(e,"aqe:analyze","Redraw")),na(e,t,n),n!=="processing"&&so(e,ra())}function ra(){return{anyBusy:Fo,requestDefaultGraph:Lo}}function $o(){document.body.dataset.aqeBusy="false",window.__aqeActiveField=null,window.__aqeLastCursorIntent=null,document.querySelectorAll(".aqe-controls").forEach(e=>{e.dataset.busy="false",e.dataset.aqeSourceFilename="",e.querySelectorAll(".aqe-button").forEach(o=>{o.disabled=!1,o.dataset.aqeCommand==="aqe:analyze"&&Jt(Number(e.dataset.aqeFieldOrd||"0"),"aqe:analyze","Graph"),o.dataset.aqeCommand==="aqe:play"&&Jt(Number(e.dataset.aqeFieldOrd||"0"),"aqe:play","Play")});const t=e.querySelector(".aqe-status");t&&(t.textContent="",t.dataset.kind="info",t.title="");const n=e.querySelector(".aqe-visualizer");if(!n)return;Jl(n),zl(n),n.hidden=!0,n.dataset.anchorMs="0",n.dataset.cursorMs="0",n.dataset.progressMs="0",n.dataset.graphActive="false",n.dataset.graphBusy="false",n.dataset.hasTrack="false",n.dataset.playbackState="stopped",n.dataset.playbackEngine="",n.dataset.resumeRequiresRestart="false",n.dataset.durationMs="0",n.dataset.sourceFilename="",n.dataset.analyzerName="",n.dataset.playStartedAt="0",n.dataset.playStartMs="0",n.dataset.playbackStartMs="0",n.dataset.playbackEndMs="0",n.dataset.playbackRegionMode="full",n.dataset.progressClockMode="stopped",zr(n,Co()),Tn(n),yo(n),Cl(n);const r=n.querySelector(".aqe-visualizer-status");r&&(r.textContent="",r.dataset.kind="info");const a=n.querySelector(".aqe-spinner");a&&(a.hidden=!0)})}function _u(e,t){const n=Number(e.dataset.aqeFieldOrd||"0");Jt(n,"aqe:play",t)}function Bo(e){return Po(e)}function mu(e,t,n={}){return Ur(e,t,xn(),n)}function vu(e,t){rt(e,t,xn())}function Go(e,t,n={}){Wl(e,t,xn(),n)}function Vo(e){jl(e,xn())}function mt(e,t={}){Xr(e,xn(),t)}function Ho(e){const t=I(e);return t?fl({anchorMs:Number(t.dataset.anchorMs||t.dataset.cursorMs||"0"),currentProgressMs:Bo(t),cursorMs:Number(t.dataset.cursorMs||"0"),engine:Rn(t),ord:e,playbackState:zt(t),region:Jr(t),repeat:ea(t),resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true"}):{ord:e,action:"start",cursorMs:0}}function Rn(e){if(!e||e.dataset.hasTrack!=="true")return"native";const t=e.dataset.playbackEngine||"";return e.dataset.playbackState!=="stopped"&&(t==="html"||t==="native")?t:Zr(e)?"html":"native"}function aa(e){const t=I(e.ord);t&&(t.dataset.playbackEngine=e.engine||""),Wi(e),window.__aqeActiveField=e.ord,he.info("playback request queued",e),Yt(e.ord,"aqe:play")}function Wo(e,t){return Go(e,t.cursorMs,{engine:"html",manualFallback:!1,onAudioStarted(){aa(t)},onAudioPlayFailed(){if(he.warn("html playback failed; falling back to native",{ord:t.ord}),mt(e),t.regionMode==="selection"||t.loop){window.__aqeActiveField=t.ord,To("Selected repeat playback needs browser audio.","warning");return}aa({...t,engine:"native"})}}),!0}function gu(e){const t=I(e);if(!t||Rn(t)!=="html")return!1;const n={...Ho(e),engine:"html"};return n.action==="pause"?(Vo(t),n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0"),aa(n),!0):(n.action==="resume"&&(n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0")),Wo(t,n))}function yu(e,t,n){const r=I(e);r&&((t==="playing"||t==="paused")&&(r.dataset.resumeRequiresRestart="false"),t==="playing"?Go(r,n,{engine:r.dataset.playbackEngine==="html"||r.dataset.playbackEngine==="native"?r.dataset.playbackEngine:""}):t==="paused"?Vo(r):mt(r))}function bu(){const e=ji();if(e)return e;const t=Number(window.__aqeActiveField||"0"),n=Ho(t),r=I(t);return r&&(r.dataset.playbackEngine=n.engine||""),n}function wu(e){const t=I(e);return t?(mt(t),!0):!1}function qu(){const e=Number(window.__aqeActiveField||"0"),t=I(e);return t?Number(t.dataset.cursorMs||"0"):0}function Mu(){const e=Number(window.__aqeActiveField||"0"),t=I(e),n=t?Number(t.dataset.cursorMs||"0"):0;return window.__aqeLastCursorIntent||{cursorMs:n,previousPlaybackState:t?zt(t):"stopped",restartPlayback:!1}}function zt(e){const t=e.dataset.playbackState;return Hr(t)?t:"stopped"}const jo=(gi=(vi=globalThis.process)==null?void 0:vi.env)==null?void 0:gi.NODE_ENV,y=jo&&!jo.toLowerCase().startsWith("prod");var oa=Array.isArray,Su=Array.prototype.indexOf,Pt=Array.prototype.includes,yr=Array.from,Nt=Object.defineProperty,at=Object.getOwnPropertyDescriptor,ku=Object.getOwnPropertyDescriptors,Au=Object.prototype,Eu=Array.prototype,Uo=Object.getPrototypeOf,Ko=Object.isExtensible;function Dn(e){return typeof e=="function"}const W=()=>{};function Pu(e){for(var t=0;t<e.length;t++)e[t]()}function Xo(){var e,t,n=new Promise((r,a)=>{e=r,t=a});return{promise:n,resolve:e,reject:t}}function Nu(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const r of e)if(n.push(r),n.length===t)break;return n}const ie=2,On=4,br=8,sa=1<<24,ot=16,De=32,Ft=64,ia=128,Ae=512,ae=1024,le=2048,Oe=4096,be=8192,st=16384,Ct=32768,vt=65536,wr=1<<17,Yo=1<<18,en=1<<19,Fu=1<<20,it=1<<25,gt=65536,la=1<<21,qr=1<<22,yt=1<<23,lt=Symbol("$state"),Qo=Symbol("legacy props"),Cu=Symbol(""),Zo=Symbol("proxy path"),Tt=new class extends Error{constructor(){super(...arguments);tt(this,"name","StaleReactionError");tt(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}},ua=!!((yi=globalThis.document)!=null&&yi.contentType)&&globalThis.document.contentType.includes("xml");function Jo(e){if(y){const t=new Error(`lifecycle_outside_component
\`${e}(...)\` can only be used during component initialisation
https://svelte.dev/e/lifecycle_outside_component`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/lifecycle_outside_component")}function Tu(){if(y){const e=new Error("async_derived_orphan\nCannot create a `$derived(...)` with an `await` expression outside of an effect tree\nhttps://svelte.dev/e/async_derived_orphan");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/async_derived_orphan")}function xu(){if(y){const e=new Error(`derived_references_self
A derived value cannot reference itself recursively
https://svelte.dev/e/derived_references_self`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/derived_references_self")}function zo(e,t,n){if(y){const r=new Error(`each_key_duplicate
${n?`Keyed each block has duplicate key \`${n}\` at indexes ${e} and ${t}`:`Keyed each block has duplicate key at indexes ${e} and ${t}`}
https://svelte.dev/e/each_key_duplicate`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_duplicate")}function Ru(e,t,n){if(y){const r=new Error(`each_key_volatile
Keyed each block has key that is not idempotent — the key for item at index ${e} was \`${t}\` but is now \`${n}\`. Keys must be the same each time for a given item
https://svelte.dev/e/each_key_volatile`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_volatile")}function Du(e){if(y){const t=new Error(`effect_in_teardown
\`${e}\` cannot be used inside an effect cleanup function
https://svelte.dev/e/effect_in_teardown`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_in_teardown")}function Ou(){if(y){const e=new Error("effect_in_unowned_derived\nEffect cannot be created inside a `$derived` value that was not itself created inside an effect\nhttps://svelte.dev/e/effect_in_unowned_derived");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Lu(e){if(y){const t=new Error(`effect_orphan
\`${e}\` can only be used inside an effect (e.g. during component initialisation)
https://svelte.dev/e/effect_orphan`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_orphan")}function Iu(){if(y){const e=new Error(`effect_update_depth_exceeded
Maximum update depth exceeded. This typically indicates that an effect reads and writes the same piece of state
https://svelte.dev/e/effect_update_depth_exceeded`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function $u(){if(y){const e=new Error("invalid_snippet\nCould not `{@render}` snippet due to the expression being `null` or `undefined`. Consider using optional chaining `{@render snippet?.()}`\nhttps://svelte.dev/e/invalid_snippet");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/invalid_snippet")}function Bu(e){if(y){const t=new Error(`props_invalid_value
Cannot do \`bind:${e}={undefined}\` when \`${e}\` has a fallback value
https://svelte.dev/e/props_invalid_value`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_invalid_value")}function Gu(e){if(y){const t=new Error(`props_rest_readonly
Rest element properties of \`$props()\` such as \`${e}\` are readonly
https://svelte.dev/e/props_rest_readonly`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_rest_readonly")}function Vu(e){if(y){const t=new Error(`rune_outside_svelte
The \`${e}\` rune is only available inside \`.svelte\` and \`.svelte.js/ts\` files
https://svelte.dev/e/rune_outside_svelte`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/rune_outside_svelte")}function Hu(){if(y){const e=new Error("state_descriptors_fixed\nProperty descriptors defined on `$state` objects must contain `value` and always be `enumerable`, `configurable` and `writable`.\nhttps://svelte.dev/e/state_descriptors_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function Wu(){if(y){const e=new Error("state_prototype_fixed\nCannot set prototype of `$state` object\nhttps://svelte.dev/e/state_prototype_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_prototype_fixed")}function ju(){if(y){const e=new Error("state_unsafe_mutation\nUpdating state inside `$derived(...)`, `$inspect(...)` or a template expression is forbidden. If the value should not be reactive, declare it without `$state`\nhttps://svelte.dev/e/state_unsafe_mutation");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Uu(){if(y){const e=new Error("svelte_boundary_reset_onerror\nA `<svelte:boundary>` `reset` function cannot be called while an error is still being handled\nhttps://svelte.dev/e/svelte_boundary_reset_onerror");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Ku=1,Xu=2,es=4,Yu=8,Qu=16,Zu=1,Ju=4,zu=8,ec=16,tc=1,nc=2,oe=Symbol(),rc=Symbol("filename"),ts="http://www.w3.org/1999/xhtml",ac="http://www.w3.org/2000/svg",oc="@attach";var Ln="font-weight: bold",In="font-weight: normal";function sc(){y?console.warn(`%c[svelte] lifecycle_double_unmount
%cTried to unmount a component that was not mounted
https://svelte.dev/e/lifecycle_double_unmount`,Ln,In):console.warn("https://svelte.dev/e/lifecycle_double_unmount")}function ic(){y?console.warn("%c[svelte] select_multiple_invalid_value\n%cThe `value` property of a `<select multiple>` element should be an array, but it received a non-array value. The selection will be kept as is.\nhttps://svelte.dev/e/select_multiple_invalid_value",Ln,In):console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function ca(e){y?console.warn(`%c[svelte] state_proxy_equality_mismatch
%cReactive \`$state(...)\` proxies and the values they proxy have different identities. Because of this, comparisons with \`${e}\` will produce unexpected results
https://svelte.dev/e/state_proxy_equality_mismatch`,Ln,In):console.warn("https://svelte.dev/e/state_proxy_equality_mismatch")}function lc(){y?console.warn(`%c[svelte] state_proxy_unmount
%cTried to unmount a state proxy, rather than a component
https://svelte.dev/e/state_proxy_unmount`,Ln,In):console.warn("https://svelte.dev/e/state_proxy_unmount")}function uc(){y?console.warn("%c[svelte] svelte_boundary_reset_noop\n%cA `<svelte:boundary>` `reset` function only resets the boundary the first time it is called\nhttps://svelte.dev/e/svelte_boundary_reset_noop",Ln,In):console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function ns(e){return e===this.v}function cc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function rs(e){return!cc(e,this.v)}let fc=!1;function je(e,t){return e.label=t,as(e.v,t),e}function as(e,t){var n;return(n=e==null?void 0:e[Zo])==null||n.call(e,t),e}function dc(e){const t=new Error,n=hc();return n.length===0?null:(n.unshift(`
`),Nt(t,"stack",{value:n.join(`
`)}),Nt(t,"name",{value:e}),t)}function hc(){const e=Error.stackTraceLimit;Error.stackTraceLimit=1/0;const t=new Error().stack;if(Error.stackTraceLimit=e,!t)return[];const n=t.split(`
`),r=[];for(let a=0;a<n.length;a++){const o=n[a],s=o.replaceAll("\\","/");if(o.trim()!=="Error"){if(o.includes("validate_each_keys"))return[];s.includes("svelte/src/internal")||s.includes("node_modules/.vite")||r.push(o)}}return r}let U=null;function tn(e){U=e}let nn=null;function Mr(e){nn=e}let $n=null;function os(e){$n=e}function pc(e){return _c("getContext").get(e)}function $(e,t=!1,n){U={p:U,i:!1,c:null,e:null,s:e,x:null,l:null},y&&(U.function=n,$n=n)}function B(e){var t=U,n=t.e;if(n!==null){t.e=null;for(var r of n)Ps(r)}return t.i=!0,U=t.p,y&&($n=(U==null?void 0:U.function)??null),{}}function ss(){return!0}function _c(e){return U===null&&Jo(e),U.c??(U.c=new Map(mc(U)||void 0))}function mc(e){let t=e.p;for(;t!==null;){const n=t.c;if(n!==null)return n;t=t.p}return null}let rn=[];function vc(){var e=rn;rn=[],Pu(e)}function Ue(e){if(rn.length===0){var t=rn;queueMicrotask(()=>{t===rn&&vc()})}rn.push(e)}const fa=new WeakMap;function is(e){var t=D;if(t===null)return x.f|=yt,e;if(y&&e instanceof Error&&!fa.has(e)&&fa.set(e,gc(e,t)),(t.f&Ct)===0&&(t.f&On)===0)throw y&&!t.parent&&e instanceof Error&&ls(e),e;bt(e,t)}function bt(e,t){for(;t!==null;){if((t.f&ia)!==0){if((t.f&Ct)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw y&&e instanceof Error&&ls(e),e}function gc(e,t){var s,i,l;const n=at(e,"message");if(!(n&&!n.configurable)){for(var r=ya?"  ":"	",a=`
${r}in ${((s=t.fn)==null?void 0:s.name)||"<unknown>"}`,o=t.ctx;o!==null;)a+=`
${r}in ${(i=o.function)==null?void 0:i[rc].split("/").pop()}`,o=o.p;return{message:e.message+`
${a}
`,stack:(l=e.stack)==null?void 0:l.split(`
`).filter(c=>!c.includes("svelte/src/internal")).join(`
`)}}}function ls(e){const t=fa.get(e);t&&(Nt(e,"message",{value:t.message}),Nt(e,"stack",{value:t.stack}))}const yc=-7169;function Z(e,t){e.f=e.f&yc|t}function da(e){(e.f&Ae)!==0||e.deps===null?Z(e,ae):Z(e,Oe)}function us(e){if(e!==null)for(const t of e)(t.f&ie)===0||(t.f&gt)===0||(t.f^=gt,us(t.deps))}function cs(e,t,n){(e.f&le)!==0?t.add(e):(e.f&Oe)!==0&&n.add(e),us(e.deps),Z(e,ae)}const Sr=new Set;let L=null,ue=null,Ee=[],ha=null,pa=!1;const Wa=class Wa{constructor(){R(this,qe);tt(this,"current",new Map);tt(this,"previous",new Map);R(this,pn,new Set);R(this,_n,new Set);R(this,$t,0);R(this,mn,0);R(this,Jn,null);R(this,zn,new Set);R(this,Bt,new Set);R(this,ft,new Map);tt(this,"is_fork",!1);R(this,vn,!1)}skip_effect(t){h(this,ft).has(t)||h(this,ft).set(t,{d:[],m:[]})}unskip_effect(t){var n=h(this,ft).get(t);if(n){h(this,ft).delete(t);for(var r of n.d)Z(r,le),Ie(r);for(r of n.m)Z(r,Oe),Ie(r)}}process(t){var a;Ee=[],this.apply();var n=[],r=[];for(const o of t)se(this,qe,Qa).call(this,o,n,r);if(se(this,qe,Ya).call(this)){se(this,qe,Za).call(this,r),se(this,qe,Za).call(this,n);for(const[o,s]of h(this,ft))ps(o,s)}else{for(const o of h(this,pn))o();h(this,pn).clear(),h(this,$t)===0&&se(this,qe,$i).call(this),L=null,fs(r),fs(n),(a=h(this,Jn))==null||a.resolve()}ue=null}capture(t,n){n!==oe&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&yt)===0&&(this.current.set(t,t.v),ue==null||ue.set(t,t.v))}activate(){L=this,this.apply()}deactivate(){L===this&&(L=null,ue=null)}flush(){if(this.activate(),Ee.length>0){if(bc(),L!==null&&L!==this)return}else h(this,$t)===0&&this.process([]);this.deactivate()}discard(){for(const t of h(this,_n))t(this);h(this,_n).clear()}increment(t){T(this,$t,h(this,$t)+1),t&&T(this,mn,h(this,mn)+1)}decrement(t){T(this,$t,h(this,$t)-1),t&&T(this,mn,h(this,mn)-1),!h(this,vn)&&(T(this,vn,!0),Ue(()=>{T(this,vn,!1),se(this,qe,Ya).call(this)?Ee.length>0&&this.flush():this.revive()}))}revive(){for(const t of h(this,zn))h(this,Bt).delete(t),Z(t,le),Ie(t);for(const t of h(this,Bt))Z(t,Oe),Ie(t);this.flush()}oncommit(t){h(this,pn).add(t)}ondiscard(t){h(this,_n).add(t)}settled(){return(h(this,Jn)??T(this,Jn,Xo())).promise}static ensure(){if(L===null){const t=L=new Wa;Sr.add(L),Ue(()=>{L===t&&t.flush()})}return L}apply(){}};pn=new WeakMap,_n=new WeakMap,$t=new WeakMap,mn=new WeakMap,Jn=new WeakMap,zn=new WeakMap,Bt=new WeakMap,ft=new WeakMap,vn=new WeakMap,qe=new WeakSet,Ya=function(){return this.is_fork||h(this,mn)>0},Qa=function(t,n,r){t.f^=ae;for(var a=t.first;a!==null;){var o=a.f,s=(o&(De|Ft))!==0,i=s&&(o&ae)!==0,l=i||(o&be)!==0||h(this,ft).has(a);if(!l&&a.fn!==null){s?a.f^=ae:(o&On)!==0?n.push(a):Wn(a)&&((o&ot)!==0&&h(this,Bt).add(a),un(a));var c=a.first;if(c!==null){a=c;continue}}for(;a!==null;){var f=a.next;if(f!==null){a=f;break}a=a.parent}}},Za=function(t){for(var n=0;n<t.length;n+=1)cs(t[n],h(this,zn),h(this,Bt))},$i=function(){var a;if(Sr.size>1){this.previous.clear();var t=ue,n=!0;for(const o of Sr){if(o===this){n=!1;continue}const s=[];for(const[l,c]of this.current){if(o.current.has(l))if(n&&c!==o.current.get(l))o.current.set(l,c);else continue;s.push(l)}if(s.length===0)continue;const i=[...o.current.keys()].filter(l=>!this.current.has(l));if(i.length>0){var r=Ee;Ee=[];const l=new Set,c=new Map;for(const f of s)ds(f,i,l,c);if(Ee.length>0){L=o,o.apply();for(const f of Ee)se(a=o,qe,Qa).call(a,f,[],[]);o.deactivate()}Ee=r}}L=null,ue=t}Sr.delete(this)};let wt=Wa;function bc(){pa=!0;var e=y?new Set:null;try{for(var t=0;Ee.length>0;){var n=wt.ensure();if(t++>1e3){if(y){var r=new Map;for(const o of n.current.keys())for(const[s,i]of o.updated??[]){var a=r.get(s);a||(a={error:i.error,count:0},r.set(s,a)),a.count+=i.count}for(const o of r.values())o.error&&console.error(o.error)}wc()}if(n.process(Ee),qt.clear(),y)for(const o of n.current.keys())e.add(o)}}finally{if(Ee=[],pa=!1,ha=null,y)for(const o of e)o.updated=null}}function wc(){try{Iu()}catch(e){y&&Nt(e,"stack",{value:""}),bt(e,ha)}}let Le=null;function fs(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var r=e[n++];if((r.f&(st|be))===0&&Wn(r)&&(Le=new Set,un(r),r.deps===null&&r.first===null&&r.nodes===null&&r.teardown===null&&r.ac===null&&Ts(r),(Le==null?void 0:Le.size)>0)){qt.clear();for(const a of Le){if((a.f&(st|be))!==0)continue;const o=[a];let s=a.parent;for(;s!==null;)Le.has(s)&&(Le.delete(s),o.push(s)),s=s.parent;for(let i=o.length-1;i>=0;i--){const l=o[i];(l.f&(st|be))===0&&un(l)}}Le.clear()}}Le=null}}function ds(e,t,n,r){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const a of e.reactions){const o=a.f;(o&ie)!==0?ds(a,t,n,r):(o&(qr|ot))!==0&&(o&le)===0&&hs(a,t,r)&&(Z(a,le),Ie(a))}}function hs(e,t,n){const r=n.get(e);if(r!==void 0)return r;if(e.deps!==null)for(const a of e.deps){if(Pt.call(t,a))return!0;if((a.f&ie)!==0&&hs(a,t,n))return n.set(a,!0),!0}return n.set(e,!1),!1}function Ie(e){var t=ha=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(On|br|sa))!==0&&(e.f&Ct)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var r=t.f;if(pa&&t===D&&(r&ot)!==0&&(r&Yo)===0&&(r&Ct)!==0)return;if((r&(Ft|De))!==0){if((r&ae)===0)return;t.f^=ae}}Ee.push(t)}function ps(e,t){if(!((e.f&De)!==0&&(e.f&ae)!==0)){(e.f&le)!==0?t.d.push(e):(e.f&Oe)!==0&&t.m.push(e),Z(e,ae);for(var n=e.first;n!==null;)ps(n,t),n=n.next}}function qc(e){let t=0,n=xt(0),r;return y&&je(n,"createSubscriber version"),()=>{wa()&&(k(n),Ns(()=>(t===0&&(r=Pr(()=>e(()=>Bn(n)))),t+=1,()=>{Ue(()=>{t-=1,t===0&&(r==null||r(),r=void 0,Bn(n))})})))}}var Mc=vt|en;function Sc(e,t,n,r){new kc(e,t,n,r)}class kc{constructor(t,n,r,a){R(this,re);tt(this,"parent");tt(this,"is_pending",!1);tt(this,"transform_error");R(this,Te);R(this,ja,null);R(this,Qe);R(this,Gt);R(this,ge);R(this,Ze,null);R(this,Me,null);R(this,Ge,null);R(this,dt,null);R(this,Vt,0);R(this,kt,0);R(this,gn,!1);R(this,yn,new Set);R(this,bn,new Set);R(this,Je,null);R(this,Tr,qc(()=>(T(this,Je,xt(h(this,Vt))),y&&je(h(this,Je),"$effect.pending()"),()=>{T(this,Je,null)})));var o;T(this,Te,t),T(this,Qe,n),T(this,Gt,s=>{var i=D;i.b=this,i.f|=ia,r(s)}),this.parent=D.b,this.transform_error=a??((o=this.parent)==null?void 0:o.transform_error)??(s=>s),T(this,ge,Hn(()=>{se(this,re,Ja).call(this)},Mc))}defer_effect(t){cs(t,h(this,yn),h(this,bn))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!h(this,Qe).pending}update_pending_count(t){se(this,re,za).call(this,t),T(this,Vt,h(this,Vt)+t),!(!h(this,Je)||h(this,gn))&&(T(this,gn,!0),Ue(()=>{T(this,gn,!1),h(this,Je)&&on(h(this,Je),h(this,Vt))}))}get_effect_pending(){return h(this,Tr).call(this),k(h(this,Je))}error(t){var n=h(this,Qe).onerror;let r=h(this,Qe).failed;if(!n&&!r)throw t;h(this,Ze)&&(ce(h(this,Ze)),T(this,Ze,null)),h(this,Me)&&(ce(h(this,Me)),T(this,Me,null)),h(this,Ge)&&(ce(h(this,Ge)),T(this,Ge,null));var a=!1,o=!1;const s=()=>{if(a){uc();return}a=!0,o&&Uu(),h(this,Ge)!==null&&Dt(h(this,Ge),()=>{T(this,Ge,null)}),se(this,re,Lr).call(this,()=>{wt.ensure(),se(this,re,Ja).call(this)})},i=l=>{try{o=!0,n==null||n(l,s),o=!1}catch(c){bt(c,h(this,ge)&&h(this,ge).parent)}r&&T(this,Ge,se(this,re,Lr).call(this,()=>{wt.ensure();try{return me(()=>{var c=D;c.b=this,c.f|=ia,r(h(this,Te),()=>l,()=>s)})}catch(c){return bt(c,h(this,ge).parent),null}}))};Ue(()=>{var l;try{l=this.transform_error(t)}catch(c){bt(c,h(this,ge)&&h(this,ge).parent);return}l!==null&&typeof l=="object"&&typeof l.then=="function"?l.then(i,c=>bt(c,h(this,ge)&&h(this,ge).parent)):i(l)})}}Te=new WeakMap,ja=new WeakMap,Qe=new WeakMap,Gt=new WeakMap,ge=new WeakMap,Ze=new WeakMap,Me=new WeakMap,Ge=new WeakMap,dt=new WeakMap,Vt=new WeakMap,kt=new WeakMap,gn=new WeakMap,yn=new WeakMap,bn=new WeakMap,Je=new WeakMap,Tr=new WeakMap,re=new WeakSet,mh=function(){try{T(this,Ze,me(()=>h(this,Gt).call(this,h(this,Te))))}catch(t){this.error(t)}},vh=function(t){const n=h(this,Qe).failed;n&&T(this,Ge,me(()=>{n(h(this,Te),()=>t,()=>()=>{})}))},gh=function(){const t=h(this,Qe).pending;t&&(this.is_pending=!0,T(this,Me,me(()=>t(h(this,Te)))),Ue(()=>{var n=T(this,dt,document.createDocumentFragment()),r=ut();n.append(r),T(this,Ze,se(this,re,Lr).call(this,()=>(wt.ensure(),me(()=>h(this,Gt).call(this,r))))),h(this,kt)===0&&(h(this,Te).before(n),T(this,dt,null),Dt(h(this,Me),()=>{T(this,Me,null)}),se(this,re,Or).call(this))}))},Ja=function(){try{if(this.is_pending=this.has_pending_snippet(),T(this,kt,0),T(this,Vt,0),T(this,Ze,me(()=>{h(this,Gt).call(this,h(this,Te))})),h(this,kt)>0){var t=T(this,dt,document.createDocumentFragment());Ds(h(this,Ze),t);const n=h(this,Qe).pending;T(this,Me,me(()=>n(h(this,Te))))}else se(this,re,Or).call(this)}catch(n){this.error(n)}},Or=function(){this.is_pending=!1;for(const t of h(this,yn))Z(t,le),Ie(t);for(const t of h(this,bn))Z(t,Oe),Ie(t);h(this,yn).clear(),h(this,bn).clear()},Lr=function(t){var n=D,r=x,a=U;Be(h(this,ge)),Ne(h(this,ge)),tn(h(this,ge).ctx);try{return t()}catch(o){return is(o),null}finally{Be(n),Ne(r),tn(a)}},za=function(t){var n;if(!this.has_pending_snippet()){this.parent&&se(n=this.parent,re,za).call(n,t);return}T(this,kt,h(this,kt)+t),h(this,kt)===0&&(se(this,re,Or).call(this),h(this,Me)&&Dt(h(this,Me),()=>{T(this,Me,null)}),h(this,dt)&&(h(this,Te).before(h(this,dt)),T(this,dt,null)))};function _s(e,t,n,r){const a=kr;var o=e.filter(u=>!u.settled);if(n.length===0&&o.length===0){r(t.map(a));return}var s=D,i=Ac(),l=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(u=>u.promise)):null;function c(u){i();try{r(u)}catch(d){(s.f&st)===0&&bt(d,s)}_a()}if(n.length===0){l.then(()=>c(t.map(a)));return}function f(){i(),Promise.all(n.map(u=>Nc(u))).then(u=>c([...t.map(a),...u])).catch(u=>bt(u,s))}l?l.then(f):f()}function Ac(){var e=D,t=x,n=U,r=L;if(y)var a=nn;return function(s=!0){Be(e),Ne(t),tn(n),s&&(r==null||r.activate()),y&&Mr(a)}}function _a(e=!0){Be(null),Ne(null),tn(null),e&&(L==null||L.deactivate()),y&&Mr(null)}function Ec(){var e=D.b,t=L,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}const Pc=new Set;function kr(e){var t=ie|le,n=x!==null&&(x.f&ie)!==0?x:null;return D!==null&&(D.f|=en),{ctx:U,deps:null,effects:null,equals:ns,f:t,fn:e,reactions:null,rv:0,v:oe,wv:0,parent:n??D,ac:null}}function Nc(e,t,n){D===null&&Tu();var a=void 0,o=xt(oe);y&&(o.label=t);var s=!x,i=new Map;return Uc(()=>{var d;var l=Xo();a=l.promise;try{Promise.resolve(e()).then(l.resolve,l.reject).finally(_a)}catch(m){l.reject(m),_a()}var c=L;if(s){var f=Ec();(d=i.get(c))==null||d.reject(Tt),i.delete(c),i.set(c,l)}const u=(m,p=void 0)=>{if(c.activate(),p)p!==Tt&&(o.f|=yt,on(o,p));else{(o.f&yt)!==0&&(o.f^=yt),on(o,m);for(const[w,_]of i){if(i.delete(w),w===c)break;_.reject(Tt)}}f&&f()};l.promise.then(u,m=>u(null,m||"unknown"))}),qa(()=>{for(const l of i.values())l.reject(Tt)}),y&&(o.f|=qr),new Promise(l=>{function c(f){function u(){f===a?l(o):c(a)}f.then(u,u)}c(a)})}function Ar(e){const t=kr(e);return Ls(t),t}function ms(e){const t=kr(e);return t.equals=rs,t}function vs(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)ce(t[n])}}let ma=[];function Fc(e){for(var t=e.parent;t!==null;){if((t.f&ie)===0)return(t.f&st)===0?t:null;t=t.parent}return null}function va(e){var t,n=D;if(Be(Fc(e)),y){let r=an;bs(new Set);try{Pt.call(ma,e)&&xu(),ma.push(e),e.f&=~gt,vs(e),t=Aa(e)}finally{Be(n),bs(r),ma.pop()}}else try{e.f&=~gt,vs(e),t=Aa(e)}finally{Be(n)}return t}function gs(e){var t=va(e);if(!e.equals(t)&&(e.wv=Bs(),(!(L!=null&&L.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){Z(e,ae);return}Mt||(ue!==null?(wa()||L!=null&&L.is_fork)&&ue.set(e,t):da(e))}function Cc(e){var t,n;if(e.effects!==null)for(const r of e.effects)(r.teardown||r.ac)&&((t=r.teardown)==null||t.call(r),(n=r.ac)==null||n.abort(Tt),r.teardown=W,r.ac=null,jn(r,0),Sa(r))}function ys(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&un(t)}let an=new Set;const qt=new Map;function bs(e){an=e}let ga=!1;function Tc(){ga=!0}function xt(e,t){var n={f:0,v:e,reactions:null,equals:ns,rv:0,wv:0};return n}function Ke(e,t){const n=xt(e);return Ls(n),n}function xc(e,t=!1,n=!0){const r=xt(e);return t||(r.equals=rs),r}function Pe(e,t,n=!1){x!==null&&(!$e||(x.f&wr)!==0)&&ss()&&(x.f&(ie|ot|qr|wr))!==0&&(Fe===null||!Pt.call(Fe,e))&&ju();let r=n?sn(t):t;return y&&as(r,e.label),on(e,r)}function on(e,t){var a;if(!e.equals(t)){var n=e.v;Mt?qt.set(e,t):qt.set(e,n),e.v=t;var r=wt.ensure();if(r.capture(e,n),y){if(D!==null){e.updated??(e.updated=new Map);const o=(((a=e.updated.get(""))==null?void 0:a.count)??0)+1;if(e.updated.set("",{error:null,count:o}),o>5){const s=dc("updated at");if(s!==null){let i=e.updated.get(s.stack);i||(i={error:s,count:0},e.updated.set(s.stack,i)),i.count++}}}D!==null&&(e.set_during_effect=!0)}if((e.f&ie)!==0){const o=e;(e.f&le)!==0&&va(o),da(o)}e.wv=Bs(),qs(e,le),D!==null&&(D.f&ae)!==0&&(D.f&(De|Ft))===0&&(Ce===null?Yc([e]):Ce.push(e)),!r.is_fork&&an.size>0&&!ga&&ws()}return t}function ws(){ga=!1;for(const e of an)(e.f&ae)!==0&&Z(e,Oe),Wn(e)&&un(e);an.clear()}function Bn(e){Pe(e,e.v+1)}function qs(e,t){var n=e.reactions;if(n!==null)for(var r=n.length,a=0;a<r;a++){var o=n[a],s=o.f;if(y&&(s&wr)!==0){an.add(o);continue}var i=(s&le)===0;if(i&&Z(o,t),(s&ie)!==0){var l=o;ue==null||ue.delete(l),(s&gt)===0&&(s&Ae&&(o.f|=gt),qs(l,Oe))}else i&&((s&ot)!==0&&Le!==null&&Le.add(o),Ie(o))}}const Rc=/^[a-zA-Z_$][a-zA-Z_$0-9]*$/;function sn(e){if(typeof e!="object"||e===null||lt in e)return e;const t=Uo(e);if(t!==Au&&t!==Eu)return e;var n=new Map,r=oa(e),a=Ke(0),o=Lt,s=f=>{if(Lt===o)return f();var u=x,d=Lt;Ne(null),$s(o);var m=f();return Ne(u),$s(d),m};r&&(n.set("length",Ke(e.length)),y&&(e=Lc(e)));var i="";let l=!1;function c(f){if(!l){l=!0,i=f,je(a,`${i} version`);for(const[u,d]of n)je(d,Rt(i,u));l=!1}}return new Proxy(e,{defineProperty(f,u,d){(!("value"in d)||d.configurable===!1||d.enumerable===!1||d.writable===!1)&&Hu();var m=n.get(u);return m===void 0?s(()=>{var p=Ke(d.value);return n.set(u,p),y&&typeof u=="string"&&je(p,Rt(i,u)),p}):Pe(m,d.value,!0),!0},deleteProperty(f,u){var d=n.get(u);if(d===void 0){if(u in f){const m=s(()=>Ke(oe));n.set(u,m),Bn(a),y&&je(m,Rt(i,u))}}else Pe(d,oe),Bn(a);return!0},get(f,u,d){var _;if(u===lt)return e;if(y&&u===Zo)return c;var m=n.get(u),p=u in f;if(m===void 0&&(!p||(_=at(f,u))!=null&&_.writable)&&(m=s(()=>{var v=sn(p?f[u]:oe),A=Ke(v);return y&&je(A,Rt(i,u)),A}),n.set(u,m)),m!==void 0){var w=k(m);return w===oe?void 0:w}return Reflect.get(f,u,d)},getOwnPropertyDescriptor(f,u){var d=Reflect.getOwnPropertyDescriptor(f,u);if(d&&"value"in d){var m=n.get(u);m&&(d.value=k(m))}else if(d===void 0){var p=n.get(u),w=p==null?void 0:p.v;if(p!==void 0&&w!==oe)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return d},has(f,u){var w;if(u===lt)return!0;var d=n.get(u),m=d!==void 0&&d.v!==oe||Reflect.has(f,u);if(d!==void 0||D!==null&&(!m||(w=at(f,u))!=null&&w.writable)){d===void 0&&(d=s(()=>{var _=m?sn(f[u]):oe,v=Ke(_);return y&&je(v,Rt(i,u)),v}),n.set(u,d));var p=k(d);if(p===oe)return!1}return m},set(f,u,d,m){var P;var p=n.get(u),w=u in f;if(r&&u==="length")for(var _=d;_<p.v;_+=1){var v=n.get(_+"");v!==void 0?Pe(v,oe):_ in f&&(v=s(()=>Ke(oe)),n.set(_+"",v),y&&je(v,Rt(i,_)))}if(p===void 0)(!w||(P=at(f,u))!=null&&P.writable)&&(p=s(()=>Ke(void 0)),y&&je(p,Rt(i,u)),Pe(p,sn(d)),n.set(u,p));else{w=p.v!==oe;var A=s(()=>sn(d));Pe(p,A)}var b=Reflect.getOwnPropertyDescriptor(f,u);if(b!=null&&b.set&&b.set.call(m,d),!w){if(r&&typeof u=="string"){var E=n.get("length"),F=Number(u);Number.isInteger(F)&&F>=E.v&&Pe(E,F+1)}Bn(a)}return!0},ownKeys(f){k(a);var u=Reflect.ownKeys(f).filter(p=>{var w=n.get(p);return w===void 0||w.v!==oe});for(var[d,m]of n)m.v!==oe&&!(d in f)&&u.push(d);return u},setPrototypeOf(){Wu()}})}function Rt(e,t){return typeof t=="symbol"?`${e}[Symbol(${t.description??""})]`:Rc.test(t)?`${e}.${t}`:/^\d+$/.test(t)?`${e}[${t}]`:`${e}['${t}']`}function Gn(e){try{if(e!==null&&typeof e=="object"&&lt in e)return e[lt]}catch{}return e}function Dc(e,t){return Object.is(Gn(e),Gn(t))}const Oc=new Set(["copyWithin","fill","pop","push","reverse","shift","sort","splice","unshift"]);function Lc(e){return new Proxy(e,{get(t,n,r){var a=Reflect.get(t,n,r);return Oc.has(n)?function(...o){Tc();var s=a.apply(this,o);return ws(),s}:a}})}function Ic(){const e=Array.prototype,t=Array.__svelte_cleanup;t&&t();const{indexOf:n,lastIndexOf:r,includes:a}=e;e.indexOf=function(o,s){const i=n.call(this,o,s);if(i===-1){for(let l=s??0;l<this.length;l+=1)if(Gn(this[l])===o){ca("array.indexOf(...)");break}}return i},e.lastIndexOf=function(o,s){const i=r.call(this,o,s??this.length-1);if(i===-1){for(let l=0;l<=(s??this.length-1);l+=1)if(Gn(this[l])===o){ca("array.lastIndexOf(...)");break}}return i},e.includes=function(o,s){const i=a.call(this,o,s);if(!i){for(let l=0;l<this.length;l+=1)if(Gn(this[l])===o){ca("array.includes(...)");break}}return i},Array.__svelte_cleanup=()=>{e.indexOf=n,e.lastIndexOf=r,e.includes=a}}var Ms,ya,Ss,ks;function $c(){if(Ms===void 0){Ms=window,ya=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;Ss=at(t,"firstChild").get,ks=at(t,"nextSibling").get,Ko(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Ko(n)&&(n.__t=void 0),y&&(e.__svelte_meta=null,Ic())}}function ut(e=""){return document.createTextNode(e)}function ln(e){return Ss.call(e)}function Vn(e){return ks.call(e)}function S(e,t){return ln(e)}function j(e,t=!1){{var n=ln(e);return n instanceof Comment&&n.data===""?Vn(n):n}}function N(e,t=1,n=!1){let r=e;for(;t--;)r=Vn(r);return r}function Bc(e){e.textContent=""}function As(){return!1}function Es(e,t,n){return document.createElementNS(t??ts,e,void 0)}function Gc(e,t){if(t){const n=document.body;e.autofocus=!0,Ue(()=>{document.activeElement===n&&e.focus()})}}function ba(e){var t=x,n=D;Ne(null),Be(null);try{return e()}finally{Ne(t),Be(n)}}function Vc(e){D===null&&(x===null&&Lu(e),Ou()),Mt&&Du(e)}function Hc(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function Xe(e,t,n){var r=D;if(y)for(;r!==null&&(r.f&wr)!==0;)r=r.parent;r!==null&&(r.f&be)!==0&&(e|=be);var a={ctx:U,deps:null,nodes:null,f:e|le|Ae,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null};if(y&&(a.component_function=$n),n)try{un(a)}catch(i){throw ce(a),i}else t!==null&&Ie(a);var o=a;if(n&&o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&en)===0&&(o=o.first,(e&ot)!==0&&(e&vt)!==0&&o!==null&&(o.f|=vt)),o!==null&&(o.parent=r,r!==null&&Hc(o,r),x!==null&&(x.f&ie)!==0&&(e&Ft)===0)){var s=x;(s.effects??(s.effects=[])).push(o)}return a}function wa(){return x!==null&&!$e}function qa(e){const t=Xe(br,null,!1);return Z(t,ae),t.teardown=e,t}function Wc(e){Vc("$effect"),y&&Nt(e,"name",{value:"$effect"});var t=D.f,n=!x&&(t&De)!==0&&(t&Ct)===0;if(n){var r=U;(r.e??(r.e=[])).push(e)}else return Ps(e)}function Ps(e){return Xe(On|Fu,e,!1)}function jc(e){wt.ensure();const t=Xe(Ft|en,e,!0);return(n={})=>new Promise(r=>{n.outro?Dt(t,()=>{ce(t),r(void 0)}):(ce(t),r(void 0))})}function Ma(e){return Xe(On,e,!1)}function Uc(e){return Xe(qr|en,e,!0)}function Ns(e,t=0){return Xe(br|t,e,!0)}function ct(e,t=[],n=[],r=[]){_s(r,t,n,a=>{Xe(br,()=>e(...a.map(k)),!0)})}function Hn(e,t=0){var n=Xe(ot|t,e,!0);return y&&(n.dev_stack=nn),n}function Fs(e,t=0){var n=Xe(sa|t,e,!0);return y&&(n.dev_stack=nn),n}function me(e){return Xe(De|en,e,!0)}function Cs(e){var t=e.teardown;if(t!==null){const n=Mt,r=x;Os(!0),Ne(null);try{t.call(null)}finally{Os(n),Ne(r)}}}function Sa(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const a=n.ac;a!==null&&ba(()=>{a.abort(Tt)});var r=n.next;(n.f&Ft)!==0?n.parent=null:ce(n,t),n=r}}function Kc(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&De)===0&&ce(t),t=n}}function ce(e,t=!0){var n=!1;(t||(e.f&Yo)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(Xc(e.nodes.start,e.nodes.end),n=!0),Sa(e,t&&!n),jn(e,0),Z(e,st);var r=e.nodes&&e.nodes.t;if(r!==null)for(const o of r)o.stop();Cs(e);var a=e.parent;a!==null&&a.first!==null&&Ts(e),y&&(e.component_function=null),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function Xc(e,t){for(;e!==null;){var n=e===t?null:Vn(e);e.remove(),e=n}}function Ts(e){var t=e.parent,n=e.prev,r=e.next;n!==null&&(n.next=r),r!==null&&(r.prev=n),t!==null&&(t.first===e&&(t.first=r),t.last===e&&(t.last=n))}function Dt(e,t,n=!0){var r=[];xs(e,r,!0);var a=()=>{n&&ce(e),t&&t()},o=r.length;if(o>0){var s=()=>--o||a();for(var i of r)i.out(s)}else a()}function xs(e,t,n){if((e.f&be)===0){e.f^=be;var r=e.nodes&&e.nodes.t;if(r!==null)for(const i of r)(i.is_global||n)&&t.push(i);for(var a=e.first;a!==null;){var o=a.next,s=(a.f&vt)!==0||(a.f&De)!==0&&(e.f&ot)!==0;xs(a,t,s?n:!1),a=o}}}function ka(e){Rs(e,!0)}function Rs(e,t){if((e.f&be)!==0){e.f^=be,(e.f&ae)===0&&(Z(e,le),Ie(e));for(var n=e.first;n!==null;){var r=n.next,a=(n.f&vt)!==0||(n.f&De)!==0;Rs(n,a?t:!1),n=r}var o=e.nodes&&e.nodes.t;if(o!==null)for(const s of o)(s.is_global||t)&&s.in()}}function Ds(e,t){if(e.nodes)for(var n=e.nodes.start,r=e.nodes.end;n!==null;){var a=n===r?null:Vn(n);t.append(n),n=a}}let Er=!1,Mt=!1;function Os(e){Mt=e}let x=null,$e=!1;function Ne(e){x=e}let D=null;function Be(e){D=e}let Fe=null;function Ls(e){x!==null&&(Fe===null?Fe=[e]:Fe.push(e))}let ve=null,we=0,Ce=null;function Yc(e){Ce=e}let Is=1,Ot=0,Lt=Ot;function $s(e){Lt=e}function Bs(){return++Is}function Wn(e){var t=e.f;if((t&le)!==0)return!0;if(t&ie&&(e.f&=~gt),(t&Oe)!==0){for(var n=e.deps,r=n.length,a=0;a<r;a++){var o=n[a];if(Wn(o)&&gs(o),o.wv>e.wv)return!0}(t&Ae)!==0&&ue===null&&Z(e,ae)}return!1}function Gs(e,t,n=!0){var r=e.reactions;if(r!==null&&!(Fe!==null&&Pt.call(Fe,e)))for(var a=0;a<r.length;a++){var o=r[a];(o.f&ie)!==0?Gs(o,t,!1):t===o&&(n?Z(o,le):(o.f&ae)!==0&&Z(o,Oe),Ie(o))}}function Aa(e){var w;var t=ve,n=we,r=Ce,a=x,o=Fe,s=U,i=$e,l=Lt,c=e.f;ve=null,we=0,Ce=null,x=(c&(De|Ft))===0?e:null,Fe=null,tn(e.ctx),$e=!1,Lt=++Ot,e.ac!==null&&(ba(()=>{e.ac.abort(Tt)}),e.ac=null);try{e.f|=la;var f=e.fn,u=f();e.f|=Ct;var d=e.deps,m=L==null?void 0:L.is_fork;if(ve!==null){var p;if(m||jn(e,we),d!==null&&we>0)for(d.length=we+ve.length,p=0;p<ve.length;p++)d[we+p]=ve[p];else e.deps=d=ve;if(wa()&&(e.f&Ae)!==0)for(p=we;p<d.length;p++)((w=d[p]).reactions??(w.reactions=[])).push(e)}else!m&&d!==null&&we<d.length&&(jn(e,we),d.length=we);if(ss()&&Ce!==null&&!$e&&d!==null&&(e.f&(ie|Oe|le))===0)for(p=0;p<Ce.length;p++)Gs(Ce[p],e);if(a!==null&&a!==e){if(Ot++,a.deps!==null)for(let _=0;_<n;_+=1)a.deps[_].rv=Ot;if(t!==null)for(const _ of t)_.rv=Ot;Ce!==null&&(r===null?r=Ce:r.push(...Ce))}return(e.f&yt)!==0&&(e.f^=yt),u}catch(_){return is(_)}finally{e.f^=la,ve=t,we=n,Ce=r,x=a,Fe=o,tn(s),$e=i,Lt=l}}function Qc(e,t){let n=t.reactions;if(n!==null){var r=Su.call(n,e);if(r!==-1){var a=n.length-1;a===0?n=t.reactions=null:(n[r]=n[a],n.pop())}}if(n===null&&(t.f&ie)!==0&&(ve===null||!Pt.call(ve,t))){var o=t;(o.f&Ae)!==0&&(o.f^=Ae,o.f&=~gt),da(o),Cc(o),jn(o,0)}}function jn(e,t){var n=e.deps;if(n!==null)for(var r=t;r<n.length;r++)Qc(e,n[r])}function un(e){var t=e.f;if((t&st)===0){Z(e,ae);var n=D,r=Er;if(D=e,Er=!0,y){var a=$n;os(e.component_function);var o=nn;Mr(e.dev_stack??nn)}try{(t&(ot|sa))!==0?Kc(e):Sa(e),Cs(e);var s=Aa(e);e.teardown=typeof s=="function"?s:null,e.wv=Is;var i;y&&fc&&(e.f&le)!==0&&e.deps}finally{Er=r,D=n,y&&(os(a),Mr(o))}}}function k(e){var t=e.f,n=(t&ie)!==0;if(x!==null&&!$e){var r=D!==null&&(D.f&st)!==0;if(!r&&(Fe===null||!Pt.call(Fe,e))){var a=x.deps;if((x.f&la)!==0)e.rv<Ot&&(e.rv=Ot,ve===null&&a!==null&&a[we]===e?we++:ve===null?ve=[e]:ve.push(e));else{(x.deps??(x.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[x]:Pt.call(o,x)||o.push(x)}}}if(y&&Pc.delete(e),Mt&&qt.has(e))return qt.get(e);if(n){var s=e;if(Mt){var i=s.v;return((s.f&ae)===0&&s.reactions!==null||Hs(s))&&(i=va(s)),qt.set(s,i),i}var l=(s.f&Ae)===0&&!$e&&x!==null&&(Er||(x.f&Ae)!==0),c=(s.f&Ct)===0;Wn(s)&&(l&&(s.f|=Ae),gs(s)),l&&!c&&(ys(s),Vs(s))}if(ue!=null&&ue.has(e))return ue.get(e);if((e.f&yt)!==0)throw e.v;return e.v}function Vs(e){if(e.f|=Ae,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&ie)!==0&&(t.f&Ae)===0&&(ys(t),Vs(t))}function Hs(e){if(e.v===oe)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(qt.has(t)||(t.f&ie)!==0&&Hs(t))return!0;return!1}function Pr(e){var t=$e;try{return $e=!0,e()}finally{$e=t}}function Zc(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const Jc=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function zc(e){return Jc.includes(e)}const ef={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function tf(e){return e=e.toLowerCase(),ef[e]??e}const nf=["touchstart","touchmove"];function rf(e){return nf.includes(e)}const It=Symbol("events"),Ws=new Set,Ea=new Set;function af(e,t,n,r={}){function a(o){if(r.capture||Na.call(t,o),!o.cancelBubble)return ba(()=>n==null?void 0:n.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Ue(()=>{t.addEventListener(e,a,r)}):t.addEventListener(e,a,r),a}function fe(e,t,n){(t[It]??(t[It]={}))[e]=n}function Pa(e){for(var t=0;t<e.length;t++)Ws.add(e[t]);for(var n of Ea)n(e)}let js=null;function Na(e){var _,v;var t=this,n=t.ownerDocument,r=e.type,a=((_=e.composedPath)==null?void 0:_.call(e))||[],o=a[0]||e.target;js=e;var s=0,i=js===e&&e[It];if(i){var l=a.indexOf(i);if(l!==-1&&(t===document||t===window)){e[It]=t;return}var c=a.indexOf(t);if(c===-1)return;l<=c&&(s=l)}if(o=a[s]||e.target,o!==t){Nt(e,"currentTarget",{configurable:!0,get(){return o||n}});var f=x,u=D;Ne(null),Be(null);try{for(var d,m=[];o!==null;){var p=o.assignedSlot||o.parentNode||o.host||null;try{var w=(v=o[It])==null?void 0:v[r];w!=null&&(!o.disabled||e.target===o)&&w.call(o,e)}catch(A){d?m.push(A):d=A}if(e.cancelBubble||p===t||p===null)break;o=p}if(d){for(let A of m)queueMicrotask(()=>{throw A});throw d}}finally{e[It]=t,delete e.currentTarget,Ne(f),Be(u)}}}const Fa=((bi=globalThis==null?void 0:globalThis.window)==null?void 0:bi.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function of(e){return(Fa==null?void 0:Fa.createHTML(e))??e}function Us(e){var t=Es("template");return t.innerHTML=of(e.replaceAll("<!>","<!---->")),t.content}function Un(e,t){var n=D;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function Ye(e,t){var n=(t&tc)!==0,r=(t&nc)!==0,a,o=!e.startsWith("<!>");return()=>{a===void 0&&(a=Us(o?e:"<!>"+e),n||(a=ln(a)));var s=r||ya?document.importNode(a,!0):a.cloneNode(!0);if(n){var i=ln(s),l=s.lastChild;Un(i,l)}else Un(s,s);return s}}function sf(e,t,n="svg"){var r=!e.startsWith("<!>"),a=`<${n}>${r?e:"<!>"+e}</${n}>`,o;return()=>{if(!o){var s=Us(a),i=ln(s);o=ln(i)}var l=o.cloneNode(!0);return Un(l,l),l}}function lf(e,t){return sf(e,t,"svg")}function K(){var e=document.createDocumentFragment(),t=document.createComment(""),n=ut();return e.append(t,n),Un(t,n),e}function O(e,t){e!==null&&e.before(t)}function cn(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function uf(e,t){return cf(e,t)}const Nr=new Map;function cf(e,{target:t,anchor:n,props:r={},events:a,context:o,intro:s=!0,transformError:i}){$c();var l=void 0,c=jc(()=>{var f=n??t.appendChild(ut());Sc(f,{pending:()=>{}},m=>{$({});var p=U;o&&(p.c=o),a&&(r.$$events=a),l=e(m,r)||{},B()},i);var u=new Set,d=m=>{for(var p=0;p<m.length;p++){var w=m[p];if(!u.has(w)){u.add(w);var _=rf(w);for(const b of[t,document]){var v=Nr.get(b);v===void 0&&(v=new Map,Nr.set(b,v));var A=v.get(w);A===void 0?(b.addEventListener(w,Na,{passive:_}),v.set(w,1)):v.set(w,A+1)}}}};return d(yr(Ws)),Ea.add(d),()=>{var _;for(var m of u)for(const v of[t,document]){var p=Nr.get(v),w=p.get(m);--w==0?(v.removeEventListener(m,Na),p.delete(m),p.size===0&&Nr.delete(v)):p.set(m,w)}Ea.delete(d),f!==n&&((_=f.parentNode)==null||_.removeChild(f))}});return Ca.set(l,c),l}let Ca=new WeakMap;function Ks(e,t){const n=Ca.get(e);return n?(Ca.delete(e),n(t)):(y&&(lt in e?lc():sc()),Promise.resolve())}class Ta{constructor(t,n=!0){tt(this,"anchor");R(this,Ve,new Map);R(this,ze,new Map);R(this,Se,new Map);R(this,Ht,new Set);R(this,er,!0);R(this,tr,()=>{var t=L;if(h(this,Ve).has(t)){var n=h(this,Ve).get(t),r=h(this,ze).get(n);if(r)ka(r),h(this,Ht).delete(n);else{var a=h(this,Se).get(n);a&&(h(this,ze).set(n,a.effect),h(this,Se).delete(n),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),r=a.effect)}for(const[o,s]of h(this,Ve)){if(h(this,Ve).delete(o),o===t)break;const i=h(this,Se).get(s);i&&(ce(i.effect),h(this,Se).delete(s))}for(const[o,s]of h(this,ze)){if(o===n||h(this,Ht).has(o))continue;const i=()=>{if(Array.from(h(this,Ve).values()).includes(o)){var c=document.createDocumentFragment();Ds(s,c),c.append(ut()),h(this,Se).set(o,{effect:s,fragment:c})}else ce(s);h(this,Ht).delete(o),h(this,ze).delete(o)};h(this,er)||!r?(h(this,Ht).add(o),Dt(s,i,!1)):i()}}});R(this,xr,t=>{h(this,Ve).delete(t);const n=Array.from(h(this,Ve).values());for(const[r,a]of h(this,Se))n.includes(r)||(ce(a.effect),h(this,Se).delete(r))});this.anchor=t,T(this,er,n)}ensure(t,n){var r=L,a=As();if(n&&!h(this,ze).has(t)&&!h(this,Se).has(t))if(a){var o=document.createDocumentFragment(),s=ut();o.append(s),h(this,Se).set(t,{effect:me(()=>n(s)),fragment:o})}else h(this,ze).set(t,me(()=>n(this.anchor)));if(h(this,Ve).set(r,t),a){for(const[i,l]of h(this,ze))i===t?r.unskip_effect(l):r.skip_effect(l);for(const[i,l]of h(this,Se))i===t?r.unskip_effect(l.effect):r.skip_effect(l.effect);r.oncommit(h(this,tr)),r.ondiscard(h(this,xr))}else h(this,tr).call(this)}}Ve=new WeakMap,ze=new WeakMap,Se=new WeakMap,Ht=new WeakMap,er=new WeakMap,tr=new WeakMap,xr=new WeakMap;function fn(e,t,n=!1){var r=new Ta(e),a=n?vt:0;function o(s,i){r.ensure(s,i)}Hn(()=>{var s=!1;t((i,l=0)=>{s=!0,o(l,i)}),s||o(!1,null)},a)}function Xs(e,t){return t}function ff(e,t,n){for(var r=[],a=t.length,o,s=t.length,i=0;i<a;i++){let u=t[i];Dt(u,()=>{if(o){if(o.pending.delete(u),o.done.add(u),o.pending.size===0){var d=e.outrogroups;xa(yr(o.done)),d.delete(o),d.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var l=r.length===0&&n!==null;if(l){var c=n,f=c.parentNode;Bc(f),f.append(c),e.items.clear()}xa(t,!l)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function xa(e,t=!0){for(var n=0;n<e.length;n++)ce(e[n],t)}var Ys;function Fr(e,t,n,r,a,o=null){var s=e,i=new Map,l=(t&es)!==0;if(l){var c=e;s=c.appendChild(ut())}var f=null,u=ms(()=>{var v=n();return oa(v)?v:v==null?[]:yr(v)}),d,m=!0;function p(){_.fallback=f,df(_,d,s,t,r),f!==null&&(d.length===0?(f.f&it)===0?ka(f):(f.f^=it,Xn(f,null,s)):Dt(f,()=>{f=null}))}var w=Hn(()=>{d=k(u);for(var v=d.length,A=new Set,b=L,E=As(),F=0;F<v;F+=1){var P=d[F],C=r(P,F);if(y){var _e=r(P,F);C!==_e&&Ru(String(F),String(C),String(_e))}var ee=m?null:i.get(C);ee?(ee.v&&on(ee.v,P),ee.i&&on(ee.i,F),E&&b.unskip_effect(ee.e)):(ee=hf(i,m?s:Ys??(Ys=ut()),P,C,F,a,t,n),m||(ee.e.f|=it),i.set(C,ee)),A.add(C)}if(v===0&&o&&!f&&(m?f=me(()=>o(s)):(f=me(()=>o(Ys??(Ys=ut()))),f.f|=it)),v>A.size&&(y?pf(d,r):zo("","","")),!m)if(E){for(const[et,g]of i)A.has(et)||b.skip_effect(g.e);b.oncommit(p),b.ondiscard(()=>{})}else p();k(u)}),_={effect:w,items:i,outrogroups:null,fallback:f};m=!1}function Kn(e){for(;e!==null&&(e.f&De)===0;)e=e.next;return e}function df(e,t,n,r,a){var et,g,Wt,ht,wn,He,We,xe,jt;var o=(r&Yu)!==0,s=t.length,i=e.items,l=Kn(e.effect.first),c,f=null,u,d=[],m=[],p,w,_,v;if(o)for(v=0;v<s;v+=1)p=t[v],w=a(p,v),_=i.get(w).e,(_.f&it)===0&&((g=(et=_.nodes)==null?void 0:et.a)==null||g.measure(),(u??(u=new Set)).add(_));for(v=0;v<s;v+=1){if(p=t[v],w=a(p,v),_=i.get(w).e,e.outrogroups!==null)for(const ke of e.outrogroups)ke.pending.delete(_),ke.done.delete(_);if((_.f&it)!==0)if(_.f^=it,_===l)Xn(_,null,n);else{var A=f?f.next:l;_===e.effect.last&&(e.effect.last=_.prev),_.prev&&(_.prev.next=_.next),_.next&&(_.next.prev=_.prev),St(e,f,_),St(e,_,A),Xn(_,A,n),f=_,d=[],m=[],l=Kn(f.next);continue}if((_.f&be)!==0&&(ka(_),o&&((ht=(Wt=_.nodes)==null?void 0:Wt.a)==null||ht.unfix(),(u??(u=new Set)).delete(_))),_!==l){if(c!==void 0&&c.has(_)){if(d.length<m.length){var b=m[0],E;f=b.prev;var F=d[0],P=d[d.length-1];for(E=0;E<d.length;E+=1)Xn(d[E],b,n);for(E=0;E<m.length;E+=1)c.delete(m[E]);St(e,F.prev,P.next),St(e,f,F),St(e,P,b),l=b,f=P,v-=1,d=[],m=[]}else c.delete(_),Xn(_,l,n),St(e,_.prev,_.next),St(e,_,f===null?e.effect.first:f.next),St(e,f,_),f=_;continue}for(d=[],m=[];l!==null&&l!==_;)(c??(c=new Set)).add(l),m.push(l),l=Kn(l.next);if(l===null)continue}(_.f&it)===0&&d.push(_),f=_,l=Kn(_.next)}if(e.outrogroups!==null){for(const ke of e.outrogroups)ke.pending.size===0&&(xa(yr(ke.done)),(wn=e.outrogroups)==null||wn.delete(ke));e.outrogroups.size===0&&(e.outrogroups=null)}if(l!==null||c!==void 0){var C=[];if(c!==void 0)for(_ of c)(_.f&be)===0&&C.push(_);for(;l!==null;)(l.f&be)===0&&l!==e.fallback&&C.push(l),l=Kn(l.next);var _e=C.length;if(_e>0){var ee=(r&es)!==0&&s===0?n:null;if(o){for(v=0;v<_e;v+=1)(We=(He=C[v].nodes)==null?void 0:He.a)==null||We.measure();for(v=0;v<_e;v+=1)(jt=(xe=C[v].nodes)==null?void 0:xe.a)==null||jt.fix()}ff(e,C,ee)}}o&&Ue(()=>{var ke,qn;if(u!==void 0)for(_ of u)(qn=(ke=_.nodes)==null?void 0:ke.a)==null||qn.apply()})}function hf(e,t,n,r,a,o,s,i){var l=(s&Ku)!==0?(s&Qu)===0?xc(n,!1,!1):xt(n):null,c=(s&Xu)!==0?xt(a):null;return y&&l&&(l.trace=()=>{i()[(c==null?void 0:c.v)??a]}),{v:l,i:c,e:me(()=>(o(t,l??n,c??a,i),()=>{e.delete(r)}))}}function Xn(e,t,n){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end,o=t&&(t.f&it)===0?t.nodes.start:n;r!==null;){var s=Vn(r);if(o.before(r),r===a)return;r=s}}function St(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function pf(e,t){const n=new Map,r=e.length;for(let a=0;a<r;a++){const o=t(e[a],a);if(n.has(o)){const s=String(n.get(o)),i=String(a);let l=String(o);l.startsWith("[object ")&&(l=null),zo(s,i,l)}n.set(o,a)}}function X(e,t,...n){var r=new Ta(e);Hn(()=>{const a=t()??null;y&&a==null&&$u(),r.ensure(a,a&&(o=>a(o,...n)))},vt)}function _f(e,t,n,r,a,o){var s=null,i=e,l=new Ta(i,!1);Hn(()=>{const c=t()||null;var f=ac;if(c===null){l.ensure(null,null);return}return l.ensure(c,u=>{if(c){if(s=Es(c,f),Un(s,s),r){var d=s.appendChild(ut());r(s,d)}D.nodes.end=s,u.before(s)}}),()=>{}},vt),qa(()=>{})}function mf(e,t){var n=void 0,r;Fs(()=>{n!==(n=t())&&(r&&(ce(r),r=null),n&&(r=me(()=>{Ma(()=>n(e))})))})}function Qs(e){var t,n,r="";if(typeof e=="string"||typeof e=="number")r+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(n=Qs(e[t]))&&(r&&(r+=" "),r+=n)}else for(n in e)e[n]&&(r&&(r+=" "),r+=n);return r}function vf(){for(var e,t,n=0,r="",a=arguments.length;n<a;n++)(e=arguments[n])&&(t=Qs(e))&&(r&&(r+=" "),r+=t);return r}function Zs(e){return typeof e=="object"?vf(e):e??""}const Js=[...` 	
\r\f \v\uFEFF`];function gf(e,t,n){var r=e==null?"":""+e;if(t&&(r=r?r+" "+t:t),n){for(var a of Object.keys(n))if(n[a])r=r?r+" "+a:a;else if(r.length)for(var o=a.length,s=0;(s=r.indexOf(a,s))>=0;){var i=s+o;(s===0||Js.includes(r[s-1]))&&(i===r.length||Js.includes(r[i]))?r=(s===0?"":r.substring(0,s))+r.substring(i+1):s=i}}return r===""?null:r}function zs(e,t=!1){var n=t?" !important;":";",r="";for(var a of Object.keys(e)){var o=e[a];o!=null&&o!==""&&(r+=" "+a+": "+o+n)}return r}function Ra(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function yf(e,t){if(t){var n="",r,a;if(Array.isArray(t)?(r=t[0],a=t[1]):r=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,s=0,i=!1,l=[];r&&l.push(...Object.keys(r).map(Ra)),a&&l.push(...Object.keys(a).map(Ra));var c=0,f=-1;const w=e.length;for(var u=0;u<w;u++){var d=e[u];if(i?d==="/"&&e[u-1]==="*"&&(i=!1):o?o===d&&(o=!1):d==="/"&&e[u+1]==="*"?i=!0:d==='"'||d==="'"?o=d:d==="("?s++:d===")"&&s--,!i&&o===!1&&s===0){if(d===":"&&f===-1)f=u;else if(d===";"||u===w-1){if(f!==-1){var m=Ra(e.substring(c,f).trim());if(!l.includes(m)){d!==";"&&u++;var p=e.substring(c,u).trim();n+=" "+p+";"}}c=u+1,f=-1}}}}return r&&(n+=zs(r)),a&&(n+=zs(a,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function Da(e,t,n,r,a,o){var s=e.__className;if(s!==n||s===void 0){var i=gf(n,r,o);i==null?e.removeAttribute("class"):t?e.className=i:e.setAttribute("class",i),e.__className=n}else if(o&&a!==o)for(var l in o){var c=!!o[l];(a==null||c!==!!a[l])&&e.classList.toggle(l,c)}return o}function Oa(e,t={},n,r){for(var a in n){var o=n[a];t[a]!==o&&(n[a]==null?e.style.removeProperty(a):e.style.setProperty(a,o,r))}}function bf(e,t,n,r){var a=e.__style;if(a!==t){var o=yf(t,r);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else r&&(Array.isArray(r)?(Oa(e,n==null?void 0:n[0],r[0]),Oa(e,n==null?void 0:n[1],r[1],"important")):Oa(e,n,r));return r}function La(e,t,n=!1){if(e.multiple){if(t==null)return;if(!oa(t))return ic();for(var r of e.options)r.selected=t.includes(ei(r));return}for(r of e.options){var a=ei(r);if(Dc(a,t)){r.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function wf(e){var t=new MutationObserver(()=>{La(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),qa(()=>{t.disconnect()})}function ei(e){return"__value"in e?e.__value:e.value}const Yn=Symbol("class"),Qn=Symbol("style"),ti=Symbol("is custom element"),ni=Symbol("is html"),qf=ua?"option":"OPTION",Mf=ua?"select":"SELECT",Sf=ua?"progress":"PROGRESS";function kf(e,t){var n=Ia(e);n.value===(n.value=t??void 0)||e.value===t&&(t!==0||e.nodeName!==Sf)||(e.value=t??"")}function Af(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function q(e,t,n,r){var a=Ia(e);a[t]!==(a[t]=n)&&(t==="loading"&&(e[Cu]=n),n==null?e.removeAttribute(t):typeof n!="string"&&oi(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function Ef(e,t,n,r,a=!1,o=!1){var s=Ia(e),i=s[ti],l=!s[ni],c=t||{},f=e.nodeName===qf;for(var u in t)u in n||(n[u]=null);n.class?n.class=Zs(n.class):n[Yn]&&(n.class=null),n[Qn]&&(n.style??(n.style=null));var d=oi(e);for(const b in n){let E=n[b];if(f&&b==="value"&&E==null){e.value=e.__value="",c[b]=E;continue}if(b==="class"){var m=e.namespaceURI==="http://www.w3.org/1999/xhtml";Da(e,m,E,r,t==null?void 0:t[Yn],n[Yn]),c[b]=E,c[Yn]=n[Yn];continue}if(b==="style"){bf(e,E,t==null?void 0:t[Qn],n[Qn]),c[b]=E,c[Qn]=n[Qn];continue}var p=c[b];if(!(E===p&&!(E===void 0&&e.hasAttribute(b)))){c[b]=E;var w=b[0]+b[1];if(w!=="$$")if(w==="on"){const F={},P="$$"+b;let C=b.slice(2);var _=zc(C);if(Zc(C)&&(C=C.slice(0,-7),F.capture=!0),!_&&p){if(E!=null)continue;e.removeEventListener(C,c[P],F),c[P]=null}if(_)fe(C,e,E),Pa([C]);else if(E!=null){let _e=function(ee){c[b].call(this,ee)};c[P]=af(C,e,_e,F)}}else if(b==="style")q(e,b,E);else if(b==="autofocus")Gc(e,!!E);else if(!i&&(b==="__value"||b==="value"&&E!=null))e.value=e.__value=E;else if(b==="selected"&&f)Af(e,E);else{var v=b;l||(v=tf(v));var A=v==="defaultValue"||v==="defaultChecked";if(E==null&&!i&&!A)if(s[b]=null,v==="value"||v==="checked"){let F=e;const P=t===void 0;if(v==="value"){let C=F.defaultValue;F.removeAttribute(v),F.defaultValue=C,F.value=F.__value=P?C:null}else{let C=F.defaultChecked;F.removeAttribute(v),F.defaultChecked=C,F.checked=P?C:!1}}else e.removeAttribute(b);else A||d.includes(v)&&(i||typeof E!="string")?(e[v]=E,v in s&&(s[v]=oe)):typeof E!="function"&&q(e,v,E)}}}return c}function ri(e,t,n=[],r=[],a=[],o,s=!1,i=!1){_s(a,n,r,l=>{var c=void 0,f={},u=e.nodeName===Mf,d=!1;if(Fs(()=>{var p=t(...l.map(k)),w=Ef(e,c,p,o,s,i);d&&u&&"value"in p&&La(e,p.value);for(let v of Object.getOwnPropertySymbols(f))p[v]||ce(f[v]);for(let v of Object.getOwnPropertySymbols(p)){var _=p[v];v.description===oc&&(!c||_!==c[v])&&(f[v]&&ce(f[v]),f[v]=me(()=>mf(e,()=>_))),w[v]=_}c=w}),u){var m=e;Ma(()=>{La(m,c.value,!0),wf(m)})}d=!0})}function Ia(e){return e.__attributes??(e.__attributes={[ti]:e.nodeName.includes("-"),[ni]:e.namespaceURI===ts})}var ai=new Map;function oi(e){var t=e.getAttribute("is")||e.nodeName,n=ai.get(t);if(n)return n;ai.set(t,n=[]);for(var r,a=e,o=Element.prototype;o!==a;){r=ku(a);for(var s in r)r[s].set&&n.push(s);a=Uo(a)}return n}function si(e,t){return e===t||(e==null?void 0:e[lt])===t}function Pf(e={},t,n,r){return Ma(()=>{var a,o;return Ns(()=>{a=o,o=[],Pr(()=>{e!==n(...o)&&(t(e,...o),a&&si(n(...a),e)&&t(null,...a))})}),()=>{Ue(()=>{o&&si(n(...o),e)&&t(null,...o)})}}),e}let Cr=!1;function Nf(e){var t=Cr;try{return Cr=!1,[e(),Cr]}finally{Cr=t}}const Ff={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return y&&Gu(`${e.name}.${String(t)}`),!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function Y(e,t,n){return new Proxy(y?{props:e,exclude:t,name:n,other:{},to_proxy:[]}:{props:e,exclude:t},Ff)}const Cf={get(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(Dn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r)return r[t]}},set(e,t,n){let r=e.props.length;for(;r--;){let a=e.props[r];Dn(a)&&(a=a());const o=at(a,t);if(o&&o.set)return o.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(Dn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r){const a=at(r,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===lt||t===Qo)return!1;for(let n of e.props)if(Dn(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(Dn(n)&&(n=n()),!!n){for(const r in n)t.includes(r)||t.push(r);for(const r of Object.getOwnPropertySymbols(n))t.includes(r)||t.push(r)}return t}};function J(...e){return new Proxy({props:e},Cf)}function dn(e,t,n,r){var A;var a=(n&zu)!==0,o=(n&ec)!==0,s=r,i=!0,l=()=>(i&&(i=!1,s=o?Pr(r):r),s),c;if(a){var f=lt in e||Qo in e;c=((A=at(e,t))==null?void 0:A.set)??(f&&t in e?b=>e[t]=b:void 0)}var u,d=!1;a?[u,d]=Nf(()=>e[t]):u=e[t],u===void 0&&r!==void 0&&(u=l(),c&&(Bu(t),c(u)));var m;if(m=()=>{var b=e[t];return b===void 0?l():(i=!0,b)},(n&Ju)===0)return m;if(c){var p=e.$$legacy;return(function(b,E){return arguments.length>0?((!E||p||d)&&c(E?m():b),b):m()})}var w=!1,_=((n&Zu)!==0?kr:ms)(()=>(w=!1,m()));y&&(_.label=t),a&&k(_);var v=D;return(function(b,E){if(arguments.length>0){const F=E?k(_):a?sn(b):b;return Pe(_,F),w=!0,s!==void 0&&(s=F),b}return Mt&&w||(v.f&st)!==0?_.v:k(_)})}if(y){let e=function(t){if(!(t in globalThis)){let n;Object.defineProperty(globalThis,t,{configurable:!0,get:()=>{if(n!==void 0)return n;Vu(t)},set:r=>{n=r}})}};e("$state"),e("$effect"),e("$derived"),e("$inspect"),e("$props"),e("$bindable")}function ii(e){U===null&&Jo("onMount"),Wc(()=>{const t=Pr(e);if(typeof t=="function")return t})}const Tf="5";typeof window<"u"&&((wi=window.__svelte??(window.__svelte={})).v??(wi.v=new Set)).add(Tf);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const xf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Rf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Df=Symbol("lucide-context"),Of=()=>pc(Df);var Lf=lf("<svg><!><!></svg>");function z(e,t){$(t,!0);const n=Of()??{},r=dn(t,"color",19,()=>n.color??"currentColor"),a=dn(t,"size",19,()=>n.size??24),o=dn(t,"strokeWidth",19,()=>n.strokeWidth??2),s=dn(t,"absoluteStrokeWidth",19,()=>n.absoluteStrokeWidth??!1),i=dn(t,"iconNode",19,()=>[]),l=Y(t,["$$slots","$$events","$$legacy","name","color","size","strokeWidth","absoluteStrokeWidth","iconNode","children"]),c=Ar(()=>s()?Number(o())*24/Number(a()):o());var f=Lf();ri(f,m=>({...xf,...m,...l,width:a(),height:a(),stroke:r(),"stroke-width":k(c),class:["lucide-icon lucide",n.class,t.name&&`lucide-${t.name}`,t.class]}),[()=>!t.children&&!Rf(l)&&{"aria-hidden":"true"}]);var u=S(f);Fr(u,17,i,Xs,(m,p)=>{var w=Ar(()=>Nu(k(p),2));let _=()=>k(w)[0],v=()=>k(w)[1];var A=K(),b=j(A);_f(b,_,!0,(E,F)=>{ri(E,()=>({...v()}))}),O(m,A)});var d=N(u);X(d,()=>t.children??W),O(e,f),B()}function If(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];z(e,J({name:"chart-line"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function $f(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 9 6 6 6-6"}]];z(e,J({name:"chevron-down"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Bf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"}],["path",{d:"M12 17h.01"}]];z(e,J({name:"circle-question-mark"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Gf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 12 18z"}],["path",{d:"M2 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 2 18z"}]];z(e,J({name:"fast-forward"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Vf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"}]];z(e,J({name:"folder-open"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Hf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["rect",{x:"14",y:"3",width:"5",height:"18",rx:"1"}],["rect",{x:"5",y:"3",width:"5",height:"18",rx:"1"}]];z(e,J({name:"pause"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Wf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"}]];z(e,J({name:"play"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function jf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m15 14 5-5-5-5"}],["path",{d:"M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13"}]];z(e,J({name:"redo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Uf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];z(e,J({name:"refresh-cw"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Kf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m2 9 3-3 3 3"}],["path",{d:"M13 18H7a2 2 0 0 1-2-2V6"}],["path",{d:"m22 15-3 3-3-3"}],["path",{d:"M11 6h6a2 2 0 0 1 2 2v10"}]];z(e,J({name:"repeat-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Xf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 12 18z"}],["path",{d:"M22 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 22 18z"}]];z(e,J({name:"rewind"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Yf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M8.12 8.12 12 12"}],["path",{d:"M20 4 8.12 15.88"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M14.8 14.8 20 20"}]];z(e,J({name:"scissors"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Qf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];z(e,J({name:"settings"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Zf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];z(e,J({name:"sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function Jf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 2h4"}],["path",{d:"M12 14v-4"}],["path",{d:"M4 13a8 8 0 0 1 8-7 8 8 0 1 1-5.3 14L4 17.6"}],["path",{d:"M9 17H4v5"}]];z(e,J({name:"timer-reset"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function zf(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];z(e,J({name:"trash-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function ed(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9 14 4 9l5-5"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"}]];z(e,J({name:"undo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function td(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}]];z(e,J({name:"volume-1"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function nd(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}],["path",{d:"M19.364 18.364a9 9 0 0 0 0-12.728"}]];z(e,J({name:"volume-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function rd(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["line",{x1:"22",x2:"16",y1:"9",y2:"15"}],["line",{x1:"16",x2:"22",y1:"9",y2:"15"}]];z(e,J({name:"volume-x"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}function ad(e,t){$(t,!0);/**
 * @license @lucide/svelte v1.3.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */let n=Y(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}]];z(e,J({name:"waves"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=K(),i=j(s);X(i,()=>t.children??W),O(a,s)},$$slots:{default:!0}})),B()}var od=Ye('<span aria-hidden="true"><!></span>');function H(e,t){$(t,!0);const n=dn(t,"className",3,""),r=Ar(()=>["aqe-button-icon",n()].filter(Boolean).join(" "));var a=od(),o=S(a);{var s=g=>{If(g,{size:14,strokeWidth:2})},i=g=>{$f(g,{size:14,strokeWidth:2})},l=g=>{Bf(g,{size:14,strokeWidth:2})},c=g=>{Gf(g,{size:14,strokeWidth:2})},f=g=>{Vf(g,{size:14,strokeWidth:2})},u=g=>{Hf(g,{size:14,strokeWidth:2})},d=g=>{Wf(g,{size:14,strokeWidth:2})},m=g=>{jf(g,{size:14,strokeWidth:2})},p=g=>{Uf(g,{size:14,strokeWidth:2})},w=g=>{Kf(g,{size:14,strokeWidth:2})},_=g=>{Xf(g,{size:14,strokeWidth:2})},v=g=>{Yf(g,{size:14,strokeWidth:2})},A=g=>{Qf(g,{size:14,strokeWidth:2})},b=g=>{Zf(g,{size:14,strokeWidth:2})},E=g=>{Jf(g,{size:14,strokeWidth:2})},F=g=>{zf(g,{size:14,strokeWidth:2})},P=g=>{ed(g,{size:14,strokeWidth:2})},C=g=>{td(g,{size:14,strokeWidth:2})},_e=g=>{nd(g,{size:14,strokeWidth:2})},ee=g=>{rd(g,{size:14,strokeWidth:2})},et=g=>{ad(g,{size:14,strokeWidth:2})};fn(o,g=>{t.icon==="chart-line"?g(s):t.icon==="chevron-down"?g(i,1):t.icon==="circle-help"?g(l,2):t.icon==="fast-forward"?g(c,3):t.icon==="folder-open"?g(f,4):t.icon==="pause"?g(u,5):t.icon==="play"?g(d,6):t.icon==="redo-2"?g(m,7):t.icon==="refresh-cw"?g(p,8):t.icon==="repeat-2"?g(w,9):t.icon==="rewind"?g(_,10):t.icon==="scissors"?g(v,11):t.icon==="settings"?g(A,12):t.icon==="sparkles"?g(b,13):t.icon==="timer-reset"?g(E,14):t.icon==="trash-2"?g(F,15):t.icon==="undo-2"?g(P,16):t.icon==="volume-1"?g(C,17):t.icon==="volume-2"?g(_e,18):t.icon==="volume-x"?g(ee,19):t.icon==="waves"&&g(et,20)})}ct(()=>Da(a,1,Zs(k(r)))),O(e,a),B()}const sd=50,id=1e4,li={denoiseAlgorithm:"standard",pauseAggressiveness:"normal",speedStep:.05,trimStepMs:100,volumeStepDb:3};function ld(){return window.__aqeSplitButtonStates??(window.__aqeSplitButtonStates={}),window.__aqeSplitButtonStates}function ud(){var e;return{...li,...(e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.splitButtonDefaults}}function $a(e){return Number.isFinite(e)?Math.max(sd,Math.min(id,Math.round(e))):li.trimStepMs}function ui(e){const t=$a(e);if(t<1e3)return`${t} ms`;const n=t/1e3;return`${Number.isInteger(n)?n.toFixed(0):n.toFixed(1)} s`}function Ba(e){const t=$a(ud().trimStepMs),n=ld(),r=n[e];if(r)return!r.trimEdited&&r.defaultTrimStepMs!==t&&(r.defaultTrimStepMs=t,r.trimStepMs=t),r;const a={defaultTrimStepMs:t,trimEdited:!1,trimStepMs:t};return n[e]=a,a}function cd(e,t){const n=Ba(e);return n.trimEdited=!0,n.trimStepMs=$a(t),n}function fd(e,t){return{command:e,fieldOrd:t,overrides:{trimStepMs:Ba(t).trimStepMs}}}var dd=Ye('<button type="button" class="aqe-button aqe-split-preset"> </button>'),hd=Ye('<div class="aqe-split-popover"><div class="aqe-split-popover-header"><strong> </strong> <span> </span></div> <input type="range" min="50" max="10000" step="50"/> <div class="aqe-split-range-labels"><span>50 ms</span> <span>10 s</span></div> <div class="aqe-split-presets"></div></div>'),pd=Ye('<span class="aqe-split-button"><button type="button" class="aqe-button aqe-split-primary" data-aqe-button-state="default"><!> <span class="aqe-button-label"> </span></button> <button type="button" class="aqe-button aqe-icon-only aqe-split-menu-button"><!> <span class="aqe-button-label">Options</span></button> <!></span>');function _d(e,t){$(t,!0);const n=[100,200,500,1e3];let r,a=Ke(!1),o=Ke(100);function s(){return kn[t.button.command]}function i(){Pe(a,!1)}function l(P){P.preventDefault(),P.stopPropagation(),Pe(a,!k(a))}function c(P){Pe(o,cd(t.target.ord,P).trimStepMs,!0)}function f(){i(),Qr(t.button.command,t.target.node,t.target.ord,fd(t.button.command,t.target.ord))}function u(P){!k(a)||!r||P.target instanceof Node&&r.contains(P.target)||i()}function d(P){P.key==="Escape"&&i()}ii(()=>(Pe(o,Ba(t.target.ord).trimStepMs,!0),document.addEventListener("mousedown",u,!0),document.addEventListener("keydown",d,!0),()=>{document.removeEventListener("mousedown",u,!0),document.removeEventListener("keydown",d,!0)}));var m=pd(),p=S(m),w=S(p);H(w,{get icon(){return t.button.icon}});var _=N(w,2),v=S(_),A=N(p,2),b=S(A);H(b,{icon:"chevron-down"});var E=N(A,2);{var F=P=>{var C=hd(),_e=S(C),ee=S(_e),et=S(ee),g=N(ee,2),Wt=S(g),ht=N(_e,2),wn=N(ht,4);Fr(wn,21,()=>n,Xs,(He,We)=>{var xe=dd(),jt=S(xe);ct((ke,qn)=>{q(xe,"data-testid",ke),q(xe,"aria-pressed",k(o)===k(We)?"true":"false"),cn(jt,qn)},[()=>`aqe-split-${t.target.ord}-${s()}-preset-${k(We)}`,()=>ui(k(We))]),fe("click",xe,()=>c(k(We))),O(He,xe)}),ct((He,We,xe)=>{q(C,"data-testid",He),cn(et,t.button.label),cn(Wt,We),q(ht,"data-testid",xe),kf(ht,k(o))},[()=>`aqe-split-${t.target.ord}-${s()}-popover`,()=>ui(k(o)),()=>`aqe-split-${t.target.ord}-${s()}-slider`]),fe("input",ht,He=>c(Number(He.currentTarget.value))),O(P,C)};fn(E,P=>{k(a)&&P(F)})}Pf(m,P=>r=P,()=>r),ct((P,C)=>{q(p,"data-aqe-command",t.button.command),q(p,"data-testid",P),q(p,"title",t.button.title),q(p,"aria-label",t.button.title),cn(v,t.button.label),q(A,"data-testid",C),q(A,"title",`${t.button.title} amount`),q(A,"aria-label",`${t.button.title} amount`),q(A,"aria-expanded",k(a)?"true":"false")},[()=>`aqe-button-${t.target.ord}-${s()}`,()=>`aqe-split-${t.target.ord}-${s()}-menu`]),fe("mousedown",p,P=>P.preventDefault()),fe("click",p,f),fe("mousedown",A,P=>P.preventDefault()),fe("click",A,l),O(e,m),B()}Pa(["mousedown","click","input"]);function ci(){return document.body.dataset.aqeBusy==="true"}function fi(e,t,n){if(ci())return;const r=I(n);if(!r)return;const a=So(r,e);Cn(r),a&&(typeof t.focus=="function"&&t.focus(),mt(r,{clearAudio:!0}),Ki(a),window.__aqeActiveField=n,he.info("region delete request queued",{ord:n,sourceFilename:a.sourceFilename,selectionStartMs:a.selectionStartMs,selectionEndMs:a.selectionEndMs,durationMs:a.durationMs,trigger:e,playbackActive:a.playbackActive}),Zt(n,!0,eo("aqe:delete-selection")),Yt(n,"aqe:delete-selection"))}function md(e,t){if(e.key!=="Backspace")return;const n=I(t);if(!(!n||document.activeElement!==n||ci())){if(!So(n,"backspace")){Cn(n);return}e.preventDefault(),fi("backspace",n,t)}}var vd=Ye('<button type="button"><!> <!> <span class="aqe-button-label"> </span></button>'),gd=Ye('<button type="button" class="aqe-button aqe-icon-only aqe-repeat-button" title="Repeat selected region, or the whole graph when no region is selected." aria-label="Repeat playback"><!> <span class="aqe-button-label">Repeat</span></button>'),yd=Ye('<button type="button" class="aqe-button aqe-menu-item" data-aqe-button-state="default" role="menuitem"><!> <span class="aqe-button-label"> </span></button>'),bd=Ye('<details class="aqe-menu"><summary class="aqe-button aqe-menu-summary" title="Denoise audio" aria-label="Denoise audio"><!> <span class="aqe-button-label">Denoise</span> <!></summary> <div class="aqe-menu-items" role="menu"></div></details>'),wd=Ye("<!> <!> <!>",1),qd=Ye('<div class="aqe-controls"><!> <button type="button" class="aqe-button aqe-delete-region-button" data-aqe-command="aqe:delete-selection" data-aqe-button-state="default" title="Delete selected region" aria-label="Delete selected region" hidden=""><!> <span class="aqe-button-label">Delete Region</span></button> <span class="aqe-status"></span> <details class="aqe-help"><summary class="aqe-help-summary" title="Show editor help"><!> <span>Help</span></summary> <div class="aqe-help-body"><section class="aqe-help-section"><h4 class="aqe-help-title">Graph and regions</h4> <ul class="aqe-help-list"><li><kbd>Shift</kbd>-drag on the graph to select a region.</li> <li>Play uses the selected region when one is active; Repeat loops the selected region, or the full graph otherwise.</li> <li>Delete Region removes only the selected region. Backspace does the same when the graph is focused.</li> <li>In the graph, grey is loudness and lines are pitch of the voice.</li></ul></section> <section class="aqe-help-section"><h4 class="aqe-help-title">Buttons</h4> <div class="aqe-help-grid"><span class="aqe-help-item"><span class="aqe-help-command"><!><span>Play</span></span> <span>Start or pause audio.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Graph</span></span> <span>Show pitch and loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Folder</span></span> <span>Open the current audio file.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>-L</span></span> <span>Trim 100 ms from the left.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>-R</span></span> <span>Trim 100 ms from the right.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Shorten Pauses</span></span> <span>Speed up long internal pauses.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Denoise</span></span> <span>Use Standard or RNNoise cleanup.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Slower</span></span> <span>Decrease speed.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Faster</span></span> <span>Increase speed.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Volume -</span></span> <span>Decrease loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Volume +</span></span> <span>Increase loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Undo</span></span> <span>Restore the previous edit.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Redo</span></span> <span>Restore the undone edit.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Delete Region</span></span> <span>Remove the selected graph region.</span></span></div></section> <p class="aqe-help-note">Every edit creates a new media file and updates the field to point at it. The original file remains in your media collection.</p></div></details> <div class="aqe-visualizer" data-anchor-ms="0" data-cursor-ms="0" data-progress-ms="0" data-graph-active="false" data-graph-busy="false" data-has-track="false" data-playback-state="stopped" data-playback-engine="" data-playback-start-ms="0" data-playback-end-ms="0" data-playback-region-mode="full" data-resume-requires-restart="false" data-selection-active="false" data-selection-start-ms="" data-selection-end-ms="" data-selection-draft-active="false" data-selection-draft-start-ms="" data-selection-draft-end-ms="" role="button" aria-label="Audio graph" tabindex="0" hidden=""><audio class="aqe-audio-clock" preload="metadata" hidden=""></audio> <svg class="aqe-visualizer-svg" preserveAspectRatio="xMinYMin meet" role="img" aria-label="Audio pitch and intensity visualization"><rect class="aqe-selection" width="0" visibility="hidden"></rect><path class="aqe-intensity" d=""></path><g class="aqe-pitch"></g><g class="aqe-labels"></g><g class="aqe-x-axis"></g><line class="aqe-selection-edge aqe-selection-start" visibility="hidden"></line><line class="aqe-selection-edge aqe-selection-end" visibility="hidden"></line><line class="aqe-cursor"></line></svg> <div class="aqe-visualizer-meta"><span class="aqe-spinner" hidden="" aria-hidden="true"></span> <span class="aqe-cursor-label">0 ms</span> <span class="aqe-visualizer-status"></span></div></div></div>');function Md(e,t){var Ri;$(t,!0);const n=((Ri=window.__AQE_EDITOR_CONFIG__)==null?void 0:Ri.repeatPlaybackByDefault)===!0;function r(te){const Rr=te.currentTarget.ariaPressed!=="true";ru(t.target.ord,Rr)}function a(te){return te==="aqe:trim-left"||te==="aqe:trim-right"}ii(()=>{const te=I(t.target.ord);te&&(Zl(te),iu(te),tu(te))});var o=qd(),s=S(o);Fr(s,17,()=>G,te=>te.command,(te,de)=>{var Rr=wd(),Di=j(Rr);{var sh=ye=>{_d(ye,{get button(){return k(de)},get target(){return t.target}})},ih=Ar(()=>a(k(de).command)),lh=ye=>{var Q=vd();let Ut;var Kt=S(Q);H(Kt,{className:"aqe-button-icon-default",get icon(){return k(de).icon}});var Dr=N(Kt,2);{var Ua=pe=>{H(pe,{className:"aqe-button-icon-active",get icon(){return k(de).activeIcon}})};fn(Dr,pe=>{k(de).activeIcon&&pe(Ua)})}var sr=N(Dr,2),pt=S(sr);ct(pe=>{Ut=Da(Q,1,"aqe-button",null,Ut,{"aqe-icon-only":k(de).iconOnly===!0}),q(Q,"data-aqe-command",k(de).command),q(Q,"data-aqe-button-state",k(de).command==="aqe:play"?"play":k(de).command==="aqe:analyze"?"graph":"default"),q(Q,"data-testid",pe),q(Q,"title",k(de).title),q(Q,"aria-label",k(de).title),cn(pt,k(de).label)},[()=>Ir(t.target.ord,k(de).command)]),fe("mousedown",Q,pe=>pe.preventDefault()),fe("click",Q,()=>Qr(k(de).command,t.target.node,t.target.ord)),O(ye,Q)};fn(Di,ye=>{k(ih)?ye(sh):ye(lh,!1)})}var Oi=N(Di,2);{var uh=ye=>{var Q=gd(),Ut=S(Q);H(Ut,{icon:"repeat-2"}),ct(()=>{q(Q,"data-aqe-button-state",n?"active":"default"),q(Q,"data-testid",`aqe-repeat-${t.target.ord}`),q(Q,"aria-pressed",n?"true":"false")}),fe("mousedown",Q,Kt=>Kt.preventDefault()),fe("click",Q,r),O(ye,Q)};fn(Oi,ye=>{k(de).command==="aqe:play"&&ye(uh)})}var ch=N(Oi,2);{var fh=ye=>{var Q=bd(),Ut=S(Q),Kt=S(Ut);H(Kt,{icon:"sparkles"});var Dr=N(Kt,4);H(Dr,{className:"aqe-menu-chevron",icon:"chevron-down"});var Ua=N(Ut,2);Fr(Ua,21,()=>V,sr=>sr.command,(sr,pt)=>{var pe=yd(),Li=S(pe);H(Li,{get icon(){return k(pt).icon}});var dh=N(Li,2),hh=S(dh);ct(Ka=>{q(pe,"data-aqe-command",k(pt).command),q(pe,"data-testid",Ka),q(pe,"title",k(pt).title),q(pe,"aria-label",k(pt).title),cn(hh,k(pt).label)},[()=>Ir(t.target.ord,k(pt).command)]),fe("mousedown",pe,Ka=>Ka.preventDefault()),fe("click",pe,()=>Qr(k(pt).command,t.target.node,t.target.ord)),O(sr,pe)}),ct(()=>q(Q,"data-testid",`aqe-denoise-menu-${t.target.ord}`)),O(ye,Q)};fn(ch,ye=>{k(de).command==="aqe:remove-pauses"&&ye(fh)})}O(te,Rr)});var i=N(s,2),l=S(i);H(l,{icon:"trash-2"});var c=N(i,2),f=N(c,2),u=S(f),d=S(u);H(d,{icon:"circle-help"});var m=N(u,2),p=N(S(m),2),w=N(S(p),2),_=S(w),v=S(_),A=S(v);H(A,{icon:"play"});var b=N(_,2),E=S(b),F=S(E);H(F,{icon:"chart-line"});var P=N(b,2),C=S(P),_e=S(C);H(_e,{icon:"folder-open"});var ee=N(P,2),et=S(ee),g=S(et);H(g,{icon:"scissors"});var Wt=N(ee,2),ht=S(Wt),wn=S(ht);H(wn,{icon:"scissors"});var He=N(Wt,2),We=S(He),xe=S(We);H(xe,{icon:"timer-reset"});var jt=N(He,2),ke=S(jt),qn=S(ke);H(qn,{icon:"sparkles"});var qi=N(jt,2),Hd=S(qi),Wd=S(Hd);H(Wd,{icon:"rewind"});var Mi=N(qi,2),jd=S(Mi),Ud=S(jd);H(Ud,{icon:"fast-forward"});var Si=N(Mi,2),Kd=S(Si),Xd=S(Kd);H(Xd,{icon:"volume-1"});var ki=N(Si,2),Yd=S(ki),Qd=S(Yd);H(Qd,{icon:"volume-2"});var Ai=N(ki,2),Zd=S(Ai),Jd=S(Zd);H(Jd,{icon:"undo-2"});var Ei=N(Ai,2),zd=S(Ei),eh=S(zd);H(eh,{icon:"redo-2"});var th=N(Ei,2),nh=S(th),rh=S(nh);H(rh,{icon:"trash-2"});var nr=N(f,2),Pi=S(nr),rr=N(Pi,2),ar=S(rr),Ni=N(ar),Fi=N(Ni),Ci=N(Fi,2),Mn=N(Ci),Sn=N(Mn),or=N(Sn),ah=N(rr,2),Ti=S(ah),xi=N(Ti,2),oh=N(xi,2);ct(te=>{q(o,"data-aqe-field-ord",t.target.ord),q(o,"data-aqe-source-filename",t.target.sourceFilename),q(o,"data-testid",`aqe-controls-${t.target.ord}`),q(i,"data-testid",te),q(c,"data-testid",`aqe-status-${t.target.ord}`),q(f,"data-testid",`aqe-help-${t.target.ord}`),q(nr,"data-aqe-field-ord",t.target.ord),q(nr,"data-repeat-enabled",n?"true":"false"),q(nr,"data-testid",`aqe-graph-${t.target.ord}`),q(Pi,"data-testid",`aqe-audio-clock-${t.target.ord}`),q(rr,"data-testid",`aqe-graph-svg-${t.target.ord}`),q(rr,"viewBox",`0 0 ${M.width} ${M.height}`),q(ar,"data-testid",`aqe-selection-${t.target.ord}`),q(ar,"x",M.left),q(ar,"y",M.top),q(ar,"height",M.height-M.top-M.bottom),q(Ni,"data-testid",`aqe-intensity-${t.target.ord}`),q(Fi,"data-testid",`aqe-pitch-${t.target.ord}`),q(Ci,"data-testid",`aqe-x-axis-${t.target.ord}`),q(Mn,"data-testid",`aqe-selection-start-${t.target.ord}`),q(Mn,"x1",M.left),q(Mn,"x2",M.left),q(Mn,"y1",M.top),q(Mn,"y2",M.height-M.bottom),q(Sn,"data-testid",`aqe-selection-end-${t.target.ord}`),q(Sn,"x1",M.left),q(Sn,"x2",M.left),q(Sn,"y1",M.top),q(Sn,"y2",M.height-M.bottom),q(or,"data-testid",`aqe-cursor-${t.target.ord}`),q(or,"x1",M.left),q(or,"x2",M.left),q(or,"y1",M.top),q(or,"y2",M.height-M.bottom),q(Ti,"data-testid",`aqe-graph-spinner-${t.target.ord}`),q(xi,"data-testid",`aqe-progress-label-${t.target.ord}`),q(oh,"data-testid",`aqe-graph-status-${t.target.ord}`)},[()=>Ir(t.target.ord,"aqe:delete-selection")]),fe("mousedown",i,te=>te.preventDefault()),fe("click",i,()=>fi("button",t.target.node,t.target.ord)),fe("keydown",nr,te=>md(te,t.target.ord)),fe("pointerdown",rr,te=>fu(te,t.target.ord)),O(e,o),B()}Pa(["mousedown","click","keydown","pointerdown"]);const hn=new Map;function Sd(e){const t=hn.get(e.ord);if(t){if(document.body.contains(t.host)||di(e,t.host),Ga(e.ord,t.host),!e.sourceFilename||t.sourceFilename===e.sourceFilename)return t;const o=I(e.ord);if((o==null?void 0:o.dataset.graphBusy)==="true"||(o==null?void 0:o.dataset.hasTrack)==="true"){const s=o.dataset.sourceFilename||e.sourceFilename;t.sourceFilename=s;const i=document.querySelector(`.aqe-controls[data-aqe-field-ord="${e.ord}"]`);return i&&(i.dataset.aqeSourceFilename=s),Ga(e.ord,t.host),t}}kd(e.ord);const n=document.createElement("div");n.className="aqe-mount-host",di(e,n);const a={component:uf(Md,{target:n,props:{target:e}}),host:n,ord:e.ord,sourceFilename:e.sourceFilename};return hn.set(e.ord,a),Ga(e.ord,n),a}function kd(e){const t=hn.get(e);t&&(Ks(t.component),t.host.remove(),hn.delete(e)),document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>n.remove())}function Ad(){for(const e of hn.values())Ks(e.component),e.host.remove();hn.clear(),Ed()}function di(e,t){const n=e.node.closest(".field-container")||e.node.closest(".field")||e.node.parentElement||e.node;n.parentElement?n.after(t):e.node.after(t)}function Ga(e,t){document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>{t.contains(n)||n.remove()}),document.querySelectorAll(".aqe-mount-host").forEach(n=>{n!==t&&!n.querySelector(".aqe-controls")&&n.remove()})}function Ed(){document.querySelectorAll(".aqe-mount-host").forEach(e=>e.remove()),document.querySelectorAll(".aqe-controls").forEach(e=>e.remove())}function Pd(){window.__aqeGraphStateForTest=Td,window.__aqeInstallAudioPlaybackTestDriverForTest=Nd,window.__aqeSetCursorByClientXForTest=Cd,window.__aqeSetCursorForTest=Fd}function Nd(e){const t=I(e),n=Re(t);return!t||!n?!1:(n.__aqeTestDriverInstalled=!0,n.pause=function(){n.__aqeTestPlaying=!1,n.__aqeTestFrame&&(window.cancelAnimationFrame(n.__aqeTestFrame),n.__aqeTestFrame=null)},n.play=function(){n.__aqeTestPlaying=!0,n.__aqeTestLastNow=performance.now();const a=()=>{if(!n.__aqeTestPlaying)return;const o=performance.now(),s=Number(t.dataset.durationMs||"0")/1e3,i=Math.max(0,(o-Number(n.__aqeTestLastNow||o))/1e3);if(n.__aqeTestLastNow=o,n.currentTime=Math.min(s,(Number(n.currentTime)||0)+i),s&&n.currentTime>=s){n.__aqeTestPlaying=!1,n.dispatchEvent(new Event("ended"));return}n.__aqeTestFrame=window.requestAnimationFrame(a)};return n.__aqeTestFrame=window.requestAnimationFrame(a),Promise.resolve()},!0)}function Fd(e,t,n){const r=I(e);return r?(r.hidden=!1,r.dataset.graphActive="true",Et(r,t,!!n),!0):!1}function Cd(e,t,n){var i;const r=I(e),a=(r==null?void 0:r.querySelector(".aqe-visualizer-svg"))??null;if(!r||!a)return null;const o=Number(r.dataset.durationMs||"0"),s=Nn({clientX:t},a,o);return Et(r,s,!!n),{cursorMs:Number(r.dataset.cursorMs||"0"),cursorX:Number(((i=r.querySelector(".aqe-cursor"))==null?void 0:i.getAttribute("x1"))||"0"),bounds:go(a)}}function Td(e){var c,f,u,d,m;const t=I(e),n=no(e),r=ro(e),a=((c=nt(e))==null?void 0:c.querySelector(".aqe-delete-region-button"))??null;if(!t)return null;const o=ir().flatMap(p=>Array.from(p.querySelectorAll(".aqe-button-icon svg"))),s=Re(t),i=xo(t),l=Ro(t);return{active:t.dataset.graphActive==="true",busy:t.dataset.graphBusy==="true",hidden:!!t.hidden,hasTrack:t.dataset.hasTrack==="true",durationMs:Number(t.dataset.durationMs||"0"),anchorMs:Number(t.dataset.anchorMs||"0"),cursorMs:Number(t.dataset.cursorMs||"0"),progressMs:Number(t.dataset.progressMs||"0"),sourceFilename:t.dataset.sourceFilename||"",graphButtonLabel:hi(n),graphButtonState:(n==null?void 0:n.dataset.aqeButtonState)||"",playButtonLabel:hi(r),playButtonState:(r==null?void 0:r.dataset.aqeButtonState)||"",playbackState:xd(t),selectionActive:i!==null,selectionStartMs:(i==null?void 0:i.startMs)??null,selectionEndMs:(i==null?void 0:i.endMs)??null,selectionDraftActive:l!==null,selectionDraftStartMs:(l==null?void 0:l.startMs)??null,selectionDraftEndMs:(l==null?void 0:l.endMs)??null,repeatEnabled:t.dataset.repeatEnabled==="true",repeatControlDisabled:!!((f=ao(e))!=null&&f.disabled),regionDeleteButtonDisabled:!!(a!=null&&a.disabled),regionDeleteButtonHidden:a?!!a.hidden:!0,playbackStartMs:Number(t.dataset.playbackStartMs||"0"),playbackEndMs:Number(t.dataset.playbackEndMs||"0"),playbackRegionMode:t.dataset.playbackRegionMode==="selection"?"selection":"full",resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true",audioClockSrc:s&&s.getAttribute("src")||"",audioClockCurrentMs:s?Math.round((Number(s.currentTime)||0)*1e3):0,audioClockReady:!!(s&&t.__aqeAudioClockAvailable),audioClockFallback:!!t.__aqeAudioClockFallback,audioClockMuted:!!(s&&s.muted),audioPlaybackTestDriver:!!(s&&s.__aqeTestDriverInstalled),playbackEngine:Rn(t),progressClockMode:Rd(t),xAxisLabels:Array.from(t.querySelectorAll(".aqe-x-label")).map(p=>p.textContent||""),pitchPaths:t.querySelectorAll(".aqe-pitch-path").length,intensity:((u=t.querySelector(".aqe-intensity"))==null?void 0:u.getAttribute("d"))||"",cursorX:Number(((d=t.querySelector(".aqe-cursor"))==null?void 0:d.getAttribute("x1"))||"0"),spinnerVisible:t.querySelector(".aqe-spinner")?!((m=t.querySelector(".aqe-spinner"))!=null&&m.hidden):!1,allButtonsDisabled:ir().every(p=>p.disabled),anyButtonDisabled:ir().some(p=>p.disabled),buttonIconCount:o.length,buttonIconStrokeValues:o.map(p=>p.getAttribute("stroke")||getComputedStyle(p).stroke||"")}}function xd(e){const t=e.dataset.playbackState;return Hr(t)?t:"stopped"}function Rd(e){const t=e.dataset.progressClockMode;return t==="audio"||t==="manual"||t==="stopped"?t:"stopped"}function hi(e){var t;return((t=e==null?void 0:e.querySelector(".aqe-button-label"))==null?void 0:t.textContent)||(e==null?void 0:e.textContent)||""}function Dd(){window.__aqeSetBusy=Zt,window.__aqeSetStatus=To,window.__aqeSetVisualizer=hu,window.__aqeSetVisualizerStatus=pu,window.__aqeResetGraphAfterEdit=du,window.__aqeSetPlaybackState=yu,window.__aqeGetPlaybackRequest=bu,window.__aqeStopEditorPlayback=wu,window.__aqeGetCursorMs=qu,window.__aqeGetCursorIntent=Mu,window.__aqePrepareForNewNote=$o,window.__aqePopFrontendLog=Hi,window.__aqePopPendingGraphAnalysisRequest=Ui,window.__aqePopPendingRegionDeleteRequest=Xi,Pd()}const Od=/\[sound:([^\]]+)\]/i,Ld=/\.(aac|flac|m4a|mp3|oga|ogg|opus|wav|webm)$/i;let Zn=[];function Id(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){pi(),window.__AQE_EDITOR_CONFIG__=e,Dd(),$o(),il(),window.__aqeEditorDispose=pi,he.info("editor runtime initialized",{audioFieldIndices:e.audioFieldIndices,showGraphByDefault:e.showGraphByDefault===!0});const t=()=>$d(e);window.__aqeScan=t,Ha(t,0),Ha(t,250),Ha(t,1e3)}function pi(){Zn.forEach(e=>window.clearTimeout(e)),Zn=[],Ad()}function $d(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){if(e.audioFieldIndices.length){const r=Gd(e.audioFieldIndices,e.audioFieldSources);r.forEach(a=>_i(a)),he.debug("scan mounted explicit fields",{count:r.length}),ta(),mi(e,r);return}const t=[];let n=0;Bd().forEach((r,a)=>{const o=Va(r);if(!o)return;const s={node:r,ord:Vd(r,a),sourceFilename:o};_i(s),t.push(s),n+=1}),he.debug("scan mounted detected fields",{count:n}),ta(),mi(e,t)}function Bd(){const e=Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]')),t=new Set;return e.filter(n=>t.has(n)?!1:(t.add(n),!!(n.textContent||n.innerHTML)))}function Gd(e,t={}){return e.map(n=>{const r=document.querySelector(`.field-container[data-index="${n}"]`);if(!r)return null;const a=r.querySelector('[contenteditable="true"]')||r,o=Va(a)||Va(r)||t[n]||"";return{ord:n,node:a,sourceFilename:o}}).filter(n=>n!==null)}function Vd(e,t){const n=["data-field-ord","data-ord","data-index"];for(const a of n){const o=e.getAttribute(a);if(o!==null&&/^\d+$/.test(o))return Number(o)}const r=/(\d+)/.exec(String(e.id||""));return r?Number(r[1]):t}function Va(e){const t=e.innerHTML||e.textContent||"",n=Od.exec(t),r=n==null?void 0:n[1];return r&&Ld.test(r)?r:""}function _i(e){Sd(e)}function mi(e,t){e.showGraphByDefault&&ll(t.map(({ord:n,sourceFilename:r})=>({ord:n,sourceFilename:r})),{anyBusy:()=>document.body.dataset.aqeBusy==="true",requestDefaultGraph:Lo})}function Ha(e,t){const n=window.setTimeout(()=>{Zn=Zn.filter(r=>r!==n),e()},t);Zn.push(n)}Id()})();
