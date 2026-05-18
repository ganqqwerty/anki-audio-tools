var Qd=Object.defineProperty;var Fi=$=>{throw TypeError($)};var Zd=($,G,z)=>G in $?Qd($,G,{enumerable:!0,configurable:!0,writable:!0,value:z}):$[G]=z;var Ke=($,G,z)=>Zd($,typeof G!="symbol"?G+"":G,z),Ia=($,G,z)=>G.has($)||Fi("Cannot "+z);var d=($,G,z)=>(Ia($,G,"read from private field"),z?z.call($):G.get($)),R=($,G,z)=>G.has($)?Fi("Cannot add the same private member more than once"):G instanceof WeakSet?G.add($):G.set($,z),F=($,G,z,Qn)=>(Ia($,G,"write to private field"),Qn?Qn.call($,z):G.set($,z),z),ae=($,G,z)=>(Ia($,G,"access private method"),z);(function(){"use strict";var li,ui,ci,rn,an,xt,on,In,Bn,Tt,nt,sn,ge,Ba,Ga,Va,Ci,Ee,Oa,Ve,Dt,_e,He,ye,Oe,rt,Ot,vt,ln,un,cn,We,wr,ee,Jd,zd,eh,Ha,Cr,Rr,Wa,fi,Le,je,be,Lt,Gn,Vn,qr,di;const $=[{activeIcon:"pause",command:"aqe:play",icon:"play",iconOnly:!0,label:"Play",title:"Play or pause current audio"},{activeIcon:"refresh-cw",command:"aqe:analyze",icon:"chart-line",iconOnly:!0,label:"Graph",title:"Analyze and show pitch/intensity graph"},{command:"aqe:show-file",icon:"folder-open",label:"Folder",title:"Show current audio file in folder"},{command:"aqe:trim-left",icon:"scissors",label:"-L",title:"Trim 100 ms from left"},{command:"aqe:trim-right",icon:"scissors",label:"-R",title:"Trim 100 ms from right"},{command:"aqe:remove-pauses",icon:"timer-reset",label:"Shorten Pauses",title:"Speed up long internal pauses"},{command:"aqe:slower",icon:"rewind",label:"Slower",title:"Decrease speed"},{command:"aqe:faster",icon:"fast-forward",label:"Faster",title:"Increase speed"},{command:"aqe:volume-down",icon:"volume-1",iconOnly:!0,label:"Volume -",title:"Decrease volume"},{command:"aqe:volume-up",icon:"volume-2",iconOnly:!0,label:"Volume +",title:"Increase volume"},{command:"aqe:undo",icon:"undo-2",iconOnly:!0,label:"Undo",title:"Restore the previous generated audio reference"},{command:"aqe:redo",icon:"redo-2",iconOnly:!0,label:"Redo",title:"Restore the most recently undone audio reference"},{command:"aqe:settings",icon:"settings",iconOnly:!0,label:"Settings",title:"Open Audio Quick Editor settings"}],G=[{command:"aqe:denoise-standard",icon:"volume-x",label:"Standard",title:"Denoise speech with DeepFilterNet"},{command:"aqe:rnnoise",icon:"waves",label:"RNNoise",title:"Denoise speech with RNNoise"}],z=new Set(["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:remove-pauses","aqe:denoise-standard","aqe:rnnoise","aqe:volume-down","aqe:volume-up"]),Qn={"aqe:play":"play","aqe:analyze":"graph","aqe:show-file":"show-file","aqe:delete-selection":"delete-selection","aqe:trim-left":"trim-left","aqe:trim-right":"trim-right","aqe:remove-pauses":"remove-pauses","aqe:denoise-standard":"denoise-standard","aqe:rnnoise":"rnnoise","aqe:slower":"slower","aqe:faster":"faster","aqe:volume-down":"volume-down","aqe:volume-up":"volume-up","aqe:undo":"undo","aqe:redo":"redo","aqe:settings":"settings"};function xr(e,t){return`aqe-button-${e}-${Qn[t]}`}function ja(e){return e==="aqe:denoise-standard"?"Denoising with Standard...":e==="aqe:rnnoise"?"Denoising with RNNoise...":e==="aqe:delete-selection"?"Deleting region...":"Processing..."}function Xe(e){return document.querySelector(`.aqe-controls[data-aqe-field-ord="${e}"]`)}function L(e){return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${e}"]`)}function Ua(e,t){const n=Xe(e);return(n==null?void 0:n.querySelector(`[data-aqe-command="${t}"]`))??null}function Ka(e){return Ua(e,"aqe:analyze")}function Xa(e){return Ua(e,"aqe:play")}function Ya(e){const t=Xe(e);return(t==null?void 0:t.querySelector(".aqe-repeat-button"))??null}function Zn(){return Array.from(document.querySelectorAll(".aqe-button"))}function Tr(){return Array.from(document.querySelectorAll(".aqe-visualizer"))}const Qa=[];let Jn=null,zn=null;function er(e){globalThis.pycmd!==void 0&&globalThis.pycmd(e)}function It(e,t){er(`focus:${e}`),er(t)}function Ri(e){Jn=e,er("aqe:analyze-field")}function xi(e){Qa.push(e),er("aqe:frontend-log")}function Ti(){return Qa.shift()??null}function Di(e){window.__aqePendingPlaybackRequest=e,window.__aqeLastPlaybackRequest=e}function Oi(){if(!window.__aqePendingPlaybackRequest)return null;const e=window.__aqePendingPlaybackRequest;return window.__aqePendingPlaybackRequest=null,e}function Li(){if(!Jn)return null;const e=Jn;return Jn=null,e}function $i(e){zn=e}function Ii(){if(!zn)return null;const e=zn;return zn=null,e}function Bi(e){window.__aqeLastCursorIntent=e}function Gi(e){return encodeURIComponent(e||"").replaceAll("%2F","/")}function Pe(e){return(e==null?void 0:e.querySelector(".aqe-audio-clock"))??null}function Dr(e){e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!1,e.__aqeAudioClockLastSeekedMs=0,e.dataset.progressClockMode="stopped"}function hn(e){const t=Pe(e);if(!(!t||typeof t.pause!="function"))try{t.pause()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function Or(e){const t=Pe(e);if(Dr(e),!!t){hn(e),t.removeAttribute("src"),t.src="";try{t.load()}catch{e.__aqeAudioClockFallback=!0}}}function Vi(e,t){const n=Pe(e);if(Dr(e),!n){e.__aqeAudioClockFallback=!0;return}if(hn(e),!t){Or(e);return}n.setAttribute("src",Gi(t));try{n.load()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function Hi(e,t={}){const n=Pe(e);!n||n.__aqeClockHandlersInstalled||(n.__aqeClockHandlersInstalled=!0,n.addEventListener("loadedmetadata",()=>{n.getAttribute("src")&&(e.__aqeAudioClockAvailable=!0,e.__aqeAudioClockFallback=!1)}),n.addEventListener("error",()=>{var r;e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,e.dataset.playbackState==="playing"&&e.dataset.progressClockMode==="audio"&&((r=t.onErrorDuringPlayback)==null||r.call(t))}),n.addEventListener("ended",()=>{var r;e.dataset.playbackState==="playing"&&((r=t.onEndedDuringPlayback)==null||r.call(t))}),n.addEventListener("seeked",()=>{e.__aqeAudioClockLastSeekedMs=Math.round((Number(n.currentTime)||0)*1e3)}))}function tr(e){const t=Pe(e);return!t||!(e!=null&&e.__aqeAudioClockAvailable)||!t.getAttribute("src")?!1:t.readyState===void 0||t.readyState>=1}function nr(e,t,n){const r=Pe(e);if(!r)return!1;const a=Math.max(0,Math.min(Number(t)||0,n||0));try{return r.currentTime=a/1e3,e.__aqeAudioClockLastSeekedMs=Math.round(a),!0}catch{return e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,!1}}var pn=(e=>(e.Debug="debug",e.Error="error",e.Info="info",e.Unknown="unknown",e.Warn="warn",e))(pn||{});function Wi(e){return e==="error"?console.error:console.warn}function ji(e){return e==="debug"?pn.Debug:e==="warn"?pn.Warn:e==="error"?pn.Error:pn.Info}function Lr(e,t=0){const n=Ui(e);return n!==void 0?n:Array.isArray(e)?Ki(e,t):e!==null&&typeof e=="object"?Xi(e,t):Yi(e)}function Ui(e){if(e===void 0)return"[undefined]";if(e===null)return null;if(typeof e=="boolean"||typeof e=="number"||typeof e=="string")return e}function Ki(e,t){return t>=4?"[array]":e.map(n=>Lr(n,t+1))}function Xi(e,t){if(t>=4)return"[object]";const n={};for(const[r,a]of Object.entries(e))n[r]=Lr(a,t+1);return n}function Yi(e){return typeof e=="bigint"?e.toString():typeof e=="symbol"?e.description?`Symbol(${e.description})`:"Symbol()":typeof e=="function"?`[function ${e.name||"anonymous"}]`:"[unserializable]"}function Qi(e,t,n){const r={level:ji(e),message:t};return n!==void 0&&(r.context=Lr(n)),r}function Zi(e,t){function n(r,a,o){const s=Wi(r);o===void 0?s(`[${e}] ${a}`):s(`[${e}] ${a}`,o);try{t(Qi(r,a,o))}catch{}}return{debug:(r,a)=>n("debug",r,a),error:(r,a)=>n("error",r,a),info:(r,a)=>n("info",r,a),warn:(r,a)=>n("warn",r,a)}}const ce=Zi("editor",xi),_n=[],rr=new Set;let ar=null,or=null,sr=!1;function Ji(){_n.length=0,rr.clear(),ar=null,or=null,sr=!1}function zi(e,t){for(const n of e){if(!n.sourceFilename)continue;const r=el(n);if(rr.has(r))continue;const a=L(n.ord);if((a==null?void 0:a.dataset.hasTrack)==="true"&&a.dataset.sourceFilename===n.sourceFilename){rr.add(r);continue}rr.add(r),_n.push({key:r,ord:n.ord,sourceFilename:n.sourceFilename})}ir(t)}function ir(e){if(!(ar!==null||e.anyBusy()))for(;_n.length;){const t=_n.shift();if(!t)return;const n=L(t.ord);if(!n){Ja(t,e);return}const r=Xe(t.ord);if(!r){Ja(t,e);return}if((r.dataset.aqeSourceFilename||t.sourceFilename)===t.sourceFilename&&!(n.dataset.hasTrack==="true"&&n.dataset.sourceFilename===t.sourceFilename)){ar=t.key,or=t.ord,e.requestDefaultGraph({ord:t.ord,sourceFilename:t.sourceFilename});return}}}function Za(e,t){or===e&&(ar=null,or=null,queueMicrotask(()=>ir(t)))}function el(e){return`${e.ord}\0${e.sourceFilename}`}function Ja(e,t){_n.unshift(e),!sr&&(sr=!0,window.setTimeout(()=>{sr=!1,ir(t)},0))}function tl(e,t){return Math.max(t.startMs,Math.min(Number(e)||0,t.endMs))}function nl(e){let t="start";e.playbackState==="playing"&&(t="pause"),e.playbackState==="paused"&&(t=e.resumeRequiresRestart?"start":"resume");let n=e.anchorMs;return t==="start"&&e.region.mode==="selection"&&(n=e.region.startMs),t==="pause"&&(n=za(e.currentProgressMs,e.cursorMs,n)),t==="resume"&&(n=za(e.currentProgressMs,e.cursorMs,n),e.region.mode==="selection"&&(n<e.region.startMs||n>e.region.endMs)&&(t="start",n=e.region.startMs)),{action:t,cursorMs:Math.round(n),endMs:Math.round(e.region.endMs),engine:e.engine,loop:e.repeat,ord:e.ord,regionMode:e.region.mode}}function za(e,t,n){return Number(e||t||n||0)}function rl(e){return{analyzerName:e.analyzerName,durationMs:Number(e.durationMs)||0,pitchMaxHz:e.pitchMaxHz,pitchMinHz:e.pitchMinHz,points:e.points.map(al),sourceFilename:e.sourceFilename}}function al(e){const t=typeof e[0]=="number"?e[0]:0,n=typeof e[1]=="number"?e[1]:null,r=typeof e[2]=="number"?e[2]:null,a=typeof e[3]=="boolean"?e[3]:!1;return[t,n,r,a]}function $r(e){return e==="playing"||e==="paused"||e==="stopped"}const eo=50,ol=4;function to(){return{active:!1,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:null,startMs:null}}function no(e,t){return Math.max(0,Math.min(Number(e)||0,Math.max(0,Number(t)||0)))}function lr(e,t,n,r=eo){const a=no(Math.min(e,t),n),o=no(Math.max(e,t),n);return!n||o-a<r?null:{startMs:Math.round(a),endMs:Math.round(o)}}function sl(e,t){if(!e.active||e.startMs===null||e.endMs===null)return null;const n=lr(e.startMs,e.endMs,t);return n?{...n,mode:"selection"}:null}function il(e,t){if(!e.draftActive||e.draftStartMs===null||e.draftEndMs===null)return null;const n=lr(e.draftStartMs,e.draftEndMs,t);return n?{...n,mode:"selection"}:null}function ll(e,t,n,r){const a=lr(t,n,r);return a?{...e,active:!0,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:a.endMs,startMs:a.startMs}:cl(e)}function ul(e,t,n,r){const a=lr(t,n,r);return a?{...e,draftActive:!0,draftEndMs:a.endMs,draftStartMs:a.startMs}:ro(e)}function cl(e){return{...ro(e),active:!1,endMs:null,startMs:null}}function ro(e){return{...e,draftActive:!1,draftEndMs:null,draftStartMs:null}}function ao(e,t,n,r){return Math.abs(t.clientX-e.clientX)<ol||Math.abs(r-n)<eo}const q={width:620,height:150,left:44,right:10,top:10,bottom:34};function oo(){return q.width-q.left-q.right}function so(){return q.height-q.top-q.bottom}function at(e,t){return t?q.left+Math.max(0,Math.min(1,e/t))*oo():q.left}function fl(e,t,n){if(!e||!t||!n||n<=t)return q.height-q.bottom;const r=Math.max(0,Math.min(1,(e-t)/(n-t)));return q.top+(1-r)*so()}function io(e,t){return t&&t<2e3?`${Math.round(e)} ms`:`${(e/1e3).toFixed(2)}s`}function dl(e,t){if(!e.length||!t)return"";const n=q.height-q.bottom,r=e[0];if(!r)return"";const a=`M ${at(r[0],t).toFixed(2)} ${n.toFixed(2)}`,o=e.map(l=>{const c=at(l[0],t).toFixed(2),f=Math.max(0,Math.min(1,l[2]??0)),u=(n-f*so()).toFixed(2);return`L ${c} ${u}`}).join(" "),s=e.at(-1)??r,i=`L ${at(s[0],t).toFixed(2)} ${n.toFixed(2)} Z`;return`${a} ${o} ${i}`}function hl(e,t,n,r){const a=[];let o=[];for(const s of e){const i=s[1];if(!(s[3]===!0&&i!==null&&i!==void 0)){o.length&&a.push(o),o=[];continue}o.push([at(s[0],t),fl(i,n,r)])}return o.length&&a.push(o),a}function pl(e,t){const n=e.querySelector(".aqe-pitch");if(n){n.textContent="";for(const r of hl(t.points,t.durationMs,t.pitchMinHz,t.pitchMaxHz)){if(r.length<2)continue;const a=document.createElementNS("http://www.w3.org/2000/svg","path");a.setAttribute("class","aqe-pitch-path"),a.setAttribute("d",r.map((o,s)=>{const i=o[0]??0,l=o[1]??0;return`${s?"L":"M"} ${i.toFixed(2)} ${l.toFixed(2)}`}).join(" ")),n.appendChild(a)}}}function _l(e,t){const n=e.querySelector(".aqe-labels");if(!n)return;n.textContent="";const r=t.pitchMaxHz||500,a=t.pitchMinHz||75;for(const o of[[r,q.top+10],[a,q.height-q.bottom]]){const s=document.createElementNS("http://www.w3.org/2000/svg","text");s.setAttribute("class","aqe-hz-label"),s.setAttribute("x","2"),s.setAttribute("y",String(o[1])),s.textContent=`${Math.round(o[0])} Hz`,n.appendChild(s)}}function ml(e,t){const n=e.querySelector(".aqe-x-axis");if(!n)return;n.textContent="";const r=[0,t/2,t].filter((a,o,s)=>o===0||a!==s[o-1]);for(const a of r){const o=at(a,t),s=document.createElementNS("http://www.w3.org/2000/svg","line");s.setAttribute("class","aqe-x-tick"),s.setAttribute("x1",o.toFixed(2)),s.setAttribute("x2",o.toFixed(2)),s.setAttribute("y1",String(q.height-q.bottom)),s.setAttribute("y2",String(q.height-q.bottom+4));const i=document.createElementNS("http://www.w3.org/2000/svg","text");i.setAttribute("class","aqe-x-label"),i.setAttribute("x",o.toFixed(2)),i.setAttribute("y",String(q.height-8)),i.textContent=io(a,t),n.append(s,i)}}function lo(e){const t=e.getBoundingClientRect(),n=Number(t.width)||q.width,r=Number(t.height)||q.height,a=Math.min(n/q.width,r/q.height)||1;return{left:t.left+q.left*a,width:oo()*a}}function mn(e,t,n){const r=lo(t);return Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*n}function vl(e){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="true",e.dataset.hasTrack="false",e.dataset.durationMs="0",e.dataset.sourceFilename="",e.dataset.anchorMs="0",e.dataset.cursorMs="0",e.dataset.progressMs="0",e.dataset.resumeRequiresRestart="false",e.dataset.playbackEngine="",e.dataset.playbackStartMs="0",e.dataset.playbackEndMs="0",e.dataset.playbackRegionMode="full",uo(e)}function gl(e,t){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="false",e.dataset.hasTrack="true",e.dataset.durationMs=String(t.durationMs||0),e.dataset.analyzerName=t.analyzerName||"",e.dataset.sourceFilename=t.sourceFilename||"";const n=e.querySelector(".aqe-intensity");n&&n.setAttribute("d",dl(t.points,t.durationMs)),pl(e,t),_l(e,t),ml(e,t.durationMs||0)}function yl(e,t,n="info"){const r=e.querySelector(".aqe-visualizer-status"),a=e.querySelector(".aqe-spinner"),o=n==="processing";e.dataset.graphBusy=o?"true":"false",a&&(a.hidden=!o),r&&(r.textContent=t||"",r.dataset.kind=n||"info")}function bl(e,t,n){const r=e.querySelector(".aqe-selection"),a=e.querySelector(".aqe-selection-start"),o=e.querySelector(".aqe-selection-end"),s=n??t,i=Number(e.dataset.durationMs||"0");if(!r||!a||!o||!s||!i){r==null||r.setAttribute("width","0"),r==null||r.setAttribute("visibility","hidden"),r==null||r.classList.remove("aqe-selection-draft"),a==null||a.setAttribute("visibility","hidden"),o==null||o.setAttribute("visibility","hidden");return}const l=at(s.startMs,i),c=at(s.endMs,i);r.setAttribute("visibility","visible"),r.classList.toggle("aqe-selection-draft",n!==null),r.setAttribute("x",l.toFixed(2)),r.setAttribute("y",String(q.top)),r.setAttribute("width",Math.max(0,c-l).toFixed(2)),r.setAttribute("height",String(q.height-q.top-q.bottom)),a.setAttribute("visibility","visible"),o.setAttribute("visibility","visible");for(const[f,u]of[[a,l],[o,c]])f.setAttribute("x1",u.toFixed(2)),f.setAttribute("x2",u.toFixed(2)),f.setAttribute("y1",String(q.top)),f.setAttribute("y2",String(q.height-q.bottom))}function wl(e,t,n){const r=at(t,n),a=e.querySelector(".aqe-cursor");a&&(a.setAttribute("x1",r.toFixed(2)),a.setAttribute("x2",r.toFixed(2)));const o=e.querySelector(".aqe-cursor-label");o&&(o.textContent=io(t,n))}function uo(e){var t;(t=e.querySelector(".aqe-intensity"))==null||t.setAttribute("d",""),Ir(e,".aqe-pitch"),Ir(e,".aqe-labels"),Ir(e,".aqe-x-axis")}function ql(e){const t=e.querySelector(".aqe-cursor");t&&(t.setAttribute("x1",String(q.left)),t.setAttribute("x2",String(q.left)));const n=e.querySelector(".aqe-cursor-label");n&&(n.textContent="0 ms")}function Ml(e,t){return{analyzerName:t.analyzerName,durationMs:t.durationMs,ord:e,points:t.points.length,sourceFilename:t.sourceFilename}}function Ir(e,t){const n=e.querySelector(t);n&&(n.textContent="")}function vn(e){return!e||e.dataset.selectionActive!=="true"?null:sl({active:e.dataset.selectionActive==="true",startMs:Number(e.dataset.selectionStartMs||"0"),endMs:Number(e.dataset.selectionEndMs||"0")},Number(e.dataset.durationMs||"0"))}function Br(e){return!e||e.dataset.selectionDraftActive!=="true"?null:il({draftActive:e.dataset.selectionDraftActive==="true",draftStartMs:Number(e.dataset.selectionDraftStartMs||"0"),draftEndMs:Number(e.dataset.selectionDraftEndMs||"0")},Number(e.dataset.durationMs||"0"))}function co(e){const t=vn(e);return t||{startMs:0,endMs:Number(e.dataset.durationMs||"0")||0,mode:"full"}}function Bt(e,t={}){e.dataset.selectionDraftActive="false",e.dataset.selectionDraftStartMs="",e.dataset.selectionDraftEndMs="",t.redraw!==!1&&ur(e)}function Sl(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=ul(to(),t,n,a);return!o.draftActive||o.draftStartMs===null||o.draftEndMs===null?(Bt(e,r),!1):(e.dataset.selectionDraftActive="true",e.dataset.selectionDraftStartMs=String(o.draftStartMs),e.dataset.selectionDraftEndMs=String(o.draftEndMs),r.redraw!==!1&&ur(e),!0)}function kl(e,t,n={}){const r=Br(e);return r?(Bt(e,{redraw:!1}),Al(e,r.startMs,r.endMs,t,n)):(Bt(e),!1)}function fo(e,t={}){if(e.dataset.selectionActive="false",e.dataset.selectionStartMs="",e.dataset.selectionEndMs="",Bt(e,{redraw:!1}),ur(e),t.resetPlaybackRegion!==!1){const n=co(e);e.dataset.playbackStartMs=String(Math.round(n.startMs)),e.dataset.playbackEndMs=String(Math.round(n.endMs)),e.dataset.playbackRegionMode=n.mode}}function Al(e,t,n,r,a={}){const o=Number(e.dataset.durationMs||"0"),s=ll(to(),t,n,o);return!s.active||s.startMs===null||s.endMs===null?(fo(e),!1):(Bt(e,{redraw:!1}),e.dataset.selectionActive="true",e.dataset.selectionStartMs=String(s.startMs),e.dataset.selectionEndMs=String(s.endMs),e.dataset.playbackStartMs=String(s.startMs),e.dataset.playbackEndMs=String(s.endMs),e.dataset.playbackRegionMode="selection",ur(e),a.updateCursor!==!1&&r.setCursor(e,s.startMs,!1),!0)}function ur(e){const t=Br(e),n=t??vn(e);bl(e,n,t)}function El(){return document.body.dataset.aqeBusy==="true"}function Pl(e){var t;return((t=Xe(e))==null?void 0:t.querySelector(".aqe-delete-region-button"))??null}function ho(e,t){return e.startMs<=0&&e.endMs>=t}function po(e,t){return!!e&&e.endMs>e.startMs&&!ho(e,t)}function gn(e){const t=Number(e.dataset.aqeFieldOrd||"0"),n=Pl(t);if(!n)return;const r=vn(e),a=Number(e.dataset.durationMs||"0"),o=r!==null,s=po(r,a);n.hidden=!o,n.disabled=El()||!s,n.dataset.aqeButtonState=s?"default":"unavailable",n.title=s?"Delete selected region":"Cannot delete the whole audio clip",n.setAttribute("aria-disabled",n.disabled?"true":"false")}function Nl(){Tr().forEach(gn)}function _o(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=Number(e.dataset.durationMs||"0")||0,a=vn(e);if(!a||!po(a,r))return a&&ho(a,r)&&ce.warn("region delete rejected whole clip",{ord:n,sourceFilename:e.dataset.sourceFilename||"",selectionStartMs:a.startMs,selectionEndMs:a.endMs,durationMs:r,trigger:t}),null;const o=e.dataset.sourceFilename||"";if(!o)return null;const s=e.dataset.playbackState;return{ord:n,sourceFilename:o,selectionStartMs:Math.round(a.startMs),selectionEndMs:Math.round(a.endMs),cursorMs:Math.round(Number(e.dataset.cursorMs||"0")||0),durationMs:Math.round(r),trigger:t,playbackActive:$r(s)&&s!=="stopped"}}function Fl(e,t,n,r,a){e.preventDefault();const o=a.playbackStateFor(t),s=t.querySelector(".aqe-visualizer-svg"),i=Number(t.dataset.durationMs||"0");if(!s||!i)return;o==="playing"&&a.stopProgressClock(t);const l=f=>{a.setCursor(t,mo(f,s,i,t,a),!1)},c=f=>{window.removeEventListener("pointermove",l),window.removeEventListener("pointerup",c);const u=o==="playing";o==="paused"&&(t.dataset.resumeRequiresRestart="true");const h=mo(f,s,i,t,a),m=u&&a.audioClockReady(t)?"html":"";a.setCursor(t,h,r,{previousPlaybackState:o,restartPlayback:u,engine:m}),a.audioClockReady(t)&&a.seekAudioClock(t,h),u&&m==="html"&&a.startEditorHtmlPlayback(t,a.playbackRequestForStart(t,n,h,"html"))};l(e),window.addEventListener("pointermove",l),window.addEventListener("pointerup",c)}function Cl(e,t,n,r){e.preventDefault();const a=t.querySelector(".aqe-visualizer-svg"),o=Number(t.dataset.durationMs||"0");if(!a||!o)return;const s=r.playbackStateFor(t),i=r.currentProgressMs(t)??Number(t.dataset.cursorMs||"0"),l={clientX:e.clientX},c=mn(e,a,o);let f=!1,u=A=>{},h=A=>{},m=()=>{},_=A=>{};const w=()=>{window.removeEventListener("pointermove",u),window.removeEventListener("pointerup",h),window.removeEventListener("pointercancel",m),window.removeEventListener("keydown",_),window.removeEventListener("blur",m),a.removeEventListener("lostpointercapture",m)},p=()=>{f||s!=="playing"||(f=!0,r.stopProgressClock(t,{clearEngine:!1}),r.setCursor(t,i,!1,{updateAnchor:!1}))},v=()=>{s==="playing"&&f&&r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,i,"html"))};u=A=>{const b=mn(A,a,o);if(ao(l,A,c,b)){r.clearSelectionDraft(t);return}p(),r.setSelectionDraft(t,c,b)},h=A=>{w();const b=mn(A,a,o);if(ao(l,A,c,b)){r.clearSelection(t),v();return}p(),r.draftSelectionForVisualizer(t)||r.setSelectionDraft(t,c,b,{redraw:!1});const S=r.commitSelectionDraft(t);if(s==="paused"&&(t.dataset.resumeRequiresRestart="true"),S&&s==="playing"){const E=r.selectionForVisualizer(t);r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,(E==null?void 0:E.startMs)??c,"html"))}},m=()=>{w(),r.clearSelectionDraft(t),v()},_=A=>{A.key==="Escape"&&m()},window.addEventListener("pointermove",u),window.addEventListener("pointerup",h),window.addEventListener("pointercancel",m),window.addEventListener("keydown",_),window.addEventListener("blur",m),a.addEventListener("lostpointercapture",m)}function Rl(e,t,n){const r=n.visualizerForOrd(t);if(r){if(e.shiftKey){Cl(e,r,t,n);return}Fl(e,r,t,!0,n)}}function mo(e,t,n,r,a){const o=mn(e,t,n),s=a.selectionForVisualizer(r);return s&&r.dataset.repeatEnabled==="true"?tl(o,s):o}function bt(e){e.__aqePlaybackTimer&&(window.cancelAnimationFrame(e.__aqePlaybackTimer),e.__aqePlaybackTimer=null)}function vo(e){const t=Number(e.dataset.durationMs||"0"),n=performance.now()-Number(e.dataset.playStartedAt||"0");return Math.min(t,Number(e.dataset.playStartMs||"0")+n)}function go(e){const t=Pe(e);if(!t)return null;const n=Number(e.dataset.durationMs||"0");return Math.min(n,(Number(t.currentTime)||0)*1e3)}function yo(e){return e.dataset.progressClockMode==="audio"?go(e):e.dataset.progressClockMode==="manual"?vo(e):Number(e.dataset.progressMs||e.dataset.cursorMs||"0")}function Gr(e,t,n,r={}){return t<Ll(e,n)?!1:n.repeatEnabledFor(e)?($l(e,n,r),!0):(xl(e,n),!0)}function xl(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=t.effectivePlaybackRegion(e),a=e.dataset.playbackRegionMode==="selection"?r.startMs:Number(e.dataset.anchorMs||"0");Hr(e,t),t.setCursor(e,a,!1,{updateAnchor:!1}),tr(e)&&nr(e,a,Number(e.dataset.durationMs||"0")),t.clearStatus(n),window.__aqeActiveField=n,t.focusAndSendCommand(n,"aqe:play-ended")}function Vr(e,t){const n=()=>{if(e.dataset.playbackState!=="playing")return;const r=go(e);if(r===null){Ye(e,Number(e.dataset.cursorMs||"0"),t);return}t.setCursor(e,r,!1,{updateAnchor:!1}),!Gr(e,r,t)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(n))};e.__aqePlaybackTimer=window.requestAnimationFrame(n)}function Ye(e,t,n){if(bt(e),hn(e),!Number(e.dataset.durationMs||"0"))return;const a=bo(e,t);e.__aqeAudioClockFallback=!0,e.dataset.playbackState="playing",e.dataset.progressClockMode="manual",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),Wr(e,a,n),n.setPlaybackButtonLabel(e,"Pause");const o=()=>{if(e.dataset.playbackState!=="playing")return;const s=vo(e);n.setCursor(e,s,!1,{updateAnchor:!1}),!Gr(e,s,n)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(o))};e.__aqePlaybackTimer=window.requestAnimationFrame(o)}function Tl(e,t,n,r={}){var i;const a=Pe(e);if(!a||!nr(e,t,Number(e.dataset.durationMs||"0"))||typeof a.play!="function"){if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}Ye(e,t,n);return}e.dataset.progressClockMode="audio",e.__aqeAudioClockFallback=!1;const o=()=>{var l;if(r.manualFallback===!1){(l=r.onAudioPlayFailed)==null||l.call(r);return}Ye(e,t,n)},s=()=>{var l;e.dataset.playbackState==="playing"&&(bt(e),e.dataset.progressClockMode="audio",ce.info("html audio playback started",{ord:e.dataset.aqeFieldOrd}),Vr(e,n),(l=r.onAudioStarted)==null||l.call(r))};Promise.resolve(a.play()).then(s).catch(()=>{e.dataset.playbackState==="playing"&&(ce.warn("html audio play rejected; using manual clock",{ord:e.dataset.aqeFieldOrd}),o())})}function Dl(e,t,n,r={}){var i;const a=r.engine||e.dataset.playbackEngine||"";if(Hr(e,n,{clearEngine:!1}),n.stopOtherPlayback(e),!Number(e.dataset.durationMs||"0"))return;const s=bo(e,t);if(e.dataset.playbackEngine=a,e.dataset.playbackState="playing",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(s),Wr(e,s,n),n.setCursor(e,s,!1,{updateAnchor:!1}),n.setPlaybackButtonLabel(e,"Pause"),ce.info("playback clock selected",{engine:a||"auto",startMs:s}),a==="native"){Ye(e,s,n);return}if(tr(e)){Tl(e,s,n,r);return}if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}Ye(e,s,n)}function Ol(e,t){const n=yo(e);n!==null&&t.setCursor(e,n,!1,{updateAnchor:!1}),bt(e),hn(e),e.dataset.playbackState="paused",e.dataset.progressClockMode="stopped",t.setPlaybackButtonLabel(e,"Play")}function Hr(e,t,n={}){bt(e),hn(e),e.dataset.playbackState="stopped",e.dataset.progressClockMode="stopped",e.dataset.resumeRequiresRestart="false",n.clearEngine!==!1&&(e.dataset.playbackEngine=""),n.clearAudio&&Or(e),t.setPlaybackButtonLabel(e,"Play")}function Wr(e,t,n,r=n.effectivePlaybackRegion(e)){e.dataset.playbackStartMs=String(Math.round(t)),e.dataset.playbackEndMs=String(Math.round(r.endMs)),e.dataset.playbackRegionMode=r.mode}function Ll(e,t){const n=t.effectivePlaybackRegion(e),r=Number(e.dataset.playbackEndMs||"0")||n.endMs;return Math.max(n.startMs,Math.min(r,Number(e.dataset.durationMs||"0")||0))}function $l(e,t,n={}){const r=t.effectivePlaybackRegion(e),a=r.startMs;if(Wr(e,a,t,r),e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),t.setCursor(e,a,!1,{updateAnchor:!1}),e.dataset.progressClockMode!=="audio"||!tr(e)){Ye(e,a,t);return}if(!nr(e,a,Number(e.dataset.durationMs||"0"))){Ye(e,a,t);return}if(!n.forceAudioPlay){bt(e),Vr(e,t);return}const o=Pe(e);!o||typeof o.play!="function"||(bt(e),Promise.resolve(o.play()).then(()=>{e.dataset.playbackState==="playing"&&Vr(e,t)}).catch(()=>{e.dataset.playbackState==="playing"&&Ye(e,a,t)}))}function bo(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function wo(){return document.body.dataset.aqeBusy==="true"}function qo(){var e;return((e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.repeatPlaybackByDefault)===!0}function Il(e){for(const t of Tr())t!==e&&Ht(t)!=="stopped"&&ot(t)}function Bl(){for(const e of Tr())Ht(e)!=="stopped"&&ot(e)}function Gt(e,t,n="",r=""){document.body.dataset.aqeBusy=t?"true":"false",document.querySelectorAll(".aqe-controls").forEach(s=>{s.dataset.busy=t?"true":"false"}),Zn().forEach(s=>{s.disabled=!!t}),Nl(),t||queueMicrotask(()=>ir(Zr()));const a=Xe(e),o=a==null?void 0:a.querySelector(".aqe-status");o&&(o.textContent=n||"",o.dataset.kind=t?"processing":"info",o.title=r||"")}function Mo(e,t="info"){const n=Number(window.__aqeActiveField??0),r=Xe(n),a=r==null?void 0:r.querySelector(".aqe-status");a&&(a.textContent=e||"",a.dataset.kind=t||"info")}function Gl(e){const t=Xe(e),n=t==null?void 0:t.querySelector(".aqe-status");n&&(n.textContent="",n.dataset.kind="info",n.title="")}function Vt(e,t,n){var o;const r=t==="aqe:play"?Xa(e):t==="aqe:analyze"?Ka(e):((o=Xe(e))==null?void 0:o.querySelector(`[data-aqe-command="${t}"]`))??null;if(!r)return;const a=r.querySelector(".aqe-button-label");a?a.textContent=n:r.textContent=n,t==="aqe:play"&&(r.dataset.aqeButtonState=n==="Pause"?"pause":"play"),t==="aqe:analyze"&&(r.dataset.aqeButtonState=n==="Redraw"?"redraw":"graph")}function So(e,t,n){if(!wo()){if(typeof t.focus=="function"&&t.focus(),window.__aqeActiveField=n,ce.info("command dispatched",{command:e,ord:n}),e==="aqe:analyze"){Po(n,!0);return}e==="aqe:play"&&uu(n)||(z.has(e)&&(Bl(),Gt(n,!0,ja(e))),It(n,e))}}function Vl(e){Dr(e)}function Hl(e){bt(e)}function Wl(e){Or(e)}function jl(e,t){Vi(e,t)}function Ul(e){Hi(e,{onErrorDuringPlayback(){ce.warn("audio clock failed during playback",{ord:e.dataset.aqeFieldOrd}),lu(e,Number(e.dataset.cursorMs||"0"))},onEndedDuringPlayback(){iu(e,Number(e.dataset.durationMs||"0"),{forceAudioPlay:!0})}})}function jr(e){return tr(e)}function Kl(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function ko(e){return vn(e)}function Ao(e){return Br(e)}function Ur(e){return co(e)}function Kr(e,t){e.dataset.repeatEnabled=t?"true":"false";const n=Number(e.dataset.aqeFieldOrd||"0"),r=Ya(n);r&&(r.ariaPressed=t?"true":"false",r.dataset.aqeButtonState=t?"active":"default")}function Xl(e,t){const n=L(e);return n?(Kr(n,t),!0):!1}function Yl(e,t={}){Bt(e,t)}function Ql(e,t,n,r={}){return Sl(e,t,n,r)}function Zl(e,t={}){const n=kl(e,eu(),t);return gn(e),n}function yn(e,t={}){fo(e,t),gn(e)}function Jl(e){e.dataset.playbackStartMs="0",e.dataset.playbackEndMs=String(Number(e.dataset.durationMs||"0")||0),e.dataset.playbackRegionMode="full",Kr(e,qo()),yn(e,{resetPlaybackRegion:!1})}function zl(){return{audioClockReady:jr,clearSelection:yn,clearSelectionDraft:Yl,commitSelectionDraft:Zl,currentProgressMs:Ro,draftSelectionForVisualizer:Ao,playbackRequestForStart:tu,playbackStateFor:Ht,seekAudioClock:Eo,selectionForVisualizer:ko,setCursor:wt,setSelectionDraft:Ql,startEditorHtmlPlayback:Oo,stopProgressClock:ot,visualizerForOrd:L}}function eu(){return{setCursor:wt}}function Xr(e){return e.dataset.repeatEnabled==="true"}function bn(){return{clearStatus:Gl,effectivePlaybackRegion:Ur,focusAndSendCommand:It,playbackEngineFor:wn,repeatEnabledFor:Xr,setCursor:wt,setPlaybackButtonLabel:su,stopOtherPlayback:Il}}function tu(e,t,n,r=wn(e)){const a=Ur(e);return{ord:t,action:"start",cursorMs:Math.round(Kl(e,n)),endMs:Math.round(a.endMs),engine:r,loop:Xr(e),regionMode:a.mode}}function Eo(e,t){return nr(e,t,Number(e.dataset.durationMs||"0"))}function wt(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Math.max(0,Math.min(Number(t)||0,a||0));if(e.dataset.cursorMs=String(Math.round(o)),e.dataset.progressMs=String(Math.round(o)),r.updateAnchor!==!1&&(e.dataset.anchorMs=String(Math.round(o))),wl(e,o,a),n){window.__aqeActiveField=Number(e.dataset.aqeFieldOrd||"0");const s={cursorMs:Math.round(o),previousPlaybackState:r.previousPlaybackState||Ht(e),restartPlayback:!!r.restartPlayback};r.engine&&(s.engine=r.engine),Bi(s),ce.info("cursor committed",s),It(window.__aqeActiveField,"aqe:set-cursor")}}function nu(e,t){var n;(n=L(t))==null||n.focus(),Rl(e,t,zl())}function Po(e,t){Fo(e)&&(window.__aqeActiveField=e,ce.info("graph requested",{notifyPython:t,ord:e}),Gt(e,!0,"Analyzing...",""),It(e,"aqe:analyze"))}function No(e){Fo(e.ord)&&(ce.info("default graph requested",e),Gt(e.ord,!0,"Analyzing...",""),Ri(e))}function Fo(e){const t=L(e);return t?(ot(t,{clearAudio:!0}),vl(t),yn(t),wt(t,0,!1),Vt(e,"aqe:analyze","Redraw"),Qr(e,"Analyzing...","processing"),!0):!1}function ru(e){return window.__aqePendingGraphRedrawField=e,Yr()}function Yr(){const e=window.__aqePendingGraphRedrawField;if(typeof e!="number")return!1;const t=L(e);return t?(t.dataset.graphBusy==="true"||t.dataset.hasTrack==="true"||Po(e,!0),!0):!1}function Qr(e,t,n="info"){const r=L(e);r&&yl(r,t,n)}function au(e,t,n){const r=L(e);if(!r||!t)return;const a=rl(t);gl(r,a),r.dataset.anchorMs=String(n||0),window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null),yn(r),r.dataset.playbackStartMs="0",r.dataset.playbackEndMs=String(a.durationMs||0),r.dataset.playbackRegionMode="full",jl(r,a.sourceFilename||""),Vt(e,"aqe:analyze","Redraw"),wt(r,n||0,!1),jr(r)&&Eo(r,n||0),Qr(e,a.analyzerName||"","info"),Gt(e,!1,"",""),Za(e,Zr()),ce.info("graph rendered",Ml(e,a))}function ou(e,t,n="info"){n!=="processing"&&window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null);const r=L(e);r&&(r.hidden=!1,r.dataset.graphActive="true",n==="processing"&&(r.dataset.hasTrack="false"),Vt(e,"aqe:analyze","Redraw")),Qr(e,t,n),n!=="processing"&&Za(e,Zr())}function Zr(){return{anyBusy:wo,requestDefaultGraph:No}}function Co(){document.body.dataset.aqeBusy="false",window.__aqeActiveField=null,window.__aqeLastCursorIntent=null,document.querySelectorAll(".aqe-controls").forEach(e=>{e.dataset.busy="false",e.dataset.aqeSourceFilename="",e.querySelectorAll(".aqe-button").forEach(o=>{o.disabled=!1,o.dataset.aqeCommand==="aqe:analyze"&&Vt(Number(e.dataset.aqeFieldOrd||"0"),"aqe:analyze","Graph"),o.dataset.aqeCommand==="aqe:play"&&Vt(Number(e.dataset.aqeFieldOrd||"0"),"aqe:play","Play")});const t=e.querySelector(".aqe-status");t&&(t.textContent="",t.dataset.kind="info",t.title="");const n=e.querySelector(".aqe-visualizer");if(!n)return;Hl(n),Wl(n),n.hidden=!0,n.dataset.anchorMs="0",n.dataset.cursorMs="0",n.dataset.progressMs="0",n.dataset.graphActive="false",n.dataset.graphBusy="false",n.dataset.hasTrack="false",n.dataset.playbackState="stopped",n.dataset.playbackEngine="",n.dataset.resumeRequiresRestart="false",n.dataset.durationMs="0",n.dataset.sourceFilename="",n.dataset.analyzerName="",n.dataset.playStartedAt="0",n.dataset.playStartMs="0",n.dataset.playbackStartMs="0",n.dataset.playbackEndMs="0",n.dataset.playbackRegionMode="full",n.dataset.progressClockMode="stopped",Kr(n,qo()),yn(n),uo(n),ql(n);const r=n.querySelector(".aqe-visualizer-status");r&&(r.textContent="",r.dataset.kind="info");const a=n.querySelector(".aqe-spinner");a&&(a.hidden=!0)})}function su(e,t){const n=Number(e.dataset.aqeFieldOrd||"0");Vt(n,"aqe:play",t)}function Ro(e){return yo(e)}function iu(e,t,n={}){return Gr(e,t,bn(),n)}function lu(e,t){Ye(e,t,bn())}function xo(e,t,n={}){Dl(e,t,bn(),n)}function To(e){Ol(e,bn())}function ot(e,t={}){Hr(e,bn(),t)}function Do(e){const t=L(e);return t?nl({anchorMs:Number(t.dataset.anchorMs||t.dataset.cursorMs||"0"),currentProgressMs:Ro(t),cursorMs:Number(t.dataset.cursorMs||"0"),engine:wn(t),ord:e,playbackState:Ht(t),region:Ur(t),repeat:Xr(t),resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true"}):{ord:e,action:"start",cursorMs:0}}function wn(e){if(!e||e.dataset.hasTrack!=="true")return"native";const t=e.dataset.playbackEngine||"";return e.dataset.playbackState!=="stopped"&&(t==="html"||t==="native")?t:jr(e)?"html":"native"}function Jr(e){const t=L(e.ord);t&&(t.dataset.playbackEngine=e.engine||""),Di(e),window.__aqeActiveField=e.ord,ce.info("playback request queued",e),It(e.ord,"aqe:play")}function Oo(e,t){return xo(e,t.cursorMs,{engine:"html",manualFallback:!1,onAudioStarted(){Jr(t)},onAudioPlayFailed(){if(ce.warn("html playback failed; falling back to native",{ord:t.ord}),ot(e),t.regionMode==="selection"||t.loop){window.__aqeActiveField=t.ord,Mo("Selected repeat playback needs browser audio.","warning");return}Jr({...t,engine:"native"})}}),!0}function uu(e){const t=L(e);if(!t||wn(t)!=="html")return!1;const n={...Do(e),engine:"html"};return n.action==="pause"?(To(t),n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0"),Jr(n),!0):(n.action==="resume"&&(n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0")),Oo(t,n))}function cu(e,t,n){const r=L(e);r&&((t==="playing"||t==="paused")&&(r.dataset.resumeRequiresRestart="false"),t==="playing"?xo(r,n,{engine:r.dataset.playbackEngine==="html"||r.dataset.playbackEngine==="native"?r.dataset.playbackEngine:""}):t==="paused"?To(r):ot(r))}function fu(){const e=Oi();if(e)return e;const t=Number(window.__aqeActiveField||"0"),n=Do(t),r=L(t);return r&&(r.dataset.playbackEngine=n.engine||""),n}function du(e){const t=L(e);return t?(ot(t),!0):!1}function hu(){const e=Number(window.__aqeActiveField||"0"),t=L(e);return t?Number(t.dataset.cursorMs||"0"):0}function pu(){const e=Number(window.__aqeActiveField||"0"),t=L(e),n=t?Number(t.dataset.cursorMs||"0"):0;return window.__aqeLastCursorIntent||{cursorMs:n,previousPlaybackState:t?Ht(t):"stopped",restartPlayback:!1}}function Ht(e){const t=e.dataset.playbackState;return $r(t)?t:"stopped"}const Lo=(ui=(li=globalThis.process)==null?void 0:li.env)==null?void 0:ui.NODE_ENV,g=Lo&&!Lo.toLowerCase().startsWith("prod");var zr=Array.isArray,_u=Array.prototype.indexOf,qt=Array.prototype.includes,cr=Array.from,Mt=Object.defineProperty,Qe=Object.getOwnPropertyDescriptor,mu=Object.getOwnPropertyDescriptors,vu=Object.prototype,gu=Array.prototype,$o=Object.getPrototypeOf,Io=Object.isExtensible;function qn(e){return typeof e=="function"}const V=()=>{};function yu(e){for(var t=0;t<e.length;t++)e[t]()}function Bo(){var e,t,n=new Promise((r,a)=>{e=r,t=a});return{promise:n,resolve:e,reject:t}}function bu(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const r of e)if(n.push(r),n.length===t)break;return n}const oe=2,Mn=4,fr=8,ea=1<<24,Ze=16,Ne=32,St=64,ta=128,qe=512,te=1024,se=2048,Fe=4096,me=8192,Je=16384,kt=32768,st=65536,dr=1<<17,Go=1<<18,Wt=1<<19,wu=1<<20,ze=1<<25,it=65536,na=1<<21,hr=1<<22,lt=1<<23,ut=Symbol("$state"),Vo=Symbol("legacy props"),qu=Symbol(""),Ho=Symbol("proxy path"),At=new class extends Error{constructor(){super(...arguments);Ke(this,"name","StaleReactionError");Ke(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}},Wo=!!((ci=globalThis.document)!=null&&ci.contentType)&&globalThis.document.contentType.includes("xml");function jo(e){if(g){const t=new Error(`lifecycle_outside_component
\`${e}(...)\` can only be used during component initialisation
https://svelte.dev/e/lifecycle_outside_component`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/lifecycle_outside_component")}function Mu(){if(g){const e=new Error("async_derived_orphan\nCannot create a `$derived(...)` with an `await` expression outside of an effect tree\nhttps://svelte.dev/e/async_derived_orphan");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/async_derived_orphan")}function Su(){if(g){const e=new Error(`derived_references_self
A derived value cannot reference itself recursively
https://svelte.dev/e/derived_references_self`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/derived_references_self")}function Uo(e,t,n){if(g){const r=new Error(`each_key_duplicate
${n?`Keyed each block has duplicate key \`${n}\` at indexes ${e} and ${t}`:`Keyed each block has duplicate key at indexes ${e} and ${t}`}
https://svelte.dev/e/each_key_duplicate`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_duplicate")}function ku(e,t,n){if(g){const r=new Error(`each_key_volatile
Keyed each block has key that is not idempotent — the key for item at index ${e} was \`${t}\` but is now \`${n}\`. Keys must be the same each time for a given item
https://svelte.dev/e/each_key_volatile`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_volatile")}function Au(e){if(g){const t=new Error(`effect_in_teardown
\`${e}\` cannot be used inside an effect cleanup function
https://svelte.dev/e/effect_in_teardown`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_in_teardown")}function Eu(){if(g){const e=new Error("effect_in_unowned_derived\nEffect cannot be created inside a `$derived` value that was not itself created inside an effect\nhttps://svelte.dev/e/effect_in_unowned_derived");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Pu(e){if(g){const t=new Error(`effect_orphan
\`${e}\` can only be used inside an effect (e.g. during component initialisation)
https://svelte.dev/e/effect_orphan`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_orphan")}function Nu(){if(g){const e=new Error(`effect_update_depth_exceeded
Maximum update depth exceeded. This typically indicates that an effect reads and writes the same piece of state
https://svelte.dev/e/effect_update_depth_exceeded`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Fu(){if(g){const e=new Error("invalid_snippet\nCould not `{@render}` snippet due to the expression being `null` or `undefined`. Consider using optional chaining `{@render snippet?.()}`\nhttps://svelte.dev/e/invalid_snippet");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/invalid_snippet")}function Cu(e){if(g){const t=new Error(`props_invalid_value
Cannot do \`bind:${e}={undefined}\` when \`${e}\` has a fallback value
https://svelte.dev/e/props_invalid_value`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_invalid_value")}function Ru(e){if(g){const t=new Error(`props_rest_readonly
Rest element properties of \`$props()\` such as \`${e}\` are readonly
https://svelte.dev/e/props_rest_readonly`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_rest_readonly")}function xu(e){if(g){const t=new Error(`rune_outside_svelte
The \`${e}\` rune is only available inside \`.svelte\` and \`.svelte.js/ts\` files
https://svelte.dev/e/rune_outside_svelte`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/rune_outside_svelte")}function Tu(){if(g){const e=new Error("state_descriptors_fixed\nProperty descriptors defined on `$state` objects must contain `value` and always be `enumerable`, `configurable` and `writable`.\nhttps://svelte.dev/e/state_descriptors_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function Du(){if(g){const e=new Error("state_prototype_fixed\nCannot set prototype of `$state` object\nhttps://svelte.dev/e/state_prototype_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Ou(){if(g){const e=new Error("state_unsafe_mutation\nUpdating state inside `$derived(...)`, `$inspect(...)` or a template expression is forbidden. If the value should not be reactive, declare it without `$state`\nhttps://svelte.dev/e/state_unsafe_mutation");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Lu(){if(g){const e=new Error("svelte_boundary_reset_onerror\nA `<svelte:boundary>` `reset` function cannot be called while an error is still being handled\nhttps://svelte.dev/e/svelte_boundary_reset_onerror");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const $u=1,Iu=2,Ko=4,Bu=8,Gu=16,Vu=1,Hu=4,Wu=8,ju=16,Uu=1,Ku=2,ne=Symbol(),Xu=Symbol("filename"),Xo="http://www.w3.org/1999/xhtml",Yu="http://www.w3.org/2000/svg",Qu="@attach";var Sn="font-weight: bold",kn="font-weight: normal";function Zu(){g?console.warn(`%c[svelte] lifecycle_double_unmount
%cTried to unmount a component that was not mounted
https://svelte.dev/e/lifecycle_double_unmount`,Sn,kn):console.warn("https://svelte.dev/e/lifecycle_double_unmount")}function Ju(){g?console.warn("%c[svelte] select_multiple_invalid_value\n%cThe `value` property of a `<select multiple>` element should be an array, but it received a non-array value. The selection will be kept as is.\nhttps://svelte.dev/e/select_multiple_invalid_value",Sn,kn):console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function ra(e){g?console.warn(`%c[svelte] state_proxy_equality_mismatch
%cReactive \`$state(...)\` proxies and the values they proxy have different identities. Because of this, comparisons with \`${e}\` will produce unexpected results
https://svelte.dev/e/state_proxy_equality_mismatch`,Sn,kn):console.warn("https://svelte.dev/e/state_proxy_equality_mismatch")}function zu(){g?console.warn(`%c[svelte] state_proxy_unmount
%cTried to unmount a state proxy, rather than a component
https://svelte.dev/e/state_proxy_unmount`,Sn,kn):console.warn("https://svelte.dev/e/state_proxy_unmount")}function ec(){g?console.warn("%c[svelte] svelte_boundary_reset_noop\n%cA `<svelte:boundary>` `reset` function only resets the boundary the first time it is called\nhttps://svelte.dev/e/svelte_boundary_reset_noop",Sn,kn):console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Yo(e){return e===this.v}function tc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Qo(e){return!tc(e,this.v)}let nc=!1;function Be(e,t){return e.label=t,Zo(e.v,t),e}function Zo(e,t){var n;return(n=e==null?void 0:e[Ho])==null||n.call(e,t),e}function rc(e){const t=new Error,n=ac();return n.length===0?null:(n.unshift(`
`),Mt(t,"stack",{value:n.join(`
`)}),Mt(t,"name",{value:e}),t)}function ac(){const e=Error.stackTraceLimit;Error.stackTraceLimit=1/0;const t=new Error().stack;if(Error.stackTraceLimit=e,!t)return[];const n=t.split(`
`),r=[];for(let a=0;a<n.length;a++){const o=n[a],s=o.replaceAll("\\","/");if(o.trim()!=="Error"){if(o.includes("validate_each_keys"))return[];s.includes("svelte/src/internal")||s.includes("node_modules/.vite")||r.push(o)}}return r}let W=null;function jt(e){W=e}let Ut=null;function pr(e){Ut=e}let An=null;function Jo(e){An=e}function oc(e){return sc("getContext").get(e)}function I(e,t=!1,n){W={p:W,i:!1,c:null,e:null,s:e,x:null,l:null},g&&(W.function=n,An=n)}function B(e){var t=W,n=t.e;if(n!==null){t.e=null;for(var r of n)ws(r)}return t.i=!0,W=t.p,g&&(An=(W==null?void 0:W.function)??null),{}}function zo(){return!0}function sc(e){return W===null&&jo(e),W.c??(W.c=new Map(ic(W)||void 0))}function ic(e){let t=e.p;for(;t!==null;){const n=t.c;if(n!==null)return n;t=t.p}return null}let Kt=[];function lc(){var e=Kt;Kt=[],yu(e)}function et(e){if(Kt.length===0){var t=Kt;queueMicrotask(()=>{t===Kt&&lc()})}Kt.push(e)}const aa=new WeakMap;function es(e){var t=x;if(t===null)return C.f|=lt,e;if(g&&e instanceof Error&&!aa.has(e)&&aa.set(e,uc(e,t)),(t.f&kt)===0&&(t.f&Mn)===0)throw g&&!t.parent&&e instanceof Error&&ts(e),e;ct(e,t)}function ct(e,t){for(;t!==null;){if((t.f&ta)!==0){if((t.f&kt)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw g&&e instanceof Error&&ts(e),e}function uc(e,t){var s,i,l;const n=Qe(e,"message");if(!(n&&!n.configurable)){for(var r=ha?"  ":"	",a=`
${r}in ${((s=t.fn)==null?void 0:s.name)||"<unknown>"}`,o=t.ctx;o!==null;)a+=`
${r}in ${(i=o.function)==null?void 0:i[Xu].split("/").pop()}`,o=o.p;return{message:e.message+`
${a}
`,stack:(l=e.stack)==null?void 0:l.split(`
`).filter(c=>!c.includes("svelte/src/internal")).join(`
`)}}}function ts(e){const t=aa.get(e);t&&(Mt(e,"message",{value:t.message}),Mt(e,"stack",{value:t.stack}))}const cc=-7169;function Q(e,t){e.f=e.f&cc|t}function oa(e){(e.f&qe)!==0||e.deps===null?Q(e,te):Q(e,Fe)}function ns(e){if(e!==null)for(const t of e)(t.f&oe)===0||(t.f&it)===0||(t.f^=it,ns(t.deps))}function rs(e,t,n){(e.f&se)!==0?t.add(e):(e.f&Fe)!==0&&n.add(e),ns(e.deps),Q(e,te)}const _r=new Set;let D=null,ie=null,Me=[],sa=null,ia=!1;const Da=class Da{constructor(){R(this,ge);Ke(this,"current",new Map);Ke(this,"previous",new Map);R(this,rn,new Set);R(this,an,new Set);R(this,xt,0);R(this,on,0);R(this,In,null);R(this,Bn,new Set);R(this,Tt,new Set);R(this,nt,new Map);Ke(this,"is_fork",!1);R(this,sn,!1)}skip_effect(t){d(this,nt).has(t)||d(this,nt).set(t,{d:[],m:[]})}unskip_effect(t){var n=d(this,nt).get(t);if(n){d(this,nt).delete(t);for(var r of n.d)Q(r,se),Re(r);for(r of n.m)Q(r,Fe),Re(r)}}process(t){var a;Me=[],this.apply();var n=[],r=[];for(const o of t)ae(this,ge,Ga).call(this,o,n,r);if(ae(this,ge,Ba).call(this)){ae(this,ge,Va).call(this,r),ae(this,ge,Va).call(this,n);for(const[o,s]of d(this,nt))is(o,s)}else{for(const o of d(this,rn))o();d(this,rn).clear(),d(this,xt)===0&&ae(this,ge,Ci).call(this),D=null,as(r),as(n),(a=d(this,In))==null||a.resolve()}ie=null}capture(t,n){n!==ne&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&lt)===0&&(this.current.set(t,t.v),ie==null||ie.set(t,t.v))}activate(){D=this,this.apply()}deactivate(){D===this&&(D=null,ie=null)}flush(){if(this.activate(),Me.length>0){if(fc(),D!==null&&D!==this)return}else d(this,xt)===0&&this.process([]);this.deactivate()}discard(){for(const t of d(this,an))t(this);d(this,an).clear()}increment(t){F(this,xt,d(this,xt)+1),t&&F(this,on,d(this,on)+1)}decrement(t){F(this,xt,d(this,xt)-1),t&&F(this,on,d(this,on)-1),!d(this,sn)&&(F(this,sn,!0),et(()=>{F(this,sn,!1),ae(this,ge,Ba).call(this)?Me.length>0&&this.flush():this.revive()}))}revive(){for(const t of d(this,Bn))d(this,Tt).delete(t),Q(t,se),Re(t);for(const t of d(this,Tt))Q(t,Fe),Re(t);this.flush()}oncommit(t){d(this,rn).add(t)}ondiscard(t){d(this,an).add(t)}settled(){return(d(this,In)??F(this,In,Bo())).promise}static ensure(){if(D===null){const t=D=new Da;_r.add(D),et(()=>{D===t&&t.flush()})}return D}apply(){}};rn=new WeakMap,an=new WeakMap,xt=new WeakMap,on=new WeakMap,In=new WeakMap,Bn=new WeakMap,Tt=new WeakMap,nt=new WeakMap,sn=new WeakMap,ge=new WeakSet,Ba=function(){return this.is_fork||d(this,on)>0},Ga=function(t,n,r){t.f^=te;for(var a=t.first;a!==null;){var o=a.f,s=(o&(Ne|St))!==0,i=s&&(o&te)!==0,l=i||(o&me)!==0||d(this,nt).has(a);if(!l&&a.fn!==null){s?a.f^=te:(o&Mn)!==0?n.push(a):Cn(a)&&((o&Ze)!==0&&d(this,Tt).add(a),zt(a));var c=a.first;if(c!==null){a=c;continue}}for(;a!==null;){var f=a.next;if(f!==null){a=f;break}a=a.parent}}},Va=function(t){for(var n=0;n<t.length;n+=1)rs(t[n],d(this,Bn),d(this,Tt))},Ci=function(){var a;if(_r.size>1){this.previous.clear();var t=ie,n=!0;for(const o of _r){if(o===this){n=!1;continue}const s=[];for(const[l,c]of this.current){if(o.current.has(l))if(n&&c!==o.current.get(l))o.current.set(l,c);else continue;s.push(l)}if(s.length===0)continue;const i=[...o.current.keys()].filter(l=>!this.current.has(l));if(i.length>0){var r=Me;Me=[];const l=new Set,c=new Map;for(const f of s)os(f,i,l,c);if(Me.length>0){D=o,o.apply();for(const f of Me)ae(a=o,ge,Ga).call(a,f,[],[]);o.deactivate()}Me=r}}D=null,ie=t}_r.delete(this)};let ft=Da;function fc(){ia=!0;var e=g?new Set:null;try{for(var t=0;Me.length>0;){var n=ft.ensure();if(t++>1e3){if(g){var r=new Map;for(const o of n.current.keys())for(const[s,i]of o.updated??[]){var a=r.get(s);a||(a={error:i.error,count:0},r.set(s,a)),a.count+=i.count}for(const o of r.values())o.error&&console.error(o.error)}dc()}if(n.process(Me),dt.clear(),g)for(const o of n.current.keys())e.add(o)}}finally{if(Me=[],ia=!1,sa=null,g)for(const o of e)o.updated=null}}function dc(){try{Nu()}catch(e){g&&Mt(e,"stack",{value:""}),ct(e,sa)}}let Ce=null;function as(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var r=e[n++];if((r.f&(Je|me))===0&&Cn(r)&&(Ce=new Set,zt(r),r.deps===null&&r.first===null&&r.nodes===null&&r.teardown===null&&r.ac===null&&ks(r),(Ce==null?void 0:Ce.size)>0)){dt.clear();for(const a of Ce){if((a.f&(Je|me))!==0)continue;const o=[a];let s=a.parent;for(;s!==null;)Ce.has(s)&&(Ce.delete(s),o.push(s)),s=s.parent;for(let i=o.length-1;i>=0;i--){const l=o[i];(l.f&(Je|me))===0&&zt(l)}}Ce.clear()}}Ce=null}}function os(e,t,n,r){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const a of e.reactions){const o=a.f;(o&oe)!==0?os(a,t,n,r):(o&(hr|Ze))!==0&&(o&se)===0&&ss(a,t,r)&&(Q(a,se),Re(a))}}function ss(e,t,n){const r=n.get(e);if(r!==void 0)return r;if(e.deps!==null)for(const a of e.deps){if(qt.call(t,a))return!0;if((a.f&oe)!==0&&ss(a,t,n))return n.set(a,!0),!0}return n.set(e,!1),!1}function Re(e){var t=sa=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(Mn|fr|ea))!==0&&(e.f&kt)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var r=t.f;if(ia&&t===x&&(r&Ze)!==0&&(r&Go)===0&&(r&kt)!==0)return;if((r&(St|Ne))!==0){if((r&te)===0)return;t.f^=te}}Me.push(t)}function is(e,t){if(!((e.f&Ne)!==0&&(e.f&te)!==0)){(e.f&se)!==0?t.d.push(e):(e.f&Fe)!==0&&t.m.push(e),Q(e,te);for(var n=e.first;n!==null;)is(n,t),n=n.next}}function hc(e){let t=0,n=Et(0),r;return g&&Be(n,"createSubscriber version"),()=>{_a()&&(P(n),$c(()=>(t===0&&(r=ba(()=>e(()=>En(n)))),t+=1,()=>{et(()=>{t-=1,t===0&&(r==null||r(),r=void 0,En(n))})})))}}var pc=st|Wt;function _c(e,t,n,r){new mc(e,t,n,r)}class mc{constructor(t,n,r,a){R(this,ee);Ke(this,"parent");Ke(this,"is_pending",!1);Ke(this,"transform_error");R(this,Ee);R(this,Oa,null);R(this,Ve);R(this,Dt);R(this,_e);R(this,He,null);R(this,ye,null);R(this,Oe,null);R(this,rt,null);R(this,Ot,0);R(this,vt,0);R(this,ln,!1);R(this,un,new Set);R(this,cn,new Set);R(this,We,null);R(this,wr,hc(()=>(F(this,We,Et(d(this,Ot))),g&&Be(d(this,We),"$effect.pending()"),()=>{F(this,We,null)})));var o;F(this,Ee,t),F(this,Ve,n),F(this,Dt,s=>{var i=x;i.b=this,i.f|=ta,r(s)}),this.parent=x.b,this.transform_error=a??((o=this.parent)==null?void 0:o.transform_error)??(s=>s),F(this,_e,Fn(()=>{ae(this,ee,Ha).call(this)},pc))}defer_effect(t){rs(t,d(this,un),d(this,cn))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!d(this,Ve).pending}update_pending_count(t){ae(this,ee,Wa).call(this,t),F(this,Ot,d(this,Ot)+t),!(!d(this,We)||d(this,ln))&&(F(this,ln,!0),et(()=>{F(this,ln,!1),d(this,We)&&Yt(d(this,We),d(this,Ot))}))}get_effect_pending(){return d(this,wr).call(this),P(d(this,We))}error(t){var n=d(this,Ve).onerror;let r=d(this,Ve).failed;if(!n&&!r)throw t;d(this,He)&&(le(d(this,He)),F(this,He,null)),d(this,ye)&&(le(d(this,ye)),F(this,ye,null)),d(this,Oe)&&(le(d(this,Oe)),F(this,Oe,null));var a=!1,o=!1;const s=()=>{if(a){ec();return}a=!0,o&&Lu(),d(this,Oe)!==null&&Nt(d(this,Oe),()=>{F(this,Oe,null)}),ae(this,ee,Rr).call(this,()=>{ft.ensure(),ae(this,ee,Ha).call(this)})},i=l=>{try{o=!0,n==null||n(l,s),o=!1}catch(c){ct(c,d(this,_e)&&d(this,_e).parent)}r&&F(this,Oe,ae(this,ee,Rr).call(this,()=>{ft.ensure();try{return he(()=>{var c=x;c.b=this,c.f|=ta,r(d(this,Ee),()=>l,()=>s)})}catch(c){return ct(c,d(this,_e).parent),null}}))};et(()=>{var l;try{l=this.transform_error(t)}catch(c){ct(c,d(this,_e)&&d(this,_e).parent);return}l!==null&&typeof l=="object"&&typeof l.then=="function"?l.then(i,c=>ct(c,d(this,_e)&&d(this,_e).parent)):i(l)})}}Ee=new WeakMap,Oa=new WeakMap,Ve=new WeakMap,Dt=new WeakMap,_e=new WeakMap,He=new WeakMap,ye=new WeakMap,Oe=new WeakMap,rt=new WeakMap,Ot=new WeakMap,vt=new WeakMap,ln=new WeakMap,un=new WeakMap,cn=new WeakMap,We=new WeakMap,wr=new WeakMap,ee=new WeakSet,Jd=function(){try{F(this,He,he(()=>d(this,Dt).call(this,d(this,Ee))))}catch(t){this.error(t)}},zd=function(t){const n=d(this,Ve).failed;n&&F(this,Oe,he(()=>{n(d(this,Ee),()=>t,()=>()=>{})}))},eh=function(){const t=d(this,Ve).pending;t&&(this.is_pending=!0,F(this,ye,he(()=>t(d(this,Ee)))),et(()=>{var n=F(this,rt,document.createDocumentFragment()),r=tt();n.append(r),F(this,He,ae(this,ee,Rr).call(this,()=>(ft.ensure(),he(()=>d(this,Dt).call(this,r))))),d(this,vt)===0&&(d(this,Ee).before(n),F(this,rt,null),Nt(d(this,ye),()=>{F(this,ye,null)}),ae(this,ee,Cr).call(this))}))},Ha=function(){try{if(this.is_pending=this.has_pending_snippet(),F(this,vt,0),F(this,Ot,0),F(this,He,he(()=>{d(this,Dt).call(this,d(this,Ee))})),d(this,vt)>0){var t=F(this,rt,document.createDocumentFragment());Ps(d(this,He),t);const n=d(this,Ve).pending;F(this,ye,he(()=>n(d(this,Ee))))}else ae(this,ee,Cr).call(this)}catch(n){this.error(n)}},Cr=function(){this.is_pending=!1;for(const t of d(this,un))Q(t,se),Re(t);for(const t of d(this,cn))Q(t,Fe),Re(t);d(this,un).clear(),d(this,cn).clear()},Rr=function(t){var n=x,r=C,a=W;Te(d(this,_e)),Se(d(this,_e)),jt(d(this,_e).ctx);try{return t()}catch(o){return es(o),null}finally{Te(n),Se(r),jt(a)}},Wa=function(t){var n;if(!this.has_pending_snippet()){this.parent&&ae(n=this.parent,ee,Wa).call(n,t);return}F(this,vt,d(this,vt)+t),d(this,vt)===0&&(ae(this,ee,Cr).call(this),d(this,ye)&&Nt(d(this,ye),()=>{F(this,ye,null)}),d(this,rt)&&(d(this,Ee).before(d(this,rt)),F(this,rt,null)))};function ls(e,t,n,r){const a=mr;var o=e.filter(u=>!u.settled);if(n.length===0&&o.length===0){r(t.map(a));return}var s=x,i=vc(),l=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(u=>u.promise)):null;function c(u){i();try{r(u)}catch(h){(s.f&Je)===0&&ct(h,s)}la()}if(n.length===0){l.then(()=>c(t.map(a)));return}function f(){i(),Promise.all(n.map(u=>bc(u))).then(u=>c([...t.map(a),...u])).catch(u=>ct(u,s))}l?l.then(f):f()}function vc(){var e=x,t=C,n=W,r=D;if(g)var a=Ut;return function(s=!0){Te(e),Se(t),jt(n),s&&(r==null||r.activate()),g&&pr(a)}}function la(e=!0){Te(null),Se(null),jt(null),e&&(D==null||D.deactivate()),g&&pr(null)}function gc(){var e=x.b,t=D,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}const yc=new Set;function mr(e){var t=oe|se,n=C!==null&&(C.f&oe)!==0?C:null;return x!==null&&(x.f|=Wt),{ctx:W,deps:null,effects:null,equals:Yo,f:t,fn:e,reactions:null,rv:0,v:ne,wv:0,parent:n??x,ac:null}}function bc(e,t,n){x===null&&Mu();var a=void 0,o=Et(ne);g&&(o.label=t);var s=!C,i=new Map;return Lc(()=>{var h;var l=Bo();a=l.promise;try{Promise.resolve(e()).then(l.resolve,l.reject).finally(la)}catch(m){l.reject(m),la()}var c=D;if(s){var f=gc();(h=i.get(c))==null||h.reject(At),i.delete(c),i.set(c,l)}const u=(m,_=void 0)=>{if(c.activate(),_)_!==At&&(o.f|=lt,Yt(o,_));else{(o.f&lt)!==0&&(o.f^=lt),Yt(o,m);for(const[w,p]of i){if(i.delete(w),w===c)break;p.reject(At)}}f&&f()};l.promise.then(u,m=>u(null,m||"unknown"))}),ma(()=>{for(const l of i.values())l.reject(At)}),g&&(o.f|=hr),new Promise(l=>{function c(f){function u(){f===a?l(o):c(a)}f.then(u,u)}c(a)})}function ua(e){const t=mr(e);return Fs(t),t}function us(e){const t=mr(e);return t.equals=Qo,t}function cs(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)le(t[n])}}let ca=[];function wc(e){for(var t=e.parent;t!==null;){if((t.f&oe)===0)return(t.f&Je)===0?t:null;t=t.parent}return null}function fa(e){var t,n=x;if(Te(wc(e)),g){let r=Xt;hs(new Set);try{qt.call(ca,e)&&Su(),ca.push(e),e.f&=~it,cs(e),t=ya(e)}finally{Te(n),hs(r),ca.pop()}}else try{e.f&=~it,cs(e),t=ya(e)}finally{Te(n)}return t}function fs(e){var t=fa(e);if(!e.equals(t)&&(e.wv=xs(),(!(D!=null&&D.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){Q(e,te);return}_t||(ie!==null?(_a()||D!=null&&D.is_fork)&&ie.set(e,t):oa(e))}function qc(e){var t,n;if(e.effects!==null)for(const r of e.effects)(r.teardown||r.ac)&&((t=r.teardown)==null||t.call(r),(n=r.ac)==null||n.abort(At),r.teardown=V,r.ac=null,Rn(r,0),va(r))}function ds(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&zt(t)}let Xt=new Set;const dt=new Map;function hs(e){Xt=e}let da=!1;function Mc(){da=!0}function Et(e,t){var n={f:0,v:e,reactions:null,equals:Yo,rv:0,wv:0};return n}function ht(e,t){const n=Et(e);return Fs(n),n}function Sc(e,t=!1,n=!0){const r=Et(e);return t||(r.equals=Qo),r}function pt(e,t,n=!1){C!==null&&(!xe||(C.f&dr)!==0)&&zo()&&(C.f&(oe|Ze|hr|dr))!==0&&(ke===null||!qt.call(ke,e))&&Ou();let r=n?Qt(t):t;return g&&Zo(r,e.label),Yt(e,r)}function Yt(e,t){var a;if(!e.equals(t)){var n=e.v;_t?dt.set(e,t):dt.set(e,n),e.v=t;var r=ft.ensure();if(r.capture(e,n),g){if(x!==null){e.updated??(e.updated=new Map);const o=(((a=e.updated.get(""))==null?void 0:a.count)??0)+1;if(e.updated.set("",{error:null,count:o}),o>5){const s=rc("updated at");if(s!==null){let i=e.updated.get(s.stack);i||(i={error:s,count:0},e.updated.set(s.stack,i)),i.count++}}}x!==null&&(e.set_during_effect=!0)}if((e.f&oe)!==0){const o=e;(e.f&se)!==0&&fa(o),oa(o)}e.wv=xs(),_s(e,se),x!==null&&(x.f&te)!==0&&(x.f&(Ne|St))===0&&(Ae===null?Gc([e]):Ae.push(e)),!r.is_fork&&Xt.size>0&&!da&&ps()}return t}function ps(){da=!1;for(const e of Xt)(e.f&te)!==0&&Q(e,Fe),Cn(e)&&zt(e);Xt.clear()}function En(e){pt(e,e.v+1)}function _s(e,t){var n=e.reactions;if(n!==null)for(var r=n.length,a=0;a<r;a++){var o=n[a],s=o.f;if(g&&(s&dr)!==0){Xt.add(o);continue}var i=(s&se)===0;if(i&&Q(o,t),(s&oe)!==0){var l=o;ie==null||ie.delete(l),(s&it)===0&&(s&qe&&(o.f|=it),_s(l,Fe))}else i&&((s&Ze)!==0&&Ce!==null&&Ce.add(o),Re(o))}}const kc=/^[a-zA-Z_$][a-zA-Z_$0-9]*$/;function Qt(e){if(typeof e!="object"||e===null||ut in e)return e;const t=$o(e);if(t!==vu&&t!==gu)return e;var n=new Map,r=zr(e),a=ht(0),o=Ct,s=f=>{if(Ct===o)return f();var u=C,h=Ct;Se(null),Rs(o);var m=f();return Se(u),Rs(h),m};r&&(n.set("length",ht(e.length)),g&&(e=Pc(e)));var i="";let l=!1;function c(f){if(!l){l=!0,i=f,Be(a,`${i} version`);for(const[u,h]of n)Be(h,Pt(i,u));l=!1}}return new Proxy(e,{defineProperty(f,u,h){(!("value"in h)||h.configurable===!1||h.enumerable===!1||h.writable===!1)&&Tu();var m=n.get(u);return m===void 0?s(()=>{var _=ht(h.value);return n.set(u,_),g&&typeof u=="string"&&Be(_,Pt(i,u)),_}):pt(m,h.value,!0),!0},deleteProperty(f,u){var h=n.get(u);if(h===void 0){if(u in f){const m=s(()=>ht(ne));n.set(u,m),En(a),g&&Be(m,Pt(i,u))}}else pt(h,ne),En(a);return!0},get(f,u,h){var p;if(u===ut)return e;if(g&&u===Ho)return c;var m=n.get(u),_=u in f;if(m===void 0&&(!_||(p=Qe(f,u))!=null&&p.writable)&&(m=s(()=>{var v=Qt(_?f[u]:ne),A=ht(v);return g&&Be(A,Pt(i,u)),A}),n.set(u,m)),m!==void 0){var w=P(m);return w===ne?void 0:w}return Reflect.get(f,u,h)},getOwnPropertyDescriptor(f,u){var h=Reflect.getOwnPropertyDescriptor(f,u);if(h&&"value"in h){var m=n.get(u);m&&(h.value=P(m))}else if(h===void 0){var _=n.get(u),w=_==null?void 0:_.v;if(_!==void 0&&w!==ne)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return h},has(f,u){var w;if(u===ut)return!0;var h=n.get(u),m=h!==void 0&&h.v!==ne||Reflect.has(f,u);if(h!==void 0||x!==null&&(!m||(w=Qe(f,u))!=null&&w.writable)){h===void 0&&(h=s(()=>{var p=m?Qt(f[u]):ne,v=ht(p);return g&&Be(v,Pt(i,u)),v}),n.set(u,h));var _=P(h);if(_===ne)return!1}return m},set(f,u,h,m){var Y;var _=n.get(u),w=u in f;if(r&&u==="length")for(var p=h;p<_.v;p+=1){var v=n.get(p+"");v!==void 0?pt(v,ne):p in f&&(v=s(()=>ht(ne)),n.set(p+"",v),g&&Be(v,Pt(i,p)))}if(_===void 0)(!w||(Y=Qe(f,u))!=null&&Y.writable)&&(_=s(()=>ht(void 0)),g&&Be(_,Pt(i,u)),pt(_,Qt(h)),n.set(u,_));else{w=_.v!==ne;var A=s(()=>Qt(h));pt(_,A)}var b=Reflect.getOwnPropertyDescriptor(f,u);if(b!=null&&b.set&&b.set.call(m,h),!w){if(r&&typeof u=="string"){var S=n.get("length"),E=Number(u);Number.isInteger(E)&&E>=S.v&&pt(S,E+1)}En(a)}return!0},ownKeys(f){P(a);var u=Reflect.ownKeys(f).filter(_=>{var w=n.get(_);return w===void 0||w.v!==ne});for(var[h,m]of n)m.v!==ne&&!(h in f)&&u.push(h);return u},setPrototypeOf(){Du()}})}function Pt(e,t){return typeof t=="symbol"?`${e}[Symbol(${t.description??""})]`:kc.test(t)?`${e}.${t}`:/^\d+$/.test(t)?`${e}[${t}]`:`${e}['${t}']`}function Pn(e){try{if(e!==null&&typeof e=="object"&&ut in e)return e[ut]}catch{}return e}function Ac(e,t){return Object.is(Pn(e),Pn(t))}const Ec=new Set(["copyWithin","fill","pop","push","reverse","shift","sort","splice","unshift"]);function Pc(e){return new Proxy(e,{get(t,n,r){var a=Reflect.get(t,n,r);return Ec.has(n)?function(...o){Mc();var s=a.apply(this,o);return ps(),s}:a}})}function Nc(){const e=Array.prototype,t=Array.__svelte_cleanup;t&&t();const{indexOf:n,lastIndexOf:r,includes:a}=e;e.indexOf=function(o,s){const i=n.call(this,o,s);if(i===-1){for(let l=s??0;l<this.length;l+=1)if(Pn(this[l])===o){ra("array.indexOf(...)");break}}return i},e.lastIndexOf=function(o,s){const i=r.call(this,o,s??this.length-1);if(i===-1){for(let l=0;l<=(s??this.length-1);l+=1)if(Pn(this[l])===o){ra("array.lastIndexOf(...)");break}}return i},e.includes=function(o,s){const i=a.call(this,o,s);if(!i){for(let l=0;l<this.length;l+=1)if(Pn(this[l])===o){ra("array.includes(...)");break}}return i},Array.__svelte_cleanup=()=>{e.indexOf=n,e.lastIndexOf=r,e.includes=a}}var ms,ha,vs,gs;function Fc(){if(ms===void 0){ms=window,ha=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;vs=Qe(t,"firstChild").get,gs=Qe(t,"nextSibling").get,Io(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Io(n)&&(n.__t=void 0),g&&(e.__svelte_meta=null,Nc())}}function tt(e=""){return document.createTextNode(e)}function Zt(e){return vs.call(e)}function Nn(e){return gs.call(e)}function k(e,t){return Zt(e)}function H(e,t=!1){{var n=Zt(e);return n instanceof Comment&&n.data===""?Nn(n):n}}function N(e,t=1,n=!1){let r=e;for(;t--;)r=Nn(r);return r}function Cc(e){e.textContent=""}function ys(){return!1}function bs(e,t,n){return document.createElementNS(t??Xo,e,void 0)}function Rc(e,t){if(t){const n=document.body;e.autofocus=!0,et(()=>{document.activeElement===n&&e.focus()})}}function pa(e){var t=C,n=x;Se(null),Te(null);try{return e()}finally{Se(t),Te(n)}}function xc(e){x===null&&(C===null&&Pu(e),Eu()),_t&&Au(e)}function Tc(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function Ge(e,t,n){var r=x;if(g)for(;r!==null&&(r.f&dr)!==0;)r=r.parent;r!==null&&(r.f&me)!==0&&(e|=me);var a={ctx:W,deps:null,nodes:null,f:e|se|qe,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null};if(g&&(a.component_function=An),n)try{zt(a)}catch(i){throw le(a),i}else t!==null&&Re(a);var o=a;if(n&&o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&Wt)===0&&(o=o.first,(e&Ze)!==0&&(e&st)!==0&&o!==null&&(o.f|=st)),o!==null&&(o.parent=r,r!==null&&Tc(o,r),C!==null&&(C.f&oe)!==0&&(e&St)===0)){var s=C;(s.effects??(s.effects=[])).push(o)}return a}function _a(){return C!==null&&!xe}function ma(e){const t=Ge(fr,null,!1);return Q(t,te),t.teardown=e,t}function Dc(e){xc("$effect"),g&&Mt(e,"name",{value:"$effect"});var t=x.f,n=!C&&(t&Ne)!==0&&(t&kt)===0;if(n){var r=W;(r.e??(r.e=[])).push(e)}else return ws(e)}function ws(e){return Ge(Mn|wu,e,!1)}function Oc(e){ft.ensure();const t=Ge(St|Wt,e,!0);return(n={})=>new Promise(r=>{n.outro?Nt(t,()=>{le(t),r(void 0)}):(le(t),r(void 0))})}function qs(e){return Ge(Mn,e,!1)}function Lc(e){return Ge(hr|Wt,e,!0)}function $c(e,t=0){return Ge(fr|t,e,!0)}function Jt(e,t=[],n=[],r=[]){ls(r,t,n,a=>{Ge(fr,()=>e(...a.map(P)),!0)})}function Fn(e,t=0){var n=Ge(Ze|t,e,!0);return g&&(n.dev_stack=Ut),n}function Ms(e,t=0){var n=Ge(ea|t,e,!0);return g&&(n.dev_stack=Ut),n}function he(e){return Ge(Ne|Wt,e,!0)}function Ss(e){var t=e.teardown;if(t!==null){const n=_t,r=C;Ns(!0),Se(null);try{t.call(null)}finally{Ns(n),Se(r)}}}function va(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const a=n.ac;a!==null&&pa(()=>{a.abort(At)});var r=n.next;(n.f&St)!==0?n.parent=null:le(n,t),n=r}}function Ic(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&Ne)===0&&le(t),t=n}}function le(e,t=!0){var n=!1;(t||(e.f&Go)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(Bc(e.nodes.start,e.nodes.end),n=!0),va(e,t&&!n),Rn(e,0),Q(e,Je);var r=e.nodes&&e.nodes.t;if(r!==null)for(const o of r)o.stop();Ss(e);var a=e.parent;a!==null&&a.first!==null&&ks(e),g&&(e.component_function=null),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function Bc(e,t){for(;e!==null;){var n=e===t?null:Nn(e);e.remove(),e=n}}function ks(e){var t=e.parent,n=e.prev,r=e.next;n!==null&&(n.next=r),r!==null&&(r.prev=n),t!==null&&(t.first===e&&(t.first=r),t.last===e&&(t.last=n))}function Nt(e,t,n=!0){var r=[];As(e,r,!0);var a=()=>{n&&le(e),t&&t()},o=r.length;if(o>0){var s=()=>--o||a();for(var i of r)i.out(s)}else a()}function As(e,t,n){if((e.f&me)===0){e.f^=me;var r=e.nodes&&e.nodes.t;if(r!==null)for(const i of r)(i.is_global||n)&&t.push(i);for(var a=e.first;a!==null;){var o=a.next,s=(a.f&st)!==0||(a.f&Ne)!==0&&(e.f&Ze)!==0;As(a,t,s?n:!1),a=o}}}function ga(e){Es(e,!0)}function Es(e,t){if((e.f&me)!==0){e.f^=me,(e.f&te)===0&&(Q(e,se),Re(e));for(var n=e.first;n!==null;){var r=n.next,a=(n.f&st)!==0||(n.f&Ne)!==0;Es(n,a?t:!1),n=r}var o=e.nodes&&e.nodes.t;if(o!==null)for(const s of o)(s.is_global||t)&&s.in()}}function Ps(e,t){if(e.nodes)for(var n=e.nodes.start,r=e.nodes.end;n!==null;){var a=n===r?null:Nn(n);t.append(n),n=a}}let vr=!1,_t=!1;function Ns(e){_t=e}let C=null,xe=!1;function Se(e){C=e}let x=null;function Te(e){x=e}let ke=null;function Fs(e){C!==null&&(ke===null?ke=[e]:ke.push(e))}let pe=null,ve=0,Ae=null;function Gc(e){Ae=e}let Cs=1,Ft=0,Ct=Ft;function Rs(e){Ct=e}function xs(){return++Cs}function Cn(e){var t=e.f;if((t&se)!==0)return!0;if(t&oe&&(e.f&=~it),(t&Fe)!==0){for(var n=e.deps,r=n.length,a=0;a<r;a++){var o=n[a];if(Cn(o)&&fs(o),o.wv>e.wv)return!0}(t&qe)!==0&&ie===null&&Q(e,te)}return!1}function Ts(e,t,n=!0){var r=e.reactions;if(r!==null&&!(ke!==null&&qt.call(ke,e)))for(var a=0;a<r.length;a++){var o=r[a];(o.f&oe)!==0?Ts(o,t,!1):t===o&&(n?Q(o,se):(o.f&te)!==0&&Q(o,Fe),Re(o))}}function ya(e){var w;var t=pe,n=ve,r=Ae,a=C,o=ke,s=W,i=xe,l=Ct,c=e.f;pe=null,ve=0,Ae=null,C=(c&(Ne|St))===0?e:null,ke=null,jt(e.ctx),xe=!1,Ct=++Ft,e.ac!==null&&(pa(()=>{e.ac.abort(At)}),e.ac=null);try{e.f|=na;var f=e.fn,u=f();e.f|=kt;var h=e.deps,m=D==null?void 0:D.is_fork;if(pe!==null){var _;if(m||Rn(e,ve),h!==null&&ve>0)for(h.length=ve+pe.length,_=0;_<pe.length;_++)h[ve+_]=pe[_];else e.deps=h=pe;if(_a()&&(e.f&qe)!==0)for(_=ve;_<h.length;_++)((w=h[_]).reactions??(w.reactions=[])).push(e)}else!m&&h!==null&&ve<h.length&&(Rn(e,ve),h.length=ve);if(zo()&&Ae!==null&&!xe&&h!==null&&(e.f&(oe|Fe|se))===0)for(_=0;_<Ae.length;_++)Ts(Ae[_],e);if(a!==null&&a!==e){if(Ft++,a.deps!==null)for(let p=0;p<n;p+=1)a.deps[p].rv=Ft;if(t!==null)for(const p of t)p.rv=Ft;Ae!==null&&(r===null?r=Ae:r.push(...Ae))}return(e.f&lt)!==0&&(e.f^=lt),u}catch(p){return es(p)}finally{e.f^=na,pe=t,ve=n,Ae=r,C=a,ke=o,jt(s),xe=i,Ct=l}}function Vc(e,t){let n=t.reactions;if(n!==null){var r=_u.call(n,e);if(r!==-1){var a=n.length-1;a===0?n=t.reactions=null:(n[r]=n[a],n.pop())}}if(n===null&&(t.f&oe)!==0&&(pe===null||!qt.call(pe,t))){var o=t;(o.f&qe)!==0&&(o.f^=qe,o.f&=~it),oa(o),qc(o),Rn(o,0)}}function Rn(e,t){var n=e.deps;if(n!==null)for(var r=t;r<n.length;r++)Vc(e,n[r])}function zt(e){var t=e.f;if((t&Je)===0){Q(e,te);var n=x,r=vr;if(x=e,vr=!0,g){var a=An;Jo(e.component_function);var o=Ut;pr(e.dev_stack??Ut)}try{(t&(Ze|ea))!==0?Ic(e):va(e),Ss(e);var s=ya(e);e.teardown=typeof s=="function"?s:null,e.wv=Cs;var i;g&&nc&&(e.f&se)!==0&&e.deps}finally{vr=r,x=n,g&&(Jo(a),pr(o))}}}function P(e){var t=e.f,n=(t&oe)!==0;if(C!==null&&!xe){var r=x!==null&&(x.f&Je)!==0;if(!r&&(ke===null||!qt.call(ke,e))){var a=C.deps;if((C.f&na)!==0)e.rv<Ft&&(e.rv=Ft,pe===null&&a!==null&&a[ve]===e?ve++:pe===null?pe=[e]:pe.push(e));else{(C.deps??(C.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[C]:qt.call(o,C)||o.push(C)}}}if(g&&yc.delete(e),_t&&dt.has(e))return dt.get(e);if(n){var s=e;if(_t){var i=s.v;return((s.f&te)===0&&s.reactions!==null||Os(s))&&(i=fa(s)),dt.set(s,i),i}var l=(s.f&qe)===0&&!xe&&C!==null&&(vr||(C.f&qe)!==0),c=(s.f&kt)===0;Cn(s)&&(l&&(s.f|=qe),fs(s)),l&&!c&&(ds(s),Ds(s))}if(ie!=null&&ie.has(e))return ie.get(e);if((e.f&lt)!==0)throw e.v;return e.v}function Ds(e){if(e.f|=qe,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&oe)!==0&&(t.f&qe)===0&&(ds(t),Ds(t))}function Os(e){if(e.v===ne)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(dt.has(t)||(t.f&oe)!==0&&Os(t))return!0;return!1}function ba(e){var t=xe;try{return xe=!0,e()}finally{xe=t}}function Hc(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const Wc=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function jc(e){return Wc.includes(e)}const Uc={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Kc(e){return e=e.toLowerCase(),Uc[e]??e}const Xc=["touchstart","touchmove"];function Yc(e){return Xc.includes(e)}const Rt=Symbol("events"),Ls=new Set,wa=new Set;function Qc(e,t,n,r={}){function a(o){if(r.capture||qa.call(t,o),!o.cancelBubble)return pa(()=>n==null?void 0:n.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?et(()=>{t.addEventListener(e,a,r)}):t.addEventListener(e,a,r),a}function De(e,t,n){(t[Rt]??(t[Rt]={}))[e]=n}function $s(e){for(var t=0;t<e.length;t++)Ls.add(e[t]);for(var n of wa)n(e)}let Is=null;function qa(e){var p,v;var t=this,n=t.ownerDocument,r=e.type,a=((p=e.composedPath)==null?void 0:p.call(e))||[],o=a[0]||e.target;Is=e;var s=0,i=Is===e&&e[Rt];if(i){var l=a.indexOf(i);if(l!==-1&&(t===document||t===window)){e[Rt]=t;return}var c=a.indexOf(t);if(c===-1)return;l<=c&&(s=l)}if(o=a[s]||e.target,o!==t){Mt(e,"currentTarget",{configurable:!0,get(){return o||n}});var f=C,u=x;Se(null),Te(null);try{for(var h,m=[];o!==null;){var _=o.assignedSlot||o.parentNode||o.host||null;try{var w=(v=o[Rt])==null?void 0:v[r];w!=null&&(!o.disabled||e.target===o)&&w.call(o,e)}catch(A){h?m.push(A):h=A}if(e.cancelBubble||_===t||_===null)break;o=_}if(h){for(let A of m)queueMicrotask(()=>{throw A});throw h}}finally{e[Rt]=t,delete e.currentTarget,Se(f),Te(u)}}}const Ma=((fi=globalThis==null?void 0:globalThis.window)==null?void 0:fi.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function Zc(e){return(Ma==null?void 0:Ma.createHTML(e))??e}function Bs(e){var t=bs("template");return t.innerHTML=Zc(e.replaceAll("<!>","<!---->")),t.content}function xn(e,t){var n=x;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function en(e,t){var n=(t&Uu)!==0,r=(t&Ku)!==0,a,o=!e.startsWith("<!>");return()=>{a===void 0&&(a=Bs(o?e:"<!>"+e),n||(a=Zt(a)));var s=r||ha?document.importNode(a,!0):a.cloneNode(!0);if(n){var i=Zt(s),l=s.lastChild;xn(i,l)}else xn(s,s);return s}}function Jc(e,t,n="svg"){var r=!e.startsWith("<!>"),a=`<${n}>${r?e:"<!>"+e}</${n}>`,o;return()=>{if(!o){var s=Bs(a),i=Zt(s);o=Zt(i)}var l=o.cloneNode(!0);return xn(l,l),l}}function zc(e,t){return Jc(e,t,"svg")}function j(){var e=document.createDocumentFragment(),t=document.createComment(""),n=tt();return e.append(t,n),xn(t,n),e}function O(e,t){e!==null&&e.before(t)}function Gs(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function ef(e,t){return tf(e,t)}const gr=new Map;function tf(e,{target:t,anchor:n,props:r={},events:a,context:o,intro:s=!0,transformError:i}){Fc();var l=void 0,c=Oc(()=>{var f=n??t.appendChild(tt());_c(f,{pending:()=>{}},m=>{I({});var _=W;o&&(_.c=o),a&&(r.$$events=a),l=e(m,r)||{},B()},i);var u=new Set,h=m=>{for(var _=0;_<m.length;_++){var w=m[_];if(!u.has(w)){u.add(w);var p=Yc(w);for(const b of[t,document]){var v=gr.get(b);v===void 0&&(v=new Map,gr.set(b,v));var A=v.get(w);A===void 0?(b.addEventListener(w,qa,{passive:p}),v.set(w,1)):v.set(w,A+1)}}}};return h(cr(Ls)),wa.add(h),()=>{var p;for(var m of u)for(const v of[t,document]){var _=gr.get(v),w=_.get(m);--w==0?(v.removeEventListener(m,qa),_.delete(m),_.size===0&&gr.delete(v)):_.set(m,w)}wa.delete(h),f!==n&&((p=f.parentNode)==null||p.removeChild(f))}});return Sa.set(l,c),l}let Sa=new WeakMap;function Vs(e,t){const n=Sa.get(e);return n?(Sa.delete(e),n(t)):(g&&(ut in e?zu():Zu()),Promise.resolve())}class ka{constructor(t,n=!0){Ke(this,"anchor");R(this,Le,new Map);R(this,je,new Map);R(this,be,new Map);R(this,Lt,new Set);R(this,Gn,!0);R(this,Vn,()=>{var t=D;if(d(this,Le).has(t)){var n=d(this,Le).get(t),r=d(this,je).get(n);if(r)ga(r),d(this,Lt).delete(n);else{var a=d(this,be).get(n);a&&(d(this,je).set(n,a.effect),d(this,be).delete(n),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),r=a.effect)}for(const[o,s]of d(this,Le)){if(d(this,Le).delete(o),o===t)break;const i=d(this,be).get(s);i&&(le(i.effect),d(this,be).delete(s))}for(const[o,s]of d(this,je)){if(o===n||d(this,Lt).has(o))continue;const i=()=>{if(Array.from(d(this,Le).values()).includes(o)){var c=document.createDocumentFragment();Ps(s,c),c.append(tt()),d(this,be).set(o,{effect:s,fragment:c})}else le(s);d(this,Lt).delete(o),d(this,je).delete(o)};d(this,Gn)||!r?(d(this,Lt).add(o),Nt(s,i,!1)):i()}}});R(this,qr,t=>{d(this,Le).delete(t);const n=Array.from(d(this,Le).values());for(const[r,a]of d(this,be))n.includes(r)||(le(a.effect),d(this,be).delete(r))});this.anchor=t,F(this,Gn,n)}ensure(t,n){var r=D,a=ys();if(n&&!d(this,je).has(t)&&!d(this,be).has(t))if(a){var o=document.createDocumentFragment(),s=tt();o.append(s),d(this,be).set(t,{effect:he(()=>n(s)),fragment:o})}else d(this,je).set(t,he(()=>n(this.anchor)));if(d(this,Le).set(r,t),a){for(const[i,l]of d(this,je))i===t?r.unskip_effect(l):r.skip_effect(l);for(const[i,l]of d(this,be))i===t?r.unskip_effect(l.effect):r.skip_effect(l.effect);r.oncommit(d(this,Vn)),r.ondiscard(d(this,qr))}else d(this,Vn).call(this)}}Le=new WeakMap,je=new WeakMap,be=new WeakMap,Lt=new WeakMap,Gn=new WeakMap,Vn=new WeakMap,qr=new WeakMap;function yr(e,t,n=!1){var r=new ka(e),a=n?st:0;function o(s,i){r.ensure(s,i)}Fn(()=>{var s=!1;t((i,l=0)=>{s=!0,o(l,i)}),s||o(!1,null)},a)}function nf(e,t){return t}function rf(e,t,n){for(var r=[],a=t.length,o,s=t.length,i=0;i<a;i++){let u=t[i];Nt(u,()=>{if(o){if(o.pending.delete(u),o.done.add(u),o.pending.size===0){var h=e.outrogroups;Aa(cr(o.done)),h.delete(o),h.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var l=r.length===0&&n!==null;if(l){var c=n,f=c.parentNode;Cc(f),f.append(c),e.items.clear()}Aa(t,!l)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function Aa(e,t=!0){for(var n=0;n<e.length;n++)le(e[n],t)}var Hs;function Ea(e,t,n,r,a,o=null){var s=e,i=new Map,l=(t&Ko)!==0;if(l){var c=e;s=c.appendChild(tt())}var f=null,u=us(()=>{var v=n();return zr(v)?v:v==null?[]:cr(v)}),h,m=!0;function _(){p.fallback=f,af(p,h,s,t,r),f!==null&&(h.length===0?(f.f&ze)===0?ga(f):(f.f^=ze,Dn(f,null,s)):Nt(f,()=>{f=null}))}var w=Fn(()=>{h=P(u);for(var v=h.length,A=new Set,b=D,S=ys(),E=0;E<v;E+=1){var Y=h[E],T=r(Y,E);if(g){var we=r(Y,E);T!==we&&ku(String(E),String(T),String(we))}var ue=m?null:i.get(T);ue?(ue.v&&Yt(ue.v,Y),ue.i&&Yt(ue.i,E),S&&b.unskip_effect(ue.e)):(ue=of(i,m?s:Hs??(Hs=tt()),Y,T,E,a,t,n),m||(ue.e.f|=ze),i.set(T,ue)),A.add(T)}if(v===0&&o&&!f&&(m?f=he(()=>o(s)):(f=he(()=>o(Hs??(Hs=tt()))),f.f|=ze)),v>A.size&&(g?sf(h,r):Uo("","","")),!m)if(S){for(const[gt,y]of i)A.has(gt)||b.skip_effect(y.e);b.oncommit(_),b.ondiscard(()=>{})}else _();P(u)}),p={effect:w,items:i,outrogroups:null,fallback:f};m=!1}function Tn(e){for(;e!==null&&(e.f&Ne)===0;)e=e.next;return e}function af(e,t,n,r,a){var gt,y,Mr,Sr,Hn,kr,Ar,Wn,Er;var o=(r&Bu)!==0,s=t.length,i=e.items,l=Tn(e.effect.first),c,f=null,u,h=[],m=[],_,w,p,v;if(o)for(v=0;v<s;v+=1)_=t[v],w=a(_,v),p=i.get(w).e,(p.f&ze)===0&&((y=(gt=p.nodes)==null?void 0:gt.a)==null||y.measure(),(u??(u=new Set)).add(p));for(v=0;v<s;v+=1){if(_=t[v],w=a(_,v),p=i.get(w).e,e.outrogroups!==null)for(const $e of e.outrogroups)$e.pending.delete(p),$e.done.delete(p);if((p.f&ze)!==0)if(p.f^=ze,p===l)Dn(p,null,n);else{var A=f?f.next:l;p===e.effect.last&&(e.effect.last=p.prev),p.prev&&(p.prev.next=p.next),p.next&&(p.next.prev=p.prev),mt(e,f,p),mt(e,p,A),Dn(p,A,n),f=p,h=[],m=[],l=Tn(f.next);continue}if((p.f&me)!==0&&(ga(p),o&&((Sr=(Mr=p.nodes)==null?void 0:Mr.a)==null||Sr.unfix(),(u??(u=new Set)).delete(p))),p!==l){if(c!==void 0&&c.has(p)){if(h.length<m.length){var b=m[0],S;f=b.prev;var E=h[0],Y=h[h.length-1];for(S=0;S<h.length;S+=1)Dn(h[S],b,n);for(S=0;S<m.length;S+=1)c.delete(m[S]);mt(e,E.prev,Y.next),mt(e,f,E),mt(e,Y,b),l=b,f=Y,v-=1,h=[],m=[]}else c.delete(p),Dn(p,l,n),mt(e,p.prev,p.next),mt(e,p,f===null?e.effect.first:f.next),mt(e,f,p),f=p;continue}for(h=[],m=[];l!==null&&l!==p;)(c??(c=new Set)).add(l),m.push(l),l=Tn(l.next);if(l===null)continue}(p.f&ze)===0&&h.push(p),f=p,l=Tn(p.next)}if(e.outrogroups!==null){for(const $e of e.outrogroups)$e.pending.size===0&&(Aa(cr($e.done)),(Hn=e.outrogroups)==null||Hn.delete($e));e.outrogroups.size===0&&(e.outrogroups=null)}if(l!==null||c!==void 0){var T=[];if(c!==void 0)for(p of c)(p.f&me)===0&&T.push(p);for(;l!==null;)(l.f&me)===0&&l!==e.fallback&&T.push(l),l=Tn(l.next);var we=T.length;if(we>0){var ue=(r&Ko)!==0&&s===0?n:null;if(o){for(v=0;v<we;v+=1)(Ar=(kr=T[v].nodes)==null?void 0:kr.a)==null||Ar.measure();for(v=0;v<we;v+=1)(Er=(Wn=T[v].nodes)==null?void 0:Wn.a)==null||Er.fix()}rf(e,T,ue)}}o&&et(()=>{var $e,jn;if(u!==void 0)for(p of u)(jn=($e=p.nodes)==null?void 0:$e.a)==null||jn.apply()})}function of(e,t,n,r,a,o,s,i){var l=(s&$u)!==0?(s&Gu)===0?Sc(n,!1,!1):Et(n):null,c=(s&Iu)!==0?Et(a):null;return g&&l&&(l.trace=()=>{i()[(c==null?void 0:c.v)??a]}),{v:l,i:c,e:he(()=>(o(t,l??n,c??a,i),()=>{e.delete(r)}))}}function Dn(e,t,n){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end,o=t&&(t.f&ze)===0?t.nodes.start:n;r!==null;){var s=Nn(r);if(o.before(r),r===a)return;r=s}}function mt(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function sf(e,t){const n=new Map,r=e.length;for(let a=0;a<r;a++){const o=t(e[a],a);if(n.has(o)){const s=String(n.get(o)),i=String(a);let l=String(o);l.startsWith("[object ")&&(l=null),Uo(s,i,l)}n.set(o,a)}}function U(e,t,...n){var r=new ka(e);Fn(()=>{const a=t()??null;g&&a==null&&Fu(),r.ensure(a,a&&(o=>a(o,...n)))},st)}function lf(e,t,n,r,a,o){var s=null,i=e,l=new ka(i,!1);Fn(()=>{const c=t()||null;var f=Yu;if(c===null){l.ensure(null,null);return}return l.ensure(c,u=>{if(c){if(s=bs(c,f),xn(s,s),r){var h=s.appendChild(tt());r(s,h)}x.nodes.end=s,u.before(s)}}),()=>{}},st),ma(()=>{})}function uf(e,t){var n=void 0,r;Ms(()=>{n!==(n=t())&&(r&&(le(r),r=null),n&&(r=he(()=>{qs(()=>n(e))})))})}function Ws(e){var t,n,r="";if(typeof e=="string"||typeof e=="number")r+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(n=Ws(e[t]))&&(r&&(r+=" "),r+=n)}else for(n in e)e[n]&&(r&&(r+=" "),r+=n);return r}function cf(){for(var e,t,n=0,r="",a=arguments.length;n<a;n++)(e=arguments[n])&&(t=Ws(e))&&(r&&(r+=" "),r+=t);return r}function js(e){return typeof e=="object"?cf(e):e??""}const Us=[...` 	
\r\f \v\uFEFF`];function ff(e,t,n){var r=e==null?"":""+e;if(t&&(r=r?r+" "+t:t),n){for(var a of Object.keys(n))if(n[a])r=r?r+" "+a:a;else if(r.length)for(var o=a.length,s=0;(s=r.indexOf(a,s))>=0;){var i=s+o;(s===0||Us.includes(r[s-1]))&&(i===r.length||Us.includes(r[i]))?r=(s===0?"":r.substring(0,s))+r.substring(i+1):s=i}}return r===""?null:r}function Ks(e,t=!1){var n=t?" !important;":";",r="";for(var a of Object.keys(e)){var o=e[a];o!=null&&o!==""&&(r+=" "+a+": "+o+n)}return r}function Pa(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function df(e,t){if(t){var n="",r,a;if(Array.isArray(t)?(r=t[0],a=t[1]):r=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,s=0,i=!1,l=[];r&&l.push(...Object.keys(r).map(Pa)),a&&l.push(...Object.keys(a).map(Pa));var c=0,f=-1;const w=e.length;for(var u=0;u<w;u++){var h=e[u];if(i?h==="/"&&e[u-1]==="*"&&(i=!1):o?o===h&&(o=!1):h==="/"&&e[u+1]==="*"?i=!0:h==='"'||h==="'"?o=h:h==="("?s++:h===")"&&s--,!i&&o===!1&&s===0){if(h===":"&&f===-1)f=u;else if(h===";"||u===w-1){if(f!==-1){var m=Pa(e.substring(c,f).trim());if(!l.includes(m)){h!==";"&&u++;var _=e.substring(c,u).trim();n+=" "+_+";"}}c=u+1,f=-1}}}}return r&&(n+=Ks(r)),a&&(n+=Ks(a,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function Na(e,t,n,r,a,o){var s=e.__className;if(s!==n||s===void 0){var i=ff(n,r,o);i==null?e.removeAttribute("class"):t?e.className=i:e.setAttribute("class",i),e.__className=n}else if(o&&a!==o)for(var l in o){var c=!!o[l];(a==null||c!==!!a[l])&&e.classList.toggle(l,c)}return o}function Fa(e,t={},n,r){for(var a in n){var o=n[a];t[a]!==o&&(n[a]==null?e.style.removeProperty(a):e.style.setProperty(a,o,r))}}function hf(e,t,n,r){var a=e.__style;if(a!==t){var o=df(t,r);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else r&&(Array.isArray(r)?(Fa(e,n==null?void 0:n[0],r[0]),Fa(e,n==null?void 0:n[1],r[1],"important")):Fa(e,n,r));return r}function Ca(e,t,n=!1){if(e.multiple){if(t==null)return;if(!zr(t))return Ju();for(var r of e.options)r.selected=t.includes(Xs(r));return}for(r of e.options){var a=Xs(r);if(Ac(a,t)){r.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function pf(e){var t=new MutationObserver(()=>{Ca(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),ma(()=>{t.disconnect()})}function Xs(e){return"__value"in e?e.__value:e.value}const On=Symbol("class"),Ln=Symbol("style"),Ys=Symbol("is custom element"),Qs=Symbol("is html"),_f=Wo?"option":"OPTION",mf=Wo?"select":"SELECT";function vf(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function M(e,t,n,r){var a=Js(e);a[t]!==(a[t]=n)&&(t==="loading"&&(e[qu]=n),n==null?e.removeAttribute(t):typeof n!="string"&&ei(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function gf(e,t,n,r,a=!1,o=!1){var s=Js(e),i=s[Ys],l=!s[Qs],c=t||{},f=e.nodeName===_f;for(var u in t)u in n||(n[u]=null);n.class?n.class=js(n.class):n[On]&&(n.class=null),n[Ln]&&(n.style??(n.style=null));var h=ei(e);for(const b in n){let S=n[b];if(f&&b==="value"&&S==null){e.value=e.__value="",c[b]=S;continue}if(b==="class"){var m=e.namespaceURI==="http://www.w3.org/1999/xhtml";Na(e,m,S,r,t==null?void 0:t[On],n[On]),c[b]=S,c[On]=n[On];continue}if(b==="style"){hf(e,S,t==null?void 0:t[Ln],n[Ln]),c[b]=S,c[Ln]=n[Ln];continue}var _=c[b];if(!(S===_&&!(S===void 0&&e.hasAttribute(b)))){c[b]=S;var w=b[0]+b[1];if(w!=="$$")if(w==="on"){const E={},Y="$$"+b;let T=b.slice(2);var p=jc(T);if(Hc(T)&&(T=T.slice(0,-7),E.capture=!0),!p&&_){if(S!=null)continue;e.removeEventListener(T,c[Y],E),c[Y]=null}if(p)De(T,e,S),$s([T]);else if(S!=null){let we=function(ue){c[b].call(this,ue)};c[Y]=Qc(T,e,we,E)}}else if(b==="style")M(e,b,S);else if(b==="autofocus")Rc(e,!!S);else if(!i&&(b==="__value"||b==="value"&&S!=null))e.value=e.__value=S;else if(b==="selected"&&f)vf(e,S);else{var v=b;l||(v=Kc(v));var A=v==="defaultValue"||v==="defaultChecked";if(S==null&&!i&&!A)if(s[b]=null,v==="value"||v==="checked"){let E=e;const Y=t===void 0;if(v==="value"){let T=E.defaultValue;E.removeAttribute(v),E.defaultValue=T,E.value=E.__value=Y?T:null}else{let T=E.defaultChecked;E.removeAttribute(v),E.defaultChecked=T,E.checked=Y?T:!1}}else e.removeAttribute(b);else A||h.includes(v)&&(i||typeof S!="string")?(e[v]=S,v in s&&(s[v]=ne)):typeof S!="function"&&M(e,v,S)}}}return c}function Zs(e,t,n=[],r=[],a=[],o,s=!1,i=!1){ls(a,n,r,l=>{var c=void 0,f={},u=e.nodeName===mf,h=!1;if(Ms(()=>{var _=t(...l.map(P)),w=gf(e,c,_,o,s,i);h&&u&&"value"in _&&Ca(e,_.value);for(let v of Object.getOwnPropertySymbols(f))_[v]||le(f[v]);for(let v of Object.getOwnPropertySymbols(_)){var p=_[v];v.description===Qu&&(!c||p!==c[v])&&(f[v]&&le(f[v]),f[v]=he(()=>uf(e,()=>p))),w[v]=p}c=w}),u){var m=e;qs(()=>{Ca(m,c.value,!0),pf(m)})}h=!0})}function Js(e){return e.__attributes??(e.__attributes={[Ys]:e.nodeName.includes("-"),[Qs]:e.namespaceURI===Xo})}var zs=new Map;function ei(e){var t=e.getAttribute("is")||e.nodeName,n=zs.get(t);if(n)return n;zs.set(t,n=[]);for(var r,a=e,o=Element.prototype;o!==a;){r=mu(a);for(var s in r)r[s].set&&n.push(s);a=$o(a)}return n}let br=!1;function yf(e){var t=br;try{return br=!1,[e(),br]}finally{br=t}}const bf={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return g&&Ru(`${e.name}.${String(t)}`),!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function K(e,t,n){return new Proxy(g?{props:e,exclude:t,name:n,other:{},to_proxy:[]}:{props:e,exclude:t},bf)}const wf={get(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(qn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r)return r[t]}},set(e,t,n){let r=e.props.length;for(;r--;){let a=e.props[r];qn(a)&&(a=a());const o=Qe(a,t);if(o&&o.set)return o.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(qn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r){const a=Qe(r,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===ut||t===Vo)return!1;for(let n of e.props)if(qn(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(qn(n)&&(n=n()),!!n){for(const r in n)t.includes(r)||t.push(r);for(const r of Object.getOwnPropertySymbols(n))t.includes(r)||t.push(r)}return t}};function Z(...e){return new Proxy({props:e},wf)}function tn(e,t,n,r){var A;var a=(n&Wu)!==0,o=(n&ju)!==0,s=r,i=!0,l=()=>(i&&(i=!1,s=o?ba(r):r),s),c;if(a){var f=ut in e||Vo in e;c=((A=Qe(e,t))==null?void 0:A.set)??(f&&t in e?b=>e[t]=b:void 0)}var u,h=!1;a?[u,h]=yf(()=>e[t]):u=e[t],u===void 0&&r!==void 0&&(u=l(),c&&(Cu(t),c(u)));var m;if(m=()=>{var b=e[t];return b===void 0?l():(i=!0,b)},(n&Hu)===0)return m;if(c){var _=e.$$legacy;return(function(b,S){return arguments.length>0?((!S||_||h)&&c(S?m():b),b):m()})}var w=!1,p=((n&Vu)!==0?mr:us)(()=>(w=!1,m()));g&&(p.label=t),a&&P(p);var v=x;return(function(b,S){if(arguments.length>0){const E=S?P(p):a?Qt(b):b;return pt(p,E),w=!0,s!==void 0&&(s=E),b}return _t&&w||(v.f&Je)!==0?p.v:P(p)})}if(g){let e=function(t){if(!(t in globalThis)){let n;Object.defineProperty(globalThis,t,{configurable:!0,get:()=>{if(n!==void 0)return n;xu(t)},set:r=>{n=r}})}};e("$state"),e("$effect"),e("$derived"),e("$inspect"),e("$props"),e("$bindable")}function qf(e){W===null&&jo("onMount"),Dc(()=>{const t=ba(e);if(typeof t=="function")return t})}const Mf="5";typeof window<"u"&&((di=window.__svelte??(window.__svelte={})).v??(di.v=new Set)).add(Mf);/**
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
 */const Sf={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const kf=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const Af=Symbol("lucide-context"),Ef=()=>oc(Af);var Pf=zc("<svg><!><!></svg>");function J(e,t){I(t,!0);const n=Ef()??{},r=tn(t,"color",19,()=>n.color??"currentColor"),a=tn(t,"size",19,()=>n.size??24),o=tn(t,"strokeWidth",19,()=>n.strokeWidth??2),s=tn(t,"absoluteStrokeWidth",19,()=>n.absoluteStrokeWidth??!1),i=tn(t,"iconNode",19,()=>[]),l=K(t,["$$slots","$$events","$$legacy","name","color","size","strokeWidth","absoluteStrokeWidth","iconNode","children"]),c=ua(()=>s()?Number(o())*24/Number(a()):o());var f=Pf();Zs(f,m=>({...Sf,...m,...l,width:a(),height:a(),stroke:r(),"stroke-width":P(c),class:["lucide-icon lucide",n.class,t.name&&`lucide-${t.name}`,t.class]}),[()=>!t.children&&!kf(l)&&{"aria-hidden":"true"}]);var u=k(f);Ea(u,17,i,nf,(m,_)=>{var w=ua(()=>bu(P(_),2));let p=()=>P(w)[0],v=()=>P(w)[1];var A=j(),b=H(A);lf(b,p,!0,(S,E)=>{Zs(S,()=>({...v()}))}),O(m,A)});var h=N(u);U(h,()=>t.children??V),O(e,f),B()}function Nf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];J(e,Z({name:"chart-line"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Ff(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 9 6 6 6-6"}]];J(e,Z({name:"chevron-down"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Cf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"}],["path",{d:"M12 17h.01"}]];J(e,Z({name:"circle-question-mark"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Rf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 12 18z"}],["path",{d:"M2 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 2 18z"}]];J(e,Z({name:"fast-forward"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function xf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"}]];J(e,Z({name:"folder-open"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Tf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["rect",{x:"14",y:"3",width:"5",height:"18",rx:"1"}],["rect",{x:"5",y:"3",width:"5",height:"18",rx:"1"}]];J(e,Z({name:"pause"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Df(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"}]];J(e,Z({name:"play"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Of(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m15 14 5-5-5-5"}],["path",{d:"M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13"}]];J(e,Z({name:"redo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Lf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];J(e,Z({name:"refresh-cw"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function $f(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m2 9 3-3 3 3"}],["path",{d:"M13 18H7a2 2 0 0 1-2-2V6"}],["path",{d:"m22 15-3 3-3-3"}],["path",{d:"M11 6h6a2 2 0 0 1 2 2v10"}]];J(e,Z({name:"repeat-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function If(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 12 18z"}],["path",{d:"M22 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 22 18z"}]];J(e,Z({name:"rewind"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Bf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M8.12 8.12 12 12"}],["path",{d:"M20 4 8.12 15.88"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M14.8 14.8 20 20"}]];J(e,Z({name:"scissors"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Gf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];J(e,Z({name:"settings"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Vf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];J(e,Z({name:"sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Hf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 2h4"}],["path",{d:"M12 14v-4"}],["path",{d:"M4 13a8 8 0 0 1 8-7 8 8 0 1 1-5.3 14L4 17.6"}],["path",{d:"M9 17H4v5"}]];J(e,Z({name:"timer-reset"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Wf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];J(e,Z({name:"trash-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function jf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9 14 4 9l5-5"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"}]];J(e,Z({name:"undo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Uf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}]];J(e,Z({name:"volume-1"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Kf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}],["path",{d:"M19.364 18.364a9 9 0 0 0 0-12.728"}]];J(e,Z({name:"volume-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Xf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["line",{x1:"22",x2:"16",y1:"9",y2:"15"}],["line",{x1:"16",x2:"22",y1:"9",y2:"15"}]];J(e,Z({name:"volume-x"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}function Yf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}]];J(e,Z({name:"waves"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=j(),i=H(s);U(i,()=>t.children??V),O(a,s)},$$slots:{default:!0}})),B()}var Qf=en('<span aria-hidden="true"><!></span>');function X(e,t){I(t,!0);const n=tn(t,"className",3,""),r=ua(()=>["aqe-button-icon",n()].filter(Boolean).join(" "));var a=Qf(),o=k(a);{var s=y=>{Nf(y,{size:14,strokeWidth:2})},i=y=>{Ff(y,{size:14,strokeWidth:2})},l=y=>{Cf(y,{size:14,strokeWidth:2})},c=y=>{Rf(y,{size:14,strokeWidth:2})},f=y=>{xf(y,{size:14,strokeWidth:2})},u=y=>{Tf(y,{size:14,strokeWidth:2})},h=y=>{Df(y,{size:14,strokeWidth:2})},m=y=>{Of(y,{size:14,strokeWidth:2})},_=y=>{Lf(y,{size:14,strokeWidth:2})},w=y=>{$f(y,{size:14,strokeWidth:2})},p=y=>{If(y,{size:14,strokeWidth:2})},v=y=>{Bf(y,{size:14,strokeWidth:2})},A=y=>{Gf(y,{size:14,strokeWidth:2})},b=y=>{Vf(y,{size:14,strokeWidth:2})},S=y=>{Hf(y,{size:14,strokeWidth:2})},E=y=>{Wf(y,{size:14,strokeWidth:2})},Y=y=>{jf(y,{size:14,strokeWidth:2})},T=y=>{Uf(y,{size:14,strokeWidth:2})},we=y=>{Kf(y,{size:14,strokeWidth:2})},ue=y=>{Xf(y,{size:14,strokeWidth:2})},gt=y=>{Yf(y,{size:14,strokeWidth:2})};yr(o,y=>{t.icon==="chart-line"?y(s):t.icon==="chevron-down"?y(i,1):t.icon==="circle-help"?y(l,2):t.icon==="fast-forward"?y(c,3):t.icon==="folder-open"?y(f,4):t.icon==="pause"?y(u,5):t.icon==="play"?y(h,6):t.icon==="redo-2"?y(m,7):t.icon==="refresh-cw"?y(_,8):t.icon==="repeat-2"?y(w,9):t.icon==="rewind"?y(p,10):t.icon==="scissors"?y(v,11):t.icon==="settings"?y(A,12):t.icon==="sparkles"?y(b,13):t.icon==="timer-reset"?y(S,14):t.icon==="trash-2"?y(E,15):t.icon==="undo-2"?y(Y,16):t.icon==="volume-1"?y(T,17):t.icon==="volume-2"?y(we,18):t.icon==="volume-x"?y(ue,19):t.icon==="waves"&&y(gt,20)})}Jt(()=>Na(a,1,js(P(r)))),O(e,a),B()}function ti(){return document.body.dataset.aqeBusy==="true"}function ni(e,t,n){if(ti())return;const r=L(n);if(!r)return;const a=_o(r,e);gn(r),a&&(typeof t.focus=="function"&&t.focus(),ot(r,{clearAudio:!0}),$i(a),window.__aqeActiveField=n,ce.info("region delete request queued",{ord:n,sourceFilename:a.sourceFilename,selectionStartMs:a.selectionStartMs,selectionEndMs:a.selectionEndMs,durationMs:a.durationMs,trigger:e,playbackActive:a.playbackActive}),Gt(n,!0,ja("aqe:delete-selection")),It(n,"aqe:delete-selection"))}function Zf(e,t){if(e.key!=="Backspace")return;const n=L(t);if(!(!n||document.activeElement!==n||ti())){if(!_o(n,"backspace")){gn(n);return}e.preventDefault(),ni("backspace",n,t)}}var Jf=en('<button type="button" class="aqe-button aqe-icon-only aqe-repeat-button" title="Repeat selected region, or the whole graph when no region is selected." aria-label="Repeat playback"><!> <span class="aqe-button-label">Repeat</span></button>'),zf=en('<button type="button" class="aqe-button aqe-menu-item" data-aqe-button-state="default" role="menuitem"><!> <span class="aqe-button-label"> </span></button>'),ed=en('<details class="aqe-menu"><summary class="aqe-button aqe-menu-summary" title="Denoise audio" aria-label="Denoise audio"><!> <span class="aqe-button-label">Denoise</span> <!></summary> <div class="aqe-menu-items" role="menu"></div></details>'),td=en('<button type="button"><!> <!> <span class="aqe-button-label"> </span></button> <!> <!>',1),nd=en('<div class="aqe-controls"><!> <button type="button" class="aqe-button aqe-delete-region-button" data-aqe-command="aqe:delete-selection" data-aqe-button-state="default" title="Delete selected region" aria-label="Delete selected region" hidden=""><!> <span class="aqe-button-label">Delete Region</span></button> <span class="aqe-status"></span> <details class="aqe-help"><summary class="aqe-help-summary" title="Show editor help"><!> <span>Help</span></summary> <div class="aqe-help-body"><section class="aqe-help-section"><h4 class="aqe-help-title">Graph and regions</h4> <ul class="aqe-help-list"><li><kbd>Shift</kbd>-drag on the graph to select a region.</li> <li>Play uses the selected region when one is active; Repeat loops the selected region, or the full graph otherwise.</li> <li>Delete Region removes only the selected region. Backspace does the same when the graph is focused.</li> <li>In the graph, grey is loudness and lines are pitch of the voice.</li></ul></section> <section class="aqe-help-section"><h4 class="aqe-help-title">Buttons</h4> <div class="aqe-help-grid"><span class="aqe-help-item"><span class="aqe-help-command"><!><span>Play</span></span> <span>Start or pause audio.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Graph</span></span> <span>Show pitch and loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Folder</span></span> <span>Open the current audio file.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>-L</span></span> <span>Trim 100 ms from the left.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>-R</span></span> <span>Trim 100 ms from the right.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Shorten Pauses</span></span> <span>Speed up long internal pauses.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Denoise</span></span> <span>Use Standard or RNNoise cleanup.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Slower</span></span> <span>Decrease speed.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Faster</span></span> <span>Increase speed.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Volume -</span></span> <span>Decrease loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Volume +</span></span> <span>Increase loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Undo</span></span> <span>Restore the previous edit.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Redo</span></span> <span>Restore the undone edit.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Delete Region</span></span> <span>Remove the selected graph region.</span></span></div></section> <p class="aqe-help-note">Every edit creates a new media file and updates the field to point at it. The original file remains in your media collection.</p></div></details> <div class="aqe-visualizer" data-anchor-ms="0" data-cursor-ms="0" data-progress-ms="0" data-graph-active="false" data-graph-busy="false" data-has-track="false" data-playback-state="stopped" data-playback-engine="" data-playback-start-ms="0" data-playback-end-ms="0" data-playback-region-mode="full" data-resume-requires-restart="false" data-selection-active="false" data-selection-start-ms="" data-selection-end-ms="" data-selection-draft-active="false" data-selection-draft-start-ms="" data-selection-draft-end-ms="" role="button" aria-label="Audio graph" tabindex="0" hidden=""><audio class="aqe-audio-clock" preload="metadata" hidden=""></audio> <svg class="aqe-visualizer-svg" preserveAspectRatio="xMinYMin meet" role="img" aria-label="Audio pitch and intensity visualization"><rect class="aqe-selection" width="0" visibility="hidden"></rect><path class="aqe-intensity" d=""></path><g class="aqe-pitch"></g><g class="aqe-labels"></g><g class="aqe-x-axis"></g><line class="aqe-selection-edge aqe-selection-start" visibility="hidden"></line><line class="aqe-selection-edge aqe-selection-end" visibility="hidden"></line><line class="aqe-cursor"></line></svg> <div class="aqe-visualizer-meta"><span class="aqe-spinner" hidden="" aria-hidden="true"></span> <span class="aqe-cursor-label">0 ms</span> <span class="aqe-visualizer-status"></span></div></div></div>');function rd(e,t){var Si;I(t,!0);const n=((Si=window.__AQE_EDITOR_CONFIG__)==null?void 0:Si.repeatPlaybackByDefault)===!0;function r(re){const Pr=re.currentTarget.ariaPressed!=="true";Xl(t.target.ord,Pr)}qf(()=>{const re=L(t.target.ord);re&&(Vl(re),Jl(re),Ul(re))});var a=nd(),o=k(a);Ea(o,17,()=>$,re=>re.command,(re,fe)=>{var Pr=td(),Ue=H(Pr);let ki;var Ai=k(Ue);X(Ai,{className:"aqe-button-icon-default",get icon(){return P(fe).icon}});var Ei=N(Ai,2);{var Bd=de=>{X(de,{className:"aqe-button-icon-active",get icon(){return P(fe).activeIcon}})};yr(Ei,de=>{P(fe).activeIcon&&de(Bd)})}var Gd=N(Ei,2),Vd=k(Gd),Pi=N(Ue,2);{var Hd=de=>{var Ie=Jf(),Nr=k(Ie);X(Nr,{icon:"repeat-2"}),Jt(()=>{M(Ie,"data-aqe-button-state",n?"active":"default"),M(Ie,"data-testid",`aqe-repeat-${t.target.ord}`),M(Ie,"aria-pressed",n?"true":"false")}),De("mousedown",Ie,Fr=>Fr.preventDefault()),De("click",Ie,r),O(de,Ie)};yr(Pi,de=>{P(fe).command==="aqe:play"&&de(Hd)})}var Wd=N(Pi,2);{var jd=de=>{var Ie=ed(),Nr=k(Ie),Fr=k(Nr);X(Fr,{icon:"sparkles"});var Ud=N(Fr,4);X(Ud,{className:"aqe-menu-chevron",icon:"chevron-down"});var Kd=N(Nr,2);Ea(Kd,21,()=>G,La=>La.command,(La,$t)=>{var yt=zf(),Ni=k(yt);X(Ni,{get icon(){return P($t).icon}});var Xd=N(Ni,2),Yd=k(Xd);Jt($a=>{M(yt,"data-aqe-command",P($t).command),M(yt,"data-testid",$a),M(yt,"title",P($t).title),M(yt,"aria-label",P($t).title),Gs(Yd,P($t).label)},[()=>xr(t.target.ord,P($t).command)]),De("mousedown",yt,$a=>$a.preventDefault()),De("click",yt,()=>So(P($t).command,t.target.node,t.target.ord)),O(La,yt)}),Jt(()=>M(Ie,"data-testid",`aqe-denoise-menu-${t.target.ord}`)),O(de,Ie)};yr(Wd,de=>{P(fe).command==="aqe:remove-pauses"&&de(jd)})}Jt(de=>{ki=Na(Ue,1,"aqe-button",null,ki,{"aqe-icon-only":P(fe).iconOnly===!0}),M(Ue,"data-aqe-command",P(fe).command),M(Ue,"data-aqe-button-state",P(fe).command==="aqe:play"?"play":P(fe).command==="aqe:analyze"?"graph":"default"),M(Ue,"data-testid",de),M(Ue,"title",P(fe).title),M(Ue,"aria-label",P(fe).title),Gs(Vd,P(fe).label)},[()=>xr(t.target.ord,P(fe).command)]),De("mousedown",Ue,de=>de.preventDefault()),De("click",Ue,()=>So(P(fe).command,t.target.node,t.target.ord)),O(re,Pr)});var s=N(o,2),i=k(s);X(i,{icon:"trash-2"});var l=N(s,2),c=N(l,2),f=k(c),u=k(f);X(u,{icon:"circle-help"});var h=N(f,2),m=N(k(h),2),_=N(k(m),2),w=k(_),p=k(w),v=k(p);X(v,{icon:"play"});var A=N(w,2),b=k(A),S=k(b);X(S,{icon:"chart-line"});var E=N(A,2),Y=k(E),T=k(Y);X(T,{icon:"folder-open"});var we=N(E,2),ue=k(we),gt=k(ue);X(gt,{icon:"scissors"});var y=N(we,2),Mr=k(y),Sr=k(Mr);X(Sr,{icon:"scissors"});var Hn=N(y,2),kr=k(Hn),Ar=k(kr);X(Ar,{icon:"timer-reset"});var Wn=N(Hn,2),Er=k(Wn),$e=k(Er);X($e,{icon:"sparkles"});var jn=N(Wn,2),Md=k(jn),Sd=k(Md);X(Sd,{icon:"rewind"});var hi=N(jn,2),kd=k(hi),Ad=k(kd);X(Ad,{icon:"fast-forward"});var pi=N(hi,2),Ed=k(pi),Pd=k(Ed);X(Pd,{icon:"volume-1"});var _i=N(pi,2),Nd=k(_i),Fd=k(Nd);X(Fd,{icon:"volume-2"});var mi=N(_i,2),Cd=k(mi),Rd=k(Cd);X(Rd,{icon:"undo-2"});var vi=N(mi,2),xd=k(vi),Td=k(xd);X(Td,{icon:"redo-2"});var Dd=N(vi,2),Od=k(Dd),Ld=k(Od);X(Ld,{icon:"trash-2"});var Un=N(c,2),gi=k(Un),Kn=N(gi,2),Xn=k(Kn),yi=N(Xn),bi=N(yi),wi=N(bi,2),fn=N(wi),dn=N(fn),Yn=N(dn),$d=N(Kn,2),qi=k($d),Mi=N(qi,2),Id=N(Mi,2);Jt(re=>{M(a,"data-aqe-field-ord",t.target.ord),M(a,"data-aqe-source-filename",t.target.sourceFilename),M(a,"data-testid",`aqe-controls-${t.target.ord}`),M(s,"data-testid",re),M(l,"data-testid",`aqe-status-${t.target.ord}`),M(c,"data-testid",`aqe-help-${t.target.ord}`),M(Un,"data-aqe-field-ord",t.target.ord),M(Un,"data-repeat-enabled",n?"true":"false"),M(Un,"data-testid",`aqe-graph-${t.target.ord}`),M(gi,"data-testid",`aqe-audio-clock-${t.target.ord}`),M(Kn,"data-testid",`aqe-graph-svg-${t.target.ord}`),M(Kn,"viewBox",`0 0 ${q.width} ${q.height}`),M(Xn,"data-testid",`aqe-selection-${t.target.ord}`),M(Xn,"x",q.left),M(Xn,"y",q.top),M(Xn,"height",q.height-q.top-q.bottom),M(yi,"data-testid",`aqe-intensity-${t.target.ord}`),M(bi,"data-testid",`aqe-pitch-${t.target.ord}`),M(wi,"data-testid",`aqe-x-axis-${t.target.ord}`),M(fn,"data-testid",`aqe-selection-start-${t.target.ord}`),M(fn,"x1",q.left),M(fn,"x2",q.left),M(fn,"y1",q.top),M(fn,"y2",q.height-q.bottom),M(dn,"data-testid",`aqe-selection-end-${t.target.ord}`),M(dn,"x1",q.left),M(dn,"x2",q.left),M(dn,"y1",q.top),M(dn,"y2",q.height-q.bottom),M(Yn,"data-testid",`aqe-cursor-${t.target.ord}`),M(Yn,"x1",q.left),M(Yn,"x2",q.left),M(Yn,"y1",q.top),M(Yn,"y2",q.height-q.bottom),M(qi,"data-testid",`aqe-graph-spinner-${t.target.ord}`),M(Mi,"data-testid",`aqe-progress-label-${t.target.ord}`),M(Id,"data-testid",`aqe-graph-status-${t.target.ord}`)},[()=>xr(t.target.ord,"aqe:delete-selection")]),De("mousedown",s,re=>re.preventDefault()),De("click",s,()=>ni("button",t.target.node,t.target.ord)),De("keydown",Un,re=>Zf(re,t.target.ord)),De("pointerdown",Kn,re=>nu(re,t.target.ord)),O(e,a),B()}$s(["mousedown","click","keydown","pointerdown"]);const nn=new Map;function ad(e){const t=nn.get(e.ord);if(t){if(document.body.contains(t.host)||ri(e,t.host),Ra(e.ord,t.host),!e.sourceFilename||t.sourceFilename===e.sourceFilename)return t;const o=L(e.ord);if((o==null?void 0:o.dataset.graphBusy)==="true"||(o==null?void 0:o.dataset.hasTrack)==="true"){const s=o.dataset.sourceFilename||e.sourceFilename;t.sourceFilename=s;const i=document.querySelector(`.aqe-controls[data-aqe-field-ord="${e.ord}"]`);return i&&(i.dataset.aqeSourceFilename=s),Ra(e.ord,t.host),t}}od(e.ord);const n=document.createElement("div");n.className="aqe-mount-host",ri(e,n);const a={component:ef(rd,{target:n,props:{target:e}}),host:n,ord:e.ord,sourceFilename:e.sourceFilename};return nn.set(e.ord,a),Ra(e.ord,n),a}function od(e){const t=nn.get(e);t&&(Vs(t.component),t.host.remove(),nn.delete(e)),document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>n.remove())}function sd(){for(const e of nn.values())Vs(e.component),e.host.remove();nn.clear(),id()}function ri(e,t){const n=e.node.closest(".field-container")||e.node.closest(".field")||e.node.parentElement||e.node;n.parentElement?n.after(t):e.node.after(t)}function Ra(e,t){document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>{t.contains(n)||n.remove()}),document.querySelectorAll(".aqe-mount-host").forEach(n=>{n!==t&&!n.querySelector(".aqe-controls")&&n.remove()})}function id(){document.querySelectorAll(".aqe-mount-host").forEach(e=>e.remove()),document.querySelectorAll(".aqe-controls").forEach(e=>e.remove())}function ld(){window.__aqeGraphStateForTest=dd,window.__aqeInstallAudioPlaybackTestDriverForTest=ud,window.__aqeSetCursorByClientXForTest=fd,window.__aqeSetCursorForTest=cd}function ud(e){const t=L(e),n=Pe(t);return!t||!n?!1:(n.__aqeTestDriverInstalled=!0,n.pause=function(){n.__aqeTestPlaying=!1,n.__aqeTestFrame&&(window.cancelAnimationFrame(n.__aqeTestFrame),n.__aqeTestFrame=null)},n.play=function(){n.__aqeTestPlaying=!0,n.__aqeTestLastNow=performance.now();const a=()=>{if(!n.__aqeTestPlaying)return;const o=performance.now(),s=Number(t.dataset.durationMs||"0")/1e3,i=Math.max(0,(o-Number(n.__aqeTestLastNow||o))/1e3);if(n.__aqeTestLastNow=o,n.currentTime=Math.min(s,(Number(n.currentTime)||0)+i),s&&n.currentTime>=s){n.__aqeTestPlaying=!1,n.dispatchEvent(new Event("ended"));return}n.__aqeTestFrame=window.requestAnimationFrame(a)};return n.__aqeTestFrame=window.requestAnimationFrame(a),Promise.resolve()},!0)}function cd(e,t,n){const r=L(e);return r?(r.hidden=!1,r.dataset.graphActive="true",wt(r,t,!!n),!0):!1}function fd(e,t,n){var i;const r=L(e),a=(r==null?void 0:r.querySelector(".aqe-visualizer-svg"))??null;if(!r||!a)return null;const o=Number(r.dataset.durationMs||"0"),s=mn({clientX:t},a,o);return wt(r,s,!!n),{cursorMs:Number(r.dataset.cursorMs||"0"),cursorX:Number(((i=r.querySelector(".aqe-cursor"))==null?void 0:i.getAttribute("x1"))||"0"),bounds:lo(a)}}function dd(e){var c,f,u,h,m;const t=L(e),n=Ka(e),r=Xa(e),a=((c=Xe(e))==null?void 0:c.querySelector(".aqe-delete-region-button"))??null;if(!t)return null;const o=Zn().flatMap(_=>Array.from(_.querySelectorAll(".aqe-button-icon svg"))),s=Pe(t),i=ko(t),l=Ao(t);return{active:t.dataset.graphActive==="true",busy:t.dataset.graphBusy==="true",hidden:!!t.hidden,hasTrack:t.dataset.hasTrack==="true",durationMs:Number(t.dataset.durationMs||"0"),anchorMs:Number(t.dataset.anchorMs||"0"),cursorMs:Number(t.dataset.cursorMs||"0"),progressMs:Number(t.dataset.progressMs||"0"),sourceFilename:t.dataset.sourceFilename||"",graphButtonLabel:ai(n),graphButtonState:(n==null?void 0:n.dataset.aqeButtonState)||"",playButtonLabel:ai(r),playButtonState:(r==null?void 0:r.dataset.aqeButtonState)||"",playbackState:hd(t),selectionActive:i!==null,selectionStartMs:(i==null?void 0:i.startMs)??null,selectionEndMs:(i==null?void 0:i.endMs)??null,selectionDraftActive:l!==null,selectionDraftStartMs:(l==null?void 0:l.startMs)??null,selectionDraftEndMs:(l==null?void 0:l.endMs)??null,repeatEnabled:t.dataset.repeatEnabled==="true",repeatControlDisabled:!!((f=Ya(e))!=null&&f.disabled),regionDeleteButtonDisabled:!!(a!=null&&a.disabled),regionDeleteButtonHidden:a?!!a.hidden:!0,playbackStartMs:Number(t.dataset.playbackStartMs||"0"),playbackEndMs:Number(t.dataset.playbackEndMs||"0"),playbackRegionMode:t.dataset.playbackRegionMode==="selection"?"selection":"full",resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true",audioClockSrc:s&&s.getAttribute("src")||"",audioClockCurrentMs:s?Math.round((Number(s.currentTime)||0)*1e3):0,audioClockReady:!!(s&&t.__aqeAudioClockAvailable),audioClockFallback:!!t.__aqeAudioClockFallback,audioClockMuted:!!(s&&s.muted),audioPlaybackTestDriver:!!(s&&s.__aqeTestDriverInstalled),playbackEngine:wn(t),progressClockMode:pd(t),xAxisLabels:Array.from(t.querySelectorAll(".aqe-x-label")).map(_=>_.textContent||""),pitchPaths:t.querySelectorAll(".aqe-pitch-path").length,intensity:((u=t.querySelector(".aqe-intensity"))==null?void 0:u.getAttribute("d"))||"",cursorX:Number(((h=t.querySelector(".aqe-cursor"))==null?void 0:h.getAttribute("x1"))||"0"),spinnerVisible:t.querySelector(".aqe-spinner")?!((m=t.querySelector(".aqe-spinner"))!=null&&m.hidden):!1,allButtonsDisabled:Zn().every(_=>_.disabled),anyButtonDisabled:Zn().some(_=>_.disabled),buttonIconCount:o.length,buttonIconStrokeValues:o.map(_=>_.getAttribute("stroke")||getComputedStyle(_).stroke||"")}}function hd(e){const t=e.dataset.playbackState;return $r(t)?t:"stopped"}function pd(e){const t=e.dataset.progressClockMode;return t==="audio"||t==="manual"||t==="stopped"?t:"stopped"}function ai(e){var t;return((t=e==null?void 0:e.querySelector(".aqe-button-label"))==null?void 0:t.textContent)||(e==null?void 0:e.textContent)||""}function _d(){window.__aqeSetBusy=Gt,window.__aqeSetStatus=Mo,window.__aqeSetVisualizer=au,window.__aqeSetVisualizerStatus=ou,window.__aqeResetGraphAfterEdit=ru,window.__aqeSetPlaybackState=cu,window.__aqeGetPlaybackRequest=fu,window.__aqeStopEditorPlayback=du,window.__aqeGetCursorMs=hu,window.__aqeGetCursorIntent=pu,window.__aqePrepareForNewNote=Co,window.__aqePopFrontendLog=Ti,window.__aqePopPendingGraphAnalysisRequest=Li,window.__aqePopPendingRegionDeleteRequest=Ii,ld()}const md=/\[sound:([^\]]+)\]/i,vd=/\.(aac|flac|m4a|mp3|oga|ogg|opus|wav|webm)$/i;let $n=[];function gd(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){oi(),window.__AQE_EDITOR_CONFIG__=e,_d(),Co(),Ji(),window.__aqeEditorDispose=oi,ce.info("editor runtime initialized",{audioFieldIndices:e.audioFieldIndices,showGraphByDefault:e.showGraphByDefault===!0});const t=()=>yd(e);window.__aqeScan=t,Ta(t,0),Ta(t,250),Ta(t,1e3)}function oi(){$n.forEach(e=>window.clearTimeout(e)),$n=[],sd()}function yd(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){if(e.audioFieldIndices.length){const r=wd(e.audioFieldIndices,e.audioFieldSources);r.forEach(a=>si(a)),ce.debug("scan mounted explicit fields",{count:r.length}),Yr(),ii(e,r);return}const t=[];let n=0;bd().forEach((r,a)=>{const o=xa(r);if(!o)return;const s={node:r,ord:qd(r,a),sourceFilename:o};si(s),t.push(s),n+=1}),ce.debug("scan mounted detected fields",{count:n}),Yr(),ii(e,t)}function bd(){const e=Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]')),t=new Set;return e.filter(n=>t.has(n)?!1:(t.add(n),!!(n.textContent||n.innerHTML)))}function wd(e,t={}){return e.map(n=>{const r=document.querySelector(`.field-container[data-index="${n}"]`);if(!r)return null;const a=r.querySelector('[contenteditable="true"]')||r,o=xa(a)||xa(r)||t[n]||"";return{ord:n,node:a,sourceFilename:o}}).filter(n=>n!==null)}function qd(e,t){const n=["data-field-ord","data-ord","data-index"];for(const a of n){const o=e.getAttribute(a);if(o!==null&&/^\d+$/.test(o))return Number(o)}const r=/(\d+)/.exec(String(e.id||""));return r?Number(r[1]):t}function xa(e){const t=e.innerHTML||e.textContent||"",n=md.exec(t),r=n==null?void 0:n[1];return r&&vd.test(r)?r:""}function si(e){ad(e)}function ii(e,t){e.showGraphByDefault&&zi(t.map(({ord:n,sourceFilename:r})=>({ord:n,sourceFilename:r})),{anyBusy:()=>document.body.dataset.aqeBusy==="true",requestDefaultGraph:No})}function Ta(e,t){const n=window.setTimeout(()=>{$n=$n.filter(r=>r!==n),e()},t);$n.push(n)}gd()})();
