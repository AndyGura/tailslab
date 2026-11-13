import{$n as ih,A as Cw,Dr as rn,Fr as te,L as Fc,Lt as Rl,Qt as Ty,Ur as w0,Y as I,bn as Yt,cn as Vp,dt as Ml,hn as Xp,jt as Pn,kr as sE,ot as LI,ti as yi,tr as iy,tt as Jp,wt as Nw}from"./chunk-6B6O2DWR.js";import{Dt as gm,H as Pm}from"./chunk-CamVZSRl.js";import"./chunk-CcLbjPvh.js";import{i as Gt}from"./main-INAPFNEV.js";import{A as Ue,F as Vn,O as T0,R as _t,Z as rt,d as I$1,l as He,n as Ci,p as Ie}from"./chunk-VbVOOEOM.js";import{n as p,r as x$1,t as d}from"./chunk-BkMRjAQN.js";import{n as o,t as n}from"./chunk-Db4r5fXk.js";import{t as nt}from"./chunk-7fq5373T.js";var ie={space:`camera`,directions:[[6.82,-6.1,-8.56],[-5,-1,0],[1.28,-1.17,1.28]],colors:[[80,80,80],[64,64,64],[128,128,180]],ambient:[32,32,32]};var w=new Float32Array(1);var ne=new Int32Array(w.buffer);var ce=l=>(w[0]=l,ne[0]);var pe=l=>(ne[0]=l,w[0]);var he=(l,t)=>(l=Math.fround(l),[l,Math.fround(Math.fround(ce(Math.fround(t)))-Math.fround(l*1065353216))]);var re=he(-.5,pe(1064354972));var _=class{directions={value:[new I$1,new I$1,new I$1]};colors={value:[new I$1,new I$1,new I$1]};ambient={value:new _t};cameraSpace={value:1};cube={value:null};cubeMatrix={value:new Ue};envMode={value:1};sceneLight={value:0}};var x=class{vectors={value:[new _t,new _t,new _t,new _t]};lit={value:0};env={value:0};paint={value:0};alphaTest={value:1};blend={value:10};repeat={value:new Ie}};function ue(l,t,e,i,s){let a=l.onBeforeCompile,r=l.customProgramCacheKey;l.onBeforeCompile=(n,p)=>{a.call(l,n,p),Object.assign(n.uniforms,{ps2LightDirections:t.directions,ps2LightColors:t.colors,ps2Ambient:t.ambient,ps2CameraSpace:t.cameraSpace,ps2Cube:t.cube,ps2CubeMatrix:t.cubeMatrix,ps2EnvMode:t.envMode,ps2SceneLight:t.sceneLight,ps2Vectors:e.vectors,ps2Lit:e.lit,ps2Env:e.env,ps2Paint:e.paint,ps2AlphaTest:e.alphaTest,ps2Blend:e.blend,ps2Repeat:e.repeat}),n.uniforms.ps2MapSrgb={get value(){return l.map?.colorSpace===`srgb`?1:0}},n.vertexShader=n.vertexShader.replace(`#include <fog_pars_vertex>`,`#include <fog_pars_vertex>
        ${i?`attribute vec3 _game_normal;`:``}
        uniform vec3 ps2LightDirections[ 3 ];
        uniform vec3 ps2LightColors[ 3 ];
        uniform vec4 ps2Ambient;
        uniform float ps2CameraSpace;
        uniform vec4 ps2Vectors[ 4 ];
        uniform float ps2Lit;
        uniform float ps2Paint;
        uniform float ps2EnvMode;
        uniform float ps2Env;
        uniform float ps2SceneLight;
        uniform samplerCube ps2Cube;
        uniform mat3 ps2CubeMatrix;
        varying vec4 vPs2Color;
        varying vec4 vPs2EnvColor;
        varying vec3 vPs2Reflect;
        ${d}
        // nfs6Ps2Pow
        float ps2Pow( float x, vec2 q ) {
          return intBitsToFloat( int( float( floatBitsToInt( x ) ) * q.x + q.y ) );
        }`).replace(`#include <fog_vertex>`,`#include <fog_vertex>
        {
          vec3 n = ${i?`_game_normal`:`normal`};
          vec3 ps2N = length( n ) > 0.0 ? normalize( mat3( modelMatrix ) * n ) * length( n ) : vec3( 0.0 );
          vec3 ps2V = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz - cameraPosition;
          vec3 ps2R = ps2V - 2.0 * dot( ps2N, ps2V ) * ps2N;
          // nfs6Ps2Reflect, NFS6_PS2_RSQRT
          ps2R *= ps2Pow( dot( ps2R, ps2R ), vec2( ${re[0].toFixed(1)}, ${re[1].toFixed(1)} ) );
          vPs2Reflect = ps2R;
          // the raw vertex colour, 0..255 (OBJ colours are sRGB to three.js, GLB COLOR_0 alpha is / 128)
          #if defined( USE_COLOR_ALPHA )
          vec4 c = vec4( color.rgb, color.a * 128.0 / 255.0 );
          #elif defined( USE_COLOR )
          vec4 c = vec4( color.rgb, 128.0 / 255.0 );
          #else
          vec4 c = vec4( 128.0 / 255.0 );
          #endif
          ${s?`c.rgb = mix( c.rgb * 12.92, pow( max( c.rgb, 0.0 ), vec3( 1.0 / 2.4 ) ) * 1.055 - 0.055, step( 0.0031308, c.rgb ) );`:``}
          c = floor( c * 255.0 + 0.5 );
          vec4 q0 = ps2Vectors[ 0 ];
          vec4 q3 = ps2Vectors[ 3 ];
          if ( ps2Lit > 0.5 ) {
            // nfs6Ps2VertexLight
            vec2 q = ps2Paint > 0.5 ? q3.xy : q0.xy;
            vec3 rgb = ps2Ambient.rgb;
            if ( ps2SceneLight > 0.5 ) {
              // the hemisphere ambient of the scene's sky, 128 = 1
              float up = length( ps2N ) > 0.0 ? normalize( ps2N ).z * 0.5 + 0.5 : 0.5;
              rgb = mix( sceneSkyMean( ps2Cube, ps2CubeMatrix, -1.0 ), sceneSkyMean( ps2Cube, ps2CubeMatrix, 1.0 ), up )
                * 128.0;
            }
            float alpha = ps2Paint > 0.5 ? q3.z : ps2Ambient.w;
            float s0 = 0.0;
            for ( int i = 0; i < 3; i++ ) {
              vec3 l = ps2CameraSpace > 0.5
                ? transpose( mat3( viewMatrix ) ) * ( ps2LightDirections[ i ] * vec3( 1.0, -1.0, -1.0 ) )
                : ps2LightDirections[ i ];
              l = normalize( l );
              float s = ps2Pow( max( dot( ps2R, l ), q0.z ), q );
              s0 = i == 0 ? s : s0;
              rgb += ps2LightColors[ i ] * ( ps2Vectors[ 1 ].rgb * max( dot( ps2N, l ), 0.0 ) + ps2Vectors[ 2 ].rgb * s );
            }
            alpha += q3.w * s0 * ps2Paint;
            rgb *= 1.0 + ( c.rgb - 255.0 ) * q0.w;
            vPs2Color = floor( clamp( vec4( rgb, alpha ), 0.0, 255.0 ) );
          } else {
            vPs2Color = c;
          }
          // nfs6Ps2EnvAlpha: R'z of the environment map view, the camera's (forward = -z of the view matrix rows)
          vec3 forward = -vec3( viewMatrix[ 0 ][ 2 ], viewMatrix[ 1 ][ 2 ], viewMatrix[ 2 ][ 2 ] );
          float envAlpha = mod( trunc( ps2Vectors[ 1 ].w + ps2Vectors[ 2 ].w * -dot( ps2R, forward ) ), 256.0 );
          vPs2EnvColor = vec4( ps2Paint > 0.5 ? vPs2Color.rgb : vec3( 128.0 ), envAlpha );
        }`),n.fragmentShader=n.fragmentShader.replace(`#include <fog_pars_fragment>`,`#include <fog_pars_fragment>
        uniform samplerCube ps2Cube;
        uniform mat3 ps2CubeMatrix;
        uniform float ps2EnvMode;
        uniform float ps2Env;
        uniform float ps2Paint;
        uniform float ps2AlphaTest;
        uniform float ps2Blend;
        uniform float ps2MapSrgb;
        uniform vec2 ps2Repeat;
        varying vec4 vPs2Color;
        varying vec4 vPs2EnvColor;
        varying vec3 vPs2Reflect;
        #ifdef USE_MAP
        // a texel as stored, 0..255 RGB, alpha 0..128 (the PNG alpha is doubled)
        vec4 ps2Texel( ivec2 p ) {
          ivec2 size = textureSize( map, 0 );
          p = ivec2(
            ps2Repeat.x > 0.5 ? ( p.x % size.x + size.x ) % size.x : clamp( p.x, 0, size.x - 1 ),
            ps2Repeat.y > 0.5 ? ( p.y % size.y + size.y ) % size.y : clamp( p.y, 0, size.y - 1 ) );
          vec4 t = texelFetch( map, p, 0 );
          if ( ps2MapSrgb > 0.5 ) {
            t = vec4( sRGBTransferOETF( t ).rgb, t.a );
          }
          t = floor( t * 255.0 + 0.5 );
          return vec4( t.rgb, t.a >= 255.0 ? 128.0 : floor( t.a / 2.0 ) );
        }
        #endif`).replace(`#include <opaque_fragment>`,`#include <opaque_fragment>
        {
          #ifdef USE_MAP
          // bilinear (GS TEX1 MMAG 1)
          vec2 p = vMapUv * vec2( textureSize( map, 0 ) ) - 0.5;
          ivec2 i0 = ivec2( floor( p ) );
          vec2 f = p - floor( p );
          vec4 texel = mix(
            mix( ps2Texel( i0 ), ps2Texel( i0 + ivec2( 1, 0 ) ), f.x ),
            mix( ps2Texel( i0 + ivec2( 0, 1 ) ), ps2Texel( i0 + ivec2( 1, 1 ) ), f.x ),
            f.y );
          texel = floor( texel );
          #else
          vec4 texel = vec4( 128.0 );
          #endif
          // nfs6Ps2Modulate
          vec4 ps2Out = min( floor( texel * vPs2Color / 128.0 ), 255.0 );
          if ( ps2AlphaTest > 0.5 && ps2Out.a < 48.0 ) {
            discard;
          }
          vec3 ps2Add = vec3( 0.0 );
          if ( ps2Env > 0.5 && ps2EnvMode > 0.5 ) {
            vec3 d = normalize( vPs2Reflect );
            vec3 envTexel = floor(
              sRGBTransferOETF( vec4( textureCube( ps2Cube, ps2CubeMatrix * d ).rgb, 1.0 ) ).rgb * 255.0 + 0.5 );
            vec3 cs = min( floor( envTexel * vPs2EnvColor.rgb / 128.0 ), 255.0 );
            // front end: the vertex alpha (environment texel alpha 0x80); race paints: the main pass alpha
            float a = ps2EnvMode > 1.5 && ps2Paint > 0.5 ? ps2Out.a : vPs2EnvColor.a;
            ps2Add = floor( cs * a / 128.0 );
          }
          float alpha = ps2Blend == 10.0 ? 1.0 : min( ps2Out.a / 128.0, 1.0 );
          // blending adds the environment pass whole
          vec3 rgb = ps2Blend == 10.0
            ? min( ps2Out.rgb + ps2Add, 255.0 )
            : ps2Out.rgb + ps2Add / max( alpha, 1.0 / 255.0 );
          gl_FragColor = vec4( sRGBTransferEOTF( vec4( clamp( rgb / 255.0, 0.0, 1.0 ), 1.0 ) ).rgb, alpha );
        }`)},l.customProgramCacheKey=()=>`${r.call(l)}|nfs6-ps2-car-${i?`game`:`normal`}-${s?`srgb`:`linear`}`,l.needsUpdate=!0}var de=/^(?:hp|mp|lp|vlp)_(tire|brake|wheel_blur)_(fl|fr|rr|rl)(?:__|$)/;var g=class{info;skins;baseUrl;wheels=[];spinAngle=0;materials={};originalMaps=new Map;textureLoader=new Vn;textures={};animationTimer=null;lightingUniforms=new _;shaded=[];envEnabled=!0;_skin=null;get skin(){return this._skin}set skin(t){let e=this.skins.find(i=>i.name===t);e&&(this._skin=t,this.setMap(`skin`,e.texture),e.texture_b&&this.setMap(`skin_b`,e.texture_b),this.updateMaterials())}_raceMaterials=!1;get raceMaterials(){return this._raceMaterials}set raceMaterials(t){this._raceMaterials=t,this.updateMaterials()}_lighting=ie;get lighting(){return this._lighting}set lighting(t){this._lighting=t,this.updateLights()}_sceneLighting=null;get sceneLighting(){return this._sceneLighting}set sceneLighting(t){this._sceneLighting=t,this.updateLights()}get hasGameShading(){return this.shaded.length>0}_headlightsOn=!1;get headlightsOn(){return this._headlightsOn}set headlightsOn(t){this._headlightsOn=t,this.setLight(`headlight`,t)}_brakeLightsOn=!1;get brakeLightsOn(){return this._brakeLightsOn}set brakeLightsOn(t){this._brakeLightsOn=t,this.setLight(`brakelight`,t)}_speed=0;get speed(){return this._speed}set speed(t){let e=this._speed!==0;this._speed=t,e!==(t!==0)&&(this.animationTimer&&(clearInterval(this.animationTimer),this.animationTimer=null),t!==0&&(this.animationTimer=setInterval(()=>{this.spinAngle-=this._speed/this.wheelRadius/60,this.updateWheels()},1e3/60)))}_steeringAngle=0;get steeringAngle(){return this._steeringAngle}set steeringAngle(t){this._steeringAngle=t,this.updateWheels()}get hasWheels(){return this.wheels.length>0}get hasLights(){return Object.keys(this.info.lights).some(t=>!!this.materials[t])}get wheelRadius(){return this.info.wheels[0]?.radius||.33}constructor(t,e,i,s,a={}){this.info=e,this.skins=i,this.baseUrl=s,this.lighting=ie,t.traverse(r=>{if(!(r instanceof He))return;let n=r.geometry,p=e.meshes?.[r.name]||e.meshes?.[r.parent?.name||``];p&&!(r.material instanceof Array)&&this.shade(r,p,!!a.srgbVertexColors);for(let c of r.material instanceof Array?r.material:[r.material]){!p&&n.getAttribute(`color`)&&!c.vertexColors&&(c.vertexColors=!0,c.needsUpdate=!0);let m=this.materials[c.name]||=[];m.includes(c)||(m.push(c),this.originalMaps.set(c,c.map||null))}let o=de.exec(r.name),h=o&&e.wheels.find(c=>c.name===o[2]);if(o&&h){let c=new I$1(...h.position);n.translate(-c.x,-c.y,-c.z),r.position.add(c),r.rotation.order=`ZXY`,this.wheels.push({mesh:r,isFront:o[2].startsWith(`f`),spins:o[1]!==`brake`})}}),this.skins.length>0&&this.materials.skin&&(this._skin=this.skins[0].name),this.updateMaterials()}shade(t,e,i){let s=t.material.clone();t.material=s;let a=this.info.textures?.[s.name],r=new x;r.lit.value=e.vu_flags&128?1:0,r.env.value=e.vu_flags&256?1:0,r.paint.value=a?.vertex_lit_env?1:0,r.alphaTest.value=a&&a.alpha_test?1:0,r.blend.value=a?.alpha_blend??10;let n=s.map;r.repeat.value.set(a?a.repeat[0]?1:0:n?.wrapS===1e3?1:0,a?a.repeat[1]?1:0:n?.wrapT===1e3?1:0),s.transparent=r.blend.value!==10,s.blending=r.blend.value===72?2:1,r.blend.value!==10&&(s.depthWrite=!1),s.alphaTest=0,s.toneMapped=!1;let p=t.geometry;p.getAttribute(`color`)&&(s.vertexColors=!0),ue(s,this.lightingUniforms,r,!!p.getAttribute(`_game_normal`),i),this.shaded.push({uniforms:r,lightingMaterial:e.lighting_material});let o=t.onBeforeRender;t.onBeforeRender=(h,c,m,...le)=>{o.call(t,h,c,m,...le),this.updateEnvironment(c)}}updateLights(){let t=this.lightingUniforms,e=this._sceneLighting,i=e?{space:`world`,directions:[e.direction,[0,0,1],[0,0,1]],colors:[e.color.map(s=>s*128),[0,0,0],[0,0,0]],ambient:this._lighting.ambient}:this._lighting;i.directions.forEach((s,a)=>t.directions.value[a].set(...s)),i.colors.forEach((s,a)=>t.colors.value[a].set(...s)),t.ambient.value.set(...i.ambient,128),t.cameraSpace.value=i.space===`camera`?1:0}updateMaterials(){let t=this.skins.find(e=>e.name===this._skin)?.lighting_material||null;for(let{uniforms:e,lightingMaterial:i}of this.shaded){let s=i===`CARSKIN`?t:i,a=s&&this.info.lighting_materials?.[s]||this.info.lighting_materials?.Default,r=a?this._raceMaterials?a.race:a.frontend:new Array(16).fill(0);e.vectors.value.forEach((n,p)=>n.fromArray(r,p*4))}}updateEnvironment(t){let e=this.lightingUniforms,i=x$1(t,e.cubeMatrix.value);e.cube.value=i,e.envMode.value=this.envEnabled&&i?this._raceMaterials?2:1:0,e.sceneLight.value=this._sceneLighting&&i?1:0}texture(t){return this.textures[t]||=this.textureLoader.loadAsync(this.baseUrl+t)}setMap(t,e){for(let i of this.materials[t]||[]){let s=this.originalMaps.get(i);!e||!s||this.texture(e).then(a=>{let r=a.clone();r.flipY=s.flipY,r.wrapS=s.wrapS,r.wrapT=s.wrapT,r.colorSpace=s.colorSpace,r.anisotropy=s.anisotropy,r.magFilter=s.magFilter,r.minFilter=s.minFilter,r.needsUpdate=!0,i.map=r,i.needsUpdate=!0})}}setLight(t,e){let i=this.info.lights[t],s=e?i?.on:i?.off;s&&this.setMap(t,s)}updateWheels(){for(let{mesh:t,isFront:e,spins:i}of this.wheels)t.rotation.set(i?this.spinAngle:0,0,e?this._steeringAngle:0)}dispose(){this.animationTimer&&(clearInterval(this.animationTimer),this.animationTimer=null)}};var ae=`Showroom`;var oe=`Scene`;var Oe=(()=>{class l extends gm{previewPaths$=new Pn(null);cdr=I(w0);customControls=[];carPath=null;skinsPath=null;meshController=null;destroyed$=new te;ngAfterViewInit(){return Yt(this,null,function*(){this.changes.change$.pipe(Rl(this.destroyed$),rn(e=>!!(this.resourceId&&e.startsWith(this.resourceId))),Ml(150)).subscribe(()=>Yt(this,null,function*(){yield this.loadPreview()}))})}ngOnChanges(e){(e.hasOwnProperty(`resourceId`)||e.hasOwnProperty(`resourceData`))&&this.loadPreview().then()}loadPreview(){return Yt(this,null,function*(){if(this.previewPaths$.next(null),this.resourceId){let e=yield this.mainService.api.serializeResource(this.resourceId,null,{geometry__save_obj:!0,geometry__save_blend:!1,geometry__export_to_gg_web_engine:!1});this.carPath=e.find(i=>i.endsWith(`/car.json`))||null,this.skinsPath=e.find(i=>i.endsWith(`/skins.json`))||null,this.previewPaths$.next([e.find(i=>i.endsWith(`.obj`)),e.find(i=>i.endsWith(`.mtl`))])}})}onObjectLoaded(e){return Yt(this,null,function*(){if(this.meshController?.dispose(),this.meshController=null,this.customControls=[],!this.carPath){this.cdr.markForCheck();return}try{let i=o=>Yt(this,null,function*(){try{return o?yield(yield fetch(o)).json():null}catch(h){return console.warn(`Cannot load ${o}`,h),null}}),s=yield i(this.carPath),a=(yield i(this.skinsPath))||[],n$1=new g(e,s,a,this.carPath.substring(0,this.carPath.lastIndexOf(`/`)+1),{srgbVertexColors:!0});this.meshController=n$1;let p$1=[];if(n$1.skin&&a.length>1){let o=h=>`${h.label} (${h.name})`;p$1.push({label:`Paint`,type:`radio`,options:a.map(o),value:o(a[0]),change:h=>n$1.skin=a.find(c=>o(c)===h)?.name||null})}n$1.hasGameShading&&p$1.push({label:`Lighting`,type:`radio`,options:[ae,oe],value:ae,change:o=>n$1.sceneLighting=o===oe?p(T0):null},{label:`Reflections`,type:`checkbox`,value:n$1.envEnabled,change:o=>n$1.envEnabled=o},{label:`Race materials`,type:`checkbox`,value:n$1.raceMaterials,change:o=>n$1.raceMaterials=o}),n$1.hasLights&&p$1.push({label:`Headlights`,type:`checkbox`,value:n$1.headlightsOn,change:o=>n$1.headlightsOn=o},{label:`Brake lights`,type:`checkbox`,value:n$1.brakeLightsOn,change:o=>n$1.brakeLightsOn=o}),n$1.hasWheels&&p$1.push(n(o=>n$1.speed=o),o(o=>n$1.steeringAngle=o)),this.customControls=p$1.length>0?[{title:`Car features`,controls:p$1}]:[]}catch(i){console.error(i)}this.cdr.markForCheck()})}previewViewFilters=[{name:`LOD`,filterGroups:[`High-poly`,`Medium-poly`,`Low-poly`,`Lowest-poly`,`Wheel blur`,`Scuffs`],checkedIndex:0,pickFunction:e=>{if(e.name.includes(`_wheel_blur_`))return 4;if(e.name.includes(`_scuffs__`))return 5;let i=[`hp_`,`mp_`,`lp_`,`vlp_`].findIndex(s=>e.name.startsWith(s));return i>=0?i:0}}];ngOnDestroy(){this.meshController?.dispose(),this.destroyed$.next(),this.destroyed$.complete()}static ɵfac=(()=>{let e;return function(s){return(e||(e=Ty(l)))(s||l)}})();static ɵcmp=LI({type:l,selectors:[[`app-nfs6-ps2-car-block-ui`]],features:[Vp,iy],decls:3,vars:13,consts:[[3,`onObjectLoaded`,`paths`,`viewFilters`,`customControls`],[3,`resourceId`,`resourceName`,`resourceSchema`,`resourceData`,`resourceDescription`,`hideName`,`hideBlockActions`,`disabled`]],template:function(i,s){i&1&&(yi(0,`app-obj-viewer`,0),Cw(1,`async`),ih(`onObjectLoaded`,function(r){return s.onObjectLoaded(r)}),Fc(),Xp(2,`app-compound-block-ui`,1)),i&2&&(Jp(`paths`,Nw(1,11,s.previewPaths$))(`viewFilters`,s.previewViewFilters)(`customControls`,s.customControls),sE(2),Jp(`resourceId`,s.resourceId)(`resourceName`,s.resourceName)(`resourceSchema`,s.resourceSchema)(`resourceData`,s.resourceData)(`resourceDescription`,s.resourceDescription)(`hideName`,s.hideName)(`hideBlockActions`,s.hideBlockActions)(`disabled`,s.disabled))},dependencies:[nt,Gt,Pm],encapsulation:2})}return l})();export{Oe as Nfs6Ps2CarBlockUiComponent};