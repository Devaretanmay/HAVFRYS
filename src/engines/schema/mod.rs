mod diff;
mod parser;
mod types;

pub use diff::diff_specs;
pub use parser::parse_spec;
pub use types::{
    BreakingSeverity, ChangeKind, EndpointChange, FieldChange, ParsedSpec, SchemaDiff, SpecInfo,
};
