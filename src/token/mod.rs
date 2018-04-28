
use core;


#[derive(Debug)]
pub struct Token<'a> {
    name: &'a str,
    id: i64,
}

pub trait Tokenizer<'a> {
    fn feed(self, pos: &core::Pos, ch: char) -> Option<(Token<'a>, core::Range<'a>)>;
}

