import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.126.0/build/three.module.js'
import { scene, camera, renderer } from "./init.js";
import { vertices, solidLine, h_snapLine, v_snapLine, curves } from "./mouse-down.js";


//initialize and export basic three variables
const rect = renderer.domElement.getBoundingClientRect();
let mouse = new THREE.Vector2();
const plane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
let raycaster = new THREE.Raycaster();
export let point = new THREE.Vector3();

//dottedLine variables 
export let dottedLine;
export const dottedGeometry = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(0,0,0)]);
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

//intersection variables
export let crossings = new THREE.Group();

// preview variables
let previewGroup = null;

/*
Description: renders a snapGroup, consisting of a snapLine and a vertex-marking circle, visible
with one exception if the the vertex in question is the first vertex (here polygon-closing logic takes priority) 
*/
function drawPreview(snapGroup, lastVertex){
    previewGroup = snapGroup;
    const ortho_vertex = previewGroup.children[0].position;

    if(ortho_vertex.x.toFixed(5)==lastVertex.x.toFixed(5)||ortho_vertex.y.toFixed(5)==lastVertex.y.toFixed(5)){
        return null;
    } else {
        previewGroup.visible = true;
        return ortho_vertex;
    }
}

/*
Description: returns a circle object at the position of vertex input
geometry: constant 
material: color set from input 
visibility set from input
*/
export function drawCircle(vertex, color, visibility){
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

export function onMouseMove(event){
    event.preventDefault();
    mouse.x = ((event.clientX - rect.left) / (rect.right - rect.left)) * 2 - 1;
    mouse.y = - ((event.clientY - rect.top) / (rect.bottom - rect.top)) * 2 + 1;

    // calculate intersection point with plane
    raycaster.setFromCamera(mouse, camera);
    raycaster.ray.intersectPlane(plane, point);

    if (vertices.length > 0) {
        if (previewGroup) {
            previewGroup.visible = false;
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
        let nextVertex;
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

        nextVertex = new THREE.Vector3(order[0].x, order[1].y, 0);
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
            snap_intersects = orthocaster.intersectObjects(snapSet[0]);
            if (snap_intersects && snap_intersects[0] && snap_intersects[0].distance<0.5) {
                orthogonal_vertex = drawPreview(snap_intersects[0].object.parent, lastVertex);
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
};