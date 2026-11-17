import { test } from "node:test";
import assert from "node:assert/strict";
import { loadCpu } from "./cpu_bundle.js";
import {
  Apple2, Controls, GameClock, Trace, keyToAscii,
  KEYBOARD, KBDSTRB, PRESENT, VBLREG, ROM, PADDLE_LEFT, PADDLE_CENTER, PADDLE_RIGHT,
} from "../apple2.js";

const CPU = loadCpu();

// LDA #$42 / STA $C054 / LDA $C000 / STA $C010 / JMP $6000
const PROGRAM = [0xA9, 0x42, 0x8D, 0x54, 0xC0, 0xAD, 0x00, 0xC0, 0x8D, 0x10, 0xC0, 0x4C, 0x00, 0x60];

function machineWith(bytes, addr = 0x6000) {
  const m = new Apple2(CPU);
  m.load(new Uint8Array(bytes), addr, addr);
  return m;
}

test("load installs the binary, ROM stubs and vectors", () => {
  const m = machineWith(PROGRAM);
  assert.equal(m.pc, 0x6000);
  assert.equal(m.state.SP, 0xFF);
  assert.equal(m.ram[0x6000], 0xA9);
  assert.equal(m.ram[ROM.WAIT], 0x60);
  assert.deepEqual(Array.from(m.ram.slice(ROM.PREAD, ROM.PREAD + 3)), [0xA0, PADDLE_CENTER, 0x60]);
  assert.equal(m.ram[0xFFFC] | (m.ram[0xFFFD] << 8), ROM.RTI_STUB);
  assert.equal(m.ram[ROM.RTI_STUB], 0x40);
  assert.ok(m.presentRequested, "first frame is presented without waiting for a strobe");
  assert.throws(() => m.load(new Uint8Array(10), 0xFFFA, 0), RangeError);
});

// LDA $C07E / WAIT: CMP $C07E / BEQ WAIT / STA $C054 / JMP $6000  -- a game frame: wait for VBL, then present
const WAITING_PROGRAM = [0xAD, 0x7E, 0xC0, 0xCD, 0x7E, 0xC0, 0xF0, 0xFB, 0x8D, 0x54, 0xC0, 0x4C, 0x00, 0x60];

test("a program that never waits for VBL is cut off after one extra present", () => {
  const m = machineWith(PROGRAM);
  m.presentRequested = false;
  const r = m.run({ frames: 1 });
  assert.equal(r.stopped, null);
  assert.equal(r.presents, 2);
  assert.equal(r.steps, 7);          // LDA, STA, LDA, STA, JMP, LDA, STA
  assert.equal(m.pc, 0x6005);
  assert.equal(m.state.A, 0x42);
});

test("a frame ends when the game parks polling VBLREG, and catch-up frames tick in between", () => {
  const m = machineWith(WAITING_PROGRAM);
  m.presentRequested = false;
  m.tick(1);
  let r = m.run({ frames: 1 });
  assert.deepEqual(r, { steps: r.steps, presents: 0, frames: 1, stopped: null, pc: r.pc });
  assert.ok(r.pc >= 0x6003 && r.pc <= 0x6007, `parked inside the wait loop, pc=$${r.pc.toString(16)}`);
  assert.ok(r.steps < 10, "returns as soon as the wait loop is recognised, not when the budget runs out");
  assert.ok(m.parked);

  m.tick(1);                                  // next display frame releases the wait
  assert.ok(!m.parked);
  r = m.run({ frames: 1 });
  assert.equal(r.presents, 1);
  assert.equal(r.frames, 1);
  assert.ok(r.steps < 12);
  assert.equal(m.read8(VBLREG), 2);

  m.tick(1);                                  // a slow display: three game frames in one go
  r = m.run({ frames: 3 });
  assert.equal(r.presents, 3);
  assert.equal(r.frames, 3);
  assert.equal(m.read8(VBLREG), 5, "two catch-up ticks happened inside run");
});

test("run halts on uninitialised memory and at a breakpoint", () => {
  const m = machineWith([0xEA]);     // a lone NOP, then nothing was loaded
  m.presentRequested = false;
  assert.deepEqual(m.run({}), { steps: 1, presents: 0, frames: 0, stopped: "halt", pc: 0x6001 });

  const b = machineWith(PROGRAM);
  b.presentRequested = false;
  const r = b.run({ frames: 9, breakpoint: 0x6005 });
  assert.equal(r.stopped, "break");
  assert.equal(r.pc, 0x6005);
  assert.equal(r.steps, 2);
});

test("run gives up after maxSteps even if the clock never advances", () => {
  const m = machineWith([0x4C, 0x00, 0x60]);   // JMP $6000 forever, no present strobe
  m.presentRequested = false;
  const r = m.run({ budgetMs: 1e9, maxSteps: 1000 });
  assert.equal(r.stopped, null);
  assert.equal(r.presents, 0);
  assert.equal(r.steps, 1000);
});

test("keyboard latch and strobe behave like the Apple II soft switches", () => {
  const m = machineWith(PROGRAM);
  assert.equal(m.read8(KEYBOARD), 0x00);
  m.pressKey(0x4A);
  assert.equal(m.read8(KEYBOARD), 0xCA, "bit 7 set while a key waits");
  assert.equal(m.read8(KBDSTRB), 0x4A, "reading the strobe clears bit 7");
  assert.equal(m.read8(KEYBOARD), 0x4A);
  m.pressKey(0x1B);
  m.write8(KBDSTRB, 0);
  assert.equal(m.read8(KEYBOARD), 0x1B, "writing the strobe clears bit 7 too");
});

test("VBLREG counts game ticks and the present strobe sets the flag", () => {
  const m = machineWith(PROGRAM);
  m.presentRequested = false;
  m.tick(3);
  assert.equal(m.read8(VBLREG), 3);
  m.tick(255);
  assert.equal(m.read8(VBLREG), 2, "wraps at 8 bits");
  m.write8(PRESENT, 0);
  assert.ok(m.presentRequested);
  m.setPaddle(PADDLE_RIGHT);
  assert.equal(m.ram[ROM.PREAD + 1], PADDLE_RIGHT);
});

test("keyToAscii maps game keys and ignores browser shortcuts", () => {
  assert.equal(keyToAscii({ key: "j" }), 0x4A);
  assert.equal(keyToAscii({ key: "K" }), 0x4B);
  assert.equal(keyToAscii({ key: "Escape" }), 0x1B);
  assert.equal(keyToAscii({ key: "ArrowLeft" }), 0x08);
  assert.equal(keyToAscii({ key: "r", metaKey: true }), 0, "Cmd+R must reach the browser");
  assert.equal(keyToAscii({ key: "c", ctrlKey: true }), 0);
  assert.equal(keyToAscii({ key: "Shift" }), 0);
  assert.equal(keyToAscii({ key: "F5" }), 0);
});

test("Controls track held keys by physical code and release on blur", () => {
  const m = machineWith(PROGRAM);
  const c = new Controls(m);
  let prevented = 0;
  const ev = (key, code, extra = {}) => ({ key, code, preventDefault: () => prevented++, ...extra });

  c.onKeyDown(ev("J", "KeyJ", { shiftKey: true }));   // pressed with Shift held
  assert.equal(c.paddleValue(), PADDLE_LEFT);
  assert.equal(m.read8(KEYBOARD), 0xCA);
  c.onKeyUp(ev("j", "KeyJ"));                          // released after Shift
  assert.equal(c.paddleValue(), PADDLE_CENTER, "no stuck key");

  c.onKeyDown(ev("ArrowRight", "ArrowRight"));
  assert.equal(c.paddleValue(), PADDLE_RIGHT);
  c.onKeyDown(ev("j", "KeyJ"));
  assert.equal(c.paddleValue(), PADDLE_CENTER, "both directions cancel");
  c.releaseAll();
  assert.equal(c.paddleValue(), PADDLE_CENTER);
  assert.equal(prevented, 3);

  c.onKeyDown(ev("r", "KeyR", { metaKey: true }));
  assert.equal(prevented, 3, "shortcuts are not prevented");

  const inactive = new Controls(m, () => false);
  inactive.onKeyDown(ev("k", "KeyK"));
  assert.equal(inactive.paddleValue(), PADDLE_CENTER);

  c.onKeyDown(ev("k", "KeyK"));
  c.apply();
  assert.equal(m.ram[ROM.PREAD + 1], PADDLE_RIGHT);
});

test("GameClock yields 60 Hz ticks for any display rate", () => {
  const clock = new GameClock();
  assert.equal(clock.ticks(1000), 1, "first frame is one tick");
  assert.equal(clock.ticks(1034), 2, "30 Hz display: two ticks per frame");
  assert.equal(clock.ticks(1039), 0, "fast display: skip a frame");
  assert.equal(clock.ticks(1051), 1, "the remainder carries over");
  clock.reset();
  assert.equal(clock.ticks(5000), 1);
  assert.equal(clock.ticks(9000), 2, "a hidden tab is capped at 50 ms, so at most two ticks catch up");
});

test("Trace keeps the most recent entries in order", () => {
  const t = new Trace(3);
  for (let i = 1; i <= 4; i++) t.record(0x6000 + i, i);
  const lines = t.format(0x6005).split("\n");
  assert.equal(lines.length, 5);
  assert.match(lines[1], /\$6002 +op=\$02/);
  assert.match(lines[3], /\$6004 +op=\$04/);
  assert.match(lines[4], /\$6005/);
});
