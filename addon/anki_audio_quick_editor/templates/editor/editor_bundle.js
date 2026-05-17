var pf=Object.defineProperty;var Es=T=>{throw TypeError(T)};var _f=(T,R,I)=>R in T?pf(T,R,{enumerable:!0,configurable:!0,writable:!0,value:I}):T[R]=I;var Le=(T,R,I)=>_f(T,typeof R!="symbol"?R+"":R,I),oa=(T,R,I)=>R.has(T)||Es("Cannot "+I);var h=(T,R,I)=>(oa(T,R,"read from private field"),I?I.call(T):R.get(T)),P=(T,R,I)=>R.has(T)?Es("Cannot add the same private member more than once"):R instanceof WeakSet?R.add(T):R.set(T,I),A=(T,R,I,An)=>(oa(T,R,"write to private field"),An?An.call(T,I):R.set(T,I),I),W=(T,R,I)=>(oa(T,R,"access private method"),I);(function(){"use strict";var bs,ws,Ms,Vt,jt,kt,Ht,Mn,kn,St,je,Wt,fe,sa,ia,la,Cs,be,ra,Te,qt,ie,Re,de,Ce,He,At,it,Ut,Kt,Xt,De,Zn,V,mf,vf,gf,ua,zn,er,ca,ks,Pe,$e,he,Et,Sn,qn,Jn,Ss;const T=[{activeIcon:"pause",command:"aqe:play",icon:"play",label:"Play",title:"Play or pause current audio"},{activeIcon:"refresh-cw",command:"aqe:analyze",icon:"chart-line",label:"Graph",title:"Analyze and show pitch/intensity graph"},{command:"aqe:show-file",icon:"folder-open",label:"Folder",title:"Show current audio file in folder"},{command:"aqe:trim-left",icon:"scissors",label:"-L",title:"Trim 100 ms from left"},{command:"aqe:trim-right",icon:"scissors",label:"-R",title:"Trim 100 ms from right"},{command:"aqe:remove-pauses",icon:"timer-reset",label:"Shorten Pauses",title:"Speed up long internal pauses"},{command:"aqe:sidon",icon:"wand-sparkles",label:"Sidon",title:"Restore speech with Sidon"},{command:"aqe:mp-senet",icon:"sparkles",label:"MP-SENet",title:"Denoise speech with MP-SENet"},{command:"aqe:remove-noise",icon:"volume-x",label:"Remove noise",title:"Reduce background noise with DeepFilterNet"},{command:"aqe:slower",icon:"rewind",label:"Slower",title:"Decrease speed"},{command:"aqe:faster",icon:"fast-forward",label:"Faster",title:"Increase speed"},{command:"aqe:volume-down",icon:"volume-1",label:"Volume -",title:"Decrease volume"},{command:"aqe:volume-up",icon:"volume-2",label:"Volume +",title:"Increase volume"},{command:"aqe:undo",icon:"undo-2",label:"Undo",title:"Restore the previous generated audio reference"}],R=new Set(["aqe:trim-left","aqe:trim-right","aqe:slower","aqe:faster","aqe:remove-pauses","aqe:remove-noise","aqe:sidon","aqe:mp-senet","aqe:volume-down","aqe:volume-up"]),I={"aqe:play":"play","aqe:analyze":"graph","aqe:show-file":"show-file","aqe:trim-left":"trim-left","aqe:trim-right":"trim-right","aqe:remove-pauses":"remove-pauses","aqe:remove-noise":"remove-noise","aqe:sidon":"sidon","aqe:mp-senet":"mp-senet","aqe:slower":"slower","aqe:faster":"faster","aqe:volume-down":"volume-down","aqe:volume-up":"volume-up","aqe:undo":"undo"};function An(e,t){return`aqe-button-${e}-${I[t]}`}function Ps(e){return e==="aqe:remove-noise"?"Removing noise...":e==="aqe:sidon"?"Restoring speech...":e==="aqe:mp-senet"?"Denoising with MP-SENet...":"Processing..."}function lt(e){return document.querySelector(`.aqe-controls[data-aqe-field-ord="${e}"]`)}function D(e){return document.querySelector(`.aqe-visualizer[data-aqe-field-ord="${e}"]`)}function fa(e,t){const n=lt(e);return(n==null?void 0:n.querySelector(`[data-aqe-command="${t}"]`))??null}function da(e){return fa(e,"aqe:analyze")}function ha(e){return fa(e,"aqe:play")}function pa(e){const t=lt(e);return(t==null?void 0:t.querySelector(".aqe-repeat-checkbox"))??null}function En(){return Array.from(document.querySelectorAll(".aqe-button"))}function Fs(){return Array.from(document.querySelectorAll(".aqe-repeat-checkbox"))}function _a(){return Array.from(document.querySelectorAll(".aqe-visualizer"))}const ma=[];function tr(e){globalThis.pycmd!==void 0&&globalThis.pycmd(e)}function Yt(e,t){tr(`focus:${e}`),tr(t)}function Ns(e){ma.push(e),tr("aqe:frontend-log")}function xs(){return ma.shift()??null}function Ts(e){window.__aqePendingPlaybackRequest=e,window.__aqeLastPlaybackRequest=e}function Rs(){if(!window.__aqePendingPlaybackRequest)return null;const e=window.__aqePendingPlaybackRequest;return window.__aqePendingPlaybackRequest=null,e}function Ds(e){window.__aqeLastCursorIntent=e}function $s(e){return encodeURIComponent(e||"").replaceAll("%2F","/")}function we(e){return(e==null?void 0:e.querySelector(".aqe-audio-clock"))??null}function nr(e){e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!1,e.__aqeAudioClockLastSeekedMs=0,e.dataset.progressClockMode="stopped"}function Qt(e){const t=we(e);if(!(!t||typeof t.pause!="function"))try{t.pause()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function rr(e){const t=we(e);if(nr(e),!!t){Qt(e),t.removeAttribute("src"),t.src="";try{t.load()}catch{e.__aqeAudioClockFallback=!0}}}function Ls(e,t){const n=we(e);if(nr(e),!n){e.__aqeAudioClockFallback=!0;return}if(Qt(e),!t){rr(e);return}n.setAttribute("src",$s(t));try{n.load()}catch{e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0}}function Os(e,t={}){const n=we(e);!n||n.__aqeClockHandlersInstalled||(n.__aqeClockHandlersInstalled=!0,n.addEventListener("loadedmetadata",()=>{n.getAttribute("src")&&(e.__aqeAudioClockAvailable=!0,e.__aqeAudioClockFallback=!1)}),n.addEventListener("error",()=>{var r;e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,e.dataset.playbackState==="playing"&&e.dataset.progressClockMode==="audio"&&((r=t.onErrorDuringPlayback)==null||r.call(t))}),n.addEventListener("ended",()=>{var r;e.dataset.playbackState==="playing"&&((r=t.onEndedDuringPlayback)==null||r.call(t))}),n.addEventListener("seeked",()=>{e.__aqeAudioClockLastSeekedMs=Math.round((Number(n.currentTime)||0)*1e3)}))}function Cn(e){const t=we(e);return!t||!(e!=null&&e.__aqeAudioClockAvailable)||!t.getAttribute("src")?!1:t.readyState===void 0||t.readyState>=1}function Pn(e,t,n){const r=we(e);if(!r)return!1;const a=Math.max(0,Math.min(Number(t)||0,n||0));try{return r.currentTime=a/1e3,e.__aqeAudioClockLastSeekedMs=Math.round(a),!0}catch{return e.__aqeAudioClockAvailable=!1,e.__aqeAudioClockFallback=!0,!1}}var Zt=(e=>(e.Debug="debug",e.Error="error",e.Info="info",e.Unknown="unknown",e.Warn="warn",e))(Zt||{});function Is(e){return e==="error"?console.error:console.warn}function Bs(e){return e==="debug"?Zt.Debug:e==="warn"?Zt.Warn:e==="error"?Zt.Error:Zt.Info}function ar(e,t=0){const n=Gs(e);return n!==void 0?n:Array.isArray(e)?Vs(e,t):e!==null&&typeof e=="object"?js(e,t):Hs(e)}function Gs(e){if(e===void 0)return"[undefined]";if(e===null)return null;if(typeof e=="boolean"||typeof e=="number"||typeof e=="string")return e}function Vs(e,t){return t>=4?"[array]":e.map(n=>ar(n,t+1))}function js(e,t){if(t>=4)return"[object]";const n={};for(const[r,a]of Object.entries(e))n[r]=ar(a,t+1);return n}function Hs(e){return typeof e=="bigint"?e.toString():typeof e=="symbol"?e.description?`Symbol(${e.description})`:"Symbol()":typeof e=="function"?`[function ${e.name||"anonymous"}]`:"[unserializable]"}function Ws(e,t,n){const r={level:Bs(e),message:t};return n!==void 0&&(r.context=ar(n)),r}function Us(e,t){function n(r,a,o){const s=Is(r);o===void 0?s(`[${e}] ${a}`):s(`[${e}] ${a}`,o);try{t(Ws(r,a,o))}catch{}}return{debug:(r,a)=>n("debug",r,a),error:(r,a)=>n("error",r,a),info:(r,a)=>n("info",r,a),warn:(r,a)=>n("warn",r,a)}}const le=Us("editor",Ns),Jt=[],Fn=new Set;let Nn=null,xn=null,Tn=!1;function Ks(){Jt.length=0,Fn.clear(),Nn=null,xn=null,Tn=!1}function Xs(e,t){for(const n of e){if(!n.sourceFilename)continue;const r=Ys(n);if(Fn.has(r))continue;const a=D(n.ord);if((a==null?void 0:a.dataset.hasTrack)==="true"&&a.dataset.sourceFilename===n.sourceFilename){Fn.add(r);continue}Fn.add(r),Jt.push({key:r,ord:n.ord,sourceFilename:n.sourceFilename})}Rn(t)}function Rn(e){if(!(Nn!==null||e.anyBusy()))for(;Jt.length;){const t=Jt.shift();if(!t)return;const n=D(t.ord);if(!n){ga(t,e);return}const r=lt(t.ord);if(!r){ga(t,e);return}if((r.dataset.aqeSourceFilename||t.sourceFilename)===t.sourceFilename&&!(n.dataset.hasTrack==="true"&&n.dataset.sourceFilename===t.sourceFilename)){Nn=t.key,xn=t.ord,e.requestGraph(t.ord,!0);return}}}function va(e,t){xn===e&&(Nn=null,xn=null,queueMicrotask(()=>Rn(t)))}function Ys(e){return`${e.ord}\0${e.sourceFilename}`}function ga(e,t){Jt.unshift(e),!Tn&&(Tn=!0,window.setTimeout(()=>{Tn=!1,Rn(t)},0))}function Qs(e,t){return Math.max(t.startMs,Math.min(Number(e)||0,t.endMs))}function Zs(e){let t="start";e.playbackState==="playing"&&(t="pause"),e.playbackState==="paused"&&(t=e.resumeRequiresRestart?"start":"resume");let n=e.anchorMs;return t==="start"&&e.region.mode==="selection"&&(n=e.region.startMs),t==="pause"&&(n=ya(e.currentProgressMs,e.cursorMs,n)),t==="resume"&&(n=ya(e.currentProgressMs,e.cursorMs,n),e.region.mode==="selection"&&(n<e.region.startMs||n>e.region.endMs)&&(t="start",n=e.region.startMs)),{action:t,cursorMs:Math.round(n),endMs:Math.round(e.region.endMs),engine:e.engine,loop:e.repeat,ord:e.ord,regionMode:e.region.mode}}function ya(e,t,n){return Number(e||t||n||0)}function Js(e){return{analyzerName:e.analyzerName,durationMs:Number(e.durationMs)||0,pitchMaxHz:e.pitchMaxHz,pitchMinHz:e.pitchMinHz,points:e.points.map(zs),sourceFilename:e.sourceFilename}}function zs(e){const t=typeof e[0]=="number"?e[0]:0,n=typeof e[1]=="number"?e[1]:null,r=typeof e[2]=="number"?e[2]:null,a=typeof e[3]=="boolean"?e[3]:!1;return[t,n,r,a]}function ba(e){return e==="playing"||e==="paused"||e==="stopped"}const wa=50,ei=4;function Ma(){return{active:!1,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:null,startMs:null}}function ka(e,t){return Math.max(0,Math.min(Number(e)||0,Math.max(0,Number(t)||0)))}function Dn(e,t,n,r=wa){const a=ka(Math.min(e,t),n),o=ka(Math.max(e,t),n);return!n||o-a<r?null:{startMs:Math.round(a),endMs:Math.round(o)}}function ti(e,t){if(!e.active||e.startMs===null||e.endMs===null)return null;const n=Dn(e.startMs,e.endMs,t);return n?{...n,mode:"selection"}:null}function ni(e,t){if(!e.draftActive||e.draftStartMs===null||e.draftEndMs===null)return null;const n=Dn(e.draftStartMs,e.draftEndMs,t);return n?{...n,mode:"selection"}:null}function ri(e,t,n,r){const a=Dn(t,n,r);return a?{...e,active:!0,draftActive:!1,draftEndMs:null,draftStartMs:null,endMs:a.endMs,startMs:a.startMs}:oi(e)}function ai(e,t,n,r){const a=Dn(t,n,r);return a?{...e,draftActive:!0,draftEndMs:a.endMs,draftStartMs:a.startMs}:Sa(e)}function oi(e){return{...Sa(e),active:!1,endMs:null,startMs:null}}function Sa(e){return{...e,draftActive:!1,draftEndMs:null,draftStartMs:null}}function qa(e,t,n,r){return Math.abs(t.clientX-e.clientX)<ei||Math.abs(r-n)<wa}const M={width:620,height:150,left:44,right:10,top:10,bottom:34};function Aa(){return M.width-M.left-M.right}function Ea(){return M.height-M.top-M.bottom}function Ue(e,t){return t?M.left+Math.max(0,Math.min(1,e/t))*Aa():M.left}function si(e,t,n){if(!e||!t||!n||n<=t)return M.height-M.bottom;const r=Math.max(0,Math.min(1,(e-t)/(n-t)));return M.top+(1-r)*Ea()}function Ca(e,t){return t&&t<2e3?`${Math.round(e)} ms`:`${(e/1e3).toFixed(2)}s`}function ii(e,t){if(!e.length||!t)return"";const n=M.height-M.bottom,r=e[0];if(!r)return"";const a=`M ${Ue(r[0],t).toFixed(2)} ${n.toFixed(2)}`,o=e.map(l=>{const c=Ue(l[0],t).toFixed(2),p=Math.max(0,Math.min(1,l[2]??0)),u=(n-p*Ea()).toFixed(2);return`L ${c} ${u}`}).join(" "),s=e.at(-1)??r,i=`L ${Ue(s[0],t).toFixed(2)} ${n.toFixed(2)} Z`;return`${a} ${o} ${i}`}function li(e,t,n,r){const a=[];let o=[];for(const s of e){const i=s[1];if(!(s[3]===!0&&i!==null&&i!==void 0)){o.length&&a.push(o),o=[];continue}o.push([Ue(s[0],t),si(i,n,r)])}return o.length&&a.push(o),a}function ui(e,t){const n=e.querySelector(".aqe-pitch");if(n){n.textContent="";for(const r of li(t.points,t.durationMs,t.pitchMinHz,t.pitchMaxHz)){if(r.length<2)continue;const a=document.createElementNS("http://www.w3.org/2000/svg","path");a.setAttribute("class","aqe-pitch-path"),a.setAttribute("d",r.map((o,s)=>{const i=o[0]??0,l=o[1]??0;return`${s?"L":"M"} ${i.toFixed(2)} ${l.toFixed(2)}`}).join(" ")),n.appendChild(a)}}}function ci(e,t){const n=e.querySelector(".aqe-labels");if(!n)return;n.textContent="";const r=t.pitchMaxHz||500,a=t.pitchMinHz||75;for(const o of[[r,M.top+10],[a,M.height-M.bottom]]){const s=document.createElementNS("http://www.w3.org/2000/svg","text");s.setAttribute("class","aqe-hz-label"),s.setAttribute("x","2"),s.setAttribute("y",String(o[1])),s.textContent=`${Math.round(o[0])} Hz`,n.appendChild(s)}}function fi(e,t){const n=e.querySelector(".aqe-x-axis");if(!n)return;n.textContent="";const r=[0,t/2,t].filter((a,o,s)=>o===0||a!==s[o-1]);for(const a of r){const o=Ue(a,t),s=document.createElementNS("http://www.w3.org/2000/svg","line");s.setAttribute("class","aqe-x-tick"),s.setAttribute("x1",o.toFixed(2)),s.setAttribute("x2",o.toFixed(2)),s.setAttribute("y1",String(M.height-M.bottom)),s.setAttribute("y2",String(M.height-M.bottom+4));const i=document.createElementNS("http://www.w3.org/2000/svg","text");i.setAttribute("class","aqe-x-label"),i.setAttribute("x",o.toFixed(2)),i.setAttribute("y",String(M.height-8)),i.textContent=Ca(a,t),n.append(s,i)}}function Pa(e){const t=e.getBoundingClientRect(),n=Number(t.width)||M.width,r=Number(t.height)||M.height,a=Math.min(n/M.width,r/M.height)||1;return{left:t.left+(n-M.width*a)/2+M.left*a,width:Aa()*a}}function zt(e,t,n){const r=Pa(t);return Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*n}function di(e){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="true",e.dataset.hasTrack="false",e.dataset.durationMs="0",e.dataset.sourceFilename="",e.dataset.anchorMs="0",e.dataset.cursorMs="0",e.dataset.progressMs="0",e.dataset.resumeRequiresRestart="false",e.dataset.playbackEngine="",e.dataset.playbackStartMs="0",e.dataset.playbackEndMs="0",e.dataset.playbackRegionMode="full",Fa(e)}function hi(e,t){e.hidden=!1,e.dataset.graphActive="true",e.dataset.graphBusy="false",e.dataset.hasTrack="true",e.dataset.durationMs=String(t.durationMs||0),e.dataset.analyzerName=t.analyzerName||"",e.dataset.sourceFilename=t.sourceFilename||"";const n=e.querySelector(".aqe-intensity");n&&n.setAttribute("d",ii(t.points,t.durationMs)),ui(e,t),ci(e,t),fi(e,t.durationMs||0)}function pi(e,t,n="info"){const r=e.querySelector(".aqe-visualizer-status"),a=e.querySelector(".aqe-spinner"),o=n==="processing";e.dataset.graphBusy=o?"true":"false",a&&(a.hidden=!o),r&&(r.textContent=t||"",r.dataset.kind=n||"info")}function _i(e,t,n){const r=e.querySelector(".aqe-selection"),a=e.querySelector(".aqe-selection-start"),o=e.querySelector(".aqe-selection-end"),s=n??t,i=Number(e.dataset.durationMs||"0");if(!r||!a||!o||!s||!i){r==null||r.setAttribute("width","0"),r==null||r.setAttribute("visibility","hidden"),r==null||r.classList.remove("aqe-selection-draft"),a==null||a.setAttribute("visibility","hidden"),o==null||o.setAttribute("visibility","hidden");return}const l=Ue(s.startMs,i),c=Ue(s.endMs,i);r.setAttribute("visibility","visible"),r.classList.toggle("aqe-selection-draft",n!==null),r.setAttribute("x",l.toFixed(2)),r.setAttribute("y",String(M.top)),r.setAttribute("width",Math.max(0,c-l).toFixed(2)),r.setAttribute("height",String(M.height-M.top-M.bottom)),a.setAttribute("visibility","visible"),o.setAttribute("visibility","visible");for(const[p,u]of[[a,l],[o,c]])p.setAttribute("x1",u.toFixed(2)),p.setAttribute("x2",u.toFixed(2)),p.setAttribute("y1",String(M.top)),p.setAttribute("y2",String(M.height-M.bottom))}function mi(e,t,n){const r=Ue(t,n),a=e.querySelector(".aqe-cursor");a&&(a.setAttribute("x1",r.toFixed(2)),a.setAttribute("x2",r.toFixed(2)));const o=e.querySelector(".aqe-cursor-label");o&&(o.textContent=Ca(t,n))}function Fa(e){var t;(t=e.querySelector(".aqe-intensity"))==null||t.setAttribute("d",""),or(e,".aqe-pitch"),or(e,".aqe-labels"),or(e,".aqe-x-axis")}function vi(e){const t=e.querySelector(".aqe-cursor");t&&(t.setAttribute("x1",String(M.left)),t.setAttribute("x2",String(M.left)));const n=e.querySelector(".aqe-cursor-label");n&&(n.textContent="0 ms")}function gi(e,t){return{analyzerName:t.analyzerName,durationMs:t.durationMs,ord:e,points:t.points.length,sourceFilename:t.sourceFilename}}function or(e,t){const n=e.querySelector(t);n&&(n.textContent="")}function sr(e){return!e||e.dataset.selectionActive!=="true"?null:ti({active:e.dataset.selectionActive==="true",startMs:Number(e.dataset.selectionStartMs||"0"),endMs:Number(e.dataset.selectionEndMs||"0")},Number(e.dataset.durationMs||"0"))}function ir(e){return!e||e.dataset.selectionDraftActive!=="true"?null:ni({draftActive:e.dataset.selectionDraftActive==="true",draftStartMs:Number(e.dataset.selectionDraftStartMs||"0"),draftEndMs:Number(e.dataset.selectionDraftEndMs||"0")},Number(e.dataset.durationMs||"0"))}function Na(e){const t=sr(e);return t||{startMs:0,endMs:Number(e.dataset.durationMs||"0")||0,mode:"full"}}function Ct(e,t={}){e.dataset.selectionDraftActive="false",e.dataset.selectionDraftStartMs="",e.dataset.selectionDraftEndMs="",t.redraw!==!1&&$n(e)}function yi(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=ai(Ma(),t,n,a);return!o.draftActive||o.draftStartMs===null||o.draftEndMs===null?(Ct(e,r),!1):(e.dataset.selectionDraftActive="true",e.dataset.selectionDraftStartMs=String(o.draftStartMs),e.dataset.selectionDraftEndMs=String(o.draftEndMs),r.redraw!==!1&&$n(e),!0)}function bi(e,t,n={}){const r=ir(e);return r?(Ct(e,{redraw:!1}),wi(e,r.startMs,r.endMs,t,n)):(Ct(e),!1)}function xa(e,t={}){if(e.dataset.selectionActive="false",e.dataset.selectionStartMs="",e.dataset.selectionEndMs="",Ct(e,{redraw:!1}),$n(e),t.resetPlaybackRegion!==!1){const n=Na(e);e.dataset.playbackStartMs=String(Math.round(n.startMs)),e.dataset.playbackEndMs=String(Math.round(n.endMs)),e.dataset.playbackRegionMode=n.mode}}function wi(e,t,n,r,a={}){const o=Number(e.dataset.durationMs||"0"),s=ri(Ma(),t,n,o);return!s.active||s.startMs===null||s.endMs===null?(xa(e),!1):(Ct(e,{redraw:!1}),e.dataset.selectionActive="true",e.dataset.selectionStartMs=String(s.startMs),e.dataset.selectionEndMs=String(s.endMs),e.dataset.playbackStartMs=String(s.startMs),e.dataset.playbackEndMs=String(s.endMs),e.dataset.playbackRegionMode="selection",$n(e),a.updateCursor!==!1&&r.setCursor(e,s.startMs,!1),!0)}function $n(e){const t=ir(e),n=t??sr(e);_i(e,n,t)}function Mi(e,t,n,r,a){e.preventDefault();const o=a.playbackStateFor(t),s=t.querySelector(".aqe-visualizer-svg"),i=Number(t.dataset.durationMs||"0");if(!s||!i)return;o==="playing"&&a.stopProgressClock(t);const l=p=>{a.setCursor(t,Ta(p,s,i,t,a),!1)},c=p=>{window.removeEventListener("pointermove",l),window.removeEventListener("pointerup",c);const u=o==="playing";o==="paused"&&(t.dataset.resumeRequiresRestart="true");const d=Ta(p,s,i,t,a),m=u&&a.audioClockReady(t)?"html":"";a.setCursor(t,d,r,{previousPlaybackState:o,restartPlayback:u,engine:m}),a.audioClockReady(t)&&a.seekAudioClock(t,d),u&&m==="html"&&a.startEditorHtmlPlayback(t,a.playbackRequestForStart(t,n,d,"html"))};l(e),window.addEventListener("pointermove",l),window.addEventListener("pointerup",c)}function ki(e,t,n,r){e.preventDefault();const a=t.querySelector(".aqe-visualizer-svg"),o=Number(t.dataset.durationMs||"0");if(!a||!o)return;const s=r.playbackStateFor(t),i=r.currentProgressMs(t)??Number(t.dataset.cursorMs||"0"),l={clientX:e.clientX},c=zt(e,a,o);let p=!1,u=S=>{},d=S=>{},m=()=>{},f=S=>{};const v=()=>{window.removeEventListener("pointermove",u),window.removeEventListener("pointerup",d),window.removeEventListener("pointercancel",m),window.removeEventListener("keydown",f),window.removeEventListener("blur",m),a.removeEventListener("lostpointercapture",m)},w=()=>{p||s!=="playing"||(p=!0,r.stopProgressClock(t,{clearEngine:!1}),r.setCursor(t,i,!1,{updateAnchor:!1}))},g=()=>{s==="playing"&&p&&r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,i,"html"))};u=S=>{const b=zt(S,a,o);if(qa(l,S,c,b)){r.clearSelectionDraft(t);return}w(),r.setSelectionDraft(t,c,b)},d=S=>{v();const b=zt(S,a,o);if(qa(l,S,c,b)){r.clearSelection(t),g();return}w(),r.draftSelectionForVisualizer(t)||r.setSelectionDraft(t,c,b,{redraw:!1});const k=r.commitSelectionDraft(t);if(s==="paused"&&(t.dataset.resumeRequiresRestart="true"),k&&s==="playing"){const _=r.selectionForVisualizer(t);r.startEditorHtmlPlayback(t,r.playbackRequestForStart(t,n,(_==null?void 0:_.startMs)??c,"html"))}},m=()=>{v(),r.clearSelectionDraft(t),g()},f=S=>{S.key==="Escape"&&m()},window.addEventListener("pointermove",u),window.addEventListener("pointerup",d),window.addEventListener("pointercancel",m),window.addEventListener("keydown",f),window.addEventListener("blur",m),a.addEventListener("lostpointercapture",m)}function Si(e,t,n){const r=n.visualizerForOrd(t);if(r){if(e.shiftKey){ki(e,r,t,n);return}Mi(e,r,t,!0,n)}}function Ta(e,t,n,r,a){const o=zt(e,t,n),s=a.selectionForVisualizer(r);return s&&r.dataset.repeatEnabled==="true"?Qs(o,s):o}function ut(e){e.__aqePlaybackTimer&&(window.cancelAnimationFrame(e.__aqePlaybackTimer),e.__aqePlaybackTimer=null)}function Ra(e){const t=Number(e.dataset.durationMs||"0"),n=performance.now()-Number(e.dataset.playStartedAt||"0");return Math.min(t,Number(e.dataset.playStartMs||"0")+n)}function Da(e){const t=we(e);if(!t)return null;const n=Number(e.dataset.durationMs||"0");return Math.min(n,(Number(t.currentTime)||0)*1e3)}function $a(e){return e.dataset.progressClockMode==="audio"?Da(e):e.dataset.progressClockMode==="manual"?Ra(e):Number(e.dataset.progressMs||e.dataset.cursorMs||"0")}function lr(e,t,n,r={}){return t<Pi(e,n)?!1:n.repeatEnabledFor(e)?(Fi(e,n,r),!0):(qi(e,n),!0)}function qi(e,t){const n=Number(e.dataset.aqeFieldOrd||"0"),r=t.effectivePlaybackRegion(e),a=e.dataset.playbackRegionMode==="selection"?r.startMs:Number(e.dataset.anchorMs||"0");cr(e,t),t.setCursor(e,a,!1,{updateAnchor:!1}),Cn(e)&&Pn(e,a,Number(e.dataset.durationMs||"0")),t.clearStatus(n),window.__aqeActiveField=n,t.focusAndSendCommand(n,"aqe:play-ended")}function ur(e,t){const n=()=>{if(e.dataset.playbackState!=="playing")return;const r=Da(e);if(r===null){Oe(e,Number(e.dataset.cursorMs||"0"),t);return}t.setCursor(e,r,!1,{updateAnchor:!1}),!lr(e,r,t)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(n))};e.__aqePlaybackTimer=window.requestAnimationFrame(n)}function Oe(e,t,n){if(ut(e),Qt(e),!Number(e.dataset.durationMs||"0"))return;const a=La(e,t);e.__aqeAudioClockFallback=!0,e.dataset.playbackState="playing",e.dataset.progressClockMode="manual",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),fr(e,a,n),n.setPlaybackButtonLabel(e,"Pause");const o=()=>{if(e.dataset.playbackState!=="playing")return;const s=Ra(e);n.setCursor(e,s,!1,{updateAnchor:!1}),!lr(e,s,n)&&(e.__aqePlaybackTimer=window.requestAnimationFrame(o))};e.__aqePlaybackTimer=window.requestAnimationFrame(o)}function Ai(e,t,n,r={}){var i;const a=we(e);if(!a||!Pn(e,t,Number(e.dataset.durationMs||"0"))||typeof a.play!="function"){if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}Oe(e,t,n);return}e.dataset.progressClockMode="audio",e.__aqeAudioClockFallback=!1;const o=()=>{var l;if(r.manualFallback===!1){(l=r.onAudioPlayFailed)==null||l.call(r);return}Oe(e,t,n)},s=()=>{var l;e.dataset.playbackState==="playing"&&(ut(e),e.dataset.progressClockMode="audio",le.info("html audio playback started",{ord:e.dataset.aqeFieldOrd}),ur(e,n),(l=r.onAudioStarted)==null||l.call(r))};Promise.resolve(a.play()).then(s).catch(()=>{e.dataset.playbackState==="playing"&&(le.warn("html audio play rejected; using manual clock",{ord:e.dataset.aqeFieldOrd}),o())})}function Ei(e,t,n,r={}){var i;const a=r.engine||e.dataset.playbackEngine||"";if(cr(e,n,{clearEngine:!1}),n.stopOtherPlayback(e),!Number(e.dataset.durationMs||"0"))return;const s=La(e,t);if(e.dataset.playbackEngine=a,e.dataset.playbackState="playing",e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(s),fr(e,s,n),n.setCursor(e,s,!1,{updateAnchor:!1}),n.setPlaybackButtonLabel(e,"Pause"),le.info("playback clock selected",{engine:a||"auto",startMs:s}),a==="native"){Oe(e,s,n);return}if(Cn(e)){Ai(e,s,n,r);return}if(r.manualFallback===!1){(i=r.onAudioPlayFailed)==null||i.call(r);return}Oe(e,s,n)}function Ci(e,t){const n=$a(e);n!==null&&t.setCursor(e,n,!1,{updateAnchor:!1}),ut(e),Qt(e),e.dataset.playbackState="paused",e.dataset.progressClockMode="stopped",t.setPlaybackButtonLabel(e,"Play")}function cr(e,t,n={}){ut(e),Qt(e),e.dataset.playbackState="stopped",e.dataset.progressClockMode="stopped",e.dataset.resumeRequiresRestart="false",n.clearEngine!==!1&&(e.dataset.playbackEngine=""),n.clearAudio&&rr(e),t.setPlaybackButtonLabel(e,"Play")}function fr(e,t,n,r=n.effectivePlaybackRegion(e)){e.dataset.playbackStartMs=String(Math.round(t)),e.dataset.playbackEndMs=String(Math.round(r.endMs)),e.dataset.playbackRegionMode=r.mode}function Pi(e,t){const n=t.effectivePlaybackRegion(e),r=Number(e.dataset.playbackEndMs||"0")||n.endMs;return Math.max(n.startMs,Math.min(r,Number(e.dataset.durationMs||"0")||0))}function Fi(e,t,n={}){const r=t.effectivePlaybackRegion(e),a=r.startMs;if(fr(e,a,t,r),e.dataset.playStartedAt=String(performance.now()),e.dataset.playStartMs=String(a),t.setCursor(e,a,!1,{updateAnchor:!1}),e.dataset.progressClockMode!=="audio"||!Cn(e)){Oe(e,a,t);return}if(!Pn(e,a,Number(e.dataset.durationMs||"0"))){Oe(e,a,t);return}if(!n.forceAudioPlay){ut(e),ur(e,t);return}const o=we(e);!o||typeof o.play!="function"||(ut(e),Promise.resolve(o.play()).then(()=>{e.dataset.playbackState==="playing"&&ur(e,t)}).catch(()=>{e.dataset.playbackState==="playing"&&Oe(e,a,t)}))}function La(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function Oa(){return document.body.dataset.aqeBusy==="true"}function Ia(){var e;return((e=window.__AQE_EDITOR_CONFIG__)==null?void 0:e.repeatPlaybackByDefault)===!0}function Ni(e){for(const t of _a())t!==e&&Ft(t)!=="stopped"&&ft(t)}function xi(){for(const e of _a())Ft(e)!=="stopped"&&ft(e)}function Ln(e,t,n="",r=""){document.body.dataset.aqeBusy=t?"true":"false",document.querySelectorAll(".aqe-controls").forEach(s=>{s.dataset.busy=t?"true":"false"}),En().forEach(s=>{s.disabled=!!t}),Fs().forEach(s=>{s.disabled=!!t}),t||queueMicrotask(()=>Rn(gr()));const a=lt(e),o=a==null?void 0:a.querySelector(".aqe-status");o&&(o.textContent=n||"",o.dataset.kind=t?"processing":"info",o.title=r||"")}function Ba(e,t="info"){const n=Number(window.__aqeActiveField??0),r=lt(n),a=r==null?void 0:r.querySelector(".aqe-status");a&&(a.textContent=e||"",a.dataset.kind=t||"info")}function Ti(e){const t=lt(e),n=t==null?void 0:t.querySelector(".aqe-status");n&&(n.textContent="",n.dataset.kind="info",n.title="")}function Pt(e,t,n){var o;const r=t==="aqe:play"?ha(e):t==="aqe:analyze"?da(e):((o=lt(e))==null?void 0:o.querySelector(`[data-aqe-command="${t}"]`))??null;if(!r)return;const a=r.querySelector(".aqe-button-label");a?a.textContent=n:r.textContent=n,t==="aqe:play"&&(r.dataset.aqeButtonState=n==="Pause"?"pause":"play"),t==="aqe:analyze"&&(r.dataset.aqeButtonState=n==="Redraw"?"redraw":"graph")}function Ri(e,t,n){if(!Oa()){if(typeof t.focus=="function"&&t.focus(),window.__aqeActiveField=n,le.info("command dispatched",{command:e,ord:n}),e==="aqe:analyze"){On(n,!0);return}e==="aqe:play"&&nl(n)||(R.has(e)&&(xi(),Ln(n,!0,Ps(e))),Yt(n,e))}}function Di(e){nr(e)}function $i(e){ut(e)}function Li(e){rr(e)}function Oi(e,t){Ls(e,t)}function Ii(e){Os(e,{onErrorDuringPlayback(){le.warn("audio clock failed during playback",{ord:e.dataset.aqeFieldOrd}),tl(e,Number(e.dataset.cursorMs||"0"))},onEndedDuringPlayback(){el(e,Number(e.dataset.durationMs||"0"),{forceAudioPlay:!0})}})}function dr(e){return Cn(e)}function Bi(e,t){const n=Number(e.dataset.durationMs||"0");return Math.max(0,Math.min(Number(t)||0,n||0))}function Ga(e){return sr(e)}function Va(e){return ir(e)}function hr(e){return Na(e)}function pr(e,t){e.dataset.repeatEnabled=t?"true":"false";const n=Number(e.dataset.aqeFieldOrd||"0"),r=pa(n);r&&(r.checked=t)}function Gi(e,t){const n=D(e);return n?(pr(n,t),!0):!1}function Vi(e,t={}){Ct(e,t)}function ji(e,t,n,r={}){return yi(e,t,n,r)}function Hi(e,t={}){return bi(e,Ki(),t)}function en(e,t={}){xa(e,t)}function Wi(e){e.dataset.playbackStartMs="0",e.dataset.playbackEndMs=String(Number(e.dataset.durationMs||"0")||0),e.dataset.playbackRegionMode="full",pr(e,Ia()),en(e,{resetPlaybackRegion:!1})}function Ui(){return{audioClockReady:dr,clearSelection:en,clearSelectionDraft:Vi,commitSelectionDraft:Hi,currentProgressMs:Wa,draftSelectionForVisualizer:Va,playbackRequestForStart:Xi,playbackStateFor:Ft,seekAudioClock:ja,selectionForVisualizer:Ga,setCursor:ct,setSelectionDraft:ji,startEditorHtmlPlayback:Ya,stopProgressClock:ft,visualizerForOrd:D}}function Ki(){return{setCursor:ct}}function _r(e){return e.dataset.repeatEnabled==="true"}function tn(){return{clearStatus:Ti,effectivePlaybackRegion:hr,focusAndSendCommand:Yt,playbackEngineFor:nn,repeatEnabledFor:_r,setCursor:ct,setPlaybackButtonLabel:zi,stopOtherPlayback:Ni}}function Xi(e,t,n,r=nn(e)){const a=hr(e);return{ord:t,action:"start",cursorMs:Math.round(Bi(e,n)),endMs:Math.round(a.endMs),engine:r,loop:_r(e),regionMode:a.mode}}function ja(e,t){return Pn(e,t,Number(e.dataset.durationMs||"0"))}function ct(e,t,n,r={}){const a=Number(e.dataset.durationMs||"0"),o=Math.max(0,Math.min(Number(t)||0,a||0));if(e.dataset.cursorMs=String(Math.round(o)),e.dataset.progressMs=String(Math.round(o)),r.updateAnchor!==!1&&(e.dataset.anchorMs=String(Math.round(o))),mi(e,o,a),n){window.__aqeActiveField=Number(e.dataset.aqeFieldOrd||"0");const s={cursorMs:Math.round(o),previousPlaybackState:r.previousPlaybackState||Ft(e),restartPlayback:!!r.restartPlayback};r.engine&&(s.engine=r.engine),Ds(s),le.info("cursor committed",s),Yt(window.__aqeActiveField,"aqe:set-cursor")}}function Yi(e,t){Si(e,t,Ui())}function On(e,t){const n=D(e);n&&(ft(n,{clearAudio:!0}),di(n),en(n),ct(n,0,!1),Pt(e,"aqe:analyze","Redraw"),vr(e,"Analyzing...","processing"),window.__aqeActiveField=e,le.info("graph requested",{notifyPython:t,ord:e}),t&&(Ln(e,!0,"Analyzing...",""),Yt(e,"aqe:analyze")))}function Qi(e){return window.__aqePendingGraphRedrawField=e,mr()}function mr(){const e=window.__aqePendingGraphRedrawField;if(typeof e!="number")return!1;const t=D(e);return t?(t.dataset.graphBusy==="true"||t.dataset.hasTrack==="true"||On(e,!0),!0):!1}function vr(e,t,n="info"){const r=D(e);r&&pi(r,t,n)}function Zi(e,t,n){const r=D(e);if(!r||!t)return;const a=Js(t);hi(r,a),r.dataset.anchorMs=String(n||0),window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null),en(r),r.dataset.playbackStartMs="0",r.dataset.playbackEndMs=String(a.durationMs||0),r.dataset.playbackRegionMode="full",Oi(r,a.sourceFilename||""),Pt(e,"aqe:analyze","Redraw"),ct(r,n||0,!1),dr(r)&&ja(r,n||0),vr(e,a.analyzerName||"","info"),Ln(e,!1,"",""),va(e,gr()),le.info("graph rendered",gi(e,a))}function Ji(e,t,n="info"){n!=="processing"&&window.__aqePendingGraphRedrawField===e&&(window.__aqePendingGraphRedrawField=null);const r=D(e);r&&(r.hidden=!1,r.dataset.graphActive="true",n==="processing"&&(r.dataset.hasTrack="false"),Pt(e,"aqe:analyze","Redraw")),vr(e,t,n),n!=="processing"&&va(e,gr())}function gr(){return{anyBusy:Oa,requestGraph:On}}function Ha(){document.body.dataset.aqeBusy="false",window.__aqeActiveField=null,window.__aqeLastCursorIntent=null,document.querySelectorAll(".aqe-controls").forEach(e=>{e.dataset.busy="false",e.dataset.aqeSourceFilename="",e.querySelectorAll(".aqe-button").forEach(o=>{o.disabled=!1,o.dataset.aqeCommand==="aqe:analyze"&&Pt(Number(e.dataset.aqeFieldOrd||"0"),"aqe:analyze","Graph"),o.dataset.aqeCommand==="aqe:play"&&Pt(Number(e.dataset.aqeFieldOrd||"0"),"aqe:play","Play")}),e.querySelectorAll(".aqe-repeat-checkbox").forEach(o=>{o.disabled=!1});const t=e.querySelector(".aqe-status");t&&(t.textContent="",t.dataset.kind="info",t.title="");const n=e.querySelector(".aqe-visualizer");if(!n)return;$i(n),Li(n),n.hidden=!0,n.dataset.anchorMs="0",n.dataset.cursorMs="0",n.dataset.progressMs="0",n.dataset.graphActive="false",n.dataset.graphBusy="false",n.dataset.hasTrack="false",n.dataset.playbackState="stopped",n.dataset.playbackEngine="",n.dataset.resumeRequiresRestart="false",n.dataset.durationMs="0",n.dataset.sourceFilename="",n.dataset.analyzerName="",n.dataset.playStartedAt="0",n.dataset.playStartMs="0",n.dataset.playbackStartMs="0",n.dataset.playbackEndMs="0",n.dataset.playbackRegionMode="full",n.dataset.progressClockMode="stopped",pr(n,Ia()),en(n),Fa(n),vi(n);const r=n.querySelector(".aqe-visualizer-status");r&&(r.textContent="",r.dataset.kind="info");const a=n.querySelector(".aqe-spinner");a&&(a.hidden=!0)})}function zi(e,t){const n=Number(e.dataset.aqeFieldOrd||"0");Pt(n,"aqe:play",t)}function Wa(e){return $a(e)}function el(e,t,n={}){return lr(e,t,tn(),n)}function tl(e,t){Oe(e,t,tn())}function Ua(e,t,n={}){Ei(e,t,tn(),n)}function Ka(e){Ci(e,tn())}function ft(e,t={}){cr(e,tn(),t)}function Xa(e){const t=D(e);return t?Zs({anchorMs:Number(t.dataset.anchorMs||t.dataset.cursorMs||"0"),currentProgressMs:Wa(t),cursorMs:Number(t.dataset.cursorMs||"0"),engine:nn(t),ord:e,playbackState:Ft(t),region:hr(t),repeat:_r(t),resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true"}):{ord:e,action:"start",cursorMs:0}}function nn(e){if(!e||e.dataset.hasTrack!=="true")return"native";const t=e.dataset.playbackEngine||"";return e.dataset.playbackState!=="stopped"&&(t==="html"||t==="native")?t:dr(e)?"html":"native"}function yr(e){const t=D(e.ord);t&&(t.dataset.playbackEngine=e.engine||""),Ts(e),window.__aqeActiveField=e.ord,le.info("playback request queued",e),Yt(e.ord,"aqe:play")}function Ya(e,t){return Ua(e,t.cursorMs,{engine:"html",manualFallback:!1,onAudioStarted(){yr(t)},onAudioPlayFailed(){if(le.warn("html playback failed; falling back to native",{ord:t.ord}),ft(e),t.regionMode==="selection"||t.loop){window.__aqeActiveField=t.ord,Ba("Selected repeat playback needs browser audio.","warning");return}yr({...t,engine:"native"})}}),!0}function nl(e){const t=D(e);if(!t||nn(t)!=="html")return!1;const n={...Xa(e),engine:"html"};return n.action==="pause"?(Ka(t),n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0"),yr(n),!0):(n.action==="resume"&&(n.cursorMs=Number(t.dataset.cursorMs||n.cursorMs||"0")),Ya(t,n))}function rl(e,t,n){const r=D(e);r&&((t==="playing"||t==="paused")&&(r.dataset.resumeRequiresRestart="false"),t==="playing"?Ua(r,n,{engine:r.dataset.playbackEngine==="html"||r.dataset.playbackEngine==="native"?r.dataset.playbackEngine:""}):t==="paused"?Ka(r):ft(r))}function al(){const e=Rs();if(e)return e;const t=Number(window.__aqeActiveField||"0"),n=Xa(t),r=D(t);return r&&(r.dataset.playbackEngine=n.engine||""),n}function ol(e){const t=D(e);return t?(ft(t),!0):!1}function sl(){const e=Number(window.__aqeActiveField||"0"),t=D(e);return t?Number(t.dataset.cursorMs||"0"):0}function il(){const e=Number(window.__aqeActiveField||"0"),t=D(e),n=t?Number(t.dataset.cursorMs||"0"):0;return window.__aqeLastCursorIntent||{cursorMs:n,previousPlaybackState:t?Ft(t):"stopped",restartPlayback:!1}}function Ft(e){const t=e.dataset.playbackState;return ba(t)?t:"stopped"}const Qa=(ws=(bs=globalThis.process)==null?void 0:bs.env)==null?void 0:ws.NODE_ENV,y=Qa&&!Qa.toLowerCase().startsWith("prod");var br=Array.isArray,ll=Array.prototype.indexOf,dt=Array.prototype.includes,In=Array.from,ht=Object.defineProperty,Ie=Object.getOwnPropertyDescriptor,ul=Object.getOwnPropertyDescriptors,cl=Object.prototype,fl=Array.prototype,Za=Object.getPrototypeOf,Ja=Object.isExtensible;function rn(e){return typeof e=="function"}const U=()=>{};function dl(e){for(var t=0;t<e.length;t++)e[t]()}function za(){var e,t,n=new Promise((r,a)=>{e=r,t=a});return{promise:n,resolve:e,reject:t}}function hl(e,t){if(Array.isArray(e))return e;if(!(Symbol.iterator in e))return Array.from(e);const n=[];for(const r of e)if(n.push(r),n.length===t)break;return n}const K=2,an=4,Bn=8,wr=1<<24,Be=16,Me=32,pt=64,Mr=128,_e=512,j=1024,X=2048,ke=4096,ue=8192,Ge=16384,_t=32768,Ke=65536,Gn=1<<17,eo=1<<18,Nt=1<<19,pl=1<<20,Xe=1<<25,Ye=65536,kr=1<<21,Vn=1<<22,Qe=1<<23,Ze=Symbol("$state"),to=Symbol("legacy props"),_l=Symbol(""),no=Symbol("proxy path"),mt=new class extends Error{constructor(){super(...arguments);Le(this,"name","StaleReactionError");Le(this,"message","The reaction that called `getAbortSignal()` was re-run or destroyed")}},ro=!!((Ms=globalThis.document)!=null&&Ms.contentType)&&globalThis.document.contentType.includes("xml");function ao(e){if(y){const t=new Error(`lifecycle_outside_component
\`${e}(...)\` can only be used during component initialisation
https://svelte.dev/e/lifecycle_outside_component`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/lifecycle_outside_component")}function ml(){if(y){const e=new Error("async_derived_orphan\nCannot create a `$derived(...)` with an `await` expression outside of an effect tree\nhttps://svelte.dev/e/async_derived_orphan");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/async_derived_orphan")}function vl(){if(y){const e=new Error(`derived_references_self
A derived value cannot reference itself recursively
https://svelte.dev/e/derived_references_self`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/derived_references_self")}function oo(e,t,n){if(y){const r=new Error(`each_key_duplicate
${n?`Keyed each block has duplicate key \`${n}\` at indexes ${e} and ${t}`:`Keyed each block has duplicate key at indexes ${e} and ${t}`}
https://svelte.dev/e/each_key_duplicate`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_duplicate")}function gl(e,t,n){if(y){const r=new Error(`each_key_volatile
Keyed each block has key that is not idempotent — the key for item at index ${e} was \`${t}\` but is now \`${n}\`. Keys must be the same each time for a given item
https://svelte.dev/e/each_key_volatile`);throw r.name="Svelte error",r}else throw new Error("https://svelte.dev/e/each_key_volatile")}function yl(e){if(y){const t=new Error(`effect_in_teardown
\`${e}\` cannot be used inside an effect cleanup function
https://svelte.dev/e/effect_in_teardown`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_in_teardown")}function bl(){if(y){const e=new Error("effect_in_unowned_derived\nEffect cannot be created inside a `$derived` value that was not itself created inside an effect\nhttps://svelte.dev/e/effect_in_unowned_derived");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_in_unowned_derived")}function wl(e){if(y){const t=new Error(`effect_orphan
\`${e}\` can only be used inside an effect (e.g. during component initialisation)
https://svelte.dev/e/effect_orphan`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/effect_orphan")}function Ml(){if(y){const e=new Error(`effect_update_depth_exceeded
Maximum update depth exceeded. This typically indicates that an effect reads and writes the same piece of state
https://svelte.dev/e/effect_update_depth_exceeded`);throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/effect_update_depth_exceeded")}function kl(){if(y){const e=new Error("invalid_snippet\nCould not `{@render}` snippet due to the expression being `null` or `undefined`. Consider using optional chaining `{@render snippet?.()}`\nhttps://svelte.dev/e/invalid_snippet");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/invalid_snippet")}function Sl(e){if(y){const t=new Error(`props_invalid_value
Cannot do \`bind:${e}={undefined}\` when \`${e}\` has a fallback value
https://svelte.dev/e/props_invalid_value`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_invalid_value")}function ql(e){if(y){const t=new Error(`props_rest_readonly
Rest element properties of \`$props()\` such as \`${e}\` are readonly
https://svelte.dev/e/props_rest_readonly`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/props_rest_readonly")}function Al(e){if(y){const t=new Error(`rune_outside_svelte
The \`${e}\` rune is only available inside \`.svelte\` and \`.svelte.js/ts\` files
https://svelte.dev/e/rune_outside_svelte`);throw t.name="Svelte error",t}else throw new Error("https://svelte.dev/e/rune_outside_svelte")}function El(){if(y){const e=new Error("state_descriptors_fixed\nProperty descriptors defined on `$state` objects must contain `value` and always be `enumerable`, `configurable` and `writable`.\nhttps://svelte.dev/e/state_descriptors_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_descriptors_fixed")}function Cl(){if(y){const e=new Error("state_prototype_fixed\nCannot set prototype of `$state` object\nhttps://svelte.dev/e/state_prototype_fixed");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_prototype_fixed")}function Pl(){if(y){const e=new Error("state_unsafe_mutation\nUpdating state inside `$derived(...)`, `$inspect(...)` or a template expression is forbidden. If the value should not be reactive, declare it without `$state`\nhttps://svelte.dev/e/state_unsafe_mutation");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/state_unsafe_mutation")}function Fl(){if(y){const e=new Error("svelte_boundary_reset_onerror\nA `<svelte:boundary>` `reset` function cannot be called while an error is still being handled\nhttps://svelte.dev/e/svelte_boundary_reset_onerror");throw e.name="Svelte error",e}else throw new Error("https://svelte.dev/e/svelte_boundary_reset_onerror")}const Nl=1,xl=2,Tl=16,Rl=1,Dl=4,$l=8,Ll=16,Ol=1,Il=2,H=Symbol(),Bl=Symbol("filename"),so="http://www.w3.org/1999/xhtml",Gl="http://www.w3.org/2000/svg",Vl="@attach";var on="font-weight: bold",sn="font-weight: normal";function jl(){y?console.warn(`%c[svelte] lifecycle_double_unmount
%cTried to unmount a component that was not mounted
https://svelte.dev/e/lifecycle_double_unmount`,on,sn):console.warn("https://svelte.dev/e/lifecycle_double_unmount")}function Hl(){y?console.warn("%c[svelte] select_multiple_invalid_value\n%cThe `value` property of a `<select multiple>` element should be an array, but it received a non-array value. The selection will be kept as is.\nhttps://svelte.dev/e/select_multiple_invalid_value",on,sn):console.warn("https://svelte.dev/e/select_multiple_invalid_value")}function Sr(e){y?console.warn(`%c[svelte] state_proxy_equality_mismatch
%cReactive \`$state(...)\` proxies and the values they proxy have different identities. Because of this, comparisons with \`${e}\` will produce unexpected results
https://svelte.dev/e/state_proxy_equality_mismatch`,on,sn):console.warn("https://svelte.dev/e/state_proxy_equality_mismatch")}function Wl(){y?console.warn(`%c[svelte] state_proxy_unmount
%cTried to unmount a state proxy, rather than a component
https://svelte.dev/e/state_proxy_unmount`,on,sn):console.warn("https://svelte.dev/e/state_proxy_unmount")}function Ul(){y?console.warn("%c[svelte] svelte_boundary_reset_noop\n%cA `<svelte:boundary>` `reset` function only resets the boundary the first time it is called\nhttps://svelte.dev/e/svelte_boundary_reset_noop",on,sn):console.warn("https://svelte.dev/e/svelte_boundary_reset_noop")}function io(e){return e===this.v}function Kl(e,t){return e!=e?t==t:e!==t||e!==null&&typeof e=="object"||typeof e=="function"}function lo(e){return!Kl(e,this.v)}let Xl=!1;function Ne(e,t){return e.label=t,uo(e.v,t),e}function uo(e,t){var n;return(n=e==null?void 0:e[no])==null||n.call(e,t),e}function Yl(e){const t=new Error,n=Ql();return n.length===0?null:(n.unshift(`
`),ht(t,"stack",{value:n.join(`
`)}),ht(t,"name",{value:e}),t)}function Ql(){const e=Error.stackTraceLimit;Error.stackTraceLimit=1/0;const t=new Error().stack;if(Error.stackTraceLimit=e,!t)return[];const n=t.split(`
`),r=[];for(let a=0;a<n.length;a++){const o=n[a],s=o.replaceAll("\\","/");if(o.trim()!=="Error"){if(o.includes("validate_each_keys"))return[];s.includes("svelte/src/internal")||s.includes("node_modules/.vite")||r.push(o)}}return r}let $=null;function xt(e){$=e}let Tt=null;function jn(e){Tt=e}let ln=null;function co(e){ln=e}function Zl(e){return Jl("getContext").get(e)}function B(e,t=!1,n){$={p:$,i:!1,c:null,e:null,s:e,x:null,l:null},y&&($.function=n,ln=n)}function G(e){var t=$,n=t.e;if(n!==null){t.e=null;for(var r of n)Ro(r)}return t.i=!0,$=t.p,y&&(ln=($==null?void 0:$.function)??null),{}}function fo(){return!0}function Jl(e){return $===null&&ao(e),$.c??($.c=new Map(zl($)||void 0))}function zl(e){let t=e.p;for(;t!==null;){const n=t.c;if(n!==null)return n;t=t.p}return null}let Rt=[];function eu(){var e=Rt;Rt=[],dl(e)}function Je(e){if(Rt.length===0){var t=Rt;queueMicrotask(()=>{t===Rt&&eu()})}Rt.push(e)}const qr=new WeakMap;function ho(e){var t=F;if(t===null)return E.f|=Qe,e;if(y&&e instanceof Error&&!qr.has(e)&&qr.set(e,tu(e,t)),(t.f&_t)===0&&(t.f&an)===0)throw y&&!t.parent&&e instanceof Error&&po(e),e;ze(e,t)}function ze(e,t){for(;t!==null;){if((t.f&Mr)!==0){if((t.f&_t)===0)throw e;try{t.b.error(e);return}catch(n){e=n}}t=t.parent}throw y&&e instanceof Error&&po(e),e}function tu(e,t){var s,i,l;const n=Ie(e,"message");if(!(n&&!n.configurable)){for(var r=Rr?"  ":"	",a=`
${r}in ${((s=t.fn)==null?void 0:s.name)||"<unknown>"}`,o=t.ctx;o!==null;)a+=`
${r}in ${(i=o.function)==null?void 0:i[Bl].split("/").pop()}`,o=o.p;return{message:e.message+`
${a}
`,stack:(l=e.stack)==null?void 0:l.split(`
`).filter(c=>!c.includes("svelte/src/internal")).join(`
`)}}}function po(e){const t=qr.get(e);t&&(ht(e,"message",{value:t.message}),ht(e,"stack",{value:t.stack}))}const nu=-7169;function L(e,t){e.f=e.f&nu|t}function Ar(e){(e.f&_e)!==0||e.deps===null?L(e,j):L(e,ke)}function _o(e){if(e!==null)for(const t of e)(t.f&K)===0||(t.f&Ye)===0||(t.f^=Ye,_o(t.deps))}function mo(e,t,n){(e.f&X)!==0?t.add(e):(e.f&ke)!==0&&n.add(e),_o(e.deps),L(e,j)}const Hn=new Set;let N=null,Y=null,me=[],Er=null,Cr=!1;const na=class na{constructor(){P(this,fe);Le(this,"current",new Map);Le(this,"previous",new Map);P(this,Vt,new Set);P(this,jt,new Set);P(this,kt,0);P(this,Ht,0);P(this,Mn,null);P(this,kn,new Set);P(this,St,new Set);P(this,je,new Map);Le(this,"is_fork",!1);P(this,Wt,!1)}skip_effect(t){h(this,je).has(t)||h(this,je).set(t,{d:[],m:[]})}unskip_effect(t){var n=h(this,je).get(t);if(n){h(this,je).delete(t);for(var r of n.d)L(r,X),qe(r);for(r of n.m)L(r,ke),qe(r)}}process(t){var a;me=[],this.apply();var n=[],r=[];for(const o of t)W(this,fe,ia).call(this,o,n,r);if(W(this,fe,sa).call(this)){W(this,fe,la).call(this,r),W(this,fe,la).call(this,n);for(const[o,s]of h(this,je))bo(o,s)}else{for(const o of h(this,Vt))o();h(this,Vt).clear(),h(this,kt)===0&&W(this,fe,Cs).call(this),N=null,vo(r),vo(n),(a=h(this,Mn))==null||a.resolve()}Y=null}capture(t,n){n!==H&&!this.previous.has(t)&&this.previous.set(t,n),(t.f&Qe)===0&&(this.current.set(t,t.v),Y==null||Y.set(t,t.v))}activate(){N=this,this.apply()}deactivate(){N===this&&(N=null,Y=null)}flush(){if(this.activate(),me.length>0){if(ru(),N!==null&&N!==this)return}else h(this,kt)===0&&this.process([]);this.deactivate()}discard(){for(const t of h(this,jt))t(this);h(this,jt).clear()}increment(t){A(this,kt,h(this,kt)+1),t&&A(this,Ht,h(this,Ht)+1)}decrement(t){A(this,kt,h(this,kt)-1),t&&A(this,Ht,h(this,Ht)-1),!h(this,Wt)&&(A(this,Wt,!0),Je(()=>{A(this,Wt,!1),W(this,fe,sa).call(this)?me.length>0&&this.flush():this.revive()}))}revive(){for(const t of h(this,kn))h(this,St).delete(t),L(t,X),qe(t);for(const t of h(this,St))L(t,ke),qe(t);this.flush()}oncommit(t){h(this,Vt).add(t)}ondiscard(t){h(this,jt).add(t)}settled(){return(h(this,Mn)??A(this,Mn,za())).promise}static ensure(){if(N===null){const t=N=new na;Hn.add(N),Je(()=>{N===t&&t.flush()})}return N}apply(){}};Vt=new WeakMap,jt=new WeakMap,kt=new WeakMap,Ht=new WeakMap,Mn=new WeakMap,kn=new WeakMap,St=new WeakMap,je=new WeakMap,Wt=new WeakMap,fe=new WeakSet,sa=function(){return this.is_fork||h(this,Ht)>0},ia=function(t,n,r){t.f^=j;for(var a=t.first;a!==null;){var o=a.f,s=(o&(Me|pt))!==0,i=s&&(o&j)!==0,l=i||(o&ue)!==0||h(this,je).has(a);if(!l&&a.fn!==null){s?a.f^=j:(o&an)!==0?n.push(a):hn(a)&&((o&Be)!==0&&h(this,St).add(a),It(a));var c=a.first;if(c!==null){a=c;continue}}for(;a!==null;){var p=a.next;if(p!==null){a=p;break}a=a.parent}}},la=function(t){for(var n=0;n<t.length;n+=1)mo(t[n],h(this,kn),h(this,St))},Cs=function(){var a;if(Hn.size>1){this.previous.clear();var t=Y,n=!0;for(const o of Hn){if(o===this){n=!1;continue}const s=[];for(const[l,c]of this.current){if(o.current.has(l))if(n&&c!==o.current.get(l))o.current.set(l,c);else continue;s.push(l)}if(s.length===0)continue;const i=[...o.current.keys()].filter(l=>!this.current.has(l));if(i.length>0){var r=me;me=[];const l=new Set,c=new Map;for(const p of s)go(p,i,l,c);if(me.length>0){N=o,o.apply();for(const p of me)W(a=o,fe,ia).call(a,p,[],[]);o.deactivate()}me=r}}N=null,Y=t}Hn.delete(this)};let et=na;function ru(){Cr=!0;var e=y?new Set:null;try{for(var t=0;me.length>0;){var n=et.ensure();if(t++>1e3){if(y){var r=new Map;for(const o of n.current.keys())for(const[s,i]of o.updated??[]){var a=r.get(s);a||(a={error:i.error,count:0},r.set(s,a)),a.count+=i.count}for(const o of r.values())o.error&&console.error(o.error)}au()}if(n.process(me),tt.clear(),y)for(const o of n.current.keys())e.add(o)}}finally{if(me=[],Cr=!1,Er=null,y)for(const o of e)o.updated=null}}function au(){try{Ml()}catch(e){y&&ht(e,"stack",{value:""}),ze(e,Er)}}let Se=null;function vo(e){var t=e.length;if(t!==0){for(var n=0;n<t;){var r=e[n++];if((r.f&(Ge|ue))===0&&hn(r)&&(Se=new Set,It(r),r.deps===null&&r.first===null&&r.nodes===null&&r.teardown===null&&r.ac===null&&Oo(r),(Se==null?void 0:Se.size)>0)){tt.clear();for(const a of Se){if((a.f&(Ge|ue))!==0)continue;const o=[a];let s=a.parent;for(;s!==null;)Se.has(s)&&(Se.delete(s),o.push(s)),s=s.parent;for(let i=o.length-1;i>=0;i--){const l=o[i];(l.f&(Ge|ue))===0&&It(l)}}Se.clear()}}Se=null}}function go(e,t,n,r){if(!n.has(e)&&(n.add(e),e.reactions!==null))for(const a of e.reactions){const o=a.f;(o&K)!==0?go(a,t,n,r):(o&(Vn|Be))!==0&&(o&X)===0&&yo(a,t,r)&&(L(a,X),qe(a))}}function yo(e,t,n){const r=n.get(e);if(r!==void 0)return r;if(e.deps!==null)for(const a of e.deps){if(dt.call(t,a))return!0;if((a.f&K)!==0&&yo(a,t,n))return n.set(a,!0),!0}return n.set(e,!1),!1}function qe(e){var t=Er=e,n=t.b;if(n!=null&&n.is_pending&&(e.f&(an|Bn|wr))!==0&&(e.f&_t)===0){n.defer_effect(e);return}for(;t.parent!==null;){t=t.parent;var r=t.f;if(Cr&&t===F&&(r&Be)!==0&&(r&eo)===0&&(r&_t)!==0)return;if((r&(pt|Me))!==0){if((r&j)===0)return;t.f^=j}}me.push(t)}function bo(e,t){if(!((e.f&Me)!==0&&(e.f&j)!==0)){(e.f&X)!==0?t.d.push(e):(e.f&ke)!==0&&t.m.push(e),L(e,j);for(var n=e.first;n!==null;)bo(n,t),n=n.next}}function ou(e){let t=0,n=vt(0),r;return y&&Ne(n,"createSubscriber version"),()=>{$r()&&(x(n),Fu(()=>(t===0&&(r=Gr(()=>e(()=>un(n)))),t+=1,()=>{Je(()=>{t-=1,t===0&&(r==null||r(),r=void 0,un(n))})})))}}var su=Ke|Nt;function iu(e,t,n,r){new lu(e,t,n,r)}class lu{constructor(t,n,r,a){P(this,V);Le(this,"parent");Le(this,"is_pending",!1);Le(this,"transform_error");P(this,be);P(this,ra,null);P(this,Te);P(this,qt);P(this,ie);P(this,Re,null);P(this,de,null);P(this,Ce,null);P(this,He,null);P(this,At,0);P(this,it,0);P(this,Ut,!1);P(this,Kt,new Set);P(this,Xt,new Set);P(this,De,null);P(this,Zn,ou(()=>(A(this,De,vt(h(this,At))),y&&Ne(h(this,De),"$effect.pending()"),()=>{A(this,De,null)})));var o;A(this,be,t),A(this,Te,n),A(this,qt,s=>{var i=F;i.b=this,i.f|=Mr,r(s)}),this.parent=F.b,this.transform_error=a??((o=this.parent)==null?void 0:o.transform_error)??(s=>s),A(this,ie,dn(()=>{W(this,V,ua).call(this)},su))}defer_effect(t){mo(t,h(this,Kt),h(this,Xt))}is_rendered(){return!this.is_pending&&(!this.parent||this.parent.is_rendered())}has_pending_snippet(){return!!h(this,Te).pending}update_pending_count(t){W(this,V,ca).call(this,t),A(this,At,h(this,At)+t),!(!h(this,De)||h(this,Ut))&&(A(this,Ut,!0),Je(()=>{A(this,Ut,!1),h(this,De)&&$t(h(this,De),h(this,At))}))}get_effect_pending(){return h(this,Zn).call(this),x(h(this,De))}error(t){var n=h(this,Te).onerror;let r=h(this,Te).failed;if(!n&&!r)throw t;h(this,Re)&&(Z(h(this,Re)),A(this,Re,null)),h(this,de)&&(Z(h(this,de)),A(this,de,null)),h(this,Ce)&&(Z(h(this,Ce)),A(this,Ce,null));var a=!1,o=!1;const s=()=>{if(a){Ul();return}a=!0,o&&Fl(),h(this,Ce)!==null&&yt(h(this,Ce),()=>{A(this,Ce,null)}),W(this,V,er).call(this,()=>{et.ensure(),W(this,V,ua).call(this)})},i=l=>{try{o=!0,n==null||n(l,s),o=!1}catch(c){ze(c,h(this,ie)&&h(this,ie).parent)}r&&A(this,Ce,W(this,V,er).call(this,()=>{et.ensure();try{return oe(()=>{var c=F;c.b=this,c.f|=Mr,r(h(this,be),()=>l,()=>s)})}catch(c){return ze(c,h(this,ie).parent),null}}))};Je(()=>{var l;try{l=this.transform_error(t)}catch(c){ze(c,h(this,ie)&&h(this,ie).parent);return}l!==null&&typeof l=="object"&&typeof l.then=="function"?l.then(i,c=>ze(c,h(this,ie)&&h(this,ie).parent)):i(l)})}}be=new WeakMap,ra=new WeakMap,Te=new WeakMap,qt=new WeakMap,ie=new WeakMap,Re=new WeakMap,de=new WeakMap,Ce=new WeakMap,He=new WeakMap,At=new WeakMap,it=new WeakMap,Ut=new WeakMap,Kt=new WeakMap,Xt=new WeakMap,De=new WeakMap,Zn=new WeakMap,V=new WeakSet,mf=function(){try{A(this,Re,oe(()=>h(this,qt).call(this,h(this,be))))}catch(t){this.error(t)}},vf=function(t){const n=h(this,Te).failed;n&&A(this,Ce,oe(()=>{n(h(this,be),()=>t,()=>()=>{})}))},gf=function(){const t=h(this,Te).pending;t&&(this.is_pending=!0,A(this,de,oe(()=>t(h(this,be)))),Je(()=>{var n=A(this,He,document.createDocumentFragment()),r=at();n.append(r),A(this,Re,W(this,V,er).call(this,()=>(et.ensure(),oe(()=>h(this,qt).call(this,r))))),h(this,it)===0&&(h(this,be).before(n),A(this,He,null),yt(h(this,de),()=>{A(this,de,null)}),W(this,V,zn).call(this))}))},ua=function(){try{if(this.is_pending=this.has_pending_snippet(),A(this,it,0),A(this,At,0),A(this,Re,oe(()=>{h(this,qt).call(this,h(this,be))})),h(this,it)>0){var t=A(this,He,document.createDocumentFragment());Go(h(this,Re),t);const n=h(this,Te).pending;A(this,de,oe(()=>n(h(this,be))))}else W(this,V,zn).call(this)}catch(n){this.error(n)}},zn=function(){this.is_pending=!1;for(const t of h(this,Kt))L(t,X),qe(t);for(const t of h(this,Xt))L(t,ke),qe(t);h(this,Kt).clear(),h(this,Xt).clear()},er=function(t){var n=F,r=E,a=$;Ee(h(this,ie)),ve(h(this,ie)),xt(h(this,ie).ctx);try{return t()}catch(o){return ho(o),null}finally{Ee(n),ve(r),xt(a)}},ca=function(t){var n;if(!this.has_pending_snippet()){this.parent&&W(n=this.parent,V,ca).call(n,t);return}A(this,it,h(this,it)+t),h(this,it)===0&&(W(this,V,zn).call(this),h(this,de)&&yt(h(this,de),()=>{A(this,de,null)}),h(this,He)&&(h(this,be).before(h(this,He)),A(this,He,null)))};function wo(e,t,n,r){const a=Wn;var o=e.filter(u=>!u.settled);if(n.length===0&&o.length===0){r(t.map(a));return}var s=F,i=uu(),l=o.length===1?o[0].promise:o.length>1?Promise.all(o.map(u=>u.promise)):null;function c(u){i();try{r(u)}catch(d){(s.f&Ge)===0&&ze(d,s)}Pr()}if(n.length===0){l.then(()=>c(t.map(a)));return}function p(){i(),Promise.all(n.map(u=>du(u))).then(u=>c([...t.map(a),...u])).catch(u=>ze(u,s))}l?l.then(p):p()}function uu(){var e=F,t=E,n=$,r=N;if(y)var a=Tt;return function(s=!0){Ee(e),ve(t),xt(n),s&&(r==null||r.activate()),y&&jn(a)}}function Pr(e=!0){Ee(null),ve(null),xt(null),e&&(N==null||N.deactivate()),y&&jn(null)}function cu(){var e=F.b,t=N,n=e.is_rendered();return e.update_pending_count(1),t.increment(n),()=>{e.update_pending_count(-1),t.decrement(n)}}const fu=new Set;function Wn(e){var t=K|X,n=E!==null&&(E.f&K)!==0?E:null;return F!==null&&(F.f|=Nt),{ctx:$,deps:null,effects:null,equals:io,f:t,fn:e,reactions:null,rv:0,v:H,wv:0,parent:n??F,ac:null}}function du(e,t,n){F===null&&ml();var a=void 0,o=vt(H);y&&(o.label=t);var s=!E,i=new Map;return Pu(()=>{var d;var l=za();a=l.promise;try{Promise.resolve(e()).then(l.resolve,l.reject).finally(Pr)}catch(m){l.reject(m),Pr()}var c=N;if(s){var p=cu();(d=i.get(c))==null||d.reject(mt),i.delete(c),i.set(c,l)}const u=(m,f=void 0)=>{if(c.activate(),f)f!==mt&&(o.f|=Qe,$t(o,f));else{(o.f&Qe)!==0&&(o.f^=Qe),$t(o,m);for(const[v,w]of i){if(i.delete(v),v===c)break;w.reject(mt)}}p&&p()};l.promise.then(u,m=>u(null,m||"unknown"))}),Lr(()=>{for(const l of i.values())l.reject(mt)}),y&&(o.f|=Vn),new Promise(l=>{function c(p){function u(){p===a?l(o):c(a)}p.then(u,u)}c(a)})}function Fr(e){const t=Wn(e);return jo(t),t}function Mo(e){const t=Wn(e);return t.equals=lo,t}function ko(e){var t=e.effects;if(t!==null){e.effects=null;for(var n=0;n<t.length;n+=1)Z(t[n])}}let Nr=[];function hu(e){for(var t=e.parent;t!==null;){if((t.f&K)===0)return(t.f&Ge)===0?t:null;t=t.parent}return null}function xr(e){var t,n=F;if(Ee(hu(e)),y){let r=Dt;Ao(new Set);try{dt.call(Nr,e)&&vl(),Nr.push(e),e.f&=~Ye,ko(e),t=Br(e)}finally{Ee(n),Ao(r),Nr.pop()}}else try{e.f&=~Ye,ko(e),t=Br(e)}finally{Ee(n)}return t}function So(e){var t=xr(e);if(!e.equals(t)&&(e.wv=Uo(),(!(N!=null&&N.is_fork)||e.deps===null)&&(e.v=t,e.deps===null))){L(e,j);return}ot||(Y!==null?($r()||N!=null&&N.is_fork)&&Y.set(e,t):Ar(e))}function pu(e){var t,n;if(e.effects!==null)for(const r of e.effects)(r.teardown||r.ac)&&((t=r.teardown)==null||t.call(r),(n=r.ac)==null||n.abort(mt),r.teardown=U,r.ac=null,pn(r,0),Or(r))}function qo(e){if(e.effects!==null)for(const t of e.effects)t.teardown&&It(t)}let Dt=new Set;const tt=new Map;function Ao(e){Dt=e}let Tr=!1;function _u(){Tr=!0}function vt(e,t){var n={f:0,v:e,reactions:null,equals:io,rv:0,wv:0};return n}function nt(e,t){const n=vt(e);return jo(n),n}function mu(e,t=!1,n=!0){const r=vt(e);return t||(r.equals=lo),r}function rt(e,t,n=!1){E!==null&&(!Ae||(E.f&Gn)!==0)&&fo()&&(E.f&(K|Be|Vn|Gn))!==0&&(ge===null||!dt.call(ge,e))&&Pl();let r=n?Lt(t):t;return y&&uo(r,e.label),$t(e,r)}function $t(e,t){var a;if(!e.equals(t)){var n=e.v;ot?tt.set(e,t):tt.set(e,n),e.v=t;var r=et.ensure();if(r.capture(e,n),y){if(F!==null){e.updated??(e.updated=new Map);const o=(((a=e.updated.get(""))==null?void 0:a.count)??0)+1;if(e.updated.set("",{error:null,count:o}),o>5){const s=Yl("updated at");if(s!==null){let i=e.updated.get(s.stack);i||(i={error:s,count:0},e.updated.set(s.stack,i)),i.count++}}}F!==null&&(e.set_during_effect=!0)}if((e.f&K)!==0){const o=e;(e.f&X)!==0&&xr(o),Ar(o)}e.wv=Uo(),Co(e,X),F!==null&&(F.f&j)!==0&&(F.f&(Me|pt))===0&&(ye===null?Tu([e]):ye.push(e)),!r.is_fork&&Dt.size>0&&!Tr&&Eo()}return t}function Eo(){Tr=!1;for(const e of Dt)(e.f&j)!==0&&L(e,ke),hn(e)&&It(e);Dt.clear()}function un(e){rt(e,e.v+1)}function Co(e,t){var n=e.reactions;if(n!==null)for(var r=n.length,a=0;a<r;a++){var o=n[a],s=o.f;if(y&&(s&Gn)!==0){Dt.add(o);continue}var i=(s&X)===0;if(i&&L(o,t),(s&K)!==0){var l=o;Y==null||Y.delete(l),(s&Ye)===0&&(s&_e&&(o.f|=Ye),Co(l,ke))}else i&&((s&Be)!==0&&Se!==null&&Se.add(o),qe(o))}}const vu=/^[a-zA-Z_$][a-zA-Z_$0-9]*$/;function Lt(e){if(typeof e!="object"||e===null||Ze in e)return e;const t=Za(e);if(t!==cl&&t!==fl)return e;var n=new Map,r=br(e),a=nt(0),o=wt,s=p=>{if(wt===o)return p();var u=E,d=wt;ve(null),Wo(o);var m=p();return ve(u),Wo(d),m};r&&(n.set("length",nt(e.length)),y&&(e=bu(e)));var i="";let l=!1;function c(p){if(!l){l=!0,i=p,Ne(a,`${i} version`);for(const[u,d]of n)Ne(d,gt(i,u));l=!1}}return new Proxy(e,{defineProperty(p,u,d){(!("value"in d)||d.configurable===!1||d.enumerable===!1||d.writable===!1)&&El();var m=n.get(u);return m===void 0?s(()=>{var f=nt(d.value);return n.set(u,f),y&&typeof u=="string"&&Ne(f,gt(i,u)),f}):rt(m,d.value,!0),!0},deleteProperty(p,u){var d=n.get(u);if(d===void 0){if(u in p){const m=s(()=>nt(H));n.set(u,m),un(a),y&&Ne(m,gt(i,u))}}else rt(d,H),un(a);return!0},get(p,u,d){var w;if(u===Ze)return e;if(y&&u===no)return c;var m=n.get(u),f=u in p;if(m===void 0&&(!f||(w=Ie(p,u))!=null&&w.writable)&&(m=s(()=>{var g=Lt(f?p[u]:H),S=nt(g);return y&&Ne(S,gt(i,u)),S}),n.set(u,m)),m!==void 0){var v=x(m);return v===H?void 0:v}return Reflect.get(p,u,d)},getOwnPropertyDescriptor(p,u){var d=Reflect.getOwnPropertyDescriptor(p,u);if(d&&"value"in d){var m=n.get(u);m&&(d.value=x(m))}else if(d===void 0){var f=n.get(u),v=f==null?void 0:f.v;if(f!==void 0&&v!==H)return{enumerable:!0,configurable:!0,value:v,writable:!0}}return d},has(p,u){var v;if(u===Ze)return!0;var d=n.get(u),m=d!==void 0&&d.v!==H||Reflect.has(p,u);if(d!==void 0||F!==null&&(!m||(v=Ie(p,u))!=null&&v.writable)){d===void 0&&(d=s(()=>{var w=m?Lt(p[u]):H,g=nt(w);return y&&Ne(g,gt(i,u)),g}),n.set(u,d));var f=x(d);if(f===H)return!1}return m},set(p,u,d,m){var J;var f=n.get(u),v=u in p;if(r&&u==="length")for(var w=d;w<f.v;w+=1){var g=n.get(w+"");g!==void 0?rt(g,H):w in p&&(g=s(()=>nt(H)),n.set(w+"",g),y&&Ne(g,gt(i,w)))}if(f===void 0)(!v||(J=Ie(p,u))!=null&&J.writable)&&(f=s(()=>nt(void 0)),y&&Ne(f,gt(i,u)),rt(f,Lt(d)),n.set(u,f));else{v=f.v!==H;var S=s(()=>Lt(d));rt(f,S)}var b=Reflect.getOwnPropertyDescriptor(p,u);if(b!=null&&b.set&&b.set.call(m,d),!v){if(r&&typeof u=="string"){var k=n.get("length"),_=Number(u);Number.isInteger(_)&&_>=k.v&&rt(k,_+1)}un(a)}return!0},ownKeys(p){x(a);var u=Reflect.ownKeys(p).filter(f=>{var v=n.get(f);return v===void 0||v.v!==H});for(var[d,m]of n)m.v!==H&&!(d in p)&&u.push(d);return u},setPrototypeOf(){Cl()}})}function gt(e,t){return typeof t=="symbol"?`${e}[Symbol(${t.description??""})]`:vu.test(t)?`${e}.${t}`:/^\d+$/.test(t)?`${e}[${t}]`:`${e}['${t}']`}function cn(e){try{if(e!==null&&typeof e=="object"&&Ze in e)return e[Ze]}catch{}return e}function gu(e,t){return Object.is(cn(e),cn(t))}const yu=new Set(["copyWithin","fill","pop","push","reverse","shift","sort","splice","unshift"]);function bu(e){return new Proxy(e,{get(t,n,r){var a=Reflect.get(t,n,r);return yu.has(n)?function(...o){_u();var s=a.apply(this,o);return Eo(),s}:a}})}function wu(){const e=Array.prototype,t=Array.__svelte_cleanup;t&&t();const{indexOf:n,lastIndexOf:r,includes:a}=e;e.indexOf=function(o,s){const i=n.call(this,o,s);if(i===-1){for(let l=s??0;l<this.length;l+=1)if(cn(this[l])===o){Sr("array.indexOf(...)");break}}return i},e.lastIndexOf=function(o,s){const i=r.call(this,o,s??this.length-1);if(i===-1){for(let l=0;l<=(s??this.length-1);l+=1)if(cn(this[l])===o){Sr("array.lastIndexOf(...)");break}}return i},e.includes=function(o,s){const i=a.call(this,o,s);if(!i){for(let l=0;l<this.length;l+=1)if(cn(this[l])===o){Sr("array.includes(...)");break}}return i},Array.__svelte_cleanup=()=>{e.indexOf=n,e.lastIndexOf=r,e.includes=a}}var Po,Rr,Fo,No;function Mu(){if(Po===void 0){Po=window,Rr=/Firefox/.test(navigator.userAgent);var e=Element.prototype,t=Node.prototype,n=Text.prototype;Fo=Ie(t,"firstChild").get,No=Ie(t,"nextSibling").get,Ja(e)&&(e.__click=void 0,e.__className=void 0,e.__attributes=null,e.__style=void 0,e.__e=void 0),Ja(n)&&(n.__t=void 0),y&&(e.__svelte_meta=null,wu())}}function at(e=""){return document.createTextNode(e)}function Ot(e){return Fo.call(e)}function fn(e){return No.call(e)}function Ve(e,t){return Ot(e)}function Q(e,t=!1){{var n=Ot(e);return n instanceof Comment&&n.data===""?fn(n):n}}function z(e,t=1,n=!1){let r=e;for(;t--;)r=fn(r);return r}function ku(e){e.textContent=""}function xo(){return!1}function To(e,t,n){return document.createElementNS(t??so,e,void 0)}function Su(e,t){if(t){const n=document.body;e.autofocus=!0,Je(()=>{document.activeElement===n&&e.focus()})}}function Dr(e){var t=E,n=F;ve(null),Ee(null);try{return e()}finally{ve(t),Ee(n)}}function qu(e){F===null&&(E===null&&wl(e),bl()),ot&&yl(e)}function Au(e,t){var n=t.last;n===null?t.last=t.first=e:(n.next=e,e.prev=n,t.last=e)}function xe(e,t,n){var r=F;if(y)for(;r!==null&&(r.f&Gn)!==0;)r=r.parent;r!==null&&(r.f&ue)!==0&&(e|=ue);var a={ctx:$,deps:null,nodes:null,f:e|X|_e,first:null,fn:t,last:null,next:null,parent:r,b:r&&r.b,prev:null,teardown:null,wv:0,ac:null};if(y&&(a.component_function=ln),n)try{It(a)}catch(i){throw Z(a),i}else t!==null&&qe(a);var o=a;if(n&&o.deps===null&&o.teardown===null&&o.nodes===null&&o.first===o.last&&(o.f&Nt)===0&&(o=o.first,(e&Be)!==0&&(e&Ke)!==0&&o!==null&&(o.f|=Ke)),o!==null&&(o.parent=r,r!==null&&Au(o,r),E!==null&&(E.f&K)!==0&&(e&pt)===0)){var s=E;(s.effects??(s.effects=[])).push(o)}return a}function $r(){return E!==null&&!Ae}function Lr(e){const t=xe(Bn,null,!1);return L(t,j),t.teardown=e,t}function Eu(e){qu("$effect"),y&&ht(e,"name",{value:"$effect"});var t=F.f,n=!E&&(t&Me)!==0&&(t&_t)===0;if(n){var r=$;(r.e??(r.e=[])).push(e)}else return Ro(e)}function Ro(e){return xe(an|pl,e,!1)}function Cu(e){et.ensure();const t=xe(pt|Nt,e,!0);return(n={})=>new Promise(r=>{n.outro?yt(t,()=>{Z(t),r(void 0)}):(Z(t),r(void 0))})}function Do(e){return xe(an,e,!1)}function Pu(e){return xe(Vn|Nt,e,!0)}function Fu(e,t=0){return xe(Bn|t,e,!0)}function Un(e,t=[],n=[],r=[]){wo(r,t,n,a=>{xe(Bn,()=>e(...a.map(x)),!0)})}function dn(e,t=0){var n=xe(Be|t,e,!0);return y&&(n.dev_stack=Tt),n}function $o(e,t=0){var n=xe(wr|t,e,!0);return y&&(n.dev_stack=Tt),n}function oe(e){return xe(Me|Nt,e,!0)}function Lo(e){var t=e.teardown;if(t!==null){const n=ot,r=E;Vo(!0),ve(null);try{t.call(null)}finally{Vo(n),ve(r)}}}function Or(e,t=!1){var n=e.first;for(e.first=e.last=null;n!==null;){const a=n.ac;a!==null&&Dr(()=>{a.abort(mt)});var r=n.next;(n.f&pt)!==0?n.parent=null:Z(n,t),n=r}}function Nu(e){for(var t=e.first;t!==null;){var n=t.next;(t.f&Me)===0&&Z(t),t=n}}function Z(e,t=!0){var n=!1;(t||(e.f&eo)!==0)&&e.nodes!==null&&e.nodes.end!==null&&(xu(e.nodes.start,e.nodes.end),n=!0),Or(e,t&&!n),pn(e,0),L(e,Ge);var r=e.nodes&&e.nodes.t;if(r!==null)for(const o of r)o.stop();Lo(e);var a=e.parent;a!==null&&a.first!==null&&Oo(e),y&&(e.component_function=null),e.next=e.prev=e.teardown=e.ctx=e.deps=e.fn=e.nodes=e.ac=null}function xu(e,t){for(;e!==null;){var n=e===t?null:fn(e);e.remove(),e=n}}function Oo(e){var t=e.parent,n=e.prev,r=e.next;n!==null&&(n.next=r),r!==null&&(r.prev=n),t!==null&&(t.first===e&&(t.first=r),t.last===e&&(t.last=n))}function yt(e,t,n=!0){var r=[];Io(e,r,!0);var a=()=>{n&&Z(e),t&&t()},o=r.length;if(o>0){var s=()=>--o||a();for(var i of r)i.out(s)}else a()}function Io(e,t,n){if((e.f&ue)===0){e.f^=ue;var r=e.nodes&&e.nodes.t;if(r!==null)for(const i of r)(i.is_global||n)&&t.push(i);for(var a=e.first;a!==null;){var o=a.next,s=(a.f&Ke)!==0||(a.f&Me)!==0&&(e.f&Be)!==0;Io(a,t,s?n:!1),a=o}}}function Ir(e){Bo(e,!0)}function Bo(e,t){if((e.f&ue)!==0){e.f^=ue,(e.f&j)===0&&(L(e,X),qe(e));for(var n=e.first;n!==null;){var r=n.next,a=(n.f&Ke)!==0||(n.f&Me)!==0;Bo(n,a?t:!1),n=r}var o=e.nodes&&e.nodes.t;if(o!==null)for(const s of o)(s.is_global||t)&&s.in()}}function Go(e,t){if(e.nodes)for(var n=e.nodes.start,r=e.nodes.end;n!==null;){var a=n===r?null:fn(n);t.append(n),n=a}}let Kn=!1,ot=!1;function Vo(e){ot=e}let E=null,Ae=!1;function ve(e){E=e}let F=null;function Ee(e){F=e}let ge=null;function jo(e){E!==null&&(ge===null?ge=[e]:ge.push(e))}let se=null,ce=0,ye=null;function Tu(e){ye=e}let Ho=1,bt=0,wt=bt;function Wo(e){wt=e}function Uo(){return++Ho}function hn(e){var t=e.f;if((t&X)!==0)return!0;if(t&K&&(e.f&=~Ye),(t&ke)!==0){for(var n=e.deps,r=n.length,a=0;a<r;a++){var o=n[a];if(hn(o)&&So(o),o.wv>e.wv)return!0}(t&_e)!==0&&Y===null&&L(e,j)}return!1}function Ko(e,t,n=!0){var r=e.reactions;if(r!==null&&!(ge!==null&&dt.call(ge,e)))for(var a=0;a<r.length;a++){var o=r[a];(o.f&K)!==0?Ko(o,t,!1):t===o&&(n?L(o,X):(o.f&j)!==0&&L(o,ke),qe(o))}}function Br(e){var v;var t=se,n=ce,r=ye,a=E,o=ge,s=$,i=Ae,l=wt,c=e.f;se=null,ce=0,ye=null,E=(c&(Me|pt))===0?e:null,ge=null,xt(e.ctx),Ae=!1,wt=++bt,e.ac!==null&&(Dr(()=>{e.ac.abort(mt)}),e.ac=null);try{e.f|=kr;var p=e.fn,u=p();e.f|=_t;var d=e.deps,m=N==null?void 0:N.is_fork;if(se!==null){var f;if(m||pn(e,ce),d!==null&&ce>0)for(d.length=ce+se.length,f=0;f<se.length;f++)d[ce+f]=se[f];else e.deps=d=se;if($r()&&(e.f&_e)!==0)for(f=ce;f<d.length;f++)((v=d[f]).reactions??(v.reactions=[])).push(e)}else!m&&d!==null&&ce<d.length&&(pn(e,ce),d.length=ce);if(fo()&&ye!==null&&!Ae&&d!==null&&(e.f&(K|ke|X))===0)for(f=0;f<ye.length;f++)Ko(ye[f],e);if(a!==null&&a!==e){if(bt++,a.deps!==null)for(let w=0;w<n;w+=1)a.deps[w].rv=bt;if(t!==null)for(const w of t)w.rv=bt;ye!==null&&(r===null?r=ye:r.push(...ye))}return(e.f&Qe)!==0&&(e.f^=Qe),u}catch(w){return ho(w)}finally{e.f^=kr,se=t,ce=n,ye=r,E=a,ge=o,xt(s),Ae=i,wt=l}}function Ru(e,t){let n=t.reactions;if(n!==null){var r=ll.call(n,e);if(r!==-1){var a=n.length-1;a===0?n=t.reactions=null:(n[r]=n[a],n.pop())}}if(n===null&&(t.f&K)!==0&&(se===null||!dt.call(se,t))){var o=t;(o.f&_e)!==0&&(o.f^=_e,o.f&=~Ye),Ar(o),pu(o),pn(o,0)}}function pn(e,t){var n=e.deps;if(n!==null)for(var r=t;r<n.length;r++)Ru(e,n[r])}function It(e){var t=e.f;if((t&Ge)===0){L(e,j);var n=F,r=Kn;if(F=e,Kn=!0,y){var a=ln;co(e.component_function);var o=Tt;jn(e.dev_stack??Tt)}try{(t&(Be|wr))!==0?Nu(e):Or(e),Lo(e);var s=Br(e);e.teardown=typeof s=="function"?s:null,e.wv=Ho;var i;y&&Xl&&(e.f&X)!==0&&e.deps}finally{Kn=r,F=n,y&&(co(a),jn(o))}}}function x(e){var t=e.f,n=(t&K)!==0;if(E!==null&&!Ae){var r=F!==null&&(F.f&Ge)!==0;if(!r&&(ge===null||!dt.call(ge,e))){var a=E.deps;if((E.f&kr)!==0)e.rv<bt&&(e.rv=bt,se===null&&a!==null&&a[ce]===e?ce++:se===null?se=[e]:se.push(e));else{(E.deps??(E.deps=[])).push(e);var o=e.reactions;o===null?e.reactions=[E]:dt.call(o,E)||o.push(E)}}}if(y&&fu.delete(e),ot&&tt.has(e))return tt.get(e);if(n){var s=e;if(ot){var i=s.v;return((s.f&j)===0&&s.reactions!==null||Yo(s))&&(i=xr(s)),tt.set(s,i),i}var l=(s.f&_e)===0&&!Ae&&E!==null&&(Kn||(E.f&_e)!==0),c=(s.f&_t)===0;hn(s)&&(l&&(s.f|=_e),So(s)),l&&!c&&(qo(s),Xo(s))}if(Y!=null&&Y.has(e))return Y.get(e);if((e.f&Qe)!==0)throw e.v;return e.v}function Xo(e){if(e.f|=_e,e.deps!==null)for(const t of e.deps)(t.reactions??(t.reactions=[])).push(e),(t.f&K)!==0&&(t.f&_e)===0&&(qo(t),Xo(t))}function Yo(e){if(e.v===H)return!0;if(e.deps===null)return!1;for(const t of e.deps)if(tt.has(t)||(t.f&K)!==0&&Yo(t))return!0;return!1}function Gr(e){var t=Ae;try{return Ae=!0,e()}finally{Ae=t}}function Du(e){return e.endsWith("capture")&&e!=="gotpointercapture"&&e!=="lostpointercapture"}const $u=["beforeinput","click","change","dblclick","contextmenu","focusin","focusout","input","keydown","keyup","mousedown","mousemove","mouseout","mouseover","mouseup","pointerdown","pointermove","pointerout","pointerover","pointerup","touchend","touchmove","touchstart"];function Lu(e){return $u.includes(e)}const Ou={formnovalidate:"formNoValidate",ismap:"isMap",nomodule:"noModule",playsinline:"playsInline",readonly:"readOnly",defaultvalue:"defaultValue",defaultchecked:"defaultChecked",srcobject:"srcObject",novalidate:"noValidate",allowfullscreen:"allowFullscreen",disablepictureinpicture:"disablePictureInPicture",disableremoteplayback:"disableRemotePlayback"};function Iu(e){return e=e.toLowerCase(),Ou[e]??e}const Bu=["touchstart","touchmove"];function Gu(e){return Bu.includes(e)}const Mt=Symbol("events"),Qo=new Set,Vr=new Set;function Vu(e,t,n,r={}){function a(o){if(r.capture||jr.call(t,o),!o.cancelBubble)return Dr(()=>n==null?void 0:n.call(this,o))}return e.startsWith("pointer")||e.startsWith("touch")||e==="wheel"?Je(()=>{t.addEventListener(e,a,r)}):t.addEventListener(e,a,r),a}function _n(e,t,n){(t[Mt]??(t[Mt]={}))[e]=n}function Zo(e){for(var t=0;t<e.length;t++)Qo.add(e[t]);for(var n of Vr)n(e)}let Jo=null;function jr(e){var w,g;var t=this,n=t.ownerDocument,r=e.type,a=((w=e.composedPath)==null?void 0:w.call(e))||[],o=a[0]||e.target;Jo=e;var s=0,i=Jo===e&&e[Mt];if(i){var l=a.indexOf(i);if(l!==-1&&(t===document||t===window)){e[Mt]=t;return}var c=a.indexOf(t);if(c===-1)return;l<=c&&(s=l)}if(o=a[s]||e.target,o!==t){ht(e,"currentTarget",{configurable:!0,get(){return o||n}});var p=E,u=F;ve(null),Ee(null);try{for(var d,m=[];o!==null;){var f=o.assignedSlot||o.parentNode||o.host||null;try{var v=(g=o[Mt])==null?void 0:g[r];v!=null&&(!o.disabled||e.target===o)&&v.call(o,e)}catch(S){d?m.push(S):d=S}if(e.cancelBubble||f===t||f===null)break;o=f}if(d){for(let S of m)queueMicrotask(()=>{throw S});throw d}}finally{e[Mt]=t,delete e.currentTarget,ve(p),Ee(u)}}}const Hr=((ks=globalThis==null?void 0:globalThis.window)==null?void 0:ks.trustedTypes)&&globalThis.window.trustedTypes.createPolicy("svelte-trusted-html",{createHTML:e=>e});function ju(e){return(Hr==null?void 0:Hr.createHTML(e))??e}function zo(e){var t=To("template");return t.innerHTML=ju(e.replaceAll("<!>","<!---->")),t.content}function mn(e,t){var n=F;n.nodes===null&&(n.nodes={start:e,end:t,a:null,t:null})}function Xn(e,t){var n=(t&Ol)!==0,r=(t&Il)!==0,a,o=!e.startsWith("<!>");return()=>{a===void 0&&(a=zo(o?e:"<!>"+e),n||(a=Ot(a)));var s=r||Rr?document.importNode(a,!0):a.cloneNode(!0);if(n){var i=Ot(s),l=s.lastChild;mn(i,l)}else mn(s,s);return s}}function Hu(e,t,n="svg"){var r=!e.startsWith("<!>"),a=`<${n}>${r?e:"<!>"+e}</${n}>`,o;return()=>{if(!o){var s=zo(a),i=Ot(s);o=Ot(i)}var l=o.cloneNode(!0);return mn(l,l),l}}function Wu(e,t){return Hu(e,t,"svg")}function ee(){var e=document.createDocumentFragment(),t=document.createComment(""),n=at();return e.append(t,n),mn(t,n),e}function O(e,t){e!==null&&e.before(t)}function Uu(e,t){var n=t==null?"":typeof t=="object"?`${t}`:t;n!==(e.__t??(e.__t=e.nodeValue))&&(e.__t=n,e.nodeValue=`${n}`)}function Ku(e,t){return Xu(e,t)}const Yn=new Map;function Xu(e,{target:t,anchor:n,props:r={},events:a,context:o,intro:s=!0,transformError:i}){Mu();var l=void 0,c=Cu(()=>{var p=n??t.appendChild(at());iu(p,{pending:()=>{}},m=>{B({});var f=$;o&&(f.c=o),a&&(r.$$events=a),l=e(m,r)||{},G()},i);var u=new Set,d=m=>{for(var f=0;f<m.length;f++){var v=m[f];if(!u.has(v)){u.add(v);var w=Gu(v);for(const b of[t,document]){var g=Yn.get(b);g===void 0&&(g=new Map,Yn.set(b,g));var S=g.get(v);S===void 0?(b.addEventListener(v,jr,{passive:w}),g.set(v,1)):g.set(v,S+1)}}}};return d(In(Qo)),Vr.add(d),()=>{var w;for(var m of u)for(const g of[t,document]){var f=Yn.get(g),v=f.get(m);--v==0?(g.removeEventListener(m,jr),f.delete(m),f.size===0&&Yn.delete(g)):f.set(m,v)}Vr.delete(d),p!==n&&((w=p.parentNode)==null||w.removeChild(p))}});return Wr.set(l,c),l}let Wr=new WeakMap;function es(e,t){const n=Wr.get(e);return n?(Wr.delete(e),n(t)):(y&&(Ze in e?Wl():jl()),Promise.resolve())}class Ur{constructor(t,n=!0){Le(this,"anchor");P(this,Pe,new Map);P(this,$e,new Map);P(this,he,new Map);P(this,Et,new Set);P(this,Sn,!0);P(this,qn,()=>{var t=N;if(h(this,Pe).has(t)){var n=h(this,Pe).get(t),r=h(this,$e).get(n);if(r)Ir(r),h(this,Et).delete(n);else{var a=h(this,he).get(n);a&&(h(this,$e).set(n,a.effect),h(this,he).delete(n),a.fragment.lastChild.remove(),this.anchor.before(a.fragment),r=a.effect)}for(const[o,s]of h(this,Pe)){if(h(this,Pe).delete(o),o===t)break;const i=h(this,he).get(s);i&&(Z(i.effect),h(this,he).delete(s))}for(const[o,s]of h(this,$e)){if(o===n||h(this,Et).has(o))continue;const i=()=>{if(Array.from(h(this,Pe).values()).includes(o)){var c=document.createDocumentFragment();Go(s,c),c.append(at()),h(this,he).set(o,{effect:s,fragment:c})}else Z(s);h(this,Et).delete(o),h(this,$e).delete(o)};h(this,Sn)||!r?(h(this,Et).add(o),yt(s,i,!1)):i()}}});P(this,Jn,t=>{h(this,Pe).delete(t);const n=Array.from(h(this,Pe).values());for(const[r,a]of h(this,he))n.includes(r)||(Z(a.effect),h(this,he).delete(r))});this.anchor=t,A(this,Sn,n)}ensure(t,n){var r=N,a=xo();if(n&&!h(this,$e).has(t)&&!h(this,he).has(t))if(a){var o=document.createDocumentFragment(),s=at();o.append(s),h(this,he).set(t,{effect:oe(()=>n(s)),fragment:o})}else h(this,$e).set(t,oe(()=>n(this.anchor)));if(h(this,Pe).set(r,t),a){for(const[i,l]of h(this,$e))i===t?r.unskip_effect(l):r.skip_effect(l);for(const[i,l]of h(this,he))i===t?r.unskip_effect(l.effect):r.skip_effect(l.effect);r.oncommit(h(this,qn)),r.ondiscard(h(this,Jn))}else h(this,qn).call(this)}}Pe=new WeakMap,$e=new WeakMap,he=new WeakMap,Et=new WeakMap,Sn=new WeakMap,qn=new WeakMap,Jn=new WeakMap;function Kr(e,t,n=!1){var r=new Ur(e),a=n?Ke:0;function o(s,i){r.ensure(s,i)}dn(()=>{var s=!1;t((i,l=0)=>{s=!0,o(l,i)}),s||o(!1,null)},a)}function Yu(e,t){return t}function Qu(e,t,n){for(var r=[],a=t.length,o,s=t.length,i=0;i<a;i++){let u=t[i];yt(u,()=>{if(o){if(o.pending.delete(u),o.done.add(u),o.pending.size===0){var d=e.outrogroups;Xr(In(o.done)),d.delete(o),d.size===0&&(e.outrogroups=null)}}else s-=1},!1)}if(s===0){var l=r.length===0&&n!==null;if(l){var c=n,p=c.parentNode;ku(p),p.append(c),e.items.clear()}Xr(t,!l)}else o={pending:new Set(t),done:new Set},(e.outrogroups??(e.outrogroups=new Set)).add(o)}function Xr(e,t=!0){for(var n=0;n<e.length;n++)Z(e[n],t)}var ts;function ns(e,t,n,r,a,o=null){var s=e,i=new Map,l=null,c=Mo(()=>{var v=n();return br(v)?v:v==null?[]:In(v)}),p,u=!0;function d(){f.fallback=l,Zu(f,p,s,t,r),l!==null&&(p.length===0?(l.f&Xe)===0?Ir(l):(l.f^=Xe,gn(l,null,s)):yt(l,()=>{l=null}))}var m=dn(()=>{p=x(c);for(var v=p.length,w=new Set,g=N,S=xo(),b=0;b<v;b+=1){var k=p[b],_=r(k,b);if(y){var J=r(k,b);_!==J&&gl(String(b),String(_),String(J))}var C=u?null:i.get(_);C?(C.v&&$t(C.v,k),C.i&&$t(C.i,b),S&&g.unskip_effect(C.e)):(C=Ju(i,u?s:ts??(ts=at()),k,_,b,a,t,n),u||(C.e.f|=Xe),i.set(_,C)),w.add(_)}if(v===0&&o&&!l&&(u?l=oe(()=>o(s)):(l=oe(()=>o(ts??(ts=at()))),l.f|=Xe)),v>w.size&&(y?zu(p,r):oo("","","")),!u)if(S){for(const[We,pe]of i)w.has(We)||g.skip_effect(pe.e);g.oncommit(d),g.ondiscard(()=>{})}else d();x(c)}),f={effect:m,items:i,outrogroups:null,fallback:l};u=!1}function vn(e){for(;e!==null&&(e.f&Me)===0;)e=e.next;return e}function Zu(e,t,n,r,a){var We;var o=t.length,s=e.items,i=vn(e.effect.first),l,c=null,p=[],u=[],d,m,f,v;for(v=0;v<o;v+=1){if(d=t[v],m=a(d,v),f=s.get(m).e,e.outrogroups!==null)for(const pe of e.outrogroups)pe.pending.delete(f),pe.done.delete(f);if((f.f&Xe)!==0)if(f.f^=Xe,f===i)gn(f,null,n);else{var w=c?c.next:i;f===e.effect.last&&(e.effect.last=f.prev),f.prev&&(f.prev.next=f.next),f.next&&(f.next.prev=f.prev),st(e,c,f),st(e,f,w),gn(f,w,n),c=f,p=[],u=[],i=vn(c.next);continue}if((f.f&ue)!==0&&Ir(f),f!==i){if(l!==void 0&&l.has(f)){if(p.length<u.length){var g=u[0],S;c=g.prev;var b=p[0],k=p[p.length-1];for(S=0;S<p.length;S+=1)gn(p[S],g,n);for(S=0;S<u.length;S+=1)l.delete(u[S]);st(e,b.prev,k.next),st(e,c,b),st(e,k,g),i=g,c=k,v-=1,p=[],u=[]}else l.delete(f),gn(f,i,n),st(e,f.prev,f.next),st(e,f,c===null?e.effect.first:c.next),st(e,c,f),c=f;continue}for(p=[],u=[];i!==null&&i!==f;)(l??(l=new Set)).add(i),u.push(i),i=vn(i.next);if(i===null)continue}(f.f&Xe)===0&&p.push(f),c=f,i=vn(f.next)}if(e.outrogroups!==null){for(const pe of e.outrogroups)pe.pending.size===0&&(Xr(In(pe.done)),(We=e.outrogroups)==null||We.delete(pe));e.outrogroups.size===0&&(e.outrogroups=null)}if(i!==null||l!==void 0){var _=[];if(l!==void 0)for(f of l)(f.f&ue)===0&&_.push(f);for(;i!==null;)(i.f&ue)===0&&i!==e.fallback&&_.push(i),i=vn(i.next);var J=_.length;if(J>0){var C=null;Qu(e,_,C)}}}function Ju(e,t,n,r,a,o,s,i){var l=(s&Nl)!==0?(s&Tl)===0?mu(n,!1,!1):vt(n):null,c=(s&xl)!==0?vt(a):null;return y&&l&&(l.trace=()=>{i()[(c==null?void 0:c.v)??a]}),{v:l,i:c,e:oe(()=>(o(t,l??n,c??a,i),()=>{e.delete(r)}))}}function gn(e,t,n){if(e.nodes)for(var r=e.nodes.start,a=e.nodes.end,o=t&&(t.f&Xe)===0?t.nodes.start:n;r!==null;){var s=fn(r);if(o.before(r),r===a)return;r=s}}function st(e,t,n){t===null?e.effect.first=n:t.next=n,n===null?e.effect.last=t:n.prev=t}function zu(e,t){const n=new Map,r=e.length;for(let a=0;a<r;a++){const o=t(e[a],a);if(n.has(o)){const s=String(n.get(o)),i=String(a);let l=String(o);l.startsWith("[object ")&&(l=null),oo(s,i,l)}n.set(o,a)}}function te(e,t,...n){var r=new Ur(e);dn(()=>{const a=t()??null;y&&a==null&&kl(),r.ensure(a,a&&(o=>a(o,...n)))},Ke)}function ec(e,t,n,r,a,o){var s=null,i=e,l=new Ur(i,!1);dn(()=>{const c=t()||null;var p=Gl;if(c===null){l.ensure(null,null);return}return l.ensure(c,u=>{if(c){if(s=To(c,p),mn(s,s),r){var d=s.appendChild(at());r(s,d)}F.nodes.end=s,u.before(s)}}),()=>{}},Ke),Lr(()=>{})}function tc(e,t){var n=void 0,r;$o(()=>{n!==(n=t())&&(r&&(Z(r),r=null),n&&(r=oe(()=>{Do(()=>n(e))})))})}function rs(e){var t,n,r="";if(typeof e=="string"||typeof e=="number")r+=e;else if(typeof e=="object")if(Array.isArray(e)){var a=e.length;for(t=0;t<a;t++)e[t]&&(n=rs(e[t]))&&(r&&(r+=" "),r+=n)}else for(n in e)e[n]&&(r&&(r+=" "),r+=n);return r}function nc(){for(var e,t,n=0,r="",a=arguments.length;n<a;n++)(e=arguments[n])&&(t=rs(e))&&(r&&(r+=" "),r+=t);return r}function as(e){return typeof e=="object"?nc(e):e??""}const os=[...` 	
\r\f \v\uFEFF`];function rc(e,t,n){var r=e==null?"":""+e;if(n){for(var a of Object.keys(n))if(n[a])r=r?r+" "+a:a;else if(r.length)for(var o=a.length,s=0;(s=r.indexOf(a,s))>=0;){var i=s+o;(s===0||os.includes(r[s-1]))&&(i===r.length||os.includes(r[i]))?r=(s===0?"":r.substring(0,s))+r.substring(i+1):s=i}}return r===""?null:r}function ss(e,t=!1){var n=t?" !important;":";",r="";for(var a of Object.keys(e)){var o=e[a];o!=null&&o!==""&&(r+=" "+a+": "+o+n)}return r}function Yr(e){return e[0]!=="-"||e[1]!=="-"?e.toLowerCase():e}function ac(e,t){if(t){var n="",r,a;if(Array.isArray(t)?(r=t[0],a=t[1]):r=t,e){e=String(e).replaceAll(/\s*\/\*.*?\*\/\s*/g,"").trim();var o=!1,s=0,i=!1,l=[];r&&l.push(...Object.keys(r).map(Yr)),a&&l.push(...Object.keys(a).map(Yr));var c=0,p=-1;const v=e.length;for(var u=0;u<v;u++){var d=e[u];if(i?d==="/"&&e[u-1]==="*"&&(i=!1):o?o===d&&(o=!1):d==="/"&&e[u+1]==="*"?i=!0:d==='"'||d==="'"?o=d:d==="("?s++:d===")"&&s--,!i&&o===!1&&s===0){if(d===":"&&p===-1)p=u;else if(d===";"||u===v-1){if(p!==-1){var m=Yr(e.substring(c,p).trim());if(!l.includes(m)){d!==";"&&u++;var f=e.substring(c,u).trim();n+=" "+f+";"}}c=u+1,p=-1}}}}return r&&(n+=ss(r)),a&&(n+=ss(a,!0)),n=n.trim(),n===""?null:n}return e==null?null:String(e)}function is(e,t,n,r,a,o){var s=e.__className;if(s!==n||s===void 0){var i=rc(n,r,o);i==null?e.removeAttribute("class"):t?e.className=i:e.setAttribute("class",i),e.__className=n}else if(o&&a!==o)for(var l in o){var c=!!o[l];(a==null||c!==!!a[l])&&e.classList.toggle(l,c)}return o}function Qr(e,t={},n,r){for(var a in n){var o=n[a];t[a]!==o&&(n[a]==null?e.style.removeProperty(a):e.style.setProperty(a,o,r))}}function oc(e,t,n,r){var a=e.__style;if(a!==t){var o=ac(t,r);o==null?e.removeAttribute("style"):e.style.cssText=o,e.__style=t}else r&&(Array.isArray(r)?(Qr(e,n==null?void 0:n[0],r[0]),Qr(e,n==null?void 0:n[1],r[1],"important")):Qr(e,n,r));return r}function Zr(e,t,n=!1){if(e.multiple){if(t==null)return;if(!br(t))return Hl();for(var r of e.options)r.selected=t.includes(ls(r));return}for(r of e.options){var a=ls(r);if(gu(a,t)){r.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function sc(e){var t=new MutationObserver(()=>{Zr(e,e.__value)});t.observe(e,{childList:!0,subtree:!0,attributes:!0,attributeFilter:["value"]}),Lr(()=>{t.disconnect()})}function ls(e){return"__value"in e?e.__value:e.value}const yn=Symbol("class"),bn=Symbol("style"),us=Symbol("is custom element"),cs=Symbol("is html"),ic=ro?"option":"OPTION",lc=ro?"select":"SELECT";function uc(e,t){var n=Jr(e);n.checked!==(n.checked=t??void 0)&&(e.checked=t)}function cc(e,t){t?e.hasAttribute("selected")||e.setAttribute("selected",""):e.removeAttribute("selected")}function q(e,t,n,r){var a=Jr(e);a[t]!==(a[t]=n)&&(t==="loading"&&(e[_l]=n),n==null?e.removeAttribute(t):typeof n!="string"&&hs(e).includes(t)?e[t]=n:e.setAttribute(t,n))}function fc(e,t,n,r,a=!1,o=!1){var s=Jr(e),i=s[us],l=!s[cs],c=t||{},p=e.nodeName===ic;for(var u in t)u in n||(n[u]=null);n.class?n.class=as(n.class):n[yn]&&(n.class=null),n[bn]&&(n.style??(n.style=null));var d=hs(e);for(const b in n){let k=n[b];if(p&&b==="value"&&k==null){e.value=e.__value="",c[b]=k;continue}if(b==="class"){var m=e.namespaceURI==="http://www.w3.org/1999/xhtml";is(e,m,k,r,t==null?void 0:t[yn],n[yn]),c[b]=k,c[yn]=n[yn];continue}if(b==="style"){oc(e,k,t==null?void 0:t[bn],n[bn]),c[b]=k,c[bn]=n[bn];continue}var f=c[b];if(!(k===f&&!(k===void 0&&e.hasAttribute(b)))){c[b]=k;var v=b[0]+b[1];if(v!=="$$")if(v==="on"){const _={},J="$$"+b;let C=b.slice(2);var w=Lu(C);if(Du(C)&&(C=C.slice(0,-7),_.capture=!0),!w&&f){if(k!=null)continue;e.removeEventListener(C,c[J],_),c[J]=null}if(w)_n(C,e,k),Zo([C]);else if(k!=null){let We=function(pe){c[b].call(this,pe)};c[J]=Vu(C,e,We,_)}}else if(b==="style")q(e,b,k);else if(b==="autofocus")Su(e,!!k);else if(!i&&(b==="__value"||b==="value"&&k!=null))e.value=e.__value=k;else if(b==="selected"&&p)cc(e,k);else{var g=b;l||(g=Iu(g));var S=g==="defaultValue"||g==="defaultChecked";if(k==null&&!i&&!S)if(s[b]=null,g==="value"||g==="checked"){let _=e;const J=t===void 0;if(g==="value"){let C=_.defaultValue;_.removeAttribute(g),_.defaultValue=C,_.value=_.__value=J?C:null}else{let C=_.defaultChecked;_.removeAttribute(g),_.defaultChecked=C,_.checked=J?C:!1}}else e.removeAttribute(b);else S||d.includes(g)&&(i||typeof k!="string")?(e[g]=k,g in s&&(s[g]=H)):typeof k!="function"&&q(e,g,k)}}}return c}function fs(e,t,n=[],r=[],a=[],o,s=!1,i=!1){wo(a,n,r,l=>{var c=void 0,p={},u=e.nodeName===lc,d=!1;if($o(()=>{var f=t(...l.map(x)),v=fc(e,c,f,o,s,i);d&&u&&"value"in f&&Zr(e,f.value);for(let g of Object.getOwnPropertySymbols(p))f[g]||Z(p[g]);for(let g of Object.getOwnPropertySymbols(f)){var w=f[g];g.description===Vl&&(!c||w!==c[g])&&(p[g]&&Z(p[g]),p[g]=oe(()=>tc(e,()=>w))),v[g]=w}c=v}),u){var m=e;Do(()=>{Zr(m,c.value,!0),sc(m)})}d=!0})}function Jr(e){return e.__attributes??(e.__attributes={[us]:e.nodeName.includes("-"),[cs]:e.namespaceURI===so})}var ds=new Map;function hs(e){var t=e.getAttribute("is")||e.nodeName,n=ds.get(t);if(n)return n;ds.set(t,n=[]);for(var r,a=e,o=Element.prototype;o!==a;){r=ul(a);for(var s in r)r[s].set&&n.push(s);a=Za(a)}return n}let Qn=!1;function dc(e){var t=Qn;try{return Qn=!1,[e(),Qn]}finally{Qn=t}}const hc={get(e,t){if(!e.exclude.includes(t))return e.props[t]},set(e,t){return y&&ql(`${e.name}.${String(t)}`),!1},getOwnPropertyDescriptor(e,t){if(!e.exclude.includes(t)&&t in e.props)return{enumerable:!0,configurable:!0,value:e.props[t]}},has(e,t){return e.exclude.includes(t)?!1:t in e.props},ownKeys(e){return Reflect.ownKeys(e.props).filter(t=>!e.exclude.includes(t))}};function ne(e,t,n){return new Proxy(y?{props:e,exclude:t,name:n,other:{},to_proxy:[]}:{props:e,exclude:t},hc)}const pc={get(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(rn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r)return r[t]}},set(e,t,n){let r=e.props.length;for(;r--;){let a=e.props[r];rn(a)&&(a=a());const o=Ie(a,t);if(o&&o.set)return o.set(n),!0}return!1},getOwnPropertyDescriptor(e,t){let n=e.props.length;for(;n--;){let r=e.props[n];if(rn(r)&&(r=r()),typeof r=="object"&&r!==null&&t in r){const a=Ie(r,t);return a&&!a.configurable&&(a.configurable=!0),a}}},has(e,t){if(t===Ze||t===to)return!1;for(let n of e.props)if(rn(n)&&(n=n()),n!=null&&t in n)return!0;return!1},ownKeys(e){const t=[];for(let n of e.props)if(rn(n)&&(n=n()),!!n){for(const r in n)t.includes(r)||t.push(r);for(const r of Object.getOwnPropertySymbols(n))t.includes(r)||t.push(r)}return t}};function re(...e){return new Proxy({props:e},pc)}function Bt(e,t,n,r){var S;var a=(n&$l)!==0,o=(n&Ll)!==0,s=r,i=!0,l=()=>(i&&(i=!1,s=o?Gr(r):r),s),c;if(a){var p=Ze in e||to in e;c=((S=Ie(e,t))==null?void 0:S.set)??(p&&t in e?b=>e[t]=b:void 0)}var u,d=!1;a?[u,d]=dc(()=>e[t]):u=e[t],u===void 0&&r!==void 0&&(u=l(),c&&(Sl(t),c(u)));var m;if(m=()=>{var b=e[t];return b===void 0?l():(i=!0,b)},(n&Dl)===0)return m;if(c){var f=e.$$legacy;return(function(b,k){return arguments.length>0?((!k||f||d)&&c(k?m():b),b):m()})}var v=!1,w=((n&Rl)!==0?Wn:Mo)(()=>(v=!1,m()));y&&(w.label=t),a&&x(w);var g=F;return(function(b,k){if(arguments.length>0){const _=k?x(w):a?Lt(b):b;return rt(w,_),v=!0,s!==void 0&&(s=_),b}return ot&&v||(g.f&Ge)!==0?w.v:x(w)})}if(y){let e=function(t){if(!(t in globalThis)){let n;Object.defineProperty(globalThis,t,{configurable:!0,get:()=>{if(n!==void 0)return n;Al(t)},set:r=>{n=r}})}};e("$state"),e("$effect"),e("$derived"),e("$inspect"),e("$props"),e("$bindable")}function _c(e){$===null&&ao("onMount"),Eu(()=>{const t=Gr(e);if(typeof t=="function")return t})}const mc="5";typeof window<"u"&&((Ss=window.__svelte??(window.__svelte={})).v??(Ss.v=new Set)).add(mc);/**
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
 */const vc={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const gc=e=>{for(const t in e)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const yc=Symbol("lucide-context"),bc=()=>Zl(yc);var wc=Wu("<svg><!><!></svg>");function ae(e,t){B(t,!0);const n=bc()??{},r=Bt(t,"color",19,()=>n.color??"currentColor"),a=Bt(t,"size",19,()=>n.size??24),o=Bt(t,"strokeWidth",19,()=>n.strokeWidth??2),s=Bt(t,"absoluteStrokeWidth",19,()=>n.absoluteStrokeWidth??!1),i=Bt(t,"iconNode",19,()=>[]),l=ne(t,["$$slots","$$events","$$legacy","name","color","size","strokeWidth","absoluteStrokeWidth","iconNode","children"]),c=Fr(()=>s()?Number(o())*24/Number(a()):o());var p=wc();fs(p,m=>({...vc,...m,...l,width:a(),height:a(),stroke:r(),"stroke-width":x(c),class:["lucide-icon lucide",n.class,t.name&&`lucide-${t.name}`,t.class]}),[()=>!t.children&&!gc(l)&&{"aria-hidden":"true"}]);var u=Ve(p);ns(u,17,i,Yu,(m,f)=>{var v=Fr(()=>hl(x(f),2));let w=()=>x(v)[0],g=()=>x(v)[1];var S=ee(),b=Q(S);ec(b,w,!0,(k,_)=>{fs(k,()=>({...g()}))}),O(m,S)});var d=z(u);te(d,()=>t.children??U),O(e,p),G()}function Mc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];ae(e,re({name:"chart-line"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function kc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 12 18z"}],["path",{d:"M2 6a2 2 0 0 1 3.414-1.414l6 6a2 2 0 0 1 0 2.828l-6 6A2 2 0 0 1 2 18z"}]];ae(e,re({name:"fast-forward"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function Sc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"}]];ae(e,re({name:"folder-open"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function qc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["rect",{x:"14",y:"3",width:"5",height:"18",rx:"1"}],["rect",{x:"5",y:"3",width:"5",height:"18",rx:"1"}]];ae(e,re({name:"pause"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function Ac(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"}]];ae(e,re({name:"play"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function Ec(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"}],["path",{d:"M21 3v5h-5"}],["path",{d:"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"}],["path",{d:"M8 16H3v5"}]];ae(e,re({name:"refresh-cw"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function Cc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M12 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 12 18z"}],["path",{d:"M22 6a2 2 0 0 0-3.414-1.414l-6 6a2 2 0 0 0 0 2.828l6 6A2 2 0 0 0 22 18z"}]];ae(e,re({name:"rewind"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function Pc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["circle",{cx:"6",cy:"6",r:"3"}],["path",{d:"M8.12 8.12 12 12"}],["path",{d:"M20 4 8.12 15.88"}],["circle",{cx:"6",cy:"18",r:"3"}],["path",{d:"M14.8 14.8 20 20"}]];ae(e,re({name:"scissors"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function Fc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"}],["path",{d:"M20 2v4"}],["path",{d:"M22 4h-4"}],["circle",{cx:"4",cy:"20",r:"2"}]];ae(e,re({name:"sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function Nc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M10 2h4"}],["path",{d:"M12 14v-4"}],["path",{d:"M4 13a8 8 0 0 1 8-7 8 8 0 1 1-5.3 14L4 17.6"}],["path",{d:"M9 17H4v5"}]];ae(e,re({name:"timer-reset"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function xc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M9 14 4 9l5-5"}],["path",{d:"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"}]];ae(e,re({name:"undo-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function Tc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}]];ae(e,re({name:"volume-1"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function Rc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["path",{d:"M16 9a5 5 0 0 1 0 6"}],["path",{d:"M19.364 18.364a9 9 0 0 0 0-12.728"}]];ae(e,re({name:"volume-2"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function Dc(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"}],["line",{x1:"22",x2:"16",y1:"9",y2:"15"}],["line",{x1:"16",x2:"22",y1:"9",y2:"15"}]];ae(e,re({name:"volume-x"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}function $c(e,t){B(t,!0);/**
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
 */let n=ne(t,["$$slots","$$events","$$legacy"]);const r=[["path",{d:"m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72"}],["path",{d:"m14 7 3 3"}],["path",{d:"M5 6v4"}],["path",{d:"M19 14v4"}],["path",{d:"M10 2v2"}],["path",{d:"M7 8H3"}],["path",{d:"M21 16h-4"}],["path",{d:"M11 3H9"}]];ae(e,re({name:"wand-sparkles"},()=>n,{get iconNode(){return r},children:(a,o)=>{var s=ee(),i=Q(s);te(i,()=>t.children??U),O(a,s)},$$slots:{default:!0}})),G()}var Lc=Xn('<span aria-hidden="true"><!></span>');function ps(e,t){B(t,!0);const n=Bt(t,"className",3,""),r=Fr(()=>["aqe-button-icon",n()].filter(Boolean).join(" "));var a=Lc(),o=Ve(a);{var s=_=>{Mc(_,{size:14,strokeWidth:2})},i=_=>{kc(_,{size:14,strokeWidth:2})},l=_=>{Sc(_,{size:14,strokeWidth:2})},c=_=>{qc(_,{size:14,strokeWidth:2})},p=_=>{Ac(_,{size:14,strokeWidth:2})},u=_=>{Ec(_,{size:14,strokeWidth:2})},d=_=>{Cc(_,{size:14,strokeWidth:2})},m=_=>{Pc(_,{size:14,strokeWidth:2})},f=_=>{Fc(_,{size:14,strokeWidth:2})},v=_=>{Nc(_,{size:14,strokeWidth:2})},w=_=>{xc(_,{size:14,strokeWidth:2})},g=_=>{Tc(_,{size:14,strokeWidth:2})},S=_=>{Rc(_,{size:14,strokeWidth:2})},b=_=>{Dc(_,{size:14,strokeWidth:2})},k=_=>{$c(_,{size:14,strokeWidth:2})};Kr(o,_=>{t.icon==="chart-line"?_(s):t.icon==="fast-forward"?_(i,1):t.icon==="folder-open"?_(l,2):t.icon==="pause"?_(c,3):t.icon==="play"?_(p,4):t.icon==="refresh-cw"?_(u,5):t.icon==="rewind"?_(d,6):t.icon==="scissors"?_(m,7):t.icon==="sparkles"?_(f,8):t.icon==="timer-reset"?_(v,9):t.icon==="undo-2"?_(w,10):t.icon==="volume-1"?_(g,11):t.icon==="volume-2"?_(S,12):t.icon==="volume-x"?_(b,13):t.icon==="wand-sparkles"&&_(k,14)})}Un(()=>is(a,1,as(x(r)))),O(e,a),G()}var Oc=Xn('<label class="aqe-repeat-toggle" title="Repeat selected region, or the whole graph when no region is selected."><input class="aqe-repeat-checkbox" type="checkbox"/> <span>Repeat</span></label>'),Ic=Xn('<button type="button" class="aqe-button"><!> <!> <span class="aqe-button-label"> </span></button> <!>',1),Bc=Xn('<div class="aqe-controls"><!> <span class="aqe-status"></span> <div class="aqe-visualizer" data-anchor-ms="0" data-cursor-ms="0" data-progress-ms="0" data-graph-active="false" data-graph-busy="false" data-has-track="false" data-playback-state="stopped" data-playback-engine="" data-playback-start-ms="0" data-playback-end-ms="0" data-playback-region-mode="full" data-resume-requires-restart="false" data-selection-active="false" data-selection-start-ms="" data-selection-end-ms="" data-selection-draft-active="false" data-selection-draft-start-ms="" data-selection-draft-end-ms="" hidden=""><audio class="aqe-audio-clock" preload="metadata" hidden=""></audio> <svg class="aqe-visualizer-svg" role="img" aria-label="Audio pitch and intensity visualization"><rect class="aqe-selection" width="0" visibility="hidden"></rect><path class="aqe-intensity" d=""></path><g class="aqe-pitch"></g><g class="aqe-labels"></g><g class="aqe-x-axis"></g><line class="aqe-selection-edge aqe-selection-start" visibility="hidden"></line><line class="aqe-selection-edge aqe-selection-end" visibility="hidden"></line><line class="aqe-cursor"></line></svg> <div class="aqe-visualizer-meta"><span class="aqe-spinner" hidden="" aria-hidden="true"></span> <span class="aqe-cursor-label">0 ms</span> <span class="aqe-visualizer-status"></span></div></div></div>');function Gc(e,t){var b;B(t,!0),_c(()=>{const k=D(t.target.ord);k&&(Di(k),Wi(k),Ii(k))});var n=Bc(),r=Ve(n);ns(r,17,()=>T,k=>k.command,(k,_)=>{var J=Ic(),C=Q(J),We=Ve(C);ps(We,{className:"aqe-button-icon-default",get icon(){return x(_).icon}});var pe=z(We,2);{var lf=Fe=>{ps(Fe,{className:"aqe-button-icon-active",get icon(){return x(_).activeIcon}})};Kr(pe,Fe=>{x(_).activeIcon&&Fe(lf)})}var uf=z(pe,2),cf=Ve(uf),ff=z(C,2);{var df=Fe=>{var As;var qs=Oc(),aa=Ve(qs);uc(aa,((As=window.__AQE_EDITOR_CONFIG__)==null?void 0:As.repeatPlaybackByDefault)===!0),Un(()=>q(aa,"data-testid",`aqe-repeat-${t.target.ord}`)),_n("change",aa,hf=>Gi(t.target.ord,hf.currentTarget.checked)),O(Fe,qs)};Kr(ff,Fe=>{x(_).command==="aqe:play"&&Fe(df)})}Un(Fe=>{q(C,"data-aqe-command",x(_).command),q(C,"data-aqe-button-state",x(_).command==="aqe:play"?"play":x(_).command==="aqe:analyze"?"graph":"default"),q(C,"data-testid",Fe),q(C,"title",x(_).title),Uu(cf,x(_).label)},[()=>An(t.target.ord,x(_).command)]),_n("mousedown",C,Fe=>Fe.preventDefault()),_n("click",C,()=>Ri(x(_).command,t.target.node,t.target.ord)),O(k,J)});var a=z(r,2),o=z(a,2);q(o,"data-repeat-enabled",((b=window.__AQE_EDITOR_CONFIG__)==null?void 0:b.repeatPlaybackByDefault)===!0?"true":"false");var s=Ve(o),i=z(s,2),l=Ve(i),c=z(l),p=z(c),u=z(p,2),d=z(u),m=z(d),f=z(m),v=z(i,2),w=Ve(v),g=z(w,2),S=z(g,2);Un(()=>{q(n,"data-aqe-field-ord",t.target.ord),q(n,"data-aqe-source-filename",t.target.sourceFilename),q(n,"data-testid",`aqe-controls-${t.target.ord}`),q(a,"data-testid",`aqe-status-${t.target.ord}`),q(o,"data-aqe-field-ord",t.target.ord),q(o,"data-testid",`aqe-graph-${t.target.ord}`),q(s,"data-testid",`aqe-audio-clock-${t.target.ord}`),q(i,"data-testid",`aqe-graph-svg-${t.target.ord}`),q(i,"viewBox",`0 0 ${M.width} ${M.height}`),q(l,"data-testid",`aqe-selection-${t.target.ord}`),q(l,"x",M.left),q(l,"y",M.top),q(l,"height",M.height-M.top-M.bottom),q(c,"data-testid",`aqe-intensity-${t.target.ord}`),q(p,"data-testid",`aqe-pitch-${t.target.ord}`),q(u,"data-testid",`aqe-x-axis-${t.target.ord}`),q(d,"data-testid",`aqe-selection-start-${t.target.ord}`),q(d,"x1",M.left),q(d,"x2",M.left),q(d,"y1",M.top),q(d,"y2",M.height-M.bottom),q(m,"data-testid",`aqe-selection-end-${t.target.ord}`),q(m,"x1",M.left),q(m,"x2",M.left),q(m,"y1",M.top),q(m,"y2",M.height-M.bottom),q(f,"data-testid",`aqe-cursor-${t.target.ord}`),q(f,"x1",M.left),q(f,"x2",M.left),q(f,"y1",M.top),q(f,"y2",M.height-M.bottom),q(w,"data-testid",`aqe-graph-spinner-${t.target.ord}`),q(g,"data-testid",`aqe-progress-label-${t.target.ord}`),q(S,"data-testid",`aqe-graph-status-${t.target.ord}`)}),_n("pointerdown",i,k=>Yi(k,t.target.ord)),O(e,n),G()}Zo(["mousedown","click","change","pointerdown"]);const Gt=new Map;function Vc(e){const t=Gt.get(e.ord);if(t){if(document.body.contains(t.host)||_s(e,t.host),zr(e.ord,t.host),!e.sourceFilename||t.sourceFilename===e.sourceFilename)return t;const o=D(e.ord);if((o==null?void 0:o.dataset.graphBusy)==="true"||(o==null?void 0:o.dataset.hasTrack)==="true"){const s=o.dataset.sourceFilename||e.sourceFilename;t.sourceFilename=s;const i=document.querySelector(`.aqe-controls[data-aqe-field-ord="${e.ord}"]`);return i&&(i.dataset.aqeSourceFilename=s),zr(e.ord,t.host),t}}jc(e.ord);const n=document.createElement("div");n.className="aqe-mount-host",_s(e,n);const a={component:Ku(Gc,{target:n,props:{target:e}}),host:n,ord:e.ord,sourceFilename:e.sourceFilename};return Gt.set(e.ord,a),zr(e.ord,n),a}function jc(e){const t=Gt.get(e);t&&(es(t.component),t.host.remove(),Gt.delete(e)),document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>n.remove())}function Hc(){for(const e of Gt.values())es(e.component),e.host.remove();Gt.clear(),Wc()}function _s(e,t){const n=e.node.closest(".field-container")||e.node.closest(".field")||e.node.parentElement||e.node;n.parentElement?n.after(t):e.node.after(t)}function zr(e,t){document.querySelectorAll(`.aqe-controls[data-aqe-field-ord="${e}"]`).forEach(n=>{t.contains(n)||n.remove()}),document.querySelectorAll(".aqe-mount-host").forEach(n=>{n!==t&&!n.querySelector(".aqe-controls")&&n.remove()})}function Wc(){document.querySelectorAll(".aqe-mount-host").forEach(e=>e.remove()),document.querySelectorAll(".aqe-controls").forEach(e=>e.remove())}function Uc(){window.__aqeGraphStateForTest=Qc,window.__aqeInstallAudioPlaybackTestDriverForTest=Kc,window.__aqeSetCursorByClientXForTest=Yc,window.__aqeSetCursorForTest=Xc}function Kc(e){const t=D(e),n=we(t);return!t||!n?!1:(n.__aqeTestDriverInstalled=!0,n.pause=function(){n.__aqeTestPlaying=!1,n.__aqeTestFrame&&(window.cancelAnimationFrame(n.__aqeTestFrame),n.__aqeTestFrame=null)},n.play=function(){n.__aqeTestPlaying=!0,n.__aqeTestLastNow=performance.now();const a=()=>{if(!n.__aqeTestPlaying)return;const o=performance.now(),s=Number(t.dataset.durationMs||"0")/1e3,i=Math.max(0,(o-Number(n.__aqeTestLastNow||o))/1e3);if(n.__aqeTestLastNow=o,n.currentTime=Math.min(s,(Number(n.currentTime)||0)+i),s&&n.currentTime>=s){n.__aqeTestPlaying=!1,n.dispatchEvent(new Event("ended"));return}n.__aqeTestFrame=window.requestAnimationFrame(a)};return n.__aqeTestFrame=window.requestAnimationFrame(a),Promise.resolve()},!0)}function Xc(e,t,n){const r=D(e);return r?(r.hidden=!1,r.dataset.graphActive="true",ct(r,t,!!n),!0):!1}function Yc(e,t,n){var i;const r=D(e),a=(r==null?void 0:r.querySelector(".aqe-visualizer-svg"))??null;if(!r||!a)return null;const o=Number(r.dataset.durationMs||"0"),s=zt({clientX:t},a,o);return ct(r,s,!!n),{cursorMs:Number(r.dataset.cursorMs||"0"),cursorX:Number(((i=r.querySelector(".aqe-cursor"))==null?void 0:i.getAttribute("x1"))||"0"),bounds:Pa(a)}}function Qc(e){var l,c,p,u;const t=D(e),n=da(e),r=ha(e);if(!t)return null;const a=En().flatMap(d=>Array.from(d.querySelectorAll(".aqe-button-icon svg"))),o=we(t),s=Ga(t),i=Va(t);return{active:t.dataset.graphActive==="true",busy:t.dataset.graphBusy==="true",hidden:!!t.hidden,hasTrack:t.dataset.hasTrack==="true",durationMs:Number(t.dataset.durationMs||"0"),anchorMs:Number(t.dataset.anchorMs||"0"),cursorMs:Number(t.dataset.cursorMs||"0"),progressMs:Number(t.dataset.progressMs||"0"),sourceFilename:t.dataset.sourceFilename||"",graphButtonLabel:ms(n),graphButtonState:(n==null?void 0:n.dataset.aqeButtonState)||"",playButtonLabel:ms(r),playButtonState:(r==null?void 0:r.dataset.aqeButtonState)||"",playbackState:Zc(t),selectionActive:s!==null,selectionStartMs:(s==null?void 0:s.startMs)??null,selectionEndMs:(s==null?void 0:s.endMs)??null,selectionDraftActive:i!==null,selectionDraftStartMs:(i==null?void 0:i.startMs)??null,selectionDraftEndMs:(i==null?void 0:i.endMs)??null,repeatEnabled:t.dataset.repeatEnabled==="true",repeatCheckboxDisabled:!!((l=pa(e))!=null&&l.disabled),playbackStartMs:Number(t.dataset.playbackStartMs||"0"),playbackEndMs:Number(t.dataset.playbackEndMs||"0"),playbackRegionMode:t.dataset.playbackRegionMode==="selection"?"selection":"full",resumeRequiresRestart:t.dataset.resumeRequiresRestart==="true",audioClockSrc:o&&o.getAttribute("src")||"",audioClockCurrentMs:o?Math.round((Number(o.currentTime)||0)*1e3):0,audioClockReady:!!(o&&t.__aqeAudioClockAvailable),audioClockFallback:!!t.__aqeAudioClockFallback,audioClockMuted:!!(o&&o.muted),audioPlaybackTestDriver:!!(o&&o.__aqeTestDriverInstalled),playbackEngine:nn(t),progressClockMode:Jc(t),xAxisLabels:Array.from(t.querySelectorAll(".aqe-x-label")).map(d=>d.textContent||""),pitchPaths:t.querySelectorAll(".aqe-pitch-path").length,intensity:((c=t.querySelector(".aqe-intensity"))==null?void 0:c.getAttribute("d"))||"",cursorX:Number(((p=t.querySelector(".aqe-cursor"))==null?void 0:p.getAttribute("x1"))||"0"),spinnerVisible:t.querySelector(".aqe-spinner")?!((u=t.querySelector(".aqe-spinner"))!=null&&u.hidden):!1,allButtonsDisabled:En().every(d=>d.disabled),anyButtonDisabled:En().some(d=>d.disabled),buttonIconCount:a.length,buttonIconStrokeValues:a.map(d=>d.getAttribute("stroke")||getComputedStyle(d).stroke||"")}}function Zc(e){const t=e.dataset.playbackState;return ba(t)?t:"stopped"}function Jc(e){const t=e.dataset.progressClockMode;return t==="audio"||t==="manual"||t==="stopped"?t:"stopped"}function ms(e){var t;return((t=e==null?void 0:e.querySelector(".aqe-button-label"))==null?void 0:t.textContent)||(e==null?void 0:e.textContent)||""}function zc(){window.__aqeSetBusy=Ln,window.__aqeSetStatus=Ba,window.__aqeSetVisualizer=Zi,window.__aqeSetVisualizerStatus=Ji,window.__aqeResetGraphAfterEdit=Qi,window.__aqeSetPlaybackState=rl,window.__aqeGetPlaybackRequest=al,window.__aqeStopEditorPlayback=ol,window.__aqeGetCursorMs=sl,window.__aqeGetCursorIntent=il,window.__aqePrepareForNewNote=Ha,window.__aqePopFrontendLog=xs,Uc()}const ef=/\[sound:([^\]]+)\]/i,tf=/\.(mp3|wav|ogg)$/i;let wn=[];function nf(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){vs(),window.__AQE_EDITOR_CONFIG__=e,zc(),Ha(),Ks(),window.__aqeEditorDispose=vs,le.info("editor runtime initialized",{audioFieldIndices:e.audioFieldIndices,showGraphByDefault:e.showGraphByDefault===!0});const t=()=>rf(e);window.__aqeScan=t,ta(t,0),ta(t,250),ta(t,1e3)}function vs(){wn.forEach(e=>window.clearTimeout(e)),wn=[],Hc()}function rf(e=window.__AQE_EDITOR_CONFIG__??{audioFieldIndices:[]}){if(e.audioFieldIndices.length){const r=of(e.audioFieldIndices,e.audioFieldSources);r.forEach(a=>gs(a)),le.debug("scan mounted explicit fields",{count:r.length}),mr(),ys(e,r);return}const t=[];let n=0;af().forEach((r,a)=>{const o=ea(r);if(!o)return;const s={node:r,ord:sf(r,a),sourceFilename:o};gs(s),t.push(s),n+=1}),le.debug("scan mounted detected fields",{count:n}),mr(),ys(e,t)}function af(){const e=Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]')),t=new Set;return e.filter(n=>t.has(n)?!1:(t.add(n),!!(n.textContent||n.innerHTML)))}function of(e,t={}){return e.map(n=>{const r=document.querySelector(`.field-container[data-index="${n}"]`);if(!r)return null;const a=r.querySelector('[contenteditable="true"]')||r,o=ea(a)||ea(r)||t[n]||"";return{ord:n,node:a,sourceFilename:o}}).filter(n=>n!==null)}function sf(e,t){const n=["data-field-ord","data-ord","data-index"];for(const a of n){const o=e.getAttribute(a);if(o!==null&&/^\d+$/.test(o))return Number(o)}const r=/(\d+)/.exec(String(e.id||""));return r?Number(r[1]):t}function ea(e){const t=e.innerHTML||e.textContent||"",n=ef.exec(t),r=n==null?void 0:n[1];return r&&tf.test(r)?r:""}function gs(e){Vc(e)}function ys(e,t){e.showGraphByDefault&&Xs(t.map(({ord:n,sourceFilename:r})=>({ord:n,sourceFilename:r})),{anyBusy:()=>document.body.dataset.aqeBusy==="true",requestGraph:On})}function ta(e,t){const n=window.setTimeout(()=>{wn=wn.filter(r=>r!==n),e()},t);wn.push(n)}nf()})();
