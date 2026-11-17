// Apple II machine model for the web frontend: 64 KB RAM around the CPU6502
// bundle, the soft switches the game touches, ROM entry-point stubs, keyboard
// and paddle input, and a frame clock that keeps the game at 60 Hz whatever
// the display refresh rate is.
//
// The CPU object is passed in rather than read from a global so the module
// also runs under node for the tests.

export const KEYBOARD = 0xC000;   // bit 7 = key waiting, bits 6-0 = ASCII
export const KBDSTRB  = 0xC010;   // read or write clears the key strobe
export const PRESENT  = 0xC054;   // LOWSCR; the game writes it once per frame as a present strobe
export const PB0      = 0xC061;
export const PB1      = 0xC062;
export const VBLREG   = 0xC07E;   // frame counter advanced once per 60 Hz game tick

export const ROM = {
  PREAD:    0xFB1E,  // read paddle 0 into Y; stubbed as LDY #value / RTS
  HOME:     0xFC58,  // clear text screen; stubbed as RTS
  WAIT:     0xFCA8,  // delay; stubbed as RTS (the game syncs on VBLREG instead)
  COUT:     0xFDED,  // print character; stubbed as RTS
  RTI_STUB: 0xFFF0,  // all three vectors point here so BRK/IRQ/NMI unwind cleanly
};

export const PADDLE_LEFT = 0x10, PADDLE_CENTER = 0x80, PADDLE_RIGHT = 0xF0;

export class Apple2 {
  constructor(cpu) {
    this.cpu = cpu;
    this.ram = new Uint8Array(cpu.MEMORY_SIZE);
    this.initialized = new Uint8Array(cpu.MEMORY_SIZE); // bytes the loader wrote; executing elsewhere halts
    this.state = new cpu.State();
    this.frameCount = 0;
    this.kbdLatch = 0;
    this.presentRequested = false;
    this.vblPc = -1;        // PC of the last VBLREG read and how often it repeated:
    this.vblReads = 0;      // the same instruction polling VBLREG means the game is waiting for the next frame
    this.read8 = this.read8.bind(this);
    this.write8 = this.write8.bind(this);
  }

  get pc() { return this.state.PC & 0xFFFF; }

  /** True while the CPU sits in a loop polling VBLREG for the next frame. */
  get parked() { return this.vblReads >= 2; }

  /** Clear the machine, load a binary and point the CPU at startPC. */
  load(bytes, loadAddr, startPC) {
    if (loadAddr < 0 || loadAddr + bytes.length > this.ram.length) {
      throw new RangeError(`binary of ${bytes.length} bytes does not fit at $${hex4(loadAddr)}`);
    }
    this.ram.fill(0);
    this.initialized.fill(0);
    this.state = new this.cpu.State();
    this.state.SP = 0xFF;
    this.state.PC = startPC & 0xFFFF;
    this.frameCount = 0;
    this.kbdLatch = 0;
    this.presentRequested = true; // draw the screen once before the first strobe
    this.ram.set(bytes, loadAddr);
    this.initialized.fill(1, loadAddr, loadAddr + bytes.length);
    this.installRomStubs();
  }

  poke(addr, ...bytes) {
    for (let i = 0; i < bytes.length; i++) {
      this.ram[(addr + i) & 0xFFFF] = bytes[i] & 0xFF;
      this.initialized[(addr + i) & 0xFFFF] = 1;
    }
  }

  installRomStubs() {
    this.poke(ROM.RTI_STUB, 0x40);                                            // RTI
    for (const vec of [0xFFFA, 0xFFFC, 0xFFFE]) this.poke(vec, ROM.RTI_STUB & 0xFF, ROM.RTI_STUB >> 8);
    this.poke(ROM.WAIT, 0x60);                                                // RTS
    this.poke(ROM.HOME, 0x60);                                                // RTS
    this.poke(ROM.COUT, 0x60);                                                // RTS
    this.poke(ROM.PREAD, 0xA0, PADDLE_CENTER, 0x60);                          // LDY #$80 / RTS
  }

  /** Paddle 0 value returned by the PREAD stub. */
  setPaddle(value) { this.ram[ROM.PREAD + 1] = value & 0xFF; }

  pressKey(ascii) { this.kbdLatch = 0x80 | (ascii & 0x7F); }

  /** Advance the VBL frame counter by n 60 Hz ticks, releasing a parked wait loop. */
  tick(n = 1) {
    this.frameCount = (this.frameCount + n) & 0xFF;
    this.vblPc = -1;
    this.vblReads = 0;
  }

  read8(addr) {
    addr &= 0xFFFF;
    if (addr === KEYBOARD) return this.kbdLatch;
    if (addr === KBDSTRB) { this.kbdLatch &= 0x7F; return this.kbdLatch; }
    if (addr === PB0 || addr === PB1) return 0x00;      // buttons not pressed
    if (addr === VBLREG) {
      const pc = this.state.PC;
      if (pc === this.vblPc) this.vblReads++; else { this.vblPc = pc; this.vblReads = 0; }
      return this.frameCount;
    }
    return this.ram[addr];
  }

  write8(addr, val) {
    addr &= 0xFFFF;
    this.ram[addr] = val & 0xFF;
    if (addr === KBDSTRB) this.kbdLatch &= 0x7F;
    if (addr === PRESENT) this.presentRequested = true;
  }

  step() { this.state = this.cpu.step(this.state, this.read8, this.write8); }

  /**
   * Simulate `frames` 60 Hz frames. Call tick() first to start the frame.
   *
   * A frame ends when the game parks in its wait-for-VBL loop (the same
   * instruction polling VBLREG); between frames the counter is ticked so the
   * game continues. A program that never waits is cut off after one present
   * strobe more than `frames`. The run also stops when `budgetMs` is spent or
   * after `maxSteps` instructions (a game frame is well under a million), at
   * `breakpoint`, or when the PC reaches memory nothing loaded.
   *
   * Returns { steps, presents, frames, stopped: null | "break" | "halt", pc }.
   */
  run({ budgetMs = 12, frames = 1, maxSteps = 2_000_000, breakpoint = -1, trace = null } = {}) {
    const BATCH = 200; // steps between clock checks
    const tStart = performance.now();
    let steps = 0, presents = 0, done = 0;
    const result = stopped => ({ steps, presents, frames: done, stopped, pc: this.pc });
    while (steps < maxSteps && performance.now() - tStart < budgetMs) {
      for (let i = 0; i < BATCH; i++) {
        const pc = this.pc;
        if (pc === breakpoint) return result("break");
        if (!this.initialized[pc]) return result("halt");
        if (trace) trace.record(pc, this.ram[pc]);
        this.step();
        steps++;
        if (this.presentRequested) {
          this.presentRequested = false;
          if (++presents > frames) return result(null);   // no wait loop: presents are the frames
        }
        if (this.parked) {
          if (++done >= frames) return result(null);
          this.tick(1);                                    // catch-up frame: release the wait and go on
        }
      }
    }
    return result(null);
  }

  registers() {
    const s = this.state;
    return `A=$${hex2(s.A)} X=$${hex2(s.X)} Y=$${hex2(s.Y)} SP=$${hex2(s.SP)} PC=$${hex4(s.PC)}`;
  }
}

/** Ring buffer of the last few (PC, opcode) pairs, for the developer page. */
export class Trace {
  constructor(size = 16) {
    this.pc = new Uint16Array(size);
    this.op = new Uint8Array(size);
    this.idx = 0;
    this.count = 0;
  }
  record(pc, op) {
    this.pc[this.idx] = pc;
    this.op[this.idx] = op;
    this.idx = (this.idx + 1) % this.pc.length;
    if (this.count < this.pc.length) this.count++;
  }
  format(currentPc) {
    const lines = ["--- trace (oldest to newest) ---"];
    for (let k = this.count; k >= 1; k--) {
      const i = (this.idx - k + this.pc.length) % this.pc.length;
      lines.push(`  $${hex4(this.pc[i])}  op=$${hex2(this.op[i])}`);
    }
    lines.push(`-> $${hex4(currentPc)}`);
    return lines.join("\n");
  }
}

/**
 * Converts display frames into 60 Hz game ticks. A 30 Hz display gets two ticks
 * per frame, a 120 Hz display gets one tick every other frame.
 */
export class GameClock {
  constructor(hz = 60) {
    this.frameMs = 1000 / hz;
    this.reset();
  }
  reset() { this.last = 0; this.accum = 0; }
  ticks(timestamp) {
    const dt = this.last ? Math.min(timestamp - this.last, 50) : this.frameMs; // cap: tab was hidden
    this.last = timestamp;
    this.accum += dt;
    let n = 0;
    while (this.accum >= this.frameMs) { this.accum -= this.frameMs; n++; }
    return n;
  }
}

/** Apple II ASCII for a KeyboardEvent, or 0 for keys the game cannot use (including browser shortcuts). */
export function keyToAscii(e) {
  if (e.metaKey || e.ctrlKey || e.altKey) return 0;
  if (e.key.length === 1) {
    let ascii = e.key.charCodeAt(0);
    if (ascii >= 0x61 && ascii <= 0x7A) ascii -= 0x20; // the Apple II keyboard is upper case
    return ascii < 0x80 ? ascii : 0;
  }
  switch (e.key) {
    case "Enter":      return 0x0D;
    case "Backspace":  return 0x08;
    case "Escape":     return 0x1B;
    case "ArrowLeft":  return 0x08;
    case "ArrowRight": return 0x15;
    case "ArrowUp":    return 0x0B;
    case "ArrowDown":  return 0x0A;
    default:           return 0;
  }
}

const LEFT_CODES  = new Set(["KeyJ", "ArrowLeft"]);
const RIGHT_CODES = new Set(["KeyK", "ArrowRight"]);

/**
 * Keyboard and touch input. Held keys are tracked by physical key code so a
 * Shift pressed or released mid-hold cannot leave a key stuck, and everything
 * is released when the window loses focus.
 */
export class Controls {
  constructor(machine, isActive = () => true) {
    this.machine = machine;
    this.isActive = isActive;
    this.held = new Set();
    this.onKeyDown = this.onKeyDown.bind(this);
    this.onKeyUp = this.onKeyUp.bind(this);
    this.releaseAll = this.releaseAll.bind(this);
  }

  attach(target = window) {
    target.addEventListener("keydown", this.onKeyDown);
    target.addEventListener("keyup", this.onKeyUp);
    target.addEventListener("blur", this.releaseAll);
    return this;
  }

  onKeyDown(e) {
    if (!this.isActive()) return;
    const ascii = keyToAscii(e);
    if (!ascii) return;                 // leave browser shortcuts alone
    e.preventDefault();
    this.held.add(e.code);
    this.machine.pressKey(ascii);
  }

  onKeyUp(e) { this.held.delete(e.code); }

  releaseAll() { this.held.clear(); }

  /** Bind a touch/pointer button to a key code for as long as it is pressed. */
  bindButton(element, code) {
    const press = e => { e.preventDefault(); this.held.add(code); };
    const release = () => this.held.delete(code);
    element.addEventListener("pointerdown", press);
    element.addEventListener("pointerup", release);
    element.addEventListener("pointercancel", release);
    element.addEventListener("pointerleave", release);
    element.addEventListener("contextmenu", e => e.preventDefault());
  }

  paddleValue() {
    const left  = [...this.held].some(c => LEFT_CODES.has(c));
    const right = [...this.held].some(c => RIGHT_CODES.has(c));
    if (left && !right) return PADDLE_LEFT;
    if (right && !left) return PADDLE_RIGHT;
    return PADDLE_CENTER;
  }

  /** Push the current paddle position into the machine; call once per frame. */
  apply() { this.machine.setPaddle(this.paddleValue()); }
}

export const hex2 = v => (v & 0xFF).toString(16).toUpperCase().padStart(2, "0");
export const hex4 = v => (v & 0xFFFF).toString(16).toUpperCase().padStart(4, "0");
