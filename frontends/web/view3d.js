// Three.js view of an HGR screen: one small sphere per pixel, instanced, with
// a colour mesh (140x192) and a mono mesh (280x192) that are toggled.
//
// Imports resolve through the page's import map: "three" and "three/addons/".

import * as THREE from "three";
import { OrbitControls } from "three/addons/OrbitControls.js";
import { WIDTH, COLOR_WIDTH, HEIGHT, PALETTE } from "./hgr.js";

// Apple II 140x192 on a 4:3 display: colour pixel aspect 64/35, mono pixels half as wide
const PAR = 64 / 35;
const RADIUS = 0.018;
const SPACING_Y = 0.022;
const SPACING_X = SPACING_Y * PAR;
const SPACING_X_MONO = SPACING_X / 2;
const FOV = 60;

export class HgrView {
  /**
   * @param {object} opts
   * @param {boolean} opts.colorMode  start in colour (true) or mono (false)
   * @param {boolean} opts.fit        keep the camera distance such that the whole screen is visible
   * @param {HTMLElement} opts.container  where the canvas goes
   */
  constructor({ colorMode = true, fit = false, container = document.body } = {}) {
    this.colorMode = colorMode;
    this.fit = fit;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0b0b0b);
    this.camera = new THREE.PerspectiveCamera(FOV, window.innerWidth / window.innerHeight, 0.01, 100);

    this.renderer = new THREE.WebGLRenderer({ antialias: true }); // throws without WebGL
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.12;
    this.controls.target.set(0, 0, 0);

    this.scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const light = new THREE.DirectionalLight(0xffffff, 1.0);
    light.position.set(2, 3, 2);
    this.scene.add(light);

    const geometry = new THREE.SphereGeometry(RADIUS, 6, 4);
    const material = new THREE.MeshStandardMaterial({ roughness: 0.5 });
    this.colorMesh = makeGrid(geometry, material, COLOR_WIDTH, HEIGHT, SPACING_X);
    this.monoMesh = makeGrid(geometry, material, WIDTH, HEIGHT, SPACING_X_MONO);
    this.scene.add(this.colorMesh, this.monoMesh);
    this.setColorMode(colorMode);

    this.displayW = (WIDTH - 1) * SPACING_X_MONO + RADIUS * 2;
    this.displayH = (HEIGHT - 1) * SPACING_Y + RADIUS * 2;
    this.camera.position.set(0, 0, fit ? this.fitDistance() : 4.0);
    this.controls.update();

    window.addEventListener("resize", () => this.resize());
  }

  setColorMode(on) {
    this.colorMode = on;
    this.colorMesh.visible = on;
    this.monoMesh.visible = !on;
  }

  /** Upload decoded pixels: colour indices (140x192) or mono 0/1 values (280x192). */
  upload(colorPix, monoPix) {
    if (this.colorMode) {
      const colors = this.colorMesh.instanceColor.array;
      for (let i = 0, ci = 0; i < colorPix.length; i++, ci += 3) {
        const rgb = PALETTE[colorPix[i]];
        colors[ci] = rgb[0]; colors[ci + 1] = rgb[1]; colors[ci + 2] = rgb[2];
      }
      this.colorMesh.instanceColor.needsUpdate = true;
    } else {
      const colors = this.monoMesh.instanceColor.array;
      for (let i = 0, ci = 0; i < monoPix.length; i++, ci += 3) {
        const v = monoPix[i];
        colors[ci] = v; colors[ci + 1] = v; colors[ci + 2] = v;
      }
      this.monoMesh.instanceColor.needsUpdate = true;
    }
  }

  /** Camera distance at which the whole mono screen fits the viewport with an 8% margin. */
  fitDistance() {
    const halfTan = Math.tan((FOV / 2) * Math.PI / 180);
    const margin = 1.08;
    const zW = (this.displayW * margin * 0.5) / (halfTan * this.camera.aspect);
    const zH = (this.displayH * margin * 0.5) / halfTan;
    return Math.max(zW, zH);
  }

  resize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    if (this.fit) {
      const dir = this.camera.position.clone().sub(this.controls.target).normalize();
      this.camera.position.copy(this.controls.target).addScaledVector(dir, this.fitDistance());
    }
  }

  /** Nudge the camera around the target a little; call once per frame while enabled. */
  autoOrbit(now = performance.now()) {
    const t = now * 0.0003;
    const maxTilt = 10 * Math.PI / 180;
    const dAzimuth = Math.cos(t) * 0.0015;
    const dPolar = Math.cos(t * 0.7) * maxTilt * 0.002;
    const offset = this.camera.position.clone().sub(this.controls.target);
    const r = offset.length();
    let theta = Math.atan2(offset.x, offset.z);
    let phi = Math.asin(Math.max(-1, Math.min(1, offset.y / r)));
    theta += dAzimuth;
    phi = Math.max(-maxTilt, Math.min(maxTilt, phi + dPolar));
    offset.set(r * Math.sin(theta) * Math.cos(phi), r * Math.sin(phi), r * Math.cos(theta) * Math.cos(phi));
    this.camera.position.copy(this.controls.target).add(offset);
    this.camera.lookAt(this.controls.target);
  }

  render() {
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}

function makeGrid(geometry, material, cols, rows, spacingX) {
  const mesh = new THREE.InstancedMesh(geometry, material, cols * rows);
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(cols * rows * 3), 3);
  mesh.instanceColor.setUsage(THREE.DynamicDrawUsage);

  const dummy = new THREE.Object3D();
  const x0 = -(cols - 1) * spacingX * 0.5;
  const y0 = (rows - 1) * SPACING_Y * 0.5;
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      dummy.position.set(x0 + x * spacingX, y0 - y * SPACING_Y, 0);
      dummy.updateMatrix();
      mesh.setMatrixAt(y * cols + x, dummy.matrix);
    }
  }
  mesh.instanceMatrix.needsUpdate = true;
  return mesh;
}
