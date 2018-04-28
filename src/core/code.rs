


pub struct CodePos<'a> {
    filename: &'a str,
    pos: &'a Pos,
}

pub struct CodeRange<'a> {
    filename: &'a str,
    range: &'a Range,
}


pub trait CodeReader<'a> {
    fn getPath() -> &'a Path;
    fn getFileName() -> &'a str;
}

#[derive(Debug)]
pub struct FileCodeReader {
}


impl CodeReader for FileCodeReader {
    // add code here
}