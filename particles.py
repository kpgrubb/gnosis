"""Animated particle canvas for the GNOSIS landing page."""

PARTICLE_HTML = """
<canvas id="gnosis-canvas" style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;pointer-events:none"></canvas>
<script>
(function() {
  const canvas = document.getElementById('gnosis-canvas');
  const ctx = canvas.getContext('2d');
  let W, H, particles = [], mouse = {x: -1000, y: -1000};
  const COUNT = 90, CONNECT_DIST = 140, TRAIL_LEN = 8;

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 0.6;
      this.vy = (Math.random() - 0.5) * 0.6;
      this.r = Math.random() * 2 + 1;
      this.trail = [];
      this.hue = 195 + Math.random() * 30;
      this.alpha = 0.6 + Math.random() * 0.4;
    }
    update() {
      this.trail.push({x: this.x, y: this.y, a: this.alpha});
      if (this.trail.length > TRAIL_LEN) this.trail.shift();
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > W) this.vx *= -1;
      if (this.y < 0 || this.y > H) this.vy *= -1;
    }
    draw() {
      // Trail
      for (let i = 0; i < this.trail.length; i++) {
        const t = this.trail[i];
        const fade = (i / this.trail.length) * 0.3;
        ctx.beginPath();
        ctx.arc(t.x, t.y, this.r * 0.6, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${this.hue}, 100%, 65%, ${fade})`;
        ctx.fill();
      }
      // Dot
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${this.hue}, 100%, 70%, ${this.alpha})`;
      ctx.shadowColor = `hsla(${this.hue}, 100%, 60%, 0.8)`;
      ctx.shadowBlur = 12;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  for (let i = 0; i < COUNT; i++) particles.push(new Particle());

  function drawConnections() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CONNECT_DIST) {
          const alpha = (1 - dist / CONNECT_DIST) * 0.15;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0, 180, 255, ${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, W, H);
    drawConnections();
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(animate);
  }
  animate();
})();
</script>
"""
