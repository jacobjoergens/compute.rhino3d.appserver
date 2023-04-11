// Import libraries
import { Rhino3dmLoader } from 'three/addons/loaders/3DMLoader.js'
import rhino3dm from 'https://cdn.jsdelivr.net/npm/rhino3dm@0.15.0-beta/rhino3dm.module.js'
import { RhinoCompute } from 'https://cdn.jsdelivr.net/npm/compute-rhino3d@0.13.0-beta/compute.rhino3d.module.js'

import { init, showSpinner } from './initThree.js'
import { spinUpSocket } from './toMiddleware.js'
import { createListeners } from './threeUI.js' 

// reference the definition
const definitionName = 'Digest-Curves.gh'

// globals
let rhino, definition, doc

rhino3dm().then(async m => {
    console.log('Loaded rhino3dm.')
    rhino = m // global
    RhinoCompute.url = "http://localhost:8081/" // RhinoCompute server url. Use http://localhost:8081 if debugging locally.
    RhinoCompute.apiKey = getAuth('RHINO_COMPUTE_KEY')  // RhinoCompute server api key. Leave blank if debugging locally.

    //source a .gh / .ghx file in the same directory
    // let url = definitionName
    // let res = await fetch(url)
    // let buffer = await res.arrayBuffer()
    // definition = new Uint8Array(buffer)

    await init();
    showSpinner(true); //show loading until websocket server is up
    await spinUpSocket(); //spin up websocket server in min-k-partition.py via python.js
    createListeners(); //three.js ui
});

// async function compute() {
//     console.log("compute")
//     showSpinner(true);
//     let nCrv = [];

//     for (const points of crvPoints){
//         nCrv.push(new rhino.NurbsCurve.create(false, 1, points).encode());
//     }

//     let crvData = nCrv.map((e) => JSON.stringify(e))

//     const data = {
//         definition: definitionName,
//         inputs: {
//           'threeCurve': crvData
//         }
//       }

//     const request = {
//         'method':'POST',
//         'body': JSON.stringify(data),
//         'headers': {'Content-Type': 'application/json'}
//       }
    
//       try {
//         const response = await fetch('/solve', request)
    
//         if(!response.ok)
//           throw new Error(response.statusText)
    
//         const responseJson = await response.json()
//         collectResults(responseJson)
    
//       } catch(error){
//         console.log("error")
//         console.error(error)
//       }
// }

// /**
//  * Parse response
//  */
// function collectResults(responseJson) {

//     const values = responseJson.values
//     console.log("Response: ", responseJson)
    
//     // clear doc
//     if (doc !== undefined)
//         doc.delete()

    
//     doc = new rhino.File3dm()

//     // for each output (RH_OUT:*)...
//     for (let i = 0; i < values.length; i++) {
//         // ...iterate through data tree structure...
//         for (const path in values[i].InnerTree) {
//             const branch = values[i].InnerTree[path]
//             // ...and for each branch...
//             for (let j = 0; j < branch.length; j++) {
//                 // ...load rhino geometry into doc
//                 const rhinoObject = decodeItem(branch[j])
//                 if (rhinoObject !== null) {
//                     doc.objects().add(rhinoObject, null)
//                 }
//             }
//         }
//     }

//     if (doc.objects().count < 1) {
//         console.error('No rhino objects to load!')
//         showSpinner(false)
//         return
//     }

//     // set up loader for converting the results to threejs
//     const loader = new Rhino3dmLoader()
//     loader.setLibraryPath('https://cdn.jsdelivr.net/npm/rhino3dm@0.15.0-beta/')

//     const resMaterial = new THREE.MeshBasicMaterial({ 
//         vertexColors: false, 
//         wireframe: false, 
//         color: "pink", 
//         transparent: true, 
//         opacity: .2
//     })
//     const resLineMaterial = new THREE.LineBasicMaterial({color: "blue"})
//     // load rhino doc into three.js scene
//     const buffer = new Uint8Array(doc.toByteArray()).buffer
//     loader.parse(buffer, function (object) {

//         // add material to resulting meshes
//         object.traverse(child => {
//             console.log("child: ",child.type);
//             if(child instanceof THREE.Mesh){
//                 child.material = resMaterial
//             } else {
//                 child.material = resLineMaterial
//             }
//         })

//         // add object graph from rhino model to three.js scene
//         scene.add(object)

//         // hide spinner
//         showSpinner(false)

//     })
// }

// /**
// * Attempt to decode data tree item to rhino geometry
// */
// function decodeItem(item) {
//     const data = JSON.parse(item.data)
//     console.log('typeof: ',typeof data)
//     if (item.type === 'System.String') {
//         // hack for draco meshes
//         try {
//             return rhino.DracoCompression.decompressBase64String(data)
//         } catch { } // ignore errors (maybe the string was just a string...)
//     } else if (typeof data === 'object') {
//         return rhino.CommonObject.decode(data)
//     }
//     return null
// }

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