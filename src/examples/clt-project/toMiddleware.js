import { showSpinner } from "./initThree.js";
import { crvPoints } from "./drawCurve.js";
import { addFigures, showPartition, partitionCache, activePartition } from "./threeUI.js";
import * as THREE from 'three';

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
    let areas = []

    // iterate over the curves
    for (let i = 0; i < crvPoints.length; i++) {
        const curve = crvPoints[i];
        const numVertices = curve.length; 
        let signedArea = 0;

        // iterate over the vertices of the curve and compute the signed area using cross products
        for (let j = 0; j < numVertices; j++) {
            const p1 = new THREE.Vector3(curve[j][0], curve[j][1], curve[j][2]);
            const p2 = new THREE.Vector3(curve[(j + 1) % numVertices][0], curve[(j + 1) % numVertices][1], curve[(j + 1) % numVertices][2]);
            signedArea += p1.x * p2.y - p2.x * p1.y;
        }
        
        if(signedArea<0){
            curve.reverse();
            signedArea*=-1;
        }
        areas.push(signedArea)
    }

    let resData
    const response = await fetch('/python/stagePartitioning', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            crvPoints: crvPoints,
            k: 4, 
            areas: areas
        })
    })
        .then(response => response.text())
        .then(data => {
            //DEBUG console.log("getting data: ", data)
            resData = JSON.parse(data)
        })
        .catch(error => console.error(error));

    addFigures(resData.bipartite_figures);
    console.log('staged!');
    await showPartition(0);
}

export async function getPartition(partitionCache, degSetIndex, index) {
    let resData
    const response = await fetch('/python/getPartition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            index: index,
            degSetIndex: degSetIndex
        })
    })
        .then(response => response.text())
        .then(data => {
            //DEBUG 
            resData = JSON.parse(data)
            // console.log('resData: ',resData);
            // console.log('index: ',index);
            partitionCache[degSetIndex][index] = resData
        })
        .catch(error => console.error(error));
}