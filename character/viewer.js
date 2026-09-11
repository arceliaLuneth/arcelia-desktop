import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';

let scene, camera, renderer, clock;
let currentVrm = null;

let isSpeaking = false;
let mouthPhase = 0;

let nextBlinkAt = 0;
let blinkPhase = 0; // 0 = eyes open, ramps 0->1->0 during a blink

// Camera framing: aimed at roughly chest/waist height so head-to-hip is
// visible (not just a chest-up crop), with scroll-wheel zoom on top.
const CAMERA_TARGET = new THREE.Vector3(0, 1.0, 0);
const CAMERA_MIN_DIST = 1.0;
const CAMERA_MAX_DIST = 4.0;
let cameraDistance = 2.2;
let cameraDistanceTarget = 2.2; // scroll sets this; actual distance eases toward it each frame

function init() {
  try {
    const container = document.getElementById('app');

    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera(30, window.innerWidth / window.innerHeight, 0.1, 20);
    updateCameraPosition();

    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0); // fully transparent background
    container.appendChild(renderer.domElement);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(0.5, 1, 1);
    scene.add(keyLight);

    const ambient = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambient);

    clock = new THREE.Clock();
    window.addEventListener('resize', onResize);
    renderer.domElement.addEventListener('wheel', onWheelZoom, { passive: false });

    nextBlinkAt = clock.getElapsedTime() + 2 + Math.random() * 3;

    animate();
    notifyReady();
  } catch (err) {
    console.error('INIT_FAILED:', err.message);
    document.title = 'arcelia-character-init-failed:' + err.message;
  }
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function updateCameraPosition() {
  camera.position.set(CAMERA_TARGET.x, CAMERA_TARGET.y, CAMERA_TARGET.z + cameraDistance);
  camera.lookAt(CAMERA_TARGET);
}

function onWheelZoom(event) {
  event.preventDefault();
  const step = event.deltaY > 0 ? 0.25 : -0.25;
  cameraDistanceTarget = Math.min(CAMERA_MAX_DIST, Math.max(CAMERA_MIN_DIST, cameraDistanceTarget + step));
}

function updateCameraZoom() {
  // Ease current distance toward the target — smooth zoom instead of an
  // instant jump on every scroll tick.
  const diff = cameraDistanceTarget - cameraDistance;
  if (Math.abs(diff) < 0.001) return;
  cameraDistance += diff * 0.15;
  updateCameraPosition();
}

function applyRestPose(vrm) {
  const humanoid = vrm.humanoid;
  if (!humanoid) return;

  // T-pose (arms straight out) is VRM's default bind pose with no
  // animation applied. Rotate upper/lower arms down to a relaxed
  // "idle standing" pose instead. Values are a standard approximation
  // used across VRM viewer projects — fine-tune here if it looks off
  // for a specific model's proportions.
  const setBoneZ = (boneName, angle) => {
    const bone = humanoid.getNormalizedBoneNode(boneName);
    if (bone) bone.rotation.z = angle;
  };

  setBoneZ('leftUpperArm', 1.1);
  setBoneZ('rightUpperArm', -1.1);
  setBoneZ('leftLowerArm', 0.2);
  setBoneZ('rightLowerArm', -0.2);
}

async function loadVRM(url) {
  const loader = new GLTFLoader();
  loader.register((parser) => new VRMLoaderPlugin(parser));

  try {
    const gltf = await loader.loadAsync(url);
    const vrm = gltf.userData.vrm;

    if (!vrm) {
      const msg = 'File berhasil dibaca tapi bukan VRM yang valid (tidak ada data VRM di dalamnya).';
      notifyLoaded(false, msg);
      return { ok: false, error: msg };
    }

    if (currentVrm) {
      scene.remove(currentVrm.scene);
      VRMUtils.deepDispose(currentVrm.scene);
    }

    VRMUtils.removeUnnecessaryVertices(gltf.scene);
    VRMUtils.combineSkeletons(gltf.scene);
    VRMUtils.rotateVRM0(vrm); // VRM0.x faces -Z by default (backward); no-op for VRM1.0
    vrm.scene.traverse((obj) => { obj.frustumCulled = false; });
    applyRestPose(vrm);

    currentVrm = vrm;
    scene.add(vrm.scene);
    notifyLoaded(true, '');
    return { ok: true, error: '' };
  } catch (err) {
    const msg = String(err && err.message ? err.message : err);
    notifyLoaded(false, msg);
    return { ok: false, error: msg };
  }
}

function updateBlink(t) {
  if (!currentVrm || !currentVrm.expressionManager) return;

  if (t >= nextBlinkAt && blinkPhase === 0) {
    blinkPhase = 0.001; // start a blink
  }

  if (blinkPhase > 0) {
    // Quick close-open cycle (~150ms total), simple triangle wave.
    blinkPhase += 0.09;
    const value = blinkPhase <= 1 ? blinkPhase : Math.max(0, 2 - blinkPhase);
    currentVrm.expressionManager.setValue('blink', value);
    if (blinkPhase >= 2) {
      blinkPhase = 0;
      nextBlinkAt = t + 2 + Math.random() * 4;
    }
  }
}

function updateMouth(t) {
  if (!currentVrm || !currentVrm.expressionManager) return;

  if (isSpeaking) {
    // Not real lip-sync (no phoneme data available) — a smooth open/close
    // flap gives a reasonable "talking" impression while TTS audio plays.
    mouthPhase += 0.35;
    const value = 0.15 + 0.5 * Math.abs(Math.sin(mouthPhase));
    currentVrm.expressionManager.setValue('aa', value);
  } else {
    currentVrm.expressionManager.setValue('aa', 0);
    mouthPhase = 0;
  }
}

function updateBreathing(t) {
  if (!currentVrm || !currentVrm.humanoid) return;

  const chest = currentVrm.humanoid.getNormalizedBoneNode('chest');
  const spine = currentVrm.humanoid.getNormalizedBoneNode('spine');
  if (!chest && !spine) return;

  // Slow sine wave, small amplitude — a static VRM model otherwise reads
  // as a frozen photo. This alone is what makes "idle" feel alive.
  const cycle = Math.sin(t * 0.5) * 0.015;
  if (chest) chest.rotation.x = cycle;
  if (spine) spine.rotation.x = cycle * 0.5;
}

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  const t = clock.getElapsedTime();

  updateCameraZoom();

  if (currentVrm) {
    updateBlink(t);
    updateMouth(t);
    updateBreathing(t);
    currentVrm.update(delta);
  }

  renderer.render(scene, camera);
}

// -- Bridge functions, called from Python via page().runJavaScript() --

window.loadVRM = loadVRM;

window.setSpeaking = (speaking) => {
  isSpeaking = !!speaking;
};

window.playExpression = (name, weight = 1.0) => {
  if (!currentVrm || !currentVrm.expressionManager) return;
  currentVrm.expressionManager.setValue(name, weight);
};

function notifyReady() {
  document.title = 'arcelia-character-ready';
  window.__arceliaInitWatchActive = false;
}

function notifyLoaded(ok, error) {
  document.title = 'vrm-load-result:' + JSON.stringify({ ok, error });
}

init();
