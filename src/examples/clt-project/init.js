import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.126.0/build/three.module.js'

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, .1, 1000);
const renderer = new THREE.WebGLRenderer({alpha: true});
renderer.setSize(window.innerWidth, window.innerHeight*.9);
document.body.appendChild(renderer.domElement);

// Create a button element
export const button = document.createElement("button");
// Set the button text
button.innerHTML = "rhino compute";


// Add the button to the document body
document.body.appendChild(button);

export { scene, camera, renderer };

