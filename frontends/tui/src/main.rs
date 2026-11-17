//! Terminal frontend: runs an Apple II binary and draws the HGR screen as
//! Braille, 60 frames per second, only redrawing lines that changed.

use std::error::Error;
use std::io::{self, Write};
use std::panic;
use std::path::Path;
use std::process::ExitCode;
use std::time::{Duration, Instant};

use crossterm::{
    cursor,
    event::{self, Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers},
    execute, queue,
    style::{Attribute, Print, SetAttribute},
    terminal::{self, Clear, ClearType},
};

use caterkiller_tui::apple2::Apple2;
use caterkiller_tui::cpu::Cpu;
use caterkiller_tui::renderer::{self, COLS, ROWS};

const USAGE: &str = "\
Usage: caterkiller-tui <binary.bin> [--load ADDR] [--start ADDR]

  --load ADDR    address the binary is loaded at (default $4000)
  --start ADDR   address execution starts at (default: the load address)

Addresses are hex, with or without a $ or 0x prefix.
Keys: J/K or arrows move, Esc Esc pauses, Ctrl-C quits.";

const FRAME: Duration = Duration::from_micros(1_000_000 / 60);
/// Upper bound on instructions per frame if the game never presents a frame.
const STEPS_PER_FRAME: u32 = 25_000;
const DOUBLE_ESC: Duration = Duration::from_millis(350);
const PADDLE_LEFT: u8 = 0x10;
const PADDLE_RIGHT: u8 = 0xF0;

struct Options {
    binary: String,
    load_addr: u16,
    start_pc: u16,
}

fn parse_hex(s: &str) -> Result<u16, String> {
    let digits = s.trim().trim_start_matches("0x").trim_start_matches("0X").trim_start_matches('$');
    u16::from_str_radix(digits, 16).map_err(|_| format!("'{s}' is not a 16-bit hex address"))
}

fn parse_args(args: &[String]) -> Result<Options, String> {
    let mut binary = None;
    let mut load_addr = 0x4000;
    let mut start_pc = None;
    let mut it = args.iter().skip(1);
    while let Some(arg) = it.next() {
        let mut value_for = |flag: &str| -> Result<u16, String> {
            match arg.strip_prefix(&format!("{flag}=")) {
                Some(v) => parse_hex(v),
                None => it.next().ok_or_else(|| format!("{flag} needs an address")).and_then(|v| parse_hex(v)),
            }
        };
        if arg == "--help" || arg == "-h" {
            return Err(String::new());
        } else if arg.starts_with("--load") {
            load_addr = value_for("--load")?;
        } else if arg.starts_with("--start") {
            start_pc = Some(value_for("--start")?);
        } else if arg.starts_with('-') {
            return Err(format!("unknown option {arg}"));
        } else if binary.is_none() {
            binary = Some(arg.clone());
        } else {
            return Err(format!("unexpected argument {arg}"));
        }
    }
    let binary = binary.ok_or_else(|| "no binary given".to_string())?;
    Ok(Options { binary, load_addr, start_pc: start_pc.unwrap_or(load_addr) })
}

/// Puts the terminal into raw mode on the alternate screen and restores it on
/// drop, including during a panic.
struct Terminal;

impl Terminal {
    fn enter() -> io::Result<Self> {
        terminal::enable_raw_mode()?;
        execute!(io::stdout(), terminal::EnterAlternateScreen, cursor::Hide)?;
        Ok(Terminal)
    }

    fn restore() {
        let _ = execute!(io::stdout(), cursor::Show, terminal::LeaveAlternateScreen);
        let _ = terminal::disable_raw_mode();
    }
}

impl Drop for Terminal {
    fn drop(&mut self) {
        Terminal::restore();
    }
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().collect();
    let opts = match parse_args(&args) {
        Ok(o) => o,
        Err(msg) if msg.is_empty() => {
            println!("{USAGE}");
            return ExitCode::SUCCESS;
        }
        Err(msg) => {
            eprintln!("error: {msg}\n\n{USAGE}");
            return ExitCode::from(2);
        }
    };

    match run(&opts) {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("error: {e}");
            ExitCode::FAILURE
        }
    }
}

fn run(opts: &Options) -> Result<(), Box<dyn Error>> {
    let image = std::fs::read(&opts.binary).map_err(|e| format!("cannot read {}: {e}", opts.binary))?;
    let mut sys = Apple2::new();
    sys.load_binary(&image, opts.load_addr)?;
    sys.install_rom_stubs();
    let mut cpu = Cpu::new();
    cpu.pc = opts.start_pc;

    // If anything panics while the terminal is in raw mode, put it back before
    // the default hook prints the message.
    let default_hook = panic::take_hook();
    panic::set_hook(Box::new(move |info| {
        Terminal::restore();
        default_hook(info);
    }));

    let _terminal = Terminal::enter()?;
    let name = Path::new(&opts.binary).file_name().map(|s| s.to_string_lossy().into_owned()).unwrap_or_default();
    let outcome = Frontend::new(name, opts.load_addr).run(&mut cpu, &mut sys);
    drop(_terminal);
    let _ = panic::take_hook();
    outcome
}

struct Frontend {
    name: String,
    load_addr: u16,
    cols: u16,
    rows: u16,
    lines: Vec<String>,
    shown: Vec<String>,
    shown_status: String,
    force_redraw: bool,
    paused: bool,
    last_esc: Option<Instant>,
}

enum Input {
    Quit,
    Continue,
}

impl Frontend {
    fn new(name: String, load_addr: u16) -> Self {
        Self {
            name,
            load_addr,
            cols: 0,
            rows: 0,
            lines: Vec::new(),
            shown: Vec::new(),
            shown_status: String::new(),
            force_redraw: true,
            paused: false,
            last_esc: None,
        }
    }

    fn run(&mut self, cpu: &mut Cpu, sys: &mut Apple2) -> Result<(), Box<dyn Error>> {
        let (cols, rows) = terminal::size()?;
        self.resize(cols, rows);
        let mut out = io::BufWriter::new(io::stdout());

        loop {
            let frame_start = Instant::now();

            if let Input::Quit = self.poll_input(sys)? {
                return Ok(());
            }

            if self.paused {
                self.draw_status(&mut out, " PAUSED   Esc Esc resumes, Ctrl-C quits ")?;
                out.flush()?;
                std::thread::sleep(Duration::from_millis(50));
                continue;
            }

            // One emulated frame: advance the VBL counter the game syncs to, then run
            // until the game presents a frame or the instruction budget runs out.
            sys.advance_frame();
            for _ in 0..STEPS_PER_FRAME {
                cpu.step(sys)?;
                if sys.present_requested {
                    sys.present_requested = false;
                    break;
                }
            }
            // Keys have no release events, so a paddle deflection lasts one frame.
            if !sys.paddle_is_centered() {
                sys.center_paddle();
            }

            self.draw(&mut out, cpu, sys)?;
            out.flush()?;

            let elapsed = frame_start.elapsed();
            if elapsed < FRAME {
                std::thread::sleep(FRAME - elapsed);
            }
        }
    }

    fn resize(&mut self, cols: u16, rows: u16) {
        self.cols = cols;
        self.rows = rows;
        self.force_redraw = true;
    }

    fn poll_input(&mut self, sys: &mut Apple2) -> io::Result<Input> {
        while event::poll(Duration::ZERO)? {
            match event::read()? {
                Event::Resize(cols, rows) => self.resize(cols, rows),
                Event::Key(KeyEvent { code, modifiers, kind: KeyEventKind::Press, .. }) => {
                    if code == KeyCode::Char('c') && modifiers.contains(KeyModifiers::CONTROL) {
                        return Ok(Input::Quit);
                    }
                    self.handle_key(code, sys);
                }
                _ => {}
            }
        }
        Ok(Input::Continue)
    }

    fn handle_key(&mut self, code: KeyCode, sys: &mut Apple2) {
        if code == KeyCode::Esc {
            let now = Instant::now();
            if self.last_esc.is_some_and(|t| now.duration_since(t) < DOUBLE_ESC) {
                self.paused = !self.paused;
                self.last_esc = None;
                self.force_redraw = true;
            } else {
                self.last_esc = Some(now);
                sys.key_press(0x1B);
            }
            return;
        }

        let key = match code {
            KeyCode::Left | KeyCode::Backspace => Some(0x08),
            KeyCode::Right => Some(0x15),
            KeyCode::Up => Some(0x0B),
            KeyCode::Down => Some(0x0A),
            KeyCode::Enter => Some(0x0D),
            KeyCode::Char(c) if c.is_ascii() => Some(c.to_ascii_uppercase() as u8),
            _ => None,
        };
        if let Some(k) = key {
            sys.key_press(k);
        }

        match code {
            KeyCode::Char('j') | KeyCode::Char('J') | KeyCode::Left => sys.update_paddle(PADDLE_LEFT),
            KeyCode::Char('k') | KeyCode::Char('K') | KeyCode::Right => sys.update_paddle(PADDLE_RIGHT),
            _ => {}
        }
    }

    fn draw(&mut self, out: &mut impl Write, cpu: &Cpu, sys: &Apple2) -> io::Result<()> {
        let status_row = self.rows.saturating_sub(1);
        if (self.cols as usize) < COLS || (self.rows as usize) < ROWS + 1 {
            if self.force_redraw {
                queue!(out, Clear(ClearType::All))?;
                self.force_redraw = false;
                self.shown.clear();
            }
            let msg = format!(
                "Terminal too small: need {}x{}, have {}x{}. Emulation continues.",
                COLS, ROWS + 1, self.cols, self.rows
            );
            return self.draw_status(out, &msg);
        }

        renderer::render_hgr_braille(&sys.ram[0x2000..0x4000], &mut self.lines);
        let x_off = ((self.cols as usize - COLS) / 2) as u16;

        if self.force_redraw {
            queue!(out, Clear(ClearType::All))?;
            self.shown.clear();
            self.shown.resize_with(ROWS, String::new);
            self.shown_status.clear();
            self.force_redraw = false;
        }
        for (row, line) in self.lines.iter().enumerate() {
            if row as u16 >= status_row {
                break;
            }
            if self.shown[row] != *line {
                queue!(out, cursor::MoveTo(x_off, row as u16), Print(line))?;
                self.shown[row].clone_from(line);
            }
        }

        let status = format!(
            " {} @ ${:04X}   PC ${:04X}   J/K move   Esc Esc pause   Ctrl-C quit ",
            self.name, self.load_addr, cpu.pc
        );
        self.draw_status(out, &status)
    }

    fn draw_status(&mut self, out: &mut impl Write, text: &str) -> io::Result<()> {
        if self.shown_status == text {
            return Ok(());
        }
        let row = self.rows.saturating_sub(1);
        let width = self.cols as usize;
        queue!(
            out,
            cursor::MoveTo(0, row),
            SetAttribute(Attribute::Reverse),
            Print(format!("{text:<width$.width$}")),
            SetAttribute(Attribute::Reset)
        )?;
        self.shown_status = text.to_string();
        Ok(())
    }
}
