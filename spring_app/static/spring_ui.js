(function () {
  function byId(id) { return document.getElementById(id); }
  function v(id) { return parseFloat(byId(id).value) || 0; }

  function updatePreviewLabel(text) {
    var label = document.querySelector('.preview-label');
    if (label) label.textContent = text;
  }

  window.step = function step(id, delta) {
    var el = byId(id);
    if (!el) return;
    var val = Math.round((parseFloat(el.value || 0) + delta) * 1000) / 1000;
    el.value = val;
    var rng = byId(id + '_range');
    if (rng) rng.value = val;
    drawPreview();
  };

  window.sync = function sync(id, val) {
    var input = byId(id);
    if (!input) return;
    input.value = parseFloat(val).toFixed(1);
    drawPreview();
  };

  ['thickness', 'width'].forEach(function (id) {
    var input = byId(id);
    if (!input) return;
    input.addEventListener('input', function () {
      var rng = byId(id + '_range');
      if (rng) rng.value = input.value;
      drawPreview();
    });
  });

  ['coils', 'pitch', 'inside_dia', 'support_gap'].forEach(function (id) {
    var input = byId(id);
    if (input) input.addEventListener('input', drawPreview);
  });

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = function () { resolve(src); };
      script.onerror = function () { reject(new Error('Failed to load: ' + src)); };
      document.head.appendChild(script);
    });
  }

  async function ensureThreeLoaded() {
    if (window.THREE) return true;
    var sources = [
      '/static/vendor/three.min.js',
      'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
      'https://unpkg.com/three@0.128.0/build/three.min.js',
      'https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js'
    ];

    for (var i = 0; i < sources.length; i++) {
      try {
        await loadScript(sources[i]);
        if (window.THREE) return true;
      } catch (err) {
        // try next source
      }
    }
    return false;
  }

  async function ensureOrbitControlsLoaded() {
    if (!window.THREE || THREE.OrbitControls) return !!(window.THREE && THREE.OrbitControls);

    var sources = [
      '/static/vendor/OrbitControls.js',
      'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js',
      'https://unpkg.com/three@0.128.0/examples/js/controls/OrbitControls.js'
    ];

    for (var i = 0; i < sources.length; i++) {
      try {
        await loadScript(sources[i]);
        if (THREE.OrbitControls) return true;
      } catch (err) {
        // try next source
      }
    }
    return false;
  }

  var renderer;
  var camera;
  var scene;
  var controls;
  var springMesh = null;
  var material;

  function initThree() {
    var viewport = byId('springViewport');
    if (!viewport) return;

    if (!window.THREE) {
      updatePreviewLabel('3D preview unavailable (Three.js failed to load)');
      return;
    }

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setClearColor(0x090d16, 1);
    viewport.appendChild(renderer.domElement);

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x090d16);
    camera = new THREE.PerspectiveCamera(45, 1, 0.1, 2000);
    camera.position.set(45, 35, 45);

    if (THREE.OrbitControls) {
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.target.set(0, 0, 0);
    } else {
      controls = { target: { set: function () {} }, update: function () {} };
      updatePreviewLabel('3D preview active (orbit controls unavailable)');
    }

    scene.add(new THREE.AmbientLight(0xffffff, 0.65));
    var keyLight = new THREE.DirectionalLight(0xffffff, 0.9);
    keyLight.position.set(35, 40, 25);
    scene.add(keyLight);

    material = new THREE.MeshStandardMaterial({ color: 0xc8d8e8, metalness: 0.35, roughness: 0.35 });

    var grid = new THREE.GridHelper(120, 24, 0x1e3050, 0x141e30);
    grid.position.y = -30;
    scene.add(grid);

    onResize();
    animate();
  }

  function buildSpringGeometry(coils, thickness, width, pitch, insideDia) {
    var path = new THREE.Curve();
    var turns = Math.max(1, coils);
    var totalAngle = turns * Math.PI * 2;
    var radius = insideDia / 2 + width / 2;
    var totalHeight = turns * pitch;

    path.getPoint = function (t) {
      var a = totalAngle * t;
      var x = radius * Math.cos(a);
      var z = radius * Math.sin(a);
      var y = -totalHeight / 2 + pitch * turns * t;
      return new THREE.Vector3(x, y, z);
    };

    var tubeRadius = Math.max(0.1, thickness / 2);
    return new THREE.TubeGeometry(path, Math.max(80, Math.round(turns * 90)), tubeRadius, 24, false);
  }

  function drawPreview() {
    if (!scene) return;

    var coils = Math.max(1, v('coils'));
    var thickness = Math.max(0.2, v('thickness'));
    var width = Math.max(0.2, v('width'));
    var pitch = Math.max(0.5, v('pitch'));
    var insideDia = Math.max(1, v('inside_dia'));

    if (springMesh) {
      scene.remove(springMesh);
      springMesh.geometry.dispose();
    }

    springMesh = new THREE.Mesh(buildSpringGeometry(coils, thickness, width, pitch, insideDia), material);
    scene.add(springMesh);

    var totalHeight = coils * pitch;
    var outerRadius = insideDia / 2 + width + thickness;
    var fit = Math.max(totalHeight, outerRadius * 2);
    camera.position.set(fit * 1.2, fit * 0.9, fit * 1.2);
    camera.near = 0.1;
    camera.far = fit * 20;
    camera.updateProjectionMatrix();
    controls.target.set(0, 0, 0);
    controls.update();
  }

  function onResize() {
    if (!renderer || !camera) return;
    var viewport = byId('springViewport');
    var w = Math.max(1, viewport.clientWidth);
    var h = Math.max(1, viewport.clientHeight);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  function animate() {
    requestAnimationFrame(animate);
    if (!renderer || !scene || !camera) return;
    controls.update();
    renderer.render(scene, camera);
  }

  async function bootstrapPreview() {
    var loaded = await ensureThreeLoaded();
    if (!loaded) {
      updatePreviewLabel('3D preview unavailable (Three.js failed to load)');
      return;
    }
    await ensureOrbitControlsLoaded();
    initThree();
    drawPreview();
  }

  window.addEventListener('resize', onResize);

  var _exportFormat = 'stl';

  window.setFmt = function setFmt(btn) {
    _exportFormat = btn.dataset.fmt;
    var group = document.getElementById('fmtGroup');
    if (group) {
      group.querySelectorAll('.fmt-btn').forEach(function (b) {
        b.classList.toggle('active', b === btn);
      });
    }
  };

  window.generate = async function generate() {
    var btn = byId('genBtn');
    var spinner = byId('spinner');
    var statusEl = byId('status');
    var statusText = byId('statusText');

    btn.disabled = true;
    spinner.style.display = 'block';
    statusEl.className = 'status';
    statusText.textContent = 'Generating spring geometry…';

    var params = {
      coils: v('coils'),
      thickness: v('thickness'),
      width: v('width'),
      pitch: v('pitch'),
      inside_dia: v('inside_dia'),
      support_gap: v('support_gap'),
      format: _exportFormat
    };

    try {
      var res = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });

      if (!res.ok) {
        var err = await res.json();
        throw new Error(err.error || ('HTTP ' + res.status));
      }

      var blob = await res.blob();
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      var ext = (params.format === '3mf_bambu' || params.format === '3mf_snapmaker') ? '.3mf' : '.stl';
      var fname = 'spring_c' + params.coils + '_id' + params.inside_dia + '_p' + params.pitch + ext;
      a.href = url;
      a.download = fname;
      a.click();
      URL.revokeObjectURL(url);

      var kb = (blob.size / 1024).toFixed(1);
      statusEl.className = 'status success';
      statusText.textContent = '✓ Downloaded ' + fname + ' (' + kb + ' KB)';
    } catch (e) {
      statusEl.className = 'status error';
      statusText.textContent = '✗ Error: ' + e.message;
    } finally {
      btn.disabled = false;
      spinner.style.display = 'none';
    }
  };

  document.addEventListener('DOMContentLoaded', bootstrapPreview);
})();
