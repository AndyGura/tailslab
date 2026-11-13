import{A as Ue,B as e0,r as De}from"./chunk-VbVOOEOM.js";var p=e=>{let{sunDirection:t,sunLight:o}=e0(e),r=o.color;return{direction:[t.x,t.y,t.z],color:[r>>16&255,r>>8&255,r&255].map(a=>a/255*o.intensity)}};var u=new Ue().set(-1,0,0,0,1,0,0,0,1);var l=`skyCube`;var s=e=>e&&e.isCubeTexture?e:null;var x=(e,t)=>{let o=e?s(e.userData[l])??s(e.background):null;return o&&e&&(t.setFromMatrix4(new De().makeRotationFromEuler(e.backgroundRotation)).transpose(),o.isRenderTargetTexture||t.premultiply(u)),o};var d=`
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
}`;export{p as n,x as r,d as t};