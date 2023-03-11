// Import libraries
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.125.0/build/three.module.js'
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.125.0/examples/jsm/controls/OrbitControls.js'
import { Rhino3dmLoader } from 'https://cdn.jsdelivr.net/npm/three@0.125.0/examples/jsm/loaders/3DMLoader.js'
import rhino3dm from 'https://cdn.jsdelivr.net/npm/rhino3dm@0.15.0-beta/rhino3dm.module.js'
import { RhinoCompute } from 'https://cdn.jsdelivr.net/npm/compute-rhino3d@0.13.0-beta/compute.rhino3d.module.js'

// reference the definition
const definitionName = 'CLT-Project.gh'

// globals
let rhino, definition, doc

let crvPoints

rhino3dm().then(async m => {
    console.log('Loaded rhino3dm.')
    rhino = m // global
    crvPoints = [];
    RhinoCompute.url = "http://localhost:8081/" // RhinoCompute server url. Use http://localhost:8081 if debugging locally.
    RhinoCompute.apiKey = getAuth('RHINO_COMPUTE_KEY')  // RhinoCompute server api key. Leave blank if debugging locally.

    //source a .gh / .ghx file in the same directory
    let url = definitionName
    let res = await fetch(url)
    let buffer = await res.arrayBuffer()
    definition = new Uint8Array(buffer)

    //initialize scene, camera, renderer
    init();
    //stage three.js components
    stage();
})

let dottedGeometry, dottedLine
let crossings = new THREE.Group()
let previewGroup

let solidGeometry, solidLine

//solidLine variables
let vertices = [];
let curves =  new THREE.Group();

//snapLine variables
let h_snapLine =[];
let v_snapLine = [];

function stage() {
    dottedGeometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0), 
        new THREE.Vector3(0, 0, 0)
    ]);
    const dottedMaterial = new THREE.LineDashedMaterial({
        color: 0xbfffbf,
        dashSize: 0.25,
        gapSize: 0.25,
        opacity: 0.75,
        transparent: true
    });
    dottedLine = new THREE.Line(dottedGeometry, dottedMaterial);
    dottedLine.computeLineDistances();
    dottedLine.visible = false;
    scene.add(dottedLine);

    solidGeometry = new THREE.BufferGeometry();
    solidGeometry.setAttribute('position', new THREE.Float32BufferAttribute([], 3));
    const solidMaterial = new THREE.LineBasicMaterial({ color: 0xbfffbf });
    solidLine = new THREE.LineSegments(solidGeometry, solidMaterial);
    scene.add(solidLine);

    console.log("running");
    showSpinner(false);
    renderer.domElement.addEventListener('click', onMouseDown);
    renderer.domElement.addEventListener('mousemove', onMouseMove);
    renderer.domElement.addEventListener('mouseup',onMouseUp)
    computeButton.onclick = compute
    // computeButton.addEventListener('click', () => {
    //     fetch('/python', {
    //       method: 'POST'
    //     })
    //     .then(response => {
    //       console.log('Python script executed successfully!');
    //     })
    //     .catch(error => {
    //       console.error('Error running Python script:', error);
    //     });
    //   });
}

function onMouseDown(event){
    let point = getXY(event);
    event.preventDefault();
    if (crossings.children.length > 0) {
        crossings.traverse((child) => {
            if (child instanceof THREE.Mesh) {
                if(child.material.color.equals(new THREE.Color('green'))){
                    closePolygon();
                }else{
                child.material.color.set('red');
                }
            }
        });
        renderer.render(scene, camera);
        return;
    }
    if (vertices.length > 0) {
        const positionAttribute = dottedGeometry.getAttribute('position');
        
        if (vertices.length == 1) {
            vertices[0] = new THREE.Vector3().fromBufferAttribute(positionAttribute, 0);
            crvPoints.push(new rhino.Point3dList());
            crvPoints[crvPoints.length-1].add(...vertices[0].toArray());
        }
        const endpoint = new THREE.Vector3().fromBufferAttribute(positionAttribute, 1);

        // add solid line to scene
        vertices.push(endpoint);
        crvPoints[crvPoints.length-1].add(...endpoint.toArray())
        updateSolidLine();
    } else {
        // add first vertex
        vertices.push(point);
        updateSolidLine();
    }

    const vertex = vertices[vertices.length - 1];

    if (vertices.length > 1) {
        const lastVertex = vertices[vertices.length - 2];
        let secondLast;
        if (vertices.length > 2) {
            secondLast = vertices[vertices.length - 3];
        }
        setSnapLines(vertex, lastVertex, secondLast);
    }
    
    scene.add(curves);
    //render scene
    renderer.render(scene, camera);
}

function onMouseMove(event){
    event.preventDefault();
    let point = getXY(event);

    if (vertices.length > 0) {
        if (previewGroup) {
            previewGroup[0].visible = false;
            previewGroup[1].visible = false;
            previewGroup = null;
        }

        if (crossings.children.length>0) {
            crossings.visible = false;
            while (crossings.children.length > 0) {
                crossings.remove(crossings.children[0]);
            }
            scene.remove(crossings);
        }

        const lastVertex = vertices[vertices.length - 1];
        const dx = Math.abs(point.x - lastVertex.x);
        const dy = Math.abs(point.y - lastVertex.y);
        let snap_intersects, orthogonal_vertex;
        let snapSet = [h_snapLine, v_snapLine];
        const order = [lastVertex, point];
        let intersects;

        if (dx > dy) { // horizontal line
            order.reverse();
            snapSet.reverse();
        } 

        const nextVertex = new THREE.Vector3(order[0].x, order[1].y, 0);
        let direction = new THREE.Vector3().subVectors(nextVertex, lastVertex);

        if(vertices.length>1){
            const parallel = lastVertex.clone().sub(vertices[vertices.length - 2]).normalize();
            if (direction.dot(parallel) < 0) {
                order.reverse();
                snapSet.reverse();
                nextVertex.set(order[0].x, order[1].y, 0);
                direction.subVectors(nextVertex, lastVertex);
            }
        }
        const orthocaster = new THREE.Raycaster(nextVertex, direction.normalize());
        if (vertices.length > 2) {
            const snaplines = snapSet[0].map(el => el[0]);
            snap_intersects = orthocaster.intersectObjects(snaplines);
            if (snap_intersects && snap_intersects[0] && snap_intersects[0].distance<.5) {
                console.log("snapped")
                orthogonal_vertex = drawPreview(snap_intersects[0].object, lastVertex);
                if (orthogonal_vertex) {
                    order[order.indexOf(point)] = orthogonal_vertex;
                    nextVertex.set(order[0].x, order[1].y, 0);
                }
            }
        }

        const intersect_caster = new THREE.Raycaster(lastVertex, direction.normalize());
        if (vertices.length > 3) {
            intersects = intersect_caster.intersectObjects([solidLine,curves]);
            if (intersects && intersects.length > 0) {
                for (const intersect of intersects.slice(1)) {
                    if(intersect.distance <= nextVertex.distanceTo(lastVertex)) {
                        if (nextVertex.distanceTo(vertices[0]) <= 1) {
                            const circle = drawCircle(intersect.point, 'green', true);
                            crossings.add(circle);
                            crossings.visible = true;
                            scene.add(crossings);
                            nextVertex.set(vertices[0].x,vertices[0].y,0);
                        } else {
                            const circle = drawCircle(intersect.point, 0xbb6a79, true);
                            crossings.add(circle);
                            crossings.visible = true;
                            scene.add(crossings);
                        }
                    }
                }
            }
        }
        updateDottedGeometry(lastVertex, nextVertex);
    }
    // render scene
    renderer.render(scene, camera);
}

function onMouseUp(event){
    if(crossings.children.length>0){
        crossings.traverse((child) => {
            if (child instanceof THREE.Mesh) {
              child.material.color.set(0xbb6a79);
            }
          });
        renderer.render(scene, camera);
        return;
    }
}

function getXY(evt) {
    const rect = renderer.domElement.getBoundingClientRect();
    let mouse = new THREE.Vector2();
    const plane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
    let raycaster = new THREE.Raycaster();
    let point = new THREE.Vector3();

    mouse.x = ((evt.clientX - rect.left) / (rect.right - rect.left)) * 2 - 1;
    mouse.y = - ((evt.clientY - rect.top) / (rect.bottom - rect.top)) * 2 + 1;

    // calculate intersection point with plane
    raycaster.setFromCamera(mouse, camera);
    raycaster.ray.intersectPlane(plane, point);
    return point
}

function updateSolidLine() {
    solidGeometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices.flatMap(v => v.toArray()), 3));
    const indices = [];
    for (let i = 0; i < vertices.length - 1; i++) {
      indices.push(i, i + 1);
    }
    solidGeometry.setIndex(indices);
    solidLine.geometry.boundingSphere = null;
    solidLine.geometry.attributes.position.needsUpdate = true;
}

function setSnapLines(vertex, lastVertex, secondLast){
    const material = new THREE.LineBasicMaterial({ color: 0xb8a5a3, opacity: 0.25, transparent: true});

    const cardinal = [
        new THREE.Vector3(1,0,0),
        new THREE.Vector3(-1,0,0),
        new THREE.Vector3(0,1,0),
        new THREE.Vector3(0,-1,0)
    ];

    //get unviable directions
    const last_direction = new THREE.Vector3().subVectors(vertex,lastVertex).normalize().round();
    let second_direction;
    
    if(secondLast!=null){
        second_direction = new THREE.Vector3().subVectors(secondLast,lastVertex).normalize().round();
    }
    
    let a,b;
    // create viable, cardinal snapLines around new vertex
    
    const circle = drawCircle(lastVertex, 0xb8a5a3, false);
    scene.add(circle);

    for(const el of cardinal){
        if(el.equals(last_direction)||(second_direction&&el.equals(second_direction))){
            continue;
        }else if(el.y==0){
            a = new THREE.Vector3(lastVertex.x,lastVertex.y,0);
            b = new THREE.Vector3(el.x*window.innerWidth/2,lastVertex.y,0);
        } else {
            a = new THREE.Vector3(lastVertex.x,lastVertex.y,0);
            b = new THREE.Vector3(lastVertex.x,el.y*window.innerHeight/2,0);
        }
    
        const snapGeometry = new THREE.BufferGeometry().setFromPoints([a,b]);
        const snapLine = new THREE.Line(snapGeometry, material);
        snapLine.visible = false;
        // group.add(circle,snapLine);
        // group.visible = true;
        snapLine.userData = {ass_circle: circle};
          
        scene.add(snapLine);
        if(el.y==0){
            h_snapLine.push([snapLine,circle]);
            //h_snapGroup.push(group)
        } else { 
            v_snapLine.push([snapLine,circle]);
            //v_snapGroup.push(group)
        }
    }
}


function closePolygon(){
    // close polygon
    vertices.push(vertices[0]);
    crvPoints[crvPoints.length-1].add(...vertices[0].toArray());
    updateSolidLine(vertices);
    const curveMaterial = new THREE.LineBasicMaterial({ color: 'green' });
    const curveGeometry = solidGeometry.clone();
    const curve = new THREE.LineSegments(curveGeometry,curveMaterial);
    curves.add(curve); 
    solidGeometry.dispose();
    solidGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(0), 3));
    solidLine.geometry.attributes.position.needsUpdate = true;
    vertices = [];
    while (crossings.children.length > 0) {
        crossings.remove(crossings.children[0]);
    }
    dottedGeometry.setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(0,0,0)]);
    computeButton.disabled = false
}


/*
Description: renders a snapGroup, consisting of a snapLine and a vertex-marking circle, visible
with one exception if the the vertex in question is the first vertex (here polygon-closing logic takes priority) 
*/
function drawPreview(snapGroup, lastVertex){
    previewGroup = [snapGroup,snapGroup.userData.ass_circle];
    const ortho_vertex = previewGroup[1].position;
    if(ortho_vertex.x.toFixed(5)==lastVertex.x.toFixed(5)||ortho_vertex.y.toFixed(5)==lastVertex.y.toFixed(5)){
        return null;
    } else {
        previewGroup[0].visible = true;
        previewGroup[1].visible = true;
        return ortho_vertex;
    }
}

/*
Description: returns a circle object at the position of vertex input
geometry: constant 
material: color set from input 
visibility set from input
*/
function drawCircle(vertex, color, visibility){
    const material = new THREE.MeshBasicMaterial({ color: color });
    const geometry = new THREE.CircleGeometry(.5, 32);
    const circle = new THREE.Mesh(geometry, material);
    circle.position.set(vertex.x, vertex.y, 0);
    circle.visible = visibility; 
    return circle;
} 

function updateDottedGeometry(lastVertex, nextVertex){
    const positionAttribute = dottedGeometry.getAttribute('position');
    dottedLine.visible = true;
    positionAttribute.setXYZ(0, lastVertex.x, lastVertex.y, lastVertex.z); 
    positionAttribute.setXYZ(1, nextVertex.x, nextVertex.y, nextVertex.z); 
    dottedLine.computeLineDistances();
    dottedLine.geometry.attributes.position.needsUpdate = true;
}
   
async function compute() {
    console.log("compute")
    showSpinner(true);
    let nCrv = [];

    for (const points of crvPoints){
        nCrv.push(new rhino.NurbsCurve.create(false, 1, points).encode());
    }

    let crvData = nCrv.map((e) => JSON.stringify(e))

    const data = {
        definition: definitionName,
        inputs: {
          'threeCurve': crvData
        }
      }

    const request = {
        'method':'POST',
        'body': JSON.stringify(data),
        'headers': {'Content-Type': 'application/json'}
      }
    
      try {
        const response = await fetch('/solve', request)
    
        if(!response.ok)
          throw new Error(response.statusText)
    
        const responseJson = await response.json()
        collectResults(responseJson)
    
      } catch(error){
        console.log("error")
        console.error(error)
      }

    // const param1 = new RhinoCompute.Grasshopper.DataTree('threeCurve')
    // param1.append([0], crvData)

    // // clear values
    // let trees = []
    // trees.push(param1)
    // console.log("scriptrees: ",trees)
    // // Call RhinoCompute

    // const res = await RhinoCompute.Grasshopper.evaluateDefinition(definition, trees)

    // console.log(res)

    // collectResults(res)
}

/**
 * Parse response
 */
function collectResults(responseJson) {

    const values = responseJson.values
    console.log("Response: ", responseJson)
    
    // clear doc
    if (doc !== undefined)
        doc.delete()

    
    doc = new rhino.File3dm()

    // for each output (RH_OUT:*)...
    for (let i = 0; i < values.length; i++) {
        // ...iterate through data tree structure...
        for (const path in values[i].InnerTree) {
            const branch = values[i].InnerTree[path]
            // ...and for each branch...
            for (let j = 0; j < branch.length; j++) {
                // ...load rhino geometry into doc
                const rhinoObject = decodeItem(branch[j])
                if (rhinoObject !== null) {
                    doc.objects().add(rhinoObject, null)
                }
            }
        }
    }

    if (doc.objects().count < 1) {
        console.error('No rhino objects to load!')
        showSpinner(false)
        return
    }

    // set up loader for converting the results to threejs
    const loader = new Rhino3dmLoader()
    loader.setLibraryPath('https://cdn.jsdelivr.net/npm/rhino3dm@0.15.0-beta/')

    const resMaterial = new THREE.MeshBasicMaterial({ 
        vertexColors: false, 
        wireframe: false, 
        color: "pink", 
        transparent: true, 
        opacity: .2
    })
    const resLineMaterial = new THREE.LineBasicMaterial({color: "blue"})
    // load rhino doc into three.js scene
    const buffer = new Uint8Array(doc.toByteArray()).buffer
    loader.parse(buffer, function (object) {

        // add material to resulting meshes
        object.traverse(child => {
            console.log("child: ",child.type);
            if(child instanceof THREE.Mesh){
                child.material = resMaterial
            } else {
                child.material = resLineMaterial
            }
        })

        // add object graph from rhino model to three.js scene
        scene.add(object)

        // hide spinner
        showSpinner(false)

    })
}

/**
 * Shows or hides the loading spinner
 */
function showSpinner(enable) {
    if (enable)
        document.getElementById('loader').style.display = 'block'
    else
        document.getElementById('loader').style.display = 'none'
}

/**
* Attempt to decode data tree item to rhino geometry
*/
function decodeItem(item) {
    const data = JSON.parse(item.data)
    console.log('typeof: ',typeof data)
    if (item.type === 'System.String') {
        // hack for draco meshes
        try {
            return rhino.DracoCompression.decompressBase64String(data)
        } catch { } // ignore errors (maybe the string was just a string...)
    } else if (typeof data === 'object') {
        return rhino.CommonObject.decode(data)
    }
    return null
}

function getAuth(key) {
    let value = localStorage[key]
    if (value === undefined) {
        const prompt = key.includes('URL') ? 'Server URL' : 'Server API Key'
        value = window.prompt('RhinoCompute ' + prompt)
        if (value !== null) {
            localStorage.setItem(key, value)
        }
    }
    return value
}

// BOILERPLATE //

var scene, camera, renderer

function init() {
    // Rhino models are z-up, so set this as the default
    THREE.Object3D.DefaultUp = new THREE.Vector3(0, 0, 1)

    scene = new THREE.Scene()
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000)

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(window.devicePixelRatio)
    renderer.setSize(window.innerWidth, window.innerHeight)
    document.body.appendChild(renderer.domElement)

    // const layer_meshes = new rhino.Layer()
    // layer_meshes.name = 'Meshes'
    // layer_meshes.color = { r: 255, g: 255, b: 0, a: 255 }
    // doc.layers().add( layer_meshes )

    camera.position.set(0, 0, 100);
    camera.lookAt(0, 0, 0);
    const light = new THREE.DirectionalLight(0xffffff, 1)
    light.position.set(0,1,0)
    scene.add( light )

    // add some controls to orbit the camera
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableRotate = false; 
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