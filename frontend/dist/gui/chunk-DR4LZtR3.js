import{$n as ih,A as Cw,Dr as rn,Fr as te,L as Fc,Lt as Rl,Qt as Ty,Ur as w0,Y as I,bn as Yt,cn as Vp,dt as Ml,hn as Xp,jt as Pn,kr as sE,ot as LI,t as $,ti as yi,tr as iy,tt as Jp,wt as Nw}from"./chunk-6B6O2DWR.js";import{Dt as gm,H as Pm}from"./chunk-CamVZSRl.js";import"./chunk-CcLbjPvh.js";import{i as Gt}from"./main-INAPFNEV.js";import{A as Ue,D as St,F as Vn,R as _t,Z as rt,c as Gt$1,d as I$1,l as He,q as na,r as De,rt as zt,y as Kt}from"./chunk-VbVOOEOM.js";import{r as x}from"./chunk-BkMRjAQN.js";import{n as o,t as n}from"./chunk-Db4r5fXk.js";import{t as nt}from"./chunk-7fq5373T.js";var P=n=>{let r=n.hue/255*6,e=n.saturation/255,t=n.brightness/255,o=a=>{let i=(a+r)%6;return Math.round(255*(t-t*e*Math.max(0,Math.min(i,4-i,1))))};return o(5)<<16|o(3)<<8|o(1)};var S=(n,r)=>{let[e,t,o]=[n>>16,n>>8&255,n&255],a=Math.max(e,t,o),i=a-Math.min(e,t,o),s=0;if(i>0){let l=a===e?(t-o)/i:a===t?(o-e)/i+2:(e-t)/i+4;s=Math.min(255,Math.floor((l+6)%6/6*256))}return{hue:s,saturation:a?Math.round(i/a*255):0,brightness:a,transparency:r}};var ae=n=>{let{hue:r,saturation:e,brightness:t}=n,o=f=>Math.max(0,Math.min(255,f));if(t<=0)return[0,0,0];if(e<=0)return[o(t),o(t),o(t)];let a=r*6>>8,i=r*6-a*256,s=t*(256-e)>>8,l=(256-(e*i+128>>8))*t>>8,c=(256-(e*(256-i)+128>>8))*t>>8;return[[t,c,s],[l,t,s],[s,t,c],[s,l,t],[c,s,t],[t,s,l]][a].map(o)};var d=[224,164,96,32];var ce=[1,2,3,4];var le=[7,6,9,8];var he=/^(?:hp|mp)_\d+_[HM][LR]([FMR])W(?=__|_damaged$|$)/i;var fe=/^hp_\d+_O[LR]B(?=__|_damaged$|$)/i;var me=.33;var ue=64;var pe=(n,r,e)=>{let t=!r&&e?.05:.5;return .25*Math.max(-t,Math.min(t,n/30))};var de=n=>{let r=n.source.data?.src;return r&&/\.png(\?.*)?$/.test(r)?r.replace(/\.png(\?.*)?$/,`_paint_mask.png$1`):null};var F=class{colors;fce4;mask={value:null};enabled={value:0};constructor(r,e){this.colors=r,this.fce4=e}};function ve(n,r){let e=n.onBeforeCompile,t=n.customProgramCacheKey;n.onBeforeCompile=(o,a)=>{e.call(n,o,a),o.uniforms.fcePaintColors=r.colors,o.uniforms.fcePaintFce4=r.fce4,o.uniforms.fcePaintMask=r.mask,o.uniforms.fcePaintEnabled=r.enabled,o.uniforms.fcePaintFiltered={get value(){let i=n.map;return i&&i.magFilter!==1003?1:0}},o.fragmentShader=o.fragmentShader.replace(`#include <map_pars_fragment>`,`#include <map_pars_fragment>
        uniform vec4 fcePaintColors[ 4 ];
        uniform float fcePaintFce4;
        uniform sampler2D fcePaintMask;
        uniform float fcePaintEnabled;
        uniform float fcePaintFiltered;
        float fceShr8( float a ) { return floor( a / 256.0 ); }
        // fce3HsbToRgb: integer math in floats, exact below 2^24
        vec3 fce3HsbToRgb( vec4 hsb ) {
          float h = hsb.x, s = hsb.y, v = hsb.z;
          if ( v <= 0.0 ) {
            return vec3( 0.0 );
          }
          if ( s <= 0.0 ) {
            return vec3( clamp( v, 0.0, 255.0 ) );
          }
          float sector = fceShr8( h * 6.0 );
          float x = h * 6.0 - sector * 256.0;
          float p = fceShr8( v * ( 256.0 - s ) );
          float q = fceShr8( ( 256.0 - fceShr8( s * x + 128.0 ) ) * v );
          float t = fceShr8( ( 256.0 - fceShr8( s * ( 256.0 - x ) + 128.0 ) ) * v );
          vec3 rgb = sector < 0.5 ? vec3( v, t, p ) : sector < 1.5 ? vec3( q, v, p ) : sector < 2.5 ? vec3( p, v, t )
            : sector < 3.5 ? vec3( p, q, v ) : sector < 4.5 ? vec3( t, p, v ) : vec3( v, p, q );
          return clamp( rgb, 0.0, 255.0 );
        }
        // fce3PaintColor
        vec3 fce3PaintColor( float blue, vec4 color ) {
          float blue8 = floor( blue / 8.0 ) * 8.0;
          float factor = color.w == 255.0 ? blue8 : blue8 / ( 255.0 - color.w );
          return fce3HsbToRgb( vec4( color.xy, min( 255.0, floor( color.z * factor ) ), color.w ) );
        }
        vec4 fcePaint( vec4 sampled, vec2 uv ) {
          float alpha = floor( textureLod( fcePaintMask, uv, 0.0 ).a * 255.0 + 0.5 );
          vec3 texel = floor( sRGBTransferOETF( sampled ).rgb * 255.0 + 0.5 );
          vec3 painted;
          if ( fcePaintFce4 < 0.5 ) {
            // fce3TexelColor: every texel of the texture goes through the 16-bit texture
            if ( alpha > 0.0 && alpha < 128.0 ) {
              texel = fce3PaintColor( texel.b, fcePaintColors[ 0 ] );
            } else if ( alpha > 0.0 && alpha < 255.0 ) {
              texel = fce3PaintColor( texel.b, fcePaintColors[ 1 ] );
            }
            painted = floor( floor( texel / 8.0 ) * 255.0 / 31.0 + 0.5 );
          } else {
            if ( alpha == 0.0 || alpha == 255.0 ) {
              return sampled;
            }
            vec3 paint = alpha >= ${(d[0]+d[1])/2}.0 ? fcePaintColors[ 0 ].rgb
              : alpha >= ${(d[1]+d[2])/2}.0 ? fcePaintColors[ 1 ].rgb
              : alpha >= ${(d[2]+d[3])/2}.0 ? fcePaintColors[ 2 ].rgb
              : fcePaintColors[ 3 ].rgb;
            painted = min( floor( texel * paint / 128.0 + 0.5 ), 255.0 );
          }
          return vec4( sRGBTransferEOTF( vec4( painted / 255.0, 1.0 ) ).rgb, sampled.a );
        }`).replace(`#include <map_fragment>`,`#include <map_fragment>
        #ifdef USE_MAP
        if ( fcePaintEnabled > 0.5 ) {
          ivec2 size = textureSize( map, 0 );
          vec4 painted;
          if ( fcePaintFiltered > 0.5 ) {
            // the 4 texels of a bilinear sample painted, then blended (base level only)
            vec2 p = vMapUv * vec2( size ) - 0.5;
            ivec2 i0 = ivec2( floor( p ) );
            vec2 f = p - floor( p );
            ivec2 last = size - 1;
            ivec2 c00 = clamp( i0, ivec2( 0 ), last );
            ivec2 c10 = clamp( i0 + ivec2( 1, 0 ), ivec2( 0 ), last );
            ivec2 c01 = clamp( i0 + ivec2( 0, 1 ), ivec2( 0 ), last );
            ivec2 c11 = clamp( i0 + ivec2( 1, 1 ), ivec2( 0 ), last );
            vec2 texelSize = 1.0 / vec2( size );
            vec4 t00 = fcePaint( texelFetch( map, c00, 0 ), ( vec2( c00 ) + 0.5 ) * texelSize );
            vec4 t10 = fcePaint( texelFetch( map, c10, 0 ), ( vec2( c10 ) + 0.5 ) * texelSize );
            vec4 t01 = fcePaint( texelFetch( map, c01, 0 ), ( vec2( c01 ) + 0.5 ) * texelSize );
            vec4 t11 = fcePaint( texelFetch( map, c11, 0 ), ( vec2( c11 ) + 0.5 ) * texelSize );
            painted = mix( mix( t00, t10, f.x ), mix( t01, t11, f.x ), f.y );
          } else {
            // nearest: the sample is the texel, the mask is read at its centre
            vec2 texel = clamp( floor( vMapUv * vec2( size ) ), vec2( 0.0 ), vec2( size - 1 ) );
            painted = fcePaint( sampledDiffuseColor, ( texel + 0.5 ) / vec2( size ) );
          }
          diffuseColor = vec4( diffuse, opacity ) * painted;
        }
        #endif`)},n.customProgramCacheKey=()=>`${t.call(n)}|fce-paint`,n.needsUpdate=!0}var ge=n=>{let r=2*Math.PI,e=(Math.atan2(n[0],n[2])/r-.5)*r,t=(Math.atan2(Math.hypot(n[0],n[2]),n[1])/r-.25)*r,[o,a,i,s]=[Math.sin(e),Math.cos(e),Math.sin(t),Math.cos(t)],l=[a,0,-o,0,1,0,o,0,a],c=[1,0,0,0,s,i,0,-i,s],h=[];for(let f=0;f<3;f++)for(let m=0;m<3;m++)h.push(l[f*3]*c[m]+l[f*3+1]*c[3+m]+l[f*3+2]*c[6+m]);return h};var Ce={normal:127/255,high:1};var T=class{map={value:null};cube={value:null};mode={value:0};matrix={value:new Ue};worldMatrix={value:new Ue};eye={value:new I$1(0,0,1)};cubeMatrix={value:new Ue}};function xe(n,r,e,t){let o=n.onBeforeCompile,a=n.customProgramCacheKey;n.onBeforeCompile=(i,s)=>{o.call(n,i,s),i.uniforms.fceChromeMap=r.map,i.uniforms.fceChromeCube=r.cube,i.uniforms.fceChromeMode=r.mode,i.uniforms.fceChromeMatrix=r.matrix,i.uniforms.fceChromeWorldMatrix=r.worldMatrix,i.uniforms.fceChromeEye=r.eye,i.uniforms.fceChromeCubeMatrix=r.cubeMatrix,i.uniforms.fceChromeColor={value:e},i.uniforms.fceChromeFlipY={get value(){return r.map.value?.flipY?1:0}},i.uniforms.fceChromeFiltered={get value(){return r.map.value&&r.map.value.magFilter!==1003?1:0}},i.uniforms.fceChromeSrgb={get value(){return r.map.value?.colorSpace===`srgb`?1:0}},i.vertexShader=i.vertexShader.replace(`#include <fog_pars_vertex>`,`#include <fog_pars_vertex>
        ${t?`attribute vec3 _game_normal;`:``}
        uniform mat3 fceChromeMatrix;
        uniform mat3 fceChromeWorldMatrix;
        uniform vec3 fceChromeEye;
        uniform float fceChromeFlipY;
        varying vec2 vFceChromeUv;
        varying vec3 vFceChromeReflect;`).replace(`#include <fog_vertex>`,`#include <fog_vertex>
        vec3 fceChromeNormal = fceChromeMatrix * ${t?`_game_normal`:`normal`};
        float fceChromeM = 0.707106 / sqrt( ( abs( fceChromeNormal.z ) + 1.0 ) * 2.0 );
        vFceChromeUv = fceChromeNormal.xy * fceChromeM + 0.5;
        // D3D: v = 0 is the top row
        if ( fceChromeFlipY > 0.5 ) {
          vFceChromeUv.y = 1.0 - vFceChromeUv.y;
        }
        vec3 fceChromeWorldNormal = normalize( fceChromeWorldMatrix * ${t?`_game_normal`:`normal`} );
        vFceChromeReflect = reflect( -fceChromeEye, fceChromeWorldNormal );`),i.fragmentShader=i.fragmentShader.replace(`#include <fog_pars_fragment>`,`#include <fog_pars_fragment>
        uniform sampler2D fceChromeMap;
        uniform samplerCube fceChromeCube;
        uniform mat3 fceChromeCubeMatrix;
        uniform float fceChromeMode;
        uniform float fceChromeColor;
        uniform float fceChromeFiltered;
        uniform float fceChromeSrgb;
        varying vec2 vFceChromeUv;
        varying vec3 vFceChromeReflect;
        // a texel of the 4444 chrome texture, 0..1
        vec4 fceChromeTexel( ivec2 c ) {
          vec4 t = texelFetch( fceChromeMap, c, 0 );
          if ( fceChromeSrgb > 0.5 ) {
            t = vec4( sRGBTransferOETF( t ).rgb, t.a );
          }
          return floor( floor( t * 255.0 + 0.5 ) / 16.0 ) / 15.0;
        }
        // the scene's sky in a world direction as a 4444 chrome texel, 0..1 (linear texels to the output's sRGB)
        vec4 fceChromeSkyTexel( vec3 direction ) {
          vec3 d = normalize( direction );
          vec4 t = vec4(
            sRGBTransferOETF( vec4( textureCube( fceChromeCube, fceChromeCubeMatrix * d ).rgb, 1.0 ) ).rgb,
            // fce3SkyChromeAlpha
            0.6 * smoothstep( -0.1, 0.1, d.z ) );
          return floor( floor( clamp( t, 0.0, 1.0 ) * 255.0 + 0.5 ) / 16.0 ) / 15.0;
        }`).replace(`#include <premultiplied_alpha_fragment>`,`#include <premultiplied_alpha_fragment>
        if ( fceChromeMode > 0.5 ) {
          vec4 env;
          if ( fceChromeMode > 1.5 ) {
            env = fceChromeSkyTexel( vFceChromeReflect );
          } else {
            ivec2 size = textureSize( fceChromeMap, 0 );
            ivec2 last = size - 1;
            if ( fceChromeFiltered > 0.5 ) {
              vec2 p = vFceChromeUv * vec2( size ) - 0.5;
              ivec2 i0 = ivec2( floor( p ) );
              vec2 f = p - floor( p );
              env = mix(
                mix( fceChromeTexel( clamp( i0, ivec2( 0 ), last ) ), fceChromeTexel( clamp( i0 + ivec2( 1, 0 ), ivec2( 0 ), last ) ), f.x ),
                mix( fceChromeTexel( clamp( i0 + ivec2( 0, 1 ), ivec2( 0 ), last ) ), fceChromeTexel( clamp( i0 + ivec2( 1, 1 ), ivec2( 0 ), last ) ), f.x ),
                f.y );
            } else {
              env = fceChromeTexel( clamp( ivec2( floor( vFceChromeUv * vec2( size ) ) ), ivec2( 0 ), last ) );
            }
          }
          vec3 fceChromeAdd = env.rgb * fceChromeColor * env.a;
          #ifdef PREMULTIPLIED_ALPHA
          gl_FragColor.rgb += fceChromeAdd;
          #else
          gl_FragColor.rgb += fceChromeAdd / max( gl_FragColor.a, 1.0 / 255.0 );
          #endif
        }`)},n.customProgramCacheKey=()=>`${a.call(n)}|fce-chrome-${t?`game`:`normal`}-${e}`,n.needsUpdate=!0}var M=class n{version;wheels=[];lights=null;spinTurns={front:0,rear:0};paintTextures=new Map;paintedMaterials=new Set;disposed=!1;chrome=new T;chromeMeshes=[];get hasChrome(){return this.chromeMeshes.length>0}chromeEnabled=!0;chromeTexture=null;colors;colorUniforms={value:[new _t,new _t,new _t,new _t]};getColor(r){return this.colors[r]}setColor(r,e){this.colors[r]=$({},e),this.updateColorUniforms()}get isPaintable(){return this.paintTextures.size>0}animationTimer=null;_speed=0;get speed(){return this._speed}set speed(r){this._speed=r,this.updateAnimationTimer()}_handbrake=!1;get handbrake(){return this._handbrake}set handbrake(r){this._handbrake=r}spinTicks=0;spinStart=0;updateAnimationTimer(){if(!!this.animationTimer!=(this._speed!==0&&!this.disposed)){if(this.animationTimer){clearInterval(this.animationTimer),this.animationTimer=null;return}this.spinTicks=0,this.spinStart=performance.now(),this.animationTimer=setInterval(()=>this.spinWheels(),1e3/60)}}spinWheels(){if(this.version===3){let r=Math.floor((performance.now()-this.spinStart)*ue/1e3);for(;this.spinTicks<r;this.spinTicks++)for(let e of[`front`,`rear`]){let t=this.spinTurns[e]+pe(this._speed,e===`front`,this._handbrake);this.spinTurns[e]=t-Math.trunc(t)}}else{let r=this.spinTurns.front+this._speed/me/60/(2*Math.PI);this.spinTurns.front=this.spinTurns.rear=r-Math.trunc(r)}this.updateWheels()}_steeringAngle=0;get steeringAngle(){return this._steeringAngle}set steeringAngle(r){this._steeringAngle=r,this.updateWheels()}get showLights(){return!!this.lights?.visible}set showLights(r){this.lights&&(this.lights.visible=r)}get hasWheels(){return this.wheels.length>0}get hasLights(){return!!this.lights}constructor(r,e,t,o,a=de){this.version=e,this.colors=o.map(c=>$({},c)),this.updateColorUniforms(),this.root=r,e===3&&this.setupChrome(r),this.setupPaint(r,a);let i={},s=null;r.traverse(c=>{if(!(c instanceof He))return;let h=/^(hp|mp)_(\d+)/.exec(c.name);if(!h)return;let f=+h[2];(e===3?f===0:/^hp_\d+_HB(?=__|$)/i.test(c.name))&&!s&&(s=c);let v=null;if(e===3)for(let g of[ce,le])g.includes(f)&&(v={isFront:g.indexOf(f)<2,spins:!0});else{let g=he.exec(c.name);g?v={isFront:g[1].toUpperCase()===`F`,spins:!0}:fe.test(c.name)&&(v={isFront:!0,spins:!1})}v&&(i[f]=i[f]||$({meshes:[]},v)).meshes.push(c)});for(let c of Object.values(i)){let h=new Kt;for(let m of c.meshes)m.geometry.computeBoundingBox(),h.union(m.geometry.boundingBox);let f=h.getCenter(new I$1);for(let m of c.meshes)m.geometry.translate(-f.x,-f.y,-f.z),m.position.copy(f),m.rotation.order=`ZXY`;this.wheels.push(c)}let l=t.filter(c=>n.lightColor(e,c.name)!==null);if(s&&l.length>0){this.lights=new zt;for(let c of l){let h=new He(new na(.05,8,8),new Gt$1({color:n.lightColor(e,c.name)}));h.name=c.name,h.position.set(...c.position),this.lights.add(h)}s.add(this.lights)}}root;setupChrome(r){r.traverse(e=>{if(!(e instanceof He)||!/^(hp|mp)_0(?:_|$)/.test(e.name))return;let t=e.name.replace(/_damaged$/,``),a=Ce[e.userData?.fceChrome??(/_matte$/.test(t)?`none`:/_high_chrome$/.test(t)?`high`:`normal`)];if(a===void 0)return;let i=!!e.geometry.getAttribute(`_game_normal`),s=c=>{let h=c.clone();return h.transparent&&(h.premultipliedAlpha=!0),xe(h,this.chrome,a,i),h};e.material=e.material instanceof Array?e.material.map(s):s(e.material);let l=e.onBeforeRender;e.onBeforeRender=(c,h,f,...m)=>{l.call(e,c,h,f,...m),this.disposed||this.updateChrome(f.getWorldPosition(this.cameraPosition),h,e)},this.chromeMeshes.push(e)})}cameraPosition=new I$1;updateChrome(r,e,t=this.chromeMeshes[0]){let o=this.chrome,a=x(e,o.cubeMatrix.value);if(o.map.value=this.chromeTexture,o.cube.value=a,o.mode.value=!t||!this.chromeEnabled?0:this.chromeTexture?1:a?2:0,o.mode.value===0)return;this.root.updateWorldMatrix(!0,!1),t.updateWorldMatrix(!0,!1);let i=r.clone().sub(new I$1().setFromMatrixPosition(this.root.matrixWorld)),s=new Ue().setFromMatrix4(new De().extractRotation(t.matrixWorld));o.worldMatrix.value.copy(s),o.eye.value.copy(i).normalize();let l=ge([i.x,i.z,i.y]),c=new Ue().set(l[0],l[3],l[6],l[1],l[4],l[7],l[2],l[5],l[8]),h=new Ue().set(1,0,0,0,0,1,0,1,0);o.matrix.value.copy(c.multiply(h).multiply(s))}setupPaint(r,e){let t={value:this.version===4?1:0};r.traverse(o=>{if(!(o instanceof He))return;let a=o.material instanceof Array?o.material:[o.material];for(let i of a){let s=i.map;if(!s||this.paintedMaterials.has(i))continue;let l=this.paintTextures.get(s);if(!l){let c=e(s);if(!c)continue;let h=new F(this.colorUniforms,t);this.paintTextures.set(s,h),new Vn().load(c,f=>{if(this.disposed){f.dispose();return}f.flipY=s.flipY,f.magFilter=St,f.minFilter=St,f.generateMipmaps=!1,f.needsUpdate=!0,h.mask.value=f,h.enabled.value=1},void 0,()=>{}),l=h}ve(i,l),this.paintedMaterials.add(i)}})}updateColorUniforms(){this.colors.forEach((r,e)=>{if(this.version===3)this.colorUniforms.value[e]?.set(r.hue,r.saturation,r.brightness,r.transparency);else{let t=P(r);this.colorUniforms.value[e]?.set(t>>16,t>>8&255,t&255,0)}})}static lightColor(r,e){let t=e.toUpperCase();if(r===4){if(t.startsWith(`:`))return null;let o={W:16777164,R:16711680,B:255,O:16744448,Y:16776960}[t[1]];return o===void 0?16711935:o}return t.startsWith(`H`)?16777164:t.startsWith(`T`)?16711680:t.startsWith(`M`)?t[2]===`L`?16711680:255:16711935}updateWheels(){for(let{meshes:r,isFront:e,spins:t}of this.wheels)for(let o of r){let a=t?-this.spinTurns[e?`front`:`rear`]*2*Math.PI:0;o.rotation.set(a,0,e?this._steeringAngle:0)}}dispose(){this.disposed=!0,this.animationTimer&&(clearInterval(this.animationTimer),this.animationTimer=null);for(let r of this.paintTextures.values())r.enabled.value=0,r.mask.value?.dispose(),r.mask.value=null}};var be=([n,r,e])=>n<<16|r<<8|e;var ze=(()=>{class n$1 extends gm{customControls=[];previewPaths$=new Pn(null);cdr=I(w0);previewViewFilters=[];extraPath=null;meshController=null;destroyed$=new te;ngOnChanges(e){e.hasOwnProperty(`resourceSchema`)&&(this.previewViewFilters=this.version===4?[this.previewViewFilter,this.damageViewFilter]:[this.previewViewFilter]),(e.hasOwnProperty(`resourceId`)||e.hasOwnProperty(`resourceData`))&&this.loadPreview().then()}ngAfterViewInit(){return Yt(this,null,function*(){this.changes.change$.pipe(Rl(this.destroyed$),rn(e=>!!(this.resourceId&&e.startsWith(this.resourceId))),Ml(150)).subscribe(()=>Yt(this,null,function*(){yield this.loadPreview()}))})}onObjectLoaded(e){return Yt(this,null,function*(){try{this.meshController?.dispose();let t=[];if(this.extraPath)try{t=(yield(yield fetch(this.extraPath)).json()).dummies||[]}catch(s){console.warn(`Cannot load FCE dummies`,s)}let o$1=this.paints,a=new M(e,this.version,t,o$1.map(s=>s.color));this.meshController=a;let i=[];a.isPaintable&&o$1.forEach(({label:s,color:l},c)=>i.push({label:s,type:`color`,value:this.version===3?be(ae(l)):P(l),change:h=>this.debounced(()=>a.setColor(c,S(h,l.transparency)))})),a.hasChrome&&i.push({label:`Chrome`,type:`checkbox`,value:a.chromeEnabled,change:s=>a.chromeEnabled=s}),a.hasLights&&i.push({label:`Show lights`,type:`checkbox`,value:a.showLights,change:s=>a.showLights=s}),a.hasWheels&&(i.push(n(s=>a.speed=s),o(s=>a.steeringAngle=s)),this.version===3&&i.push({label:`Handbrake`,type:`checkbox`,value:a.handbrake,change:s=>a.handbrake=s})),this.customControls=i.length>0?[{title:`NFS${this.version} car features`,controls:i}]:[],this.cdr.markForCheck()}catch(t){console.error(t)}})}get version(){return this.resourceSchema?.block_class_mro?.startsWith(`Fce4Geometry`)?4:3}get paints(){let e=this.resourceData,t=(o,a,i,s)=>({label:o,color:i>0?$({},e[a][0]):S(s,127)});return this.version===4?[t(`Primary color`,`primary_colors`,e?.num_colors,16711680),t(`Interior color`,`interior_colors`,e?.num_colors,4210752),t(`Secondary color`,`secondary_colors`,e?.num_colors,8421504),t(`Driver hair color`,`driver_hair_colors`,e?.num_colors,3153936)]:[t(`Primary color`,`primary_colors`,e?.num_primary_colors,16711680),t(`Secondary color`,`secondary_colors`,e?.num_secondary_colors,8421504)]}debounceTimer=null;debounced(e){this.debounceTimer&&clearTimeout(this.debounceTimer),this.debounceTimer=setTimeout(e,50)}serializerSettings={geometry__save_obj:!0,geometry__save_blend:!1,geometry__export_to_gg_web_engine:!1};loadPreview(){return Yt(this,null,function*(){if(this.previewPaths$.next(null),this.resourceId){let e=yield this.mainService.api.serializeResource(this.resourceId,null,this.serializerSettings);this.extraPath=e.find(t=>t.endsWith(`_extra.json`))||null,this.previewPaths$.next([e.find(t=>t.endsWith(`.obj`)),e.find(t=>t.endsWith(`.mtl`))])}})}previewObjectGroupFunc(e){let t=/^(?:hp|mp|lp|tp|part)_\d+(?:_.*?)?(?=__|_damaged$|$)/.exec(e.name);return t?t[0]:e.name}damageViewFilter={name:`Damage`,filterGroups:[`Not damaged`,`Damaged`],checkedIndex:0,pickFunction:e=>e.name.endsWith(`_damaged`)?1:0};previewViewFilter={name:`LOD`,filterGroups:[`High-poly`,`Medium-poly`,`Low-poly`,`Tiny`,`Other`],checkedIndex:0,pickFunction:e=>{let t=[`hp_`,`mp_`,`lp_`,`tp_`].findIndex(o=>e.name.startsWith(o));return t>=0?t:4}};ngOnDestroy(){this.meshController?.dispose(),this.destroyed$.next(),this.destroyed$.complete()}static ɵfac=(()=>{let e;return function(o){return(e||(e=Ty(n$1)))(o||n$1)}})();static ɵcmp=LI({type:n$1,selectors:[[`app-fce-geometry-block-ui`]],features:[Vp,iy],decls:3,vars:14,consts:[[3,`onObjectLoaded`,`paths`,`viewFilters`,`visibilityGroupFunction`,`customControls`],[3,`resourceId`,`resourceName`,`resourceSchema`,`resourceData`,`resourceDescription`,`hideName`,`hideBlockActions`,`disabled`]],template:function(t,o){t&1&&(yi(0,`app-obj-viewer`,0),Cw(1,`async`),ih(`onObjectLoaded`,function(i){return o.onObjectLoaded(i)}),Fc(),Xp(2,`app-compound-block-ui`,1)),t&2&&(Jp(`paths`,Nw(1,12,o.previewPaths$))(`viewFilters`,o.previewViewFilters)(`visibilityGroupFunction`,o.previewObjectGroupFunc)(`customControls`,o.customControls),sE(2),Jp(`resourceId`,o.resourceId)(`resourceName`,o.resourceName)(`resourceSchema`,o.resourceSchema)(`resourceData`,o.resourceData)(`resourceDescription`,o.resourceDescription)(`hideName`,o.hideName)(`hideBlockActions`,o.hideBlockActions)(`disabled`,o.disabled))},dependencies:[nt,Gt,Pm],encapsulation:2})}return n$1})();export{ze as FceGeometryBlockUiComponent};