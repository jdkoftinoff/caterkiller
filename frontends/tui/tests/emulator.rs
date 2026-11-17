//! Tests for the CPU core, Apple II bus and Braille renderer.

use std::path::PathBuf;

use caterkiller_tui::apple2::{Apple2, LOWSCR, VBLREG};
use caterkiller_tui::cpu::{Bus, Cpu};
use caterkiller_tui::renderer::{self, COLS, ROWS};

struct Ram(Vec<u8>);

impl Bus for Ram {
    fn read(&mut self, a: u16) -> u8 { self.0[a as usize] }
    fn write(&mut self, a: u16, v: u8) { self.0[a as usize] = v; }
}

/// Assemble-by-hand helper: load `code` at $0200 and run `n` instructions.
fn run(code: &[u8], n: usize) -> (Cpu, Ram) {
    let mut ram = Ram(vec![0; 65536]);
    ram.0[0x200..0x200 + code.len()].copy_from_slice(code);
    let mut cpu = Cpu::new();
    cpu.pc = 0x200;
    for _ in 0..n {
        cpu.step(&mut ram).unwrap();
    }
    (cpu, ram)
}

fn repo_file(rel: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..").join(rel)
}

#[test]
fn binary_add_sets_flags() {
    // LDA #$50 ; ADC #$50  -> $A0, V set, N set, C clear
    let (cpu, _) = run(&[0xA9, 0x50, 0x69, 0x50], 2);
    assert_eq!(cpu.a, 0xA0);
    assert!(cpu.v && cpu.n && !cpu.c && !cpu.z);
}

#[test]
fn decimal_add_and_subtract() {
    // SED ; CLC ; LDA #$19 ; ADC #$01 -> $20 ; SEC ; SBC #$01 -> $19
    let (cpu, _) = run(&[0xF8, 0x18, 0xA9, 0x19, 0x69, 0x01], 4);
    assert_eq!(cpu.a, 0x20);
    assert!(!cpu.c);
    let (cpu, _) = run(&[0xF8, 0x38, 0xA9, 0x20, 0xE9, 0x01], 4);
    assert_eq!(cpu.a, 0x19);
    assert!(cpu.c);
}

#[test]
fn jsr_rts_round_trip_and_stack() {
    // JSR $0206 ; NOP ; NOP ; NOP ; $0206: RTS
    let (cpu, ram) = run(&[0x20, 0x06, 0x02, 0xEA, 0xEA, 0xEA, 0x60], 2);
    assert_eq!(cpu.pc, 0x0203);
    assert_eq!(cpu.sp, 0xFF);
    assert_eq!(ram.0[0x1FF], 0x02);
    assert_eq!(ram.0[0x1FE], 0x02); // return address - 1 = $0202
}

#[test]
fn indirect_jmp_page_wrap_bug() {
    // JMP ($02FF) reads the high byte from $0200, not $0300
    let mut ram = Ram(vec![0; 65536]);
    ram.0[0x200] = 0x6C; ram.0[0x201] = 0xFF; ram.0[0x202] = 0x02;
    ram.0[0x2FF] = 0x34; ram.0[0x300] = 0x99; ram.0[0x200] = 0x6C; // high byte wraps to $0200 = $6C
    let mut cpu = Cpu::new();
    cpu.pc = 0x200;
    cpu.step(&mut ram).unwrap();
    assert_eq!(cpu.pc, 0x6C34);
}

#[test]
fn illegal_opcode_is_reported_and_pc_not_advanced() {
    let mut ram = Ram(vec![0; 65536]);
    ram.0[0x200] = 0x02;
    let mut cpu = Cpu::new();
    cpu.pc = 0x200;
    let err = cpu.step(&mut ram).unwrap_err();
    assert_eq!((err.opcode, err.pc), (0x02, 0x200));
    assert_eq!(cpu.pc, 0x200);
}

/// A bus that records which addresses were read.
struct Spy { ram: Vec<u8>, reads: Vec<u16> }
impl Bus for Spy {
    fn read(&mut self, a: u16) -> u8 { self.reads.push(a); self.ram[a as usize] }
    fn write(&mut self, a: u16, v: u8) { self.ram[a as usize] = v; }
}

#[test]
fn stores_do_not_read_their_target() {
    let mut bus = Spy { ram: vec![0; 65536], reads: Vec::new() };
    bus.ram[0x200..0x203].copy_from_slice(&[0x8D, 0x54, 0xC0]); // STA $C054
    let mut cpu = Cpu::new();
    cpu.pc = 0x200;
    cpu.step(&mut bus).unwrap();
    assert!(!bus.reads.contains(&0xC054), "store performed a phantom read: {:?}", bus.reads);
}

#[test]
fn apple2_soft_switches() {
    let mut sys = Apple2::new();
    sys.key_press(b'J');
    assert_eq!(sys.read(0xC000), 0xCA);
    sys.read(0xC010);
    assert_eq!(sys.read(0xC000), 0x4A, "strobe cleared");
    sys.write(LOWSCR, 0);
    assert!(sys.present_requested);
    assert_eq!(sys.ram[LOWSCR as usize], 0, "I/O page writes do not land in RAM");
    sys.advance_frame();
    assert_eq!(sys.read(VBLREG), 1);
    assert!(sys.load_binary(&[0; 16], 0xFFF8).is_err());
    assert!(sys.load_binary(&[0; 8], 0xFFF8).is_ok());
}

#[test]
fn renderer_maps_pixels_to_braille_dots() {
    let mut page = vec![0u8; 0x2000];
    // pixel (0,0): bit 0 of byte 0 of row 0  -> dot 1 of cell (0,0)
    page[renderer::hires_offset(0, 0)] |= 0x01;
    // pixel (1,3): row 3, right column of cell 0 -> dot 8
    page[renderer::hires_offset(3, 0)] |= 0x02;
    // pixel (279,191): last cell, row 3 right -> dot 8 of cell (47,139)
    page[renderer::hires_offset(191, 39)] |= 0x40;
    let mut lines = Vec::new();
    renderer::render_hgr_braille(&page, &mut lines);
    assert_eq!(lines.len(), ROWS);
    assert!(lines.iter().all(|l| l.chars().count() == COLS));
    assert_eq!(lines[0].chars().next(), Some('\u{2881}'));
    assert_eq!(lines[47].chars().last(), Some('\u{2880}'));
    assert_eq!(lines[1].chars().next(), Some('\u{2800}'));
}

#[test]
fn hires_offset_matches_apple_ii_layout() {
    assert_eq!(renderer::hires_offset(0, 0), 0x0000);
    assert_eq!(renderer::hires_offset(1, 0), 0x0400);
    assert_eq!(renderer::hires_offset(8, 0), 0x0080);
    assert_eq!(renderer::hires_offset(64, 0), 0x0028);
    assert_eq!(renderer::hires_offset(191, 39), 0x1FF7);
}

#[test]
fn original_level3_runs_and_draws() {
    let image = std::fs::read(repo_file("games/caterkiller/original/level3.bin")).expect("level3.bin");
    let mut sys = Apple2::new();
    sys.load_binary(&image, 0x6000).unwrap();
    let mut cpu = Cpu::new();
    cpu.pc = 0x7200;
    let mut presents = 0;
    for _ in 0..600 {
        sys.advance_frame();
        for _ in 0..25_000 {
            cpu.step(&mut sys).unwrap();
            if sys.present_requested {
                sys.present_requested = false;
                presents += 1;
                break;
            }
        }
    }
    assert!(presents > 0, "the game never presented a frame");
    assert!(sys.ram[0x2000..0x4000].iter().any(|&b| b != 0), "HGR page 1 is blank");
}
