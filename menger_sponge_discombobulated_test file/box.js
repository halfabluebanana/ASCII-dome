class Box {
  constructor(x, y, z) {
    this.pos = createVector(x, y, z);
    this.rot = createVector(random(TAU), random(TAU), random(TAU));
    this.size = random(20, 60);
    this.rotSpeed = p5.Vector.random3D().mult(0.01);
  }

  update() {
    this.rot.add(this.rotSpeed);
  }

  draw() {
    push();
    translate(this.pos.x, this.pos.y, this.pos.z);
    rotateX(this.rot.x);
    rotateY(this.rot.y);
    rotateZ(this.rot.z);
    noFill();
    stroke(255);
    box(this.size);
    pop();
  }
}
