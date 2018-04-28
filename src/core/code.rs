
use std::fs::File;
use std::io::Read;
use std::string::String;
use std::path::Path;
use std::error::Error;
use std::fmt;

pub struct CodePos<'a> {
    filename: &'a str,
    offset: i64,
    line: i64,
    column: i64,
}

pub struct CodeRange<'a> {
    filename: &'a str,
    offset: i64,
    length: i64,
}


#[derive(Debug)]
pub struct CodeReaderError {
    msg: Option<String>,
    cause: Option<&Error>,
}

impl CodeReaderError {
    fn new(msg: &str) -> CodeReaderError {
        CodeReaderError {
            msg: Some(String::from(msg)),
            cause: None,
        }
    }

    fn from(err: &Error) -> CodeReaderError {
        CodeReaderError {
            msg: None,
            cause: Some(err),
        }
    }
}

impl fmt::Display for CodeReaderError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        if let Some(m) = self.msg {
            write!(f, "{}", m)
        }
        if let Some(err) = self.cause {
            write!(f, "{}", err)
        }
    }
}

impl Error for CodeReaderError {
    fn description(&self) -> &str {
        format!("{}", self)
    }
}

pub trait CodeReader<'a> {
    // file path
    fn path(self) -> &'a Path;

    // get char at position
    fn charAt(&self, pos: &super::Pos) -> Result<char, Error>;

    // get piece of chars at range
    fn pieceAt(&self, range: &super::Range) -> Result<&'a [char], CodeReaderError>;
}

#[derive(Debug)]
pub struct FileCodeReader {
    path: String,
    file: File,
    buf: String,
}

impl FileCodeReader {
    fn open<P: AsRef<Path>>(path: P) -> Result<FileCodeReader, CodeReaderError> {
        let pathString = String::from(path.as_ref().to_str().unwrap().to_owned());
        let mut file;
        match File::open(path) {
            Ok(f) => {
                file = f;
            },
            Err(err) => return Result::Err(err),
        }

        // FIXME: check permission: can read?
        // let metadata;
        // match file.metadata() {
        //     Ok(m) => {
        //         metadata = m;
        //     },
        //     Err(err) => return Result::Err(err),
        // }

        let mut fileString = String::new();
        if let Err(err) = file.read_to_string(&mut fileString) {
            return Result::Err(err)
        }

        return Result::Ok(
            FileCodeReader {
                path: pathString,
                file: file,
                buf: fileString,
            }
        )
    }
}

impl<'a> CodeReader<'a> for FileCodeReader {

    fn path(self) -> &'a Path {
        self.path.as_str()
    }

    fn charAt(&self, pos: &super::Pos) -> Result<char, CodeReaderError> {
        if pos.offset < 0 || pos.offset > self.buf.len() {
            return CodeReaderError::new("pos is out of bounds!")
        }

        return Ok(self.buf.as_str()[pos.offset])
    }

    fn pieceAt(&self, range: &super::Range) -> Result<&'a [char], CodeReaderError> {
        if range.offset < 0 || range.offset > self.buf.len() {
            return CodeReaderError::new("range is out of bounds!")
        }
        if range.offset + range.length < 0 || range.offset + range.length > self.buf.len() {
            return CodeReaderError::new("range is out of bounds!")
        }

        return Ok(self.buf.as_str()[range.offset .. range.offset + range.length])
    }
}
