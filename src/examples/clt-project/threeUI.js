import * as THREE from 'three'
import { scene, camera, renderer, controls } from './initThree.js'
import { stagePartitioning } from './toMiddleware.js'
import { onMouseMove, onMouseDown, onMouseUp, curves } from './drawCurve.js';

export function createListeners() {
    console.log("running");
    // showSpinner(false);
    renderer.domElement.addEventListener('click', onMouseDown);
    renderer.domElement.addEventListener('mousemove', onMouseMove);
    renderer.domElement.addEventListener('mouseup', onMouseUp);
    // renderer.domElement.addEventListener('wheel', zoomToMouse);
    //computeButton.onclick = compute
    computeButton.addEventListener('click', stagePartitioning);
}

export function addFigures(figures) {
    addCarouselHandlers();
    for (var i = 0; i < figures.length; i++) {
        // Create an image element with the base64-encoded image
        const src = "data:image/svg+xml;base64," + figures[i]
        // var img = $("<img>").attr("src", src);
        // Add the image to the carousel
        addFigure(src, "Bipartite Figure " + (i + 1), (i == 0));
    }

    var carousel = $(".carousel");
    var carouselHeight = carousel.outerHeight();
    var carouselWidth = carousel.outerWidth();
    $(".carousel-inner").css({ "height": carouselHeight, "width": carouselWidth });
    $(".carousel").css("display", "block");

    let canvas_container = document.getElementById('canvas-container');
    let carousel_container = document.getElementById('carousel-container');
    canvas_container.classList.remove('col-12');
    canvas_container.classList.add('col-md-8');
    carousel_container.classList.remove('col-0');
    carousel_container.classList.add('col-md-4');
    let canvas = document.getElementById('mainCanvas');
    canvas.height = canvas_container.offsetHeight; 
    canvas.width = canvas_container.offsetWidth;
    zoomToFit(canvas, controls);
}

function addFigure(src, alt, active) {
    // Create an indicator
    var indicator = $("<li></li>").attr("data-target", "#myCarousel").attr("data-slide-to", $(".carousel-indicators li").length);
    if (active) {
        indicator.addClass("active");
    }
    $(".carousel-indicators").append(indicator);

    // Create an SVG slide
    var slide = $("<div></div>").addClass("carousel-item").attr("height", $(".carousel").height()).attr("width", $(".carousel").width());
    if (active) {
        slide.addClass("active");
    }
    var aspectRatio = $(".carousel").width() / $(".carousel").height();
    var svg = $("<svg></svg>")
        .attr("viewBox", "0 0 " + aspectRatio + " 1")
        .attr("preserveaspectratio", "xMidYMid meet")
        .attr("xmlns", "http://www.w3.org/2000/svg")
        .attr("height", $(".carousel").height()).attr("width", $(".carousel").width());
    var img = $("<img>").attr("src", src).attr("height", $(".carousel").height()).attr("width", $(".carousel").width());
    svg.append(img)
    slide.append(svg);

    $(".carousel-inner").append(slide);
}

function addCarouselHandlers() {
    // Handle the click event for the previous arrow
    $(".carousel-control-prev").click(function (event) {
        event.preventDefault();
        var $activeItem = $(".carousel-item.active");
        var $prevItem = $activeItem.prev(".carousel-item");
        if (!$prevItem.length) {
            $prevItem = $(".carousel-item:last");
        }
        $activeItem.removeClass("active");
        $prevItem.addClass("active");

        var $activeIndicator = $(".carousel-indicators li.active");
        var $prevIndicator = $activeIndicator.prev();
        if (!$prevIndicator.length) {
            $prevIndicator = $(".carousel-indicators li:last");
        }
        $activeIndicator.removeClass("active");
        $prevIndicator.addClass("active");
    });

    // Handle the click event for the next arrow
    $(".carousel-control-next").click(function (event) {
        event.preventDefault();
        var $activeItem = $(".carousel-item.active");
        var $nextItem = $activeItem.next(".carousel-item");
        if (!$nextItem.length) {
            $nextItem = $(".carousel-item:first");
        }
        $activeItem.removeClass("active");
        $nextItem.addClass("active");

        var $activeIndicator = $(".carousel-indicators li.active");
        var $nextIndicator = $activeIndicator.next();
        if (!$nextIndicator.length) {
            $nextIndicator = $(".carousel-indicators li:first");
        }
        $activeIndicator.removeClass("active");
        $nextIndicator.addClass("active");
    });
}

function zoomToFit(canvas, controls) {
    const canvasWidth = canvas.width;
    const canvasHeight = canvas.height;
    console.log(canvasWidth, canvasHeight);

    renderer.setSize(canvasWidth, canvasHeight);

    camera.aspect = canvasWidth / canvasHeight;

    camera.updateProjectionMatrix();

    const box = new THREE.Box3().setFromObject(curves);
    const center = box.getCenter(new THREE.Vector3());
    // calculate the distance from the camera to the center of the bounding box
    const boundingBoxSize = box.getSize(new THREE.Vector3());
    const boundingBoxRadius = boundingBoxSize.length() / 2;
    const maxDim = Math.max(boundingBoxSize.x, boundingBoxSize.y, boundingBoxSize.z)
    var distance = maxDim / 2 /  camera.aspect / Math.tan(Math.PI * camera.fov / 360);
    // move the camera to the appropriate distance
    console.log('before: ',camera.position, box);
    camera.position.set(center.x, center.y, center.z + distance);
    console.log('after: ',camera.position);
    camera.lookAt(center);
}

