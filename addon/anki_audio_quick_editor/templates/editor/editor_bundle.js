var Lf=Object.defineProperty;var Ks=D=>{throw TypeError(D)};var $f=(D,O,Q)=>O in D?Lf(D,O,{enumerable:!0,configurable:!0,writable:!0,value:Q}):D[O]=Q;var Ve=(D,O,Q)=>$f(D,typeof O!="symbol"?O+"":O,Q),Sa=(D,O,Q)=>O.has(D)||Ks("Cannot "+Q);var h=(D,O,Q)=>(Sa(D,O,"read from private field"),Q?Q.call(D):O.get(D)),N=(D,O,Q)=>O.has(D)?Ks("Cannot add the same private member more than once"):O instanceof WeakSet?O.add(D):O.set(D,Q),P=(D,O,Q,In)=>(Sa(D,O,"write to private field"),In?In.call(D,Q):O.set(D,Q),Q),ne=(D,O,Q)=>(Sa(D,O,"access private method"),Q);(function(){"use strict";var Gs,Hs,Vs,zt,en,Ft,tn,xn,Tn,xt,Ze,nn,_e,ka,Aa,Ea,Xs,ke,wa,Ie,Tt,fe,Be,me,Re,Je,Rt,ht,rn,an,on,Ge,ur,z,If,Bf,Gf,Pa,vr,gr,Ca,js,De,He,ve,Dt,Rn,Dn,cr,Ws;const D=[{activeIcon:"pause",command:"aqe:play",icon:"play",iconOnly:!0,label:"Play",title:"Play or pause current audio"},{activeIcon:"refresh-cw",command:"aqe:analyze",icon:"chart-line",iconOnly:!0,label:"Graph",title:"Analyze and show pitch/intensity graph"},{command:"aqe:show-file",icon:"folder-open",label:"Folder",title:"Show current audio file in folder"},{command:"aqe:trim-left",icon:"scissors",label:"-L",title:"Trim 100 ms from left"},{command:"aqe:trim-right",icon:"scissors",label:"-R",title:"Trim 100 ms from right"},{command:"aqe:remove-pauses",icon:"timer-reset",label:"Shorten Pauses",title:"Speed up long internal pauses"},{command:"aqe:slower",icon:"rewind",label:"Slower",title:"Decrease speed"},{command:"aqe:faster",icon:"fast-forward",label:"Faster",title:"Increase speed"},{command:"aqe:volume-down",icon:"volume-1",iconOnly:!0,label:"Volume -",title:"Decrease volume"},{command:"aqe:volume-up",icon:"volume-2",iconOnly:!0,label:"Volume +",title:"Increase volume"},{command:"aqe:undo",icon:"undo-2",iconOnly:!0,label:"Undo",title:"Restore the previous generated audio reference"},{command:"aqe:redo",icon:"redo-2",iconOnly:!0,label:"Redo",title:"Restore the most recently undone audio reference"},{command:"aqe:settings",icon:"settings",iconOnly:!0,label:"Settings",title:"Open Audio Quick Editor settings"}],O=[{command:"aqe:denoise-standard",icon:"volume-x",label:"Standard",title:"Denoise speech with DeepFilterNet"},{command:"aqe:mp-senet",icon:"sparkles",label:"MP-SENet",title:"Denoise speech with MP-SENet"}],Q=new Set(["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:remove-pauses","aqe:denoise-standard","aqe:mp-senet","aqe:volume-down","aqe:volume-up"]),In={"aqe:play":"play","aqe:analyze":"graph","aqe:show-file":"show-file","aqe:trim-left":"trim-left","aqe:trim-right":"trim-right","aqe:remove-pauses":"remove-pauses","aqe:denoise-standard":"denoise-standard","aqe:mp-senet":"mp-senet","aqe:slower":"slower","aqe:faster":"faster","aqe:volume-down":"volume-down","aqe:volume-up":"volume-up","aqe:undo":"undo","aqe:redo":"redo","aqe:settings":"settings"};function Na(e,t){return`aqe-button-${e}-${In[t]}`}function Ys(e){return e==="aqe:denoise-standard"?"Denoising with Standard...":e==="aqe:mp-senet"?"Denoising with MP-SENet...":"Processing..."}function _t(e){return document.querySelector(`.aqe-controls[data-aqe-field-ord="${e}"]`)}function L(e){return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${e}"]`)}function Fa(e,t){const n=_t(e);return(n==null?void 0:n.querySelector(`[data-aqe-command="${t}"]`))??null}function xa(e){return Fa(e,"aqe:analyze")}function Ta(e){return Fa(e,"aqe:play")}function Ra(e){const t=_t(e);return(t==null?void 0:t.querySelector(".aqe-repeat-button"))??null}function Bn(){return Array.from(document.querySelectorAll(".aqe-button"))}function Da(){return Array.from(document.querySelectorAll(".aqe-visualizer"))}const Oa=[];function yr(e){globalThis.pycmd!==void 0&&globalThis.pycmd(e)}function sn(e,t){yr(`focus:${e}`),yr(t)}function Qs(e){Oa.push(e),yr("aqe:frontend-log")}function Zs(){return Oa.shift()??null}function Js(e){window.__aqePendingPlaybackRequest=e,window.__aqeLastPlaybackRequest=e}function zs(){if(!window.__aqePendingPlaybackRequest)return null;const e=window.__aqePendingPlaybackRequest;return window.__aqePendingPlaybackRequest=null,e}function ei(e){window.__aqeLastCursorIntent=e}function ti(e){return encodeURIComponent(e||"").replaceAll("%2F","/")}function Ee(e){return(e==null?void 0:e.querySelector(".aqe-audio-clock"))??null}function br(e){e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!1,e.__aqeAudioClockLastSeekedMs=0,e.dataset.progressClockMode="stopped"}function ln(e){const t=Ee(e);if(!(!t||typeof t.pause!="function"))try{t.pause()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function wr(e){const t=Ee(e);if(br(e),!!t){ln(e),t.removeAttribute("src"),t.src="";try{t.load()}catch{e.__aqeAudioClockFallback=!0}}}function ni(e,t){const n=Ee(e);if(br(e),!n){e.__aqeAudioClockFallback=!0;return}if(ln(e),!t){wr(e);return}n.setAttribute("src",ti(t));try{n.load()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function ri(e,t={}){const n=Ee(e);!n||n.__aqeClockHandlersInstalled||(n.__aqeClockHandlersInstalled=!0,n.addEventListener("loadedmetadata",()=>{n.getAttribute("src")&&(e.__aqeAudioClockAvailable=!0,e.__aqeAudioClockFallback=!1)}),n.addEventListener("error",()=>{var r;e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,e.dataset.playbackState==="playing"&&e.dataset.progressClockMode==="audio"&&((r=t.onErrorDuringPlayback)==null||r.call(t))}),n.addEventListener("ended",()=>{var r;e.dataset.playbackState==="playing"&&((r=t.onEndedDuringPlayback)==null||r.call(t))}),n.addEventListener("seeked",()=>{e.__aqeAudioClockLastSeekedMs=Math.round((Number(n.currentTime)||0)*1e3)}))}function Gn(e){const t=Ee(e);return!t||!(e!=null&&e.__aqeAudioClockAvailable)||!t.getAttribute("src")?!1:t.readyState===void 0||t.readyState>=1}function Hn(e,t,n){const r=Ee(e);if(!r)return!1;const a=Math.max(0,Math.min(Number(t)||0,n||0));try{return r.currentTime=a/1e3,e.__aqeAudioClockLastSeekedMs=Math.round(a),!0}catch{return e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,!1}}var un=(e=>(e.Debug="debug",e.Error="error",e.Info="info",e.Unknown="unknown",e.Warn="warn",e))(un||{});function ai(e){return e==="error"?console.error:console.warn}function oi(e){return e==="debug"?un.Debug:e==="warn"?un.Warn:e==="error"?un.Error:un.Info}function Mr(e,t=0){const n=si(e);return n!==void 0?n:Array.isArray(e)?ii(e,t):e!==null&&typeof e=="object"?li(e,t):ui(e)}function si(e){if(e===void 0)return"[undefined]";if(e===null)return null;if(typeof e=="boolean"||typeof e=="number"||typeof e=="string")return e}function ii(e,t){return t>=4?"[array]":e.map(n=>Mr(n,t+1))}function li(e,t){if(t>=4)return"[object]";const n={};for(const[r,a]of Object.entries(e))n[r]=Mr(a,t+1);return n}function ui(e){return typeof e=="bigint"?e.toString():typeof e=="symbol"?e.description?`Symbol(${e.description})`:"Symbol()":typeof e=="function"?`[function ${e.name||"anonymous"}]`:"[unserializable]"}function ci(e,t,n){const r={level:oi(e),message:t};return n!==void 0&&(r.context=Mr(n)),r}function fi(e,t){function n(r,a,o){const s=ai(r);o===void 0?s(`[${e}] ${a}`):s(`[${e}] ${a}`,o);try{t(ci(r,a,o))}catch{}}return{debug:(r,a)=>n("debug",r,a),error:(r,a)=>n("error",r,a),info:(r,a)=>n("info",r,a),warn:(r,a)=>n("warn",r,a)}}const de=fi("editor",Qs),cn=[],Vn=new Set;let jn=null,Wn=null,Un=!1;function di(){cn.length=0,Vn.clear(),jn=null,Wn=null,Un=!1}function hi(e,t){for(const n of e){if(!n.sourceFilename)continue;const r=pi(n);if(Vn.has(r))continue;const a=L(n.ord);if((a==null?void 0:a.dataset.hasTrack)==="true"&&a.dataset.sourceFilename===n.sourceFilename){Vn.add(r);continue}Vn.add(r),cn.push({key:r,ord:n.ord,sourceFilename:n.sourceFilename})}Kn(t)}function Kn(e){if(!(jn!==null||e.anyBusy()))for(;cn.length;){const t=cn.shift();if(!t)return;const n=L(t.ord);if(!n){$a(t,e);return}const r=_t(t.ord);if(!r){$a(t,e);return}if((r.dataset.aqeSourceFilename||t.sourceFilename)===t.sourceFilename&&!(n.dataset.hasTrack==="true"&&n.dataset.sourceFilename===t.sourceFilename)){jn=t.key,Wn=t.ord,e.requestGraph(t.ord,!0);return}}}function La(e,t){Wn===e&&(jn=null,Wn=null,queueMicrotask(()=>Kn(t)))}function pi(e){return`${e.ord}\0${e.sourceFilename}`}function $a(e,t){cn.unshift(e),!Un&&(Un=!0,window.setTimeout(()=>{Un=!1,Kn(t)},0))}function _i(e,t){return Math.max(t.startMs,Math.min(Number(e)||0,t.endMs))}function mi(e){let t="start";e.playbackState==="playing"&&(t="pause"),e.playbackState==="paused"&&(t=e.resumeRequiresRestart?"start":"resume");let n=e.anchorMs;return t==="start"&&e.region.mode==="selection"&&(n=e.region.startMs),t==="pause"&&(n=Ia(e.currentProgressMs,e.cursorMs,n)),t==="resume"&&(n=Ia(e.currentProgressMs,e.cursorMs,n),e.region.mode==="selection"&&(n<e.region.startMs||n>e.region.endMs)&&(t="start",n=e.region.startMs)),{action:t,cursorMs:Math.round(n),endMs:Math.round(e.region.endMs),engine:e.engine,loop:e.repeat,ord:e.ord,regionMode:e.region.mode}}function Ia(e,t,n){return Number(e||t||n||0)}function vi(e){return{analyzerName:e.analyzerName,durationMs:Number(e.durationMs)||0,pitchMaxHz:e.pitchMaxHz,pitchMinHz:e.pitchMinHz,points:e.points.map(gi),sourceFilename:e.sourceFilename}}function gi(e){const t=typeof e[0]=="number"?e[0]:0,n=typeof e[1]=="number"?e[1]:null,r=typeof e[2]=="number"?e[2]:null,a=typeof e[3]=="boolean"?e[3]:!1;return[t,n,r,a]}function Ba(e){return e==="playing"||e==="paused"||e==="stopped"}const Ga=50,yi=4;function Ha(){return{active:!1,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:null,startMs:null}}function Va(e,t){return Math.max(0,Math.min(Number(e)||0,Math.max(0,Number(t)||0)))}function Xn(e,t,n,r=Ga){const a=Va(Math.min(e,t),n),o=Va(Math.max(e,t),n);return!n||o-a<r?null:{startMs:Math.round(a),endMs:Math.round(o)}}function bi(e,t){if(!e.active||e.startMs===null||e.endMs===null)return null;const n=Xn(e.startMs,e.endMs,t);return n?{...n,mode:"selection"}:null}function wi(e,t){if(!e.draftActive||e.draftStartMs===null||e.draftEndMs===null)return null;const n=Xn(e.draftStartMs,e.draftEndMs,t);return n?{...n,mode:"selection"}:null}function Mi(e,t,n,r){const a=Xn(t,n,r);return a?{...e,active:!0,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:a.endMs,startMs:a.startMs}:Si(e)}function qi(e,t,n,r){const a=Xn(t,n,r);return a?{...e,draftActive:!0,draftEndMs:a.endMs,draftStartMs:a.startMs}:ja(e)}function Si(e){return{...ja(e),active:!1,endMs:null,startMs:null}}function ja(e){return{...e,draftActive:!1,draftEndMs:null,draftStartMs:null}}function Wa(e,t,n,r){return Math.abs(t.clientX-e.clientX)<yi||Math.abs(r-n)<Ga}const M={width:620,height:150,left:44,right:10,top:10,bottom:34};function Ua(){return M.width-M.left-M.right}function Ka(){return M.height-M.top-M.bottom}function et(e,t){return t?M.left+Math.max(0,Math.min(1,e/t))*Ua():M.left}function ki(e,t,n){if(!e||!t||!n||n<=t)return M.height-M.bottom;const r=Math.max(0,Math.min(1,(e-t)/(n-t)));return M.top+(1-r)*Ka()}function Xa(e,t){return t&&t<2e3?`${Math.round(e)} ms`:`${(e/1e3).toFixed(2)}s`}function Ai(e,t){if(!e.length||!t)return"";const n=M.height-M.bottom,r=e[0];if(!r)return"";const a=`M ${et(r[0],t).toFixed(2)} ${n.toFixed(2)}`,o=e.map(l=>{const d=et(l[0],t).toFixed(2),f=Math.max(0,Math.min(1,l[2]??0)),u=(n-f*Ka()).toFixed(2);return`L ${d} ${u}`}).join(" "),s=e.at(-1)??r,i=`L ${et(s[0],t).toFixed(2)} ${n.toFixed(2)} Z`;return`${a} ${o} ${i}`}function Ei(e,t,n,r){const a=[];let o=[];for(const s of e){const i=s[1];if(!(s[3]===!0&&i!==null&&i!==void 0)){o.length&&a.push(o),o=[];continue}o.push([et(s[0],t),ki(i,n,r)])}return o.length&&a.push(o),a}function Pi(e,t){const n=e.querySelector(".aqe-pitch");if(n){n.textContent="";for(const r of Ei(t.points,t.durationMs,t.pitchMinHz,t.pitchMaxHz)){if(r.length<2)continue;const a=document.createElementNS("http://www.w3.org/2000/svg","path");a.setAttribute("class","aqe-pitch-path"),a.setAttribute("d",r.map((o,s)=>{const i=o[0]??0,l=o[1]??0;return`${s?"L":"M"} ${i.toFixed(2)} ${l.toFixed(2)}`}).join(" ")),n.appendChild(a)}}}function Ci(e,t){const n=e.querySelector(".aqe-labels");if(!n)return;n.textContent="";const r=t.pitchMaxHz||500,a=t.pitchMinHz||75;for(const o of[[r,M.top+10],[a,M.height-M.bottom]]){const s=document.createElementNS("http://www.w3.org/2000/svg","text");s.setAttribute("class","aqe-hz-label"),s.setAttribute("x","2"),s.setAttribute("y",String(o[1])),s.textContent=`${Math.round(o[0])} Hz`,n.appendChild(s)}}function Ni(e,t){const n=e.querySelector(".aqe-x-axis");if(!n)return;n.textContent="";const r=[0,t/2,t].filter((a,o,s)=>o===0||a!==s[o-1]);for(const a of r){const o=et(a,t),s=document.createElementNS("http://www.w3.org/2000/svg","line");s.setAttribute("class","aqe-x-tick"),s.setAttribute("x1",o.toFixed(2)),s.setAttribute("x2",o.toFixed(2)),s.setAttribute("y1",String(M.height-M.bottom)),s.setAttribute("y2",String(M.height-M.bottom+4));const i=document.createElementNS("http://www.w3.org/2000/svg","text");i.setAttribute("class","aqe-x-label"),i.setAttribute("x",o.toFixed(2)),i.setAttribute("y",String(M.height-8)),i.textContent=Xa(a,t),n.append(s,i)}}function Ya(e){const t=e.getBoundingClientRect(),n=Number(t.width)||M.width,r=Number(t.height)||M.height,a=Math.min(n/M.width,r/M.height)||1;return{left:t.left+(n-M.width*a)/2+M.left*a,width:Ua()*a}}function fn(e,t,n){const r=Ya(t);return Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*n}function Fi(e){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="true",e.dataset.hasTrack="false",e.dataset.durationMs="0",e.dataset.sourceFilename="",e.dataset.anchorMs="0",e.dataset.cursorMs="0",e.dataset.progressMs="0",e.dataset.resumeRequiresRestart="false",e.dataset.playbackEngine="",e.dataset.playbackStartMs="0",e.dataset.playbackEndMs="0",e.dataset.playbackRegionMode="full",Qa(e)}function xi(e,t){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="false",e.dataset.hasTrack="true",e.dataset.durationMs=String(t.durationMs||0),e.dataset.analyzerName=t.analyzerName||"",e.dataset.sourceFilename=t.sourceFilename||"";const n=e.querySelector(".aqe-intensity");n&&n.setAttribute("d",Ai(t.points,t.durationMs)),Pi(e,t),Ci(e,t),Ni(e,t.durationMs||0)}function Ti(e,t,n="info"){const r=e.querySelector(".aqe-visualizer-status"),a=e.querySelector(".aqe-spinner"),o=n==="processing";e.dataset.graphBusy=o?"true":"false",a&&(a.hidden=!o),r&&(r.textContent=t||"",r.dataset.kind=n||"info")}function Ri(e,t,n){const r=e.querySelector(".aqe-selection"),a=e.querySelector(".aqe-selection-start"),o=e.querySelector(".aqe-selection-end"),s=n??t,i=Number(e.dataset.durationMs||"0");if(!r||!a||!o||!s||!i){r==null||r.setAttribute("width","0"),r==null||r.setAttribute("visibility","hidden"),r==null||r.classList.remove("aqe-selection-draft"),a==null||a.setAttribute("visibility","hidden"),o==null||o.setAttribute("visibility","hidden");return}const l=et(s.startMs,i),d=et(s.endMs,i);r.setAttribute("visibility","visible"),r.classList.toggle("aqe-selection-draft",n!==null),r.setAttribute("x",l.toFixed(2)),r.setAttribute("y",String(M.top)),r.setAttribute("width",Math.max(0,d-l).toFixed(2)),r.setAttribute("height",String(M.height-M.top-M.bottom)),a.setAttribute("visibility","visible"),o.setAttribute("visibility","visible");for(const[f,u]of[[a,l],[o,d]])f.setAttribute("x1",u.toFixed(2)),f.setAttribute("x2",u.toFixed(2)),f.setAttribute("y1",String(M.top)),f.setAttribute("y2",String(M.height-M.bottom))}function Di(e,t,n){const r=et(t,n),a=e.querySelector(".aqe-cursor");a&&(a.setAttribute("x1",r.toFixed(2)),a.setAttribute("x2",r.toFixed(2)));const o=e.querySelector(".aqe-cursor-label");o&&(o.textContent=Xa(t,n))}function Qa(e){var t;(t=e.querySelector(".aqe-intensity"))==null||t.setAttribute("d",""),qr(e,".aqe-pitch"),qr(e,".aqe-labels"),qr(e,".aqe-x-axis")}function Oi(e){const t=e.querySelector(".aqe-cursor");t&&(t.setAttribute("x1",String(M.left)),t.setAttribute("x2",String(M.left)));const n=e.querySelector(".aqe-cursor-label");n&&(n.textContent="0 ms")}function Li(e,t){return{analyzerName:t.analyzerName,durationMs:t.durationMs,ord:e,points:t.points.length,sourceFilename:t.sourceFilename}}function qr(e,t){const n=e.querySelector(t);n&&(n.textContent="")}function Sr(e){return!e||e.dataset.selectionActive!=="true"?null:bi({active:e.dataset.selectionActive==="true",startMs:Number(e.dataset.selectionStartMs||"0"),endMs:Number(e.dataset.selectionEndMs||"0")},Number(e.dataset.durationMs||"0"))}function kr(e){return!e||e.dataset.selectionDraftActive!=="true"?null:wi({draftActive:e.dataset.selectionDraftActive==="true",draftStartMs:Number(e.dataset.selectionDraftStartMs||"0"),draftEndMs:Number(e.dataset.selectionDraftEndMs||"0")},Number(e.dataset.durationMs||"0"))}function Za(e){const t=Sr(e);return t||{startMs:0,endMs:Number(e.dataset.durationMs||"0")||0,mode:"full"}}function Lt(e,t={}){e.dataset.selectionDraftActive="false",e.dataset.selectionDraftStartMs="",e.dataset.selectionDraftEndMs="",t.redraw!==!1&&Yn(e)}function $i(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=qi(Ha(),t,n,a);return!o.draftActive||o.draftStartMs===null||o.draftEndMs===null?(Lt(e,r),!1):(e.dataset.selectionDraftActive="true",e.dataset.selectionDraftStartMs=String(o.draftStartMs),e.dataset.selectionDraftEndMs=String(o.draftEndMs),r.redraw!==!1&&Yn(e),!0)}function Ii(e,t,n={}){const r=kr(e);return r?(Lt(e,{redraw:!1}),Bi(e,r.startMs,r.endMs,t,n)):(Lt(e),!1)}function Ja(e,t={}){if(e.dataset.selectionActive="false",e.dataset.selectionStartMs="",e.dataset.selectionEndMs="",Lt(e,{redraw:!1}),Yn(e),t.resetPlaybackRegion!==!1){const n=Za(e);e.dataset.playbackStartMs=String(Math.round(n.startMs)),e.dataset.playbackEndMs=String(Math.round(n.endMs)),e.dataset.playbackRegionMode=n.mode}}function Bi(e,t,n,r,a={}){const o=Number(e.dataset.durationMs||"0"),s=Mi(Ha(),t,n,o);return!s.active||s.startMs===null||s.endMs===null?(Ja(e),!1):(Lt(e,{redraw:!1}),e.dataset.selectionActive="true",e.dataset.selectionStartMs=String(s.startMs),e.dataset.selectionEndMs=String(s.endMs),e.dataset.playbackStartMs=String(s.startMs),e.dataset.playbackEndMs=String(s.endMs),e.dataset.playbackRegionMode="selection",Yn(e),a.updateCursor!==!1&&r.setCursor(e,s.startMs,!1),!0)}function Yn(e){const t=kr(e),n=t??Sr(e);Ri(e,n,t)}function Gi(e,t,n,r,a){e.preventDefault();const o=a.playbackStateFor(t),s=t.querySelector(".aqe-visualizer-svg"),i=Number(t.dataset.durationMs||"0");if(!s||!i)return;o==="playing"&&a.stopProgressClock(t);const l=f=>{a.setCursor(t,za(f,s,i,t,a),!1)},d=f=>{window.removeEventListener("pointermove",l),window.removeEventListener("pointerup",d);const u=o==="playing";o==="paused"&&(t.dataset.resumeRequiresRestart="true");const c=za(f,s,i,t,a),_=u&&a.audioClockReady(t)?"html":"";a.setCursor(t,c,r,{previousPlaybackState:o,restartPlayback:u,engine:_}),a.audioClockReady(t)&&a.seekAudioClock(t,c),u&&_==="html"&&a.startEditorHtmlPlayback(t,a.playbackRequestForStart(t,n,c,"html"))};l(e),window.addEventListener("pointermove",l),window.addEventListener("pointerup",d)}function Hi(e,t,n,r){e.preventDefault();const a=t.querySelector(".aqe-visualizer-svg"),o=Number(t.dataset.durationMs||"0");if(!a||!o)return;const s=r.playbackStateFor(t),i=r.currentProgressMs(t)??Number(t.dataset.cursorMs||"0"),l={clientX:e.clientX},d=fn(e,a,o);let f=!1,u=k=>{},c=k=>{},_=()=>{},v=k=>{};const w=()=>{window.removeEventListener("pointermove",u),window.removeEventListener("pointerup",c),window.removeEventListener("pointercancel",_),window.removeEventListener("keydown",v),window.removeEventListener("blur",_),a.removeEventListener("lostpointercapture",_)},p=()=>{f||s!=="playing"||(f=!0,r.stopProgressClock(t,{clearEngine:!1}),r.setCursor(t,i,!1,{updateAnchor:!1}))},m=()=>{s==="playing"&&f&&r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,i,"html"))};u=k=>{const b=fn(k,a,o);if(Wa(l,k,d,b)){r.clearSelectionDraft(t);return}p(),r.setSelectionDraft(t,d,b)},c=k=>{w();const b=fn(k,a,o);if(Wa(l,k,d,b)){r.clearSelection(t),m();return}p(),r.draftSelectionForVisualizer(t)||r.setSelectionDraft(t,d,b,{redraw:!1});const S=r.commitSelectionDraft(t);if(s==="paused"&&(t.dataset.resumeRequiresRestart="true"),S&&s==="playing"){const A=r.selectionForVisualizer(t);r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,(A==null?void 0:A.startMs)??d,"html"))}},_=()=>{w(),r.clearSelectionDraft(t),m()},v=k=>{k.key==="Escape"&&_()},window.addEventListener("pointermove",u),window.addEventListener("pointerup",c),window.addEventListener("pointercancel",_),window.addEventListener("keydown",v),window.addEventListener("blur",_),a.addEventListener("lostpointercapture",_)}function Vi(e,t,n){const r=n.visualizerForOrd(t);if(r){if(e.shiftKey){Hi(e,r,t,n);return}Gi(e,r,t,!0,n)}}function za(e,t,n,r,a){const o=fn(e,t,n),s=a.selectionForVisualizer(r);return s&&r.dataset.repeatEnabled==="true"?_i(o,s):o}function mt(e){e.__aqePlaybackTimer&&(window.cancelAnimationFrame(e.__aqePlaybackTimer),e.__aqePlaybackTimer=null)}function eo(e){const t=Number(e.dataset.durationMs||"0"),n=performance.now()-Number(e.dataset.playStartedAt||"0");return Math.min(t,Number(e.dataset.playStartMs||"0")+n)}function to(e){const t=Ee(e);if(!t)return null;const n=Number(e.dataset.durationMs||"0");return Math.min(n,(Number(t.currentTime)||0)*1e3)}function no(e){return e.dataset.progressClockMode==="audio"?to(e):e.dataset.progressClockMode==="manual"?eo(e):Number(e.dataset.progressMs||e.dataset.cursorMs||"0")}function Ar(e,t,n,r={}){return t<Xi(e,n)?!1:n.repeatEnabledFor(e)?(Yi(e,n,r),!0):(ji(e,n),!0)}function ji(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=t.effectivePlaybackRegion(e),a=e.dataset.playbackRegionMode==="selection"?r.startMs:Number(e.dataset.anchorMs||"0");Pr(e,t),t.setCursor(e,a,!1,{updateAnchor:!1}),Gn(e)&&Hn(e,a,Number(e.dataset.durationMs||"0")),t.clearStatus(n),window.__aqeActiveField=n,t.focusAndSendCommand(n,"aqe:play-ended")}function Er(e,t){const n=()=>{if(e.dataset.playbackState!=="playing")return;const r=to(e);if(r===null){je(e,Number(e.dataset.cursorMs||"0"),t);return}t.setCursor(e,r,!1,{updateAnchor:!1}),!Ar(e,r,t)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(n))};e.__aqePlaybackTimer=window.requestAnimationFrame(n)}function je(e,t,n){if(mt(e),ln(e),!Number(e.dataset.durationMs||"0"))return;const a=ro(e,t);e.__aqeAudioClockFallback=!0,e.dataset.playbackState="playing",e.dataset.progressClockMode="manual",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),Cr(e,a,n),n.setPlaybackButtonLabel(e,"Pause");const o=()=>{if(e.dataset.playbackState!=="playing")return;const s=eo(e);n.setCursor(e,s,!1,{updateAnchor:!1}),!Ar(e,s,n)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(o))};e.__aqePlaybackTimer=window.requestAnimationFrame(o)}function Wi(e,t,n,r={}){var i;const a=Ee(e);if(!a||!Hn(e,t,Number(e.dataset.durationMs||"0"))||typeof a.play!="function"){if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}je(e,t,n);return}e.dataset.progressClockMode="audio",e.__aqeAudioClockFallback=!1;const o=()=>{var l;if(r.manualFallback===!1){(l=r.onAudioPlayFailed)==null||l.call(r);return}je(e,t,n)},s=()=>{var l;e.dataset.playbackState==="playing"&&(mt(e),e.dataset.progressClockMode="audio",de.info("html audio playback started",{ord:e.dataset.aqeFieldOrd}),Er(e,n),(l=r.onAudioStarted)==null||l.call(r))};Promise.resolve(a.play()).then(s).catch(()=>{e.dataset.playbackState==="playing"&&(de.warn("html audio play rejected; using manual clock",{ord:e.dataset.aqeFieldOrd}),o())})}function Ui(e,t,n,r={}){var i;const a=r.engine||e.dataset.playbackEngine||"";if(Pr(e,n,{clearEngine:!1}),n.stopOtherPlayback(e),!Number(e.dataset.durationMs||"0"))return;const s=ro(e,t);if(e.dataset.playbackEngine=a,e.dataset.playbackState="playing",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(s),Cr(e,s,n),n.setCursor(e,s,!1,{updateAnchor:!1}),n.setPlaybackButtonLabel(e,"Pause"),de.info("playback clock selected",{engine:a||"auto",startMs:s}),a==="native"){je(e,s,n);return}if(Gn(e)){Wi(e,s,n,r);return}if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}je(e,s,n)}function Ki(e,t){const n=no(e);n!==null&&t.setCursor(e,n,!1,{updateAnchor:!1}),mt(e),ln(e),e.dataset.playbackState="paused",e.dataset.progressClockMode="stopped",t.setPlaybackButtonLabel(e,"Play")}function Pr(e,t,n={}){mt(e),ln(e),e.dataset.playbackState="stopped",e.dataset.progressClockMode="stopped",e.dataset.resumeRequiresRestart="false",n.clearEngine!==!1&&(e.dataset.playbackEngine=""),n.clearAudio&&wr(e),t.setPlaybackButtonLabel(e,"Play")}function Cr(e,t,n,r=n.effectivePlaybackRegion(e)){e.dataset.playbackStartMs=String(Math.round(t)),e.dataset.playbackEndMs=String(Math.round(r.endMs)),e.dataset.playbackRegionMode=r.mode}function Xi(e,t){const n=t.effectivePlaybackRegion(e),r=Number(e.dataset.playbackEndMs||"0")||n.endMs;return Math.max(n.startMs,Math.min(r,Number(e.dataset.durationMs||"0")||0))}function Yi(e,t,n={}){const r=t.effectivePlaybackRegion(e),a=r.startMs;if(Cr(e,a,t,r),e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),t.setCursor(e,a,!1,{updateAnchor:!1}),e.dataset.progressClockMode!=="audio"||!Gn(e)){je(e,a,t);return}if(!Hn(e,a,Number(e.dataset.durationMs||"0"))){je(e,a,t);return}if(!n.forceAudioPlay){mt(e),Er(e,t);return}const o=Ee(e);!o||typeof o.play!="function"||(mt(e),Promise.resolve(o.play()).then(()=>{e.dataset.playbackState==="playing"&&Er(e,t)}).catch(()=>{e.dataset.playbackState==="playing"&&je(e,a,t)}))}function ro(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function ao(){return document.body.dataset.aqeBusy==="true"}function oo(){var e;return((e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.repeatPlaybackByDefault)===!0}function Qi(e){for(const t of Da())t!==e&&It(t)!=="stopped"&&gt(t)}function Zi(){for(const e of Da())It(e)!=="stopped"&&gt(e)}function Qn(e,t,n="",r=""){document.body.dataset.aqeBusy=t?"true":"false",document.querySelectorAll(".aqe-controls").forEach(s=>{s.dataset.busy=t?"true":"false"}),Bn().forEach(s=>{s.disabled=!!t}),t||queueMicrotask(()=>Kn(Or()));const a=_t(e),o=a==null?void 0:a.querySelector(".aqe-status");o&&(o.textContent=n||"",o.dataset.kind=t?"processing":"info",o.title=r||"")}function so(e,t="info"){const n=Number(window.__aqeActiveField??0),r=_t(n),a=r==null?void 0:r.querySelector(".aqe-status");a&&(a.textContent=e||"",a.dataset.kind=t||"info")}function Ji(e){const t=_t(e),n=t==null?void 0:t.querySelector(".aqe-status");n&&(n.textContent="",n.dataset.kind="info",n.title="")}function $t(e,t,n){var o;const r=t==="aqe:play"?Ta(e):t==="aqe:analyze"?xa(e):((o=_t(e))==null?void 0:o.querySelector(`[data-aqe-command="${t}"]`))??null;if(!r)return;const a=r.querySelector(".aqe-button-label");a?a.textContent=n:r.textContent=n,t==="aqe:play"&&(r.dataset.aqeButtonState=n==="Pause"?"pause":"play"),t==="aqe:analyze"&&(r.dataset.aqeButtonState=n==="Redraw"?"redraw":"graph")}function io(e,t,n){if(!ao()){if(typeof t.focus=="function"&&t.focus(),window.__aqeActiveField=n,de.info("command dispatched",{command:e,ord:n}),e==="aqe:analyze"){Zn(n,!0);return}e==="aqe:play"&&bl(n)||(Q.has(e)&&(Zi(),Qn(n,!0,Ys(e))),sn(n,e))}}function zi(e){br(e)}function el(e){mt(e)}function tl(e){wr(e)}function nl(e,t){ni(e,t)}function rl(e){ri(e,{onErrorDuringPlayback(){de.warn("audio clock failed during playback",{ord:e.dataset.aqeFieldOrd}),yl(e,Number(e.dataset.cursorMs||"0"))},onEndedDuringPlayback(){gl(e,Number(e.dataset.durationMs||"0"),{forceAudioPlay:!0})}})}function Nr(e){return Gn(e)}function al(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function lo(e){return Sr(e)}function uo(e){return kr(e)}function Fr(e){return Za(e)}function xr(e,t){e.dataset.repeatEnabled=t?"true":"false";const n=Number(e.dataset.aqeFieldOrd||"0"),r=Ra(n);r&&(r.ariaPressed=t?"true":"false",r.dataset.aqeButtonState=t?"active":"default")}function ol(e,t){const n=L(e);return n?(xr(n,t),!0):!1}function sl(e,t={}){Lt(e,t)}function il(e,t,n,r={}){return $i(e,t,n,r)}function ll(e,t={}){return Ii(e,fl(),t)}function dn(e,t={}){Ja(e,t)}function ul(e){e.dataset.playbackStartMs="0",e.dataset.playbackEndMs=String(Number(e.dataset.durationMs||"0")||0),e.dataset.playbackRegionMode="full",xr(e,oo()),dn(e,{resetPlaybackRegion:!1})}function cl(){return{audioClockReady:Nr,clearSelection:dn,clearSelectionDraft:sl,commitSelectionDraft:ll,currentProgressMs:ho,draftSelectionForVisualizer:uo,playbackRequestForStart:dl,playbackStateFor:It,seekAudioClock:co,selectionForVisualizer:lo,setCursor:vt,setSelectionDraft:il,startEditorHtmlPlayback:vo,stopProgressClock:gt,visualizerForOrd:L}}function fl(){return{setCursor:vt}}function Tr(e){return e.dataset.repeatEnabled==="true"}function hn(){return{clearStatus:Ji,effectivePlaybackRegion:Fr,focusAndSendCommand:sn,playbackEngineFor:pn,repeatEnabledFor:Tr,setCursor:vt,setPlaybackButtonLabel:vl,stopOtherPlayback:Qi}}function dl(e,t,n,r=pn(e)){const a=Fr(e);return{ord:t,action:"start",cursorMs:Math.round(al(e,n)),endMs:Math.round(a.endMs),engine:r,loop:Tr(e),regionMode:a.mode}}function co(e,t){return Hn(e,t,Number(e.dataset.durationMs||"0"))}function vt(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Math.max(0,Math.min(Number(t)||0,a||0));if(e.dataset.cursorMs=String(Math.round(o)),e.dataset.progressMs=String(Math.round(o)),r.updateAnchor!==!1&&(e.dataset.anchorMs=String(Math.round(o))),Di(e,o,a),n){window.__aqeActiveField=Number(e.dataset.aqeFieldOrd||"0");const s={cursorMs:Math.round(o),previousPlaybackState:r.previousPlaybackState||It(e),restartPlayback:!!r.restartPlayback};r.engine&&(s.engine=r.engine),ei(s),de.info("cursor committed",s),sn(window.__aqeActiveField,"aqe:set-cursor")}}function hl(e,t){Vi(e,t,cl())}function Zn(e,t){const n=L(e);n&&(gt(n,{clearAudio:!0}),Fi(n),dn(n),vt(n,0,!1),$t(e,"aqe:analyze","Redraw"),Dr(e,"Analyzing...","processing"),window.__aqeActiveField=e,de.info("graph requested",{notifyPython:t,ord:e}),t&&(Qn(e,!0,"Analyzing...",""),sn(e,"aqe:analyze")))}function pl(e){return window.__aqePendingGraphRedrawField=e,Rr()}function Rr(){const e=window.__aqePendingGraphRedrawField;if(typeof e!="number")return!1;const t=L(e);return t?(t.dataset.graphBusy==="true"||t.dataset.hasTrack==="true"||Zn(e,!0),!0):!1}function Dr(e,t,n="info"){const r=L(e);r&&Ti(r,t,n)}function _l(e,t,n){const r=L(e);if(!r||!t)return;const a=vi(t);xi(r,a),r.dataset.anchorMs=String(n||0),window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null),dn(r),r.dataset.playbackStartMs="0",r.dataset.playbackEndMs=String(a.durationMs||0),r.dataset.playbackRegionMode="full",nl(r,a.sourceFilename||""),$t(e,"aqe:analyze","Redraw"),vt(r,n||0,!1),Nr(r)&&co(r,n||0),Dr(e,a.analyzerName||"","info"),Qn(e,!1,"",""),La(e,Or()),de.info("graph rendered",Li(e,a))}function ml(e,t,n="info"){n!=="processing"&&window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null);const r=L(e);r&&(r.hidden=!1,r.dataset.graphActive="true",n==="processing"&&(r.dataset.hasTrack="false"),$t(e,"aqe:analyze","Redraw")),Dr(e,t,n),n!=="processing"&&La(e,Or())}function Or(){return{anyBusy:ao,requestGraph:Zn}}function fo(){document.body.dataset.aqeBusy="false",window.__aqeActiveField=null,window.__aqeLastCursorIntent=null,document.querySelectorAll(".aqe-controls").forEach(e=>{e.dataset.busy="false",e.dataset.aqeSourceFilename="",e.querySelectorAll(".aqe-button").forEach(o=>{o.disabled=!1,o.dataset.aqeCommand==="aqe:analyze"&&$t(Number(e.dataset.aqeFieldOrd||"0"),"aqe:analyze","Graph"),o.dataset.aqeCommand==="aqe:play"&&$t(Number(e.dataset.aqeFieldOrd||"0"),"aqe:play","Play")});const t=e.querySelector(".aqe-status");t&&(t.textContent="",t.dataset.kind="info",t.title="");const n=e.querySelector(".aqe-visualizer");if(!n)return;el(n),tl(n),n.hidden=!0,n.dataset.anchorMs="0",n.dataset.cursorMs="0",n.dataset.progressMs="0",n.dataset.graphActive="false",n.dataset.graphBusy="false",n.dataset.hasTrack="false",n.dataset.playbackState="stopped",n.dataset.playbackEngine="",n.dataset.resumeRequiresRestart="false",n.dataset.durationMs="0",n.dataset.sourceFilename="",n.dataset.analyzerName="",n.dataset.playStartedAt="0",n.dataset.playStartMs="0",n.dataset.playbackStartMs="0",n.dataset.playbackEndMs="0",n.dataset.playbackRegionMode="full",n.dataset.progressClockMode="stopped",xr(n,oo()),dn(n),Qa(n),Oi(n);const r=n.querySelector(".aqe-visualizer-status");r&&(r.textContent="",r.dataset.kind="info");const a=n.querySelector(".aqe-spinner");a&&(a.hidden=!0)})}function vl(e,t){const n=Number(e.dataset.aqeFieldOrd||"0");$t(n,"aqe:play",t)}function ho(e){return no(e)}function gl(e,t,n={}){return Ar(e,t,hn(),n)}function yl(e,t){je(e,t,hn())}function po(e,t,n={}){Ui(e,t,hn(),n)}function _o(e){Ki(e,hn())}function gt(e,t={}){Pr(e,hn(),t)}function mo(e){const t=L(e);return t?mi({anchorMs:Number(t.dataset.anchorMs||t.dataset.cursorMs||"0"),currentProgressMs:ho(t),cursorMs:Number(t.dataset.cursorMs||"0"),engine:pn(t),ord:e,playbackState:It(t),region:Fr(t),repeat:Tr(t),resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true"}):{ord:e,action:"start",cursorMs:0}}function pn(e){if(!e||e.dataset.hasTrack!=="true")return"native";const t=e.dataset.playbackEngine||"";return e.dataset.playbackState!=="stopped"&&(t==="html"||t==="native")?t:Nr(e)?"html":"native"}function Lr(e){const t=L(e.ord);t&&(t.dataset.playbackEngine=e.engine||""),Js(e),window.__aqeActiveField=e.ord,de.info("playback request queued",e),sn(e.ord,"aqe:play")}function vo(e,t){return po(e,t.cursorMs,{engine:"html",manualFallback:!1,onAudioStarted(){Lr(t)},onAudioPlayFailed(){if(de.warn("html playback failed; falling back to native",{ord:t.ord}),gt(e),t.regionMode==="selection"||t.loop){window.__aqeActiveField=t.ord,so("Selected repeat playback needs browser audio.","warning");return}Lr({...t,engine:"native"})}}),!0}function bl(e){const t=L(e);if(!t||pn(t)!=="html")return!1;const n={...mo(e),engine:"html"};return n.action==="pause"?(_o(t),n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0"),Lr(n),!0):(n.action==="resume"&&(n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0")),vo(t,n))}function wl(e,t,n){const r=L(e);r&&((t==="playing"||t==="paused")&&(r.dataset.resumeRequiresRestart="false"),t==="playing"?po(r,n,{engine:r.dataset.playbackEngine==="html"||r.dataset.playbackEngine==="native"?r.dataset.playbackEngine:""}):t==="paused"?_o(r):gt(r))}function Ml(){const e=zs();if(e)return e;const t=Number(window.__aqeActiveField||"0"),n=mo(t),r=L(t);return r&&(r.dataset.playbackEngine=n.engine||""),n}function ql(e){const t=L(e);return t?(gt(t),!0):!1}function Sl(){const e=Number(window.__aqeActiveField||"0"),t=L(e);return t?Number(t.dataset.cursorMs||"0"):0}function kl(){const e=Number(window.__aqeActiveField||"0"),t=L(e),n=t?Number(t.dataset.cursorMs||"0"):0;return window.__aqeLastCursorIntent||{cursorMs:n,previousPlaybackState:t?It(t):"stopped",restartPlayback:!1}}function It(e){const t=e.dataset.playbackState;return Ba(t)?t:"stopped"}const go=(Hs=(Gs=globalThis.process)==null?void 0:Gs.env)==null?void 0:Hs.NODE_ENV,y=go&&!go.toLowerCase().startsWith("prod");var $r=Array.isArray,Al=Array.prototype.indexOf,yt=Array.prototype.includes,Jn=Array.from,bt=Object.defineProperty,We=Object.getOwnPropertyDescriptor,El=Object.getOwnPropertyDescriptors,Pl=Object.prototype,Cl=Array.prototype,yo=Object.getPrototypeOf,bo=Object.isExtensible;function _n(e){return typeof e=="function"}const H=()=>{};function Nl(e){for(var t=0;t<e.length;t++)e[t]()}function wo(){var e,t,n=new Promise((r,a)=>{e=r,t=a});return{promise:n,resolve:e,reject:t}}function Fl(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const r of e)if(n.push(r),n.length===t)break;return n}const re=2,mn=4,zn=8,Ir=1<<24,Ue=16,Pe=32,wt=64,Br=128,be=512,ee=1024,ae=2048,Ce=4096,he=8192,Ke=16384,Mt=32768,tt=65536,er=1<<17,Mo=1<<18,Bt=1<<19,xl=1<<20,Xe=1<<25,nt=65536,Gr=1<<21,tr=1<<22,rt=1<<23,at=Symbol("$state"),qo=Symbol("legacy props"),Tl=Symbol(""),So=Symbol("proxy path"),qt=new class extends Error{constructor(){super(...arguments);Ve(this,"name","StaleReactionError");Ve(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}},ko=!!((Vs=globalThis.document)!=null&&Vs.contentType)&&globalThis.document.contentType.includes("xml");function Ao(e){if(y){const t=new Error(`lifecycle_outside_component
\`${e}(...)\` can only be used during component initialisation
https://svelte.dev/e/lifecycle_outside_component`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/lifecycle_outside_component")}function Rl(){if(y){const e=new Error("async_derived_orphan\nCannot create a `$derived(...)` with an `await` expression outside of an effect tree\nhttps://svelte.dev/e/async_derived_orphan");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/async_derived_orphan")}function Dl(){if(y){const e=new Error(`derived_references_self
A derived value cannot reference itself recursively
https://svelte.dev/e/derived_references_self`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/derived_references_self")}function Eo(e,t,n){if(y){const r=new Error(`each_key_duplicate
${n?`Keyed each block has duplicate key \`${n}\` at indexes ${e} and ${t}`:`Keyed each block has duplicate key at indexes ${e} and ${t}`}
https://svelte.dev/e/each_key_duplicate`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_duplicate")}function Ol(e,t,n){if(y){const r=new Error(`each_key_volatile
Keyed each block has key that is not idempotent — the key for item at index ${e} was \`${t}\` but is now \`${n}\`. Keys must be the same each time for a given item
https://svelte.dev/e/each_key_volatile`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_volatile")}function Ll(e){if(y){const t=new Error(`effect_in_teardown
\`${e}\` cannot be used inside an effect cleanup function
https://svelte.dev/e/effect_in_teardown`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_in_teardown")}function $l(){if(y){const e=new Error("effect_in_unowned_derived\nEffect cannot be created inside a `$derived` value that was not itself created inside an effect\nhttps://svelte.dev/e/effect_in_unowned_derived");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function Il(e){if(y){const t=new Error(`effect_orphan
\`${e}\` can only be used inside an effect (e.g. during component initialisation)
https://svelte.dev/e/effect_orphan`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_orphan")}function Bl(){if(y){const e=new Error(`effect_update_depth_exceeded
Maximum update depth exceeded. This typically indicates that an effect reads and writes the same piece of state
https://svelte.dev/e/effect_update_depth_exceeded`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function Gl(){if(y){const e=new Error("invalid_snippet\nCould not `{@render}` snippet due to the expression being `null` or `undefined`. Consider using optional chaining `{@render snippet?.()}`\nhttps://svelte.dev/e/invalid_snippet");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/invalid_snippet")}function Hl(e){if(y){const t=new Error(`props_invalid_value
Cannot do \`bind:${e}={undefined}\` when \`${e}\` has a fallback value
https://svelte.dev/e/props_invalid_value`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_invalid_value")}function Vl(e){if(y){const t=new Error(`props_rest_readonly
Rest element properties of \`$props()\` such as \`${e}\` are readonly
https://svelte.dev/e/props_rest_readonly`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_rest_readonly")}function jl(e){if(y){const t=new Error(`rune_outside_svelte
The \`${e}\` rune is only available inside \`.svelte\` and \`.svelte.js/ts\` files
https://svelte.dev/e/rune_outside_svelte`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/rune_outside_svelte")}function Wl(){if(y){const e=new Error("state_descriptors_fixed\nProperty descriptors defined on `$state` objects must contain `value` and always be `enumerable`, `configurable` and `writable`.\nhttps://svelte.dev/e/state_descriptors_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function Ul(){if(y){const e=new Error("state_prototype_fixed\nCannot set prototype of `$state` object\nhttps://svelte.dev/e/state_prototype_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Kl(){if(y){const e=new Error("state_unsafe_mutation\nUpdating state inside `$derived(...)`, `$inspect(...)` or a template expression is forbidden. If the value should not be reactive, declare it without `$state`\nhttps://svelte.dev/e/state_unsafe_mutation");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Xl(){if(y){const e=new Error("svelte_boundary_reset_onerror\nA `<svelte:boundary>` `reset` function cannot be called while an error is still being handled\nhttps://svelte.dev/e/svelte_boundary_reset_onerror");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Yl=1,Ql=2,Po=4,Zl=8,Jl=16,zl=1,eu=4,tu=8,nu=16,ru=1,au=2,te=Symbol(),ou=Symbol("filename"),Co="http://www.w3.org/1999/xhtml",su="http://www.w3.org/2000/svg",iu="@attach";var vn="font-weight: bold",gn="font-weight: normal";function lu(){y?console.warn(`%c[svelte] lifecycle_double_unmount
%cTried to unmount a component that was not mounted
https://svelte.dev/e/lifecycle_double_unmount`,vn,gn):console.warn("https://svelte.dev/e/lifecycle_double_unmount")}function uu(){y?console.warn("%c[svelte] select_multiple_invalid_value\n%cThe `value` property of a `<select multiple>` element should be an array, but it received a non-array value. The selection will be kept as is.\nhttps://svelte.dev/e/select_multiple_invalid_value",vn,gn):console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function Hr(e){y?console.warn(`%c[svelte] state_proxy_equality_mismatch
%cReactive \`$state(...)\` proxies and the values they proxy have different identities. Because of this, comparisons with \`${e}\` will produce unexpected results
https://svelte.dev/e/state_proxy_equality_mismatch`,vn,gn):console.warn("https://svelte.dev/e/state_proxy_equality_mismatch")}function cu(){y?console.warn(`%c[svelte] state_proxy_unmount
%cTried to unmount a state proxy, rather than a component
https://svelte.dev/e/state_proxy_unmount`,vn,gn):console.warn("https://svelte.dev/e/state_proxy_unmount")}function fu(){y?console.warn("%c[svelte] svelte_boundary_reset_noop\n%cA `<svelte:boundary>` `reset` function only resets the boundary the first time it is called\nhttps://svelte.dev/e/svelte_boundary_reset_noop",vn,gn):console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function No(e){return e===this.v}function du(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function Fo(e){return!du(e,this.v)}let hu=!1;function Le(e,t){return e.label=t,xo(e.v,t),e}function xo(e,t){var n;return(n=e==null?void 0:e[So])==null||n.call(e,t),e}function pu(e){const t=new Error,n=_u();return n.length===0?null:(n.unshift(`
`),bt(t,"stack",{value:n.join(`
`)}),bt(t,"name",{value:e}),t)}function _u(){const e=Error.stackTraceLimit;Error.stackTraceLimit=1/0;const t=new Error().stack;if(Error.stackTraceLimit=e,!t)return[];const n=t.split(`
`),r=[];for(let a=0;a<n.length;a++){const o=n[a],s=o.replaceAll("\\","/");if(o.trim()!=="Error"){if(o.includes("validate_each_keys"))return[];s.includes("svelte/src/internal")||s.includes("node_modules/.vite")||r.push(o)}}return r}let G=null;function Gt(e){G=e}let Ht=null;function nr(e){Ht=e}let yn=null;function To(e){yn=e}function mu(e){return vu("getContext").get(e)}function $(e,t=!1,n){G={p:G,i:!1,c:null,e:null,s:e,x:null,l:null},y&&(G.function=n,yn=n)}function I(e){var t=G,n=t.e;if(n!==null){t.e=null;for(var r of n)ns(r)}return t.i=!0,G=t.p,y&&(yn=(G==null?void 0:G.function)??null),{}}function Ro(){return!0}function vu(e){return G===null&&Ao(e),G.c??(G.c=new Map(gu(G)||void 0))}function gu(e){let t=e.p;for(;t!==null;){const n=t.c;if(n!==null)return n;t=t.p}return null}let Vt=[];function yu(){var e=Vt;Vt=[],Nl(e)}function Ye(e){if(Vt.length===0){var t=Vt;queueMicrotask(()=>{t===Vt&&yu()})}Vt.push(e)}const Vr=new WeakMap;function Do(e){var t=F;if(t===null)return C.f|=rt,e;if(y&&e instanceof Error&&!Vr.has(e)&&Vr.set(e,bu(e,t)),(t.f&Mt)===0&&(t.f&mn)===0)throw y&&!t.parent&&e instanceof Error&&Oo(e),e;ot(e,t)}function ot(e,t){for(;t!==null;){if((t.f&Br)!==0){if((t.f&Mt)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw y&&e instanceof Error&&Oo(e),e}function bu(e,t){var s,i,l;const n=We(e,"message");if(!(n&&!n.configurable)){for(var r=Jr?"  ":"	",a=`
${r}in ${((s=t.fn)==null?void 0:s.name)||"<unknown>"}`,o=t.ctx;o!==null;)a+=`
${r}in ${(i=o.function)==null?void 0:i[ou].split("/").pop()}`,o=o.p;return{message:e.message+`
${a}
`,stack:(l=e.stack)==null?void 0:l.split(`
`).filter(d=>!d.includes("svelte/src/internal")).join(`
`)}}}function Oo(e){const t=Vr.get(e);t&&(bt(e,"message",{value:t.message}),bt(e,"stack",{value:t.stack}))}const wu=-7169;function V(e,t){e.f=e.f&wu|t}function jr(e){(e.f&be)!==0||e.deps===null?V(e,ee):V(e,Ce)}function Lo(e){if(e!==null)for(const t of e)(t.f&re)===0||(t.f&nt)===0||(t.f^=nt,Lo(t.deps))}function $o(e,t,n){(e.f&ae)!==0?t.add(e):(e.f&Ce)!==0&&n.add(e),Lo(e.deps),V(e,ee)}const rr=new Set;let T=null,oe=null,we=[],Wr=null,Ur=!1;const ba=class ba{constructor(){N(this,_e);Ve(this,"current",new Map);Ve(this,"previous",new Map);N(this,zt,new Set);N(this,en,new Set);N(this,Ft,0);N(this,tn,0);N(this,xn,null);N(this,Tn,new Set);N(this,xt,new Set);N(this,Ze,new Map);Ve(this,"is_fork",!1);N(this,nn,!1)}skip_effect(t){h(this,Ze).has(t)||h(this,Ze).set(t,{d:[],m:[]})}unskip_effect(t){var n=h(this,Ze).get(t);if(n){h(this,Ze).delete(t);for(var r of n.d)V(r,ae),Fe(r);for(r of n.m)V(r,Ce),Fe(r)}}process(t){var a;we=[],this.apply();var n=[],r=[];for(const o of t)ne(this,_e,Aa).call(this,o,n,r);if(ne(this,_e,ka).call(this)){ne(this,_e,Ea).call(this,r),ne(this,_e,Ea).call(this,n);for(const[o,s]of h(this,Ze))Ho(o,s)}else{for(const o of h(this,zt))o();h(this,zt).clear(),h(this,Ft)===0&&ne(this,_e,Xs).call(this),T=null,Io(r),Io(n),(a=h(this,xn))==null||a.resolve()}oe=null}capture(t,n){n!==te&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&rt)===0&&(this.current.set(t,t.v),oe==null||oe.set(t,t.v))}activate(){T=this,this.apply()}deactivate(){T===this&&(T=null,oe=null)}flush(){if(this.activate(),we.length>0){if(Mu(),T!==null&&T!==this)return}else h(this,Ft)===0&&this.process([]);this.deactivate()}discard(){for(const t of h(this,en))t(this);h(this,en).clear()}increment(t){P(this,Ft,h(this,Ft)+1),t&&P(this,tn,h(this,tn)+1)}decrement(t){P(this,Ft,h(this,Ft)-1),t&&P(this,tn,h(this,tn)-1),!h(this,nn)&&(P(this,nn,!0),Ye(()=>{P(this,nn,!1),ne(this,_e,ka).call(this)?we.length>0&&this.flush():this.revive()}))}revive(){for(const t of h(this,Tn))h(this,xt).delete(t),V(t,ae),Fe(t);for(const t of h(this,xt))V(t,Ce),Fe(t);this.flush()}oncommit(t){h(this,zt).add(t)}ondiscard(t){h(this,en).add(t)}settled(){return(h(this,xn)??P(this,xn,wo())).promise}static ensure(){if(T===null){const t=T=new ba;rr.add(T),Ye(()=>{T===t&&t.flush()})}return T}apply(){}};zt=new WeakMap,en=new WeakMap,Ft=new WeakMap,tn=new WeakMap,xn=new WeakMap,Tn=new WeakMap,xt=new WeakMap,Ze=new WeakMap,nn=new WeakMap,_e=new WeakSet,ka=function(){return this.is_fork||h(this,tn)>0},Aa=function(t,n,r){t.f^=ee;for(var a=t.first;a!==null;){var o=a.f,s=(o&(Pe|wt))!==0,i=s&&(o&ee)!==0,l=i||(o&he)!==0||h(this,Ze).has(a);if(!l&&a.fn!==null){s?a.f^=ee:(o&mn)!==0?n.push(a):Sn(a)&&((o&Ue)!==0&&h(this,xt).add(a),Yt(a));var d=a.first;if(d!==null){a=d;continue}}for(;a!==null;){var f=a.next;if(f!==null){a=f;break}a=a.parent}}},Ea=function(t){for(var n=0;n<t.length;n+=1)$o(t[n],h(this,Tn),h(this,xt))},Xs=function(){var a;if(rr.size>1){this.previous.clear();var t=oe,n=!0;for(const o of rr){if(o===this){n=!1;continue}const s=[];for(const[l,d]of this.current){if(o.current.has(l))if(n&&d!==o.current.get(l))o.current.set(l,d);else continue;s.push(l)}if(s.length===0)continue;const i=[...o.current.keys()].filter(l=>!this.current.has(l));if(i.length>0){var r=we;we=[];const l=new Set,d=new Map;for(const f of s)Bo(f,i,l,d);if(we.length>0){T=o,o.apply();for(const f of we)ne(a=o,_e,Aa).call(a,f,[],[]);o.deactivate()}we=r}}T=null,oe=t}rr.delete(this)};let st=ba;function Mu(){Ur=!0;var e=y?new Set:null;try{for(var t=0;we.length>0;){var n=st.ensure();if(t++>1e3){if(y){var r=new Map;for(const o of n.current.keys())for(const[s,i]of o.updated??[]){var a=r.get(s);a||(a={error:i.error,count:0},r.set(s,a)),a.count+=i.count}for(const o of r.values())o.error&&console.error(o.error)}qu()}if(n.process(we),it.clear(),y)for(const o of n.current.keys())e.add(o)}}finally{if(we=[],Ur=!1,Wr=null,y)for(const o of e)o.updated=null}}function qu(){try{Bl()}catch(e){y&&bt(e,"stack",{value:""}),ot(e,Wr)}}let Ne=null;function Io(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var r=e[n++];if((r.f&(Ke|he))===0&&Sn(r)&&(Ne=new Set,Yt(r),r.deps===null&&r.first===null&&r.nodes===null&&r.teardown===null&&r.ac===null&&ss(r),(Ne==null?void 0:Ne.size)>0)){it.clear();for(const a of Ne){if((a.f&(Ke|he))!==0)continue;const o=[a];let s=a.parent;for(;s!==null;)Ne.has(s)&&(Ne.delete(s),o.push(s)),s=s.parent;for(let i=o.length-1;i>=0;i--){const l=o[i];(l.f&(Ke|he))===0&&Yt(l)}}Ne.clear()}}Ne=null}}function Bo(e,t,n,r){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const a of e.reactions){const o=a.f;(o&re)!==0?Bo(a,t,n,r):(o&(tr|Ue))!==0&&(o&ae)===0&&Go(a,t,r)&&(V(a,ae),Fe(a))}}function Go(e,t,n){const r=n.get(e);if(r!==void 0)return r;if(e.deps!==null)for(const a of e.deps){if(yt.call(t,a))return!0;if((a.f&re)!==0&&Go(a,t,n))return n.set(a,!0),!0}return n.set(e,!1),!1}function Fe(e){var t=Wr=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(mn|zn|Ir))!==0&&(e.f&Mt)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var r=t.f;if(Ur&&t===F&&(r&Ue)!==0&&(r&Mo)===0&&(r&Mt)!==0)return;if((r&(wt|Pe))!==0){if((r&ee)===0)return;t.f^=ee}}we.push(t)}function Ho(e,t){if(!((e.f&Pe)!==0&&(e.f&ee)!==0)){(e.f&ae)!==0?t.d.push(e):(e.f&Ce)!==0&&t.m.push(e),V(e,ee);for(var n=e.first;n!==null;)Ho(n,t),n=n.next}}function Su(e){let t=0,n=St(0),r;return y&&Le(n,"createSubscriber version"),()=>{ea()&&(E(n),Yu(()=>(t===0&&(r=oa(()=>e(()=>bn(n)))),t+=1,()=>{Ye(()=>{t-=1,t===0&&(r==null||r(),r=void 0,bn(n))})})))}}var ku=tt|Bt;function Au(e,t,n,r){new Eu(e,t,n,r)}class Eu{constructor(t,n,r,a){N(this,z);Ve(this,"parent");Ve(this,"is_pending",!1);Ve(this,"transform_error");N(this,ke);N(this,wa,null);N(this,Ie);N(this,Tt);N(this,fe);N(this,Be,null);N(this,me,null);N(this,Re,null);N(this,Je,null);N(this,Rt,0);N(this,ht,0);N(this,rn,!1);N(this,an,new Set);N(this,on,new Set);N(this,Ge,null);N(this,ur,Su(()=>(P(this,Ge,St(h(this,Rt))),y&&Le(h(this,Ge),"$effect.pending()"),()=>{P(this,Ge,null)})));var o;P(this,ke,t),P(this,Ie,n),P(this,Tt,s=>{var i=F;i.b=this,i.f|=Br,r(s)}),this.parent=F.b,this.transform_error=a??((o=this.parent)==null?void 0:o.transform_error)??(s=>s),P(this,fe,qn(()=>{ne(this,z,Pa).call(this)},ku))}defer_effect(t){$o(t,h(this,an),h(this,on))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!h(this,Ie).pending}update_pending_count(t){ne(this,z,Ca).call(this,t),P(this,Rt,h(this,Rt)+t),!(!h(this,Ge)||h(this,rn))&&(P(this,rn,!0),Ye(()=>{P(this,rn,!1),h(this,Ge)&&Wt(h(this,Ge),h(this,Rt))}))}get_effect_pending(){return h(this,ur).call(this),E(h(this,Ge))}error(t){var n=h(this,Ie).onerror;let r=h(this,Ie).failed;if(!n&&!r)throw t;h(this,Be)&&(se(h(this,Be)),P(this,Be,null)),h(this,me)&&(se(h(this,me)),P(this,me,null)),h(this,Re)&&(se(h(this,Re)),P(this,Re,null));var a=!1,o=!1;const s=()=>{if(a){fu();return}a=!0,o&&Xl(),h(this,Re)!==null&&At(h(this,Re),()=>{P(this,Re,null)}),ne(this,z,gr).call(this,()=>{st.ensure(),ne(this,z,Pa).call(this)})},i=l=>{try{o=!0,n==null||n(l,s),o=!1}catch(d){ot(d,h(this,fe)&&h(this,fe).parent)}r&&P(this,Re,ne(this,z,gr).call(this,()=>{st.ensure();try{return ue(()=>{var d=F;d.b=this,d.f|=Br,r(h(this,ke),()=>l,()=>s)})}catch(d){return ot(d,h(this,fe).parent),null}}))};Ye(()=>{var l;try{l=this.transform_error(t)}catch(d){ot(d,h(this,fe)&&h(this,fe).parent);return}l!==null&&typeof l=="object"&&typeof l.then=="function"?l.then(i,d=>ot(d,h(this,fe)&&h(this,fe).parent)):i(l)})}}ke=new WeakMap,wa=new WeakMap,Ie=new WeakMap,Tt=new WeakMap,fe=new WeakMap,Be=new WeakMap,me=new WeakMap,Re=new WeakMap,Je=new WeakMap,Rt=new WeakMap,ht=new WeakMap,rn=new WeakMap,an=new WeakMap,on=new WeakMap,Ge=new WeakMap,ur=new WeakMap,z=new WeakSet,If=function(){try{P(this,Be,ue(()=>h(this,Tt).call(this,h(this,ke))))}catch(t){this.error(t)}},Bf=function(t){const n=h(this,Ie).failed;n&&P(this,Re,ue(()=>{n(h(this,ke),()=>t,()=>()=>{})}))},Gf=function(){const t=h(this,Ie).pending;t&&(this.is_pending=!0,P(this,me,ue(()=>t(h(this,ke)))),Ye(()=>{var n=P(this,Je,document.createDocumentFragment()),r=Qe();n.append(r),P(this,Be,ne(this,z,gr).call(this,()=>(st.ensure(),ue(()=>h(this,Tt).call(this,r))))),h(this,ht)===0&&(h(this,ke).before(n),P(this,Je,null),At(h(this,me),()=>{P(this,me,null)}),ne(this,z,vr).call(this))}))},Pa=function(){try{if(this.is_pending=this.has_pending_snippet(),P(this,ht,0),P(this,Rt,0),P(this,Be,ue(()=>{h(this,Tt).call(this,h(this,ke))})),h(this,ht)>0){var t=P(this,Je,document.createDocumentFragment());us(h(this,Be),t);const n=h(this,Ie).pending;P(this,me,ue(()=>n(h(this,ke))))}else ne(this,z,vr).call(this)}catch(n){this.error(n)}},vr=function(){this.is_pending=!1;for(const t of h(this,an))V(t,ae),Fe(t);for(const t of h(this,on))V(t,Ce),Fe(t);h(this,an).clear(),h(this,on).clear()},gr=function(t){var n=F,r=C,a=G;Te(h(this,fe)),Me(h(this,fe)),Gt(h(this,fe).ctx);try{return t()}catch(o){return Do(o),null}finally{Te(n),Me(r),Gt(a)}},Ca=function(t){var n;if(!this.has_pending_snippet()){this.parent&&ne(n=this.parent,z,Ca).call(n,t);return}P(this,ht,h(this,ht)+t),h(this,ht)===0&&(ne(this,z,vr).call(this),h(this,me)&&At(h(this,me),()=>{P(this,me,null)}),h(this,Je)&&(h(this,ke).before(h(this,Je)),P(this,Je,null)))};function Vo(e,t,n,r){const a=ar;var o=e.filter(u=>!u.settled);if(n.length===0&&o.length===0){r(t.map(a));return}var s=F,i=Pu(),l=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(u=>u.promise)):null;function d(u){i();try{r(u)}catch(c){(s.f&Ke)===0&&ot(c,s)}Kr()}if(n.length===0){l.then(()=>d(t.map(a)));return}function f(){i(),Promise.all(n.map(u=>Fu(u))).then(u=>d([...t.map(a),...u])).catch(u=>ot(u,s))}l?l.then(f):f()}function Pu(){var e=F,t=C,n=G,r=T;if(y)var a=Ht;return function(s=!0){Te(e),Me(t),Gt(n),s&&(r==null||r.activate()),y&&nr(a)}}function Kr(e=!0){Te(null),Me(null),Gt(null),e&&(T==null||T.deactivate()),y&&nr(null)}function Cu(){var e=F.b,t=T,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}const Nu=new Set;function ar(e){var t=re|ae,n=C!==null&&(C.f&re)!==0?C:null;return F!==null&&(F.f|=Bt),{ctx:G,deps:null,effects:null,equals:No,f:t,fn:e,reactions:null,rv:0,v:te,wv:0,parent:n??F,ac:null}}function Fu(e,t,n){F===null&&Rl();var a=void 0,o=St(te);y&&(o.label=t);var s=!C,i=new Map;return Xu(()=>{var c;var l=wo();a=l.promise;try{Promise.resolve(e()).then(l.resolve,l.reject).finally(Kr)}catch(_){l.reject(_),Kr()}var d=T;if(s){var f=Cu();(c=i.get(d))==null||c.reject(qt),i.delete(d),i.set(d,l)}const u=(_,v=void 0)=>{if(d.activate(),v)v!==qt&&(o.f|=rt,Wt(o,v));else{(o.f&rt)!==0&&(o.f^=rt),Wt(o,_);for(const[w,p]of i){if(i.delete(w),w===d)break;p.reject(qt)}}f&&f()};l.promise.then(u,_=>u(null,_||"unknown"))}),ta(()=>{for(const l of i.values())l.reject(qt)}),y&&(o.f|=tr),new Promise(l=>{function d(f){function u(){f===a?l(o):d(a)}f.then(u,u)}d(a)})}function Xr(e){const t=ar(e);return fs(t),t}function jo(e){const t=ar(e);return t.equals=Fo,t}function Wo(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)se(t[n])}}let Yr=[];function xu(e){for(var t=e.parent;t!==null;){if((t.f&re)===0)return(t.f&Ke)===0?t:null;t=t.parent}return null}function Qr(e){var t,n=F;if(Te(xu(e)),y){let r=jt;Xo(new Set);try{yt.call(Yr,e)&&Dl(),Yr.push(e),e.f&=~nt,Wo(e),t=aa(e)}finally{Te(n),Xo(r),Yr.pop()}}else try{e.f&=~nt,Wo(e),t=aa(e)}finally{Te(n)}return t}function Uo(e){var t=Qr(e);if(!e.equals(t)&&(e.wv=ps(),(!(T!=null&&T.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){V(e,ee);return}ct||(oe!==null?(ea()||T!=null&&T.is_fork)&&oe.set(e,t):jr(e))}function Tu(e){var t,n;if(e.effects!==null)for(const r of e.effects)(r.teardown||r.ac)&&((t=r.teardown)==null||t.call(r),(n=r.ac)==null||n.abort(qt),r.teardown=H,r.ac=null,kn(r,0),na(r))}function Ko(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&Yt(t)}let jt=new Set;const it=new Map;function Xo(e){jt=e}let Zr=!1;function Ru(){Zr=!0}function St(e,t){var n={f:0,v:e,reactions:null,equals:No,rv:0,wv:0};return n}function lt(e,t){const n=St(e);return fs(n),n}function Du(e,t=!1,n=!0){const r=St(e);return t||(r.equals=Fo),r}function ut(e,t,n=!1){C!==null&&(!xe||(C.f&er)!==0)&&Ro()&&(C.f&(re|Ue|tr|er))!==0&&(qe===null||!yt.call(qe,e))&&Kl();let r=n?Ut(t):t;return y&&xo(r,e.label),Wt(e,r)}function Wt(e,t){var a;if(!e.equals(t)){var n=e.v;ct?it.set(e,t):it.set(e,n),e.v=t;var r=st.ensure();if(r.capture(e,n),y){if(F!==null){e.updated??(e.updated=new Map);const o=(((a=e.updated.get(""))==null?void 0:a.count)??0)+1;if(e.updated.set("",{error:null,count:o}),o>5){const s=pu("updated at");if(s!==null){let i=e.updated.get(s.stack);i||(i={error:s,count:0},e.updated.set(s.stack,i)),i.count++}}}F!==null&&(e.set_during_effect=!0)}if((e.f&re)!==0){const o=e;(e.f&ae)!==0&&Qr(o),jr(o)}e.wv=ps(),Qo(e,ae),F!==null&&(F.f&ee)!==0&&(F.f&(Pe|wt))===0&&(Se===null?Ju([e]):Se.push(e)),!r.is_fork&&jt.size>0&&!Zr&&Yo()}return t}function Yo(){Zr=!1;for(const e of jt)(e.f&ee)!==0&&V(e,Ce),Sn(e)&&Yt(e);jt.clear()}function bn(e){ut(e,e.v+1)}function Qo(e,t){var n=e.reactions;if(n!==null)for(var r=n.length,a=0;a<r;a++){var o=n[a],s=o.f;if(y&&(s&er)!==0){jt.add(o);continue}var i=(s&ae)===0;if(i&&V(o,t),(s&re)!==0){var l=o;oe==null||oe.delete(l),(s&nt)===0&&(s&be&&(o.f|=nt),Qo(l,Ce))}else i&&((s&Ue)!==0&&Ne!==null&&Ne.add(o),Fe(o))}}const Ou=/^[a-zA-Z_$][a-zA-Z_$0-9]*$/;function Ut(e){if(typeof e!="object"||e===null||at in e)return e;const t=yo(e);if(t!==Pl&&t!==Cl)return e;var n=new Map,r=$r(e),a=lt(0),o=Pt,s=f=>{if(Pt===o)return f();var u=C,c=Pt;Me(null),hs(o);var _=f();return Me(u),hs(c),_};r&&(n.set("length",lt(e.length)),y&&(e=Iu(e)));var i="";let l=!1;function d(f){if(!l){l=!0,i=f,Le(a,`${i} version`);for(const[u,c]of n)Le(c,kt(i,u));l=!1}}return new Proxy(e,{defineProperty(f,u,c){(!("value"in c)||c.configurable===!1||c.enumerable===!1||c.writable===!1)&&Wl();var _=n.get(u);return _===void 0?s(()=>{var v=lt(c.value);return n.set(u,v),y&&typeof u=="string"&&Le(v,kt(i,u)),v}):ut(_,c.value,!0),!0},deleteProperty(f,u){var c=n.get(u);if(c===void 0){if(u in f){const _=s(()=>lt(te));n.set(u,_),bn(a),y&&Le(_,kt(i,u))}}else ut(c,te),bn(a);return!0},get(f,u,c){var p;if(u===at)return e;if(y&&u===So)return d;var _=n.get(u),v=u in f;if(_===void 0&&(!v||(p=We(f,u))!=null&&p.writable)&&(_=s(()=>{var m=Ut(v?f[u]:te),k=lt(m);return y&&Le(k,kt(i,u)),k}),n.set(u,_)),_!==void 0){var w=E(_);return w===te?void 0:w}return Reflect.get(f,u,c)},getOwnPropertyDescriptor(f,u){var c=Reflect.getOwnPropertyDescriptor(f,u);if(c&&"value"in c){var _=n.get(u);_&&(c.value=E(_))}else if(c===void 0){var v=n.get(u),w=v==null?void 0:v.v;if(v!==void 0&&w!==te)return{enumerable:!0,configurable:!0,value:w,writable:!0}}return c},has(f,u){var w;if(u===at)return!0;var c=n.get(u),_=c!==void 0&&c.v!==te||Reflect.has(f,u);if(c!==void 0||F!==null&&(!_||(w=We(f,u))!=null&&w.writable)){c===void 0&&(c=s(()=>{var p=_?Ut(f[u]):te,m=lt(p);return y&&Le(m,kt(i,u)),m}),n.set(u,c));var v=E(c);if(v===te)return!1}return _},set(f,u,c,_){var B;var v=n.get(u),w=u in f;if(r&&u==="length")for(var p=c;p<v.v;p+=1){var m=n.get(p+"");m!==void 0?ut(m,te):p in f&&(m=s(()=>lt(te)),n.set(p+"",m),y&&Le(m,kt(i,p)))}if(v===void 0)(!w||(B=We(f,u))!=null&&B.writable)&&(v=s(()=>lt(void 0)),y&&Le(v,kt(i,u)),ut(v,Ut(c)),n.set(u,v));else{w=v.v!==te;var k=s(()=>Ut(c));ut(v,k)}var b=Reflect.getOwnPropertyDescriptor(f,u);if(b!=null&&b.set&&b.set.call(_,c),!w){if(r&&typeof u=="string"){var S=n.get("length"),A=Number(u);Number.isInteger(A)&&A>=S.v&&ut(S,A+1)}bn(a)}return!0},ownKeys(f){E(a);var u=Reflect.ownKeys(f).filter(v=>{var w=n.get(v);return w===void 0||w.v!==te});for(var[c,_]of n)_.v!==te&&!(c in f)&&u.push(c);return u},setPrototypeOf(){Ul()}})}function kt(e,t){return typeof t=="symbol"?`${e}[Symbol(${t.description??""})]`:Ou.test(t)?`${e}.${t}`:/^\d+$/.test(t)?`${e}[${t}]`:`${e}['${t}']`}function wn(e){try{if(e!==null&&typeof e=="object"&&at in e)return e[at]}catch{}return e}function Lu(e,t){return Object.is(wn(e),wn(t))}const $u=new Set(["copyWithin","fill","pop","push","reverse","shift","sort","splice","unshift"]);function Iu(e){return new Proxy(e,{get(t,n,r){var a=Reflect.get(t,n,r);return $u.has(n)?function(...o){Ru();var s=a.apply(this,o);return Yo(),s}:a}})}function Bu(){const e=Array.prototype,t=Array.__svelte_cleanup;t&&t();const{indexOf:n,lastIndexOf:r,includes:a}=e;e.indexOf=function(o,s){const i=n.call(this,o,s);if(i===-1){for(let l=s??0;l<this.length;l+=1)if(wn(this[l])===o){Hr("array.indexOf(...)");break}}return i},e.lastIndexOf=function(o,s){const i=r.call(this,o,s??this.length-1);if(i===-1){for(let l=0;l<=(s??this.length-1);l+=1)if(wn(this[l])===o){Hr("array.lastIndexOf(...)");break}}return i},e.includes=function(o,s){const i=a.call(this,o,s);if(!i){for(let l=0;l<this.length;l+=1)if(wn(this[l])===o){Hr("array.includes(...)");break}}return i},Array.__svelte_cleanup=()=>{e.indexOf=n,e.lastIndexOf=r,e.includes=a}}var Zo,Jr,Jo,zo;function Gu(){if(Zo===void 0){Zo=window,Jr=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;Jo=We(t,"firstChild").get,zo=We(t,"nextSibling").get,bo(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),bo(n)&&(n.__t=void 0),y&&(e.__svelte_meta=null,Bu())}}function Qe(e=""){return document.createTextNode(e)}function Kt(e){return Jo.call(e)}function Mn(e){return zo.call(e)}function ie(e,t){return Kt(e)}function j(e,t=!1){{var n=Kt(e);return n instanceof Comment&&n.data===""?Mn(n):n}}function W(e,t=1,n=!1){let r=e;for(;t--;)r=Mn(r);return r}function Hu(e){e.textContent=""}function es(){return!1}function ts(e,t,n){return document.createElementNS(t??Co,e,void 0)}function Vu(e,t){if(t){const n=document.body;e.autofocus=!0,Ye(()=>{document.activeElement===n&&e.focus()})}}function zr(e){var t=C,n=F;Me(null),Te(null);try{return e()}finally{Me(t),Te(n)}}function ju(e){F===null&&(C===null&&Il(e),$l()),ct&&Ll(e)}function Wu(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function $e(e,t,n){var r=F;if(y)for(;r!==null&&(r.f&er)!==0;)r=r.parent;r!==null&&(r.f&he)!==0&&(e|=he);var a={ctx:G,deps:null,nodes:null,f:e|ae|be,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null};if(y&&(a.component_function=yn),n)try{Yt(a)}catch(i){throw se(a),i}else t!==null&&Fe(a);var o=a;if(n&&o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&Bt)===0&&(o=o.first,(e&Ue)!==0&&(e&tt)!==0&&o!==null&&(o.f|=tt)),o!==null&&(o.parent=r,r!==null&&Wu(o,r),C!==null&&(C.f&re)!==0&&(e&wt)===0)){var s=C;(s.effects??(s.effects=[])).push(o)}return a}function ea(){return C!==null&&!xe}function ta(e){const t=$e(zn,null,!1);return V(t,ee),t.teardown=e,t}function Uu(e){ju("$effect"),y&&bt(e,"name",{value:"$effect"});var t=F.f,n=!C&&(t&Pe)!==0&&(t&Mt)===0;if(n){var r=G;(r.e??(r.e=[])).push(e)}else return ns(e)}function ns(e){return $e(mn|xl,e,!1)}function Ku(e){st.ensure();const t=$e(wt|Bt,e,!0);return(n={})=>new Promise(r=>{n.outro?At(t,()=>{se(t),r(void 0)}):(se(t),r(void 0))})}function rs(e){return $e(mn,e,!1)}function Xu(e){return $e(tr|Bt,e,!0)}function Yu(e,t=0){return $e(zn|t,e,!0)}function Xt(e,t=[],n=[],r=[]){Vo(r,t,n,a=>{$e(zn,()=>e(...a.map(E)),!0)})}function qn(e,t=0){var n=$e(Ue|t,e,!0);return y&&(n.dev_stack=Ht),n}function as(e,t=0){var n=$e(Ir|t,e,!0);return y&&(n.dev_stack=Ht),n}function ue(e){return $e(Pe|Bt,e,!0)}function os(e){var t=e.teardown;if(t!==null){const n=ct,r=C;cs(!0),Me(null);try{t.call(null)}finally{cs(n),Me(r)}}}function na(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const a=n.ac;a!==null&&zr(()=>{a.abort(qt)});var r=n.next;(n.f&wt)!==0?n.parent=null:se(n,t),n=r}}function Qu(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&Pe)===0&&se(t),t=n}}function se(e,t=!0){var n=!1;(t||(e.f&Mo)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(Zu(e.nodes.start,e.nodes.end),n=!0),na(e,t&&!n),kn(e,0),V(e,Ke);var r=e.nodes&&e.nodes.t;if(r!==null)for(const o of r)o.stop();os(e);var a=e.parent;a!==null&&a.first!==null&&ss(e),y&&(e.component_function=null),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function Zu(e,t){for(;e!==null;){var n=e===t?null:Mn(e);e.remove(),e=n}}function ss(e){var t=e.parent,n=e.prev,r=e.next;n!==null&&(n.next=r),r!==null&&(r.prev=n),t!==null&&(t.first===e&&(t.first=r),t.last===e&&(t.last=n))}function At(e,t,n=!0){var r=[];is(e,r,!0);var a=()=>{n&&se(e),t&&t()},o=r.length;if(o>0){var s=()=>--o||a();for(var i of r)i.out(s)}else a()}function is(e,t,n){if((e.f&he)===0){e.f^=he;var r=e.nodes&&e.nodes.t;if(r!==null)for(const i of r)(i.is_global||n)&&t.push(i);for(var a=e.first;a!==null;){var o=a.next,s=(a.f&tt)!==0||(a.f&Pe)!==0&&(e.f&Ue)!==0;is(a,t,s?n:!1),a=o}}}function ra(e){ls(e,!0)}function ls(e,t){if((e.f&he)!==0){e.f^=he,(e.f&ee)===0&&(V(e,ae),Fe(e));for(var n=e.first;n!==null;){var r=n.next,a=(n.f&tt)!==0||(n.f&Pe)!==0;ls(n,a?t:!1),n=r}var o=e.nodes&&e.nodes.t;if(o!==null)for(const s of o)(s.is_global||t)&&s.in()}}function us(e,t){if(e.nodes)for(var n=e.nodes.start,r=e.nodes.end;n!==null;){var a=n===r?null:Mn(n);t.append(n),n=a}}let or=!1,ct=!1;function cs(e){ct=e}let C=null,xe=!1;function Me(e){C=e}let F=null;function Te(e){F=e}let qe=null;function fs(e){C!==null&&(qe===null?qe=[e]:qe.push(e))}let ce=null,pe=0,Se=null;function Ju(e){Se=e}let ds=1,Et=0,Pt=Et;function hs(e){Pt=e}function ps(){return++ds}function Sn(e){var t=e.f;if((t&ae)!==0)return!0;if(t&re&&(e.f&=~nt),(t&Ce)!==0){for(var n=e.deps,r=n.length,a=0;a<r;a++){var o=n[a];if(Sn(o)&&Uo(o),o.wv>e.wv)return!0}(t&be)!==0&&oe===null&&V(e,ee)}return!1}function _s(e,t,n=!0){var r=e.reactions;if(r!==null&&!(qe!==null&&yt.call(qe,e)))for(var a=0;a<r.length;a++){var o=r[a];(o.f&re)!==0?_s(o,t,!1):t===o&&(n?V(o,ae):(o.f&ee)!==0&&V(o,Ce),Fe(o))}}function aa(e){var w;var t=ce,n=pe,r=Se,a=C,o=qe,s=G,i=xe,l=Pt,d=e.f;ce=null,pe=0,Se=null,C=(d&(Pe|wt))===0?e:null,qe=null,Gt(e.ctx),xe=!1,Pt=++Et,e.ac!==null&&(zr(()=>{e.ac.abort(qt)}),e.ac=null);try{e.f|=Gr;var f=e.fn,u=f();e.f|=Mt;var c=e.deps,_=T==null?void 0:T.is_fork;if(ce!==null){var v;if(_||kn(e,pe),c!==null&&pe>0)for(c.length=pe+ce.length,v=0;v<ce.length;v++)c[pe+v]=ce[v];else e.deps=c=ce;if(ea()&&(e.f&be)!==0)for(v=pe;v<c.length;v++)((w=c[v]).reactions??(w.reactions=[])).push(e)}else!_&&c!==null&&pe<c.length&&(kn(e,pe),c.length=pe);if(Ro()&&Se!==null&&!xe&&c!==null&&(e.f&(re|Ce|ae))===0)for(v=0;v<Se.length;v++)_s(Se[v],e);if(a!==null&&a!==e){if(Et++,a.deps!==null)for(let p=0;p<n;p+=1)a.deps[p].rv=Et;if(t!==null)for(const p of t)p.rv=Et;Se!==null&&(r===null?r=Se:r.push(...Se))}return(e.f&rt)!==0&&(e.f^=rt),u}catch(p){return Do(p)}finally{e.f^=Gr,ce=t,pe=n,Se=r,C=a,qe=o,Gt(s),xe=i,Pt=l}}function zu(e,t){let n=t.reactions;if(n!==null){var r=Al.call(n,e);if(r!==-1){var a=n.length-1;a===0?n=t.reactions=null:(n[r]=n[a],n.pop())}}if(n===null&&(t.f&re)!==0&&(ce===null||!yt.call(ce,t))){var o=t;(o.f&be)!==0&&(o.f^=be,o.f&=~nt),jr(o),Tu(o),kn(o,0)}}function kn(e,t){var n=e.deps;if(n!==null)for(var r=t;r<n.length;r++)zu(e,n[r])}function Yt(e){var t=e.f;if((t&Ke)===0){V(e,ee);var n=F,r=or;if(F=e,or=!0,y){var a=yn;To(e.component_function);var o=Ht;nr(e.dev_stack??Ht)}try{(t&(Ue|Ir))!==0?Qu(e):na(e),os(e);var s=aa(e);e.teardown=typeof s=="function"?s:null,e.wv=ds;var i;y&&hu&&(e.f&ae)!==0&&e.deps}finally{or=r,F=n,y&&(To(a),nr(o))}}}function E(e){var t=e.f,n=(t&re)!==0;if(C!==null&&!xe){var r=F!==null&&(F.f&Ke)!==0;if(!r&&(qe===null||!yt.call(qe,e))){var a=C.deps;if((C.f&Gr)!==0)e.rv<Et&&(e.rv=Et,ce===null&&a!==null&&a[pe]===e?pe++:ce===null?ce=[e]:ce.push(e));else{(C.deps??(C.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[C]:yt.call(o,C)||o.push(C)}}}if(y&&Nu.delete(e),ct&&it.has(e))return it.get(e);if(n){var s=e;if(ct){var i=s.v;return((s.f&ee)===0&&s.reactions!==null||vs(s))&&(i=Qr(s)),it.set(s,i),i}var l=(s.f&be)===0&&!xe&&C!==null&&(or||(C.f&be)!==0),d=(s.f&Mt)===0;Sn(s)&&(l&&(s.f|=be),Uo(s)),l&&!d&&(Ko(s),ms(s))}if(oe!=null&&oe.has(e))return oe.get(e);if((e.f&rt)!==0)throw e.v;return e.v}function ms(e){if(e.f|=be,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&re)!==0&&(t.f&be)===0&&(Ko(t),ms(t))}function vs(e){if(e.v===te)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(it.has(t)||(t.f&re)!==0&&vs(t))return!0;return!1}function oa(e){var t=xe;try{return xe=!0,e()}finally{xe=t}}function ec(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const tc=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function nc(e){return tc.includes(e)}const rc={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function ac(e){return e=e.toLowerCase(),rc[e]??e}const oc=["touchstart","touchmove"];function sc(e){return oc.includes(e)}const Ct=Symbol("events"),gs=new Set,sa=new Set;function ic(e,t,n,r={}){function a(o){if(r.capture||ia.call(t,o),!o.cancelBubble)return zr(()=>n==null?void 0:n.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Ye(()=>{t.addEventListener(e,a,r)}):t.addEventListener(e,a,r),a}function ft(e,t,n){(t[Ct]??(t[Ct]={}))[e]=n}function ys(e){for(var t=0;t<e.length;t++)gs.add(e[t]);for(var n of sa)n(e)}let bs=null;function ia(e){var p,m;var t=this,n=t.ownerDocument,r=e.type,a=((p=e.composedPath)==null?void 0:p.call(e))||[],o=a[0]||e.target;bs=e;var s=0,i=bs===e&&e[Ct];if(i){var l=a.indexOf(i);if(l!==-1&&(t===document||t===window)){e[Ct]=t;return}var d=a.indexOf(t);if(d===-1)return;l<=d&&(s=l)}if(o=a[s]||e.target,o!==t){bt(e,"currentTarget",{configurable:!0,get(){return o||n}});var f=C,u=F;Me(null),Te(null);try{for(var c,_=[];o!==null;){var v=o.assignedSlot||o.parentNode||o.host||null;try{var w=(m=o[Ct])==null?void 0:m[r];w!=null&&(!o.disabled||e.target===o)&&w.call(o,e)}catch(k){c?_.push(k):c=k}if(e.cancelBubble||v===t||v===null)break;o=v}if(c){for(let k of _)queueMicrotask(()=>{throw k});throw c}}finally{e[Ct]=t,delete e.currentTarget,Me(f),Te(u)}}}const la=((js=globalThis==null?void 0:globalThis.window)==null?void 0:js.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function lc(e){return(la==null?void 0:la.createHTML(e))??e}function ws(e){var t=ts("template");return t.innerHTML=lc(e.replaceAll("<!>","<!---->")),t.content}function An(e,t){var n=F;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function Qt(e,t){var n=(t&ru)!==0,r=(t&au)!==0,a,o=!e.startsWith("<!>");return()=>{a===void 0&&(a=ws(o?e:"<!>"+e),n||(a=Kt(a)));var s=r||Jr?document.importNode(a,!0):a.cloneNode(!0);if(n){var i=Kt(s),l=s.lastChild;An(i,l)}else An(s,s);return s}}function uc(e,t,n="svg"){var r=!e.startsWith("<!>"),a=`<${n}>${r?e:"<!>"+e}</${n}>`,o;return()=>{if(!o){var s=ws(a),i=Kt(s);o=Kt(i)}var l=o.cloneNode(!0);return An(l,l),l}}function cc(e,t){return uc(e,t,"svg")}function U(){var e=document.createDocumentFragment(),t=document.createComment(""),n=Qe();return e.append(t,n),An(t,n),e}function R(e,t){e!==null&&e.before(t)}function Ms(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function fc(e,t){return dc(e,t)}const sr=new Map;function dc(e,{target:t,anchor:n,props:r={},events:a,context:o,intro:s=!0,transformError:i}){Gu();var l=void 0,d=Ku(()=>{var f=n??t.appendChild(Qe());Au(f,{pending:()=>{}},_=>{$({});var v=G;o&&(v.c=o),a&&(r.$$events=a),l=e(_,r)||{},I()},i);var u=new Set,c=_=>{for(var v=0;v<_.length;v++){var w=_[v];if(!u.has(w)){u.add(w);var p=sc(w);for(const b of[t,document]){var m=sr.get(b);m===void 0&&(m=new Map,sr.set(b,m));var k=m.get(w);k===void 0?(b.addEventListener(w,ia,{passive:p}),m.set(w,1)):m.set(w,k+1)}}}};return c(Jn(gs)),sa.add(c),()=>{var p;for(var _ of u)for(const m of[t,document]){var v=sr.get(m),w=v.get(_);--w==0?(m.removeEventListener(_,ia),v.delete(_),v.size===0&&sr.delete(m)):v.set(_,w)}sa.delete(c),f!==n&&((p=f.parentNode)==null||p.removeChild(f))}});return ua.set(l,d),l}let ua=new WeakMap;function qs(e,t){const n=ua.get(e);return n?(ua.delete(e),n(t)):(y&&(at in e?cu():lu()),Promise.resolve())}class ca{constructor(t,n=!0){Ve(this,"anchor");N(this,De,new Map);N(this,He,new Map);N(this,ve,new Map);N(this,Dt,new Set);N(this,Rn,!0);N(this,Dn,()=>{var t=T;if(h(this,De).has(t)){var n=h(this,De).get(t),r=h(this,He).get(n);if(r)ra(r),h(this,Dt).delete(n);else{var a=h(this,ve).get(n);a&&(h(this,He).set(n,a.effect),h(this,ve).delete(n),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),r=a.effect)}for(const[o,s]of h(this,De)){if(h(this,De).delete(o),o===t)break;const i=h(this,ve).get(s);i&&(se(i.effect),h(this,ve).delete(s))}for(const[o,s]of h(this,He)){if(o===n||h(this,Dt).has(o))continue;const i=()=>{if(Array.from(h(this,De).values()).includes(o)){var d=document.createDocumentFragment();us(s,d),d.append(Qe()),h(this,ve).set(o,{effect:s,fragment:d})}else se(s);h(this,Dt).delete(o),h(this,He).delete(o)};h(this,Rn)||!r?(h(this,Dt).add(o),At(s,i,!1)):i()}}});N(this,cr,t=>{h(this,De).delete(t);const n=Array.from(h(this,De).values());for(const[r,a]of h(this,ve))n.includes(r)||(se(a.effect),h(this,ve).delete(r))});this.anchor=t,P(this,Rn,n)}ensure(t,n){var r=T,a=es();if(n&&!h(this,He).has(t)&&!h(this,ve).has(t))if(a){var o=document.createDocumentFragment(),s=Qe();o.append(s),h(this,ve).set(t,{effect:ue(()=>n(s)),fragment:o})}else h(this,He).set(t,ue(()=>n(this.anchor)));if(h(this,De).set(r,t),a){for(const[i,l]of h(this,He))i===t?r.unskip_effect(l):r.skip_effect(l);for(const[i,l]of h(this,ve))i===t?r.unskip_effect(l.effect):r.skip_effect(l.effect);r.oncommit(h(this,Dn)),r.ondiscard(h(this,cr))}else h(this,Dn).call(this)}}De=new WeakMap,He=new WeakMap,ve=new WeakMap,Dt=new WeakMap,Rn=new WeakMap,Dn=new WeakMap,cr=new WeakMap;function ir(e,t,n=!1){var r=new ca(e),a=n?tt:0;function o(s,i){r.ensure(s,i)}qn(()=>{var s=!1;t((i,l=0)=>{s=!0,o(l,i)}),s||o(!1,null)},a)}function hc(e,t){return t}function pc(e,t,n){for(var r=[],a=t.length,o,s=t.length,i=0;i<a;i++){let u=t[i];At(u,()=>{if(o){if(o.pending.delete(u),o.done.add(u),o.pending.size===0){var c=e.outrogroups;fa(Jn(o.done)),c.delete(o),c.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var l=r.length===0&&n!==null;if(l){var d=n,f=d.parentNode;Hu(f),f.append(d),e.items.clear()}fa(t,!l)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function fa(e,t=!0){for(var n=0;n<e.length;n++)se(e[n],t)}var Ss;function da(e,t,n,r,a,o=null){var s=e,i=new Map,l=(t&Po)!==0;if(l){var d=e;s=d.appendChild(Qe())}var f=null,u=jo(()=>{var m=n();return $r(m)?m:m==null?[]:Jn(m)}),c,_=!0;function v(){p.fallback=f,_c(p,c,s,t,r),f!==null&&(c.length===0?(f.f&Xe)===0?ra(f):(f.f^=Xe,Pn(f,null,s)):At(f,()=>{f=null}))}var w=qn(()=>{c=E(u);for(var m=c.length,k=new Set,b=T,S=es(),A=0;A<m;A+=1){var B=c[A],x=r(B,A);if(y){var ge=r(B,A);x!==ge&&Ol(String(A),String(x),String(ge))}var g=_?null:i.get(x);g?(g.v&&Wt(g.v,B),g.i&&Wt(g.i,A),S&&b.unskip_effect(g.e)):(g=mc(i,_?s:Ss??(Ss=Qe()),B,x,A,a,t,n),_||(g.e.f|=Xe),i.set(x,g)),k.add(x)}if(m===0&&o&&!f&&(_?f=ue(()=>o(s)):(f=ue(()=>o(Ss??(Ss=Qe()))),f.f|=Xe)),m>k.size&&(y?vc(c,r):Eo("","","")),!_)if(S){for(const[Y,ze]of i)k.has(Y)||b.skip_effect(ze.e);b.oncommit(v),b.ondiscard(()=>{})}else v();E(u)}),p={effect:w,items:i,outrogroups:null,fallback:f};_=!1}function En(e){for(;e!==null&&(e.f&Pe)===0;)e=e.next;return e}function _c(e,t,n,r,a){var Y,ze,ye,On,Ln,$n,fr,dr,hr;var o=(r&Zl)!==0,s=t.length,i=e.items,l=En(e.effect.first),d,f=null,u,c=[],_=[],v,w,p,m;if(o)for(m=0;m<s;m+=1)v=t[m],w=a(v,m),p=i.get(w).e,(p.f&Xe)===0&&((ze=(Y=p.nodes)==null?void 0:Y.a)==null||ze.measure(),(u??(u=new Set)).add(p));for(m=0;m<s;m+=1){if(v=t[m],w=a(v,m),p=i.get(w).e,e.outrogroups!==null)for(const Ae of e.outrogroups)Ae.pending.delete(p),Ae.done.delete(p);if((p.f&Xe)!==0)if(p.f^=Xe,p===l)Pn(p,null,n);else{var k=f?f.next:l;p===e.effect.last&&(e.effect.last=p.prev),p.prev&&(p.prev.next=p.next),p.next&&(p.next.prev=p.prev),dt(e,f,p),dt(e,p,k),Pn(p,k,n),f=p,c=[],_=[],l=En(f.next);continue}if((p.f&he)!==0&&(ra(p),o&&((On=(ye=p.nodes)==null?void 0:ye.a)==null||On.unfix(),(u??(u=new Set)).delete(p))),p!==l){if(d!==void 0&&d.has(p)){if(c.length<_.length){var b=_[0],S;f=b.prev;var A=c[0],B=c[c.length-1];for(S=0;S<c.length;S+=1)Pn(c[S],b,n);for(S=0;S<_.length;S+=1)d.delete(_[S]);dt(e,A.prev,B.next),dt(e,f,A),dt(e,B,b),l=b,f=B,m-=1,c=[],_=[]}else d.delete(p),Pn(p,l,n),dt(e,p.prev,p.next),dt(e,p,f===null?e.effect.first:f.next),dt(e,f,p),f=p;continue}for(c=[],_=[];l!==null&&l!==p;)(d??(d=new Set)).add(l),_.push(l),l=En(l.next);if(l===null)continue}(p.f&Xe)===0&&c.push(p),f=p,l=En(p.next)}if(e.outrogroups!==null){for(const Ae of e.outrogroups)Ae.pending.size===0&&(fa(Jn(Ae.done)),(Ln=e.outrogroups)==null||Ln.delete(Ae));e.outrogroups.size===0&&(e.outrogroups=null)}if(l!==null||d!==void 0){var x=[];if(d!==void 0)for(p of d)(p.f&he)===0&&x.push(p);for(;l!==null;)(l.f&he)===0&&l!==e.fallback&&x.push(l),l=En(l.next);var ge=x.length;if(ge>0){var g=(r&Po)!==0&&s===0?n:null;if(o){for(m=0;m<ge;m+=1)(fr=($n=x[m].nodes)==null?void 0:$n.a)==null||fr.measure();for(m=0;m<ge;m+=1)(hr=(dr=x[m].nodes)==null?void 0:dr.a)==null||hr.fix()}pc(e,x,g)}}o&&Ye(()=>{var Ae,pr;if(u!==void 0)for(p of u)(pr=(Ae=p.nodes)==null?void 0:Ae.a)==null||pr.apply()})}function mc(e,t,n,r,a,o,s,i){var l=(s&Yl)!==0?(s&Jl)===0?Du(n,!1,!1):St(n):null,d=(s&Ql)!==0?St(a):null;return y&&l&&(l.trace=()=>{i()[(d==null?void 0:d.v)??a]}),{v:l,i:d,e:ue(()=>(o(t,l??n,d??a,i),()=>{e.delete(r)}))}}function Pn(e,t,n){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end,o=t&&(t.f&Xe)===0?t.nodes.start:n;r!==null;){var s=Mn(r);if(o.before(r),r===a)return;r=s}}function dt(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function vc(e,t){const n=new Map,r=e.length;for(let a=0;a<r;a++){const o=t(e[a],a);if(n.has(o)){const s=String(n.get(o)),i=String(a);let l=String(o);l.startsWith("[object ")&&(l=null),Eo(s,i,l)}n.set(o,a)}}function K(e,t,...n){var r=new ca(e);qn(()=>{const a=t()??null;y&&a==null&&Gl(),r.ensure(a,a&&(o=>a(o,...n)))},tt)}function gc(e,t,n,r,a,o){var s=null,i=e,l=new ca(i,!1);qn(()=>{const d=t()||null;var f=su;if(d===null){l.ensure(null,null);return}return l.ensure(d,u=>{if(d){if(s=ts(d,f),An(s,s),r){var c=s.appendChild(Qe());r(s,c)}F.nodes.end=s,u.before(s)}}),()=>{}},tt),ta(()=>{})}function yc(e,t){var n=void 0,r;as(()=>{n!==(n=t())&&(r&&(se(r),r=null),n&&(r=ue(()=>{rs(()=>n(e))})))})}function ks(e){var t,n,r="";if(typeof e=="string"||typeof e=="number")r+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(n=ks(e[t]))&&(r&&(r+=" "),r+=n)}else for(n in e)e[n]&&(r&&(r+=" "),r+=n);return r}function bc(){for(var e,t,n=0,r="",a=arguments.length;n<a;n++)(e=arguments[n])&&(t=ks(e))&&(r&&(r+=" "),r+=t);return r}function As(e){return typeof e=="object"?bc(e):e??""}const Es=[...` 	
\r\f \v\uFEFF`];function wc(e,t,n){var r=e==null?"":""+e;if(t&&(r=r?r+" "+t:t),n){for(var a of Object.keys(n))if(n[a])r=r?r+" "+a:a;else if(r.length)for(var o=a.length,s=0;(s=r.indexOf(a,s))>=0;){var i=s+o;(s===0||Es.includes(r[s-1]))&&(i===r.length||Es.includes(r[i]))?r=(s===0?"":r.substring(0,s))+r.substring(i+1):s=i}}return r===""?null:r}function Ps(e,t=!1){var n=t?" !important;":";",r="";for(var a of Object.keys(e)){var o=e[a];o!=null&&o!==""&&(r+=" "+a+": "+o+n)}return r}function ha(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function Mc(e,t){if(t){var n="",r,a;if(Array.isArray(t)?(r=t[0],a=t[1]):r=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,s=0,i=!1,l=[];r&&l.push(...Object.keys(r).map(ha)),a&&l.push(...Object.keys(a).map(ha));var d=0,f=-1;const w=e.length;for(var u=0;u<w;u++){var c=e[u];if(i?c==="/"&&e[u-1]==="*"&&(i=!1):o?o===c&&(o=!1):c==="/"&&e[u+1]==="*"?i=!0:c==='"'||c==="'"?o=c:c==="("?s++:c===")"&&s--,!i&&o===!1&&s===0){if(c===":"&&f===-1)f=u;else if(c===";"||u===w-1){if(f!==-1){var _=ha(e.substring(d,f).trim());if(!l.includes(_)){c!==";"&&u++;var v=e.substring(d,u).trim();n+=" "+v+";"}}d=u+1,f=-1}}}}return r&&(n+=Ps(r)),a&&(n+=Ps(a,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function pa(e,t,n,r,a,o){var s=e.__className;if(s!==n||s===void 0){var i=wc(n,r,o);i==null?e.removeAttribute("class"):t?e.className=i:e.setAttribute("class",i),e.__className=n}else if(o&&a!==o)for(var l in o){var d=!!o[l];(a==null||d!==!!a[l])&&e.classList.toggle(l,d)}return o}function _a(e,t={},n,r){for(var a in n){var o=n[a];t[a]!==o&&(n[a]==null?e.style.removeProperty(a):e.style.setProperty(a,o,r))}}function qc(e,t,n,r){var a=e.__style;if(a!==t){var o=Mc(t,r);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else r&&(Array.isArray(r)?(_a(e,n==null?void 0:n[0],r[0]),_a(e,n==null?void 0:n[1],r[1],"important")):_a(e,n,r));return r}function ma(e,t,n=!1){if(e.multiple){if(t==null)return;if(!$r(t))return uu();for(var r of e.options)r.selected=t.includes(Cs(r));return}for(r of e.options){var a=Cs(r);if(Lu(a,t)){r.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function Sc(e){var t=new MutationObserver(()=>{ma(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),ta(()=>{t.disconnect()})}function Cs(e){return"__value"in e?e.__value:e.value}const Cn=Symbol("class"),Nn=Symbol("style"),Ns=Symbol("is custom element"),Fs=Symbol("is html"),kc=ko?"option":"OPTION",Ac=ko?"select":"SELECT";function Ec(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function q(e,t,n,r){var a=Ts(e);a[t]!==(a[t]=n)&&(t==="loading"&&(e[Tl]=n),n==null?e.removeAttribute(t):typeof n!="string"&&Ds(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function Pc(e,t,n,r,a=!1,o=!1){var s=Ts(e),i=s[Ns],l=!s[Fs],d=t||{},f=e.nodeName===kc;for(var u in t)u in n||(n[u]=null);n.class?n.class=As(n.class):n[Cn]&&(n.class=null),n[Nn]&&(n.style??(n.style=null));var c=Ds(e);for(const b in n){let S=n[b];if(f&&b==="value"&&S==null){e.value=e.__value="",d[b]=S;continue}if(b==="class"){var _=e.namespaceURI==="http://www.w3.org/1999/xhtml";pa(e,_,S,r,t==null?void 0:t[Cn],n[Cn]),d[b]=S,d[Cn]=n[Cn];continue}if(b==="style"){qc(e,S,t==null?void 0:t[Nn],n[Nn]),d[b]=S,d[Nn]=n[Nn];continue}var v=d[b];if(!(S===v&&!(S===void 0&&e.hasAttribute(b)))){d[b]=S;var w=b[0]+b[1];if(w!=="$$")if(w==="on"){const A={},B="$$"+b;let x=b.slice(2);var p=nc(x);if(ec(x)&&(x=x.slice(0,-7),A.capture=!0),!p&&v){if(S!=null)continue;e.removeEventListener(x,d[B],A),d[B]=null}if(p)ft(x,e,S),ys([x]);else if(S!=null){let ge=function(g){d[b].call(this,g)};d[B]=ic(x,e,ge,A)}}else if(b==="style")q(e,b,S);else if(b==="autofocus")Vu(e,!!S);else if(!i&&(b==="__value"||b==="value"&&S!=null))e.value=e.__value=S;else if(b==="selected"&&f)Ec(e,S);else{var m=b;l||(m=ac(m));var k=m==="defaultValue"||m==="defaultChecked";if(S==null&&!i&&!k)if(s[b]=null,m==="value"||m==="checked"){let A=e;const B=t===void 0;if(m==="value"){let x=A.defaultValue;A.removeAttribute(m),A.defaultValue=x,A.value=A.__value=B?x:null}else{let x=A.defaultChecked;A.removeAttribute(m),A.defaultChecked=x,A.checked=B?x:!1}}else e.removeAttribute(b);else k||c.includes(m)&&(i||typeof S!="string")?(e[m]=S,m in s&&(s[m]=te)):typeof S!="function"&&q(e,m,S)}}}return d}function xs(e,t,n=[],r=[],a=[],o,s=!1,i=!1){Vo(a,n,r,l=>{var d=void 0,f={},u=e.nodeName===Ac,c=!1;if(as(()=>{var v=t(...l.map(E)),w=Pc(e,d,v,o,s,i);c&&u&&"value"in v&&ma(e,v.value);for(let m of Object.getOwnPropertySymbols(f))v[m]||se(f[m]);for(let m of Object.getOwnPropertySymbols(v)){var p=v[m];m.description===iu&&(!d||p!==d[m])&&(f[m]&&se(f[m]),f[m]=ue(()=>yc(e,()=>p))),w[m]=p}d=w}),u){var _=e;rs(()=>{ma(_,d.value,!0),Sc(_)})}c=!0})}function Ts(e){return e.__attributes??(e.__attributes={[Ns]:e.nodeName.includes("-"),[Fs]:e.namespaceURI===Co})}var Rs=new Map;function Ds(e){var t=e.getAttribute("is")||e.nodeName,n=Rs.get(t);if(n)return n;Rs.set(t,n=[]);for(var r,a=e,o=Element.prototype;o!==a;){r=El(a);for(var s in r)r[s].set&&n.push(s);a=yo(a)}return n}let lr=!1;function Cc(e){var t=lr;try{return lr=!1,[e(),lr]}finally{lr=t}}const Nc={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return y&&Vl(`${e.name}.${String(t)}`),!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function X(e,t,n){return new Proxy(y?{props:e,exclude:t,name:n,other:{},to_proxy:[]}:{props:e,exclude:t},Nc)}const Fc={get(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(_n(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r)return r[t]}},set(e,t,n){let r=e.props.length;for(;r--;){let a=e.props[r];_n(a)&&(a=a());const o=We(a,t);if(o&&o.set)return o.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(_n(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r){const a=We(r,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===at||t===qo)return!1;for(let n of e.props)if(_n(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(_n(n)&&(n=n()),!!n){for(const r in n)t.includes(r)||t.push(r);for(const r of Object.getOwnPropertySymbols(n))t.includes(r)||t.push(r)}return t}};function Z(...e){return new Proxy({props:e},Fc)}function Zt(e,t,n,r){var k;var a=(n&tu)!==0,o=(n&nu)!==0,s=r,i=!0,l=()=>(i&&(i=!1,s=o?oa(r):r),s),d;if(a){var f=at in e||qo in e;d=((k=We(e,t))==null?void 0:k.set)??(f&&t in e?b=>e[t]=b:void 0)}var u,c=!1;a?[u,c]=Cc(()=>e[t]):u=e[t],u===void 0&&r!==void 0&&(u=l(),d&&(Hl(t),d(u)));var _;if(_=()=>{var b=e[t];return b===void 0?l():(i=!0,b)},(n&eu)===0)return _;if(d){var v=e.$$legacy;return(function(b,S){return arguments.length>0?((!S||v||c)&&d(S?_():b),b):_()})}var w=!1,p=((n&zl)!==0?ar:jo)(()=>(w=!1,_()));y&&(p.label=t),a&&E(p);var m=F;return(function(b,S){if(arguments.length>0){const A=S?E(p):a?Ut(b):b;return ut(p,A),w=!0,s!==void 0&&(s=A),b}return ct&&w||(m.f&Ke)!==0?p.v:E(p)})}if(y){let e=function(t){if(!(t in globalThis)){let n;Object.defineProperty(globalThis,t,{configurable:!0,get:()=>{if(n!==void 0)return n;jl(t)},set:r=>{n=r}})}};e("$state"),e("$effect"),e("$derived"),e("$inspect"),e("$props"),e("$bindable")}function xc(e){G===null&&Ao("onMount"),Uu(()=>{const t=oa(e);if(typeof t=="function")return t})}const Tc="5";typeof window<"u"&&((Ws=window.__svelte??(window.__svelte={})).v??(Ws.v=new Set)).add(Tc);/**
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
 */const Rc={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const Dc=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const Oc=Symbol("lucide-context"),Lc=()=>mu(Oc);var $c=cc("<svg><!><!></svg>");function J(e,t){$(t,!0);const n=Lc()??{},r=Zt(t,"color",19,()=>n.color??"currentColor"),a=Zt(t,"size",19,()=>n.size??24),o=Zt(t,"strokeWidth",19,()=>n.strokeWidth??2),s=Zt(t,"absoluteStrokeWidth",19,()=>n.absoluteStrokeWidth??!1),i=Zt(t,"iconNode",19,()=>[]),l=X(t,["$$slots","$$events","$$legacy","name","color","size","strokeWidth","absoluteStrokeWidth","iconNode","children"]),d=Xr(()=>s()?Number(o())*24/Number(a()):o());var f=$c();xs(f,_=>({...Rc,..._,...l,width:a(),height:a(),stroke:r(),"stroke-width":E(d),class:["lucide-icon lucide",n.class,t.name&&`lucide-${t.name}`,t.class]}),[()=>!t.children&&!Dc(l)&&{"aria-hidden":"true"}]);var u=ie(f);da(u,17,i,hc,(_,v)=>{var w=Xr(()=>Fl(E(v),2));let p=()=>E(w)[0],m=()=>E(w)[1];var k=U(),b=j(k);gc(b,p,!0,(S,A)=>{xs(S,()=>({...m()}))}),R(_,k)});var c=W(u);K(c,()=>t.children??H),R(e,f),I()}function Ic(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];J(e,Z({name:"chart-line"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Bc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 9 6 6 6-6"}]];J(e,Z({name:"chevron-down"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Gc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"12",cy:"12",r:"10"}],["path",{d:"M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"}],["path",{d:"M12 17h.01"}]];J(e,Z({name:"circle-question-mark"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Hc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 12 18z"}],["path",{d:"M2 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 2 18z"}]];J(e,Z({name:"fast-forward"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Vc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"}]];J(e,Z({name:"folder-open"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function jc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["rect",{x:"14",y:"3",width:"5",height:"18",rx:"1"}],["rect",{x:"5",y:"3",width:"5",height:"18",rx:"1"}]];J(e,Z({name:"pause"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Wc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"}]];J(e,Z({name:"play"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Uc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m15 14 5-5-5-5"}],["path",{d:"M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13"}]];J(e,Z({name:"redo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Kc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];J(e,Z({name:"refresh-cw"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Xc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m2 9 3-3 3 3"}],["path",{d:"M13 18H7a2 2 0 0 1-2-2V6"}],["path",{d:"m22 15-3 3-3-3"}],["path",{d:"M11 6h6a2 2 0 0 1 2 2v10"}]];J(e,Z({name:"repeat-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Yc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 12 18z"}],["path",{d:"M22 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 22 18z"}]];J(e,Z({name:"rewind"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Qc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M8.12 8.12 12 12"}],["path",{d:"M20 4 8.12 15.88"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M14.8 14.8 20 20"}]];J(e,Z({name:"scissors"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Zc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"}],["circle",{cx:"12",cy:"12",r:"3"}]];J(e,Z({name:"settings"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function Jc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];J(e,Z({name:"sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function zc(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 2h4"}],["path",{d:"M12 14v-4"}],["path",{d:"M4 13a8 8 0 0 1 8-7 8 8 0 1 1-5.3 14L4 17.6"}],["path",{d:"M9 17H4v5"}]];J(e,Z({name:"timer-reset"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function ef(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9 14 4 9l5-5"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"}]];J(e,Z({name:"undo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function tf(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}]];J(e,Z({name:"volume-1"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function nf(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}],["path",{d:"M19.364 18.364a9 9 0 0 0 0-12.728"}]];J(e,Z({name:"volume-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}function rf(e,t){$(t,!0);/**
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
 */let n=X(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["line",{x1:"22",x2:"16",y1:"9",y2:"15"}],["line",{x1:"16",x2:"22",y1:"9",y2:"15"}]];J(e,Z({name:"volume-x"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=U(),i=j(s);K(i,()=>t.children??H),R(a,s)},$$slots:{default:!0}})),I()}var af=Qt('<span aria-hidden="true"><!></span>');function Nt(e,t){$(t,!0);const n=Zt(t,"className",3,""),r=Xr(()=>["aqe-button-icon",n()].filter(Boolean).join(" "));var a=af(),o=ie(a);{var s=g=>{Ic(g,{size:14,strokeWidth:2})},i=g=>{Bc(g,{size:14,strokeWidth:2})},l=g=>{Gc(g,{size:14,strokeWidth:2})},d=g=>{Hc(g,{size:14,strokeWidth:2})},f=g=>{Vc(g,{size:14,strokeWidth:2})},u=g=>{jc(g,{size:14,strokeWidth:2})},c=g=>{Wc(g,{size:14,strokeWidth:2})},_=g=>{Uc(g,{size:14,strokeWidth:2})},v=g=>{Kc(g,{size:14,strokeWidth:2})},w=g=>{Xc(g,{size:14,strokeWidth:2})},p=g=>{Yc(g,{size:14,strokeWidth:2})},m=g=>{Qc(g,{size:14,strokeWidth:2})},k=g=>{Zc(g,{size:14,strokeWidth:2})},b=g=>{Jc(g,{size:14,strokeWidth:2})},S=g=>{zc(g,{size:14,strokeWidth:2})},A=g=>{ef(g,{size:14,strokeWidth:2})},B=g=>{tf(g,{size:14,strokeWidth:2})},x=g=>{nf(g,{size:14,strokeWidth:2})},ge=g=>{rf(g,{size:14,strokeWidth:2})};ir(o,g=>{t.icon==="chart-line"?g(s):t.icon==="chevron-down"?g(i,1):t.icon==="circle-help"?g(l,2):t.icon==="fast-forward"?g(d,3):t.icon==="folder-open"?g(f,4):t.icon==="pause"?g(u,5):t.icon==="play"?g(c,6):t.icon==="redo-2"?g(_,7):t.icon==="refresh-cw"?g(v,8):t.icon==="repeat-2"?g(w,9):t.icon==="rewind"?g(p,10):t.icon==="scissors"?g(m,11):t.icon==="settings"?g(k,12):t.icon==="sparkles"?g(b,13):t.icon==="timer-reset"?g(S,14):t.icon==="undo-2"?g(A,15):t.icon==="volume-1"?g(B,16):t.icon==="volume-2"?g(x,17):t.icon==="volume-x"&&g(ge,18)})}Xt(()=>pa(a,1,As(E(r)))),R(e,a),I()}var of=Qt('<button type="button" class="aqe-button aqe-icon-only aqe-repeat-button" title="Repeat selected region, or the whole graph when no region is selected." aria-label="Repeat playback"><!> <span class="aqe-button-label">Repeat</span></button>'),sf=Qt('<button type="button" class="aqe-button aqe-menu-item" data-aqe-button-state="default" role="menuitem"><!> <span class="aqe-button-label"> </span></button>'),lf=Qt('<details class="aqe-menu"><summary class="aqe-button aqe-menu-summary" title="Denoise audio" aria-label="Denoise audio"><!> <span class="aqe-button-label">Denoise</span> <!></summary> <div class="aqe-menu-items" role="menu"></div></details>'),uf=Qt('<button type="button"><!> <!> <span class="aqe-button-label"> </span></button> <!> <!>',1),cf=Qt('<div class="aqe-controls"><!> <span class="aqe-status"></span> <details class="aqe-help"><summary class="aqe-help-summary" title="Show editor help"><!> <span>Help</span></summary> <div class="aqe-help-body"><p>Holding Shift on the graph selects a region. Playing with a selected region plays only that region; Repeat loops the selected region, or the full graph when no region is selected.</p> <p>Play starts or pauses audio. Graph shows the pitch and loudness graph. Folder opens the current audio file. -L and -R trim 100 ms from the left or right. Shorten Pauses speeds up long internal pauses. Denoise Standard uses DeepFilterNet, and Denoise MP-SENet uses MP-SENet. Slower and Faster change speed. Volume - and Volume + change loudness. Undo and Redo move through generated audio edits. Settings opens the add-on settings.</p> <p>In the graph, grey is loudness and lines are pitch of the voice.</p></div></details> <div class="aqe-visualizer" data-anchor-ms="0" data-cursor-ms="0" data-progress-ms="0" data-graph-active="false" data-graph-busy="false" data-has-track="false" data-playback-state="stopped" data-playback-engine="" data-playback-start-ms="0" data-playback-end-ms="0" data-playback-region-mode="full" data-resume-requires-restart="false" data-selection-active="false" data-selection-start-ms="" data-selection-end-ms="" data-selection-draft-active="false" data-selection-draft-start-ms="" data-selection-draft-end-ms="" hidden=""><audio class="aqe-audio-clock" preload="metadata" hidden=""></audio> <svg class="aqe-visualizer-svg" role="img" aria-label="Audio pitch and intensity visualization"><rect class="aqe-selection" width="0" visibility="hidden"></rect><path class="aqe-intensity" d=""></path><g class="aqe-pitch"></g><g class="aqe-labels"></g><g class="aqe-x-axis"></g><line class="aqe-selection-edge aqe-selection-start" visibility="hidden"></line><line class="aqe-selection-edge aqe-selection-end" visibility="hidden"></line><line class="aqe-cursor"></line></svg> <div class="aqe-visualizer-meta"><span class="aqe-spinner" hidden="" aria-hidden="true"></span> <span class="aqe-cursor-label">0 ms</span> <span class="aqe-visualizer-status"></span></div></div></div>');function ff(e,t){var ge;$(t,!0);const n=((ge=window.__AQE_EDITOR_CONFIG__)==null?void 0:ge.repeatPlaybackByDefault)===!0;function r(g){const ze=g.currentTarget.ariaPressed!=="true";ol(t.target.ord,ze)}xc(()=>{const g=L(t.target.ord);g&&(zi(g),ul(g),rl(g))});var a=cf(),o=ie(a);da(o,17,()=>D,g=>g.command,(g,Y)=>{var ze=uf(),ye=j(ze);let On;var Ln=ie(ye);Nt(Ln,{className:"aqe-button-icon-default",get icon(){return E(Y).icon}});var $n=W(Ln,2);{var fr=le=>{Nt(le,{className:"aqe-button-icon-active",get icon(){return E(Y).activeIcon}})};ir($n,le=>{E(Y).activeIcon&&le(fr)})}var dr=W($n,2),hr=ie(dr),Ae=W(ye,2);{var pr=le=>{var Oe=of(),_r=ie(Oe);Nt(_r,{icon:"repeat-2"}),Xt(()=>{q(Oe,"data-aqe-button-state",n?"active":"default"),q(Oe,"data-testid",`aqe-repeat-${t.target.ord}`),q(Oe,"aria-pressed",n?"true":"false")}),ft("mousedown",Oe,mr=>mr.preventDefault()),ft("click",Oe,r),R(le,Oe)};ir(Ae,le=>{E(Y).command==="aqe:play"&&le(pr)})}var Ff=W(Ae,2);{var xf=le=>{var Oe=lf(),_r=ie(Oe),mr=ie(_r);Nt(mr,{icon:"sparkles"});var Tf=W(mr,4);Nt(Tf,{className:"aqe-menu-chevron",icon:"chevron-down"});var Rf=W(_r,2);da(Rf,21,()=>O,Ma=>Ma.command,(Ma,Ot)=>{var pt=sf(),Us=ie(pt);Nt(Us,{get icon(){return E(Ot).icon}});var Df=W(Us,2),Of=ie(Df);Xt(qa=>{q(pt,"data-aqe-command",E(Ot).command),q(pt,"data-testid",qa),q(pt,"title",E(Ot).title),q(pt,"aria-label",E(Ot).title),Ms(Of,E(Ot).label)},[()=>Na(t.target.ord,E(Ot).command)]),ft("mousedown",pt,qa=>qa.preventDefault()),ft("click",pt,()=>io(E(Ot).command,t.target.node,t.target.ord)),R(Ma,pt)}),Xt(()=>q(Oe,"data-testid",`aqe-denoise-menu-${t.target.ord}`)),R(le,Oe)};ir(Ff,le=>{E(Y).command==="aqe:remove-pauses"&&le(xf)})}Xt(le=>{On=pa(ye,1,"aqe-button",null,On,{"aqe-icon-only":E(Y).iconOnly===!0}),q(ye,"data-aqe-command",E(Y).command),q(ye,"data-aqe-button-state",E(Y).command==="aqe:play"?"play":E(Y).command==="aqe:analyze"?"graph":"default"),q(ye,"data-testid",le),q(ye,"title",E(Y).title),q(ye,"aria-label",E(Y).title),Ms(hr,E(Y).label)},[()=>Na(t.target.ord,E(Y).command)]),ft("mousedown",ye,le=>le.preventDefault()),ft("click",ye,()=>io(E(Y).command,t.target.node,t.target.ord)),R(g,ze)});var s=W(o,2),i=W(s,2),l=ie(i),d=ie(l);Nt(d,{icon:"circle-help"});var f=W(i,2),u=ie(f),c=W(u,2),_=ie(c),v=W(_),w=W(v),p=W(w,2),m=W(p),k=W(m),b=W(k),S=W(c,2),A=ie(S),B=W(A,2),x=W(B,2);Xt(()=>{q(a,"data-aqe-field-ord",t.target.ord),q(a,"data-aqe-source-filename",t.target.sourceFilename),q(a,"data-testid",`aqe-controls-${t.target.ord}`),q(s,"data-testid",`aqe-status-${t.target.ord}`),q(i,"data-testid",`aqe-help-${t.target.ord}`),q(f,"data-aqe-field-ord",t.target.ord),q(f,"data-repeat-enabled",n?"true":"false"),q(f,"data-testid",`aqe-graph-${t.target.ord}`),q(u,"data-testid",`aqe-audio-clock-${t.target.ord}`),q(c,"data-testid",`aqe-graph-svg-${t.target.ord}`),q(c,"viewBox",`0 0 ${M.width} ${M.height}`),q(_,"data-testid",`aqe-selection-${t.target.ord}`),q(_,"x",M.left),q(_,"y",M.top),q(_,"height",M.height-M.top-M.bottom),q(v,"data-testid",`aqe-intensity-${t.target.ord}`),q(w,"data-testid",`aqe-pitch-${t.target.ord}`),q(p,"data-testid",`aqe-x-axis-${t.target.ord}`),q(m,"data-testid",`aqe-selection-start-${t.target.ord}`),q(m,"x1",M.left),q(m,"x2",M.left),q(m,"y1",M.top),q(m,"y2",M.height-M.bottom),q(k,"data-testid",`aqe-selection-end-${t.target.ord}`),q(k,"x1",M.left),q(k,"x2",M.left),q(k,"y1",M.top),q(k,"y2",M.height-M.bottom),q(b,"data-testid",`aqe-cursor-${t.target.ord}`),q(b,"x1",M.left),q(b,"x2",M.left),q(b,"y1",M.top),q(b,"y2",M.height-M.bottom),q(A,"data-testid",`aqe-graph-spinner-${t.target.ord}`),q(B,"data-testid",`aqe-progress-label-${t.target.ord}`),q(x,"data-testid",`aqe-graph-status-${t.target.ord}`)}),ft("pointerdown",c,g=>hl(g,t.target.ord)),R(e,a),I()}ys(["mousedown","click","pointerdown"]);const Jt=new Map;function df(e){const t=Jt.get(e.ord);if(t){if(document.body.contains(t.host)||Os(e,t.host),va(e.ord,t.host),!e.sourceFilename||t.sourceFilename===e.sourceFilename)return t;const o=L(e.ord);if((o==null?void 0:o.dataset.graphBusy)==="true"||(o==null?void 0:o.dataset.hasTrack)==="true"){const s=o.dataset.sourceFilename||e.sourceFilename;t.sourceFilename=s;const i=document.querySelector(`.aqe-controls[data-aqe-field-ord="${e.ord}"]`);return i&&(i.dataset.aqeSourceFilename=s),va(e.ord,t.host),t}}hf(e.ord);const n=document.createElement("div");n.className="aqe-mount-host",Os(e,n);const a={component:fc(ff,{target:n,props:{target:e}}),host:n,ord:e.ord,sourceFilename:e.sourceFilename};return Jt.set(e.ord,a),va(e.ord,n),a}function hf(e){const t=Jt.get(e);t&&(qs(t.component),t.host.remove(),Jt.delete(e)),document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>n.remove())}function pf(){for(const e of Jt.values())qs(e.component),e.host.remove();Jt.clear(),_f()}function Os(e,t){const n=e.node.closest(".field-container")||e.node.closest(".field")||e.node.parentElement||e.node;n.parentElement?n.after(t):e.node.after(t)}function va(e,t){document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>{t.contains(n)||n.remove()}),document.querySelectorAll(".aqe-mount-host").forEach(n=>{n!==t&&!n.querySelector(".aqe-controls")&&n.remove()})}function _f(){document.querySelectorAll(".aqe-mount-host").forEach(e=>e.remove()),document.querySelectorAll(".aqe-controls").forEach(e=>e.remove())}function mf(){window.__aqeGraphStateForTest=bf,window.__aqeInstallAudioPlaybackTestDriverForTest=vf,window.__aqeSetCursorByClientXForTest=yf,window.__aqeSetCursorForTest=gf}function vf(e){const t=L(e),n=Ee(t);return!t||!n?!1:(n.__aqeTestDriverInstalled=!0,n.pause=function(){n.__aqeTestPlaying=!1,n.__aqeTestFrame&&(window.cancelAnimationFrame(n.__aqeTestFrame),n.__aqeTestFrame=null)},n.play=function(){n.__aqeTestPlaying=!0,n.__aqeTestLastNow=performance.now();const a=()=>{if(!n.__aqeTestPlaying)return;const o=performance.now(),s=Number(t.dataset.durationMs||"0")/1e3,i=Math.max(0,(o-Number(n.__aqeTestLastNow||o))/1e3);if(n.__aqeTestLastNow=o,n.currentTime=Math.min(s,(Number(n.currentTime)||0)+i),s&&n.currentTime>=s){n.__aqeTestPlaying=!1,n.dispatchEvent(new Event("ended"));return}n.__aqeTestFrame=window.requestAnimationFrame(a)};return n.__aqeTestFrame=window.requestAnimationFrame(a),Promise.resolve()},!0)}function gf(e,t,n){const r=L(e);return r?(r.hidden=!1,r.dataset.graphActive="true",vt(r,t,!!n),!0):!1}function yf(e,t,n){var i;const r=L(e),a=(r==null?void 0:r.querySelector(".aqe-visualizer-svg"))??null;if(!r||!a)return null;const o=Number(r.dataset.durationMs||"0"),s=fn({clientX:t},a,o);return vt(r,s,!!n),{cursorMs:Number(r.dataset.cursorMs||"0"),cursorX:Number(((i=r.querySelector(".aqe-cursor"))==null?void 0:i.getAttribute("x1"))||"0"),bounds:Ya(a)}}function bf(e){var l,d,f,u;const t=L(e),n=xa(e),r=Ta(e);if(!t)return null;const a=Bn().flatMap(c=>Array.from(c.querySelectorAll(".aqe-button-icon svg"))),o=Ee(t),s=lo(t),i=uo(t);return{active:t.dataset.graphActive==="true",busy:t.dataset.graphBusy==="true",hidden:!!t.hidden,hasTrack:t.dataset.hasTrack==="true",durationMs:Number(t.dataset.durationMs||"0"),anchorMs:Number(t.dataset.anchorMs||"0"),cursorMs:Number(t.dataset.cursorMs||"0"),progressMs:Number(t.dataset.progressMs||"0"),sourceFilename:t.dataset.sourceFilename||"",graphButtonLabel:Ls(n),graphButtonState:(n==null?void 0:n.dataset.aqeButtonState)||"",playButtonLabel:Ls(r),playButtonState:(r==null?void 0:r.dataset.aqeButtonState)||"",playbackState:wf(t),selectionActive:s!==null,selectionStartMs:(s==null?void 0:s.startMs)??null,selectionEndMs:(s==null?void 0:s.endMs)??null,selectionDraftActive:i!==null,selectionDraftStartMs:(i==null?void 0:i.startMs)??null,selectionDraftEndMs:(i==null?void 0:i.endMs)??null,repeatEnabled:t.dataset.repeatEnabled==="true",repeatControlDisabled:!!((l=Ra(e))!=null&&l.disabled),playbackStartMs:Number(t.dataset.playbackStartMs||"0"),playbackEndMs:Number(t.dataset.playbackEndMs||"0"),playbackRegionMode:t.dataset.playbackRegionMode==="selection"?"selection":"full",resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true",audioClockSrc:o&&o.getAttribute("src")||"",audioClockCurrentMs:o?Math.round((Number(o.currentTime)||0)*1e3):0,audioClockReady:!!(o&&t.__aqeAudioClockAvailable),audioClockFallback:!!t.__aqeAudioClockFallback,audioClockMuted:!!(o&&o.muted),audioPlaybackTestDriver:!!(o&&o.__aqeTestDriverInstalled),playbackEngine:pn(t),progressClockMode:Mf(t),xAxisLabels:Array.from(t.querySelectorAll(".aqe-x-label")).map(c=>c.textContent||""),pitchPaths:t.querySelectorAll(".aqe-pitch-path").length,intensity:((d=t.querySelector(".aqe-intensity"))==null?void 0:d.getAttribute("d"))||"",cursorX:Number(((f=t.querySelector(".aqe-cursor"))==null?void 0:f.getAttribute("x1"))||"0"),spinnerVisible:t.querySelector(".aqe-spinner")?!((u=t.querySelector(".aqe-spinner"))!=null&&u.hidden):!1,allButtonsDisabled:Bn().every(c=>c.disabled),anyButtonDisabled:Bn().some(c=>c.disabled),buttonIconCount:a.length,buttonIconStrokeValues:a.map(c=>c.getAttribute("stroke")||getComputedStyle(c).stroke||"")}}function wf(e){const t=e.dataset.playbackState;return Ba(t)?t:"stopped"}function Mf(e){const t=e.dataset.progressClockMode;return t==="audio"||t==="manual"||t==="stopped"?t:"stopped"}function Ls(e){var t;return((t=e==null?void 0:e.querySelector(".aqe-button-label"))==null?void 0:t.textContent)||(e==null?void 0:e.textContent)||""}function qf(){window.__aqeSetBusy=Qn,window.__aqeSetStatus=so,window.__aqeSetVisualizer=_l,window.__aqeSetVisualizerStatus=ml,window.__aqeResetGraphAfterEdit=pl,window.__aqeSetPlaybackState=wl,window.__aqeGetPlaybackRequest=Ml,window.__aqeStopEditorPlayback=ql,window.__aqeGetCursorMs=Sl,window.__aqeGetCursorIntent=kl,window.__aqePrepareForNewNote=fo,window.__aqePopFrontendLog=Zs,mf()}const Sf=/\[sound:([^\]]+)\]/i,kf=/\.(mp3|wav|ogg)$/i;let Fn=[];function Af(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){$s(),window.__AQE_EDITOR_CONFIG__=e,qf(),fo(),di(),window.__aqeEditorDispose=$s,de.info("editor runtime initialized",{audioFieldIndices:e.audioFieldIndices,showGraphByDefault:e.showGraphByDefault===!0});const t=()=>Ef(e);window.__aqeScan=t,ya(t,0),ya(t,250),ya(t,1e3)}function $s(){Fn.forEach(e=>window.clearTimeout(e)),Fn=[],pf()}function Ef(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){if(e.audioFieldIndices.length){const r=Cf(e.audioFieldIndices,e.audioFieldSources);r.forEach(a=>Is(a)),de.debug("scan mounted explicit fields",{count:r.length}),Rr(),Bs(e,r);return}const t=[];let n=0;Pf().forEach((r,a)=>{const o=ga(r);if(!o)return;const s={node:r,ord:Nf(r,a),sourceFilename:o};Is(s),t.push(s),n+=1}),de.debug("scan mounted detected fields",{count:n}),Rr(),Bs(e,t)}function Pf(){const e=Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]')),t=new Set;return e.filter(n=>t.has(n)?!1:(t.add(n),!!(n.textContent||n.innerHTML)))}function Cf(e,t={}){return e.map(n=>{const r=document.querySelector(`.field-container[data-index="${n}"]`);if(!r)return null;const a=r.querySelector('[contenteditable="true"]')||r,o=ga(a)||ga(r)||t[n]||"";return{ord:n,node:a,sourceFilename:o}}).filter(n=>n!==null)}function Nf(e,t){const n=["data-field-ord","data-ord","data-index"];for(const a of n){const o=e.getAttribute(a);if(o!==null&&/^\d+$/.test(o))return Number(o)}const r=/(\d+)/.exec(String(e.id||""));return r?Number(r[1]):t}function ga(e){const t=e.innerHTML||e.textContent||"",n=Sf.exec(t),r=n==null?void 0:n[1];return r&&kf.test(r)?r:""}function Is(e){df(e)}function Bs(e,t){e.showGraphByDefault&&hi(t.map(({ord:n,sourceFilename:r})=>({ord:n,sourceFilename:r})),{anyBusy:()=>document.body.dataset.aqeBusy==="true",requestGraph:Zn})}function ya(e,t){const n=window.setTimeout(()=>{Fn=Fn.filter(r=>r!==n),e()},t);Fn.push(n)}Af()})();
