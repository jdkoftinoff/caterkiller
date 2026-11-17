//! Apple II system: 64 KB of RAM, the soft switches the game uses, and stubs
//! for the few Monitor ROM routines it calls.

use std::fmt;

use crate::cpu::Bus;

pub const KEYBOARD: u16 = 0xC000;
pub const KBDSTRB: u16 = 0xC010;
pub const LOWSCR: u16 = 0xC054;
pub const PB0: u16 = 0xC061;
pub const PB1: u16 = 0xC062;
/// Frame counter the frontends expose to the game (not real Apple II hardware).
pub const VBLREG: u16 = 0xC07E;

const PADDLE_CENTER: u8 = 0x80;

/// A binary image would not fit below the top of memory.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ImageTooLarge {
    pub load_addr: u16,
    pub len: usize,
}

impl fmt::Display for ImageTooLarge {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} bytes loaded at ${:04X} would run past $FFFF", self.len, self.load_addr)
    }
}

impl std::error::Error for ImageTooLarge {}

pub struct Apple2 {
    pub ram: Box<[u8; 65536]>,
    /// Last key pressed, with bit 7 set until the strobe is cleared.
    pub kbd_latch: u8,
    /// Value returned from $C07E; the frontend advances it once per frame.
    pub frame_count: u8,
    /// Set when the game writes $C054; the frontend clears it after drawing.
    pub present_requested: bool,
    pub paddle_value: u8,
}

impl Default for Apple2 {
    fn default() -> Self {
        let mut sys = Self {
            ram: Box::new([0u8; 65536]),
            kbd_latch: 0,
            frame_count: 0,
            present_requested: false,
            paddle_value: PADDLE_CENTER,
        };
        sys.install_rom_stubs();
        sys
    }
}

impl Bus for Apple2 {
    fn read(&mut self, addr: u16) -> u8 {
        match addr {
            KEYBOARD => self.kbd_latch,
            KBDSTRB => {
                self.kbd_latch &= 0x7F;
                self.kbd_latch
            }
            PB0 | PB1 => 0x00,
            VBLREG => self.frame_count,
            _ => self.ram[addr as usize],
        }
    }

    fn write(&mut self, addr: u16, val: u8) {
        match addr {
            KBDSTRB => self.kbd_latch &= 0x7F,
            LOWSCR => self.present_requested = true,
            0xC000..=0xC0FF => {}
            _ => self.ram[addr as usize] = val,
        }
    }
}

impl Apple2 {
    /// A machine with zeroed RAM and the ROM stubs installed.
    pub fn new() -> Self {
        Self::default()
    }

    /// Latch an ASCII key for the game to read at $C000.
    pub fn key_press(&mut self, ascii: u8) {
        self.kbd_latch = 0x80 | (ascii & 0x7F);
    }

    /// Advance the frame counter the game polls at $C07E.
    pub fn advance_frame(&mut self) {
        self.frame_count = self.frame_count.wrapping_add(1);
    }

    /// Copy a binary image into RAM.
    pub fn load_binary(&mut self, data: &[u8], load_addr: u16) -> Result<(), ImageTooLarge> {
        let start = load_addr as usize;
        let end = start + data.len();
        if end > self.ram.len() {
            return Err(ImageTooLarge { load_addr, len: data.len() });
        }
        self.ram[start..end].copy_from_slice(data);
        Ok(())
    }

    /// Minimal stand-ins for the Monitor ROM routines the game calls, plus
    /// an RTI at the interrupt vectors. Call again after loading an image
    /// that overlaps them.
    pub fn install_rom_stubs(&mut self) {
        // Vectors -> $FFF0: RTI
        self.ram[0xFFF0] = 0x40;
        for vec in [0xFFFAu16, 0xFFFC, 0xFFFE] {
            self.ram[vec as usize] = 0xF0;
            self.ram[vec as usize + 1] = 0xFF;
        }
        self.ram[0xFCA8] = 0x60; // WAIT  -> RTS
        self.ram[0xFC58] = 0x60; // HOME  -> RTS
        self.ram[0xFDED] = 0x60; // COUT  -> RTS
        // PREAD -> LDY #paddle; RTS. update_paddle() rewrites the operand.
        self.ram[0xFB1E] = 0xA0;
        self.ram[0xFB1F] = self.paddle_value;
        self.ram[0xFB20] = 0x60;
    }

    /// Set the paddle 0 reading returned by the PREAD stub (0 = left, $FF = right).
    pub fn update_paddle(&mut self, value: u8) {
        self.paddle_value = value;
        self.ram[0xFB1F] = value;
    }

    pub fn center_paddle(&mut self) {
        self.update_paddle(PADDLE_CENTER);
    }

    pub fn paddle_is_centered(&self) -> bool {
        self.paddle_value == PADDLE_CENTER
    }
}
