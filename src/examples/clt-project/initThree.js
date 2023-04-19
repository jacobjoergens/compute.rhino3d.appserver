
import * as THREE from 'three';
import { ArcballControls } from 'three/addons/controls/ArcballControls.js';

export var scene, camera, renderer, controls

/**
 * Shows or hides the loading spinner
 */
export function showSpinner(enable) {
    if (enable)
        document.getElementById('loader').style.display = 'block'
    else
        document.getElementById('loader').style.display = 'none'
}

export async function init() {
    // Rhino models are z-up, so set this as the default
    THREE.Object3D.DefaultUp = new THREE.Vector3(0, 0, 1)

    scene = new THREE.Scene()
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000)
    
    const canvas = document.getElementById('mainCanvas')
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, canvas: canvas})
    renderer.setPixelRatio(window.devicePixelRatio)
    const mainContainer = document.getElementById('mainContainer')
    renderer.setSize(mainContainer.offsetWidth,  mainContainer.offsetHeight)
    // document.body.appendChild(renderer.domElement)

    // const layer_meshes = new rhino.Layer()
    // layer_meshes.name = 'Meshes'
    // layer_meshes.color = { r: 255, g: 255, b: 0, a: 255 }
    // doc.layers().add( layer_meshes )

    camera.position.set(0, 0, 50);
    camera.lookAt(0, 0, 0);
    const light = new THREE.DirectionalLight(0xffffff, 1)
    light.position.set(0,1,0)
    scene.add( light )

    // add some controls to orbit the camera
    controls = new ArcballControls(camera, renderer.domElement);
    controls.enableRotate = false; 
    controls.cursorZoom = true;
    controls.enableGrid = true;
    window.addEventListener('resize', onWindowResize, false)
    animate()
}

function animate() {
    requestAnimationFrame(animate)
    renderer.render(scene, camera)
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
    animate()
}