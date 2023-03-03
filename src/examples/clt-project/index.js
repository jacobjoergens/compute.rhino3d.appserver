import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.126.0/build/three.module.js'
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.126.0/examples/jsm/controls/OrbitControls.js'
import { Rhino3dmLoader } from 'https://cdn.jsdelivr.net/npm/three@0.126.0/examples/jsm/loaders/3DMLoader.js'
import rhino3dm from 'https://cdn.jsdelivr.net/npm/rhino3dm@0.15.0-beta/rhino3dm.module.js'

const downloadButton = document.getElementById("downloadButton")
downloadButton.onclick = download

// global variables
let _model = {
    // saved nurbs curves
    curves: [],
    // new nurbs curve
    points: null,
    // viewport for canvas
    viewport: null,
}

let rhino, doc
rhino3dm().then(async m => {
    console.log('Loaded rhino3dm.')
    rhino = m // global
    run()
    // init()
    // create()
})

// initialize canvas and model
function run() {
    let canvas = getCanvas()
    canvas.addEventListener('mousedown', onMouseDown)
    canvas.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    _model.points = new rhino.Point3dList()
    _model.viewport = new rhino.ViewportInfo()
    _model.viewport.screenPort = [0, 0, canvas.clientWidth, canvas.clientHeight]
    _model.viewport.setFrustum(-30,30,-30,30,1,1000)
    draw()
  }

function create () {

    const loader = new Rhino3dmLoader()
    loader.setLibraryPath( 'https://cdn.jsdelivr.net/npm/rhino3dm@0.15.0-beta/' )

    doc = new rhino.File3dm()

    // Create layers
    const layer_points = new rhino.Layer()
    layer_points.name = 'Points'
    layer_points.color = { r: 255, g: 0, b: 0, a: 255 }
    doc.layers().add( layer_points )

    const layer_curves = new rhino.Layer()
    layer_curves.name = 'Curves'
    layer_curves.color = { r: 0, g: 0, b: 0, a: 255 }
    doc.layers().add( layer_curves )

    const layer_meshes = new rhino.Layer()
    layer_meshes.name = 'Meshes'
    layer_meshes.color = { r: 255, g: 255, b: 0, a: 255 }
    doc.layers().add( layer_meshes )

    const layer_breps = new rhino.Layer()
    layer_breps.name = 'Breps'
    layer_breps.color = { r: 255, g: 255, b: 255, a: 255 }
    doc.layers().add( layer_breps )

    const layer_extrusions = new rhino.Layer()
    layer_extrusions.name = 'Extrusions'
    layer_extrusions.color = { r: 0, g: 255, b: 255, a: 255 }
    doc.layers().add( layer_extrusions )

    const layer_dots = new rhino.Layer()
    layer_dots.name = 'TextDots'
    layer_dots.color = { r: 0, g: 0, b: 255, a: 255 }
    doc.layers().add( layer_dots )

    // -- POINTS / POINTCLOUDS -- //

    const oa_points = new rhino.ObjectAttributes()
    oa_points.layerIndex = 0

    // POINTS

    const ptA = [0, 0, 0]
    const point = new rhino.Point( ptA )

    //doc.objects().add( point, oa_points )

    // POINTCLOUD

    const ptB = [ 10, 0, 0 ]
    const ptC = [ 10, 10, 0 ]
    const ptD = [ 0, 10, 0 ]
    const ptE = [ 20, 20, 20 ]
    const ptF = [ 30, 0, 0 ]
    const ptG = [ 35, 5, 0 ]
    const ptH = [ 40, -5, 0 ]
    const ptI = [ 45, 5, 0 ]
    const ptJ = [ 50, 0, 0 ]

    const red = { r: 255, g: 0, b: 0, a: 0 }

    const pointCloud = new rhino.PointCloud()
    pointCloud.add( ptA, red )
    pointCloud.add( ptB, red )
    pointCloud.add( ptC, red )
    pointCloud.add( ptD, red )
    pointCloud.add( ptE, red )
    pointCloud.add( ptF, red )
    pointCloud.add( ptG, red )
    pointCloud.add( ptH, red )
    pointCloud.add( ptI, red )
    pointCloud.add( ptJ, red )

    //doc.objects().add( pointCloud, oa_points )

    // -- CURVES -- //

    const oa_curves = new rhino.ObjectAttributes()
    oa_curves.layerIndex = 1

    // CURVE //

    const curvePoints = new rhino.Point3dList()
    curvePoints.add( ptF[0], ptF[1], ptF[2] )
    curvePoints.add( ptG[0], ptG[1], ptG[2] )
    curvePoints.add( ptH[0], ptH[1], ptH[2] )
    curvePoints.add( ptI[0], ptI[1], ptI[2] )
    curvePoints.add( ptJ[0], ptJ[1], ptJ[2] )

    const nurbsCurveD1 = rhino.NurbsCurve.create( false, 1, curvePoints )

    doc.objects().add( nurbsCurveD1, oa_curves )


    // create a copy of the doc.toByteArray data to get an ArrayBuffer
    let arr = new Uint8Array( doc.toByteArray() ).buffer

    loader.parse( arr, function ( object ) {

      // hide spinner
      document.getElementById('loader').style.display = 'none'
      console.log( object )
      scene.add( object )

      // enable download button
      downloadButton.disabled = false
  
    } )

}

// download button handler
function download () {
  let buffer = doc.toByteArray()
  saveByteArray( 'rhinoObjects.3dm', buffer )
}

function saveByteArray ( fileName, byte ) {
  let blob = new Blob( [ byte ], {type: 'application/octect-stream'} )
  let link = document.createElement( 'a' )
  link.href = window.URL.createObjectURL( blob )
  link.download = fileName
  link.click()
}

// get the location of the mouse on the canvas
let [x,y] = getXY(event)

// if this is a brand new curve, add the first control point
if (_model.points.count === 0) {
  _model.points.add(x, y, 0)
}

// add a new control point that will be saved on the next mouse click
// (the location of the previous control point is now frozen)
_model.points.add(x, y, 0)

// gets the canvas
function getCanvas() {
    return document.getElementById('canvas')
  }
  
  // gets the [x, y] location of the mouse in world coordinates
  function getXY(evt) {
    let canvas = getCanvas()
    let rect = canvas.getBoundingClientRect()
    let x = evt.clientX - rect.left
    let y = evt.clientY - rect.top
    let s2w = _model.viewport.getXform(rhino.CoordinateSystem.Screen, rhino.CoordinateSystem.World)
    let world_point = rhino.Point3d.transform([x,y,0], s2w)
    s2w.delete()
    return [world_point[0],world_point[1]]
  }

// BOILERPLATE //

let scene, camera, renderer

function init () {

  // Rhino models are z-up, so set this as the default
  THREE.Object3D.DefaultUp = new THREE.Vector3( 0, 0, 1 )

  scene = new THREE.Scene()
  scene.background = new THREE.Color( 1,1,1 )
  camera = new THREE.PerspectiveCamera( 45, window.innerWidth/window.innerHeight, 1, 1000 )
  camera.position.z = 50

  renderer = new THREE.WebGLRenderer( { antialias: true } )
  renderer.setPixelRatio( window.devicePixelRatio )
  renderer.setSize( window.innerWidth, window.innerHeight )
  document.body.appendChild( renderer.domElement )

  const controls = new OrbitControls( camera, renderer.domElement  )

  const light = new THREE.DirectionalLight()
  scene.add( light )

  window.addEventListener( 'resize', onWindowResize, false )

  animate()
}

function animate () {
  requestAnimationFrame( animate )
  renderer.render( scene, camera )
}
  
function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize( window.innerWidth, window.innerHeight )
  animate()
}