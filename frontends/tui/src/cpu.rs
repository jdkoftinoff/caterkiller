//! 6502 CPU core.
//!
//! All 56 official opcodes and 13 addressing modes, decimal-mode ADC/SBC with
//! NMOS flag behaviour, and the indirect-JMP page-wrap bug. Illegal opcodes
//! stop execution with [`IllegalOpcode`] rather than being skipped. Stores do
//! not read their target, so write-only soft switches are never touched by a
//! phantom read. No cycle counting: the frontend paces the CPU by instruction
//! count and the game syncs itself to a frame counter.

use std::fmt;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Mode {
    Imp, Imm, Zp, Zpx, Zpy, Abs, Abx, Aby, Ind, Izx, Izy, Rel,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[allow(clippy::upper_case_acronyms)]
enum Op {
    ADC, AND, ASL, BCC, BCS, BEQ, BIT, BMI, BNE, BPL, BRK, BVC, BVS,
    CLC, CLD, CLI, CLV, CMP, CPX, CPY, DEC, DEX, DEY, EOR, INC, INX,
    INY, JMP, JSR, LDA, LDX, LDY, LSR, NOP, ORA, PHA, PHP, PLA, PLP,
    ROL, ROR, RTI, RTS, SBC, SEC, SED, SEI, STA, STX, STY, TAX, TAY,
    TSX, TXA, TXS, TYA, ILL,
}

#[derive(Clone, Copy)]
struct Instr(Op, Mode);

macro_rules! i { ($op:ident, $mode:ident) => { Instr(Op::$op, Mode::$mode) }; }
const ILLEGAL: Instr = Instr(Op::ILL, Mode::Imp);

static DECODE: [Instr; 256] = {
    let x = ILLEGAL;
    [
        // 0x00-0x0F
        i!(BRK,Imp), i!(ORA,Izx), x, x, x, i!(ORA,Zp), i!(ASL,Zp), x,
        i!(PHP,Imp), i!(ORA,Imm), i!(ASL,Imp), x, x, i!(ORA,Abs), i!(ASL,Abs), x,
        // 0x10-0x1F
        i!(BPL,Rel), i!(ORA,Izy), x, x, x, i!(ORA,Zpx), i!(ASL,Zpx), x,
        i!(CLC,Imp), i!(ORA,Aby), x, x, x, i!(ORA,Abx), i!(ASL,Abx), x,
        // 0x20-0x2F
        i!(JSR,Abs), i!(AND,Izx), x, x, i!(BIT,Zp), i!(AND,Zp), i!(ROL,Zp), x,
        i!(PLP,Imp), i!(AND,Imm), i!(ROL,Imp), x, i!(BIT,Abs), i!(AND,Abs), i!(ROL,Abs), x,
        // 0x30-0x3F
        i!(BMI,Rel), i!(AND,Izy), x, x, x, i!(AND,Zpx), i!(ROL,Zpx), x,
        i!(SEC,Imp), i!(AND,Aby), x, x, x, i!(AND,Abx), i!(ROL,Abx), x,
        // 0x40-0x4F
        i!(RTI,Imp), i!(EOR,Izx), x, x, x, i!(EOR,Zp), i!(LSR,Zp), x,
        i!(PHA,Imp), i!(EOR,Imm), i!(LSR,Imp), x, i!(JMP,Abs), i!(EOR,Abs), i!(LSR,Abs), x,
        // 0x50-0x5F
        i!(BVC,Rel), i!(EOR,Izy), x, x, x, i!(EOR,Zpx), i!(LSR,Zpx), x,
        i!(CLI,Imp), i!(EOR,Aby), x, x, x, i!(EOR,Abx), i!(LSR,Abx), x,
        // 0x60-0x6F
        i!(RTS,Imp), i!(ADC,Izx), x, x, x, i!(ADC,Zp), i!(ROR,Zp), x,
        i!(PLA,Imp), i!(ADC,Imm), i!(ROR,Imp), x, i!(JMP,Ind), i!(ADC,Abs), i!(ROR,Abs), x,
        // 0x70-0x7F
        i!(BVS,Rel), i!(ADC,Izy), x, x, x, i!(ADC,Zpx), i!(ROR,Zpx), x,
        i!(SEI,Imp), i!(ADC,Aby), x, x, x, i!(ADC,Abx), i!(ROR,Abx), x,
        // 0x80-0x8F
        x, i!(STA,Izx), x, x, i!(STY,Zp), i!(STA,Zp), i!(STX,Zp), x,
        i!(DEY,Imp), x, i!(TXA,Imp), x, i!(STY,Abs), i!(STA,Abs), i!(STX,Abs), x,
        // 0x90-0x9F
        i!(BCC,Rel), i!(STA,Izy), x, x, i!(STY,Zpx), i!(STA,Zpx), i!(STX,Zpy), x,
        i!(TYA,Imp), i!(STA,Aby), i!(TXS,Imp), x, x, i!(STA,Abx), x, x,
        // 0xA0-0xAF
        i!(LDY,Imm), i!(LDA,Izx), i!(LDX,Imm), x, i!(LDY,Zp), i!(LDA,Zp), i!(LDX,Zp), x,
        i!(TAY,Imp), i!(LDA,Imm), i!(TAX,Imp), x, i!(LDY,Abs), i!(LDA,Abs), i!(LDX,Abs), x,
        // 0xB0-0xBF
        i!(BCS,Rel), i!(LDA,Izy), x, x, i!(LDY,Zpx), i!(LDA,Zpx), i!(LDX,Zpy), x,
        i!(CLV,Imp), i!(LDA,Aby), i!(TSX,Imp), x, i!(LDY,Abx), i!(LDA,Abx), i!(LDX,Aby), x,
        // 0xC0-0xCF
        i!(CPY,Imm), i!(CMP,Izx), x, x, i!(CPY,Zp), i!(CMP,Zp), i!(DEC,Zp), x,
        i!(INY,Imp), i!(CMP,Imm), i!(DEX,Imp), x, i!(CPY,Abs), i!(CMP,Abs), i!(DEC,Abs), x,
        // 0xD0-0xDF
        i!(BNE,Rel), i!(CMP,Izy), x, x, x, i!(CMP,Zpx), i!(DEC,Zpx), x,
        i!(CLD,Imp), i!(CMP,Aby), x, x, x, i!(CMP,Abx), i!(DEC,Abx), x,
        // 0xE0-0xEF
        i!(CPX,Imm), i!(SBC,Izx), x, x, i!(CPX,Zp), i!(SBC,Zp), i!(INC,Zp), x,
        i!(INX,Imp), i!(SBC,Imm), i!(NOP,Imp), x, i!(CPX,Abs), i!(SBC,Abs), i!(INC,Abs), x,
        // 0xF0-0xFF
        i!(BEQ,Rel), i!(SBC,Izy), x, x, x, i!(SBC,Zpx), i!(INC,Zpx), x,
        i!(SED,Imp), i!(SBC,Aby), x, x, x, i!(SBC,Abx), i!(INC,Abx), x,
    ]
};

/// Memory and I/O the CPU talks to.
pub trait Bus {
    fn read(&mut self, addr: u16) -> u8;
    fn write(&mut self, addr: u16, val: u8);
}

/// Returned by [`Cpu::step`] when it fetches an opcode the 6502 does not define.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct IllegalOpcode {
    pub opcode: u8,
    /// Address the opcode was fetched from.
    pub pc: u16,
}

impl fmt::Display for IllegalOpcode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "illegal opcode ${:02X} at ${:04X}", self.opcode, self.pc)
    }
}

impl std::error::Error for IllegalOpcode {}

#[derive(Clone, Debug)]
pub struct Cpu {
    pub a: u8,
    pub x: u8,
    pub y: u8,
    pub sp: u8,
    pub pc: u16,
    pub n: bool,
    pub v: bool,
    pub d: bool,
    pub i: bool,
    pub z: bool,
    pub c: bool,
}

impl Default for Cpu {
    fn default() -> Self {
        Self { a: 0, x: 0, y: 0, sp: 0xFF, pc: 0, n: false, v: false, d: false, i: true, z: true, c: false }
    }
}

impl Cpu {
    pub fn new() -> Self {
        Self::default()
    }

    fn get_p(&self) -> u8 {
        (if self.n { 0x80 } else { 0 })
            | (if self.v { 0x40 } else { 0 })
            | 0x20
            | (if self.d { 0x08 } else { 0 })
            | (if self.i { 0x04 } else { 0 })
            | (if self.z { 0x02 } else { 0 })
            | (if self.c { 0x01 } else { 0 })
    }

    fn set_p(&mut self, v: u8) {
        self.n = v & 0x80 != 0;
        self.v = v & 0x40 != 0;
        self.d = v & 0x08 != 0;
        self.i = v & 0x04 != 0;
        self.z = v & 0x02 != 0;
        self.c = v & 0x01 != 0;
    }

    #[inline]
    fn set_nz(&mut self, v: u8) -> u8 {
        self.n = v & 0x80 != 0;
        self.z = v == 0;
        v
    }

    #[inline]
    fn push(&mut self, bus: &mut dyn Bus, v: u8) {
        bus.write(0x0100 | self.sp as u16, v);
        self.sp = self.sp.wrapping_sub(1);
    }

    #[inline]
    fn pull(&mut self, bus: &mut dyn Bus) -> u8 {
        self.sp = self.sp.wrapping_add(1);
        bus.read(0x0100 | self.sp as u16)
    }

    fn push16(&mut self, bus: &mut dyn Bus, v: u16) {
        self.push(bus, (v >> 8) as u8);
        self.push(bus, v as u8);
    }

    fn pull16(&mut self, bus: &mut dyn Bus) -> u16 {
        let lo = self.pull(bus) as u16;
        let hi = self.pull(bus) as u16;
        lo | (hi << 8)
    }

    #[inline]
    fn fetch8(&mut self, bus: &mut dyn Bus) -> u8 {
        let v = bus.read(self.pc);
        self.pc = self.pc.wrapping_add(1);
        v
    }

    #[inline]
    fn fetch16(&mut self, bus: &mut dyn Bus) -> u16 {
        let lo = self.fetch8(bus) as u16;
        let hi = self.fetch8(bus) as u16;
        lo | (hi << 8)
    }

    /// Execute one instruction.
    pub fn step(&mut self, bus: &mut dyn Bus) -> Result<(), IllegalOpcode> {
        let opcode_pc = self.pc;
        let opcode = self.fetch8(bus);
        let Instr(op, mode) = DECODE[opcode as usize];
        if op == Op::ILL {
            self.pc = opcode_pc;
            return Err(IllegalOpcode { opcode, pc: opcode_pc });
        }

        // Effective address. Only instructions that need the operand read it, so a
        // store never performs a phantom read of its target.
        let addr = self.resolve(mode, bus);
        macro_rules! operand {
            () => { if mode == Mode::Imp { self.a } else { bus.read(addr) } };
        }
        macro_rules! store_result {
            ($r:expr) => { if mode == Mode::Imp { self.a = $r; } else { bus.write(addr, $r); } };
        }

        use Op::*;
        match op {
            LDA => { let v = operand!(); self.a = self.set_nz(v); }
            LDX => { let v = operand!(); self.x = self.set_nz(v); }
            LDY => { let v = operand!(); self.y = self.set_nz(v); }
            STA => bus.write(addr, self.a),
            STX => bus.write(addr, self.x),
            STY => bus.write(addr, self.y),
            TAX => { self.x = self.set_nz(self.a); }
            TAY => { self.y = self.set_nz(self.a); }
            TXA => { self.a = self.set_nz(self.x); }
            TYA => { self.a = self.set_nz(self.y); }
            TSX => { self.x = self.set_nz(self.sp); }
            TXS => { self.sp = self.x; }
            ADC => { let v = operand!(); self.adc(v); }
            SBC => { let v = operand!(); self.sbc(v); }
            AND => { let v = operand!(); self.a = self.set_nz(self.a & v); }
            ORA => { let v = operand!(); self.a = self.set_nz(self.a | v); }
            EOR => { let v = operand!(); self.a = self.set_nz(self.a ^ v); }
            CMP => { let v = operand!(); self.compare(self.a, v); }
            CPX => { let v = operand!(); self.compare(self.x, v); }
            CPY => { let v = operand!(); self.compare(self.y, v); }
            BIT => {
                let v = operand!();
                self.z = (self.a & v) == 0;
                self.n = v & 0x80 != 0;
                self.v = v & 0x40 != 0;
            }
            INC => { let v = operand!(); let r = self.set_nz(v.wrapping_add(1)); bus.write(addr, r); }
            DEC => { let v = operand!(); let r = self.set_nz(v.wrapping_sub(1)); bus.write(addr, r); }
            INX => { self.x = self.set_nz(self.x.wrapping_add(1)); }
            DEX => { self.x = self.set_nz(self.x.wrapping_sub(1)); }
            INY => { self.y = self.set_nz(self.y.wrapping_add(1)); }
            DEY => { self.y = self.set_nz(self.y.wrapping_sub(1)); }
            ASL => {
                let v = operand!();
                self.c = v & 0x80 != 0;
                let r = self.set_nz(v << 1);
                store_result!(r);
            }
            LSR => {
                let v = operand!();
                self.c = v & 0x01 != 0;
                let r = self.set_nz(v >> 1);
                store_result!(r);
            }
            ROL => {
                let v = operand!();
                let ci = u8::from(self.c);
                self.c = v & 0x80 != 0;
                let r = self.set_nz((v << 1) | ci);
                store_result!(r);
            }
            ROR => {
                let v = operand!();
                let ci = if self.c { 0x80u8 } else { 0 };
                self.c = v & 0x01 != 0;
                let r = self.set_nz((v >> 1) | ci);
                store_result!(r);
            }
            JMP => { self.pc = addr; }
            JSR => {
                let ret = self.pc.wrapping_sub(1);
                self.push16(bus, ret);
                self.pc = addr;
            }
            RTS => { self.pc = self.pull16(bus).wrapping_add(1); }
            RTI => {
                let p = self.pull(bus);
                self.set_p(p);
                self.pc = self.pull16(bus);
            }
            BRK => {
                let ret = self.pc.wrapping_add(1);
                self.push16(bus, ret);
                let p = self.get_p() | 0x10;
                self.push(bus, p);
                self.i = true;
                let lo = bus.read(0xFFFE) as u16;
                let hi = bus.read(0xFFFF) as u16;
                self.pc = lo | (hi << 8);
            }
            BCC => { if !self.c { self.pc = addr; } }
            BCS => { if self.c { self.pc = addr; } }
            BEQ => { if self.z { self.pc = addr; } }
            BNE => { if !self.z { self.pc = addr; } }
            BMI => { if self.n { self.pc = addr; } }
            BPL => { if !self.n { self.pc = addr; } }
            BVS => { if self.v { self.pc = addr; } }
            BVC => { if !self.v { self.pc = addr; } }
            PHA => { let a = self.a; self.push(bus, a); }
            PHP => { let p = self.get_p() | 0x30; self.push(bus, p); }
            PLA => { let v = self.pull(bus); self.a = self.set_nz(v); }
            PLP => { let v = self.pull(bus); self.set_p(v); }
            CLC => { self.c = false; }
            SEC => { self.c = true; }
            CLD => { self.d = false; }
            SED => { self.d = true; }
            CLI => { self.i = false; }
            SEI => { self.i = true; }
            CLV => { self.v = false; }
            NOP => {}
            ILL => unreachable!("handled above"),
        }
        Ok(())
    }

    /// Compute the effective address for `mode`, consuming operand bytes.
    /// For `Rel` this is the branch target; for `Imp` it is unused.
    fn resolve(&mut self, mode: Mode, bus: &mut dyn Bus) -> u16 {
        match mode {
            Mode::Imp => 0,
            Mode::Imm => {
                let a = self.pc;
                self.pc = self.pc.wrapping_add(1);
                a
            }
            Mode::Zp => self.fetch8(bus) as u16,
            Mode::Zpx => self.fetch8(bus).wrapping_add(self.x) as u16,
            Mode::Zpy => self.fetch8(bus).wrapping_add(self.y) as u16,
            Mode::Abs => self.fetch16(bus),
            Mode::Abx => self.fetch16(bus).wrapping_add(self.x as u16),
            Mode::Aby => self.fetch16(bus).wrapping_add(self.y as u16),
            Mode::Ind => {
                // NMOS bug: the high byte is read from the same page as the low byte
                let ptr = self.fetch16(bus);
                let hi_addr = (ptr & 0xFF00) | (ptr.wrapping_add(1) & 0x00FF);
                (bus.read(ptr) as u16) | ((bus.read(hi_addr) as u16) << 8)
            }
            Mode::Izx => {
                let zp = self.fetch8(bus).wrapping_add(self.x);
                let lo = bus.read(zp as u16) as u16;
                let hi = bus.read(zp.wrapping_add(1) as u16) as u16;
                lo | (hi << 8)
            }
            Mode::Izy => {
                let zp = self.fetch8(bus);
                let lo = bus.read(zp as u16) as u16;
                let hi = bus.read(zp.wrapping_add(1) as u16) as u16;
                (lo | (hi << 8)).wrapping_add(self.y as u16)
            }
            Mode::Rel => {
                let off = self.fetch8(bus) as i8;
                self.pc.wrapping_add(off as u16)
            }
        }
    }

    fn adc(&mut self, val: u8) {
        let a = self.a as u16;
        let v = val as u16;
        let c = u16::from(self.c);
        if self.d {
            // NMOS 6502: Z from the binary result, N and V from the intermediate high nibble
            let mut lo = (a & 0x0F) + (v & 0x0F) + c;
            if lo > 9 { lo += 6; }
            let mut hi = (a >> 4) + (v >> 4) + u16::from(lo > 0x0F);
            let bin = a + v + c;
            self.z = (bin & 0xFF) == 0;
            self.n = (hi & 0x08) != 0;
            self.v = (!(a ^ v) & (a ^ (hi << 4))) & 0x80 != 0;
            if hi > 9 { hi += 6; }
            self.c = hi > 0x0F;
            self.a = (((hi & 0x0F) << 4) | (lo & 0x0F)) as u8;
        } else {
            let result = a + v + c;
            self.c = result > 0xFF;
            self.v = (!(a ^ v) & (a ^ result)) & 0x80 != 0;
            self.a = self.set_nz(result as u8);
        }
    }

    fn sbc(&mut self, val: u8) {
        let a = self.a as i16;
        let v = val as i16;
        let borrow = i16::from(!self.c);
        if self.d {
            let mut lo = (a & 0x0F) - (v & 0x0F) - borrow;
            let mut hi = (a >> 4) - (v >> 4);
            if lo < 0 { lo -= 6; hi -= 1; }
            if hi < 0 { hi -= 6; }
            // NMOS 6502: N, Z, C and V all come from the binary result
            let bin = a - v - borrow;
            self.c = bin >= 0;
            self.v = ((a ^ v) & (a ^ bin)) as u16 & 0x80 != 0;
            self.set_nz(bin as u8);
            self.a = (((hi & 0x0F) << 4) | (lo & 0x0F)) as u8;
        } else {
            let result = a - v - borrow;
            self.c = result >= 0;
            self.v = ((a ^ v) & (a ^ result)) as u16 & 0x80 != 0;
            self.a = self.set_nz(result as u8);
        }
    }

    fn compare(&mut self, reg: u8, val: u8) {
        let diff = (reg as i16) - (val as i16);
        self.c = diff >= 0;
        self.set_nz(diff as u8);
    }
}
