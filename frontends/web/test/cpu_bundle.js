// Load frontends/shared/cpu6502/6502.bundle.js (an IIFE that defines the global
// CPU6502) inside a vm context and return the CPU6502 object.
import fs from "node:fs";
import vm from "node:vm";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
export const BUNDLE = path.join(here, "..", "..", "shared", "cpu6502", "6502.bundle.js");

export function loadCpu() {
  const ctx = vm.createContext({});
  vm.runInContext(fs.readFileSync(BUNDLE, "utf8") + "\n;this.CPU6502 = CPU6502;", ctx);
  return ctx.CPU6502;
}
