var Eh=Object.defineProperty;var zi=V=>{throw TypeError(V)};var Ph=(V,j,ee)=>j in V?Eh(V,j,{enumerable:!0,configurable:!0,writable:!0,value:ee}):V[j]=ee;var ot=(V,j,ee)=>Ph(V,typeof j!="symbol"?j+"":j,ee),mo=(V,j,ee)=>j.has(V)||zi("Cannot "+ee);var h=(V,j,ee)=>(mo(V,j,"read from private field"),ee?ee.call(V):j.get(V)),D=(V,j,ee)=>j.has(V)?zi("Cannot add the same private member more than once"):j instanceof WeakSet?j.add(V):j.set(V,ee),C=(V,j,ee,Ln)=>(mo(V,j,"write to private field"),Ln?Ln.call(V,ee):j.set(V,ee),ee),le=(V,j,ee)=>(mo(V,j,"access private method"),ee);(function(){"use strict";var Bi,Gi,Vi,qn,Sn,Qt,Mn,dr,fr,Zt,mt,kn,Ae,_o,vo,go,el,Re,lo,Je,Jt,be,ze,Ee,$e,_t,zt,Rt,An,En,Pn,et,$r,ae,Fh,Nh,Ch,bo,zr,ea,yo,Hi,Ue,tt,Pe,en,hr,pr,Ur,Wi;const V=[{activeIcon:"pause",command:"aqe:play",icon:"play",iconOnly:!0,label:"Play",title:"Play or pause current audio"},{activeIcon:"audio-lines",command:"aqe:analyze",icon:"audio-lines",iconOnly:!0,label:"Graph",title:"Analyze and show pitch/intensity graph"},{command:"aqe:show-file",icon:"folder-open",label:"Folder",title:"Show current audio file in folder"},{command:"aqe:trim-left",icon:"scissors",label:"-L",title:"Trim 100 ms from left"},{command:"aqe:trim-right",icon:"scissors",label:"-R",title:"Trim 100 ms from right"},{command:"aqe:remove-pauses",icon:"timer-reset",label:"Shorten Pauses",title:"Speed up long internal pauses"},{command:"aqe:slower",icon:"rewind",label:"Slower",title:"Decrease speed"},{command:"aqe:faster",icon:"fast-forward",label:"Faster",title:"Increase speed"},{command:"aqe:volume-down",icon:"volume-1",iconOnly:!0,label:"Volume -",title:"Decrease volume"},{command:"aqe:volume-up",icon:"volume-2",iconOnly:!0,label:"Volume +",title:"Increase volume"},{command:"aqe:undo",icon:"undo-2",iconOnly:!0,label:"Undo",title:"Restore the previous generated audio reference"},{command:"aqe:redo",icon:"redo-2",iconOnly:!0,label:"Redo",title:"Restore the most recently undone audio reference"},{command:"aqe:settings",icon:"settings",iconOnly:!0,label:"Settings",title:"Open Audio Quick Editor settings"}],j=new Set(["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:remove-pauses","aqe:denoise-standard","aqe:rnnoise","aqe:volume-down","aqe:volume-up"]),ee={"aqe:play":"play","aqe:analyze":"graph","aqe:show-file":"show-file","aqe:delete-selection":"delete-selection","aqe:trim-left":"trim-left","aqe:trim-right":"trim-right","aqe:remove-pauses":"remove-pauses","aqe:denoise-standard":"denoise-standard","aqe:rnnoise":"rnnoise","aqe:slower":"slower","aqe:faster":"faster","aqe:volume-down":"volume-down","aqe:volume-up":"volume-up","aqe:undo":"undo","aqe:redo":"redo","aqe:settings":"settings"};function Ln(e,t){return`aqe-button-${e}-${ee[t]}`}function wo(e){return e==="aqe:denoise-standard"?"Denoising with Standard...":e==="aqe:rnnoise"?"Denoising with RNNoise...":e==="aqe:delete-selection"?"Deleting region...":"Processing..."}function st(e){return document.querySelector(`.aqe-controls[data-aqe-field-ord="${e}"]`)}function G(e){return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${e}"]`)}function qo(e,t){const n=st(e);return(n==null?void 0:n.querySelector(`[data-aqe-command="${t}"]`))??null}function So(e){return qo(e,"aqe:analyze")}function Mo(e){return qo(e,"aqe:play")}function ko(e){const t=st(e);return(t==null?void 0:t.querySelector(".aqe-repeat-button"))??null}function yr(){return Array.from(document.querySelectorAll(".aqe-button"))}function ta(){return Array.from(document.querySelectorAll(".aqe-visualizer"))}const Ao=[];let wr=null,qr=null;function an(e){globalThis.pycmd!==void 0&&globalThis.pycmd(e)}function on(e,t){an(`focus:${e}`),an(t)}function tl(e,t){an(`focus:${e}`),window.__aqePendingCommandPayload=t,an("aqe:command-payload")}function nl(e){wr=e,an("aqe:analyze-field")}function rl(e){Ao.push(e),an("aqe:frontend-log")}function al(){return Ao.shift()??null}function ol(e){window.__aqePendingPlaybackRequest=e,window.__aqeLastPlaybackRequest=e}function sl(){if(!window.__aqePendingPlaybackRequest)return null;const e=window.__aqePendingPlaybackRequest;return window.__aqePendingPlaybackRequest=null,e}function il(){if(!wr)return null;const e=wr;return wr=null,e}function ll(e){qr=e}function ul(){if(!qr)return null;const e=qr;return qr=null,e}function cl(e){window.__aqeLastCursorIntent=e}function dl(e){return encodeURIComponent(e||"").replaceAll("%2F","/")}function Le(e){return(e==null?void 0:e.querySelector(".aqe-audio-clock"))??null}function na(e){e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!1,e.__aqeAudioClockLastSeekedMs=0,e.dataset.progressClockMode="stopped"}function In(e){const t=Le(e);if(!(!t||typeof t.pause!="function"))try{t.pause()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function ra(e){const t=Le(e);if(na(e),!!t){In(e),t.removeAttribute("src"),t.src="";try{t.load()}catch{e.__aqeAudioClockFallback=!0}}}function fl(e,t){const n=Le(e);if(na(e),!n){e.__aqeAudioClockFallback=!0;return}if(In(e),!t){ra(e);return}n.setAttribute("src",dl(t));try{n.load()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function hl(e,t={}){const n=Le(e);!n||n.__aqeClockHandlersInstalled||(n.__aqeClockHandlersInstalled=!0,n.addEventListener("loadedmetadata",()=>{n.getAttribute("src")&&(e.__aqeAudioClockAvailable=!0,e.__aqeAudioClockFallback=!1)}),n.addEventListener("error",()=>{var r;e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,e.dataset.playbackState==="playing"&&e.dataset.progressClockMode==="audio"&&((r=t.onErrorDuringPlayback)==null||r.call(t))}),n.addEventListener("ended",()=>{var r;e.dataset.playbackState==="playing"&&((r=t.onEndedDuringPlayback)==null||r.call(t))}),n.addEventListener("seeked",()=>{e.__aqeAudioClockLastSeekedMs=Math.round((Number(n.currentTime)||0)*1e3)}))}function Sr(e){const t=Le(e);return!t||!(e!=null&&e.__aqeAudioClockAvailable)||!t.getAttribute("src")?!1:t.readyState===void 0||t.readyState>=1}function Mr(e,t,n){const r=Le(e);if(!r)return!1;const a=Math.max(0,Math.min(Number(t)||0,n||0));try{return r.currentTime=a/1e3,e.__aqeAudioClockLastSeekedMs=Math.round(a),!0}catch{return e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,!1}}var Bn=(e=>(e.Debug="debug",e.Error="error",e.Info="info",e.Unknown="unknown",e.Warn="warn",e))(Bn||{});function pl(e){return e==="error"?console.error:console.warn}function ml(e){return e==="debug"?Bn.Debug:e==="warn"?Bn.Warn:e==="error"?Bn.Error:Bn.Info}function aa(e,t=0){const n=_l(e);return n!==void 0?n:Array.isArray(e)?vl(e,t):e!==null&&typeof e=="object"?gl(e,t):bl(e)}function _l(e){if(e===void 0)return"[undefined]";if(e===null)return null;if(typeof e=="boolean"||typeof e=="number"||typeof e=="string")return e}function vl(e,t){return t>=4?"[array]":e.map(n=>aa(n,t+1))}function gl(e,t){if(t>=4)return"[object]";const n={};for(const[r,a]of Object.entries(e))n[r]=aa(a,t+1);return n}function bl(e){return typeof e=="bigint"?e.toString():typeof e=="symbol"?e.description?`Symbol(${e.description})`:"Symbol()":typeof e=="function"?`[function ${e.name||"anonymous"}]`:"[unserializable]"}function yl(e,t,n){const r={level:ml(e),message:t};return n!==void 0&&(r.context=aa(n)),r}function wl(e,t){function n(r,a,o){const s=pl(r);o===void 0?s(`[${e}] ${a}`):s(`[${e}] ${a}`,o);try{t(yl(r,a,o))}catch{}}return{debug:(r,a)=>n("debug",r,a),error:(r,a)=>n("error",r,a),info:(r,a)=>n("info",r,a),warn:(r,a)=>n("warn",r,a)}}const pe=wl("editor",rl),Gn=[],kr=new Set;let Ar=null,Er=null,Pr=!1;function ql(){Gn.length=0,kr.clear(),Ar=null,Er=null,Pr=!1}function Sl(e,t){for(const n of e){if(!n.sourceFilename)continue;const r=Ml(n);if(kr.has(r))continue;const a=G(n.ord);if((a==null?void 0:a.dataset.hasTrack)==="true"&&a.dataset.sourceFilename===n.sourceFilename){kr.add(r);continue}kr.add(r),Gn.push({key:r,ord:n.ord,sourceFilename:n.sourceFilename})}Fr(t)}function Fr(e){if(!(Ar!==null||e.anyBusy()))for(;Gn.length;){const t=Gn.shift();if(!t)return;const n=G(t.ord);if(!n){Po(t,e);return}const r=st(t.ord);if(!r){Po(t,e);return}if((r.dataset.aqeSourceFilename||t.sourceFilename)===t.sourceFilename&&!(n.dataset.hasTrack==="true"&&n.dataset.sourceFilename===t.sourceFilename)){Ar=t.key,Er=t.ord,e.requestDefaultGraph({ord:t.ord,sourceFilename:t.sourceFilename});return}}}function Eo(e,t){Er===e&&(Ar=null,Er=null,queueMicrotask(()=>Fr(t)))}function Ml(e){return`${e.ord}\0${e.sourceFilename}`}function Po(e,t){Gn.unshift(e),!Pr&&(Pr=!0,window.setTimeout(()=>{Pr=!1,Fr(t)},0))}function kl(e,t){return Math.max(t.startMs,Math.min(Number(e)||0,t.endMs))}function Al(e){let t="start";e.playbackState==="playing"&&(t="pause"),e.playbackState==="paused"&&(t=e.resumeRequiresRestart?"start":"resume");let n=e.anchorMs;return t==="start"&&e.region.mode==="selection"&&(n=e.region.startMs),t==="pause"&&(n=Fo(e.currentProgressMs,e.cursorMs,n)),t==="resume"&&(n=Fo(e.currentProgressMs,e.cursorMs,n),e.region.mode==="selection"&&(n<e.region.startMs||n>e.region.endMs)&&(t="start",n=e.region.startMs)),{action:t,cursorMs:Math.round(n),endMs:Math.round(e.region.endMs),engine:e.engine,loop:e.repeat,ord:e.ord,regionMode:e.region.mode}}function Fo(e,t,n){return Number(e||t||n||0)}function El(e){return{analyzerName:e.analyzerName,durationMs:Number(e.durationMs)||0,pitchMaxHz:e.pitchMaxHz,pitchMinHz:e.pitchMinHz,points:e.points.map(Pl),sourceFilename:e.sourceFilename}}function Pl(e){const t=typeof e[0]=="number"?e[0]:0,n=typeof e[1]=="number"?e[1]:null,r=typeof e[2]=="number"?e[2]:null,a=typeof e[3]=="boolean"?e[3]:!1;return[t,n,r,a]}function oa(e){return e==="playing"||e==="paused"||e==="stopped"}const No=50,Fl=4;function Co(){return{active:!1,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:null,startMs:null}}function xo(e,t){return Math.max(0,Math.min(Number(e)||0,Math.max(0,Number(t)||0)))}function Nr(e,t,n,r=No){const a=xo(Math.min(e,t),n),o=xo(Math.max(e,t),n);return!n||o-a<r?null:{startMs:Math.round(a),endMs:Math.round(o)}}function Nl(e,t){if(!e.active||e.startMs===null||e.endMs===null)return null;const n=Nr(e.startMs,e.endMs,t);return n?{...n,mode:"selection"}:null}function Cl(e,t){if(!e.draftActive||e.draftStartMs===null||e.draftEndMs===null)return null;const n=Nr(e.draftStartMs,e.draftEndMs,t);return n?{...n,mode:"selection"}:null}function xl(e,t,n,r){const a=Nr(t,n,r);return a?{...e,active:!0,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:a.endMs,startMs:a.startMs}:Rl(e)}function Tl(e,t,n,r){const a=Nr(t,n,r);return a?{...e,draftActive:!0,draftEndMs:a.endMs,draftStartMs:a.startMs}:To(e)}function Rl(e){return{...To(e),active:!1,endMs:null,startMs:null}}function To(e){return{...e,draftActive:!1,draftEndMs:null,draftStartMs:null}}function Ro(e,t,n,r){return Math.abs(t.clientX-e.clientX)<Fl||Math.abs(r-n)<No}const k={width:620,height:150,left:44,right:10,top:10,bottom:34};function Do(){return k.width-k.left-k.right}function Oo(){return k.height-k.top-k.bottom}function qt(e,t){return t?k.left+Math.max(0,Math.min(1,e/t))*Do():k.left}function Dl(e,t,n){if(!e||!t||!n||n<=t)return k.height-k.bottom;const r=Math.max(0,Math.min(1,(e-t)/(n-t)));return k.top+(1-r)*Oo()}function Lo(e,t){return t&&t<2e3?`${Math.round(e)} ms`:`${(e/1e3).toFixed(2)}s`}function Ol(e,t){if(!e.length||!t)return"";const n=k.height-k.bottom,r=e[0];if(!r)return"";const a=`M ${qt(r[0],t).toFixed(2)} ${n.toFixed(2)}`,o=e.map(l=>{const c=qt(l[0],t).toFixed(2),d=Math.max(0,Math.min(1,l[2]??0)),u=(n-d*Oo()).toFixed(2);return`L ${c} ${u}`}).join(" "),s=e.at(-1)??r,i=`L ${qt(s[0],t).toFixed(2)} ${n.toFixed(2)} Z`;return`${a} ${o} ${i}`}function Ll(e,t,n,r){const a=[];let o=[];for(const s of e){const i=s[1];if(!(s[3]===!0&&i!==null&&i!==void 0)){o.length&&a.push(o),o=[];continue}o.push([qt(s[0],t),Dl(i,n,r)])}return o.length&&a.push(o),a}function Il(e,t){const n=e.querySelector(".aqe-pitch");if(n){n.textContent="";for(const r of Ll(t.points,t.durationMs,t.pitchMinHz,t.pitchMaxHz)){if(r.length<2)continue;const a=document.createElementNS("http://www.w3.org/2000/svg","path");a.setAttribute("class","aqe-pitch-path"),a.setAttribute("d",r.map((o,s)=>{const i=o[0]??0,l=o[1]??0;return`${s?"L":"M"} ${i.toFixed(2)} ${l.toFixed(2)}`}).join(" ")),n.appendChild(a)}}}function Bl(e,t){const n=e.querySelector(".aqe-labels");if(!n)return;n.textContent="";const r=t.pitchMaxHz||500,a=t.pitchMinHz||75;for(const o of[[r,k.top+10],[a,k.height-k.bottom]]){const s=document.createElementNS("http://www.w3.org/2000/svg","text");s.setAttribute("class","aqe-hz-label"),s.setAttribute("x","2"),s.setAttribute("y",String(o[1])),s.textContent=`${Math.round(o[0])} Hz`,n.appendChild(s)}}function Gl(e,t){const n=e.querySelector(".aqe-x-axis");if(!n)return;n.textContent="";const r=[0,t/2,t].filter((a,o,s)=>o===0||a!==s[o-1]);for(const a of r){const o=qt(a,t),s=document.createElementNS("http://www.w3.org/2000/svg","line");s.setAttribute("class","aqe-x-tick"),s.setAttribute("x1",o.toFixed(2)),s.setAttribute("x2",o.toFixed(2)),s.setAttribute("y1",String(k.height-k.bottom)),s.setAttribute("y2",String(k.height-k.bottom+4));const i=document.createElementNS("http://www.w3.org/2000/svg","text");i.setAttribute("class","aqe-x-label"),i.setAttribute("x",o.toFixed(2)),i.setAttribute("y",String(k.height-8)),i.textContent=Lo(a,t),n.append(s,i)}}function Io(e){const t=e.getBoundingClientRect(),n=Number(t.width)||k.width,r=Number(t.height)||k.height,a=Math.min(n/k.width,r/k.height)||1;return{left:t.left+k.left*a,width:Do()*a}}function Vn(e,t,n){const r=Io(t);return Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*n}function Vl(e){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="true",e.dataset.hasTrack="false",e.dataset.durationMs="0",e.dataset.sourceFilename="",e.dataset.anchorMs="0",e.dataset.cursorMs="0",e.dataset.progressMs="0",e.dataset.resumeRequiresRestart="false",e.dataset.playbackEngine="",e.dataset.playbackStartMs="0",e.dataset.playbackEndMs="0",e.dataset.playbackRegionMode="full",Bo(e)}function Hl(e,t){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="false",e.dataset.hasTrack="true",e.dataset.durationMs=String(t.durationMs||0),e.dataset.analyzerName=t.analyzerName||"",e.dataset.sourceFilename=t.sourceFilename||"";const n=e.querySelector(".aqe-intensity");n&&n.setAttribute("d",Ol(t.points,t.durationMs)),Il(e,t),Bl(e,t),Gl(e,t.durationMs||0)}function Wl(e,t,n="info"){const r=e.querySelector(".aqe-visualizer-status"),a=e.querySelector(".aqe-spinner"),o=n==="processing";e.dataset.graphBusy=o?"true":"false",a&&(a.hidden=!o),r&&(r.textContent=t||"",r.dataset.kind=n||"info")}function jl(e,t,n){const r=e.querySelector(".aqe-selection"),a=e.querySelector(".aqe-selection-start"),o=e.querySelector(".aqe-selection-end"),s=n??t,i=Number(e.dataset.durationMs||"0");if(!r||!a||!o||!s||!i){r==null||r.setAttribute("width","0"),r==null||r.setAttribute("visibility","hidden"),r==null||r.classList.remove("aqe-selection-draft"),a==null||a.setAttribute("visibility","hidden"),o==null||o.setAttribute("visibility","hidden");return}const l=qt(s.startMs,i),c=qt(s.endMs,i);r.setAttribute("visibility","visible"),r.classList.toggle("aqe-selection-draft",n!==null),r.setAttribute("x",l.toFixed(2)),r.setAttribute("y",String(k.top)),r.setAttribute("width",Math.max(0,c-l).toFixed(2)),r.setAttribute("height",String(k.height-k.top-k.bottom)),a.setAttribute("visibility","visible"),o.setAttribute("visibility","visible");for(const[d,u]of[[a,l],[o,c]])d.setAttribute("x1",u.toFixed(2)),d.setAttribute("x2",u.toFixed(2)),d.setAttribute("y1",String(k.top)),d.setAttribute("y2",String(k.height-k.bottom))}function $l(e,t,n){const r=qt(t,n),a=e.querySelector(".aqe-cursor");a&&(a.setAttribute("x1",r.toFixed(2)),a.setAttribute("x2",r.toFixed(2)));const o=e.querySelector(".aqe-cursor-label");o&&(o.textContent=Lo(t,n))}function Bo(e){var t;(t=e.querySelector(".aqe-intensity"))==null||t.setAttribute("d",""),sa(e,".aqe-pitch"),sa(e,".aqe-labels"),sa(e,".aqe-x-axis")}function Ul(e){const t=e.querySelector(".aqe-cursor");t&&(t.setAttribute("x1",String(k.left)),t.setAttribute("x2",String(k.left)));const n=e.querySelector(".aqe-cursor-label");n&&(n.textContent="0 ms")}function Xl(e,t){return{analyzerName:t.analyzerName,durationMs:t.durationMs,ord:e,points:t.points.length,sourceFilename:t.sourceFilename}}function sa(e,t){const n=e.querySelector(t);n&&(n.textContent="")}function Hn(e){return!e||e.dataset.selectionActive!=="true"?null:Nl({active:e.dataset.selectionActive==="true",startMs:Number(e.dataset.selectionStartMs||"0"),endMs:Number(e.dataset.selectionEndMs||"0")},Number(e.dataset.durationMs||"0"))}function ia(e){return!e||e.dataset.selectionDraftActive!=="true"?null:Cl({draftActive:e.dataset.selectionDraftActive==="true",draftStartMs:Number(e.dataset.selectionDraftStartMs||"0"),draftEndMs:Number(e.dataset.selectionDraftEndMs||"0")},Number(e.dataset.durationMs||"0"))}function Go(e){const t=Hn(e);return t||{startMs:0,endMs:Number(e.dataset.durationMs||"0")||0,mode:"full"}}function sn(e,t={}){e.dataset.selectionDraftActive="false",e.dataset.selectionDraftStartMs="",e.dataset.selectionDraftEndMs="",t.redraw!==!1&&Cr(e)}function Kl(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Tl(Co(),t,n,a);return!o.draftActive||o.draftStartMs===null||o.draftEndMs===null?(sn(e,r),!1):(e.dataset.selectionDraftActive="true",e.dataset.selectionDraftStartMs=String(o.draftStartMs),e.dataset.selectionDraftEndMs=String(o.draftEndMs),r.redraw!==!1&&Cr(e),!0)}function Yl(e,t,n={}){const r=ia(e);return r?(sn(e,{redraw:!1}),Ql(e,r.startMs,r.endMs,t,n)):(sn(e),!1)}function Vo(e,t={}){if(e.dataset.selectionActive="false",e.dataset.selectionStartMs="",e.dataset.selectionEndMs="",sn(e,{redraw:!1}),Cr(e),t.resetPlaybackRegion!==!1){const n=Go(e);e.dataset.playbackStartMs=String(Math.round(n.startMs)),e.dataset.playbackEndMs=String(Math.round(n.endMs)),e.dataset.playbackRegionMode=n.mode}}function Ql(e,t,n,r,a={}){const o=Number(e.dataset.durationMs||"0"),s=xl(Co(),t,n,o);return!s.active||s.startMs===null||s.endMs===null?(Vo(e),!1):(sn(e,{redraw:!1}),e.dataset.selectionActive="true",e.dataset.selectionStartMs=String(s.startMs),e.dataset.selectionEndMs=String(s.endMs),e.dataset.playbackStartMs=String(s.startMs),e.dataset.playbackEndMs=String(s.endMs),e.dataset.playbackRegionMode="selection",Cr(e),a.updateCursor!==!1&&r.setCursor(e,s.startMs,!1),!0)}function Cr(e){const t=ia(e),n=t??Hn(e);jl(e,n,t)}function Zl(){return document.body.dataset.aqeBusy==="true"}function Jl(e){var t;return((t=st(e))==null?void 0:t.querySelector(".aqe-delete-region-button"))??null}function Ho(e,t){return e.startMs<=0&&e.endMs>=t}function Wo(e,t){return!!e&&e.endMs>e.startMs&&!Ho(e,t)}function Wn(e){const t=Number(e.dataset.aqeFieldOrd||"0"),n=Jl(t);if(!n)return;const r=Hn(e),a=Number(e.dataset.durationMs||"0"),o=r!==null,s=Wo(r,a);n.hidden=!o,n.disabled=Zl()||!s,n.dataset.aqeButtonState=s?"default":"unavailable",n.title=s?"Delete selected region":"Cannot delete the whole audio clip",n.setAttribute("aria-disabled",n.disabled?"true":"false")}function zl(){ta().forEach(Wn)}function jo(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=Number(e.dataset.durationMs||"0")||0,a=Hn(e);if(!a||!Wo(a,r))return a&&Ho(a,r)&&pe.warn("region delete rejected whole clip",{ord:n,sourceFilename:e.dataset.sourceFilename||"",selectionStartMs:a.startMs,selectionEndMs:a.endMs,durationMs:r,trigger:t}),null;const o=e.dataset.sourceFilename||"";if(!o)return null;const s=e.dataset.playbackState;return{ord:n,sourceFilename:o,selectionStartMs:Math.round(a.startMs),selectionEndMs:Math.round(a.endMs),cursorMs:Math.round(Number(e.dataset.cursorMs||"0")||0),durationMs:Math.round(r),trigger:t,playbackActive:oa(s)&&s!=="stopped"}}function eu(e,t,n,r,a){e.preventDefault();const o=a.playbackStateFor(t),s=t.querySelector(".aqe-visualizer-svg"),i=Number(t.dataset.durationMs||"0");if(!s||!i)return;o==="playing"&&a.stopProgressClock(t);const l=d=>{a.setCursor(t,$o(d,s,i,t,a),!1)},c=d=>{window.removeEventListener("pointermove",l),window.removeEventListener("pointerup",c);const u=o==="playing";o==="paused"&&(t.dataset.resumeRequiresRestart="true");const f=$o(d,s,i,t,a),_=u&&a.audioClockReady(t)?"html":"";a.setCursor(t,f,r,{previousPlaybackState:o,restartPlayback:u,engine:_}),a.audioClockReady(t)&&a.seekAudioClock(t,f),u&&_==="html"&&a.startEditorHtmlPlayback(t,a.playbackRequestForStart(t,n,f,"html"))};l(e),window.addEventListener("pointermove",l),window.addEventListener("pointerup",c)}function tu(e,t,n,r){e.preventDefault();const a=t.querySelector(".aqe-visualizer-svg"),o=Number(t.dataset.durationMs||"0");if(!a||!o)return;const s=r.playbackStateFor(t),i=r.currentProgressMs(t)??Number(t.dataset.cursorMs||"0"),l={clientX:e.clientX},c=Vn(e,a,o);let d=!1,u=P=>{},f=P=>{},_=()=>{},m=P=>{};const w=()=>{window.removeEventListener("pointermove",u),window.removeEventListener("pointerup",f),window.removeEventListener("pointercancel",_),window.removeEventListener("keydown",m),window.removeEventListener("blur",_),a.removeEventListener("lostpointercapture",_)},p=()=>{d||s!=="playing"||(d=!0,r.stopProgressClock(t,{clearEngine:!1}),r.setCursor(t,i,!1,{updateAnchor:!1}))},v=()=>{s==="playing"&&d&&r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,i,"html"))};u=P=>{const y=Vn(P,a,o);if(Ro(l,P,c,y)){r.clearSelectionDraft(t);return}p(),r.setSelectionDraft(t,c,y)},f=P=>{w();const y=Vn(P,a,o);if(Ro(l,P,c,y)){r.clearSelection(t),v();return}p(),r.draftSelectionForVisualizer(t)||r.setSelectionDraft(t,c,y,{redraw:!1});const M=r.commitSelectionDraft(t);if(s==="paused"&&(t.dataset.resumeRequiresRestart="true"),M&&s==="playing"){const F=r.selectionForVisualizer(t);r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,(F==null?void 0:F.startMs)??c,"html"))}},_=()=>{w(),r.clearSelectionDraft(t),v()},m=P=>{P.key==="Escape"&&_()},window.addEventListener("pointermove",u),window.addEventListener("pointerup",f),window.addEventListener("pointercancel",_),window.addEventListener("keydown",m),window.addEventListener("blur",_),a.addEventListener("lostpointercapture",_)}function nu(e,t,n){const r=n.visualizerForOrd(t);if(r){if(e.shiftKey){tu(e,r,t,n);return}eu(e,r,t,!0,n)}}function $o(e,t,n,r,a){const o=Vn(e,t,n),s=a.selectionForVisualizer(r);return s&&r.dataset.repeatEnabled==="true"?kl(o,s):o}function Ot(e){e.__aqePlaybackTimer&&(window.cancelAnimationFrame(e.__aqePlaybackTimer),e.__aqePlaybackTimer=null)}function Uo(e){const t=Number(e.dataset.durationMs||"0"),n=performance.now()-Number(e.dataset.playStartedAt||"0");return Math.min(t,Number(e.dataset.playStartMs||"0")+n)}function Xo(e){const t=Le(e);if(!t)return null;const n=Number(e.dataset.durationMs||"0");return Math.min(n,(Number(t.currentTime)||0)*1e3)}function Ko(e){return e.dataset.progressClockMode==="audio"?Xo(e):e.dataset.progressClockMode==="manual"?Uo(e):Number(e.dataset.progressMs||e.dataset.cursorMs||"0")}function la(e,t,n,r={}){return t<iu(e,n)?!1:n.repeatEnabledFor(e)?(lu(e,n,r),!0):(ru(e,n),!0)}function ru(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=t.effectivePlaybackRegion(e),a=e.dataset.playbackRegionMode==="selection"?r.startMs:Number(e.dataset.anchorMs||"0");ca(e,t),t.setCursor(e,a,!1,{updateAnchor:!1}),Sr(e)&&Mr(e,a,Number(e.dataset.durationMs||"0")),t.clearStatus(n),window.__aqeActiveField=n,t.focusAndSendCommand(n,"aqe:play-ended")}function ua(e,t){const n=()=>{if(e.dataset.playbackState!=="playing")return;const r=Xo(e);if(r===null){it(e,Number(e.dataset.cursorMs||"0"),t);return}t.setCursor(e,r,!1,{updateAnchor:!1}),!la(e,r,t)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(n))};e.__aqePlaybackTimer=window.requestAnimationFrame(n)}function it(e,t,n){if(Ot(e),In(e),!Number(e.dataset.durationMs||"0"))return;const a=Yo(e,t);e.__aqeAudioClockFallback=!0,e.dataset.playbackState="playing",e.dataset.progressClockMode="manual",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),da(e,a,n),n.setPlaybackButtonLabel(e,"Pause");const o=()=>{if(e.dataset.playbackState!=="playing")return;const s=Uo(e);n.setCursor(e,s,!1,{updateAnchor:!1}),!la(e,s,n)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(o))};e.__aqePlaybackTimer=window.requestAnimationFrame(o)}function au(e,t,n,r={}){var i;const a=Le(e);if(!a||!Mr(e,t,Number(e.dataset.durationMs||"0"))||typeof a.play!="function"){if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}it(e,t,n);return}e.dataset.progressClockMode="audio",e.__aqeAudioClockFallback=!1;const o=()=>{var l;if(r.manualFallback===!1){(l=r.onAudioPlayFailed)==null||l.call(r);return}it(e,t,n)},s=()=>{var l;e.dataset.playbackState==="playing"&&(Ot(e),e.dataset.progressClockMode="audio",pe.info("html audio playback started",{ord:e.dataset.aqeFieldOrd}),ua(e,n),(l=r.onAudioStarted)==null||l.call(r))};Promise.resolve(a.play()).then(s).catch(()=>{e.dataset.playbackState==="playing"&&(pe.warn("html audio play rejected; using manual clock",{ord:e.dataset.aqeFieldOrd}),o())})}function ou(e,t,n,r={}){var i;const a=r.engine||e.dataset.playbackEngine||"";if(ca(e,n,{clearEngine:!1}),n.stopOtherPlayback(e),!Number(e.dataset.durationMs||"0"))return;const s=Yo(e,t);if(e.dataset.playbackEngine=a,e.dataset.playbackState="playing",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(s),da(e,s,n),n.setCursor(e,s,!1,{updateAnchor:!1}),n.setPlaybackButtonLabel(e,"Pause"),pe.info("playback clock selected",{engine:a||"auto",startMs:s}),a==="native"){it(e,s,n);return}if(Sr(e)){au(e,s,n,r);return}if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}it(e,s,n)}function su(e,t){const n=Ko(e);n!==null&&t.setCursor(e,n,!1,{updateAnchor:!1}),Ot(e),In(e),e.dataset.playbackState="paused",e.dataset.progressClockMode="stopped",t.setPlaybackButtonLabel(e,"Play")}function ca(e,t,n={}){Ot(e),In(e),e.dataset.playbackState="stopped",e.dataset.progressClockMode="stopped",e.dataset.resumeRequiresRestart="false",n.clearEngine!==!1&&(e.dataset.playbackEngine=""),n.clearAudio&&ra(e),t.setPlaybackButtonLabel(e,"Play")}function da(e,t,n,r=n.effectivePlaybackRegion(e)){e.dataset.playbackStartMs=String(Math.round(t)),e.dataset.playbackEndMs=String(Math.round(r.endMs)),e.dataset.playbackRegionMode=r.mode}function iu(e,t){const n=t.effectivePlaybackRegion(e),r=Number(e.dataset.playbackEndMs||"0")||n.endMs;return Math.max(n.startMs,Math.min(r,Number(e.dataset.durationMs||"0")||0))}function lu(e,t,n={}){const r=t.effectivePlaybackRegion(e),a=r.startMs;if(da(e,a,t,r),e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),t.setCursor(e,a,!1,{updateAnchor:!1}),e.dataset.progressClockMode!=="audio"||!Sr(e)){it(e,a,t);return}if(!Mr(e,a,Number(e.dataset.durationMs||"0"))){it(e,a,t);return}if(!n.forceAudioPlay){Ot(e),ua(e,t);return}const o=Le(e);!o||typeof o.play!="function"||(Ot(e),Promise.resolve(o.play()).then(()=>{e.dataset.playbackState==="playing"&&ua(e,t)}).catch(()=>{e.dataset.playbackState==="playing"&&it(e,a,t)}))}function Yo(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function Qo(){return document.body.dataset.aqeBusy==="true"}function Zo(){var e;return((e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.repeatPlaybackByDefault)===!0}function uu(e){for(const t of ta())t!==e&&cn(t)!=="stopped"&&St(t)}function cu(){for(const e of ta())cn(e)!=="stopped"&&St(e)}function ln(e,t,n="",r=""){document.body.dataset.aqeBusy=t?"true":"false",document.querySelectorAll(".aqe-controls").forEach(s=>{s.dataset.busy=t?"true":"false"}),yr().forEach(s=>{s.disabled=!!t}),zl(),t||queueMicrotask(()=>Fr(ga()));const a=st(e),o=a==null?void 0:a.querySelector(".aqe-status");o&&(o.textContent=n||"",o.dataset.kind=t?"processing":"info",o.title=r||"")}function Jo(e,t="info"){const n=Number(window.__aqeActiveField??0),r=st(n),a=r==null?void 0:r.querySelector(".aqe-status");a&&(a.textContent=e||"",a.dataset.kind=t||"info")}function du(e){const t=st(e),n=t==null?void 0:t.querySelector(".aqe-status");n&&(n.textContent="",n.dataset.kind="info",n.title="")}function un(e,t,n){var o;const r=t==="aqe:play"?Mo(e):t==="aqe:analyze"?So(e):((o=st(e))==null?void 0:o.querySelector(`[data-aqe-command="${t}"]`))??null;if(!r)return;const a=r.querySelector(".aqe-button-label");if(a?a.textContent=n:r.textContent=n,t==="aqe:play"&&(r.dataset.aqeButtonState=n==="Pause"?"pause":"play"),t==="aqe:analyze"){r.dataset.aqeButtonState=n==="Redraw"?"redraw":"graph";const s=n==="Redraw"?"Redraw the pitch graph":"Analyze and show pitch/intensity graph";r.title=s,r.setAttribute("aria-label",s)}}function zo(e,t,n,r){if(!Qo()){if(typeof t.focus=="function"&&t.focus(),window.__aqeActiveField=n,pe.info("command dispatched",{command:e,ord:n}),e==="aqe:analyze"){rs(n,!0);return}if(!(e==="aqe:play"&&Tu(n))){if(j.has(e)&&(cu(),ln(n,!0,wo(e))),r){tl(n,r);return}on(n,e)}}}function fu(e){na(e)}function hu(e){Ot(e)}function pu(e){ra(e)}function mu(e,t){fl(e,t)}function _u(e){hl(e,{onErrorDuringPlayback(){pe.warn("audio clock failed during playback",{ord:e.dataset.aqeFieldOrd}),xu(e,Number(e.dataset.cursorMs||"0"))},onEndedDuringPlayback(){Cu(e,Number(e.dataset.durationMs||"0"),{forceAudioPlay:!0})}})}function fa(e){return Sr(e)}function vu(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function es(e){return Hn(e)}function ts(e){return ia(e)}function ha(e){return Go(e)}function pa(e,t){e.dataset.repeatEnabled=t?"true":"false";const n=Number(e.dataset.aqeFieldOrd||"0"),r=ko(n);r&&(r.ariaPressed=t?"true":"false",r.dataset.aqeButtonState=t?"active":"default")}function gu(e,t){const n=G(e);return n?(pa(n,t),!0):!1}function bu(e,t={}){sn(e,t)}function yu(e,t,n,r={}){return Kl(e,t,n,r)}function wu(e,t={}){const n=Yl(e,Mu(),t);return Wn(e),n}function jn(e,t={}){Vo(e,t),Wn(e)}function qu(e){e.dataset.playbackStartMs="0",e.dataset.playbackEndMs=String(Number(e.dataset.durationMs||"0")||0),e.dataset.playbackRegionMode="full",pa(e,Zo()),jn(e,{resetPlaybackRegion:!1})}function Su(){return{audioClockReady:fa,clearSelection:jn,clearSelectionDraft:bu,commitSelectionDraft:wu,currentProgressMs:is,draftSelectionForVisualizer:ts,playbackRequestForStart:ku,playbackStateFor:cn,seekAudioClock:ns,selectionForVisualizer:es,setCursor:Lt,setSelectionDraft:yu,startEditorHtmlPlayback:ds,stopProgressClock:St,visualizerForOrd:G}}function Mu(){return{setCursor:Lt}}function ma(e){return e.dataset.repeatEnabled==="true"}function $n(){return{clearStatus:du,effectivePlaybackRegion:ha,focusAndSendCommand:on,playbackEngineFor:Un,repeatEnabledFor:ma,setCursor:Lt,setPlaybackButtonLabel:Nu,stopOtherPlayback:uu}}function ku(e,t,n,r=Un(e)){const a=ha(e);return{ord:t,action:"start",cursorMs:Math.round(vu(e,n)),endMs:Math.round(a.endMs),engine:r,loop:ma(e),regionMode:a.mode}}function ns(e,t){return Mr(e,t,Number(e.dataset.durationMs||"0"))}function Lt(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Math.max(0,Math.min(Number(t)||0,a||0));if(e.dataset.cursorMs=String(Math.round(o)),e.dataset.progressMs=String(Math.round(o)),r.updateAnchor!==!1&&(e.dataset.anchorMs=String(Math.round(o))),$l(e,o,a),n){window.__aqeActiveField=Number(e.dataset.aqeFieldOrd||"0");const s={cursorMs:Math.round(o),previousPlaybackState:r.previousPlaybackState||cn(e),restartPlayback:!!r.restartPlayback};r.engine&&(s.engine=r.engine),cl(s),pe.info("cursor committed",s),on(window.__aqeActiveField,"aqe:set-cursor")}}function Au(e,t){var n;(n=G(t))==null||n.focus(),nu(e,t,Su())}function rs(e,t){os(e)&&(window.__aqeActiveField=e,pe.info("graph requested",{notifyPython:t,ord:e}),ln(e,!0,"Analyzing...",""),on(e,"aqe:analyze"))}function as(e){os(e.ord)&&(pe.info("default graph requested",e),ln(e.ord,!0,"Analyzing...",""),nl(e))}function os(e){const t=G(e);return t?(St(t,{clearAudio:!0}),Vl(t),jn(t),Lt(t,0,!1),un(e,"aqe:analyze","Redraw"),va(e,"Analyzing...","processing"),!0):!1}function Eu(e){return window.__aqePendingGraphRedrawField=e,_a()}function _a(){const e=window.__aqePendingGraphRedrawField;if(typeof e!="number")return!1;const t=G(e);return t?(t.dataset.graphBusy==="true"||t.dataset.hasTrack==="true"||rs(e,!0),!0):!1}function va(e,t,n="info"){const r=G(e);r&&Wl(r,t,n)}function Pu(e,t,n){const r=G(e);if(!r||!t)return;const a=El(t);Hl(r,a),r.dataset.anchorMs=String(n||0),window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null),jn(r),r.dataset.playbackStartMs="0",r.dataset.playbackEndMs=String(a.durationMs||0),r.dataset.playbackRegionMode="full",mu(r,a.sourceFilename||""),un(e,"aqe:analyze","Redraw"),Lt(r,n||0,!1),fa(r)&&ns(r,n||0),va(e,a.analyzerName||"","info"),ln(e,!1,"",""),Eo(e,ga()),pe.info("graph rendered",Xl(e,a))}function Fu(e,t,n="info"){n!=="processing"&&window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null);const r=G(e);r&&(r.hidden=!1,r.dataset.graphActive="true",n==="processing"&&(r.dataset.hasTrack="false"),un(e,"aqe:analyze","Redraw")),va(e,t,n),n!=="processing"&&Eo(e,ga())}function ga(){return{anyBusy:Qo,requestDefaultGraph:as}}function ss(){document.body.dataset.aqeBusy="false",window.__aqeActiveField=null,window.__aqeLastCursorIntent=null,document.querySelectorAll(".aqe-controls").forEach(e=>{e.dataset.busy="false",e.dataset.aqeSourceFilename="",e.querySelectorAll(".aqe-button").forEach(o=>{o.disabled=!1,o.dataset.aqeCommand==="aqe:analyze"&&un(Number(e.dataset.aqeFieldOrd||"0"),"aqe:analyze","Graph"),o.dataset.aqeCommand==="aqe:play"&&un(Number(e.dataset.aqeFieldOrd||"0"),"aqe:play","Play")});const t=e.querySelector(".aqe-status");t&&(t.textContent="",t.dataset.kind="info",t.title="");const n=e.querySelector(".aqe-visualizer");if(!n)return;hu(n),pu(n),n.hidden=!0,n.dataset.anchorMs="0",n.dataset.cursorMs="0",n.dataset.progressMs="0",n.dataset.graphActive="false",n.dataset.graphBusy="false",n.dataset.hasTrack="false",n.dataset.playbackState="stopped",n.dataset.playbackEngine="",n.dataset.resumeRequiresRestart="false",n.dataset.durationMs="0",n.dataset.sourceFilename="",n.dataset.analyzerName="",n.dataset.playStartedAt="0",n.dataset.playStartMs="0",n.dataset.playbackStartMs="0",n.dataset.playbackEndMs="0",n.dataset.playbackRegionMode="full",n.dataset.progressClockMode="stopped",pa(n,Zo()),jn(n),Bo(n),Ul(n);const r=n.querySelector(".aqe-visualizer-status");r&&(r.textContent="",r.dataset.kind="info");const a=n.querySelector(".aqe-spinner");a&&(a.hidden=!0)})}function Nu(e,t){const n=Number(e.dataset.aqeFieldOrd||"0");un(n,"aqe:play",t)}function is(e){return Ko(e)}function Cu(e,t,n={}){return la(e,t,$n(),n)}function xu(e,t){it(e,t,$n())}function ls(e,t,n={}){ou(e,t,$n(),n)}function us(e){su(e,$n())}function St(e,t={}){ca(e,$n(),t)}function cs(e){const t=G(e);return t?Al({anchorMs:Number(t.dataset.anchorMs||t.dataset.cursorMs||"0"),currentProgressMs:is(t),cursorMs:Number(t.dataset.cursorMs||"0"),engine:Un(t),ord:e,playbackState:cn(t),region:ha(t),repeat:ma(t),resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true"}):{ord:e,action:"start",cursorMs:0}}function Un(e){if(!e||e.dataset.hasTrack!=="true")return"native";const t=e.dataset.playbackEngine||"";return e.dataset.playbackState!=="stopped"&&(t==="html"||t==="native")?t:fa(e)?"html":"native"}function ba(e){const t=G(e.ord);t&&(t.dataset.playbackEngine=e.engine||""),ol(e),window.__aqeActiveField=e.ord,pe.info("playback request queued",e),on(e.ord,"aqe:play")}function ds(e,t){return ls(e,t.cursorMs,{engine:"html",manualFallback:!1,onAudioStarted(){ba(t)},onAudioPlayFailed(){if(pe.warn("html playback failed; falling back to native",{ord:t.ord}),St(e),t.regionMode==="selection"||t.loop){window.__aqeActiveField=t.ord,Jo("Selected repeat playback needs browser audio.","warning");return}ba({...t,engine:"native"})}}),!0}function Tu(e){const t=G(e);if(!t||Un(t)!=="html")return!1;const n={...cs(e),engine:"html"};return n.action==="pause"?(us(t),n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0"),ba(n),!0):(n.action==="resume"&&(n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0")),ds(t,n))}function Ru(e,t,n){const r=G(e);r&&((t==="playing"||t==="paused")&&(r.dataset.resumeRequiresRestart="false"),t==="playing"?ls(r,n,{engine:r.dataset.playbackEngine==="html"||r.dataset.playbackEngine==="native"?r.dataset.playbackEngine:""}):t==="paused"?us(r):St(r))}function Du(){const e=sl();if(e)return e;const t=Number(window.__aqeActiveField||"0"),n=cs(t),r=G(t);return r&&(r.dataset.playbackEngine=n.engine||""),n}function Ou(e){const t=G(e);return t?(St(t),!0):!1}function Lu(){const e=Number(window.__aqeActiveField||"0"),t=G(e);return t?Number(t.dataset.cursorMs||"0"):0}function Iu(){const e=Number(window.__aqeActiveField||"0"),t=G(e),n=t?Number(t.dataset.cursorMs||"0"):0;return window.__aqeLastCursorIntent||{cursorMs:n,previousPlaybackState:t?cn(t):"stopped",restartPlayback:!1}}function cn(e){const t=e.dataset.playbackState;return oa(t)?t:"stopped"}const fs=(Gi=(Bi=globalThis.process)==null?void 0:Bi.env)==null?void 0:Gi.NODE_ENV,b=fs&&!fs.toLowerCase().startsWith("prod");var ya=Array.isArray,Bu=Array.prototype.indexOf,It=Array.prototype.includes,xr=Array.from,Bt=Object.defineProperty,lt=Object.getOwnPropertyDescriptor,Gu=Object.getOwnPropertyDescriptors,Vu=Object.prototype,Hu=Array.prototype,hs=Object.getPrototypeOf,ps=Object.isExtensible;function Xn(e){return typeof e=="function"}const $=()=>{};function Wu(e){for(var t=0;t<e.length;t++)e[t]()}function ms(){var e,t,n=new Promise((r,a)=>{e=r,t=a});return{promise:n,resolve:e,reject:t}}function ju(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const r of e)if(n.push(r),n.length===t)break;return n}const ue=2,Kn=4,Tr=8,wa=1<<24,ut=16,Ie=32,Gt=64,qa=128,Fe=512,oe=1024,ce=2048,Be=4096,Me=8192,ct=16384,Vt=32768,Mt=65536,Rr=1<<17,_s=1<<18,dn=1<<19,$u=1<<20,dt=1<<25,kt=65536,Sa=1<<21,Dr=1<<22,At=1<<23,ft=Symbol("$state"),vs=Symbol("legacy props"),Uu=Symbol(""),gs=Symbol("proxy path"),Ht=new class extends Error{constructor(){super(...arguments);ot(this,"name","StaleReactionError");ot(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}},Ma=!!((Vi=globalThis.document)!=null&&Vi.contentType)&&globalThis.document.contentType.includes("xml");function bs(e){if(b){const t=new Error(`lifecycle_outside_component
\`${e}(...)\` can only be used during component initialisation
https://svelte.dev/e/lifecycle_outside_component`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/lifecycle_outside_component")}function Xu(){if(b){const e=new Error("async_derived_orphan\nCannot create a `$derived(...)` with an `await` expression outside of an effect tree\nhttps://svelte.dev/e/async_derived_orphan");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/async_derived_orphan")}function Ku(){if(b){const e=new Error(`derived_references_self
A derived value cannot reference itself recursively
https://svelte.dev/e/derived_references_self`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/derived_references_self")}function ys(e,t,n){if(b){const r=new Error(`each_key_duplicate
${n?`Keyed each block has duplicate key \`${n}\` at indexes ${e} and ${t}`:`Keyed each block has duplicate key at indexes ${e} and ${t}`}
https://svelte.dev/e/each_key_duplicate`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_duplicate")}function Yu(e,t,n){if(b){const r=new Error(`each_key_volatile
Keyed each block has key that is not idempotent — the key for item at index ${e} was \`${t}\` but is now \`${n}\`. Keys must be the same each time for a given item
https://svelte.dev/e/each_key_volatile`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_volatile")}function Qu(e){if(b){const t=new Error(`effect_in_teardown
\`${e}\` cannot be used inside an effect cleanup function
https://svelte.dev/e/effect_in_teardown`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_in_teardown")}function Zu(){if(b){const e=new Error("effect_in_unowned_derived\nEffect cannot be created inside a `$derived` value that was not itself created inside an effect\nhttps://svelte.dev/e/effect_in_unowned_derived");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Ju(e){if(b){const t=new Error(`effect_orphan
\`${e}\` can only be used inside an effect (e.g. during component initialisation)
https://svelte.dev/e/effect_orphan`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_orphan")}function zu(){if(b){const e=new Error(`effect_update_depth_exceeded
Maximum update depth exceeded. This typically indicates that an effect reads and writes the same piece of state
https://svelte.dev/e/effect_update_depth_exceeded`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function ec(){if(b){const e=new Error("invalid_snippet\nCould not `{@render}` snippet due to the expression being `null` or `undefined`. Consider using optional chaining `{@render snippet?.()}`\nhttps://svelte.dev/e/invalid_snippet");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/invalid_snippet")}function tc(e){if(b){const t=new Error(`props_invalid_value
Cannot do \`bind:${e}={undefined}\` when \`${e}\` has a fallback value
https://svelte.dev/e/props_invalid_value`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_invalid_value")}function nc(e){if(b){const t=new Error(`props_rest_readonly
Rest element properties of \`$props()\` such as \`${e}\` are readonly
https://svelte.dev/e/props_rest_readonly`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_rest_readonly")}function rc(e){if(b){const t=new Error(`rune_outside_svelte
The \`${e}\` rune is only available inside \`.svelte\` and \`.svelte.js/ts\` files
https://svelte.dev/e/rune_outside_svelte`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/rune_outside_svelte")}function ac(){if(b){const e=new Error("state_descriptors_fixed\nProperty descriptors defined on `$state` objects must contain `value` and always be `enumerable`, `configurable` and `writable`.\nhttps://svelte.dev/e/state_descriptors_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function oc(){if(b){const e=new Error("state_prototype_fixed\nCannot set prototype of `$state` object\nhttps://svelte.dev/e/state_prototype_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_prototype_fixed")}function sc(){if(b){const e=new Error("state_unsafe_mutation\nUpdating state inside `$derived(...)`, `$inspect(...)` or a template expression is forbidden. If the value should not be reactive, declare it without `$state`\nhttps://svelte.dev/e/state_unsafe_mutation");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function ic(){if(b){const e=new Error("svelte_boundary_reset_onerror\nA `<svelte:boundary>` `reset` function cannot be called while an error is still being handled\nhttps://svelte.dev/e/svelte_boundary_reset_onerror");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const lc=1,uc=2,ws=4,cc=8,dc=16,fc=1,hc=4,pc=8,mc=16,_c=1,vc=2,se=Symbol(),gc=Symbol("filename"),qs="http://www.w3.org/1999/xhtml",bc="http://www.w3.org/2000/svg",yc="@attach";var Yn="font-weight: bold",Qn="font-weight: normal";function wc(){b?console.warn(`%c[svelte] lifecycle_double_unmount
%cTried to unmount a component that was not mounted
https://svelte.dev/e/lifecycle_double_unmount`,Yn,Qn):console.warn("https://svelte.dev/e/lifecycle_double_unmount")}function qc(){b?console.warn("%c[svelte] select_multiple_invalid_value\n%cThe `value` property of a `<select multiple>` element should be an array, but it received a non-array value. The selection will be kept as is.\nhttps://svelte.dev/e/select_multiple_invalid_value",Yn,Qn):console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function ka(e){b?console.warn(`%c[svelte] state_proxy_equality_mismatch
%cReactive \`$state(...)\` proxies and the values they proxy have different identities. Because of this, comparisons with \`${e}\` will produce unexpected results
https://svelte.dev/e/state_proxy_equality_mismatch`,Yn,Qn):console.warn("https://svelte.dev/e/state_proxy_equality_mismatch")}function Sc(){b?console.warn(`%c[svelte] state_proxy_unmount
%cTried to unmount a state proxy, rather than a component
https://svelte.dev/e/state_proxy_unmount`,Yn,Qn):console.warn("https://svelte.dev/e/state_proxy_unmount")}function Mc(){b?console.warn("%c[svelte] svelte_boundary_reset_noop\n%cA `<svelte:boundary>` `reset` function only resets the boundary the first time it is called\nhttps://svelte.dev/e/svelte_boundary_reset_noop",Yn,Qn):console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function Ss(e){return e===this.v}function kc(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Ms(e){return!kc(e,this.v)}let Ac=!1;function Ye(e,t){return e.label=t,ks(e.v,t),e}function ks(e,t){var n;return(n=e==null?void 0:e[gs])==null||n.call(e,t),e}function Ec(e){const t=new Error,n=Pc();return n.length===0?null:(n.unshift(`
`),Bt(t,"stack",{value:n.join(`
`)}),Bt(t,"name",{value:e}),t)}function Pc(){const e=Error.stackTraceLimit;Error.stackTraceLimit=1/0;const t=new Error().stack;if(Error.stackTraceLimit=e,!t)return[];const n=t.split(`
`),r=[];for(let a=0;a<n.length;a++){const o=n[a],s=o.replaceAll("\\","/");if(o.trim()!=="Error"){if(o.includes("validate_each_keys"))return[];s.includes("svelte/src/internal")||s.includes("node_modules/.vite")||r.push(o)}}return r}let Y=null;function fn(e){Y=e}let hn=null;function Or(e){hn=e}let Zn=null;function As(e){Zn=e}function Fc(e){return Nc("getContext").get(e)}function I(e,t=!1,n){Y={p:Y,i:!1,c:null,e:null,s:e,x:null,l:null},b&&(Y.function=n,Zn=n)}function B(e){var t=Y,n=t.e;if(n!==null){t.e=null;for(var r of n)Ys(r)}return t.i=!0,Y=t.p,b&&(Zn=(Y==null?void 0:Y.function)??null),{}}function Es(){return!0}function Nc(e){return Y===null&&bs(e),Y.c??(Y.c=new Map(Cc(Y)||void 0))}function Cc(e){let t=e.p;for(;t!==null;){const n=t.c;if(n!==null)return n;t=t.p}return null}let pn=[];function xc(){var e=pn;pn=[],Wu(e)}function Qe(e){if(pn.length===0){var t=pn;queueMicrotask(()=>{t===pn&&xc()})}pn.push(e)}const Aa=new WeakMap;function Ps(e){var t=O;if(t===null)return x.f|=At,e;if(b&&e instanceof Error&&!Aa.has(e)&&Aa.set(e,Tc(e,t)),(t.f&Vt)===0&&(t.f&Kn)===0)throw b&&!t.parent&&e instanceof Error&&Fs(e),e;Et(e,t)}function Et(e,t){for(;t!==null;){if((t.f&qa)!==0){if((t.f&Vt)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw b&&e instanceof Error&&Fs(e),e}function Tc(e,t){var s,i,l;const n=lt(e,"message");if(!(n&&!n.configurable)){for(var r=Ra?"  ":"	",a=`
${r}in ${((s=t.fn)==null?void 0:s.name)||"<unknown>"}`,o=t.ctx;o!==null;)a+=`
${r}in ${(i=o.function)==null?void 0:i[gc].split("/").pop()}`,o=o.p;return{message:e.message+`
${a}
`,stack:(l=e.stack)==null?void 0:l.split(`
`).filter(c=>!c.includes("svelte/src/internal")).join(`
`)}}}function Fs(e){const t=Aa.get(e);t&&(Bt(e,"message",{value:t.message}),Bt(e,"stack",{value:t.stack}))}const Rc=-7169;function J(e,t){e.f=e.f&Rc|t}function Ea(e){(e.f&Fe)!==0||e.deps===null?J(e,oe):J(e,Be)}function Ns(e){if(e!==null)for(const t of e)(t.f&ue)===0||(t.f&kt)===0||(t.f^=kt,Ns(t.deps))}function Cs(e,t,n){(e.f&ce)!==0?t.add(e):(e.f&Be)!==0&&n.add(e),Ns(e.deps),J(e,oe)}const Lr=new Set;let L=null,de=null,Ne=[],Pa=null,Fa=!1;const io=class io{constructor(){D(this,Ae);ot(this,"current",new Map);ot(this,"previous",new Map);D(this,qn,new Set);D(this,Sn,new Set);D(this,Qt,0);D(this,Mn,0);D(this,dr,null);D(this,fr,new Set);D(this,Zt,new Set);D(this,mt,new Map);ot(this,"is_fork",!1);D(this,kn,!1)}skip_effect(t){h(this,mt).has(t)||h(this,mt).set(t,{d:[],m:[]})}unskip_effect(t){var n=h(this,mt).get(t);if(n){h(this,mt).delete(t);for(var r of n.d)J(r,ce),Ve(r);for(r of n.m)J(r,Be),Ve(r)}}process(t){var a;Ne=[],this.apply();var n=[],r=[];for(const o of t)le(this,Ae,vo).call(this,o,n,r);if(le(this,Ae,_o).call(this)){le(this,Ae,go).call(this,r),le(this,Ae,go).call(this,n);for(const[o,s]of h(this,mt))Ds(o,s)}else{for(const o of h(this,qn))o();h(this,qn).clear(),h(this,Qt)===0&&le(this,Ae,el).call(this),L=null,xs(r),xs(n),(a=h(this,dr))==null||a.resolve()}de=null}capture(t,n){n!==se&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&At)===0&&(this.current.set(t,t.v),de==null||de.set(t,t.v))}activate(){L=this,this.apply()}deactivate(){L===this&&(L=null,de=null)}flush(){if(this.activate(),Ne.length>0){if(Dc(),L!==null&&L!==this)return}else h(this,Qt)===0&&this.process([]);this.deactivate()}discard(){for(const t of h(this,Sn))t(this);h(this,Sn).clear()}increment(t){C(this,Qt,h(this,Qt)+1),t&&C(this,Mn,h(this,Mn)+1)}decrement(t){C(this,Qt,h(this,Qt)-1),t&&C(this,Mn,h(this,Mn)-1),!h(this,kn)&&(C(this,kn,!0),Qe(()=>{C(this,kn,!1),le(this,Ae,_o).call(this)?Ne.length>0&&this.flush():this.revive()}))}revive(){for(const t of h(this,fr))h(this,Zt).delete(t),J(t,ce),Ve(t);for(const t of h(this,Zt))J(t,Be),Ve(t);this.flush()}oncommit(t){h(this,qn).add(t)}ondiscard(t){h(this,Sn).add(t)}settled(){return(h(this,dr)??C(this,dr,ms())).promise}static ensure(){if(L===null){const t=L=new io;Lr.add(L),Qe(()=>{L===t&&t.flush()})}return L}apply(){}};qn=new WeakMap,Sn=new WeakMap,Qt=new WeakMap,Mn=new WeakMap,dr=new WeakMap,fr=new WeakMap,Zt=new WeakMap,mt=new WeakMap,kn=new WeakMap,Ae=new WeakSet,_o=function(){return this.is_fork||h(this,Mn)>0},vo=function(t,n,r){t.f^=oe;for(var a=t.first;a!==null;){var o=a.f,s=(o&(Ie|Gt))!==0,i=s&&(o&oe)!==0,l=i||(o&Me)!==0||h(this,mt).has(a);if(!l&&a.fn!==null){s?a.f^=oe:(o&Kn)!==0?n.push(a):rr(a)&&((o&ut)!==0&&h(this,Zt).add(a),bn(a));var c=a.first;if(c!==null){a=c;continue}}for(;a!==null;){var d=a.next;if(d!==null){a=d;break}a=a.parent}}},go=function(t){for(var n=0;n<t.length;n+=1)Cs(t[n],h(this,fr),h(this,Zt))},el=function(){var a;if(Lr.size>1){this.previous.clear();var t=de,n=!0;for(const o of Lr){if(o===this){n=!1;continue}const s=[];for(const[l,c]of this.current){if(o.current.has(l))if(n&&c!==o.current.get(l))o.current.set(l,c);else continue;s.push(l)}if(s.length===0)continue;const i=[...o.current.keys()].filter(l=>!this.current.has(l));if(i.length>0){var r=Ne;Ne=[];const l=new Set,c=new Map;for(const d of s)Ts(d,i,l,c);if(Ne.length>0){L=o,o.apply();for(const d of Ne)le(a=o,Ae,vo).call(a,d,[],[]);o.deactivate()}Ne=r}}L=null,de=t}Lr.delete(this)};let Pt=io;function Dc(){Fa=!0;var e=b?new Set:null;try{for(var t=0;Ne.length>0;){var n=Pt.ensure();if(t++>1e3){if(b){var r=new Map;for(const o of n.current.keys())for(const[s,i]of o.updated??[]){var a=r.get(s);a||(a={error:i.error,count:0},r.set(s,a)),a.count+=i.count}for(const o of r.values())o.error&&console.error(o.error)}Oc()}if(n.process(Ne),Ft.clear(),b)for(const o of n.current.keys())e.add(o)}}finally{if(Ne=[],Fa=!1,Pa=null,b)for(const o of e)o.updated=null}}function Oc(){try{zu()}catch(e){b&&Bt(e,"stack",{value:""}),Et(e,Pa)}}let Ge=null;function xs(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var r=e[n++];if((r.f&(ct|Me))===0&&rr(r)&&(Ge=new Set,bn(r),r.deps===null&&r.first===null&&r.nodes===null&&r.teardown===null&&r.ac===null&&zs(r),(Ge==null?void 0:Ge.size)>0)){Ft.clear();for(const a of Ge){if((a.f&(ct|Me))!==0)continue;const o=[a];let s=a.parent;for(;s!==null;)Ge.has(s)&&(Ge.delete(s),o.push(s)),s=s.parent;for(let i=o.length-1;i>=0;i--){const l=o[i];(l.f&(ct|Me))===0&&bn(l)}}Ge.clear()}}Ge=null}}function Ts(e,t,n,r){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const a of e.reactions){const o=a.f;(o&ue)!==0?Ts(a,t,n,r):(o&(Dr|ut))!==0&&(o&ce)===0&&Rs(a,t,r)&&(J(a,ce),Ve(a))}}function Rs(e,t,n){const r=n.get(e);if(r!==void 0)return r;if(e.deps!==null)for(const a of e.deps){if(It.call(t,a))return!0;if((a.f&ue)!==0&&Rs(a,t,n))return n.set(a,!0),!0}return n.set(e,!1),!1}function Ve(e){var t=Pa=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(Kn|Tr|wa))!==0&&(e.f&Vt)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var r=t.f;if(Fa&&t===O&&(r&ut)!==0&&(r&_s)===0&&(r&Vt)!==0)return;if((r&(Gt|Ie))!==0){if((r&oe)===0)return;t.f^=oe}}Ne.push(t)}function Ds(e,t){if(!((e.f&Ie)!==0&&(e.f&oe)!==0)){(e.f&ce)!==0?t.d.push(e):(e.f&Be)!==0&&t.m.push(e),J(e,oe);for(var n=e.first;n!==null;)Ds(n,t),n=n.next}}function Lc(e){let t=0,n=Wt(0),r;return b&&Ye(n,"createSubscriber version"),()=>{Oa()&&(S(n),Qs(()=>(t===0&&(r=Gr(()=>e(()=>zn(n)))),t+=1,()=>{Qe(()=>{t-=1,t===0&&(r==null||r(),r=void 0,zn(n))})})))}}var Ic=Mt|dn;function Bc(e,t,n,r){new Gc(e,t,n,r)}class Gc{constructor(t,n,r,a){D(this,ae);ot(this,"parent");ot(this,"is_pending",!1);ot(this,"transform_error");D(this,Re);D(this,lo,null);D(this,Je);D(this,Jt);D(this,be);D(this,ze,null);D(this,Ee,null);D(this,$e,null);D(this,_t,null);D(this,zt,0);D(this,Rt,0);D(this,An,!1);D(this,En,new Set);D(this,Pn,new Set);D(this,et,null);D(this,$r,Lc(()=>(C(this,et,Wt(h(this,zt))),b&&Ye(h(this,et),"$effect.pending()"),()=>{C(this,et,null)})));var o;C(this,Re,t),C(this,Je,n),C(this,Jt,s=>{var i=O;i.b=this,i.f|=qa,r(s)}),this.parent=O.b,this.transform_error=a??((o=this.parent)==null?void 0:o.transform_error)??(s=>s),C(this,be,nr(()=>{le(this,ae,bo).call(this)},Ic))}defer_effect(t){Cs(t,h(this,En),h(this,Pn))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!h(this,Je).pending}update_pending_count(t){le(this,ae,yo).call(this,t),C(this,zt,h(this,zt)+t),!(!h(this,et)||h(this,An))&&(C(this,An,!0),Qe(()=>{C(this,An,!1),h(this,et)&&_n(h(this,et),h(this,zt))}))}get_effect_pending(){return h(this,$r).call(this),S(h(this,et))}error(t){var n=h(this,Je).onerror;let r=h(this,Je).failed;if(!n&&!r)throw t;h(this,ze)&&(fe(h(this,ze)),C(this,ze,null)),h(this,Ee)&&(fe(h(this,Ee)),C(this,Ee,null)),h(this,$e)&&(fe(h(this,$e)),C(this,$e,null));var a=!1,o=!1;const s=()=>{if(a){Mc();return}a=!0,o&&ic(),h(this,$e)!==null&&$t(h(this,$e),()=>{C(this,$e,null)}),le(this,ae,ea).call(this,()=>{Pt.ensure(),le(this,ae,bo).call(this)})},i=l=>{try{o=!0,n==null||n(l,s),o=!1}catch(c){Et(c,h(this,be)&&h(this,be).parent)}r&&C(this,$e,le(this,ae,ea).call(this,()=>{Pt.ensure();try{return ve(()=>{var c=O;c.b=this,c.f|=qa,r(h(this,Re),()=>l,()=>s)})}catch(c){return Et(c,h(this,be).parent),null}}))};Qe(()=>{var l;try{l=this.transform_error(t)}catch(c){Et(c,h(this,be)&&h(this,be).parent);return}l!==null&&typeof l=="object"&&typeof l.then=="function"?l.then(i,c=>Et(c,h(this,be)&&h(this,be).parent)):i(l)})}}Re=new WeakMap,lo=new WeakMap,Je=new WeakMap,Jt=new WeakMap,be=new WeakMap,ze=new WeakMap,Ee=new WeakMap,$e=new WeakMap,_t=new WeakMap,zt=new WeakMap,Rt=new WeakMap,An=new WeakMap,En=new WeakMap,Pn=new WeakMap,et=new WeakMap,$r=new WeakMap,ae=new WeakSet,Fh=function(){try{C(this,ze,ve(()=>h(this,Jt).call(this,h(this,Re))))}catch(t){this.error(t)}},Nh=function(t){const n=h(this,Je).failed;n&&C(this,$e,ve(()=>{n(h(this,Re),()=>t,()=>()=>{})}))},Ch=function(){const t=h(this,Je).pending;t&&(this.is_pending=!0,C(this,Ee,ve(()=>t(h(this,Re)))),Qe(()=>{var n=C(this,_t,document.createDocumentFragment()),r=ht();n.append(r),C(this,ze,le(this,ae,ea).call(this,()=>(Pt.ensure(),ve(()=>h(this,Jt).call(this,r))))),h(this,Rt)===0&&(h(this,Re).before(n),C(this,_t,null),$t(h(this,Ee),()=>{C(this,Ee,null)}),le(this,ae,zr).call(this))}))},bo=function(){try{if(this.is_pending=this.has_pending_snippet(),C(this,Rt,0),C(this,zt,0),C(this,ze,ve(()=>{h(this,Jt).call(this,h(this,Re))})),h(this,Rt)>0){var t=C(this,_t,document.createDocumentFragment());ni(h(this,ze),t);const n=h(this,Je).pending;C(this,Ee,ve(()=>n(h(this,Re))))}else le(this,ae,zr).call(this)}catch(n){this.error(n)}},zr=function(){this.is_pending=!1;for(const t of h(this,En))J(t,ce),Ve(t);for(const t of h(this,Pn))J(t,Be),Ve(t);h(this,En).clear(),h(this,Pn).clear()},ea=function(t){var n=O,r=x,a=Y;We(h(this,be)),Ce(h(this,be)),fn(h(this,be).ctx);try{return t()}catch(o){return Ps(o),null}finally{We(n),Ce(r),fn(a)}},yo=function(t){var n;if(!this.has_pending_snippet()){this.parent&&le(n=this.parent,ae,yo).call(n,t);return}C(this,Rt,h(this,Rt)+t),h(this,Rt)===0&&(le(this,ae,zr).call(this),h(this,Ee)&&$t(h(this,Ee),()=>{C(this,Ee,null)}),h(this,_t)&&(h(this,Re).before(h(this,_t)),C(this,_t,null)))};function Os(e,t,n,r){const a=Ir;var o=e.filter(u=>!u.settled);if(n.length===0&&o.length===0){r(t.map(a));return}var s=O,i=Vc(),l=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(u=>u.promise)):null;function c(u){i();try{r(u)}catch(f){(s.f&ct)===0&&Et(f,s)}Na()}if(n.length===0){l.then(()=>c(t.map(a)));return}function d(){i(),Promise.all(n.map(u=>jc(u))).then(u=>c([...t.map(a),...u])).catch(u=>Et(u,s))}l?l.then(d):d()}function Vc(){var e=O,t=x,n=Y,r=L;if(b)var a=hn;return function(s=!0){We(e),Ce(t),fn(n),s&&(r==null||r.activate()),b&&Or(a)}}function Na(e=!0){We(null),Ce(null),fn(null),e&&(L==null||L.deactivate()),b&&Or(null)}function Hc(){var e=O.b,t=L,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}const Wc=new Set;function Ir(e){var t=ue|ce,n=x!==null&&(x.f&ue)!==0?x:null;return O!==null&&(O.f|=dn),{ctx:Y,deps:null,effects:null,equals:Ss,f:t,fn:e,reactions:null,rv:0,v:se,wv:0,parent:n??O,ac:null}}function jc(e,t,n){O===null&&Xu();var a=void 0,o=Wt(se);b&&(o.label=t);var s=!x,i=new Map;return id(()=>{var f;var l=ms();a=l.promise;try{Promise.resolve(e()).then(l.resolve,l.reject).finally(Na)}catch(_){l.reject(_),Na()}var c=L;if(s){var d=Hc();(f=i.get(c))==null||f.reject(Ht),i.delete(c),i.set(c,l)}const u=(_,m=void 0)=>{if(c.activate(),m)m!==Ht&&(o.f|=At,_n(o,m));else{(o.f&At)!==0&&(o.f^=At),_n(o,_);for(const[w,p]of i){if(i.delete(w),w===c)break;p.reject(Ht)}}d&&d()};l.promise.then(u,_=>u(null,_||"unknown"))}),La(()=>{for(const l of i.values())l.reject(Ht)}),b&&(o.f|=Dr),new Promise(l=>{function c(d){function u(){d===a?l(o):c(a)}d.then(u,u)}c(a)})}function Jn(e){const t=Ir(e);return ai(t),t}function Ls(e){const t=Ir(e);return t.equals=Ms,t}function Is(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)fe(t[n])}}let Ca=[];function $c(e){for(var t=e.parent;t!==null;){if((t.f&ue)===0)return(t.f&ct)===0?t:null;t=t.parent}return null}function xa(e){var t,n=O;if(We($c(e)),b){let r=mn;Vs(new Set);try{It.call(Ca,e)&&Ku(),Ca.push(e),e.f&=~kt,Is(e),t=Va(e)}finally{We(n),Vs(r),Ca.pop()}}else try{e.f&=~kt,Is(e),t=Va(e)}finally{We(n)}return t}function Bs(e){var t=xa(e);if(!e.equals(t)&&(e.wv=ii(),(!(L!=null&&L.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){J(e,oe);return}Nt||(de!==null?(Oa()||L!=null&&L.is_fork)&&de.set(e,t):Ea(e))}function Uc(e){var t,n;if(e.effects!==null)for(const r of e.effects)(r.teardown||r.ac)&&((t=r.teardown)==null||t.call(r),(n=r.ac)==null||n.abort(Ht),r.teardown=$,r.ac=null,ar(r,0),Ba(r))}function Gs(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&bn(t)}let mn=new Set;const Ft=new Map;function Vs(e){mn=e}let Ta=!1;function Xc(){Ta=!0}function Wt(e,t){var n={f:0,v:e,reactions:null,equals:Ss,rv:0,wv:0};return n}function _e(e,t){const n=Wt(e);return ai(n),n}function Kc(e,t=!1,n=!0){const r=Wt(e);return t||(r.equals=Ms),r}function te(e,t,n=!1){x!==null&&(!He||(x.f&Rr)!==0)&&Es()&&(x.f&(ue|ut|Dr|Rr))!==0&&(xe===null||!It.call(xe,e))&&sc();let r=n?vn(t):t;return b&&ks(r,e.label),_n(e,r)}function _n(e,t){var a;if(!e.equals(t)){var n=e.v;Nt?Ft.set(e,t):Ft.set(e,n),e.v=t;var r=Pt.ensure();if(r.capture(e,n),b){if(O!==null){e.updated??(e.updated=new Map);const o=(((a=e.updated.get(""))==null?void 0:a.count)??0)+1;if(e.updated.set("",{error:null,count:o}),o>5){const s=Ec("updated at");if(s!==null){let i=e.updated.get(s.stack);i||(i={error:s,count:0},e.updated.set(s.stack,i)),i.count++}}}O!==null&&(e.set_during_effect=!0)}if((e.f&ue)!==0){const o=e;(e.f&ce)!==0&&xa(o),Ea(o)}e.wv=ii(),Ws(e,ce),O!==null&&(O.f&oe)!==0&&(O.f&(Ie|Gt))===0&&(Te===null?cd([e]):Te.push(e)),!r.is_fork&&mn.size>0&&!Ta&&Hs()}return t}function Hs(){Ta=!1;for(const e of mn)(e.f&oe)!==0&&J(e,Be),rr(e)&&bn(e);mn.clear()}function zn(e){te(e,e.v+1)}function Ws(e,t){var n=e.reactions;if(n!==null)for(var r=n.length,a=0;a<r;a++){var o=n[a],s=o.f;if(b&&(s&Rr)!==0){mn.add(o);continue}var i=(s&ce)===0;if(i&&J(o,t),(s&ue)!==0){var l=o;de==null||de.delete(l),(s&kt)===0&&(s&Fe&&(o.f|=kt),Ws(l,Be))}else i&&((s&ut)!==0&&Ge!==null&&Ge.add(o),Ve(o))}}const Yc=/^[a-zA-Z_$][a-zA-Z_$0-9]*$/;function vn(e){if(typeof e!="object"||e===null||ft in e)return e;const t=hs(e);if(t!==Vu&&t!==Hu)return e;var n=new Map,r=ya(e),a=_e(0),o=Xt,s=d=>{if(Xt===o)return d();var u=x,f=Xt;Ce(null),si(o);var _=d();return Ce(u),si(f),_};r&&(n.set("length",_e(e.length)),b&&(e=Jc(e)));var i="";let l=!1;function c(d){if(!l){l=!0,i=d,Ye(a,`${i} version`);for(const[u,f]of n)Ye(f,jt(i,u));l=!1}}return new Proxy(e,{defineProperty(d,u,f){(!("value"in f)||f.configurable===!1||f.enumerable===!1||f.writable===!1)&&ac();var _=n.get(u);return _===void 0?s(()=>{var m=_e(f.value);return n.set(u,m),b&&typeof u=="string"&&Ye(m,jt(i,u)),m}):te(_,f.value,!0),!0},deleteProperty(d,u){var f=n.get(u);if(f===void 0){if(u in d){const _=s(()=>_e(se));n.set(u,_),zn(a),b&&Ye(_,jt(i,u))}}else te(f,se),zn(a);return!0},get(d,u,f){var p;if(u===ft)return e;if(b&&u===gs)return c;var _=n.get(u),m=u in d;if(_===void 0&&(!m||(p=lt(d,u))!=null&&p.writable)&&(_=s(()=>{var v=vn(m?d[u]:se),P=_e(v);return b&&Ye(P,jt(i,u)),P}),n.set(u,_)),_!==void 0){var w=S(_);return w===se?void 0:w}return Reflect.get(d,u,f)},getOwnPropertyDescriptor(d,u){var f=Reflect.getOwnPropertyDescriptor(d,u);if(f&&"value"in f){var _=n.get(u);_&&(f.value=S(_))}else if(f===void 0){var m=n.get(u),w=m==null?void 0:m.v;if(m!==void 0&&w!==se)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return f},has(d,u){var w;if(u===ft)return!0;var f=n.get(u),_=f!==void 0&&f.v!==se||Reflect.has(d,u);if(f!==void 0||O!==null&&(!_||(w=lt(d,u))!=null&&w.writable)){f===void 0&&(f=s(()=>{var p=_?vn(d[u]):se,v=_e(p);return b&&Ye(v,jt(i,u)),v}),n.set(u,f));var m=S(f);if(m===se)return!1}return _},set(d,u,f,_){var W;var m=n.get(u),w=u in d;if(r&&u==="length")for(var p=f;p<m.v;p+=1){var v=n.get(p+"");v!==void 0?te(v,se):p in d&&(v=s(()=>_e(se)),n.set(p+"",v),b&&Ye(v,jt(i,p)))}if(m===void 0)(!w||(W=lt(d,u))!=null&&W.writable)&&(m=s(()=>_e(void 0)),b&&Ye(m,jt(i,u)),te(m,vn(f)),n.set(u,m));else{w=m.v!==se;var P=s(()=>vn(f));te(m,P)}var y=Reflect.getOwnPropertyDescriptor(d,u);if(y!=null&&y.set&&y.set.call(_,f),!w){if(r&&typeof u=="string"){var M=n.get("length"),F=Number(u);Number.isInteger(F)&&F>=M.v&&te(M,F+1)}zn(a)}return!0},ownKeys(d){S(a);var u=Reflect.ownKeys(d).filter(m=>{var w=n.get(m);return w===void 0||w.v!==se});for(var[f,_]of n)_.v!==se&&!(f in d)&&u.push(f);return u},setPrototypeOf(){oc()}})}function jt(e,t){return typeof t=="symbol"?`${e}[Symbol(${t.description??""})]`:Yc.test(t)?`${e}.${t}`:/^\d+$/.test(t)?`${e}[${t}]`:`${e}['${t}']`}function er(e){try{if(e!==null&&typeof e=="object"&&ft in e)return e[ft]}catch{}return e}function Qc(e,t){return Object.is(er(e),er(t))}const Zc=new Set(["copyWithin","fill","pop","push","reverse","shift","sort","splice","unshift"]);function Jc(e){return new Proxy(e,{get(t,n,r){var a=Reflect.get(t,n,r);return Zc.has(n)?function(...o){Xc();var s=a.apply(this,o);return Hs(),s}:a}})}function zc(){const e=Array.prototype,t=Array.__svelte_cleanup;t&&t();const{indexOf:n,lastIndexOf:r,includes:a}=e;e.indexOf=function(o,s){const i=n.call(this,o,s);if(i===-1){for(let l=s??0;l<this.length;l+=1)if(er(this[l])===o){ka("array.indexOf(...)");break}}return i},e.lastIndexOf=function(o,s){const i=r.call(this,o,s??this.length-1);if(i===-1){for(let l=0;l<=(s??this.length-1);l+=1)if(er(this[l])===o){ka("array.lastIndexOf(...)");break}}return i},e.includes=function(o,s){const i=a.call(this,o,s);if(!i){for(let l=0;l<this.length;l+=1)if(er(this[l])===o){ka("array.includes(...)");break}}return i},Array.__svelte_cleanup=()=>{e.indexOf=n,e.lastIndexOf=r,e.includes=a}}var js,Ra,$s,Us;function ed(){if(js===void 0){js=window,Ra=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;$s=lt(t,"firstChild").get,Us=lt(t,"nextSibling").get,ps(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),ps(n)&&(n.__t=void 0),b&&(e.__svelte_meta=null,zc())}}function ht(e=""){return document.createTextNode(e)}function gn(e){return $s.call(e)}function tr(e){return Us.call(e)}function E(e,t){return gn(e)}function H(e,t=!1){{var n=gn(e);return n instanceof Comment&&n.data===""?tr(n):n}}function N(e,t=1,n=!1){let r=e;for(;t--;)r=tr(r);return r}function td(e){e.textContent=""}function Xs(){return!1}function Ks(e,t,n){return document.createElementNS(t??qs,e,void 0)}function nd(e,t){if(t){const n=document.body;e.autofocus=!0,Qe(()=>{document.activeElement===n&&e.focus()})}}function Da(e){var t=x,n=O;Ce(null),We(null);try{return e()}finally{Ce(t),We(n)}}function rd(e){O===null&&(x===null&&Ju(e),Zu()),Nt&&Qu(e)}function ad(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function Ze(e,t,n){var r=O;if(b)for(;r!==null&&(r.f&Rr)!==0;)r=r.parent;r!==null&&(r.f&Me)!==0&&(e|=Me);var a={ctx:Y,deps:null,nodes:null,f:e|ce|Fe,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null};if(b&&(a.component_function=Zn),n)try{bn(a)}catch(i){throw fe(a),i}else t!==null&&Ve(a);var o=a;if(n&&o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&dn)===0&&(o=o.first,(e&ut)!==0&&(e&Mt)!==0&&o!==null&&(o.f|=Mt)),o!==null&&(o.parent=r,r!==null&&ad(o,r),x!==null&&(x.f&ue)!==0&&(e&Gt)===0)){var s=x;(s.effects??(s.effects=[])).push(o)}return a}function Oa(){return x!==null&&!He}function La(e){const t=Ze(Tr,null,!1);return J(t,oe),t.teardown=e,t}function od(e){rd("$effect"),b&&Bt(e,"name",{value:"$effect"});var t=O.f,n=!x&&(t&Ie)!==0&&(t&Vt)===0;if(n){var r=Y;(r.e??(r.e=[])).push(e)}else return Ys(e)}function Ys(e){return Ze(Kn|$u,e,!1)}function sd(e){Pt.ensure();const t=Ze(Gt|dn,e,!0);return(n={})=>new Promise(r=>{n.outro?$t(t,()=>{fe(t),r(void 0)}):(fe(t),r(void 0))})}function Ia(e){return Ze(Kn,e,!1)}function id(e){return Ze(Dr|dn,e,!0)}function Qs(e,t=0){return Ze(Tr|t,e,!0)}function pt(e,t=[],n=[],r=[]){Os(r,t,n,a=>{Ze(Tr,()=>e(...a.map(S)),!0)})}function nr(e,t=0){var n=Ze(ut|t,e,!0);return b&&(n.dev_stack=hn),n}function Zs(e,t=0){var n=Ze(wa|t,e,!0);return b&&(n.dev_stack=hn),n}function ve(e){return Ze(Ie|dn,e,!0)}function Js(e){var t=e.teardown;if(t!==null){const n=Nt,r=x;ri(!0),Ce(null);try{t.call(null)}finally{ri(n),Ce(r)}}}function Ba(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const a=n.ac;a!==null&&Da(()=>{a.abort(Ht)});var r=n.next;(n.f&Gt)!==0?n.parent=null:fe(n,t),n=r}}function ld(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&Ie)===0&&fe(t),t=n}}function fe(e,t=!0){var n=!1;(t||(e.f&_s)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(ud(e.nodes.start,e.nodes.end),n=!0),Ba(e,t&&!n),ar(e,0),J(e,ct);var r=e.nodes&&e.nodes.t;if(r!==null)for(const o of r)o.stop();Js(e);var a=e.parent;a!==null&&a.first!==null&&zs(e),b&&(e.component_function=null),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function ud(e,t){for(;e!==null;){var n=e===t?null:tr(e);e.remove(),e=n}}function zs(e){var t=e.parent,n=e.prev,r=e.next;n!==null&&(n.next=r),r!==null&&(r.prev=n),t!==null&&(t.first===e&&(t.first=r),t.last===e&&(t.last=n))}function $t(e,t,n=!0){var r=[];ei(e,r,!0);var a=()=>{n&&fe(e),t&&t()},o=r.length;if(o>0){var s=()=>--o||a();for(var i of r)i.out(s)}else a()}function ei(e,t,n){if((e.f&Me)===0){e.f^=Me;var r=e.nodes&&e.nodes.t;if(r!==null)for(const i of r)(i.is_global||n)&&t.push(i);for(var a=e.first;a!==null;){var o=a.next,s=(a.f&Mt)!==0||(a.f&Ie)!==0&&(e.f&ut)!==0;ei(a,t,s?n:!1),a=o}}}function Ga(e){ti(e,!0)}function ti(e,t){if((e.f&Me)!==0){e.f^=Me,(e.f&oe)===0&&(J(e,ce),Ve(e));for(var n=e.first;n!==null;){var r=n.next,a=(n.f&Mt)!==0||(n.f&Ie)!==0;ti(n,a?t:!1),n=r}var o=e.nodes&&e.nodes.t;if(o!==null)for(const s of o)(s.is_global||t)&&s.in()}}function ni(e,t){if(e.nodes)for(var n=e.nodes.start,r=e.nodes.end;n!==null;){var a=n===r?null:tr(n);t.append(n),n=a}}let Br=!1,Nt=!1;function ri(e){Nt=e}let x=null,He=!1;function Ce(e){x=e}let O=null;function We(e){O=e}let xe=null;function ai(e){x!==null&&(xe===null?xe=[e]:xe.push(e))}let ge=null,ke=0,Te=null;function cd(e){Te=e}let oi=1,Ut=0,Xt=Ut;function si(e){Xt=e}function ii(){return++oi}function rr(e){var t=e.f;if((t&ce)!==0)return!0;if(t&ue&&(e.f&=~kt),(t&Be)!==0){for(var n=e.deps,r=n.length,a=0;a<r;a++){var o=n[a];if(rr(o)&&Bs(o),o.wv>e.wv)return!0}(t&Fe)!==0&&de===null&&J(e,oe)}return!1}function li(e,t,n=!0){var r=e.reactions;if(r!==null&&!(xe!==null&&It.call(xe,e)))for(var a=0;a<r.length;a++){var o=r[a];(o.f&ue)!==0?li(o,t,!1):t===o&&(n?J(o,ce):(o.f&oe)!==0&&J(o,Be),Ve(o))}}function Va(e){var w;var t=ge,n=ke,r=Te,a=x,o=xe,s=Y,i=He,l=Xt,c=e.f;ge=null,ke=0,Te=null,x=(c&(Ie|Gt))===0?e:null,xe=null,fn(e.ctx),He=!1,Xt=++Ut,e.ac!==null&&(Da(()=>{e.ac.abort(Ht)}),e.ac=null);try{e.f|=Sa;var d=e.fn,u=d();e.f|=Vt;var f=e.deps,_=L==null?void 0:L.is_fork;if(ge!==null){var m;if(_||ar(e,ke),f!==null&&ke>0)for(f.length=ke+ge.length,m=0;m<ge.length;m++)f[ke+m]=ge[m];else e.deps=f=ge;if(Oa()&&(e.f&Fe)!==0)for(m=ke;m<f.length;m++)((w=f[m]).reactions??(w.reactions=[])).push(e)}else!_&&f!==null&&ke<f.length&&(ar(e,ke),f.length=ke);if(Es()&&Te!==null&&!He&&f!==null&&(e.f&(ue|Be|ce))===0)for(m=0;m<Te.length;m++)li(Te[m],e);if(a!==null&&a!==e){if(Ut++,a.deps!==null)for(let p=0;p<n;p+=1)a.deps[p].rv=Ut;if(t!==null)for(const p of t)p.rv=Ut;Te!==null&&(r===null?r=Te:r.push(...Te))}return(e.f&At)!==0&&(e.f^=At),u}catch(p){return Ps(p)}finally{e.f^=Sa,ge=t,ke=n,Te=r,x=a,xe=o,fn(s),He=i,Xt=l}}function dd(e,t){let n=t.reactions;if(n!==null){var r=Bu.call(n,e);if(r!==-1){var a=n.length-1;a===0?n=t.reactions=null:(n[r]=n[a],n.pop())}}if(n===null&&(t.f&ue)!==0&&(ge===null||!It.call(ge,t))){var o=t;(o.f&Fe)!==0&&(o.f^=Fe,o.f&=~kt),Ea(o),Uc(o),ar(o,0)}}function ar(e,t){var n=e.deps;if(n!==null)for(var r=t;r<n.length;r++)dd(e,n[r])}function bn(e){var t=e.f;if((t&ct)===0){J(e,oe);var n=O,r=Br;if(O=e,Br=!0,b){var a=Zn;As(e.component_function);var o=hn;Or(e.dev_stack??hn)}try{(t&(ut|wa))!==0?ld(e):Ba(e),Js(e);var s=Va(e);e.teardown=typeof s=="function"?s:null,e.wv=oi;var i;b&&Ac&&(e.f&ce)!==0&&e.deps}finally{Br=r,O=n,b&&(As(a),Or(o))}}}function S(e){var t=e.f,n=(t&ue)!==0;if(x!==null&&!He){var r=O!==null&&(O.f&ct)!==0;if(!r&&(xe===null||!It.call(xe,e))){var a=x.deps;if((x.f&Sa)!==0)e.rv<Ut&&(e.rv=Ut,ge===null&&a!==null&&a[ke]===e?ke++:ge===null?ge=[e]:ge.push(e));else{(x.deps??(x.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[x]:It.call(o,x)||o.push(x)}}}if(b&&Wc.delete(e),Nt&&Ft.has(e))return Ft.get(e);if(n){var s=e;if(Nt){var i=s.v;return((s.f&oe)===0&&s.reactions!==null||ci(s))&&(i=xa(s)),Ft.set(s,i),i}var l=(s.f&Fe)===0&&!He&&x!==null&&(Br||(x.f&Fe)!==0),c=(s.f&Vt)===0;rr(s)&&(l&&(s.f|=Fe),Bs(s)),l&&!c&&(Gs(s),ui(s))}if(de!=null&&de.has(e))return de.get(e);if((e.f&At)!==0)throw e.v;return e.v}function ui(e){if(e.f|=Fe,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&ue)!==0&&(t.f&Fe)===0&&(Gs(t),ui(t))}function ci(e){if(e.v===se)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(Ft.has(t)||(t.f&ue)!==0&&ci(t))return!0;return!1}function Gr(e){var t=He;try{return He=!0,e()}finally{He=t}}function fd(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const hd=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function pd(e){return hd.includes(e)}const md={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function _d(e){return e=e.toLowerCase(),md[e]??e}const vd=["touchstart","touchmove"];function gd(e){return vd.includes(e)}const Kt=Symbol("events"),di=new Set,Ha=new Set;function bd(e,t,n,r={}){function a(o){if(r.capture||ja.call(t,o),!o.cancelBubble)return Da(()=>n==null?void 0:n.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Qe(()=>{t.addEventListener(e,a,r)}):t.addEventListener(e,a,r),a}function me(e,t,n){(t[Kt]??(t[Kt]={}))[e]=n}function Wa(e){for(var t=0;t<e.length;t++)di.add(e[t]);for(var n of Ha)n(e)}let fi=null;function ja(e){var p,v;var t=this,n=t.ownerDocument,r=e.type,a=((p=e.composedPath)==null?void 0:p.call(e))||[],o=a[0]||e.target;fi=e;var s=0,i=fi===e&&e[Kt];if(i){var l=a.indexOf(i);if(l!==-1&&(t===document||t===window)){e[Kt]=t;return}var c=a.indexOf(t);if(c===-1)return;l<=c&&(s=l)}if(o=a[s]||e.target,o!==t){Bt(e,"currentTarget",{configurable:!0,get(){return o||n}});var d=x,u=O;Ce(null),We(null);try{for(var f,_=[];o!==null;){var m=o.assignedSlot||o.parentNode||o.host||null;try{var w=(v=o[Kt])==null?void 0:v[r];w!=null&&(!o.disabled||e.target===o)&&w.call(o,e)}catch(P){f?_.push(P):f=P}if(e.cancelBubble||m===t||m===null)break;o=m}if(f){for(let P of _)queueMicrotask(()=>{throw P});throw f}}finally{e[Kt]=t,delete e.currentTarget,Ce(d),We(u)}}}const $a=((Hi=globalThis==null?void 0:globalThis.window)==null?void 0:Hi.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function yd(e){return($a==null?void 0:$a.createHTML(e))??e}function hi(e){var t=Ks("template");return t.innerHTML=yd(e.replaceAll("<!>","<!---->")),t.content}function or(e,t){var n=O;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function je(e,t){var n=(t&_c)!==0,r=(t&vc)!==0,a,o=!e.startsWith("<!>");return()=>{a===void 0&&(a=hi(o?e:"<!>"+e),n||(a=gn(a)));var s=r||Ra?document.importNode(a,!0):a.cloneNode(!0);if(n){var i=gn(s),l=s.lastChild;or(i,l)}else or(s,s);return s}}function wd(e,t,n="svg"){var r=!e.startsWith("<!>"),a=`<${n}>${r?e:"<!>"+e}</${n}>`,o;return()=>{if(!o){var s=hi(a),i=gn(s);o=gn(i)}var l=o.cloneNode(!0);return or(l,l),l}}function qd(e,t){return wd(e,t,"svg")}function U(){var e=document.createDocumentFragment(),t=document.createComment(""),n=ht();return e.append(t,n),or(t,n),e}function R(e,t){e!==null&&e.before(t)}function Ct(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function Sd(e,t){return Md(e,t)}const Vr=new Map;function Md(e,{target:t,anchor:n,props:r={},events:a,context:o,intro:s=!0,transformError:i}){ed();var l=void 0,c=sd(()=>{var d=n??t.appendChild(ht());Bc(d,{pending:()=>{}},_=>{I({});var m=Y;o&&(m.c=o),a&&(r.$$events=a),l=e(_,r)||{},B()},i);var u=new Set,f=_=>{for(var m=0;m<_.length;m++){var w=_[m];if(!u.has(w)){u.add(w);var p=gd(w);for(const y of[t,document]){var v=Vr.get(y);v===void 0&&(v=new Map,Vr.set(y,v));var P=v.get(w);P===void 0?(y.addEventListener(w,ja,{passive:p}),v.set(w,1)):v.set(w,P+1)}}}};return f(xr(di)),Ha.add(f),()=>{var p;for(var _ of u)for(const v of[t,document]){var m=Vr.get(v),w=m.get(_);--w==0?(v.removeEventListener(_,ja),m.delete(_),m.size===0&&Vr.delete(v)):m.set(_,w)}Ha.delete(f),d!==n&&((p=d.parentNode)==null||p.removeChild(d))}});return Ua.set(l,c),l}let Ua=new WeakMap;function pi(e,t){const n=Ua.get(e);return n?(Ua.delete(e),n(t)):(b&&(ft in e?Sc():wc()),Promise.resolve())}class Xa{constructor(t,n=!0){ot(this,"anchor");D(this,Ue,new Map);D(this,tt,new Map);D(this,Pe,new Map);D(this,en,new Set);D(this,hr,!0);D(this,pr,()=>{var t=L;if(h(this,Ue).has(t)){var n=h(this,Ue).get(t),r=h(this,tt).get(n);if(r)Ga(r),h(this,en).delete(n);else{var a=h(this,Pe).get(n);a&&(h(this,tt).set(n,a.effect),h(this,Pe).delete(n),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),r=a.effect)}for(const[o,s]of h(this,Ue)){if(h(this,Ue).delete(o),o===t)break;const i=h(this,Pe).get(s);i&&(fe(i.effect),h(this,Pe).delete(s))}for(const[o,s]of h(this,tt)){if(o===n||h(this,en).has(o))continue;const i=()=>{if(Array.from(h(this,Ue).values()).includes(o)){var c=document.createDocumentFragment();ni(s,c),c.append(ht()),h(this,Pe).set(o,{effect:s,fragment:c})}else fe(s);h(this,en).delete(o),h(this,tt).delete(o)};h(this,hr)||!r?(h(this,en).add(o),$t(s,i,!1)):i()}}});D(this,Ur,t=>{h(this,Ue).delete(t);const n=Array.from(h(this,Ue).values());for(const[r,a]of h(this,Pe))n.includes(r)||(fe(a.effect),h(this,Pe).delete(r))});this.anchor=t,C(this,hr,n)}ensure(t,n){var r=L,a=Xs();if(n&&!h(this,tt).has(t)&&!h(this,Pe).has(t))if(a){var o=document.createDocumentFragment(),s=ht();o.append(s),h(this,Pe).set(t,{effect:ve(()=>n(s)),fragment:o})}else h(this,tt).set(t,ve(()=>n(this.anchor)));if(h(this,Ue).set(r,t),a){for(const[i,l]of h(this,tt))i===t?r.unskip_effect(l):r.skip_effect(l);for(const[i,l]of h(this,Pe))i===t?r.unskip_effect(l.effect):r.skip_effect(l.effect);r.oncommit(h(this,pr)),r.ondiscard(h(this,Ur))}else h(this,pr).call(this)}}Ue=new WeakMap,tt=new WeakMap,Pe=new WeakMap,en=new WeakMap,hr=new WeakMap,pr=new WeakMap,Ur=new WeakMap;function Yt(e,t,n=!1){var r=new Xa(e),a=n?Mt:0;function o(s,i){r.ensure(s,i)}nr(()=>{var s=!1;t((i,l=0)=>{s=!0,o(l,i)}),s||o(!1,null)},a)}function Ka(e,t){return t}function kd(e,t,n){for(var r=[],a=t.length,o,s=t.length,i=0;i<a;i++){let u=t[i];$t(u,()=>{if(o){if(o.pending.delete(u),o.done.add(u),o.pending.size===0){var f=e.outrogroups;Ya(xr(o.done)),f.delete(o),f.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var l=r.length===0&&n!==null;if(l){var c=n,d=c.parentNode;td(d),d.append(c),e.items.clear()}Ya(t,!l)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function Ya(e,t=!0){for(var n=0;n<e.length;n++)fe(e[n],t)}var mi;function Hr(e,t,n,r,a,o=null){var s=e,i=new Map,l=(t&ws)!==0;if(l){var c=e;s=c.appendChild(ht())}var d=null,u=Ls(()=>{var v=n();return ya(v)?v:v==null?[]:xr(v)}),f,_=!0;function m(){p.fallback=d,Ad(p,f,s,t,r),d!==null&&(f.length===0?(d.f&dt)===0?Ga(d):(d.f^=dt,ir(d,null,s)):$t(d,()=>{d=null}))}var w=nr(()=>{f=S(u);for(var v=f.length,P=new Set,y=L,M=Xs(),F=0;F<v;F+=1){var W=f[F],T=r(W,F);if(b){var ye=r(W,F);T!==ye&&Yu(String(F),String(T),String(ye))}var ne=_?null:i.get(T);ne?(ne.v&&_n(ne.v,W),ne.i&&_n(ne.i,F),M&&y.unskip_effect(ne.e)):(ne=Ed(i,_?s:mi??(mi=ht()),W,T,F,a,t,n),_||(ne.e.f|=dt),i.set(T,ne)),P.add(T)}if(v===0&&o&&!d&&(_?d=ve(()=>o(s)):(d=ve(()=>o(mi??(mi=ht()))),d.f|=dt)),v>P.size&&(b?Pd(f,r):ys("","","")),!_)if(M){for(const[De,Oe]of i)P.has(De)||y.skip_effect(Oe.e);y.oncommit(m),y.ondiscard(()=>{})}else m();S(u)}),p={effect:w,items:i,outrogroups:null,fallback:d};_=!1}function sr(e){for(;e!==null&&(e.f&Ie)===0;)e=e.next;return e}function Ad(e,t,n,r,a){var De,Oe,g,Dt,Fn,Nn,we,Cn,xn;var o=(r&cc)!==0,s=t.length,i=e.items,l=sr(e.effect.first),c,d=null,u,f=[],_=[],m,w,p,v;if(o)for(v=0;v<s;v+=1)m=t[v],w=a(m,v),p=i.get(w).e,(p.f&dt)===0&&((Oe=(De=p.nodes)==null?void 0:De.a)==null||Oe.measure(),(u??(u=new Set)).add(p));for(v=0;v<s;v+=1){if(m=t[v],w=a(m,v),p=i.get(w).e,e.outrogroups!==null)for(const qe of e.outrogroups)qe.pending.delete(p),qe.done.delete(p);if((p.f&dt)!==0)if(p.f^=dt,p===l)ir(p,null,n);else{var P=d?d.next:l;p===e.effect.last&&(e.effect.last=p.prev),p.prev&&(p.prev.next=p.next),p.next&&(p.next.prev=p.prev),xt(e,d,p),xt(e,p,P),ir(p,P,n),d=p,f=[],_=[],l=sr(d.next);continue}if((p.f&Me)!==0&&(Ga(p),o&&((Dt=(g=p.nodes)==null?void 0:g.a)==null||Dt.unfix(),(u??(u=new Set)).delete(p))),p!==l){if(c!==void 0&&c.has(p)){if(f.length<_.length){var y=_[0],M;d=y.prev;var F=f[0],W=f[f.length-1];for(M=0;M<f.length;M+=1)ir(f[M],y,n);for(M=0;M<_.length;M+=1)c.delete(_[M]);xt(e,F.prev,W.next),xt(e,d,F),xt(e,W,y),l=y,d=W,v-=1,f=[],_=[]}else c.delete(p),ir(p,l,n),xt(e,p.prev,p.next),xt(e,p,d===null?e.effect.first:d.next),xt(e,d,p),d=p;continue}for(f=[],_=[];l!==null&&l!==p;)(c??(c=new Set)).add(l),_.push(l),l=sr(l.next);if(l===null)continue}(p.f&dt)===0&&f.push(p),d=p,l=sr(p.next)}if(e.outrogroups!==null){for(const qe of e.outrogroups)qe.pending.size===0&&(Ya(xr(qe.done)),(Fn=e.outrogroups)==null||Fn.delete(qe));e.outrogroups.size===0&&(e.outrogroups=null)}if(l!==null||c!==void 0){var T=[];if(c!==void 0)for(p of c)(p.f&Me)===0&&T.push(p);for(;l!==null;)(l.f&Me)===0&&l!==e.fallback&&T.push(l),l=sr(l.next);var ye=T.length;if(ye>0){var ne=(r&ws)!==0&&s===0?n:null;if(o){for(v=0;v<ye;v+=1)(we=(Nn=T[v].nodes)==null?void 0:Nn.a)==null||we.measure();for(v=0;v<ye;v+=1)(xn=(Cn=T[v].nodes)==null?void 0:Cn.a)==null||xn.fix()}kd(e,T,ne)}}o&&Qe(()=>{var qe,A;if(u!==void 0)for(p of u)(A=(qe=p.nodes)==null?void 0:qe.a)==null||A.apply()})}function Ed(e,t,n,r,a,o,s,i){var l=(s&lc)!==0?(s&dc)===0?Kc(n,!1,!1):Wt(n):null,c=(s&uc)!==0?Wt(a):null;return b&&l&&(l.trace=()=>{i()[(c==null?void 0:c.v)??a]}),{v:l,i:c,e:ve(()=>(o(t,l??n,c??a,i),()=>{e.delete(r)}))}}function ir(e,t,n){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end,o=t&&(t.f&dt)===0?t.nodes.start:n;r!==null;){var s=tr(r);if(o.before(r),r===a)return;r=s}}function xt(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function Pd(e,t){const n=new Map,r=e.length;for(let a=0;a<r;a++){const o=t(e[a],a);if(n.has(o)){const s=String(n.get(o)),i=String(a);let l=String(o);l.startsWith("[object ")&&(l=null),ys(s,i,l)}n.set(o,a)}}function X(e,t,...n){var r=new Xa(e);nr(()=>{const a=t()??null;b&&a==null&&ec(),r.ensure(a,a&&(o=>a(o,...n)))},Mt)}function Fd(e,t,n,r,a,o){var s=null,i=e,l=new Xa(i,!1);nr(()=>{const c=t()||null;var d=bc;if(c===null){l.ensure(null,null);return}return l.ensure(c,u=>{if(c){if(s=Ks(c,d),or(s,s),r){var f=s.appendChild(ht());r(s,f)}O.nodes.end=s,u.before(s)}}),()=>{}},Mt),La(()=>{})}function Nd(e,t){var n=void 0,r;Zs(()=>{n!==(n=t())&&(r&&(fe(r),r=null),n&&(r=ve(()=>{Ia(()=>n(e))})))})}function _i(e){var t,n,r="";if(typeof e=="string"||typeof e=="number")r+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(n=_i(e[t]))&&(r&&(r+=" "),r+=n)}else for(n in e)e[n]&&(r&&(r+=" "),r+=n);return r}function Cd(){for(var e,t,n=0,r="",a=arguments.length;n<a;n++)(e=arguments[n])&&(t=_i(e))&&(r&&(r+=" "),r+=t);return r}function vi(e){return typeof e=="object"?Cd(e):e??""}const gi=[...` 	
\r\f \v\uFEFF`];function xd(e,t,n){var r=e==null?"":""+e;if(t&&(r=r?r+" "+t:t),n){for(var a of Object.keys(n))if(n[a])r=r?r+" "+a:a;else if(r.length)for(var o=a.length,s=0;(s=r.indexOf(a,s))>=0;){var i=s+o;(s===0||gi.includes(r[s-1]))&&(i===r.length||gi.includes(r[i]))?r=(s===0?"":r.substring(0,s))+r.substring(i+1):s=i}}return r===""?null:r}function bi(e,t=!1){var n=t?" !important;":";",r="";for(var a of Object.keys(e)){var o=e[a];o!=null&&o!==""&&(r+=" "+a+": "+o+n)}return r}function Qa(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Td(e,t){if(t){var n="",r,a;if(Array.isArray(t)?(r=t[0],a=t[1]):r=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,s=0,i=!1,l=[];r&&l.push(...Object.keys(r).map(Qa)),a&&l.push(...Object.keys(a).map(Qa));var c=0,d=-1;const w=e.length;for(var u=0;u<w;u++){var f=e[u];if(i?f==="/"&&e[u-1]==="*"&&(i=!1):o?o===f&&(o=!1):f==="/"&&e[u+1]==="*"?i=!0:f==='"'||f==="'"?o=f:f==="("?s++:f===")"&&s--,!i&&o===!1&&s===0){if(f===":"&&d===-1)d=u;else if(f===";"||u===w-1){if(d!==-1){var _=Qa(e.substring(c,d).trim());if(!l.includes(_)){f!==";"&&u++;var m=e.substring(c,u).trim();n+=" "+m+";"}}c=u+1,d=-1}}}}return r&&(n+=bi(r)),a&&(n+=bi(a,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function Za(e,t,n,r,a,o){var s=e.__className;if(s!==n||s===void 0){var i=xd(n,r,o);i==null?e.removeAttribute("class"):t?e.className=i:e.setAttribute("class",i),e.__className=n}else if(o&&a!==o)for(var l in o){var c=!!o[l];(a==null||c!==!!a[l])&&e.classList.toggle(l,c)}return o}function Ja(e,t={},n,r){for(var a in n){var o=n[a];t[a]!==o&&(n[a]==null?e.style.removeProperty(a):e.style.setProperty(a,o,r))}}function Rd(e,t,n,r){var a=e.__style;if(a!==t){var o=Td(t,r);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else r&&(Array.isArray(r)?(Ja(e,n==null?void 0:n[0],r[0]),Ja(e,n==null?void 0:n[1],r[1],"important")):Ja(e,n,r));return r}function za(e,t,n=!1){if(e.multiple){if(t==null)return;if(!ya(t))return qc();for(var r of e.options)r.selected=t.includes(yi(r));return}for(r of e.options){var a=yi(r);if(Qc(a,t)){r.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function Dd(e){var t=new MutationObserver(()=>{za(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),La(()=>{t.disconnect()})}function yi(e){return"__value"in e?e.__value:e.value}const lr=Symbol("class"),ur=Symbol("style"),wi=Symbol("is custom element"),qi=Symbol("is html"),Od=Ma?"option":"OPTION",Ld=Ma?"select":"SELECT",Id=Ma?"progress":"PROGRESS";function Bd(e,t){var n=eo(e);n.value===(n.value=t??void 0)||e.value===t&&(t!==0||e.nodeName!==Id)||(e.value=t??"")}function Gd(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function q(e,t,n,r){var a=eo(e);a[t]!==(a[t]=n)&&(t==="loading"&&(e[Uu]=n),n==null?e.removeAttribute(t):typeof n!="string"&&ki(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function Vd(e,t,n,r,a=!1,o=!1){var s=eo(e),i=s[wi],l=!s[qi],c=t||{},d=e.nodeName===Od;for(var u in t)u in n||(n[u]=null);n.class?n.class=vi(n.class):n[lr]&&(n.class=null),n[ur]&&(n.style??(n.style=null));var f=ki(e);for(const y in n){let M=n[y];if(d&&y==="value"&&M==null){e.value=e.__value="",c[y]=M;continue}if(y==="class"){var _=e.namespaceURI==="http://www.w3.org/1999/xhtml";Za(e,_,M,r,t==null?void 0:t[lr],n[lr]),c[y]=M,c[lr]=n[lr];continue}if(y==="style"){Rd(e,M,t==null?void 0:t[ur],n[ur]),c[y]=M,c[ur]=n[ur];continue}var m=c[y];if(!(M===m&&!(M===void 0&&e.hasAttribute(y)))){c[y]=M;var w=y[0]+y[1];if(w!=="$$")if(w==="on"){const F={},W="$$"+y;let T=y.slice(2);var p=pd(T);if(fd(T)&&(T=T.slice(0,-7),F.capture=!0),!p&&m){if(M!=null)continue;e.removeEventListener(T,c[W],F),c[W]=null}if(p)me(T,e,M),Wa([T]);else if(M!=null){let ye=function(ne){c[y].call(this,ne)};c[W]=bd(T,e,ye,F)}}else if(y==="style")q(e,y,M);else if(y==="autofocus")nd(e,!!M);else if(!i&&(y==="__value"||y==="value"&&M!=null))e.value=e.__value=M;else if(y==="selected"&&d)Gd(e,M);else{var v=y;l||(v=_d(v));var P=v==="defaultValue"||v==="defaultChecked";if(M==null&&!i&&!P)if(s[y]=null,v==="value"||v==="checked"){let F=e;const W=t===void 0;if(v==="value"){let T=F.defaultValue;F.removeAttribute(v),F.defaultValue=T,F.value=F.__value=W?T:null}else{let T=F.defaultChecked;F.removeAttribute(v),F.defaultChecked=T,F.checked=W?T:!1}}else e.removeAttribute(y);else P||f.includes(v)&&(i||typeof M!="string")?(e[v]=M,v in s&&(s[v]=se)):typeof M!="function"&&q(e,v,M)}}}return c}function Si(e,t,n=[],r=[],a=[],o,s=!1,i=!1){Os(a,n,r,l=>{var c=void 0,d={},u=e.nodeName===Ld,f=!1;if(Zs(()=>{var m=t(...l.map(S)),w=Vd(e,c,m,o,s,i);f&&u&&"value"in m&&za(e,m.value);for(let v of Object.getOwnPropertySymbols(d))m[v]||fe(d[v]);for(let v of Object.getOwnPropertySymbols(m)){var p=m[v];v.description===yc&&(!c||p!==c[v])&&(d[v]&&fe(d[v]),d[v]=ve(()=>Nd(e,()=>p))),w[v]=p}c=w}),u){var _=e;Ia(()=>{za(_,c.value,!0),Dd(_)})}f=!0})}function eo(e){return e.__attributes??(e.__attributes={[wi]:e.nodeName.includes("-"),[qi]:e.namespaceURI===qs})}var Mi=new Map;function ki(e){var t=e.getAttribute("is")||e.nodeName,n=Mi.get(t);if(n)return n;Mi.set(t,n=[]);for(var r,a=e,o=Element.prototype;o!==a;){r=Gu(a);for(var s in r)r[s].set&&n.push(s);a=hs(a)}return n}function Ai(e,t){return e===t||(e==null?void 0:e[ft])===t}function Hd(e={},t,n,r){return Ia(()=>{var a,o;return Qs(()=>{a=o,o=[],Gr(()=>{e!==n(...o)&&(t(e,...o),a&&Ai(n(...a),e)&&t(null,...a))})}),()=>{Qe(()=>{o&&Ai(n(...o),e)&&t(null,...o)})}}),e}let Wr=!1;function Wd(e){var t=Wr;try{return Wr=!1,[e(),Wr]}finally{Wr=t}}const jd={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return b&&nc(`${e.name}.${String(t)}`),!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function K(e,t,n){return new Proxy(b?{props:e,exclude:t,name:n,other:{},to_proxy:[]}:{props:e,exclude:t},jd)}const $d={get(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(Xn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r)return r[t]}},set(e,t,n){let r=e.props.length;for(;r--;){let a=e.props[r];Xn(a)&&(a=a());const o=lt(a,t);if(o&&o.set)return o.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(Xn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r){const a=lt(r,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===ft||t===vs)return!1;for(let n of e.props)if(Xn(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(Xn(n)&&(n=n()),!!n){for(const r in n)t.includes(r)||t.push(r);for(const r of Object.getOwnPropertySymbols(n))t.includes(r)||t.push(r)}return t}};function Q(...e){return new Proxy({props:e},$d)}function yn(e,t,n,r){var P;var a=(n&pc)!==0,o=(n&mc)!==0,s=r,i=!0,l=()=>(i&&(i=!1,s=o?Gr(r):r),s),c;if(a){var d=ft in e||vs in e;c=((P=lt(e,t))==null?void 0:P.set)??(d&&t in e?y=>e[t]=y:void 0)}var u,f=!1;a?[u,f]=Wd(()=>e[t]):u=e[t],u===void 0&&r!==void 0&&(u=l(),c&&(tc(t),c(u)));var _;if(_=()=>{var y=e[t];return y===void 0?l():(i=!0,y)},(n&hc)===0)return _;if(c){var m=e.$$legacy;return(function(y,M){return arguments.length>0?((!M||m||f)&&c(M?_():y),y):_()})}var w=!1,p=((n&fc)!==0?Ir:Ls)(()=>(w=!1,_()));b&&(p.label=t),a&&S(p);var v=O;return(function(y,M){if(arguments.length>0){const F=M?S(p):a?vn(y):y;return te(p,F),w=!0,s!==void 0&&(s=F),y}return Nt&&w||(v.f&ct)!==0?p.v:S(p)})}if(b){let e=function(t){if(!(t in globalThis)){let n;Object.defineProperty(globalThis,t,{configurable:!0,get:()=>{if(n!==void 0)return n;rc(t)},set:r=>{n=r}})}};e("$state"),e("$effect"),e("$derived"),e("$inspect"),e("$props"),e("$bindable")}function Ei(e){Y===null&&bs("onMount"),od(()=>{const t=Gr(e);if(typeof t=="function")return t})}const Ud="5";typeof window<"u"&&((Wi=window.__svelte??(window.__svelte={})).v??(Wi.v=new Set)).add(Ud);/**
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
 */const Xd={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const Kd=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const Yd=Symbol("lucide-context"),Qd=()=>Fc(Yd);var Zd=qd("<svg><!><!></svg>");function Z(e,t){I(t,!0);const n=Qd()??{},r=yn(t,"color",19,()=>n.color??"currentColor"),a=yn(t,"size",19,()=>n.size??24),o=yn(t,"strokeWidth",19,()=>n.strokeWidth??2),s=yn(t,"absoluteStrokeWidth",19,()=>n.absoluteStrokeWidth??!1),i=yn(t,"iconNode",19,()=>[]),l=K(t,["$$slots","$$events","$$legacy","name","color","size","strokeWidth","absoluteStrokeWidth","iconNode","children"]),c=Jn(()=>s()?Number(o())*24/Number(a()):o());var d=Zd();Si(d,_=>({...Xd,..._,...l,width:a(),height:a(),stroke:r(),"stroke-width":S(c),class:["lucide-icon lucide",n.class,t.name&&`lucide-${t.name}`,t.class]}),[()=>!t.children&&!Kd(l)&&{"aria-hidden":"true"}]);var u=E(d);Hr(u,17,i,Ka,(_,m)=>{var w=Jn(()=>ju(S(m),2));let p=()=>S(w)[0],v=()=>S(w)[1];var P=U(),y=H(P);Fd(y,p,!0,(M,F)=>{Si(M,()=>({...v()}))}),R(_,P)});var f=N(u);X(f,()=>t.children??$),R(e,d),B()}function Jd(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M2 10v3"}],["path",{d:"M6 6v11"}],["path",{d:"M10 3v18"}],["path",{d:"M14 8v7"}],["path",{d:"M18 5v13"}],["path",{d:"M22 10v3"}]];Z(e,Q({name:"audio-lines"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function zd(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];Z(e,Q({name:"chart-line"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function ef(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 9 6 6 6-6"}]];Z(e,Q({name:"chevron-down"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function tf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"}],["path",{d:"M12 17h.01"}]];Z(e,Q({name:"circle-question-mark"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function nf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 12 18z"}],["path",{d:"M2 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 2 18z"}]];Z(e,Q({name:"fast-forward"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function rf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"}]];Z(e,Q({name:"folder-open"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function af(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["rect",{x:"14",y:"3",width:"5",height:"18",rx:"1"}],["rect",{x:"5",y:"3",width:"5",height:"18",rx:"1"}]];Z(e,Q({name:"pause"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function of(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"}]];Z(e,Q({name:"play"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function sf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m15 14 5-5-5-5"}],["path",{d:"M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13"}]];Z(e,Q({name:"redo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function lf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];Z(e,Q({name:"refresh-cw"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function uf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m2 9 3-3 3 3"}],["path",{d:"M13 18H7a2 2 0 0 1-2-2V6"}],["path",{d:"m22 15-3 3-3-3"}],["path",{d:"M11 6h6a2 2 0 0 1 2 2v10"}]];Z(e,Q({name:"repeat-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function cf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 12 18z"}],["path",{d:"M22 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 22 18z"}]];Z(e,Q({name:"rewind"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function df(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M8.12 8.12 12 12"}],["path",{d:"M20 4 8.12 15.88"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M14.8 14.8 20 20"}]];Z(e,Q({name:"scissors"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function ff(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];Z(e,Q({name:"settings"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function hf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];Z(e,Q({name:"sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function pf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 2h4"}],["path",{d:"M12 14v-4"}],["path",{d:"M4 13a8 8 0 0 1 8-7 8 8 0 1 1-5.3 14L4 17.6"}],["path",{d:"M9 17H4v5"}]];Z(e,Q({name:"timer-reset"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function mf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 11v6"}],["path",{d:"M14 11v6"}],["path",{d:"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"}],["path",{d:"M3 6h18"}],["path",{d:"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"}]];Z(e,Q({name:"trash-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function _f(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9 14 4 9l5-5"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"}]];Z(e,Q({name:"undo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function vf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}]];Z(e,Q({name:"volume-1"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function gf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}],["path",{d:"M19.364 18.364a9 9 0 0 0 0-12.728"}]];Z(e,Q({name:"volume-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function bf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["line",{x1:"22",x2:"16",y1:"9",y2:"15"}],["line",{x1:"16",x2:"22",y1:"9",y2:"15"}]];Z(e,Q({name:"volume-x"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}function yf(e,t){I(t,!0);/**
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
 */let n=K(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}],["path",{d:"M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"}]];Z(e,Q({name:"waves"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=H(s);X(i,()=>t.children??$),R(a,s)},$$slots:{default:!0}})),B()}var wf=je('<span aria-hidden="true"><!></span>');function z(e,t){I(t,!0);const n=yn(t,"className",3,""),r=Jn(()=>["aqe-button-icon",n()].filter(Boolean).join(" "));var a=wf(),o=E(a);{var s=g=>{Jd(g,{size:14,strokeWidth:2})},i=g=>{zd(g,{size:14,strokeWidth:2})},l=g=>{ef(g,{size:14,strokeWidth:2})},c=g=>{tf(g,{size:14,strokeWidth:2})},d=g=>{nf(g,{size:14,strokeWidth:2})},u=g=>{rf(g,{size:14,strokeWidth:2})},f=g=>{af(g,{size:14,strokeWidth:2})},_=g=>{of(g,{size:14,strokeWidth:2})},m=g=>{sf(g,{size:14,strokeWidth:2})},w=g=>{lf(g,{size:14,strokeWidth:2})},p=g=>{uf(g,{size:14,strokeWidth:2})},v=g=>{cf(g,{size:14,strokeWidth:2})},P=g=>{df(g,{size:14,strokeWidth:2})},y=g=>{ff(g,{size:14,strokeWidth:2})},M=g=>{hf(g,{size:14,strokeWidth:2})},F=g=>{pf(g,{size:14,strokeWidth:2})},W=g=>{mf(g,{size:14,strokeWidth:2})},T=g=>{_f(g,{size:14,strokeWidth:2})},ye=g=>{vf(g,{size:14,strokeWidth:2})},ne=g=>{gf(g,{size:14,strokeWidth:2})},De=g=>{bf(g,{size:14,strokeWidth:2})},Oe=g=>{yf(g,{size:14,strokeWidth:2})};Yt(o,g=>{t.icon==="audio-lines"?g(s):t.icon==="chart-line"?g(i,1):t.icon==="chevron-down"?g(l,2):t.icon==="circle-help"?g(c,3):t.icon==="fast-forward"?g(d,4):t.icon==="folder-open"?g(u,5):t.icon==="pause"?g(f,6):t.icon==="play"?g(_,7):t.icon==="redo-2"?g(m,8):t.icon==="refresh-cw"?g(w,9):t.icon==="repeat-2"?g(p,10):t.icon==="rewind"?g(v,11):t.icon==="scissors"?g(P,12):t.icon==="settings"?g(y,13):t.icon==="sparkles"?g(M,14):t.icon==="timer-reset"?g(F,15):t.icon==="trash-2"?g(W,16):t.icon==="undo-2"?g(T,17):t.icon==="volume-1"?g(ye,18):t.icon==="volume-2"?g(ne,19):t.icon==="volume-x"?g(De,20):t.icon==="waves"&&g(Oe,21)})}pt(()=>Za(a,1,vi(S(r)))),R(e,a),B()}const qf=50,Sf=1e4,Mf=.5,kf=12,Af=.01,Ef=.25,jr={denoiseAlgorithm:"standard",pauseAggressiveness:"normal",speedStep:.05,trimStepMs:100,volumeStepDb:3};function Pf(){return window.__aqeSplitButtonStates??(window.__aqeSplitButtonStates={}),window.__aqeSplitButtonStates}function Ff(){var e;return{...jr,...(e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.splitButtonDefaults}}function to(e){return Number.isFinite(e)?Math.max(qf,Math.min(Sf,Math.round(e))):jr.trimStepMs}function no(e){return Number.isFinite(e)?Math.max(Mf,Math.min(kf,Math.round(e*10)/10)):jr.volumeStepDb}function ro(e){return Number.isFinite(e)?Math.max(Af,Math.min(Ef,Math.round(e*100)/100)):jr.speedStep}function Pi(e){const t=to(e);if(t<1e3)return`${t} ms`;const n=t/1e3;return`${Number.isInteger(n)?n.toFixed(0):n.toFixed(1)} s`}function Fi(e){const t=no(e);return`${Number.isInteger(t)?t.toFixed(0):t.toFixed(1)} dB`}function Ni(e,t){const n=ro(e);return`x${(t==="aqe:slower"?1-n:1+n).toFixed(2)}`}function Nf(e){return e==="aggressive"?"Aggressive":e==="gentle"?"Gentle":"Normal"}function Cf(e){return e==="rnnoise"?"RNNoise":"Standard"}function Tt(e){const t=Ff(),n=to(t.trimStepMs),r=no(t.volumeStepDb),a=ro(t.speedStep),o=t.pauseAggressiveness,s=t.denoiseAlgorithm,i=Pf(),l=i[e];if(l)return!l.trimEdited&&l.defaultTrimStepMs!==n&&(l.defaultTrimStepMs=n,l.trimStepMs=n),!l.volumeEdited&&l.defaultVolumeStepDb!==r&&(l.defaultVolumeStepDb=r,l.volumeStepDb=r),!l.speedEdited&&l.defaultSpeedStep!==a&&(l.defaultSpeedStep=a,l.speedStep=a),!l.pauseEdited&&l.defaultPauseAggressiveness!==o&&(l.defaultPauseAggressiveness=o,l.pauseAggressiveness=o),!l.denoiseEdited&&l.defaultDenoiseAlgorithm!==s&&(l.defaultDenoiseAlgorithm=s,l.denoiseAlgorithm=s),l;const c={defaultDenoiseAlgorithm:s,defaultPauseAggressiveness:o,defaultTrimStepMs:n,defaultVolumeStepDb:r,defaultSpeedStep:a,denoiseAlgorithm:s,denoiseEdited:!1,pauseAggressiveness:o,pauseEdited:!1,speedEdited:!1,speedStep:a,trimEdited:!1,trimStepMs:n,volumeEdited:!1,volumeStepDb:r};return i[e]=c,c}function xf(e,t){const n=Tt(e);return n.trimEdited=!0,n.trimStepMs=to(t),n}function Tf(e,t){const n=Tt(e);return n.volumeEdited=!0,n.volumeStepDb=no(t),n}function Rf(e,t){const n=Tt(e);return n.speedEdited=!0,n.speedStep=ro(t),n}function Df(e,t){const n=Tt(e);return n.pauseEdited=!0,n.pauseAggressiveness=t,n}function Of(e,t){const n=Tt(e);return n.denoiseEdited=!0,n.denoiseAlgorithm=t,n}function Lf(e,t){return{command:e,fieldOrd:t,overrides:{trimStepMs:Tt(t).trimStepMs}}}function If(e,t){const n=Tt(t);return e==="aqe:volume-up"||e==="aqe:volume-down"?{command:e,fieldOrd:t,overrides:{volumeStepDb:n.volumeStepDb}}:e==="aqe:faster"||e==="aqe:slower"?{command:e,fieldOrd:t,overrides:{speedStep:n.speedStep}}:e==="aqe:remove-pauses"?{command:e,fieldOrd:t,overrides:{pauseAggressiveness:n.pauseAggressiveness}}:e==="aqe:denoise-standard"||e==="aqe:rnnoise"?{command:n.denoiseAlgorithm==="rnnoise"?"aqe:rnnoise":"aqe:denoise-standard",fieldOrd:t,overrides:{denoiseAlgorithm:n.denoiseAlgorithm}}:Lf(e,t)}var Bf=je('<button type="button" class="aqe-button aqe-split-preset"> </button>'),Gf=je('<div class="aqe-split-presets"></div>'),Vf=je('<button type="button" class="aqe-button aqe-split-preset"> </button>'),Hf=je('<input type="range"/> <div class="aqe-split-range-labels"><span> </span> <span> </span></div> <div class="aqe-split-presets"></div>',1),Wf=je('<div class="aqe-split-popover"><div class="aqe-split-popover-header"><strong> </strong> <span> </span></div> <!></div>'),jf=je('<span class="aqe-split-button"><button type="button" class="aqe-button aqe-split-primary" data-aqe-button-state="default"><!> <span class="aqe-button-label"> </span></button> <button type="button" class="aqe-button aqe-icon-only aqe-split-menu-button"><!> <span class="aqe-button-label">Options</span></button> <!></span>');function Ci(e,t){I(t,!0);let n,r=_e(!1),a=_e(100),o=_e(3),s=_e(.05),i=_e("normal"),l=_e("standard");function c(){return ee[t.button.command]}function d(){te(r,!1)}function u(A){A.preventDefault(),A.stopPropagation(),te(r,!S(r))}function f(A){te(a,xf(t.target.ord,A).trimStepMs,!0)}function _(A){te(o,Tf(t.target.ord,A).volumeStepDb,!0)}function m(A){te(s,Rf(t.target.ord,A).speedStep,!0)}function w(A){te(i,Df(t.target.ord,A).pauseAggressiveness,!0)}function p(A){te(l,Of(t.target.ord,A).denoiseAlgorithm,!0)}function v(){d(),zo(t.button.command,t.target.node,t.target.ord,If(t.button.command,t.target.ord))}function P(){return t.button.command==="aqe:volume-up"||t.button.command==="aqe:volume-down"?Fi(S(o)):t.button.command==="aqe:faster"||t.button.command==="aqe:slower"?Ni(S(s),t.button.command):t.button.command==="aqe:remove-pauses"?Nf(S(i)):t.button.command==="aqe:denoise-standard"||t.button.command==="aqe:rnnoise"?Cf(S(l)):Pi(S(a))}function y(){return t.button.command==="aqe:volume-up"||t.button.command==="aqe:volume-down"?S(o):t.button.command==="aqe:faster"||t.button.command==="aqe:slower"?S(s):S(a)}function M(){return t.button.command==="aqe:volume-up"||t.button.command==="aqe:volume-down"?{min:"0.5",max:"12",step:"0.5",labels:["0.5 dB","12 dB"],presets:[1,3,6,9]}:t.button.command==="aqe:faster"||t.button.command==="aqe:slower"?{min:"0.01",max:"0.25",step:"0.01",labels:["x1.01","x1.25"],presets:[.03,.05,.1,.2]}:{min:"50",max:"10000",step:"50",labels:["50 ms","10 s"],presets:[100,200,500,1e3]}}function F(A){if(t.button.command==="aqe:volume-up"||t.button.command==="aqe:volume-down"){_(A);return}if(t.button.command==="aqe:faster"||t.button.command==="aqe:slower"){m(A);return}f(A)}function W(){return t.button.command==="aqe:remove-pauses"?["gentle","normal","aggressive"]:t.button.command==="aqe:denoise-standard"||t.button.command==="aqe:rnnoise"?["standard","rnnoise"]:[]}function T(A){return A==="rnnoise"?"RNNoise":A==="aggressive"?"Aggressive":A==="gentle"?"Gentle":A==="standard"?"Standard":"Normal"}function ye(A){(A==="gentle"||A==="normal"||A==="aggressive")&&w(A),(A==="standard"||A==="rnnoise")&&p(A)}function ne(A){!S(r)||!n||A.target instanceof Node&&n.contains(A.target)||d()}function De(A){A.key==="Escape"&&d()}Ei(()=>{const A=Tt(t.target.ord);return te(a,A.trimStepMs,!0),te(o,A.volumeStepDb,!0),te(s,A.speedStep,!0),te(i,A.pauseAggressiveness,!0),te(l,A.denoiseAlgorithm,!0),document.addEventListener("mousedown",ne,!0),document.addEventListener("keydown",De,!0),()=>{document.removeEventListener("mousedown",ne,!0),document.removeEventListener("keydown",De,!0)}});var Oe=jf(),g=E(Oe),Dt=E(g);z(Dt,{get icon(){return t.button.icon}});var Fn=N(Dt,2),Nn=E(Fn),we=N(g,2),Cn=E(we);z(Cn,{icon:"chevron-down"});var xn=N(we,2);{var qe=A=>{var tn=Wf(),mr=E(tn),Xr=E(mr),uo=E(Xr),Kr=N(Xr,2),co=E(Kr),fo=N(mr,2);{var Yr=Xe=>{var vt=Gf();Hr(vt,21,W,Ka,(Ke,nt)=>{var rt=Bf(),_r=E(rt);pt((Tn,vr,gr)=>{q(rt,"data-testid",Tn),q(rt,"aria-pressed",vr),Ct(_r,gr)},[()=>`aqe-split-${t.target.ord}-${c()}-preset-${S(nt)}`,()=>P()===T(S(nt))?"true":"false",()=>T(S(nt))]),me("click",rt,()=>ye(S(nt))),R(Ke,rt)}),R(Xe,vt)},ho=Jn(()=>W().length),po=Xe=>{var vt=Hf(),Ke=H(vt),nt=N(Ke,2),rt=E(nt),_r=E(rt),Tn=N(rt,2),vr=E(Tn),gr=N(nt,2);Hr(gr,21,()=>M().presets,Ka,(nn,at)=>{var gt=Vf(),bt=E(gt);pt((Rn,yt,wt)=>{q(gt,"data-testid",Rn),q(gt,"aria-pressed",yt),Ct(bt,wt)},[()=>`aqe-split-${t.target.ord}-${c()}-preset-${S(at)}`,()=>y()===S(at)?"true":"false",()=>t.button.command==="aqe:volume-up"||t.button.command==="aqe:volume-down"?Fi(S(at)):t.button.command==="aqe:faster"||t.button.command==="aqe:slower"?Ni(S(at),t.button.command):Pi(S(at))]),me("click",gt,()=>F(S(at))),R(nn,gt)}),pt((nn,at,gt,bt,Rn,yt,wt)=>{q(Ke,"data-testid",nn),q(Ke,"min",at),q(Ke,"max",gt),q(Ke,"step",bt),Bd(Ke,Rn),Ct(_r,yt),Ct(vr,wt)},[()=>`aqe-split-${t.target.ord}-${c()}-slider`,()=>M().min,()=>M().max,()=>M().step,y,()=>M().labels[0],()=>M().labels[1]]),me("input",Ke,nn=>F(Number(nn.currentTarget.value))),R(Xe,vt)};Yt(fo,Xe=>{S(ho)?Xe(Yr):Xe(po,!1)})}pt((Xe,vt)=>{q(tn,"data-testid",Xe),Ct(uo,t.button.label),Ct(co,vt)},[()=>`aqe-split-${t.target.ord}-${c()}-popover`,P]),R(A,tn)};Yt(xn,A=>{S(r)&&A(qe)})}Hd(Oe,A=>n=A,()=>n),pt((A,tn)=>{q(g,"data-aqe-command",t.button.command),q(g,"data-testid",A),q(g,"title",t.button.title),q(g,"aria-label",t.button.title),Ct(Nn,t.button.label),q(we,"data-testid",tn),q(we,"title",`${t.button.title} amount`),q(we,"aria-label",`${t.button.title} amount`),q(we,"aria-expanded",S(r)?"true":"false")},[()=>`aqe-button-${t.target.ord}-${c()}`,()=>`aqe-split-${t.target.ord}-${c()}-menu`]),me("mousedown",g,A=>A.preventDefault()),me("click",g,v),me("mousedown",we,A=>A.preventDefault()),me("click",we,u),R(e,Oe),B()}Wa(["mousedown","click","input"]);function xi(){return document.body.dataset.aqeBusy==="true"}function Ti(e,t,n){if(xi())return;const r=G(n);if(!r)return;const a=jo(r,e);Wn(r),a&&(typeof t.focus=="function"&&t.focus(),St(r,{clearAudio:!0}),ll(a),window.__aqeActiveField=n,pe.info("region delete request queued",{ord:n,sourceFilename:a.sourceFilename,selectionStartMs:a.selectionStartMs,selectionEndMs:a.selectionEndMs,durationMs:a.durationMs,trigger:e,playbackActive:a.playbackActive}),ln(n,!0,wo("aqe:delete-selection")),on(n,"aqe:delete-selection"))}function $f(e,t){if(e.key!=="Backspace")return;const n=G(t);if(!(!n||document.activeElement!==n||xi())){if(!jo(n,"backspace")){Wn(n);return}e.preventDefault(),Ti("backspace",n,t)}}var Uf=je('<button type="button"><!> <!> <span class="aqe-button-label"> </span></button>'),Xf=je('<button type="button" class="aqe-button aqe-icon-only aqe-repeat-button" title="Repeat selected region, or the whole graph when no region is selected." aria-label="Repeat playback"><!> <span class="aqe-button-label">Repeat</span></button>'),Kf=je("<!> <!> <!>",1),Yf=je('<div class="aqe-controls"><!> <button type="button" class="aqe-button aqe-delete-region-button" data-aqe-command="aqe:delete-selection" data-aqe-button-state="default" title="Delete selected region" aria-label="Delete selected region" hidden=""><!> <span class="aqe-button-label">Delete Region</span></button> <span class="aqe-status"></span> <details class="aqe-help"><summary class="aqe-help-summary" title="Show editor help"><!> <span>Help</span></summary> <div class="aqe-help-body"><section class="aqe-help-section"><h4 class="aqe-help-title">Graph and regions</h4> <ul class="aqe-help-list"><li><kbd>Shift</kbd>-drag on the graph to select a region.</li> <li>Play uses the selected region when one is active; Repeat loops the selected region, or the full graph otherwise.</li> <li>Delete Region removes only the selected region. Backspace does the same when the graph is focused.</li> <li>In the graph, grey is loudness and lines are pitch of the voice.</li></ul></section> <section class="aqe-help-section"><h4 class="aqe-help-title">Buttons</h4> <div class="aqe-help-grid"><span class="aqe-help-item"><span class="aqe-help-command"><!><span>Play</span></span> <span>Start or pause audio.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Graph</span></span> <span>Show pitch and loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Folder</span></span> <span>Open the current audio file.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>-L</span></span> <span>Trim 100 ms from the left.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>-R</span></span> <span>Trim 100 ms from the right.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Shorten Pauses</span></span> <span>Speed up long internal pauses.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Denoise</span></span> <span>Use Standard or RNNoise cleanup.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Slower</span></span> <span>Decrease speed.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Faster</span></span> <span>Increase speed.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Volume -</span></span> <span>Decrease loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Volume +</span></span> <span>Increase loudness.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Undo</span></span> <span>Restore the previous edit.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Redo</span></span> <span>Restore the undone edit.</span></span> <span class="aqe-help-item"><span class="aqe-help-command"><!><span>Delete Region</span></span> <span>Remove the selected graph region.</span></span></div></section> <p class="aqe-help-note">Every edit creates a new media file and updates the field to point at it. The original file remains in your media collection.</p></div></details> <div class="aqe-visualizer" data-anchor-ms="0" data-cursor-ms="0" data-progress-ms="0" data-graph-active="false" data-graph-busy="false" data-has-track="false" data-playback-state="stopped" data-playback-engine="" data-playback-start-ms="0" data-playback-end-ms="0" data-playback-region-mode="full" data-resume-requires-restart="false" data-selection-active="false" data-selection-start-ms="" data-selection-end-ms="" data-selection-draft-active="false" data-selection-draft-start-ms="" data-selection-draft-end-ms="" role="button" aria-label="Audio graph" tabindex="0" hidden=""><audio class="aqe-audio-clock" preload="metadata" hidden=""></audio> <svg class="aqe-visualizer-svg" preserveAspectRatio="xMinYMin meet" role="img" aria-label="Audio pitch and intensity visualization"><rect class="aqe-selection" width="0" visibility="hidden"></rect><path class="aqe-intensity" d=""></path><g class="aqe-pitch"></g><g class="aqe-labels"></g><g class="aqe-x-axis"></g><line class="aqe-selection-edge aqe-selection-start" visibility="hidden"></line><line class="aqe-selection-edge aqe-selection-end" visibility="hidden"></line><line class="aqe-cursor"></line></svg> <div class="aqe-visualizer-meta"><span class="aqe-spinner" hidden="" aria-hidden="true"></span> <span class="aqe-cursor-label">0 ms</span> <span class="aqe-visualizer-status"></span></div></div></div>');function Qf(e,t){var Yi;I(t,!0);const n=((Yi=window.__AQE_EDITOR_CONFIG__)==null?void 0:Yi.repeatPlaybackByDefault)===!0,r={command:"aqe:denoise-standard",icon:"sparkles",label:"Denoise",title:"Denoise audio"};function a(re){const Qr=re.currentTarget.ariaPressed!=="true";gu(t.target.ord,Qr)}function o(re){return["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:volume-down","aqe:volume-up","aqe:remove-pauses","aqe:denoise-standard"].includes(re)}Ei(()=>{const re=G(t.target.ord);re&&(fu(re),qu(re),_u(re))});var s=Yf(),i=E(s);Hr(i,17,()=>V,re=>re.command,(re,he)=>{var Qr=Kf(),Qi=H(Qr);{var gh=Se=>{Ci(Se,{get button(){return S(he)},get target(){return t.target}})},bh=Jn(()=>o(S(he).command)),yh=Se=>{var ie=Uf();let Zr;var Jr=E(ie);z(Jr,{className:"aqe-button-icon-default",get icon(){return S(he).icon}});var Ji=N(Jr,2);{var Mh=rn=>{z(rn,{className:"aqe-button-icon-active",get icon(){return S(he).activeIcon}})};Yt(Ji,rn=>{S(he).activeIcon&&rn(Mh)})}var kh=N(Ji,2),Ah=E(kh);pt(rn=>{Zr=Za(ie,1,"aqe-button",null,Zr,{"aqe-icon-only":S(he).iconOnly===!0}),q(ie,"data-aqe-command",S(he).command),q(ie,"data-aqe-button-state",S(he).command==="aqe:play"?"play":S(he).command==="aqe:analyze"?"graph":"default"),q(ie,"data-testid",rn),q(ie,"title",S(he).title),q(ie,"aria-label",S(he).title),Ct(Ah,S(he).label)},[()=>Ln(t.target.ord,S(he).command)]),me("mousedown",ie,rn=>rn.preventDefault()),me("click",ie,()=>zo(S(he).command,t.target.node,t.target.ord)),R(Se,ie)};Yt(Qi,Se=>{S(bh)?Se(gh):Se(yh,!1)})}var Zi=N(Qi,2);{var wh=Se=>{var ie=Xf(),Zr=E(ie);z(Zr,{icon:"repeat-2"}),pt(()=>{q(ie,"data-aqe-button-state",n?"active":"default"),q(ie,"data-testid",`aqe-repeat-${t.target.ord}`),q(ie,"aria-pressed",n?"true":"false")}),me("mousedown",ie,Jr=>Jr.preventDefault()),me("click",ie,a),R(Se,ie)};Yt(Zi,Se=>{S(he).command==="aqe:play"&&Se(wh)})}var qh=N(Zi,2);{var Sh=Se=>{Ci(Se,{get button(){return r},get target(){return t.target}})};Yt(qh,Se=>{S(he).command==="aqe:remove-pauses"&&Se(Sh)})}R(re,Qr)});var l=N(i,2),c=E(l);z(c,{icon:"trash-2"});var d=N(l,2),u=N(d,2),f=E(u),_=E(f);z(_,{icon:"circle-help"});var m=N(f,2),w=N(E(m),2),p=N(E(w),2),v=E(p),P=E(v),y=E(P);z(y,{icon:"play"});var M=N(v,2),F=E(M),W=E(F);z(W,{icon:"audio-lines"});var T=N(M,2),ye=E(T),ne=E(ye);z(ne,{icon:"folder-open"});var De=N(T,2),Oe=E(De),g=E(Oe);z(g,{icon:"scissors"});var Dt=N(De,2),Fn=E(Dt),Nn=E(Fn);z(Nn,{icon:"scissors"});var we=N(Dt,2),Cn=E(we),xn=E(Cn);z(xn,{icon:"timer-reset"});var qe=N(we,2),A=E(qe),tn=E(A);z(tn,{icon:"sparkles"});var mr=N(qe,2),Xr=E(mr),uo=E(Xr);z(uo,{icon:"rewind"});var Kr=N(mr,2),co=E(Kr),fo=E(co);z(fo,{icon:"fast-forward"});var Yr=N(Kr,2),ho=E(Yr),po=E(ho);z(po,{icon:"volume-1"});var Xe=N(Yr,2),vt=E(Xe),Ke=E(vt);z(Ke,{icon:"volume-2"});var nt=N(Xe,2),rt=E(nt),_r=E(rt);z(_r,{icon:"undo-2"});var Tn=N(nt,2),vr=E(Tn),gr=E(vr);z(gr,{icon:"redo-2"});var nn=N(Tn,2),at=E(nn),gt=E(at);z(gt,{icon:"trash-2"});var bt=N(u,2),Rn=E(bt),yt=N(Rn,2),wt=E(yt),ji=N(wt),$i=N(ji),Ui=N($i,2),Dn=N(Ui),On=N(Dn),br=N(On),_h=N(yt,2),Xi=E(_h),Ki=N(Xi,2),vh=N(Ki,2);pt(re=>{q(s,"data-aqe-field-ord",t.target.ord),q(s,"data-aqe-source-filename",t.target.sourceFilename),q(s,"data-testid",`aqe-controls-${t.target.ord}`),q(l,"data-testid",re),q(d,"data-testid",`aqe-status-${t.target.ord}`),q(u,"data-testid",`aqe-help-${t.target.ord}`),q(bt,"data-aqe-field-ord",t.target.ord),q(bt,"data-repeat-enabled",n?"true":"false"),q(bt,"data-testid",`aqe-graph-${t.target.ord}`),q(Rn,"data-testid",`aqe-audio-clock-${t.target.ord}`),q(yt,"data-testid",`aqe-graph-svg-${t.target.ord}`),q(yt,"viewBox",`0 0 ${k.width} ${k.height}`),q(wt,"data-testid",`aqe-selection-${t.target.ord}`),q(wt,"x",k.left),q(wt,"y",k.top),q(wt,"height",k.height-k.top-k.bottom),q(ji,"data-testid",`aqe-intensity-${t.target.ord}`),q($i,"data-testid",`aqe-pitch-${t.target.ord}`),q(Ui,"data-testid",`aqe-x-axis-${t.target.ord}`),q(Dn,"data-testid",`aqe-selection-start-${t.target.ord}`),q(Dn,"x1",k.left),q(Dn,"x2",k.left),q(Dn,"y1",k.top),q(Dn,"y2",k.height-k.bottom),q(On,"data-testid",`aqe-selection-end-${t.target.ord}`),q(On,"x1",k.left),q(On,"x2",k.left),q(On,"y1",k.top),q(On,"y2",k.height-k.bottom),q(br,"data-testid",`aqe-cursor-${t.target.ord}`),q(br,"x1",k.left),q(br,"x2",k.left),q(br,"y1",k.top),q(br,"y2",k.height-k.bottom),q(Xi,"data-testid",`aqe-graph-spinner-${t.target.ord}`),q(Ki,"data-testid",`aqe-progress-label-${t.target.ord}`),q(vh,"data-testid",`aqe-graph-status-${t.target.ord}`)},[()=>Ln(t.target.ord,"aqe:delete-selection")]),me("mousedown",l,re=>re.preventDefault()),me("click",l,()=>Ti("button",t.target.node,t.target.ord)),me("keydown",bt,re=>$f(re,t.target.ord)),me("pointerdown",yt,re=>Au(re,t.target.ord)),R(e,s),B()}Wa(["mousedown","click","keydown","pointerdown"]);const wn=new Map;function Zf(e){const t=wn.get(e.ord);if(t){if(document.body.contains(t.host)||Ri(e,t.host),ao(e.ord,t.host),!e.sourceFilename||t.sourceFilename===e.sourceFilename)return t;const o=G(e.ord);if((o==null?void 0:o.dataset.graphBusy)==="true"||(o==null?void 0:o.dataset.hasTrack)==="true"){const s=o.dataset.sourceFilename||e.sourceFilename;t.sourceFilename=s;const i=document.querySelector(`.aqe-controls[data-aqe-field-ord="${e.ord}"]`);return i&&(i.dataset.aqeSourceFilename=s),ao(e.ord,t.host),t}}Jf(e.ord);const n=document.createElement("div");n.className="aqe-mount-host",Ri(e,n);const a={component:Sd(Qf,{target:n,props:{target:e}}),host:n,ord:e.ord,sourceFilename:e.sourceFilename};return wn.set(e.ord,a),ao(e.ord,n),a}function Jf(e){const t=wn.get(e);t&&(pi(t.component),t.host.remove(),wn.delete(e)),document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>n.remove())}function zf(){for(const e of wn.values())pi(e.component),e.host.remove();wn.clear(),eh()}function Ri(e,t){const n=e.node.closest(".field-container")||e.node.closest(".field")||e.node.parentElement||e.node;n.parentElement?n.after(t):e.node.after(t)}function ao(e,t){document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>{t.contains(n)||n.remove()}),document.querySelectorAll(".aqe-mount-host").forEach(n=>{n!==t&&!n.querySelector(".aqe-controls")&&n.remove()})}function eh(){document.querySelectorAll(".aqe-mount-host").forEach(e=>e.remove()),document.querySelectorAll(".aqe-controls").forEach(e=>e.remove())}function th(){window.__aqeGraphStateForTest=oh,window.__aqeInstallAudioPlaybackTestDriverForTest=nh,window.__aqeSetCursorByClientXForTest=ah,window.__aqeSetCursorForTest=rh}function nh(e){const t=G(e),n=Le(t);return!t||!n?!1:(n.__aqeTestDriverInstalled=!0,n.pause=function(){n.__aqeTestPlaying=!1,n.__aqeTestFrame&&(window.cancelAnimationFrame(n.__aqeTestFrame),n.__aqeTestFrame=null)},n.play=function(){n.__aqeTestPlaying=!0,n.__aqeTestLastNow=performance.now();const a=()=>{if(!n.__aqeTestPlaying)return;const o=performance.now(),s=Number(t.dataset.durationMs||"0")/1e3,i=Math.max(0,(o-Number(n.__aqeTestLastNow||o))/1e3);if(n.__aqeTestLastNow=o,n.currentTime=Math.min(s,(Number(n.currentTime)||0)+i),s&&n.currentTime>=s){n.__aqeTestPlaying=!1,n.dispatchEvent(new Event("ended"));return}n.__aqeTestFrame=window.requestAnimationFrame(a)};return n.__aqeTestFrame=window.requestAnimationFrame(a),Promise.resolve()},!0)}function rh(e,t,n){const r=G(e);return r?(r.hidden=!1,r.dataset.graphActive="true",Lt(r,t,!!n),!0):!1}function ah(e,t,n){var i;const r=G(e),a=(r==null?void 0:r.querySelector(".aqe-visualizer-svg"))??null;if(!r||!a)return null;const o=Number(r.dataset.durationMs||"0"),s=Vn({clientX:t},a,o);return Lt(r,s,!!n),{cursorMs:Number(r.dataset.cursorMs||"0"),cursorX:Number(((i=r.querySelector(".aqe-cursor"))==null?void 0:i.getAttribute("x1"))||"0"),bounds:Io(a)}}function oh(e){var c,d,u,f,_;const t=G(e),n=So(e),r=Mo(e),a=((c=st(e))==null?void 0:c.querySelector(".aqe-delete-region-button"))??null;if(!t)return null;const o=yr().flatMap(m=>Array.from(m.querySelectorAll(".aqe-button-icon svg"))),s=Le(t),i=es(t),l=ts(t);return{active:t.dataset.graphActive==="true",busy:t.dataset.graphBusy==="true",hidden:!!t.hidden,hasTrack:t.dataset.hasTrack==="true",durationMs:Number(t.dataset.durationMs||"0"),anchorMs:Number(t.dataset.anchorMs||"0"),cursorMs:Number(t.dataset.cursorMs||"0"),progressMs:Number(t.dataset.progressMs||"0"),sourceFilename:t.dataset.sourceFilename||"",graphButtonLabel:Di(n),graphButtonState:(n==null?void 0:n.dataset.aqeButtonState)||"",graphButtonTitle:(n==null?void 0:n.title)||"",playButtonLabel:Di(r),playButtonState:(r==null?void 0:r.dataset.aqeButtonState)||"",playbackState:sh(t),selectionActive:i!==null,selectionStartMs:(i==null?void 0:i.startMs)??null,selectionEndMs:(i==null?void 0:i.endMs)??null,selectionDraftActive:l!==null,selectionDraftStartMs:(l==null?void 0:l.startMs)??null,selectionDraftEndMs:(l==null?void 0:l.endMs)??null,repeatEnabled:t.dataset.repeatEnabled==="true",repeatControlDisabled:!!((d=ko(e))!=null&&d.disabled),regionDeleteButtonDisabled:!!(a!=null&&a.disabled),regionDeleteButtonHidden:a?!!a.hidden:!0,playbackStartMs:Number(t.dataset.playbackStartMs||"0"),playbackEndMs:Number(t.dataset.playbackEndMs||"0"),playbackRegionMode:t.dataset.playbackRegionMode==="selection"?"selection":"full",resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true",audioClockSrc:s&&s.getAttribute("src")||"",audioClockCurrentMs:s?Math.round((Number(s.currentTime)||0)*1e3):0,audioClockReady:!!(s&&t.__aqeAudioClockAvailable),audioClockFallback:!!t.__aqeAudioClockFallback,audioClockMuted:!!(s&&s.muted),audioPlaybackTestDriver:!!(s&&s.__aqeTestDriverInstalled),playbackEngine:Un(t),progressClockMode:ih(t),xAxisLabels:Array.from(t.querySelectorAll(".aqe-x-label")).map(m=>m.textContent||""),pitchPaths:t.querySelectorAll(".aqe-pitch-path").length,intensity:((u=t.querySelector(".aqe-intensity"))==null?void 0:u.getAttribute("d"))||"",cursorX:Number(((f=t.querySelector(".aqe-cursor"))==null?void 0:f.getAttribute("x1"))||"0"),spinnerVisible:t.querySelector(".aqe-spinner")?!((_=t.querySelector(".aqe-spinner"))!=null&&_.hidden):!1,allButtonsDisabled:yr().every(m=>m.disabled),anyButtonDisabled:yr().some(m=>m.disabled),buttonIconCount:o.length,buttonIconStrokeValues:o.map(m=>m.getAttribute("stroke")||getComputedStyle(m).stroke||"")}}function sh(e){const t=e.dataset.playbackState;return oa(t)?t:"stopped"}function ih(e){const t=e.dataset.progressClockMode;return t==="audio"||t==="manual"||t==="stopped"?t:"stopped"}function Di(e){var t;return((t=e==null?void 0:e.querySelector(".aqe-button-label"))==null?void 0:t.textContent)||(e==null?void 0:e.textContent)||""}function lh(){window.__aqeSetBusy=ln,window.__aqeSetStatus=Jo,window.__aqeSetVisualizer=Pu,window.__aqeSetVisualizerStatus=Fu,window.__aqeResetGraphAfterEdit=Eu,window.__aqeSetPlaybackState=Ru,window.__aqeGetPlaybackRequest=Du,window.__aqeStopEditorPlayback=Ou,window.__aqeGetCursorMs=Lu,window.__aqeGetCursorIntent=Iu,window.__aqePrepareForNewNote=ss,window.__aqePopFrontendLog=al,window.__aqePopPendingGraphAnalysisRequest=il,window.__aqePopPendingRegionDeleteRequest=ul,th()}const uh=/\[sound:([^\]]+)\]/i,ch=/\.(aac|flac|m4a|mp3|oga|ogg|opus|wav|webm)$/i;let cr=[];function dh(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){Oi(),window.__AQE_EDITOR_CONFIG__=e,lh(),ss(),ql(),window.__aqeEditorDispose=Oi,pe.info("editor runtime initialized",{audioFieldIndices:e.audioFieldIndices,showGraphByDefault:e.showGraphByDefault===!0});const t=()=>fh(e);window.__aqeScan=t,so(t,0),so(t,250),so(t,1e3)}function Oi(){cr.forEach(e=>window.clearTimeout(e)),cr=[],zf()}function fh(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){if(e.audioFieldIndices.length){const r=ph(e.audioFieldIndices,e.audioFieldSources);r.forEach(a=>Li(a)),pe.debug("scan mounted explicit fields",{count:r.length}),_a(),Ii(e,r);return}const t=[];let n=0;hh().forEach((r,a)=>{const o=oo(r);if(!o)return;const s={node:r,ord:mh(r,a),sourceFilename:o};Li(s),t.push(s),n+=1}),pe.debug("scan mounted detected fields",{count:n}),_a(),Ii(e,t)}function hh(){const e=Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]')),t=new Set;return e.filter(n=>t.has(n)?!1:(t.add(n),!!(n.textContent||n.innerHTML)))}function ph(e,t={}){return e.map(n=>{const r=document.querySelector(`.field-container[data-index="${n}"]`);if(!r)return null;const a=r.querySelector('[contenteditable="true"]')||r,o=oo(a)||oo(r)||t[n]||"";return{ord:n,node:a,sourceFilename:o}}).filter(n=>n!==null)}function mh(e,t){const n=["data-field-ord","data-ord","data-index"];for(const a of n){const o=e.getAttribute(a);if(o!==null&&/^\d+$/.test(o))return Number(o)}const r=/(\d+)/.exec(String(e.id||""));return r?Number(r[1]):t}function oo(e){const t=e.innerHTML||e.textContent||"",n=uh.exec(t),r=n==null?void 0:n[1];return r&&ch.test(r)?r:""}function Li(e){Zf(e)}function Ii(e,t){e.showGraphByDefault&&Sl(t.map(({ord:n,sourceFilename:r})=>({ord:n,sourceFilename:r})),{anyBusy:()=>document.body.dataset.aqeBusy==="true",requestDefaultGraph:as})}function so(e,t){const n=window.setTimeout(()=>{cr=cr.filter(r=>r!==n),e()},t);cr.push(n)}dh()})();
