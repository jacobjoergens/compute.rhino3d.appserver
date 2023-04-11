import { showSpinner } from "./initThree.js";
import { crvPoints } from "./drawCurve.js";
import { addFigures } from "./threeUI.js";

export async function spinUpSocket() {
    const response = await fetch('/python/startServer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
        .then(response => response.text())
        .then(data => {
            console.log(data)
            if (data == 'Connection established!') {
                showSpinner(false);
            }
        })
        .catch(error => console.error(error));
}

export async function stagePartitioning() {
    let resData
    const response = await fetch('/python/stagePartitioning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            crvPoints: crvPoints,
            k: 4
        })
    })
        .then(response => response.text())
        .then(data => {
            //DEBUG console.log("getting data: ", data)
            resData = JSON.parse(data)
        })
        .catch(error => console.error(error));

    addFigures(resData.bipartite_figures);

    //         const regions = resData.regions
    //         for(let j=0; j<regions.length; j++){
    //             let points = regions[j]
    //             const regionMaterial = new THREE.LineBasicMaterial({ color: 'pink' });
    //             // create a new Float32Array with the point data
    //             let vertices = new Float32Array(points.length * 3);
    //             for (var i = 0; i < points.length; i++) {
    //                 vertices[i * 3] = points[i][0];
    //                 vertices[i * 3 + 1] = points[i][1];
    //                 vertices[i * 3 + 2] = points[i][2];
    //             }

    // // create a new BufferGeometry and set the vertices attribute
    //             let regionGeo = new THREE.BufferGeometry();
    //             regionGeo.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    //             const regionLine = new THREE.Line(regionGeo, regionMaterial);
    //             scene.add(regionLine)
    //         }
}



