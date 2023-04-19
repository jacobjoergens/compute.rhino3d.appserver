import { showSpinner } from "./initThree.js";
import { crvPoints } from "./drawCurve.js";
import { addFigures, showPartition, partitionCache, activePartition } from "./threeUI.js";

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
    console.log('staged!');
    await showPartition(0);
}

export async function getPartition(partitionCache, degSetIndex, index){
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