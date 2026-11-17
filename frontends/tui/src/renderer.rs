//! Render an Apple II HGR page as Braille characters.
//!
//! Each Braille cell (U+2800..U+28FF) is a 2x4 dot grid, so the 280x192
//! display becomes 140 columns by 48 rows.

pub const COLS: usize = 140;
pub const ROWS: usize = 48;
const HGR_WIDTH: usize = 280;
const HGR_HEIGHT: usize = 192;
const BRAILLE_BASE: u32 = 0x2800;

/// Byte offset of (y, x_byte) within an HGR page.
#[inline]
pub fn hires_offset(y: usize, x_byte: usize) -> usize {
    ((y & 0x07) << 10) + ((y & 0x38) << 4) + ((y >> 6) * 40) + x_byte
}

#[inline]
fn get_pixel(page: &[u8], y: usize, px: usize) -> bool {
    debug_assert!(y < HGR_HEIGHT && px < HGR_WIDTH);
    (page[hires_offset(y, px / 7)] >> (px % 7)) & 1 != 0
}

/// Braille dot bit for a (row, column) within the 4x2 cell.
#[inline]
fn dot(row: usize, right: bool) -> u8 {
    match (row, right) {
        (3, false) => 0x40,
        (3, true) => 0x80,
        (r, false) => 1 << r,
        (r, true) => 1 << (r + 3),
    }
}

/// Render the 8 KB HGR page starting at `page` into `lines`, one `String`
/// per text row. `lines` is resized to [`ROWS`] entries and reused.
pub fn render_hgr_braille(page: &[u8], lines: &mut Vec<String>) {
    lines.resize_with(ROWS, String::new);
    for (char_row, line) in lines.iter_mut().enumerate() {
        line.clear();
        for col in 0..COLS {
            let mut pattern = 0u8;
            for row in 0..4 {
                let y = char_row * 4 + row;
                if get_pixel(page, y, col * 2) {
                    pattern |= dot(row, false);
                }
                if get_pixel(page, y, col * 2 + 1) {
                    pattern |= dot(row, true);
                }
            }
            // The whole Braille block is valid Unicode, so this cannot fail.
            line.push(char::from_u32(BRAILLE_BASE + pattern as u32).unwrap_or(' '));
        }
    }
}
