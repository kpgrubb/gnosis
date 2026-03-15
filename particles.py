"""Animated particle canvas for the GNOSIS landing page.

Rendered via st.components.v1.html() inside an iframe.
Parent CSS repositions the iframe to fill the viewport behind content.
"""

PARTICLE_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  html, body {
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: transparent;
  }
  canvas {
    display: block;
    width: 100vw;
    height: 100vh;
  }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
var canvas = document.getElementById('c');
var ctx = canvas.getContext('2d');
var W, H;
var COUNT = 80, CONNECT = 130, TRAIL = 8;
var particles = [];

function resize() {
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

function Particle() {
  this.x = Math.random() * W;
  this.y = Math.random() * H;
  this.vx = (Math.random() - 0.5) * 0.5;
  this.vy = (Math.random() - 0.5) * 0.5;
  this.r = Math.random() * 2 + 1;
  this.trail = [];
  this.hue = 195 + Math.floor(Math.random() * 30);
  this.alpha = 0.5 + Math.random() * 0.4;
}

Particle.prototype.update = function() {
  this.trail.push({x: this.x, y: this.y});
  if (this.trail.length > TRAIL) this.trail.shift();
  this.x += this.vx;
  this.y += this.vy;
  if (this.x < 0 || this.x > W) this.vx *= -1;
  if (this.y < 0 || this.y > H) this.vy *= -1;
};

Particle.prototype.draw = function() {
  var i, t, fade;
  for (i = 0; i < this.trail.length; i++) {
    t = this.trail[i];
    fade = (i / this.trail.length) * 0.25;
    ctx.beginPath();
    ctx.arc(t.x, t.y, this.r * 0.5, 0, Math.PI * 2);
    ctx.fillStyle = 'hsla(' + this.hue + ', 100%, 65%, ' + fade + ')';
    ctx.fill();
  }
  ctx.beginPath();
  ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
  ctx.fillStyle = 'hsla(' + this.hue + ', 100%, 70%, ' + this.alpha + ')';
  ctx.shadowColor = 'hsla(' + this.hue + ', 100%, 60%, 0.8)';
  ctx.shadowBlur = 12;
  ctx.fill();
  ctx.shadowBlur = 0;
};

for (var i = 0; i < COUNT; i++) particles.push(new Particle());

function connections() {
  var i, j, dx, dy, dist, alpha;
  for (i = 0; i < particles.length; i++) {
    for (j = i + 1; j < particles.length; j++) {
      dx = particles[i].x - particles[j].x;
      dy = particles[i].y - particles[j].y;
      dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < CONNECT) {
        alpha = (1 - dist / CONNECT) * 0.12;
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.strokeStyle = 'rgba(0, 180, 255, ' + alpha + ')';
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }
    }
  }
}

function animate() {
  ctx.clearRect(0, 0, W, H);
  connections();
  for (var i = 0; i < particles.length; i++) {
    particles[i].update();
    particles[i].draw();
  }
  requestAnimationFrame(animate);
}
animate();
</script>
</body>
</html>
"""
