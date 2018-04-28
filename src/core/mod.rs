
pub struct Pos {
    line: i64,
    column: i64,
}

pub struct Range<'a> {
    at: &'a Pos,
    length: i64,
}