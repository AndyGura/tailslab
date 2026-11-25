import{V as e0,j as Ue,r as De}from"./chunk-BOthpRJt.js";var k=t=>{let{sunDirection:e,sunLight:o}=e0(t),r=o.color;return{direction:[e.x,e.y,e.z],color:[r>>16&255,r>>8&255,r&255].map(a=>a/255*o.intensity)}};var u=new Ue().set(-1,0,0,0,1,0,0,0,1);var f=`skyCube`;var l=`skyTopColor`;var C=t=>{let e=t?.userData[l];return typeof e==`number`?e&16777215:16777215};var p=`trackLight`;var S=t=>{let e=t?.userData[p];return typeof e==`function`?e:null};var i=t=>t&&t.isCubeTexture?t:null;var y=(t,e)=>{let o=t?i(t.userData[f])??i(t.background):null;return o&&t&&(e.setFromMatrix4(new De().makeRotationFromEuler(t.backgroundRotation)).transpose(),o.isRenderTargetTexture||e.premultiply(u)),o};var d=`
vec3 sceneSkyMean( samplerCube cube, mat3 matrix, float side ) {
  vec3 sum = vec3( 0.0 );
  float weight = 0.0;
  for ( int i = 0; i < 3; i++ ) {
    float e = ( float( i ) + 0.5 ) * 0.5235988;
    for ( int j = 0; j < 8; j++ ) {
      float a = float( j ) * 0.7853982;
      vec3 d = vec3( cos( e ) * cos( a ), cos( e ) * sin( a ), side * sin( e ) );
      sum += textureLod( cube, matrix * d, 0.0 ).rgb * sin( e );
      weight += sin( e );
    }
  }
  vec3 c = clamp( sum / weight, 0.0, 1.0 );
  return mix( c * 12.92, pow( c, vec3( 1.0 / 2.4 ) ) * 1.055 - 0.055, step( 0.0031308, c ) );
}`;export{y as a,k as i,S as n,d as r,C as t};