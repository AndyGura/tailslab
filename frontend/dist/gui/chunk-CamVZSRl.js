import{$n as ih$1,$r as y0,$t as Ug,An as at$1,Ar as sc$1,B as GI,Bn as fD,Br as vs$1,C as Bo,Cn as Zt$1,Cr as qE,Ct as Nl$1,D as Bw,Dn as _h$1,Dr as rn,Dt as Ow,E as Bu,En as _f$1,Er as rh$1,Et as Op$1,Fr as te$1,G as Hm,H as Gp$1,Hn as gp$1,In as dg,Ir as uD,It as Rh$1,Jn as hw,Jt as Sw,Kn as hD,Kr as xD,Kt as Sp$1,L as Fc$1,Ln as dh$1,Lr as uh$1,Lt as Rl$1,M as Dr,Mr as si$1,Mt as Qg,Nr as sn,O as By,On as _t,Or as rw,P as E0,Pn as ch$1,Pr as td$1,Pt as RD,Q as Io$1,Qn as ic$1,Qt as Ty,R as Fe,Rn as eb,S as Bn$1,T as Bt$1,Tn as _D,Tr as qy,Tt as Og,U as Gt$1,Un as gr,Ur as w0,Ut as SD,Vn as gD,Vt as S,W as HI,Wn as gt$1,Wr as wD,Wt as Sg,X as I0,Xn as ia$1,Xr as xn$1,Xt as T0,Y as I,Yn as iD,Yr as xi$1,Yt as T,Zt as TD,_ as Ay,_t as N,ai as zE,an as Vc$1,ar as le,at as Ku$1,b as Bl$1,bn as Yt$1,bt as Ne$1,c as $t$1,cn as Vp$1,ct as M0,d as AD,dn as Wp$1,dr as mr$1,dt as Ml$1,ei as yh$1,er as ii$1,et as Jg,f as Ac$1,fn as Wy,fr as ms$1,ft as Mo$1,g as Al$1,gn as Y,gr as no$1,gt as Mu$1,h as Ah$1,hn as Xp$1,hr as nh$1,ht as Mt,ii as zD,in as VI,ir as kl$1,it as Kp,j as De,jr as sh$1,jt as Pn$1,k as C0,kn as ae,kr as sE,l as $u,lr as mD,lt as Me$1,mn as Xg,mr as ne,mt as Ms,nn as Up$1,nr as jc$1,nt as K,o as $m$1,on as Vl$1,or as lh$1,ot as LI,p as Ae,pn as XE,pt as Mr,q as Hv,qn as ht$1,qr as xg,qt as Su$1,r as $c$1,ri as z,rn as Uy,rr as kg,rt as Kg,s as $p$1,si as zt$1,sr as lw,st as La$1,t as $,ti as yi,tn as Ul$1,tr as iy,tt as Jp$1,u as $y,un as Wm$1,ur as mh$1,v as Bg,vn as Yg,vr as oa,vt as N0,w as Bp$1,wn as _0,wr as qI,x as Bm$1,xn as Yu$1,xr as q,xt as Ng,y as Bh$1,yt as ND,z as Fv,zn as eh$1,zr as v0,zt as Rw}from"./chunk-6B6O2DWR.js";var al=null;function Xe(){return al}function Ko(n){al??=n}var xi=class{};var $t=(()=>{class n{historyGo(e){throw new Error(``)}static ɵfac=function(t){return new(t||n)};static ɵprov=K({token:n,factory:()=>I(sl),providedIn:`platform`})}return n})();var Dm=new S(``);var sl=(()=>{class n extends $t{_location;_history;_doc=I(Bo);constructor(){super(),this._location=window.location,this._history=window.history}getBaseHrefFromDOM(){return Xe().getBaseHref(this._doc)}onPopState(e){let t=Xe().getGlobalEventTarget(this._doc,`window`);return t.addEventListener(`popstate`,e,!1),()=>t.removeEventListener(`popstate`,e)}onHashChange(e){let t=Xe().getGlobalEventTarget(this._doc,`window`);return t.addEventListener(`hashchange`,e,!1),()=>t.removeEventListener(`hashchange`,e)}get href(){return this._location.href}get protocol(){return this._location.protocol}get hostname(){return this._location.hostname}get port(){return this._location.port}get pathname(){return this._location.pathname}get search(){return this._location.search}get hash(){return this._location.hash}set pathname(e){this._location.pathname=e}pushState(e,t,r){this._history.pushState(e,t,r)}replaceState(e,t,r){this._history.replaceState(e,t,r)}forward(){this._history.forward()}back(){this._history.back()}historyGo(e=0){this._history.go(e)}getState(){return this._history.state}static ɵfac=function(t){return new(t||n)};static ɵprov=K({token:n,factory:()=>new n,providedIn:`platform`})}return n})();function Tr(n,i){return n?i?n.endsWith(`/`)?i.startsWith(`/`)?n+i.slice(1):n+i:i.startsWith(`/`)?n+i:`${n}/${i}`:n:i}function ll(n){let i=n.search(/#|\?|$/);return n[i-1]===`/`?n.slice(0,i-1)+n.slice(i):n}function ct(n){return n&&n[0]!==`?`?`?${n}`:n}var On=(()=>{class n{historyGo(e){throw new Error(``)}static ɵfac=function(t){return new(t||n)};static ɵprov=K({token:n,factory:()=>I(dl),providedIn:`root`})}return n})();var Rr=new S(``);var dl=(()=>{class n extends On{_platformLocation;_baseHref;_removeListenerFns=[];constructor(e,t){super(),this._platformLocation=e,this._baseHref=t??this._platformLocation.getBaseHrefFromDOM()??I(Bo).location?.origin??``}ngOnDestroy(){for(;this._removeListenerFns.length;)this._removeListenerFns.pop()()}onPopState(e){this._removeListenerFns.push(this._platformLocation.onPopState(e),this._platformLocation.onHashChange(e))}getBaseHref(){return this._baseHref}prepareExternalUrl(e){return Tr(this._baseHref,e)}path(e=!1){let t=this._platformLocation.pathname+ct(this._platformLocation.search),r=this._platformLocation.hash;return r&&e?`${t}${r}`:t}pushState(e,t,r,o){let a=this.prepareExternalUrl(r+ct(o));this._platformLocation.pushState(e,t,a)}replaceState(e,t,r,o){let a=this.prepareExternalUrl(r+ct(o));this._platformLocation.replaceState(e,t,a)}forward(){this._platformLocation.forward()}back(){this._platformLocation.back()}getState(){return this._platformLocation.getState()}historyGo(e=0){this._platformLocation.historyGo?.(e)}static ɵfac=function(t){return new(t||n)(ae($t),ae(Rr,8))};static ɵprov=K({token:n,factory:n.ɵfac,providedIn:`root`})}return n})();var Or=(()=>{class n{_subject=new te$1;_basePath;_locationStrategy;_urlChangeListeners=[];_urlChangeSubscription=null;constructor(e){this._locationStrategy=e;let t=this._locationStrategy.getBaseHref();this._basePath=Am(ll(cl(t))),this._locationStrategy.onPopState(r=>{let o={url:this.path(!0),pop:!0,state:r.state,type:r.type};r.hasUAVisualTransition&&(o.hasUAVisualTransition=!0),this._subject.next(o)})}ngOnDestroy(){this._urlChangeSubscription?.unsubscribe(),this._urlChangeListeners=[]}path(e=!1){return this.normalize(this._locationStrategy.path(e))}getState(){return this._locationStrategy.getState()}isCurrentPathEqualTo(e,t=``){return this.path()==this.normalize(e+ct(t))}normalize(e){return n.stripTrailingSlash(Mm(this._basePath,cl(e)))}prepareExternalUrl(e){return e&&e[0]!==`/`&&(e=`/`+e),this._locationStrategy.prepareExternalUrl(e)}go(e,t=``,r=null){this._locationStrategy.pushState(r,``,e,t),this._notifyUrlChangeListeners(this.prepareExternalUrl(e+ct(t)),r)}replaceState(e,t=``,r=null){this._locationStrategy.replaceState(r,``,e,t),this._notifyUrlChangeListeners(this.prepareExternalUrl(e+ct(t)),r)}forward(){this._locationStrategy.forward()}back(){this._locationStrategy.back()}historyGo(e=0){this._locationStrategy.historyGo?.(e)}onUrlChange(e){return this._urlChangeListeners.push(e),this._urlChangeSubscription??=this.subscribe(t=>{this._notifyUrlChangeListeners(t.url,t.state)}),()=>{let t=this._urlChangeListeners.indexOf(e);this._urlChangeListeners.splice(t,1),this._urlChangeListeners.length===0&&(this._urlChangeSubscription?.unsubscribe(),this._urlChangeSubscription=null)}}_notifyUrlChangeListeners(e=``,t){this._urlChangeListeners.forEach(r=>r(e,t))}subscribe(e,t,r){return this._subject.subscribe({next:e,error:t??void 0,complete:r??void 0})}static normalizeQueryParams=ct;static joinWithSlash=Tr;static stripTrailingSlash=ll;static ɵfac=function(t){return new(t||n)(ae(On))};static ɵprov=K({token:n,factory:()=>Em(),providedIn:`root`})}return n})();function Em(){return new Or(ae(On))}function Mm(n,i){if(!n||!i.startsWith(n))return i;let e=i.substring(n.length);return e===``||[`/`,`;`,`?`,`#`].includes(e[0])?e:i}function cl(n){return n.replace(/\/index\.html$/,``)}function Am(n){if(new RegExp(`^(https?:)?//`).test(n)){let[,e]=n.split(/\/\/[^\/]+/);return e}return n}var Nm=(()=>{class n extends On{_platformLocation;_baseHref=``;_removeListenerFns=[];constructor(e,t){super(),this._platformLocation=e,t!=null&&(this._baseHref=t)}ngOnDestroy(){for(;this._removeListenerFns.length;)this._removeListenerFns.pop()()}onPopState(e){this._removeListenerFns.push(this._platformLocation.onPopState(e),this._platformLocation.onHashChange(e))}getBaseHref(){return this._baseHref}path(e=!1){let t=this._platformLocation.hash??`#`;return t.length>0?t.substring(1):t}prepareExternalUrl(e){let t=Tr(this._baseHref,e);return t.length>0?`#`+t:t}pushState(e,t,r,o){let a=this.prepareExternalUrl(r+ct(o))||this._platformLocation.pathname;this._platformLocation.pushState(e,t,a)}replaceState(e,t,r,o){let a=this.prepareExternalUrl(r+ct(o))||this._platformLocation.pathname;this._platformLocation.replaceState(e,t,a)}forward(){this._platformLocation.forward()}back(){this._platformLocation.back()}getState(){return this._platformLocation.getState()}historyGo(e=0){this._platformLocation.historyGo?.(e)}static ɵfac=function(t){return new(t||n)(ae($t),ae(Rr,8))};static ɵprov=K({token:n,factory:n.ɵfac})}return n})();var qo=/\s+/;var ml=[];var Tm=(()=>{class n{_ngEl;_renderer;initialClasses=ml;rawClass;stateMap=new Map;constructor(e,t){this._ngEl=e,this._renderer=t}set klass(e){this.initialClasses=e!=null?e.trim().split(qo):ml}set ngClass(e){this.rawClass=typeof e==`string`?e.trim().split(qo):e}ngDoCheck(){for(let t of this.initialClasses)this._updateState(t,!0);let e=this.rawClass;if(Array.isArray(e)||e instanceof Set)for(let t of e)this._updateState(t,!0);else if(e!=null)for(let t of Object.keys(e))this._updateState(t,!!e[t]);this._applyStateDiff()}_updateState(e,t){let r=this.stateMap.get(e);r!==void 0?(r.enabled!==t&&(r.changed=!0,r.enabled=t),r.touched=!0):this.stateMap.set(e,{enabled:t,changed:!0,touched:!0})}_applyStateDiff(){for(let e of this.stateMap){let t=e[0],r=e[1];r.changed?(this._toggleClass(t,r.enabled),r.changed=!1):r.touched||(r.enabled&&this._toggleClass(t,!1),this.stateMap.delete(t)),r.touched=!1}}_toggleClass(e,t){e=e.trim(),e.length>0&&e.split(qo).forEach(r=>{t?this._renderer.addClass(this._ngEl.nativeElement,r):this._renderer.removeClass(this._ngEl.nativeElement,r)})}static ɵfac=function(t){return new(t||n)(Mr(Dr),Mr(La$1))};static ɵdir=VI({type:n,selectors:[[``,`ngClass`,``]],inputs:{klass:[0,`class`,`klass`],ngClass:`ngClass`}})}return n})();var Rm=(()=>{class n{_ngEl;_differs;_renderer;_ngStyle=null;_differ=null;constructor(e,t,r){this._ngEl=e,this._differs=t,this._renderer=r}set ngStyle(e){this._ngStyle=e,!this._differ&&e&&(this._differ=this._differs.find(e).create())}ngDoCheck(){if(this._differ){let e=this._differ.diff(this._ngStyle);e&&this._applyChanges(e)}}_setStyle(e,t){let[r,o]=e.split(`.`),a=r.indexOf(`-`)===-1?void 0:si$1.DashCase;t!=null?this._renderer.setStyle(this._ngEl.nativeElement,r,o?`${t}${o}`:t,a):this._renderer.removeStyle(this._ngEl.nativeElement,r,a)}_applyChanges(e){e.forEachRemovedItem(t=>this._setStyle(t.key,null)),e.forEachAddedItem(t=>this._setStyle(t.key,t.currentValue)),e.forEachChangedItem(t=>this._setStyle(t.key,t.currentValue))}static ɵfac=function(t){return new(t||n)(Mr(Dr),Mr(Bw),Mr(La$1))};static ɵdir=VI({type:n,selectors:[[``,`ngStyle`,``]],inputs:{ngStyle:`ngStyle`}})}return n})();var Ci=(()=>{class n{_viewContainerRef;_viewRef=null;ngTemplateOutletContext=null;ngTemplateOutlet=null;ngTemplateOutletInjector=null;injector=I(le);constructor(e){this._viewContainerRef=e}ngOnChanges(e){if(this._shouldRecreateView(e)){let t=this._viewContainerRef;if(this._viewRef&&t.remove(t.indexOf(this._viewRef)),!this.ngTemplateOutlet){this._viewRef=null;return}let r=this._createContextForwardProxy();this._viewRef=t.createEmbeddedView(this.ngTemplateOutlet,r,{injector:this._getInjector()})}}_getInjector(){return this.ngTemplateOutletInjector===`outlet`?this.injector:this.ngTemplateOutletInjector??void 0}_shouldRecreateView(e){return!!e.ngTemplateOutlet||!!e.ngTemplateOutletInjector}_createContextForwardProxy(){return new Proxy({},{set:(e,t,r)=>this.ngTemplateOutletContext?Reflect.set(this.ngTemplateOutletContext,t,r):!1,get:(e,t,r)=>{if(this.ngTemplateOutletContext)return Reflect.get(this.ngTemplateOutletContext,t,r)}})}static ɵfac=function(t){return new(t||n)(Mr(xi$1))};static ɵdir=VI({type:n,selectors:[[``,`ngTemplateOutlet`,``]],inputs:{ngTemplateOutletContext:`ngTemplateOutletContext`,ngTemplateOutlet:`ngTemplateOutlet`,ngTemplateOutletInjector:`ngTemplateOutletInjector`},features:[iy]})}return n})();function hl(n,i){return new T(2100,!1)}var Zo=class{createSubscription(i,e,t){return Ow(()=>i.subscribe({next:e,error:t}))}dispose(i){Ow(()=>i.unsubscribe())}};var Qo=class{createSubscription(i,e,t){return i.then(r=>e?.(r),r=>t?.(r)),{unsubscribe:()=>{e=null,t=null}}}dispose(i){i.unsubscribe()}};var Om=new Qo;var Fm=new Zo;var Pm=(()=>{class n{_ref;_latestValue=null;markForCheckOnValueUpdate=!0;_subscription=null;_obj=null;_strategy=null;applicationErrorHandler=I(at$1);constructor(e){this._ref=e}ngOnDestroy(){this._subscription&&this._dispose(),this._ref=null}transform(e){if(!this._obj){if(e)try{this.markForCheckOnValueUpdate=!1,this._subscribe(e)}finally{this.markForCheckOnValueUpdate=!0}return this._latestValue}return e!==this._obj?(this._dispose(),this.transform(e)):this._latestValue}_subscribe(e){this._obj=e,this._strategy=this._selectStrategy(e),this._subscription=this._strategy.createSubscription(e,t=>this._updateLatestValue(e,t),t=>this.applicationErrorHandler(t))}_selectStrategy(e){if(Ac$1(e))return Om;if(Sp$1(e))return Fm;throw hl(n,e)}_dispose(){this._strategy.dispose(this._subscription),this._latestValue=null,this._subscription=null,this._obj=null}_updateLatestValue(e,t){e===this._obj&&(this._latestValue=t,this.markForCheckOnValueUpdate&&this._ref?.markForCheck())}static ɵfac=function(t){return new(t||n)(Mr(w0,16))};static ɵpipe=HI({name:`async`,type:n,pure:!1})}return n})();var Lm=(()=>{class n{transform(e){return e==null?null:(Vm(n,e),e.toUpperCase())}static ɵfac=function(t){return new(t||n)};static ɵpipe=HI({name:`uppercase`,type:n,pure:!0})}return n})();function Vm(n,i){if(typeof i!=`string`)throw hl(n,i)}function Bm(n,i){return{key:n,value:i}}var zm=(()=>{class n{differs;constructor(e){this.differs=e}differ;keyValues=[];compareFn=ul;transform(e,t=ul){if(!e||!(e instanceof Map)&&typeof e!=`object`)return null;this.differ??=this.differs.find(e).create();let r=this.differ.diff(e),o=t!==this.compareFn;return r&&(this.keyValues=[],r.forEachItem(a=>{this.keyValues.push(Bm(a.key,a.currentValue))})),(r||o)&&(t&&this.keyValues.sort(t),this.compareFn=t),this.keyValues}static ɵfac=function(t){return new(t||n)(Mr(Bw,16))};static ɵpipe=HI({name:`keyvalue`,type:n,pure:!1})}return n})();function ul(n,i){let e=n.key,t=i.key;if(e===t)return 0;if(e==null)return 1;if(t==null)return-1;if(typeof e==`string`&&typeof t==`string`)return e<t?-1:1;if(typeof e==`number`&&typeof t==`number`)return e-t;if(typeof e==`boolean`&&typeof t==`boolean`)return e<t?-1:1;let r=String(e),o=String(t);return r==o?0:r<o?-1:1}var Jo=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({})}return n})();function Si(n,i){i=encodeURIComponent(i);for(let e of n.split(`;`)){let t=e.indexOf(`=`),[r,o]=t==-1?[e,``]:[e.slice(0,t),e.slice(t+1)];if(r.trim()!==i)continue;let a=o;try{a=decodeURIComponent(o)}catch(s){}return a.length>1&&a[0]===`"`&&a[a.length-1]===`"`&&(a=a.slice(1,-1)),a}return null}var ta=`browser`;function fl(n){return n===ta}var Nb=(()=>{class n{static ɵprov=K({token:n,providedIn:`root`,factory:()=>new ea(I(Bo),window)})}return n})();var ea=class{document;window;offset=()=>[0,0];constructor(i,e){this.document=i,this.window=e}setOffset(i){Array.isArray(i)?this.offset=()=>i:this.offset=i}getScrollPosition(){return[this.window.scrollX,this.window.scrollY]}scrollToPosition(i,e){this.window.scrollTo(Y($({},e),{left:i[0],top:i[1]}))}scrollToAnchor(i,e){let t=$m(this.document,i);t&&(this.scrollToElement(t,e),t.focus({preventScroll:!0}))}setHistoryScrollRestoration(i){try{this.window.history.scrollRestoration=i}catch(e){console.warn(ms$1(2400,!1))}}scrollToElement(i,e){let t=i.getBoundingClientRect(),r=t.left+this.window.pageXOffset,o=t.top+this.window.pageYOffset,a=this.offset();this.window.scrollTo(Y($({},e),{left:r-a[0],top:o-a[1]}))}};function $m(n,i){let e=n.getElementById(i)||n.getElementsByName(i)[0];if(e)return e;if(typeof n.createTreeWalker==`function`&&n.body&&typeof n.body.attachShadow==`function`){let t=n.createTreeWalker(n.body,NodeFilter.SHOW_ELEMENT),r=t.currentNode;for(;r;){let o=r.shadowRoot;if(o){let a=o.getElementById(i)||o.querySelector(`[name="${CSS.escape(i)}"]`);if(a)return a}r=t.nextNode()}}return null}var wi=class{_doc;constructor(i){this._doc=i}manager};var Fr=(()=>{class n extends wi{constructor(e){super(e)}supports(e){return!0}addEventListener(e,t,r,o){return e.addEventListener(t,r,o),()=>this.removeEventListener(e,t,r,o)}removeEventListener(e,t,r,o){return e.removeEventListener(t,r,o)}static ɵfac=function(t){return new(t||n)(ae(Bo))};static ɵprov=K({token:n,factory:n.ɵfac})}return n})();var Vr=new S(``);var aa=(()=>{class n{_zone;_plugins;_eventNameToPlugin=new Map;constructor(e,t){this._zone=t,e.forEach(a=>{a.manager=this});let r=e.filter(a=>!(a instanceof Fr));this._plugins=r.slice().reverse();let o=e.find(a=>a instanceof Fr);o&&this._plugins.push(o)}addEventListener(e,t,r,o){return this._findPluginFor(t).addEventListener(e,t,r,o)}getZone(){return this._zone}_findPluginFor(e){let t=this._eventNameToPlugin.get(e);if(t)return t;if(t=this._plugins.find(o=>o.supports(e)),!t)throw new T(-5101,!1);return this._eventNameToPlugin.set(e,t),t}static ɵfac=function(t){return new(t||n)(ae(Vr),ae(z))};static ɵprov=K({token:n,factory:n.ɵfac})}return n})();var na=`ng-app-id`;function gl(n){for(let i of n)i.remove()}function bl(n,i){let e=i.createElement(`style`);return e.textContent=n,e}function Gm(n,i,e,t){let r=n.head?.querySelectorAll(`style[${na}="${i}"],link[${na}="${i}"]`);if(!r||r.length===0)return!1;for(let o of r)o.removeAttribute(na),o instanceof HTMLLinkElement?t.set(o.href.slice(o.href.lastIndexOf(`/`)+1),{usage:0,elements:[o]}):o.textContent&&e.set(o.textContent,{usage:0,elements:[o]});return!0}function ra(n,i){let e=i.createElement(`link`);return e.setAttribute(`rel`,`stylesheet`),e.setAttribute(`href`,n),e}var sa=(()=>{class n{doc;appId;nonce;inline=new Map;external=new Map;hosts=new Set;constructor(e,t,r,o={}){this.doc=e,this.appId=t,this.nonce=r,Gm(e,t,this.inline,this.external)&&this.hosts.add(e.head)}addStyles(e,t){for(let r of e)this.addUsage(r,this.inline,bl);t?.forEach(r=>this.addUsage(r,this.external,ra))}removeStyles(e,t){for(let r of e)this.removeUsage(r,this.inline);t?.forEach(r=>this.removeUsage(r,this.external))}addUsage(e,t,r){let o=t.get(e);o?o.usage++:t.set(e,{usage:1,elements:[...this.hosts].map(a=>this.addElement(a,r(e,this.doc)))})}removeUsage(e,t){let r=t.get(e);r&&(r.usage--,r.usage<=0&&(gl(r.elements),t.delete(e)))}ngOnDestroy(){for(let[,{elements:e}]of[...this.inline,...this.external])gl(e);this.hosts.clear()}addHost(e){if(!this.hosts.has(e)){this.hosts.add(e);for(let[t,{elements:r}]of this.inline)r.push(this.addElement(e,bl(t,this.doc)));for(let[t,{elements:r}]of this.external)r.push(this.addElement(e,ra(t,this.doc)))}}removeHost(e){this.hosts.delete(e);for(let t of[...this.inline.values(),...this.external.values()]){let r=[];for(let o of t.elements)o.parentNode===e?o.remove():r.push(o);t.elements=r}}addElement(e,t){return this.nonce&&t.setAttribute(`nonce`,this.nonce),e.appendChild(t)}static ɵfac=function(t){return new(t||n)(ae(Bo),ae(Yu$1),ae($m$1,8),ae(Hm))};static ɵprov=K({token:n,factory:n.ɵfac})}return n})();var ia={svg:`http://www.w3.org/2000/svg`,xhtml:`http://www.w3.org/1999/xhtml`,xlink:`http://www.w3.org/1999/xlink`,xml:`http://www.w3.org/XML/1998/namespace`,xmlns:`http://www.w3.org/2000/xmlns/`,math:`http://www.w3.org/1998/Math/MathML`};var la=/%COMP%/g;var yl=`%COMP%`;var Wm=`_nghost-${yl}`;var Ym=`_ngcontent-${yl}`;var Xm=!0;var Km=new S(``,{factory:()=>Xm});var qm=new S(``);function Zm(n){return Ym.replace(la,n)}function Qm(n){return Wm.replace(la,n)}function vl(n,i){return i.map(e=>e.replace(la,n))}var ca=(()=>{class n{eventManager;sharedStylesHost;appId;removeStylesOnCompDestroy;doc;ngZone;nonce;tracingService;rendererByCompId=new Map;defaultRenderer;cssVarNamespace;constructor(e,t,r,o,a,s,c=null,d=null,m=null){this.eventManager=e,this.sharedStylesHost=t,this.appId=r,this.removeStylesOnCompDestroy=o,this.doc=a,this.ngZone=s,this.nonce=c,this.tracingService=d,this.cssVarNamespace=m??``,this.defaultRenderer=new ki(e,a,s,this.tracingService,this.cssVarNamespace)}createRenderer(e,t){if(!e||!t)return this.defaultRenderer;let r=this.getOrCreateRenderer(e,t);return r instanceof Lr?r.applyToHost(e):r instanceof Di&&r.applyStyles(),r}getOrCreateRenderer(e,t){let r=this.rendererByCompId,o=r.get(t.id);if(!o){let a=this.doc,s=this.ngZone,c=this.eventManager,d=this.sharedStylesHost,m=this.removeStylesOnCompDestroy,_=this.tracingService;switch(t.encapsulation){case Bt$1.Emulated:o=new Lr(c,d,t,this.appId,m,a,s,_,this.cssVarNamespace);break;case Bt$1.ShadowDom:return new Pr(c,e,t,a,s,this.nonce,_,this.cssVarNamespace,d);case Bt$1.ExperimentalIsolatedShadowDom:return new Pr(c,e,t,a,s,this.nonce,_,this.cssVarNamespace);default:o=new Di(c,d,t,m,a,s,_,this.cssVarNamespace)}r.set(t.id,o)}return o}ngOnDestroy(){this.rendererByCompId.clear()}componentReplaced(e){this.rendererByCompId.delete(e)}static ɵfac=function(t){return new(t||n)(ae(aa),ae(gp$1),ae(Yu$1),ae(Km),ae(Bo),ae(z),ae($m$1),ae(zt$1,8),ae(qm,8))};static ɵprov=K({token:n,factory:n.ɵfac})}return n})();var ki=class{eventManager;doc;ngZone;tracingService;cssVarNamespace;data=Object.create(null);throwOnSyntheticProps=!0;constructor(i,e,t,r,o=``){this.eventManager=i,this.doc=e,this.ngZone=t,this.tracingService=r,this.cssVarNamespace=o}destroy(){}destroyNode=null;createElement(i,e){return e?this.doc.createElementNS(ia[e]||e,i):this.doc.createElement(i)}createComment(i){return this.doc.createComment(i)}createText(i){return this.doc.createTextNode(i)}appendChild(i,e){(_l(i)?i.content:i).appendChild(e)}insertBefore(i,e,t){if(i){let r=_l(i)?i.content:i;if(t!=null&&t.parentNode!==r)throw new T(-5106,!1);r.insertBefore(e,t)}}removeChild(i,e){e.remove()}selectRootElement(i,e){let t=typeof i==`string`?this.doc.querySelector(i):i;if(!t)throw new T(-5104,!1);return e||(t.textContent=``),t}parentNode(i){return i.parentNode}nextSibling(i){return i.nextSibling}setAttribute(i,e,t,r){if(r){e=r+`:`+e;let o=ia[r];o?i.setAttributeNS(o,e,t):i.setAttribute(e,t)}else i.setAttribute(e,t)}removeAttribute(i,e,t){if(t){let r=ia[t];r?i.removeAttributeNS(r,e):i.removeAttribute(`${t}:${e}`)}else i.removeAttribute(e)}addClass(i,e){i.classList.add(e)}removeClass(i,e){i.classList.remove(e)}setStyle(i,e,t,r){let o=e.startsWith(`--`);o&&(e=e.replace(`%NS%`,this.cssVarNamespace)),o||r&(si$1.DashCase|si$1.Important)?i.style.setProperty(e,t,r&si$1.Important?`important`:``):i.style[e]=t}removeStyle(i,e,t){let r=e.startsWith(`--`);r&&(e=e.replace(`%NS%`,this.cssVarNamespace)),r||t&si$1.DashCase?i.style.removeProperty(e):i.style[e]=``}setProperty(i,e,t){i!=null&&(i[e]=t)}setValue(i,e){i.nodeValue=e}listen(i,e,t,r){if(typeof i==`string`&&(i=Xe().getGlobalEventTarget(this.doc,i),!i))throw new T(-5102,!1);let o=this.decoratePreventDefault(t);return this.tracingService?.wrapEventListener&&(o=this.tracingService.wrapEventListener(i,e,o)),this.eventManager.addEventListener(i,e,o,r)}decoratePreventDefault(i){return e=>{if(e===`__ngUnwrap__`)return i;i(e)===!1&&e.preventDefault()}}};function _l(n){return n.tagName===`TEMPLATE`&&n.content!==void 0}var Pr=class extends ki{hostEl;sharedStylesHost;shadowRoot;constructor(i,e,t,r,o,a,s,c,d){super(i,r,o,s,c),this.hostEl=e,this.sharedStylesHost=d,this.shadowRoot=e.attachShadow({mode:`open`}),this.sharedStylesHost&&this.sharedStylesHost.addHost(this.shadowRoot);let m=t.styles;m=vl(t.id,m).map(k=>k.replace(/%NS%/g,c));for(let k of m){let p=document.createElement(`style`);a&&p.setAttribute(`nonce`,a),p.textContent=k,this.shadowRoot.appendChild(p)}let _=t.getExternalStyles?.();if(_)for(let k of _){let p=ra(k,r);a&&p.setAttribute(`nonce`,a),this.shadowRoot.appendChild(p)}}nodeOrShadowRoot(i){return i===this.hostEl?this.shadowRoot:i}appendChild(i,e){return super.appendChild(this.nodeOrShadowRoot(i),e)}insertBefore(i,e,t){return super.insertBefore(this.nodeOrShadowRoot(i),e,t)}removeChild(i,e){return super.removeChild(null,e)}parentNode(i){return this.nodeOrShadowRoot(super.parentNode(this.nodeOrShadowRoot(i)))}destroy(){this.sharedStylesHost&&this.sharedStylesHost.removeHost(this.shadowRoot)}};var Di=class extends ki{sharedStylesHost;removeStylesOnCompDestroy;styles;styleUrls;constructor(i,e,t,r,o,a,s,c,d){super(i,o,a,s,c),this.sharedStylesHost=e,this.removeStylesOnCompDestroy=r;let m=t.styles,_=d?vl(d,m):m;this.styles=_.map(k=>k.replace(/%NS%/g,c)),this.styleUrls=t.getExternalStyles?.(d)}applyStyles(){this.sharedStylesHost.addStyles(this.styles,this.styleUrls)}destroy(){this.removeStylesOnCompDestroy&&Fv.size===0&&this.sharedStylesHost.removeStyles(this.styles,this.styleUrls)}};var Lr=class extends Di{contentAttr;hostAttr;constructor(i,e,t,r,o,a,s,c,d){let m=r+`-`+t.id;super(i,e,t,o,a,s,c,d,m),this.contentAttr=Zm(m),this.hostAttr=Qm(m)}applyToHost(i){this.applyStyles(),this.setAttribute(i,this.hostAttr,``)}createElement(i,e){let t=super.createElement(i,e);return super.setAttribute(t,this.contentAttr,``),t}};var Br=class n extends xi{supportsDOMEvents=!0;static makeCurrent(){Ko(new n)}onAndCancel(i,e,t,r){return i.addEventListener(e,t,r),()=>{i.removeEventListener(e,t,r)}}dispatchEvent(i,e){i.dispatchEvent(e)}remove(i){i.remove()}createElement(i,e){return e=e||this.getDefaultDocument(),e.createElement(i)}createHtmlDocument(){return document.implementation.createHTMLDocument(`fakeTitle`)}getDefaultDocument(){return document}isElementNode(i){return i.nodeType===Node.ELEMENT_NODE}isShadowRoot(i){return i instanceof DocumentFragment}getGlobalEventTarget(i,e){return e===`window`?window:e===`document`?i:e===`body`?i.body:null}getBaseHref(i){let e=Jm();return e==null?null:eu(e)}resetBaseElement(){Ei=null}getUserAgent(){return window.navigator.userAgent}getCookie(i){return Si(document.cookie,i)}};var Ei=null;function Jm(){return Ei=Ei||document.head.querySelector(`base`),Ei?Ei.getAttribute(`href`):null}function eu(n){return new URL(n,document.baseURI).pathname}var zr=class{addToWindow(i){Mt.getAngularTestability=(t,r=!0)=>{let o=i.findTestabilityInTree(t,r);if(o==null)throw new T(5103,!1);return o},Mt.getAllAngularTestabilities=()=>i.getAllTestabilities(),Mt.getAllAngularRootElements=()=>i.getAllRootElements();let e=t=>{let r=Mt.getAllAngularTestabilities(),o=r.length,a=function(){o--,o==0&&t()};r.forEach(s=>{s.whenStable(a)})};Mt.frameworkStabilizers||(Mt.frameworkStabilizers=[]),Mt.frameworkStabilizers.push(e)}findTestabilityInTree(i,e,t){if(e==null)return null;return i.getTestability(e)??(t?Xe().isShadowRoot(e)?this.findTestabilityInTree(i,e.host,!0):this.findTestabilityInTree(i,e.parentElement,!0):null)}};var xl=[`alt`,`control`,`meta`,`shift`];var tu={"\b":`Backspace`,"	":`Tab`,"":`Delete`,"\x1B":`Escape`,Del:`Delete`,Esc:`Escape`,Left:`ArrowLeft`,Right:`ArrowRight`,Up:`ArrowUp`,Down:`ArrowDown`,Menu:`ContextMenu`,Scroll:`ScrollLock`,Win:`OS`};var nu={alt:n=>n.altKey,control:n=>n.ctrlKey,meta:n=>n.metaKey,shift:n=>n.shiftKey};var Cl=(()=>{class n extends wi{constructor(e){super(e)}supports(e){return n.parseEventName(e)!=null}addEventListener(e,t,r,o){let a=n.parseEventName(t),s=n.eventCallback(a.fullKey,r,this.manager.getZone());return this.manager.getZone().runOutsideAngular(()=>Xe().onAndCancel(e,a.domEventName,s,o))}static parseEventName(e){let t=e.toLowerCase().split(`.`),r=t.shift();if(t.length===0||!(r===`keydown`||r===`keyup`))return null;let o=n._normalizeKey(t.pop()),a=``,s=t.indexOf(`code`);if(s>-1&&(t.splice(s,1),a=`code.`),xl.forEach(d=>{let m=t.indexOf(d);m>-1&&(t.splice(m,1),a+=d+`.`)}),a+=o,t.length!=0||o.length===0)return null;let c={};return c.domEventName=r,c.fullKey=a,c}static matchEventFullKeyCode(e,t){let r=tu[e.key]||e.key,o=``;return t.indexOf(`code.`)>-1&&(r=e.code,o=`code.`),r==null||!r?!1:(r=r.toLowerCase(),r===` `?r=`space`:r===`.`&&(r=`dot`),xl.forEach(a=>{if(a!==r){let s=nu[a];s(e)&&(o+=a+`.`)}}),o+=r,o===t)}static eventCallback(e,t,r){return o=>{n.matchEventFullKeyCode(o,e)&&r.runGuarded(()=>t(o))}}static _normalizeKey(e){return e===`esc`?`escape`:e}static ɵfac=function(t){return new(t||n)(ae(Bo))};static ɵprov=K({token:n,factory:n.ɵfac})}return n})();function iu(){Br.makeCurrent()}function ru(){return new _t}function ou(){return Ay(document),document}var su=eb(N0,`browser`,[{provide:Hm,useValue:ta},{provide:Ku$1,useValue:iu,multi:!0},{provide:Bo,useFactory:ou}]);var lu=[{provide:Wp$1,useClass:zr},{provide:Up$1,useClass:iD,deps:[z,Gp$1,Wp$1]},{provide:iD,useClass:iD,deps:[z,Gp$1,Wp$1]}];var cu=[{provide:Ms,useValue:`root`},{provide:_t,useFactory:ru},{provide:Vr,useClass:Fr,multi:!0},{provide:Vr,useClass:Cl,multi:!0},ca,{provide:gp$1,useClass:sa},{provide:sa,useExisting:gp$1},aa,{provide:mr$1,useExisting:ca},[]];var du=(()=>{class n{constructor(){}static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({providers:[...cu,...lu],imports:[Jo,I0]})}return n})();var It=class n{headers;normalizedNames=new Map;lazyInit;lazyUpdate=null;constructor(i){i?typeof i==`string`?this.lazyInit=()=>{this.headers=new Map,i.split(`
`).forEach(e=>{let t=e.indexOf(`:`);if(t>0){let r=e.slice(0,t),o=e.slice(t+1).trim();this.addHeaderEntry(r,o)}})}:typeof Headers<`u`&&i instanceof Headers?(this.headers=new Map,i.forEach((e,t)=>{this.addHeaderEntry(t,e)})):this.lazyInit=()=>{this.headers=new Map,Object.entries(i).forEach(([e,t])=>{this.setHeaderEntries(e,t)})}:this.headers=new Map}has(i){return this.init(),this.headers.has(i.toLowerCase())}get(i){this.init();let e=this.headers.get(i.toLowerCase());return e&&e.length>0?e[0]:null}keys(){return this.init(),Array.from(this.normalizedNames.values())}getAll(i){return this.init(),this.headers.get(i.toLowerCase())||null}append(i,e){return this.clone({name:i,value:e,op:`a`})}set(i,e){return this.clone({name:i,value:e,op:`s`})}delete(i,e){return this.clone({name:i,value:e,op:`d`})}maybeSetNormalizedName(i,e){this.normalizedNames.has(e)||this.normalizedNames.set(e,i)}init(){this.lazyInit&&(this.lazyInit instanceof n?this.copyFrom(this.lazyInit):this.lazyInit(),this.lazyInit=null,this.lazyUpdate&&(this.lazyUpdate.forEach(i=>this.applyUpdate(i)),this.lazyUpdate=null))}copyFrom(i){i.init();for(let[e,t]of i.headers.entries())this.headers.set(e,t),this.normalizedNames.set(e,i.normalizedNames.get(e))}clone(i){let e=new n;return e.lazyInit=this.lazyInit&&this.lazyInit instanceof n?this.lazyInit:this,e.lazyUpdate=(this.lazyUpdate||[]).concat([i]),e}applyUpdate(i){let e=i.name.toLowerCase();switch(i.op){case`a`:case`s`:let t=i.value;if(typeof t==`string`&&(t=[t]),t.length===0)return;this.maybeSetNormalizedName(i.name,e);let r=i.op===`a`?(this.headers.get(e)||[]).slice():[];r.push(...t),this.headers.set(e,r);break;case`d`:let o=i.value;if(o===void 0)this.headers.delete(e),this.normalizedNames.delete(e);else{let a=Array.isArray(o)?o:[o],s=this.headers.get(e);if(!s)return;s=s.filter(c=>a.indexOf(c)===-1),s.length===0?(this.headers.delete(e),this.normalizedNames.delete(e)):this.headers.set(e,s)}}}addHeaderEntry(i,e){let t=i.toLowerCase();this.maybeSetNormalizedName(i,t),this.headers.has(t)?this.headers.get(t).push(e):this.headers.set(t,[e])}setHeaderEntries(i,e){let t=(Array.isArray(e)?e:[e]).map(o=>o.toString()),r=i.toLowerCase();this.headers.set(r,t),this.maybeSetNormalizedName(i,r)}forEach(i){this.init(),Array.from(this.normalizedNames.keys()).forEach(e=>i(this.normalizedNames.get(e),this.headers.get(e)))}};var ua=class{map=new Map;set(i,e){return this.map.set(i,e),this}get(i){return this.map.has(i)||this.map.set(i,i.defaultValue()),this.map.get(i)}delete(i){return this.map.delete(i),this}has(i){return this.map.has(i)}keys(){return this.map.keys()}};var ha=class{encodeKey(i){return Sl(i)}encodeValue(i){return Sl(i)}decodeKey(i){return decodeURIComponent(i)}decodeValue(i){return decodeURIComponent(i)}};function mu(n,i){let e=new Map;return n.length>0&&n.replace(/^\?/,``).split(`&`).forEach(r=>{let o=r.indexOf(`=`),[a,s]=o==-1?[i.decodeKey(r),``]:[i.decodeKey(r.slice(0,o)),i.decodeValue(r.slice(o+1))],c=e.get(a)||[];c.push(s),e.set(a,c)}),e}var uu=/%(\d[a-f0-9])/gi;var hu={40:`@`,"3A":`:`,24:`$`,"2C":`,`,"3B":`;`,"3D":`=`,"3F":`?`,"2F":`/`};function Sl(n){return encodeURIComponent(n).replace(uu,(i,e)=>hu[e]??i)}function jr(n){return`${n}`}var At=class n{map;encoder;updates=null;cloneFrom=null;constructor(i={}){if(this.encoder=i.encoder||new ha,i.fromString){if(i.fromObject)throw new T(2805,!1);this.map=mu(i.fromString,this.encoder)}else i.fromObject?(this.map=new Map,Object.keys(i.fromObject).forEach(e=>{let t=i.fromObject[e],r=Array.isArray(t)?t.map(jr):[jr(t)];this.map.set(e,r)})):this.map=null}has(i){return this.init(),this.map.has(i)}get(i){this.init();let e=this.map.get(i);return e?e[0]:null}getAll(i){return this.init(),this.map.get(i)||null}keys(){return this.init(),Array.from(this.map.keys())}append(i,e){return this.clone({param:i,value:e,op:`a`})}appendAll(i){let e=[];return Object.keys(i).forEach(t=>{let r=i[t];Array.isArray(r)?r.forEach(o=>{e.push({param:t,value:o,op:`a`})}):e.push({param:t,value:r,op:`a`})}),this.clone(e)}set(i,e){return this.clone({param:i,value:e,op:`s`})}delete(i,e){return this.clone({param:i,value:e,op:`d`})}toString(){return this.init(),this.keys().map(i=>{let e=this.encoder.encodeKey(i);return this.map.get(i).map(t=>e+`=`+this.encoder.encodeValue(t)).join(`&`)}).filter(i=>i!==``).join(`&`)}clone(i){let e=new n({encoder:this.encoder});return e.cloneFrom=this.cloneFrom||this,e.updates=(this.updates||[]).concat(i),e}init(){if(this.map===null&&(this.map=new Map),this.cloneFrom!==null){this.cloneFrom.init();for(let[i,e]of this.cloneFrom.map.entries())this.map.set(i,e);this.updates.forEach(i=>{switch(i.op){case`a`:case`s`:let e=i.op===`a`?(this.map.get(i.param)||[]).slice():[];e.push(jr(i.value)),this.map.set(i.param,e);break;case`d`:if(i.value!==void 0){let t=(this.map.get(i.param)||[]).slice(),r=t.indexOf(jr(i.value));r!==-1&&t.splice(r,1),t.length>0?this.map.set(i.param,t):this.map.delete(i.param)}else{this.map.delete(i.param);break}}}),this.cloneFrom=this.updates=null}}};function pu(n){switch(n){case`DELETE`:case`GET`:case`HEAD`:case`OPTIONS`:case`JSONP`:return!1;default:return!0}}function wl(n){return typeof ArrayBuffer<`u`&&n instanceof ArrayBuffer}function kl(n){return typeof Blob<`u`&&n instanceof Blob}function Dl(n){return typeof FormData<`u`&&n instanceof FormData}function fu(n){return typeof URLSearchParams<`u`&&n instanceof URLSearchParams}var da=`Content-Type`;var El=`Accept`;var Il=`text/plain`;var Nl=`application/json`;var gu=`${Nl}, ${Il}, */*`;var Fn=class n{url;body=null;headers;context;reportProgress=!1;reportUploadProgress=!1;reportDownloadProgress=!1;withCredentials=!1;credentials;keepalive=!1;cache;priority;mode;redirect;referrer;integrity;referrerPolicy;responseType=`json`;method;params;urlWithParams;transferCache;timeout;constructor(i,e,t,r){this.url=e,this.method=i.toUpperCase();let o;if(pu(this.method)||r?(this.body=t!==void 0?t:null,o=r):o=t,o){if(this.reportProgress=!!o.reportProgress,this.reportUploadProgress=!!o.reportUploadProgress,this.reportDownloadProgress=!!o.reportDownloadProgress,this.withCredentials=!!o.withCredentials,this.keepalive=!!o.keepalive,o.responseType&&(this.responseType=o.responseType),o.headers&&(this.headers=o.headers),o.context&&(this.context=o.context),o.params&&(this.params=o.params),o.priority&&(this.priority=o.priority),o.cache&&(this.cache=o.cache),o.credentials&&(this.credentials=o.credentials),typeof o.timeout==`number`){if(o.timeout<1||!Number.isInteger(o.timeout))throw new T(2822,``);this.timeout=o.timeout}o.mode&&(this.mode=o.mode),o.redirect&&(this.redirect=o.redirect),o.integrity&&(this.integrity=o.integrity),o.referrer!==void 0&&(this.referrer=o.referrer),o.referrerPolicy&&(this.referrerPolicy=o.referrerPolicy),this.transferCache=o.transferCache}if(this.headers??=new It,this.context??=new ua,!this.params)this.params=new At,this.urlWithParams=e;else{let a=this.params.toString();if(a.length===0)this.urlWithParams=e;else{let s=e,c=``,d=e.indexOf(`#`);d!==-1&&(c=e.substring(d),s=e.substring(0,d));let m=s.indexOf(`?`),_=m===-1?`?`:m<s.length-1?`&`:``;this.urlWithParams=s+_+a+c}}}serializeBody(){return this.body===null?null:typeof this.body==`string`||wl(this.body)||kl(this.body)||Dl(this.body)||fu(this.body)?this.body:this.body instanceof At?this.body.toString():typeof this.body==`object`||typeof this.body==`boolean`||Array.isArray(this.body)?JSON.stringify(this.body):this.body.toString()}detectContentTypeHeader(){return this.body===null||Dl(this.body)?null:kl(this.body)?this.body.type||null:wl(this.body)?null:typeof this.body==`string`?Il:this.body instanceof At?`application/x-www-form-urlencoded;charset=UTF-8`:typeof this.body==`object`||typeof this.body==`number`||typeof this.body==`boolean`?Nl:null}clone(i={}){let e=i.method||this.method,t=i.url||this.url,r=i.responseType||this.responseType,o=i.keepalive??this.keepalive,a=i.priority||this.priority,s=i.cache||this.cache,c=i.mode||this.mode,d=i.redirect||this.redirect,m=i.credentials||this.credentials,_=i.referrer??this.referrer,k=i.integrity||this.integrity,p=i.referrerPolicy||this.referrerPolicy,z=i.transferCache??this.transferCache,K=i.timeout??this.timeout,fe=i.body!==void 0?i.body:this.body,St=i.withCredentials??this.withCredentials,qe=i.reportProgress??this.reportProgress,wt=i.reportUploadProgress??this.reportUploadProgress,tn=i.reportDownloadProgress??this.reportDownloadProgress,bt=i.headers||this.headers,nn=i.params||this.params,rn=i.context??this.context;return i.setHeaders!==void 0&&(bt=Object.keys(i.setHeaders).reduce((jt,_t)=>jt.set(_t,i.setHeaders[_t]),bt)),i.setParams&&(nn=Object.keys(i.setParams).reduce((jt,_t)=>jt.set(_t,i.setParams[_t]),nn)),new n(e,t,fe,{params:nn,headers:bt,context:rn,reportProgress:qe,reportUploadProgress:wt,reportDownloadProgress:tn,responseType:r,withCredentials:St,transferCache:z,keepalive:o,cache:s,priority:a,timeout:K,mode:c,redirect:d,credentials:m,referrer:_,integrity:k,referrerPolicy:p})}};var mn=(function(n){return n[n.Sent=0]=`Sent`,n[n.UploadProgress=1]=`UploadProgress`,n[n.ResponseHeader=2]=`ResponseHeader`,n[n.DownloadProgress=3]=`DownloadProgress`,n[n.Response=4]=`Response`,n[n.User=5]=`User`,n})(mn||{});var Mi=class{headers;status;statusText;url;ok;type;redirected;responseType;constructor(i,e=200,t=`OK`){this.headers=i.headers||new It,this.status=i.status!==void 0?i.status:e,this.statusText=i.statusText||t,this.url=i.url||null,this.redirected=i.redirected,this.responseType=i.responseType,this.ok=this.status>=200&&this.status<300}};var pa=class n extends Mi{constructor(i={}){super(i)}type=mn.ResponseHeader;clone(i={}){return new n({headers:i.headers||this.headers,status:i.status!==void 0?i.status:this.status,statusText:i.statusText||this.statusText,url:i.url||this.url||void 0})}};var Ai=class n extends Mi{body;constructor(i={}){super(i),this.body=i.body!==void 0?i.body:null}type=mn.Response;clone(i={}){return new n({body:i.body!==void 0?i.body:this.body,headers:i.headers||this.headers,status:i.status!==void 0?i.status:this.status,statusText:i.statusText||this.statusText,url:i.url||this.url||void 0,redirected:i.redirected??this.redirected,responseType:i.responseType??this.responseType})}};var dn=class extends Mi{name=`HttpErrorResponse`;message;error;ok=!1;constructor(i){super(i,0,`Unknown Error`),this.status>=200&&this.status<300?this.message=`Http failure during parsing for ${i.url||`(unknown url)`}`:this.message=`Http failure response for ${i.url||`(unknown url)`}: ${i.status} ${i.statusText}`,this.error=i.error||null}};var bu=200;var _u=/^\)\]\}',?\n/;var yu=new S(``,{factory:()=>null});var vu=(()=>{class n{fetchImpl=I(fa,{optional:!0})?.fetch??((...e)=>globalThis.fetch(...e));ngZone=I(z);destroyRef=I(Ae);maxResponseSize=I(yu);handle(e){return new N(t=>{let r=new AbortController,o=!1,a={next:c=>{c.type===mn.Response&&(o=!0),t.next(c)},error:c=>{o=!0,t.error(c)},complete:()=>{o=!0,t.complete()}};this.doRequest(e,r.signal,a).then(ga,c=>a.error(new dn({error:c})));let s;return e.timeout&&(s=this.ngZone.runOutsideAngular(()=>setTimeout(()=>{r.signal.aborted||r.abort(new DOMException(`signal timed out`,`TimeoutError`))},e.timeout))),()=>{s!==void 0&&clearTimeout(s),!o&&!r.signal.aborted&&r.abort()}})}doRequest(e,t,r){return Yt$1(this,null,function*(){let o=this.createRequestInit(e),a;try{let fe=this.ngZone.runOutsideAngular(()=>this.fetchImpl(e.urlWithParams,$({signal:t},o)));xu(fe),r.next({type:mn.Sent}),a=yield fe}catch(fe){r.error(new dn({error:fe,status:fe.status??0,statusText:fe.statusText,url:e.urlWithParams,headers:fe.headers}));return}let s=new It(a.headers),c=a.statusText,d=a.url||e.urlWithParams,m=a.status,_=null,k=e.reportProgress||e.reportDownloadProgress;if(k&&r.next(new pa({headers:s,status:m,statusText:c,url:d})),a.body){let fe=a.headers.get(da)??``,St=a.headers.get(`content-length`),qe=St!==null?Number(St):NaN;this.maxResponseSize!==null&&Number.isFinite(qe)&&qe>this.maxResponseSize&&(yield a.body.cancel(),Ml(this.maxResponseSize));let wt=[],tn=a.body.getReader(),bt=0,nn,rn,jt=typeof Zone<`u`&&Zone.current,_t=!1;if(yield this.ngZone.runOutsideAngular(()=>Yt$1(this,null,function*(){for(;;){if(this.destroyRef.destroyed){yield tn.cancel(),_t=!0;break}let{done:oe,value:g}=yield tn.read();if(oe)break;if(wt.push(g),bt+=g.length,this.maxResponseSize!==null&&bt>this.maxResponseSize&&(yield tn.cancel(),Ml(this.maxResponseSize)),k){rn=e.responseType===`text`?(rn??``)+(nn??=Al(fe)).decode(g,{stream:!0}):void 0;let se=()=>r.next({type:mn.DownloadProgress,total:Number.isFinite(qe)?qe:void 0,loaded:bt,partialText:rn});jt?jt.run(se):se()}}})),_t){r.complete();return}let G=this.concatChunks(wt,bt);try{_=this.parseBody(e,G,fe,m)}catch(oe){r.error(new dn({error:oe,headers:new It(a.headers),status:a.status,statusText:a.statusText,url:a.url||e.urlWithParams}));return}}m===0&&(m=_?bu:0);let p=m>=200&&m<300,z=a.redirected,K=a.type;p?(r.next(new Ai({body:_,headers:s,status:m,statusText:c,url:d,redirected:z,responseType:K})),r.complete()):r.error(new dn({error:_,headers:s,status:m,statusText:c,url:d,redirected:z,responseType:K}))})}parseBody(e,t,r,o){switch(e.responseType){case`json`:let a=new TextDecoder().decode(t).replace(_u,``);if(a===``)return null;try{return JSON.parse(a)}catch(s){if(o<200||o>=300)return a;throw s}case`text`:return Al(r).decode(t);case`blob`:return new Blob([t],{type:r});case`arraybuffer`:return t.buffer}}createRequestInit(e){if(e.reportUploadProgress)throw new T(2824,!1);let t={},r;if(r=e.credentials,e.withCredentials&&(r=`include`),e.headers.forEach((o,a)=>t[o]=a.join(`,`)),e.headers.has(El)||(t[El]=gu),!e.headers.has(da)){let o=e.detectContentTypeHeader();o!==null&&(t[da]=o)}return{body:e.serializeBody(),method:e.method,headers:t,credentials:r,keepalive:e.keepalive,cache:e.cache,priority:e.priority,mode:e.mode,redirect:e.redirect,referrer:e.referrer,integrity:e.integrity,referrerPolicy:e.referrerPolicy}}concatChunks(e,t){let r=new Uint8Array(t),o=0;for(let a of e)r.set(a,o),o+=a.length;return r}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var fa=class{};function ga(){}function xu(n){n.then(ga,ga)}function Ml(n){throw new T(-2825,!1)}var Cu=/charset=\s*["']?([^;"'\s]+)["']?/i;function Al(n){let i=n.match(Cu);if(i!==null)try{return new TextDecoder(i[1])}catch(e){}return new TextDecoder}var Su=new S(``,{factory:()=>!0});var wu=`XSRF-TOKEN`;var ku=new S(``,{factory:()=>wu});var Du=`X-XSRF-TOKEN`;var Eu=new S(``,{factory:()=>Du});var Mu=(()=>{class n{cookieName=I(ku);doc=I(Bo);lastCookieString=``;lastToken=null;parseCount=0;getToken(){let e=this.doc.cookie||``;return e!==this.lastCookieString&&(this.parseCount++,this.lastToken=Si(e,this.cookieName),this.lastCookieString=e),this.lastToken}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Au=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵprov=K({token:n,factory:function(t){let r=null;return t?r=new(t||n):r=ae(Mu),r},providedIn:`root`})}return n})();function Iu(n,i){if(!I(Su)||n.method===`GET`||n.method===`HEAD`)return i(n);try{let r=I($t).href,{origin:o}=new URL(r),{origin:a}=new URL(n.url,o);if(o!==a)return i(n)}catch(r){return i(n)}let e=I(Au).getToken(),t=I(Eu);return e!=null&&!n.headers.has(t)&&(n=n.clone({headers:n.headers.set(t,e)})),i(n)}function Nu(n,i){return i(n)}function Tu(n,i,e){return(t,r)=>Mo$1(e,()=>i(t,o=>n(o,r)))}var Ru=new S(``,{factory:()=>[Iu]});var Tl=new S(``);var Ou=new S(``,{factory:()=>!0});var Fu=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵprov=K({token:n,factory:function(t){let r=null;return t?r=new(t||n):r=ae(vu),r},providedIn:`root`})}return n})();var Pu=(()=>{class n{backend;injector;chain=null;pendingTasks=I(td$1);contributeToStability=I(Ou);constructor(e,t){this.backend=e,this.injector=t}handle(e){if(this.chain===null){let r=this.injector.get(Rl,null,{skipSelf:!0}),o=r!==null&&this.backend===r,a=this.injector.get(Tl,[],o?{self:!0}:void 0),s=Array.from(new Set([...this.injector.get(Ru),...a]));this.chain=s.reduceRight((c,d)=>Tu(c,d,this.injector),Nu)}let t=this.chain;if(this.contributeToStability){let r=this.pendingTasks.add();return Ow(()=>t(e,o=>this.backend.handle(o))).pipe(Bl$1(r))}else return Ow(()=>t(e,r=>this.backend.handle(r)))}static ɵfac=function(t){return new(t||n)(ae(Fu),ae(De))};static ɵprov=K({token:n,factory:n.ɵfac,providedIn:`root`})}return n})();var Rl=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵprov=K({token:n,factory:function(t){let r=null;return t?r=new(t||n):r=ae(Pu),r},providedIn:`root`})}return n})();function ma(n,i){return $({body:i},n)}var ba=(()=>{class n{handler;constructor(e){this.handler=e}request(e,t,r={}){let o;if(e instanceof Fn)o=e;else{let c;r.headers instanceof It?c=r.headers:c=new It(r.headers);let d;r.params&&(r.params instanceof At?d=r.params:d=new At({fromObject:r.params})),o=new Fn(e,t,r.body!==void 0?r.body:null,{headers:c,context:r.context,params:d,reportProgress:r.reportProgress,reportUploadProgress:r.reportUploadProgress,reportDownloadProgress:r.reportDownloadProgress,responseType:r.responseType||`json`,withCredentials:r.withCredentials,transferCache:r.transferCache,keepalive:r.keepalive,priority:r.priority,cache:r.cache,mode:r.mode,redirect:r.redirect,credentials:r.credentials,referrer:r.referrer,referrerPolicy:r.referrerPolicy,integrity:r.integrity,timeout:r.timeout})}let a=Sg(o).pipe(Ug(c=>this.handler.handle(c)));if(e instanceof Fn||r.observe===`events`)return a;let s=a.pipe(rn(c=>c instanceof Ai));switch(r.observe||`body`){case`body`:switch(o.responseType){case`arraybuffer`:return s.pipe(Me$1(c=>{if(c.body!==null&&!(c.body instanceof ArrayBuffer))throw new T(2806,!1);return c.body}));case`blob`:return s.pipe(Me$1(c=>{if(c.body!==null&&!(c.body instanceof Blob))throw new T(2807,!1);return c.body}));case`text`:return s.pipe(Me$1(c=>{if(c.body!==null&&typeof c.body!=`string`)throw new T(2808,!1);return c.body}));default:return s.pipe(Me$1(c=>c.body))}case`response`:return s;default:throw new T(2809,!1)}}delete(e,t={}){return this.request(`DELETE`,e,t)}get(e,t={}){return this.request(`GET`,e,t)}head(e,t={}){return this.request(`HEAD`,e,t)}jsonp(e,t){return this.request(`JSONP`,e,{params:new At().append(t,`JSONP_CALLBACK`),observe:`body`,responseType:`json`})}options(e,t={}){return this.request(`OPTIONS`,e,t)}patch(e,t,r={}){return this.request(`PATCH`,e,ma(r,t))}post(e,t,r={}){return this.request(`POST`,e,ma(r,t))}put(e,t,r={}){return this.request(`PUT`,e,ma(r,t))}static ɵfac=function(t){return new(t||n)(ae(Rl))};static ɵprov=K({token:n,factory:n.ɵfac,providedIn:`root`})}return n})();var j_=(()=>{class n{_doc;constructor(e){this._doc=e}getTitle(){return this._doc.title}setTitle(e){this._doc.title=e||``}static ɵfac=function(t){return new(t||n)(ae(Bo))};static ɵprov=K({token:n,factory:n.ɵfac,providedIn:`root`})}return n})();var Ii=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵprov=K({token:n,factory:function(t){let r=null;return t?r=new(t||n):r=ae(Vu),r},providedIn:`root`})}return n})();var Vu=(()=>{class n extends Ii{_doc=I(Bo);sanitize(e,t){if(t==null)return null;switch(e){case ne.NONE:return t;case ne.HTML:return ic$1(t,`HTML`)?$t$1(t):_f$1(this._doc,String(t)).toString();case ne.STYLE:return ic$1(t,`Style`)?$t$1(t):t;case ne.SCRIPT:if(ic$1(t,`Script`))return $t$1(t);throw new T(5200,!1);case ne.URL:return ic$1(t,`URL`)?$t$1(t):sc$1(String(t));case ne.RESOURCE_URL:if(ic$1(t,`ResourceURL`))return $t$1(t);throw new T(-5201,!1);default:throw new T(5202,!1)}}bypassSecurityTrustHtml(e){return By(e)}bypassSecurityTrustStyle(e){return $y(e)}bypassSecurityTrustScript(e){return Uy(e)}bypassSecurityTrustUrl(e){return Wy(e)}bypassSecurityTrustResourceUrl(e){return qy(e)}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var _a;try{_a=typeof Intl<`u`&&Intl.v8BreakIterator}catch(n){_a=!1}var J=(()=>{class n{_platformId=I(Hm);isBrowser=this._platformId?fl(this._platformId):typeof document==`object`&&!!document;EDGE=this.isBrowser&&/(edge)/i.test(navigator.userAgent);TRIDENT=this.isBrowser&&/(msie|trident)/i.test(navigator.userAgent);BLINK=this.isBrowser&&!!(window.chrome||_a)&&typeof CSS<`u`&&!this.EDGE&&!this.TRIDENT;WEBKIT=this.isBrowser&&/AppleWebKit/i.test(navigator.userAgent)&&!this.BLINK&&!this.EDGE&&!this.TRIDENT;IOS=this.isBrowser&&/iPad|iPhone|iPod/.test(navigator.userAgent)&&!(`MSStream`in window);FIREFOX=this.isBrowser&&/(firefox|minefield)/i.test(navigator.userAgent);ANDROID=this.isBrowser&&/android/i.test(navigator.userAgent)&&!this.TRIDENT;SAFARI=this.isBrowser&&/safari/i.test(navigator.userAgent)&&this.WEBKIT;static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var ya;function Ol(){if(ya==null){let n=typeof document<`u`?document.head:null;ya=!!(n&&(n.createShadowRoot||n.attachShadow))}return ya}function va(n){if(Ol()){let i=n.getRootNode?n.getRootNode():null;if(typeof ShadowRoot<`u`&&ShadowRoot&&i instanceof ShadowRoot)return i}return null}function Ni(){let n=typeof document<`u`&&document?document.activeElement:null;for(;n&&n.shadowRoot;){let i=n.shadowRoot.activeElement;if(i===n)break;n=i}return n}function Ie(n){if(n.composedPath)try{return n.composedPath()[0]}catch(i){}return n.target}function xa(){return typeof __karma__<`u`&&!!__karma__||typeof jasmine<`u`&&!!jasmine||typeof jest<`u`&&!!jest||typeof Mocha<`u`&&!!Mocha}var Ur=new WeakMap;var Se=(()=>{class n{_appRef;_injector=I(le);_environmentInjector=I(De);load(e){let t=this._appRef=this._appRef||this._injector.get(Zt$1),r=Ur.get(t);r||(r={loaders:new Set,refs:[]},Ur.set(t,r),t.onDestroy(()=>{Ur.get(t)?.refs.forEach(o=>o.destroy()),Ur.delete(t)})),r.loaders.has(e)||(r.loaders.add(e),r.refs.push(M0(e,{environmentInjector:this._environmentInjector})))}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();function ve(n){return n==null?``:typeof n==`string`?n:`${n}px`}function Pn(n){return Array.isArray(n)?n:[n]}function dt(n,i=0){return Fl(n)?Number(n):arguments.length===2?i:0}function Fl(n){return!isNaN(parseFloat(n))&&!isNaN(Number(n))}function je(n){return n instanceof Dr?n.nativeElement:n}var zu=new S(`cdk-dir-doc`,{providedIn:`root`,factory:()=>I(Bo)});var ju=/^(ar|ckb|dv|he|iw|fa|nqo|ps|sd|ug|ur|yi|.*[-_](Adlm|Arab|Hebr|Nkoo|Rohg|Thaa))(?!.*[-_](Latn|Cyrl)($|-|_))($|-|_)/i;function Pl(n){let i=n?.toLowerCase()||``;return i===`auto`&&typeof navigator<`u`&&navigator?.language?ju.test(navigator.language)?`rtl`:`ltr`:i===`rtl`?`rtl`:`ltr`}var Ne=(()=>{class n{get value(){return this.valueSignal()}valueSignal=oa(`ltr`);change=new Fe;constructor(){let e=I(zu,{optional:!0});if(e){let t=e.body?e.body.dir:null,r=e.documentElement?e.documentElement.dir:null;this.valueSignal.set(Pl(t||r||`ltr`))}}ngOnDestroy(){this.change.complete()}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var mt=(function(n){return n[n.NORMAL=0]=`NORMAL`,n[n.NEGATED=1]=`NEGATED`,n[n.INVERTED=2]=`INVERTED`,n})(mt||{});var Hr;var un;function $r(){if(un==null){if(typeof document!=`object`||!document||typeof Element!=`function`||!Element)return un=!1,un;if(document.documentElement?.style&&`scrollBehavior`in document.documentElement.style)un=!0;else{let n=Element.prototype.scrollTo;n?un=!/\{\s*\[native code\]\s*\}/.test(n.toString()):un=!1}}return un}function Ln(){if(typeof document!=`object`||!document)return mt.NORMAL;if(Hr==null){let n=document.createElement(`div`),i=n.style;n.dir=`rtl`,i.width=`1px`,i.overflow=`auto`,i.visibility=`hidden`,i.pointerEvents=`none`,i.position=`absolute`;let e=document.createElement(`div`),t=e.style;t.width=`2px`,t.height=`1px`,n.appendChild(e),document.body.appendChild(n),Hr=mt.NORMAL,n.scrollLeft===0&&(n.scrollLeft=1,Hr=n.scrollLeft===0?mt.NEGATED:mt.INVERTED),n.remove()}return Hr}var te=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({})}return n})();var Uu=20;var Gt=(()=>{class n{_ngZone=I(z);_platform=I(J);_renderer=I(mr$1).createRenderer(null,null);_cleanupGlobalListener;_scrolled=new te$1;_scrolledCount=0;scrollContainers=new Map;register(e){this.scrollContainers.has(e)||this.scrollContainers.set(e,e.elementScrolled().subscribe(()=>this._scrolled.next(e)))}deregister(e){let t=this.scrollContainers.get(e);t&&(t.unsubscribe(),this.scrollContainers.delete(e))}scrolled(e=Uu){return this._platform.isBrowser?new N(t=>{this._cleanupGlobalListener||(this._cleanupGlobalListener=this._ngZone.runOutsideAngular(()=>this._renderer.listen(`document`,`scroll`,()=>this._scrolled.next())));let r=e>0?this._scrolled.pipe(Nl$1(e)).subscribe(t):this._scrolled.subscribe(t);return this._scrolledCount++,()=>{r.unsubscribe(),this._scrolledCount--,this._scrolledCount||(this._cleanupGlobalListener?.(),this._cleanupGlobalListener=void 0)}}):Sg()}ngOnDestroy(){this._cleanupGlobalListener?.(),this._cleanupGlobalListener=void 0,this.scrollContainers.forEach((e,t)=>this.deregister(t)),this._scrolled.complete()}ancestorScrolled(e,t){let r=this.getAncestorScrollContainers(e);return this.scrolled(t).pipe(rn(o=>!o||r.indexOf(o)>-1))}getAncestorScrollContainers(e){let t=[];return this.scrollContainers.forEach((r,o)=>{this._targetContainsElement(o,e)&&t.push(o)}),t}_targetContainsElement(e,t){let r=je(t),o=e.getElementRef().nativeElement;do if(r==o)return!0;while(r=r.parentElement);return!1}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Ca=(()=>{class n{elementRef=I(Dr);scrollDispatcher=I(Gt);ngZone=I(z);dir=I(Ne,{optional:!0});_scrollElement=this.elementRef.nativeElement;_destroyed=new te$1;_renderer=I(La$1);_cleanupScroll;_elementScrolled=new te$1;ngOnInit(){this._cleanupScroll=this.ngZone.runOutsideAngular(()=>this._renderer.listen(this._scrollElement,`scroll`,e=>this._elementScrolled.next(e))),this.scrollDispatcher.register(this)}ngOnDestroy(){this._cleanupScroll?.(),this._elementScrolled.complete(),this.scrollDispatcher.deregister(this),this._destroyed.next(),this._destroyed.complete()}elementScrolled(){return this._elementScrolled}getElementRef(){return this.elementRef}scrollTo(e){let t=this.elementRef.nativeElement,r=this.dir&&this.dir.value==`rtl`;e.left??=r?e.end:e.start,e.right??=r?e.start:e.end,e.bottom!=null&&(e.top=t.scrollHeight-t.clientHeight-e.bottom),r&&Ln()!=mt.NORMAL?(e.left!=null&&(e.right=t.scrollWidth-t.clientWidth-e.left),Ln()==mt.INVERTED?e.left=e.right:Ln()==mt.NEGATED&&(e.left=e.right?-e.right:e.right)):e.right!=null&&(e.left=t.scrollWidth-t.clientWidth-e.right),this._applyScrollToOptions(e)}_applyScrollToOptions(e){let t=this.elementRef.nativeElement;$r()?t.scrollTo(e):(e.top!=null&&(t.scrollTop=e.top),e.left!=null&&(t.scrollLeft=e.left))}measureScrollOffset(e){let t=`left`,r=`right`,o=this.elementRef.nativeElement;if(e==`top`)return o.scrollTop;if(e==`bottom`)return o.scrollHeight-o.clientHeight-o.scrollTop;let a=this.dir&&this.dir.value==`rtl`;return e==`start`?e=a?r:t:e==`end`&&(e=a?t:r),a&&Ln()==mt.INVERTED?e==t?o.scrollWidth-o.clientWidth-o.scrollLeft:o.scrollLeft:a&&Ln()==mt.NEGATED?e==t?o.scrollLeft+o.scrollWidth-o.clientWidth:-o.scrollLeft:e==t?o.scrollLeft:o.scrollWidth-o.clientWidth-o.scrollLeft}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`cdk-scrollable`,``],[``,`cdkScrollable`,``]]})}return n})();var Hu=20;var Tt=(()=>{class n{_platform=I(J);_listeners;_viewportSize=null;_change=new te$1;_document=I(Bo);constructor(){let e=I(z),t=I(mr$1).createRenderer(null,null);e.runOutsideAngular(()=>{if(this._platform.isBrowser){let r=o=>this._change.next(o);this._listeners=[t.listen(`window`,`resize`,r),t.listen(`window`,`orientationchange`,r)]}this.change().subscribe(()=>this._viewportSize=null)})}ngOnDestroy(){this._listeners?.forEach(e=>e()),this._change.complete()}getViewportSize(){this._viewportSize||this._updateViewportSize();let e={width:this._viewportSize.width,height:this._viewportSize.height};return this._platform.isBrowser||(this._viewportSize=null),e}getViewportRect(){let e=this.getViewportScrollPosition(),{width:t,height:r}=this.getViewportSize();return{top:e.top,left:e.left,bottom:e.top+r,right:e.left+t,height:r,width:t}}getViewportScrollPosition(){if(!this._platform.isBrowser)return{top:0,left:0};let e=this._document,t=this._getWindow(),r=e.documentElement,o=r.getBoundingClientRect();return{top:-o.top||e.body?.scrollTop||t.scrollY||r.scrollTop||0,left:-o.left||e.body?.scrollLeft||t.scrollX||r.scrollLeft||0}}change(e=Hu){return e>0?this._change.pipe(Nl$1(e)):this._change}_getWindow(){return this._document.defaultView||window}_updateViewportSize(){let e=this._getWindow();this._viewportSize=this._platform.isBrowser?{width:e.innerWidth,height:e.innerHeight}:{width:0,height:0}}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Nt=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({})}return n})();var Sa=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[te,Nt,te,Nt]})}return n})();var Ll=new Map;var me=class n{_appId=I(Yu$1);static _infix=`a${Math.floor(Math.random()*1e5).toString()}`;getId(i,e=!1){this._appId!==`ng`&&(i+=this._appId);let t=Ll.get(i);return t===void 0?t=0:t++,Ll.set(i,t),`${i}${e?n._infix+`-`:``}${t}`}static ɵfac=function(e){return new(e||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})};var Ti=class{_attachedHost=null;attach(i){return this._attachedHost=i,i.attach(this)}detach(){let i=this._attachedHost;i!=null&&(this._attachedHost=null,i.detach())}get isAttached(){return this._attachedHost!=null}setAttachedHost(i){this._attachedHost=i}};var ut=class extends Ti{component;viewContainerRef;injector;projectableNodes;bindings;directives;constructor(i,e,t,r,o,a){super(),this.component=i,this.viewContainerRef=e,this.injector=t,this.projectableNodes=r,this.bindings=o||null,this.directives=a||null}};var rt=class extends Ti{templateRef;viewContainerRef;context;injector;constructor(i,e,t,r){super(),this.templateRef=i,this.viewContainerRef=e,this.context=t,this.injector=r}get origin(){return this.templateRef.elementRef}attach(i,e=this.context){return this.context=e,super.attach(i)}detach(){return this.context=void 0,super.detach()}};var wa=class extends Ti{element;constructor(i){super(),this.element=i instanceof Dr?i.nativeElement:i}};var Wt=class{_attachedPortal=null;_disposeFn=null;_isDisposed=!1;hasAttached(){return!!this._attachedPortal}attach(i){if(i instanceof ut)return this._attachedPortal=i,this.attachComponentPortal(i);if(i instanceof rt)return this._attachedPortal=i,this.attachTemplatePortal(i);if(this.attachDomPortal&&i instanceof wa)return this._attachedPortal=i,this.attachDomPortal(i)}attachDomPortal=null;detach(){this._attachedPortal&&(this._attachedPortal.setAttachedHost(null),this._attachedPortal=null),this._invokeDisposeFn()}dispose(){this.hasAttached()&&this.detach(),this._invokeDisposeFn(),this._isDisposed=!0}setDisposeFn(i){this._disposeFn=i}_invokeDisposeFn(){this._disposeFn&&(this._disposeFn(),this._disposeFn=null)}};var Ri=class extends Wt{outletElement;_appRef;_defaultInjector;constructor(i,e,t){super(),this.outletElement=i,this._appRef=e,this._defaultInjector=t}attachComponentPortal(i){let e;if(i.viewContainerRef){let t=i.injector||i.viewContainerRef.injector,r=t.get(xn$1,null,{optional:!0})||void 0;e=i.viewContainerRef.createComponent(i.component,{index:i.viewContainerRef.length,injector:t,ngModuleRef:r,projectableNodes:i.projectableNodes||void 0,bindings:i.bindings||void 0,directives:i.directives||void 0}),this.setDisposeFn(()=>e.destroy())}else{let t=this._appRef,r=i.injector||this._defaultInjector||le.NULL,o=r.get(De,t.injector);e=M0(i.component,{elementInjector:r,environmentInjector:o,projectableNodes:i.projectableNodes||void 0,bindings:i.bindings||void 0,directives:i.directives||void 0}),t.attachView(e.hostView),this.setDisposeFn(()=>{t.viewCount>0&&t.detachView(e.hostView),e.destroy()})}return this.outletElement.appendChild(this._getComponentRootNode(e)),this._attachedPortal=i,e}attachTemplatePortal(i){let e=i.viewContainerRef,t=e.createEmbeddedView(i.templateRef,i.context,{injector:i.injector});return t.rootNodes.forEach(r=>this.outletElement.appendChild(r)),t.detectChanges(),this.setDisposeFn(()=>{let r=e.indexOf(t);r!==-1&&e.remove(r)}),this._attachedPortal=i,t}attachDomPortal=i=>{let e=i.element;e.parentNode;let t=this.outletElement.ownerDocument.createComment(`dom-portal`);e.parentNode.insertBefore(t,e),this.outletElement.appendChild(e),this._attachedPortal=i,super.setDisposeFn(()=>{t.parentNode&&t.parentNode.replaceChild(e,t)})};dispose(){super.dispose(),this.outletElement.remove()}_getComponentRootNode(i){return i.hostView.rootNodes[0]}};var Fy=(()=>{class n extends rt{constructor(){let e=I(gr),t=I(xi$1);super(e,t)}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`cdkPortal`,``]],exportAs:[`cdkPortal`],features:[Vp$1]})}return n})();var Yt=(()=>{class n extends Wt{_moduleRef=I(xn$1,{optional:!0});_document=I(Bo);_viewContainerRef=I(xi$1);_isInitialized=!1;_attachedRef=null;get portal(){return this._attachedPortal}set portal(e){this.hasAttached()&&!e&&!this._isInitialized||(this.hasAttached()&&super.detach(),e&&super.attach(e),this._attachedPortal=e||null)}attached=new Fe;get attachedRef(){return this._attachedRef}ngOnInit(){this._isInitialized=!0}ngOnDestroy(){super.dispose(),this._attachedRef=this._attachedPortal=null}attachComponentPortal(e){e.setAttachedHost(this);let t=e.viewContainerRef!=null?e.viewContainerRef:this._viewContainerRef,r=t.createComponent(e.component,{index:t.length,injector:e.injector||t.injector,projectableNodes:e.projectableNodes||void 0,ngModuleRef:this._moduleRef||void 0,bindings:e.bindings||void 0,directives:e.directives||void 0});return t!==this._viewContainerRef&&this._getRootNode().appendChild(r.hostView.rootNodes[0]),super.setDisposeFn(()=>r.destroy()),this._attachedPortal=e,this._attachedRef=r,this.attached.emit(r),r}attachTemplatePortal(e){e.setAttachedHost(this);let t=this._viewContainerRef.createEmbeddedView(e.templateRef,e.context,{injector:e.injector});return super.setDisposeFn(()=>this._viewContainerRef.clear()),this._attachedPortal=e,this._attachedRef=t,this.attached.emit(t),t}attachDomPortal=e=>{let t=e.element;t.parentNode;let r=this._document.createComment(`dom-portal`);e.setAttachedHost(this),t.parentNode.insertBefore(r,t),this._getRootNode().appendChild(t),this._attachedPortal=e,super.setDisposeFn(()=>{r.parentNode&&r.parentNode.replaceChild(t,r)})};_getRootNode(){let e=this._viewContainerRef.element.nativeElement;return e.nodeType===e.ELEMENT_NODE?e:e.parentNode}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[``,`cdkPortalOutlet`,``]],inputs:{portal:[0,`cdkPortalOutlet`,`portal`]},outputs:{attached:`attached`},exportAs:[`cdkPortalOutlet`],features:[Vp$1]})}return n})();var Rt=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({})}return n})();function Me(n,...i){return i.length?i.some(e=>n[e]):n.altKey||n.shiftKey||n.ctrlKey||n.metaKey}var Vl=$r();function zn(n){return new Gr(n.get(Tt),n.get(Bo))}var Gr=class{_viewportRuler;_previousHTMLStyles={top:``,left:``};_previousScrollPosition;_isEnabled=!1;_document;constructor(i,e){this._viewportRuler=i,this._document=e}attach(){}enable(){if(this._canBeEnabled()){let i=this._document.documentElement;this._previousScrollPosition=this._viewportRuler.getViewportScrollPosition(),this._previousHTMLStyles.left=i.style.left||``,this._previousHTMLStyles.top=i.style.top||``,i.style.left=ve(-this._previousScrollPosition.left),i.style.top=ve(-this._previousScrollPosition.top),i.classList.add(`cdk-global-scrollblock`),this._isEnabled=!0}}disable(){if(this._isEnabled){let i=this._document.documentElement,e=this._document.body,t=i.style,r=e.style,o=t.scrollBehavior||``,a=r.scrollBehavior||``;this._isEnabled=!1,t.left=this._previousHTMLStyles.left,t.top=this._previousHTMLStyles.top,i.classList.remove(`cdk-global-scrollblock`),Vl&&(t.scrollBehavior=r.scrollBehavior=`auto`),window.scroll(this._previousScrollPosition.left,this._previousScrollPosition.top),Vl&&(t.scrollBehavior=o,r.scrollBehavior=a)}}_canBeEnabled(){if(this._document.documentElement.classList.contains(`cdk-global-scrollblock`)||this._isEnabled)return!1;let e=this._document.documentElement,t=this._viewportRuler.getViewportSize();return e.scrollHeight>t.height||e.scrollWidth>t.width}};function Gl(n,i){return new Wr(n.get(Gt),n.get(z),n.get(Tt),i)}var Wr=class{_scrollDispatcher;_ngZone;_viewportRuler;_config;_scrollSubscription=null;_overlayRef;_initialScrollPosition;constructor(i,e,t,r){this._scrollDispatcher=i,this._ngZone=e,this._viewportRuler=t,this._config=r}attach(i){this._overlayRef,this._overlayRef=i}enable(){if(this._scrollSubscription)return;let i=this._scrollDispatcher.scrolled(0).pipe(rn(e=>!e||!this._overlayRef.overlayElement.contains(e.getElementRef().nativeElement)));this._config&&this._config.threshold&&this._config.threshold>1?(this._initialScrollPosition=this._viewportRuler.getViewportScrollPosition().top,this._scrollSubscription=i.subscribe(()=>{let e=this._viewportRuler.getViewportScrollPosition().top;Math.abs(e-this._initialScrollPosition)>this._config.threshold?this._detach():this._overlayRef.updatePosition()})):this._scrollSubscription=i.subscribe(this._detach)}disable(){this._scrollSubscription&&(this._scrollSubscription.unsubscribe(),this._scrollSubscription=null)}detach(){this.disable(),this._overlayRef=null}_detach=()=>{this.disable(),this._overlayRef.hasAttached()&&this._ngZone.run(()=>this._overlayRef.detach())}};var Oi=class{enable(){}disable(){}attach(){}};function Da(n,i){return i.some(e=>{let t=n.bottom<e.top,r=n.top>e.bottom,o=n.right<e.left,a=n.left>e.right;return t||r||o||a})}function Bl(n,i){return i.some(e=>{let t=n.top<e.top,r=n.bottom>e.bottom,o=n.left<e.left,a=n.right>e.right;return t||r||o||a})}function Ft(n,i){return new Yr(n.get(Gt),n.get(Tt),n.get(z),i)}var Yr=class{_scrollDispatcher;_viewportRuler;_ngZone;_config;_scrollSubscription=null;_overlayRef;constructor(i,e,t,r){this._scrollDispatcher=i,this._viewportRuler=e,this._ngZone=t,this._config=r}attach(i){this._overlayRef,this._overlayRef=i}enable(){if(!this._scrollSubscription){let i=this._config?this._config.scrollThrottle:0;this._scrollSubscription=this._scrollDispatcher.scrolled(i).subscribe(()=>{if(this._overlayRef.updatePosition(),this._config&&this._config.autoClose){let e=this._overlayRef.overlayElement.getBoundingClientRect(),{width:t,height:r}=this._viewportRuler.getViewportSize();Da(e,[{width:t,height:r,bottom:r,right:t,top:0,left:0}])&&(this.disable(),this._ngZone.run(()=>this._overlayRef.detach()))}})}}disable(){this._scrollSubscription&&(this._scrollSubscription.unsubscribe(),this._scrollSubscription=null)}detach(){this.disable(),this._overlayRef=null}};var Wl=(()=>{class n{_injector=I(le);noop=()=>new Oi;close=e=>Gl(this._injector,e);block=()=>zn(this._injector);reposition=e=>Ft(this._injector,e);static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var ht=class{positionStrategy;scrollStrategy=new Oi;panelClass=``;hasBackdrop=!1;backdropClass=`cdk-overlay-dark-backdrop`;disableAnimations;width;height;minWidth;minHeight;maxWidth;maxHeight;direction;disposeOnNavigation=!1;usePopover;eventPredicate;constructor(i){if(i){let e=Object.keys(i);for(let t of e)i[t]!==void 0&&(this[t]=i[t])}}};var Xr=class{connectionPair;scrollableViewProperties;constructor(i,e){this.connectionPair=i,this.scrollableViewProperties=e}};var Yl=(()=>{class n{_attachedOverlays=[];_document=I(Bo);_isAttached=!1;ngOnDestroy(){this.detach()}add(e){this.remove(e),this._attachedOverlays.push(e)}remove(e){let t=this._attachedOverlays.indexOf(e);t>-1&&this._attachedOverlays.splice(t,1),this._attachedOverlays.length===0&&this.detach()}canReceiveEvent(e,t,r){return r.observers.length<1?!1:e.eventPredicate?e.eventPredicate(t):!0}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Xl=(()=>{class n extends Yl{_ngZone=I(z);_renderer=I(mr$1).createRenderer(null,null);_cleanupKeydown;add(e){super.add(e),this._isAttached||(this._ngZone.runOutsideAngular(()=>{this._cleanupKeydown=this._renderer.listen(`body`,`keydown`,this._keydownListener)}),this._isAttached=!0)}detach(){this._isAttached&&(this._cleanupKeydown?.(),this._isAttached=!1)}_keydownListener=e=>{let t=this._attachedOverlays;for(let r=t.length-1;r>-1;r--){let o=t[r];if(this.canReceiveEvent(o,e,o._keydownEvents)){this._ngZone.run(()=>o._keydownEvents.next(e));break}}};static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Kl=(()=>{class n extends Yl{_platform=I(J);_ngZone=I(z);_renderer=I(mr$1).createRenderer(null,null);_cursorOriginalValue;_cursorStyleIsSet=!1;_pointerDownEventTarget=null;_cleanups;add(e){if(super.add(e),!this._isAttached){let t=this._document.body,r={capture:!0},o=this._renderer;this._cleanups=this._ngZone.runOutsideAngular(()=>[o.listen(t,`pointerdown`,this._pointerDownListener,r),o.listen(t,`click`,this._clickListener,r),o.listen(t,`auxclick`,this._clickListener,r),o.listen(t,`contextmenu`,this._clickListener,r)]),this._platform.IOS&&!this._cursorStyleIsSet&&(this._cursorOriginalValue=t.style.cursor,t.style.cursor=`pointer`,this._cursorStyleIsSet=!0),this._isAttached=!0}}detach(){this._isAttached&&(this._cleanups?.forEach(e=>e()),this._cleanups=void 0,this._platform.IOS&&this._cursorStyleIsSet&&(this._document.body.style.cursor=this._cursorOriginalValue,this._cursorStyleIsSet=!1),this._isAttached=!1)}_pointerDownListener=e=>{this._pointerDownEventTarget=Ie(e)};_clickListener=e=>{let t=Ie(e),r=e.type===`click`&&this._pointerDownEventTarget?this._pointerDownEventTarget:t;this._pointerDownEventTarget=null;let o=this._attachedOverlays.slice();for(let a=o.length-1;a>-1;a--){let s=o[a],c=s._outsidePointerEvents;if(!(!s.hasAttached()||!this.canReceiveEvent(s,e,c))){if(zl(s.overlayElement,t)||zl(s.overlayElement,r))break;this._ngZone?this._ngZone.run(()=>c.next(e)):c.next(e)}}};static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();function zl(n,i){let e=typeof ShadowRoot<`u`&&ShadowRoot,t=i;for(;t;){if(t===n)return!0;t=e&&t instanceof ShadowRoot?t.host:t.parentNode}return!1}var ql=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵcmp=LI({type:n,selectors:[[`ng-component`]],hostAttrs:[`cdk-overlay-style-loader`,``],decls:0,vars:0,template:function(t,r){},styles:[`.cdk-overlay-container, .cdk-global-overlay-wrapper {
  pointer-events: none;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
}

.cdk-overlay-container {
  position: fixed;
}
@layer cdk-overlay {
  .cdk-overlay-container {
    z-index: 1000;
  }
}
.cdk-overlay-container:empty {
  display: none;
}

.cdk-global-overlay-wrapper {
  display: flex;
  position: absolute;
}
@layer cdk-overlay {
  .cdk-global-overlay-wrapper {
    z-index: 1000;
  }
}

.cdk-overlay-pane {
  position: absolute;
  pointer-events: auto;
  box-sizing: border-box;
  display: flex;
  max-width: 100%;
  max-height: 100%;
}
@layer cdk-overlay {
  .cdk-overlay-pane {
    z-index: 1000;
  }
}

.cdk-overlay-backdrop {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  pointer-events: auto;
  -webkit-tap-highlight-color: transparent;
  opacity: 0;
  touch-action: manipulation;
}
@layer cdk-overlay {
  .cdk-overlay-backdrop {
    z-index: 1000;
    transition: opacity 400ms cubic-bezier(0.25, 0.8, 0.25, 1);
  }
}
@media (prefers-reduced-motion) {
  .cdk-overlay-backdrop {
    transition-duration: 1ms;
  }
}

.cdk-overlay-backdrop-showing {
  opacity: 1;
}
@media (forced-colors: active) {
  .cdk-overlay-backdrop-showing {
    opacity: 0.6;
  }
}

@layer cdk-overlay {
  .cdk-overlay-dark-backdrop {
    background: rgba(0, 0, 0, 0.32);
  }
}

.cdk-overlay-transparent-backdrop {
  transition: visibility 1ms linear, opacity 1ms linear;
  visibility: hidden;
  opacity: 1;
}
.cdk-overlay-transparent-backdrop.cdk-overlay-backdrop-showing, .cdk-high-contrast-active .cdk-overlay-transparent-backdrop {
  opacity: 0;
  visibility: visible;
}

.cdk-overlay-backdrop-noop-animation {
  transition: none;
}

.cdk-overlay-connected-position-bounding-box {
  position: absolute;
  display: flex;
  flex-direction: column;
  min-width: 1px;
  min-height: 1px;
}
@layer cdk-overlay {
  .cdk-overlay-connected-position-bounding-box {
    z-index: 1000;
  }
}

.cdk-global-scrollblock {
  position: fixed;
  width: 100%;
  overflow-y: scroll;
}

.cdk-overlay-popover {
  background: none;
  border: none;
  padding: 0;
  outline: 0;
  overflow: visible;
  position: fixed;
  pointer-events: none;
  white-space: normal;
  color: inherit;
  text-decoration: none;
  width: 100%;
  height: 100%;
  inset: auto;
  top: 0;
  left: 0;
}
.cdk-overlay-popover::backdrop {
  display: none;
}
.cdk-overlay-popover .cdk-overlay-backdrop {
  position: fixed;
  z-index: auto;
}
`],encapsulation:2})}return n})();var Zr=(()=>{class n{_platform=I(J);_containerElement;_document=I(Bo);_styleLoader=I(Se);ngOnDestroy(){this._containerElement?.remove()}getContainerElement(){return this._loadStyles(),this._containerElement||this._createContainer(),this._containerElement}_createContainer(){let e=`cdk-overlay-container`;if(this._platform.isBrowser||xa()){let r=this._document.querySelectorAll(`.${e}[platform="server"], .${e}[platform="test"]`);for(let o=0;o<r.length;o++)r[o].remove()}let t=this._document.createElement(`div`);t.classList.add(e),xa()?t.setAttribute(`platform`,`test`):this._platform.isBrowser||t.setAttribute(`platform`,`server`),this._document.body.appendChild(t),this._containerElement=t}_loadStyles(){this._styleLoader.load(ql)}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Ea=class{_renderer;_ngZone;element;_cleanupClick;_cleanupTransitionEnd;_fallbackTimeout;constructor(i,e,t,r){this._renderer=e,this._ngZone=t,this.element=i.createElement(`div`),this.element.classList.add(`cdk-overlay-backdrop`),this._cleanupClick=e.listen(this.element,`click`,r)}detach(){this._ngZone.runOutsideAngular(()=>{let i=this.element;clearTimeout(this._fallbackTimeout),this._cleanupTransitionEnd?.(),this._cleanupTransitionEnd=this._renderer.listen(i,`transitionend`,this.dispose),this._fallbackTimeout=setTimeout(this.dispose,500),i.style.pointerEvents=`none`,i.classList.remove(`cdk-overlay-backdrop-showing`)})}dispose=()=>{clearTimeout(this._fallbackTimeout),this._cleanupClick?.(),this._cleanupTransitionEnd?.(),this._cleanupClick=this._cleanupTransitionEnd=this._fallbackTimeout=void 0,this.element.remove()}};function Ma(n){return n&&n.nodeType===1}var ka=oa([]);var Vn=class{_portalOutlet;_host;_pane;_config;_ngZone;_keyboardDispatcher;_document;_location;_outsideClickDispatcher;_animationsDisabled;_injector;_renderer;_backdropClick=new te$1;_attachments=new te$1;_detachments=new te$1;_positionStrategy;_scrollStrategy;_locationChanges;_backdropRef=null;_detachContentMutationObserver;_detachContentAfterRenderRef;_disposed=!1;_previousHostParent;_keydownEvents=new te$1;_outsidePointerEvents=new te$1;_afterNextRenderRef;constructor(i,e,t,r,o,a,s,c,d,m=!1,_,k){this._portalOutlet=i,this._host=e,this._pane=t,this._config=r,this._ngZone=o,this._keyboardDispatcher=a,this._document=s,this._location=c,this._outsideClickDispatcher=d,this._animationsDisabled=m,this._injector=_,this._renderer=k,r.scrollStrategy&&(this._scrollStrategy=r.scrollStrategy,this._scrollStrategy.attach(this)),this._positionStrategy=r.positionStrategy}get overlayElement(){return this._pane}get backdropElement(){return this._backdropRef?.element||null}get hostElement(){return this._host}get eventPredicate(){return this._config?.eventPredicate||null}attach(i){if(this._disposed)return null;this._attachHost();let e=this._portalOutlet.attach(i);if(this._positionStrategy?.attach(this),this._updateStackingOrder(),this._updateElementSize(),this._updateElementDirection(),Ow(()=>{ka.update(t=>t.includes(this)?t:[...t,this])}),this._scrollStrategy&&this._scrollStrategy.enable(),this._afterNextRenderRef?.destroy(),this._afterNextRenderRef=Hv(()=>{this.hasAttached()&&this.updatePosition()},{injector:this._injector}),this._togglePointerEvents(!0),this._config.hasBackdrop&&this._attachBackdrop(),this._config.panelClass&&this._toggleClasses(this._pane,this._config.panelClass,!0),this._attachments.next(),this._completeDetachContent(),this._keyboardDispatcher.add(this),this._config.disposeOnNavigation===!0||this._config.disposeOnNavigation===`pop-state`){let t=this._location.subscribe(()=>this.dispose());this._locationChanges=()=>t.unsubscribe()}else this._config.disposeOnNavigation===`url-change`&&(this._locationChanges=this._location.onUrlChange(()=>this.dispose()));return this._outsideClickDispatcher.add(this),typeof e?.onDestroy==`function`&&e.onDestroy(()=>{this.hasAttached()&&this._ngZone.runOutsideAngular(()=>Promise.resolve().then(()=>this.detach()))}),e}detach(){if(!this.hasAttached())return;this.detachBackdrop(),this._togglePointerEvents(!1),this._positionStrategy&&this._positionStrategy.detach&&this._positionStrategy.detach(),this._scrollStrategy&&this._scrollStrategy.disable();let i=this._portalOutlet.detach();return this._detachments.next(),this._completeDetachContent(),this._keyboardDispatcher.remove(this),this._detachContentWhenEmpty(),this._locationChanges?.(),this._outsideClickDispatcher.remove(this),Ow(()=>{ka.update(e=>e.filter(t=>t!==this))}),i}dispose(){if(this._disposed)return;let i=this.hasAttached();this._positionStrategy&&this._positionStrategy.dispose(),this._disposeScrollStrategy(),this._backdropRef?.dispose(),this._locationChanges?.(),this._keyboardDispatcher.remove(this),this._portalOutlet.dispose(),this._attachments.complete(),this._backdropClick.complete(),this._keydownEvents.complete(),this._outsidePointerEvents.complete(),this._outsideClickDispatcher.remove(this),this._host?.remove(),this._afterNextRenderRef?.destroy(),this._previousHostParent=this._pane=this._host=this._backdropRef=null,i&&this._detachments.next(),this._detachments.complete(),this._completeDetachContent(),this._disposed=!0,Ow(()=>{ka.update(e=>e.filter(t=>t!==this))})}hasAttached(){return this._portalOutlet.hasAttached()}backdropClick(){return this._backdropClick}attachments(){return this._attachments}detachments(){return this._detachments}keydownEvents(){return this._keydownEvents}outsidePointerEvents(){return this._outsidePointerEvents}getConfig(){return this._config}updatePosition(){this._positionStrategy&&this._positionStrategy.apply()}updatePositionStrategy(i){i!==this._positionStrategy&&(this._positionStrategy&&this._positionStrategy.dispose(),this._positionStrategy=i,this.hasAttached()&&(i.attach(this),this.updatePosition()))}updateSize(i){this._config=$($({},this._config),i),this._updateElementSize()}setDirection(i){this._config=Y($({},this._config),{direction:i}),this._updateElementDirection()}addPanelClass(i){this._pane&&this._toggleClasses(this._pane,i,!0)}removePanelClass(i){this._pane&&this._toggleClasses(this._pane,i,!1)}getDirection(){let i=this._config.direction;return i?typeof i==`string`?i:i.value:`ltr`}updateScrollStrategy(i){i!==this._scrollStrategy&&(this._disposeScrollStrategy(),this._scrollStrategy=i,this.hasAttached()&&(i.attach(this),i.enable()))}_updateElementDirection(){this._host.setAttribute(`dir`,this.getDirection())}_updateElementSize(){if(!this._pane)return;let i=this._pane.style;i.width=ve(this._config.width),i.height=ve(this._config.height),i.minWidth=ve(this._config.minWidth),i.minHeight=ve(this._config.minHeight),i.maxWidth=ve(this._config.maxWidth),i.maxHeight=ve(this._config.maxHeight)}_togglePointerEvents(i){this._pane.style.pointerEvents=i?``:`none`}_attachHost(){if(!this._host.parentElement){let i=this._config.usePopover?this._positionStrategy?.getPopoverInsertionPoint?.():null;Ma(i)?i.after(this._host):i?.type===`parent`?i.element.appendChild(this._host):this._previousHostParent?.appendChild(this._host)}if(this._config.usePopover)try{this._host.showPopover()}catch(i){}}_attachBackdrop(){let i=`cdk-overlay-backdrop-showing`;this._backdropRef?.dispose(),this._backdropRef=new Ea(this._document,this._renderer,this._ngZone,e=>{this._backdropClick.next(e)}),this._animationsDisabled&&this._backdropRef.element.classList.add(`cdk-overlay-backdrop-noop-animation`),this._config.backdropClass&&this._toggleClasses(this._backdropRef.element,this._config.backdropClass,!0),this._config.usePopover?this._host.prepend(this._backdropRef.element):this._host.parentElement.insertBefore(this._backdropRef.element,this._host),!this._animationsDisabled&&typeof requestAnimationFrame<`u`?this._ngZone.runOutsideAngular(()=>{requestAnimationFrame(()=>this._backdropRef?.element.classList.add(i))}):this._backdropRef.element.classList.add(i)}_updateStackingOrder(){!this._config.usePopover&&this._host.nextSibling&&this._host.parentNode.appendChild(this._host)}detachBackdrop(){this._animationsDisabled?(this._backdropRef?.dispose(),this._backdropRef=null):this._backdropRef?.detach()}_toggleClasses(i,e,t){let r=Pn(e||[]).filter(o=>!!o);r.length&&(t?i.classList.add(...r):i.classList.remove(...r))}_detachContentWhenEmpty(){let i=!1;try{this._detachContentAfterRenderRef=Hv(()=>{i=!0,this._detachContent()},{injector:this._injector})}catch(e){if(i)throw e;this._detachContent()}globalThis.MutationObserver&&this._pane&&(this._detachContentMutationObserver||=new globalThis.MutationObserver(()=>{this._detachContent()}),this._detachContentMutationObserver.observe(this._pane,{childList:!0}))}_detachContent(){(!this._pane||!this._host||this._pane.children.length===0)&&(this._pane&&this._config.panelClass&&this._toggleClasses(this._pane,this._config.panelClass,!1),this._host&&this._host.parentElement&&(this._previousHostParent=this._host.parentElement,this._host.remove()),this._completeDetachContent())}_completeDetachContent(){this._detachContentAfterRenderRef?.destroy(),this._detachContentAfterRenderRef=void 0,this._detachContentMutationObserver?.disconnect()}_disposeScrollStrategy(){let i=this._scrollStrategy;i?.disable(),i?.detach?.()}};var jl=`cdk-overlay-connected-position-bounding-box`;var Gu=/([A-Za-z%]+)$/;function pn(n,i){return new Kr(i,n.get(Tt),n.get(Bo),n.get(J),n.get(Zr))}var Kr=class{_viewportRuler;_document;_platform;_overlayContainer;_overlayRef;_isInitialRender=!1;_lastBoundingBoxSize={width:0,height:0};_isPushed=!1;_canPush=!0;_growAfterOpen=!1;_hasFlexibleDimensions=!0;_positionLocked=!1;_originRect;_overlayRect;_viewportRect;_containerRect;_viewportMargin=0;_scrollables=[];_preferredPositions=[];_origin;_pane;_isDisposed=!1;_boundingBox=null;_lastPosition=null;_lastScrollVisibility=null;_positionChanges=new te$1;_resizeSubscription=q.EMPTY;_offsetX=0;_offsetY=0;_transformOriginSelector;_appliedPanelClasses=[];_previousPushAmount=null;_popoverLocation=`global`;positionChanges=this._positionChanges;get positions(){return this._preferredPositions}constructor(i,e,t,r,o){this._viewportRuler=e,this._document=t,this._platform=r,this._overlayContainer=o,this.setOrigin(i)}attach(i){this._overlayRef&&this._overlayRef,this._validatePositions(),i.hostElement.classList.add(jl),this._overlayRef=i,this._boundingBox=i.hostElement,this._pane=i.overlayElement,this._isDisposed=!1,this._isInitialRender=!0,this._lastPosition=null,this._resizeSubscription.unsubscribe(),this._resizeSubscription=this._viewportRuler.change().subscribe(()=>{this._isInitialRender=!0,this.apply()})}apply(){if(this._isDisposed||!this._platform.isBrowser)return;if(!this._isInitialRender&&this._positionLocked&&this._lastPosition){this.reapplyLastPosition();return}this._clearPanelClasses(),this._resetOverlayElementStyles(),this._resetBoundingBoxStyles(),this._viewportRect=this._getNarrowedViewportRect(),this._originRect=this._getOriginRect(),this._overlayRect=this._pane.getBoundingClientRect(),this._containerRect=this._getContainerRect();let i=this._originRect,e=this._overlayRect,t=this._viewportRect,r=this._containerRect,o=[],a;for(let s of this._preferredPositions){let c=this._getOriginPoint(i,r,s),d=this._getOverlayPoint(c,e,s),m=this._getOverlayFit(d,e,t,s);if(m.isCompletelyWithinViewport){this._isPushed=!1,this._applyPosition(s,c);return}if(this._canFitWithFlexibleDimensions(m,d,t)){o.push({position:s,origin:c,overlayRect:e,boundingBoxRect:this._calculateBoundingBoxRect(c,s)});continue}(!a||a.overlayFit.visibleArea<m.visibleArea)&&(a={overlayFit:m,overlayPoint:d,originPoint:c,position:s,overlayRect:e})}if(o.length){let s=null,c=-1;for(let d of o){let m=d.boundingBoxRect.width*d.boundingBoxRect.height*(d.position.weight||1);m>c&&(c=m,s=d)}this._isPushed=!1,this._applyPosition(s.position,s.origin);return}if(this._canPush){this._isPushed=!0,this._applyPosition(a.position,a.originPoint);return}this._applyPosition(a.position,a.originPoint)}detach(){this._clearPanelClasses(),this._lastPosition=null,this._previousPushAmount=null,this._resizeSubscription.unsubscribe()}dispose(){this._isDisposed||(this._boundingBox&&hn(this._boundingBox.style,{top:``,left:``,right:``,bottom:``,height:``,width:``,alignItems:``,justifyContent:``}),this._pane&&this._resetOverlayElementStyles(),this._overlayRef&&this._overlayRef.hostElement.classList.remove(jl),this.detach(),this._positionChanges.complete(),this._overlayRef=this._boundingBox=null,this._isDisposed=!0)}reapplyLastPosition(){if(this._isDisposed||!this._platform.isBrowser)return;let i=this._lastPosition;i?(this._originRect=this._getOriginRect(),this._overlayRect=this._pane.getBoundingClientRect(),this._viewportRect=this._getNarrowedViewportRect(),this._containerRect=this._getContainerRect(),this._applyPosition(i,this._getOriginPoint(this._originRect,this._containerRect,i))):this.apply()}withScrollableContainers(i){return this._scrollables=i,this}withPositions(i){return this._preferredPositions=i,i.indexOf(this._lastPosition)===-1&&(this._lastPosition=null),this._validatePositions(),this}withViewportMargin(i){return this._viewportMargin=i,this}withFlexibleDimensions(i=!0){return this._hasFlexibleDimensions=i,this}withGrowAfterOpen(i=!0){return this._growAfterOpen=i,this}withPush(i=!0){return this._canPush=i,this}withLockedPosition(i=!0){return this._positionLocked=i,this}setOrigin(i){return this._origin=i,this}withDefaultOffsetX(i){return this._offsetX=i,this}withDefaultOffsetY(i){return this._offsetY=i,this}withTransformOriginOn(i){return this._transformOriginSelector=i,this}withPopoverLocation(i){return this._popoverLocation=i,this}getPopoverInsertionPoint(){return this._popoverLocation===`global`?null:this._popoverLocation!==`inline`?this._popoverLocation:this._origin instanceof Dr?this._origin.nativeElement:Ma(this._origin)?this._origin:null}_getOriginPoint(i,e,t){let r;if(t.originX==`center`)r=i.left+i.width/2;else{let a=this._isRtl()?i.right:i.left,s=this._isRtl()?i.left:i.right;r=t.originX==`start`?a:s}e.left<0&&(r-=e.left);let o;return t.originY==`center`?o=i.top+i.height/2:o=t.originY==`top`?i.top:i.bottom,e.top<0&&(o-=e.top),{x:r,y:o}}_getOverlayPoint(i,e,t){let r;t.overlayX==`center`?r=-e.width/2:t.overlayX===`start`?r=this._isRtl()?-e.width:0:r=this._isRtl()?0:-e.width;let o;return t.overlayY==`center`?o=-e.height/2:o=t.overlayY==`top`?0:-e.height,{x:i.x+r,y:i.y+o}}_getOverlayFit(i,e,t,r){let o=Hl(e),{x:a,y:s}=i,c=this._getOffset(r,`x`),d=this._getOffset(r,`y`);c&&(a+=c),d&&(s+=d);let m=0-a,_=a+o.width-t.width,k=0-s,p=s+o.height-t.height,z=this._subtractOverflows(o.width,m,_),K=this._subtractOverflows(o.height,k,p),fe=z*K;return{visibleArea:fe,isCompletelyWithinViewport:o.width*o.height===fe,fitsInViewportVertically:K===o.height,fitsInViewportHorizontally:z==o.width}}_canFitWithFlexibleDimensions(i,e,t){if(this._hasFlexibleDimensions){let r=t.bottom-e.y,o=t.right-e.x,a=Ul(this._overlayRef.getConfig().minHeight),s=Ul(this._overlayRef.getConfig().minWidth),c=i.fitsInViewportVertically||a!=null&&a<=r,d=i.fitsInViewportHorizontally||s!=null&&s<=o;return c&&d}return!1}_pushOverlayOnScreen(i,e,t){if(this._previousPushAmount&&this._positionLocked)return{x:i.x+this._previousPushAmount.x,y:i.y+this._previousPushAmount.y};let r=Hl(e),o=this._viewportRect,a=Math.max(i.x+r.width-o.width,0),s=Math.max(i.y+r.height-o.height,0),c=Math.max(o.top-t.top-i.y,0),d=Math.max(o.left-t.left-i.x,0),m=0,_=0;return r.width<=o.width?m=d||-a:m=i.x<this._getViewportMarginStart()?o.left-t.left-i.x:0,r.height<=o.height?_=c||-s:_=i.y<this._getViewportMarginTop()?o.top-t.top-i.y:0,this._previousPushAmount={x:m,y:_},{x:i.x+m,y:i.y+_}}_applyPosition(i,e){if(this._setTransformOrigin(i),this._setOverlayElementStyles(e,i),this._setBoundingBoxStyles(e,i),i.panelClass&&this._addPanelClasses(i.panelClass),this._positionChanges.observers.length){let t=this._getScrollVisibility();if(i!==this._lastPosition||!this._lastScrollVisibility||!Wu(this._lastScrollVisibility,t)){let r=new Xr(i,t);this._positionChanges.next(r)}this._lastScrollVisibility=t}this._lastPosition=i,this._isInitialRender=!1}_setTransformOrigin(i){if(!this._transformOriginSelector)return;let e=this._boundingBox.querySelectorAll(this._transformOriginSelector),t,r=i.overlayY;i.overlayX===`center`?t=`center`:this._isRtl()?t=i.overlayX===`start`?`right`:`left`:t=i.overlayX===`start`?`left`:`right`;for(let o=0;o<e.length;o++)e[o].style.transformOrigin=`${t} ${r}`}_calculateBoundingBoxRect(i,e){let t=this._viewportRect,r=this._isRtl(),o,a,s;if(e.overlayY===`top`)a=i.y,o=t.height-a+this._getViewportMarginBottom();else if(e.overlayY===`bottom`)s=t.height-i.y+this._getViewportMarginTop()+this._getViewportMarginBottom(),o=t.height-s+this._getViewportMarginTop();else{let p=Math.min(t.bottom-i.y+t.top,i.y),z=this._lastBoundingBoxSize.height;o=p*2,a=i.y-p,o>z&&!this._isInitialRender&&!this._growAfterOpen&&(a=i.y-z/2)}let c=e.overlayX===`start`&&!r||e.overlayX===`end`&&r,d=e.overlayX===`end`&&!r||e.overlayX===`start`&&r,m,_,k;if(d)k=t.width-i.x+this._getViewportMarginStart()+this._getViewportMarginEnd(),m=i.x-this._getViewportMarginStart();else if(c)_=i.x,m=t.right-i.x-this._getViewportMarginEnd();else{let p=Math.min(t.right-i.x+t.left,i.x),z=this._lastBoundingBoxSize.width;m=p*2,_=i.x-p,m>z&&!this._isInitialRender&&!this._growAfterOpen&&(_=i.x-z/2)}return{top:a,left:_,bottom:s,right:k,width:m,height:o}}_setBoundingBoxStyles(i,e){let t=this._calculateBoundingBoxRect(i,e);!this._isInitialRender&&!this._growAfterOpen&&(t.height=Math.min(t.height,this._lastBoundingBoxSize.height),t.width=Math.min(t.width,this._lastBoundingBoxSize.width));let r={};if(this._hasExactPosition())r.top=r.left=`0`,r.bottom=r.right=`auto`,r.maxHeight=r.maxWidth=``,r.width=r.height=`100%`;else{let o=this._overlayRef.getConfig().maxHeight,a=this._overlayRef.getConfig().maxWidth;r.width=ve(t.width),r.height=ve(t.height),r.top=ve(t.top)||`auto`,r.bottom=ve(t.bottom)||`auto`,r.left=ve(t.left)||`auto`,r.right=ve(t.right)||`auto`,e.overlayX===`center`?r.alignItems=`center`:r.alignItems=e.overlayX===`end`?`flex-end`:`flex-start`,e.overlayY===`center`?r.justifyContent=`center`:r.justifyContent=e.overlayY===`bottom`?`flex-end`:`flex-start`,o&&(r.maxHeight=ve(o)),a&&(r.maxWidth=ve(a))}this._lastBoundingBoxSize=t,hn(this._boundingBox.style,r)}_resetBoundingBoxStyles(){hn(this._boundingBox.style,{top:`0`,left:`0`,right:`0`,bottom:`0`,height:``,width:``,alignItems:``,justifyContent:``})}_resetOverlayElementStyles(){hn(this._pane.style,{top:``,left:``,bottom:``,right:``,position:``,transform:``})}_setOverlayElementStyles(i,e){let t={},r=this._hasExactPosition(),o=this._hasFlexibleDimensions,a=this._overlayRef.getConfig();if(r){let m=this._viewportRuler.getViewportScrollPosition();hn(t,this._getExactOverlayY(e,i,m)),hn(t,this._getExactOverlayX(e,i,m))}else t.position=`static`;let s=``,c=this._getOffset(e,`x`),d=this._getOffset(e,`y`);c&&(s+=`translateX(${c}px) `),d&&(s+=`translateY(${d}px)`),t.transform=s.trim(),a.maxHeight&&(r?t.maxHeight=ve(a.maxHeight):o&&(t.maxHeight=``)),a.maxWidth&&(r?t.maxWidth=ve(a.maxWidth):o&&(t.maxWidth=``)),hn(this._pane.style,t)}_getExactOverlayY(i,e,t){let r={top:``,bottom:``},o=this._getOverlayPoint(e,this._overlayRect,i);if(this._isPushed&&(o=this._pushOverlayOnScreen(o,this._overlayRect,t)),i.overlayY===`bottom`)r.bottom=`${this._document.documentElement.clientHeight-(o.y+this._overlayRect.height)}px`;else r.top=ve(o.y);return r}_getExactOverlayX(i,e,t){let r={left:``,right:``},o=this._getOverlayPoint(e,this._overlayRect,i);this._isPushed&&(o=this._pushOverlayOnScreen(o,this._overlayRect,t));let a;if(this._isRtl()?a=i.overlayX===`end`?`left`:`right`:a=i.overlayX===`end`?`right`:`left`,a===`right`)r.right=`${this._document.documentElement.clientWidth-(o.x+this._overlayRect.width)}px`;else r.left=ve(o.x);return r}_getScrollVisibility(){let i=this._getOriginRect(),e=this._pane.getBoundingClientRect(),t=this._scrollables.map(r=>r.getElementRef().nativeElement.getBoundingClientRect());return{isOriginClipped:Bl(i,t),isOriginOutsideView:Da(i,t),isOverlayClipped:Bl(e,t),isOverlayOutsideView:Da(e,t)}}_subtractOverflows(i,...e){return e.reduce((t,r)=>t-Math.max(r,0),i)}_getNarrowedViewportRect(){let i=this._document.documentElement.clientWidth,e=this._document.documentElement.clientHeight,t=this._viewportRuler.getViewportScrollPosition();return{top:t.top+this._getViewportMarginTop(),left:t.left+this._getViewportMarginStart(),right:t.left+i-this._getViewportMarginEnd(),bottom:t.top+e-this._getViewportMarginBottom(),width:i-this._getViewportMarginStart()-this._getViewportMarginEnd(),height:e-this._getViewportMarginTop()-this._getViewportMarginBottom()}}_isRtl(){return this._overlayRef.getDirection()===`rtl`}_hasExactPosition(){return!this._hasFlexibleDimensions||this._isPushed}_getOffset(i,e){return e===`x`?i.offsetX==null?this._offsetX:i.offsetX:i.offsetY==null?this._offsetY:i.offsetY}_validatePositions(){}_addPanelClasses(i){this._pane&&Pn(i).forEach(e=>{e!==``&&this._appliedPanelClasses.indexOf(e)===-1&&(this._appliedPanelClasses.push(e),this._pane.classList.add(e))})}_clearPanelClasses(){this._pane&&(this._appliedPanelClasses.forEach(i=>{this._pane.classList.remove(i)}),this._appliedPanelClasses=[])}_getViewportMarginStart(){return typeof this._viewportMargin==`number`?this._viewportMargin:this._viewportMargin?.start??0}_getViewportMarginEnd(){return typeof this._viewportMargin==`number`?this._viewportMargin:this._viewportMargin?.end??0}_getViewportMarginTop(){return typeof this._viewportMargin==`number`?this._viewportMargin:this._viewportMargin?.top??0}_getViewportMarginBottom(){return typeof this._viewportMargin==`number`?this._viewportMargin:this._viewportMargin?.bottom??0}_getOriginRect(){let i=this._origin;if(i instanceof Dr)return i.nativeElement.getBoundingClientRect();if(i instanceof Element)return i.getBoundingClientRect();let e=i.width||0,t=i.height||0;return{top:i.y,bottom:i.y+t,left:i.x,right:i.x+e,height:t,width:e}}_getContainerRect(){let i=this._overlayRef.getConfig().usePopover&&this._popoverLocation!==`global`,e=this._overlayContainer.getContainerElement();i&&(e.style.display=`block`);let t=e.getBoundingClientRect();return i&&(e.style.display=``),t}};function hn(n,i){for(let e in i)Object.hasOwn(i,e)&&(n[e]=i[e]);return n}function Ul(n){if(typeof n!=`number`&&n!=null){let[i,e]=n.split(Gu);return!e||e===`px`?parseFloat(i):null}return n||null}function Hl(n){return{top:Math.floor(n.top),right:Math.floor(n.right),bottom:Math.floor(n.bottom),left:Math.floor(n.left),width:Math.floor(n.width),height:Math.floor(n.height)}}function Wu(n,i){return n===i?!0:n.isOriginClipped===i.isOriginClipped&&n.isOriginOutsideView===i.isOriginOutsideView&&n.isOverlayClipped===i.isOverlayClipped&&n.isOverlayOutsideView===i.isOverlayOutsideView}var $l=`cdk-global-overlay-wrapper`;function Xt(n){return new qr}var qr=class{_overlayRef;_cssPosition=`static`;_topOffset=``;_bottomOffset=``;_alignItems=``;_xPosition=``;_xOffset=``;_width=``;_height=``;_isDisposed=!1;attach(i){let e=i.getConfig();this._overlayRef=i,this._width&&!e.width&&i.updateSize({width:this._width}),this._height&&!e.height&&i.updateSize({height:this._height}),i.hostElement.classList.add($l),this._isDisposed=!1}top(i=``){return this._bottomOffset=``,this._topOffset=i,this._alignItems=`flex-start`,this}left(i=``){return this._xOffset=i,this._xPosition=`left`,this}bottom(i=``){return this._topOffset=``,this._bottomOffset=i,this._alignItems=`flex-end`,this}right(i=``){return this._xOffset=i,this._xPosition=`right`,this}start(i=``){return this._xOffset=i,this._xPosition=`start`,this}end(i=``){return this._xOffset=i,this._xPosition=`end`,this}width(i=``){return this._overlayRef?this._overlayRef.updateSize({width:i}):this._width=i,this}height(i=``){return this._overlayRef?this._overlayRef.updateSize({height:i}):this._height=i,this}centerHorizontally(i=``){return this.left(i),this._xPosition=`center`,this}centerVertically(i=``){return this.top(i),this._alignItems=`center`,this}apply(){if(!this._overlayRef||!this._overlayRef.hasAttached())return;let i=this._overlayRef.overlayElement.style,e=this._overlayRef.hostElement.style,{width:r,height:o,maxWidth:a,maxHeight:s}=this._overlayRef.getConfig(),c=(r===`100%`||r===`100vw`)&&(!a||a===`100%`||a===`100vw`),d=(o===`100%`||o===`100vh`)&&(!s||s===`100%`||s===`100vh`),m=this._xPosition,_=this._xOffset,k=this._overlayRef.getConfig().direction===`rtl`,p=``,z=``,K=``;c?K=`flex-start`:m===`center`?(K=`center`,k?z=_:p=_):k?m===`left`||m===`end`?(K=`flex-end`,p=_):(m===`right`||m===`start`)&&(K=`flex-start`,z=_):m===`left`||m===`start`?(K=`flex-start`,p=_):(m===`right`||m===`end`)&&(K=`flex-end`,z=_),i.position=this._cssPosition,i.marginLeft=c?`0`:p,i.marginTop=d?`0`:this._topOffset,i.marginBottom=this._bottomOffset,i.marginRight=c?`0`:z,e.justifyContent=K,e.alignItems=d?`flex-start`:this._alignItems}dispose(){if(this._isDisposed||!this._overlayRef)return;let i=this._overlayRef.overlayElement.style,e=this._overlayRef.hostElement,t=e.style;e.classList.remove($l),t.justifyContent=t.alignItems=i.marginTop=i.marginBottom=i.marginLeft=i.marginRight=i.position=``,this._overlayRef=null,this._isDisposed=!0}};var Zl=(()=>{class n{_injector=I(le);global(){return Xt()}flexibleConnectedTo(e){return pn(this._injector,e)}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Fi=new S(`OVERLAY_DEFAULT_CONFIG`);function pt(n,i){n.get(Se).load(ql);let e=n.get(Zr),t=n.get(Bo),r=n.get(me),o=n.get(Zt$1),a=n.get(Ne),s=n.get(La$1,null,{optional:!0})||n.get(mr$1).createRenderer(null,null),c=new ht(i),d=n.get(Fi,null,{optional:!0})?.usePopover??!0;c.direction=c.direction||a.value,!t.body||!(`showPopover`in t.body)?c.usePopover=!1:c.usePopover=i?.usePopover??d;let m=t.createElement(`div`),_=t.createElement(`div`);m.id=r.getId(`cdk-overlay-`),m.classList.add(`cdk-overlay-pane`),_.appendChild(m),c.usePopover&&(_.setAttribute(`popover`,`manual`),_.classList.add(`cdk-overlay-popover`));let k=c.usePopover?c.positionStrategy?.getPopoverInsertionPoint?.():null;return Ma(k)?k.after(_):k?.type===`parent`?k.element.appendChild(_):e.getContainerElement().appendChild(_),new Vn(new Ri(m,o,n),_,m,c,n.get(z),n.get(Xl),t,n.get(Or),n.get(Kl),i?.disableAnimations??n.get(Bm$1,null,{optional:!0})===`NoopAnimations`,n.get(De),s)}var Ql=(()=>{class n{scrollStrategies=I(Wl);_positionBuilder=I(Zl);_injector=I(le);create(e){return pt(this._injector,e)}position(){return this._positionBuilder}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Yu=[{originX:`start`,originY:`bottom`,overlayX:`start`,overlayY:`top`},{originX:`start`,originY:`top`,overlayX:`start`,overlayY:`bottom`},{originX:`end`,originY:`top`,overlayX:`end`,overlayY:`bottom`},{originX:`end`,originY:`bottom`,overlayX:`end`,overlayY:`top`}];var Xu=new S(`cdk-connected-overlay-scroll-strategy`,{providedIn:`root`,factory:()=>{let n=I(le);return()=>Ft(n)}});var Bn=(()=>{class n{elementRef=I(Dr);static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`cdk-overlay-origin`,``],[``,`overlay-origin`,``],[``,`cdkOverlayOrigin`,``]],exportAs:[`cdkOverlayOrigin`]})}return n})();var Jl=new S(`cdk-connected-overlay-default-config`);var Qr=(()=>{class n{_dir=I(Ne,{optional:!0});_injector=I(le);_overlayRef;_templatePortal;_backdropSubscription=q.EMPTY;_attachSubscription=q.EMPTY;_detachSubscription=q.EMPTY;_positionSubscription=q.EMPTY;_offsetX;_offsetY;_position;_scrollStrategyFactory=I(Xu);_ngZone=I(z);origin;positions;positionStrategy;get offsetX(){return this._offsetX}set offsetX(e){this._offsetX=e,this._position&&this._updatePositionStrategy(this._position)}get offsetY(){return this._offsetY}set offsetY(e){this._offsetY=e,this._position&&this._updatePositionStrategy(this._position)}width;height;minWidth;minHeight;backdropClass;panelClass;viewportMargin=0;scrollStrategy;open=!1;disableClose=!1;transformOriginSelector;hasBackdrop=!1;lockPosition=!1;flexibleDimensions=!1;growAfterOpen=!1;push=!1;disposeOnNavigation=!1;usePopover;matchWidth=!1;set _config(e){typeof e!=`string`&&this._assignConfig(e)}backdropClick=new Fe;positionChange=new Fe;attach=new Fe;detach=new Fe;overlayKeydown=new Fe;overlayOutsideClick=new Fe;constructor(){let e=I(gr),t=I(xi$1),r=I(Jl,{optional:!0}),o=I(Fi,{optional:!0});this.usePopover=o?.usePopover===!1?null:`global`,this._templatePortal=new rt(e,t),this.scrollStrategy=this._scrollStrategyFactory(),r&&this._assignConfig(r)}get overlayRef(){return this._overlayRef}get dir(){return this._dir?this._dir.value:`ltr`}ngOnDestroy(){this._attachSubscription.unsubscribe(),this._detachSubscription.unsubscribe(),this._backdropSubscription.unsubscribe(),this._positionSubscription.unsubscribe(),this._overlayRef?.dispose()}ngOnChanges(e){this._position&&(this._updatePositionStrategy(this._position),this._overlayRef?.updateSize({width:this._getWidth(),minWidth:this.minWidth,height:this.height,minHeight:this.minHeight}),e.origin&&this.open&&this._position.apply()),e.open&&(this.open?this.attachOverlay():this.detachOverlay())}_createOverlay(){(!this.positions||!this.positions.length)&&(this.positions=Yu);let e=this._overlayRef=pt(this._injector,this._buildConfig());this._attachSubscription=e.attachments().subscribe(()=>this.attach.emit()),this._detachSubscription=e.detachments().subscribe(()=>this.detach.emit()),e.keydownEvents().subscribe(t=>{this.overlayKeydown.next(t),t.keyCode===27&&!this.disableClose&&!Me(t)&&(t.preventDefault(),this.detachOverlay())}),this._overlayRef.outsidePointerEvents().subscribe(t=>{let r=this._getOriginElement(),o=Ie(t);(!r||r!==o&&!r.contains(o))&&this.overlayOutsideClick.next(t)})}_buildConfig(){let e=this._position=this.positionStrategy||this._createPositionStrategy(),t=new ht({direction:this._dir||`ltr`,positionStrategy:e,scrollStrategy:this.scrollStrategy,hasBackdrop:this.hasBackdrop,disposeOnNavigation:this.disposeOnNavigation,usePopover:!!this.usePopover});return(this.height||this.height===0)&&(t.height=this.height),(this.minWidth||this.minWidth===0)&&(t.minWidth=this.minWidth),(this.minHeight||this.minHeight===0)&&(t.minHeight=this.minHeight),this.backdropClass&&(t.backdropClass=this.backdropClass),this.panelClass&&(t.panelClass=this.panelClass),t}_updatePositionStrategy(e){let t=this.positions.map(r=>({originX:r.originX,originY:r.originY,overlayX:r.overlayX,overlayY:r.overlayY,offsetX:r.offsetX||this.offsetX,offsetY:r.offsetY||this.offsetY,panelClass:r.panelClass||void 0}));return e.setOrigin(this._getOrigin()).withPositions(t).withFlexibleDimensions(this.flexibleDimensions).withPush(this.push).withGrowAfterOpen(this.growAfterOpen).withViewportMargin(this.viewportMargin).withLockedPosition(this.lockPosition).withTransformOriginOn(this.transformOriginSelector).withPopoverLocation(this.usePopover===null?`global`:this.usePopover)}_createPositionStrategy(){let e=pn(this._injector,this._getOrigin());return this._updatePositionStrategy(e),e}_getOrigin(){return this.origin instanceof Bn?this.origin.elementRef:this.origin}_getOriginElement(){return this.origin instanceof Bn?this.origin.elementRef.nativeElement:this.origin instanceof Dr?this.origin.nativeElement:typeof Element<`u`&&this.origin instanceof Element?this.origin:null}_getWidth(){return this.width?this.width:this.matchWidth?this._getOriginElement()?.getBoundingClientRect?.().width:void 0}attachOverlay(){this._overlayRef||this._createOverlay();let e=this._overlayRef;e.getConfig().hasBackdrop=this.hasBackdrop,e.updateSize({width:this._getWidth()}),e.hasAttached()||e.attach(this._templatePortal),this.hasBackdrop?this._backdropSubscription=e.backdropClick().subscribe(t=>this.backdropClick.emit(t)):this._backdropSubscription.unsubscribe(),this._positionSubscription.unsubscribe(),this.positionChange.observers.length>0&&(this._positionSubscription=this._position.positionChanges.pipe(Jg(()=>this.positionChange.observers.length>0)).subscribe(t=>{this._ngZone.run(()=>this.positionChange.emit(t)),this.positionChange.observers.length===0&&this._positionSubscription.unsubscribe()})),this.open=!0}detachOverlay(){this._overlayRef?.detach(),this._backdropSubscription.unsubscribe(),this._positionSubscription.unsubscribe(),this.open=!1}_assignConfig(e){this.origin=e.origin??this.origin,this.positions=e.positions??this.positions,this.positionStrategy=e.positionStrategy??this.positionStrategy,this.offsetX=e.offsetX??this.offsetX,this.offsetY=e.offsetY??this.offsetY,this.width=e.width??this.width,this.height=e.height??this.height,this.minWidth=e.minWidth??this.minWidth,this.minHeight=e.minHeight??this.minHeight,this.backdropClass=e.backdropClass??this.backdropClass,this.panelClass=e.panelClass??this.panelClass,this.viewportMargin=e.viewportMargin??this.viewportMargin,this.scrollStrategy=e.scrollStrategy??this.scrollStrategy,this.disableClose=e.disableClose??this.disableClose,this.transformOriginSelector=e.transformOriginSelector??this.transformOriginSelector,this.hasBackdrop=e.hasBackdrop??this.hasBackdrop,this.lockPosition=e.lockPosition??this.lockPosition,this.flexibleDimensions=e.flexibleDimensions??this.flexibleDimensions,this.growAfterOpen=e.growAfterOpen??this.growAfterOpen,this.push=e.push??this.push,this.disposeOnNavigation=e.disposeOnNavigation??this.disposeOnNavigation,this.usePopover=e.usePopover??this.usePopover,this.matchWidth=e.matchWidth??this.matchWidth}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`cdk-connected-overlay`,``],[``,`connected-overlay`,``],[``,`cdkConnectedOverlay`,``]],inputs:{origin:[0,`cdkConnectedOverlayOrigin`,`origin`],positions:[0,`cdkConnectedOverlayPositions`,`positions`],positionStrategy:[0,`cdkConnectedOverlayPositionStrategy`,`positionStrategy`],offsetX:[0,`cdkConnectedOverlayOffsetX`,`offsetX`],offsetY:[0,`cdkConnectedOverlayOffsetY`,`offsetY`],width:[0,`cdkConnectedOverlayWidth`,`width`],height:[0,`cdkConnectedOverlayHeight`,`height`],minWidth:[0,`cdkConnectedOverlayMinWidth`,`minWidth`],minHeight:[0,`cdkConnectedOverlayMinHeight`,`minHeight`],backdropClass:[0,`cdkConnectedOverlayBackdropClass`,`backdropClass`],panelClass:[0,`cdkConnectedOverlayPanelClass`,`panelClass`],viewportMargin:[0,`cdkConnectedOverlayViewportMargin`,`viewportMargin`],scrollStrategy:[0,`cdkConnectedOverlayScrollStrategy`,`scrollStrategy`],open:[0,`cdkConnectedOverlayOpen`,`open`],disableClose:[0,`cdkConnectedOverlayDisableClose`,`disableClose`],transformOriginSelector:[0,`cdkConnectedOverlayTransformOriginOn`,`transformOriginSelector`],hasBackdrop:[2,`cdkConnectedOverlayHasBackdrop`,`hasBackdrop`,T0],lockPosition:[2,`cdkConnectedOverlayLockPosition`,`lockPosition`,T0],flexibleDimensions:[2,`cdkConnectedOverlayFlexibleDimensions`,`flexibleDimensions`,T0],growAfterOpen:[2,`cdkConnectedOverlayGrowAfterOpen`,`growAfterOpen`,T0],push:[2,`cdkConnectedOverlayPush`,`push`,T0],disposeOnNavigation:[2,`cdkConnectedOverlayDisposeOnNavigation`,`disposeOnNavigation`,e=>e===`url-change`||e===`pop-state`?e:T0(e)],usePopover:[0,`cdkConnectedOverlayUsePopover`,`usePopover`],matchWidth:[2,`cdkConnectedOverlayMatchWidth`,`matchWidth`,T0],_config:[0,`cdkConnectedOverlay`,`_config`]},outputs:{backdropClick:`backdropClick`,positionChange:`positionChange`,attach:`attach`,detach:`detach`,overlayKeydown:`overlayKeydown`,overlayOutsideClick:`overlayOutsideClick`},exportAs:[`cdkConnectedOverlay`],features:[iy]})}return n})();var Ke=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({providers:[Ql],imports:[te,Rt,Sa,Sa]})}return n})();function fn(n){return n.buttons===0||n.detail===0}function gn(n){let i=n.touches&&n.touches[0]||n.changedTouches&&n.changedTouches[0];return!!i&&i.identifier===-1&&(i.radiusX==null||i.radiusX===1)&&(i.radiusY==null||i.radiusY===1)}var Pi;function ec(){if(Pi==null&&typeof window<`u`)try{window.addEventListener(`test`,null,Object.defineProperty({},"passive",{get:()=>Pi=!0}))}finally{Pi=Pi||!1}return Pi}function jn(n){return ec()?n:!!n.capture}var tc=new S(`cdk-input-modality-detector-options`);var nc={ignoreKeys:[18,17,224,91,16]};var ic=650;var Aa={passive:!0,capture:!0};var rc=(()=>{class n{_platform=I(J);_listenerCleanups;modalityDetected;modalityChanged;get mostRecentModality(){return this._modality.value}_mostRecentTarget=null;_modality=new Pn$1(null);_options;_lastTouchMs=0;_onKeydown=e=>{this._options?.ignoreKeys?.some(t=>t===e.keyCode)||(this._modality.next(`keyboard`),this._mostRecentTarget=Ie(e))};_onMousedown=e=>{Date.now()-this._lastTouchMs<ic||(this._modality.next(fn(e)?`keyboard`:`mouse`),this._mostRecentTarget=Ie(e))};_onTouchstart=e=>{if(gn(e)){this._modality.next(`keyboard`);return}this._lastTouchMs=Date.now(),this._modality.next(`touch`),this._mostRecentTarget=Ie(e)};constructor(){let e=I(z),t=I(Bo),r=I(tc,{optional:!0});if(this._options=$($({},nc),r),this.modalityDetected=this._modality.pipe(Kg(1)),this.modalityChanged=this.modalityDetected.pipe(Vl$1()),this._platform.isBrowser){let o=I(mr$1).createRenderer(null,null);this._listenerCleanups=e.runOutsideAngular(()=>[o.listen(t,`keydown`,this._onKeydown,Aa),o.listen(t,`mousedown`,this._onMousedown,Aa),o.listen(t,`touchstart`,this._onTouchstart,Aa)])}}ngOnDestroy(){this._modality.complete(),this._listenerCleanups?.forEach(e=>e())}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Li=(function(n){return n[n.IMMEDIATE=0]=`IMMEDIATE`,n[n.EVENTUAL=1]=`EVENTUAL`,n})(Li||{});var oc=new S(`cdk-focus-monitor-default-options`);var Jr=jn({passive:!0,capture:!0});var ft=(()=>{class n{_ngZone=I(z);_platform=I(J);_inputModalityDetector=I(rc);_origin=null;_lastFocusOrigin=null;_windowFocused=!1;_windowFocusTimeoutId;_originTimeoutId;_originFromTouchInteraction=!1;_elementInfo=new Map;_monitoredElementCount=0;_rootNodeFocusListenerCount=new Map;_detectionMode;_windowFocusListener=()=>{this._windowFocused=!0,this._windowFocusTimeoutId=setTimeout(()=>this._windowFocused=!1)};_document=I(Bo);_stopInputModalityDetector=new te$1;constructor(){let e=I(oc,{optional:!0});this._detectionMode=e?.detectionMode||Li.IMMEDIATE}_rootNodeFocusAndBlurListener=e=>{let t=Ie(e);for(let r=t;r;r=r.parentElement)e.type===`focus`?this._onFocus(e,r):this._onBlur(e,r)};monitor(e,t=!1){let r=je(e);if(!this._platform.isBrowser||r.nodeType!==1)return Sg();let o=va(r)||this._document,a=this._elementInfo.get(r);if(a)return t&&(a.checkChildren=!0),a.subject;let s={checkChildren:t,subject:new te$1,rootNode:o};return this._elementInfo.set(r,s),this._registerGlobalListeners(s),s.subject}stopMonitoring(e){let t=je(e),r=this._elementInfo.get(t);r&&(r.subject.complete(),this._setClasses(t),this._elementInfo.delete(t),this._removeGlobalListeners(r))}focusVia(e,t,r){let o=je(e);o===this._document.activeElement?this._getClosestElementsInfo(o).forEach(([s,c])=>this._originChanged(s,t,c)):(this._setOrigin(t),typeof o.focus==`function`&&o.focus(r))}ngOnDestroy(){this._elementInfo.forEach((e,t)=>this.stopMonitoring(t))}_getWindow(){return this._document.defaultView||window}_getFocusOrigin(e){return this._origin?this._originFromTouchInteraction?this._shouldBeAttributedToTouch(e)?`touch`:`program`:this._origin:this._windowFocused&&this._lastFocusOrigin?this._lastFocusOrigin:e&&this._isLastInteractionFromInputLabel(e)?`mouse`:`program`}_shouldBeAttributedToTouch(e){return this._detectionMode===Li.EVENTUAL||!!e?.contains(this._inputModalityDetector._mostRecentTarget)}_setClasses(e,t){e.classList.toggle(`cdk-focused`,!!t),e.classList.toggle(`cdk-touch-focused`,t===`touch`),e.classList.toggle(`cdk-keyboard-focused`,t===`keyboard`),e.classList.toggle(`cdk-mouse-focused`,t===`mouse`),e.classList.toggle(`cdk-program-focused`,t===`program`)}_setOrigin(e,t=!1){this._ngZone.runOutsideAngular(()=>{if(this._origin=e,this._originFromTouchInteraction=e===`touch`&&t,this._detectionMode===Li.IMMEDIATE){clearTimeout(this._originTimeoutId);let r=this._originFromTouchInteraction?ic:1;this._originTimeoutId=setTimeout(()=>this._origin=null,r)}})}_onFocus(e,t){let r=this._elementInfo.get(t),o=Ie(e);!r||!r.checkChildren&&t!==o||this._originChanged(t,this._getFocusOrigin(o),r)}_onBlur(e,t){let r=this._elementInfo.get(t);!r||r.checkChildren&&e.relatedTarget instanceof Node&&t.contains(e.relatedTarget)||(this._setClasses(t),this._emitOrigin(r,null))}_emitOrigin(e,t){e.subject.observers.length&&this._ngZone.run(()=>e.subject.next(t))}_registerGlobalListeners(e){if(!this._platform.isBrowser)return;let t=e.rootNode,r=this._rootNodeFocusListenerCount.get(t)||0;r||this._ngZone.runOutsideAngular(()=>{t.addEventListener(`focus`,this._rootNodeFocusAndBlurListener,Jr),t.addEventListener(`blur`,this._rootNodeFocusAndBlurListener,Jr)}),this._rootNodeFocusListenerCount.set(t,r+1),++this._monitoredElementCount===1&&(this._ngZone.runOutsideAngular(()=>{this._getWindow().addEventListener(`focus`,this._windowFocusListener)}),this._inputModalityDetector.modalityDetected.pipe(Rl$1(this._stopInputModalityDetector)).subscribe(o=>{this._setOrigin(o,!0)}))}_removeGlobalListeners(e){let t=e.rootNode;if(this._rootNodeFocusListenerCount.has(t)){let r=this._rootNodeFocusListenerCount.get(t);r>1?this._rootNodeFocusListenerCount.set(t,r-1):(t.removeEventListener(`focus`,this._rootNodeFocusAndBlurListener,Jr),t.removeEventListener(`blur`,this._rootNodeFocusAndBlurListener,Jr),this._rootNodeFocusListenerCount.delete(t))}--this._monitoredElementCount||(this._getWindow().removeEventListener(`focus`,this._windowFocusListener),this._stopInputModalityDetector.next(),clearTimeout(this._windowFocusTimeoutId),clearTimeout(this._originTimeoutId))}_originChanged(e,t,r){this._setClasses(e,t),this._emitOrigin(r,t),this._lastFocusOrigin=t}_getClosestElementsInfo(e){let t=[];return this._elementInfo.forEach((r,o)=>{(o===e||r.checkChildren&&o.contains(e))&&t.push([o,r])}),t}_isLastInteractionFromInputLabel(e){let{_mostRecentTarget:t,mostRecentModality:r}=this._inputModalityDetector;if(r!==`mouse`||!t||t===e||e.nodeName!==`INPUT`&&e.nodeName!==`TEXTAREA`||e.disabled)return!1;let o=e.labels;if(o){for(let a=0;a<o.length;a++)if(o[a].contains(t))return!0}return!1}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Ku=(()=>{class n{_elementRef=I(Dr);_focusMonitor=I(ft);_monitorSubscription;_focusOrigin=null;cdkFocusChange=new Fe;get focusOrigin(){return this._focusOrigin}ngAfterViewInit(){let e=this._elementRef.nativeElement;this._monitorSubscription=this._focusMonitor.monitor(e,e.nodeType===1&&e.hasAttribute(`cdkMonitorSubtreeFocus`)).subscribe(t=>{this._focusOrigin=t,this.cdkFocusChange.emit(t)})}ngOnDestroy(){this._focusMonitor.stopMonitoring(this._elementRef),this._monitorSubscription?.unsubscribe()}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`cdkMonitorElementFocus`,``],[``,`cdkMonitorSubtreeFocus`,``]],outputs:{cdkFocusChange:`cdkFocusChange`},exportAs:[`cdkMonitorFocus`]})}return n})();var Un=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵcmp=LI({type:n,selectors:[[`ng-component`]],exportAs:[`cdkVisuallyHidden`],decls:0,vars:0,template:function(t,r){},styles:[`.cdk-visually-hidden {
  border: 0;
  clip: rect(0 0 0 0);
  height: 1px;
  margin: -1px;
  overflow: hidden;
  padding: 0;
  position: absolute;
  width: 1px;
  white-space: nowrap;
  outline: 0;
  -webkit-appearance: none;
  -moz-appearance: none;
  left: 0;
}
[dir=rtl] .cdk-visually-hidden {
  left: auto;
  right: 0;
}
`],encapsulation:2})}return n})();var eo;function qu(){if(eo===void 0&&(eo=null,typeof window<`u`)){let n=window;if(n.trustedTypes!==void 0)try{eo=n.trustedTypes.createPolicy(`angular#components`,{createHTML:i=>i})}catch(i){console.error(i)}}return eo}function bn(n){return qu()?.createHTML(n)||n}function ac(n,i,e){n.innerHTML=bn(e.sanitize(ne.HTML,i)||``)}var sc=new Set;var _n;var Hn=(()=>{class n{_platform=I(J);_nonce=I($m$1,{optional:!0});_matchMedia;constructor(){this._matchMedia=this._platform.isBrowser&&window.matchMedia?window.matchMedia.bind(window):Qu}matchMedia(e){return(this._platform.WEBKIT||this._platform.BLINK)&&Zu(e,this._nonce),this._matchMedia(e)}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();function Zu(n,i){if(!sc.has(n))try{_n||(_n=document.createElement(`style`),i&&_n.setAttribute(`nonce`,i),_n.setAttribute(`type`,`text/css`),document.head.appendChild(_n)),_n.sheet&&(_n.sheet.insertRule(`@media ${n.replace(/[{}]/g,``)} {body{ }}`,0),sc.add(n))}catch(e){console.error(e)}}function Qu(n){return{matches:n===`all`||n===``,media:n,addListener:()=>{},removeListener:()=>{}}}var Vi=(()=>{class n{_mediaMatcher=I(Hn);_zone=I(z);_queries=new Map;_destroySubject=new te$1;ngOnDestroy(){this._destroySubject.next(),this._destroySubject.complete()}isMatched(e){return lc(Pn(e)).some(r=>this._registerQuery(r).mql.matches)}observe(e){let r=lc(Pn(e)).map(a=>this._registerQuery(a).observable),o=Ng(r);return o=sn(o.pipe(gt$1(1)),o.pipe(Kg(1),Ml$1(0))),o.pipe(Me$1(a=>{let s={matches:!1,breakpoints:{}};return a.forEach(({matches:c,query:d})=>{s.matches=s.matches||c,s.breakpoints[d]=c}),s}))}_registerQuery(e){if(this._queries.has(e))return this._queries.get(e);let t=this._mediaMatcher.matchMedia(e),o={observable:new N(a=>{let s=c=>this._zone.run(()=>a.next(c));return t.addListener(s),()=>{t.removeListener(s)}}).pipe(Al$1(t),Me$1(({matches:a})=>({query:e,matches:a})),Rl$1(this._destroySubject)),mql:t};return this._queries.set(e,o),o}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();function lc(n){return n.map(i=>i.split(`,`)).reduce((i,e)=>i.concat(e)).map(i=>i.trim())}function Ju(n){if(n.type===`characterData`&&n.target instanceof Comment)return!0;if(n.type===`childList`){for(let i=0;i<n.addedNodes.length;i++)if(!(n.addedNodes[i]instanceof Comment))return!1;for(let i=0;i<n.removedNodes.length;i++)if(!(n.removedNodes[i]instanceof Comment))return!1;return!0}return!1}var cc=(()=>{class n{create(e){return typeof MutationObserver>`u`?null:new MutationObserver(e)}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var dc=(()=>{class n{_mutationObserverFactory=I(cc);_observedElements=new Map;_ngZone=I(z);ngOnDestroy(){this._observedElements.forEach((e,t)=>this._cleanupObserver(t))}observe(e){let t=je(e);return new N(r=>{let a=this._observeElement(t).pipe(Me$1(s=>s.filter(c=>!Ju(c))),rn(s=>!!s.length)).subscribe(s=>{this._ngZone.run(()=>{r.next(s)})});return()=>{a.unsubscribe(),this._unobserveElement(t)}})}_observeElement(e){return this._ngZone.runOutsideAngular(()=>{if(this._observedElements.has(e))this._observedElements.get(e).count++;else{let t=new te$1,r=this._mutationObserverFactory.create(o=>t.next(o));r&&r.observe(e,{characterData:!0,childList:!0,subtree:!0}),this._observedElements.set(e,{observer:r,stream:t,count:1})}return this._observedElements.get(e).stream})}_unobserveElement(e){this._observedElements.has(e)&&(this._observedElements.get(e).count--,this._observedElements.get(e).count||this._cleanupObserver(e))}_cleanupObserver(e){if(this._observedElements.has(e)){let{observer:t,stream:r}=this._observedElements.get(e);t&&t.disconnect(),r.complete(),this._observedElements.delete(e)}}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var u0=(()=>{class n{_contentObserver=I(dc);_elementRef=I(Dr);event=new Fe;get disabled(){return this._disabled}set disabled(e){this._disabled=e,this._disabled?this._unsubscribe():this._subscribe()}_disabled=!1;get debounce(){return this._debounce}set debounce(e){this._debounce=dt(e),this._subscribe()}_debounce;_currentSubscription=null;ngAfterContentInit(){!this._currentSubscription&&!this.disabled&&this._subscribe()}ngOnDestroy(){this._unsubscribe()}_subscribe(){this._unsubscribe();let e=this._contentObserver.observe(this._elementRef);this._currentSubscription=(this.debounce?e.pipe(Ml$1(this.debounce)):e).subscribe(this.event)}_unsubscribe(){this._currentSubscription?.unsubscribe()}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`cdkObserveContent`,``]],inputs:{disabled:[2,`cdkObserveContentDisabled`,`disabled`,T0],debounce:`debounce`},outputs:{event:`cdkObserveContent`},exportAs:[`cdkObserveContent`]})}return n})();var to=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({providers:[cc]})}return n})();var Ta=(()=>{class n{_platform=I(J);isDisabled(e){return e.hasAttribute(`disabled`)}isVisible(e){return th(e)&&getComputedStyle(e).visibility===`visible`}isTabbable(e){if(!this._platform.isBrowser)return!1;let t=eh(ch(e));if(t&&(mc(t)===-1||!this.isVisible(t)))return!1;let r=e.nodeName.toLowerCase(),o=mc(e);return e.hasAttribute(`contenteditable`)?o!==-1:r===`iframe`||r===`object`||this._platform.WEBKIT&&this._platform.IOS&&!sh(e)?!1:r===`audio`?e.hasAttribute(`controls`)?o!==-1:!1:r===`video`?o===-1?!1:o!==null?!0:this._platform.FIREFOX||e.hasAttribute(`controls`):e.tabIndex>=0}isFocusable(e,t){return lh(e)&&!this.isDisabled(e)&&(t?.ignoreVisibility||this.isVisible(e))}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();function eh(n){try{return n.frameElement}catch(i){return null}}function th(n){return!!(n.offsetWidth||n.offsetHeight||typeof n.getClientRects==`function`&&n.getClientRects().length)}function nh(n){let i=n.nodeName.toLowerCase();return i===`input`||i===`select`||i===`button`||i===`textarea`}function ih(n){return oh(n)&&n.type==`hidden`}function rh(n){return ah(n)&&n.hasAttribute(`href`)}function oh(n){return n.nodeName.toLowerCase()==`input`}function ah(n){return n.nodeName.toLowerCase()==`a`}function pc(n){if(!n.hasAttribute(`tabindex`)||n.tabIndex===void 0)return!1;let i=n.getAttribute(`tabindex`);return!!(i&&!isNaN(parseInt(i,10)))}function mc(n){if(!pc(n))return null;let i=parseInt(n.getAttribute(`tabindex`)||``,10);return isNaN(i)?-1:i}function sh(n){let i=n.nodeName.toLowerCase(),e=i===`input`&&n.type;return e===`text`||e===`password`||i===`select`||i===`textarea`}function lh(n){return ih(n)?!1:nh(n)||rh(n)||n.hasAttribute(`contenteditable`)||pc(n)}function ch(n){return n.ownerDocument&&n.ownerDocument.defaultView||window}var Na=class{_element;_checker;_ngZone;_document;_injector;_startAnchor=null;_endAnchor=null;_hasAttached=!1;startAnchorListener=()=>{!this.focusLastTabbableElement()&&this._checker.isFocusable(this._element)&&this._element.focus()};endAnchorListener=()=>{!this.focusFirstTabbableElement()&&this._checker.isFocusable(this._element)&&this._element.focus()};get enabled(){return this._enabled}set enabled(i){this._enabled=i,this._startAnchor&&this._endAnchor&&(this._toggleAnchorTabIndex(i,this._startAnchor),this._toggleAnchorTabIndex(i,this._endAnchor))}_enabled=!0;constructor(i,e,t,r,o=!1,a){this._element=i,this._checker=e,this._ngZone=t,this._document=r,this._injector=a,o||this.attachAnchors()}destroy(){let i=this._startAnchor,e=this._endAnchor;i&&(i.removeEventListener(`focus`,this.startAnchorListener),i.remove()),e&&(e.removeEventListener(`focus`,this.endAnchorListener),e.remove()),this._startAnchor=this._endAnchor=null,this._hasAttached=!1}attachAnchors(){return this._hasAttached?!0:(this._ngZone.runOutsideAngular(()=>{this._startAnchor||(this._startAnchor=this._createAnchor(),this._startAnchor.addEventListener(`focus`,this.startAnchorListener)),this._endAnchor||(this._endAnchor=this._createAnchor(),this._endAnchor.addEventListener(`focus`,this.endAnchorListener))}),this._element.parentNode&&(this._element.parentNode.insertBefore(this._startAnchor,this._element),this._element.parentNode.insertBefore(this._endAnchor,this._element.nextSibling),this._hasAttached=!0),this._hasAttached)}focusInitialElementWhenReady(i){return new Promise(e=>{this._executeOnStable(()=>e(this.focusInitialElement(i)))})}focusFirstTabbableElementWhenReady(i){return new Promise(e=>{this._executeOnStable(()=>e(this.focusFirstTabbableElement(i)))})}focusLastTabbableElementWhenReady(i){return new Promise(e=>{this._executeOnStable(()=>e(this.focusLastTabbableElement(i)))})}_getRegionBoundary(i){let e=this._element.querySelectorAll(`[cdk-focus-region-${i}], [cdkFocusRegion${i}], [cdk-focus-${i}]`);return i==`start`?e.length?e[0]:this._getFirstTabbableElement(this._element):e.length?e[e.length-1]:this._getLastTabbableElement(this._element)}focusInitialElement(i){let e=this._element.querySelector(`[cdk-focus-initial], [cdkFocusInitial]`);if(e){if(!this._checker.isFocusable(e)){let t=this._getFirstTabbableElement(e);return t?.focus(i),!!t}return e.focus(i),!0}return this.focusFirstTabbableElement(i)}focusFirstTabbableElement(i){let e=this._getRegionBoundary(`start`);return e&&e.focus(i),!!e}focusLastTabbableElement(i){let e=this._getRegionBoundary(`end`);return e&&e.focus(i),!!e}hasAttached(){return this._hasAttached}_getFirstTabbableElement(i){if(this._checker.isFocusable(i)&&this._checker.isTabbable(i))return i;let e=i.children;for(let t=0;t<e.length;t++){let r=e[t].nodeType===this._document.ELEMENT_NODE?this._getFirstTabbableElement(e[t]):null;if(r)return r}return null}_getLastTabbableElement(i){if(this._checker.isFocusable(i)&&this._checker.isTabbable(i))return i;let e=i.children;for(let t=e.length-1;t>=0;t--){let r=e[t].nodeType===this._document.ELEMENT_NODE?this._getLastTabbableElement(e[t]):null;if(r)return r}return null}_createAnchor(){let i=this._document.createElement(`div`);return this._toggleAnchorTabIndex(this._enabled,i),i.classList.add(`cdk-visually-hidden`),i.classList.add(`cdk-focus-trap-anchor`),i.setAttribute(`aria-hidden`,`true`),i}_toggleAnchorTabIndex(i,e){i?e.setAttribute(`tabindex`,`0`):e.removeAttribute(`tabindex`)}toggleAnchors(i){this._startAnchor&&this._endAnchor&&(this._toggleAnchorTabIndex(i,this._startAnchor),this._toggleAnchorTabIndex(i,this._endAnchor))}_executeOnStable(i){Hv(i,{injector:this._injector})}};var Ra=(()=>{class n{_checker=I(Ta);_ngZone=I(z);_document=I(Bo);_injector=I(le);constructor(){I(Se).load(Un)}create(e,t=!1){return new Na(e,this._checker,this._ngZone,this._document,t,this._injector)}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var fc=new S(`liveAnnouncerElement`,{providedIn:`root`,factory:()=>null});var gc=new S(`LIVE_ANNOUNCER_DEFAULT_OPTIONS`);var dh=0;var Bi=(()=>{class n{_ngZone=I(z);_defaultOptions=I(gc,{optional:!0});_liveElement;_document=I(Bo);_sanitizer=I(Ii);_previousTimeout;_currentPromise;_currentResolve;constructor(){let e=I(fc,{optional:!0});this._liveElement=e||this._createLiveElement()}announce(e,...t){let r=this._defaultOptions,o,a;return t.length===1&&typeof t[0]==`number`?a=t[0]:[o,a]=t,this.clear(),clearTimeout(this._previousTimeout),o||(o=r&&r.politeness?r.politeness:`polite`),a==null&&r&&(a=r.duration),this._liveElement.setAttribute(`aria-live`,o),this._liveElement.id&&this._exposeAnnouncerToModals(this._liveElement.id),this._ngZone.runOutsideAngular(()=>(this._currentPromise||(this._currentPromise=new Promise(s=>this._currentResolve=s)),clearTimeout(this._previousTimeout),this._previousTimeout=setTimeout(()=>{!e||typeof e==`string`?this._liveElement.textContent=e:ac(this._liveElement,e,this._sanitizer),typeof a==`number`&&(this._previousTimeout=setTimeout(()=>this.clear(),a)),this._currentResolve?.(),this._currentPromise=this._currentResolve=void 0},100),this._currentPromise))}clear(){this._liveElement&&(this._liveElement.textContent=``)}ngOnDestroy(){clearTimeout(this._previousTimeout),this._liveElement?.remove(),this._liveElement=null,this._currentResolve?.(),this._currentPromise=this._currentResolve=void 0}_createLiveElement(){let e=`cdk-live-announcer-element`,t=this._document.getElementsByClassName(e),r=this._document.createElement(`div`);for(let o=0;o<t.length;o++)t[o].remove();return r.classList.add(e),r.classList.add(`cdk-visually-hidden`),r.setAttribute(`aria-atomic`,`true`),r.setAttribute(`aria-live`,`polite`),r.id=`cdk-live-announcer-${dh++}`,this._document.body.appendChild(r),r}_exposeAnnouncerToModals(e){let t=this._document.querySelectorAll(`body > .cdk-overlay-container [aria-modal="true"]`);for(let r=0;r<t.length;r++){let o=t[r],a=o.getAttribute(`aria-owns`);a?a.indexOf(e)===-1&&o.setAttribute(`aria-owns`,a+` `+e):o.setAttribute(`aria-owns`,e)}}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Kt=(function(n){return n[n.NONE=0]=`NONE`,n[n.BLACK_ON_WHITE=1]=`BLACK_ON_WHITE`,n[n.WHITE_ON_BLACK=2]=`WHITE_ON_BLACK`,n})(Kt||{});var uc=`cdk-high-contrast-black-on-white`;var hc=`cdk-high-contrast-white-on-black`;var Ia=`cdk-high-contrast-active`;var bc=(()=>{class n{_platform=I(J);_hasCheckedHighContrastMode=!1;_document=I(Bo);_breakpointSubscription;constructor(){this._breakpointSubscription=I(Vi).observe(`(forced-colors: active)`).subscribe(()=>{this._hasCheckedHighContrastMode&&(this._hasCheckedHighContrastMode=!1,this._applyBodyHighContrastModeCssClasses())})}getHighContrastMode(){if(!this._platform.isBrowser)return Kt.NONE;let e=this._document.createElement(`div`);e.style.backgroundColor=`rgb(1,2,3)`,e.style.position=`absolute`,this._document.body.appendChild(e);let t=this._document.defaultView||window,r=t&&t.getComputedStyle?t.getComputedStyle(e):null,o=(r&&r.backgroundColor||``).replace(/ /g,``);switch(e.remove(),o){case`rgb(0,0,0)`:case`rgb(45,50,54)`:case`rgb(32,32,32)`:return Kt.WHITE_ON_BLACK;case`rgb(255,255,255)`:case`rgb(255,250,239)`:return Kt.BLACK_ON_WHITE}return Kt.NONE}ngOnDestroy(){this._breakpointSubscription.unsubscribe()}_applyBodyHighContrastModeCssClasses(){if(!this._hasCheckedHighContrastMode&&this._platform.isBrowser&&this._document.body){let e=this._document.body.classList;e.remove(Ia,uc,hc),this._hasCheckedHighContrastMode=!0;let t=this.getHighContrastMode();t===Kt.BLACK_ON_WHITE?e.add(Ia,uc):t===Kt.WHITE_ON_BLACK&&e.add(Ia,hc)}}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var zi=(()=>{class n{constructor(){I(bc)._applyBodyHighContrastModeCssClasses()}static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[to]})}return n})();var qt=class{viewContainerRef;injector;id;role=`dialog`;panelClass=``;hasBackdrop=!0;backdropClass=``;disableClose=!1;closePredicate;width=``;height=``;minWidth;minHeight;maxWidth;maxHeight;positionStrategy;data=null;direction;ariaDescribedBy=null;ariaLabelledBy=null;ariaLabel=null;ariaModal=!1;autoFocus=`first-tabbable`;restoreFocus=!0;scrollStrategy;closeOnNavigation=!0;closeOnDestroy=!0;closeOnOverlayDetachments=!0;disableAnimations=!1;providers;container;templateContext;bindings};var Fa=(()=>{class n extends Wt{_elementRef=I(Dr);_focusTrapFactory=I(Ra);_config;_interactivityChecker=I(Ta);_ngZone=I(z);_focusMonitor=I(ft);_renderer=I(La$1);_changeDetectorRef=I(w0);_injector=I(le);_platform=I(J);_document=I(Bo);_portalOutlet;_focusTrapped=new te$1;_focusTrap=null;_elementFocusedBeforeDialogWasOpened=null;_closeInteractionType=null;_ariaLabelledByQueue=[];_isDestroyed=!1;constructor(){super(),this._config=I(qt,{optional:!0})||new qt,this._config.ariaLabelledBy&&this._ariaLabelledByQueue.push(this._config.ariaLabelledBy)}_addAriaLabelledBy(e){this._ariaLabelledByQueue.push(e),this._changeDetectorRef.markForCheck()}_removeAriaLabelledBy(e){let t=this._ariaLabelledByQueue.indexOf(e);t>-1&&(this._ariaLabelledByQueue.splice(t,1),this._changeDetectorRef.markForCheck())}_contentAttached(){this._initializeFocusTrap(),this._captureInitialFocus()}_captureInitialFocus(){this._trapFocus()}ngOnDestroy(){this._focusTrapped.complete(),this._isDestroyed=!0,this._restoreFocus()}attachComponentPortal(e){this._portalOutlet.hasAttached();let t=this._portalOutlet.attachComponentPortal(e);return this._contentAttached(),t}attachTemplatePortal(e){this._portalOutlet.hasAttached();let t=this._portalOutlet.attachTemplatePortal(e);return this._contentAttached(),t}attachDomPortal=e=>{this._portalOutlet.hasAttached();let t=this._portalOutlet.attachDomPortal(e);return this._contentAttached(),t};_recaptureFocus(){this._containsFocus()||this._trapFocus()}_forceFocus(e,t){this._interactivityChecker.isFocusable(e)||(e.tabIndex=-1,this._ngZone.runOutsideAngular(()=>{let r=()=>{o(),a(),e.removeAttribute(`tabindex`)},o=this._renderer.listen(e,`blur`,r),a=this._renderer.listen(e,`mousedown`,r)})),e.focus(t)}_focusByCssSelector(e,t){let r=this._elementRef.nativeElement.querySelector(e);r&&this._forceFocus(r,t)}_trapFocus(e){this._isDestroyed||Hv(()=>{let t=this._elementRef.nativeElement;switch(this._config.autoFocus){case!1:case`dialog`:this._containsFocus()||t.focus(e);break;case!0:case`first-tabbable`:this._focusTrap?.focusInitialElement(e)||this._focusDialogContainer(e);break;case`first-heading`:this._focusByCssSelector(`h1, h2, h3, h4, h5, h6, [role="heading"]`,e);break;default:this._focusByCssSelector(this._config.autoFocus,e)}this._focusTrapped.next()},{injector:this._injector})}_restoreFocus(){let e=this._config.restoreFocus,t=null;if(typeof e==`string`?t=this._document.querySelector(e):typeof e==`boolean`?t=e?this._elementFocusedBeforeDialogWasOpened:null:e&&(t=e),this._config.restoreFocus&&t&&typeof t.focus==`function`){let r=Ni(),o=this._elementRef.nativeElement;(!r||r===this._document.body||r===o||o.contains(r))&&(this._focusMonitor?(this._focusMonitor.focusVia(t,this._closeInteractionType),this._closeInteractionType=null):t.focus())}this._focusTrap&&this._focusTrap.destroy()}_focusDialogContainer(e){this._elementRef.nativeElement.focus?.(e)}_containsFocus(){let e=this._elementRef.nativeElement,t=Ni();return e===t||e.contains(t)}_initializeFocusTrap(){this._platform.isBrowser&&(this._focusTrap=this._focusTrapFactory.create(this._elementRef.nativeElement),this._document&&(this._elementFocusedBeforeDialogWasOpened=Ni()))}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){function e(t,r){}return LI({type:n,selectors:[[`cdk-dialog-container`]],viewQuery:function(r,o){if(r&1&&lh$1(Yt,7),r&2){let a;SD(a=xD())&&(o._portalOutlet=a.first)}},hostAttrs:[`tabindex`,`-1`,1,`cdk-dialog-container`],hostVars:6,hostBindings:function(r,o){r&2&&Kp(`id`,o._config.id||null)(`role`,o._config.role)(`aria-modal`,o._config.ariaModal)(`aria-labelledby`,o._config.ariaLabel?null:o._ariaLabelledByQueue[0])(`aria-label`,o._config.ariaLabel)(`aria-describedby`,o._config.ariaDescribedBy||null)},features:[Vp$1],decls:1,vars:0,consts:[[`cdkPortalOutlet`,``]],template:function(r,o){r&1&&Bp$1(0,e,0,0,`ng-template`,0)},dependencies:[Yt],styles:[`.cdk-dialog-container {
  display: block;
  width: 100%;
  height: 100%;
  min-height: inherit;
  max-height: inherit;
}
`],encapsulation:2,changeDetection:1})})()}return n})();var yn=class{overlayRef;config;componentInstance=null;componentRef=null;containerInstance;disableClose;closed=new te$1;backdropClick;keydownEvents;outsidePointerEvents;id;_detachSubscription;constructor(i,e){this.overlayRef=i,this.config=e,this.disableClose=e.disableClose,this.backdropClick=i.backdropClick(),this.keydownEvents=i.keydownEvents(),this.outsidePointerEvents=i.outsidePointerEvents(),this.id=e.id,this.keydownEvents.subscribe(t=>{t.keyCode===27&&!this.disableClose&&!Me(t)&&(t.preventDefault(),this.close(void 0,{focusOrigin:`keyboard`}))}),this.backdropClick.subscribe(()=>{!this.disableClose&&this._canClose()?this.close(void 0,{focusOrigin:`mouse`}):this.containerInstance._recaptureFocus?.()}),this._detachSubscription=i.detachments().subscribe(()=>{e.closeOnOverlayDetachments!==!1&&this.close()})}close(i,e){if(this._canClose(i)){let t=this.closed;this.containerInstance._closeInteractionType=e?.focusOrigin||`program`,this._detachSubscription.unsubscribe(),this.overlayRef.dispose(),t.next(i),t.complete(),this.componentInstance=this.containerInstance=null}}updatePosition(){return this.overlayRef.updatePosition(),this}updateSize(i=``,e=``){return this.overlayRef.updateSize({width:i,height:e}),this}addPanelClass(i){return this.overlayRef.addPanelClass(i),this}removePanelClass(i){return this.overlayRef.removePanelClass(i),this}_canClose(i){let e=this.config;return!!this.containerInstance&&(!e.closePredicate||e.closePredicate(i,e,this.componentInstance))}};var mh=new S(`DialogScrollStrategy`,{providedIn:`root`,factory:()=>{let n=I(le);return()=>zn(n)}});var uh=new S(`DialogData`);var hh=new S(`DefaultDialogConfig`);function ph(n){let i=oa(n),e=new Fe;return{valueSignal:i,get value(){return i()},change:e,ngOnDestroy(){e.complete()}}}var Pa=(()=>{class n{_injector=I(le);_defaultOptions=I(hh,{optional:!0});_parentDialog=I(n,{optional:!0,skipSelf:!0});_overlayContainer=I(Zr);_idGenerator=I(me);_openDialogsAtThisLevel=[];_afterAllClosedAtThisLevel=new te$1;_afterOpenedAtThisLevel=new te$1;_ariaHiddenElements=new Map;_scrollStrategy=I(mh);get openDialogs(){return this._parentDialog?this._parentDialog.openDialogs:this._openDialogsAtThisLevel}get afterOpened(){return this._parentDialog?this._parentDialog.afterOpened:this._afterOpenedAtThisLevel}afterAllClosed=Og(()=>this.openDialogs.length?this._getAfterAllClosed():this._getAfterAllClosed().pipe(Al$1(void 0)));open(e,t){let r=this._defaultOptions||new qt;t=$($({},r),t),t.id=t.id||this._idGenerator.getId(`cdk-dialog-`),t.id&&this.getDialogById(t.id);let o=this._getOverlayConfig(t),a=pt(this._injector,o),s=new yn(a,t),c=this._attachContainer(a,s,t);if(s.containerInstance=c,!this.openDialogs.length){let d=this._overlayContainer.getContainerElement();c._focusTrapped?c._focusTrapped.pipe(gt$1(1)).subscribe(()=>{this._hideNonDialogContentFromAssistiveTechnology(d)}):this._hideNonDialogContentFromAssistiveTechnology(d)}return this._attachDialogContent(e,s,c,t),this.openDialogs.push(s),s.closed.subscribe(()=>this._removeOpenDialog(s,!0)),this.afterOpened.next(s),s}closeAll(){Oa(this.openDialogs,e=>e.close())}getDialogById(e){return this.openDialogs.find(t=>t.id===e)}ngOnDestroy(){Oa(this._openDialogsAtThisLevel,e=>{e.config.closeOnDestroy===!1&&this._removeOpenDialog(e,!1)}),Oa(this._openDialogsAtThisLevel,e=>e.close()),this._afterAllClosedAtThisLevel.complete(),this._afterOpenedAtThisLevel.complete(),this._openDialogsAtThisLevel=[]}_getOverlayConfig(e){let t=new ht({positionStrategy:e.positionStrategy||Xt().centerHorizontally().centerVertically(),scrollStrategy:e.scrollStrategy||this._scrollStrategy(),panelClass:e.panelClass,hasBackdrop:e.hasBackdrop,direction:e.direction,minWidth:e.minWidth,minHeight:e.minHeight,maxWidth:e.maxWidth,maxHeight:e.maxHeight,width:e.width,height:e.height,disposeOnNavigation:e.closeOnNavigation,disableAnimations:e.disableAnimations});return e.backdropClass&&(t.backdropClass=e.backdropClass),t}_attachContainer(e,t,r){let o=r.injector||r.viewContainerRef?.injector,a=[{provide:qt,useValue:r},{provide:yn,useValue:t},{provide:Vn,useValue:e}],s;r.container?typeof r.container==`function`?s=r.container:(s=r.container.type,a.push(...r.container.providers(r))):s=Fa;let c=new ut(s,r.viewContainerRef,le.create({parent:o||this._injector,providers:a}));return e.attach(c).instance}_attachDialogContent(e,t,r,o){if(e instanceof gr){let a=this._createInjector(o,t,r,void 0),s={$implicit:o.data,dialogRef:t};o.templateContext&&(s=$($({},s),typeof o.templateContext==`function`?o.templateContext():o.templateContext)),r.attachTemplatePortal(new rt(e,null,s,a))}else{let a=this._createInjector(o,t,r,this._injector),s=r.attachComponentPortal(new ut(e,o.viewContainerRef,a,null,o.bindings));t.componentRef=s,t.componentInstance=s.instance}}_createInjector(e,t,r,o){let a=e.injector||e.viewContainerRef?.injector,s=[{provide:uh,useValue:e.data},{provide:yn,useValue:t}];return e.providers&&(typeof e.providers==`function`?s.push(...e.providers(t,e,r)):s.push(...e.providers)),e.direction&&(!a||!a.get(Ne,null,{optional:!0}))&&s.push({provide:Ne,useValue:ph(e.direction)}),le.create({parent:a||o,providers:s})}_removeOpenDialog(e,t){let r=this.openDialogs.indexOf(e);r>-1&&(this.openDialogs.splice(r,1),this.openDialogs.length||(this._ariaHiddenElements.forEach((o,a)=>{o?a.setAttribute(`aria-hidden`,o):a.removeAttribute(`aria-hidden`)}),this._ariaHiddenElements.clear(),t&&this._getAfterAllClosed().next()))}_hideNonDialogContentFromAssistiveTechnology(e){if(e.parentElement){let t=e.parentElement.children;for(let r=t.length-1;r>-1;r--){let o=t[r];o!==e&&o.nodeName!==`SCRIPT`&&o.nodeName!==`STYLE`&&!o.hasAttribute(`aria-live`)&&!o.hasAttribute(`popover`)&&(this._ariaHiddenElements.set(o,o.getAttribute(`aria-hidden`)),o.setAttribute(`aria-hidden`,`true`))}}}_getAfterAllClosed(){let e=this._parentDialog;return e?e._getAfterAllClosed():this._afterAllClosedAtThisLevel}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();function Oa(n,i){let e=n.length;for(;e--;)i(n[e])}var _c=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({providers:[Pa],imports:[Ke,Rt,zi,Rt]})}return n})();function Pt(n){return n!=null&&`${n}`!=`false`}var yc={XSmall:`(max-width: 599.98px)`,Small:`(min-width: 600px) and (max-width: 959.98px)`,Medium:`(min-width: 960px) and (max-width: 1279.98px)`,Large:`(min-width: 1280px) and (max-width: 1919.98px)`,XLarge:`(min-width: 1920px)`,Handset:`(max-width: 599.98px) and (orientation: portrait), (max-width: 959.98px) and (orientation: landscape)`,Tablet:`(min-width: 600px) and (max-width: 839.98px) and (orientation: portrait), (min-width: 960px) and (max-width: 1279.98px) and (orientation: landscape)`,Web:`(min-width: 840px) and (orientation: portrait), (min-width: 1280px) and (orientation: landscape)`,HandsetPortrait:`(max-width: 599.98px) and (orientation: portrait)`,TabletPortrait:`(min-width: 600px) and (max-width: 839.98px) and (orientation: portrait)`,WebPortrait:`(min-width: 840px) and (orientation: portrait)`,HandsetLandscape:`(max-width: 959.98px) and (orientation: landscape)`,TabletLandscape:`(min-width: 960px) and (max-width: 1279.98px) and (orientation: landscape)`,WebLandscape:`(min-width: 1280px) and (orientation: landscape)`};var fh=new S(`MATERIAL_ANIMATIONS`);var vc=null;function La(){return I(fh,{optional:!0})?.animationsDisabled||I(Bm$1,{optional:!0})===`NoopAnimations`?`di-disabled`:(vc??=I(Hn).matchMedia(`(prefers-reduced-motion)`).matches,vc?`reduced-motion`:`enabled`)}function ue(){return La()!==`enabled`}var gh=200;var no=class{_letterKeyStream=new te$1;_items=[];_selectedItemIndex=-1;_pressedLetters=[];_skipPredicateFn;_selectedItem=new te$1;selectedItem=this._selectedItem;constructor(i,e){let t=typeof e?.debounceInterval==`number`?e.debounceInterval:gh;e?.skipPredicate&&(this._skipPredicateFn=e.skipPredicate),this.setItems(i),this._setupKeyHandler(t)}destroy(){this._pressedLetters=[],this._letterKeyStream.complete(),this._selectedItem.complete()}setCurrentSelectedItemIndex(i){this._selectedItemIndex=i}setItems(i){this._items=i}handleKey(i){let e=i.keyCode;i.key&&i.key.length===1?this._letterKeyStream.next(i.key.toLocaleUpperCase()):(e>=65&&e<=90||e>=48&&e<=57)&&this._letterKeyStream.next(String.fromCharCode(e))}isTyping(){return this._pressedLetters.length>0}reset(){this._pressedLetters=[]}_setupKeyHandler(i){this._letterKeyStream.pipe(Xg(e=>this._pressedLetters.push(e)),Ml$1(i),rn(()=>this._pressedLetters.length>0),Me$1(()=>this._pressedLetters.join(``).toLocaleUpperCase())).subscribe(e=>{for(let t=1;t<this._items.length+1;t++){let r=(this._selectedItemIndex+t)%this._items.length,o=this._items[r];if(!this._skipPredicateFn?.(o)&&o.getLabel?.().toLocaleUpperCase().trim().indexOf(e)===0){this._selectedItem.next(o);break}}this._pressedLetters=[]})}};var $n=class{_items;_activeItemIndex=oa(-1);_activeItem=oa(null);_wrap=!1;_typeaheadSubscription=q.EMPTY;_itemChangesSubscription;_vertical=!0;_horizontal=null;_allowedModifierKeys=[];_homeAndEnd=!1;_pageUpAndDown={enabled:!1,delta:10};_effectRef;_typeahead;_skipPredicateFn=i=>i.disabled;constructor(i,e){this._items=i,i instanceof ii$1?this._itemChangesSubscription=i.changes.subscribe(t=>this._itemsChanged(t.toArray())):ia$1(i)&&(this._effectRef=Wm$1(()=>this._itemsChanged(i()),{injector:e}))}tabOut=new te$1;change=new te$1;skipPredicate(i){return this._skipPredicateFn=i,this}withWrap(i=!0){return this._wrap=i,this}withVerticalOrientation(i=!0){return this._vertical=i,this}withHorizontalOrientation(i){return this._horizontal=i,this}withAllowedModifierKeys(i){return this._allowedModifierKeys=i,this}withTypeAhead(i=200){this._typeaheadSubscription.unsubscribe();let e=this._getItemsArray();return this._typeahead=new no(e,{debounceInterval:typeof i==`number`?i:void 0,skipPredicate:t=>this._skipPredicateFn(t)}),this._typeaheadSubscription=this._typeahead.selectedItem.subscribe(t=>{this.setActiveItem(t)}),this}cancelTypeahead(){return this._typeahead?.reset(),this}withHomeAndEnd(i=!0){return this._homeAndEnd=i,this}withPageUpDown(i=!0,e=10){return this._pageUpAndDown={enabled:i,delta:e},this}setActiveItem(i){let e=this._activeItem();this.updateActiveItem(i),this._activeItem()!==e&&this.change.next(this._activeItemIndex())}onKeydown(i){let e=i.keyCode,r=[`altKey`,`ctrlKey`,`metaKey`,`shiftKey`].every(o=>!i[o]||this._allowedModifierKeys.indexOf(o)>-1);switch(e){case 9:this.tabOut.next();return;case 40:if(this._vertical&&r){this.setNextItemActive();break}else return;case 38:if(this._vertical&&r){this.setPreviousItemActive();break}else return;case 39:if(this._horizontal&&r){this._horizontal===`rtl`?this.setPreviousItemActive():this.setNextItemActive();break}else return;case 37:if(this._horizontal&&r){this._horizontal===`rtl`?this.setNextItemActive():this.setPreviousItemActive();break}else return;case 36:if(this._homeAndEnd&&r){this.setFirstItemActive();break}else return;case 35:if(this._homeAndEnd&&r){this.setLastItemActive();break}else return;case 33:if(this._pageUpAndDown.enabled&&r){let o=this._activeItemIndex()-this._pageUpAndDown.delta;this._setActiveItemByIndex(o>0?o:0,1);break}else return;case 34:if(this._pageUpAndDown.enabled&&r){let o=this._activeItemIndex()+this._pageUpAndDown.delta,a=this._getItemsArray().length;this._setActiveItemByIndex(o<a?o:a-1,-1);break}else return;default:(r||Me(i,`shiftKey`))&&this._typeahead?.handleKey(i);return}this._typeahead?.reset(),i.preventDefault()}get activeItemIndex(){return this._activeItemIndex()}get activeItem(){return this._activeItem()}isTyping(){return!!this._typeahead&&this._typeahead.isTyping()}setFirstItemActive(){this._setActiveItemByIndex(0,1)}setLastItemActive(){this._setActiveItemByIndex(this._getItemsArray().length-1,-1)}setNextItemActive(){this._activeItemIndex()<0?this.setFirstItemActive():this._setActiveItemByDelta(1)}setPreviousItemActive(){this._activeItemIndex()<0&&this._wrap?this.setLastItemActive():this._setActiveItemByDelta(-1)}updateActiveItem(i){let e=this._getItemsArray(),t=typeof i==`number`?i:e.indexOf(i),r=e[t];this._activeItem.set(r??null),this._activeItemIndex.set(t),this._typeahead?.setCurrentSelectedItemIndex(t)}destroy(){this._typeaheadSubscription.unsubscribe(),this._itemChangesSubscription?.unsubscribe(),this._effectRef?.destroy(),this._typeahead?.destroy(),this.tabOut.complete(),this.change.complete()}_setActiveItemByDelta(i){this._wrap?this._setActiveInWrapMode(i):this._setActiveInDefaultMode(i)}_setActiveInWrapMode(i){let e=this._getItemsArray();for(let t=1;t<=e.length;t++){let r=(this._activeItemIndex()+i*t+e.length)%e.length,o=e[r];if(!this._skipPredicateFn(o)){this.setActiveItem(r);return}}}_setActiveInDefaultMode(i){this._setActiveItemByIndex(this._activeItemIndex()+i,i)}_setActiveItemByIndex(i,e){let t=this._getItemsArray();if(t[i]){for(;this._skipPredicateFn(t[i]);)if(i+=e,!t[i])return;this.setActiveItem(i)}}_getItemsArray(){return ia$1(this._items)?this._items():this._items instanceof ii$1?this._items.toArray():this._items}_itemsChanged(i){this._typeahead?.setItems(i);let e=this._activeItem();if(e){let t=i.indexOf(e);t>-1&&t!==this._activeItemIndex()&&(this._activeItemIndex.set(t),this._typeahead?.setCurrentSelectedItemIndex(t))}}};var Gi=class extends $n{setActiveItem(i){this.activeItem&&this.activeItem.setInactiveStyles(),super.setActiveItem(i),this.activeItem&&this.activeItem.setActiveStyles()}};var Wi=class extends $n{_origin=`program`;setFocusOrigin(i){return this._origin=i,this}setActiveItem(i){super.setActiveItem(i),this.activeItem&&this.activeItem.focus(this._origin)}};var Sc=` `;function bh(n,i,e){let t=ro(n,i);e=e.trim(),!t.some(r=>r.trim()===e)&&(t.push(e),n.setAttribute(i,t.join(Sc)))}function _h(n,i,e){let t=ro(n,i);e=e.trim();let r=t.filter(o=>o!==e);r.length?n.setAttribute(i,r.join(Sc)):n.removeAttribute(i)}function ro(n,i){return n.getAttribute(i)?.match(/\S+/g)??[]}var wc=`cdk-describedby-message`;var io=`cdk-describedby-host`;var Ba=0;var kc=(()=>{class n{_platform=I(J);_document=I(Bo);_messageRegistry=new Map;_messagesContainer=null;_id=`${Ba++}`;constructor(){I(Se).load(Un),this._id=I(Yu$1)+`-`+Ba++}describe(e,t,r){if(!this._canBeDescribed(e,t))return;let o=Va(t,r);typeof t!=`string`?(Cc(t,this._id),this._messageRegistry.set(o,{messageElement:t,referenceCount:0})):this._messageRegistry.has(o)||this._createMessageElement(t,r),this._isElementDescribedByMessage(e,o)||this._addMessageReference(e,o)}removeDescription(e,t,r){if(!t||!this._isElementNode(e))return;let o=Va(t,r);if(this._isElementDescribedByMessage(e,o)&&this._removeMessageReference(e,o),typeof t==`string`){let a=this._messageRegistry.get(o);a&&a.referenceCount===0&&this._deleteMessageElement(o)}this._messagesContainer?.childNodes.length===0&&(this._messagesContainer.remove(),this._messagesContainer=null)}ngOnDestroy(){let e=this._document.querySelectorAll(`[${io}="${this._id}"]`);for(let t=0;t<e.length;t++)this._removeCdkDescribedByReferenceIds(e[t]),e[t].removeAttribute(io);this._messagesContainer?.remove(),this._messagesContainer=null,this._messageRegistry.clear()}_createMessageElement(e,t){let r=this._document.createElement(`div`);Cc(r,this._id),r.textContent=e,t&&r.setAttribute(`role`,t),this._createMessagesContainer(),this._messagesContainer.appendChild(r),this._messageRegistry.set(Va(e,t),{messageElement:r,referenceCount:0})}_deleteMessageElement(e){this._messageRegistry.get(e)?.messageElement?.remove(),this._messageRegistry.delete(e)}_createMessagesContainer(){if(this._messagesContainer)return;let e=`cdk-describedby-message-container`,t=this._document.querySelectorAll(`.${e}[platform="server"]`);for(let o=0;o<t.length;o++)t[o].remove();let r=this._document.createElement(`div`);r.style.visibility=`hidden`,r.classList.add(e),r.classList.add(`cdk-visually-hidden`),this._platform.isBrowser||r.setAttribute(`platform`,`server`),this._document.body.appendChild(r),this._messagesContainer=r}_removeCdkDescribedByReferenceIds(e){let t=ro(e,`aria-describedby`).filter(r=>r.indexOf(wc)!=0);e.setAttribute(`aria-describedby`,t.join(` `))}_addMessageReference(e,t){let r=this._messageRegistry.get(t);bh(e,`aria-describedby`,r.messageElement.id),e.setAttribute(io,this._id),r.referenceCount++}_removeMessageReference(e,t){let r=this._messageRegistry.get(t);r.referenceCount--,_h(e,`aria-describedby`,r.messageElement.id),e.removeAttribute(io)}_isElementDescribedByMessage(e,t){let r=ro(e,`aria-describedby`),o=this._messageRegistry.get(t),a=o&&o.messageElement.id;return!!a&&r.indexOf(a)!=-1}_canBeDescribed(e,t){if(!this._isElementNode(e))return!1;if(t&&typeof t==`object`)return!0;let r=t==null?``:`${t}`.trim(),o=e.getAttribute(`aria-label`);return r?!o||o.trim()!==r:!1}_isElementNode(e){return e.nodeType===this._document.ELEMENT_NODE}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();function Va(n,i){return typeof n==`string`?`${i||``}/${n}`:n}function Cc(n,i){n.id||(n.id=`${wc}-${i}-${Ba++}`)}var ao=class{viewContainerRef;injector;id;role=`dialog`;panelClass=``;hasBackdrop=!0;backdropClass=``;disableClose=!1;closePredicate;width=``;height=``;minWidth;minHeight;maxWidth;maxHeight;position;data=null;direction;ariaDescribedBy=null;ariaLabelledBy=null;ariaLabel=null;ariaModal=!1;autoFocus=`first-tabbable`;restoreFocus=!0;delayFocusTrap=!0;scrollStrategy;closeOnNavigation=!0;enterAnimationDuration;exitAnimationDuration;bindings};var za=`mdc-dialog--open`;var Dc=`mdc-dialog--opening`;var Ec=`mdc-dialog--closing`;var yh=150;var vh=75;var xh=(()=>{class n extends Fa{_animationStateChanged=new Fe;_animationsEnabled=!ue();_actionSectionCount=0;_hostElement=this._elementRef.nativeElement;_enterAnimationDuration=this._animationsEnabled?Ac(this._config.enterAnimationDuration)??yh:0;_exitAnimationDuration=this._animationsEnabled?Ac(this._config.exitAnimationDuration)??vh:0;_animationTimer=null;_contentAttached(){super._contentAttached(),this._startOpenAnimation()}_startOpenAnimation(){this._animationStateChanged.emit({state:`opening`,totalTime:this._enterAnimationDuration}),this._animationsEnabled?(this._hostElement.style.setProperty(Mc,`${this._enterAnimationDuration}ms`),this._requestAnimationFrame(()=>this._hostElement.classList.add(Dc,za)),this._waitForAnimationToComplete(this._enterAnimationDuration,this._finishDialogOpen)):(this._hostElement.classList.add(za),Promise.resolve().then(()=>this._finishDialogOpen()))}_startExitAnimation(){this._animationStateChanged.emit({state:`closing`,totalTime:this._exitAnimationDuration}),this._hostElement.classList.remove(za),this._animationsEnabled?(this._hostElement.style.setProperty(Mc,`${this._exitAnimationDuration}ms`),this._requestAnimationFrame(()=>this._hostElement.classList.add(Ec)),this._waitForAnimationToComplete(this._exitAnimationDuration,this._finishDialogClose)):Promise.resolve().then(()=>this._finishDialogClose())}_updateActionSectionCount(e){this._actionSectionCount+=e,this._changeDetectorRef.markForCheck()}_finishDialogOpen=()=>{this._clearAnimationClasses(),this._openAnimationDone(this._enterAnimationDuration)};_finishDialogClose=()=>{this._clearAnimationClasses(),this._animationStateChanged.emit({state:`closed`,totalTime:this._exitAnimationDuration})};_clearAnimationClasses(){this._hostElement.classList.remove(Dc,Ec)}_waitForAnimationToComplete(e,t){this._animationTimer!==null&&clearTimeout(this._animationTimer),this._animationTimer=setTimeout(t,e)}_requestAnimationFrame(e){this._ngZone.runOutsideAngular(()=>{typeof requestAnimationFrame==`function`?requestAnimationFrame(e):e()})}_captureInitialFocus(){this._config.delayFocusTrap||this._trapFocus()}_openAnimationDone(e){this._config.delayFocusTrap&&this._trapFocus(),this._animationStateChanged.next({state:`opened`,totalTime:e})}ngOnDestroy(){super.ngOnDestroy(),this._animationTimer!==null&&clearTimeout(this._animationTimer)}attachComponentPortal(e){let t=super.attachComponentPortal(e);return t.location.nativeElement.classList.add(`mat-mdc-dialog-component-host`),t}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵcmp=(function(){function e(t,r){}return LI({type:n,selectors:[[`mat-dialog-container`]],hostAttrs:[`tabindex`,`-1`,1,`mat-mdc-dialog-container`,`mdc-dialog`],hostVars:10,hostBindings:function(r,o){r&2&&(rh$1(`id`,o._config.id),Kp(`aria-modal`,o._config.ariaModal)(`role`,o._config.role)(`aria-labelledby`,o._config.ariaLabel?null:o._ariaLabelledByQueue[0])(`aria-label`,o._config.ariaLabel)(`aria-describedby`,o._config.ariaDescribedBy||null),yh$1(`_mat-animation-noopable`,!o._animationsEnabled)(`mat-mdc-dialog-container-with-actions`,o._actionSectionCount>0))},features:[Vp$1],decls:3,vars:0,consts:[[1,`mat-mdc-dialog-inner-container`,`mdc-dialog__container`],[1,`mat-mdc-dialog-surface`,`mdc-dialog__surface`],[`cdkPortalOutlet`,``]],template:function(r,o){r&1&&(yi(0,`div`,0)(1,`div`,1),Bp$1(2,e,0,0,`ng-template`,2),Fc$1()())},dependencies:[Yt],styles:[`.mat-mdc-dialog-container {
  width: 100%;
  height: 100%;
  display: block;
  box-sizing: border-box;
  max-height: inherit;
  min-height: inherit;
  min-width: inherit;
  max-width: inherit;
  outline: 0;
}

.cdk-overlay-pane.mat-mdc-dialog-panel {
  max-width: var(--%NS%mat-dialog-container-max-width, 560px);
  min-width: var(--%NS%mat-dialog-container-min-width, 280px);
}
@media (max-width: 599px) {
  .cdk-overlay-pane.mat-mdc-dialog-panel {
    max-width: var(--%NS%mat-dialog-container-small-max-width, calc(100vw - 32px));
  }
}

.mat-mdc-dialog-inner-container {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-around;
  box-sizing: border-box;
  height: 100%;
  opacity: 0;
  transition: opacity linear var(--%NS%mat-dialog-transition-duration, 0ms);
  max-height: inherit;
  min-height: inherit;
  min-width: inherit;
  max-width: inherit;
}
.mdc-dialog--closing .mat-mdc-dialog-inner-container {
  transition: opacity 75ms linear;
  transform: none;
}
.mdc-dialog--open .mat-mdc-dialog-inner-container {
  opacity: 1;
}
._mat-animation-noopable .mat-mdc-dialog-inner-container {
  transition: none;
}

.mat-mdc-dialog-surface {
  display: flex;
  flex-direction: column;
  flex-grow: 0;
  flex-shrink: 0;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  position: relative;
  overflow-y: auto;
  outline: 0;
  transform: scale(0.8);
  transition: transform var(--%NS%mat-dialog-transition-duration, 0ms) cubic-bezier(0, 0, 0.2, 1);
  max-height: inherit;
  min-height: inherit;
  min-width: inherit;
  max-width: inherit;
  box-shadow: var(--%NS%mat-dialog-container-elevation-shadow, none);
  border-radius: var(--%NS%mat-dialog-container-shape, var(--%NS%mat-sys-corner-extra-large, 4px));
  background-color: var(--%NS%mat-dialog-container-color, var(--%NS%mat-sys-surface, white));
}
[dir=rtl] .mat-mdc-dialog-surface {
  text-align: right;
}
.mdc-dialog--open .mat-mdc-dialog-surface, .mdc-dialog--closing .mat-mdc-dialog-surface {
  transform: none;
}
._mat-animation-noopable .mat-mdc-dialog-surface {
  transition: none;
}
.mat-mdc-dialog-surface::before {
  position: absolute;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  border: 2px solid transparent;
  border-radius: inherit;
  content: "";
  pointer-events: none;
}

.mat-mdc-dialog-title {
  display: block;
  position: relative;
  flex-shrink: 0;
  box-sizing: border-box;
  margin: 0 0 1px;
  padding: var(--%NS%mat-dialog-headline-padding, 6px 24px 13px);
}
.mat-mdc-dialog-title::before {
  display: inline-block;
  width: 0;
  height: 40px;
  content: "";
  vertical-align: 0;
}
[dir=rtl] .mat-mdc-dialog-title {
  text-align: right;
}
.mat-mdc-dialog-container .mat-mdc-dialog-title {
  color: var(--%NS%mat-dialog-subhead-color, var(--%NS%mat-sys-on-surface, rgba(0, 0, 0, 0.87)));
  font-family: var(--%NS%mat-dialog-subhead-font, var(--%NS%mat-sys-headline-small-font, inherit));
  line-height: var(--%NS%mat-dialog-subhead-line-height, var(--%NS%mat-sys-headline-small-line-height, 1.5rem));
  font-size: var(--%NS%mat-dialog-subhead-size, var(--%NS%mat-sys-headline-small-size, 1rem));
  font-weight: var(--%NS%mat-dialog-subhead-weight, var(--%NS%mat-sys-headline-small-weight, 400));
  letter-spacing: var(--%NS%mat-dialog-subhead-tracking, var(--%NS%mat-sys-headline-small-tracking, 0.03125em));
}

.mat-mdc-dialog-content {
  display: block;
  flex-grow: 1;
  box-sizing: border-box;
  margin: 0;
  overflow: auto;
  max-height: 65vh;
}
.mat-mdc-dialog-content > :first-child {
  margin-top: 0;
}
.mat-mdc-dialog-content > :last-child {
  margin-bottom: 0;
}
.mat-mdc-dialog-container .mat-mdc-dialog-content {
  color: var(--%NS%mat-dialog-supporting-text-color, var(--%NS%mat-sys-on-surface-variant, rgba(0, 0, 0, 0.6)));
  font-family: var(--%NS%mat-dialog-supporting-text-font, var(--%NS%mat-sys-body-medium-font, inherit));
  line-height: var(--%NS%mat-dialog-supporting-text-line-height, var(--%NS%mat-sys-body-medium-line-height, 1.5rem));
  font-size: var(--%NS%mat-dialog-supporting-text-size, var(--%NS%mat-sys-body-medium-size, 1rem));
  font-weight: var(--%NS%mat-dialog-supporting-text-weight, var(--%NS%mat-sys-body-medium-weight, 400));
  letter-spacing: var(--%NS%mat-dialog-supporting-text-tracking, var(--%NS%mat-sys-body-medium-tracking, 0.03125em));
}
.mat-mdc-dialog-container .mat-mdc-dialog-content {
  padding: var(--%NS%mat-dialog-content-padding, 20px 24px);
}
.mat-mdc-dialog-container-with-actions .mat-mdc-dialog-content {
  padding: var(--%NS%mat-dialog-with-actions-content-padding, 20px 24px 0);
}
.mat-mdc-dialog-container .mat-mdc-dialog-title + .mat-mdc-dialog-content {
  padding-top: 0;
}

.mat-mdc-dialog-actions {
  display: flex;
  position: relative;
  flex-shrink: 0;
  flex-wrap: wrap;
  align-items: center;
  box-sizing: border-box;
  min-height: 52px;
  margin: 0;
  border-top: 1px solid transparent;
  padding: var(--%NS%mat-dialog-actions-padding, 16px 24px);
  justify-content: var(--%NS%mat-dialog-actions-alignment, flex-end);
}
@media (forced-colors: active) {
  .mat-mdc-dialog-actions {
    border-top-color: CanvasText;
  }
}
.mat-mdc-dialog-actions.mat-mdc-dialog-actions-align-start, .mat-mdc-dialog-actions[align=start] {
  justify-content: start;
}
.mat-mdc-dialog-actions.mat-mdc-dialog-actions-align-center, .mat-mdc-dialog-actions[align=center] {
  justify-content: center;
}
.mat-mdc-dialog-actions.mat-mdc-dialog-actions-align-end, .mat-mdc-dialog-actions[align=end] {
  justify-content: flex-end;
}
.mat-mdc-dialog-actions .mat-button-base + .mat-button-base,
.mat-mdc-dialog-actions .mat-mdc-button-base + .mat-mdc-button-base {
  margin-left: 8px;
}
[dir=rtl] .mat-mdc-dialog-actions .mat-button-base + .mat-button-base,
[dir=rtl] .mat-mdc-dialog-actions .mat-mdc-button-base + .mat-mdc-button-base {
  margin-left: 0;
  margin-right: 8px;
}

.mat-mdc-dialog-component-host {
  display: contents;
}
`],encapsulation:2,changeDetection:1})})()}return n})();var Mc=`--mat-dialog-transition-duration`;function Ac(n){return n==null?null:typeof n==`number`?n:n.endsWith(`ms`)?dt(n.substring(0,n.length-2)):n.endsWith(`s`)?dt(n.substring(0,n.length-1))*1e3:n===`0`?0:null}var oo=(function(n){return n[n.OPEN=0]=`OPEN`,n[n.CLOSING=1]=`CLOSING`,n[n.CLOSED=2]=`CLOSED`,n})(oo||{});var gt=class{_ref;_config;_containerInstance;componentInstance;componentRef=null;disableClose;id;_afterOpened=new Bn$1(1);_beforeClosed=new Bn$1(1);_result;_closeFallbackTimeout;_state=oo.OPEN;_closeInteractionType;constructor(i,e,t){this._ref=i,this._config=e,this._containerInstance=t,this.disableClose=e.disableClose,this.id=i.id,i.addPanelClass(`mat-mdc-dialog-panel`),t._animationStateChanged.pipe(rn(r=>r.state===`opened`),gt$1(1)).subscribe(()=>{this._afterOpened.next(),this._afterOpened.complete()}),t._animationStateChanged.pipe(rn(r=>r.state===`closed`),gt$1(1)).subscribe(()=>{clearTimeout(this._closeFallbackTimeout),this._finishDialogClose()}),i.overlayRef.detachments().subscribe(()=>{this._beforeClosed.next(this._result),this._beforeClosed.complete(),this._finishDialogClose()}),Bg(this.backdropClick(),this.keydownEvents().pipe(rn(r=>r.keyCode===27&&!this.disableClose&&!Me(r)))).subscribe(r=>{this.disableClose||(r.preventDefault(),Ic(this,r.type===`keydown`?`keyboard`:`mouse`))})}close(i){let e=this._config.closePredicate;e&&!e(i,this._config,this.componentInstance)||(this._result=i,this._containerInstance._animationStateChanged.pipe(rn(t=>t.state===`closing`),gt$1(1)).subscribe(t=>{this._beforeClosed.next(i),this._beforeClosed.complete(),this._ref.overlayRef.detachBackdrop(),this._closeFallbackTimeout=setTimeout(()=>this._finishDialogClose(),t.totalTime+100)}),this._state=oo.CLOSING,this._containerInstance._startExitAnimation())}afterOpened(){return this._afterOpened}afterClosed(){return this._ref.closed}beforeClosed(){return this._beforeClosed}backdropClick(){return this._ref.backdropClick}keydownEvents(){return this._ref.keydownEvents}updatePosition(i){let e=this._ref.config.positionStrategy;return i&&(i.left||i.right)?i.left?e.left(i.left):e.right(i.right):e.centerHorizontally(),i&&(i.top||i.bottom)?i.top?e.top(i.top):e.bottom(i.bottom):e.centerVertically(),this._ref.updatePosition(),this}updateSize(i=``,e=``){return this._ref.updateSize(i,e),this}addPanelClass(i){return this._ref.addPanelClass(i),this}removePanelClass(i){return this._ref.removePanelClass(i),this}getState(){return this._state}_finishDialogClose(){this._state=oo.CLOSED,this._ref.close(this._result,{focusOrigin:this._closeInteractionType}),this.componentInstance=null}};function Ic(n,i,e){return n._closeInteractionType=i,n.close(e)}var vn=new S(`MatMdcDialogData`);var Ch=new S(`mat-mdc-dialog-default-options`);var Sh=new S(`mat-mdc-dialog-scroll-strategy`,{providedIn:`root`,factory:()=>{let n=I(le);return()=>zn(n)}});var Lt=(()=>{class n{_defaultOptions=I(Ch,{optional:!0});_scrollStrategy=I(Sh);_parentDialog=I(n,{optional:!0,skipSelf:!0});_idGenerator=I(me);_injector=I(le);_dialog=I(Pa);_animationsDisabled=ue();_openDialogsAtThisLevel=[];_afterAllClosedAtThisLevel=new te$1;_afterOpenedAtThisLevel=new te$1;dialogConfigClass=ao;_dialogRefConstructor;_dialogContainerType;_dialogDataToken;get openDialogs(){return this._parentDialog?this._parentDialog.openDialogs:this._openDialogsAtThisLevel}get afterOpened(){return this._parentDialog?this._parentDialog.afterOpened:this._afterOpenedAtThisLevel}_getAfterAllClosed(){let e=this._parentDialog;return e?e._getAfterAllClosed():this._afterAllClosedAtThisLevel}afterAllClosed=Og(()=>this.openDialogs.length?this._getAfterAllClosed():this._getAfterAllClosed().pipe(Al$1(void 0)));constructor(){this._dialogRefConstructor=gt,this._dialogContainerType=xh,this._dialogDataToken=vn}open(e,t){let r;t=$($({},this._defaultOptions||new ao),t),t.id=t.id||this._idGenerator.getId(`mat-mdc-dialog-`),t.scrollStrategy=t.scrollStrategy||this._scrollStrategy();let o=this._dialog.open(e,Y($({},t),{positionStrategy:Xt(this._injector).centerHorizontally().centerVertically(),disableClose:!0,closePredicate:void 0,closeOnDestroy:!1,closeOnOverlayDetachments:!1,disableAnimations:this._animationsDisabled||t.enterAnimationDuration?.toLocaleString()===`0`||t.exitAnimationDuration?.toString()===`0`,container:{type:this._dialogContainerType,providers:()=>[{provide:this.dialogConfigClass,useValue:t},{provide:qt,useValue:t}]},templateContext:()=>({dialogRef:r}),providers:(a,s,c)=>(r=new this._dialogRefConstructor(a,t,c),r.updatePosition(t?.position),[{provide:this._dialogContainerType,useValue:c},{provide:this._dialogDataToken,useValue:s.data},{provide:this._dialogRefConstructor,useValue:r},{provide:yn,useValue:null}])}));return r.componentRef=o.componentRef,r.componentInstance=o.componentInstance,this.openDialogs.push(r),this.afterOpened.next(r),r.afterClosed().subscribe(()=>{let a=this.openDialogs.indexOf(r);a>-1&&(this.openDialogs.splice(a,1),this.openDialogs.length||this._getAfterAllClosed().next())}),r}closeAll(){this._closeDialogs(this.openDialogs)}getDialogById(e){return this.openDialogs.find(t=>t.id===e)}ngOnDestroy(){this._closeDialogs(this._openDialogsAtThisLevel),this._afterAllClosedAtThisLevel.complete(),this._afterOpenedAtThisLevel.complete()}_closeDialogs(e){let t=e.length;for(;t--;)e[t].close()}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Qx=(()=>{class n{dialogRef=I(gt,{optional:!0});_elementRef=I(Dr);_dialog=I(Lt);ariaLabel;type=`button`;dialogResult;_matDialogClose;ngOnInit(){this.dialogRef||(this.dialogRef=Tc(this._elementRef,this._dialog.openDialogs))}ngOnChanges(e){let t=e._matDialogClose;t&&(this.dialogResult=t.currentValue)}_onButtonClick(e){this._elementRef.nativeElement.getAttribute(`aria-disabled`)!==`true`&&Ic(this.dialogRef,e.screenX===0&&e.screenY===0?`keyboard`:`mouse`,this.dialogResult)}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`mat-dialog-close`,``],[``,`matDialogClose`,``]],hostVars:2,hostBindings:function(t,r){t&1&&ih$1(`click`,function(a){return r._onButtonClick(a)}),t&2&&Kp(`aria-label`,r.ariaLabel||null)(`type`,r.type)},inputs:{ariaLabel:[0,`aria-label`,`ariaLabel`],type:`type`,dialogResult:[0,`mat-dialog-close`,`dialogResult`],_matDialogClose:[0,`matDialogClose`,`_matDialogClose`]},exportAs:[`matDialogClose`],features:[iy]})}return n})();var Nc=(()=>{class n{_dialogRef=I(gt,{optional:!0});_elementRef=I(Dr);_dialog=I(Lt);ngOnInit(){this._dialogRef||(this._dialogRef=Tc(this._elementRef,this._dialog.openDialogs)),this._dialogRef&&Promise.resolve().then(()=>{this._onAdd()})}ngOnDestroy(){this._dialogRef?._containerInstance&&Promise.resolve().then(()=>{this._onRemove()})}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n})}return n})();var Gn=(()=>{class n extends Nc{id=I(me).getId(`mat-mdc-dialog-title-`);_onAdd(){this._dialogRef._containerInstance?._addAriaLabelledBy?.(this.id)}_onRemove(){this._dialogRef?._containerInstance?._removeAriaLabelledBy?.(this.id)}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[``,`mat-dialog-title`,``],[``,`matDialogTitle`,``]],hostAttrs:[1,`mat-mdc-dialog-title`,`mdc-dialog__title`],hostVars:1,hostBindings:function(t,r){t&2&&rh$1(`id`,r.id)},inputs:{id:`id`},exportAs:[`matDialogTitle`],features:[Vp$1]})}return n})();var Wn=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`mat-dialog-content`,``],[`mat-dialog-content`],[``,`matDialogContent`,``]],hostAttrs:[1,`mat-mdc-dialog-content`,`mdc-dialog__content`],features:[GI([Ca])]})}return n})();var Yn=(()=>{class n extends Nc{align;_onAdd(){this._dialogRef._containerInstance?._updateActionSectionCount?.(1)}_onRemove(){this._dialogRef._containerInstance?._updateActionSectionCount?.(-1)}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[``,`mat-dialog-actions`,``],[`mat-dialog-actions`],[``,`matDialogActions`,``]],hostAttrs:[1,`mat-mdc-dialog-actions`,`mdc-dialog__actions`],hostVars:6,hostBindings:function(t,r){t&2&&yh$1(`mat-mdc-dialog-actions-align-start`,r.align===`start`)(`mat-mdc-dialog-actions-align-center`,r.align===`center`)(`mat-mdc-dialog-actions-align-end`,r.align===`end`)},inputs:{align:`align`},features:[Vp$1]})}return n})();function Tc(n,i){let e=n.nativeElement.parentElement;for(;e&&!e.classList.contains(`mat-mdc-dialog-container`);)e=e.parentElement;return e?i.find(t=>t.id===e.id):null}var Jx=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({providers:[Lt],imports:[_c,Ke,Rt,te]})}return n})();var Kn;var Rc=[`color`,`button`,`checkbox`,`date`,`datetime-local`,`email`,`file`,`hidden`,`image`,`month`,`number`,`password`,`radio`,`range`,`reset`,`search`,`submit`,`tel`,`text`,`time`,`url`,`week`];function ja(){if(Kn)return Kn;if(typeof document!=`object`||!document)return Kn=new Set(Rc),Kn;let n=document.createElement(`input`);return Kn=new Set(Rc.filter(i=>(n.setAttribute(`type`,i),n.type===i))),Kn}var ot=(function(n){return n[n.FADING_IN=0]=`FADING_IN`,n[n.VISIBLE=1]=`VISIBLE`,n[n.FADING_OUT=2]=`FADING_OUT`,n[n.HIDDEN=3]=`HIDDEN`,n})(ot||{});var Ua=class{_renderer;element;config;_animationForciblyDisabledThroughCss;state=ot.HIDDEN;constructor(i,e,t,r=!1){this._renderer=i,this.element=e,this.config=t,this._animationForciblyDisabledThroughCss=r}fadeOut(){this._renderer.fadeOutRipple(this)}};var Oc=jn({passive:!0,capture:!0});var Ha=class{_events=new Map;addHandler(i,e,t,r){let o=this._events.get(e);if(o){let a=o.get(t);a?a.add(r):o.set(t,new Set([r]))}else this._events.set(e,new Map([[t,new Set([r])]])),i.runOutsideAngular(()=>{document.addEventListener(e,this._delegateEventHandler,Oc)})}removeHandler(i,e,t){let r=this._events.get(i);if(!r)return;let o=r.get(e);o&&(o.delete(t),o.size===0&&r.delete(e),r.size===0&&(this._events.delete(i),document.removeEventListener(i,this._delegateEventHandler,Oc)))}_delegateEventHandler=i=>{let e=Ie(i);e&&this._events.get(i.type)?.forEach((t,r)=>{(r===e||r.contains(e))&&t.forEach(o=>o.handleEvent(i))})}};var Yi={enterDuration:225,exitDuration:150};var wh=800;var Fc=jn({passive:!0,capture:!0});var Pc=[`mousedown`,`touchstart`];var Lc=[`mouseup`,`mouseleave`,`touchend`,`touchcancel`];var kh=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵcmp=LI({type:n,selectors:[[`ng-component`]],hostAttrs:[`mat-ripple-style-loader`,``],decls:0,vars:0,template:function(t,r){},styles:[`.mat-ripple {
  overflow: hidden;
  position: relative;
}
.mat-ripple:not(:empty) {
  transform: translateZ(0);
}

.mat-ripple.mat-ripple-unbounded {
  overflow: visible;
}

.mat-ripple-element {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  transition: opacity, transform 0ms cubic-bezier(0, 0, 0.2, 1);
  transform: scale3d(0, 0, 0);
  background-color: var(--%NS%mat-ripple-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 10%, transparent));
}
@media (forced-colors: active) {
  .mat-ripple-element {
    display: none;
  }
}
.cdk-drag-preview .mat-ripple-element, .cdk-drag-placeholder .mat-ripple-element {
  display: none;
}
`],encapsulation:2})}return n})();var Xi=class n{_target;_ngZone;_platform;_containerElement;_triggerElement=null;_isPointerDown=!1;_activeRipples=new Map;_mostRecentTransientRipple=null;_lastTouchStartEvent;_pointerUpEventsRegistered=!1;_containerRect=null;static _eventManager=new Ha;constructor(i,e,t,r,o){this._target=i,this._ngZone=e,this._platform=r,r.isBrowser&&(this._containerElement=je(t)),o&&o.get(Se).load(kh)}fadeInRipple(i,e,t={}){let r=this._containerRect=this._containerRect||this._containerElement.getBoundingClientRect(),o=$($({},Yi),t.animation);t.centered&&(i=r.left+r.width/2,e=r.top+r.height/2);let a=t.radius||Dh(i,e,r),s=i-r.left,c=e-r.top,d=o.enterDuration,m=document.createElement(`div`);m.classList.add(`mat-ripple-element`),m.style.left=`${s-a}px`,m.style.top=`${c-a}px`,m.style.height=`${a*2}px`,m.style.width=`${a*2}px`,t.color!=null&&(m.style.backgroundColor=t.color),m.style.transitionDuration=`${d}ms`,this._containerElement.appendChild(m);let _=window.getComputedStyle(m),k=_.transitionProperty,p=_.transitionDuration,z=k===`none`||p===`0s`||p===`0s, 0s`||r.width===0&&r.height===0,K=new Ua(this,m,t,z);m.style.transform=`scale3d(1, 1, 1)`,K.state=ot.FADING_IN,t.persistent||(this._mostRecentTransientRipple=K);let fe=null;return!z&&(d||o.exitDuration)&&this._ngZone.runOutsideAngular(()=>{let St=()=>{fe&&(fe.fallbackTimer=null),clearTimeout(wt),this._finishRippleTransition(K)},qe=()=>this._destroyRipple(K),wt=setTimeout(qe,d+100);m.addEventListener(`transitionend`,St),m.addEventListener(`transitioncancel`,qe),fe={onTransitionEnd:St,onTransitionCancel:qe,fallbackTimer:wt}}),this._activeRipples.set(K,fe),(z||!d)&&this._finishRippleTransition(K),K}fadeOutRipple(i){if(i.state===ot.FADING_OUT||i.state===ot.HIDDEN)return;let e=i.element,t=$($({},Yi),i.config.animation);e.style.transitionDuration=`${t.exitDuration}ms`,e.style.opacity=`0`,i.state=ot.FADING_OUT,(i._animationForciblyDisabledThroughCss||!t.exitDuration)&&this._finishRippleTransition(i)}fadeOutAll(){this._getActiveRipples().forEach(i=>i.fadeOut())}fadeOutAllNonPersistent(){this._getActiveRipples().forEach(i=>{i.config.persistent||i.fadeOut()})}setupTriggerEvents(i){let e=je(i);!this._platform.isBrowser||!e||e===this._triggerElement||(this._removeTriggerEvents(),this._triggerElement=e,Pc.forEach(t=>{n._eventManager.addHandler(this._ngZone,t,e,this)}))}handleEvent(i){i.type===`mousedown`?this._onMousedown(i):i.type===`touchstart`?this._onTouchStart(i):this._onPointerUp(),this._pointerUpEventsRegistered||(this._ngZone.runOutsideAngular(()=>{Lc.forEach(e=>{this._triggerElement.addEventListener(e,this,Fc)})}),this._pointerUpEventsRegistered=!0)}_finishRippleTransition(i){i.state===ot.FADING_IN?this._startFadeOutTransition(i):i.state===ot.FADING_OUT&&this._destroyRipple(i)}_startFadeOutTransition(i){let e=i===this._mostRecentTransientRipple,{persistent:t}=i.config;i.state=ot.VISIBLE,!t&&(!e||!this._isPointerDown)&&i.fadeOut()}_destroyRipple(i){let e=this._activeRipples.get(i)??null;this._activeRipples.delete(i),this._activeRipples.size||(this._containerRect=null),i===this._mostRecentTransientRipple&&(this._mostRecentTransientRipple=null),i.state=ot.HIDDEN,e!==null&&(i.element.removeEventListener(`transitionend`,e.onTransitionEnd),i.element.removeEventListener(`transitioncancel`,e.onTransitionCancel),e.fallbackTimer!==null&&clearTimeout(e.fallbackTimer)),i.element.remove()}_onMousedown(i){let e=fn(i),t=this._lastTouchStartEvent&&Date.now()<this._lastTouchStartEvent+wh;!this._target.rippleDisabled&&!e&&!t&&(this._isPointerDown=!0,this.fadeInRipple(i.clientX,i.clientY,this._target.rippleConfig))}_onTouchStart(i){if(!this._target.rippleDisabled&&!gn(i)){this._lastTouchStartEvent=Date.now(),this._isPointerDown=!0;let e=i.changedTouches;if(e)for(let t=0;t<e.length;t++)this.fadeInRipple(e[t].clientX,e[t].clientY,this._target.rippleConfig)}}_onPointerUp(){this._isPointerDown&&(this._isPointerDown=!1,this._getActiveRipples().forEach(i=>{let e=i.state===ot.VISIBLE||i.config.terminateOnPointerUp&&i.state===ot.FADING_IN;!i.config.persistent&&e&&i.fadeOut()}))}_getActiveRipples(){return Array.from(this._activeRipples.keys())}_removeTriggerEvents(){let i=this._triggerElement;i&&(Pc.forEach(e=>n._eventManager.removeHandler(e,i,this)),this._pointerUpEventsRegistered&&(Lc.forEach(e=>i.removeEventListener(e,this,Fc)),this._pointerUpEventsRegistered=!1))}};function Dh(n,i,e){let t=Math.max(Math.abs(n-e.left),Math.abs(n-e.right)),r=Math.max(Math.abs(i-e.top),Math.abs(i-e.bottom));return Math.sqrt(t*t+r*r)}var $a=new S(`mat-ripple-global-options`);var qn=(()=>{class n{_elementRef=I(Dr);_animationsDisabled=ue();color;unbounded=!1;centered=!1;radius=0;animation;get disabled(){return this._disabled}set disabled(e){e&&this.fadeOutAllNonPersistent(),this._disabled=e,this._setupTriggerEventsIfEnabled()}_disabled=!1;get trigger(){return this._trigger||this._elementRef.nativeElement}set trigger(e){this._trigger=e,this._setupTriggerEventsIfEnabled()}_trigger;_rippleRenderer;_globalOptions;_isInitialized=!1;constructor(){let e=I(z),t=I(J),r=I($a,{optional:!0}),o=I(le);this._globalOptions=r||{},this._rippleRenderer=new Xi(this,e,this._elementRef,t,o)}ngOnInit(){this._isInitialized=!0,this._setupTriggerEventsIfEnabled()}ngOnDestroy(){this._rippleRenderer._removeTriggerEvents()}fadeOutAll(){this._rippleRenderer.fadeOutAll()}fadeOutAllNonPersistent(){this._rippleRenderer.fadeOutAllNonPersistent()}get rippleConfig(){return{centered:this.centered,radius:this.radius,color:this.color,animation:$($($({},this._globalOptions.animation),this._animationsDisabled?{enterDuration:0,exitDuration:0}:{}),this.animation),terminateOnPointerUp:this._globalOptions.terminateOnPointerUp}}get rippleDisabled(){return this.disabled||!!this._globalOptions.disabled}_setupTriggerEventsIfEnabled(){!this.disabled&&this._isInitialized&&this._rippleRenderer.setupTriggerEvents(this.trigger)}launch(e,t=0,r){return typeof e==`number`?this._rippleRenderer.fadeInRipple(e,t,$($({},this.rippleConfig),r)):this._rippleRenderer.fadeInRipple(0,0,$($({},this.rippleConfig),e))}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`mat-ripple`,``],[``,`matRipple`,``]],hostAttrs:[1,`mat-ripple`],hostVars:2,hostBindings:function(t,r){t&2&&yh$1(`mat-ripple-unbounded`,r.unbounded)},inputs:{color:[0,`matRippleColor`,`color`],unbounded:[0,`matRippleUnbounded`,`unbounded`],centered:[0,`matRippleCentered`,`centered`],radius:[0,`matRippleRadius`,`radius`],animation:[0,`matRippleAnimation`,`animation`],disabled:[0,`matRippleDisabled`,`disabled`],trigger:[0,`matRippleTrigger`,`trigger`]},exportAs:[`matRipple`]})}return n})();var Eh={capture:!0};var Mh=[`focus`,`mousedown`,`mouseenter`,`touchstart`];var Ga=`mat-ripple-loader-uninitialized`;var Wa=`mat-ripple-loader-class-name`;var Vc=`mat-ripple-loader-centered`;var so=`mat-ripple-loader-disabled`;var Bc=(()=>{class n{_document=I(Bo);_animationsDisabled=ue();_globalRippleOptions=I($a,{optional:!0});_platform=I(J);_ngZone=I(z);_injector=I(le);_eventCleanups;_hosts=new Map;constructor(){let e=I(mr$1).createRenderer(null,null);this._eventCleanups=this._ngZone.runOutsideAngular(()=>Mh.map(t=>e.listen(this._document,t,this._onInteraction,Eh)))}ngOnDestroy(){let e=this._hosts.keys();for(let t of e)this.destroyRipple(t);this._eventCleanups.forEach(t=>t())}configureRipple(e,t){e.setAttribute(Ga,this._globalRippleOptions?.namespace??``),(t.className||!e.hasAttribute(Wa))&&e.setAttribute(Wa,t.className||``),t.centered&&e.setAttribute(Vc,``),t.disabled&&e.setAttribute(so,``)}setDisabled(e,t){let r=this._hosts.get(e);r?(r.target.rippleDisabled=t,!t&&!r.hasSetUpEvents&&(r.hasSetUpEvents=!0,r.renderer.setupTriggerEvents(e))):t?e.setAttribute(so,``):e.removeAttribute(so)}_onInteraction=e=>{let t=Ie(e);if(t instanceof HTMLElement){let r=t.closest(`[${Ga}="${this._globalRippleOptions?.namespace??``}"]`);r&&this._createRipple(r)}};_createRipple(e){if(!this._document||this._hosts.has(e))return;e.querySelector(`.mat-ripple`)?.remove();let t=this._document.createElement(`span`);t.classList.add(`mat-ripple`,e.getAttribute(Wa)),e.append(t);let r=this._globalRippleOptions,o=this._animationsDisabled?0:r?.animation?.enterDuration??Yi.enterDuration,a=this._animationsDisabled?0:r?.animation?.exitDuration??Yi.exitDuration,s={rippleDisabled:this._animationsDisabled||r?.disabled||e.hasAttribute(so),rippleConfig:{centered:e.hasAttribute(Vc),terminateOnPointerUp:r?.terminateOnPointerUp,animation:{enterDuration:o,exitDuration:a}}},c=new Xi(s,this._ngZone,t,this._platform,this._injector),d=!s.rippleDisabled;d&&c.setupTriggerEvents(e),this._hosts.set(e,{target:s,renderer:c,hasSetUpEvents:d}),e.removeAttribute(Ga)}destroyRipple(e){let t=this._hosts.get(e);t&&(t.renderer._removeTriggerEvents(),this._hosts.delete(e))}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Zt=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵcmp=LI({type:n,selectors:[[`structural-styles`]],decls:0,vars:0,template:function(t,r){},styles:[`.mat-focus-indicator {
  position: relative;
}
.mat-focus-indicator::before {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  position: absolute;
  box-sizing: border-box;
  pointer-events: none;
  display: var(--%NS%mat-focus-indicator-display, none);
  border-width: var(--%NS%mat-focus-indicator-border-width, 3px);
  border-style: var(--%NS%mat-focus-indicator-border-style, solid);
  border-color: var(--%NS%mat-focus-indicator-border-color, transparent);
  border-radius: var(--%NS%mat-focus-indicator-border-radius, 4px);
}
.mat-focus-indicator:focus-visible::before {
  content: "";
}

@media (forced-colors: active) {
  html {
    --%NS%mat-focus-indicator-display: block;
    --%NS%mat-focus-indicator-fallback-border-style: none;
  }
}
`],encapsulation:2})}return n})();var Ah=new S(`MAT_BUTTON_CONFIG`);function zc(n){return n==null?void 0:C0(n)}var Ya=(()=>{class n{_elementRef=I(Dr);_ngZone=I(z);_animationsDisabled=ue();_config=I(Ah,{optional:!0});_focusMonitor=I(ft);_cleanupClick;_renderer=I(La$1);_rippleLoader=I(Bc);_isAnchor;_isFab=!1;color;get disableRipple(){return this._disableRipple}set disableRipple(e){this._disableRipple=e,this._updateRippleDisabled()}_disableRipple=!1;get disabled(){return this._disabled}set disabled(e){this._disabled=e,this._updateRippleDisabled()}_disabled=!1;ariaDisabled;disabledInteractive;tabIndex;set _tabindex(e){this.tabIndex=e}showProgress=y0(!1,{transform:T0});constructor(){I(Se).load(Zt);let e=this._elementRef.nativeElement;this._isAnchor=e.tagName===`A`,this.disabledInteractive=this._config?.disabledInteractive??!1,this.color=this._config?.color??null,this._rippleLoader?.configureRipple(e,{className:`mat-mdc-button-ripple`})}ngAfterViewInit(){this._focusMonitor.monitor(this._elementRef,!0),this._isAnchor&&this._setupAsAnchor()}ngOnDestroy(){this._cleanupClick?.(),this._focusMonitor.stopMonitoring(this._elementRef),this._rippleLoader?.destroyRipple(this._elementRef.nativeElement)}focus(e=`program`,t){e?this._focusMonitor.focusVia(this._elementRef.nativeElement,e,t):this._elementRef.nativeElement.focus(t)}_getAriaDisabled(){return this.ariaDisabled!=null?this.ariaDisabled:this._isAnchor?this.disabled||null:this.disabled&&this.disabledInteractive?!0:null}_getDisabledAttribute(){return this.disabledInteractive||!this.disabled?null:!0}_updateRippleDisabled(){this._rippleLoader?.setDisabled(this._elementRef.nativeElement,this.disableRipple||this.disabled)}_getTabIndex(){return this._isAnchor?this.disabled&&!this.disabledInteractive?-1:this.tabIndex:this.tabIndex}_setupAsAnchor(){this._cleanupClick=this._ngZone.runOutsideAngular(()=>this._renderer.listen(this._elementRef.nativeElement,`click`,e=>{this.disabled&&(e.preventDefault(),e.stopImmediatePropagation())}))}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,hostAttrs:[1,`mat-mdc-button-base`],hostVars:15,hostBindings:function(t,r){t&2&&(Kp(`disabled`,r._getDisabledAttribute())(`aria-disabled`,r._getAriaDisabled())(`tabindex`,r._getTabIndex()),zD(r.color?`mat-`+r.color:``),yh$1(`mat-mdc-button-progress-indicator-shown`,r.showProgress())(`mat-mdc-button-disabled`,r.disabled)(`mat-mdc-button-disabled-interactive`,r.disabledInteractive)(`mat-unthemed`,!r.color)(`_mat-animation-noopable`,r._animationsDisabled))},inputs:{color:`color`,disableRipple:[2,`disableRipple`,`disableRipple`,T0],disabled:[2,`disabled`,`disabled`,T0],ariaDisabled:[2,`aria-disabled`,`ariaDisabled`,T0],disabledInteractive:[2,`disabledInteractive`,`disabledInteractive`,T0],tabIndex:[2,`tabIndex`,`tabIndex`,zc],_tabindex:[2,`tabindex`,`_tabindex`,zc],showProgress:[1,`showProgress`]}})}return n})();var Ki=(()=>{class n extends Ya{constructor(){super(),this._rippleLoader.configureRipple(this._elementRef.nativeElement,{centered:!0})}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`*`,[[``,`progressIndicator`,``]]],t=[`*`,`[progressIndicator]`];function r(o,a){o&1&&(jc$1(0,`div`,1),ND(1,1),Vc$1())}return LI({type:n,selectors:[[`button`,`mat-icon-button`,``],[`a`,`mat-icon-button`,``],[`button`,`matIconButton`,``],[`a`,`matIconButton`,``]],hostAttrs:[1,`mdc-icon-button`,`mat-mdc-icon-button`],exportAs:[`matButton`,`matAnchor`],features:[Vp$1],ngContentSelectors:t,decls:5,vars:1,consts:[[1,`mat-mdc-button-persistent-ripple`,`mdc-icon-button__ripple`],[1,`mat-mdc-button-progress-indicator-container`],[1,`mat-focus-indicator`],[1,`mat-mdc-button-touch-target`]],template:function(a,s){a&1&&(_D(e),eh$1(0,`span`,0),ND(1),uD(2,r,2,0,`div`,1),eh$1(3,`span`,2)(4,`span`,3)),a&2&&(sE(2),fD(s.showProgress()?2:-1))},styles:[`.mat-mdc-icon-button {
  -webkit-user-select: none;
  user-select: none;
  display: inline-block;
  position: relative;
  box-sizing: border-box;
  border: none;
  outline: none;
  background-color: transparent;
  fill: currentColor;
  text-decoration: none;
  cursor: pointer;
  z-index: 0;
  overflow: visible;
  border-radius: var(--%NS%mat-icon-button-container-shape, var(--%NS%mat-sys-corner-full, 50%));
  flex-shrink: 0;
  text-align: center;
  width: var(--%NS%mat-icon-button-state-layer-size, 40px);
  height: var(--%NS%mat-icon-button-state-layer-size, 40px);
  padding: calc(calc(var(--%NS%mat-icon-button-state-layer-size, 40px) - var(--%NS%mat-icon-button-icon-size, 24px)) / 2);
  font-size: var(--%NS%mat-icon-button-icon-size, 24px);
  color: var(--%NS%mat-icon-button-icon-color, var(--%NS%mat-sys-on-surface-variant));
  -webkit-tap-highlight-color: transparent;
}
.mat-mdc-icon-button .mat-mdc-button-ripple,
.mat-mdc-icon-button .mat-mdc-button-persistent-ripple,
.mat-mdc-icon-button .mat-mdc-button-persistent-ripple::before {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  position: absolute;
  pointer-events: none;
  border-radius: inherit;
}
.mat-mdc-icon-button .mat-mdc-button-ripple {
  overflow: hidden;
}
.mat-mdc-icon-button .mat-mdc-button-persistent-ripple::before {
  content: "";
  opacity: 0;
}
.mat-mdc-icon-button .mdc-button__label,
.mat-mdc-icon-button .mat-icon {
  z-index: 1;
  position: relative;
}
.mat-mdc-icon-button .mat-focus-indicator {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  position: absolute;
  border-radius: inherit;
}
.mat-mdc-icon-button:focus-visible > .mat-focus-indicator::before {
  content: "";
  border-radius: inherit;
}
.mat-mdc-icon-button .mat-ripple-element {
  background-color: var(--%NS%mat-icon-button-ripple-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface-variant) calc(var(--%NS%mat-sys-pressed-state-layer-opacity) * 100%), transparent));
}
.mat-mdc-icon-button .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-icon-button-state-layer-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-mdc-icon-button.mat-mdc-button-disabled .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-icon-button-disabled-state-layer-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-mdc-icon-button:hover > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-icon-button-hover-state-layer-opacity, var(--%NS%mat-sys-hover-state-layer-opacity));
}
.mat-mdc-icon-button.cdk-program-focused > .mat-mdc-button-persistent-ripple::before, .mat-mdc-icon-button.cdk-keyboard-focused > .mat-mdc-button-persistent-ripple::before, .mat-mdc-icon-button.mat-mdc-button-disabled-interactive:focus > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-icon-button-focus-state-layer-opacity, var(--%NS%mat-sys-focus-state-layer-opacity));
}
.mat-mdc-icon-button:active > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-icon-button-pressed-state-layer-opacity, var(--%NS%mat-sys-pressed-state-layer-opacity));
}
.mat-mdc-icon-button .mat-mdc-button-touch-target {
  position: absolute;
  top: 50%;
  height: var(--%NS%mat-icon-button-touch-target-size, 48px);
  display: var(--%NS%mat-icon-button-touch-target-display, block);
  left: 50%;
  width: var(--%NS%mat-icon-button-touch-target-size, 48px);
  transform: translate(-50%, -50%);
}
.mat-mdc-icon-button._mat-animation-noopable {
  transition: none !important;
  animation: none !important;
}
.mat-mdc-icon-button[disabled], .mat-mdc-icon-button.mat-mdc-button-disabled {
  cursor: default;
  pointer-events: none;
  color: var(--%NS%mat-icon-button-disabled-icon-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-mdc-icon-button.mat-mdc-button-disabled-interactive {
  pointer-events: auto;
}
.mat-mdc-icon-button img,
.mat-mdc-icon-button svg {
  width: var(--%NS%mat-icon-button-icon-size, 24px);
  height: var(--%NS%mat-icon-button-icon-size, 24px);
  vertical-align: baseline;
}
.mat-mdc-icon-button .mat-mdc-button-progress-indicator-container .mdc-circular-progress__determinate-circle-graphic {
  width: inherit;
  height: inherit;
}
.mat-mdc-icon-button .mat-mdc-button-progress-indicator-container .mdc-circular-progress__indeterminate-circle-graphic {
  height: 100%;
}
.mat-mdc-icon-button .mat-mdc-button-persistent-ripple {
  border-radius: var(--%NS%mat-icon-button-container-shape, var(--%NS%mat-sys-corner-full, 50%));
}
.mat-mdc-icon-button[hidden] {
  display: none;
}
.mat-mdc-icon-button.mat-unthemed:not(.mdc-ripple-upgraded):focus::before, .mat-mdc-icon-button.mat-primary:not(.mdc-ripple-upgraded):focus::before, .mat-mdc-icon-button.mat-accent:not(.mdc-ripple-upgraded):focus::before, .mat-mdc-icon-button.mat-warn:not(.mdc-ripple-upgraded):focus::before {
  background: transparent;
  opacity: 1;
}

.mat-mdc-button-progress-indicator-container {
  position: absolute;
  inset-inline-start: 0;
  inset-block-start: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.mat-mdc-button-progress-indicator-shown mat-icon {
  visibility: hidden;
}
`,`@media (forced-colors: active) {
  .mat-mdc-button:not(.mdc-button--outlined),
  .mat-mdc-unelevated-button:not(.mdc-button--outlined),
  .mat-mdc-raised-button:not(.mdc-button--outlined),
  .mat-mdc-outlined-button:not(.mdc-button--outlined),
  .mat-mdc-button-base.mat-tonal-button,
  .mat-mdc-icon-button.mat-mdc-icon-button,
  .mat-mdc-outlined-button .mdc-button__ripple {
    outline: solid 1px;
  }
}
`],encapsulation:2})})()}return n})();var Zn=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[te]})}return n})();var jc=new Map([[`text`,[`mat-mdc-button`]],[`filled`,[`mdc-button--unelevated`,`mat-mdc-unelevated-button`]],[`elevated`,[`mdc-button--raised`,`mat-mdc-raised-button`]],[`outlined`,[`mdc-button--outlined`,`mat-mdc-outlined-button`]],[`tonal`,[`mat-tonal-button`]]]);var Qt=(()=>{class n extends Ya{get appearance(){return this._appearance}set appearance(e){this.setAppearance(e||this._config?.defaultAppearance||`text`)}_appearance=null;constructor(){super();let e=Ih(this._elementRef.nativeElement);e&&this.setAppearance(e)}setAppearance(e){if(e===this._appearance)return;let t=this._elementRef.nativeElement.classList,r=this._appearance?jc.get(this._appearance):null,o=jc.get(e);r&&t.remove(...r),t.add(...o),this._appearance=e}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[[[``,8,`material-icons`,3,`iconPositionEnd`,``],[`mat-icon`,3,`iconPositionEnd`,``],[``,`matButtonIcon`,``,3,`iconPositionEnd`,``],[``,8,`material-symbols-outlined`,3,`iconPositionEnd`,``],[``,8,`material-symbols-rounded`,3,`iconPositionEnd`,``],[``,8,`material-symbols-sharp`,3,`iconPositionEnd`,``]],`*`,[[``,`iconPositionEnd`,``,8,`material-icons`],[`mat-icon`,`iconPositionEnd`,``],[``,`matButtonIcon`,``,`iconPositionEnd`,``],[``,`iconPositionEnd`,``,8,`material-symbols-outlined`],[``,`iconPositionEnd`,``,8,`material-symbols-rounded`],[``,`iconPositionEnd`,``,8,`material-symbols-sharp`]],[[``,`progressIndicator`,``]]],t=[`.material-icons:not([iconPositionEnd]), mat-icon:not([iconPositionEnd]), [matButtonIcon]:not([iconPositionEnd]), .material-symbols-outlined:not([iconPositionEnd]), .material-symbols-rounded:not([iconPositionEnd]), .material-symbols-sharp:not([iconPositionEnd])`,`*`,`.material-icons[iconPositionEnd], mat-icon[iconPositionEnd], [matButtonIcon][iconPositionEnd], .material-symbols-outlined[iconPositionEnd], .material-symbols-rounded[iconPositionEnd], .material-symbols-sharp[iconPositionEnd]`,`[progressIndicator]`];function r(o,a){o&1&&(jc$1(0,`div`,2),ND(1,3),Vc$1())}return LI({type:n,selectors:[[`button`,`matButton`,``],[`a`,`matButton`,``],[`button`,`mat-button`,``],[`button`,`mat-raised-button`,``],[`button`,`mat-flat-button`,``],[`button`,`mat-stroked-button`,``],[`a`,`mat-button`,``],[`a`,`mat-raised-button`,``],[`a`,`mat-flat-button`,``],[`a`,`mat-stroked-button`,``]],hostAttrs:[1,`mdc-button`],inputs:{appearance:[0,`matButton`,`appearance`]},exportAs:[`matButton`,`matAnchor`],features:[Vp$1],ngContentSelectors:t,decls:8,vars:5,consts:[[1,`mat-mdc-button-persistent-ripple`],[1,`mdc-button__label`],[1,`mat-mdc-button-progress-indicator-container`],[1,`mat-focus-indicator`],[1,`mat-mdc-button-touch-target`]],template:function(a,s){a&1&&(_D(e),eh$1(0,`span`,0),ND(1),jc$1(2,`span`,1),ND(3,1),Vc$1(),ND(4,2),uD(5,r,2,0,`div`,2),eh$1(6,`span`,3)(7,`span`,4)),a&2&&(yh$1(`mdc-button__ripple`,!s._isFab)(`mdc-fab__ripple`,s._isFab),sE(5),fD(s.showProgress()?5:-1))},styles:[`.mat-mdc-button-base {
  text-decoration: none;
}
.mat-mdc-button-base .mat-icon {
  min-height: fit-content;
  flex-shrink: 0;
}
@media (hover: none) {
  .mat-mdc-button-base:hover > span.mat-mdc-button-persistent-ripple::before {
    opacity: 0;
  }
}

.mdc-button {
  -webkit-user-select: none;
  user-select: none;
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  min-width: 64px;
  border: none;
  outline: none;
  line-height: inherit;
  -webkit-appearance: none;
  overflow: visible;
  vertical-align: middle;
  background: transparent;
  padding: 0 8px;
}
.mdc-button::-moz-focus-inner {
  padding: 0;
  border: 0;
}
.mdc-button:active {
  outline: none;
}
.mdc-button:hover {
  cursor: pointer;
}
.mdc-button:disabled {
  cursor: default;
  pointer-events: none;
}
.mdc-button[hidden] {
  display: none;
}
.mdc-button .mdc-button__label {
  position: relative;
}

.mat-mdc-button {
  padding: 0 var(--%NS%mat-button-text-horizontal-padding, 12px);
  height: var(--%NS%mat-button-text-container-height, 40px);
  font-family: var(--%NS%mat-button-text-label-text-font, var(--%NS%mat-sys-label-large-font));
  font-size: var(--%NS%mat-button-text-label-text-size, var(--%NS%mat-sys-label-large-size));
  letter-spacing: var(--%NS%mat-button-text-label-text-tracking, var(--%NS%mat-sys-label-large-tracking));
  text-transform: var(--%NS%mat-button-text-label-text-transform);
  font-weight: var(--%NS%mat-button-text-label-text-weight, var(--%NS%mat-sys-label-large-weight));
}
.mat-mdc-button, .mat-mdc-button .mdc-button__ripple {
  border-radius: var(--%NS%mat-button-text-container-shape, var(--%NS%mat-sys-corner-full));
}
.mat-mdc-button:not(:disabled) {
  color: var(--%NS%mat-button-text-label-text-color, var(--%NS%mat-sys-primary));
}
.mat-mdc-button[disabled], .mat-mdc-button.mat-mdc-button-disabled {
  cursor: default;
  pointer-events: none;
  color: var(--%NS%mat-button-text-disabled-label-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-mdc-button.mat-mdc-button-disabled-interactive {
  pointer-events: auto;
}
.mat-mdc-button:has(.material-icons, .material-symbols-outlined, .material-symbols-rounded,
.material-symbols-sharp, mat-icon, [matButtonIcon]) {
  padding: 0 var(--%NS%mat-button-text-with-icon-horizontal-padding, 16px);
}
.mat-mdc-button > .mat-icon {
  margin-right: var(--%NS%mat-button-text-icon-spacing, 8px);
  margin-left: var(--%NS%mat-button-text-icon-offset, -4px);
}
[dir=rtl] .mat-mdc-button > .mat-icon {
  margin-right: var(--%NS%mat-button-text-icon-offset, -4px);
  margin-left: var(--%NS%mat-button-text-icon-spacing, 8px);
}
.mat-mdc-button .mdc-button__label + .mat-icon {
  margin-right: var(--%NS%mat-button-text-icon-offset, -4px);
  margin-left: var(--%NS%mat-button-text-icon-spacing, 8px);
}
[dir=rtl] .mat-mdc-button .mdc-button__label + .mat-icon {
  margin-right: var(--%NS%mat-button-text-icon-spacing, 8px);
  margin-left: var(--%NS%mat-button-text-icon-offset, -4px);
}
.mat-mdc-button .mat-ripple-element {
  background-color: var(--%NS%mat-button-text-ripple-color, color-mix(in srgb, var(--%NS%mat-sys-primary) calc(var(--%NS%mat-sys-pressed-state-layer-opacity) * 100%), transparent));
}
.mat-mdc-button .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-button-text-state-layer-color, var(--%NS%mat-sys-primary));
}
.mat-mdc-button.mat-mdc-button-disabled .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-button-text-disabled-state-layer-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-mdc-button:hover > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-text-hover-state-layer-opacity, var(--%NS%mat-sys-hover-state-layer-opacity));
}
.mat-mdc-button.cdk-program-focused > .mat-mdc-button-persistent-ripple::before, .mat-mdc-button.cdk-keyboard-focused > .mat-mdc-button-persistent-ripple::before, .mat-mdc-button.mat-mdc-button-disabled-interactive:focus > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-text-focus-state-layer-opacity, var(--%NS%mat-sys-focus-state-layer-opacity));
}
.mat-mdc-button:active > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-text-pressed-state-layer-opacity, var(--%NS%mat-sys-pressed-state-layer-opacity));
}
.mat-mdc-button .mat-mdc-button-touch-target {
  position: absolute;
  top: 50%;
  height: var(--%NS%mat-button-text-touch-target-size, 48px);
  display: var(--%NS%mat-button-text-touch-target-display, block);
  left: 0;
  right: 0;
  transform: translateY(-50%);
}

.mat-mdc-unelevated-button {
  transition: box-shadow 280ms cubic-bezier(0.4, 0, 0.2, 1);
  height: var(--%NS%mat-button-filled-container-height, 40px);
  font-family: var(--%NS%mat-button-filled-label-text-font, var(--%NS%mat-sys-label-large-font));
  font-size: var(--%NS%mat-button-filled-label-text-size, var(--%NS%mat-sys-label-large-size));
  letter-spacing: var(--%NS%mat-button-filled-label-text-tracking, var(--%NS%mat-sys-label-large-tracking));
  text-transform: var(--%NS%mat-button-filled-label-text-transform);
  font-weight: var(--%NS%mat-button-filled-label-text-weight, var(--%NS%mat-sys-label-large-weight));
  padding: 0 var(--%NS%mat-button-filled-horizontal-padding, 24px);
}
.mat-mdc-unelevated-button > .mat-icon {
  margin-right: var(--%NS%mat-button-filled-icon-spacing, 8px);
  margin-left: var(--%NS%mat-button-filled-icon-offset, -8px);
}
[dir=rtl] .mat-mdc-unelevated-button > .mat-icon {
  margin-right: var(--%NS%mat-button-filled-icon-offset, -8px);
  margin-left: var(--%NS%mat-button-filled-icon-spacing, 8px);
}
.mat-mdc-unelevated-button .mdc-button__label + .mat-icon {
  margin-right: var(--%NS%mat-button-filled-icon-offset, -8px);
  margin-left: var(--%NS%mat-button-filled-icon-spacing, 8px);
}
[dir=rtl] .mat-mdc-unelevated-button .mdc-button__label + .mat-icon {
  margin-right: var(--%NS%mat-button-filled-icon-spacing, 8px);
  margin-left: var(--%NS%mat-button-filled-icon-offset, -8px);
}
.mat-mdc-unelevated-button .mat-ripple-element {
  background-color: var(--%NS%mat-button-filled-ripple-color, color-mix(in srgb, var(--%NS%mat-sys-on-primary) calc(var(--%NS%mat-sys-pressed-state-layer-opacity) * 100%), transparent));
}
.mat-mdc-unelevated-button .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-button-filled-state-layer-color, var(--%NS%mat-sys-on-primary));
}
.mat-mdc-unelevated-button.mat-mdc-button-disabled .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-button-filled-disabled-state-layer-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-mdc-unelevated-button:hover > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-filled-hover-state-layer-opacity, var(--%NS%mat-sys-hover-state-layer-opacity));
}
.mat-mdc-unelevated-button.cdk-program-focused > .mat-mdc-button-persistent-ripple::before, .mat-mdc-unelevated-button.cdk-keyboard-focused > .mat-mdc-button-persistent-ripple::before, .mat-mdc-unelevated-button.mat-mdc-button-disabled-interactive:focus > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-filled-focus-state-layer-opacity, var(--%NS%mat-sys-focus-state-layer-opacity));
}
.mat-mdc-unelevated-button:active > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-filled-pressed-state-layer-opacity, var(--%NS%mat-sys-pressed-state-layer-opacity));
}
.mat-mdc-unelevated-button .mat-mdc-button-touch-target {
  position: absolute;
  top: 50%;
  height: var(--%NS%mat-button-filled-touch-target-size, 48px);
  display: var(--%NS%mat-button-filled-touch-target-display, block);
  left: 0;
  right: 0;
  transform: translateY(-50%);
}
.mat-mdc-unelevated-button:not(:disabled) {
  color: var(--%NS%mat-button-filled-label-text-color, var(--%NS%mat-sys-on-primary));
  background-color: var(--%NS%mat-button-filled-container-color, var(--%NS%mat-sys-primary));
}
.mat-mdc-unelevated-button, .mat-mdc-unelevated-button .mdc-button__ripple {
  border-radius: var(--%NS%mat-button-filled-container-shape, var(--%NS%mat-sys-corner-full));
}
.mat-mdc-unelevated-button .mat-mdc-button-progress-indicator-container {
  --%NS%mat-progress-spinner-active-indicator-color: var(--%NS%mat-button-filled-progress-active-indicator-color, var(--%NS%mat-sys-on-primary));
}
.mat-mdc-unelevated-button[disabled], .mat-mdc-unelevated-button.mat-mdc-button-disabled {
  cursor: default;
  pointer-events: none;
  color: var(--%NS%mat-button-filled-disabled-label-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
  background-color: var(--%NS%mat-button-filled-disabled-container-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 12%, transparent));
}
.mat-mdc-unelevated-button.mat-mdc-button-disabled-interactive {
  pointer-events: auto;
}

.mat-mdc-raised-button {
  transition: box-shadow 280ms cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--%NS%mat-button-protected-container-elevation-shadow, var(--%NS%mat-sys-level1));
  height: var(--%NS%mat-button-protected-container-height, 40px);
  font-family: var(--%NS%mat-button-protected-label-text-font, var(--%NS%mat-sys-label-large-font));
  font-size: var(--%NS%mat-button-protected-label-text-size, var(--%NS%mat-sys-label-large-size));
  letter-spacing: var(--%NS%mat-button-protected-label-text-tracking, var(--%NS%mat-sys-label-large-tracking));
  text-transform: var(--%NS%mat-button-protected-label-text-transform);
  font-weight: var(--%NS%mat-button-protected-label-text-weight, var(--%NS%mat-sys-label-large-weight));
  padding: 0 var(--%NS%mat-button-protected-horizontal-padding, 24px);
}
.mat-mdc-raised-button > .mat-icon {
  margin-right: var(--%NS%mat-button-protected-icon-spacing, 8px);
  margin-left: var(--%NS%mat-button-protected-icon-offset, -8px);
}
[dir=rtl] .mat-mdc-raised-button > .mat-icon {
  margin-right: var(--%NS%mat-button-protected-icon-offset, -8px);
  margin-left: var(--%NS%mat-button-protected-icon-spacing, 8px);
}
.mat-mdc-raised-button .mdc-button__label + .mat-icon {
  margin-right: var(--%NS%mat-button-protected-icon-offset, -8px);
  margin-left: var(--%NS%mat-button-protected-icon-spacing, 8px);
}
[dir=rtl] .mat-mdc-raised-button .mdc-button__label + .mat-icon {
  margin-right: var(--%NS%mat-button-protected-icon-spacing, 8px);
  margin-left: var(--%NS%mat-button-protected-icon-offset, -8px);
}
.mat-mdc-raised-button .mat-ripple-element {
  background-color: var(--%NS%mat-button-protected-ripple-color, color-mix(in srgb, var(--%NS%mat-sys-primary) calc(var(--%NS%mat-sys-pressed-state-layer-opacity) * 100%), transparent));
}
.mat-mdc-raised-button .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-button-protected-state-layer-color, var(--%NS%mat-sys-primary));
}
.mat-mdc-raised-button.mat-mdc-button-disabled .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-button-protected-disabled-state-layer-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-mdc-raised-button:hover > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-protected-hover-state-layer-opacity, var(--%NS%mat-sys-hover-state-layer-opacity));
}
.mat-mdc-raised-button.cdk-program-focused > .mat-mdc-button-persistent-ripple::before, .mat-mdc-raised-button.cdk-keyboard-focused > .mat-mdc-button-persistent-ripple::before, .mat-mdc-raised-button.mat-mdc-button-disabled-interactive:focus > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-protected-focus-state-layer-opacity, var(--%NS%mat-sys-focus-state-layer-opacity));
}
.mat-mdc-raised-button:active > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-protected-pressed-state-layer-opacity, var(--%NS%mat-sys-pressed-state-layer-opacity));
}
.mat-mdc-raised-button .mat-mdc-button-touch-target {
  position: absolute;
  top: 50%;
  height: var(--%NS%mat-button-protected-touch-target-size, 48px);
  display: var(--%NS%mat-button-protected-touch-target-display, block);
  left: 0;
  right: 0;
  transform: translateY(-50%);
}
.mat-mdc-raised-button:not(:disabled) {
  color: var(--%NS%mat-button-protected-label-text-color, var(--%NS%mat-sys-primary));
  background-color: var(--%NS%mat-button-protected-container-color, var(--%NS%mat-sys-surface));
}
.mat-mdc-raised-button, .mat-mdc-raised-button .mdc-button__ripple {
  border-radius: var(--%NS%mat-button-protected-container-shape, var(--%NS%mat-sys-corner-full));
}
@media (hover: hover) {
  .mat-mdc-raised-button:hover {
    box-shadow: var(--%NS%mat-button-protected-hover-container-elevation-shadow, var(--%NS%mat-sys-level2));
  }
}
.mat-mdc-raised-button:focus {
  box-shadow: var(--%NS%mat-button-protected-focus-container-elevation-shadow, var(--%NS%mat-sys-level1));
}
.mat-mdc-raised-button:active, .mat-mdc-raised-button:focus:active {
  box-shadow: var(--%NS%mat-button-protected-pressed-container-elevation-shadow, var(--%NS%mat-sys-level1));
}
.mat-mdc-raised-button[disabled], .mat-mdc-raised-button.mat-mdc-button-disabled {
  cursor: default;
  pointer-events: none;
  color: var(--%NS%mat-button-protected-disabled-label-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
  background-color: var(--%NS%mat-button-protected-disabled-container-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 12%, transparent));
}
.mat-mdc-raised-button[disabled].mat-mdc-button-disabled, .mat-mdc-raised-button.mat-mdc-button-disabled.mat-mdc-button-disabled {
  box-shadow: var(--%NS%mat-button-protected-disabled-container-elevation-shadow, var(--%NS%mat-sys-level0));
}
.mat-mdc-raised-button.mat-mdc-button-disabled-interactive {
  pointer-events: auto;
}

.mat-mdc-outlined-button {
  border-style: solid;
  transition: border 280ms cubic-bezier(0.4, 0, 0.2, 1);
  height: var(--%NS%mat-button-outlined-container-height, 40px);
  font-family: var(--%NS%mat-button-outlined-label-text-font, var(--%NS%mat-sys-label-large-font));
  font-size: var(--%NS%mat-button-outlined-label-text-size, var(--%NS%mat-sys-label-large-size));
  letter-spacing: var(--%NS%mat-button-outlined-label-text-tracking, var(--%NS%mat-sys-label-large-tracking));
  text-transform: var(--%NS%mat-button-outlined-label-text-transform);
  font-weight: var(--%NS%mat-button-outlined-label-text-weight, var(--%NS%mat-sys-label-large-weight));
  border-radius: var(--%NS%mat-button-outlined-container-shape, var(--%NS%mat-sys-corner-full));
  border-width: var(--%NS%mat-button-outlined-outline-width, 1px);
  padding: 0 var(--%NS%mat-button-outlined-horizontal-padding, 24px);
}
.mat-mdc-outlined-button > .mat-icon {
  margin-right: var(--%NS%mat-button-outlined-icon-spacing, 8px);
  margin-left: var(--%NS%mat-button-outlined-icon-offset, -8px);
}
[dir=rtl] .mat-mdc-outlined-button > .mat-icon {
  margin-right: var(--%NS%mat-button-outlined-icon-offset, -8px);
  margin-left: var(--%NS%mat-button-outlined-icon-spacing, 8px);
}
.mat-mdc-outlined-button .mdc-button__label + .mat-icon {
  margin-right: var(--%NS%mat-button-outlined-icon-offset, -8px);
  margin-left: var(--%NS%mat-button-outlined-icon-spacing, 8px);
}
[dir=rtl] .mat-mdc-outlined-button .mdc-button__label + .mat-icon {
  margin-right: var(--%NS%mat-button-outlined-icon-spacing, 8px);
  margin-left: var(--%NS%mat-button-outlined-icon-offset, -8px);
}
.mat-mdc-outlined-button .mat-ripple-element {
  background-color: var(--%NS%mat-button-outlined-ripple-color, color-mix(in srgb, var(--%NS%mat-sys-primary) calc(var(--%NS%mat-sys-pressed-state-layer-opacity) * 100%), transparent));
}
.mat-mdc-outlined-button .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-button-outlined-state-layer-color, var(--%NS%mat-sys-primary));
}
.mat-mdc-outlined-button.mat-mdc-button-disabled .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-button-outlined-disabled-state-layer-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-mdc-outlined-button:hover > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-outlined-hover-state-layer-opacity, var(--%NS%mat-sys-hover-state-layer-opacity));
}
.mat-mdc-outlined-button.cdk-program-focused > .mat-mdc-button-persistent-ripple::before, .mat-mdc-outlined-button.cdk-keyboard-focused > .mat-mdc-button-persistent-ripple::before, .mat-mdc-outlined-button.mat-mdc-button-disabled-interactive:focus > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-outlined-focus-state-layer-opacity, var(--%NS%mat-sys-focus-state-layer-opacity));
}
.mat-mdc-outlined-button:active > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-outlined-pressed-state-layer-opacity, var(--%NS%mat-sys-pressed-state-layer-opacity));
}
.mat-mdc-outlined-button .mat-mdc-button-touch-target {
  position: absolute;
  top: 50%;
  height: var(--%NS%mat-button-outlined-touch-target-size, 48px);
  display: var(--%NS%mat-button-outlined-touch-target-display, block);
  left: 0;
  right: 0;
  transform: translateY(-50%);
}
.mat-mdc-outlined-button:not(:disabled) {
  color: var(--%NS%mat-button-outlined-label-text-color, var(--%NS%mat-sys-primary));
  border-color: var(--%NS%mat-button-outlined-outline-color, var(--%NS%mat-sys-outline));
}
.mat-mdc-outlined-button[disabled], .mat-mdc-outlined-button.mat-mdc-button-disabled {
  cursor: default;
  pointer-events: none;
  color: var(--%NS%mat-button-outlined-disabled-label-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
  border-color: var(--%NS%mat-button-outlined-disabled-outline-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 12%, transparent));
}
.mat-mdc-outlined-button.mat-mdc-button-disabled-interactive {
  pointer-events: auto;
}

.mat-tonal-button {
  transition: box-shadow 280ms cubic-bezier(0.4, 0, 0.2, 1);
  height: var(--%NS%mat-button-tonal-container-height, 40px);
  font-family: var(--%NS%mat-button-tonal-label-text-font, var(--%NS%mat-sys-label-large-font));
  font-size: var(--%NS%mat-button-tonal-label-text-size, var(--%NS%mat-sys-label-large-size));
  letter-spacing: var(--%NS%mat-button-tonal-label-text-tracking, var(--%NS%mat-sys-label-large-tracking));
  text-transform: var(--%NS%mat-button-tonal-label-text-transform);
  font-weight: var(--%NS%mat-button-tonal-label-text-weight, var(--%NS%mat-sys-label-large-weight));
  padding: 0 var(--%NS%mat-button-tonal-horizontal-padding, 24px);
}
.mat-tonal-button:not(:disabled) {
  color: var(--%NS%mat-button-tonal-label-text-color, var(--%NS%mat-sys-on-secondary-container));
  background-color: var(--%NS%mat-button-tonal-container-color, var(--%NS%mat-sys-secondary-container));
}
.mat-tonal-button, .mat-tonal-button .mdc-button__ripple {
  border-radius: var(--%NS%mat-button-tonal-container-shape, var(--%NS%mat-sys-corner-full));
}
.mat-tonal-button[disabled], .mat-tonal-button.mat-mdc-button-disabled {
  cursor: default;
  pointer-events: none;
  color: var(--%NS%mat-button-tonal-disabled-label-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
  background-color: var(--%NS%mat-button-tonal-disabled-container-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 12%, transparent));
}
.mat-tonal-button.mat-mdc-button-disabled-interactive {
  pointer-events: auto;
}
.mat-tonal-button > .mat-icon {
  margin-right: var(--%NS%mat-button-tonal-icon-spacing, 8px);
  margin-left: var(--%NS%mat-button-tonal-icon-offset, -8px);
}
[dir=rtl] .mat-tonal-button > .mat-icon {
  margin-right: var(--%NS%mat-button-tonal-icon-offset, -8px);
  margin-left: var(--%NS%mat-button-tonal-icon-spacing, 8px);
}
.mat-tonal-button .mdc-button__label + .mat-icon {
  margin-right: var(--%NS%mat-button-tonal-icon-offset, -8px);
  margin-left: var(--%NS%mat-button-tonal-icon-spacing, 8px);
}
[dir=rtl] .mat-tonal-button .mdc-button__label + .mat-icon {
  margin-right: var(--%NS%mat-button-tonal-icon-spacing, 8px);
  margin-left: var(--%NS%mat-button-tonal-icon-offset, -8px);
}
.mat-tonal-button .mat-ripple-element {
  background-color: var(--%NS%mat-button-tonal-ripple-color, color-mix(in srgb, var(--%NS%mat-sys-on-secondary-container) calc(var(--%NS%mat-sys-pressed-state-layer-opacity) * 100%), transparent));
}
.mat-tonal-button .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-button-tonal-state-layer-color, var(--%NS%mat-sys-on-secondary-container));
}
.mat-tonal-button.mat-mdc-button-disabled .mat-mdc-button-persistent-ripple::before {
  background-color: var(--%NS%mat-button-tonal-disabled-state-layer-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-tonal-button:hover > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-tonal-hover-state-layer-opacity, var(--%NS%mat-sys-hover-state-layer-opacity));
}
.mat-tonal-button.cdk-program-focused > .mat-mdc-button-persistent-ripple::before, .mat-tonal-button.cdk-keyboard-focused > .mat-mdc-button-persistent-ripple::before, .mat-tonal-button.mat-mdc-button-disabled-interactive:focus > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-tonal-focus-state-layer-opacity, var(--%NS%mat-sys-focus-state-layer-opacity));
}
.mat-tonal-button:active > .mat-mdc-button-persistent-ripple::before {
  opacity: var(--%NS%mat-button-tonal-pressed-state-layer-opacity, var(--%NS%mat-sys-pressed-state-layer-opacity));
}
.mat-tonal-button .mat-mdc-button-touch-target {
  position: absolute;
  top: 50%;
  height: var(--%NS%mat-button-tonal-touch-target-size, 48px);
  display: var(--%NS%mat-button-tonal-touch-target-display, block);
  left: 0;
  right: 0;
  transform: translateY(-50%);
}

.mat-mdc-button,
.mat-mdc-unelevated-button,
.mat-mdc-raised-button,
.mat-mdc-outlined-button,
.mat-tonal-button {
  -webkit-tap-highlight-color: transparent;
}
.mat-mdc-button .mat-mdc-button-ripple,
.mat-mdc-button .mat-mdc-button-persistent-ripple,
.mat-mdc-button .mat-mdc-button-persistent-ripple::before,
.mat-mdc-unelevated-button .mat-mdc-button-ripple,
.mat-mdc-unelevated-button .mat-mdc-button-persistent-ripple,
.mat-mdc-unelevated-button .mat-mdc-button-persistent-ripple::before,
.mat-mdc-raised-button .mat-mdc-button-ripple,
.mat-mdc-raised-button .mat-mdc-button-persistent-ripple,
.mat-mdc-raised-button .mat-mdc-button-persistent-ripple::before,
.mat-mdc-outlined-button .mat-mdc-button-ripple,
.mat-mdc-outlined-button .mat-mdc-button-persistent-ripple,
.mat-mdc-outlined-button .mat-mdc-button-persistent-ripple::before,
.mat-tonal-button .mat-mdc-button-ripple,
.mat-tonal-button .mat-mdc-button-persistent-ripple,
.mat-tonal-button .mat-mdc-button-persistent-ripple::before {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  position: absolute;
  pointer-events: none;
  border-radius: inherit;
}
.mat-mdc-button .mat-mdc-button-ripple,
.mat-mdc-unelevated-button .mat-mdc-button-ripple,
.mat-mdc-raised-button .mat-mdc-button-ripple,
.mat-mdc-outlined-button .mat-mdc-button-ripple,
.mat-tonal-button .mat-mdc-button-ripple {
  overflow: hidden;
}
.mat-mdc-button .mat-mdc-button-persistent-ripple::before,
.mat-mdc-unelevated-button .mat-mdc-button-persistent-ripple::before,
.mat-mdc-raised-button .mat-mdc-button-persistent-ripple::before,
.mat-mdc-outlined-button .mat-mdc-button-persistent-ripple::before,
.mat-tonal-button .mat-mdc-button-persistent-ripple::before {
  content: "";
  opacity: 0;
}
.mat-mdc-button .mdc-button__label,
.mat-mdc-button .mat-icon,
.mat-mdc-unelevated-button .mdc-button__label,
.mat-mdc-unelevated-button .mat-icon,
.mat-mdc-raised-button .mdc-button__label,
.mat-mdc-raised-button .mat-icon,
.mat-mdc-outlined-button .mdc-button__label,
.mat-mdc-outlined-button .mat-icon,
.mat-tonal-button .mdc-button__label,
.mat-tonal-button .mat-icon {
  z-index: 1;
  position: relative;
}
.mat-mdc-button .mat-focus-indicator,
.mat-mdc-unelevated-button .mat-focus-indicator,
.mat-mdc-raised-button .mat-focus-indicator,
.mat-mdc-outlined-button .mat-focus-indicator,
.mat-tonal-button .mat-focus-indicator {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  position: absolute;
  border-radius: inherit;
}
.mat-mdc-button:focus-visible > .mat-focus-indicator::before,
.mat-mdc-unelevated-button:focus-visible > .mat-focus-indicator::before,
.mat-mdc-raised-button:focus-visible > .mat-focus-indicator::before,
.mat-mdc-outlined-button:focus-visible > .mat-focus-indicator::before,
.mat-tonal-button:focus-visible > .mat-focus-indicator::before {
  content: "";
  border-radius: inherit;
}
.mat-mdc-button._mat-animation-noopable,
.mat-mdc-unelevated-button._mat-animation-noopable,
.mat-mdc-raised-button._mat-animation-noopable,
.mat-mdc-outlined-button._mat-animation-noopable,
.mat-tonal-button._mat-animation-noopable {
  transition: none !important;
  animation: none !important;
}
.mat-mdc-button > .mat-icon,
.mat-mdc-unelevated-button > .mat-icon,
.mat-mdc-raised-button > .mat-icon,
.mat-mdc-outlined-button > .mat-icon,
.mat-tonal-button > .mat-icon {
  display: inline-block;
  position: relative;
  vertical-align: top;
  font-size: 1.125rem;
  height: 1.125rem;
  width: 1.125rem;
}

.mat-mdc-outlined-button .mat-mdc-button-ripple,
.mat-mdc-outlined-button .mdc-button__ripple {
  top: -1px;
  left: -1px;
  bottom: -1px;
  right: -1px;
}

.mat-mdc-unelevated-button .mat-focus-indicator::before,
.mat-tonal-button .mat-focus-indicator::before,
.mat-mdc-raised-button .mat-focus-indicator::before {
  margin: calc(calc(var(--%NS%mat-focus-indicator-border-width, 3px) + 2px) * -1);
}

.mat-mdc-outlined-button .mat-focus-indicator::before {
  margin: calc(calc(var(--%NS%mat-focus-indicator-border-width, 3px) + 3px) * -1);
}

.mat-mdc-button-progress-indicator-container {
  position: absolute;
  inset-inline-start: 0;
  inset-block-start: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.mat-mdc-button-progress-indicator-shown mat-icon,
.mat-mdc-button-progress-indicator-shown [matButtonIcon],
.mat-mdc-button-progress-indicator-shown .mdc-button__label {
  visibility: hidden;
}
`,`@media (forced-colors: active) {
  .mat-mdc-button:not(.mdc-button--outlined),
  .mat-mdc-unelevated-button:not(.mdc-button--outlined),
  .mat-mdc-raised-button:not(.mdc-button--outlined),
  .mat-mdc-outlined-button:not(.mdc-button--outlined),
  .mat-mdc-button-base.mat-tonal-button,
  .mat-mdc-icon-button.mat-mdc-icon-button,
  .mat-mdc-outlined-button .mdc-button__ripple {
    outline: solid 1px;
  }
}
`],encapsulation:2})})()}return n})();function Ih(n){return n.hasAttribute(`mat-raised-button`)?`elevated`:n.hasAttribute(`mat-stroked-button`)?`outlined`:n.hasAttribute(`mat-flat-button`)?`filled`:n.hasAttribute(`mat-button`)?`text`:null}var Uc=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[Zn,te]})}return n})();var Qc=(()=>{class n{_renderer;_elementRef;onChange=e=>{};onTouched=()=>{};constructor(e,t){this._renderer=e,this._elementRef=t}setProperty(e,t){this._renderer.setProperty(this._elementRef.nativeElement,e,t)}registerOnTouched(e){this.onTouched=e}registerOnChange(e){this.onChange=e}setDisabledState(e){this.setProperty(`disabled`,e)}static ɵfac=function(t){return new(t||n)(Mr(La$1),Mr(Dr))};static ɵdir=VI({type:n})}return n})();var vo=(()=>{class n extends Qc{static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,features:[Vp$1]})}return n})();var Bt=new S(``);var Nh={provide:Bt,useExisting:Io$1(()=>xo),multi:!0};function Th(){let n=Xe()?Xe().getUserAgent():``;return/android (\d+)/.test(n.toLowerCase())}var Rh=new S(``);var xo=(()=>{class n extends Qc{_compositionMode;_composing=!1;constructor(e,t,r){super(e,t),this._compositionMode=r,this._compositionMode??=!Th()}writeValue(e){let t=e??``;this.setProperty(`value`,t)}_handleInput(e){(!this._compositionMode||this._compositionMode&&!this._composing)&&this.onChange(e)}_compositionStart(){this._composing=!0}_compositionEnd(e){this._composing=!1,this._compositionMode&&this.onChange(e)}static ɵfac=function(t){return new(t||n)(Mr(La$1),Mr(Dr),Mr(Rh,8))};static ɵdir=VI({type:n,selectors:[[`input`,`formControlName`,``,3,`type`,`checkbox`,3,`ngNoCva`,``],[`textarea`,`formControlName`,``,3,`ngNoCva`,``],[`input`,`formControl`,``,3,`type`,`checkbox`,3,`ngNoCva`,``],[`textarea`,`formControl`,``,3,`ngNoCva`,``],[`input`,`ngModel`,``,3,`type`,`checkbox`,3,`ngNoCva`,``],[`textarea`,`ngModel`,``,3,`ngNoCva`,``],[``,`ngDefaultControl`,``]],hostBindings:function(t,r){t&1&&ih$1(`input`,function(a){return r._handleInput(a.target.value)})(`blur`,function(){return r.onTouched()})(`compositionstart`,function(){return r._compositionStart()})(`compositionend`,function(a){return r._compositionEnd(a.target.value)})},standalone:!1,features:[hw([Nh]),Vp$1]})}return n})();function Qa(n){return n==null||Ja(n)===0}function Ja(n){return n==null?null:Array.isArray(n)||typeof n==`string`?n.length:n instanceof Set?n.size:null}var at=new S(``);var nr=new S(``);var Oh=/^(?=.{1,254}$)(?=.{1,64}@)[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;var Ct=class{static min(i){return Jc(i)}static max(i){return ed(i)}static required(i){return td(i)}static requiredTrue(i){return Fh(i)}static email(i){return Ph(i)}static minLength(i){return nd(i)}static maxLength(i){return id(i)}static pattern(i){return Lh(i)}static nullValidator(i){return co()}static compose(i){return cd(i)}static composeAsync(i){return dd(i)}};function Jc(n){return i=>{if(i.value==null||n==null)return null;let e=parseFloat(i.value);return!isNaN(e)&&e<n?{min:{min:n,actual:i.value}}:null}}function ed(n){return i=>{if(i.value==null||n==null)return null;let e=parseFloat(i.value);return!isNaN(e)&&e>n?{max:{max:n,actual:i.value}}:null}}function td(n){return Qa(n.value)?{required:!0}:null}function Fh(n){return n.value===!0?null:{required:!0}}function Ph(n){return Qa(n.value)||Oh.test(n.value)?null:{email:!0}}function nd(n){return i=>{let e=i.value?.length??Ja(i.value);return e===null||e===0?null:e<n?{minlength:{requiredLength:n,actualLength:e}}:null}}function id(n){return i=>{let e=i.value?.length??Ja(i.value);return e!==null&&e>n?{maxlength:{requiredLength:n,actualLength:e}}:null}}function Lh(n){if(!n)return co;let i,e;return typeof n==`string`?(e=``,n.charAt(0)!==`^`&&(e+=`^`),e+=n,n.charAt(n.length-1)!==`$`&&(e+=`$`),i=new RegExp(e)):(e=n.toString(),i=n),t=>{if(Qa(t.value))return null;let r=t.value;return i.test(r)?null:{pattern:{requiredPattern:e,actualValue:r}}}}function co(n){return null}function rd(n){return n!=null}function od(n){return Ac$1(n)?Ne$1(n):n}function ad(n){let i={};return n.forEach(e=>{i=e!=null?$($({},i),e):i}),Object.keys(i).length===0?null:i}function sd(n,i){return i.map(e=>e(n))}function Vh(n){return!n.validate}function ld(n){return n.map(i=>Vh(i)?i:e=>i.validate(e))}function cd(n){if(!n)return null;let i=n.filter(rd);return i.length==0?null:function(e){return ad(sd(e,i))}}function es(n){return n!=null?cd(ld(n)):null}function dd(n){if(!n)return null;let i=n.filter(rd);return i.length==0?null:function(e){let t=sd(e,i).map(od);return kg(t).pipe(Me$1(ad))}}function ts(n){return n!=null?dd(ld(n)):null}function $c(n,i){return n===null?[i]:Array.isArray(n)?[...n,i]:[n,i]}function md(n){return n._rawValidators}function ud(n){return n._rawAsyncValidators}function Xa(n){return n?Array.isArray(n)?n:[n]:[]}function mo(n,i){return Array.isArray(n)?n.includes(i):n===i}function Gc(n,i){let e=Xa(i);return Xa(n).forEach(r=>{mo(e,r)||e.push(r)}),e}function Wc(n,i){return Xa(i).filter(e=>!mo(n,e))}var uo=class{get value(){return this.control?this.control.value:null}get valid(){return this.control?this.control.valid:null}get invalid(){return this.control?this.control.invalid:null}get pending(){return this.control?this.control.pending:null}get disabled(){return this.control?this.control.disabled:null}get enabled(){return this.control?this.control.enabled:null}get errors(){return this.control?this.control.errors:null}get pristine(){return this.control?this.control.pristine:null}get dirty(){return this.control?this.control.dirty:null}get touched(){return this.control?this.control.touched:null}get status(){return this.control?this.control.status:null}get untouched(){return this.control?this.control.untouched:null}get statusChanges(){return this.control?this.control.statusChanges:null}get valueChanges(){return this.control?this.control.valueChanges:null}get path(){return null}_composedValidatorFn;_composedAsyncValidatorFn;_rawValidators=[];_rawAsyncValidators=[];_setValidators(i){this._rawValidators=i||[],this._composedValidatorFn=es(this._rawValidators)}_setAsyncValidators(i){this._rawAsyncValidators=i||[],this._composedAsyncValidatorFn=ts(this._rawAsyncValidators)}get validator(){return this._composedValidatorFn||null}get asyncValidator(){return this._composedAsyncValidatorFn||null}_onDestroyCallbacks=[];_registerOnDestroy(i){this._onDestroyCallbacks.push(i)}_invokeOnDestroyCallbacks(){this._onDestroyCallbacks.forEach(i=>i()),this._onDestroyCallbacks=[]}reset(i=void 0){this.control?.reset(i)}hasError(i,e){return this.control?this.control.hasError(i,e):!1}getError(i,e){return this.control?this.control.getError(i,e):null}};var Vt=class extends uo{name;get formDirective(){return null}get path(){return null}};var qi=`VALID`;var lo=`INVALID`;var Qn=`PENDING`;var Zi=`DISABLED`;var Jt=class{};var ho=class extends Jt{value;source;constructor(i,e){super(),this.value=i,this.source=e}};var Ji=class extends Jt{pristine;source;constructor(i,e){super(),this.pristine=i,this.source=e}};var er=class extends Jt{touched;source;constructor(i,e){super(),this.touched=i,this.source=e}};var Jn=class extends Jt{status;source;constructor(i,e){super(),this.status=i,this.source=e}};var po=class extends Jt{source;constructor(i){super(),this.source=i}};var xn=class extends Jt{source;constructor(i){super(),this.source=i}};function ns(n){return(Co(n)?n.validators:n)||null}function Bh(n){return Array.isArray(n)?es(n):n||null}function is(n,i){return(Co(i)?i.asyncValidators:n)||null}function zh(n){return Array.isArray(n)?ts(n):n||null}function Co(n){return n!=null&&!Array.isArray(n)&&typeof n==`object`}function hd(n,i,e){let t=n.controls;if(!(i?Object.keys(t):t).length)throw new T(1e3,``);if(!fd(t,e))throw new T(1001,``)}function pd(n,i,e){n._forEachChild((t,r)=>{if(e[r]===void 0)throw new T(-1002,``)})}var ei=class{_pendingDirty=!1;_hasOwnPendingAsyncValidator=null;_pendingTouched=!1;_onCollectionChange=()=>{};_updateOn;_hasRequired=oa(!1);_parent=null;_asyncValidationSubscription;_composedValidatorFn;_composedAsyncValidatorFn;_rawValidators;_rawAsyncValidators;value;constructor(i,e){this._assignValidators(i),this._assignAsyncValidators(e)}get validator(){return this._composedValidatorFn}set validator(i){this._rawValidators=this._composedValidatorFn=i,this._updateHasRequiredValidator()}get asyncValidator(){return this._composedAsyncValidatorFn}set asyncValidator(i){this._rawAsyncValidators=this._composedAsyncValidatorFn=i}get parent(){return this._parent}get status(){return Ow(this.statusReactive)}set status(i){Ow(()=>this.statusReactive.set(i))}_status=Rw(()=>this.statusReactive());statusReactive=oa(void 0);get valid(){return this.status===qi}get invalid(){return this.status===lo}get pending(){return this.status===Qn}get disabled(){return this.status===Zi}get enabled(){return this.status!==Zi}errors;get pristine(){return Ow(this.pristineReactive)}set pristine(i){Ow(()=>this.pristineReactive.set(i))}_pristine=Rw(()=>this.pristineReactive());pristineReactive=oa(!0);get dirty(){return!this.pristine}get touched(){return Ow(this.touchedReactive)}set touched(i){Ow(()=>this.touchedReactive.set(i))}_touched=Rw(()=>this.touchedReactive());touchedReactive=oa(!1);get untouched(){return!this.touched}_events=new te$1;events=this._events.asObservable();valueChanges;statusChanges;get updateOn(){return this._updateOn?this._updateOn:this.parent?this.parent.updateOn:`change`}setValidators(i){this._assignValidators(i)}setAsyncValidators(i){this._assignAsyncValidators(i)}addValidators(i){this.setValidators(Gc(i,this._rawValidators))}addAsyncValidators(i){this.setAsyncValidators(Gc(i,this._rawAsyncValidators))}removeValidators(i){this.setValidators(Wc(i,this._rawValidators))}removeAsyncValidators(i){this.setAsyncValidators(Wc(i,this._rawAsyncValidators))}hasValidator(i){return mo(this._rawValidators,i)}hasAsyncValidator(i){return mo(this._rawAsyncValidators,i)}clearValidators(){this.validator=null}clearAsyncValidators(){this.asyncValidator=null}markAsTouched(i={}){let e=this.touched===!1;this.touched=!0;let t=i.sourceControl??this;i.onlySelf||this._parent?.markAsTouched(Y($({},i),{sourceControl:t})),e&&i.emitEvent!==!1&&this._events.next(new er(!0,t))}markAllAsDirty(i={}){this.markAsDirty({onlySelf:!0,emitEvent:i.emitEvent,sourceControl:this}),this._forEachChild(e=>e.markAllAsDirty(i))}markAllAsTouched(i={}){this.markAsTouched({onlySelf:!0,emitEvent:i.emitEvent,sourceControl:this}),this._forEachChild(e=>e.markAllAsTouched(i))}markAsUntouched(i={}){let e=this.touched===!0;this.touched=!1,this._pendingTouched=!1;let t=i.sourceControl??this;this._forEachChild(r=>{r.markAsUntouched({onlySelf:!0,emitEvent:i.emitEvent,sourceControl:t})}),i.onlySelf||this._parent?._updateTouched(i,t),e&&i.emitEvent!==!1&&this._events.next(new er(!1,t))}markAsDirty(i={}){let e=this.pristine===!0;this.pristine=!1;let t=i.sourceControl??this;i.onlySelf||this._parent?.markAsDirty(Y($({},i),{sourceControl:t})),e&&i.emitEvent!==!1&&this._events.next(new Ji(!1,t))}markAsPristine(i={}){let e=this.pristine===!1;this.pristine=!0,this._pendingDirty=!1;let t=i.sourceControl??this;this._forEachChild(r=>{r.markAsPristine({onlySelf:!0,emitEvent:i.emitEvent})}),i.onlySelf||this._parent?._updatePristine(i,t),e&&i.emitEvent!==!1&&this._events.next(new Ji(!0,t))}markAsPending(i={}){this.status=Qn;let e=i.sourceControl??this;i.emitEvent!==!1&&(this._events.next(new Jn(this.status,e)),this.statusChanges.emit(this.status)),i.onlySelf||this._parent?.markAsPending(Y($({},i),{sourceControl:e}))}disable(i={}){let e=this._parentMarkedDirty(i.onlySelf);this.status=Zi,this.errors=null,this._forEachChild(r=>{r.disable(Y($({},i),{onlySelf:!0}))}),this._updateValue();let t=i.sourceControl??this;i.emitEvent!==!1&&(this._events.next(new ho(this.value,t)),this._events.next(new Jn(this.status,t)),this.valueChanges.emit(this.value),this.statusChanges.emit(this.status)),this._updateAncestors(Y($({},i),{skipPristineCheck:e}),this),this._onDisabledChange.forEach(r=>r(!0))}enable(i={}){let e=this._parentMarkedDirty(i.onlySelf);this.status=qi,this._forEachChild(t=>{t.enable(Y($({},i),{onlySelf:!0}))}),this.updateValueAndValidity({onlySelf:!0,emitEvent:i.emitEvent}),this._updateAncestors(Y($({},i),{skipPristineCheck:e}),this),this._onDisabledChange.forEach(t=>t(!1))}_updateAncestors(i,e){i.onlySelf||(this._parent?.updateValueAndValidity(i),i.skipPristineCheck||this._parent?._updatePristine({},e),this._parent?._updateTouched({},e))}setParent(i){this._parent=i}getRawValue(){return this.value}updateValueAndValidity(i={}){if(this._setInitialStatus(),this._updateValue(),this.enabled){let t=this._cancelExistingSubscription();this.errors=this._runValidator(),this.status=this._calculateStatus(),(this.status===qi||this.status===Qn)&&this._runAsyncValidator(t,i.emitEvent)}let e=i.sourceControl??this;i.emitEvent!==!1&&(this._events.next(new ho(this.value,e)),this._events.next(new Jn(this.status,e)),this.valueChanges.emit(this.value),this.statusChanges.emit(this.status)),i.onlySelf||this._parent?.updateValueAndValidity(Y($({},i),{sourceControl:e}))}_updateTreeValidity(i={emitEvent:!0}){this._forEachChild(e=>e._updateTreeValidity(i)),this.updateValueAndValidity({onlySelf:!0,emitEvent:i.emitEvent})}_setInitialStatus(){this.status=this._allControlsDisabled()?Zi:qi}_runValidator(){return this.validator?this.validator(this):null}_runAsyncValidator(i,e){if(this.asyncValidator){this.status=Qn,this._hasOwnPendingAsyncValidator={emitEvent:e!==!1,shouldHaveEmitted:i!==!1};let t=od(this.asyncValidator(this));this._asyncValidationSubscription=t.subscribe(r=>{this._hasOwnPendingAsyncValidator=null,this.setErrors(r,{emitEvent:e,shouldHaveEmitted:i})})}}_cancelExistingSubscription(){if(this._asyncValidationSubscription){this._asyncValidationSubscription.unsubscribe();let i=(this._hasOwnPendingAsyncValidator?.emitEvent||this._hasOwnPendingAsyncValidator?.shouldHaveEmitted)??!1;return this._hasOwnPendingAsyncValidator=null,i}return!1}setErrors(i,e={}){this.errors=i,this._updateControlsErrors(e.emitEvent!==!1,this,e.shouldHaveEmitted)}get(i){let e=i;return e==null||(Array.isArray(e)||(e=e.split(`.`)),e.length===0)?null:e.reduce((t,r)=>t&&t._find(r),this)}getError(i,e){let t=e?this.get(e):this;return t?.errors?t.errors[i]:null}hasError(i,e){return!!this.getError(i,e)}get root(){let i=this;for(;i._parent;)i=i._parent;return i}_updateControlsErrors(i,e,t){this.status=this._calculateStatus(),i&&this.statusChanges.emit(this.status),(i||t)&&this._events.next(new Jn(this.status,e)),this._parent&&this._parent._updateControlsErrors(i,e,t)}_initObservables(){this.valueChanges=new Fe,this.statusChanges=new Fe}_calculateStatus(){return this._allControlsDisabled()?Zi:this.errors?lo:this._hasOwnPendingAsyncValidator||this._anyControlsHaveStatus(Qn)?Qn:this._anyControlsHaveStatus(lo)?lo:qi}_anyControlsHaveStatus(i){return this._anyControls(e=>e.status===i)}_anyControlsDirty(){return this._anyControls(i=>i.dirty)}_anyControlsTouched(){return this._anyControls(i=>i.touched)}_updatePristine(i,e){let t=!this._anyControlsDirty(),r=this.pristine!==t;this.pristine=t,i.onlySelf||this._parent?._updatePristine(i,e),r&&this._events.next(new Ji(this.pristine,e))}_updateTouched(i={},e){this.touched=this._anyControlsTouched(),this._events.next(new er(this.touched,e)),i.onlySelf||this._parent?._updateTouched(i,e)}_onDisabledChange=[];_registerOnCollectionChange(i){this._onCollectionChange=i}_setUpdateStrategy(i){Co(i)&&i.updateOn!=null&&(this._updateOn=i.updateOn)}_parentMarkedDirty(i){return!i&&!!this._parent?.dirty&&!this._parent._anyControlsDirty()}_find(i){return null}_assignValidators(i){this._rawValidators=Array.isArray(i)?i.slice():i,this._composedValidatorFn=Bh(this._rawValidators),this._updateHasRequiredValidator()}_assignAsyncValidators(i){this._rawAsyncValidators=Array.isArray(i)?i.slice():i,this._composedAsyncValidatorFn=zh(this._rawAsyncValidators)}_updateHasRequiredValidator(){Ow(()=>this._hasRequired.set(this.hasValidator(Ct.required)))}};function fd(n,i){return Object.hasOwn(n,i)}function jh(n){return n.tagName===`INPUT`||n.tagName===`SELECT`||n.tagName===`TEXTAREA`}function Uh(n,i,e,t){switch(e){case`name`:n.setAttribute(i,e,t);break;case`disabled`:case`readonly`:case`required`:t?n.setAttribute(i,e,``):n.removeAttribute(i,e);break;case`max`:case`min`:case`minLength`:case`maxLength`:t!==void 0?n.setAttribute(i,e,t.toString()):n.removeAttribute(i,e)}}var Ka=class{kind;context;control;message;constructor({kind:i,context:e,control:t}){this.kind=i,this.context=e,this.control=t}};function gd(n){return typeof n==`number`?n:parseInt(n,10)}function bd(n){return typeof n==`number`?n:parseFloat(n)}var ir=(()=>{class n{_validator=co;_onChange;_enabled;ngOnChanges(e){if(this.inputName in e){let t=this.normalizeInput(e[this.inputName].currentValue);this._enabled=this.enabled(t),this._validator=this._enabled?this.createValidator(t):co,this._onChange?.()}}validate(e){return this._validator(e)}registerOnValidatorChange(e){this._onChange=e}enabled(e){return e!=null}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,features:[iy]})}return n})();var Hh={provide:at,useExisting:Io$1(()=>$h),multi:!0};var $h=(()=>{class n extends ir{max;inputName=`max`;normalizeInput=e=>bd(e);createValidator=e=>ed(e);static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[`input`,`type`,`number`,`max`,``,`formControlName`,``],[`input`,`type`,`number`,`max`,``,`formControl`,``],[`input`,`type`,`number`,`max`,``,`ngModel`,``]],hostVars:1,hostBindings:function(t,r){t&2&&Kp(`max`,r._enabled?r.max:null)},inputs:{max:`max`},standalone:!1,features:[hw([Hh]),Vp$1]})}return n})();var Gh={provide:at,useExisting:Io$1(()=>Wh),multi:!0};var Wh=(()=>{class n extends ir{min;inputName=`min`;normalizeInput=e=>bd(e);createValidator=e=>Jc(e);static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[`input`,`type`,`number`,`min`,``,`formControlName`,``],[`input`,`type`,`number`,`min`,``,`formControl`,``],[`input`,`type`,`number`,`min`,``,`ngModel`,``]],hostVars:1,hostBindings:function(t,r){t&2&&Kp(`min`,r._enabled?r.min:null)},inputs:{min:`min`},standalone:!1,features:[hw([Gh]),Vp$1]})}return n})();var Yh={provide:at,useExisting:Io$1(()=>_d),multi:!0};var _d=(()=>{class n extends ir{required;inputName=`required`;normalizeInput=T0;createValidator=e=>td;enabled(e){return e}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[``,`required`,``,`formControlName`,``,3,`type`,`checkbox`],[``,`required`,``,`formControl`,``,3,`type`,`checkbox`],[``,`required`,``,`ngModel`,``,3,`type`,`checkbox`]],hostVars:1,hostBindings:function(t,r){t&2&&Kp(`required`,r._enabled?``:null)},inputs:{required:`required`},standalone:!1,features:[hw([Yh]),Vp$1]})}return n})();var Xh={provide:at,useExisting:Io$1(()=>Kh),multi:!0};var Kh=(()=>{class n extends ir{minlength;inputName=`minlength`;normalizeInput=e=>gd(e);createValidator=e=>nd(e);static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[``,`minlength`,``,`formControlName`,``],[``,`minlength`,``,`formControl`,``],[``,`minlength`,``,`ngModel`,``]],hostVars:1,hostBindings:function(t,r){t&2&&Kp(`minlength`,r._enabled?r.minlength:null)},inputs:{minlength:`minlength`},standalone:!1,features:[hw([Xh]),Vp$1]})}return n})();var qh={provide:at,useExisting:Io$1(()=>Zh),multi:!0};var Zh=(()=>{class n extends ir{maxlength;inputName=`maxlength`;normalizeInput=e=>gd(e);createValidator=e=>id(e);static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[``,`maxlength`,``,`formControlName`,``],[``,`maxlength`,``,`formControl`,``],[``,`maxlength`,``,`ngModel`,``]],hostVars:1,hostBindings:function(t,r){t&2&&Kp(`maxlength`,r._enabled?r.maxlength:null)},inputs:{maxlength:`maxlength`},standalone:!1,features:[hw([qh]),Vp$1]})}return n})();var Qh=new S(``);var ni=new S(``,{factory:()=>So});var So=`always`;function yd(n,i){return[...i.path,n]}function fo(n,i,e=So){rs(n,i),i.valueAccessor.writeValue(n.value),(n.disabled||e===`always`)&&i.valueAccessor.setDisabledState?.(n.disabled),ep(n,i),np(n,i),tp(n,i),Jh(n,i)}function go(n,i,e=!0){let t=()=>{};i?.valueAccessor?.registerOnChange(t),i?.valueAccessor?.registerOnTouched(t),_o(n,i),n&&(i._invokeOnDestroyCallbacks(),n._registerOnCollectionChange(()=>{}))}function bo(n,i){n.forEach(e=>{e.registerOnValidatorChange&&e.registerOnValidatorChange(i)})}function Jh(n,i){if(i.valueAccessor.setDisabledState){let e=t=>{i.valueAccessor.setDisabledState(t)};n.registerOnDisabledChange(e),i._registerOnDestroy(()=>{n._unregisterOnDisabledChange(e)})}}function rs(n,i){let e=md(n);i.validator!==null?n.setValidators($c(e,i.validator)):typeof e==`function`&&n.setValidators([e]);let t=ud(n);i.asyncValidator!==null?n.setAsyncValidators($c(t,i.asyncValidator)):typeof t==`function`&&n.setAsyncValidators([t]);let r=()=>n.updateValueAndValidity();bo(i._rawValidators,r),bo(i._rawAsyncValidators,r)}function _o(n,i){let e=!1;if(n!==null){if(i.validator!==null){let r=md(n);if(Array.isArray(r)&&r.length>0){let o=r.filter(a=>a!==i.validator);o.length!==r.length&&(e=!0,n.setValidators(o))}}if(i.asyncValidator!==null){let r=ud(n);if(Array.isArray(r)&&r.length>0){let o=r.filter(a=>a!==i.asyncValidator);o.length!==r.length&&(e=!0,n.setAsyncValidators(o))}}}let t=()=>{};return bo(i._rawValidators,t),bo(i._rawAsyncValidators,t),e}function ep(n,i){i.valueAccessor.registerOnChange(e=>{n._pendingValue=e,n._pendingChange=!0,n._pendingDirty=!0,n.updateOn===`change`&&vd(n,i)})}function tp(n,i){i.valueAccessor.registerOnTouched(()=>{n._pendingTouched=!0,n.updateOn===`blur`&&n._pendingChange&&vd(n,i),n.updateOn!==`submit`&&n.markAsTouched()})}function vd(n,i){n._pendingDirty&&n.markAsDirty(),n.setValue(n._pendingValue,{emitModelToViewChange:!1}),i.viewToModelUpdate(n._pendingValue),n._pendingChange=!1}function np(n,i){let e=(t,r)=>{i.valueAccessor.writeValue(t),r&&i.viewToModelUpdate(t)};n.registerOnChange(e),i._registerOnDestroy(()=>{n._unregisterOnChange(e)})}function xd(n,i){rs(n,i)}function ip(n,i){return _o(n,i)}function os(n,i){if(!Object.hasOwn(n,`model`))return!1;let e=n.model;return e.isFirstChange()?!0:!Object.is(i,e.currentValue)}function rp(n){return Object.getPrototypeOf(n.constructor)===vo}function Cd(n,i){n._syncPendingControls(),i.forEach(e=>{let t=e.control;t.updateOn===`submit`&&t._pendingChange&&(e.viewToModelUpdate(t._pendingValue),t._pendingChange=!1)})}function op(n,i){if(!i)return null;let e,t,r;return i.forEach(o=>{o.constructor===xo?e=o:rp(o)?t=o:r=o}),r||t||e||null}function ap(n,i){let e=n.indexOf(i);e>-1&&n.splice(e,1)}var as={provide:Qh,useFactory:()=>{let n=I(Ye,{self:!0});return{setParseErrors:i=>{n.setParseErrorSource(i)},set onReset(i){n.onReset=i}}}};var Ye=class extends uo{_parent=null;name=null;valueAccessor=null;isCustomControlBased=!1;userOnReset;resetSubscription;set onReset(i){this.userOnReset=i,this.resetSubscription?.unsubscribe(),this.resetSubscription=void 0,this.control&&(this.resetSubscription=this.control.events.subscribe(e=>{e instanceof xn&&this.control&&this.userOnReset?.(this.control.value)}),this.subscription?.add(this.resetSubscription))}isNativeFormElement=!1;rawValueAccessors;_selectedValueAccessor=null;get selectedValueAccessor(){return this._selectedValueAccessor??=op(this,this.rawValueAccessors)}parseErrorsValidator=null;renderer;injector;requiredValidatorViaDi;subscription;customControlBindings=null;constructor(i,e,t){super(),this.injector=i,this.renderer=e,this.rawValueAccessors=t,this.injector?.get(Ae)?.onDestroy(()=>{this.removeParseErrorsValidator(this.control),this.subscription?.unsubscribe()})}setupCustomControl(){this.subscription?.unsubscribe();let i=this.injector?.get(w0);if(!this.control||!i)return;let e=i.markForCheck.bind(i);this.subscription=new q,this.subscription.add(this.control.valueChanges.subscribe(e)),this.subscription.add(this.control.statusChanges.subscribe(e)),this.resetSubscription?.unsubscribe(),this.resetSubscription=void 0,this.userOnReset&&(this.resetSubscription=this.control.events.subscribe(t=>{t instanceof xn&&this.control&&this.userOnReset?.(this.control.value)}),this.subscription.add(this.resetSubscription)),this.parseErrorsValidator&&this.control.addValidators(this.parseErrorsValidator)}ngControlCreate(i){!i.nativeElement.hasAttribute?.(`ngNoCva`)&&(this.rawValueAccessors&&this.rawValueAccessors.length>0||this.valueAccessor!==null)||!i.customControl||(this.isCustomControlBased=!0,i.listenToCustomControlModel(r=>{this.control?.markAsDirty(),this.control?.setValue(r,{emitModelToViewChange:!1}),this.viewToModelUpdate(r)}),i.listenToCustomControlOutput(`touch`,()=>{this.control?.markAsTouched()}),this.customControlBindings={},this.isNativeFormElement=jh(i.nativeElement),this.requiredValidatorViaDi=this._rawValidators.find(r=>r instanceof _d))}ngControlUpdate(i,e){if(!this.isCustomControlBased)return;let t=this.control,r=this.customControlBindings;Object.is(r.value,t.value)||(r.value=t.value,i.setCustomControlModelInput(t.value)),this.bindControlProperty(i,r,`touched`,t.touched),this.bindControlProperty(i,r,`dirty`,t.dirty),this.bindControlProperty(i,r,`valid`,t.valid),this.bindControlProperty(i,r,`invalid`,t.invalid),this.bindControlProperty(i,r,`pending`,t.pending),this.bindControlProperty(i,r,`disabled`,t.disabled),this.shouldBindRequired&&this.bindControlProperty(i,r,`required`,this.isRequired);let o=t.errors;if(r.errors!==o){r.errors=o;let a=this._convertErrors(o);i.setInputOnDirectives(`errors`,a)}}get isRequired(){return(this.requiredValidatorViaDi?._enabled||this.control?._hasRequired())??!1}get shouldBindRequired(){return!0}bindControlProperty(i,e,t,r){if(e[t]===r)return;e[t]=r;let o=i.setInputOnDirectives(t,r);this.isNativeFormElement&&!o&&(t===`disabled`||t===`required`)&&this.renderer&&Uh(this.renderer,i.nativeElement,t,r)}_convertErrors(i){if(i===null)return[];let e=this.control;return Object.entries(i).map(([t,r])=>new Ka({context:r,kind:t,control:e}))}setParseErrorSource(i){if(i===void 0)return;let e=null,t=Rw(()=>{let r=i();return r.length===0?null:r.reduce((o,a)=>(o[a.kind]=a,o),{})});this.parseErrorsValidator=(()=>e).bind(this),Wm$1(()=>{e=t(),this.control?.updateValueAndValidity({emitEvent:!1})},{injector:this.injector})}removeParseErrorsValidator(i){this.parseErrorsValidator&&(i?.removeValidators(this.parseErrorsValidator),i?.updateValueAndValidity({emitEvent:!1}))}};var yo=class{_cd;constructor(i){this._cd=i}get isTouched(){return this._cd?.control?._touched?.(),!!this._cd?.control?.touched}get isUntouched(){return!!this._cd?.control?.untouched}get isPristine(){return this._cd?.control?._pristine?.(),!!this._cd?.control?.pristine}get isDirty(){return!!this._cd?.control?.dirty}get isValid(){return this._cd?.control?._status?.(),!!this._cd?.control?.valid}get isInvalid(){return!!this._cd?.control?.invalid}get isPending(){return!!this._cd?.control?.pending}get isSubmitted(){return this._cd?._submitted?.(),!!this._cd?.submitted}};var wo=(()=>{class n extends yo{constructor(e){super(e)}static ɵfac=function(t){return new(t||n)(Mr(Ye,2))};static ɵdir=VI({type:n,selectors:[[``,`formControlName`,``],[``,`ngModel`,``],[``,`formControl`,``]],hostVars:14,hostBindings:function(t,r){t&2&&yh$1(`ng-untouched`,r.isUntouched)(`ng-touched`,r.isTouched)(`ng-pristine`,r.isPristine)(`ng-dirty`,r.isDirty)(`ng-valid`,r.isValid)(`ng-invalid`,r.isInvalid)(`ng-pending`,r.isPending)},standalone:!1,features:[Vp$1]})}return n})();var Sd=(()=>{class n extends yo{constructor(e){super(e)}static ɵfac=function(t){return new(t||n)(Mr(Vt,10))};static ɵdir=VI({type:n,selectors:[[``,`formGroupName`,``],[``,`formArrayName`,``],[``,`ngModelGroup`,``],[``,`formGroup`,``],[``,`formArray`,``],[`form`,3,`ngNoForm`,``],[``,`ngForm`,``]],hostVars:16,hostBindings:function(t,r){t&2&&yh$1(`ng-untouched`,r.isUntouched)(`ng-touched`,r.isTouched)(`ng-pristine`,r.isPristine)(`ng-dirty`,r.isDirty)(`ng-valid`,r.isValid)(`ng-invalid`,r.isInvalid)(`ng-pending`,r.isPending)(`ng-submitted`,r.isSubmitted)},standalone:!1,features:[Vp$1]})}return n})();var ti=class extends ei{constructor(i,e,t){super(ns(e),is(t,e)),this.controls=i,this._initObservables(),this._setUpdateStrategy(e),this._setUpControls(),this.updateValueAndValidity({onlySelf:!0,emitEvent:!!this.asyncValidator})}controls;registerControl(i,e){return this._find(i)||(this.controls[i]=e,e.setParent(this),e._registerOnCollectionChange(this._onCollectionChange),e)}addControl(i,e,t={}){this.registerControl(i,e),this.updateValueAndValidity({emitEvent:t.emitEvent}),this._onCollectionChange()}removeControl(i,e={}){let t=this._find(i);t&&t._registerOnCollectionChange(()=>{}),delete this.controls[i],this.updateValueAndValidity({emitEvent:e.emitEvent}),this._onCollectionChange()}setControl(i,e,t={}){let r=this._find(i);r&&r._registerOnCollectionChange(()=>{}),delete this.controls[i],e&&this.registerControl(i,e),this.updateValueAndValidity({emitEvent:t.emitEvent}),this._onCollectionChange()}contains(i){return this._find(i)?.enabled===!0}setValue(i,e={}){Ow(()=>{pd(this,!0,i),Object.keys(i).forEach(t=>{hd(this,!0,t),this.controls[t].setValue(i[t],{onlySelf:!0,emitEvent:e.emitEvent})}),this.updateValueAndValidity(e)})}patchValue(i,e={}){i!=null&&(Object.keys(i).forEach(t=>{let r=this._find(t);r&&r.patchValue(i[t],{onlySelf:!0,emitEvent:e.emitEvent})}),this.updateValueAndValidity(e))}reset(i={},e={}){this._forEachChild((t,r)=>{t.reset(i?i[r]:null,Y($({},e),{onlySelf:!0}))}),this._updatePristine(e,this),this._updateTouched(e,this),this.updateValueAndValidity(e),e?.emitEvent!==!1&&this._events.next(new xn(this))}getRawValue(){return this._reduceChildren({},(i,e,t)=>(i[t]=e.getRawValue(),i))}_syncPendingControls(){let i=this._reduceChildren(!1,(e,t)=>t._syncPendingControls()?!0:e);return i&&this.updateValueAndValidity({onlySelf:!0}),i}_forEachChild(i){Object.keys(this.controls).forEach(e=>{let t=this.controls[e];t&&i(t,e)})}_setUpControls(){this._forEachChild(i=>{i.setParent(this),i._registerOnCollectionChange(this._onCollectionChange)})}_updateValue(){this.value=this._reduceValue()}_anyControls(i){for(let[e,t]of Object.entries(this.controls))if(this.contains(e)&&i(t))return!0;return!1}_reduceValue(){return this._reduceChildren({},(e,t,r)=>((t.enabled||this.disabled)&&(e[r]=t.value),e))}_reduceChildren(i,e){let t=i;return this._forEachChild((r,o)=>{t=e(t,r,o)}),t}_allControlsDisabled(){for(let i of Object.keys(this.controls))if(this.controls[i].enabled)return!1;return Object.keys(this.controls).length>0||this.disabled}_find(i){return fd(this.controls,i)?this.controls[i]:null}};var qa=class extends ti{};var sp={provide:Vt,useExisting:Io$1(()=>rr)};var Qi=Promise.resolve();var rr=(()=>{class n extends Vt{callSetDisabledState;get submitted(){return Ow(this.submittedReactive)}_submitted=Rw(()=>this.submittedReactive());submittedReactive=oa(!1);_directives=new Set;form;ngSubmit=new Fe;options;constructor(e,t,r){super(),this.callSetDisabledState=r,this.form=new ti({},es(e),ts(t))}ngAfterViewInit(){this._setUpdateStrategy()}get formDirective(){return this}get control(){return this.form}get path(){return[]}get controls(){return this.form.controls}addControl(e){Qi.then(()=>{e.control=this._findContainer(e.path).registerControl(e.name,e.control),e._setupWithForm(this.callSetDisabledState),e.control.updateValueAndValidity({emitEvent:!1}),this._directives.add(e)})}getControl(e){return this.form.get(e.path)}removeControl(e){Qi.then(()=>{this._findContainer(e.path)?.removeControl(e.name),this._directives.delete(e)})}addFormGroup(e){Qi.then(()=>{let t=this._findContainer(e.path),r=new ti({});xd(r,e),t.registerControl(e.name,r),r.updateValueAndValidity({emitEvent:!1})})}removeFormGroup(e){Qi.then(()=>{this._findContainer(e.path)?.removeControl?.(e.name)})}getFormGroup(e){return this.form.get(e.path)}updateModel(e,t){Qi.then(()=>{this.form.get(e.path).setValue(t)})}setValue(e){this.control.setValue(e)}onSubmit(e){return this.submittedReactive.set(!0),Cd(this.form,this._directives),this.ngSubmit.emit(e),this.form._events.next(new po(this.control)),e?.target?.method===`dialog`}onReset(){this.resetForm()}resetForm(e=void 0){this.form.reset(e),this.submittedReactive.set(!1)}_setUpdateStrategy(){this.options&&this.options.updateOn!=null&&(this.form._updateOn=this.options.updateOn)}_findContainer(e){return e.pop(),e.length?this.form.get(e):this.form}static ɵfac=function(t){return new(t||n)(Mr(at,10),Mr(nr,10),Mr(ni,8))};static ɵdir=VI({type:n,selectors:[[`form`,3,`ngNoForm`,``,3,`formGroup`,``,3,`formArray`,``],[`ng-form`],[``,`ngForm`,``]],hostBindings:function(t,r){t&1&&ih$1(`submit`,function(a){return r.onSubmit(a)})(`reset`,function(){return r.onReset()})},inputs:{options:[0,`ngFormOptions`,`options`]},outputs:{ngSubmit:`ngSubmit`},exportAs:[`ngForm`],standalone:!1,features:[hw([sp]),Vp$1]})}return n})();function Yc(n,i){let e=n.indexOf(i);e>-1&&n.splice(e,1)}function Xc(n){return typeof n==`object`&&n!==null&&Object.keys(n).length===2&&`value`in n&&`disabled`in n}var tr=class extends ei{defaultValue=null;_onChange=[];_pendingValue;_pendingChange=!1;constructor(i=null,e,t){super(ns(e),is(t,e)),this._applyFormState(i),this._setUpdateStrategy(e),this._initObservables(),this.updateValueAndValidity({onlySelf:!0,emitEvent:!!this.asyncValidator}),Co(e)&&(e.nonNullable||e.initialValueIsDefault)&&(Xc(i)?this.defaultValue=i.value:this.defaultValue=i)}setValue(i,e={}){Ow(()=>{this.value=this._pendingValue=i,this._onChange.length&&e.emitModelToViewChange!==!1&&this._onChange.forEach(t=>t(this.value,e.emitViewToModelChange!==!1)),this.updateValueAndValidity(e)})}patchValue(i,e={}){this.setValue(i,e)}reset(i=this.defaultValue,e={}){this._applyFormState(i),this.markAsPristine(e),this.markAsUntouched(e),this.setValue(this.value,e),e.overwriteDefaultValue&&(this.defaultValue=this.value),this._pendingChange=!1,e?.emitEvent!==!1&&this._events.next(new xn(this))}_updateValue(){}_anyControls(i){return!1}_allControlsDisabled(){return this.disabled}registerOnChange(i){this._onChange.push(i)}_unregisterOnChange(i){Yc(this._onChange,i)}registerOnDisabledChange(i){this._onDisabledChange.push(i)}_unregisterOnDisabledChange(i){Yc(this._onDisabledChange,i)}_forEachChild(i){}_syncPendingControls(){return this.updateOn===`submit`&&(this._pendingDirty&&this.markAsDirty(),this._pendingTouched&&this.markAsTouched(),this._pendingChange)?(this.setValue(this._pendingValue,{onlySelf:!0,emitModelToViewChange:!1}),!0):!1}_applyFormState(i){Xc(i)?(this.value=this._pendingValue=i.value,i.disabled?this.disable({onlySelf:!0,emitEvent:!1}):this.enable({onlySelf:!0,emitEvent:!1})):this.value=this._pendingValue=i}};var lp=n=>n instanceof tr;var cp=(()=>{class n extends Vt{callSetDisabledState;get submitted(){return Ow(this._submittedReactive)}set submitted(e){this._submittedReactive.set(e)}_submitted=Rw(()=>this._submittedReactive());_submittedReactive=oa(!1);_oldForm;_onCollectionChange=()=>this._updateDomValue();directives=[];constructor(e,t,r){super(),this.callSetDisabledState=r,this._setValidators(e),this._setAsyncValidators(t)}ngOnChanges(e){this.onChanges(e)}ngOnDestroy(){this.onDestroy()}onChanges(e){this._checkFormPresent(),Object.hasOwn(e,`form`)&&(this._updateValidators(),this._updateDomValue(),this._updateRegistrations(),this._oldForm=this.form)}onDestroy(){this.form&&(_o(this.form,this),this.form._onCollectionChange===this._onCollectionChange&&this.form._registerOnCollectionChange(()=>{}))}get formDirective(){return this}get path(){return[]}addControl(e){let t=this.form.get(e.path);return e._setupWithForm(t,this.callSetDisabledState),t.updateValueAndValidity({emitEvent:!1}),this.directives.push(e),t}getControl(e){return this.form.get(e.path)}removeControl(e){go(e.control||null,e,!1),ap(this.directives,e)}addFormGroup(e){this._setUpFormContainer(e)}removeFormGroup(e){this._cleanUpFormContainer(e)}getFormGroup(e){return this.form.get(e.path)}getFormArray(e){return this.form.get(e.path)}addFormArray(e){this._setUpFormContainer(e)}removeFormArray(e){this._cleanUpFormContainer(e)}updateModel(e,t){this.form.get(e.path).setValue(t)}onReset(){this.resetForm()}resetForm(e=void 0,t={}){this.form.reset(e,t),this._submittedReactive.set(!1)}onSubmit(e){return this.submitted=!0,Cd(this.form,this.directives),this.ngSubmit.emit(e),this.form._events.next(new po(this.control)),e?.target?.method===`dialog`}_updateDomValue(){this.directives.forEach(e=>{let t=e.control,r=this.form.get(e.path);t!==r&&(go(t||null,e),lp(r)&&e._setupWithForm(r,this.callSetDisabledState))}),this.form._updateTreeValidity({emitEvent:!1})}_setUpFormContainer(e){let t=this.form.get(e.path);xd(t,e),t.updateValueAndValidity({emitEvent:!1})}_cleanUpFormContainer(e){let t=this.form?.get(e.path);t&&ip(t,e)&&t.updateValueAndValidity({emitEvent:!1})}_updateRegistrations(){this.form._registerOnCollectionChange(this._onCollectionChange),this._oldForm?._registerOnCollectionChange(()=>{})}_updateValidators(){rs(this.form,this),this._oldForm&&_o(this._oldForm,this)}_checkFormPresent(){this.form}static ɵfac=function(t){return new(t||n)(Mr(at,10),Mr(nr,10),Mr(ni,8))};static ɵdir=VI({type:n,features:[Vp$1,iy]})}return n})();var dp={provide:Vt,useExisting:Io$1(()=>Cn)};var Cn=(()=>{class n extends cp{form=null;ngSubmit=new Fe;get control(){return this.form}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[``,`formGroup`,``]],hostBindings:function(t,r){t&1&&ih$1(`submit`,function(a){return r.onSubmit(a)})(`reset`,function(){return r.onReset()})},inputs:{form:[0,`formGroup`,`form`]},outputs:{ngSubmit:`ngSubmit`},exportAs:[`ngForm`],standalone:!1,features:[hw([dp]),Vp$1]})}return n})();var mp={provide:Ye,useExisting:Io$1(()=>ss)};var Kc=Promise.resolve();var ss=(()=>{class n extends Ye{_changeDetectorRef;callSetDisabledState;control=new tr;static ngAcceptInputType_isDisabled;_registered=!1;_ngModelInjector;viewModel;name=``;isDisabled;model;options;update=new Fe;constructor(e,t,r,o,a,s,c,d){super(c,d,o),this._changeDetectorRef=a,this.callSetDisabledState=s,this._parent=e,this._setValidators(t),this._setAsyncValidators(r)}ngOnChanges(e){if(this._registered,this._checkForErrors(),!this._registered||`name`in e){if(this._registered&&(this._checkName(),this.formDirective)){let t=e.name.previousValue;this.formDirective.removeControl({name:t,path:this._getPath(t)})}this._setUpControl()}`isDisabled`in e&&this._updateDisabled(e),os(e,this.viewModel)&&(this._updateValue(this.model),this.viewModel=this.model)}ngOnDestroy(){this.formDirective?.removeControl(this)}ɵngControlCreate(e){super.ngControlCreate(e)}ɵngControlUpdate(e){super.ngControlUpdate(e,!1)}get shouldBindRequired(){return!1}get path(){return this._getPath(this.name)}get formDirective(){return this._parent?this._parent.formDirective:null}viewToModelUpdate(e){this.viewModel=e,this.update.emit(e)}_setUpControl(){this._setUpdateStrategy(),this._isStandalone()?this._setUpStandalone():this.formDirective.addControl(this),this._registered=!0}_setUpdateStrategy(){this.options&&this.options.updateOn!=null&&(this.control._updateOn=this.options.updateOn)}_isStandalone(){return!this._parent||!!(this.options&&this.options.standalone)}_setUpStandalone(){this.isCustomControlBased?this.setupCustomControl():(this.valueAccessor??=this.selectedValueAccessor,fo(this.control,this,this.callSetDisabledState)),this.control.updateValueAndValidity({emitEvent:!1})}_setupWithForm(e){this.isCustomControlBased?this.setupCustomControl():(this.valueAccessor??=this.selectedValueAccessor,fo(this.control,this,e))}_checkForErrors(){this._checkName()}_checkName(){this.options&&this.options.name&&(this.name=this.options.name),!this._isStandalone()&&this.name}_updateValue(e){Kc.then(()=>{this.control.setValue(e,{emitViewToModelChange:!1}),this._changeDetectorRef?.markForCheck()})}_updateDisabled(e){let t=e.isDisabled.currentValue,r=t!==0&&T0(t);Kc.then(()=>{r&&!this.control.disabled?this.control.disable():!r&&this.control.disabled&&this.control.enable(),this._changeDetectorRef?.markForCheck()})}_getPath(e){return this._parent?yd(e,this._parent):[e]}static ɵfac=function(t){return new(t||n)(Mr(Vt,9),Mr(at,10),Mr(nr,10),Mr(Bt,10),Mr(w0,8),Mr(ni,8),Mr(le,8),Mr(La$1,8))};static ɵdir=VI({type:n,selectors:[[``,`ngModel`,``,3,`formControlName`,``,3,`formControl`,``]],inputs:{name:`name`,isDisabled:[0,`disabled`,`isDisabled`],model:[0,`ngModel`,`model`],options:[0,`ngModelOptions`,`options`]},outputs:{update:`ngModelChange`},exportAs:[`ngModel`],standalone:!1,features:[hw([mp,as]),Vp$1,iy,qI(null)]})}return n})();var wd=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[`form`,3,`ngNoForm`,``,3,`ngNativeValidate`,``]],hostAttrs:[`novalidate`,``],standalone:!1})}return n})();var up={provide:Bt,useExisting:Io$1(()=>hp),multi:!0};var hp=(()=>{class n extends vo{writeValue(e){let t=e??``;this.setProperty(`value`,t)}registerOnChange(e){this.onChange=t=>{e(t==``?null:parseFloat(t))}}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[`input`,`type`,`number`,`formControlName`,``,3,`ngNoCva`,``],[`input`,`type`,`number`,`formControl`,``,3,`ngNoCva`,``],[`input`,`type`,`number`,`ngModel`,``,3,`ngNoCva`,``]],hostBindings:function(t,r){t&1&&ih$1(`input`,function(a){return r.onChange(a.target.value)})(`blur`,function(){return r.onTouched()})},standalone:!1,features:[hw([up]),Vp$1]})}return n})();var Za=class extends ei{constructor(i,e,t){super(ns(e),is(t,e)),this.controls=i,this._initObservables(),this._setUpdateStrategy(e),this._setUpControls(),this.updateValueAndValidity({onlySelf:!0,emitEvent:!!this.asyncValidator})}controls;at(i){return this.controls[this._adjustIndex(i)]}push(i,e={}){Array.isArray(i)?i.forEach(t=>{this.controls.push(t),this._registerControl(t)}):(this.controls.push(i),this._registerControl(i)),this.updateValueAndValidity({emitEvent:e.emitEvent}),this._onCollectionChange()}insert(i,e,t={}){this.controls.splice(i,0,e),this._registerControl(e),this.updateValueAndValidity({emitEvent:t.emitEvent})}removeAt(i,e={}){let t=this._adjustIndex(i);t<0&&(t=0),this.controls[t]&&this.controls[t]._registerOnCollectionChange(()=>{}),this.controls.splice(t,1),this.updateValueAndValidity({emitEvent:e.emitEvent})}setControl(i,e,t={}){let r=this._adjustIndex(i);r<0&&(r=0),this.controls[r]&&this.controls[r]._registerOnCollectionChange(()=>{}),this.controls.splice(r,1),e&&(this.controls.splice(r,0,e),this._registerControl(e)),this.updateValueAndValidity({emitEvent:t.emitEvent}),this._onCollectionChange()}get length(){return this.controls.length}setValue(i,e={}){Ow(()=>{pd(this,!1,i),i.forEach((t,r)=>{hd(this,!1,r),this.at(r).setValue(t,{onlySelf:!0,emitEvent:e.emitEvent})}),this.updateValueAndValidity(e)})}patchValue(i,e={}){i!=null&&(i.forEach((t,r)=>{this.at(r)&&this.at(r).patchValue(t,{onlySelf:!0,emitEvent:e.emitEvent})}),this.updateValueAndValidity(e))}reset(i=[],e={}){this._forEachChild((t,r)=>{t.reset(i[r],Y($({},e),{onlySelf:!0}))}),this._updatePristine(e,this),this._updateTouched(e,this),this.updateValueAndValidity(e),e?.emitEvent!==!1&&this._events.next(new xn(this))}getRawValue(){return this.controls.map(i=>i.getRawValue())}clear(i={}){this.controls.length<1||(this._forEachChild(e=>e._registerOnCollectionChange(()=>{})),this.controls.splice(0),this.updateValueAndValidity({emitEvent:i.emitEvent}))}_adjustIndex(i){return i<0?i+this.length:i}_syncPendingControls(){let i=this.controls.reduce((e,t)=>t._syncPendingControls()?!0:e,!1);return i&&this.updateValueAndValidity({onlySelf:!0}),i}_forEachChild(i){this.controls.forEach((e,t)=>{i(e,t)})}_updateValue(){this.value=this.controls.filter(i=>i.enabled||this.disabled).map(i=>i.value)}_anyControls(i){return this.controls.some(e=>e.enabled&&i(e))}_setUpControls(){this._forEachChild(i=>this._registerControl(i))}_allControlsDisabled(){for(let i of this.controls)if(i.enabled)return!1;return this.controls.length>0||this.disabled}_registerControl(i){i.setParent(this),i._registerOnCollectionChange(this._onCollectionChange)}_find(i){return this.at(i)??null}};var ls=new S(``);var pp={provide:Ye,useExisting:Io$1(()=>fp)};var fp=(()=>{class n extends Ye{_ngModelWarningConfig;callSetDisabledState;viewModel;form;set isDisabled(e){}model;update=new Fe;static _ngModelWarningSentOnce=!1;_ngModelWarningSent=!1;constructor(e,t,r,o,a,s,c){super(c,s,r),this._ngModelWarningConfig=o,this.callSetDisabledState=a,this._setValidators(e),this._setAsyncValidators(t)}ngOnChanges(e){if(this._isControlChanged(e)){let t=e.form.previousValue;t&&(go(t,this,!1),this.removeParseErrorsValidator(t)),this.isCustomControlBased?this.setupCustomControl():(this.valueAccessor??=this.selectedValueAccessor,fo(this.form,this,this.callSetDisabledState)),this.form.updateValueAndValidity({emitEvent:!1})}os(e,this.viewModel)&&(this.form.setValue(this.model),this.viewModel=this.model)}ngOnDestroy(){this.form&&go(this.form,this,!1)}get path(){return[]}get control(){return this.form}viewToModelUpdate(e){this.viewModel=e,this.update.emit(e)}_isControlChanged(e){return Object.hasOwn(e,`form`)}ɵngControlCreate(e){super.ngControlCreate(e)}ɵngControlUpdate(e){super.ngControlUpdate(e,!0)}static ɵfac=function(t){return new(t||n)(Mr(at,10),Mr(nr,10),Mr(Bt,10),Mr(ls,8),Mr(ni,8),Mr(La$1,8),Mr(le,8))};static ɵdir=VI({type:n,selectors:[[``,`formControl`,``]],inputs:{form:[0,`formControl`,`form`],isDisabled:[0,`disabled`,`isDisabled`],model:[0,`ngModel`,`model`]},outputs:{update:`ngModelChange`},exportAs:[`ngForm`],standalone:!1,features:[hw([pp,as]),Vp$1,iy,qI(null)]})}return n})();var gp={provide:Ye,useExisting:Io$1(()=>cs)};var cs=(()=>{class n extends Ye{_ngModelWarningConfig;_added=!1;viewModel;control;name=null;set isDisabled(e){}model;update=new Fe;static _ngModelWarningSentOnce=!1;_ngModelWarningSent=!1;constructor(e,t,r,o,a,s,c){super(c,s,o),this._ngModelWarningConfig=a,this._parent=e,this._setValidators(t),this._setAsyncValidators(r)}_setupWithForm(e,t){this.control=e,this.isCustomControlBased?this.setupCustomControl():(this.valueAccessor??=this.selectedValueAccessor,fo(e,this,t))}ngOnChanges(e){this._added||this._setUpControl(),os(e,this.viewModel)&&(this.viewModel=this.model,this.formDirective.updateModel(this,this.model))}ngOnDestroy(){this.formDirective?.removeControl(this)}viewToModelUpdate(e){this.viewModel=e,this.update.emit(e)}get path(){return yd(this.name==null?this.name:this.name.toString(),this._parent)}get formDirective(){return this._parent?this._parent.formDirective:null}_setUpControl(){this.control=this.formDirective.addControl(this),this._added=!0}ɵngControlCreate(e){super.ngControlCreate(e)}ɵngControlUpdate(e){this.isCustomControlBased&&(this._added||this._setUpControl(),super.ngControlUpdate(e,!0))}static ɵfac=function(t){return new(t||n)(Mr(Vt,13),Mr(at,10),Mr(nr,10),Mr(Bt,10),Mr(ls,8),Mr(La$1,8),Mr(le,8))};static ɵdir=VI({type:n,selectors:[[``,`formControlName`,``]],inputs:{name:[0,`formControlName`,`name`],isDisabled:[0,`disabled`,`isDisabled`],model:[0,`ngModel`,`model`]},outputs:{update:`ngModelChange`},standalone:!1,features:[hw([gp,as]),Vp$1,iy,qI(null)]})}return n})();var bp={provide:Bt,useExisting:Io$1(()=>Dd),multi:!0};function kd(n,i){return n==null?`${i}`:(i&&typeof i==`object`&&(i=`Object`),`${n}: ${i}`.slice(0,50))}function _p(n){return n.split(`:`)[0]}var Dd=(()=>{class n extends vo{value;_optionMap=new Map;_idCounter=0;set compareWith(e){this._compareWith=e}_compareWith=Object.is;appRefInjector=I(Zt$1).injector;destroyRef=I(Ae);cdr=I(w0);_queuedWrite=!1;_writeValueAfterRender(){this._queuedWrite||this.appRefInjector.destroyed||(this._queuedWrite=!0,Hv({write:()=>{this.destroyRef.destroyed||(this._queuedWrite=!1,this.writeValue(this.value))}},{injector:this.appRefInjector}))}writeValue(e){this.cdr.markForCheck(),this.value=e;let r=kd(this._getOptionId(e),e);this.setProperty(`value`,r)}registerOnChange(e){this.onChange=t=>{this.value=this._getOptionValue(t),e(this.value)}}_registerOption(){return(this._idCounter++).toString()}_getOptionId(e){for(let t of this._optionMap.keys())if(this._compareWith(this._optionMap.get(t),e))return t;return null}_getOptionValue(e){let t=_p(e);return this._optionMap.has(t)?this._optionMap.get(t):e}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[`select`,`formControlName`,``,3,`multiple`,``,3,`ngNoCva`,``],[`select`,`formControl`,``,3,`multiple`,``,3,`ngNoCva`,``],[`select`,`ngModel`,``,3,`multiple`,``,3,`ngNoCva`,``]],hostBindings:function(t,r){t&1&&ih$1(`change`,function(a){return r.onChange(a.target.value)})(`blur`,function(){return r.onTouched()})},inputs:{compareWith:`compareWith`},standalone:!1,features:[hw([bp]),Vp$1]})}return n})();var iS=(()=>{class n{_element;_renderer;_select;id;constructor(e,t,r){this._element=e,this._renderer=t,this._select=r,this._select&&(this.id=this._select._registerOption())}set ngValue(e){this._select!=null&&(this._select._optionMap.set(this.id,e),this._setElementValue(kd(this.id,e)),this._select._writeValueAfterRender())}set value(e){this._setElementValue(e),this._select?._writeValueAfterRender()}_setElementValue(e){this._renderer.setProperty(this._element.nativeElement,`value`,e)}ngOnDestroy(){this._select?._optionMap.delete(this.id),this._select?._writeValueAfterRender()}static ɵfac=function(t){return new(t||n)(Mr(Dr),Mr(La$1),Mr(Dd,9))};static ɵdir=VI({type:n,selectors:[[`option`]],inputs:{ngValue:`ngValue`,value:`value`},standalone:!1})}return n})();var yp={provide:Bt,useExisting:Io$1(()=>Ed),multi:!0};function qc(n,i){return n==null?`${i}`:(typeof i==`string`&&(i=`'${i}'`),i&&typeof i==`object`&&(i=`Object`),`${n}: ${i}`.slice(0,50))}function vp(n){return n.split(`:`)[0]}var Ed=(()=>{class n extends vo{value;_optionMap=new Map;_idCounter=0;set compareWith(e){this._compareWith=e}_compareWith=Object.is;writeValue(e){this.value=e;let t;if(Array.isArray(e)){let r=e.map(o=>this._getOptionId(o));t=(o,a)=>{o._setSelected(r.indexOf(a)>-1)}}else t=r=>{r._setSelected(!1)};this._optionMap.forEach(t)}registerOnChange(e){this.onChange=t=>{let r=[],o=t.selectedOptions;if(o!==void 0){let a=o;for(let s=0;s<a.length;s++){let c=a[s],d=this._getOptionValue(c.value);r.push(d)}}else{let a=t.options;for(let s=0;s<a.length;s++){let c=a[s];if(c.selected){let d=this._getOptionValue(c.value);r.push(d)}}}this.value=r,e(r)}}_registerOption(e){let t=(this._idCounter++).toString();return this._optionMap.set(t,e),t}_getOptionId(e){for(let t of this._optionMap.keys())if(this._compareWith(this._optionMap.get(t)._value,e))return t;return null}_getOptionValue(e){let t=vp(e);return this._optionMap.has(t)?this._optionMap.get(t)._value:e}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,selectors:[[`select`,`multiple`,``,`formControlName`,``,3,`ngNoCva`,``],[`select`,`multiple`,``,`formControl`,``,3,`ngNoCva`,``],[`select`,`multiple`,``,`ngModel`,``,3,`ngNoCva`,``]],hostBindings:function(t,r){t&1&&ih$1(`change`,function(a){return r.onChange(a.target)})(`blur`,function(){return r.onTouched()})},inputs:{compareWith:`compareWith`},standalone:!1,features:[hw([yp]),Vp$1]})}return n})();var rS=(()=>{class n{_element;_renderer;_select;id;_value;constructor(e,t,r){this._element=e,this._renderer=t,this._select=r,this._select&&(this.id=this._select._registerOption(this))}set ngValue(e){this._select!=null&&(this._value=e,this._setElementValue(qc(this.id,e)),this._select.writeValue(this._select.value))}set value(e){this._select?(this._value=e,this._setElementValue(qc(this.id,e)),this._select.writeValue(this._select.value)):this._setElementValue(e)}_setElementValue(e){this._renderer.setProperty(this._element.nativeElement,`value`,e)}_setSelected(e){this._renderer.setProperty(this._element.nativeElement,`selected`,e)}ngOnDestroy(){this._select&&(this._select._optionMap.delete(this.id),this._select.writeValue(this._select.value))}static ɵfac=function(t){return new(t||n)(Mr(Dr),Mr(La$1),Mr(Ed,9))};static ɵdir=VI({type:n,selectors:[[`option`]],inputs:{ngValue:`ngValue`,value:`value`},standalone:!1})}return n})();var Md=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({})}return n})();function Zc(n){return!!n&&(n.asyncValidators!==void 0||n.validators!==void 0||n.updateOn!==void 0)}var Ad=(()=>{class n{useNonNullable=!1;get nonNullable(){let e=new n;return e.useNonNullable=!0,e}group(e,t=null){let r=this._reduceControls(e),o={};return Zc(t)?o=t:t!==null&&(o.validators=t.validator,o.asyncValidators=t.asyncValidator),new ti(r,o)}record(e,t=null){return new qa(this._reduceControls(e),t)}control(e,t,r){let o={};return this.useNonNullable?(Zc(t)?o=t:(o.validators=t,o.asyncValidators=r),new tr(e,Y($({},o),{nonNullable:!0}))):new tr(e,t,r)}array(e,t,r){return new Za(e.map(a=>this._createControl(a)),t,r)}_reduceControls(e){let t={};return Object.keys(e).forEach(r=>{t[r]=this._createControl(e[r])}),t}_createControl(e){if(e instanceof tr)return e;if(e instanceof ei)return e;if(Array.isArray(e)){let t=e[0],r=e.length>1?e[1]:null,o=e.length>2?e[2]:null;return this.control(t,r,o)}else return this.control(e)}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Id=(()=>{class n{static withConfig(e){return{ngModule:n,providers:[{provide:ni,useValue:e.callSetDisabledState??So}]}}static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[Md]})}return n})();var oS=(()=>{class n{static withConfig(e){return{ngModule:n,providers:[{provide:ls,useValue:e.warnOnNgModelWithFormControl??`always`},{provide:ni,useValue:e.callSetDisabledState??So}]}}static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[Md]})}return n})();var Rd=Symbol(`FIELD_TREE`);function or(n){return typeof n==`function`&&n[Rd]===!0}var ko=new S(``);var ds=class{_box;_destroyed=new te$1;_resizeSubject=new te$1;_resizeObserver;_elementObservables=new Map;constructor(i){this._box=i,typeof ResizeObserver<`u`&&(this._resizeObserver=new ResizeObserver(e=>this._resizeSubject.next(e)))}observe(i){return this._elementObservables.has(i)||this._elementObservables.set(i,new N(e=>{let t=this._resizeSubject.subscribe(e);return this._resizeObserver?.observe(i,{box:this._box}),()=>{this._resizeObserver?.unobserve(i),t.unsubscribe(),this._elementObservables.delete(i)}}).pipe(rn(e=>e.some(t=>t.target===i)),Yg({bufferSize:1,refCount:!0}),Rl$1(this._destroyed))),this._elementObservables.get(i)}destroy(){this._destroyed.next(),this._destroyed.complete(),this._resizeSubject.complete(),this._elementObservables.clear()}};var Fd=(()=>{class n{_cleanupErrorListener;_observers=new Map;_ngZone=I(z);constructor(){}ngOnDestroy(){for(let[,e]of this._observers)e.destroy();this._observers.clear(),this._cleanupErrorListener?.()}observe(e,t){let r=t?.box||`content-box`;return this._observers.has(r)||this._observers.set(r,new ds(r)),this._observers.get(r).observe(e)}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var ii=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[`mat-label`]]})}return n})();var Ud=new S(`MatError`);var Mo=(()=>{class n{id=I(me).getId(`mat-mdc-error-`);static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[`mat-error`],[``,`matError`,``]],hostAttrs:[1,`mat-mdc-form-field-error`,`mat-mdc-form-field-bottom-align`],hostVars:1,hostBindings:function(t,r){t&2&&rh$1(`id`,r.id)},inputs:{id:`id`},features:[hw([{provide:Ud,useExisting:n}])]})}return n})();var Eo=(()=>{class n{align=`start`;id=I(me).getId(`mat-mdc-hint-`);static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[`mat-hint`]],hostAttrs:[1,`mat-mdc-form-field-hint`,`mat-mdc-form-field-bottom-align`],hostVars:4,hostBindings:function(t,r){t&2&&(rh$1(`id`,r.id),Kp(`align`,null),yh$1(`mat-mdc-form-field-hint-end`,r.align===`end`))},inputs:{align:`align`,id:`id`}})}return n})();var xp=new S(`MatPrefix`);var Hd=new S(`MatSuffix`);var $d=(()=>{class n{set _isTextSelector(e){this._isText=!0}_isText=!1;static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`matSuffix`,``],[``,`matIconSuffix`,``],[``,`matTextSuffix`,``]],inputs:{_isTextSelector:[0,`matTextSuffix`,`_isTextSelector`]},features:[hw([{provide:Hd,useExisting:n}])]})}return n})();var Gd=new S(`FloatingLabelParent`);var Pd=(()=>{class n{_elementRef=I(Dr);get floating(){return this._floating}set floating(e){this._floating=e,this.monitorResize&&this._handleResize()}_floating=!1;get monitorResize(){return this._monitorResize}set monitorResize(e){this._monitorResize=e,this._monitorResize?this._subscribeToResize():this._resizeSubscription.unsubscribe()}_monitorResize=!1;_resizeObserver=I(Fd);_ngZone=I(z);_parent=I(Gd);_resizeSubscription=new q;ngOnDestroy(){this._resizeSubscription.unsubscribe()}getWidth(){return Cp(this._elementRef.nativeElement)}get element(){return this._elementRef.nativeElement}_handleResize(){setTimeout(()=>this._parent._handleLabelResized())}_subscribeToResize(){this._resizeSubscription.unsubscribe(),this._ngZone.runOutsideAngular(()=>{this._resizeSubscription=this._resizeObserver.observe(this._elementRef.nativeElement,{box:`border-box`}).subscribe(()=>this._handleResize())})}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[`label`,`matFormFieldFloatingLabel`,``]],hostAttrs:[1,`mdc-floating-label`,`mat-mdc-floating-label`],hostVars:2,hostBindings:function(t,r){t&2&&yh$1(`mdc-floating-label--float-above`,r.floating)},inputs:{floating:`floating`,monitorResize:`monitorResize`}})}return n})();function Cp(n){let i=n;if(i.offsetParent!==null)return i.scrollWidth;let e=i.cloneNode(!0);e.style.setProperty(`position`,`absolute`),e.style.setProperty(`transform`,`translate(-9999px, -9999px)`),document.documentElement.appendChild(e);let t=e.scrollWidth;return e.remove(),t}var Ld=`mdc-line-ripple--active`;var Do=`mdc-line-ripple--deactivating`;var Vd=(()=>{class n{_elementRef=I(Dr);_cleanupTransitionEnd;constructor(){let e=I(z),t=I(La$1);e.runOutsideAngular(()=>{this._cleanupTransitionEnd=t.listen(this._elementRef.nativeElement,`transitionend`,this._handleTransitionEnd)})}activate(){let e=this._elementRef.nativeElement.classList;e.remove(Do),e.add(Ld)}deactivate(){this._elementRef.nativeElement.classList.add(Do)}_handleTransitionEnd=e=>{let t=this._elementRef.nativeElement.classList,r=t.contains(Do);e.propertyName===`opacity`&&r&&t.remove(Ld,Do)};ngOnDestroy(){this._cleanupTransitionEnd()}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[`div`,`matFormFieldLineRipple`,``]],hostAttrs:[1,`mdc-line-ripple`]})}return n})();var Bd=(()=>{class n{_elementRef=I(Dr);_ngZone=I(z);open=!1;_notch;ngAfterViewInit(){let e=this._elementRef.nativeElement,t=e.querySelector(`.mdc-floating-label`);t?(e.classList.add(`mdc-notched-outline--upgraded`),typeof requestAnimationFrame==`function`&&(t.style.transitionDuration=`0s`,this._ngZone.runOutsideAngular(()=>{requestAnimationFrame(()=>t.style.transitionDuration=``)}))):e.classList.add(`mdc-notched-outline--no-label`)}_setNotchWidth(e){let t=this._notch.nativeElement;!this.open||!e?t.style.width=``:t.style.width=`calc(${e}px * var(--mat-mdc-form-field-floating-label-scale, 0.75) + 9px)`}_setMaxWidth(e){this._notch.nativeElement.style.setProperty(`--mat-form-field-notch-max-width`,`calc(100% - ${e}px)`)}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`notch`];return LI({type:n,selectors:[[`div`,`matFormFieldNotchedOutline`,``]],viewQuery:function(o,a){if(o&1&&lh$1(e,5),o&2){let s;SD(s=xD())&&(a._notch=s.first)}},hostAttrs:[1,`mdc-notched-outline`],hostVars:2,hostBindings:function(o,a){o&2&&yh$1(`mdc-notched-outline--notched`,a.open)},inputs:{open:[0,`matFormFieldNotchedOutlineOpen`,`open`]},ngContentSelectors:[`*`],decls:5,vars:0,consts:[[`notch`,``],[1,`mat-mdc-notch-piece`,`mdc-notched-outline__leading`],[1,`mat-mdc-notch-piece`,`mdc-notched-outline__notch`],[1,`mat-mdc-notch-piece`,`mdc-notched-outline__trailing`]],template:function(o,a){o&1&&(_D(),eh$1(0,`div`,1),jc$1(1,`div`,2,0),ND(3),Vc$1(),eh$1(4,`div`,3))},encapsulation:2})})()}return n})();var ar=(()=>{class n{id;ngField=null;ngControl=null;focused=!1;empty=!1;shouldLabelFloat=!1;required=!1;disabled=!1;errorState=!1;controlType;autofilled;userAriaDescribedBy;disableAutomaticLabeling;describedByIds;stateChanges=null;value;static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n})}return n})();var sr=new S(`MatFormField`);var Sp=new S(`MAT_FORM_FIELD_DEFAULT_OPTIONS`);var zd=`fill`;var wp=`auto`;var jd=`fixed`;var kp=`translateY(-50%)`;var lr=(()=>{class n{_elementRef=I(Dr);_changeDetectorRef=I(w0);_platform=I(J);_idGenerator=I(me);_ngZone=I(z);_defaults=I(Sp,{optional:!0});_currentDirection;_unwrapMaybeSignal(e){return ia$1(e)?e():e}_textField;_iconPrefixContainer;_textPrefixContainer;_iconSuffixContainer;_textSuffixContainer;_floatingLabel;_notchedOutline;_lineRipple;_iconPrefixContainerSignal=v0(`iconPrefixContainer`);_textPrefixContainerSignal=v0(`textPrefixContainer`);_iconSuffixContainerSignal=v0(`iconSuffixContainer`);_textSuffixContainerSignal=v0(`textSuffixContainer`);_prefixSuffixContainers=Rw(()=>[this._iconPrefixContainerSignal(),this._textPrefixContainerSignal(),this._iconSuffixContainerSignal(),this._textSuffixContainerSignal()].map(e=>e?.nativeElement).filter(e=>e!==void 0));_formFieldControl;_prefixChildren;_suffixChildren;_errorChildren;_hintChildren;_labelChild=E0(ii);get hideRequiredMarker(){return this._hideRequiredMarker}set hideRequiredMarker(e){this._hideRequiredMarker=Pt(e)}_hideRequiredMarker=!1;color=`primary`;get floatLabel(){return this._floatLabel||this._defaults?.floatLabel||wp}set floatLabel(e){e!==this._floatLabel&&(this._floatLabel=e,this._changeDetectorRef.markForCheck())}_floatLabel;get appearance(){return this._appearanceSignal()}set appearance(e){let t=e||this._defaults?.appearance||zd;this._appearanceSignal.set(t)}_appearanceSignal=oa(zd);get subscriptSizing(){return this._subscriptSizing||this._defaults?.subscriptSizing||jd}set subscriptSizing(e){this._subscriptSizing=e||this._defaults?.subscriptSizing||jd}_subscriptSizing=null;get hintLabel(){return this._hintLabel}set hintLabel(e){this._hintLabel=e,this._processHints()}_hintLabel=``;_hasIconPrefix=!1;_hasTextPrefix=!1;_hasIconSuffix=!1;_hasTextSuffix=!1;_labelId=this._idGenerator.getId(`mat-mdc-form-field-label-`);_hintLabelId=this._idGenerator.getId(`mat-mdc-hint-`);_describedByIds;get _control(){return this._explicitFormFieldControl||this._formFieldControl}set _control(e){this._explicitFormFieldControl=e}_destroyed=new te$1;_isFocused=null;_explicitFormFieldControl;_previousControl=null;_previousControlValidatorFn=null;_stateChanges;_valueChanges;_describedByChanges;_outlineLabelOffsetResizeObserver=null;_animationsDisabled=ue();constructor(){let e=this._defaults,t=I(Ne);e&&(e.appearance&&(this.appearance=e.appearance),this._hideRequiredMarker=!!e?.hideRequiredMarker,e.color&&(this.color=e.color)),Wm$1(()=>this._currentDirection=t.valueSignal()),this._syncOutlineLabelOffset()}ngAfterViewInit(){this._updateFocusState(),this._animationsDisabled||this._ngZone.runOutsideAngular(()=>{setTimeout(()=>{this._elementRef.nativeElement.classList.add(`mat-form-field-animations-enabled`)},300)}),this._changeDetectorRef.detectChanges()}ngAfterContentInit(){this._assertFormFieldControl(),this._initializeSubscript(),this._initializePrefixAndSuffix()}ngAfterContentChecked(){this._assertFormFieldControl(),this._control!==this._previousControl&&(this._initializeControl(this._previousControl),this._control.ngControl&&this._control.ngControl.control&&(this._previousControlValidatorFn=or(this._control.ngField)?null:this._control.ngControl.control.validator),this._previousControl=this._control,this._changeDetectorRef.markForCheck()),this._control.ngControl&&this._control.ngControl.control&&!or(this._control.ngField)&&this._control.ngControl.control.validator!==this._previousControlValidatorFn&&this._changeDetectorRef.markForCheck()}ngOnDestroy(){this._outlineLabelOffsetResizeObserver?.disconnect(),this._stateChanges?.unsubscribe(),this._valueChanges?.unsubscribe(),this._describedByChanges?.unsubscribe(),this._destroyed.next(),this._destroyed.complete()}getLabelId=Rw(()=>this._hasFloatingLabel()?this._labelId:null);getConnectedOverlayOrigin(){return this._textField||this._elementRef}_animateAndLockLabel(){this._hasFloatingLabel()&&(this.floatLabel=`always`)}_initializeControl(e){let t=this._control,r=`mat-mdc-form-field-type-`;e&&this._elementRef.nativeElement.classList.remove(r+e.controlType),t.controlType&&this._elementRef.nativeElement.classList.add(r+t.controlType),this._stateChanges?.unsubscribe(),this._stateChanges=t.stateChanges?.subscribe(()=>{this._updateFocusState(),this._changeDetectorRef.markForCheck()}),this._describedByChanges?.unsubscribe(),this._describedByChanges=t.stateChanges?.pipe(Al$1([void 0,void 0]),Me$1(()=>[this._unwrapMaybeSignal(t.errorState),t.userAriaDescribedBy]),Qg(),rn(([[o,a],[s,c]])=>o!==s||a!==c)).subscribe(()=>this._syncDescribedByIds()),this._valueChanges?.unsubscribe(),t.ngControl&&t.ngControl.valueChanges&&!or(t.ngField)&&(this._valueChanges=t.ngControl.valueChanges.pipe(Rl$1(this._destroyed)).subscribe(()=>this._changeDetectorRef.markForCheck()))}_checkPrefixAndSuffixTypes(){this._hasIconPrefix=!!this._prefixChildren.find(e=>!e._isText),this._hasTextPrefix=!!this._prefixChildren.find(e=>e._isText),this._hasIconSuffix=!!this._suffixChildren.find(e=>!e._isText),this._hasTextSuffix=!!this._suffixChildren.find(e=>e._isText)}_initializePrefixAndSuffix(){this._checkPrefixAndSuffixTypes(),Bg(this._prefixChildren.changes,this._suffixChildren.changes).subscribe(()=>{this._checkPrefixAndSuffixTypes(),this._changeDetectorRef.markForCheck()})}_initializeSubscript(){this._hintChildren.changes.subscribe(()=>{this._processHints(),this._changeDetectorRef.markForCheck()}),this._errorChildren.changes.subscribe(()=>{this._syncDescribedByIds(),this._changeDetectorRef.markForCheck()}),this._validateHints(),this._syncDescribedByIds()}_assertFormFieldControl(){this._control}_updateFocusState(){let e=this._unwrapMaybeSignal(this._control.focused);e&&!this._isFocused?(this._isFocused=!0,this._lineRipple?.activate()):!e&&(this._isFocused||this._isFocused===null)&&(this._isFocused=!1,this._lineRipple?.deactivate()),this._elementRef.nativeElement.classList.toggle(`mat-focused`,e),this._textField?.nativeElement.classList.toggle(`mdc-text-field--focused`,e)}_syncOutlineLabelOffset(){_0({earlyRead:()=>{if(this._appearanceSignal()!==`outline`)return this._outlineLabelOffsetResizeObserver?.disconnect(),null;if(globalThis.ResizeObserver){this._outlineLabelOffsetResizeObserver||=new globalThis.ResizeObserver(()=>{this._writeOutlinedLabelStyles(this._getOutlinedLabelOffset())});for(let e of this._prefixSuffixContainers())this._outlineLabelOffsetResizeObserver.observe(e,{box:`border-box`})}return this._getOutlinedLabelOffset()},write:e=>this._writeOutlinedLabelStyles(e())})}_shouldAlwaysFloat(){return this.floatLabel===`always`}_hasOutline(){return this.appearance===`outline`}_forceDisplayInfixLabel(){return!this._platform.isBrowser&&this._prefixChildren.length&&!this._shouldLabelFloat()}_hasFloatingLabel=Rw(()=>!!this._labelChild());_shouldLabelFloat(){return this._hasFloatingLabel()?this._shouldAlwaysFloat()||this._unwrapMaybeSignal(this._control.shouldLabelFloat):!1}_shouldForward(e){let t=this._control?.ngField||this._control?.ngControl;if(!t)return!1;if(or(t)){let r=t();return e===`valid`?r.valid():e===`dirty`?r.dirty():e===`touched`?r.touched():e===`pending`?r.pending():e===`untouched`?!r.touched():e===`pristine`?!r.dirty():e===`invalid`?!r.valid():!1}else{let r=t;return e===`valid`?r.valid:e===`dirty`?r.dirty:e===`touched`?r.touched:e===`pending`?r.pending:e===`untouched`?r.untouched:e===`pristine`?r.pristine:e===`invalid`?r.invalid:!1}}_getSubscriptMessageType(){return this._errorChildren&&this._errorChildren.length>0&&this._unwrapMaybeSignal(this._control.errorState)?`error`:`hint`}_handleLabelResized(){this._refreshOutlineNotchWidth()}_refreshOutlineNotchWidth(){!this._hasOutline()||!this._floatingLabel||!this._shouldLabelFloat()?this._notchedOutline?._setNotchWidth(0):this._notchedOutline?._setNotchWidth(this._floatingLabel.getWidth())}_processHints(){this._validateHints(),this._syncDescribedByIds()}_validateHints(){this._hintChildren}_syncDescribedByIds(){if(this._control){let e=[];if(this._control.userAriaDescribedBy&&typeof this._control.userAriaDescribedBy==`string`&&e.push(...this._control.userAriaDescribedBy.split(` `)),this._getSubscriptMessageType()===`hint`){let o=this._hintChildren?this._hintChildren.find(s=>s.align===`start`):null,a=this._hintChildren?this._hintChildren.find(s=>s.align===`end`):null;o?e.push(o.id):this._hintLabel&&e.push(this._hintLabelId),a&&e.push(a.id)}else this._errorChildren&&e.push(...this._errorChildren.map(o=>o.id));let t=this._control.describedByIds,r;if(t){let o=this._describedByIds||e;r=e.concat(t.filter(a=>a&&!o.includes(a)))}else r=e;this._control.setDescribedByIds(r),this._describedByIds=e}}_getOutlinedLabelOffset(){if(!this._hasOutline()||!this._floatingLabel)return null;if(!this._iconPrefixContainer&&!this._textPrefixContainer)return[``,null];if(!this._isAttachedToDom())return null;let e=this._iconPrefixContainer?.nativeElement,t=this._textPrefixContainer?.nativeElement,r=this._iconSuffixContainer?.nativeElement,o=this._textSuffixContainer?.nativeElement,a=e?.getBoundingClientRect().width??0,s=t?.getBoundingClientRect().width??0,c=r?.getBoundingClientRect().width??0,d=o?.getBoundingClientRect().width??0;return[`var(--mat-mdc-form-field-label-transform, ${kp} translateX(${`calc(${this._currentDirection===`rtl`?`-1`:`1`} * (${`${a+s}px`} + var(--mat-mdc-form-field-label-offset-x, 0px)))`}))`,a+s+c+d]}_writeOutlinedLabelStyles(e){if(e!==null){let[t,r]=e;this._floatingLabel&&(this._floatingLabel.element.style.transform=t),r!==null&&this._notchedOutline?._setMaxWidth(r)}}_isAttachedToDom(){let e=this._elementRef.nativeElement;if(e.getRootNode){let t=e.getRootNode();return t&&t!==e}return document.documentElement.contains(e)}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`iconPrefixContainer`],t=[`textPrefixContainer`],r=[`iconSuffixContainer`],o=[`textSuffixContainer`],a=[`textField`],s=[`*`,[[`mat-label`]],[[``,`matPrefix`,``],[``,`matIconPrefix`,``]],[[``,`matTextPrefix`,``]],[[``,`matTextSuffix`,``]],[[``,`matSuffix`,``],[``,`matIconSuffix`,``]],[[`mat-error`],[``,`matError`,``]],[[`mat-hint`,3,`align`,`end`]],[[`mat-hint`,`align`,`end`]]],c=[`*`,`mat-label`,`[matPrefix], [matIconPrefix]`,`[matTextPrefix]`,`[matTextSuffix]`,`[matSuffix], [matIconSuffix]`,`mat-error, [matError]`,`mat-hint:not([align='end'])`,`mat-hint[align='end']`];function d(G,oe){G&1&&Xp$1(0,`span`,21)}function m(G,oe){if(G&1&&(yi(0,`label`,20),ND(1,1),uD(2,d,1,0,`span`,21),Fc$1()),G&2){let g=TD(2);Jp$1(`floating`,g._shouldLabelFloat())(`monitorResize`,g._hasOutline())(`id`,g._labelId),Kp(`for`,g._control.disableAutomaticLabeling?null:g._control.id),sE(2),fD(!g.hideRequiredMarker&&g._unwrapMaybeSignal(g._control.required)?2:-1)}}function _(G,oe){if(G&1&&uD(0,m,3,5,`label`,20),G&2){let g=TD();fD(g._hasFloatingLabel()?0:-1)}}function k(G,oe){G&1&&Xp$1(0,`div`,7)}function p(G,oe){}function z(G,oe){if(G&1&&Bp$1(0,p,0,0,`ng-template`,13),G&2){TD(2);let g=RD(1);Jp$1(`ngTemplateOutlet`,g)}}function K(G,oe){if(G&1&&(yi(0,`div`,9),uD(1,z,1,1,null,13),Fc$1()),G&2){let g=TD();Jp$1(`matFormFieldNotchedOutlineOpen`,g._shouldLabelFloat()),sE(),fD(g._forceDisplayInfixLabel()?-1:1)}}function fe(G,oe){G&1&&(yi(0,`div`,10,2),ND(2,2),Fc$1())}function St(G,oe){G&1&&(yi(0,`div`,11,3),ND(2,3),Fc$1())}function qe(G,oe){}function wt(G,oe){if(G&1&&Bp$1(0,qe,0,0,`ng-template`,13),G&2){TD();let g=RD(1);Jp$1(`ngTemplateOutlet`,g)}}function tn(G,oe){G&1&&(yi(0,`div`,14,4),ND(2,4),Fc$1())}function bt(G,oe){G&1&&(yi(0,`div`,15,5),ND(2,5),Fc$1())}function nn(G,oe){G&1&&Xp$1(0,`div`,16)}function rn(G,oe){G&1&&(yi(0,`div`,18),ND(1,6),Fc$1())}function jt(G,oe){if(G&1&&(yi(0,`mat-hint`,22),rw(1),Fc$1()),G&2){let g=TD(2);Jp$1(`id`,g._hintLabelId),sE(),_h$1(g.hintLabel)}}function _t(G,oe){if(G&1&&(yi(0,`div`,19),uD(1,jt,2,2,`mat-hint`,22),ND(2,7),Xp$1(3,`div`,23),ND(4,8),Fc$1()),G&2){let g=TD();sE(),fD(g.hintLabel?1:-1)}}return LI({type:n,selectors:[[`mat-form-field`]],contentQueries:function(oe,g,se){if(oe&1&&(uh$1(se,g._labelChild,ii,5),ch$1(se,ar,5)(se,xp,5)(se,Hd,5)(se,Ud,5)(se,Eo,5)),oe&2){AD();let Fe;SD(Fe=xD())&&(g._formFieldControl=Fe.first),SD(Fe=xD())&&(g._prefixChildren=Fe),SD(Fe=xD())&&(g._suffixChildren=Fe),SD(Fe=xD())&&(g._errorChildren=Fe),SD(Fe=xD())&&(g._hintChildren=Fe)}},viewQuery:function(oe,g){if(oe&1&&(dh$1(g._iconPrefixContainerSignal,e,5)(g._textPrefixContainerSignal,t,5)(g._iconSuffixContainerSignal,r,5)(g._textSuffixContainerSignal,o,5),lh$1(a,5)(e,5)(t,5)(r,5)(o,5)(Pd,5)(Bd,5)(Vd,5)),oe&2){AD(4);let se;SD(se=xD())&&(g._textField=se.first),SD(se=xD())&&(g._iconPrefixContainer=se.first),SD(se=xD())&&(g._textPrefixContainer=se.first),SD(se=xD())&&(g._iconSuffixContainer=se.first),SD(se=xD())&&(g._textSuffixContainer=se.first),SD(se=xD())&&(g._floatingLabel=se.first),SD(se=xD())&&(g._notchedOutline=se.first),SD(se=xD())&&(g._lineRipple=se.first)}},hostAttrs:[1,`mat-mdc-form-field`],hostVars:38,hostBindings:function(oe,g){oe&2&&yh$1(`mat-mdc-form-field-label-always-float`,g._shouldAlwaysFloat())(`mat-mdc-form-field-has-icon-prefix`,g._hasIconPrefix)(`mat-mdc-form-field-has-icon-suffix`,g._hasIconSuffix)(`mat-form-field-invalid`,g._unwrapMaybeSignal(g._control.errorState))(`mat-form-field-disabled`,g._unwrapMaybeSignal(g._control.disabled))(`mat-form-field-autofilled`,g._unwrapMaybeSignal(g._control.autofilled))(`mat-form-field-appearance-fill`,g.appearance==`fill`)(`mat-form-field-appearance-outline`,g.appearance==`outline`)(`mat-form-field-hide-placeholder`,g._hasFloatingLabel()&&!g._shouldLabelFloat())(`mat-primary`,g.color!==`accent`&&g.color!==`warn`)(`mat-accent`,g.color===`accent`)(`mat-warn`,g.color===`warn`)(`ng-untouched`,g._shouldForward(`untouched`))(`ng-touched`,g._shouldForward(`touched`))(`ng-pristine`,g._shouldForward(`pristine`))(`ng-dirty`,g._shouldForward(`dirty`))(`ng-valid`,g._shouldForward(`valid`))(`ng-invalid`,g._shouldForward(`invalid`))(`ng-pending`,g._shouldForward(`pending`))},inputs:{hideRequiredMarker:`hideRequiredMarker`,color:`color`,floatLabel:`floatLabel`,appearance:`appearance`,subscriptSizing:`subscriptSizing`,hintLabel:`hintLabel`},exportAs:[`matFormField`],features:[hw([{provide:sr,useExisting:n},{provide:Gd,useExisting:n}])],ngContentSelectors:c,decls:18,vars:21,consts:[[`labelTemplate`,``],[`textField`,``],[`iconPrefixContainer`,``],[`textPrefixContainer`,``],[`textSuffixContainer`,``],[`iconSuffixContainer`,``],[1,`mat-mdc-text-field-wrapper`,`mdc-text-field`,3,`click`],[1,`mat-mdc-form-field-focus-overlay`],[1,`mat-mdc-form-field-flex`],[`matFormFieldNotchedOutline`,``,3,`matFormFieldNotchedOutlineOpen`],[1,`mat-mdc-form-field-icon-prefix`],[1,`mat-mdc-form-field-text-prefix`],[1,`mat-mdc-form-field-infix`],[3,`ngTemplateOutlet`],[1,`mat-mdc-form-field-text-suffix`],[1,`mat-mdc-form-field-icon-suffix`],[`matFormFieldLineRipple`,``],[`aria-atomic`,`true`,`aria-live`,`polite`,1,`mat-mdc-form-field-subscript-wrapper`,`mat-mdc-form-field-bottom-align`],[1,`mat-mdc-form-field-error-wrapper`],[1,`mat-mdc-form-field-hint-wrapper`],[`matFormFieldFloatingLabel`,``,3,`floating`,`monitorResize`,`id`],[`aria-hidden`,`true`,1,`mat-mdc-form-field-required-marker`,`mdc-floating-label--required`],[3,`id`],[1,`mat-mdc-form-field-hint-spacer`]],template:function(oe,g){if(oe&1&&(_D(s),Bp$1(0,_,1,1,`ng-template`,null,0,Sw),yi(2,`div`,6,1),ih$1(`click`,function(Fe){return g._control.onContainerClick(Fe)}),uD(4,k,1,0,`div`,7),yi(5,`div`,8),uD(6,K,2,2,`div`,9),uD(7,fe,3,0,`div`,10),uD(8,St,3,0,`div`,11),yi(9,`div`,12),uD(10,wt,1,1,null,13),ND(11),Fc$1(),uD(12,tn,3,0,`div`,14),uD(13,bt,3,0,`div`,15),Fc$1(),uD(14,nn,1,0,`div`,16),Fc$1(),yi(15,`div`,17),uD(16,rn,2,0,`div`,18)(17,_t,5,1,`div`,19),Fc$1()),oe&2){let se,Fe=g._unwrapMaybeSignal(g._control.disabled);sE(2),yh$1(`mdc-text-field--filled`,!g._hasOutline())(`mdc-text-field--outlined`,g._hasOutline())(`mdc-text-field--no-label`,!g._hasFloatingLabel())(`mdc-text-field--disabled`,Fe)(`mdc-text-field--invalid`,g._unwrapMaybeSignal(g._control.errorState)),sE(2),fD(!g._hasOutline()&&!Fe?4:-1),sE(2),fD(g._hasOutline()?6:-1),sE(),fD(g._hasIconPrefix?7:-1),sE(),fD(g._hasTextPrefix?8:-1),sE(2),fD(!g._hasOutline()||g._forceDisplayInfixLabel()?10:-1),sE(2),fD(g._hasTextSuffix?12:-1),sE(),fD(g._hasIconSuffix?13:-1),sE(),fD(g._hasOutline()?-1:14),sE(),yh$1(`mat-mdc-form-field-subscript-dynamic-size`,g.subscriptSizing===`dynamic`);let km=g._getSubscriptMessageType();sE(),fD((se=km)===`error`?16:se===`hint`?17:-1)}},dependencies:[Pd,Bd,Ci,Vd,Eo],styles:[`.mdc-text-field {
  display: inline-flex;
  align-items: baseline;
  padding: 0 16px;
  position: relative;
  box-sizing: border-box;
  overflow: hidden;
  will-change: opacity, transform, color;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  border-bottom-right-radius: 0;
  border-bottom-left-radius: 0;
}

.mdc-text-field__input {
  width: 100%;
  min-width: 0;
  border: none;
  border-radius: 0;
  background: none;
  padding: 0;
  -moz-appearance: none;
  -webkit-appearance: none;
  height: 28px;
}
.mdc-text-field__input::-webkit-calendar-picker-indicator, .mdc-text-field__input::-webkit-search-cancel-button {
  display: none;
}
.mdc-text-field__input::-ms-clear {
  display: none;
}
.mdc-text-field__input:focus {
  outline: none;
}
.mdc-text-field__input:invalid {
  box-shadow: none;
}
.mdc-text-field__input::placeholder {
  opacity: 0;
}
.mdc-text-field__input::-moz-placeholder {
  opacity: 0;
}
.mdc-text-field__input::-webkit-input-placeholder {
  opacity: 0;
}
.mdc-text-field__input:-ms-input-placeholder {
  opacity: 0;
}
.mdc-text-field--no-label .mdc-text-field__input::placeholder, .mdc-text-field--focused .mdc-text-field__input::placeholder {
  opacity: 1;
}
.mdc-text-field--no-label .mdc-text-field__input::-moz-placeholder, .mdc-text-field--focused .mdc-text-field__input::-moz-placeholder {
  opacity: 1;
}
.mdc-text-field--no-label .mdc-text-field__input::-webkit-input-placeholder, .mdc-text-field--focused .mdc-text-field__input::-webkit-input-placeholder {
  opacity: 1;
}
.mdc-text-field--no-label .mdc-text-field__input:-ms-input-placeholder, .mdc-text-field--focused .mdc-text-field__input:-ms-input-placeholder {
  opacity: 1;
}
.mdc-text-field--%NS%disabled:not(.mdc-text-field--no-label) .mdc-text-field__input.mat-mdc-input-disabled-interactive::placeholder {
  opacity: 0;
}
.mdc-text-field--%NS%disabled:not(.mdc-text-field--no-label) .mdc-text-field__input.mat-mdc-input-disabled-interactive::-moz-placeholder {
  opacity: 0;
}
.mdc-text-field--%NS%disabled:not(.mdc-text-field--no-label) .mdc-text-field__input.mat-mdc-input-disabled-interactive::-webkit-input-placeholder {
  opacity: 0;
}
.mdc-text-field--%NS%disabled:not(.mdc-text-field--no-label) .mdc-text-field__input.mat-mdc-input-disabled-interactive:-ms-input-placeholder {
  opacity: 0;
}
.mdc-text-field--outlined .mdc-text-field__input, .mdc-text-field--filled.mdc-text-field--no-label .mdc-text-field__input {
  height: 100%;
}
.mdc-text-field--outlined .mdc-text-field__input {
  display: flex;
  border: none !important;
  background-color: transparent;
}
.mdc-text-field--disabled .mdc-text-field__input {
  pointer-events: auto;
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled) .mdc-text-field__input {
  color: var(--%NS%mat-form-field-filled-input-text-color, var(--%NS%mat-sys-on-surface));
  caret-color: var(--%NS%mat-form-field-filled-caret-color, var(--%NS%mat-sys-primary));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled) .mdc-text-field__input::placeholder {
  color: var(--%NS%mat-form-field-filled-input-text-placeholder-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled) .mdc-text-field__input::-moz-placeholder {
  color: var(--%NS%mat-form-field-filled-input-text-placeholder-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled) .mdc-text-field__input::-webkit-input-placeholder {
  color: var(--%NS%mat-form-field-filled-input-text-placeholder-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled) .mdc-text-field__input:-ms-input-placeholder {
  color: var(--%NS%mat-form-field-filled-input-text-placeholder-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled) .mdc-text-field__input {
  color: var(--%NS%mat-form-field-outlined-input-text-color, var(--%NS%mat-sys-on-surface));
  caret-color: var(--%NS%mat-form-field-outlined-caret-color, var(--%NS%mat-sys-primary));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled) .mdc-text-field__input::placeholder {
  color: var(--%NS%mat-form-field-outlined-input-text-placeholder-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled) .mdc-text-field__input::-moz-placeholder {
  color: var(--%NS%mat-form-field-outlined-input-text-placeholder-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled) .mdc-text-field__input::-webkit-input-placeholder {
  color: var(--%NS%mat-form-field-outlined-input-text-placeholder-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled) .mdc-text-field__input:-ms-input-placeholder {
  color: var(--%NS%mat-form-field-outlined-input-text-placeholder-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--filled.mdc-text-field--%NS%invalid:not(.mdc-text-field--disabled) .mdc-text-field__input {
  caret-color: var(--%NS%mat-form-field-filled-error-caret-color, var(--%NS%mat-sys-error));
}
.mdc-text-field--outlined.mdc-text-field--%NS%invalid:not(.mdc-text-field--disabled) .mdc-text-field__input {
  caret-color: var(--%NS%mat-form-field-outlined-error-caret-color, var(--%NS%mat-sys-error));
}
.mdc-text-field--filled.mdc-text-field--disabled .mdc-text-field__input {
  color: var(--%NS%mat-form-field-filled-disabled-input-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mdc-text-field--outlined.mdc-text-field--disabled .mdc-text-field__input {
  color: var(--%NS%mat-form-field-outlined-disabled-input-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
@media (forced-colors: active) {
  .mdc-text-field--disabled .mdc-text-field__input {
    background-color: Window;
  }
}

.mdc-text-field--filled {
  height: 56px;
  border-bottom-right-radius: 0;
  border-bottom-left-radius: 0;
  border-top-left-radius: var(--%NS%mat-form-field-filled-container-shape, var(--%NS%mat-sys-corner-extra-small));
  border-top-right-radius: var(--%NS%mat-form-field-filled-container-shape, var(--%NS%mat-sys-corner-extra-small));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled) {
  background-color: var(--%NS%mat-form-field-filled-container-color, var(--%NS%mat-sys-surface-variant));
}
.mdc-text-field--filled.mdc-text-field--disabled {
  background-color: var(--%NS%mat-form-field-filled-disabled-container-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 4%, transparent));
}

.mdc-text-field--outlined {
  height: 56px;
  overflow: visible;
  padding-right: max(16px, var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small)));
  padding-left: max(16px, var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small)) + 4px);
}
[dir=rtl] .mdc-text-field--outlined {
  padding-right: max(16px, var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small)) + 4px);
  padding-left: max(16px, var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small)));
}

.mdc-floating-label {
  position: absolute;
  left: 0;
  transform-origin: left top;
  line-height: 1.15rem;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: text;
  overflow: hidden;
  will-change: transform;
}
[dir=rtl] .mdc-floating-label {
  right: 0;
  left: auto;
  transform-origin: right top;
  text-align: right;
}
.mdc-text-field .mdc-floating-label {
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}
.mdc-notched-outline .mdc-floating-label {
  display: inline-block;
  position: relative;
  max-width: 100%;
}
.mdc-text-field--outlined .mdc-floating-label {
  left: 4px;
  right: auto;
}
[dir=rtl] .mdc-text-field--outlined .mdc-floating-label {
  left: auto;
  right: 4px;
}
.mdc-text-field--filled .mdc-floating-label {
  left: 16px;
  right: auto;
}
[dir=rtl] .mdc-text-field--filled .mdc-floating-label {
  left: auto;
  right: 16px;
}
.mdc-text-field--disabled .mdc-floating-label {
  cursor: default;
}
@media (forced-colors: active) {
  .mdc-text-field--disabled .mdc-floating-label {
    z-index: 1;
  }
}
.mdc-text-field--filled.mdc-text-field--no-label .mdc-floating-label {
  display: none;
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled) .mdc-floating-label {
  color: var(--%NS%mat-form-field-filled-label-text-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled).mdc-text-field--focused .mdc-floating-label {
  color: var(--%NS%mat-form-field-filled-focus-label-text-color, var(--%NS%mat-sys-primary));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled):not(.mdc-text-field--focused):hover .mdc-floating-label {
  color: var(--%NS%mat-form-field-filled-hover-label-text-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--filled.mdc-text-field--disabled .mdc-floating-label {
  color: var(--%NS%mat-form-field-filled-disabled-label-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled).mdc-text-field--invalid .mdc-floating-label {
  color: var(--%NS%mat-form-field-filled-error-label-text-color, var(--%NS%mat-sys-error));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled).mdc-text-field--invalid.mdc-text-field--focused .mdc-floating-label {
  color: var(--%NS%mat-form-field-filled-error-focus-label-text-color, var(--%NS%mat-sys-error));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled).mdc-text-field--%NS%invalid:not(.mdc-text-field--disabled):hover .mdc-floating-label {
  color: var(--%NS%mat-form-field-filled-error-hover-label-text-color, var(--%NS%mat-sys-on-error-container));
}
.mdc-text-field--filled .mdc-floating-label {
  font-family: var(--%NS%mat-form-field-filled-label-text-font, var(--%NS%mat-sys-body-large-font));
  font-size: var(--%NS%mat-form-field-filled-label-text-size, var(--%NS%mat-sys-body-large-size));
  font-weight: var(--%NS%mat-form-field-filled-label-text-weight, var(--%NS%mat-sys-body-large-weight));
  letter-spacing: var(--%NS%mat-form-field-filled-label-text-tracking, var(--%NS%mat-sys-body-large-tracking));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled) .mdc-floating-label {
  color: var(--%NS%mat-form-field-outlined-label-text-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled).mdc-text-field--focused .mdc-floating-label {
  color: var(--%NS%mat-form-field-outlined-focus-label-text-color, var(--%NS%mat-sys-primary));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled):not(.mdc-text-field--focused):hover .mdc-floating-label {
  color: var(--%NS%mat-form-field-outlined-hover-label-text-color, var(--%NS%mat-sys-on-surface));
}
.mdc-text-field--outlined.mdc-text-field--disabled .mdc-floating-label {
  color: var(--%NS%mat-form-field-outlined-disabled-label-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled).mdc-text-field--invalid .mdc-floating-label {
  color: var(--%NS%mat-form-field-outlined-error-label-text-color, var(--%NS%mat-sys-error));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled).mdc-text-field--invalid.mdc-text-field--focused .mdc-floating-label {
  color: var(--%NS%mat-form-field-outlined-error-focus-label-text-color, var(--%NS%mat-sys-error));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled).mdc-text-field--%NS%invalid:not(.mdc-text-field--disabled):hover .mdc-floating-label {
  color: var(--%NS%mat-form-field-outlined-error-hover-label-text-color, var(--%NS%mat-sys-on-error-container));
}
.mdc-text-field--outlined .mdc-floating-label {
  font-family: var(--%NS%mat-form-field-outlined-label-text-font, var(--%NS%mat-sys-body-large-font));
  font-size: var(--%NS%mat-form-field-outlined-label-text-size, var(--%NS%mat-sys-body-large-size));
  font-weight: var(--%NS%mat-form-field-outlined-label-text-weight, var(--%NS%mat-sys-body-large-weight));
  letter-spacing: var(--%NS%mat-form-field-outlined-label-text-tracking, var(--%NS%mat-sys-body-large-tracking));
}

.mdc-floating-label--float-above {
  cursor: auto;
  transform: translateY(-106%) scale(0.75);
}
.mdc-text-field--filled .mdc-floating-label--float-above {
  transform: translateY(-106%) scale(0.75);
}
.mdc-text-field--outlined .mdc-floating-label--float-above {
  transform: translateY(-37.25px) scale(1);
  font-size: 0.75rem;
}
.mdc-notched-outline .mdc-floating-label--float-above {
  text-overflow: clip;
}
.mdc-notched-outline--upgraded .mdc-floating-label--float-above {
  max-width: 133.3333333333%;
}
.mdc-text-field--outlined.mdc-notched-outline--upgraded .mdc-floating-label--float-above, .mdc-text-field--outlined .mdc-notched-outline--upgraded .mdc-floating-label--float-above {
  transform: translateY(-34.75px) scale(0.75);
}
.mdc-text-field--outlined.mdc-notched-outline--upgraded .mdc-floating-label--float-above, .mdc-text-field--outlined .mdc-notched-outline--upgraded .mdc-floating-label--float-above {
  font-size: 1rem;
}

.mdc-floating-label--%NS%required:not(.mdc-floating-label--hide-required-marker)::after {
  margin-left: 1px;
  margin-right: 0;
  content: "*";
}
[dir=rtl] .mdc-floating-label--%NS%required:not(.mdc-floating-label--hide-required-marker)::after {
  margin-left: 0;
  margin-right: 1px;
}

.mdc-notched-outline {
  display: flex;
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  height: 100%;
  text-align: left;
  pointer-events: none;
}
[dir=rtl] .mdc-notched-outline {
  text-align: right;
}
.mdc-text-field--outlined .mdc-notched-outline {
  z-index: 1;
}

.mat-mdc-notch-piece {
  box-sizing: border-box;
  height: 100%;
  pointer-events: none;
  border: none;
  border-top: 1px solid;
  border-bottom: 1px solid;
}
.mdc-text-field--focused .mat-mdc-notch-piece {
  border-width: 2px;
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled) .mat-mdc-notch-piece {
  border-color: var(--%NS%mat-form-field-outlined-outline-color, var(--%NS%mat-sys-outline));
  border-width: var(--%NS%mat-form-field-outlined-outline-width, 1px);
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled):not(.mdc-text-field--focused):hover .mat-mdc-notch-piece {
  border-color: var(--%NS%mat-form-field-outlined-hover-outline-color, var(--%NS%mat-sys-on-surface));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled).mdc-text-field--focused .mat-mdc-notch-piece {
  border-color: var(--%NS%mat-form-field-outlined-focus-outline-color, var(--%NS%mat-sys-primary));
}
.mdc-text-field--outlined.mdc-text-field--disabled .mat-mdc-notch-piece {
  border-color: var(--%NS%mat-form-field-outlined-disabled-outline-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 12%, transparent));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled).mdc-text-field--invalid .mat-mdc-notch-piece {
  border-color: var(--%NS%mat-form-field-outlined-error-outline-color, var(--%NS%mat-sys-error));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled).mdc-text-field--%NS%invalid:not(.mdc-text-field--focused):hover .mdc-notched-outline .mat-mdc-notch-piece {
  border-color: var(--%NS%mat-form-field-outlined-error-hover-outline-color, var(--%NS%mat-sys-on-error-container));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled).mdc-text-field--invalid.mdc-text-field--focused .mat-mdc-notch-piece {
  border-color: var(--%NS%mat-form-field-outlined-error-focus-outline-color, var(--%NS%mat-sys-error));
}
.mdc-text-field--%NS%outlined:not(.mdc-text-field--disabled).mdc-text-field--focused .mdc-notched-outline .mat-mdc-notch-piece {
  border-width: var(--%NS%mat-form-field-outlined-focus-outline-width, 2px);
}

.mdc-notched-outline__leading {
  border-left: 1px solid;
  border-right: none;
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
  border-top-left-radius: var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small));
  border-bottom-left-radius: var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small));
}
.mdc-text-field--outlined .mdc-notched-outline .mdc-notched-outline__leading {
  width: max(12px, var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small)));
}
[dir=rtl] .mdc-notched-outline__leading {
  border-left: none;
  border-right: 1px solid;
  border-bottom-left-radius: 0;
  border-top-left-radius: 0;
  border-top-right-radius: var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small));
  border-bottom-right-radius: var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small));
}

.mdc-notched-outline__trailing {
  flex-grow: 1;
  border-left: none;
  border-right: 1px solid;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  border-top-right-radius: var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small));
  border-bottom-right-radius: var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small));
}
[dir=rtl] .mdc-notched-outline__trailing {
  border-left: 1px solid;
  border-right: none;
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
  border-top-left-radius: var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small));
  border-bottom-left-radius: var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small));
}

.mdc-notched-outline__notch {
  flex: 0 0 auto;
  width: auto;
}
.mdc-text-field--outlined .mdc-notched-outline .mdc-notched-outline__notch {
  max-width: min(var(--%NS%mat-form-field-notch-max-width, 100%), calc(100% - max(12px, var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small))) * 2));
}
.mdc-text-field--outlined .mdc-notched-outline--notched .mdc-notched-outline__notch {
  max-width: min(100%, calc(100% - max(12px, var(--%NS%mat-form-field-outlined-container-shape, var(--%NS%mat-sys-corner-extra-small))) * 2));
}
.mdc-text-field--outlined .mdc-notched-outline--notched .mdc-notched-outline__notch {
  padding-top: 1px;
}
.mdc-text-field--focused.mdc-text-field--outlined .mdc-notched-outline--notched .mdc-notched-outline__notch {
  padding-top: 2px;
}
.mdc-notched-outline--notched .mdc-notched-outline__notch {
  padding-left: 0;
  padding-right: 8px;
  border-top: none;
}
[dir=rtl] .mdc-notched-outline--notched .mdc-notched-outline__notch {
  padding-left: 8px;
  padding-right: 0;
}
.mdc-notched-outline--no-label .mdc-notched-outline__notch {
  display: none;
}

.mdc-line-ripple::before, .mdc-line-ripple::after {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  border-bottom-style: solid;
  content: "";
}
.mdc-line-ripple::before {
  z-index: 1;
  border-bottom-width: var(--%NS%mat-form-field-filled-active-indicator-height, 1px);
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled) .mdc-line-ripple::before {
  border-bottom-color: var(--%NS%mat-form-field-filled-active-indicator-color, var(--%NS%mat-sys-on-surface-variant));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled):not(.mdc-text-field--focused):hover .mdc-line-ripple::before {
  border-bottom-color: var(--%NS%mat-form-field-filled-hover-active-indicator-color, var(--%NS%mat-sys-on-surface));
}
.mdc-text-field--filled.mdc-text-field--disabled .mdc-line-ripple::before {
  border-bottom-color: var(--%NS%mat-form-field-filled-disabled-active-indicator-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled).mdc-text-field--invalid .mdc-line-ripple::before {
  border-bottom-color: var(--%NS%mat-form-field-filled-error-active-indicator-color, var(--%NS%mat-sys-error));
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled).mdc-text-field--%NS%invalid:not(.mdc-text-field--focused):hover .mdc-line-ripple::before {
  border-bottom-color: var(--%NS%mat-form-field-filled-error-hover-active-indicator-color, var(--%NS%mat-sys-on-error-container));
}
.mdc-line-ripple::after {
  transform: scaleX(0);
  opacity: 0;
  z-index: 2;
}
.mdc-text-field--filled .mdc-line-ripple::after {
  border-bottom-width: var(--%NS%mat-form-field-filled-focus-active-indicator-height, 2px);
}
.mdc-text-field--%NS%filled:not(.mdc-text-field--disabled) .mdc-line-ripple::after {
  border-bottom-color: var(--%NS%mat-form-field-filled-focus-active-indicator-color, var(--%NS%mat-sys-primary));
}
.mdc-text-field--filled.mdc-text-field--%NS%invalid:not(.mdc-text-field--disabled) .mdc-line-ripple::after {
  border-bottom-color: var(--%NS%mat-form-field-filled-error-focus-active-indicator-color, var(--%NS%mat-sys-error));
}

.mdc-line-ripple--%NS%active::after {
  transform: scaleX(1);
  opacity: 1;
}

.mdc-line-ripple--%NS%deactivating::after {
  opacity: 0;
}

.mdc-text-field--disabled {
  pointer-events: none;
}

.mat-mdc-form-field-textarea-control {
  vertical-align: middle;
  resize: vertical;
  box-sizing: border-box;
  height: auto;
  margin: 0;
  padding: 0;
  border: none;
  overflow: auto;
}

.mat-mdc-form-field-input-control.mat-mdc-form-field-input-control {
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  font: inherit;
  letter-spacing: inherit;
  text-decoration: inherit;
  text-transform: inherit;
  border: none;
}

.mat-mdc-form-field .mat-mdc-floating-label.mdc-floating-label {
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  line-height: normal;
  pointer-events: all;
  will-change: auto;
}

.mat-mdc-form-field:not(.mat-form-field-disabled) .mat-mdc-floating-label.mdc-floating-label {
  cursor: inherit;
}

.mdc-text-field--%NS%no-label:not(.mdc-text-field--textarea) .mat-mdc-form-field-input-control.mdc-text-field__input,
.mat-mdc-text-field-wrapper .mat-mdc-form-field-input-control {
  height: auto;
}

.mat-mdc-text-field-wrapper .mat-mdc-form-field-input-control.mdc-text-field__input[type=color] {
  height: 23px;
}

.mat-mdc-text-field-wrapper {
  height: auto;
  flex: auto;
  will-change: auto;
}

.mat-mdc-form-field-has-icon-prefix .mat-mdc-text-field-wrapper {
  padding-left: 0;
  --%NS%mat-mdc-form-field-label-offset-x: -16px;
}

.mat-mdc-form-field-has-icon-suffix .mat-mdc-text-field-wrapper {
  padding-right: 0;
}

[dir=rtl] .mat-mdc-text-field-wrapper {
  padding-left: 16px;
  padding-right: 16px;
}
[dir=rtl] .mat-mdc-form-field-has-icon-suffix .mat-mdc-text-field-wrapper {
  padding-left: 0;
}
[dir=rtl] .mat-mdc-form-field-has-icon-prefix .mat-mdc-text-field-wrapper {
  padding-right: 0;
}

.mat-form-field-disabled .mdc-text-field__input::placeholder {
  color: var(--%NS%mat-form-field-disabled-input-text-placeholder-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-form-field-disabled .mdc-text-field__input::-moz-placeholder {
  color: var(--%NS%mat-form-field-disabled-input-text-placeholder-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-form-field-disabled .mdc-text-field__input::-webkit-input-placeholder {
  color: var(--%NS%mat-form-field-disabled-input-text-placeholder-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-form-field-disabled .mdc-text-field__input:-ms-input-placeholder {
  color: var(--%NS%mat-form-field-disabled-input-text-placeholder-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}

.mat-mdc-form-field-label-always-float .mdc-text-field__input::placeholder {
  transition-delay: 40ms;
  transition-duration: 110ms;
  opacity: 1;
}

.mat-mdc-text-field-wrapper .mat-mdc-form-field-infix .mat-mdc-floating-label {
  left: auto;
  right: auto;
}

.mat-mdc-text-field-wrapper.mdc-text-field--outlined .mdc-text-field__input {
  display: inline-block;
}

.mat-mdc-form-field .mat-mdc-text-field-wrapper.mdc-text-field .mdc-notched-outline__notch {
  padding-top: 0;
}

.mat-mdc-form-field.mat-mdc-form-field.mat-mdc-form-field.mat-mdc-form-field.mat-mdc-form-field.mat-mdc-form-field .mdc-notched-outline__notch {
  border-left: 1px solid transparent;
}

[dir=rtl] .mat-mdc-form-field.mat-mdc-form-field.mat-mdc-form-field.mat-mdc-form-field.mat-mdc-form-field.mat-mdc-form-field .mdc-notched-outline__notch {
  border-left: none;
  border-right: 1px solid transparent;
}

.mat-mdc-form-field-infix {
  min-height: var(--%NS%mat-form-field-container-height, 56px);
  padding-top: var(--%NS%mat-form-field-filled-with-label-container-padding-top, 24px);
  padding-bottom: var(--%NS%mat-form-field-filled-with-label-container-padding-bottom, 8px);
}
.mdc-text-field--outlined .mat-mdc-form-field-infix, .mdc-text-field--no-label .mat-mdc-form-field-infix {
  padding-top: var(--%NS%mat-form-field-container-vertical-padding, 16px);
  padding-bottom: var(--%NS%mat-form-field-container-vertical-padding, 16px);
}

.mat-mdc-text-field-wrapper .mat-mdc-form-field-flex .mat-mdc-floating-label {
  top: calc(var(--%NS%mat-form-field-container-height, 56px) / 2);
}

.mdc-text-field--filled .mat-mdc-floating-label {
  display: var(--%NS%mat-form-field-filled-label-display, block);
}

.mat-mdc-text-field-wrapper.mdc-text-field--outlined .mdc-notched-outline--upgraded .mdc-floating-label--float-above {
  --%NS%mat-mdc-form-field-label-transform: translateY(calc(calc(6.75px + var(--%NS%mat-form-field-container-height, 56px) / 2) * -1))
    scale(var(--%NS%mat-mdc-form-field-floating-label-scale, 0.75));
  transform: var(--%NS%mat-mdc-form-field-label-transform);
}

@keyframes _mat-form-field-subscript-animation {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.mat-mdc-form-field-subscript-wrapper {
  box-sizing: border-box;
  width: 100%;
  position: relative;
}

.mat-mdc-form-field-hint-wrapper,
.mat-mdc-form-field-error-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 0 16px;
  opacity: 1;
  transform: translateY(0);
  animation: _mat-form-field-subscript-animation 0ms cubic-bezier(0.55, 0, 0.55, 0.2);
}

.mat-mdc-form-field-subscript-dynamic-size .mat-mdc-form-field-hint-wrapper,
.mat-mdc-form-field-subscript-dynamic-size .mat-mdc-form-field-error-wrapper {
  position: static;
}

.mat-mdc-form-field-bottom-align::before {
  content: "";
  display: inline-block;
  height: 16px;
}

.mat-mdc-form-field-bottom-align.mat-mdc-form-field-subscript-dynamic-size::before {
  content: unset;
}

.mat-mdc-form-field-hint-end {
  order: 1;
}

.mat-mdc-form-field-hint-wrapper {
  display: flex;
}

.mat-mdc-form-field-hint-spacer {
  flex: 1 0 1em;
}

.mat-mdc-form-field-error {
  display: block;
  color: var(--%NS%mat-form-field-error-text-color, var(--%NS%mat-sys-error));
}

.mat-mdc-form-field-subscript-wrapper,
.mat-mdc-form-field-bottom-align::before {
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  font-family: var(--%NS%mat-form-field-subscript-text-font, var(--%NS%mat-sys-body-small-font));
  line-height: var(--%NS%mat-form-field-subscript-text-line-height, var(--%NS%mat-sys-body-small-line-height));
  font-size: var(--%NS%mat-form-field-subscript-text-size, var(--%NS%mat-sys-body-small-size));
  letter-spacing: var(--%NS%mat-form-field-subscript-text-tracking, var(--%NS%mat-sys-body-small-tracking));
  font-weight: var(--%NS%mat-form-field-subscript-text-weight, var(--%NS%mat-sys-body-small-weight));
}

.mat-mdc-form-field-focus-overlay {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  position: absolute;
  opacity: 0;
  pointer-events: none;
  background-color: var(--%NS%mat-form-field-state-layer-color, var(--%NS%mat-sys-on-surface));
}
.mat-mdc-text-field-wrapper:hover .mat-mdc-form-field-focus-overlay {
  opacity: var(--%NS%mat-form-field-hover-state-layer-opacity, var(--%NS%mat-sys-hover-state-layer-opacity));
}
.mat-mdc-form-field.mat-focused .mat-mdc-form-field-focus-overlay {
  opacity: var(--%NS%mat-form-field-focus-state-layer-opacity, 0);
}

select.mat-mdc-form-field-input-control {
  -moz-appearance: none;
  -webkit-appearance: none;
  background-color: transparent;
  display: inline-flex;
  box-sizing: border-box;
}
select.mat-mdc-form-field-input-control:not(:disabled) {
  cursor: pointer;
}
select.mat-mdc-form-field-input-control:not(.mat-mdc-native-select-inline) option {
  color: var(--%NS%mat-form-field-select-option-text-color, var(--%NS%mat-sys-neutral10));
}
select.mat-mdc-form-field-input-control:not(.mat-mdc-native-select-inline) option:disabled {
  color: var(--%NS%mat-form-field-select-disabled-option-text-color, color-mix(in srgb, var(--%NS%mat-sys-neutral10) 38%, transparent));
}

.mat-mdc-form-field-type-mat-native-select .mat-mdc-form-field-infix::after {
  content: "";
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 5px solid;
  position: absolute;
  right: 0;
  top: 50%;
  margin-top: -2.5px;
  pointer-events: none;
  color: var(--%NS%mat-form-field-enabled-select-arrow-color, var(--%NS%mat-sys-on-surface-variant));
}
[dir=rtl] .mat-mdc-form-field-type-mat-native-select .mat-mdc-form-field-infix::after {
  right: auto;
  left: 0;
}
.mat-mdc-form-field-type-mat-native-select.mat-focused .mat-mdc-form-field-infix::after {
  color: var(--%NS%mat-form-field-focus-select-arrow-color, var(--%NS%mat-sys-primary));
}
.mat-mdc-form-field-type-mat-native-select.mat-form-field-disabled .mat-mdc-form-field-infix::after {
  color: var(--%NS%mat-form-field-disabled-select-arrow-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-mdc-form-field-type-mat-native-select .mat-mdc-form-field-input-control {
  padding-right: 15px;
}
[dir=rtl] .mat-mdc-form-field-type-mat-native-select .mat-mdc-form-field-input-control {
  padding-right: 0;
  padding-left: 15px;
}

@media (forced-colors: active) {
  .mat-form-field-appearance-fill .mat-mdc-text-field-wrapper {
    outline: solid 1px;
  }
}
@media (forced-colors: active) {
  .mat-form-field-appearance-fill.mat-form-field-disabled .mat-mdc-text-field-wrapper {
    outline-color: GrayText;
  }
}

@media (forced-colors: active) {
  .mat-form-field-appearance-fill.mat-focused .mat-mdc-text-field-wrapper {
    outline: dashed 3px;
  }
}

@media (forced-colors: active) {
  .mat-mdc-form-field.mat-focused .mdc-notched-outline {
    border: dashed 3px;
  }
}

.mat-mdc-form-field-input-control[type=date], .mat-mdc-form-field-input-control[type=datetime], .mat-mdc-form-field-input-control[type=datetime-local], .mat-mdc-form-field-input-control[type=month], .mat-mdc-form-field-input-control[type=week], .mat-mdc-form-field-input-control[type=time] {
  line-height: 1;
}
.mat-mdc-form-field-input-control::-webkit-datetime-edit {
  line-height: 1;
  padding: 0;
  margin-bottom: -2px;
}

.mat-mdc-form-field {
  --%NS%mat-mdc-form-field-floating-label-scale: 0.75;
  display: inline-flex;
  flex-direction: column;
  min-width: 0;
  text-align: left;
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  font-family: var(--%NS%mat-form-field-container-text-font, var(--%NS%mat-sys-body-large-font));
  line-height: var(--%NS%mat-form-field-container-text-line-height, var(--%NS%mat-sys-body-large-line-height));
  font-size: var(--%NS%mat-form-field-container-text-size, var(--%NS%mat-sys-body-large-size));
  letter-spacing: var(--%NS%mat-form-field-container-text-tracking, var(--%NS%mat-sys-body-large-tracking));
  font-weight: var(--%NS%mat-form-field-container-text-weight, var(--%NS%mat-sys-body-large-weight));
}
.mat-mdc-form-field .mdc-text-field--outlined .mdc-floating-label--float-above {
  font-size: calc(var(--%NS%mat-form-field-outlined-label-text-populated-size) * var(--%NS%mat-mdc-form-field-floating-label-scale));
}
.mat-mdc-form-field .mdc-text-field--outlined .mdc-notched-outline--upgraded .mdc-floating-label--float-above {
  font-size: var(--%NS%mat-form-field-outlined-label-text-populated-size);
}
[dir=rtl] .mat-mdc-form-field {
  text-align: right;
}

.mat-mdc-form-field-flex {
  display: inline-flex;
  align-items: baseline;
  box-sizing: border-box;
  width: 100%;
}

.mat-mdc-text-field-wrapper {
  width: 100%;
  z-index: 0;
}

.mat-mdc-form-field-icon-prefix,
.mat-mdc-form-field-icon-suffix {
  align-self: center;
  line-height: 0;
  pointer-events: auto;
  position: relative;
  z-index: 1;
}
.mat-mdc-form-field-icon-prefix > .mat-icon,
.mat-mdc-form-field-icon-suffix > .mat-icon {
  padding: 0 12px;
  box-sizing: content-box;
}

.mat-mdc-form-field-icon-prefix {
  color: var(--%NS%mat-form-field-leading-icon-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-form-field-disabled .mat-mdc-form-field-icon-prefix {
  color: var(--%NS%mat-form-field-disabled-leading-icon-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}

.mat-mdc-form-field-icon-suffix {
  color: var(--%NS%mat-form-field-trailing-icon-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-form-field-disabled .mat-mdc-form-field-icon-suffix {
  color: var(--%NS%mat-form-field-disabled-trailing-icon-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-form-field-invalid .mat-mdc-form-field-icon-suffix {
  color: var(--%NS%mat-form-field-error-trailing-icon-color, var(--%NS%mat-sys-error));
}
.mat-form-field-invalid:not(.mat-focused):not(.mat-form-field-disabled) .mat-mdc-text-field-wrapper:hover .mat-mdc-form-field-icon-suffix {
  color: var(--%NS%mat-form-field-error-hover-trailing-icon-color, var(--%NS%mat-sys-on-error-container));
}
.mat-form-field-invalid.mat-focused .mat-mdc-text-field-wrapper .mat-mdc-form-field-icon-suffix {
  color: var(--%NS%mat-form-field-error-focus-trailing-icon-color, var(--%NS%mat-sys-error));
}

.mat-mdc-form-field-icon-prefix,
[dir=rtl] .mat-mdc-form-field-icon-suffix {
  padding: 0 4px 0 0;
}

.mat-mdc-form-field-icon-suffix,
[dir=rtl] .mat-mdc-form-field-icon-prefix {
  padding: 0 0 0 4px;
}

.mat-mdc-form-field-subscript-wrapper .mat-icon,
.mat-mdc-form-field label .mat-icon {
  width: 1em;
  height: 1em;
  font-size: inherit;
}

.mat-mdc-form-field-infix {
  flex: auto;
  min-width: 0;
  width: 180px;
  position: relative;
  box-sizing: border-box;
}
.mat-mdc-form-field-infix:has(textarea[cols]) {
  width: auto;
}

.mat-mdc-form-field .mdc-notched-outline__notch {
  margin-left: -1px;
  -webkit-clip-path: inset(-9em -999em -9em 1px);
  clip-path: inset(-9em -999em -9em 1px);
}
[dir=rtl] .mat-mdc-form-field .mdc-notched-outline__notch {
  margin-left: 0;
  margin-right: -1px;
  -webkit-clip-path: inset(-9em 1px -9em -999em);
  clip-path: inset(-9em 1px -9em -999em);
}

.mat-mdc-form-field.mat-form-field-animations-enabled .mdc-floating-label {
  transition: transform 150ms cubic-bezier(0.4, 0, 0.2, 1), color 150ms cubic-bezier(0.4, 0, 0.2, 1);
}
.mat-mdc-form-field.mat-form-field-animations-enabled .mdc-text-field__input {
  transition: opacity 150ms cubic-bezier(0.4, 0, 0.2, 1);
}
.mat-mdc-form-field.mat-form-field-animations-enabled .mdc-text-field__input::placeholder {
  transition: opacity 67ms cubic-bezier(0.4, 0, 0.2, 1);
}
.mat-mdc-form-field.mat-form-field-animations-enabled .mdc-text-field__input::-moz-placeholder {
  transition: opacity 67ms cubic-bezier(0.4, 0, 0.2, 1);
}
.mat-mdc-form-field.mat-form-field-animations-enabled .mdc-text-field__input::-webkit-input-placeholder {
  transition: opacity 67ms cubic-bezier(0.4, 0, 0.2, 1);
}
.mat-mdc-form-field.mat-form-field-animations-enabled .mdc-text-field__input:-ms-input-placeholder {
  transition: opacity 67ms cubic-bezier(0.4, 0, 0.2, 1);
}
.mat-mdc-form-field.mat-form-field-animations-enabled.mdc-text-field--no-label .mdc-text-field__input::placeholder, .mat-mdc-form-field.mat-form-field-animations-enabled.mdc-text-field--focused .mdc-text-field__input::placeholder {
  transition-delay: 40ms;
  transition-duration: 110ms;
}
.mat-mdc-form-field.mat-form-field-animations-enabled.mdc-text-field--no-label .mdc-text-field__input::-moz-placeholder, .mat-mdc-form-field.mat-form-field-animations-enabled.mdc-text-field--focused .mdc-text-field__input::-moz-placeholder {
  transition-delay: 40ms;
  transition-duration: 110ms;
}
.mat-mdc-form-field.mat-form-field-animations-enabled.mdc-text-field--no-label .mdc-text-field__input::-webkit-input-placeholder, .mat-mdc-form-field.mat-form-field-animations-enabled.mdc-text-field--focused .mdc-text-field__input::-webkit-input-placeholder {
  transition-delay: 40ms;
  transition-duration: 110ms;
}
.mat-mdc-form-field.mat-form-field-animations-enabled.mdc-text-field--no-label .mdc-text-field__input:-ms-input-placeholder, .mat-mdc-form-field.mat-form-field-animations-enabled.mdc-text-field--focused .mdc-text-field__input:-ms-input-placeholder {
  transition-delay: 40ms;
  transition-duration: 110ms;
}
.mat-mdc-form-field.mat-form-field-animations-enabled .mdc-text-field--%NS%filled:not(.mdc-ripple-upgraded):focus .mdc-text-field__ripple::before {
  transition-duration: 75ms;
}
.mat-mdc-form-field.mat-form-field-animations-enabled .mdc-line-ripple::after {
  transition: transform 180ms cubic-bezier(0.4, 0, 0.2, 1), opacity 180ms cubic-bezier(0.4, 0, 0.2, 1);
}
.mat-mdc-form-field.mat-form-field-animations-enabled .mat-mdc-form-field-hint-wrapper,
.mat-mdc-form-field.mat-form-field-animations-enabled .mat-mdc-form-field-error-wrapper {
  animation-duration: 300ms;
}

.mdc-notched-outline .mdc-floating-label {
  max-width: calc(100% + 1px);
}

.mdc-notched-outline--upgraded .mdc-floating-label--float-above {
  max-width: calc(133.3333333333% + 1px);
}
`],encapsulation:2})})()}return n})();var Dp=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵcmp=LI({type:n,selectors:[[`ng-component`]],hostAttrs:[`cdk-text-field-style-loader`,``],decls:0,vars:0,template:function(t,r){},styles:[`textarea.cdk-textarea-autosize {
  resize: none;
}

textarea.cdk-textarea-autosize-measuring {
  padding: 2px 0 !important;
  box-sizing: content-box !important;
  height: auto !important;
  overflow: hidden !important;
}

textarea.cdk-textarea-autosize-measuring-firefox {
  padding: 2px 0 !important;
  box-sizing: content-box !important;
  height: 0 !important;
}

@keyframes cdk-text-field-autofill-start { /*!*/ }
@keyframes cdk-text-field-autofill-end { /*!*/ }
.cdk-text-field-autofill-monitored:-webkit-autofill {
  animation: cdk-text-field-autofill-start 0s 1ms;
}

.cdk-text-field-autofill-monitored:not(:-webkit-autofill) {
  animation: cdk-text-field-autofill-end 0s 1ms;
}
`],encapsulation:2})}return n})();var Ep={passive:!0};var Wd=(()=>{class n{_platform=I(J);_ngZone=I(z);_renderer=I(mr$1).createRenderer(null,null);_styleLoader=I(Se);_monitoredElements=new Map;monitor(e){if(!this._platform.isBrowser)return ht$1;this._styleLoader.load(Dp);let t=je(e),r=this._monitoredElements.get(t);if(r)return r.subject;let o=new te$1,a=`cdk-text-field-autofilled`,s=d=>{d.animationName===`cdk-text-field-autofill-start`&&!t.classList.contains(a)?(t.classList.add(a),this._ngZone.run(()=>o.next({target:d.target,isAutofilled:!0}))):d.animationName===`cdk-text-field-autofill-end`&&t.classList.contains(a)&&(t.classList.remove(a),this._ngZone.run(()=>o.next({target:d.target,isAutofilled:!1})))},c=this._ngZone.runOutsideAngular(()=>(t.classList.add(`cdk-text-field-autofill-monitored`),this._renderer.listen(t,`animationstart`,s,Ep)));return this._monitoredElements.set(t,{subject:o,unlisten:c}),o}stopMonitoring(e){let t=je(e),r=this._monitoredElements.get(t);r&&(r.unlisten(),r.subject.complete(),t.classList.remove(`cdk-text-field-autofill-monitored`),t.classList.remove(`cdk-text-field-autofilled`),this._monitoredElements.delete(t))}ngOnDestroy(){this._monitoredElements.forEach((e,t)=>this.stopMonitoring(t))}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var Yd=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({})}return n})();var Xd=new S(`MAT_INPUT_VALUE_ACCESSOR`);var Ao=(()=>{class n{isErrorState(e,t){return!!(e&&e.invalid&&(e.touched||t&&t.submitted))}isSignalErrorState(e){if(!e)return!1;let t=e().invalid(),r=e().touched();return t&&r}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var ri=class{_defaultMatcher;_parentFormGroup;_parentForm;_stateChanges;errorState=!1;matcher;ngControl;formField;constructor(i,e,t,r,o){this._defaultMatcher=i,this._parentFormGroup=t,this._parentForm=r,this._stateChanges=o,e?ia$1(e.field)&&!e.updateValueAndValidity?(this.formField=e,this.ngControl=null):(this.formField=null,this.ngControl=e):this.ngControl=this.formField=null}updateErrorState(){let i=this.errorState,e=this._getCurrentErrorState(this.matcher||this._defaultMatcher);e!==i&&(this.errorState=e,this._stateChanges.next())}_getCurrentErrorState(i){if(this.formField&&i?.isSignalErrorState)return i.isSignalErrorState(this.formField.field())??!1;let e=this._parentFormGroup||this._parentForm,t=this.ngControl?this.ngControl.control:null;return i?.isErrorState(t,e)??!1}};var cr=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[to,lr,te]})}return n})();var Ap=[`button`,`checkbox`,`file`,`hidden`,`image`,`radio`,`range`,`reset`,`submit`];var Ip=new S(`MAT_INPUT_CONFIG`);var Kd=(()=>{class n{_elementRef=I(Dr);_platform=I(J);ngControl=I(Ye,{optional:!0,self:!0});_autofillMonitor=I(Wd);_ngZone=I(z);_formField=I(sr,{optional:!0});_renderer=I(La$1);_uid=I(me).getId(`mat-input-`);_previousNativeValue;_inputValueAccessor;_signalBasedValueAccessor;_previousPlaceholder=null;_errorStateTracker;_config=I(Ip,{optional:!0});_cleanupIosKeyup;_cleanupWebkitWheel;_isServer=!1;_isNativeSelect=!1;_isTextarea=!1;_isInFormField=!1;focused=!1;stateChanges=new te$1;controlType=`mat-input`;autofilled=!1;get disabled(){return this._disabled}set disabled(e){this._disabled=Pt(e),this.focused&&(this.focused=!1,this.stateChanges.next())}_disabled=!1;get id(){return this._id}set id(e){this._id=e||this._uid}_id;placeholder;name;get required(){return this._required??this.ngControl?.control?.hasValidator(Ct.required)??!1}set required(e){this._required=Pt(e)}_required;get type(){return this._type}set type(e){this._type=e||`text`,this._validateType(),!this._isTextarea&&ja().has(this._type)&&(this._elementRef.nativeElement.type=this._type)}_type=`text`;get errorStateMatcher(){return this._errorStateTracker.matcher}set errorStateMatcher(e){this._errorStateTracker.matcher=e}userAriaDescribedBy;get value(){return this._signalBasedValueAccessor?this._signalBasedValueAccessor.value():this._inputValueAccessor.value}set value(e){e!==this.value&&(this._signalBasedValueAccessor?this._signalBasedValueAccessor.value.set(e):this._inputValueAccessor.value=e,this.stateChanges.next())}get readonly(){return this._readonly}set readonly(e){this._readonly=Pt(e)}_readonly=!1;disabledInteractive;get errorState(){return this._errorStateTracker.errorState}set errorState(e){this._errorStateTracker.errorState=e}_neverEmptyInputTypes=[`date`,`datetime`,`datetime-local`,`month`,`time`,`week`].filter(e=>ja().has(e));constructor(){let e=I(rr,{optional:!0}),t=I(Cn,{optional:!0}),r=I(Ao),o=I(Xd,{optional:!0,self:!0}),a=I(ko,{optional:!0,self:!0}),s=this._elementRef.nativeElement,c=s.nodeName.toLowerCase();o?ia$1(o.value)?this._signalBasedValueAccessor=o:this._inputValueAccessor=o:this._inputValueAccessor=s,this._previousNativeValue=this.value,this.id=this.id,this._platform.IOS&&this._ngZone.runOutsideAngular(()=>{this._cleanupIosKeyup=this._renderer.listen(s,`keyup`,this._iOSKeyupListener)}),this._errorStateTracker=new ri(r,a||this.ngControl,t,e,this.stateChanges),this._isServer=!this._platform.isBrowser,this._isNativeSelect=c===`select`,this._isTextarea=c===`textarea`,this._isInFormField=!!this._formField,this.disabledInteractive=this._config?.disabledInteractive||!1,this._isNativeSelect&&(this.controlType=s.multiple?`mat-native-select-multiple`:`mat-native-select`),this._signalBasedValueAccessor&&Wm$1(()=>{this._signalBasedValueAccessor.value(),this.stateChanges.next()})}ngAfterViewInit(){this._platform.isBrowser&&this._autofillMonitor.monitor(this._elementRef.nativeElement).subscribe(e=>{this.autofilled=e.isAutofilled,this.stateChanges.next()})}ngOnChanges(){this.stateChanges.next()}ngOnDestroy(){this.stateChanges.complete(),this._platform.isBrowser&&this._autofillMonitor.stopMonitoring(this._elementRef.nativeElement),this._cleanupIosKeyup?.(),this._cleanupWebkitWheel?.()}ngDoCheck(){this.ngControl&&(this.updateErrorState(),this.ngControl.disabled!==null&&this.ngControl.disabled!==this.disabled&&(this.disabled=this.ngControl.disabled,this.stateChanges.next())),this._dirtyCheckNativeValue(),this._dirtyCheckPlaceholder()}focus(e){this._elementRef.nativeElement.focus(e)}updateErrorState(){this._errorStateTracker.updateErrorState()}_focusChanged(e){if(e!==this.focused){if(!this._isNativeSelect&&e&&this.disabled&&this.disabledInteractive){let t=this._elementRef.nativeElement;t.type===`number`?(t.type=`text`,t.setSelectionRange(0,0),t.type=`number`):t.setSelectionRange(0,0)}this.focused=e,this.stateChanges.next()}}_onInput(){}_dirtyCheckNativeValue(){let e=this._elementRef.nativeElement.value;this._previousNativeValue!==e&&(this._previousNativeValue=e,this.stateChanges.next())}_dirtyCheckPlaceholder(){let e=this._getPlaceholder();if(e!==this._previousPlaceholder){let t=this._elementRef.nativeElement;this._previousPlaceholder=e,e?t.setAttribute(`placeholder`,e):t.removeAttribute(`placeholder`)}}_getPlaceholder(){return this.placeholder||null}_validateType(){Ap.indexOf(this._type)}_isNeverEmpty(){return this._neverEmptyInputTypes.indexOf(this._type)>-1}_isBadInput(){let e=this._elementRef.nativeElement.validity;return e&&e.badInput}get empty(){return!this._isNeverEmpty()&&!this._elementRef.nativeElement.value&&!this._isBadInput()&&!this.autofilled}get shouldLabelFloat(){if(this._isNativeSelect){let e=this._elementRef.nativeElement,t=e.options[0];return this.focused||e.multiple||!this.empty||!!(e.selectedIndex>-1&&t&&t.label)}else return this.focused&&!this.disabled||!this.empty}get describedByIds(){return this._elementRef.nativeElement.getAttribute(`aria-describedby`)?.split(` `)||[]}setDescribedByIds(e){let t=this._elementRef.nativeElement;e.length?t.setAttribute(`aria-describedby`,e.join(` `)):t.removeAttribute(`aria-describedby`)}onContainerClick(){this.focused||this.focus()}_isInlineSelect(){let e=this._elementRef.nativeElement;return this._isNativeSelect&&(e.multiple||e.size>1)}_iOSKeyupListener=e=>{let t=e.target;!t.value&&t.selectionStart===0&&t.selectionEnd===0&&(t.setSelectionRange(1,1),t.setSelectionRange(0,0))};_getReadonlyAttribute(){return this._isNativeSelect?null:this.readonly||this.disabled&&this.disabledInteractive?`true`:null}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[`input`,`matInput`,``],[`textarea`,`matInput`,``],[`select`,`matNativeControl`,``],[`input`,`matNativeControl`,``],[`textarea`,`matNativeControl`,``]],hostAttrs:[1,`mat-mdc-input-element`],hostVars:21,hostBindings:function(t,r){t&1&&ih$1(`focus`,function(){return r._focusChanged(!0)})(`blur`,function(){return r._focusChanged(!1)})(`input`,function(){return r._onInput()}),t&2&&(rh$1(`id`,r.id)(`disabled`,r.disabled&&!r.disabledInteractive)(`required`,r.required),Kp(`name`,r.name||null)(`readonly`,r._getReadonlyAttribute())(`aria-disabled`,r.disabled&&r.disabledInteractive?`true`:null)(`aria-invalid`,r.empty&&r.required?null:r.errorState)(`aria-required`,r.required)(`id`,r.id),yh$1(`mat-input-server`,r._isServer)(`mat-mdc-form-field-textarea-control`,r._isInFormField&&r._isTextarea)(`mat-mdc-form-field-input-control`,r._isInFormField)(`mat-mdc-input-disabled-interactive`,r.disabledInteractive)(`mdc-text-field__input`,r._isInFormField)(`mat-mdc-native-select-inline`,r._isInlineSelect()))},inputs:{disabled:`disabled`,id:`id`,placeholder:`placeholder`,name:`name`,required:`required`,type:`type`,errorStateMatcher:`errorStateMatcher`,userAriaDescribedBy:[0,`aria-describedby`,`userAriaDescribedBy`],value:`value`,readonly:`readonly`,disabledInteractive:[2,`disabledInteractive`,`disabledInteractive`,T0]},exportAs:[`matInput`],features:[hw([{provide:ar,useExisting:n}]),iy]})}return n})();var nk=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[cr,cr,Yd,te]})}return n})();var qd=(()=>{class n{labelPosition=`after`;static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){return LI({type:n,selectors:[[``,`mat-internal-form-field`,``]],hostAttrs:[1,`mdc-form-field`,`mat-internal-form-field`],hostVars:2,hostBindings:function(r,o){r&2&&yh$1(`mdc-form-field--align-end`,o.labelPosition===`before`)},inputs:{labelPosition:`labelPosition`},ngContentSelectors:[`*`],decls:1,vars:0,template:function(r,o){r&1&&(_D(),ND(0))},styles:[`.mat-internal-form-field {
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
}
.mat-internal-form-field > label, .mat-internal-form-field > .mat-internal-form-field-label {
  margin-left: 0;
  margin-right: auto;
  padding-left: 4px;
  padding-right: 0;
  order: 0;
}
[dir=rtl] .mat-internal-form-field > label, [dir=rtl] .mat-internal-form-field > .mat-internal-form-field-label {
  margin-left: auto;
  margin-right: 0;
  padding-left: 0;
  padding-right: 4px;
}

.mdc-form-field--align-end > label, .mdc-form-field--align-end > .mat-internal-form-field-label {
  margin-left: auto;
  margin-right: 0;
  padding-left: 0;
  padding-right: 4px;
  order: -1;
}
[dir=rtl] .mdc-form-field--align-end .mdc-form-field--align-end label, [dir=rtl] .mdc-form-field--align-end .mdc-form-field--align-end .mat-internal-form-field-label {
  margin-left: 0;
  margin-right: auto;
  padding-left: 4px;
  padding-right: 0;
}
`],encapsulation:2})})()}return n})();var ms={color:`accent`,clickAction:`check-indeterminate`,disabledInteractive:!1};var Tp=new S(`mat-checkbox-default-options`,{providedIn:`root`,factory:()=>ms});var Oe=(function(n){return n[n.Init=0]=`Init`,n[n.Checked=1]=`Checked`,n[n.Unchecked=2]=`Unchecked`,n[n.Indeterminate=3]=`Indeterminate`,n})(Oe||{});var us=class{source;checked};var dr=(()=>{class n{_elementRef=I(Dr);_changeDetectorRef=I(w0);_ngZone=I(z);_animationsDisabled=ue();_options=I(Tp,{optional:!0});focus(){this._inputElement.nativeElement.focus()}_createChangeEvent(e){let t=new us;return t.source=this,t.checked=e,t}_getAnimationTargetElement(){return this._inputElement?.nativeElement}_animationClasses={uncheckedToChecked:`mdc-checkbox--anim-unchecked-checked`,uncheckedToIndeterminate:`mdc-checkbox--anim-unchecked-indeterminate`,checkedToUnchecked:`mdc-checkbox--anim-checked-unchecked`,checkedToIndeterminate:`mdc-checkbox--anim-checked-indeterminate`,indeterminateToChecked:`mdc-checkbox--anim-indeterminate-checked`,indeterminateToUnchecked:`mdc-checkbox--anim-indeterminate-unchecked`};ariaLabel=``;ariaLabelledby=null;ariaDescribedby;ariaExpanded;ariaControls;ariaOwns;_uniqueId;id;get inputId(){return`${this.id||this._uniqueId}-input`}required=!1;labelPosition=`after`;name=null;change=new Fe;indeterminateChange=new Fe;value;disableRipple=!1;_inputElement;tabIndex;color;disabledInteractive;_onTouched=()=>{};_currentAnimationClass=``;_currentCheckState=Oe.Init;_controlValueAccessorChangeFn=()=>{};_validatorChangeFn=()=>{};constructor(){I(Se).load(Zt);let e=I(new Bh$1(`tabindex`),{optional:!0});this._options=this._options||ms,this.color=this._options.color||ms.color,this.tabIndex=e==null?0:parseInt(e)||0,this.id=this._uniqueId=I(me).getId(`mat-mdc-checkbox-`),this.disabledInteractive=this._options?.disabledInteractive??!1}ngOnChanges(e){e.required&&this._validatorChangeFn()}ngAfterViewInit(){this._syncIndeterminate(this.indeterminate)}get checked(){return this._checked}set checked(e){e!=this.checked&&(this._checked=e,this._changeDetectorRef.markForCheck())}_checked=!1;get disabled(){return this._disabled}set disabled(e){e!==this.disabled&&(this._disabled=e,this._changeDetectorRef.markForCheck())}_disabled=!1;get indeterminate(){return this._indeterminate()}set indeterminate(e){let t=e!=this._indeterminate();this._indeterminate.set(e),t&&(e?this._transitionCheckState(Oe.Indeterminate):this._transitionCheckState(this.checked?Oe.Checked:Oe.Unchecked),this.indeterminateChange.emit(e)),this._syncIndeterminate(e)}_indeterminate=oa(!1);_isRippleDisabled(){return this.disableRipple||this.disabled}_onLabelTextChange(){this._changeDetectorRef.detectChanges()}writeValue(e){this.checked=!!e}registerOnChange(e){this._controlValueAccessorChangeFn=e}registerOnTouched(e){this._onTouched=e}setDisabledState(e){this.disabled=e}validate(e){return this.required&&e.value!==!0?{required:!0}:null}registerOnValidatorChange(e){this._validatorChangeFn=e}_transitionCheckState(e){let t=this._currentCheckState,r=this._getAnimationTargetElement();if(!(t===e||!r)&&(this._currentAnimationClass&&r.classList.remove(this._currentAnimationClass),this._currentAnimationClass=this._getAnimationClassForCheckStateTransition(t,e),this._currentCheckState=e,this._currentAnimationClass.length>0)){r.classList.add(this._currentAnimationClass);let o=this._currentAnimationClass;this._ngZone.runOutsideAngular(()=>{setTimeout(()=>{r.classList.remove(o)},1e3)})}}_emitChangeEvent(){this._controlValueAccessorChangeFn(this.checked),this.change.emit(this._createChangeEvent(this.checked)),this._inputElement&&(this._inputElement.nativeElement.checked=this.checked)}toggle(){this.checked=!this.checked,this._controlValueAccessorChangeFn(this.checked)}_handleInputClick(){let e=this._options?.clickAction;!this.disabled&&e!==`noop`?(this.indeterminate&&e!==`check`&&Promise.resolve().then(()=>{this._indeterminate.set(!1),this.indeterminateChange.emit(!1)}),this._checked=!this._checked,this._transitionCheckState(this._checked?Oe.Checked:Oe.Unchecked),this._emitChangeEvent()):(this.disabled&&this.disabledInteractive||!this.disabled&&e===`noop`)&&(this._inputElement.nativeElement.checked=this.checked,this._inputElement.nativeElement.indeterminate=this.indeterminate)}_onInteractionEvent(e){e.stopPropagation()}_onBlur(){Promise.resolve().then(()=>{this._onTouched(),this._changeDetectorRef.markForCheck()})}_getAnimationClassForCheckStateTransition(e,t){if(this._animationsDisabled)return``;switch(e){case Oe.Init:if(t===Oe.Checked)return this._animationClasses.uncheckedToChecked;if(t==Oe.Indeterminate)return this._checked?this._animationClasses.checkedToIndeterminate:this._animationClasses.uncheckedToIndeterminate;break;case Oe.Unchecked:return t===Oe.Checked?this._animationClasses.uncheckedToChecked:this._animationClasses.uncheckedToIndeterminate;case Oe.Checked:return t===Oe.Unchecked?this._animationClasses.checkedToUnchecked:this._animationClasses.checkedToIndeterminate;case Oe.Indeterminate:return t===Oe.Checked?this._animationClasses.indeterminateToChecked:this._animationClasses.indeterminateToUnchecked}return``}_syncIndeterminate(e){let t=this._inputElement;t&&(t.nativeElement.indeterminate=e)}_onInputClick(){this._handleInputClick()}_preventBubblingFromLabel(e){e.target&&this._inputElement&&e.target!==this._inputElement.nativeElement&&e.stopPropagation()}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`input`];return LI({type:n,selectors:[[`mat-checkbox`]],viewQuery:function(o,a){if(o&1&&lh$1(e,5),o&2){let s;SD(s=xD())&&(a._inputElement=s.first)}},hostAttrs:[1,`mat-mdc-checkbox`],hostVars:16,hostBindings:function(o,a){o&2&&(rh$1(`id`,a.id),Kp(`tabindex`,null)(`aria-label`,null)(`aria-labelledby`,null),zD(a.color?`mat-`+a.color:`mat-accent`),yh$1(`_mat-animation-noopable`,a._animationsDisabled)(`mdc-checkbox--disabled`,a.disabled)(`mat-mdc-checkbox-disabled`,a.disabled)(`mat-mdc-checkbox-checked`,a.checked)(`mat-mdc-checkbox-disabled-interactive`,a.disabledInteractive))},inputs:{ariaLabel:[0,`aria-label`,`ariaLabel`],ariaLabelledby:[0,`aria-labelledby`,`ariaLabelledby`],ariaDescribedby:[0,`aria-describedby`,`ariaDescribedby`],ariaExpanded:[2,`aria-expanded`,`ariaExpanded`,T0],ariaControls:[0,`aria-controls`,`ariaControls`],ariaOwns:[0,`aria-owns`,`ariaOwns`],id:`id`,required:[2,`required`,`required`,T0],labelPosition:`labelPosition`,name:`name`,value:`value`,disableRipple:[2,`disableRipple`,`disableRipple`,T0],tabIndex:[2,`tabIndex`,`tabIndex`,r=>r==null?void 0:C0(r)],color:`color`,disabledInteractive:[2,`disabledInteractive`,`disabledInteractive`,T0],checked:[2,`checked`,`checked`,T0],disabled:[2,`disabled`,`disabled`,T0],indeterminate:[2,`indeterminate`,`indeterminate`,T0]},outputs:{change:`change`,indeterminateChange:`indeterminateChange`},exportAs:[`matCheckbox`],features:[hw([{provide:Bt,useExisting:Io$1(()=>n),multi:!0},{provide:at,useExisting:n,multi:!0}]),iy],ngContentSelectors:[`*`],decls:15,vars:23,consts:[[`checkbox`,``],[`input`,``],[`label`,``],[`mat-internal-form-field`,``,3,`click`,`labelPosition`,`for`],[1,`mdc-checkbox`],[`aria-hidden`,`true`,1,`mat-mdc-checkbox-touch-target`],[`type`,`checkbox`,1,`mdc-checkbox__native-control`,3,`blur`,`click`,`change`,`checked`,`indeterminate`,`disabled`,`id`,`required`,`tabIndex`],[`aria-hidden`,`true`,1,`mdc-checkbox__ripple`],[`aria-hidden`,`true`,1,`mdc-checkbox__background`],[`focusable`,`false`,`viewBox`,`0 0 24 24`,1,`mdc-checkbox__checkmark`],[`fill`,`none`,`d`,`M1.73,12.91 8.1,19.28 22.79,4.59`,1,`mdc-checkbox__checkmark-path`],[1,`mdc-checkbox__mixedmark`],[`mat-ripple`,``,`aria-hidden`,`true`,1,`mat-mdc-checkbox-ripple`,`mat-focus-indicator`,3,`matRippleTrigger`,`matRippleDisabled`,`matRippleCentered`],[1,`mat-internal-form-field-label`,`mdc-label`]],template:function(o,a){if(o&1&&(_D(),yi(0,`label`,3),ih$1(`click`,function(c){return a._preventBubblingFromLabel(c)}),yi(1,`span`,4,0),Xp$1(3,`span`,5),yi(4,`input`,6,1),ih$1(`blur`,function(){return a._onBlur()})(`click`,function(){return a._onInputClick()})(`change`,function(c){return a._onInteractionEvent(c)}),Fc$1(),Xp$1(6,`span`,7),yi(7,`span`,8),Bu(),yi(8,`svg`,9),Xp$1(9,`path`,10),Fc$1(),$u(),Xp$1(10,`span`,11),Fc$1(),Xp$1(11,`span`,12),Fc$1(),yi(12,`span`,13,2),ND(14),Fc$1()()),o&2){let s=RD(2);Jp$1(`labelPosition`,a.labelPosition)(`for`,a.inputId),sE(4),yh$1(`mdc-checkbox--selected`,a.checked),Jp$1(`checked`,a.checked)(`indeterminate`,a.indeterminate)(`disabled`,a.disabled&&!a.disabledInteractive)(`id`,a.inputId)(`required`,a.required)(`tabIndex`,a.disabled&&!a.disabledInteractive?-1:a.tabIndex),Kp(`aria-label`,a.ariaLabel||null)(`aria-labelledby`,a.ariaLabelledby)(`aria-describedby`,a.ariaDescribedby)(`aria-checked`,a.indeterminate?`mixed`:null)(`aria-controls`,a.ariaControls)(`aria-disabled`,a.disabled&&a.disabledInteractive?!0:null)(`aria-expanded`,a.ariaExpanded)(`aria-owns`,a.ariaOwns)(`name`,a.name)(`value`,a.value),sE(7),Jp$1(`matRippleTrigger`,s)(`matRippleDisabled`,a.disableRipple||a.disabled)(`matRippleCentered`,!0)}},dependencies:[qn,qd],styles:[`.mdc-checkbox {
  display: inline-block;
  position: relative;
  flex: 0 0 18px;
  box-sizing: content-box;
  width: 18px;
  height: 18px;
  line-height: 0;
  white-space: nowrap;
  cursor: pointer;
  vertical-align: bottom;
  padding: calc((var(--%NS%mat-checkbox-state-layer-size, 40px) - 18px) / 2);
  margin: calc((var(--%NS%mat-checkbox-state-layer-size, 40px) - var(--%NS%mat-checkbox-state-layer-size, 40px)) / 2);
}
.mdc-checkbox:hover > .mdc-checkbox__ripple {
  opacity: var(--%NS%mat-checkbox-unselected-hover-state-layer-opacity, var(--%NS%mat-sys-hover-state-layer-opacity));
  background-color: var(--%NS%mat-checkbox-unselected-hover-state-layer-color, var(--%NS%mat-sys-on-surface));
}
.mdc-checkbox:hover > .mat-mdc-checkbox-ripple > .mat-ripple-element {
  background-color: var(--%NS%mat-checkbox-unselected-hover-state-layer-color, var(--%NS%mat-sys-on-surface));
}
.mdc-checkbox .mdc-checkbox__native-control:focus + .mdc-checkbox__ripple {
  opacity: var(--%NS%mat-checkbox-unselected-focus-state-layer-opacity, var(--%NS%mat-sys-focus-state-layer-opacity));
  background-color: var(--%NS%mat-checkbox-unselected-focus-state-layer-color, var(--%NS%mat-sys-on-surface));
}
.mdc-checkbox .mdc-checkbox__native-control:focus ~ .mat-mdc-checkbox-ripple .mat-ripple-element {
  background-color: var(--%NS%mat-checkbox-unselected-focus-state-layer-color, var(--%NS%mat-sys-on-surface));
}
.mdc-checkbox:active > .mdc-checkbox__native-control + .mdc-checkbox__ripple {
  opacity: var(--%NS%mat-checkbox-unselected-pressed-state-layer-opacity, var(--%NS%mat-sys-pressed-state-layer-opacity));
  background-color: var(--%NS%mat-checkbox-unselected-pressed-state-layer-color, var(--%NS%mat-sys-primary));
}
.mdc-checkbox:active > .mdc-checkbox__native-control ~ .mat-mdc-checkbox-ripple .mat-ripple-element {
  background-color: var(--%NS%mat-checkbox-unselected-pressed-state-layer-color, var(--%NS%mat-sys-primary));
}
.mdc-checkbox:hover > .mdc-checkbox__native-control:checked + .mdc-checkbox__ripple {
  opacity: var(--%NS%mat-checkbox-selected-hover-state-layer-opacity, var(--%NS%mat-sys-hover-state-layer-opacity));
  background-color: var(--%NS%mat-checkbox-selected-hover-state-layer-color, var(--%NS%mat-sys-primary));
}
.mdc-checkbox:hover > .mdc-checkbox__native-control:checked ~ .mat-mdc-checkbox-ripple .mat-ripple-element {
  background-color: var(--%NS%mat-checkbox-selected-hover-state-layer-color, var(--%NS%mat-sys-primary));
}
.mdc-checkbox .mdc-checkbox__native-control:focus:checked + .mdc-checkbox__ripple {
  opacity: var(--%NS%mat-checkbox-selected-focus-state-layer-opacity, var(--%NS%mat-sys-focus-state-layer-opacity));
  background-color: var(--%NS%mat-checkbox-selected-focus-state-layer-color, var(--%NS%mat-sys-primary));
}
.mdc-checkbox .mdc-checkbox__native-control:focus:checked ~ .mat-mdc-checkbox-ripple .mat-ripple-element {
  background-color: var(--%NS%mat-checkbox-selected-focus-state-layer-color, var(--%NS%mat-sys-primary));
}
.mdc-checkbox:active > .mdc-checkbox__native-control:checked + .mdc-checkbox__ripple {
  opacity: var(--%NS%mat-checkbox-selected-pressed-state-layer-opacity, var(--%NS%mat-sys-pressed-state-layer-opacity));
  background-color: var(--%NS%mat-checkbox-selected-pressed-state-layer-color, var(--%NS%mat-sys-on-surface));
}
.mdc-checkbox:active > .mdc-checkbox__native-control:checked ~ .mat-mdc-checkbox-ripple .mat-ripple-element {
  background-color: var(--%NS%mat-checkbox-selected-pressed-state-layer-color, var(--%NS%mat-sys-on-surface));
}
.mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox .mdc-checkbox__native-control ~ .mat-mdc-checkbox-ripple .mat-ripple-element,
.mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox .mdc-checkbox__native-control + .mdc-checkbox__ripple {
  background-color: var(--%NS%mat-checkbox-unselected-hover-state-layer-color, var(--%NS%mat-sys-on-surface));
}
.mdc-checkbox .mdc-checkbox__native-control {
  position: absolute;
  margin: 0;
  padding: 0;
  opacity: 0;
  cursor: inherit;
  z-index: 1;
  width: var(--%NS%mat-checkbox-state-layer-size, 40px);
  height: var(--%NS%mat-checkbox-state-layer-size, 40px);
  top: calc((var(--%NS%mat-checkbox-state-layer-size, 40px) - var(--%NS%mat-checkbox-state-layer-size, 40px)) / 2);
  right: calc((var(--%NS%mat-checkbox-state-layer-size, 40px) - var(--%NS%mat-checkbox-state-layer-size, 40px)) / 2);
  left: calc((var(--%NS%mat-checkbox-state-layer-size, 40px) - var(--%NS%mat-checkbox-state-layer-size, 40px)) / 2);
}

.mdc-checkbox--disabled {
  cursor: default;
  pointer-events: none;
}

.mdc-checkbox__background {
  display: inline-flex;
  position: absolute;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: 18px;
  height: 18px;
  border: 2px solid currentColor;
  border-radius: 2px;
  background-color: transparent;
  pointer-events: none;
  will-change: background-color, border-color;
  transition: background-color 90ms cubic-bezier(0.4, 0, 0.6, 1), border-color 90ms cubic-bezier(0.4, 0, 0.6, 1);
  -webkit-print-color-adjust: exact;
  color-adjust: exact;
  border-color: var(--%NS%mat-checkbox-unselected-icon-color, var(--%NS%mat-sys-on-surface-variant));
  top: calc((var(--%NS%mat-checkbox-state-layer-size, 40px) - 18px) / 2);
  left: calc((var(--%NS%mat-checkbox-state-layer-size, 40px) - 18px) / 2);
}

.mdc-checkbox__native-control:enabled:checked ~ .mdc-checkbox__background,
.mdc-checkbox__native-control:enabled:indeterminate ~ .mdc-checkbox__background {
  border-color: var(--%NS%mat-checkbox-selected-icon-color, var(--%NS%mat-sys-primary));
  background-color: var(--%NS%mat-checkbox-selected-icon-color, var(--%NS%mat-sys-primary));
}

.mdc-checkbox--disabled .mdc-checkbox__background {
  border-color: var(--%NS%mat-checkbox-disabled-unselected-icon-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
@media (forced-colors: active) {
  .mdc-checkbox--disabled .mdc-checkbox__background {
    border-color: GrayText;
  }
}

.mdc-checkbox__native-control:disabled:checked ~ .mdc-checkbox__background,
.mdc-checkbox__native-control:disabled:indeterminate ~ .mdc-checkbox__background {
  background-color: var(--%NS%mat-checkbox-disabled-selected-icon-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
  border-color: transparent;
}
@media (forced-colors: active) {
  .mdc-checkbox__native-control:disabled:checked ~ .mdc-checkbox__background,
  .mdc-checkbox__native-control:disabled:indeterminate ~ .mdc-checkbox__background {
    border-color: GrayText;
  }
}

.mdc-checkbox:hover > .mdc-checkbox__native-control:not(:checked) ~ .mdc-checkbox__background,
.mdc-checkbox:hover > .mdc-checkbox__native-control:not(:indeterminate) ~ .mdc-checkbox__background {
  border-color: var(--%NS%mat-checkbox-unselected-hover-icon-color, var(--%NS%mat-sys-on-surface));
  background-color: transparent;
}

.mdc-checkbox:hover > .mdc-checkbox__native-control:checked ~ .mdc-checkbox__background,
.mdc-checkbox:hover > .mdc-checkbox__native-control:indeterminate ~ .mdc-checkbox__background {
  border-color: var(--%NS%mat-checkbox-selected-hover-icon-color, var(--%NS%mat-sys-primary));
  background-color: var(--%NS%mat-checkbox-selected-hover-icon-color, var(--%NS%mat-sys-primary));
}

.mdc-checkbox__native-control:focus:focus:not(:checked) ~ .mdc-checkbox__background,
.mdc-checkbox__native-control:focus:focus:not(:indeterminate) ~ .mdc-checkbox__background {
  border-color: var(--%NS%mat-checkbox-unselected-focus-icon-color, var(--%NS%mat-sys-on-surface));
}

.mdc-checkbox__native-control:focus:focus:checked ~ .mdc-checkbox__background,
.mdc-checkbox__native-control:focus:focus:indeterminate ~ .mdc-checkbox__background {
  border-color: var(--%NS%mat-checkbox-selected-focus-icon-color, var(--%NS%mat-sys-primary));
  background-color: var(--%NS%mat-checkbox-selected-focus-icon-color, var(--%NS%mat-sys-primary));
}

.mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox:hover > .mdc-checkbox__native-control ~ .mdc-checkbox__background,
.mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox .mdc-checkbox__native-control:focus ~ .mdc-checkbox__background,
.mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox__background {
  border-color: var(--%NS%mat-checkbox-disabled-unselected-icon-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
@media (forced-colors: active) {
  .mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox:hover > .mdc-checkbox__native-control ~ .mdc-checkbox__background,
  .mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox .mdc-checkbox__native-control:focus ~ .mdc-checkbox__background,
  .mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox__background {
    border-color: GrayText;
  }
}
.mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox__native-control:checked ~ .mdc-checkbox__background,
.mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox__native-control:indeterminate ~ .mdc-checkbox__background {
  background-color: var(--%NS%mat-checkbox-disabled-selected-icon-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
  border-color: transparent;
}

.mdc-checkbox__checkmark {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  width: 100%;
  opacity: 0;
  transition: opacity 180ms cubic-bezier(0.4, 0, 0.6, 1);
  color: var(--%NS%mat-checkbox-selected-checkmark-color, var(--%NS%mat-sys-on-primary));
}
@media (forced-colors: active) {
  .mdc-checkbox__checkmark {
    color: CanvasText;
  }
}

.mdc-checkbox--disabled .mdc-checkbox__checkmark, .mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox__checkmark {
  color: var(--%NS%mat-checkbox-disabled-selected-checkmark-color, var(--%NS%mat-sys-surface));
}
@media (forced-colors: active) {
  .mdc-checkbox--disabled .mdc-checkbox__checkmark, .mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox__checkmark {
    color: GrayText;
  }
}

.mdc-checkbox__checkmark-path {
  transition: stroke-dashoffset 180ms cubic-bezier(0.4, 0, 0.6, 1);
  stroke: currentColor;
  stroke-width: 3.12px;
  stroke-dashoffset: 29.7833385;
  stroke-dasharray: 29.7833385;
}

.mdc-checkbox__mixedmark {
  width: 100%;
  height: 0;
  transform: scaleX(0) rotate(0deg);
  border-width: 1px;
  border-style: solid;
  opacity: 0;
  transition: opacity 90ms cubic-bezier(0.4, 0, 0.6, 1), transform 90ms cubic-bezier(0.4, 0, 0.6, 1);
  border-color: var(--%NS%mat-checkbox-selected-checkmark-color, var(--%NS%mat-sys-on-primary));
}
@media (forced-colors: active) {
  .mdc-checkbox__mixedmark {
    margin: 0 1px;
  }
}

.mdc-checkbox--disabled .mdc-checkbox__mixedmark, .mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox__mixedmark {
  border-color: var(--%NS%mat-checkbox-disabled-selected-checkmark-color, var(--%NS%mat-sys-surface));
}
@media (forced-colors: active) {
  .mdc-checkbox--disabled .mdc-checkbox__mixedmark, .mdc-checkbox--disabled.mat-mdc-checkbox-disabled-interactive .mdc-checkbox__mixedmark {
    border-color: GrayText;
  }
}

.mdc-checkbox--anim-unchecked-checked .mdc-checkbox__background,
.mdc-checkbox--anim-unchecked-indeterminate .mdc-checkbox__background,
.mdc-checkbox--anim-checked-unchecked .mdc-checkbox__background,
.mdc-checkbox--anim-indeterminate-unchecked .mdc-checkbox__background {
  animation-duration: 180ms;
  animation-timing-function: linear;
}

.mdc-checkbox--anim-unchecked-checked .mdc-checkbox__checkmark-path {
  animation: mdc-checkbox-unchecked-checked-checkmark-path 180ms linear;
  transition: none;
}

.mdc-checkbox--anim-unchecked-indeterminate .mdc-checkbox__mixedmark {
  animation: mdc-checkbox-unchecked-indeterminate-mixedmark 90ms linear;
  transition: none;
}

.mdc-checkbox--anim-checked-unchecked .mdc-checkbox__checkmark-path {
  animation: mdc-checkbox-checked-unchecked-checkmark-path 90ms linear;
  transition: none;
}

.mdc-checkbox--anim-checked-indeterminate .mdc-checkbox__checkmark {
  animation: mdc-checkbox-checked-indeterminate-checkmark 90ms linear;
  transition: none;
}
.mdc-checkbox--anim-checked-indeterminate .mdc-checkbox__mixedmark {
  animation: mdc-checkbox-checked-indeterminate-mixedmark 90ms linear;
  transition: none;
}

.mdc-checkbox--anim-indeterminate-checked .mdc-checkbox__checkmark {
  animation: mdc-checkbox-indeterminate-checked-checkmark 500ms linear;
  transition: none;
}
.mdc-checkbox--anim-indeterminate-checked .mdc-checkbox__mixedmark {
  animation: mdc-checkbox-indeterminate-checked-mixedmark 500ms linear;
  transition: none;
}

.mdc-checkbox--anim-indeterminate-unchecked .mdc-checkbox__mixedmark {
  animation: mdc-checkbox-indeterminate-unchecked-mixedmark 300ms linear;
  transition: none;
}

.mdc-checkbox__native-control:checked ~ .mdc-checkbox__background,
.mdc-checkbox__native-control:indeterminate ~ .mdc-checkbox__background {
  transition: border-color 90ms cubic-bezier(0, 0, 0.2, 1), background-color 90ms cubic-bezier(0, 0, 0.2, 1);
}
.mdc-checkbox__native-control:checked ~ .mdc-checkbox__background > .mdc-checkbox__checkmark > .mdc-checkbox__checkmark-path,
.mdc-checkbox__native-control:indeterminate ~ .mdc-checkbox__background > .mdc-checkbox__checkmark > .mdc-checkbox__checkmark-path {
  stroke-dashoffset: 0;
}

.mdc-checkbox__native-control:checked ~ .mdc-checkbox__background > .mdc-checkbox__checkmark {
  transition: opacity 180ms cubic-bezier(0, 0, 0.2, 1), transform 180ms cubic-bezier(0, 0, 0.2, 1);
  opacity: 1;
}
.mdc-checkbox__native-control:checked ~ .mdc-checkbox__background > .mdc-checkbox__mixedmark {
  transform: scaleX(1) rotate(-45deg);
}

.mdc-checkbox__native-control:indeterminate ~ .mdc-checkbox__background > .mdc-checkbox__checkmark {
  transform: rotate(45deg);
  opacity: 0;
  transition: opacity 90ms cubic-bezier(0.4, 0, 0.6, 1), transform 90ms cubic-bezier(0.4, 0, 0.6, 1);
}
.mdc-checkbox__native-control:indeterminate ~ .mdc-checkbox__background > .mdc-checkbox__mixedmark {
  transform: scaleX(1) rotate(0deg);
  opacity: 1;
}

@keyframes mdc-checkbox-unchecked-checked-checkmark-path {
  0%, 50% {
    stroke-dashoffset: 29.7833385;
  }
  50% {
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
  100% {
    stroke-dashoffset: 0;
  }
}
@keyframes mdc-checkbox-unchecked-indeterminate-mixedmark {
  0%, 68.2% {
    transform: scaleX(0);
  }
  68.2% {
    animation-timing-function: cubic-bezier(0, 0, 0, 1);
  }
  100% {
    transform: scaleX(1);
  }
}
@keyframes mdc-checkbox-checked-unchecked-checkmark-path {
  from {
    animation-timing-function: cubic-bezier(0.4, 0, 1, 1);
    opacity: 1;
    stroke-dashoffset: 0;
  }
  to {
    opacity: 0;
    stroke-dashoffset: -29.7833385;
  }
}
@keyframes mdc-checkbox-checked-indeterminate-checkmark {
  from {
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
    transform: rotate(0deg);
    opacity: 1;
  }
  to {
    transform: rotate(45deg);
    opacity: 0;
  }
}
@keyframes mdc-checkbox-indeterminate-checked-checkmark {
  from {
    animation-timing-function: cubic-bezier(0.14, 0, 0, 1);
    transform: rotate(45deg);
    opacity: 0;
  }
  to {
    transform: rotate(360deg);
    opacity: 1;
  }
}
@keyframes mdc-checkbox-checked-indeterminate-mixedmark {
  from {
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
    transform: rotate(-45deg);
    opacity: 0;
  }
  to {
    transform: rotate(0deg);
    opacity: 1;
  }
}
@keyframes mdc-checkbox-indeterminate-checked-mixedmark {
  from {
    animation-timing-function: cubic-bezier(0.14, 0, 0, 1);
    transform: rotate(0deg);
    opacity: 1;
  }
  to {
    transform: rotate(315deg);
    opacity: 0;
  }
}
@keyframes mdc-checkbox-indeterminate-unchecked-mixedmark {
  0% {
    animation-timing-function: linear;
    transform: scaleX(1);
    opacity: 1;
  }
  32.8%, 100% {
    transform: scaleX(0);
    opacity: 0;
  }
}
.mat-mdc-checkbox {
  display: inline-block;
  position: relative;
  -webkit-tap-highlight-color: transparent;
}
.mat-mdc-checkbox._mat-animation-noopable > .mat-internal-form-field > .mdc-checkbox > .mat-mdc-checkbox-touch-target,
.mat-mdc-checkbox._mat-animation-noopable > .mat-internal-form-field > .mdc-checkbox > .mdc-checkbox__native-control,
.mat-mdc-checkbox._mat-animation-noopable > .mat-internal-form-field > .mdc-checkbox > .mdc-checkbox__ripple,
.mat-mdc-checkbox._mat-animation-noopable > .mat-internal-form-field > .mdc-checkbox > .mat-mdc-checkbox-ripple::before,
.mat-mdc-checkbox._mat-animation-noopable > .mat-internal-form-field > .mdc-checkbox > .mdc-checkbox__background,
.mat-mdc-checkbox._mat-animation-noopable > .mat-internal-form-field > .mdc-checkbox > .mdc-checkbox__background > .mdc-checkbox__checkmark,
.mat-mdc-checkbox._mat-animation-noopable > .mat-internal-form-field > .mdc-checkbox > .mdc-checkbox__background > .mdc-checkbox__checkmark > .mdc-checkbox__checkmark-path,
.mat-mdc-checkbox._mat-animation-noopable > .mat-internal-form-field > .mdc-checkbox > .mdc-checkbox__background > .mdc-checkbox__mixedmark {
  transition: none !important;
  animation: none !important;
}
.mat-mdc-checkbox label {
  cursor: pointer;
}
.mat-mdc-checkbox .mat-internal-form-field {
  color: var(--%NS%mat-checkbox-label-text-color, var(--%NS%mat-sys-on-surface));
  font-family: var(--%NS%mat-checkbox-label-text-font, var(--%NS%mat-sys-body-medium-font));
  line-height: var(--%NS%mat-checkbox-label-text-line-height, var(--%NS%mat-sys-body-medium-line-height));
  font-size: var(--%NS%mat-checkbox-label-text-size, var(--%NS%mat-sys-body-medium-size));
  letter-spacing: var(--%NS%mat-checkbox-label-text-tracking, var(--%NS%mat-sys-body-medium-tracking));
  font-weight: var(--%NS%mat-checkbox-label-text-weight, var(--%NS%mat-sys-body-medium-weight));
}
.mat-mdc-checkbox.mat-mdc-checkbox-disabled.mat-mdc-checkbox-disabled-interactive {
  pointer-events: auto;
}
.mat-mdc-checkbox.mat-mdc-checkbox-disabled.mat-mdc-checkbox-disabled-interactive input {
  cursor: default;
}
.mat-mdc-checkbox.mat-mdc-checkbox-disabled label {
  cursor: default;
}
.mat-mdc-checkbox.mat-mdc-checkbox-disabled .mat-internal-form-field-label {
  color: var(--%NS%mat-checkbox-disabled-label-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
@media (forced-colors: active) {
  .mat-mdc-checkbox.mat-mdc-checkbox-disabled .mat-internal-form-field-label {
    color: GrayText;
  }
}
.mat-mdc-checkbox .mat-internal-form-field-label:empty {
  display: none;
}
.mat-mdc-checkbox .mdc-checkbox__ripple {
  opacity: 0;
}

.mat-mdc-checkbox .mat-mdc-checkbox-ripple,
.mdc-checkbox__ripple {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}
.mat-mdc-checkbox .mat-mdc-checkbox-ripple:not(:empty),
.mdc-checkbox__ripple:not(:empty) {
  transform: translateZ(0);
}

.mat-mdc-checkbox-ripple .mat-ripple-element {
  opacity: 0.1;
}

.mat-mdc-checkbox-touch-target {
  position: absolute;
  top: 50%;
  left: 50%;
  height: var(--%NS%mat-checkbox-touch-target-size, 48px);
  width: var(--%NS%mat-checkbox-touch-target-size, 48px);
  transform: translate(-50%, -50%);
  display: var(--%NS%mat-checkbox-touch-target-display, block);
}

.mat-mdc-checkbox .mat-mdc-checkbox-ripple::before {
  border-radius: 50%;
}

.mdc-checkbox__native-control:focus-visible ~ .mat-focus-indicator::before {
  content: "";
}
`],encapsulation:2})})()}return n})();var yk=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[dr,te]})}return n})();var Op=20;var Fp=new S(`mat-tooltip-scroll-strategy`,{providedIn:`root`,factory:()=>{let n=I(le);return()=>Ft(n,{scrollThrottle:Op})}});var Pp=new S(`mat-tooltip-default-options`,{providedIn:`root`,factory:()=>({showDelay:0,hideDelay:0,touchendHideDelay:1500})});var Zd=`tooltip-panel`;var Lp={passive:!0};var Vp=8;var Bp=8;var zp=24;var jp=200;var hs=(()=>{class n{_elementRef=I(Dr);_ngZone=I(z);_platform=I(J);_ariaDescriber=I(kc);_focusMonitor=I(ft);_dir=I(Ne);_injector=I(le);_viewContainerRef=I(xi$1);_mediaMatcher=I(Hn);_document=I(Bo);_renderer=I(La$1);_animationsDisabled=ue();_defaultOptions=I(Pp,{optional:!0});_overlayRef=null;_tooltipInstance=null;_overlayPanelClass;_portal;_position=`below`;_positionAtOrigin=!1;_disabled=!1;_tooltipClass;_viewInitialized=!1;_pointerExitEventsInitialized=!1;_tooltipComponent=Qd;_viewportMargin=8;_currentPosition;_cssClassPrefix=`mat-mdc`;_ariaDescriptionPending=!1;_dirSubscribed=!1;get position(){return this._position}set position(e){e!==this._position&&(this._position=e,this._overlayRef&&(this._updatePosition(this._overlayRef),this._tooltipInstance?.show(0),this._overlayRef.updatePosition()))}get positionAtOrigin(){return this._positionAtOrigin}set positionAtOrigin(e){this._positionAtOrigin=Pt(e),this._detach(),this._overlayRef=null}get disabled(){return this._disabled}set disabled(e){let t=Pt(e);this._disabled!==t&&(this._disabled=t,t?this.hide(0):this._setupPointerEnterEventsIfNeeded(),this._syncAriaDescription(this.message))}get showDelay(){return this._showDelay}set showDelay(e){this._showDelay=dt(e)}_showDelay;get hideDelay(){return this._hideDelay}set hideDelay(e){this._hideDelay=dt(e),this._tooltipInstance&&(this._tooltipInstance._mouseLeaveHideDelay=this._hideDelay)}_hideDelay;touchGestures=`auto`;get message(){return this._message}set message(e){let t=this._message;this._message=e!=null?String(e).trim():``,!this._message&&this._isTooltipVisible()?this.hide(0):(this._setupPointerEnterEventsIfNeeded(),this._updateTooltipMessage()),this._syncAriaDescription(t)}_message=``;get tooltipClass(){return this._tooltipClass}set tooltipClass(e){this._tooltipClass=e,this._tooltipInstance&&this._setTooltipClass(this._tooltipClass)}_eventCleanups=[];_touchstartTimeout=null;_destroyed=new te$1;_isDestroyed=!1;constructor(){let e=this._defaultOptions;e&&(this._showDelay=e.showDelay,this._hideDelay=e.hideDelay,e.position&&(this.position=e.position),e.positionAtOrigin&&(this.positionAtOrigin=e.positionAtOrigin),e.touchGestures&&(this.touchGestures=e.touchGestures),e.tooltipClass&&(this.tooltipClass=e.tooltipClass)),this._viewportMargin=Vp}ngAfterViewInit(){this._viewInitialized=!0,this._setupPointerEnterEventsIfNeeded(),this._focusMonitor.monitor(this._elementRef).pipe(Rl$1(this._destroyed)).subscribe(e=>{e?e===`keyboard`&&this._ngZone.run(()=>this.show()):this._ngZone.run(()=>this.hide(0))})}ngOnDestroy(){let e=this._elementRef.nativeElement;this._touchstartTimeout&&clearTimeout(this._touchstartTimeout),this._overlayRef&&(this._overlayRef.dispose(),this._tooltipInstance=null),this._eventCleanups.forEach(t=>t()),this._eventCleanups.length=0,this._destroyed.next(),this._destroyed.complete(),this._isDestroyed=!0,this._ariaDescriber.removeDescription(e,this.message,`tooltip`),this._focusMonitor.stopMonitoring(e)}show(e=this.showDelay,t){if(this.disabled||!this.message||this._isTooltipVisible()){this._tooltipInstance?._cancelPendingAnimations();return}let r=this._createOverlay(t);this._detach(),this._portal=this._portal||new ut(this._tooltipComponent,this._viewContainerRef);let o=this._tooltipInstance=r.attach(this._portal).instance;o._triggerElement=this._elementRef.nativeElement,o._mouseLeaveHideDelay=this._hideDelay,o.afterHidden().pipe(Rl$1(this._destroyed)).subscribe(()=>this._detach()),this._setTooltipClass(this._tooltipClass),this._updateTooltipMessage(),o.show(e)}hide(e=this.hideDelay){let t=this._tooltipInstance;t&&(t.isVisible()?t.hide(e):(t._cancelPendingAnimations(),this._detach()))}toggle(e){this._isTooltipVisible()?this.hide():this.show(void 0,e)}_isTooltipVisible(){return!!this._tooltipInstance&&this._tooltipInstance.isVisible()}_createOverlay(e){if(this._overlayRef){let a=this._overlayRef.getConfig().positionStrategy;if((!this.positionAtOrigin||!e)&&a._origin instanceof Dr)return this._overlayRef;this._detach()}let t=this._injector.get(Gt).getAncestorScrollContainers(this._elementRef),r=`${this._cssClassPrefix}-${Zd}`,o=pn(this._injector,this.positionAtOrigin?e||this._elementRef:this._elementRef).withTransformOriginOn(`.${this._cssClassPrefix}-tooltip`).withFlexibleDimensions(!1).withViewportMargin(this._viewportMargin).withScrollableContainers(t).withPopoverLocation(`global`);return o.positionChanges.pipe(Rl$1(this._destroyed)).subscribe(a=>{this._updateCurrentPositionClass(a.connectionPair),this._tooltipInstance&&a.scrollableViewProperties.isOverlayClipped&&this._tooltipInstance.isVisible()&&this._ngZone.run(()=>this.hide(0))}),this._overlayRef=pt(this._injector,{direction:this._dir,positionStrategy:o,panelClass:this._overlayPanelClass?[...this._overlayPanelClass,r]:r,scrollStrategy:this._injector.get(Fp)(),disableAnimations:this._animationsDisabled,eventPredicate:this._overlayEventPredicate}),this._updatePosition(this._overlayRef),this._overlayRef.detachments().pipe(Rl$1(this._destroyed)).subscribe(()=>this._detach()),this._overlayRef.outsidePointerEvents().pipe(Rl$1(this._destroyed)).subscribe(()=>this._tooltipInstance?._handleBodyInteraction()),this._overlayRef.keydownEvents().pipe(Rl$1(this._destroyed)).subscribe(a=>{a.preventDefault(),a.stopPropagation(),this._ngZone.run(()=>this.hide(0))}),this._defaultOptions?.disableTooltipInteractivity&&this._overlayRef.addPanelClass(`${this._cssClassPrefix}-tooltip-panel-non-interactive`),this._dirSubscribed||(this._dirSubscribed=!0,this._dir.change.pipe(Rl$1(this._destroyed)).subscribe(()=>{this._overlayRef&&this._updatePosition(this._overlayRef)})),this._overlayRef}_detach(){this._overlayRef&&this._overlayRef.hasAttached()&&this._overlayRef.detach(),this._tooltipInstance=null}_updatePosition(e){let t=e.getConfig().positionStrategy,r=this._getOrigin(),o=this._getOverlayPosition();t.withPositions([this._addOffset($($({},r.main),o.main)),this._addOffset($($({},r.fallback),o.fallback))])}_addOffset(e){let t=Bp,r=!this._dir||this._dir.value==`ltr`;return e.originY===`top`?e.offsetY=-t:e.originY===`bottom`?e.offsetY=t:e.originX===`start`?e.offsetX=r?-t:t:e.originX===`end`&&(e.offsetX=r?t:-t),e}_getOrigin(){let e=!this._dir||this._dir.value==`ltr`,t=this.position,r;t==`above`||t==`below`?r={originX:`center`,originY:t==`above`?`top`:`bottom`}:t==`before`||t==`left`&&e||t==`right`&&!e?r={originX:`start`,originY:`center`}:(t==`after`||t==`right`&&e||t==`left`&&!e)&&(r={originX:`end`,originY:`center`});let{x:o,y:a}=this._invertPosition(r.originX,r.originY);return{main:r,fallback:{originX:o,originY:a}}}_getOverlayPosition(){let e=!this._dir||this._dir.value==`ltr`,t=this.position,r;t==`above`?r={overlayX:`center`,overlayY:`bottom`}:t==`below`?r={overlayX:`center`,overlayY:`top`}:t==`before`||t==`left`&&e||t==`right`&&!e?r={overlayX:`end`,overlayY:`center`}:(t==`after`||t==`right`&&e||t==`left`&&!e)&&(r={overlayX:`start`,overlayY:`center`});let{x:o,y:a}=this._invertPosition(r.overlayX,r.overlayY);return{main:r,fallback:{overlayX:o,overlayY:a}}}_updateTooltipMessage(){this._tooltipInstance&&(this._tooltipInstance.message=this.message,this._tooltipInstance._markForCheck(),Hv(()=>{this._tooltipInstance&&this._overlayRef.updatePosition()},{injector:this._injector}))}_setTooltipClass(e){this._tooltipInstance&&(this._tooltipInstance.tooltipClass=e instanceof Set?Array.from(e):e,this._tooltipInstance._markForCheck())}_invertPosition(e,t){return this.position===`above`||this.position===`below`?t===`top`?t=`bottom`:t===`bottom`&&(t=`top`):e===`end`?e=`start`:e===`start`&&(e=`end`),{x:e,y:t}}_updateCurrentPositionClass(e){let{overlayY:t,originX:r,originY:o}=e,a;if(t===`center`?this._dir&&this._dir.value===`rtl`?a=r===`end`?`left`:`right`:a=r===`start`?`left`:`right`:a=t===`bottom`&&o===`top`?`above`:`below`,a!==this._currentPosition){let s=this._overlayRef;if(s){let c=`${this._cssClassPrefix}-${Zd}-`;s.removePanelClass(c+this._currentPosition),s.addPanelClass(c+a)}this._currentPosition=a}}_setupPointerEnterEventsIfNeeded(){this._disabled||!this.message||!this._viewInitialized||this._eventCleanups.length||(this._isTouchPlatform()?this.touchGestures!==`off`&&(this._disableNativeGesturesIfNecessary(),this._addListener(`touchstart`,e=>{let t=e.targetTouches?.[0],r=t?{x:t.clientX,y:t.clientY}:void 0;this._setupPointerExitEventsIfNeeded(),this._touchstartTimeout&&clearTimeout(this._touchstartTimeout);let o=500;this._touchstartTimeout=setTimeout(()=>{this._touchstartTimeout=null,this.show(void 0,r)},this._defaultOptions?.touchLongPressShowDelay??o)})):this._addListener(`mouseenter`,e=>{this._setupPointerExitEventsIfNeeded();let t;e.x!==void 0&&e.y!==void 0&&(t=e),this.show(void 0,t)}))}_setupPointerExitEventsIfNeeded(){if(!this._pointerExitEventsInitialized){if(this._pointerExitEventsInitialized=!0,!this._isTouchPlatform())this._addListener(`mouseleave`,e=>{let t=e.relatedTarget;(!t||!this._overlayRef?.overlayElement.contains(t))&&this.hide()}),this._addListener(`wheel`,e=>{if(this._isTooltipVisible()){let t=this._document.elementFromPoint(e.clientX,e.clientY),r=this._elementRef.nativeElement;t!==r&&!r.contains(t)&&this.hide()}});else if(this.touchGestures!==`off`){this._disableNativeGesturesIfNecessary();let e=()=>{this._touchstartTimeout&&clearTimeout(this._touchstartTimeout),this.hide(this._defaultOptions?.touchendHideDelay)};this._addListener(`touchend`,e),this._addListener(`touchcancel`,e)}}}_addListener(e,t){this._eventCleanups.push(this._renderer.listen(this._elementRef.nativeElement,e,t,Lp))}_isTouchPlatform(){let e=this._defaultOptions?.detectHoverCapability;return typeof e==`function`?!e():this._platform.IOS||this._platform.ANDROID?!0:this._platform.isBrowser?!!e&&this._mediaMatcher.matchMedia(`(any-hover: none)`).matches:!1}_disableNativeGesturesIfNecessary(){let e=this.touchGestures;if(e!==`off`){let t=this._elementRef.nativeElement,r=t.style;(e===`on`||t.nodeName!==`INPUT`&&t.nodeName!==`TEXTAREA`)&&(r.userSelect=r.msUserSelect=r.webkitUserSelect=r.MozUserSelect=`none`),(e===`on`||!t.draggable)&&(r.webkitUserDrag=`none`),r.touchAction=`none`,r.webkitTapHighlightColor=`transparent`}}_syncAriaDescription(e){this._ariaDescriptionPending||(this._ariaDescriptionPending=!0,this._ariaDescriber.removeDescription(this._elementRef.nativeElement,e,`tooltip`),this._isDestroyed||Hv({write:()=>{this._ariaDescriptionPending=!1,this.message&&!this.disabled&&this._ariaDescriber.describe(this._elementRef.nativeElement,this.message,`tooltip`)}},{injector:this._injector}))}_overlayEventPredicate=e=>e.type===`keydown`?this._isTooltipVisible()&&e.keyCode===27&&!Me(e):!0;static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`matTooltip`,``]],hostAttrs:[1,`mat-mdc-tooltip-trigger`],hostVars:2,hostBindings:function(t,r){t&2&&yh$1(`mat-mdc-tooltip-disabled`,r.disabled)},inputs:{position:[0,`matTooltipPosition`,`position`],positionAtOrigin:[0,`matTooltipPositionAtOrigin`,`positionAtOrigin`],disabled:[0,`matTooltipDisabled`,`disabled`],showDelay:[0,`matTooltipShowDelay`,`showDelay`],hideDelay:[0,`matTooltipHideDelay`,`hideDelay`],touchGestures:[0,`matTooltipTouchGestures`,`touchGestures`],message:[0,`matTooltip`,`message`],tooltipClass:[0,`matTooltipClass`,`tooltipClass`]},exportAs:[`matTooltip`]})}return n})();var Qd=(()=>{class n{_changeDetectorRef=I(w0);_elementRef=I(Dr);_isMultiline=!1;message;tooltipClass;_showTimeoutId;_hideTimeoutId;_triggerElement;_mouseLeaveHideDelay;_animationsDisabled=ue();_tooltip;_closeOnInteraction=!1;_isVisible=!1;_onHide=new te$1;_showAnimation=`mat-mdc-tooltip-show`;_hideAnimation=`mat-mdc-tooltip-hide`;show(e){this._hideTimeoutId!=null&&clearTimeout(this._hideTimeoutId),this._showTimeoutId=setTimeout(()=>{this._toggleVisibility(!0),this._showTimeoutId=void 0},e)}hide(e){this._showTimeoutId!=null&&clearTimeout(this._showTimeoutId),this._hideTimeoutId=setTimeout(()=>{this._toggleVisibility(!1),this._hideTimeoutId=void 0},e)}afterHidden(){return this._onHide}isVisible(){return this._isVisible}ngOnDestroy(){this._cancelPendingAnimations(),this._onHide.complete(),this._triggerElement=null}_handleBodyInteraction(){this._closeOnInteraction&&this.hide(0)}_markForCheck(){this._changeDetectorRef.markForCheck()}_handleMouseLeave({relatedTarget:e}){(!e||!this._triggerElement.contains(e))&&(this.isVisible()?this.hide(this._mouseLeaveHideDelay):this._finalizeAnimation(!1))}_onShow(){this._isMultiline=this._isTooltipMultiline(),this._markForCheck()}_isTooltipMultiline(){let e=this._elementRef.nativeElement.getBoundingClientRect();return e.height>zp&&e.width>=jp}_handleAnimationEnd({animationName:e}){(e===this._showAnimation||e===this._hideAnimation)&&this._finalizeAnimation(e===this._showAnimation)}_cancelPendingAnimations(){this._showTimeoutId!=null&&clearTimeout(this._showTimeoutId),this._hideTimeoutId!=null&&clearTimeout(this._hideTimeoutId),this._showTimeoutId=this._hideTimeoutId=void 0}_finalizeAnimation(e){e?this._closeOnInteraction=!0:this.isVisible()||this._onHide.next()}_toggleVisibility(e){let t=this._tooltip.nativeElement,r=this._showAnimation,o=this._hideAnimation;if(t.classList.remove(e?o:r),t.classList.add(e?r:o),this._isVisible!==e&&(this._isVisible=e,this._changeDetectorRef.markForCheck()),e&&!this._animationsDisabled&&typeof getComputedStyle==`function`){let a=getComputedStyle(t);(a.getPropertyValue(`animation-duration`)===`0s`||a.getPropertyValue(`animation-name`)===`none`)&&(this._animationsDisabled=!0)}e&&this._onShow(),this._animationsDisabled&&(t.classList.add(`_mat-animation-noopable`),this._finalizeAnimation(e))}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`tooltip`];return LI({type:n,selectors:[[`mat-tooltip-component`]],viewQuery:function(r,o){if(r&1&&lh$1(e,7),r&2){let a;SD(a=xD())&&(o._tooltip=a.first)}},hostAttrs:[`aria-hidden`,`true`],hostBindings:function(r,o){r&1&&ih$1(`mouseleave`,function(s){return o._handleMouseLeave(s)})},decls:4,vars:5,consts:[[`tooltip`,``],[1,`mdc-tooltip`,`mat-mdc-tooltip`,3,`animationend`],[1,`mat-mdc-tooltip-surface`,`mdc-tooltip__surface`]],template:function(r,o){r&1&&(jc$1(0,`div`,1,0),sh$1(`animationend`,function(s){return o._handleAnimationEnd(s)}),jc$1(2,`div`,2),rw(3),Vc$1()()),r&2&&(zD(o.tooltipClass),yh$1(`mdc-tooltip--multiline`,o._isMultiline),sE(3),_h$1(o.message))},styles:[`.mat-mdc-tooltip {
  position: relative;
  transform: scale(0);
  display: inline-flex;
}
.mat-mdc-tooltip::before {
  content: "";
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: -1;
  position: absolute;
}
.mat-mdc-tooltip-panel-below .mat-mdc-tooltip::before {
  top: -8px;
}
.mat-mdc-tooltip-panel-above .mat-mdc-tooltip::before {
  bottom: -8px;
}
.mat-mdc-tooltip-panel-right .mat-mdc-tooltip::before {
  left: -8px;
}
.mat-mdc-tooltip-panel-left .mat-mdc-tooltip::before {
  right: -8px;
}
.mat-mdc-tooltip._mat-animation-noopable {
  animation: none;
  transform: scale(1);
}

.mat-mdc-tooltip-surface {
  word-break: normal;
  overflow-wrap: anywhere;
  padding: 4px 8px;
  min-width: 40px;
  max-width: 200px;
  min-height: 24px;
  max-height: 40vh;
  box-sizing: border-box;
  overflow: hidden;
  text-align: center;
  will-change: transform, opacity;
  background-color: var(--%NS%mat-tooltip-container-color, var(--%NS%mat-sys-inverse-surface));
  color: var(--%NS%mat-tooltip-supporting-text-color, var(--%NS%mat-sys-inverse-on-surface));
  border-radius: var(--%NS%mat-tooltip-container-shape, var(--%NS%mat-sys-corner-extra-small));
  font-family: var(--%NS%mat-tooltip-supporting-text-font, var(--%NS%mat-sys-body-small-font));
  font-size: var(--%NS%mat-tooltip-supporting-text-size, var(--%NS%mat-sys-body-small-size));
  font-weight: var(--%NS%mat-tooltip-supporting-text-weight, var(--%NS%mat-sys-body-small-weight));
  line-height: var(--%NS%mat-tooltip-supporting-text-line-height, var(--%NS%mat-sys-body-small-line-height));
  letter-spacing: var(--%NS%mat-tooltip-supporting-text-tracking, var(--%NS%mat-sys-body-small-tracking));
}
.mat-mdc-tooltip-surface::before {
  position: absolute;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  border: 1px solid transparent;
  border-radius: inherit;
  content: "";
  pointer-events: none;
}
.mdc-tooltip--multiline .mat-mdc-tooltip-surface {
  text-align: left;
}
[dir=rtl] .mdc-tooltip--multiline .mat-mdc-tooltip-surface {
  text-align: right;
}

.mat-mdc-tooltip-panel {
  line-height: normal;
}
.mat-mdc-tooltip-panel.mat-mdc-tooltip-panel-non-interactive {
  pointer-events: none;
}

@keyframes mat-mdc-tooltip-show {
  0% {
    opacity: 0;
    transform: scale(0.8);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes mat-mdc-tooltip-hide {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(0.8);
  }
}
.mat-mdc-tooltip-show {
  animation: mat-mdc-tooltip-show 150ms cubic-bezier(0, 0, 0.2, 1) forwards;
}

.mat-mdc-tooltip-hide {
  animation: mat-mdc-tooltip-hide 75ms cubic-bezier(0.4, 0, 1, 1) forwards;
}
`],encapsulation:2})})()}return n})();var $k=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[zi,Ke,te,Nt]})}return n})();function Jd(n){return Error(`Unable to find icon with the name "${n}"`)}function Up(){return Error(`Could not find HttpClient for use with Angular Material icons. Please add provideHttpClient() to your providers.`)}function em(n){return Error(`The URL provided to MatIconRegistry was not trusted as a resource URL via Angular's DomSanitizer. Attempted URL was "${n}".`)}function tm(n){return Error(`The literal provided to MatIconRegistry was not trusted as safe HTML by Angular's DomSanitizer. Attempted literal was "${n}".`)}var zt=class{url;svgText;options;svgElement=null;constructor(i,e,t){this.url=i,this.svgText=e,this.options=t}};var im=(()=>{class n{_httpClient;_sanitizer;_errorHandler;_document;_svgIconConfigs=new Map;_iconSetConfigs=new Map;_cachedIconsByUrl=new Map;_inProgressUrlFetches=new Map;_fontCssClassesByAlias=new Map;_resolvers=[];_defaultFontSetClass;constructor(e,t,r,o){this._httpClient=e,this._sanitizer=t,this._errorHandler=o,this._document=r}addSvgIcon(e,t,r){return this.addSvgIconInNamespace(``,e,t,r)}addSvgIconLiteral(e,t,r){return this.addSvgIconLiteralInNamespace(``,e,t,r)}addSvgIconInNamespace(e,t,r,o){return this._addSvgIconConfig(e,t,new zt(r,null,o))}addSvgIconResolver(e){return this._resolvers.push(e),this}addSvgIconLiteralInNamespace(e,t,r,o){let a=this._sanitizer.sanitize(ne.HTML,r);if(!a)throw tm(r);let s=bn(a);return this._addSvgIconConfig(e,t,new zt(``,s,o))}addSvgIconSet(e,t){return this.addSvgIconSetInNamespace(``,e,t)}addSvgIconSetLiteral(e,t){return this.addSvgIconSetLiteralInNamespace(``,e,t)}addSvgIconSetInNamespace(e,t,r){return this._addSvgIconSetConfig(e,new zt(t,null,r))}addSvgIconSetLiteralInNamespace(e,t,r){let o=this._sanitizer.sanitize(ne.HTML,t);if(!o)throw tm(t);let a=bn(o);return this._addSvgIconSetConfig(e,new zt(``,a,r))}registerFontClassAlias(e,t=e){return this._fontCssClassesByAlias.set(e,t),this}classNameForFontAlias(e){return this._fontCssClassesByAlias.get(e)||e}setDefaultFontSetClass(...e){return this._defaultFontSetClass=e,this}getDefaultFontSetClass(){return this._defaultFontSetClass??=$p(this._document),this._defaultFontSetClass}getSvgIconFromUrl(e){let t=this._sanitizer.sanitize(ne.RESOURCE_URL,e);if(!t)throw em(e);let r=this._cachedIconsByUrl.get(t);return r?Sg(Io(r)):this._loadSvgIconFromConfig(new zt(e,null)).pipe(Xg(o=>this._cachedIconsByUrl.set(t,o)),Me$1(o=>Io(o)))}getNamedSvgIcon(e,t=``){let r=nm(t,e),o=this._svgIconConfigs.get(r);if(o)return this._getSvgFromConfig(o);if(o=this._getIconConfigFromResolvers(t,e),o)return this._svgIconConfigs.set(r,o),this._getSvgFromConfig(o);let a=this._iconSetConfigs.get(t);return a?this._getSvgFromIconSetConfigs(e,a):xg(Jd(r))}ngOnDestroy(){this._resolvers=[],this._svgIconConfigs.clear(),this._iconSetConfigs.clear(),this._cachedIconsByUrl.clear()}_getSvgFromConfig(e){return e.svgText?Sg(Io(this._svgElementFromConfig(e))):this._loadSvgIconFromConfig(e).pipe(Me$1(t=>Io(t)))}_getSvgFromIconSetConfigs(e,t){let r=this._extractIconWithNameFromAnySet(e,t);if(r)return Sg(r);let o=t.filter(a=>!a.svgText).map(a=>this._loadSvgIconSetFromConfig(a).pipe(kl$1(s=>{let d=`Loading icon set URL: ${this._sanitizer.sanitize(ne.RESOURCE_URL,a.url)} failed: ${s.message}`;return this._errorHandler.handleError(new Error(d)),Sg(null)})));return kg(o).pipe(Me$1(()=>{let a=this._extractIconWithNameFromAnySet(e,t);if(!a)throw Jd(e);return a}))}_extractIconWithNameFromAnySet(e,t){for(let r=t.length-1;r>=0;r--){let o=t[r];if(o.svgText&&o.svgText.toString().indexOf(e)>-1){let a=this._svgElementFromConfig(o),s=this._extractSvgIconFromSet(a,e,o.options);if(s)return s}}return null}_loadSvgIconFromConfig(e){return this._fetchIcon(e).pipe(Xg(t=>e.svgText=t),Me$1(()=>this._svgElementFromConfig(e)))}_loadSvgIconSetFromConfig(e){return e.svgText?Sg(null):this._fetchIcon(e).pipe(Xg(t=>e.svgText=t))}_extractSvgIconFromSet(e,t,r){let o=e.querySelector(`[id="${t}"]`);if(!o)return null;let a=o.cloneNode(!0);if(a.removeAttribute(`id`),a.nodeName.toLowerCase()===`svg`)return this._setSvgAttributes(a,r);if(a.nodeName.toLowerCase()===`symbol`)return this._setSvgAttributes(this._toSvgElement(a),r);let s=this._svgElementFromString(bn(`<svg></svg>`));return s.appendChild(a),this._setSvgAttributes(s,r)}_svgElementFromString(e){let t=this._document.createElement(`DIV`);t.innerHTML=e;let r=t.querySelector(`svg`);if(!r)throw Error(`<svg> tag not found`);return r}_toSvgElement(e){let t=this._svgElementFromString(bn(`<svg></svg>`)),r=e.attributes;for(let o=0;o<r.length;o++){let{name:a,value:s}=r[o];a!==`id`&&t.setAttribute(a,s)}for(let o=0;o<e.childNodes.length;o++)e.childNodes[o].nodeType===this._document.ELEMENT_NODE&&t.appendChild(e.childNodes[o].cloneNode(!0));return t}_setSvgAttributes(e,t){return e.setAttribute(`fit`,``),e.setAttribute(`height`,`100%`),e.setAttribute(`width`,`100%`),e.setAttribute(`preserveAspectRatio`,`xMidYMid meet`),e.setAttribute(`focusable`,`false`),t&&t.viewBox&&e.setAttribute(`viewBox`,t.viewBox),e}_fetchIcon(e){let{url:t,options:r}=e,o=r?.withCredentials??!1;if(!this._httpClient)throw Up();if(t==null)throw Error(`Cannot fetch icon from URL "${t}".`);let a=this._sanitizer.sanitize(ne.RESOURCE_URL,t);if(!a)throw em(t);let s=this._inProgressUrlFetches.get(a);if(s)return s;let c=this._httpClient.get(a,{responseType:`text`,withCredentials:o}).pipe(Me$1(d=>bn(d)),Bl$1(()=>this._inProgressUrlFetches.delete(a)),no$1());return this._inProgressUrlFetches.set(a,c),c}_addSvgIconConfig(e,t,r){return this._svgIconConfigs.set(nm(e,t),r),this}_addSvgIconSetConfig(e,t){let r=this._iconSetConfigs.get(e);return r?r.push(t):this._iconSetConfigs.set(e,[t]),this}_svgElementFromConfig(e){if(!e.svgElement){let t=this._svgElementFromString(e.svgText);this._setSvgAttributes(t,e.options),e.svgElement=t}return e.svgElement}_getIconConfigFromResolvers(e,t){for(let r=0;r<this._resolvers.length;r++){let o=this._resolvers[r](t,e);if(o)return Hp(o)?new zt(o.url,null,o.options):new zt(o,null)}}static ɵfac=function(t){return new(t||n)(ae(ba,8),ae(Ii),ae(Bo,8),ae(_t))};static ɵprov=K({token:n,factory:n.ɵfac,providedIn:`root`})}return n})();function Io(n){return n.cloneNode(!0)}function nm(n,i){return n+`:`+i}function Hp(n){return!!(n.url&&n.options)}function $p(n){let i=null,e=!1;return n.fonts&&typeof n.fonts.forEach==`function`&&n.fonts.forEach(t=>{let r=t.family.replace(/['"]/g,``).trim().toLowerCase();(r===`material icons`||r.startsWith(`material icons `))&&(e=!0),r.startsWith(`material symbols rounded`)?i=`rounded`:r.startsWith(`material symbols sharp`)?i=`sharp`:r.startsWith(`material symbols`)&&(i=`outlined`)}),[i&&!e?`material-symbols-${i}`:`material-icons`,`mat-ligature-font`]}var Gp=new S(`MAT_ICON_DEFAULT_OPTIONS`);var Wp=new S(`mat-icon-location`,{providedIn:`root`,factory:()=>{let n=I(Bo),i=n?n.location:null;return{getPathname:()=>i?i.pathname+i.search:``}}});var rm=[`clip-path`,`color-profile`,`src`,`cursor`,`fill`,`filter`,`marker`,`marker-start`,`marker-mid`,`marker-end`,`mask`,`stroke`];var Yp=rm.map(n=>`[${n}]`).join(`, `);var Xp=/^url\(['"]?#(.*?)['"]?\)$/;var No=(()=>{class n{_elementRef=I(Dr);_iconRegistry=I(im);_location=I(Wp);_errorHandler=I(_t);_defaultColor;get color(){return this._color||this._defaultColor}set color(e){this._color=e}_color;inline=!1;get svgIcon(){return this._svgIcon}set svgIcon(e){e!==this._svgIcon&&(e?this._updateSvgIcon(e):this._svgIcon&&this._clearSvgElement(),this._svgIcon=e)}_svgIcon;get fontSet(){return this._fontSet}set fontSet(e){let t=this._cleanupFontValue(e);t!==this._fontSet&&(this._fontSet=t,this._updateFontIconClasses())}_fontSet;get fontIcon(){return this._fontIcon}set fontIcon(e){let t=this._cleanupFontValue(e);t!==this._fontIcon&&(this._fontIcon=t,this._updateFontIconClasses())}_fontIcon;_previousFontSetClass=[];_previousFontIconClass;_svgName=null;_svgNamespace=null;_previousPath;_elementsWithExternalReferences;_currentIconFetch=q.EMPTY;constructor(){let e=I(new Bh$1(`aria-hidden`),{optional:!0}),t=I(Gp,{optional:!0});t&&(t.color&&(this.color=this._defaultColor=t.color),t.fontSet&&(this.fontSet=t.fontSet)),e||this._elementRef.nativeElement.setAttribute(`aria-hidden`,`true`)}_splitIconName(e){if(!e)return[``,``];let t=e.split(`:`);switch(t.length){case 1:return[``,t[0]];case 2:return t;default:throw Error(`Invalid icon name: "${e}"`)}}ngOnInit(){this._updateFontIconClasses()}ngAfterViewChecked(){let e=this._elementsWithExternalReferences;if(e&&e.size){let t=this._location.getPathname();t!==this._previousPath&&(this._previousPath=t,this._prependPathToReferences(t))}}ngOnDestroy(){this._currentIconFetch.unsubscribe(),this._elementsWithExternalReferences&&this._elementsWithExternalReferences.clear()}_usingFontIcon(){return!this.svgIcon}_setSvgElement(e){this._clearSvgElement();let t=this._location.getPathname();this._previousPath=t,this._cacheChildrenWithExternalReferences(e),this._prependPathToReferences(t),this._elementRef.nativeElement.appendChild(e)}_clearSvgElement(){let e=this._elementRef.nativeElement,t=e.childNodes.length;for(this._elementsWithExternalReferences&&this._elementsWithExternalReferences.clear();t--;){let r=e.childNodes[t];(r.nodeType!==1||r.nodeName.toLowerCase()===`svg`)&&r.remove()}}_updateFontIconClasses(){if(!this._usingFontIcon())return;let e=this._elementRef.nativeElement,t=(this.fontSet?this._iconRegistry.classNameForFontAlias(this.fontSet).split(/ +/):this._iconRegistry.getDefaultFontSetClass()).filter(r=>r.length>0);this._previousFontSetClass.forEach(r=>e.classList.remove(r)),t.forEach(r=>e.classList.add(r)),this._previousFontSetClass=t,this.fontIcon!==this._previousFontIconClass&&!t.includes(`mat-ligature-font`)&&(this._previousFontIconClass&&e.classList.remove(this._previousFontIconClass),this.fontIcon&&e.classList.add(this.fontIcon),this._previousFontIconClass=this.fontIcon)}_cleanupFontValue(e){return typeof e==`string`?e.trim().split(` `)[0]:e}_prependPathToReferences(e){let t=this._elementsWithExternalReferences,r=e.startsWith(`//`)?`/.${e}`:e;t&&t.forEach((o,a)=>{o.forEach(s=>{a.setAttribute(s.name,`url('${r}#${s.value}')`)})})}_cacheChildrenWithExternalReferences(e){let t=e.querySelectorAll(Yp),r=this._elementsWithExternalReferences=this._elementsWithExternalReferences||new Map;for(let o=0;o<t.length;o++)rm.forEach(a=>{let s=t[o],c=s.getAttribute(a),d=c?c.match(Xp):null;if(d){let m=r.get(s);m||(m=[],r.set(s,m)),m.push({name:a,value:d[1]})}})}_updateSvgIcon(e){if(this._svgNamespace=null,this._svgName=null,this._currentIconFetch.unsubscribe(),e){let[t,r]=this._splitIconName(e);t&&(this._svgNamespace=t),r&&(this._svgName=r),this._currentIconFetch=this._iconRegistry.getNamedSvgIcon(r,t).pipe(gt$1(1)).subscribe(o=>this._setSvgElement(o),o=>{let a=`Error retrieving icon ${t}:${r}! ${o.message}`;this._errorHandler.handleError(new Error(a))})}}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){return LI({type:n,selectors:[[`mat-icon`]],hostAttrs:[`role`,`img`,1,`mat-icon`,`notranslate`],hostVars:10,hostBindings:function(r,o){r&2&&(Kp(`data-mat-icon-type`,o._usingFontIcon()?`font`:`svg`)(`data-mat-icon-name`,o._svgName||o.fontIcon)(`data-mat-icon-namespace`,o._svgNamespace||o.fontSet)(`fontIcon`,o._usingFontIcon()?o.fontIcon:null),zD(o.color?`mat-`+o.color:``),yh$1(`mat-icon-inline`,o.inline)(`mat-icon-no-color`,o.color!==`primary`&&o.color!==`accent`&&o.color!==`warn`))},inputs:{color:`color`,inline:[2,`inline`,`inline`,T0],svgIcon:`svgIcon`,fontSet:`fontSet`,fontIcon:`fontIcon`},exportAs:[`matIcon`],ngContentSelectors:[`*`],decls:1,vars:0,template:function(r,o){r&1&&(_D(),ND(0))},styles:[`mat-icon, mat-icon.mat-primary, mat-icon.mat-accent, mat-icon.mat-warn {
  color: var(--%NS%mat-icon-color, inherit);
}

.mat-icon {
  -webkit-user-select: none;
  user-select: none;
  background-repeat: no-repeat;
  display: inline-block;
  fill: currentColor;
  height: 24px;
  width: 24px;
  overflow: hidden;
}
.mat-icon.mat-icon-inline {
  font-size: inherit;
  height: inherit;
  line-height: inherit;
  width: inherit;
}
.mat-icon.mat-ligature-font[fontIcon]::before {
  content: attr(fontIcon);
}

[dir=rtl] .mat-icon-rtl-mirror {
  transform: scale(-1, 1);
}

.mat-form-field:not(.mat-form-field-appearance-legacy) .mat-form-field-prefix .mat-icon,
.mat-form-field:not(.mat-form-field-appearance-legacy) .mat-form-field-suffix .mat-icon {
  display: block;
}
.mat-form-field:not(.mat-form-field-appearance-legacy) .mat-form-field-prefix .mat-icon-button .mat-icon,
.mat-form-field:not(.mat-form-field-appearance-legacy) .mat-form-field-suffix .mat-icon-button .mat-icon {
  margin: auto;
}
`],encapsulation:2})})()}return n})();var cD=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[te]})}return n})();var om=(()=>{class n{_animationsDisabled=ue();state=`unchecked`;disabled=!1;appearance=`full`;static ɵfac=function(t){return new(t||n)};static ɵcmp=LI({type:n,selectors:[[`mat-pseudo-checkbox`]],hostAttrs:[1,`mat-pseudo-checkbox`],hostVars:12,hostBindings:function(t,r){t&2&&yh$1(`mat-pseudo-checkbox-indeterminate`,r.state===`indeterminate`)(`mat-pseudo-checkbox-checked`,r.state===`checked`)(`mat-pseudo-checkbox-disabled`,r.disabled)(`mat-pseudo-checkbox-minimal`,r.appearance===`minimal`)(`mat-pseudo-checkbox-full`,r.appearance===`full`)(`_mat-animation-noopable`,r._animationsDisabled)},inputs:{state:`state`,disabled:`disabled`,appearance:`appearance`},decls:0,vars:0,template:function(t,r){},styles:[`.mat-pseudo-checkbox {
  border-radius: 2px;
  cursor: pointer;
  display: inline-block;
  vertical-align: middle;
  box-sizing: border-box;
  position: relative;
  flex-shrink: 0;
  transition: border-color 90ms cubic-bezier(0, 0, 0.2, 0.1), background-color 90ms cubic-bezier(0, 0, 0.2, 0.1);
}
.mat-pseudo-checkbox::after {
  position: absolute;
  opacity: 0;
  content: "";
  border-bottom: 2px solid currentColor;
  transition: opacity 90ms cubic-bezier(0, 0, 0.2, 0.1);
}
.mat-pseudo-checkbox._mat-animation-noopable {
  transition: none !important;
  animation: none !important;
}
.mat-pseudo-checkbox._mat-animation-noopable::after {
  transition: none;
}

.mat-pseudo-checkbox-disabled {
  cursor: default;
}

.mat-pseudo-checkbox-indeterminate::after {
  left: 1px;
  opacity: 1;
  border-radius: 2px;
}

.mat-pseudo-checkbox-checked::after {
  left: 1px;
  border-left: 2px solid currentColor;
  transform: rotate(-45deg);
  opacity: 1;
  box-sizing: content-box;
}

.mat-pseudo-checkbox-minimal.mat-pseudo-checkbox-checked::after, .mat-pseudo-checkbox-minimal.mat-pseudo-checkbox-indeterminate::after {
  color: var(--%NS%mat-pseudo-checkbox-minimal-selected-checkmark-color, var(--%NS%mat-sys-primary));
}
.mat-pseudo-checkbox-minimal.mat-pseudo-checkbox-checked.mat-pseudo-checkbox-disabled::after, .mat-pseudo-checkbox-minimal.mat-pseudo-checkbox-indeterminate.mat-pseudo-checkbox-disabled::after {
  color: var(--%NS%mat-pseudo-checkbox-minimal-disabled-selected-checkmark-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}

.mat-pseudo-checkbox-full {
  border-color: var(--%NS%mat-pseudo-checkbox-full-unselected-icon-color, var(--%NS%mat-sys-on-surface-variant));
  border-width: 2px;
  border-style: solid;
}
.mat-pseudo-checkbox-full.mat-pseudo-checkbox-disabled {
  border-color: var(--%NS%mat-pseudo-checkbox-full-disabled-unselected-icon-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-pseudo-checkbox-full.mat-pseudo-checkbox-checked, .mat-pseudo-checkbox-full.mat-pseudo-checkbox-indeterminate {
  background-color: var(--%NS%mat-pseudo-checkbox-full-selected-icon-color, var(--%NS%mat-sys-primary));
  border-color: transparent;
}
.mat-pseudo-checkbox-full.mat-pseudo-checkbox-checked::after, .mat-pseudo-checkbox-full.mat-pseudo-checkbox-indeterminate::after {
  color: var(--%NS%mat-pseudo-checkbox-full-selected-checkmark-color, var(--%NS%mat-sys-on-primary));
}
.mat-pseudo-checkbox-full.mat-pseudo-checkbox-checked.mat-pseudo-checkbox-disabled, .mat-pseudo-checkbox-full.mat-pseudo-checkbox-indeterminate.mat-pseudo-checkbox-disabled {
  background-color: var(--%NS%mat-pseudo-checkbox-full-disabled-selected-icon-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-pseudo-checkbox-full.mat-pseudo-checkbox-checked.mat-pseudo-checkbox-disabled::after, .mat-pseudo-checkbox-full.mat-pseudo-checkbox-indeterminate.mat-pseudo-checkbox-disabled::after {
  color: var(--%NS%mat-pseudo-checkbox-full-disabled-selected-checkmark-color, var(--%NS%mat-sys-surface));
}

.mat-pseudo-checkbox {
  width: 18px;
  height: 18px;
}

.mat-pseudo-checkbox-minimal.mat-pseudo-checkbox-checked::after {
  width: 14px;
  height: 6px;
  transform-origin: center;
  top: -4.2426406871px;
  left: 0;
  bottom: 0;
  right: 0;
  margin: auto;
}
.mat-pseudo-checkbox-minimal.mat-pseudo-checkbox-indeterminate::after {
  top: 8px;
  width: 16px;
}

.mat-pseudo-checkbox-full.mat-pseudo-checkbox-checked::after {
  width: 10px;
  height: 4px;
  transform-origin: center;
  top: -2.8284271247px;
  left: 0;
  bottom: 0;
  right: 0;
  margin: auto;
}
.mat-pseudo-checkbox-full.mat-pseudo-checkbox-indeterminate::after {
  top: 6px;
  width: 12px;
}
`],encapsulation:2})}return n})();var To=new S(`MAT_OPTION_PARENT_COMPONENT`);var Ro=new S(`MatOptgroup`);var qp=(()=>{class n{label;disabled=!1;_labelId=I(me).getId(`mat-optgroup-label-`);_inert;constructor(){let e=I(To,{optional:!0});this._inert=e?.inertGroups??!1}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`*`,[[`mat-option`],[`ng-container`]]];return LI({type:n,selectors:[[`mat-optgroup`]],hostAttrs:[1,`mat-mdc-optgroup`],hostVars:3,hostBindings:function(o,a){o&2&&Kp(`role`,a._inert?null:`group`)(`aria-disabled`,a._inert?null:a.disabled.toString())(`aria-labelledby`,a._inert?null:a._labelId)},inputs:{label:`label`,disabled:[2,`disabled`,`disabled`,T0]},exportAs:[`matOptgroup`],features:[hw([{provide:Ro,useExisting:n}])],ngContentSelectors:[`*`,`mat-option, ng-container`],decls:5,vars:4,consts:[[`role`,`presentation`,1,`mat-mdc-optgroup-label`,3,`id`],[1,`mdc-list-item__primary-text`]],template:function(o,a){o&1&&(_D(e),jc$1(0,`span`,0)(1,`span`,1),rw(2),ND(3),Vc$1()(),ND(4,1)),o&2&&(yh$1(`mdc-list-item--disabled`,a.disabled),rh$1(`id`,a._labelId),sE(2),$c$1(``,a.label,` `))},styles:[`.mat-mdc-optgroup {
  color: var(--%NS%mat-optgroup-label-text-color, var(--%NS%mat-sys-on-surface-variant));
  font-family: var(--%NS%mat-optgroup-label-text-font, var(--%NS%mat-sys-title-small-font));
  line-height: var(--%NS%mat-optgroup-label-text-line-height, var(--%NS%mat-sys-title-small-line-height));
  font-size: var(--%NS%mat-optgroup-label-text-size, var(--%NS%mat-sys-title-small-size));
  letter-spacing: var(--%NS%mat-optgroup-label-text-tracking, var(--%NS%mat-sys-title-small-tracking));
  font-weight: var(--%NS%mat-optgroup-label-text-weight, var(--%NS%mat-sys-title-small-weight));
}

.mat-mdc-optgroup-label {
  display: flex;
  position: relative;
  align-items: center;
  justify-content: flex-start;
  overflow: hidden;
  min-height: 48px;
  padding: 0 16px;
  outline: none;
}
.mat-mdc-optgroup-label.mdc-list-item--disabled {
  opacity: 0.38;
}
.mat-mdc-optgroup-label .mdc-list-item__primary-text {
  font-size: inherit;
  font-weight: inherit;
  letter-spacing: inherit;
  line-height: inherit;
  font-family: inherit;
  text-decoration: inherit;
  text-transform: inherit;
  white-space: normal;
  color: inherit;
}
`],encapsulation:2})})()}return n})();var ps=class{source;isUserInput;constructor(i,e=!1){this.source=i,this.isUserInput=e}};var si=(()=>{class n{_element=I(Dr);_changeDetectorRef=I(w0);_parent=I(To,{optional:!0});group=I(Ro,{optional:!0});_signalDisableRipple=!1;_selected=!1;_active=!1;_mostRecentViewValue=``;get multiple(){return this._parent&&this._parent.multiple}get selected(){return this._selected}value;id=I(me).getId(`mat-option-`);get disabled(){return this.group&&this.group.disabled||this._disabled()}set disabled(e){this._disabled.set(e)}_disabled=oa(!1);get disableRipple(){return this._signalDisableRipple?this._parent.disableRipple():!!this._parent?.disableRipple}get hideSingleSelectionIndicator(){return!!(this._parent&&this._parent.hideSingleSelectionIndicator)}onSelectionChange=new Fe;_text;_stateChanges=new te$1;constructor(){let e=I(Se);e.load(Zt),e.load(Un),this._signalDisableRipple=!!this._parent&&ia$1(this._parent.disableRipple)}get active(){return this._active}get viewValue(){return(this._text?.nativeElement.textContent||``).trim()}select(e=!0){this._selected||(this._selected=!0,this._changeDetectorRef.markForCheck(),e&&this._emitSelectionChangeEvent())}deselect(e=!0){this._selected&&(this._selected=!1,this._changeDetectorRef.markForCheck(),e&&this._emitSelectionChangeEvent())}focus(e,t){let r=this._getHostElement();typeof r.focus==`function`&&r.focus(t)}setActiveStyles(){this._active||(this._active=!0,this._changeDetectorRef.markForCheck())}setInactiveStyles(){this._active&&(this._active=!1,this._changeDetectorRef.markForCheck())}getLabel(){return this.viewValue}_handleKeydown(e){(e.keyCode===13||e.keyCode===32)&&!Me(e)&&(this._selectViaInteraction(),e.preventDefault())}_selectViaInteraction(){this.disabled||(this._selected=this.multiple?!this._selected:!0,this._changeDetectorRef.markForCheck(),this._emitSelectionChangeEvent(!0))}_getTabIndex(){return this.disabled?`-1`:`0`}_getHostElement(){return this._element.nativeElement}ngAfterViewChecked(){if(this._selected){let e=this.viewValue;e!==this._mostRecentViewValue&&(this._mostRecentViewValue&&this._stateChanges.next(),this._mostRecentViewValue=e)}}ngOnDestroy(){this._stateChanges.complete()}_emitSelectionChangeEvent(e=!1){this.onSelectionChange.emit(new ps(this,e))}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`text`],t=[[[`mat-icon`]],`*`],r=[`mat-icon`,`*`];function o(c,d){if(c&1&&Xp$1(0,`mat-pseudo-checkbox`,1),c&2){let m=TD();Jp$1(`disabled`,m.disabled)(`state`,m.selected?`checked`:`unchecked`)}}function a(c,d){if(c&1&&Xp$1(0,`mat-pseudo-checkbox`,3),c&2){let m=TD();Jp$1(`disabled`,m.disabled)}}function s(c,d){if(c&1&&(yi(0,`span`,4),rw(1),Fc$1()),c&2){let m=TD();sE(),$c$1(`(`,m.group.label,`)`)}}return LI({type:n,selectors:[[`mat-option`]],viewQuery:function(d,m){if(d&1&&lh$1(e,7),d&2){let _;SD(_=xD())&&(m._text=_.first)}},hostAttrs:[`role`,`option`,1,`mat-mdc-option`,`mdc-list-item`],hostVars:11,hostBindings:function(d,m){d&1&&ih$1(`click`,function(){return m._selectViaInteraction()})(`keydown`,function(k){return m._handleKeydown(k)}),d&2&&(rh$1(`id`,m.id),Kp(`aria-selected`,m.selected)(`aria-disabled`,m.disabled.toString()),yh$1(`mdc-list-item--selected`,m.selected)(`mat-mdc-option-multiple`,m.multiple)(`mat-mdc-option-active`,m.active)(`mdc-list-item--disabled`,m.disabled))},inputs:{value:`value`,id:`id`,disabled:[2,`disabled`,`disabled`,T0]},outputs:{onSelectionChange:`onSelectionChange`},exportAs:[`matOption`],ngContentSelectors:r,decls:8,vars:5,consts:[[`text`,``],[`aria-hidden`,`true`,1,`mat-mdc-option-pseudo-checkbox`,3,`disabled`,`state`],[1,`mdc-list-item__primary-text`],[`state`,`checked`,`aria-hidden`,`true`,`appearance`,`minimal`,1,`mat-mdc-option-pseudo-checkbox`,3,`disabled`],[1,`cdk-visually-hidden`],[`aria-hidden`,`true`,`mat-ripple`,``,1,`mat-mdc-option-ripple`,`mat-focus-indicator`,3,`matRippleTrigger`,`matRippleDisabled`]],template:function(d,m){d&1&&(_D(t),uD(0,o,1,2,`mat-pseudo-checkbox`,1),ND(1),yi(2,`span`,2,0),ND(4,1),Fc$1(),uD(5,a,1,1,`mat-pseudo-checkbox`,3),uD(6,s,2,1,`span`,4),Xp$1(7,`div`,5)),d&2&&(fD(m.multiple?0:-1),sE(5),fD(!m.multiple&&m.selected&&!m.hideSingleSelectionIndicator?5:-1),sE(),fD(m.group&&m.group._inert?6:-1),sE(),Jp$1(`matRippleTrigger`,m._getHostElement())(`matRippleDisabled`,m.disabled||m.disableRipple))},dependencies:[om,qn],styles:[`.mat-mdc-option {
  -webkit-user-select: none;
  user-select: none;
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  display: flex;
  position: relative;
  align-items: center;
  justify-content: flex-start;
  overflow: hidden;
  min-height: 48px;
  padding: 0 16px;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  color: var(--%NS%mat-option-label-text-color, var(--%NS%mat-sys-on-surface));
  font-family: var(--%NS%mat-option-label-text-font, var(--%NS%mat-sys-label-large-font));
  line-height: var(--%NS%mat-option-label-text-line-height, var(--%NS%mat-sys-label-large-line-height));
  font-size: var(--%NS%mat-option-label-text-size, var(--%NS%mat-sys-body-large-size));
  letter-spacing: var(--%NS%mat-option-label-text-tracking, var(--%NS%mat-sys-label-large-tracking));
  font-weight: var(--%NS%mat-option-label-text-weight, var(--%NS%mat-sys-body-large-weight));
}
.mat-mdc-option:hover:not(.mdc-list-item--disabled) {
  background-color: var(--%NS%mat-option-hover-state-layer-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) calc(var(--%NS%mat-sys-hover-state-layer-opacity) * 100%), transparent));
}
.mat-mdc-option:focus.mdc-list-item, .mat-mdc-option.mat-mdc-option-active.mdc-list-item {
  background-color: var(--%NS%mat-option-focus-state-layer-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) calc(var(--%NS%mat-sys-focus-state-layer-opacity) * 100%), transparent));
  outline: 0;
}
.mat-mdc-option.mdc-list-item--%NS%selected:not(.mdc-list-item--disabled):not(.mat-mdc-option-active, .mat-mdc-option-multiple, :focus, :hover) {
  background-color: var(--%NS%mat-option-selected-state-layer-color, var(--%NS%mat-sys-secondary-container));
}
.mat-mdc-option.mdc-list-item--%NS%selected:not(.mdc-list-item--disabled):not(.mat-mdc-option-active, .mat-mdc-option-multiple, :focus, :hover) .mdc-list-item__primary-text {
  color: var(--%NS%mat-option-selected-state-label-text-color, var(--%NS%mat-sys-on-secondary-container));
}
.mat-mdc-option .mat-pseudo-checkbox {
  --%NS%mat-pseudo-checkbox-minimal-selected-checkmark-color: var(--%NS%mat-option-selected-state-label-text-color, var(--%NS%mat-sys-on-secondary-container));
}
.mat-mdc-option.mdc-list-item {
  align-items: center;
  background: transparent;
}
.mat-mdc-option.mdc-list-item--disabled {
  cursor: default;
  pointer-events: none;
}
.mat-mdc-option.mdc-list-item--disabled .mat-mdc-option-pseudo-checkbox, .mat-mdc-option.mdc-list-item--disabled .mdc-list-item__primary-text, .mat-mdc-option.mdc-list-item--disabled > mat-icon {
  opacity: 0.38;
}
.mat-mdc-optgroup .mat-mdc-option:not(.mat-mdc-option-multiple) {
  padding-left: 32px;
}
[dir=rtl] .mat-mdc-optgroup .mat-mdc-option:not(.mat-mdc-option-multiple) {
  padding-left: 16px;
  padding-right: 32px;
}
.mat-mdc-option .mat-icon,
.mat-mdc-option .mat-pseudo-checkbox-full {
  margin-right: 16px;
  flex-shrink: 0;
}
[dir=rtl] .mat-mdc-option .mat-icon,
[dir=rtl] .mat-mdc-option .mat-pseudo-checkbox-full {
  margin-right: 0;
  margin-left: 16px;
}
.mat-mdc-option .mat-pseudo-checkbox-minimal {
  margin-left: 16px;
  flex-shrink: 0;
}
[dir=rtl] .mat-mdc-option .mat-pseudo-checkbox-minimal {
  margin-right: 16px;
  margin-left: 0;
}
.mat-mdc-option .mat-mdc-option-ripple {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  position: absolute;
  pointer-events: none;
}
.mat-mdc-option .mdc-list-item__primary-text {
  white-space: normal;
  font-size: inherit;
  font-weight: inherit;
  letter-spacing: inherit;
  line-height: inherit;
  font-family: inherit;
  text-decoration: inherit;
  text-transform: inherit;
  margin-right: auto;
}
[dir=rtl] .mat-mdc-option .mdc-list-item__primary-text {
  margin-right: 0;
  margin-left: auto;
}
@media (forced-colors: active) {
  .mat-mdc-option.mdc-list-item--%NS%selected:not(:has(.mat-mdc-option-pseudo-checkbox))::after {
    content: "";
    position: absolute;
    top: 50%;
    right: 16px;
    transform: translateY(-50%);
    width: 10px;
    height: 0;
    border-bottom: solid 10px;
    border-radius: 10px;
  }
  [dir=rtl] .mat-mdc-option.mdc-list-item--%NS%selected:not(:has(.mat-mdc-option-pseudo-checkbox))::after {
    right: auto;
    left: 16px;
  }
}

.mat-mdc-option-multiple {
  --%NS%mat-list-list-item-selected-container-color: var(--%NS%mat-list-list-item-container-color, transparent);
}

.mat-mdc-option-active .mat-focus-indicator::before {
  content: "";
}
`],encapsulation:2})})()}return n})();function am(n,i,e){if(e.length){let t=i.toArray(),r=e.toArray(),o=0;for(let a=0;a<n+1;a++)t[a].group&&t[a].group===r[o]&&o++;return o}return 0}function sm(n,i,e,t){return n<e?n:n+i>e+t?Math.max(0,n-t+i):e}var mr=class{_multiple;_emitChanges;compareWith;_selection=new Set;_deselectedToEmit=[];_selectedToEmit=[];_selected=null;get selected(){return this._selected||(this._selected=Array.from(this._selection.values())),this._selected}changed=new te$1;bulk={select:i=>this._select(i),deselect:i=>this._deselect(i),setSelection:i=>this._setSelection(i)};constructor(i=!1,e,t=!0,r){this._multiple=i,this._emitChanges=t,this.compareWith=r,e&&e.length&&(i?e.forEach(o=>this._markSelected(o)):this._markSelected(e[0]),this._selectedToEmit.length=0)}select(...i){return this._select(i)}deselect(...i){return this._deselect(i)}setSelection(...i){return this._setSelection(i)}toggle(i){return this.isSelected(i)?this.deselect(i):this.select(i)}clear(i=!0){this._unmarkAll();let e=this._hasQueuedChanges();return i&&this._emitChangeEvent(),e}isSelected(i){return this._selection.has(this._getConcreteValue(i))}isEmpty(){return this._selection.size===0}hasValue(){return!this.isEmpty()}sort(i){this._multiple&&this.selected&&this._selected.sort(i)}isMultipleSelection(){return this._multiple}_select(i){this._verifyValueAssignment(i),i.forEach(t=>this._markSelected(t));let e=this._hasQueuedChanges();return this._emitChangeEvent(),e}_deselect(i){this._verifyValueAssignment(i),i.forEach(t=>this._unmarkSelected(t));let e=this._hasQueuedChanges();return this._emitChangeEvent(),e}_setSelection(i){this._verifyValueAssignment(i);let e=this.selected,t=new Set(i.map(o=>this._getConcreteValue(o)));i.forEach(o=>this._markSelected(o)),e.filter(o=>!t.has(this._getConcreteValue(o,t))).forEach(o=>this._unmarkSelected(o));let r=this._hasQueuedChanges();return this._emitChangeEvent(),r}_emitChangeEvent(){this._selected=null,(this._selectedToEmit.length||this._deselectedToEmit.length)&&(this.changed.next({source:this,added:this._selectedToEmit,removed:this._deselectedToEmit}),this._deselectedToEmit=[],this._selectedToEmit=[])}_markSelected(i){i=this._getConcreteValue(i),this.isSelected(i)||(this._multiple||this._unmarkAll(),this.isSelected(i)||this._selection.add(i),this._emitChanges&&this._selectedToEmit.push(i))}_unmarkSelected(i){i=this._getConcreteValue(i),this.isSelected(i)&&(this._selection.delete(i),this._emitChanges&&this._deselectedToEmit.push(i))}_unmarkAll(){this.isEmpty()||this._selection.forEach(i=>this._unmarkSelected(i))}_verifyValueAssignment(i){i.length>1&&this._multiple}_hasQueuedChanges(){return!!(this._deselectedToEmit.length||this._selectedToEmit.length)}_getConcreteValue(i,e){if(this.compareWith){e=e??this._selection;for(let t of e)if(this.compareWith(i,t))return t;return i}else return i}};var Zp=(()=>{class n{_listeners=[];notify(e,t){for(let r of this._listeners)r(e,t)}listen(e){return this._listeners.push(e),()=>{this._listeners=this._listeners.filter(t=>e!==t)}}ngOnDestroy(){this._listeners=[]}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var lm=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[te]})}return n})();var fs=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[Zn,lm,si,te]})}return n})();var Qp=new S(`mat-select-scroll-strategy`,{providedIn:`root`,factory:()=>{let n=I(le);return()=>Ft(n)}});var Jp=new S(`MAT_SELECT_CONFIG`);var cm=new S(`MatSelectTrigger`);var gs=class{source;value;constructor(i,e){this.source=i,this.value=e}};var dm=(()=>{class n{_viewportRuler=I(Tt);_changeDetectorRef=I(w0);_elementRef=I(Dr);_dir=I(Ne,{optional:!0});_idGenerator=I(me);_renderer=I(La$1);_parentFormField=I(sr,{optional:!0});ngControl=I(Ye,{self:!0,optional:!0});_liveAnnouncer=I(Bi);_defaultOptions=I(Jp,{optional:!0});_animationsDisabled=ue();_popoverLocation;_initialized=new te$1;_cleanupDetach;options;optionGroups;customTrigger;_positions=[{originX:`start`,originY:`bottom`,overlayX:`start`,overlayY:`top`},{originX:`end`,originY:`bottom`,overlayX:`end`,overlayY:`top`},{originX:`start`,originY:`top`,overlayX:`start`,overlayY:`bottom`,panelClass:`mat-mdc-select-panel-above`},{originX:`end`,originY:`top`,overlayX:`end`,overlayY:`bottom`,panelClass:`mat-mdc-select-panel-above`}];_scrollOptionIntoView(e){let t=this.options.toArray()[e];if(t){let r=this.panel.nativeElement,o=am(e,this.options,this.optionGroups),a=t._getHostElement();e===0&&o===1?r.scrollTop=0:r.scrollTop=sm(a.offsetTop,a.offsetHeight,r.scrollTop,r.offsetHeight)}}_positioningSettled(){this._scrollOptionIntoView(this._keyManager.activeItemIndex||0)}_getChangeEvent(e){return new gs(this,e)}_scrollStrategyFactory=I(Qp);_panelOpen=!1;_compareWith=(e,t)=>e===t;_uid=this._idGenerator.getId(`mat-select-`);_triggerAriaLabelledBy=null;_previousControl;_destroy=new te$1;_errorStateTracker;stateChanges=new te$1;disableAutomaticLabeling=!0;userAriaDescribedBy;_selectionModel;_keyManager;_preferredOverlayOrigin;_overlayWidth;_onChange=()=>{};_onTouched=()=>{};_valueId=this._idGenerator.getId(`mat-select-value-`);_scrollStrategy;_overlayPanelClass=this._defaultOptions?.overlayPanelClass||``;get focused(){return this._focused||this._panelOpen}_focused=!1;controlType=`mat-select`;trigger;panel;_overlayDir;panelClass;disabled=!1;get disableRipple(){return this._disableRipple()}set disableRipple(e){this._disableRipple.set(e)}_disableRipple=oa(!1);tabIndex=0;get hideSingleSelectionIndicator(){return this._hideSingleSelectionIndicator}set hideSingleSelectionIndicator(e){this._hideSingleSelectionIndicator=e,this._syncParentProperties()}_hideSingleSelectionIndicator=this._defaultOptions?.hideSingleSelectionIndicator??!1;get placeholder(){return this._placeholder}set placeholder(e){this._placeholder=e,this.stateChanges.next()}_placeholder;get required(){return this._required??this.ngControl?.control?.hasValidator(Ct.required)??!1}set required(e){this._required=e,this.stateChanges.next()}_required;get multiple(){return this._multiple}set multiple(e){this._selectionModel,this._multiple=e}_multiple=!1;disableOptionCentering=this._defaultOptions?.disableOptionCentering??!1;get compareWith(){return this._compareWith}set compareWith(e){this._compareWith=e,this._selectionModel&&this._initializeSelection()}get value(){return this._value}set value(e){this._assignValue(e)&&this._onChange(e)}_value;ariaLabel=``;ariaLabelledby;get errorStateMatcher(){return this._errorStateTracker.matcher}set errorStateMatcher(e){this._errorStateTracker.matcher=e}typeaheadDebounceInterval;sortComparator;get id(){return this._id}set id(e){this._id=e||this._uid,this.stateChanges.next()}_id;get errorState(){return this._errorStateTracker.errorState}set errorState(e){this._errorStateTracker.errorState=e}panelWidth=this._defaultOptions&&typeof this._defaultOptions.panelWidth<`u`?this._defaultOptions.panelWidth:`auto`;canSelectNullableOptions=this._defaultOptions?.canSelectNullableOptions??!1;optionSelectionChanges=Og(()=>{let e=this.options;return e?e.changes.pipe(Al$1(e),Ul$1(()=>Bg(...e.map(t=>t.onSelectionChange)))):this._initialized.pipe(Ul$1(()=>this.optionSelectionChanges))});openedChange=new Fe;_openedStream=this.openedChange.pipe(rn(e=>e),Me$1(()=>{}));_closedStream=this.openedChange.pipe(rn(e=>!e),Me$1(()=>{}));selectionChange=new Fe;valueChange=new Fe;constructor(){let e=I(Ao),t=I(rr,{optional:!0}),r=I(Cn,{optional:!0}),o=I(new Bh$1(`tabindex`),{optional:!0}),a=I(Fi,{optional:!0}),s=I(ko,{optional:!0,self:!0});this.ngControl&&(this.ngControl.valueAccessor=this),this._defaultOptions?.typeaheadDebounceInterval!=null&&(this.typeaheadDebounceInterval=this._defaultOptions.typeaheadDebounceInterval),this._errorStateTracker=new ri(e,s||this.ngControl,r,t,this.stateChanges),this._scrollStrategy=this._scrollStrategyFactory(),this.tabIndex=o==null?0:parseInt(o)||0,this._popoverLocation=a?.usePopover===!1?null:`inline`,this.id=this.id}ngOnInit(){this._selectionModel=new mr(this.multiple),this.stateChanges.next(),this._viewportRuler.change().pipe(Rl$1(this._destroy)).subscribe(()=>{this.panelOpen&&(this._overlayWidth=this._getOverlayWidth(this._preferredOverlayOrigin),this._changeDetectorRef.detectChanges())})}ngAfterContentInit(){this._initialized.next(),this._initialized.complete(),this._initKeyManager(),this._selectionModel.changed.pipe(Rl$1(this._destroy)).subscribe(e=>{e.added.forEach(t=>t.select()),e.removed.forEach(t=>t.deselect())}),this.options.changes.pipe(Al$1(null),Rl$1(this._destroy)).subscribe(()=>{this._resetOptions(),this._initializeSelection()})}ngDoCheck(){let e=this._getTriggerAriaLabelledby(),t=this.ngControl;if(e!==this._triggerAriaLabelledBy){let r=this._elementRef.nativeElement;this._triggerAriaLabelledBy=e,e?r.setAttribute(`aria-labelledby`,e):r.removeAttribute(`aria-labelledby`)}t&&(this._previousControl!==t.control&&(this._previousControl!==void 0&&t.disabled!==null&&t.disabled!==this.disabled&&(this.disabled=t.disabled),this._previousControl=t.control),this.updateErrorState())}ngOnChanges(e){(e.disabled||e.userAriaDescribedBy)&&this.stateChanges.next(),e.typeaheadDebounceInterval&&this._keyManager&&this._keyManager.withTypeAhead(this.typeaheadDebounceInterval),e.panelClass&&this.panelClass instanceof Set&&(this.panelClass=Array.from(this.panelClass))}ngOnDestroy(){this._cleanupDetach?.(),this._keyManager?.destroy(),this._destroy.next(),this._destroy.complete(),this.stateChanges.complete()}toggle(){this.panelOpen?this.close():this.open()}open(){this._canOpen()&&(this._parentFormField&&(this._preferredOverlayOrigin=this._parentFormField.getConnectedOverlayOrigin()),this._cleanupDetach?.(),this._overlayWidth=this._getOverlayWidth(this._preferredOverlayOrigin),this._panelOpen=!0,this._overlayDir.positionChange.pipe(gt$1(1)).subscribe(()=>{this._changeDetectorRef.detectChanges(),this._positioningSettled()}),this._overlayDir.attachOverlay(),this._keyManager.withHorizontalOrientation(null),this._highlightCorrectOption(),this._changeDetectorRef.markForCheck(),this.stateChanges.next(),Promise.resolve().then(()=>this.openedChange.emit(!0)))}close(){this._panelOpen&&(this._panelOpen=!1,this._exitAndDetach(),this._keyManager.withHorizontalOrientation(this._isRtl()?`rtl`:`ltr`),this._changeDetectorRef.markForCheck(),this._onTouched(),this.stateChanges.next(),Promise.resolve().then(()=>this.openedChange.emit(!1)))}_exitAndDetach(){if(this._animationsDisabled||!this.panel){this._detachOverlay();return}this._cleanupDetach?.(),this._cleanupDetach=()=>{t(),clearTimeout(r),this._cleanupDetach=void 0};let e=this.panel.nativeElement,t=this._renderer.listen(e,`animationend`,o=>{o.animationName===`_mat-select-exit`&&(this._cleanupDetach?.(),this._detachOverlay())}),r=setTimeout(()=>{this._cleanupDetach?.(),this._detachOverlay()},200);e.classList.add(`mat-select-panel-exit`)}_detachOverlay(){this._overlayDir.detachOverlay(),this._changeDetectorRef.markForCheck()}writeValue(e){this._assignValue(e)}registerOnChange(e){this._onChange=e}registerOnTouched(e){this._onTouched=e}setDisabledState(e){this.disabled=e,this._changeDetectorRef.markForCheck(),this.stateChanges.next()}get panelOpen(){return this._panelOpen}get selected(){return this.multiple?this._selectionModel?.selected||[]:this._selectionModel?.selected[0]}get triggerValue(){if(this.empty)return``;if(this._multiple){let e=this._selectionModel.selected.map(t=>t.viewValue);return this._isRtl()&&e.reverse(),e.join(`, `)}return this._selectionModel.selected[0].viewValue}updateErrorState(){this._errorStateTracker.updateErrorState()}_isRtl(){return this._dir?this._dir.value===`rtl`:!1}_handleKeydown(e){this.disabled||(this.panelOpen?this._handleOpenKeydown(e):this._handleClosedKeydown(e))}_handleClosedKeydown(e){let t=e.keyCode,r=t===40||t===38||t===37||t===39,o=t===13||t===32,a=this._keyManager;if(!a.isTyping()&&o&&!Me(e)||(this.multiple||e.altKey)&&r)e.preventDefault(),this.open();else if(!this.multiple){let s=this.selected;a.onKeydown(e);let c=this.selected;c&&s!==c&&this._liveAnnouncer.announce(c.viewValue,1e4)}}_handleOpenKeydown(e){let t=this._keyManager,r=e.keyCode,o=r===40||r===38,a=t.isTyping();if(o&&e.altKey)e.preventDefault(),this.close();else if(!a&&(r===13||r===32)&&t.activeItem&&!Me(e))e.preventDefault(),t.activeItem._selectViaInteraction();else if(!a&&this._multiple&&r===65&&e.ctrlKey){e.preventDefault();let s=this.options.some(c=>!c.disabled&&!c.selected);this.options.forEach(c=>{c.disabled||(s?c.select():c.deselect())})}else{let s=t.activeItemIndex;t.onKeydown(e),this._multiple&&o&&e.shiftKey&&t.activeItem&&t.activeItemIndex!==s&&t.activeItem._selectViaInteraction()}}_handleOverlayKeydown(e){e.keyCode===27&&!Me(e)&&(e.preventDefault(),this.close())}_onFocus(){this.disabled||(this._focused=!0,this.stateChanges.next())}_onBlur(){this._focused=!1,this._keyManager?.cancelTypeahead(),!this.disabled&&!this.panelOpen&&(this._onTouched(),this._changeDetectorRef.markForCheck(),this.stateChanges.next())}get empty(){return!this._selectionModel||this._selectionModel.isEmpty()}_initializeSelection(){Promise.resolve().then(()=>{this.ngControl&&(this._value=this.ngControl.value),this._setSelectionByValue(this._value),this.stateChanges.next()})}_setSelectionByValue(e){if(this.options.forEach(t=>t.setInactiveStyles()),this._selectionModel.clear(),this.multiple&&e)e.forEach(t=>this._selectOptionByValue(t)),this._sortValues();else{let t=this._selectOptionByValue(e);t?this._keyManager.updateActiveItem(t):this.panelOpen||this._keyManager.updateActiveItem(-1)}this._changeDetectorRef.markForCheck()}_selectOptionByValue(e){let t=this.options.find(r=>{if(this._selectionModel.isSelected(r))return!1;try{return(r.value!=null||this.canSelectNullableOptions)&&this._compareWith(r.value,e)}catch(o){return!1}});return t&&this._selectionModel.select(t),t}_assignValue(e){return e!==this._value||this._multiple&&Array.isArray(e)?(this.options&&this._setSelectionByValue(e),this._value=e,!0):!1}_skipPredicate=e=>this.panelOpen?!1:e.disabled;_getOverlayWidth(e){return this.panelWidth===`auto`?(e instanceof Bn?e.elementRef:e||this._elementRef).nativeElement.getBoundingClientRect().width:this.panelWidth===null?``:this.panelWidth}_syncParentProperties(){if(this.options)for(let e of this.options)e._changeDetectorRef.markForCheck()}_initKeyManager(){this._keyManager=new Gi(this.options).withTypeAhead(this.typeaheadDebounceInterval).withVerticalOrientation().withHorizontalOrientation(this._isRtl()?`rtl`:`ltr`).withHomeAndEnd().withPageUpDown().withAllowedModifierKeys([`shiftKey`]).skipPredicate(this._skipPredicate),this._keyManager.tabOut.subscribe(()=>{this.panelOpen&&(!this.multiple&&this._keyManager.activeItem&&this._keyManager.activeItem._selectViaInteraction(),this.focus(),this.close())}),this._keyManager.change.subscribe(()=>{this._panelOpen&&this.panel?this._scrollOptionIntoView(this._keyManager.activeItemIndex||0):!this._panelOpen&&!this.multiple&&this._keyManager.activeItem&&this._keyManager.activeItem._selectViaInteraction()})}_resetOptions(){let e=Bg(this.options.changes,this._destroy);this.optionSelectionChanges.pipe(Rl$1(e)).subscribe(t=>{this._onSelect(t.source,t.isUserInput),t.isUserInput&&!this.multiple&&this._panelOpen&&(this.close(),this.focus())}),Bg(...this.options.map(t=>t._stateChanges)).pipe(Rl$1(e)).subscribe(()=>{this._changeDetectorRef.detectChanges(),this.stateChanges.next()})}_onSelect(e,t){let r=this._selectionModel.isSelected(e);!this.canSelectNullableOptions&&e.value==null&&!this._multiple?(e.deselect(),this._selectionModel.clear(),this.value!=null&&this._propagateChanges(e.value)):(r!==e.selected&&(e.selected?this._selectionModel.select(e):this._selectionModel.deselect(e)),t&&this._keyManager.setActiveItem(e),this.multiple&&(this._sortValues(),t&&this.focus())),r!==this._selectionModel.isSelected(e)&&this._propagateChanges(),this.stateChanges.next()}_sortValues(){if(this.multiple){let e=this.options.toArray();this._selectionModel.sort((t,r)=>this.sortComparator?this.sortComparator(t,r,e):e.indexOf(t)-e.indexOf(r)),this.stateChanges.next()}}_propagateChanges(e){let t;this.multiple?t=this.selected.map(r=>r.value):t=this.selected?this.selected.value:e,this._value=t,this.valueChange.emit(t),this._onChange(t),this.selectionChange.emit(this._getChangeEvent(t)),this._changeDetectorRef.markForCheck()}_highlightCorrectOption(){if(this._keyManager)if(this.empty){let e=-1;for(let t=0;t<this.options.length;t++)if(!this.options.get(t).disabled){e=t;break}this._keyManager.setActiveItem(e)}else this._keyManager.setActiveItem(this._selectionModel.selected[0])}_canOpen(){return!this._panelOpen&&!this.disabled&&this.options?.length>0&&!!this._overlayDir}focus(e){this._elementRef.nativeElement.focus(e)}_getPanelAriaLabelledby(){if(this.ariaLabel)return null;let e=this._parentFormField?.getLabelId()||null,t=e?e+` `:``;return this.ariaLabelledby?t+this.ariaLabelledby:e}_getAriaActiveDescendant(){return this.panelOpen&&this._keyManager&&this._keyManager.activeItem?this._keyManager.activeItem.id:null}_getTriggerAriaLabelledby(){if(this.ariaLabel)return null;let e=this._parentFormField?.getLabelId()||``;return this.ariaLabelledby&&(e+=` `+this.ariaLabelledby),e||(e=this._valueId),e}get describedByIds(){return this._elementRef.nativeElement.getAttribute(`aria-describedby`)?.split(` `)||[]}setDescribedByIds(e){let t=this._elementRef.nativeElement;e.length?t.setAttribute(`aria-describedby`,e.join(` `)):t.removeAttribute(`aria-describedby`)}onContainerClick(e){let t=Ie(e);t&&(t.tagName===`MAT-OPTION`||t.classList.contains(`cdk-overlay-backdrop`)||t.closest(`.mat-mdc-select-panel`))||(this.focus(),this.open())}get shouldLabelFloat(){return this.panelOpen||!this.empty||this.focused&&!!this.placeholder}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`trigger`],t=[`panel`],r=[[[`mat-select-trigger`]],`*`],o=[`mat-select-trigger`,`*`];function a(_,k){if(_&1&&(yi(0,`span`,4),rw(1),Fc$1()),_&2){let p=TD();sE(),_h$1(p.placeholder)}}function s(_,k){_&1&&ND(0)}function c(_,k){if(_&1&&(yi(0,`span`,11),rw(1),Fc$1()),_&2){let p=TD(2);sE(),_h$1(p.triggerValue)}}function d(_,k){if(_&1&&(yi(0,`span`,5),uD(1,s,1,0)(2,c,2,1,`span`,11),Fc$1()),_&2){let p=TD();sE(),fD(p.customTrigger?1:2)}}function m(_,k){if(_&1){let p=wD();yi(0,`div`,12,1),ih$1(`keydown`,function(K){Mu$1(p);let fe=TD();return Su$1(fe._handleKeydown(K))}),ND(2,1),Fc$1()}if(_&2){let p=TD();zD(p.panelClass),yh$1(`mat-select-panel-animations-enabled`,!p._animationsDisabled)(`mat-primary`,p._parentFormField?.color===`primary`)(`mat-accent`,p._parentFormField?.color===`accent`)(`mat-warn`,p._parentFormField?.color===`warn`)(`mat-undefined`,!p._parentFormField?.color),Kp(`id`,p.id+`-panel`)(`aria-multiselectable`,p.multiple)(`aria-label`,p.ariaLabel||null)(`aria-labelledby`,p._getPanelAriaLabelledby())}}return LI({type:n,selectors:[[`mat-select`]],contentQueries:function(k,p,z){if(k&1&&ch$1(z,cm,5)(z,si,5)(z,Ro,5),k&2){let K;SD(K=xD())&&(p.customTrigger=K.first),SD(K=xD())&&(p.options=K),SD(K=xD())&&(p.optionGroups=K)}},viewQuery:function(k,p){if(k&1&&lh$1(e,5)(t,5)(Qr,5),k&2){let z;SD(z=xD())&&(p.trigger=z.first),SD(z=xD())&&(p.panel=z.first),SD(z=xD())&&(p._overlayDir=z.first)}},hostAttrs:[`role`,`combobox`,`aria-haspopup`,`listbox`,1,`mat-mdc-select`],hostVars:21,hostBindings:function(k,p){k&1&&ih$1(`keydown`,function(K){return p._handleKeydown(K)})(`focus`,function(){return p._onFocus()})(`blur`,function(){return p._onBlur()}),k&2&&(Kp(`id`,p.id)(`tabindex`,p.disabled?-1:p.tabIndex)(`aria-controls`,p.panelOpen?p.id+`-panel`:null)(`aria-expanded`,p.panelOpen)(`aria-label`,p.ariaLabel||null)(`aria-required`,p.required.toString())(`aria-disabled`,p.disabled.toString())(`aria-invalid`,p.errorState)(`aria-activedescendant`,p._getAriaActiveDescendant()),yh$1(`mat-mdc-select-disabled`,p.disabled)(`mat-mdc-select-invalid`,p.errorState)(`mat-mdc-select-required`,p.required)(`mat-mdc-select-empty`,p.empty)(`mat-mdc-select-multiple`,p.multiple)(`mat-select-open`,p.panelOpen))},inputs:{userAriaDescribedBy:[0,`aria-describedby`,`userAriaDescribedBy`],panelClass:`panelClass`,disabled:[2,`disabled`,`disabled`,T0],disableRipple:[2,`disableRipple`,`disableRipple`,T0],tabIndex:[2,`tabIndex`,`tabIndex`,_=>_==null?0:C0(_)],hideSingleSelectionIndicator:[2,`hideSingleSelectionIndicator`,`hideSingleSelectionIndicator`,T0],placeholder:`placeholder`,required:[2,`required`,`required`,T0],multiple:[2,`multiple`,`multiple`,T0],disableOptionCentering:[2,`disableOptionCentering`,`disableOptionCentering`,T0],compareWith:`compareWith`,value:`value`,ariaLabel:[0,`aria-label`,`ariaLabel`],ariaLabelledby:[0,`aria-labelledby`,`ariaLabelledby`],errorStateMatcher:`errorStateMatcher`,typeaheadDebounceInterval:[2,`typeaheadDebounceInterval`,`typeaheadDebounceInterval`,C0],sortComparator:`sortComparator`,id:`id`,panelWidth:`panelWidth`,canSelectNullableOptions:[2,`canSelectNullableOptions`,`canSelectNullableOptions`,T0]},outputs:{openedChange:`openedChange`,_openedStream:`opened`,_closedStream:`closed`,selectionChange:`selectionChange`,valueChange:`valueChange`},exportAs:[`matSelect`],features:[hw([{provide:ar,useExisting:n},{provide:To,useExisting:n}]),iy],ngContentSelectors:o,decls:11,vars:10,consts:[[`fallbackOverlayOrigin`,`cdkOverlayOrigin`,`trigger`,``],[`panel`,``],[`cdk-overlay-origin`,``,1,`mat-mdc-select-trigger`,3,`click`],[1,`mat-mdc-select-value`],[1,`mat-mdc-select-placeholder`,`mat-mdc-select-min-line`],[1,`mat-mdc-select-value-text`],[1,`mat-mdc-select-arrow-wrapper`],[1,`mat-mdc-select-arrow`],[`viewBox`,`0 0 24 24`,`width`,`24px`,`height`,`24px`,`focusable`,`false`,`aria-hidden`,`true`],[`d`,`M7 10l5 5 5-5z`],[`cdk-connected-overlay`,``,`cdkConnectedOverlayHasBackdrop`,``,`cdkConnectedOverlayBackdropClass`,`cdk-overlay-transparent-backdrop`,3,`detach`,`backdropClick`,`overlayKeydown`,`cdkConnectedOverlayDisableClose`,`cdkConnectedOverlayPanelClass`,`cdkConnectedOverlayScrollStrategy`,`cdkConnectedOverlayOrigin`,`cdkConnectedOverlayPositions`,`cdkConnectedOverlayWidth`,`cdkConnectedOverlayFlexibleDimensions`,`cdkConnectedOverlayUsePopover`],[1,`mat-mdc-select-min-line`],[`role`,`listbox`,`tabindex`,`-1`,1,`mat-mdc-select-panel`,`mdc-menu-surface`,`mdc-menu-surface--open`,3,`keydown`]],template:function(k,p){if(k&1&&(_D(r),yi(0,`div`,2,0),ih$1(`click`,function(){return p.open()}),yi(3,`div`,3),uD(4,a,2,1,`span`,4)(5,d,3,1,`span`,5),Fc$1(),yi(6,`div`,6)(7,`div`,7),Bu(),yi(8,`svg`,8),Xp$1(9,`path`,9),Fc$1()()()(),Bp$1(10,m,3,16,`ng-template`,10),ih$1(`detach`,function(){return p.close()})(`backdropClick`,function(){return p.close()})(`overlayKeydown`,function(K){return p._handleOverlayKeydown(K)})),k&2){let z=RD(1);sE(3),Kp(`id`,p._valueId),sE(),fD(p.empty?4:5),sE(6),Jp$1(`cdkConnectedOverlayDisableClose`,!0)(`cdkConnectedOverlayPanelClass`,p._overlayPanelClass)(`cdkConnectedOverlayScrollStrategy`,p._scrollStrategy)(`cdkConnectedOverlayOrigin`,p._preferredOverlayOrigin||z)(`cdkConnectedOverlayPositions`,p._positions)(`cdkConnectedOverlayWidth`,p._overlayWidth)(`cdkConnectedOverlayFlexibleDimensions`,!0)(`cdkConnectedOverlayUsePopover`,p._popoverLocation)}},dependencies:[Bn,Qr],styles:[`@keyframes _mat-select-enter {
  from {
    opacity: 0;
    transform: scaleY(0.8);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
@keyframes _mat-select-exit {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
.mat-mdc-select {
  display: inline-block;
  width: 100%;
  outline: none;
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  color: var(--%NS%mat-select-enabled-trigger-text-color, var(--%NS%mat-sys-on-surface));
  font-family: var(--%NS%mat-select-trigger-text-font, var(--%NS%mat-sys-body-large-font));
  line-height: var(--%NS%mat-select-trigger-text-line-height, var(--%NS%mat-sys-body-large-line-height));
  font-size: var(--%NS%mat-select-trigger-text-size, var(--%NS%mat-sys-body-large-size));
  font-weight: var(--%NS%mat-select-trigger-text-weight, var(--%NS%mat-sys-body-large-weight));
  letter-spacing: var(--%NS%mat-select-trigger-text-tracking, var(--%NS%mat-sys-body-large-tracking));
}

div.mat-mdc-select-panel {
  box-shadow: var(--%NS%mat-select-container-elevation-shadow, 0px 3px 1px -2px rgba(0, 0, 0, 0.2), 0px 2px 2px 0px rgba(0, 0, 0, 0.14), 0px 1px 5px 0px rgba(0, 0, 0, 0.12));
}

.mat-mdc-select-disabled {
  color: var(--%NS%mat-select-disabled-trigger-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-mdc-select-disabled .mat-mdc-select-placeholder {
  color: var(--%NS%mat-select-disabled-trigger-text-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}

.mat-mdc-select-trigger {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  position: relative;
  box-sizing: border-box;
  width: 100%;
}
.mat-mdc-select-disabled .mat-mdc-select-trigger {
  -webkit-user-select: none;
  user-select: none;
  cursor: default;
}

.mat-mdc-select-value {
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mat-mdc-select-value-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mat-mdc-select-arrow-wrapper {
  height: 24px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
}
.mat-form-field-appearance-fill .mdc-text-field--no-label .mat-mdc-select-arrow-wrapper {
  transform: none;
}

.mat-mdc-form-field .mat-mdc-select.mat-mdc-select-invalid .mat-mdc-select-arrow,
.mat-form-field-invalid:not(.mat-form-field-disabled) .mat-mdc-form-field-infix::after {
  color: var(--%NS%mat-select-invalid-arrow-color, var(--%NS%mat-sys-error));
}

.mat-mdc-select-arrow {
  width: 10px;
  height: 5px;
  position: relative;
  color: var(--%NS%mat-select-enabled-arrow-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-mdc-form-field.mat-focused .mat-mdc-select-arrow {
  color: var(--%NS%mat-select-focused-arrow-color, var(--%NS%mat-sys-primary));
}
.mat-mdc-form-field .mat-mdc-select.mat-mdc-select-disabled .mat-mdc-select-arrow {
  color: var(--%NS%mat-select-disabled-arrow-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) 38%, transparent));
}
.mat-select-open .mat-mdc-select-arrow {
  transform: rotate(180deg);
}
.mat-form-field-animations-enabled .mat-mdc-select-arrow {
  transition: transform 80ms linear;
}
.mat-mdc-select-arrow svg {
  fill: currentColor;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
@media (forced-colors: active) {
  .mat-mdc-select-arrow svg {
    fill: CanvasText;
  }
  .mat-mdc-select-disabled .mat-mdc-select-arrow svg {
    fill: GrayText;
  }
}

div.mat-mdc-select-panel {
  width: 100%;
  max-height: 275px;
  outline: 0;
  overflow: auto;
  padding: 8px 0;
  box-sizing: border-box;
  transform-origin: top center;
  border-radius: 0 0 4px 4px;
  position: relative;
  background-color: var(--%NS%mat-select-panel-background-color, var(--%NS%mat-sys-surface-container));
}
.mat-mdc-select-panel-above div.mat-mdc-select-panel {
  border-radius: 4px 4px 0 0;
  transform-origin: bottom center;
}
@media (forced-colors: active) {
  div.mat-mdc-select-panel {
    outline: solid 1px;
  }
}

.mat-select-panel-animations-enabled {
  animation: _mat-select-enter 120ms cubic-bezier(0, 0, 0.2, 1) forwards;
}
.mat-select-panel-animations-enabled.mat-select-panel-exit {
  animation: _mat-select-exit 100ms linear forwards;
}

.mat-mdc-select-placeholder {
  transition: color 400ms 133.3333333333ms cubic-bezier(0.25, 0.8, 0.25, 1);
  color: var(--%NS%mat-select-placeholder-text-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-mdc-form-field:not(.mat-form-field-animations-enabled) .mat-mdc-select-placeholder, ._mat-animation-noopable .mat-mdc-select-placeholder {
  transition: none;
}
.mat-form-field-hide-placeholder .mat-mdc-select-placeholder {
  color: transparent;
  -webkit-text-fill-color: transparent;
  transition: none;
  display: block;
}

.mat-mdc-form-field-type-mat-select:not(.mat-form-field-disabled) .mat-mdc-text-field-wrapper {
  cursor: pointer;
}
.mat-mdc-form-field-type-mat-select.mat-form-field-appearance-fill .mat-mdc-floating-label {
  max-width: calc(100% - 18px);
}
.mat-mdc-form-field-type-mat-select.mat-form-field-appearance-fill .mdc-floating-label--float-above {
  max-width: calc(100% / 0.75 - 24px);
}
.mat-mdc-form-field-type-mat-select.mat-form-field-appearance-outline .mdc-notched-outline__notch {
  max-width: calc(100% - 60px);
}
.mat-mdc-form-field-type-mat-select.mat-form-field-appearance-outline .mdc-text-field--label-floating .mdc-notched-outline__notch {
  max-width: calc(100% - 24px);
}

.mat-mdc-select-min-line:empty::before {
  content: " ";
  white-space: pre;
  width: 1px;
  display: inline-block;
  visibility: hidden;
}

.mat-form-field-appearance-fill .mat-mdc-select-arrow-wrapper {
  transform: var(--%NS%mat-select-arrow-transform, translateY(-8px));
}
`],encapsulation:2})})()}return n})();var fE=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[`mat-select-trigger`]],features:[hw([{provide:cm,useExisting:n}])]})}return n})();var gE=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[Ke,fs,te,Nt,cr,fs]})}return n})();var tf=new S(`mat-progress-spinner-default-options`,{providedIn:`root`,factory:()=>({diameter:mm})});var mm=100;var nf=10;var um=(()=>{class n{_elementRef=I(Dr);_noopAnimations;get color(){return this._color||this._defaultColor}set color(e){this._color=e}_color;_defaultColor=`primary`;_determinateCircle;constructor(){let e=I(tf),t=La(),r=this._elementRef.nativeElement;this._noopAnimations=t===`di-disabled`&&!!e&&!e._forceAnimations,this.mode=r.nodeName.toLowerCase()===`mat-spinner`?`indeterminate`:`determinate`,!this._noopAnimations&&t===`reduced-motion`&&r.classList.add(`mat-progress-spinner-reduced-motion`),e&&(e.color&&(this.color=this._defaultColor=e.color),e.diameter&&(this.diameter=e.diameter),e.strokeWidth&&(this.strokeWidth=e.strokeWidth))}mode;get value(){return this.mode===`determinate`?this._value:0}set value(e){this._value=Math.max(0,Math.min(100,e||0))}_value=0;get diameter(){return this._diameter}set diameter(e){this._diameter=e||0}_diameter=mm;get strokeWidth(){return this._strokeWidth??this.diameter/10}set strokeWidth(e){this._strokeWidth=e||0}_strokeWidth;_circleRadius(){return(this.diameter-nf)/2}_viewBox(){let e=this._circleRadius()*2+this.strokeWidth;return`0 0 ${e} ${e}`}_strokeCircumference(){return 2*Math.PI*this._circleRadius()}_strokeDashOffset(){return this.mode===`determinate`?this._strokeCircumference()*(100-this._value)/100:null}_circleStrokeWidth(){return this.strokeWidth/this.diameter*100}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`determinateSpinner`];function t(r,o){if(r&1&&(Bu(),yi(0,`svg`,11),Xp$1(1,`circle`,12),Fc$1()),r&2){let a=TD();Kp(`viewBox`,a._viewBox()),sE(),mh$1(`stroke-dasharray`,a._strokeCircumference(),`px`)(`stroke-dashoffset`,a._strokeCircumference()/2,`px`)(`stroke-width`,a._circleStrokeWidth(),`%`),Kp(`r`,a._circleRadius())}}return LI({type:n,selectors:[[`mat-progress-spinner`],[`mat-spinner`]],viewQuery:function(o,a){if(o&1&&lh$1(e,5),o&2){let s;SD(s=xD())&&(a._determinateCircle=s.first)}},hostAttrs:[`role`,`progressbar`,`tabindex`,`-1`,1,`mat-mdc-progress-spinner`,`mdc-circular-progress`],hostVars:18,hostBindings:function(o,a){o&2&&(Kp(`aria-valuemin`,0)(`aria-valuemax`,100)(`aria-valuenow`,a.mode===`determinate`?a.value:null)(`mode`,a.mode),zD(`mat-`+a.color),mh$1(`width`,a.diameter,`px`)(`height`,a.diameter,`px`)(`--%NS%mat-progress-spinner-size`,a.diameter+`px`)(`--%NS%mat-progress-spinner-active-indicator-width`,a.diameter+`px`),yh$1(`_mat-animation-noopable`,a._noopAnimations)(`mdc-circular-progress--indeterminate`,a.mode===`indeterminate`))},inputs:{color:`color`,mode:`mode`,value:[2,`value`,`value`,C0],diameter:[2,`diameter`,`diameter`,C0],strokeWidth:[2,`strokeWidth`,`strokeWidth`,C0]},exportAs:[`matProgressSpinner`],decls:14,vars:11,consts:[[`circle`,``],[`determinateSpinner`,``],[`aria-hidden`,`true`,1,`mdc-circular-progress__determinate-container`],[`xmlns`,`http://www.w3.org/2000/svg`,`focusable`,`false`,1,`mdc-circular-progress__determinate-circle-graphic`],[`cx`,`50%`,`cy`,`50%`,1,`mdc-circular-progress__determinate-circle`],[`aria-hidden`,`true`,1,`mdc-circular-progress__indeterminate-container`],[1,`mdc-circular-progress__spinner-layer`],[1,`mdc-circular-progress__circle-clipper`,`mdc-circular-progress__circle-left`],[3,`ngTemplateOutlet`],[1,`mdc-circular-progress__gap-patch`],[1,`mdc-circular-progress__circle-clipper`,`mdc-circular-progress__circle-right`],[`xmlns`,`http://www.w3.org/2000/svg`,`focusable`,`false`,1,`mdc-circular-progress__indeterminate-circle-graphic`],[`cx`,`50%`,`cy`,`50%`]],template:function(o,a){if(o&1&&(Bp$1(0,t,2,8,`ng-template`,null,0,Sw),yi(2,`div`,2,1),Bu(),yi(4,`svg`,3),Xp$1(5,`circle`,4),Fc$1()(),$u(),yi(6,`div`,5)(7,`div`,6)(8,`div`,7),nh$1(9,8),Fc$1(),yi(10,`div`,9),nh$1(11,8),Fc$1(),yi(12,`div`,10),nh$1(13,8),Fc$1()()()),o&2){let s=RD(1);sE(4),Kp(`viewBox`,a._viewBox()),sE(),mh$1(`stroke-dasharray`,a._strokeCircumference(),`px`)(`stroke-dashoffset`,a._strokeDashOffset(),`px`)(`stroke-width`,a._circleStrokeWidth(),`%`),Kp(`r`,a._circleRadius()),sE(4),Jp$1(`ngTemplateOutlet`,s),sE(2),Jp$1(`ngTemplateOutlet`,s),sE(2),Jp$1(`ngTemplateOutlet`,s)}},dependencies:[Ci],styles:[`.mat-mdc-progress-spinner {
  --%NS%mat-progress-spinner-animation-multiplier: 1;
  display: block;
  overflow: hidden;
  line-height: 0;
  position: relative;
  direction: ltr;
  transition: opacity 250ms cubic-bezier(0.4, 0, 0.6, 1);
}
.mat-mdc-progress-spinner circle {
  stroke-width: var(--%NS%mat-progress-spinner-active-indicator-width, 4px);
}
.mat-mdc-progress-spinner._mat-animation-noopable, .mat-mdc-progress-spinner._mat-animation-noopable .mdc-circular-progress__determinate-circle {
  transition: none !important;
}
.mat-mdc-progress-spinner._mat-animation-noopable .mdc-circular-progress__indeterminate-circle-graphic,
.mat-mdc-progress-spinner._mat-animation-noopable .mdc-circular-progress__spinner-layer,
.mat-mdc-progress-spinner._mat-animation-noopable .mdc-circular-progress__indeterminate-container {
  animation: none !important;
}
.mat-mdc-progress-spinner._mat-animation-noopable .mdc-circular-progress__indeterminate-container circle {
  stroke-dasharray: 0 !important;
}
@media (forced-colors: active) {
  .mat-mdc-progress-spinner .mdc-circular-progress__indeterminate-circle-graphic,
  .mat-mdc-progress-spinner .mdc-circular-progress__determinate-circle {
    stroke: currentColor;
    stroke: CanvasText;
  }
}

.mat-progress-spinner-reduced-motion {
  --%NS%mat-progress-spinner-animation-multiplier: 1.25;
}

.mdc-circular-progress__determinate-container,
.mdc-circular-progress__indeterminate-circle-graphic,
.mdc-circular-progress__indeterminate-container,
.mdc-circular-progress__spinner-layer {
  position: absolute;
  width: 100%;
  height: 100%;
}

.mdc-circular-progress__determinate-container {
  transform: rotate(-90deg);
}
.mdc-circular-progress--indeterminate .mdc-circular-progress__determinate-container {
  opacity: 0;
}

.mdc-circular-progress__indeterminate-container {
  font-size: 0;
  letter-spacing: 0;
  white-space: nowrap;
  opacity: 0;
}
.mdc-circular-progress--indeterminate .mdc-circular-progress__indeterminate-container {
  opacity: 1;
  animation: mdc-circular-progress-container-rotate calc(1568.2352941176ms * var(--%NS%mat-progress-spinner-animation-multiplier)) linear infinite;
}

.mdc-circular-progress__determinate-circle-graphic,
.mdc-circular-progress__indeterminate-circle-graphic {
  fill: transparent;
}

.mat-mdc-progress-spinner .mdc-circular-progress__determinate-circle,
.mat-mdc-progress-spinner .mdc-circular-progress__indeterminate-circle-graphic {
  stroke: var(--%NS%mat-progress-spinner-active-indicator-color, var(--%NS%mat-sys-primary));
}
@media (forced-colors: active) {
  .mat-mdc-progress-spinner .mdc-circular-progress__determinate-circle,
  .mat-mdc-progress-spinner .mdc-circular-progress__indeterminate-circle-graphic {
    stroke: CanvasText;
  }
}

.mdc-circular-progress__determinate-circle {
  transition: stroke-dashoffset 500ms cubic-bezier(0, 0, 0.2, 1);
}

.mdc-circular-progress__gap-patch {
  position: absolute;
  top: 0;
  left: 47.5%;
  box-sizing: border-box;
  width: 5%;
  height: 100%;
  overflow: hidden;
}

.mdc-circular-progress__gap-patch .mdc-circular-progress__indeterminate-circle-graphic {
  left: -900%;
  width: 2000%;
  transform: rotate(180deg);
}
.mdc-circular-progress__circle-clipper .mdc-circular-progress__indeterminate-circle-graphic {
  width: 200%;
}
.mdc-circular-progress__circle-right .mdc-circular-progress__indeterminate-circle-graphic {
  left: -100%;
}
.mdc-circular-progress--indeterminate .mdc-circular-progress__circle-left .mdc-circular-progress__indeterminate-circle-graphic {
  animation: mdc-circular-progress-left-spin calc(1333ms * var(--%NS%mat-progress-spinner-animation-multiplier)) cubic-bezier(0.4, 0, 0.2, 1) infinite both;
}
.mdc-circular-progress--indeterminate .mdc-circular-progress__circle-right .mdc-circular-progress__indeterminate-circle-graphic {
  animation: mdc-circular-progress-right-spin calc(1333ms * var(--%NS%mat-progress-spinner-animation-multiplier)) cubic-bezier(0.4, 0, 0.2, 1) infinite both;
}

.mdc-circular-progress__circle-clipper {
  display: inline-flex;
  position: relative;
  width: 50%;
  height: 100%;
  overflow: hidden;
}

.mdc-circular-progress--indeterminate .mdc-circular-progress__spinner-layer {
  animation: mdc-circular-progress-spinner-layer-rotate calc(5332ms * var(--%NS%mat-progress-spinner-animation-multiplier)) cubic-bezier(0.4, 0, 0.2, 1) infinite both;
}

@keyframes mdc-circular-progress-container-rotate {
  to {
    transform: rotate(360deg);
  }
}
@keyframes mdc-circular-progress-spinner-layer-rotate {
  12.5% {
    transform: rotate(135deg);
  }
  25% {
    transform: rotate(270deg);
  }
  37.5% {
    transform: rotate(405deg);
  }
  50% {
    transform: rotate(540deg);
  }
  62.5% {
    transform: rotate(675deg);
  }
  75% {
    transform: rotate(810deg);
  }
  87.5% {
    transform: rotate(945deg);
  }
  100% {
    transform: rotate(1080deg);
  }
}
@keyframes mdc-circular-progress-left-spin {
  from {
    transform: rotate(265deg);
  }
  50% {
    transform: rotate(130deg);
  }
  to {
    transform: rotate(265deg);
  }
}
@keyframes mdc-circular-progress-right-spin {
  from {
    transform: rotate(-265deg);
  }
  50% {
    transform: rotate(-130deg);
  }
  to {
    transform: rotate(-265deg);
  }
}
`],encapsulation:2})})()}return n})();var ME=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[te]})}return n})();var Oo=(n,...i)=>n+(n.includes(`__`)?`/`:`__`)+i.join(`/`);var li=n=>{let i=n.split(/\/|__/).filter(e=>e!==``);return i[i.length-1]};var hm=n=>{let i=n.split(`/`);if(i[i.length-1].includes(`__`)){let e=i[i.length-1].split(`__`);return[i.slice(0,-1).join(`/`),e[e.length-1]]}return[i.slice(0,-1).join(`/`),i[i.length-1]]};var bs=`__lazy__`;var Sn=n=>!!n&&typeof n==`object`&&!Array.isArray(n)&&n[bs]===!0;var pm=(()=>{class n{dialogRef;data;constructor(e,t){this.dialogRef=e,this.data=t}static ɵfac=function(t){return new(t||n)(Mr(gt),Mr(vn))};static ɵcmp=LI({type:n,selectors:[[`app-error`,8,`dialog`]],standalone:!1,decls:8,vars:1,consts:[[`mat-dialog-title`,``],[`mat-dialog-content`,``],[`mat-dialog-actions`,``],[`mat-button`,``,`cdkFocusInitial`,``,3,`click`]],template:function(t,r){t&1&&(yi(0,`h1`,0),rw(1,`Error`),Fc$1(),yi(2,`div`,1)(3,`p`),rw(4),Fc$1()(),yi(5,`div`,2)(6,`button`,3),ih$1(`click`,function(){return r.dialogRef.close()}),rw(7,`OK`),Fc$1()()),t&2&&(sE(4),_h$1(r.data.message))},dependencies:[Qt,Gn,Yn,Wn],styles:[`div[mat-dialog-content][_ngcontent-%COMP%]{min-width:300px}`],changeDetection:1})}return n})();var Fo=class{dialog;_implPromise=null;_impl=null;openedResource$=new Pn$1(null);openedResourcePath$=new Pn$1(null);recentFiles$=new Pn$1([]);version$=new Pn$1(``);onFileOpened$=new te$1;onAppendChanges$=new te$1;conversionProgress$=new Pn$1([0,0]);constructor(i){this.dialog=i}getImpl(){return Yt$1(this,null,function*(){return this._impl?this._impl:(this._implPromise||(this._implPromise=this.initImpl(),this._implPromise.then(i=>{this._impl=i,this._implPromise=null,this._impl.openedResource$.subscribe(e=>{this.openedResource$.getValue()!==e&&this.openedResource$.next(e)}),this._impl.openedResourcePath$.subscribe(e=>{this.openedResourcePath$.getValue()!==e&&this.openedResourcePath$.next(e)}),this._impl.recentFiles$.subscribe(e=>{this.recentFiles$.getValue()!==e&&this.recentFiles$.next(e)}),this._impl.version$.subscribe(e=>{this.version$.getValue()!==e&&this.version$.next(e)}),this._impl.onFileOpened$.subscribe(()=>{this.onFileOpened$.next()}),this._impl.apiError$.subscribe(e=>{this.dialog.open(pm,{data:{message:e}})}),this._impl.onAppendChanges$.subscribe(e=>{this.onAppendChanges$.next(e)}),this._impl.conversionProgress$.subscribe(e=>{this.conversionProgress$.getValue()!==e&&this.conversionProgress$.next(e)})})),this._implPromise)})}openFile(i,e=!1){return Yt$1(this,null,function*(){return(yield this.getImpl()).openFile(i,e)})}openFileWithSystemApp(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).openFileWithSystemApp(i)})}openUrl(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).openUrl(i)})}findFiles(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).findFiles(i)})}saveFile(){return Yt$1(this,null,function*(){return(yield this.getImpl()).saveFile()})}createNewFile(i,e){return Yt$1(this,null,function*(){return(yield this.getImpl()).createNewFile(i,e)})}closeFile(){return Yt$1(this,null,function*(){return(yield this.getImpl()).closeFile()})}retrieveValue(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).retrieveValue(i)})}loadLazyPart(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).loadLazyPart(i)})}runCustomAction(i,e,t){return Yt$1(this,null,function*(){return(yield this.getImpl()).runCustomAction(i,e,t)})}getNewItemData(t){return Yt$1(this,arguments,function*(i,e={}){return(yield this.getImpl()).getNewItemData(i,e)})}spatialHandles(i,e,t){return Yt$1(this,null,function*(){return(yield this.getImpl()).spatialHandles(i,e,t)})}spatialMove(i,e,t){return Yt$1(this,null,function*(){return(yield this.getImpl()).spatialMove(i,e,t)})}serializeChunks(i,e){return Yt$1(this,null,function*(){return(yield this.getImpl()).serializeChunks(i,e)})}paletteUsage(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).paletteUsage(i)})}archiveImageStats(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).archiveImageStats(i)})}getTrailingOptionalFieldData(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).getTrailingOptionalFieldData(i)})}serializeResource(r){return Yt$1(this,arguments,function*(i,e=null,t={}){return(yield this.getImpl()).serializeResource(i,e,t)})}serializeResourceSilent(r){return Yt$1(this,arguments,function*(i,e=null,t={}){return(yield this.getImpl()).serializeResourceSilent(i,e,t)})}deserializeResource(r,o){return Yt$1(this,arguments,function*(i,e,t={}){return(yield this.getImpl()).deserializeResource(i,e,t)})}newImagesFromFiles(i,e){return Yt$1(this,null,function*(){return(yield this.getImpl()).newImagesFromFiles(i,e)})}convertFiles(i,e,t){return Yt$1(this,null,function*(){return(yield this.getImpl()).convertFiles(i,e,t)})}getGeneralConfig(){return Yt$1(this,null,function*(){return(yield this.getImpl()).getGeneralConfig()})}getConversionConfig(i=null){return Yt$1(this,null,function*(){return(yield this.getImpl()).getConversionConfig(i)})}patchGeneralConfig(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).patchGeneralConfig(i)})}patchConversionConfig(i,e=null){return Yt$1(this,null,function*(){return(yield this.getImpl()).patchConversionConfig(i,e)})}getConversionPresets(){return Yt$1(this,null,function*(){return(yield this.getImpl()).getConversionPresets()})}selectConversionPreset(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).selectConversionPreset(i)})}createConversionPreset(i,e){return Yt$1(this,null,function*(){return(yield this.getImpl()).createConversionPreset(i,e)})}deleteConversionPreset(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).deleteConversionPreset(i)})}testExecutable(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).testExecutable(i)})}detectExecutablePath(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).detectExecutablePath(i)})}isFirstRun(){return Yt$1(this,null,function*(){return(yield this.getImpl()).isFirstRun()})}getRevisions(){return Yt$1(this,null,function*(){return(yield this.getImpl()).getRevisions()})}getChanges(){return Yt$1(this,null,function*(){return(yield this.getImpl()).getChanges()})}onFeUpdate(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).onFeUpdate(i)})}openFileDialog(){return Yt$1(this,arguments,function*(i=!1,e=[]){return(yield this.getImpl()).openFileDialog(i,e)})}saveFileDialog(i){return Yt$1(this,null,function*(){return(yield this.getImpl()).saveFileDialog(i)})}selectDirectoryDialog(){return Yt$1(this,null,function*(){return(yield this.getImpl()).selectDirectoryDialog()})}syncRecentFiles(){return Yt$1(this,null,function*(){return(yield this.getImpl()).syncRecentFiles()})}syncVersion(){return Yt$1(this,null,function*(){return(yield this.getImpl()).syncVersion()})}};var Po=(()=>{class n extends Fo{ngZone;initImpl(){return Yt$1(this,null,function*(){return import(`./chunk-BiBdzTwd.js`).then(e=>new e.ApiDelegateImplService(this.ngZone))})}constructor(e,t){super(t),this.ngZone=e}static ɵfac=function(t){return new(t||n)(ae(z),ae(Lt))};static ɵprov=K({token:n,factory:n.ɵfac})}return n})();var ci=class n{static locateId(i,e,t=!1){if(!i)throw new Error(`No resource opened`);if(i.id===e)throw new Error(`Cannot apply change to the top-level resource`);let r=e.substring(i.id.length).replace(`__`,`/`).split(`/`).filter(a=>a),o=i.data;for(let a of r){if(Sn(o))return null;o=o[a]||o[+a]}return Sn(o)&&!t?null:o}static setResourceValue(i,e,t){let[r,o]=hm(e),a=n.locateId(i,r,!0);a===null||Sn(a)&&!(o in a)||(a[o]===void 0&&a[+o]!==void 0?a[+o]=t:a[o]=t)}static applyChange(i,e){let t=i.openedResource$.getValue();if(e.op===`set`)return n.setResourceValue(t,e.id,e.newValue),[e.id];if(e.op==`array_insert`)return n.locateId(t,e.id)?.splice(e.index,0,e.value),[e.id];if(e.op==`array_remove`)return n.locateId(t,e.id)?.splice(e.index,1),[e.id];if(e.op==`array_swap`){let r=n.locateId(t,e.id);return r&&([r[e.indexA],r[e.indexB]]=[r[e.indexB],r[e.indexA]]),[e.id]}else{if(e.op==`binary_delta`)return n.locateId(t,e.id)?.$bytes?.splice(e.index,e.oldPart.length,...e.newPart),[e.id];if(e.op==`bundle`){let r=new Set;for(let o of e.changes)for(let a of n.applyChange(i,o))r.add(a);return Array.from(r)}else throw new Error(`Unknown change operation: `+e.op)}}static revertChange(i,e){let t=i.openedResource$.getValue();if(e.op===`set`)return n.setResourceValue(t,e.id,e.oldValue),[e.id];if(e.op==`array_insert`)return n.locateId(t,e.id)?.splice(e.index,1),[e.id];if(e.op==`array_remove`)return n.locateId(t,e.id)?.splice(e.index,0,e.oldValue),[e.id];if(e.op==`array_swap`){let r=n.locateId(t,e.id);return r&&([r[e.indexA],r[e.indexB]]=[r[e.indexB],r[e.indexA]]),[e.id]}else{if(e.op==`binary_delta`)return n.locateId(t,e.id)?.$bytes?.splice(e.index,e.newPart.length,...e.oldPart),[e.id];if(e.op==`bundle`){let r=new Set;for(let o=e.changes.length-1;o>=0;o--){let a=e.changes[o];for(let s of n.revertChange(i,a))r.add(s)}return Array.from(r)}else throw new Error(`Unknown change operation: `+e.op)}}};var Lo=(()=>{class n{api;ngZone;_changes=[];_localRevision=0;_fileRevision=0;_cdrSubscribers={};_pendingCalls=new Set;change$=new te$1;hasUnsavedChanges$=new Pn$1(!1);isUndoAvailable$=new Pn$1(!1);isRedoAvailable$=new Pn$1(!1);get changes(){return this._changes}get localRevision(){return this._localRevision}get fileRevision(){return this._fileRevision}constructor(e,t){this.api=e,this.ngZone=t,this.api.onAppendChanges$.subscribe(([r])=>{this._localRevision<this._changes.length&&this._changes.splice(this._localRevision),this._changes.push(...r),this._localRevision=this._changes.length;let o=new Set;for(let a of r)for(let s of ci.applyChange(this.api,a))o.add(s);this.notifyUi(Array.from(o)),this.track(this.refreshRevisions()).then()}),this.api.onFileOpened$.subscribe(()=>{this.clear()})}syncState(){return Yt$1(this,null,function*(){let e=yield this.api.getChanges(),[t,r]=yield this.api.getRevisions();this._changes=e,this._fileRevision=t,this._localRevision=r,this.hasUnsavedChanges$.next(this._fileRevision!==this._localRevision),this.isUndoAvailable$.next(this._localRevision>0),this.isRedoAvailable$.next(this._localRevision<this._changes.length)})}refreshRevisions(){return Yt$1(this,null,function*(){let[e,t]=yield this.api.getRevisions();(this._fileRevision!==e||this._localRevision!==t)&&console.warn(`Changes revisions out of sync`),this._fileRevision=e,this._localRevision=t,this.hasUnsavedChanges$.next(this._fileRevision!==this._localRevision),this.isUndoAvailable$.next(this._localRevision>0),this.isRedoAvailable$.next(this._localRevision<this._changes.length)})}appendChanges(...e){return Yt$1(this,null,function*(){let t=this.changes.length-this._localRevision;t>0&&this._changes.splice(this._localRevision),this._changes.push(...e),this._localRevision=this.changes.length;let r=new Set;for(let o of e)for(let a of ci.applyChange(this.api,o))r.add(a);this.notifyUi(Array.from(r)),yield this.track(this.api.onFeUpdate({newLocalRevision:this._localRevision,newChanges:e,poppedChanges:t})),this.track(this.refreshRevisions()).then()})}track(e){return this._pendingCalls.add(e),e.finally(()=>this._pendingCalls.delete(e)).catch(()=>{}),e}settled(){return Yt$1(this,null,function*(){for(;this._pendingCalls.size>0;)yield Promise.allSettled(Array.from(this._pendingCalls))})}clear(){this._changes=[],this._localRevision=0,this._fileRevision=0,this.hasUnsavedChanges$.next(!1),this.isUndoAvailable$.next(!1),this.isRedoAvailable$.next(!1)}undo(){return Yt$1(this,null,function*(){if(this._localRevision===0)return;let e=ci.revertChange(this.api,this.changes[this._localRevision-1]);this._localRevision-=1,yield this.track(this.api.onFeUpdate({newLocalRevision:this._localRevision,newChanges:[],poppedChanges:0})),yield this.track(this.refreshRevisions()),this.notifyUi(e)})}redo(){return Yt$1(this,null,function*(){if(this._localRevision===this._changes.length)return;let e=ci.applyChange(this.api,this.changes[this._localRevision]);this._localRevision+=1,yield this.track(this.api.onFeUpdate({newLocalRevision:this._localRevision,newChanges:[],poppedChanges:0})),yield this.track(this.refreshRevisions()),this.notifyUi(e)})}notifyUi(e){let t=new Set;for(let r of e){let o=Object.keys(this._cdrSubscribers).filter(a=>r.startsWith(a)).reduce((a,s)=>!r.startsWith(s)||a&&a.length>s.length?a:s,null);if(o!==null)for(let a of this._cdrSubscribers[o])t.add(a)}this.ngZone.run(()=>{for(let r of t)r.onExternalChanges()});for(let r of e)this.change$.next(r)}subscribeComponent(e,t){this._cdrSubscribers[e]?this._cdrSubscribers[e].push(t):this._cdrSubscribers[e]=[t]}unsubscribeComponent(e,t){this._cdrSubscribers[e]&&(this._cdrSubscribers[e]=this._cdrSubscribers[e].filter(r=>r!==t),this._cdrSubscribers[e].length===0&&delete this._cdrSubscribers[e])}static ɵfac=function(t){return new(t||n)(ae(Po),ae(z))};static ɵprov=K({token:n,factory:n.ɵfac,providedIn:`root`})}return n})();var en=(()=>{class n{api;changes;resource$=new Pn$1(null);error$=new Pn$1(null);customActionRunning$=new Pn$1(!1);isSaving$=new Pn$1(!1);hideHiddenFields$=new Pn$1(!0);focusedResourceId$=new Pn$1(null);lazyLoads=new Map;constructor(e,t){this.api=e,this.changes=t,this.api.getGeneralConfig().then(r=>{this.hideHiddenFields$.next(!r.show_hidden_fields),this.hideHiddenFields$.subscribe(o=>Yt$1(this,null,function*(){(yield this.api.getGeneralConfig()).show_hidden_fields!==!o&&(yield this.api.patchGeneralConfig({show_hidden_fields:!o}))}))}),this.api.openedResource$.subscribe(r=>{this.changes.syncState().then(),r?.data.error_class?(this.error$.next(r),this.resource$.next(null)):r?.schema?(this.resource$.next(r),this.error$.next(null)):(this.resource$.next(null),this.error$.next(null))})}ensureLoaded(e,t){return Yt$1(this,null,function*(){if(!Sn(t))return;let r=this.lazyLoads.get(e);return r||(r=this.api.loadLazyPart(e).then(o=>{if(Sn(t)){for(let a of Object.keys(t))delete t[a];Object.assign(t,o),delete t[bs]}}),this.lazyLoads.set(e,r),r.finally(()=>this.lazyLoads.delete(e)).catch(()=>{})),r})}runCustomAction(e,t,r){return Yt$1(this,null,function*(){this.customActionRunning$.next(!0);try{yield this.api.runCustomAction(e,t,r)}finally{this.customActionRunning$.next(!1)}})}deserializeResource(o,a){return Yt$1(this,arguments,function*(e,t,r={}){return(yield this.api.deserializeResource(e,t,r))?.report??null})}reloadResource(){return Yt$1(this,null,function*(){let e=this.api.openedResourcePath$.getValue();e&&(yield this.api.openFile(e,!0),this.changes.syncState().then())})}saveResource(){return Yt$1(this,null,function*(){this.isSaving$.next(!0);try{yield this.changes.settled();let e=yield this.api.saveFile();return yield this.changes.syncState(),e}finally{this.isSaving$.next(!1)}})}getNewItemData(r){return Yt$1(this,arguments,function*(e,t={}){return this.api.getNewItemData(e,t)})}getTrailingOptionalFieldData(e){return Yt$1(this,null,function*(){return this.api.getTrailingOptionalFieldData(e)})}static ɵfac=function(t){return new(t||n)(ae(Po),ae(Lo))};static ɵprov=K({token:n,factory:n.ɵfac,providedIn:`root`})}return n})();var gm=(()=>{class n{mainService=I(en);changes=I(Lo);_resourceId;_resourceName;_resourceSchema;_resourceData;_resourceDescription;_hideName;_hideBlockActions;_disabled;get resourceId(){return this._resourceId}get resourceName(){return this._resourceName}get resourceSchema(){return this._resourceSchema}get resourceData(){return this._resourceData}get resourceDescription(){return this._resourceDescription}get hideName(){return this._hideName}get hideBlockActions(){return this._hideBlockActions}get disabled(){return this._disabled}set resourceId(e){this._resourceId=e}set resourceName(e){this._resourceName=e}set resourceSchema(e){this._resourceSchema=e}set resourceData(e){this._resourceData=e}set resourceDescription(e){this._resourceDescription=e}set hideName(e){this._hideName=e}set hideBlockActions(e){this._hideBlockActions=e}set disabled(e){this._disabled=e}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,inputs:{resourceId:`resourceId`,resourceName:`resourceName`,resourceSchema:`resourceSchema`,resourceData:`resourceData`,resourceDescription:`resourceDescription`,hideName:`hideName`,hideBlockActions:`hideBlockActions`,disabled:`disabled`}})}return n})();var JE=(()=>{class n extends gm{cdr=I(w0);get resourceId(){return super.resourceId}set resourceId(e){if(super.resourceId!==e){if(super.resourceId)for(let t of this.subscriptionKeys(super.resourceId))this.changes.unsubscribeComponent(t,this);if(super.resourceId=e,super.resourceId)for(let t of this.subscriptionKeys(super.resourceId))this.changes.subscribeComponent(t,this)}}ngOnDestroy(){if(this._resourceId)for(let e of this.subscriptionKeys(this._resourceId))this.changes.unsubscribeComponent(e,this)}onExternalChanges(){this.cdr.markForCheck()}subscriptionKeys(e){return[e]}emitNewChange(e){this.changes.appendChanges($({timestamp:Date.now(),id:this.resourceId},e)).then()}onValueSet(e,...t){let r=this.resourceData;for(let o of t){if(r==null)break;r=r[o]}this.emitNewChange({op:`set`,id:Oo(this.resourceId,...t),oldValue:r,newValue:e})}onFocus(...e){this.resourceId&&this.mainService.focusedResourceId$.next(Oo(this.resourceId,...e))}onBlur(...e){this.resourceId&&this.mainService.focusedResourceId$.getValue()?.startsWith(Oo(this.resourceId,...e))&&this.mainService.focusedResourceId$.next(null)}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,inputs:{resourceId:`resourceId`},features:[Vp$1]})}return n})();var eM=(()=>{class n extends gm{onValueSet(e){this.changes.appendChanges({timestamp:Date.now(),op:`set`,id:this.resourceId,oldValue:this.resourceData??null,newValue:e}).then()}onFocus(){this.resourceId&&this.mainService.focusedResourceId$.next(this.resourceId)}onBlur(){this.mainService.focusedResourceId$.getValue()===this.resourceId&&this.mainService.focusedResourceId$.next(null)}static ɵfac=(()=>{let e;return function(r){return(e||(e=Ty(n)))(r||n)}})();static ɵdir=VI({type:n,features:[Vp$1]})}return n})();function of(n,i){if(n&1&&(yi(0,`mat-checkbox`,6),qE(),rw(1),Fc$1()),n&2){let e=TD(2).$implicit;Jp$1(`formControlName`,e.id),zE(),sE(),$c$1(` `,e.title,` `)}}function af(n,i){if(n&1&&(yi(0,`mat-option`,12),rw(1),Fc$1()),n&2){let e=i.$implicit;Jp$1(`value`,e),sE(),$c$1(` `,e,` `)}}function sf(n,i){if(n&1&&(yi(0,`mat-select`,9),qE(),gD(1,af,2,2,`mat-option`,12,hD),Fc$1()),n&2){let e=TD(3).$implicit;Jp$1(`formControlName`,e.id),zE(),sE(),mD(e.choices)}}function lf(n,i){if(n&1&&(yi(0,`input`,10),qE(),Fc$1()),n&2){let e=TD(3).$implicit,t=TD();Jp$1(`id`,e.id)(`type`,t.getInputType(e.type))(`formControlName`,e.id)(`placeholder`,e.type===`file_output`?`Enter output file path`:e.type===`number`?`Enter a number`:`Enter text`),zE()}}function cf(n,i){if(n&1&&(yi(0,`mat-error`),rw(1),Fc$1()),n&2){let e=TD(3).$implicit;sE(),$c$1(` `,e.title,` is required`)}}function df(n,i){n&1&&(yi(0,`mat-error`),rw(1,` Please enter a valid number`),Fc$1())}function mf(n,i){if(n&1){let e=wD();yi(0,`button`,13),ih$1(`click`,function(){Mu$1(e);let r=TD(3).$implicit,o=TD();return Su$1(o.selectOutputFile(r))}),yi(1,`mat-icon`),rw(2,`folder_open`),Fc$1()()}}function uf(n,i){if(n&1&&(yi(0,`div`,7)(1,`mat-form-field`,8)(2,`mat-label`),rw(3),Fc$1(),uD(4,sf,3,1,`mat-select`,9),uD(5,lf,1,4,`input`,10),uD(6,cf,2,1,`mat-error`),uD(7,df,2,0,`mat-error`),Fc$1(),uD(8,mf,3,0,`button`,11),Fc$1()),n&2){let e=TD(2).$implicit,t=TD();sE(3),_h$1(e.title),sE(),fD(e.type===`enum_string`?4:-1),sE(),fD(e.type!==`enum_string`?5:-1),sE(),fD(t.argsForm.get(e.id)?.hasError(`required`)?6:-1),sE(),fD(t.argsForm.get(e.id)?.hasError(`pattern`)&&e.type===`number`?7:-1),sE(),fD(e.type===`file_output`?8:-1)}}function hf(n,i){if(n&1&&(uD(0,of,2,2,`mat-checkbox`,6),uD(1,uf,9,6,`div`,7)),n&2){let e=TD().$implicit;fD(e.type===`bool`?0:-1),sE(),fD(e.type!==`bool`?1:-1)}}function pf(n,i){if(n&1&&uD(0,hf,2,2),n&2){let e=i.$implicit,t=TD();fD(t.data.formPatch?.[e.id]===void 0&&t.isArgVisible(e)?0:-1)}}var bm=(()=>{class n{dialogRef;fb;data;mainService;argsForm;argValidators=new Map;constructor(e,t,r,o){this.dialogRef=e,this.fb=t,this.data=r,this.mainService=o;let a={};for(let s of r.action.args){if(r.formPatch?.[s.id]){a[s.id]=[r.formPatch[s.id]];continue}let c=[Ct.required];s.type===`number`&&c.push(Ct.pattern(/^\d+(\.\d+)?$/)),this.argValidators.set(s.id,c);let d=``;s.type===`enum_string`?d=s.default||s.choices[0]||``:s.type===`bool`?d=!!s.default:s.type===`number`?d=s.default===void 0?``:s.default.toString():s.type===`string`&&(d=s.default===void 0?``:s.default),a[s.id]=[d,s.visible_when?[]:c]}this.argsForm=this.fb.group(a),this.updateConditionalValidators(),this.argsForm.valueChanges.subscribe(()=>this.updateConditionalValidators())}isArgVisible(e){return!e.visible_when||this.argsForm.get(e.visible_when.arg)?.value===e.visible_when.value}updateConditionalValidators(){for(let e of this.data.action.args){if(!e.visible_when)continue;let t=this.argsForm.get(e.id);t&&(t.setValidators(this.isArgVisible(e)?this.argValidators.get(e.id)??null:null),t.updateValueAndValidity({emitEvent:!1}))}}submit(){let e=$($({},this.data.formPatch||{}),this.argsForm.value);for(let t of this.data.action.args)t.type===`number`?e[t.id]=+e[t.id]:t.type===`file_output`&&(e[t.id]=e[t.id]||``);this.dialogRef.close(e)}getInputType(e){switch(e){case`number`:return`number`;case`string`:return`text`;case`file_output`:return`text`;default:return`text`}}selectOutputFile(e){return Yt$1(this,null,function*(){if(e.type===`file_output`){let t=this.data.resourceId,r=li(t);for(;r==`data`;)t=t.substring(0,t.length-r.length),r=li(t);r+=e.file_name_suffix||``;let o=yield this.mainService.api.saveFileDialog(r);o&&this.argsForm.get(e.id)?.setValue(o)}})}static ɵfac=function(t){return new(t||n)(Mr(gt),Mr(Ad),Mr(vn),Mr(en))};static ɵcmp=LI({type:n,selectors:[[`app-run-custom-action`,8,`dialog`]],standalone:!1,decls:13,vars:4,consts:[[`mat-dialog-title`,``],[`mat-dialog-content`,``],[3,`formGroup`],[`mat-dialog-actions`,``],[`mat-button`,``,3,`click`],[`mat-button`,``,3,`click`,`disabled`],[1,`action-arg-checkbox`,3,`formControlName`],[1,`arg-row`],[`appearance`,`fill`],[3,`formControlName`],[`matInput`,``,3,`id`,`type`,`formControlName`,`placeholder`],[`mat-icon-button`,``,`type`,`button`,1,`file-output-button`],[3,`value`],[`mat-icon-button`,``,`type`,`button`,1,`file-output-button`,3,`click`]],template:function(t,r){t&1&&(yi(0,`h1`,0),rw(1),Fc$1(),yi(2,`div`,1)(3,`p`),rw(4),Fc$1()(),yi(5,`form`,2),gD(6,pf,1,1,null,null,hD),Fc$1(),yi(8,`div`,3)(9,`button`,4),ih$1(`click`,function(){return r.dialogRef.close()}),rw(10,`Cancel`),Fc$1(),yi(11,`button`,5),ih$1(`click`,function(){return r.submit()}),rw(12,`Run`),Fc$1()()),t&2&&(sE(),$c$1(`Run action "`,r.data.action.title,`"`),sE(3),_h$1(r.data.action.description),sE(),Jp$1(`formGroup`,r.argsForm),sE(),mD(r.data.action.args),sE(5),Jp$1(`disabled`,r.argsForm.invalid))},dependencies:[Qt,Ki,No,Gn,Yn,Wn,lr,ii,Mo,dm,si,dr,Kd,wd,xo,wo,Sd,Cn,cs],styles:[`form[_ngcontent-%COMP%]{padding:0 24px;display:flex;flex-direction:column}form[_ngcontent-%COMP%]   .action-arg-checkbox[_ngcontent-%COMP%]{margin-bottom:16px}form[_ngcontent-%COMP%]   .arg-row[_ngcontent-%COMP%]{display:flex;align-items:flex-start;gap:8px}form[_ngcontent-%COMP%]   .arg-row[_ngcontent-%COMP%]   mat-form-field[_ngcontent-%COMP%]{flex:1}form[_ngcontent-%COMP%]   .arg-row[_ngcontent-%COMP%]   .file-output-button[_ngcontent-%COMP%]{margin-top:4px}`],changeDetection:1})}return n})();var ff=Math.pow(2,31)-1;var ur=class{_overlayRef;instance;containerInstance;_afterDismissed=new te$1;_afterOpened=new te$1;_onAction=new te$1;_durationTimeoutId;_dismissedByAction=!1;constructor(i,e){this._overlayRef=e,this.containerInstance=i,i._onExit.subscribe(()=>this._finishDismiss())}dismiss(){this._afterDismissed.closed||this.containerInstance.exit(),clearTimeout(this._durationTimeoutId)}dismissWithAction(){this._onAction.closed||(this._dismissedByAction=!0,this._onAction.next(),this._onAction.complete(),this.dismiss()),clearTimeout(this._durationTimeoutId)}closeWithAction(){this.dismissWithAction()}_dismissAfter(i){this._durationTimeoutId=setTimeout(()=>this.dismiss(),Math.min(i,ff))}_open(){this._afterOpened.closed||(this._afterOpened.next(),this._afterOpened.complete())}_finishDismiss(){this._overlayRef.dispose(),this._onAction.closed||this._onAction.complete(),this._afterDismissed.next({dismissedByAction:this._dismissedByAction}),this._afterDismissed.complete(),this._dismissedByAction=!1}afterDismissed(){return this._afterDismissed}afterOpened(){return this.containerInstance._onEnter}onAction(){return this._onAction}};var _m=new S(`MatSnackBarData`);var di=class{politeness=`polite`;announcementMessage=``;viewContainerRef;duration=0;panelClass;direction;data=null;horizontalPosition=`center`;verticalPosition=`bottom`};var gf=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`matSnackBarLabel`,``]],hostAttrs:[1,`mat-mdc-snack-bar-label`,`mdc-snackbar__label`]})}return n})();var bf=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`matSnackBarActions`,``]],hostAttrs:[1,`mat-mdc-snack-bar-actions`,`mdc-snackbar__actions`]})}return n})();var _f=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`matSnackBarAction`,``]],hostAttrs:[1,`mat-mdc-snack-bar-action`,`mdc-snackbar__action`]})}return n})();var ym=(()=>{class n{snackBarRef=I(ur);data=I(_m);action(){this.snackBarRef.dismissWithAction()}get hasAction(){return!!this.data.action}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){function e(t,r){if(t&1){let o=wD();yi(0,`div`,1)(1,`button`,2),ih$1(`click`,function(){Mu$1(o);let s=TD();return Su$1(s.action())}),rw(2),Fc$1()()}if(t&2){let o=TD();sE(2),$c$1(` `,o.data.action,` `)}}return LI({type:n,selectors:[[`simple-snack-bar`]],hostAttrs:[1,`mat-mdc-simple-snack-bar`],exportAs:[`matSnackBar`],decls:3,vars:2,consts:[[`matSnackBarLabel`,``],[`matSnackBarActions`,``],[`matButton`,``,`matSnackBarAction`,``,3,`click`]],template:function(r,o){r&1&&(yi(0,`div`,0),rw(1),Fc$1(),uD(2,e,3,1,`div`,1)),r&2&&(sE(),$c$1(` `,o.data.message,`
`),sE(),fD(o.hasAction?2:-1))},dependencies:[Qt,gf,bf,_f],styles:[`.mat-mdc-simple-snack-bar {
  display: flex;
}
.mat-mdc-simple-snack-bar .mat-mdc-snack-bar-label {
  max-height: 50vh;
  overflow: auto;
}
`],encapsulation:2})})()}return n})();var ys=`_mat-snack-bar-enter`;var vs=`_mat-snack-bar-exit`;var yf=(()=>{class n extends Wt{_ngZone=I(z);_elementRef=I(Dr);_changeDetectorRef=I(w0);_platform=I(J);_animationsDisabled=ue();snackBarConfig=I(di);_document=I(Bo);_trackedModals=new Set;_enterFallback;_exitFallback;_injector=I(le);_announceDelay=150;_announceTimeoutId;_destroyed=!1;_portalOutlet;_onAnnounce=new te$1;_onExit=new te$1;_onEnter=new te$1;_animationState=`void`;_live;_label;_role;_liveElementId=I(me).getId(`mat-snack-bar-container-live-`);constructor(){super();let e=this.snackBarConfig;e.politeness===`assertive`&&!e.announcementMessage?this._live=`assertive`:e.politeness===`off`?this._live=`off`:this._live=`polite`,this._platform.FIREFOX&&(this._live===`polite`&&(this._role=`status`),this._live===`assertive`&&(this._role=`alert`))}attachComponentPortal(e){this._assertNotAttached();let t=this._portalOutlet.attachComponentPortal(e);return this._afterPortalAttached(),t}attachTemplatePortal(e){this._assertNotAttached();let t=this._portalOutlet.attachTemplatePortal(e);return this._afterPortalAttached(),t}attachDomPortal=e=>{this._assertNotAttached();let t=this._portalOutlet.attachDomPortal(e);return this._afterPortalAttached(),t};onAnimationEnd(e){e===vs?this._completeExit():e===ys&&(clearTimeout(this._enterFallback),this._ngZone.run(()=>{this._onEnter.next(),this._onEnter.complete()}))}enter(){this._destroyed||(this._animationState=`visible`,this._changeDetectorRef.markForCheck(),this._changeDetectorRef.detectChanges(),this._screenReaderAnnounce(),this._animationsDisabled?Hv(()=>{this._ngZone.run(()=>queueMicrotask(()=>this.onAnimationEnd(ys)))},{injector:this._injector}):(clearTimeout(this._enterFallback),this._enterFallback=setTimeout(()=>{this._elementRef.nativeElement.classList.add(`mat-snack-bar-fallback-visible`),this.onAnimationEnd(ys)},200)))}exit(){return this._destroyed?Sg(void 0):(this._ngZone.run(()=>{this._animationState=`hidden`,this._changeDetectorRef.markForCheck(),this._elementRef.nativeElement.setAttribute(`mat-exit`,``),clearTimeout(this._announceTimeoutId),this._animationsDisabled?Hv(()=>{this._ngZone.run(()=>queueMicrotask(()=>this.onAnimationEnd(vs)))},{injector:this._injector}):(clearTimeout(this._exitFallback),this._exitFallback=setTimeout(()=>this.onAnimationEnd(vs),200))}),this._onExit)}ngOnDestroy(){this._destroyed=!0,this._clearFromModals(),this._completeExit()}_completeExit(){clearTimeout(this._exitFallback),queueMicrotask(()=>{this._onExit.next(),this._onExit.complete()})}_afterPortalAttached(){let e=this._elementRef.nativeElement,t=this.snackBarConfig.panelClass;t&&(Array.isArray(t)?t.forEach(a=>e.classList.add(a)):e.classList.add(t)),this._exposeToModals();let r=this._label.nativeElement,o=`mdc-snackbar__label`;r.classList.toggle(o,!r.querySelector(`.${o}`))}_exposeToModals(){let e=this._liveElementId,t=this._document.querySelectorAll(`body > .cdk-overlay-container [aria-modal="true"]`);for(let r=0;r<t.length;r++){let o=t[r],a=o.getAttribute(`aria-owns`);this._trackedModals.add(o),a?a.indexOf(e)===-1&&o.setAttribute(`aria-owns`,a+` `+e):o.setAttribute(`aria-owns`,e)}}_clearFromModals(){this._trackedModals.forEach(e=>{let t=e.getAttribute(`aria-owns`);if(t){let r=t.replace(this._liveElementId,``).trim();r.length>0?e.setAttribute(`aria-owns`,r):e.removeAttribute(`aria-owns`)}}),this._trackedModals.clear()}_assertNotAttached(){this._portalOutlet.hasAttached()}_screenReaderAnnounce(){this._announceTimeoutId||this._ngZone.runOutsideAngular(()=>{this._announceTimeoutId=setTimeout(()=>{if(this._destroyed)return;let e=this._elementRef.nativeElement,t=e.querySelector(`[aria-hidden]`),r=e.querySelector(`[aria-live]`);if(t&&r){let o=null;this._platform.isBrowser&&document.activeElement instanceof HTMLElement&&t.contains(document.activeElement)&&(o=document.activeElement),t.removeAttribute(`aria-hidden`),r.appendChild(t),o?.focus(),this._onAnnounce.next(),this._onAnnounce.complete()}},this._announceDelay)})}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`label`];function t(r,o){}return LI({type:n,selectors:[[`mat-snack-bar-container`]],viewQuery:function(o,a){if(o&1&&lh$1(Yt,7)(e,7),o&2){let s;SD(s=xD())&&(a._portalOutlet=s.first),SD(s=xD())&&(a._label=s.first)}},hostAttrs:[1,`mdc-snackbar`,`mat-mdc-snack-bar-container`],hostVars:6,hostBindings:function(o,a){o&1&&ih$1(`animationend`,function(c){return a.onAnimationEnd(c.animationName)})(`animationcancel`,function(c){return a.onAnimationEnd(c.animationName)}),o&2&&yh$1(`mat-snack-bar-container-enter`,a._animationState===`visible`)(`mat-snack-bar-container-exit`,a._animationState===`hidden`)(`mat-snack-bar-container-animations-enabled`,!a._animationsDisabled)},features:[Vp$1],decls:6,vars:3,consts:[[`label`,``],[1,`mdc-snackbar__surface`,`mat-mdc-snackbar-surface`],[1,`mat-mdc-snack-bar-label`],[`aria-hidden`,`true`],[`cdkPortalOutlet`,``]],template:function(o,a){o&1&&(yi(0,`div`,1)(1,`div`,2,0)(3,`div`,3),Bp$1(4,t,0,0,`ng-template`,4),Fc$1(),Xp$1(5,`div`),Fc$1()()),o&2&&(sE(5),Kp(`aria-live`,a._live)(`role`,a._role)(`id`,a._liveElementId))},dependencies:[Yt],styles:[`@keyframes _mat-snack-bar-enter {
  from {
    transform: scale(0.8);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
@keyframes _mat-snack-bar-exit {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
.mat-mdc-snack-bar-container {
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
  margin: 8px;
}
.mat-mdc-snack-bar-handset .mat-mdc-snack-bar-container {
  width: 100vw;
}

.mat-snack-bar-container-animations-enabled {
  opacity: 0;
}
.mat-snack-bar-container-animations-enabled.mat-snack-bar-fallback-visible {
  opacity: 1;
}
.mat-snack-bar-container-animations-enabled.mat-snack-bar-container-enter {
  animation: _mat-snack-bar-enter 150ms cubic-bezier(0, 0, 0.2, 1) forwards;
}
.mat-snack-bar-container-animations-enabled.mat-snack-bar-container-exit {
  animation: _mat-snack-bar-exit 75ms cubic-bezier(0.4, 0, 1, 1) forwards;
}

.mat-mdc-snackbar-surface {
  box-shadow: 0px 3px 5px -1px rgba(0, 0, 0, 0.2), 0px 6px 10px 0px rgba(0, 0, 0, 0.14), 0px 1px 18px 0px rgba(0, 0, 0, 0.12);
  display: flex;
  align-items: center;
  justify-content: flex-start;
  box-sizing: border-box;
  padding-left: 0;
  padding-right: 8px;
}
[dir=rtl] .mat-mdc-snackbar-surface {
  padding-right: 0;
  padding-left: 8px;
}
.mat-mdc-snack-bar-container .mat-mdc-snackbar-surface {
  min-width: 344px;
  max-width: 672px;
}
.mat-mdc-snack-bar-handset .mat-mdc-snackbar-surface {
  width: 100%;
  min-width: 0;
}
@media (forced-colors: active) {
  .mat-mdc-snackbar-surface {
    outline: solid 1px;
  }
}
.mat-mdc-snack-bar-container .mat-mdc-snackbar-surface {
  color: var(--%NS%mat-snack-bar-supporting-text-color, var(--%NS%mat-sys-inverse-on-surface));
  border-radius: var(--%NS%mat-snack-bar-container-shape, var(--%NS%mat-sys-corner-extra-small));
  background-color: var(--%NS%mat-snack-bar-container-color, var(--%NS%mat-sys-inverse-surface));
}

.mdc-snackbar__label {
  width: 100%;
  flex-grow: 1;
  box-sizing: border-box;
  margin: 0;
  padding: 14px 8px 14px 16px;
}
[dir=rtl] .mdc-snackbar__label {
  padding-left: 8px;
  padding-right: 16px;
}
.mat-mdc-snack-bar-container .mdc-snackbar__label {
  font-family: var(--%NS%mat-snack-bar-supporting-text-font, var(--%NS%mat-sys-body-medium-font));
  font-size: var(--%NS%mat-snack-bar-supporting-text-size, var(--%NS%mat-sys-body-medium-size));
  font-weight: var(--%NS%mat-snack-bar-supporting-text-weight, var(--%NS%mat-sys-body-medium-weight));
  line-height: var(--%NS%mat-snack-bar-supporting-text-line-height, var(--%NS%mat-sys-body-medium-line-height));
}

.mat-mdc-snack-bar-actions {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  box-sizing: border-box;
}

.mat-mdc-snack-bar-handset,
.mat-mdc-snack-bar-container,
.mat-mdc-snack-bar-label {
  flex: 1 1 auto;
}

.mat-mdc-snack-bar-container .mat-mdc-button.mat-mdc-snack-bar-action:not(:disabled).mat-unthemed {
  color: var(--%NS%mat-snack-bar-button-color, var(--%NS%mat-sys-inverse-primary));
}
.mat-mdc-snack-bar-container .mat-mdc-button.mat-mdc-snack-bar-action:not(:disabled) {
  --%NS%mat-button-text-state-layer-color: currentColor;
  --%NS%mat-button-text-ripple-color: currentColor;
}
.mat-mdc-snack-bar-container .mat-mdc-button.mat-mdc-snack-bar-action:not(:disabled) .mat-ripple-element {
  opacity: 0.1;
}
`],encapsulation:2,changeDetection:1})})()}return n})();var vf=new S(`mat-snack-bar-default-options`,{providedIn:`root`,factory:()=>new di});var hr=(()=>{class n{_live=I(Bi);_injector=I(le);_breakpointObserver=I(Vi);_parentSnackBar=I(n,{optional:!0,skipSelf:!0});_defaultConfig=I(vf);_animationsDisabled=ue();_snackBarRefAtThisLevel=null;simpleSnackBarComponent=ym;snackBarContainerComponent=yf;handsetCssClass=`mat-mdc-snack-bar-handset`;get _openedSnackBarRef(){let e=this._parentSnackBar;return e?e._openedSnackBarRef:this._snackBarRefAtThisLevel}set _openedSnackBarRef(e){this._parentSnackBar?this._parentSnackBar._openedSnackBarRef=e:this._snackBarRefAtThisLevel=e}openFromComponent(e,t){return this._attach(e,t)}openFromTemplate(e,t){return this._attach(e,t)}open(e,t=``,r){let o=$($({},this._defaultConfig),r);return o.data={message:e,action:t},o.announcementMessage===e&&(o.announcementMessage=void 0),this.openFromComponent(this.simpleSnackBarComponent,o)}dismiss(){this._openedSnackBarRef&&this._openedSnackBarRef.dismiss()}ngOnDestroy(){this._snackBarRefAtThisLevel&&this._snackBarRefAtThisLevel.dismiss()}_attachSnackBarContainer(e,t){let r=t&&t.viewContainerRef&&t.viewContainerRef.injector,o=le.create({parent:r||this._injector,providers:[{provide:di,useValue:t}]}),a=new ut(this.snackBarContainerComponent,t.viewContainerRef,o),s=e.attach(a);return s.instance.snackBarConfig=t,s.instance}_attach(e,t){let r=$($($({},new di),this._defaultConfig),t),o=this._createOverlay(r),a=this._attachSnackBarContainer(o,r),s=new ur(a,o);if(e instanceof gr){let c=new rt(e,null,{$implicit:r.data,snackBarRef:s});s.instance=a.attachTemplatePortal(c)}else{let d=new ut(e,void 0,this._createInjector(r,s));s.instance=a.attachComponentPortal(d).instance}return this._breakpointObserver.observe(yc.HandsetPortrait).pipe(Rl$1(o.detachments())).subscribe(c=>{o.overlayElement.classList.toggle(this.handsetCssClass,c.matches)}),r.announcementMessage&&a._onAnnounce.subscribe(()=>{this._live.announce(r.announcementMessage,r.politeness)}),this._animateSnackBar(s,r),this._openedSnackBarRef=s,this._openedSnackBarRef}_animateSnackBar(e,t){e.afterDismissed().subscribe(()=>{this._openedSnackBarRef==e&&(this._openedSnackBarRef=null),t.announcementMessage&&this._live.clear()}),t.duration&&t.duration>0&&e.afterOpened().subscribe(()=>e._dismissAfter(t.duration)),this._openedSnackBarRef?(this._openedSnackBarRef.afterDismissed().subscribe(()=>{e.containerInstance.enter()}),this._openedSnackBarRef.dismiss()):e.containerInstance.enter()}_createOverlay(e){let t=new ht;t.direction=e.direction;let r=Xt(this._injector),o=e.direction===`rtl`,a=e.horizontalPosition===`left`||e.horizontalPosition===`start`&&!o||e.horizontalPosition===`end`&&o,s=!a&&e.horizontalPosition!==`center`;return a?r.left(`0`):s?r.right(`0`):r.centerHorizontally(),e.verticalPosition===`top`?r.top(`0`):r.bottom(`0`),t.positionStrategy=r,t.disableAnimations=this._animationsDisabled,pt(this._injector,t)}_createInjector(e,t){let r=e&&e.viewContainerRef&&e.viewContainerRef.injector;return le.create({parent:r||this._injector,providers:[{provide:ur,useValue:t},{provide:_m,useValue:e.data}]})}static ɵfac=function(t){return new(t||n)};static ɵprov=Gt$1({token:n,factory:n.ɵfac})}return n})();var DM=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({providers:[hr],imports:[Ke,Rt,Uc,ym,te]})}return n})();var xm=(()=>{class n{mainService;dialog;snackBar;constructor(e,t,r){this.mainService=e,this.dialog=t,this.snackBar=r}runCustomAction(a,s){return Yt$1(this,arguments,function*(e,t,r={},o=!1){if(t.idDepth)for(let d=0;d<t.idDepth;d++)e=e.substring(0,Math.max(e.lastIndexOf(`/`),e.lastIndexOf(`__`)));if(o){for(let{id:d}of t.args)if(r[d]===void 0){o=!1;break}}let c=[];if(o)c=r;else{let d=this.dialog.open(bm,{data:{action:t,resourceId:e,formPatch:r}}),m=yield dg(d.afterClosed());if(!m)return!1;c=m}try{return yield this.mainService.runCustomAction(e,t,c),this.snackBar.open(`Action performed!`,`OK`,{duration:1500}),!0}catch(d){return yield this.mainService.reloadResource(),this.snackBar.open(`Error while performing action! Reverting file state.. `+(d.errorText||d),`OK :(`,{duration:5e3}),!1}})}static ɵfac=function(t){return new(t||n)(ae(en),ae(Lt),ae(hr))};static ɵprov=K({token:n,factory:n.ɵfac,providedIn:`root`})}return n})();function Cf(n,i){n&1&&(yi(0,`h2`,4),rw(1,`Importing a 3D model from OBJ`),Fc$1(),yi(2,`mat-dialog-content`)(3,`p`),rw(4,` The OBJ of the folder you pick next replaces this model. Start from a folder this app exported (the download button) and keep its files together: `),yi(5,`code`),rw(6,`geometry.obj`),Fc$1(),rw(7,`, `),yi(8,`code`),rw(9,`material.mtl`),Fc$1(),rw(10,`, `),yi(11,`code`),rw(12,`geometry_extra.json`),Fc$1(),rw(13,` (the drawing order the game needs; without it the model still imports, with tiny differences) and `),yi(14,`code`),rw(15,`assets/`),Fc$1(),rw(16,` (the textures). `),Fc$1(),yi(17,`h3`),rw(18,`Blender`),Fc$1(),yi(19,`ul`)(20,`li`),rw(21,`File › Import › Wavefront (.obj) with the default settings.`),Fc$1(),yi(22,`li`),rw(23,` Edit, then File › Export › Wavefront (.obj) with the default settings, over `),yi(24,`code`),rw(25,`geometry.obj`),Fc$1(),rw(26,` in the same folder: when a folder holds several OBJ files, `),yi(27,`code`),rw(28,`geometry.obj`),Fc$1(),rw(29,` is the one imported. `),Fc$1()(),yi(30,`h3`),rw(31,`Materials`),Fc$1(),yi(32,`ul`)(33,`li`),rw(34,` A textured material is named after a bitmap of the model's FSH, 4 characters at most (`),yi(35,`code`),rw(36,`rsid`),Fc$1(),rw(37,`), or its image file has such a name. An image that differs from the FSH bitmap replaces it, a new name adds a bitmap. `),Fc$1(),yi(38,`li`)(39,`code`),rw(40,`flat_rrggbb`),Fc$1(),rw(41,`: one colour (hex RGB), no texture.`),Fc$1(),yi(42,`li`)(43,`code`),rw(44,`<bitmap>__cutout`),Fc$1(),rw(45,` / `),yi(46,`code`),rw(47,`<bitmap>__opaque`),Fc$1(),rw(48,`: the transparent pixels of the bitmap are skipped / painted. `),Fc$1()(),yi(49,`h3`),rw(50,`Objects`),Fc$1(),yi(51,`ul`)(52,`li`),rw(53,` The game draws a model's parts in three groups, `),yi(54,`code`),rw(55,`inside`),Fc$1(),rw(56,`, `),yi(57,`code`),rw(58,`surface`),Fc$1(),rw(59,`, `),yi(60,`code`),rw(61,`outside`),Fc$1(),rw(62,`, sorting by depth only within a group. A new part goes to `),yi(63,`code`),rw(64,`surface`),Fc$1(),rw(65,`: end its object name with `),yi(66,`code`),rw(67,`__outside`),Fc$1(),rw(68,` to draw it over the body (a spoiler, mirrors), with `),yi(69,`code`),rw(70,`__inside`),Fc$1(),rw(71,` to draw it under. `),Fc$1(),yi(72,`li`),rw(73,` Car wheels are the objects `),yi(74,`code`),rw(75,`lbl__lt_frnt`),Fc$1(),rw(76,`, `),yi(77,`code`),rw(78,`lbl__rt_frnt`),Fc$1(),rw(79,`, `),yi(80,`code`),rw(81,`lbl__lt_rear`),Fc$1(),rw(82,`, `),yi(83,`code`),rw(84,`lbl__rt_rear`),Fc$1(),rw(85,`: the game puts the tyre textures on them and steers the front ones. `),Fc$1(),yi(86,`li`),rw(87,`Faces with more than 4 corners are split into triangles: keep them convex.`),Fc$1()(),yi(88,`h3`),rw(89,`Car files (CFM)`),Fc$1(),yi(90,`ul`)(91,`li`),rw(92,` A car has two models: the first one is drawn close, the second one far away. Import each one separately. `),Fc$1(),yi(93,`li`),rw(94,`The import changes the opened file in memory: save the file to write it.`),Fc$1()()())}var Cm={orip_obj:`show_orip_import_guide`};var Sm=(()=>{class n{dialogRef;data;dontShowAgain=!1;constructor(e,t){this.dialogRef=e,this.data=t}close(e){this.dialogRef.close({proceed:e,dontShowAgain:this.dontShowAgain})}static ɵfac=function(t){return new(t||n)(Mr(gt),Mr(vn))};static ɵcmp=LI({type:n,selectors:[[`app-import-guide-dialog`]],decls:8,vars:2,consts:[[`align`,`end`],[3,`ngModelChange`,`ngModel`],[`mat-button`,``,3,`click`],[`mat-raised-button`,``,`color`,`primary`,3,`click`],[`mat-dialog-title`,``]],template:function(t,r){if(t&1&&(uD(0,Cf,95,0),yi(1,`mat-dialog-actions`,0)(2,`mat-checkbox`,1),qE(),Rh$1(`ngModelChange`,function(a){return lw(r.dontShowAgain,a)||(r.dontShowAgain=a),a}),rw(3,`Don't show this again`),Fc$1(),yi(4,`button`,2),ih$1(`click`,function(){return r.close(!1)}),rw(5,`Cancel`),Fc$1(),yi(6,`button`,3),ih$1(`click`,function(){return r.close(!0)}),rw(7,`Pick folder`),Fc$1()()),t&2)fD(r.data.guide===`orip_obj`?0:-1),sE(2),Ah$1(`ngModel`,r.dontShowAgain),zE()},dependencies:[Gn,Wn,Yn,dr,Id,wo,ss,Qt],styles:[`mat-dialog-content[_ngcontent-%COMP%]{min-width:400px;max-width:720px;max-height:70vh}h3[_ngcontent-%COMP%]{margin:16px 0 4px}ul[_ngcontent-%COMP%]{margin:0;padding-left:20px}li[_ngcontent-%COMP%]{margin:4px 0}code[_ngcontent-%COMP%]{font-size:.95em}mat-dialog-actions[_ngcontent-%COMP%]   mat-checkbox[_ngcontent-%COMP%]{margin-right:auto}`]})}return n})();var Cs=new S(`MAT_MENU_PANEL`);var pr=(()=>{class n{_isAnchor;_elementRef=I(Dr);_document=I(Bo);_focusMonitor=I(ft);_parentMenu=I(Cs,{optional:!0});_changeDetectorRef=I(w0);role=`menuitem`;disabled=!1;disabledInteractive=!1;disableRipple=!1;_hovered=new te$1;_focused=new te$1;_highlighted=!1;_triggersSubmenu=!1;constructor(){I(Se).load(Zt),this._parentMenu?.addItem?.(this),this._isAnchor=this._elementRef.nativeElement.tagName===`A`}focus(e,t){this._focusMonitor&&e?this._focusMonitor.focusVia(this._getHostElement(),e,t):this._getHostElement().focus(t),this._focused.next(this)}ngAfterViewInit(){this._focusMonitor&&this._focusMonitor.monitor(this._elementRef,!1)}ngOnDestroy(){this._focusMonitor&&this._focusMonitor.stopMonitoring(this._elementRef),this._parentMenu&&this._parentMenu.removeItem&&this._parentMenu.removeItem(this),this._hovered.complete(),this._focused.complete()}_getTabIndex(){return this.disabled&&!this.disabledInteractive?`-1`:`0`}_getAriaDisabled(){return this._isAnchor?this.disabled||null:this.disabled&&this.disabledInteractive?!0:null}_getDisabled(){return this.disabledInteractive||!this.disabled?null:!0}_getHostElement(){return this._elementRef.nativeElement}_checkDisabled(e){this.disabled&&(e.preventDefault(),e.stopPropagation())}_handleMouseEnter(){this._hovered.next(this)}getLabel(){let e=this._elementRef.nativeElement.cloneNode(!0),t=e.querySelectorAll(`mat-icon, .material-icons, .material-symbols-outlined, .material-symbols-rounded, .material-symbols-sharp`);for(let r=0;r<t.length;r++)t[r].remove();return e.textContent?.trim()||``}_setHighlighted(e){this._highlighted=e,this._changeDetectorRef.markForCheck()}_setTriggersSubmenu(e){this._triggersSubmenu=e,this._changeDetectorRef.markForCheck()}_hasFocus(){return this._document&&this._document.activeElement===this._getHostElement()}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[[[`mat-icon`],[``,`matMenuItemIcon`,``]],`*`],t=[`mat-icon, [matMenuItemIcon]`,`*`];function r(o,a){o&1&&(Bu(),yi(0,`svg`,2),Xp$1(1,`polygon`,3),Fc$1())}return LI({type:n,selectors:[[``,`mat-menu-item`,``]],hostAttrs:[1,`mat-mdc-menu-item`,`mat-focus-indicator`],hostVars:12,hostBindings:function(a,s){a&1&&ih$1(`click`,function(d){return s._checkDisabled(d)})(`mouseenter`,function(){return s._handleMouseEnter()}),a&2&&(Kp(`role`,s.role)(`tabindex`,s._getTabIndex())(`aria-disabled`,s._getAriaDisabled())(`disabled`,s._getDisabled()),yh$1(`mat-mdc-menu-item-highlighted`,s._highlighted)(`mat-mdc-menu-item-submenu-trigger`,s._triggersSubmenu)(`mat-mdc-menu-item-disabled`,s.disabled)(`mat-mdc-menu-item-disabled-interactive`,s.disabledInteractive))},inputs:{role:`role`,disabled:[2,`disabled`,`disabled`,T0],disabledInteractive:[2,`disabledInteractive`,`disabledInteractive`,T0],disableRipple:[2,`disableRipple`,`disableRipple`,T0]},exportAs:[`matMenuItem`],ngContentSelectors:t,decls:5,vars:3,consts:[[1,`mat-mdc-menu-item-text`],[`matRipple`,``,1,`mat-mdc-menu-ripple`,3,`matRippleDisabled`,`matRippleTrigger`],[`viewBox`,`0 0 5 10`,`focusable`,`false`,`aria-hidden`,`true`,1,`mat-mdc-menu-submenu-icon`],[`points`,`0,0 5,5 0,10`]],template:function(a,s){a&1&&(_D(e),ND(0),yi(1,`span`,0),ND(2,1),Fc$1(),Xp$1(3,`div`,1),uD(4,r,2,0,`:svg:svg`,2)),a&2&&(sE(3),Jp$1(`matRippleDisabled`,s.disableRipple||s.disabled)(`matRippleTrigger`,s._getHostElement()),sE(),fD(s._triggersSubmenu?4:-1))},dependencies:[qn],encapsulation:2})})()}return n})();var Sf=new S(`MatMenuContent`);var wf=new S(`mat-menu-default-options`,{providedIn:`root`,factory:()=>({overlapTrigger:!1,xPosition:`after`,yPosition:`below`,backdropClass:`cdk-overlay-transparent-backdrop`})});var xs=`_mat-menu-enter`;var Vo=`_mat-menu-exit`;var ui=(()=>{class n{_elementRef=I(Dr);_changeDetectorRef=I(w0);_injector=I(le);_keyManager;_xPosition;_yPosition;_firstItemFocusRef;_exitFallbackTimeout;_animationsDisabled=ue();_allItems;_directDescendantItems=new ii$1;_classList={};_panelAnimationState=`void`;_animationDone=new te$1;_isAnimating=oa(!1);parentMenu;direction;overlayPanelClass;backdropClass;ariaLabel;ariaLabelledby;ariaDescribedby;get xPosition(){return this._xPosition}set xPosition(e){this._xPosition=e,this.setPositionClasses()}get yPosition(){return this._yPosition}set yPosition(e){this._yPosition=e,this.setPositionClasses()}templateRef;items;lazyContent;overlapTrigger=!1;hasBackdrop;get panelClass(){return this._previousPanelClass}set panelClass(e){let t=this._previousPanelClass,r=$({},this._classList);t&&t.length&&t.split(` `).forEach(o=>{r[o]=!1}),this._previousPanelClass=e,e&&e.length&&(e.split(` `).forEach(o=>{r[o]=!0}),this._elementRef.nativeElement.className=``),this._classList=r}_previousPanelClass=``;get classList(){return this.panelClass}set classList(e){this.panelClass=e}closed=new Fe;close=this.closed;panelId=I(me).getId(`mat-menu-panel-`);constructor(){let e=I(wf);this.overlayPanelClass=e.overlayPanelClass||``,this._xPosition=e.xPosition,this._yPosition=e.yPosition,this.backdropClass=e.backdropClass,this.overlapTrigger=e.overlapTrigger,this.hasBackdrop=e.hasBackdrop}ngOnInit(){this.setPositionClasses()}ngAfterContentInit(){this._updateDirectDescendants(),this._keyManager=new Wi(this._directDescendantItems).withWrap().withTypeAhead().withHomeAndEnd().skipPredicate(e=>e.disabled&&!e.disabledInteractive),this._keyManager.tabOut.subscribe(()=>this.closed.emit(`tab`)),this._directDescendantItems.changes.pipe(Al$1(this._directDescendantItems),Ul$1(e=>Bg(...e.map(t=>t._focused)))).subscribe(e=>this._keyManager.updateActiveItem(e)),this._directDescendantItems.changes.subscribe(e=>{let t=this._keyManager;if(this._panelAnimationState===`enter`&&t.activeItem?._hasFocus()){let r=e.toArray(),o=Math.max(0,Math.min(r.length-1,t.activeItemIndex||0));r[o]&&!r[o].disabled?t.setActiveItem(o):t.setNextItemActive()}})}ngOnDestroy(){this._keyManager?.destroy(),this._directDescendantItems.destroy(),this.closed.complete(),this._firstItemFocusRef?.destroy(),clearTimeout(this._exitFallbackTimeout)}_hovered(){return this._directDescendantItems.changes.pipe(Al$1(this._directDescendantItems),Ul$1(t=>Bg(...t.map(r=>r._hovered))))}addItem(e){}removeItem(e){}_handleKeydown(e){let t=e.keyCode,r=this._keyManager;switch(t){case 27:Me(e)||(e.preventDefault(),this.closed.emit(`keydown`));break;case 37:this.parentMenu&&this.direction===`ltr`&&this.closed.emit(`keydown`);break;case 39:this.parentMenu&&this.direction===`rtl`&&this.closed.emit(`keydown`);break;default:(t===38||t===40)&&r.setFocusOrigin(`keyboard`),r.onKeydown(e);return}}focusFirstItem(e=`program`){this._firstItemFocusRef?.destroy(),this._firstItemFocusRef=Hv(()=>{let t=this._resolvePanel();if(!t||!t.contains(document.activeElement)){let r=this._keyManager;r.setFocusOrigin(e).setFirstItemActive(),!r.activeItem&&t&&t.focus()}},{injector:this._injector})}resetActiveItem(){this._keyManager.setActiveItem(-1)}setElevation(e){}setPositionClasses(e=this.xPosition,t=this.yPosition){this._classList=Y($({},this._classList),{"mat-menu-before":e===`before`,"mat-menu-after":e===`after`,"mat-menu-above":t===`above`,"mat-menu-below":t===`below`}),this._changeDetectorRef.markForCheck()}_onAnimationDone(e){let t=e===Vo;(t||e===xs)&&(t&&(clearTimeout(this._exitFallbackTimeout),this._exitFallbackTimeout=void 0),this._animationDone.next(t?`void`:`enter`),this._isAnimating.set(!1))}_onAnimationStart(e){(e===xs||e===Vo)&&this._isAnimating.set(!0)}_setIsOpen(e){if(this._panelAnimationState=e?`enter`:`void`,e){if(this._keyManager.activeItemIndex===0){let t=this._resolvePanel();t&&(t.scrollTop=0)}}else this._animationsDisabled||(this._exitFallbackTimeout=setTimeout(()=>this._onAnimationDone(Vo),200));this._animationsDisabled&&setTimeout(()=>{this._onAnimationDone(e?xs:Vo)}),this._changeDetectorRef.markForCheck()}_updateDirectDescendants(){this._allItems.changes.pipe(Al$1(this._allItems)).subscribe(e=>{this._directDescendantItems.reset(e.filter(t=>t._parentMenu===this)),this._directDescendantItems.notifyOnChanges()})}_resolvePanel(){let e=null;return this._directDescendantItems.length&&(e=this._directDescendantItems.first._getHostElement().closest(`[role="menu"]`)),e}static ɵfac=function(t){return new(t||n)};static ɵcmp=(function(){let e=[`*`];function t(r,o){if(r&1){let a=wD();jc$1(0,`div`,0),sh$1(`click`,function(){Mu$1(a);let c=TD();return Su$1(c.closed.emit(`click`))})(`animationstart`,function(c){Mu$1(a);let d=TD();return Su$1(d._onAnimationStart(c.animationName))})(`animationend`,function(c){Mu$1(a);let d=TD();return Su$1(d._onAnimationDone(c.animationName))})(`animationcancel`,function(c){Mu$1(a);let d=TD();return Su$1(d._onAnimationDone(c.animationName))}),jc$1(1,`div`,1),ND(2),Vc$1()()}if(r&2){let a=TD();zD(a._classList),yh$1(`mat-menu-panel-animations-disabled`,a._animationsDisabled)(`mat-menu-panel-exit-animation`,a._panelAnimationState===`void`)(`mat-menu-panel-animating`,a._isAnimating()),rh$1(`id`,a.panelId),Kp(`aria-label`,a.ariaLabel||null)(`aria-labelledby`,a.ariaLabelledby||null)(`aria-describedby`,a.ariaDescribedby||null)}}return LI({type:n,selectors:[[`mat-menu`]],contentQueries:function(o,a,s){if(o&1&&ch$1(s,Sf,5)(s,pr,5)(s,pr,4),o&2){let c;SD(c=xD())&&(a.lazyContent=c.first),SD(c=xD())&&(a._allItems=c),SD(c=xD())&&(a.items=c)}},viewQuery:function(o,a){if(o&1&&lh$1(gr,5),o&2){let s;SD(s=xD())&&(a.templateRef=s.first)}},hostVars:3,hostBindings:function(o,a){o&2&&Kp(`aria-label`,null)(`aria-labelledby`,null)(`aria-describedby`,null)},inputs:{backdropClass:`backdropClass`,ariaLabel:[0,`aria-label`,`ariaLabel`],ariaLabelledby:[0,`aria-labelledby`,`ariaLabelledby`],ariaDescribedby:[0,`aria-describedby`,`ariaDescribedby`],xPosition:`xPosition`,yPosition:`yPosition`,overlapTrigger:[2,`overlapTrigger`,`overlapTrigger`,T0],hasBackdrop:[2,`hasBackdrop`,`hasBackdrop`,r=>r==null?null:T0(r)],panelClass:[0,`class`,`panelClass`],classList:`classList`},outputs:{closed:`closed`,close:`close`},exportAs:[`matMenu`],features:[hw([{provide:Cs,useExisting:n}])],ngContentSelectors:e,decls:1,vars:0,consts:[[`tabindex`,`-1`,`role`,`menu`,1,`mat-mdc-menu-panel`,3,`click`,`animationstart`,`animationend`,`animationcancel`,`id`],[1,`mat-mdc-menu-content`]],template:function(o,a){o&1&&(_D(),$p$1(0,t,3,12,`ng-template`))},styles:[`mat-menu {
  display: none;
}

.mat-mdc-menu-content {
  margin: 0;
  padding: 8px 0;
  outline: 0;
}
.mat-mdc-menu-content,
.mat-mdc-menu-content .mat-mdc-menu-item .mat-mdc-menu-item-text {
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  flex: 1;
  white-space: normal;
  font-family: var(--%NS%mat-menu-item-label-text-font, var(--%NS%mat-sys-label-large-font));
  line-height: var(--%NS%mat-menu-item-label-text-line-height, var(--%NS%mat-sys-label-large-line-height));
  font-size: var(--%NS%mat-menu-item-label-text-size, var(--%NS%mat-sys-label-large-size));
  letter-spacing: var(--%NS%mat-menu-item-label-text-tracking, var(--%NS%mat-sys-label-large-tracking));
  font-weight: var(--%NS%mat-menu-item-label-text-weight, var(--%NS%mat-sys-label-large-weight));
}

@keyframes _mat-menu-enter {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
@keyframes _mat-menu-exit {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
.mat-mdc-menu-panel {
  min-width: 112px;
  max-width: 280px;
  overflow: auto;
  box-sizing: border-box;
  outline: 0;
  animation: _mat-menu-enter 120ms cubic-bezier(0, 0, 0.2, 1);
  border-radius: var(--%NS%mat-menu-container-shape, var(--%NS%mat-sys-corner-extra-small));
  background-color: var(--%NS%mat-menu-container-color, var(--%NS%mat-sys-surface-container));
  box-shadow: var(--%NS%mat-menu-container-elevation-shadow, 0px 3px 1px -2px rgba(0, 0, 0, 0.2), 0px 2px 2px 0px rgba(0, 0, 0, 0.14), 0px 1px 5px 0px rgba(0, 0, 0, 0.12));
  will-change: transform, opacity;
}
.mat-mdc-menu-panel.mat-menu-panel-exit-animation {
  animation: _mat-menu-exit 100ms 25ms linear forwards;
}
.mat-mdc-menu-panel.mat-menu-panel-animations-disabled {
  animation: none;
}
.mat-mdc-menu-panel.mat-menu-panel-animating {
  pointer-events: none;
}
.mat-mdc-menu-panel.mat-menu-panel-animating:has(.mat-mdc-menu-content:empty) {
  display: none;
}
@media (forced-colors: active) {
  .mat-mdc-menu-panel {
    outline: solid 1px;
  }
}
.mat-mdc-menu-panel .mat-divider {
  border-top-color: var(--%NS%mat-menu-divider-color, var(--%NS%mat-sys-surface-variant));
  margin-bottom: var(--%NS%mat-menu-divider-bottom-spacing, 8px);
  margin-top: var(--%NS%mat-menu-divider-top-spacing, 8px);
}

.mat-mdc-menu-item {
  display: flex;
  position: relative;
  align-items: center;
  justify-content: flex-start;
  overflow: hidden;
  padding: 0;
  cursor: pointer;
  width: 100%;
  text-align: left;
  box-sizing: border-box;
  color: inherit;
  font-size: inherit;
  background: none;
  text-decoration: none;
  margin: 0;
  min-height: 48px;
  padding-left: var(--%NS%mat-menu-item-leading-spacing, 12px);
  padding-right: var(--%NS%mat-menu-item-trailing-spacing, 12px);
  -webkit-user-select: none;
  user-select: none;
  cursor: pointer;
  outline: none;
  border: none;
  -webkit-tap-highlight-color: transparent;
}
.mat-mdc-menu-item::-moz-focus-inner {
  border: 0;
}
[dir=rtl] .mat-mdc-menu-item {
  padding-left: var(--%NS%mat-menu-item-trailing-spacing, 12px);
  padding-right: var(--%NS%mat-menu-item-leading-spacing, 12px);
}
.mat-mdc-menu-item:has(.material-icons, .material-symbols-outlined, .material-symbols-rounded, .material-symbols-sharp, mat-icon, [matButtonIcon]) {
  padding-left: var(--%NS%mat-menu-item-with-icon-leading-spacing, 12px);
  padding-right: var(--%NS%mat-menu-item-with-icon-trailing-spacing, 12px);
}
[dir=rtl] .mat-mdc-menu-item:has(.material-icons, .material-symbols-outlined, .material-symbols-rounded, .material-symbols-sharp, mat-icon, [matButtonIcon]) {
  padding-left: var(--%NS%mat-menu-item-with-icon-trailing-spacing, 12px);
  padding-right: var(--%NS%mat-menu-item-with-icon-leading-spacing, 12px);
}
.mat-mdc-menu-item, .mat-mdc-menu-item:visited, .mat-mdc-menu-item:link {
  color: var(--%NS%mat-menu-item-label-text-color, var(--%NS%mat-sys-on-surface));
}
.mat-mdc-menu-item .mat-icon-no-color,
.mat-mdc-menu-item .mat-mdc-menu-submenu-icon {
  color: var(--%NS%mat-menu-item-icon-color, var(--%NS%mat-sys-on-surface-variant));
}
.mat-mdc-menu-item[disabled], .mat-mdc-menu-item.mat-mdc-menu-item-disabled {
  cursor: default;
  opacity: 0.38;
}
.mat-mdc-menu-item[disabled]::after, .mat-mdc-menu-item.mat-mdc-menu-item-disabled::after {
  display: block;
  position: absolute;
  content: "";
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
}
.mat-mdc-menu-item:focus {
  outline: 0;
}
.mat-mdc-menu-item .mat-icon {
  flex-shrink: 0;
  margin-right: var(--%NS%mat-menu-item-spacing, 12px);
  height: var(--%NS%mat-menu-item-icon-size, 24px);
  width: var(--%NS%mat-menu-item-icon-size, 24px);
}
[dir=rtl] .mat-mdc-menu-item {
  text-align: right;
}
[dir=rtl] .mat-mdc-menu-item .mat-icon {
  margin-right: 0;
  margin-left: var(--%NS%mat-menu-item-spacing, 12px);
}
.mat-mdc-menu-item:not([disabled]):hover {
  background-color: var(--%NS%mat-menu-item-hover-state-layer-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) calc(var(--%NS%mat-sys-hover-state-layer-opacity) * 100%), transparent));
}
.mat-mdc-menu-item:not([disabled]).cdk-program-focused, .mat-mdc-menu-item:not([disabled]).cdk-keyboard-focused, .mat-mdc-menu-item:not([disabled]).mat-mdc-menu-item-highlighted {
  background-color: var(--%NS%mat-menu-item-focus-state-layer-color, color-mix(in srgb, var(--%NS%mat-sys-on-surface) calc(var(--%NS%mat-sys-focus-state-layer-opacity) * 100%), transparent));
}
@media (forced-colors: active) {
  .mat-mdc-menu-item {
    margin-top: 1px;
  }
}

.mat-mdc-menu-submenu-icon {
  width: var(--%NS%mat-menu-item-icon-size, 24px);
  height: 10px;
  fill: currentColor;
  padding-left: var(--%NS%mat-menu-item-spacing, 12px);
}
[dir=rtl] .mat-mdc-menu-submenu-icon {
  padding-right: var(--%NS%mat-menu-item-spacing, 12px);
  padding-left: 0;
}
[dir=rtl] .mat-mdc-menu-submenu-icon polygon {
  transform: scaleX(-1);
  transform-origin: center;
}
@media (forced-colors: active) {
  .mat-mdc-menu-submenu-icon {
    fill: CanvasText;
  }
}

.mat-mdc-menu-item .mat-mdc-menu-ripple {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  position: absolute;
  pointer-events: none;
}
`],encapsulation:2})})()}return n})();var kf=new S(`mat-menu-scroll-strategy`,{providedIn:`root`,factory:()=>{let n=I(le);return()=>Ft(n)}});var mi=new WeakMap;var Df=(()=>{class n{_canHaveBackdrop;_element=I(Dr);_viewContainerRef=I(xi$1);_menuItemInstance=I(pr,{optional:!0,self:!0});_dir=I(Ne,{optional:!0});_focusMonitor=I(ft);_ngZone=I(z);_injector=I(le);_scrollStrategy=I(kf);_changeDetectorRef=I(w0);_animationsDisabled=ue();_portal;_overlayRef=null;_menuOpen=!1;_closingActionsSubscription=q.EMPTY;_menuCloseSubscription=q.EMPTY;_pendingRemoval;_parentMaterialMenu;_parentInnerPadding;_openedBy=void 0;get _menu(){return this._menuInternal}set _menu(e){e!==this._menuInternal&&(this._menuInternal=e,this._menuCloseSubscription.unsubscribe(),e?(this._parentMaterialMenu,this._menuCloseSubscription=e.close.subscribe(t=>{this._destroyMenu(t),(t===`click`||t===`tab`)&&this._parentMaterialMenu&&this._parentMaterialMenu.closed.emit(t)})):this._destroyMenu(),this._menuItemInstance?._setTriggersSubmenu(this._triggersSubmenu()))}_menuInternal=null;constructor(e){this._canHaveBackdrop=e;let t=I(Cs,{optional:!0});this._parentMaterialMenu=t instanceof ui?t:void 0}ngOnDestroy(){this._menu&&this._ownsMenu(this._menu)&&mi.delete(this._menu),this._pendingRemoval?.unsubscribe(),this._menuCloseSubscription.unsubscribe(),this._closingActionsSubscription.unsubscribe(),this._overlayRef&&(this._overlayRef.dispose(),this._overlayRef=null)}get menuOpen(){return this._menuOpen}get dir(){return this._dir&&this._dir.value===`rtl`?`rtl`:`ltr`}_triggersSubmenu(){return!!(this._menuItemInstance&&this._parentMaterialMenu&&this._menu)}_closeMenu(){this._menu?.close.emit()}_openMenu(e){if(this._triggerIsAriaDisabled())return;let t=this._menu;if(this._menuOpen||!t)return;this._pendingRemoval?.unsubscribe();let r=mi.get(t);mi.set(t,this),r&&r!==this&&r._closeMenu();let o=this._createOverlay(t),a=o.getConfig(),s=a.positionStrategy;this._setPosition(t,s),this._canHaveBackdrop?a.hasBackdrop=t.hasBackdrop==null?!this._triggersSubmenu():t.hasBackdrop:a.hasBackdrop=t.hasBackdrop??!1,o.hasAttached()||(o.attach(this._getPortal(t)),t.lazyContent?.attach(this.menuData)),this._closingActionsSubscription=this._menuClosingActions().subscribe(()=>this._closeMenu()),t.parentMenu=this._triggersSubmenu()?this._parentMaterialMenu:void 0,t.direction=this.dir,e&&t.focusFirstItem(this._openedBy||`program`),this._setIsMenuOpen(!0),t instanceof ui&&(t._setIsOpen(!0),t._directDescendantItems.changes.pipe(Rl$1(t.close)).subscribe(()=>{s.withLockedPosition(!1).reapplyLastPosition(),s.withLockedPosition(!0)}))}focus(e,t){this._focusMonitor&&e?this._focusMonitor.focusVia(this._element,e,t):this._element.nativeElement.focus(t)}_destroyMenu(e){let t=this._overlayRef,r=this._menu;!t||!this.menuOpen||(this._closingActionsSubscription.unsubscribe(),this._pendingRemoval?.unsubscribe(),r instanceof ui&&this._ownsMenu(r)?(this._pendingRemoval=r._animationDone.pipe(gt$1(1)).subscribe(()=>{t.detach(),mi.has(r)||r.lazyContent?.detach()}),r._setIsOpen(!1)):(t.detach(),r?.lazyContent?.detach()),r&&this._ownsMenu(r)&&mi.delete(r),this.restoreFocus&&(e===`keydown`||!this._openedBy||!this._triggersSubmenu())&&this.focus(this._openedBy),this._openedBy=void 0,this._setIsMenuOpen(!1))}_setIsMenuOpen(e){e!==this._menuOpen&&(this._menuOpen=e,this._menuOpen?this.menuOpened.emit():this.menuClosed.emit(),this._triggersSubmenu()&&this._menuItemInstance._setHighlighted(e),this._changeDetectorRef.markForCheck())}_createOverlay(e){if(!this._overlayRef){let t=this._getOverlayConfig(e);this._subscribeToPositions(e,t.positionStrategy),this._overlayRef=pt(this._injector,t),this._overlayRef.keydownEvents().subscribe(r=>{this._menu instanceof ui&&this._menu._handleKeydown(r)})}return this._overlayRef}_getOverlayConfig(e){return new ht({positionStrategy:pn(this._injector,this._getOverlayOrigin()).withLockedPosition().withGrowAfterOpen().withTransformOriginOn(`.mat-menu-panel, .mat-mdc-menu-panel`),backdropClass:e.backdropClass||`cdk-overlay-transparent-backdrop`,panelClass:e.overlayPanelClass,scrollStrategy:this._scrollStrategy(),direction:this._dir||`ltr`,disableAnimations:this._animationsDisabled})}_subscribeToPositions(e,t){e.setPositionClasses&&t.positionChanges.subscribe(r=>{this._ngZone.run(()=>{let o=r.connectionPair.overlayX===`start`?`after`:`before`,a=r.connectionPair.overlayY===`top`?`below`:`above`;e.setPositionClasses(o,a)})})}_setPosition(e,t){let[r,o]=e.xPosition===`before`?[`end`,`start`]:[`start`,`end`],[a,s]=e.yPosition===`above`?[`bottom`,`top`]:[`top`,`bottom`],[c,d]=[a,s],[m,_]=[r,o],k=0;if(this._triggersSubmenu()){if(_=r=e.xPosition===`before`?`start`:`end`,o=m=r===`end`?`start`:`end`,this._parentMaterialMenu){if(this._parentInnerPadding==null){let p=this._parentMaterialMenu.items.first;this._parentInnerPadding=p?p._getHostElement().offsetTop:0}k=a===`bottom`?this._parentInnerPadding:-this._parentInnerPadding}}else e.overlapTrigger||(c=a===`top`?`bottom`:`top`,d=s===`top`?`bottom`:`top`);t.withPositions([{originX:r,originY:c,overlayX:m,overlayY:a,offsetY:k},{originX:o,originY:c,overlayX:_,overlayY:a,offsetY:k},{originX:r,originY:d,overlayX:m,overlayY:s,offsetY:-k},{originX:o,originY:d,overlayX:_,overlayY:s,offsetY:-k}])}_menuClosingActions(){let e=this._getOutsideClickStream(this._overlayRef),t=this._overlayRef.detachments(),r=this._parentMaterialMenu?this._parentMaterialMenu.closed:Sg(),o=this._parentMaterialMenu?this._parentMaterialMenu._hovered().pipe(rn(a=>this._menuOpen&&a!==this._menuItemInstance)):Sg();return Bg(e,r,o,t)}_getPortal(e){return(!this._portal||this._portal.templateRef!==e.templateRef)&&(this._portal=new rt(e.templateRef,this._viewContainerRef)),this._portal}_ownsMenu(e){return mi.get(e)===this}_triggerIsAriaDisabled(){return T0(this._element.nativeElement.getAttribute(`aria-disabled`))}static ɵfac=function(t){XE()};static ɵdir=VI({type:n})}return n})();var wm=(()=>{class n extends Df{_cleanupTouchstart;_hoverSubscription=q.EMPTY;get _deprecatedMatMenuTriggerFor(){return this.menu}set _deprecatedMatMenuTriggerFor(e){this.menu=e}get menu(){return this._menu}set menu(e){this._menu=e}menuData;restoreFocus=!0;menuOpened=new Fe;onMenuOpen=this.menuOpened;menuClosed=new Fe;onMenuClose=this.menuClosed;constructor(){super(!0);let e=I(La$1);this._cleanupTouchstart=e.listen(this._element.nativeElement,`touchstart`,t=>{gn(t)||(this._openedBy=`touch`)},{passive:!0})}triggersSubmenu(){return super._triggersSubmenu()}toggleMenu(){return this.menuOpen?this.closeMenu():this.openMenu()}openMenu(){this._openMenu(!0)}closeMenu(){this._closeMenu()}updatePosition(){this._overlayRef?.updatePosition()}ngAfterContentInit(){this._handleHover()}ngOnDestroy(){super.ngOnDestroy(),this._cleanupTouchstart(),this._hoverSubscription.unsubscribe()}_getOverlayOrigin(){return this._element}_getOutsideClickStream(e){return e.backdropClick()}_handleMousedown(e){fn(e)||(this._openedBy=e.button===0?`mouse`:void 0,this.triggersSubmenu()&&e.preventDefault())}_handleKeydown(e){let t=e.keyCode;(t===13||t===32)&&(this._openedBy=`keyboard`),this.triggersSubmenu()&&(t===39&&this.dir===`ltr`||t===37&&this.dir===`rtl`)&&(this._openedBy=`keyboard`,this.openMenu())}_handleClick(e){this.triggersSubmenu()?(e.stopPropagation(),this.openMenu()):this.toggleMenu()}_handleHover(){this.triggersSubmenu()&&this._parentMaterialMenu&&(this._hoverSubscription=this._parentMaterialMenu._hovered().subscribe(e=>{e===this._menuItemInstance&&!e.disabled&&this._parentMaterialMenu?._panelAnimationState!==`void`&&(this._openedBy=`mouse`,this._openMenu(!1))}))}static ɵfac=function(t){return new(t||n)};static ɵdir=VI({type:n,selectors:[[``,`mat-menu-trigger-for`,``],[``,`matMenuTriggerFor`,``]],hostAttrs:[1,`mat-mdc-menu-trigger`],hostVars:3,hostBindings:function(t,r){t&1&&ih$1(`click`,function(a){return r._handleClick(a)})(`mousedown`,function(a){return r._handleMousedown(a)})(`keydown`,function(a){return r._handleKeydown(a)}),t&2&&Kp(`aria-haspopup`,r.menu?`menu`:null)(`aria-expanded`,r.menuOpen)(`aria-controls`,r.menuOpen?r.menu?.panelId:null)},inputs:{_deprecatedMatMenuTriggerFor:[0,`mat-menu-trigger-for`,`_deprecatedMatMenuTriggerFor`],menu:[0,`matMenuTriggerFor`,`menu`],menuData:[0,`matMenuTriggerData`,`menuData`],restoreFocus:[0,`matMenuTriggerRestoreFocus`,`restoreFocus`]},outputs:{menuOpened:`menuOpened`,onMenuOpen:`onMenuOpen`,menuClosed:`menuClosed`,onMenuClose:`onMenuClose`},exportAs:[`matMenuTrigger`],features:[Vp$1]})}return n})();var aA=(()=>{class n{static ɵfac=function(t){return new(t||n)};static ɵmod=Op$1({type:n});static ɵinj=vs$1({imports:[Zn,Ke,te,Nt]})}return n})();function Ef(n,i){n&1&&Xp$1(0,`mat-icon`,7)}function Mf(n,i){n&1&&Xp$1(0,`mat-spinner`,6)}function Af(n,i){if(n&1){let e=wD();yi(0,`button`,4),ih$1(`click`,function(){Mu$1(e);let r=TD(2);return Su$1(r.deserialize())}),uD(1,Ef,1,0,`mat-icon`,7)(2,Mf,1,0,`mat-spinner`,6),Fc$1()}if(n&2){let e=TD(2);yh$1(`mat-icon-button-sm-32`,e.size===`small`),Jp$1(`matTooltip`,`Deserialize from `+(e.resource?.schema?.serialization?.file_type||`common format`))(`disabled`,e.isDeserializing),Kp(`aria-label`,`Deserialize from `+(e.resource?.schema?.serialization?.file_type||`common format`)),sE(),fD(e.isDeserializing?2:1)}}function If(n,i){n&1&&Xp$1(0,`mat-icon`,5)}function Nf(n,i){n&1&&Xp$1(0,`mat-spinner`,6)}function Tf(n,i){if(n&1){let e=wD();uD(0,Af,3,6,`button`,3),yi(1,`button`,4),ih$1(`click`,function(){Mu$1(e);let r=TD();return Su$1(r.serialize())}),uD(2,If,1,0,`mat-icon`,5)(3,Nf,1,0,`mat-spinner`,6),Fc$1()}if(n&2){let e=TD();fD(e.resource?.schema?.serialization?.reversible?0:-1),sE(),yh$1(`mat-icon-button-sm-32`,e.size===`small`),Jp$1(`matTooltip`,`Serialize to `+(e.resource?.schema?.serialization?.file_type||`common format`))(`disabled`,e.isSerializing),Kp(`aria-label`,`Serialize to `+(e.resource?.schema?.serialization?.file_type||`common format`)),sE(),fD(e.isSerializing?3:2)}}function Rf(n,i){n&1&&Xp$1(0,`mat-icon`,9)}function Of(n,i){n&1&&Xp$1(0,`mat-spinner`,6)}function Ff(n,i){if(n&1&&(yi(0,`button`,8),uD(1,Rf,1,0,`mat-icon`,9)(2,Of,1,0,`mat-spinner`,6),Fc$1()),n&2){let e=TD(),t=RD(3);yh$1(`mat-icon-button-sm-32`,e.size===`small`),Jp$1(`matMenuTriggerFor`,t)(`disabled`,e.isCustomActionRunning),sE(),fD(e.isCustomActionRunning?2:1)}}function Pf(n,i){if(n&1){let e=wD();yi(0,`button`,10),ih$1(`click`,function(){let r=Mu$1(e).$implicit,o=TD();return Su$1(o.runCustomAction(r))}),yi(1,`span`),rw(2),Fc$1()()}if(n&2){let e=i.$implicit;sE(2),_h$1(e.title)}}var bA=(()=>{class n{mainService;cdr;customActionService;snackBar;dialog;resource=null;hideCustomActions=!1;customActionsBlacklist=[];size=`default`;isSerializing=!1;isDeserializing=!1;isCustomActionRunning=!1;get customActions(){return(this.resource?.schema?.custom_actions||[]).filter(e=>!this.customActionsBlacklist.includes(e.method))}constructor(e,t,r,o,a){this.mainService=e,this.cdr=t,this.customActionService=r,this.snackBar=o,this.dialog=a}serialize(){return Yt$1(this,null,function*(){if(!this.resource)return;let e=this.resource.id,t=li(e);for(;t==`data`;)e=e.substring(0,e.length-t.length),t=li(e);this.resource.schema.serialization.is_directory?t+=`/`:t+=this.resource.schema.serialization.output_file_name_suffix||``;let r=yield this.mainService.api.saveFileDialog(t);if(r){this.isSerializing=!0,this.cdr.markForCheck();try{let o=yield this.mainService.api.serializeResource(this.resource.id,r,this.resource.schema.serialization.reversible_settings_patch);if(o&&o.length>0){let a=o.reduce((m,_)=>{let k=0;for(;k<m.length&&k<_.length&&m[k]===_[k];)k++;return m.substring(0,k)}),s=a.lastIndexOf(`/`),c=s!==-1?a.substring(0,s):a;this.snackBar.open(`Files exported`,`Open location`,{duration:1e4}).onAction().subscribe(()=>{this.mainService.api.openFileWithSystemApp(c)})}}finally{this.isSerializing=!1,this.cdr.markForCheck()}}})}deserialize(){return Yt$1(this,null,function*(){if(!this.resource)return;let e=this.resource.schema?.serialization?.import_guide;if(e&&!(yield this.confirmImportGuide(e)))return;let t=!!this.resource.schema?.serialization?.is_directory,r=null;if(t){let o=yield this.mainService.api.selectDirectoryDialog();o&&(r=[o])}else r=yield this.mainService.api.openFileDialog(!0);if(!(!r||r.length===0)){this.isDeserializing=!0,this.cdr.markForCheck();try{let o=yield this.mainService.deserializeResource(this.resource.id,r);o&&this.snackBar.open(`Imported: ${o}`,`OK`,{duration:8e3})}finally{this.isDeserializing=!1,this.cdr.markForCheck()}}})}confirmImportGuide(e){return Yt$1(this,null,function*(){let t=Cm[e];if((yield this.mainService.api.getGeneralConfig())[t]===!1)return!0;let o=yield dg(this.dialog.open(Sm,{data:{guide:e}}).afterClosed());return o?.dontShowAgain&&(yield this.mainService.api.patchGeneralConfig({[t]:!1})),!!o?.proceed})}runCustomAction(e){return Yt$1(this,null,function*(){if(this.resource){this.isCustomActionRunning=!0,this.cdr.markForCheck();try{yield this.customActionService.runCustomAction(this.resource.id,e)}finally{this.isCustomActionRunning=!1,this.cdr.markForCheck()}}})}static ɵfac=function(t){return new(t||n)(Mr(en),Mr(w0),Mr(xm),Mr(hr),Mr(Lt))};static ɵcmp=LI({type:n,selectors:[[`app-block-actions`]],inputs:{resource:`resource`,hideCustomActions:`hideCustomActions`,customActionsBlacklist:`customActionsBlacklist`,size:`size`},decls:6,vars:2,consts:[[`customActionsMenu`,`matMenu`],[`mat-icon-button`,``,`matTooltip`,`Run custom action`,`aria-label`,`Run custom action`,3,`matMenuTriggerFor`,`disabled`,`mat-icon-button-sm-32`],[`mat-menu-item`,``],[`mat-icon-button`,``,3,`matTooltip`,`mat-icon-button-sm-32`,`disabled`],[`mat-icon-button`,``,3,`click`,`matTooltip`,`disabled`],[`fontIcon`,`download`],[`mode`,`indeterminate`,`diameter`,`24`,`color`,`accent`],[`fontIcon`,`upload`],[`mat-icon-button`,``,`matTooltip`,`Run custom action`,`aria-label`,`Run custom action`,3,`matMenuTriggerFor`,`disabled`],[`fontIcon`,`bolt`],[`mat-menu-item`,``,3,`click`]],template:function(t,r){t&1&&(uD(0,Tf,4,7),uD(1,Ff,3,5,`button`,1),yi(2,`mat-menu`,null,0),gD(4,Pf,3,1,`button`,2,hD),Fc$1()),t&2&&(fD(r.resource?.schema?.serialization?0:-1),sE(),fD(!r.hideCustomActions&&r.customActions.length>0?1:-1),sE(3),mD(r.customActions))},dependencies:[Ki,hs,No,um,wm,ui,pr],styles:[`[_nghost-%COMP%]{display:flex;justify-content:flex-end}`],changeDetection:1})}return n})();export{Tt as $,u0 as $t,Lt as A,hr as At,Oo as B,oS as Bt,Kd as C,fE as Ct,La as D,gm as Dt,Ku as E,gE as Et,Ne as F,lm as Ft,Qt as G,rS as Gt,Pm as H,pr as Ht,Ni as I,lr as It,Rt as J,ss as Jt,Qx as K,rt as Kt,Nm as L,me as Lt,Me as M,iS as Mt,Mo as N,ii as Nt,Lm as O,gt as Ot,Nb as P,j_ as Pt,Tm as Q,tr as Qt,No as R,mr as Rt,Jx as S,en as St,Ki as T,ft as Tt,Po as U,qn as Ut,Or as V,ot as Vt,Pt as W,qp as Wt,Se as X,te as Xt,Sd as Y,su as Yt,Sn as Z,to as Zt,Gn as _,dm as _t,Ad as a,wm as an,Yn as at,JE as b,du as bt,Ci as c,xo as cn,Zn as ct,DM as d,aA as dt,ue as en,Uc as et,Dd as f,bA as ft,Fy as g,dl as gt,Fd as h,cs as ht,$k as i,wd as in,Xi as it,ME as j,hs as jt,Lo as k,hp as kt,Cn as l,yk as ln,Zp as lt,Eo as m,cr as mt,$d as n,um as nn,Wi as nt,Bt as o,wo as on,Yt as ot,Dm as p,cD as pt,Rm as q,si as qt,$h as r,vn as rn,Wn as rt,Ca as s,xm as sn,Zh as st,$a as t,ui as tn,Wh as tt,Ct as u,zm as un,Zt as ut,Id as v,dr as vt,Kh as w,fp as wt,Jo as x,eM as xt,J as y,dt as yt,On as z,nk as zt};