import * as THREE from 'three'
import { scene, camera, renderer, controls } from './initThree.js'
export let crvPoints = []


let dottedGeometry, dottedLine
let crossings = new THREE.Group()
let previewGroup

let solidGeometry, solidLine

//solidLine variables
let vertices = [];
export let curves = new THREE.Group();

//snapLine variables
let h_snapLine = [];
let v_snapLine = [];

function init(point){
    dottedGeometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(point.x, point.y, 0),
        new THREE.Vector3(point.x, point.y, 0)
    ]);
    
    const dottedMaterial = new THREE.LineDashedMaterial({
        color: 0xbfffbf,
        scale: 1, 
        dashSize: 0.25,
        gapSize: 0.25,
        opacity: 0.75,
        transparent: true
    });
    
    dottedLine = new THREE.Line(dottedGeometry, dottedMaterial);
    dottedLine.computeLineDistances();
    
    solidGeometry = new THREE.BufferGeometry();
    solidGeometry.setAttribute('position', new THREE.Float32BufferAttribute([], 3));
    const solidMaterial = new THREE.LineBasicMaterial({ color: 0xbfffbf });
    solidLine = new THREE.LineSegments(solidGeometry, solidMaterial);

    scene.add(dottedLine);
    scene.add(solidLine);
}

export function onMouseDown(event) {
    let point = getXY(event);
    event.preventDefault();
    if (crossings.children.length > 0) {
        crossings.traverse((child) => {
            if (child instanceof THREE.Sprite) {
                console.log(child.material.color)
                if (child.material.color.equals(new THREE.Color('green'))) {
                    closePolygon();
                } else {
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
            crvPoints.push([]);//new rhino.Point3dList());
            crvPoints[crvPoints.length - 1].push(vertices[0].toArray());
        }
        const endpoint = new THREE.Vector3().fromBufferAttribute(positionAttribute, 1);

        // add solid line to scene
        vertices.push(endpoint);
        crvPoints[crvPoints.length - 1].push(endpoint.toArray())
        updateSolidLine();
    } else {
        // add first vertex
        vertices.push(point);
        init(point);
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

export function onMouseMove(event) {
    event.preventDefault();
    let point = getXY(event);

    if (vertices.length > 0) {
        if (previewGroup) {
            previewGroup[0].visible = false;
            previewGroup[1].visible = false;
            previewGroup = null;
        }

        if (crossings.children.length > 0) {
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

        if (vertices.length > 1) {
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
            // if (snap_intersects && snap_intersects[0] && snap_intersects[0].distance < .025) {
            if(snap_intersects && snap_intersects[0]){
                if(snap_intersects[0].point.clone().project(camera).distanceTo(nextVertex.clone().project(camera)) * window.innerWidth / 2 < 10){
                    console.log("snapped")
                    orthogonal_vertex = drawPreview(snap_intersects[0].object, lastVertex);
                    if (orthogonal_vertex) {
                        order[order.indexOf(point)] = orthogonal_vertex;
                        nextVertex.set(order[0].x, order[1].y, 0);
                    }
                }
            }
        }

        const current_distance = nextVertex.distanceTo(lastVertex);
        const intersect_caster = new THREE.Raycaster(lastVertex, direction.normalize());
        intersect_caster.near = 0.00001;
        intersect_caster.params = { Line: { threshold: 0, useVertices: false } }; // Only check for intersections with lines
        if (vertices.length > 3) {
            intersects = intersect_caster.intersectObjects([solidLine, curves],true);
            if (intersects && intersects.length > 0) {
                for (const intersect of intersects) {
                    if (intersect.distance <= current_distance) {
                        // if (nextVertex.distanceTo(vertices[0]) <= .001) {
                        if(nextVertex.clone().project(camera).distanceTo(vertices[0].clone().project(camera)) * window.innerWidth / 2 < 10){
                            const circle = drawCircle(intersect.point, 'green', true);
                            crossings.add(circle);
                            crossings.visible = true;
                            scene.add(crossings);
                            nextVertex.set(vertices[0].x, vertices[0].y, 0);
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

export function onMouseUp(event) {
    if (crossings.children.length > 0) {
        crossings.traverse((child) => {
            if (child instanceof THREE.Mesh) {
                child.material.color.set(0xbb6a79);
            }
        });
        renderer.render(scene, camera);
        return;
    }
}

export function getXY(evt) {
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
    solidLine.geometry.boundingBox = null;
    solidLine.geometry.boundingSphere = null;
    solidLine.geometry.attributes.position.needsUpdate = true;

    if(vertices.length>1){
        const positions = solidLine.geometry.attributes.position.array;
        const recent = positions.slice(positions.length-6)
        const start = new THREE.Vector3(recent[0], recent[1], recent[2]);
        const end = new THREE.Vector3(recent[3], recent[4], recent[5]);
        const newSegment = new THREE.Line3(start, end);
        newSegment.visible = false;
    }
}

function setSnapLines(vertex, lastVertex, secondLast) {
    const material = new THREE.LineBasicMaterial({ color: 0xb8a5a3, opacity: 0.25, transparent: true });

    const cardinal = [
        new THREE.Vector3(1, 0, 0),
        new THREE.Vector3(-1, 0, 0),
        new THREE.Vector3(0, 1, 0),
        new THREE.Vector3(0, -1, 0)
    ];

    //get unviable directions
    const last_direction = new THREE.Vector3().subVectors(vertex, lastVertex).normalize().round();
    let second_direction;

    if (secondLast != null) {
        second_direction = new THREE.Vector3().subVectors(secondLast, lastVertex).normalize().round();
    }

    let a, b;
    // create viable, cardinal snapLines around new vertex

    const circle = drawCircle(lastVertex, 0xb8a5a3, false);
    scene.add(circle);

    for (const el of cardinal) {
        if (el.equals(last_direction) || (second_direction && el.equals(second_direction))) {
            continue;
        } else if (el.y == 0) {
            a = new THREE.Vector3(lastVertex.x, lastVertex.y, 0);
            b = new THREE.Vector3(el.x * window.innerWidth / 2, lastVertex.y, 0);
        } else {
            a = new THREE.Vector3(lastVertex.x, lastVertex.y, 0);
            b = new THREE.Vector3(lastVertex.x, el.y * window.innerHeight / 2, 0);
        }

        const snapGeometry = new THREE.BufferGeometry().setFromPoints([a, b]);
        const snapLine = new THREE.Line(snapGeometry, material);
        snapLine.visible = false;
        snapLine.userData = { ass_circle: circle };

        scene.add(snapLine);
        if (el.y == 0) {
            h_snapLine.push([snapLine, circle]);
        } else {
            v_snapLine.push([snapLine, circle]);
        }
    }
}


function closePolygon() {
    // close polygon
    console.log('closing')
    vertices.push(vertices[0]);
    crvPoints[crvPoints.length - 1].push(vertices[0].toArray())
    updateSolidLine(vertices);
    const curveMaterial = new THREE.LineBasicMaterial({ color: 'green' });
    const curveGeometry = solidGeometry.clone();
    const curve = new THREE.LineSegments(curveGeometry, curveMaterial);
    curves.add(curve);
    solidGeometry.dispose();
    solidGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(0), 3));
    solidLine.geometry.attributes.position.needsUpdate = true;
    vertices = [];
    while (crossings.children.length > 0) {
        crossings.remove(crossings.children[0]);
    }
    dottedGeometry.setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, 0)]);
    computeButton.disabled = false
}


/*
Description: renders a snapGroup, consisting of a snapLine and a vertex-marking circle, visible
with one exception if the the vertex in question is the first vertex (here polygon-closing logic takes priority) 
*/
function drawPreview(snapGroup, lastVertex) {
    previewGroup = [snapGroup, snapGroup.userData.ass_circle];
    const ortho_vertex = previewGroup[1].position;
    if (ortho_vertex.x.toFixed(5) == lastVertex.x.toFixed(5) || ortho_vertex.y.toFixed(5) == lastVertex.y.toFixed(5)) {
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
function drawCircle(vertex, color, visibility) {
    const geometry = new THREE.CircleGeometry(.05, 32);
    const material = new THREE.SpriteMaterial({ sizeAttenuation: false, color: color });

    // Create the sprite
    const circle = new THREE.Sprite(material);
    const sizeInPixels = .1;
    circle.scale.set(sizeInPixels, sizeInPixels, 1);

    // Set the circle geometry as the sprite's geometry
    circle.geometry = geometry;

    // Add the sprite to the scene
    circle.position.set(vertex.x, vertex.y, 0);
    circle.visible = visibility;
    return(circle)
}

function updateDottedGeometry(lastVertex, nextVertex) {
    const cameraDistance = camera.position.distanceTo(dottedLine.position);
    const dashSize = 0.01 * cameraDistance;
    const gapSize = 0.005 * cameraDistance;

    const positionAttribute = dottedGeometry.getAttribute('position');
    positionAttribute.setXYZ(0, lastVertex.x, lastVertex.y, lastVertex.z);
    positionAttribute.setXYZ(1, nextVertex.x, nextVertex.y, nextVertex.z);

    const updatedMaterial = new THREE.LineDashedMaterial({
        color: 0xbfffbf,
        scale: 1, 
        dashSize: dashSize,
        gapSize: gapSize,
        opacity: 0.75,
        transparent: true
    });
    dottedLine.material = updatedMaterial;
    dottedLine.geometry.attributes.position.needsUpdate = true;
    dottedLine.computeLineDistances();
    dottedLine.visible = true;
}